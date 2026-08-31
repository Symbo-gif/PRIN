"""Phase-2 scaling support restored over current PRIN model components.

Statistical aggregation, synthetic benchmark data, and training orchestration
remain Python experiment tooling. Phase/slot model computations delegate to
PRIN's Rust-backed modules.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from prin.dynamics import Seed
from prin.nn import PhaseTracker, TemporalSlotAttentionMOT
from prin.temporal_training import SequenceData
from scipy import stats

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DET_DIM = 4


class _TrackerAdapter(torch.nn.Module):
    """Expose legacy benchmark calls over current Rust-backed trackers."""

    def __init__(self, owner: torch.nn.Module, hidden: int, seed: int) -> None:
        super().__init__()
        self.owner = owner
        self.probe = torch.nn.Sequential(
            torch.nn.Linear(DET_DIM, hidden),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden, DET_DIM),
        )
        self._seed = seed

    def _prepare(self, detections: torch.Tensor) -> torch.Tensor:
        """Apply the benchmark probe and marshal to the Rust bridge dtype."""
        return self.probe(detections).to(dtype=torch.float64)

    def forward(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor
    ) -> tuple[list[int], torch.Tensor]:
        """Match two frames through the wrapped current PRIN tracker."""
        first = self._prepare(detections_t)
        second = self._prepare(detections_t1)
        if isinstance(self.owner, PhaseTracker):
            matches, similarity = self.owner.match_frames(first, second)
        else:
            matches, similarity = self.owner.match_frames(
                first, second, Seed(self._seed, 0)
            )
        return matches, similarity.to(dtype=detections_t.dtype)

    def encode(self, detections: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode detections through the Rust-backed PhaseTracker owner."""
        if not isinstance(self.owner, PhaseTracker):
            raise TypeError("encode is only available for PhaseTracker")
        return self.owner.encode(self._prepare(detections))

    def track_sequence(self, frames: list[torch.Tensor]) -> dict[str, float]:
        """Track a sequence and normalize the legacy result container."""
        prepared = [self._prepare(frame) for frame in frames]
        if isinstance(self.owner, PhaseTracker):
            result = self.owner.track_sequence(prepared)
            identity_preservation = result.identity_preservation
        else:
            result = self.owner.track_sequence(prepared, Seed(self._seed, 0))
            identity_preservation = result[2]
        return {"identity_preservation": float(identity_preservation)}


def _save(name: str, data: dict[str, Any]) -> bool:
    """Write one deterministic JSON benchmark artefact."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"phase2_{name}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, default=str)
    return True


def _build_pt(seed: int = 42) -> _TrackerAdapter:
    """Build a benchmark adapter over Rust-backed PhaseTracker."""
    torch.manual_seed(seed)
    owner = PhaseTracker(
        detection_dim=DET_DIM,
        n_delta=4,
        n_theta=8,
        n_gamma=16,
        n_discrete_steps=5,
        match_threshold=0.1,
        seed_counter=seed,
    )
    return _TrackerAdapter(owner, hidden=16, seed=seed)


def _build_sa(seed: int = 42) -> _TrackerAdapter:
    """Build a benchmark adapter over Rust-backed TemporalSlotAttentionMOT."""
    torch.manual_seed(seed)
    owner = TemporalSlotAttentionMOT(
        detection_dim=DET_DIM,
        num_slots=6,
        slot_dim=64,
        num_iterations=3,
        match_threshold=0.1,
        seed_counter=seed,
    )
    return _TrackerAdapter(owner, hidden=256, seed=seed)


def _gen(
    n: int,
    n_objects: int = 4,
    n_frames: int = 20,
    base_seed: int = 42,
    **_: Any,
) -> list[SequenceData]:
    """Generate deterministic synthetic benchmark sequences."""
    sequences: list[SequenceData] = []
    for sequence_index in range(n):
        generator = torch.Generator().manual_seed(base_seed + sequence_index)
        frames = [
            torch.randn(n_objects, DET_DIM, generator=generator)
            for _ in range(n_frames)
        ]
        sequences.append(
            SequenceData(frames=frames, n_objects=n_objects, n_frames=n_frames)
        )
    return sequences


def _eval_ip(
    model: _TrackerAdapter,
    dataset: list[SequenceData],
    device: str = "cpu",
) -> list[float]:
    """Evaluate identity preservation through current PRIN tracker owners."""
    model.eval()
    return [
        model.track_sequence([frame.to(device) for frame in sequence.frames])[
            "identity_preservation"
        ]
        for sequence in dataset
    ]


def _bootstrap_ci(
    values: list[float], n_boot: int = 5000, alpha: float = 0.05
) -> dict[str, float]:
    """Compute a deterministic non-parametric bootstrap confidence interval."""
    array = np.asarray(values, dtype=float)
    if len(array) < 2:
        value = float(array[0])
        return {"mean": value, "ci_low": value, "ci_high": value, "std": 0.0}
    generator = np.random.default_rng(42)
    means = np.sort(
        [
            generator.choice(array, size=len(array), replace=True).mean()
            for _ in range(n_boot)
        ]
    )
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=1)),
        "ci_low": float(means[int(n_boot * alpha / 2)]),
        "ci_high": float(means[min(int(n_boot * (1 - alpha / 2)), n_boot - 1)]),
    }


def _cliffs_delta(group_a: list[float], group_b: list[float]) -> float:
    """Compute Cliff's delta for phase-2 reports."""
    if not group_a or not group_b:
        return 0.0
    more = sum(a > b for a in group_a for b in group_b)
    less = sum(a < b for a in group_a for b in group_b)
    return (more - less) / (len(group_a) * len(group_b))


def _welch_t(group_a: list[float], group_b: list[float]) -> dict[str, float]:
    """Compute Welch's t-test and pooled-standard-deviation Cohen's d."""
    first = np.asarray(group_a, dtype=float)
    second = np.asarray(group_b, dtype=float)
    if np.array_equal(first, second):
        return {
            "t_stat": 0.0,
            "p_value": 1.0,
            "cohens_d": 0.0,
            "mean_a": float(first.mean()),
            "mean_b": float(second.mean()),
        }
    statistic, p_value = stats.ttest_ind(first, second, equal_var=False)
    pooled = np.sqrt(
        ((len(first) - 1) * first.var(ddof=1) + (len(second) - 1) * second.var(ddof=1))
        / (len(first) + len(second) - 2)
    )
    return {
        "t_stat": float(statistic),
        "p_value": float(p_value),
        "cohens_d": float((first.mean() - second.mean()) / pooled),
        "mean_a": float(first.mean()),
        "mean_b": float(second.mean()),
    }


def _train_model(
    model: _TrackerAdapter,
    seed: int,
    n_objects: int = 4,
    n_frames: int = 20,
    hooks: dict[str, list[float]] | None = None,
    **_: Any,
) -> tuple[_TrackerAdapter, dict[str, Any]]:
    """Run one deterministic benchmark-training epoch over adapter parameters."""
    torch.manual_seed(seed)
    handles: list[torch.utils.hooks.RemovableHandle] = []
    if hooks is not None:
        for name, module in model.named_modules():
            if isinstance(module, torch.nn.Linear):
                handles.append(
                    module.register_full_backward_hook(
                        lambda _module, _inputs, outputs, key=name: hooks.setdefault(
                            key, []
                        ).append(float(outputs[0].detach().norm().item()))
                    )
                )
    optimizer = torch.optim.Adam(model.probe.parameters(), lr=1e-3)
    data = _gen(1, n_objects=n_objects, n_frames=n_frames, base_seed=seed)[0]
    started = time.perf_counter()
    model.train()
    optimizer.zero_grad()
    projected = model.probe(data.frames[0].requires_grad_(True))
    loss = projected.square().mean()
    loss.backward()
    optimizer.step()
    for handle in handles:
        handle.remove()
    return model, {"epochs": 1, "wall_time_s": max(time.perf_counter() - started, 1e-9)}

"""Year 2 Q2 Benchmarks — Temporal CLEVR & A/B Testing Utilities.

Provides:
- ``make_temporal_clevr``: Multi-frame temporal CLEVR sequence generator.
- ``run_f_ab_test``: A/B comparison of active vs passive control training.
"""

from __future__ import annotations

import math
from typing import Any

import torch
import torch.nn.functional as F
from torch import Tensor

from benchmarks.clevr_n import (
    D_FEAT,
    D_PHASE,
    N_POSITIONS,
    _sample_scene,
    encode_features_phase,
    make_clevr_n,
)
from benchmarks.y2q1_benchmarks import DiscreteDTGCLEVRN

SEED = 42


def make_temporal_clevr(
    n_items: int = 6,
    n_frames: int = 5,
    n_samples: int = 1000,
    seed: int = SEED,
    movement_scale: float = 0.2,
) -> tuple[Tensor, Tensor, Tensor]:
    """Generate Temporal CLEVR dataset: multi-frame sequences.

    Each sample is a sequence of T frames. Objects persist across frames
    with small position changes (simulating movement). The query asks
    whether two specific objects maintain their relative order across
    all frames (temporal identity tracking).

    Args:
        n_items: Objects per scene.
        n_frames: Frames per sequence.
        n_samples: Number of sequences.
        seed: Random seed.
        movement_scale: Max position shift per frame (in grid units).

    Returns:
        scenes: ``(n_samples, n_frames, n_items, 16)`` phase-encoded features.
        queries: ``(n_samples, 32)`` encoded relational queries.
        labels: ``(n_samples,)`` binary labels (0 or 1).
    """
    rng = torch.Generator().manual_seed(seed)

    all_scenes: list[Tensor] = []
    all_queries: list[Tensor] = []
    all_labels: list[int] = []

    for _ in range(n_samples):
        # Initial scene
        colors, shapes, positions = _sample_scene(n_items, rng)
        positions_float = positions.float()

        frame_encodings: list[Tensor] = []

        for t in range(n_frames):
            if t > 0:
                delta = (torch.rand(n_items, generator=rng) * 2 - 1) * movement_scale
                positions_float = positions_float + delta
                positions_float = torch.clamp(
                    positions_float, 0.0, float(N_POSITIONS - 1)
                )

            pos_ids = positions_float.round().long().clamp(0, N_POSITIONS - 1)
            enc = encode_features_phase(colors, shapes, pos_ids)
            frame_encodings.append(enc)

        scene_seq = torch.stack(frame_encodings)  # (T, n_items, D_PHASE)

        # Query: pick two objects, encode as 32-dim feature vector
        idx = torch.randperm(n_items, generator=rng)[:2]
        i, j = idx[0].item(), idx[1].item()

        # Build a 32-dim relational query from the two objects' features
        q_i = torch.zeros(16)
        q_j = torch.zeros(16)
        # Encode object features as phase-like vectors
        angle_i = (colors[i].float() / 8.0) * 2.0 * math.pi
        angle_j = (colors[j].float() / 8.0) * 2.0 * math.pi
        for k in range(8):
            freq = float(k + 1)
            q_i[2 * k] = math.sin(freq * angle_i.item())
            q_i[2 * k + 1] = math.cos(freq * angle_i.item())
            q_j[2 * k] = math.sin(freq * angle_j.item())
            q_j[2 * k + 1] = math.cos(freq * angle_j.item())
        query = torch.cat([q_i, q_j])  # (32,)

        # Label: 1 if relative order is maintained across all frames
        initial_order = positions[i] < positions[j]
        final_pos = positions_float.round().long().clamp(0, N_POSITIONS - 1)
        final_order = final_pos[i] < final_pos[j]
        label = 1 if (initial_order == final_order) else 0

        all_scenes.append(scene_seq)
        all_queries.append(query)
        all_labels.append(label)

    scenes = torch.stack(all_scenes)  # (N, T, n_items, D_PHASE)
    queries = torch.stack(all_queries)  # (N, 32)
    labels = torch.tensor(all_labels, dtype=torch.long)

    return scenes, queries, labels


def _train_single_run(
    n_epochs: int,
    n_items: int,
    seed: int,
    device: str,
    active: bool,
) -> list[float]:
    """Train DiscreteDTGCLEVRN for one run and return per-epoch losses.

    When ``active`` is True, a simple active-control heuristic adjusts
    the learning rate based on loss trend. When False, plain SGD is used.
    """
    torch.manual_seed(seed)

    model = DiscreteDTGCLEVRN(scene_dim=D_PHASE, query_dim=D_FEAT * 2).to(device)
    base_lr = 1e-3
    optimizer = torch.optim.Adam(model.parameters(), lr=base_lr)

    scenes, queries, labels = make_clevr_n(
        n_items,
        n_samples=100,
        seed=seed,
        phase_encode=True,
    )
    scenes, queries, labels = scenes.to(device), queries.to(device), labels.to(device)

    losses: list[float] = []
    prev_loss = float("inf")

    for _epoch in range(n_epochs):
        model.train()
        optimizer.zero_grad()
        log_probs = model(scenes, queries)
        loss = F.nll_loss(log_probs, labels)
        loss.backward()
        optimizer.step()

        epoch_loss = loss.item()
        losses.append(epoch_loss)

        if active:
            # Simple active control: reduce LR if loss is increasing
            if epoch_loss > prev_loss:
                for pg in optimizer.param_groups:
                    pg["lr"] = max(pg["lr"] * 0.95, 1e-5)
            else:
                for pg in optimizer.param_groups:
                    pg["lr"] = min(pg["lr"] * 1.01, base_lr)

        prev_loss = epoch_loss

    return losses


def run_f_ab_test(
    n_runs_per_group: int = 10,
    n_epochs: int = 5,
    n_items: int = 4,
    base_seed: int = SEED,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run A/B comparison of active vs passive control training.

    Trains ``DiscreteDTGCLEVRN`` for ``n_runs_per_group`` runs each,
    with active control (adaptive LR) vs passive (fixed LR).

    Args:
        n_runs_per_group: Number of runs per group.
        n_epochs: Training epochs per run.
        n_items: Number of objects per scene.
        base_seed: Base random seed.
        device: Device string.

    Returns:
        Dict with ``active_runs``, ``passive_runs`` (lists of per-run
        loss lists), and ``statistics`` (``t_statistic``, ``p_value_approx``).
    """
    active_runs: list[list[float]] = []
    passive_runs: list[list[float]] = []

    for r in range(n_runs_per_group):
        active_losses = _train_single_run(
            n_epochs,
            n_items,
            seed=base_seed + r * 2,
            device=device,
            active=True,
        )
        passive_losses = _train_single_run(
            n_epochs,
            n_items,
            seed=base_seed + r * 2 + 1,
            device=device,
            active=False,
        )
        active_runs.append(active_losses)
        passive_runs.append(passive_losses)

    # Compute final-loss statistics
    active_final = [run[-1] for run in active_runs]
    passive_final = [run[-1] for run in passive_runs]

    mean_a = sum(active_final) / len(active_final)
    mean_p = sum(passive_final) / len(passive_final)
    n_a = max(len(active_final) - 1, 1)
    n_p = max(len(passive_final) - 1, 1)
    var_a = sum((x - mean_a) ** 2 for x in active_final) / n_a
    var_p = sum((x - mean_p) ** 2 for x in passive_final) / n_p

    se = math.sqrt(var_a / len(active_final) + var_p / len(passive_final))
    t_stat = (mean_a - mean_p) / max(se, 1e-12)

    # Rough p-value approximation (two-tailed, using normal approx)
    p_value = 2.0 * math.exp(-0.5 * t_stat * t_stat) / math.sqrt(2.0 * math.pi)
    p_value = min(max(p_value, 0.0), 1.0)

    return {
        "active_runs": active_runs,
        "passive_runs": passive_runs,
        "statistics": {
            "t_statistic": t_stat if math.isfinite(t_stat) else 0.0,
            "p_value_approx": p_value if math.isfinite(p_value) else 1.0,
        },
    }

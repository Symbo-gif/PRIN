"""PRINet 3.0-compatible temporal training framework (``temporal_training``).

Faithful port (Testing Standards §1.1) of the PRINet 3.0 unified temporal
training framework for fair PhaseTracker vs. SlotAttention comparison: the
CLEVR-N temporal sequence generators, the similarity-matching losses, the
complex-aware parameter counter, and the :class:`TemporalTrainer` loop with
validation-based early stopping, gradient clipping, and dynamics snapshots.

Numerics disposition: the same benchmark/experiment-tooling category as
:mod:`prin.y4q1_tools` and :mod:`prin.nn.mot_evaluation` — the trainer
orchestrates ``torch.optim`` steps over models whose numerical cores live in
Rust (:class:`prin.nn.temporal_compat.PhaseTracker`'s
:class:`prin.nn.DiscreteDeltaThetaGamma` dynamics) or in the explicitly
non-oscillatory Slot Attention baseline. This module is excluded from the
``check_no_python_numerics`` compat-surface scan (WP-036C S1 0144M6/0144M7).
"""

from __future__ import annotations

import copy
import math
import time
from dataclasses import dataclass, field
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from prin.temporal_metrics import (
    identity_switches,
    track_fragmentation_rate,
)

__all__ = [
    "MultiSeedResult",
    "SequenceData",
    "TemporalTrainer",
    "TrainingResult",
    "TrainingSnapshot",
    "count_parameters",
    "generate_dataset",
    "generate_temporal_clevr_n",
    "hungarian_similarity_loss",
    "temporal_smoothness_loss",
    "train_multi_seed",
]


@dataclass
class SequenceData:
    """Container for a generated temporal sequence.

    Faithful dataclass port of the PRINet 3.0 ``SequenceData``. Holds
    per-frame detections and ground-truth labels. No computation.

    Attributes:
        frames: Per-frame detection tensors (list of ``(N, D)`` arrays).
        positions: 2-D positions ``(T, N, 2)``.
        velocities: Per-frame velocities ``(T, N, 2)``.
        identities: Ground-truth identity labels ``(T, N)``.
        occlusion_mask: Visibility mask ``(T, N)``; 1 = visible.
        n_objects: Number of ground-truth objects.
        n_frames: Number of frames.
    """

    frames: list[Any] = field(default_factory=list)
    positions: Any = None
    velocities: Any = None
    identities: Any = None
    occlusion_mask: Any = None
    n_objects: int = 0
    n_frames: int = 0


@dataclass
class TrainingSnapshot:
    """Captured training state at a specific epoch.

    Attributes:
        epoch: Epoch number.
        train_loss: Training loss.
        val_loss: Validation loss.
        val_ip: Validation identity preservation.
        val_idsw: Validation identity switches.
        gradient_norm: Mean gradient L2 norm.
        param_norm: Mean parameter L2 norm.
        phase_coherence: Mean phase coherence (PT only).
        slot_entropy: Mean slot attention entropy (SA only).
    """

    epoch: int = 0
    train_loss: float = 0.0
    val_loss: float = 0.0
    val_ip: float = 0.0
    val_idsw: int = 0
    gradient_norm: float = 0.0
    param_norm: float = 0.0
    phase_coherence: float = 0.0
    slot_entropy: float = 0.0


@dataclass
class MultiSeedResult:
    """Aggregated results across multiple random seeds.

    Attributes:
        model_name: Name of the model.
        seeds: List of seeds used.
        per_seed: Per-seed training results.
        mean_ip: Mean identity preservation across seeds.
        std_ip: Standard deviation of identity preservation.
        mean_idsw: Mean identity switches.
        mean_tfr: Mean track fragmentation rate.
        mean_epochs: Mean epochs to convergence.
        mean_wall_time: Mean wall time.
    """

    model_name: str = ""
    seeds: list[int] = field(default_factory=list)
    per_seed: list[Any] = field(default_factory=list)
    mean_ip: float = 0.0
    std_ip: float = 0.0
    mean_idsw: float = 0.0
    mean_tfr: float = 0.0
    mean_epochs: float = 0.0
    mean_wall_time: float = 0.0


def count_parameters(
    model: Any,
    count_complex_as_double: bool = True,
) -> dict[str, int]:
    """Count model parameters with complex-aware counting.

    Introspects ``model.named_parameters()`` (any object exposing that
    method, typically a ``torch.nn.Module``). Complex-valued parameters
    count as 2x real parameters for fair comparison between phase-based
    and real-valued architectures.

    Args:
        model: Model exposing ``named_parameters()``.
        count_complex_as_double: If ``True``, complex params count as 2x.

    Returns:
        Dict with ``total``, ``trainable``, ``frozen``, ``complex_adjusted``.

    Example:
        >>> import torch
        >>> m = torch.nn.Linear(4, 2)
        >>> counts = count_parameters(m)
        >>> counts["total"]
        10
    """
    total = 0
    trainable = 0
    frozen = 0
    complex_adjusted = 0

    for _name, p in model.named_parameters():
        numel = p.numel()
        is_complex = p.is_complex()
        real_count = numel * 2 if (is_complex and count_complex_as_double) else numel

        total += numel
        complex_adjusted += real_count
        if p.requires_grad:
            trainable += numel
        else:
            frozen += numel

    return {
        "total": total,
        "trainable": trainable,
        "frozen": frozen,
        "complex_adjusted": complex_adjusted,
    }


def generate_temporal_clevr_n(
    n_objects: int = 4,
    n_frames: int = 20,
    det_dim: int = 4,
    velocity_range: tuple[float, float] = (0.5, 2.0),
    occlusion_rate: float = 0.0,
    swap_rate: float = 0.0,
    reversal_count: int = 0,
    noise_sigma: float = 0.0,
    seed: int = 42,
) -> SequenceData:
    """Generate a CLEVR-N-style temporal sequence with ground-truth labels."""
    gen = torch.Generator()
    gen.manual_seed(seed)

    identities = torch.arange(n_objects).unsqueeze(0).expand(n_frames, -1)
    pos = torch.rand(n_objects, 2, generator=gen) * 10.0
    speed = (
        torch.rand(n_objects, 1, generator=gen)
        * (velocity_range[1] - velocity_range[0])
        + velocity_range[0]
    )
    angle = torch.rand(n_objects, 1, generator=gen) * 2.0 * math.pi
    vel = speed * torch.cat([torch.cos(angle), torch.sin(angle)], dim=-1)
    appearance = torch.randn(n_objects, max(det_dim - 2, 2), generator=gen) * 0.5

    reversal_frames: set[int] = set()
    if reversal_count > 0 and n_frames > 2:
        rev_gen = torch.Generator()
        rev_gen.manual_seed(seed + 999)
        rev_idx = torch.randint(1, n_frames - 1, (reversal_count,), generator=rev_gen)
        reversal_frames = set(rev_idx.tolist())

    occ_mask = torch.ones(n_frames, n_objects)
    if occlusion_rate > 0:
        occ_gen = torch.Generator()
        occ_gen.manual_seed(seed + 1000)
        occ_rand = torch.rand(n_frames, n_objects, generator=occ_gen)
        occ_mask = (occ_rand > occlusion_rate).float()
        occ_mask[0] = 1.0

    swap_frames: set[int] = set()
    if swap_rate > 0 and n_frames > 1 and n_objects >= 2:
        swap_gen = torch.Generator()
        swap_gen.manual_seed(seed + 2000)
        n_swaps = max(1, int(n_frames * swap_rate))
        swap_idx = torch.randint(1, n_frames, (n_swaps,), generator=swap_gen)
        swap_frames = set(swap_idx.tolist())

    positions_list: list[torch.Tensor] = []
    velocities_list: list[torch.Tensor] = []
    frames: list[torch.Tensor] = []

    for t in range(n_frames):
        if t in reversal_frames:
            vel = -vel
        if t > 0:
            pos = pos + vel * 0.1
        for dim_i in range(2):
            low_mask = pos[:, dim_i] < 0
            high_mask = pos[:, dim_i] > 10
            vel[low_mask, dim_i] = vel[low_mask, dim_i].abs()
            vel[high_mask, dim_i] = -vel[high_mask, dim_i].abs()
            pos[:, dim_i] = pos[:, dim_i].clamp(0, 10)

        positions_list.append(pos.clone())
        velocities_list.append(vel.clone())

        det = torch.cat([pos, appearance[:, : det_dim - 2]], dim=-1)

        if noise_sigma > 0:
            noise_gen = torch.Generator()
            noise_gen.manual_seed(seed + 3000 + t)
            noise = torch.randn(n_objects, det_dim, generator=noise_gen) * noise_sigma
            det = det + noise

        if t in swap_frames:
            swap_gen2 = torch.Generator()
            swap_gen2.manual_seed(seed + 4000 + t)
            i, j = 0, 1
            if n_objects > 2:
                perm = torch.randperm(n_objects, generator=swap_gen2)
                i, j = int(perm[0].item()), int(perm[1].item())
            det_copy = det.clone()
            det[i, 2:] = det_copy[j, 2:]
            det[j, 2:] = det_copy[i, 2:]

        vis = occ_mask[t].unsqueeze(-1)
        det = det * vis
        frames.append(det.clone())

    positions = torch.stack(positions_list, dim=0)
    velocities = torch.stack(velocities_list, dim=0)

    return SequenceData(
        frames=frames,
        positions=positions,
        velocities=velocities,
        identities=identities.clone(),
        occlusion_mask=occ_mask,
        n_objects=n_objects,
        n_frames=n_frames,
    )


def generate_dataset(
    n_sequences: int,
    n_objects: int = 4,
    n_frames: int = 20,
    det_dim: int = 4,
    occlusion_rate: float = 0.0,
    swap_rate: float = 0.0,
    reversal_count: int = 0,
    noise_sigma: float = 0.0,
    base_seed: int = 42,
) -> list[SequenceData]:
    """Generate a dataset of multiple temporal sequences."""
    return [
        generate_temporal_clevr_n(
            n_objects=n_objects,
            n_frames=n_frames,
            det_dim=det_dim,
            occlusion_rate=occlusion_rate,
            swap_rate=swap_rate,
            reversal_count=reversal_count,
            noise_sigma=noise_sigma,
            seed=base_seed + i,
        )
        for i in range(n_sequences)
    ]


def hungarian_similarity_loss(
    similarity: torch.Tensor,
    n_objects: int,
) -> torch.Tensor:
    """Compute assignment loss on the similarity matrix.

    Soft cross-entropy treating each row as a classification problem whose
    correct class is the diagonal (identity permutation target).
    """
    N = min(similarity.shape[0], similarity.shape[1], n_objects)
    if N == 0:
        return similarity.new_tensor(0.0)
    sim_block = similarity[:N, :N]
    temperature = 0.1
    logits = sim_block / temperature
    target = torch.arange(N, device=similarity.device)
    return F.cross_entropy(logits, target)


def temporal_smoothness_loss(
    similarity_sequence: list[torch.Tensor],
) -> torch.Tensor:
    """Penalize jittery similarity patterns across frames.

    Encourages smooth evolution of the similarity matrix over time (mean
    squared difference of same-size blocks between consecutive frames).

    Args:
        similarity_sequence: List of T-1 similarity matrices.

    Returns:
        Scalar loss tensor.
    """
    if len(similarity_sequence) < 2:
        return (
            similarity_sequence[0].new_tensor(0.0)
            if similarity_sequence
            else torch.tensor(0.0)
        )

    diffs = []
    for t in range(1, len(similarity_sequence)):
        prev = similarity_sequence[t - 1]
        curr = similarity_sequence[t]
        n = min(prev.shape[0], curr.shape[0])
        m = min(prev.shape[1], curr.shape[1])
        diff = (prev[:n, :m] - curr[:n, :m]).pow(2).mean()
        diffs.append(diff)

    return torch.stack(diffs).mean()


# =========================================================================
# 4. Training Dynamics Snapshot
# =========================================================================


@dataclass
class TrainingResult:
    """Complete training result with dynamics.

    Attributes:
        final_train_loss: Final training loss.
        final_val_loss: Final validation loss.
        final_val_ip: Final validation identity preservation.
        best_val_loss: Best (smoothed) validation loss.
        best_epoch: Epoch with best validation loss.
        total_epochs: Total epochs trained.
        wall_time_s: Total wall time in seconds.
        snapshots: List of training snapshots.
        train_losses: Per-epoch training losses.
        val_losses: Per-epoch validation losses.
        val_ips: Per-epoch validation IPs.
    """

    final_train_loss: float = 0.0
    final_val_loss: float = 0.0
    final_val_ip: float = 0.0
    best_val_loss: float = float("inf")
    best_epoch: int = 0
    total_epochs: int = 0
    wall_time_s: float = 0.0
    snapshots: list[TrainingSnapshot] = field(default_factory=list)
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    val_ips: list[float] = field(default_factory=list)


# =========================================================================
# 5. Temporal Trainer
# =========================================================================


class TemporalTrainer:
    """Fair-comparison training for PhaseTracker vs. SlotAttention.

    Identical loss, optimizer, LR schedule (cosine annealing + linear warmup),
    validation-based early stopping with moving-average smoothing, gradient
    clipping, and dynamics snapshots for both architectures. The models'
    numerical cores are Rust-backed (see the module docstring).

    Args:
        model: Tracker model (:class:`~prin.nn.temporal_compat.PhaseTracker`
            or :class:`~prin.nn.temporal_compat.TemporalSlotAttentionMOT`, or
            an ablation variant).
        lr: Learning rate.
        weight_decay: Weight decay coefficient.
        max_epochs: Maximum training epochs.
        patience: Early stopping patience (epochs).
        smoothing_window: Moving-average window for loss smoothing.
        warmup_epochs: Linear LR warmup epochs.
        grad_clip: Maximum gradient norm for clipping.
        snapshot_epochs: Epochs at which to capture snapshots.
        device: Device string.
        seed: Random seed.
    """

    def __init__(
        self,
        model: nn.Module,
        lr: float = 3e-4,
        weight_decay: float = 0.0,
        max_epochs: int = 100,
        patience: int = 10,
        smoothing_window: int = 5,
        warmup_epochs: int = 5,
        grad_clip: float = 1.0,
        snapshot_epochs: tuple[int, ...] = (0, 10, 25, 50, 100),
        device: str = "cpu",
        seed: int = 42,
    ) -> None:
        """Build the optimizer + schedule and move the model to ``device``."""
        self.model = model.to(device)
        self.device = device
        self.max_epochs = max_epochs
        self.patience = patience
        self.smoothing_window = smoothing_window
        self.warmup_epochs = warmup_epochs
        self.grad_clip = grad_clip
        self.snapshot_epochs = set(snapshot_epochs)
        self.seed = seed
        self.lr = lr

        torch.manual_seed(seed)
        self.optimizer = torch.optim.Adam(
            model.parameters(), lr=lr, weight_decay=weight_decay
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=max_epochs, eta_min=lr * 0.01
        )

    def _warmup_lr(self, epoch: int) -> None:
        """Apply linear warmup to the learning rate."""
        if epoch < self.warmup_epochs:
            warmup_factor = (epoch + 1) / self.warmup_epochs
            for pg in self.optimizer.param_groups:
                pg["lr"] = self.lr * warmup_factor

    def _compute_gradient_norm(self) -> float:
        """Total gradient L2 norm across all parameters."""
        total = 0.0
        for p in self.model.parameters():
            if p.grad is not None:
                total += p.grad.data.norm(2).item() ** 2
        return math.sqrt(total)

    def _compute_param_norm(self) -> float:
        """Total parameter L2 norm."""
        total = 0.0
        for p in self.model.parameters():
            total += p.data.norm(2).item() ** 2
        return math.sqrt(total)

    def _train_step_pt(self, seq: SequenceData) -> tuple[float, torch.Tensor]:
        """Training step for PhaseTracker-family models via ``forward()`` similarity."""
        self.model.train()
        total_loss = torch.tensor(0.0, device=self.device)
        n_transitions = 0
        sim_history: list[torch.Tensor] = []
        dyn_model: Any = self.model

        for t in range(1, seq.n_frames):
            dets_prev = seq.frames[t - 1].to(self.device)
            dets_curr = seq.frames[t].to(self.device)

            if dets_prev.abs().sum() < 1e-8 or dets_curr.abs().sum() < 1e-8:
                continue

            _, sim = dyn_model(dets_prev, dets_curr)
            loss = hungarian_similarity_loss(sim, seq.n_objects)
            total_loss = total_loss + loss
            sim_history.append(sim.detach())
            n_transitions += 1

        if n_transitions > 0:
            total_loss = total_loss / n_transitions
            if len(sim_history) >= 2:
                ts_loss = temporal_smoothness_loss(sim_history)
                total_loss = total_loss + 0.1 * ts_loss

        return float(total_loss.item()) if n_transitions > 0 else 0.0, total_loss

    def _train_step_sa(self, seq: SequenceData) -> tuple[float, torch.Tensor]:
        """Training step for SlotAttention-family models via ``process_frame()``."""
        self.model.train()
        total_loss = torch.tensor(0.0, device=self.device)
        n_transitions = 0
        sim_history: list[torch.Tensor] = []
        prev_slots = None
        dyn_model: Any = self.model

        for t in range(seq.n_frames):
            dets = seq.frames[t].to(self.device)
            slots = dyn_model.process_frame(dets, prev_slots)

            if prev_slots is not None:
                sim = dyn_model.slot_similarity(prev_slots, slots)
                n = min(sim.shape[0], sim.shape[1], seq.n_objects)
                if n > 0:
                    loss = hungarian_similarity_loss(sim, seq.n_objects)
                    total_loss = total_loss + loss
                    sim_history.append(sim.detach())
                    n_transitions += 1

            prev_slots = slots

        if n_transitions > 0:
            total_loss = total_loss / n_transitions
            if len(sim_history) >= 2:
                ts_loss = temporal_smoothness_loss(sim_history)
                total_loss = total_loss + 0.1 * ts_loss

        return float(total_loss.item()) if n_transitions > 0 else 0.0, total_loss

    def _is_phase_tracker(self) -> bool:
        """Whether the model is a PhaseTracker or a wrapped PhaseTracker variant."""
        m = self.model
        if hasattr(m, "det_to_phase") and hasattr(m, "dynamics"):
            return True
        if hasattr(m, "_inner") and hasattr(m._inner, "det_to_phase"):
            return True
        if hasattr(m, "det_to_phase") and hasattr(m, "frequencies"):
            return True
        return False

    def train_epoch(self, dataset: list[SequenceData]) -> float:
        """Run one training epoch; returns the mean training loss."""
        self.model.train()
        total_loss = 0.0
        is_pt = self._is_phase_tracker()

        for seq in dataset:
            self.optimizer.zero_grad()
            if is_pt:
                loss_val, loss_tensor = self._train_step_pt(seq)
            else:
                loss_val, loss_tensor = self._train_step_sa(seq)

            if loss_val > 0:
                has_trainable = any(p.requires_grad for p in self.model.parameters())
                if has_trainable and loss_tensor.requires_grad:
                    loss_tensor.backward()  # type: ignore[no-untyped-call]
                    if self.grad_clip > 0:
                        nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.grad_clip
                        )
                    self.optimizer.step()

            total_loss += loss_val

        return total_loss / max(len(dataset), 1)

    @torch.no_grad()
    def evaluate(self, dataset: list[SequenceData]) -> dict[str, float]:
        """Evaluate the model; returns ``loss``/``ip``/``idsw``/``tfr`` means."""
        self.model.eval()
        is_pt = self._is_phase_tracker()
        total_loss = 0.0
        total_ip = 0.0
        total_idsw = 0
        total_tfr = 0.0
        n_seqs = 0
        dyn_model: Any = self.model

        for seq in dataset:
            frames = [f.to(self.device) for f in seq.frames]

            result = dyn_model.track_sequence(frames)
            matches = result["identity_matches"]
            ip = result["identity_preservation"]

            total_ip += ip
            total_idsw += identity_switches(matches, seq.n_objects)
            total_tfr += track_fragmentation_rate(matches, seq.n_objects)
            n_seqs += 1

            loss = 0.0
            n_trans = 0
            for t in range(1, seq.n_frames):
                dets_prev = frames[t - 1]
                dets_curr = frames[t]
                if dets_prev.abs().sum() < 1e-8 or dets_curr.abs().sum() < 1e-8:
                    continue
                if is_pt:
                    _, sim = dyn_model(dets_prev, dets_curr)
                else:
                    prev_slots_eval = dyn_model.process_frame(dets_prev)
                    curr_slots_eval = dyn_model.process_frame(
                        dets_curr, prev_slots_eval
                    )
                    sim = dyn_model.slot_similarity(prev_slots_eval, curr_slots_eval)
                loss += float(hungarian_similarity_loss(sim, seq.n_objects).item())
                n_trans += 1
            total_loss += loss / max(n_trans, 1)

        n = max(n_seqs, 1)
        return {
            "loss": total_loss / n,
            "ip": total_ip / n,
            "idsw": total_idsw / n,
            "tfr": total_tfr / n,
        }

    def _capture_snapshot(
        self, epoch: int, train_loss: float, val_metrics: dict[str, float]
    ) -> TrainingSnapshot:
        """Capture a training dynamics snapshot."""
        snap = TrainingSnapshot(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_metrics.get("loss", 0.0),
            val_ip=val_metrics.get("ip", 0.0),
            val_idsw=int(val_metrics.get("idsw", 0)),
            gradient_norm=self._compute_gradient_norm(),
            param_norm=self._compute_param_norm(),
        )

        if self._is_phase_tracker() and hasattr(self.model, "dynamics"):
            try:
                dyn_model: Any = self.model
                n_osc = getattr(dyn_model, "n_osc", None)
                if n_osc is not None:
                    test_phase = torch.rand(1, n_osc, device=self.device) * 2 * math.pi
                    test_amp = torch.ones(1, n_osc, device=self.device)
                    evolved_phase, _ = dyn_model.evolve(test_phase, test_amp)
                    z = torch.exp(1j * evolved_phase.to(torch.complex64))
                    snap.phase_coherence = float(z.mean(dim=-1).abs().mean().item())
            except Exception:
                snap.phase_coherence = 0.0

        return snap

    def train(
        self,
        train_data: list[SequenceData],
        val_data: list[SequenceData],
    ) -> TrainingResult:
        """Train with early stopping and dynamics capture."""
        result = TrainingResult()
        best_val_loss = float("inf")
        best_state = None
        patience_counter = 0
        val_loss_history: list[float] = []

        t0 = time.perf_counter()

        for epoch in range(self.max_epochs):
            self._warmup_lr(epoch)

            train_loss = self.train_epoch(train_data)
            result.train_losses.append(train_loss)

            if epoch >= self.warmup_epochs:
                self.scheduler.step()

            val_metrics = self.evaluate(val_data)
            val_loss = val_metrics["loss"]
            result.val_losses.append(val_loss)
            result.val_ips.append(val_metrics["ip"])
            val_loss_history.append(val_loss)

            if epoch in self.snapshot_epochs:
                snap = self._capture_snapshot(epoch, train_loss, val_metrics)
                result.snapshots.append(snap)

            if len(val_loss_history) >= self.smoothing_window:
                smoothed = (
                    sum(val_loss_history[-self.smoothing_window :])
                    / self.smoothing_window
                )
            else:
                smoothed = val_loss

            if smoothed < best_val_loss - 1e-6:
                best_val_loss = smoothed
                best_state = copy.deepcopy(self.model.state_dict())
                result.best_epoch = epoch
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= self.patience:
                break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        wall_time = time.perf_counter() - t0
        final_val = self.evaluate(val_data)

        result.final_train_loss = (
            result.train_losses[-1] if result.train_losses else 0.0
        )
        result.final_val_loss = final_val["loss"]
        result.final_val_ip = final_val["ip"]
        result.best_val_loss = best_val_loss
        result.total_epochs = len(result.train_losses)
        result.wall_time_s = wall_time

        if result.total_epochs - 1 not in self.snapshot_epochs:
            snap = self._capture_snapshot(
                result.total_epochs - 1, result.final_train_loss, final_val
            )
            result.snapshots.append(snap)

        return result


# =========================================================================
# 6. Multi-Seed Experiment Runner
# =========================================================================


def train_multi_seed(
    model_factory: Any,
    model_name: str,
    train_data: list[SequenceData],
    val_data: list[SequenceData],
    seeds: Any = (42, 123, 456, 789, 1024),
    device: str = "cpu",
    **trainer_kwargs: Any,
) -> MultiSeedResult:
    """Train a model across multiple seeds for statistical reliability."""
    result = MultiSeedResult(model_name=model_name, seeds=list(seeds))

    for seed in seeds:
        torch.manual_seed(seed)
        model = model_factory()
        trainer = TemporalTrainer(model, device=device, seed=seed, **trainer_kwargs)
        tr = trainer.train(train_data, val_data)
        result.per_seed.append(tr)

    ips = [r.final_val_ip for r in result.per_seed]
    result.mean_ip = sum(ips) / len(ips)
    result.std_ip = (
        sum((x - result.mean_ip) ** 2 for x in ips) / max(len(ips) - 1, 1)
    ) ** 0.5

    epochs = [r.total_epochs for r in result.per_seed]
    result.mean_epochs = sum(epochs) / len(epochs)

    times = [r.wall_time_s for r in result.per_seed]
    result.mean_wall_time = sum(times) / len(times)

    return result

"""PRINet 3.0-compatible temporal training framework surface.

This module provides the PRINet 3.0 ``prinet.utils.temporal_training`` public
API as a mix of real data containers / non-numeric utilities and documented
D-2.2 stubs. Dataclasses (``SequenceData``, ``TrainingSnapshot``,
``MultiSeedResult``) and the ``count_parameters`` introspection utility are
real implementations. Training loops, loss functions, and data generators
require Python numerics and receive typed D-2.2 dispositions.

No numerical computation is introduced (Coding Standards Sec. 1.2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, NoReturn

import torch

__all__ = [
    "MultiSeedResult",
    "SequenceData",
    "TemporalTrainer",
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


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


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
    """Compute assignment loss on the similarity matrix."""
    import torch.nn.functional as F

    N = min(similarity.shape[0], similarity.shape[1], n_objects)
    if N == 0:
        return similarity.new_tensor(0.0)
    sim_block = similarity[:N, :N]
    temperature = 0.1
    logits = sim_block / temperature
    target = torch.arange(N, device=similarity.device)
    return F.cross_entropy(logits, target)


def temporal_smoothness_loss(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred temporal smoothness loss.

    Raises:
        NotImplementedError: Always. The loss computes MSE over similarity
        sequences (Python numerics). PRIN's ``prin.eval.temporal_smoothness``
        takes position trajectories, not similarity-matrix sequences, so it
        is not a faithful owner.
    """
    _raise_disposition(
        "temporal_smoothness_loss",
        "Numeric loss function; no faithful prin.eval owner.",
    )


class TemporalTrainer:
    """Deferred-rebuild stub for the temporal training loop.

    PRINet 3.0 ``TemporalTrainer`` manages a complete training loop with
    validation-based early stopping, gradient clipping, and snapshot
    recording. This requires Python numerics (forward/backward passes,
    optimizer steps).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "TemporalTrainer",
            "Training loop requires Python numerics (forward/backward passes).",
        )


def train_multi_seed(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred multi-seed training runner.

    Raises:
        NotImplementedError: Always. Delegates to ``TemporalTrainer``
            which is a D-2.2 stub.
    """
    _raise_disposition(
        "train_multi_seed",
        "Multi-seed training requires Python numerics.",
    )

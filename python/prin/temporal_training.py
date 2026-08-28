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

from dataclasses import dataclass, field
from typing import Any, NoReturn

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


def generate_temporal_clevr_n(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred temporal CLEVR-N data generator.

    Raises:
        NotImplementedError: Always. The generator requires PyTorch RNG
            numerics; a future WP will provide a Rust-backed data generator.
    """
    _raise_disposition(
        "generate_temporal_clevr_n",
        "Data generator requires PyTorch RNG numerics.",
    )


def generate_dataset(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred dataset generator.

    Raises:
        NotImplementedError: Always. Delegates to
            ``generate_temporal_clevr_n`` which is a D-2.2 stub.
    """
    _raise_disposition(
        "generate_dataset",
        "Data generator requires PyTorch RNG numerics.",
    )


def hungarian_similarity_loss(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred Hungarian similarity loss.

    Raises:
        NotImplementedError: Always. The loss computes cross-entropy over
            a similarity matrix (Python numerics).
    """
    _raise_disposition(
        "hungarian_similarity_loss",
        "Numeric loss function (cross-entropy over similarity matrix).",
    )


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

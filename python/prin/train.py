"""Rust-native trainable-stack orchestration entry points (WP-027).

Thin Python wrapper around the Rust-native temporal CLEVR-N training
pipeline (`crates/prin-train/src/trainer.rs`: Adam + linear-warmup/cosine
learning-rate schedule + gradient clipping + early stopping). All numerics
run in Rust (Project Plan §4 rule 2, "the Python layer contains no
numerics"); :func:`train_phase_tracker` only converts the Rust result into
Python-facing types (:class:`prin.nn.PhaseTracker`, :class:`TrainingResult`).

This is a narrow, single-model entry point — distinct in scope from the
fair PT-vs-SlotAttention multi-model statistical comparison framework
planned for :mod:`prin.experiments` (Phase 5): that framework is expected to
compose calls like :func:`train_phase_tracker` as one building block among
several, not duplicate its training loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from prin._prin_core import train_phase_tracker as _train_phase_tracker
from prin.nn.phase_tracker import PhaseTracker

if TYPE_CHECKING:
    from prin._prin_core import TrainingResult as _RustTrainingResult

__all__: list[str] = ["TrainingResult", "train_phase_tracker"]


@dataclass(frozen=True)
class TrainingResult:
    """Python-facing mirror of `prin._prin_core.TrainingResult`.

    Attributes:
        final_train_loss: Final epoch's mean training loss.
        final_val_loss: Final (best-restored) validation loss.
        final_val_ip: Final (best-restored) validation identity
            preservation, in ``[0, 1]``.
        best_val_loss: Best smoothed validation loss observed.
        best_epoch: Epoch at which the best smoothed validation loss was
            observed.
        total_epochs: Total epochs actually run (may be less than
            `max_epochs` on early stop).
        train_losses: Per-epoch mean training loss.
        val_losses: Per-epoch validation loss.
        val_ips: Per-epoch validation identity preservation.
    """

    final_train_loss: float
    final_val_loss: float
    final_val_ip: float
    best_val_loss: float
    best_epoch: int
    total_epochs: int
    train_losses: list[float]
    val_losses: list[float]
    val_ips: list[float]

    @staticmethod
    def _from_rust(result: _RustTrainingResult) -> TrainingResult:
        """Convert the Rust-facing result into this dataclass."""
        return TrainingResult(
            final_train_loss=result.final_train_loss,
            final_val_loss=result.final_val_loss,
            final_val_ip=result.final_val_ip,
            best_val_loss=result.best_val_loss,
            best_epoch=result.best_epoch,
            total_epochs=result.total_epochs,
            train_losses=result.train_losses,
            val_losses=result.val_losses,
            val_ips=result.val_ips,
        )


def train_phase_tracker(
    detection_dim: int,
    n_delta: int = 4,
    n_theta: int = 8,
    n_gamma: int = 16,
    n_discrete_steps: int = 5,
    match_threshold: float = 0.3,
    n_objects: int = 4,
    n_frames: int = 20,
    det_dim: int = 4,
    train_seqs: int = 50,
    val_seqs: int = 10,
    dataset_seed: int = 42,
    lr: float = 3e-4,
    weight_decay: float = 0.0,
    max_epochs: int = 100,
    patience: int = 10,
    smoothing_window: int = 5,
    warmup_epochs: int = 5,
    grad_clip: float = 1.0,
    model_seed: int = 0,
) -> tuple[PhaseTracker, TrainingResult]:
    """Construct, train, and validate a :class:`prin.nn.PhaseTracker`.

    Generates temporal CLEVR-N training/validation sequences
    (`crates/prin-train/src/dataset.rs`) and runs the full Rust-native
    training loop end to end. Dataset perturbations (occlusion/swap/
    reversal/noise) are fixed at the PRINet 3.0 reference's defaults
    (disabled), matching the registered validation protocol; callers
    needing perturbed sequences should compose the lower-level Rust API
    directly — a deliberate, documented scope boundary, not a silently
    dropped capability.

    Args:
        detection_dim: Per-detection input feature dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per frame.
        match_threshold: Minimum phase similarity for a valid match.
        n_objects: Objects per generated sequence.
        n_frames: Frames per generated sequence.
        det_dim: Detection feature dimension of the generated dataset
            (independent of `detection_dim` only if you intend a mismatch;
            normally equal).
        train_seqs: Number of training sequences to generate.
        val_seqs: Number of validation sequences to generate.
        dataset_seed: Base seed for dataset generation.
        lr: Base (post-warmup peak) learning rate.
        weight_decay: Adam weight-decay coefficient.
        max_epochs: Maximum training epochs.
        patience: Early-stopping patience, in epochs.
        smoothing_window: Moving-average window for the early-stopping
            validation-loss signal.
        warmup_epochs: Linear-warmup epoch count.
        grad_clip: Gradient-clipping L2-norm threshold.
        model_seed: Seed for the tracker's initial parameters.

    Returns:
        `(trained_tracker, result)`: the trained :class:`prin.nn.PhaseTracker`
        (usable exactly like a freshly-constructed one) and the full
        training history.

    Raises:
        ValueError: If any hyperparameter is invalid.

    Examples:
        >>> from prin.train import train_phase_tracker
        >>> tracker, result = train_phase_tracker(
        ...     4, n_delta=2, n_theta=3, n_gamma=4, n_discrete_steps=2,
        ...     match_threshold=0.1, n_objects=3, n_frames=6,
        ...     train_seqs=4, val_seqs=2, max_epochs=3, patience=3,
        ...     warmup_epochs=1, smoothing_window=2,
        ... )
        >>> 0.0 <= result.final_val_ip <= 1.0
        True
    """
    bridge, rust_result = _train_phase_tracker(
        detection_dim,
        n_delta=n_delta,
        n_theta=n_theta,
        n_gamma=n_gamma,
        n_discrete_steps=n_discrete_steps,
        match_threshold=match_threshold,
        n_objects=n_objects,
        n_frames=n_frames,
        det_dim=det_dim,
        train_seqs=train_seqs,
        val_seqs=val_seqs,
        dataset_seed=dataset_seed,
        lr=lr,
        weight_decay=weight_decay,
        max_epochs=max_epochs,
        patience=patience,
        smoothing_window=smoothing_window,
        warmup_epochs=warmup_epochs,
        grad_clip=grad_clip,
        model_seed=model_seed,
    )
    return PhaseTracker._from_bridge(bridge), TrainingResult._from_rust(rust_result)

"""Rust-backed statistical and adversarial experiment orchestration.

This package exposes deterministic bootstrap/Welch utilities and FGSM/PGD
evaluation over the Rust trainable trackers. Python selects an experiment and
passes configuration; all statistics, attacks, and metric computation execute
in ``prin._prin_core``.
"""

from __future__ import annotations

from prin._prin_core import (
    AdversarialEvalResult,
    BootstrapCi,
    WelchTTest,
    cohens_d,
    compute_p_value,
)
from prin._prin_core import (
    py_adversarial_evaluate_phase_tracker as _adversarial_evaluate_phase_tracker,
)
from prin._prin_core import (
    py_adversarial_evaluate_slot_attention as _adversarial_evaluate_slot_attention,
)
from prin._prin_core import py_bootstrap_ci as bootstrap_ci
from prin._prin_core import py_welch_t_test as welch_t_test
from prin.nn.phase_tracker import PhaseTracker
from prin.nn.slot_attention import TemporalSlotAttentionMOT

__all__: list[str] = [
    "AdversarialEvalResult",
    "BootstrapCi",
    "WelchTTest",
    "adversarial_evaluate_phase_tracker",
    "adversarial_evaluate_slot_attention",
    "bootstrap_ci",
    "cohens_d",
    "compute_p_value",
    "welch_t_test",
]


def adversarial_evaluate_phase_tracker(
    tracker: PhaseTracker,
    epsilon: float,
    attack: str = "fgsm",
    pgd_steps: int = 20,
    n_sequences: int = 4,
    n_objects: int = 4,
    n_frames: int = 20,
    detection_dim: int = 4,
    seed: int = 0,
) -> AdversarialEvalResult:
    """Evaluate a phase tracker on deterministic synthetic attacks.

    Args:
        tracker: Phase-based tracker to evaluate.
        epsilon: L-infinity perturbation budget. Must be positive.
        attack: ``"fgsm"`` or ``"pgd"``.
        pgd_steps: PGD iteration count; ignored for FGSM.
        n_sequences: Number of deterministic synthetic sequences.
        n_objects: Objects per sequence.
        n_frames: Frames per sequence.
        detection_dim: Per-detection feature dimension. Must match ``tracker``.
        seed: Counter used for dataset generation and attack randomness.

    Returns:
        Clean/adversarial identity preservation and per-sequence values.

    Raises:
        ValueError: If any configuration value is invalid.
    """
    return _adversarial_evaluate_phase_tracker(
        tracker._bridge,
        epsilon,
        attack,
        pgd_steps,
        n_sequences,
        n_objects,
        n_frames,
        detection_dim,
        seed,
    )


def adversarial_evaluate_slot_attention(
    tracker: TemporalSlotAttentionMOT,
    epsilon: float,
    attack: str = "fgsm",
    pgd_steps: int = 20,
    n_sequences: int = 4,
    n_objects: int = 4,
    n_frames: int = 20,
    detection_dim: int = 4,
    seed: int = 0,
) -> AdversarialEvalResult:
    """Evaluate a temporal Slot Attention tracker under FGSM or PGD.

    Args:
        tracker: Slot Attention tracking baseline to evaluate.
        epsilon: L-infinity perturbation budget. Must be positive.
        attack: ``"fgsm"`` or ``"pgd"``.
        pgd_steps: PGD iteration count; ignored for FGSM.
        n_sequences: Number of deterministic synthetic sequences.
        n_objects: Objects per sequence.
        n_frames: Frames per sequence.
        detection_dim: Per-detection feature dimension. Must match ``tracker``.
        seed: Counter used for dataset generation and attack randomness.

    Returns:
        Clean/adversarial identity preservation and per-sequence values.

    Raises:
        ValueError: If any configuration value is invalid.
    """
    return _adversarial_evaluate_slot_attention(
        tracker._bridge,
        epsilon,
        attack,
        pgd_steps,
        n_sequences,
        n_objects,
        n_frames,
        detection_dim,
        seed,
    )

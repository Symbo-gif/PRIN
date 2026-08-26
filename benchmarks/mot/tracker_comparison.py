"""PhaseTracker vs. TemporalSlotAttentionMOT: clean identity preservation and
per-call wall time on deterministic synthetic sequences.

Rust-backed successor to PRINet 3.0's `clevr_n.py` (CLEVR-N binding capacity)
and `run_clevr_n_sweep.py`. The clean (unperturbed) identity-preservation
score and its synthetic input sequences come entirely from
`prin.experiments.adversarial_evaluate_*`, already parity-dispositioned in
WP-031/WP-032 -- this module runs no synthetic-data generation or tracking
numerics itself, only timing and comparison.
"""

from __future__ import annotations

from typing import Any

from prin.experiments import (
    AdversarialEvalResult,
    adversarial_evaluate_phase_tracker,
    adversarial_evaluate_slot_attention,
)
from prin.nn.phase_tracker import PhaseTracker
from prin.nn.slot_attention import TemporalSlotAttentionMOT

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_DETECTION_DIM = 4
_DEFAULT_N_SEQUENCES = 4
_DEFAULT_N_OBJECTS = 4
_DEFAULT_N_FRAMES = 10
_DEFAULT_EPSILON = 0.01


def _phase_tracker_run(
    detection_dim: int,
    n_sequences: int,
    n_objects: int,
    n_frames: int,
    epsilon: float,
    seed: int,
) -> AdversarialEvalResult:
    tracker = PhaseTracker(detection_dim, seed_counter=seed, seed_key=0)
    return adversarial_evaluate_phase_tracker(
        tracker,
        epsilon,
        attack="fgsm",
        n_sequences=n_sequences,
        n_objects=n_objects,
        n_frames=n_frames,
        detection_dim=detection_dim,
        seed=seed,
    )


def _slot_attention_run(
    detection_dim: int,
    n_sequences: int,
    n_objects: int,
    n_frames: int,
    epsilon: float,
    seed: int,
) -> AdversarialEvalResult:
    tracker = TemporalSlotAttentionMOT(detection_dim, seed_counter=seed, seed_key=0)
    return adversarial_evaluate_slot_attention(
        tracker,
        epsilon,
        attack="fgsm",
        n_sequences=n_sequences,
        n_objects=n_objects,
        n_frames=n_frames,
        detection_dim=detection_dim,
        seed=seed,
    )


@register(
    "mot",
    "tracker_comparison",
    summary="PhaseTracker vs. TemporalSlotAttentionMOT: clean IP, per-call wall time",
)
def tracker_identity_preservation(config: BenchmarkConfig) -> dict[str, Any]:
    """Compare both tracker families' clean identity preservation and timing.

    ``config.params`` may override ``detection_dim``, ``n_sequences``,
    ``n_objects``, ``n_frames``, and ``epsilon``.
    """
    detection_dim = int(config.params.get("detection_dim", _DEFAULT_DETECTION_DIM))
    n_sequences = int(config.params.get("n_sequences", _DEFAULT_N_SEQUENCES))
    n_objects = int(config.params.get("n_objects", _DEFAULT_N_OBJECTS))
    n_frames = int(config.params.get("n_frames", _DEFAULT_N_FRAMES))
    epsilon = float(config.params.get("epsilon", _DEFAULT_EPSILON))
    seed = config.seed_counter

    trackers: dict[str, Any] = {}
    for name, run_fn in (
        ("phase_tracker", _phase_tracker_run),
        ("slot_attention", _slot_attention_run),
    ):
        stats, result = timed_run(
            lambda run_fn=run_fn: run_fn(
                detection_dim, n_sequences, n_objects, n_frames, epsilon, seed
            ),
            iterations=config.iterations,
            warmup=config.warmup,
        )
        trackers[name] = {
            "clean_identity_preservation": result.clean_ip,
            "per_sequence_clean_ip": result.per_seq_clean,
            "timing": stats.to_dict(),
        }

    return {
        "benchmark": "mot_tracker_comparison",
        "backend": "host CPU",
        "dtype": "f64",
        "detection_dim": detection_dim,
        "n_sequences": n_sequences,
        "n_objects": n_objects,
        "n_frames": n_frames,
        "trackers": trackers,
    }

"""FGSM/PGD robustness: clean vs. adversarial identity-preservation degradation
for both tracker families.

Rust-backed successor to PRINet 3.0's `y4q1_8_benchmarks.py` and
`run_q18_individual.py`.
"""

from __future__ import annotations

from typing import Any

from prin.experiments import (
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
_DEFAULT_EPSILON = 0.05
_DEFAULT_PGD_STEPS = 10
_ATTACKS: tuple[str, ...] = ("fgsm", "pgd")


@register(
    "adversarial",
    "robustness",
    summary="FGSM/PGD clean-vs-adv identity preservation, both tracker families",
)
def adversarial_robustness(config: BenchmarkConfig) -> dict[str, Any]:
    """Run FGSM and PGD attacks against both tracker families.

    ``config.params`` may override ``detection_dim``, ``n_sequences``,
    ``n_objects``, ``n_frames``, ``epsilon``, and ``pgd_steps``.
    """
    detection_dim = int(config.params.get("detection_dim", _DEFAULT_DETECTION_DIM))
    n_sequences = int(config.params.get("n_sequences", _DEFAULT_N_SEQUENCES))
    n_objects = int(config.params.get("n_objects", _DEFAULT_N_OBJECTS))
    n_frames = int(config.params.get("n_frames", _DEFAULT_N_FRAMES))
    epsilon = float(config.params.get("epsilon", _DEFAULT_EPSILON))
    pgd_steps = int(config.params.get("pgd_steps", _DEFAULT_PGD_STEPS))
    seed = config.seed_counter

    tracker_runs = {
        "phase_tracker": (
            PhaseTracker(detection_dim, seed_counter=seed, seed_key=0),
            adversarial_evaluate_phase_tracker,
        ),
        "slot_attention": (
            TemporalSlotAttentionMOT(detection_dim, seed_counter=seed, seed_key=0),
            adversarial_evaluate_slot_attention,
        ),
    }

    trackers: dict[str, Any] = {}
    for tracker_name, (tracker, evaluate_fn) in tracker_runs.items():
        attacks: dict[str, Any] = {}
        for attack in _ATTACKS:
            stats, result = timed_run(
                lambda tracker=tracker, evaluate_fn=evaluate_fn, attack=attack: (
                    evaluate_fn(
                        tracker,
                        epsilon,
                        attack=attack,
                        pgd_steps=pgd_steps,
                        n_sequences=n_sequences,
                        n_objects=n_objects,
                        n_frames=n_frames,
                        detection_dim=detection_dim,
                        seed=seed,
                    )
                ),
                iterations=config.iterations,
                warmup=config.warmup,
            )
            attacks[attack] = {
                "clean_identity_preservation": result.clean_ip,
                "adversarial_identity_preservation": result.adv_ip,
                "degradation": result.degradation,
                "timing": stats.to_dict(),
            }
        trackers[tracker_name] = attacks

    return {
        "benchmark": "adversarial_robustness",
        "backend": "host CPU",
        "dtype": "f64",
        "detection_dim": detection_dim,
        "n_sequences": n_sequences,
        "n_objects": n_objects,
        "n_frames": n_frames,
        "epsilon": epsilon,
        "pgd_steps": pgd_steps,
        "trackers": trackers,
    }

"""Ablation variant comparison: Rust-owned state size, identity preservation,
and per-call wall time for each structural ablation vs. its full baseline.

Rust-backed successor to PRINet 3.0's `q4_benchmarks.py` (`run_ablation`,
`run_adaptive_control`) and `run_q17_individual.py`. Detection sequences are
a fixed deterministic function of frame/object index (no RNG), so identity
preservation differences reflect only the structural ablation, not sampling.
"""

from __future__ import annotations

import math
from typing import Any

import torch
from prin.dynamics import Seed
from prin.nn.ablation import (
    PhaseTrackerFrozen,
    PhaseTrackerStatic,
    SlotAttentionFrozen,
    SlotAttentionNoGRU,
)
from prin.nn.phase_tracker import PhaseTracker
from prin.nn.slot_attention import TemporalSlotAttentionMOT

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

#: Slot-attention variants take an extra `Seed` and return a plain tuple
#: (`slot_history, identity_matches, identity_preservation,
#: per_frame_similarity`) instead of a `TrackingResult`; PhaseTracker
#: variants return `TrackingResult` and need no `Seed` argument.
_SLOT_ATTENTION_VARIANTS = (
    "slot_attention_full",
    "slot_attention_frozen",
    "slot_attention_no_gru",
)

_DEFAULT_DETECTION_DIM = 4
_DEFAULT_N_OBJECTS = 4
_DEFAULT_N_FRAMES = 8


def _deterministic_sequence(
    n_frames: int, n_objects: int, detection_dim: int
) -> list[torch.Tensor]:
    """A fixed, RNG-free detection sequence: distinct, slowly-drifting objects."""
    return [
        torch.tensor(
            [
                [math.sin(0.3 * f + obj + d) for d in range(detection_dim)]
                for obj in range(n_objects)
            ],
            dtype=torch.float64,
        )
        for f in range(n_frames)
    ]


def _state_size_bytes(module: Any) -> int:
    """Size of the Rust-owned serialized state.

    All parameters live in the Rust bridge, not as `torch.nn.Parameter`
    (gradients flow through a custom `torch.autograd.Function`, not
    parameter registration) -- `module.parameters()` is always empty for
    every one of these classes, so `rust_state_dict()`'s byte length is the
    only available real size proxy, not an invented substitute.
    """
    return len(module.rust_state_dict())


def _measure(
    name: str, module: torch.nn.Module, frames: list[torch.Tensor], seed: Seed
) -> tuple[int, float]:
    if name in _SLOT_ATTENTION_VARIANTS:
        _, _, identity_preservation, _ = module.track_sequence(frames, seed)
    else:
        identity_preservation = module.track_sequence(frames).identity_preservation
    return _state_size_bytes(module), identity_preservation


@register(
    "ablations",
    "variant_comparison",
    summary="State size/identity preservation/wall time: ablated vs. full trackers",
)
def ablation_variant_comparison(config: BenchmarkConfig) -> dict[str, Any]:
    """Compare each structural ablation to its full-baseline tracker.

    ``config.params`` may override ``detection_dim``, ``n_objects``, and
    ``n_frames``.
    """
    detection_dim = int(config.params.get("detection_dim", _DEFAULT_DETECTION_DIM))
    n_objects = int(config.params.get("n_objects", _DEFAULT_N_OBJECTS))
    n_frames = int(config.params.get("n_frames", _DEFAULT_N_FRAMES))
    seed_counter = config.seed_counter

    frames = _deterministic_sequence(n_frames, n_objects, detection_dim)
    track_seed = Seed(config.seed_counter, config.seed_key)

    variants: dict[str, torch.nn.Module] = {
        "phase_tracker_full": PhaseTracker(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
        "phase_tracker_frozen": PhaseTrackerFrozen(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
        "phase_tracker_static": PhaseTrackerStatic(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
        "slot_attention_full": TemporalSlotAttentionMOT(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
        "slot_attention_frozen": SlotAttentionFrozen(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
        "slot_attention_no_gru": SlotAttentionNoGRU(
            detection_dim, seed_counter=seed_counter, seed_key=0
        ),
    }

    results: dict[str, Any] = {}
    for name, module in variants.items():
        stats, (state_size_bytes, identity_preservation) = timed_run(
            lambda name=name, module=module: _measure(name, module, frames, track_seed),
            iterations=config.iterations,
            warmup=config.warmup,
        )
        results[name] = {
            "state_size_bytes": state_size_bytes,
            "identity_preservation": identity_preservation,
            "timing": stats.to_dict(),
        }

    return {
        "benchmark": "ablation_variant_comparison",
        "backend": "host CPU",
        "dtype": "f64",
        "detection_dim": detection_dim,
        "n_objects": n_objects,
        "n_frames": n_frames,
        "variants": results,
    }

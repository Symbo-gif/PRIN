"""Rust-backed multi-object tracking and temporal evaluation utilities.

The orchestration surface combines ``prin-daemon`` CLEAR-MOT/IDF1 metrics with
``prin-train`` temporal identity metrics without introducing a dependency
between those sibling Rust crates. All numerical work remains in
``prin._prin_core``.
"""

from __future__ import annotations

from prin._prin_core import (
    MotAccumulator,
    MotSummary,
    TemporalMetrics,
    binding_robustness_score,
    identity_overcount,
    identity_switches,
    iou_distance_matrix,
    mostly_tracked_lost,
    recovery_speed,
    temporal_smoothness,
    track_duration_stats,
    track_fragmentation_rate,
)
from prin._prin_core import (
    py_compute_full_temporal_metrics as compute_full_temporal_metrics,
)

__all__: list[str] = [
    "MotAccumulator",
    "MotSummary",
    "TemporalMetrics",
    "binding_robustness_score",
    "compute_full_temporal_metrics",
    "identity_overcount",
    "identity_switches",
    "iou_distance_matrix",
    "mostly_tracked_lost",
    "recovery_speed",
    "temporal_smoothness",
    "track_duration_stats",
    "track_fragmentation_rate",
]

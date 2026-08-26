"""``ablations``: structural ablation variants (frozen/static/no-GRU, adaptive
allocation).

Consolidates PRINet 3.0's `q4_benchmarks.py` (`run_ablation`,
`run_adaptive_control`) and `run_q17_individual.py`. See
`DOCS/baselines/wp033_benchmark_traceability.md`.

Measurement uses the Rust-backed ablation bridges in `prin.nn.ablation`
(`PhaseTrackerFrozen`/`PhaseTrackerStatic`/`SlotAttentionFrozen`/
`SlotAttentionNoGRU`); this module performs no tracking numerics itself.
"""

from __future__ import annotations

from benchmarks.ablations import variant_comparison

__all__ = ["variant_comparison"]

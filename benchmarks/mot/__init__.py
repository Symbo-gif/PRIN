"""``mot``: multi-object tracking (PhaseTracker vs. SlotAttention).

Consolidates PRINet 3.0's `clevr_n.py`, `run_clevr_n_sweep.py`, and the MOT
halves of the `y2q*`/`y3q*`/`y4q1_4`-`y4q1_9` quarterly suites. See
`DOCS/baselines/wp033_benchmark_traceability.md`.

Measurement reuses `prin.experiments.adversarial_evaluate_{phase_tracker,
slot_attention}`, which already generates its deterministic synthetic MOT
sequences and computes clean/adversarial identity preservation entirely in
Rust (`prin._prin_core`); this module adds no synthetic-data generation or
tracking numerics of its own.
"""

from __future__ import annotations

from benchmarks.mot import tracker_comparison

__all__ = ["tracker_comparison"]

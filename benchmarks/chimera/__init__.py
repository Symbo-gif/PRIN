"""``chimera``: chimera phase diagrams and metrics.

Consolidates PRINet 3.0's `phase_diagram.py`, `desync_catastrophe.py`,
`phase1_statistical_hardening.py`, `y4q1_benchmarks.py`, and
`y4q1_2_benchmarks.py`/`y4q1_3_benchmarks.py`'s chimera-state deepening. See
`DOCS/baselines/wp033_benchmark_traceability.md`.

All measurement is `prin.dynamics`/`prin.metrics`-backed (`KuramotoOscillator`,
`Topology`, `chimera_index`, `strength_of_incoherence`, `metastability`);
this module performs no numerics of its own.
"""

from __future__ import annotations

from benchmarks.chimera import phase_diagram

__all__ = ["phase_diagram"]

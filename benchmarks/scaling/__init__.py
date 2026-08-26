"""``scaling``: oscillator-count scaling and sweep throughput.

Consolidates PRINet 3.0's `oscillator_scaling.py`, `on_stress_benchmark.py`,
`on_vs_onlogn_benchmark.py`, `pairwise_coupling_scaling.py`,
`coupling_complexity_benchmark.py`, `scientific_coupling_benchmark.py`,
`goldilocks_sustained_benchmark.py`/`_cpu_benchmark.py`,
`phase2_scaling_analysis.py`, and `gpu_benchmarks.py`'s oscillator-scaling
half. See `DOCS/baselines/wp033_benchmark_traceability.md`.

All measurement is `prin.dynamics`-backed (`KuramotoOscillator`,
`OscillatorState`, `RK4Integrator`, `kuramoto_order_parameter`); this module
performs no numerics of its own.
"""

from __future__ import annotations

from benchmarks.scaling import coupling_complexity, oscillator_count

__all__ = ["coupling_complexity", "oscillator_count"]

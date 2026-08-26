"""``integrators``: integrator accuracy/cost (RK45, exponential, multi-rate).

PRINet 3.0's benchmark suite has no script whose primary topic is
integrator accuracy/cost in this sense (RK45/exponential/multi-rate are
PRIN-native constructs built in Phase 2); `multirate_triton_benchmark.py` is
the closest secondary reference (multi-rate *kernel* timing, tracked under
`kernels/` instead). This is recorded as a finding in
`DOCS/baselines/wp033_benchmark_traceability.md` rather than silently
assigning a legacy row here.

All measurement is `prin.dynamics`-backed (`EulerIntegrator`, `RK4Integrator`,
`RK45Integrator`, `ExponentialIntegrator`, `MultiRateIntegrator`); this module
performs no numerics of its own.
"""

from __future__ import annotations

from benchmarks.integrators import accuracy_cost

__all__ = ["accuracy_cost"]

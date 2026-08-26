# benchmarks/integrators/ (integrator accuracy/cost)

Wall time and final-state agreement across Euler, RK4, adaptive RK45,
exponential, and multi-rate integrators on the same mean-field Kuramoto
system (WP-033).

## No legacy predecessor

No PRINet 3.0 benchmark script has integrator accuracy/cost in this sense as
its primary topic — RK45/exponential/multi-rate integrators are PRIN-native
constructs built in Phase 2 (`crates/prin-dynamics`), absent from the 3.0
suite in this form. See `DOCS/baselines/wp033_benchmark_traceability.md` for
the full accounting; this category is still implemented (nine topic
categories are required, not eight), just with no legacy row pointing to it.

## Contents

- `accuracy_cost.py` — `integrator_accuracy_cost`: times Euler/RK4/
  exponential/multi-rate `integrate`/`integrate_fixed` and adaptive RK45
  `integrate_adaptive`, and reports each integrator's final order-parameter
  agreement against a tight-tolerance (`rtol=1e-10`) RK45 reference —
  "accuracy" here is agreement with that Rust-computed reference, not an
  independent numerical implementation.

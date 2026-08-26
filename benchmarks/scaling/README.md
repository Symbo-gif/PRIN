# benchmarks/scaling/ (oscillator-count scaling and sweep throughput)

Wall time, throughput, and final order parameter across oscillator counts
and coupling modes (WP-033). Consolidates 10 PRINet 3.0 legacy scripts — see
`DOCS/baselines/wp033_benchmark_traceability.md` for the full mapping.

## Contents

- `oscillator_count.py` — `oscillator_count_scaling`: wall time/throughput/R
  vs. N for mean-field Kuramoto. Schema-compatible with the legacy
  `benchmark_y4q1_ring_scaling.json` field names (`N`, `wall_time_s`,
  `throughput`, `final_order_param`).
- `coupling_complexity.py` — `coupling_complexity_scaling`: wall time vs. N
  for `mean_field`/`sparse_knn`/`full` coupling modes (O(N) vs. O(N log N)
  vs. O(N²) asymptotic comparison).

All measurement is `prin.dynamics`-backed (`KuramotoOscillator`,
`OscillatorState`, `RK4Integrator`, `prin.metrics.kuramoto_order_parameter`).

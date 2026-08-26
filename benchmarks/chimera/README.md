# benchmarks/chimera/ (chimera phase diagrams and metrics)

Order parameter, chimera index, strength of incoherence, and metastability
across a coupling-strength sweep (WP-033). Consolidates 6 PRINet 3.0 legacy
scripts — see `DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `phase_diagram.py` — `phase_diagram_sweep`: sweeps coupling strength K over
  a sparse-k-NN ring Kuramoto system and reports R, chimera index, strength
  of incoherence, and metastability at each point.

All measurement is `prin.dynamics`/`prin.metrics`-backed (`KuramotoOscillator`,
`chimera_index`, `strength_of_incoherence`, `metastability`,
`build_phase_knn`).

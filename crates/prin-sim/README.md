# prin-sim

OscilloSim sparse simulation engine for PRIN: CSR sparse coupling, chimera detection,
pruning, and integration orchestration for large oscillator systems.

Rebuild target for PRINet 3.0 `utils/oscillosim.py` and
`core/propagation/sweep_utils.py`. Phase 2, WP-015.

## Modules

- **`csr_coupling`** — [`SparseCoupling`]: Compressed Sparse Row (CSR) coupling matrix
  representation with $O(\mathrm{nnz})$ SpMV-based Kuramoto (sine/cosine trig decomposition)
  and Stuart–Landau (diffusive linear) coupling computations. Factory builders for
  all-to-all, k-nearest-neighbor ring, and small-world topologies with $K/\mathrm{degree}$
  energy normalization and memory tracking (`memory_bytes()`).
- **`engine`** — [`OscilloSim`] simulation engine coordinating oscillator state, sparse dynamics
  ([`SparseKuramoto`], [`SparseStuartLandau`]), integration (`integrate_fixed`), step-by-step
  simulation (`step()`), and trajectory recording (`Trajectory`). Enforces numerical guards
  ([`apply_guards`]) and zero hidden RNG state via `prin_dynamics::Seed`.
- **`pruning`** — [`PruningStrategy`] and [`PruningResult`] implementing amplitude-threshold
  dynamic oscillator pruning. Provides forward index mapping (`pruned_to_original`,
  `original_to_pruned`) and lossless/sub-network state restoration (`restore()`) with
  configurable default amplitude.
- **`chimera`** — [`ChimeraMetrics`], [`compute_chimera_metrics`], and [`trajectory_chimera_metrics`]
  integrating CSR neighbor sparsity directly with `prin-metrics` chimera measures (local order
  parameter, bimodality index, strength of incoherence, discontinuity measure, chimera index).
- **`error`** — Typed [`SimError`] enum (10 variants) covering dimension mismatches, index bounds,
  invalid parameters, empty systems, non-finite values, and pruning failures.

## Numerics and Parity

All sparse coupling and engine computations run in `f64`. Single-runtime parity with dense
dynamics models (`KuramotoOscillator`, `StuartLandauOscillator`) is verified across small,
medium, and large $N$ ($N \in \{8, 64, 256\}$ for Kuramoto, $N \in \{8, 16\}$ for Stuart–Landau)
at numerical tolerances `rtol = 1e-10` to `1e-12` (`tests/parity_sparse_vs_dense.rs`).
Property tests (`tests/proptest_properties.rs`) verify arbitrary-$N$ equivalence, memory footprint,
and deterministic repeatability under `proptest`.

## PRINet 3.0 Migration Notes

- `prinet.utils.oscillosim.OscilloSim` → `prin_sim::OscilloSim` + `prin_sim::SparseCoupling`.
- Sparse coupling uses strict CSR storage with $O(\mathrm{nnz})$ evaluation rather than dense
  tensor operations masked by adjacency matrices.
- Dynamic pruning replaces Python-level array indexing with explicit `PruningStrategy` and
  `PruningResult` forward/inverse mappings and configurable `default_amplitude`.
- Python bindings and parallel parameter sweep orchestration are deferred to WP-016.

## Dependencies

- `prin-dynamics` — `OscillatorState`, `StateDerivatives`, `Dynamics`, `Integrator`, `Seed`
- `prin-metrics` — Chimera analysis functions and thresholds
- `serde` — Serialization support for configuration and trajectory records


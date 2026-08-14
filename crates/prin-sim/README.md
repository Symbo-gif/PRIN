# prin-sim

OscilloSim sparse simulation engine for PRIN: CSR sparse coupling, chimera detection,
pruning, integration orchestration, parallel parameter sweeps, and CPU dispatch for
large oscillator systems.

Rebuild target for PRINet 3.0 `utils/oscillosim.py` and
`core/propagation/sweep_utils.py`. Phase 2, WP-015 (engine) and WP-016 (sweeps, dispatch).

## Modules

- **`csr_coupling`** — [`SparseCoupling`]: Compressed Sparse Row (CSR) coupling matrix
  representation with $O(\mathrm{nnz})$ SpMV-based Kuramoto (sine/cosine trig decomposition)
  and Stuart–Landau (diffusive linear) coupling computations. Factory builders for
  all-to-all, k-nearest-neighbor ring, and small-world topologies with $K/\mathrm{degree}$
  energy normalization and memory tracking (`memory_bytes()`). Size-gated CPU dispatch
  via the `dispatch` module (sequential reference below threshold, rayon-parallel above).
- **`engine`** — [`OscilloSim`] simulation engine coordinating oscillator state, sparse dynamics
  ([`SparseKuramoto`], [`SparseStuartLandau`]), integration (`integrate_fixed`), step-by-step
  simulation (`step()`), and trajectory recording (`Trajectory`). Enforces numerical guards
  ([`apply_guards`]) and zero hidden RNG state via `prin_dynamics::Seed`. Models share their
  `SparseCoupling` via `Arc` to avoid deep-cloning the CSR storage per sweep configuration.
- **`sweep`** — [`run_sweep`], [`SweepConfig`], [`SweepResult`], [`SweepAxis`], [`SweepModel`],
  and [`detect_oscillation`]: rayon-parallel parameter sweeps over coupling strength, decay
  rate, frequency adaptation, and bifurcation axes with deterministic per-config seeding.
  Oscillation detection uses windowed variance on the order-parameter history, reusing
  `prin_metrics::order::kuramoto_order_parameter` (one algorithm, one implementation).
- **`pruning`** — [`PruningStrategy`] and [`PruningResult`] implementing amplitude-threshold
  dynamic oscillator pruning. Provides forward index mapping (`pruned_to_original`,
  `original_to_pruned`) and lossless/sub-network state restoration (`restore()`) with
  configurable default amplitude.
- **`chimera`** — [`ChimeraMetrics`], [`compute_chimera_metrics`], and [`trajectory_chimera_metrics`]
  integrating CSR neighbor sparsity directly with `prin-metrics` chimera measures (local order
  parameter, bimodality index, strength of incoherence, discontinuity measure, chimera index).
- **`dispatch`** (crate-private) — Size-gated sequential/parallel CPU dispatch
  (`map_dispatch`, `zip_map_dispatch`) with `PARALLEL_LEN_THRESHOLD = 32,768`. Sequential
  reference path below threshold; rayon-parallel path at or above. Eliminates the
  thread-pool overhead on small problem sizes while scaling to available cores on large ones.
- **`error`** — Typed [`SimError`] enum (10 variants) covering dimension mismatches, index bounds,
  invalid parameters, empty systems, non-finite values, and pruning failures.

## Numerics and Parity

All sparse coupling and engine computations run in `f64`. Single-runtime parity with dense
dynamics models (`KuramotoOscillator`, `StuartLandauOscillator`) is verified across small,
medium, and large $N$ ($N \in \{8, 64, 256\}$ for Kuramoto, $N \in \{8, 16\}$ for Stuart–Landau)
at numerical tolerances `rtol = 1e-10` to `1e-12` (`tests/parity_sparse_vs_dense.rs`).
Property tests (`tests/proptest_properties.rs`) verify arbitrary-$N$ equivalence, memory footprint,
and deterministic repeatability under `proptest`.

Large-$N$ evidence: $N = 100{,}000$ deterministic regression test (bit-identical across runs,
finite phases/amplitudes, order parameter $\in [0,1]$, coupling memory $< 20\,\mathrm{MB}$).
$N = 1{,}000{,}000$ exercised as benchmark evidence (`sweep_bench.rs`: `kuramoto_coupling`
31.7 ms parallel, `engine.step()` 218 ms parallel). Full dense-vs-sparse parity at $N = 1\mathrm{M}$
is mathematically infeasible ($\sim 8\,\mathrm{TB}$ dense matrix); derivative-level dense parity
is evidenced by the $N \leq 256$ tests.

`detect_oscillation` parity with PRINet 3.0 `sweep_utils.detect_oscillation` is verified across
384 combinations (8 histories × 8 windows × 6 thresholds) in `tests/parity_detect_oscillation.rs`.

## Performance

Criterion benchmarks (`benches/sweep_bench.rs`) include in-process serial baselines
(dedicated 1-thread `rayon::ThreadPool`) alongside parallel variants for every size.
Sweep workload: $N = 4096$, 300 steps, 4–64 configurations. SpMV/engine: up to $N = 1{,}000{,}000$.

Peak sweep speedup: ~3.9× at 8 configs (8 physical cores), meeting the amended ≥3.5×
target (plan amendment #21). SpMV/engine parallel-vs-serial: 1.3–1.5× at $N = 65{,}536$–$1{,}000{,}000$.

## PRINet 3.0 Migration Notes

- `prinet.utils.oscillosim.OscilloSim` → `prin_sim::OscilloSim` + `prin_sim::SparseCoupling`.
- `prinet.core.propagation.sweep_utils.sweep_coupling_params` → `prin_sim::sweep::run_sweep`.
- `prinet.core.propagation.sweep_utils.detect_oscillation` → `prin_sim::sweep::detect_oscillation`.
- Sparse coupling uses strict CSR storage with $O(\mathrm{nnz})$ evaluation rather than dense
  tensor operations masked by adjacency matrices.
- Dynamic pruning replaces Python-level array indexing with explicit `PruningStrategy` and
  `PruningResult` forward/inverse mappings and configurable `default_amplitude`.
- Python bindings (`prin-py` sweep/engine exposure) are deferred to a future WP (plan
  amendment #20).

## Dependencies

- `prin-dynamics` — `OscillatorState`, `StateDerivatives`, `Dynamics`, `Integrator`, `Seed`
- `prin-metrics` — `kuramoto_order_parameter`, chimera analysis functions and thresholds
- `sprs` — CSR sparse matrix storage
- `rayon` — Parallel sweep dispatch
- `serde` — Serialization support for configuration and trajectory records


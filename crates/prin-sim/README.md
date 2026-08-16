# prin-sim

OscilloSim sparse simulation engine for PRIN: CSR sparse coupling, chimera detection,
pruning, integration orchestration, parallel parameter sweeps, CPU dispatch, and GPU kernel
integration for large oscillator systems.

Rebuild target for PRINet 3.0 `utils/oscillosim.py` and
`core/propagation/sweep_utils.py`. Phase 2, WP-015 (engine), WP-016 (sweeps, dispatch),
and Phase 3, WP-021 (GPU integration).

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
- **`gpu`** (gated on `cpu`, `cuda`, or `wgpu` features) — GPU kernel integration wrapping
  `prin-kernels` CubeCL dispatch into simulation-layer components:
  - [`GpuSparseKuramoto`] — `Dynamics` implementation dispatching sparse Kuramoto coupling
    derivatives to `prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto` while reusing
    existing CSR storage. Validates uniform $K/\mathrm{degree}$ weights at construction.
  - [`GpuMeanFieldEngine`] — Fused dense all-to-all RK4 stepper wrapping
    `prin_kernels::mean_field_rk4::cubecl::step_auto` with trajectory recording.
  - [`GpuBandStepper`] — Fused three-band (delta/theta/gamma) discrete-time stepper wrapping
    `prin_kernels::discrete_step::cubecl::discrete_step_auto`.
  - Boundary conversions: `f64` at the simulation/dynamics layer $\leftrightarrow$ `f32` in
    device kernels.
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
- **`error`** — Typed [`SimError`] enum (13 variants) covering dimension mismatches, index bounds,
  invalid parameters, empty systems, non-finite values, pruning failures, and wrapped
  `prin-kernels` kernel errors (`MeanFieldKernel`, `DiscreteStepKernel`, `SparseKnnKernel`).

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

GPU integration benchmarks (`benches/gpu_bench.rs`, CUDA on RTX 4060):
- Mean-field RK4 at $N = 1{,}000{,}000$: `GpuMeanFieldEngine` fused single-launch-sequence RK4
  measures ~32 ms vs CPU dynamics reference ~192 ms (~5.9× speedup).
- Sparse Kuramoto at $N = 16{,}000, k = 14$: `GpuSparseKuramoto` measures ~5.6–7.0 ms vs CPU SpMV
  ~3.6 ms (unpooled per-stage buffer allocation dominates at this scale; pooled execution is a candidate
  future performance optimization).

## PRINet 3.0 Migration Notes

- `prinet.utils.oscillosim.OscilloSim` → `prin_sim::OscilloSim` + `prin_sim::SparseCoupling`.
- `prinet.core.propagation.sweep_utils.sweep_coupling_params` → `prin_sim::sweep::run_sweep`.
- `prinet.core.propagation.sweep_utils.detect_oscillation` → `prin_sim::sweep::detect_oscillation`.
- Sparse coupling uses strict CSR storage with $O(\mathrm{nnz})$ evaluation rather than dense
  tensor operations masked by adjacency matrices.
- Dynamic pruning replaces Python-level array indexing with explicit `PruningStrategy` and
  `PruningResult` forward/inverse mappings and configurable `default_amplitude`.
- Python bindings (`prin-py` sweep/engine exposure) are deferred to Phase 6 WP-036 (plan
  amendment #20).

## Dependencies

- `prin-dynamics` — `OscillatorState`, `StateDerivatives`, `Dynamics`, `Integrator`, `Seed`
- `prin-metrics` — `kuramoto_order_parameter`, chimera analysis functions and thresholds
- `prin-kernels` (optional, under `cpu`/`cuda`/`wgpu`) — CubeCL single-source GPU kernels
- `sprs` — CSR sparse matrix storage
- `rayon` — Parallel sweep dispatch
- `serde` — Serialization support for configuration and trajectory records


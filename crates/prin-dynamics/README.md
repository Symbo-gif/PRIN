# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state (struct-of-arrays),
deterministic counter-based PRNG authority (`Seed`), numerical guards and clamps,
Kuramoto / Stuart–Landau / Hopf models, Euler / RK4 / RK45 integrators,
exponential (direct/Krylov) and multi-rate sub-stepped integrators,
phase–amplitude coupling, and coupling topologies. Continuous hierarchical band
networks and temporal propagation are planned for Phase 2 (WP-013).

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

## Modules Implemented (WP-006, WP-007, WP-008, WP-009, WP-012)

- **`state`**: Struct-of-arrays `OscillatorState` (`phase`, `amplitude`, `frequency`, optional `freq_band`), phase wrapping to `[0, 2π)`, `atan2`-safe phase differences, amplitude and derivative clamps/guards, and sort-based phase k-NN indexing. WP-007 adds `StateDerivatives` (`dphase`, `damplitude`, `dfrequency`) with length validation and derivative guards honoring `strict-checks`.
- **`seed`**: Counter-based deterministic `Seed` authority (`Pcg64` with `(counter, key)` stream identity, `jump`, bounded range draw, `RngCore` integration).
- **`errors`**: Typed error enumerations `StateError` and `SeedError` built with `thiserror`.
- **`models`** (WP-007): `Dynamics` trait (`compute_derivatives`) and three oscillator models implementing it:
  - `KuramotoOscillator` — extended Kuramoto with amplitude decay and frequency adaptation; mean-field `O(N)`, full pairwise `O(N²)` (custom matrix or uniform `K/N`), and sparse k-NN `O(N·k)` coupling.
  - `StuartLandauOscillator` — complex-amplitude Hopf normal form with mean-field, full, and sparse k-NN coupling.
  - `HopfOscillator` — supercritical Hopf bifurcation in polar coordinates with `limit_cycle_amplitude`; mean-field, full, and sparse k-NN coupling.
- **`coupling`** (WP-007, WP-009): `CouplingMode` enum (`MeanField`, `Full { matrix }`, `SparseKnn { k }`) with enum-dispatched coupling semantics (no string dispatch); `Default` is `Full { matrix: None }`. WP-009 adds `Topology` enum (`AllToAll`, `Ring { k_ring }`, `SmallWorld { k_ring, rewire_prob, seed }`) with `build_matrix` builders that produce `N × N` coupling matrices with `K / degree` per-edge normalization, `CouplingError` typed error enum, and `validate_coupling_matrix` helper. The `SmallWorld` variant is a directed Watts–Strogatz rewiring (outgoing edges only); `k_ring` is clamped to the largest even number `≤ N - 1` to preserve the `K / degree` energy invariant.
- **`integrate`** (WP-008, WP-012): `Integrator` trait (`step`) plus five integrators with explicit reusable buffers and numerical guards:
  - `EulerIntegrator` — first-order explicit Euler.
  - `RK4Integrator` — classic fourth-order Runge–Kutta (order `h^4`).
  - `RK45Integrator` — adaptive Dormand–Prince RK45 with FSAL caching, PI step-size control, and typed tolerance/step-budget errors; returns `AdaptiveResult`.
  - `ExponentialIntegrator` (WP-012) — exponential Euler (`y_{n+1} = exp(hA) y_n + h·φ₁(hA)·g(y_n)`) for stiff dynamics via direct Padé(13) scaling-and-squaring (`dim ≤ max_direct_dim`) or Krylov–Arnoldi subspace approximation (`dim > max_direct_dim` or `stiff_mode`, adaptive rank from the estimated Jacobian condition number). `matrix_exp`/`phi1_matrix`/Krylov solves propagate `IntegrateError::LinearSolveFailed` instead of silently returning identity on a singular LU denominator; `step`/`integrate` validate `3 · state.phase.len() == dim` and return `IntegrateError::InvalidDim` on mismatch.
  - `MultiRateIntegrator` (WP-012) — uniform sub-stepping: divides the outer timestep into `sub_steps` equal inner RK4 or Euler (`MultiRateMethod`) steps applied to all oscillators, matching the PRINet 3.0 reference implementation (Project Plan amendment #18). Band-aware per-`freq_band` scheduling is a deferred capability, not implemented.
  - `integrate_fixed` free function for multi-step fixed-step integration.
  - `IntegrateError` enum with ten typed variants (`InvalidTimestep`, `InvalidTolerance`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue`, `InvalidDim`, `InvalidKrylovRank`, `LinearSolveFailed`).
- **`pac`** (WP-009): `PhaseAmplitudeCoupling` struct implementing cross-frequency phase–amplitude coupling `A_fast = A₀·[1 + m·cos(φ_slow + offset)]` with mean slow-band phase, broadcast modulation, and amplitude clamp `[AMPLITUDE_MIN, AMPLITUDE_MAX]`. `PacError` typed error enum with five variants (`InvalidModulationDepth`, `EmptyInput`, `NonFiniteValue`, `InvalidPhaseOffset`, `InvalidClampRange`). `new` / `with_clamp` constructors validate modulation depth `m ∈ [0, 1]` and clamp range finiteness/ordering.

## Parity

Rust-vs-PRINet 3.0 derivative parity is verified in
`tests/parity_models.rs` for all three models and all coupling modes. Pure
float64 paths (Kuramoto/Hopf full and sparse) agree to `1e-12`; paths affected
by PRINet 3.0's internal `torch.complex64` (f32) arithmetic (Kuramoto/Hopf
mean-field, all Stuart–Landau modes) agree to `1e-6`. See the Parity Report
(`DOCS/sphinx/parity_report.rst`) and Project Plan §5 (preserved numerical
hazard, amendment #14).

Rust-vs-PRINet 3.0 trajectory parity is verified in
`tests/parity_integrators.rs` (23 golden-trajectory cases: 16 for Euler/RK4,
plus 4 `ExponentialIntegrator` and 3 `MultiRateIntegrator` cases added in
WP-012) comparing against `torch.float64` reference values at `rtol=1e-6,
atol=1e-8` (and tighter for pure f64 paths). RK4 order-`h^4` convergence and
RK45 tolerance properties are asserted in both unit and parity tests.

Rust-vs-PRINet 3.0 PAC parity is verified in `tests/parity_pac.rs` (9 golden
cases) comparing `PhaseAmplitudeCoupling::modulate` against hard-coded PRINet
3.0 reference values at `epsilon = 1e-6` (amendment #14 f32-truncation
tolerance). The 1/N versus 1/k normalization distinction is asserted by
`sparse_knn_k_equals_n_minus_1_equals_full_default` (exact `(N-1)/N` ratio) and
`normalization_one_over_n_explicit_in_mean_field` / `normalization_one_over_k_explicit_in_sparse`
(explicit per-edge weight checks on the actual k-NN neighbour set). Sparse/full
equivalence and k-NN edge properties are covered by 5 edge-property tests, 1
proptest, and a topology equivalence test.

## Feature Flags

- **`strict-checks`**: Optional feature. When enabled, guard functions return typed errors on invalid inputs (NaN/Inf, out-of-range dimensions or values) rather than clamping/repairing.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate preserves.

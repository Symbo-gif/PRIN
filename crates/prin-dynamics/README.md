# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state, deterministic PRNG,
numerical guards, Kuramoto / Stuart–Landau / Hopf models, integrators
(Euler / RK4 / RK45 / exponential / multi-rate), phase–amplitude coupling,
coupling topologies, hierarchical band networks, and temporal propagation.

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

## Module Summary

| Module | Purpose | Key Types |
|---|---|---|
| `state` | Struct-of-arrays oscillator state, phase wrapping, guards | `OscillatorState`, `StateDerivatives` |
| `seed` | Counter-based deterministic PRNG authority | `Seed` (`Pcg64`) |
| `errors` | Typed error enumerations | `StateError`, `SeedError` |
| `models` | Three oscillator models with mean-field, full, and sparse k-NN coupling | `KuramotoOscillator`, `StuartLandauOscillator`, `HopfOscillator` |
| `coupling` | Coupling modes and topology builders | `CouplingMode`, `Topology` |
| `integrate` | Five integrators with reusable buffers and numerical guards | `EulerIntegrator`, `RK4Integrator`, `RK45Integrator`, `ExponentialIntegrator`, `MultiRateIntegrator` |
| `pac` | Cross-frequency phase–amplitude coupling | `PhaseAmplitudeCoupling` |
| `bands` | Continuous hierarchical band networks (θ/γ, δ/θ/γ) | `BandNetwork`, `BandParams`, `PacPair` |
| `temporal` | Frame-to-frame temporal propagation via complex-phasor blending | `TemporalPropagator`, `ComplexPhasorBlender`, `EmaAmplitudeBlender` |

## Modules Implemented (WP-006, WP-007, WP-008, WP-009, WP-012, WP-013)

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
- **`bands`** (WP-013): continuous hierarchical band networks implementing the `Dynamics` trait so they compose with every `Integrator` rather than embedding one (PRINet 3.0's `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` are steppers — see Project Plan amendment #19).
  - `BandParams` — per-band `KuramotoOscillator` configuration (frequency, coupling `K`, amplitude decay `λ`, frequency adaptation `γ`, optional `freq_adaptation_rate`, and per-band `CouplingMode` via `with_coupling`; the PRINet 3.0 reference uses `sparse_knn`).
  - `PacPair` — declares a slow→fast cross-frequency PAC link (any strictly slow→fast pair is permitted, including the non-adjacent delta→gamma cascade).
  - `BandNetwork` — single continuous ODE right-hand side over the concatenated state. Intra-band derivatives are evaluated by the crate's `KuramotoOscillator` on each band's sub-state (one algorithm, one implementation), so every `CouplingMode` is available per band. Cross-band PAC enters `dA_fast/dt` as the relaxation term `λ_fast·(A_target − A_fast)` toward the reference's modulation target `A_fast·[1 + m·cos(mean(φ_slow) + offset)]` (the continuous-time analogue of PRINet's discrete assignment).
  - `theta_gamma_network` / `delta_theta_gamma_network` factories (2- and 3-band hierarchies), `theoretical_capacity` (`floor(f_fast / f_slow)`, ~7 for typical θ/γ frequencies; the Lisman–Jensen working-memory capacity model), `create_band_state` helper.
  - `BandError` typed enum (`NoBands`, `EmptyBand`, `InvalidBandIndex`, `InvalidCouplingMode`, `MissingBandLabels`, `InvalidCapacity`, `Partition`).
- **`temporal`** (WP-013): frame-to-frame temporal propagation via complex-phasor phase blending + EMA amplitude blending.
  - `ComplexPhasorBlender` — converts phases to unit phasors `z = e^{iφ}`, takes a weighted complex average, and extracts the resultant phase via `atan2` (correctly handles the wrap-around case: blending `0.1` and `2π − 0.1` gives ≈ `0`, not `π`).
  - `EmaAmplitudeBlender` — exponential moving average for amplitudes with `alpha` weighting the new frame and clamping to `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
  - `TemporalPropagator` — combines both, maintaining a running blended state across frames.
  - **Parameter mapping to PRINet 3.0:** PRIN's `alpha` weights the new frame, PRINet's `carry_strength`/`amplitude_decay` weight the carried frame; `ComplexPhasorBlender::alpha = 1 − carry_strength`, `EmaAmplitudeBlender::alpha = 1 − amplitude_decay` (the conventions are complements, not synonyms). Documented on every type and enforced by `parity_temporal::parity_reversed_convention_does_not_match`.
  - `TemporalError` typed enum (`InvalidBlendingFactor`, `EmptyInput`, `LengthMismatch`, `NonFiniteValue`).

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

Rust-vs-PRINet 3.0 band-network parity is verified in
`tests/parity_bands.rs` (12 golden cases added in WP-013) covering per-mode
intra-band derivatives (`mean_field`, `full`, `sparse_knn`) against
`prinet==3.0.0` `KuramotoOscillator.compute_derivatives`, the composed 2-band
and 3-band right-hand sides (including the reference PAC target), RK4 golden
trajectories at `n = 1` and `n = 10`, `dt = 0.01`, for both `mean_field` and
the reference networks' `sparse_knn`, and `theoretical_capacity` vs the
reference `MultiRateIntegrator` sub-step count. Measured worst-case drift:
`2.22e-16` (sparse k-NN, the reference mode), `2.74e-9` (full), `1.19e-7`
(mean-field, amendment #14 f32-complex hazard). Whole-network step-for-step
trajectory parity with the reference stepper is not claimed — PRIN's
`BandNetwork` is a continuous ODE right-hand side, not a per-band stepper
(Project Plan amendment #19).

Rust-vs-PRINet 3.0 temporal-propagation parity is verified in
`tests/parity_temporal.rs` (6 golden cases added in WP-013) against
`prinet==3.0.0` `TemporalPhasePropagator.propagate`: a single blend, a chained
5-frame golden sequence, `0`/`2π` wrap-around, amplitude-clamp saturation, and
a directional guard on the `alpha = 1 − carry_strength` parameter mapping.
Both sides are fully `f64`; comparisons are at `1e-12`.

## Feature Flags

- **`strict-checks`**: Optional feature. When enabled, guard functions return typed errors on invalid inputs (NaN/Inf, out-of-range dimensions or values) rather than clamping/repairing.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate preserves.

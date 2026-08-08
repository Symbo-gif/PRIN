# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state (struct-of-arrays),
deterministic counter-based PRNG authority (`Seed`), numerical guards and clamps,
Kuramoto / Stuart–Landau / Hopf models, Euler / RK4 / RK45 integrators,
phase–amplitude coupling, coupling topologies, continuous hierarchical band
networks, and temporal propagation. Exponential and multi-rate integrators are
planned for Phase 2 (WP-012).

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

## Modules Implemented (WP-006, WP-007, WP-008)

- **`state`**: Struct-of-arrays `OscillatorState` (`phase`, `amplitude`, `frequency`, optional `freq_band`), phase wrapping to `[0, 2π)`, `atan2`-safe phase differences, amplitude and derivative clamps/guards, and sort-based phase k-NN indexing. WP-007 adds `StateDerivatives` (`dphase`, `damplitude`, `dfrequency`) with length validation and derivative guards honoring `strict-checks`.
- **`seed`**: Counter-based deterministic `Seed` authority (`Pcg64` with `(counter, key)` stream identity, `jump`, bounded range draw, `RngCore` integration).
- **`errors`**: Typed error enumerations `StateError` and `SeedError` built with `thiserror`.
- **`models`** (WP-007): `Dynamics` trait (`compute_derivatives`) and three oscillator models implementing it:
  - `KuramotoOscillator` — extended Kuramoto with amplitude decay and frequency adaptation; mean-field `O(N)`, full pairwise `O(N²)` (custom matrix or uniform `K/N`), and sparse k-NN `O(N·k)` coupling.
  - `StuartLandauOscillator` — complex-amplitude Hopf normal form with mean-field, full, and sparse k-NN coupling.
  - `HopfOscillator` — supercritical Hopf bifurcation in polar coordinates with `limit_cycle_amplitude`; mean-field, full, and sparse k-NN coupling.
- **`coupling`** (WP-007): `CouplingMode` enum (`MeanField`, `Full { matrix }`, `SparseKnn { k }`) with enum-dispatched coupling semantics (no string dispatch); `Default` is `Full { matrix: None }`.
- **`integrate`** (WP-008): `Integrator` trait (`step`) plus three integrators with explicit reusable buffers and numerical guards:
  - `EulerIntegrator` — first-order explicit Euler.
  - `RK4Integrator` — classic fourth-order Runge–Kutta (order `h^4`).
  - `RK45Integrator` — adaptive Dormand–Prince RK45 with FSAL caching, PI step-size control, and typed tolerance/step-budget errors; returns `AdaptiveResult`.
  - `integrate_fixed` free function for multi-step fixed-step integration.
  - `IntegrateError` enum with seven typed variants (`InvalidTimestep`, `InvalidTolerance`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue`).

## Parity

Rust-vs-PRINet 3.0 derivative parity is verified in
`tests/parity_models.rs` for all three models and all coupling modes. Pure
float64 paths (Kuramoto/Hopf full and sparse) agree to `1e-12`; paths affected
by PRINet 3.0's internal `torch.complex64` (f32) arithmetic (Kuramoto/Hopf
mean-field, all Stuart–Landau modes) agree to `1e-6`. See the Parity Report
(`DOCS/sphinx/parity_report.rst`) and Project Plan §5 (preserved numerical
hazard, amendment #14).

Rust-vs-PRINet 3.0 trajectory parity is verified in
`tests/parity_integrators.rs` (16 golden-trajectory cases) comparing Euler and
RK4 against `torch.float64` reference values at `rtol=1e-6, atol=1e-8` (and
tighter for pure f64 paths). RK4 order-`h^4` convergence and RK45 tolerance
properties are asserted in both unit and parity tests.

## Feature Flags

- **`strict-checks`**: Optional feature. When enabled, guard functions return typed errors on invalid inputs (NaN/Inf, out-of-range dimensions or values) rather than clamping/repairing.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate preserves.

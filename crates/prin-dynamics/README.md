# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state (struct-of-arrays),
deterministic counter-based PRNG authority (`Seed`), numerical guards and clamps,
Kuramoto / Stuart–Landau / Hopf models, Euler / RK4 / RK45 / exponential /
multi-rate integrators, phase–amplitude coupling, coupling topologies,
continuous hierarchical band networks, and temporal propagation.

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

## Modules Implemented (WP-006, WP-007)

- **`state`**: Struct-of-arrays `OscillatorState` (`phase`, `amplitude`, `frequency`, optional `freq_band`), phase wrapping to `[0, 2π)`, `atan2`-safe phase differences, amplitude and derivative clamps/guards, and sort-based phase k-NN indexing. WP-007 adds `StateDerivatives` (`dphase`, `damplitude`, `dfrequency`) with length validation and derivative guards honoring `strict-checks`.
- **`seed`**: Counter-based deterministic `Seed` authority (`Pcg64` with `(counter, key)` stream identity, `jump`, bounded range draw, `RngCore` integration).
- **`errors`**: Typed error enumerations `StateError` and `SeedError` built with `thiserror`.
- **`models`** (WP-007): `Dynamics` trait (`compute_derivatives`) and three oscillator models implementing it:
  - `KuramotoOscillator` — extended Kuramoto with amplitude decay and frequency adaptation; mean-field `O(N)`, full pairwise `O(N²)` (custom matrix or uniform `K/N`), and sparse k-NN `O(N·k)` coupling.
  - `StuartLandauOscillator` — complex-amplitude Hopf normal form with mean-field, full, and sparse k-NN coupling.
  - `HopfOscillator` — supercritical Hopf bifurcation in polar coordinates with `limit_cycle_amplitude`; mean-field, full, and sparse k-NN coupling.
- **`coupling`** (WP-007): `CouplingMode` enum (`MeanField`, `Full { matrix }`, `SparseKnn { k }`) with enum-dispatched coupling semantics (no string dispatch); `Default` is `Full { matrix: None }`.

## Parity

Rust-vs-PRINet 3.0 derivative parity is verified in
`tests/parity_models.rs` for all three models and all coupling modes. Pure
float64 paths (Kuramoto/Hopf full and sparse) agree to `1e-12`; paths affected
by PRINet 3.0's internal `torch.complex64` (f32) arithmetic (Kuramoto/Hopf
mean-field, all Stuart–Landau modes) agree to `1e-6`. See the Parity Report
(`DOCS/sphinx/parity_report.rst`) and Project Plan §5 (preserved numerical
hazard, amendment #14).

## Feature Flags

- **`strict-checks`**: Optional feature. When enabled, guard functions return typed errors on invalid inputs (NaN/Inf, out-of-range dimensions or values) rather than clamping/repairing.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate preserves.

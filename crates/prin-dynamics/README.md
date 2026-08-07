# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state (struct-of-arrays),
deterministic counter-based PRNG authority (`Seed`), numerical guards and clamps,
Kuramoto / Stuart–Landau / Hopf models, Euler / RK4 / RK45 / exponential /
multi-rate integrators, phase–amplitude coupling, coupling topologies,
continuous hierarchical band networks, and temporal propagation.

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

## Modules Implemented (WP-006)

- **`state`**: Struct-of-arrays `OscillatorState` (`phase`, `amplitude`, `frequency`, optional `freq_band`), phase wrapping to `[0, 2π)`, `atan2`-safe phase differences, amplitude and derivative clamps/guards, and sort-based phase k-NN indexing.
- **`seed`**: Counter-based deterministic `Seed` authority (`Pcg64` with `(counter, key)` stream identity, `jump`, bounded range draw, `RngCore` integration).
- **`errors`**: Typed error enumerations `StateError` and `SeedError` built with `thiserror`.

## Feature Flags

- **`strict-checks`**: Optional feature. When enabled, guard functions return typed errors on invalid inputs (NaN/Inf, out-of-range dimensions or values) rather than clamping/repairing.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate preserves.

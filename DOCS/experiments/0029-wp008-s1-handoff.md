# WP-008 S1 handoff to session 0030

**Session:** 0029 — S1 Coding  
**Work package:** WP-008 — Basic integrators  
**Date:** 2026-08-07  
**Branch:** `feat/wp006-oscillator-state` (continuing on the WP-006 feature branch per repository convention)  
**Pre-S1 baseline:** `6f55691` (WP-007 S4 documentation baseline)  
**Implementation range:** `6f55691..` (to be recorded at S4)  
**Successor:** [Session 0030](../sessions/phase-1/0030-wp008-s2-basic-integrators.md) — mandatory read-only S2 audit

## 1. S1 author claim

The WP-008 S1 implementation and evidence outputs are complete to the author's
knowledge. The new `prin-dynamics` `integrate` module implements the
`Integrator` trait plus `EulerIntegrator`, `RK4Integrator`, and adaptive
`RK45Integrator` (Dormand–Prince 5(4)) with explicit reusable buffers,
PRINet 3.0 numerical guards (phase wrap, amplitude clamp, derivative clamp),
and typed failure paths. Acceptance criteria are mapped below.

This claim is not an audit verdict or cycle-completion claim. Session status and
register updates are reserved for S4.

## 2. Acceptance-to-evidence map

| WP-008 acceptance criterion | S1 evidence | Author assessment |
|---|---|---|
| Integrator abstraction | `Integrator` trait with `step(&mut self, &dyn Dynamics, &OscillatorState, f64) -> Result<OscillatorState, IntegrateError>` in `crates/prin-dynamics/src/integrate.rs` | MET |
| Euler integrator | `EulerIntegrator` — faithful port of PRINet 3.0 `_step_euler`; phase wrap + amplitude clamp on final state | MET |
| RK4 integrator | `RK4Integrator` — faithful port of PRINet 3.0 `_step_rk4`; intermediate states built without phase wrap (matching `_make_state`); final state wraps + clamps | MET |
| Adaptive RK45 | `RK45Integrator` — Dormand–Prince 5(4) with embedded 4th-order error estimate, PI step-size control, FSAL optimization; new PRIN capability (no PRINet counterpart) | MET |
| Explicit buffers | All integrators use pre-allocated reusable `Vec<f64>` buffers (sized `3N`); `with_capacity(n)` constructors; no per-step heap allocation after first use | MET |
| Numerical guards | Phase wrap to `[0, 2π)`, amplitude clamp to `[AMPLITUDE_MIN, AMPLITUDE_MAX]`, derivative clamp via `StateDerivatives::new`; applied in `make_final_state` and intermediate state construction | MET |
| Golden trajectories at rtol=1e-6/atol=1e-8 | `tests/parity_integrators.rs`: 12 golden-trajectory tests (Euler + RK4 × Kuramoto mean-field/full, Hopf mean-field, Stuart–Landau full) at registered tolerances; mean-field/f32-complex paths at rtol=1e-6/atol=1e-8 (1-step) and rtol=1e-5/atol=1e-7 (multi-step); pure f64 paths at rtol=1e-10/atol=1e-12 | MET |
| RK4 order h^4 | `rk4_order_h4_convergence` unit test + `parity_rk4_order_h4_on_amplitude_decay` parity test + `prop_rk4_order_h4` proptest; all verify error ratio ≈ 16 (2^4) on amplitude decay | MET |
| RK45 tolerance properties | `rk45_tolerance_property` unit test + `parity_rk45_tolerance_property_on_amplitude_decay` parity test + `prop_rk45_error_within_tolerance` proptest; all verify tighter tolerance → smaller error | MET |
| Typed failure paths | `IntegrateError` enum with `InvalidTimestep`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue` (strict-checks); validated by `parity_integrator_invalid_dt_returns_typed_error`, `parity_integrate_fixed_zero_steps_returns_typed_error`, `rk45_tolerance_not_met_error`, `rk45_rejects_invalid_tolerances` | MET |
| Non-goals respected | No exponential, Krylov, or multi-rate methods implemented | MET |
| `freq_band` preservation | `make_final_state` carries `freq_band` from the base state; verified by `rk4_freq_band_preserved` | MET |
| `strict-checks` feature | `check_finite` honors `#[cfg(feature = "strict-checks")]`; non-strict silently repairs, strict returns `NonFiniteValue` error; all tests pass under both feature configurations | MET |

## 3. Required evidence map

| Requirement | Evidence | Result |
|---|---|---|
| Tests in tandem | 28 new Rust unit/property tests in `crates/prin-dynamics/src/integrate.rs`; 16 new parity tests in `crates/prin-dynamics/tests/parity_integrators.rs`; 132 total tests in `prin-dynamics` | PASS |
| Golden cases green at registered tolerances | `cargo test -p prin-dynamics --test parity_integrators` — 16 passed | PASS |
| `cargo fmt` | `cargo fmt --all -- --check` | PASS |
| `cargo clippy` | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| `cargo test` | `cargo test --workspace` — all green; `cargo test -p prin-dynamics` — 107 unit + 16 parity_integrators + 9 parity_models = 132; `cargo test -p prin-dynamics --features strict-checks` — 133 | PASS |
| `cargo doc` | `$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps` | PASS |
| `cargo audit` | `cargo audit` — only inherited `paste` (RUSTSEC-2024-0436) warning via `cubecl`; no actionable new finding | PASS |
| Snyk Code | `snyk_code_scan` on `C:\dev\PRIN\crates\prin-dynamics\src\integrate.rs` and `tests\parity_integrators.rs` with `severity_threshold=low` | 0 issues |
| Snyk Open Source | Not applicable — no dependency manifests changed in this S1 | N/A |
| pip-audit | Not applicable — no Python or dependency changes in this S1 | N/A |
| Coverage on new/changed code | Deferred to S2 audit coverage measurement; new `integrate.rs` is exercised by 28 inline tests + 16 parity tests | DEFERRED to S2 |

## 4. Implementation summary

- **`crates/prin-dynamics/src/integrate.rs`** (new, ~900 lines):
  - `Integrator` trait with `step` method.
  - `IntegrateError` enum: `InvalidTimestep`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue`.
  - `EulerIntegrator`: forward Euler; faithful port of PRINet 3.0 `_step_euler`; reusable `3N` derivative buffer.
  - `RK4Integrator`: classic fourth-order Runge–Kutta; faithful port of PRINet 3.0 `_step_rk4`; four `3N` stage buffers + three intermediate-state buffers; intermediate states built without phase wrap (matching PRINet `_make_state`), final state wraps + clamps.
  - `RK45Integrator`: adaptive Dormand–Prince 5(4) with embedded 4th-order error estimate, FSAL optimization, PI step-size control (`SAFETY=0.9`, `MIN_FACTOR=0.2`, `MAX_FACTOR=5.0`); seven `3N` stage buffers; `integrate_adaptive` driver with trajectory recording; `Integrator::step` for single fixed-size DOPRI5 steps. New PRIN capability (no PRINet counterpart).
  - `AdaptiveResult` struct: `final_state`, `trajectory`, `accepted_steps`, `rejected_steps`, `final_dt`.
  - `integrate_fixed` driver for fixed-step integrators with optional trajectory recording.
  - `make_intermediate_state` / `make_final_state` helpers applying PRINet numerical guards.
  - `check_finite` honoring `strict-checks` feature.
  - 28 inline unit/property tests: Euler/RK4 correctness, phase wrap, amplitude clamp, invalid-dt rejection, RK4 order h^4, RK4 exactness for linear ODEs, RK45 tolerance property, RK45 step-vs-adaptive consistency, RK45 trajectory recording, RK45 error paths, `integrate_fixed` driver, proptest invariants (phase-in-range, RK4 order, RK45 tolerance).

- **`crates/prin-dynamics/tests/parity_integrators.rs`** (new, 338 lines):
  - 16 golden-trajectory parity tests comparing Rust Euler/RK4 against PRINet 3.0 `torch.float64` reference values for Kuramoto mean-field (1/5/10 steps), Kuramoto full (5 steps), Hopf mean-field (5 steps), Stuart–Landau full (5 steps).
  - Tolerance tiers: mean-field/f32-complex paths at `rtol=1e-6, atol=1e-8` (1-step) / `rtol=1e-5, atol=1e-7` (multi-step) per Plan §5 and amendment #14; pure f64 paths at `rtol=1e-10, atol=1e-12`.
  - RK4 order-of-convergence and RK45 tolerance-property parity tests.
  - Typed error-path parity tests.

- **`crates/prin-dynamics/src/lib.rs`** (modified):
  - Re-exports `AdaptiveResult`, `EulerIntegrator`, `IntegrateError`, `Integrator`, `RK4Integrator`, `RK45Integrator`, `integrate_fixed`.

## 5. Out-of-scope discovery log

| Discovery | Why not implemented in S1 | Planned owner / next control |
|---|---|---|
| Python bindings for integrators | WP-008 S1 is Rust core only; PyO3 integration belongs to WP-011 | WP-011 |
| Coverage measurement (`cargo llvm-cov`) | Deferred to S2 audit per workflow convention | S2 (session 0030) |
| Benchmark / performance measurement | No performance work package active; timing not part of WP-008 acceptance | WP-012+ |
| Exponential / Krylov / multi-rate integrators | Explicitly excluded by session brief non-goals | Future WP |

## 6. Parity reference provenance

Golden trajectory reference values were generated from `prinet==3.0.0` using
`torch.float64` with the following configuration:

- **Kuramoto mean-field (N=2):** `KuramotoOscillator(2, coupling_strength=1.0, decay_rate=0.1, freq_adaptation_rate=0.01, mean_field=True, dtype=torch.float64)`, initial phase `[0.1, 0.5]`, amplitude `[1.0, 1.2]`, frequency `[1.0, 2.0]`, dt=0.01.
- **Kuramoto full (N=3):** `KuramotoOscillator(3, coupling_strength=1.5, decay_rate=0.1, freq_adaptation_rate=0.01, dtype=torch.float64)`, initial phase `[0.0, 0.2, 1.0]`, amplitude `[1.0, 1.0, 1.0]`, frequency `[1.0, 1.0, 1.0]`, dt=0.01.
- **Hopf mean-field (N=3):** `HopfOscillator(3, coupling_strength=1.0, bifurcation_param=1.0, mean_field=True, dtype=torch.float64)`, initial phase `[0.1, 0.5, 1.0]`, amplitude `[1.5, 0.5, 1.0]`, frequency `[1.0, 2.0, 1.5]`, dt=0.01.
- **Stuart–Landau full (N=2):** `StuartLandauOscillator(2, coupling_strength=1.0, bifurcation_param=1.0, dtype=torch.float64)`, initial phase `[0.0, 0.2]`, amplitude `[1.0, 1.0]`, frequency `[1.0, 1.0]`, dt=0.01.

Reference values are embedded directly in `tests/parity_integrators.rs` so the
test suite is self-contained and does not require a Python subprocess.

## 7. Handoff constraints

- Freeze the S1 source/evidence range for read-only inspection.
- Begin only session `0030-wp008-s2-basic-integrators` via the audit flow.
- Do not remediate during S2.
- Do not update the session register, brief status, CHANGELOG, or Project State Report until their governed sessions.

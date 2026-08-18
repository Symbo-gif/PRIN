# Session 0085 — WP-022 S1 Handoff Note

**Session:** 0085 — WP-022 S1: Coding — Trainable bands and resonance primitives
**Date:** 2026-08-18
**Status:** S1 delivered; handoff to S2 audit (session 0086)

## Mission recap

"Implement Burn `DiscreteDeltaThetaGamma`, `ResonanceLayer`, parameter/state
contracts, and differentiable forward references." Contract
(`DOCS/sessions/phase-4/0085-wp022-s1-trainable-bands-and-resonance-primitives.md`):
forward and gradient reference tests pass; serialization, shape, dtype, and
numerical guards are covered. Non-goals: inhibition, HEP, optimizers, full
models.

## Scope decision: Rust-only (`crates/prin-train`), no `prin-py` bridge

PSR-021 §8's WP-022 declaration lists `crates/prin-train/`, `crates/prin-py/`
in its file scope, but the session brief's own mission text and acceptance
criteria are Rust/Burn-only ("Implement Burn `DiscreteDeltaThetaGamma`,
`ResonanceLayer`..."), and WP-025 is separately and specifically titled
"Production Torch autograd bridge" (`DOCS/sessions/phase-4/0097–0100`). The
Python `torch.autograd.Function` bridge (Coding Standards §3.2's "every
Rust-backed trainable op is a `torch.autograd.Function`") is therefore
WP-025's job, not WP-022's; `prin-py` was untouched this session. Recorded
here as a scope clarification (WP-016/amendment #20 precedent), not a
silent scope narrowing — flagged for the S2 auditor.

## GPU CI runner strategy decision (R24 checkpoint, Project Plan amendment #26)

The Phase 3 recommendation-implementation session assigned this exact
session (WP-022 S1) as R24's checkpoint to resolve the GPU CI runner
strategy for DV-001/DV-002/DV-005 — a plan-amendment-class decision R24
itself said could not be made unilaterally. Consulted the maintainer before
starting the bands/layers coding work (this decision gates the DV register,
independent of the coding mission): **self-hosted GPU runner**, confirming
`gpu.yml`'s pre-existing `[self-hosted, gpu]` design. Changes:

- `.github/workflows/gpu.yml`: added a `gpu-wgpu` job (`cargo test
  --workspace --features wgpu -- --test-threads=1`), closing the CI-step
  half of DV-002; the existing `gpu-cuda` job (renamed from `gpu`) is
  unchanged.
- `DOCS/PRIN_Project_Plan.md` §8.3: amendment #26.
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`: DV-001/DV-002 updated to
  record the decided strategy with runner *registration* (an out-of-band
  GitHub Settings → Actions → Runners action, not a code change) as the sole
  remaining step; DV-001 additionally flagged as needing a **Linux** runner
  specifically for the Triton comparison (Triton has no Windows support, so
  the on-hand Windows RTX 4060 host cannot close that half even once
  registered). DV-005 re-audited and confirmed unaffected — this session's
  Burn primitives are CPU-only (`NdArray`), no DLPack touched. R24 closed.

No runner was registered in this session (outside repository-code scope);
DV-001/DV-002 remain OPEN pending that out-of-band action.

## Scope delivered

| File | Change |
|---|---|
| `Cargo.toml` (workspace) | Added `burn = { version = "0.16", default-features = false, features = ["std", "ndarray", "autodiff"] }` — first use of Burn in this repository. `ndarray`/`autodiff` give a CPU reference backend + gradient computation for now; GPU-backed Burn backends (`wgpu`/`cuda`) are deferred to WP-025 per Project Plan §4.3 risk register #5. |
| `crates/prin-train/Cargo.toml` | Added `burn.workspace = true`; added a `strict-checks` feature (Coding Standards §2.2 numerical-guard convention, matching `prin-dynamics`/`prin-kernels`). |
| `crates/prin-train/src/lib.rs` | Rewrote the module doc to describe only what is now implemented (`bands`, `layers`) vs. still-planned (`inhibition`, `activations`, `hep`, `optim` — WP-023/024/025), matching the WP008-F4 precedent (don't list unimplemented submodules as if present). |
| `crates/prin-train/src/error.rs` | **New.** `TrainError` (`thiserror`): `EmptyBand`, `ShapeMismatch`, `NonFiniteParameter`, `InvalidTimestep`, `NonFiniteState`. |
| `crates/prin-train/src/support.rs` | **New.** Shared helpers: `seeded_uniform` (draws parameter tensors from the project's deterministic `prin_dynamics::Seed`, not Burn's own unseeded RNG — Coding Standards §1.3), `xavier_bound`, `check_dims`, `validate_dt`, `validate_finite`, and the `strict-checks`-gated `check_finite` numerical guard. |
| `crates/prin-train/src/bands.rs` | **New** (`DiscreteDeltaThetaGamma`). See below. |
| `crates/prin-train/src/layers.rs` | **New** (`ResonanceLayer`). See below. |
| `crates/prin-train/tests/parity_bands.rs`, `tests/parity_layers.rs` | **New.** Golden-value parity tests against PRINet 3.0. |
| `crates/prin-train/README.md` | Rewritten to describe the implemented/not-yet-implemented split. |
| `DOCS/test_and_benchmark_results/wp022_generate_prinet_references.py` | **New**, ad-hoc, gitignored (WP-009/.../WP-021 precedent). Generates the golden values embedded in the two parity test files. |

## `DiscreteDeltaThetaGamma` and `ResonanceLayer`

Both are `#[derive(Module)]` Burn modules generic over `B: Backend`, exposing:

- a validated `Config` (`DiscreteDeltaThetaGammaConfig` /
  `ResonanceLayerConfig`) with two initializers: `init` (seeded-random
  parameters via `prin_dynamics::Seed`, for production use) and
  `init_from_params` (explicit parameter tensors via a `Params` struct,
  shape-validated against the config — used by parity/gradient tests and
  any non-`burn::record` checkpoint path);
- a validated `State` contract (`DiscreteBandState` /
  `ResonanceState`) that `step`/`integrate` operate on, constructed only
  via `::new`, which checks every tensor shares a shape;
- `step`/`integrate`, returning `Result<State, TrainError>` — shape
  mismatches and (under `strict-checks`) non-finite outputs are typed
  errors, not panics or silent corruption.

`DiscreteDeltaThetaGamma::step` is a line-for-line Burn port of PRINet 3.0's
`core.propagation.networks.DiscreteDeltaThetaGamma.step`: phase advance with
learned intra-band coupling, delta→theta/theta→gamma PAC gating
(multiplicative, sigmoid-gated), Stuart–Landau amplitude update with a
learned per-band growth rate. `ResonanceLayer::step` is the same port of the
core Kuramoto loop in `nn.layers.ResonanceLayer.forward` (coupling, decay,
frequency-modulation terms, all evaluated from pre-step state, matching the
reference's ordering). `ResonanceLayer` documents one deliberate deviation:
`init_state`'s input→initial-state projection is a simpler, real-valued,
fully differentiable mapping in place of PRINet 3.0's FFT-based
initializer (Burn has no complex-tensor autodiff); the step dynamics
themselves are unaffected and are the half golden-tested against the
reference. Both modules' rustdoc has a "Correspondence to the PRINet 3.0
reference" section spelling out the formula and any deviation, matching the
`prin_dynamics::bands` precedent.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Forward reference tests pass** | **GREEN** | `tests/parity_bands.rs::discrete_delta_theta_gamma_step_matches_prinet_3_0` and `tests/parity_layers.rs::resonance_layer_step_matches_prinet_3_0` — golden values transcribed from the PRINet 3.0 `step` formulas and evaluated independently in `torch==2.13.0+cpu` float64 (`wp022_generate_prinet_references.py`), compared against the Rust/Burn `step` output at `rtol=1e-7, atol=5e-8` (measured worst case `1.65e-8` absolute — Burn `matmul`/`sum_dim` reduction order vs. torch's, same discrepancy class as `prin-dynamics`' `parity_bands.rs` `FULL_RTOL`/`FULL_ATOL`) and `rtol=1e-10, atol=1e-12` respectively. Two rustdoc `# Example` blocks (one per module) are also executed as doctests. |
| **Gradient reference tests pass** | **GREEN** | Per module: `gradients_flow_to_every_parameter` (every learnable `Param` receives a non-zero, finite gradient from `Tensor::backward()` on `Autodiff<NdArray<f64>>` — the `bands.rs` version deliberately sums both `phase` and `amplitude` outputs, since `w_gamma` only shapes gamma's own phase trajectory and an amplitude-only loss gives it a structurally, correctly zero gradient, discovered while writing this test) and `gradient_matches_central_finite_difference` (autodiff gradient vs. a central finite difference at `eps=1e-6`, float64, agreement `<1e-3` — the project's `torch.autograd.gradcheck` requirement's Burn-native equivalent, Testing Standards §2). |
| **Serialization is covered** | **GREEN** | `record_roundtrip_preserves_parameters` per module: `Module::into_record`/`load_record` through `burn::record::BinBytesRecorder<DoublePrecisionSettings>` (float64 — `FullPrecisionSettings` is f32 and lost ~1e-8 precision on roundtrip, corrected during S1), exact equality after roundtrip. |
| **Shape guards are covered** | **GREEN** | `Config::with_params`/`init_from_params` reject zero band/oscillator sizes and mismatched parameter-tensor shapes (`TrainError::EmptyBand`/`ShapeMismatch`); `State::new` rejects mismatched phase/amplitude/frequency shapes; `step`/`init_state` reject wrong-width input. One test per guard per module. |
| **Dtype guards are covered** | **GREEN** | All tests run on `NdArray<f64>` (double precision, matching the project's gradcheck-precision convention) and `Autodiff<NdArray<f64>>`; `strict-checks`' `check_finite` converts through the backend's own `B::FloatElem` (not a hardcoded `f32`) specifically because `to_vec::<E>()` requires an exact dtype match with no implicit numeric cast — a hardcoded target type would spuriously fail on a differently-typed backend (found and fixed during S1: an early version hardcoded `f32` and every `strict-checks` test failed with a swallowed `DataError::TypeMismatch` masquerading as "non-finite"). |
| **Numerical guards are covered** | **GREEN** | `strict-checks`-gated `check_finite` returns `TrainError::NonFiniteState` for a non-finite `step` output; regression test `step_rejects_non_finite_input_under_strict_checks` per module (feeds `NaN` phase in, confirms the typed error, not a panic or silent `NaN` propagation into the caller). Amplitude clamp (`[1e-6, 10.0]`) and phase wrap (`[0, 2π)`) invariants are covered by dedicated tests plus a `proptest` property test per module (`step_output_always_finite_and_in_range` / `forward_output_always_finite_and_in_range`) over random band sizes/seeds. |
| **≥95% coverage on new/changed code** | **GREEN** | `cargo llvm-cov -p prin-train --features strict-checks`: `bands.rs` 99.26% lines / 100% functions, `layers.rs` 99.32% lines / 100% functions, `support.rs` 98.31% lines / 88.89% functions (the one uncovered function is the `#[cfg(not(feature = "strict-checks"))]` no-op variant of `check_finite`, never compiled into the `strict-checks`-featured coverage run — the complementary variant covers when run without the feature; same non-instrumentable-under-one-configuration class as DV-004's `#[cube(launch)]` carve-out, not a real gap). `error.rs`/`lib.rs` have zero instrumentable regions (declarations/derives only). |
| **All quality/security/parity/documentation gates green** | **GREEN, with one new flagged risk (DV-017)** | See tables below. |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Workspace tests (default) | `cargo test --workspace` | PASS, no regressions |
| Workspace tests (strict-checks) | `cargo test --workspace --features strict-checks` | PASS |
| `prin-train` (default) | `cargo test -p prin-train` | PASS — 35 unit + 2 parity + 2 doctests |
| `prin-train` (strict-checks) | `cargo test -p prin-train --features strict-checks` | PASS — 37 unit (includes the 2 `strict-checks`-only NaN-guard tests) + 2 parity + 2 doctests |
| Rustdoc (workspace) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings, including `#![warn(missing_docs)]` (100% public-item documentation) |
| `cargo audit` | `cargo audit` | Exit code 0; 2 allowed warnings — pre-existing `paste` RUSTSEC-2024-0436 (amendment #9, unchanged) and **new** `bincode` RUSTSEC-2025-0141 (DV-017, below) |
| Snyk Code | `snyk code test crates/prin-train` | PASS — 0 issues |
| Snyk Open Source | Not run — Cargo/Rust is not a Snyk-supported package manager (R23 disposition, confirmed live: `snyk test --file=Cargo.lock --package-manager=cargo` → `SNYK-CLI-0008 Unsupported package manager 'cargo'`); `cargo audit` is the authoritative ecosystem-native gate for this dependency change per Coding Standards §6.2 |
| Python gates (ruff/mypy/interrogate/bandit/pytest) | Not run | Not applicable — no Python file was touched this session (`git status` confirms; scope is `crates/prin-train` + CI/plan/register docs only) |

## New discovered risk: DV-017 (`bincode` RUSTSEC-2025-0141)

Adding `burn` pulls `bincode` 2.0.1 transitively (via `burn-core`'s
`BinBytesRecorder`/`BinFileRecorder`, which this session's own
`record_roundtrip_preserves_parameters` tests exercise directly). `cargo
audit` reports it as an "unmaintained" warning (not a CVE), matching the
existing `paste` advisory's class and current disposition (DV-008,
amendment #9: allowed, re-checked every cycle). No newer `bincode` 2.x
exists (`cargo update -p bincode --dry-run` confirms already-latest) and no
alternative recorder in `burn` 0.16 avoids it. **This is flagged, not
governed** — recorded in `DEFERRED_VALIDATION_REGISTER.md` (DV-017) for the
S2 auditor / maintainer to formally disposition (accept via a plan
amendment analogous to #9, or find a mitigation), rather than silently
carried as if already accepted.

## Out-of-scope discoveries

- **`prin-py` Torch bridge (WP-025) untouched, by design.** See "Scope
  decision" above.
- **`ResonanceLayer`'s diagnostic methods (`get_order_parameter`,
  `order_parameters`, `pac_index` in the PRINet 3.0 reference) were not
  ported.** These are measurement/monitoring helpers, not part of the
  "resonance primitive" forward/gradient contract this session's acceptance
  criteria describe, and several depend on non-differentiable `.item()`
  calls in the reference — left for a future WP if training-loop monitoring
  needs them (would naturally live alongside `prin-metrics` integration).
- **GPU-backed Burn backends (`wgpu`/`cuda` feature flags on the `burn`
  dependency) are not wired up.** WP-022 S1's Burn primitives are generic
  over `B: Backend` and will work with any backend without code changes;
  actually adding `burn-wgpu`/`burn-cuda` as available backends (and
  kernel-equivalence-testing them) is Torch-bridge/GPU-integration work
  matching WP-025's declared scope, not this session's.

## Parity-evidence disposition

Two new numerical primitives are introduced this session (the first in
`prin-train`). Both are golden-value-tested against formulas transcribed
directly from the PRINet 3.0 source (`core/propagation/networks.py::
DiscreteDeltaThetaGamma.step`, `nn/layers.py::ResonanceLayer.forward`'s
loop body) and evaluated independently in plain `torch==2.13.0+cpu` float64
— the same "transcribe the reference formula into an independent Python
computation" pattern `prin-dynamics`' `parity_bands.rs`/`
wp013_generate_prinet_references.py` established, necessary here because
Burn has no complex-tensor autodiff and no PRINet `nn.Module` object exists
to call end-to-end from Rust. See "Acceptance criteria → evidence map"
above for the exact tolerances and their justification.

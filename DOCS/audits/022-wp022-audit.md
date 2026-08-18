# PRIN Audit Report — Cycle 022 / WP-022

**Date:** 2026-08-18
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-022 "Trainable bands and resonance primitives" — `crates/prin-train/` (`src/bands.rs`, `src/layers.rs`, `src/error.rs`, `src/support.rs`, `src/lib.rs`, `Cargo.toml`, `README.md`, `tests/parity_bands.rs`, `tests/parity_layers.rs`), workspace `Cargo.toml`/`Cargo.lock`, `.github/workflows/gpu.yml`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `DOCS/PRIN_Project_Plan.md` (amendment #26)
**Sessions:** 0085 (S1 implementation); 0086 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-4/0086-wp022-s2-trainable-bands-and-resonance-primitives.md`
**Git state:** `main` @ `8bce1a2`
**Verdict:** **PASS-WITH-FINDINGS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope present (`git diff --stat 8d7a6b7..8bce1a2`: 20 files, +4126/-198). `DiscreteDeltaThetaGamma`, `ResonanceLayer`, parameter/state contracts, differentiable forward references all delivered. Non-goals (inhibition, HEP, optimizers, full models) untouched. `prin-py` scope narrowing explicitly documented in S1 handoff note (WP-016/amendment #20 precedent). |
| Plan/architecture conformance (A2) | ✅ | `prin-train` → `prin-dynamics` dependency for `Seed` is a valid lateral call (both Phase 4 crates). Burn added as workspace dependency with minimal features (`std`/`ndarray`/`autodiff`), matching Project Plan §4.3 risk register #5 (GPU backends deferred to WP-025). No numerics duplicated in Python. Deterministic `Seed` flow preserved (Coding Standards §1.3). `#![forbid(unsafe_code)]` on the crate. |
| Tests in tandem + coverage (A3) | ✅ | 35 unit + 2 parity + 2 doctests (strict-checks). `bands.rs` 99.26% lines / 100% functions; `layers.rs` 99.32% lines / 100% functions; `support.rs` 98.31% lines / 88.89% functions (one uncovered function is `#[cfg(not(feature = "strict-checks"))]` no-op variant — same non-instrumentable-under-one-configuration class as DV-004). Gradient tests (autodiff vs. central finite difference), property tests (`proptest`), serialization roundtrips, golden-value parity tests all present and green. |
| Numerical parity + invariants (A4) | ✅ | Parity tests: `bands` at `rtol=1e-7, atol=5e-8` (measured worst case `1.65e-8`), `layers` at `rtol=1e-10, atol=1e-12`. Phase wrap `[0, 2π)` and amplitude clamp `[1e-6, 10.0]` invariants covered by dedicated tests + `proptest` property tests. Golden values independently evaluated in `torch==2.13.0+cpu` float64. |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy (default + strict-checks), rustdoc — all independently re-run clean. |
| Security (A6) | ⚠️ | `#![forbid(unsafe_code)]` enforced. `cargo audit`: 2 allowed warnings — pre-existing `paste` RUSTSEC-2024-0436 (DV-008, amendment #9) and **new** `bincode` RUSTSEC-2025-0141 (DV-017). The `bincode` advisory is flagged but not yet governed by a plan amendment (unlike `paste`). See WP022-F1. |
| Docstring/doc coverage (A7) | ✅ | Rustdoc: 0 warnings under `RUSTDOCFLAGS=-D warnings` with `#![warn(missing_docs)]` (100% public-item documentation). Module docs include "Correspondence to the PRINet 3.0 reference" sections with exact formulas. Two runnable rustdoc examples (one per module). Python gates N/A (no Python files touched). |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers in new code. `lib.rs` module doc accurately describes implemented vs. not-yet-implemented modules (WP008-F4 precedent). `CHANGELOG.md` updated. Session register current (0085 COMPLETE, 0086 PLANNED). `README.md` rewritten to match implemented/not-yet-implemented split. One minor observation: `DiscreteDeltaThetaGammaParams` / `ResonanceLayerParams` are `pub` in non-re-exported modules — see WP022-F2. |
| CI status (A9) | ✅ | `.github/workflows/gpu.yml` extended with `gpu-wgpu` job (amendment #26). Workspace default tests all pass locally (0 failed). Python gates N/A (no Python files touched). |
| Artefact trail (A10) | ✅ | S1 handoff note (`DOCS/experiments/0085-wp022-s1-handoff.md`) is comprehensive: acceptance-criterion evidence map, scope decisions, parity-evidence disposition, out-of-scope discoveries, quality-gate table, new risk (DV-017). Prior audit (`021-wp021-audit.md`, PASS-WITH-FINDINGS → WP021-F1 FIXED → CLEAN delta re-audit) consistent. PSR-021 deviation ledger intact. |

## 2. Methodology

All commands executed on Windows (local dev machine, NVIDIA GeForce RTX 4060 driver 595.95 / CUDA 13.2). Git diff range: `8d7a6b7` (Phase 3 analytics) → `8bce1a2` (WP-022 S1 handoff).

```powershell
# A1 — scope
git diff --stat 8d7a6b7..8bce1a2                                           # 20 files, +4126/-198

# A5 — Quality gates
cargo fmt --all -- --check                                                  # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                       # exit 0, clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0, clean
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps            # exit 0, 0 warnings

# A3 — Tests
cargo test -p prin-train                                                    # 33 unit + 1 parity + 1 parity + 2 doctests passed
cargo test -p prin-train --features strict-checks                           # 35 unit + 1 parity + 1 parity + 2 doctests passed
cargo test --workspace                                                      # all crates green, 0 failed

# A3 — Coverage
cargo llvm-cov -p prin-train --features strict-checks                       # bands.rs 99.26%, layers.rs 99.32%, support.rs 98.31%

# A6 — Security
cargo audit                                                                 # 2 allowed warnings (paste RUSTSEC-2024-0436, bincode RUSTSEC-2025-0141)

# A8 — Hygiene
# grep TODO|FIXME|HACK|XXX|STUB|unimplemented!|todo! in crates/prin-train/  # 0 matches
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (session 0085/0086 brief, PSR-021 §6): implement Burn `DiscreteDeltaThetaGamma`, `ResonanceLayer`, parameter/state contracts, and differentiable forward references. Non-goals: inhibition, HEP, optimizers, full models.

**Delivered** (`git diff --stat 8d7a6b7..8bce1a2`, 20 files):

| File | Change | In scope? |
|---|---|---|
| `Cargo.toml` (workspace) | Added `burn` 0.16 workspace dependency (`std`/`ndarray`/`autodiff`) | ✅ |
| `crates/prin-train/Cargo.toml` | Added `burn.workspace = true`; `strict-checks` feature | ✅ |
| `crates/prin-train/src/error.rs` | **New** (49 lines). `TrainError` enum: `EmptyBand`, `ShapeMismatch`, `NonFiniteParameter`, `InvalidTimestep`, `NonFiniteState` | ✅ |
| `crates/prin-train/src/support.rs` | **New** (107 lines). Shared helpers: `seeded_uniform`, `xavier_bound`, `check_dims`, `validate_dt`, `validate_finite`, `check_finite` | ✅ |
| `crates/prin-train/src/bands.rs` | **New** (968 lines). `DiscreteDeltaThetaGamma` Burn `Module` with `Config`/`Params`/`State` contracts | ✅ |
| `crates/prin-train/src/layers.rs` | **New** (822 lines). `ResonanceLayer` Burn `Module` with `Config`/`Params`/`State` contracts | ✅ |
| `crates/prin-train/src/lib.rs` | Module doc rewritten; `pub mod bands/layers/error`; `mod support`; `pub use error::TrainError` | ✅ |
| `crates/prin-train/tests/parity_bands.rs` | **New** (123 lines). Golden-value parity test vs. PRINet 3.0 | ✅ |
| `crates/prin-train/tests/parity_layers.rs` | **New** (91 lines). Golden-value parity test vs. PRINet 3.0 | ✅ |
| `crates/prin-train/README.md` | Rewritten to describe implemented/not-yet-implemented split | ✅ |
| `CHANGELOG.md` | WP-022 S1 entry under `[Unreleased]` | ✅ |
| `.github/workflows/gpu.yml` | Added `gpu-wgpu` job (amendment #26, R24 checkpoint) | ✅ (maintainer-approved scope addition) |
| `DOCS/PRIN_Project_Plan.md` | Amendment #26 | ✅ |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | DV-001/DV-002/DV-005 updated; DV-017 added | ✅ |
| `DOCS/experiments/0085-wp022-s1-handoff.md` | **New** (179 lines). S1 handoff note | ✅ |
| Session/register docs | Session 0085 marked COMPLETE | ✅ |

**Scope decisions explicitly documented in S1 handoff note:**
- `prin-py` untouched (Torch bridge is WP-025's job, not WP-022's) — flagged for S2 per WP-016/amendment #20 precedent.
- GPU-backed Burn backends (`wgpu`/`cuda` features on `burn`) deferred to WP-025 — matches Project Plan §4.3 risk register #5.
- `ResonanceLayer` diagnostic methods (`get_order_parameter`, `order_parameters`, `pac_index`) not ported — measurement helpers, not part of the forward/gradient contract.

**Verdict: ✅ PASS** — everything declared is present; nothing undeclared shipped.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** `prin-train` depends on `prin-dynamics` (for `Seed`) — a valid lateral dependency between Phase 4 crates. No circular dependencies.
- **Burn integration:** Added as workspace dependency with minimal features (`std`/`ndarray`/`autodiff`), matching the plan's risk register. GPU backends correctly deferred.
- **Deterministic seeding:** `support::seeded_uniform` draws from `prin_dynamics::Seed`, not Burn's unseeded RNG — Coding Standards §1.3 preserved.
- **No Python numerics:** No Python files touched. The Python Torch bridge is WP-025's scope.
- **`one algorithm one implementation`:** `DiscreteDeltaThetaGamma` (discrete-time trainable) is distinct from `prin_dynamics::bands::BandNetwork` (continuous ODE) — documented in `bands.rs` module docs explaining why the discrete variant lives in `prin-train`.
- **`#![forbid(unsafe_code)]`** on `prin-train` — matches project convention.

**Verdict: ✅ PASS** — no architecture violations.

### 3.3 A3 — Tests in tandem + coverage

**Test inventory (strict-checks):**

| Test file | Tests | Categories |
|---|---|---|
| `bands.rs` `mod tests` | 16 | Config validation (3), construction (4), forward/shape/dtype (4), numerical guards (3), gradient reference (2), serialization (1) |
| `layers.rs` `mod tests` | 14 | Config validation (2), construction (2), forward/shape/dtype (4), numerical guards (2), gradient reference (2), serialization (1), coupling diagonal (1) |
| `bands.rs` `mod proptests` | 1 | Property: `step_output_always_finite_and_in_range` |
| `layers.rs` `mod proptests` | 1 | Property: `forward_output_always_finite_and_in_range` |
| `tests/parity_bands.rs` | 1 | Golden-value parity vs. PRINet 3.0 |
| `tests/parity_layers.rs` | 1 | Golden-value parity vs. PRINet 3.0 |
| Doctests | 2 | `bands.rs` + `layers.rs` module examples |
| **Total** | **37** | |

**Coverage (`cargo llvm-cov -p prin-train --features strict-checks`):**

| File | Lines | Cover | Functions | Cover |
|---|---|---|---|---|
| `bands.rs` | 541 | 99.26% | 48 | 100% |
| `layers.rs` | 440 | 99.32% | 45 | 100% |
| `support.rs` | 59 | 98.31% | 9 | 88.89% |

The one uncovered function in `support.rs` is the `#[cfg(not(feature = "strict-checks"))]` no-op variant of `check_finite` — it is never compiled into the `strict-checks`-featured coverage run; the complementary variant covers when run without the feature. Same non-instrumentable-under-one-configuration class as DV-004's `#[cube(launch)]` carve-out, not a real gap.

**Gradient tests:**
- `gradients_flow_to_every_parameter` (per module): every learnable `Param` receives a non-zero, finite gradient from `Tensor::backward()` on `Autodiff<NdArray<f64>>`. The `bands.rs` version deliberately sums both `phase` and `amplitude` outputs (since `w_gamma` only shapes gamma's phase trajectory — a structurally correct zero gradient from an amplitude-only loss).
- `gradient_matches_central_finite_difference` (per module): autodiff gradient vs. central finite difference at `eps=1e-6`, float64, agreement `<1e-3`.

**Serialization tests:**
- `record_roundtrip_preserves_parameters` (per module): `Module::into_record`/`load_record` through `burn::record::BinBytesRecorder<DoublePrecisionSettings>`, exact equality after roundtrip.

**Verdict: ✅ PASS** — tests in tandem, coverage ≥95% on all new code, all required test categories present.

### 3.4 A4 — Numerical parity + invariants

**Parity tests:**
- `discrete_delta_theta_gamma_step_matches_prinet_3_0`: golden values transcribed from PRINet 3.0 `core.propagation.networks.DiscreteDeltaThetaGamma.step`, evaluated in `torch==2.13.0+cpu` float64. Tolerance: `rtol=1e-7, atol=5e-8` (measured worst case `1.65e-8` absolute — Burn `matmul`/`sum_dim` reduction order vs. torch's, same discrepancy class as `prin-dynamics`' `parity_bands.rs`).
- `resonance_layer_step_matches_prinet_3_0`: golden values from PRINet 3.0 `nn.layers.ResonanceLayer.forward` loop body. Tolerance: `rtol=1e-10, atol=1e-12`.

**Invariants:**
- Phase wrap `[0, 2π)`: tested in `phase_output_wrapped_to_0_2pi` (bands), `step_output_phase_wrapped` (layers).
- Amplitude clamp `[1e-6, 10.0]`: tested in `amplitude_output_clamped_to_valid_range` (bands), `step_output_amplitude_within_clamp_range` (layers).
- `proptest` property tests verify finiteness and range over random band sizes/seeds.
- Zero-diagonal coupling: `coupling_diagonal_does_not_self_couple` verifies single-oscillator case evolves at exactly its own frequency.

**Documented deviation:** `ResonanceLayer::init_state` substitutes a real-valued, differentiable mapping for PRINet 3.0's FFT-based initializer (Burn has no complex-tensor autodiff). The step dynamics are unaffected and parity-tested. Documented in module rustdoc with "Correspondence to the PRINet 3.0 reference" section — matches `prin_dynamics::bands` precedent.

**Verdict: ✅ PASS** — parity and invariants green at documented tolerances.

### 3.5 A5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS (exit 0) |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS (exit 0) |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS (exit 0) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS (0 warnings) |
| Workspace tests | `cargo test --workspace` | PASS (0 failed) |

**Verdict: ✅ PASS**

### 3.6 A6 — Security

- `#![forbid(unsafe_code)]` on `crates/prin-train/` — no `unsafe` introduced.
- `cargo audit`: 2 allowed warnings:
  - `paste` RUSTSEC-2024-0436 (pre-existing, DV-008, amendment #9)
  - **`bincode` RUSTSEC-2025-0141** (new, DV-017) — transitive via `burn-core`'s `BinBytesRecorder`/`BinFileRecorder`. "Unmaintained" warning, not a CVE. No newer `bincode` 2.x exists; no alternative recorder in `burn` 0.16 avoids it.

DV-017 is flagged in the Deferred Validation Register but **not yet governed by a plan amendment** — unlike the analogous `paste` advisory (DV-008, amendment #9). The S1 handoff note explicitly flags this for S2/maintainer disposition.

**Verdict: ⚠️ PASS with WP022-F1** — the advisory itself is warning-level (exit code 0, not a CVE), but the governance gap (no amendment) is a procedural gap that should be formalized.

### 3.7 A7 — Documentation coverage

- `#![warn(missing_docs)]` on `prin-train` — 100% public-item documentation (rustdoc 0 warnings under `-D warnings`).
- Module docs include:
  - "Correspondence to the PRINet 3.0 reference" sections with exact per-step formulas
  - Documented deviation (layers: FFT → real-valued init)
  - Runnable `# Example` blocks (executed as doctests)
- `README.md` rewritten to describe implemented vs. not-yet-implemented split.
- `CHANGELOG.md` entry under `[Unreleased]` is comprehensive.
- Python gates N/A (no Python files touched).

**Verdict: ✅ PASS**

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/stub/`unimplemented!`/`todo!` markers in `crates/prin-train/`.
- `lib.rs` module doc accurately lists implemented (`bands`, `layers`) vs. planned (`inhibition`, `activations`, `hep`, `optim`) — matches WP008-F4 precedent.
- Session register: 0085 COMPLETE, 0086 PLANNED, 0087 PLANNED — consistent with briefs.
- `CHANGELOG.md` updated.
- `.gitignore` respected (`DOCS/test_and_benchmark_results/` is gitignored; reference generation script is ad-hoc, matching WP-009/.../WP-021 precedent).

**Minor observation (WP022-F2):** `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` are `pub` structs in `pub mod bands`/`pub mod layers`, but neither type is re-exported at the crate root (`lib.rs` only re-exports `TrainError`). External users can receive these types via type inference but cannot name them in explicit type annotations without reaching into submodule paths (`prin_train::bands::DiscreteDeltaThetaGammaParams`). The parity tests (which are external integration tests) use `use prin_train::bands::{..., DiscreteDeltaThetaGammaParams}` successfully, so this works — but it is inconsistent with the crate-level re-export pattern for other key types.

**Verdict: ✅ PASS with WP022-F2** — minor usability inconsistency, not a correctness issue.

### 3.9 A9 — CI status

- `.github/workflows/gpu.yml` extended with `gpu-wgpu` job (`cargo test --workspace --features wgpu -- --test-threads=1`), closing the CI-step half of DV-002.
- Existing `gpu-cuda` job (renamed from `gpu`) unchanged.
- Both jobs gated on `[gpu]` commit message tag and `[self-hosted, gpu]` runner labels — no runner registered yet (out-of-band GitHub Settings action).
- Workspace default tests all pass locally.
- Python CI gates N/A (no Python files touched).

**Verdict: ✅ PASS**

### 3.10 A10 — Artefact trail

- S1 handoff note (`DOCS/experiments/0085-wp022-s1-handoff.md`): comprehensive — acceptance-criterion evidence map, scope decisions with precedents, parity-evidence disposition, out-of-scope discoveries, quality-gate table, new risk (DV-017).
- Prior audit (`DOCS/audits/021-wp021-audit.md`): PASS-WITH-FINDINGS → WP021-F1 FIXED → CLEAN delta re-audit. Consistent.
- PSR-021 deviation ledger: intact (cumulative table with all rows from WP001-F1 through WP021-F1).
- Deferred Validation Register: DV-001/DV-002 updated with amendment #26 strategy; DV-005 re-audited (unaffected); DV-017 added.
- Project Plan: amendment #26 recorded with full context.

**Verdict: ✅ PASS**

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP022-F1 | D4 | `Cargo.lock` (bincode 2.0.1), `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-017 | `bincode` RUSTSEC-2025-0141 ("unmaintained") is a new transitive advisory via `burn-core`. It is flagged in DV-017 but not yet governed by a plan amendment — unlike the analogous `paste` advisory (DV-008, amendment #9), which has formal maintainer acceptance. The advisory itself is warning-level (exit code 0, not a CVE); the gap is procedural, not security-critical. | Coding Standards §6.2 (dependency audit); DV-008 amendment #9 precedent | S4 should draft a plan amendment (analogous to #9) formally accepting the `bincode` advisory with the same "re-check every cycle, upgrade when Burn moves off bincode" cadence. Cross-reference from DV-017. |
| WP022-F2 | D4 | `crates/prin-train/src/lib.rs` | `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` are `pub` structs in `pub mod bands`/`pub mod layers`, but not re-exported at the crate root. External users can receive these types via type inference but cannot name them in explicit type annotations without reaching into submodule paths. Inconsistent with the crate-level re-export pattern for `TrainError` (`pub use error::TrainError`). | Coding Standards §3 (public API ergonomics); minor | Add `pub use bands::DiscreteDeltaThetaGammaParams;` and `pub use layers::ResonanceLayerParams;` to `lib.rs`, or document the submodule-import convention in the crate-level rustdoc. |

## 5. Deviation-ledger delta

New findings added to the ledger: **WP022-F1** (D4, `bincode` advisory governance gap), **WP022-F2** (D4, Params struct re-export ergonomics). Carried findings re-inspected: DV-001/DV-002 (updated with amendment #26 strategy, runner registration still pending), DV-005 (re-audited, unaffected — Burn primitives are CPU-only `NdArray`), DV-008 (re-checked, unchanged), DV-017 (newly discovered, flagged for governance).

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS** — two D4 findings, no D1/D2/D3.

WP-022 S1 delivered a high-quality, well-documented, well-tested implementation of the declared scope. The Burn integration follows project conventions (deterministic seeding, typed errors, `strict-checks` feature, `#![forbid(unsafe_code)]`), the parity tests are rigorous (golden values independently evaluated in torch float64), and the gradient tests (autodiff vs. central finite difference) provide strong correctness evidence. The S1 handoff note is exemplary in its scope-decision documentation and evidence mapping.

**Ordered S3 work list:**

1. **WP022-F1 (D4):** Draft plan amendment formally accepting the `bincode` RUSTSEC-2025-0141 advisory (analogous to amendment #9 for `paste`). Update DV-017's "Governing amendment" column.
2. **WP022-F2 (D4):** Add `pub use` re-exports for `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` in `lib.rs`, or document the submodule-import convention.

---

## 7. Closure table (appended by S3 remediation)

**Session:** 0087 (WP-022 S3) — **Date:** 2026-08-18 — **Executor:** Claude Sonnet 5 (AI pair)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP022-F1 | **AMENDED** — Plan amendment #27 (`DOCS/PRIN_Project_Plan.md` §8.3) formally accepts the `bincode` RUSTSEC-2025-0141 advisory with a Coding Standards §6.2 threat assessment (advisory is `informational = "unmaintained"`, no patched version, no exploit/affected-API disclosure; dependency path `bincode 2.0.1 ← burn-core 0.16.1 ← burn 0.16.1 ← prin-train` confirmed via `cargo tree -p prin-train -i bincode`; no newer 2.x release per `cargo update -p bincode --dry-run`; compensating control is the existing `record_roundtrip_preserves_parameters` regression coverage on both `bands.rs`/`layers.rs`), same disposition class and per-cycle recheck cadence as amendment #9/DV-008 (`paste`). Maintainer approval granted (MichaelMaillet, 2026-08-18). `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-017's "Governing amendment" and "Current status" columns updated to reference amendment #27. | commit `c3ae5c8`; Project Plan amendment #27 | `cargo audit` re-run post-commit: still exactly 2 allowed warnings (`paste` RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141), exit code 0 — both now governed by an approved amendment (#9, #27 respectively). No new advisories introduced. |
| WP022-F2 | **FIXED** — Added `pub use bands::DiscreteDeltaThetaGammaParams;` and `pub use layers::ResonanceLayerParams;` to `crates/prin-train/src/lib.rs`, alongside the existing `pub use error::TrainError;`, so both `Params` types are nameable via the crate root in explicit type annotations. Regression test added: `crates/prin-train/tests/public_api.rs::params_are_nameable_at_crate_root` — two zero-sized functions that take `DiscreteDeltaThetaGammaParams<NdArray<f64>>`/`ResonanceLayerParams<NdArray<f64>>` by crate-root path; the test fails to *compile* (not just fail at runtime) if either re-export is ever removed, which is the correct regression class for a purely type-level ergonomics fix. | commit `a5458ef` | `cargo test -p prin-train --test public_api`: 1 passed, 0 failed. Full re-run: `cargo test --workspace` — all crates green, 0 failed (275+ tests across the workspace including the 38 `prin-train` tests: 33 unit + 1 new `public_api` + 2 parity + 2 doctests). `cargo fmt --all -- --check`: clean. `cargo clippy --workspace --all-targets -- -D warnings` and `--features strict-checks`: both clean. `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`: clean, 0 warnings (re-exported items inherit their original items' doc comments, so `#![warn(missing_docs)]` raises nothing new). |

**Delta re-audit commands (re-run against `c3ae5c8`):**

```powershell
cargo fmt --all -- --check                                                     # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                          # exit 0, clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0, clean
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps               # exit 0, 0 warnings
cargo test --workspace                                                         # exit 0, all crates green, 0 failed
cargo test -p prin-train --test public_api                                     # 1 passed, 0 failed
cargo audit                                                                    # exit 0, 2 allowed warnings (both amendment-governed)
cargo tree -p prin-train -i bincode                                            # confirms burn-core → burn → prin-train path
cargo update -p bincode --dry-run                                              # confirms already-latest, no fix available
```

No new deviation was introduced by either fix: WP022-F2 is a purely additive, type-level re-export with a compile-time regression test; WP022-F1 is a documentation-only governance action (no source/dependency change). A1–A10 are unaffected outside A6 (security — now fully governed, no open advisory-governance gap) and A8 (hygiene — `Params` re-export ergonomics now consistent with `TrainError`'s existing pattern).

**Delta re-audit date:** 2026-08-18 — **Result:** **CLEAN**. Both findings closed (1 FIXED, 1 AMENDED); no D1/D2/D3 findings; no second carry of any D4; local gate fully green with no newly introduced deviation. WP-022 S3 exit gate met — hand off to S4 (session 0088).

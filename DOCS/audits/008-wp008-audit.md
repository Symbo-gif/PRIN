# PRIN Audit Report — Cycle 008 / WP-008

**Date:** 2026-08-07
**Auditor:** Devin (AI pair)
**Scope:** WP-008 "Basic integrators" — `crates/prin-dynamics/src/integrate.rs`, `crates/prin-dynamics/src/lib.rs`, `crates/prin-dynamics/tests/parity_integrators.rs`
**Sessions:** 0029 (S1 implementation); 0030 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-1/0030-wp008-s2-basic-integrators.md`
**Git state:** `feat/wp006-oscillator-state` @ `64d41ef`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | Integrator trait + Euler/RK4/RK45 present; no exponential/Krylov/multi-rate; no undeclared files |
| Plan/architecture conformance (A2) | ✅ | Numerics in Rust; `Integrator` trait dispatch; no Python numerics; `#![forbid(unsafe_code)]` preserved |
| Tests in tandem + coverage (A3) | ⚠️ | 28 inline + 16 parity tests; 96.66% line coverage on `integrate.rs`; `NonFiniteValue` path untested (WP008-F2) |
| Numerical parity + invariants (A4) | ⚠️ | 16 golden-trajectory parity tests pass; RK4 order h^4 and RK45 tolerance property hold; FSAL cache bug confirmed (WP008-F1) |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy `-D warnings` (default + strict), rustdoc `-D warnings` all clean |
| Security (A6) | ✅ | Snyk Code 0 issues on both files; `cargo audit` only inherited `paste` (amendment #9); no `unsafe`; no new deps |
| Docstring/doc coverage (A7) | ⚠️ | Rustdoc 100% public, 0 warnings; `check_finite` doc inaccurate (WP008-F3); `lib.rs` module doc stale (WP008-F4) |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers; no orphan files; `__all__` N/A (Rust); gitignore respected |
| CI status (A9) | ✅ | `rust.yml` runs fmt, clippy, clippy-strict, test (3 OS), test-strict; local equivalents all green |
| Artefact trail (A10) | ✅ | S1 handoff at `DOCS/experiments/0029-wp008-s1-handoff.md`; session register consistent; predecessor closure (WP-007) committed |

## 2. Methodology

Commands executed and environments used (every claim is evidence-backed):

```powershell
# Scope inspection
git show --stat 64d41ef
git diff 6f55691..64d41ef -- crates/prin-dynamics/Cargo.toml
git diff 6f55691..64d41ef -- Cargo.lock
git diff 6f55691..64d41ef -- crates/prin-dynamics/src/lib.rs

# Quality gates
cargo fmt --all -- --check                          # PASS (no output)
cargo clippy --workspace --all-targets -- -D warnings  # PASS
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings  # PASS
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # PASS, 0 warnings

# Tests
cargo test -p prin-dynamics                          # 107 unit + 16 parity_integrators + 9 parity_models = 132 passed
cargo test -p prin-dynamics --features strict-checks # 108 unit + 16 + 9 = 133 passed
cargo test --workspace                               # all green (151 tests total)

# Coverage
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
#   integrate.rs: 897 lines, 30 missed, 96.66% line coverage
#   TOTAL:        2762 lines, 64 missed, 97.68% line coverage

# Security
cargo audit                                          # 1 inherited paste RUSTSEC-2024-0436 (amendment #9); no new findings
# Snyk Code (MCP):
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\src\integrate.rs severity_threshold=low  → 0 issues
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\tests\parity_integrators.rs severity_threshold=low → 0 issues

# Hygiene
# grep TODO|FIXME|HACK|XXX|stub|unimplemented!|todo! in integrate.rs → 0 matches
# grep unsafe in integrate.rs → 0 matches

# FSAL bug reproduction (temporary test, not committed)
# cargo test -p prin-dynamics --test fsal_repro -- --nocapture
#   → FAILED: reused vs fresh differ in phase by 6.0e-10, amplitude by 1.8e-9
```

## 3. Detailed findings

### 3.1 A1 — Scope conformance

The S1 commit `64d41ef` touches exactly four files:

| File | Change | In scope? |
|---|---|---|
| `crates/prin-dynamics/src/integrate.rs` | +1531 lines (stub → full implementation) | ✅ |
| `crates/prin-dynamics/src/lib.rs` | +4 lines (`pub use integrate::…`) | ✅ |
| `crates/prin-dynamics/tests/parity_integrators.rs` | +344 lines (new parity test file) | ✅ |
| `DOCS/experiments/0029-wp008-s1-handoff.md` | +107 lines (S1 handoff note) | ✅ |

No exponential, Krylov, or multi-rate methods implemented (non-goals respected). No Python files touched. No `Cargo.toml` or `Cargo.lock` changes (no new dependencies). No undeclared files.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** All numerics in `prin-dynamics` (Rust core). No Python numerics. ✅
- **One algorithm one implementation:** Each integrator (Euler, RK4, RK45) has a single implementation behind the `Integrator` trait. ✅
- **Explicit state/seeding:** `OscillatorState` is explicit; integrators are deterministic (no RNG). ✅
- **`#![forbid(unsafe_code)]`:** Preserved in `lib.rs`; no `unsafe` in `integrate.rs`. ✅
- **Numerical guards:** Phase wrap `[0, 2π)`, amplitude clamp `[1e-6, 10]`, derivative clamp `±1e4` applied via `make_final_state` and `StateDerivatives::new`. ✅

### 3.3 A3 — Tests in tandem + coverage

Tests are in the same commit as the implementation (single S1 commit `64d41ef`). 28 inline unit/property tests in `integrate.rs` and 16 parity tests in `parity_integrators.rs`.

Coverage (`cargo llvm-cov -p prin-dynamics --features strict-checks`):
- `integrate.rs`: 897 lines, 30 missed, **96.66%** line coverage (≥95% gate met)
- 30 missed lines: `NonFiniteValue` error returns (lines 184–208, strict-checks), `EulerIntegrator::default` (251–253), `RK4Integrator::default` (364–366)

The `IntegrateError::NonFiniteValue` error path is implemented but not exercised by any test (WP008-F2). The S1 handoff claims it is "validated" by `rk45_rejects_invalid_tolerances` and other tests, but those test `InvalidTimestep` and `ZeroSteps`, not `NonFiniteValue`.

### 3.4 A4 — Numerical parity + invariants

**Golden trajectories:** 16 parity tests pass comparing Rust Euler/RK4 against PRINet 3.0 `torch.float64` reference values:
- Kuramoto mean-field (N=2): Euler + RK4 × 1/5/10 steps — `rtol=1e-6, atol=1e-8` (1-step), `rtol=1e-5, atol=1e-7` (multi-step)
- Kuramoto full (N=3): Euler + RK4 × 5 steps — `rtol=1e-10, atol=1e-12`
- Hopf mean-field (N=3): Euler + RK4 × 5 steps — `rtol=1e-5, atol=1e-7`
- Stuart–Landau full (N=2): Euler + RK4 × 5 steps — `rtol=1e-5, atol=1e-7`

Tolerances are consistent with Plan §5 and amendment #14 (f32-complex numerical hazard). No tolerance drift or weakened assertions detected.

**RK4 order h^4:** `rk4_order_h4_convergence` unit test + `parity_rk4_order_h4_on_amplitude_decay` parity test verify error ratio ≈ 16 (2^4). ✅

**RK45 tolerance property:** `rk45_tolerance_property` unit test + `parity_rk45_tolerance_property_on_amplitude_decay` parity test verify tighter tolerance → smaller error. ✅

**FSAL cache bug (WP008-F1):** Independently reproduced. When an `RK45Integrator` instance is reused across two `integrate_adaptive` calls with different initial states (same `n`), the FSAL cache check `self.ks[0].len() != 3 * n` passes (buffer is sized from the previous call), and k1 is NOT recomputed. The stale k7 from the previous integration is used as k1 for the first step of the new integration, producing incorrect results. Reproduction showed ~6e-10 phase and ~1.8e-9 amplitude deviation from a fresh integrator. No existing test exercises integrator reuse across `integrate_adaptive` calls.

### 3.5 A5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Rustdoc | `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | PASS |

### 3.6 A6 — Security

| Control | Scope | Result |
|---|---|---|
| Snyk Code | `integrate.rs` (severity_threshold=low) | 0 issues |
| Snyk Code | `parity_integrators.rs` (severity_threshold=low) | 0 issues |
| `cargo audit` | workspace | 1 inherited `paste` RUSTSEC-2024-0436 (amendment #9); no new findings |
| `unsafe` scan | `integrate.rs` | 0 matches; `#![forbid(unsafe_code)]` preserved |
| New dependencies | `Cargo.toml` / `Cargo.lock` diff | None |
| Secrets / codegen | diff inspection | None |

Snyk Open Source and pip-audit not applicable (no dependency manifest changes in this S1).

### 3.7 A7 — Documentation coverage

- Rustdoc: 100% public API documented; `cargo doc -D warnings` passes with 0 warnings. ✅
- `check_finite` doc comment (line 177–178) claims "phase wrap of `NaN` yields `NaN` which is repaired to `0.0` here" but the non-strict branch does nothing (`let _ = state`). Non-finite phase/frequency can pass through in non-strict mode (WP008-F3).
- `lib.rs` module doc (line 12–13) lists "exponential (direct + Krylov), and multi-rate sub-stepped RK4 integrators" which are WP-008 non-goals and not implemented. Stale text from the pre-S1 stub (WP008-F4).

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/HACK/XXX/stub/unimplemented!/todo! markers in `integrate.rs`. ✅
- No orphan files. ✅
- `__all__` N/A (Rust). ✅
- `.gitignore` respected. ✅

### 3.9 A9 — CI status

`.github/workflows/rust.yml` includes: `fmt`, `clippy`, `clippy-strict`, `test` (ubuntu/windows/macos), `test-strict`. All local equivalents pass. CI is the authoritative merge gate; local verification confirms all configured gates are green on the WP branch.

### 3.10 A10 — Artefact trail

- S1 handoff note: `DOCS/experiments/0029-wp008-s1-handoff.md` — present, acceptance-to-evidence map complete. ✅
- Session register: `DOCS/sessions/SESSION_REGISTER.md` — 0029 READY, 0030 PLANNED. Consistent. ✅
- Predecessor closure: WP-007 S4 (commit `6f55691`) — committed, Project State Report 007 present. ✅
- Deviation ledger: No carried findings from cycle 007. ✅

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP008-F1 | D2 | `crates/prin-dynamics/src/integrate.rs:716` | FSAL cache in `RK45Integrator::integrate_adaptive` is not invalidated at the start of a new integration. The check `self.ks[0].len() != 3 * n` only verifies buffer size, not cache validity. Reusing an integrator across two `integrate_adaptive` calls with different states (same `n`) produces silently incorrect results (~6e-10 phase deviation confirmed by reproduction). | Coding Standards (correctness); Testing Standards §1 (test-in-tandem: reuse scenario untested) | Add a `fsal_valid: bool` flag (or clear `self.ks[0]` at the start of `integrate_adaptive`); add a regression test that reuses an integrator across two calls and asserts equality with fresh integrators. |
| WP008-F2 | D3 | `crates/prin-dynamics/src/integrate.rs:184–208` | `IntegrateError::NonFiniteValue` error path (strict-checks) is not exercised by any test. S1 handoff claims it is "validated" but the cited tests cover `InvalidTimestep`/`ZeroSteps`, not `NonFiniteValue`. Coverage confirms lines 184–208 are uncovered. | Testing Standards §1 (test-in-tandem); S1 handoff accuracy | Add a test under `--features strict-checks` that produces a non-finite value (e.g., via a custom `Dynamics` impl returning `f64::NAN` derivatives) and asserts `IntegrateError::NonFiniteValue`. |
| WP008-F3 | D4 | `crates/prin-dynamics/src/integrate.rs:177–178` | `check_finite` doc comment claims "phase wrap of `NaN` yields `NaN` which is repaired to `0.0` here" but the non-strict branch does nothing (`let _ = state`). Non-finite phase/frequency can pass through to output in non-strict mode. | Documentation Standards §2 (doc accuracy) | Either repair non-finite phase/frequency to safe defaults in the non-strict branch, or correct the doc comment to state that non-finite repair is limited to amplitude (via `clamp_amplitude`) and that phase/frequency non-finite values are only caught under `strict-checks`. |
| WP008-F4 | D4 | `crates/prin-dynamics/src/lib.rs:12–13` | Module doc lists "exponential (direct + Krylov), and multi-rate sub-stepped RK4 integrators" which are WP-008 non-goals and not implemented. Stale text from the pre-S1 stub. | Documentation Standards §2 (doc accuracy); WP-008 non-goals | Update the `integrate` module doc to list only the implemented integrators (Euler, RK4, adaptive RK45). Exponential/Krylov/multi-rate belong to Phase 2 (WP-009+). |
| WP008-F5 | D4 | `crates/prin-dynamics/src/integrate.rs:528,531` | `RK45Integrator::new` uses `IntegrateError::InvalidTimestep { dt: rtol }` for invalid tolerances, which is semantically misleading (the error variant says "invalid timestep" but the problem is an invalid tolerance). The test `rk45_rejects_invalid_tolerances` only checks `is_err()`, not the specific variant. | Coding Standards (typed error accuracy) | Either add a dedicated `IntegrateError::InvalidTolerance` variant, or document the reuse of `InvalidTimestep` for tolerance validation. Update the test to assert the specific variant. |

## 5. Deviation-ledger delta

New findings added to the ledger: WP008-F1 (D2), WP008-F2 (D3), WP008-F3 (D4), WP008-F4 (D4), WP008-F5 (D4).

Carried findings re-inspected: None (cycle 007 closed with zero carried findings).

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS**

No D1 finding (trajectory breach) was raised. The acceptance criteria are met:
- Golden trajectories pass at `rtol=1e-6, atol=1e-8` (and tighter for pure f64 paths). ✅
- RK4 order h^4 and RK45 tolerance properties hold. ✅
- Failure paths are typed (`IntegrateError` enum with six variants). ✅
- Coverage 96.66% on new code (≥95% gate). ✅
- All quality, security, and documentation gates green. ✅

The FSAL cache bug (WP008-F1, D2) is a correctness issue in a new numerical capability that does not affect the parity-tested paths (Euler/RK4) or the acceptance tests, but could produce silently wrong results when an integrator is reused across multiple `integrate_adaptive` calls. It must be fixed in S3.

**Ordered S3 action list:**

1. **WP008-F1 (D2):** Fix the FSAL cache invalidation in `RK45Integrator::integrate_adaptive`. Add a `fsal_valid: bool` flag or clear `self.ks[0]` at the start of each `integrate_adaptive` call. Add a regression test that reuses an integrator across two calls with different states and asserts equality with fresh integrators.
2. **WP008-F2 (D3):** Add a test under `--features strict-checks` that triggers `IntegrateError::NonFiniteValue` (e.g., via a custom `Dynamics` impl or a model configuration that produces non-finite derivatives).
3. **WP008-F3 (D4):** Correct the `check_finite` doc comment to accurately describe the non-strict behavior (amplitude repaired via clamp; phase/frequency non-finite only caught under strict-checks), or implement the claimed repair.
4. **WP008-F4 (D4):** Update the `lib.rs` `integrate` module doc to list only implemented integrators (Euler, RK4, RK45).
5. **WP008-F5 (D4):** Either add `IntegrateError::InvalidTolerance` or document the `InvalidTimestep` reuse for tolerance validation; update `rk45_rejects_invalid_tolerances` to assert the specific variant.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP008-F1 | _pending S3_ | | |
| WP008-F2 | _pending S3_ | | |
| WP008-F3 | _pending S3_ | | |
| WP008-F4 | _pending S3_ | | |
| WP008-F5 | _pending S3_ | | |

**Delta re-audit date:** _pending S3_ — **Result:** _pending_

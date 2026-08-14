# PRIN Audit Report — Cycle 015 / WP-015

**Date:** 2026-08-14
**Auditor:** Devin (AI pair)
**Scope:** WP-015 "OscilloSim sparse simulation engine" — `crates/prin-sim/` (engine, CSR coupling, pruning, chimera, parity tests)
**Sessions:** 0057 (S1 implementation); 0058 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-2/0058-wp015-s2-oscillosim-sparse-simulation-engine.md`
**Git state:** `main` @ `bfc2417`
**Verdict:** **FAIL**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope present; no undeclared features shipped |
| Plan/architecture conformance (A2) | ✅ | Crate layering `dynamics → sim` correct; numerics in Rust; `#![forbid(unsafe_code)]`; explicit `Seed` flow |
| Tests in tandem + coverage (A3) | ⚠️ | Tests in same commit; line coverage ≥95% all files; but `strict-checks` gate not run by S1 and fails (F1) |
| Numerical parity + invariants (A4) | ✅ | 21 parity tests pass: Kuramoto N=8/64/256, Stuart–Landau N=8/16, trajectory N=16; memory bounded at N=10k |
| Quality gates (A5) | ⚠️ | fmt/clippy/rustdoc green; `cargo test --workspace` green; `--features strict-checks` **FAILS** (F1) |
| Security (A6) | ✅ | `cargo audit` clean (1 allowed `paste` advisory); Snyk Code 0 issues; Snyk SCA 0 issues; no `unsafe` |
| Docstring/doc coverage (A7) | ✅ | `missing_docs` warned; rustdoc `-D warnings` clean; 1 doctest passes |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub markers; 6 unused runtime deps + 2 unused dev-deps (F4); misleading crate description (F5) |
| CI status (A9) | ❌ | `test-strict` job **failed** on `bfc2417`; all other rust jobs green (F1) |
| Artefact trail (A10) | ✅ | S1 handoff note, session register, session brief status all consistent |

## 2. Methodology

Commands executed and environments used (every claim backed by command output):

```powershell
# Git inspection
git log --oneline -30
git show --stat bfc2417
git show bfc2417 -- DOCS/sessions/SESSION_REGISTER.md

# Quality gates
cargo fmt --all -- --check                                    # PASS (exit 0)
cargo clippy --workspace --all-targets -- -D warnings         # PASS (exit 0)
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings  # PASS (exit 0)
cargo test --workspace                                        # PASS (all green)
cargo test --workspace --features strict-checks               # FAILED (4 tests in prin-sim)

# Coverage
cargo llvm-cov -p prin-sim --summary-only
# chimera.rs:      100.00% lines (156/156), 100.00% functions (15/15)
# csr_coupling.rs:  99.83% lines (578/579), 100.00% functions (63/63)
# engine.rs:        96.50% lines (524/543),  93.44% functions (57/61)
# pruning.rs:      100.00% lines (270/270), 100.00% functions (34/34)

# Rustdoc
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # PASS (exit 0)

# Security
cargo audit                                                   # 1 allowed warning (paste RUSTSEC-2024-0436)
# Snyk Code scan: path=C:\dev\PRIN\crates\prin-sim\src, severity=low  → 0 issues
# Snyk SCA scan:  path=C:\dev\PRIN, all_projects=true, severity=low   → 0 issues

# CI verification
gh run list --limit 5
gh run view 31803599728 --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
gh run view 31803599728 --log-failed
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

The WP-015 declaration (Project State Report 014 §6) defines scope as:
`crates/prin-sim/` — engine core, CSR coupling storage, pruning, integration
orchration, and chimera metric integration.

S1 commit `bfc2417` delivered:

| File | Lines | Content |
|---|---|---|
| `src/lib.rs` | 57 | Module declarations, re-exports, crate-level docs |
| `src/error.rs` | 85 | `SimError` enum (10 variants) |
| `src/csr_coupling.rs` | 900 | `SparseCoupling` CSR matrix, builders, SpMV coupling |
| `src/engine.rs` | 871 | `SparseKuramoto`, `SparseStuartLandau`, `OscilloSim`, `Trajectory` |
| `src/pruning.rs` | 415 | `PruningStrategy`, `PruningResult` with apply/restore |
| `src/chimera.rs` | 290 | `ChimeraMetrics`, `compute_chimera_metrics`, trajectory variant |
| `tests/parity_sparse_vs_dense.rs` | 519 | 21 integration tests |

All declared scope items are present. No undeclared features were shipped.
Non-goals (parameter sweeps, GPU dispatch, 1M performance claims) were
respected — the handoff note explicitly defers them.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** `prin-sim` depends on `prin-dynamics`, `prin-metrics`,
  `prin-kernels` (workspace). The dependency graph matches the plan's
  `dynamics → sim` layering rule.
- **Numerics in Rust:** All numerical logic (SpMV, trig decomposition,
  diffusive coupling, integration) is in Rust. No Python numerics were
  duplicated. No PyO3 bindings were added (correctly deferred).
- **One algorithm, one implementation:** The sparse models implement the
  same `Dynamics` trait as the dense models but use CSR SpMV instead of
  dense iteration. This is the intended production path for large N; the
  dense models remain the reference. Parity tests verify equivalence.
- **Seeding:** All RNG flows through `prin_dynamics::Seed`. The
  `engine_deterministic_across_runs` test verifies identical trajectories
  from the same seed. No thread-local or global state.
- **`unsafe`:** `#![forbid(unsafe_code)]` is enforced at the crate root.

### 3.3 A3 — Tests in tandem + coverage

**Tests in tandem:** All source code and tests were added in a single commit
(`bfc2417`). The Testing Standards §1 require tests "in the same session's
commit range" — having them in the same commit satisfies this. However, the
commit message is `docs(WP015 S1): …` despite adding 3,195 lines of source
code (see F2).

**Coverage** (`cargo llvm-cov -p prin-sim --summary-only`):

| File | Lines | Missed | Line % | Functions | Missed | Func % |
|---|---|---|---|---|---|---|
| `chimera.rs` | 156 | 0 | 100.00% | 15 | 0 | 100.00% |
| `csr_coupling.rs` | 579 | 1 | 99.83% | 63 | 0 | 100.00% |
| `engine.rs` | 543 | 19 | 96.50% | 61 | 4 | 93.44% |
| `pruning.rs` | 270 | 0 | 100.00% | 34 | 0 | 100.00% |

All files meet the ≥95% line coverage gate (Testing Standards §4). The
`engine.rs` function coverage is 93.44% (4 of 61 functions uncovered), but
the gate is on line coverage, not function coverage.

**Strict-checks gate:** The S1 handoff quality-gates table does not include
`cargo test --workspace --features strict-checks`. This command is required
by Testing Standards §6 and AGENTS.md. When run, 4 tests fail (see F1).

### 3.4 A4 — Numerical parity + invariants

Independently reproduced all 21 integration tests + 105 unit tests + 1
doctest:

```
cargo test -p prin-sim
# 105 passed; 0 failed (unit)
# 21 passed; 0 failed (integration)
# 1 passed; 0 failed (doctest)
```

Parity evidence:
- **Kuramoto N=8 ring:** sparse vs dense derivatives at `ε=1e-12` ✅
- **Kuramoto N=64 ring:** at `ε=1e-12` ✅
- **Kuramoto N=256 ring:** at `ε=1e-10` ✅
- **Stuart–Landau N=8 ring:** at `ε=1e-10` ✅
- **Stuart–Landau N=16 ring:** at `ε=1e-10` ✅
- **Engine trajectory N=16:** 100-step RK4 vs `integrate_fixed` at `ε=1e-10` ✅
- **Large-N memory:** N=10,000, nnz=200,000, memory=3,280,008 bytes (< 5 MB) ✅
- **Determinism:** identical trajectories from `Seed::new(42, 0)` across runs ✅
- **Chimera metrics:** all metrics in valid ranges on a 32-oscillator trajectory ✅

Tolerances are set at write time (new tests, not loosened existing tests).
No tolerance drift or weakened assertions.

### 3.5 A5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Tests | `cargo test --workspace` | PASS (all green) |
| Tests (strict) | `cargo test --workspace --features strict-checks` | **FAIL** (4 tests, F1) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS |

### 3.6 A6 — Security

| Gate | Result |
|---|---|
| `cargo audit` | 1 allowed warning (`paste` RUSTSEC-2024-0436, amendment #9) |
| Snyk Code (`crates/prin-sim/src`, severity=low) | 0 issues |
| Snyk SCA (whole repo, `all_projects=true`, severity=low) | 0 issues |
| `unsafe` scan | `#![forbid(unsafe_code)]` enforced; no `unsafe` blocks |
| Secrets scan | No secrets in diff; no runtime codegen |

No Python code was modified in S1, so Python security gates (bandit,
pip-audit) are unchanged from the WP-014 S4 baseline and remain green.

### 3.7 A7 — Documentation

- `#![warn(missing_docs)]` enforced; all public items have doc comments.
- Rustdoc builds clean with `-D warnings`.
- 1 doctest in `engine.rs` (usage example) compiles and passes.
- No Python code changed; `interrogate` and Sphinx gates unchanged.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/stub scan:** No matches in `crates/prin-sim/`.
- **Unused dependencies:** 6 unused runtime deps + 2 unused dev-deps (F4).
- **Misleading crate description:** `Cargo.toml` description and `README.md`
  mention "async pipelines" and "parallel parameter sweeps" — not implemented
  (F5).
- **`__all__`:** N/A (Rust crate, not Python).
- **Orphan files:** None detected.

### 3.9 A9 — CI status

CI run for `bfc2417` (workflow `rust`, run ID 31803599728):

| Job | Result |
|---|---|
| fmt | success |
| clippy | success |
| clippy-strict | success |
| test (ubuntu-latest) | success |
| test (windows-latest) | success |
| test (macos-latest) | success |
| **test-strict** | **failure** |
| docs | success |
| audit | success |

The `test-strict` job runs `cargo test --workspace --features strict-checks`
and fails with 4 test failures in `prin-sim` (see F1). All other workflows
(python, snyk, repro) are green; gpu is skipped (expected).

### 3.10 A10 — Artefact trail

- S1 handoff note: `DOCS/experiments/0057-wp015-s1-handoff.md` ✅
- Session register: session 0057 flipped READY → COMPLETE ✅
- Session brief: status flipped to COMPLETE ✅
- Prior cycle audit: `DOCS/audits/014-wp014-audit.md` (CLEAN delta re-audit) ✅
- Prior cycle state report: `DOCS/reports/014-project-state.md` ✅
- Deviation ledger: all WP-014 findings FIXED; no unresolved D1/D2 ✅

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP015-F1 | D1 | `crates/prin-sim/src/engine.rs:637,653`; `crates/prin-sim/src/pruning.rs:257,387` | `cargo test --workspace --features strict-checks` fails with 4 test failures. Tests create `OscillatorState` with amplitudes outside the strict-checks range `[1e-6, 10.0]`: `apply_guards_wraps_and_clamps` uses 20.0; `engine_with_low_amplitude_state` uses 1e-7; `apply_and_restore_round_trip` and `restore_with_freq_band` use `default_amplitude=0.0`. The S1 handoff did not run this gate and claims all gates green. CI `test-strict` job is red on `bfc2417`. | Testing Standards §6; Development Workflow Standards §3 (S1 exit gate "Local gate green"); Coding Standards §5 | Fix the 4 tests to use amplitudes within `[AMPLITUDE_MIN, AMPLITUDE_MAX]` or gate them with `#[cfg(not(feature = "strict-checks"))]` where the test scenario is specific to non-strict clamping. Run `cargo test --workspace --features strict-checks` and verify green. |
| WP015-F2 | D2 | commit `bfc2417` | Misleading commit message: tagged `docs(WP015 S1): mark session 0057 COMPLETE and update crate documentation` but adds 3,195 lines of source code (engine, CSR coupling, pruning, chimera, parity tests). The conventional-commit type should be `feat(WP-015)`. | Repository hygiene / commit message conventions | No source fix needed (S2 is read-only). S3 should amend the commit message or add a corrective note. Future S1 commits should use `feat(WP-NNN): …` for code additions. |
| WP015-F3 | D2 | `crates/prin-sim/src/engine.rs:164-171, 278-285` | Error mapping in `SparseKuramoto::compute_derivatives` and `SparseStuartLandau::compute_derivatives` converts any `SimError` from coupling computations to `StateError::LengthMismatch`, setting `got: 0` for non-dimension errors. This loses error information and misclassifies non-dimension failures as length mismatches. | Coding Standards (typed errors, error handling) | Map `SimError::DimensionMismatch` to `StateError::LengthMismatch` but propagate other `SimError` variants via a more appropriate error path (e.g., `StateError::NonFiniteValue` or a new variant). |
| WP015-F4 | D3 | `crates/prin-sim/Cargo.toml` | 6 unused runtime dependencies: `prin-kernels`, `ndarray`, `rayon`, `rand`, `rand_pcg`, `tracing`. 2 unused dev-dependencies: `proptest`, `criterion`. These increase build time and supply-chain attack surface. | Repository hygiene (A8); Coding Standards §6 (dependency hygiene) | Remove unused dependencies from `Cargo.toml`. If `prin-kernels` is intended for future GPU dispatch, add a comment but remove from the deps list until used. |
| WP015-F5 | D3 | `crates/prin-sim/Cargo.toml:3`; `crates/prin-sim/README.md:3-4` | Misleading crate description and README: mention "async pipelines" and "parallel parameter sweeps" which are not implemented (non-goals for this WP). | Documentation Standards (accurate documentation) | Update `Cargo.toml` description and `README.md` to reflect what was actually delivered: CSR sparse coupling, chimera detection, pruning, integration orchestration. |
| WP015-F6 | D3 | `crates/prin-sim/` (test suite) | No property tests (`proptest`) for the sparse simulation engine. The Testing Standards §2 list proptest as a required test layer for invariants. While existing tests cover key invariants at representative values, property tests would strengthen the parity and determinism evidence (e.g., sparse-vs-dense parity for arbitrary N, memory_bytes correctness for arbitrary nnz). | Testing Standards §2 | Add proptest-based property tests for: (a) sparse-vs-dense Kuramoto parity at arbitrary N and ring degree; (b) `memory_bytes()` correctness for arbitrary N and nnz; (c) determinism for arbitrary seeds. |

## 5. Deviation-ledger delta

New findings added to the ledger: WP015-F1 (D1), WP015-F2 (D2), WP015-F3
(D2), WP015-F4 (D3), WP015-F5 (D3), WP015-F6 (D3).

Carried findings re-inspected: all WP-014 findings (WP014-F1 through F7)
remain FIXED. No carried findings are affected by the WP-015 S1 changes.

## 6. Verdict and required actions

**Verdict: FAIL**

The S1 exit gate is not met: `cargo test --workspace --features strict-checks`
fails with 4 test failures (WP015-F1), and the CI `test-strict` job is red
on the S1 commit. The S1 handoff note did not run this required gate and
incorrectly claims all quality gates are green. This is a trajectory breach
— the S1 exit criteria ("Local gate green") is claimed but not achieved.

**Ordered S3 action list (severity order):**

1. **WP015-F1 (D1):** Fix the 4 strict-checks test failures. Either:
   - `apply_guards_wraps_and_clamps`: use amplitude 10.0 (within range) and
     test that `apply_guards` is a no-op, or gate with
     `#[cfg(not(feature = "strict-checks"))]` since the test scenario
     (amplitude 20.0) can only arise under non-strict clamping.
   - `engine_with_low_amplitude_state`: use amplitude `AMPLITUDE_MIN` (1e-6)
     instead of 1e-7.
   - `apply_and_restore_round_trip` and `restore_with_freq_band`: use
     `AMPLITUDE_MIN` (1e-6) as `default_amplitude` instead of 0.0, or
     validate `default_amplitude` in `PruningResult::restore`.
   Run `cargo test --workspace --features strict-checks` and verify all
   green. Re-check CI `test-strict` job.

2. **WP015-F2 (D2):** Amend the commit message or add a corrective note
   documenting that `bfc2417` is a `feat` commit mislabeled as `docs`.

3. **WP015-F3 (D2):** Fix the error mapping in
   `SparseKuramoto::compute_derivatives` and
   `SparseStuartLandau::compute_derivatives` to preserve error type
   information for non-dimension errors.

4. **WP015-F4 (D3):** Remove unused dependencies from
   `crates/prin-sim/Cargo.toml`: `prin-kernels`, `ndarray`, `rayon`, `rand`,
   `rand_pcg`, `tracing`, `proptest`, `criterion`.

5. **WP015-F5 (D3):** Update `Cargo.toml` description and `README.md` to
   remove references to unimplemented "async pipelines" and "parallel
   parameter sweeps".

6. **WP015-F6 (D3):** Add proptest-based property tests for sparse-vs-dense
   parity, memory_bytes correctness, and determinism.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP015-F1 | | | |
| WP015-F2 | | | |
| WP015-F3 | | | |
| WP015-F4 | | | |
| WP015-F5 | | | |
| WP015-F6 | | | |

**Delta re-audit date:** — **Result:** —

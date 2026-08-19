# PRIN Audit Report — Cycle 024 / WP-024

**Date:** 2026-08-19
**Auditor:** Devin (AI pair), session 0094
**Scope:** WP-024 "Oscillator-aware optimizers" — `crates/prin-train/src/{feedback,sync_gd,rip,scalr,support,error}.rs`, `crates/prin-train/tests/{parity_optimizers,public_api}.rs`, `crates/prin-train/src/lib.rs`, `crates/prin-train/Cargo.toml`
**Sessions:** 0093 (S1 implementation); 0094 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-4/0094-wp024-s2-oscillator-aware-optimizers.md`
**Git state:** `main` @ `bac481e`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Delivered scope matches session brief and PRINet 3.0 reference; PSR-023 §7 declaration named non-existent classes (DV-020, WP024-F1) |
| Plan/architecture conformance (A2) | ✅ | Crate layering correct; no Python numerics; `forbid(unsafe_code)` maintained; deterministic state serialization |
| Tests in tandem + coverage (A3) | ✅ | 57 new unit + 5 parity + 1 public-api + 3 doctests; coverage 97.9–100% regions / 99.7–100% lines on all four new files |
| Numerical parity + invariants (A4) | ✅ | 5 golden-value parity tests vs. actual PRINet 3.0 classes at `rtol=1e-9, atol=1e-12`; all pass |
| Quality gates (A5) | ✅ | fmt/clippy (default + strict-checks)/rustdoc/ruff/mypy all clean |
| Security (A6) | ✅ | `forbid(unsafe_code)`; bandit 0 issues; `cargo audit` exit 0 (2 allowed warnings, amendment-governed); Snyk blocked (unauthenticated, reported as such) |
| Docstring/doc coverage (A7) | ✅ | interrogate 100% (106/106); rustdoc `missing_docs` clean; module-level docs with update equations; doctest examples for all three optimizers |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers; ad-hoc reference script gitignored; `pub use` re-exports consistent |
| CI status (A9) | ✅ | Nothing pushed yet (amendment #28 cadence); local gate reproduction fully green |
| Artefact trail (A10) | ✅ | PSR-023, audit 023, S1 handoff note, DV-020 register entry all present and consistent |

## 2. Methodology

All commands executed on Windows, local hardware, 2026-08-19. Every claim below is backed by the command output shown.

```powershell
# Format and lint
cargo fmt --all -- --check                                                    # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0, clean
cargo clippy -p prin-train --all-targets --features strict-checks -- -D warnings  # exit 0, clean
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps              # exit 0, 0 warnings

# Tests
cargo test -p prin-train                                                      # 150 unit + 14 integration + 9 doctests, all pass
cargo test --workspace                                                        # all pass, 0 failures

# Coverage
cargo llvm-cov -p prin-train --summary-only                                   # see §3.3

# Security
cargo audit                                                                   # exit 0; 2 allowed warnings (paste RUSTSEC-2024-0436, bincode RUSTSEC-2025-0141)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 0 issues

# Python gates (no Python files touched; run to confirm no regressions)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 50 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues found in 18 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (106/106)

# Hygiene
git diff --name-only bac481e~1..bac481e -- "*.py"                             # (empty — no tracked Python files touched)
git check-ignore DOCS/test_and_benchmark_results/wp024_generate_prinet_references.py  # confirmed gitignored
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Session brief mission:** "Implement SCALR, RIP, SyncGD, order-parameter feedback, state serialization, and thin torch-side optimizer contracts."

**Delivered (14 files, +2872/−6 lines):**

| File | Change |
|---|---|
| `crates/prin-train/src/feedback.rs` | **New.** `OrderParameter`, `StepFeedback`, `OscillatorOptimizer` trait |
| `crates/prin-train/src/sync_gd.rs` | **New.** `SyncGd`/`SyncGdConfig`/`SyncGdState` |
| `crates/prin-train/src/rip.rs` | **New.** `Rip`/`RipConfig`/`RipState` |
| `crates/prin-train/src/scalr.rs` | **New.** `Scalr`/`ScalrConfig`/`ScalrState` |
| `crates/prin-train/src/error.rs` | Extended with 8 new `TrainError` variants |
| `crates/prin-train/src/support.rs` | Added shared `sgd_update` core |
| `crates/prin-train/src/lib.rs` | Module declarations + `pub use` re-exports |
| `crates/prin-train/Cargo.toml` | Added `serde_json` dev-dependency (workspace-existing) |
| `crates/prin-train/tests/parity_optimizers.rs` | **New.** 5 golden-value parity tests |
| `crates/prin-train/tests/public_api.rs` | Extended with optimizer re-export regression |
| `DOCS/experiments/0093-wp024-s1-handoff.md` | **New.** S1 handoff note |
| `DOCS/experiments/README.md` | Index updated |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | DV-020 added |

**Non-goals respected:** No Python bindings (WP-025), no training-loop integration (WP-027), no end-to-end models or experiment statistics.

**⚠️ PSR-023 §7 naming discrepancy (DV-020 → WP024-F1).** PSR-023 §7's WP-024 declaration names `PhaseAdam`/`KuramotoOptimizer` and `phase_adam.rs`/`kuramoto_optimizer.rs`. `grep -rl "PhaseAdam\|KuramotoOptimizer"` against the full archived PRINet 3.0 tree returns zero matches — those class names never existed in the reference. The session brief (`0093-wp024-s1-oscillator-aware-optimizers.md`) mission text instead names SCALR/RIP/SyncGD, matching the Rebuild Planning Document's normative `nn/optimizers.py` mapping and PRINet 3.0's actual `SCALROptimizer`/`RIPOptimizer`/`SynchronizedGradientDescent` classes. S1 correctly followed the session brief and the verifiable reference. This is a governance-artifact drafting inconsistency in PSR-023 §7, not a code defect. See WP024-F1 below.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** All new code lives in `prin-train`, the correct crate for trainable components. No cross-layer violations.
- **No numerics in Python:** `git diff --name-only bac481e~1..bac481e -- "*.py"` returns empty — no tracked Python file was touched. The ad-hoc `wp024_generate_prinet_references.py` is gitignored (confirmed).
- **Explicit state/seeding:** `OscillatorOptimizer` trait mandates `state_dict`/`load_state_dict`; all three optimizers implement serde `State` snapshots; `load_state_dict` re-validates through the original constructor (untrusted-input-at-public-boundary discipline).
- **`#![forbid(unsafe_code)]`:** Maintained at crate root. `grep unsafe` in `prin-train/src/` returns only the `forbid` attribute itself.
- **One algorithm, one implementation:** Each optimizer is a single Rust implementation, no duplicated logic.
- **Documented deviation (Rip fixed square shape):** PRINet 3.0's `RIPOptimizer` silently skips the Hebbian term for non-square-matching parameters; `Rip` fixes `n_oscillators` at construction and returns `TrainError::ShapeMismatch` on mismatch, per Coding Standards §2.2 ("validate public inputs at every public boundary"). Documented in `rip.rs` module docs with full rationale. ✅

### 3.3 A3 — Tests in tandem + coverage

**Test counts (new this session):**
- 57 new unit tests (5 `feedback`, 17 `sync_gd`, 12 `rip`, 23 `scalr`)
- 5 new golden-value parity tests (`parity_optimizers.rs`)
- 1 new public-API regression test (`optimizers_are_nameable_and_usable_at_crate_root`)
- 3 new doctests (`sync_gd`, `rip`, `scalr` module-doc examples)

**Coverage (`cargo llvm-cov -p prin-train --summary-only`):**

| File | Regions | Lines | Functions |
|---|---|---|---|
| `feedback.rs` | 100.00% | 100.00% | 100.00% |
| `sync_gd.rs` | 98.34% | 99.70% | 100.00% |
| `rip.rs` | 97.91% | 100.00% | 100.00% |
| `scalr.rs` | 98.24% | 99.80% | 100.00% |
| `support.rs` (touched: `sgd_update`) | 100.00% | 100.00% | 100.00% |

All files ≥97.9% regions / ≥99.7% lines / 100% functions. Well above the ≥95% gate.

**No weakened/skipped tests.** All 150 unit tests + 14 integration tests + 9 doctests pass. `strict-checks` feature also clean.

### 3.4 A4 — Numerical parity + invariants

**5 golden-value parity tests** in `tests/parity_optimizers.rs`, all passing at `rtol=1e-9, atol=1e-12`:

1. `sync_gd_step_matches_prinet_3_0` — 2-step sequence with momentum + weight decay + dampening + a critical-order penalty transition (below then above threshold); checks parameter values, penalty history, order history.
2. `rip_step_matches_prinet_3_0` — combined gradient + Hebbian update on a 4×4 coupling matrix with non-trivial phase/amplitude inputs.
3. `scalr_step_basic_matches_prinet_3_0` — 3 steps with momentum, `warmup_steps=1`, varying order parameter; checks parameter values and lr history.
4. `scalr_oscillation_and_adaptive_r_min_matches_prinet_3_0` — 5 steps exercising oscillation-aware decay (`oscillation_window=4`) + adaptive `r_min` (`r_min_ema_alpha=0.3`); checks `lr_decay_factor`, `r_ema`, `r_min`, and final parameter.
5. `order_parameter_dict_resolution_matches_reference_formula` — pure-formula check of SCALR's Q3 dict-resolution mean/fallback.

**Methodology:** Tests call the **actual PRINet 3.0 classes** directly (via `wp024_generate_prinet_references.py`, gitignored), not formula retranscriptions. Multi-step sequences exercise state-carrying behavior (momentum buffers, histories, oscillation decay, adaptive `r_min`), not just stateless formulas. All 5 passed on first attempt after the initial Rust port — evidence the port faithfully reproduces the reference's exact arithmetic.

**Deterministic resume tests:** All three optimizers have `deterministic_resume_matches_uninterrupted_run` tests (step N uninterrupted vs. step k → snapshot → restore → step N−k, assert `<1e-12` final parameters and identical histories). `load_state_dict_revalidates` tests confirm corrupted states are rejected with typed errors.

### 3.5 A5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS (exit 0) |
| Clippy (workspace) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS (exit 0) |
| Clippy (strict-checks) | `cargo clippy -p prin-train --all-targets --features strict-checks -- -D warnings` | PASS (exit 0) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS (0 warnings) |
| ruff check | `.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| ruff format | `.venv\Scripts\ruff format --check ...` | PASS (50 files already formatted) |
| mypy | `.venv\Scripts\mypy python/prin --strict` | PASS (18 files, 0 issues) |
| Workspace tests | `cargo test --workspace` | PASS (all pass, 0 failures) |

### 3.6 A6 — Security

- **`#![forbid(unsafe_code)]`** at `prin-train` crate root; no `unsafe` in any new file.
- **bandit:** 0 issues identified across 3543 lines.
- **`cargo audit`:** exit 0; 2 allowed warnings, both unchanged from WP-023 close and amendment-governed:
  - `paste` RUSTSEC-2024-0436 (DV-008, amendment #9)
  - `bincode` RUSTSEC-2025-0141 (DV-017, amendment #27)
  - No new dependency added (`serde_json` was already a workspace dependency used in 5 other crates).
- **No secrets, no runtime codegen.**
- **Snyk Code:** Local scan BLOCKED — Snyk CLI unauthenticated on this machine (same standing condition documented in PSR-022/PSR-023). Reported as blocked per Coding Standards §6, not claimed as passed. CI `snyk` workflow is the authoritative gate.
- **Snyk Open Source:** N/A for Cargo (unsupported package manager); `cargo audit` is the authoritative ecosystem-native gate.

### 3.7 A7 — Docstring/doc coverage

- **interrogate:** 100.0% (106/106) — unchanged, no Python files touched.
- **Rust `missing_docs`:** Clean under `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` — 100% public-item rustdoc coverage across all crates.
- **Module-level documentation:** All four new modules (`feedback`, `sync_gd`, `rip`, `scalr`) have comprehensive module docs with update equations, PRINet 3.0 mapping, and usage examples.
- **Doctests:** 3 new doctest examples (one per optimizer module), all passing.
- **`lib.rs` crate doc:** Extended to list all four new modules with cross-references.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/HACK/XXX/STUB scan:** `grep` across `crates/prin-train/src/` returns zero matches.
- **`__all__`:** Not applicable — no Python files touched.
- **Ad-hoc reference script:** `DOCS/test_and_benchmark_results/wp024_generate_prinet_references.py` confirmed gitignored (matches the `DOCS/test_and_benchmark_results/` pattern in `.gitignore`).
- **`pub use` re-exports:** Consistent with WP022-F2/WP023-F1 precedent — every new public type (`SyncGd`, `SyncGdConfig`, `Rip`, `RipConfig`, `Scalr`, `ScalrConfig`, `OrderParameter`, `OscillatorOptimizer`, `StepFeedback`) re-exported at the crate root. `public_api.rs` regression test extended to cover all new re-exports.
- **No orphan files.** All new files are referenced from `lib.rs`, the handoff note, or the DV register.
- **`Cargo.toml`:** Only change is adding `serde_json.workspace = true` to `[dev-dependencies]` — already a workspace dependency, used in 5 other crates. No new external dependency introduced.

### 3.9 A9 — CI status

Per the Push and CI cadence (Plan amendment #28), nothing has been pushed yet this cycle. S2 verifies against local gate reproduction:

- All quality gates green locally (see §3.5).
- All tests pass locally (150 unit + 14 integration + 9 doctests for `prin-train`; full workspace clean).
- Coverage above threshold (see §3.3).
- Security gates clean at governed threshold (see §3.6).

CI will run on the S4 push carrying the full S1–S4 commit range.

### 3.10 A10 — Artefact trail

| Artefact | Status |
|---|---|
| `DOCS/audits/023-wp023-audit.md` | ✅ Present, verdict PASS-WITH-FINDINGS, 1 D4 finding closed in S3 |
| `DOCS/reports/023-project-state.md` | ✅ Present, WP-024 declared in §7, deviation ledger current |
| `DOCS/experiments/0093-wp024-s1-handoff.md` | ✅ Present, comprehensive acceptance-criteria → evidence map |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | ✅ DV-020 added, flagged for S2 review |
| Session briefs 0093–0096 | ✅ Present in `DOCS/sessions/phase-4/` |

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP024-F1 | D3 | `DOCS/reports/023-project-state.md` §7 | PSR-023 §7 WP-024 declaration names `PhaseAdam`/`KuramotoOptimizer` and `phase_adam.rs`/`kuramoto_optimizer.rs`; none exist in the PRINet 3.0 reference (`grep -rl` returns zero matches). The session brief and Rebuild Planning Document correctly name SCALR/RIP/SyncGD. S1 followed the evidence-backed naming. The declaration text does not match the delivered (correct) scope. | Plan §6 (WP declaration accuracy); Development Workflow §2 (WP declaration defines scope) | PSR-024 at S4 naturally supersedes PSR-023 §7's WP-024 declaration with the correct scope description (delivered `sync_gd.rs`/`rip.rs`/`scalr.rs`/`feedback.rs`, not `phase_adam.rs`/`kuramoto_optimizer.rs`). If the maintainer prefers an explicit plan amendment correcting PSR-023 §7 before S4, that path is also available. DV-020 already tracks this item. |

## 5. Deviation-ledger delta

**New findings added to the ledger:** WP024-F1 (D3, PSR-023 §7 naming discrepancy — already tracked as DV-020).

**Carried findings re-inspected:**
- DV-019 (WP-022 `bands::tests::gradients_flow_to_every_parameter` flake): S1 handoff note reports one isolated recurrence during `cargo llvm-cov -p prin-train`, immediate re-run clean. Same pre-existing WP-022 flakiness class; not a WP-024 regression. Status unchanged (OPEN).
- DV-020 (WP-024 naming discrepancy): confirmed at S2 as WP024-F1 (D3).

**No D1/D2 findings. No findings carried from prior cycle remain open.**

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

One D3 finding (WP024-F1): PSR-023 §7's WP-024 declaration named classes that do not exist in the PRINet 3.0 reference. S1 correctly followed the session brief and the verifiable reference, delivering SCALR/RIP/SyncGD. The discrepancy is a governance-artifact drafting inconsistency, not a code defect.

**Rationale:** The implementation is technically excellent — faithful PRINet 3.0 ports with golden-value parity at `rtol=1e-9`, comprehensive test coverage (97.9–100% on all new files), clean quality gates, proper state serialization with re-validation, and thorough documentation. The single finding is a plan-text discrepancy that S4 will naturally resolve.

**Ordered S3 work list:**

1. **WP024-F1 (D3):** Update PSR-024 at S4 to correctly describe the WP-024 scope as delivered (`sync_gd.rs`/`rip.rs`/`scalr.rs`/`feedback.rs`), superseding PSR-023 §7's incorrect `phase_adam.rs`/`kuramoto_optimizer.rs` declaration. Alternatively, if the maintainer prefers, submit a plan amendment correcting PSR-023 §7 before S4.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(to be filled by S3)* | | | |

**Delta re-audit date:** YYYY-MM-DD — **Result:** CLEAN / findings remain

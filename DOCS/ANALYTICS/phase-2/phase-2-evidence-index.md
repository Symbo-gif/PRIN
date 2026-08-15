# Phase 2 Evidence Index

**Phase:** 2 — Advanced numerics and simulation
**Date:** 2026-08-15
**Companion to:** [`phase-2-analytics-report.md`](phase-2-analytics-report.md)

This index lists every evidence artefact cited in the Phase 2 Analytics
Report, with file path, purpose, and the dimension(s) it supports.

---

## 1. Governance documents

| Path | Purpose | Dimensions |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | Official project plan; Phase 2 scope, exit criteria, amendment log §8.3 (amendments #18–#25) | P6, P8, P9 |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | Session Cycle methodology, audit checklist, deviation classification | P6 |
| `DOCS/standards/Coding_Standards.md` | Rust + Python coding standards, security controls §6 | P4, P7 |
| `DOCS/standards/Testing_Standards.md` | Testing layers, tolerances, coverage gates, parity-before-landing rule §1.3 | P1, P3 |
| `DOCS/standards/Documentation_Standards.md` | Documentation thresholds; S4 checklist §7, item 8 (R7's documentation-accuracy sweep) | P2 |
| `DOCS/standards/Benchmarking_and_Reproducibility_Standards.md` | Performance targets §2.4 (amended by #21) | P1, P8 |
| `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` | Executive audit criteria E1–E10, deviation severities | P6 |
| `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md` | EMA session type, claim taxonomy, policy engine (introduced by amendment #23) | P5, P6 |
| `DOCS/ANALYTICS/phase-1/phase-1-recommendations.md` | Phase 1 recommendations R7–R13 tracked to closure in §9.1 | P1, P2, P3, P9 |
| `DOCS/ANALYTICS/phase-1/phase-1-recommendation-implementation-governance.md` | Inter-phase session that implemented R7/R8/R9/R12 before WP-012 S1 | P1, P2, P3, P9 |

## 2. Audit reports (Phase 2)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/012-wp012-audit.md` | FAIL → CLEAN | 5 (3 D1, 1 D3, 1 D4) | P1, P4, P8 |
| `DOCS/audits/013-wp013-audit.md` | FAIL → CLEAN | 6 (1 D1, 1 D2, 1 D3, 3 D4) | P1, P4 |
| `DOCS/audits/014-wp014-audit.md` | FAIL → CLEAN | 7 (1 D1, 3 D2, 2 D3, 1 D4) | P1, P2, P3, P4, P6 |
| `DOCS/audits/015-wp015-audit.md` | FAIL → CLEAN | 6 (1 D1, 2 D2, 3 D3) | P3, P4, P6 |
| `DOCS/audits/016-wp016-audit.md` | FAIL → CLEAN | 7 (1 D1, 3 D2, 3 D3) | P1, P4, P8 |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_003.md` | PASS-WITH-REMEDIATION | 14 (E-F1–E-F14: 2 D1, 5 D2, 3 D3, 4 D4) | P1, P2, P5, P6, P7, P9 |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_001.md` | FAIL → PASS-WITH-REMEDIATION (§7–§9 addendum) | 6 (M-F1–M-F6: 1 D1, 1 D2, 2 D3, 2 D4) | P1, P5, P6, P9 |

## 3. Audit reports (Phase 1, retained for trend comparison)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/006-wp006-audit.md` – `DOCS/audits/011-wp011-audit.md` | PASS/PASS-WITH-FINDINGS | 22 total (0 D1) | §11 comparison |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md`, `EXECUTIVE_AUDIT_REPORT_002.md` | PASS-WITH-REMEDIATION | 18 total | §11 comparison |

## 4. Project state reports (Phase 2)

| Path | Cycle | Key content | Dimensions |
|---|---|---|---|
| `DOCS/reports/012-project-state.md` | 012 | WP-012 closure, WP-013 declaration | P6 |
| `DOCS/reports/013-project-state.md` | 013 | WP-013 closure; last verified pre-corruption deviation-ledger table (used by EA-003 E-F1 to restore 014–016) | P6 |
| `DOCS/reports/014-project-state.md` | 014 | WP-014 closure; corrupted ledger table (EA-003 E-F1), correction note added | P6 |
| `DOCS/reports/015-project-state.md` | 015 | WP-015 closure; corrupted ledger table carried, correction pointer added | P6 |
| `DOCS/reports/016-project-state.md` | 016 | WP-016 closure; restored ledger table (E-F1 fix); **Phase 2 exit-gate verdict GREEN** §5; risks §6 cross-referenced by EMA-001 | P6, P8, P9 |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | — | 10 active deferred items (DV-001–DV-010); Phase 1 recommendation deferrals | P9 |

## 5. Session briefs and register (Phase 2)

| Path | Scope | Dimensions |
|---|---|---|
| `DOCS/sessions/phase-2/README.md` | Phase 2 session status table — all 20 (0045–0064) COMPLETE | P6 |
| `DOCS/sessions/phase-2/0045-0064-*.md` | 20 individual session briefs | P6 |
| `DOCS/sessions/SESSION_REGISTER.md` | Master register — sessions 0045–0064 plus Global Sessions section (EA-003, EMA-001, EMA-001R) | P6 |
| `DOCS/sessions/TRACEABILITY.md` | Requirement/risk/DoD traceability matrix; N1 performance row, WP-016 §2 row | P6, P8 |
| `DOCS/experiments/0049-wp013-s1-handoff.md` | WP-013 S1 handoff (added in S3 remediation, WP013-F3) | P1, P2 |
| `DOCS/experiments/0053-wp014-s1-handoff.md` | WP-014 S1 handoff (contains the refuted "no reference found" claim, WP014-F1) | P1, P2 |
| `DOCS/experiments/0057-wp015-s1-handoff.md` | WP-015 S1 handoff | P3, P6 |
| `DOCS/experiments/0061-wp016-s1-handoff.md` | WP-016 S1 handoff | P4, P8 |

## 6. Evidence files — math-audit chain (EMA-001)

| Path | Content | Dimensions |
|---|---|---|
| `EVIDENCE/math-audit/ema-run-summary.json` | Consolidated 23-claim run summary, both original and remediation policy snapshots | P5, P9 |
| `EVIDENCE/math-audit/audits/bundle-83cd0a683ec1/` | z3-invariants delta re-audit bundle (PW-02 fix verification) | P5 |
| `EVIDENCE/math-audit/audits/bundle-861cee2f1497/` | graph-topology bundle (`GRA-01-LEAN` PASS) | P5 |
| `EVIDENCE/math-audit/audits/bundle-492de710aafb/` | tensor-contracts bundle (`TEN-01-LEAN` PASS) | P5 |
| `EVIDENCE/math-audit/manual/ema-001-remediation-wolfram-ode-corroboration.{wls,txt}` | Independent Wolfram Engine corroboration for `INT-01/02`, `HOPF-01`, `KUR-01` (M-F3 resolution) | P5, P9 |
| `tools/math_audit_claims/prin-dynamics-{z3-invariants,symbolic-identities,ode-properties,tensor-contracts,graph-topology}.json` | Committed, versioned claim ledgers (23 claims + 2 Lean additions) | P5 |
| `tools/math_audit_policy.yaml` | EMA policy (`prin-ema`, strict-derived); `enable_lean: true` per amendment #24 | P5, P6 |
| `tools/math_audit_run.py` | Gate script invoking `audit_claim_ledger`; **fails `ruff check`/`ruff format --check` — PA2-F1** | P2, P5 |

## 7. Rust crates (Phase 2 new/changed code)

### `prin-dynamics` (extended)

| Path | Purpose | Dimensions |
|---|---|---|
| `crates/prin-dynamics/src/integrate.rs` | `ExponentialIntegrator` (Padé(13)/Krylov), `MultiRateIntegrator`; WP012-F3 (`matrix_exp` typed-error fix) | P1, P4 |
| `crates/prin-dynamics/src/bands.rs` | `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`; WP013-F2 coupling-mode dispatch | P1, P4 |
| `crates/prin-dynamics/src/temporal.rs` | `ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator` | P1, P4 |
| `crates/prin-dynamics/tests/parity_integrators.rs` | +7 parity cases (Exponential ×4, MultiRate ×3) | P1, P3 |
| `crates/prin-dynamics/tests/parity_bands.rs` | 12 parity cases vs. `prinet==3.0.0` | P1, P3 |
| `crates/prin-dynamics/tests/parity_temporal.rs` | 6 parity cases | P1, P3 |

### `prin-tensor` (new crate)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-tensor/src/lib.rs` | ~40 | Crate root, `#![forbid(unsafe_code)]`, module docs | P4, P7 |
| `crates/prin-tensor/src/error.rs` | ~90 | `TensorError` (10+ variants incl. `InvalidRank`, `InvalidMode`, `InvalidMaxIter`) | P4, P7 |
| `crates/prin-tensor/src/utils.rs` | ~330 | Mode unfolding, mode-n product, Frobenius norm, `flat_to_multi` (de-duplicated) | P4 |
| `crates/prin-tensor/src/tucker.rs` | ~450 | `PolyadicTensor`, `hosvd` (fixed rank-bound validation, WP014-F3) | P1, P4 |
| `crates/prin-tensor/src/cp.rs` | ~700 | `CPDecomposition`, `cp_als` (error-based convergence, all-factor normalization, WP014-F5) | P1, P4 |
| `crates/prin-tensor/tests/parity_decomposition.rs` | ~340 | 9 invariant/normalization/reproducibility tests + `parity_hosvd_matches_prinet_reference_reconstruction` (EA-003 E-F5) | P1, P3 |
| `crates/prin-tensor/tests/data/prinet_reference_hosvd.json` | — | Genuine PRINet 3.0 HOSVD reference output (EA-003 E-F5) | P1 |

### `prin-sim` (new crate)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-sim/src/lib.rs` | ~60 | Crate root, `#![forbid(unsafe_code)]` | P4, P7 |
| `crates/prin-sim/src/error.rs` | ~85 | `SimError` (10 variants) | P4, P7 |
| `crates/prin-sim/src/csr_coupling.rs` | ~930 | `SparseCoupling` CSR matrix, sin/cos-decomposition SpMV | P1, P4 |
| `crates/prin-sim/src/engine.rs` | ~900 | `SparseKuramoto`, `SparseStuartLandau`, `OscilloSim`, `Trajectory` | P1, P4 |
| `crates/prin-sim/src/pruning.rs` | ~415 | `PruningStrategy`, `PruningResult` | P4 |
| `crates/prin-sim/src/chimera.rs` | ~290 | `ChimeraMetrics`, trajectory variant | P1, P4 |
| `crates/prin-sim/src/sweep.rs` | — | `run_sweep`, `SweepConfig`/`Result`/`Axis`/`Model`, `detect_oscillation` | P1, P4 |
| `crates/prin-sim/src/dispatch.rs` | — | Size-gated sequential/rayon dispatcher (WP016-F1/F2 fix) | P4 |
| `crates/prin-sim/tests/parity_sparse_vs_dense.rs` | ~520 | 21 sparse-vs-dense parity/determinism/memory tests | P1, P3 |
| `crates/prin-sim/tests/proptest_properties.rs` | — | 4 property tests (WP015-F6) | P3 |
| `crates/prin-sim/tests/proptest_sweep.rs` | — | 5 sweep-invariant property tests | P3 |
| `crates/prin-sim/tests/parity_detect_oscillation.rs` | — | 7 parity cases (384 combinations, WP-016) | P1, P3 |
| `crates/prin-sim/benches/sweep_bench.rs` | — | Criterion suite with in-process serial baselines (verified genuine by EA-003 E8) | P8 |

## 8. Metrics correctness (EMA-001 M-F1)

| Path | Content | Dimensions |
|---|---|---|
| `crates/prin-metrics/src/chimera.rs` | `strength_of_incoherence`, `centred_wrap` helper (fixed: `(diff + PI).rem_euclid(TAU) - PI`) | P1, P5 |
| `crates/prin-metrics/tests/parity_chimera.rs` | Regression tests `centred_wrap_maps_zero_to_zero`, `strength_of_incoherence_local_coherence_not_inverted`; test-local reimplementation of PRINet's buggy formula (documents the amendment #25 exception) | P1, P3, P5 |

## 9. Security artefacts

| Path | Content | Dimensions |
|---|---|---|
| `.snyk` | 6 `torch@2.13.0` ignore entries with investigation evidence, maintainer approval, 2026-11-14 recheck (EA-003 E-F7) | P7 |
| `python/prin/__init__.py` | `__version__` (fixed to `0.3.0-alpha.1`, EA-003 E-F3) | P5, P7 |
| `tools/wp001_baseline.py` | Version-consistency check; independently re-run this session, passed | P5 |

## 10. CI workflows

| Path | Purpose | Phase 2 changes | Dimensions |
|---|---|---|---|
| `.github/workflows/rust.yml` | Rust quality (3 OS + strict-checks) | Added `bench-smoke` job (EA-003 E-F9) | P5, P8 |
| `.github/workflows/parity.yml` | Differential testing | Parameterized for 504-case exhaustive CI with `pytest-xdist` (R8) | P1, P5 |
| `.github/workflows/python.yml`, `snyk.yml`, `repro.yml`, `release.yml`, `gpu.yml` | Unchanged structurally | Re-run live on previously-billing-blocked commits (EA-003 E-F2/E-F4) | P5 |

## 11. Independent re-verification (this session, 2026-08-15)

| Command | Result | Dimensions |
|---|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | **3 errors** — `tools/math_audit_run.py` (PA2-F1) | P2, P5 |
| `ruff format --check` | **1 file** would be reformatted — `tools/math_audit_run.py` (PA2-F1) | P2, P5 |
| `mypy python/prin --strict` | Success: no issues in 18 files | P4 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (106/106) | P2 |
| `bandit -r . -c pyproject.toml` | 0 issues | P7 |
| `pytest tests/ -m "not slow and not gpu" --cov=prin` | 306 passed, 6 deselected, 99% coverage | P3 |
| `pytest parity/ -m parity` | 510 passed | P1, P3 |
| `cargo fmt --all -- --check` | Clean | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | P4 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | Clean | P4 |
| `cargo test --workspace` | 731 passed, 0 failed | P3, P4 |
| `cargo test --workspace --features strict-checks` | 734 passed, 0 failed | P3, P4 |
| `cargo audit` | 0 vulnerabilities; 1 allowed advisory | P7 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings | P2 |
| `sphinx-build -W --keep-going -b html` | Build succeeded, 0 warnings | P2 |
| `tools/wp001_baseline.py check` | Passed | P5 |

## 12. Git history

| Range | Commits | Content |
|---|---|---|
| `d02e478..dac017e` | ~48 | WP-012 through WP-016 (S1–S3 baselines) |
| `dac017e..fbe1c92` | ~4 | WP-016 S4 documentation + `v0.3.0-alpha.1` Phase 2 exit release |
| `fbe1c92..f1204ed` | 3 | EA-003 (`6777ef1`, `c228264`, `f1204ed`) |
| `f1204ed..630c5d6` | 1 | EMA-001 governance + audit + report |
| `630c5d6..4d0f75b` | 1 | EMA-001R remediation (current `HEAD`) |

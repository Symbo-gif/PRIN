# Phase 3 Evidence Index

**Phase:** 3 — GPU kernels
**Date:** 2026-08-18
**Companion to:** [`phase-3-analytics-report.md`](phase-3-analytics-report.md)

This index lists every evidence artefact cited in the Phase 3 Analytics
Report, with file path, purpose, and the dimension(s) it supports.

---

## 1. Governance documents

| Path | Purpose | Dimensions |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | Official project plan; Phase 3 scope (§6), amendment log §8.3 (unchanged at #25 — PA3-F2) | P2, P6, P8, P9 |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | Session Cycle methodology, audit checklist, deviation classification; §3 S4 action 6 (new, EA-004 durable fix) | P6 |
| `DOCS/standards/Coding_Standards.md` §2.1/§6.1 | `unsafe`/kernel-FFI policy (amendment #8's governed exception) | P4, P7 |
| `DOCS/standards/Coding_Standards.md` §6.2 | Security scanning mandate (`cargo audit`, Snyk Code/OSS, `pip-audit`, `bandit`) | P5, P7 |
| `DOCS/standards/Testing_Standards.md` §2/§3 | Kernel-equivalence testing layer, GPU-vs-CPU tolerance (`rtol=1e-5, atol=1e-6`) | P1, P3 |
| `DOCS/standards/Documentation_Standards.md` §7 | S4 documentation checklist, item 8 (R7's sweep) | P2 |
| `DOCS/standards/Benchmarking_and_Reproducibility_Standards.md` §2.4 | GPU/CPU performance targets table | P1, P8 |
| `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` §5 | EA closing checklist (R16 fix) | P6 |
| `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md` §8 | EMA closing checklist (R16 fix) | P5, P6 |
| `DOCS/ANALYTICS/phase-2/phase-2-recommendations.md` | Phase 2 recommendations R14–R20 tracked to closure in §9.1 | P1, P2, P5, P6, P9 |

## 2. Audit reports (Phase 3)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/017-wp017-audit.md` | FAIL → CLEAN | 5 (1 D1, 3 D2, 1 D4) | P1, P4, P7 |
| `DOCS/audits/018-wp018-audit.md` | PASS | 0 | P1, P3 |
| `DOCS/audits/019-wp019-audit.md` | PASS-WITH-FINDINGS → CLEAN | 1 (D4) | P1, P2 |
| `DOCS/audits/020-wp020-audit.md` | PASS → CLEAN | 1 (D4, self-discovered) | P1, P6 |
| `DOCS/audits/021-wp021-audit.md` | PASS-WITH-FINDINGS → CLEAN | 1 (D4) | P4, P6, P8 |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_004.md` | PASS-WITH-REMEDIATION | 2 (E-F1, E-F2: both D1) | P1, P3, P5, P6, P8, P9 |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_002.md` | PASS-WITH-REMEDIATION | 0 new (M-F7 carried forward, D3, by design) | P1, P5, P9 |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_PREPARATION_002.md` | — | EMA-002 pre-audit preparation (claim ledger authoring) | P5 |

## 3. Audit reports (Phase 2, retained for trend comparison)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/012-wp012-audit.md` – `DOCS/audits/016-wp016-audit.md` | FAIL → CLEAN (all 5) | 31 total (7 D1) | §11 comparison |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_003.md`, `EXECUTIVE_MATH_AUDIT_REPORT_001.md` | PASS-WITH-REMEDIATION | 20 total | §11 comparison |

## 4. Project state reports (Phase 3)

| Path | Cycle | Key content | Dimensions |
|---|---|---|---|
| `DOCS/reports/017-project-state.md` | 017 | WP-017 closure (FAIL → CLEAN); `tools/check_deviation_ledger.py` built and first run (closing Phase 2's R17) | P5, P6 |
| `DOCS/reports/018-project-state.md` | 018 | WP-018 closure (zero findings); `check_deviation_ledger.py` run again | P3, P5 |
| `DOCS/reports/019-project-state.md` | 019 | WP-019 closure; last PSR authored before the ledger corruption (used by EA-004 to restore 020/021) | P2, P6 |
| `DOCS/reports/020-project-state.md` | 020 | WP-020 closure; corrupted ledger table introduced here (EA-004 E-F2); correction pointer note added post-EA-004 | P6 |
| `DOCS/reports/021-project-state.md` | 021 | WP-021 closure; restored ledger table (E-F2 fix, `[RETROACTIVE UPDATE - Executive Audit 004]` tags); **Phase 3 exit-gate verdict GREEN** §5; WP-022 declaration §8 | P1, P3, P6, P8, P9 |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | — | 16 active/closed deferred items (DV-001–DV-016); Phase 2 recommendation deferrals (R18–R20) | P9 |

## 5. Session briefs and register (Phase 3)

| Path | Scope | Dimensions |
|---|---|---|
| `DOCS/sessions/phase-3/README.md` | Phase 3 session status table — all 20 (0065–0084) COMPLETE | P6 |
| `DOCS/sessions/phase-3/0065-0084-*.md` | 20 individual session briefs | P6 |
| `DOCS/sessions/SESSION_REGISTER.md` | Master register — sessions 0065–0084 plus Global Sessions section (EA-004, EMA-002); session 0081 status-mismatch fix (WP021-F1) confirmed durable | P6 |
| `DOCS/experiments/0065-wp017-s1-handoff.md` | WP-017 S1 handoff | P1, P4 |
| `DOCS/experiments/0069-wp018-s1-handoff.md` | WP-018 S1 handoff | P1, P3 |
| `DOCS/experiments/0073-wp019-s1-handoff.md` | WP-019 S1 handoff (contains the WP019-F1 corrected coverage cell) | P1, P2 |
| `DOCS/experiments/0077-wp020-s1-handoff.md` | WP-020 S1 handoff | P1, P4 |
| `DOCS/experiments/0081-wp021-s1-handoff.md` | WP-021 S1 handoff — **not indexed in `DOCS/experiments/README.md` (PA3-F1)** | P2, P8 |

## 6. Evidence files — math-audit chain (EMA-002)

| Path | Content | Dimensions |
|---|---|---|
| `EVIDENCE/math-audit/ema-run-summary.json` | Consolidated 28-claim run summary (6 ledgers); dated 2026-08-18, matching current `HEAD` | P5, P9 |
| `EVIDENCE/math-audit/audits/bundle-46c95f84bb4e/` | `prin-kernels-gpu-properties.json` bundle — GPU-RK4-01/GPU-RED-01/GPU-KNN-01, all SymPy PASS (first EMA coverage of `prin-kernels`) | P1, P5 |
| `tools/math_audit_claims/prin-kernels-gpu-properties.json` | New claim ledger (3 claims), committed and versioned | P5 |
| `tools/math_audit_claims/prin-dynamics-{symbolic-identities,z3-invariants,ode-properties,tensor-contracts,graph-topology}.json` | 25 claims carried from EMA-001R, re-verified with zero regressions | P5 |
| `tools/math_audit_policy.yaml` | EMA policy (`prin-ema`); policy snapshot hash unchanged from EMA-001R | P5, P6 |
| `tools/math_audit_run.py` | Gate script; `ruff check`/`format --check`/`mypy --strict` all clean this session (per EMA-002 §7, confirming Phase 2's PA2-F1 fix held) | P2, P5 |

## 7. Rust crates (Phase 3 new/changed code)

### `prin-kernels` (extended)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-kernels/src/backend.rs` | 149 | `backend_priority`/`auto_detect_order`; WP-017 new | P4 |
| `crates/prin-kernels/src/buffers.rs` | 357 | `CubeclBufferPool`/`MeanFieldRk4Buffers`; `capacity()` accessor (WP017-F1 fix) | P4, P7 |
| `crates/prin-kernels/src/equivalence.rs` | 444 | `EquivalenceHarness`; mismatch-detection coverage (WP017-F2 fix) | P1, P3 |
| `crates/prin-kernels/src/mean_field_rk4.rs` | 728 | Authoritative CPU reference (`step_cpu`) | P1, P4 |
| `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | 1,226 | Fused CubeCL kernel; hierarchical block-reduce, device-event timing (WP-018); 1 `unsafe` block (`array_arg`) | P1, P4, P7 |
| `crates/prin-kernels/src/sparse_knn.rs` | 832 | `SparseKnnGraph`, CPU gather reference; new (WP-019) | P1, P4 |
| `crates/prin-kernels/src/sparse_knn/cubecl.rs` | 645 | Fused CubeCL sparse-gather kernel; new (WP-019); 2 `unsafe` blocks | P1, P4, P7 |
| `crates/prin-kernels/src/pac.rs` | 454 | `PacParams`, `pac_modulate_cpu`; new (WP-019) | P1, P4 |
| `crates/prin-kernels/src/pac/cubecl.rs` | 448 | Fused CubeCL PAC reduce+broadcast kernel; new (WP-019); 1 `unsafe` block | P1, P4, P7 |
| `crates/prin-kernels/src/discrete_step.rs` | 923 | `discrete_step_cpu` — fused 3-band stepper; new (WP-020) | P1, P4 |
| `crates/prin-kernels/src/discrete_step/cubecl.rs` | 1,034 | Fused CubeCL 10-launch discrete-step kernel; new (WP-020); 1 `unsafe` block | P1, P4, P7 |
| `crates/prin-kernels/src/ops.rs` | 42 | Shared kernel arithmetic helpers | P4 |
| `crates/prin-kernels/src/lib.rs` | 55 | Crate root; `#![deny(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]` (governed exception, amendment #8) | P4, P7 |

**Total: 7,337 lines, 5 `unsafe` blocks (all `ArrayArg::from_raw_parts`, all `// SAFETY:`-commented, all in `*_cubecl.rs` files).**

### `prin-sim` (extended)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-sim/src/gpu.rs` | 968 | **New (WP-021).** `GpuSparseKuramoto`, `GpuMeanFieldEngine`, `GpuBandStepper`; 99.67% line coverage | P1, P4 |
| `crates/prin-sim/src/error.rs` | 100 | `SimError::{MeanFieldKernel,DiscreteStepKernel,SparseKnnKernel,InvalidCoupling}` (WP-021 additions) | P4, P7 |
| `crates/prin-sim/src/lib.rs` | 86 | Crate root; `#![forbid(unsafe_code)]`, unchanged | P4, P7 |
| `crates/prin-sim/src/{csr_coupling,engine,pruning,chimera,sweep,dispatch}.rs` | 3,309 (combined) | Pre-existing (Phase 2 WP-015/WP-016), unchanged this phase | — |

## 8. Security artefacts

| Path | Content | Dimensions |
|---|---|---|
| `.snyk` | 6 `torch@2.13.0` ignore entries (DV-011), reproduced identically by EA-004, unchanged | P7 |
| `tools/wp001_baseline.py` | Version-consistency check; independently re-run this session, passed | P5 |
| `tools/check_deviation_ledger.py` | Ledger consistency check; independently re-run this session against PSR-021 — 94 rows validated clean; now CI-enforced (EA-004 durable fix) | P5, P6 |

## 9. CI workflows

| Path | Purpose | Phase 3 changes | Dimensions |
|---|---|---|---|
| `.github/workflows/rust.yml` | Rust quality (3 OS + strict-checks) | Added `cargo test -p prin-sim --features cpu -- --test-threads=1` (WP-021); `timeout-minutes: 120` added to `test` job (EA-004, DV-016 safety net) | P3, P5, P8 |
| `.github/workflows/python.yml` | Python quality | `lint` job gained a "Deviation-ledger consistency" step running `tools/check_deviation_ledger.py` on every push/PR (EA-004, closing DV-015); `fetch-depth: 0` added to `lint`'s checkout step (EA-004 addendum fix) | P5, P6 |
| `.github/workflows/gpu.yml` | Headless GPU CI (opt-in) | Unchanged; still gated on a self-hosted GPU runner that does not exist (DV-002) | P1, P8 |
| `.github/workflows/parity.yml`, `snyk.yml`, `repro.yml`, `release.yml` | Unchanged structurally | Re-run live post-DV-014 resolution (EA-004 addendum) | P5 |

## 10. Independent re-verification (this session, 2026-08-18)

All commands run on the identical RTX 4060 hardware (driver 595.95, CUDA
13.2) that produced the original WP-021/EA-004 evidence.

| Command | Result | Dimensions |
|---|---|---|
| `cargo fmt --all -- --check` | Clean | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | P4 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | Clean | P4 |
| `cargo clippy -p prin-sim --all-targets --features cpu,cuda,wgpu -- -D warnings` | Clean | P4 |
| `cargo clippy -p prin-kernels --all-targets --features cuda,wgpu -- -D warnings` | Clean | P4 |
| `cargo test --workspace` | 821 passed, 0 failed, 28 doctests | P3, P4 |
| `cargo test -p prin-kernels --features cuda` | 113 passed, 0 failed (hardware CUDA) | P1, P3, P8 |
| `cargo test -p prin-kernels --features cpu` | 121 passed, 0 failed | P1, P3 |
| `cargo test -p prin-sim --features cuda -- --test-threads=1` | 153 passed (hardware CUDA) | P1, P3, P8 |
| `cargo test -p prin-sim --features cpu -- --test-threads=1` | 153 passed | P1, P3 |
| `cargo audit` | 1 allowed advisory, 0 new | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings | P2 |
| `ruff check` / `ruff format --check` (python/tests/benchmarks/tools/parity) | Clean / 50 files formatted | P2, P5 |
| `mypy python/prin --strict` | Success, 18 files, 0 issues | P4 |
| `bandit -r . -c pyproject.toml` | 0 issues | P7 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (106/106) | P2 |
| `pytest tests/ -m "not slow and not gpu"` | 306 passed, 6 deselected | P3 |
| `pytest parity/ -m parity` | 510 passed | P1, P3 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | P7 |
| `sphinx-build -W --keep-going -b html` | Build succeeded, 0 warnings | P2 |
| `tools/wp001_baseline.py check` | Passed | P5 |
| `tools/check_deviation_ledger.py DOCS/reports/021-project-state.md` | Passed, 94 rows validated | P5, P6 |
| `ToolSearch` for Snyk MCP | No match — confirmed unavailable | P5, P7 |
| `nvidia-smi` | RTX 4060, driver 595.95, CUDA 13.2 — confirms identical hardware to WP-021/EA-004 | P1, P3 |

## 11. This session's own findings

| ID | Severity | Location | Dimensions |
|---|---|---|---|
| PA3-F1 | D4 | `DOCS/experiments/README.md` (index staleness — missing `0081-wp021-s1-handoff.md`) | P2 |
| PA3-F2 | D3 | `DOCS/PRIN_Project_Plan.md` §6 (Phase 3 roadmap-table completion marker missing) | P2, P6 |

## 12. Git history

| Range | Commits | Content |
|---|---|---|
| `4d0f75b..4e507bc` | ~5 | Inter-phase Phase 2 recommendation implementation (R14–R17, R19–R20 groundwork) |
| `4e507bc..933f8a3` | ~24 | WP-017 through WP-021 (S1–S4), Phase 3 exit release |
| `933f8a3..36e8d0d` | 1 | EA-004 audit report |
| `36e8d0d..1bce918` | 1 | EA-004 fetch-depth CI fix |
| `1bce918..1604bd6` | 1 | EA-004 DV-014 close / DV-016 safety net |
| `1604bd6..c6407f7` | 1 | EMA-002 (current `HEAD`) |

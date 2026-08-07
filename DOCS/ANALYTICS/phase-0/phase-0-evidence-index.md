# Phase 0 Evidence Index

**Phase:** 0 — Foundation
**Date:** 2026-08-07
**Companion to:** [`phase-0-analytics-report.md`](phase-0-analytics-report.md)

This index lists every evidence artefact cited in the Phase 0 Analytics
Report, with file path, purpose, and the dimension(s) it supports.

---

## 1. Governance documents

| Path | Purpose | Dimensions |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | Official project plan; phase scope, exit criteria, amendment log (§8.3) | P6, P8, P9 |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | Session Cycle methodology, audit checklist, deviation classification | P6 |
| `DOCS/standards/Coding_Standards.md` | Rust + Python coding standards, security standards (§6) | P4, P7 |
| `DOCS/standards/Testing_Standards.md` | Testing layers, tolerances, coverage gates | P3 |
| `DOCS/standards/Documentation_Standards.md` | Documentation thresholds, S4 checklist | P2 |
| `DOCS/standards/Benchmarking_and_Reproducibility_Standards.md` | Reproducibility and benchmarking requirements | P1 |
| `DOCS/standards/Experimentation_Standards.md` | Pre-registration, campaign rules, scientific integrity | P6 |
| `DOCS/standards/Versioning_and_Release_Standards.md` | Versioning, CI/CD gates, release procedure | P5, P8 |

## 2. Audit reports

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/001-wp001-audit.md` | FAIL → PASS (S3) | 11 (4 D1, 6 D2, 1 D4) | P5, P6, P7 |
| `DOCS/audits/002-wp002-audit.md` | PASS-WITH-FINDINGS → clean | 4 (2 D2, 2 D4) | P1, P5, P6 |
| `DOCS/audits/003-wp003-audit.md` | PASS-WITH-FINDINGS → clean | 5 (2 D2, 1 D3, 2 D4) | P4, P5, P7 |
| `DOCS/audits/004-wp004-audit.md` | PASS-WITH-FINDINGS → clean | 9 (4 D2, 4 D3, 1 D4) | P3, P4, P5, P7 |
| `DOCS/audits/005-wp005-audit.md` | PASS-WITH-FINDINGS → clean | 4 (2 D3, 2 D4) | P5, P8 |
| `DOCS/audits/TEMPLATE_Audit_Report.md` | — | — | P6 |
| `DOCS/audits/README.md` | — | — | P6 |

## 3. Project state reports

| Path | Cycle | Key content | Dimensions |
|---|---|---|---|
| `DOCS/reports/001-project-state.md` | 001 | WP-001 closure, WP-002 declaration | P6 |
| `DOCS/reports/002-project-state.md` | 002 | WP-002 closure, WP-003 declaration | P6 |
| `DOCS/reports/003-project-state.md` | 003 | WP-003 closure, WP-004 declaration | P6 |
| `DOCS/reports/004-project-state.md` | 004 | WP-004 closure, WP-005 declaration | P6 |
| `DOCS/reports/005-project-state.md` | 005 | WP-005 closure, Phase 0 exit gate GREEN, WP-006 declaration | P6, P8, P9 |

## 4. Session briefs

| Path | Scope | Dimensions |
|---|---|---|
| `DOCS/sessions/phase-0/README.md` | Phase 0 session status table (all 20 COMPLETE) | P6 |
| `DOCS/sessions/phase-0/0001-0020-*.md` | 20 individual session briefs | P6 |
| `DOCS/sessions/SESSION_REGISTER.md` | Master register (198 sessions) | P6 |
| `DOCS/sessions/TRACEABILITY.md` | Requirement/risk/DoD traceability matrix | P6 |

## 5. Evidence files

| Path | Content | Dimensions |
|---|---|---|
| `EVIDENCE/0005-wp002-s1-handoff.md` | WP-002 S1 handoff to S2 | P1, P5 |
| `EVIDENCE/0017-wp005-s1-ort-probe.json` | ORT probe: selected=directml, active=CPU, can_run=true, shape=(1,8) | P1, P8 |
| `EVIDENCE/0017-wp005-s1-phase0-gate.json` | Phase 0 gate: ready=true, all 4 checks ok | P8 |

## 6. Baselines

| Path | Content | Dimensions |
|---|---|---|
| `DOCS/baselines/wp001_baseline_report.md` | Repository inventory, API traceability, quality/security baseline | P4, P5, P6 |
| `DOCS/baselines/wp001_api_traceability.md` | 657-symbol traceability matrix | P6 |
| `DOCS/baselines/wp001_repository_inventory.json` | Repository state inventory | P6 |
| `DOCS/baselines/wp001_s1_handoff.md` | WP-001 S1 handoff | P5 |

## 7. Experiment handoffs

| Path | Content | Dimensions |
|---|---|---|
| `DOCS/experiments/0013-wp004-s1-handoff.md` | WP-004 S1 handoff (CubeCL spike) | P4, P5 |
| `DOCS/experiments/0013-wp004-s1-coverage.md` | WP-004 S1 coverage evidence | P3 |
| `DOCS/experiments/0017-wp005-s1-handoff.md` | WP-005 S1 handoff (ORT + gate) | P5, P8 |

## 8. Parity corpus

| Path | Content | Dimensions |
|---|---|---|
| `parity/corpus/manifest.json` | 504-case manifest with SHA-256 digests | P1 |
| `parity/corpus/cases/*.npz` | 504 golden-trajectory case files | P1 |
| `parity/generate_corpus.py` | Corpus generation from PRINet 3.0.0 | P1 |
| `parity/test_parity_differential.py` | 6 differential tests | P1, P3 |
| `parity/README.md` | Parity package documentation | P1 |

## 9. Python package

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `python/prin/__init__.py` | 35 | Package root | P4 |
| `python/prin/_ort.py` | 411 | ORT provider probe | P1, P4 |
| `python/prin/_phase0.py` | 285 | Phase 0 exit-gate consolidation | P8 |
| `python/prin/dlpack.py` | 70 | DLPack bridge wrapper | P4 |
| `python/prin/parity/__init__.py` | 68 | Parity package root | P1 |
| `python/prin/parity/schema.py` | 319 | Canonical schema | P1 |
| `python/prin/parity/manifest.py` | 261 | Manifest + SHA-256 | P1 |
| `python/prin/parity/harness.py` | 189 | Differential harness | P1, P3 |
| `python/prin/parity/loader.py` | 98 | Corpus loader | P1 |
| `python/prin/parity/strategies.py` | 124 | Hypothesis strategies | P1, P3 |

## 10. Rust crates

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-kernels/src/mean_field_rk4.rs` | 484 | CPU reference + kernel dispatch | P4 |
| `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | 640 | CubeCL single-source kernels (audited unsafe) | P4, P7 |
| `crates/prin-py/src/dlpack.rs` | 566 | DLPack bridge (audited unsafe) | P4, P7 |
| `crates/prin-kernels/src/ops.rs` | 42 | Element-wise CPU kernels | P4 |
| `crates/prin-py/src/lib.rs` | 41 | PyO3 module root | P4 |
| `crates/prin-kernels/src/lib.rs` | 30 | Kernel crate root | P4 |

## 11. Tests

| Path | Tests | Purpose | Dimensions |
|---|---|---|---|
| `tests/test_wp001_baseline.py` | 31 | Foundation baseline | P3, P6 |
| `tests/test_parity_schema.py` | 16 | Schema validation | P1, P3 |
| `tests/test_phase0_gate.py` | 29 | Phase 0 exit gate | P3, P8 |
| `tests/test_ort_backends.py` | 29 | ORT provider probe | P3 |
| `tests/test_parity_manifest.py` | 11 | Manifest validation | P1, P3 |
| `tests/test_parity_harness.py` | 11 | Differential harness | P1, P3 |
| `tests/test_parity_loader.py` | 9 | Corpus loader | P1, P3 |
| `tests/test_dlpack_bridge.py` | 12 | DLPack bridge | P3, P4 |
| `tests/test_parity_strategies.py` | 6 | Hypothesis strategies | P3 |
| `tests/test_generate_corpus.py` | 2 | Corpus generation | P3 |
| `tests/test_scaffold.py` | 1 | Scaffold smoke | P3 |

## 12. CI workflows

| Path | Purpose | Dimensions |
|---|---|---|
| `.github/workflows/rust.yml` | Rust quality (3 OS) | P5 |
| `.github/workflows/python.yml` | Python quality (2 OS × 3 Py) | P5 |
| `.github/workflows/parity.yml` | Differential testing | P1, P5 |
| `.github/workflows/gpu.yml` | GPU tests (opt-in) | P5 |
| `.github/workflows/release.yml` | Wheel matrix + publish | P5, P8 |
| `.github/workflows/repro.yml` | Reproducibility | P5 |
| `.github/workflows/snyk.yml` | Snyk Code + Open Source | P5, P7 |

## 13. Config files

| Path | Key content | Dimensions |
|---|---|---|
| `Cargo.toml` | 8 workspace members, version 0.1.0-alpha.1 | P4 |
| `pyproject.toml` | maturin, ruff, mypy, interrogate, bandit, pytest config | P4, P3 |
| `rust-toolchain.toml` | Stable, rustfmt, clippy, llvm-tools | P4 |
| `.gitleaks.toml` | Secret scanning config | P7 |
| `.gitignore` | Ignores caches, build artifacts, `.pytest_basetemp` | P5 |

## 14. Models

| Path | Size | Purpose | Dimensions |
|---|---|---|---|
| `models/subconscious_controller.onnx` | 18 KB | Pre-trained ONNX graph | P1 |
| `models/subconscious_controller.onnx.data` | 86 KB | External tensor data | P1 |

## 15. Independent re-verification (this session)

| Command | Result | Dimensions |
|---|---|---|
| `ruff check` | All checks passed | P4 |
| `mypy --strict` | Success: no issues in 16 files | P4 |
| `interrogate` | 100.0% (104/104) | P2 |
| `bandit` | 0 low/medium/high | P7 |
| `pytest tests/` | 172 passed, 6 deselected, 99% | P3 |
| `cargo test --workspace` | 19 passed | P3, P4 |
| `cargo test -p prin-kernels --features wgpu,cpu` | 21 passed | P3, P4 |
| `cargo audit` | 1 allowed `paste` advisory | P7 |
| `pip-audit .` | No known vulnerabilities | P7 |
| `sphinx-build -W --keep-going` | build succeeded, 0 warnings | P2 |
| Snyk Code (MCP, medium+) | 0 issues | P7 |
| Snyk Open Source (MCP, low+) | 0 issues | P7 |

## 16. Git history

| Range | Commits | Content |
|---|---|---|
| `655521d..8d7999c` | 41 | Full Phase 0 (pre-launch scaffold through v0.1.0-alpha.1 release tag) |

# Phase 6 Evidence Index

**Phase:** 6 — Benchmarks, reproduction, docs, and RC1 release
**Date:** 2026-09-17
**Companion to:** [`phase-6-analytics-report.md`](phase-6-analytics-report.md)

Structured index of every evidence artefact cited in the Phase 6 analytics
report. Each entry states the file path, the dimension(s) it supports, and
a brief description.

---

## Source code artefacts (Rust)

| Path | Dimensions | Description |
|---|---|---|
| `crates/prin-dynamics/src/` (9 files, ~10,626 LOC) | P4 | Core ODE dynamics, coupling, integration |
| `crates/prin-metrics/src/` (9 files, ~2,775 LOC) | P4 | Chimera, coherence, order parameters, spectral |
| `crates/prin-tensor/src/` (5 files, ~1,672 LOC) | P4 | CP/Tucker decomposition |
| `crates/prin-kernels/src/` (14 files, ~9,760 LOC) | P1, P4 | GPU compute kernels (CubeCL); device-Handle dispatch (WP-036E) |
| `crates/prin-sim/src/` (12 files, ~7,666 LOC) | P1, P4 | Simulation engine; persistent device buffers (WP-036E) |
| `crates/prin-train/src/` (31 files, ~22,191 LOC) | P1, P3, P4 | Training stack; 13 trainable modules rebuilt (WP-036A) |
| `crates/prin-daemon/src/` (10 files, ~6,926 LOC) | P1, P4 | Subconscious controller daemon; DirectML re-export (WP-036F) |
| `crates/prin-py/src/` (32 files, ~13,762 LOC) | P4, P7 | PyO3 bindings; GPU bindings (WP-036D); zero-copy DLPack (WP-036E) |

## Source code artefacts (Python)

| Path | Dimensions | Description |
|---|---|---|
| `python/prin/__init__.py` + `_deprecation.py` | P1, P4 | 172-symbol frozen API surface; freeze/deprecation machinery |
| `python/prin/nn/` (18 files) | P1, P3, P4 | Trainable compatibility layers (WP-036A) |
| `python/prin/_torch_compat.py` | P1, P4 | CPU/GPU device dispatch (WP-036D) |
| `python/prin/kernels.py` | P1, P4 | Kernel reference bindings (DV-012) |
| `python/prin/reporting/` (6 files) | P1, P2 | Deterministic reporting, figures, tables, profiling (WP-034) |
| `python/prin/parity/` (7 files) | P1 | Parity harness, manifest, schema, strategies |

## Test artefacts

| Path | Tests | Dimensions | Description |
|---|---|---|---|
| `tests/test_acceptance_*.py` (40+ files) | ~1,670 | P1, P3 | PRINet 3.0 reference acceptance suite port (WP-036B/C) |
| `tests/test_train_bridge*.py` (9 files) | ~200 | P1, P3 | Trainable bridge gradcheck tests |
| `tests/test_wp036d_gpu_dispatch.py` | ~20 | P1, P3 | GPU dispatch acceptance (WP-036D) |
| `tests/test_wp036e_q3_zero_copy.py` | ~10 | P1, P3 | Zero-copy DLPack export (WP-036E) |
| `tests/test_wp036f_reexport.py` | ~10 | P1, P3 | DirectML re-export verification (WP-036F) |
| `tests/test_api_surface*.py` | ~200 | P1, P4 | API surface freeze/regression tests |
| `tests/test_benchrunner.py` | ~48 | P3 | Benchmark runner tests (WP-033) |
| `tests/test_notebooks.py` | ~28 | P2 | Notebook execution tests (WP-037) |
| `tests/test_paper_wiring.py` | ~13 | P2 | Paper artefact wiring (WP-037) |
| `crates/*/tests/` (32 files) | ~350 | P1, P3 | Rust integration/parity tests |

## Evidence JSON artefacts

| Path | Dimensions | Description |
|---|---|---|
| `EVIDENCE/0144S-wp036e-s3-changed-line-coverage.md` | P3, P5 | WP-036E changed-line coverage evidence |
| `EVIDENCE/0144S-wp036e-s3-dv003-timing-reprobe.md` | P1, P8 | DV-003 timing reprobe (device-event vs host wall-clock) |
| `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json` | P1, P8 | DirectML controller provider report |
| `EVIDENCE/0144W-wp036f-s3-remediation-gate.md` | P5, P7 | WP-036F remediation gate |
| `EVIDENCE/0144Y-wp036g-s1-dv-reverification/reverification.md` | P6, P9 | DV register reverification |

## Audit and governance artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/audits/033-wp033-audit.md` | P6 | WP-033 S2 audit (PASS-WITH-FINDINGS, 1 D2) |
| `DOCS/audits/034-wp034-audit.md` | P6 | WP-034 S2 audit (PASS-WITH-FINDINGS, 4 D4) |
| `DOCS/audits/035-wp035-audit.md` | P6 | WP-035 S2 audit (PASS-WITH-FINDINGS, 1 D4) |
| `DOCS/audits/036-wp036-audit.md` | P6 | WP-036 S2 audit (PASS-WITH-FINDINGS, 2 D4) |
| `DOCS/audits/036a-wp036a-audit.md` | P6 | WP-036A S2 audit (PASS, zero findings) |
| `DOCS/audits/036b-wp036b-audit.md` | P6 | WP-036B S2 audit (PASS, zero findings) |
| `DOCS/audits/036c-wp036c-audit.md` | P6 | WP-036C S2 audit (FAIL → S3 CLEAN, 9 findings) |
| `DOCS/audits/036d-wp036d-audit.md` | P6 | WP-036D S2 audit (PASS-WITH-FINDINGS, 3 findings) |
| `DOCS/audits/036e-wp036e-audit.md` | P6 | WP-036E S2 audit (FAIL → S3 CLEAN, 4 findings) |
| `DOCS/audits/036f-wp036f-audit.md` | P6 | WP-036F S2 audit (PASS-WITH-FINDINGS, 2 findings) |
| `DOCS/audits/036g-wp036g-audit.md` | P6 | WP-036G S2 audit (PASS, zero findings) |
| `DOCS/audits/037-wp037-audit.md` | P6 | WP-037 S2 audit (FAIL → S3 CLEAN, 8 findings) |
| `DOCS/audits/038-wp038-audit.md` | P6 | WP-038 S2 audit (PASS-WITH-FINDINGS, 6 findings) |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_006.md` | P1, P5 | EMA-006 mid-phase mathematical audit |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_007.md` | P1, P5 | EMA-007 Phase 6 close mathematical audit (PASS) |
| `DOCS/audits/EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_001.md` | P2, P5 | EDA-001 first documentation audit |
| `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md` | P3, P5 | ETCA-001 first testing/CI audit |
| `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_002.md` | P3, P5 | ETCA-002 testing/CI audit remediation |

## Project state reports

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/reports/033-project-state.md` | P6 | PSR-033 (WP-033 cycle) |
| `DOCS/reports/034-project-state.md` | P6 | PSR-034 (WP-034 cycle) |
| `DOCS/reports/035-project-state.md` | P6 | PSR-035 (WP-035 cycle) |
| `DOCS/reports/036-project-state.md` | P6 | PSR-036 (WP-036 cycle) |
| `DOCS/reports/036a-project-state.md` | P6 | PSR-036a (WP-036A cycle) |
| `DOCS/reports/036b-project-state.md` | P6 | PSR-036b (WP-036B cycle) |
| `DOCS/reports/036c-project-state.md` | P6 | PSR-036c (WP-036C cycle) |
| `DOCS/reports/036d-project-state.md` | P6 | PSR-036d (WP-036D cycle) |
| `DOCS/reports/036e-project-state.md` | P6 | PSR-036e (WP-036E cycle) |
| `DOCS/reports/036f-project-state.md` | P6 | PSR-036f (WP-036F cycle) |
| `DOCS/reports/036g-project-state.md` | P6, P8, P9 | PSR-036g (WP-036G cycle, DV consolidation, Phase 7 entry statement) |
| `DOCS/reports/037-project-state.md` | P2, P6, P8 | PSR-037 (WP-037 cycle, documentation closure) |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | P6, P9 | Deferred validation register (DV-001 through DV-037) |

## Session artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/sessions/phase-6/README.md` | P6 | Phase 6 session directory README (92 files total) |
| `DOCS/sessions/phase-6/0129-wp033-s1-*.md` through `0152-wp038-s4-*.md` | P6 | Session briefs (all sub-sessions included) |
| `DOCS/sessions/SESSION_REGISTER.md` | P6 | Master session register (256 planned sessions) |
| `DOCS/sessions/TRACEABILITY.md` | P6 | Traceability matrix |

## Standards and plan artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | P2, P6, P8 | Project plan (Phase 6 row: `✅ COMPLETE`; amendments #30–#45) |
| `DOCS/standards/Coding_Standards.md` | P4 | Coding standards |
| `DOCS/standards/Testing_Standards.md` | P3 | Testing standards |
| `DOCS/standards/Documentation_Standards.md` | P2 | Documentation standards |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | P6 | Development workflow standards |
| `CHANGELOG.md` | P2 | Changelog (2,557 lines; Phase 6 entries present) |

## Math-audit artefacts

| Path | Dimensions | Description |
|---|---|---|
| `tools/math_audit_claims/prin-sim-phase6-stats-properties.json` | P1 | New EMA-006 ledger (Phase 6 sim statistics) |
| `tools/math_audit_claims/prin-train-phase6-properties.json` | P1 | New EMA-006 ledger (Phase 6 trainable properties) |

## Tools

| Path | Dimensions | Description |
|---|---|---|
| `tools/check_dv_register_gates.py` | P5, P6 | DV-register gate enforcement (R34 implementation) |
| `tools/wp036_migration_table.py` | P1, P2 | 172-symbol Migration Guide machine check |
| `tools/reproduce.py` | P1, P8 | Byte-identical reproduction pipeline |
| `tools/check_deviation_ledger.py` | P5, P6 | Cumulative deviation ledger consistency |
| `tools/check_no_python_numerics.py` | P4 | No-numerics-in-Python gate |
| `tools/wp001_baseline.py` | P1 | WP-001 baseline validation |
| `tools/check_bench_regression.py` | P3 | Benchmark regression gate |
| `tools/check_ci_green.py` | P5 | CI green verification |
| `tools/coverage_changed_lines.py` | P3 | Changed-line coverage |
| `tools/dv003_timing_probe.py` | P1, P8 | DV-003 device-event timing probe |

## CI workflows

| Path | Dimensions | Description |
|---|---|---|
| `.github/workflows/python.yml` | P5 | Python test matrix |
| `.github/workflows/rust.yml` | P5 | Rust fmt/clippy/test |
| `.github/workflows/gpu.yml` | P5 | GPU/CUDA tests |
| `.github/workflows/gpu-triton.yml` | P5 | Triton kernel tests (dormant) |
| `.github/workflows/parity.yml` | P5 | PRINet 3.0 parity |
| `.github/workflows/release.yml` | P5, P8 | PyPI + crates.io publishing |
| `.github/workflows/repro.yml` | P5 | Reproducibility checks |
| `.github/workflows/snyk.yml` | P5, P7 | Snyk security scanning |

## Independent verification outputs (this session)

| Command | Result | Dimensions |
|---|---|---|
| `cargo fmt --all -- --check` | Clean (exit 0) | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean (exit 0) | P4 |
| `cargo test --workspace --exclude prin-py -- --test-threads=1` | 1,577 passed, 0 failed, 1 ignored | P3 |
| `cargo audit` | 3 governed warnings (paste, bincode, chacha20), exit 0 | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings | P2 |
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed | P4 |
| `ruff format --check` (same paths) | 252 files already formatted | P4 |
| `mypy python/prin --strict` | 62 files, 0 issues | P4 |
| `interrogate -c pyproject.toml python/prin` | 97.6% (987/1011) | P2 |
| `bandit -r python/prin -c pyproject.toml` | 0 issues (20,216 lines) | P7 |
| `pip-audit .` | No known vulnerabilities | P7 |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities | P7 |
| `tools/check_deviation_ledger.py` | Passed (120→128 rows) | P5, P6 |
| `tools/check_dv_register_gates.py` | Passed (37 rows, 198 sessions) | P5, P6 |
| `tools/wp001_baseline.py check` | Passed | P1 |
| `tools/wp036_migration_table.py check` | Passed (172 symbols) | P1, P2 |
| `tools/check_no_python_numerics.py` | Clean (19 modules) | P4 |
| `verify_api_surface(prin.__all__)` | `(set(), set())` | P1, P4 |
| `pytest tests/ -m "not slow and not gpu"` | Timed out at 300s (PSR-037: 2,873 passed) | P3, P5 |
| `pytest tests/ parity/` | Timed out at 600s (PSR-037: 3,496 passed) | P1, P3, P5 |

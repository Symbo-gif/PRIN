# Phase 5 Evidence Index

**Phase:** 5 — Daemon and experiment tooling
**Date:** 2026-08-26
**Companion to:** [`phase-5-analytics-report.md`](phase-5-analytics-report.md)

Structured index of every evidence artefact cited in the Phase 5 analytics
report. Each entry states the file path, the dimension(s) it supports, and
a brief description.

---

## Source code artefacts

| Path | Lines | Dimensions | Description |
|---|---|---|---|
| `crates/prin-daemon/src/lib.rs` | 112 | P4, P7 | Crate root; `#![forbid(unsafe_code)]` at line 85 |
| `crates/prin-daemon/src/state.rs` | 777 | P1, P4 | Controller state types |
| `crates/prin-daemon/src/model.rs` | 770 | P1, P4 | ONNX controller model loading |
| `crates/prin-daemon/src/onnx.rs` | 1,072 | P1, P4 | ONNX Runtime backend integration |
| `crates/prin-daemon/src/backend.rs` | 681 | P1, P4 | Cross-provider backend selection |
| `crates/prin-daemon/src/error.rs` | 236 | P4 | Typed `DaemonError` enum |
| `crates/prin-daemon/src/daemon.rs` | 1,281 | P1, P3, P4 | `SubconsciousDaemon` native runtime |
| `crates/prin-daemon/src/hooks.rs` | 528 | P1, P3, P4 | `TrainingHooks` training-loop integration |
| `crates/prin-daemon/src/assignment.rs` | 458 | P1, P4 | Hungarian/Kuhn-Munkres assignment solver |
| `crates/prin-daemon/src/mot.rs` | 1,011 | P1, P3, P4 | IoU/MOTA/MOTP/IDF1 metrics |
| `crates/prin-train/src/stats.rs` | ~400 | P1, P4 | Cohen's d, Welch t-test, Student's-t p-value |
| `crates/prin-train/src/adversarial.rs` | ~300 | P1, P4 | FGSM/PGD adversarial perturbation |
| `crates/prin-py/src/bindings/daemon.rs` | 1,082 | P4, P7 | PyO3 bindings for daemon (0 `unsafe`) |
| `crates/prin-py/src/bindings/phase5.rs` | 478 | P4, P7 | PyO3 bindings for Phase 5 modules (0 `unsafe`) |
| `python/prin/daemon.py` | 760 | P1, P4 | Python daemon facade (no numerics) |
| `python/prin/eval/__init__.py` | 43 | P1, P4 | MOT/temporal evaluation facade |
| `python/prin/experiments/__init__.py` | 125 | P1, P4 | Statistical/adversarial facade |

## Test artefacts

| Path | Tests | Dimensions | Description |
|---|---|---|---|
| `crates/prin-daemon/tests/daemon_concurrency.rs` | 4 | P3 | Daemon thread-safety tests |
| `crates/prin-daemon/tests/hooks_daemon_integration.rs` | 2 | P3 | Training hooks + daemon integration |
| `crates/prin-daemon/tests/integration_controller_model.rs` | 7 | P3 | Controller model integration |
| `crates/prin-daemon/tests/parity_mot.rs` | 2 | P1, P3 | MOT parity vs. `motmetrics` reference |
| `crates/prin-daemon/tests/parity_subconscious.rs` | 8 | P1, P3 | Subconscious controller parity vs. PRINet 3.0 |
| `crates/prin-daemon/tests/proptest_properties.rs` | 12 | P3 | Property-based tests for daemon modules |
| `tests/test_phase5_integration.py` | 8 | P1, P3 | End-to-end Phase 5 integration tests |

## Evidence JSON artefacts

| Path | Dimensions | Description |
|---|---|---|
| `EVIDENCE/0109-wp028-s1-controller-provider-report.json` | P1, P8 | ONNX controller provider report (CPU/DirectML/VitisAI) |
| `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` | P1, P8 | Lock-free control buffer pilot benchmark |
| `EVIDENCE/0125-wp032-s1-daemon-latency.json` | P1, P8 | Daemon latency acceptance evidence (p95 200 ns vs. PRINet 3.0 250 ns) |
| `EVIDENCE/0125-wp032-s1-provider-acceptance.json` | P1, P8 | Provider acceptance evidence |

## Audit and governance artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/audits/028-wp028-audit.md` | P6 | WP-028 S2 audit report (PASS, zero findings) |
| `DOCS/audits/029-wp029-audit.md` | P6 | WP-029 S2 audit report (PASS, zero findings) |
| `DOCS/audits/030-wp030-audit.md` | P6 | WP-030 S2 audit report (PASS, zero findings) |
| `DOCS/audits/031-wp031-audit.md` | P6 | WP-031 S2 audit report (PASS, zero findings) |
| `DOCS/audits/032-wp032-audit.md` | P6 | WP-032 S2 audit report (PASS, zero findings) |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_006.md` | P5, P6, P7 | EA-006 full-project executive audit |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_005.md` | P1, P5 | EMA-005 Phase 5 close mathematical audit |

## Project state reports

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/reports/028-project-state.md` | P6 | PSR-028 (WP-028 cycle) |
| `DOCS/reports/029-project-state.md` | P6 | PSR-029 (WP-029 cycle) |
| `DOCS/reports/030-project-state.md` | P6 | PSR-030 (WP-030 cycle) |
| `DOCS/reports/031-project-state.md` | P6 | PSR-031 (WP-031 cycle) |
| `DOCS/reports/032-project-state.md` | P6, P8 | PSR-032 (WP-032 cycle, Phase 5 exit gate GREEN) |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | P6, P9 | Deferred validation register (DV-001 through DV-028) |

## Session artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/sessions/phase-5/README.md` | P6 | Phase 5 session directory README |
| `DOCS/sessions/phase-5/0109-wp028-s1-*.md` through `0128-wp032-s4-*.md` | P6 | 20 session briefs (sessions 0109–0128) |
| `DOCS/sessions/SESSION_REGISTER.md` | P6 | Master session register (all Phase 5 sessions COMPLETE) |
| `DOCS/sessions/TRACEABILITY.md` | P6 | Traceability matrix |

## Standards and plan artefacts

| Path | Dimensions | Description |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | P2, P6, P8 | Project plan (Phase 5 row: `✅ COMPLETE`; amendment #30) |
| `DOCS/standards/Coding_Standards.md` | P4 | Coding standards |
| `DOCS/standards/Testing_Standards.md` | P3 | Testing standards |
| `DOCS/standards/Documentation_Standards.md` | P2 | Documentation standards |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | P6 | Development workflow standards |
| `CHANGELOG.md` | P2 | Changelog (Phase 5 entries present) |

## Math-audit artefacts

| Path | Dimensions | Description |
|---|---|---|
| `tools/math_audit_claims/prin-daemon-phase5-properties.json` | P1 | New EMA-005 ledger (6 claims: HUN-01, IOU-01, COHEN-01, WELCH-DF-01, GAMMA-REFLECT-01, BETA-SYM-01) |
| `EVIDENCE/math-audit/manual/ema-005-wolfram-corroboration.{wls,txt}` | P1 | Wolfram Engine cross-validation for EMA-005 claims |
| `EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py` | P5, P7 | M-F9/DV-026 remediation verification |

## Independent verification outputs (this session)

| Command | Result | Dimensions |
|---|---|---|
| `cargo fmt --all -- --check` | Clean (exit 0) | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean (exit 0) | P4 |
| `cargo test --workspace --exclude prin-py -- --test-threads=1` | 1442 passed, 0 failed, 1 ignored | P3 |
| `cargo audit` | 2 pre-accepted warnings (paste DV-008, bincode DV-017), 0 new | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings | P2 |
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | Clean | P4 |
| `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | 76 files already formatted | P4 |
| `mypy python/prin --strict` | 28 files, 0 issues | P4 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (266/266) | P2 |
| `bandit -r . -c pyproject.toml` | 0 medium/high (2 Low in EVIDENCE/) | P7 |
| `pip-audit .` | No known vulnerabilities | P7 |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities | P7 |
| `snyk code test --severity-threshold=medium` | 0 issues | P5, P7 |
| `sphinx-build -W --keep-going -b html` (fresh directory) | 0 warnings | P2 |
| `tools/check_deviation_ledger.py` | Passed (111→112 rows) | P5, P6 |
| `tools/wp001_baseline.py check` | Passed | P1 |
| `pytest tests/ -m "not slow and not gpu"` | 555 passed, 8 deselected | P3 |
| `pytest tests/ parity/` | 1155 passed | P1, P3 |

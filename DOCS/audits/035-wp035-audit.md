# PRIN Audit Report — WP-035 / Cycle 035

**Date:** 2026-08-27
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-035 "Reproduction pipeline and manifest" — `tools/reproduce.py` (+421 lines), `paper/artefact_manifest.json` (867 lines), `tests/test_reproduce.py` (337 lines), `tests/test_wp001_baseline.py` (9-line delta), `.github/workflows/repro.yml` (12-line delta)
**Sessions:** 0137 (S1 implementation); 0138 (this audit)
**Active brief:** `DOCS/sessions/phase-6/0138-wp035-s2-reproduction-pipeline-and-manifest.md`
**Git state:** `main` @ `34e1a74`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared deliverables present; 14-vs-15 figure discrepancy already governed by PSR-034/WP034-F1 factual correction. |
| Plan/architecture conformance (A2) | ✅ | No numerics in Python; orchestration only — imports `prin.reporting` generators, reads archived JSON data without importing/executing archived code; no dependency changes. |
| Tests in tandem + coverage (A3) | ✅ | 22 tests; `tools/reproduce.py` **100%** line coverage (161 statements, 0 miss); full fast suite 718 passed. |
| Numerical parity + invariants (A4) | ✅ | No new numerical primitives. Independently verified: 172 manifest records match, 39 outputs generated (28 figure files + 11 tables), tamper tests fail closed on all three mutation modes. |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy `-D warnings`, ruff, ruff format, mypy strict all clean. |
| Security (A6) | ✅ | No `unsafe`/`exec`/`eval`/`subprocess`; no new dependencies; `cargo audit`/`pip-audit`/bandit clean at governed thresholds; manifest destination confined to allowed roots; path-traversal and duplicate-name checks on manifest records. |
| Docstring/doc coverage (A7) | ✅ | `python/prin` interrogate 95.6% overall (PASS); all public functions in `tools/reproduce.py` have Google-style docstrings. |
| Repository hygiene (A8) | ⚠️ | Private cross-module import: `tools/reproduce.py:25` reaches into `prin.reporting._artifacts` for `ReportingError`, which is re-exported publicly (WP035-F1). |
| CI status (A9) | ✅ | Local gate reproduction clean (nothing pushed yet this cycle, per Push and CI cadence). `repro.yml` correctly removes the pre-WP-035 disabled guard and runs tamper tests + verified regeneration. |
| Artefact trail (A10) | ✅ | PSR-034 committed; S1 handoff note with full acceptance-criterion evidence map; session register and phase-6 README updated; deviation-ledger and DV-register gate checks pass. |

## 2. Methodology

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
# Reproduction pipeline verification
.venv\Scripts\python tools/reproduce.py --verify-manifest
# Verified 172 stored JSON artefacts. Generated 39 files. (exit 0)

# Reproduction tests with coverage
.venv\Scripts\python -m pytest tests/test_reproduce.py --cov=tools.reproduce --cov-report=term-missing --basetemp=.pytest_basetemp-wp035-audit -q
# 22 passed; tools/reproduce.py 100% (161 statements, 0 missed)

# Full fast test suite
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp-wp035-audit-fast -q
# 718 passed, 9 deselected

# WP-001 baseline regression tests
.venv\Scripts\python -m pytest tests/test_wp001_baseline.py -q --basetemp=.pytest_basetemp-wp035-audit-baseline
# 44 passed

# Python quality gates
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 127 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 33 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 95.6% (351/367), PASS
.venv\Scripts\python -m bandit -r tools/reproduce.py -c pyproject.toml        # 0 issues

# Dependency audits
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
cargo audit                                                                   # exit 0; DV-008/DV-017 allowed warnings only

# Rust quality gates
cargo fmt --all -- --check                                                    # exit 0
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0

# Governance tools
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/033-project-state.md DOCS/reports/034-project-state.md
# Ledger consistency check passed (113 vs 117 rows)
.venv\Scripts\python tools/check_dv_register_gates.py                         # 29 rows / 198 sessions, passed

# Sphinx documentation
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# build succeeded (0 warnings, fresh directory)
```

## 3. Detailed findings

### 3.1 WP scope conformance (A1)

The S1 commit `34e1a74` delivers exactly the declared scope:

| Deliverable | Status | Evidence |
|---|---|---|
| `tools/reproduce.py` — complete CLI/API | ✅ | 421 lines added; typed errors, SHA-256 hashing, manifest load/append/verify, reproduction runner, CLI |
| `paper/artefact_manifest.json` — governed 172-record manifest | ✅ | schema_version 1, 172 entries, all `.json`, sorted, unique, full SHA-256 digests |
| `tests/test_reproduce.py` — test suite | ✅ | 22 tests covering manifest verification, append-only semantics, tamper detection, CLI modes, schema validation |
| `tests/test_wp001_baseline.py` — updated guard | ✅ | Retired pre-WP-035 guard replaced with assertions that repro CI runs tamper tests and verified pipeline |
| `.github/workflows/repro.yml` — active CI | ✅ | `PRIN_REPRO_ENABLED` guard removed; runs `pytest tests/test_reproduce.py` then `python tools/reproduce.py --verify-manifest` |
| S1 handoff note | ✅ | `DOCS/experiments/0137-wp035-s1-handoff.md` with full acceptance-criterion evidence map and parity disposition |

No undeclared scope was shipped. The diff is confined to the 10 files reported in `--stat`. No changes to `pyproject.toml`, `Cargo.toml`, or `Cargo.lock` — zero new dependencies.

The 14-vs-15 figure count follows PSR-034's governed WP034-F1 factual correction: PRINet 3.0 has 14 verifiable generators (`fig2`–`fig15`); no `fig1` exists. The pipeline correctly generates all 14.

### 3.2 Plan/architecture conformance (A2)

- **No Python numerics.** `tools/reproduce.py` imports only `argparse`, `hashlib`, `json`, `re`, `sys`, `tempfile`, `dataclasses`, `pathlib`, `typing` from stdlib, plus `prin.reporting` for generation. No oscillator equations, kernel dispatch, or numerical computation.
- **Archived code is never imported.** The pipeline reads JSON data from the archived `benchmarks/results/` directory but imports only current `prin.reporting` generators — exactly as the handoff note's scope decision §1 states.
- **Crate layering preserved.** No Rust code changed; `cargo fmt`/`clippy`/`test` all clean.
- **Seed flow preserved.** No RNG is sampled; the pipeline is fully deterministic from stored inputs.

### 3.3 Tests in tandem + coverage (A3)

- **22 tests** in `tests/test_reproduce.py`, all in the same S1 commit as the code.
- **100% line coverage** on `tools/reproduce.py` (161 statements, 0 miss).
- Tests cover: repository manifest validation (172 records), append-only behavior (add/modify/delete/resize), three tamper mutation modes (missing/corrupt/extra), size-before-hash optimization, 8 malformed-manifest parametric cases, output mode selection, conflicting-mode rejection, verify-before-generation ordering, CLI success/failure paths, and deterministic checksum output.
- The updated `test_wp001_baseline.py` regression test confirms the CI workflow no longer contains the disabled guard and does contain the active pipeline commands.
- Full fast suite: **718 passed**, 9 deselected. Full suite: S1 reported 1319 passed; audit independently confirmed 718 in the fast suite.

### 3.4 Numerical parity + invariants (A4)

No new numerical primitives. The applicable golden evidence is:

- **Manifest integrity:** `test_repository_manifest_matches_all_stored_json_artefacts` validates all 172 records; the production command independently reports `Verified 172 stored JSON artefacts.`
- **Output completeness:** Two independent runs both generated exactly 39 files (28 figure outputs: 14 PDF + 14 PNG; 11 LaTeX tables).
- **Determinism:** Two consecutive runs produced identical `Generated 39 files.` summaries with identical SHA-256 values for every output.
- **Tamper detection:** Three parametric mutation modes (deletion, same-size corruption, unmanifested addition) all raise `ManifestMismatchError`. Additional tests cover size changes, append-time mutation/removal, and verify-before-generation ordering (generation never runs after verification failure).
- **Append-only semantics:** Existing records are verified before new ones are added; modified, resized, or missing artefacts cause hard failure.

### 3.5 Quality gates (A5)

All clean:

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check` | 127 files already formatted |
| `mypy python/prin --strict` | 33 files, 0 issues |

### 3.6 Security (A6)

- **No `unsafe`, `exec`, `eval`, `subprocess`, `os.system`, or `__import__`** in `tools/reproduce.py` (grep-verified).
- **No new dependencies** — `pyproject.toml`, `Cargo.toml`, and `Cargo.lock` are unchanged.
- **Manifest destination confinement:** `append_manifest` rejects paths outside `paper/`, `benchmarks/results/`, and the OS temp directory (`ReproductionConfigurationError`).
- **Path-traversal protection:** manifest record paths are validated to be plain filenames (no `/`, `\\`, parent references); `Path.name != path` check rejects `../escape.json`.
- **Duplicate detection:** duplicate manifest paths are rejected at load time.
- **bandit:** 0 issues on `tools/reproduce.py`.
- **cargo audit:** exit 0; only governed DV-008 (`paste`) and DV-017 (`bincode`) allowed warnings — unchanged from prior cycles.
- **pip-audit:** 0 vulnerabilities in both project and Sphinx requirements.

### 3.7 Docstring/doc coverage (A7)

- **interrogate:** 95.6% overall (351/367), PASS at ≥95% threshold. All public functions/classes in `python/prin` have Google-style docstrings.
- **`tools/reproduce.py`:** all public functions (`compute_sha256`, `load_manifest`, `append_manifest`, `verify_manifest`, `run_reproduction`, `main`) and all public classes (`ReproductionError`, `ReproductionConfigurationError`, `ManifestFormatError`, `ManifestMismatchError`, `ManifestRecord`, `ReproductionResult`) have complete Google-style docstrings with Args/Returns/Raises sections.
- **Sphinx:** clean-directory build with `-W --keep-going` passes with 0 warnings.

### 3.8 Repository hygiene (A8)

- **No TODO/FIXME/HACK/XXX/STUB markers** in `tools/reproduce.py` or `tests/test_reproduce.py` (grep-verified).
- **No orphan files** — all 10 changed files are accounted for in the WP scope.
- **Session register and phase-6 README** correctly updated: session 0137 marked COMPLETE.
- **Finding WP035-F1:** `tools/reproduce.py:25` imports `ReportingError` from the private module `prin.reporting._artifacts`. The same symbol is re-exported through `prin.reporting.__init__.py` and listed in its `__all__`. This is the same cross-module private-import pattern as WP034-F4, which was FIXED in commit `8dbf55d`. The WP-035 code reaches into the same private module from outside the package.

### 3.9 CI status (A9)

Per the Push and CI cadence (Plan amendment #28), nothing has been pushed this cycle; S2 verifies by local gate reproduction:

- All Python quality gates green (ruff, mypy, interrogate, bandit, pip-audit).
- All Rust quality gates green (fmt, clippy, test, audit).
- 718 fast-suite tests pass; 44 WP-001 baseline tests pass.
- `repro.yml` correctly activates the pipeline: removes `PRIN_REPRO_ENABLED` guard, adds relevant path triggers, runs tamper tests and verified regeneration.
- Deviation-ledger consistency check passes (113 vs 117 rows).
- DV-register gate check passes (29 rows / 198 sessions).

### 3.10 Artefact trail (A10)

- **PSR-034** committed at `DOCS/reports/034-project-state.md` with complete cumulative deviation ledger (117 rows).
- **WP-034 audit** at `DOCS/audits/034-wp034-audit.md` exists and is consistent.
- **S1 handoff note** at `DOCS/experiments/0137-wp035-s1-handoff.md` with full acceptance-criterion evidence map and parity-evidence disposition.
- **Session register** updated: 0137 COMPLETE, 0138 PLANNED.
- **`DOCS/sessions/phase-6/README.md`** updated consistently.

### 3.11 Out-of-scope observation: pre-existing unseeded gradcheck

The S1 handoff note §"Out-of-scope discoveries" §1 reports a non-repeating `test_encode_gradcheck` Jacobian mismatch in `tests/test_train_bridge_ablation.py` during the first full-suite run. The test passed immediately in isolation and in a complete clean rerun (1319 passed). The audit independently ran the test in isolation: **PASSED**. This is a pre-existing, unseeded random-input test unrelated to WP-035 scope. It is noted for independent tracking without expanding WP-035 retroactively.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP035-F1 | D4 | `tools/reproduce.py:25` | `from prin.reporting._artifacts import ReportingError` reaches into the private `_artifacts` module. `ReportingError` is re-exported through `prin.reporting.__init__.py` and listed in its `__all__`. Same pattern as WP034-F4 (FIXED in `8dbf55d`). | Coding Standards (public-surface imports); 3.0 audit methodology (repository hygiene) | Change to `from prin.reporting import ReportingError`. |

## 5. Deviation-ledger delta

New findings added to the ledger: **WP035-F1** (D4, private cross-module import). Carried findings re-inspected: WP034-F1 (closed in PSR-034 S4, no recurrence). No unresolved D1/D2 findings exist.

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS** — one D4 finding (WP035-F1). No D1/D2/D3 findings.

The reproduction pipeline is functionally complete, secure, and well-tested. All 172 stored JSON artefacts verify, all 14 figures and 11 tables regenerate deterministically in seconds without GPU/training, tamper tests fail closed on all mutation modes, and CI is correctly activated. The single finding is a cosmetic import-path consistency issue identical in kind to the WP034-F4 pattern fixed earlier.

**Ordered S3 work list:**

1. **WP035-F1 (D4):** Change `tools/reproduce.py:25` from `from prin.reporting._artifacts import ReportingError` to `from prin.reporting import ReportingError`. Add a regression assertion in `test_wp001_baseline.py` or a targeted test that `tools/reproduce` does not import from `prin.reporting._*` private modules.

---

## 7. Closure table (appended by S3 remediation)

**Session:** 0139 (WP-035 S3) — **Git state at entry:** `main` @ `34e1a74` —
**Remediation commit:** `cbbbbb3`

| ID | Severity | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|---|
| WP035-F1 | D4 | **FIXED** | `cbbbbb3` — `tools/reproduce.py:25` changed from `from prin.reporting._artifacts import ReportingError` to `from prin.reporting import ReportingError`; regression test `test_reproduce_imports_only_public_reporting_surface` added to `tests/test_reproduce.py` (AST-parses the module, fails on any `prin.reporting._*` import, and asserts `reproduce.ReportingError is prin.reporting.ReportingError`). | A8 re-check: `grep -n "prin\.reporting\._" tools/reproduce.py` → no matches; only import is `from prin.reporting import ReportingError` (line 25). `ReportingError` still used at lines 325 (docstring) and 408 (`except` clause). New regression test passes. See §7.1. |

### 7.1 Delta re-audit (touched checklist rows)

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0 at `main` @ `cbbbbb3`:

| Row | Check | Result |
|---|---|---|
| A2 — Plan/architecture | `prin.reporting` imports are public-surface only; no private `_*` module reached from `tools/`. `ReportingError` resolves to the identical class object exported in `prin.reporting.__all__`. | ✅ |
| A3 — Tests in tandem + coverage | `pytest tests/test_reproduce.py --cov=tools.reproduce --cov-report=term-missing` → **23 passed**; `tools/reproduce.py` **100%** (161 statements, 0 miss). Regression test committed in the same commit as the fix. | ✅ |
| A3 — Fast suite | `pytest tests/ -m "not slow and not gpu"` → **719 passed**, 9 deselected (was 718; +1 = the new regression test). | ✅ |
| A3 — WP-001 baseline | `pytest tests/test_wp001_baseline.py` → **44 passed**. | ✅ |
| A4 — Acceptance evidence | `python tools/reproduce.py --verify-manifest` → `Verified 172 stored JSON artefacts.` / `Generated 39 files.` (14 PDF + 14 PNG figures + 11 LaTeX tables), exit 0. Tamper tests (`missing` / `corrupt` / `extra` mutation modes) still fail closed with `ManifestMismatchError`. | ✅ |
| A5 — Quality gates | `ruff check python/ tests/ benchmarks/ tools/ parity/` → All checks passed. `ruff format --check` → 127 files already formatted. `mypy tools/reproduce.py --strict` → 0 issues; `mypy python/prin --strict` → 33 files, 0 issues. `cargo fmt --all -- --check` → exit 0. `cargo clippy --workspace --all-targets -- -D warnings` → exit 0. `cargo test --workspace` → all pass. | ✅ |
| A6 — Security | `bandit -r tools/reproduce.py -c pyproject.toml` → 0 issues. `pip-audit .` → No known vulnerabilities. `cargo audit` → exit 0; only governed DV-008 (`paste`) / DV-017 (`bincode`) allowed warnings. No dependency changes (`pyproject.toml`, `Cargo.toml`, `Cargo.lock` untouched). | ✅ |
| A7 — Docs | `interrogate -c pyproject.toml python/prin` → 95.6% (351/367), PASS. `sphinx-build -W --keep-going -b html DOCS/sphinx …` → build succeeded, 0 warnings. | ✅ |
| A8 — Hygiene | Private cross-module import removed (the sole finding). No TODO/FIXME/STUB markers introduced. Diff confined to `tools/reproduce.py` (1 line) and `tests/test_reproduce.py` (+24 lines). | ✅ |
| A9 — CI (local gate) | Per the Push and CI cadence, nothing pushed this cycle; local gate reproduced green above. `check_deviation_ledger.py 033→034` → passed (113 vs 117 rows). `check_dv_register_gates.py` → passed (29 rows / 198 sessions). | ✅ |
| A10 — Artefact trail | This closure table appended; no register/PSR changes required at S3 (deviation-ledger update belongs to S4 per Development Workflow §3). | ✅ |

**Delta re-audit date:** 2026-08-27 — **Result:** **CLEAN**. The single D4
finding (WP035-F1) is **FIXED** with a regression test in the same commit
(`cbbbbb3`). No D1/D2/D3 findings existed. No new deviation introduced; no D4
carried. Full local gate green. Exit gate satisfied — hand off to S4 (0140).

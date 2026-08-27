# PRIN Audit Report — WP-034 / Cycle 034

**Date:** 2026-08-27
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-034 "Reporting, figures, tables, and profiling" — `python/prin/reporting/` (4 modules + `__init__.py`, +2 226 lines), `tests/test_reporting_profiler.py` (525 lines), `tests/test_publication_generation.py` (430 lines)
**Sessions:** 0133 (S1 implementation); 0134 (this audit)
**Active brief:** `DOCS/sessions/phase-6/0134-wp034-s2-reporting-figures-tables-and-profiling.md`
**Git state:** `main` @ `d88a331`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope delivered; 14-vs-15 figure discrepancy is a factual correction, not a code defect (WP034-F1). |
| Plan/architecture conformance (A2) | ✅ | No numerics in Python; reporting/rendering/profiling only; crate layering preserved; no dependency changes. |
| Tests in tandem + coverage (A3) | ✅ | 70 tests; `prin.reporting` 99% line coverage (1 044 stmts, 13 miss); interrogate 95.6% overall (PASS). |
| Numerical parity + invariants (A4) | ✅ | No new numerical primitives; stored-artefact byte comparison and deterministic normalization are the applicable golden evidence. |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy `-D warnings`, ruff, ruff format, mypy strict all clean. |
| Security (A6) | ✅ | No `subprocess`/`eval`/`exec`/`shell=True`; no new deps; `cargo audit`/`pip-audit`/bandit clean at governed thresholds; output-path confinement with symlink-safe `resolve()` on every writer. |
| Docstring/doc coverage (A7) | ✅ | `python/prin` interrogate 95.6% overall (PASS); all public functions have Google-style docstrings; doctests pass. |
| Repository hygiene (A8) | ⚠️ | Cross-module private import (`_load_json`) between `table_generation` and `figure_generation` (WP034-F4). |
| CI status (A9) | ✅ | Local gate reproduction clean (nothing pushed yet this cycle, per Push and CI cadence). |
| Artefact trail (A10) | ✅ | PSR-033 committed; S1 handoff note with full acceptance-criterion evidence map; session register and phase-6 README updated. |

## 2. Methodology

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
# Python quality gates
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 125 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 32 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 95.6% (348/364), PASS
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 2 pre-existing Low in EVIDENCE/ (not this WP)

# Dependency audits
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities

# Doctests
.venv\Scripts\python -m doctest python/prin/reporting/figure_generation.py python/prin/reporting/table_generation.py
                                                                               # exit 0

# WP-034 coverage
.venv\Scripts\python -m pytest tests/test_reporting_profiler.py tests/test_publication_generation.py --cov=prin.reporting --cov-report=term-missing --basetemp=.pytest_basetemp-wp034 -q
                                                                               # 70 passed; prin.reporting 99% (1044 stmts, 13 miss)

# Fast test suite
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
                                                                               # 694 passed, 9 deselected

# Rust quality gates
cargo fmt --all -- --check                                                     # exit 0
cargo clippy --workspace --all-targets -- -D warnings                          # exit 0
cargo audit                                                                   # exit 0; 2 allowed warnings (DV-008/DV-017)

# Sphinx documentation
Remove-Item -Recurse -Force DOCS/sphinx/_build -ErrorAction SilentlyContinue
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
                                                                               # build succeeded, 0 warnings

# Governance tools
.venv\Scripts\python tools/check_dv_register_gates.py                         # 29 rows / 198 sessions, passed
.venv\Scripts\python tools/wp001_baseline.py check                            # passed

# Dependency manifest diff
git diff daaafd9..d88a331 -- pyproject.toml Cargo.toml Cargo.lock              # empty — no dependency changes
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Scope delivered.** The S1 commit (`d88a331`) adds:

- `python/prin/reporting/benchmark_reporting.py` (562 lines): deterministic Markdown benchmark reports, leaderboards, SCALR summaries, typed validation/errors, Markdown escaping, confined writes.
- `python/prin/reporting/figure_generation.py` (1 243 lines): 14 stored-artefact figure generators, headless 300-DPI style, typed artefact/schema/output errors, deterministic PDF/PNG normalization, master generation.
- `python/prin/reporting/table_generation.py` (808 lines): 11 byte-comparable LaTeX fragment generators and master generation.
- `python/prin/reporting/profiler.py` (513 lines): typed `torch.profiler` wrapper, legacy `ProfileReport`, Chrome trace export, training-loop helper, explicit Rust-backed operation labels.
- `python/prin/reporting/__init__.py` (modified): public reporting API exports (55 symbols in `__all__`).
- `tests/test_reporting_profiler.py` (525 lines): 59 tests covering reports, leaderboards, SCALR, profiler lifecycle, trace, validation, and training-loop.
- `tests/test_publication_generation.py` (430 lines): 11 tests covering all 14 figure generators, all 11 table generators, stored 3.0 artefacts, exact table bytes, deterministic normalization, schema errors, and output confinement.
- `DOCS/experiments/0133-wp034-s1-handoff.md` (201 lines): full acceptance-criterion evidence map.

**14-vs-15 figure discrepancy.** The session brief declares "15 figures." S1 verified that the PRINet 3.0 reference contains 14 figure generators (fig2–fig15) and 14 stored figure outputs (28 files: 14 PDF + 14 PNG). No fig1 exists in either the archived reference module (`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/utils/figure_generation.py`) or the stored outputs (`paper/figures/`). The `FIGURE_GENERATORS` dict registers exactly 14 entries. This is a factual discrepancy in the session brief, correctly flagged by S1 for S2 disposition (WP034-F1).

**11 LaTeX tables confirmed.** The `TABLE_GENERATORS` dict registers exactly 11 entries. All 11 regenerate byte-identical output from stored 3.0 JSON artefacts.

**No undeclared scope shipped.** `git diff --stat` confirms all 12 changed files are within `python/prin/reporting/`, `tests/`, and `DOCS/` (experiments, sessions). No `crates/`, CI workflow, or dependency-manifest changes.

### 3.2 A2 — Plan/architecture conformance

**No numerics in Python.** All four modules are reporting/rendering/profiling only:

- `benchmark_reporting.py`: Markdown report generation from stored JSON. The SCALR CV computation (population standard deviation / mean over caller-supplied values) is a reporting statistic, not a model primitive.
- `figure_generation.py`: matplotlib rendering of stored JSON values. No scientific computation.
- `table_generation.py`: LaTeX rendering of stored JSON values. No scientific computation.
- `profiler.py`: `torch.profiler` wrapper. No dynamics, kernels, or optimizers.

**Crate layering preserved.** No changes to `crates/`, `pyproject.toml`, `Cargo.toml`, or `Cargo.lock`.

**Deterministic output preserved.** Report timestamps are caller-supplied only (no implicit `datetime.now()`). PDF metadata uses a fixed date (`datetime(2000, 1, 1)`). SVG has a fixed `hashsalt`. Matplotlib uses the non-interactive `Agg` backend. The profiler documents that it does not mutate RNG state.

### 3.3 A3 — Tests in tandem + coverage

**70 tests** across two test files:

| Test file | Count | What it covers |
|---|---|---|
| `test_reporting_profiler.py` | 59 | Benchmark report determinism, legacy schema preservation, UTC timestamp normalization, Markdown escaping, output confinement, leaderboard ranking/tie-breaking, SCALR windowed summary, malformed-JSON isolation, profiler lifecycle/state validation, Rust-backed operation labels, Chrome trace export, training-loop forward/backward, input validation (8 parametrized cases), empty/invalid batch rejection, non-scalar loss rejection, event timing sanitization |
| `test_publication_generation.py` | 11 | All 14 figure generators, all 11 table generators, stored 3.0 artefact regeneration, exact LaTeX byte comparison, deterministic normalized PNG/PDF, schema errors (missing keys, non-object JSON, invalid JSON), missing-artefact errors, output-path confinement, normalizer format validation, optional Phase 1 tables, throughput formatting |

**Coverage: 99% on `prin.reporting`** (1 044 statements, 13 miss). Missed lines are defensive error-path branches in `_ArtifactError` formatting, `ArtifactSchemaError`/`OutputPathError` string formatting edge cases, and a warmup-step scheduler branch — all unreachable through the public API under normal test conditions.

**≥95% changed-code gate: SATISFIED** (99% ≥ 95%).

**Interrogate: 95.6% overall** (348/364), PASS at the ≥95% threshold. Per-module: `benchmark_reporting.py` 100%, `profiler.py` 100%, `__init__.py` 100%; `figure_generation.py` 72% and `table_generation.py` 65% — the misses are private helper functions (e.g. `_save_fig`, `_row`, `_col`, `_checked`, `_load_json`, `_dirs`) without standalone docstrings. All public functions have Google-style docstrings with Args/Returns/Raises/Examples sections.

### 3.4 A4 — Numerical parity + invariants

**No new numerical primitive introduced.** The parity-evidence disposition in the S1 handoff note is accurate: this WP ports reporting/rendering/profiling contracts, not scientific computations. Stored-artefact byte comparison (11 LaTeX fragments) and deterministic normalization (PDF/PNG) are the applicable golden evidence.

**Stored 3.0 artefacts regenerate correctly.** `test_stored_3_0_artefacts_regenerate_all_outputs` points the generators at the repository's stored PRINet 3.0 JSON artefacts and verifies all 14 figures (PDF + PNG = 28 files) and all 11 LaTeX fragments. Every table is byte-compared against its stored counterpart.

**Deterministic normalization is stable.** `test_repeat_figure_generation_has_deterministic_normalized_bytes` proves the PDF/PNG normalization produces identical output across repeated generation.

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | exit 0 (no Rust source changed) |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | 125 files already formatted |
| `mypy python/prin --strict` | 32 files, 0 issues |

### 3.6 A6 — Security

| Check | Result |
|---|---|
| `subprocess`/`eval`/`exec`/`os.system`/`shell=True` in `python/prin/reporting/` | None found |
| `pickle.load`/`yaml.load`/unsafe deserialization | None — only `json.load`/`json.loads` |
| Runtime code generation / `__import__` | None found |
| `cargo audit` | exit 0; 2 allowed warnings (DV-008 `paste` RUSTSEC-2024-0436, DV-017 `bincode` RUSTSEC-2025-0141 — unchanged) |
| `pip-audit .` | 0 vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | 0 vulnerabilities |
| `bandit -r . -c pyproject.toml` | 2 pre-existing Low in `EVIDENCE/math-audit/` (not this WP) |
| New dependencies | None (`git diff` on `pyproject.toml`/`Cargo.toml`/`Cargo.lock` is empty) |
| `unsafe` (Rust) | No Rust source changed |
| Output-path confinement | All four modules resolve paths via `Path.resolve()` (follows symlinks) and check against 3 allowed roots before every write; typed errors on escape |
| Snyk Code | S1 reports 0 issues on all changed files at Low threshold |

### 3.7 A7 — Docstring/doc coverage

- `python/prin` interrogate: **95.6%** (348/364) — PASS at ≥95% threshold.
- All public functions/classes in the four reporting modules have Google-style docstrings with Args, Returns, Raises, and Examples sections.
- Module doctests pass (`python -m doctest` exit 0 on both `figure_generation.py` and `table_generation.py`).
- Sphinx warning-as-error build: **0 warnings** (fresh-directory build).
- `__init__.py` module docstring updated to reflect the completed port.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/HACK/XXX/STUB scan:** 0 matches in `python/prin/reporting/` and both test files.
- **`__all__` consistency:** `__init__.py` exports 55 symbols; every name matches an actual import from the submodules, and every submodule `__all__` is internally consistent.
- **No orphan files:** All new files are referenced by `__init__.py`, test files, or the handoff note.
- **Cross-module private import (WP034-F4):** `table_generation.py` imports `_load_json` (a private function by naming convention) from `figure_generation.py`. This creates a hidden coupling: changes to `_load_json` in `figure_generation.py` could break `table_generation.py` without any `__all__` or public-API signal. See §4.

### 3.9 A9 — CI status

Per the Push and CI cadence (Development Workflow and Audit Standards §3), nothing has been pushed this cycle; A9 is verified by local gate reproduction. All locally reproduced gates are green (see §2).

### 3.10 A10 — Artefact trail

- PSR-033 (`DOCS/reports/033-project-state.md`) committed and consistent.
- S1 handoff note (`DOCS/experiments/0133-wp034-s1-handoff.md`) committed with full acceptance-criterion evidence map.
- Session register (`DOCS/sessions/SESSION_REGISTER.md`) updated: 0133 marked COMPLETE.
- Phase-6 README (`DOCS/sessions/phase-6/README.md`) updated: 0133 marked COMPLETE.
- Deviation ledger in PSR-033 is up to date (no WP-034 entries yet — this audit adds the first).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP034-F1 | D4 | Session brief `0133-wp034-s1-reporting-figures-tables-and-profiling.md` (Mission) | Session brief declares "15 figures"; the PRINet 3.0 reference contains 14 (fig2–fig15). No fig1 exists in the archived module, stored outputs, or `FIGURE_GENERATORS` dict. S1 correctly implemented 14 and flagged the discrepancy. | Documentation Standards §1 (factual accuracy) | S4 should record the factual correction (14, not 15) in the PSR and CHANGELOG. No code change needed. |
| WP034-F2 | D4 | `python/prin/reporting/figure_generation.py:287,289,294,299` | `normalize_matplotlib_output` raises bare `ValueError` instead of the module's typed `PublicationGenerationError` hierarchy. Every other public function in the WP uses typed errors. | Coding Standards §3 (typed errors at public boundaries) | Raise `PublicationGenerationError` (or a new `NormalizationError` subclass) instead of bare `ValueError`. Update the docstring Raises section and the test match patterns accordingly. |
| WP034-F3 | D4 | `python/prin/reporting/benchmark_reporting.py:37,41` | `ReportInputError` and `ReportOutputError` subclass `ValueError`, while `PublicationGenerationError` (in `figure_generation.py`) subclasses `Exception` and `ProfilerConfigurationError` subclasses `ValueError`. The error hierarchy is inconsistent across the three reporting modules. | Coding Standards §3 (consistent error design) | Adopt a uniform base: either all reporting errors subclass a shared `ReportingError(Exception)` root, or all subclass `ValueError`/`RuntimeError` as appropriate. The current mix works but weakens type discrimination for callers catching base types. |
| WP034-F4 | D4 | `python/prin/reporting/table_generation.py:10-15` | `table_generation.py` imports `_load_json` (a private function by naming convention) from `figure_generation.py`. This creates a hidden cross-module coupling: changes to `_load_json` in `figure_generation.py` could break `table_generation.py` without any `__all__` or public-API signal. | Coding Standards §2 (module boundaries) | Promote `_load_json` to a shared utility module (e.g. `reporting/_json_utils.py`) or make it public (`load_json`) with a documented contract and `__all__` export. |

## 5. Deviation-ledger delta

**New findings:** WP034-F1, WP034-F2, WP034-F3, WP034-F4 (all D4).

**Carried findings re-inspected:** No unresolved findings were carried into WP-034 (PSR-033 confirms WP033-F1 was FIXED in S3; all prior findings are FIXED or AMENDED).

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

Four D4 findings: one session-brief factual discrepancy (14 vs. 15 figures), one bare-`ValueError` in a public normalizer function, one inconsistent error hierarchy across reporting modules, and one cross-module private import. The implementation is otherwise clean — all acceptance criteria are evidence-mapped, no new numerics, no security issues, no dependency changes, 99% coverage, all quality gates green, Sphinx clean, doctests pass.

**S3 ordered work list:**

1. **WP034-F2 (D4):** Replace bare `ValueError` in `normalize_matplotlib_output` with a typed error from the `PublicationGenerationError` hierarchy. Update docstring and test match patterns.
2. **WP034-F3 (D4):** Unify the error hierarchy across the three reporting modules (or document the rationale for the current mix).
3. **WP034-F4 (D4):** Promote `_load_json` to a shared utility or make it public with a documented contract.
4. **WP034-F1 (D4):** S4 records the 14-vs-15 factual correction in the PSR and CHANGELOG. No code change needed.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP034-F2 | FIXED | `11a97cb` — `normalize_matplotlib_output` now raises `NormalizationError(PublicationGenerationError, ValueError)`; docstring `Raises` section and regression test updated to assert on the typed error while confirming it remains a `ValueError` | §8 below: targeted + full test suites pass; ruff/mypy/interrogate/doctest/bandit clean |
| WP034-F3 | FIXED | `8dbf55d` — every reporting error (`PublicationGenerationError`, `ReportInputError`, `ReportOutputError`, `ProfilerConfigurationError`, `ProfilerStateError`, and their subclasses) now also subclasses a new shared `ReportingError(Exception)` root in `prin.reporting._artifacts`, while retaining each type's original stdlib base (`ValueError`/`RuntimeError`/`FileNotFoundError`) for backward-compatible `isinstance` catches | §8 below: new `test_all_reporting_errors_share_one_root` regression test passes; full suite green |
| WP034-F4 | FIXED | `8dbf55d` — `_load_json` (and its `_checked`/`_CheckedDict`/`_CheckedList` schema-validation machinery) moved out of `figure_generation.py` into new shared module `prin.reporting._artifacts`; `table_generation.py` now imports the loader from that shared module instead of reaching into `figure_generation`'s private name | §8 below: new `test_json_loading_is_shared_not_privately_cross_imported` regression test passes; full suite green |
| WP034-F1 | CARRIED(1) → WP-034 S4 (session 0136) | n/a — documentation-only correction; the audit's own remedy assigns the PSR/CHANGELOG factual correction ("14 figures, not 15") to S4, which is this cycle's documentation session, not a future WP. Recorded here as the single permitted D4 carry per Development Workflow and Audit Standards §5 | S4 must record the 14-vs-15 correction in PSR-034 and `CHANGELOG.md`; no source change required |

**Delta re-audit date:** 2026-08-27 **Result:** CLEAN

### 7.1 Delta re-audit method

Independent re-verification after the F2/F3/F4 commits, scoped to the touched
files and the WP-034 acceptance evidence:

- Read `python/prin/reporting/_artifacts.py` (new), and the diffs to
  `figure_generation.py`, `table_generation.py`, `benchmark_reporting.py`,
  `profiler.py`, `__init__.py`, and `tests/test_publication_generation.py`.
- Confirmed `figures.PublicationGenerationError is tables.PublicationGenerationError`
  and `figures.ArtifactSchemaError is tables.ArtifactSchemaError` still hold
  (shared identity preserved through the new common module), so no caller-visible
  behavior changed.
- Confirmed `_load_json` has exactly one definition in the package
  (`prin.reporting._artifacts`) and zero remaining private cross-module imports
  between `figure_generation.py` and `table_generation.py`.
- Confirmed every reporting error type is a subclass of the new `ReportingError`
  root while still satisfying every pre-existing `pytest.raises(ValueError, ...)`
  / `pytest.raises(RuntimeError, ...)` / `pytest.raises(FileNotFoundError, ...)`
  assertion in the existing test suite (no test weakened or skipped).
- Re-ran the full local gate (§8) and the WP-034-specific acceptance evidence
  (stored 3.0 byte-comparable artefact regeneration); all green with no new
  deviation introduced.

No new findings surfaced during the delta re-audit. WP034-F1 is the sole open
item, explicitly carried to S4 as documented above (first and only carry).

## 8. Delta re-audit command evidence

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0 after commits
`8dbf55d` (WP034-F3, WP034-F4) and `11a97cb` (WP034-F2):

```powershell
# WP-034 targeted tests + coverage
.venv\Scripts\python -m pytest tests/test_reporting_profiler.py tests/test_publication_generation.py --cov=prin.reporting --cov-report=term-missing --basetemp=.pytest_basetemp-wp034s3-final -q
                                                                               # 72 passed; prin.reporting 99% (1053 stmts, 13 miss)

# Full fast test suite
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp-full -q
                                                                               # 696 passed, 9 deselected (was 694 before; +2 new regression tests)

# Python quality gates
.venv\Scripts\ruff check python/prin/reporting/ tests/test_publication_generation.py tests/test_reporting_profiler.py
                                                                               # All checks passed
.venv\Scripts\ruff format --check python/prin/reporting/ tests/test_publication_generation.py tests/test_reporting_profiler.py
                                                                               # 9 files already formatted
.venv\Scripts\mypy python/prin --strict                                      # 33 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin            # 95.6% (351/367), PASS

# Doctests (including the new shared module)
.venv\Scripts\python -m doctest python/prin/reporting/_artifacts.py python/prin/reporting/figure_generation.py python/prin/reporting/table_generation.py
                                                                               # exit 0

# Security
.venv\Scripts\python -m bandit -r python/prin/reporting -c pyproject.toml    # 0 issues
.venv\Scripts\python -m pip_audit .                                          # 0 vulnerabilities
snyk code test python/prin/reporting/                                        # 0 issues
git diff daaafd9..HEAD -- pyproject.toml Cargo.toml Cargo.lock               # empty — no dependency changes (Snyk Open Source not applicable)

# Sphinx documentation
Remove-Item -Recurse -Force DOCS/sphinx/_build -ErrorAction SilentlyContinue
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
                                                                               # build succeeded, 0 warnings

# Rust quality gates (no Rust source touched this cycle)
cargo fmt --all -- --check                                                    # exit 0
cargo clippy --workspace --all-targets -- -D warnings                        # exit 0
cargo audit                                                                   # exit 0; 2 allowed warnings (DV-008/DV-017), unchanged

# Governance tools
.venv\Scripts\python tools/check_dv_register_gates.py                        # 29 rows / 198 sessions, passed
.venv\Scripts\python tools/wp001_baseline.py check                           # passed
```

All gates green with no newly introduced deviation. Full local gate reproduction
stands in for CI per the Push and CI cadence (S1–S3 commit locally only; the S4
commit is this cycle's sole push).

# PRIN Audit Report — WP-033 / Cycle 033

**Date:** 2026-08-26
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-033 "Unified benchmark runner and category migration" — `benchmarks/` (47 files, +3 461 lines), `tests/test_benchrunner.py` (708 lines)
**Sessions:** 0129 (S1 implementation); 0130 (this audit)
**Active brief:** `DOCS/sessions/phase-6/0130-wp033-s2-unified-benchmark-runner-and-category-migration.md`
**Git state:** `main` @ `dfa3a1e`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope delivered; 58-vs-62 correction is factual and evidenced. |
| Plan/architecture conformance (A2) | ✅ | No numerics in Python; Rust-backed orchestration only; crate layering preserved. |
| Tests in tandem + coverage (A3) | ⚠️ | 98% coverage on `benchmarks/`; 2 tests fail under the project's documented `--basetemp=.pytest_basetemp` Windows invocation (WP033-F1). |
| Numerical parity + invariants (A4) | ✅ | No new numerical primitives; all categories orchestrate already-parity-dispositioned Rust APIs. |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy `-D warnings`, ruff, ruff format all clean. |
| Security (A6) | ✅ | No `shell=True`; no new deps; `cargo audit`/`pip-audit`/bandit clean at governed thresholds; output-path confinement implemented. |
| Docstring/doc coverage (A7) | ✅ | `python/prin` interrogate 100% (266/266); every `benchmarks/` category has a module docstring and README; governed scope unaffected. |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers; `__all__` consistent across all 10 category packages + `_common`; no orphan files. |
| CI status (A9) | ✅ | Local gate reproduction clean (nothing pushed yet this cycle, per Push and CI cadence). |
| Artefact trail (A10) | ✅ | PSR-032 committed; S1 handoff note, traceability doc, and category READMEs all present. |

## 2. Methodology

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
# Rust quality gates (no Rust source changed this WP; re-verified for regression)
cargo fmt --all -- --check                                                     # exit 0
cargo clippy --workspace --all-targets -- -D warnings                          # exit 0
cargo audit                                                                   # exit 0; 2 allowed warnings (DV-008/DV-017, unchanged)

# Python quality gates on new code
.venv\Scripts\ruff check benchmarks/ tests/test_benchrunner.py                 # All checks passed!
.venv\Scripts\ruff format --check benchmarks/ tests/test_benchrunner.py        # 42 files already formatted
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 2 pre-existing Low in EVIDENCE/ (not this WP)
.venv\Scripts\python -m pip_audit .                                            # No known vulnerabilities found

# Governed docstring gate (python/prin only — benchmarks/ excluded per established scope)
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin              # 100.0% (266/266)

# Test suite — default temp dir (CI and Linux/Mac path)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" -q            # 624 passed, 9 deselected

# Test suite — in-repo basetemp (AGENTS.md-documented Windows workaround)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
                                                                               # 2 failed, 622 passed, 9 deselected (WP033-F1)

# Coverage on benchmarks/ (default temp dir)
.venv\Scripts\python -m pytest tests/test_benchrunner.py -m "not slow and not gpu" --cov=benchmarks --cov-report=term-missing
                                                                               # 49 passed, 1 deselected; benchmarks/ 98%

# Dependency manifest diff
git diff a5b0794..dfa3a1e -- pyproject.toml Cargo.toml Cargo.lock              # empty — no dependency changes
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Scope delivered.** The S1 commit (`dfa3a1e`) adds:

- `benchmarks/_common/` (5 modules: config, environment, timing, registry, result)
- `benchmarks/benchrunner/` (CLI: `__main__.py`)
- 9 category packages with 10 registered benchmarks (scaling has 2)
- `tests/test_benchrunner.py` (50 tests: 49 fast + 1 slow)
- `DOCS/baselines/wp033_benchmark_traceability.md` (58-row traceability table)
- READMEs for `benchmarks/`, every category, `_common/`, `benchrunner/`, `results/`

**58-vs-62 script count.** The session brief says 62; S1 verified 58 `.py` scripts in the archive via `Get-ChildItem -Filter *.py`. The traceability doc gives every one of the 58 a row (56 migrated, 2 deferred as non-benchmark tooling). This is a factual correction, not a unilateral plan amendment — correctly flagged for S2/maintainer disposition. The 2 deferred scripts (`y4q2_benchmarks.py`, `y4q4_benchmarks.py`) are genuinely non-benchmark release/reporting tooling (their `def` listings contain no timed measurement).

**No undeclared scope shipped.** `git diff --stat` confirms all 47 changed files are within `benchmarks/`, `tests/`, and `DOCS/` (baselines, experiments, handoff note). No `python/prin`, `crates/`, or CI workflow changes.

### 3.2 A2 — Plan/architecture conformance

**No numerics in Python.** Every category module delegates to already-parity-dispositioned Rust APIs:

- `scaling`/`chimera`/`integrators`: `prin.dynamics`/`prin.metrics` (Kuramoto/RK4/RK45/exponential/multi-rate/order-parameter/chimera-index)
- `mot`/`adversarial`: `prin.experiments.adversarial_evaluate_*` (WP-031/WP-032 parity-dispositioned)
- `ablations`: `prin.nn.ablation` bridges (WP-026 parity-dispositioned)
- `training`: `prin.train.train_phase_tracker` (WP-027 parity-dispositioned)
- `daemon`: `prin.daemon.SubconsciousDaemon` (WP-029/WP-032 parity-dispositioned)
- `kernels`: subprocess orchestration of `crates/prin-kernels/benches/*.rs` criterion output (no Python measurement)

The only Python-side arithmetic is measurement-harness plumbing in `timing.py` (nearest-rank percentile, median over a sample list) — the same class of code as the already-accepted `tools/wp029_control_buffer_pilot.py::_percentile` helper, not a scientific-model primitive.

**Crate layering preserved.** No changes to `crates/`, `python/prin/`, `pyproject.toml`, `Cargo.toml`, or `Cargo.lock`.

**Deterministic Seed flow preserved.** Every category module constructs `Seed(config.seed_counter, config.seed_key)` from the shared config; no hidden RNG.

### 3.3 A3 — Tests in tandem + coverage

**50 tests in `tests/test_benchrunner.py`** covering:

| Test class | Count | What it covers |
|---|---|---|
| `TestBenchmarkConfig` | 3 | Config validation, minimum iterations, negative warmup |
| `TestTimedRun` | 4 | ≥10-iteration rule, warmup exclusion, median/p95 correctness |
| `TestRegistry` | 5 | All 9 categories registered, unknown category/name errors, duplicate rejection |
| `TestCaptureEnvironment` | 3 | Required fields, backend/dtype/seed roundtrip, seed=None |
| `TestWriteResult` | 3 | Writes inside allowed roots, reserved-key collision, path confinement |
| `TestSchemaCompatibility` | 3 | Legacy field names for scaling/chimera/adversarial |
| `TestBenchrunnerCli` | 7 | --list, error paths, end-to-end JSON write, output confinement |
| `TestKernelCriterionBridgeParsing` | 8 | Estimates parsing, cargo arg shape, error paths, faked suite |
| `TestRemainingCategories` | 7 | One test per remaining category (mot, ablations, integrators, training, daemon + daemon error) |
| `TestCaptureEnvironmentFallbacks` | 6 | Missing executables, subprocess failure, nonzero exit, missing package, GPU info edge cases |
| `TestKernelCriterionBridgeSlow` | 1 | Real `cargo bench` end-to-end proof (slow-marked) |

**Coverage: 98% on `benchmarks/`** (607 statements, 10 miss). Missed lines:
- `scaling/coupling_complexity.py:39` — unreachable `ValueError` guard in coupling-mode dispatch (defensive; cannot be reached through the public API since `_MODES` is a closed tuple)
- `benchrunner/__main__.py:127-129` — the "no benchmarks registered for category" error branch (tested via monkeypatch in `test_category_with_no_registered_benchmarks_is_an_error`, but coverage attributes it to the CLI module's line range)
- `result.py:33, 69-79` — the `OutputPathError` raise and `write_result` body are only reached via the `tmp_path`-using tests; these show as missed under `--basetemp=.pytest_basetemp` but are covered under the default temp dir

**≥95% changed-code gate: SATISFIED** (98% ≥ 95%).

**WP033-F1 — 2 tests fail under `--basetemp=.pytest_basetemp`.** See §4.

### 3.4 A4 — Numerical parity + invariants

**No new numerical primitive introduced.** The parity-evidence disposition in the S1 handoff note is accurate:

- Every category module calls already-parity-dispositioned Rust APIs (verified by import inspection).
- `kernels/` republishes criterion output; measures nothing itself.
- `ablations/` uses `rust_state_dict()` byte length instead of `module.parameters()` (correctly justified: gradients flow through a custom `torch.autograd.Function`, not `torch.nn.Parameter` registration — `sum(p.numel() for p in PhaseTracker(4).parameters())` is `0`).

**JSON schema compatibility tested.** `TestSchemaCompatibility` asserts legacy field names (`N`/`wall_time_s`/`throughput`/`final_order_param` for scaling; `coupling_strength`/`order_parameter`/`chimera_index` for chimera; `clean_identity_preservation`/`adversarial_identity_preservation`/`degradation` for adversarial).

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | exit 0 (no Rust source changed) |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `ruff check benchmarks/ tests/test_benchrunner.py` | All checks passed! |
| `ruff format --check benchmarks/ tests/test_benchrunner.py` | 42 files already formatted |
| `mypy python/prin --strict` | 0 issues (unchanged — `benchmarks/` is outside governed mypy scope, consistent with pre-existing policy) |

### 3.6 A6 — Security

| Check | Result |
|---|---|
| `shell=True` in `benchmarks/` | None found |
| `cargo audit` | exit 0; 2 allowed warnings (DV-008 `paste` RUSTSEC-2024-0436, DV-017 `bincode` RUSTSEC-2025-0141 — unchanged) |
| `pip-audit .` | No known vulnerabilities found |
| `bandit -r . -c pyproject.toml` | 2 pre-existing Low in `EVIDENCE/math-audit/` (not this WP); `benchmarks/` excluded per `pyproject.toml` |
| New dependencies | None (`git diff` on `pyproject.toml`/`Cargo.toml`/`Cargo.lock` is empty) |
| `unsafe` (Rust) | No Rust source changed |
| Output-path confinement | `_validate_output_path()` in `result.py` resolves paths and checks against 3 allowed roots; `OutputPathError` on escape |
| Subprocess construction | `criterion_bridge.py`: absolute cargo path via `shutil.which`, argument list, `check=False` + explicit exit-code handling; `environment.py`: same pattern |
| Snyk Code | S1 reports 0 issues on `benchmarks/` and `tests/test_benchrunner.py` |

### 3.7 A7 — Docstring/doc coverage

- `python/prin` interrogate: **100.0%** (266/266) — unaffected by this WP.
- `benchmarks/` interrogate: 75.0% — outside the governed scope (`interrogate -c pyproject.toml python/prin`), consistent with pre-existing project policy (same carve-out as `mypy` and `bandit`).
- Every `benchmarks/` module has a module-level docstring explaining its purpose, Rust-backed API, and legacy predecessor.
- Every category has its own README.
- All public functions/classes in `_common/` have docstrings with Args/Returns/Raises sections.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/HACK/XXX/STUB scan:** 0 matches in `benchmarks/`.
- **`__all__` consistency:** All 9 category packages + `_common/` define `__all__` listing their public modules/symbols.
- **No orphan files:** Every new file is referenced by a README, `__init__.py`, or the traceability doc.
- **`.gitignore` respected:** `benchmarks/results/` has a README but no committed result files (correctly empty for future campaign use).

### 3.9 A9 — CI status

Per the Push and CI cadence (Development Workflow and Audit Standards §3), nothing has been pushed this cycle; A9 is verified by local gate reproduction. All locally reproduced gates are green (see §2).

### 3.10 A10 — Artefact trail

- PSR-032 (`DOCS/reports/032-project-state.md`) committed and consistent.
- S1 handoff note (`DOCS/experiments/0129-wp033-s1-handoff.md`) committed with full acceptance-criterion evidence map.
- Traceability doc (`DOCS/baselines/wp033_benchmark_traceability.md`) committed with all 58 legacy scripts mapped.
- Category READMEs, `benchmarks/README.md`, `benchmarks/results/README.md` all committed.
- Deviation ledger in PSR-032 is up to date (no WP-033 entries yet — this audit adds the first).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP033-F1 | D2 | `tests/test_benchrunner.py:167,309`; `benchmarks/_common/result.py:21-26` | Two tests (`test_writes_inside_results_dir`, `test_runs_one_named_benchmark_and_writes_json`) fail when pytest is invoked with `--basetemp=.pytest_basetemp` (the project's AGENTS.md-documented Windows workaround). `_ALLOWED_ROOTS` includes `benchmarks/results/`, `DOCS/test_and_benchmark_results/`, and `tempfile.gettempdir()` — but `.pytest_basetemp` resolves inside the repo root, outside all three. The full test suite (624 tests) fails under this invocation (2 failures). Pass with default system temp dir. | Coding Standards §5 (local gate must pass); Testing Standards §1 (tests must be reliable) | In the two affected tests, monkeypatch `_ALLOWED_ROOTS` to include the pytest basetemp root, or write to a path under one of the existing allowed roots (e.g. `benchmarks/results/` with cleanup, or explicitly add `Path(tempfile.gettempdir())` as a parent check that also covers in-repo basetemp). |

## 5. Deviation-ledger delta

**New findings:** WP033-F1 (D2).

**Carried findings re-inspected:** None — no unresolved findings were carried into WP-033 (PSR-032 confirms all prior findings are FIXED or AMENDED).

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

One D2 finding (WP033-F1): two tests fail under the project's documented Windows pytest invocation. The implementation is otherwise clean — all acceptance criteria are evidence-mapped, no new numerics, no security issues, no dependency changes, 98% coverage, all quality gates green.

**S3 ordered work list:**

1. **WP033-F1 (D2):** Fix the two failing tests so they pass under both the default system temp dir and `--basetemp=.pytest_basetemp`. Add a regression assertion that the full fast suite passes under both invocations.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP033-F1 | FIXED | `6eb4e8b` | Both affected tests pass with the default pytest temp root and `--basetemp=.pytest_basetemp`; the full fast suite passes under the governed in-repository basetemp. Production `_ALLOWED_ROOTS` is unchanged. |

### Delta re-audit

Session 0131 changed only the two tests identified by WP033-F1. Each test now
monkeypatches `_ALLOWED_ROOTS` to its own resolved `tmp_path`, making the test's
write root explicit without broadening the production writer's confinement
policy.

| Check | Result |
|---|---|
| A1 — scope | PASS — only WP033-F1's two affected tests changed; no feature or production-source change |
| A2/A4 — architecture and parity | PASS — no numerical or production implementation changed |
| A3 — tests and coverage | PASS — targeted tests pass in both temp modes; WP suite 49 passed / 1 slow deselected; `benchmarks/` 99% line coverage |
| A5 — quality | PASS — Ruff check/format, mypy strict, interrogate, cargo fmt, clippy, and rustdoc gates clean |
| A6 — security | PASS — production output confinement unchanged; Snyk Code 0 issues on the modified test; native audits clean at governed thresholds |
| A7/A8 — documentation and hygiene | PASS — 100% governed Python docstring coverage; `git diff --check` clean; no generated result artefacts tracked |
| A9 — local regression gate | PASS — 624 passed / 9 deselected under `--basetemp=.pytest_basetemp`; full Python/parity suite 1225 passed; all `cargo test --workspace` binaries and doctests passed (one established expensive test ignored) |
| A10 — artefact trail | PASS — finding-specific commit, closure table, session brief, and session-register status recorded |

**Independent S3 verification (2026-08-26, Windows 11 / Rust 1.92.0 / Python
3.14.0):**

```powershell
.venv\Scripts\python -m pytest tests/test_benchrunner.py::TestWriteResult::test_writes_inside_results_dir tests/test_benchrunner.py::TestBenchrunnerCli::test_runs_one_named_benchmark_and_writes_json --basetemp=.pytest_basetemp -q  # 2 passed
.venv\Scripts\python -m pytest tests/test_benchrunner.py::TestWriteResult::test_writes_inside_results_dir tests/test_benchrunner.py::TestBenchrunnerCli::test_runs_one_named_benchmark_and_writes_json -q  # 2 passed
.venv\Scripts\python -m pytest tests/test_benchrunner.py -m "not slow and not gpu" --cov=benchmarks --cov-report=term-missing --basetemp=.pytest_basetemp -q  # 49 passed, 1 deselected; 99%
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 624 passed, 9 deselected; 99%
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-full -q  # 1225 passed; 99%
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 119 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 28 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (266/266)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml               # 0 issues
cargo fmt --all -- --check                                                     # clean
$env:CARGO_INCREMENTAL='0'; cargo clippy --workspace --all-targets -- -D warnings  # clean
cargo test --workspace                                                        # all binaries/doctests passed; 1 established expensive test ignored
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps               # clean
cargo audit                                                                    # exit 0; DV-008/DV-017 allowed warnings only
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python tools/wp001_baseline.py check                            # passed
.venv\Scripts\python tools/check_dv_register_gates.py                         # passed; 29 rows / 198 sessions
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build_s3_0131/html  # fresh output; 0 warnings
```

The defense-in-depth whole-repository Bandit scan also found only the two
pre-existing Low-severity `assert` uses in
`EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`; neither file nor
finding is attributable to WP033-F1. No dependency manifest changed, so no
change-attributable Snyk Open Source scan was required. Snyk Code scanned
`tests/test_benchrunner.py` at the Low threshold and returned 0 issues.

The WP acceptance evidence remains intact: all 58 verified legacy scripts retain
traceability rows, all registered replacements execute in the WP suite, schema
compatibility tests pass, and the minimum-ten-iteration tests pass. No final
measurements or scientific conclusions were produced.

**Delta re-audit date:** 2026-08-26 — **Result: CLEAN. WP033-F1 closed; no newly introduced deviation.**

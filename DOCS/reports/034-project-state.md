# PRIN Project State Report — Cycle 034

**Date:** 2026-08-27
**Cycle:** 034 (WP-034 "Reporting, figures, tables, and profiling")
**Completed sessions:** 0133–0136
**Author:** Claude Code (AI pair), approved by maintainer MichaelMaillet
**Git state:** `main` @ S4 closure (predecessor `cd844b0`; this session's commit follows)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**2 of 6**
  phase-6 WPs complete: WP-033, WP-034).
- **This cycle delivered:**
  - **`prin.reporting` publication surface** — near-verbatim ports of the
    PRINet 3.0 `utils/{benchmark_reporting,figure_generation,table_generation,
    profiler}.py` tools, rebuilt with typed public-boundary errors,
    deterministic output, and output-path confinement:
    - `benchmark_reporting.py` (565 lines): `generate_benchmark_report`,
      `generate_leaderboard`, `generate_scalr_metrics_report` — deterministic
      Markdown from stored benchmark JSON; the 3.0 implicit `datetime.now()`
      timestamp is replaced by a caller-supplied `generated_at` normalized to
      UTC minute precision, so unchanged inputs produce byte-stable output.
    - `figure_generation.py` (1 139 lines): **14** stored-artefact figure
      generators (historical `fig2`–`fig15`), the headless 300-DPI NeurIPS
      style, `generate_all_figures`, and `normalize_matplotlib_output` for
      deterministic PDF/PNG byte comparison.
    - `table_generation.py` (810 lines): **11** byte-comparable LaTeX fragment
      generators and `generate_all_tables`; every fragment regenerates
      bytes-identical to its stored `paper/tables/` counterpart.
    - `profiler.py` (516 lines): `PRINetProfiler` (typed `torch.profiler`
      wrapper), the legacy `ProfileReport` shape/trace name,
      `profile_training_loop`, and `record_function(label)` as the explicit
      boundary that surfaces Rust-backed operations in torch traces. No model
      numerics; RNG state is never mutated.
    - `_artifacts.py` (147 lines): internal shared module — the single home
      for stored-artefact JSON loading/schema validation and the typed
      `ReportingError` hierarchy.
  - **Test suite** (`tests/test_reporting_profiler.py` 59 tests +
    `tests/test_publication_generation.py` 13 tests): 72 tests; `prin.reporting`
    99% line coverage (1 053 statements, 13 miss). Covers report/leaderboard/
    SCALR determinism, schema and output-confinement errors, profiler
    lifecycle/state validation, Rust-call labels, Chrome-trace export, all 14
    figure generators, all 11 table generators, exact LaTeX bytes, and
    deterministic normalized PDF/PNG.
  - **S1 handoff** (`DOCS/experiments/0133-wp034-s1-handoff.md`): full
    acceptance-criterion evidence map and parity-evidence disposition (no
    numerical primitive introduced; stored-artefact byte comparison and
    deterministic normalization are the applicable golden evidence).
  - **S2 audit** (`DOCS/audits/034-wp034-audit.md`): verdict
    `PASS-WITH-FINDINGS`, four D4 findings (WP034-F1..F4).
  - **S3 remediation:** WP034-F2/F3/F4 FIXED (`11a97cb`, `8dbf55d`); delta
    re-audit CLEAN. WP034-F1 (documentation-only figure-count correction)
    carried to S4 as the single permitted D4 carry.
  - **S4 documentation:** `prin.reporting`/`tests/` READMEs expanded;
    `DOCS/audits/README.md` (034 entry + backfilled 033 entry),
    `DOCS/reports/README.md`, `DOCS/sessions/SESSION_REGISTER.md`,
    `DOCS/sessions/phase-6/README.md` updated; `CHANGELOG.md` WP-034 entry;
    `DOCS/sphinx/migration_guide.rst` WP-034 module-mapping section;
    this report; WP-035 declared (§6).
- **WP034-F1 figure-count correction (D4):** the WP-034 session briefs (and
  the already-written WP-035 brief) quote "15 figures". The verified PRINet 3.0
  reference — `utils/figure_generation.py` and the stored `paper/figures/`
  tree — contains **14** generated figures, numbered `fig2`–`fig15`; no `fig1`
  implementation or stored output has ever existed. PRIN ports all 14
  verifiable generators. This is a factual correction to brief text, not a
  plan amendment and not a dropped deliverable; it mirrors the WP-033
  62-vs-58 legacy-script correction. The WP-035 brief text is left unedited
  (a future cycle's artefact); its S1 must read "15 figures" as 14.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#30
  remain in force; no new Plan-text amendment was required this cycle.
- **Audit:** `DOCS/audits/034-wp034-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS` (4 D4 findings). S3 FIXED WP034-F2/F3/F4, delta
  re-audit CLEAN; WP034-F1 closed in this S4. No unresolved D1/D2 finding
  exists.
- **Session Register:** 0133 (S1), 0134 (S2), 0135 (S3), 0136 (S4) all marked
  **COMPLETE**; 0137 (WP-035 S1) is the registered successor, present in
  `SESSION_REGISTER.md`/`DOCS/sessions/phase-6/` as `PLANNED`.

---

## 2. Metric trends

| Metric | Previous (PSR-033) | Current (PSR-034) | Gate |
|---|---|---|---|
| Rust tests passing | ~1563/~1563 default workspace (excluding `prin-py`), 0 failed, 1 ignored | **1447 passed across 48 test binaries, 0 failed, 1 ignored** (`cargo test --workspace --quiet`, which collapses the per-doctest summary lines the prior figure counted); unchanged in substance — WP-034 touches no `crates/` file, adds no Rust code, and changes no `Cargo.*` manifest | 100% where defined |
| Python tests passing | 624 passed, 9 deselected (fast suite); full suite 1225 passed | **696 passed**, 9 deselected (fast suite, `-m "not slow and not gpu"`); full suite (`tests/` + `parity/`) **1297 passed** (+72 from WP-034's `test_reporting_profiler.py`/`test_publication_generation.py`) | 100% |
| Coverage (changed code) | `benchmarks/` 99% lines | `prin.reporting` **99%** lines (1 053 stmts, 13 miss); missed lines are defensive error-path branches unreachable through the public API | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (266/266) | **95.6%** overall (351/367), PASS at ≥95%; all public functions/classes have Google-style docstrings; the misses are private helpers (`_save_fig`, `_row`, `_col`, `_load_json`, `_dirs`, …) without standalone docstrings | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; 15 `prin-train` golden-value + 1 statistical; 10 `prin-daemon` bit-exact; 82 differential | Unchanged — WP-034 introduces **no numerical primitive**. Its applicable golden evidence is stored-artefact byte comparison (11 LaTeX fragments regenerate byte-identical) and deterministic PDF/PNG normalization (stable across repeated generation) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 across all gates; `cargo audit` exit 0 with 2 allowed warnings | 0 across all gates; `cargo audit` exit 0 with **2 allowed warnings** (DV-008 `paste`, DV-017 `bincode` — unchanged); `pip-audit` clean (project + `DOCS/sphinx/requirements.txt`); `bandit -r python/prin/reporting` 0 issues | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (fresh-directory build; `api/reporting.rst` renders the expanded module) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code: S1 ran clean scans; CI authoritative | Snyk Code: S1 reported 0 issues on all changed files (Low threshold); S3 re-confirmed 0 on `python/prin/reporting/`. No dependency manifest changed, so Snyk Open Source is not applicable. CI's Snyk job remains authoritative | 0 at gate threshold |
| Benchmark regression gates | none tripped | none tripped (no benchmark code changed) | none tripped |

**Verification commands re-run in S4 (2026-08-27, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0):**

```
cargo fmt --all -- --check                                                    # clean (exit 0)
cargo clippy --workspace --all-targets -- -D warnings                         # clean (exit 0)
cargo test --workspace --quiet                                                # exit 0; 1447 passed / 0 failed / 1 ignored across 48 binaries
cargo audit                                                                   # exit 0; DV-008/DV-017 allowed warnings only
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 126 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 33 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 95.6% (351/367), PASS
.venv\Scripts\python -m bandit -r python/prin/reporting -c pyproject.toml     # 0 issues
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python -m doctest python/prin/reporting/_artifacts.py python/prin/reporting/figure_generation.py python/prin/reporting/table_generation.py   # exit 0
.venv\Scripts\python -m pytest tests/test_reporting_profiler.py tests/test_publication_generation.py --cov=prin.reporting --basetemp=.pytest_basetemp-wp034s4 -q   # 72 passed; prin.reporting 99%
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp-full -q   # 696 passed, 9 deselected
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full2 -q                    # 1297 passed
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/033-project-state.md DOCS/reports/034-project-state.md   # passed; 113 vs 117 rows
.venv\Scripts\python tools/check_dv_register_gates.py                         # 29 rows / 198 sessions, passed
.venv\Scripts\python tools/wp001_baseline.py check                            # passed
Sphinx clean-dir build -W --keep-going -b html                                # 0 warnings
```

---

## 3. Deviation ledger (cumulative)

Four new findings this cycle, all D4: WP034-F1 (session-brief figure-count
discrepancy, documentation correction closed in this S4), WP034-F2 (bare
`ValueError` in `normalize_matplotlib_output`, FIXED `11a97cb`), WP034-F3
(inconsistent reporting error hierarchy, FIXED `8dbf55d`), WP034-F4 (private
cross-module import between `table_generation` and `figure_generation`, FIXED
`8dbf55d`). The cumulative table below carries forward every row from
`DOCS/reports/033-project-state.md` §3 unchanged (verified by
`tools/check_deviation_ledger.py`, run in two-report mode against this report)
and appends the four WP034 rows.

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| WP001-F1 | 001 | D1 | PyO3 dependency carried two RustSec advisories | FIXED | `13eac9e`; PyO3/rust-numpy 0.29.0 |
| WP001-F2 | 001 | D1 | `python.yml` did not audit all dependencies and suppressed failures | FIXED | `510e0c9`; project/docs Pip Audit gating |
| WP001-F3 | 001 | D1 | Long-lived crates.io token in `release.yml` | FIXED | `510e0c9`; pre-WP-005 guard |
| WP001-F4 | 001 | D2 | Traceability check was fail-open on symbol count | FIXED | `510e0c9`; exact 657 contract + mutation test |
| WP001-F5 | 001 | D2 | Duplicate session brief IDs could pass validation | FIXED | `510e0c9`; duplicate-ID regression test |
| WP001-F6 | 001 | D2 | Repro CI path was not explicitly guarded | FIXED | `510e0c9`; pre-WP-035 guard |
| WP001-F7 | 001 | D2 | Unready workspace crate publication was possible | FIXED | `510e0c9`; publication guard |
| WP001-F8 | 001 | D1 | GitHub secret scanning/push protection unavailable | AMENDED | Plan amendment #5; Gitleaks + branch-protection substitute |
| WP001-F9 | 001 | D4 | Sphinx had two warnings and a misattribution | FIXED | `510e0c9`; warning-free wheel-backed build |
| WP001-F10 | 001 | D2 | `main` was unprotected | FIXED | Hosted setting, 2026-08-06 |
| WP001-F11 | 001 | D2 | Linux Python/Repro jobs did not create explicit venvs | FIXED | `510e0c9`; explicit venvs in `python.yml`/`repro.yml` |
| WP002-F1 | 002 | D2 | Fast `tests/` suite was below 95% coverage on `prin.parity` | FIXED | `c7d8a25`; fast-suite regression tests, `prin.parity` 100% |
| WP002-F2 | 002 | D2 | Snyk Open Source reported 12 docs-dependency advisories | FIXED | `d6037b8`; pinned transitive minimums, Snyk/pip-audit 0 |
| WP002-F3 | 002 | D4 | Stale docstrings/PyPI references for `prin.parity` | FIXED | `d0b7207`; docstring, README, markers updated |
| WP002-F4 | 002 | D4 | `bandit -r parity/` flagged test `assert` | FIXED | `4da34da`; `parity/` and archive in `bandit` exclusions |
| WP003-F1 | 003 | D2 | `unsafe` in `prin-py` outside the `prin-kernels` exception | AMENDED | Plan amendment #6; Coding Standards §2.1/§6.1 Python-FFI exception |
| WP003-F2 | 003 | D2 | Missing shape-dimension sign validation before `std::slice::from_raw_parts` | FIXED | `b481078`; `BridgeError::NegativeDim`, `validate_shape`, Rust + Python regression tests |
| WP003-F3 | 003 | D2 | WP-003/Phase 0 go/no-go amendment not recorded | AMENDED | Plan amendment #7; CPU path validated, CUDA + `<5%` deferred to Phase 4 |
| WP003-F4 | 003 | D4 | Package docstring omits the new `prin.dlpack` module | FIXED | `b481078`; `python/prin/__init__.py` updated |
| WP003-F5 | 003 | D4 | `python/prin/dlpack.py` lacks `__all__` | FIXED | `b481078`; `__all__` added, ruff + baseline check pass |
| WP004-F1 | 004 | D2 | `paste` RUSTSEC-2024-0436 inherited from `cubecl` 0.10.0 | AMENDED | Plan amendment #9; re-check every cycle, upgrade when fixed upstream |
| WP004-F2 | 004 | D2 | `cargo-llvm-cov` line coverage 86.36% due to non-instrumentable `#[cube(launch)]` bodies | AMENDED | Plan amendment #10; instrumentable code ≥95%, kernel equivalence validates correctness |
| WP004-F3 | 004 | D2 | Missing `proptest` invariants for `step_cpu` | FIXED | Added proptest module + deterministic RK4 scaling test; `cargo test -p prin-kernels --features wgpu,cpu` passes 21 tests |
| WP004-F4 | 004 | D2 | `prin-kernels` crate-level unsafe lint relaxed without plan amendment | AMENDED | Plan amendment #8; `#![deny(unsafe_code)]` + module `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, `// SAFETY:` justifications |
| WP004-F5 | 004 | D3 | Direct same-hardware Triton 3.0 fused-kernel comparison blocked on Windows Python 3.14 | AMENDED | Plan amendment #11; PyTorch reference + wgpu/CPU equivalence validated, Triton timing deferred to Phase 3 / `gpu.yml` |
| WP004-F6 | 004 | D3 | `try_step_wgpu`/`try_step_cuda` could panic on missing backend | FIXED | `catch_unwind` + `MeanFieldRk4Error::BackendUnavailable` + regression test |
| WP004-F7 | 004 | D3 | Default CI did not run `cpu`/`wgpu` kernel-equivalence tests | FIXED + AMENDED | `rust.yml` runs `--features cpu`; `wgpu` deferred to headless GPU runner (amendment #12) |
| WP004-F8 | 004 | D3 | `StepReport.wall_time_seconds` used host wall-clock, not device events | FIXED | Documented prototype caveat in rustdoc; device-event timing is Phase 3 |
| WP004-F9 | 004 | D4 | Stale log message and READMEs omit `cpu`/WP-004 spike | FIXED | Corrected log label, updated `crates/prin-kernels/README.md` and `crates/README.md` |
| WP005-F1 | 005 | D3 | ORT go/no-go not recorded as plan amendment #13; gate check did not validate plan text | FIXED | Plan amendment #13; commit `fe5dc8b`; `_check_spike_decisions` requires `\| 13 \|` and ORT/ONNX/VitisAI in plan text; regression `test_missing_ort_amendment_in_plan` |
| WP005-F2 | 005 | D3 | Real ORT model probe only exercised on one CI matrix cell | FIXED | Commit `82db761`; `python.yml` installs `-e ".[dev,onnx]"` on every test matrix cell |
| WP005-F3 | 005 | D4 | `models/README.md` did not describe the split ONNX model files | FIXED | Commit `b5fc211`; README describes both `.onnx` and `.onnx.data` files and gitignore exemption |
| WP005-F4 | 005 | D4 | `tools/README.md` did not list the WP-005 CLI tools | FIXED | Commit `39cef38`; README lists `wp005_ort_probe.py` and `wp005_phase0_gate.py` |
| WP006-F1 | 006 | D2 | `Seed::next_f64_range` half-open interval contract rounding to upper bound `hi` | FIXED | Commit `4f80491`; `Seed::next_f64_range` returns `Result<f64, SeedError>`, validates `lo < hi` and finiteness, uses scale-decrease loop so max draw cannot round to `hi`, added regression tests |
| WP006-F2 | 006 | D3 | `strict-checks` feature not exercised in `.github/workflows/rust.yml` CI | FIXED | Commit `5f78c3e`; added `clippy-strict` and `test-strict` jobs to `rust.yml` |
| WP006-F3 | 006 | D4 | Post-S1 baseline tool hardening commit `9153c7c` outside declared S1 range | FIXED | Commit `9153c7c`; recorded as retroactive WP-001 hotfix; disposition confirmed on branch for S4 consolidation; `tools/wp001_baseline.py check` passes |
| WP007-F1 | 007 | D2 | Coupled Stuart–Landau and Hopf derivative outputs not asserted against closed-form/PRINet reference values | FIXED | Commit `d030fff`; added `test_stuart_landau_coupled_reference_values` and `test_hopf_coupled_reference_values` unit tests for Full/MeanField/SparseKnn modes |
| WP007-F2 | 007 | D2 | No committed Rust-vs-PRINet derivative parity test for the new `Dynamics` implementation | FIXED | Commit `d030fff`; added `crates/prin-dynamics/tests/parity_models.rs` with 9 parity cases covering all models and coupling modes |
| WP007-F3 | 007 | D3 | Rust f64 implementations diverge from PRINet 3.0 reference due to PRINet's internal `torch.complex64` (f32) arithmetic; not listed among preserved numerical hazards | AMENDED | Plan amendment #14; preserved numerical hazard documented in Project Plan §5 and `DOCS/sphinx/parity_report.rst`; `1e-6` derivative parity tolerance for affected paths |
| WP007-F4 | 007 | D4 | `EVIDENCE/0017-wp005-s1-ort-probe.json` had uncommitted timestamp drift and CRLF→LF warning | FIXED | Restored committed version; `git status` clean against `HEAD` |
| WP007-F5 | 007 | D4 | Stuart–Landau and Hopf rustdoc did not spell out per-`CouplingMode` coupling-term formulas | FIXED | Commit `d030fff`; expanded rustdoc with explicit `C_i` (SL) and `C_i^sin`/`C_i^cos` (Hopf) per-mode formulas |
| WP008-F1 | 008 | D2 | FSAL cache in `RK45Integrator::integrate_adaptive` not invalidated at start of new integration; reuse across calls produces silently incorrect results | FIXED | Commit `f97ba5c`; added `fsal_valid: bool` flag invalidated on entry/rejected steps; regression test `rk45_fsal_cache_invalidated_on_reuse` |
| WP008-F2 | 008 | D3 | `IntegrateError::NonFiniteValue` error path (strict-checks) not exercised by any test | FIXED | Commit `f97ba5c`; added `NanDynamics` test helper + `strict_check_non_finite_value_error`/`strict_check_non_finite_value_rk4` tests; coverage 96.66% → 97.48% |
| WP008-F3 | 008 | D4 | `check_finite` doc comment inaccurate about non-strict NaN repair behavior | FIXED | Commit `b4749ba`; corrected doc comment to state amplitude-only repair in non-strict mode |
| WP008-F4 | 008 | D4 | `lib.rs` module doc listed exponential/Krylov/multi-rate integrators (WP-008 non-goals) | FIXED | Commit `b4749ba`; updated to list only Euler, RK4, adaptive RK45/Dormand–Prince |
| WP008-F5 | 008 | D4 | `RK45Integrator::new` reused `InvalidTimestep` for tolerance validation; test only checked `is_err()` | FIXED | Commit `b4749ba`; added `IntegrateError::InvalidTolerance { param, value }` variant; updated test to assert specific variant |
| WP009-F1 | 009 | D2 | `cargo fmt --check` fails on `coupling.rs:339` test comment indentation | FIXED | Commit `b4749ba`; restructured `topology_ring_basic` trailing comment; `cargo fmt --check` exit 0 |
| WP009-F2 | 009 | D2 | `normalization_one_over_k_explicit_in_sparse` only asserts `is_finite()` — does not verify the 1/k normalization | FIXED | Commit `b4749ba`; strengthened to assert explicit `K/k` per-edge weight + shared-neighbour 3/2 ratio check |
| WP009-F3 | 009 | D3 | `build_ring`/`build_small_world` odd-clamp normalization violates `K/degree` energy invariant | FIXED | Commit `b4749ba`; new `clamp_ring_k` helper clamps to largest even `≤ n-1`; regression tests for both builders |
| WP009-F4 | 009 | D3 | `with_clamp` does not validate `amp_min <= amp_max` or finiteness — `f64::clamp` panics on inverted range | FIXED | Commit `b4749ba`; added `PacError::InvalidClampRange` variant + finiteness/ordering validation + regression tests |
| WP009-F5 | 009 | D4 | S1 handoff note factual errors (pac.rs stub→full, rayon sort, test count 198) | FIXED | Commit `bf46cee`; handoff note corrected |
| WP009-F6 | 009 | D4 | `topology_ring_clamps_k_to_n_minus_1` test comment inaccurate; no weight assertion | FIXED | Commit `b4749ba`; comment corrected + degree/weight/energy assertions added |
| WP009-F7 | 009 | D4 | `build_small_world` rewiring is directed; module docs don't clarify | FIXED | Commit `b4749ba`; directed interpretation documented in rustdoc + `Topology::SmallWorld` variant doc |
| WP010-F1 | 010 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP011-F1 | 011 | D4 | `#![allow(unsafe_code)]` unnecessary in `state.rs` — no `unsafe` code exists | FIXED | Commit `cd20b1a`; attribute removed; `cargo clippy -D warnings` clean under crate-level `#![deny(unsafe_code)]` |
| WP012-F1 | 012 | D1 | S1 commit omitted the declared `prin-py` Python bindings for `ExponentialIntegrator`/`MultiRateIntegrator` | FIXED | `62deb43`; `PyExponentialIntegrator`/`PyMultiRateIntegrator`, `dynamics.py` re-exports, `.pyi` stubs, 21 new Python acceptance tests |
| WP012-F2 | 012 | D1 | No Rust-vs-PRINet 3.0 parity evidence for the new integrators | FIXED | `e4e7772`; 7 new golden-trajectory parity tests (4 Exponential, 3 MultiRate) in `parity_integrators.rs` |
| WP012-F3 | 012 | D1 | `matrix_exp` silently returned identity on a singular Padé LU denominator instead of a typed error | FIXED | `2dc641e`; `matrix_exp`/`phi1_matrix`/Krylov solves propagate `IntegrateError::LinearSolveFailed`; regression test `matrix_exp_singular_denominator_returns_typed_error` |
| WP012-F4 | 012 | D3 | WP-012 text implied band-aware multi-rate scheduling; implementation is uniform sub-stepping (matches PRINet 3.0 reference) | AMENDED | Plan amendment #18; Project Plan §6 WP-012 declaration clarified; `MultiRateIntegrator` rustdoc corrected in S4 to match |
| WP012-F5 | 012 | D4 | `ExponentialIntegrator::step`/`::integrate` did not validate the stored `dim` against the state size | FIXED | `2dc641e`; `IntegrateError::InvalidDim` on mismatch; regression tests `exp_integrator_dim_mismatch_returns_typed_error`, `exp_integrator_integrate_dim_mismatch_returns_typed_error` |
| WP013-F1 | 013 | D1 | No Rust-vs-PRINet 3.0 parity tests for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator` | FIXED | `d2c1f1c`; 12 cases in `parity_bands.rs` + 6 in `parity_temporal.rs`, all green at documented tolerances |
| WP013-F2 | 013 | D2 | `BandNetwork` hard-coded mean-field intra-band coupling; PRINet 3.0 reference uses `sparse_knn` with per-band `MultiRateIntegrator` sub-stepping | FIXED + AMENDED | `20673c4`; plan amendment #19 (`5e0c602`); per-band `CouplingMode` dispatch via `BandParams::with_coupling`; residual composition difference (continuous ODE vs. stepper) governed by amendment #19 with parity evidence |
| WP013-F3 | 013 | D3 | No S1 handoff note / acceptance-criterion evidence map was committed | FIXED | `62843d4`; `DOCS/experiments/0049-wp013-s1-handoff.md` maps all twelve acceptance criteria to evidence |
| WP013-F4 | 013 | D4 | Function coverage below 95% on `bands.rs` (92.00%) and `temporal.rs` (94.64%) | FIXED | `20673c4`, `62843d4`; `bands.rs` 98.68% functions, `temporal.rs` 100% functions |
| WP013-F5 | 013 | D4 | `BandNetwork::new` returned `EmptyBand { band: 0 }` for an empty band list; non-adjacent PAC pairs allowed despite "adjacent" docstring | FIXED | `20673c4`; `BandError::NoBands` added; `PacPair` rustdoc/docstring corrected — any strictly slow→fast pair is intentional |
| WP013-F6 | 013 | D4 | `TemporalPropagator` blend convention opposite to PRINet's `TemporalPhasePropagator`; mapping undocumented | FIXED | `20673c4`, `d2c1f1c`; `alpha = 1 − carry_strength` / `alpha = 1 − amplitude_decay` documented on all types and PyO3 classes; enforced by `parity_reversed_convention_does_not_match` |
| WP014-F1 | 014 | D1 | No Rust-vs-PRINet 3.0 parity tests for tensor decompositions | FIXED | `0a2c95d`; `crates/prin-tensor/tests/parity_decomposition.rs` — `[RETROACTIVE UPDATE - Executive Audit 003]` the `0a2c95d` suite verified mathematical invariants only; EA-003 finding E-F1 (D2) added a true differential HOSVD-vs-PRINet-3.0 reconstruction comparison |
| WP014-F2 | 014 | D2 | S1 marked complete with change set uncommitted | FIXED | `039ee7b`; committed mid-audit, delta re-audit verified |
| WP014-F3 | 014 | D2 | `hosvd` panicked on contract-valid rank > unfolding bound | FIXED | `72898f9`; rank validation + regression tests |
| WP014-F4 | 014 | D2 | `cp.rs` coverage below 95% | FIXED | `f72d6d1`; 8 new unit tests, 96.23% lines |
| WP014-F5 | 014 | D3 | `cp_als` convergence/normalization diverged from PRINet 3.0 | FIXED | `d377836`; error-based convergence, all-factor normalization |
| WP014-F6 | 014 | D4 | Documentation/hygiene: inaccurate convergence text, dead code, duplicated helper, misused error variants, handoff miscount | FIXED | `ca52af6`; README/lib.rs, remove dead code, deduplicate `flat_to_multi`, add `InvalidMaxIter`/`InvalidMode`, fix handoff |
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` — `[RETROACTIVE UPDATE - Executive Audit 003]` |
| WP015-F1 | 015 | D1 | 16-core CPU optimization below performance targets (sweep ≤2.1×, CPU/SpMV paths 3–6× slower parallel) | FIXED + AMENDED | `35dbb3e`; new `dispatch.rs` sequential/parallel dispatcher; plan amendment #21 re-scopes targets to hardware-evidenced figures `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP015-F2 | 015 | D2 | Commit `bfc2417` mislabeled as `docs` instead of `feat` | AMENDED | Closure record in `DOCS/audits/015-wp015-audit.md` |
| WP015-F3 | 015 | D2 | Lossy error mapping in `compute_derivatives` | FIXED | `f138476`; replaced unreachable error mapping with `.expect()` |
| WP015-F4 | 015 | D3 | 6 unused runtime deps and 1 unused dev dep in `prin-sim` | FIXED | `f138476`; removed unused deps from `Cargo.toml` |
| WP015-F5 | 015 | D3 | Misleading crate description and README | FIXED | `f138476`; updated description and README |
| WP015-F6 | 015 | D3 | Missing property tests (`proptest`) for the sparse simulation engine | FIXED | `f138476`; added `tests/proptest_properties.rs` with 4 property test suites `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F1 | 016 | D1 | 16-core CPU optimization below performance targets | FIXED + AMENDED | `35dbb3e`; new `dispatch.rs` sequential/parallel dispatcher; plan amendment #21 re-scopes targets `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F2 | 016 | D2 | Missing SIMD/reference dispatch | FIXED | `35dbb3e`; `dispatch.rs` `map_dispatch`/`zip_map_dispatch` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F3 | 016 | D2 | Algorithm duplication: private `order_parameter` instead of reusing `prin_metrics` | FIXED | `35dbb3e`; removed private function, calls `prin_metrics::order::kuramoto_order_parameter` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F4 | 016 | D2 | No N=1M `OscilloSim` parity/scale evidence | FIXED | `35dbb3e`; N=100k determinism/memory regression tes... `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F5 | 016 | D3 | Benchmark regression test absent | FIXED | `35dbb3e`; Criterion regression test at N=100k `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F6 | 016 | D3 | Stale `lib.rs` docs; WP declaration scope mismatch; missing `strict-checks` feature | FIXED + AMENDED | `35dbb3e`; `lib.rs` docs corrected; plan amendment #20 `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F7 | 016 | D3 | Unnecessary full `SparseCoupling` clone per sweep (~136 MB at N=1M) | FIXED | `35dbb3e`; `Arc<SparseCoupling>` sharing via `coupling_arc()` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F1 | 017 | D1 | `step_cubecl_with_pool` did not validate oscillator count against `CubeclBufferPool` size | FIXED | `2bf872d`; `MeanFieldRk4Error::PoolSizeMismatch`; `CubeclBufferPool::capacity()`; regression tests `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F2 | 017 | D2 | `buffers.rs` and `equivalence.rs` below 95% coverage | FIXED | `2bf872d`; removed dead accessors, added tests; both ≥95% `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F3 | 017 | D2 | `prin-kernels` provided backend priority but no end-to-end device/dtype dispatch | FIXED | `2bf872d`; `step_auto` dispatcher `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F4 | 017 | D2 | S1 commit typed `docs(WP-017)` despite 1,349 lines of source | AMENDED / RECORDED | `4e507bc` retains historical type; closure table records correct `feat(WP-017)` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F5 | 017 | D4 | `SESSION_REGISTER.md` row 0065 still `PLANNED` after S1 delivery | FIXED | `2bf872d`; register and brief updated `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP018-F1 | 018 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP019-F1 | 019 | D4 | Factual inaccuracy in S1 handoff note coverage table | FIXED | Commit `cdc01e6`; coverage cell corrected |
| WP020-F1 | 020 | D4 | `cargo test -p prin-kernels --features cpu` count transcription error in S2 audit report §2 | FIXED | S3 commit (session 0079); §2 corrected to "121 unit + 1 doctest" |
| WP021-F1 | 021 | D4 | Session 0081 row in `SESSION_REGISTER.md` was `PLANNED` while brief was `COMPLETE` | FIXED | Commit `00c636f`; register and phase-3 README updated |
| WP022-F1 | 022 | D4 | `bincode` RUSTSEC-2025-0141 advisory flagged without governing plan amendment | AMENDED | Plan amendment #27; commit `c3ae5c8` |
| WP022-F2 | 022 | D4 | `DiscreteDeltaThetaGammaParams`/`ResonanceLayerParams` not re-exported at crate root | FIXED | Commit `a5458ef`; crate-root `pub use` + compile-time regression test |
| WP022-F3 | 022 | D1 | `h2` RUSTSEC-2026-0258 DoS vulnerability in transitive build-time dependency | FIXED | Commit `1b7a8e9`; `h2` 0.4.15 → 0.4.16 in `Cargo.lock` |
| WP023-F1 | 023 | D4 | `public_api.rs` regression test did not cover `GatedPhaseActivationParams` re-export | FIXED | Commit `11821c0`; extended compile-time regression check |
| WP024-F1 | 024 | D3 | PSR-023 §7 WP-024 declaration named non-existent classes | AMENDED | Plan amendment #29 (session 0095); declaration text formally read as `SCALR`/`RIP`/`SyncGD` |
| WP025-F1 | 025 | D2 | `load_state_dict` did not guard against well-formed record with wrong tensor shape | FIXED | Commit `7b49e4e`; `validate_shapes`; load-into-clone-validate-commit pattern; 4 regression tests |
| WP025-F2 | 025 | D3 | `<5%` boundary-overhead evidence was a single unrepeated pilot | FIXED (evidence); gap tracked as DV-021 | Commit `2a41195`; 5-run median-of-medians measurement |
| WP025-F3 | 025 | D4 | `python/prin/nn/__init__.py` coverage was exactly 95% with zero margin | FIXED | Closed as byproduct of WP025-F1 fix; coverage now 100% |
| WP025-F4 | 025 | D4 | S1 handoff note cited wrong test counts | FIXED | Commit `2a41195`; both counts corrected |
| WP026-F1 | 026 | D4 | `AdaptiveOscillatorAllocator::validate_shapes` did not detect strategy mismatch | FIXED | S3 commit `2135077`; `TrainError::StrategyMismatch` variant; 2 regression tests |
| WP026-F2 | 026 | D4 | No whole-module golden-value parity test for `HybridPRINetV2.forward` | FIXED | S3 commit `2135077`; `HybridPRINetV2Params` + parity test; revealed and fixed missing ReLU in classifier head |
| WP027-F1 | 027 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP028-F1 | 028 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP029-F1 | 029 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP030-F1 | 030 | D4 | `SubconsciousController.export_to_onnx`/`.quantize_onnx`/`retrain_controller`: WP-028's approved deferral to "WP-030" (audit `028-wp028-audit.md` A1) was never reflected in WP-030's actual declared scope (PSR-029 §6) or delivered work; the committed `DOCS/baselines/wp001_api_traceability.md` had also drifted out of sync with its own generator (`tools/wp001_ownership.json` was never given the symbol-level override the WP-028 S4 hand-edit implied) | FIXED | This session (WP-030 S4, session 0120); `tools/wp001_ownership.json` symbol override on `prinet.nn.subconscious_model.retrain_controller` → WP-036; `DOCS/baselines/wp001_api_traceability.md` regenerated; `DOCS/sphinx/migration_guide.rst` corrected; see `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-025 |
| WP031-F1 | 031 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP032-F1 | 032 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP033-F1 | 033 | D2 | Two tests fail under `--basetemp=.pytest_basetemp` (AGENTS.md-documented Windows pytest workaround) — `_ALLOWED_ROOTS` did not cover the in-repo basetemp path | FIXED | `6eb4e8b`; monkeypatched `_ALLOWED_ROOTS` in the two affected tests; production confinement unchanged; delta re-audit CLEAN |
| WP034-F1 | 034 | D4 | Session briefs quote "15 figures"; the verified PRINet 3.0 reference contains 14 (`fig2`–`fig15`, no `fig1`). S1 ported all 14 and flagged the discrepancy | FIXED | Documentation-only correction closed in WP-034 S4 (session 0136): recorded in this PSR §1 and `CHANGELOG.md`; no source change. Single permitted D4 carry (S2→S4) per Development Workflow and Audit Standards §5 |
| WP034-F2 | 034 | D4 | `normalize_matplotlib_output` raised bare `ValueError` instead of the module's typed error hierarchy | FIXED | `11a97cb`; raises `NormalizationError(PublicationGenerationError, ValueError)`; docstring `Raises` and regression test updated |
| WP034-F3 | 034 | D4 | Reporting error hierarchy inconsistent across `benchmark_reporting`/`figure_generation`/`profiler` | FIXED | `8dbf55d`; every reporting error also subclasses a shared `ReportingError(Exception)` root in `prin.reporting._artifacts` while keeping its original stdlib base; regression test `test_all_reporting_errors_share_one_root` |
| WP034-F4 | 034 | D4 | `table_generation.py` imported the private `_load_json` from `figure_generation.py` (hidden cross-module coupling) | FIXED | `8dbf55d`; loader + schema-validation machinery moved to shared `prin.reporting._artifacts`; regression test `test_json_loading_is_shared_not_privately_cross_imported` |

---

## 4. Plan amendments this cycle

No new Project Plan §6 text amendment was required this cycle. Amendments
#1–#30 remain in force.

The WP034-F1 figure-count correction (14, not 15) is a **factual correction to
session-brief prose**, not a plan amendment: the Project Plan §6 WP-034
declaration does not quote a figure count, and the acceptance criterion
("stored 3.0 artefacts generate byte-comparable expected outputs or documented
deterministic normalization") is met for all 14 verifiable figures. This is the
same disposition class as the WP-033 62-vs-58 legacy-script correction
(PSR-033 §1).

---

## 5. Risks and blockers

- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC):** unchanged — allowed warnings
  per amendments #9/#27, re-verified this cycle (`cargo audit` exit 0, only
  these two warnings).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action.
- **DV-022 (ubuntu runner disk exhaustion):** external infrastructure
  condition. Status: OPEN, unchanged — WP-034 changes no CI workflow.
- All other DV register items closed at or before PSR-033 remain closed;
  `tools/check_dv_register_gates.py` passes (29 rows / 198 sessions).
- **WP-035 session-brief figure count:** the already-written WP-035 S1 brief
  (`0137-…`) inherits the "15 figures / 11 tables" wording from the same
  source. Per WP034-F1, its S1 must read "15" as **14**; the brief text is a
  future cycle's artefact and is intentionally left unedited here (stale
  prospective-brief prose is a D4 governance item, tracked by this note, not a
  blocker).
- No new risks introduced. `prin.reporting` adds no dependency, no numerics,
  no `unsafe`, no CI change, and no crate change.

---

## 6. Next work package declaration — WP-035

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0137-wp035-s1-reproduction-pipeline-and-manifest.md`),
per Documentation Standards §7 item 5:

- **Title:** Reproduction pipeline and manifest.
- **Scope (files/crates/modules):** Per the session brief's Mission —
  `tools/reproduce.py`, append-only artefact handling, SHA-256 manifest
  verification, and repro CI.
- **Plan sections advanced:** §6 (Phase 6 roadmap).
- **Acceptance criteria:** Per the session brief's Contract — all figures
  (**14**, per WP034-F1; brief text says 15) and 11 tables regenerate in
  seconds without GPU/training; manifest matches; tamper tests fail closed.
- **Non-goals:** Per the session brief — no new scientific claims.
- **First session brief:**
  `DOCS/sessions/phase-6/0137-wp035-s1-reproduction-pipeline-and-manifest.md`
  (already present in `SESSION_REGISTER.md`/`DOCS/sessions/phase-6/` as
  `PLANNED`, along with its S2–S4 successors 0138–0140).
- **Maintainer approval:** pending (recorded here at declaration; approval
  required before WP-035 S1 begins).

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(2/6 WPs complete: WP-033, WP-034).

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0133-wp034-s1-handoff.md`.

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — EA-001 through EA-006 and EMA-001 through EMA-005 all
listed and marked COMPLETE; `Hotfix-DV019` listed and marked COMPLETE; no
new global session ran this cycle.

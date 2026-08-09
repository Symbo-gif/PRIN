# PRIN Project State Report — Cycle 006

**Date:** 2026-08-07
**Cycle:** 006 (WP-006 "Oscillator state, errors, and deterministic seed")
**Completed sessions:** 0021–0024
**Author:** Devin (AI pair)
**Maintainer approval:** pending
**Git state:** `feat/wp006-oscillator-state` @ `a83bd48` (pre-S4 documentation baseline)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 1 — Dynamics core (**1 of 6** phase-1 WPs complete).
- **This cycle delivered:**
  - `OscillatorState` in `crates/prin-dynamics/src/state.rs`: struct-of-arrays representation for oscillator ensembles (`phase`, `amplitude`, `frequency`, optional `freq_band`) with constructors (`new`, `create_random`, `create_synchronized`), getters, and shape checks.
  - Counter-based deterministic `Seed` authority in `crates/prin-dynamics/src/seed.rs`: `rand_pcg::Pcg64` wrapper with `(counter, key)` stream identity, `jump`, bounded `next_f64_range`, `RngCore` integration, and `serde` round-trip support.
  - Phase and amplitude numerical guards: `% 2π` phase wrap (`wrap_phase`, `wrap_phases`), `atan2`-safe phase differences (`safe_phase_diff`, `safe_phase_diffs`), amplitude clamps `[1e-6, 10]` (`clamp_amplitude`, `guard_amplitude`), derivative clamps `±1e4` (`clamp_derivative`, `guard_derivative`), and sort-based phase k-NN index (`build_phase_knn_index`).
  - Typed error enumerations `StateError` and `SeedError` built with `thiserror`.
  - Opt-in `strict-checks` feature flag in `Cargo.toml` for strict guard validation returning errors versus default automatic clamping/repairing.
  - CI update in `.github/workflows/rust.yml`: added `clippy-strict` and `test-strict` jobs to exercise `--features strict-checks`.
  - Retroactive WP-001 hotfix `9153c7c` recorded in deviation ledger: hardening `tools/wp001_baseline.py` against untrusted root/ownership paths.
  - 58 Rust unit/property tests in `prin-dynamics` (including proptests for wrap, safe diffs, clamps, reproducibility, and k-NN), 13 in `prin-kernels`, 6 in `_prin_core` (77 total Rust tests). Python test suite 184 passed.
- **Plan conformance:** ON TRAJECTORY — no new plan amendments were required for WP-006. Prior amendments #1–13 remain in force.
- **Audit:** `DOCS/audits/006-wp006-audit.md` — S2 verdict `PASS-WITH-FINDINGS` (three findings: WP006-F1 D2, WP006-F2 D3, WP006-F3 D4); S3 delta re-audit **CLEAN**, all findings resolved (WP006-F1 FIXED, WP006-F2 FIXED, WP006-F3 FIXED/recorded).
- **Session Register:** 0021 (S1), 0022 (S2), 0023 (S3), 0024 (S4) marked **COMPLETE**; 0025 (WP-007 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 19/19 (workspace), 14/14 (`--features cpu`), 21/21 (`--features wgpu,cpu`) | 73/73 default workspace, 74/74 with `--features strict-checks` | 100% where defined |
| Python tests passing | 172 fast (6 deselected), 184 full | 172 fast (6 deselected), 184 full (tests + parity) | 100% |
| Coverage (changed code) | `prin._ort` 100%, `prin._phase0` 100% | `prin-dynamics` lines 99.70%, regions 98.21% (both default & strict builds) | ≥95% |
| Docstring coverage (interrogate) | 100% public (104/104) | 100% public (104/104); `cargo doc -D warnings` 0 warnings | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, 6 representative differential tests pass | 504 defined, 6 representative differential tests pass (unchanged) | 100% at tolerance when defined |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 warning (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code (medium+ threshold) | 0 | 0 medium/high findings | 0 at gate threshold |
| Snyk Open Source (low+ threshold) | 0 | 0 findings | 0 at gate threshold |
| Benchmark regression gates | N/A | none defined | none tripped |

**Verification commands run in S4:**

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp_fast
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp_full
.venv\Scripts\python tools/wp001_baseline.py check
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
cargo llvm-cov -p prin-dynamics --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

S4 re-ran the full suite after all documentation edits (README sweep, Sphinx `migration_guide.rst`, CHANGELOG, session register, and this report). All quality, coverage, documentation, security, and parity gates remain green.

## 3. Deviation ledger (cumulative)

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
| WP003-F3 | 003 | D3 | WP-003/Phase 0 go/no-go amendment not recorded | AMENDED | Plan amendment #7; CPU path validated, CUDA + `<5%` deferred to Phase 4 |
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

No findings are carried.

## 4. Plan amendments this cycle

None. Amendments #1–13 from cycles 001–005 remain in force.

## 5. Risks and blockers

- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; Snyk Open Source reports no findings.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp_fast` or `--basetemp=.pytest_basetemp_full` on Windows; directory pattern is ignored by `.gitignore`.
- **GitHub native secret scanning:** Remains unavailable for this private repository. Amendment #5's substitute is in force; availability rechecked each cycle.
- **No current blockers** for starting WP-007 S1 once maintainer approval is recorded.

## 6. Next work package declaration — WP-007

- **Title:** Oscillator dynamics models.
- **Scope (files/crates/modules):** `crates/prin-dynamics/src/models.rs` — Kuramoto (mean-field, pairwise, sparse k-NN), Stuart–Landau, and Hopf dynamics models implementing the `Dynamics` trait.
- **Plan sections advanced:** §4 (architecture rules — dynamics trait, clean separation of models and integrators), §6 Phase 1 (Dynamics core).
- **Acceptance criteria:**
  - Unit/property/parity tests cover model equations, parameter validation, order parameters, zero-coupling free-run, and parity against golden corpus cases.
  - ≥95% coverage on new/changed code; `cargo fmt`, clippy `-D warnings`, rustdoc `-D warnings`, ruff, mypy `--strict`, interrogate, bandit, pytest, dependency audits all clean.
  - Relevant golden corpus cases match reference at registered tolerances.
- **Non-goals:** Integrators, network propagation, GPU kernel optimization.
- **First session brief:** `DOCS/sessions/phase-1/0025-wp007-s1-oscillator-dynamics-models.md`
- **Maintainer approval:** pending

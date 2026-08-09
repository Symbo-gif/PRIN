# PRIN Project State Report — Cycle 008

**Date:** 2026-08-07
**Cycle:** 008 (WP-008 "Basic integrators")
**Completed sessions:** 0029–0032
**Author:** Devin (AI pair)
**Maintainer approval:** pending
**Git state:** `feat/wp006-oscillator-state` @ `9e24774` (pre-S4 documentation baseline)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 1 — Dynamics core (**3 of 6** phase-1 WPs complete).
- **This cycle delivered:**
  - `Integrator` trait (`step(&mut self, model, state, dt) -> Result<OscillatorState, IntegrateError>`) in `crates/prin-dynamics/src/integrate.rs` as the uniform interface for time integrators of oscillator dynamics.
  - `EulerIntegrator` — first-order explicit Euler with reusable derivative buffer.
  - `RK4Integrator` — classic fourth-order Runge–Kutta (order `h^4`) with explicit `k1`–`k4` reusable buffers.
  - `RK45Integrator` — adaptive Dormand–Prince RK45 with FSAL (First Same As Last) caching, PI step-size control (`clamp(SAFETY · err_norm^(-1/5), MIN_FACTOR, MAX_FACTOR)`), typed tolerance/step-budget errors, and `fsal_valid` invalidation on reuse/rejected steps.
  - `AdaptiveResult` struct (`final_state`, `accepted_steps`, `rejected_steps`, `final_dt`) returned by `RK45Integrator::integrate_adaptive`.
  - `integrate_fixed` free function for multi-step fixed-step integration with any `Integrator`.
  - `IntegrateError` enum with seven typed variants: `InvalidTimestep`, `InvalidTolerance`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue` (the latter under `strict-checks`).
  - Rust-vs-PRINet 3.0 trajectory parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` (16 golden-trajectory cases) comparing Euler and RK4 against `torch.float64` reference values at `rtol=1e-6, atol=1e-8` (and tighter for pure f64 paths); RK4 order-`h^4` convergence and RK45 tolerance-property parity tests.
  - 108 Rust unit/property tests in `prin-dynamics` (default), 111 with `--features strict-checks`; 16 integration parity tests in `parity_integrators.rs`; 9 in `parity_models.rs`; 13 in `prin-kernels`, 6 in `_prin_core` (152 total Rust tests default; 155 with `--features strict-checks`). Python test suite 184 passed.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — no new plan amendments this cycle. Prior amendments #1–14 remain in force.
- **Audit:** `DOCS/audits/008-wp008-audit.md` — S2 verdict `PASS-WITH-FINDINGS` (five findings: WP008-F1 D2, WP008-F2 D3, WP008-F3 D4, WP008-F4 D4, WP008-F5 D4); S3 delta re-audit **CLEAN**, all findings resolved (F1 FIXED, F2 FIXED, F3 FIXED, F4 FIXED, F5 FIXED).
- **Session Register:** 0029 (S1), 0030 (S2), 0031 (S3), 0032 (S4) marked **COMPLETE**; 0033 (WP-009 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 110/110 default workspace, 111/111 with `--features strict-checks` | 152/152 default workspace (108 `prin-dynamics` unit + 16 parity_integrators + 9 parity_models + 13 `prin-kernels` + 6 `_prin_core`), 155/155 with `--features strict-checks` | 100% where defined |
| Python tests passing | 172 fast (6 deselected), 184 full | 172 fast (6 deselected), 184 full (tests + parity) | 100% |
| Coverage (changed code) | `prin-dynamics` lines 98.18%, regions 97.74% | `prin-dynamics` lines 97.93%, regions 97.62% (integrate.rs 97.48% line / 96.72% function; models.rs 98.18% line; coupling.rs 100%; state.rs 97.63%; seed.rs 99.50%) | ≥95% |
| Docstring coverage (interrogate) | 100% public (104/104) | 100% public (104/104); `cargo doc -D warnings` 0 warnings | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, 6 representative differential tests pass; 9 Rust-vs-PRINet derivative parity cases pass | 504 defined, 6 representative differential tests pass; 9 derivative parity + 16 trajectory parity cases pass (`1e-12` float64 paths, `1e-6` f32-complex paths, `rtol=1e-6/atol=1e-8` trajectories) | 100% at tolerance when defined |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 warning (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code (low+ threshold) | 0 | 0 findings on `integrate.rs` | 0 at gate threshold |
| Snyk Open Source (low+ threshold) | 0 | 0 findings | 0 at gate threshold |
| Benchmark regression gates | N/A | none defined | none tripped |

**Verification commands run in S4:**

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp_full
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo test --doc -p prin-dynamics
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\src\integrate.rs severity_threshold=low  → 0 issues
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python  → 0 findings
```

S4 re-ran the full suite after all documentation edits (README sweep, CHANGELOG,
Migration Guide, Parity Report, session register, and this report). All quality,
coverage, documentation, security, and parity gates remain green.

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
| WP007-F1 | 007 | D2 | Coupled Stuart–Landau and Hopf derivative outputs not asserted against closed-form/PRINet reference values | FIXED | Commit `d030fff`; added `test_stuart_landau_coupled_reference_values` and `test_hopf_coupled_reference_values` unit tests for Full/MeanField/SparseKnn modes |
| WP007-F2 | 007 | D2 | No committed Rust-vs-PRINet derivative parity test for the new `Dynamics` implementation | FIXED | Commit `d030fff`; added `crates/prin-dynamics/tests/parity_models.rs` with 9 parity cases covering all models and coupling modes |
| WP007-F3 | 007 | D3 | Rust f64 implementations diverge from PRINet 3.0 reference due to PRINet's internal `torch.complex64` (f32) arithmetic; not listed among preserved numerical hazards | AMENDED | Plan amendment #14; preserved numerical hazard documented in Project Plan §5 and `DOCS/sphinx/parity_report.rst`; `1e-6` derivative parity tolerance for affected paths |
| WP007-F4 | 007 | D4 | `EVIDENCE/0017-wp005-s1-ort-probe.json` had uncommitted timestamp drift and CRLF→LF warning | FIXED | Restored committed version; `git status` clean against `HEAD` |
| WP007-F5 | 007 | D4 | Stuart–Landau and Hopf rustdoc did not spell out per-`CouplingMode` coupling-term formulas | FIXED | Commit `d030fff`; expanded rustdoc with explicit `C_i` (SL) and `C_i^sin`/`C_i^cos` (Hopf) per-mode formulas |
| WP008-F1 | 008 | D2 | FSAL cache in `RK45Integrator::integrate_adaptive` not invalidated at start of new integration; reuse across calls produces silently incorrect results | FIXED | Commit `f97ba5c`; added `fsal_valid: bool` flag invalidated on entry/rejected steps; regression test `rk45_fsal_cache_invalidated_on_reuse` |
| WP008-F2 | 008 | D3 | `IntegrateError::NonFiniteValue` error path (strict-checks) not exercised by any test | FIXED | Commit `f97ba5c`; added `NanDynamics` test helper + `strict_check_non_finite_value_error`/`strict_check_non_finite_value_rk4` tests; coverage 96.66% → 97.48% |
| WP008-F3 | 008 | D4 | `check_finite` doc comment inaccurate about non-strict NaN repair behavior | FIXED | Commit `f97ba5c`; corrected doc comment to state amplitude-only repair in non-strict mode |
| WP008-F4 | 008 | D4 | `lib.rs` module doc listed exponential/Krylov/multi-rate integrators (WP-008 non-goals) | FIXED | Commit `f97ba5c`; updated to list only Euler, RK4, adaptive RK45/Dormand–Prince |
| WP008-F5 | 008 | D4 | `RK45Integrator::new` reused `InvalidTimestep` for tolerance validation; test only checked `is_err()` | FIXED | Commit `f97ba5c`; added `IntegrateError::InvalidTolerance { param, value }` variant; updated test to assert specific variant |

No findings are carried.

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| — | — | No new plan amendments this cycle | — |

Amendments #1–14 from cycles 001–007 remain in force.

## 5. Risks and blockers

- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; Snyk Open Source reports no findings.
- **f64/f32 complex numerical hazard (amendment #14):** PRINet 3.0's `torch.complex64` internal arithmetic produces up to ~1e-7 per-step drift on Kuramoto/Hopf mean-field and all Stuart–Landau coupling paths. Accepted as a preserved numerical hazard with a `1e-6` derivative parity tolerance. Trajectory-level parity for integrators uses `rtol=1e-6, atol=1e-8` per Project Plan §5. Will be re-evaluated when a bit-for-bit f64 reference corpus is regenerated or an optional f32-complex reference path is added to `prin-dynamics`.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp` on Windows; directory pattern is ignored by `.gitignore`.
- **GitHub native secret scanning:** Remains unavailable for this private repository. Amendment #5's substitute is in force; availability rechecked each cycle.
- **No current blockers** for starting WP-009 S1 once maintainer approval is recorded.

## 6. Next work package declaration — WP-009

- **Title:** PAC, coupling topologies, and phase k-NN.
- **Scope (files/crates/modules):** `crates/prin-dynamics/src/pac.rs`, `crates/prin-dynamics/src/coupling.rs` — phase–amplitude coupling (`A_fast = A₀·[1 + m·cos(φ_slow + offset)]`), mean-field/local/sparse coupling, topology enums/builders, normalization rules (1/N versus 1/k), and rayon phase-sort k-NN index.
- **Plan sections advanced:** §4 (architecture rules — dynamics trait, clean separation of models and integrators), §6 Phase 1 (Dynamics core).
- **Acceptance criteria:**
  - Golden parity covers all modes; 1/N versus 1/k is explicit; sparse/full equivalence and k-NN edge properties pass.
  - ≥95% coverage on new/changed code; `cargo fmt`, clippy `-D warnings`, rustdoc `-D warnings`, ruff, mypy `--strict`, interrogate, bandit, pytest, dependency audits all clean.
  - Relevant golden corpus cases match reference at registered tolerances.
- **Non-goals:** GPU kernels or trainable discrete bands.
- **First session brief:** `DOCS/sessions/phase-1/0033-wp009-s1-pac-coupling-topologies-and-phase-k-nn.md`
- **Maintainer approval:** pending

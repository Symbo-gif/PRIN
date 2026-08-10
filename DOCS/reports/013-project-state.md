# PRIN Project State Report — Cycle 013

**Date:** 2026-08-10
**Cycle:** 013 (WP-013 "Continuous band networks and temporal propagation")
**Completed sessions:** 0049–0052
**Author:** GLM-5.2 High 1M (AI pair)
**Git state:** `main` @ `7e8bf21` (post-S3 baseline; S4 documentation commits follow)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 2 — Advanced numerics and simulation (**2 of 5** phase-2 WPs complete).
- **This cycle delivered:**
  - `BandParams`, `PacPair`, `BandNetwork` (implementing `Dynamics`), `theta_gamma_network` / `delta_theta_gamma_network` factories, `theoretical_capacity`, `create_band_state`, and `BandError` in `crates/prin-dynamics/src/bands.rs`.
  - `ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator`, and `TemporalError` in `crates/prin-dynamics/src/temporal.rs`.
  - `prin-py` PyO3 bindings `PyBandParams`, `PyPacPair`, `PyBandNetwork`, `create_band_state_py`, `PyComplexPhasorBlender`, `PyEmaAmplitudeBlender`, `PyTemporalPropagator` in `bindings/bands.rs` and `bindings/temporal.rs`; `python/prin/dynamics.py` `__all__` grew from 20 to 27 symbols; `python/prin/_prin_core.pyi` stubs; 44 Python acceptance tests in `tests/test_wp013_bands_temporal.py`.
  - 18 new Rust-vs-PRINet 3.0.0 parity tests: 12 in `crates/prin-dynamics/tests/parity_bands.rs` and 6 in `crates/prin-dynamics/tests/parity_temporal.rs`.
  - Integrator stage-state fix: `make_intermediate_state` and DOPRI5 `stage_state` in `crates/prin-dynamics/src/integrate.rs` now carry `freq_band` from the base state, enabling `BandNetwork` to be driven by RK4/RK45/exponential integrators (an additional defect found and fixed during S3 parity evidence generation, audit §7.1).
  - S2 audit (`DOCS/audits/013-wp013-audit.md`) found six findings (WP013-F1 D1, F2 D2, F3 D3, F4–F6 D4): missing parity evidence (F1), mean-field coupling mismatch with the PRINet 3.0 reference (F2), missing S1 handoff note (F3), function coverage below 95% (F4), `BandError::EmptyBand` semantics and PAC adjacency (F5), undocumented blend-parameter mapping (F6).
  - S3 remediation closed all six: F1/F3/F4/F5/F6 fixed with regression tests; F2 resolved via Project Plan amendment #19 (continuous ODE composition vs. the reference stepper, with parity evidence for each consequence). Delta re-audit: **CLEAN**.
  - S4 (this cycle) updated `crates/prin-dynamics/README.md`, `crates/prin-py/README.md`, `python/prin/README.md`, `tests/README.md`, `DOCS/audits/README.md`, `DOCS/reports/README.md`, `DOCS/experiments/README.md`, the Sphinx Migration Guide and Parity Report, `CHANGELOG.md`, and corrected a D4 symbol-count inaccuracy in the S1 handoff note (the note stated `__all__` grew from 20 to 26 symbols; the actual count is 27).
- **Plan conformance:** ON TRAJECTORY WITH ONE AMENDMENT — plan amendment #19 (WP-013 band-network composition decision: continuous ODE right-hand side vs. the reference's per-band stepper). Amendments #1–18 remain in force.
- **Audit:** `DOCS/audits/013-wp013-audit.md` — S2 verdict `FAIL` (six findings: one D1, one D2, one D3, three D4); S3 closure with CLEAN delta re-audit (five FIXED, one FIXED + AMENDED via plan amendment #19). One additional integrator-stage defect found during S3 was fixed in the same remediation.
- **Session Register:** 0049 (S1), 0050 (S2), 0051 (S3) marked **COMPLETE**; 0052 (S4) marked **COMPLETE**; 0053 (WP-014 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 401/401 default workspace, 404/404 with `--features strict-checks` | 501/501 default workspace, 504/504 with `--features strict-checks`; 22 doctests passing | 100% where defined |
| Python tests passing | 262 fast (6 deselected), 778 full (`tests/` + `parity/`, all markers) | 306 fast (6 deselected); 510 parity-marked tests (504 golden-corpus cases + 6 harness/schema tests), all pass | 100% |
| Coverage (changed code) | `prin-dynamics/src/integrate.rs` (WP-012): 98.24% lines / 98.46% functions (default), 97.74% lines / 98.50% functions (`strict-checks`); Python overall 99% (677 stmts, 10 miss) | `bands.rs`: 97.73% lines / 98.68% functions / 98.97% regions (identical under `strict-checks`); `temporal.rs`: 98.98% lines / 100% functions / 99.79% regions (identical under `strict-checks`); `integrate.rs` (stage-state fix): 97.14% lines / 98.46% functions (default), 97.16% lines / 98.50% functions (`strict-checks`); Python overall 99% (677 stmts, 10 miss) | ≥95% |
| Docstring coverage (interrogate) | 100% public (106/106) | 100% public (106/106); no new Python modules this cycle (Rust-backed PyO3 symbols) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 golden-corpus cases, all pass; 23 Rust-native parity tests in `parity_integrators.rs` (16 WP-008 + 7 WP-012) | 510 parity-marked tests pass (504 golden-corpus cases + 6 harness/schema tests, unchanged); 23 Rust-native integrator parity tests unchanged; 18 new Rust-native band/temporal parity tests (12 `parity_bands.rs` + 6 `parity_temporal.rs`), all pass | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code / Snyk Open Source | Not run in 012 S4 (no MCP connector available; reported blocked) | Snyk Code on `crates/prin-dynamics/src` and `crates/prin-py/src`: **0 issues**; whole-repo Snyk Code: 3 Low path-traversal findings in `tools/wp001_baseline.py` (pre-existing, `.snyk`-governed, outside WP-013 scope); Snyk Open Source (`all_projects=true`): **0 issues** | 0 at gate threshold |
| Benchmark regression gates | none defined | none defined for `prin-dynamics` | none tripped |

**Verification commands run in S4:**

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace                                    # 501 passing
cargo test --workspace --features strict-checks           # 504 passing
cargo test --doc --workspace                              # 22 doctests
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo llvm-cov -p prin-dynamics --summary-only
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
cargo audit
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp    # 306 passed, 6 deselected
.venv\Scripts\python -m pytest parity/ -m parity --basetemp=.pytest_basetemp-full                                              # 510 passed
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
.venv\Scripts\python tools\wp001_baseline.py check
# Snyk MCP scans:
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\src severity_threshold=low   → 0 issues
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-py\src severity_threshold=low          → 0 issues
#   snyk_code_scan path=C:\dev\PRIN severity_threshold=low                            → 3 Low (pre-existing in tools/wp001_baseline.py, .snyk-governed)
#   snyk_sca_scan  path=C:\dev\PRIN all_projects=true severity_threshold=low           → 0 issues
```

All quality, coverage, documentation, parity, and security gates are green after
the S4 documentation edits. No flaky-environment issues were observed this cycle
(the `.pytest_basetemp` directories were cleared before each run per the
documented Windows pytest temp-directory workaround in `AGENTS.md`).

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
| WP009-F1 | 009 | D2 | `cargo fmt --check` fails on `coupling.rs:339` test comment indentation | FIXED | Commit `b4749ba`; restructured `topology_ring_basic` trailing comment; `cargo fmt --check` exit 0 |
| WP009-F2 | 009 | D2 | `normalization_one_over_k_explicit_in_sparse` only asserts `is_finite()` — does not verify the 1/k normalization | FIXED | Commit `b4749ba`; strengthened to assert explicit `K/k` per-edge weight + shared-neighbour 3/2 ratio check |
| WP009-F3 | 009 | D3 | `build_ring`/`build_small_world` odd-clamp normalization violates `K/degree` energy invariant | FIXED | Commit `b4749ba`; new `clamp_ring_k` helper clamps to largest even `≤ n-1`; regression tests for both builders |
| WP009-F4 | 009 | D3 | `with_clamp` does not validate `amp_min <= amp_max` or finiteness — `f64::clamp` panics on inverted range | FIXED | Commit `b4749ba`; added `PacError::InvalidClampRange` variant + finiteness/ordering validation + regression tests |
| WP009-F5 | 009 | D4 | S1 handoff note factual errors (pac.rs stub→full, rayon sort, test count 198) | FIXED | Commit `bf46cee`; handoff note corrected |
| WP009-F6 | 009 | D4 | `topology_ring_clamps_k_to_n_minus_1` test comment inaccurate; no weight assertion | FIXED | Commit `b4749ba`; comment corrected + degree/weight/energy assertions added |
| WP009-F7 | 009 | D4 | `build_small_world` rewiring is directed; module docs don't clarify | FIXED | Commit `b4749ba`; directed interpretation documented in rustdoc + `Topology::SmallWorld` variant doc |
| WP011-F1 | 011 | D4 | `#![allow(unsafe_code)]` unnecessary in `state.rs` — no `unsafe` code exists | FIXED | Commit `cd20b1a`; attribute removed; `cargo clippy -D warnings` clean under crate-level `#![deny(unsafe_code)]` |
| WP012-F1 | 012 | D1 | S1 commit omitted the declared `prin-py` Python bindings for `ExponentialIntegrator`/`MultiRateIntegrator` | FIXED | `62deb43`; `PyExponentialIntegrator`/`PyMultiRateIntegrator`, `dynamics.py` re-exports, `.pyi` stubs, 21 new Python acceptance tests |
| WP012-F2 | 012 | D1 | No Rust-vs-PRINet 3.0 parity evidence for the new integrators | FIXED | `e4e7772`; 7 new golden-trajectory parity tests (4 Exponential, 3 MultiRate) in `parity_integrators.rs` |
| WP012-F3 | 012 | D1 | `matrix_exp` silently returned identity on a singular Padé LU denominator instead of a typed error | FIXED | `2dc641e`; `matrix_exp`/`phi1_matrix`/Krylov solves propagate `IntegrateError::LinearSolveFailed`; regression test `matrix_exp_singular_denominator_returns_typed_error` |
| WP012-F4 | 012 | D3 | WP-012 text implied band-aware multi-rate scheduling; implementation is uniform sub-stepping (matches PRINet 3.0 reference) | AMENDED | Plan amendment #18; Project Plan §6 WP-012 declaration clarified; `MultiRateIntegrator` rustdoc corrected in S4 to match |
| WP012-F5 | 012 | D4 | `ExponentialIntegrator::step`/`::integrate` did not validate the stored `dim` against the state size | FIXED | `2dc641e`; `IntegrateError::InvalidDim` on mismatch; regression tests `exp_integrator_dim_mismatch_returns_typed_error`, `exp_integrator_integrate_dim_mismatch_returns_typed_error` |
| WP013-F1 | 013 | D1 | No Rust-vs-PRINet 3.0 parity evidence for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator` | FIXED | `d2c1f1c`; 12 cases in `parity_bands.rs` + 6 in `parity_temporal.rs`, all green at documented tolerances |
| WP013-F2 | 013 | D2 | `BandNetwork` hard-coded mean-field intra-band coupling; PRINet 3.0 reference uses `sparse_knn` with per-band `MultiRateIntegrator` sub-stepping | FIXED + AMENDED | `20673c4`; plan amendment #19 (`5e0c602`); per-band `CouplingMode` dispatch via `BandParams::with_coupling`; residual composition difference (continuous ODE vs. stepper) governed by amendment #19 with parity evidence |
| WP013-F3 | 013 | D3 | No S1 handoff note / acceptance-criterion evidence map was committed | FIXED | `62843d4`; `DOCS/experiments/0049-wp013-s1-handoff.md` maps all twelve acceptance criteria to evidence |
| WP013-F4 | 013 | D4 | Function coverage below 95% on `bands.rs` (92.00%) and `temporal.rs` (94.64%) | FIXED | `20673c4`, `62843d4`; `bands.rs` 98.68% functions, `temporal.rs` 100% functions |
| WP013-F5 | 013 | D4 | `BandNetwork::new` returned `EmptyBand { band: 0 }` for an empty band list; non-adjacent PAC pairs allowed despite "adjacent" docstring | FIXED | `20673c4`; `BandError::NoBands` added; `PacPair` rustdoc/docstring corrected — any strictly slow→fast pair is intentional |
| WP013-F6 | 013 | D4 | `TemporalPropagator` blend convention opposite to PRINet's `TemporalPhasePropagator`; mapping undocumented | FIXED | `20673c4`, `d2c1f1c`; `alpha = 1 − carry_strength` / `alpha = 1 − amplitude_decay` documented on all types and PyO3 classes; enforced by `parity_reversed_convention_does_not_match` |

No findings are carried. WP-013 audit: FAIL at S2 (six findings); CLEAN delta
re-audit at S3 (five fixed, one fixed + amended via plan amendment #19). One
additional integrator-stage defect found during S3 was fixed in the same
remediation (audit §7.1).

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| 19 | Project Plan §4/§5 / WP-013 declaration (`DOCS/reports/012-project-state.md` §6) | Recorded the WP-013 band-network composition decision. PRINet 3.0's `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` are *steppers*: a per-band `KuramotoOscillator`, PAC applied as an instantaneous amplitude assignment between band steps, and a per-band `MultiRateIntegrator` with `sub_steps = floor(f_fast / f_slow)` embedded in the network. PRIN's `BandNetwork` is instead a single continuous ODE right-hand side over the concatenated state implementing `Dynamics`, so it composes with every PRIN `Integrator` rather than embedding one. Three consequences are accepted as the intended trajectory: (a) intra-band terms are the identical Kuramoto equations for the configured `CouplingMode`, including the reference's `sparse_knn`, and are parity-verified per mode against `prinet==3.0.0`; (b) PAC enters `dA_fast/dt` as the relaxation term `λ_fast·(A_target − A_fast)` toward the reference's modulation target, which is the continuous-time analogue of the reference's discrete assignment and is parity-verified against the reference's `PhaseAmplitudeCoupling.modulate` target; (c) per-band sub-stepping is supplied by driving the network with `MultiRateIntegrator`, with the reference's sub-step count exposed as `BandNetwork::theoretical_capacity`. Whole-network step-for-step trajectory parity with the reference stepper is therefore not claimed and is not a WP-013 acceptance criterion; band/temporal golden-trajectory acceptance is evidenced by `parity_bands.rs` and `parity_temporal.rs` | S3 (WP-013); WP013-F2 (D2) |

Amendments #1–18 from cycles 001–012 remain in force.

## 5. Risks and blockers

- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; no change this cycle.
- **f64/f32 complex numerical hazard (amendment #14):** Extended this cycle to the band-network mean-field coupling path. `BandNetwork` with `CouplingMode::MeanField` inherits the same Kuramoto mean-field f32-complex drift as WP-007, covered by the `1e-6` relative / `5e-7` absolute parity tolerance in `parity_bands.rs` (measured worst case `1.19e-7`). The `sparse_knn` mode the reference band networks actually use is unaffected and matches to ~1 ulp (`2.22e-16`).
- **Continuous ODE vs. stepper composition (amendment #19):** Whole-network step-for-step trajectory parity with PRINet 3.0's per-band stepper is not claimed. Parity is established at the level of intra-band terms, PAC target, composed right-hand side, golden trajectories, and capacity ratio. If a future WP requires step-for-step stepper parity, a dedicated stepper-mode `BandNetwork` variant would need to be implemented and amended into the plan.
- **Windows pytest temp directory:** No issues this cycle. The `.pytest_basetemp` and `.pytest_basetemp-full` directories were cleared before each run per the documented workaround in `AGENTS.md`. The risk remains and is re-confirmed each cycle.
- **Snyk Open Source availability:** Snyk Open Source ran successfully this cycle via the MCP connector (`all_projects=true`, 0 issues), unlike the 012 S4 cycle where it was blocked by the monthly private-test limit. CI's `snyk.yml` workflow remains the authoritative merge gate.
- **GitHub native secret scanning:** Remains unavailable for this private repository. Amendment #5's substitute is in force; availability rechecked each cycle — unchanged this cycle.
- **No current blockers** for starting WP-014 S1 once maintainer approval is recorded.

## 6. Next work package declaration — WP-014

- **Title:** Tensor decompositions.
- **Scope (files/crates/modules):** `crates/prin-tensor` — Tucker/HOSVD and CP/PARAFAC ALS decomposition with deterministic initialization and convergence diagnostics. The crate currently exists as a stub (0 tests, 0 implementations).
- **Plan sections advanced:** §4 (architecture rules), §6 Phase 2 (Advanced numerics + sim — third WP), §5 (numerical parity program — single-runtime metric/decomposition verification targeting `rtol=1e-10`).
- **Acceptance criteria:**
  - Reconstruction, rank/shape, degeneracy, and PRINet 3.0 parity tests pass at `rtol=1e-10` (per the WP-014 S1 brief, `DOCS/sessions/phase-2/0053-wp014-s1-tensor-decompositions.md`).
  - Seed reproducibility is exact (deterministic initialization via `prin-dynamics::Seed`).
  - ≥95% coverage on new/changed code; all quality gates clean.
  - Python bindings and stubs if the public API surface is exposed to Python.
- **Non-goals:** Learned tensor layers or benchmark figures (Phase 4 / Phase 6).
- **First session brief:** `DOCS/sessions/phase-2/0053-wp014-s1-tensor-decompositions.md`
- **Maintainer approval:** pending

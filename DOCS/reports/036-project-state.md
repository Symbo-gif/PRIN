# PRIN Project State Report — Cycle 036

**Date:** 2026-08-28
**Cycle:** 036 (WP-036 "API completion, acceptance suite, and migration")
**Completed sessions:** 0141A–0141E (S1), 0142 (S2), 0143 (S3), 0144 (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**4 of 6**
  phase-6 WPs complete: WP-033, WP-034, WP-035, WP-036).
- **This cycle delivered:**
  - **`prin` PRINet-3.0-compatible symbol surface** — all 172 `prinet.__all__`
    symbols resolve from `prin` and pass a construct/callable smoke check
    (parametrized matrix, 346 cases + 2 guards).
  - **`prin._deprecation` freeze machinery** — `deprecated`,
    `deprecated_parameter`, `verify_api_surface`, `FROZEN_PUBLIC_API` (175-name
    frozenset derived from PRIN RC1 `__all__`).
  - **New PyO3 bindings** (26 symbols): `prin-tensor` (2: `PolyadicTensor`,
    `CPDecomposition`), `prin-train` (6: `dSiLU`, `PhaseActivation`,
    `HolomorphicActivation`, `FeedbackInhibition`, `HolomorphicEnergy`,
    `HolomorphicEPTrainer`), `prin-kernels` (15: `pytorch_*` CPU reference
    family + sparse-coupling helpers), `prin-sim` (3: `sweep_coupling_params`,
    `detect_oscillation`, `phase_to_rate`). All thin marshalling; no numerics
    in `prin-py`.
  - **Net-new Python surface** (19 real + 18 D-2.2 stubs): `OscilloSim`,
    `SimulationResult`, `quick_simulate`, `ring_topology`,
    `small_world_topology`, solver family (`SolverResult`, `BatchedRK45Solver`,
    `FixedStepRK4Solver`, `gradient_checkpoint_integration`), `TelemetryLogger`,
    `ControlSignalBuffer`, dataclasses (`SequenceData`, `TrainingSnapshot`,
    `MultiSeedResult`, `AblationConfig`, `ExtendedTrainingResult`), profiling
    utilities (`count_parameters`, `count_flops`, `measure_wall_time`), and 18
    documented D-2.2 stubs for symbols requiring trainable Rust numerics.
  - **GPU/Triton D-D dispositions** — 6 `triton_*` stubs + 2 CUDA stubs raise
    `BackendUnavailableError`; predicates (`triton_available`,
    `cuda_fused_kernel_available`) return `False`.
  - **Consolidated 172-row Migration Guide table** — machine-checked against
    `DOCS/baselines/wp001_api_traceability.md` by `tools/wp036_migration_table.py`
    + `tests/test_migration_guide_consolidated.py`. No silent removals.
  - **No-Python-numerics AST check** — `tools/check_no_python_numerics.py`
    scans 13 compat modules; clean.
  - **DV-012 closed** — `prin-py` sweep/engine PyO3 bindings delivered
    (0141C); register row updated to `CLOSED`.
  - **S2 audit** (`DOCS/audits/036-wp036-audit.md`): verdict
    `PASS-WITH-FINDINGS` (2 D4 findings: WP036-F1 per-module coverage gaps,
    WP036-F2 handoff drafting process deviation).
  - **S3 remediation:** WP036-F1 FIXED (5 new branch-coverage tests;
    `simulation.py` 90%→100%, `y4q1_tools.py` 89%→100%); WP036-F2 AMENDED.
    Delta re-audit CLEAN.
  - **S4 documentation:** This report; CHANGELOG updated; session registers
    current.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#32
  remain in force. Amendments #31 (WP-036 split) and #32 (S1 decomposition
  into sub-passes) were adopted and executed this cycle.
- **Audit:** `DOCS/audits/036-wp036-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS` (2 D4). S3 FIXED WP036-F1, AMENDED WP036-F2, delta
  re-audit CLEAN. No unresolved D1/D2 finding exists.
- **Session Register:** 0141A–0141E (S1), 0142 (S2), 0143 (S3), 0144 (S4)
  all marked COMPLETE; 0144A (WP-036B S1) is the registered successor.

---

## 2. Metric trends

| Metric | Previous (PSR-035) | Current (PSR-036) | Gate |
|---|---|---|---|
| Rust tests passing | 1447 passed, 0 failed, 1 ignored | **Unchanged** — 1447 passed, 0 failed, 1 ignored; WP-036 adds no new Rust tests (bindings are tested from Python) | 100% where defined |
| Python tests passing | 719 passed, 9 deselected (fast suite) | **1214 passed**, 9 deselected (fast suite); +495 from WP-036 (534 WP-036-specific tests minus 39 that overlap existing suite parametrization) | 100% |
| Coverage (changed code) | `tools/reproduce.py` 100% | **99% overall** (`python/prin/`); all 13 new WP-036 compat modules at 95–100% | ≥95% on instrumented changed code |
| Docstring coverage (interrogate) | 95.6% overall | **97.1%** overall (532/548); all new WP-036 modules at 100% except pre-existing `reporting/` modules | ≥95% overall |
| Parity cases passing | Unchanged from PSR-033 | 172-symbol smoke matrix green; kernel-equivalence tests match CPU references at `rtol=1e-5, atol=1e-6`; migration table machine-checked | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 with 3 governed allowed warnings (`paste`/`bincode`/`chacha20`); `pip-audit` clean | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (fresh-directory build; Migration Guide renders the consolidated 172-symbol table) | 0 warnings |
| Snyk Code / Snyk Open Source | CI authoritative | Snyk Code: 0 issues on every new/modified first-party file; Snyk Open Source: N/A (no dependency manifest changed) | 0 at gate threshold |
| Benchmark regression gates | none tripped | none tripped (no benchmark code changed) | none tripped |

**Verification commands re-run in S4 (2026-08-28, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0):**

```
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0
cargo test --workspace                                                        # all green (1 ignored)
RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps                      # exit 0
cargo audit                                                                   # exit 0; 3 governed allowed warnings
.venv\Scripts\ruff check python/prin tools tests                              # All checks passed
.venv\Scripts\ruff format --check python/prin tools tests                     # clean
.venv\Scripts\mypy python/prin --strict                                       # 49 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 97.1%, PASS
.venv\Scripts\python -m bandit -r python/prin tools -c pyproject.toml         # 0 issues
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin    # 1214 passed, 9 deselected, 99% cov
.venv\Scripts\python tools/wp001_baseline.py check                            # passed
.venv\Scripts\python tools/check_deviation_ledger.py ...                      # passed
.venv\Scripts\python tools/check_dv_register_gates.py                         # 29 rows / 198 sessions, passed
.venv\Scripts\python tools/wp036_migration_table.py check                     # OK (172 symbols)
.venv\Scripts\python tools/check_no_python_numerics.py                        # clean (13 modules)
python -c "import prin; from prin._deprecation import verify_api_surface; ..."  # (set(), set())
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html      # build succeeded
```

---

## 3. Deviation ledger (cumulative)

Two new findings this cycle: WP036-F1 (D4, FIXED) and WP036-F2 (D4, AMENDED).
The cumulative table carries forward every row from PSR-035 §3 unchanged
(verified by `tools/check_deviation_ledger.py`) and appends the two WP-036
rows.

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
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` — `[RETROACTIVE UPDATE - Executive Audit 004]` |
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
| WP034-F1 | 034 | D4 | Session briefs quote "15 figures"; the verified PRINet 3.0 reference contains 14 (`fig2`–`fig15`, no `fig1`). S1 ported all 14 and flagged the discrepancy | FIXED | Documentation-only correction closed in WP-034 S4 (session 0136): recorded in PSR-034 §1 and `CHANGELOG.md`; no source change |
| WP034-F2 | 034 | D4 | `normalize_matplotlib_output` raised bare `ValueError` instead of the module's typed error hierarchy | FIXED | `11a97cb`; raises `NormalizationError(PublicationGenerationError, ValueError)`; docstring `Raises` and regression test updated |
| WP034-F3 | 034 | D4 | Reporting error hierarchy inconsistent across `benchmark_reporting`/`figure_generation`/`profiler` | FIXED | `8dbf55d`; every reporting error also subclasses a shared `ReportingError(Exception)` root in `prin.reporting._artifacts` while keeping its original stdlib base; regression test `test_all_reporting_errors_share_one_root` |
| WP034-F4 | 034 | D4 | `table_generation.py` imported the private `_load_json` from `figure_generation.py` (hidden cross-module coupling) | FIXED | `8dbf55d`; loader + schema-validation machinery moved to shared `prin.reporting._artifacts`; regression test `test_json_loading_is_shared_not_privately_cross_imported` |
| WP035-F1 | 035 | D4 | `tools/reproduce.py:25` imported `ReportingError` from the private `prin.reporting._artifacts` module; same cross-module private-import pattern as WP034-F4 | FIXED | `cbbbbb3`; changed to `from prin.reporting import ReportingError`; AST-based regression test `test_reproduce_imports_only_public_reporting_surface` committed in the same fix |
| WP036-F1 | 036 | D4 | `simulation.py` (90%) and `y4q1_tools.py` (89%) fell slightly below 95% individual module coverage; uncovered lines were real code branches (Stuart-Landau path, topology alias resolution, RK45 integrator, `Conv2d`/`GRUCell` FLOP estimation) | FIXED | S3 commit (`3d4033f`); 5 new tests in `tests/test_bucket_g_remainder.py`; both modules now 100% |
| WP036-F2 | 036 | D4 | Sub-pass 0141D2 did not append its handoff section to the running draft as its brief required; 0141E compiled the section from committed artefacts | AMENDED | Process deviation acknowledged; no code change applicable; future decomposed sessions will enforce the per-sub-pass handoff-append convention |

---

## 4. Plan amendments this cycle

Two new amendments adopted and executed:

- **Amendment #31** (2026-08-27): Split WP-036 into WP-036 / WP-036B /
  WP-036C. WP-036 delivers the compatibility surface only; WP-036B/C port the
  ~1,670-test acceptance suite. Sessions `0144A`–`0144H` inserted between
  planned integers 0144 and 0145.
- **Amendment #32** (2026-08-27): WP-036 S1 executed as five sequential
  sub-passes `0141A`–`0141E` (dependency-ordered), all feeding the single S2
  audit `0142`.

---

## 5. Risks and blockers

- **DV-005 (CUDA Burn backend):** Scoping decision per R31 disposition —
  deferred out of Phase 6; RC1's exit criteria do not require GPU training.
  Re-gate at the Phase 6 WP-036 S4 PSR (this document). Standing disposition
  (plan amendment #7) unchanged.
- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — allowed warnings per amendments #9/#27, re-verified this cycle
  (`cargo audit` exit 0, only these three warnings).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action.
- **DV-022 (ubuntu runner disk exhaustion):** external infrastructure
  condition. Status: OPEN, unchanged.
- **DV-025 (`retrain_controller`):** Stub delivered in WP-036 S1 (0141E);
  real implementation owned by WP-036C S1 (session 0144E) per register row.
- **Owning WP for trainable-layer rebuild (D-D rows 31–44):** Open maintainer
  decision. 14 symbols (`FeedforwardInhibition`, `DentateGyrusConverter`,
  `DGLayer`, `oscillatory_weight_init`, `PhaseToRateConverter`,
  `PhaseToRateAutoencoder`, `DenseAutoencoder`, `SparsityRegularizationLoss`,
  `HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`, `PRINetModel`,
  `compile_model`, `DiscreteDeltaThetaGamma`, `DiscreteDeltaThetaGammaLayer`)
  need a maintainer-declared owning WP. WP-036B/C is the plausible catch
  basin (each ported reference test that exercises one forces its rebuild).
- All other DV register items closed at or before PSR-035 remain closed;
  `tools/check_dv_register_gates.py` passes (29 rows / 198 sessions).
- No new risks introduced.

---

## 6. Next work package declaration — WP-036B

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144A-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md`),
per Documentation Standards §7 item 5:

- **Title:** Acceptance suite port — core, dynamics, model stack, subconscious.
- **Scope (files/crates/modules):** Port reference test clusters
  `test_core`, `test_utils`, `test_phases`, `test_hierarchical`,
  `test_phase_to_rate`, `test_q2`, `test_q2_remaining`, `test_q3_new`,
  `test_nn`, `test_scalr_enhanced`, `test_hybrid`, `test_clevr_n`,
  `test_subconscious` (~805 reference `def test_` functions). Imports adapted
  to `prin`; assertions unchanged.
- **Plan sections advanced:** §6 (Phase 6 roadmap).
- **Acceptance criteria:** Ported subset green on CPU, Linux + Windows,
  Python 3.11–3.13; coverage non-decreasing; zero skipped tests without a
  linked, maintainer-approved quarantine issue.
- **Non-goals:** Behavioural parity beyond "imports only" (tolerance
  governance per D-A of the execution plan); final documentation prose.
- **First session brief:**
  `DOCS/sessions/phase-6/0144A-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md`
  (present in `SESSION_REGISTER.md`/`DOCS/sessions/phase-6/` as `PLANNED`).
- **Maintainer approval:** Required before WP-036B S1 begins.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(4/6 WPs complete: WP-033, WP-034, WP-035, WP-036).

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0141-wp036-s1-handoff.md` and `0141-wp036-s1-dd-dispositions.md`.

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — 0141A–0141E, 0142, 0143, 0144 all marked COMPLETE;
0144A–0144H (WP-036B/C) marked PLANNED.

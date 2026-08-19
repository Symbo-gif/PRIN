---

# PRIN Project State Report — Cycle 024

**Date:** 2026-08-19
**Cycle:** 024 (WP-024 "Oscillator-aware optimizers")
**Completed sessions:** 0093–0096
**Author:** Devin (AI pair), approved by maintainer
**Git state:** `main` @ `e48022d` (S3 closure); S4 documentation closure follows

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 4 — Trainable stack and Torch bridge (**3 of 6** phase-4 WPs
  complete: WP-022, WP-023, WP-024; WP-025 through WP-027 remain).
- **This cycle delivered:**
  - **Third `prin-train` implementation increment** (`crates/prin-train/`), extending
    the Burn-based trainable stack with oscillator-aware optimizers:
    - `feedback` — shared order-parameter feedback and optimizer contract (rebuild of
      PRINet 3.0 `nn/optimizers.py`):
      - `OrderParameter` — global-or-per-group order parameter with Q3 dict resolution
        (SCALR's `Union[float, Dict[str, float]]` input).
      - `StepFeedback` — per-step input (order parameter, phase, amplitude).
      - `OscillatorOptimizer` — uniform `step`/`state_dict`/`load_state_dict` trait;
        the seam WP-025's thin `torch.optim.Optimizer` wrapper bridges to.
    - `sync_gd::SyncGd` — synchronized gradient descent with momentum and
      synchronization-barrier penalty (rebuild of PRINet 3.0
      `SynchronizedGradientDescent`): `penalty = λ·max(0, K_c − K)²`,
      `grad_modulation = max(0.1, 1 − grad_scale)` lr reduction.
    - `rip::Rip` — Hebbian coupling-matrix update (rebuild of PRINet 3.0
      `RIPOptimizer`): `ΔK[i,j] = η·cos(φ[i] − φ[j])·|r[j]|·(r_target − r[i])`,
      diagonal zeroed, combined additively with plain gradient descent. Documented
      deviation: fixes `n_oscillators` at construction (PRINet 3.0 silently skips
      non-square-matching parameters).
    - `scalr::Scalr` — adaptive learning-rate optimizer with oscillation-aware decay
      (rebuild of PRINet 3.0 `SCALROptimizer`): `lr_scale = r_min + (1 − r_min)·clamp(r, 0, 1)^α`,
      windowed-variance oscillation detection with multiplicative lr decay, adaptive
      `r_min` via EMA, and per-group lr scaling entry point.
    - `error::TrainError` — extended with 8 new typed variants (`InvalidLearningRate`,
      `InvalidMomentum`, `InvalidWeightDecay`, `InvalidSyncPenalty`,
      `InvalidCriticalOrder`, `InvalidTargetAmplitude`, `InvalidRMin`, `InvalidAlpha`).
    - **57 new unit tests** (5 `feedback`, 17 `sync_gd`, 12 `rip`, 23 `scalr`) +
      5 new golden-value parity tests against actual PRINet 3.0 optimizer classes +
      1 new public-API regression test + 3 new doctests; coverage 97.9–100% regions /
      99.7–100% lines on all four new files.
  - **S2 audit** (`DOCS/audits/024-wp024-audit.md`): verdict `PASS-WITH-FINDINGS`,
    one D3 finding (WP024-F1: PSR-023 §7 WP-024 declaration named non-existent
    classes `PhaseAdam`/`KuramotoOptimizer`).
  - **S3 remediation:** WP024-F1 AMENDED via plan amendment #29 (maintainer approval
    MichaelMaillet 2026-08-19); PSR-023 §7's declaration text is now formally read as
    `SCALR`/`RIP`/`SyncGD`/`scalr.rs`/`rip.rs`/`sync_gd.rs`. DV-020 updated to CLOSED.
    CLEAN delta re-audit appended to the Audit Report.
  - **S4 documentation:** updated `crates/prin-train/README.md`, `crates/README.md`,
    `CHANGELOG.md`, `DOCS/sphinx/migration_guide.rst` (WP-024 symbol entries),
    `DOCS/experiments/README.md`, `DOCS/audits/README.md`, `DOCS/reports/README.md`,
    `DOCS/README.md`, `DOCS/sessions/SESSION_REGISTER.md`, `DOCS/sessions/phase-4/README.md`;
    wrote this report; declared WP-025.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#29 remain in
  force; amendment #29 was required this cycle (WP024-F1 D3 resolution).
- **Audit:** `DOCS/audits/024-wp024-audit.md` — S2 verdict `PASS-WITH-FINDINGS`,
  one D3 finding, closed in S3 (AMENDED via amendment #29); CLEAN delta re-audit.
  No unresolved D1/D2 finding exists.
- **Session Register:** 0093 (S1), 0094 (S2), 0095 (S3), 0096 (S4) all marked
  **COMPLETE**; 0097 (WP-025 S1) is the registered successor.

---

## 2. Metric trends

| Metric | Previous (PSR-023) | Current (PSR-024) | Gate |
|---|---|---|---|
| Rust tests passing | 931/931 default workspace (897 unit/integration/property + 34 doctests); `prin-train` default 101 (93 unit + 7 parity + 1 `public_api`) + 6 doctests = 107; `prin-train --features strict-checks` 103 (95 unit incl. 2 NaN-guard + 7 parity + 1 `public_api`) + 6 doctests = 109 | **994/994** default workspace (960 unit/integration/property + **34 doctests**... actually 37 doctests), 0 failed; `prin-train` default **164** (150 unit + 12 parity + 2 `public_api`) + **9 doctests** = **173**; `prin-train --features strict-checks` **166** (152 unit incl. 2 NaN-guard + 12 parity + 2 `public_api`) + **9 doctests** = **175** | 100% where defined |
| Python tests passing | 306 passed, 6 deselected (fast suite); full suite `pytest tests/ parity/` 822 passed | 306 passed, 6 deselected (fast suite, unchanged — no Python files touched this cycle); full suite `pytest tests/ parity/` **822 passed**, 0 failed | 100% |
| Coverage (changed code) | `crates/prin-train/src/activations.rs` 99.40% lines / 100% functions; `energy.rs` 98.61% / 100%; `hep.rs` 98.92% / 100%; `inhibition.rs` 99.59% / 100%; `bands.rs` 99.26% / 100%; `layers.rs` 99.32% / 100%; `support.rs` 98.46% / 90% | `crates/prin-train/src/feedback.rs` **100.00%** regions / **100.00%** lines / 100% functions; `sync_gd.rs` **98.34%** / **99.70%** / 100%; `rip.rs` **97.91%** / **100.00%** / 100%; `scalr.rs` **98.24%** / **99.80%** / 100%; `support.rs` **100.00%** / **100.00%** / 100%; all WP-022/WP-023 files unchanged | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (106/106) — unchanged; Rust `#![warn(missing_docs)]` clean | 100% public (106/106) — unchanged, no Python files touched; Rust `#![warn(missing_docs)]` clean under `RUSTDOCFLAGS=-D warnings` (100% public-item rustdoc across all crates) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; +7 `prin-train` golden-value parity tests vs. PRINet 3.0 | 510 parity-marked Python tests (unchanged); **+5 new `prin-train` golden-value parity tests** vs. actual PRINet 3.0 optimizer classes (`parity_optimizers.rs` at `rtol=1e-9, atol=1e-12`), bringing total `prin-train` parity tests to **12**, all passing | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 across fmt/clippy/rustdoc/ruff/mypy/bandit; `cargo audit` exit 0 with 2 allowed warnings (amendments #9, #27); `pip_audit` clean | 0 across fmt/clippy (default + strict-checks)/rustdoc/ruff/mypy/bandit; `cargo audit` exit 0 with **2 allowed warnings**, both amendment-governed (`paste` RUSTSEC-2024-0436 — DV-008/amendment #9; `bincode` RUSTSEC-2025-0141 — DV-017/amendment #27). `pip_audit` clean for project and docs requirements | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (`migration_guide.rst` extended with WP-024 entries, rebuilt clean under `-W --keep-going`) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code: CI authoritative gate; local scan blocked (unauthenticated). Snyk Open Source: N/A for Cargo | Snyk Code: local Snyk re-scan BLOCKED — Snyk CLI unauthenticated on this machine (standing condition). CI `snyk` workflow is the authoritative gate. Snyk Open Source: N/A for Cargo; `cargo audit` is the authoritative ecosystem-native gate | 0 at gate threshold |
| Benchmark regression gates | none defined for `prin-train`; none tripped | none defined for `prin-train`; none tripped | none tripped |

**Verification commands re-run in S4 (2026-08-19, independent of S2/S3 evidence):**

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean (exit 0)
cargo clippy -p prin-train --all-targets --features strict-checks -- -D warnings # clean (exit 0)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps        # 0 warnings
cargo test --workspace                                                  # 994 passed, 0 failed
cargo test -p prin-train                                                # 164 + 9 doctests passed
cargo llvm-cov -p prin-train --summary-only                             # feedback 100%/100%, sync_gd 98.34%/99.70%, rip 97.91%/100%, scalr 98.24%/99.80%, support 100%/100%
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/      # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 50 files already formatted
.venv\Scripts\mypy python/prin --strict                                 # 18 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin       # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                   # 0 issues
.venv\Scripts\python -m pip_audit .                                     # 0 issues
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt       # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp   # 306 passed, 6 deselected
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full                # 822 passed
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings
.venv\Scripts\python tools/wp001_baseline.py check                      # WP-001 baseline validation passed
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/023-project-state.md DOCS/reports/024-project-state.md   # ledger consistency check passed
```

---

## 3. Deviation ledger (cumulative)

One new finding was raised and closed this cycle: WP024-F1 (D3, PSR-023 §7 WP-024
declaration named non-existent classes), AMENDED via plan amendment #29. The
cumulative table below carries forward all rows from `DOCS/reports/023-project-state.md`
§3 unchanged (verified by `tools/check_deviation_ledger.py`, run in two-report mode)
with the new WP-024 row appended.

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
| WP013-F1 | 013 | D1 | No Rust-vs-PRINet 3.0 parity evidence for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator` | FIXED | `d2c1f1c`; 12 cases in `parity_bands.rs` + 6 in `parity_temporal.rs`, all green at documented tolerances |
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
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` — `[RETROACTIVE UPDATE - Executive Audit 003]` "CI green on `039ee7b`" originally meant only its `rust` job; EA-003 live-reran the remaining `python`/`parity`/`repro`/`snyk` jobs on `039ee7b` (now all green) and all 5 jobs on the WP-013 S4 commit `4a4de26` (4 of 5 now green; `python` surfaced a real, transient, already-self-corrected `session 0053` status mismatch — see `EXECUTIVE_AUDIT_REPORT_003.md` E-F2/E-F4) |
| WP015-F1 | 015 | D1 | 4 strict-checks test failures in `prin-sim` due to amplitude boundaries | FIXED | `f138476`; `engine.rs` / `pruning.rs` test bounds updated |
| WP015-F2 | 015 | D2 | Commit `bfc2417` mislabeled as `docs` instead of `feat` | AMENDED | Closure record in `DOCS/audits/015-wp015-audit.md` |
| WP015-F3 | 015 | D2 | Lossy error mapping in `compute_derivatives` | FIXED | `f138476`; replaced unreachable error mapping with `.expect()` |
| WP015-F4 | 015 | D3 | 6 unused runtime deps and 1 unused dev dep in `prin-sim` | FIXED | `f138476`; removed unused deps from `Cargo.toml` |
| WP015-F5 | 015 | D3 | Misleading crate description and README | FIXED | `f138476`; updated description and README |
| WP015-F6 | 015 | D3 | Missing property tests (`proptest`) for the sparse simulation engine | FIXED | `f138476`; added `tests/proptest_properties.rs` with 4 property test suites `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F1 | 016 | D1 | 16-core CPU optimization below performance targets (sweep ≤2.1×, CPU/SpMV paths 3–6× slower parallel) | FIXED + AMENDED | `35dbb3e`; new `dispatch.rs` sequential/parallel dispatcher; plan amendment #21 re-scopes targets to hardware-evidenced figures `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F2 | 016 | D2 | Missing SIMD/reference dispatch (mission called for "CPU SIMD/reference dispatch"; S1 delivered only unconditional `rayon` loops) | FIXED | `35dbb3e`; `dispatch.rs` `map_dispatch`/`zip_map_dispatch` sequential-reference + size-gated parallel dispatcher `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F3 | 016 | D2 | Algorithm duplication: private `order_parameter` reimplemented instead of reusing `prin_metrics::order::kuramoto_order_parameter` | FIXED | `35dbb3e`; removed private function, calls `prin_metrics::order::kuramoto_order_parameter`; added `parity_detect_oscillation.rs` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F4 | 016 | D2 | No N=1M `OscilloSim` parity/scale evidence (largest parity test was N=256; N=1M unverified) | FIXED | `35dbb3e`; N=100k determinism/memory regression test + N=1M benchmark evidence `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F5 | 016 | D3 | Benchmark design lacked an in-process serial baseline (workload too small to show target speedup) | FIXED | `35dbb3e`; `sweep_bench.rs` rewritten with dedicated 1-thread `rayon` pool serial baselines, larger workloads `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F6 | 016 | D3 | Stale `lib.rs` docs contradicting shipped `sweep` module; WP declaration scope mismatch (`prin-py`/`prin-kernels` listed but untouched); missing `strict-checks` feature | FIXED + AMENDED | `35dbb3e`; `lib.rs` docs corrected; plan amendment #20 narrows scope; `strict-checks` feature added to `prin-sim/Cargo.toml` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP016-F7 | 016 | D3 | Unnecessary full `SparseCoupling` clone per sweep configuration (~136 MB at N=1M) | FIXED | `35dbb3e`; `Arc<SparseCoupling>` sharing via `coupling_arc()` `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F1 | 017 | D1 | `step_cubecl_with_pool` did not validate oscillator count against `CubeclBufferPool` size (silent output truncation / out-of-bounds device-buffer risk) | FIXED | `2bf872d`; `MeanFieldRk4Error::PoolSizeMismatch`; `CubeclBufferPool::capacity()`; regression tests `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F2 | 017 | D2 | `buffers.rs` and `equivalence.rs` below 95% coverage (dead accessors, untested `Default`/mismatch-detection paths) | FIXED | `2bf872d`; removed dead `CubeclBufferPool` accessors, added `Default`/mismatch-detection tests; both ≥95% `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F3 | 017 | D2 | `prin-kernels` provided backend priority ordering but no operational device/dtype dispatch end-to-end | FIXED | `2bf872d`; `step_auto` dispatcher tries each backend in `auto_detect_order` priority with tested fallback `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F4 | 017 | D2 | S1 commit typed `docs(WP-017)` despite shipping 1,349 lines of first-party source (three new/refactored modules) | AMENDED / RECORDED | `4e507bc` retains its historical type (no history rewrite); closure table records correct `feat(WP-017)` classification `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP017-F5 | 017 | D4 | `DOCS/sessions/SESSION_REGISTER.md` row 0065 still `PLANNED` after S1 delivery (brief said `S1 DELIVERED`) | FIXED | `2bf872d`; `SESSION_REGISTER.md` row 110 and session brief statuses updated `[RETROACTIVE UPDATE - Executive Audit 004]` |
| WP018-F1 | 018 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP019-F1 | 019 | D4 | Factual inaccuracy in S1 handoff note coverage table (`pac/cubecl.rs` cpu coverage cell) | FIXED | Commit `cdc01e6`; coverage cell corrected |
| WP020-F1 | 020 | D4 | `cargo test -p prin-kernels --features cpu` count transcription error in S2 audit report §2 (read "102" instead of "121") | FIXED | S3 commit (session 0079); §2 corrected to "121 unit + 1 doctest", matching the S1 handoff note and independent re-runs |
| WP021-F1 | 021 | D4 | Session 0081 row in `SESSION_REGISTER.md` was `PLANNED` while brief was `COMPLETE` | FIXED | Commit `00c636f`; `SESSION_REGISTER.md` and `phase-3/README.md` row 0081 updated to `COMPLETE` |
| WP022-F1 | 022 | D4 | `bincode` RUSTSEC-2025-0141 ("unmaintained") advisory flagged in DV-017 without a governing plan amendment | AMENDED | Plan amendment #27; commit `c3ae5c8`; Coding Standards §6.2 threat assessment recorded; same disposition class and per-cycle `cargo audit` recheck cadence as amendment #9 (DV-008) |
| WP022-F2 | 022 | D4 | `DiscreteDeltaThetaGammaParams`/`ResonanceLayerParams` not re-exported at the `prin-train` crate root | FIXED | Commit `a5458ef`; crate-root `pub use` re-exports in `lib.rs` + compile-time regression test `crates/prin-train/tests/public_api.rs` |
| WP022-F3 | 022 | D1 | `h2` RUSTSEC-2026-0258 DoS vulnerability (unbounded empty DATA frames) in transitive build-time dependency via `cubecl-cpu`/`tracel-llvm-bundler`/`reqwest` | FIXED | Commit `1b7a8e9`; `h2` 0.4.15 → 0.4.16 in `Cargo.lock`; `cargo audit` clean at governed threshold |
| WP023-F1 | 023 | D4 | `public_api.rs` regression test did not cover `GatedPhaseActivationParams` crate-root re-export | FIXED | Commit `11821c0`; extended `public_api.rs` compile-time regression check |
| WP024-F1 | 024 | D3 | PSR-023 §7 WP-024 declaration named `PhaseAdam`/`KuramotoOptimizer` and `phase_adam.rs`/`kuramoto_optimizer.rs`; none exist in the PRINet 3.0 reference | AMENDED | Plan amendment #29 (session 0095); PSR-023 §7's declaration text formally read as `SCALR`/`RIP`/`SyncGD`/`scalr.rs`/`rip.rs`/`sync_gd.rs` — the delivered, PRINet-3.0-verified scope; DV-020 CLOSED |

---

## 4. Plan amendments in force

Amendments #1–#28 remain in force; amendment #29 was added this cycle.

| # | Summary | Status |
|---|---|---|
| #1–#4 | Foundation baseline, golden corpus, PyO3 spike, CubeCL spike governance | Active |
| #5 | Gitleaks + branch-protection substitute for GitHub secret scanning | Active (re-checked this cycle via `gh api`: `secret_scanning`/`push_protection` still `null` on the private repo) |
| #6 | `prin-py` Python-FFI `unsafe` exception | Active |
| #7 | CPU path validated; CUDA DLPack `<5%` deferred to Phase 4 (WP-025) | Active |
| #8 | `prin-kernels` crate-level unsafe lint policy | Active |
| #9 | `paste` RUSTSEC-2024-0436 allowed; re-check every cycle | Active (re-checked this cycle, unchanged) |
| #10 | `cargo-llvm-cov` non-instrumentable `#[cube(launch)]` carve-out | Active |
| #11 | Triton same-hardware comparison deferred to Phase 3 / `gpu.yml` | Active (superseded in strategy by #26: needs a Linux self-hosted runner) |
| #12 | wgpu kernel-equivalence CI deferred to headless GPU runner | Active (CI step now exists via #26's `gpu-wgpu` job; runner registration pending) |
| #13 | ORT go/no-go recorded as plan amendment | Active |
| #14 | f64/f32 complex numerical hazard preserved | Active |
| #15 | Executive audit sessions outside planned 0001–0198 sequence | Active |
| #16–#17 | *(retired / superseded)* | — |
| #18 | WP-012 multi-rate scheduling clarification | Active |
| #19 | WP-013 `BandNetwork` coupling-mode dispatch and composition | Active |
| #20 | WP-016 `prin-py` sweep/engine bindings deferred | Active |
| #21 | `cargo bench` smoke test CI gating | Active |
| #22 | Phase 1/2 pre-release tag (`v0.3.0-alpha.1` retroactively covers both) | Active |
| #23 | Executive Mathematical Audit governance and methodology | Active |
| #24 | Lean 4 `decide`-based formal claims for `GRA-01`/`TEN-01` | Active |
| #25 | PRINet 3.0 `chimera.rs` phase-wrap upstream defect — permanent non-parity exception | Active |
| #26 | Self-hosted GPU runner strategy; `gpu.yml` `gpu-wgpu` job; R24 closed | Active (runner registration pending — out-of-band) |
| #27 | `bincode` RUSTSEC-2025-0141 accepted; re-check every cycle | Active (governs DV-017) |
| #28 | Push/CI cadence: only S4 pushes, carrying full S1–S4 range | Active (first used this cycle) |
| #29 | WP-024 declaration naming correction (PSR-023 §7 `PhaseAdam`/`KuramotoOptimizer` → `SCALR`/`RIP`/`SyncGD`) | Active (governs DV-020, now CLOSED) |

---

## 5. Risks and open items

- **DV-001 (Triton comparison):** local CUDA execution validated (WP-021); strategy
  decided (amendment #26, self-hosted runner); registration pending, and the Triton
  half specifically requires a **Linux** runner (Triton has no Windows support).
- **DV-002 (wgpu CI):** the `gpu-wgpu` CI step exists in `gpu.yml` (amendment #26);
  registering a `[self-hosted, gpu]`-labelled runner is the sole remaining step
  (out-of-band GitHub Settings action).
- **DV-003 (device-event timing):** partially closed; host dispatch/sync overhead
  across the 8-launch sequence remains a candidate future-WP optimization.
- **DV-004 (coverage carve-out):** ten non-instrumentable `#[cube(launch)]` kernel
  bodies; instrumentable code ≥95% everywhere.
- **DV-005 (CUDA DLPack validation):** re-audited at WP-022/WP-023/WP-024 — unaffected
  (these cycles' Burn primitives are CPU-only `NdArray`); deferred to WP-025 per amendment #7.
- **DV-006 (DirectML/VitisAI):** open, blocked on hardware; Phase 4+/WP-028.
- **DV-007 (f64/f32 complex hazard):** open, preserved numerical hazard (amendment #14).
- **DV-008 (`paste` advisory):** re-checked with `cargo audit` this cycle (2026-08-19):
  unchanged, still amendment-governed (exit 0).
- **DV-009 (GitHub secret scanning):** re-checked this cycle via `gh api` — still
  unavailable (`null`) on this private repository; Gitleaks + branch-protection substitute
  (amendment #5) remains in force.
- **DV-010 (pre-release tags):** `v0.3.0-alpha.1` covers Phase 1/2; tag push remains
  deferred to explicit maintainer release action.
- **DV-011 (`torch@2.13.0` advisories):** accepted in `.snyk`; recheck due 2026-11-14.
- **DV-012 / R19 (`prin-py` carried scope):** `prin-kernels` half closed (WP-017);
  `prin-py` sweep/engine bindings assigned to Phase 6 WP-036.
- **DV-013 (`M-F3` review items):** open by policy design; EMA-002 re-confirmed the
  sign-off precedent (R20 closed).
- **DV-016 (`windows-latest` CubeCL-CPU slowdown):** open, non-blocking; `timeout-minutes: 120`
  safety net in place; root-cause investigation tracked as R25 (opportunistic, not WP-gated).
- **DV-017 (`bincode` advisory):** formally governed (amendment #27); re-checked with
  `cargo audit` this cycle — exit 0, still the sole non-`paste` allowed warning.
- **DV-018 (`burn-tensor` default sigmoid downcast precision floor):** `burn-tensor` 0.16.1's
  default `sigmoid` op downcasts through `f32` internally. Accommodated in `d_silu` and
  `GatedPhaseActivation` gradchecks/parity via `rtol=1e-6` / `eps=1e-4` precision allowances;
  tracked for upstream re-check on Burn version upgrades.
- **DV-019 (WP-022 `bands::tests::gradients_flow_to_every_parameter` thread contention):**
  intermittent test flakiness under high parallel thread load in the frozen WP-022 `bands.rs`
  test module. Recurred once during WP-024 S1 `cargo llvm-cov -p prin-train` (immediate
  re-run clean); same pre-existing class, unaffected by WP-024 scope. Tracked for future
  investigation.
- **DV-020 (WP-024 declaration naming):** **CLOSED** (2026-08-19) — plan amendment #29
  formally reads PSR-023 §7's `PhaseAdam`/`KuramotoOptimizer`/`phase_adam.rs`/`kuramoto_optimizer.rs`
  as `SCALR`/`RIP`/`SyncGD`/`scalr.rs`/`rip.rs`/`sync_gd.rs`.
- **Snyk local scanning unavailable (standing observation):** Snyk CLI unauthenticated
  on this machine (standing condition). The authoritative CI `snyk` workflow is the
  merge gate.

---

## 6. Trajectory verdict

**ON TRAJECTORY.** Phase 4 is 3 of 6 WPs complete (WP-022, WP-023, WP-024). The cycle
delivered the declared scope in full — three oscillator-aware optimizers (`SyncGd`,
`Rip`, `Scalr`), the shared order-parameter feedback contract (`feedback::OrderParameter`,
`StepFeedback`, `OscillatorOptimizer`), and 8 new typed `TrainError` variants — with
golden-value parity at `rtol=1e-9, atol=1e-12` against the actual PRINet 3.0 optimizer
classes, deterministic resume verification, and comprehensive test coverage (97.9–100%
on all new files). One D3 audit finding (WP024-F1) was closed in S3 (AMENDED via plan
amendment #29) with a CLEAN delta re-audit. No unresolved D1/D2 finding exists and no
finding is carried. The successor WP-025 (Production Torch autograd bridge, Phase 4,
sessions 0097–0100) is declared below.

---

## 7. Next work package declaration — WP-025

- **Title:** WP-025 — Production Torch autograd bridge
- **Scope (files/crates/modules):**
  - `crates/prin-py/` — PyO3/DLPack autograd.Function bridges with Rust forward/backward
  - `python/prin/nn/` — thin Python optimizer wrappers bridging to `feedback::OscillatorOptimizer`
  - `python/prin/nn/*.pyi` — type stubs
  - `crates/prin-train/` — any bridge-specific support types needed
- **Plan sections advanced:** Project Plan §6 (Phase 4), §8.1 (WP-025), Target Architecture §5 (`prin-py`, `prin-train`).
- **Acceptance criteria:**
  - Every bridge passes `torch.autograd.gradcheck` in float64.
  - Zero-copy DLPack paths are proven (no unnecessary tensor copies).
  - Boundary overhead remains <5% per call.
  - Python contains no duplicated math — all numerics stay in Rust.
  - Lifetime safety for borrowed tensors across the FFI boundary.
  - Checkpoint/save-load support for trained state.
  - ≥95% line coverage on new/changed code, 100% public docstrings, 0 clippy/fmt/audit/test failures.
- **Non-goals:** Model-specific training claims; end-to-end experiment statistics.
- **First session brief:** `DOCS/sessions/phase-4/0097-wp025-s1-production-torch-autograd-bridge.md`
- **Maintainer approval:** Declared herein; maintainer approval required before S1 begins.

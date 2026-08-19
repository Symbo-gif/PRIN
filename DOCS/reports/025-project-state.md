# PRIN Project State Report — Cycle 025

**Date:** 2026-08-19
**Cycle:** 025 (WP-025 "Production Torch autograd bridge")
**Completed sessions:** 0097–0100 (plus S3-exec executive session)
**Author:** Claude Sonnet 5 (AI pair), approved by maintainer
**Git state:** `main` @ `a57da3e` (S3-exec closure); S4 documentation closure follows

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 4 — Trainable stack and Torch bridge (**4 of 6** phase-4 WPs
  complete: WP-022, WP-023, WP-024, WP-025; WP-026 and WP-027 remain).
- **This cycle delivered:**
  - **Production PyO3/DLPack `torch.autograd.Function` bridge** exposing
    `prin-train`'s Rust forward/backward to Python training loops:
    - `crates/prin-py/src/bindings/train.rs` — `PyResonanceLayerBridge` /
      `PyGatedPhaseActivationBridge` with `*Ctx` backward contexts; each
      bridge reads a DLPack capsule, runs the `prin-train` Rust forward
      (multi-step Kuramoto integration or gated phase activation), and
      returns a DLPack capsule plus a Rust context whose `backward` runs
      the Rust backward pass. Forward and backward each cross the boundary
      exactly once per call (Coding Standards §3.2).
    - `crates/prin-py/src/dlpack.rs` — two additive helpers
      (`read_dlpack_f64` / `export_dlpack_f64`) reusing the validated-shape
      → `contiguous_strides` → `element_count` → `std::slice::from_raw_parts`
      pattern; no new `unsafe` blocks.
    - `python/prin/nn/__init__.py` — `ResonanceLayer` and
      `GatedPhaseActivation` `torch.nn.Module` wrappers (the user-facing
      API), with `rust_state_dict` / `load_rust_state_dict` checkpoint
      methods.
    - `crates/prin-train/src/layers.rs` / `activations.rs` —
      `ResonanceLayer::validate_shapes` / `GatedPhaseActivation::validate_shapes`
      for checkpoint shape validation (WP025-F1 fix).
    - `tensor2_from_dlpack_with_data` eliminating a redundant
      Tensor→`TensorData`→`Vec` round trip in both bridges' `forward()`
      (DV-021 S3-exec optimization, commit `e720a24`).
  - **S2 audit** (`DOCS/audits/025-wp025-audit.md`): verdict
    `PASS-WITH-FINDINGS`, four findings: WP025-F1 (D2), WP025-F2 (D3),
    WP025-F3 (D4), WP025-F4 (D4).
  - **S3 remediation:** WP025-F1 FIXED (checkpoint shape validation with
    regression tests at both Rust and Python levels); WP025-F2 FIXED at the
    evidentiary level (5-run median-of-medians measurement), underlying
    performance gap recorded as DV-021; WP025-F3 FIXED (coverage now 100%,
    was 95%); WP025-F4 FIXED (test-count transcription errors corrected).
    CLEAN delta re-audit.
  - **S3-exec addendum:** DV-021 performance investigation (redundant copy
    elimination, zero-behavior-change verified, does not measurably close
    DV-021 — expected since the Rust criterion baseline never touches
    `train.rs`/DLPack by construction); register-wide deferred-item review
    (DV-003 disposition updated, DV-019 third flaky recurrence documented
    with two candidate mitigations).
  - **S4 documentation:** updated `crates/prin-py/README.md`,
    `crates/prin-train/README.md`, `crates/README.md`, `CHANGELOG.md`,
    `DOCS/sphinx/migration_guide.rst`, `DOCS/experiments/README.md`,
    `DOCS/audits/README.md`, `DOCS/reports/README.md`, `DOCS/README.md`,
    `DOCS/sessions/SESSION_REGISTER.md`,
    `DOCS/sessions/phase-4/README.md`; wrote this report; declared WP-026.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#29
  remain in force; no new amendment was required this cycle (WP025-F2's
  underlying performance gap was recorded as DV-021 rather than amended,
  per maintainer direction).
- **Audit:** `DOCS/audits/025-wp025-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS`, four findings (one D2, one D3, two D4), all closed
  in S3 (FIXED); CLEAN delta re-audit. No unresolved D1/D2 finding exists.
- **Session Register:** 0097 (S1), 0098 (S2), 0099 (S3), 0100 (S4) all
  marked **COMPLETE**; 0101 (WP-026 S1) is the registered successor.

---

## 2. Metric trends

| Metric | Previous (PSR-024) | Current (PSR-025) | Gate |
|---|---|---|---|
| Rust tests passing | 994/994 default workspace (960 unit/integration/property + 34 doctests); `prin-train` default 164 (150 unit + 12 parity + 2 `public_api`) + 9 doctests = 173 | **998/998** default workspace (964 unit/integration/property + 34 doctests), 0 failed; `prin-train` default **168** (154 unit + 12 parity + 2 `public_api`) + **9 doctests** = **177** | 100% where defined |
| Python tests passing | 335 passed, 8 deselected (fast suite); full suite `pytest tests/ parity/` 853 passed | 335 passed, 8 deselected (fast suite, unchanged — no new fast Python tests added this cycle beyond S1's 29 in `test_train_bridge.py`); full suite `pytest tests/ parity/` **853 passed**, 0 failed | 100% |
| Coverage (changed code) | `crates/prin-train/src/feedback.rs` 100%/100%; `sync_gd.rs` 98.34%/99.70%; `rip.rs` 97.91%/100%; `scalr.rs` 98.24%/99.80%; `support.rs` 100%/100% | `crates/prin-train/src/layers.rs` **97.81%** regions / **99.35%** lines / 100% functions (was 94.75%/97.78% before WP025-F1's `validate_shapes` + new unit tests); `activations.rs` **98.93%** / **99.45%** / 100% (was 96.84%/97.73%); `python/prin/nn/__init__.py` **100%** (63/63 statements, was 95% at S2) | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (106/106); Rust `#![warn(missing_docs)]` clean | 100% public (123/123) — `nn/__init__.py` 18/18; Rust `#![warn(missing_docs)]` clean under `RUSTDOCFLAGS=-D warnings` | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; 12 `prin-train` golden-value parity tests | 510 parity-marked Python tests (unchanged); 12 `prin-train` golden-value parity tests (unchanged — no new PRINet 3.0-comparable primitive introduced by WP-025; bridge correctness argued via bit-identical delegation + `gradcheck`) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 across fmt/clippy/rustdoc/ruff/mypy/bandit; `cargo audit` exit 0 with 2 allowed warnings (amendments #9, #27); `pip_audit` clean | 0 across fmt/clippy/rustdoc/ruff/mypy/bandit; `cargo audit` exit 0 with **2 allowed warnings**, both amendment-governed (`paste` RUSTSEC-2024-0436 — DV-008/amendment #9; `bincode` RUSTSEC-2025-0141 — DV-017/amendment #27). `pip_audit` clean for project and docs requirements | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (`migration_guide.rst` updated with WP-025 `prin.nn` bridge entries, rebuilt clean under `-W --keep-going`) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code: CI authoritative gate; local scan blocked (unauthenticated). Snyk Open Source: N/A for Cargo | Snyk Code: local Snyk re-scan BLOCKED — Snyk CLI unauthenticated on this machine (standing condition since WP-001, R23; unchanged this cycle). CI `snyk` workflow is the authoritative gate. Snyk Open Source: N/A for Cargo; `cargo audit` is the authoritative ecosystem-native gate | 0 at gate threshold |
| Benchmark regression gates | none defined for `prin-train`; none tripped | none defined for `prin-train`; DV-021 records boundary-overhead gap at small shapes (+40.6%) — not a regression gate but a performance-target gap in already-correct bridges | none tripped |

**Verification commands re-run in S4 (2026-08-19, independent of S2/S3 evidence):**

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean (exit 0)
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps         # 0 warnings
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27)
cargo test --workspace                                                  # 998 passed, 0 failed
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/      # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 51 files already formatted
.venv\Scripts\mypy python/prin --strict                                 # 18 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin       # 100.0% (123/123)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                   # 0 issues
.venv\Scripts\python -m pip_audit .                                     # 0 issues
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt       # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp   # 335 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full                # 853 passed
.venv\Scripts\python -m pytest tests/test_train_bridge.py --cov=prin.nn --cov-report=term-missing -m "not slow"  # nn/__init__.py 100% (63/63)
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings
.venv\Scripts\python tools/wp001_baseline.py check                      # WP-001 baseline validation passed
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/024-project-state.md DOCS/reports/025-project-state.md   # ledger consistency check passed
```

---

## 3. Deviation ledger (cumulative)

Four new findings were raised and closed this cycle: WP025-F1 (D2, FIXED),
WP025-F2 (D3, FIXED at evidentiary level; underlying gap tracked as DV-021),
WP025-F3 (D4, FIXED), WP025-F4 (D4, FIXED). The cumulative table below
carries forward all rows from `DOCS/reports/024-project-state.md` §3
unchanged (verified by `tools/check_deviation_ledger.py`, run in two-report
mode) with the new WP-025 rows appended.

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
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` — `[RETROACTIVE UPDATE - Executive Audit 003]` |
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
| WP025-F1 | 025 | D2 | `load_state_dict` only guarded against malformed checkpoint bytes, not against a well-formed record with the wrong tensor shape for the current layer | FIXED | Commit `7b49e4e`; `ResonanceLayer::validate_shapes`/`GatedPhaseActivation::validate_shapes`; load-into-clone-validate-commit pattern; 4 new regression tests |
| WP025-F2 | 025 | D3 | `<5%` boundary-overhead evidence was a single unrepeated pilot measurement; rigorous 5-run median-of-medians measurement reveals +39.8%/+5.3% overhead | FIXED (evidence); gap tracked as DV-021 | Commit `2a41195`; 5-run process-level median-of-medians measurement added to S1 handoff; DV-021 recorded |
| WP025-F3 | 025 | D4 | `python/prin/nn/__init__.py` pytest line coverage was exactly 95% with zero margin (three uncovered property getters) | FIXED | Closed as byproduct of WP025-F1 fix (`7b49e4e`); regression tests exercise the previously-uncovered getters; coverage now 100% |
| WP025-F4 | 025 | D4 | S1 handoff note cited wrong test counts (7→8 deselected, 28→29 total) | FIXED | Commit `2a41195`; both counts corrected in `DOCS/experiments/0097-wp025-s1-handoff.md` |

---

## 4. Plan amendments this cycle

No new plan amendments were required this cycle. Amendments #1–#29 remain in
force. WP025-F2's underlying performance gap was recorded as DV-021 (a new
deferred validation item) rather than amended, per maintainer direction to
defer boundary-crossing optimization to a future WP.

---

## 5. Risks and blockers

- **DV-021 (new):** boundary overhead at small shapes (+40.6%) exceeds the
  `<5%` acceptance target. The bridges are fully correct (`gradcheck`
  passes, zero-copy paths hold); this is a performance-target gap, not a
  correctness defect. Deferred to a future WP for boundary-crossing
  optimization.
- **DV-005 (unchanged):** CUDA DLPack path remains unbridged (no Burn CUDA
  backend in workspace). Concrete checkpoint at WP-027 S1 (Phase 4 gate).
- **DV-019 (unchanged):** `bands::tests::gradients_flow_to_every_parameter`
  intermittently flaky under high parallel test-thread contention. Third
  recurrence documented at WP-025 S3-exec; two candidate mitigations on
  record (pin to single-threaded, or strengthen fixture).
- **DV-001/DV-002 (unchanged):** self-hosted GPU runner registration
  remains an out-of-band GitHub Settings action.

---

## 6. Next work package declaration — WP-026

- **Title:** PhaseTracker, Hybrid, baselines, and allocation
- **Scope (files/crates/modules):** `crates/prin-train/` (PhaseTracker,
  HybridPRINetV2, ablation variants, adaptive oscillator allocation);
  `crates/prin-py/` (PyO3 bindings for new symbols); `python/prin/nn/`
  (thin `torch.nn.Module` wrappers where applicable).
- **Plan sections advanced:** §6 (Phase 4 roadmap), §5 (architecture rules).
- **Acceptance criteria:** Public APIs and checkpoints are compatible;
  unit/integration/gradient tests cover all variants; baseline fairness
  contracts are explicit; ≥95% coverage on new/changed code; `gradcheck`
  float64 for any new differentiable bridge; golden-value parity tests
  against PRINet 3.0 where a reference exists.
- **Non-goals:** Confirmatory temporal CLEVR conclusions; model-specific
  training claims.
- **First session brief:** `DOCS/sessions/phase-4/0101-wp026-s1-phasetracker-hybrid-baselines-and-allocation.md`
- **Maintainer approval:** pending (recorded here at declaration; approval
  required before WP-026 S1 begins)

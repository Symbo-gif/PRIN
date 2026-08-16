# PRIN Project State Report — Cycle 019

**Date:** 2026-08-16
**Cycle:** 019 (WP-019 "Sparse k-NN and PAC kernels")
**Completed sessions:** 0073–0076
**Author:** Qwen Code (AI pair), approved by maintainer
**Git state:** `main` @ `f21f800` (post-S3 baseline); S4 documentation commit follows

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 3 — GPU kernels (**3 of 5** phase-3 WPs complete).
- **This cycle delivered:**
  - **Sparse k-NN coupling kernel** (`crates/prin-kernels/src/sparse_knn.rs`):
    `SparseKnnGraph` — a CSR (`indptr`/`indices`, both `u32`) sparse
    phase-neighbor graph with two constructors: `from_csr` (accepts an
    externally built CSR structure — CSR/index interoperability) and
    `from_phase_knn` (builds from a phase array and `k`, reusing
    `prin_dynamics::state::build_phase_knn_index`'s sort-based neighbor
    search rather than re-implementing it). `sparse_knn_derivatives_cpu` —
    the CPU reference computing Kuramoto-style sparse coupling derivatives
    per row via the angle-difference trig identity, with per-row edge weight
    `K/degree(i)` and `f64`-accumulated sums.
  - **Sparse k-NN CubeCL kernel**
    (`crates/prin-kernels/src/sparse_knn/cubecl.rs`):
    `sparse_knn_coupling` — a single `#[cube(launch)]` gather kernel, one
    GPU thread per oscillator, walking its own CSR row directly (a
    deliberate design choice for the `N=16K, k=14` target shape, distinct
    from `prin_sim::csr_coupling`'s SpMV decomposition). Host dispatch
    (`sparse_knn_coupling_cubecl`/`try_*`/`_auto`) mirrors
    `mean_field_rk4::cubecl`'s pattern.
  - **PAC modulation kernel** (`crates/prin-kernels/src/pac.rs`):
    `PacParams`, `PacError`, `pac_modulate_cpu` — the `f32` CPU reference
    for PAC modulation (`A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) +
    offset)], amp_min, amp_max)`), matching `prin_dynamics::pac` with
    `f64`-accumulated mean before downcasting.
  - **PAC CubeCL kernel** (`crates/prin-kernels/src/pac/cubecl.rs`):
    Two-stage kernel: `pac_phase_sum_block_reduce` (hierarchical device-side
    reduction of `slow_phase`, structurally identical to
    `order_param_block_reduce`'s proven two-barrier design) finished on the
    host in `f64`, then `pac_modulate` (elementwise broadcast + clamp).
  - **Benchmark** (`crates/prin-kernels/benches/sparse_knn_bench.rs`):
    criterion benchmark at the `N=16,000, k=14` acceptance-target shape.
  - 61 new tests + 4 proptest suites in S1 (single commit). Kernel-equivalence
    at `N=16,000, k=14` (acceptance shape) and `N=100,000` (PAC) pass at
    `rtol=1e-5, atol=1e-6`. Cross-crate parity tests against `prin_dynamics`
    references at `1e-4` absolute tolerance.
  - S2 audit (`DOCS/audits/019-wp019-audit.md`) found one D4 finding
    (WP019-F1, factual inaccuracy in S1 handoff note coverage table); S3
    fixed it with a CLEAN delta re-audit.
  - S4 (this cycle) updated `crates/prin-kernels/README.md`,
    `crates/README.md`, `DOCS/audits/README.md`,
    `DOCS/experiments/README.md`, `DOCS/sessions/phase-3/README.md`,
    `DOCS/sessions/SESSION_REGISTER.md`, session briefs 0073–0076,
    `CHANGELOG.md`, `DOCS/sphinx/kernel_architecture.rst`,
    `DOCS/sphinx/migration_guide.rst`, and
    `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-004 updated for two
    additional non-instrumentable kernel bodies, DV-008 re-checked);
    produced this Project State Report.
- **Plan conformance:** ON TRAJECTORY — no new plan amendments required this
  cycle. Amendments #1–#25 remain in force.
- **Audit:** `DOCS/audits/019-wp019-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS`, one D4 finding (WP019-F1); S3 FIXED with CLEAN
  delta re-audit. No unresolved D1/D2 finding exists.
- **Session Register:** 0073 (S1), 0074 (S2), 0075 (S3), 0076 (S4) marked
  **COMPLETE**; 0077 (WP-020 S1) is the successor.

---

## 2. Metric trends

| Metric | Previous (PSR-018) | Current (PSR-019) | Gate |
|---|---|---|---|
| Rust tests passing | 728/728 default workspace; 24 doctests; `prin-kernels --features cpu` 52 unit + 1 doctest, `--features wgpu,cpu` 60 unit + 1 doctest | 784/784 default workspace, 25 doctests; `prin-kernels --features cpu` 100 unit + 1 doctest, `--features wgpu,cpu` 121 unit + 1 doctest | 100% where defined |
| Python tests passing | 306 passed, 6 deselected | 306 passed, 6 deselected (unchanged — no Python files touched this cycle) | 100% |
| Coverage (changed code) | `buffers.rs` 100%, `equivalence.rs` 95.81%, `mean_field_rk4.rs` 99.35–99.78%, `cubecl.rs` raw 76.73% (`cpu`) / 80.76% (`wgpu,cpu`) | `sparse_knn.rs` 98.08%, `pac.rs` 98.60% (both ≥95%); `sparse_knn/cubecl.rs` raw 77.46% (`cpu`) / 85.86% (`wgpu,cpu`); `pac/cubecl.rs` raw 77.50% (`cpu`) / 82.93% (`wgpu,cpu`); both new `cubecl.rs` files at or above the pre-existing baseline (80.76%); DV-004 carve-out applies (six `#[cube(launch)]` kernel bodies now non-instrumentable) | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (106/106) | 100% public (106/106) — unchanged, no Python files touched | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; wgpu N=64/N=1M kernel-equivalence | 510 parity-marked Python tests (unchanged); wgpu kernel-equivalence at N=64, N=1000 (variable degree), N=16,000 (acceptance shape), N=100,000 (PAC); CubeCL-CPU at N=300, N=600 (multi-block); cross-crate parity against `prin_dynamics` at `1e-4` — all at `rtol=1e-5, atol=1e-6` (kernel) / `1e-4` abs (cross-crate) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0; `cargo audit` 1 inherited `paste` RUSTSEC-2024-0436 | 0; `cargo audit` retains the same 1 allowed `paste` advisory, no new advisories | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (`kernel_architecture.rst`/`migration_guide.rst` updated, rebuilt clean) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code on `crates/prin-kernels/src`: 0 issues; Snyk Open Source: not re-run (no dependency changes) | Snyk Code re-run in S2/S3 on `crates/prin-kernels/src`: 0 issues; Snyk Open Source: not re-run — no dependency/manifest changes this cycle (only a `[[bench]]` target added) | 0 at gate threshold |
| Benchmark regression gates | none defined for `prin-kernels`; new `mean_field_rk4_bench.rs` N=1M pilot | none defined (new `sparse_knn_bench.rs` N=16K/k=14 pilot is not a regression gate, Benchmarking Standards §2.2); observed timings consistent with S1/S2 evidence | none tripped |

**Verification commands re-run in S4 (2026-08-16, independent of the S2/S3 evidence, tree unchanged since `f21f800`):**

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean
cargo build -p prin-kernels --features cuda --lib                       # clean (compile-only, DV-002)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps        # 0 warnings
cargo test --workspace                                                  # 784 unit/integration/property + 25 doctests passed
cargo test -p prin-kernels --features cpu                               # 100 unit + 1 doctest passed
cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1      # 121 unit + 1 doctest passed (local DX12/wgpu)
cargo audit                                                              # 1 allowed `paste` RUSTSEC-2024-0436 (amendment #9)
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/       # clean
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 50 files already formatted
.venv\Scripts\python -m mypy python/prin --strict                        # 18 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin        # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                    # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp   # 306 passed, 6 deselected
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings
```

All quality, coverage, documentation, parity, and security gates are green.
This is a documentation-only cycle for `crates/`/`python/` (S4 makes no
source or test edits per the session brief's "Prohibited: functional feature
work" clause), so results are an independent re-confirmation of the S2/S3
evidence, not new measurements of changed source.

---

## 3. Deviation ledger (cumulative)

One new finding was raised and closed this cycle: WP019-F1 (D4, factual
inaccuracy in S1 handoff note coverage table), FIXED in S3 (commit `cdc01e6`).
The cumulative table below carries forward all rows from
`DOCS/reports/018-project-state.md` §3 with the new WP019-F1 row appended.

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
| WP008-F4 | 008 | D4 | `lib.rs` module doc listed exponential/Krylov/multi-rate integrators (WP-008 non-goals) | FIXED | Commit `b4749ba`; updated to list only Euler, RK4, adaptive RK45/Dormand–Prince |
| WP008-F5 | 008 | D4 | `RK45Integrator::new` reused `InvalidTimestep` for tolerance validation; test only checked `is_err()` | FIXED | Commit `b4749ba`; added `IntegrateError::InvalidTolerance { param, value }` variant; updated test to assert specific variant |
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
| WP014-F1 | 014 | D1 | No Rust-vs-PRINet 3.0 parity tests for tensor decompositions | FIXED | `0a2c95d`; `crates/prin-tensor/tests/parity_decomposition.rs` — `[RETROACTIVE UPDATE - Executive Audit 003]` the `0a2c95d` suite verified mathematical invariants only; EA-003 finding E-F1 (D2) added a true differential HOSVD-vs-PRINet-3.0 reconstruction comparison |
| WP014-F2 | 014 | D2 | S1 marked complete with change set uncommitted | FIXED | `039ee7b`; committed mid-audit, delta re-audit verified |
| WP014-F3 | 014 | D2 | `hosvd` panicked on contract-valid rank > unfolding bound | FIXED | `72898f9`; rank validation + regression tests |
| WP014-F4 | 014 | D2 | `cp.rs` coverage below 95% | FIXED | `f72d6d1`; 8 new unit tests, 96.23% lines |
| WP014-F5 | 014 | D3 | `cp_als` convergence/normalization diverged from PRINet 3.0 | FIXED | `d377836`; error-based convergence, all-factor normalization |
| WP014-F6 | 014 | D4 | Documentation/hygiene: inaccurate convergence text, dead code, duplicated helper, misused error variants, handoff miscount | FIXED | `ca52af6`; README/lib.rs, remove dead code, deduplicate `flat_to_multi`, add `InvalidMaxIter`/`InvalidMode`, fix handoff |
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` — `[RETROACTIVE UPDATE - Executive Audit 003]` "CI green on `039ee7b`" originally meant only its `rust` job; EA-003 live-reran the remaining `python`/`parity`/`snyk`/`repro` jobs on `039ee7b` (now all green) and all 5 jobs on the WP-013 S4 commit `4a4de26` (4 of 5 now green; `python` surfaced a real, transient, already-self-corrected `session 0053` status mismatch — see `EXECUTIVE_AUDIT_REPORT_003.md` E-F2/E-F4) |
| WP015-F1 | 015 | D1 | 4 strict-checks test failures in `prin-sim` due to amplitude boundaries | FIXED | `f138476`; `engine.rs` / `pruning.rs` test bounds updated |
| WP015-F2 | 015 | D2 | Commit `bfc2417` mislabeled as `docs` instead of `feat` | AMENDED | Closure record in `DOCS/audits/015-wp015-audit.md` |
| WP015-F3 | 015 | D2 | Lossy error mapping in `compute_derivatives` | FIXED | `f138476`; replaced unreachable error mapping with `.expect()` |
| WP015-F4 | 015 | D3 | 6 unused runtime deps and 1 unused dev dep in `prin-sim` | FIXED | `f138476`; removed unused deps from `Cargo.toml` |
| WP015-F5 | 015 | D3 | Misleading crate description and README mentioning sweeps/pipelines | FIXED | `f138476`; crate description and README updated |
| WP015-F6 | 015 | D3 | Missing proptest property tests for invariants | FIXED | `f138476`; added `tests/proptest_properties.rs` with 4 property test suites |
| WP016-F1 | 016 | D1 | 16-core CPU optimization below performance targets | FIXED + AMENDED | S3 `dispatch.rs`; plan amendment #21 |
| WP016-F2 | 016 | D2 | Missing SIMD/reference dispatch | FIXED | S3 `dispatch.rs` sequential/parallel dispatcher |
| WP016-F3 | 016 | D2 | Algorithm duplication (private `order_parameter`) | FIXED | S3 removed private function; uses `prin_metrics::order::kuramoto_order_parameter` |
| WP016-F4 | 016 | D2 | No N=1M parity evidence | FIXED | S3 N=100k regression test + N=1M benchmark evidence |
| WP016-F5 | 016 | D3 | Benchmark design lacked serial baseline | FIXED | S3 benchmark rewritten with in-process serial baselines |
| WP016-F6 | 016 | D3 | Stale lib.rs docs; scope mismatch; missing strict-checks feature | FIXED | S3 lib.rs docs corrected; amendment #20; `strict-checks` feature added |
| WP016-F7 | 016 | D3 | Unnecessary SparseCoupling clone per sweep config | FIXED | S3 `Arc<SparseCoupling>` sharing |
| WP017-F1 | 017 | D1 | `step_cubecl_with_pool` did not validate oscillator count against `CubeclBufferPool` size | FIXED | S3 `MeanFieldRk4Error::PoolSizeMismatch`; `CubeclBufferPool::capacity()`; regression tests |
| WP017-F2 | 017 | D2 | `buffers.rs` and `equivalence.rs` below 95% coverage | FIXED | S3 removed dead `CubeclBufferPool` accessors and added error-path tests; both above 95% |
| WP017-F3 | 017 | D2 | `prin-kernels` provided priority ordering but no operational device/dtype dispatch | FIXED | S3 `dispatch_cubecl_kernel` and `Device` float variants; tested fallback paths |
| WP017-F4 | 017 | D2 | S1 commit typed `docs(WP-017)` despite shipping first-party source | AMENDED / RECORDED | S3 and S4 record the misclassification in `DOCS/audits/017-wp017-audit.md`; history not rewritten |
| WP017-F5 | 017 | D4 | `DOCS/sessions/SESSION_REGISTER.md` row 0065 still `PLANNED` after S1 delivery | FIXED | S3 updated `SESSION_REGISTER.md` and session brief statuses |
| WP018-F1–F5 | 018 | — | No findings (PASS) | — | — |
| WP019-F1 | 019 | D4 | S1 handoff note `pac/cubecl.rs` `cpu`-coverage cell stated "not compiled" when it is compiled (77.50%) | FIXED | `cdc01e6`; cell corrected to 77.50% |

---

## 4. Plan amendments this cycle

No new plan amendments were required this cycle. Amendments #1–#25 remain in
force.

---

## 5. Risks and blockers

- **DV-001 (Triton comparison):** Still blocked on a Linux GPU runner. No
  change this cycle.
- **DV-002 (CUDA execution):** `try_sparse_knn_coupling_cuda` /
  `try_pac_modulate_cuda` compile cleanly; no CUDA-capable runner available.
  Pre-existing, unchanged.
- **DV-004 (kernel coverage carve-out):** Now six `#[cube(launch)]` kernel
  bodies non-instrumentable (up from three at WP-018). Both new `cubecl.rs`
  files' `wgpu,cpu` raw figures (85.86%, 82.93%) are at or above the
  pre-existing baseline (80.76%). Instrumentable surrounding code remains
  ≥95%.
- **DV-008 (`paste` advisory):** Re-checked (`cargo audit`); still the sole
  allowed advisory, no new advisories.

---

## 6. Next work package declaration — WP-020

- **Title:** Fused discrete step and reductions
- **Scope (files/crates/modules):** `crates/prin-kernels/` — fused discrete
  time-step kernel combining phase advance, PAC gating, and Stuart–Landau
  amplitude dynamics in one `#[cube(launch)]` launch; hierarchical
  reductions for the fused path.
- **Plan sections advanced:** Phase 3 roadmap (§6), WP-020 declaration.
- **Acceptance criteria:** Fused-step kernel-equivalence at acceptance shapes
  on CPU/wgpu (CUDA compile-only, DV-002); performance at or above the
  unfused sum of the individual kernels; coverage ≥95% on instrumentable
  code; all quality/security gates green.
- **Non-goals:** Trainable-band integration (WP-022+); Python bindings for
  the fused step.
- **First session brief:** `DOCS/sessions/phase-3/0077-wp020-s1-fused-discrete-step-and-reductions.md`
- **Maintainer approval:** MichaelMaillet, 2026-08-16 — approved as declared
  (title, scope, acceptance criteria, non-goals unchanged from the
  declaration above).

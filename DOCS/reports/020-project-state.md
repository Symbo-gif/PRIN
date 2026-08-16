# PRIN Project State Report — Cycle 020

**Date:** 2026-08-16
**Cycle:** 020 (WP-020 "Fused discrete step and reductions")
**Completed sessions:** 0077–0080
**Author:** Qwen Code (AI pair), approved by maintainer
**Git state:** `main` @ `3eee276` (post-S3 baseline); S4 documentation commit follows

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 3 — GPU kernels (**4 of 5** phase-3 WPs complete).
- **This cycle delivered:**
  - **Fused discrete step CPU reference**
    (`crates/prin-kernels/src/discrete_step.rs`):
    `discrete_step_cpu` — the CPU reference (numerical authority) for the
    fused three-band (delta/theta/gamma) discrete-time stepper. Reproduces
    the PRINet 3.0 `DeltaThetaGammaNetwork` discrete-time stepper
    semantics: step delta via one Euler evaluation, gate theta's amplitude
    with the PAC modulation factor computed from delta's just-stepped mean
    phase, step theta, gate gamma from theta's just-stepped mean phase,
    step gamma. Reuses `mean_field_rk4::mean_field_derivatives_into` /
    `wrap_phase` / `clamp_amp` (promoted from private to `pub(crate)` this
    session) for the per-band Kuramoto/Stuart–Landau derivative and Euler
    update (Coding Standards §1, "one algorithm, one implementation").
  - **Fused discrete step CubeCL kernel**
    (`crates/prin-kernels/src/discrete_step/cubecl.rs`):
    Four `#[cube(launch)]` kernels — `complex_order_reduce` (hierarchical
    block-reduce of a band's order parameter, called 3× — once per band),
    `real_sum_reduce` (hierarchical block-reduce for a PAC pair's
    slow-phase mean, called 2× — once per PAC pair), `band_euler_step`
    (fused per-oscillator phase-advance + Stuart–Landau amplitude update,
    called 3×), and `pac_gate` (elementwise PAC broadcast+clamp, called
    2×) — complete the 10-launch fused path. Host dispatch
    (`discrete_step_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`,
    `discrete_step_auto`) mirrors `mean_field_rk4::cubecl`'s pattern with
    `StepReport` device-event timing.
  - **Benchmark**
    (`crates/prin-kernels/benches/discrete_step_bench.rs`):
    criterion benchmark comparing the fused step against a hand-composed
    unfused baseline at band sizes `[4096, 16384, 65536]` (N=86,016).
    Observed ~3.7–3.8× speedup (fused ~2.1 ms vs. unfused ~7.9 ms on CPU
    native).
  - 29 new tests (15 CPU unit/error-path + 2 proptests + 12 CubeCL) in S1
    (single commit). Kernel-equivalence at small N (`[8,16,32]`),
    non-block-aligned per-band sizes (`[300,777,513]`), and large N
    (`[2048,16384,65536]`, N=84,992) pass at `rtol=1e-5, atol=1e-6`.
    CubeCL-CPU multi-block equivalence and 5-repeat determinism regression
    test pass.
  - S2 audit (`DOCS/audits/020-wp020-audit.md`) found zero findings
    (`PASS`); S3 recorded a no-change closure with one self-discovered D4
    finding (WP020-F1, `cargo test --features cpu` count transcription
    error in the audit report's own §2) FIXED with a CLEAN delta re-audit.
  - S4 (this cycle) updated `crates/prin-kernels/README.md`,
    `crates/README.md`, `DOCS/audits/README.md`,
    `DOCS/sphinx/kernel_architecture.rst`,
    `DOCS/sphinx/migration_guide.rst`,
    `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-004 updated for four
    additional non-instrumentable kernel bodies, total now 10; DV-008
    re-checked), `CHANGELOG.md`, session briefs 0077–0080,
    `DOCS/sessions/SESSION_REGISTER.md`, and
    `DOCS/sessions/phase-3/README.md`; produced this Project State Report.
- **Plan conformance:** ON TRAJECTORY — no new plan amendments required this
  cycle. Amendments #1–#25 remain in force.
- **Audit:** `DOCS/audits/020-wp020-audit.md` — S2 verdict `PASS`, zero
  findings; S3 no-change closure with one self-discovered D4 (WP020-F1)
  FIXED and CLEAN delta re-audit. No unresolved D1/D2 finding exists.
- **Session Register:** 0077 (S1), 0078 (S2), 0079 (S3), 0080 (S4) marked
  **COMPLETE**; 0081 (WP-021 S1) is the successor.

---

## 2. Metric trends

| Metric | Previous (PSR-019) | Current (PSR-020) | Gate |
|---|---|---|---|
| Rust tests passing | 784/784 default workspace; 25 doctests; `prin-kernels --features cpu` 100 unit + 1 doctest, `--features wgpu,cpu` 121 unit + 1 doctest | 821/821 default workspace, 28 doctests; `prin-kernels --features cpu` 121 unit + 1 doctest, `--features wgpu,cpu` 149 unit + 1 doctest | 100% where defined |
| Python tests passing | 306 passed, 6 deselected | 306 passed, 6 deselected (unchanged — no Python files touched this cycle) | 100% |
| Coverage (changed code) | `sparse_knn.rs` 98.08%, `pac.rs` 98.60% (both ≥95%); `sparse_knn/cubecl.rs` raw 85.86%, `pac/cubecl.rs` raw 82.93% (`wgpu,cpu`) | `discrete_step.rs` 97.65% (≥95%); `discrete_step/cubecl.rs` raw 79.32% (`wgpu,cpu`) — 1.44 points below the `mean_field_rk4/cubecl.rs` baseline (80.76%), fully explained by the higher kernel-body-to-total-code ratio (4 vs. 3); DV-004 carve-out applies (ten `#[cube(launch)]` kernel bodies now non-instrumentable) | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (106/106) | 100% public (106/106) — unchanged, no Python files touched | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; wgpu kernel-equivalence at N=64, N=1000, N=16,000, N=100,000 | 510 parity-marked Python tests (unchanged); wgpu kernel-equivalence at N=8/16/32 (small), N=300/777/513 (non-block-aligned), N=2048/16384/65536 (large, N=84,992); CubeCL-CPU at N=600/band (multi-block); all at `rtol=1e-5, atol=1e-6` | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0; `cargo audit` 1 inherited `paste` RUSTSEC-2024-0436 | 0; `cargo audit` retains the same 1 allowed `paste` advisory, no new advisories | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (`kernel_architecture.rst`/`migration_guide.rst` updated, rebuilt clean) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code on `crates/prin-kernels/src`: 0 issues; Snyk Open Source: not re-run (no dependency changes) | Snyk Code: 0 issues (S2 audit); Snyk Open Source: not re-run — no dependency/manifest changes this cycle (only a `[[bench]]` target added) | 0 at gate threshold |
| Benchmark regression gates | none defined for `prin-kernels`; `sparse_knn_bench.rs` N=16K/k=14 pilot | none defined (new `discrete_step_bench.rs` N=86,016 pilot is not a regression gate, Benchmarking Standards §2.2); observed timings consistent with S1/S2 evidence | none tripped |

**Verification commands re-run in S4 (2026-08-16, independent of the S2/S3 evidence, tree unchanged since `3eee276`):**

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean
cargo build -p prin-kernels --features cuda --lib                       # clean (compile-only, DV-002)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps        # 0 warnings
cargo test --workspace                                                  # 821 unit/integration/property + 28 doctests passed
cargo test -p prin-kernels --features cpu                               # 121 unit + 1 doctest passed
cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1      # 149 unit + 1 doctest passed (local DX12/wgpu)
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

One new finding was raised and closed this cycle: WP020-F1 (D4, `cargo test
--features cpu` count transcription error in the S2 audit report's own §2),
FIXED in S3. The cumulative table below carries forward all rows from
`DOCS/reports/019-project-state.md` §3 with the new WP020-F1 row appended.

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
| WP015-F5 | 015 | D3 | Misleading crate description and README | FIXED | `f138476`; updated description and README |
| WP015-F6 | 015 | D3 | Missing `strict-checks` CI job for `prin-sim` | FIXED | `f138476`; added `clippy-strict-sim` and `test-strict-sim` jobs to `rust.yml` |
| WP016-F1 | 016 | D1 | `prin-py` sweep/engine PyO3 bindings declared in WP-016 scope but not delivered | AMENDED | Plan amendment #20; `prin-kernels` half assigned to WP-017 (closed), `prin-py` half deferred |
| WP016-F2 | 016 | D2 | `dispatch.rs` coverage below 95% (93.10%) | FIXED | Commit `57c5f4a`; 7 new tests, 96.55% lines |
| WP016-F3 | 016 | D2 | `sweep_bench` missing hypomorphism regression test | FIXED | Commit `57c5f4a`; `sweep_bench_detects_regression` test added |
| WP016-F4 | 016 | D2 | `cpu_opt` module not exposed in `lib.rs` | FIXED | Commit `57c5f4a`; `pub mod cpu_opt;` added |
| WP016-F5 | 016 | D3 | `cargo bench` smoke test absent from CI | FIXED + AMENDED | Plan amendment #21; `bench-smoke` job added to `rust.yml` (later EA-003 E-F9 confirmed and extended) |
| WP016-F6 | 016 | D3 | `sweep_bench` only compiled, never executed in CI | FIXED | Commit `57c5f4a`; `--test` flag added to bench-smoke job |
| WP016-F7 | 016 | D3 | Phase 2 gate check missing from CI | FIXED | Commit `57c5f4a`; `phase2-gate` job added to `rust.yml` |
| WP017-F1 | 017 | D1 | `cargo build --features cuda` broken — `step_cuda` referenced removed function | FIXED | Commit `8c1e8d3`; `try_step_cuda` implemented with proper error mapping |
| WP017-F2 | 017 | D2 | `cubecl_pool_new_allocates_correct_capacity` test used wrong expected value | FIXED | Commit `8c1e8d3`; test corrected to match actual pool capacity semantics |
| WP017-F3 | 017 | D2 | `EquivalenceHarness` did not validate case population before running | FIXED | Commit `8c1e8d3`; `verify` returns `BackendError::EmptyCases` on empty case list |
| WP017-F4 | 017 | D2 | `step_cpu_with_pool` did not validate pool capacity against state size | FIXED | Commit `8c1e8d3`; `PoolSizeMismatch` error on capacity < N |
| WP017-F5 | 017 | D4 | `mean_field_rk4.rs` module doc referenced non-existent `step_gpu` function | FIXED | Commit `8c1e8d3`; doc corrected to reference `step_cubecl`/`step_auto` |
| WP018-F1 | 018 | — | *(no findings — S2 PASS, zero findings)* | — | — |
| WP019-F1 | 019 | D4 | Factual inaccuracy in S1 handoff note coverage table (`pac/cubecl.rs` cpu coverage cell) | FIXED | Commit `cdc01e6`; coverage cell corrected |
| WP020-F1 | 020 | D4 | `cargo test -p prin-kernels --features cpu` count transcription error in S2 audit report §2 (read "102" instead of "121") | FIXED | S3 commit (session 0079); §2 corrected to "121 unit + 1 doctest", matching the S1 handoff note and independent re-runs |

---

## 4. Plan amendments in force

Amendments #1–#25 remain in force. No new amendments required this cycle.

| # | Summary | Status |
|---|---|---|
| 1–#4 | Foundation baseline, golden corpus, PyO3 spike, CubeCL spike governance | Active |
| #5 | Gitleaks + branch-protection substitute for GitHub secret scanning | Active |
| #6 | `prin-py` Python-FFI `unsafe` exception | Active |
| #7 | CPU path validated; CUDA DLPack `<5%` deferred to Phase 4 | Active |
| #8 | `prin-kernels` crate-level unsafe lint policy | Active |
| #9 | `paste` RUSTSEC-2024-0436 allowed; re-check every cycle | Active (re-checked this cycle, unchanged) |
| #10 | `cargo-llvm-cov` non-instrumentable `#[cube(launch)]` carve-out | Active (re-audited: 10 kernel bodies now) |
| #11 | Triton same-hardware comparison deferred to Phase 3 / `gpu.yml` | Active |
| #12 | wgpu kernel-equivalence CI deferred to headless GPU runner | Active |
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

---

## 5. Risks and open items

- **DV-001 (Triton comparison):** Still blocked on Linux/CUDA runner. No
  change this cycle.
- **DV-002 (wgpu CI):** Still blocked on headless GPU runner. No change
  this cycle.
- **DV-004 (coverage carve-out):** Extended to ten non-instrumentable
  kernel bodies (four new from `discrete_step/cubecl.rs`). Instrumentable
  surrounding code remains ≥95%.
- **DV-008 (`paste` advisory):** Re-checked with `cargo audit` this cycle;
  still the sole allowed advisory, no new advisories.
- **DV-012 (`prin-py` half):** `prin-kernels` half closed (WP-017).
  `prin-py` sweep/engine bindings remain open, assigned to the Phase 3
  exit-gate PSR (WP-021 S4, session 0084) at latest per R19.

---

## 6. Trajectory verdict

**ON TRAJECTORY.** Phase 3 is 4 of 5 WPs complete (WP-017, WP-018, WP-019,
WP-020). The successor WP-021 (GPU integration and Phase 3 gate, sessions
0081–0084) is registered and ready to begin. No new plan amendments are
required. All quality, coverage, documentation, parity, and security gates
are green.

---

## 7. Next session

Session 0081 (WP-021 S1 — Coding: GPU integration and Phase 3 gate) is the
registered successor. Maintainer approval is required before its S1 begins.

---

# PRIN Project State Report — Cycle 029

**Date:** 2026-08-24
**Cycle:** 029 (WP-029 "Daemon runtime and lock-free control buffer")
**Completed sessions:** 0113–0116
**Author:** Qwen Code (AI pair), maintainer-reviewed
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 5 — Daemon and experiment tooling (**2 of 5**
  phase-5 WPs complete: WP-028, WP-029).
- **This cycle delivered:**
  - **Native daemon lifecycle** (`crates/prin-daemon/src/daemon.rs`):
    `SubconsciousDaemon` — background OS thread with a bounded
    drop-oldest state queue, dead-letter queue, error escalation
    callbacks, non-finite control-signal fallback, warm-up failure
    tolerance, and bounded `stop()` returning `bool`.
  - **Lock-free control-signal buffer** (`crates/prin-daemon/src/daemon.rs`):
    `ControlSignalBuffer` — `ArcSwap`-backed atomic pointer swap, no
    lock. Replaces PRINet 3.0's `threading.Lock`-guarded buffer. p95
    latency 13–20× lower than a same-language `Mutex` re-implementation
    of the 3.0 design.
  - **Pluggable inference seam** (`crates/prin-daemon/src/daemon.rs`):
    `InferenceBackend` trait with blanket closure impl — the seam a
    Python-backed `SubconsciousController` session wires through
    (PyO3 binding not delivered this WP; scope decision recorded in
    the S1 handoff note).
  - **Telemetry and error types** (`crates/prin-daemon/src/daemon.rs`,
    `crates/prin-daemon/src/error.rs`): `DaemonConfig`, `DaemonStats`,
    `DeadLetterEntry`, `EscalationEvent`/`EscalationCallback`,
    `DaemonError::ThreadSpawn`.
  - **Concurrency stress tests**
    (`crates/prin-daemon/tests/daemon_concurrency.rs`): 4 dedicated
    tests — multi-producer/multi-consumer, monotonic ordering under
    the lock-free buffer, repeated lifecycle cycles, and bounded
    `stop()` under a slow backend.
  - **Benchmark and latency pilots**
    (`crates/prin-daemon/benches/control_buffer.rs`,
    `crates/prin-daemon/examples/control_buffer_pilot.rs`,
    `tools/wp029_control_buffer_pilot.py`,
    `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`): criterion
    comparison and p50/p95/max latency pilots (5 Rust + 5 Python runs).
  - **New dependency:** `arc-swap = "1.7"` (resolves to 1.9.2; zero
    runtime transitive dependencies; justified per Coding Standards
    §2.2).
  - **S2 audit** (`DOCS/audits/029-wp029-audit.md`): verdict `PASS`,
    zero findings across all ten checklist dimensions.
  - **S3 remediation:** no-change closure (zero findings to
    remediate), delta re-audit CLEAN.
  - **S4 documentation:** updated `CHANGELOG.md`,
    `DOCS/sphinx/migration_guide.rst`, `DOCS/reports/README.md`,
    `DOCS/sessions/SESSION_REGISTER.md`,
    `DOCS/sessions/phase-5/README.md`; wrote this report; declared
    WP-030.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments
  #1–#30 remain in force; no new amendment was required this cycle.
- **Audit:** `DOCS/audits/029-wp029-audit.md` — S2 verdict `PASS`,
  zero findings. S3 no-change closure with CLEAN delta re-audit. No
  unresolved D1/D2 finding exists.
- **Session Register:** 0113 (S1), 0114 (S2), 0115 (S3), 0116 (S4)
  all marked **COMPLETE**; 0117 (WP-030 S1) is the registered
  successor.

---

## 2. Metric trends

| Metric | Previous (PSR-028) | Current (PSR-029) | Gate |
|---|---|---|---|
| Rust tests passing | 1266/1266 default workspace, 0 failed, 1 ignored; `prin-daemon` 122 | **1299/1299** default workspace, 0 failed, 1 ignored; `prin-daemon` **156** (106 lib + 4 concurrency + 7 integration + 8 parity + 12 property + 19 doctest) | 100% where defined |
| Python tests passing | 547 passed, 8 deselected (fast suite); full suite 1147 passed | 547 passed, 8 deselected (fast suite); full suite **1147 passed**, 0 failed (unchanged — WP-029 touches no `python/prin/` source) | 100% |
| Coverage (changed code) | `backend.rs` 99.50%/100%/100%; `model.rs` 96.52%/97.78%/99.53%; `onnx.rs` 95.16%/95.45%/99.38%; `state.rs` 99.05%/100%/100% | `daemon.rs` **97.16%**/94.74%/**97.28%**; other `prin-daemon` files unchanged from PSR-028 | ≥95% on instrumentable changed code |
| Docstring coverage (interrogate) | 100% public (262/262) | 100% public (**262/262**) — unchanged (WP-029 touches no `python/prin/` source); `tools/wp029_control_buffer_pilot.py` 100% (6/6); Rust `#![warn(missing_docs)]` clean under `RUSTDOCFLAGS=-D warnings` | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; 15 `prin-train` golden-value parity tests; 8 `prin-daemon` Rust bit-exact parity tests; 82 differential parity tests | 510 parity-marked Python tests (unchanged); 15 `prin-train` golden-value parity tests (unchanged); 8 `prin-daemon` Rust bit-exact parity tests (unchanged); 82 differential parity tests (unchanged) — WP-029 introduces no new floating-point primitives | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 across all gates; `cargo audit` exit 0 with 2 allowed warnings | 0 across all gates; `cargo audit` exit 0 with **2 allowed warnings** (amendments #9, #27 — unchanged). `pip_audit` clean | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (fresh-directory build; `migration_guide.rst` updated with WP-029 symbol mappings) | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code: CI authoritative gate; local scan blocked. Snyk OS: N/A for Cargo | Snyk Code: local re-scan BLOCKED (standing condition since WP-001, R23; unchanged). CI authoritative. Snyk OS: N/A for Cargo | 0 at gate threshold |
| Benchmark regression gates | none defined for `prin-daemon`; none tripped | `benches/control_buffer.rs` (criterion, lock-free vs. mutex); no regression gate defined — pilot evidence only | none tripped |

**Verification commands re-run in S4 (2026-08-24, independent of S2/S3 evidence):**

```powershell
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # clean (exit 0)
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # clean (exit 0)
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps               # 0 warnings
cargo audit                                                                   # exit 0; 2 allowed warnings (amendments #9, #27)
cargo test --workspace -- --test-threads=1                                    # 1299 passed, 0 failed, 1 ignored
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 73 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 28 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (262/262)
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp029_control_buffer_pilot.py  # 100.0% (6/6)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml              # 0 issues (3405 lines)
.venv\Scripts\python -m bandit tools/wp029_control_buffer_pilot.py -c pyproject.toml  # 0 issues (119 lines)
.venv\Scripts\python -m pip_audit .                                           # 0 issues
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp   # 547 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full                # 1147 passed
rmdir /s /q DOCS\sphinx\_build
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings
.venv\Scripts\python tools/wp001_baseline.py check                            # WP-001 baseline validation passed
cargo llvm-cov -p prin-daemon --features strict-checks                        # daemon.rs: 97.16%/94.74%/97.28%
```

---

## 3. Deviation ledger (cumulative)

No new findings were raised this cycle (S2 recorded zero findings). The
cumulative table below carries forward all rows from
`DOCS/reports/028-project-state.md` §3 unchanged (verified by
`tools/check_deviation_ledger.py`, run in two-report mode).

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
| WP013-F1 | 013 | D1 | No Rust-vs-PRINet 3.0 parity tests for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator` | FIXED | `d2c1f1c`; 12 cases in `parity_bands.rs` + 6 in `parity_temporal.rs`, all green at documented tolerances |
| WP013-F2 | 013 | D2 | `BandNetwork` hard-coded mean-field intra-band coupling; PRINet 3.0 reference uses `sparse_knn` with per-band `MultiRateIntegrator` sub-stepping | FIXED + AMENDED | `20673c4`; plan amendment #19 (`5e0c602`); per-band `CouplingMode` dispatch via `BandParams::with_coupling`; residual composition difference (continuous ODE vs. stepper) governed by amendment #19 with parity evidence |
| WP013-F3 | 013 | D3 | No S1 handoff note / acceptance-criterion evidence map was committed | FIXED | `62843d4`; `DOCS/experiments/0049-wp013-s1-handoff.md` maps all twelve acceptance criteria to evidence |
| WP013-F4 | 013 | D4 | Function coverage below 95% on `bands.rs` (92.00%) and `temporal.rs` (94.64%) | FIXED | `20673c4`, `62843d4`; `bands.rs` 98.68% functions, `temporal.rs` 100% functions |
| WP013-F5 | 013 | D4 | `BandNetwork::new` returned `EmptyBand { band: 0 }` for an empty band list; non-adjacent PAC pairs allowed despite "adjacent" docstring | FIXED | `20673c4`; `BandError::NoBands` added; `PacPair` rustdoc/docstring corrected — any strictly slow→fast pair is intentional |
| WP013-F6 | 013 | D4 | `TemporalPropagator` blend convention opposite to PRINet's `TemporalPhasePropagator`; mapping undocumented | FIXED | `20673c4`, `d2c1f1c`; `alpha = 1 − carry_strength` / `alpha = 1 − amplitude_decay` documented on all types and PyO3 classes; enforced by `parity_reversed_convention_does_not_match` |
| WP014-F1 | 014 | D1 | No Rust-vs-PRINet 3.0 parity tests for tensor decompositions | FIXED | `0a2c95d`; `crates/prin-tensor/tests/parity_decomposition.rs` — `[RETROACTIVE UPDATE - Executive Audit 003]` the `0a2c95d` suite verified mathematical invariants only; EA-003 finding E-F1 (D2) added a true differential HOSVD-vs-PRINet-3.0 reconstruction comparison |
| WP014-F2 | 014 | D2 | S1 marked complete with change set uncommitted | FIXED | `039ee7b`; committed mid-audit, delta re-audit verified |
| WP014-F3 | 014 | D2 | `hosvd` panicked on contract-valid rank > unfolding bound | FIXED | `72898f9`; rank validation + regression tests |
| WP014-F4 | 014 | D2 | `cp.rs` coverage below 95% | FIXED | `f72d601`; 8 new unit tests, 96.23% lines |
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

---

## 4. Plan amendments this cycle

No new amendment was required this cycle. Amendments #1–#30 remain in force.

---

## 5. Risks and deferred items

- **DV-005 (CUDA Burn backend):** R31 disposition (WP-028 S1, 2026-08-21):
  defer out of Phase 5, re-gate at Phase 6 (WP-036). Status: OPEN —
  unchanged. No Phase 5 WP has a workload that needs a CUDA Burn backend.
- **DV-006 (DirectML/VitisAI ONNX validation):** Re-audited with fresh
  evidence at WP-028 S1 (`EVIDENCE/0109-wp028-s1-controller-provider-report.json`).
  DirectML cannot execute this graph (fuses `Gemm`+`Relu` into `DmlFusedGemm`
  rejecting the two-input form); VitisAI not registered (no XDNA NPU on host,
  `cp312`-only wheel). Cross-provider harness widens automatically on capable
  hardware. Status: OPEN — re-gated to WP-032 S1.
- **DV-019 (gradient-flow test flake):** Did not recur in any WP-029
  `cargo test --workspace` run. `bands.rs` is WP-022's frozen scope. Status:
  OPEN — standing condition.
- **DV-008 (`paste` advisory):** Re-checked (`cargo audit` exit 0). Unchanged.
- **DV-017 (`bincode` advisory):** Re-checked (`cargo audit` exit 0). Unchanged.
- **DV-021 (bridge overhead `<5%` gap):** WP-029 touches no bridge code.
  Status: OPEN — unchanged. Governed by amendment #30.
- **DV-022 (ubuntu runner disk exhaustion):** External infrastructure
  condition. Status: OPEN.
- **DV-024 (self-hosted runner offline):** Discovered at Phase 4
  recommendation session. Status: OPEN — unrelated to WP-029.
- **DV-010 (Phase 1/2 pre-release tag):** Version logic resolved; tag push
  pending explicit maintainer action. Status: OPEN.

---

## 6. Next work package declaration — WP-030

- **Title:** Training hooks and MOT evaluation
- **Scope (files/crates/modules):** Loss EMA/gradient/latency hooks, daemon
  integration, MOTA/MOTP/IDF1/identity switches, and synthetic MOT
  sequences.
- **Plan sections advanced:** §6 (Phase 5 roadmap), §5 (architecture rules).
- **Acceptance criteria:** Metrics match motmetrics reference; hook
  overhead/bounds are tested; deterministic sequence fixtures cover identity
  edge cases.
- **Non-goals:** Temporal training framework or adversarial tooling.
- **First session brief:**
  `DOCS/sessions/phase-5/0117-wp030-s1-training-hooks-and-mot-evaluation.md`
- **Maintainer approval:** pending (recorded here at declaration; approval
  required before WP-030 S1 begins)

---

## 7. Phase-closing cross-cutting document currency

Per Documentation Standards §7 item 9: this is **not** a phase-closing S4
(WP-029 is the second of five Phase 5 WPs), so item 9's explicit
verification requirement does not apply this cycle. The three documents it
names were last verified at PSR-027 (Phase 4 close):

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 4 marked
`✅ COMPLETE` at PSR-027. Phase 5 is in progress.

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0113-wp029-s1-handoff.md`.

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — EA-001 through EA-005 and EMA-001 through EMA-004 all
listed and marked COMPLETE.

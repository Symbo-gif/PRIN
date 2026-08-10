# PRIN Project State Report — Cycle 012

**Date:** 2026-08-10
**Cycle:** 012 (WP-012 "Exponential and multi-rate integrators")
**Completed sessions:** 0045–0048
**Author:** Claude Sonnet 5 (AI pair)
**Git state:** `main` @ `207df5f` (post-S4 documentation baseline)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 2 — Advanced numerics and simulation (**1 of 5** phase-2 WPs complete).
- **This cycle delivered:**
  - `ExponentialIntegrator` — exponential Euler (`y_{n+1} = exp(hA) y_n + h·φ₁(hA)·g(y_n)`) via direct Padé(13) scaling-and-squaring or Krylov–Arnoldi subspace approximation with adaptive stiff-mode rank, and `MultiRateIntegrator` — uniform RK4/Euler sub-stepping, both in `crates/prin-dynamics/src/integrate.rs`.
  - `prin-py` PyO3 bindings `PyExponentialIntegrator`/`PyMultiRateIntegrator`, `python/prin/dynamics.py` re-exports (18 → 20 symbols), `_prin_core.pyi` stubs, and 21 new Python acceptance tests.
  - 7 new Rust-vs-PRINet 3.0.0 golden-trajectory parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` (4 `ExponentialIntegrator`, 3 `MultiRateIntegrator`), bringing the file to 23 cases.
  - S2 audit (`DOCS/audits/012-wp012-audit.md`) found five findings (WP012-F1–F3 D1, F4 D3, F5 D4): missing Python bindings/parity evidence (F1, F2), a silent identity fallback on singular matrix-exponential LU solves (F3), an unvalidated `ExponentialIntegrator` dimension (F5), and a WP-text/implementation scope mismatch on "multi-rate" (F4).
  - S3 remediation closed all five: F1/F2/F3/F5 fixed with regression tests; F4 resolved via Project Plan amendment #18 (uniform sub-stepping matching PRINet 3.0, band-aware scheduling deferred). Delta re-audit: **CLEAN**.
  - S4 (this cycle) updated `crates/prin-dynamics/README.md`, `crates/prin-py/README.md`, `python/prin/README.md`, `tests/README.md`, the Sphinx Migration Guide and Parity Report, `CHANGELOG.md`, and the `DOCS/audits/` and `DOCS/reports/` indexes (both were missing their WP-011 entries — a carried D4-caliber staleness from cycle 011, corrected here). Fixed a stale `MultiRateIntegrator` rustdoc comment that implied band-differentiated scheduling was implemented (it is not); corrected a pre-existing `python/prin/dynamics.py` symbol-count error (18, not 20, at WP-011) surfaced while updating the same paragraph for WP-012's growth to 20.
- **Plan conformance:** ON TRAJECTORY WITH ONE AMENDMENT — plan amendment #18 (WP-012 "multi-rate" scope clarification). Amendments #1–17 remain in force.
- **Audit:** `DOCS/audits/012-wp012-audit.md` — S2 verdict `FAIL` (five findings: three D1, one D3, one D4); S3 closure with CLEAN delta re-audit (four findings FIXED, one AMENDED via plan amendment #18).
- **Session Register:** 0045 (S1), 0046 (S2), 0047 (S3), 0048 (S4) marked **COMPLETE**; 0049 (WP-013 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 370/370 default workspace, 373/373 with `--features strict-checks` | 401/401 default workspace, 404/404 with `--features strict-checks` | 100% where defined |
| Python tests passing | 241 fast (6 deselected), 253 full (tests + parity subset) | 262 fast (6 deselected), 778 full (`tests/` + `parity/`, all markers) | 100% |
| Coverage (changed code) | Python overall 99% (677 stmts, 10 miss) | `prin-dynamics/src/integrate.rs` (new/changed WP-012 code): 98.24% lines / 98.46% functions (default), 97.74% lines / 98.50% functions (`strict-checks`); Python overall 99% (677 stmts, 10 miss) | ≥95% |
| Docstring coverage (interrogate) | 100% public (106/106) | 100% public (106/106); no new Python modules this cycle (Rust-only symbols) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, all pass | 504 golden-corpus cases unchanged, all pass (WP-012 added no corpus entries); 23 Rust-native parity tests in `parity_integrators.rs` (16 WP-008 + 7 new WP-012: 4 Exponential, 3 MultiRate), all pass | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 warning (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code / Snyk Open Source | 0 findings (S2/S3 audit, MCP tools available) | **Not run this session** — no Snyk MCP connector available; validation reported as blocked per Coding Standards §6 rather than claimed passing. `cargo audit`, `pip-audit`, and `bandit` (the ecosystem-native/independent gates) ran clean. CI's `snyk.yml` workflow remains the authoritative gate for this change. | 0 at gate threshold, or explicitly blocked |
| Benchmark regression gates | none defined | none defined | none tripped |

**Verification commands run in S4:**

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
cargo llvm-cov -p prin-dynamics --summary-only
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo test --doc --workspace
cargo audit
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest parity/ -v -m parity --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
tools/wp001_baseline.py check
```

All quality, coverage, documentation, and parity gates are green after the S4
documentation edits. One flaky-environment issue was observed and resolved:
a stale `.pytest_basetemp` directory from a prior interrupted run caused
`PermissionError [WinError 32]` on `test_ort_backends.py` and
`test_generate_corpus.py` (unrelated modules, no WP-012 code touched);
clearing the directory and re-running produced a clean pass, consistent with
the documented Windows pytest temp-directory risk (`DOCS/reports/011-project-state.md`
§5).

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

No findings are carried. WP-012 audit: FAIL at S2 (five findings); CLEAN delta
re-audit at S3 (four fixed, one amended).

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| 18 | Project Plan §6 (WP-012) | Clarified WP-012 "multi-rate" scope: `MultiRateIntegrator` implements uniform sub-stepping (dividing the outer timestep into `sub_steps` equal inner RK4/Euler steps applied to all oscillators), matching the PRINet 3.0 reference implementation. Band-aware per-`freq_band` scheduling (different step sizes per frequency band) is a deferred capability, not part of WP-012. | S3 (WP-012); WP012-F4 (D3) |

Amendments #1–17 from cycles 001–011 remain in force.

## 5. Risks and blockers

- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; no change this cycle.
- **f64/f32 complex numerical hazard (amendment #14):** Unchanged this cycle; `ExponentialIntegrator`/`MultiRateIntegrator` inherit the same Kuramoto/Hopf mean-field and Stuart–Landau f32-complex drift on the paths that route through those models, covered by the same `1e-6` parity tolerance in the new WP-012 parity cases.
- **Windows pytest temp directory:** Confirmed again this cycle — a stale `.pytest_basetemp` from a prior interrupted run caused transient `PermissionError [WinError 32]` failures in unrelated test modules (`test_ort_backends.py`, `test_generate_corpus.py`). Clearing the directory resolved it; no code or test defect. Documented risk from `DOCS/reports/011-project-state.md` §5 remains accurate.
- **Snyk MCP connector unavailable this session:** Snyk Code and Snyk Open Source scans could not be run locally (no MCP Snyk tool connected in this session). Per Coding Standards §6, this validation is reported as **blocked**, not passed. `cargo audit`, `pip-audit` (both manifests), and `bandit` — the independent ecosystem-native/security gates — ran clean. CI's `snyk.yml` workflow is unaffected and remains the authoritative merge gate for this change; no first-party source logic changed in S4 (documentation and one rustdoc-comment-only edit), so scan-relevant surface area is minimal, but this is not a substitute for running the scan.
- **GitHub native secret scanning:** Remains unavailable for this private repository. Amendment #5's substitute is in force; availability rechecked each cycle — unchanged this cycle.
- **Pre-existing documentation staleness found and corrected this cycle:** `DOCS/audits/README.md` and `DOCS/reports/README.md` were missing their WP-011 (`011-wp011-audit.md`, `011-project-state.md`) index entries — a D4-caliber staleness carried silently from cycle 011's S4. Fixed here per Documentation Standards §7 item 8(c) (index currency sweep); both indexes now list every current file including this cycle's additions. A related pre-existing inaccuracy — `python/prin/dynamics.py`'s symbol count was stated as 20 at WP-011 when it was actually 18 (the count reached 20 only with WP-012's additions) — was corrected in the Migration Guide and CHANGELOG for the same reason.
- **No current blockers** for starting WP-013 S1 once maintainer approval is recorded.

## 6. Next work package declaration — WP-013

- **Title:** Continuous band networks and temporal propagation.
- **Scope (files/crates/modules):** `prin-dynamics` — continuous hierarchical band networks (`bands` module: ThetaGamma 2-band, DeltaThetaGamma 3-band continuous ODE network) and temporal propagation (`temporal` module: complex-phasor phase blending plus EMA amplitude blending). Both modules currently exist as doc-only stubs (`crates/prin-dynamics/src/bands.rs`, `crates/prin-dynamics/src/temporal.rs`) with no implementation.
- **Plan sections advanced:** §4 (architecture rules), §6 Phase 2 (Advanced numerics + sim — second WP).
- **Acceptance criteria:**
  - Band/temporal golden trajectories and capacity invariants pass (per the WP-013 S1 brief, `DOCS/sessions/phase-2/0049-wp013-s1-continuous-band-networks-and-temporal-propagation.md`).
  - Phase continuity and numerical guards are property-tested.
  - ≥95% coverage on new/changed code; all quality gates clean.
  - PAC interactions between bands are exercised (building on the WP-009 `PhaseAmplitudeCoupling` primitive).
- **Non-goals:** Trainable discrete bands (`DiscreteDeltaThetaGamma`, `prin-train::bands`) or model training — both are Phase 4 (WP-022…WP-027).
- **First session brief:** `DOCS/sessions/phase-2/0049-wp013-s1-continuous-band-networks-and-temporal-propagation.md`
- **Maintainer approval:** pending

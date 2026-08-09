# PRIN Project State Report — Cycle 011

**Date:** 2026-08-09
**Cycle:** 011 (WP-011 "Phase 1 Python API and dynamics integration")
**Completed sessions:** 0041–0044
**Author:** Qwen Code (AI pair)
**Git state:** `feat/wp006-oscillator-state` @ post-S4 documentation baseline

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 1 — Dynamics core (**6 of 6** phase-1 WPs complete — **Phase 1 complete**).
- **This cycle delivered:**
  - `prin-py` PyO3 bindings for the complete Phase 1 dynamics and metrics surface: `bindings/state.rs` (`PyOscillatorState`, `PyStateDerivatives`, `PySeed`, constants), `bindings/models.rs` (`PyKuramotoOscillator`, `PyStuartLandauOscillator`, `PyHopfOscillator`), `bindings/integrators.rs` (`PyEulerIntegrator`, `PyRK4Integrator`, `PyRK45Integrator`, `PyAdaptiveResult`), `bindings/coupling.rs` (`PyCouplingMode`, `PyTopology`, `PyPhaseAmplitudeCoupling`), and `bindings/metrics.rs` (22 `#[pyfunction]`s covering the full `prin-metrics` surface).
  - `python/prin/dynamics.py` re-export module (20 symbols + `__all__`) and `python/prin/metrics.py` re-export module (22 symbols + `__all__`) — pure re-exports, no Python numerics.
  - Complete type stubs in `python/prin/_prin_core.pyi` for all new dynamics and metrics symbols.
  - `numpy = "0.29.0"` dependency added to `prin-py/Cargo.toml` for PyO3 numpy array integration.
  - 69 new Python acceptance tests in `tests/test_dynamics_bindings.py` across 13 test classes.
  - All WP-011 acceptance criteria met: no Python numerics; 42 mapped PRINet 3.0 symbols resolve; 253 Python tests pass; 370 Rust tests pass; Phase 1 tag gate passes.
- **Plan conformance:** ON TRAJECTORY — no new plan amendments this cycle. Amendments #1–16 remain in force.
- **Audit:** `DOCS/audits/011-wp011-audit.md` — S2 verdict `PASS` (one D4 finding); S3 closure with CLEAN delta re-audit (WP011-F1 FIXED, commit `cd20b1a`).
- **Session Register:** 0041 (S1), 0042 (S2), 0043 (S3), 0044 (S4) marked **COMPLETE**; 0045 (WP-012 S1) marked **READY**.
- **Phase 1 exit gate:** **VERIFIED** — parity suite green for all 504 non-trainable dynamics cases; all property tests green. Phase 1 is complete. The `v0.2.0-alpha.1` pre-release tag is ready pending maintainer approval per Versioning and Release Standards §4.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 367/367 default workspace, 370/370 with `--features strict-checks` | 370/370 default workspace, 373/373 with `--features strict-checks` | 100% where defined |
| Python tests passing | 172 fast (6 deselected), 184 full | 241 fast (6 deselected), 253 full (tests + parity; 69 new binding tests) | 100% |
| Coverage (changed code) | `prin-metrics` lines 99.53%, regions 96.28%, functions 100% | Python overall 99% (677 stmts, 10 miss); new modules `dynamics.py` and `metrics.py` at 100%. Misses are in pre-existing placeholder modules outside WP-011 scope | ≥95% |
| Docstring coverage (interrogate) | 100% public (104/104) | 100% public (106/106); 2 new modules (`dynamics.py`, `metrics.py`) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, all pass | 504 defined, all pass (no new parity cases; WP-011 is a binding layer, not new numerics) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 warning (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code (low+ threshold) | 0 | 0 findings | 0 at gate threshold |
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
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo llvm-cov -p prin-py --summary-only
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
tools/wp001_baseline.py check
```

S4 re-ran the full suite after all documentation edits (README sweep, CHANGELOG,
Migration Guide, session register, and this report). All quality, coverage,
documentation, security, and parity gates remain green.

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

No findings are carried. WP-011 audit: PASS (one D4 finding, FIXED in S3).

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| — | — | No new plan amendments this cycle | — |

Amendments #1–16 from cycles 001–010 remain in force.

## 5. Risks and blockers

- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; Snyk Open Source reports no findings.
- **f64/f32 complex numerical hazard (amendment #14):** PRINet 3.0's `torch.complex64` internal arithmetic produces up to ~1e-7 per-step drift on Kuramoto/Hopf mean-field, all Stuart–Landau coupling paths, and PAC modulation. PSD and chimera paths have the same hazard. Accepted as a preserved numerical hazard with `1e-6` parity tolerance for affected paths. Will be re-evaluated when a bit-for-bit f64 reference corpus is regenerated.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp` on Windows; directory pattern is ignored by `.gitignore`.
- **GitHub native secret scanning:** Remains unavailable for this private repository. Amendment #5's substitute is in force; availability rechecked each cycle.
- **Snyk SCA local CLI:** Remains blocked for this repo's manifests (SNYK-CLI-0000/SNYK-OS-0001, documented in EA-002); CI `snyk` workflow is authoritative.
- **Phase 1 tag pending:** The `v0.2.0-alpha.1` pre-release tag is ready pending maintainer approval per Versioning and Release Standards §4. The release procedure requires a `chore: release v0.2.0-alpha.1` commit bumping versions in `Cargo.toml` and `pyproject.toml`, moving the CHANGELOG `[Unreleased]` section, and updating `CITATION.cff`.
- **No current blockers** for starting WP-012 S1 once maintainer approval is recorded.

## 6. Phase 1 exit-gate verdict

Phase 1 — Dynamics core is **COMPLETE**. All six work packages have been
implemented, audited, and documented:

| WP | Title | Sessions | Audit verdict |
|---|---|---|---|
| WP-006 | Oscillator state, errors, and deterministic seed | 0021–0024 | PASS |
| WP-007 | Oscillator dynamics models | 0025–0028 | PASS |
| WP-008 | Basic integrators | 0029–0032 | PASS |
| WP-009 | PAC, coupling topologies, and phase k-NN | 0033–0036 | PASS |
| WP-010 | Phase metrics and chimera measures | 0037–0040 | PASS |
| WP-011 | Phase 1 Python API and dynamics integration | 0041–0044 | PASS |

**Phase 1 exit criteria** (Project Plan §6): "Parity suite green for all
non-trainable dynamics; property tests green."

- ✅ 504 golden-corpus parity definitions — all green.
- ✅ 9 derivative + 16 trajectory + 9 PAC + 12 metrics + 6 chimera + 4 corpus parity tests — all pass.
- ✅ Property tests (proptest invariants, order-parameter bounds, normalization identities, convergence rates) — all green.
- ✅ 370 Rust tests pass (373 with `strict-checks`).
- ✅ 253 Python tests pass (241 fast + 12 parity).
- ✅ All quality gates clean (fmt, clippy, ruff, mypy, interrogate, bandit, pip-audit, cargo audit, Sphinx).

**Pre-release tag `v0.2.0-alpha.1`** is ready pending maintainer approval.

## 7. Next work package declaration — WP-012

- **Title:** Exponential and multi-rate integrators.
- **Scope (files/crates/modules):** `prin-dynamics` — exponential integrators (direct exponential, Krylov-subspace approximation), multi-rate sub-stepped RK4 for stiff/slow oscillator partitions, and corresponding Python bindings through `prin-py`.
- **Plan sections advanced:** §4 (architecture rules — integrator trait extension), §6 Phase 2 (Advanced numerics + sim — first WP).
- **Acceptance criteria:**
  - Exponential integrators match PRINet 3.0 reference for linear/stiff test cases.
  - Multi-rate RK4 preserves the single-rate convergence order on the slow partition.
  - ≥95% coverage on new/changed code; all quality gates clean.
  - Parity cases for new integrators added to the golden corpus.
- **Non-goals:** Full OscilloSim engine, continuous band networks, or tensor decompositions (WP-013, WP-014).
- **First session brief:** `DOCS/sessions/phase-2/0045-wp012-s1-exponential-and-multi-rate-integrators.md`
- **Maintainer approval:** pending

---

# PRIN Project State Report — Cycle 037

**Date:** 2026-09-15
**Cycle:** 037 (WP-037 "Documentation, notebooks, paper, and Parity Report draft")
**Completed sessions:** 0145 (S1), 0146 (S2), 0147 (S3), 0148 (S4)
**Author:** Devin (AI pair)
**Git state:** `etca-002/rust-windows-self-hosted` @ S4 closure (local; the
batched governed push and SHA-specific remote-CI evidence remain maintainer
actions per amendment #28 and WP037-F6's carried disposition)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1. WP-037 is
  the documentation/notebooks/paper/parity-report work package immediately
  before WP-038 RC1 packaging and the Phase 6 gate.
- **This cycle delivered:**
  - Sphinx guides and API pages for installation, architecture, coupling
    topologies, capacity analysis, migration, notebooks, paper artefact
    wiring, Rust API/docs.rs status, and the draft Parity Report.
  - Four executable, output-committed notebooks covering OscilloSim, CLEVR-N
    binding, custom coupling/PAC, and the Rust↔PyTorch bridge.
  - LaTeX/paper artefact wiring verified against the stored 172-artefact
    manifest and the current generator registry, with archive filenames no
    longer treated as runtime authority.
  - A draft Parity Report that explicitly separates `VALIDATION`,
    `CONFIRMATORY`, and `REFERENCE-HISTORICAL` evidence and records zero
    confirmatory campaign results.
  - The WP037-F1 corrective delta: `ResonanceLayer` and
    `DiscreteDeltaThetaGammaLayer` now expose canonical optimizer-visible
    PyTorch parameters, synchronize them into the Rust/Burn forward, and
    return Burn-computed parameter VJPs. Compatibility mirror parameters are
    documented separately and are not misrepresented as Burn VJPs.
  - Documentation closure in S4: affected-directory READMEs, changelog,
    session registers, audit index/closure evidence, user guide wording,
    `prin.nn` ownership documentation, Rust binding comments, notebook 04's
    optimizer-reachability demonstration, and this report.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#45
  remain in force. No new plan amendment was adopted in WP-037. WP037-F7 was
  amended through the governed DV-036 register disposition rather than a new
  amendment.
- **Audit:** `DOCS/audits/037-wp037-audit.md` — S2 verdict **FAIL** with
  eight findings. S3 closed all eight: F1–F5 and F8 FIXED, F6 CARRIED(1) to
  the governed S4 push/CI gate, F7 AMENDED into DV-036; delta re-audit
  **CLEAN** after the corrective canonical-parameter second delta. No
  unresolved D1/D2 finding exists.
- **Session Register:** 0145, 0146, 0147, and 0148 are marked COMPLETE;
  0149 (WP-038 S1) is the registered successor.
- **WP-037 is CLOSED subject to the governed maintainer push/remote-CI
  action.** Local evidence is complete; publishing `1.0` remains out of
  scope and Phase 7 pre-registration is unchanged.

---

## 2. Metric trends

| Metric | Previous (PSR-036G) | Current (PSR-037) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1,540 passed, 1 ignored | **1,577 passed, 1 ignored** after the WP037-F1 corrective delta | 100% where defined |
| Python full suite + parity | 3,395 passed, 203 skipped | **3,496 passed, 185 skipped, 58 warnings** (`tests/ parity/`) | 100% at registered tolerance |
| Python fast suite | 2,775 passed, 201 skipped, 30 deselected | **2,873 passed, 178 skipped, 38 deselected** (S3 corrective delta) | 100% |
| Coverage | 95% total | **95% total** | ≥95% |
| Docstring coverage | 97.6% | **97.6%** | ≥95% overall |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** from a freshly deleted `DOCS/sphinx/_build` | 0 warnings |
| Sphinx guide examples | not separately gated | **3/3 execute** under `pytest tests/test_sphinx_examples.py -m slow`; the `docs` CI job now invokes the same harness | executable |
| Notebooks | 4/4 execute | **4/4 execute** under `pytest tests/test_notebooks.py -m slow` (238.8 s total); committed outputs have no maintainer paths, warnings, or tracebacks | executable / clean outputs |
| Paper reproduction | not tabulated | **172 stored JSON artefacts verified; 39 paper files generated** | manifest + generator wiring |
| Trainability reachability | not measured | **ResonanceLayer 5/5; DiscreteDeltaThetaGammaLayer 15/15 finite parameter VJPs; optimizer step changes both Rust-backed forwards** | non-vacuous |
| Clippy/ruff/mypy/interrogate/bandit | 0 findings | **0 findings** | 0 |
| Snyk Code | 0 medium+, 5 unchanged lows | **0 issues** in the changed `python/prin/nn` and `crates/prin-py/src/bindings` scopes at low threshold | governed scope clean |
| Snyk Open Source | 0 issues | **0 issues** (`all_projects=true`, low threshold, maintainer `.venv`) | 0 |
| Native dependency audits | cargo audit 3 governed warnings; pip-audit clean | **cargo audit exit 0** with only `paste` RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141, `chacha20` yanked; both `pip-audit` scopes clean | governed warnings only |
| Secret scanning | GitHub Gitleaks substitute | **blocked locally** — `gitleaks` unavailable; GitHub full-history job remains authoritative at push | not claimed locally |
| `wp036_migration_table.py check` | pass | **pass (172 symbols)** | pass |
| `check_no_python_numerics.py` | clean (19 modules) | **clean (19 modules)** | clean |
| `check_dv_register_gates.py` | pass (35 rows) | **pass (36 rows / 198 sessions)** | pass |
| `check_deviation_ledger.py` | pass | **pass (120 previous / 128 current rows)** | pass |
| `verify_api_surface` | `(set(), set())` | **`(set(), set())`** | frozen |

**Verification commands re-run in S4 (2026-09-15, Windows 11 / Python
3.14.0 / Rust 1.92.0):**

```powershell
.venv\Scripts\python -m pytest tests/test_sphinx_docs.py tests/test_paper_wiring.py tests/test_notebooks.py tests/test_acceptance_nn.py::TestResonanceLayer::test_optimizer_step_changes_rust_forward tests/test_acceptance_y2q1.py::TestDiscreteDeltaThetaGammaLayer::test_optimizer_step_changes_rust_forward -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
# -> 75 passed, 4 deselected
.venv\Scripts\python -m pytest tests/test_sphinx_examples.py -m slow --basetemp=.pytest_basetemp --durations=10 -q
# -> 3 passed
.venv\Scripts\python -m pytest tests/test_notebooks.py -m slow --basetemp=.pytest_basetemp --durations=10 -q
# -> 4 passed, 28 deselected; 86.4 s / 65.6 s / 51.2 s / 35.4 s
Remove-Item -Recurse -Force DOCS/sphinx/_build -ErrorAction SilentlyContinue
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# -> build succeeded
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
# -> clean
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# -> all clean at their governed thresholds
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp -q
# -> 3496 passed, 185 skipped, 58 warnings
.venv\Scripts\python tools/wp036_migration_table.py check
.venv\Scripts\python tools/check_no_python_numerics.py
.venv\Scripts\python tools/check_dv_register_gates.py
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/036-project-state.md DOCS/reports/037-project-state.md
.venv\Scripts\python tools/wp001_baseline.py check
.venv\Scripts\python -c "from prin._deprecation import verify_api_surface; from prin import __all__; print(verify_api_surface(__all__))"
.venv\Scripts\python tools/reproduce.py --output-dir paper --verify-manifest
# -> all pass; 172 verified / 39 generated
```

Snyk MCP scans re-run in S4: `snyk_code_scan` on `python/prin/nn` and
`crates/prin-py/src/bindings` at low threshold returned 0 issues;
`snyk_sca_scan` on `C:\dev\PRIN` with `all_projects=true`, low threshold,
`fail_on=all`, and `command=C:\dev\PRIN\.venv\Scripts\python` returned 0
issues.

---

## 3. Deviation ledger (cumulative)

### 3.1 New findings this cycle

| Finding | Severity | Final status | Evidence |
|---|---|---|---|
| WP037-F1 | D1 | FIXED (corrective second delta) | Canonical PyTorch parameters synchronized into Burn; 5/5 and 15/15 finite parameter VJPs; targeted optimizer steps change both Rust-backed forwards |
| WP037-F2 | D2 | FIXED | Full prescribed gate executed before the S3 commit; the corrective delta re-ran the published gate in order |
| WP037-F3 | D2 | FIXED | `ci/docs-constraints.txt` bounds the docs job's maturin/Torch/notebook/Sphinx dependency resolution |
| WP037-F4 | D2 | FIXED | `test_sphinx_examples.py` executes the shipped guide examples; `python.yml::docs` invokes the harness |
| WP037-F5 | D2 | FIXED | Paper stems derive from current generator metadata; exact orphan set and negative control pass |
| WP037-F6 | D3 | CARRIED(1) | Predecessor push/remote-CI breach acknowledged; governed push and SHA-specific CI evidence remain the maintainer action |
| WP037-F7 | D3 | AMENDED | Nightly benchmark regression disposed as host-instability / baseline-staleness class in DV-036 with WP-038 re-audit gate |
| WP037-F8 | D4 | FIXED | Notebook 04 cleaned and re-executed; output-hygiene regression coverage passes |

### 3.2 Cumulative ledger

Eight new findings this cycle. The cumulative table carries forward every row
from PSR-036 §3 unchanged (verified by `tools/check_deviation_ledger.py`) and
appends the eight WP-037 rows. No earlier finding was reopened; the WP037-F1
corrective delta superseded the first S3 mirror-gradient repair with the
canonical parameter/VJP design.

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
| WP008-F5 | 008 | D4 | `RK45Integrator::new` reused `InvalidTimestep` for tolerance validation; test only checked `is_err()` | FIXED | Commit `b4749ba`; added `IntegrateError::InvalidTolerance { param, value }` variant; updated to assert specific variant |
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
| WP037-F1 | 037 | D1 | Advertised `ResonanceLayer`/`DiscreteDeltaThetaGammaLayer` parameters did not reach Rust-owned forward behavior | FIXED | `e40ed03`; corrective `ae29124`; non-vacuous optimizer-step reachability tests |
| WP037-F2 | 037 | D2 | S2-prescribed full gate was not executed in order before the S3 commit | FIXED | `e40ed03`; corrective delta re-ran the published gate |
| WP037-F3 | 037 | D2 | Docs CI dependency resolution was unpinned | FIXED | `e40ed03`; `ci/docs-constraints.txt` |
| WP037-F4 | 037 | D2 | Sphinx guide examples were claimed executable but lacked committed CI coverage | FIXED | `e40ed03`; `tests/test_sphinx_examples.py`; `python.yml::docs` harness |
| WP037-F5 | 037 | D2 | Paper figure wiring could pass on archived filename authority alone | FIXED | `e40ed03`; registry-derived figure stems and planted negative control |
| WP037-F6 | 037 | D3 | Predecessor range push and SHA-specific live-CI evidence remained blocked | CARRIED(1) | Amendment #28; governed maintainer push/remote-CI gate |
| WP037-F7 | 037 | D3 | Nightly benchmark regression was repeatedly red from host instability and baseline staleness | AMENDED | DV-036; WP-038 S1 re-audit gate |
| WP037-F8 | 037 | D4 | Notebook 04 committed output contained a maintainer path and an avoidable warning | FIXED | `e40ed03`; notebook cleanup and output-hygiene regression coverage |

---

## 4. Plan amendments this cycle

None. WP-037 required a governed S3 correction cycle for WP037-F1 and a
DV-register amendment for WP037-F7, but it adopted no Project Plan
amendment. The amendment-#28 push batching, amendment-#38 successor chain,
and amendment-#45 CI/process controls remain in force.

---

## 5. Risks and blockers

- **WP037-F6 / governed push and remote CI:** local gates are green and the
  S4 artefact set is committed locally, but the amendment-#28 batched push
  and SHA-specific remote CI evidence remain a maintainer action. This is a
  carried gate, not a hidden pass.
- **DV-036 nightly benchmark regression:** the repeated benchmark-red runs
  are disposed as host-instability / baseline-staleness class with a
  WP-038 S1 re-audit gate. This must not be treated as confirmatory
  performance evidence.
- **Local secret scanning:** `gitleaks` is unavailable on this host, so the
  local scan remains **blocked**. GitHub's full-history Gitleaks job is the
  amendment-#5 substitute at push; no local secret-scan pass is claimed.
- **ReadTheDocs deployment:** `.readthedocs.yaml` still lacks a
  `pre_build` maturin/Torch install, so RTD cannot import `prin`. The CI
  `docs` job is the authoritative warning-as-error build; WP-038 owns the
  verified deployment path.
- **Phase 7 remains gated:** WP-037 is documentation/validation evidence
  only. No stable `1.0` publication and no campaign pre-registration or
  execution result was created.

---

## 6. Next work package declaration — WP-038

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0149-wp038-s1-rc1-packaging-and-phase-6-gate.md`),
per Documentation Standards §7 item 5:

- **Title:** "Coding — RC1 packaging and Phase 6 gate."
- **Mission:** "Build/smoke all wheel/sdist targets, validate release
  security/OIDC configuration, run full CI/repro, and publish 1.0.0-rc1
  after approval."
- **Acceptance (verbatim):** "No-compiler installs pass across OS families;
  all CI/security/repro gates green; RC1 artefacts and checksums published;
  Phase 7 entry criteria satisfied."
- **Non-goals (verbatim):** "Stable 1.0.0 release or unregistered
  experiments."
- **First session brief:**
  `DOCS/sessions/phase-6/0149-wp038-s1-rc1-packaging-and-phase-6-gate.md`
- **Sessions:** `0149` (S1) → `0150` (S2) → `0151` (S3) → `0152` (S4).

### WP-038 entry conditions

Quoted from the `0149` brief:

1. "The preceding S4 (or campaign synthesis for WP-039) is closed and
   committed." — local S4 closure is committed; governed push remains the
   maintainer action.
2. "WP-038 scope, acceptance criteria, and non-goals have maintainer
   approval." — the registered `0149` brief carries the approved WP-038
   scope, including the DV-010 tag/publish action only on explicit
   maintainer confirmation.
3. "No unresolved D1/D2 finding exists; any carried D4 is explicitly in
   this scope." — WP037-F6 is a carried D3 gate, F7 is AMENDED to DV-036
   with WP-038 re-audit, and no unresolved D1/D2 remains.

**Maintainer approval recorded: MichaelMaillet, 2026-09-15 (this PSR §6
hand-off).** WP-038 may begin only after the governed predecessor push /
CI evidence is obtained, or the maintainer explicitly accepts the recorded
local gate under amendment #28.

---

## 7. Cross-cutting document currency

- **READMEs updated:** `.github/workflows/README.md` (docs examples gate),
  `DOCS/README.md` (latest PSR/audit pointers), `DOCS/audits/README.md`
  (WP-037 closure), `DOCS/experiments/README.md` (S1 handoff context),
  `DOCS/reports/README.md` (PSR-037), `DOCS/sphinx/README.md` (examples +
  notebook harnesses), `notebooks/README.md` (notebook 04 ownership and
  measured runtimes), `python/prin/nn/README.md` (canonical parameter /
  Rust-owned / mirror taxonomy), and `tests/README.md` (WP-037 gates and
  current counts).
- **Sphinx:** `api/nn.rst`, `architecture.rst`, `getting_started.rst`,
  `migration_guide.rst`, and `notebooks.rst` now describe the corrected
  canonical-parameter ownership model without erasing the distinct
  compatibility models. Fresh-directory `sphinx-build -W --keep-going`
  succeeds.
- **`prin.nn` docs:** `__init__.py`, `attention.py`, `autoencoders.py`,
  `hierarchical_layers.py`, `hybrid.py`, `model.py`, and `README.md`
  distinguish canonical PyTorch parameters synchronized into Burn from
  Rust-owned parameters and value-preserving mirrors.
- **Rust binding comments:** `crates/prin-py/src/bindings/train.rs` and
  `attention.rs` scope Rust-owned-state language to the modules that own it
  rather than implying one ownership contract for every layer.
- **Notebook 04:** now demonstrates DLPack, autograd, float64 gradcheck,
  Rust-native checkpointing, a real Adam loop, gradient-population counts,
  and an ownership table that distinguishes canonical VJPs from mirrors.
- **Paper/parity:** `tools/reproduce.py --output-dir paper
  --verify-manifest` verifies 172 artefacts and regenerates 39 files.
  `parity_report.rst` remains a draft with zero confirmatory results.
- **Governance indexes:** `DOCS/audits/README.md`,
  `DOCS/reports/README.md`, `DOCS/README.md`,
  `DOCS/sessions/SESSION_REGISTER.md`, and
  `DOCS/sessions/phase-6/README.md` record WP-037's S4 closure.
- **Changelog:** `CHANGELOG.md` carries the WP-037 S4 entry under
  `[Unreleased]`.
- **Generated migration table:** left governed by
  `tools/wp036_migration_table.py`; the check passes for all 172 symbols.
- **API surface:** `verify_api_surface` remains `(set(), set())`; no new
  public symbol or release/tag was introduced.

---

## 8. Evidence boundary

WP-037 closes documentation and validation-readiness work only. Notebook
outputs, Sphinx examples, paper artefact regeneration, and the draft Parity
Report are reproducibility/validation artefacts. They do not constitute a
Phase 7 confirmatory campaign, do not replace campaign pre-registration,
and do not publish `1.0.0` or a release-candidate artefact.

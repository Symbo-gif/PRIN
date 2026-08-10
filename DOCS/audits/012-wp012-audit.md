# PRIN Audit Report — Cycle 012 / WP-012

**Date:** 2026-08-10
**Auditor:** Devin (AI pair)
**Scope:** WP-012 "Exponential and multi-rate integrators" — `crates/prin-dynamics/src/integrate.rs`, `crates/prin-dynamics/src/lib.rs`; expected `crates/prin-py/src/bindings/integrators.rs`, `python/prin/dynamics.py`, `python/prin/_prin_core.pyi`, and parity corpus
**Sessions:** S1 — session 0045 (implementation, commit `d02e478`); S2 — session 0046 (this audit)
**Active brief:** `DOCS/sessions/phase-2/0046-wp012-s2-exponential-and-multi-rate-integrators.md`
**Git state:** `main` @ `d02e478b84f14eab80258f1630ad89057471a2d0`
**Verdict:** FAIL

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ❌ | Rust core integrators present; Python bindings, parity corpus, and slow-partition multi-rate scope missing |
| Plan/architecture conformance (A2) | ✅/⚠️ | No Python numerics; Rust core architecture preserved; `matrix_exp` silently falls back to identity on singular denominator |
| Tests in tandem + coverage (A3) | ✅ | Rust unit/property tests added in same commit; `integrate.rs` line coverage 98.13% default / 97.61% strict-checks |
| Numerical parity + invariants (A4) | ⚠️ | Unit-level invariants pass (matrix-exp zero/diagonal, φ₁(0)=I, Krylov≈direct, multi-rate h⁴ convergence); no Rust-vs-PRINet parity cases for new integrators |
| Quality gates (A5) | ✅ | fmt, clippy `-D warnings`, ruff, mypy strict, interrogate, bandit, Sphinx, rustdoc all clean |
| Security (A6) | ⚠️ | Changed code clean; Snyk Code reports 3 pre-existing Low path-traversal findings in `tools/wp001_baseline.py` governed by `.snyk` ignores (EA-002 E-F4) |
| Docstring/doc coverage (A7) | ✅ | Rust public items documented; `missing_docs` clean under `-D warnings`; Sphinx 0 warnings |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers in changed code; `__all__` consistent for existing symbols; baseline traceability clean |
| CI status (A9) | ✅ | Local reproduction of all gates green; `strict-checks` exercised |
| Artefact trail (A10) | ⚠️ | Predecessor S1 handoff note not present; S1 commit supplies tests but no evidence map or parity corpus update |

---

## 2. Methodology

All commands executed on Windows, Python 3.14.0, Rust toolchain per `rust-toolchain.toml`.

```powershell
# Repository state
git rev-parse HEAD                                   # d02e478b84f14eab80258f1630ad89057471a2d0
git show --stat d02e478 --name-only                  # only integrate.rs and lib.rs changed

# Rust quality gates
cargo fmt --all -- --check                           # exit 0
cargo clippy --workspace --all-targets -- -D warnings # exit 0
cargo test --workspace                               # all pass
cargo test --workspace --features strict-checks      # all pass
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # exit 0, 0 warnings
cargo llvm-cov -p prin-dynamics --summary-only       # integrate.rs 98.13% lines / 97.62% functions
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only  # integrate.rs 97.61% lines / 97.67% functions
cargo audit                                          # 1 inherited paste advisory (amendment #9)

# Python quality gates
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 47 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues in 18 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # No issues identified
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 241 passed, 6 deselected
.venv\Scripts\python -m pytest parity/ -v -m parity --basetemp=.pytest_basetemp  # 510 passed
.venv\Scripts\python -m pip_audit .                                           # No known vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # No known vulnerabilities
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html  # build succeeded, 0 warnings

# Traceability / baseline
.venv\Scripts\python tools\wp001_baseline.py check                            # WP-001 baseline validation passed

# Security scans (MCP)
# snyk_code_scan path=C:\dev\PRIN severity_threshold=low  # 3 Low path-traversal findings in tools/wp001_baseline.py (already ignored in .snyk)
# snyk_sca_scan  path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python  # 0 issues
```

---

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (011-project-state.md §7): `prin-dynamics` — exponential integrators (direct exponential, Krylov-subspace approximation), multi-rate sub-stepped RK4 for stiff/slow oscillator partitions, **and corresponding Python bindings through `prin-py`**.

**Present in S1 commit `d02e478`:**
- `ExponentialIntegrator` with direct Padé(13) scaling-and-squaring, Krylov–Arnoldi, and stiff-mode adaptive rank in `crates/prin-dynamics/src/integrate.rs`.
- `MultiRateIntegrator` with uniform RK4/Euler sub-stepping in `crates/prin-dynamics/src/integrate.rs`.
- `MultiRateMethod` enum and `InvalidDim`/`InvalidKrylovRank`/`LinearSolveFailed` error variants in `crates/prin-dynamics/src/integrate.rs`.
- Rust unit/property tests in the same file.

**Missing from S1 commit:**
- `prin-py` `PyExponentialIntegrator` / `PyMultiRateIntegrator` bindings.
- `python/prin/dynamics.py` re-exports and `python/prin/_prin_core.pyi` stubs.
- Python acceptance tests for the new integrators.
- Golden-corpus / parity cases for the new integrators.

This is a scope omission against the WP-012 declaration and the public-API traceability matrix (`DOCS/baselines/wp001_api_traceability.md` lines 252, 257, 298, 303, 325, 326).

### 3.2 A2 — Plan/architecture conformance

- **No Python numerics:** `python/prin/dynamics.py` remains a pure re-export module. ✅
- **Crate layering:** `prin-py` is unchanged, so the only crate linking Python is still `prin-py`. ✅
- **One algorithm, one implementation:** The new integrators are implemented once in `prin-dynamics`. ✅
- **Numerical hazard:** `matrix_exp` silently returns the identity matrix when the Padé denominator `V - U` is singular or near-singular (`crates/prin-dynamics/src/integrate.rs:1300`). This violates the parity-program invariant that numerical failures must surface as typed errors, not silent wrong values.

### 3.3 A3 — Tests in tandem + coverage

The S1 commit adds code and unit tests in the same commit:
- `matrix_exp_zero_is_identity`, `phi1_zero_is_identity`, `matrix_exp_diagonal` (lines 2518–2552).
- `krylov_exp_vec_matches_direct_small` (line 2555).
- `exp_integrator_*` initialization, step, integration, invalid-dt, stiff-mode, and Krylov-path tests (lines 2586–2758).
- `multi_rate_*` initialization, zero-substeps, RK4 equivalence, output shape, convergence order, trajectory, Euler method, invalid-dt, and freq-band preservation tests (lines 2764–2899).

`cargo llvm-cov` reports `integrate.rs` at 98.13% lines / 97.62% functions (default) and 97.61% lines / 97.67% functions (`strict-checks`). This meets the ≥95% gate for new/changed code.

### 3.4 A4 — Numerical parity + invariants

**Green unit-level invariants:**
- `exp(h·diag(a,b))` matches `diag(e^{ha}, e^{hb})` within `1e-10`.
- `φ₁(0) = I` within `1e-10`.
- Krylov `exp(hA)v` matches direct `exp(hA)·v` within `1e-6` for a small test matrix.
- `MultiRateIntegrator` with `sub_steps=1` matches single RK4 exactly.
- `MultiRateIntegrator` with RK4 sub-steps preserves `h⁴` convergence on a single-oscillator decay problem (ratios within 8–32).

**Missing parity:** There are no Rust-vs-PRINet 3.0.0 trajectory or differential parity tests for `ExponentialIntegrator` or `MultiRateIntegrator`, and no new entries in `parity/corpus/`. The existing 504/510 parity cases still pass, but none exercise the WP-012 primitives.

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | exit 0 |
| `cargo test --workspace` | all pass |
| `cargo test --workspace --features strict-checks` | all pass |
| `ruff check` | All checks passed |
| `ruff format --check` | 47 files already formatted |
| `mypy --strict` | Success: no issues in 18 source files |
| `cargo doc -D warnings` | 0 warnings |
| `Sphinx -W --keep-going` | build succeeded, 0 warnings |

### 3.6 A6 — Security

- `bandit -r .`: no issues.
- `cargo audit`: only the inherited `paste` RUSTSEC-2024-0436 advisory (amendment #9).
- `pip-audit .` and `pip-audit -r DOCS/sphinx/requirements.txt`: no known vulnerabilities.
- Snyk Open Source (`snyk_sca_scan`): 0 issues.
- Snyk Code (`snyk_code_scan`): 3 Low path-traversal findings in `tools/wp001_baseline.py`. These are **pre-existing**, already governed by `.snyk` ignores (EA-002 E-F4, maintainer approval 2026-08-08), and not introduced by WP-012. No WP-012 source file triggered Snyk Code.

### 3.7 A7 — Docstring/doc coverage

- `interrogate` reports 100.0% (106/106) for `python/prin`.
- `cargo doc -D warnings` is clean.
- All new public Rust structs/enums/methods in `integrate.rs` have doc comments.
- Sphinx builds with 0 warnings.

### 3.8 A8 — Repository hygiene

- No `TODO`/`FIXME`/`stub` markers in `crates/prin-dynamics/src/integrate.rs`.
- `python/prin/dynamics.py` `__all__` is consistent for the symbols it exports (but incomplete for WP-012 scope).
- `tools/wp001_baseline.py check` passes.
- No orphan files introduced by the S1 commit.

### 3.9 A9 — CI status

All local quality gates green. `strict-checks` feature exercised and passes. No benchmark regression gates defined for WP-012.

### 3.10 A10 — Artefact trail

- Predecessor S1 handoff note (`DOCS/experiments/0045-wp012-s1-handoff.md` or equivalent) is absent.
- The S1 commit message describes the change but does not map acceptance criteria to evidence.
- `DOCS/reports/011-project-state.md` contains the WP-012 declaration and is consistent with this audit.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP012-F1 | D1 | `crates/prin-py/src/bindings/integrators.rs` (registration missing); `python/prin/dynamics.py` (`__all__` omits new integrators); `python/prin/_prin_core.pyi` (no stubs) | WP-012 declared scope includes "corresponding Python bindings through `prin-py`". S1 commit `d02e478` changes only `crates/prin-dynamics/src/integrate.rs` and `lib.rs`; no PyO3 classes, no `dynamics.py` re-exports, no `.pyi` stubs, no Python tests. Public-API traceability matrix (`DOCS/baselines/wp001_api_traceability.md`) maps `ExponentialIntegrator` and `MultiRateIntegrator` to WP-012. | WP-012 declaration (011-project-state.md §7); Project Plan §4 (Python layer is the public API); traceability matrix | Add `PyExponentialIntegrator` and `PyMultiRateIntegrator`/`PyMultiRateMethod` to `crates/prin-py/src/bindings/integrators.rs`; register them in `crates/prin-py/src/lib.rs`; update `python/prin/dynamics.py` `__all__`; regenerate `python/prin/_prin_core.pyi`; add Python acceptance tests mirroring the Rust unit tests. |
| WP012-F2 | D1 | `parity/corpus/` (no exponential/multi-rate cases); `crates/prin-dynamics/tests/parity_integrators.rs` (no new parity tests) | WP-012 acceptance criterion: "Parity cases for new integrators added to the golden corpus." No new `.npz` corpus entries or Rust-vs-PRINet parity tests exist for `ExponentialIntegrator` or `MultiRateIntegrator`. | WP-012 acceptance criteria; Testing Standards §3 (parity for touched primitives); Project Plan §5 (numerical parity program) | Generate reference trajectories from `prinet==3.0.0` `ExponentialIntegrator` and `MultiRateIntegrator` for representative model/coupling/dt combinations; add them to `parity/corpus/` and the differential parity harness; add hard-coded Rust parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` if they do not require a Python subprocess. |
| WP012-F3 | D1 | `crates/prin-dynamics/src/integrate.rs:1300` | `matrix_exp` computes the Padé approximant by solving `(V - U) X = (V + U)`. If `lu_solve` fails (singular or near-singular denominator), it silently returns `Array2::<f64>::eye(n)` instead of propagating the error. This can produce incorrect trajectories without a typed failure. | Project Plan §5 (numerical parity — failures must not silently produce wrong values); Coding Standards §6 (input validation and typed errors at public boundaries) | Propagate the LU failure. Either change `matrix_exp`/`phi1_matrix` to return `Result<Array2<f64>, IntegrateError>` and add an `IntegrateError::MatrixExpFailed` variant, or handle the error in `exp_step`/`krylov_*` callers. Add a regression test that forces a near-singular denominator and asserts a typed error, not identity. |
| WP012-F4 | D3 | `crates/prin-dynamics/src/integrate.rs:1784–1909` (`MultiRateIntegrator`) | The WP text and acceptance criteria refer to "multi-rate scheduling" and "slow partition" convergence. The implementation applies a uniform `inner_dt = dt / sub_steps` to **all** oscillators and does not use `freq_band` to schedule different step sizes per band. The convergence test uses a single-oscillator decay, not a slow partition. The PRINet 3.0 reference implementation also uses uniform sub-stepping, so this is a justified match to the reference but a drift from the WP wording. | WP-012 declaration ("multi-rate sub-stepped RK4 for stiff/slow oscillator partitions"); Testing Standards §3 (acceptance tests must demonstrate claimed behavior) | Either (a) implement band-aware multi-rate scheduling using `OscillatorState::freq_band` with per-band sub-step counts, and add a slow-partition convergence test, or (b) amend WP-012 to clarify that "multi-rate" means uniform sub-stepping matching PRINet 3.0 and add a regression test that documents this design choice. |
| WP012-F5 | D4 | `crates/prin-dynamics/src/integrate.rs:1558–1778` (`ExponentialIntegrator`) | `ExponentialIntegrator` stores a `dim` field that the user supplies. `Integrator::step` and `exp_step` derive the actual dimension from the state vector and never validate that it equals `self.dim`. A misconfigured `dim` can cause the direct/Krylov path decision (`use_krylov`) and adaptive Krylov rank to be inconsistent with the Jacobian size. | Coding Standards §6 (input validation at public boundaries) | Validate `state.phase.len() * 3 == self.dim` (or remove the stored `dim` and derive the path decision from the state at runtime) and return `IntegrateError::InvalidDim` or a new dimension-mismatch error. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP012-F1** (D1), **WP012-F2** (D1), **WP012-F3** (D1), **WP012-F4** (D3), **WP012-F5** (D4).

Carried findings re-inspected: none (no findings carried from cycle 011).

Pre-existing security findings not added as WP-012 findings: the 3 Low path-traversal Snyk Code findings in `tools/wp001_baseline.py` are governed by `.snyk` ignores (EA-002 E-F4) and are not in WP-012 scope.

---

## 6. Verdict and required actions

**Verdict: FAIL**

WP-012 S1 (`d02e478`) delivers a mathematically coherent Rust-core implementation of exponential (direct/Krylov) and uniform-substep multi-rate integrators, with strong unit-test coverage (≈98% on `integrate.rs`) and clean quality gates. However, the WP-012 scope explicitly includes `prin-py` Python bindings and golden-corpus parity cases, neither of which is present. In addition, `matrix_exp` contains a silent identity fallback on singular LU denominators that can produce wrong numerical results without a typed error. These are D1 trajectory breaches. The multi-rate implementation matches the PRINet 3.0 reference but does not realize the band-aware scheduling implied by the WP text (D3). Finally, `ExponentialIntegrator` does not validate its stored dimension against the state (D4).

**Ordered S3 action list (severity order):**

1. **WP012-F1:** Add Python bindings and public API surface for `ExponentialIntegrator`, `MultiRateIntegrator`, and `MultiRateMethod`:
   - `crates/prin-py/src/bindings/integrators.rs`: new `#[pyclass]` types with constructors, `step`, `integrate`, and getters.
   - `crates/prin-py/src/lib.rs`: register the new classes.
   - `python/prin/dynamics.py`: re-export the new classes and update `__all__`.
   - `python/prin/_prin_core.pyi`: add type stubs.
   - `tests/test_dynamics_bindings.py` or a new test module: Python acceptance tests.

2. **WP012-F2:** Add Rust-vs-PRINet parity evidence for the new integrators:
   - Generate reference trajectories from `prinet==3.0.0` and add them to `parity/corpus/`.
   - Add differential parity coverage in `parity/test_parity_differential.py` or equivalent harness.
   - Add hard-coded Rust parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` if feasible.

3. **WP012-F3:** Replace the silent identity fallback in `matrix_exp` (line 1300) with typed error propagation. Add a regression test that exercises the failure path.

4. **WP012-F4:** Resolve the multi-rate scheduling scope: implement per-`freq_band` sub-stepping with a slow-partition convergence test, or amend WP-012 to document that the current uniform sub-stepping matches the PRINet 3.0 reference.

5. **WP012-F5:** Add dimension validation in `ExponentialIntegrator` or derive the direct/Krylov decision from the state at runtime.

After all D1–D2 findings are addressed, re-run the full A1–A10 checklist and a delta re-audit before entering S4 documentation.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP012-F1 | | | |
| WP012-F2 | | | |
| WP012-F3 | | | |
| WP012-F4 | | | |
| WP012-F5 | | | |

**Delta re-audit date:** TBD — **Result:** TBD

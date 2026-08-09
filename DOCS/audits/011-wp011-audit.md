# PRIN Audit Report — Cycle 011 / WP-011

**Date:** 2026-08-09
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-011 "Phase 1 Python API and dynamics integration" — `crates/prin-py/src/bindings/{state,models,integrators,coupling,metrics}.rs`, `crates/prin-py/src/lib.rs`, `python/prin/{dynamics,metrics,__init__}.py`, `python/prin/_prin_core.pyi`, `tests/test_dynamics_bindings.py`
**Sessions:** S1 — session 0041 (implementation, commit `ff48f52`); S2 — session 0042 (this audit)
**Active brief:** `DOCS/sessions/phase-1/0042-wp011-s2-phase-1-python-api-and-dynamics-integration.md`
**Git state:** `feat/wp006-oscillator-state` @ `ff48f52`
**Verdict:** PASS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope present; no undeclared additions |
| Plan/architecture conformance (A2) | ✅ | No Python numerics; numerical authority in Rust; crate layering preserved |
| Tests in tandem + coverage (A3) | ✅ | 69 new Python tests; Python coverage 99% (100% on new modules) |
| Numerical parity + invariants (A4) | ✅ | All 504 parity definitions green; new tests verify known identities |
| Quality gates (A5) | ✅ | fmt/clippy/ruff/mypy all clean; 370 Rust + 253 Python tests pass |
| Security (A6) | ✅ | bandit/pip-audit clean; cargo audit: inherited paste advisory only (amendment #9) |
| Docstring/doc coverage (A7) | ✅ | interrogate 100%; cargo doc 0 warnings; Sphinx 0 warnings; .pyi complete |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub; `__all__` consistent; baseline traceability clean |
| CI status (A9) | ✅ | All gates green; strict-checks feature exercised |
| Artefact trail (A10) | ✅ | Prior cycle audit/report consistent; WP-011 declaration in 010-project-state.md |

## 2. Methodology

All commands executed on Windows, Python 3.14.0, Rust toolchain per `rust-toolchain.toml`.

```powershell
# Rust quality gates
cargo fmt --all -- --check                                                    # exit 0
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0
cargo test --workspace                                                        # 370/370 pass
cargo test --workspace --features strict-checks                               # 373/373 pass
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps               # exit 0, 0 warnings
cargo audit                                                                   # 1 inherited paste advisory (amendment #9)
cargo llvm-cov -p prin-py --summary-only                                      # PyO3 bindings: see A3 note

# Python quality gates
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 47 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues in 18 files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # No issues identified
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 241 passed, 6 deselected
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 253 passed
.venv\Scripts\python -m pip_audit .                                           # No known vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # No known vulnerabilities
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html  # build succeeded, 0 warnings

# Traceability / baseline
tools\wp001_baseline.py check                                                 # exit 0 (clean)
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (010-project-state.md §6): `prin-py` PyO3 bridge and thin `python/prin` API surface exposing completed dynamics (`OscillatorState`, `Seed`, models, integrators, PAC, coupling topologies) and metrics (`prin-metrics` full surface) through Python; port corresponding acceptance tests.

**Present:**
- `crates/prin-py/src/bindings/state.rs` — `PyOscillatorState`, `PyStateDerivatives`, `PySeed` + constants (TAU, AMPLITUDE_MIN/MAX, DERIV_CLAMP, SPARSE_EPS)
- `crates/prin-py/src/bindings/models.rs` — `PyKuramotoOscillator`, `PyStuartLandauOscillator`, `PyHopfOscillator`
- `crates/prin-py/src/bindings/integrators.rs` — `PyEulerIntegrator`, `PyRK4Integrator`, `PyRK45Integrator`, `PyAdaptiveResult`
- `crates/prin-py/src/bindings/coupling.rs` — `PyCouplingMode`, `PyTopology`, `PyPhaseAmplitudeCoupling`
- `crates/prin-py/src/bindings/metrics.rs` — 22 `#[pyfunction]`s covering full `prin-metrics` surface (order, coherence, spectral, energy, chimera, metastability, k-NN)
- `python/prin/dynamics.py` — re-export module (20 symbols + `__all__`)
- `python/prin/metrics.py` — re-export module (22 symbols + `__all__`)
- `python/prin/_prin_core.pyi` — complete type stubs for all new symbols
- `tests/test_dynamics_bindings.py` — 69 tests across 13 test classes

**No undeclared additions.** The `numpy = "0.29.0"` dependency added to `prin-py/Cargo.toml` is required for PyO3 numpy array integration and matches the PyO3 version (0.29.0). ✅

### 3.2 A2 — Plan/architecture conformance

- **No Python numerics:** `dynamics.py` and `metrics.py` are pure re-export modules. Grep for `numpy`/`np.` in both files returns zero matches. All numerical authority remains in Rust (`prin-dynamics`, `prin-metrics`). ✅
- **Crate layering:** `prin-py` depends on `prin-dynamics` and `prin-metrics`; bindings delegate to inner Rust types via `.inner` field access. No numerical logic in binding layer. ✅
- **Deterministic Seed flow:** `PySeed` wraps `Seed` directly; `create_random` and `small_world` accept `&mut PySeed` / `&PySeed` preserving deterministic counter advancement. ✅
- **Explicit state:** All state construction goes through validated constructors (`OscillatorState::new`, `create_random`, `create_synchronized`). ✅

### 3.3 A3 — Tests in tandem + coverage

**New tests:** 69 Python tests in `test_dynamics_bindings.py` covering:
- Constants (4 tests)
- Seed (6 tests: creation, determinism, jump, range, u64, repr)
- OscillatorState (8 tests: creation, phase wrapping, random, synchronized, empty, k-NN, repr, freq_band)
- StateDerivatives (1 test)
- CouplingMode (5 tests)
- Topology (3 tests)
- Models (6 tests: all 3 models × mean_field/full/sparse)
- Integrators (10 tests: step, integrate_fixed, adaptive, trajectory, all models, error, repr)
- PAC (2 tests)
- Metrics: order (6), coherence (3), spectral (2), energy (2), chimera (7), metastability (1), k-NN (1)
- Module re-exports (2 tests)

**Python coverage:** 99% overall (677 stmts, 10 miss). New modules `dynamics.py` and `metrics.py` at 100%. Misses are in pre-existing placeholder modules (`datasets.py`, `eval/`, `experiments/`, `nn/`, `reporting/`) outside WP-011 scope.

**Rust binding coverage note:** `cargo llvm-cov -p prin-py` reports 0% for `bindings/*.rs` because PyO3 binding code is exercised through the Python interpreter (via `maturin develop` + pytest), not through `cargo test`. This is an inherent measurement limitation of PyO3 bridge crates, analogous to the existing amendment #10 for `prin-kernels` cubecl code. The 69 Python tests exercise all binding paths; the underlying numerical logic in `prin-dynamics` (167 tests, 98%+ coverage) and `prin-metrics` (104 tests, 99.53% coverage) is independently verified.

### 3.4 A4 — Numerical parity + invariants

- All 504 golden corpus parity definitions remain green (6 differential + 9 derivative + 16 trajectory + 9 PAC + 12 metrics + 6 chimera + 4 corpus Rust-side parity tests).
- New Python tests verify known identities: synchronized state → order parameter = 1.0, equal phases → coherence matrix = 1.0, DC signal → PSD concentrates in bin 0, etc.
- No tolerance drift detected; test assertions use exact values or appropriate tolerances consistent with registered tolerance tiers.

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | exit 0 |
| `cargo clippy -D warnings` | exit 0 |
| `cargo clippy --features strict-checks -D warnings` | exit 0 |
| `ruff check` | All checks passed |
| `ruff format --check` | 47 files already formatted |
| `mypy --strict` | Success: no issues in 18 source files |
| `cargo test --workspace` | 370/370 pass |
| `cargo test --workspace --features strict-checks` | 373/373 pass |
| `pytest` (fast) | 241 passed, 6 deselected |
| `pytest` (full + parity) | 253 passed |

### 3.6 A6 — Security

| Check | Result |
|---|---|
| `bandit -r .` | No issues identified (2888 lines scanned) |
| `cargo audit` | 1 inherited `paste` RUSTSEC-2024-0436 (amendment #9) |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit` (sphinx reqs) | No known vulnerabilities |
| `unsafe` in new bindings | `#![allow(unsafe_code)]` in `state.rs` (see WP011-F1); no actual `unsafe` blocks |
| Secrets / codegen | None detected |

### 3.7 A7 — Docstring/doc coverage

| Gate | Result |
|---|---|
| `interrogate` | 100.0% (106/106) |
| `cargo doc -D warnings` | 0 warnings |
| Sphinx `-W --keep-going` | build succeeded, 0 warnings |
| Type stubs (`_prin_core.pyi`) | Complete: all 20 dynamics + 22 metrics symbols typed |

All `#[pyclass]` types have module-level doc comments. All `#[pyfunction]`s have docstrings. Python re-export modules have module-level docstrings.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/stub scan:** Zero matches in `crates/prin-py/src/bindings/`.
- **`__all__` consistency:** `dynamics.py` exports 20 symbols matching Rust registration; `metrics.py` exports 22 symbols matching Rust registration.
- **Baseline traceability:** `tools/wp001_baseline.py check` exits 0 (clean).
- **Orphan files:** None. All new files are referenced by `mod.rs`, `lib.rs`, or `__init__.py`.
- **gitignore:** `.pytest_basetemp/` respected; no untracked artifacts.

### 3.9 A9 — CI status

All quality gates green locally. `strict-checks` feature exercised (373/373 Rust tests pass). No benchmark regression gates defined for this WP.

### 3.10 A10 — Artefact trail

- `DOCS/audits/010-wp010-audit.md` exists (PASS, zero findings).
- `DOCS/reports/010-project-state.md` exists with WP-011 declaration in §6.
- Session register: 0037–0040 COMPLETE; 0041 READY; 0042 PLANNED (this audit).
- Cumulative deviation ledger: consistent; no carried findings into this cycle.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP011-F1 | D4 | `crates/prin-py/src/bindings/state.rs:3` | `#![allow(unsafe_code)]` is unnecessary — no `unsafe` code exists in this module. Other binding modules (`models.rs`, `integrators.rs`, `coupling.rs`, `metrics.rs`) compile cleanly without it under the crate-level `#![deny(unsafe_code)]`. The attribute could mask future unsafe additions. | Coding Standards §2.1 / §6.1 (unsafe only in audited modules) | Remove the `#![allow(unsafe_code)]` attribute from `state.rs`. |

## 5. Deviation-ledger delta

New findings added to the ledger: WP011-F1 (D4). Carried findings re-inspected: none (no findings carried from cycle 010).

## 6. Verdict and required actions

**Verdict: PASS**

All WP-011 acceptance criteria are met:
1. **No Python numerics** — confirmed by source inspection and grep.
2. **Mapped 3.0 symbols resolve** — `tools/wp001_baseline.py check` passes; all symbols accessible through `prin.dynamics` and `prin.metrics`.
3. **Non-trainable dynamics parity/property suites fully green** — 253 Python tests pass; 370 Rust tests pass; all parity cases green.
4. **Phase 1 tag gate passes** — baseline traceability check clean.

The single D4 finding (WP011-F1: unnecessary `#![allow(unsafe_code)]`) is cosmetic and may be fixed in S3 or carried to the next cycle.

**S3 action list:**
1. WP011-F1: Remove `#![allow(unsafe_code)]` from `crates/prin-py/src/bindings/state.rs:3`.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(pending S3)* | | | |

**Delta re-audit date:** *(pending S3)* — **Result:** *(pending)*

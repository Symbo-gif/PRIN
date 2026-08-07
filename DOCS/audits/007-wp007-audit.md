# PRIN Audit Report — Cycle 007 / WP-007

**Date:** 2026-08-07
**Auditor:** Devin (AI pair)
**Scope:** WP-007 "Oscillator dynamics models" — `crates/prin-dynamics/src/models.rs`, `crates/prin-dynamics/src/coupling.rs`, `crates/prin-dynamics/src/state.rs`, `crates/prin-dynamics/src/lib.rs`
**Sessions:** 0025 S1 implementation; 0026 S2 this audit
**Active brief:** `DOCS/sessions/phase-1/0026-wp007-s2-oscillator-dynamics-models.md`
**Git state:** `feat/wp006-oscillator-state` @ `c1a9027`
**Pre-S1 baseline:** `a83bd48` (WP-006 S4 documentation baseline)
**S1 implementation range:** `a83bd48..c1a9027` (intermediate `d1e6e0a` is the EA-001 executive-audit artefact, not WP-007 S1)
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-007 delivers the `Dynamics` trait and the `KuramotoOscillator`, `StuartLandauOscillator`, and `HopfOscillator` models in `prin-dynamics`. All three models implement MeanField, Full (custom or uniform `K/N`), and SparseKnn coupling; `StateDerivatives` with `dphase`/`damplitude`/`dfrequency` and derivative guards; and typed constructors/setters returning `StateError`. The S1 code and tests are written in tandem, the default and `strict-checks` builds are green, and security/dependency scans are clean. Rust line coverage on the new `prin-dynamics` code is 97.8% line / 97.4% region, and the Python parity suite remains green.

The audit raises two **D2** test-coverage/parity findings, one **D3** numerical-parity/plan-drift finding, and two **D4** hygiene/doc findings. No D1 trajectory breach is found.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared `Dynamics` trait and Kuramoto/Stuart–Landau/Hopf models; `prin-dynamics::integrate` remains a placeholder per the out-of-scope log |
| Plan/architecture conformance (A2) | PASS | New code lives in `prin-dynamics`; no numerics in Python; explicit `OscillatorState`/`StateDerivatives`; `#![forbid(unsafe_code)]` retained; no hidden global RNG |
| Tests in tandem + coverage (A3) | ⚠️ | 21 new unit/property tests; `cargo llvm-cov` reports 97.8% line / 97.4% region; Kuramoto has strong closed-form assertions, but coupled Stuart–Landau and Hopf outputs are only checked for finiteness/shape (`WP007-F1`, `WP007-F2`) |
| Numerical parity + invariants (A4) | ⚠️ | Phase wrap, amplitude/derivative clamps, `N=1` uncoupled, zero-coupling, and sparse-kNN edge cases are tested; independent Rust-vs-PRINet derivative comparison shows exact agreement for Kuramoto/Hopf full paths, but 1e-8–1e-9 differences for mean-field and Stuart–Landau paths due to PRINet's internal `torch.complex64` (f32) arithmetic (`WP007-F3`) |
| Quality gates (A5) | PASS | `cargo fmt`, `cargo clippy` (default + `strict-checks`), `cargo doc -D warnings`, `ruff`, `mypy --strict`, `interrogate`, `bandit` all pass |
| Security (A6) | PASS | Snyk Code (medium+) and Snyk Open Source (low+) report 0 issues; `cargo audit` retains the allowed inherited `paste` RUSTSEC-2024-0436 warning; no new `unsafe` |
| Docstring/doc coverage (A7) | ⚠️ | All new public Rust symbols are documented; Sphinx build clean; `interrogate` 100% on `python/prin`; docstrings do not spell out the per-coupling-mode coupling term for Stuart–Landau/Hopf (`WP007-F5`) |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub markers in new source; `EVIDENCE/0017-wp005-s1-ort-probe.json` has an uncommitted timestamp drift from test runs (`WP007-F4`) |
| CI status (A9) | PASS | Local one-liner green; `.github/workflows/rust.yml` and `python.yml` unchanged in this WP |
| Artefact trail (A10) | PASS | WP-006 S4 project state and audit are present; S1 handoff `DOCS/experiments/0025-wp007-s1-handoff.md` is committed; session register is unchanged per S1 handoff constraints |

## 1.1 Acceptance reproduction

| WP-007 acceptance criterion | Independent result | Assessment |
|---|---|---|
| `Dynamics` trait | `Dynamics` trait with `compute_derivatives(&self, &OscillatorState) -> Result<StateDerivatives, StateError>` in `crates/prin-dynamics/src/models.rs` | MET |
| Kuramoto model | `KuramotoOscillator` with MeanField/Full/SparseKNN paths; full-path output matches PRINet 3.0.0 to rounding precision (see §3.3) | MET |
| Stuart–Landau model | `StuartLandauOscillator` with all coupling paths; complex-amplitude limit-cycle invariant verified; coupled full-path output differs from PRINet by ~1e-8 because Rust uses f64 complex and PRINet uses `torch.complex64` (f32) | MET mathematically; PARITY NOT YET DEMONSTRATED (`WP007-F3`) |
| Hopf model | `HopfOscillator` with all coupling paths; polar limit-cycle and `N=1` invariants verified; mean-field output differs from PRINet by ~1e-8 for the same f32-order-parameter reason | MET mathematically; PARITY NOT YET DEMONSTRATED (`WP007-F3`) |
| Enum-based coupling | `CouplingMode` enum in `crates/prin-dynamics/src/coupling.rs` with `MeanField`, `Full { matrix }`, `SparseKnn { k }` | MET |
| Mean-field coupling | Rust computes complex order parameter `Z` with f64 `atan2` and real/imag sums; PRINet uses `torch.complex64` for `exp(iφ)` and `z.angle()` (`models.rs:331-344` vs `prinet/core/propagation/oscillator_models.py:355-362`) | MET structurally; f32/f64 reconciliation needed (`WP007-F3`) |
| Full pairwise coupling | Optional custom matrix or uniform `K/N` with zero diagonal; O(N²) loops; matches PRINet exactly | MET |
| Sparse k-NN coupling | `build_phase_knn_index` reused; `K/k` effective coupling; `k` defaults to `ceil(log2 N)`; edge cases for `N=1` and invalid `k` handled | MET |
| State derivatives container | `StateDerivatives` with `dphase`, `damplitude`, `dfrequency`; validated lengths and `guard_derivatives` | MET |
| Typed errors | `StateError` used for empty population, length mismatch, non-finite values, out-of-range derivatives, and invalid k-NN; setters return `Result<(), StateError>` | MET |
| `strict-checks` behavior | `StateDerivatives::new` and `guard_derivatives` honor `#[cfg(feature = "strict-checks")]` | MET |
| Deterministic behavior / no hidden global RNG | All model constructors and setters take explicit parameters; no thread-local or global RNG introduced | MET |

---

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `torch`: 2.13.0+cpu
- `prinet`: 3.0.0 installed from `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main`

### 2.2 Scope and artefact commands

```powershell
git log --oneline a83bd48..HEAD
git diff --stat a83bd48..c1a9027
```

Key results:

```text
c1a9027 feat(WP-007): implement Dynamics trait and oscillator models
d1e6e0a docs(EA-001): complete executive audit session 001, governance, report, and remediation
086e473 docs(WP-006 S4): close WP-006 oscillator state, errors, and seed
```

```text
diff --stat a83bd48..c1a9027:
 crates/prin-dynamics/src/coupling.rs |   36 +
 crates/prin-dynamics/src/lib.rs      |    4 +
 crates/prin-dynamics/src/models.rs   | 1489 ++++++++++++++++++++
 crates/prin-dynamics/src/state.rs    |   75 +
 ... (executive-audit and documentation artefacts) ...
```

### 2.3 Python quality, test, and coverage commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp_full
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

Key results:

```text
ruff check: All checks passed
ruff format --check: 44 files already formatted
mypy: Success: no issues found in 16 source files
interrogate: 100.0% (min 95.0%)
bandit: No issues identified
pytest tests/ -m "not slow and not gpu": 172 passed, 6 deselected; coverage 99%
pytest tests/ parity/: 184 passed; coverage 99%
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
sphinx: build succeeded
```

### 2.4 Rust quality, test, and documentation commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy (default): 0 warnings
cargo clippy (--features strict-checks): 0 warnings
cargo test --workspace: 80 Rust tests passed (55 in prin-dynamics, 13 in prin-kernels, 6 in _prin_core, 2 in others)
cargo test --workspace --features strict-checks: 81 Rust tests passed (56 in prin-dynamics)
cargo doc -D warnings: 0 warnings
```

### 2.5 Rust coverage commands

```powershell
cargo llvm-cov -p prin-dynamics --features strict-checks
```

Key results:

```text
Filename       Regions  Missed  Cover    Functions  Missed  Executed  Lines  Missed  Cover
coupling.rs    3        0       100.00%  1          0       100.00%   3      0       100.00%
models.rs      1837     50      97.28%   71         2       97.18%    1019   25      97.55%
seed.rs        392      10      97.45%   28         0       100.00%   201    1       99.50%
state.rs       829      19      97.71%   73         1       98.63%   507    12      97.63%
TOTAL          3061     79      97.42%   173        3       98.27%   1730   38      97.80%
```

### 2.6 Security and dependency commands

```powershell
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
snyk_code_scan path="C:\dev\PRIN" severity_threshold="medium"
snyk_sca_scan path="C:\dev\PRIN" all_projects="true" severity_threshold="low" command="C:\dev\PRIN\.venv\Scripts\python"
```

Key results:

```text
cargo audit: 1 allowed warning (paste RUSTSEC-2024-0436), no new issues
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
snyk_code_scan (medium+): 0 issues
snyk_sca_scan (low+): 0 issues
```

---

## 3. Numerical parity reproduction

### 3.1 Reference implementation authority

The numerical authority for the golden corpus is `prinet==3.0.0` installed from the local archive. The relevant files are:

- `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/oscillator_models.py`
- `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/oscillator_state.py`

### 3.2 Ad-hoc Rust-vs-PRINet derivative comparison

Because WP-007 does not wire the Rust `Dynamics` trait into an integrator or into the parity harness, an independent ad-hoc comparison was performed by constructing the same `OscillatorState` and parameters in both `prinet` and `prin-dynamics` and calling `compute_derivatives`.

The Python reference script (`C:\Users\there\AppData\Local\Temp\prinet_check.py`) and a standalone Rust binary (`C:\Users\there\AppData\Local\Temp\prin_rust_check`) were used. These files are temporary evidence only and are not committed.

Representative cases and results:

**Kuramoto Full (N=3, K=1.5, λ=0.1, γ=0.01, phases [0.0, 0.2, 1.0], amplitudes all 1.0, frequencies all 1.0)**

| quantity | PRINet 3.0.0 | Rust `KuramotoOscillator` | max |Δ| |
|---|---|---|---|
| dphase | [1.5200701578014788, 1.259343380052231, 0.2205864621462903] | [1.5200701578014788, 1.2593433800522309, 0.2205864621462903] | < 1e-15 |
| damplitude | [0.6601844418546907, 0.7383866435942036, 0.5185045076076525] | [0.6601844418546907, 0.7383866435942036, 0.5185045076076525] | 0 |
| dfrequency | [0.001733567192671596, 0.000864477933507436, -0.0025980451261790323] | [0.0017335671926716, 0.0008644779335074, -0.0025980451261790] | < 2e-16 (format rounding) |

**Kuramoto MeanField (N=2, K=1.0, λ=0.1, γ=0.01, phases [0.1, 0.5], amplitudes [1.0, 1.2], frequencies [1.0, 2.0])**

| quantity | PRINet 3.0.0 | Rust `KuramotoOscillator` | max |Δ| |
|---|---|---|---|
| dphase | [1.2336510028046368, 1.805290836783974] | [1.2336510053851901, 1.8052908288456748] | 2.6e-9 |
| damplitude | [0.9526365699131317, 0.9405304715989121] | [0.9526365964017310, 0.9405304970014424] | 2.7e-8 |
| dfrequency | [0.001168254981733353, -0.0009735457891719377] | [0.0011682550269260, -0.0009735458557716] | 7e-11 |

**Hopf MeanField (N=3, K=1.0, μ=1.0, γ=0.01, phases [0.1, 0.5, 1.0], amplitudes [1.5, 0.5, 1.0], frequencies [1.0, 2.0, 1.5])**

| quantity | PRINet 3.0.0 | Rust `HopfOscillator` | max |Δ| |
|---|---|---|---|
| dphase | [1.2173413382538607, 1.9301986572827874, 1.0284322865210977] | [1.2173413512848463, 1.9301986834274847, 1.0284322887522244] | 2.7e-8 |
| damplitude | [-1.0142865242388244, 1.2947246650232098, 0.7904020546010853] | [-1.0142865115759643, 1.2947246842982336, 0.7904020777837278] | 2.3e-8 |
| dfrequency | [0.0010867066912693042, -0.00011633557119535445, -0.0015718923782630076] | [0.0010867067564242, -0.0001163355276209, -0.0015718923708259] | 6.5e-11 |

**Hopf Full (N=3, K=1.5, μ=1.0, γ=0.01, phases [0.0, 0.2, 1.0], amplitudes all 1.0, frequencies all 1.0)**

| quantity | PRINet 3.0.0 | Rust `HopfOscillator` | max |Δ| |
|---|---|---|---|
| dphase | [1.5200701578014788, 1.259343380052231, 0.2205864621462903] | [1.5200701578014788, 1.2593433800522309, 0.2205864621462903] | < 1e-15 |
| damplitude | [0.7601844418546907, 0.8383866435942036, 0.6185045076076525] | [0.7601844418546907, 0.8383866435942036, 0.6185045076076525] | 0 |
| dfrequency | [0.001733567192671596, 0.000864477933507436, -0.0025980451261790323] | [0.0017335671926716, 0.0008644779335074, -0.0025980451261790] | < 2e-16 |

**Stuart–Landau Full (N=2, K=1.0, μ=1.0, phases [0.0, 0.2], amplitudes all 1.0, frequencies all 1.0)**

| quantity | PRINet 3.0.0 | Rust `StuartLandauOscillator` | max |Δ| |
|---|---|---|---|
| dphase | [1.0993346646428108, 0.9006653732161427] | [1.0993346653975307, 0.9006653346024693] | 7.5e-10 |
| damplitude | [-0.00996670126914978, -0.009966720198626544] | [-0.0099667110793792, -0.0099667110793792] | 1.0e-8 |
| dfrequency | [0.0, 0.0] | [0.0, 0.0] | 0 |

### 3.3 Root-cause analysis

The differences in mean-field Kuramoto/Hopf and full Stuart–Landau are not from a bug in the Rust implementation. They are explained by the PRINet 3.0 reference performing part of the computation in `torch.complex64` (f32) even when the model is constructed with `dtype=torch.float64`:

- Kuramoto mean field: `z = (amp * torch.exp(1j * phase.to(torch.complex64))).mean(dim=-1); R = z.abs().float(); psi = z.angle().float()`.
- Hopf mean field: same order-parameter computation, with `R` and `psi` then downcast to float32.
- Stuart–Landau full: `z = amp * torch.exp(1j * phase.to(torch.float64)).to(torch.complex64)` and subsequent complex arithmetic in `complex64`.

In contrast, the Rust implementation uses `f64` real arithmetic for Kuramoto/Hopf order parameters and `Complex64` (f64 complex) for Stuart–Landau. The Rust code is therefore mathematically more accurate, but it is not bit-for-bit with the f32-complex reference. The trajectory tolerance of `rtol=1e-6, atol=1e-8` may absorb the 1e-8 per-step drift, but the 1e-10 metric tolerance will not. This is an unlisted numerical hazard and a plan-level parity reconciliation item.

---

## 4. Detailed findings

| ID | Severity | Location | Description | Violated plan/standard clause | S3 remediation |
|---|---|---|---|---|---|
| **WP007-F1** | D2 | `crates/prin-dynamics/src/models.rs` (unit tests) | Coupled derivative outputs for `StuartLandauOscillator` and `HopfOscillator` are not asserted against closed-form or PRINet 3.0 reference values. Existing tests only verify construction, uncoupled limit-cycle behavior, and finiteness for coupled paths. | Testing_Standards §2 (per-module math correctness); A3 (tests in tandem) | Add reference-comparison unit tests for coupled Stuart–Landau and Hopf in Full/MeanField/SparseKnn modes, using the ad-hoc PRINet-vs-Rust cases from §3.2 as a starting point. |
| **WP007-F2** | D2 | `parity/test_parity_differential.py` (S1 evidence map) | The S1 handoff cites `test_parity_differential.py` corpus-regeneration as WP-007 golden-case evidence, but these tests compare PRINet 3.0 to itself, not the new Rust `Dynamics` implementation. No committed Rust-vs-PRINet derivative parity test exists. | Testing_Standards §2 (parity cases for touched primitives); A4 (numerical parity) | Create a committed parity test for `prin-dynamics` models (e.g. `crates/prin-dynamics/tests/parity_models.rs` or a Python bridge once WP-011 lands) that compares `Dynamics::compute_derivatives` against `prinet.compute_derivatives` for the same initial state and parameters, with documented tolerances. |
| **WP007-F3** | D3 | `crates/prin-dynamics/src/models.rs` (mean-field and Stuart–Landau paths) and `DOCS/PRIN_Project_Plan.md` §5 | The Rust f64 implementations diverge from the PRINet 3.0 reference because the reference uses `torch.complex64` (f32) internally for mean-field order parameters and Stuart–Landau complex amplitudes. This produces systematic 1e-8–1e-9 differences and is not listed among the plan's "preserved numerical hazards". | Plan §5 (numerical parity program / preserved numerical hazards); A4 (numerical parity) | Resolve the f64/f32 reference mismatch through one of: (a) document it as a preserved numerical hazard and adjust parity tolerances, (b) regenerate the golden corpus with a corrected f64 PRINet implementation, or (c) add an optional f32-complex code path to `prin-dynamics` for bit-for-bit reference matching. Record the decision in the Parity Report and/or a plan amendment. |
| **WP007-F4** | D4 | `EVIDENCE/0017-wp005-s1-ort-probe.json` | The file has an uncommitted working-tree change (updated `timestamp` from `test_probe_real_subconscious_model` or similar) and a CRLF→LF warning. | A8 (repository hygiene) | Either commit the updated evidence timestamp or add `EVIDENCE/*-probe.json` to `.gitignore` if these are transient test artifacts. |
| **WP007-F5** | D4 | `crates/prin-dynamics/src/models.rs` (rustdoc for `StuartLandauOscillator` and `HopfOscillator`) | Docstrings state the governing ODEs but do not define the coupling term `C_i` for each `CouplingMode` (`MeanField`, `Full { matrix }`, `SparseKnn`). The per-mode formulas are only in the implementation. | Documentation_Standards §2 (public API docstrings) | Expand the model docstrings to include the explicit coupling-term formula for each coupling mode, matching the level of detail in the Kuramoto docstring. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP007-F1** (D2), **WP007-F2** (D2), **WP007-F3** (D3), **WP007-F4** (D4), **WP007-F5** (D4).

Carried findings re-inspected and unchanged by this WP:

- WP001-F8 (AMENDED) — GitHub secret scanning substitute remains in force.
- WP003-F1 (AMENDED) — `prin-py` Python-FFI `unsafe` exception remains in force.
- WP003-F3 (AMENDED) — WP-003/Phase 0 go/no-go documented as amendment #7.
- WP004-F1 (AMENDED) — inherited `paste` RUSTSEC-2024-0436 warning remains allowed under amendment #9; reconfirmed by `cargo audit`.
- WP004-F2 (AMENDED) — `#[cube(launch)]` non-instrumentability remains documented under amendment #10.
- WP004-F4 (AMENDED) — `prin-kernels` crate-level `unsafe` lint pattern remains under amendment #8.
- WP004-F5 (AMENDED) — Triton 3.0 direct comparison remains deferred to Phase 3/`gpu.yml` under amendment #11.
- WP005-F1–F4 (FIXED) — WP-005 S3 delta re-audit was CLEAN.
- WP006-F1–F3 (FIXED) — WP-006 S3 delta re-audit was CLEAN.

No open D1 findings are carried into WP-007.

---

## 6. Verdict and required actions

**Verdict:** `PASS-WITH-FINDINGS` — the WP-007 S1 implementation is in declared scope, the quality and security gates are green, the new oscillator models are mathematically correct, and Rust coverage is above the 95% threshold. The five findings above are not trajectory breaches (no D1), but the D2 findings must be fixed in S3 before the cycle can close; the D3 finding requires either an S3 fix or an approved plan amendment.

**Ordered S3 action list:**

1. **WP007-F1:** Add closed-form or PRINet-reference unit tests for coupled `StuartLandauOscillator` and `HopfOscillator` in all three coupling modes. Use the ad-hoc cases from §3.2 as seed data.
2. **WP007-F2:** Add a committed Rust-vs-PRINet derivative parity test that directly compares `Dynamics::compute_derivatives` to `prinet` for the same state and parameters, covering Kuramoto, Stuart–Landau, and Hopf. Until a Python bridge exists, this can live as a Rust integration test that loads `prinet` via a subprocess or uses hard-coded reference values with a documented provenance.
3. **WP007-F3:** Decide and document the f64/f32 numerical reconciliation. Options: (a) accept the f32-complex reference as a preserved numerical hazard, adjust the Parity Report tolerances, and document the expected 1e-8 per-step drift; (b) regenerate the golden corpus with a corrected f64 PRINet implementation; or (c) add an f32-complex mode to `prin-dynamics` for reference matching. Update `DOCS/PRIN_Project_Plan.md` §5 via an approved amendment if the plan text changes.
4. **WP007-F4:** Commit or ignore the uncommitted `EVIDENCE/0017-wp005-s1-ort-probe.json` change.
5. **WP007-F5:** Expand `StuartLandauOscillator` and `HopfOscillator` rustdoc with explicit per-`CouplingMode` coupling terms.

After these fixes, re-run the full local one-liner and perform a delta re-audit.

---

## 7. Closure table (appended by S3 remediation)

*To be completed in session 0027 (WP-007 S3).*

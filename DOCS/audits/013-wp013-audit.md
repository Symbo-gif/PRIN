# PRIN Audit Report — Cycle 013 / WP-013

**Date:** 2026-08-10
**Auditor:** Devin (AI pair)
**Scope:** WP-013 "Continuous band networks and temporal propagation" — `crates/prin-dynamics/src/bands.rs`, `crates/prin-dynamics/src/temporal.rs`, `crates/prin-py/src/bindings/bands.rs`, `crates/prin-py/src/bindings/temporal.rs`, `python/prin/_prin_core.pyi`, `python/prin/dynamics.py`, `tests/test_wp013_bands_temporal.py`
**Sessions:** S1 — session 0049 (implementation, commit `c2c7b062ada33f8bcf9ff5ce7ab9859dcb70270c`); S2 — session 0050 (this audit)
**Active brief:** `DOCS/sessions/phase-2/0050-wp013-s2-continuous-band-networks-and-temporal-propagation.md`
**Git state:** `main` @ `c2c7b062ada33f8bcf9ff5ce7ab9859dcb70270c`
**Verdict:** FAIL

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Rust `bands`/`temporal` core, Python bindings, and Python acceptance tests are present; no Rust-vs-PRINet parity cases or corpus entries for the new primitives |
| Plan/architecture conformance (A2) | ⚠️ | No Python numerics; crate layering preserved; `BandNetwork` hard-codes mean-field intra-band coupling while PRINet 3.0 reference uses `sparse_knn` |
| Tests in tandem + coverage (A3) | ✅/⚠️ | Rust unit/property tests and Python acceptance tests added in the same commit; line coverage ≥95%, function coverage slightly below on new modules |
| Numerical parity + invariants (A4) | ❌ | Capacity invariants and phase-continuity properties pass internally; no golden-trajectory parity evidence against PRINet 3.0 reference |
| Quality gates (A5) | ✅ | fmt, clippy `-D warnings`, ruff, mypy strict, interrogate, bandit, Sphinx, rustdoc all clean |
| Security (A6) | ✅/⚠️ | Changed code clean; Snyk Code reports 3 pre-existing Low path-traversal findings in `tools/wp001_baseline.py` (governed by `.snyk` ignores, not WP-013 scope) |
| Docstring/doc coverage (A7) | ✅ | Rust public items documented; `missing_docs` clean under `-D warnings`; Sphinx 0 warnings |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers in changed code; `__all__` consistent for new symbols |
| CI status (A9) | ✅ | Local reproduction of all gates green; `strict-checks` exercised |
| Artefact trail (A10) | ⚠️ | Predecessor S1 handoff note / evidence map is not present in the commit; session register still lists 0049 as READY |

---

## 2. Methodology

All commands executed on Windows, Python 3.14.0, Rust toolchain per `rust-toolchain.toml`.

```powershell
# Repository state
git rev-parse HEAD                                   # c2c7b062ada33f8bcf9ff5ce7ab9859dcb70270c
git show --stat c2c7b062ada33f8bcf9ff5ce7ab9859dcb70270c --name-only

# Rust quality gates
cargo fmt --all -- --check                           # exit 0
cargo clippy --workspace --all-targets -- -D warnings # exit 0
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0
cargo test --workspace                               # all pass
cargo test --workspace --features strict-checks      # all pass
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # exit 0, 0 doc warnings
cargo llvm-cov -p prin-dynamics --summary-only       # bands.rs 95.96% lines / 92.00% functions; temporal.rs 96.91% lines / 94.64% functions
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only  # bands.rs 95.96% lines / 92.00% functions; temporal.rs 96.91% lines / 94.64% functions
cargo llvm-cov -p prin-dynamics --show-missing-lines --ignore-filename-regex "^c:\\dev\\PRIN\\crates\\prin-(metrics|kernels|py)" --features strict-checks
cargo audit                                          # 1 inherited paste advisory (amendment #9)

# Python quality gates
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 48 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues in 18 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # No issues identified
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 298 passed, 6 deselected
.venv\Scripts\python -m pytest tests/test_wp013_bands_temporal.py -v --basetemp=.pytest_basetemp  # 36 passed
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

**Declared scope** (012-project-state.md §6): `prin-dynamics` — continuous hierarchical band networks (`bands` module: ThetaGamma 2-band, DeltaThetaGamma 3-band continuous ODE network) and temporal propagation (`temporal` module: complex-phasor phase blending plus EMA amplitude blending). Acceptance criteria: band/temporal golden trajectories and capacity invariants pass; phase continuity and numerical guards property-tested; PAC interactions exercised; Python bindings and stubs.

**Present in S1 commit `c2c7b06`:**
- `BandParams`, `PacPair`, `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `create_band_state` in `crates/prin-dynamics/src/bands.rs`.
- `ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator` in `crates/prin-dynamics/src/temporal.rs`.
- Corresponding `#[pyclass]` bindings in `crates/prin-py/src/bindings/bands.rs` and `crates/prin-py/src/bindings/temporal.rs`.
- Re-exports in `python/prin/dynamics.py` and type stubs in `python/prin/_prin_core.pyi`.
- 36 Python acceptance tests in `tests/test_wp013_bands_temporal.py`.

**Missing from S1 commit:**
- Rust-vs-PRINet 3.0.0 parity tests or new `parity/corpus/` entries for `BandNetwork` and `TemporalPropagator`.
- An S1 handoff note mapping each acceptance criterion to evidence.

### 3.2 A2 — Plan/architecture conformance

- **No Python numerics:** `python/prin/dynamics.py` remains a pure re-export module. ✅
- **Crate layering:** new bindings live in `prin-py`; `prin-dynamics` does not link Python. ✅
- **One algorithm, one implementation:** the band-network and temporal-blending math is implemented once in `prin-dynamics` and only wrapped in Python. ✅
- **Coupling-mode mismatch with reference:** `BandNetwork::compute_band_derivatives` (lines 381–427) hard-codes mean-field Kuramoto intra-band coupling (`1/N_b` order parameter). The PRINet 3.0 reference `ThetaGammaNetwork` and `DeltaThetaGammaNetwork` instantiate per-band `KuramotoOscillator` with `coupling_mode="sparse_knn"` and `MultiRateIntegrator` sub-stepping (see `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/networks.py` lines 72–87 and 270–305). Without parity evidence, this is an unvalidated scientific-fidelity change.

### 3.3 A3 — Tests in tandem + coverage

The S1 commit adds code and tests in the same commit:
- Rust unit tests for construction, validation, state partitioning, derivative finiteness, zero-PAC identity, capacity invariants, serialization, and `create_band_state` in `bands.rs`.
- Rust unit/property tests for phasor wrap-around, EMA clamping, temporal propagator initialization/convergence, and phase continuity in `temporal.rs`.
- Python acceptance tests mirroring the Rust tests in `tests/test_wp013_bands_temporal.py`.

`cargo llvm-cov` reports for the new modules:

| File | Lines | Functions |
|---|---|---|
| `bands.rs` | 95.96% | 92.00% |
| `temporal.rs` | 96.91% | 94.64% |

Line coverage meets the ≥95% gate. Function coverage is slightly below because several getter/setter paths (`EmaAmplitudeBlender::set_alpha`, `amp_min`, `amp_max`; `BandNetwork::band_params`, `pac_pairs`; the empty-path of `mean_frequency`) are not exercised by the current tests. Missed lines are listed in the `cargo llvm-cov --show-missing-lines` output (e.g., `bands.rs:240,255–258,301–303,306–308,330,438–443,475,563`; `temporal.rs:270–276,279–286`).

### 3.4 A4 — Numerical parity + invariants

**Green internal invariants:**
- `theta_gamma_capacity_matches_frequency_ratio`: capacity is `floor(f_gamma / f_theta)` and falls in `[3, 15]` for the test frequencies.
- `zero_pac_does_not_change_intra_band_structure`: with `m=0`, PAC adds zero amplitude derivative contribution.
- `synchronized_state_has_zero_phase_derivative_spread`: equal phases yield `dphase = omega`.
- `phase_continuity_under_small_perturbation`: a `1e-8` phase perturbation changes derivatives by less than `1e-4`.
- `phasor_blender_handles_wrap_around`: blending phases near `0` and `2π` correctly returns a value near `0`.

**Missing numerical parity:** There are no Rust-vs-PRINet 3.0.0 parity tests for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator`. The archived PRINet 3.0 reference contains `ThetaGammaNetwork`, `DeltaThetaGammaNetwork`, and `TemporalPhasePropagator` (see `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/networks.py` and `temporal.py`), so parity evidence is feasible. The existing 510 parity cases still pass, but none exercise the WP-013 primitives.

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | exit 0 |
| `cargo test --workspace` | all pass |
| `cargo test --workspace --features strict-checks` | all pass |
| `cargo doc -D warnings` | 0 warnings |
| `ruff check` | All checks passed |
| `ruff format --check` | 48 files already formatted |
| `mypy --strict` | Success: no issues in 18 source files |
| `interrogate` | 100.0% (106/106) |
| `bandit` | No issues identified |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| `Sphinx -W --keep-going` | build succeeded, 0 warnings |

### 3.6 A6 — Security

- Changed code contains no `unsafe`, no runtime codegen, and no new dependencies.
- `cargo audit` reports only the inherited `paste` RUSTSEC-2024-0436 advisory (amendment #9).
- `bandit` reports no issues.
- Snyk SCA reports 0 issues.
- Snyk Code reports 3 Low path-traversal findings, all in `tools/wp001_baseline.py`. These are pre-existing, covered by `.snyk` ignores, and outside WP-013 scope.

### 3.7 A7 — Docstring/doc coverage

All new public Rust items are documented; `#![warn(missing_docs)]` is clean. Python stubs cover the new classes and functions. Sphinx build passes with 0 warnings.

### 3.8 A8 — Repository hygiene

No TODO/FIXME/stub markers in the changed code. `python/prin/dynamics.py` `__all__` is updated and consistent with the new re-exports.

### 3.9 A9 — CI status

All local gates reproduced green on the S1 commit. `strict-checks` was exercised and passed.

### 3.10 A10 — Artefact trail

The S1 commit does not contain an S1 handoff note mapping acceptance criteria to evidence. The session register (`DOCS/sessions/SESSION_REGISTER.md` and 012-project-state.md) still lists session 0049 as `READY` rather than `COMPLETE`. The predecessor S4 cycle (WP-012) is committed and closed.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP013-F1 | D1 | `parity/corpus/`, `crates/prin-dynamics/tests/`, `tests/test_wp013_bands_temporal.py` | No Rust-vs-PRINet 3.0.0 parity tests or corpus entries for `BandNetwork`, `theta_gamma_network`, `delta_theta_gamma_network`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`, or `TemporalPropagator`. The numerical-parity claim for the new primitives is unverified. | Plan §5 numerical parity program; acceptance criteria in 012-project-state.md §6 and session 0049 brief | Generate reference trajectories from `prinet==3.0.0` `ThetaGammaNetwork`, `DeltaThetaGammaNetwork`, and `TemporalPhasePropagator`; add hard-coded Rust parity tests and/or corpus cases; verify within documented tolerances. |
| WP013-F2 | D2 | `crates/prin-dynamics/src/bands.rs:381–427` | `BandNetwork` hard-codes mean-field intra-band coupling. PRINet 3.0 reference uses `sparse_knn` coupling and per-frequency multi-rate sub-stepping, so the network dynamics differ from the reference implementation. | Plan §4/§5 (preserve scientific functionality and numerical parity) | Either (a) add coupling-mode dispatch (mean-field/full/sparse_knn) to `BandNetwork` and match the PRINet stepping/integrator scheme, or (b) amend the plan to document this deliberate architectural simplification and supply parity evidence for the chosen mean-field variant. |
| WP013-F3 | D3 | `DOCS/sessions/phase-2/0049-wp013-s1-continuous-band-networks-and-temporal-propagation.md` and S1 commit | No S1 handoff note / acceptance-criterion evidence map was committed. | Development Workflow and Audit Standards §3 S1 exit criteria; session 0049 brief | Add an S1 handoff note mapping each acceptance criterion (golden trajectories, capacity invariants, phase continuity, numerical guards, PAC interactions, coverage, quality gates) to the test/command evidence that satisfies it. |
| WP013-F4 | D4 | `crates/prin-dynamics/src/bands.rs`, `crates/prin-dynamics/src/temporal.rs` | Function coverage on new modules is below 95%: `bands.rs` 92.00%, `temporal.rs` 94.64%. Missed functions include getters/setters and empty-input branches (`EmaAmplitudeBlender::set_alpha`, `amp_min`, `amp_max`; `BandNetwork::band_params`, `pac_pairs`; `mean_frequency` empty path). | Testing Standards ≥95% coverage on new/changed code | Add regression tests for the uncovered getter/setter and empty-input branches to bring function coverage above 95%. |
| WP013-F5 | D4 | `crates/prin-dynamics/src/bands.rs:239–241`, `crates/prin-dynamics/src/bands.rs:253–272` | `BandNetwork::new` returns `BandError::EmptyBand { band: 0 }` when `band_sizes` is empty, which is semantically an empty band list rather than a band with zero oscillators. It also allows non-adjacent PAC pairs despite the `PacPair` docstring describing pairs as "between adjacent bands". | Repository hygiene / semantic correctness | Add a dedicated error variant for an empty band list or adjust the existing variant/index; enforce or document whether non-adjacent PAC pairs are intentional. |
| WP013-F6 | D4 | `crates/prin-dynamics/src/temporal.rs:74–212`, `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/temporal.py:30–116` | `TemporalPropagator` blends `alpha * new + (1-alpha) * old` for phases and amplitudes, while PRINet's `TemporalPhasePropagator` blends `alpha * prev + (1-alpha) * input`. The conventions are opposite for the same numeric value, and no mapping to the PRINet reference is documented. | Numerical parity / documentation parity | Document the parameter mapping (`TemporalPropagator.alpha` corresponds to `1 - PRINet.carry_strength`) and use it in parity tests, or align the API naming with the reference. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP013-F1** (D1), **WP013-F2** (D2), **WP013-F3** (D3), **WP013-F4** (D4), **WP013-F5** (D4), **WP013-F6** (D4).

Carried findings re-inspected: none (no findings carried from cycle 012).

Pre-existing security findings not added as WP-013 findings: the 3 Low path-traversal Snyk Code findings in `tools/wp001_baseline.py` are governed by `.snyk` ignores and are not in WP-013 scope.

---

## 6. Verdict and required actions

**Verdict: FAIL**

WP-013 S1 (`c2c7b06`) delivers a coherent, well-tested Rust-core implementation of continuous hierarchical band networks and temporal propagation, together with the required Python bindings and acceptance tests. All quality gates are green and the internal invariants (capacity, phase continuity, numerical guards, PAC identity at zero depth) pass. However, the WP-013 acceptance criteria explicitly require "band/temporal golden trajectories" to pass, and the PRIN numerical parity program (Plan §5) requires golden-trajectory evidence for touched primitives. No such parity tests or `parity/corpus/` entries were added, even though PRINet 3.0 contains directly comparable `ThetaGammaNetwork`, `DeltaThetaGammaNetwork`, and `TemporalPhasePropagator` references. This is a D1 trajectory breach. In addition, the chosen mean-field intra-band coupling in `BandNetwork` differs from the PRINet 3.0 `sparse_knn` reference (D2), and the S1 handoff note / evidence map is missing (D3).

**Ordered S3 action list (severity order):**

1. **WP013-F1:** Add Rust-vs-PRINet 3.0.0 parity evidence for the new primitives:
   - Generate reference trajectories from `prinet==3.0.0` for `ThetaGammaNetwork`, `DeltaThetaGammaNetwork`, and `TemporalPhasePropagator`.
   - Add hard-coded Rust parity tests (e.g., in `crates/prin-dynamics/tests/parity_bands.rs` and `parity_temporal.rs`) or extend `parity/test_parity_differential.py`.
   - Add corpus cases and manifest entries if the parity harness requires them.
   - Verify results within the documented tolerances.

2. **WP013-F2:** Resolve the intra-band coupling mismatch:
   - Option A: extend `BandNetwork` to support multiple coupling modes (mean-field/full/sparse_knn) and match the PRINet stepping scheme, then verify parity.
   - Option B: amend the project plan to document that WP-013 deliberately adopts mean-field continuous dynamics and provide parity evidence for that chosen variant.

3. **WP013-F3:** Add the S1 handoff note (`DOCS/sessions/phase-2/0049-wp013-s1-handoff.md` or equivalent) mapping each acceptance criterion to the command/test evidence that satisfies it.

4. **WP013-F4:** Add regression tests to raise function coverage on `bands.rs` and `temporal.rs` above 95%.

5. **WP013-F5:** Fix the semantic error for an empty `band_sizes` vector and clarify the PAC-pair adjacency rule.

6. **WP013-F6:** Document the `TemporalPropagator.alpha` ↔ `PRINet.carry_strength` mapping and apply it in parity tests.

After all D1–D3 findings are addressed, re-run the full A1–A10 checklist and a delta re-audit before entering S4 documentation.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP013-F1 | | | |
| WP013-F2 | | | |
| WP013-F3 | | | |
| WP013-F4 | | | |
| WP013-F5 | | | |
| WP013-F6 | | | |

**Delta re-audit date:** — **Result:**

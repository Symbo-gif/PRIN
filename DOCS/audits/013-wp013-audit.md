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

**S3 session:** 0051 (`DOCS/sessions/phase-2/0051-wp013-s3-continuous-band-networks-and-temporal-propagation.md`)
**S3 date:** 2026-08-10 **Remediator:** Claude Opus 5 (AI pair)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP013-F1 | FIXED | `d2c1f1c` | `crates/prin-dynamics/tests/parity_bands.rs` (12 cases) and `crates/prin-dynamics/tests/parity_temporal.rs` (6 cases), all green. Band cases cover per-mode intra-band derivatives vs `prinet ... KuramotoOscillator.compute_derivatives`, the composed 2-band and 3-band right-hand sides including the reference PAC target, RK4 golden trajectories at `n = 1` and `n = 10` for `mean_field` and `sparse_knn`, and `theoretical_capacity` vs the reference `MultiRateIntegrator` sub-step count. Temporal cases cover a single blend, a chained 5-frame golden sequence, wrap-around, clamp saturation, and a mapping-direction guard, vs `prinet ... TemporalPhasePropagator.propagate`. Measured worst-case drift: `2.22e-16` (sparse k-NN, the reference mode), `2.74e-9` (full), `1.19e-7` (mean-field — amendment #14 hazard), `~1 ulp` (temporal). |
| WP013-F2 | FIXED + AMENDED | `20673c4`; plan amendment #19 (`5e0c602`) | **Fixed:** `BandParams::with_coupling` adds `freq_adaptation_rate` and `coupling_mode`, so a band can use the reference's `sparse_knn` mode; intra-band derivatives are now computed by the crate's `KuramotoOscillator` on the band sub-state rather than a band-local copy of the mean-field equations. Parity per mode is verified in `parity_bands.rs`; `bands::tests::band_derivatives_match_standalone_kuramoto_per_mode` and `coupling_modes_produce_different_dynamics` guard the dispatch. **Amended:** the residual structural difference (continuous unified ODE, PAC as a relaxation term, sub-stepping delegated to the integrator) is recorded as plan amendment #19 with the parity evidence required for each consequence. |
| WP013-F3 | FIXED | `62843d4` | `DOCS/experiments/0049-wp013-s1-handoff.md` maps all twelve WP-013 acceptance criteria to their evidence, attributing each row to S1 or S3, and carries a provenance caveat stating it was written in S3 and does not alter the S2 verdict. |
| WP013-F4 | FIXED | `20673c4`, `62843d4` | `cargo llvm-cov -p prin-dynamics --summary-only` (identical with `--features strict-checks`): `bands.rs` 98.97% lines / 98.68% functions (was 95.96% / 92.00%); `temporal.rs` 99.79% lines / 100.00% functions (was 96.91% / 94.64%). Both gates ≥95%. New tests cover the `EmaAmplitudeBlender` accessors (`set_alpha`, `amp_min`, `amp_max`), `BandNetwork::band_params`/`pac_pairs`, the `mean_frequency` empty path, the non-positive slow-frequency capacity branch, the out-of-range `slow_band` arm, and both partition error mappings. |
| WP013-F5 | FIXED | `20673c4` | `BandError::NoBands` added; `BandNetwork::new(vec![], …)` now reports "band network requires at least one band, got an empty band list" instead of `EmptyBand { band: 0 }` (`bands::tests::no_bands_rejected_with_dedicated_variant`, Python `test_no_bands_rejected_with_distinct_message`). PAC adjacency resolved as documentation: any strictly slow→fast pair is intentional and permitted; `PacPair` rustdoc and the Python binding docstring corrected, with `non_adjacent_pac_pair_accepted` covering a delta→gamma pair in both languages. |
| WP013-F6 | FIXED | `20673c4`, `d2c1f1c` | The mapping `ComplexPhasorBlender::alpha = 1 − carry_strength` and `EmaAmplitudeBlender::alpha = 1 − amplitude_decay` is documented in the `temporal` module docs, on all three types, and on the three PyO3 classes. It is applied in `parity_temporal.rs` (references generated with `carry_strength = 0.2`, `amplitude_decay = 0.3`; tests run at `alpha = 0.8 / 0.7`) and guarded against the reversed reading by `parity_reversed_convention_does_not_match`. |

### 7.1 Additional defect found and fixed while producing WP013-F1 evidence

Producing golden trajectories required integrating a `BandNetwork`, which
surfaced a defect not raised in S2: `make_intermediate_state` and the DOPRI5
`stage_state` in `crates/prin-dynamics/src/integrate.rs` set `freq_band: None`
on every stage state. A `BandNetwork` therefore could not be driven by RK4,
RK45, or the exponential integrator at all — stages 2 and later lost the band
labels and `compute_derivatives` failed with `MissingBandLabels`, contradicting
the `bands` module documentation. Both sites now carry `freq_band` from the base
state; the labels are fixed rather than evolving, so this is numerically exact
and no existing parity value changed (`parity_integrators.rs`,
`parity_models.rs`, and the 510 corpus cases are unchanged and green).
Regression tests: `bands::tests::band_network_integrates_with_rk4` and
`band_network_integrates_with_multi_rate`. Fixed in `20673c4` as part of the
WP013-F1/F2 remediation rather than deferred, because the WP-013 acceptance
criterion "band golden trajectories pass" is unreachable without it.

### 7.2 Behaviour changes introduced by remediation

1. `dfrequency` is now propagated from the band model instead of forced to
   zero. Identical while `γ = 0`, which `BandParams::new` still sets.
2. A single-oscillator band follows the `KuramotoOscillator` `N ≤ 1` contract
   (`dφ = ω`, `dr = −λr`, `dω = 0`) instead of coupling to itself through its
   own order parameter (`bands::tests::single_oscillator_band_has_no_self_coupling`).
3. An invalid per-band coupling mode (e.g. sparse `k ≥ N_b`) is rejected at
   `BandNetwork::new` rather than at the first derivative evaluation.
4. `BandParams` gained two serialised fields; the round-trip test still passes
   and no committed artefact contains a serialised `BandParams`.

### 7.3 Delta re-audit (A1–A10)

| # | Dimension | Result | Evidence |
|---|---|---|---|
| A1 | WP scope conformance | ✅ | All declared WP-013 scope present; parity evidence and the S1 handoff note, previously missing, are now committed. No undeclared scope shipped — every change traces to a finding ID. |
| A2 | Plan/architecture conformance | ✅ | No Python numerics (`python/prin/dynamics.py` remains re-exports only). Crate layering unchanged. "One algorithm, one implementation" now holds for the band dynamics: the duplicated mean-field Kuramoto block is gone. The coupling-mode mismatch is resolved in code, with the residual composition difference governed by amendment #19. |
| A3 | Tests in tandem + coverage | ✅ | 24 new Rust tests (13 unit + 3 error-path + 12 parity band + 6 parity temporal, minus overlap) and 8 new Python acceptance tests, each committed with the code it covers. `bands.rs` 98.97%/98.68%, `temporal.rs` 99.79%/100%. |
| A4 | Numerical parity + invariants | ✅ | 18 new parity cases green at documented tolerances (§7 WP013-F1 row). Pre-existing parity unchanged: `cargo test --workspace` 501 passing (504 with `strict-checks`); `pytest parity/ -m parity` 510 passing. |
| A5 | Quality gates | ✅ | `cargo fmt --check` exit 0; `cargo clippy --workspace --all-targets -- -D warnings` exit 0, also with `--features strict-checks`; ruff check + format clean (48 files); `mypy --strict` clean (18 files); interrogate 100% (106/106); bandit 0 issues; Sphinx `-W --keep-going` 0 warnings. |
| A6 | Security | ✅/⚠️ | Snyk Code (CLI 1.1306.2, org `symbo-gif`, threshold low) on `crates/prin-dynamics/src` and `crates/prin-py/src`: **0 issues**. Whole-repository Snyk Code: 3 Low path-traversal findings, all pre-existing in `tools/wp001_baseline.py`, unchanged from S2 and outside WP-013 scope. `cargo audit`: only the inherited `paste` RUSTSEC-2024-0436 (amendment #9). `pip-audit` clean on both manifests. Snyk Open Source: the npm sub-project tested clean (30 dependencies, 0 issues); the Python manifests and `Cargo.lock` could not be resolved by the CLI (the documented SNYK-CLI-0000 limitation, EA-002), and the org has hit its monthly private-test limit — reported as **partially blocked locally, not passed**. No dependency manifest changed in this session (`git diff 0c24b64..HEAD` touches no `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, or `requirements.txt`), and CI's `snyk.yml` remains the authoritative gate. |
| A7 | Docstring/doc coverage | ✅ | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` exit 0; all new public items (`BandParams::with_coupling`, `BandError::NoBands`, the two new fields and getters) documented; `cargo test --doc --workspace` 22 doctests passing; interrogate 100%. |
| A8 | Repository hygiene | ✅ | No TODO/FIXME/stub markers in changed code. `__all__` and `.pyi` stubs updated for the new `BandParams` signature and getters. The reference generator lives under the gitignored `DOCS/test_and_benchmark_results/` (WP-009/WP-010 precedent) and is not committed tooling. |
| A9 | CI status | ✅ | All CI-equivalent gates reproduced locally and green, including the `strict-checks` clippy and test jobs. No benchmark regression gates are defined for `prin-dynamics`. |
| A10 | Artefact trail | ✅ | S1 handoff note committed (`62843d4`); this closure table appended; plan amendment #19 recorded in Project Plan §8.3; session register updated to mark 0049/0050 COMPLETE and 0051 COMPLETE. |

**Verification commands (S3):**

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace                               # 501 passing
cargo test --workspace --features strict-checks      # 504 passing
cargo test --doc --workspace                         # 22 doctests
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo llvm-cov -p prin-dynamics --summary-only
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
cargo audit
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp   # 306 passed, 6 deselected
.venv\Scripts\python -m pytest parity/ -m parity --basetemp=.pytest_basetemp                                                      # 510 passed
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
.venv\Scripts\python tools\wp001_baseline.py check
snyk code test --severity-threshold=low crates\prin-dynamics\src
snyk code test --severity-threshold=low crates\prin-py\src
snyk code test --severity-threshold=low .
snyk test --all-projects --severity-threshold=low --command=.venv\Scripts\python.exe
```

**Delta re-audit date:** 2026-08-10 — **Result: CLEAN**

All six S2 findings are closed (five FIXED, one FIXED + AMENDED via plan
amendment #19). One additional defect found while producing the F1 evidence was
fixed in the same remediation and is recorded in §7.1. No new deviation was
introduced. Snyk Open Source is reported as partially blocked locally per
Coding Standards §6, not as passing. WP-013 may proceed to S4 (session 0052).

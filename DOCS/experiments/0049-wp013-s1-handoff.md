# Session 0049 — WP-013 S1 Handoff Note

**Session:** 0049 — WP-013 S1: Coding — Continuous band networks and temporal propagation
**S1 commit:** `c2c7b062ada33f8bcf9ff5ce7ab9859dcb70270c`
**Author:** written retrospectively in session 0051 (WP-013 S3) as the remedy for
finding **WP013-F3 (D3)**, which recorded that the S1 commit shipped without an
acceptance-criterion evidence map
**Date:** 2026-08-10
**Status:** S1 delivered; audited in session 0050 (verdict FAIL, six findings);
remediated in session 0051

> **Provenance caveat.** This note is not contemporaneous with S1. It maps the
> WP-013 acceptance criteria to the evidence that exists in the repository, and
> states explicitly, per row, whether that evidence came from the S1 commit or
> from the S3 remediation. Nothing here upgrades the S1 verdict: the S2 audit
> (`DOCS/audits/013-wp013-audit.md`) remains the authority on what S1 did and
> did not deliver.

## Scope delivered by S1 (`c2c7b06`)

| File | Change |
|---|---|
| `crates/prin-dynamics/src/bands.rs` | Stub → `BandParams`, `PacPair`, `BandNetwork` (`Dynamics` impl), `theta_gamma_network`, `delta_theta_gamma_network`, `theoretical_capacity`, `create_band_state`, `BandError` |
| `crates/prin-dynamics/src/temporal.rs` | Stub → `ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator`, `TemporalError` |
| `crates/prin-dynamics/src/lib.rs` | Re-exports for the new public symbols |
| `crates/prin-py/src/bindings/bands.rs` | New — `PyBandParams`, `PyPacPair`, `PyBandNetwork`, `create_band_state_py` |
| `crates/prin-py/src/bindings/temporal.rs` | New — `PyComplexPhasorBlender`, `PyEmaAmplitudeBlender`, `PyTemporalPropagator` |
| `python/prin/_prin_core.pyi`, `python/prin/dynamics.py` | Stubs and re-exports (`__all__` 20 → 26 symbols) |
| `tests/test_wp013_bands_temporal.py` | New — 36 Python acceptance tests |

## Acceptance criteria → evidence map

Acceptance criteria are those declared for WP-013 in
`DOCS/reports/012-project-state.md` §6 and in the session 0049 brief.

| Acceptance criterion | Evidence | Delivered by |
|---|---|---|
| **Band golden trajectories pass** | `crates/prin-dynamics/tests/parity_bands.rs` — 12 cases against `prinet==3.0.0`: per-mode intra-band derivatives (`mean_field`, `full`, `sparse_knn`), the composed 2-band and 3-band right-hand sides, and RK4 golden trajectories at `n = 1` and `n = 10`, `dt = 0.01`, for both `mean_field` and the reference networks' `sparse_knn`. Worst-case drift: `2.22e-16` (sparse k-NN), `2.74e-9` (full), `1.19e-7` (mean-field, amendment #14 hazard). | **S3** (WP013-F1). S1 shipped no parity evidence — the D1 finding. |
| **Temporal golden trajectories pass** | `crates/prin-dynamics/tests/parity_temporal.rs` — 6 cases against `prinet ... TemporalPhasePropagator.propagate`: single blend, chained 5-frame sequence, 0/2π wrap-around, amplitude-clamp saturation, and a directional guard on the parameter mapping. Fully f64 on both sides; compared at `1e-12`. | **S3** (WP013-F1) |
| **Capacity invariants pass** | `bands::tests::theta_gamma_capacity_matches_frequency_ratio`, `delta_theta_gamma_capacity_uses_extreme_bands`, `capacity_single_band_is_zero`, `capacity_zero_for_non_positive_slow_frequency`; proptest `capacity_positive_for_valid_frequencies`. Cross-checked against the reference in `parity_bands::parity_capacity_matches_prinet_sub_step_count`: `theoretical_capacity` equals the `sub_steps = max(1, int(f_fast / f_slow))` PRINet's `ThetaGammaNetwork` gives its `MultiRateIntegrator`, for four frequency pairs. | S1 (internal invariants); **S3** (reference cross-check) |
| **Phase continuity property-tested** | `bands::proptests::phase_continuity_under_small_perturbation` (a `1e-8` phase perturbation moves derivatives by `< 1e-4`); `temporal::proptests::phase_continuity_small_perturbation` (a `1e-10` perturbation moves the blended phase by `< 1e-6`, compared on the circle); `temporal::tests::phasor_blender_handles_wrap_around`. | S1 |
| **Numerical guards property-tested** | `bands::proptests::theta_gamma_derivatives_always_finite`; `temporal::proptests::phasor_blend_output_is_wrapped` and `ema_blend_output_in_clamp_range`; `bands::tests::derivatives_respect_clamp`; `temporal::tests::clamp_amp_repairs_non_finite`. Guards preserved: derivative clamp `±1e4`, amplitude clamp `[1e-6, 10]`, phase wrap `% 2π`. | S1 |
| **PAC interactions between bands exercised** | `zero_pac_does_not_change_intra_band_structure` (m = 0 is the identity), `non_adjacent_pac_pair_accepted`, the 3-band cascade in `delta_theta_gamma_derivatives_finite`, and — against the reference PAC operator — `parity_composed_theta_gamma_mean_field`, `parity_composed_theta_gamma_sparse_knn`, `parity_composed_delta_theta_gamma_cascade`. | S1 (internal); **S3** (reference-checked composition) |
| **≥95% coverage on new/changed code** | `cargo llvm-cov -p prin-dynamics --summary-only`: `bands.rs` 98.97% lines / 98.68% functions; `temporal.rs` 99.79% lines / 100% functions. Identical under `--features strict-checks`. | S1 met the line gate (95.96% / 96.91%) but not the function gate (92.00% / 94.64%) — finding WP013-F4; **S3** closed it. |
| **Tests in tandem with code** | The S1 commit adds `bands.rs`/`temporal.rs` implementations together with 21 + 24 inline unit/property tests and 36 Python acceptance tests in the same commit — confirmed by the S2 audit (A3 ✅). | S1 |
| **Python bindings and stubs** | `PyBandParams`/`PyPacPair`/`PyBandNetwork`/`create_band_state_py`, `PyComplexPhasorBlender`/`PyEmaAmplitudeBlender`/`PyTemporalPropagator`, `_prin_core.pyi` stubs, `python/prin/dynamics.py` re-exports; 44 Python acceptance tests. | S1 (36 tests); **S3** (+8 tests for the coupling-mode surface) |
| **All quality gates clean** | See the gate table below. | S1, re-verified in S3 |
| **No Python numerics** | `python/prin/dynamics.py` is re-exports only; all band and temporal math lives in `prin-dynamics`. Confirmed by the S2 audit (A2 ✅). | S1 |
| **One algorithm, one implementation** | S1's `compute_band_derivatives` was a band-local second copy of the mean-field Kuramoto equations. S3 replaced it with a call into the crate's `KuramotoOscillator` on the band's sub-state, so there is now exactly one Kuramoto implementation. | **S3** (WP013-F2) |

## Quality gates (S3 verification run)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy strict | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — 501 |
| Workspace tests strict | `cargo test --workspace --features strict-checks` | PASS — 504 |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Coverage | `cargo llvm-cov -p prin-dynamics --summary-only` | PASS — `bands.rs` 98.97% / 98.68%, `temporal.rs` 99.79% / 100% |
| `cargo audit` | `cargo audit` | PASS — only the inherited `paste` RUSTSEC-2024-0436 (amendment #9) |
| ruff | `ruff check` + `ruff format --check` | PASS |
| mypy | `mypy python/prin --strict` | PASS |
| interrogate | `python -m interrogate -c pyproject.toml python/prin` | PASS — 100% |
| bandit | `python -m bandit -r . -c pyproject.toml` | PASS — 0 findings |
| pytest fast | `pytest tests/ -m "not slow and not gpu"` | PASS — 306 passed, 6 deselected |
| pytest parity | `pytest parity/ -m parity` | PASS — 510 |
| pip-audit | `pip_audit .` and `-r DOCS/sphinx/requirements.txt` | PASS |
| Sphinx | `sphinx-build -W --keep-going` | PASS — 0 warnings |
| Baseline | `tools/wp001_baseline.py check` | PASS |

Exact commands and outputs are in the S3 closure section of
`DOCS/audits/013-wp013-audit.md`.

## Numerical design decisions and preserved hazards

1. **Continuous ODE composition, not a stepper.** `BandNetwork` is a single
   `Dynamics` right-hand side over the concatenated state rather than PRINet
   3.0's per-band stepper with an embedded `MultiRateIntegrator`. Recorded as
   Project Plan amendment #19 with the parity evidence required for each of its
   three consequences.
2. **PAC as relaxation.** The reference assigns
   `A_fast ← A_fast·[1 + m·cos(mean(φ_slow) + offset)]` between band steps; the
   continuous form adds `λ_fast·(A_target − A_fast)` to `dA_fast/dt` toward the
   same target. Both use the identical modulation target, which the composed
   parity cases check against `prinet ... PhaseAmplitudeCoupling.modulate`.
3. **f32-complex mean-field hazard (amendment #14).** PRINet computes the
   mean-field order parameter through `torch.complex64` even for f64 input, so
   `CouplingMode::MeanField` parity is asserted at `1e-6` relative / `5e-7`
   absolute (measured worst case `1.19e-7`). The `sparse_knn` mode the reference
   band networks actually use is unaffected and matches to ~1 ulp.
4. **Blending-convention complement (WP013-F6).** PRIN's `alpha` weights the new
   frame, PRINet's `carry_strength`/`amplitude_decay` weight the carried frame;
   `alpha = 1 − carry_strength`. Documented in `temporal.rs` and enforced by
   `parity_temporal::parity_reversed_convention_does_not_match`.
5. **Single-oscillator bands.** Delegating to `KuramotoOscillator` adopts its
   `N ≤ 1` contract (`dφ = ω`, `dr = −λr`, `dω = 0`): an isolated oscillator no
   longer couples to itself through its own order parameter.
6. **`freq_band` is state, not decoration.** Integrator stage states now carry
   the band labels. Without this a `BandNetwork` could not be driven by
   RK4/RK45/exponential integrators at all — stages 2+ lost the labels and the
   dynamics failed with `MissingBandLabels`. The labels are fixed, so carrying
   them is numerically exact.

## Public API added (`prin_dynamics`)

- `bands`: `BandNetwork`, `BandParams`, `PacPair`, `BandError`,
  `theta_gamma_network`, `delta_theta_gamma_network`, `create_band_state`
- `temporal`: `ComplexPhasorBlender`, `EmaAmplitudeBlender`,
  `TemporalPropagator`, `TemporalError`

Python: `BandNetwork`, `BandParams`, `PacPair`, `create_band_state_py`,
`ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator`.

## Non-goals respected

- **No trainable discrete bands.** `DiscreteDeltaThetaGamma` and
  `prin-train::bands` are untouched (Phase 4, WP-022…WP-027).
- **No model training, no autodiff.**
- **No Python numerics.**
- **No GPU kernels.**

## Known limitations / notes for later work packages

1. **Whole-network stepper parity is not claimed.** Step-for-step equality with
   PRINet's `ThetaGammaNetwork.step` is out of scope by amendment #19; parity is
   established at the level of the intra-band terms, the PAC target, the
   composed right-hand side, the golden trajectories, and the capacity ratio.
2. **No `parity/corpus/` entries were added.** WP-013 follows the WP-012
   precedent of hard-coded Rust parity tests. Corpus entries for band and
   temporal primitives remain a candidate for a later WP if the differential
   harness is extended to composed networks.
3. **Per-band `Full { matrix: Some(..) }` cost.** The band model is constructed
   per derivative evaluation; this is `O(1)` for `MeanField`/`SparseKnn` and
   `O(N_b²)` for an explicit dense matrix — the same order as evaluating that
   mode, but a candidate for caching if dense per-band matrices become common.
4. **Band-aware sub-stepping** (different `sub_steps` per band in one integrator
   call) remains deferred per amendment #18; the reference's per-band ratio is
   available as `theoretical_capacity` and can be applied by driving the network
   with `MultiRateIntegrator`.

## Handoff

S1's deliverables, the S2 findings against them, and the S3 corrections are all
recorded above and in `DOCS/audits/013-wp013-audit.md`. S3 hands off to the
mandatory S4 documentation session (0052) per the Development Workflow Standards
§3. No session may self-certify completion.

# Session 0037 — WP-010 S1 Handoff Note

**Session:** 0037 — WP-010 S1: Coding — Phase metrics and chimera measures
**Author:** S1 coding session
**Date:** 2026-08-08
**Status:** S1 complete; handing off to mandatory S2 audit (session 0038)

## Scope delivered

This S1 session implemented the WP-010 S1 scope in the `prin-metrics` crate
(rebuild of PRINet 3.0 `core/measurement.py` and the Year-4-Q1 chimera
utilities in `utils/oscillosim.py`):

1. **Order parameters** — `crates/prin-metrics/src/order.rs`:
   `kuramoto_order_parameter`, `kuramoto_order_parameter_complex`,
   `inter_frame_phase_correlation`, `order_parameter_series`.
2. **Coherence (full + sparse)** — `crates/prin-metrics/src/coherence.rs`:
   `mean_phase_coherence`, `phase_coherence_matrix`,
   `sparse_mean_phase_coherence`.
3. **PSD** — `crates/prin-metrics/src/spectral.rs`:
   `power_spectral_density`, `extract_concept_probabilities` (rustfft-backed).
4. **Synchronization energy (full + sparse)** —
   `crates/prin-metrics/src/energy.rs`: `synchronization_energy`,
   `sparse_synchronization_energy`.
5. **Chimera metrics** — `crates/prin-metrics/src/chimera.rs`:
   `local_order_parameter`, `bimodality_index`, `strength_of_incoherence`,
   `discontinuity_measure`, `chimera_index`,
   `strength_of_incoherence_temporal`.
6. **Metastability** — `crates/prin-metrics/src/metastability.rs`: temporal
   standard deviation of the order parameter (PRIN extension; no PRINet 3.0
   analogue — definition documented in rustdoc).
7. **Measurement-facing k-NN wrapper** — `crates/prin-metrics/src/knn.rs`:
   `build_phase_knn` delegating to
   `prin_dynamics::state::build_phase_knn_index` (one algorithm, one
   implementation) with PRINet's `1 ≤ k < N` user contract.
8. **Typed errors** — `crates/prin-metrics/src/error.rs`: `MetricError` enum
   (9 variants) + internal validation helpers; all public metrics validate
   emptiness, finiteness, lengths, neighbour indices, and parameter ranges at
   the boundary and never panic on invalid input.
9. **Parity test data** — `crates/prin-metrics/tests/data/`:
   `prinet_reference_metrics.json`, `prinet_reference_chimera.json` (produced
   by an ad-hoc helper running `prinet==3.0.0` on `torch==2.13.0+cpu`,
   mirroring the WP-009 `parity_pac.rs` precedent; provenance embedded) and
   `corpus_metric_cases.json` (6 representative cases extracted from
   `parity/corpus`: 126 snapshots across Kuramoto/Hopf/Stuart–Landau,
   mean-field/full/sparse-kNN, Euler/RK4).

## Acceptance criteria → evidence mapping

| Acceptance criterion (session brief §Contract) | Evidence |
|---|---|
| Metrics/decompositions tolerance target `rtol=1e-10` is met | `tests/parity_metrics.rs` asserts every f64-reference-path quantity (order parameter, complex order parameter, mean phase coherence, coherence matrix, synchronization energy incl. explicit matrix, sparse coherence k=3/k=11, sparse energy k=3/k=11, inter-frame correlation) against embedded `prinet==3.0.0` f64 references at `rtol=1e-10, atol=1e-12` — **all pass**. Measured worst-case drift **8.58e-16** (one-off probe, deleted after measurement; ~2× machine epsilon, five orders of magnitude inside target). |
| Corpus golden cases green at registered tolerances | `tests/corpus_metrics.rs` compares Rust `kuramoto_order_parameter` / `mean_phase_coherence` against the PRINet-authored corpus arrays for 6 cases × 21 snapshots at the registered METRIC tolerance (`rtol=1e-8, atol=1e-12`, amendment #16) — **all pass**; measured worst-case drift **2.75e-15**. The `C = (N r² − 1)/(N − 1)` identity is additionally cross-checked on the corpus data. |
| `R` stays in `[0, 1]` | Order parameters, inter-frame correlation, sparse coherence, and local order parameters clamp to `[0, 1]` (exact mathematical range; floating-point accumulation can exceed it by ~1 ulp). Asserted in unit tests, property tests (`order_parameter_in_unit_interval`, etc.), parity tests, and for every corpus snapshot (`corpus_metrics.rs`). Coherence is clamped to `[-1, 1]` likewise. |
| Sparse/full variants agree where equivalent | `parity_sparse_full_agreement_for_synchronized_phases`: both full and sparse coherence equal exactly 1 for synchronized phases. `parity_sparse_energy_ratio_to_full_at_k_n_minus_1`: sparse energy at k=N−1, K=1 equals the dense default energy × the exact normalization ratio `N/(N−1)` (the `1/N` vs `1/k` invariant). Unit tests: `sparse_coherence_two_cluster_state`, `sparse_energy_k_full_ratio_to_dense`, `sparse_energy_synchronized_is_minus_k_n`. |
| ≥95% coverage on new/changed code | `cargo llvm-cov -p prin-metrics --summary-only`: **lines 99.53%**, regions 96.28%, functions 100% (all modules ≥ 98.86% lines). |
| Tests in tandem with code | Code and tests are in the same commit range: 104 inline unit/property tests + 22 integration parity tests + 19 doctests = **145 new tests**, all green. |
| `cargo fmt`, clippy `-D warnings`, Rust tests, rustdoc | `cargo fmt --all -- --check` exit 0; `cargo clippy --workspace --all-targets -- -D warnings` exit 0 (also with `--features strict-checks`); `cargo test --workspace` **367/367** (346 unit/integration + 21 doctests; identical under `--features strict-checks`); `cargo doc --workspace --no-deps` with `RUSTDOCFLAGS=-D warnings` exit 0. |
| ruff, mypy strict, interrogate, bandit, pytest, dependency audits | `ruff check` + `ruff format --check` clean; `mypy python/prin --strict` clean; interrogate 100%; `bandit -r . -c pyproject.toml` 0 findings; pytest fast 172 passed (6 deselected), full 184 passed; `cargo audit` clean except the inherited `paste` RUSTSEC-2024-0436 warning (amendment #9); `pip-audit` clean (project + `DOCS/sphinx/requirements.txt`); Snyk Code (CLI, authenticated, low threshold) on `crates/prin-metrics/src`: **0 issues**. |
| Validate public inputs, typed errors, document all public API | Every public function validates at the boundary and returns `MetricError` variants (no panics); 100% public-item rustdoc (rustdoc gate enforces); 19 executable doctests. |
| Preserve deterministic Seed flow | No stochastic entry points introduced: all metrics are deterministic pure functions of their inputs; `build_phase_knn` delegates to the deterministic sort-based index in `prin-dynamics`. No hidden RNG. |
| Benchmark before/after evidence for performance work | N/A — no performance work in this WP (no criterion benchmarks defined for `prin-metrics` yet; criterion dev-dependency retained for future WPs). |

## Quality gates (commands and results)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy strict | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — 367 tests (167 dynamics + 34 parity_integrators/models/pac + 13 kernels + 6 `_prin_core` + 126 metrics + 21 doctests) |
| Workspace tests strict | `cargo test --workspace --features strict-checks` | PASS |
| Rustdoc | `set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps` | PASS |
| Cargo audit | `cargo audit` | PASS — only inherited `paste` RUSTSEC-2024-0436 (amendment #9); rustfft 6.4.1 introduced no advisories |
| Coverage | `cargo llvm-cov -p prin-metrics --summary-only` | PASS — lines 99.53%, regions 96.28%, functions 100% |
| Snyk Code | `snyk code test --severity-threshold=low crates\prin-metrics\src` | PASS — 0 issues (org `symbo-gif`) |
| Snyk Open Source | not runnable locally for this repo's manifests (SNYK-CLI-0000/SNYK-OS-0001, documented in EA-002); fallbacks `pip-audit` + `cargo audit` clean; CI `python.yml` Snyk SCA job is authoritative | BLOCKED locally, fallbacks PASS |
| ruff | `.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/` + `ruff format --check` | PASS |
| mypy | `.venv\Scripts\mypy python/prin --strict` | PASS |
| interrogate | `.venv\Scripts\python -m interrogate -c pyproject.toml python/prin` | PASS — 100% |
| bandit | `.venv\Scripts\python -m bandit -r . -c pyproject.toml` | PASS — 0 findings |
| pytest fast | `.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp` | PASS — 172 passed, 6 deselected |
| pytest full | `.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full` | PASS — 184 passed |
| pip-audit | `.venv\Scripts\python -m pip_audit .` and `-r DOCS/sphinx/requirements.txt` | PASS — no known vulnerabilities |

## Numerical design decisions and preserved hazards

1. **f64 reference authority.** Order parameter, complex order parameter, mean
   phase coherence, coherence matrix, synchronization energy, sparse
   coherence/energy, and inter-frame correlation are computed in f64,
   matching PRINet 3.0's `torch.float64` paths. Measured parity drift
   ≤ 8.58e-16 vs the embedded references.
2. **PSD complex64 hazard (preserved, cf. amendment #14).** PRINet 3.0
   evaluates `amplitude · exp(iφ)|_{complex64}` — the complex exponential is
   truncated to `complex64` before the FFT regardless of amplitude dtype.
   PRIN keeps the pure-f64 path instead of reproducing the truncation;
   PSD/concept-probability parity uses the documented `1e-6` tolerance
   (measured drift 9.99e-7). Documented in `spectral.rs` module docs.
3. **Chimera f32 hazard (preserved, cf. amendment #14).** PRINet 3.0
   evaluates `local_order_parameter` in `complex64` and the remaining chimera
   utilities in `torch.float32`; PRIN computes in f64 and parity uses `1e-6`
   (documented in `chimera.rs` module docs). The discrete outputs
   (discontinuity mask, η) match PRINet exactly for the fixture.
4. **Invariant clamps.** `R`, `ρ`, sparse coherence, and local `r_i` are
   clamped to `[0, 1]`; mean phase coherence to `[-1, 1]`. These guards
   protect the exact mathematical range against ~1 ulp accumulation noise
   (WP-010 acceptance: "R stays in [0,1]") and have no measurable parity
   impact.
5. **`C = (N r² − 1)/(N − 1)` identity** between `mean_phase_coherence` and
   `kuramoto_order_parameter` is cross-checked in unit tests, property tests,
   and on the golden corpus.
6. **SI pad+conv semantics.** `strength_of_incoherence` replicates PRINet's
   `z_padded = [z[-w:], z, z[:w]]` + valid `conv1d` + `[:N]` slice exactly,
   including Python slice clamping for `window_size > N` (covered by a
   dedicated test).
7. **FFT.** `rustfft = "6.2"` (resolved 6.4.1) added to
   `[workspace.dependencies]`: pure-Rust, widely audited FFT needed for PSD
   (naive DFT would be O(N²)); forward-transform convention matches
   `torch.fft.fft` (unnormalized, negative exponent); Parseval invariant
   tested. `cargo audit` clean.

## Public API added (`prin_metrics`)

- `kuramoto_order_parameter`, `kuramoto_order_parameter_complex`,
  `inter_frame_phase_correlation`, `order_parameter_series`
- `mean_phase_coherence`, `phase_coherence_matrix`,
  `sparse_mean_phase_coherence`
- `power_spectral_density`, `extract_concept_probabilities`
- `synchronization_energy`, `sparse_synchronization_energy`
- `local_order_parameter`, `bimodality_index`, `strength_of_incoherence`,
  `discontinuity_measure`, `chimera_index`,
  `strength_of_incoherence_temporal`, `BIMODALITY_CHIMERA_THRESHOLD`,
  `DEFAULT_CHIMERA_THRESHOLD`
- `metastability`
- `build_phase_knn`
- `MetricError`

## Files changed

| File | Change |
|---|---|
| `Cargo.toml` | **Modified** — added `rustfft = "6.2"` to `[workspace.dependencies]` with justification comment |
| `Cargo.lock` | **Modified** — rustfft 6.4.1 + transitive deps |
| `crates/prin-metrics/Cargo.toml` | **Modified** — `rustfft.workspace = true`, `serde_json` dev-dependency for fixtures |
| `crates/prin-metrics/src/lib.rs` | **Modified** — expanded from stub docs to module declarations, public re-exports, numerics/invariant documentation |
| `crates/prin-metrics/src/error.rs` | **New** — `MetricError` (9 variants), validation helpers, `StateErrorExt` conversion (16 tests) |
| `crates/prin-metrics/src/order.rs` | **New** — order parameters + inter-frame correlation (21 tests incl. 4 property tests) |
| `crates/prin-metrics/src/coherence.rs` | **New** — coherence metrics full + sparse (16 tests incl. 3 property tests) |
| `crates/prin-metrics/src/spectral.rs` | **New** — PSD + concept probabilities (12 tests incl. 1 property test) |
| `crates/prin-metrics/src/energy.rs` | **New** — synchronization energy dense + sparse (8 tests) |
| `crates/prin-metrics/src/chimera.rs` | **New** — chimera metric set (18 tests incl. 3 property tests) |
| `crates/prin-metrics/src/metastability.rs` | **New** — metastability (5 tests incl. 1 property test) |
| `crates/prin-metrics/src/knn.rs` | **New** — measurement-facing k-NN wrapper delegating to `prin-dynamics` (7 tests incl. 1 property test) |
| `crates/prin-metrics/tests/parity_metrics.rs` | **New** — 12 parity tests vs embedded PRINet f64 references |
| `crates/prin-metrics/tests/parity_chimera.rs` | **New** — 6 parity tests vs embedded PRINet chimera references |
| `crates/prin-metrics/tests/corpus_metrics.rs` | **New** — 4 golden-corpus tests (126 snapshots) |
| `crates/prin-metrics/tests/data/*.json` | **New** — parity fixtures with embedded provenance |

## Non-goals respected

- **No tensor decompositions, no report generation** — untouched.
- **No Python numerics** — WP-010 is Rust-only; `python/prin` unchanged
  (Python API exposure is WP-011).
- **No GPU kernels** — CPU-only, as specified for Phase 1.
- **No scope creep** — only `crates/prin-metrics`, its manifest, and the
  workspace dependency list were touched.

## Out-of-scope discoveries (recorded for later WPs)

1. **Batched `(B, N)` metric variants.** PRINet's measurement functions
   accept batched input; the PRIN Rust API is per-snapshot (matching the
   corpus usage). WP-011's Python bridge can call per snapshot; a batched
   Rust API is a candidate for a later WP if performance evidence demands it.
2. **Neighbour-index topology builders.** PRINet's `ring_topology` /
   `small_world_topology` / `cosine_coupling_kernel` (traceability: WP-009)
   produce `(N, k)` neighbour indices; WP-009 delivered the `Topology`
   coupling-matrix builders instead. Chimera metrics take neighbour indices
   as input, so nothing was blocked here, but the index-builder variants need
   a home (WP-011 Python API or a future WP) to mirror the full PRINet
   surface.
3. **`extract_concept_probabilities` bin-index semantics.** PRINet compares
   concept centre frequencies directly against FFT bin indices (no sampling
   scaling); reproduced and documented, but downstream consumers should be
   aware when wiring concept extraction in later phases.

## Known limitations / notes for S2

1. **Parity tolerance stratification** is documented per module: f64 paths at
   `rtol=1e-10` (acceptance target; measured ≤ 8.58e-16), corpus at the
   registered `rtol=1e-8` (measured ≤ 2.75e-15), PSD/chimera f32-hazard paths
   at `1e-6` (measured ≤ 9.99e-7). S2 should verify the tolerance
   stratification against plan §5 / amendment #14 / amendment #16.
2. **Reference generation provenance.** Fixtures were produced by an ad-hoc
   helper (`DOCS/test_and_benchmark_results/wp010_generate_prinet_references.py`,
   gitignored, not committed tooling — WP-009 precedent) using the venv's
   `prinet==3.0.0` / `torch==2.13.0+cpu`; provenance blocks are embedded in
   each fixture.
3. **Coverage** measured with `cargo llvm-cov` (lines 99.53% / regions
   96.28% / functions 100%); the region-cover shortfall is concentrated in
   proptest macro expansion regions, not logic branches.
4. **Metastability** is a PRIN extension with no PRINet counterpart; the
   definition (population standard deviation of the per-snapshot order
   parameter, bounded by `[0, 0.5]`) is documented in rustdoc. S2 should
   confirm this is acceptable under the WP declaration's "metastability"
   scope item.

## Handoff

S1 is complete. All acceptance criteria are evidence-mapped above. Handing
off to the mandatory S2 audit (session 0038) per the Development Workflow
Standards §3. S1 may not self-certify completion.

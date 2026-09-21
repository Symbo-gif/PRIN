# Pre-registration — EXP-001: Golden-trajectory numerical parity

**Status:** DRAFT
**Authors:** MichaelMaillet (maintainer, to countersign at E2); Claude Sonnet 5 (AI pair, drafting)
**Date:** 2026-09-21
**Maintainer approval:** _pending — recorded at E2 (session 0155)_
**Code version:** `prin` 1.0.0-rc1 @ `8ce115f` (campaign baseline SHA; this
document is drafted on branch `campaign/0154-exp001-e1`, which carries the
DV-038/DV-039 hotfix in addition to `8ce115f` — the exact HEAD SHA at freeze
is recorded in `log.md` line 1 per campaign plan §12.4)
**Session briefs:** [0154 — E1](../../sessions/phase-7/0154-exp001-e1-golden-trajectory-numerical-parity.md)
through [0158 — E5](../../sessions/phase-7/0158-exp001-e5-golden-trajectory-numerical-parity.md)
**Related plan items:** Project Plan §5 (numerical parity program), §6 Phase 7
row, §8.1, §9 DoD #12; Experimentation Standards §2–§4; campaign plan
(`DOCS/experiments/campaign-plan.md`) §2.1 row EXP-001/C1, §5–§10, §12

---

## 0. Reconciliation binding on this pre-registration (campaign plan §2.1)

Per the brief's own header ("If this brief conflicts with a normative
standard, the standard wins") and campaign plan §2.1, this pre-registration
targets the **reconciled** values below, not the brief's unreconciled prose:

| Quantity | Reconciled target | Source |
|---|---|---|
| Trajectory tolerance | `rtol=1e-6, atol=1e-8` (float64 reference) | Plan §5 rule 2; corpus `manifest.json` `trajectory_rtol`/`trajectory_atol` |
| Metric/decomposition tolerance (cross-implementation) | `rtol=2e-6, atol=1e-12` | Plan §5 rule 2, amendments #16/#17; `prin.parity.schema.METRIC_RTOL/METRIC_ATOL` |
| Metric tolerance, single-runtime | `rtol=1e-10` where achievable | Plan §5 rule 2 (WP-010/WP-014 acceptance) — not separately re-verified by this experiment, which is cross-implementation by construction |
| GPU/wgpu kernel-path tolerance | `rtol=1e-5, atol=1e-6` (f32) | Testing Standards §3; `prin_kernels::equivalence::{DEFAULT_RTOL, DEFAULT_ATOL}` — **not** the f64 trajectory tolerance, because the fused kernels compute in f32 |
| `strength_of_incoherence*` non-hazard exception (amendment #25) | Not applicable to this experiment | The golden corpus's `CaseArrays` schema (`prin.parity.schema`) does not include `strength_of_incoherence`/`strength_of_incoherence_temporal` — those are chimera-specific measures owned by EXP-005. Cited here only because campaign plan §2.1's reconciliation column lists it against every C1 row; it binds no EXP-001 decision rule. |
| DV-007 (f64/f32 preserved hazard) | Not applicable to this experiment | DV-007 covers PRINet 3.0's own internal `torch.complex64` order-parameter arithmetic, already absorbed into the registered `rtol=2e-6` metric tolerance above. No additional exception is needed. |

## 1. Background and motivation

WP-001 through WP-036G established, work-package by work-package, that
`prin-dynamics` (the Rust numerical core) reproduces PRINet 3.0.0's oscillator
dynamics within the tolerances above; that evidence is scattered across ~40
work-package Audit/PSR pairs and the Rust-side `crates/prin-dynamics/tests/
parity_models.rs` suite. EXP-001 is the first Phase 7 campaign experiment
because every downstream experiment (§3.2 of the campaign plan) assumes
numerical parity: EXP-002's benchmark-result parity, EXP-003/EXP-004's
performance claims, and EXP-005–EXP-007's scientific replications are only
meaningful if the trajectories and derived metrics they are computed from
already match the reference implementation. This experiment answers, with a
single pre-registered, full-corpus-plus-fuzz confirmatory pass: **does the
shipped `prin` 1.0.0-rc1 numerical core reproduce PRINet 3.0.0's golden
trajectories and derived metrics within the registered tolerances, on the
full corpus, under randomized fuzzing, and repeatably?**

This is a confirmatory replication of an already-tested property (Phase 1–3
exit criteria required parity suites green), not a first-time exploration;
the campaign's contribution is doing so **exhaustively** (full 504-case
corpus, not a CI-selected subset), **adversarially** (≥1,000 hypothesis-fuzzed
cases outside the fixed corpus grid), and **with a permanent, immutable,
manifested artefact record** — which the pre-existing CI-gated parity suite
(`parity.yml`) does not produce (it reports pass/fail, not a stored,
versioned per-case evidence artefact).

## 2. Hypotheses (falsifiable, quantitative)

- **H1 (corpus parity):** Re-integrating the actual `prin` (Rust) numerical
  core from each of the 504 golden-corpus cases' stored initial state
  reproduces the PRINet-3.0-authored reference trajectory and metric arrays
  within the registered tolerances (§0) for **100% of the 504 cases**.
- **H2 (hypothesis-fuzzed parity, with a registered shadowing horizon):** For
  ≥1,000 hypothesis-fuzzed cases (drawn from the value ranges in
  `prin.parity.strategies`, §5 below), run from an identical explicit initial
  condition on both PRINet 3.0 and `prin`:
  - **H2a (within-horizon, pointwise):** every array value at trajectory
    steps `0..20` inclusive (the shadowing horizon `T* = 20`, defined in §6)
    satisfies the registered tolerance, for 100% of the ≥1,000 cases.
  - **H2b (beyond-horizon, distributional):** for the pooled set of
    `order_parameter` and `mean_phase_coherence` values at steps `21..n_steps`
    across every fuzzed case with `n_steps > 20`, the PRINet-3.0 and `prin`
    samples show no practically significant difference: a two-sided Welch
    t-test (`prin.y4q1_tools.welch_t_test`) at `α=0.05` is either
    non-significant, or significant with `|Cohen's d| < 0.2` (negligible,
    Cohen's convention), **and** the 95% bootstrap CI
    (`prin.y4q1_tools.bootstrap_ci`, 10,000 resamples, seeded per §7) on the
    mean paired difference contains 0.
- **H3 (bit-level seeded repeatability):** For one representative corpus case
  per each of the 14 `(model, coupling, integrator)` grid cells, running the
  `prin` reproduction twice from the identical stored initial state produces
  byte-identical (`numpy.array_equal`) output for every array, for 14/14
  cases.
- **H4 (GPU kernel-path tolerance-identity) — driver support pending, see
  §5.4:** The Kuramoto sparse-k-NN GPU derivative kernel
  (`prin._prin_core.GpuSparseKuramoto`, WP-036D) reproduces the CPU `prin`
  reference for every `kuramoto_sparse_knn_*` corpus case (72 cases) within
  `rtol=1e-5, atol=1e-6` (f32; Testing Standards §3), for 100% of those cases.

H1–H3 are addressed by the committed driver
(`benchmarks/campaign/exp001_driver.py`, tested in tandem —
`tests/test_exp001_driver.py`, 29/29 passing at freeze). H4's driver support
is **not yet committed**; §5.4 records why and what closes the gap before E3.

## 3. Expected results

| Hypothesis | Predicted direction | Predicted magnitude | Basis for prediction |
|---|---|---|---|
| H1 | Confirmed | 504/504 (100%) pass | Phase 1–3 exit criteria required the CI-gated parity suite green on this same corpus; a 4-case representative smoke test run during E1 driver development (`kuramoto_mean_field_euler`, `kuramoto_full_rk4`, `hopf_sparse_knn_rk4`, `stuart_landau_full_euler`, all `n=8, s=20`) passed 4/4 at the registered tolerance. |
| H2a | Confirmed | 100% within-horizon pass | Same basis as H1: the horizon `T*=20` is chosen to equal the corpus's own validated trajectory length. |
| H2b | Confirmed | `\|Cohen's d\| < 0.05` (well under the `0.2` registered threshold) | An 8-case pilot batch drawn by the fuzz sampler during E1 driver development (`seed_counter=0, seed_key=1`) showed 7/8 cases fully within tolerance at all steps; the one exception (`hopf, mean_field, rk4, N=26, n_steps=35`) breached the trajectory tolerance by a small margin (`max_abs_diff=1.13e-6` vs the `1e-8`-anchored `1e-6` relative bound, 2/936 array elements) only in the `phase_traj` array — consistent with float64 rounding-order divergence between two independently-implemented integrators accumulating past step 20, not a systematic bias. This pilot evidence is **not** a campaign result (Experimentation Standards §1.1: no post-hoc hypotheses from peeking at results); it is cited only as the basis for choosing `T*=20` and predicting a near-zero effect size beyond it, exactly as the pre-registration template invites ("PRINet 3.0 Table N / theory / **pilot**"). |
| H3 | Confirmed | 14/14 bit-identical | `prin`'s dynamics core is a pure function of its explicit inputs once an initial state is given (no internal RNG re-draw); a 4-case repeatability smoke test during driver development passed 4/4 bit-identical. |
| H4 | Confirmed, pending driver support | 72/72 pass | Testing Standards §3 already documents this tolerance as the established GPU-vs-CPU bound for existing kernel-equivalence tests (`crates/prin-kernels/src/equivalence.rs`); no contrary evidence exists. |

## 4. Failure conditions

**Falsification (per hypothesis):**

| Hypothesis | Outcome that refutes it |
|---|---|
| H1 | Any of the 504 cases has `within_tolerance=False` for any array, and the breach is not attributable to a registered abort criterion (§4 below) |
| H2a | Any within-horizon (`step ≤ 20`) array value breaches the registered tolerance in any fuzzed case |
| H2b | Beyond-horizon pooled Welch t-test is significant (`p<0.05`) with `\|Cohen's d\| ≥ 0.2`, or the 95% bootstrap CI on the mean paired difference excludes 0 while `\|d\| ≥ 0.2` |
| H3 | Any of the 14 representative cases produces a non-bit-identical rerun |
| H4 | Any of the 72 `kuramoto_sparse_knn_*` cases breaches `rtol=1e-5, atol=1e-6` on the GPU derivative kernel vs. the CPU reference |

Per campaign plan §10.4, **any H1/H2a/H3/H4 refutation is a D1** ("scientific
conclusion differs from PRINet 3.0" / cross-run seed mismatch), not a
publishable novelty: it blocks EXP-001's successor (EXP-002 E1, session 0159)
and triggers the four contingency correction sessions before the campaign
resumes. An H2b refutation (a *distributional* conclusion reversal beyond the
shadowing horizon) is likewise a D1 under the same clause, since it is still
"scientific conclusion differs from PRINet 3.0", just evaluated statistically
rather than pointwise.

**Abort criteria (invalid run, not a negative result) — campaign plan §10.1:**

1. NaN/Inf in any produced array, or `order_parameter`/`mean_phase_coherence`
   outside `[0, 1]`, or phase outside its wrapped range, or an
   amplitude/derivative clamp trip outside the documented hazard envelope
   (Plan §5 rule 6).
2. Seed irreproducibility on the H3 repeatability gate re-run of any
   configuration beyond the 14 registered cases (campaign plan §6.5).
3. Environment capture incomplete for a configuration the run requires — in
   particular, **fuzz mode (H2) aborts with `PrinetUnavailableError` if
   PRINet 3.0 is not importable** rather than silently skipping (verified
   behavior: `tests/test_exp001_driver.py::TestFuzzComparison::
   test_fuzz_unavailable_without_prinet`).
4. `tools.reproduce.verify_manifest` raises for any input corpus or the run's
   own output directory.
5. Budget exceeded (§9).
6. For H4 only: CUDA/wgpu unavailable, or the ONNX/CubeCL build lacks the
   kernel binding (`GpuSparseKuramoto is None`) — logged as
   `NOT EXECUTED — cuda feature not built`, verdict `INCONCLUSIVE`, per the
   reporting mechanics of campaign plan §5.4 (this is a build-configuration
   gap, not literally unavailable hardware — H1's RTX 4060 is present and
   CUDA-visible to `torch`, per E1 driver-development verification — but the
   same "never silently skipped, never reported negative" discipline applies).

**Reporting commitment on failure:** results are reported in full per
Experimentation Standards §1.2 regardless of outcome; H2's per-case pilot
evidence in §3 is disclosed as pilot data, never substituted for the
confirmatory ≥1,000-case run.

## 5. Method

### 5.1 Configurations

- **Corpus (H1, H3):** all 504 cases in `parity/corpus/manifest.json`
  (schema 1, generator `prinet==3.0.0`) — 3 models (kuramoto 216, hopf 216,
  stuart_landau 72) × 3 couplings (mean_field 144, full 216, sparse_knn 144)
  × 2 integrators (euler 252, rk4 252) × a fixed `(N, K, dt)` grid
  (`N∈{8,12,16,24}`, `K∈{0.5,1.0,2.0}`, `dt∈{0.005,0.01,0.02}`), each 20
  steps. H3 uses one representative case per one of the 14 valid
  `(model, coupling, integrator)` cells (stuart_landau only has `full`
  coupling, so 3 models × 3 couplings − 2 invalid stuart_landau cells = 7
  model×coupling combinations × 2 integrators = 14 cells); the four already
  identified in `parity/test_parity_differential.py`'s
  `_REPRESENTATIVE_CASES` plus ten more selected at E3 to complete the grid.
- **Fuzz (H2):** ≥1,000 cases drawn by `benchmarks.campaign.exp001_driver.
  draw_fuzz_spec`/`draw_fuzz_initial`, mirroring `prin.parity.strategies`'
  ranges: `model ∈ {kuramoto, hopf, stuart_landau}`; `coupling` valid for the
  model (stuart_landau is always `full`); `integrator ∈ {euler, rk4}`;
  `n_oscillators ∈ [8, 64]`; `n_steps ∈ [5, 50]`; `dt ∈ [0.001, 0.05]`;
  `coupling_strength ∈ [0.1, 4.0]`; model-specific parameters per §5.2's table
  reproduced from `prin.parity.strategies.model_parameters_strategy`. The
  explicit initial condition is drawn as `phase ~ U(0, 2π)`,
  `amplitude ~ U(0.5, 1.5)`, `frequency ~ U(-1, 1)`, fed identically into
  both implementations.
- **GPU kernel-path (H4):** the 72 `kuramoto_sparse_knn_*` corpus cases,
  executed on H1's CUDA backend via `prin._prin_core.GpuSparseKuramoto`
  (pending the driver support in §5.4).
- **Hardware/backend:** H1 CPU (primary, all of H1–H3); H1 CUDA (H4, pending);
  H1 wgpu (H4 scope currently limited to CUDA — no wgpu-equivalent kernel
  binding was found during E1 driver development; if one exists it is added
  before E3, else the wgpu leg is `INCONCLUSIVE` for the same
  build-configuration reason as CUDA if the feature is not compiled in). No
  H2/H3/H4 case is timed; this experiment measures correctness, not
  performance (that is EXP-003/EXP-004).

### 5.2 Model-specific fuzz parameter ranges (from `prin.parity.strategies`)

| Model | Extra parameters | Range |
|---|---|---|
| kuramoto | `decay_rate` | `[0.0, 0.5]` |
| kuramoto | `freq_adaptation_rate` | `[0.0, 0.05]` |
| hopf | `bifurcation_param` | `[-0.5, 2.0]` |
| hopf | `freq_adaptation_rate` | `[0.0, 0.05]` |
| stuart_landau | `bifurcation_param` | `[-0.5, 2.0]` |
| any, if `coupling=sparse_knn` | `sparse_k` | `[2, min(12, n_oscillators-1)]` |

### 5.3 Procedure

All three implemented modes are invoked through the single committed driver;
campaign runs never call `benchrunner` directly (campaign plan §7.1).

```bash
# H1 — full corpus (E3 invocation; 504 cases from the manifest)
python -m benchmarks.campaign.exp001_driver \
  --mode corpus --corpus-dir parity/corpus \
  --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-corpus-cpu \
  --label corpus-cpu --session 0156 --operator MichaelMaillet

# H3 — repeatability (14 representative cases, one --case-id per grid cell)
python -m benchmarks.campaign.exp001_driver \
  --mode repeatability --corpus-dir parity/corpus \
  --case-id <id_1> [... 14 total] \
  --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-repeatability-cpu \
  --label repeatability-cpu --session 0156 --operator MichaelMaillet

# H2 — fuzz (>=1000 cases; seed_key=1 per campaign plan §6.2)
python -m benchmarks.campaign.exp001_driver \
  --mode fuzz --n-fuzz-cases 1000 --seed-counter 0 --seed-key 1 \
  --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-fuzz-cpu \
  --label fuzz-cpu --session 0156 --operator MichaelMaillet
```

Each invocation writes exactly one result artefact
(`<mode>_<label>.json`, payload `{"cases": [...]}`, `prin.parity.harness.
ComparisonResult.to_dict()` per array) plus the run's `campaign-metadata.json`
sidecar (`exp_id="EXP-001"`, `run_id`, `session`, `operator`, `artefacts`).
E3 closes each run directory with `tools.reproduce.append_manifest`/
`verify_manifest` per the `benchmarks/results/EXP-001/README.md` rule.

### 5.4 Driver-support gap for H4 (recorded for E2 review)

During E1 driver development, `prin._prin_core.GpuSparseKuramoto` (the only
confirmed GPU-dispatchable execution path found — WP-036D, reached through
`prin._torch_compat.KuramotoOscillator._compute_derivatives_gpu`, sparse-k-NN
coupling only) was verified **absent** from the currently built `prin`
extension on H1, although H1's CUDA device itself is visible to `torch`
(`torch.cuda.is_available() == True`, `NVIDIA GeForce RTX 4060`):

```
>>> torch.cuda.is_available()
True
>>> hasattr(prin._prin_core, "GpuSparseKuramoto")
False
```

This means the current default build was not compiled with the `cuda`
feature flag (consistent with prior session notes that `maturin` needs
`--features cuda`). Two other model/coupling combinations
(`KuramotoOscillator` with `mean_field`/`full`, and both `HopfOscillator`
and `StuartLandauOscillator` regardless of coupling) have **no** GPU
dispatch override in `prin._torch_compat` at all — their `step`/`integrate`
always execute the CPU `_raw` path even when given a CUDA-resident tensor.
H4 is therefore pre-registered against the one combination that does have a
GPU execution path, not the full corpus.

**Committing a driver function without being able to run or test it against
real hardware here would violate "tests in tandem" (Coding Standards §5) and
Experimentation Standards §2 E3's driver-freeze discipline** — an untested
driver is exactly the kind of change §12.1 forbids adding at E3. This
pre-registration therefore names H4's exact hypothesis and tolerance now
(§2, §4) but defers `compare_kernel_path_case`'s implementation to a
documented pre-execution amendment: it is added, tested against a
`--features cuda` rebuild of `prin` on H1, and frozen **before E3 (session
0156) starts**, per the normal E1→E2 edit window (Experimentation Standards
§2 E2: "amendments before execution are normal edits"). If the `cuda`-feature
build is not available before E3, H4 is logged
`NOT EXECUTED — cuda feature not built` and reported `INCONCLUSIVE` (§4 item
6), not silently dropped, and the maintainer decides at E5/E6 whether this is
a build-provisioning action or a scope amendment — the same disposition
pattern the campaign plan already uses for DV-001 (Linux GPU host) and DV-006
(NPU).

## 6. Variables and controls

- **Independent variables:** oscillator model, coupling mode, integrator,
  `N`, `dt`, `n_steps`, coupling strength, model-specific parameters, initial
  condition, backend (cpu / cuda pending).
- **Dependent variables:** per-array `ComparisonResult` (`within_tolerance`,
  `max_abs_diff`, `max_rel_diff`, `failed_count`/`total_count`) for
  `phase`/`amplitude`/`frequency` (init, final, trajectory) and
  `order_parameter_traj`/`mean_phase_coherence_traj`.
- **Controlled/confounders:**
  - **Identical initial condition.** H1/H3 use the corpus's own stored
    `*_init` arrays; H2 draws one explicit initial condition and feeds it to
    both implementations (§5.1) — neither implementation draws its own
    random state, eliminating "different RNG semantics" as a confound.
  - **Identical parameters.** The same `CaseSpec`/fuzz-spec dict parameterizes
    both implementations' model construction (`build_prin_model` /
    `run_prinet_trajectory`'s `_build_model`).
  - **Single seed authority.** The fuzz sampler draws from a
    `numpy.random.Generator` seeded from the registered `(seed_counter,
    seed_key)` pair (`seed_key=1000000×seed_key_component`... concretely
    `np.random.default_rng(seed_key * 1_000_000_007 + seed_counter)`); it
    does **not** use Hypothesis's internal engine, keeping the campaign's
    single registered `Seed` authority intact (Plan §4 rule 3; campaign plan
    §6.1). `prin.parity.strategies` remains the canonical definition of valid
    fuzz-case space; `tests/test_exp001_driver.py::TestFuzzSampler` checks
    the sampler's bounds and per-model coupling constraints against it.
  - **Shadowing horizon `T* = 20` steps.** Chosen because it equals the
    golden corpus's own validated trajectory length (H1's target), giving a
    non-arbitrary, evidence-grounded cutoff between "must match pointwise"
    and "compared distributionally" for the wider fuzz parameter space
    (`n_steps` up to 50, vs. the corpus's fixed 20).
- **Baselines:** PRINet 3.0.0 (archived source,
  `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main`,
  `prinet==3.0.0`) is the reference implementation throughout; `prin`
  1.0.0-rc1 is the implementation under test.

## 7. Sample plan and statistics

- **H1:** deterministic, exhaustive — all 504 corpus cases (not a sample).
- **H2:** ≥1,000 fuzzed cases, `seed_counter=0` for the confirmatory run
  (single deterministic draw sequence from `seed_key=1`; campaign plan §6.3's
  "replicate = seed_counter" does not apply here since H2 is not a
  seeds-across-arms comparison but one large fuzzed ensemble — this is stated
  explicitly as the sample-plan justification for `n=1` "replicate" of the
  fuzz *procedure*, while `n≥1,000` *cases* are drawn within it).
- **H3:** 14 cases (one per grid cell; exhaustive over the corpus's valid
  `(model, coupling, integrator)` combinations, not a statistical sample).
- **H4:** 72 cases (exhaustive over `kuramoto_sparse_knn_*` corpus cases),
  pending §5.4.
- **Tests:** H1/H2a/H3/H4 use the deterministic per-case pass/fail decision
  rule (campaign plan §9.1: "no significance test is needed, and none may be
  used to rescue a failed case"); reported statistics are pass counts and the
  max relative/absolute error distribution. H2b uses Welch's t-test
  (`prin.y4q1_tools.welch_t_test`) with Cohen's *d*
  (`prin.y4q1_tools.cohens_d`) and a 95% bootstrap CI on the mean paired
  difference (`prin.y4q1_tools.bootstrap_ci`, `n_bootstrap=10_000`,
  `seed=42` — the function's documented default, itself derived from no
  experiment-specific randomness since it operates on already-collected
  values).
- **Effect size:** Cohen's *d*, negligible threshold `|d| < 0.2`.
- **Multiple comparisons:** H2b is a single pooled comparison (all
  beyond-horizon samples pooled across cases into two groups), not a family
  of per-case tests, so Holm–Bonferroni does not apply (campaign plan §9.1
  triggers it only "> 2 comparisons in one hypothesis family").
- **α:** 0.05 (default, no deviation).

## 8. Analysis plan

- **Artefacts:** `benchmarks/results/EXP-001/RUN-*/corpus_*.json`,
  `repeatability_*.json`, `fuzz_*.json` (H1–H3, this session's driver);
  `kernel_path_*.json` (H4, pending §5.4); each with its
  `campaign-metadata.json` sidecar and per-run `manifest.json`.
- **E4 adjudication per hypothesis:**
  - H1: `CONFIRMED` iff all 504 `within_tolerance=True`; otherwise
    `REFUTED` (D1) unless every failing case matches a §4 abort criterion, in
    which case those cases are `ABORTED` (invalid) and H1 is adjudicated on
    the remaining cases — if that remaining set is not the full 504,
    `INCONCLUSIVE` with the abort reasons documented.
  - H2a: `CONFIRMED` iff no within-horizon breach across all fuzzed cases;
    otherwise `REFUTED` (D1) subject to the same abort-criterion carve-out.
  - H2b: computed once per run on the pooled beyond-horizon
    `order_parameter`/`mean_phase_coherence` value pairs; `CONFIRMED` iff
    `|d| < 0.2` and (if significant) the bootstrap CI contains 0; otherwise
    `REFUTED` (D1).
  - H3: `CONFIRMED` iff all 14 `bit_identical=True`; otherwise `REFUTED` (D1).
  - H4: `CONFIRMED` iff all 72 `within_tolerance=True` at the f32 kernel
    tolerance; `INCONCLUSIVE` if `NOT EXECUTED — cuda feature not built`;
    otherwise `REFUTED` (D1).
- **Tables/figures:** a single summary table (hypothesis × verdict × pass
  count × max error) generated deterministically via `prin.reporting`
  from the stored run artefacts (Experimentation Standards §2 E4: "figures/
  tables regenerate deterministically... SHA-256 manifest"); no new
  visualization is required for a pass/fail parity table.
- **Regeneration path:** campaign plan §7.4 — E4 re-derives every table from
  the committed run manifests; the E5 report's artefact index lists each
  input run's `manifest.json` digest and the output `report-manifest.json`
  digest.

## 9. Resource budget

Within the campaign plan §8 cap for EXP-001 (≤8 h H1 CPU wall, ≤2 h H1 GPU
wall, ≤3 h hosted CI, ≤5 MiB tracked storage):

| Item | Estimate |
|---|---|
| H1 (504 corpus cases, CPU) | Minutes (each case is `N≤24`, 20 steps; the 4-case smoke test during E1 development completed in well under 1 s) |
| H2 (1,000 fuzz cases, CPU, both implementations) | Tens of minutes (`N≤64`, up to 50 steps, PRINet 3.0's torch-based integration dominates wall time; an 8-case pilot batch completed in a few seconds) |
| H3 (14 repeatability reruns, CPU) | Seconds |
| H4 (72 kernel-path cases, CUDA, pending §5.4) | Minutes, well under the 2 h GPU cap |
| Tracked storage | Each `cases` array is small (`N≤64`, ≤51 steps); the four artefacts plus manifests are expected well under the 5 MiB cap — no `.npz` sidecar to `DOCS/test_and_benchmark_results/` is anticipated |
| Hosted CI (H2/H3) | Not used — EXP-001's cross-OS regeneration leg (campaign plan §5.2, "○ cross-OS regeneration") is optional/confirmatory, not required for this pre-registration's four confirmatory hypotheses, and is not scheduled by this document |

No budget amendment is anticipated.

## 10. Distinguishing negative from invalid/aborted runs (brief item 4)

- A **negative result** is a hypothesis fully executed and adjudicated
  `REFUTED` per §8's decision rule — reported in full, with every failing
  case's `ComparisonResult`, and flagged as a D1 per campaign plan §10.4
  (this project's C1 tier treats every parity reversal as a correction-cycle
  trigger, not a publishable novelty).
- An **invalid/aborted run** is any execution that trips a §4 abort
  criterion before or during adjudication (NaN/Inf, hazard-envelope
  violation, unreproducible seed, incomplete environment capture — including
  fuzz mode running without PRINet 3.0 importable, or the H4 CUDA-feature
  gap) — it is recorded in `log.md` and its `RUN-` directory but excluded
  from the pass/fail count, never silently dropped, and never counted as
  either a confirmation or a refutation.
- Both are reported with equal rigor in the E5 report (Experimentation
  Standards §1.2); a run that mixes aborted and non-aborted cases (e.g. one
  H4 case tripping an amplitude-clamp abort while the rest execute) reports
  the abort explicitly and adjudicates the hypothesis on the non-aborted
  cases only, noting the reduced sample size.

---

## Appendix A — Driver and test evidence at freeze

- **Driver:** `benchmarks/campaign/exp001_driver.py` (H1/H2/H3 implemented;
  H4 pending §5.4).
- **Tests:** `tests/test_exp001_driver.py`, 29/29 passing at E1 freeze
  (`ruff check`/`ruff format --check` clean; `mypy python/prin
  benchmarks/campaign --strict` clean; Snyk Code: 0 issues on both files).
- **Smoke-test evidence cited in §3 as pilot data** (not campaign results):
  4/4 representative corpus cases within tolerance and bit-identical on
  rerun; 7/8 fuzz-sampled pilot cases fully within tolerance, 1/8 breaching
  only past the shadowing horizon by `1.13e-6` on 2/936 `phase_traj`
  elements.

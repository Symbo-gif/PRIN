# Pre-registration — EXP-001: Golden-trajectory numerical parity

**Status:** APPROVED
**Authors:** MichaelMaillet (maintainer); Claude Sonnet 5 (AI pair, drafting E1 and E2)
**Date:** 2026-09-21
**Maintainer approval:** MichaelMaillet, 2026-09-21 — recorded at E2 (session
0155); independent review against Experimentation Standards §2 E2
(falsifiability, statistical adequacy, fair baselines, resource sanity) and
this brief's criteria found no unresolved defect; the one open item (H4
driver support, §5.4) was closed as a pre-execution amendment during this
same E2 session (normal E1→E2 edit window, Experimentation Standards §2 E2;
campaign plan §12 item 1). The E1+E2 branch was then pushed for CI and code
review (PR #20) ahead of E3, per maintainer direction; Devin/CodeRabbit/
Copilot findings from that review were triaged and fixed as a second
pre-execution amendment (§5.5). A fresh CodeRabbit review plus a new Copilot
review were then explicitly requested on the same PR; their findings were
triaged and fixed as a third pre-execution amendment (§5.6), and a further
Copilot review of that commit found two follow-on defects §5.6 had itself
introduced, fixed as a fourth (§5.7) — still within the same E1→E2 edit
window throughout, since no `RUN-` directory exists yet.
**EXP-001 E3 (session 0156) is authorized to begin.**
**Code version:** `prin` 1.0.0-rc1 @ `8ce115f` (campaign baseline SHA; this
document was drafted at E1 on branch `campaign/0154-exp001-e1` and amended at
E2 on branch `campaign/0155-exp001-e2`, both carrying the DV-038/DV-039
hotfix in addition to `8ce115f` — the exact HEAD SHA at freeze is recorded in
`log.md` line 1 per campaign plan §12.4)
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
    steps `0..min(20, n_steps)` inclusive (the shadowing horizon `T* = 20`,
    defined in §6, bounded to the case's own length when `n_steps < 20`)
    satisfies the registered tolerance, for 100% of the ≥1,000 cases.
  - **H2b (beyond-horizon, distributional):** for each of the two metrics
    `order_parameter` and `mean_phase_coherence` **independently** (never
    pooled into one combined sample — they are different physical
    quantities with different ranges, `[0, 1]` vs. `[-1, 1]`, and mixing
    their paired differences into a single mean has no clear interpretation;
    corrected during E2 remediation, §5.5, after a code-review finding
    showed the original pooled-sample wording), computed on the set of
    values at steps `21..n_steps` across every fuzzed case with
    `n_steps > 20`: the PRINet-3.0 and `prin` samples show no practically
    significant difference, adjudicated by one predicate applied identically
    per metric at §4/§8: **a metric is CONFIRMED iff `|Cohen's d| < 0.2`
    (negligible, Cohen's convention; `prin.y4q1_tools.cohens_d`) AND the 95%
    bootstrap CI (`prin.y4q1_tools.bootstrap_ci`, 10,000 resamples, seeded
    per §7) on the mean paired difference contains 0 — otherwise REFUTED for
    that metric. H2b overall is CONFIRMED iff *both* metrics are CONFIRMED;
    REFUTED if either metric is REFUTED.** The two-sided Welch t-test
    (`prin.y4q1_tools.welch_t_test`, `α=0.05`) is still computed and
    reported per metric for transparency, but does not gate either
    predicate: at the fuzz batch's scale a trivially small,
    practically-negligible difference can still test "significant", which is
    why the effect size and CI — not the raw p-value — decide each metric's
    verdict (standard equivalence-testing practice).
- **H3 (bit-level seeded repeatability):** For one representative corpus case
  per each of the 14 `(model, coupling, integrator)` grid cells, running the
  `prin` reproduction twice from the identical stored initial state produces
  byte-identical output (identical dtype, shape, and raw bytes — stricter
  than `numpy.array_equal`, which compares element values only and does not
  check `dtype`) for every array, for 14/14 cases.
- **H4 (GPU kernel-path tolerance-identity):** The Kuramoto sparse-k-NN GPU
  derivative kernel (`prin._prin_core.GpuSparseKuramoto`, WP-036D) reproduces
  the CPU `prin` reference for every `kuramoto_sparse_knn_*` corpus case (72
  cases) within `rtol=1e-5, atol=1e-6` (f32; Testing Standards §3), for 100%
  of those cases.

H1–H4 are all addressed by the committed driver
(`benchmarks/campaign/exp001_driver.py`, tested in tandem —
`tests/test_exp001_driver.py`, 57/57 passing at freeze, including the 3
`slow`/PRINet-gated H2 tests). H4's driver support
(`compare_kernel_path_case`/`compare_kernel_path_subset`, `--mode
kernel-path`) was closed as a pre-execution amendment at E2 (session 0155);
§5.4 records the closure, and three further E2 remediation passes (§5.5,
§5.6, §5.7) fixed a total of eleven code-review findings across three review
rounds — an H2a/H2b data-sufficiency gap, unenforced abort criteria,
artefact-write races and the sidecar/result transaction, H4's CUDA/wgpu
ambiguity (closed properly only at §5.6, after §5.5's first attempt proved
insufficient), H2b's cross-metric pooling, the clamp-trip criterion's scope,
the H4 test guards, and two follow-on defects §5.6 itself introduced.

## 3. Expected results

| Hypothesis | Predicted direction | Predicted magnitude | Basis for prediction |
|---|---|---|---|
| H1 | Confirmed | 504/504 (100%) pass | Phase 1–3 exit criteria required the CI-gated parity suite green on this same corpus; a 4-case representative smoke test run during E1 driver development (`kuramoto_mean_field_euler`, `kuramoto_full_rk4`, `hopf_sparse_knn_rk4`, `stuart_landau_full_euler`, all `n=8, s=20`) passed 4/4 at the registered tolerance. |
| H2a | Confirmed | 100% within-horizon pass | Same basis as H1: the horizon `T*=20` is chosen to equal the corpus's own validated trajectory length. |
| H2b | Confirmed | `\|Cohen's d\| < 0.05` (well under the `0.2` registered threshold) | An 8-case pilot batch drawn by the fuzz sampler during E1 driver development (`seed_counter=0, seed_key=1`) showed 7/8 cases fully within tolerance at all steps; the one exception (`hopf, mean_field, rk4, N=26, n_steps=35`) breached the trajectory tolerance by a small margin (`max_abs_diff=1.13e-6` vs the `1e-8`-anchored `1e-6` relative bound, 2/936 array elements) only in the `phase_traj` array — consistent with float64 rounding-order divergence between two independently-implemented integrators accumulating past step 20, not a systematic bias. This pilot evidence is **not** a campaign result (Experimentation Standards §1.1: no post-hoc hypotheses from peeking at results); it is cited only as the basis for choosing `T*=20` and predicting a near-zero effect size beyond it, exactly as the pre-registration template invites ("PRINet 3.0 Table N / theory / **pilot**"). |
| H3 | Confirmed | 14/14 bit-identical | `prin`'s dynamics core is a pure function of its explicit inputs once an initial state is given (no internal RNG re-draw); a 4-case repeatability smoke test during driver development passed 4/4 bit-identical. |
| H4 | Confirmed | 72/72 pass | Testing Standards §3 already documents this tolerance as the established GPU-vs-CPU bound for existing kernel-equivalence tests (`crates/prin-kernels/src/equivalence.rs`); the E2 driver-closure run (§5.4) already exercised all 72 `kuramoto_sparse_knn_*` corpus cases through the committed driver and observed 72/72 within tolerance (worst case `max_abs_diff≈8.98e-7` against the `atol=1e-6` bound) — cited here as pilot/closure evidence per the same "not a campaign result" discipline as H2b's pilot batch, since this exact driver invocation is not the registered E3 run. |

## 4. Failure conditions

**Falsification (per hypothesis):**

| Hypothesis | Outcome that refutes it |
|---|---|
| H1 | Any of the 504 cases has `within_tolerance=False` for any array, and the breach is not attributable to a registered abort criterion (§4 below) |
| H2a | Any within-horizon (`step ≤ min(20, n_steps)`) array value breaches the registered tolerance in any fuzzed case |
| H2b | For either metric (`order_parameter` or `mean_phase_coherence`, evaluated independently — §2): `\|Cohen's d\| ≥ 0.2`, or the 95% bootstrap CI on the mean paired difference excludes 0 (the same per-metric predicate as §2/§8 — a metric is REFUTED whenever it is not CONFIRMED; H2b overall is REFUTED if either metric is) |
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

1. **Enforced by this experiment's driver**
   (`benchmarks/campaign/exp001_driver.py::_case_arrays_hazard_violation`,
   mechanically checked on every produced — and, for fuzz mode, reference —
   array): NaN/Inf in any array; `order_parameter` outside `[0, 1]`
   (`kuramoto_order_parameter` — the complex mean field's magnitude, clamped
   to `1.0`, `crates/prin-metrics/src/order.rs`); `mean_phase_coherence`
   outside `[-1, 1]` (a mean pairwise cosine, clamped to that range — *not*
   `[0, 1]`; corrected during E2 remediation, §5.5, after the driver's own
   implementation of this criterion caught the corpus's real
   `mean_phase_coherence` values going negative, which the pre-registration
   had originally mis-bounded); phase outside its wrapped range. A breach
   marks that case `"aborted": true` with an `"abort_reason"` and the batch
   continues over the remaining cases (§10).
   **Not enforced — registered validity boundary, not silently claimed as
   covered (§5.5, second code-review finding):** Plan §5 rule 6's
   amplitude/derivative *clamp trip* sub-criterion is **not** part of this
   experiment's mechanically-checked abort rule. `prin-dynamics::
   clamp_derivative` exposes no trip signal to Python, so a clamp trip that
   leaves every checked output finite and in-range (a real possibility —
   `clamp_derivative` returns only the bounded value, not whether it was
   bounded) reaches an ordinary `aborted: false` result rather than an
   abort. Closing this would require exposing a new trip signal from
   `prin-dynamics` through the PyO3 boundary — a cross-crate change (new
   Rust API, rebuild, tests, Snyk) materially larger than an E2 amendment,
   so it is deferred rather than attempted here, the same disposition
   pattern this document already uses for DV-001/DV-006 in §5.4/§5.1. Any
   H1/H2/H3/H4 verdict from this experiment carries this residual boundary:
   a clamp-trip-affected case cannot be distinguished from a genuinely clean
   one by this driver.
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
6. For H4 only: the extension lacks the `GpuSparseKuramoto` binding
   (`hasattr` false — no `--features cuda`/`--features wgpu` build), **or**
   the binding is present but the raw derivative-kernel call does not return
   a CUDA device-resident (`kDLCUDA`) result (§5.1/§5.6: a `--features
   wgpu`-only build, no CUDA device at all, or a `--features cuda` build
   whose CubeCL client failed to initialise and fell back to `prin-sim`'s
   host-slice path — neither the binding's presence nor
   `torch.cuda.is_available()` distinguishes these from a true CUDA run, so
   the driver checks the actual DLPack capsule's device directly). H1's
   build carries the binding and was verified to dispatch through real CUDA
   as of the E2 driver closure (§5.4/§5.6), so this abort is not expected to
   trip on H1 at E3, but remains registered for any other host/leg — logged
   as `NOT EXECUTED — cuda feature not built`, verdict `INCONCLUSIVE`, per
   the reporting mechanics of campaign plan §5.4
   (a build-configuration gap, not literally unavailable hardware — the
   same "never silently skipped, never reported negative" discipline
   applies).

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
  (driver support closed at E2, §5.4).
- **Hardware/backend:** H1 CPU (primary, all of H1–H3); H1 CUDA (H4, driver
  support closed at E2 — §5.4). H1 wgpu is a distinct, not-yet-exercised
  leg: `GpuSparseKuramoto` itself compiles under `cfg(any(feature = "cuda",
  feature = "wgpu"))` (`crates/prin-py/src/bindings/mod.rs`) — the *same*
  Python class, not a separate wgpu-specific binding, corrected during E2
  remediation (§5.5) after a code-review finding showed the earlier E1/E2
  text ("no wgpu-equivalent kernel binding was found") was factually wrong.
  The two backends are mutually exclusive at compile time
  (`cubecl-cuda`/`cubecl-wgpu` behind a `SimRuntime` type alias,
  `crates/prin-sim/src/gpu.rs`: cuda wins whenever both features are
  enabled), and there is no compile-time-independent Python query to tell
  them apart. Nor is a live device even conclusive on its own: a
  `--features cuda` build silently falls back to `prin-sim`'s host-slice
  (CPU) path when its CubeCL client fails to initialise
  (`crates/prin-sim/src/gpu.rs`). So the driver calls
  `GpuSparseKuramoto.compute_derivatives` directly and inspects the raw
  DLPack capsule's device — only the true CUDA device-resident path returns
  a zero-copy `kDLCUDA` capsule (WP-036E Q3); wgpu, CPU-SIMD, and the
  host-slice fallback all return a CPU-resident one (§5.6, superseding
  §5.5's weaker `torch.cuda.is_available()` proxy) — before recording a
  `backend: "cuda"` result, and aborts `INCONCLUSIVE` for the same
  build-configuration reason as CUDA-absent (§4 item 6) otherwise, rather
  than risk mislabeling a non-CUDA result as the required CUDA leg. No
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

All four implemented modes are invoked through the single committed driver;
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

# H4 — GPU kernel-path (72 kuramoto_sparse_knn_* corpus cases, default
# --case-id selection; requires a --features cuda build, §5.4)
python -m benchmarks.campaign.exp001_driver \
  --mode kernel-path --corpus-dir parity/corpus \
  --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-kernel-path-cuda \
  --label kernel-path-cuda --session 0156 --operator MichaelMaillet
```

Each invocation writes exactly one result artefact (`<mode>_<label>.json`,
payload `{"cases": [...]}`): H1–H3 cases carry `prin.parity.harness.
ComparisonResult.to_dict()` per array; H4 cases carry an analogous per-array
dict (`array_name`, `within_tolerance`, `max_abs_diff`, `max_rel_diff`,
`failed_count`, `total_count`) computed at `KERNEL_RTOL`/`KERNEL_ATOL`
instead of `prin.parity.harness`'s f64 quantity-derived tolerance (§5.4).
Every artefact is paired with the run's `campaign-metadata.json` sidecar
(`exp_id="EXP-001"`, `run_id`, `session`, `operator`, `artefacts` — tagged
`["H1"]`/`["H2"]`/`["H3"]`/`["H4"]` by mode).
E3 closes each run directory with `tools.reproduce.append_manifest`/
`verify_manifest` per the `benchmarks/results/EXP-001/README.md` rule.

### 5.4 Driver-support gap for H4 — closed at E2 (pre-execution amendment)

During E1 driver development, `prin._prin_core.GpuSparseKuramoto` (the only
confirmed GPU-dispatchable execution path found — WP-036D, reached through
`prin._torch_compat.KuramotoOscillator._compute_derivatives_gpu`, sparse-k-NN
coupling only) was verified **absent** from the then-current `prin`
extension on H1, although H1's CUDA device itself is visible to `torch`
(`torch.cuda.is_available() == True`, `NVIDIA GeForce RTX 4060`):

```
>>> torch.cuda.is_available()
True
>>> hasattr(prin._prin_core, "GpuSparseKuramoto")
False
```

This meant the E1 default build was not compiled with the `cuda` feature
flag (consistent with prior session notes that `maturin` needs `--features
cuda`). Two other model/coupling combinations (`KuramotoOscillator` with
`mean_field`/`full`, and both `HopfOscillator` and `StuartLandauOscillator`
regardless of coupling) have **no** GPU dispatch override in
`prin._torch_compat` at all — their `step`/`integrate` always execute the CPU
`_raw` path even when given a CUDA-resident tensor. H4 is therefore
pre-registered against the one combination that does have a GPU execution
path, not the full corpus. Committing an untested driver function at E1
would have violated "tests in tandem" (Coding Standards §5); this
pre-registration therefore named H4's exact hypothesis and tolerance at E1
(§2, §4) and deferred `compare_kernel_path_case`'s implementation to this E2
review, per campaign plan §12 item 1 ("New or modified drivers are authored
in E1... reviewed and approved in E2, and frozen at E3 start").

**Closure (E2, session 0155):** the extension was rebuilt with
`.venv\Scripts\python.exe -m maturin develop --release -m
crates/prin-py/Cargo.toml --features cuda` on H1 (NVCC 12.5 present;
`cubecl-cuda 0.10.0` compiled clean, `Finished release profile in 2m 49s`),
after which `hasattr(prin._prin_core, "GpuSparseKuramoto")` is `True`.
`compare_kernel_path_case`/`compare_kernel_path_subset` were added to
`benchmarks/campaign/exp001_driver.py` (`--mode kernel-path`): for each
`kuramoto_sparse_knn_*` corpus case, a `prin._torch_compat.KuramotoOscillator`
is built from the case's stored parameters, and one derivative step
(`dphase`, `damplitude`, `dfrequency`) is evaluated through the CPU (f64
Rust) path and the GPU (f32 CubeCL) `_compute_derivatives_gpu` dispatch hook
and compared at `KERNEL_RTOL=1e-5`/`KERNEL_ATOL=1e-6` (the GPU acquisition
path described here was superseded by §5.6, which calls
`GpuSparseKuramoto` directly instead of through this dispatch hook, for a
stronger backend-confirmation guarantee; the CPU path and tolerance are
unchanged). Tests in tandem
(`tests/test_exp001_driver.py::TestKernelPath`, `TestCli::
test_kernel_path_mode_writes_artefact_and_sidecar`) are `skipif`-guarded on
`GpuSparseKuramoto`'s presence, mirroring
`tests/test_wp036d_gpu_dispatch.py`'s existing convention, so the suite still
skips cleanly on a build without the `cuda` feature (GitHub-hosted legs).
`ruff check`/`ruff format --check` and `mypy python/prin
benchmarks/campaign --strict` are clean on both files; Snyk Code reports 0
issues on both. A closure run over all 72 corpus `kuramoto_sparse_knn_*`
cases (not a campaign run — driver-development/closure evidence, same
disclosure discipline as the H1/H2/H3 pilot data in §3) passed 72/72, worst
case `max_abs_diff≈8.98e-7` (`dphase`, case
`kuramoto_sparse_knn_rk4_n24_s20_dt0_005_K1_seed1500030`) against the
`atol=1e-6` bound — consistent with the pre-registered `Confirmed` direction
(§3) and with the existing `crates/prin-kernels/src/equivalence.rs`
measured-worst-case note. H4's abort path (§4 item 6, `NOT EXECUTED — cuda
feature not built` → `INCONCLUSIVE`) remains registered for any host/leg
without a `--features cuda` build (H2–H4 GitHub-hosted legs, and any future
H1 rebuild that omits the feature) — the same disposition pattern the
campaign plan uses for DV-001 (Linux GPU host) and DV-006 (NPU).

### 5.5 Second E2 remediation pass — code-review findings (pre-execution amendment)

PR #20 (the E1+E2 push, campaign plan §12 item 3) drew review from Devin,
CodeRabbit, and GitHub Copilot before E3 started. Per the same "amendments
before execution are normal edits" rule as §5.4, five findings were fixed as
a second pre-execution amendment (still no `RUN-` directory exists; the
pre-registration is not yet frozen):

1. **H2a/H2b data-sufficiency gap (Devin, CodeRabbit).** The original
   `compare_fuzz_case` applied one whole-trajectory pointwise comparison
   (`prin.parity.harness.compare_case`) with no horizon split at all: points
   beyond step 20 were checked with the same strict pointwise tolerance as
   H2a, and the stored artefact retained only aggregate
   `ComparisonResult`s (max error, pass count) — not the raw paired values
   H2b's Welch-t/Cohen's-d/bootstrap-CI test needs. E4 could not have
   computed the registered H2b analysis from an E3 run. Fixed: H2a now
   compares only steps `0..min(T_STAR, n_steps)` inclusive on the
   trajectory-shaped arrays (`T_STAR = 20`, now a named module constant)
   plus the `_init` arrays; `_final` is excluded (redundant within the
   horizon, out of either hypothesis's scope beyond it). A new
   `"beyond_horizon"` field stores the raw paired
   `order_parameter`/`mean_phase_coherence` values at every step past the
   horizon (`None` when `n_steps ≤ T_STAR`) for E4 to pool across cases —
   this driver stores the data, it does not compute H2b's statistic itself
   (E3 executes, E4 analyzes).
2. **Abort criteria were never enforced (Devin, Copilot — 6 call sites).**
   Nothing checked produced arrays for NaN/Inf, `order_parameter`/
   `mean_phase_coherence` range, or phase-wrap range before writing a
   result; a hazard-envelope breach would have silently become an ordinary
   `within_tolerance=False` failure (a *negative result*), not the
   registered ABORT (an *invalid run* — §10's distinction). Fixed:
   `_case_arrays_hazard_violation`/`_finite_violation` check every produced
   array (and, for fuzz mode, the PRINet reference array too — both are
   live-computed, not stored corpus data) before comparison; a breach marks
   that case `"aborted": true` with an `"abort_reason"` and the batch
   continues over the remaining cases, per §10. **Implementing this check
   surfaced a real pre-existing error in this pre-registration itself**
   (not in the driver): `mean_phase_coherence`'s true range is `[-1, 1]`
   (`crates/prin-metrics/src/coherence.rs` — a mean pairwise cosine, clamped
   to that range), not `[0, 1]` as §4 item 1 originally stated; the first
   hazard-check implementation false-positived on real corpus cases whose
   coherence is genuinely negative. §4 item 1 is corrected above.
3. **Two artefact-write races (Devin, Copilot).** `write_campaign_metadata`
   used check-then-write (`path.exists()` then `write_text`) — not atomic,
   so two concurrent invocations could both pass the check and the later one
   silently overwrite the earlier sidecar (the same race class DV-038 had
   already closed for `write_result`, just not applied here). Separately,
   `main()` wrote the result artefact *before* its mandatory metadata
   sidecar, so a sidecar-write failure could strand a result with no
   provenance. Fixed: the stage-then-exclusive-create write DV-038
   established for `write_result` is now a shared primitive
   (`benchmarks._common.result.write_json_exclusive`) used by both writers;
   `main()` writes the sidecar first.
4. **H4 backend mislabeling (Devin, Copilot; §5.1).** Documented above and
   in the corrected §5.1 hardware/backend bullet: `compare_kernel_path_case`
   at this point also required a live `torch.cuda.is_available()` check, not
   just the `GpuSparseKuramoto` binding's presence, since that binding
   compiles under `--features wgpu` alone too. **This check was itself
   superseded by a stronger fix in §5.6** after a second review round showed
   it was necessary but not sufficient.

Evidence: `tests/test_exp001_driver.py`, 55/55 passing (36 prior + 19 new:
`TestHazardEnvelope` ×13, `TestBitIdentical` ×4,
`TestFuzzComparison::test_beyond_horizon_present_only_when_n_steps_exceeds_t_star`,
one H4 backend-mislabeling regression test later superseded, §5.6);
`ruff check`/`ruff format --check` and `mypy python/prin benchmarks/campaign
--strict` clean; Snyk Code 0 issues on `benchmarks/campaign/exp001_driver.py`,
`benchmarks/_common/result.py`, `benchmarks/_common/__init__.py`, and
`tests/test_exp001_driver.py` (the shared-write refactor in item 3 above also
closed 3 LOW path-traversal findings Snyk raised against the new
staging/`os.link` code once it lived directly in the CLI-argument-handling
file; moving it into `benchmarks._common.result` — already scanned clean —
resolved them without weakening the check itself, since `write_result`
already relies on the identical pattern there).

### 5.6 Third E2 remediation pass — second review round (pre-execution amendment)

Per the maintainer's direction, a fresh CodeRabbit review and a new Copilot
review were explicitly requested on PR #20 after §5.5's push. Both landed
findings; all fixed as a third pre-execution amendment (same E1→E2 edit
window — still no `RUN-` directory exists):

1. **H4's CUDA check was necessary but not sufficient (CodeRabbit).**
   `torch.cuda.is_available()` (§5.5 item 4) only confirms a CUDA device
   exists on the host — it says nothing about which backend
   `GpuSparseKuramoto` itself is dispatching through. Two real gaps: (a) a
   `--features wgpu`-only build's binding can pass both `hasattr` and
   `torch.cuda.is_available()` on a CUDA-capable host, since `torch` and
   `prin._prin_core` are compiled independently; (b) **even a
   `--features cuda` build silently falls back to a host-slice (CPU)
   compute path** when its CubeCL client fails to initialise
   (`crates/prin-sim/src/gpu.rs`'s `try_create_client`/host-slice-fallback
   design, confirmed by reading the source — this is documented, intentional
   behavior, not a bug in `prin-sim`). Fixed: `compare_kernel_path_case` now
   calls `prin._prin_core.GpuSparseKuramoto` directly (not through
   `prin._torch_compat`'s `_compute_derivatives_gpu`, whose `_from_gpu`
   always normalizes the result to the input tensor's device, hiding the
   distinction) and inspects the **raw** DLPack capsule's `.device.type`
   before any placement change: only the true CUDA device-resident path
   returns a zero-copy `kDLCUDA` capsule (WP-036E Q3); wgpu, CPU-SIMD, and
   the host-slice fallback all return a CPU-resident one. A non-`"cuda"`
   result now aborts. Verified empirically on H1: a real call's raw capsule
   reports `device='cuda:0'`.
2. **Reserve the result path before publishing metadata (CodeRabbit).** The
   §5.5 fix (write metadata before the result) closed the "unprovenanced
   result" failure mode but opened a different one: if `result_name` already
   existed (a stale result from an earlier invocation reusing the same
   `--out`/`--label`) while its metadata did not, `write_campaign_metadata`
   would succeed — writing a *fresh* sidecar — before `write_result` failed
   with `ArtefactExistsError`, leaving that fresh sidecar claiming
   provenance over an unrelated, older result it never produced. Fixed:
   `main()` now checks whether the result path already exists and aborts
   before writing *either* file if so.
3. **H2b pooled two different metrics into one sample (CodeRabbit).**
   `order_parameter` (`[0, 1]`) and `mean_phase_coherence` (`[-1, 1]`) were
   combined into a single pooled sample for one Cohen's-d/bootstrap-CI test,
   so a large mismatch in one metric could be masked by the other passing.
   Fixed (preregistration text only — the driver's `beyond_horizon` field
   already stores the two metrics separately, §5.5 item 1): §2/§4/§8 now
   register two independent per-metric predicates; H2b is CONFIRMED only if
   both metrics are.
4. **Clamp-trip abort criterion neither enforced nor formally scoped out
   (CodeRabbit).** §4 item 1 previously described the clamp-trip
   sub-criterion as a "disclosed limitation" alongside the three
   mechanically-checked ones, without making explicit that it is not part
   of the *enforced* rule. Per the finding's own two options ("expose and
   propagate a trip signal... or remove this criterion... and document the
   resulting validity boundary"), the first (new PyO3 telemetry surface,
   cross-crate rebuild, new tests) is materially larger than an E2
   amendment; fixed by the second: §4 item 1 now explicitly separates
   "enforced by this experiment's driver" from "not enforced — registered
   validity boundary," naming the residual risk plainly rather than
   describing it ambiguously as merely "disclosed."
5. **H4 test guards did not track the CUDA requirement (Copilot).**
   `TestKernelPath`'s execution tests (and the matching `TestCli` case) were
   `skipif`-guarded only on `GpuSparseKuramoto`'s presence; once
   `compare_kernel_path_case` also required real CUDA execution (item 1
   above), those tests would run-and-fail rather than skip cleanly on a
   hypothetical `--features wgpu`-only build. Fixed: a new
   `_needs_gpu_execution` guard (binding presence **and**
   `torch.cuda.is_available()`) on the four tests that actually execute
   `compare_kernel_path_case` expecting success; the two tests that exercise
   its error paths directly (`test_missing_binding_raises`,
   `test_non_cuda_resident_result_raises`) keep the weaker
   `_needs_gpu_binding` guard, since they do not need real GPU execution to
   succeed. Verified by simulating a `torch.cuda.is_available() = False`
   host: the four execution tests now skip cleanly instead of failing.

Evidence: `tests/test_exp001_driver.py`, 56/56 passing (55 prior + 1 new:
`TestCli::test_preexisting_result_aborts_before_writing_metadata`; one
existing H4 test renamed/rewritten in place —
`test_binding_present_but_cuda_unavailable_raises` →
`test_non_cuda_resident_result_raises` — to match the item 1 fix, not a net
addition); `ruff check`/`ruff format --check` and `mypy python/prin
benchmarks/campaign --strict` clean; Snyk Code 0 issues on
`benchmarks/campaign/exp001_driver.py` and `tests/test_exp001_driver.py`.

### 5.7 Fourth E2 remediation pass — third review round (pre-execution amendment)

A further Copilot review of §5.6's commit found two follow-on defects that
§5.6's own fixes had introduced. Both fixed as a fourth pre-execution
amendment (still no `RUN-` directory; CI green on all 29 checks throughout):

1. **The "reservation" was only a TOCTOU check (Copilot).** §5.6 item 2
   fast-fails on a pre-existing result via `Path.exists()`, which the
   surrounding comment described as *reserving* the path. It does not: a
   concurrent writer can still take the result path between that check and
   `write_result`, in which case this invocation would publish its sidecar
   and only then fail — exactly the misattributed-provenance outcome §5.6
   set out to prevent, just through a narrower window. Fixed by making the
   pair genuinely transactional rather than by widening the check: the
   sidecar is still published first (campaign plan §7.2 accepts a result
   only with its provenance), but any failure of the subsequent
   `write_result` now **rolls the sidecar back**. That rollback can only
   ever remove this invocation's own sidecar, since
   `write_campaign_metadata` publishes by exclusive-create and raises if one
   already exists — so reaching the rollback proves we created it. Either
   both artefacts land or neither does. The `exists()` check is retained as
   a cheap fast-fail and its comment corrected to say so.
2. **Module docstring described the superseded H4 path (Copilot).** The
   driver's own module docstring still said H4's GPU side runs "via
   `prin._torch_compat.KuramotoOscillator`", which §5.6 item 1 had
   deliberately changed to a direct `prin._prin_core.GpuSparseKuramoto`
   call. Beyond being stale, that wording invited a future change to reroute
   the path back through the dispatch hook and silently drop the
   CUDA-residency check. Corrected, with an explicit note that the direct
   call is load-bearing rather than stylistic.

Evidence: `tests/test_exp001_driver.py`, 57/57 passing (56 prior + 1 new:
`TestCli::test_result_write_failure_rolls_back_the_sidecar`, which asserts
both that the sidecar exists when `write_result` is entered and that it is
gone after the failure — a weaker test would pass even if the sidecar were
never written); `ruff check`/`ruff format --check` and `mypy python/prin
benchmarks/campaign --strict` clean; Snyk Code 0 issues on both touched
files; full local quick suite green.

## 6. Variables and controls

- **Independent variables:** oscillator model, coupling mode, integrator,
  `N`, `dt`, `n_steps`, coupling strength, model-specific parameters, initial
  condition, backend (cpu / cuda — driver support for both closed at E2, §5.4).
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
- **H4:** 72 cases (exhaustive over `kuramoto_sparse_knn_*` corpus cases);
  driver support closed at E2, §5.4.
- **Tests:** H1/H2a/H3/H4 use the deterministic per-case pass/fail decision
  rule (campaign plan §9.1: "no significance test is needed, and none may be
  used to rescue a failed case"); reported statistics are pass counts and the
  max relative/absolute error distribution. H2b uses Welch's t-test
  (`prin.y4q1_tools.welch_t_test`) with Cohen's *d*
  (`prin.y4q1_tools.cohens_d`) and a 95% bootstrap CI on the mean paired
  difference (`prin.y4q1_tools.bootstrap_ci`, `n_bootstrap=10_000`,
  `seed=42` — the function's documented default, itself derived from no
  experiment-specific randomness since it operates on already-collected
  values), computed **twice** — once for `order_parameter`, once for
  `mean_phase_coherence` — never pooled into one combined sample (§2, §5.5).
- **Effect size:** Cohen's *d*, negligible threshold `|d| < 0.2`, computed
  per metric.
- **Multiple comparisons:** H2b's family is the 2 per-metric tests
  (`order_parameter`, `mean_phase_coherence`); each pools all beyond-horizon
  cases into two groups (PRINet-3.0 vs. `prin`) rather than testing
  per-case, so within a metric there is still only one comparison.
  2 comparisons does not exceed campaign plan §9.1's "> 2 comparisons in one
  hypothesis family" Holm–Bonferroni trigger, so it does not apply; both
  metrics use the unadjusted `α = 0.05` bootstrap CI/effect-size predicate.
- **α:** 0.05 (default, no deviation).

## 8. Analysis plan

- **Artefacts:** `benchmarks/results/EXP-001/RUN-*/corpus_*.json`,
  `repeatability_*.json`, `fuzz_*.json`, `kernel-path_*.json` (H1–H4, all
  four produced by `benchmarks/campaign/exp001_driver.py`); each with its
  `campaign-metadata.json` sidecar and per-run `manifest.json`.
- **E4 adjudication per hypothesis.** Every driver record now carries an
  explicit `"aborted"` boolean (§5.5 remediation): a case with
  `aborted=True` is excluded from the pass/fail count entirely (never
  counted as a pass, a failure, or silently dropped — its `abort_reason` is
  reported per §10). Each hypothesis below is adjudicated on its
  non-aborted cases; **any hypothesis whose non-aborted case count is below
  its full registered denominator is `INCONCLUSIVE`, not `CONFIRMED`** — a
  partial abort can only ever produce `INCONCLUSIVE` or `REFUTED`, never
  `CONFIRMED`, closing the gap where dropping a failing case via an abort
  carve-out could otherwise let a sub-full-denominator run pass:
  - H1: full denominator 504. `CONFIRMED` iff all non-aborted cases have
    `within_tolerance=True` **and** the non-aborted count is exactly 504;
    `REFUTED` (D1) if any non-aborted case has `within_tolerance=False`;
    otherwise (some cases aborted, remaining ones all pass) `INCONCLUSIVE`
    with the abort reasons documented.
  - H2a: full denominator ≥1,000 (the registered fuzz batch size).
    `CONFIRMED` iff no within-horizon breach across all non-aborted cases
    **and** the non-aborted count meets the registered batch size; `REFUTED`
    (D1) on any non-aborted breach; otherwise `INCONCLUSIVE`.
  - H2b: computed once per run, **independently for each of
    `order_parameter` and `mean_phase_coherence`** (never pooled into one
    combined sample — §2/§5.5), on the value pairs from non-aborted,
    `n_steps > 20` cases (the `"beyond_horizon"` field). Each metric is
    `CONFIRMED` iff `|d| < 0.2` **and** the bootstrap CI contains 0 (the same
    per-metric predicate as §2/§4 — both conditions required,
    unconditionally, regardless of the Welch test's significance); `REFUTED`
    (D1) for that metric otherwise. H2b overall is `CONFIRMED` iff *both*
    metrics are `CONFIRMED`; `REFUTED` (D1) if either metric is `REFUTED`.
    If no non-aborted case has `n_steps > 20` (no beyond-horizon pool at
    all — e.g. every such case aborted), H2b is `INCONCLUSIVE` for lack of
    data.
  - H3: full denominator 14. `CONFIRMED` iff all non-aborted cases have
    `bit_identical=True` **and** the non-aborted count is exactly 14;
    `REFUTED` (D1) on any non-aborted mismatch; otherwise `INCONCLUSIVE`.
  - H4: full denominator 72. `CONFIRMED` iff all non-aborted cases have
    `within_tolerance=True` at the f32 kernel tolerance **and** the
    non-aborted count is exactly 72; `INCONCLUSIVE` if `NOT EXECUTED — cuda
    feature not built` (§4 item 6) or if any case aborted for another
    reason; `REFUTED` (D1) on any non-aborted breach.
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
| H4 (72 kernel-path cases, CUDA) | Seconds — the E2 closure run (§5.4) over all 72 cases completed in ≈0.37 s wall, well under the 2 h GPU cap |
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
  H4 case tripping a hazard-envelope abort while the rest execute) reports
  the abort explicitly. Per §8's rule, the hypothesis is then `INCONCLUSIVE`
  (never `CONFIRMED`) unless the non-aborted cases still meet the full
  registered denominator — a partial abort narrows what can be concluded,
  it never lets a reduced sample stand in for the registered one.

---

## Appendix A — Driver and test evidence at freeze

- **Driver (E1):** `benchmarks/campaign/exp001_driver.py`, H1/H2/H3
  implemented; `tests/test_exp001_driver.py`, 29/29 passing at E1 freeze
  (`ruff check`/`ruff format --check` clean; `mypy python/prin
  benchmarks/campaign --strict` clean; Snyk Code: 0 issues on both files).
- **Smoke-test evidence cited in §3 as pilot data** (not campaign results):
  4/4 representative corpus cases within tolerance and bit-identical on
  rerun; 7/8 fuzz-sampled pilot cases fully within tolerance, 1/8 breaching
  only past the shadowing horizon by `1.13e-6` on 2/936 `phase_traj`
  elements.
- **Driver (E2 amendment, §5.4):** H4 closed — `compare_kernel_path_case`/
  `compare_kernel_path_subset`/`--mode kernel-path` added to the same driver
  module against a `--features cuda` rebuild of `prin` on H1.
  `tests/test_exp001_driver.py`, 36/36 passing at E2 freeze (29 pre-existing
  + 7 new: `TestKernelPath` ×5, `TestCli::
  test_kernel_path_mode_writes_artefact_and_sidecar`, `TestCli::
  test_repeatability_mode_tags_artefact_h3` — the latter a regression test
  for a pre-existing H1/H3 artefact-tagging bug found and fixed during this
  review, see below); `ruff check`/`ruff format --check` clean; `mypy
  python/prin benchmarks/campaign --strict` clean; Snyk Code: 0 issues on
  both files. Closure run over all 72 `kuramoto_sparse_knn_*` corpus cases:
  72/72 within tolerance, worst case `max_abs_diff≈8.98e-7` vs.
  `atol=1e-6` (cited in §3 as closure/pilot evidence, not a campaign result).
- **E2 review finding, fixed (not a D1 — driver code, pre-execution):** the
  E1 driver's `main()` tagged every non-fuzz run's `campaign-metadata.json`
  `artefacts` entry `["H1"]`, including `--mode repeatability` runs, which
  should have been tagged `["H3"]`. Fixed by replacing the ad hoc ternary
  with an explicit `_MODE_HYPOTHESIS` mapping (`corpus→H1`,
  `repeatability→H3`, `fuzz→H2`, `kernel-path→H4`); regression-tested by
  `TestCli::test_repeatability_mode_tags_artefact_h3`. This was caught during
  E2 review (Experimentation Standards §2 E2: "the maintainer reviews for...
  resource sanity" — construed here to include the artefact-provenance
  metadata the E4/E5 adjudication and campaign audit trail depend on) before
  any H3 run had executed, so no artefact was ever mistagged in practice.
- **Driver (E2 second remediation, §5.5):** PR #20 code review (Devin,
  CodeRabbit, Copilot) found and this session fixed 5 further issues before
  E3: the H2a/H2b data-sufficiency gap, unenforced abort criteria (which
  also surfaced and corrected this document's own `mean_phase_coherence`
  range error), two artefact-write races, and H4's CUDA/wgpu ambiguity.
  `tests/test_exp001_driver.py`, 55/55 passing at freeze (36 prior + 19
  new); `ruff`/`mypy --strict` clean; Snyk Code 0 issues on all four touched
  files (`exp001_driver.py`, `benchmarks/_common/result.py`,
  `benchmarks/_common/__init__.py`, `test_exp001_driver.py`) — see §5.5 for
  the full evidence and finding-by-finding disposition.
- **Driver (E2 third remediation, §5.6):** a maintainer-requested fresh
  CodeRabbit review plus a new Copilot review on PR #20 found and this
  session fixed 5 more issues: H4's CUDA check was real but insufficient (a
  wgpu-only build, or a CUDA build silently falling back to host-slice
  dispatch, could both still pass it — closed with a direct raw-DLPack
  device check instead), a result/metadata provenance-reservation gap
  introduced by §5.5's own fix, H2b's cross-metric pooling, the clamp-trip
  criterion's enforced/not-enforced scope, and the H4 test guards missing
  the strengthened CUDA requirement. `tests/test_exp001_driver.py`, 56/56
  passing at that point; `ruff`/`mypy --strict` clean; Snyk Code 0 issues on
  `exp001_driver.py` and `test_exp001_driver.py` — see §5.6 for the full
  evidence and finding-by-finding disposition.
- **Driver (E2 fourth remediation, §5.7):** a further Copilot review of the
  §5.6 commit found 2 follow-on defects that §5.6's own fixes had
  introduced: its pre-existing-result `exists()` check was described as a
  reservation but is only a TOCTOU check (closed by making the
  sidecar/result pair transactional — the sidecar is rolled back if the
  result write fails, and can only ever roll back this invocation's own
  creation), and the module docstring still described the superseded
  `_torch_compat` H4 path (corrected, with a note that the direct binding
  call is load-bearing because it carries the CUDA-residency check).
  `tests/test_exp001_driver.py`, 57/57 passing at freeze;
  `ruff`/`mypy --strict` clean; Snyk Code 0 issues on both touched files —
  see §5.7 for the full evidence and finding-by-finding disposition.

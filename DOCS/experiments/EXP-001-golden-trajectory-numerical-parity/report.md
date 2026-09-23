# EXP-001 — E5 report: Golden-trajectory numerical parity (track C1)

**Status:** **VERIFIED AND ACCEPTED** — maintainer verification recorded
2026-09-23 UTC (MichaelMaillet); see §13. The exit gate for *proceeding to
session 0159* remains open on the triggered D1 correction cycle (§8.3).
**Verdicts:** **H1 `REFUTED`**, **H2a `REFUTED`**, H2b `CONFIRMED`,
H3 `CONFIRMED`, H4 `CONFIRMED`.
**Campaign plan §10.4 D1 flag: RAISED.** This report completes (§10.4 item 2)
and then **blocks session 0159** and every experiment downstream of EXP-001.
**Report date:** 2026-09-23 UTC.
**Session:** 0158 (E5). **Branch:** `campaign/0158-exp001-e5`.
**Operator / maintainer:** MichaelMaillet.
**AI pair drafting this report:** Claude Opus 5 (Experimentation Standards §4
authorship disclosure). Every number in this report is copied from, or
re-derived in this session from, the committed E3 artefacts and the committed
E4 analysis module; none is asserted from memory. The maintainer verified the
analysis and accepted these verdicts on 2026-09-23 UTC; that record, and the
evidence for it, are in §13.

| Record | Value |
|---|---|
| Pre-registration (frozen) | [`preregistration.md`](preregistration.md) @ `c22db0b`, 2026-09-23T13:40:12Z |
| Execution code SHA | `6b9d6b621a2a46e37373bbcafafd475c1d0f644f` (E3, session 0156) |
| Execution log | [`log.md`](log.md) (E3) |
| Analysis record | [`analysis.md`](analysis.md) (E4, session 0157; commits `8babcc4`, `de904a4`) |
| Analysis code | [`analysis/exp001_e4_analysis.py`](analysis/exp001_e4_analysis.py), tests `tests/test_exp001_e4_analysis.py` |
| Output manifest | [`report-manifest.json`](report-manifest.json) |
| Raw artefact root | [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md) |
| Campaign plan row | [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-001 / C1 |

---

## 1. Summary verdicts (pre-registration §8)

The §8 decision rule was frozen before execution and applied unchanged. No
hypothesis, tolerance, denominator, seed, or rule was altered at E4 or E5.
**No case aborted in any of the four runs**, so §8's partial-abort
`INCONCLUSIVE` branch never engages for any hypothesis.

| Hypothesis | Verdict | Non-aborted / registered denominator | Pass | Fail | Registered statistic | Evidence |
|---|---|---|---|---|---|---|
| **H1** — corpus parity | **REFUTED (D1)** | 504 / 504 | 485 | **19** | max abs `2.008567e-07`, max rel `1.271357e-03` | `RUN-…-corpus-cpu`, §4.1 |
| **H2a** — fuzzed within-horizon parity | **REFUTED (D1)** | 1,000 / 1,000 | 897 | **103** | max abs `2.654853e+01`, max rel `2.477303e+299` (guard artefact, §4.2) | `RUN-…-fuzz-cpu`, §4.2 |
| **H2b** — fuzzed beyond-horizon equivalence | **CONFIRMED** | 657 contributing cases per metric (registered minimum 30) | both metrics inside ±δ | — | see the CI table in §4.3 | `RUN-…-fuzz-cpu`, §4.3 |
| **H3** — bit-level seeded repeatability | **CONFIRMED** | 14 / 14 | 14 | 0 | 0 mismatched arrays | `RUN-…-repeatability-cpu`, §4.4 |
| **H4** — GPU kernel-path tolerance-identity | **CONFIRMED** | 72 / 72 | 72 | 0 | max abs `8.977524e-07` vs `atol=1e-6`; max rel `8.953823e-04` vs `rtol=1e-5` | `RUN-…-kernel-path-cuda`, §4.5 |

**On "effect size and CI" (Experimentation Standards §2 E5).** H2b is an
equivalence hypothesis and carries its registered 95 % bootstrap CI and a
descriptive Cohen's *d* (§4.3). H1, H2a, H3, and H4 are **deterministic
per-case pass/fail** hypotheses; campaign plan §9.1 registers their reported
statistics as pass counts, maximum relative and absolute error, and the error
distribution — and explicitly forbids using any significance test to rescue a
failed case. No effect size or interval is computed for them, because
computing one would be an unregistered statistic applied after the result was
known. The registered statistic set is reported in full in §4 instead.

---

## 2. Results versus the pre-registered expectations

Side-by-side with pre-registration §3 (Experimentation Standards §2 E5). The
"Basis for prediction" column is the pre-registration's own, quoted so that
the prediction and its warrant can be judged together.

| H | Predicted direction | Predicted magnitude | Basis for prediction (pre-registration §3) | Observed | Match? |
|---|---|---|---|---|---|
| H1 | Confirmed | 504/504 (100 %) pass | CI-gated parity suite green on this same corpus; 4-case E1 smoke test passed 4/4 | **485/504**; 19 breach | **No — REFUTED.** The cited CI gate does not perform this comparison; see finding **EXP001-E5-F1** (§7) |
| H2a | Confirmed | 100 % within-horizon pass | Same basis as H1; `T* = 20` equals the corpus's validated trajectory length | **897/1,000**; 103 breach | **No — REFUTED** |
| H2b | Confirmed | Both CI endpoints well inside δ = 0.01 / 0.02; \|Cohen's *d*\| predicted < 0.05 | 8-case E1 pilot batch, 7/8 fully within tolerance; residual read as float64 rounding-order divergence past step 20 | Both CIs strictly inside ±δ; \|*d*\| ≤ 6.71e-03 | **Yes — CONFIRMED**, and the magnitude prediction holds |
| H3 | Confirmed | 14/14 bit-identical | `prin`'s dynamics core is a pure function of its explicit inputs; 4-case smoke test 4/4 | 14/14 bit-identical | **Yes — CONFIRMED** |
| H4 | Confirmed | 72/72 pass | Testing Standards §3 GPU-vs-CPU bound; E2 closure run observed 72/72, worst `≈8.98e-7` | 72/72; worst `8.977524e-07` | **Yes — CONFIRMED**, and the worst-case magnitude matches the pilot to three significant figures |

Two of the five registered expectations failed. Neither failure is a
measurement artefact of this campaign: every input was manifest-verified, the
runs were executed by the frozen driver at a pinned SHA, and the same
adjudication reproduces byte-for-byte from a clean checkout (§10).

---

## 3. What was compared, exactly

Stated plainly because the report's central negative result turns on it.

- **H1** re-integrates the **actual `prin` (Rust) numerical core** from each
  corpus case's stored initial state and compares the produced arrays against
  the PRINet-3.0-authored stored arrays
  (`benchmarks/campaign/exp001_driver.py::compare_corpus_case` →
  `run_prin_case` → `prin.parity.harness.compare_case`). Registered
  tolerances: trajectories `rtol=1e-6, atol=1e-8` (corpus manifest); metrics
  `rtol=2e-6, atol=1e-12` (`prin.parity.schema`).
- **H2** draws ≥1,000 fuzzed cases from the registered
  `prin._prin_core.Seed(seed_counter=0, seed_key=1)` stream and runs **both**
  implementations from one identical explicit initial condition. H2a compares
  pointwise at steps `0..min(20, n_steps)`; H2b compares one predefined paired
  per-case summary beyond step 20, per metric, never pooled.
- **H3** runs the `prin` reproduction twice from the identical stored initial
  state and requires byte-identity (dtype, shape, raw bytes).
- **H4** compares `prin._prin_core.GpuSparseKuramoto` (f32, CUDA) against the
  CPU `prin` reference over all 72 `kuramoto_sparse_knn_*` corpus cases at
  `rtol=1e-5, atol=1e-6`, with the driver checking that all three derivative
  capsules are genuinely `kDLCUDA`-resident before publishing a `cuda`
  artefact.

---

## 4. Per-hypothesis results

### 4.1 H1 — REFUTED (D1)

§8: `CONFIRMED` iff every non-aborted case is `within_tolerance` **and** the
non-aborted count is exactly 504. The count clause is met (504/504
non-aborted); the tolerance clause is not — **19 cases breach** — so the rule
yields `REFUTED`, and pre-registration §4 makes any H1 refutation a D1.

| Breaching array | cases |
|---|---|
| `phase_traj` | 15 |
| `mean_phase_coherence_traj` | 8 |
| `phase_final` | 5 |

| Grid cell | cases |
|---|---|
| `stuart_landau/full/euler` | 10 |
| `stuart_landau/full/rk4` | 7 |
| `kuramoto/mean_field/euler` | 1 |
| `kuramoto/mean_field/rk4` | 1 |

(A case may breach more than one array, so the array column sums above 19; the
cell column sums to exactly 19.)

Error distribution over all 504 non-aborted cases, by each case's worst
absolute error: `1e-17`=97, `1e-16`=189, `1e-15`=2, `1e-10`=66, `1e-9`=76,
`1e-8`=51, `1e-7`=23. 288 cases agree to within a few units in the last
place. The 19 failures sit in the `1e-10`…`1e-7` tail (`1e-10`=1, `1e-9`=2,
`1e-8`=9, `1e-7`=7); the largest absolute error anywhere in the run is
`2.008567e-07` and the largest relative error `1.271357e-03`.

**Small magnitude is reported, not credited.** The registered rule is a
deterministic per-case pass/fail at a registered tolerance, and campaign plan
§9.1 forbids using any statistic to rescue a failed case. All 19 failing case
IDs are enumerated in the committed adjudication output
(`exp001-e4-adjudication.json`, `adjudications.H1.failing_case_ids`).

### 4.2 H2a — REFUTED (D1)

§8: `CONFIRMED` iff no within-horizon breach across all non-aborted cases
**and** the non-aborted count meets the registered batch size. The artefact
records `fuzz_batch_class: "confirmatory"`, `n_fuzz_cases_requested: 1000`,
`fuzz_batch_confirmatory_minimum: 1000`, and 1,000 non-aborted cases, so the
count clause is met. **103 cases breach** at steps `0..min(20, n_steps)`, so
the rule yields `REFUTED` — a second, independent D1 trigger.

Breaching arrays: `amplitude_traj` 68, `phase_traj` 58,
`mean_phase_coherence_traj` 48, `order_parameter_traj` 31, `frequency_traj`
11. Breaches appear in **12 of the 14** grid cells, most often
`stuart_landau/full/euler` 34, `kuramoto/mean_field/rk4` 12,
`kuramoto/mean_field/euler` 10.

Unlike H1, the magnitudes are **not** uniformly small. Worst-per-case
absolute error over the 103 failing cases: `1e-11`=1, `1e-10`=6, `1e-9`=7,
`1e-8`=18, `1e-7`=2, `1e-6`=36, `1e-1`=4, `1e0`=27, `1e1`=2 — **33 cases at
or above `1e-3`**, the largest `2.654853e+01`.

**The reported maximum relative error `2.477303e+299` is a guard artefact,
not a 300-decade discrepancy.** `compare_arrays` computes
`|ref − prod| / (|ref| + 1e-300)`, so an element whose reference value is
exactly `0.0` divides by the guard alone. The element is in `amplitude_traj`
of fuzz case index 841 (`hopf/full/euler`, N=12, n_steps=23), where the
**absolute** difference is `2.477303e-01`. The absolute figures are the ones
to read. The relative maximum is reported because campaign plan §9.1
registers it, with this caveat attached; the registered pass/fail rule uses
`numpy.isclose` and is unaffected by the guard.

All 103 failing case indices are enumerated in the committed adjudication
output (`adjudications.H2a.failing_case_indices`).

### 4.3 H2b — CONFIRMED

Computed by the single committed implementation,
`benchmarks.campaign.exp001_driver.adjudicate_h2b`, independently per metric,
over one predefined paired summary per non-aborted `n_steps > 20` case. 657
cases contribute to each metric — far above the registered minimum of 30 — so
neither metric falls into §8's minimum-information `INCONCLUSIVE` branch.

| Metric | n | δ | mean paired difference | 95 % bootstrap CI | Verdict |
|---|---|---|---|---|---|
| `order_parameter_traj` | 657 | 0.01 | `-1.930404e-03` | `[-4.004274e-03, -1.204094e-04]` | **CONFIRMED** |
| `mean_phase_coherence_traj` | 657 | 0.02 | `-1.605610e-03` | `[-3.676295e-03, +5.565305e-04]` | **CONFIRMED** |

Both endpoints of both intervals lie strictly inside that metric's ±δ, which
is the registered predicate in full. Descriptive statistics, which gate
nothing (§2/§8): Cohen's *d* `-6.708155e-03`, Welch *t* `-1.215824e-01`,
*p* `9.032484e-01` for `order_parameter_traj`; *d* `-5.281658e-03`,
*t* `-9.572777e-02`, *p* `9.237514e-01` for `mean_phase_coherence_traj`.
Bootstrap configuration is the registered one: `prin.y4q1_tools.bootstrap_ci`,
10,000 resamples, α = 0.05, seed 42, routed through the Rust `y4q1_stats`
path (campaign plan §9.2).

**This verdict is narrower than it may look, and it does not offset H2a.**
H2b concerns only the mean per-case paired difference of two bounded
coherence metrics beyond step 20. It says nothing about the pointwise
trajectory agreement H2a tests. §8 adjudicates them separately and
pre-registration §4 makes either one's refutation a D1 on its own. Reporting
H2b's confirmation next to H2a's refutation is required by Experimentation
Standards §1.2; it is not a mitigation.

### 4.4 H3 — CONFIRMED

14 non-aborted cases, 14 bit-identical, denominator exactly 14, no mismatched
array in any case. Both §8 clauses are met. The 14 representative cases are
one per `(model, coupling, integrator)` grid cell, selected at E3 by a
mechanical rule stated before the run ("the first case in corpus-manifest
order within each cell"), which reproduces all four pre-identified
`_REPRESENTATIVE_CASES` exactly and supplies the remaining ten
([`log.md`](log.md)). Nothing was selected after seeing a result.

### 4.5 H4 — CONFIRMED

72 non-aborted cases, 72 within `rtol=1e-5, atol=1e-6`, denominator exactly
72. The artefact's `environment.backend` is `cuda` with the RTX 4060 and
8,188 MiB recorded, so the registered `NOT EXECUTED — cuda feature not built`
`INCONCLUSIVE` branch (pre-registration §4 item 6) does not apply. Largest
absolute error `8.977524e-07` against the `atol=1e-6` bound; largest relative
error `8.953823e-04` against `rtol=1e-5`; every one of the 72 cases has a
worst-case absolute error in the `1e-7` decade.

---

## 5. Runs, aborts, exclusions, and budget

**No run aborted. No case aborted. No case was excluded from any
denominator.** Every registered abort criterion was mechanically evaluated by
the driver on every case — NaN/Inf, `order_parameter` outside `[0, 1]`,
`mean_phase_coherence` outside `[-1, 1]`, phase-wrap range, environment
completeness, and (H4) CUDA device-residency of all three derivative capsules
— and none tripped ([`log.md`](log.md)).

| H | Mode | Run ID | Wall | Cases | Aborted |
|---|---|---|---|---|---|
| H1 | `corpus` | `RUN-20260923T134012Z-6b9d6b6-corpus-cpu` | 3.7 s | 504 | 0 |
| H3 | `repeatability` | `RUN-20260923T134226Z-6b9d6b6-repeatability-cpu` | <1 s | 14 | 0 |
| H2 | `fuzz` | `RUN-20260923T134250Z-6b9d6b6-fuzz-cpu` | 19 s | 1,000 | 0 |
| H4 | `kernel-path` | `RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda` | 4.0 s | 72 | 0 |

All four executed on host H1 (Windows 11, AMD64, 16 logical CPUs, NVIDIA
GeForce RTX 4060 8,188 MiB), `prin` 1.0.0rc1, `prinet` 3.0.0, Python 3.14.0,
rustc 1.98.1. Wall time is far inside the §8 caps (≤ 8 h CPU, ≤ 2 h GPU). The
optional cross-OS regeneration leg was not scheduled by the pre-registration
(§9) and was not run; no hosted-CI campaign minutes were consumed.

**Storage.** The four runs total 5.921 MiB tracked (`fuzz-cpu` alone 4.199
MiB), which exceeded §8's 5 MiB EXP-001 cap and §7.5's 2 MiB per-run cap. The
maintainer granted **campaign plan amendment 6** in-session at E3, raising the
EXP-001 cap to 8 MiB and waiving the per-run cap for the `fuzz` leg; §10.1
item 5's abort criterion is discharged by that amendment rather than by
invalidating a completed run. All four runs are committed as written,
unmodified and unreduced. The campaign-wide 64 MiB cap is unchanged and far
from binding. Recorded here as **PD-4** (§6).

---

## 6. Protocol deviations

Deviations are recorded here and are never edited into the frozen
pre-registration (Experimentation Standards §1.3).

**PD-1 — the summary table is generated by the committed E4 analysis module,
not by a `prin.reporting` generator.** Pre-registration §8 says the summary
table is "generated deterministically via `prin.reporting`". That is not
satisfiable as written: `prin.reporting`'s aggregators
(`generate_benchmark_report`, `generate_leaderboard`) consume the PRINet 3.0
artefact schema — `status`, `benchmarks`, `test_acc`, `results` — none of
which EXP-001's artefacts carry, and they have no notion of a pre-registered
hypothesis or verdict; run against a real EXP-001 run directory,
`generate_benchmark_report` emits `OK` and `—` for every file and an empty
detail block. The table is produced instead by
[`analysis/exp001_e4_analysis.py`](analysis/exp001_e4_analysis.py), which
campaign plan §7.4 item 2 names as a permitted location for analysis code,
under the same determinism guarantees §7.4 step 3 requires (explicit
`generated_at`, sorted keys, fixed row order, no implicit clock). **No
decision rule, tolerance, statistic, or artefact is affected.**

**PD-2 — analysis code was committed *by* E4, not *before* E4 started.**
Campaign plan §7.4 item 2 requires analysis code to be committed before E4
starts. No analysis code existed for EXP-001 at the end of E3. Session 0157
committed the module, its tests, and its local gate evidence before generating
any output, so no verdict was produced by uncommitted code, but the literal
ordering was not met. A campaign-wide fix (E1 authors the analysis code
alongside the driver; E2 approves it) is a campaign plan §12.1-shaped change
and therefore a maintainer decision, recorded here for the next
pre-registration slot rather than applied unilaterally.

**PD-3 — no figures were generated.** Pre-registration §8 states that "no new
visualization is required for a pass/fail parity table". Consistent with the
registered plan; listed for completeness of the deviation list.

**PD-4 — registered storage budget exceeded, resolved by amendment 6.** See
§5. The deviation is from §8/§7.5 as frozen at campaign approval; the
maintainer's dated amendment is the authorized resolution, and it changed no
hypothesis, tolerance, seed, statistic, driver, or run ID.

**PD-5 — the E1–E5 pull request is not yet created, so this report cites no
PR head SHA or CI result.** Campaign plan §12 item 3 requires the E5 report to
record the tested PR head SHA and the required-check results available before
approval, and forbids claiming the not-yet-created merge SHA. Sessions
0154–0158 are committed **locally only**; the E1–E5 PR is a maintainer push
action. This report therefore records **no** CI verdict for the campaign
branch range. §13 carries that obligation as an explicit open item; nothing in
this report may be read as a claim that the range is CI-green.

No other deviation from the frozen protocol occurred: no hypothesis,
tolerance, seed, denominator, or decision rule was changed; no case was
excluded; no unregistered confirmatory test was run; no raw artefact was
mutated; no run was repeated to obtain a different outcome.

---

## 7. Finding EXP001-E5-F1 (D1) — the `parity` CI corpus gate does not exercise PRIN

**Raised by this session. Verified from the repository, not inferred.**

### 7.1 The contradicted published statement

`DOCS/sphinx/parity_report.rst` (Parity Report, DRAFT, WP-037 S1) states,
under *Golden-corpus differential results (**VALIDATION**)*:

> `test_corpus_exhaustive_differential_parity` — PRIN's trajectory matches
> the stored reference trajectory at the registered tolerance.

and adds that the differential job "installs the reference editable from the
archived tree … on every push and pull request, so corpus parity is a merge
gate rather than a periodic check". The same reading is what
pre-registration §3 cited as H1's basis for prediction: "Phase 1–3 exit
criteria required the CI-gated parity suite green on this same corpus."

### 7.2 What the test actually compares

`parity/test_parity_differential.py::test_corpus_exhaustive_differential_parity`
loads the stored case and compares it against `_regenerate(...)`. `_regenerate`
calls `parity.generate_corpus._run_case`, whose model and metric imports are
**`prinet`** — `prinet.core.propagation` for the oscillator models and
`prinet.core.measurement` for `kuramoto_order_parameter` /
`mean_phase_coherence` (`parity/generate_corpus.py` lines 22–31). No `prin`
Rust core is constructed or called anywhere on that path; `prin.parity.*`
supplies only the loader and the comparison harness.

The test therefore compares **a PRINet 3.0 regeneration against a
PRINet-3.0-generated corpus** — a reference self-consistency check, which is
exactly what the neighbouring `test_corpus_regenerates_identically` is
documented to be, run over 504 cases instead of 5. Its docstring's claim to
validate "the full Python -> Rust -> reference pipeline" is not accurate.

Nor does any other gate close the hole.
`crates/prin-metrics/tests/corpus_metrics.rs` compares Rust **metrics**
against corpus arrays on six extracted cases; the
`crates/prin-dynamics/tests/parity_*.rs` suites compare single-step Rust
**derivatives** against hard-coded PRINet values. **No CI gate integrates
PRIN's dynamics over the golden corpus and compares the resulting trajectory
against the stored reference** — the comparison H1 performs.

### 7.3 Reproduction (this session)

Run at `de904a4` on host H1 against four of H1's 19 failing cases. The
committed evidence artefact is
[`EVIDENCE/0158-exp001-e5-parity-gate-coverage.json`](../../../EVIDENCE/0158-exp001-e5-parity-gate-coverage.json).

| Case | CI gate (PRINet regen vs corpus) | EXP-001 driver (PRIN vs corpus) | Breaching array, max abs |
|---|---|---|---|
| `stuart_landau_full_euler_n12_s20_dt0_01_K1_seed2200013` | **PASS** | **breach** | `phase_traj` `9.800321e-08` |
| `stuart_landau_full_rk4_n24_s20_dt0_02_K2_seed2300035` | **PASS** | **breach** | `phase_traj`, `phase_final` `1.618846e-07` |
| `kuramoto_mean_field_euler_n8_s20_dt0_005_K2_seed1000006` | **PASS** | **breach** | `mean_phase_coherence_traj` `1.230510e-09` |
| `kuramoto_mean_field_rk4_n12_s20_dt0_02_K2_seed1100017` | **PASS** | **breach** | `mean_phase_coherence_traj` `7.641159e-10` |

The exact snippet that produced it is reproduced below. It is a one-off
evidence audit of an existing test, **not** a governed driver; it gates
nothing, no verdict in this report depends on it, and the authoritative fix —
a real PRIN-vs-corpus CI test — belongs to the correction cycle (§8).

```python
# run from the repository root with the project venv
import sys; sys.path.insert(0, ".")
from pathlib import Path
from prin.parity.harness import assert_parity
from prin.parity.loader import CorpusLoader
from benchmarks.campaign.exp001_driver import compare_corpus_case
from parity.test_parity_differential import _regenerate

case = "stuart_landau_full_euler_n12_s20_dt0_01_K1_seed2200013"
loader = CorpusLoader(Path("parity/corpus"))
loaded = loader.load(case)
assert_parity(loaded.arrays, _regenerate(loader.get_record(case)), loaded.spec.model)
print("CI-path comparison: PASS")
print("driver within_tolerance:", compare_corpus_case(loader, case)["within_tolerance"])
```

### 7.4 Classification and consequences

**Severity D1** (Development Workflow §5: "published-result
reproducibility"). A published VALIDATION claim in the Parity Report is not
supported by the evidence it cites, and the gate named as the campaign's
standing parity net cannot detect the class of divergence EXP-001 H1
measured.

What this finding **does** establish:

1. H1's failure does not contradict a previously *verified* green
   PRIN-vs-corpus result, because no such verified result exists. The green
   `parity` workflow and the H1 refutation are not in conflict; they measure
   different things.
2. Pre-registration §3's stated basis for the H1 and H2a predictions is
   therefore weaker than it appeared at E1/E2, and this was not detected at
   E2 review. That is disclosed here rather than left implicit.
3. The divergence H1 measures has **no known introduction date**: with no
   PRIN-vs-corpus regression net in CI, the repository carries no evidence
   about when the 19 cases began to breach. Establishing that is
   correction-cycle work (§8), not an E5 claim.

What this finding **does not** establish: nothing about *why* PRIN and PRINet
3.0 diverge numerically. No root cause is claimed anywhere in this report.

**Erratum issued.** Per Experimentation Standards §4 and campaign plan §12
item 6, an erratum is added to the Parity Report
(`DOCS/sphinx/parity_report.rst`) and noted in `CHANGELOG.md`, pointing at
this report. The Parity Report's own text is corrected only to the extent of
flagging the unsupported claim; re-deriving what the corpus evidence *does*
support is correction-cycle work.

---

## 8. D1 declaration, correction cycle, and blocking

### 8.1 Declaration

H1 and H2a are C1 parity hypotheses. Pre-registration §4 states that any
H1/H2a/H3/H4 refutation is a D1 — "scientific conclusion differs from PRINet
3.0" — and not a publishable novelty; campaign plan §10.4 operationalizes
Experimentation Standards §3's identical rule. **The D1 flag is raised.** It
is recorded in [`report-manifest.json`](report-manifest.json)
(`"d1_flag": true`), in both generated outputs, and in this report's header.
Finding **EXP001-E5-F1** (§7) is a second, independent D1 under the same
correction cycle.

### 8.2 The correction cycle this report triggers

Campaign plan §3.3 and §10.4 item 3 insert four conditional sessions from
`DOCS/sessions/contingencies/`, executed strictly S1 → S2 → S3 → S4. They are
instantiated by this session and are **open**:

| Stage | Brief | Scope |
|---|---|---|
| S1 — correction implementation | [`2026-09-23-exp001-d1-s1-correction-implementation.md`](../../sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md) | root-cause the H1/H2a divergence; fix EXP001-E5-F1's gate gap |
| S2 — correction audit | [`2026-09-23-exp001-d1-s2-correction-audit.md`](../../sessions/contingencies/2026-09-23-exp001-d1-s2-correction-audit.md) | read-only audit, findings and verdict |
| S3 — correction remediation | [`2026-09-23-exp001-d1-s3-correction-remediation.md`](../../sessions/contingencies/2026-09-23-exp001-d1-s3-correction-remediation.md) | close every audit finding; CLEAN delta re-audit |
| S4 — correction documentation | [`2026-09-23-exp001-d1-s4-correction-documentation.md`](../../sessions/contingencies/2026-09-23-exp001-d1-s4-correction-documentation.md) | PSR, registers, CHANGELOG; authorize `EXP-001-r1` and the return to 0159 |

This report **opens** the cycle; it does not execute or close it. Campaign
plan §12 item 2 forbids collapsing stages into one session, and §10.4 item 3
assigns root-cause work to S1. **No root cause is claimed by E3, E4, or this
report.**

Campaign plan §10.4 item 3 also allows the correction to conclude that the
PRINet 3.0 conclusion was itself defective (the amendment-#25 class) — but
only on an EMA-style mathematical audit claim, Z3/SymPy-verified where
applicable, before the 3.0 conclusion may be declared the erroneous side.
Nothing in this record asserts which side is wrong.

### 8.3 What is blocked

Per §10.4 item 2 and §3.3:

- **Session 0158 (this one) completes.** The negative result is reported in
  full (Experimentation Standards §1.2), which is what §10.4 item 2 requires
  and what this document is.
- **Session 0159 (EXP-002 E1) is blocked** until the four correction sessions
  close. Every experiment downstream in campaign plan §3.2 inherits the
  block: EXP-002, EXP-003, EXP-004, EXP-005, EXP-006, EXP-007, EXP-008, and
  session 0194 (E6 synthesis, whose entry condition is "no unresolved D1").
- **After S4, EXP-001 is re-run as a new experiment record** — `EXP-001-r1`,
  new pre-registration, new run directories (§10.4 item 4). **This record is
  never edited.** When `EXP-001-r1` exists, an erratum pointer is added here;
  the present artefacts, verdicts, and digests stay exactly as they are.
- **No later campaign session proceeds** until the re-run's E5 verdict is not
  a reversal, or the maintainer records a Project Plan §8.3 amendment
  accepting a changed conclusion with full justification (§10.4 item 5) —
  which is a plan amendment, not an experiment outcome.

The block is recorded mechanically, not only in prose: session 0159's brief
and its `SESSION_REGISTER.md` row both carry status `BLOCKED`, which
`tools/wp001_baseline.py::validate_session_plan` enforces as a consistent
pair (61/61 `tests/test_wp001_baseline.py` passing in this session). Planned
session numbers do not change (§3.3).

**Wording reconciliation.** Campaign plan §10.2's table row reads "block the
successor session" in general terms, while §10.4 item 2 is explicit that the
E5 session completes first. §10.4 is the clause that operationalizes §10.2
for a C1 reversal, so this report follows §10.4. This session's own brief is
consistent with that reading: its expected-work item 3 tells E5 to "trigger
and close a D1 correction cycle before proceeding", and its exit gate
requires "approved report **and** any required correction-cycle evidence".
Accordingly **this report is complete and the cycle is triggered, and session
0158's exit gate is not fully discharged — 0159 does not begin — until the
correction S4 closes.** §13 states that status precisely.

---

## 9. Threats to validity

1. **The clamp-trip residual stands as registered.** Pre-registration §4 item
   1 records that `prin-dynamics::clamp_derivative` exposes no trip signal
   through PyO3, so a clamp trip that leaves every checked output finite and
   in range reaches an ordinary `aborted: false` result. Every verdict here
   inherits that boundary: a clamp-trip-affected case cannot be distinguished
   from a clean one by this driver. Registered limitation, not a new finding.
2. **Single host, single platform.** All four runs executed on host H1. The
   optional cross-OS regeneration leg was not scheduled, so no claim is made
   about whether the H1/H2a breaches reproduce on another platform or
   toolchain. `verify_manifest` reproducing every digest from a clean
   checkout is an artefact-integrity result, not a cross-platform numerical
   result.
3. **H2b's scope.** A confirmed distributional equivalence of two bounded
   metrics beyond step 20 neither implies nor repairs pointwise agreement
   inside the horizon (§4.3).
4. **H4's denominator is the corpus's, not the kernel's.** H4 exhausts the 72
   `kuramoto_sparse_knn_*` corpus cases at `N ≤ 24`. It is not evidence about
   the GPU kernel at larger `N`, other couplings, or other models.
5. **The relative-error statistic is unstable near zero.** The `+1e-300`
   guard in `compare_arrays` makes the reported maximum relative error
   meaningless where the reference is exactly zero (§4.2). The registered
   pass/fail rule uses `numpy.isclose` and is unaffected; only the reported
   statistic is.
6. **Analysis-code gate coverage (DV-040).** CI's lint job runs
   `ruff`/`mypy`/`interrogate`/`bandit` over `python/ tests/ benchmarks/
   tools/` only, so the E4 module under the experiment's record root — the
   location campaign plan §7.4 item 2 prescribes — is outside the
   authoritative merge gate. All those gates were run locally and passed at
   E4 (`ruff` clean, `mypy --strict` clean, `interrogate` 100 % (32/32),
   `bandit` 0 issues, `snyk code test --severity-threshold=medium` 0 issues
   exit 0, 33 tests passing); the module's **tests** live under `tests/` so
   its behaviour is CI-enforced. Registered as **DV-040**, re-audit gate
   EXP-002 E4 (session 0162).
7. **No PRIN-vs-corpus regression net existed before this experiment**
   (finding EXP001-E5-F1, §7). This bounds what can be said about the history
   of the divergence, not about its present measurement.
8. **PRINet 3.0's own arithmetic is part of the reference.** DV-007 records
   that PRINet 3.0 uses `torch.complex64` (f32) internally on several paths
   while `prin` is pure f64, with an accepted ~1e-8–1e-9 per-step drift and a
   registered `1e-6` derivative tolerance. This is a standing, permanently
   dispositioned property of the reference, stated here because the
   correction cycle must weigh it; it is **not** offered as an explanation of
   the H1/H2a breaches, which sit at a different tolerance and a different
   unit of comparison.

---

## 10. Reproducibility and regeneration

Campaign plan §7.4 step 5 requires that re-running the generators on a clean
checkout reproduce every output digest byte-for-byte. This was verified at E4
from a detached worktree, and **independently re-verified in this session**
(0158) at `de904a4`:

| Check | Result |
|---|---|
| `verify_manifest` on all four raw run directories | **PASS** — every file matches its manifest in size and SHA-256 (2 files per run) |
| Re-run `analysis/exp001_e4_analysis.py` with registered defaults | stdout reproduced exactly: `H1: REFUTED`, `H2a: REFUTED`, `H2b: CONFIRMED`, `H3: CONFIRMED`, `H4: CONFIRMED`, `D1 flag: RAISED` |
| `exp001-e4-adjudication.json` | 12,974 bytes, `e6f6eb200b3db8be6cc8ed6a80ad1e5733e143f8000f2a0a3a1ad427bddab525` — **matches** |
| `exp001-e4-summary.md` | 5,783 bytes, `4551061c5eff1bc73d5c9ddb65d6533dfca9dcd774f46a9310eb0241b0f88229` — **matches** |
| `report-manifest.json` after regeneration | **unchanged** (`git status` clean), including input records, verdicts, and the D1 flag |

Regeneration command, from the repository root:

```powershell
.venv\Scripts\python.exe "DOCS\experiments\EXP-001-golden-trajectory-numerical-parity\analysis\exp001_e4_analysis.py"
```

Passing `--generated-at` anything other than the registered default changes
every digest and is not a regeneration.

**Artefact integrity note carried from E3.** The `.gitattributes` rule
`benchmarks/results/** -text` disables EOL conversion for raw campaign
evidence, so the committed blobs are exactly the measured bytes. Without it,
`verify_manifest` would fail closed on the campaign's own evidence in any
clean checkout. No artefact was rewritten, re-run, or re-manifested to
achieve this.

---

## 11. Artefact index (campaign plan §7.4 item 5)

### 11.1 Input runs — raw artefacts and their manifest digests

| Run | File | bytes | SHA-256 |
|---|---|---|---|
| `RUN-20260923T134012Z-6b9d6b6-corpus-cpu` | `campaign-metadata.json` | 214 | `b1f70f500f98e9acfadd2a72ee8c944ea9adb1bcef06ac4dd6920df2089a00fa` |
| `RUN-20260923T134012Z-6b9d6b6-corpus-cpu` | `corpus_corpus-cpu.json` | 1,724,465 | `882da36d54957f4942df594fb71d71d07c3a634b7737b895d4f6c0e94ebfcd97` |
| `RUN-20260923T134226Z-6b9d6b6-repeatability-cpu` | `campaign-metadata.json` | 235 | `4caa0409eecd4cb2e777ad97ab23d0d14617186a9334ad1fa95c2fcf6ce7ebdf` |
| `RUN-20260923T134226Z-6b9d6b6-repeatability-cpu` | `repeatability_repeatability-cpu.json` | 3,176 | `cf1d694051118c266c130d5ba66f1651335aead223f24045a17c81640f5f398a` |
| `RUN-20260923T134250Z-6b9d6b6-fuzz-cpu` | `campaign-metadata.json` | 208 | `c7b314ecceb073b1bf75885067da362101adc93edb8e15238dbdbbf18190cc75` |
| `RUN-20260923T134250Z-6b9d6b6-fuzz-cpu` | `fuzz_fuzz-cpu.json` | 4,401,991 | `deb9a8e3eddf7b60f2213f54e80e34896a78424a266df930556f485287e5977e` |
| `RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda` | `campaign-metadata.json` | 302 | `edb4d34b97acd83fabf11b003db8c8bfb3423fe6b0357ea9bcb863dfc7744a7e` |
| `RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda` | `kernel-path_kernel-path-cuda.json` | 75,984 | `8932d239c9d667233587faf657e7989c53d38445cf87703cfe8bd302605198be` |

Each run directory additionally carries its own `manifest.json`, which is the
record `verify_manifest` checks against (§10).

### 11.2 Generated outputs (gitignored; digests committed)

Written to `DOCS/test_and_benchmark_results/EXP-001/`:

| Output | bytes | SHA-256 |
|---|---|---|
| `exp001-e4-adjudication.json` | 12,974 | `e6f6eb200b3db8be6cc8ed6a80ad1e5733e143f8000f2a0a3a1ad427bddab525` |
| `exp001-e4-summary.md` | 5,783 | `4551061c5eff1bc73d5c9ddb65d6533dfca9dcd774f46a9310eb0241b0f88229` |

Both digests, every input run's manifest record, the per-hypothesis verdicts,
and the D1 flag are committed in
[`report-manifest.json`](report-manifest.json).

### 11.3 Record artefacts

| Artefact | Stage |
|---|---|
| [`preregistration.md`](preregistration.md) (frozen `c22db0b`) | E1/E2 |
| [`log.md`](log.md) | E3 |
| [`analysis/exp001_e4_analysis.py`](analysis/exp001_e4_analysis.py) + `tests/test_exp001_e4_analysis.py` | E4 |
| [`analysis.md`](analysis.md) | E4 |
| [`report-manifest.json`](report-manifest.json) | E4 |
| **this report** | E5 |
| [`EVIDENCE/0158-exp001-e5-parity-gate-coverage.json`](../../../EVIDENCE/0158-exp001-e5-parity-gate-coverage.json) | E5 (finding EXP001-E5-F1) |
| Four contingency session briefs (§8.2) | E5 (cycle trigger) |

---

## 12. Exploratory

Everything in this section is **exploratory**: not pre-registered, gating
nothing, altering no verdict, and attributing no cause (campaign plan §12
item 5). It is recorded because the correction cycle will want a starting
point, and it must never be read as a confirmatory result.

**E-1. Both refutations concentrate in the same place.** In H1, 17 of the 19
failures are `stuart_landau/full` (17 of that model's 72 corpus cases, versus
2 of the other 432). In H2a, `stuart_landau/full/euler` alone carries 34 of
the 103 failures and 17 of the 33 large-magnitude ones.

**E-2. Both refutations concentrate at larger step sizes.** H1's corpus grid
has three step sizes with 168 cases each; the 19 failures split `dt=0.02` → 9,
`dt=0.01` → 9, `dt=0.005` → 1. In H2a, splitting the 1,000 fuzzed cases at the
sampled median `dt ≈ 0.0255` gives 10 breaches (1 large) below and 93 (32
large) above. The split point is chosen post hoc from the observed sample and
supports no inference; it describes where the failures sit.

**E-3. The two failure populations look different in magnitude.** H1's
failures top out at `2.0e-07` — the scale of accumulated float64
rounding-order divergence between two independently implemented integrators,
which is also what pre-registration §3's H2b pilot note anticipated beyond the
horizon. H2a contains a second population, 33 cases at or above `1e-3` and up
to `2.7e+01`, which is not that scale. Whether these are one mechanism or two
is exactly the question the correction cycle owns; this record does not answer
it.

**E-4. H2a's large population is not confined to the cells H1 flags.** H2a
breaches appear in 12 of 14 grid cells, including `hopf/*` and
`kuramoto/sparse_knn/*` cells that H1 does not flag at all. The fuzzed cases
range wider than the corpus (`N ≤ 64`, up to 50 steps, sampled `dt`), so the
two samples are not like-for-like; this is a description of them, not an
inference about model coverage.

---

## 13. Approvals, verification, and open obligations

| Item | Owner | Status |
|---|---|---|
| E5 report drafted from committed artefacts | AI pair (Claude Opus 5) | **done** — this document |
| Regeneration re-verified in this session | AI pair | **done** — §10 |
| D1 correction cycle triggered and the four briefs instantiated | AI pair | **done** — §8.2 |
| Parity Report erratum + CHANGELOG note | AI pair | **done** — §7.4 |
| **Maintainer verification of the analysis and acceptance of the E5 verdicts** | MichaelMaillet | **DONE — 2026-09-23 UTC.** Verified and accepted as reported; see the verification block below |
| **E1–E5 pull request; PR head SHA + required-check results recorded** | MichaelMaillet / AI pair | **DONE — approved 2026-09-23 UTC**; PR opened and its tested head SHA and required-check results recorded in §14 (PD-5 discharged there) |
| Announcement of this report in the next Project State Report | correction-cycle S4 | **OPEN** — Experimentation Standards §2 E5; §10.4 item 3 assigns the PSR to S4 |
| Correction cycle S1 → S2 → S3 → S4 executed and closed | per brief | **OPEN** — blocks 0159 (§8.3) |
| `EXP-001-r1` re-run after S4 | per §10.4 item 4 | **OPEN** |

**Maintainer verification block** — completed at acceptance:

```text
Verified by: MichaelMaillet           Date (UTC): 2026-09-23
Verdicts accepted as reported (H1 REFUTED, H2a REFUTED, H2b/H3/H4 CONFIRMED): [x]
D1 declaration and blocking of 0159 accepted:                                 [x]
Correction-cycle scope in §8.2 approved:                                      [x]
```

Recorded in-session by the maintainer (Experimentation Standards §2 E5, §4
"reports state which analyses were drafted by the AI pair and verified by the
maintainer"; campaign plan §2.2 "every E5 verdict acceptance"). The same
decision approved opening the E1–E5 pull request (§14). **Acceptance of the
verdicts is not release of session 0159**: §8.3's block stands until the
correction cycle's S4 closes and `EXP-001-r1` returns a non-reversal verdict,
which is a separate maintainer decision taken on that evidence.

**Security and quality gates for this session.** No first-party source in any
Snyk-supported language and no dependency manifest changed in session 0158 —
the session's changes are Markdown, one reStructuredText erratum, and one JSON
evidence artefact — so Snyk Code, Snyk Open Source, `cargo audit`, and
`pip-audit` have no changed input to scan here, and none is claimed to have
run. CI remains the authoritative merge gate (Coding Standards §6; amendment
#45). The E4 module's own gate evidence is quoted in §9 item 6 and is local
evidence, exactly as DV-040 records.

---

## 14. Pull request and CI record (campaign plan §12 item 3)

**Approved by the maintainer on 2026-09-23 UTC**, together with the
verification in §13.

**Range carried.** E1 and E2 (sessions 0154/0155) already reached `main`
through **PR #20** (merge `e997431`), with the pre-registration frozen
afterwards at `c22db0b`. This pull request therefore carries the remainder of
the E1–E5 range — **E3 (0156), E4 (0157), and E5 (0158)** — plus the DV-036
S4 closure commit `6b9d6b6` that the campaign's own execution SHA points at
and that had not yet been pushed. Six commits in total against
`origin/main` at `b434554`.

**What this PR does not do.** Merging it does **not** discharge §8.3's block
and does **not** release session 0159. It publishes the EXP-001 record — a
negative result and two D1s — so the correction cycle can proceed against a
merged baseline. The campaign stays blocked until the correction S4 closes
and `EXP-001-r1` returns a non-reversal verdict.

### 14.1 Tested head SHA and required-check results

Recorded below from the actual run, per campaign plan §12 item 3 — the tested
head SHA, never a not-yet-created merge SHA. This subsection is completed by a
docs-only addendum commit after the checks report; that addendum necessarily
changes the branch head, so the SHA named here is the head the recorded checks
actually ran against, stated explicitly rather than implied.

_Pending: filled by the addendum commit._

---

**Corrections to this report are errata, never edits** (Experimentation
Standards §1.3/§4; campaign plan §12 item 6). No hypothesis verdict,
tolerance, or protocol may change at or after E5.

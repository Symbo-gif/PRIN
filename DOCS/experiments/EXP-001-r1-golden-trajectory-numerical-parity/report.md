# EXP-001-r1 — E5 report: Golden-trajectory numerical parity, re-run (track C1)

**Status:** **REPORT ISSUED — MAINTAINER VERIFICATION PENDING** (§13). The
campaign plan §10.4 item 5 non-reversal condition is **satisfied** by the
verdicts below; the release of session 0159 and every experiment downstream of
EXP-001, plus 0194, takes effect on the maintainer's verification recorded in
§13, which is this session's exit gate. Until then they remain **BLOCKED**.
**Verdicts:** **H1 `CONFIRMED`**, **H2a `CONFIRMED`**, **H2b `CONFIRMED`**,
**H3 `CONFIRMED`**, **H4 `CONFIRMED`**.
**Campaign plan §10.4 D1 flag: NOT RAISED.** No C1 conclusion reversal was
detected at E4, so no correction cycle is triggered and nothing is blocked by
this report.
**Report date:** 2026-09-29 UTC.
**Session:** `EXP-001-r1-E5`, declared by MichaelMaillet. **Branch:**
`campaign/exp001-r1-e5`, off `campaign/exp001-r1-e4` @ `46fea62`.
**Operator / maintainer:** MichaelMaillet.
**AI pair drafting this report:** Qwen Code (Experimentation Standards §4
authorship disclosure). It did not draft E1, E2 or E3, and it drafted E4 — so
this report restates E4's numbers from the committed artefacts rather than
independently re-deriving them, and §9 item 9 records that as a threat. Every
number here is copied from, or re-derived in this session from, the committed
E3 artefacts, the committed E4 analysis module and its committed output
manifest; none is asserted from memory.

| Record | Value |
|---|---|
| Pre-registration (frozen) | [`preregistration.md`](preregistration.md) @ `F = 5d5ae3521317af47a11afa8d689935ac2fc0f447`, frozen 2026-09-29T09:17:35Z |
| Execution code SHA `R` | `5d5ae3521317af47a11afa8d689935ac2fc0f447` (E3, all six runs) |
| Green-main baseline `M` | `9b79d2e5b246bead1243074659dc99d049762a40` (PR #26, DV-043) |
| Execution log | [`log.md`](log.md) (E3) |
| Analysis record | [`analysis.md`](analysis.md) (E4; analysis code SHA `3270699`, record commit `46fea62`) |
| Analysis code | [`analysis/exp001_r1_e4_analysis.py`](analysis/exp001_r1_e4_analysis.py), tests [`tests/test_exp001_r1_e4_analysis.py`](../../../tests/test_exp001_r1_e4_analysis.py) (89) |
| Output manifest | [`report-manifest.json`](report-manifest.json) — `906ec394bd0533d17e4c2d2ecf51cb9bf84ac8f6e4374591b2e32ba0dbcd054b` |
| Raw artefact root | [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md) (shared with the predecessor; r1 runs are distinguishable by their own SHA and `-r1-` label) |
| Predecessor record | [`EXP-001/report.md`](../EXP-001-golden-trajectory-numerical-parity/report.md) — H1/H2a `REFUTED`, D1 raised, **immutable and unrevised by this report** |
| Campaign plan row | [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-001 / C1; §10.4 item 4 |
| Errata against this report | [§15](#15-errata) — none at issue |

---

## 1. Summary verdicts (pre-registration §8)

The §8 decision rule was frozen at `F = 5d5ae35…` before the first `RUN-`
directory was created, and applied unchanged at E4. No hypothesis, tolerance,
denominator, seed, decision rule or case population was altered at E4 or E5.
**No case aborted in any of the six runs**, so §8's partial-coverage
`INCONCLUSIVE` branch never engages for any hypothesis, and no exclusion was
made — pre-registered or post hoc.

| Hypothesis | Verdict | Non-aborted / registered denominator | Accepted / passing | Unexplained breaches | Registered statistic | Evidence |
|---|---|---|---|---|---|---|
| **H1** — corpus parity with the registered DV-007 explanation | **CONFIRMED** | 504 / 504 | 504 (485 native-parity + 19 explained-dv007) | **0** | native max abs `2.008567e-07`, max rel `1.271357e-03`; corrected max abs `8.881784e-16` | `RUN-…-r1-corpus-cpu`, §4.1 |
| **H2a** — fuzz parity within the comparison horizon | **CONFIRMED** | 1,000 / 1,000 | **978 pointwise + 22 characterized** | **0** eligible | eligible native max abs `5.050686e+00`, max rel `1.000000e+00` (guard artefact, §9 item 6); eligible corrected max abs `2.775092e-08` | `RUN-…-r1-fuzz-cpu`, §4.2 |
| **H2b** — beyond-horizon ensemble mean coherence equivalence | **CONFIRMED** | 657 contributing cases per metric (registered floor 30) | both metrics' CIs strictly inside ±δ | — | see the CI table in §4.3 | `RUN-…-r1-fuzz-cpu`, §4.3 |
| **H3** — CPU bit-level repeatability | **CONFIRMED** | 14 / 14 in each of two runs | 28 / 28 byte-identical; separate-run projections identical | 0 mismatched arrays | 308 per-array digests compared | both `RUN-…-r1-repeatability-cpu` and `RUN-…-r1-seedrep0-cpu`, §4.4 |
| **H4** — CUDA **and** wgpu derivative-kernel agreement | **CONFIRMED** | 72 / 72 on **each** backend | 144 / 144, zero failed derivative elements | 0 | CUDA max abs `8.977524e-07`, max rel `8.953823e-04`; wgpu max abs `1.345382e-06`, max rel `3.030776e-04` | both `RUN-…-r1-kernel-path-cuda` and `RUN-…-r1-kernel-path-wgpu`, §4.5 |

**On "effect size and CI" (Experimentation Standards §2 E5).** H2b is an
equivalence hypothesis and carries its registered 95 % bootstrap CI plus a
descriptive Cohen's *d* and Welch *t* (§4.3). H1, H2a, H3 and H4 are
**deterministic per-case pass/fail** hypotheses; campaign plan §9.1 registers
their reported statistics as pass counts, maximum relative and absolute error,
and the error distribution, and §7 forbids using any significance test to
rescue a failed case. No effect size or interval is computed for them, because
computing one would be an unregistered statistic applied after the result was
known. The registered statistic set is reported in full in §4 and in
`error-distributions.json`.

**What "CONFIRMED" does not claim for H1 and H2a.** Pre-registration §2 is
explicit: H1's confirmation "is not a claim that every native PRINet array was
reproduced within tolerance", and H2a must be reported as
`978 pointwise + 22 characterized`, **never** as `1,000 pointwise passes`. 19
corpus cases and 48 eligible fuzz cases breach natively and are accepted only
through §5.3's positive float64-reference explanation; 22 fuzz cases are
characterized as ill-conditioned and are **not** pointwise parity successes at
all. §4.1 and §4.2 give the exact partitions.

---

## 2. Results versus the pre-registered expectations

Pre-registration §3's predictions were based on prior governed evidence, not on
r1 results, and §3 states that the native breach count is host-dependent and is
**not** an acceptance target. Nothing below was used to choose a threshold,
input or exclusion.

| Hypothesis | Predicted direction (§3) | Predicted magnitude/range (§3) | Observed | Agreement |
|---|---|---|---|---|
| H1 | Confirmed under the registered rule | 504 accepted; approximately 19 native DV-007 breaches positively explained; zero unexplained breaches | 504/504 accepted — 485 native-parity + **exactly 19** explained-dv007; 0 unexplained; 0 aborted | **as predicted**, including the count |
| H2a | Confirmed with the fixed characterization stratum | 978 accepted pointwise; 22 sensitivity proofs and valid PRIN outputs; zero unexplained eligible breaches | 978/978 eligible accepted (930 native-parity + 48 explained-dv007); 22/22 characterizations valid; 0 unexplained eligible; 0 aborted | **as predicted** |
| H2b | Equivalent ensemble means | Each mean difference near zero, both CI endpoints strictly inside its margin; no directional bias predicted | Both means negative and near zero (−1.36e-04, −2.51e-04); all four endpoints strictly inside ±δ; no boundary touched | **as predicted**; the small negative sign is consistent with the predecessor's H2b direction and is not evidence of bias at this magnitude |
| H3 | Identical | 14/14 byte-identical within each invocation; zero separate-run digest differences | 14/14 in both invocations; zero separate-run digest differences | **as predicted** |
| H4 | Both backends within the same kernel tolerance | CUDA 72/72 and wgpu 72/72, zero failed derivative elements on either | CUDA 72/72 and wgpu 72/72; zero failed derivative elements on either | **as predicted** |

No prediction was contradicted, and none was over-shot in a way that would
suggest the registered denominators or populations were mis-specified: the
observed counts are exactly the registered ones.

---

## 3. What was compared, exactly

| Comparison | Arms | Tolerance | Authority |
|---|---|---|---|
| H1 corpus | PRIN (`legacy.run_prin_trajectory` → `prin.dynamics` → Rust, float64, corrected Euler/RK4 default) against the **stored golden corpus** | trajectories `rtol=1e-6, atol=1e-8`; metrics `rtol=2e-6, atol=1e-12` | pre-registration §1.1; Project Plan §5; amendments #16/#17 |
| H1/H2a DV-007 explanation | PRIN against `parity.prinet_f64.f64_corrected_reference` — the same PRINet 3.0 model with **only** the three adjudicated derivative methods' narrowing casts widened | the **same** array tolerances and horizon; no guard, integrator, coupling, metric or initial-state rule changed | pre-registration §5.3 |
| H2a pointwise | PRIN against a **fresh unmodified PRINet 3.0** trajectory from the identical explicit initial state, over steps `0..min(20, n_steps)` | as H1 | pre-registration §2, §5.3 step 1 |
| H2a characterized stratum | the **reference against itself**: original phases vs `numpy.nextafter(phase_init, +inf)`, amplitudes/frequencies/parameters identical | the same tolerance; the witness must **breach** it | pre-registration §5.4 |
| H2b | `mean(produced[21:] − native_reference[21:])`, one equal-weight paired summary per valid case with `n_steps > 20`, per metric, against the **unmodified** PRINet 3.0 reference | equivalence margins δ = 0.01 (`order_parameter_traj`) and 0.02 (`mean_phase_coherence_traj`) | pre-registration §2, §7 |
| H3 | PRIN against PRIN: two integrations within each invocation, and two separately manifested invocations | byte identity of dtype, shape and raw bytes | pre-registration §2 |
| H4 | three float32 GPU derivative arrays (`dphase`, `damplitude`, `dfrequency`) from raw `GpuSparseKuramoto` against the same float64 Rust CPU reference | `rtol=1e-5, atol=1e-6` | Testing Standards §3; pre-registration §2 |

Elementwise decisions are `numpy.isclose(reference, produced, rtol, atol)`,
whose relative term uses the **second** operand (§1.1). Neither a different
operand order nor a relative-error summary replaces that decision, which is why
§9 item 6 warns against reading the reported relative maxima literally.

H2b always uses the **native** reference, so the corrected reference used to
explain H1/H2a cannot silently change H2b's estimand (§6). `strength_of_incoherence*`
is absent from this experiment's `CaseArrays` and no parity claim is made for
it (§1.1, amendment #25). No timing measurement and no ONNX provider
comparison is part of this protocol.

---

## 4. Per-hypothesis results

### 4.1 H1 — CONFIRMED

§8 rule 3: any valid unexplained breach refutes; otherwise confirm only with
504 valid accepted cases; incomplete valid coverage is inconclusive. All 504
cases are non-aborted and accepted, so the rule yields `CONFIRMED`.

Published separately, as §2 requires:

| Classification | Cases | Meaning |
|---|---|---|
| `native-parity` | **485** | All 11 arrays match the stored corpus within tolerance |
| `explained-dv007` | **19** | Native breach on a §5.3-eligible path, and all 11 comparisons against the float64-widened reference pass at the unchanged tolerances |
| `unexplained-breach` | **0** | — |
| aborted | **0** | — |

The 19 explained cases distribute over `stuart_landau/full/euler` 10,
`stuart_landau/full/rk4` 7, `kuramoto/mean_field/euler` 1,
`kuramoto/mean_field/rk4` 1 — precisely the eligible path families §5.3 step 3
names, and no cell outside them. Eligibility was re-tested at E4 from each
case's own recorded `(model, coupling)`; a model name or a historical case ID
alone was never accepted as an excuse.

Magnitudes. Over all 504 cases the native worst-per-case absolute error
distributes `1e-17`=97, `1e-16`=189, `1e-15`=2, `1e-10`=66, `1e-9`=76,
`1e-8`=51, `1e-7`=23 — 288 of 504 cases agree to within a few units in the
last place. The 19 explained cases are the `1e-9`…`1e-7` part of that tail
(`1e-9`=2, `1e-8`=9, `1e-7`=8; worst-per-case absolute error from
`2.079373e-09` to `2.008567e-07`). Against the float64-widened reference those
same 19 cases collapse to machine precision: max abs **8.881784e-16**, max rel
**1.281938e-13**, distributed `1e-17`=2, `1e-16`=17. That collapse is the
positive evidence §5.3 requires; it is not an assumption inherited from the
correction cycle.

### 4.2 H2a — CONFIRMED

§8 rule 4: any valid eligible unexplained breach refutes; otherwise confirm
only with 978 valid accepted eligible cases **plus** all 22 valid registered
characterizations; a missing or aborted sensitivity witness cannot reduce the
registered denominator and yield confirmation.

**Reported as `978 pointwise + 22 characterized`.**

| Stratum | Cases | Breakdown |
|---|---|---|
| Eligible, accepted pointwise | **978** | 930 `native-parity` + 48 `explained-dv007` |
| Eligible, unexplained breach | **0** | — |
| Characterized (`ill-conditioned-characterization`) | **22** | all 22 carry a reproduced one-ulp reference-sensitivity witness, `pointwise_eligible=false`, `accepted=null` |
| Aborted | **0** | — |

The 22 are exactly the registered zero-based indices 50, 76, 90, 270, 310, 330,
334, 362, 385, 398, 399, 415, 456, 522, 621, 623, 653, 691, 734, 841, 867,
878 — fixed before execution from the correction's committed reference-only
sensitivity evidence, never expanded in response to a PRIN residual (§5.4).
Their characterization is **evidence about the reference's conditioning**, not
a pointwise parity success, and no residual ceiling was invented for this
stratum.

The 48 eligible explained cases distribute over `stuart_landau/full` 20,
`kuramoto/mean_field` 17 and `hopf/mean_field` 11 — again only §5.3-eligible
paths.

Magnitudes, which must be read in pairs. The `fuzz-eligible/native` stratum's
maximum absolute error is **5.050686e+00**; the same cases'
`fuzz-eligible/corrected` maximum is **2.775092e-08**, inside the registered
bound. The large native figure is a *reference-side* divergence on a DV-007
path, not a PRIN defect. For the characterized stratum the native, corrected
and reference-sensitivity maxima are 6.098203e+00, 4.912669e+00 and
5.336729e+00 respectively — the sensitivity witness is *required* to be large,
since it proves the reference itself moves under a one-ulp input change.

Input provenance. The 1,000 draws were replayed at E4 from
`prin._prin_core.Seed(0, 1)` through the driver's own sampler; the whole-stream
digest equals the frozen pin `9804fc09…ff76`, and **every** case's
`input_sha256` and all seven recorded spec fields equal the replayed draw at
that index. No case was excluded, and no exclusion was selected from a PRIN
error.

### 4.3 H2b — CONFIRMED

Adjudicated by `benchmarks.campaign.exp001_r1_driver.adjudicate_h2b` — the
single committed implementation of the registered three-way (TOST-style) rule,
which E2 approved on 2026-09-28 UTC as a prospective change from the
predecessor's binary rule. Each metric is decided independently on one
predefined paired summary per contributing case; the two are never pooled and
serial time points are never treated as independent observations.

`CONFIRMED` iff `-margin < CI_low` **and** `CI_high < margin`; `REFUTED` iff
`CI_low > margin` or `CI_high < -margin`; otherwise `INCONCLUSIVE`, including a
touching or overlapping boundary.

| Metric | n | δ | mean paired diff | 95 % bootstrap CI | Verdict |
|---|---|---|---|---|---|
| `order_parameter_traj` | 657 | 0.01 | −1.363025e-04 | [−5.388353e-04, +3.189321e-04] | **CONFIRMED** |
| `mean_phase_coherence_traj` | 657 | 0.02 | −2.509004e-04 | [−9.586380e-04, +5.733745e-04] | **CONFIRMED** |

All four endpoints lie strictly inside their margin; no interval touches or
overlaps a boundary, so neither metric is `INCONCLUSIVE`. Descriptive
statistics, which gate nothing: Cohen's *d* −4.740832e-04, Welch *t*
−8.592553e-03, *p* 9.931455e-01 for `order_parameter_traj`; *d* −8.241057e-04,
*t* −1.493656e-02, *p* 9.880851e-01 for `mean_phase_coherence_traj`. No
descriptive statistic was undefined, so nothing was silently zeroed.

Bootstrap: `prin.y4q1_tools.bootstrap_ci`, **10,000** resamples, α = **0.05**,
seed **12455822396014146421** = `Seed(0, 1).next_u64()` from a fresh analysis
stream, with the Rust implementation's own domain key `0x626f6f74`. Both
metrics use that same deterministic seed and no new RNG path was introduced
(campaign plan §6.1). This differs from the predecessor's seed 42 by design —
§7 registered the new value prospectively.

Contributors: **657** per metric against a registered floor of 30, and all
1,000 draws accounted for with zero aborts, so §8 rule 5's completeness
condition holds. Per §5.4, 21 of the 22 characterized cases have
`n_steps > 20` and remain eligible contributors; no separate statistical
confirmation of that small subgroup is claimed.

Before the adjudicator ran, E4 recomputed every contributing case's
`reference_mean`, `produced_mean` and `mean_paired_difference` from the stored
paired metric arrays and required **exact** agreement (657 × 2, zero
discrepancies), so the bootstrap ran on values the analysis derived itself.

**Scope.** H2b tests ensemble mean differences of two bounded coherence
metrics beyond step 20. It does not establish equality of the full
distributions, equivalence of every regime, a phase-boundary theorem, or the
absence of canceling case-level differences. The fixed 20-step cutoff is
inherited from the original protocol and corpus length; it is **not** a newly
measured Lyapunov shadowing horizon, and ill-conditioning alone is not proof of
chaos. Margins retain the predecessor's 1 %-of-bounded-range choice: they are
engineering equivalence margins, and a difference below them does not by itself
prove that a scientific classification near a boundary cannot change.

### 4.4 H3 — CONFIRMED

§8 rule 6: both runs' metadata validate independently; all 14 cases in each
must be byte-identical internally; and the two canonical scientific result
projections must agree after removing **only** `environment`, `config.out_dir`
and any per-run `run_id` — no scientific field and no array digest removed.

| Run | Cases | Byte-identical | Mismatched arrays |
|---|---|---|---|
| `RUN-20260929T092626Z-5d5ae35-r1-repeatability-cpu` | 14 / 14 | 14 | none |
| `RUN-20260929T092631Z-5d5ae35-r1-seedrep0-cpu` | 14 / 14 | 14 | none |

Byte identity was **recomputed at E4 from the retained per-array digests**
rather than read from the stored `bit_identical` flag: 28 case-runs × 11 arrays
= **308** digest pairs, all equal, and each case's `mismatched_arrays` list
equals the digest-derived mismatch set. The two separately manifested
invocations' canonical projections are identical, so there are **zero**
separate-run digest differences — including every per-array digest, which the
projection deliberately retains. Both legs carry exactly the 14 registered
representatives (the lexicographically first case ID in each valid
`(model, coupling, integrator)` cell, fixed at E1 from metadata only).

### 4.5 H4 — CONFIRMED

§8 rule 7: validate both complete 72-case inventories and their per-case
backend proofs separately; one valid breach on either backend refutes (D1);
confirmation requires all 72 non-aborted comparisons on **both** backends;
missing or aborted coverage without a valid breach is inconclusive. Never
relabel CUDA as wgpu, never pool the counts.

| Backend | run ID | env backend | dtype | cases | pass | failed elements | max abs | max rel | capsule devices | `backend_name` | extension SHA-256 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CUDA | `RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda` | `cuda` | f32 | 72 | **72** | 0 | 8.977524e-07 | 8.953823e-04 | `cuda` ×3 on all 72 | not recorded (correct — only a wgpu record carries it) | `701bb529965a6916a71a5f5350e286428346e81f541a0c46f6e509b2008753c2` |
| wgpu | `RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu` | `wgpu` | f32 | 72 | **72** | 0 | 1.345382e-06 | 3.030776e-04 | `cpu` ×3 on all 72 (host-exported — the binding's documented behaviour) | `wgpu<wgsl>` on all 72 | `2f902e806a3cab860f3fbdf9b4e7ad7d4928329df63aaf46df4010ed430e748b` |

Both inventories are exactly the 72 `kuramoto_sparse_knn_*` corpus case IDs in
manifest order, with no duplication or substitution. Coverage is 2 distinct run
IDs, 2 distinct manifest-verified environments and 2 distinct E3 build
extension hashes on the one execution SHA `R` — the admissibility condition §8
rule 1 sets for an H4 analysis. The two hashes differ **by design** (two
feature-exclusive builds from one unchanged execution checkout) and were each
verified against their own `log.md` entry, not against each other.

The CUDA leg's worst absolute error sits just inside `atol=1e-6`; the wgpu
leg's sits just *above* it and still passes, because
`numpy.isclose(reference, produced, rtol, atol)` admits
`|diff| <= atol + rtol * |produced|` rather than `atol` alone. Over each case's
worst per-array absolute error the CUDA leg distributes `1e-7`=72 and the wgpu
leg `1e-7`=67, `1e-6`=5 (72 cases each; `error-distributions.json` strata
`kernel-cuda/derivative` and `kernel-wgpu/derivative`).

**Two different decade histograms exist for these legs, and they are not the
same quantity.** The figures just quoted are over each **case's worst** of its
three arrays — 72 values per leg. `summary.json`'s
`h4_backends[*].abs_diff_decade_histogram` is instead over **every retained
comparator record** — 216 values per leg (72 cases × 3 arrays) — and so spreads
across `0`, `1e-11`…`1e-7`. The `0` bucket holds **36** records on each leg,
and all 36 are `dfrequency`: exactly half of that array's 72 records agree with
the CPU reference bit-for-bit, while no `dphase` or `damplitude` record is
exactly zero on either leg. *Why* half of the `dfrequency` records are exactly
zero is not established here and no mechanism is asserted — that would be a
kernel-implementation finding outside this protocol's scope. Both histograms are
legitimate registered statistics under campaign plan §9.1 and both are reported,
but the shared field name does not carry its unit. Nothing in a verdict depends
on either; §9 item 11 records the ambiguity so the next analysis module labels
it.

**What E4 verified, and what it did not.** The driver retained comparator
records, not the raw float32 derivative arrays, and §8 rule 7 forbids claiming
an independent numerical `isclose` re-evaluation from absent raw arrays or
running a new kernel to construct one. No kernel was dispatched at E4 or E5.
What was checked: each case's three `dlpack_devices` keys and values; the wgpu
post-dispatch `backend_name`; each comparator record for internal consistency
against the unchanged tolerance (necessary conditions only —
`within_tolerance == (failed_count == 0)`, a breach implies
`max_abs_diff > atol`, `total_count` equals the case's `n_oscillators`, counts
ordered and non-negative, a zero absolute maximum forces a zero relative
maximum); and each case-level flag against its own three records.
`summary.json` carries `re_evaluated_from_raw_arrays: false` and
`raw_derivative_arrays_retained: false` so no reader can mistake this for a
re-measurement. The **numerical authority for H4 remains E3's live comparison**,
in which the driver rejected any wrong capsule export or non-wgpu
`backend_name` before publishing a result.

---

## 5. Runs, aborts, exclusions, and budget

### 5.1 Run inventory

Six registered runs, all executed from `R = 5d5ae35…` in the order §5.5
registers, all closed with the driver's `check_run_complete` + `append_manifest`
+ `verify_manifest`, all re-verified at E4 and again in this session (§10).

| # | UTC | Mode / label | Cases | Backend | Result |
|---|---|---|---|---|---|
| 1 | 2026-09-29T09:17:35Z | `kernel-path` / `r1-kernel-path-wgpu` | 72 | wgpu (f32) | completed, manifested |
| 2 | 2026-09-29T09:26:19Z | `corpus` / `r1-corpus-cpu` | 504 | cpu (f64) | completed, manifested |
| 3 | 2026-09-29T09:26:26Z | `repeatability` / `r1-repeatability-cpu` | 14 | cpu (f64) | completed, manifested |
| 4 | 2026-09-29T09:26:31Z | `repeatability` / `r1-seedrep0-cpu` | 14 | cpu (f64) | completed, manifested |
| 5 | 2026-09-29T09:26:41Z | `fuzz` / `r1-fuzz-cpu` | 1,000 | cpu (f64) | completed, manifested |
| 6 | 2026-09-29T09:30:35Z | `kernel-path` / `r1-kernel-path-cuda` | 72 | cuda (f32) | completed, manifested |

**Aborts: 0. Retries: 0. Reused directories: 0. Exclusions: 0.** No run or case
was dropped, and nothing was re-run to obtain a different result. The
predecessor's four `RUN-…-6b9d6b6-*` directories are retained untouched; r1
reuses none of EXP-001's run IDs or artefacts (campaign plan §10.4 item 4).

### 5.2 Budget consumption (pre-registration §9; campaign plan §8)

| Budget | Cap | Consumed | Status |
|---|---|---|---|
| New r1 tracked run artefacts (all six, with manifests) | 8 MiB | **7,188,506 B = 6.855 MiB** | within |
| Shared `benchmarks/results/EXP-001/` root (original + r1) | 16 MiB | **13,404,517 B = 12.784 MiB** | within |
| r1 fuzz leg, per-run exception | 6 MiB | **5,017,696 B = 4.785 MiB** | within |
| Every other r1 run, generic per-run cap | 2 MiB each | corpus 1.836 MiB; wgpu 0.085; cuda 0.082; repeatability 0.033 each | within |
| Campaign-wide tracked artefacts | 64 MiB | **13,397,377 B = 12.777 MiB** | within |
| Generated reports / untracked diagnostics | 64 MiB working-space estimate | **10,506,349 B = 10.02 MiB** (four E4 outputs; see erratum E-1) | within |
| CPU wall time | 8 CPU hours (shared with EXP-001) | E3's six invocations span 09:17:35Z–09:30:39Z = **13 m 04 s**, plus two `maturin develop` builds (leg 2 recorded at 3 m 12 s); E4's analysis runs in seconds | far within |
| GPU time | 2 GPU hours | The two kernel-path legs are single-derivative-step comparisons over 72 cases; the CUDA leg occupied 09:30:35Z–09:30:39Z. Minutes at most | far within |
| Hosted-CI hours | 3 hours | **0** charged to r1 — no hosted campaign run was scheduled. The forced `nightly.yml` dispatch `36525353031` that gated DV-043's closure is a hotfix-session cost, disclosed here rather than silently attributed | within |

The driver enforced every storage cap at publication time (`RAW_ROOT_CAP_BYTES`,
`R1_ROOT_CAP_BYTES`, `RUN_CAP_BYTES`, `FUZZ_RUN_CAP_BYTES`,
`CAMPAIGN_CAP_BYTES`), so these are measured outcomes of an enforced limit, not
estimates. No case was reduced and no evidence dropped to fit storage.

---

## 6. Protocol deviations

PD-1 through PD-4 were recorded at E4 ([`analysis.md`](analysis.md)); PD-5 and
PD-6 are this session's. None changes a hypothesis, tolerance, denominator,
seed, decision rule or case population.

**PD-1 — `prin.reporting` cannot render the hypothesis table, so it renders
everything it can.** Pre-registration §8 asks for `summary.md`'s two registered
tables "using deterministic `prin.reporting` rendering". Its aggregators consume
the PRINet 3.0 artefact schema (`status`, `benchmarks`, `test_acc`, `results`)
and have no notion of a pre-registered hypothesis, denominator or verdict, so
they cannot emit a hypothesis × verdict × denominator table. E4 nevertheless
made the generator do real work: `summary.json` carries the `status` and
`benchmarks` fields those aggregators understand, and
`prin.reporting.generate_benchmark_report` is invoked over the three JSON
outputs with the same explicit `generated_at` and no implicit clock; its render
is embedded in `summary.md` as a substantive per-hypothesis section. The two
registered tables themselves come from the committed analysis module under the
same determinism guarantees §7.4 step 3 requires. This is the same gap the
predecessor recorded as its PD-1, now partly closed rather than only disclosed.

**PD-2 — no figures.** §8 registers that "No new figure is needed for this
parity experiment." Consistent with the plan; recorded for completeness.

**PD-3 — the fuzz sidecar carries the campaign's registered `H2` tag, while §2
splits it into H2a and H2b.** Not a defect: campaign plan §7.2's registered tag
set is H1…H4 and the driver stamps `_MODE_HYPOTHESIS["fuzz"] = ["H2"]`.
Recorded because E4's first adjudication attempt **failed closed** on the
mismatch — the run index was wrong about the artefact, not the artefact wrong.
No artefact was edited and no check weakened to make it pass; the index was
corrected and both mappings are now reported side by side
(`sidecar_hypotheses` / `adjudicated_hypotheses`).

**PD-4 — E4 and E5 executed from linked worktrees of the campaign branch, not
from the E3 checkout.** E3 ran in `C:\dev\PRIN-r1-amendment`; the sessions that
followed cannot run `git` there, so E4 committed on
`campaign/exp001-r1-e4` in a linked worktree and E5 continues on
`campaign/exp001-r1-e5` — which is also what campaign plan §12 rule 3's
per-stage branch shape and the predecessor's own history
(`campaign/0154-exp001-e1` … `campaign/0158-exp001-e5`) prescribe. Three
properties keep this equivalent to working from `R`:
`git diff 5d5ae35 HEAD -- python benchmarks/campaign tools parity crates` is
**empty**, so every first-party numerical, driver, corpus and tooling source is
byte-identical to `R`; the imported `_prin_core.pyd` is the **`R`-built
binary**, copied rather than rebuilt, so no `maturin develop` disturbed the
shared venv's `.pth` files or E3's recorded environment; and `PYTHONPATH` pinned
`prin.__file__` to the active checkout, verified by printing both `prin.__file__`
and `prin._prin_core.__file__` before each run. The E3 checkout is deliberately
left at `541fbfe`: it is the environment `log.md` cites, and moving it would
obscure that provenance.

**PD-5 — the E2-baseline-to-E3-main code delta, listed as §10 item 5 requires.**
`149cf2d..M` (`149cf2d` = the EXP-001 D1 correction merge that E1's tree
incorporated; `M = 9b79d2e`) is **23 files, 2,253 insertions, 34 deletions**,
comprising exactly two governed hotfixes and their documentation:

- **DV-041** (PR #25, `5615eda`) — positive wgpu-dispatch identification:
  `backend_name()` on `GpuSparseKuramoto`/`GpuMeanFieldEngine`/`GpuBandStepper`
  plus PyO3 getters (`crates/prin-sim/src/gpu.rs`, `src/engine.rs`,
  `crates/prin-py/src/bindings/gpu.rs`, `python/prin/_prin_core.pyi`), with
  `tests/test_gpu_backend_name.py` and `tests/_env.py` probes. This is the
  capability the approved H4 wgpu leg depends on.
- **DV-043** (PR #26, `9b79d2e`) — the redundant derivative-guard removal on
  the fixed-step path (`crates/prin-dynamics/src/{integrate,state,models,lib}.rs`,
  `crates/prin-kernels/src/sparse_knn/cubecl.rs`).
- Documentation and governance only: two audit reports, `DOCS/audits/README.md`,
  `campaign-plan.md` (§11.7/§11.8, amendments #8/#9), `triage-dv043-handoff.md`,
  the DV register, the session register, `migration_guide.rst`, `CHANGELOG.md`,
  two crate READMEs, `tests/README.md`.

**`R` is the experiment's distinct source SHA, not a second mid-experiment
`main` change.** `M` was incorporated into the campaign branch *before* E3, as
§10 item 5 requires, and all six runs record `R` — not `M` — as
`environment.git_commit` and as their run-ID `<sha>`. `F`, `M` and `R` keep
distinct roles; `F` and `R` coincide at `5d5ae35…` and `log.md` says so
explicitly rather than letting the coincidence imply the roles merged. E3's own
log carries the same disclosure from the execution side.

**PD-6 — §10 item 5's "report fresh results of both 72-case H4 GPU regression
legs" is discharged by reporting the two legs E3 freshly executed, not by
executing new ones at E5.** The clause is read as requiring the report to carry
both r1 GPU legs' results — which are the *fresh* GPU regression evidence,
against the predecessor's single CUDA leg — because E5 is a report stage, the
pre-registration is frozen, and a new leg would need a new run ID under §7.1 and
a pre-execution amendment under §14.2. Creating `RUN-` directories at E5 would
itself be the deviation. §4.5 and §7 report both legs in full. **This reading is
stated explicitly so it can be contradicted by the maintainer at §13 rather than
absorbed silently.**

No other deviation occurred. No case was excluded, no unregistered confirmatory
test was run, no raw artefact was mutated, no tolerance was widened, and the
predecessor EXP-001 record and its `REFUTED` verdicts were not touched.

---

## 7. The two 72-case H4 GPU regression legs (pre-registration §10 item 5)

Reported in full, per PD-6's reading. Both legs ran the **same** 72
`kuramoto_sparse_knn_*` corpus cases from their stored initial states, against
the **same** float64 Rust CPU reference, at the **same** unchanged
`rtol=1e-5, atol=1e-6`, from the **same** execution checkout `R`, in two
feature-exclusive builds with no tracked source change between them.

| Property | wgpu leg | CUDA leg |
|---|---|---|
| Run ID | `RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu` | `RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda` |
| Build | `maturin develop -m crates/prin-py/Cargo.toml --features wgpu` | `maturin develop -m crates/prin-py/Cargo.toml --features cuda` |
| Extension SHA-256 | `2f902e80…430e748b` | `701bb529…2008753c2` |
| Live backend probe before the run | `tests/_env.py::wgpu_kernel_executes()` → `True` (a live wgpu dispatch observed, not merely a compiled module) | `tests/_env.py::cuda_kernel_executes()` → `True` |
| `environment.backend` / `dtype` | `wgpu` / `f32` | `cuda` / `f32` |
| `timing_method` | `not-timed` | `not-timed` |
| Cases / pass / fail / aborted | 72 / **72** / 0 / 0 | 72 / **72** / 0 / 0 |
| Failed derivative elements | **0** | **0** |
| Capsule residency (all three outputs, all cases) | `cpu` — host-exported, the binding's documented wgpu behaviour | `cuda` — `kDLCUDA`, true device residency |
| Post-dispatch `backend_name` | `wgpu<wgsl>` on all 72 | not recorded (a CUDA record must not carry one) |
| max abs / max rel | 1.345382e-06 / 3.030776e-04 | 8.977524e-07 / 8.953823e-04 |
| Host | H1: Windows 11 (10.0.26200), AMD64 Family 25 Model 117, NVIDIA GeForce RTX 4060, 8,188 MiB, 16 logical CPUs | same |

The wgpu leg is the capability DV-041 exists for: before that fix, a silent
host-slice CPU fallback returned a capsule indistinguishable from a real wgpu
dispatch. Here the fallback is excluded twice over — the binding's
`backend_name` getter was read **after each actual kernel dispatch** and
reported the wgpu backend family on all 72 cases, and the live probe asserted a
kernel actually ran before the leg started. A `"cpu-native"` or `"cuda"`
reading, an absent getter, or an unexpected capsule device would have been a
build/backend **abort**, not a passing case; none occurred.

Neither leg is evidence about the GPU kernel at larger `N`, other couplings,
other models, or the mean-field engine — the denominator is the corpus's 72
sparse k-NN cases at `N ≤ 24` (§9 item 5).

---

## 8. Non-reversal determination and the campaign block

Campaign plan §10.4 makes a C1–C3 conclusion reversal — "scientific conclusion
differs from PRINet 3.0" — a D1 that blocks the successor session and inserts a
four-session correction cycle. Item 5 then provides:

> No later campaign session proceeds until step 4's E5 verdict is not a
> reversal (or the maintainer records a Plan §8.3 amendment accepting a changed
> conclusion with full justification …).

**This experiment's E5 verdict is not a reversal.** All five hypotheses are
`CONFIRMED`, the D1 flag is not raised, and the result agrees with the parity
conclusion the campaign registered for track C1. No Project Plan §8.3 amendment
is required, because §8.3's path exists for a *changed* conclusion becoming
publishable and nothing here changed a conclusion.

Consequences:

1. **No correction cycle is triggered.** §10.4 items 2–4 do not engage: there
   is no negative result to report, no successor to block, and no S1–S4 to run.
2. **The block's condition is satisfied.** Session 0159 (EXP-002 E1), every
   experiment downstream of EXP-001 (EXP-002 … EXP-008) and session 0194 were
   blocked solely on this verdict being a non-reversal.
3. **Release takes effect on the §13 verification, not on this sentence.**
   Experimentation Standards §2 E5 and the E5 exit gate require an *approved*
   report; §10.4 item 5 keys the release to "E5's verdict", and the verdict is
   this report's. To keep the two requirements from being conflated, this report
   records the condition as satisfied and the release as **pending the
   maintainer's verification in §13**. The register and the phase-7 index say
   the same, so no downstream session can read a release that has not been
   granted.
4. **The predecessor's record is not revised.** EXP-001's H1 and H2a remain
   `REFUTED` in its own immutable record; r1 is a separate experiment on
   separate runs, per §10.4 item 4. An append-only erratum (**E-4**) is added to
   EXP-001's §15 recording that the condition its own E-3 described has now been
   met — the sanctioned mechanism, not an edit.
5. **The Parity Report's standing caveat is updated by admonition, not edit.**
   `DOCS/sphinx/parity_report.rst` carries a dated-admonition chain; this
   session appends one recording r1's outcome and the exact scope of what the
   corpus evidence now supports, retaining every earlier admonition verbatim.

---

## 9. Threats to validity

1. **The clamp-trip residual stands as registered, and §4.2 requires it be
   repeated here.** An internal clamp-trip signal is not exposed at the Python
   boundary: the driver checks the observable envelope and the new amplitude
   floor, but it does not claim to observe every derivative clamp event. A clamp
   trip that leaves every checked output finite and in range reaches an ordinary
   `aborted: false` record. Every verdict in this report inherits that boundary.
   **This applies with particular force to the 22 characterized cases**, whose
   large native divergences are exactly the regime in which a clamp could trip
   unobserved; their characterization rests on a reference-only witness and
   does not assert that PRIN's internal clamp path was exercised or unexercised.
   Positive float64-reference parity constrains the eligible paths but does not
   replace the missing trip instrumentation.
2. **This is a verification of a correction on a known input population, not an
   independent holdout study** (§1). The original experiment's and the
   correction's results were known when the protocol was drafted, and the same
   seed and inputs are deliberately reused to test the correction. Old outcomes
   were never used as new measurements — but the design cannot detect a defect
   that only appears on inputs outside this population, and the H1/H2a
   confirmations are correspondingly narrower than a fresh discovery study would
   give.
3. **Single host, single platform.** All six runs executed on campaign host H1
   (Windows 11, AMD64 Family 25 Model 117, RTX 4060, 8,188 MiB, Python 3.14.0,
   rustc 1.98.1). §5.1 records the H2/H3/H4 hosted cross-OS legs as optional and
   unscheduled, so no claim is made that these results reproduce on another
   platform or toolchain. `verify_manifest` reproducing every digest from a clean
   checkout is an artefact-integrity result, not a cross-platform numerical one.
   §3 also warns that the native breach count is host-dependent and is not an
   acceptance target — so the *split* 485/19 should be expected to move on
   another host even though the verdict rule would not.
4. **H2b's scope.** See §4.3: equivalence of two bounded metrics' ensemble means
   beyond step 20 neither implies nor repairs pointwise agreement inside the
   horizon, does not establish distributional equality, and cannot locate a
   phase boundary. The margins are engineering choices (1 % of each metric's
   bounded range), not derived indifference thresholds.
5. **H4's denominator is the corpus's, not the kernel's.** 72 sparse k-NN
   Kuramoto cases at `N ≤ 24`, one derivative step each. No claim about larger
   `N`, other couplings, other models, the mean-field engine, multi-step
   integration, or throughput — the legs are `timing_method="not-timed"` and no
   timing measurement is part of this protocol.
6. **The relative-error statistic is unstable near zero.**
   `compare_arrays` computes `|ref − prod| / (|ref| + 1e-300)`, so an element
   whose reference value is exactly `0.0` divides by the guard alone. That is why
   `fuzz-characterized/native` and `/corrected` report a maximum relative error
   of **1.261799e+300** and the sensitivity stratum **2.365011e+299**, while
   their absolute maxima are 6.098203e+00, 4.912669e+00 and 5.336729e+00, and
   why `fuzz-eligible/native` reports max rel exactly `1.000000e+00`. **Read the
   absolute figures.** The registered pass/fail rule uses `numpy.isclose` and is
   unaffected; only the reported statistic is. `error-distributions.json` carries
   this caveat in its own `note` field so it travels with the data.
7. **N=1 mean-field behaviour, RK45, exponential/Jacobian and single-step
   `_torch_compat` guard differences remain outside this population** (§6), as do
   DV-001, DV-003, DV-036 and DV-040. This experiment closes none of those
   dispositions, and its confirmations must not be read as covering them.
8. **Governance gap in the gate coverage of the analysis code (DV-040).** CI's
   lint job runs `ruff`/`mypy`/`interrogate`/`bandit` over `python/ tests/
   benchmarks/ tools/` only, so the record-root analysis module — the location
   campaign plan §7.4 item 2 prescribes — is outside the authoritative merge
   gate. Its gates were run locally (quoted in [`analysis.md`](analysis.md)) and
   its 89 tests live in `tests/`, so at least the behavioural check is
   CI-enforced. DV-040's re-audit gate is EXP-002 E4 (session 0162); this
   experiment is a second instance of the same gap, which is evidence for that
   re-audit, not a closure.
9. **E4 and E5 share one AI pair.** The same system drafted the E4 analysis
   module and this report, so E5's restatement of E4's numbers is not an
   independent re-derivation. The compensating controls are mechanical rather
   than personal: every figure here is copied from committed artefacts or
   recomputed in this session from them (§10 records the regeneration), the
   analysis module re-derives every stored decision from the retained per-array
   records rather than trusting it, the adjudicator for the only statistical
   hypothesis is the separately committed and separately tested driver function,
   and E2's independent review (Claude Sonnet 5, who did not draft E1) covers the
   protocol these verdicts apply. Maintainer verification in §13 is the
   governance step that closes it; a fresh-context independent review of this
   report before approval would close it further and is recommended.
10. **The ill-conditioned stratum is characterized, not passed.** The 22 cases
    are evidence that PRINet 3.0's own float64 map is sensitive to a one-ulp
    input change there. That is a statement about the reference's conditioning.
    It is **not** evidence that PRIN reproduces those trajectories, and ill
    conditioning alone is not proof of chaos.
11. **One output field name does not carry its unit.** `summary.json`'s
    `h4_backends[*].abs_diff_decade_histogram` /
    `rel_diff_decade_histogram` are decade histograms over **all 216 retained
    comparator records** per leg, while `error-distributions.json`'s
    `kernel-*/derivative` strata histograms of the same name are over the **72
    per-case worst** values. Both are correct and both are registered §9.1
    statistics, but a reader who assumes one unit will mis-read the other by a
    factor of three in sample size. §4.5 states both explicitly. No verdict
    depends on either. This is a naming defect in the E4 module rather than a
    numerical one, and it is recorded here so that DV-040's re-audit gate
    (EXP-002 E4, session 0162) — the next session to commit an analysis module
    under the same §7.4 item 2 rule — labels histogram units in field names.

---

## 10. Reproducibility and regeneration

Campaign plan §7.4's five steps, discharged:

1. **Inputs.** The six run directories named in §11 and their `manifest.json`
   files, each verified with `tools.reproduce.verify_manifest` before use — at
   E4, again from a clean detached checkout at `f966921`, and again in **this**
   session's checkout at `46fea62`.
2. **Analysis code.** [`analysis/exp001_r1_e4_analysis.py`](analysis/exp001_r1_e4_analysis.py),
   committed at `f057ef0` **before** any adjudication ran (campaign plan §7.4
   item 2), refined at `f966921` and `3270699`. Tests:
   [`tests/test_exp001_r1_e4_analysis.py`](../../../tests/test_exp001_r1_e4_analysis.py),
   89 passing, inside CI's authoritative gate.
3. **Generators.** `prin.reporting.generate_benchmark_report` for the
   registered-reporting section; the hypothesis and expected-versus-observed
   tables from the committed module (PD-1). Both deterministic: explicit
   `generated_at`, sorted keys, fixed row order, no implicit clock, no
   randomness outside H2b's seeded bootstrap.
4. **Outputs.** `summary.json`, `summary.md`, `case-comparisons.json`,
   `error-distributions.json` under the gitignored
   `DOCS/test_and_benchmark_results/EXP-001-r1/`, with
   [`report-manifest.json`](report-manifest.json) committed to the record root.
5. **Check.** Re-running step 3 on a clean checkout reproduces every output
   digest byte-for-byte.

**Verification performed in this session (2026-09-29 UTC, checkout `46fea62`).**
The generator was run from this E5 checkout — a separate linked worktree, with
`PYTHONPATH` pinned to it and the `R`-built extension — and all four output
digests and sizes were compared programmatically against the **committed**
`report-manifest.json`:

```text
H1: CONFIRMED
H2a: CONFIRMED
H2b: CONFIRMED
H3: CONFIRMED
H4: CONFIRMED
D1 flag: not raised
committed-manifest digests reproduced in the E5 checkout: True
```

`git status` in that checkout reported no change at all, including to
`report-manifest.json` itself. Together with E4's three in-worktree runs and its
clean detached-checkout run at `3270699`, the same five files have now been
reproduced byte-identically **five times across three separate checkouts and six
separate processes**. Passing `--generated-at` anything other than the
registered `2026-09-29T12:00:00Z` changes every digest and is not a
regeneration.

Regeneration command, from the repository root:

```powershell
.venv\Scripts\python.exe "DOCS\experiments\EXP-001-r1-golden-trajectory-numerical-parity\analysis\exp001_r1_e4_analysis.py"
```

---

## 11. Artefact index (campaign plan §7.4 item 5)

### 11.1 Input runs — raw artefacts and their manifest digests

All six under [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md),
each `environment.git_commit = R = 5d5ae3521317af47a11afa8d689935ac2fc0f447`.
Per-file digests for every `campaign-metadata.json` and result artefact are in
[`report-manifest.json`](report-manifest.json) under `inputs[].files`; the
run-manifest digests are repeated here because §7.4 item 5 names them.

| Run ID | Backend | `manifest.json` bytes | `manifest.json` SHA-256 |
|---|---|---|---|
| `RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu` | wgpu | 582 | `cb278646c61381099801cd60f970d89abb94e2f14085b635964f570ae8302884` |
| `RUN-20260929T092619Z-5d5ae35-r1-corpus-cpu` | cpu | 573 | `93514868caa9fed4d7719b29846c7ea485ce1a4b94f47687109c3c3d1e9155a0` |
| `RUN-20260929T092626Z-5d5ae35-r1-repeatability-cpu` | cpu | 585 | `b7f9e1b6ed94d77c742fc186829082b5f030d3822abc0ff032f876d201328ec6` |
| `RUN-20260929T092631Z-5d5ae35-r1-seedrep0-cpu` | cpu | 580 | `91066059c792216da290aa3061473940e601b7e25f7d4bafbae67ac0b5605bfd` |
| `RUN-20260929T092641Z-5d5ae35-r1-fuzz-cpu` | cpu | 569 | `388072ee5efb38e25f360027b380777890d010639377dde3105ab3d397b467c0` |
| `RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda` | cuda | 582 | `73edce4a6560fe50d27a7a426da43353462cba66cedc75d78b7b645e8de9d07b` |

Registered input fingerprints, recomputed at E4 from disk rather than trusted
from the run `config`: corpus manifest
`fcbaad1cb16edb3445c9b9ce122131bf4361d9c4ce17c4bc67edd74c62edd2cf`; fuzz stream
`9804fc09e4a510ef0c34dfa5b58c6639a62baf15cf4f38f481ed1c8b854cff76`; PRINet 3.0
`oscillator_models.py` `89d19734c714e31f355d018d7b5889e48f4787841dc15c43df6abdad9d77d4b9`;
`parity/prinet_f64.py` `c6972d5f1ca1380f0d80249034479ed2974a34d20c27b295ddf90f441c1631c2`.

### 11.2 Generated outputs (gitignored; digests committed)

| Output | bytes | SHA-256 |
|---|---|---|
| `case-comparisons.json` | 5,897,415 | `9962628f71bdb4013e0f92da3507bd2f87d769016785fad3cc3e48d92559d0e9` |
| `error-distributions.json` | 4,558,744 | `c1d2ed994716001ec542f08d1583f849de66f4fbe5892a3806ad884deec50223` |
| `summary.json` | 36,153 | `dd0240dbfae531b5c1d79e5c22dd05bf4e8912659ec10b16c39884e0abc64292` |
| `summary.md` | 14,037 | `38d8d8e35fdbeebb7488a0c738d6febc7cee8228c592488df5516aca564f7ba5` |

**Output manifest digest** (`report-manifest.json`, tracked):
`906ec394bd0533d17e4c2d2ecf51cb9bf84ac8f6e4374591b2e32ba0dbcd054b`, 6,281 bytes.

`case-comparisons.json` retains all **1,676** registered cases
(504 + 978 + 22 + 14 + 14 + 72 + 72) with every native, corrected and
reference-sensitivity comparison record, including every breach and every abort
field. `error-distributions.json` retains **14,921** comparator records across
**9** registered strata, sorted per case and per array, separated by
native / corrected / reference-sensitivity / kernel and by the eligible and
characterized populations.

### 11.3 Record artefacts

| Artefact | Stage |
|---|---|
| [`README.md`](README.md) | E1, updated through E5 |
| [`preregistration.md`](preregistration.md) | E1, frozen at E3's first `RUN-` |
| [`e1-handoff.md`](e1-handoff.md) | E1 |
| [`e2-review.md`](e2-review.md) | E2 (original + follow-up H4 method approval) |
| [`log.md`](log.md) | E3 |
| [`analysis/`](analysis/README.md) | E4 — committed analysis code |
| [`analysis.md`](analysis.md) | E4 |
| [`report-manifest.json`](report-manifest.json) | E4 |
| `report.md` | E5 — this document |

---

## 12. Exploratory

Everything below is **exploratory**: not pre-registered, gating nothing,
altering no verdict, and attributing no cause (campaign plan §12.5). It is
carried forward from [`analysis.md`](analysis.md) §Exploratory because E5 is
where the cross-record picture belongs. §1's rule that "old outcomes are never
used as new measurements" means none of this is r1 evidence.

**E-1. The 19 corpus cases DV-007 now explains are exactly the 19 that refuted
EXP-001's H1.** The r1 `explained_dv007_case_ids` set and the predecessor's
`failing_case_ids` set are identical — same 19 IDs, no additions on either side
— over the same four grid cells. The corpus's native pass/fail partition is
unchanged between the two records: the same 485 cases pass natively and the same
19 do not. What differs is that a registered, positively-evidenced §5.3
explanation now exists for precisely the population that previously breached.

**E-2. H2a's movement is concentrated in the eligible stratum, and every
residual eligible breach is on a DV-007 path.** EXP-001's H2a had 897 passing
and 103 failing, with all 22 registered ill-conditioned indices among the
failures and so 81 failing eligible cases. r1 has 930 native-parity and 48
explained-dv007 among the 978 eligible, and those 48 indices are a strict subset
of the predecessor's 81 — 33 indices that previously breached natively now pass
natively. Which of the two correction mechanisms produced that shift is the
correction cycle's finding, not this report's, and §12.5 keeps cause out of an
exploratory section.

**E-3. The characterized stratum is concentrated and mostly long.** The 22 fixed
indices distribute as `stuart_landau/full/euler` 15, `stuart_landau/full/rk4` 2,
`hopf/full/euler` 2, `hopf/mean_field/euler` 2, `hopf/full/rk4` 1; 21 of 22 have
`n_steps > 20` and so remain H2b contributors, as §5.4 requires. Their native
worst-per-case absolute errors sit in `1e-1`=2 and `1e0`=20 — large-divergence,
not last-place, cases.

**No extra subgroup, distributional-distance or phase-boundary analysis was
performed**, and §8 forbids any from changing these verdicts.

---

## 13. Approvals, verification, and open obligations

| Item | Owner | Status |
|---|---|---|
| E5 report drafted from committed artefacts | AI pair (Qwen Code) | **done** — this document |
| Regeneration re-verified in this session | AI pair | **done** — §10, against the committed `report-manifest.json` |
| §10 item 5's `149cf2d..M` baseline delta listed as a deviation | AI pair | **done** — PD-5 |
| §10 item 5's both-72-case H4 GPU legs reported | AI pair | **done** — §7, under PD-6's stated reading |
| Parity Report admonition + CHANGELOG note | AI pair | **done** — this session's commit |
| EXP-001 erratum E-4 (append-only; no verdict changed) | AI pair | **done** — this session's commit |
| **Maintainer verification of the analysis and acceptance of the E5 verdicts** | MichaelMaillet | **PENDING** — the block below is unfilled |
| **Release of 0159 / EXP-002…EXP-008 / 0194** | MichaelMaillet | **PENDING §13 verification** — condition satisfied (§8), release not yet in force |
| **E1–E5 pull request; PR head SHA + required-check results recorded** | MichaelMaillet / AI pair | **OPEN** — nothing pushed; §14 records why and what it will need |
| Announcement of this report in the next Project State Report | next PSR session | **OPEN** — Experimentation Standards §2 E5; PSR-040 is not this session's to issue |
| Fresh-context independent review of this report before approval | recommended | **OPEN** — §9 item 9; not required by the plan, offered because E4 and E5 share one AI pair |

**Maintainer verification block** — to be completed at acceptance:

```text
Verified by: MichaelMaillet           Date (UTC): ____________
Verdicts accepted as reported (H1/H2a/H2b/H3/H4 all CONFIRMED):              [ ]
"No D1 raised" and the non-reversal determination in §8 accepted:            [ ]
PD-6's reading of §10 item 5 (report both legs; execute none at E5) accepted:[ ]
Release of 0159, EXP-002…EXP-008 and 0194 authorised on that verification:   [ ]
Opening the E1–E5 pull request authorised:                                   [ ]
```

Recorded in-session by the maintainer (Experimentation Standards §2 E5 and §4
"reports state which analyses were drafted by the AI pair and verified by the
maintainer"; campaign plan §2.2). **Acceptance of the verdicts is what releases
the block**: §8 item 3 explains why this report does not release it by itself.

**Security and quality gates for this session.** No first-party source in any
Snyk-supported language and no dependency manifest changed in this session — the
changes are Markdown, one reStructuredText admonition, and no code — so Snyk
Code, Snyk Open Source, `cargo audit` and `pip-audit` have no changed input to
scan here, and none is claimed to have run. The E4 module's own gate evidence
(ruff, `ruff format --check`, `mypy --strict`, interrogate 100 % (87/87), bandit,
Snyk Code 0 issues at `medium`, 89 tests, both CI pytest selections) is quoted in
[`analysis.md`](analysis.md) and is **local** evidence for the record-root module,
exactly as DV-040 records. CI remains the authoritative merge gate (Coding
Standards §6; amendment #45).

Because this session edits a Sphinx source and three governance-bearing
registers, the gates that *do* have changed input were run, all from this
checkout:

| Gate | Command | Result |
|---|---|---|
| Sphinx, clean output directory (AGENTS.md discipline: `_build` deleted first, never reused) | `python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | **`build succeeded`** with `-W` (warnings as errors); 35 sources, fresh environment. The nine "referenced in multiple toctrees" lines are pre-existing consistency notices, not warnings, and did not fail `-W` |
| Documentation-surface and paper-wiring regressions (`python.yml` docs job) | `pytest tests/test_sphinx_docs.py tests/test_paper_wiring.py tests/test_notebooks.py -m "not slow"` | **73 passed, 4 deselected** |
| Global-session registration | `python tools/check_global_session_registration.py` | passed (17 Executive Audit reports) |
| DV-register gate | `python tools/check_dv_register_gates.py` | passed (44 DV rows against 198 session-register entries) |
| skipif-guard executability | `python tools/check_skipif_probes.py` | passed |
| Deviation-ledger consistency | `python tools/check_deviation_ledger.py DOCS/reports/038-project-state.md DOCS/reports/039-project-state.md` | passed (128 → 142 rows; no PSR is issued here, so this confirms the existing ledger is undisturbed) |
| Documentation links | mechanical resolution of every relative link in the eight touched Markdown documents | **494 checked, 0 broken**; the RST admonition's cited repo paths and `report.md`'s in-page anchor also resolve |
| Report-figure cross-check | every quantitative claim in this report re-read from `summary.json`, `error-distributions.json`, `case-comparisons.json`, `report-manifest.json` and the on-disk artefact sizes, and compared programmatically | **194 assertions, all matching** — after correcting the one discrepancy it found (erratum **E-1**, a 2-byte stale total). Also surfaced the histogram-unit ambiguity now recorded as §9 item 11 and `analysis.md` erratum A-2 |

---

## 14. Pull request and CI record (campaign plan §12 item 3)

**No pull request exists yet and nothing has been pushed.** Campaign plan §12
item 3 requires each E-session to commit locally at its exit gate on its own
`campaign/<session>-<exp>-<stage>` branch, with `main` PR-only under ruleset
`22150076`, and the E5 session's PR to carry the E1–E5 range. Pushing and
opening that PR are shared-state actions this session was not authorized to
take, so they are recorded here as the next step rather than performed.

**Range the PR will carry.** Unlike the predecessor — whose E1/E2 reached `main`
early through PR #20 — **none** of EXP-001-r1's stages is on `main` yet. The PR
will carry the whole r1 range: E1 (`3f04460`), E2 (`f68f9d0`), the pre-execution
amendments and gate closures through `5d5ae35`, E3's six run directories
(`2036870`), the DV-044 correction merged into the campaign branch (`9cda4e5`),
E4 (`f057ef0`, `f966921`, `3270699`, `46fea62`) and E5 (this session). Its base
is `origin/main`; note that the campaign branch already incorporated
`M = 9b79d2e` via `b3b4a92`, so the PR's own delta against `main` is the r1
record, driver, artefacts and the DV-044 tool correction — not DV-041 or DV-043,
which reached `main` through PRs #25 and #26.

**What the report must not claim.** Per §12 item 3, the report records the
**tested PR head SHA** and the required-check results available before approval;
it must not claim the not-yet-created merge SHA. Neither exists, so neither is
stated. When the PR is opened, this section is completed by a docs-only addendum
commit naming the head the recorded checks actually ran against — the pattern
the predecessor's §14.1 established, including its note that later review-response
commits move the head and the *final* head's checks are the operative ones.

**Local branch state at issue of this report.**

| Branch | Tip | Contents |
|---|---|---|
| `campaign/exp001-r1-e1` | `f68f9d0` | E1 pre-registration, E2 review (historical; superseded by the preexecution branch) |
| `campaign/exp001-r1-preexecution` | `541fbfe` | E2 amendments, DV-043/DV-044 closure, `M` incorporated, E3 execution + log. Left untouched: this is the checkout `log.md` cites |
| `campaign/exp001-r1-e4` | `46fea62` | E4 analysis code, tests, record, output manifest, status reconciliations |
| `campaign/exp001-r1-e5` | this session | E5 report, erratum E-4, Parity Report admonition, CHANGELOG, register/index updates |

---

## 15. Errata

Corrections to this report are errata, never edits (campaign plan §12 item 6;
Experimentation Standards §1.3/§4). Each entry is appended at the point it
corrects and the original text is retained verbatim.

| # | Date (UTC) | Corrects | Substance | Raised by |
|---|---|---|---|---|
| **E-1** | 2026-09-29 | §5.2's "Generated reports / untracked diagnostics" row (and the same total quoted in [`analysis.md`](analysis.md), corrected there under its own erratum A-1) | The four generated outputs total **10,506,349 bytes**, not the 10,506,347 originally stated. The figure had been copied from a `dir` total taken *before* commit `f966921` added two backslash escapes to `summary.md`, which grew it from 14,035 to 14,037 bytes; every individual output digest and size quoted in §11.2 was and is correct, so the total simply disagreed with its own parts. Found by a mechanical cross-check of all 194 figures in this report against the committed artefacts, run before maintainer verification. **No verdict, digest, denominator, statistic or budget conclusion changes**: 10,506,349 B = 10.02 MiB, still far inside §9's 64 MiB working-space estimate. | This session's pre-verification figure cross-check |

No other erratum has been raised against this report.

Related append-only errata elsewhere, for traceability:

- **EXP-001 `report.md` §15 E-4** (added by this session): records that the
  condition E-3 described — 0159 blocked until `EXP-001-r1`'s E5 verdict is not
  a reversal — has been met by this report, subject to §13's verification.
  EXP-001's own verdicts, digests and artefacts are **not** edited.
- **[`analysis.md`](analysis.md) erratum A-1** (added by this session): the same
  10,506,347 → 10,506,349 byte-total correction as E-1 above, in the E4 record
  where the figure also appeared.

---

**Corrections to this report are errata, never edits.** No hypothesis verdict,
tolerance, denominator or protocol may change at or after E5.

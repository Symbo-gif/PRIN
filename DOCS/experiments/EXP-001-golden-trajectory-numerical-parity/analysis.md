# EXP-001 — Session 0157 E4 analysis record

**Status:** ANALYSED — the frozen pre-registration §8 decision rule has been
applied to all four immutable E3 run artefacts. **H1 and H2a are `REFUTED`,
which campaign plan §10.4 makes a D1.** H2b, H3, and H4 are `CONFIRMED`.
**Record date:** 2026-09-23 UTC.
**Operator:** MichaelMaillet.
**AI pair drafting this analysis:** Claude Opus 5 (Experimentation Standards §4
authorship disclosure). The maintainer verifies the analysis at E5 approval;
this record does not claim that verification has happened.
**Branch:** `campaign/0157-exp001-e4`.
**Pre-registration freeze SHA:** `c22db0b` (`log.md` line 1, campaign plan §12.4).
**Execution code SHA under analysis:** `6b9d6b621a2a46e37373bbcafafd475c1d0f644f`.

> This record interprets nothing beyond the registered rule. Diagnosis of the
> refuted hypotheses belongs to the correction cycle campaign plan §10.4
> inserts, not here.

## Entry conditions

| Condition | Evidence |
|---|---|
| E3 log closes execution | `log.md` §"Handoff": all four registered runs executed, none aborted, each closed with `check_run_complete` + `append_manifest` + `verify_manifest` |
| Raw artefacts immutable and manifest-verified | `tools.reproduce.verify_manifest` re-run here on all four run directories from this checkout: **all pass**, every file matching its manifest in size and SHA-256. The digests are reproduced in the summary output's artefact index and in `report-manifest.json` |
| Inputs come from the registered code SHA | The analysis module fails closed unless each artefact's `environment.git_commit` is exactly `6b9d6b6…f644f` (`_load_artefact`); all four match |
| No E3 driver or artefact change | `git diff` against `main` touches no file under `benchmarks/results/EXP-001/` or `benchmarks/campaign/` in this session |

Per the E3 log's recorded property, `check_run_complete` is a *closure-time*
validator bound to the absolute `out_dir` recorded at execution and raises
`IncompleteRunError` from any other path by design. E4 therefore uses
`verify_manifest` — campaign plan §7.4 step 1's portable check — exactly as
that note instructs.

## Analysis code (campaign plan §7.4 item 2)

| Item | Value |
|---|---|
| Path | [`analysis/exp001_e4_analysis.py`](analysis/exp001_e4_analysis.py) |
| Tests | [`tests/test_exp001_e4_analysis.py`](../../../tests/test_exp001_e4_analysis.py) — 33 passing |
| Registered H2b predicate | **Not re-implemented.** Delegated to `benchmarks.campaign.exp001_driver.adjudicate_h2b`, the single committed implementation (pre-registration §2) |
| Statistics added | **None.** The only estimator anywhere in this analysis is H2b's registered bootstrap CI inside the driver, which routes through `prin.y4q1_tools` → Rust `y4q1_stats` (campaign plan §9.2) |
| Determinism | No wall clock is read (`--generated-at` defaults to the registered `2026-09-23T00:00:00Z`); no randomness is drawn outside the seeded bootstrap; JSON is emitted with sorted keys and LF newlines; Markdown rows are emitted in fixed order |

Local gate on the new code, run in this session:

| Gate | Command | Result |
|---|---|---|
| Lint | `ruff check` on the module and its tests | passed |
| Format | `ruff format --check` on both | passed |
| Types | `mypy --strict` on the module | `Success: no issues found in 1 source file` |
| Docstrings | `interrogate -c pyproject.toml` on `analysis/` | 100 % (32/32), gate ≥ 95 % |
| SAST | `bandit` on the module (926 LOC scanned) | no issues identified |
| Snyk Code | `snyk code test --severity-threshold=medium` on `analysis/` and on the test file | **0 issues, exit 0** — clean at the governed threshold `snyk.yml` enforces |
| Tests | `pytest tests/test_exp001_e4_analysis.py` | 33 passed, with and without `--basetemp=.pytest_basetemp` |
| Full suite | `pytest tests/ parity/ --basetemp=.pytest_basetemp` | **3,847 passed, 178 skipped, 0 failed** (638.84 s, exit 0) |

**Snyk residual, disclosed rather than suppressed.** At `--severity-threshold=low`
the module reports three `LOW` "Path Traversal" informationals where the
operator-supplied `--output-dir` / `--manifest-path` reach a write. They are
below the governed threshold and no `.snyk` ignore was added for them. The
first pass reported five; the two read-path findings were **fixed**, not
waived, by removing the `--repository-root` command-line option (the analysis
is now bound to its own checkout, which is what campaign plan §7.4 step 5
wants anyway), and the three remaining writes are contained by
`allowed_output_roots` — the pattern `tools.reproduce` and
`prin.reporting._artifacts` already use — which Snyk's taint model does not
recognise as a sanitizer.

That containment is applied in `main`, at the command-line boundary, not
inside `run_analysis`. The first draft put it in `run_analysis` and the full
suite caught the consequence: under the repository's documented
`--basetemp=.pytest_basetemp`, a pytest scratch directory lives *inside* the
repository and is not one of the governed roots, so four tests failed on their
own scratch paths. Constraining a library function's caller was the wrong
boundary — the untrusted input is the command line, and a programmatic caller
supplies its own trusted directory. Moving the check left the command-line
guard intact (now covered by its own test) and changed no output digest.

**Full-suite invocation note.** An earlier full-suite run of the same tree
through PowerShell reported four failures in
`tests/test_wp001_baseline.py::test_release_workflow_publish_or_skip_*`. Those
tests shell out through `shutil.which("bash")`, they pass in isolation, and
they touch no file this session changed; under the repository's documented
Git Bash invocation the whole suite is green. The failing invocation is
disclosed here rather than dropped, and nothing was relabeled a pass — this
matches the environment-dependence the DV-036 correction cycle already
recorded for this host.

No first-party source in another supported language and no dependency manifest
changed in this session, so Snyk Open Source, `cargo audit`, and `pip-audit`
have no changed input to scan here. CI remains the authoritative merge gate.

## Verdicts (pre-registration §8)

| Hypothesis | Verdict | Non-aborted | Pass | Fail | Registered denominator |
|---|---|---|---|---|---|
| H1 — corpus parity | **REFUTED (D1)** | 504 | 485 | **19** | 504 |
| H2a — fuzzed within-horizon parity | **REFUTED (D1)** | 1,000 | 897 | **103** | 1,000 |
| H2b — fuzzed beyond-horizon equivalence | **CONFIRMED** | 657 contributing cases per metric | both metrics inside ±δ | — | ≥ 30 per metric |
| H3 — bit-level seeded repeatability | **CONFIRMED** | 14 | 14 | 0 | 14 |
| H4 — GPU kernel-path tolerance-identity | **CONFIRMED** | 72 | 72 | 0 | 72 |

**No case aborted in any run**, so no hypothesis falls into §8's
partial-abort `INCONCLUSIVE` branch and no abort reason is reported.

### H1 — REFUTED

§8: `CONFIRMED` iff all non-aborted cases have `within_tolerance=True` **and**
the non-aborted count is exactly 504; `REFUTED` (D1) if any non-aborted case
has `within_tolerance=False`. The count clause is met (504/504 non-aborted);
the tolerance clause is not — 19 cases breach. The rule yields `REFUTED`.

Registered tolerances applied by `prin.parity.harness.compare_case`:
trajectories `rtol=1e-6, atol=1e-8`; metrics `rtol=2e-6, atol=1e-12`.

Breaching arrays (a case may breach more than one): `phase_traj` 15,
`mean_phase_coherence_traj` 8, `phase_final` 5. Breaching grid cells:
`stuart_landau/full/euler` 10, `stuart_landau/full/rk4` 7,
`kuramoto/mean_field/euler` 1, `kuramoto/mean_field/rk4` 1.

Magnitudes are small: the largest absolute error anywhere in the run is
**2.008567e-07** and the largest relative error **1.271357e-03**. Over the
504 non-aborted cases the worst-per-case absolute error distributes as
`1e-17`=97, `1e-16`=189, `1e-15`=2, `1e-10`=66, `1e-9`=76, `1e-8`=51,
`1e-7`=23 — 288 cases agree to within a few units in the last place, and the
19 failures sit in the `1e-10`…`1e-7` tail (`1e-10`=1, `1e-9`=2, `1e-8`=9,
`1e-7`=7).

The registered rule is a deterministic per-case pass/fail and campaign plan
§9.1 forbids using any significance test to rescue a failed case. Small
magnitude is reported, not credited.

### H2a — REFUTED

§8: `CONFIRMED` iff no within-horizon breach across all non-aborted cases
**and** the non-aborted count meets the registered batch size. The artefact
records `fuzz_batch_class: "confirmatory"`, `n_fuzz_cases_requested: 1000`,
and `fuzz_batch_confirmatory_minimum: 1000`; 1,000 cases are non-aborted, so
the count clause is met. 103 cases breach at steps `0..min(20, n_steps)`, so
the rule yields `REFUTED`.

Breaching arrays: `amplitude_traj` 68, `phase_traj` 58,
`mean_phase_coherence_traj` 48, `order_parameter_traj` 31, `frequency_traj`
11. Breaches appear in 12 of the 14 grid cells, most often
`stuart_landau/full/euler` 34, `kuramoto/mean_field/rk4` 12,
`kuramoto/mean_field/euler` 10.

Unlike H1, the magnitudes are **not** uniformly small. Worst-per-case
absolute error over the 103 failing cases: `1e-11`=1, `1e-10`=6, `1e-9`=7,
`1e-8`=18, `1e-7`=2, `1e-6`=36, `1e-1`=4, `1e0`=27, `1e1`=2 — that is 33
cases at or above `1e-3`, the largest being **2.654853e+01**.

**On the reported maximum relative error of 2.477303e+299.** This is a guard
artefact, not a 300-decade discrepancy. `compare_arrays` computes
`|ref − prod| / (|ref| + 1e-300)`, so an element whose reference value is
exactly `0.0` divides by the guard alone. The element in question is in
`amplitude_traj` of fuzz case index 841 (`hopf/full/euler`, N=12,
n_steps=23), where the absolute difference is **2.477303e-01**. The absolute
figures above are the ones to read; the relative maximum is reported because
campaign plan §9.1 registers it, with this caveat attached.

### H2b — CONFIRMED

Computed by `exp001_driver.adjudicate_h2b`, independently per metric, over one
predefined paired summary per non-aborted `n_steps > 20` case. 657 cases
contribute to each metric, far above the registered minimum of 30, so neither
metric falls into the minimum-information `INCONCLUSIVE` branch.

| Metric | n | δ | mean paired difference | 95 % bootstrap CI | Verdict |
|---|---|---|---|---|---|
| `order_parameter_traj` | 657 | 0.01 | −1.930404e-03 | [−4.004274e-03, −1.204094e-04] | **CONFIRMED** |
| `mean_phase_coherence_traj` | 657 | 0.02 | −1.605610e-03 | [−3.676295e-03, +5.565305e-04] | **CONFIRMED** |

Both endpoints of both intervals lie strictly inside that metric's ±δ, which
is the registered predicate in full. Descriptive statistics, which gate
nothing: Cohen's *d* −6.708155e-03 and Welch *t* −1.215824e-01, *p*
9.032484e-01 for `order_parameter_traj`; *d* −5.281658e-03 and *t*
−9.572777e-02, *p* 9.237514e-01 for `mean_phase_coherence_traj`.

The bootstrap is `prin.y4q1_tools.bootstrap_ci`, 10,000 resamples, α = 0.05,
seed 42 — the registered configuration. Re-running the adjudication in the
same process and from a fresh process reproduces identical endpoints.

**This verdict is narrower than it may look.** H2b concerns only the mean
per-case paired difference of two bounded coherence metrics beyond step 20.
It says nothing about the pointwise trajectory agreement H2a tests, and it
does not offset H2a's refutation: §8 adjudicates them separately and
pre-registration §4 makes either one's refutation a D1 on its own.

### H3 — CONFIRMED

14 non-aborted cases, 14 bit-identical, denominator exactly 14, no mismatched
array in any case. Both §8 clauses are met.

### H4 — CONFIRMED

72 non-aborted cases, 72 within `rtol=1e-5, atol=1e-6`, denominator exactly
72. The artefact's `environment.backend` is `cuda` with the RTX 4060 and
8,188 MiB recorded, so the registered `NOT EXECUTED — cuda feature not built`
`INCONCLUSIVE` branch (pre-registration §4 item 6) does not apply. Largest
absolute error **8.977524e-07** against the `atol=1e-6` bound; largest
relative error 8.953823e-04 against `rtol=1e-5`; every one of the 72 cases has
a worst-case absolute error in the `1e-7` decade.

## D1 declaration (campaign plan §10.4)

H1 and H2a are C1 parity hypotheses, and pre-registration §4 states that any
H1/H2a/H3/H4 refutation is a D1 — "scientific conclusion differs from
PRINet 3.0" — and not a publishable novelty. **The D1 flag is raised**, and it
is recorded in `report-manifest.json` (`"d1_flag": true`) as well as in every
generated output.

Consequences, as the plan already fixes them — this session opens no
correction cycle and makes no root-cause claim:

1. Detection is at E4 and is recorded in the E5 report as `REFUTED` with the
   D1 flag (§10.4 item 1). This record is that detection.
2. **Session 0158 (E5) still completes** and reports the negative result in
   full (§10.4 item 2; Experimentation Standards §1.2). E4 does not block it.
3. 0158 then **blocks its successor, session 0159 (EXP-002 E1)**, and the four
   contingency correction sessions (S1-correction → S2 → S3 → S4) run before
   the blocked numbered session resumes (§3.3). Every experiment downstream in
   §3.2 inherits the block, which is all of EXP-002…EXP-008 and 0194.
4. After S4, EXP-001 is re-run as a **new** experiment record (`EXP-001-r1`,
   new pre-registration, new run directories); this record stays as-is with an
   erratum pointer (§10.4 item 4). The present artefacts are never edited.
5. Campaign plan §10.4 item 3 allows the correction to conclude instead that
   the PRINet 3.0 conclusion was itself defective (the amendment-#25 class),
   but only on an EMA-style mathematical audit claim, Z3/SymPy-verified where
   applicable. Nothing in this record asserts which side is wrong.

§10.2's row reads "block the successor session" in general terms while §10.4
item 2 is explicit that the E5 session completes first. §10.4 is the clause
that operationalizes §10.2 for a C1 reversal, so this record follows it and
flags the wording difference for the E5 session to restate.

## Protocol deviations

**PD-1 — the summary table is generated by the committed E4 analysis module,
not by a `prin.reporting` generator.** Pre-registration §8 says the summary
table is "generated deterministically via `prin.reporting`". That is not
satisfiable as written: `prin.reporting`'s aggregators
(`generate_benchmark_report`, `generate_leaderboard`) consume the PRINet 3.0
artefact schema — `status`, `benchmarks`, `test_acc`, `results` — none of
which EXP-001's artefacts carry, and they have no notion of a pre-registered
hypothesis or verdict. Run against a real EXP-001 run directory,
`generate_benchmark_report` emits `OK` and `—` for every file and an empty
detail block; it cannot produce a hypothesis × verdict × pass count × max
error table. The table is therefore produced by
`analysis/exp001_e4_analysis.py`, which campaign plan §7.4 item 2 names as a
permitted location for analysis code, under the same determinism guarantees
§7.4 step 3 requires of the `prin.reporting` generators (explicit
`generated_at`, sorted keys, fixed row order, no implicit clock). **No
decision rule, tolerance, statistic, or artefact is affected.** The E5 report
carries this deviation forward; it is not edited into the frozen
pre-registration.

**PD-2 — campaign plan §7.4 item 2 says analysis code is committed "before E4
starts"; it was committed *by* E4.** No analysis code existed for EXP-001 at
the end of E3. This session committed the module, its tests, and the local
gate evidence before generating any output, so no verdict was produced by
uncommitted code, but the literal ordering was not met. Recorded as a
deviation rather than narrated as compliance. A campaign-wide fix belongs to
the E1/E2 slot of the next experiment (E1 authors the analysis code alongside
the driver, E2 approves it), which is a campaign plan §12.1-shaped change and
therefore a maintainer decision, not an E4 one.

**PD-3 — no figures were generated.** Pre-registration §8 states that "no new
visualization is required for a pass/fail parity table". Consistent with the
registered plan, recorded here for completeness of the deviation list.

No other deviation from the frozen protocol occurred: no hypothesis, tolerance,
seed, denominator, or decision rule was changed; no case was excluded; no
unregistered confirmatory test was run; no raw artefact was mutated.

## Threats to validity

1. **The clamp-trip residual stands as registered.** Pre-registration §4
   item 1 records that `prin-dynamics::clamp_derivative` exposes no trip
   signal through PyO3, so a clamp trip that leaves every checked output
   finite and in range reaches an ordinary `aborted: false` result. Every
   verdict in this record inherits that boundary: a clamp-trip-affected case
   cannot be distinguished from a clean one by this driver. This is a
   registered limitation, not a new finding.
2. **Single host, single platform.** All four runs executed on host H1
   (Windows 11, AMD64, RTX 4060). Pre-registration §9 records that the
   optional cross-OS regeneration leg was not scheduled, so no claim is made
   about whether the H1/H2a breaches reproduce on another platform or
   toolchain. `verify_manifest` reproducing every digest from a clean checkout
   is an artefact-integrity result, not a cross-platform numerical result.
3. **H2b's scope.** See the note under H2b: a confirmed distributional
   equivalence of two bounded metrics beyond step 20 neither implies nor
   repairs pointwise agreement inside the horizon.
4. **H4's denominator is the corpus's, not the kernel's.** H4 exhausts the 72
   `kuramoto_sparse_knn_*` corpus cases at `N ≤ 24`. It is not evidence about
   the GPU kernel at larger `N`, other couplings, or other models.
5. **The relative-error statistic is unstable near zero.** The
   `+1e-300` guard in `compare_arrays` makes the reported maximum relative
   error meaningless where the reference is exactly zero (H2a above). The
   registered pass/fail rule uses `numpy.isclose`, which is unaffected; only
   the reported statistic is.
6. **Governance gap in the gate coverage of this analysis code.** CI's lint
   job runs `ruff`/`mypy`/`interrogate`/`bandit` over `python/ tests/
   benchmarks/ tools/` only, so a module under the experiment's record root —
   the location campaign plan §7.4 item 2 prescribes — is outside the
   authoritative merge gate. The gates above were therefore run locally, and
   the tests were placed under `tests/` so that at least the behavioural
   check is CI-enforced. Registered as **DV-040**.

## Exploratory

Everything below is **exploratory**: it is not pre-registered, it gates
nothing, it alters no verdict, and it attributes no cause (campaign plan
§12.5). It is recorded because the correction cycle §10.4 inserts will want a
starting point.

**E-1. Both refutations concentrate in the same place.** In H1, 17 of the 19
failures are `stuart_landau/full` (17 of that model's 72 corpus cases, versus
2 of the other 432). In H2a, `stuart_landau/full/euler` alone carries 34 of
the 103 failures and 17 of the 33 large-magnitude ones.

**E-2. Both refutations concentrate at larger step sizes.** H1's corpus grid
has three step sizes with 168 cases each; the 19 failures split
`dt=0.02` → 9, `dt=0.01` → 9, `dt=0.005` → 1. In H2a, splitting the 1,000
fuzzed cases at the sampled median `dt ≈ 0.0255` gives 10 breaches (1 of them
large) below it and 93 (32 large) above. The split point is chosen post hoc
from the observed sample and supports no inference; it is reported as a
description of where the failures sit.

**E-3. The two failure populations look different in magnitude.** H1's
failures top out at 2.0e-07 — the scale of accumulated float64 rounding-order
divergence between two independently implemented integrators, which is also
what pre-registration §3's H2b pilot note anticipated beyond the horizon. H2a
contains a second population, 33 cases at or above 1e-3 and up to 2.7e+01,
which is not that scale. Whether these are one mechanism or two is exactly the
question the correction cycle owns; this record does not answer it.

## Outputs and regeneration

Generated deterministically into the gitignored
`DOCS/test_and_benchmark_results/EXP-001/` and digested in the committed
[`report-manifest.json`](report-manifest.json) (campaign plan §7.4 item 4):

| Output | bytes | SHA-256 |
|---|---|---|
| `exp001-e4-adjudication.json` | 12,974 | `e6f6eb200b3db8be6cc8ed6a80ad1e5733e143f8000f2a0a3a1ad427bddab525` |
| `exp001-e4-summary.md` | 5,783 | `4551061c5eff1bc73d5c9ddb65d6533dfca9dcd774f46a9310eb0241b0f88229` |

`report-manifest.json` also carries each input run's `manifest.json` records,
the per-hypothesis verdicts, and the D1 flag, because the generated outputs
themselves are gitignored.

Regeneration (campaign plan §7.4 step 5) — from a clean checkout of this
session's commit, at the repository root:

```powershell
.venv\Scripts\python.exe "DOCS\experiments\EXP-001-golden-trajectory-numerical-parity\analysis\exp001_e4_analysis.py"
```

Expected stdout:

```
H1: REFUTED
H2a: REFUTED
H2b: CONFIRMED
H3: CONFIRMED
H4: CONFIRMED
D1 flag: RAISED
```

Both output digests must match the table above byte for byte. Passing
`--generated-at` anything other than the registered default changes every
digest and is not a regeneration.

## Handoff to E5 (session 0158)

- The E4 exit gate is met: reproducible analysis outputs and the manifest are
  committed, and every verdict comes from the frozen §8 rule.
- 0158 reports all five verdicts in full, including the two negatives, with
  the expected-vs-observed table pre-registration §3 sets up, PD-1 through
  PD-3, and the threats above.
- 0158 carries the **D1 flag** and blocks session 0159 per §10.4 item 2. Its
  own brief is consistent with that reading: expected-work item 3 tells E5 to
  "trigger and close a D1 correction cycle before proceeding", and its exit
  gate requires "approved report **and** any required correction-cycle
  evidence". So 0158 writes and approves the report, opens the cycle, and its
  exit gate is not discharged until the correction S4 closes — which is the
  same thing §10.4 items 2–4 describe from the campaign's side.
- 0158's artefact index lists each input run's `manifest.json` digest and this
  session's `report-manifest.json` digest (campaign plan §7.4 item 5).
- No hypothesis verdict, tolerance, or protocol may change at E5; corrections
  to this record are errata (Experimentation Standards §1.3/§4).

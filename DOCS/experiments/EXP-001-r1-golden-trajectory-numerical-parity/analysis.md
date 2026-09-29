# EXP-001-r1 — E4 analysis record

**Status:** ANALYSED — the frozen pre-registration §8 decision rule has been
applied to all six immutable E3 run artefacts. **All five hypotheses are
`CONFIRMED`; the campaign plan §10.4 D1 flag is not raised.** This is a
**non-reversal** detection relative to the predecessor EXP-001, whose H1 and
H2a were `REFUTED`.
**Record date:** 2026-09-29 UTC.
**Session:** `EXP-001-r1-E4`, declared by MichaelMaillet. The r1 stages carry
no integer session number; the register's next numbered session, 0159
(EXP-002 E1), is **not** released by this record — campaign plan §10.4 item 5
keys the release to E5's verdict.
**Operator:** the AI pair below, acting on the maintainer's session
declaration and this record's frozen protocol.
**AI pair drafting this analysis:** Qwen Code (Experimentation Standards §4
authorship disclosure). It did not draft E1, E2 or E3. The maintainer verifies
the analysis at E5 approval; this record does not claim that verification has
happened.
**Branch:** `campaign/exp001-r1-e4`, off `campaign/exp001-r1-preexecution`
(see PD-4).
**Pre-registration freeze SHA `F`:** `5d5ae3521317af47a11afa8d689935ac2fc0f447`
(`log.md` line 1, campaign plan §12.4).
**Execution code SHA under analysis `R`:** `5d5ae3521317af47a11afa8d689935ac2fc0f447`.
**Green-main baseline `M`:** `9b79d2e5b246bead1243074659dc99d049762a40`.
**Analysis code SHA (campaign plan §7.4 item 2):** `3270699` — the verdicts in
this record were produced by exactly this commit.

> This record interprets nothing beyond the registered rule. It makes no
> root-cause claim, no new tolerance, no new denominator and no exclusion.

## Entry conditions

| Condition | Evidence |
|---|---|
| E3 log closes execution | [`log.md`](log.md): all six registered runs executed 2026-09-29 in the registered order, zero aborts, zero retries, no reused directory, each closed with the driver's `check_run_complete` + `append_manifest` + `verify_manifest` |
| Raw artefacts immutable and manifest-verified | `tools.reproduce.verify_manifest` re-run here on all six run directories from this checkout: **all pass**, every file matching its manifest in size and SHA-256. Independently repeated from a clean detached checkout at `3270699` (see "Regeneration"). Digests are reproduced in `summary.md`'s artefact index and in [`report-manifest.json`](report-manifest.json) |
| Inputs come from the registered code SHA `R` | The analysis fails closed unless every artefact's `environment.git_commit` is exactly `5d5ae35…f447` **and** each run-ID `<sha>` prefixes it (`load_run`); all six match |
| Exactly six distinct r1 runs, no more | `verify_run_inventory` enumerates run-directory *names* under the shared raw root and requires the set to equal the index exactly. Present: the six indexed runs; the four predecessor `RUN-…-6b9d6b6-*` directories are retained untouched and are not r1 runs |
| Two backend-labelled kernel-path legs on one `R`, with two build-log extension hashes | `log.md` records `2f902e80…` for the `--features wgpu` build and `701bb529…` for the `--features cuda` build; `verify_e3_log` requires both literals plus `F`, `R` and `M` in the log, and `_verify_envelope` requires each leg to carry **its own** hash. Both legs record `git_commit = R`; the hashes differ by design and binary identity is not demanded (§5.1, §8 rule 1) |
| Input fingerprints | Corpus manifest SHA-256 recomputed from `parity/corpus/manifest.json` = `fcbaad1c…d2cf`; fuzz stream replayed from `Seed(0, 1)` = `9804fc09…ff76`; reference source `89d19734…d4b9`; instrument `c6972d5f…31c2`; PRINet `3.0.0`. All equal the frozen pins and every run's own `config` values |
| No E3 driver or artefact change | `git diff 5d5ae35 HEAD -- python benchmarks/campaign tools parity crates` is **empty**: no first-party numerical, driver, corpus or tooling source differs between `R` and the analysis commit. The only later additions are this record's analysis module, its tests, and documentation |

Per the E3 log's recorded property, the driver's `check_run_complete` is a
*closure-time* validator bound to the absolute `out_dir` recorded at execution
and raises `IncompleteRunError` from any other path by design. E4 therefore uses
`verify_manifest` — campaign plan §7.4 step 1's portable check — and validates
`config.out_dir` by basename only, exactly as the predecessor's E4 record
instructs.

## Analysis code (campaign plan §7.4 item 2)

| Item | Value |
|---|---|
| Path | [`analysis/exp001_r1_e4_analysis.py`](analysis/exp001_r1_e4_analysis.py) |
| Committed | `f057ef0`, **before any adjudication ran** — §7.4 item 2's ordering is met literally this time, so the predecessor's PD-2 does not recur |
| Tests | [`tests/test_exp001_r1_e4_analysis.py`](../../../tests/test_exp001_r1_e4_analysis.py) — 89 passing |
| Predecessor module | **Not imported, not retargeted.** `EXP-001/analysis/exp001_e4_analysis.py` is pinned to the four original `RUN-…-6b9d6b6-*` runs and to `EXP-001`'s identity; §8 forbids it as a source of r1 verdicts |
| Registered H2b predicate | **Not re-implemented.** Delegated to `benchmarks.campaign.exp001_r1_driver.adjudicate_h2b`, the single committed implementation (pre-registration §7) |
| Other registered predicates | Imported, not restated: `ILL_CONDITIONED`, `REPEATABILITY_CASES`, the DV-007 path predicate, the fuzz sampler and `h2a_stream_digest`, `KERNEL_RTOL`/`KERNEL_ATOL`, `T_STAR`, and the H2b statistical configuration. Tolerances come from `prin.parity.schema` |
| Statistics added | **None.** The only estimator anywhere in this analysis is H2b's registered bootstrap CI inside the driver, routing through `prin.y4q1_tools` → Rust `y4q1_stats` (campaign plan §9.2). Error distributions are exact decade counts and order statistics. The module does import NumPy, but only for the arithmetic §8 rule 2 *mandates*: recomputing each contributing case's `reference_mean`/`produced_mean`/`mean_paired_difference` from the stored paired arrays so the bootstrap runs on values this analysis derived itself. That is a reproducibility check on retained data, not a second numerical implementation of PRIN, and no integrator, model, coupling or metric reduction is evaluated here. `tools/check_no_python_numerics.py` scans a fixed list of WP-036 S1 compat modules and does not cover record-root analysis code; it was run and passes unchanged |
| Determinism | No wall clock is read (`--generated-at` defaults to the registered `2026-09-29T12:00:00Z`); no randomness is drawn outside the seeded bootstrap; JSON is emitted with sorted keys, `allow_nan=False` and LF newlines; Markdown rows are in fixed order; every number passes one renderer |

Local gate on the new code, run in this session (DV-040's compensating
control: a record-root module is outside CI's lint/type/SAST paths, so the
gates are run locally and the tests live in `tests/`):

| Gate | Command | Result |
|---|---|---|
| Lint | `ruff check` on `analysis/` and the test file | passed |
| Format | `ruff format --check` on both | passed |
| Types | `mypy --strict` on the module | `Success: no issues found in 1 source file` |
| Docstrings | `interrogate -c pyproject.toml` on `analysis/` | 100 % (87/87), gate ≥ 95 % |
| SAST | `bandit -c pyproject.toml` on the module | no issues identified |
| Snyk Code | `snyk code test --severity-threshold=medium` on `analysis/` and on the test file | **0 issues, exit 0** — clean at the governed threshold `snyk.yml` enforces |
| Tests | `pytest tests/test_exp001_r1_e4_analysis.py --basetemp=.pytest_basetemp` | 89 passed |
| Neighbouring suites | `pytest tests/test_exp001_r1_e4_analysis.py tests/test_exp001_e4_analysis.py tests/test_exp001_r1_driver.py tests/test_exp001_driver.py tests/test_reproduce.py --basetemp=.pytest_basetemp` | 481 passed, 3 skipped, 0 failed |
| CI test selection (`python.yml`'s `test` job) | `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp` | **3,450 passed, 178 skipped, 55 deselected, 1 failed, 1 error** (584.93 s) — both non-greens pass in isolation, see below |
| CI parity selection (`parity.yml`) | `pytest parity/ -m parity --basetemp=.pytest_basetemp` | **2,143 passed, 1 skipped, 1 error** (209.46 s) — the error passes in isolation, see below |

Both CI selections were run with the two process-level settings AGENTS.md
requires on this host: `PYTHONPATH` pinned to *this* checkout's `python`
directory (the shared venv's `prin.pth` points at `C:\dev\PRIN\python`, a
different worktree) and `C:\Program Files\Git\bin` prepended ahead of the
Windows WSL `bash.exe` relay. Neither is a test weakening; both are documented
host requirements. A session-local wrapper script set them and spawned pytest
as a subprocess; it lives under the gitignored `.qwen/tmp` and is not committed,
because the two environment variables are the whole of it.

**The three non-greens, disclosed rather than dropped.** None is a regression
from this session, and all three pass when re-run alone:

| Test | In-suite result | In isolation |
|---|---|---|
| `tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression` | `FAILED` — `Throughput ratio 2.64 > 1.30` | **passed** (4.15 s) |
| `tests/test_acceptance_phases.py::TestArtefactIO::test_save_load_roundtrip` | `ERROR` at setup — `PermissionError: [WinError 32]` on a `.pytest_basetemp` scratch directory | **passed** (2.93 s) |
| `parity/test_parity_subconscious.py::TestBackendSelectionParity::test_vitisai_option_keys_match_the_reference` | `ERROR` at setup — same `WinError 32` class | **passed** (2.30 s) |

The two errors are exactly the Windows `tmp_path` cleanup contention AGENTS.md
documents ("if lock errors appear, re-run the suite in isolation"). The failure
is a *timing-ratio* assertion measured on a workstation that was concurrently
loaded — an earlier suite run was still draining when this one started — which
is the DV-036 host-variance class, not a throughput regression: this session
changes no `prin`, Rust, benchmark, ONNX or provider source, only a
record-root analysis module, its tests and documentation. The same test passed
in an earlier run of the same tree in this session. Nothing was relabelled a
pass; the in-suite numbers above are the ones the run actually produced.

**A harness mistake made and corrected, recorded because it produced numbers
that looked like failures.** The first attempt at the CI selections called
`pytest.main()` in-process after setting `PYTHONPATH` inside the already-running
interpreter, where it has no effect. `prin` therefore resolved through the
venv's `prin.pth` to `C:\dev\PRIN\python`, so
`prin.reporting._artifacts._REPO_ROOT` pointed at the *wrong* checkout and
every allowed-output-root assertion failed: 15 failures across
`tests/test_acceptance_y4q2.py` and `tests/test_paper_wiring.py`, plus 4
`tests/test_wp001_baseline.py` `bash` failures from the missing Git Bash
prepend. Those 19 were artefacts of the harness, not properties of the tree;
spawning pytest as a subprocess with both settings correct removed all of them.
Disclosed here so the discarded numbers are not mistaken for a regression
someone later "fixed".

Governance gates re-run locally after this session's `SESSION_REGISTER.md` and
`phase-7/README.md` edits — the same four `python.yml`'s governance job runs:

| Gate | Result |
|---|---|
| `tools/check_global_session_registration.py` | `Global-session registration check passed` (17 Executive Audit reports) |
| `tools/check_dv_register_gates.py` | `DV-register gate check passed` (44 DV register rows against 198 session-register entries) |
| `tools/check_skipif_probes.py` | `no registration-probe skipif guards` |
| `tools/check_deviation_ledger.py 038-project-state.md 039-project-state.md` | `Ledger consistency check passed` — 128 → 142 rows |

`tools/check_no_python_numerics.py` was also run and passes unchanged; it scans
a fixed list of 19 WP-036 S1 compat modules and does not cover record-root
analysis code. This session issues no PSR and changes no deviation ledger, so
the ledger comparison has no new input; it is run to confirm this session did
not disturb the existing one.

Documentation links were checked mechanically rather than by eye: all **427**
relative Markdown links across the six documents this session touched (this
record, the record `README.md`, `analysis/README.md`,
`DOCS/experiments/README.md`, `SESSION_REGISTER.md` and
`DOCS/sessions/phase-7/README.md`) resolve to an existing path — **0 broken**.

**Snyk residual, disclosed rather than suppressed.** At
`--severity-threshold=low` the module reports **one** `LOW` "Path Traversal"
informational where the operator-supplied `--output-dir`/`--manifest-path`
reach a write. It is below the governed threshold and no `.snyk` ignore was
added for it. Those two writes are contained by `allowed_output_roots` /
`allowed_generated_output_dirs` — the pattern `tools.reproduce` and
`prin.reporting._artifacts` already use — which Snyk's taint model does not
recognise as a sanitizer. Containment is applied in `main`, at the
command-line boundary, not inside `run_analysis`: under the repository's
documented `--basetemp=.pytest_basetemp` a pytest scratch directory lives
*inside* the checkout and is not a governed root, so constraining the library
function would break its own tests. The predecessor hit the same boundary and
reached the same conclusion; its tests are the reason this one is placed
correctly from the start. The input root is never a command-line option at all.

No first-party source in another supported language and no dependency manifest
changed in this session, so Snyk Open Source, `cargo audit` and `pip-audit`
have no changed input to scan here. CI remains the authoritative merge gate.

**One fail-closed abort during this session, and its resolution.** The first
adjudication attempt raised `AnalysisError`: the index declared the fuzz leg's
sidecar hypotheses as `["H2a", "H2b"]`, while the artefact E3 committed
carries `["H2"]`. The artefact is correct — the campaign's registered tag set
is H1…H4 (`_VALID_HYPOTHESES`), and `H2a`/`H2b` are §2's split of `H2`, which
the sidecar schema has no slot for. The **index was wrong, not the evidence**:
no artefact was edited, no check was weakened, and no verdict was produced
from the aborted run. `3270699` corrected the index and added
`ADJUDICATED_HYPOTHESES`, so `summary.json` and `report-manifest.json` now
report both what E3 committed (`sidecar_hypotheses`) and what E4 derives
(`adjudicated_hypotheses`). All verdicts in this record come from `3270699`.

## Verdicts (pre-registration §8 rules 3 to 7)

| Hypothesis | Verdict | Non-aborted | Accepted / passing | Registered denominator |
|---|---|---|---|---|
| H1 — corpus parity with the registered DV-007 explanation | **CONFIRMED** | 504 | 504 (485 native-parity + 19 explained-dv007) | 504 |
| H2a — fuzz parity within the comparison horizon | **CONFIRMED** | 1,000 | **978 pointwise + 22 characterized** | 978 + 22 |
| H2b — beyond-horizon ensemble mean coherence equivalence | **CONFIRMED** | 657 contributors per metric | both metrics' CIs strictly inside ±δ | ≥ 30 per metric |
| H3 — CPU bit-level repeatability | **CONFIRMED** | 14 + 14 | 28/28 byte-identical; projections identical | 14 per run, 2 runs |
| H4 — CUDA and wgpu derivative-kernel agreement | **CONFIRMED** | 72 + 72 | 144/144, zero failed derivative elements | 72 per backend |

**No case aborted in any of the six runs**, so no hypothesis falls into §8's
partial-coverage `INCONCLUSIVE` branch and no abort reason is reported. Zero
unexplained breaches anywhere: `n_unexplained_breach = 0` for H1 and H2a.

### H1 — CONFIRMED

§8 rule 3: any valid unexplained breach refutes; otherwise confirm only with
504 valid accepted cases; incomplete valid coverage is inconclusive. All 504
cases are non-aborted and accepted, so the rule yields `CONFIRMED`.

The confirmation is **not** a claim that every native PRINet array was
reproduced within tolerance, and §2 forbids reading it that way. Published
separately, as §2 requires: **485 native-parity**, **19 explained-dv007**,
**0 unexplained breaches**, **0 aborts**.

Each of the 19 was re-derived here from its retained per-array records (§8
rule 2), not taken on trust: the case breached natively, its `(model,
coupling)` is on a §5.3-eligible path (Stuart–Landau full coupling, or
Kuramoto/Hopf mean-field), and every one of its 11 float64-reference
comparisons passes at the *unchanged* array tolerances. The corrected
reference reproduces PRIN to machine precision on exactly those cases: the
`corpus/corrected` stratum (19 cases, 209 comparator records) has a maximum
absolute error of **8.881784e-16** and a maximum relative error of
**1.281938e-13**, distributed `1e-17`=2, `1e-16`=17 — against a
`corpus/native` maximum absolute error of **2.008567e-07**. Over all 504 cases
the native worst-per-case absolute error distributes as `1e-17`=97,
`1e-16`=189, `1e-15`=2, `1e-10`=66, `1e-9`=76, `1e-8`=51, `1e-7`=23, so 288 of
504 cases agree to within a few units in the last place. The 19 explained
cases are exactly the `1e-9`…`1e-7` part of that tail (`1e-9`=2, `1e-8`=9,
`1e-7`=8; worst-per-case absolute error from **2.079373e-09** to
**2.008567e-07**), and the 485 native-parity cases hold the remaining
`1e-17`…`1e-7` mass.

The 19 explained cases distribute over four grid cells:
`stuart_landau/full/euler` 10, `stuart_landau/full/rk4` 7,
`kuramoto/mean_field/euler` 1, `kuramoto/mean_field/rk4` 1 — precisely the
three DV-007-eligible path families §5.3 step 3 names, and no cell outside
them. A model name or a historical case ID alone was never accepted as an
excuse: eligibility was re-tested from each case's own recorded
`(model, coupling)`.

Registered tolerances, applied by `prin.parity.harness.compare_case` at E3 and
re-checked here for internal consistency: trajectories `rtol=1e-6, atol=1e-8`;
metrics `rtol=2e-6, atol=1e-12`.

### H2a — CONFIRMED

§8 rule 4: any valid eligible unexplained breach refutes; otherwise confirm
only with 978 valid accepted eligible cases **plus** all 22 valid registered
characterizations; a missing or aborted sensitivity witness cannot reduce the
registered denominator and yield confirmation.

Reported as **978 pointwise + 22 characterized**, never as 1,000 pointwise
passes:

- **978 eligible** (all stream indices outside the fixed 22): 930
  `native-parity` + 48 `explained-dv007`, all accepted, **0 unexplained
  breaches**.
- **22 characterized** (exactly the registered indices 50, 76, 90, 270, 310,
  330, 334, 362, 385, 398, 399, 415, 456, 522, 621, 623, 653, 691, 734, 841,
  867, 878): every one carries a reproduced one-ulp reference-sensitivity
  witness, `pointwise_eligible = false`, `accepted = null`,
  `classification = "ill-conditioned-characterization"`. Their
  characterization is **not** a pointwise-parity success (§2, §5.4).

The index inventory was checked against a replay of the pinned stream, not
just against its own recorded digest: the 1,000 draws were redrawn from
`Seed(0, 1)` through the driver's own sampler, the whole-stream digest equals
the frozen `9804fc09…ff76`, and **every** case's `input_sha256` and all seven
recorded spec fields equal the redrawn values at that index. No case was
excluded, and no exclusion was selected from a PRIN error.

The `fuzz-eligible/native` stratum's maximum absolute error is
**5.050686e+00** — that is a *native* reference divergence on a DV-007 path,
not a PRIN defect: the same 48 cases' `fuzz-eligible/corrected` maximum is
**2.775092e-08**, inside the registered bound. The two numbers must be read
together.

### H2b — CONFIRMED

Computed by `exp001_r1_driver.adjudicate_h2b` — the single committed
implementation of the registered three-way (TOST-style) rule — independently
per metric, over one predefined paired summary per contributing case
(`n_steps > 20`). **657** cases contribute to each metric against a floor of
30, and all 1,000 draws are accounted for with zero aborts, so §8 rule 5's
completeness condition holds and neither metric falls into the
minimum-information branch.

Before the helper ran, §8 rule 2's recomputation was performed: each
contributing case's `reference_mean`, `produced_mean` and
`mean_paired_difference` were recomputed from the stored paired metric arrays
and required to match the stored values **exactly** (binary64 round-trips
through JSON and `np.mean` is deterministic for a fixed array). All 657 × 2
matched with zero discrepancies; a tampered summary would have aborted the
analysis rather than being averaged over.

| Metric | n | δ | mean paired diff | 95 % bootstrap CI | Verdict |
|---|---|---|---|---|---|
| `order_parameter_traj` | 657 | 0.01 | −1.363025e-04 | [−5.388353e-04, +3.189321e-04] | **CONFIRMED** |
| `mean_phase_coherence_traj` | 657 | 0.02 | −2.509004e-04 | [−9.586380e-04, +5.733745e-04] | **CONFIRMED** |

Both endpoints of both intervals lie strictly inside that metric's ±δ, which
is the registered predicate in full; neither interval touches or overlaps a
boundary, so no metric is `INCONCLUSIVE`. Descriptive statistics, which gate
nothing: Cohen's *d* −4.740832e-04 and Welch *t* −8.592553e-03, *p*
9.931455e-01 for `order_parameter_traj`; *d* −8.241057e-04 and *t*
−1.493656e-02, *p* 9.880851e-01 for `mean_phase_coherence_traj`. No
descriptive statistic was undefined, so `undefined_descriptive` is empty for
both metrics and nothing was silently zeroed.

The bootstrap is `prin.y4q1_tools.bootstrap_ci`, 10,000 resamples, α = 0.05,
seed **12455822396014146421** = `Seed(0, 1).next_u64()` — the registered
analysis-stream seed, not the predecessor's 42. Both metrics use that same
deterministic resampling seed and no new RNG was introduced.

**This verdict is narrower than it looks.** H2b concerns only the mean
per-case paired difference of two bounded coherence metrics beyond step 20,
against the **unmodified** PRINet 3.0 reference. It does not establish
equality of the full distributions, equivalence of every regime, a
phase-boundary theorem, or the absence of canceling case-level differences;
the fixed 20-step cutoff is inherited from the original protocol and is not a
newly measured Lyapunov shadowing horizon. It neither implies nor repairs
pointwise agreement inside the horizon — §8 adjudicates H2a and H2b
separately. Per §5.4, 21 of the 22 characterized cases have `n_steps > 20` and
remain eligible H2b contributors; no separate statistical confirmation of that
small subgroup is claimed.

### H3 — CONFIRMED

§8 rule 6: both runs' metadata validate independently; all 14 cases in each
must be byte-identical internally; and the two canonical scientific result
projections must agree after removing **only** `environment`, `config.out_dir`
and any per-run `run_id`.

Both legs carry exactly the 14 registered representatives. Byte identity was
**recomputed from the retained per-array digests** rather than read from
`bit_identical`: `first_array_sha256` and `second_array_sha256` agree on all 11
arrays in all 14 cases in both runs (28 case-runs, 308 array digests), and
each case's `mismatched_arrays` list equals the digest-derived mismatch set.
The two projections are identical, so zero separate-run digest differences —
including every per-array digest, which the projection deliberately retains.

### H4 — CONFIRMED

§8 rule 7: validate both complete 72-case inventories and their per-case
backend proofs separately; one valid breach on either backend refutes (D1);
confirmation requires all 72 non-aborted comparisons on **both** backends.

| Backend | run ID | env backend | dtype | cases | pass | failed elements | max abs | max rel | capsule devices | `backend_name` | extension SHA-256 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CUDA | `RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda` | `cuda` | f32 | 72 | 72 | 0 | 8.977524e-07 | 8.953823e-04 | `cuda` ×3 on all 72 | not recorded (correct: only a wgpu record carries it) | `701bb529…` |
| wgpu | `RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu` | `wgpu` | f32 | 72 | 72 | 0 | 1.345382e-06 | 3.030776e-04 | `cpu` ×3 on all 72 (host-exported, the binding's documented behaviour) | `wgpu<wgsl>` on all 72 | `2f902e80…` |

Both inventories are exactly the 72 `kuramoto_sparse_knn_*` corpus case IDs in
manifest order, with no duplication, substitution or pooling; a CUDA result
was never counted as the wgpu run. Coverage is therefore 2 distinct run IDs, 2
distinct manifest-verified environments and 2 distinct E3 build extension
hashes on the one execution SHA `R`, which is what §8 rule 1 requires for an
admissible H4 analysis. Over each case's worst per-array absolute error the
CUDA leg distributes `1e-7`=72 and the wgpu leg `1e-7`=67, `1e-6`=5. The CUDA
leg's worst absolute error (**8.977524e-07**) sits just inside `atol=1e-6`;
the wgpu leg's (**1.345382e-06**) sits just *above* it and still passes, because
`numpy.isclose(reference, produced, rtol, atol)` admits
`|diff| <= atol + rtol * |produced|` — the relative term uses the **second**
operand, as §1.1 records — rather than `atol` alone, which is exactly why the
registered rule, not a bare absolute bound, is what this analysis checks.
Both legs' relative maxima (**8.953823e-04** CUDA,
**3.030776e-04** wgpu) are well inside `rtol=1e-5`. Zero derivative elements
failed on either backend.

**What E4 did and did not verify here, stated plainly.** The driver retained
comparator records, not the raw float32 derivative arrays, and §8 rule 7
forbids claiming an independent numerical `isclose` re-evaluation from absent
raw arrays or running a new kernel to construct one. No kernel was dispatched
in this session. What was checked is (a) each case's three retained
`dlpack_devices` keys and values, and the wgpu post-dispatch `backend_name`;
(b) each comparator record for internal consistency against the unchanged
`rtol=1e-5, atol=1e-6` rule — `within_tolerance == (failed_count == 0)`, a
reported breach must carry `max_abs_diff > atol` (a necessary condition the
registered `isclose` predicate implies), `total_count` must equal the case's
`n_oscillators`, counts must be ordered and non-negative, and a zero absolute
maximum must force a zero relative maximum; and (c) each case-level
`within_tolerance` against its own three comparator records. `summary.json`
carries `re_evaluated_from_raw_arrays: false` and
`raw_derivative_arrays_retained: false` so no reader can mistake this for a
re-measurement. The live driver had already rejected any wrong export or
backend before publishing each result.

## D1 status (campaign plan §10.4)

**The D1 flag is not raised.** No hypothesis is `REFUTED`, so no C1 conclusion
reversal was detected at E4 and no correction cycle is opened.
`report-manifest.json` records `"d1_flag": false` and
`summary.json` records `"status": "E4 ADJUDICATED — D1 NOT RAISED"`.

Had any valid breach appeared, §8 and §4.1 require escalating it as a D1
rather than rescuing it — no rerun-until-green, altered tolerance, optional
stopping or post-hoc exclusion. The analysis module implements that posture
directly: `is_d1` reports any `REFUTED` verdict, the writers stamp the flag
into every output, and `main` still exits 0 because a refutation is a
scientific result rather than a tool error. Nothing in this session exercised
that path on real evidence; it is covered by the test suite instead.

**Consequence for the campaign block.** E4 detects; it does not release.
Campaign plan §10.4 item 5 keys the release to *E5's* verdict, and the
pre-registration's own closing paragraph repeats that neither a correction
merge, E1 completion nor E2 approval alone releases 0159. Session **0159
(EXP-002 E1), every experiment downstream of EXP-001, and 0194 therefore
remain BLOCKED** until E5 reports this non-reversal result, or the maintainer
records a Project Plan §8.3 amendment.

## Protocol deviations

**PD-1 — `summary.md`'s hypothesis and expected-versus-observed tables are
rendered by the committed analysis module; `prin.reporting` renders the rest.**
Pre-registration §8 asks for `summary.md` to carry those two tables "using
deterministic `prin.reporting` rendering with fixed generation time" and to
"regenerate the tables through `prin.reporting`". This is the same constraint
the predecessor recorded as its PD-1, and it is still not satisfiable as
written for the *hypothesis* table: `prin.reporting`'s aggregators
(`generate_benchmark_report`, `generate_leaderboard`) consume the PRINet 3.0
artefact schema — `status`, `benchmarks`, `test_acc`, `results` — and have no
notion of a pre-registered hypothesis, denominator or verdict. They cannot
emit a hypothesis × verdict × denominator × breach table.

What this session did, rather than only recording the gap:

1. `prin.reporting.generate_benchmark_report` **is** invoked, over the three
   JSON outputs in `DOCS/test_and_benchmark_results/EXP-001-r1/`, with the same
   explicit `generated_at` and no implicit clock. Its render is embedded in
   `summary.md` under "Deterministic `prin.reporting` render (campaign plan
   §7.4 step 3)". Because `summary.json` carries the `status` and `benchmarks`
   fields those aggregators understand, the render is substantive: a real
   Summary table over the three outputs and a per-hypothesis
   name/status list for all five hypotheses. It is not decorative.
2. The two registered tables themselves are produced by
   `analysis/exp001_r1_e4_analysis.py` — the location campaign plan §7.4 item 2
   names for analysis code — under the same determinism guarantees §7.4 step 3
   requires of the `prin.reporting` generators.

**No decision rule, tolerance, denominator, statistic or artefact is
affected.** E5 carries this deviation forward; the frozen pre-registration is
not edited.

**PD-2 — no figures were generated.** §8 states "No new figure is needed for
this parity experiment." Consistent with the registered plan; recorded for
completeness of the deviation list.

**PD-3 — the fuzz leg's sidecar carries `H2`, while §2 and §8 speak of H2a and
H2b.** Not a defect and not an artefact change: campaign plan §7.2's registered
tag set is H1…H4, the driver stamps `_MODE_HYPOTHESIS["fuzz"] = ["H2"]`, and
H2a/H2b are the pre-registration's split of `H2`. Recorded because the first
adjudication attempt failed closed on it, and because §8 rule 1's
"experiment/session identity" check has to be read against the sidecar's own
vocabulary rather than the hypothesis numbering. The analysis now reports both
mappings side by side.

**PD-4 — E4 executed from a linked worktree of the campaign branch, not from
the E3 checkout.** E3 ran in `C:\dev\PRIN-r1-amendment`; this session's
tooling can read that path but cannot run `git` there, so committing the E4
record from it was impossible. A linked worktree was created at
`C:\dev\PRIN\.qwen\worktrees\exp001-r1-e4` on a new branch
`campaign/exp001-r1-e4` based on `campaign/exp001-r1-preexecution` (`541fbfe`),
which matches campaign plan §12 rule 3's per-E-stage branch shape. Three
properties keep this equivalent to analysing from `R`:

- `git diff 5d5ae35 HEAD -- python benchmarks/campaign tools parity crates` is
  **empty**, so every first-party numerical, driver, corpus and tooling source
  the analysis imports is byte-identical to `R`. The commits between `R` and
  the analysis touch only documentation, the append-only `RUN-` artefacts, and
  one DV-044 test annotation.
- The imported `_prin_core.pyd` is the **`R`-built binary**, copied from the E3
  checkout rather than rebuilt, so no `maturin develop` disturbed the shared
  venv's `prin.pth`/`prin_core.pth` or the recorded E3 environment. E4
  dispatches no kernel and re-integrates no trajectory, so the extension is
  used only for `prin.y4q1_tools`' Rust-backed statistics.
- `PYTHONPATH` pinned `prin.__file__` to this worktree's `python/prin`, the
  same discipline §5.1 requires of E3, verified by printing both
  `prin.__file__` and `prin._prin_core.__file__` before the run.

The analysis is bound to its own checkout by construction (the input root is
not a command-line option), and the clean-checkout regeneration below shows the
outputs do not depend on which checkout it ran from. **This is a
working-location deviation, not a scientific one**; E5 should restate it and
the maintainer may prefer to fast-forward `campaign/exp001-r1-preexecution` to
this branch rather than carry two.

No other deviation from the frozen protocol occurred: no hypothesis,
tolerance, seed, denominator or decision rule was changed; no case was
excluded; no unregistered confirmatory test was run; no raw artefact was
mutated; the predecessor's four run directories and EXP-001's record were not
touched.

## Threats to validity

1. **The clamp-trip residual stands as registered.** §4.2's retained validity
   limit: an internal clamp-trip signal is not exposed at the Python boundary,
   so the driver checks the observable envelope and the new amplitude floor but
   cannot claim to observe every derivative clamp event. A clamp trip that
   leaves every checked output finite and in range reaches an ordinary
   `aborted: false` record. Every verdict here inherits that boundary. **E5
   must repeat this limitation, particularly for the 22 characterized cases**,
   as §4.2 directs.
2. **This is a verification of a correction on a known input population, not an
   independent holdout study** (§1). The original experiment's and the
   correction's results were known when the protocol was drafted, and the same
   seed and inputs are deliberately reused. Old outcomes were never used as new
   measurements, but the design cannot detect a defect that only appears on
   inputs outside this population.
3. **Single host, single platform.** All six runs executed on campaign host H1
   (Windows 11, AMD64 Family 25, RTX 4060, 8,188 MiB). §5.1 records H2/H3/H4
   hosted cross-OS runs as optional and unscheduled, so no claim is made that
   these results reproduce on another platform or toolchain. `verify_manifest`
   reproducing every digest from a clean checkout is an artefact-integrity
   result, not a cross-platform numerical one. The native breach count is
   host-dependent and §3 explicitly says it is not an acceptance target.
4. **H2b's scope.** See the note under H2b: a confirmed equivalence of two
   bounded metrics' ensemble means beyond step 20 says nothing about pointwise
   agreement inside the horizon, and does not offset or substitute for H2a.
5. **H4's denominator is the corpus's, not the kernel's.** H4 exhausts the 72
   `kuramoto_sparse_knn_*` corpus cases at `N ≤ 24`. It is not evidence about
   the GPU kernel at larger `N`, other couplings, other models, or the
   mean-field engine. And per §8 rule 7 the E4 check is a consistency check on
   retained comparator records plus the backend proofs — the numerical
   authority for H4 remains E3's live comparison, not this session.
6. **The relative-error statistic is unstable near zero.**
   `compare_arrays` computes `|ref − prod| / (|ref| + 1e-300)`, so an element
   whose reference value is exactly `0.0` divides by the guard alone. That is
   why `fuzz-characterized/native` and `/corrected` report a maximum relative
   error of **1.261799e+300** and the sensitivity stratum **2.365011e+299**
   while their absolute maxima are 6.098203e+00, 4.912669e+00 and
   5.336729e+00. **Read the absolute figures.** The registered pass/fail rule
   uses `numpy.isclose`, which is unaffected; only the reported statistic is.
   `error-distributions.json` carries this caveat in its own `note` field so it
   travels with the data.
7. **N=1 mean-field behaviour, RK45, exponential/Jacobian and single-step
   `_torch_compat` guard differences remain outside this population** (§6), as
   do DV-001, DV-003, DV-036 and DV-040. This experiment closes none of those
   dispositions.
8. **Governance gap in the gate coverage of this analysis code (DV-040).** CI's
   lint job runs `ruff`/`mypy`/`interrogate`/`bandit` over `python/ tests/
   benchmarks/ tools/` only, so a module under the experiment's record root —
   the location campaign plan §7.4 item 2 prescribes — is outside the
   authoritative merge gate. The gates above were run locally and the tests were
   placed under `tests/` so at least the behavioural check is CI-enforced.
   DV-040's re-audit gate is EXP-002 E4 (session 0162); this session is
   additional evidence for it, not a closure.

## Exploratory

Everything below is **exploratory**: not pre-registered, gating nothing,
altering no verdict, and attributing no cause (campaign plan §12.5). It is
recorded because E5 and the Parity Report will want the cross-record picture,
and because §1's "old outcomes are never used as new measurements" means these
comparisons must never be read as r1 evidence.

**E-1. The 19 corpus cases that DV-007 now explains are exactly the 19 that
refuted EXP-001's H1.** The r1 `explained_dv007_case_ids` set and the
predecessor's `failing_case_ids` set are **identical** — same 19 IDs, no
additions on either side — and both distribute over the same four grid cells
(`stuart_landau/full/euler` 10, `stuart_landau/full/rk4` 7,
`kuramoto/mean_field/euler` 1, `kuramoto/mean_field/rk4` 1). The corpus's
native pass/fail partition is therefore unchanged between the two records: the
same 485 cases pass natively and the same 19 do not. What differs is that a
registered, positively-evidenced §5.3 explanation now exists for precisely the
population that previously breached. No mechanism is attributed here.

**E-2. H2a's movement is concentrated in the eligible stratum, and the residual
breaches are all on DV-007 paths.** EXP-001's H2a had 897 passing and 103
failing; all 22 registered ill-conditioned indices were among the failures,
leaving 81 failing eligible cases. r1 has 930 native-parity and 48
explained-dv007 among the 978 eligible, and those 48 indices are a **strict
subset** of the predecessor's 81 — so 33 indices that previously breached
natively now pass natively, and every remaining eligible native breach sits on
a §5.3-eligible path (`stuart_landau/full` 20, `kuramoto/mean_field` 17,
`hopf/mean_field` 11). Describing where the change landed is as far as this
record goes; establishing which correction mechanism produced it was the
correction cycle's job, and §12.5 keeps cause out of an exploratory section.

**E-3. The characterized stratum is concentrated, and mostly long.** The 22
fixed indices distribute as `stuart_landau/full/euler` 15,
`stuart_landau/full/rk4` 2, `hopf/full/euler` 2, `hopf/mean_field/euler` 2,
`hopf/full/rk4` 1; 21 of the 22 have `n_steps > 20` and so remain H2b
contributors, as §5.4 requires. Their native worst-per-case absolute errors
sit in `1e-1`=2 and `1e0`=20 — i.e. these are large-divergence, not
last-place, cases, which is consistent with ill-conditioning rather than with
a tolerance that is merely tight. Ill-conditioning alone is not proof of
chaos, and no such claim is made.

## Outputs and regeneration

Generated deterministically into the gitignored
`DOCS/test_and_benchmark_results/EXP-001-r1/` (campaign plan §7.4 item 4) and
digested in the committed [`report-manifest.json`](report-manifest.json). The
four outputs are §8's fixed set; total generated size 10,506,347 bytes, inside
§9's 64 MiB working-space estimate, and nothing in the tracked tree grew.

| Output | bytes | SHA-256 |
|---|---|---|
| `case-comparisons.json` | 5,897,415 | `9962628f71bdb4013e0f92da3507bd2f87d769016785fad3cc3e48d92559d0e9` |
| `error-distributions.json` | 4,558,744 | `c1d2ed994716001ec542f08d1583f849de66f4fbe5892a3806ad884deec50223` |
| `summary.json` | 36,153 | `dd0240dbfae531b5c1d79e5c22dd05bf4e8912659ec10b16c39884e0abc64292` |
| `summary.md` | 14,037 | `38d8d8e35fdbeebb7488a0c738d6febc7cee8228c592488df5516aca564f7ba5` |

`report-manifest.json` (6,281 bytes,
`906ec394bd0533d17e4c2d2ecf51cb9bf84ac8f6e4374591b2e32ba0dbcd054b`) also
carries each input run's `manifest.json` digest and per-file records, the
per-hypothesis verdicts, the exact denominators, the D1 flag, and `F`/`R`/`M`,
because the generated outputs themselves are gitignored. `case-comparisons.json`
retains all **1,676** registered cases (504 + 978 + 22 + 14 + 14 + 72 + 72)
with every native, corrected and reference-sensitivity comparison record;
`error-distributions.json` retains **14,921** comparator records across the
**9** registered strata, sorted per case and per array.

Regeneration (campaign plan §7.4 step 5) — from a clean checkout of this
session's commit, at the repository root:

```powershell
.venv\Scripts\python.exe "DOCS\experiments\EXP-001-r1-golden-trajectory-numerical-parity\analysis\exp001_r1_e4_analysis.py"
```

Expected stdout:

```
H1: CONFIRMED
H2a: CONFIRMED
H2b: CONFIRMED
H3: CONFIRMED
H4: CONFIRMED
D1 flag: not raised
```

All four output digests must match the table above byte for byte. Passing
`--generated-at` anything other than the registered default changes every
digest and is not a regeneration.

**Clean-checkout verification performed (2026-09-29 UTC, commit `3270699`).**
A detached worktree was created at that commit and the analysis run there,
outside the working tree, with `PYTHONPATH` pinned to that checkout's `python`
directory and the `R`-built `_prin_core.pyd` copied in rather than rebuilt
(PD-4). A first identical check was run at the intermediate commit `f966921`
before the docstring-only `3270699`; both reproduced the same digests.

1. All six r1 raw run directories are manifest-verified **from a clean
   checkout**: `load_run` calls `verify_manifest` on each before reading it, so
   a clean-checkout run that completes has verified all six, and both did. A
   standalone `verify_manifest` loop over the six directories was additionally
   run in the `f966921` clean checkout and passed on each (2 manifested files
   per run) — the `.gitattributes` `benchmarks/results/** -text` rule holds, so
   the committed bytes are the measured bytes.
2. The generator printed the same six stdout lines above and reproduced **all
   four** output digests exactly, and the `report-manifest.json` it wrote is
   byte-identical to the one this record commits (`fc` reported no differences
   across all five files).
3. Three CLI runs in the working worktree, each in a separate process — twice
   before the docstring-only commit and once after it — likewise produced
   identical digests for all five files, confirming that commit changed no
   output byte.

Campaign plan §7.4 step 5 is satisfied: a clean regeneration from the fixed
input index reproduces every digest.

## Handoff to E5

- The E4 exit gate is met: the analysis code and its tests were committed
  before adjudication, every verdict comes from the frozen §8 rule, the outputs
  regenerate deterministically from the fixed six-run index, and
  `report-manifest.json` is committed to the record root.
- E5 reports all five verdicts in full with the expected-versus-observed table
  §3 sets up (already rendered in `summary.md`), PD-1 through PD-4, and the
  eight threats above — **including §4.2's clamp-trip limitation for the 22
  characterized cases, which E5 must repeat**.
- E5 lists each input run and its `manifest.json` digest, and this session's
  `report-manifest.json` digest, in its artefact index (campaign plan §7.4
  item 5). The six input digests are already tabulated in `summary.md`.
- Per §10 item 5, E5 must also list the exact E2-baseline-to-E3-main code diff
  `149cf2d..M` as a protocol deviation, identifying `R` as the experiment's
  distinct source SHA rather than a second mid-experiment main change, and
  report fresh results of **both** 72-case H4 GPU regression legs.
- **The D1 flag is not raised, so this is a non-reversal detection.** E5's
  non-reversal verdict is what releases session 0159, every experiment
  downstream of EXP-001, and 0194 (campaign plan §10.4 item 5). This record
  does not release them, and neither does E4's clean exit.
- No hypothesis verdict, tolerance, denominator or protocol may change at E5;
  corrections to this record are errata (Experimentation Standards §1.3/§4).
- The predecessor EXP-001 record stays as-is. Its H1/H2a `REFUTED` verdicts and
  its own D1 history are **not** revised by this experiment; r1 is a new record
  on a new population of runs, and any statement about the predecessor belongs
  in its erratum pointer, not here.

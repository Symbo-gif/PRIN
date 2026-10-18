# `EVIDENCE/exp002-d1-s4/` — EXP-002 D1 correction, S4 (documentation and closure)

Evidence for the fourth and final session of the `EXP-002-D1` conditional
correction cycle (campaign plan §10.4), executed 2026-10-16 UTC on
`hotfix/exp002-d1-figure-parity`. The governing brief is
[`DOCS/sessions/contingencies/2026-10-14-exp002-d1-s4-correction-documentation.md`](../../DOCS/sessions/contingencies/2026-10-14-exp002-d1-s4-correction-documentation.md);
the closure record is the `## S4 — closure` section of
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../DOCS/audits/2026-10-15-exp002-d1-correction-audit.md);
the Project State Report is
[`DOCS/reports/041-project-state.md`](../../DOCS/reports/041-project-state.md).

S4 is a **documentation-and-evidence** session. It changed **no first-party
source**: the measured change set over `6b55c6ba..157ce5bc` is **29 files, 0
`.rs`, 0 dependency manifests, 0 first-party `.py`, 0 `.github/` workflow
files** ([`gate/change-set.txt`](gate/change-set.txt)). Three conditional gate
legs are therefore not run — by measurement, not convenience.

**Scope discipline.** Windows x86_64 only; **Linux and macOS were not tested
locally** (Plan amendment #48 item 4). Every local result here is a *local*
result and is never described as "CI green". Hosted runs, re-enabled by Plan
amendment #52 during this session, are additional evidence for the exact SHA
they ran on and establish nothing about platforms they did not exercise. No
`EXP-002` verdict, tolerance, digest, protocol or raw artefact was changed;
nothing under `EVIDENCE/exp002-d1-s1/`, `-s2/` or `-s3/` was edited.

## Index

Every committed file in this bundle is listed below. Verify with

```
.venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-d1-s4
```

which must report **0 unindexed and 0 dangling**. That check is run **after**
[`collect_final.sh`](collect_final.sh) copies the records in, and its output is
[`gate/final/index-selfcheck-s4.txt`](gate/final/index-selfcheck-s4.txt) — a
bundle cannot index records that do not exist yet, which is also why
[`final_legs.sh`](final_legs.sh) self-checks only the three pre-existing
bundles. `*.log` is gitignored, so console logs are saved as `.txt`.

### Gate instruments — adapted copies of S3's, not the originals

S3's instruments hard-code S3's ranges, bundle names and scratch paths, so S4
uses **adapted copies** rather than assuming they fit. Every one aggregates
**fail-closed** — by direct `rc=$?` capture, or through the `require_marker`
helper — never by grepping a record. That is the remediation of
[`EXP002D1-S4-F1`](#the-one-confirmed-defect-exp002d1-s4-f1), the defect this
session's own review found in S3's `final_legs.sh`.

| File | What it is |
|---|---|
| [`long_legs.sh`](long_legs.sh) | The two required suite legs. **First measures the change set** and records which conditional legs that triggers, then runs the fast suite and the required full suite **once each**, strictly sequentially (pytest never concurrent with cargo or another pytest, per `AGENTS.md`). Refuses to start on a dirty tracked tree. |
| [`suite_run.sh`](suite_run.sh) | One observed pytest run: the required instrumentation (`--basetemp=.pytest_basetemp`, `-o faulthandler_timeout=300`, `--durations=20`, Git Bash first on `PATH`), a UTC timestamp on every console line, and S3's out-of-process sampler watching host and pytest CPU. Adapted from S3's `diagnostic_suite_run.sh`, scratch root moved to `~/prin-s4-scratch`. |
| [`static_gate.sh`](static_gate.sh) | The static / quality / security / governance legs (Coding Standards §5): `ruff check`, both `ruff format --check` forms, three `mypy --strict` legs, `interrogate`, two `bandit` legs, and the four governance checkers — including `check_deviation_ledger.py` with **report paths** `040` → `041`. |
| [`final_legs.sh`](final_legs.sh) | The cheap legs, run on the **final** documentation commit: the static gate, Sphinx `-W` from a **deleted** `_build`, gitleaks (full history and `--staged`), the immutability diff, the EXP-002 manifest verification, the delta re-audit, the index self-checks of the three pre-existing bundles, the Snyk Code CLI scan, and the PR #34 / branch state. **This is the corrected copy that supersedes S3's `final_legs.sh`.** |
| [`immutability.sh`](immutability.sh) | The five immutability rules for S4's range (§Rules below). Differs from S3's in exactly one place, because closure item 4 *mandates* one append to the EXP-002 record. |
| [`collect_final.sh`](collect_final.sh) | Copies the gate records from scratch (outside the repository) into [`gate/`](gate/). Text records get a provenance header; **`.jsonl` records are copied byte-for-byte** so the sampler record stays parseable. A missing source is counted and reported, never silently skipped. |

### `o2-review/` — the cold review that S3's four-round cap left owing

Observation **O-2** (D4): S3's cold-review loop hit its four-round cap, so round
4's fixes had no further cold review. S4 performed that review **read-only and by
measurement**, reproducing every suspected defect with a command and classifying
it **CONFIRMED / REFUTED / NOT REPRODUCIBLE** exactly as
[`EVIDENCE/exp002-d1-s3/cold-review/triage.md`](../exp002-d1-s3/cold-review/triage.md)
does. Scope: `closing_gate.sh`, `final_legs.sh`, `delta_reaudit.sh`,
`diagnostic_suite_run.sh`, `cold-review/launch_round.sh`,
`docstring_only_check.py`, and the `b08dd574` comment change in
`tests/test_notebooks.py`.

| File | What it is |
|---|---|
| [`o2-review/triage.md`](o2-review/triage.md) | **The review record.** One CONFIRMED defect, twelve checks verifying the round-4 fixes as claimed, one claim REFUTED as a defect, the two invocation errors of the reviewer's own that were corrected rather than left standing, and the protocol notes (read-only on S3's evidence; the one deliberate working-tree edit and its byte-verified restoration; why the optional `devin`/`agy` round was declined). |
| [`o2-review/reproduce-batch1.sh`](o2-review/reproduce-batch1.sh) · [`.txt`](o2-review/reproduce-batch1.txt) | Checks **C1–C12**: `bash -n` on all five scripts; the `diagnostic_suite_run.sh` and `launch_round.sh` argument guards; the `mkdir -p` fix with a stubbed negative control; the `delta_reaudit.sh` trap-order **red/green**; the `closing_gate.sh` aggregation census and a mechanism test of its committed `leg()`; the `wc -l` padding question behind the clean-tree guards; the notebook bound tests; and an independent recomputation of every number the `b08dd574` comment cites. |
| [`o2-review/reproduce-batch2.sh`](o2-review/reproduce-batch2.sh) · [`.txt`](o2-review/reproduce-batch2.txt) | Checks **C6b, C7b, C9b, C13–C15**: batch 1's two malformed invocations redone with resolved hexadecimal revisions; the corrected `closing_gate.sh` census (**11 of 11** legs aggregated); a mechanism test of `final_legs.sh`'s Snyk block against **three stub `snyk` binaries**; bash brace-group variable propagation; and `launch_round.sh`'s exit-status semantics. |
| [`o2-review/reproduce-batch3.sh`](o2-review/reproduce-batch3.sh) · [`.txt`](o2-review/reproduce-batch3.txt) | Checks **C16–C18**: the **non-vacuity** control for `docstring_only_check.py` (exit 1 on the real F6 code change, so batch 2's exit 0 is meaningful); **the reproduction of the CONFIRMED fail-open defect over seven record shapes**; and whether that fail-open bit any committed S3 record. |
| [`o2-review/failopen-red-green.sh`](o2-review/failopen-red-green.sh) · [`.txt`](o2-review/failopen-red-green.txt) | The **red-before / green-after** demonstration §4B requires for a CONFIRMED defect, plus the fail-closed check re-applied to all seven committed S3 final records (**0 failures**, which is what makes the defect *latent*). |

#### The one CONFIRMED defect, `EXP002D1-S4-F1`

`EVIDENCE/exp002-d1-s3/final_legs.sh` aggregates five of its legs with

```
grep -a '^# exit code' "$OUT/x.txt" | grep -qv ': 0$' && overall=1
```

`grep -qv P` exits 0 only if **some** input line does *not* match `P`. With **no**
input lines it exits **1**, so the `&&` arm is skipped: a leg whose record file is
**missing, empty, or holds no marker line** leaves `overall=0` and **reads as
passing**. Proven directly — `echo -n "" | grep -qv ': 0$'` exits 1. It is the
same class round 4 fixed for the Snyk leg alone (S3 triage **T4-2**); the five
grep-aggregated siblings (sphinx, gitleaks, immutability, verify-manifest, the
three index self-checks) were left unchanged.

**Severity D2. Latent, and the latency was measured, not asserted:** re-applying
a fail-closed check to all seven committed S3 records gives **0 failures**, so
**no recorded S3 result was masked** and every S3 leg's real exit code is honestly
present in its record. D2 because the defect is in a *quality-gate aggregator*
and the behaviour it permits contradicts Testing Standards §7 item 6
("Incomplete is not pass") and amendment #48 item 2 (an unavailable control is
"reported as *blocked*, never as passed"); S3's own round-4 reviewers rated the
identical Snyk-leg instance "medium". **D4 was considered and rejected** — it is
not a typo, stale comment or doc gap. The label is about the instrument's design
and is **not** a claim that any S3 result is wrong.

**Disposition: superseded, not edited.** S3's file is untouched (rule I2 below).
[`final_legs.sh`](final_legs.sh) in this bundle replaces the pattern with a
fail-closed `require_marker` helper, and **S4's own gate ran that corrected
copy**, so the fix is exercised rather than merely written.

### `pr34-review/` — adjudication of the external review, and the fix it prompted

The maintainer posted an independent **Perplexity Deep-Research** review of PR #34
and asked that its findings be validated before anything was acted on. Every
checkable claim was **measured** against the real hosted logs, the real PR diff and
the real repository configuration. Result: **4 CONFIRMED, 1 CONFIRMED-in-part, 1
REFUTED (fabricated), 2 recorded without independent verification**; one CONFIRMED
finding (`EXP002D1-S4-F2`, D2) was fixed, and the rest are out of this bounded
correction's scope and are recorded rather than actioned.

| File | What it is |
|---|---|
| [`pr34-review/adjudication.md`](pr34-review/adjudication.md) | **The adjudication record.** Claim-by-claim verdicts with the measurement behind each; the full `EXP002D1-S4-F2` finding (defect, why it is not a PRIN or reference defect, the fix, its four negative controls, why it corrects a false assertion rather than weakening a real one, and the four alternatives rejected); the two harness defects of my own that were corrected rather than left standing; and what was deliberately **not** done, with reasons. |
| [`pr34-review/perplexity-review-verbatim.txt`](pr34-review/perplexity-review-verbatim.txt) | The review as posted, verbatim, so the adjudication can be checked against it. |
| [`pr34-review/adjudication-evidence.txt`](pr34-review/adjudication-evidence.txt) | The measurement pass: hosted run inventory; the nightly full-suite failure; the `rust audit` advisory set; **the real `tests/test_notebooks.py` timeout diff** that refutes the "180 s to 600 s" claim; the parity step-name staleness; and the `importorskip` question. |
| [`pr34-review/failure-identity-and-schema.txt`](pr34-review/failure-identity-and-schema.txt) | Proof that the nightly full-suite's 28 failures are the **same** test the parity job fails, that **all four notebooks PASSED on Linux**, and the E3 record/driver schema showing `environment.platform` is a **required, stored** field — the evidence base for the fix. |
| [`pr34-review/parity-attempt2-failures.txt`](pr34-review/parity-attempt2-failures.txt) | The parity job's failure evidence reduced from its log: summary line, short-test-summary section, and the runner/toolchain (`linux -- Python 3.12.15`, `ubuntu-24.04`, `matplotlib-3.11.2-cp312`). |
| [`pr34-review/bench-regression-rows.txt`](pr34-review/bench-regression-rows.txt) | The full bench-regression comparison table (timestamps and ANSI stripped): **69 rows, 6 advisory, 63 gating, exactly ONE gating row past +10 %** (`engine_step/step_parallel/16384`, +10.4 %). |
| [`pr34-review/pre-decision-investigations.txt`](pr34-review/pre-decision-investigations.txt) | Read-only investigations taken **before** deciding: the bench-regression verdict block, and whether DV-045's governed lockfile-only update is feasible (`cargo update --dry-run` for both crates, `cargo tree -i` for both). |
| [`pr34-review/fix-verification.sh`](pr34-review/fix-verification.sh) · [`.txt`](pr34-review/fix-verification.txt) | Verification of the fix on this host: the unmodified run (**94 passed**), the static gate, and the record of the **two harness bugs** found and fixed in the first attempt. |
| [`pr34-review/negative-controls.sh`](pr34-review/negative-controls.sh) · [`.txt`](pr34-review/negative-controls.txt) | The **four negative controls** proving the platform-scoped digest tie is non-vacuous, including the discriminating pair (the identical corruption **fails** on the authoring platform and **passes** off it) and the control proving the tables were **not** relaxed. |
| [`pr34-review/negctl.py`](pr34-review/negctl.py) | The pytest plugin that drives those controls. Kept **outside** the repository at run time and patching `item.module`, because `parity/` has no `__init__.py` and a `parity.*` import is a *distinct* module object the collected tests never use. |
| [`pr34-review/snyk-code-changed-file.txt`](pr34-review/snyk-code-changed-file.txt) | Snyk Code on the one changed file: **Total issues 0**. This is the applicable SAST control here — `[tool.bandit] exclude_dirs` omits `parity/*`, so `bandit -r parity` scans **0 LOC** and must not be reported as "0 issues". |
| [`pr34-review/billing-lock-diagnosis.txt`](pr34-review/billing-lock-diagnosis.txt) | The account billing-lock diagnosis: every GitHub-hosted job failed in 2–3 s with the annotation *"The job was not started because your account is locked due to a billing issue"*, no runner assigned and no logs. Cleared by the maintainer at ~22:55 UTC. |
| [`pr34-review/hosted-run-triage.txt`](pr34-review/hosted-run-triage.txt) | The first triage of every hosted run on the PR head, before the billing lock was cleared. |
| [`pr34-review/hosted-inventory-final.txt`](pr34-review/hosted-inventory-final.txt) | The final hosted inventory at the PR head **before** the parity fix, including the Node-20 and Ubuntu-26 migration notices that confirm claim 5. |

### `gate/` — the local gate, verbatim

Long legs (the two required suites), run on the documentation commit
`157ce5bc`, strictly sequentially and **before** any hosted workflow was enabled:

| File | What it is |
|---|---|
| [`gate/change-set.txt`](gate/change-set.txt) | The **measured** change set — every path with its `--numstat`, counts by kind, and the resulting decision for each conditional leg (`cargo` not run: 0 `.rs`; `cargo audit`/`pip-audit`/Snyk Open Source not run: 0 manifests; per-change coverage not applicable: 0 first-party Python lines). Conditions are measured, never assumed. |
| [`gate/long-legs.txt`](gate/long-legs.txt) | The two suite legs with verbatim command, UTC start/end and exit code, plus the aggregated `# overall: 0` line. |
| [`gate/fast/run.txt`](gate/fast/run.txt) | The fast suite's identity block: label, `git HEAD`, tracked-change and untracked counts **before and after**, host, logical CPUs, the verbatim pytest command, UTC start/end, and pytest's exit status (**0**). |
| [`gate/fast/console.txt`](gate/fast/console.txt) | The fast suite's full console, every line UTC-timestamped: **4,044 passed, 178 skipped, 55 deselected, 59 warnings in 2,122.53 s (0:35:22)** — the required clean single pass. |
| [`gate/fast/samples.jsonl`](gate/fast/samples.jsonl) | Out-of-process sampler, one JSON object per 30 s (copied byte-for-byte, no header, so it stays parseable). |
| [`gate/fast/sampler-err.txt`](gate/fast/sampler-err.txt) | The sampler's stderr (empty when it ran cleanly). |
| [`gate/full/run.txt`](gate/full/run.txt) | As `fast/run.txt`, for the **required full suite** `pytest tests/ parity/`: started 2026-10-16T19:48:11Z, ended 21:33:57Z, **pytest exit status 0**, tree clean before and after. |
| [`gate/full/console.txt`](gate/full/console.txt) | The full suite's full console, UTC-timestamped: **6,331 passed, 184 skipped, 0 failed, 61 warnings in 6,189.62 s (1:43:09)**, **0** `FAILED`/`ERROR` lines, 5 faulthandler 300 s stack dumps **each followed by a pass** (amendment #49: a dump is not a kill and not proof of a hang), and the slowest-20 durations. |
| [`gate/full/samples.jsonl`](gate/full/samples.jsonl) | The full suite's sampler record — **111 samples**. This is the evidence that the run passed **under heavy contention**: host CPU min 18.3 % / median **96.5 %** / max 99.9 %, **84 of 111** samples at or above 90 %, pytest receiving a median **0.192 CPU-s per wall-second**, with `Devin.exe` (3,845 CPU-s), `mc-fw-host.exe` (2,979), `System` (2,832), `java.exe` (976), `svchost.exe` (804), `AppHelperCap.exe` (255) and `MsMpEng.exe` (98) as the largest non-PRIN consumers. |
| [`gate/full/sampler-err.txt`](gate/full/sampler-err.txt) | The full suite's sampler stderr. |
| [`gate/isolated-rerun.txt`](gate/isolated-rerun.txt) | **Not-applicable record.** Decision 4A provides for a supplementary isolation re-run of a failed node when the full suite fails on a contention flake; the single run exited **0** with 0 `FAILED`/`ERROR` lines, so there was no failed node to re-run. **No rerun-until-green was performed and no result was selected for being favourable.** |
| [`gate/immutability-before.txt`](gate/immutability-before.txt) | Rules I1a–I4 over `6b55c6ba..HEAD`, taken **before** the PSR/audit records were committed. This is also the run that exposed the trailing-blank-line artifact in S4's **own** rule I4; the instrument was corrected, the reason recorded inside it, and **both runs kept** rather than this one discarded. |

### `gate/red-leg-814b670c/` — the RED required leg at the parity-fix commit, and why

The two long-legs tables above record the run at `157ce5bc`, which was **green**.
After that, `814b670c` landed the `EXP002D1-S4-F2` parity fix, and because it
changed a file under `parity/` the required gate had to re-run on the exact
commit being closed. **That re-run is RED**, and it is recorded here in full
rather than being re-run until it went green. `gate/full/` above is the passing
**control** and was deliberately **not** overwritten.

| File | What it is |
|---|---|
| [`gate/red-leg-814b670c/FINDINGS.md`](gate/red-leg-814b670c/FINDINGS.md) | **The findings record.** What failed, the structural proof the change set is not the cause, the measured attribution, why a re-run is not available, the refutation of DV-032's hardening disposition, and the disposition (no merge). |
| [`gate/red-leg-814b670c/run.txt`](gate/red-leg-814b670c/run.txt) | The red leg's identity block: `git HEAD 814b670c…`, the verbatim pytest command, UTC start/end, and **pytest exit status 1**. |
| [`gate/red-leg-814b670c/console.txt`](gate/red-leg-814b670c/console.txt) | The red leg's full console, UTC-timestamped: **1 failed, 6331 passed, 184 skipped in 5613.67 s (1:33:33)**, the `FAILURES` block with `AssertionError: Throughput ratio 22.07 > 1.30`, three faulthandler 300 s dumps each followed by progress, and the slowest-20 durations. |
| [`gate/red-leg-814b670c/long-legs.txt`](gate/red-leg-814b670c/long-legs.txt) | The aggregated legs record: `fast suite exit: 0`, **`full suite exit: 1`**, **`overall: 1`**. |
| [`gate/red-leg-814b670c/samples.jsonl`](gate/red-leg-814b670c/samples.jsonl) | The red leg's sampler record, **108 samples** (byte-for-byte, no header). |
| [`gate/red-leg-814b670c/sampler-err.txt`](gate/red-leg-814b670c/sampler-err.txt) | The red leg's sampler stderr. |
| [`gate/red-leg-814b670c/attribution.txt`](gate/red-leg-814b670c/attribution.txt) | The structural proof: `157ce5bc` is an ancestor of HEAD, `git diff 157ce5bc..HEAD` over `python/ rust/ crates/ Cargo.toml Cargo.lock pyproject.toml tests/` is **empty** (so the test and the daemon it exercises are byte-identical to the version that passed), the full changed-file list, and the failing assertion verbatim. |
| [`gate/red-leg-814b670c/contention_window.py`](gate/red-leg-814b670c/contention_window.py) | The instrument that measures host contention in a named window and across a whole leg. Read-only over a `samples.jsonl`. |
| [`gate/red-leg-814b670c/contention-failing-leg.txt`](gate/red-leg-814b670c/contention-failing-leg.txt) | Contention of the **red** leg: median **96.2 %**, 79/108 samples ≥ 90 %, pytest 0.483 CPU-s/wall-s, and the samples bracketing the 20:28:54–20:29:07Z failure window (97.4 % → 92.4 %). |
| [`gate/red-leg-814b670c/contention-passing-leg.txt`](gate/red-leg-814b670c/contention-passing-leg.txt) | Contention of the **passing control** leg: median **96.5 %**, 84/111 samples ≥ 90 %, pytest 0.422 CPU-s/wall-s. **The control was marginally more contended yet passed** — which is why whole-leg contention is *not* recorded as the cause (§7 item 3). |
| [`gate/isolated-throughput.sh`](gate/isolated-throughput.sh) | The diagnostic that runs the one failing test five times, sampling host CPU before each iteration and recording **every** outcome whether it passes or fails. It does not touch the test or its `<1.30` tolerance (§7 items 6 and 8). |
| [`gate/red-leg-814b670c/isolated/run2-captured.txt`](gate/red-leg-814b670c/isolated/run2-captured.txt) | **Authentic capture**, reproduction #2: host CPU 11.9–24.1 %, test wall time **4.1–4.3 s**, **5 passed / 0 failed**. The quiet-host control. |
| [`gate/red-leg-814b670c/isolated/run1-transcribed.txt`](gate/red-leg-814b670c/isolated/run1-transcribed.txt) | Reproduction #1, a **verbatim transcription** (that execution had no redirection, so no capture file exists — labelled as such rather than passed off as a capture): host CPU 12.2 → **99.7 %**, test wall time 6.7–9.9 s, **3 passed / 2 failed**, measured ratios **2.13** and **3.42**. Retained because it holds the two failing iterations. |
| [`gate/red-leg-814b670c/isolated/run2-iter1.txt`](gate/red-leg-814b670c/isolated/run2-iter1.txt), [`run2-iter2.txt`](gate/red-leg-814b670c/isolated/run2-iter2.txt), [`run2-iter3.txt`](gate/red-leg-814b670c/isolated/run2-iter3.txt), [`run2-iter4.txt`](gate/red-leg-814b670c/isolated/run2-iter4.txt), [`run2-iter5.txt`](gate/red-leg-814b670c/isolated/run2-iter5.txt) | The five per-iteration pytest records behind reproduction #2. |
| [`gate/collect_red_leg.sh`](gate/collect_red_leg.sh) | The collection script that assembled this directory from scratch, including the regeneration of both contention records. |

### `gate/dv032-fix/` — the `EXP002D1-S4-F3` fix that cleared the red leg

The maintainer chose "fix the test properly" over merging on a red gate or
deferring, so DV-032's own registered fix path was implemented for
`test_no_gpu_throughput_regression` (`67100a69`). This directory holds the probes
that shaped the fix, the verification in **both** directions, the measured residual
limitation, and **both** the superseded and corrected runs of each — the first
attempts are the record of two real defects found in the fix and its harness
rather than something to discard.

| File | What it is |
|---|---|
| [`gate/dv032-fix/README.md`](gate/dv032-fix/README.md) | **The nested index for this directory** (36 files), with a one-line description of each. Its [`FIX.md`](gate/dv032-fix/FIX.md) is the narrative record. |
| [`gate/dv032-fix-probe.py`](gate/dv032-fix-probe.py) | The metric probe: four candidate clocks × two host conditions × two daemon arms. Its output showed **no** metric detected the hog, which is what forced a change of *what* is measured. |
| [`gate/dv032-bound-probe.py`](gate/dv032-bound-probe.py) | The bound-sizing probe. Its loaded arm never returned — the drain awaited an unreachable inference count — and that flaw is what produced the corrected drain in the test. |
| [`gate/dv032-tolerance-probe.py`](gate/dv032-tolerance-probe.py) | The tolerance probe whose distribution sized `_DAEMON_CPU_RATIO_LIMIT = 1.60` from the worst observed normal-daemon ratio **1.1429** (Testing Standards §7 item 2). |
| [`gate/verify-dv032-fix.sh`](gate/verify-dv032-fix.sh) | The two-directional verification: static checks, 3 quiet runs, 3 runs on a **saturated** host, and both negative controls. Aggregates fail-closed by direct `rc` capture, per the `EXP002D1-S4-F1` lesson. |
| [`gate/measure-ratio-sensitivity.sh`](gate/measure-ratio-sensitivity.sh) | Measures the ratio bound's sensitivity by forcing the assertion to report its value in both host conditions — how the residual limitation was quantified instead of assumed. |
| [`gate/collect_dv032_fix.sh`](gate/collect_dv032_fix.sh) | The collection script that assembled `gate/dv032-fix/` from scratch, reporting any missing source rather than skipping it silently. |

Cheap legs, run on the **final** documentation commit by
[`final_legs.sh`](final_legs.sh) (each record's header names the commit it ran
on), plus the hosted-workflow enablement listings:

| File | What it is |
|---|---|
| [`gate/final/static-gate.txt`](gate/final/static-gate.txt) | Every static / quality / security / governance leg with its verbatim command, UTC times and exit code, and the aggregated `# overall:` line — `ruff check` "All checks passed!", `ruff format --check` 370 + 3 files already formatted, `mypy --strict` no issues in 62 and 3 source files, `interrogate` **97.6 %**, `bandit` 27,882 and 3,901 LOC with 0 issues, and the four governance checkers including `check_deviation_ledger.py 040 041` → **146 → 159 rows**. |
| [`gate/final/sphinx.txt`](gate/final/sphinx.txt) | `sphinx.cmd.build -W --keep-going -b html` from a **deleted** `DOCS/sphinx/_build` — the clean-build discipline `AGENTS.md` requires, because an incremental build cannot see an `automodule`-sourced docstring change under an unmodified `.rst` page. **build succeeded**, exit 0. |
| [`gate/final/gitleaks.txt`](gate/final/gitleaks.txt) | The pinned, checksum-verified gitleaks 8.30.1 binary over the **full history** and then `--staged`: **776 commits**, ~104.18 MB in 27.9 s, **no leaks found**; `--staged` 0 commits, **no leaks found**. The compensating control for native push protection being disabled (amendment #48 item 6, DV-009). |
| [`gate/final/immutability-after.txt`](gate/final/immutability-after.txt) | Rules I1a–I4 re-run on the **final** commit. |
| [`gate/final/verify-manifest.txt`](gate/final/verify-manifest.txt) | `verify_manifest` over all five `benchmarks/results/EXP-002/RUN-*` records and the frozen input manifest: **`TOTAL FAILURES: 0`**, the input manifest recomputes to the pinned `300cdc09…cce5`, and 172 records PASS — re-proving that the frozen artefacts this cycle must not touch still verify. |
| [`gate/final/delta-reaudit.txt`](gate/final/delta-reaudit.txt) | S3's delta re-audit re-run on the S4 tree: pre-fix digests confirm `e0f59253` and `b41dfc13`; the regression reproduces (**18 failed / 75 passed** and **10 failed**, both exit 1 as required); the module restores byte-identically; post-fix **103 passed**, exit 0; **`# overall: 0`** → `CLEAN`. |
| [`gate/final/index-selfcheck-s1.txt`](gate/final/index-selfcheck-s1.txt) | Index self-check of `EVIDENCE/exp002-d1-s1/`: **12 files, 0 unindexed, 0 dangling**. |
| [`gate/final/index-selfcheck-s2.txt`](gate/final/index-selfcheck-s2.txt) | Index self-check of `EVIDENCE/exp002-d1-s2/`: **30 files, 0 unindexed, 0 dangling**. |
| [`gate/final/index-selfcheck-s3.txt`](gate/final/index-selfcheck-s3.txt) | Index self-check of `EVIDENCE/exp002-d1-s3/`: **129 files, 0 unindexed, 0 dangling**. |
| [`gate/final/index-selfcheck-s4.txt`](gate/final/index-selfcheck-s4.txt) | Index self-check of **this** bundle, run **after** collection so the records it must index exist. Required to report **0 unindexed and 0 dangling**. |
| [`gate/final/snyk-code-s4-final.txt`](gate/final/snyk-code-s4-final.txt) | Snyk Code CLI: `snyk whoami` verified **first** (an expired token gives 401 and no SARIF, which is *blocked*, never *clean*), then `snyk code test . --severity-threshold=low`. Test Summary **Total issues 97, Ignored 0, Open 97 [ 0 HIGH 0 MEDIUM 97 LOW ]** — the authoritative severity breakdown, since the SARIF carries no severity. All **three** ratified `python/PT` locations are visible: `changed_line_coverage.py:98`, `decomposition_rerun_check.py:92`, `snyk_sarif_filter.py:142`. |
| [`gate/final/snyk-console.txt`](gate/final/snyk-console.txt) | The Snyk CLI's own console output. |
| [`gate/final/pr-34.txt`](gate/final/pr-34.txt) | `gh pr view 34 --json state,isDraft,headRefOid`, the fetched `origin` ref, and the ahead/behind counts — the state of PR #34 at the commit the cheap legs ran on. |
| [`gate/workflows-before.txt`](gate/workflows-before.txt) | `gh workflow list --all` **before** enabling anything: all seven check workflows read **`disabled_manually`**, each confirmed individually by `gh api …/actions/workflows/<id>`, with `git status --porcelain -- .github/` and `git diff --stat 6b55c6ba..HEAD -- .github/` both **empty**. |
| [`gate/workflows-after.txt`](gate/workflows-after.txt) | The same capture **after** `gh workflow enable` on each of the seven, under Plan amendment #52. **No file under `.github/` was modified**, so enabling required no workflow edit and no STOP condition was reached. `release.yml` (tag-triggered) and `gpu-triton.yml` (manual-only) are not among the seven and were not touched; no `v*` tag was pushed. |

## Rules this bundle verifies

[`immutability.sh`](immutability.sh) over `6b55c6ba..HEAD`:

| Rule | Requirement |
|---|---|
| **I1a** | The EXP-002 record: the **only** changed file may be `report.md`, and its change must be a **pure append (0 deleted lines)** — closure item 4's erratum and nothing else. |
| **I1b** | `benchmarks/results/EXP-002/`, `.github/`, `Cargo.toml`, `Cargo.lock` and `pyproject.toml` must be **empty**. |
| **I2** | `EVIDENCE/exp002-d1-s1/`, `-s2/` and `-s3/` must be **unedited**. |
| **I3** | The correction audit must be a **pure append (0 deleted lines)**. |
| **I4** | The S4 brief's "Closure checklist" and "Carried from S3" sections must be **byte-identical** to the base; only the Status header lines and the appended completion section may differ. |

Rule I4 normalises **trailing blank lines** before comparing, and says so in its
own output: the base section ends at EOF while the head section ends at the blank
line separating it from the appended section, so an unnormalised comparison
reports a difference the rule does not mean to catch. The first run of the
instrument did exactly that; both runs are kept
([`gate/immutability-before.txt`](gate/immutability-before.txt) shows it) rather
than the earlier one being discarded.

## What this bundle does **not** contain

- **No merge commit SHA and no post-push hosted run results.** `main` is
  PR-only, so a post-merge record cannot be committed here; campaign plan §12
  item 3 assigns the merge SHA and `check_ci_green.py` output to the **next
  governed session**. The listings above record the workflow *enablement state*,
  which was known before the push; run results afterwards are in the session
  report.
- **No experiment output.** S4 ran no experiment, created no `RUN-` directory
  and computed no verdict. `EXP-002-r1` is a record skeleton only.
- **No Snyk SARIF.** It is written to the host's temporary directory and its
  digest recorded; the SARIF itself is kept outside the repository, as S3 did.
- **No `SHA256SUMS.txt`.** This bundle is not hash-frozen (contrast
  `EVIDENCE/ea007/` and `EVIDENCE/0159/`–`0163/`, whose manifests are executed by
  dedicated tests). Its integrity control is the index self-check above.
- **No external cold-review transcripts.** The optional independent `devin`/`agy`
  round was **declined deliberately**, not skipped silently, to avoid loading
  this host immediately before the full-suite leg — the sampler shows `Devin.exe`
  was already the largest non-PRIN CPU consumer during that run. The O-2 review
  is therefore S4's own measurement and is **not** corroborated by an external
  reviewer; that limitation is recorded in
  [`o2-review/triage.md`](o2-review/triage.md) rather than glossed.

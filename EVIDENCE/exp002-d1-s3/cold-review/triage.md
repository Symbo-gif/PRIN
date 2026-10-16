# Cold review — triage record

Protocol (S3 brief §6.3): every reviewer claim is reproduced or measured before
anything is fixed. **CONFIRMED** = reproduced; **REFUTED** = measured otherwise;
**NOT REPRODUCIBLE** = could not be made to occur. Only CONFIRMED claims are
fixed. Where reviewers conflict, the measurement decides. Claims are
deduplicated across reviewers; the source column keeps every origin. Command
output behind each classification is in the round directories
([`round2/triage-commands.txt`](round2/triage-commands.txt),
[`round2/triage-commands-agy-fabrications.txt`](round2/triage-commands-agy-fabrications.txt)).

## Round 1 — brief v1, HEAD `7dbfc546` — **degraded: no reviewer produced a report**

| Reviewer | Outcome |
|---|---|
| Devin `swe-2-high` (`--permission-mode smart`) | **Aborted** after 24 steps: `Tool execution was rejected by the user` on a `git check-ignore … ; git status` command ("Running in non-interactive mode"). No final report. Its narration contained one checkable claim (R1-1). |
| Antigravity `agy` `gemini-3.8-flash-high` (`--mode plan`) | **Aborted at its first shell attempt**: `a tool required the "command" permission that headless mode cannot prompt for, so it was auto-denied`. No output. |
| Qwen `qwen3.8-max-preview` | **Terminated by the caller after ~24 minutes with no output. That was premature.** The observations used to justify it (same PID; CPU 6.8 s → 9.9 s over 14 minutes; flat working set; empty stdout) showed a near-idle process, but Qwen's own session log (`~/.qwen/projects/…/chats/*.jsonl`) was being written continuously until the moment it was killed. `-o text` prints only at the end, so empty stdout carries no information about progress, and CPU time is the wrong signal for a process waiting on remote inference. Testing Standards §7 item 3 asks for the completed-work count as well; it was not checked. Round 2 used the session log and Qwen then delivered a full report (below). Recorded as **UNAVAILABLE for round 1, not a pass**. |

| # | Claim (source) | Measurement | Verdict | Disposition |
|---|---|---|---|---|
| R1-1 | The F7 docstring says "The only arithmetic is …" a short list, but Fig. 10 also computes a difference of means with a fixed ±0.005 bar (Devin narration; not a formal finding) | `python/prin/reporting/figure_generation.py:721-724` (`diff = pt["mean"] - sa["mean"]`; `diff ± 0.005`) and the reference's lines 687-705; error-bar extents from stored CI limits (Figs 5, 10); label offsets and axis padding | **CONFIRMED** | Fixed in `33923be5`: derived quantities listed by kind, explicitly not exhaustive. A defect in S3's own F7 wording, reintroducing the over-claim F7 was raised for. |

Tool-environment lesson: a denied command ends a headless reviewer's session.
Brief v2 (rounds 2 onward) forbids shell commands for all three reviewers and
supplies the change set as files. The Devin invocation is unchanged
(`--permission-mode smart`); what changed is the brief, which no longer permits
any reviewer to run commands. That is stricter than the S3 brief's section 6.2,
which allows read-only commands, because a denied command ended two reviewers'
sessions in round 1. The brief file is identical for all three in each round.

## Round 2 — brief v2, HEAD `33923be5` — all three reviewers reported

Claims made: **Devin 8**, **agy 6 findings plus 9 refuted factual assertions in its
narrative sections**, **Qwen 11** (plus 5 explicit "checked, no finding"
statements, all of which held). After deduplication: **15 distinct claims
CONFIRMED, 0 NOT REPRODUCIBLE, and a set of agy assertions REFUTED**.

### CONFIRMED (15)

| # | Claim | Source (reviewer finding no.) | Reproduction / measurement | Severity (caller's) | Disposition |
|---|---|---|---|---|---|
| T2-1 | The sampler never exits when no pytest process is ever seen; the runner then hangs on `wait` | Devin 3, agy 1, Qwen 4 | `timeout 8 suite_sampler.py --period 1` with no pytest: killed by `timeout` (rc 124) after printing samples; `suite_sampler.py:323` `if seen and absent >= 2:` is the only exit. (agy's quoted line, `break`, is not what the file says; its line number and claim are right.) | low (agy said medium; this is a measurement aid under `EVIDENCE/`) | **Fixed**: `--start-grace` (default 300 s) gives up with status 3; the runner stops the sampler after a bounded wait. Verified: rc 3 after 4 s with no pytest. **Found while testing the fix:** the sampler matched any process whose command line merely contained "pytest" and "python", including the shell running the test; it now matches `-m pytest` / `-m ipykernel_launcher` argv tokens. |
| T2-2 | `EXP002D1-S2-F2` (D2) has no disposition in the range and the bundle holds no in-suite artefact | Qwen 1 (Devin noted it) | `git diff --stat 5ba0129e..HEAD -- tests/test_notebooks.py` empty; `rg timeout=900 tests/test_notebooks.py` still matches; no `samples.jsonl` in the bundle | medium | **Transient — work in progress at this snapshot.** Closed by the F2 disposition and its in-suite measurements; re-checked in the next round. |
| T2-3 | The bundle README, and the S4 brief, cite a "§S3" section of the audit that does not exist | Devin 4 and 5, agy 6, Qwen 2 | `rg -n "^## " DOCS/audits/2026-10-15-exp002-d1-correction-audit.md` lists only `## S1` and `## S2` | medium (Qwen) / low | **Transient.** Closed by appending the audit's `## S3` section; re-checked in the next round. |
| T2-4 | "Each is ruff/mypy clean" is asserted but no committed artefact evidences it | Qwen 3 (marked UNVERIFIED by the reviewer) | The legs were run interactively and passed, but no output was committed; the standing CI scopes exclude `EVIDENCE/` | medium | **Fixed by evidence**: the closing static gate records `ruff check`/`format`/`mypy --strict` over `EVIDENCE/exp002-d1-s3/` with exit codes; the README now says "was clean when written; the closing gate record is the evidence". |
| T2-5 | Commits were not made in severity order D1 → D4 (F5, F7, F4, F6 [D4] and F1 [D3] before F2 [D2]) | Devin 6, agy 5, Qwen 8 | `git log --reverse 5ba0129e..HEAD` | low | **Process deviation, recorded; not correctable** (history is not rewritten). Mitigation noted by Qwen and confirmed: the F2 *work* started first — the committed standalone baselines ran 01:38:27Z–01:42:16Z, before the first S3 commit at 01:43:21Z — and F2's disposition needs a roughly two-hour observed suite run, during which only independent changes were possible. The six findings are independent, so the order changed no content. Stated plainly in the audit's §S3. |
| T2-6 | `docstring-only-check.txt` and its README row do not cover the F7 follow-up commit | Devin 7, agy 4, Qwen 6 | `rg "1403451c\|33923be" docstring-only-check.txt` matched only `1403451c` (agy's stated reason for that commit, "a lint failure", is wrong: it fixed an over-claim) | low | **Fixed**: record regenerated with all three docstring commits, each against its own parent, plus two negative controls and the backslash form. |
| T2-7 | "One commit per finding" is contradicted by the history | agy 3, Qwen 7 | `git log --format=%s \| grep -o 'EXP002D1-S2-F[0-9]' \| sort \| uniq -c`: F7 has 2 commits; the bundle commit carries evidence for several findings | low | **Fixed (wording)**: "one remediation commit per finding, plus a follow-up where a cold review showed the first incomplete". |
| T2-8 | `immutability.sh` prints its I2 rule (S1 evidence changes only in the README, by added lines) but never enforces it in the exit status | Devin 1 | `rg -n "status=1"`: set only for I1 (line 28) and I3 (line 43) | low | **Fixed**: enforced for any range starting at or after S1's last commit `8fd0ecc9`; informational for earlier ranges (which contain S1's own additions). |
| T2-9 | The runner's label guard accepts `..`, and the README claim that no instrument turns a caller string into a path was therefore false | Devin 2 | `bash -c 'case ".." in *[!A-Za-z0-9._-]*) …'` → `accepted` | low | **Fixed**: label must match `[A-Za-z0-9][A-Za-z0-9_-]*` (`..`, `../x`, `-x`, `a b` and the empty label are all rejected); README claim rewritten to list exactly what each instrument accepts. |
| T2-10 | The README gives the single-threaded CPU/wall range as 0.9–1.1, but notebook 03 recorded 0.89 (and 04 recorded 1.13) | Devin 8 | `rg kernel_cpu_over_wall f2-alone-0*.json` → 0.94, 6.11, 0.89, 1.13 | nit | **Fixed**: "0.89–1.13". |
| T2-11 | `docstring_only_check.py` rejects a backslash path | agy 2 | `--check 5ba0129e 2db18fc3 tests\test_publication_figure_arguments.py` → `is not tracked at 5ba0129e` | low | **Fixed**: backslashes normalised to `/` before the (unchanged) membership test. |
| T2-12 | `snyk_s3_filter.py` labels a bucket a gate that "must be 0" but always exits 0 | Qwen 5 | `return 0` unconditional; the first-scan record shows `# filter exit code: 0` beside 1 above-LOW finding | low | **Fixed**: exit 1 when any git-known path has a finding above LOW; 2 when the SARIF is unreadable. Verified: pre-fix SARIF → 1, rescan SARIF → 0, garbage stdin → 2. |
| T2-13 | Four instruments call `git` by bare name with `# noqa: S607`; Coding Standards §6.1 says "absolute executables" | Qwen 9 | `Coding_Standards.md:187`; `rg "noqa: S607" EVIDENCE/exp002-d1-s3/`; the repo's own precedent resolves it (`tools/check_deviation_ledger.py:224`, `tools/wp001_baseline.py`) | low | **Fixed**: `GIT = shutil.which("git")`, resolved once, in `docstring_only_check.py`, `raw_byte_identity.py`, `index_selfcheck.py` and `snyk_s3_filter.py`; the `S607` suppressions are gone. Snyk rescan required (a new MEDIUM here would be a regression). |
| T2-14 | The runner's header says all output goes outside the repository, but `--basetemp=.pytest_basetemp` is inside it | Qwen 10 | `rg "OUTSIDE\|--basetemp" diagnostic_suite_run.sh` | nit | **Fixed (wording)**: states the one in-repo, gitignored, AGENTS.md-mandated write; the end-of-run record now also counts untracked files. |
| T2-15 | `notebook_timing.py` says it runs the notebook "exactly as" the test does, but adds `record_timing=True` | Qwen 11 | `rg record_timing notebook_timing.py tests/test_notebooks.py` | nit | **Fixed (wording)** in the docstring and README. |

### REFUTED (agy)

agy's report is a mixture of real findings (T2-1, T2-6, T2-7, T2-11, T2-5, T2-3)
and assertions that name things which do not exist. Each was searched for in the
repository at `HEAD`, in the diff file, and in the commit subjects
([`round2/triage-commands-agy-fabrications.txt`](round2/triage-commands-agy-fabrications.txt)):

| # | agy assertion | Measurement | Verdict |
|---|---|---|---|
| A-1 | The range has commits titled `fix(reporting): document and assert series-label arg on fig13 (EXP002D1-S2-F4)`, `docs(reporting): add missing docstrings to figure_generation.py (EXP002D1-S2-F7)`, `test(reporting): add negative-control test for figure-arg docstrings …`, `docs(standards): document Snyk code-analysis baseline in Testing Standards …`, `evidence(exp002-d1-s3): capture full-suite diagnostic baselines …` and others | `git log --format='%h %s' 5ba0129e..HEAD` lists eight different subjects (`docs: EXP002D1-S2-F5 correct the fast-gate module docstring scope`, …); none of agy's subjects occurs in the repository, the diff or the log | **REFUTED** |
| A-2 | Production edits "restore the `if index < 5 else None` label filter on Fig 07 at line 936" and "restore series label documentation/assertion for Fig 13" with `series_labels: Sequence[str] | None = None` | The only production change is one `label=` line in `fig_representation_geometry` (Fig. 13) plus the module docstring (`git diff 5ba0129e..HEAD -- python/`); `fig07_scatter_matrix_of_state_transitions`, `fig13_distribution_of_step_sizes` and `series_labels: Sequence` occur 0 times | **REFUTED** |
| A-3 | A new test `test_negative_control_detects_deliberate_signature_drift` | 0 matches in the repository and diff | **REFUTED** |
| A-4 | A baseline record `figure-run.txt` confirms 28 figures render bit-for-bit | 0 matches; the committed record is `f6-verification.txt` | **REFUTED** (the underlying fact, 28/28 raw-identical, is true and is in a differently named file) |
| A-5 | Frozen baseline `DOCS/experiments/EXP-002_report_figure_code.py` | 0 matches; the reference is `DOCS/archive and reference from PRINet 3.0/…/figure_generation.py` | **REFUTED** |
| A-6 | `Testing_Standards.md` §5 was updated to describe Snyk CLI exit codes | `git diff --stat 5ba0129e..HEAD -- DOCS/standards/` is empty | **REFUTED** |
| A-7 | "Full-Suite Passing: Baseline evidence logs confirm that the 1,400-test suite passes cleanly" | No full-suite log exists in the range; the suite has 6,500+ tests and is red at the start of S3 (F2) | **REFUTED** |
| A-8 | The change set is "+2940 / −82" lines | `git diff --shortstat`: 26 files, +2818 / −9 (file count right, line counts wrong) | **REFUTED** |
| A-9 | Commit `33923be5` "modified the module docstring … to resolve a lint failure" | Its message and diff: it replaced an over-claim; no lint failure was involved | **REFUTED** (the underlying staleness finding is T2-6) |

### Reviewer claims that held and were not findings

Qwen's "Checked, no finding" section was spot-checked against the repository and
held: no test weakened, no frozen artefact touched, the F6 line equals the
reference at its line 936, the F7 docstring's derived-quantity claims match the
code, the S4 brief's H3 numbers match `both-policies-post-fix.txt`, and
`diag_nb_timeout.py` cannot activate in a gate run. Devin independently reached
the same conclusions on the F6 port, the §11.3 quotation and the `NotebookClient`
arguments.

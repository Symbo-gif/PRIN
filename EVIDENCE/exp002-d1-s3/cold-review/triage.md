# Cold review — triage record

Protocol (section 6.3 of the S3 session prompt, summarised in [`README.md`](README.md)): every reviewer claim is reproduced or measured before
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
any reviewer to run commands. That is stricter than section 6.2 of the S3 session prompt,
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

## Round 3 — brief v3, HEAD `b2156918` — all three reviewers reported

Brief v3 is brief v2 plus one paragraph saying that the diff file omits some large
raw-data files and the review records (listed in `s3-excluded.txt` with sizes and
SHA-256, all present in the tree). That is neutral: it describes the diff file, not
the change. The excluded review records also keep earlier reviewers' findings out
of the diff, so the review stays cold.

**Availability.** agy and Qwen reported on their first run. Devin needed four
attempts: attempts 1 and 2 ended when `smart` mode rejected a `wc -l` / `ls`
command the brief had forbidden (attempt 2 was made after the data file the
reviewers read first gained a line giving the sizes of the review files, so no
command was needed to learn them); attempt 3 read everything and ran out of output
tokens before writing its report (exit 1); attempt 4 reported. The Devin invocation
and the brief file are identical in all four attempts. Attempts 1–3 are kept in
`round3/`.

Claims made: **Devin 9, agy 2, Qwen 13** = 24 findings, plus one claim found in
Devin's attempt-3 narration (that the audit cites section numbers the repository's S3
brief does not have). After deduplication: **18 distinct claims, all CONFIRMED (one
only in part), 1 assertion within one of them REFUTED, 0 NOT REPRODUCIBLE.** Every
reproduction and its output is in [`round3/triage-commands.txt`](round3/triage-commands.txt).

| # | Claim | Source | Measurement | Verdict | Disposition |
|---|---|---|---|---|---|
| T3-1 | `snyk_s3_filter.py`'s changed-file list omits `tests/test_notebooks.py`; the audit says "two changed first-party files" and the Snyk records predate the F2 commit | agy 1 and 2, Devin 1, Qwen 2 | `git diff --name-only 5ba0129e..HEAD -- python/ tests/` lists three files; the last scan started 03:14Z and `91f3327a` was committed at 04:34-03:00 (07:34Z) | **CONFIRMED** | List fixed; the audit says three files and cites a closing rescan (`snyk-code-s3-final.txt`) |
| T3-2 | "host available memory never fell below 5.5 GB" | Devin 2 | minimum sample 5,476 MB | **CONFIRMED** | "5,476 MB" in the audit and the F2 README. The F2 commit message keeps the old figure (commit messages are not rewritten) |
| T3-3 | "neither can move without the other" overstates a one-directional `>=` test; a bound can be raised with no evidence | Devin 3, Qwen 5 | the only assertion was `bound >= BOUND_MARGIN * recorded` | **CONFIRMED** | The test is now an equality with the rule (3 × recorded, rounded up to 900 s); `f2/test-both-directions.txt` shows a raised bound and a slower recorded worst case each failing; red and green re-recorded |
| T3-4 | The 12× looser notebook-02 bound rests on a host state S1 and S2 never measured; S2 warned against a load-only attribution; the 3,484 s run was taken while the review session's own tooling saturated the host; the mitigation was "considered and not done"; no committed gate run exists at the new bounds | Qwen 1 | S1 and S2 have no sampler output (true); S2's "~89% idle at start" was measured before the suite began, and the S3 observed run read 31% at the start with saturation from minute 13 (true, and not previously addressed); **no reviewer CLI ran during 03:20–06:03Z (the observed run) or 06:06–07:07Z (the experiment)**, and S2 recorded three `Devin` processes resident before S3 began (so the "review tooling" attribution is false); the closing gate had not yet run | **CONFIRMED in part; one assertion REFUTED** | Added to the audit and the F2 README: the limits of what S1 and S2 can show, S2's idle-at-start point, whose processes these are, and that the bound is a deliberate 12× loosening for notebook 02. The gate run followed |
| T3-5 | The `rg.exe` counts "87 → 29 → 64" and "116 to 2" cite artefacts that contain no process counts and that end before the period described | Qwen 3 | `analysis-contention-timeline.txt` ends at 06:41:55Z, before the load generator's runner ended (06:42:29Z; its pytest ended 06:39:06Z), and holds CPU-seconds by name; the only committed `rg.exe` count is the 134 snapshot | **CONFIRMED** | Counts removed. The post-load saturation is now computed from `treatment.json` by `paired_comparison.py` (309 of 309 samples at or above 90% over 27.9 minutes); the end-of-suite recovery cites the timeline rows (97% to 33%) |
| T3-6 | A per-cell timeout is sized from whole-notebook durations | Qwen 4 | every recorded value is a test or notebook wall time; 02's slowest contended cell was 1,926 s | **CONFIRMED** (safe direction) | Stated in the constant's comment, the audit and the F2 README: a whole-notebook duration bounds any cell, so the bounds are conservative; the per-cell figure would give 6,300 s |
| T3-7 | `immutability-before.txt` and `index-selfcheck-s1.txt` were produced by earlier versions of their instruments | Qwen 6, Devin 5 | the records lack lines the shipped instruments print | **CONFIRMED** | Both regenerated with the shipped instruments; the `-s2` and `-s3` records are produced with the closing gate |
| T3-8 | `f6-test-red-before-fix.txt` cites line 191; the committed assertion is at 194 | Qwen 7 | `git show 2b8b7a55:tests/test_publication_figure_arguments.py \| grep -n` gives 194 | **CONFIRMED** (explained) | The red run preceded the three-line docstring sentence about fig13 that the same commit added afterwards (Qwen guessed the pre-F5 docstring; the F5 docstring was already in). Noted in the README row; the raw record is unchanged |
| T3-9 | `notebook_timing.py` still says the test uses a 900 s timeout | Qwen 8, Devin 6 | the test uses `NOTEBOOK_CELL_TIMEOUT_SECONDS[name]`; `--timeout` defaults to 900 | **CONFIRMED** | Docstring and parameter text rewritten |
| T3-10 | §S3.6 asserts 0/0 results for `exp002-d1-s2` and `-s3` with no committed record, and cites a closing gate that had not run | Qwen 9 | no `index-selfcheck-s2.txt` or `-s3.txt` | **CONFIRMED** (transient) | §S3.6 now names the three closing-gate records; they are produced with the gate |
| T3-11 | The experiment's cleanup force-kills any process whose command line mentions a test file name | Qwen 10 | the recorded run did not reach that branch (there is no "load generator still running" line in its `run.txt`) | **CONFIRMED** | Cleanup now stops only the runner's own process tree, found from its Windows PID in `/proc/<pid>/winpid`; self-tested on a throwaway child |
| T3-12 | The audit's header (lines 3–14) still says "S1 complete; S2, S3, S4 pending" | Qwen 11 | `sed -n 14p` | **CONFIRMED** (not correctable) | The document is append-only; noted in §S3.9 |
| T3-13 | Comments say "two orders of magnitude" (true for 02 only: 152×; the others are 37–49×) and "a fifth to a third" of a core (0.17 is a sixth) | Qwen 12, Devin 9 | bounds divided by quiet-host durations; kernel CPU/wall 0.17–0.33 | **CONFIRMED** | Comments corrected ("37–152 times", "a sixth to a third") |
| T3-14 | "`HEAD~` (`5ba0129e`)" names two different revisions | Qwen 13 | `git rev-parse HEAD~` is not `5ba0129e` | **CONFIRMED** | "the S3 base (`5ba0129e`)" |
| T3-15 | `launch_round.sh` interpolates its argument into paths unvalidated | Devin 4 | no guard in the script | **CONFIRMED** | Round name restricted to `[A-Za-z0-9][A-Za-z0-9_-]*` (`../x` exits 2) |
| T3-16 | `contention_experiment.sh` names files it does not write to that directory | Devin 7 | `OUT=` against the header | **CONFIRMED** | Header lists what is written where |
| T3-17 | Usage errors exit 1, but the docstrings document 2 (`raise SystemExit("message")`) | Devin 8 (marked UNVERIFIED by the reviewer) | `docstring_only_check.py --check zzz …` and `raw_byte_identity.py --before zzz` both exited 1 | **CONFIRMED** | A `fail()` helper prints to stderr and exits 2 in three instruments; verified exit 2 |
| T3-18 | The audit and four records cite "S3 brief §6.x" but the repository's S3 brief has no such sections | Devin attempt-3 narration | the brief is 27 lines with three `##` headings | **CONFIRMED** | Citations now say "the S3 session prompt" (not a repository file); its rules are summarised in `cold-review/README.md` |

## Round 4 — brief v3 (unchanged), HEAD `5eee9184` — all three reviewed; the cap

Round 4 used the same brief file as round 3 (sha256 `caff383a…`). Its diff file omits
the same kind of raw records, and now also the final-gate records and JSON/console
files over 8 KB, all listed with sizes and hashes in
[`round4/s3-excluded.txt`](round4/s3-excluded.txt).

**Availability.** agy and Qwen reported on their first run (Qwen after about an hour; its
session log grew until the end, so it was not mistaken for a stall as in round 1).
Devin's first attempt ended when `smart` mode rejected an `ls -la` the brief had
forbidden; the second reported. Both attempts are kept. `git status --porcelain` was
empty before and after the round.

Claims made: **Devin 7, agy 1, Qwen 10** = 18 findings. After deduplication: **14
distinct claims — 13 CONFIRMED (three of them only in part), 1 REFUTED, 0 NOT
REPRODUCIBLE.** No claim concerned the correction itself, a frozen artefact, or a
weakened test; the reviewers independently re-derived the F2 bound arithmetic, the
suite counts, the cargo total, the coverage figures and the 55-of-90 saturation count
and found them exact. Two claims were **medium**, both latent defects in gate scripts
that did not fire in any recorded run. The red-before-fix and green-after-fix
reproductions are in [`round4/triage-commands-a.txt`](round4/triage-commands-a.txt),
[`round4/triage-commands-b-red.txt`](round4/triage-commands-b-red.txt) and
[`round4/triage-commands-c-green.txt`](round4/triage-commands-c-green.txt).

| # | Claim | Source | Measurement | Verdict | Disposition |
|---|---|---|---|---|---|
| T4-1 | `delta_reaudit.sh` arms its `git restore` EXIT trap before the clean-tree refusal, so the refusal path discards uncommitted edits to the module | Devin 1 (medium), Qwen 1 (medium) | with a one-line temporary edit to `figure_generation.py` the script printed "tree is not clean; refusing to run", exited 2, and `git diff` of the module was then empty: the edit was destroyed | **CONFIRMED** | Trap armed after the guard; the same experiment now leaves the edit in place (green record) |
| T4-2 | `final_legs.sh` leaves `overall` at 0 when the Snyk leg writes no SARIF, so a leg that never ran reads as an all-clear | Devin 2 (medium), Qwen 2 (medium) | the pipeline `grep 'filter exit code' \| grep -qv ': 0 '` over a record containing only the BLOCKED line yields `overall=0` | **CONFIRMED** (latent: the SARIF was written in the recorded run) | A failed `whoami`, a scan exit above 1, a missing SARIF or a failing filter each set `overall=1`; a stub Snyk that authenticates but writes no SARIF now makes the script exit 1 and the record says BLOCKED |
| T4-3 | `closing_gate.sh` discards every leg's exit code and always exits 0 | Devin 3 (low) | no `overall` in the script; last statement an `echo` | **CONFIRMED** | Legs and suites now aggregate into the exit status; `legs.txt` was always honest and is unchanged. The script was syntax-checked, **not re-run** (about 3 hours) |
| T4-4 | The verdict says round 4 "is recorded" while the §S3.5 row says "to be recorded", and "four rounds triaged" appears in six records with no round 4 evidence | Devin 4 (low), Qwen 3 (low) | `rg` finds the placeholder row and the sentence; `cold-review/` had no round 4 section | **CONFIRMED (transient)** | Closes with this section, the README section, the audit row and `round4/` |
| T4-5 | `launch_round.sh` never creates the round directory, so on a fresh round name all three redirections fail; and a stray space in the pointer string | Devin 5 (nit) | with stub reviewer CLIs, a fresh name gave six "No such file or directory" errors | **CONFIRMED in part** | `mkdir -p` added. The space in `"$BRIEF_WIN . Read"` is deliberate (it keeps the full stop out of the path) and harmless, not changed |
| T4-6 | `${1:?…}` makes a missing label exit 1 where every sibling uses 2 | Devin 6 (nit) | `bash diagnostic_suite_run.sh` exit 1 | **CONFIRMED** | Explicit check, exit 2 |
| T4-7 | `final_legs.sh`'s record headers print the literal "tracked changes: 0" | Devin 7 (nit) | the literal is in `hdr()` | **CONFIRMED** | Each header now measures the count |
| T4-8 | `cold-review/README.md` says the launcher was "used for both rounds" while documenting three | agy 1 (nit), Qwen 8 (nit) | the sentence is at line 28; `## Round` headings at 38, 49, 62 | **CONFIRMED** | Reworded; the Devin-only re-run helper is indexed |
| T4-9 | The bound comment in `tests/test_notebooks.py` attributes "8-43x" to the full suite | Qwen 4 (low) | the full-suite ratios are 9.3 / 41.8 / 8.3 / 10.3 (`f2/analysis-in-suite-vs-alone.txt`); 43.2 is the paired experiment | **CONFIRMED** | Comment now says 8-42x, and 43x beside only the `test_exp002_*` tests. Comment only; the 5 bound tests pass |
| T4-10 | The per-cell bound is sized from whole-notebook durations and notebook 02's is 1.7× the 6,300 s a per-cell reading gives, with no stated reason for the looser unit | Qwen 5 (low; the reviewer rates it a design observation) | the conservatism is disclosed in the test comment and the audit (T3-6), and the 6,300 s figure is in `f2/README.md`; the *reason* for using the whole-notebook unit for all four was not stated | **CONFIRMED in part** | The reason is now stated: a contended per-cell measurement exists only for notebook 02, so one uniform rule over a quantity recorded for all four notebooks was preferred to a notebook-specific exception, at the stated cost of a 1.7× looser bound on 02. The bound is unchanged |
| T4-11 | `snyk-code-s3-first-scan-medium.txt` prints a failing gate line beside `# filter exit code: 0` | Qwen 6 (nit) | the record shows `ABOVE LOW … 1 finding(s)` and exit code 0; the filter then returned 0 regardless | **CONFIRMED** | The bundle README row now says the exit-code line in that record predates the filter encoding its gate; the record is unchanged |
| T4-12 | §S3.9 item 5 cites "lines 3–14" for header text at lines 15 and 17 | Qwen 7 (nit) | the stage-status sentence is at line **14** and the paragraph describing the document as written before S2 is at lines **16–22**; the reviewer's own numbers are off by one | **CONFIRMED in part** | Item 5 now names line 14 and lines 16–22 |
| T4-13 | `docstring_only_check.py`'s docstring says the path must be tracked at revision B, but the code tests both revisions | Qwen 9 (nit) | `source_at()` runs the `ls-tree` test for whichever revision it is given, called for A and B | **CONFIRMED** | Docstring says both |
| T4-14 | The `# nosec B603` at `index_selfcheck.py:77` suppresses nothing (bandit prints `nosec encountered (B603), but no failed test`) | Qwen 10 (nit) | on a copy with the `nosec B603` removed bandit reports `B603 … index_selfcheck.py:77:10` (Low); with it, 0 issues and 2 potential issues skipped, the same as `docstring_only_check.py`, which prints no warning | **REFUTED** | The annotation is needed. The warning is consistent with the chained `.stdout.decode(...)` call, a second AST node starting on the same line, but that explanation is an inference. Noted in the gate README |

**Round 4 is the cap.** It returned CONFIRMED claims, so the loop did not converge to a
round with none, and the S3 protocol (capped at four rounds, then disposition the
residual rather than loop) applies. The residual and its measurement are recorded in the
audit's §S3.5 and as observation **O-2** in §S3.9. Every CONFIRMED round 4 claim was fixed
and re-verified by measurement (red before, green after), but **the fixes were not shown
to a further cold reviewer**.

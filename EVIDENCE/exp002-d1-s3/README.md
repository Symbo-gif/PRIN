# EXP-002 D1 correction — S3 evidence

Status: **complete** (S3, 2026-10-16 UTC). This directory holds the
evidence behind the S3 remediation record, which is the `## S3 — remediation and
delta verification` section of
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../DOCS/audits/2026-10-15-exp002-d1-correction-audit.md).
It is indexed here file by file; `index_selfcheck.py` checks that mechanically.

S3 works only on S2's findings (`EXP002D1-S2-F1`…`-F8`), with one remediation
commit per finding (plus a follow-up commit where a cold review showed the first
one incomplete, as for F7; this bundle's instruments and records are committed
separately), and does not push (Plan amendment #28: the cycle's push point is S4). Every
executable here ran from the repository root on the Windows host, Python 3.14.0,
project venv, from Git Bash with `C:\Program Files\Git\bin` first on `PATH`.
Windows x86_64 only — Linux and macOS were **not** tested (Plan amendment #48).

## Instruments

Each was `ruff check`, `ruff format --check` and `mypy --strict` clean when it
was written; the closing gate's `static-gate.txt` is the
committed evidence for that. None turns a caller-supplied string into a filesystem
path: they take a name from a closed set, a hexadecimal revision, a run label
restricted to `[A-Za-z0-9][A-Za-z0-9_-]*`, a tracked file name that is only
handed to `git show REV:PATH` after a membership test, or standard input. Every
Python subprocess call uses a fixed argv with no shell and an absolute executable
(`git` is resolved once with `shutil.which`; `typeperf.exe` is a fixed path); the
shell scripts call `git`, `bash` and `powershell` from `PATH`.
The closing Snyk Code rescan (`snyk-code-s3-final.txt`) reports no finding in any of them.

| File | What it establishes |
|---|---|
| [`docstring_only_check.py`](docstring_only_check.py) | **F5, F7.** For `(revA, revB, path)` it reads the file at both revisions from `git show` as UTF-8 bytes, drops the module docstring and compares the two ASTs. Equal ASTs mean the two revisions define exactly the same executable code. Comments never appear in an AST, so a comment-only edit also compares equal. |
| [`raw_byte_identity.py`](raw_byte_identity.py) | **F6.** Renders all 14 historical figures from the module at two revisions (or the working tree) into temporary directories and compares the **raw** SHA-256 of every `.pdf` and `.png`. PRIN's raw output is deterministic (H4), so any difference is real. |
| [`index_selfcheck.py`](index_selfcheck.py) | **F4**, and the S3 bundle itself. Reports files in an `EVIDENCE/<bundle>/` that its README does not link, and README links that do not resolve. |
| [`immutability.sh`](immutability.sh) | **Immutability.** For a revision range: the EXP-002 record, `benchmarks/results/EXP-002/`, `.github/` and the dependency manifests must show an empty diff; S1's evidence may change only in its README; the correction audit must be a pure append (0 deleted lines). |
| [`notebook_timing.py`](notebook_timing.py) | **F2.** Runs one shipped notebook the way `tests/test_notebooks.py` does (the same client settings, plus `record_timing` for the per-cell times) and records per-cell wall time, the whole kernel process tree's CPU seconds, working set and page faults, and host CPU and available memory every 5 s. |
| [`suite_sampler.py`](suite_sampler.py) | **F2.** An out-of-process sampler that watches a running pytest session (pytest tree, every notebook kernel, host CPU, available memory and commit, the `Pages Input/sec` hard-fault counter, the largest resident processes and the busiest non-test CPU consumers) every 30 s, and `--summarize` / `--timeline` modes that print one row per notebook-kernel episode, or one row per sample with the host's CPU beside the CPU pytest received. It only reads the process table. It recognises pytest and kernels by their `-m pytest` / `-m ipykernel_launcher` argv tokens (an earlier substring match counted any shell whose command line merely mentioned pytest), exits when pytest has been gone for two samples, and gives up with status 3 if none appears within `--start-grace` seconds. |
| [`f2_in_suite_vs_alone.py`](f2_in_suite_vs_alone.py) | **F2.** Tabulates each notebook's standalone duration beside its S1, S2 and observed in-suite durations (those at the old 900 s bound marked censored), reading the observed console log on standard input. |
| [`paired_comparison.py`](paired_comparison.py) | **F2.** Prints the control-versus-treatment result of the contention experiment from its two committed records. |
| [`contention_experiment.sh`](contention_experiment.sh) | **F2.** The paired experiment: notebook 02 alone on a quiet host (control), then the same notebook once the host is saturated by only the `test_exp002_*` tests running beside it (treatment). The load generator is stopped afterwards and is never a gate. |
| [`static_gate.sh`](static_gate.sh) | **Gate.** The static, quality, security and governance legs in order, each with its verbatim command, UTC times and exit code: `ruff check` and `format --check` over every first-party root and the S1/S2/S3 evidence dirs, `mypy --strict` over `python/prin`, `DOCS/experiments` and every changed or new file and instrument, `interrogate`, `bandit`, and the four governance checkers. |
| [`verify_manifest_runs.py`](verify_manifest_runs.py) | **Delta re-audit.** `tools.reproduce.verify_manifest` over the five `benchmarks/results/EXP-002/RUN-*` directories and the frozen 172-input manifest, the way the EXP-002 driver calls it. Read-only. |
| [`delta_reaudit.sh`](delta_reaudit.sh) | **Delta re-audit.** Restores the pre-fix module (`d90eeabb`) and reproduces the regression (parity gate 18 failed / 75 passed; fast-gate argument tests all failing), restores the module (trap-guarded) and shows the tree clean, then runs both test files together on the current tree. |
| [`closing_gate.sh`](closing_gate.sh) | **Gate.** The long legs of the closing local gate, strictly one after another on a clean tree: the required fast suite and the required full suite (each observed by the sampler, **no** diagnostic plugin, so the shipped per-notebook bounds apply), targeted path-form coverage with the changed-line analysis, `cargo fmt` / `clippy -D warnings` / `test` (one retry allowed for the documented Windows contention class, both attempts recorded), the from-scratch Sphinx `-W` build, and `gitleaks` over the full history and `--staged`. |
| [`collect_final.sh`](collect_final.sh) | **Gate.** Copies the twelve records `final_legs.sh` wrote outside the repository into `gate/final/`, removing ANSI escape sequences and turning carriage returns into newlines and changing nothing else. |
| [`final_legs.sh`](final_legs.sh) | **Gate.** The cheap legs repeated on the final documentation commit: `static_gate.sh`, Sphinx, `gitleaks`, the immutability diffs, `verify_manifest_runs.py`, `delta_reaudit.sh`, the three index self-checks, the Snyk Code CLI scan with its bucketed SARIF, and the state of draft PR #34. |
| [`diagnostic_suite_run.sh`](diagnostic_suite_run.sh) | **F2.** Starts the sampler, runs pytest with the required instrumentation and a UTC timestamp on every console line, and writes everything it records **outside** the repository (pytest's own mandated, gitignored `.pytest_basetemp` aside; the tracked-change and untracked-file counts before and after are recorded). The run label is restricted so it cannot climb out of the scratch directory, and the sampler is stopped after a bounded wait so the script cannot hang on it. |
| [`diag_nb_timeout.py`](diag_nb_timeout.py) | **F2.** A diagnostic-only pytest plugin that lifts the notebook per-cell timeout to four hours so a slow leg is measured instead of killed at 900 s. Loaded only with `diagnostic_suite_run.sh --lift-notebook-timeout`; a run that loads it is a *diagnostic*, never the gate. `tests/test_notebooks.py` on disk is unchanged. |
| [`snyk_s3_filter.py`](snyk_s3_filter.py) | **Coding Standards §6 / F8.** Buckets a Snyk Code SARIF report (read on standard input) into: anything above LOW, the files S3 changed, the instruments S3 added, and the F8 locations. Exit status is 1 if any git-known path has a finding above LOW (the §6.2 gate), 2 if the SARIF is missing or unreadable (blocked, never clean). Its docstring records a correction to S2's "SARIF carries no severity" conclusion: `note` = LOW and `warning` = MEDIUM on this session's evidence. |

## Verification outputs

| File | What it is |
|---|---|
| [`docstring-only-check.txt`](docstring-only-check.txt) | **F5, F7.** `docstring_only_check.py` on the three docstring-only commits (F5 `2db18fc3`, F7 `1403451c`, and the F7 follow-up `33923be5`): AST identical outside the module docstring (exit 0 each). Two negative controls — S1's fix commit and S3's F6 commit — report a difference (exit 1), so the check can fail. |
| [`index-selfcheck-s1.txt`](index-selfcheck-s1.txt) | **F4.** `index_selfcheck.py exp002-d1-s1` after the README row: 12 files, 0 unindexed, 0 dangling. Records that the pre-edit README at `5ba0129e` did not mention the file, that the evidence file's sha256 (`fdfa17cc…`) is unchanged, and that it was last touched by `af894998`. |
| [`f6-test-red-before-fix.txt`](f6-test-red-before-fix.txt) | **F6, failing test first.** The new fig13-label regression test run against the unfixed module: **1 failed, 9 passed**, exit 1 (`'_child0' != 'Obj 0'`). Its traceback cites line 191 of the test file, three lines above the committed assertion (194): the run preceded the three-line docstring sentence about fig13 that the same commit added afterwards. |
| [`f6-verification.txt`](f6-verification.txt) | **F6.** After the fix: **V1** 103 passed (10 fast-gate tests + the 93-test byte-level parity gate); **V2** artist-level equivalence 14/14 EQUAL; **V3** fast-gate divergence coverage still 34/34 and the docstring no longer claims byte-material only; **V4** raw-byte identity of all 28 files before vs after the F6 commit; **V5** negative control — the pre-fix port `d90eeabb` differs from the fixed tree on exactly the 18 D1 files (exit 1). V2's output is filtered to its result lines. |
| [`immutability-before.txt`](immutability-before.txt) | The immutability diffs for `fd8854ed..5ba0129e`, the cycle's state before any S3 change: I1 empty, S1 evidence has 0 deleted lines and no `SHA256SUMS`/manifest, the audit shows 0 deletions. (Its I2 section lists S1's *additions* because the range starts before S1; the S3-only delta is recorded in the closing gate.) |
| [`snyk-code-s3-first-scan-medium.txt`](snyk-code-s3-first-scan-medium.txt) | **Coding Standards §6, found and remediated.** The first Snyk Code CLI scan reported **1 MEDIUM** `Command Injection` in the new `suite_sampler.py` (the `typeperf.exe` path was built from an environment variable). Kept in the record, not overwritten. |
| [`snyk-code-s3.txt`](snyk-code-s3.txt) | **Coding Standards §6 / F8 re-check.** The rescan after the fix: **0 HIGH / 0 MEDIUM / 97 LOW**; no finding in the files S3 changed or in the instruments it added; the F8 locations unchanged; and **one finding in an S2 instrument that the F8 record does not list**. The Snyk MCP route was not available in this session and is not claimed. |
| [`snyk-code-s3-after-review-fixes.txt`](snyk-code-s3-after-review-fixes.txt) | **Coding Standards §6.** The rescan after the round 2 instrument fixes (absolute `git`, argv-token detection, new exit statuses): **0 HIGH / 0 MEDIUM / 97 LOW**, nothing in the S3-added instruments, the F8 locations unchanged. |
| [`f2/README.md`](f2/README.md) | **F2, the whole measurement.** The standalone baselines, the observed full-suite run (exit 0, `6326 passed`, 2 h 42 m, notebook timeout lifted) with its console log and 132 sampler samples, the `rg.exe` snapshot, the paired contention experiment (notebook 02: **80.7 s alone versus 3,484 s beside only the `test_exp002_*` tests, 43×**), the analysis outputs, and the new bound tests red then green. Its README holds the findings, what is and is not established, and the disposition. |
| [`gate/README.md`](gate/README.md) | **The closing local gate.** The required fast suite (exit 0, `4044 passed`), the required full suite's first run (exit 1: `1 failed, 6330 passed`, the one failure a `WinError 5` file-handle contention on a `rename` in `.pytest_basetemp`, passing in isolation; all four notebook legs passed inside their new bounds, notebook 02 in 1,636 s) and second run (exit 1: `1 failed, 6330 passed`, the one failure the DV-032 host-timing node `test_no_gpu_throughput_regression`, passing in isolation; notebook 02 in 1,327 s), targeted coverage and the changed-line analysis, `cargo fmt` / `clippy` / `test`, the from-scratch Sphinx build, and `gitleaks`. [`gate/final/`](gate/README.md) holds the cheap legs repeated on the final commit: the static gate, Sphinx, `gitleaks`, the Snyk Code CLI scan (0 HIGH / 0 MEDIUM / 97 LOW), the immutability diffs, `verify_manifest`, the delta re-audit and the three index self-checks. **The required full suite is not green**; the audit's §S3.7 and §S3.9 item 9 say so. |
| [`cold-review/README.md`](cold-review/README.md) | **The cold-review loop (S3 session prompt §6).** Index of the briefs, each reviewer's raw stdout and export, the launcher, and the caller's triage, by round. [`cold-review/triage.md`](cold-review/triage.md) classifies every reviewer claim CONFIRMED / REFUTED / NOT REPRODUCIBLE with the measurement behind it. |

A first standalone run of notebook 02 (wall 69.0 s) is not committed: its kernel
CPU and memory columns matched the Windows venv launcher stub instead of the
real interpreter. The instrument was corrected before the baseline above.

## Regenerating

From the repository root with the project venv, Git Bash first on `PATH`:

```bash
.venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/docstring_only_check.py --check 5ba0129e 2db18fc3 tests/test_publication_figure_arguments.py
.venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/raw_byte_identity.py --before d53ab885 --after 2b8b7a55
.venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-d1-s3
bash EVIDENCE/exp002-d1-s3/immutability.sh 5ba0129e HEAD
.venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/notebook_timing.py --notebook 02_clevr_n_binding.ipynb --label alone
```

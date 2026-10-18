# O-2 cold review — triage record (S4, 2026-10-16 UTC)

The missing fifth round of S3's cold-review loop, performed by S4 read-only and
**by measurement**, on the committed S3 round-4 fixes. Method is the one
`EVIDENCE/exp002-d1-s3/cold-review/triage.md` uses: read the diff of the two
fix commits, suspect a defect, **reproduce it with a command**, and classify it
**CONFIRMED** (reproduced), **REFUTED** (measured otherwise) or **NOT
REPRODUCIBLE** (could not be made to occur). Only CONFIRMED claims are acted on.

**Scope reviewed** (the S4 session prompt §4B list): `closing_gate.sh`,
`final_legs.sh`, `delta_reaudit.sh`, `diagnostic_suite_run.sh`,
`cold-review/launch_round.sh`, `docstring_only_check.py`, and the comment change
in `tests/test_notebooks.py`.

**Reviewed commits:** `3bc12c7a` (round-4 instrument fixes, 6 files, +41/−22)
and `b08dd574` (`tests/test_notebooks.py` comment only, +7/−6). Both read in
full via `git show`.

**Result: 1 CONFIRMED defect (`EXP002D1-S4-F1`, D2, latent), 0 REFUTED claims
that had been asserted as defects, and 12 checks that verified the round-4 fixes
do what their commit message says.** S3's evidence files were **not edited**; the
one CONFIRMED defect is superseded by a corrected copy in this bundle.

## Records

| File | What it is |
|---|---|
| [`reproduce-batch1.sh`](reproduce-batch1.sh) / [`reproduce-batch1.txt`](reproduce-batch1.txt) | Checks C1–C12: `bash -n` on all five scripts; the `diagnostic_suite_run.sh` and `launch_round.sh` argument guards; the `mkdir -p` fix with a stubbed negative control; the `delta_reaudit.sh` trap-order red/green; the `closing_gate.sh` aggregation census and a mechanism test of its committed `leg()`; the `wc -l` padding question behind the clean-tree guards; the notebook bound tests; and an independent recomputation of every number the `b08dd574` comment cites. |
| [`reproduce-batch2.sh`](reproduce-batch2.txt) / [`reproduce-batch2.txt`](reproduce-batch2.txt) | Checks C6b, C7b, C9b, C13–C15: batch 1's two malformed invocations redone with resolved hexadecimal revisions; the corrected `closing_gate.sh` aggregation census; a mechanism test of `final_legs.sh`'s Snyk block against three stub `snyk` binaries; bash brace-group variable propagation; and `launch_round.sh`'s exit-status semantics. |
| [`reproduce-batch3.sh`](reproduce-batch3.sh) / [`reproduce-batch3.txt`](reproduce-batch3.txt) | Checks C16–C18: the non-vacuity control for `docstring_only_check.py`; **the reproduction of the CONFIRMED fail-open defect (C17)**; and whether that fail-open bit any committed S3 record (C18). |
| [`failopen-red-green.sh`](failopen-red-green.sh) / [`failopen-red-green.txt`](failopen-red-green.txt) | The red-before / green-after demonstration §4B requires for the CONFIRMED defect, plus the fail-closed check re-applied to all seven committed S3 final records. |

## CONFIRMED (1)

| # | Claim | Reproduction / measurement | Severity | Disposition |
|---|---|---|---|---|
| **S4-F1** | `final_legs.sh` aggregates five of its legs with `grep -a '<marker>' FILE \| grep -qv '<ok form>' && overall=1`. `grep -qv P` exits 0 only if **some** input line does not match `P`; with **no** input lines it exits 1, so the `&&` arm is skipped. A leg whose record file is missing, empty, or holds no marker line therefore leaves `overall=0` and **reads as passing**. It is the same class round 4 fixed for the Snyk leg alone (S3 triage T4-2); the five grep-aggregated siblings (sphinx, gitleaks, immutability, verify-manifest, the three index self-checks) were left unchanged. | **C17**, reproduced over seven record shapes: marker `0` → `overall=0` (correct); marker `1` → `overall=1` (correct); **file MISSING → `overall=0` (wrong)**; **file present with no marker → `overall=0` (wrong)**; **empty file → `overall=0` (wrong)**; the immutability leg's `script exit` variant with no marker → `overall=0` (wrong); two markers `0` then `1` → `overall=1` (correct). Mechanism proven directly: `echo -n "" \| grep -qv ': 0$'` exits **1**. **Latency measured (C18 + `failopen-red-green.txt`)**: re-applying a fail-closed check to all seven committed S3 records gives **0 failures** — sphinx 1 marker, gitleaks 2, verify-manifest 1, index-selfcheck s1/s2/s3 1 each, immutability-after 1 (`(script exit: 0)`) — so **no recorded S3 result was masked**. Every S3 leg's real exit code is honestly present in its record. | **D2** | **Superseded, not edited.** S3's `final_legs.sh` is untouched. This bundle's [`final_legs.sh`](../final_legs.sh) replaces the pattern with a fail-closed `require_marker` helper that fails on a missing record, an empty record, a record with no marker line, and any marker that is not the ok form. [`failopen-red-green.txt`](failopen-red-green.txt) is the red-before / green-after demonstration. **Severity reasoning, flagged for maintainer review:** D2 was chosen because the defect is in a *quality-gate aggregator* and the behaviour it permits contradicts Testing Standards §7 item 6 ("Incomplete is not pass") and amendment #48 item 2 (an unavailable control is "reported as *blocked*, never as passed"); S3's own round-4 reviewers rated the identical Snyk-leg instance "medium". **D4 was considered and rejected** — it is not a typo, stale comment or doc gap. The D2 label is about the instrument's design, **not** a claim that any S3 result is wrong: the latency measurement above shows none is. |

## Checks that verified the round-4 fixes (no defect)

| # | Round-4 claim under review | Measurement | Verdict |
|---|---|---|---|
| C1 | All five scripts are syntactically valid | `bash -n` on each → exit 0 ×5 | **holds** |
| C2 | `diagnostic_suite_run.sh` exits **2** on a missing label (was 1 via `${1:?…}`) | run with no argument → usage line, exit **2** | **holds** |
| C3 | the label guard still prevents climbing out of scratch | `../evil` → exit 2; `.hidden` → exit 2; neither directory was created | **holds** |
| C4 | `launch_round.sh` validates its round name | no argument → exit 2; `../evil` → exit 2 (no reviewer launched on either path) | **holds** |
| C5 | `launch_round.sh` now creates the round directory (`mkdir -p "$D"`) | stubbed copy keeping the committed validation + `mkdir` lines verbatim: `round5` exists, is writable, and all six per-reviewer files are written, exit 0. **Negative control** with `mkdir -p` removed: directory absent and all six redirections fail with "No such file or directory" — exactly the pre-fix behaviour round 4 described | **holds; fix is real and effective** |
| C6/C6b | `b08dd574` is comment-only | `git diff --numstat` 7/6; **non-comment changed lines: 0**; `docstring_only_check.py` over resolved hex `5eee9184..b08dd574` → *ast identical outside the module docstring: **True***, *module docstring changed: **False***, exit 0 | **holds** |
| C16 | …and that AST check is **non-vacuous** | the same tool over `d53ab885..2b8b7a55` (the F6 commit, which restores the real keyword argument `label=f"Obj {label}" if index < 5 else None`) → *ast identical: **False***, exit **1** | **holds** — so C6b's exit 0 is meaningful |
| C7/C7b | `docstring_only_check.py`'s docstring now says the path must be tracked at **both** revisions, the test running once per revision | a path tracked at `HEAD` but not at `fd8854ed` is refused: `'EVIDENCE/exp002-d1-s3/index_selfcheck.py' is not tracked at fd8854ed`, exit **2** — proving revision A is tested, not only B. Positive control on its own round-4 change (`b08dd574..3bc12c7a`): *ast identical: True*, *docstring changed: True*, exit 0 | **holds; the docstring claim is accurate** |
| C8 | `delta_reaudit.sh` arms its `git restore` EXIT trap **after** the clean-tree refusal, so the refusal path no longer destroys uncommitted edits | The two scripts differ only by the trap's position. With a one-line uncommitted edit to `figure_generation.py`: the **pre-fix** copy printed "tree is not clean; refusing to run", exited 2, and the module's sha256 became the HEAD blob — **the edit was DESTROYED**. The **committed** script printed the same refusal, exited 2, and the module kept the edited sha256 — **the edit SURVIVED**. Tree restored afterwards; module sha256 equals the HEAD blob `e216fec4…19a7`; `git status --porcelain` (tracked) empty | **holds; fix is real and effective** (red/green both reproduced) |
| C9/C9b | `closing_gate.sh` now aggregates every leg into its exit status | Census over the committed script: **11 legs found, 11 with aggregation, 0 without** (the two `diagnostic_suite_run.sh` legs capture `rc=$?` on the following line; `cargo test` attempt 1 aggregates through its retry arm by design, per `AGENTS.md`'s retry-once rule). Mechanism test driving the committed `leg()` verbatim: one failing leg → exit **1**; all legs passing → exit **0**. Last two statements are the `# overall:` line and `exit "$overall"` | **holds** |
| C10 | the clean-tree guards compare `$(… \| wc -l)` with `-eq` | `od -c` shows `wc -l` emits a bare `0\n` with **no padding** on this host; the guard evaluates to PASSES; a padded-input control also passes, so `-eq` tolerates it either way | **holds; no defect** |
| C11 | the notebook bound tests still pass after the comment change | `pytest tests/test_notebooks.py -k "timeout or contract or cells or directory"` → **7 passed, 30 deselected**, exit 0 | **holds** |
| C12 | every number the `b08dd574` comment cites | Recomputed independently from the committed constants: all four bounds equal `ceil(3.0 × recorded / 900) × 900` exactly. bound/quiet ratio **36.8–151.9** (comment: "37-152"); in-suite/quiet slowdown **8.3–41.8** (comment: "8-42x"); paired-experiment slowdown **43.2** (comment: "43x"); quiet-host durations **37.0–73.3 s** (comment: "37-73 s") | **holds; the corrected comment is arithmetically accurate** |
| C13 | `final_legs.sh` exits **1** when the Snyk leg writes no SARIF | The committed Snyk block extracted verbatim and driven by three stub `snyk` binaries: **no SARIF** → `overall=1`, exit **1**, record says "NO SARIF WRITTEN: this leg is BLOCKED, not clean."; **valid empty SARIF** → `overall=0`, exit **0**; **`whoami` fails (the 401 class)** → `overall=1`, exit **1** | **holds; fix is real and effective** |
| C14 | …and `overall=1` set inside `{ …; } > file` really reaches the caller | `{ }` is a group command, not a subshell: the brace-group assignment propagated (`overall=1`); a parenthesised subshell's did not | **holds** — C13's mechanism is sound |

## Observation, not a defect in the fixes under review

| # | Observation | Measurement | Classification |
|---|---|---|---|
| C15 | `launch_round.sh`'s last statement is a bare `wait`, so the script's own exit status is 0 regardless of whether any reviewer succeeded | Demonstrated: two background jobs exiting 3 and 4, then `wait` → `$? = 0`. Per-reviewer statuses **are** captured, each subshell writing `<round>/<tool>.exit`; the committed round-4 directory holds 4 `.exit` files, all `exit=0` (rounds 1–3 hold none, predating that launcher shape) | **Pre-existing design property, unchanged by round 4, and the per-reviewer status channel exists and was used.** Not a defect in the fixes under review; recorded so a future reader does not mistake the script's exit status for a pass/fail signal. **REFUTED as a defect.** |

## Two invocation errors of my own, corrected rather than left standing

Both were in the reviewer's harness, not in the code under review, and both are
kept in the records so the sequence stays auditable:

1. **Batch 1's C6 and C7 passed `b08dd574^` / `3bc12c7a^`** to
   `docstring_only_check.py`, which rejects a non-hexadecimal revision by design
   (`REVISION = re.compile(r"[0-9a-f]{7,40}")`) and exited **2**. That is correct
   tool behaviour, not a defect. Redone in batch 2 with `git rev-parse`-resolved
   hex (C6b, C7b).
2. **Batch 3's C18 used `re.match(r"script exit", line)`**, which anchors at the
   start of the line, so `immutability-after.txt`'s real marker `(script exit: 0)`
   was reported as absent and the check printed one spurious "FAIL-OPEN RISK".
   `final_legs.sh` itself uses unanchored `grep -a 'script exit'`, which matches.
   Corrected by the direct grep cross-check in the same record and by
   `failopen-red-green.sh`, which re-applies a fail-closed check to all seven
   committed records and reports **0 failures**.

## Protocol notes

- **Read-only on S3's evidence.** No file under `EVIDENCE/exp002-d1-s1/`,
  `-s2/` or `-s3/` was edited. The pre-fix copy of `delta_reaudit.sh` used for
  C8's red arm was extracted with `git show 3bc12c7a^:…` into scratch outside the
  repository.
- **The one deliberate working-tree edit** (C8's uncommitted one-line edit to
  `python/prin/reporting/figure_generation.py`) was restored inside the same
  check and byte-verified against the HEAD blob; `git status --porcelain`
  (tracked) was empty before and after every batch.
- **The optional independent reviewer pass was not run.** The S4 session prompt
  permits at most one round with the `devin` and `agy` CLIs. It was declined
  deliberately, not skipped silently: the review §4B requires is S4's own, by
  measurement, and loading three reviewer CLIs onto this host would directly
  worsen the contention that observation O-1 is about, immediately before the
  required full-suite gate leg that O-1's disposition depends on. This triage is
  therefore S4's own measurement, and no external reviewer corroborates it.
- **No test was weakened, no tolerance loosened, and no skip, deselection or
  suppression added** to reach this result.

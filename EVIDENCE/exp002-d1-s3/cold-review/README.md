# Cold review — S3 evidence

Index of the cold-review loop (section 6 of the S3 session prompt): three independent reviewers receive
an identical brief and no account of what changed, review the S3 diff from
scratch, and every claim is then triaged by measurement. The triage, with the
command and output behind each classification, is [`triage.md`](triage.md).

## Reviewers and how each was invoked

Interfaces were discovered from each tool's own `--help` / model listing, not
guessed.

| Reviewer | Model | Invocation | What it can do headless |
|---|---|---|---|
| Devin CLI 3000.11.3 | `swe-2-high` | `devin --model swe-2-high -p --prompt-file <brief> --permission-mode smart --export <out>` | Read files; run shell commands, but a command that `smart` mode will not auto-approve **ends the session with no report** (round 1: `git check-ignore`). |
| Antigravity `agy` 1.3.5 | `gemini-3.8-flash-high` (the "Gemini 3.8 Flash" family; the high-effort variant) | `agy --model gemini-3.8-flash-high --mode plan --output-format text -p "<pointer to the brief>"` | Read and search files. Any shell attempt is auto-denied and **ends the session with no output**. |
| Qwen Code 0.21.7 | `qwen3.8-max-preview` (the only Qwen3.8-max model configured on this host, so the closest match to "Qwen3.8-max") | `qwen.cmd -m qwen3.8-max-preview -o text -p "<pointer to the brief>"` | Read and search files; no shell tool. Prints its report only when finished, so empty stdout says nothing about progress; its session log shows it. |

`agy` and Qwen are given a one-sentence pointer ("your complete instructions are
in the file …; read it in full and carry them out exactly") because the brief is
long and Qwen runs behind a `.cmd` wrapper with command-line length and quoting
limits; Devin takes the brief itself with `--prompt-file`. The brief file is
byte-identical for all three. There is no sandbox on Windows, so read-only was
enforced in the brief and verified afterwards: `git status --porcelain` was empty
before and after each round (`status-before.txt`; the post-round counts are
recorded in the round tables below).

[`launch_round.sh`](launch_round.sh) is the launcher used for every round that
launched all three reviewers together. [`launch_devin_attempt.sh`](launch_devin_attempt.sh)
re-runs Devin alone on the same brief (round 4's second attempt).

## Briefs

| File | What it is |
|---|---|
| [`reviewer-brief-v1.md`](reviewer-brief-v1.md) | Round 1 brief (sha256 `50b3a9bc…`). Allowed read-only shell commands. |
| [`reviewer-brief-v2.md`](reviewer-brief-v2.md) | Round 2 (sha256 `126ed80f…`). Forbids shell commands for all three reviewers, because a denied command ended two reviewers' sessions in round 1; supplies the diff and commit list as files. |
| [`reviewer-brief-v3.md`](reviewer-brief-v3.md) | Round 3 (sha256 `caff383a…`). v2 plus one paragraph saying the diff file omits some large raw-data files and the review records, which are listed with sizes and hashes in `round3/s3-excluded.txt`. |

## Round 1 — HEAD `7dbfc546`, brief v1 — degraded, no reviewer produced a report

| File | What it is |
|---|---|
| [`round1/head.txt`](round1/head.txt), [`round1/status-before.txt`](round1/status-before.txt) | The reviewed commit and an empty `git status --porcelain` before the round. |
| [`round1/devin-stdout.txt`](round1/devin-stdout.txt), [`round1/devin-export.md`](round1/devin-export.md) | Devin's stdout (narration only) and its exported transcript (JSON, written by `--export`): 24 steps, ended on a rejected tool call. |
| [`round1/agy-stdout.txt`](round1/agy-stdout.txt) | agy's only output: the auto-denied-command message. |
| [`round1/qwen-terminated.txt`](round1/qwen-terminated.txt) | The caller's record of terminating Qwen after ~24 minutes. See `triage.md` for why that was premature. |

After round 1, `git status --porcelain` was empty (no reviewer modified the tree).

## Round 2 — HEAD `33923be5`, brief v2 — all three reviewed

| File | What it is |
|---|---|
| [`round2/head.txt`](round2/head.txt), [`round2/status-before.txt`](round2/status-before.txt) | The reviewed commit and an empty `git status --porcelain` before the round. |
| [`round2/devin-stdout.txt`](round2/devin-stdout.txt), [`round2/devin-export.md`](round2/devin-export.md) | Devin's report (8 findings) and its exported transcript (JSON). |
| [`round2/agy-stdout.txt`](round2/agy-stdout.txt) | agy's report (6 findings, plus narrative assertions many of which are fabricated; see `triage.md`). |
| [`round2/qwen-stdout.txt`](round2/qwen-stdout.txt) | Qwen's report (11 findings and a "checked, no finding" section). |
| [`round2/triage-commands.txt`](round2/triage-commands.txt) | The caller's reproduction of every checkable Devin, agy and Qwen claim, at the reviewed commit, with verbatim output. |
| [`round2/triage-commands-agy-fabrications.txt`](round2/triage-commands-agy-fabrications.txt) | Searches showing the things agy named do not exist in the repository, the diff or the commit log. |

After round 2, `git status --porcelain` was empty.

## Round 3 — HEAD `b2156918`, brief v3 — all three reviewed (Devin on its fourth attempt)

| File | What it is |
|---|---|
| [`round3/head.txt`](round3/head.txt), [`round3/status-before.txt`](round3/status-before.txt), [`round3/s3-excluded.txt`](round3/s3-excluded.txt) | The reviewed commit, an empty `git status --porcelain` before the round, and the list of files omitted from the diff file (with a header giving the sizes of the review files). |
| [`round3/devin-stdout.txt`](round3/devin-stdout.txt), [`round3/devin-export.md`](round3/devin-export.md) | Devin's report (attempt 4, 9 findings) and its exported transcript. |
| [`round3/devin-attempt1-stdout.txt`](round3/devin-attempt1-stdout.txt), [`round3/devin-attempt1-export.md`](round3/devin-attempt1-export.md), [`round3/devin-attempt2-stdout.txt`](round3/devin-attempt2-stdout.txt), [`round3/devin-attempt2-export.md`](round3/devin-attempt2-export.md) | Attempts 1 and 2: each ended when `smart` mode rejected a command (`wc -l` / `ls`) despite the brief; no report. |
| [`round3/devin-attempt3-stdout.txt`](round3/devin-attempt3-stdout.txt), [`round3/devin-attempt3-export.md`](round3/devin-attempt3-export.md) | Attempt 3: read everything, then hit the model's output-length limit before writing a report (exit 1). Its narration is where the citation problem T3-18 was noticed. |
| [`round3/agy-stdout.txt`](round3/agy-stdout.txt) | agy's report (2 findings). |
| [`round3/qwen-stdout.txt`](round3/qwen-stdout.txt) | Qwen's report (13 findings and a "checked, no finding" section). |
| [`round3/triage-commands.txt`](round3/triage-commands.txt) | The caller's reproduction of every checkable round 3 claim, at the reviewed commit, with verbatim output. |

After round 3, `git status --porcelain` was empty.

## Round 4 — HEAD `5eee9184`, brief v3 — all three reviewed (Devin on its second attempt); the cap

| File | What it is |
|---|---|
| [`round4/head.txt`](round4/head.txt), [`round4/status-before.txt`](round4/status-before.txt), [`round4/s3-excluded.txt`](round4/s3-excluded.txt) | The reviewed commit, an empty `git status --porcelain` before the round, and the list of files omitted from the diff file (with a header giving the sizes of the review files). The brief is [`reviewer-brief-v3.md`](reviewer-brief-v3.md), unchanged. |
| [`round4/devin-attempt2-stdout.txt`](round4/devin-attempt2-stdout.txt), [`round4/devin-attempt2-export.md`](round4/devin-attempt2-export.md), [`round4/devin-attempt2.exit`](round4/devin-attempt2.exit) | Devin's report (7 findings) and its exported transcript. |
| [`round4/devin-attempt1-stdout.txt`](round4/devin-attempt1-stdout.txt), [`round4/devin-attempt1-export.md`](round4/devin-attempt1-export.md), [`round4/devin-attempt1.exit`](round4/devin-attempt1.exit) | Attempt 1: ended on a rejected `ls -la` the brief had forbidden; no report. |
| [`round4/agy-stdout.txt`](round4/agy-stdout.txt), [`round4/agy.exit`](round4/agy.exit) | agy's report (1 finding). |
| [`round4/qwen-stdout.txt`](round4/qwen-stdout.txt), [`round4/qwen.exit`](round4/qwen.exit) | Qwen's report (10 findings and a "judgements that produced no finding" section), after about an hour. |
| [`round4/triage-commands-a.txt`](round4/triage-commands-a.txt) | The documentation claims measured at the reviewed commit. |
| [`round4/triage-commands-b-red.txt`](round4/triage-commands-b-red.txt) | The code-level claims reproduced before any fix (the module edit destroyed by the trap; the missing round directory; exit statuses). |
| [`round4/triage-commands-c-green.txt`](round4/triage-commands-c-green.txt) | The same reproductions after the fixes, including `final_legs.sh` run against a stub Snyk CLI that writes no SARIF (exit 1, leg BLOCKED). |

After round 4, `git status --porcelain` was empty (before any fix was applied).

## Protocol applied (section 6 of the S3 session prompt)

The S3 session prompt is the maintainer's execution contract for this session; it is
not a repository file, so the rules it set are summarised here:

- three independent reviewers (Devin `swe-2-high`, Antigravity Gemini 3.8 Flash,
  Qwen3.8-max), each given the **identical brief** and **no account** of what changed
  or why, reviewing the current tree and the S3 diff from scratch;
- reviewers are **read-only**, enforced in the brief and verified with
  `git status --porcelain` after each round; a reviewer that modified the tree would
  be a protocol breach (none did);
- an unavailable CLI is recorded as unavailable, never simulated, and a round with a
  reviewer missing is labelled degraded;
- every claim is **reproduced or measured before anything is changed** and classified
  CONFIRMED, REFUTED or NOT REPRODUCIBLE; only CONFIRMED claims are fixed; refutations
  are recorded with their measurement; claims are deduplicated; where reviewers
  conflict the measurement decides;
- the loop runs until a round returns **zero CONFIRMED claims** from all available
  reviewers, capped at **four rounds**, after which the residual is dispositioned with
  its measurement; no test is weakened, no tolerance loosened, no skip or suppression
  added to reach a clean round.

# Cold review — S3 evidence

Index of the cold-review loop (S3 brief §6): three independent reviewers receive
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

[`launch_round.sh`](launch_round.sh) is the launcher used for both rounds.

## Briefs

| File | What it is |
|---|---|
| [`reviewer-brief-v1.md`](reviewer-brief-v1.md) | Round 1 brief (sha256 `50b3a9bc…`). Allowed read-only shell commands. |
| [`reviewer-brief-v2.md`](reviewer-brief-v2.md) | Round 2 onward (sha256 `126ed80f…`). Forbids shell commands for all three reviewers, because a denied command ended two reviewers' sessions in round 1; supplies the diff and commit list as files. |

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

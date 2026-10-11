# EA-007 evidence

Global executive audit and EXP-002 readiness session, opened 2026-10-11 UTC.
This directory contains audit evidence, not experiment runs or E-stage work.

- `readiness-state.json`: lead-reviewed, frozen observations and maintainer
  approval. Ratios are transcribed from the recorded nightly gate, not recomputed
  from campaign data. Its command list identifies each read-only GitHub source.
- `exp001-r1-merge-ci-green.log`: verbatim historical merge check output and exit
  code for PR #28. UTF-8 capture corrects the terminal's initial encoding loss.
- `historical-nightly-and-merge-capture.log`: original command output capture
  including the latest pre-pause nightly's job metadata, benchmark log excerpt,
  historical merge check, and empty secret-alert list. The initial merge-check
  excerpt has replacement characters; use the separate UTF-8 log for that check.
- `verification/` — the executed local gate's per-command logs, retained
  with an index (`README.md`) and `SHA256SUMS.txt` integrity inventory.
  The scratch originals live in `DOCS/test_and_benchmark_results/ea007/`,
  which is **gitignored and local to the maintainer workstation — not part
  of the repository record and unreachable from any clone**; this directory
  is the committed record. These are the captured local results, not a
  promise of future re-execution.
- `verification/post-commit/` — the post-commit secret scans. Leg 15 of the
  gate index scanned base `fdd28d88` (704 commits) before any commit of this
  PR existed; these scan 706 commits @ `0738714` and 707 commits @ `add7386a`
  (704 + the PR's 3 commits). A scan of a commit can only be recorded by a
  *later* commit, so each result is stated about the commit it names, never
  about the then-current head. Commits added after `add7386a` need their own
  scan: the PR #32 review-round commit's staged-diff scan is leg L18 of
  `verification/pr32-review/pr32-gate-run.log`, and the post-commit
  full-history scan of the resulting head is reported in the PR description,
  not in the repository (a document cannot contain the result of a scan of
  itself).

The `main` SHA is `fdd28d88e4c57d544e5d30fa52cce85807ab15a9`.
Hosted workflows remain disabled under Plan amendment #48. Historical success
is not a green-CI assertion about EA-007 or current `main`; local commands and
their actual results govern this Windows session.

**Packaging:** `.gitattributes` marks `EVIDENCE/ea007/**` as
`-text whitespace=-trailing-space` so committed blobs stay byte-exact against
`verification/SHA256SUMS.txt` — raw CRLF tool output is evidence, not a style
defect (same pattern as `benchmarks/results/**`). This note lives outside the
hashed bundle (it and `verification/SHA256SUMS.txt` are the only two files
the manifest does not cover; `tests/test_ea007_manifest.py` enforces that
every other file here is listed and matches).

**Scope notes (PR #32 review round).**

- `verification/full-gate/26h-source-hashes.txt` binds the six first-party
  source/config files the gates *executed against* at gate time (its
  header's "the files this diff touches" is narrower than the PR's 19
  non-evidence files, the other 13 being `.gitattributes`, `CHANGELOG.md`,
  READMEs, reports and registers). It is a gate-time record and is not
  rewritten; the remediation round's own hashes are in
  `verification/pr32-review/pr32-source-hashes.txt`.
- `verification/full-gate/prin-requirements.txt` and
  `prin-resolved/requirements.txt` are byte-identical on purpose: the logs of
  legs 22d/22e invoked the `prin-resolved/` path and are verbatim. The file
  is *version*-pinned (`name==version`), not hash-pinned (no `--hash` lines).
- `verification/full-gate/13a-cargo-audit.log` line 5 prints the local
  `cargo` advisory-database path (a Windows home directory). It is tool
  output, not a credential, and is left verbatim because raw logs are the
  evidence; full-history gitleaks found no secret.
- At commit `0738714` (before `add7386`) 36 of the 82 manifest entries did not
  match: the `.gitattributes` byte-exactness rule landed in the same commit
  as the files it protects, so `* text=auto eol=lf` rewrote their CRLF at
  `git add` time. `add7386` re-staged them; the head verifies 82/82 and the
  history is not rewritten. Land an attribute rule in its own commit,
  before the files it protects.

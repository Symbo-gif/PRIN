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
  Originals remain in `DOCS/test_and_benchmark_results/ea007/`; these are
  the captured local results, not a promise of future re-execution.

The `main` SHA is `fdd28d88e4c57d544e5d30fa52cce85807ab15a9`.
Hosted workflows remain disabled under Plan amendment #48. Historical success
is not a green-CI assertion about EA-007 or current `main`; local commands and
their actual results govern this Windows session.

**Packaging:** `.gitattributes` marks `EVIDENCE/ea007/**` as
`-text whitespace=-trailing-space` so committed blobs stay byte-exact against
`verification/SHA256SUMS.txt` — raw CRLF tool output is evidence, not a style
defect (same pattern as `benchmarks/results/**`). This note lives outside the
hashed bundle; the manifest and its inputs are unchanged.

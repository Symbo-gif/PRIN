# Session-0159 evidence

EXP-002 / C1 E1 session (phase 7), 2026-10-11 UTC. This directory holds
session-local verification evidence only — no E3 execution, no experiment
artefacts, no preregistration or analysis content.

- `entry-state.json` — lead-authored frozen E1 entry observations (source
  baseline, initial checkout, session branch, attribute commit, settled
  GitHub observations including the completed `[]` native open-alert
  read). Frozen input evidence; read for presentation, never regenerated.
- `verification/` — preserved verification logs with an index
  (`verification/README.md`) and a `SHA256SUMS.txt` integrity inventory.
  The live/scratch originals stay in `DOCS/test_and_benchmark_results/`,
  which is gitignored and local to the maintainer workstation — not part of
  the repository record; this directory is the committed record. Only
  closed logs are copied here.

## Source and environment (settled observations)

- Source baseline: `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53` — the PR #32
  merge on `main` (mergedAt 2026-10-11T10:39:51Z, PR head
  `8b4d1803c050058c115e74258423f42414e994e2`); `origin/main` equals that
  SHA and the local repository is not shallow.
- Host `HP`: the maintainer's Windows workstation. All evidence here is
  local under Plan amendment #48 — never a hosted-CI claim. The seven check
  workflows (`rust`, `python`, `parity`, `repro`, `snyk`, `gpu`, `nightly`)
  are disabled; `release.yml` (tag-triggered) and `gpu-triton.yml`
  (manual-only) are untouched. Ruleset 22150076 is active (PR-only, no
  deletion, no non-fast-forward/force-push, no required status checks).
  GitHub native secret scanning is enabled; push protection is disabled.
  The native open-alert read completed and is settled: `[]` open alerts
  (frozen in `entry-state.json`); do not re-query.
- The byte-preservation attribute rule `EVIDENCE/0159/**` landed in the
  attribute-only commit `85b779297be0642f5c64853c1590ef341e7ff77e` before
  any file in this directory — the ea007 lesson: land the attribute rule in
  its own commit ahead of the files it protects.

## Status

The session's final full local gate is **pending**; no final full-gate
pass is asserted. `verification/` preserves two classes of closed logs:
prior unheaded tool captures (raw tool output with no command/host/UTC/exit
header — labelled as such in its index) and the two headed focused
driver-validation batches (`0159-driver-*` — the pre-review run, and
`0159-driver-final-*` — the post-review run on the corrected source), plus
`source-hashes.txt`, each headed log carrying
command/source/UTC/host/actual-exit metadata.

**Packaging:** `.gitattributes` marks `EVIDENCE/0159/**` as
`-text whitespace=-trailing-space` so committed blobs stay byte-exact
against `verification/SHA256SUMS.txt` — raw CRLF tool output is evidence,
not a style defect (same pattern as `benchmarks/results/**` and
`EVIDENCE/ea007/**`). This README and `verification/SHA256SUMS.txt` are the
only two files the manifest does not cover — un-hashed by design; every
other file in the bundle is listed and matches.

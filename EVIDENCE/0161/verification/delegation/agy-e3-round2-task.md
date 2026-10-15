# Cold self-audit, round 2 (read-only) — EXP-002 E3: the follow-up commit's text and numbers

Repository `C:\dev\PRIN`; working tree = commit `e425971` (clean). Its parent is `89f21f5`, which you
reviewed in round 1 (no finding). Round 1's accepted outcome: your report listed no defect; Devin raised twelve
items about the validation tooling, all adjudicated in
`EVIDENCE/0161/verification/delegation/adjudication.md`. This round reviews ONLY what the follow-up commit
added. You have NO shell and may not edit anything. Print the report to stdout. QUOTE VERBATIM with real
line numbers; label any paraphrase as such; do not invent IDs, values or quotes.

## HARD RULE — do not read experimental outcomes (unchanged)

Do NOT open `benchmarks/results/EXP-002/RUN-*/api.json`, `conclusions.json`, `reproduction.json`, or anything under
`DOCS/test_and_benchmark_results/`. You MAY open every `campaign-metadata.json` and `manifest.json`. Do not compare or
comment on equality or inequality between hashes, sizes or listing digests of different publication arms, and do not
say whether anything "matches" in the experimental sense. If you see observation content, do not quote or allude to it.

## What changed (read these)

- Diffs: `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\8a021180-4f6b-439e-9fe7-62b13011e219\scratchpad\e3\delegation\delta2-name-status.txt` and
  `...\delta2-records.diff` (same directory; documentation and records only; `EVIDENCE/0161/verification` is excluded from the diff).
- `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md` — new §8 (hosted results for `89f21f5`),
  §9 (`cargo audit`), §10 (cold reviews, validator revision 3, a clarification of "not examined"), §11 (state at close).
- `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/README.md` — handoff items 5 and 6 and the changed
  sentence about observation payloads; `CHANGELOG.md` — the added sentence about `cargo audit`; `EVIDENCE/0161/README.md`.
- Evidence the new text cites: `EVIDENCE/0161/verification/hosted/*`, `.../gate/R08-cargo-audit.log`, `.../gate/G14c-*`,
  `.../gate/G17b-*`, `.../gate/delta-follow-up/*`, `.../legs/*.rev3.txt`, `.../delegation/adjudication.md`,
  `.../preflight/hosted-runs-fae24c4.json`, `.../SHA256SUMS.txt`.

## Check, reporting concrete defects only

1. Numbers in log §8–§11 against the files they cite: the hosted table (IDs, conclusions, start and end, durations —
   recompute each duration), the `rust` job list, the advisory counts (1,299 → 1,307), the five RUSTSEC IDs with their
   stated severities and fixed-in versions, the three allowed warnings, the validator-rev3 counts (81/80/87/87/87), the mutation
   self-test counts (40/41/49/49/49), the byte arithmetic in §11, SHA-256 values quoted for `validate_run_record_rev3.py`
   and `mutation_test_rev3.py` against `SHA256SUMS.txt`.
2. Accuracy of the `cargo audit` narrative: is each claim supported by the cited file (reproduced locally; not attributable;
   unreachable in every resolved graph; "I opened no DV row and changed no file for it")? Anything overstated or presented as
   fact that the files do not show?
3. Does §10's clarification of "not examined" faithfully describe what the tools do, according to
   `EVIDENCE/0161/verification/tools/*.py`? Does anything in §10 or the adjudication claim a fix that the evidence does not show?
4. Verdict leakage or interpretation anywhere in the new text; any statement about equality/difference of arm outputs.
5. Consistency with the rest: statuses (0161 COMPLETE, 0162 READY), the README handoff numbering and links, timestamps labelled
   "Entered" (the current clock was about 2026-10-13T00:31Z when they were written — judge whether they are plausible), the
   CHANGELOG sentence versus log §9.
6. Honest handling: is the one red check (hosted and local `cargo audit`) reported plainly and not buried, in the log, README,
   CHANGELOG and commit text? Is the proposed disposition within what an execution-only session may do?

## By design — do NOT report

- The `Co-Authored-By: Claude Opus 5.5` trailer (maintainer's instruction; the commit bodies disclose the executing model).
- The scratch gate harness not being committed; the tracker table in §3 whose only row says "no leg run yet" (append-only design).
- The hosted results of the follow-up commit itself not being in the repository (a document cannot hold its own commit's results).
- Anything about the driver, the protocol text or E2: frozen, out of scope.

## Output

Numbered findings (file:line, verbatim quote, why wrong, suggested fix, confidence), then areas checked and found sound.

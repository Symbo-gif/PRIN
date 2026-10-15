# Cold self-audit, round 2 (read-only) — EXP-002 E3: validator revision 3 and its self-test

Repository `C:\dev\PRIN`; working tree = commit `e425971` (clean); execution source `R` = `fae24c4`.
Do NOT run shell commands or edit files. Open only the files named here. Print the report to stdout.

## HARD RULE — do not read experimental outcomes (unchanged from round 1)

Do NOT open `benchmarks/results/EXP-002/RUN-*/api.json`, `conclusions.json` or `reproduction.json`, nor anything under
`DOCS/test_and_benchmark_results/`. You MAY open every `campaign-metadata.json` and `manifest.json` and everything under
`EVIDENCE/0161/`. Do not compare or comment on equality or inequality between hashes, sizes or listing digests of different
publication arms. If you see observation content, do not quote or summarise it.

## Context

Round 1 (your report: `EVIDENCE/0161/verification/delegation/devin-e3-report.txt`) raised F-01…F-12 on validator revisions 1–2.
The adjudication is `EVIDENCE/0161/verification/delegation/adjudication.md`. Revision 3 is the response:
`EVIDENCE/0161/verification/tools/validate_run_record_rev3.py` with its self-test
`EVIDENCE/0161/verification/tools/mutation_test_rev3.py`; transcripts are `EVIDENCE/0161/verification/legs/leg*.validation.rev3.txt`
and `leg*.mutation-selftest.rev3.txt`. Compare with revision 2 (`validate_run_record.py`) in the same directory.
The driver (`benchmarks/campaign/exp002_driver.py`, frozen) is the reference for what a genuine record looks like.

## Hunt for real defects, each with a concrete scenario

1. For each of F-01…F-07: is the claimed fix really in revision 3 and really effective? Quote the lines. Is any fix vacuous
   (a check that cannot fail), or does it fail for the wrong reason?
2. New false-pass risks in revision 3: what invalid record can still pass? (key-set definitions that are too permissive, the
   `C02` extra-key rule, table-file extra keys keyed on the path, type checks, timestamp tolerance, `HEAD` relaxed to "R is an
   ancestor of HEAD", the new G1 drift check against `R`, JSON strictness, retention checks with `--generated-root`.)
3. New false-fail risks (a genuine record that revision 3 would reject, e.g. the schema it hard-codes versus what the driver
   emits). Compare the hard-coded key sets with the driver's emitted structures.
4. Does revision 3 read or judge any experimental outcome (API `resolved`/`callable`, claim `observed` vs `expected`, publication
   digests across arms)? It must only check structure and identity.
5. `mutation_test_rev3.py`: does every case exercise the check it names? Is the baseline normalisation (rewriting `out_dir` and the
   directory layout of the copy) sound, or could it mask a failure? Which important mutations are still missing? Is the junction
   case really testing S1? Are the retention cases (F1–F4) isolated on private copies?
6. The transcripts: do the counts and the SHA-256 values quoted in `log.md` §10 and `adjudication.md` match them?
7. Any command-injection, path-traversal or unsafe-write pattern in the two new scripts.

## By design — do NOT report

- Revisions 1–2 remaining in the repository; the scratch gate harness not being committed; the Opus trailer on commits.
- Driver gaps that revision 3 deliberately does not fix because the driver is frozen (junction ancestors, last-wins JSON, subset keys).
- Identical or different listing digests between arms (out of scope — do not discuss).

## Output

Each finding: severity (High/Medium/Low), file:line, a concrete scenario, why it is wrong, suggested fix. Then areas checked and found sound.

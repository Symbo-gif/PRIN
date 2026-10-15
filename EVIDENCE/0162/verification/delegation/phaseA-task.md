# Cold review (read-only) - EXP-002 E4 analysis module and its tests, BEFORE any real run

Repository `C:\dev\PRIN`, branch `campaign/0159-exp002-e1`. The module and its tests are new,
uncommitted files in the working tree. Do NOT run shell commands or edit files. Print your report to
stdout.

## HARD RULE - you must not see any experimental outcome

The analysis has not been run on the real records and nobody has looked at their observations.
Seeing them now would contaminate the session.

- Do NOT open anything under `benchmarks/results/EXP-002/RUN-*` (no `api.json`, `conclusions.json`,
  `reproduction.json`, `manifest.json` or `campaign-metadata.json`).
- Do NOT open anything under `DOCS/test_and_benchmark_results/`.
- Do NOT open anything under `DOCS/archive and reference from PRINet 3.0/` (its JSON inputs decide H2).
- Do NOT open the `EVIDENCE/0161/verification/legs/*.validation*.txt` transcripts or anything quoting
  record values, and do NOT read PR #33 comments or reviews.
- If you see outcome content anyway, do not quote, summarise or reason from it.

## What to read

1. The module: `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis/exp002_e4_analysis.py`.
2. Its tests: `tests/test_exp002_e4_analysis.py` (synthetic fixtures only).
3. The frozen rules it must implement: `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md`
   sections 2, 3, 4.1, 4.2, 4.3, 5.1-5.5, 7, 8, 8.1, 8.2, 11.3.
   Also `e2-review.md` decisions 1-10 in the same directory.
4. The record schema producer (frozen; out of scope for defects, read only to check the module's schema
   assumptions): `benchmarks/campaign/exp002_driver.py` - `collect_api`, `_collect_conclusions`,
   `collect_reproduction`, `normalized_bytes`, `sensitivity_bytes`, `_check_observations`,
   `check_run_complete`, `run_registered`.
5. `DOCS/experiments/campaign-plan.md` sections 7.4, 9.1, 10.4, 12.

## Hunt for real defects, each with a concrete failing scenario (inputs -> wrong output)

1. **Decision rules (section 4.1).** For H1-H4: is the valid-counterexample rule applied before the
   complete-coverage rule? Can any branch return CONFIRMED with incomplete coverage, REFUTED from an
   inadmissible record, or INCONCLUSIVE when a valid counterexample exists? Is any driver-provided status
   or Boolean trusted as a verdict without re-derivation?
2. **H1.** Population (172 reference names + 3 additions), ownership re-derivation (Migration Guide +
   WP-001 at `R`), row classification from the retained `type`/`callable`/`error` fields, duplicates,
   removals, unexpected names, frozen-contract sets.
3. **H2.** Does `derive_claim_cases` reproduce section 5.2 exactly (paths, operators, thresholds 0.555 /
   0.5, units, C02 stored flags, C03 by `n_oscillators`, C05 CPU entries only)? Can a record that
   disagrees with the frozen inputs in any field pass?
4. **H3.** Approved policy = normalized digests; sensitivity policy = sensitivity digests (tables raw,
   PDF masked in place, PNG normalized); the 11 archived tables as an additional reference (PRIN vs
   archived counts; reference vs archived is reported). Missing/extra outputs refute. Renderer change or
   inadmissible arm -> INCONCLUSIVE. Is H3 computed under both policies side by side?
5. **H4.** Raw bytes only; the section 5.5 projection (what it removes, what it keeps); inventory
   differences; normalization can never rescue H4.
6. **Admissibility before payload.** Is every manifest, pin, provenance and input-identity check done
   before `observations` is read? Any false pass for a tampered, missing, extra, symlinked/junction or
   aborted record or input? Any check that is vacuous?
7. **D1 flag.** Computed from primary verdicts (any REFUTED). Is the H3 sensitivity result reported so it
   cannot be hidden?
8. **Outputs.** The seven registered files and `report-manifest.json` (section 8.1): required contents,
   units on every denominator, 39 generated files separate from 7 analysis files, no wall-clock time,
   determinism (sorted keys, LF, fixed order). Writes confined to the two registered destinations.
9. **Isolation.** The module must not import `prin`, `prinet`, the driver or `tools.reproduce`; must not
   render, resolve exports or read the retained publication roots.
10. **Tests.** Which test could pass vacuously or for the wrong reason? Which decision branch is untested?
    Do the synthetic records really have the driver's shape?
11. **Security.** Command injection (git argv), path traversal, unsafe writes, TOCTOU.

## By design - do not report these as defects

- The module re-implements no-follow, manifest-verified reads with the standard library because
  `tools.reproduce` imports `prin` at module level.
- A row that claims to be resolved but is neither callable nor a built-in scalar type is "unverifiable"
  (a coverage gap, so INCONCLUSIVE unless another valid counterexample refutes), because a subclass of a
  scalar cannot be proven from its retained type name.
- H4: an identical extra output present in both PRIN runs does not refute H4 (H3 catches it); the same
  registered file missing from both PRIN runs makes H4 INCONCLUSIVE (and H3 REFUTED).
- Record-level problems make a record inadmissible (reported, never fatal); global problems (protocol,
  input manifest, frozen inputs, reference API, unindexed run directory, git) abort with nothing written.
- The tests reuse a session-verified global context for record-level tests (to avoid eight git spawns per
  test on Windows); every global precondition has its own full-path test.
- Real-record values are never asserted by the tests; one test hashes the five records' bytes to check the
  pinned run index.

## Report format

For each finding: ID, severity (High/Medium/Low), file:line, the concrete scenario, and the fix you
suggest. Then a list of what you checked and found sound. Do not include any experimental outcome.

# Self-audit (read-only) — EXP-002 E4 outputs, records and documentation, after the analysis ran

Repository `C:\dev\PRIN`, branch `campaign/0159-exp002-e1`. The committed analysis module (`3731fc2`) has
run on the five real E3 records; its outputs exist. The documentation changes are uncommitted in the working
tree. Do NOT run shell commands or edit files. Print your report to stdout.

## What you may and may not read

- MAY read: the five run records under `benchmarks/results/EXP-002/RUN-*/` (result JSON, `manifest.json`,
  `campaign-metadata.json`); the seven outputs under `DOCS/test_and_benchmark_results/EXP-002/analysis/`;
  everything under `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`; the files named
  below.
- Do NOT open anything under `DOCS/test_and_benchmark_results/EXP-002/RUN-*/` (the retained publication
  roots and input snapshots; E5 verifies them) and do not open PR #33 comments.

## Files to check

1. `DOCS/test_and_benchmark_results/EXP-002/analysis/` — `summary.json`, `api-mapping.csv`,
   `conclusion-comparisons.csv`, `reproduction-comparisons.csv`, `error-distributions.json`,
   `expected-vs-observed.md`, `coverage-and-deferrals.md`.
2. `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report-manifest.json`,
   `analysis.md`, `README.md` (status line and the "E4 to E5 handoff" section), `analysis/README.md`,
   `log.md` (line 1 only is new).
3. `DOCS/sessions/phase-7/0162-…md` and `0163-…md` (Status lines), `DOCS/sessions/SESSION_REGISTER.md`
   (line 5 and the 0162/0163 rows), `DOCS/sessions/phase-7/README.md` (0162/0163 rows), `CHANGELOG.md` (the
   first entry under "Added"), `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (the DV-040 row, last
   bracketed entry).
4. The rules: `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md`
   §2, §3, §4.1, §4.3, §5.3, §5.4, §7, §8.1, §8.2, §11.3 and `e2-review.md` decision 9.

## Check, with a concrete citation for each finding

1. **Numbers.** Recount from the run records and the CSVs: H1 (175 rows, classifications, ownership,
   observed list, frozen sets); H2 (62 cases, per-family counts, every `expected` versus `observed`); H3 (39
   files per arm, the number equal/different under the approved policy — `normalized_*` — and under the
   sensitivity policy — `sensitivity_*`, tables against `archived_*`); H4 (raw sizes/digests between the
   prin and repeatability records). Do the counts in every document agree with the records and with each
   other?
2. **Verdicts.** Given the counts, is each verdict exactly what §4.1 gives? Is the D1 flag what §4.3 gives?
   Is the H3 dual-policy statement consistent with §11.3 item 1?
3. **Denominators and units.** Every count labelled with its population (api_symbol, legacy_api_name,
   claim_comparator_record, generated_file); the 39 publication files never added to the 7 analysis files;
   no unlabeled histogram; CIs/effect sizes stated as not applicable.
4. **Digests.** Do the digests and byte sizes quoted in `analysis.md`, the README handoff and
   `report-manifest.json` agree with each other (you cannot hash files; check internal consistency and that
   the manifest lists 7 analysis outputs and 39 publication files)?
5. **Wording.** Any spin, any claim beyond the registered rules (a cause for the H3 differences, a
   reinterpretation, an "explained" mismatch), any over-claim about gates (the full local pytest leg was red
   on two tests; `cargo audit` is red; nothing may be called green that is not), any stale or contradictory
   status across the briefs, register, phase README, EXP-002 README and CHANGELOG.
6. **Coverage.** Does `coverage-and-deferrals.md` keep all seven §5.3 owners open, none silently closed?

For each finding: ID, severity, file:line, what is wrong, the evidence, the fix. Then list what you checked
and found consistent.

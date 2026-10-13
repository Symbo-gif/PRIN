# Cold review round 2 (read-only) - fixes to the EXP-002 E4 analysis module after round 1

Same repository, same rules as round 1 (`phaseA-task.md` in this directory). The **HARD RULE of round 1
applies unchanged**: do not open `benchmarks/results/EXP-002/RUN-*`, anything under
`DOCS/test_and_benchmark_results/`, anything under `DOCS/archive and reference from PRINet 3.0/`, the
validation transcripts or PR #33 comments. Do NOT run shell commands or edit files. Print your report to
stdout.

## What changed

Round 1 (Devin, findings F1-F8; Antigravity, none) led to these changes. The diffs against the
round-1 files are in this directory: `phaseA-round2-module.diff` and `phaseA-round2-tests.diff`. The
current files are
`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis/exp002_e4_analysis.py`
and `tests/test_exp002_e4_analysis.py`.

- F1: the tests' fast path now requires every global registration field (all but the run index) to match.
- F2: declined in code (the `*.json` inventory rule is `tools.reproduce.verify_manifest`'s, which the
  driver used); the docstring now says so.
- F3: `frozen_missing` / `frozen_extra` are re-derived: `python/prin/_public_api.py` and
  `python/prin/_deprecation.py` are read at `R`, must have their pre-registration section 1.1 digests,
  and `RC1_PUBLIC_API` is parsed as a literal tuple; the record's sets must equal
  `sorted(FROZEN - observed)` / `sorted(observed - FROZEN)` (`verify_api_surface`), else the record is
  inadmissible. You MAY open `python/prin/_public_api.py`, `python/prin/_deprecation.py` and the
  protocol section 1.1 table to check this.
- F4: owner-matrix row 4 copied verbatim; a test compares all seven rows with protocol section 5.3.
- F5: parse/decode/listing/read `OSError`s are wrapped into `AnalysisError` / `RecordError`.
- F6: approval date and run-name stamps are calendar-validated.
- F7: `GIT_*` environment variables are removed for every git query.
- F8: the registered claim-case key sets are used for the exact-key check.

## What to check

1. Is each fix correct and complete, with a test that would fail without it?
2. Did any fix introduce a regression or a new false pass / false fail? In particular: can the F3
   re-derivation reject a genuine driver record (ordering, duplicates in `observed_names`, the
   `sorted()` of a set), or accept an inconsistent one?
3. Any remaining defect from round 1's checklist that the fixes expose.

Report each finding as ID, severity, file:line, concrete scenario, suggested fix; then what you checked
and found sound. Do not include any experimental outcome.

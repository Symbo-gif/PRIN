# Cold review and self-audit (read-only) — EXP-002 E5 report, D1 records, and independent recount

Repository `C:\dev\PRIN`, branch `campaign/0159-exp002-e1`. Do NOT run shell commands, do NOT list directories, and do NOT edit any file. Read ONLY the exact file paths listed below. Print your complete review report to stdout.

## Hard rules on what you may and may not read

- **FORBIDDEN:** Do NOT open anything under `DOCS/test_and_benchmark_results/EXP-002/RUN-*/` (the retained publication roots and input snapshots), do NOT open `DOCS/archive and reference from PRINet 3.0/`, and do NOT open PR #33 comments.
- **PERMITTED (read these exact file paths directly — do not list directories):**
  1. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\report.md`
  2. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\analysis.md`
  3. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\report-manifest.json`
  4. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\README.md`
  5. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\preregistration.md`
  6. `C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\e2-review.md`
  7. `C:\dev\PRIN\DOCS\test_and_benchmark_results\EXP-002\analysis\summary.json`
  8. `C:\dev\PRIN\DOCS\test_and_benchmark_results\EXP-002\analysis\expected-vs-observed.md`
  9. `C:\dev\PRIN\DOCS\test_and_benchmark_results\EXP-002\analysis\coverage-and-deferrals.md`
  10. `C:\dev\PRIN\DOCS\test_and_benchmark_results\EXP-002\analysis\error-distributions.json`
  11. `C:\dev\PRIN\DOCS\test_and_benchmark_results\EXP-002\analysis\reproduction-comparisons.csv`
  12. `C:\dev\PRIN\EVIDENCE\0163\verification\regeneration\independent-recount.txt`
  13. `C:\dev\PRIN\EVIDENCE\0163\verification\regeneration\worktree-regeneration.txt`
  14. `C:\dev\PRIN\EVIDENCE\0163\verification\retained-bytes\retained-bytes-verification.txt`
  15. `C:\dev\PRIN\EVIDENCE\0163\verification\retained-bytes\listing-digests.txt`
  16. `C:\dev\PRIN\EVIDENCE\0163\verification\reconstruction\reconstruction.txt`
  17. `C:\dev\PRIN\DOCS\sessions\contingencies\2026-10-14-exp002-d1-s1-correction-implementation.md`
  18. `C:\dev\PRIN\DOCS\sessions\contingencies\2026-10-14-exp002-d1-s2-correction-audit.md`
  19. `C:\dev\PRIN\DOCS\sessions\contingencies\2026-10-14-exp002-d1-s3-correction-remediation.md`
  20. `C:\dev\PRIN\DOCS\sessions\contingencies\2026-10-14-exp002-d1-s4-correction-documentation.md`
  21. `C:\dev\PRIN\DOCS\sessions\contingencies\README.md`
  22. `C:\dev\PRIN\DOCS\sessions\phase-7\0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md`
  23. `C:\dev\PRIN\DOCS\sessions\phase-7\0164-exp003-e1-cpu-scaling-and-sweep-performance.md`
  24. `C:\dev\PRIN\DOCS\sessions\phase-7\README.md`
  25. `C:\dev\PRIN\DOCS\sessions\SESSION_REGISTER.md` (lines 1–15, lines 335–350, lines 555–605, and lines 730–775)
  26. `C:\dev\PRIN\DOCS\sphinx\parity_report.rst` (lines 1–265 and lines 390–455)
  27. `C:\dev\PRIN\DOCS\experiments\README.md` (lines 140–210)
  28. `C:\dev\PRIN\benchmarks\results\EXP-002\README.md`
  29. `C:\dev\PRIN\CHANGELOG.md` (lines 1–60)

## What to review (cite exact `file:line` for every finding)

1. **Numbers, denominators, and units:** Check that every count in `report.md`, the D1 briefs, `parity_report.rst`, `CHANGELOG.md`, and the updated READMEs/registers matches `summary.json`, `reproduction-comparisons.csv`, `report-manifest.json`, and `independent-recount.txt` (`175/175 api_symbols`, `172` callables + `3` constants; `172/172 legacy_api_names`; `62/62 claim_comparator_records` with `5/42/4/5/6`; H3 approved `21/39` equal / `18/39` differing across figures 5, 7, 8, 9, 10, 11, 12, 14, 15 in PDF and PNG, `11/11` tables; H3 sensitivity `5/39` equal / `34/39` differing; H4 `39/39` raw-identical; the `39` publication files never summed with the `7` analysis files; effect sizes and CIs marked not applicable).
2. **Reconstruction and retained-bytes accuracy:** Check that Step 1 (`39/39` retained files and `172/172` inputs per run), Step 2 (`8/8` analysis outputs + `report-manifest.json` regenerated in a detached worktree), and Step 3 (`39/39` PRIN-arm raw files, `25/39` reference-arm raw files and `39/39` normalized/sensitivity digests, recorded as a reconstruction limitation under §11.3 item 2) are reported accurately and consistently across `report.md` and the READMEs.
3. **Wording and spin:** Check that no root cause is asserted for the 18 H3 differences, that neither PRIN nor the reference generator is declared erroneous, that no difference is called "explained", "benign" or "cosmetic", that no F-item (`F1`, `F2`, `F4`) or DoD item is over-claimed, that maintainer verification is NOT claimed, that `cargo audit` and `gpu-cuda` are reported honestly as red, and that local validation is not called "CI green".
4. **D1 and register consistency:** Check that `0164` is `BLOCKED` in both its brief and `SESSION_REGISTER.md`, `0163` is `COMPLETE` in both, the four `2026-10-14-exp002-d1-s1..s4` briefs and `contingencies/README.md` are consistent, and `parity_report.rst` qualifies the `tools/reproduce.py` byte-comparability statements accurately.

For each finding: ID, severity (`High`/`Medium`/`Low`/`Info`), `file:line`, what is wrong, the evidence, and the exact fix. Then list what you checked and verified consistent.

# DV-044 S3 — Correction Remediation

**Date:** 2026-09-29 UTC
**Branch:** `hotfix/dv044-ledger-delta`
**Basis:** S2 independent audit
([`2026-09-29-dv044-s2-correction-audit.md`](2026-09-29-dv044-s2-correction-audit.md))
— verdict PASS-WITH-FINDINGS, seven findings (1×D3 code, 5×D4, 1×D3 index drift).

## Remediation per finding

| Finding | Fix |
|---|---|
| DV044-F1 (D3) lettered-PSR resolution | `parse_ledger` now zero-pads the **numeric part only** and re-attaches the single-letter suffix: `PSR-36a` → `036a-project-state.md`. Covered by `test_lettered_psr_delegation_resolves_zero_padded_numeric`. |
| DV044-F2 (D4) delegation scanned table cells | The `PSR-NNN §3` search now runs over non-table lines only, so a pointer literal inside a summary/reference cell is data, not a redirect. Covered by `test_psr_literal_inside_table_cell_cannot_redirect_delegation`. |
| DV044-F3 (D4) bare-substring marker + template gap | The delta marker must now start a (stripped) line — prose mentions cannot force the merge path. `DOCS/reports/TEMPLATE_Project_State_Report.md` §3 now documents both accepted forms (full snapshot, delegated delta) and the five-column local-table rule. |
| DV044-F4 (D4) `\\|` parity | `_markdown_cells` is a manual scan with escape parity: odd backslash runs escape the pipe (kept as `\|`-escaped content), even runs leave it a delimiter (`trail\\` ends a cell, `inner\|pipe` stays one cell). Covered by `test_escaped_backslash_before_delimiter_keeps_parity`. |
| DV044-F5 (D4) untested rejection paths | New tests cover duplicate IDs, invalid severity, empty required field, header-only canonical table + delegation, and `main()`'s exit-2 error path. |
| DV044-F6 (D4) `FileNotFoundError` outside try | `validate_commits`/`diff_ledgers` moved inside `main()`'s `try`, so a missing `git` exits 2 cleanly instead of an uncaught traceback → mislabeled exit 1. Covered by `test_main_returns_2_when_git_or_file_missing`. |
| DV044-F7 (D3) index drift | `DOCS/reports/README.md` now indexes `039-project-state.md`. The audit's `audits/README.md` half was stale — `038-wp038-audit.md` is already indexed (EDA-002 remediation); verified, no change needed. |
| Additional hardening | A canonical header with zero rows and no delta marker is now an explicit error (`canonical table has no rows`) instead of silently delegating. |

## Re-verification after remediation

- `pytest tests/test_check_deviation_ledger.py` — **12/12 pass** (6 S1 + 6 S3 tests).
- Exact original failing command —
  `python tools/check_deviation_ledger.py DOCS/reports/038-project-state.md DOCS/reports/039-project-state.md`
  — **exit 0**, "Compared 128 rows … with 142 rows".
- Regression pairs all green: 035→036 (118→120), 036→037 (120→128),
  036g→037 (120→128), 037→038 (128→128); single-arg 039 validates 142 rows.
- `python tools/check_dv_register_gates.py` — pass (44 DV rows / 198 session entries).
- `python tools/check_global_session_registration.py` — pass (17 EMA reports).
- `ruff check` / `ruff format` on both Python files — clean.
- Snyk Code (low threshold) on both modified Python files — **0 issues** each.
- `git diff --check` — clean.

## Verdict

S3 remediation **complete**; all seven S2 findings fixed (one half of F7 was
already closed upstream). The correction remains strictly fail-closed. S4
(documentation/closure + DV-044 register disposition) follows under the same
authorization; DV-044 is **not** closed yet.

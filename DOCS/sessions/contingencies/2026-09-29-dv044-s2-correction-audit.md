# DV-044 S2 Correction Audit — `hotfix/dv044-ledger-delta` @ `a07b7d5`

**Date:** 2026-09-29 UTC
**Auditor:** independent S2 reviewer (did not author the S1 correction `a07b7d5`)
**Scope:** `tools/check_deviation_ledger.py`, `tests/test_check_deviation_ledger.py`,
`DOCS/reports/039-project-state.md` §3.4, governance docs changed by S1
**Verdict:** PASS-WITH-FINDINGS (all findings D3/D4; none block the correction)

## Method

Read-only static audit of the S1 diff plus independent reproduction of the
execution claims by the orchestrating session (the auditor's environment had
no shell; every dynamic claim was re-executed on the S1 commit).

## Checklist

| Item | Result |
|---|---|
| A1 scope | PASS — `git show --stat a07b7d5` confirms only the 7 declared files |
| A3 tests in tandem | PASS — 6 tests with exact assertions on real rejection paths |
| A4/A8 data integrity | PASS — all 14 delta rows verified verbatim against the WP-038 audit §7 closure table and PSR-039 §3.1/§3.2; 128 inherited + 14 disjoint = 142 unique IDs |
| A5 quality | PASS — ruff `check`/`format` clean; docstrings on all symbols |
| A6 security | PASS — no shell/eval/secrets; subprocess uses absolute git + hex-validated commitish; canonical path built from `\d+[a-z]?` only (no traversal) |
| S1 execution claims | REPRODUCED — 6/6 tests pass; 038→039 exits 0 ("Compared 128 rows … 142"); 035→036 (118→120), 036→037 (120→128), 036g→037 (120→128), 037→038 (128→128) all pass; single-arg 039 validates 142 rows |

## Findings

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| DV044-F1 | D3 | Lettered-PSR delegation resolved `36a-project-state.md` instead of `036a-project-state.md` (`zfill(3)` on `"36a"` is a no-op). Latent — no live delegation to a lettered PSR; failure direction closed (exit 2). | **FIXED in S3** |
| DV044-F2 | D4 | `_DELEGATION_RE` scanned the whole §3 body including table cells; a `PSR-NNN §3` literal inside a cell could silently redirect the merge base. No live trigger. | **FIXED in S3** |
| DV044-F3 | D4 | Delta marker was a bare substring check; a literal mention inside a snapshot report would force the merge path and fail closed. Plus template gap: `TEMPLATE_Project_State_Report.md` documented only the full-snapshot form. | **FIXED in S3** |
| DV044-F4 | D4 | `_markdown_cells` treated `\\|` (escaped backslash + real delimiter) as an escaped pipe. Latent markdown edge only. | **FIXED in S3** |
| DV044-F5 | D4 | Implemented-but-untested rejection paths: duplicate ID, invalid severity/empty field, `OSError`→exit 2, header-only canonical table + delegation. | **FIXED in S3** |
| DV044-F6 | D4 | `validate_commits`/`subprocess.run` outside `main()`'s try: missing `git` propagated an uncaught `FileNotFoundError` → exit 1 mislabeled as consistency failure. | **FIXED in S3** |
| DV044-F7 | D3 | Index drift: `reports/README.md` index ended at PSR-038 (no 039). The `audits/README.md` half of the finding was stale — `038-wp038-audit.md` is already indexed (EDA-002 remediation). | **FIXED in S3** (reports index) |

## Verdict rationale

The S1 correction is faithful: the checker is strictly stricter (fail-closed on
every probed adversarial input class), the 14 delta rows reproduce their
sources verbatim, the arithmetic is exact, and no regression is detectable on
any historical report pair. All findings are latent hardening or adjacent-drift
items, none attributable to numerical or governance semantics. S3 remediation
per finding above; see
`DOCS/sessions/contingencies/2026-09-29-dv044-s3-correction-remediation.md`.

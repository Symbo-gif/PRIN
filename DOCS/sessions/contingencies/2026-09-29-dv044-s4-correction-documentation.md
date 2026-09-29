# DV-044 S4 — Correction Documentation

**Date:** 2026-09-29 UTC
**Branch:** `hotfix/dv044-ledger-delta`
**Status:** S1–S3 complete and recorded; **closure conditional** on merge to
`main` and a green governance CI gate (required by the same rule that
closed DV-036). DV-044 remains **OPEN** in the register until then.

## What DV-044 was

`tools/check_deviation_ledger.py` (python.yml governance gate) could not read
PSR-039's deviation ledger. PSR-039 uses local five-column finding tables
(§3.1, §3.2) plus a §3.3 delegation to PSR-038; the parser treated the local
tables as the six-column cumulative ledger, never followed the delegation,
and reported 128 inherited finding IDs missing — the exact command
`python tools/check_deviation_ledger.py DOCS/reports/038-project-state.md
DOCS/reports/039-project-state.md` exited 1. PSR-038 also claimed six WP-038
rows without supplying them as data. Not a numerical defect and not caused by
the r1 implementation.

## Correction summary

- **S1 (`a07b7d5`)** — PSR-039 §3.4 canonical six-column delta (14 rows:
  six WP-038 rows verbatim from audit `038-wp038-audit` §7, eight PSR-039
  rows verbatim from §3.1/§3.2 with statuses recast and disclosed). Parser
  made fail-closed: header-aware six-column parsing, escaped-pipe cells,
  explicit `**Cumulative ledger delta:**` marker required for merges,
  cyclic/missing delegation rejected, same-summary enforcement on overlaps.
  Six tandem tests. Exact comparison exit 0: 128→142.
- **S2** — independent non-author audit
  ([`2026-09-29-dv044-s2-correction-audit.md`](2026-09-29-dv044-s2-correction-audit.md)):
  **PASS-WITH-FINDINGS**, seven findings (1×D3 code, 5×D4, 1×D3 index
  drift). Auditor had no shell; every dynamic claim re-executed and
  reproduced by the orchestrating session.
- **S3 (`bb65aaa`)** — all seven findings remediated
  ([`2026-09-29-dv044-s3-correction-remediation.md`](2026-09-29-dv044-s3-correction-remediation.md)):
  lettered-PSR resolution (D3), non-table-only delegation search,
  line-start delta marker, escape-parity cell splitting, six additional
  tests covering previously implemented-but-untested rejection paths,
  `FileNotFoundError`→clean exit 2, PSR-039 index entry in
  `reports/README.md`, template now documents both ledger forms.
  12/12 tests, ruff clean, Snyk Code 0 issues on both Python files.

## Verification (re-executed post-S3)

- `pytest tests/test_check_deviation_ledger.py` — 12/12 pass.
- Exact failing command — **exit 0**, 128 vs 142 rows.
- Regression pairs green: 035→036 (118→120), 036→037 (120→128),
  036g→037 (120→128), 037→038 (128→128); single-arg 039 validates 142.
- `check_dv_register_gates.py`, `check_global_session_registration.py`,
  `git diff --check` — all pass.
- The checker is strictly *stricter* than before: no assertion weakened,
  no report skipped, no historical finding ID deleted or altered.

## Closure conditions still open

1. Land the correction on `main` (PR + required CI green).
2. Record the merge SHA and green governance checks here and in the
   register; only then may DV-044 be marked CLOSED.
3. EXP-001-r1 E3 remains blocked until this and DV-043's own
   merge/CI/nightly gates close and the M/R execution identity exists.

# DOCS/audits/ — Audit Reports

One report per Session-Cycle audit (S2), named `NNN-wpNNN-audit.md`
(cycle number, work package). Produced per the
[Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md);
format mirrors the PRINet 3.0 `Codebase_Assessment_Report.md`.

- Template: [`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md)
- Audits are append-only history: never edit a committed audit except to add
  the S3 closure table.
- Verdicts: `PASS` / `PASS-WITH-FINDINGS` / `FAIL` (any D1 finding ⇒ `FAIL`;
  feature work freezes until remediation clears it).

## Current reports

- [`001-wp001-audit.md`](001-wp001-audit.md) — WP-001 audit and CLEAN S3
  closure; eleven findings resolved (ten fixed, one approved amendment).
- [`002-wp002-audit.md`](002-wp002-audit.md) — WP-002 "Golden corpus and
  differential harness" audit (`PASS-WITH-FINDINGS`); four findings (F1–F4)
  resolved in S3 with a CLEAN delta re-audit.
- [`003-wp003-audit.md`](003-wp003-audit.md) — WP-003 "PyO3 and DLPack bridge
  spike" audit (`PASS-WITH-FINDINGS`); five findings (F1–F5) resolved in S3
  with a CLEAN delta re-audit (two approved plan/standard amendments #6 and
  #7).
- [`004-wp004-audit.md`](004-wp004-audit.md) — WP-004 "CubeCL fused mean-field
  RK4 spike" audit (`PASS-WITH-FINDINGS`); nine findings (F1–F4 D2, F5–F8 D3,
  F9 D4); S3 remediation pending.

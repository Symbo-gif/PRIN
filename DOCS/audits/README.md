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

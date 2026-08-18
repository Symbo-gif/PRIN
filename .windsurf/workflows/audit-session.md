---
description: S2 Audit session — compare repository state to the plan; produce the Audit Report
---

Authoritative definition: `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 (S2), §4 (checklist), §5 (severities).

1. Read the latest Project State Report, the open WP declaration, the active
   `DOCS/sessions/` brief, and `DOCS/PRIN_Project_Plan.md`. State the global
   session ID, session type (S2), and WP under audit.
2. **Read-only rule:** no source-code fixes in this session — findings only.
3. Create the report from `DOCS/audits/TEMPLATE_Audit_Report.md` as
   `DOCS/audits/NNN-wpNNN-audit.md`.
4. Work the checklist A1–A10, collecting command evidence for every claim:
   - A1 scope: diff the WP commit range vs the declaration.
   - A2 plan conformance: crate layering, no numerics in Python, explicit
     seeding, one-algorithm-one-implementation.
   - A3 tests-in-tandem + coverage (Testing Standards §5 audit hooks).
   - A4 parity: run parity cases for touched primitives.
   - A5 gates: fmt/clippy/ruff/mypy.
   - A6 security: bandit, ruff-S, cargo-audit, pip-audit, unsafe scan,
     secret scan.
   - A7 docs coverage: interrogate + cargo doc -D warnings.
   - A8 hygiene: TODO/FIXME/stub scan, `__all__` consistency.
   - A9 CI status: nothing has been pushed yet this cycle (Push and CI
     cadence, Development Workflow and Audit Standards §3, Plan amendment
     #28) — verify via local gate reproduction instead of a live CI run.
   - A10 artefact trail from the previous cycle.
5. Record every finding with ID `WPNNN-Fn`, severity D1–D4, evidence, and the
   violated clause.
6. Assign the verdict (PASS / PASS-WITH-FINDINGS / FAIL; any D1 ⇒ FAIL) and
   obtain maintainer acknowledgment.
7. Commit the Audit Report (`docs: WP-NNN audit report, verdict <V>`).
   **Commit only — do not push** (S2 is not the cycle's push point). Hand off
   to `/remediation-session` **even if there are zero findings**. A
   zero-finding S3 records no-change closure and delta verification; exact
   S1→S2→S3→S4 order permits no skipped session.

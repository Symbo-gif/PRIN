---
description: S3 Remediation session — fix audit findings only, then delta re-audit
---

Authoritative definition: `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 (S3), §5 (ledger rules).

1. Read the active numbered S3 brief and current cycle's Audit Report. State
   the global session ID, WP, and ordered finding list (D1 first). If there are
   zero findings, state that this is a mandatory no-change closure session.
2. **Findings-only rule:** no new features. Each fix commit references its
   finding ID (`fix: WP012-F3 restore 1/k normalization in sparse coupling`).
3. Fixes include a regression test where applicable (Testing Standards §4).
4. For findings that should not be fixed (justified deviation): draft a plan
   amendment PR (`DOCS/PRIN_Project_Plan.md` §8.3 amendment log + the changed
   section and affected session briefs), get maintainer approval, and mark the
   finding `AMENDED`.
5. D4 findings may be `CARRIED(1)` once, with maintainer approval, into the
   next WP's scope.
6. When all findings are resolved, perform the **delta re-audit** of touched
   areas (re-run the affected checklist rows with evidence) and append the
   closure table to the Audit Report.
7. Repeat 2–6 until the delta re-audit is CLEAN. With zero S2 findings,
   append no-change closure and independent delta-verification evidence.
// turbo
8. Re-run the full local gate to confirm nothing regressed:
   `cargo test --workspace; pytest tests/ -v -m "not slow and not gpu"`
9. **Commit only — do not push** (S3 is not the cycle's push point; see the
   Push and CI cadence, Development Workflow and Audit Standards §3, Plan
   amendment #28). Hand off to `/documentation-session`.

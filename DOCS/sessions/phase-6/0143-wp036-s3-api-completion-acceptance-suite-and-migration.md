# Session 0143 — WP-036 S3: Remediation — API completion, acceptance suite, and migration

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S3 — Remediation
**Predecessor:** [0142 — Audit](0142-wp036-s2-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0144 — Documentation](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md)
**Findings remediated:** WP036-F1 FIXED (5 new branch-coverage tests), WP036-F2 AMENDED (process deviation acknowledged). Delta re-audit: CLEAN.
**Authority:** Project Plan §6/§8 and **amendment #31**; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Scope note (amendment #31):** WP-036 covers the compatibility surface,
> freeze machinery, stubs, DV-012 bindings, and Migration Guide symbol table.

## Mission

Remediate every finding in `DOCS/audits/036-wp036-audit.md` against the WP-036
compatibility-surface scope; no feature work.

## Contract

- **Acceptance:** Every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  the 172-symbol resolve/smoke check and `verify_api_surface` stay green.
- **Non-goals:** The acceptance-suite port; final documentation prose or
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/036-wp036-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/036-wp036-audit.md` with FIXED / AMENDED / permitted
   CARRIED(1), commit/amendment reference, and delta evidence.
6. If S2 found nothing, perform and record a no-change delta verification so
   this mandatory session remains explicit and auditable.

## Required outputs

- All finding commits and regression tests.
- Completed closure table and CLEAN delta re-audit.
- Full local gate green with no newly introduced deviation.

## Prohibited

New features, opportunistic refactors, unapproved scope changes, unresolved
D1/D2 findings, or a second carry of any D4.

## Exit gate

Every finding is closed and delta re-audit is CLEAN. Hand off to S4; if not,
repeat remediation/delta verification within this session until clean.

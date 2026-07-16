# Session 0197 — WP-039 S3: Remediation — Stable-release evidence closure

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** WP-039  
**Session type:** S3 — Remediation  
**Predecessor:** [0196 — Comprehensive audit](0196-wp039-s2-stable-release-evidence-closure.md)  
**Successor:** [0198 — Documentation and release](0198-wp039-s4-stable-release-evidence-closure.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement only final release metadata/verification automation, conduct the comprehensive Definition-of-Done audit, remediate every finding, publish final documentation/state evidence, and execute the approved 1.0.0 release ceremony.

## Contract

- **Acceptance:** All twelve Definition-of-Done items pass; deviation ledger is empty; campaign and Parity Reports are published; signed/checksummed 1.0.0 artefacts install on supported platforms.
- **Non-goals:** New features, unregistered science, or unresolved findings.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/039-wp039-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/039-wp039-audit.md` with FIXED / AMENDED / permitted
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

# Session 0147 — WP-037 S3: Remediation — Documentation, notebooks, paper, and Parity Report draft

**Status:** COMPLETE (2026-09-15) — all eight S2 findings closed after the WP037-F1 corrective second delta; delta re-audit CLEAN, see `DOCS/audits/037-wp037-audit.md` §7.
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1  
**Execution unit:** WP-037  
**Session type:** S3 — Remediation  
**Predecessor:** [0146 — Audit](0146-wp037-s2-documentation-notebooks-paper-and-parity-report-draft.md)  
**Successor:** [0148 — Documentation](0148-wp037-s4-documentation-notebooks-paper-and-parity-report-draft.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Complete Sphinx guides/API, four notebooks, docs.rs links, paper artefact wiring, and evidence-backed draft Parity Report from pre-campaign validation.

## Contract

- **Acceptance:** Docs build warning-free; examples/notebooks execute; claims cite artefacts; draft clearly labels validation vs confirmatory campaign results.
- **Non-goals:** Publishing 1.0 or replacing Phase 7 pre-registration.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/037-wp037-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/037-wp037-audit.md` with FIXED / AMENDED / permitted
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

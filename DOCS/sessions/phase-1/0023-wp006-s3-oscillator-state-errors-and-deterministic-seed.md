# Session 0023 — WP-006 S3: Remediation — Oscillator state, errors, and deterministic seed

**Status:** COMPLETE  
**Roadmap phase:** 1 — Dynamics core  
**Execution unit:** WP-006  
**Session type:** S3 — Remediation  
**Predecessor:** [0022 — Audit](0022-wp006-s2-oscillator-state-errors-and-deterministic-seed.md)  
**Successor:** [0024 — Documentation](0024-wp006-s4-oscillator-state-errors-and-deterministic-seed.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement struct-of-arrays oscillator state, phase wrap/safe difference, amplitude and derivative guards, typed errors, and the single counter-based Seed authority.

## Contract

- **Acceptance:** Unit/property/parity tests cover N=1, invalid shapes/ranges, wrap semantics, clamps, reproducibility, and strict-checks behavior.
- **Non-goals:** Dynamics equations, integrators, or hidden global RNG.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/006-wp006-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/006-wp006-audit.md` with FIXED / AMENDED / permitted
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

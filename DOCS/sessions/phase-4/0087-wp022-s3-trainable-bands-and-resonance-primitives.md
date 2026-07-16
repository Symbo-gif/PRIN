# Session 0087 — WP-022 S3: Remediation — Trainable bands and resonance primitives

**Status:** PLANNED  
**Roadmap phase:** 4 — Trainable stack and Torch bridge  
**Execution unit:** WP-022  
**Session type:** S3 — Remediation  
**Predecessor:** [0086 — Audit](0086-wp022-s2-trainable-bands-and-resonance-primitives.md)  
**Successor:** [0088 — Documentation](0088-wp022-s4-trainable-bands-and-resonance-primitives.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement Burn DiscreteDeltaThetaGamma, ResonanceLayer, parameter/state contracts, and differentiable forward references.

## Contract

- **Acceptance:** Forward and gradient reference tests pass; serialization, shape, dtype, and numerical guards are covered.
- **Non-goals:** Inhibition, HEP, optimizers, or full models.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/022-wp022-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/022-wp022-audit.md` with FIXED / AMENDED / permitted
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

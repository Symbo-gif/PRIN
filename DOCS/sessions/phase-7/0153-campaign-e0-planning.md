# Session 0153 — Campaign E0: Campaign planning — Approve and freeze Phase 7 campaign plan

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** Campaign  
**Session type:** E0 — Campaign planning  
**Predecessor:** [0152 — Documentation](../phase-6/0152-wp038-s4-rc1-packaging-and-phase-6-gate.md)  
**Successor:** [0154 — Pre-registration](0154-exp001-e1-golden-trajectory-numerical-parity.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Create the dependency-ordered campaign plan, experiment registry, shared artefact schema, hardware matrix, resource budget, and approval record.

## Contract

- **Acceptance:** All eight experiments, dependencies, owners, hardware, budgets, and stop conditions are approved before any pre-registration/execution begins.
- **Non-goals:** Executing an experiment or viewing campaign outcomes.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/standards/Experimentation_Standards.md`
- `DOCS/experiments/TEMPLATE_Preregistration.md`

## Entry conditions

- Phases 0–6 and WP-038 are closed; RC1 and all required tooling exist.
- The deviation ledger has no unresolved D1/D2 finding.

## Expected work

1. Create and obtain approval for `DOCS/experiments/campaign-plan.md`.
2. Register EXP-001…EXP-008 in the exact Session Register order, dependencies,
   owners, hardware/backend matrix, seeds policy, resource/storage budgets,
   shared schemas, and campaign-wide stop/escalation rules.
3. Confirm raw artefacts are append-only and every report has a deterministic
   regeneration path and SHA-256 manifest.
4. Confirm C1–C3 conclusion reversals feed into a D1 correction cycle before
   any later campaign session proceeds.

## Required outputs

Approved/frozen campaign plan, capacity allocation, experiment directory
skeletons, and explicit authorization to begin EXP-001 E1.

## Exit gate

The maintainer approval is recorded before the first pre-registration begins.

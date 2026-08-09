# Session 0030 — WP-008 S2: Audit — Basic integrators

**Status:** COMPLETE  
**Roadmap phase:** 1 — Dynamics core  
**Execution unit:** WP-008  
**Session type:** S2 — Audit  
**Predecessor:** [0029 — Coding](0029-wp008-s1-basic-integrators.md)  
**Successor:** [0031 — Remediation](0031-wp008-s3-basic-integrators.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement Integrator abstraction plus Euler, RK4, and adaptive RK45 with explicit buffers and numerical guards.

## Contract

- **Acceptance:** Golden trajectories pass at rtol=1e-6/atol=1e-8; RK4 order h^4 and RK45 tolerance properties hold; failure paths are typed.
- **Non-goals:** Exponential, Krylov, or multi-rate methods.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- Coding/Testing/Documentation security and coverage gates

## Entry conditions

- S1 has claimed its exit gate and supplied an evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/008-wp008-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Golden trajectories pass at rtol=1e-6/atol=1e-8; RK4 order h^4 and RK45 tolerance properties hold; failure paths are typed.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP008-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/008-wp008-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

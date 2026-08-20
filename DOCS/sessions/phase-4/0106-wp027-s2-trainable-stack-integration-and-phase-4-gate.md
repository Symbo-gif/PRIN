# Session 0106 — WP-027 S2: Audit — Trainable-stack integration and Phase 4 gate

**Status:** COMPLETE
**Roadmap phase:** 4 — Trainable stack and Torch bridge
**Execution unit:** WP-027
**Session type:** S2 — Audit
**Predecessor:** [0105 — Coding](0105-wp027-s1-trainable-stack-integration-and-phase-4-gate.md)  
**Successor:** [0107 — Remediation](0107-wp027-s3-trainable-stack-integration-and-phase-4-gate.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Run controlled temporal CLEVR-N integration, full gradcheck, bridge profiling, serialization, and trainable API acceptance.

## Contract

- **Acceptance:** PhaseTracker reaches at least the registered 3.0 IP threshold in validation runs; gradchecks green; bridge overhead <5%; Phase 4 tag gate passes without treating pilot data as campaign evidence.
- **Non-goals:** Final scientific publication claims.

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

1. Create `DOCS/audits/027-wp027-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: PhaseTracker reaches at least the registered 3.0 IP threshold in validation runs; gradchecks green; bridge overhead <5%; Phase 4 tag gate passes without treating pilot data as campaign evidence.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP027-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/027-wp027-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

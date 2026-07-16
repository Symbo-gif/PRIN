# Session 0094 — WP-024 S2: Audit — Oscillator-aware optimizers

**Status:** PLANNED  
**Roadmap phase:** 4 — Trainable stack and Torch bridge  
**Execution unit:** WP-024  
**Session type:** S2 — Audit  
**Predecessor:** [0093 — Coding](0093-wp024-s1-oscillator-aware-optimizers.md)  
**Successor:** [0095 — Remediation](0095-wp024-s3-oscillator-aware-optimizers.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement SCALR, RIP, SyncGD, order-parameter feedback, state serialization, and thin torch-side optimizer contracts.

## Contract

- **Acceptance:** Update equations match references; deterministic resume/state tests pass; invalid metrics fail safely.
- **Non-goals:** End-to-end models or experiment statistics.

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

1. Create `DOCS/audits/024-wp024-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Update equations match references; deterministic resume/state tests pass; invalid metrics fail safely.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP024-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/024-wp024-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

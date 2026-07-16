# Session 0126 — WP-032 S2: Audit — Daemon/evaluation integration and Phase 5 gate

**Status:** PLANNED  
**Roadmap phase:** 5 — Daemon and experiment tooling  
**Execution unit:** WP-032  
**Session type:** S2 — Audit  
**Predecessor:** [0125 — Coding](0125-wp032-s1-daemon-evaluation-integration-and-phase-5-gate.md)  
**Successor:** [0127 — Remediation](0127-wp032-s3-daemon-evaluation-integration-and-phase-5-gate.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Integrate daemon, hooks, MOT, temporal, stats, and adversarial APIs; complete provider and latency acceptance.

## Contract

- **Acceptance:** Daemon latency target and MOT equivalence pass; optional hardware skips are justified; Phase 5 tag gate is green.
- **Non-goals:** Final benchmark campaign or release.

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

1. Create `DOCS/audits/032-wp032-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Daemon latency target and MOT equivalence pass; optional hardware skips are justified; Phase 5 tag gate is green.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP032-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/032-wp032-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

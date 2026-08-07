# Session 0018 — WP-005 S2: Audit — ORT backends, wheel matrix, and Phase 0 gate

**Status:** COMPLETE  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-005  
**Session type:** S2 — Audit  
**Predecessor:** [0017 — Coding](0017-wp005-s1-ort-backends-wheel-matrix-and-phase-0-gate.md)  
**Successor:** [0019 — Remediation](0019-wp005-s3-ort-backends-wheel-matrix-and-phase-0-gate.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Probe ONNX Runtime CPU/DirectML/VitisAI providers; complete three-OS abi3 wheel smoke matrix; consolidate all Phase 0 spike decisions and golden-corpus readiness.

## Contract

- **Acceptance:** F5 fallback is proven; wheels install without compiler; all Phase 0 go/no-go decisions are approved; corpus is committed; Phase 0 tag gate is green.
- **Non-goals:** Daemon runtime implementation or public release.

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

1. Create `DOCS/audits/005-wp005-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: F5 fallback is proven; wheels install without compiler; all Phase 0 go/no-go decisions are approved; corpus is committed; Phase 0 tag gate is green.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP005-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/005-wp005-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

## S2 closure

- Audit Report: `DOCS/audits/005-wp005-audit.md`
- Verdict: **PASS-WITH-FINDINGS**
- Findings: `WP005-F1` (D3), `WP005-F2` (D3), `WP005-F3` (D4), `WP005-F4` (D4)
- Maintainer acknowledgment: pending

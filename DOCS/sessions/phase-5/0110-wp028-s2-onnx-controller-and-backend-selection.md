# Session 0110 — WP-028 S2: Audit — ONNX controller and backend selection

**Status:** PLANNED  
**Roadmap phase:** 5 — Daemon and experiment tooling  
**Execution unit:** WP-028  
**Session type:** S2 — Audit  
**Predecessor:** [0109 — Coding](0109-wp028-s1-onnx-controller-and-backend-selection.md)  
**Successor:** [0111 — Remediation](0111-wp028-s3-onnx-controller-and-backend-selection.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement controller state/control types, ONNX model validation, provider detection (VitisAI→DirectML→CPU), and deterministic fallback.

## Contract

- **Acceptance:** Outputs match 3.0 references across available providers; missing-provider paths fall back safely; model SHA-256 is verified.
- **Non-goals:** Background runtime/threading.

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

1. Create `DOCS/audits/028-wp028-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Outputs match 3.0 references across available providers; missing-provider paths fall back safely; model SHA-256 is verified.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP028-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/028-wp028-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

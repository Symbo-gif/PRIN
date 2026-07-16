# Session 0042 — WP-011 S2: Audit — Phase 1 Python API and dynamics integration

**Status:** PLANNED  
**Roadmap phase:** 1 — Dynamics core  
**Execution unit:** WP-011  
**Session type:** S2 — Audit  
**Predecessor:** [0041 — Coding](0041-wp011-s1-phase-1-python-api-and-dynamics-integration.md)  
**Successor:** [0043 — Remediation](0043-wp011-s3-phase-1-python-api-and-dynamics-integration.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Expose completed dynamics/metrics through prin-py and thin prin API; port corresponding acceptance tests and complete Phase 1 end-to-end parity.

## Contract

- **Acceptance:** No Python numerics; mapped 3.0 symbols resolve; non-trainable dynamics parity/property suites are fully green; Phase 1 tag gate passes.
- **Non-goals:** Advanced integrators, simulation engine, or training APIs.

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

1. Create `DOCS/audits/011-wp011-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: No Python numerics; mapped 3.0 symbols resolve; non-trainable dynamics parity/property suites are fully green; Phase 1 tag gate passes.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP011-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/011-wp011-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

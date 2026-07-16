# Session 0130 — WP-033 S2: Audit — Unified benchmark runner and category migration

**Status:** PLANNED  
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1  
**Execution unit:** WP-033  
**Session type:** S2 — Audit  
**Predecessor:** [0129 — Coding](0129-wp033-s1-unified-benchmark-runner-and-category-migration.md)  
**Successor:** [0131 — Remediation](0131-wp033-s3-unified-benchmark-runner-and-category-migration.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement benchrunner CLI, shared configuration/environment capture, and migrate all 62 scripts into nine topic categories without schema changes.

## Contract

- **Acceptance:** Every legacy benchmark has a traceability row and executable replacement; JSON schema compatibility and ≥10-iteration timing rules are tested.
- **Non-goals:** Drawing conclusions from final measurements.

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

1. Create `DOCS/audits/033-wp033-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Every legacy benchmark has a traceability row and executable replacement; JSON schema compatibility and ≥10-iteration timing rules are tested.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP033-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/033-wp033-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

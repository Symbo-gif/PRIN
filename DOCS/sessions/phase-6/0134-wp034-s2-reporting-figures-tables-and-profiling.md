# Session 0134 — WP-034 S2: Audit — Reporting, figures, tables, and profiling

**Status:** PLANNED  
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1  
**Execution unit:** WP-034  
**Session type:** S2 — Audit  
**Predecessor:** [0133 — Coding](0133-wp034-s1-reporting-figures-tables-and-profiling.md)  
**Successor:** [0135 — Remediation](0135-wp034-s3-reporting-figures-tables-and-profiling.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Port benchmark reports/leaderboards, 15 figures, 11 LaTeX fragments, and torch/Rust profiling integration.

## Contract

- **Acceptance:** Stored 3.0 artefacts generate byte-comparable expected outputs or documented deterministic normalization; examples and schema tests pass.
- **Non-goals:** Re-running scientific training.

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

1. Create `DOCS/audits/034-wp034-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: Stored 3.0 artefacts generate byte-comparable expected outputs or documented deterministic normalization; examples and schema tests pass.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP034-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/034-wp034-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.

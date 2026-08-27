# Session 0144B — WP-036B S2: Audit — Acceptance suite port (core, dynamics, model stack, subconscious)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S2 — Audit
**Predecessor:** [0144A — Coding](0144A-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md)
**Successor:** [0144C — Remediation](0144C-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8 and amendment #31; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of WP-036B S1: the ported first-half acceptance suite.

## Contract

- **Acceptance:** as 0144A — every ported test passes on CPU across the matrix;
  no weakened assertion; every tolerance annotation is hazard-attributed and in
  the Parity Report; GPU-only skips are justified.
- **Non-goals:** any source fix (S3 owns that).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- WP-036B S1 handoff note and commit range
- `DOCS/standards/Testing_Standards.md` §1, §3, §4

## Entry conditions

- S1 has claimed its exit gate and supplied its evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/036b-wp036b-audit.md` from the template.
2. Execute A1–A10 with command evidence.
3. Diff every ported test against its reference original; confirm only imports
   changed except where a tolerance annotation is present, and that each such
   annotation cites a specific amendment (#14/#16/#17/#25) and a Parity Report
   line.
4. Confirm no skipped test lacks a maintainer-approved quarantine issue.
5. Independently re-run the ported subset on this host; spot-check counts
   against the reference (`def test_` per file).
6. Give each finding `WP036B-Fn`, severity D1–D4, evidence, violated clause,
   remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036b-wp036b-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.

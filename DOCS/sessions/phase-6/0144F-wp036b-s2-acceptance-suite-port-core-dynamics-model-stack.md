# Session 0144F — WP-036B S2: Audit — Acceptance suite port (core, dynamics, model stack, subconscious)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S2 — Audit
**Predecessor:** [0144E6 — subconscious and consolidation](0144E6-wp036b-s1-subconscious-and-consolidation.md)
**Successor:** [0144G — Remediation](0144G-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#35; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of the aggregate WP-036B S1 strict port across
`0144E`+`0144E1`–`0144E6`: 13 reference files, 498 source test functions, and
8,570 reference lines.

## Contract

- **Acceptance:** as 0144E — every ported test passes on CPU across the matrix;
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
5. Independently re-run the complete ported subset on this host; reconcile all
   **498** source `def test_` functions against the amendment-#35 per-file table
   (do not substitute the initial 481-collected result), and confirm all 17
   `test_clevr_n.py` functions collect after the `benchmarks.clevr_n` repair.
6. Confirm every compatibility behavior added by `0144E1`–`0144E6` is owned by
   Rust-backed layers with thin PyO3/Python delegation, not copied-test shims or
   Python numerics.
7. Give each finding `WP036B-Fn`, severity D1–D4, evidence, violated clause,
   remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036b-wp036b-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.

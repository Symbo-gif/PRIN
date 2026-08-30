# Session 0144H — WP-036B S4: Documentation — Acceptance suite port (core, dynamics, model stack, subconscious)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S4 — Documentation
**Predecessor:** [0144G — Remediation](0144G-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md)
**Successor:** [0144I — Coding](0144I-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md)
**Authority:** Project Plan §6/§8 and amendment #31; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Document the WP-036B ported acceptance-suite half and issue its Project State
Report.

## Contract

- **Acceptance:** `tests/README.md` and any touched READMEs updated; CHANGELOG
  entry; Parity Report tolerance table current; docs gates green; PSR issued.
- **Non-goals:** functional feature work; WP-036C.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Documentation_Standards.md` §7
- `DOCS/audits/036b-wp036b-audit.md` including its CLEAN closure table

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update `tests/README.md` (ported-suite inventory, counts, marker policy) and
   every other directory README touched in S1–S3.
2. Update `CHANGELOG.md`; update `DOCS/sphinx/parity_report.rst` with the
   consolidated WP-036B tolerance-annotation table; update the Migration Guide
   if any symbol behavior note changed.
3. Run documentation, link, quality, security, and the ported-subset gates.
4. Write `DOCS/reports/036b-project-state.md` with measured metric trends
   (ported test count, coverage, tolerance annotations, discoveries),
   cumulative deviation ledger, amendments, risks, and trajectory verdict.
5. Confirm WP-036C (session 0144I) entry conditions and record maintainer
   approval before its S1 begins.
6. Update this session's status and the master register from verified evidence.

## Required outputs

- Updated READMEs and docs; CHANGELOG entry; warning-free docs gates.
- Approved `DOCS/reports/036b-project-state.md`.
- Green local gates over the batched WP-036B range.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed and local gates green. WP-036B is closed; only then
may WP-036C (0144I) begin.

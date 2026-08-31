# Session 0144P — WP-036C S4: Documentation — Acceptance suite port (integration, y-series, kernels; DV-025)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S4 — Documentation
**Predecessor:** [0144O — Remediation](0144O-wp036c-s3-acceptance-suite-port-integration-y-series-kernels.md)
**Successor:** [0145 — Coding](0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md)
**Authority:** Project Plan §6/§8 and amendments #31/#36; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> Renumbered `0144L` → `0144P` by plan amendment #36.

> This is a prospective execution contract, not completion evidence.

## Mission

Document the completed acceptance-suite port, close DV-025, issue the WP-036C
Project State Report, and hand Phase 6 to WP-037.

## Contract

- **Acceptance:** all touched READMEs updated; CHANGELOG entry; Parity Report
  tolerance table complete for the whole ported suite; docs gates green; DV-025
  closed in the register; PSR issued; WP-037 (0145) re-confirmed as the
  successor with its entry conditions checked.
- **Non-goals:** functional feature work; RC1 publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Documentation_Standards.md` §7 and Versioning/Release Standards
- `DOCS/audits/036c-wp036c-audit.md` including its CLEAN closure table

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update `tests/README.md` (full ported-suite inventory ≈1,670 tests, marker
   and tolerance policy), `parity/README.md`, and every other touched README.
2. Update `CHANGELOG.md`; finalize `DOCS/sphinx/parity_report.rst` tolerance
   table; update `DOCS/sphinx/migration_guide.rst` for DV-025 and any behavior
   notes; ensure `DOCS/baselines/wp001_api_traceability.md` is regenerated.
3. Close DV-025 in `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` with evidence.
4. Run documentation, link, quality, security, and full-suite gates.
5. Write `DOCS/reports/036c-project-state.md` with measured metric trends,
   cumulative deviation ledger, amendments, risks, DoD item 1–2 status, and
   trajectory verdict. Re-confirm WP-037 scope/approval.
6. Update this session's status and the master register from verified evidence.
   This closes the WP-036 / WP-036A / WP-036B / WP-036D / WP-036C group.

## Required outputs

- Updated READMEs and all relevant user/scientist docs.
- CHANGELOG entry; warning-free docs/docstring coverage evidence.
- Approved `DOCS/reports/036c-project-state.md`.
- Green local gates over the batched WP-036C range.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed and local gates green. The WP-036 group is closed;
only then may session 0145 (WP-037 S1) begin.

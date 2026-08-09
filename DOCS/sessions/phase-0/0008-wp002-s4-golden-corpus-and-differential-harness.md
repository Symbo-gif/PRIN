# Session 0008 — WP-002 S4: Documentation — Golden corpus and differential harness

**Status:** COMPLETE  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-002  
**Session type:** S4 — Documentation  
**Predecessor:** [0007 — Remediation](0007-wp002-s3-golden-corpus-and-differential-harness.md)  
**Successor:** [0009 — Coding](0009-wp003-s1-pyo3-and-dlpack-bridge-spike.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement the versioned PRINet 3.0 golden-trajectory generator, schema/manifest validators, corpus loader, differential pytest harness, and hypothesis strategies.

## Contract

- **Acceptance:** Approximately 500 seeded float64 cases cover every model × coupling mode × basic integrator; immutable source/version metadata and SHA-256 manifest exist; harness detects planted deviations at mandated tolerances.
- **Non-goals:** Implementing PRIN numerical kernels or changing archived reference outputs.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/002-wp002-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/002-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/002-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

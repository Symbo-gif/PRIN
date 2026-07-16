# Session 0198 — WP-039 S4: Documentation and release — Stable-release evidence closure

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** WP-039  
**Session type:** S4 — Documentation and release  
**Predecessor:** [0197 — Remediation](0197-wp039-s3-stable-release-evidence-closure.md)  
**Successor:** Project complete  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement only final release metadata/verification automation, conduct the comprehensive Definition-of-Done audit, remediate every finding, publish final documentation/state evidence, and execute the approved 1.0.0 release ceremony.

## Contract

- **Acceptance:** All twelve Definition-of-Done items pass; deviation ledger is empty; campaign and Parity Reports are published; signed/checksummed 1.0.0 artefacts install on supported platforms.
- **Non-goals:** New features, unregistered science, or unresolved findings.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/039-wp039-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/039-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Record project completion and obtain maintainer approval of the stable-release outcome.
6. Verify the Phase 7 exit gate and, when approved, prepare/tag and publish `v1.0.0` per release standards.
7. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/039-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

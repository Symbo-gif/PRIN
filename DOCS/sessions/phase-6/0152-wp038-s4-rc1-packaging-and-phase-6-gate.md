# Session 0152 — WP-038 S4: Documentation — RC1 packaging and Phase 6 gate

**Status:** COMPLETE  
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1  
**Execution unit:** WP-038  
**Session type:** S4 — Documentation  
**Predecessor:** [0151 — Remediation](0151-wp038-s3-rc1-packaging-and-phase-6-gate.md)  
**Successor:** [0153 — Campaign planning](../phase-7/0153-campaign-e0-planning.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Build/smoke all wheel/sdist targets, validate release security/OIDC configuration, run full CI/repro, and publish 1.0.0-rc1 after approval.

## Contract

- **Acceptance:** No-compiler installs pass across OS families; all CI/security/repro gates green; RC1 artefacts and checksums published; Phase 7 entry criteria satisfied.
- **Non-goals:** Stable 1.0.0 release or unregistered experiments.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/038-wp038-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/038-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Verify the Phase 6 exit gate and, when approved, prepare/tag `v1.0.0-rc.1` per release standards.
7. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/038-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

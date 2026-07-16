# Session 0124 — WP-031 S4: Documentation — Temporal experiments, statistics, and adversarial tooling

**Status:** PLANNED  
**Roadmap phase:** 5 — Daemon and experiment tooling  
**Execution unit:** WP-031  
**Session type:** S4 — Documentation  
**Predecessor:** [0123 — Remediation](0123-wp031-s3-temporal-experiments-statistics-and-adversarial-tooling.md)  
**Successor:** [0125 — Coding](0125-wp032-s1-daemon-evaluation-integration-and-phase-5-gate.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement fair PT-vs-SA training framework, Hungarian similarity, temporal metrics, bootstrap CIs, Welch tests, FLOPs, and FGSM/PGD orchestration.

## Contract

- **Acceptance:** Statistical routines match trusted references; matched-budget controls are enforced; attack bounds and deterministic multi-seed behavior are tested.
- **Non-goals:** Running the final scientific campaign.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/031-wp031-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/031-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/031-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

# Session 0044 — WP-011 S4: Documentation — Phase 1 Python API and dynamics integration

**Status:** PLANNED  
**Roadmap phase:** 1 — Dynamics core  
**Execution unit:** WP-011  
**Session type:** S4 — Documentation  
**Predecessor:** [0043 — Remediation](0043-wp011-s3-phase-1-python-api-and-dynamics-integration.md)  
**Successor:** [0045 — Coding](../phase-2/0045-wp012-s1-exponential-and-multi-rate-integrators.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Expose completed dynamics/metrics through prin-py and thin prin API; port corresponding acceptance tests and complete Phase 1 end-to-end parity.

## Contract

- **Acceptance:** No Python numerics; mapped 3.0 symbols resolve; non-trainable dynamics parity/property suites are fully green; Phase 1 tag gate passes.
- **Non-goals:** Advanced integrators, simulation engine, or training APIs.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/011-wp011-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/011-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Verify the Phase 1 exit gate and, when approved, prepare/tag `v0.2.0-alpha.1` per release standards.
7. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/011-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

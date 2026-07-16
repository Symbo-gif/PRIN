# Session 0068 — WP-017 S4: Documentation — Kernel architecture and CPU references

**Status:** PLANNED  
**Roadmap phase:** 3 — GPU kernels  
**Execution unit:** WP-017  
**Session type:** S4 — Documentation  
**Predecessor:** [0067 — Remediation](0067-wp017-s3-kernel-architecture-and-cpu-references.md)  
**Successor:** [0069 — Coding](0069-wp018-s1-fused-mean-field-rk4-kernel.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Establish prin-kernels backend abstraction, CubeCL build path, device/dtype dispatch, preallocated buffers, and authoritative CPU references.

## Contract

- **Acceptance:** One-algorithm-one-implementation invariant is demonstrable; unsupported devices fall back safely; no runtime compiler dependency; equivalence harness is operational.
- **Non-goals:** Production GPU kernels.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/017-wp017-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/017-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/017-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

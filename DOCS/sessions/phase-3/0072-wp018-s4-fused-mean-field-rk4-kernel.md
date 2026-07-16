# Session 0072 — WP-018 S4: Documentation — Fused mean-field RK4 kernel

**Status:** PLANNED  
**Roadmap phase:** 3 — GPU kernels  
**Execution unit:** WP-018  
**Session type:** S4 — Documentation  
**Predecessor:** [0071 — Remediation](0071-wp018-s3-fused-mean-field-rk4-kernel.md)  
**Successor:** [0073 — Coding](0073-wp019-s1-sparse-k-nn-and-pac-kernels.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Productionize fused mean-field RK4 with hierarchical f64-accumulated reductions and CUDA/wgpu dispatch.

## Contract

- **Acceptance:** All supported shapes/dtypes match CPU tolerance; N=1M device-event benchmark meets approved Phase 0 target; no hidden synchronization defects.
- **Non-goals:** Sparse k-NN or discrete-band step.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/018-wp018-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/018-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/018-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

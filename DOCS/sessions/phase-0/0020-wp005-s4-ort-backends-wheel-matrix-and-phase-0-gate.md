# Session 0020 — WP-005 S4: Documentation — ORT backends, wheel matrix, and Phase 0 gate

**Status:** PLANNED  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-005  
**Session type:** S4 — Documentation  
**Predecessor:** [0019 — Remediation](0019-wp005-s3-ort-backends-wheel-matrix-and-phase-0-gate.md)  
**Successor:** [0021 — Coding](../phase-1/0021-wp006-s1-oscillator-state-errors-and-deterministic-seed.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Probe ONNX Runtime CPU/DirectML/VitisAI providers; complete three-OS abi3 wheel smoke matrix; consolidate all Phase 0 spike decisions and golden-corpus readiness.

## Contract

- **Acceptance:** F5 fallback is proven; wheels install without compiler; all Phase 0 go/no-go decisions are approved; corpus is committed; Phase 0 tag gate is green.
- **Non-goals:** Daemon runtime implementation or public release.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/005-wp005-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/005-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Verify the Phase 0 exit gate and, when approved, prepare/tag `v0.1.0-alpha.1` per release standards.
7. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/005-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

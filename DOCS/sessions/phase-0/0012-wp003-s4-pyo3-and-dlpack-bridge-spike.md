# Session 0012 — WP-003 S4: Documentation — PyO3 and DLPack bridge spike

**Status:** READY  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-003  
**Session type:** S4 — Documentation  
**Predecessor:** [0011 — Remediation](0011-wp003-s3-pyo3-and-dlpack-bridge-spike.md)  
**Successor:** [0013 — Coding](0013-wp004-s1-cubecl-fused-rk4-spike.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Prototype zero-copy Torch↔Rust DLPack exchange, batched boundary calls, ownership/lifetime handling, dtype/device validation, and microbenchmark instrumentation.

## Contract

- **Acceptance:** CPU and available CUDA round trips are correct; ownership and error paths are tested; measured boundary overhead supports <5% training-step target or a documented go/no-go amendment.
- **Non-goals:** Production trainable layers or per-step Python crossings.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/003-wp003-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/003-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/003-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

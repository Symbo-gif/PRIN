# Session 0036 — WP-009 S4: Documentation — PAC, coupling topologies, and phase k-NN

**Status:** COMPLETE
**Roadmap phase:** 1 — Dynamics core  
**Execution unit:** WP-009  
**Session type:** S4 — Documentation  
**Predecessor:** [0035 — Remediation](0035-wp009-s3-pac-coupling-topologies-and-phase-k-nn.md)  
**Successor:** [0037 — Coding](0037-wp010-s1-phase-metrics-and-chimera-measures.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement PAC, mean-field/local/sparse coupling, topology enums/builders, normalization rules, and rayon phase-sort k-NN index.

## Contract

- **Acceptance:** Golden parity covers all modes; 1/N versus 1/k is explicit; sparse/full equivalence and k-NN edge properties pass.
- **Non-goals:** GPU kernels or trainable discrete bands.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/009-wp009-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/009-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/009-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

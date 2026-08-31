# Session 0144D — WP-036A S4: Documentation — Trainable compatibility layers (`prin-train` extension)

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S4 — Documentation
**Predecessor:** [0144C — Remediation](0144C-wp036a-s3-trainable-compatibility-layers-prin-train-extension.md)
**Successor:** [0144E — Coding](0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8 and amendment #33; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Document the WP-036A trainable compatibility layers; update the Migration Guide,
`prin.nn.deferred_layers` docstrings, Sphinx API pages, and crate READMEs;
issue the WP-036A Project State Report declaring WP-036B as the next session.

## Contract

- **Acceptance:** Every touched directory README updated; CHANGELOG, `.pyi`
  stubs, Sphinx API pages, and Migration Guide current; docs gates green;
  PSR `DOCS/reports/036a-project-state.md` issued and declaring WP-036B.
- **Non-goals:** The acceptance-suite port; final documentation prose or
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31, #33
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Documentation_Standards.md` §7
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- `DOCS/audits/036a-wp036a-audit.md` including its closure table
- WP-036A S1 handoff note

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, `.pyi` stubs, Sphinx API pages,
   and the Migration Guide for the 13 symbols now delivered as real
   implementations.
3. Run documentation, example, link, quality, security, and relevant full-suite
   gates.
4. Write `DOCS/reports/036a-project-state.md` with measured metric trends,
   cumulative deviation ledger, and WP-036B declaration.
5. Update this session's status and the master register only from verified
   evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/036a-project-state.md`.
- Fully green CI.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may WP-036B S1 (session 0144E) begin.

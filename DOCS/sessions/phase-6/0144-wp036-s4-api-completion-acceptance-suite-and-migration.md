# Session 0144 — WP-036 S4: Documentation — API completion, acceptance suite, and migration

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S4 — Documentation
**Predecessor:** [0143 — Remediation](0143-wp036-s3-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0144A — Coding](0144A-wp036a-s1-trainable-compatibility-layers-prin-train-extension.md)
**Artefacts:** `DOCS/reports/036-project-state.md` (PSR-036), CHANGELOG entry, session registers updated.
**Authority:** Project Plan §6/§8 and **amendment #31**; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Scope note (amendment #31):** WP-036 covers the compatibility surface,
> freeze machinery, stubs, DV-012 bindings, and Migration Guide symbol table.
> Its registered successor is WP-036B S1 (session `0144A`), not WP-037.

## Mission

Document the WP-036 compatibility surface, `prin._deprecation` machinery,
stubs, DV-012 bindings, and Migration Guide symbol table; issue the WP-036
Project State Report; activate WP-036B.

## Contract

- **Acceptance:** Every touched directory README updated; CHANGELOG, stubs,
  Sphinx API pages, and Migration Guide current; docs gates green; PSR
  `DOCS/reports/036-project-state.md` issued and declaring WP-036B; DV-005
  recorded as a scoping decision; DV-012 closed.
- **Non-goals:** The acceptance-suite port; final documentation prose or
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/036-wp036-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/036-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare WP-036B (session `0144A`) from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/036-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.

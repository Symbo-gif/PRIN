---
description: S4 Documentation session — READMEs, changelog, docs gates, Project State Report
---

Authoritative definition: `DOCS/standards/Documentation_Standards.md` §7 and `Development_Workflow_and_Audit_Standards.md` §3 (S4).

1. Read the active numbered S4 brief; confirm the delta re-audit is CLEAN.
   State the global session ID, WP, and every directory touched during S1–S3.
2. Update the README of every touched directory (contents, phase status,
   usage). New directories must have READMEs.
3. Update `CHANGELOG.md` `[Unreleased]` with all user-visible changes
   (Keep-a-Changelog categories).
4. Complete API docs: docstrings/rustdoc for all new/changed symbols; update
   the relevant `DOCS/sphinx/api/` pages; update
   `DOCS/sphinx/migration_guide.rst` for any PRINet 3.0-visible change;
   regenerate `_prin_core.pyi` stubs if the extension API changed.
5. Verify documentation gates:
// turbo
6. `interrogate -c pyproject.toml python/prin`
// turbo
7. `cargo doc --workspace --no-deps` (with RUSTDOCFLAGS="-D warnings")
8. Build Sphinx if pages changed:
   `sphinx-build -b html DOCS/sphinx DOCS/sphinx/_build/html`
9. Write `DOCS/reports/NNN-project-state.md` from the template: trajectory
   position, metric trends (fill the table with measured numbers), cumulative
   deviation ledger, amendments, risks, and the **next WP declaration** (get
   maintainer approval recorded in the report).
10. Update the completed S1–S4 brief statuses and
    `DOCS/sessions/SESSION_REGISTER.md` only from committed evidence; mark the
    exact listed successor READY after maintainer approval.
11. Run the consistency sweep over plan ↔ standards ↔ session briefs/register
    ↔ READMEs ↔ workflows for anything the cycle changed.
12. Commit all artefacts (`docs: close cycle NNN (WP-NNN)`), verify CI is
    fully green. The cycle is closed; begin only the successor named by the
    active brief.

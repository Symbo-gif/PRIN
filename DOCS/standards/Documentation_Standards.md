# PRIN Documentation Standards

**Status:** Normative. Documentation is part of the definition of done for
every PR that adds or changes public API.

---

## 1. Principles

1. **Docs ship with code.** A PR changing public API updates docstrings/rustdoc,
   the relevant Sphinx page, and (if a PRINet 3.0 symbol is affected) the
   Migration Guide — in the same PR. Every Session Cycle additionally closes
   with a dedicated Documentation Session (S4, §7).
2. **Scientific claims are cited.** Equations, capacity claims (e.g. ~7-item
   θ/γ binding), and algorithmic complexity statements reference the paper or
   literature.
3. **Every source directory has a README** (PRINet 3.0 convention, kept)
   describing purpose, contents, and phase status.
4. **Examples must run.** Doctest/`Examples` blocks are executed in CI where
   practical; notebooks must run end-to-end.

## 2. API documentation

### 2.1 Rust

- **Coverage threshold: 100% of public items.** `#![warn(missing_docs)]` on
  every crate + CI `RUSTFLAGS="-D warnings"` makes undocumented public items a
  build failure; `cargo doc --no-deps` must be clean under
  `RUSTDOCFLAGS="-D warnings"`.
- Crate-level docs (`lib.rs`) state scope, PRINet 3.0 rebuild target, and
  preserved numerical invariants.
- Math in rustdoc uses inline notation consistent with the paper
  (φ, ω, K, R for order parameter).
- Published to docs.rs on release; Sphinx links to them.

### 2.2 Python

- **Coverage thresholds: 100% of public symbols; ≥95% of all callables**
  (matching-and-exceeding the 84% measured in the PRINet 3.0 audit). Enforced
  by ruff pydocstyle `D` rules (Google convention) and
  `interrogate --fail-under 95` in CI; measured per cycle in the Project State
  Report.
- **Google-style docstrings** on all public symbols, with `Args`, `Returns`,
  `Raises`, and `Examples` sections; shapes documented for every tensor
  argument (e.g. `Shape: (B, N)`), units for physical quantities (radians, Hz).
- Module docstrings state purpose and rebuild provenance.
- Type stubs (`_prin_core.pyi`) regenerate with every extension API change.

## 3. Project documentation (Sphinx, `DOCS/sphinx/`)

Required documents (project plan §11):

| Document | Owner phase |
|---|---|
| Getting Started Tutorial | 1/6 |
| Architecture Guide | 1 (living) |
| Migration Guide (PRINet 3.0 → PRIN): symbol-by-symbol mapping + tolerance notes | incremental, final in 6 |
| Kernel Architecture (single-source CubeCL design) | 3 |
| Parity Report (§7 program results) | 6, pre-release |
| Capacity Analysis, Coupling Topologies API reference (ported) | 6 |
| API reference (`DOCS/sphinx/api/`, autodoc) | continuous |

Conventions:

- Sphinx + MyST Markdown, `furo` theme, ReadTheDocs deployment.
- Benchmark reports are written to `DOCS/test_and_benchmark_results/`
  (gitignored). The archived plan's lowercase `docs/` convention is superseded:
  Windows filesystems are case-insensitive, so `docs/` and `DOCS/` cannot
  coexist — PRIN uses the single `DOCS/` tree (governance at the root, Sphinx
  site in `DOCS/sphinx/`), and all references must use the exact casing `DOCS`.
- Notebooks live in `notebooks/`, numbered, with a stated runtime budget.

## 4. Governance documents (`DOCS/`)

- `DOCS/PRIN_Project_Plan.md` is the authoritative plan; changes require
  maintainer approval and a changelog entry in the document header.
- Standards documents (this directory) are normative; amendments follow the
  same review bar as code (PR + review).
- `DOCS/archive and reference from PRINet 3.0/` is read-only reference
  material; never link runtime behavior to it.

## 5. Changelog and release notes

- `CHANGELOG.md` follows Keep a Changelog; every user-visible change lands
  under `[Unreleased]` in the same PR.
- Release notes summarize: new symbols, performance deltas (with benchmark
  evidence), parity status, and migration actions.

## 6. Style

- Line length 88 for Markdown prose where practical; fenced code blocks always
  carry a language tag.
- American English; sentence-case headings; oscillator terminology follows the
  paper glossary (δ/θ/γ bands, PAC, chimera, order parameter R).

## 7. The Documentation Session (S4)

S4 is the mandatory closing session of every Session Cycle (Development
Workflow Standards §3). Its checklist — all items required before the cycle
may close:

1. **Directory READMEs.** Every directory whose contents changed in S1–S3 has
   its README updated to describe the new state (contents, phase status,
   usage). New directories get a README on creation. All READMEs must comply
   with the readability requirements in
   [`Executive_Readability_Audit_Governance_and_Methodology.md`](Executive_Readability_Audit_Governance_and_Methodology.md)
   §6 (answer what/why/how/status; proportional length; scannable structure;
   no WP-number soup or unbroken walls of text).
2. **CHANGELOG.** All user-visible changes of the cycle are recorded under
   `[Unreleased]`, Keep-a-Changelog categories.
3. **API docs.** Docstrings/rustdoc complete for all new/changed symbols;
   coverage gates pass (§2); Sphinx builds clean **against a freshly deleted
   or newly created `DOCS/sphinx/_build` output directory** (Phase 4
   analytics R30/PA4-F2 — Sphinx's incremental build does not detect an
   `automodule`-sourced docstring change underneath an unmodified `.rst`
   page, so a reused build directory can silently mask a genuine warning;
   see `AGENTS.md`'s verification one-liner for the clean-build command);
   new symbols appear in the correct `DOCS/sphinx/api/` page; Migration
   Guide updated for any PRINet 3.0-visible change.
4. **Executable examples.** New doctest/`Examples` blocks run; affected
   notebooks re-execute (or are explicitly marked stale with an issue).
5. **Project State Report.** Written to `DOCS/reports/NNN-project-state.md`
   per the template: trajectory position, metric trends, cumulative deviation
   ledger, amendments, risks, and the next WP declaration. **Quote, do not
   paraphrase (Phase 4 analytics R32).** When the next-WP declaration names
   specific symbols, classes, or file paths, quote them directly from their
   governing normative source — the next session's own brief
   (`DOCS/sessions/`) mission text, or the Rebuild Planning Document's
   symbol-mapping table row (Project Plan §1) — rather than restating them
   from memory. Four consecutive-phase recurrences of the same declaration-
   text-drift pattern (amendments #18–#20, #29) were all caught and
   correctly resolved by a later session's `grep` against the archived
   PRINet 3.0 reference tree; quoting the source directly at authoring time
   avoids the drift instead of relying on a later audit to catch it. If
   direct quoting is impractical for a declaration that necessarily
   previews not-yet-written work, at minimum `grep` the archived PRINet 3.0
   reference tree for any named class before including it.
6. **Session-plan status.** Update the completed briefs and
   `DOCS/sessions/SESSION_REGISTER.md` only from committed evidence; activate
   the approved successor; amend future briefs/traceability if the trajectory
   changed through an approved amendment.
7. **Consistency sweep.** Cross-references (plan ↔ standards ↔ session briefs
   ↔ READMEs ↔ workflows) affected by the cycle are updated; stale statements
   found later are D4 audit findings (D2 if they could authorize wrong work).
8. **Documentation accuracy sweep.** Explicit verification that all
   documentation in touched areas matches the current code state:
   (a) every README in a directory whose source code changed in S1–S3
   accurately describes the current module contents, public API, and usage;
   (b) every rustdoc code example in touched crates compiles (verified via
   `cargo test --doc` on touched crates or the full workspace);
   (c) every index/README file in `DOCS/` subdirectories (`DOCS/audits/`,
   `DOCS/reports/`, `DOCS/sessions/`, `DOCS/ANALYTICS/`) lists all current
   files and is free of stale entries. Stale documentation found by the
   next cycle's audit is a D4 finding (D2 if it could authorize incorrect
   work), per the consistency-sweep rule in item 7.
9. **Phase-closing cross-cutting document currency (Phase 3 analytics R22).**
   At every phase-closing S4 — the WP-N session whose Project State Report
   declares the phase exit gate — explicitly verify and, if stale, update:
   (a) `DOCS/PRIN_Project_Plan.md` §6's roadmap-table completion marker for
   the closing phase; (b) `DOCS/experiments/README.md`'s file index against
   the actual directory listing; (c) `DOCS/sessions/SESSION_REGISTER.md`'s
   Global Sessions section against the actual Executive Audit/Executive
   Mathematical Audit report list. These three documents summarize *across*
   WP-N cycles and global sessions, so neither item 8 above (scoped to a
   single WP-N cycle's touched areas) nor the EA/EMA closing checklist
   (`Executive_Audit_Governance_and_Methodology.md` §5,
   `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8, which
   are scoped to the global session's own touched files) is positioned to
   own their currency — the structural gap that produced PA2-F1/PA2-F2
   (Phase 2 analytics) and PA3-F1/PA3-F2 (Phase 3 analytics). This item
   applies only at phase-closing S4, not every WP-N S4, so it is not
   re-litigated every cycle. Stale entries found by a later session are a
   D3 finding on the Project Plan (D4 on the other two), per the
   consistency-sweep rule in item 7.

   **Deferral requires a recorded rationale (Phase 4 analytics R27).** When
   this item's verification finds a genuine, stale gap, the session must
   either fix it before closing or record an explicit, reviewable rationale
   for deferring it instead — a bare "recommended for next cycle" note is
   not a rationale and does not satisfy this item. A one-line documentation
   edit with no code risk defaults to "fix now," matching the disposition
   already established for the identical situation by Phase 3's R21. This
   item's own imperative text ("explicitly verify and, if stale, update")
   is not satisfied by identifying a gap and then not acting on it in the
   same session without recording why: a later session finding an item
   deferred without a recorded rationale treats it as a repeat of the
   original finding class (this item failing to close its own gap), not as
   a new, lesser finding. The same rule applies, by cross-reference, to the
   EA/EMA closing checklists (`Executive_Audit_Governance_and_Methodology.md`
   §5, `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8):
   any global-session closing-checklist item that identifies a genuine gap
   in that session's own required artefacts must be fixed before the
   session closes, or deferred only with an explicit, reviewable rationale
   recorded in the session's report.

S4 produces no functional code changes. If a documentation task exposes a code
defect, it is logged for the next cycle (or triggers a hotfix per Workflow
Standards §7 if severe).

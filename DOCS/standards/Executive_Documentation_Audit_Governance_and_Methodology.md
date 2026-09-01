# PRIN Executive Documentation Audit Governance and Methodology

**Status:** Normative. This document establishes the governance, scope,
methodology, findings classification, remediation protocols, and reporting
requirements for **Executive Documentation Audit (EDA) Sessions** in the PRIN
project.

**Relationship to existing governance:** This document extends — and never
overrides — the [Executive Audit Governance and Methodology](Executive_Audit_Governance_and_Methodology.md),
[Executive Mathematical Audit Governance and Methodology](Executive_Mathematical_Audit_Governance_and_Methodology.md),
[Development Workflow and Audit Standards](Development_Workflow_and_Audit_Standards.md),
[Documentation Standards](Documentation_Standards.md), and
[Official Project Plan](../PRIN_Project_Plan.md). It is registered as a
global session type, following the same "global session, outside the planned
sequence" registration precedent established for Executive Audit (EA)
sessions by amendment #15 and Executive Mathematical Audit (EMA) sessions by
amendment #23.

---

## 1. Purpose and Scope

An **Executive Audit Session** (EA) verifies the full project across 10
dimensions (E1–E10), of which E5 (Standards & Documentation Adherence) is one
dimension among many. An **Executive Mathematical Audit** (EMA) independently
re-derives mathematical claims with tool-executed recomputation. Neither audit
type is purpose-built for the systematic, deep inspection of documentation
quality, consistency, and completeness that a large phase produces.

An **Executive Documentation Audit (EDA) Session** fills that gap. It is a
project-level audit dedicated to **systematic verification of documentation
artefacts** produced during a phase or series of work packages. EDA sessions:

1. Verify that every documentation artefact produced during the audited scope
   (READMEs, CHANGELOG entries, session briefs, Project State Reports, audit
   reports, analytics reports, standards cross-references, Sphinx pages,
   directory indexes, execution plans, and the Deferred Validation Register)
   is **accurate, complete, internally consistent, and current** relative to
   the code and governance state it describes.
2. Detect **documentation drift** — stale references, missing entries,
   cross-reference inconsistencies, index/README files that no longer match
   their directory contents, and Project State Reports whose cumulative
   deviation ledgers have gaps or fabrications.
3. Verify **process compliance** — that every S4 documentation session
   actually executed its mandatory checklist items (Documentation Standards
   §7), that CHANGELOG entries match committed changes, and that session
   registers accurately reflect completed work.
4. **Do not replace** EA sessions' E5 dimension or the per-cycle S4
   documentation sessions. EDA is an additional, independent verification
   layer applied at a coarser granularity — typically mid-phase or at
   phase boundaries — when the volume of documentation produced by a string
   of work packages warrants a dedicated, focused audit.

### 1.1 When an EDA session is warranted

An EDA session is warranted when:

1. **Mid-phase audit point:** A phase has produced a large volume of
   documentation across multiple work packages (typically 5+ WPs or 50+
   commits), and a dedicated documentation-quality check would provide value
   before the phase closes.
2. **Phase boundary:** At phase close, complementing the EA session's E5
   dimension with a deeper, documentation-focused audit.
3. **Maintainer discretion:** The maintainer requests a documentation audit
   at any point, e.g. after a string of rapid WPs with complex scope
   decompositions or when documentation drift is suspected.

This first EDA session (EDA-001) is triggered by condition 1: Phase 6 has
produced 8 completed work packages (WP-033 through WP-036D), ~90+ commits,
and 136 documentation files changed with 20,745 insertions since EA-006.

---

## 2. Audit Dimensions

An EDA session examines documentation across 8 dimensions:

| ID | Dimension | Assessment Scope |
|---|---|---|
| **D1** | **CHANGELOG Accuracy & Completeness** | Every user-visible change in the audited scope has a CHANGELOG entry under `[Unreleased]`; entries use correct Keep-a-Changelog categories; no orphan entries for changes that were reverted; no missing entries for committed changes. |
| **D2** | **Session Register & Brief Consistency** | `SESSION_REGISTER.md` accurately reflects every session's status (`PLANNED`, `IN_PROGRESS`, `COMPLETE`); session briefs exist for every completed session; brief statuses match the register; execution-plan documents are consistent with the briefs they decompose. |
| **D3** | **Project State Report Integrity** | PSRs exist for every completed WP; cumulative deviation ledger tables are complete and internally consistent (verified by `tools/check_deviation_ledger.py`); PSR declarations quote their governing sources per Documentation Standards §7 item 5; metric trends are accurate. |
| **D4** | **Directory README & Index Currency** | Every directory whose contents changed in the audited scope has an up-to-date README; directory indexes (e.g. `DOCS/experiments/README.md`, `DOCS/audits/README.md`) list all current files and are free of stale entries; crate READMEs accurately describe current module contents. |
| **D5** | **Cross-Reference Consistency** | Standards documents cross-reference each other correctly; audit reports reference correct session IDs and commit hashes; plan amendments are correctly logged and cross-referenced; workflow files reference current templates and standards. |
| **D6** | **Deferred Validation Register Accuracy** | DV register items reflect current status; closed items have dated closure narratives; re-audit gates are accurate; review log entries are complete; the mechanical enforcement tool (`tools/check_dv_register_gates.py`) passes. |
| **D7** | **Sphinx & API Documentation Build Health** | Sphinx HTML build passes with 0 warnings against a freshly deleted build directory (per R30 clean-build discipline); docstring coverage meets thresholds (Python 100% public / ≥95% overall; Rust 100% public); rustdoc builds clean under `RUSTDOCFLAGS='-D warnings'`. |
| **D8** | **Plan Amendment & Governance Traceability** | Plan amendments are sequentially numbered, correctly logged in the plan's amendment table, and cross-referenced from the findings/recommendations that triggered them; session register's global sessions section lists all EA/EMA reports; the plan's roadmap table accurately marks phase completion. |

---

## 3. Severity Classification

EDA findings use the same D1–D4 scale as Executive Audits
(`Executive_Audit_Governance_and_Methodology.md` §3), with
documentation-specific definitions:

| Severity | Definition | Required Response |
|---|---|---|
| **D1 — Trajectory Breach** | Documentation that could authorize incorrect work: a README describing an API that no longer exists, a PSR declaring a WP complete when it is not, a CHANGELOG entry for a change that was reverted. | Immediate fix required. Freezes progress until resolved. |
| **D2 — Subsystem Deviation** | Missing required documentation: a completed WP with no PSR, a session with no brief, a directory whose README is absent or describes the wrong contents, a DV register item whose status contradicts the evidence. | Fix in remediation step before audit session closure. |
| **D3 — Process / Quality Deviation** | Documentation inconsistency or staleness: a cross-reference to a renamed document, an index file with stale entries, a session register row whose status doesn't match the actual state, a missing CHANGELOG entry for a user-visible change. | Fix in remediation step or log with explicit future WP placeholder. |
| **D4 — Hygiene / Documentation** | Minor formatting issues, typographical errors, inconsistent heading levels, missing language tags on code blocks, or cosmetic inconsistencies that cannot authorize incorrect work. | Fix during remediation / documentation alignment step. |

---

## 4. Executive Documentation Audit Workflow Lifecycle

An EDA Session proceeds through 7 mandatory sequential tasks, mirroring the
EA lifecycle (`Executive_Audit_Governance_and_Methodology.md` §4):

```
Task 1: Governance & Methodology Definition (this document, first session)
   │     or confirmation of existing methodology (subsequent sessions)
   ▼
Task 2: Documentation Inventory & Scope Delineation
   │     (enumerate all documentation artefacts in the audited scope)
   ▼
Task 3: Multi-Dimension Audit Execution (D1–D8)
   │     (systematic verification of each dimension)
   ▼
Task 4: Executive Documentation Audit Report Compilation
   │
   ▼
Task 5: Remediation Planning (Immediate vs Pass-Forward)
   │
   ▼
Task 6: Remediation Execution & Verification
   │
   ▼
Task 7: Final Documentation, Session Register/Traceability, Git Commit
```

**Governance principles** (identical intent to EA §2, restated for the
documentation-audit context):

1. **Evidence-based verification.** Every finding is backed by a command
   output, file comparison, or direct inspection — never by recollection or
   assertion.
2. **Counterexample-first.** A finding that documentation is stale or
   inaccurate is demonstrated by showing the specific discrepancy (e.g.
   "README lists file X which does not exist" or "CHANGELOG is missing an
   entry for commit Y").
3. **No silent gaps.** Missing documentation is always recorded as a finding,
   never treated as acceptable and never omitted from the report.
4. **Clean verification gate.** An EDA session cannot close until every D1/D2
   finding is `FIXED` or `AMENDED`, matching EA §2.5 and Development
   Workflow Standards §1's "deviations never accumulate" principle.

---

## 5. Reporting and Artifact Rules

1. **Executive Documentation Audit Report:** saved as
   `DOCS/audits/EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_NNN.md` using
   `DOCS/audits/TEMPLATE_Executive_Documentation_Audit_Report.md`. Findings
   use the `D-FN` identifier prefix (distinct from EA's `E-FN` and EMA's
   `M-FN`) to keep the three audit types' finding histories independently
   traceable.
2. **Session registration:** EDA sessions are global sessions, registered in
   `DOCS/sessions/SESSION_REGISTER.md` under a dedicated "Global sessions —
   Executive Documentation Audits" section, outside the planned 0001–0198
   sequence, following the identical precedent plan amendment #15 established
   for EA sessions (`EDA-NNN` identifiers, never renumbering planned
   sessions).
3. **Remediation plan:** embedded in the EDA report or saved alongside it if
   extensive, identical convention to EA §5.2.
4. **Project State Report:** cross-referenced or updated to reflect EDA
   conclusions, identical convention to EA §5.4.
5. **Recurrence:** an EDA session is warranted at the points described in
   §1.1. At minimum, one EDA session per phase when the phase produces 5+
   work packages or 50+ commits of documentation changes.
6. **Closing checklist:** As a global session outside every WP-N S4
   checklist, an EDA session's own file changes are not otherwise swept by
   R7's documentation-accuracy net (Documentation Standards §7). Before this
   session closes, it must therefore itself: (a) add or update a
   `CHANGELOG.md` `[Unreleased]` entry for every user-visible change the
   session makes, and (b) run the relevant quality gates on every file it
   newly commits, before Task 7 (Final Documentation, Session Register/
   Traceability, Git Commit).
7. **Deferral requires a recorded rationale** (per Documentation Standards §7
   item 9's phase-closing requirement, applied here to this session type's
   own closing checklist). If this checklist identifies a genuine gap in
   this session's required artefacts, the session must fix it before closing
   or record an explicit, reviewable rationale for deferring it — a bare
   "recommended for next session" note is not sufficient.

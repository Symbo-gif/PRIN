# PRIN Development Workflow and Audit Standards

**Status:** Normative. This document defines the **PRIN Session Cycle** — the
self-auditing collaborative workflow through which all PRIN work is executed —
and the audit machinery that detects and corrects any deviation from the
planned trajectory in `DOCS/PRIN_Project_Plan.md`. It is modeled on the
workflow that produced PRINet 3.0 (per-milestone build → full repository audit
→ fix change-set → assessment report; see the archived
`Codebase_Assessment_Report.md`).

---

## 1. Principles

1. **Work is executed in cycles, never ad hoc.** Every unit of work passes
   through the four sessions of §3 **in exact order**. No session may be
   skipped, merged, or reordered.
2. **The plan is the trajectory.** `DOCS/PRIN_Project_Plan.md` (roadmap,
   requirements, architecture rules) plus the standards in `DOCS/standards/`
   define the intended state at every point. An **audit** compares reality to
   that trajectory; a **deviation** is any difference.
3. **Deviations never accumulate.** Every audit finding is either (a) corrected
   in the remediation session of the same cycle, or (b) formally absorbed into
   the plan by an approved plan amendment. There is no third state; untracked
   drift is prohibited.
4. **Audits are evidence-based.** Every claim in an audit report is backed by a
   command output, test result, coverage number, or file citation — never by
   recollection.
5. **The cycle is self-documenting.** Each cycle leaves durable artefacts:
   an Audit Report (`DOCS/audits/`), a Project State Report (`DOCS/reports/`),
   updated READMEs, and a CHANGELOG entry. A reader with no chat history must
   be able to reconstruct project state from artefacts alone.

## 2. Unit of work: the work package

- A **work package (WP)** is a coherent slice of a roadmap phase (e.g.
  "Phase 1: `prin-dynamics::state` + `models` with parity cases"), small
  enough to complete in one cycle, defined **before** S1 begins.
- Each WP is numbered `WP-NNN` (zero-padded, monotonic) and declared in the
  Project State Report of the preceding cycle (or, for WP-001, in the plan).
- A WP declaration states: scope (files/crates/modules), the plan sections it
  advances, its acceptance criteria (tests + parity cases + docs), and its
  explicit non-goals.

## 3. The Session Cycle

```
S1 Coding ──► S2 Audit ──► S3 Remediation ──► S4 Documentation ──► next WP
 (code+tests    (state vs      (fix all           (READMEs, changelog,
  in tandem)     plan)          findings)          project state report)
```

### S1 — Coding session

**Entry:** WP declared; previous cycle fully closed (S4 artefacts committed).

**Rules:**
- Tests are written **in tandem** with code — same session, same commits, per
  the Testing Standards §1. A commit that adds executable behavior without its
  tests is non-conforming.
- All code follows the Coding Standards (typing, docstrings at threshold,
  security rules) *at write time*, not retrofitted in S3/S4.
- Scope discipline: only the declared WP scope. Discovered-but-out-of-scope
  work is logged in the session log as a candidate for a future WP, not done.

**Exit criteria (all required):**
- Local gate green (Coding Standards §5).
- New/changed code at ≥95% coverage; gradcheck/parity/property tests included
  where the Testing Standards require them.
- WP acceptance criteria met to the author's knowledge.
- **Parity-evidence disposition stated** (Phase 2 analytics R15): for every new
  numerical primitive in the WP, the handoff note states whether a directly
  comparable PRINet 3.0 reference exists, backed by a stated grep/import
  check against the archived reference — never an unverified assertion that
  "no reference exists." If a reference exists, either parity evidence is
  included in this S1 commit, or its deferral is stated with a reason
  reviewable at S2. This closes the root cause behind WP-012/WP-013/WP-014's
  recurring D1 pattern (Testing Standards §1.3 already requires parity cases
  be written or identified before the algorithm lands; this item makes the
  check itself, not just the tests, an explicit exit gate).

### S2 — Audit session

**Entry:** S1 exit criteria claimed.

**Rules:**
- The audit is **read-only with respect to source code**: no fixes during S2,
  only findings. (Reproducing an issue is allowed; committing a fix is not.)
- The audit compares the repository's current state against the **audit
  checklist** (§4), which is derived mechanically from the plan and standards.
- Every finding gets an ID (`WPNNN-FN`), a severity (§5), evidence, and the
  violated plan/standard clause.

**Output:** an Audit Report at `DOCS/audits/NNN-wpNNN-audit.md` following
`DOCS/audits/TEMPLATE_Audit_Report.md` (the PRINet 3.0 assessment-report
format: executive summary table → methodology → detailed findings → issues
table → verdict).

**Verdicts:** `PASS` (no findings above D4), `PASS-WITH-FINDINGS` (findings
recorded, none D1), or `FAIL` (any D1, or systemic drift). A `FAIL` verdict
freezes all new feature work until S3 clears it.

### S3 — Remediation session

**Entry:** Audit Report committed.

**Rules:**
- Work **only** on audit findings, in severity order (D1 → D4). No new
  features.
- Each fix commits with the finding ID in the message
  (`fix: WP012-F3 restore 1/k normalization in sparse coupling`).
- Findings that cannot or should not be fixed require a **plan amendment**:
  a PR editing `DOCS/PRIN_Project_Plan.md` (or the relevant standard) with
  maintainer approval, recorded in the amendment log of the plan and
  cross-referenced from the finding. The trajectory moves only by amendment —
  never silently.

**Exit criteria:** every finding is either `FIXED` (with a regression test
where applicable) or `AMENDED` (with an approved amendment reference); a
**delta re-audit** of the touched areas confirms closure and appends a closure
table to the Audit Report. Cycles repeat S3 ↔ delta re-audit until clean.
**S3 remains mandatory when S2 finds zero deviations:** it records a no-change
closure and independent delta verification. Exact order means no session is
skipped merely because it requires no corrective source edit.

### S4 — Documentation session

**Entry:** delta re-audit clean.

**Mandatory actions (Documentation Standards §7 details each):**
1. Update the README of **every directory touched** in S1–S3.
2. Update `CHANGELOG.md` (`[Unreleased]`) with all user-visible changes.
3. Update docstrings/rustdoc and Sphinx pages for public API changes; update
   the Migration Guide for any PRINet 3.0 symbol affected.
4. Verify documentation gates: docstring coverage at threshold, Sphinx build
   clean, doc examples execute.
5. Write the **Project State Report** at `DOCS/reports/NNN-project-state.md`
   (template: `DOCS/reports/TEMPLATE_Project_State_Report.md`): plan position,
   deviation ledger status, metric trends (tests/coverage/parity/benchmarks),
   risks, and the **declaration of the next WP**.

**Exit criteria:** all four artefact classes committed; CI fully green. The
cycle is then **closed** and the next WP may begin S1.

### Campaign trigger

When the final roadmap phase's last WP closes, the project enters the
**Experimentation and Benchmarking Campaign** governed by the
[Experimentation Standards](Experimentation_Standards.md). No campaign
experiment may begin before all phases are complete and audited, and no
experiment may run without a pre-registration (expected results and failure
conditions documented **before** execution).

## 4. The audit checklist

The S2 audit examines, at minimum (extend as the plan grows — the checklist
lives in the template and is version-controlled with it):

| # | Dimension | Reference |
|---|---|---|
| A1 | WP scope: everything declared is present; nothing undeclared shipped | WP declaration |
| A2 | Plan conformance: architecture rules (crate layering, "one algorithm one implementation", no numerics in Python, explicit state/seeding) | Plan §4 |
| A3 | Test conformance: tests written in tandem; coverage ≥95% new code; required parity/property/gradcheck present; no weakened/skipped tests | Testing Standards |
| A4 | Numerical parity: golden-corpus cases for touched primitives pass at tolerance; invariants preserved | Plan §5 |
| A5 | Code quality gates: fmt, clippy `-D warnings`, ruff, mypy `--strict` all clean | Coding Standards |
| A6 | Security: no `unsafe` outside audited modules, bandit/ruff-S clean, `cargo audit` + `pip-audit` clean, no secrets, no runtime codegen | Coding Standards §6 |
| A7 | Docstring/doc coverage at threshold (Rust 100% public; Python 100% public, ≥95% overall) | Documentation Standards §2 |
| A8 | Repository hygiene: no TODO/FIXME/stub markers outside declared placeholders, `__all__` consistent, no orphan files, gitignore respected | 3.0 audit methodology |
| A9 | CI: all workflows green on the WP branch; benchmark regression gates not tripped | Versioning Standards §3 |
| A10 | Artefact trail: prior cycle's audit/report artefacts exist and are consistent | This document §5 |

## 5. Deviation classification and ledger

| Severity | Definition | Required response |
|---|---|---|
| **D1 — Trajectory breach** | Violates plan requirements/architecture rules, numerical parity, security, or published-result reproducibility | S3 fix mandatory before any other work; `FAIL` verdict |
| **D2 — Standard violation** | Breaks a normative standard (coverage, docstrings, test-in-tandem, quality gates) | Fix in S3 of the same cycle |
| **D3 — Plan drift** | Divergence between plan text and justified reality (better design found, renamed symbol, re-scoped WP) | Fix in S3 **or** plan amendment |
| **D4 — Cosmetic** | Typos, stale comments, minor doc gaps | Fix in S3 or explicitly carry to next cycle's WP (max one carry) |

The **deviation ledger** is the cumulative findings table maintained in each
Project State Report: every finding ever raised, with status
`FIXED | AMENDED | CARRIED(1)`. A finding may be carried at most once (D4
only); anything older becomes D2 automatically.

## 6. Collaborative execution (USER + AI pair)

PRIN is built by a human maintainer working with an AI pair (Cascade). To keep
that collaboration auditable:

- **Session start protocol:** every session begins by reading (1) the latest
  Project State Report, (2) the open WP declaration, (3) the active brief in
  `DOCS/sessions/`, and (4) the relevant plan sections — then stating the
  session ID/type (S1–S4 or E1–E5) and its planned outputs.
- **Session end protocol:** every session ends with its artefacts committed
  and the Project State Report's "current position" line updated (S4) or the
  session log appended (S1–S3).
- **Role split:** the AI pair executes sessions and drafts artefacts; the
  human maintainer approves WP declarations, audit verdicts, plan amendments,
  and releases. Approval is recorded in the artefact itself.
- The repository's `.windsurf/workflows/` directory provides the operational
  checklists (`/coding-session`, `/audit-session`, `/remediation-session`,
  `/documentation-session`, `/experiment-session`) mirroring this standard.
  If they diverge from this document, this document wins.

## 7. Cadence and scope limits

- One WP in flight at a time. Parallel WPs require maintainer approval and
  disjoint file scopes.
- An S1 session that grows beyond its WP declaration must stop and either
  split the WP (new declaration) or descope. Auditors treat scope creep as D3.
- Hotfixes (broken `main`, security) may bypass S1 ordering but must be
  retro-audited in the next S2 and recorded in the deviation ledger.

## 8. Prospective Session Execution Plan

`DOCS/sessions/` operationalizes this standard with one prospective brief for
every planned session from project execution start through stable release. The
Master Session Register is the default global order; the traceability matrix
maps plan obligations to owners and independent confirmations.

- A brief is an **execution contract**, not evidence or status authority.
- The latest approved Project State Report controls actual position; S4 updates
  register/brief status from committed evidence.
- No planned session is skipped, merged, or reordered without an approved
  amendment. Phase 2/3 parallelism requires disjoint scopes and separate audits.
- A campaign D1/D2 inserts all four conditional correction sessions before the
  blocked numbered session resumes; planned numbers remain stable.
- Stale or broken session-plan metadata is a governance finding (D4 normally,
  D2 when it could authorize work incorrectly).

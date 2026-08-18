# Phase 3 Recommendation Implementation — Governance and Methodology

**Status:** Normative for this implementation session.
**Date:** 2026-08-18
**Authority:** Phase 3 Analytics Report (`phase-3-analytics-report.md`),
Phase 3 Recommendations Register (`phase-3-recommendations.md`),
[Development Workflow and Audit Standards](../../standards/Development_Workflow_and_Audit_Standards.md),
[Analytics Methodology](../ANALYTICS_METHODOLOGY.md), and the Phase 1/Phase 2
precedent (`../phase-1/phase-1-recommendation-implementation-governance.md`,
`../phase-2/phase-2-recommendation-implementation-governance.md`).
**Git state:** `main` @ `64c97c9` (post-Phase 3 analytics, pre-implementation)
**Session position:** Inter-phase process improvement — between session 0084
(Phase 3 close, WP-021 S4) plus the EA-004/EMA-002 global sessions, and
session 0085 (Phase 4 start, WP-022 S1, currently `PLANNED`).

---

## 1. Purpose

This document establishes the governance, scope, methodology, and disposition
of each Phase 3 recommendation (R21–R25) for implementation before Phase 4
begins. It is the governing brief for the inter-phase recommendation
implementation session, following the identical precedent established by the
Phase 1 (R7–R13) and Phase 2 (R14–R20) recommendation implementation sessions.

### 1.1 Relationship to existing governance

The [Analytics Methodology](../ANALYTICS_METHODOLOGY.md) §7 states a phase
analytics session is not itself a Session Cycle session; it produces
recommendations that inform the next phase. The
[Recommendations Register](phase-3-recommendations.md) priority legend
assigns timing:

| Priority | Action timing |
|---|---|
| P0 — Critical | Before Phase 4's next S4/global session |
| P1 — High | Phase 4 first cycle |
| P2 — Medium | Phase 4 mid-phase |
| P3 — Low | Phase 5+ or opportunistic |

R21's own recommended-action text is stronger than its P0 timing bar
("this is a small, mechanical, single-line-per-file fix... do this
immediately"), so it is fully implemented now. R22 and R23 (both P1) state
their own confirmation evidence requires the standing instruction to already
be normative before the next relevant session — the same "implement now,
standing instruction" pattern the Phase 1 session applied to R9/R12 and the
Phase 2 session applied to R16/R18 — so both are implemented now rather than
deferred to "Phase 4 first cycle." R24 (P2) and R25 (P3) are deferred with
explicit future-session assignments, per Recommendations Register principle 3
and each recommendation's own owner field.

### 1.2 Principles

Identical to the Phase 1/Phase 2 precedent:

1. **Evidence-based implementation.** Each recommendation is implemented
   against its motivating evidence and confirmation evidence as stated in
   the Recommendations Register.
2. **Minimal blast radius.** Only the specific artefacts named by each
   recommendation are modified. No scope creep.
3. **Deferred items are tracked.** Every recommendation not implemented in
   this session is assigned to an explicit future session/WP with a
   documented rationale — never a fabricated session number where the
   recommendation's own text states the item is unscheduled.
4. **Verification-gated.** All changes pass the project's verification
   one-liner (`AGENTS.md`) before commit.
5. **Governance-compliant.** Standards amendments follow the same review
   bar as the project plan: documented rationale, cross-references.
6. **Maintainer decisions are recorded, not assumed.** Where a recommendation
   requires a maintainer decision (R23), the decision is obtained directly
   in this session (the maintainer is the session's principal) and recorded
   with its date, rather than left as an open placeholder or silently
   resolved by the AI pair.

---

## 2. Recommendation disposition

| ID | Priority | Disposition | Implementation target | Rationale |
|---|---|---|---|---|
| R21 | P0 | **Implement now** | `DOCS/PRIN_Project_Plan.md` §6; `DOCS/experiments/README.md` | Recommendation's own text: "do this immediately, since WP-022 (Phase 4) is already underway [declared] and the Project Plan is the document every future session is instructed to read first." Two small, mechanical, single-line-per-file fixes with no code impact. |
| R22 | P1 | **Implement now** | `DOCS/standards/Documentation_Standards.md` §7 | Owner field: "before the Phase 4 exit-gate S4 session." Implementing now (rather than waiting for Phase 4's close) ensures every WP-N S4 across all of Phase 4 — and specifically the phase-closing one — already operates under the strengthened checklist item, closing the exact structural gap that produced PA2-F1/PA2-F2 and PA3-F1/PA3-F2 before it can recur a third time. |
| R23 | P1 | **Implement now (maintainer decision obtained)** | `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md` §5.1; `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` §2 | Recommendation's own action: "raise Snyk MCP's persistent unavailability directly with the maintainer." The maintainer is directly available in this session; asking now rather than deferring to "the next EA/EMA session" (the owner field's stated fallback) resolves the standing escalation two sessions sooner. Maintainer selected "accept Snyk-CLI-only permanently" (2026-08-18), matching the recommendation's own first confirmation-evidence branch ("the maintainer explicitly confirms the Snyk-CLI-only posture is intentional and permanent, at which point `ANALYTICS_METHODOLOGY.md` §5.1 item 11 and `Executive_Audit_Governance_and_Methodology.md` §2 principle 6 should be updated"). |
| R24 | P2 | **Defer to WP-022 S1** | Session 0085 (WP-022 S1 — Coding, currently `PLANNED`) | Recommendation's own Owner field: "Phase 4 planning (WP-022 S1 or the Phase 4 analytics session)." Choosing a GPU CI runner strategy (self-hosted registration, a cloud provider, or a time-bounded local-only acceptance) is a plan-amendment-class decision requiring maintainer approval at WP declaration/S1 time (Development Workflow Standards §2) — not something this inter-phase session can unilaterally decide without pre-empting that approval, identical reasoning to Phase 2's R19 disposition. This session narrows `DEFERRED_VALIDATION_REGISTER.md` DV-001/DV-002/DV-005's re-audit gates to the single named session (0085) instead of three independently drifting placeholders. |
| R25 | P3 | **Defer, opportunistic (no WP gate)** | Future maintenance session; explicitly not assigned to a specific WP | Recommendation's own Owner field: "Future maintenance session, not gated to any specific WP." The `timeout-minutes: 120` safety net (EA-004, `1604bd6`) already removes the blocking/cost-runaway risk; the remaining root-cause investigation is CI-turnaround/cost work, not correctness-blocking. Assigning a fabricated session number here would misrepresent the recommendation's own stated scope and this session's own instruction to document deferred items in their *exact* future session — where no exact session exists by design, that fact is recorded instead. |

### 2.1 Summary

- **Implement now (3):** R21, R22, R23
- **Defer with explicit assignment (1):** R24 → Phase 4 / WP-022 S1 (session
  0085)
- **Defer, opportunistic, no WP gate (1):** R25 → future maintenance session
  (unscheduled by the recommendation's own design)

This implementation session addresses the P0 recommendation (R21) in full and
both P1 recommendations (R22, R23) in full — including obtaining the R23
maintainer decision directly rather than passing it forward — leaving only
the P2 (R24, correctly deferred to a WP-declaration-time maintainer decision)
and P3 (R25, correctly left unscheduled per its own text) recommendations
open, both with an explicit, evidence-backed disposition rather than a
silent gap.

---

## 3. Implementation methodology

### 3.1 Scope

This session modifies only:

1. `DOCS/PRIN_Project_Plan.md` — R21a: Phase 3 roadmap-table row gains
   `✅ COMPLETE`.
2. `DOCS/experiments/README.md` — R21b: index entry added for
   `0081-wp021-s1-handoff.md`, tagged `[RETROACTIVE UPDATE - Phase 3
   recommendation implementation session, R21/PA3-F1]`.
3. `DOCS/standards/Documentation_Standards.md` — R22: new S4 checklist item
   9 (§7), scoped to phase-closing S4 only.
4. `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md` — R23: §5.1 item 11 updated to
   record the maintainer's permanent Snyk-CLI-only decision.
5. `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` — R23: §2
   principle 6 updated identically.
6. `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — close R21/R22/R23;
   narrow DV-001/DV-002/DV-005's re-audit gates to session 0085 (R24); record
   R24/R25 dispositions in a new "Phase 3 analytics — deferred and ongoing
   items" section; append review-log entry.
7. `CHANGELOG.md` — new `[Unreleased]` entry for this implementation session.
8. This governance document.

No Rust or Python source is touched; this is a documentation/governance-only
session, identical in kind to the Phase 2 precedent's R15/R16/R18 work (its
one source-file touch, R14a, was itself a formatting-only fix with zero
behavioral change).

### 3.2 Entry conditions

- [x] Phase 3 complete (session 0084 closed; phase exit gate GREEN per
  `DOCS/reports/021-project-state.md` §5, independently re-confirmed by
  EA-004 and EMA-002).
- [x] Phase 3 Analytics Report, Evidence Index, and Recommendations Register
  drafted and indexed (`DOCS/ANALYTICS/phase-3/`, `DOCS/ANALYTICS/README.md`
  @ `64c97c9`).
- [x] No unresolved D1/D2 findings in the deviation ledger (EA-004 resolved
  E-F1/E-F2; EMA-002 raised zero new findings).
- [x] `main` up to date with `origin/main`, working tree clean at session
  start.
- [x] WP-022 (Phase 4, session 0085) confirmed still `PLANNED`, not started
  — this session genuinely precedes Phase 4 S1, matching the Phase 1/Phase 2
  precedent's session position.

### 3.3 Exit criteria

- [x] All three "implement now" recommendations addressed with artefacts.
- [x] The R23 maintainer decision obtained directly and recorded with its
  date.
- [x] Deferred items (R24, R25) documented with explicit future-session
  assignments or an explicit, evidence-backed "no WP gate" disposition.
- [x] Verification one-liner (`AGENTS.md`) passes clean.
- [x] Changes committed with descriptive messages referencing recommendation
  IDs.
- [x] This governance document updated with implementation results.

### 3.4 Verification

The full verification one-liner from `AGENTS.md` is run after all changes:

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-full
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo llvm-cov -p prin-kernels --features wgpu,cpu
cargo llvm-cov -p prin-dynamics
cargo llvm-cov -p prin-dynamics --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

Since this session touches only Markdown documentation and governance
standards (no Rust or Python source), none of the code-level gates are
expected to change outcome from the last known-green Phase 3 exit state
(re-confirmed independently at `HEAD` `c6407f7` by the Phase 3 Analytics
Report §5.4); they are re-run in full regardless, per principle 4
(verification-gated).

Per Coding Standards §6 (Secure development), Snyk is also checked per the
R23 decision recorded in this session: the Snyk CLI is the position of
record; Snyk MCP availability is checked opportunistically but its absence
is no longer an escalation.

---

## 4. Commit protocol

Each recommendation implementation is committed with the recommendation ID
in the message, grouped by file overlap where splitting would fragment a
single coherent diff:

| Commit | Message prefix | Scope |
|---|---|---|
| R21 | `docs(plan): R21 — Phase 3 roadmap marker and experiments index (PA3-F1/PA3-F2)` | `DOCS/PRIN_Project_Plan.md`, `DOCS/experiments/README.md` |
| R22 | `docs(standards): R22 — phase-closing cross-cutting document currency` | `Documentation_Standards.md` |
| R23 | `docs(standards): R23 — Snyk-CLI-only accepted as permanent (maintainer decision)` | `ANALYTICS_METHODOLOGY.md`, `Executive_Audit_Governance_and_Methodology.md` |
| Register + CHANGELOG | `docs(reports): close R21/R22/R23, narrow DV-001/002/005 to WP-022 S1, record R24/R25 dispositions` | `DEFERRED_VALIDATION_REGISTER.md`, `CHANGELOG.md` |
| Governance | `docs(analytics): Phase 3 recommendation implementation governance and methodology` | This document |

---

## 5. Implementation results

### 5.1 R21 — Fix PA3-F1 (experiments index) and PA3-F2 (Project Plan marker)

**Status:** IMPLEMENTED
**Files modified:** `DOCS/PRIN_Project_Plan.md`, `DOCS/experiments/README.md`
**Evidence:** Project Plan §6's Phase 3 row now reads `**3 — GPU kernels**
(parallel with 2) ✅ COMPLETE`, matching the convention used for Phases 0–2.
`DOCS/experiments/README.md`'s file index now lists
`0081-wp021-s1-handoff.md` with a one-line summary of its scope and a
`[RETROACTIVE UPDATE]` tag, matching the existing convention used for the
0021/0025 retroactive index entries.

### 5.2 R22 — Phase-closing cross-cutting document currency

**Status:** IMPLEMENTED
**Files modified:** `Documentation_Standards.md` (§7, new item 9)
**Evidence:** New S4 checklist item, scoped explicitly to phase-closing S4
(not every WP-N S4), requiring explicit verification/update of the Project
Plan §6 roadmap table, `DOCS/experiments/README.md`'s index, and
`SESSION_REGISTER.md`'s Global Sessions section — the three documents whose
staleness produced PA2-F1/PA2-F2 and PA3-F1/PA3-F2. Confirmation evidence per
the recommendation itself accrues at the Phase 4 exit-gate S4 session, which
this item now governs.

### 5.3 R23 — Snyk MCP escalation resolved by maintainer decision

**Status:** IMPLEMENTED
**Files modified:** `ANALYTICS_METHODOLOGY.md` (§5.1, item 11 updated),
`Executive_Audit_Governance_and_Methodology.md` (§2, principle 6 updated)
**Maintainer decision (2026-08-18):** "Accept Snyk-CLI-only permanently" —
selected directly in this session via an explicit choice among three options
(accept CLI-only permanently; register/fix MCP; leave open for the next
EA/EMA session). The Snyk CLI has produced consistent, evidence-backed
results across all 4 EA sessions to date and both phase-analytics sessions
that checked it (Phase 2, Phase 3).
**Evidence:** Both governance documents now record the maintainer's decision
with its date and state that Snyk MCP unavailability is no longer a standing
tooling-access-gap escalation; future sessions still check MCP availability
opportunistically (preferring it if present) but no longer escalate its
absence.

### 5.4 Deferred items

| ID | Deferred to | Rationale |
|---|---|---|
| R24 | Phase 4 / WP-022 S1 (session 0085) | GPU CI runner strategy is a plan-amendment-class decision requiring maintainer approval at WP declaration time; `DEFERRED_VALIDATION_REGISTER.md` DV-001/DV-002/DV-005 re-audit gates narrowed to this single session |
| R25 | Future maintenance session, explicitly unscheduled | Recommendation's own owner field states no WP gate applies; `timeout-minutes: 120` safety net (EA-004) already removes the blocking risk, so the remaining root-cause investigation is opportunistic |

### 5.5 Verification results

All gates green (2026-08-18, `main` @ `64c97c9` + this session's commits):

| Gate | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check` (same paths) | 50 files already formatted |
| `mypy python/prin --strict` | Success: no issues found in 18 source files |
| `interrogate` | 100.0% (106/106 public) |
| `bandit -r . -c pyproject.toml` | 0 issues (3,157 lines scanned) |
| `pytest tests/ -m "not slow and not gpu"` | 306 passed, 6 deselected, 99% coverage |
| `pytest tests/ parity/` | 822 passed (306 fast + 510 parity + 6 benchmark timings), 99% coverage |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean |
| `cargo test --workspace` | All suites pass — matches the Phase 3 Analytics Report's independently re-verified baseline (`HEAD` `c6407f7`: 821 default + 28 doctests); no Rust source touched this session so no delta is expected |
| `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | Ran clean, exit 0; coverage unchanged (no `prin-kernels` source touched) |
| `cargo llvm-cov -p prin-dynamics` | Ran clean, exit 0; coverage unchanged (no `prin-dynamics` source touched) |
| `cargo llvm-cov -p prin-dynamics --features strict-checks` | Ran clean, exit 0; coverage unchanged (same scope note) |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings |
| `cargo audit` | 1 allowed (`paste` RUSTSEC-2024-0436, amendment #9), 0 new |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| `sphinx.cmd.build -W --keep-going -b html` | Build succeeded, 0 warnings |

**Snyk (R23, applied to this session):** Snyk MCP tool availability was checked
explicitly (`ToolSearch` for a Snyk tool returned no match), consistent with
the R23 decision now embedded in `ANALYTICS_METHODOLOGY.md` §5.1 item 11 and
`Executive_Audit_Governance_and_Methodology.md` §2 principle 6. Per that
decision the Snyk CLI is the position of record: `snyk --version` confirms
`1.1306.2` installed and on `PATH`. This session touches zero Rust or Python
source (Markdown/documentation only, per §3.1's scope) and zero dependency
manifests, so per Coding Standards §6 ("Run Snyk Code for new or modified
first-party code... Snyk Open Source for supported dependency changes")
neither scan is triggered by this session's own changes; the most recent
verified Snyk result remains EA-004 (2026-08-17, Snyk CLI): 0 issues Snyk
Code, 6 pre-accepted `torch` advisories (DV-011), no new dependencies.

Full log: `verify.log` (this session's scratchpad), archived findings
summarized above.

---

## 6. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| AI pair | Claude Code | 2026-08-18 | Drafted |
| Maintainer | MichaelMaillet | 2026-08-18 | R23 decision recorded live in-session |

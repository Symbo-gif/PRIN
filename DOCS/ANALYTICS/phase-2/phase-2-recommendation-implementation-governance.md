# Phase 2 Recommendation Implementation — Governance and Methodology

**Status:** Normative for this implementation session.
**Date:** 2026-08-15
**Authority:** Phase 2 Analytics Report (`phase-2-analytics-report.md`),
Phase 2 Recommendations Register (`phase-2-recommendations.md`),
[Development Workflow and Audit Standards](../../standards/Development_Workflow_and_Audit_Standards.md),
[Analytics Methodology](../ANALYTICS_METHODOLOGY.md), and the Phase 1
precedent (`../phase-1/phase-1-recommendation-implementation-governance.md`).
**Git state:** `main` @ `4d0f75b` (post-Phase 2 analytics, pre-implementation)
**Session position:** Inter-phase process improvement — between session 0064
(Phase 2 close, WP-016 S4) and session 0065 (Phase 3 start, WP-017 S1).

---

## 1. Purpose

This document establishes the governance, scope, methodology, and disposition
of each Phase 2 recommendation (R14–R20) for implementation before Phase 3
begins. It is the governing brief for the inter-phase recommendation
implementation session, following the identical precedent established by the
Phase 1 recommendation implementation session (R7–R13).

### 1.1 Relationship to existing governance

The [Analytics Methodology](../ANALYTICS_METHODOLOGY.md) §7 states a phase
analytics session is not itself a Session Cycle session; it produces
recommendations that inform the next phase. The
[Recommendations Register](phase-2-recommendations.md) priority legend
assigns timing:

| Priority | Action timing |
|---|---|
| P0 — Critical | Before Phase 3 S1 |
| P1 — High | Phase 3 first cycle |
| P2 — Medium | Phase 3 mid-phase |
| P3 — Low | Phase 4+ or opportunistic |

Both P0 recommendations (R14, R15) and both P1 recommendations (R16 and,
partially, R17) are addressed in or by this inter-phase session, satisfying
the "Before Phase 3 S1" and "Phase 3 first cycle" timing respectively — R16
is fully implemented now; R17 is explicitly assigned to WP-017's first
cycle since it is process tooling, not a WP-017 kernel-architecture
deliverable. R18 (P2) is implemented now as a standing instruction because
it is low-effort and high governance value (the same rationale the Phase 1
session applied to R9/R12). R19 (P2) and R20 (P3) are deferred with explicit
future-session assignments, per Recommendations Register principle 3.

### 1.2 Principles

Identical to the Phase 1 precedent (§1.2 of that document):

1. **Evidence-based implementation.** Each recommendation is implemented
   against its motivating evidence and confirmation evidence as stated in
   the Recommendations Register.
2. **Minimal blast radius.** Only the specific artefacts named by each
   recommendation are modified. No scope creep.
3. **Deferred items are tracked.** Every recommendation not implemented in
   this session is assigned to an explicit future session/WP with a
   documented rationale.
4. **Verification-gated.** All changes pass the project's verification
   one-liner (`AGENTS.md`) before commit.
5. **Governance-compliant.** Standards amendments follow the same review
   bar as the project plan: documented rationale, cross-references.

---

## 2. Recommendation disposition

| ID | Priority | Disposition | Implementation target | Rationale |
|---|---|---|---|---|
| R14 | P0 | **Implement now** | `tools/math_audit_run.py`; `CHANGELOG.md` | P0 timing: "Before Phase 3 S1." Both PA2-F1 (red ruff gate) and PA2-F2 (missing CHANGELOG entry) are small, mechanical fixes explicitly scoped for a pre-Phase-3 hotfix by the recommendation itself. |
| R15 | P0 | **Implement now** | `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 | P0 timing: "Before Phase 3 S1"; Owner field explicitly states "before WP-017 S1." This is the root-cause fix for Phase 2's dominant D1 pattern (WP-012/013/014 each shipped without parity evidence) — it must land before WP-017 S1 begins, or Phase 3 risks repeating the pattern immediately. |
| R16 | P1 | **Implement now** | `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` §5; `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md` §8 | Owner field: "before the next EA/EMA session." Implementing now (rather than deferring to Phase 3) ensures the very next EA or EMA session — whenever it occurs — is already governed by the strengthened closing checklist. Low effort (two governance-document amendments), high governance value (direct fix for the structural gap PA2-F2 traces to). |
| R17 | P1 | **Defer to Phase 3, WP-017 S4** | Session 0068 (WP-017 S4 — Documentation) | Recommendation's own Owner field: "Phase 3, first cycle (WP-017 S1 or S4)." Assigned to S4 rather than S1 because the deliverable is process/governance tooling (a ledger-consistency checker), not WP-017's own kernel-architecture-and-CPU-references scope; S4 is the natural session for cross-cutting tooling and documentation additions, mirroring how R7 (Phase 1) landed a documentation-checklist amendment rather than mid-WP code. |
| R18 | P2 | **Implement now (standing instruction)** | `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md` §5.1; `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` §2 | Same rationale the Phase 1 session applied to R9/R12: P2 timing but low effort and high governance value. The recommendation's own confirmation evidence ("the next analytics or executive-audit session's evidence table states Snyk MCP availability explicitly") requires the instruction to already be normative before that next session begins — implementing now is the only disposition that satisfies it. |
| R19 | P2 | **Defer to Phase 3 planning** | WP-017 declaration (session 0065) or, at latest, the Phase 3 exit-gate PSR (WP-021 S4, session 0084) | Recommendation's own Owner field: "Phase 3 planning (WP-017 declaration or Phase 3 exit-gate PSR)." Assigning a specific WP number to carried scope is a plan-amendment-class decision requiring maintainer approval at WP declaration time (Development Workflow Standards §2) — not something this inter-phase session can unilaterally decide without pre-empting that approval. This session narrows `DEFERRED_VALIDATION_REGISTER.md` DV-012's re-audit gate to the exact two candidate sessions instead, closing the "no explicit future session" gap without pre-empting the WP-scope decision itself. |
| R20 | P3 | **Defer to next EMA session** | Not yet numbered — EMA sessions are declared ad hoc as global sessions outside the planned 0001–0198 sequence (`SESSION_REGISTER.md`) | Recommendation's own Owner field: "Next EMA session." No EMA-002 has been declared; there is no session number to assign yet. Tracked as `DEFERRED_VALIDATION_REGISTER.md` R20 (deferred/ongoing items table) so it is not lost between now and EMA-002's convening. |

### 2.1 Summary

- **Implement now (4):** R14, R15, R16, R18
- **Defer with explicit assignment (3):** R17 → Phase 3 / WP-017 S4 (session
  0068); R19 → WP-017 declaration (session 0065) or Phase 3 exit-gate PSR
  (session 0084); R20 → next EMA session (unnumbered)

This implementation session addresses both P0 recommendations in full and one
of two P1 recommendations in full (the other, R17, receives a concrete
session assignment rather than a code change, per the recommendation's own
"S1 or S4" owner field), plus one low-effort P2 recommendation (R18),
matching the Phase 1 precedent's disposition pattern (P1s implemented, cheap
P2s implemented, remainder deferred with explicit assignments).

---

## 3. Implementation methodology

### 3.1 Scope

This session modifies only:

1. `tools/math_audit_run.py` — R14a: `ruff check --fix` (import sorting) and
   `ruff format` (two `E501` lines wrapped). No behavioral change.
2. `CHANGELOG.md` — R14b: new `[Unreleased]` entry for EMA-001/EMA-001R
   under `### Fixed`; new `### Added` entry for this implementation session
   itself.
3. `DOCS/standards/Development_Workflow_and_Audit_Standards.md` — R15: new
   S1 exit-criteria bullet (§3) requiring a stated parity-evidence
   disposition.
4. `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` — R16
   (§5, new closing-checklist item) and R18 (§2, new governance principle).
5. `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md`
   — R16: new closing-checklist item (§8).
6. `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md` — R18: new input item (§5.1).
7. `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — close R14/R15/R16;
   narrow DV-012's re-audit gate (R19); record R17/R18/R20 dispositions;
   append review-log entry.
8. This governance document.

### 3.2 Entry conditions

- [x] Phase 2 complete (session 0064 closed, phase exit gate GREEN per
  `DOCS/reports/016-project-state.md` §5).
- [x] Phase 2 Analytics Report, Evidence Index, and Recommendations Register
  drafted (`DOCS/ANALYTICS/phase-2/`).
- [x] No unresolved D1/D2 findings in the deviation ledger (EMA-001R
  resolved M-F1/M-F3; EA-003 resolved E-F1–E-F14).
- [x] `main` up to date with `origin/main`, working tree clean apart from the
  Phase 2 analytics session's own uncommitted artefacts at session start.

### 3.3 Exit criteria

- [x] All four "implement now" recommendations addressed with artefacts.
- [x] Deferred items documented with explicit future-session assignments.
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

Since this session touches no Rust source and only one Python file (a
formatting-only change to `tools/math_audit_run.py`), the Rust suite and the
bulk of the Python suite are not expected to change outcome from the last
known-green Phase 2 exit state (`DOCS/reports/016-project-state.md` §2); they
are re-run in full regardless, per principle 4 (verification-gated).

Per Coding Standards §6 (Secure development), Snyk Code/Open Source are also
checked for availability (R18, applied to this session itself) before
relying on any result.

---

## 4. Commit protocol

Each recommendation implementation is committed separately with the
recommendation ID in the message:

| Commit | Message prefix | Scope |
|---|---|---|
| R14 | `fix(tools): R14 — ruff-clean math_audit_run.py, add EMA-001 CHANGELOG entry` | `tools/math_audit_run.py`, `CHANGELOG.md` |
| R15 | `docs(standards): R15 — parity-evidence disposition as S1 exit-gate item` | `Development_Workflow_and_Audit_Standards.md` |
| R16 | `docs(standards): R16 — EA/EMA closing checklist for CHANGELOG and quality gates` | `Executive_Audit_Governance_and_Methodology.md`, `Executive_Mathematical_Audit_Governance_and_Methodology.md` |
| R18 | `docs(analytics): R18 — standing Snyk MCP availability check` | `ANALYTICS_METHODOLOGY.md`, `Executive_Audit_Governance_and_Methodology.md` |
| Register | `docs(reports): close R14/R15/R16, narrow DV-012, record R17/R19/R20 dispositions` | `DEFERRED_VALIDATION_REGISTER.md` |
| Governance | `docs(analytics): Phase 2 recommendation implementation governance and methodology` | This document |

Given the shared files between R16 and R18 (both touch
`Executive_Audit_Governance_and_Methodology.md`), commits are grouped by file
overlap where splitting would fragment a single coherent diff; the finding
IDs are cited in the commit body regardless of grouping.

---

## 5. Implementation results

### 5.1 R14 — Fix PA2-F1 (ruff) and PA2-F2 (CHANGELOG)

**Status:** IMPLEMENTED
**Files modified:** `tools/math_audit_run.py`, `CHANGELOG.md`
**Evidence:** `ruff check tools/math_audit_run.py` and
`ruff format --check tools/math_audit_run.py` both clean (previously 3 `ruff
check` errors: one unsorted import block, two `E501` long lines). No
behavioral change — verified by diff inspection (import restructuring and
line-wrapping only). `CHANGELOG.md` `[Unreleased]` gained a full EMA-001/
EMA-001R entry (M-F1/M-F2/M-F3, `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_001.md`,
Project Plan amendments #23–#25) comparable in detail to the existing EA-003
entry.

### 5.2 R15 — Parity-evidence disposition as S1 exit-gate item

**Status:** IMPLEMENTED
**Files modified:** `Development_Workflow_and_Audit_Standards.md` (§3, S1
exit criteria)
**Evidence:** New exit-criteria bullet requires the S1 handoff note to state,
for every new numerical primitive, whether a directly comparable PRINet 3.0
reference exists (backed by a stated grep/import check, not an assertion),
and if so, either includes parity evidence in the S1 commit or explicitly
defers it with a reviewable reason.

### 5.3 R16 — EA/EMA closing checklist

**Status:** IMPLEMENTED
**Files modified:** `Executive_Audit_Governance_and_Methodology.md` (§5, new
item 5), `Executive_Mathematical_Audit_Governance_and_Methodology.md` (§8,
new item 6)
**Evidence:** Both documents now require, before session close: (a) a
`CHANGELOG.md` `[Unreleased]` entry for every user-visible change the
session makes, and (b) the relevant quality gates run on every file the
session newly commits.

### 5.4 R18 — Standing Snyk MCP availability check

**Status:** IMPLEMENTED
**Files modified:** `ANALYTICS_METHODOLOGY.md` (§5.1, new input item 11),
`Executive_Audit_Governance_and_Methodology.md` (§2, new principle 6)
**Evidence:** Both documents now require explicit Snyk MCP availability
verification at the start of every future phase-analytics or Executive Audit
session, with an escalation trigger after 2+ consecutive unavailable
sessions.

### 5.5 Deferred items

| ID | Deferred to | Rationale |
|---|---|---|
| R17 | Phase 3 / WP-017 S4 (session 0068) | Process/governance tooling, not WP-017's own kernel-architecture deliverable |
| R19 | WP-017 declaration (session 0065) or Phase 3 exit-gate PSR (session 0084) | Plan-amendment-class WP-scope decision requiring maintainer approval at declaration time |
| R20 | Next EMA session (unnumbered) | No EMA-002 declared yet; standing precedent recorded in `DEFERRED_VALIDATION_REGISTER.md` for when it is |

### 5.6 Verification results

All gates green (2026-08-15, `main` @ `4d0f75b` + this session's commits):

| Gate | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check` (same paths) | 49 files already formatted |
| `mypy python/prin --strict` | Success: no issues found in 18 source files |
| `interrogate` | 100.0% (106/106 public) |
| `bandit -r . -c pyproject.toml` | 0 low/medium/high (2,863 lines) |
| `pytest tests/ -m "not slow and not gpu"` | 306 passed, 6 deselected, 99% coverage |
| `pytest tests/ parity/` | 822 passed (306 fast + 510 parity + 6 benchmark timings), 99% coverage |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean |
| `cargo test --workspace` | All suites pass (matches PSR-016 baseline: 728 unit/integration/property + 24 doctests) |
| `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | Ran clean, exit 0; coverage unchanged (no `prin-kernels` source touched this session) |
| `cargo llvm-cov -p prin-dynamics` | Ran clean, exit 0; 55.09%/47.48%/53.20% (workspace-wide report scope; unchanged, no `prin-dynamics` source touched this session) |
| `cargo llvm-cov -p prin-dynamics --features strict-checks` | Ran clean, exit 0; 55.65%/48.14%/54.00% (same scope note) |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings |
| `cargo audit` | 1 allowed (`paste` RUSTSEC-2024-0436, amendment #9) |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| `sphinx.cmd.build -W --keep-going -b html` | Build succeeded, 0 warnings |

**Snyk Code / Snyk Open Source (R18, applied to this session):** Snyk MCP
tool availability was checked explicitly before relying on any Snyk result
(`ToolSearch` for a Snyk tool returned no match). Consistent with the R18
standing instruction now embedded in `Executive_Audit_Governance_and_Methodology.md`
§2 and `ANALYTICS_METHODOLOGY.md` §5.1, this limitation is stated rather than
silently carried forward: the most recent verified Snyk result is EA-003
(2026-08-14, `main` @ `fbe1c92` + remediation), which recorded Snyk Code/Open
Source at 0 issues project-wide (`DOCS/reports/016-project-state.md` §2).
The only Python file this session modifies (`tools/math_audit_run.py`) is a
formatting-only change (`ruff --fix`/`ruff format`; import reordering and
line-wrapping, zero semantic diff — confirmed by diff inspection) with no new
dependency or code path, so the residual risk of an un-rescanned Snyk Code
finding is assessed as minimal but not independently re-verified this
session. This is the second consecutive session (after the Phase 2 analytics
session itself) relying on the EA-003 carry-forward; per R18, a third
consecutive occurrence would warrant maintainer escalation.

---

## 6. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| AI pair | Claude Code | 2026-08-15 | Drafted |
| Maintainer | MichaelMaillet | — | Pending approval |

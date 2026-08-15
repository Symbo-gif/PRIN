# Phase 2 Recommendations Register

**Phase:** 2 — Advanced numerics and simulation
**Date:** 2026-08-15
**Companion to:** [`phase-2-analytics-report.md`](phase-2-analytics-report.md)

Prioritized recommendations for Phase 3, derived from Phase 2 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority. R14 and R15 additionally
carry the two findings (PA2-F1, PA2-F2) this analytics session discovered
independently; per Analytics Methodology §7 these are recorded here and
also trigger the normal Session Cycle remediation process (a hotfix or the
next global session), not a fix performed inside this analytics session.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 3 S1 |
| **P1 — High** | Significant improvement; should be addressed early | Phase 3 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 3 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 4+ or opportunistic |

---

## R14 — Fix the two findings this analytics session discovered (PA2-F1, PA2-F2)

| Field | Value |
|---|---|
| **ID** | R14 |
| **Priority** | **P0 — Critical** |
| **Dimension** | P2 (Documentation), P5 (Evidence), P6 (Governance) |
| **Motivating evidence** | This session's independent re-verification (analytics report §5.4) found `tools/math_audit_run.py` (added by EMA-001, commit `630c5d6`) fails the mandatory `ruff check`/`ruff format --check` gate — 3 errors, currently red on `main` `HEAD`. Separately, `CHANGELOG.md`'s `[Unreleased]` section has zero mention of EMA-001 despite it fixing a real D1 defect. Both were missed because EMA-001, as a global session, sits outside every WP-N checklist (including R7's documentation sweep). |
| **Recommended action** | (a) Run `ruff check --fix` and `ruff format` on `tools/math_audit_run.py`, verify `ruff check`/`ruff format --check` clean, commit as a small hotfix referencing PA2-F1. (b) Add a `[Unreleased]` `CHANGELOG.md` entry for EMA-001 and EMA-001R (M-F1/M-F2/M-F3, amendments #23–#25), referencing PA2-F2. Both are small, mechanical fixes — do this before Phase 3 S1 so Phase 3's baseline is genuinely gate-clean. |
| **Confirmation evidence** | `ruff check python/ tests/ benchmarks/ tools/ parity/` and `ruff format --check` both clean; `CHANGELOG.md` `[Unreleased]` contains an EMA-001 entry comparable in detail to the existing EA-003 entry. |
| **Owner** | Immediate hotfix (before WP-017 S1) or WP-017 S1's own opening commit |

---

## R15 — Require parity evidence as an S1 entry gate, not an S2-discovered gap

| Field | Value |
|---|---|
| **ID** | R15 |
| **Priority** | **P0 — Critical** |
| **Dimension** | P1 (Data and parity), P4 (Coding and architecture) |
| **Motivating evidence** | WP-012, WP-013, and WP-014 each shipped their S1 commit with zero Rust-vs-PRINet-3.0 parity evidence for the headline deliverable, despite a directly comparable PRINet 3.0 reference existing and being importable in the project venv in every case. This is the single largest driver of Phase 2's 7-D1 finding rate (vs. 0 in Phase 1) and recurred identically three times despite being flagged D1 the first time (WP-012). Testing Standards §1.3 already states parity cases should be "written or identified *before* the algorithm lands." |
| **Recommended action** | Add an explicit S1 exit-gate item (Development Workflow and Audit Standards §3) requiring: before an S1 session is marked COMPLETE, the author states in the handoff note whether a directly comparable PRINet 3.0 reference exists for the new primitive, and if so, either includes parity evidence in the S1 commit or explicitly defers it with a stated reason reviewable at S2. A handoff claiming "no reference exists" (as WP-014's did, refuted in minutes by WP014-F1) should require a one-line grep/import check against the archived reference as evidence, not an unverified assertion. |
| **Confirmation evidence** | Phase 3 WP audits show zero D1 findings whose root cause is "missing parity evidence identified at S2 that a reference for it was available at S1." |
| **Owner** | Standards amendment (`Development_Workflow_and_Audit_Standards.md` §3, S1 exit criteria) before WP-017 S1 |

---

## R16 — Extend the S4/global-session documentation net to cover EA/EMA sessions

| Field | Value |
|---|---|
| **ID** | R16 |
| **Priority** | **P1 — High** |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | R7 (Phase 1) added a documentation-accuracy sweep to the WP-N S4 checklist, and it is working within that scope (independently confirmed this session — no regression found there). But EA-003 and EMA-001 are global sessions outside any WP-N S4, so R7 never runs against them. EA-003 happened to get a full CHANGELOG entry by the auditor's own initiative; EMA-001 did not (PA2-F2, R14). Nothing in the current standards *requires* a global session to update `CHANGELOG.md` or run the S4 documentation-accuracy checklist against files it introduces. |
| **Recommended action** | Add an explicit closing-checklist item to `Executive_Audit_Governance_and_Methodology.md` and `Executive_Mathematical_Audit_Governance_and_Methodology.md`: every EA/EMA session that modifies or adds files must (a) add or update a `CHANGELOG.md` `[Unreleased]` entry, and (b) run the relevant quality gates (`ruff check`/`format`, `mypy`, etc. for Python; `cargo fmt`/`clippy` for Rust) on any file it newly commits, before the session closes. |
| **Confirmation evidence** | The next EA or EMA session's closing checklist includes both items, checked off with evidence. |
| **Owner** | Standards amendment to both executive-audit governance documents, before the next EA/EMA session |

---

## R17 — Add an automated cumulative-deviation-ledger consistency check

| Field | Value |
|---|---|
| **ID** | R17 |
| **Priority** | **P1 — High** |
| **Dimension** | P5 (Evidence), P6 (Governance) |
| **Motivating evidence** | EA-003's headline finding (E-F1, D1) was a silently corrupted cumulative deviation ledger — fabricated commit hashes, rewritten descriptions, one invented finding — introduced at WP-014 S4 and undetected through two subsequent S2 audits (WP-015, WP-016). It was caught only when EA-003 manually diffed the ledger against the last verified PSR. No automated check exists to catch this class of drift; the next occurrence could again survive multiple S2 audits before an executive audit happens to catch it. |
| **Recommended action** | Add a lightweight verification step (script or `tools/` CLI addition) that, given two consecutive PSRs, diffs their cumulative deviation-ledger tables and flags any row whose commit hash does not resolve via `git cat-file -t` or whose description text changed without a corresponding new finding ID. Run it as part of the S2 audit's A10 (Artefact trail) check, or as a pre-commit/CI check on `DOCS/reports/*.md`. |
| **Confirmation evidence** | The check exists and either (a) is exercised clean on all Phase 2 PSRs post-restoration, or (b) is documented as infeasible with a stated reason and an alternative manual-review protocol. |
| **Owner** | Phase 3, first cycle (WP-017 S1 or S4) |

---

## R18 — Independently verify Snyk MCP availability at the start of future analytics sessions

| Field | Value |
|---|---|
| **ID** | R18 |
| **Priority** | **P2 — Medium** |
| **Dimension** | P5 (Evidence), P7 (Security) |
| **Motivating evidence** | This analytics session could not re-execute Snyk Code/Open Source (MCP tool unavailable in this session's environment), and relied on EA-003's one-day-old result as the position of record (§5.3 of the analytics report). This is a stated limitation, not a finding, but repeated reliance on a stale Snyk result across consecutive sessions without independent re-verification would erode the "independent verification" principle over time. |
| **Recommended action** | At the start of each future phase-analytics or executive-audit session, explicitly check Snyk MCP tool availability first; if unavailable, state the limitation and cite the most recent verified result with its date and commit, as this report does. If Snyk MCP is unavailable across 2+ consecutive sessions, escalate to the maintainer as a tooling-access gap requiring resolution, since it degrades the security-evidence chain's independence. |
| **Confirmation evidence** | The next analytics or executive-audit session's evidence table states Snyk MCP availability explicitly, either as a fresh re-run or an explicitly dated carry-forward. |
| **Owner** | Standing instruction for future analytics/EA/EMA sessions |

---

## R19 — Investigate `prin-py`/`prin-kernels` carried-scope timing before Phase 7 campaigns

| Field | Value |
|---|---|
| **ID** | R19 |
| **Priority** | **P2 — Medium** |
| **Dimension** | P8 (Phase exit criteria), P9 (Risk and deferred validation) |
| **Motivating evidence** | Amendment #20 narrowed WP-016's scope to `crates/prin-sim/` only; the `prin-py` sweep/engine PyO3 bindings and `prin-kernels` CPU-reference work from the original WP-016 declaration were deferred to a future, not-yet-declared WP. PSR-016 §6 notes this is "not a blocker for Phase 3 but should be scheduled before the Python API is used in scientific campaigns (Phase 7)." No WP currently owns this. |
| **Recommended action** | When declaring Phase 3's WP sequence (or no later than the Phase 3 exit gate), explicitly assign the deferred `prin-py` sweep/engine bindings and `prin-kernels` CPU-reference work to a numbered WP with a target phase, so it does not become an untracked-drift risk analogous to the Phase 1 tag-cutting gap (E-F6/amendment #22). |
| **Confirmation evidence** | A WP number and target phase for this carried scope appears in the Project Plan §6 phase table or a plan amendment. |
| **Owner** | Phase 3 planning (WP-017 declaration or Phase 3 exit-gate PSR) |

---

## R20 — Re-verify `M-F3`'s `REQUIRES_HUMAN_REVIEW` sign-off cadence

| Field | Value |
|---|---|
| **ID** | R20 |
| **Priority** | **P3 — Low** |
| **Dimension** | P5 (Evidence), P9 (Risk) |
| **Motivating evidence** | EMA-001R resolved M-F3 for `INT-01`/`INT-02`/`HOPF-01`/`KUR-01` via a recorded, evidence-backed sign-off (SciPy + independent Wolfram Engine corroboration) rather than a code or policy change — these four claims remain `REQUIRES_HUMAN_REVIEW` at the governed ledger level by policy design, permanently, unless the claim type gains a symbolic/formal check route. This is a legitimate, well-documented resolution, but it establishes a new pattern (policy-gated claims resolved by recorded sign-off rather than a `PASS`) that future EMA sessions should apply consistently, not ad hoc. |
| **Recommended action** | When a future EMA session encounters a new `high`/`critical`-severity `ode_property`/`graph_topology`/`tensor_contract` claim hitting the same policy gate, follow the same two-track resolution EMA-001R established: attempt a Lean 4 formal claim first if the underlying structure is finite/decidable; otherwise use independent secondary-tool corroboration (Wolfram or equivalent) plus a recorded sign-off, rather than treating the `REQUIRES_HUMAN_REVIEW` status as unresolved indefinitely. |
| **Confirmation evidence** | The next EMA session's report cites this precedent explicitly when resolving an analogous finding. |
| **Owner** | Next EMA session |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R14 | **P0** | P2, P5, P6 | Fix PA2-F1 (red ruff gate) and PA2-F2 (missing CHANGELOG entry) before Phase 3 S1 |
| R15 | **P0** | P1, P4 | Require parity-evidence disposition as an explicit S1 exit-gate item |
| R16 | P1 | P2, P6 | Extend the S4 documentation net to cover EA/EMA global sessions |
| R17 | P1 | P5, P6 | Add an automated cumulative-deviation-ledger consistency check |
| R18 | P2 | P5, P7 | Explicitly verify Snyk MCP availability at the start of future audit/analytics sessions |
| R19 | P2 | P8, P9 | Assign a WP/phase to the deferred `prin-py`/`prin-kernels` carried scope before Phase 7 |
| R20 | P3 | P5, P9 | Apply EMA-001R's `REQUIRES_HUMAN_REVIEW` resolution pattern consistently in future EMA sessions |

**Two P0 recommendations (R14, R15) exist** — a change from Phase 1, which
had none. R14 is small and mechanical (a lint hotfix and a CHANGELOG entry)
and should not delay Phase 3 by more than a single short session. R15 is a
process/standards amendment that should land before WP-017 S1 begins, since
its entire purpose is to prevent Phase 3 from repeating Phase 2's dominant
D1 pattern.

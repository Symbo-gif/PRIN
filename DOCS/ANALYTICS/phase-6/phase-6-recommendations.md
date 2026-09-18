# Phase 6 Recommendations Register

**Phase:** 6 — Benchmarks, reproduction, docs, and RC1 release
**Date:** 2026-09-17
**Companion to:** [`phase-6-analytics-report.md`](phase-6-analytics-report.md)

Prioritized recommendations for Phase 7, derived from Phase 6 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 7's next S4/global session |
| **P1 — High** | Significant improvement; should be addressed early | Phase 7 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 7 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 8+ or opportunistic |

---

## R37 — Create the missing PSR-038 and update the phase-6 README

| Field | Value |
|---|---|
| **ID** | R37 |
| **Priority** | **P1 — High** |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | WP-038 S4 (session 0152) committed the audit report, DV register updates, and CHANGELOG entries declaring Phase 6 complete, but never created `DOCS/reports/038-project-state.md` despite the session brief listing it as a required output. The `DOCS/sessions/phase-6/README.md` still shows sessions 0149–0152 as `PLANNED` rather than `COMPLETE`. This breaks the Development Workflow Standards §1.5 self-documenting invariant ("a reader with no chat history must be able to reconstruct project state from artefacts alone") at the most visible boundary — the phase close. This is the same class of documentation-tracking gap that has been a P2 caveat since Phase 4 (PA4-F1/PA4-F2, Phase 5 hotfix CHANGELOG gaps), now recurring at the phase-close boundary for the first time. |
| **Recommended action** | Create `DOCS/reports/038-project-state.md` from the WP-038 S4 session brief, audit report, and committed evidence. Update `DOCS/sessions/phase-6/README.md` to mark sessions 0149–0152 as `COMPLETE`. Update `DOCS/sessions/SESSION_REGISTER.md` if WP-038 sessions are still marked `PLANNED`. |
| **Confirmation evidence** | `DOCS/reports/038-project-state.md` exists and is consistent with the WP-038 audit report; `DOCS/sessions/phase-6/README.md` shows 0149–0152 as `COMPLETE`; `DOCS/sessions/SESSION_REGISTER.md` is consistent. |
| **Owner** | Phase 7 first cycle (opportunistic; could be a dedicated documentation session or WP-039 S4) |

---

## R38 — Adopt extended timeout or parallel execution for analytics-session test re-verification

| Field | Value |
|---|---|
| **ID** | R38 |
| **Priority** | **P2 — Medium** |
| **Dimension** | P3 (Testing), P5 (Evidence) |
| **Motivating evidence** | The Python test suite has grown from 1,155 tests (Phase 5 close) to 3,698 tests (Phase 6 close) — a 3.2× increase driven by the PRINet 3.0 acceptance suite port. At default timeouts (300s fast, 600s full), the suite exceeded the analytics session's time budget during independent re-verification. This means the analytics session cannot independently verify the full test suite in a single pass, which weakens the Analytics Methodology §5.2 independent-verification principle. The trend will intensify if Phase 7 adds more tests. |
| **Recommended action** | Either (a) extend the analytics session's test timeout to accommodate the full suite (e.g., 900s for fast, 1200s for full), or (b) adopt parallel execution (`pytest -n auto` with `pytest-xdist`) for analytics-session re-verification, or (c) accept PSR S4 figures as authoritative for the analytics session when the suite exceeds a threshold (e.g., 3,000 tests) and document the limitation explicitly. Option (c) is the lowest-cost and most honest approach. |
| **Confirmation evidence** | The analytics session's methodology or the AGENTS.md verification one-liner documents the approach for handling large test suites; the chosen approach is exercised at least once. |
| **Owner** | Phase 7 analytics session or the Phase 7 first-cycle documentation/tooling session |

---

## R39 — Consider a `pytest-xdist` parallel test option for CI and local verification

| Field | Value |
|---|---|
| **ID** | R39 |
| **Priority** | **P3 — Low** |
| **Dimension** | P3 (Testing), P5 (Evidence) |
| **Motivating evidence** | At 3,698 tests and growing, the Python suite's wall-clock execution time is becoming a practical constraint for both CI turnaround and independent verification. The Rust suite (1,577 tests) runs in ~2 minutes with `--test-threads=1`; the Python suite at full scope exceeds 10 minutes. `pytest-xdist` could reduce wall-clock time substantially for both CI and local verification, at the cost of introducing a test-isolation dependency. |
| **Recommended action** | Evaluate `pytest-xdist` for the Python suite. If the suite is isolation-safe (no shared mutable state between tests), add a parallel execution option to the verification one-liner. If not, document which tests require sequential execution and parallelize the rest. |
| **Confirmation evidence** | A decision is recorded (adopt or reject with rationale); if adopted, the verification one-liner includes the parallel option. |
| **Owner** | Phase 7+ or opportunistic |

---

## R40 — Establish a post-release hotfix workflow for `prin-core` on PyPI

| Field | Value |
|---|---|
| **ID** | R40 |
| **Priority** | **P2 — Medium** |
| **Dimension** | P6 (Governance), P8 (Exit criteria) |
| **Motivating evidence** | Phase 6 published `prin-core` 1.0.0rc1 to PyPI and 7 crates to crates.io. This is the project's first public release. The `release.yml` workflow handles publishing, but there is no documented workflow for post-release hotfixes (e.g., if a critical bug is discovered in the published package). The WP-038 S3 session already discovered and fixed 3 publishing issues (crates.io error parsing, PyPI skip-existing, LICENSE inclusion) — these were caught before the final publication, but the pattern shows the release pipeline is still maturing. |
| **Recommended action** | Document a post-release hotfix workflow covering: (a) how to issue a patch release (version bump, re-publish), (b) how to yank a broken release if necessary, (c) how to communicate breaking changes to downstream users. This should be part of the project's governance documentation before Phase 7 begins accepting external users. |
| **Confirmation evidence** | A documented post-release hotfix workflow exists in `DOCS/standards/` or `CONTRIBUTING.md`; the workflow covers version bumping, re-publishing, and yanking. |
| **Owner** | Phase 7 first cycle (documentation) |

---

## R41 — Formalize the EA-007/EDA-001/ETCA register-row requirement

| Field | Value |
|---|---|
| **ID** | R41 |
| **Priority** | **P3 — Low** |
| **Dimension** | P6 (Governance) |
| **Motivating evidence** | The SESSION_REGISTER.md notes that EMA-006 and EDA-001 were "committed without their own register rows/sections (each governance doc requires one)." ETCA-001 flags this. The pattern is that new audit types (EDA, ETCA) are introduced with governance documents that require register rows, but the rows are not always added at the time of the audit. This is a recurring governance hygiene gap. |
| **Recommended action** | Add a CI check or S4 checklist item that verifies every EA/EMA/EDA/ETCA session has a corresponding row in SESSION_REGISTER.md before the session is marked COMPLETE. This could be an extension of `tools/check_dv_register_gates.py` or a new tool. |
| **Confirmation evidence** | A tool or checklist item exists that detects missing register rows for global sessions; the tool is exercised against the historical EMA-006/EDA-001 gap. |
| **Owner** | Phase 7+ or opportunistic |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R37 | **P1** | P2, P6 | Create the missing PSR-038 and update the phase-6 README — self-documenting invariant broken at phase-close boundary |
| R38 | P2 | P3, P5 | Adopt extended timeout or parallel execution for analytics-session test re-verification (suite now 3,698 tests) |
| R39 | P3 | P3, P5 | Consider `pytest-xdist` parallel test option for CI and local verification |
| R40 | P2 | P6, P8 | Establish a post-release hotfix workflow for `prin-core` on PyPI |
| R41 | P3 | P6 | Formalize the EA/EMA/EDA/ETCA register-row requirement |

**One P1 recommendation (R37)** addresses the most visible documentation gap:
the missing PSR-038 and stale phase-6 README. Two P2 recommendations (R38,
R40) address the structural consequences of the project's first public
release: the test suite's size outgrowing the analytics session's
verification capacity, and the need for a post-release hotfix workflow. Two
P3 recommendations (R39, R41) are opportunistic improvements for future
phases.

Notably, **no P0 (Critical) recommendations exist** — the first time since
Phase 0 that the analytics session produces no P0 items. DV-019 (the
standing P0 from Phases 4 and 5) was closed by `Hotfix-DV019` before Phase 6
began. The project's risk posture has materially improved.

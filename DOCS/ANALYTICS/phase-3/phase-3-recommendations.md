# Phase 3 Recommendations Register

**Phase:** 3 — GPU kernels
**Date:** 2026-08-18
**Companion to:** [`phase-3-analytics-report.md`](phase-3-analytics-report.md)

Prioritized recommendations for Phase 4, derived from Phase 3 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority. R21 additionally carries the
two findings (PA3-F1, PA3-F2) this analytics session discovered
independently; per Analytics Methodology §7 these are recorded here and
also trigger the normal Session Cycle remediation process (a hotfix or the
next global session), not a fix performed inside this analytics session.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 4's next S4/global session |
| **P1 — High** | Significant improvement; should be addressed early | Phase 4 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 4 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 5+ or opportunistic |

---

## R21 — Fix the two findings this analytics session discovered (PA3-F1, PA3-F2)

| Field | Value |
|---|---|
| **ID** | R21 |
| **Priority** | **P0 — Critical** |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | This session's independent re-verification (analytics report §6.4) found `DOCS/PRIN_Project_Plan.md` §6's roadmap table still reads "3 — GPU kernels (parallel with 2)" with no completion marker, despite PSR-021, EA-004, and EMA-002 all independently confirming Phase 3's exit gate GREEN two days earlier — the plan has not been touched since `4d0f75b` (the Phase 2 close). Separately, `DOCS/experiments/README.md`'s file index (lines 19–74) omits `0081-wp021-s1-handoff.md`, which exists on disk and belongs to a cleanly-closed WP. |
| **Recommended action** | (a) Update `DOCS/PRIN_Project_Plan.md` §6's Phase 3 row to `**3 — GPU kernels** ✅ COMPLETE`, matching the convention already used for Phases 0–2, referencing PA3-F2. (b) Add a `DOCS/experiments/README.md` index entry for `0081-wp021-s1-handoff.md`, referencing PA3-F1. Both are small, mechanical, single-line-per-file fixes — do this immediately, since WP-022 (Phase 4) is already underway and the Project Plan is the document every future session is instructed to read first. |
| **Confirmation evidence** | `DOCS/PRIN_Project_Plan.md` §6's Phase 3 row carries `✅ COMPLETE`; `DOCS/experiments/README.md`'s index lists `0081-wp021-s1-handoff.md`. |
| **Owner** | Immediate hotfix, or the next WP-022 S4 session's documentation sweep |

---

## R22 — Extend the documentation-currency net beyond EA/EMA CHANGELOG entries to cross-cutting summary documents

| Field | Value |
|---|---|
| **ID** | R22 |
| **Priority** | **P1 — High** |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | Phase 2's R16 fixed the specific gap it found (EA/EMA sessions not updating `CHANGELOG.md`) and this session confirmed that fix holds — every Phase 3 global session has a proper CHANGELOG entry. But the *general* structural gap R16 targeted — no session type or checklist owns the currency of documents that summarize across WP-N cycles and global sessions, because no single WP-N S4 or EA/EMA closing checklist is "about" them — recurred this phase on two different documents, one of them (the Project Plan §6 roadmap table) considerably more consequential than a CHANGELOG entry. This is now a confirmed two-phase pattern (PA2-F1/PA2-F2 → PA3-F1/PA3-F2), not a one-off. |
| **Recommended action** | Add an explicit "cross-cutting document currency" item to the S4 checklist (Documentation Standards §7) that is *not* scoped to the current WP's own touched files: at every phase-closing S4 (the WP-N session that produces the phase exit-gate PSR), explicitly verify and update, if stale: (a) the Project Plan §6 roadmap table's completion marker for the closing phase, (b) `DOCS/experiments/README.md`'s index against the actual file listing, (c) `DOCS/sessions/SESSION_REGISTER.md`'s Global Sessions section against the actual EA/EMA report list. Making this a phase-close-specific (not every-WP-N) checklist item avoids re-litigating it 20 times a phase while still giving it a durable home. |
| **Confirmation evidence** | The Phase 4 exit-gate PSR (the WP-N S4 session that closes Phase 4) explicitly checks and confirms currency of all three documents named above, with evidence cited in its own §4/§5. |
| **Owner** | Standards amendment (`Documentation_Standards.md` §7) before the Phase 4 exit-gate S4 session |

---

## R23 — Escalate Snyk MCP unavailability to the maintainer as a tooling-access gap

| Field | Value |
|---|---|
| **ID** | R23 |
| **Priority** | **P1 — High** |
| **Dimension** | P5 (Evidence), P7 (Security) |
| **Motivating evidence** | Snyk MCP was unavailable in this session (confirmed via `ToolSearch`, no match) — the **second consecutive** phase-analytics session with this result (Phase 2, Phase 3), and EA-004 independently documented the same gap for its own session type, calling it "now 4 consecutive sessions." Analytics Methodology §5.1 item 11 explicitly states: "If unavailable across 2+ consecutive analytics or executive-audit sessions, escalate to the maintainer as a tooling-access gap." That threshold is now crossed for both session types simultaneously, and this recommendation (R18, Phase 2) already asked for this check to happen — it has been happening (both this session and EA-004 performed it), but the escalation itself has not yet been raised as a distinct maintainer-facing action item. |
| **Recommended action** | Raise Snyk MCP's persistent unavailability directly with the maintainer as a standing tooling-access gap requiring resolution (registration, credential/config fix, or an explicit decision to rely on the Snyk CLI compensating control permanently and update the standards to say so). Continue using the Snyk CLI as the compensating control in the meantime — it has produced consistent, evidence-backed results across all 4 EA sessions to date. |
| **Confirmation evidence** | Either Snyk MCP becomes available in a future analytics/EA/EMA session (closing this recommendation), or the maintainer explicitly confirms the Snyk-CLI-only posture is intentional and permanent, at which point `ANALYTICS_METHODOLOGY.md` §5.1 item 11 and `Executive_Audit_Governance_and_Methodology.md` §2 principle 6 should be updated to stop treating it as an open escalation. |
| **Owner** | Maintainer decision, surfaced at the next EA/EMA session or the Phase 4 analytics session |

---

## R24 — Consolidate and re-scope the GPU CI infrastructure gap (DV-001, DV-002, DV-005)

| Field | Value |
|---|---|
| **ID** | R24 |
| **Priority** | **P2 — Medium** |
| **Dimension** | P1 (Data and parity), P8 (Phase exit criteria), P9 (Risk) |
| **Motivating evidence** | Three deferred items — DV-001 (direct Triton 3.0 timing comparison), DV-002 (headless GPU CI runner), DV-005 (CUDA DLPack trainable-stack integration) — have now been open since WP-004 (Phase 0) and have advanced only partially across three subsequent phases: local CUDA hardware execution is now validated (WP-021), but nothing in CI enforces any GPU-backed test, and Phase 4 (`WP-022/WP-025`) is precisely the phase that needs DV-005 closed for the trainable-stack Torch bridge. Continuing to carry these as three separately-worded, slowly-drifting register rows risks losing track of the fact that they share one root cause: no CI-accessible GPU runner exists for this project. |
| **Recommended action** | At Phase 4 planning (WP-022 declaration or its S1), make an explicit maintainer decision on GPU CI runner strategy: self-hosted runner registration (the `gpu.yml` workflow already exists and is structurally ready, per EA-004 E9), a cloud GPU CI provider, or an explicit, time-bounded acceptance that GPU-backed gates remain local-only through Phase 4/5 with a stated re-audit gate. Whichever is chosen, record it as a single plan amendment covering all three DV items rather than three independent partial updates. |
| **Confirmation evidence** | A plan amendment (or an explicit DV register consolidation) states the GPU CI strategy and gives DV-001/DV-002/DV-005 a shared, concrete re-audit gate tied to a specific future WP. |
| **Owner** | Phase 4 planning (WP-022 S1 or the Phase 4 analytics session) |

---

## R25 — Investigate the `windows-latest` CubeCL-CPU runner slowdown (DV-016)

| Field | Value |
|---|---|
| **ID** | R25 |
| **Priority** | **P3 — Low** |
| **Dimension** | P5 (Evidence), P9 (Risk) |
| **Motivating evidence** | EA-004's addendum discovered `rust.yml`'s `test (windows-latest)` job runs `prin-kernels --features cpu` and `prin-sim --features cpu` roughly 10–15× slower on the GitHub-hosted `windows-latest` runner than on local hardware (~78 minutes vs. ~5 minutes total), consuming Actions minutes and CI turnaround time without providing additional evidentiary value (the tests pass either way). A `timeout-minutes: 120` safety net was added same-day to prevent a silent multi-hour hang, but the root cause (2-vCPU runner contention, Defender scanning overhead, or a `rayon`/thread-pool interaction) has not been investigated. |
| **Recommended action** | In a future maintenance session (not necessarily Phase-4-blocking), profile the `windows-latest` CubeCL-CPU test steps directly on a GitHub-hosted runner (e.g., via `RUST_LOG`/`rayon` thread-count instrumentation or a minimal repro workflow) to identify the dominant cost, then either reduce it (thread-count pinning, splitting the job, disabling a scanner false-positive trigger) or explicitly accept the cost with a documented rationale. |
| **Confirmation evidence** | A future PSR or maintenance-session report states a root cause and either a fix or an explicit acceptance with rationale; `rust.yml`'s `windows-latest` job time trends down or is explained. |
| **Owner** | Future maintenance session, not gated to any specific WP |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R21 | **P0** | P2, P6 | Fix PA3-F1 (`DOCS/experiments/README.md` index) and PA3-F2 (Project Plan roadmap-table marker) immediately |
| R22 | P1 | P2, P6 | Extend the documentation-currency net to cross-cutting summary documents at phase-close S4, not just EA/EMA CHANGELOG entries |
| R23 | P1 | P5, P7 | Escalate Snyk MCP's persistent (2+ analytics / 4 EA sessions) unavailability to the maintainer as a standing tooling-access gap |
| R24 | P2 | P1, P8, P9 | Consolidate DV-001/DV-002/DV-005 into one maintainer decision on GPU CI runner strategy before Phase 4 needs DV-005 closed |
| R25 | P3 | P5, P9 | Investigate the `windows-latest` CubeCL-CPU runner's ~10–15× slowdown (DV-016) in a future maintenance session |

**One P0 recommendation (R21) exists** — smaller in scope than Phase 2's
two P0s (R14/R15), consistent with Phase 3's much lower overall finding
count. R21 is purely mechanical (two documentation edits, no code or
gate changes) and should not delay Phase 4 by more than a single short
session. R22 and R23 are process/standards amendments that should land
early in Phase 4, since their purpose is to prevent Phase 4 analytics from
finding the identical class of gap a third time.

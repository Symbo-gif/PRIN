# Phase 5 Recommendations Register

**Phase:** 5 — Daemon and experiment tooling
**Date:** 2026-08-26
**Companion to:** [`phase-5-analytics-report.md`](phase-5-analytics-report.md)

Prioritized recommendations for Phase 6, derived from Phase 5 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 6's next S4/global session |
| **P1 — High** | Significant improvement; should be addressed early | Phase 6 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 6 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 7+ or opportunistic |

---

## R33 — Schedule the DV-019 dedicated hotfix/correction session before WP-033 S1

| Field | Value |
|---|---|
| **ID** | R33 |
| **Priority** | **P0 — Critical** |
| **Dimension** | P3 (Testing), P6 (Governance), P9 (Risk) |
| **Motivating evidence** | DV-019's flaky `gradients_flow_to_every_parameter` test has now recurred at least **six times** across four modules (`bands.rs`, `hybrid.rs`, `phase_tracker.rs`, `test_train_bridge_slot_attention.py`), spanning three consecutive phases. Phase 4's R28 called for a dedicated hotfix/correction session "before session 0109 (WP-028 S1) begins"; EA-006's E-F2 recorded this precondition was never honored; and WP-033 S1's session brief now carries a hard, mechanically-enforced entry-condition gate blocking its start until the hotfix session actually runs. Two concrete mitigations remain on record in DV-019: (a) pin the test single-threaded (requires reconfiguring rayon's process-wide global thread pool — a broad architectural change); (b) strengthen the fixture so the gradient is robustly bounded away from zero (a genuine mathematical-fixture-design task). |
| **Recommended action** | Open the dedicated governed hotfix/correction session (per Development Workflow Standards §7) that R28 originally called for, implementing one of the two already-identified mitigations. This is now mechanically enforced by WP-033 S1's entry-condition gate (EA-006 E-F2 remediation). The session should evaluate both mitigation options against the evidence in DV-019 and implement the lower-risk one. |
| **Confirmation evidence** | A hotfix/correction session report closes DV-019 with one of the two recorded mitigations implemented and verified (e.g., 10+ consecutive `cargo test -p prin-train` runs at default thread count with zero recurrence, plus the Python-side test also clean). |
| **Owner** | A dedicated hotfix/correction session — now mechanically gated before WP-033 S1 (session 0129) can begin |

---

## R34 — Add a mechanical enforcement mechanism for phase-closing preconditions

| Field | Value |
|---|---|
| **ID** | R34 |
| **Priority** | **P1 — High** |
| **Dimension** | P6 (Governance) |
| **Motivating evidence** | Phase 5's most significant governance gap (EA-006 E-F2, this session's PA5-F1) was not a missing rule — R28's precondition was explicitly documented in the Deferred Validation Register, the Phase 4 recommendation implementation governance document, and the DV register review log. The gap was that no *mechanical* enforcement existed: the precondition was a text entry in a Markdown document that every session read but none checked. EA-006's fix (adding a hard entry-condition line to WP-033 S1's session brief) is the right pattern, but it was applied retroactively after the entire phase had already slipped past. The same class of risk — "documented precondition with no enforcement" — could affect any future inter-phase recommendation or DV-register gate. |
| **Recommended action** | Extend `tools/check_deviation_ledger.py` (or add a companion tool) to also parse the Deferred Validation Register for any items whose "re-audit gate" names a specific session number, and verify that the named precondition has been satisfied before the named session's S1 commit is accepted. This would mechanically enforce the same class of gate EA-006 added by hand to WP-033 S1, but for all future sessions automatically. Alternatively, add a CI step that checks the DV register against the session register. |
| **Confirmation evidence** | A tool or CI step exists that can detect when a DV register item's named precondition session has been reached without the precondition being satisfied; the tool is exercised against at least one historical case (e.g., R28/DV-019) and correctly flags the gap. |
| **Owner** | Phase 6 first cycle (opportunistic; could be WP-033 S4 or a dedicated tooling session) |

---

## R35 — Make an explicit Phase 6 scoping decision on DV-004 (kernel body coverage gap)

| Field | Value |
|---|---|
| **ID** | R35 |
| **Priority** | **P3 — Low** |
| **Dimension** | P1 (Data), P9 (Risk) |
| **Motivating evidence** | DV-004 (ten non-instrumentable `#[cube(launch)]` kernel bodies; `cargo-llvm-cov` reports understated coverage) has been open since Phase 0 (WP-004) with no movement in five consecutive phases. The instrumentable surrounding code is ≥95% across all modules, and kernel equivalence tests validate correctness, so this is not a quality gap — but it has been an open register entry for the project's entire lifetime with no explicit disposition decision beyond "re-audit each cycle." |
| **Recommended action** | At Phase 6 planning, make an explicit maintainer decision (recorded as a DV-register update) on whether DV-004 is closed as "kernel equivalence tests are the accepted coverage mechanism for `#[cube(launch)]` bodies; line coverage is not applicable" or remains open pending a specific future Rust toolchain advancement that might enable kernel-body instrumentation. Either is a legitimate outcome; what is missing is a formal disposition rather than an indefinitely carried "OPEN" status on an item that has not moved in five phases. |
| **Confirmation evidence** | The Deferred Validation Register's DV-004 row reflects an explicit, dated disposition rather than "OPEN — re-audited, unaffected" repeated unchanged. |
| **Owner** | Phase 6 planning (WP-033 S1 or the Phase 6 analytics session) |

---

## R36 — Consider vendoring `math-audit-mcp` into the PRIN repository

| Field | Value |
|---|---|
| **ID** | R36 |
| **Priority** | **P3 — Low** |
| **Dimension** | P5 (Evidence), P9 (Risk) |
| **Motivating evidence** | EMA-005 remediation added DV-028 ("vendoring `math-audit-mcp` into PRIN") to the Deferred Validation Register, consolidating the recurring EMA-004/EMA-005 architectural-decision mention into one tracked register row. The tool has its own git repository (since EMA-004, M-F6), but every EMA session to date has had to verify the tool's commit hash, working-tree state, and `.venv` metadata independently — and M-F9 (beta-function allowlist gap), M-F10 (Lean toolchain auto-upgrade), and M-F11 (stale dist-info) are all tool-side issues that would be simpler to manage if the tool were versioned alongside the project. |
| **Recommended action** | Evaluate vendoring `math-audit-mcp` as a git submodule or subtree at a known-good commit, so that tool-side changes (allowlist updates, new adapters) are tracked in the same commit history as the claims they affect. This would eliminate the "verify the tool's git state" step from every EMA session and make tool-remediation commits (like `5fdfeb0`'s M-F9 fix) part of the project's own history. |
| **Confirmation evidence** | A decision is recorded in the DV register (DV-028 dispositioned); if vendored, the tool's commit hash is pinned in the project's git history and EMA sessions no longer need to independently verify the tool's working-tree state. |
| **Owner** | Phase 6+ or opportunistic; requires maintainer decision on repository structure |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R33 | **P0** | P3, P6, P9 | Schedule the DV-019 dedicated hotfix/correction session before WP-033 S1 — now mechanically gated, six recurrences across four modules |
| R34 | P1 | P6 | Add mechanical enforcement for DV-register preconditions (extend `check_deviation_ledger.py` or add CI step) |
| R35 | P3 | P1, P9 | Make an explicit Phase 6 scoping decision on DV-004 (kernel body coverage gap, open since Phase 0) |
| R36 | P3 | P5, P9 | Consider vendoring `math-audit-mcp` into the PRIN repository (DV-028) |

**One P0 recommendation (R33)** exists — but unlike prior P0 recommendations,
its enforcement is already mechanically wired: WP-033 S1's session brief
carries a hard entry-condition gate (EA-006 E-F2 remediation) that blocks
the session from starting until the DV-019 hotfix session actually runs.
The recommendation is to *execute* what is already enforced, not to create
new enforcement. One P1 recommendation (R34) addresses the systemic class
of governance gap that R28/DV-019 demonstrated: documented preconditions
without mechanical enforcement. R35 and R36 are lower-urgency scoping/
architecture items appropriate for opportunistic handling.

# Phase 4 Recommendations Register

**Phase:** 4 — Trainable stack and Torch bridge
**Date:** 2026-08-21
**Companion to:** [`phase-4-analytics-report.md`](phase-4-analytics-report.md)

Prioritized recommendations for Phase 5, derived from Phase 4 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority. R26 additionally carries the
two findings (PA4-F1, PA4-F2) this analytics session discovered
independently; per Analytics Methodology §7 these are recorded here and
also trigger the normal Session Cycle remediation process (a hotfix or the
next global session), not a fix performed inside this analytics session.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 5's next S4/global session |
| **P1 — High** | Significant improvement; should be addressed early | Phase 5 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 5 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 6+ or opportunistic |

---

## R26 — Fix the two findings this analytics session discovered (PA4-F1, PA4-F2)

| Field | Value |
|---|---|
| **ID** | R26 |
| **Priority** | **P0 — Critical** |
| **Dimension** | P2 (Documentation), P5 (Evidence), P6 (Governance) |
| **Motivating evidence** | This session's independent re-verification (analytics report Executive Summary, §4.2, §5.4, §6.4) found: (a) `DOCS/PRIN_Project_Plan.md` §6's roadmap table still carries no completion marker for Phase 4, despite PSR-027 declaring the exit gate GREEN and Documentation Standards §7 item 9 explicitly naming the gap in PSR-027 §8(a) without it being fixed; (b) the "Sphinx build: 0 warnings" claim repeated across PSR-022 through PSR-027 and EA-005 is false on a clean build — a fresh output directory reproducibly shows 12 warnings-as-errors, reproduced twice independently this session. |
| **Recommended action** | (a) Update `DOCS/PRIN_Project_Plan.md` §6's Phase 4 row to `**4 — Trainable stack + torch bridge** ✅ COMPLETE`, matching the convention used for Phases 0–3, referencing PA4-F1. (b) Fix the 12 Sphinx warnings: correct `python/prin/__init__.py`'s module-docstring `Subpackages:` definition-list indentation (the wrapped continuation lines for `prin.dlpack`, `prin.metrics`, `prin.train`, `prin.experiments`, `prin.parity` need to match the first line's indent, not exceed it) and resolve the `prin.nn.TrackingResult` duplicate-object-description warnings (either add `:no-index:` to one of the two autodoc entries, or restructure so `TrackingResult` is documented once — via its defining module or via the re-export, not both). Verify the fix with a genuinely clean build (`rm -rf DOCS/sphinx/_build` first, or build to a fresh temp directory) before claiming "0 warnings" again. |
| **Confirmation evidence** | `DOCS/PRIN_Project_Plan.md` §6's Phase 4 row carries `✅ COMPLETE`; a Sphinx build against a freshly-deleted or newly-created `_build` output directory reports 0 warnings. |
| **Owner** | Immediate hotfix, or the next WP-028 S4 session's documentation sweep |

---

## R27 — Require an explicit, recorded rationale whenever a phase-closing checklist item is deferred rather than acted on

| Field | Value |
|---|---|
| **ID** | R27 |
| **Priority** | **P1 — High** |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | Documentation Standards §7 item 9 (R22's fix, built specifically to prevent a third occurrence of the Project-Plan-roadmap-marker gap) *did* fire correctly at WP-027 S4 — PSR-027 §8(a) explicitly names the requirement and the gap. But the session then recorded the fix as "recommended for the next cycle" and left the one-line edit undone, rather than following the item's own imperative text ("explicitly verify and, **if stale, update**"). This is a qualitatively different, and arguably more concerning, failure mode than Phase 2/3's total blind spot: the safeguard worked exactly as designed and was still overridden by a same-session judgment call, with no explicit rationale recorded for *why* deferral was chosen over a trivial one-line fix. A parallel instance (EMA-003 skipping its own required closing-checklist entries, later self-corrected by EMA-004) shows the same class of risk in the EA/EMA closing-checklist mechanism (R16). |
| **Recommended action** | Amend Documentation Standards §7 (both item 9 and, by cross-reference, the EA/EMA closing checklists in `Executive_Audit_Governance_and_Methodology.md` §5 / `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8): when a phase-closing or global-session closing-checklist item identifies a genuine gap, the session must either fix it before closing or record an explicit, reviewable rationale for deferring it (not a bare "recommended for next cycle" note) — mirroring the rigor already required of S1's parity-evidence-disposition requirement (R15). A one-line documentation edit with no code risk should default to "fix now," matching the disposition Phase 3's R21 already established as precedent for the identical situation. |
| **Confirmation evidence** | The next phase-closing S4 (or EA/EMA closing session) either fixes every checklist item it identifies as stale, or records an explicit rationale for deferral that a later analytics session can evaluate rather than merely note as unresolved. |
| **Owner** | Standards amendment (`Documentation_Standards.md` §7, and the two EA/EMA governance docs by cross-reference) before Phase 5's first phase-closing session |

---

## R28 — Schedule a dedicated governed hotfix/correction session for DV-019

| Field | Value |
|---|---|
| **ID** | R28 |
| **Priority** | **P1 — High** |
| **Dimension** | P3 (Testing), P9 (Risk) |
| **Motivating evidence** | `prin-train::bands::tests::gradients_flow_to_every_parameter` has recurred as an intermittent, thread-contention-sensitive flake **four times** across Phase 4 (WP-023 S1, WP-024 S1, WP-025 S3-exec, WP-027 S1), now affecting three modules (`bands.rs`, `hybrid.rs`, `phase_tracker.rs`). Root cause is narrowed to `bands.rs:801`'s `w_gamma` gradient-presence assertion sitting on a documented "knife-edge" gradient value, and two concrete, low-risk mitigation options are on record (pin the test single-threaded; strengthen the fixture so the gradient is robustly bounded away from zero). `bands.rs` is WP-022's closed, frozen scope, so no later WP has fixed it in passing — correctly, per Development Workflow Standards §3 — but it has also not been assigned to any concrete future session, unlike every other open Phase 4 DV item (DV-021, DV-005 both concretely checkpointed to WP-027 S1). |
| **Recommended action** | Open a dedicated, governed hotfix/correction session (per Development Workflow Standards §7) specifically to implement one of the two already-identified mitigations for DV-019, rather than waiting for a fifth recurrence to force the issue. This is a small, well-scoped, low-risk fix with the diagnosis already complete — the only missing step is scheduling it. |
| **Confirmation evidence** | A hotfix/correction session report closes DV-019 with one of the two recorded mitigations implemented and verified (e.g., 10+ consecutive `cargo test -p prin-train` runs at default thread count with zero recurrence). |
| **Owner** | A dedicated hotfix/correction session, opportunistic but no longer indefinitely deferred — target before Phase 5's exit gate |

---

## R29 — Resolve DV-021 (bridge overhead `<5%`) via a plan amendment, not an indefinitely open deviation

| Field | Value |
|---|---|
| **ID** | R29 |
| **Priority** | **P1 — High** |
| **Dimension** | P1 (Data and parity), P8 (Phase exit criteria) |
| **Motivating evidence** | Plan §6's Phase 4 exit criterion reads "bridge overhead <5%," with no qualifying language. Three independent, increasingly rigorous measurement rounds (WP-025 S3's 5-run median-of-medians, the WP-025 S3-exec optimization attempt, and WP-027 S1's re-corroboration) consistently show this target is **not met** at small batch/shape sizes (+37.8% to +40.6% across the three measurements) and is architecturally attributed to fixed-cost `torch.autograd.Function.apply()`/`from_dlpack()` dispatch overhead inherent to the mandated bridge architecture, not a fixable Rust-side inefficiency. DV-021 has been carried as an open, "governed" deviation since WP-025 S2 without a plan amendment ever revising or formally accepting the criterion's text — a materially weaker resolution than the directly analogous Phase 2 precedent (amendment #21), which formally re-scoped an unmet ≥8×/16-core sweep-speedup target to hardware-evidenced values before the phase closed. |
| **Recommended action** | Draft a plan amendment that does one of: (a) revises Plan §6's Phase 4 criterion text to state the actual, evidence-backed overhead figures and their architectural explanation (following amendment #21's precedent exactly), explicitly scoping the `<5%` target to shapes large enough to amortize the fixed per-call dispatch cost (e.g., the moderate-shape figure, ~4.5–6.5%, is close to the original target and the small-shape figure is dominated by fixed overhead any batch-size increase would shrink); or (b) explicitly accepts the architectural cost as a permanent, documented characteristic of the PyO3/DLPack/`torch.autograd.Function` bridge pattern with maintainer sign-off, closing DV-021 rather than leaving it open indefinitely. Either resolution should happen before this gap is inherited by a Phase 5 daemon/training-hook WP that might build on the same bridge pattern without knowing its performance envelope is unresolved. |
| **Confirmation evidence** | A new plan amendment (#30 or higher) addresses DV-021 explicitly; the Deferred Validation Register's DV-021 row is updated to `CLOSED` or `AMENDED` rather than `OPEN`. |
| **Owner** | Maintainer decision, at Phase 5 planning (WP-028 declaration/S1) or the next global session |

---

## R30 — Adopt a clean-build discipline for the Sphinx verification step

| Field | Value |
|---|---|
| **ID** | R30 |
| **Priority** | **P1 — High** |
| **Dimension** | P2 (Documentation), P5 (Evidence) |
| **Motivating evidence** | PA4-F2's root cause (analytics report §4.2, Executive Summary) is not the 12 warnings themselves — it is that every S4/audit session's "Sphinx build: 0 warnings" verification command reused the same local, gitignored `DOCS/sphinx/_build/html` directory, and Sphinx's incremental build does not detect that an `automodule`-sourced Python docstring changed underneath an unmodified `.rst` page. This let a false "gate green" claim persist across the entire phase. The same mechanism could silently mask any future autodoc-sourced warning in any phase that touches a docstring without touching its corresponding `.rst` page. |
| **Recommended action** | Update `AGENTS.md`'s local verification one-liner and every standards document that specifies the Sphinx build command (Coding Standards §5, Documentation Standards §7 item 3) to require a clean build: either delete `DOCS/sphinx/_build` immediately before the build command, or build to a freshly-created temporary directory each time, so incremental caching can never mask a genuine warning. This is a small, mechanical change to a single command sequence. |
| **Confirmation evidence** | `AGENTS.md` and the relevant standards' Sphinx build command is prefixed with a clean/fresh-directory step; the next S4 session's Sphinx verification is run against a demonstrably clean build. |
| **Owner** | Standards amendment (`AGENTS.md`, Coding Standards §5) before Phase 5's first S4 session |

---

## R31 — Make an explicit Phase 5 scoping decision on DV-005 (CUDA Burn backend)

| Field | Value |
|---|---|
| **ID** | R31 |
| **Priority** | **P3 — Low** |
| **Dimension** | P1 (Data and parity), P9 (Risk) |
| **Motivating evidence** | The entire `prin-train` trainable stack is CPU-only (`burn` with `features = ["std", "ndarray", "autodiff"]`, no `burn-cuda`/`burn-wgpu` anywhere in the workspace) — DV-005 has now been open since WP-003 (Phase 0) and has advanced only as far as "the CPU-path bridge is delivered and validated; CUDA remains unbridged." WP-027 S1 recorded a specific recommendation ("do not pull into near-term Phase 5 scope absent a concrete workload that needs it") but no plan amendment has formally closed or re-scoped DV-005 against that recommendation. |
| **Recommended action** | At Phase 5 planning, make an explicit maintainer decision (recorded as a DV-register update, and a plan amendment if it changes any Plan §6 text) on whether DV-005 is closed as "CPU-only trainable stack is the accepted Phase 4/5 posture" or remains open pending a specific future Phase 5/6 workload. Either is a legitimate outcome; what is missing is a formal disposition rather than an indefinitely carried "OPEN" status on an item that has not moved in four consecutive phases. |
| **Confirmation evidence** | The Deferred Validation Register's DV-005 row reflects an explicit, dated disposition rather than "OPEN — re-audited, unaffected" repeated unchanged. |
| **Owner** | Phase 5 planning (WP-028 S1 or the Phase 5 analytics session) |

---

## R32 — Reduce PSR-declaration-text drift by quoting the session brief's mission text directly

| Field | Value |
|---|---|
| **ID** | R32 |
| **Priority** | **P3 — Low** |
| **Dimension** | P6 (Governance) |
| **Motivating evidence** | Amendment #29 (WP-024) is the fourth consecutive-phase instance of the same pattern first seen at Phase 2's amendments #18–#20: a Project State Report's own "next WP declaration" section paraphrases the upcoming work package's scope, and the paraphrase drifts from the session brief's actual mission text and the Rebuild Planning Document's normative symbol mapping (here, naming non-existent classes `PhaseAdam`/`KuramotoOptimizer` instead of the real `SCALR`/`RIP`/`SyncGD`). Every instance has been caught and correctly resolved via an evidence-backed amendment with zero code impact — but four recurrences of the identical low-severity pattern across two phases suggests a cheap structural fix is available. |
| **Recommended action** | When a PSR's §7 "next work package declaration" names specific symbols, classes, or file paths, require it to directly quote (not paraphrase) the governing normative source — the session brief's own mission-text bullet, or the Rebuild Planning Document's symbol-mapping table row — rather than restating it from memory. This is a lightweight authoring-discipline change, not a new checklist item requiring verification effort. |
| **Recommended action (alternative, lower-effort)** | If direct quoting is judged too rigid for a declaration that necessarily previews not-yet-written work, at minimum require the declaring session to `grep` the archived PRINet 3.0 reference tree for any named class before including it in the declaration — the same verification step that has correctly caught every instance of this pattern to date, made an explicit authoring step rather than an audit-time catch. |
| **Confirmation evidence** | Phase 5's PSRs show zero instances of this pattern in their own S2 audits. |
| **Owner** | Documentation Standards or Development Workflow Standards amendment, opportunistic |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R26 | **P0** | P2, P5, P6 | Fix PA4-F1 (Project Plan roadmap-table marker) and PA4-F2 (12 genuine Sphinx warnings masked by stale build cache) immediately |
| R27 | P1 | P2, P6 | Require an explicit, recorded rationale whenever a correctly-firing phase-closing checklist item is deferred rather than fixed |
| R28 | P1 | P3, P9 | Schedule a dedicated hotfix/correction session for DV-019's four-times-recurring flaky test — diagnosis is complete, only scheduling remains |
| R29 | P1 | P1, P8 | Resolve DV-021 (bridge overhead `<5%`, not met, architecturally attributed) via a plan amendment, following the amendment #21 precedent, rather than an indefinitely open deviation |
| R30 | P1 | P2, P5 | Require a clean/fresh `_build` directory for every Sphinx verification command, closing the mechanism that produced PA4-F2 |
| R31 | P3 | P1, P9 | Make an explicit Phase 5 scoping decision on DV-005 (CUDA Burn backend), open since Phase 0 with no movement in four phases |
| R32 | P3 | P6 | Reduce PSR-declaration-text drift (4 recurrences across 2 phases) by quoting the session brief/Rebuild Planning Document directly rather than paraphrasing |

**One P0 recommendation (R26) exists**, matching Phase 3's precedent — both
of its component fixes are small and mechanical (one documentation-table
edit, one docstring/autodoc formatting fix) and should not delay Phase 5 by
more than a single short session. Four P1 recommendations (R27–R30) address
this phase's most substantive governance and evidentiary findings and
should land early in Phase 5, before a sixth WP inherits any of these gaps
silently. R31 and R32 are lower-urgency scoping/process-hygiene items
appropriate for opportunistic handling.

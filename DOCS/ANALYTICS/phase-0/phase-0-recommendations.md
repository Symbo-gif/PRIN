# Phase 0 Recommendations Register

**Phase:** 0 — Foundation
**Date:** 2026-08-07
**Companion to:** [`phase-0-analytics-report.md`](phase-0-analytics-report.md)

Prioritized recommendations for Phase 1, derived from Phase 0 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 1 S1 |
| **P1 — High** | Significant improvement; should be addressed early | Phase 1 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 1 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 2+ or opportunistic |

---

## R1 — Update READMEs during S1, not S4

| Field | Value |
|---|---|
| **ID** | R1 |
| **Priority** | P1 — High |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | 5 of 33 Phase 0 findings were stale READMEs caught in S2 and fixed in S3: WP001-F9, WP002-F3, WP004-F9, WP005-F3, WP005-F4. This is 15% of all findings and the single largest root-cause category after security. |
| **Recommended action** | Add "update touched-directory READMEs" to the S1 exit criteria checklist in Development Workflow Standards §3 (S1 rules). S1 authors should update READMEs when they add/change directory contents, not defer to S4. S4 remains the final consistency sweep. |
| **Confirmation evidence** | Phase 1 audits (A8 dimension) show 0 stale-README findings. |
| **Owner** | Standards amendment (PR to `DOCS/standards/Development_Workflow_and_Audit_Standards.md`) |

## R2 — Expand differential testing from representative to exhaustive

| Field | Value |
|---|---|
| **ID** | R2 |
| **Priority** | P1 — High |
| **Dimension** | P1 (Data and parity) |
| **Motivating evidence** | The differential harness (`parity/test_parity_differential.py`) runs 6 representative cases, not all 504. The corpus has 504 cases with SHA-256 manifest verification, but the differential CI job is representative, not exhaustive. When `prin-dynamics` numerics land in Phase 1, all 504 cases should be run against the new implementation. |
| **Recommended action** | In Phase 1 (WP-006 or the first WP that implements dynamics numerics), wire `parity.yml` to run all 504 corpus cases against the new PRIN implementation. Consider parameterizing for parallel execution to keep CI runtime reasonable. |
| **Confirmation evidence** | `parity.yml` runs 504/504 cases green; project state report records the full count. |
| **Owner** | Phase 1 WP implementation + `parity.yml` update |

## R3 — Improve `cargo-llvm-cov` coverage reporting for kernel bodies

| Field | Value |
|---|---|
| **ID** | R3 |
| **Priority** | P2 — Medium |
| **Dimension** | P3 (Testing) |
| **Motivating evidence** | Amendment #10 documents 86.36% line coverage due to non-instrumentable `#[cube(launch)]` kernel bodies. Kernel-equivalence tests compensate for correctness, but the coverage number understates actual test coverage and could be misleading in future audits. |
| **Recommended action** | Investigate supplementing `cargo-llvm-cov` with a custom kernel-coverage metric (e.g., counting executed `#[cube(launch)]` invocations via `StepReport` or a test harness counter). Alternatively, document the coverage gap more prominently in the coverage report output. |
| **Confirmation evidence** | Coverage report distinguishes instrumentable vs non-instrumentable code; or a supplementary kernel-coverage metric is reported alongside `cargo-llvm-cov`. |
| **Owner** | Phase 1 or Phase 3 (when more kernels land) |

## R4 — Continue proactive GitHub secret scanning availability checks

| Field | Value |
|---|---|
| **ID** | R4 |
| **Priority** | P2 — Medium |
| **Dimension** | P7 (Security) |
| **Motivating evidence** | Amendment #5's Gitleaks substitute has been in force since WP-001 (2026-07-27). GitHub native secret scanning remains unavailable for this private repository. The substitute is functional but is a compensating control, not the native platform control. |
| **Recommended action** | Continue per-cycle availability rechecks (already required by amendment #5). When GitHub native secret scanning becomes available, migrate from the substitute to the native control, retire amendment #5, and record the migration in the plan amendment log. |
| **Confirmation evidence** | Each Phase 1 project state report records the availability check result. When native scanning is enabled, amendment #5 is retired. |
| **Owner** | Each cycle's S3/S4 session |

## R5 — Create a Deferred Validation Register

| Field | Value |
|---|---|
| **ID** | R5 |
| **Priority** | P2 — Medium |
| **Dimension** | P9 (Risk and deferred validation) |
| **Motivating evidence** | 5 deferred validation items are documented across 4 amendments (#7, #11, #12, #13). They are tracked in the risk section of each project state report but not in a single dedicated register, making it harder to track closure status across phases. |
| **Recommended action** | Create a "Deferred Validation Register" as a section in the project state report template or as a standalone document in `DOCS/reports/`. List all deferred items, their re-audit gates (specific WP/phase), current status, and the amendment that governs them. Update it each cycle. |
| **Confirmation evidence** | The register exists and is updated in each Phase 1 project state report; deferred items are tracked to closure. |
| **Owner** | Standards amendment (project state report template) + each cycle's S4 |

## R6 — Ensure WP-006 implements the `Seed` type with reproducibility property tests

| Field | Value |
|---|---|
| **ID** | R6 |
| **Priority** | P0 — Critical |
| **Dimension** | P4 (Coding and architecture) |
| **Motivating evidence** | WP-006 (next WP, already declared in `DOCS/reports/005-project-state.md` §6) declares the single counter-based `Seed` type (Philox/PCG64) as in-scope. Deterministic seeding is a Plan §4 architecture rule ("explicit state, no hidden globals") and is critical for all future stochastic entry points, the reproducibility pipeline (F4), and the experimentation campaign (Phase 7). |
| **Recommended action** | Ensure WP-006 S1 implements the `Seed` type with: (1) property tests for reproducibility across CPU/GPU and across runs, (2) threading through every stochastic entry point, (3) no hidden global RNG. The WP-006 audit (A4) should verify reproducibility. |
| **Confirmation evidence** | WP-006 audit A4 confirms `Seed` reproducibility; no hidden global RNG exists in the codebase. |
| **Owner** | WP-006 S1/S2 |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R1 | P1 | P2, P6 | Update READMEs during S1, not S4 |
| R2 | P1 | P1 | Expand differential testing to all 504 cases |
| R3 | P2 | P3 | Improve kernel coverage reporting |
| R4 | P2 | P7 | Continue secret scanning availability checks |
| R5 | P2 | P9 | Create a Deferred Validation Register |
| R6 | P0 | P4 | Implement `Seed` type with reproducibility tests in WP-006 |

No P0 recommendations block Phase 1 from starting — R6 is the WP-006
declaration itself, already in force. The remaining recommendations are
process improvements that should be addressed during Phase 1.

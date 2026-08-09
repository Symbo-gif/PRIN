# Phase 1 Recommendations Register

**Phase:** 1 — Dynamics core
**Date:** 2026-08-09
**Companion to:** [`phase-1-analytics-report.md`](phase-1-analytics-report.md)

Prioritized recommendations for Phase 2, derived from Phase 1 analytics.
Each recommendation states its dimension, motivating evidence, recommended
action, confirmation evidence, and priority.

---

## Priority legend

| Priority | Meaning | Action timing |
|---|---|---|
| **P0 — Critical** | Blocks progression or introduces risk | Before Phase 2 S1 |
| **P1 — High** | Significant improvement; should be addressed early | Phase 2 first cycle |
| **P2 — Medium** | Process improvement; address when feasible | Phase 2 mid-phase |
| **P3 — Low** | Nice-to-have; track for future phases | Phase 3+ or opportunistic |

---

## R7 — Strengthen S4 consistency sweep to catch stale documentation

| Field | Value |
|---|---|
| **ID** | R7 |
| **Priority** | P1 — High |
| **Dimension** | P2 (Documentation), P6 (Governance) |
| **Motivating evidence** | EA-002 found 5 stale documentation items (E-F7–E-F11) that the regular S4 consistency sweep missed: `prin-dynamics` crate docs inaccuracy, RK4 rustdoc typo, `SmallWorld` rewiring docs, `DOCS/experiments/README.md` index, `DOCS/audits/README.md` index. Phase 0 recommendation R1 (update READMEs in S1) was not fully addressed — the S1 process was not amended. |
| **Recommended action** | Add an explicit "documentation accuracy sweep" step to the S4 checklist in `DOCS/standards/Documentation_Standards.md`: (1) verify all READMEs in touched directories match current code, (2) verify all rustdoc code examples compile, (3) verify all index/README files in `DOCS/` subdirectories are current. This supplements the existing S4 README check. |
| **Confirmation evidence** | Phase 2 executive audit (if conducted) finds 0 stale documentation items; or Phase 2 S4 session briefs record explicit documentation accuracy verification steps. |
| **Owner** | Standards amendment (PR to `DOCS/standards/Documentation_Standards.md`) |

---

## R8 — Complete the exhaustive 504-case Python differential CI

| Field | Value |
|---|---|
| **ID** | R8 |
| **Priority** | P1 — High |
| **Dimension** | P1 (Data and parity) |
| **Motivating evidence** | Phase 0 recommendation R2 called for expanding differential testing from representative (6 cases) to exhaustive (504 cases). Phase 1 added 56 Rust parity tests that provide equivalent coverage at the Rust level, but the Python `parity.yml` workflow still runs only 6 representative cases. The Python-level end-to-end validation (from Python bindings through Rust core to reference comparison) remains incomplete. |
| **Recommended action** | In Phase 2 (WP-012 or the first WP that adds new integrators), wire `parity.yml` to run all 504 corpus cases against the new PRIN implementation. Consider parameterizing with `pytest-xdist` for parallel execution to keep CI runtime reasonable. Alternatively, add a separate `parity_exhaustive.yml` workflow that runs on a slower schedule (e.g., nightly). |
| **Confirmation evidence** | `parity.yml` (or a dedicated exhaustive workflow) runs 504/504 cases green; project state report records the full count. |
| **Owner** | Phase 2 WP implementation + `parity.yml` update |

---

## R9 — Create a Deferred Validation Register

| Field | Value |
|---|---|
| **ID** | R9 |
| **Priority** | P2 — Medium |
| **Dimension** | P9 (Risk and deferred validation) |
| **Motivating evidence** | Phase 0 recommendation R5 called for a dedicated Deferred Validation Register. Phase 1 did not create one. Deferred items are tracked across multiple documents: amendments #7, #10, #11, #12, #13 (Phase 0) and #14 (Phase 1), project state reports 006–011, and the risk sections of audit reports. This makes it harder to track closure status across phases. The list of deferred items is growing: CUDA DLPack, Triton comparison, VitisAI NPU, wgpu CI, exponential integrators, tensor decompositions, GPU kernel updates, DirectML/VitisAI ONNX validation. |
| **Recommended action** | Create a "Deferred Validation Register" as a standalone document in `DOCS/reports/` or as a section in the project state report template. List all deferred items, their re-audit gates (specific WP/phase), current status, and the amendment that governs them. Update it each cycle. |
| **Confirmation evidence** | The register exists and is updated in each Phase 2 project state report; deferred items are tracked to closure. |
| **Owner** | Standards amendment (project state report template) + each cycle's S4 |

---

## R10 — Improve `cargo-llvm-cov` coverage reporting for kernel bodies

| Field | Value |
|---|---|
| **ID** | R10 |
| **Priority** | P2 — Medium |
| **Dimension** | P3 (Testing) |
| **Motivating evidence** | Phase 0 recommendation R3 called for improving kernel coverage reporting. This was not addressed in Phase 1 (the kernel code was unchanged). Amendment #10 documents 86.36% line coverage due to non-instrumentable `#[cube(launch)]` kernel bodies. As Phase 3 will add more kernels, this coverage gap will become more significant. |
| **Recommended action** | Investigate supplementing `cargo-llvm-cov` with a custom kernel-coverage metric (e.g., counting executed `#[cube(launch)]` invocations via a test harness counter). Alternatively, document the coverage gap more prominently in the coverage report output. Phase 3 (WP-017/018) is the natural inflection point. |
| **Confirmation evidence** | Coverage report distinguishes instrumentable vs non-instrumentable code; or a supplementary kernel-coverage metric is reported alongside `cargo-llvm-cov`. |
| **Owner** | Phase 3 (WP-017) |

---

## R11 — Continue proactive GitHub secret scanning availability checks

| Field | Value |
|---|---|
| **ID** | R11 |
| **Priority** | P2 — Medium |
| **Dimension** | P7 (Security) |
| **Motivating evidence** | Phase 0 recommendation R4 called for continued per-cycle availability rechecks of GitHub native secret scanning. This was maintained throughout Phase 1 (amendment #5 remains in force). The substitute is functional but remains a compensating control. |
| **Recommended action** | Continue per-cycle availability rechecks. When GitHub native secret scanning becomes available, migrate from the substitute to the native control, retire amendment #5, and record the migration in the plan amendment log. |
| **Confirmation evidence** | Each Phase 2 project state report records the availability check result. When native scanning is enabled, amendment #5 is retired. |
| **Owner** | Each cycle's S3/S4 session |

---

## R12 — Add `strict-checks` feature coverage to `cargo-llvm-cov` runs

| Field | Value |
|---|---|
| **ID** | R12 |
| **Priority** | P2 — Medium |
| **Dimension** | P3 (Testing) |
| **Motivating evidence** | The `strict-checks` feature flag in `prin-dynamics` toggles between clamp/repair and typed-error guard behavior. WP-006 F2 identified that `rust.yml` did not exercise this feature; this was fixed. However, `cargo-llvm-cov` runs do not currently merge coverage from both default and `strict-checks` builds, so the reported coverage understates the actual test coverage of the feature-gated code. |
| **Recommended action** | When running `cargo-llvm-cov`, merge coverage from both `cargo test` (default) and `cargo test --features strict-checks` to produce a unified coverage report. This ensures the coverage number reflects all code paths. |
| **Confirmation evidence** | `cargo-llvm-cov` report shows coverage from both default and strict-checks builds merged. |
| **Owner** | Phase 2 or Phase 3 |

---

## R13 — Parameterize Phase 2 integration tests for exponential integrators against the corpus

| Field | Value |
|---|---|
| **ID** | R13 |
| **Priority** | P3 — Low |
| **Dimension** | P1 (Data and parity) |
| **Motivating evidence** | Phase 2 (WP-012) will add exponential and multi-rate integrators. These integrators do not have PRINet 3.0 reference values (they are new implementations), so the parity testing approach must differ from Phase 1's embedded-reference model. The corpus can still be used for convergence and invariant tests. |
| **Recommended action** | For WP-012, design parity tests that validate: (1) convergence order (like RK4's h^4 test), (2) invariant preservation (phase wrapping, amplitude bounds), (3) agreement with RK4 at small dt (since exponential integrators should reduce to standard integrators in the limit). Use the corpus for integration-level smoke tests. |
| **Confirmation evidence** | WP-012 audit (A4 dimension) confirms convergence order and invariant tests pass. |
| **Owner** | WP-012 S1/S2 |

---

## Summary

| ID | Priority | Dimension | One-line description |
|---|---|---|---|
| R7 | P1 | P2, P6 | Strengthen S4 consistency sweep for stale docs |
| R8 | P1 | P1 | Complete exhaustive 504-case Python differential CI |
| R9 | P2 | P9 | Create a Deferred Validation Register |
| R10 | P2 | P3 | Improve kernel coverage reporting |
| R11 | P2 | P7 | Continue secret scanning availability checks |
| R12 | P2 | P3 | Add strict-checks coverage to llvm-cov runs |
| R13 | P3 | P1 | Parameterize Phase 2 integration tests |

No P0 recommendations block Phase 2 from starting. The P1 recommendations
(R7, R8) are process improvements that should be addressed during Phase 2's
first cycle.

# Deferred Validation Register

**Created:** 2026-08-09
**Authority:** Phase 1 Analytics Report recommendation R9; maintained by each
cycle's S3/S4 session.
**Status authority:** The latest approved Project State Report. This register
is a consolidated view; the deviation ledger in each Project State Report is
authoritative for individual finding status.

---

## Purpose

This register consolidates all deferred validation items — work that has been
formally acknowledged (via plan amendment, audit finding disposition, or
analytics recommendation) but whose full validation is assigned to a future
Work Package or phase. It replaces the previous scattering of deferred items
across multiple amendment logs, project state reports, and audit reports.

**Update protocol:** Each cycle's S4 session reviews this register and updates
the status of any item whose re-audit gate has been reached or whose
underlying condition has changed. Items are closed when validated or
superseded.

---

## Active deferred items

| ID | Summary | Origin | Governing amendment | Re-audit gate | Current status |
|---|---|---|---|---|---|
| DV-001 | **Triton 3.0 fused-kernel timing comparison.** Direct same-hardware Triton 3.0 comparison blocked on Windows Python 3.14. PyTorch reference + wgpu/CPU equivalence validated; Triton timing deferred. | WP-004 (WP004-F5) | Plan amendment #11 | Phase 3 / `gpu.yml` (WP-017/018) | OPEN — blocked on Linux GPU runner |
| DV-002 | **wgpu kernel-equivalence CI on headless runner.** `wgpu` feature tests deferred to a headless GPU CI runner; `cpu` feature tests run in default CI. | WP-004 (WP004-F7) | Plan amendment #12 | Phase 3 / `gpu.yml` (WP-017/018) | OPEN — blocked on headless GPU runner |
| DV-003 | **Device-event kernel timing.** `StepReport.wall_time_seconds` uses host wall-clock, not device events. Documented as prototype caveat. | WP-004 (WP004-F8) | — (documented caveat) | Phase 3 (WP-017) | OPEN — Phase 3 inflection point |
| DV-004 | **`cargo-llvm-cov` kernel body coverage gap.** `#[cube(launch)]` kernel bodies are non-instrumentable; reported line coverage (86.36%) understates actual test coverage. Kernel equivalence validates correctness. | WP-004 (WP004-F2) | Plan amendment #10 | Phase 3 (WP-017) — when more kernels are added | OPEN — Phase 1 R10 recommends supplementary metric |
| DV-005 | **CUDA DLPack full validation.** CPU path validated; CUDA DLPack path and `<5%` performance gap deferred. | WP-003 (WP003-F3) | Plan amendment #7 | Phase 4 (GPU compute) | OPEN — blocked on CUDA hardware |
| DV-006 | **DirectML / VitisAI ONNX validation.** ONNX Runtime backends validated; DirectML and VitisAI NPU execution providers not yet tested. | Phase 0 | — (non-goal) | Phase 4+ (platform-specific) | OPEN — blocked on hardware |
| DV-007 | **f64/f32 complex numerical hazard.** PRINet 3.0 uses `torch.complex64` (f32) internally; PRIN uses pure f64. ~1e-8–1e-9 per-step drift in affected paths. Accepted with `1e-6` parity tolerance. | WP-007 (WP007-F3) | Plan amendment #14 | When bit-for-bit f64 reference corpus is regenerated | OPEN — preserved numerical hazard |
| DV-008 | **Inherited `paste` advisory (RUSTSEC-2024-0436).** Transitive dependency from `cubecl` 0.10.0. No upstream fix at PRIN dependency level. | WP-004 (WP004-F1) | Plan amendment #9 | Every cycle (re-check with `cargo audit`) | OPEN — re-check each cycle |
| DV-009 | **GitHub native secret scanning availability.** Unavailable for this private repository. Gitleaks + branch-protection substitute in force. | WP-001 (WP001-F8) | Plan amendment #5 | Every cycle (re-check availability) | OPEN — re-check each cycle |
| DV-010 | **Phase 1/2 pre-release tag (`v0.1.0-alpha.1`/`v0.3.0-alpha.1`).** Amendment #22 (EA-003) has `v0.3.0-alpha.1` retroactively and jointly cover both the Phase 1 and Phase 2 exit-tagging obligations. Actual tag creation/push (triggers a real PyPI/crates.io publish via `release.yml`) is deliberately deferred to an explicit, separate maintainer-confirmed action. | WP-011; amendment #22 (EA-003, 2026-08-14) | Maintainer approval | OPEN — versioning logic resolved; tag push still pending explicit maintainer action |
| DV-011 | **`torch@2.13.0` Snyk Open Source advisories (6: 5 medium, 1 high).** No torch version fixes any of the 6 per Snyk's own database (`fixedIn: []`); confirmed unreachable via repository-wide grep of every vulnerable API. Formally accepted in `.snyk`. | EA-003 (E-F7) | `.snyk` ignore entries, maintainer approval 2026-08-14 | OPEN — recheck 2026-11-14 |
| DV-012 | **`prin-py` sweep/engine PyO3 bindings and `prin-kernels` CPU-reference work.** Original WP-016 declared scope, narrowed out by amendment #20; no successor WP yet assigned. Not a Phase 3 blocker but should land before Phase 7 scientific campaigns use the Python sweep API. | WP-016; amendment #20 | WP-017 declaration (session 0065) or, at latest, the Phase 3 exit-gate PSR (WP-021 S4, session 0084) | OPEN — no WP number assigned yet (Phase 2 analytics R19; re-audit gate narrowed by the Phase 2 recommendation implementation session, 2026-08-15) |
| DV-013 | **`M-F3` policy-gate claims (`INT-01`, `INT-02`, `HOPF-01`, `KUR-01`) permanently `REQUIRES_HUMAN_REVIEW`.** Resolved via recorded sign-off (SciPy + independent Wolfram Engine corroboration) rather than a ledger `PASS`; by policy design, non-formal evidence on critical-severity continuous-math claims cannot close otherwise. | EMA-001R (M-F3) | Documented sign-off; Wolfram Engine corroboration | OPEN by design — not expected to close without a Lean/formal-adapter extension for `ode_property` claims |

---

## Phase 1 analytics recommendations — deferred items

| Rec ID | Summary | Deferred to | Status |
|---|---|---|---|
| R10 | Improve `cargo-llvm-cov` kernel coverage reporting | Phase 3 / WP-017 (sessions 0065+) | OPEN — still deferred; no new kernel code landed in Phase 2 |
| R11 | Continue secret scanning availability checks | Ongoing per-cycle S3/S4 | ONGOING — rechecked every Phase 2 cycle (DV-009 unchanged) |
| R13 | Parameterize exponential integrator tests against corpus | WP-012 S1 (session 0045) | **CLOSED** — WP-012 parity tests include convergence-order and RK4-agreement-at-small-dt checks |

## Phase 2 analytics — deferred and ongoing items

| Rec ID | Summary | Deferred to | Rationale |
|---|---|---|---|
| R17 | Add an automated cumulative-deviation-ledger consistency check | Phase 3, first cycle — WP-017 S4 (session 0068) | Prevents a repeat of EA-003's E-F1 (ledger corruption undetected through 2 audits); assigned to S4 (documentation/tooling session) rather than S1 since it is process tooling, not WP-017's own kernel-architecture deliverable |
| R18 | Explicitly verify Snyk MCP availability at the start of future analytics/EA sessions | Ongoing per-session (standing instruction) | Embedded as normative text in `ANALYTICS_METHODOLOGY.md` §5.1 and `Executive_Audit_Governance_and_Methodology.md` §2 by the Phase 2 recommendation implementation session (2026-08-15); confirmation evidence accrues each future session's evidence table |
| R19 | Assign a WP/phase to the deferred `prin-py`/`prin-kernels` carried scope | Phase 3 planning — WP-017 declaration (session 0065) or, at latest, the Phase 3 exit-gate PSR (WP-021 S4, session 0084) | See DV-012; requires a maintainer-approved plan amendment selecting which Phase 3 WP absorbs the carried scope, not a decision unilaterally made outside WP declaration |
| R20 | Apply EMA-001R's `REQUIRES_HUMAN_REVIEW` resolution pattern consistently in future EMA sessions | Next EMA session (not yet numbered — EMA sessions are declared ad hoc as global sessions) | See DV-013; standing precedent for future `ode_property`/`graph_topology`/`tensor_contract` policy-gate claims |

---

## Closed items

| ID | Summary | Closed (cycle) | Disposition |
|---|---|---|---|
| R8 (Phase 1 analytics) | Complete the exhaustive 504-case Python differential CI | Inter-phase (before WP-012 S1) | `parity/test_parity_differential.py` parametrized over all 504 corpus cases; 510/510 independently re-verified by Phase 2 analytics |
| R9 (Phase 1 analytics) | Create a Deferred Validation Register | Inter-phase (before WP-012 S1) | This document |
| R12 (Phase 1 analytics) | Merge `strict-checks` coverage into `cargo-llvm-cov` runs | Inter-phase (before WP-012 S1) | `AGENTS.md` runs `cargo llvm-cov -p prin-dynamics` under both default and `strict-checks` |
| R13 (Phase 1 analytics) | Parameterize WP-012 tests against the corpus | WP-012 S1 | See table above |
| R14 (Phase 2 analytics) | Fix PA2-F1 (`tools/math_audit_run.py` `ruff check`/`format`) and PA2-F2 (EMA-001 absent from `CHANGELOG.md`) | Inter-phase (Phase 2 recommendation implementation session, before WP-017 S1) | `tools/math_audit_run.py` `ruff check`/`ruff format --check` clean; `CHANGELOG.md` `[Unreleased]` carries an EMA-001/EMA-001R entry |
| R15 (Phase 2 analytics) | Require parity-evidence disposition as an explicit S1 exit-gate item | Inter-phase (Phase 2 recommendation implementation session, before WP-017 S1) | `Development_Workflow_and_Audit_Standards.md` §3 S1 exit criteria amended with the parity-evidence disposition requirement |
| R16 (Phase 2 analytics) | Extend the S4/documentation-accuracy net to cover EA/EMA global sessions | Inter-phase (Phase 2 recommendation implementation session, before next EA/EMA session) | Closing checklist added to `Executive_Audit_Governance_and_Methodology.md` §5 and `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8 |

---

## Review log

| Date | Cycle | Reviewer | Changes |
|---|---|---|---|
| 2026-08-09 | Inter-phase (post-Phase 1) | Qwen Code (AI pair) | Register created; 10 active items (DV-001–DV-010), 3 analytics recommendations deferred |
| 2026-08-15 | Phase 2 analytics | Claude Code (AI pair) | Closed R8/R9/R12/R13; updated DV-010 status per amendment #22; added DV-011 (torch advisories), DV-012 (carried `prin-py`/`prin-kernels` scope), DV-013 (`M-F3` permanent-by-design review items); added Phase 2 analytics items R14–R17 |
| 2026-08-15 | Phase 2 recommendation implementation (inter-phase, before WP-017 S1) | Claude Code (AI pair) | Closed R14/R15/R16 (implemented — see `DOCS/ANALYTICS/phase-2/phase-2-recommendation-implementation-governance.md`); narrowed DV-012's re-audit gate; added Phase 2 deferred/ongoing items R17 (→ WP-017 S4, session 0068), R18 (ongoing standing instruction, now normative), R19 (→ WP-017 declaration or Phase 3 exit-gate PSR), R20 (→ next EMA session) |

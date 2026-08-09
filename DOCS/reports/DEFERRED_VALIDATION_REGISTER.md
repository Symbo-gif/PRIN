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
| DV-010 | **Phase 1 pre-release tag (`v0.2.0-alpha.1`).** Ready pending maintainer approval per Versioning and Release Standards §4. | WP-011 | — | Maintainer approval | OPEN — pending approval |

---

## Phase 1 analytics recommendations — deferred items

| Rec ID | Summary | Deferred to | Rationale |
|---|---|---|---|
| R10 | Improve `cargo-llvm-cov` kernel coverage reporting | Phase 3 / WP-017 (sessions 0053+) | Natural inflection point when new kernels are added; no new kernels in Phase 2 first cycle |
| R11 | Continue secret scanning availability checks | Ongoing per-cycle S3/S4 | Standing process instruction; no artefact to create |
| R13 | Parameterize exponential integrator tests against corpus | WP-012 S1 (session 0045) | Explicitly scoped to WP-012 exponential/multi-rate integrators |

---

## Closed items

| ID | Summary | Closed (cycle) | Disposition |
|---|---|---|---|
| — | *(none yet)* | — | — |

---

## Review log

| Date | Cycle | Reviewer | Changes |
|---|---|---|---|
| 2026-08-09 | Inter-phase (post-Phase 1) | Qwen Code (AI pair) | Register created; 10 active items (DV-001–DV-010), 3 analytics recommendations deferred |

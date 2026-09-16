# Session 0144Y / WP-036G S1 handoff

**Date:** 2026-09-15  
**Session:** 0144Y — WP-036G S1: Deferred-Validation register consolidation and permanent dispositions  
**Status:** S1 delivered and committed locally. Handoff to mandatory read-only S2 audit `0144Z`; S1 does not self-certify.  
**Predecessor:** WP-036F S4 `0144X`, re-affirmed after ETCA-002 over green SHA `9d4fd86`.  
**Successor:** `0144Z`.

## 1. Session-start and security prerequisite

The required brief, Project Plan, Development Workflow §3/§7, Coding Standards
§6, Testing Standards §1, PSR-036F (including its ETCA-002 addendum), the full
Deferred Validation Register, EMA-005/EMA-006 sign-off evidence, EA-006 E-F2,
Phase 5 analytics R34–R36, the DV-019 handoff, and the amendment-#38 execution
plan were reviewed before repository edits.

The first advisory refresh found a new actionable medium vulnerability,
RUSTSEC-2026-0285, in locked `rustls` 0.23.43. Work paused because the S1 entry
condition forbids unresolved D1/D2 security findings. The lock was advanced to
fixed `rustls` 0.23.45 / `rustls-webpki` 0.103.15; native and Snyk dependency
rescans are clean at their governed thresholds. This changes no API or
numerics.

## 2. Delivered scope

| Acceptance item | S1 result |
|---|---|
| Permanent dispositions: DV-007, DV-013, DV-018, DV-028 | Dated drafts added directly to the register and consolidated in one matrix. Each names its standing mechanism and no further WP-level gate. Maintainer signature remains correctly reserved for S4. |
| Standing external/third-party dispositions | Consolidated evidence and explicit “not repository-closeable / not a Phase 7 entry blocker” text added. Linux-runner, runner-status, secret-scanning, `.snyk`, Cargo, pip, and Snyk checks are recorded in `EVIDENCE/0144Y-wp036g-s1-dv-reverification/reverification.md`. |
| `chacha20` visibility | New DV-035 row: threat assessment, compensating controls, native-audit evidence, upstream recheck trigger, and Phase 7 disposition. |
| DV-001 workflow | New dormant `.github/workflows/gpu-triton.yml`, `workflow_dispatch` only, `runs-on: [self-hosted, linux, gpu]`, with PRIN CUDA and archived PRINet 3.0 Triton benchmark steps. |
| DV-010 / DV-027 routing | DV-010 is explicitly owned by WP-038 S1 (`0149`); no tag was created or pushed. DV-027 records the EMA-006 routing outcome and remains cosmetic external-tool housekeeping. |
| DV-019 Python sub-item | Shared-root hypothesis ruled out: PyTorch does not use Burn's process-global `AutodiffServer`. ETCA-001 found the distinct unseeded global-Torch-RNG/order root and installed an autouse `torch.manual_seed(0)` guard. The named gradcheck passed 10/10 separate invocations; no new DV item is needed. |
| `test_no_gpu_throughput_regression` | Quarantine removed. The unchanged `<1.30` assertion now compares seven daemon-active samples with seven bracketing control samples, each using fixed 1,000,000-iteration work after warm-up. Three isolated runs plus fast and full suites passed. |
| Phase 7 entry draft | §4 enumerates each non-terminal item individually. |
| Register / architecture invariants | DV gate passes for 35 rows; no Python numerics; `verify_api_surface(prin.__all__) == (set(), set())`; no `FROZEN_PUBLIC_API` change. |

## 3. Files changed

- `Cargo.lock` — security-only `rustls` / `rustls-webpki` resolved update.
- `.github/workflows/gpu-triton.yml` and workflow README — dormant DV-001 path.
- `tests/test_acceptance_subconscious.py`, `tests/conftest.py` — hardened and
  re-enabled the throughput regression.
- `tests/test_wp001_baseline.py` — expected workflow inventory 8 → 9.
- Deferred Validation Register, session/register indexes, tests README,
  CHANGELOG, evidence index, this handoff, and the `0144Y` brief.

## 4. Draft Phase 7 entry statement

Every non-terminal row below has a dated disposition and does **not** block
campaign pre-registration (`0153` E0) or campaign execution:

- **DV-001:** Linux Triton comparison remains hardware-runner-gated; dormant workflow is ready.
- **DV-003:** CubeCL CUDA device-event API residual has amendment #44's upstream release trigger.
- **DV-006 (VitisAI half):** absent NPU/provider hardware remains explicitly hardware-gated.
- **DV-007:** accepted PRINet f32-reference hazard remains bounded by registered tolerances and the Parity Report.
- **DV-008:** transitive unmaintained `paste` warning has no PRIN-level fix; native audit remains active.
- **DV-009:** GitHub native secret scanning remains unavailable; amendment #5 controls remain active.
- **DV-010:** WP-038 S1 owns the release tag action.
- **DV-011:** six no-fix torch advisories retain current threat assessments through 2026-11-14.
- **DV-013:** by-design human-review status is governed by fresh sign-off whenever the EMA claim set changes.
- **DV-016:** hosted-Windows slowdown is avoided by the service-backed self-hosted leg and bounded timeout.
- **DV-017:** transitive unmaintained `bincode` warning retains amendment #27 controls.
- **DV-018:** pinned Burn f32 sigmoid floor is controlled at each call site and rechecked only on a Burn bump.
- **DV-022:** hosted-runner disk capacity is mitigated by disk reclaim and CPU-only torch installation.
- **DV-024:** runner availability is service-backed; the remaining single-machine risk is represented by DV-034.
- **DV-027:** stale external-tool editable metadata is cosmetic and has no evidence/runtime effect.
- **DV-028:** R36's no-vendoring decision is final absent a CI-reachable published remote.
- **DV-030:** input-direction zero-copy awaits a CubeCL external-memory API or governed storage shim.
- **DV-031:** deliverables have WP-037/WP-038 owners; CUDA residuals follow DV-030's trigger.
- **DV-032:** one named test is hardened and active; two unrelated benchmark-class checks retain explicit limits and nightly/CI authority.
- **DV-033:** CI codecov remains authoritative for per-change coverage where the maintainer-host tool is unavailable.
- **DV-034:** second-runner redundancy is external infrastructure; required GPU checks remain enforced.
- **DV-035:** yanked `chacha20` remains visible and rechecked until upstream resolution changes.

DV-005 is separately `AMENDED` by amendment #38. All other rows are `CLOSED`.

## 5. Verification

| Gate | Result |
|---|---|
| Targeted fragility checks | DV-019 gradcheck 10/10; hardened throughput test 3/3 isolated |
| Python fast suite | 2775 passed, 201 skipped, 30 deselected; 95% coverage |
| Python full suite + parity | 3395 passed, 203 skipped; 95% coverage with governed `.pytest_basetemp` |
| Rust | fmt, clippy `-D warnings`, workspace tests, rustdoc all passed |
| Python quality | Ruff check/format, mypy strict (62 files), interrogate (97.6%), Bandit all passed |
| Security | `cargo audit` exit 0 with three governed warning rows; both `pip-audit` scopes clean; Snyk Open Source 0; Snyk Code 0 on all modified supported Python files |
| Governance | DV gate passed (35 rows / 198 sessions); no-Python-numerics clean; WP-001 baseline passed; API delta empty |

Snyk Code reported `SNYK-CODE-0006` for the YAML workflow because that single
file type is unsupported; no passing claim is made for it. The workflow parsed
as YAML. Full command evidence and the transparent `.pytest_basetemp-full`
path-policy observation are in the evidence bundle.

## 6. S2 audit focus / out-of-scope discovery

1. Confirm every register row maps unambiguously to one terminal/disposition
   class and that S4 maintainer-signature wording is not prematurely claimed.
2. Independently review DV-035's threat assessment and the dormant workflow.
3. Review the throughput methodology under contention without weakening 1.30.
4. Classify the pre-existing AGENTS.md `.pytest_basetemp-full` mismatch: that
   spelling is rejected by `allowed_output_roots()`, causing 11 figure/table
   path-policy failures, while the identical 3,598-test run with the governed
   `.pytest_basetemp` passes. No production path policy was widened in S1.

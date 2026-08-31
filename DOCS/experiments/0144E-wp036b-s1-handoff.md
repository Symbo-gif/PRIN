# Session 0144E / WP-036B S1 running handoff

**Date:** 2026-08-31 (session start and decomposition)  
**Status:** S1 **IN PROGRESS**. Plan amendment #35 (MichaelMaillet,
2026-08-31) inserts six sequential coding sub-passes `0144E1`–`0144E6`, all
feeding the single mandatory S2 audit `0144F`. Sub-pass `0144E1` is complete at
its green local gate; `0144E2` is next. S1 does not self-certify.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report (`DOCS/reports/036a-project-state.md`), its
cumulative deviation ledger, the 0144E brief, Project Plan §6/§8 (amendments
#31–#34), Development Workflow and Audit Standards §3/§7, Testing Standards
§1.1, the WP-036/WP-036A handoffs, and the governing WP-036A audit.

**Session ID/type:** 0144E — WP-036B S1 (Coding), stopped for governed
decomposition before implementation.  
**Planned output:** strict import-only port of the 13 assigned PRINet 3.0
reference files, with unchanged assertions; missing compatibility behavior
rebuilt through Rust-backed layers; complete handoff to `0144F`.

## Start-of-session discrepancy

The prospective 0144E brief says the assigned 13-file cluster contains
approximately 805 `def test_` functions. Direct source inventory found **498
functions across 8,570 lines**. An initial collect-only attempt reached **481
collected tests**, then stopped on an import error in `test_clevr_n.py` because
`benchmarks.clevr_n` is missing.

Neither number authorizes scope reduction. The 498 source functions are the
accounting contract; the 481 + import error result records the initial
collection state and the explicit CLEVR-N compatibility blocker.

## Exact reference-file inventory

Reference root:
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/`.

| Reference file | `def test_` | Lines | Sub-pass |
|---|---:|---:|---|
| `test_core.py` | 106 | 1,125 | `0144E1` |
| `test_utils.py` | 19 | 237 | `0144E1` |
| `test_phases.py` | 30 | 389 | `0144E2` |
| `test_hierarchical.py` | 43 | 604 | `0144E2` |
| `test_phase_to_rate.py` | 22 | 343 | `0144E2` |
| `test_q2.py` | 67 | 915 | `0144E3` |
| `test_q2_remaining.py` | 51 | 807 | `0144E3` |
| `test_q3_new.py` | 31 | 389 | `0144E4` |
| `test_nn.py` | 30 | 712 | `0144E4` |
| `test_scalr_enhanced.py` | 14 | 649 | `0144E4` |
| `test_hybrid.py` | 19 | 907 | `0144E5` |
| `test_clevr_n.py` | 17 | 403 | `0144E5` |
| `test_subconscious.py` | 49 | 1,090 | `0144E6` |
| **Total** | **498** | **8,570** | — |

## Approved split — amendment #35

Maintainer selected **Decompose strict port**:

| Sub-pass | Scope | Functions | Lines |
|---|---|---:|---:|
| `0144E1` | core + utils | 125 | 1,362 |
| `0144E2` | phases + hierarchical + phase-to-rate | 95 | 1,336 |
| `0144E3` | q2 + q2_remaining | 118 | 1,722 |
| `0144E4` | q3_new + nn + scalr_enhanced | 75 | 1,750 |
| `0144E5` | hybrid + clevr_n | 36 | 1,310 |
| `0144E6` | subconscious + consolidation | 49 | 1,090 |
| **Total** | **13 files** | **498** | **8,570** |

The adopted execution plan is
`DOCS/sessions/phase-6/WP-036B-S1-execution-plan-and-decomposition.md`.
Planned session count changes **220 → 226**; the chain is `0144E` →
`0144E1` → … → `0144E6` → `0144F`.

## Strategic strict-port disposition

- Testing Standards §1.1 remains literal: copy the reference tests, adapt
  imports only, and leave assertions/expected values/parametrization/semantics
  unchanged.
- Missing behavior is repaired in the product through Rust-backed owners and
  thin PyO3/Python delegation. Numerical compatibility logic does not move into
  Python or the copied tests.
- The missing `benchmarks.clevr_n` path is an implementation compatibility gap
  owned by `0144E5`; it is not bypassed in `test_clevr_n.py`.
- The already-public standalone `DiscreteDeltaThetaGamma` binding remains a
  binding completion, first owned where the strict hierarchical tests require
  it; no public-symbol expansion is implied.
- Existing hazard tolerances require amendment attribution plus a per-test
  annotation and Parity Report entry. GPU/Triton availability guards follow
  the existing reference precedent. No assertion deletion, weakening, or
  unapproved skip is permitted.
- Each sub-pass commits at its own green local gate; the aggregate contiguous
  range is audited read-only by `0144F`. S1 does not self-certify.

## Governance mechanics recorded

- Project Plan §8.3 amendment #35.
- Six new briefs `0144E1`–`0144E6` and adopted execution plan.
- Parent/successor links, Master Session Register, session indexes,
  TRACEABILITY, and baseline-validator metadata updated for 226 sessions.
- No source, acceptance test, Parity Report, changelog, PSR, audit, dependency,
  or release artefact changed; no commit or push performed.

## Next step

Execute **`0144E1` — core + utils**. Account for 125 source functions / 1,362
reference lines, preserve import-only/assertions-unchanged, rebuild any missing
compatibility behavior through Rust-backed layers, and append exact collection,
execution, diff, coverage, security, and discovery evidence below before the
sub-pass commits locally.

## Sub-pass evidence log

### 0144E1 — core + utils

**Complete 2026-08-31; committed locally with amendment #35; not pushed.**

#### Strict-port accounting and semantic proof

| Reference | Stable port | Source lines | `def test_` | Collected / passed | Tolerance annotations | Skips / guards | Discoveries |
|---|---|---:|---:|---:|---:|---:|---|
| `test_core.py` | `tests/test_acceptance_core.py` | 1,125 | 106 | 106 / 106 | 0 | 0 | Rust-backed Torch compatibility facade required |
| `test_utils.py` | `tests/test_acceptance_utils.py` | 237 | 19 | 19 / 19 | 0 | 0 | Solver/state marshalling required |
| **E1 total** | **2 files** | **1,362** | **125** | **125 / 125** | **0** | **0** | — |

`git diff --no-index --unified=0` against each archived reference reports
exactly six changed lines, all import-module paths: three
`prinet.core.{decomposition,measurement,propagation}` paths in `test_core.py`
and three `prinet.core.{measurement,propagation}` / `prinet.utils.cuda_kernels`
paths in `test_utils.py`, each redirected to the internal
`prin._torch_compat` facade. Source and port line/function inventories are
identical (`1,125/106` and `237/19`). No assertion, value, parameter, call
order, body, tolerance, marker, or semantic line changed.

#### Changed-owner mapping

| Compatibility behavior | Numerical owner | PyO3 / Python exposure |
|---|---|---|
| finite clamp/repair and wrapped phase differences | `crates/prin-dynamics/src/state.rs` | DLPack-only functions in `crates/prin-py/src/bindings/state.rs`; tensor marshalling in `python/prin/_torch_compat.py` |
| Torch autograd for oscillator derivative calls | `crates/prin-dynamics/src/models.rs::dynamics_vjp` | model `dynamics_vjp` methods in `crates/prin-py/src/bindings/models.rs`; `torch.autograd.Function` orchestration only in the internal facade |
| Tucker relative reconstruction error and mode-n unfolding | existing `prin-tensor` reconstruction / `utils::{frobenius_norm,mode_unfold}` | methods in `crates/prin-py/src/bindings/tensor.rs`; thin methods and compatibility exceptions/base in `python/prin/tensor.py` |
| batched Torch state/model/metric/solver API shape | existing `prin-dynamics`, `prin-metrics`, `prin-sim`, and `prin-tensor` owners | internal `python/prin/_torch_compat.py` row marshalling/delegation; no new top-level `prin` export (`verify_api_surface(prin.__all__) == (set(), set())`) |

Same-pass focused coverage consists of two new Rust unit tests for finite
clamping plus three `dynamics_vjp` regression tests (value, unclamped VJP, and
all gradient-length guards), the 125 acceptance tests themselves, and six
focused Python regressions in `tests/test_e1_compat_regressions.py`. The focused
Python coverage run (coverage started after importing Torch to avoid the host's
Python 3.14/Torch coverage-import crash) passed **131 tests** and measured
`prin._torch_compat` + `prin.tensor` at **98% (375/384 statements)**. Native
`cargo llvm-cov -p prin-dynamics --lib` passed all 278 unit tests and reported
87.96% whole-crate line coverage; the lower whole-crate number includes old
untouched branches and is not a changed-code regression. The new owner paths
are directly exercised by the added Rust tests and acceptance calls.

#### Command evidence

- `pytest ... --collect-only -q --basetemp=.pytest_basetemp`: **125 collected**.
- Acceptance-only pytest: **125 passed**; acceptance + focused regressions:
  **131 passed**; acceptance + changed Python-owner suites
  (`test_dynamics_bindings.py`, `test_tensor_bindings.py`,
  `test_solver_surface.py`) + focused regressions: **243 passed**.
- Full fast Python gate: **1,397 passed, 9 deselected**, 99% package coverage;
  `_torch_compat.py` 99% and `tensor.py` 100%.
- `cargo test --workspace`: **1,541 passed, 0 failed, 1 ignored**; the focused
  touched-crate run includes 342 dynamics, 59 tensor, and 10 PyO3 tests.
- `cargo fmt --all -- --check`; workspace `cargo clippy --all-targets --
  -D warnings`; `ruff check`; `ruff format --check`; and `mypy --strict`: clean.
- `interrogate`: **97.2%**, pass; `tools/check_no_python_numerics.py`: clean
  for its governed 17-module scope; `bandit -r .`: 0 issues.
- `cargo audit`: exit 0 with only the three pre-existing governed warnings
  (`bincode` RUSTSEC-2025-0141, `paste` RUSTSEC-2024-0436, yanked
  `chacha20`); touched-crate rustdoc under `RUSTDOCFLAGS=-D warnings`: exit 0.
- No dependency declaration changed (the `pyproject.toml` delta is lint-only),
  so Snyk Open Source was not applicable. Snyk Code at severity **low** reported
  **0 issues** across `python/prin`, `crates/prin-dynamics/src`,
  `crates/prin-py/src/bindings`, `crates/prin-tensor/src`, and `tests`.

Independent review found and this pass corrected two edge defects before the
local gate: batched adaptive trajectories now use the common available history
length rather than indexing every row to the maximum accepted-step count, and
`dynamics_vjp` returns state gradients without incorrectly applying the
`±1e4` time-derivative clamp. Both have focused regression coverage. Legacy
adaptive-control constructor fields not exercised by the E1 reference remain
stored for strict introspection; full custom-control/compiled behavior first
appears in and is owned by the E3 `test_q2_remaining.py` port.

Three direct pytest-cov attempts crashed while importing Torch under this
host's Python 3.14 coverage instrumentation. Starting coverage after the Torch
import produced the green 98% focused result above. Windows incremental-cache
finalization also emitted intermittent WinError 32 warnings while commands
still exited 0; isolated reruns were green per EA-002 E-F13.

**Parity-evidence disposition:** directly comparable PRINet 3.0 behavior exists
and is the literal 125-test acceptance source used here. The imports-only diff
plus all-green execution is the parity evidence. No new hazard tolerance or
backend guard was required, so `DOCS/sphinx/parity_report.rst` is unchanged.

### 0144E2 — phases + hierarchical + phase-to-rate

*Pending execution.*

### 0144E3 — q2 + q2_remaining

*Pending execution.*

### 0144E4 — q3_new + nn + scalr_enhanced

*Pending execution.*

### 0144E5 — hybrid + clevr_n

*Pending execution.*

### 0144E6 — subconscious + consolidation

*Pending execution.*

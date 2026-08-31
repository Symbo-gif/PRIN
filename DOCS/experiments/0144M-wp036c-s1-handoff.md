# Session 0144M / WP-036C S1 running handoff

**Date:** 2026-08-31 (session start and decomposition)
**Status:** S1 **decomposed, not yet executed.** Plan amendment #39
(MichaelMaillet, 2026-08-31) inserts eight sequential strict-port coding
sub-passes `0144M1`–`0144M8`, all feeding the single mandatory S2 audit
`0144N`. No sub-pass has run; no `tests/test_acceptance_*` file for the
WP-036C cluster is committed yet.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report (`DOCS/reports/036d-project-state.md`), its
cumulative deviation ledger, the `0144M` brief, Project Plan §6/§8 (amendments
#31/#33/#36/#38), Development Workflow and Audit Standards §3/§7, Testing
Standards §1.1, the WP-036/WP-036A/WP-036B/WP-036D handoffs, and the governing
WP-036D audit + its CLEAN closure table.

**Session ID/type:** 0144M — WP-036C S1 (Coding), stopped for governed
decomposition before implementation.
**Planned output:** strict import-only port of the 24 assigned PRINet 3.0
reference files, with unchanged assertions; missing compatibility behavior
rebuilt through Rust-backed layers; DV-025 `retrain_controller` resolved;
complete handoff to `0144N`.

## Start-of-session discrepancy

The prospective `0144M` brief says the assigned cluster is "~790 `def test_`
functions". Direct source inventory found **1,097 `def test_` functions across
~15,810 lines in 24 reference files**. `pytest --collect-only` over the 24
files reached **1,172 collected, 0 errors** against the editable `prinet`
reference install.

Neither number authorizes scope reduction. The 1,097 source functions are the
accounting contract; the 1,172 collected records the parametrization-expanded
collection state.

Brief-vs-repository naming note: `test_y3q5`–`test_y3q44` / `test_y3q46`–
`test_y3q48` (implied by the brief's "`test_y3q1`–`test_y3q49`" shorthand) do
not exist — the y3 cluster is `y3q1/2/3/4/45/49` (6 files). `test_y4q1*` is
8 files (`y4q1`, `y4q1_2/3/4/5/7/8/9`), not the brief's "7 files".

## Exact reference-file inventory

Reference root:
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/`.

| Reference file | `def test_` | Lines | Sub-pass |
|---|---:|---:|---|
| `test_integration_q3.py` | 19 | 496 | `0144M1` |
| `test_y2q1.py` | 48 | 926 | `0144M1` |
| `test_y2q4.py` | 26 | 417 | `0144M1` |
| `test_y2q2.py` | 30 | 706 | `0144M2` |
| `test_y2q3.py` | 35 | 917 | `0144M2` |
| `test_y3q1.py` | 40 | 665 | `0144M3` |
| `test_y3q2.py` | 38 | 687 | `0144M3` |
| `test_y3q3.py` | 32 | 676 | `0144M4` |
| `test_y3q4.py` | 32 | 417 | `0144M4` |
| `test_y3q45.py` | 23 | 370 | `0144M4` |
| `test_y3q49.py` | 30 | 632 | `0144M4` |
| `test_y4q1.py` | 49 | 466 | `0144M5` |
| `test_y4q1_2.py` | 73 | 801 | `0144M5` |
| `test_y4q1_3.py` | 49 | 610 | `0144M5` |
| `test_y4q1_4.py` | 52 | 623 | `0144M6` |
| `test_y4q1_5.py` | 60 | 694 | `0144M6` |
| `test_y4q1_9.py` | 46 | 703 | `0144M6` |
| `test_y4q1_7.py` | 79 | 840 | `0144M7` |
| `test_y4q1_8.py` | 115 | 1,071 | `0144M7` |
| `test_y4q2.py` | 67 | 703 | `0144M8` |
| `test_y4q3.py` | 30 | 475 | `0144M8` |
| `test_y4q4.py` | 44 | 442 | `0144M8` |
| `test_triton_kernels.py` | 40 | 874 | `0144M8` |
| `test_gpu.py` | 40 | 599 | `0144M8` |
| **Total** | **1,097** | **~15,810** | — |

## First-file compatibility probe (`0144M1`, `test_integration_q3`)

Copied to `tests/test_acceptance_integration_q3.py` with imports adapted
(`from prinet import (...)` → `from prin._torch_compat import (...)` for
`DeltaThetaGammaNetwork` / `OscillatorState` / `PhaseAmplitudeCoupling` /
`phase_to_rate`; `from prin.nn import (...)` for `HierarchicalResonanceLayer` /
`PhaseToRateConverter` / `SparsityRegularizationLoss`). Result: **11 passed,
8 failed** — all failures are genuine missing compatibility behavior, not
assertion drift:

- `DeltaThetaGammaNetwork` (`prin._torch_compat`) has no `.integrate()`,
  `.create_initial_state()`, or `.order_parameters()` — the WP-036A/E1 compat
  shape differs from the reference's stateful integrate API.
- `PhaseToRateConverter` (`prin.nn`) has no learnable `.temperature`
  `nn.Parameter`.

These are the `0144M1` compatibility-gap workload: close them in the owning
Rust crate + thin PyO3/Python delegation, no Python numerics, no test edits.
The probe file was **removed** — it is not committed; `0144M1` re-creates it.

## Decomposition (amendment #39)

| Sub-pass | Files | `def test_` | Lines |
|---|---|---:|---:|
| `0144M1` | integration_q3 + y2q1 + y2q4 | 93 | 1,839 |
| `0144M2` | y2q2 + y2q3 (DV-025 `retrain_controller`) | 65 | 1,623 |
| `0144M3` | y3q1 + y3q2 | 78 | 1,352 |
| `0144M4` | y3q3 + y3q4 + y3q45 + y3q49 | 117 | 2,095 |
| `0144M5` | y4q1 + y4q1_2 + y4q1_3 | 171 | 1,877 |
| `0144M6` | y4q1_4 + y4q1_5 + y4q1_9 | 158 | 2,020 |
| `0144M7` | y4q1_7 + y4q1_8 | 194 | 1,911 |
| `0144M8` | y4q2 + y4q3 + y4q4 + triton_kernels + gpu + consolidation | 221 | 3,093 |

Governance: Testing Standards §1.1 literal (imports only); compatibility gaps
rebuilt through Rust-backed layers; hazard-tolerance governance
(amendments #14/#16/#17/#25) unchanged; GPU/Triton stay `skipif`-guarded and
reuse WP-036D's `_torch_compat.py` device dispatch; DV-025 `retrain_controller`
in `0144M2`, `quantize_onnx` only if a ported assertion exercises it. Each
sub-pass commits at its own green local gate; the contiguous
`0144M`+`0144M1`–`0144M8` range feeds `0144N` and is pushed once with it
(amendment #28).

## Per-sub-pass log

_(appended as each sub-pass executes)_

### 0144M1 — not started
### 0144M2 — not started
### 0144M3 — not started
### 0144M4 — not started
### 0144M5 — not started
### 0144M6 — not started
### 0144M7 — not started
### 0144M8 — not started

# WP-036C S1 (session 0144M) — execution plan and decomposition

**Status:** ADOPTED (2026-08-31, MichaelMaillet). Recorded as **Plan
amendment #39**. Maintainer selected **Decompose strict port** (eight sequential
S1 coding sub-passes `0144M1`–`0144M8` feeding the single S2 audit `0144N`) and,
for DV-025, **resolve `quantize_onnx` only if a ported assertion exercises it**
(else documented stub + Migration-Guide row, S2 veto). Not itself an execution
contract; the governing contracts are the 0144M brief, amendments
#31/#33/#36/#38/#39, and the sub-pass briefs `0144M1`–`0144M8`.

**Prepared for:** session 0144M (WP-036C S1 — acceptance-suite port: integration,
y-series, kernels; DV-025).
**Author:** AI pair.
**Date:** 2026-08-31.
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36/#38; Development
Workflow and Audit Standards §7 ("An S1 session that grows beyond its WP
declaration must stop and either split the WP (new declaration) or descope");
Testing Standards §1.1.

---

## 1. Why this document exists

The prospective 0144M brief estimates the assigned PRINet 3.0 reference files at
"~790 `def test_` functions". Repository verification at session start
establishes a materially larger contract, exactly as happened at WP-036B S1
(amendment #35, 805 → 498 corrected upward in effort terms once the Rust-backed
compatibility work was counted):

- **1,097 `def test_` functions across ~15,810 lines in 24 reference files.**
- **`pytest --collect-only` over the 24 files: 1,172 tests collected** (after
  parametrization), 0 collection errors against the editable `prinet` reference
  install.

This is ~1.85× the WP-036B strict-port range (8,570 lines / 6 sub-passes). A
single S1 commit range covering the strict port **plus** DV-025's
`retrain_controller` resolution (thin `prin` wrapper over the Rust owner + unit
+ parity tests + `tools/wp001_ownership.json` / traceability regeneration)
**plus** the compatibility work that collection/execution will expose in the
y-series support modules is not reviewable. Continuing in one pass forces scope
creep (D3 under Development Workflow §7), deferred tests, or semantic edits to
the acceptance suite — all prohibited by the 0144M brief and Testing Standards
§1.1. The approved response is to decompose the strict port, not relax it.

## 2. Verified scope inventory

Reference root:
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/`.

| Reference file | `def test_` | Lines | Dominant non-stdlib imports | Proposed sub-pass |
|---|---:|---:|---|---|
| `test_integration_q3.py` | 19 | 496 | top-level `prinet` | `0144M1` |
| `test_y2q1.py` | 48 | 926 | `prinet`, `prinet.nn.layers` (`DiscreteDeltaThetaGammaLayer`, `OscillatoryAttention`), `prinet.nn.training_hooks`, `clevr_n` | `0144M1` |
| `test_y2q4.py` | 26 | 417 | `prinet._deprecation`, `prinet.nn.hybrid`, `y2q4_benchmarks` | `0144M1` |
| `test_y2q2.py` | 30 | 706 | `benchmarks.clevr_n`, `benchmarks.y2q1/y2q2_benchmarks`, `prinet.nn.subconscious_model.retrain_controller`, `prinet.nn.training_hooks.ActiveControlTrainer` | `0144M2` |
| `test_y2q3.py` | 35 | 917 | `prinet.nn.subconscious_model` (`SubconsciousController`, retrain/quantize), `prinet.utils.triton_kernels.pytorch_fused_discrete_step`, `prinet.nn.hybrid` | `0144M2` |
| `test_y3q1.py` | 40 | 665 | `prinet.core.propagation` (inhibition/DTG/`phase_to_rate`/`sweep_coupling_params`), `prinet.core.subconscious_daemon`, `prinet.utils.profiler`, `hypothesis` | `0144M3` |
| `test_y3q2.py` | 38 | 687 | `prinet.nn.adaptive_allocation`, `prinet.nn.mot_evaluation`, `hypothesis`, `motmetrics`, `scipy.stats` | `0144M3` |
| `test_y3q3.py` | 32 | 676 | `prinet.utils.fused_kernels` (`AsyncCPUGPUPipeline`, `LargeScaleOscillatorSystem`, `MixedPrecisionTrainer`, `OscillatorPruner`, …) | `0144M4` |
| `test_y3q4.py` | 32 | 417 | `prinet.utils.oscillosim` (`OscilloSim`, `SimulationResult`, `quick_simulate`), `prinet.nn.slot_attention` | `0144M4` |
| `test_y3q45.py` | 23 | 370 | `prinet.utils.fused_kernels` (MSVC helpers), `prinet.utils.oscillosim`, `prinet.core.subconscious` | `0144M4` |
| `test_y3q49.py` | 30 | 632 | `prinet.utils.oscillosim`, `prinet.core.measurement`, `prinet.core.propagation` | `0144M4` |
| `test_y4q1.py` | 49 | 466 | `prinet.utils.y4q1_tools`, `prinet.utils.oscillosim`, `prinet.nn.slot_attention.TemporalSlotAttentionMOT` | `0144M5` |
| `test_y4q1_2.py` | 73 | 801 | `prinet.utils.y4q1_tools`, `prinet.utils.oscillosim`, `hypothesis` | `0144M5` |
| `test_y4q1_3.py` | 49 | 610 | `prinet.utils.y4q1_tools`, `prinet.utils.oscillosim` | `0144M5` |
| `test_y4q1_4.py` | 52 | 623 | `prinet.utils.y4q1_tools`, `prinet.nn.hybrid.PhaseTracker`, `hypothesis` | `0144M6` |
| `test_y4q1_5.py` | 60 | 694 | `prinet.utils.y4q1_tools`, `benchmarks.y4q1_5_benchmarks`, `hypothesis`, `tomllib` | `0144M6` |
| `test_y4q1_9.py` | 46 | 703 | `prinet.nn.ablation_variants.create_ablation_tracker`, `prinet.utils.temporal_training`, `scipy.stats` | `0144M6` |
| `test_y4q1_7.py` | 79 | 840 | `prinet.nn.ablation_variants`, `prinet.utils.temporal_metrics`, `prinet.utils.temporal_training` | `0144M7` |
| `test_y4q1_8.py` | 115 | 1,071 | `prinet.utils.adversarial_tools`, `prinet.utils.temporal_training.TemporalTrainer`, `prinet.utils.oscillosim`, `prinet.utils.y4q1_tools` | `0144M7` |
| `test_y4q2.py` | 67 | 703 | `prinet.utils.figure_generation`, `prinet.utils.table_generation`, `matplotlib` | `0144M8` |
| `test_y4q3.py` | 30 | 475 | `prinet.utils.fused_kernels`, `tomllib`, `subprocess` | `0144M8` |
| `test_y4q4.py` | 44 | 442 | top-level `prinet`, `subprocess`, `hashlib` | `0144M8` |
| `test_triton_kernels.py` | 40 | 874 | `prinet.utils.triton_kernels` (`triton_available`) | `0144M8` |
| `test_gpu.py` | 40 | 599 | `prinet.core.decomposition` (`CPDecomposition`, `PolyadicTensor`), `prinet.nn.layers.PRINetModel`, `prinet.nn.optimizers`, `prinet.utils.cuda_kernels` | `0144M8` |
| **Total** | **1,097** | **~15,810** | — | — |

Collect-only cross-check: **1,172 tests collected, 0 errors.** The 1,097 source
functions are the accounting contract; every one is assigned. Files
`test_y3q5`–`test_y3q44` / `test_y3q46`–`test_y3q48` named in the brief's
"`test_y3q1`–`test_y3q49`" shorthand **do not exist** in the reference tree —
the y3 cluster is the six files above (`y3q1/2/3/4/45/49`); likewise
`test_y4q1*` is the eight `y4q1*` files above (brief says "7 files"). Recorded
as a brief-vs-repository discrepancy, not a scope change.

### 2.1 Compatibility-surface status (repository-verified)

Most of the net-new Python surface the y-series imports need already exists from
WP-036 S1 sub-passes `0141D1`/`0141D2`: `python/prin/simulation.py` (OscilloSim
family), `python/prin/y4q1_tools.py`, `python/prin/temporal_training.py`,
`python/prin/topology.py`, `python/prin/solvers.py`, and `benchmarks/`
(`clevr_n.py`, `mot/`, `ablations/`, `adversarial/`, `kernels/`, `integrators/`,
`training/`). The strict port's compatibility work is therefore expected to be
**behavioral gap-closure and import-path adaptation**, not large new-surface
construction — but the exact gap set is only knowable per sub-pass as each file
is collected and run. Modules whose PRIN status must be confirmed at sub-pass
start: `prinet.nn.adaptive_allocation`, `prinet.nn.mot_evaluation`,
`prinet.utils.fused_kernels`, `prinet.nn.ablation_variants`,
`prinet.utils.temporal_metrics`, `prinet.utils.adversarial_tools`,
`prinet.utils.figure_generation`, `prinet.utils.table_generation`,
`prinet.utils.profiler`.

### 2.2 GPU / Triton reference tests

`test_gpu.py` (40) and `test_triton_kernels.py` (40) plus scattered
`skipif`-guarded cases in the y-series (`y2q2`×1, `y2q3`×5, `y3q1`×1, `y3q2`×5,
`y3q3`×3, `y3q4`×3, `y3q45`×6, `y3q49`×7, `y4q3`×4, `triton`×5, `gpu`×2 by
raw marker grep) stay `skipif`-guarded on backend availability per the 0144M
brief non-goals, the reference files' own markers, and amendment #36's WP-036D
coordination note: *"When porting `test_gpu.py` here, reuse whatever
device-dispatch surface WP-036D established in `_torch_compat.py`; do not
re-derive a parallel path."* `test_triton_kernels.py` has no CPU analogue and
needs the Linux GPU runner tracked by DV-001. No GPU-runner execution of the
skipped tests is in WP-036C scope.

### 2.3 DV-025

DV-025 names `SubconsciousController.export_to_onnx` (delivered real in
`0144E6`), `.quantize_onnx`, and `retrain_controller`. In-scope reference files
`test_y2q2.py` and `test_y2q3.py` import `retrain_controller` (and `y2q3`
references the ONNX export/quantize surface). 0144M brief expected-work item 3:
implement `retrain_controller` "(supervised retraining from telemetry) as a
thin `prin` wrapper over the Rust owner; unit + parity tests in tandem; update
`tools/wp001_ownership.json` / regenerate the traceability baseline." Assigned
to sub-pass **`0144M2`** (the pass that ports both files that exercise it). A
DV-025 symbol not exercised by any in-scope reference test keeps its documented
`0141`-era stub + Migration-Guide row (S2 veto), consistent with
[[wp036-s1-deferred-symbols]] and the 0144E6 boundary decision.

## 3. Proposed strategic disposition — Decompose strict port

Identical governance to amendment #35 (WP-036B):

1. **Strict test text.** Each reference test is copied under a stable
   `tests/test_acceptance_*.py` name. Semantic-body changes are prohibited.
   Only imports are adapted from `prinet` to `prin` / the PRIN-owned support
   path. Assertions, expected values, parametrization, call order, and meaning
   stay unchanged.
2. **Compatibility gaps are implementation work.** A failure or collection gap
   from absent behavior is fixed in the owning Rust crate and exposed via thin
   PyO3/Python delegation. No Python numerical reimplementation.
3. **No semantic-test rewrite.** API-shape adapters live in the compatibility
   layer, never inside copied acceptance tests.
4. **Existing exception governance is unchanged.** A tolerance change is
   permitted only when attributable solely to amendments #14/#16/#17/#25 and
   carries a per-test annotation + Parity Report entry. GPU/Triton-only cases
   follow the reference's availability guard and reuse WP-036D's
   `_torch_compat.py` device dispatch. Neither mechanism permits assertion
   deletion, weakened logic, or an unapproved skip.
5. **DV-025.** `retrain_controller` resolved in `0144M2` as a thin `prin`
   wrapper over the Rust owner, with unit + parity tests and
   `tools/wp001_ownership.json` / traceability-baseline regeneration.
6. **One audit range.** Each sub-pass commits at its own green local gate. The
   contiguous `0144M`+`0144M1`–`0144M8` range feeds the single mandatory S2
   audit `0144N`; push cadence remains amendment #28.

## 4. Proposed decomposition

| Sub-pass | Reference files | `def test_` | Lines | Focus |
|---|---|---:|---:|---|
| `0144M1` | `integration_q3` + `y2q1` + `y2q4` | 93 | 1,839 | top-level `prinet` integration surface; `_deprecation` re-exercise; DiscreteDTG layer / `OscillatoryAttention` / `training_hooks` paths |
| `0144M2` | `y2q2` + `y2q3` | 65 | 1,623 | temporal-hybrid + subconscious-retraining clusters; **DV-025 `retrain_controller` resolution** + parity tests + traceability regeneration |
| `0144M3` | `y3q1` + `y3q2` | 78 | 1,352 | propagation/daemon/profiler; `adaptive_allocation`; `mot_evaluation` (hypothesis, motmetrics, scipy) |
| `0144M4` | `y3q3` + `y3q4` + `y3q45` + `y3q49` | 117 | 2,095 | `fused_kernels` family; OscilloSim; `slot_attention`; MSVC-path helpers |
| `0144M5` | `y4q1` + `y4q1_2` + `y4q1_3` | 171 | 1,877 | `y4q1_tools` statistical surface; OscilloSim; `TemporalSlotAttentionMOT` |
| `0144M6` | `y4q1_4` + `y4q1_5` + `y4q1_9` | 158 | 2,020 | `y4q1_tools` remainder; benchmark support (`y4q1_5_benchmarks`); `ablation_variants` tracker |
| `0144M7` | `y4q1_7` + `y4q1_8` | 194 | 1,911 | `ablation_variants`; `temporal_metrics`; `temporal_training.TemporalTrainer`; `adversarial_tools` |
| `0144M8` | `y4q2` + `y4q3` + `y4q4` + `triton_kernels` + `gpu` + consolidation | 221 | 3,093 | figure/table generation + publication; GPU/Triton `skipif` guarding via WP-036D dispatch; full 1,172-test accounting + S1 handoff |

`0144M8` is pre-authorised to split into `0144M8a`/`0144M8b` under Development
Workflow §7 (as `0141D`→`0141D1`/`0141D2` and the `0144A3` pre-authorisation
did) if repository verification at its start shows one reviewable range is
exceeded; planned count is held until then.

Every pass runs the relevant copied subset plus all tests for any changed
first-party implementation, keeps changed code at ≥95% line coverage, and runs
the applicable Rust/Python quality and security gates (`ruff`/`ruff format`/
`mypy --strict`/`pytest`/`bandit`/Snyk Code on modified supported source;
dependency + `cargo` gates only if a manifest or crate changes — expected for
DV-025 in `0144M2`). This governance-only amendment does not itself run those
gates. Coverage instrumentation remains host-blocked
([[wp036-coverage-tooling-blocked]]); manual review + targeted regression tests
stand in, CI authoritative.

## 5. Proposed amendment #39 recording

Amendment #39 adds eight planned sub-sessions without renumbering the integer
sequence or the surrounding `0144A`–`0144AB` block. Link chain:

`0144M` → `0144M1` → `0144M2` → `0144M3` → `0144M4` → `0144M5` → `0144M6` →
`0144M7` → `0144M8` → `0144N`.

`0144N`'s predecessor becomes `0144M8`. Planned session count: **245 → 253**
(254 if `0144M8` splits). `0144N` audits the aggregate strict port and
independently diffs every copied test against its reference, allowing only
governed import adaptations and explicitly recorded tolerance / backend-
availability annotations. WP-036C acceptance criteria and non-goals (0144M
brief) are unchanged except that completing missing behavior behind
already-public compatibility surfaces is explicitly in-scope implementation
repair (as amendment #35 established for WP-036B); no new public symbol is
authorized beyond DV-025's `retrain_controller`.

Same disposition class as amendments #32/#34/#35 (S1 decomposition).

## 6. Risks and controls

- **R1 — collection count masks uncollected tests.** Control: retain the
  per-file source-count table; reconcile all 1,097 functions in `0144M8`; do
  not treat 1,172 collected as the source contract.
- **R2 — compatibility adapters drift into Python numerics.** Control:
  numerical authority stays in Rust; Python/PyO3 layers are thin delegation;
  `check_no_python_numerics.py` gate + S2 ownership inspection.
- **R3 — pressure to edit tests after failures.** Control: copied-file diff is a
  per-pass gate and an explicit `0144N` audit action.
- **R4 — y-series integration breadth.** The y3/y4 files touch nearly every
  compat surface at once; a single missing behavior can red-line a whole file.
  Control: per-sub-pass collection first, gap triage second, port third; an
  out-of-scope discovery is governed, not worked around.
- **R5 — DV-025 Rust work in a port pass.** Control: `0144M2` is deliberately
  the smallest function-count pass (65) to absorb the `retrain_controller`
  binding + gradcheck/parity + traceability regeneration without exceeding its
  range.
- **R6 — consolidation omits earlier failures.** Control: `0144M8` runs the
  complete 24-file ported subset and the full WP-036B+WP-036C ported suite,
  and produces a file-by-file accounting table for all 1,097 functions,
  tolerances, backend guards, and discoveries.

## 7. Next step

Amendment #39 is recorded in `DOCS/PRIN_Project_Plan.md` §8.3,
`DOCS/sessions/SESSION_REGISTER.md`, `DOCS/sessions/TRACEABILITY.md`,
`DOCS/sessions/phase-6/README.md`, and `tools/wp001_baseline.py`
(`_SUBSESSION_BLOCKS` + planned count 245 → 253); the eight sub-pass briefs
`0144M1`–`0144M8` are authored; the running handoff is
`DOCS/experiments/0144M-wp036c-s1-handoff.md`. Execute `0144M1`
(integration_q3 + y2q1 + y2q4). Preserve Testing Standards §1.1 literally,
rebuild any missing compatibility behavior through Rust-backed layers, and
commit locally only when each sub-pass gate is green.

# Session 0144M / WP-036C S1 running handoff

**Date:** 2026-08-31 (session start + decomposition; `0144M1`–`0144M3` executed)
**Status:** S1 **in progress** — sub-passes `0144M1` (integration_q3 + y2q1 +
y2q4, 93 fns), `0144M2` (y2q2 + y2q3, 65 fns, DV-025 `retrain_controller`),
and `0144M3` (y3q1 + y3q2, 78 fns) **COMPLETE and committed locally** at green
gates; not pushed. **236 / 1,097** reference functions ported. Plan amendment
#39 inserted the eight strict-port sub-passes `0144M1`–`0144M8` feeding the
single mandatory S2 audit `0144N`; plan amendment #40 (2026-08-31) records
three `0144M1` scope confirmations (deferred-symbol rebuild in-scope,
`__version__` → `0.3.0`, minimal `docs/` guides). Next: `0144M4`.

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

### 0144M1 — integration_q3 + y2q1 + y2q4 — COMPLETE (2026-08-31)

**Committed locally at a green sub-pass gate; not pushed. Plan amendment #40
recorded three maintainer `AskUserQuestion` scope confirmations. Next: 0144M2.**

#### Strict-port accounting and semantic proof

| Reference | Stable port | Lines | `def test_` | Result (default gate) | Slow | Tolerance annotations | Discoveries |
|---|---|---:|---:|---|---:|---:|---|
| `test_integration_q3.py` | `tests/test_acceptance_integration_q3.py` | 496 | 19 | 19 / 19 | 0 | 0 | `DeltaThetaGammaNetwork.integrate`; `PhaseToRateConverter.temperature`; `HierarchicalResonanceLayer.pac_depth_dt/tg` mirrors |
| `test_y2q1.py` | `tests/test_acceptance_y2q1.py` | 926 | 48 | 42 / 42 + 6 not-slow… (47/48 incl. slow) | 6 | 0 | `DiscreteDeltaThetaGamma` core rebuild; `InterleavedHybridPRINet` rebuild; `OscillatoryAttention.alpha` + `mask`; `apply_lr_adjustment`/`apply_k_range_narrowing`/`apply_regime_bias`; `prin.nn` re-exports |
| `test_y2q4.py` | `tests/test_acceptance_y2q4.py` | 417 | 26 | 26 / 26 (29 incl. parametrize + slow) | 1 | 0 | `prin.__version__` → `0.3.0`; `docs/` guides; `benchmarks/y2q4_benchmarks.py` support module |
| **M1 total** | **3 files** | **1,839** | **93** | **91 / 91 default gate** | **7** | **0** | — |

Full M1 run **incl. slow**: 95 passed, 1 failed — the single failure is
`test_y2q1.py::TestDiscreteDeltaThetaGamma::test_speed_vs_transformer`
(`@pytest.mark.slow`, not in the default `-m "not slow and not gpu"` gate): it
asserts the existing Rust-backed `DiscreteDeltaThetaGammaLayer` bridge is ≤5×
slower than an `nn.TransformerEncoderLayer`; measured 5.3–8.0× depending on
host load. This is the architecturally-fixed per-call `torch.autograd.Function`
+ DLPack dispatch overhead recorded in plan amendment #30 (bridge overhead at
small shapes). Carried to `0144N` as an out-of-scope discovery, not weakened.

**Import-only proof:** `tools/_port_m1.py` performs the import remap; the ports
are then `ruff format`-normalised (matching the E4 precedent). `git diff
--no-index` against each archived reference shows only `from prinet.* import`
module-path lines changed, plus `ruff format` assert-message re-wraps
(`assert (\n cond\n), msg` → `assert cond, (\n msg\n)` — no assertion, value,
parametrization, call order, or semantics changed). Per-file `ruff` ignores
added to `pyproject.toml` for the three ports + `benchmarks/y2q4_benchmarks.py`
(faithful-copy `F401`/`I001`/`E501`/`RUF00x`/`UP045`/`B007`), matching the
E1–E6 pattern.

#### Changed-owner mapping

| Compatibility behaviour | Numerical / Rust owner | Python exposure |
|---|---|---|
| Standalone `DiscreteDeltaThetaGamma` `step` / `integrate` | `prin_train::bands::DiscreteDeltaThetaGamma` (audited Burn module, WP-022) via new `DiscreteDeltaThetaGammaBridge` PyO3 class (`crates/prin-py/src/bindings/train_hierarchical_layers.rs`) | `prin.nn.hierarchical_layers.DiscreteDeltaThetaGamma` — real `nn.Module` holding the reference `nn.Parameter` / `nn.Linear` declarations (byte-identical `torch.randn` / `xavier_uniform_` init); each `step`/`integrate` pushes params to Rust via `load_torch_weights` and runs the (non-differentiable) Rust forward, then adds a value-preserving `Σ(p.sum() − p.sum().detach())` zero term so `loss.backward()` populates `.grad` (E4 layer-mirror pattern). `deferred_layers.py` re-exports it; the D-2.2 stub + `_raise_disposition` helper are removed. |
| `DiscreteDeltaThetaGamma.order_parameters` / `.pac_index` | **new** methods on `prin_train::bands::DiscreteDeltaThetaGamma` (Rust; `order_parameters` reuses `prin_metrics::order::kuramoto_order_parameter`, `pac_index` is a faithful port of the reference cos-correlation proxy) | bridge `order_parameters` / `pac_index` → Python returns scalar tensors |
| `OscillatoryAttention.alpha` (learnable per-head coherence-bias strength) | `prin_train::attention::OscillatoryAttention` (`alpha` already owned); **new** `set_alpha` method + bridge `set_alpha(list[float])` | Python `alpha` `nn.Parameter` (zeros, `[n_heads]`) pushed to Rust before every forward (so it genuinely drives the bias) + zero term for `.grad` |
| `OscillatoryAttention(..., mask=...)` | **new** `prin_train::attention::OscillatoryAttention::forward_masked` — `[seq, seq]` mask, `-inf` at `0` positions before softmax, broadcast over batch/heads; bridge `forward` gains a `mask` arg, ctx replays it, `backward` returns a 3-tuple | `prin.nn.attention.OscillatoryAttention.forward` gains a `mask` kwarg |
| `DeltaThetaGammaNetwork.integrate(state, n_steps, dt, record_trajectory=False)` | loops the existing Rust-backed `_HierarchicalNetwork.step`; faithful port of the reference loop | new method on `prin._torch_compat._HierarchicalNetwork` |
| `PhaseToRateConverter.temperature` / `HierarchicalResonanceLayer.pac_depth_dt` / `.pac_depth_tg` | Rust bridges remain the numerical owners of the active parameters | value-preserving `nn.Parameter` mirrors carrying the reference names/init, routed through `forward` with an exactly-zero term for `.grad` population (E4 pattern) |
| `apply_lr_adjustment` / `apply_k_range_narrowing` / `apply_regime_bias` | n/a — pure control-signal bookkeeping over `torch.optim` param groups / `nn.Module` parameter clamps (same category as `StateCollector`) | faithful ports in `prin.training_hooks`; `prin.nn` re-exports them + `TelemetryLogger` so `from prinet.nn import ...` resolves under the adapted path |
| `InterleavedHybridPRINet` | PyTorch composition over the real `DiscreteDeltaThetaGamma` + `OscillatoryAttention` + `nn.Linear`/`LayerNorm`/`GELU` | real `nn.Module` in `prin.nn.hybrid_compat` (D-2.2 stub replaced), incl. `oscillatory_parameters()` / `rate_coded_parameters()` |
| `benchmarks/y2q4_benchmarks` (`run_j3_regression_suite`, `run_k1_capacity_sweep`, `run_k2_phase_diagrams`, `generate_clevr_n`, `DiscreteDTGCLEVRN`, …) | benchmark orchestration (E2 permitted experiment-tooling exception) | `benchmarks/y2q4_benchmarks.py`, import-adapted from the reference |
| `test_y2q4::TestVersioning` / `TestAPIFreeze` | n/a | `prin.__version__` / `pyproject.toml` / `Cargo.toml` / `CITATION.cff` bumped `0.3.0-alpha.1` → `0.3.0`; `CHANGELOG.md` + `tests/test_wp001_baseline.py` version assert updated |
| `test_y2q4::TestDocumentation` | n/a | new `docs/Architecture_Guide.md`, `docs/Getting_Started_Tutorial.md` (with a "Migrating from prinet" section), `docs/API_Reference_Coupling_Topologies.md` |

Rust regression coverage: 4 new `bands.rs` unit tests (`order_parameters`
synchronized/wrong-width, `pac_index` finite-non-negative/wrong-width) and 3
new `attention.rs` unit tests (`forward_masked` excludes/rejects, `set_alpha`
drives the bias). `cargo test -p prin-train --lib`: 447 passed.
`cargo test --workspace`: 48 suites ok, 0 failed.

Governance updated in step: `deferred_layers.py` docstring + `__all__`;
`prin.nn.__init__` re-exports + `__all__`; `_prin_core.pyi`
(`DiscreteDeltaThetaGammaBridge`, `OscillatoryAttentionBridge.set_alpha` /
`mask` / 3-tuple ctx); `DOCS/sphinx/migration_guide.rst` consolidated table
re-rendered + `DiscreteDeltaThetaGamma` / `InterleavedHybridPRINet` prose rows;
`tests/test_bucket_g_remainder.py` `test_hybrid_family_d22_stubs_raise`
parametrize trimmed for `InterleavedHybridPRINet`; `tools/check_no_python_numerics.py`
scope unchanged (both new/edited modules already listed as bridge modules);
`SESSION_REGISTER.md` / `TRACEABILITY.md` / `phase-6/README.md` amendment #40
recorded + `0144M1` marked COMPLETE; `tools/wp001_baseline.py` amendment
comment.

#### Command evidence

- `pytest tests/test_acceptance_integration_q3.py tests/test_acceptance_y2q1.py
  tests/test_acceptance_y2q4.py -m "not slow"`: **91 passed, 5 deselected**.
- `pytest tests/ -m "not slow and not gpu"`: **1874 passed, 2 skipped, 21
  deselected** (before the GPU-dispatch and version-assert fixes it was
  1872/3-failed; both fixed — the extension is rebuilt with `--features cuda`
  per `gpu.yml`, and `test_wp001_baseline.py`'s `0.3.0-alpha.1` assert updated).
- `ruff check` (repo) + `ruff format --check` (repo): clean.
- `mypy python/prin --strict`: clean (55 files).
- `bandit -r python/ benchmarks/y2q4_benchmarks.py -c pyproject.toml`: 0 new
  issues (the 1 remaining LOW `B110` is the pre-existing `hybrid_compat.py:327`
  from 0144E5).
- `tools/check_no_python_numerics.py`: clean (19 modules).
- `tools/wp036_migration_table.py check`: OK (172 symbols).
- `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets --
  -D warnings`: clean.
- `cargo test -p prin-train --lib`: 447 passed; `cargo test --workspace`: 48
  suites ok, 0 failed.
- `cargo audit`: exit 0 with only the three pre-existing governed warnings
  (`bincode` RUSTSEC-2025-0141, `paste` RUSTSEC-2024-0436, yanked `chacha20`).
- **Snyk Code** (`--severity-threshold=low`) on `python/prin`,
  `crates/prin-train/src`, `crates/prin-py/src`, and `tests`: **0 issues**.
- `Cargo.lock` delta is the 8 workspace-crate version strings only; no new
  dependency, so Snyk Open Source / `pip-audit` are not applicable.
- Coverage instrumentation remains host-blocked
  ([[wp036-coverage-tooling-blocked]]); the acceptance suite + `cargo test`
  unit coverage + manual review stand in, CI authoritative.

**Parity-evidence disposition:** directly comparable PRINet 3.0 behaviour
exists and is the literal 93-test acceptance source. Imports-only diff (plus
the governed `ruff format` re-wraps) + 91/91 default-gate execution is the M1
parity evidence. No new hazard tolerance or backend-availability guard was
introduced, so `DOCS/sphinx/parity_report.rst` is unchanged.

### 0144M2 — y2q2 + y2q3 (DV-025 `retrain_controller`) — COMPLETE (2026-08-31)

**Committed locally at a green sub-pass gate; not pushed. Next: 0144M3.**

#### Strict-port accounting and semantic proof

| Reference | Stable port | Lines | `def test_` | Result (default gate) | Slow | Tolerance annotations | Discoveries |
|---|---|---:|---:|---|---:|---:|---|
| `test_y2q2.py` | `tests/test_acceptance_y2q2.py` | 706 | 30 | 30 / 30 | 0 | 0 | `TemporalPhasePropagator` compat wrapper; `inter_frame_phase_correlation` torch wrapper; `TemporalHybridPRINet` rebuild; `ActiveControlTrainer` rebuild; `retrain_controller` (DV-025) real implementation; `benchmarks/y2q1_benchmarks.py` + `benchmarks/y2q2_benchmarks.py` support modules |
| `test_y2q3.py` | `tests/test_acceptance_y2q3.py` | 917 | 35 | 33 / 35 | 0 | 0 | `HybridPRINetV2` conv_stem + param mirrors; `HybridPRINetV2CLEVRN` rebuild; `PhaseTracker.forward` + param mirror; `benchmarks/y2q3_benchmarks.py` support module; `prin.nn.subconscious_model` re-export module |
| **M2 total** | **2 files** | **1,623** | **65** | **63 / 65 default gate** | **0** | **0** | — |

**2 CUDA-only out-of-scope discoveries** (Rust bridge `!Send` backward threading):
- `test_clevr6_convergence` — `PyOscillatoryAttentionCtx` unsendable on CUDA backward
- `test_v2_cifar10_no_oom` — `PyHybridPRINetV2Ctx` unsendable on CUDA backward

Both are Rust-side PyO3 `#[pyclass]` thread-safety limitations; the bridges work
correctly on CPU and for forward-only CUDA. Carried to `0144N` as out-of-scope
discoveries, not weakened.

#### Changed-owner mapping

| Compatibility behaviour | Numerical / Rust owner | Python exposure |
|---|---|---|
| `TemporalPhasePropagator(carry_strength, amplitude_decay)` `.propagate()` / `.propagate_sequence()` | orchestration over `DiscreteDeltaThetaGamma.step` | `prin._torch_compat.TemporalPhasePropagator` + `_wrap_phase` |
| `inter_frame_phase_correlation` torch-tensor API | `prin._prin_core.inter_frame_phase_correlation` (Rust; numpy) | `prin.metrics.inter_frame_phase_correlation` torch↔numpy marshalling wrapper + batched input |
| `TemporalHybridPRINet` (multi-frame sequence classification) | PyTorch composition over `DiscreteDeltaThetaGamma` + `nn.MultiheadAttention` | `prin.nn.hybrid_compat.TemporalHybridPRINet` (D-2.2 stub replaced) |
| `HybridPRINetV2CLEVRN` (scene+query CLEVR-N adapter) | PyTorch composition over `InterleavedHybridPRINet` | `prin.nn.hybrid_compat.HybridPRINetV2CLEVRN` (D-2.2 stub replaced) |
| `HybridPRINetV2` `use_conv_stem` + `oscillatory_parameters()` / `rate_coded_parameters()` | Rust bridge forward + Python param mirrors (E4 zero-term pattern) | `prin.nn.hybrid.HybridPRINetV2` enhanced with conv stem + `_freq`/`_coupling` param mirrors |
| `PhaseTracker.forward()` + gradient flow | Rust bridge `match_frames` (non-differentiable) + Python `_proj` param mirror | `prin.nn.phase_tracker.PhaseTracker.forward` + float64 CPU marshalling |
| `ActiveControlTrainer` (training-loop control policies) | orchestration over `apply_lr_adjustment` / `apply_regime_bias` | `prin.training_hooks.ActiveControlTrainer` (D-2.2 stub replaced) |
| `retrain_controller` (DV-025: telemetry-supervised controller retraining) | `SubconsciousController` MLP training + ONNX export | `prin.training_hooks.retrain_controller` (D-2.2 stub replaced); `prin.nn.subconscious_model` re-export module |
| `DiscreteDeltaThetaGamma` device dispatch | Rust bridge step/integrate | `prin.nn.hierarchical_layers` `.to(dtype, device)` on DLPack output |
| `benchmarks/y2q1_benchmarks` (`DiscreteDTGCLEVRN`, `InterleavedCLEVRN`) | benchmark orchestration | `benchmarks/y2q1_benchmarks.py` |
| `benchmarks/y2q2_benchmarks` (`make_temporal_clevr`, `run_f_ab_test`) | benchmark orchestration | `benchmarks/y2q2_benchmarks.py` |
| `benchmarks/y2q3_benchmarks` (`run_g_*`, `run_h_*`, `run_i_*`) | benchmark orchestration | `benchmarks/y2q3_benchmarks.py` |

Governance updated in step: `test_bucket_g_remainder.py` parametrize trimmed for
`HybridPRINetV2CLEVRN` / `TemporalHybridPRINet` / `ActiveControlTrainer`;
`DOCS/sphinx/migration_guide.rst` consolidated table re-rendered via
`tools/wp036_migration_table.py render`; `SESSION_REGISTER.md` / `TRACEABILITY.md`
/ `phase-6/README.md` updated; handoff appended.

#### Command evidence

- `pytest tests/test_acceptance_y2q2.py tests/test_acceptance_y2q3.py -m "not slow"`:
  **63 passed, 1 skipped, 2 failed** (CUDA-only bridge-backward threading).
- `pytest tests/ -m "not slow and not gpu"`: **1938 passed, 4 skipped, 2 failed**
  (same 2 CUDA-only).
- `tools/wp036_migration_table.py check`: OK (172 symbols).
- Full existing suite no regressions beyond the 2 known CUDA discoveries.

### 0144M3 — y3q1 + y3q2 — COMPLETE (2026-08-31)

**Committed locally at a green sub-pass gate; not pushed. Next: 0144M4.**

#### Strict-port accounting and semantic proof

| Reference | Stable port | Lines | `def test_` | Result (default gate) | Slow | Tolerance annotations | Discoveries |
|---|---|---:|---:|---|---:|---:|---|
| `test_y3q1.py` | `tests/test_acceptance_y3q1.py` | 665 | 40 | 40 / 40 | 0 | 0 | `FeedbackInhibition.compete` arbitrary leading dims; `SubconsciousDaemon` DLQ (`dead_letter_queue`/`dlq_size` + 3 ctor params + `_run_inference` escalation); `prin.datasets` port; `benchmarks/clevr_n.py` M.3/M.4 extended-palette section |
| `test_y3q2.py` | `tests/test_acceptance_y3q2.py` | 687 | 38 | 38 / 38 | 0 | 0 | `prin.nn.allocation` realigned to PRINet 3.0 `adaptive_allocation` API (`OscillatorBudget` frozen dataclass w/ `.total` property, `estimate_complexity` → `float32` tensor, `AdaptiveOscillatorAllocator.min_total/max_total/_mlp/__call__`, `DynamicPhaseTracker(dets_t, dets_t1)` callable + tensor `matches`); new `prin.nn.mot_evaluation` (synthetic generators + `evaluate_tracking` over Rust `prin.eval.MotAccumulator` + `AttentionTracker` baseline + `run_subconscious_ab_test`); `prin.nn` re-exports |
| **M3 total** | **2 files** | **1,352** | **78** | **78 / 78 default gate** | **0** | **0** | — |

No slow-marked tests in either file; no new hazard-tolerance annotation or
backend-availability guard; `DOCS/sphinx/parity_report.rst` unchanged. Full run
including slow: same 78/78 (no `@pytest.mark.slow` cases in this range).

**Import-only proof:** `tools/_port_m3.py` performs the import remap; the two
ports are then `ruff format`-normalised (M1 precedent). `git diff --no-index`
against each archived reference shows only `from prinet.* import` module-path
lines changed — plus, in `test_y3q1`, one
`from prinet.core.propagation import (…19 symbols…)` split into
`from prin._torch_compat import (…16…)` + `from prin.nn import (…3…)` because
PRIN partitions that reference module across two owners (identical in kind to
the `test_integration_q3` split in 0144M1) — and `ruff format` assert-message
re-wraps in `test_y3q2` (`assert (\n cond\n), msg` → `assert cond, (\n msg\n)`;
adjacent f-string concatenation collapsed). No assertion, value,
parametrization, call order, or semantics changed.

Per-file `ruff` ignores added to `pyproject.toml` for the two ports
(faithful-copy `F401`/`F841`/`I001`/`E501`/`B905`/`RUF002`/`RUF003`/`RUF059`/
`RUF100`), matching the `test_acceptance_y2q1`/`y2q4` pattern.

#### Changed-owner mapping

| Compatibility behaviour | Numerical / Rust owner | Python exposure |
|---|---|---|
| `FeedbackInhibition.compete(rates)` with arbitrary leading dims (`(…, N)`, incl. 1-D) and any float dtype | `prin_train::inhibition::FeedbackInhibition` STE (unchanged); Python reshapes `(…, N)` → `(-1, N)` → bridge → original shape; `apply_rust_bridge` already casts f32↔f64 and restores dtype/device | `prin.nn.inhibition.FeedbackInhibition.compete` — closes the "arbitrary leading batch dimensions are a WP-036B/C parity item" note in that module |
| `SubconsciousDaemon` dead-letter queue + escalation (`dlq_maxlen`, `max_errors_before_escalation`, `error_escalation_callback` ctor params; `dead_letter_queue`/`dlq_size` properties; `_run_inference` DLQ append + threshold callback) | n/a — threading / telemetry bookkeeping only (same disposition as `StateCollector`) | faithful port into `prin.subconscious_compat.SubconsciousDaemon` |
| `prinet.utils.datasets` (`CIFAR10_CLASSES`/`CIFAR10_MEAN`/`CIFAR10_STD`/`FMNIST_CLASSES`, `get_cifar10_loaders`, `get_fashion_mnist_loaders`, `evaluate_accuracy`) | n/a — torchvision transform pipelines + `DataLoader` construction + an `argmax`/equality accuracy count (data plumbing) | faithful port filling the `prin.datasets` stub |
| `benchmarks.clevr_n` M.3/M.4 (`COLORS_24`/`COLORS_24_RGB`/`D_COLOR_24`, `make_clevr_n_extended`, `_rgb_to_lab`/`_delta_e`/`build_adversarial_colour_pairs`, `make_adversarial_clevr`, `_make_query_ext`) | n/a — synthetic-scene generation (same category as the existing `make_clevr_n`) | appended verbatim to `benchmarks/clevr_n.py`; `TensorDataset` added to imports; two comment glyphs de-unicoded to match the file's existing normalisation |
| `prinet.nn.adaptive_allocation` full reference API surface | `prin_train::allocation` (rule allocation, learned MLP, `estimate_complexity` spread reduction, per-budget `PhaseTracker` cache) — **unchanged**; the Rust bridge is untouched | `prin.nn.allocation` reshaped: Python frozen `OscillatorBudget` (`.total` property, value eq), `estimate_complexity` returns `torch.float32` scalar tensor, `AdaptiveOscillatorAllocator` exposes `min_total`/`max_total`/`_mlp`/`__call__` + the reference `ValueError` messages, `DynamicPhaseTracker` callable as `tracker(dets_t, dets_t1)` with an internal `Seed` and an `int64` `matches` tensor |
| `prinet.nn.mot_evaluation.evaluate_tracking` / `run_subconscious_ab_test` / `AttentionTracker` / `generate_{linear,crowded,temporal_reasoning}_mot_sequence` / `Detection` / `TrackingResult` / `load_mot17_sequence` | MOT metrics core = Rust `prin_daemon::mot` via `prin.eval.MotAccumulator` (the "`python/prin/eval` orchestration" the WP-030 migration guide flagged *not yet delivered*); synthetic generators and the `AttentionTracker` baseline are Python (same category as `benchmarks` generators / the `benchmarks.clevr_n` LSTM/Transformer baselines) | new `prin.nn.mot_evaluation`, re-exported from `prin.nn`; `prin.nn.TrackingResult` now re-exports this module's (matches PRINet 3.0; `prin.nn.phase_tracker.TrackingResult` still importable from its submodule for `ablation.py`) |

No Rust crate, `Cargo.*`, PyO3 binding, or `.pyi` change — the entire M3
compatibility surface is Python delegation over already-shipped Rust owners.

Governance updated in step:
- `tests/test_train_bridge_allocation.py` realigned to the now-canonical
  `prin.nn.allocation` API (`.total()` → `.total`, `estimate_complexity`
  `abs=1e-12` → `abs=1e-6`, reference `ValueError` match string).
- `tests/test_train_layers_bindings.py::test_feedback_inhibition_requires_2d_input`
  → `test_feedback_inhibition_accepts_arbitrary_leading_dims` (asserts the new
  PRINet-3.0-parity behaviour; a 0-d tensor is still rejected).
- `DOCS/sphinx/migration_guide.rst` WP-030 "`evaluate_tracking`'s tracker-wiring
  loop … not yet delivered" deviation note → "delivered at WP-036C S1 0144M3".
- `python/prin/nn/__init__.py` module docstring + `__all__` + re-exports;
  `SESSION_REGISTER.md` / `phase-6/README.md` `0144M3` → COMPLETE.
- **Pre-existing `0144M2` gate debt cleaned in step** (same `0144M` feeder
  range → same `0144N` audit): `ruff check` (16 findings across
  `_torch_compat.py` / `metrics.py` / `hybrid_compat.py` / `training_hooks.py`
  / `test_bucket_g_remainder.py`, incl. dangling imports from M2's parametrize
  trims), `ruff format --check` (8 files incl. `benchmarks/y2q{1,2,3}_benchmarks.py`
  and the M2 ports), and `mypy --strict` (3: `hybrid.py` `conv_stem` Optional,
  `hybrid_compat.py` `no-any-return`, `_torch_compat.py` duplicate `_wrap_phase`
  def) were all red at commit `6ba0448`; all fixed here. `test_acceptance_y2q2`
  / `y2q3` per-file `ruff` ignores added (M2 committed those ports without
  them). Recorded for `0144N` visibility, not attributable to M3's changes.

#### Command evidence

- `pytest tests/test_acceptance_y3q1.py tests/test_acceptance_y3q2.py`:
  **78 passed** (no deselected — no slow/gpu cases in range).
- `pytest tests/ -m "not slow and not gpu"`: **2016 passed, 4 skipped, 21
  deselected, 2 failed** — the 2 failures are the known `0144M2` CUDA-only
  discoveries (`test_clevr6_convergence`, `test_v2_cifar10_no_oom`,
  `PyOscillatoryAttentionCtx` unsendable on CUDA backward), unchanged.
- `git diff --no-index` reference vs port (both files): import-path lines +
  the one governed split + `ruff format` assert re-wraps only.
- `ruff check python/ tests/ benchmarks/ tools/`: clean.
- `ruff format --check python/ tests/ benchmarks/ tools/`: clean (205 files).
- `mypy python/prin --strict`: clean (57 files).
- `tools/check_no_python_numerics.py`: clean (19 modules) — `nn/mot_evaluation.py`
  is **not** added to the scanned set: it houses the deliberate non-oscillatory
  `AttentionTracker` baseline + torch synthetic generators, the same
  eval/benchmark-tooling category as `benchmarks/y2q4_benchmarks.py` and
  `benchmarks/clevr_n.py`'s baselines; its MOT metrics go through Rust
  (`prin.eval.MotAccumulator`).
- `tools/wp036_migration_table.py check`: OK (172 symbols — no new
  `prinet.__all__`-level symbol; all M3 additions are submodule-level).
- `bandit -r python/ -c pyproject.toml`: 1 LOW `B110` — the pre-existing
  `hybrid_compat.py:327` from 0144E5, unchanged.
- `interrogate -c pyproject.toml python/`: PASS (97.2%, min 95%).
- **Snyk Code** (`--severity-threshold=low`) on `python/prin` and `tests`:
  **0 issues**.
- No dependency / manifest / crate change → Snyk Open Source, `pip-audit`,
  `cargo audit`, and the `cargo` build/test/clippy gates are not applicable
  (`pyproject.toml` delta is per-file `ruff` ignores only).
- Coverage instrumentation remains host-blocked
  ([[wp036-coverage-tooling-blocked]]); the 78-test acceptance subset + the
  full 2016-test suite + manual review stand in, CI authoritative.

**Parity-evidence disposition:** directly comparable PRINet 3.0 behaviour
exists and is the literal 78-test acceptance source. Imports-only diff (plus
the governed split and `ruff format` re-wraps) + 78/78 default-gate execution
is the M3 parity evidence. No new hazard tolerance or backend-availability
guard, so `DOCS/sphinx/parity_report.rst` is unchanged.

### 0144M4 — not started
### 0144M5 — not started
### 0144M6 — not started
### 0144M7 — not started
### 0144M8 — not started

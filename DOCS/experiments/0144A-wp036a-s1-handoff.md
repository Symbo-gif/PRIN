# Session 0144A / WP-036A S1 running handoff

**Date:** 2026-08-30 (decomposition); 2026-08-31 (0144A4 close)
**Status:** all four sub-passes `0144A1`–`0144A4` **COMPLETE** at their green
local gates (Plan amendment #34, MichaelMaillet, 2026-08-30). The 13 D-D
trainable-layer / discrete-network symbols (rows 31–42, 44) are all real
`prin-train`-backed implementations. The contiguous `0144A` + `0144A1`–`0144A4`
range is committed locally only and awaits the single mandatory S2 audit
`0144B`; S1 does not self-certify.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report (`DOCS/reports/036-project-state.md`),
WP-036A declaration (Plan amendment #33), the 0144A brief, Project Plan
§6/§8, Coding Standards §1.2/§2/§3.2, Testing Standards §1, the D-D
disposition appendix rows 31–44, and the existing `prin-train` /
`prin-py` bridge patterns.

**Session ID/type:** 0144A — WP-036A S1 (Coding), decomposed.
**Planned outputs (0144A brief):** 13 trainable-layer Rust implementations +
PyO3 bindings + Python stub replacements + gradcheck/parity/error tests +
Migration Guide update + S1 handoff note — satisfied **in aggregate** across
`0144A1`–`0144A4`.

## Blocking finding — S1 exceeds one reviewable commit range

Repository verification (`main` @ `2b677ee`) showed WP-036A S1 as a single
session violates Development Workflow §7:

- The 13 symbols are **13 new trainable Burn modules**, not thin bindings
  over audited owners (contrast sub-pass 0141B, bindings-only, still one of
  five sub-passes).
- **Five composed primitives have no trainable Rust owner** and must be
  Burn-ported first: continuous `DeltaThetaGammaNetwork`,
  `PhaseAmplitudeCoupling`, `phase_to_rate` (currently `prin-sim`,
  non-autodiff), the FFI phase-delay gate, the DG EMA-integration stage.
- Per-symbol PyO3 `autograd.Function` bridges + Python `nn.Module`s +
  `_prin_core.pyi` updates + float64 gradcheck + PRINet-3.0 forward-parity +
  ≥95% coverage + one maturin rebuild per unit.
- Estimated delta ≈ 3.5–4.5k Rust + 1.2–1.6k bridges + 0.6–0.9k Python +
  2–2.8k tests. Every prior Phase 3–6 S1 delivered 300–1,500 source lines.

## Decomposition (adopted — amendment #34)

`DOCS/sessions/phase-6/WP-036A-S1-execution-plan-and-decomposition.md`
(ADOPTED). Four dependency-ordered sub-passes, all feeding the single S2
audit `0144B`:

| Sub-pass | Symbols (D-D rows) |
|---|---|
| `0144A1` | `FeedforwardInhibition` (31), `DentateGyrusConverter` (32), `DGLayer` (33), `oscillatory_weight_init` (34), `SparsityRegularizationLoss` (38) |
| `0144A2` | `PhaseToRateConverter` (35), `PhaseToRateAutoencoder` (36), `DenseAutoencoder` (37) |
| `0144A3` | `HierarchicalResonanceLayer` (39), `PhaseAmplitudeCouplingLayer` (40), `DiscreteDeltaThetaGammaLayer` (44) — pre-authorised to split `0144A3a`/`0144A3b` |
| `0144A4` | `PRINetModel` (41), `compile_model` (42) + consolidation |

Strategic dispositions D-2 (`compile_model` = pure-Python `torch.compile`
passthrough), D-3 (`phase_to_rate` soft gradchecked / hard STE), D-4 (D-A
parity-tolerance governance for f32/f64 deltas), D-5
(`HierarchicalResonanceLayer` batched, documented D3).

## Governance recording (this session)

- Plan amendment #34 added to `DOCS/PRIN_Project_Plan.md` §8.3.
- `SESSION_REGISTER.md`, `DOCS/sessions/README.md`,
  `DOCS/sessions/phase-6/README.md`, `DOCS/sessions/TRACEABILITY.md`: 4
  sub-session rows + amendment note; planned count 216 → 220.
- Four sub-pass briefs authored (`0144A1`–`0144A4`); 0144A brief Successor →
  `0144A1`; `0144B` Predecessor → `0144A4`.

### Pre-existing governance debt remediated (discovered this session)

Amendment #33's mechanical execution (WP-036 S4) left `validate_session_plan`
/ `validate_baseline` red on `main` (7 errors): `tools/wp001_baseline.py`
still modelled the pre-#33 `0144A`–`0144H` block (WP-036B/C), the four
WP-036A briefs `0144A`–`0144D` carried a stray leading `---` before their
`# Session` heading, and `0144E` / `0145` predecessor links still pointed at
the pre-#33 targets. Fixed as part of amendment #34's mechanical execution
(same pattern amendment #33 itself used): `_SUBSESSION_BLOCKS` /
`_SEQUENCE_RE` / `_PLANNED_SESSION_COUNT` updated for #31/#33/#34; the four
brief headings stripped; `0144E` predecessor → `0144D`; `0145` predecessor →
`0144L`; the `DOCS/sessions/README.md` "5 sub-sessions `0141A`–`0141E`"
miscount corrected to 6. `tests/test_wp001_baseline.py` count literals
(212/211/213) updated to 220/219/221. `validate_session_plan(ROOT) == []`
and `validate_baseline(ROOT) == []` both green; full
`tests/test_wp001_baseline.py` + `tests/test_check_dv_register_gates.py`
green (66 passed).

## Next step

Execute `0144A1` at §4 of the decomposition plan. Each sub-pass commits at
its own green local gate; the contiguous `0144A`+`0144A1`–`0144A4` range
feeds the single S2 audit `0144B` and is pushed once with it (amendment #28
cadence). S1 may not self-certify.

## 0144A1 — Inhibition and sparsification family (COMPLETE 2026-08-30)

### Delivered symbol map

| Row | Symbol | Rust owner | PyO3 / Python delegation | Verification |
|---:|---|---|---|---|
| 31 | `FeedforwardInhibition` | `prin_train::inhibition_layers::FeedforwardInhibition` | `FeedforwardInhibitionBridge` → `prin.nn.inhibition_layers` | direct PRINet parity; float64 input gradcheck; vector/batch/error tests |
| 32 | `DentateGyrusConverter` | `prin_train::inhibition_layers::DentateGyrusConverter` composing `inhibition::FeedbackInhibition` | `DentateGyrusConverterBridge` → `prin.nn.inhibition_layers` | FFI→EMA→FBI parity; top-k invariant; stationary-point gradcheck; error tests |
| 33 | `DGLayer` | `prin_train::inhibition_layers::DgLayer` (`ffi_scale`, `fbi_temperature` Rust-owned) | `DGLayerBridge` → `prin.nn.inhibition_layers.DGLayer` | direct parity; stationary-point gradcheck; nonzero Rust autodiff to both inputs and both parameters; checkpoint round-trip |
| 34 | `oscillatory_weight_init` | `prin_train::weight_init` | `OscillatoryWeightInitBridge` → Python name/parameter orchestration only | symmetric/scale/zero-diagonal reference case; deterministic Xavier bound; zero bias |
| 38 | `SparsityRegularizationLoss` | `prin_train::losses::SparsityRegularizationLoss` | `SparsityRegularizationLossBridge` → `prin.nn.inhibition_layers` | direct parity; DV-018 float64 gradcheck (`eps=1e-4`); validation tests |

`python/prin/nn/deferred_layers.py` now compatibility-re-exports these five
real symbols; the other WP-036A rows remain typed D-2.2 stubs for their assigned
sub-passes. No public symbol was added:
`verify_api_surface(prin.__all__) == (set(), set())`.

### Numerical / parity evidence

- Direct installed-PRINet comparisons in `tests/test_inhibition_layers.py`:
  maximum absolute delta FFI `3.33e-16`, DG converter `1.67e-16`, DGLayer
  `1.39e-16` (`rtol=1e-10, atol=1e-12`).
- `SparsityRegularizationLoss` maximum absolute delta `1.19e-9`; its
  `rtol=1e-6, atol=1e-8` parity tier and `eps=1e-4` gradcheck are the existing
  Burn sigmoid DV-018 disposition, recorded at the test and in
  `DOCS/sphinx/parity_report.rst`.
- FBI is a deliberate hard-forward / soft-backward STE, not the Jacobian of a
  globally smooth function. DG/DGLayer finite-difference gradchecks therefore
  use the FFI stationary point `phase=pi`, where analytical and numerical
  Jacobians coincide. Away from that point, Rust autodiff tests independently
  prove finite nonzero flow to phase, amplitude, `ffi_scale`, and
  `fbi_temperature`; no STE assertion was weakened or misrepresented.

### Coverage and quality evidence

- Python targeted: 17 passed; `prin.nn.inhibition_layers` 95 statements,
  2 missed, **97.89%**.
- Rust `cargo llvm-cov -p prin-train --lib`: 389 passed;
  `inhibition_layers.rs` **97.05% lines / 100.00% functions**,
  `weight_init.rs` **100.00% lines / 100.00% functions**, extended `losses.rs`
  **95.79% lines**; crate total 96.40% lines.
- Full fast Python suite after migration-table regeneration: **1227 passed**,
  9 slow/GPU tests deselected, 99% package coverage.
- Migration Guide: all five rows and the machine-generated consolidated index
  report real WP-036A delegation; `wp036_migration_table.py check` reports 172
  symbols consistent.
- `maturin develop -m crates/prin-py/Cargo.toml` succeeded on Windows / Python
  3.14 / Rust 1.92; imports and DLPack execution verified.

### Security evidence

- Snyk Code, severity threshold **low**, scoped to modified `prin-train`,
  `prin-py`, `python/prin/nn`, the new test, and
  `tools/check_no_python_numerics.py`: **0 issues in every scope**.
- Whole-repository Snyk Code: 5 pre-existing low path-traversal findings in
  `tools/wp001_baseline.py`, `tools/wp030_mot_fixture.py`, and
  `tools/wp031_stats_fixture.py`; none arises from 0144A1. No suppression or
  exclusion added.
- No dependency manifest changed; Snyk Open Source is therefore not applicable.
  Native `cargo audit` exits 0 with the same three governed warnings
  (`paste`, `bincode`, `chacha20`); both `pip-audit` scopes report no known
  vulnerabilities. Active-source Bandit (`python/prin tools`) reports 0 issues.
  The broader `bandit -r .` observes two pre-existing low `assert` findings in
  a manual `EVIDENCE/math-audit` verification script (0 medium/high); the
  immutable evidence artifact was not changed.
- `prin-py` remains `#![deny(unsafe_code)]`; all DLPack FFI stays in the audited
  module.

### Inherited gate remediation

The full Ruff gate exposed two pre-existing `RUF003` en-dashes in comments
introduced by the immediately preceding amendment-#34
`tools/wp001_baseline.py` change. They were changed to ASCII hyphens only; no
logic changed. This is recorded rather than silently attributed to 0144A1.

### Handoff

Sub-pass 0144A1 is complete to the author's knowledge and does not self-certify
WP-036A. Proceed to 0144A2; the complete `0144A` + `0144A1`–`0144A4` range
remains subject to the single mandatory S2 audit at 0144B.

## 0144A2 — Phase-to-rate and autoencoder family (COMPLETE 2026-08-30)

### Delivered symbol map

| Row | Symbol | Rust owner | PyO3 / Python delegation | Verification |
|---:|---|---|---|---|
| 35 | `PhaseToRateConverter` | `prin_train::autoencoders::PhaseToRateConverter` (Rust-owned learnable `temperature`) | `PhaseToRateConverterBridge` → `prin.nn.autoencoders` | direct PRINet parity (soft/hard/annealed); float64 soft gradcheck; hard STE gradient-shape test; vector/error/checkpoint tests |
| 36 | `PhaseToRateAutoencoder` | `prin_train::autoencoders::PhaseToRateAutoencoder` (Rust-owned `Linear` stacks + `PhaseToRateConverter` bottleneck + classifier head) | `PhaseToRateAutoencoderBridge` (`forward` → `(recon, rates)`, `classify`) → `prin.nn.autoencoders` | weight-injected PRINet parity for `forward` + `classify`; float64 gradcheck of `forward`/`classify` wrt input; construction/error/checkpoint tests |
| 37 | `DenseAutoencoder` | `prin_train::autoencoders::DenseAutoencoder` (Rust-owned dense-MLP encoder/decoder + classifier head) | `DenseAutoencoderBridge` (`forward` → `(recon, codes)`, `classify`) → `prin.nn.autoencoders` | weight-injected PRINet parity; float64 gradcheck wrt input; construction/error/checkpoint tests |

`python/prin/nn/deferred_layers.py` now compatibility-re-exports these three
real symbols from `prin.nn.autoencoders`; `prin.nn.__init__` imports them from
the real module directly. No public symbol was added:
`verify_api_surface(prin.__all__) == (set(), set())`.

### New Rust: `crates/prin-train/src/autoencoders.rs`

- `phase_to_rate` — Burn autodiff port of PRINet 3.0's
  `core.propagation.phase_to_rate`. `soft` (softmax) is fully differentiable;
  `hard` is `rate * top_k_mask` (mask from `topk`'s non-differentiable
  indices, forward-identical to `zeros.scatter_(topk_idx, topk_vals)`);
  `annealed` blends with `blend = sigmoid(1/max(T, 1e-6) - 1)` computed from
  the (detached) temperature value, matching the reference's `.item()`.
- `PhaseToRateConverter` — `Module` with a Rust-owned `Param<Tensor<B, 1>>`
  temperature. **Documented deviation (D-3 superset):** the reference detaches
  the temperature with `.item()`; PRIN keeps it live so the softmax gradient
  reaches it. Forward-identical.
- `PhaseToRateAutoencoder` / `DenseAutoencoder` — `Module`s composing
  `burn::nn::Linear` stacks (`relu` / `softplus` / `log_softmax`), the
  converter bottleneck (row 36 only), and a classifier head.
  `*Config::init` draws Xavier-uniform `Linear` weights from the project
  `Seed` (documented deviation from PyTorch's default Kaiming init — only the
  scale is load-bearing, the `ResonanceLayer` precedent);
  `*Config::init_from_params` / `LinearWeights` inject the reference model's
  exact weights (PyTorch `[out, in]` layout transposed to Burn `[in, out]`)
  for the forward-parity tests.
- 20 `#[cfg(test)]` unit + autodiff tests. `prin-train` lib: 389 → 409 passed.

### New PyO3: `crates/prin-py/src/bindings/train_autoencoders.rs`

Three `#[pyclass]` bridges + five `*Ctx` recompute-on-backward contexts, all
thin DLPack marshalling over `prin-train`. `#![deny(unsafe_code)]` unchanged;
all DLPack FFI stays in the audited `dlpack` module. `load_torch_weights`
accepts a flat capsule list for the parity tests; `state_dict` /
`load_state_dict` delegate to `burn::record`.

### Numerical / parity evidence

Direct installed-PRINet float64 comparisons in `tests/test_autoencoders.py`
(measured maximum absolute deltas on the registered deterministic cases):

- `PhaseToRateConverter` `soft` / `hard` / `annealed`:
  `2.8e-17` / `0.0` / `2.8e-17` (`rtol=1e-9`; `hard` `rtol=1e-12`).
- `PhaseToRateAutoencoder` reconstruction / rates / `classify`:
  `1.1e-16` / `5.6e-17` / `4.4e-16` (`rtol=1e-9, atol<=1e-11`).
- `DenseAutoencoder` reconstruction / codes / `classify`:
  `1.1e-16` / `1.7e-16` / `4.4e-16` (`rtol=1e-9, atol<=1e-11`).

No hazard tolerance is invoked: `phase_to_rate`'s softmax and the
`softplus`/`relu`/`log_softmax`/`Linear` ops are `burn-tensor` elementwise/
reduction ops and do not hit the DV-018 `f32`-internal `sigmoid` floor. The
`annealed` blend at the default unit temperature is exactly `0.5` in both
float32 and float64; a non-unit fixed temperature would surface a `~1e-7`
float32 artifact governed by the D-4 mechanism (recorded in
`DOCS/sphinx/parity_report.rst`, "WP-036A — Phase-to-rate and autoencoder
parity").

### Gradient evidence

- `soft` mode: `torch.autograd.gradcheck` at `eps=1e-6, rtol=1e-3, atol=1e-3`
  (float64) passes w.r.t. phase and amplitude.
- `PhaseToRateAutoencoder` / `DenseAutoencoder`: `gradcheck` of `forward` and
  `classify` w.r.t. the input at the same tolerance.
- `hard` mode: a straight-through estimator over a discrete top-`k` selection
  is not the Jacobian of one smooth function, so it gets a
  gradient-shape/finiteness assertion (Python) plus an independent Rust
  autodiff test (`phase_to_rate_hard_ste_gradient_has_input_shape`), never a
  weakened `gradcheck`.

### Coverage and quality evidence

- Rust: `cargo test -p prin-train -p prin-py` green (409 lib + integration +
  13 doctests; no failures). `cargo fmt --all --check`, `cargo clippy
  --workspace --all-targets -D warnings`, `RUSTDOCFLAGS=-D warnings cargo doc`
  all clean.
- Python: `tests/test_autoencoders.py` 14 passed; full fast suite **1218
  passed**, 32 deselected. `ruff check` / `ruff format --check` /
  `mypy --strict` (autoencoders.py, deferred_layers.py, nn/__init__.py) /
  `interrogate -f 100` (autoencoders.py 100%) / active-source `bandit` all
  clean. `tools/check_no_python_numerics.py` green (15 modules;
  `nn/autoencoders.py` added to `_SCANNED` + `_RUST_BRIDGE_MODULES`).
  `wp036_migration_table.py check` green (172 symbols consistent);
  `tests/test_migration_guide_consolidated.py` + `tests/test_wp001_baseline.py`
  + `tests/test_check_dv_register_gates.py` + `tests/test_api_surface.py` (88
  passed).
- `maturin develop -m crates/prin-py/Cargo.toml` succeeded on Windows /
  Python 3.14 / Rust 1.92; imports and DLPack execution verified.
- **Line-coverage tooling blocked locally:** `pytest --cov` / `coverage run`
  segfault on this host (Python 3.14 + `coverage` C/sysmon tracer + torch),
  reproducibly and identically for the pre-existing `tests/test_inhibition_layers.py`
  — not a regression from this sub-pass. Per CLAUDE.md this is reported as
  blocked, not claimed passed; CI is the authoritative coverage gate. Manual
  review: every public function, property, and error branch of
  `prin.nn.autoencoders` is exercised by a test.

### Security evidence

- Snyk Code, severity threshold **low**, scoped to `crates/prin-train/src/autoencoders.rs`,
  `crates/prin-py/src/bindings/train_autoencoders.rs`,
  `python/prin/nn/autoencoders.py`, `tests/test_autoencoders.py`: **0 issues**.
  Whole-repository Snyk Code: the same 5 pre-existing low path-traversal
  findings in `tools/wp001_baseline.py` / `tools/wp030_mot_fixture.py` /
  `tools/wp031_stats_fixture.py`; none arises from 0144A2. No suppression added.
- No dependency manifest changed, so Snyk Open Source is not applicable.
  `cargo audit` exits 0 with the same three governed warnings (`paste`,
  `bincode`, `chacha20`). `pip-audit` reports only pre-existing `pip`-tool
  advisories (environment, not a PRIN manifest change).
- `prin-py` remains `#![deny(unsafe_code)]`; all DLPack FFI stays in the
  audited module.

### Handoff

Sub-pass 0144A2 is complete to the author's knowledge and does not
self-certify WP-036A. Proceed to 0144A3 (hierarchical / PAC / discrete-layer
family, rows 39/40/44 — pre-authorised to split `0144A3a`/`0144A3b`). The
complete `0144A` + `0144A1`–`0144A4` range remains subject to the single
mandatory S2 audit at 0144B.

## 0144A3 — Hierarchical, PAC, and discrete-layer family (COMPLETE 2026-08-31)

### Delivered symbol map

| Row | Symbol | Rust owner | Bridge / Python owner | Acceptance evidence |
|---:|---|---|---|---|
| 39 | `HierarchicalResonanceLayer` | `prin_train::hierarchical_layers::HierarchicalResonanceLayer` plus fully batched continuous three-band RK4/PAC dynamics | `HierarchicalResonanceLayerBridge` → `prin.nn.hierarchical_layers` | weight-injected PRINet amplitude/phase parity; float64 dual-output gradcheck; D-5 batch/vector equivalence; checkpoint/error tests |
| 40 | `PhaseAmplitudeCouplingLayer` | `prin_train::hierarchical_layers::PhaseAmplitudeCouplingLayer` | `PhaseAmplitudeCouplingLayerBridge` → `prin.nn.hierarchical_layers` | installed-PRINet parity; float64 two-input gradcheck; checkpoint/error tests |
| 44 | `DiscreteDeltaThetaGammaLayer` | `prin_train::hierarchical_layers::DiscreteDeltaThetaGammaLayer` over `prin_train::bands::DiscreteDeltaThetaGamma` | `DiscreteDeltaThetaGammaLayerBridge` → `prin.nn.hierarchical_layers` | all-weight-injected PRINet parity; float64 gradcheck; checkpoint/error tests |

`python/prin/nn/deferred_layers.py` compatibility-re-exports all three real
symbols; `prin.nn.__init__` imports them from the implementation module. No
public symbol was added: `verify_api_surface(prin.__all__) == (set(), set())`.

### Numerical, gradient, and design evidence

- Continuous hierarchical amplitude and wrapped phase match the installed
  float64 reference at `rtol=1e-9, atol=1e-11` after exact projection/PAC
  parameter injection.
- PAC matches at `rtol=1e-8, atol=1e-9`; PRINet stores `initial_depth` as
  float32 before `.double()`, producing the documented approximately `6e-9`
  scalar discrepancy.
- Discrete-layer parity uses DV-018 `rtol=2e-7, atol=2e-8`; Burn 0.16.1's
  f32-internal sigmoid produces a measured three-step maximum relative delta
  of `1.39e-7`.
- All three float64 `torch.autograd.gradcheck` calls pass at
  `rtol=1e-3, atol=1e-3`; row 39 includes amplitude and phase cotangents, and
  row 44 uses `eps=1e-5` solely to rise above the DV-018 finite-difference
  floor.
- D-5: row 39 evaluates `(batch, n_dims)` in one Burn graph with no per-sample
  loop. It matches stacking independent vector calls at
  `rtol=1e-12, atol=1e-12`, while preserving vector-in/vector-out behavior.

### Coverage and quality evidence

- Rust: `cargo fmt --all -- --check`, workspace clippy `-D warnings`, workspace
  tests, and `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` are
  green. `prin-train` has 426 passing lib tests plus integration/doctests;
  `cargo llvm-cov -p prin-train --lib` reports 99.79% line coverage for
  `hierarchical_layers.rs`.
- Python: 12 targeted layer tests pass; the full fast suite reports **1253
  passed, 9 deselected** and 99% package line coverage. Ruff check/format,
  `mypy --strict`, interrogate (97.4%), full Bandit, no-Python-numerics (16
  modules), and the 172-symbol migration-table check are green.
- `maturin develop -m crates/prin-py/Cargo.toml` succeeded on Windows / Python
  3.14 / Rust 1.92. A clean-output Sphinx `-W --keep-going` build succeeded.
- The full Bandit gate initially exposed two pre-existing B101 findings in
  `EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`; explicit
  failure branches replaced optimization-sensitive assertions. The script and
  full Bandit scan then passed without findings.

### Security evidence

- Snyk Code at severity **low** reports zero findings in the changed Rust,
  Python, test, migration-tool, and M-F9 files. Whole-repository Snyk Code
  retains the same five pre-existing low path-traversal findings in
  `tools/wp001_baseline.py`, `tools/wp030_mot_fixture.py`, and
  `tools/wp031_stats_fixture.py`; none arises from 0144A3.
- No dependency manifest changed, so Snyk Open Source is not applicable.
  `cargo audit` exits 0 with the three governed warnings (`bincode`, `paste`,
  `chacha20`). Both project and Sphinx-requirement `pip-audit` scans report no
  known vulnerabilities.
- `prin-py` remains `#![deny(unsafe_code)]`; all DLPack FFI remains in the
  audited shared module.

### Handoff

Sub-pass 0144A3 is complete to the author's knowledge and does not self-certify
WP-036A. Proceed to 0144A4 (model container and consolidation). The complete
`0144A` + `0144A1`–`0144A4` range remains subject to the single mandatory S2
audit at 0144B.

## 0144A4 — Model container and consolidation (COMPLETE 2026-08-31)

### Delivered symbol map

| Row | Symbol | Rust owner | Bridge / Python owner | Acceptance evidence |
|---:|---|---|---|---|
| 41 | `PRINetModel` | `prin_train::model::PRINetModel` (input `layers::ResonanceLayer` + `n_layers-1` stacked + per-layer `burn::nn::LayerNorm` + concept-readout `burn::nn::Linear` + `[-50, 50]` logit clamp + `log_softmax`) | `PRINetModelBridge` → `prin.nn.model.PRINetModel` | float64 `gradcheck` (`n_layers` 1 and 2); zero-input parity vs the reference float64 readout reproduction (delta `0.0`) and vs the reference's real float32 `forward` (delta `0.0`, D-4 tier); readout-head golden test; batched==stacked-singles; checkpoint round-trip / malformed-bytes / shape-mismatch; construction/error tests |
| 42 | `compile_model` | *(none — D-2; the one WP-036A symbol with no Rust component)* | pure-Python guarded `torch.compile` passthrough in `prin.nn.model` | construct/callable + `torch.compile` smoke test; guard-branch test (`torch.compile` removed → model returned unchanged); no `# pragma: no cover` |

`python/prin/nn/deferred_layers.py` now compatibility-re-exports `PRINetModel`
and `compile_model` from `prin.nn.model`; `prin.nn.__init__` imports them from
the implementation module directly. The only symbols still resolving from
`deferred_layers` as typed D-2.2 stubs are `DiscreteDeltaThetaGamma`
(core binding, WP-036B) and the `prin.training_hooks` trio
(`MixedPrecisionTrainer` / `AsyncCPUGPUPipeline` / `retrain_controller`). No
public symbol was added: `verify_api_surface(prin.__all__) == (set(), set())`.

### New Rust: `crates/prin-train/src/model.rs`

`PRINetModelConfig` (validated `new` / `with_params`), `PRINetModelParams<B>`
(`input_layer` + `stacked` + `layer_norms` + `concept_proj` for reference
injection), `PRINetModel<B>` (`#[derive(Module)]`), `LayerNormWeights<B>`.
`init` draws the concept-readout `Linear` Xavier-uniform from the project
`Seed` (documented deviation from PyTorch's Kaiming default — only scale is
load-bearing, the `ResonanceLayer` precedent); `LayerNorm` starts at
`γ=1, β=0` (identical in both). `forward` is a line-for-line port of
`PRINetModel.forward` minus the reference's `h.float()` cast (see below).
`validate_shapes` checks the stacked-layer count, every `LayerNorm` width, and
the readout shape after `load_record`. 14 `#[cfg(test)]` unit/autodiff tests;
`prin-train` lib 426 → 440 passing.

### New PyO3: `crates/prin-py/src/bindings/train_model.rs`

One `#[pyclass] PyPRINetModelBridge` + `PyPRINetModelCtx` recompute-on-backward
context, thin DLPack marshalling over `prin-train`. `load_torch_weights`
accepts a flat list of `7 * n_layers + 2` capsules (5 per resonance layer, 2
per `LayerNorm`, 2 for the readout); `input_proj` is transposed from PyTorch
`[n_osc, n_dims]` to Burn `[n_dims, n_osc]` on the way in. `state_dict` /
`load_state_dict` delegate to `burn::record`; `load_state_dict` validates
shapes on a clone before committing (WP025-F1 precedent).
`#![deny(unsafe_code)]` unchanged; all DLPack FFI stays in the audited `dlpack`
module.

### Documented deviation — the reference's broken float64 forward

PRINet 3.0's `PRINetModel.forward` unconditionally runs `h = h.float()` before
the readout; on a `.double()` model the float64 `concept_proj` weights then
raise `RuntimeError: mat1 and mat2 must have the same dtype`, so **no float64
end-to-end reference output exists** (`test_reference_forward_raises_in_float64_but_prin_does_not`
records this directly). PRIN runs the whole forward in the backend dtype with
no internal cast. Forward-parity is established two ways at a zero input — the
regime where the composed `ResonanceLayer` initial-state encoding coincides
exactly with the reference — with the reference model's exact weights injected:

- vs a float64 reproduction of the documented forward on the reference's own
  (working-in-f64) submodules: measured max abs delta `0.0`
  (`rtol=1e-9, atol=1e-11`).
- vs the reference's real float32 `forward`: measured max abs delta `0.0`,
  D-4 envelope `rtol=1e-4, atol=1e-5` (the only disagreement source in that
  regime is the f32/f64 hazard).

`PRINetModel` composes the audited `ResonanceLayer` unchanged and inherits its
FFT-vs-matmul feature-to-oscillator encoding deviation (plan amendment #19).
For an arbitrary non-zero input the end-to-end log-probability delta grows to
order 1 (measured `0.99` on a small registered case), bounded by — not newly
introduced by — that inherited deviation. The readout head `PRINetModel` adds
(`LayerNorm` + `concept_proj` + clamp + `log_softmax`) is checked in isolation
against a hand-computed `log_softmax(clamp(h @ Wᵀ + b))` (`< 1e-12`, Rust).
Recorded in `DOCS/sphinx/parity_report.rst` ("WP-036A — Model container
parity") and the Migration Guide.

### Gradient evidence

`torch.autograd.gradcheck` (float64) passes at the required
`rtol=1e-3, atol=1e-3` for `n_layers = 1` and `n_layers = 2`. No DV-018
tolerance is invoked: the added head is `LayerNorm` / `Linear` / `clamp` /
`log_softmax`, all `burn-tensor` elementwise/reduction ops, none touching the
`f32`-internal `sigmoid` floor. Rust autodiff tests independently confirm
finite non-zero gradient flow to the model input, `concept_proj` weight/bias,
and both `LayerNorm` affines. `compile_model` performs no numerics, so it has
a construct/callable + `torch.compile` smoke test and a guard-branch test
instead of a gradcheck.

### Consolidation deliverables

- **Migration Guide** (`DOCS/sphinx/migration_guide.rst`): all 13 D-D rows now
  read "real implementation" with the `prin.nn.<module>` delegation path
  (0141B deferred-rebuild table, 0141E dispositions table, deviation-notes
  bullets, and the machine-generated consolidated 172-symbol index). No silent
  removals: `python tools/wp036_migration_table.py check` →
  "WP-036 consolidated migration table OK (172 symbols)".
- **`tools/check_no_python_numerics.py`**: `nn/model.py` added to `_SCANNED`
  (16 → 17 modules) and `_RUST_BRIDGE_MODULES`; check green.
- **`verify_api_surface(prin.__all__) == (set(), set())`** re-confirmed (WP-036A
  adds no public symbols; `tests/test_model.py::test_reexports_are_real_and_public_surface_remains_frozen`
  and `tests/test_api_surface.py`).
- **Full construct/callable smoke** over all 13 symbols: every one resolves
  from `prin` and `prin.nn` as a real (non-stub) implementation, verified this
  session and by `tests/test_api_surface_matrix.py` (433 passed across the
  consolidation suites).
- **`_prin_core.pyi`**: `PRINetModelBridge` / `PRINetModelCtx` stubs added;
  `mypy --strict` clean on `nn/model.py`, `nn/deferred_layers.py`,
  `nn/__init__.py` (the 0141E stub-completeness check).

### 13-symbol aggregate map (0144A1–0144A4)

| Row | Symbol | Rust owner module | PyO3 binding | Sub-pass | gradcheck / verification |
|---:|---|---|---|---|---|
| 31 | `FeedforwardInhibition` | `inhibition_layers` | `train_inhibition_layers` | 0144A1 | float64 input gradcheck; direct PRINet parity `3.33e-16` |
| 32 | `DentateGyrusConverter` | `inhibition_layers` (composes `inhibition::FeedbackInhibition`) | `train_inhibition_layers` | 0144A1 | stationary-point gradcheck (FBI STE); parity `1.67e-16` |
| 33 | `DGLayer` | `inhibition_layers` | `train_inhibition_layers` | 0144A1 | stationary-point gradcheck; Rust autodiff to both inputs + both params; parity `1.39e-16` |
| 34 | `oscillatory_weight_init` | `weight_init` | `train_inhibition_layers` (in-place param transform) | 0144A1 | deterministic reference-scheme unit test |
| 35 | `PhaseToRateConverter` | `autoencoders` | `train_autoencoders` | 0144A2 | float64 `soft` gradcheck; `hard` STE gradient-shape test; parity `soft/hard/annealed` `2.8e-17 / 0.0 / 2.8e-17` |
| 36 | `PhaseToRateAutoencoder` | `autoencoders` | `train_autoencoders` | 0144A2 | float64 `forward`/`classify` gradcheck wrt input; weight-injected parity `≤4.4e-16` |
| 37 | `DenseAutoencoder` | `autoencoders` | `train_autoencoders` | 0144A2 | float64 `forward`/`classify` gradcheck; weight-injected parity `≤4.4e-16` |
| 38 | `SparsityRegularizationLoss` | `losses` | `train_inhibition_layers` | 0144A1 | DV-018 float64 gradcheck (`eps=1e-4`); parity `1.19e-9` (`rtol=1e-6`) |
| 39 | `HierarchicalResonanceLayer` | `hierarchical_layers` (batched continuous 3-band RK4/PAC) | `train_hierarchical_layers` | 0144A3 | float64 dual-output gradcheck; weight-injected parity `rtol=1e-9`; D-5 batch==stacked `rtol=1e-12` |
| 40 | `PhaseAmplitudeCouplingLayer` | `hierarchical_layers` | `train_hierarchical_layers` | 0144A3 | float64 two-input gradcheck; parity `rtol=1e-8` (`~6e-9` f32-stored `initial_depth`) |
| 41 | `PRINetModel` | `model` (over `layers::ResonanceLayer`) | `train_model` | 0144A4 | float64 gradcheck (`n_layers` 1, 2); zero-input parity delta `0.0` (f64 readout and f32 forward); head golden test `<1e-12` |
| 42 | `compile_model` | *(none — D-2)* | *(none)* | 0144A4 | construct/callable + `torch.compile` smoke; guard-branch test; no `# pragma: no cover` |
| 44 | `DiscreteDeltaThetaGammaLayer` | `hierarchical_layers` (over `bands::DiscreteDeltaThetaGamma`, WP-022) | `train_hierarchical_layers` | 0144A3 | float64 gradcheck (`eps=1e-5`, DV-018); all-weight-injected parity `rtol=2e-7` (DV-018) |

### 0144A acceptance-criterion → evidence (aggregate)

| 0144A brief criterion | Evidence |
|---|---|
| All 13 symbols resolve from `prin` as **real** (not stubs) | This-session smoke + `tests/test_api_surface_matrix.py`; `deferred_layers` re-exports the real modules; only `DiscreteDeltaThetaGamma` (row 43, WP-036B) + the training-hook trio remain typed stubs |
| Each trainable module passes float64 `gradcheck(rtol=1e-3, atol=1e-3)` | 11 trainable modules gradchecked in `tests/test_{inhibition_layers,autoencoders,hierarchical_layers,model}.py`; FBI-STE modules use the FFI stationary point + independent Rust autodiff (documented, not weakened); `hard` mode uses an STE gradient-shape test (D-3) |
| Forward pass matches the PRINet 3.0 reference within documented tolerance | Direct installed-PRINet float64 comparisons per family (`parity_report.rst` "WP-036A — …" sections); D-4 loosenings recorded per test, none deleted/skipped; `PRINetModel`'s reference `forward` is broken in f64, handled per the deviation note above |
| `compile_model` constructs a `PRINetModel` and returns a callable model | `tests/test_model.py::test_compile_model_returns_a_callable_wrapper` (constructs a `PRINetModel`, wraps it, asserts callable + output parity) + the guard-branch test |
| `oscillatory_weight_init` applies the documented scheme to a parameter tensor | `tests/test_inhibition_layers.py` (0144A1); `weight_init.rs` 100% line/function coverage |
| All new Rust in `crates/prin-train/`; all new PyO3 in `crates/prin-py/src/bindings/` | `inhibition_layers.rs`, `weight_init.rs`, `losses.rs` (extended), `autoencoders.rs`, `hierarchical_layers.rs`, `model.rs`; bindings `train_inhibition_layers.rs`, `train_autoencoders.rs`, `train_hierarchical_layers.rs`, `train_model.rs` |
| No Python numerics (Coding Standards §2.1) | `tools/check_no_python_numerics.py` green (17 modules) |
| `verify_api_surface(prin.__all__) == (set(), set())` | Re-confirmed every sub-pass; `tests/test_api_surface.py` + each family's re-export test |
| `tools/check_no_python_numerics.py` clean (updated module count) | 13 → 14 → 15 → 16 → 17 modules across 0141E → 0144A1 → 0144A2 → 0144A3 → 0144A4 |
| Migration Guide updated for all 13 symbols | `wp036_migration_table.py check` green (172 symbols consistent); `tests/test_migration_guide_consolidated.py` |
| S1 handoff note maps each symbol → owner / binding / test count / gradcheck | This document (per-sub-pass sections + the 13-symbol aggregate map above) |
| `mypy --strict` clean; `_prin_core.pyi` completeness (0141E check) | clean on every touched module each sub-pass |
| Rust + Python gates green across `0144A1`–`0144A4` | see the gate table below |

### Coverage and quality evidence

- **Rust:** `cargo fmt --all -- --check`, `cargo clippy --workspace
  --all-targets -D warnings`, `cargo test -p prin-train -p prin-py`
  (440 `prin-train` lib + integration + doctests; `prin-py` integration all
  green), `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` — all
  clean. `model.rs` new tests: 14 `#[cfg(test)]`.
- **Python:** `tests/test_model.py` 13 passed; full fast suite
  **1266 passed, 9 deselected** (was 1253 at 0144A3). `ruff check` /
  `ruff format --check` / `mypy --strict` (`nn/model.py`,
  `nn/deferred_layers.py`, `nn/__init__.py`) / `interrogate -f 100`
  (`model.py` 100%) / active-source `bandit` (`python/prin tools`, 0 issues) /
  `check_no_python_numerics` (17 modules) / `wp036_migration_table.py check`
  (172 symbols) / `test_migration_guide_consolidated` + `test_api_surface` +
  `test_api_surface_matrix` + `test_wp001_baseline` +
  `test_check_dv_register_gates` (433 passed) — all green.
  `pytest --doctest-modules python/prin/nn/model.py` 2 passed.
  Clean-output Sphinx `-W --keep-going` build succeeded.
- **Line-coverage tooling blocked locally:** `pytest --cov` / `coverage run`
  segfault on this host (Python 3.14 + `coverage` C/sysmon tracer + torch),
  reproducibly and unrelated to this sub-pass. Per CLAUDE.md this is reported
  as blocked, not claimed passed; CI is the authoritative coverage gate.
  Manual review: every public function, property, and error branch of
  `prin.nn.model` is exercised; every `#[cfg(test)]` path in `model.rs` and
  `train_model.rs`'s bridge/ctx methods is exercised via the Rust and Python
  suites (including `load_torch_weights`, `state_dict`/`load_state_dict`, the
  shape-mismatch and malformed-bytes branches, and the `compile_model` guard
  branch).
- `maturin develop -m crates/prin-py/Cargo.toml` succeeded on Windows /
  Python 3.14 / Rust 1.92; imports and DLPack execution verified.

### Security evidence

- Snyk Code, severity threshold **low**, scoped to
  `crates/prin-train/src/model.rs`,
  `crates/prin-py/src/bindings/train_model.rs`, `python/prin/nn/model.py`,
  `python/prin/nn/deferred_layers.py`, `tests/test_model.py`,
  `tools/wp036_migration_table.py`, `tools/check_no_python_numerics.py`:
  **0 issues in every scope**. Whole-repository Snyk Code: the same 5
  pre-existing low path-traversal findings in `tools/wp001_baseline.py`,
  `tools/wp030_mot_fixture.py`, `tools/wp031_stats_fixture.py`; none arises
  from 0144A4. No suppression or exclusion added.
- **No dependency manifest changed** (`burn::nn::LayerNorm` is already a
  workspace dependency), so Snyk Open Source is not applicable. `cargo audit`
  exits 0 with the same three governed warnings (`paste`, `bincode`,
  `chacha20`). `pip-audit` reports only pre-existing `pip`-tool advisories
  (environment, not a PRIN manifest change).
- `prin-py` remains `#![deny(unsafe_code)]`; all DLPack FFI stays in the
  audited `dlpack` module. No hidden RNG (the concept-readout `Linear` init is
  threaded through the explicit project `Seed`).

### Handoff

Sub-pass 0144A4 is complete to the author's knowledge and **does not
self-certify WP-036A**. The 13 D-D trainable-layer / discrete-network symbols
(rows 31–42, 44) are all real `prin-train`-backed implementations across
`0144A1`–`0144A4`. The complete `0144A` + `0144A1`–`0144A4` range is committed
locally only and is handed to the single mandatory S2 audit **`0144B`**; the
contiguous range is pushed once with `0144B` (amendment #28 cadence).

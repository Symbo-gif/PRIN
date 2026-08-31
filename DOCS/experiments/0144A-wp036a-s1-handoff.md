# Session 0144A / WP-036A S1 running handoff

**Date:** 2026-08-30
**Status:** decomposition **ADOPTED** (Plan amendment #34, MichaelMaillet,
2026-08-30). WP-036A S1 now executes as sub-passes `0144A1`–`0144A4`.
Sub-pass execution not yet started.

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

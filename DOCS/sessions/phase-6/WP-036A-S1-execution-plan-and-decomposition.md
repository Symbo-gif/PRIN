# WP-036A S1 (session 0144A) — execution plan and decomposition proposal

**Status:** DRAFT — PENDING MAINTAINER APPROVAL (prepared 2026-08-30 at
session 0144A start). Proposed for adoption as **Plan amendment #34**. Not
itself an execution contract; the governing contract remains the 0144A brief
and amendment #33. **Until this is approved, no WP-036A code is written.**

**Prepared for:** session 0144A (WP-036A S1 — trainable compatibility layers,
`prin-train` extension).
**Author:** Claude Sonnet 5 (AI pair).
**Date:** 2026-08-30.
**Authority:** Project Plan §6/§8 and amendment #33; Development Workflow and
Audit Standards §7 ("An S1 session that grows beyond its WP declaration must
stop and either split the WP (new declaration) or descope. Auditors treat
scope creep as D3."); Coding Standards §1.2 / §2.1 (no Python numerics),
§2 (Rust standards), §3.2 (batched boundary crossings); Testing Standards §1.

---

## 1. Why this document exists

Amendment #33 (2026-08-29) declared **WP-036A** — a faithful `prin-train`
rebuild of the 13 trainable-layer / discrete-network compatibility symbols
that the WP-036 S1 0141E finalisation shipped as importable D-2.2 stubs
(D-D appendix rows 31–42, 44). It assigned WP-036A a normal S1–S4 cycle
across sessions `0144A`–`0144D`.

Repository verification at session 0144A start (commands and results in §2)
shows that **WP-036A S1 as a single session exceeds one reviewable commit
range**, for the same structural reason amendment #32 split WP-036 S1 into
`0141A`–`0141E`:

- The 13 symbols are **13 new trainable Burn modules** (`Config`/`Params`/
  `State` contracts, autodiff forward + closed-form or autodiff backward),
  not thin bindings over audited owners. Sub-pass 0141B — *bindings only*
  over already-audited WP-022/023 Rust — was itself one of five sub-passes.
- **Five of the primitives these layers compose have no trainable (Burn)
  owner today.** The continuous three-band `DeltaThetaGammaNetwork`, the
  `PhaseAmplitudeCoupling` modulation, `phase_to_rate`, the feedforward
  inhibition gate, and the DG EMA-integration stage exist only as
  non-autodiff `prin-dynamics` / `prin-sim` code or as PRINet 3.0 Python
  reference. WP-036A must port them to Burn before the layers that use them
  can be built and gradchecked.
- Each symbol additionally needs a PyO3 `autograd.Function` bridge
  (`crates/prin-py/src/bindings/`), a Python `nn.Module` delegating to the
  bridge (`python/prin/nn/`), a `_prin_core.pyi` update, a float64
  `torch.autograd.gradcheck`, a PRINet-3.0 forward-parity test, and
  construction/error-path tests, all at ≥95% coverage — plus one maturin
  rebuild per sub-pass.

Estimated first-party delta: **~3,500–4,500 lines of new Rust**, **~1,200–1,600
lines of PyO3 bridges**, **~600–900 lines of Python**, **~2,000–2,800 lines of
tests**. Every prior Phase 3–6 S1 delivered on the order of 300–1,500 source
lines. Delivered as one session this forces either scope creep past any
auditable commit range (D3 by Development Workflow §7) or deferred tests /
weakened coverage / weakened gradcheck tolerances (all explicitly prohibited
by the 0144A brief "Prohibited" list and Testing Standards §1).

The established remedy (amendments #20, #31, #32) is: verify scope, propose a
dependency-ordered decomposition, obtain maintainer approval, record an
amendment, then execute. This is that proposal.

---

## 2. Scope inventory (repository-verified, 2026-08-30, `main` @ `237f21a`)

### 2.1 Verification commands

```
cargo --version                     # cargo 1.92.0
python --version                    # Python 3.14.0
python -c "import torch; print(torch.__version__)"   # 2.13.0+cpu
python -c "import prin.nn.deferred_layers as m; print(len(m.__all__))"   # 14 (13 in scope + DiscreteDeltaThetaGamma row 43, WP-036B)
ls crates/prin-train/src/           # bands, layers, inhibition, activations, energy, hep, ... (NO hierarchical/model/autoencoder/ffi module)
grep -rl "DeltaThetaGammaNetwork\|PhaseAmplitudeCoupling\|phase_to_rate" crates/*/src/
#   → crates/prin-dynamics/src/{bands,pac}.rs, crates/prin-sim/..., crates/prin-py/... — NONE in crates/prin-train/
```

### 2.2 The 13 symbols — per-symbol Rust-owner status and work type

| Row | Symbol | Kind | Trainable Rust owner today | New Burn numerics needed | Size |
|---:|---|---|---|---|---|
| 31 | `FeedforwardInhibition` | parameter-free gate | none (`prinet.core.propagation.inhibition` reference only) | FFI phase-delay / exp-decay gate | S |
| 32 | `DentateGyrusConverter` | pipeline (FFI→EMA→FBI) | FBI stage only (`prin_train::inhibition::FeedbackInhibition`) | FFI gate + EMA integration stage | M |
| 33 | `DGLayer` | trainable `nn.Module` | none | wrapper + learnable `ffi_scale` / `fbi_temperature` | S–M |
| 34 | `oscillatory_weight_init` | init function | none | symmetric-coupling / Xavier-adapted init over a param tensor | S |
| 35 | `PhaseToRateConverter` | trainable `nn.Module` | none (`phase_to_rate` is `prin-sim`, non-autodiff) | Burn autodiff `phase_to_rate` (soft) + learnable temperature | M |
| 36 | `PhaseToRateAutoencoder` | trainable `nn.Module` | none | encoder/decoder Linear stacks + PhaseToRate bottleneck + classifier head | M |
| 37 | `DenseAutoencoder` | trainable `nn.Module` (baseline) | none | Linear-MLP encoder/decoder + classifier head | S |
| 38 | `SparsityRegularizationLoss` | loss `nn.Module` | none | sigmoid-surrogate L0 density penalty | S |
| 39 | `HierarchicalResonanceLayer` | trainable `nn.Module` | none (`DeltaThetaGammaNetwork` is `prin-dynamics`, non-autodiff) | **Burn port of the continuous 3-band network** + learnable per-band projections + learnable PAC depths | **L** |
| 40 | `PhaseAmplitudeCouplingLayer` | trainable `nn.Module` | none (`PhaseAmplitudeCoupling` is `prin-dynamics`, non-autodiff) | Burn PAC `modulate` + learnable `modulation_depth` | S–M |
| 41 | `PRINetModel` | full model container | `prin_train::layers::ResonanceLayer` (input + stacked) | LayerNorm-between-layers + concept readout + clamped log-softmax over the existing `ResonanceLayer` | M–L |
| 42 | `compile_model` | compilation helper | n/a | **none** — pure-Python `torch.compile` passthrough (reference is a 3-line passthrough; `torch.compile` is not PRIN numerics) | XS |
| 44 | `DiscreteDeltaThetaGammaLayer` | trainable `nn.Module` | `prin_train::bands::DiscreteDeltaThetaGamma` (WP-022, audited) | new `proj_phase` / `proj_amplitude` Linear projections over the existing batched discrete core | M |

`S` ≈ ≤250 Rust LoC, `M` ≈ 250–500, `L` ≈ 500–900. Totals: 1 XS, 5 S/S–M,
5 M/M–L, 2 L.

### 2.3 Established patterns each symbol must follow

- **Rust:** `crates/prin-train/src/*.rs` — `*Config` (validated `new` /
  `with_params`), `*Params<B>`, `*State<B>` where stateful, `init` /
  `init_from_params`, `step` / `integrate` / `forward`, `#[cfg(test)]` with
  `Autodiff<NdArray<f64>>` gradient tests. Batched `[batch, n]` tensors, no
  per-sample loop (as `bands.rs` already does; the PRINet 3.0
  `HierarchicalResonanceLayer` per-sample Python loop is **not** reproduced —
  see D-5).
- **PyO3 bridge:** `crates/prin-py/src/bindings/*.rs` — `#[pyclass] *Bridge`
  owns the Burn `Module`; `forward` runs the whole pass in one boundary
  crossing and returns `(*output_capsules, ctx)`; `*Ctx.backward(*grad)`
  rebuilds `require_grad` leaves from saved plain values, re-runs forward,
  seeds `(output · grad_output).sum().backward()` (the VJP trick
  `gradcheck` needs). `#![deny(unsafe_code)]` unchanged; all DLPack FFI via
  the audited `dlpack` module.
- **Python:** `python/prin/nn/*.py` — `torch.nn.Module` (or `autograd.Function`
  + `Module`) delegating to the `_prin_core` bridge; **all parameters
  Rust-owned** (the `HybridPRINetV2` / `ResonanceLayer` training-ownership
  split). Replaces the `deferred_layers.py` stub. `.pyi` updated.
- **Tests:** float64 `gradcheck(rtol=1e-3, atol=1e-3)` for every trainable
  module (DV-018 `eps`/tolerance where a Burn `sigmoid`/`tanh` f32 internal
  floor applies, documented at the call site); PRINet-3.0 forward-parity
  within documented tolerance; construction + error-path; `compile_model`
  integration. ≥95% coverage on new/changed code.

### 2.4 Non-symbol deliverables

- Migration Guide (`DOCS/sphinx/migration_guide.rst`): 13 per-symbol rows
  move from "deferred rebuild / D-2.2 stub" to "real implementation" with the
  new `prin.nn.<module>` delegation path.
- `tools/check_no_python_numerics.py`: updated allowed-module count.
- `verify_api_surface(prin.__all__) == (set(), set())` **stays** — the 13
  symbols already resolve and are already in `prin.__all__` /
  `RC1_PUBLIC_API` (0141E). WP-036A adds **no** public symbols (0144A brief
  non-goal); it replaces stub bodies.
- `_prin_core.pyi` completeness (1,539 entries today; every new bridge adds
  rows) — checked under `mypy --strict` + the 0141E stub-completeness check.
- S1 handoff note: each symbol → Rust owner module, binding, test count,
  gradcheck result (0144A brief "Required evidence" item 8).

---

## 3. Decisions required from the maintainer

### D-1 — Decomposition mechanism

| | Mechanism | Register impact | Recommendation |
|---|---|---|---|
| **M1** | **Four sequential S1 coding sub-passes `0144A1`–`0144A4`** (dependency-ordered; §4), each committing at its own green local gate, all feeding the single S2 audit `0144B`; the contiguous `0144A`+`0144A1`–`0144A4` range pushed once with `0144B` (amendment #28 cadence). `0144A3` pre-authorised to split `0144A3a`/`0144A3b` under the same §7 rule (as `0141D`→`0141D1`/`0141D2` did). | phase-6 README / `SESSION_REGISTER.md` / `TRACEABILITY.md` gain 4 (≤5) additive sub-rows under the amendment-#31/#32 convention; `0144B`'s predecessor becomes `0144A4`. Planned count 216 → 220 (221 if `0144A3` splits). | **Recommended** — smallest deviation, identical in kind to amendment #32, one S2 over one contiguous range. |
| M2 | Re-split WP-036A into WP-036A / WP-036A2, each a full S1–S4 mini-cycle. | second Audit Report + PSR; heavier register churn. | Only if an independent audit of the "new primitives" work separate from the "layers" work is wanted. Not recommended. |
| M3 | Keep 0144A as one session; grind. | none | **Rejected — Development Workflow §7.** |

### D-2 — `compile_model` disposition (row 42)

`compile_model` in PRINet 3.0 is `return torch.compile(model, mode=mode)` with
a `hasattr` guard. It performs no PRIN numerics. **Proposal:** deliver it as a
**real pure-Python passthrough** in `python/prin/nn/` (guarded `torch.compile`
wrapper), the one WP-036A symbol with no Rust component, exercised by a
construct/callable + `torch.compile` smoke test. Confirm this is acceptable
and not required to be a Rust no-op.

### D-3 — `phase_to_rate` differentiability (rows 35, 36)

The reference `PhaseToRateConverter` supports `soft` (softmax — differentiable),
`hard` (top-k — non-differentiable in the reference too), and `annealed`
(temperature interpolation). **Proposal:** the Burn port makes `soft` fully
autodiff and gradchecked; `hard` uses a straight-through estimator matching the
reference's non-differentiable selection; `annealed` interpolates
soft↔hard. float64 gradcheck runs on `soft` (and the `annealed` soft-dominated
regime); `hard` gets a forward-parity + STE-gradient-shape test only.
Confirm.

### D-4 — Forward-parity tolerance governance

PRIN's f64 Burn core vs the PRINet 3.0 f32/`torch` reference (preserved
hazards, amendments #14/#16/#17/#25) and Burn 0.16.1's f32-internal `sigmoid`
(DV-018) mean a fraction of forward-parity assertions will not match
byte-for-byte under documented-tolerance comparison. **Proposal:** reuse the
D-A parity-tolerance mechanism — per-test tolerance annotation + a Parity
Report / PSR-036A entry for each loosening, never a deleted or skipped
assertion. Confirm (this mirrors amendment #31 D-A for WP-036B/C).

### D-5 — `HierarchicalResonanceLayer` batched vs per-sample (row 39)

The reference runs a Python `for b in range(B)` loop over a non-batched
`DeltaThetaGammaNetwork`. PRIN's Burn port will be **fully batched**
(`[batch, n_total]`), like `bands::DiscreteDeltaThetaGamma` already is —
numerically equivalent, no hidden RNG, faster. **Proposal:** record this as a
documented D3 "better design" Migration-Guide note, not a blocker. Confirm.

---

## 4. Proposed decomposition (assumes M1)

Dependency order: primitives before the layers that compose them; the model
container and the pure-Python helper last; consolidation closes the surface.
Each sub-pass: code + tests in tandem, local gate green (`cargo fmt`, clippy
`-D warnings`, `cargo nextest` / doctests where Rust changed, rustdoc; `ruff`,
`ruff format`, `mypy --strict`, `interrogate` 100% public, `bandit`, `pytest`;
`cargo audit`, `pip-audit`; Snyk Code on modified first-party source, Snyk
Open Source if a manifest changes), ≥95% coverage on new/changed code,
maturin rebuild, **commit locally only**.

### 0144A1 — Inhibition & sparsification family (rows 31, 32, 33, 34, 38)

- **Rust** `crates/prin-train/src/inhibition_layers.rs` (new):
  `FeedforwardInhibition` (parameter-free phase-delay / exp-decay gate),
  `DentateGyrusConverter` (FFI → EMA integration → `FeedbackInhibition` FBI
  pipeline, composing the existing `inhibition::FeedbackInhibition`),
  `DgLayer` (learnable `ffi_scale` / `fbi_temperature`).
  `crates/prin-train/src/weight_init.rs` (new): `oscillatory_weight_init`
  scheme over a parameter tensor. Extend `losses.rs`:
  `SparsityRegularizationLoss` (sigmoid-surrogate density penalty).
- **PyO3** `crates/prin-py/src/bindings/train_inhibition_layers.rs` (new):
  5 bridges (`FeedforwardInhibition` parameter-free; `DentateGyrusConverter`,
  `DgLayer`, `SparsityRegularizationLoss` differentiable;
  `oscillatory_weight_init` an in-place param transform).
- **Python:** replace the 5 stubs (new `python/prin/nn/inhibition_layers.py`
  or extend `inhibition.py`); update `deferred_layers.py` re-exports and
  `.pyi`.
- **Tests:** gradcheck `DgLayer` / `DentateGyrusConverter` /
  `SparsityRegularizationLoss` (and FFI wrt inputs); forward parity vs
  `prinet.core.propagation.inhibition` + `prinet.nn.layers`; init-scheme
  unit test; error paths.

### 0144A2 — Phase-to-rate & autoencoder family (rows 35, 36, 37)

- **Rust** `crates/prin-train/src/autoencoders.rs` (new): Burn autodiff
  `phase_to_rate` (soft; STE `hard`; `annealed`), `PhaseToRateConverter`
  (learnable temperature), `PhaseToRateAutoencoder` (encoder/decoder Linear
  stacks + PhaseToRate bottleneck + classifier head), `DenseAutoencoder`
  (Linear-MLP baseline + classifier head).
- **PyO3** `crates/prin-py/src/bindings/train_autoencoders.rs` (new): 3
  bridges.
- **Python:** replace 3 stubs (`python/prin/nn/autoencoders.py` new);
  `.pyi`.
- **Tests:** gradcheck all 3; forward parity vs `prinet.nn.layers`; WTA-mode
  behaviour (D-3); `classify()` path; error paths.

### 0144A3 — Hierarchical / PAC / discrete-layer family (rows 39, 40, 44)

*Pre-authorised to split `0144A3a` (row 39, the continuous band-network port
— the single largest item) / `0144A3b` (rows 40, 44) under Development
Workflow §7, flagged now so S2 is not surprised.*

- **Rust** `crates/prin-train/src/hierarchical_layers.rs` (new): a batched
  Burn port of the continuous three-band delta/theta/gamma network (3-band
  Kuramoto phase coupling + Stuart–Landau amplitude + delta→theta, theta→gamma
  PAC), `HierarchicalResonanceLayer` (learnable `proj_delta`/`proj_theta`/
  `proj_gamma` + learnable `pac_depth_dt`/`pac_depth_tg`, D-5 batched),
  `PhaseAmplitudeCouplingLayer` (Burn PAC `modulate` + learnable
  `modulation_depth`), `DiscreteDeltaThetaGammaLayer` (new `proj_phase` /
  `proj_amplitude` over the existing `bands::DiscreteDeltaThetaGamma`).
- **PyO3** `crates/prin-py/src/bindings/train_hierarchical_layers.rs` (new):
  3 bridges.
- **Python:** replace 3 stubs; `.pyi`.
- **Tests:** gradcheck all 3 (`return_phase` path for row 39); forward
  parity vs `prinet.nn.layers` within D-4 tolerance; error paths.

### 0144A4 — Model container + consolidation (rows 41, 42)

- **Rust** `crates/prin-train/src/model.rs` (new): `PRINetModel` — input
  `ResonanceLayer` + `n_layers-1` stacked `ResonanceLayer` +
  LayerNorm-between-layers + concept readout + clamped log-softmax, over the
  existing `layers::ResonanceLayer`.
- **PyO3** `crates/prin-py/src/bindings/train_model.rs` (new): 1 bridge.
- **Python:** replace `PRINetModel` stub (Rust-backed) and `compile_model`
  stub (pure-Python `torch.compile` passthrough, D-2); `.pyi`.
- **Consolidation:** Migration Guide 13 rows → "real implementation";
  `tools/check_no_python_numerics.py` module count; full gradcheck matrix
  table; `verify_api_surface(prin.__all__) == (set(), set())` re-confirmed;
  full construct/callable smoke over all 13; **S1 handoff note** (each
  symbol → owner / binding / test count / gradcheck result).
- **Tests:** gradcheck `PRINetModel`; `compile_model` integration (constructs
  a `PRINetModel` from a config dict, returns a callable); forward parity vs
  `prinet.nn.layers.PRINetModel`.

---

## 5. Proposed Plan amendment #34 — draft text

> **#34 | 2026-08-30 | Project Plan §6 / WP-036A S1 (session 0144A) /
> Development Workflow and Audit Standards §7 / `DOCS/sessions/SESSION_REGISTER.md` |**
> **WP-036A S1 executed as four sequential S1 coding sub-passes
> `0144A1`–`0144A4`** rather than one session, because repository
> verification at S1 start
> (`DOCS/sessions/phase-6/WP-036A-S1-execution-plan-and-decomposition.md`,
> adopted this date) shows the 13 trainable-layer symbols (D-D appendix rows
> 31–42, 44) are 13 new trainable Burn modules — not thin bindings — and that
> five of the primitives they compose (continuous `DeltaThetaGammaNetwork`,
> `PhaseAmplitudeCoupling`, `phase_to_rate`, the FFI gate, the DG
> EMA-integration stage) have no trainable Rust owner and must be ported to
> Burn first; with per-symbol PyO3 `autograd.Function` bridges, Python
> `nn.Module`s, `_prin_core.pyi` updates, float64 gradcheck, PRINet-3.0
> forward-parity tests, and ≥95% coverage plus a maturin rebuild, this exceeds
> one reviewable commit range (D3 by Development Workflow §7; deferred tests /
> weakened coverage / weakened gradcheck tolerances prohibited by the 0144A
> brief and Testing Standards §1). **Decomposition (option M1):** `0144A1` —
> inhibition & sparsification family (`FeedforwardInhibition`,
> `DentateGyrusConverter`, `DGLayer`, `oscillatory_weight_init`,
> `SparsityRegularizationLoss`); `0144A2` — phase-to-rate & autoencoder family
> (`PhaseToRateConverter`, `PhaseToRateAutoencoder`, `DenseAutoencoder`);
> `0144A3` — hierarchical / PAC / discrete-layer family
> (`HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`,
> `DiscreteDeltaThetaGammaLayer`; pre-authorised to split
> `0144A3a`/`0144A3b`); `0144A4` — `PRINetModel` + `compile_model` +
> consolidation (Migration Guide 13 rows, `check_no_python_numerics` count,
> full gradcheck matrix, S1 handoff note). Each sub-pass commits at its own
> green local gate with ≥95% coverage on new/changed code; the contiguous
> `0144A`+`0144A1`–`0144A4` range feeds the single S2 audit `0144B` and is
> pushed once with it (amendment #28 cadence). **Strategic dispositions:**
> (D-2) `compile_model` is delivered as a real pure-Python `torch.compile`
> passthrough (no PRIN numerics; the one symbol with no Rust component).
> (D-3) `phase_to_rate` `soft` mode is fully autodiff and gradchecked; `hard`
> is a straight-through estimator matching the reference's non-differentiable
> selection; `annealed` interpolates. (D-4) forward-parity assertions that
> fail byte-for-byte solely due to the documented f32/f64 hazard or Burn's
> f32-internal `sigmoid` (DV-018) are governed by the D-A parity-tolerance
> mechanism — per-test annotation + Parity Report / PSR entry, never deletion
> or skip. (D-5) `HierarchicalResonanceLayer` is implemented fully batched
> (the reference's per-sample Python loop is not reproduced) — a documented
> D3 "better design" Migration-Guide note. The `0144A1`–`0144A4` identifiers
> follow the amendment-#31/#32 additive-sub-session register convention and do
> **not** renumber the 0001–0198 integer sequence or the `0144E`–`0144L`
> block (`0144B`'s predecessor becomes `0144A4`; TRACEABILITY invariant 4
> preserved). Planned session count: 216 → 220 (221 if `0144A3` splits).
> WP-036A's acceptance criteria and non-goals (0144A brief) are unchanged.
> Same disposition class as amendment #32 (S1 decomposition) and #20 (scope
> decomposition). | maintainer approval (pending) |

---

## 6. Risks

- **R1 — Continuous band-network Burn port (row 39).** The single largest
  new-numerics item; no existing Burn owner; the reference composes
  `DeltaThetaGammaNetwork` + `OscillatorState` + per-sample loop. Mitigation:
  `0144A3` isolated and pre-authorised to split `0144A3a`/`0144A3b`; the
  discrete analogue (`bands::DiscreteDeltaThetaGamma`) is an audited reference
  for the batched-Kuramoto + Stuart–Landau + PAC structure.
- **R2 — gradcheck breadth.** 11 trainable modules need float64 gradcheck;
  Burn 0.16.1's f32-internal `sigmoid`/`tanh` (DV-018) touches
  `SparsityRegularizationLoss`, `PhaseToRateConverter` (softmax temperature),
  the FFI exp-decay gate, and `DgLayer.fbi_temperature`. Mitigation: the
  DV-018 `eps`/tolerance precedent, documented at each call site (as
  `train_layers.rs` already does for `d_silu`/`phase_activation`).
- **R3 — `phase_to_rate` autodiff (D-3).** `hard`/`annealed` are not cleanly
  differentiable. Mitigation: D-3 disposition (STE for `hard`, gradcheck on
  `soft`).
- **R4 — maturin rebuild on this host** (Windows / Python 3.14 / Rust 1.92).
  Mitigation: proven working through 0141B–0141E; if the toolchain blocks a
  sub-pass it is reported as blocked per CLAUDE.md, not worked around.
- **R5 — coverage on `compile_model` / thin Python.** Mitigation:
  `# pragma: no cover` is not permitted; `compile_model` is exercised by a
  construct/callable + `torch.compile` smoke test.
- **R6 — `_prin_core.pyi` drift.** ~13 new bridge classes + their `*Ctx`.
  Mitigation: `mypy --strict` + the 0141E stub-completeness check per
  sub-pass.
- **R7 — WP-036B S1 (`0144E`) is gated on WP-036A closing.** Amendment #33
  sequences WP-036A before WP-036B ports `test_hierarchical` /
  `test_phase_to_rate` / `test_q2` / `test_q2_remaining` / `test_q3_new` /
  `test_nn` / `test_hybrid`. The decomposition adds 4 sub-passes to WP-036A
  S1 but does not change the S1–S4 count or the WP-036A-before-WP-036B
  ordering; the contiguous range still feeds one S2 (`0144B`).

---

## 7. Recommendation

Approve **M1** (sub-passes `0144A1`–`0144A4` feeding the single S2 audit
`0144B`, `0144A3` pre-authorised to split), **D-2** (`compile_model` =
real pure-Python passthrough), **D-3** (`phase_to_rate` soft gradchecked /
hard STE), **D-4** (D-A parity-tolerance governance for forward-parity
deltas), and **D-5** (`HierarchicalResonanceLayer` batched, documented D3).
Record **Plan amendment #34**. Then execute `0144A1` at §4.

Until then, no WP-036A code is written.

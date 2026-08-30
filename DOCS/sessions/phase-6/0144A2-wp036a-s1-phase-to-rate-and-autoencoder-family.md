# Session 0144A2 — WP-036A S1 (sub-pass 2/4): Phase-to-rate and autoencoder family

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S1 — Coding
**Predecessor:** [0144A1 — inhibition and sparsification family](0144A1-wp036a-s1-inhibition-and-sparsification-family.md)
**Successor:** [0144A3 — hierarchical, PAC, and discrete-layer family](0144A3-wp036a-s1-hierarchical-pac-and-discrete-layer-family.md)
**Authority:** Project Plan §6/§8, amendments #33/#34, the decomposition plan
[`WP-036A-S1-execution-plan-and-decomposition.md`](WP-036A-S1-execution-plan-and-decomposition.md).
Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Replace 3 of the 13 D-2.2 stubs with real `prin-train` Rust implementations +
PyO3 bridges + Python `nn.Module`s:

| Row | Symbol | Nature |
|---:|---|---|
| 35 | `PhaseToRateConverter` | trainable `nn.Module`: phase/amplitude → sparse rate codes, learnable temperature |
| 36 | `PhaseToRateAutoencoder` | encoder/decoder + PhaseToRate bottleneck + classifier head |
| 37 | `DenseAutoencoder` | non-oscillatory dense-MLP baseline autoencoder + classifier head |

## Contract

- **Acceptance:**
  - New Rust `crates/prin-train/src/autoencoders.rs`: a Burn-autodiff
    `phase_to_rate` (`soft` fully differentiable; `hard` a straight-through
    estimator matching the reference's non-differentiable top-k; `annealed`
    interpolates — **D-3**), `PhaseToRateConverter` (learnable temperature),
    `PhaseToRateAutoencoder`, `DenseAutoencoder`. No Python numerics.
  - New PyO3 bridges (thin marshalling; unsafe-free; audited DLPack).
  - The 3 symbols resolve from `prin` / `prin.nn` as real implementations.
  - float64 `gradcheck(rtol=1e-3, atol=1e-3)` passes for all 3 in the
    differentiable regime (`soft`; `annealed` soft-dominated). `hard` gets a
    forward-parity + STE-gradient-shape test. DV-018 tolerance where the Burn
    f32 `sigmoid`/softmax floor applies, documented at the call site.
  - Forward-pass parity vs `prinet.nn.layers` within documented tolerance
    (D-4). `classify()` path covered.
  - `_prin_core.pyi` + `.pyi` updated; `mypy --strict` clean.
  - Rust gates green (`fmt`, clippy `-D warnings`, tests, rustdoc).
  - `verify_api_surface(prin.__all__) == (set(), set())` unchanged.
  - Migration Guide rows for the 3 symbols → "real implementation".
- **Non-goals:** the other 10 symbols; acceptance-suite port; GPU/CUDA.

## Required reading

- The 0144A brief, the decomposition plan, the 0144A1 sub-pass handoff
- `crates/prin-py/src/bindings/sweep.rs` (`phase_to_rate` non-autodiff owner),
  `crates/prin-sim/` phase-to-rate reference, `prinet/nn/layers.py`
- `crates/prin-train/src/{layers.rs,activations.rs}` for autodiff patterns
- `DOCS/standards/Coding_Standards.md` §2.1/§2/§6; `Testing_Standards.md` §1/§4
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-018;
  `DOCS/sphinx/parity_report.rst`; latest PSR and deviation ledger

## Entry conditions

- 0144A1 committed at its green local gate; no unresolved D1/D2.
- maturin builds on this host; else reported blocked per CLAUDE.md.

## Expected work

1. Rust + autodiff gradient tests in tandem.
2. PyO3 bridges; `maturin develop`; verify import.
3. Replace the Python stubs; record module placement.
4. gradcheck + WTA-mode + parity + construction/error tests; ≥95% coverage.
5. `.pyi`; full local gate; Snyk Code / Open Source / `cargo audit` /
   `pip-audit` as applicable.
6. Append a sub-pass handoff note.

## Prohibited

Deferred tests, weakened assertions/tolerances, Python or `prin-py` numerics,
undocumented public API, hidden RNG, unapproved `unsafe`, scope creep,
unregistered experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0144A3.

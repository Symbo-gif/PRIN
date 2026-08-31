# Session 0144A2 — WP-036A S1 (sub-pass 2/4): Phase-to-rate and autoencoder family

**Status:** COMPLETE (2026-08-30)
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

## Completion evidence (2026-08-30)

- Rust owner: `crates/prin-train/src/autoencoders.rs` — Burn-autodiff
  `phase_to_rate` (`soft` differentiable, `hard` straight-through over the
  reference top-`k` selection, `annealed` interpolating — D-3),
  `PhaseToRateConverter` (Rust-owned learnable temperature, a documented
  forward-identical superset of the reference's detached `.item()` — D-3),
  `PhaseToRateAutoencoder`, and `DenseAutoencoder` (Rust-owned `burn::nn::Linear`
  stacks + classifier heads). No Python numerics.
- PyO3: `crates/prin-py/src/bindings/train_autoencoders.rs` — three DLPack
  bridges + five recompute-on-backward `*Ctx` classes; `#![deny(unsafe_code)]`
  unchanged.
- Python: `prin.nn.autoencoders` replaces the three D-2.2 stubs;
  `prin.nn.deferred_layers` retains compatibility re-exports.
  `verify_api_surface(prin.__all__) == (set(), set())`.
- Tests: 14 Python parity/gradcheck/API/error tests + 20 Rust unit/autodiff
  tests. Maximum absolute PRINet float64 parity deltas: converter
  `soft`/`hard`/`annealed` `2.8e-17`/`0.0`/`2.8e-17`;
  `PhaseToRateAutoencoder` recon/rates/classify `1.1e-16`/`5.6e-17`/`4.4e-16`;
  `DenseAutoencoder` recon/codes/classify `1.1e-16`/`1.7e-16`/`4.4e-16`. No
  hazard tolerance invoked. `soft` gradcheck at `rtol=1e-3, atol=1e-3`
  (float64) passes.
- Gates: `cargo fmt`/`clippy -D warnings`/tests/rustdoc green; `ruff`,
  `ruff format`, `mypy --strict`, `interrogate` 100%, `bandit`, full fast
  `pytest` (1218 passed), `wp036_migration_table check`, and the WP-001/DV
  regression suites all green. `maturin develop` succeeded (Windows / Python
  3.14 / Rust 1.92). Snyk Code: 0 issues in the changed scope (5 pre-existing
  low findings elsewhere, none from this sub-pass). No manifest changed —
  Snyk Open Source not applicable; `cargo audit` 3 governed warnings only.
  Line-coverage tooling segfaults on this host (pre-existing, reproduces on
  `test_inhibition_layers.py`) — reported blocked per CLAUDE.md, CI authoritative.
- Migration Guide, `DOCS/sphinx/parity_report.rst`, and
  `DOCS/experiments/0144A-wp036a-s1-handoff.md` updated with the 0144A2
  disposition, deviations, and evidence.

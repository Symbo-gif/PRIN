# Session 0144A1 — WP-036A S1 (sub-pass 1/4): Inhibition and sparsification family

**Status:** COMPLETE (2026-08-30)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S1 — Coding
**Predecessor:** [0144A — Coding (decomposed)](0144A-wp036a-s1-trainable-compatibility-layers-prin-train-extension.md)
**Successor:** [0144A2 — phase-to-rate and autoencoder family](0144A2-wp036a-s1-phase-to-rate-and-autoencoder-family.md)
**Authority:** Project Plan §6/§8, amendments #33/#34, the decomposition plan
[`WP-036A-S1-execution-plan-and-decomposition.md`](WP-036A-S1-execution-plan-and-decomposition.md).
Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Replace 5 of the 13 D-2.2 stubs in `prin.nn.deferred_layers` with real
`prin-train` Rust implementations + PyO3 bridges + Python `nn.Module`s:

| Row | Symbol | Nature |
|---:|---|---|
| 31 | `FeedforwardInhibition` | parameter-free phase-delay / exp-decay gate |
| 32 | `DentateGyrusConverter` | FFI → EMA integration → FBI sparsification pipeline |
| 33 | `DGLayer` | trainable `nn.Module` over `DentateGyrusConverter` (learnable `ffi_scale`, `fbi_temperature`) |
| 34 | `oscillatory_weight_init` | weight-initialisation scheme over a parameter tensor |
| 38 | `SparsityRegularizationLoss` | sigmoid-surrogate L0 density-penalty loss `nn.Module` |

## Contract

- **Acceptance:**
  - New Rust in `crates/prin-train/src/` (`inhibition_layers.rs`,
    `weight_init.rs`; extend `losses.rs`) following the existing
    `Config`/`Params`/`State` + `Module` patterns. `DentateGyrusConverter`
    composes the existing `inhibition::FeedbackInhibition` for its FBI stage.
    No Python numerics (Coding Standards §2.1).
  - New PyO3 bridges in `crates/prin-py/src/bindings/` (thin marshalling;
    `#![deny(unsafe_code)]` unchanged; DLPack FFI via the audited `dlpack`
    module).
  - The 5 symbols resolve from `prin` / `prin.nn` as **real** implementations
    (not stubs); the `deferred_layers.py` stub bodies are replaced (or the
    symbols move to a real module with `deferred_layers` re-exporting).
  - `torch.autograd.gradcheck` at `rtol=1e-3, atol=1e-3` (float64) passes for
    every trainable module (`DGLayer`, `DentateGyrusConverter`,
    `SparsityRegularizationLoss`; `FeedforwardInhibition` gradcheck w.r.t.
    inputs). DV-018 `eps`/tolerance where a Burn f32-internal
    `sigmoid`/`exp` floor applies, documented at the call site.
  - Forward-pass parity vs `prinet.core.propagation.inhibition` and
    `prinet.nn.layers` within documented tolerance (D-4 parity-tolerance
    governance for f32/f64-attributable deltas).
  - `oscillatory_weight_init` applies the documented scheme (symmetric
    coupling, zero diagonal, Xavier-adapted projections, zero bias) to a
    parameter tensor; unit-tested against the reference.
  - `_prin_core.pyi` + `prin` `.pyi` stubs updated; `mypy --strict` clean.
  - Rust gates green: `cargo fmt --check`, `cargo clippy --workspace
    --all-targets -D warnings`, `cargo test --workspace` (or `cargo nextest`),
    rustdoc.
  - `verify_api_surface(prin.__all__) == (set(), set())` unchanged (no new
    public symbols).
  - Migration Guide rows for the 5 symbols move "deferred rebuild / D-2.2
    stub" → "real implementation" with the delegation path.
- **Non-goals:** the other 8 symbols (`0144A2`–`0144A4`); `DiscreteDeltaThetaGamma`
  core binding (row 43, WP-036B S1 / `0144E`); acceptance-suite test porting;
  GPU/CUDA.

## Required reading

- The 0144A brief and the decomposition plan
- `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` rows 31–44 and
  `DOCS/experiments/0144A-wp036a-s1-handoff.md`
- `crates/prin-train/src/{inhibition.rs,layers.rs,bands.rs,losses.rs}` for
  patterns; the WP-023 audit's exclusion of FFI/DG
- `crates/prin-py/src/bindings/{train.rs,train_layers.rs,train_support.rs}`
- `crates/prin-dynamics/src/` and
  `DOCS/archive and reference from PRINet 3.0/.../core/propagation/inhibition.py`,
  `.../nn/layers.py`
- `DOCS/standards/Coding_Standards.md` §2.1/§2/§6; `Testing_Standards.md` §1/§4
- `DOCS/sphinx/parity_report.rst`; latest PSR and cumulative deviation ledger

## Entry conditions

- 0144A decomposition plan adopted (amendment #34); no unresolved D1/D2.
- The maturin toolchain builds on this host (Windows / Python 3.14 / Rust
  1.92); if not, the pass is reported blocked per CLAUDE.md, not worked around.

## Expected work

1. Rust implementations + `#[cfg(test)]` autodiff gradient tests in tandem.
2. PyO3 bridges; `maturin develop -m crates/prin-py/Cargo.toml`; verify import.
3. Replace the Python stubs; decide/record module placement.
4. float64 gradcheck + forward-parity + construction/error-path tests;
   ≥95% coverage on new/changed code.
5. Update `.pyi`; run the full local gate (Rust + Python).
6. Snyk Code on modified first-party Rust/Python; Snyk Open Source +
   `cargo audit` + `pip-audit` if any manifest changes.
7. Append a sub-pass handoff note to `DOCS/experiments/0144A-wp036a-s1-handoff.md`.

## Prohibited

Deferred tests, weakened assertions/tolerances, Python or `prin-py` numerics,
undocumented public API, hidden RNG, unapproved `unsafe`, scope creep into
`0144A2`–`0144A4`, unregistered experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0144A2.

## Completion evidence (2026-08-30)

- Rust owners: `prin_train::inhibition_layers` implements FFI, DG conversion,
  and `DgLayer`; `prin_train::weight_init` implements deterministic coupling /
  Xavier / bias initialization; `prin_train::losses` owns the sigmoid-surrogate
  sparsity loss.
- PyO3: `bindings::train_inhibition_layers` provides four differentiable
  DLPack bridges plus the weight-initialization bridge, with no new `unsafe`.
- Python: `prin.nn.inhibition_layers` replaces all five D-2.2 stubs while
  `prin.nn.deferred_layers` retains compatibility re-exports.
- Tests: 13 Python parity/gradcheck/API/error tests and Rust unit/autodiff tests;
  changed-code coverage is 97.89% Python, 97.05% / 100% Rust lines for
  `inhibition_layers.rs` / `weight_init.rs`, and 95.79% for `losses.rs`.
- Numerical evidence: FFI/DG/DGLayer maximum absolute parity deltas are
  `3.33e-16` / `1.67e-16` / `1.39e-16`; sigmoid-loss delta is `1.19e-9`
  under the governed DV-018 tolerance. The FBI STE gradcheck stationary-point
  disposition is recorded in `DOCS/sphinx/parity_report.rst`.
- Detailed acceptance mapping and validation evidence are appended to
  `DOCS/experiments/0144A-wp036a-s1-handoff.md` under **0144A1**.

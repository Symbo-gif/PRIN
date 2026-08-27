# Session 0141B — WP-036 S1 (sub-pass 2/5): prin-tensor and prin-train Python bindings

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141A — freeze machinery and re-export surface](0141A-wp036-s1a-freeze-machinery-and-reexport-surface.md)
**Successor:** [0141C — kernels bindings and DV-012](0141C-wp036-s1c-kernels-bindings-and-dv012.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md). Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Expose the already-implemented `prin-tensor` (WP-014) and `prin-train`
(WP-022/023) numerics to Python as thin PyO3 bindings + `prin` wrapper surface,
covering Bucket D (`PolyadicTensor`, `CPDecomposition`) and Bucket E (~18:
`FeedforwardInhibition`, `FeedbackInhibition`, `DentateGyrusConverter`,
`DGLayer`, `HolomorphicEnergy`, `HolomorphicEPTrainer`, `HolomorphicActivation`,
`PhaseActivation`, `dSiLU`, `oscillatory_weight_init`, `PhaseToRateConverter`,
`PhaseToRateAutoencoder`, `DenseAutoencoder`, `SparsityRegularizationLoss`,
`HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`, `PRINetModel`,
`compile_model`).

## Contract

- **Acceptance:**
  - New PyO3 bindings in `crates/prin-py/src/bindings/` over the existing
    `prin-tensor` and `prin-train` owners; **no numerics added in Python or in
    `prin-py`** (thin marshalling only).
  - Every covered symbol resolves from `prin` and passes a construct/callable
    smoke check; each is added to the appropriate submodule `__all__` and to
    `prin.__all__`.
  - Every trainable binding exposed as a `torch.autograd.Function` has a
    float64 `torch.autograd.gradcheck` test that passes.
  - `_prin_core.pyi` and the `prin` `.pyi` stubs updated; `mypy --strict` clean.
  - Rust gates green: `cargo fmt --check`, `cargo clippy --workspace
    --all-targets -D warnings`, `cargo test --workspace`, rustdoc.
  - Parity-evidence disposition (Development Workflow §S1 exit): for each new
    binding, a stated grep/import check against the archived reference and
    either included parity evidence or a stated deferral reason.
  - Migration Guide rows added for every covered symbol.
- **Non-goals:** `prin-kernels`/DV-012 bindings (0141C); net-new surface
  (0141D); the full table and smoke matrix (0141E); acceptance-suite port.

## Required reading

- The 0141A handoff draft and the D-D disposition appendix
- `crates/prin-tensor/` and `crates/prin-train/` lib docs + WP-014/022/023 audits
- `crates/prin-py/src/bindings/` existing patterns (`train.rs`, `bands.rs`)
- `DOCS/standards/Coding_Standards.md` §2.1, §6; `DOCS/standards/Testing_Standards.md` §1, §4
- `DOCS/sphinx/parity_report.rst`
- Latest PSR and cumulative deviation ledger

## Entry conditions

- 0141A committed; `prin.__all__` foundation and `_deprecation` in place.
- No unresolved D1/D2 finding exists.
- The maturin toolchain builds on this host (Windows / Python 3.14 / Rust
  1.92); if it does not, the pass is reported blocked per CLAUDE.md, not
  worked around.

## Expected work

1. Add bindings; write Rust + Python tests in tandem.
2. `maturin develop -m crates/prin-py/Cargo.toml`; verify import.
3. Add `prin` wrapper modules / re-exports; decide and record each namespace
   placement (e.g. a `prin` compat module vs `prin.nn`).
4. gradcheck every trainable; property tests where the Testing Standards require.
5. Update `.pyi`; run the full local gate.
6. Record out-of-scope discoveries.

## Required evidence and outputs

- Code + tests in the same commit range; ≥95% coverage on new/changed code.
- Full local gate (Rust + Python) reproduced and recorded.
- Snyk Code on modified first-party Rust/Python; Snyk Open Source + `cargo
  audit` + `pip-audit` if any manifest changes.
- Sub-pass handoff note appended to the running S1 handoff draft.

## Prohibited

- Deferred tests, weakened assertions/tolerances, Python or `prin-py`
  numerics, undocumented public API, hidden RNG, unapproved `unsafe`, scope
  creep, unregistered experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0141C.

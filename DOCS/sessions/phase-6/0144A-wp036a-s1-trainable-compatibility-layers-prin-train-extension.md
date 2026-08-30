---

# Session 0144A — WP-036A S1: Coding — Trainable compatibility layers (`prin-train` extension)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S1 — Coding
**Predecessor:** [0144 — Documentation](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0144B — Audit](0144B-wp036a-s2-trainable-compatibility-layers-prin-train-extension.md)
**Authority:** Project Plan §6/§8 and **amendment #33**; the applicable normative
standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Scope note (amendment #33):** WP-036A delivers the 13 trainable-layer /
> discrete-network symbols (D-D appendix rows 31–42, 44) as real `prin-train`
> Rust implementations + PyO3 bindings, replacing the D-2.2 stubs shipped by
> WP-036 S1. WP-036A must execute and close **before** WP-036B S1
> (session 0144E) ports the `test_hierarchical`/`test_phase_to_rate`/`test_q2`/
> `test_q2_remaining`/`test_q3_new`/`test_nn`/`test_hybrid` reference clusters
> those symbols gate.

## Mission

Replace the 13 D-2.2 stubs in `prin.nn.deferred_layers` (amendment #33,
D-D appendix rows 31–42, 44) with real implementations backed by new
`prin-train` Rust modules and PyO3 bindings. The 13 symbols are:

| Row | Symbol | Category |
|---:|---|---|
| 31 | `FeedforwardInhibition` | Trainable `nn.Module` |
| 32 | `DentateGyrusConverter` | Trainable `nn.Module` |
| 33 | `DGLayer` | Trainable `nn.Module` (dynamic graph) |
| 34 | `oscillatory_weight_init` | Weight-initialization function |
| 35 | `PhaseToRateConverter` | Trainable `nn.Module` |
| 36 | `PhaseToRateAutoencoder` | Trainable `nn.Module` |
| 37 | `DenseAutoencoder` | Trainable `nn.Module` |
| 38 | `SparsityRegularizationLoss` | Loss function |
| 39 | `HierarchicalResonanceLayer` | Trainable `nn.Module` |
| 40 | `PhaseAmplitudeCouplingLayer` | Trainable `nn.Module` |
| 41 | `PRINetModel` | Trainable `nn.Module` (full model container) |
| 42 | `compile_model` | Model compilation function |
| 44 | `DiscreteDeltaThetaGammaLayer` | Trainable `nn.Module` (over WP-022 core + new projections) |

## Contract

- **Acceptance:** All 13 symbols resolve from `prin` as **real** implementations
  (not stubs). Each trainable module passes `torch.autograd.gradcheck` at
  `rtol=1e-3, atol=1e-3` (double-precision). Each module's forward pass matches
  the PRINet 3.0 reference output within documented tolerance. `compile_model`
  constructs a `PRINetModel` from a configuration dict and returns a callable
  model. `oscillatory_weight_init` applies the documented initialization scheme
  to a parameter tensor. All new Rust code is in `crates/prin-train/`; all new
  PyO3 bindings are in `crates/prin-py/src/bindings/`. No Python numerics
  (Coding Standards §2.1). `verify_api_surface(prin.__all__)` stays
  `(set(), set())`.
- **Non-goals:** Acceptance-suite test porting (WP-036B/C); new `prin` public
  symbols beyond the 13 listed above; GPU/CUDA/Triton implementations (DV-005
  remains a scoping decision); the `DiscreteDeltaThetaGamma` core binding
  (row 43, owned by WP-036B S1 / 0144E as an in-scope binding fix);
  `retrain_controller` (DV-025, owned by WP-036C S1 / 0144I).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31, #33
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Coding_Standards.md` §2.1 (no Python numerics), §6 (PyO3)
- `DOCS/standards/Testing_Standards.md` §1
- `DOCS/reports/036-project-state.md` and the cumulative deviation ledger
- `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` rows 31–44
- `DOCS/sphinx/migration_guide.rst` — per-symbol migration entries
- Existing `prin-train` modules (`layers.rs`, `bands.rs`, `activations.rs`,
  `inhibition.rs`, `energy.rs`) for architectural patterns
- `crates/prin-py/src/bindings/train.rs` and `train_layers.rs` for PyO3 patterns

## Entry conditions

- WP-036 S4 (0144) is closed and committed; the 13 symbols currently resolve
  as D-2.2 stubs.
- No unresolved D1/D2 finding exists.
- WP-036A scope, acceptance criteria, and non-goals have maintainer approval
  (amendment #33).

## Expected work

1. **Rust implementations** in `crates/prin-train/src/`: implement each of the
   13 symbols using Burn tensor operations, following the existing module
   patterns (`Config`/`Params`/`State` contracts, `Module` trait). Group into
   logical modules (e.g., `inhibition_layers.rs`, `autoencoders.rs`,
   `model.rs`). `DiscreteDeltaThetaGammaLayer` composes over the existing
   `DiscreteDeltaThetaGamma` core (WP-022) with new `proj_phase`/
   `proj_amplitude` linear projections.
2. **PyO3 bindings** in `crates/prin-py/src/bindings/`: thin marshalling
   wrappers for each symbol. `#![deny(unsafe_code)]` unchanged. No new
   numerics in `prin-py`.
3. **Python stub replacement**: replace the 13 D-2.2 stubs in
   `python/prin/nn/deferred_layers.py` with real implementations that delegate
   to `_prin_core` bridge classes. Update `.pyi` stubs.
4. **Tests**: gradcheck for each trainable module; forward-pass parity against
   PRINet 3.0 reference values; construction/error-path tests; `compile_model`
   integration test. ≥95% coverage on new code.
5. **Migration Guide update**: update per-symbol rows from "removed / D-2.2
   stub" to "real implementation" with the new delegation path.

## Required evidence and outputs

- New `prin-train` Rust modules and PyO3 bindings; all `cargo` gates green.
- Updated `python/prin/nn/deferred_layers.py` (13 stubs → real); `.pyi` updated.
- ≥95% coverage on new/changed code; gradcheck green for every trainable module.
- `ruff`/`ruff format`/`mypy --strict`/`bandit`/`interrogate` all pass.
- `verify_api_surface(prin.__all__) == (set(), set())` confirmed.
- `tools/check_no_python_numerics.py` clean (updated module count).
- Migration Guide updated for all 13 symbols.
- S1 handoff note mapping each symbol to its Rust owner, binding, test count,
  and gradcheck result.

## Prohibited

- Python numerics (Coding Standards §2.1); `unsafe` in `prin-py`; scope creep
  into WP-036B/C or new-symbol work beyond the 13 listed; weakened gradcheck
  tolerances; hidden RNG; unapproved `unsafe`; deferred tests; undocumented
  public API changes.

## Exit gate

All S1 gates green; every acceptance criterion is evidence-mapped. Hand off to
the mandatory S2 audit; S1 may not self-certify completion.

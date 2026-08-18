# prin-train

Trainable layer stack for PRIN, built on the [Burn](https://burn.dev)
autodiff backend.

## Implemented (WP-022, sessions 0085–0088)

- **`bands::DiscreteDeltaThetaGamma`** — trainable discrete-time multi-rate
  hierarchical oscillator network (rebuild of PRINet 3.0
  `core.propagation.networks.DiscreteDeltaThetaGamma`): learned intra-band
  coupling, phase-amplitude-coupling gating (delta→theta, theta→gamma), and
  Stuart–Landau amplitude dynamics, all in a fixed number of discrete macro
  steps (no inner ODE loop).
- **`layers::ResonanceLayer`** — trainable single-layer extended-Kuramoto
  resonance primitive (rebuild of PRINet 3.0 `nn.layers.ResonanceLayer`):
  learned coupling, decay, input projection, and frequency modulation.
- **`error::TrainError`** — the crate's typed error enum (`EmptyBand`,
  `ShapeMismatch`, `NonFiniteParameter`, `InvalidTimestep`,
  `NonFiniteState`), re-exported at the crate root.

Both modules expose a `Config` (validated hyperparameters, seeded-random or
explicit initialization), a `Params` struct (explicit parameter tensors for
golden-reference tests and non-`burn::record` checkpoint paths), and a
validated `State` contract for the tensors `step`/`integrate` operate on.
`TrainError`, `DiscreteDeltaThetaGammaParams`, and `ResonanceLayerParams`
are re-exported at the crate root (`pub use` in `lib.rs`) so callers can
name them in explicit type annotations without reaching into submodule
paths; `tests/public_api.rs` compile-guards those re-exports. See each
module's rustdoc for the exact per-step formula and its correspondence to
the PRINet 3.0 reference (`layers.rs` documents one deliberate deviation:
a simpler, fully differentiable initial-state projection in place of
PRINet 3.0's FFT-based initializer — the Kuramoto step dynamics themselves
are unaffected).

Golden-value parity tests against PRINet 3.0 (`torch==2.13.0+cpu`, float64)
live in `tests/parity_bands.rs` / `tests/parity_layers.rs`; gradient
reference tests (autodiff vs. central finite difference) and `burn::record`
serialization round-trips are in each module's unit tests. The `burn`
dependency pulls in `bincode` 2.0.1 transitively (RUSTSEC-2025-0141,
"unmaintained" informational warning, no CVE); the advisory is formally
accepted by Project Plan amendment #27 with per-cycle `cargo audit`
re-checks, same disposition class as the `paste` advisory (amendment #9).

## Not yet implemented

Later Phase 4 work packages: feedforward/feedback inhibition and the
straight-through estimator, phase activations, Holomorphic Equilibrium
Propagation (WP-023); resonance-aware optimizers (WP-024); the production
PyTorch `torch.autograd.Function` bridge exposing these primitives to
Python training loops (WP-025).

Rebuild target for PRINet 3.0 `nn/{layers,optimizers,activations,hep}.py`
and the trainable half of `core/propagation/{networks,inhibition}.py`.

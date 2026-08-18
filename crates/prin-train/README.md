# prin-train

Trainable layer stack for PRIN, built on the [Burn](https://burn.dev)
autodiff backend.

## Implemented

### WP-022: Trainable bands and resonance primitives (sessions 0085–0088)

- **`bands::DiscreteDeltaThetaGamma`** — trainable discrete-time multi-rate
  hierarchical oscillator network (rebuild of PRINet 3.0
  `core.propagation.networks.DiscreteDeltaThetaGamma`): learned intra-band
  coupling, phase-amplitude-coupling gating (delta→theta, theta→gamma), and
  Stuart–Landau amplitude dynamics, all in a fixed number of discrete macro
  steps (no inner ODE loop).
- **`layers::ResonanceLayer`** — trainable single-layer extended-Kuramoto
  resonance primitive (rebuild of PRINet 3.0 `nn.layers.ResonanceLayer`):
  learned coupling, decay, input projection, and frequency modulation.

### WP-023: Inhibition, activations, energy, and HEP (sessions 0089–0092)

- **`inhibition::FeedbackInhibition`** — feedback lateral inhibition with a
  straight-through estimator (STE) for competitive k-WTA activation
  (rebuild of the trainable half of PRINet 3.0
  `core.propagation.inhibition.FeedbackInhibition`): hard top-$k$ selection in
  the forward pass and soft temperature-scaled sigmoid backward gradients, with
  optional target-sparsity parameterization ($k = \lfloor (1 - s) \cdot N \rfloor$).
- **`activations`** — complex and phase activation functions (rebuild of PRINet 3.0
  `nn.activations`):
  - `d_silu` — analytic derivative of the SiLU/swish function ($d/dx [x \cdot \sigma(x)]$).
  - `ComplexTensor` — lightweight real-imaginary pair representation for complex
    states in Burn.
  - `HolomorphicActivation` — split-complex holomorphic activation module applying
    $\tanh$ independently to real and imaginary components.
  - `phase_activation` — periodic phase activation wrapping phase angles into
    $[-\pi, \pi)$ via $2\pi$-modular arithmetic.
  - `GatedPhaseActivation` — trainable gated phase activation combining phase
    wrapping, $d_{\text{silu}}$ modulation, and learned gate bias.
- **`energy::HolomorphicEnergy`** — holomorphic energy function for complex oscillator
  states (rebuild of PRINet 3.0 `nn.hep.HolomorphicEnergy`): coupling energy
  ($-\frac{1}{2} \text{Re}(z^\dagger W z)$), self-energy penalizing deviation from
  unit amplitude, and optional supervised task loss with $\beta$ weighting.
- **`hep::HolomorphicEp`** — Holomorphic Equilibrium Propagation trainer (rebuild
  of PRINet 3.0 `nn.hep.HolomorphicEquilibriumPropagation`): coordinates free-phase
  and nudged-phase ($+\beta, -\beta$) equilibrium relaxation and computes
  contrastive coupling parameter gradients via closed-form outer-product symmetric
  differences.
- **`error::TrainError`** — typed error enum (`EmptyBand`, `ShapeMismatch`,
  `NonFiniteParameter`, `InvalidTimestep`, `NonFiniteState`, `InvalidK`,
  `DivisionByZero`, `StepLimitExceeded`, `BetaTooSmall`), re-exported at the
  crate root.

All modules expose validated `Config` contracts, explicit `Params` structs
(where learnable parameters exist: `DiscreteDeltaThetaGammaParams`,
`ResonanceLayerParams`, `GatedPhaseActivationParams`, all re-exported at crate
root and compile-guarded by `tests/public_api.rs`), and validated `State` contracts.
See each module's rustdoc for exact formulations and correspondence to PRINet 3.0.

Golden-value parity tests against PRINet 3.0 (`torch==2.13.0+cpu`, float64)
live in `tests/parity_*.rs` (`parity_bands`, `parity_layers`, `parity_inhibition`,
`parity_activations`, `parity_energy`). Gradient reference tests (autodiff vs.
central finite difference) and `burn::record` serialization round-trips are in
each module's unit tests. The `bincode` 2.0.1 transitive advisory (RUSTSEC-2025-0141)
is governed by Project Plan amendment #27.

## Not yet implemented

Later Phase 4 work packages: resonance-aware optimizers (WP-024); the production
PyTorch `torch.autograd.Function` bridge exposing these primitives to Python
training loops (WP-025); PhaseTracker, Hybrid model, baselines, and resource
allocation (WP-026); trainable-stack integration and Phase 4 gate (WP-027).

Rebuild target for PRINet 3.0 `nn/{layers,optimizers,activations,hep}.py`
and the trainable half of `core/propagation/{networks,inhibition}.py`.

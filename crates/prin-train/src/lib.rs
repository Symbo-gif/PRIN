//! # prin-train
//!
//! Trainable components for PRIN (rebuild of PRINet 3.0 `nn/` internals),
//! built on the Burn autodiff backend and exposed to PyTorch via `prin-py`
//! bridges (Phase 4, WP-025).
//!
//! Implemented so far:
//!
//! - [`bands`] — [`bands::DiscreteDeltaThetaGamma`] (WP-022): trainable
//!   discrete-time multi-rate hierarchical oscillator network with learnable
//!   intra-band coupling, PAC gating, and Stuart–Landau amplitude dynamics.
//! - [`layers`] — [`layers::ResonanceLayer`] (WP-022): trainable
//!   single-layer extended-Kuramoto resonance primitive with learnable
//!   coupling, decay, input projection, and frequency modulation.
//! - [`inhibition`] — [`inhibition::FeedbackInhibition`] (WP-023): top-`k`
//!   winner-take-all competition with a hard-forward / soft-backward
//!   straight-through estimator (STE).
//! - [`activations`] — [`activations::d_silu`],
//!   [`activations::HolomorphicActivation`] (split-complex),
//!   [`activations::GatedPhaseActivation`] (WP-023): oscillator-compatible
//!   activation functions.
//! - [`energy`] — [`energy::HolomorphicEnergy`] (WP-023): holomorphic energy
//!   function for complex oscillator states, with a closed-form coupling
//!   gradient.
//! - [`hep`] — [`hep::HolomorphicEp`] (WP-023): ±β Holomorphic Equilibrium
//!   Propagation gradient estimator over [`layers::ResonanceLayer`].
//!
//! `bands`/`layers` (Burn `Module`s) expose a `Config` (validated
//! hyperparameters), a `Params` struct (explicit parameter tensors, for
//! golden-reference tests and checkpoint restoration outside
//! [`burn::record`]), and a validated `State` contract for the tensors
//! `step`/`integrate` operate on; `activations::GatedPhaseActivation`
//! follows the same pattern. `inhibition`/`energy`/`hep` have no learnable
//! parameters of their own (see their module docs for what "trainable"
//! means for each) and so expose only a `Config`.
//!
//! Not yet implemented (later Phase 4 work packages): resonance-aware
//! optimizers (WP-024), and the production PyTorch `torch.autograd.Function`
//! bridge (WP-025).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod activations;
pub mod bands;
pub mod energy;
pub mod error;
pub mod hep;
pub mod inhibition;
pub mod layers;

mod support;

pub use activations::GatedPhaseActivationParams;
pub use bands::DiscreteDeltaThetaGammaParams;
pub use error::TrainError;
pub use layers::ResonanceLayerParams;

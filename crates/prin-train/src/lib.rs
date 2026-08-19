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
//! - [`feedback`] — [`feedback::OscillatorOptimizer`] (WP-024): the shared
//!   step/state-dict contract [`sync_gd::SyncGd`], [`rip::Rip`], and
//!   [`scalr::Scalr`] implement, plus [`feedback::StepFeedback`] and
//!   [`feedback::OrderParameter`], the order-parameter/phase/amplitude
//!   feedback types they consume.
//! - [`sync_gd`] — [`sync_gd::SyncGd`] (WP-024): SGD with a Kuramoto
//!   order-parameter synchronization-barrier penalty (PRINet 3.0
//!   `SynchronizedGradientDescent`).
//! - [`rip`] — [`rip::Rip`] (WP-024): Resonance-Induced Plasticity, a
//!   Hebbian coupling-matrix update driven by phase coherence (PRINet 3.0
//!   `RIPOptimizer`).
//! - [`scalr`] — [`scalr::Scalr`] (WP-024): Synchronization-Coupled
//!   Adaptive Learning Rate, including oscillation-aware decay, adaptive
//!   `r_min`, and per-frequency lr scaling (PRINet 3.0 `SCALROptimizer`).
//!
//! `bands`/`layers` (Burn `Module`s) expose a `Config` (validated
//! hyperparameters), a `Params` struct (explicit parameter tensors, for
//! golden-reference tests and checkpoint restoration outside
//! [`burn::record`]), and a validated `State` contract for the tensors
//! `step`/`integrate` operate on; `activations::GatedPhaseActivation`
//! follows the same pattern. `inhibition`/`energy`/`hep` have no learnable
//! parameters of their own (see their module docs for what "trainable"
//! means for each) and so expose only a `Config`. `sync_gd`/`rip`/`scalr`
//! are not `Module`s (they *consume* gradients rather than holding
//! trainable parameters of their own); each exposes a `Config` and a
//! serializable `State` snapshot for deterministic resume, per
//! [`feedback::OscillatorOptimizer`]'s docs.
//!
//! Not yet implemented (later Phase 4 work packages): the production
//! PyTorch `torch.autograd.Function` bridge (WP-025).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod activations;
pub mod bands;
pub mod energy;
pub mod error;
pub mod feedback;
pub mod hep;
pub mod inhibition;
pub mod layers;
pub mod rip;
pub mod scalr;
pub mod sync_gd;

mod support;

pub use activations::GatedPhaseActivationParams;
pub use bands::DiscreteDeltaThetaGammaParams;
pub use error::TrainError;
pub use feedback::{OrderParameter, OscillatorOptimizer, StepFeedback};
pub use layers::ResonanceLayerParams;
pub use rip::{Rip, RipConfig};
pub use scalr::{Scalr, ScalrConfig};
pub use sync_gd::{SyncGd, SyncGdConfig};

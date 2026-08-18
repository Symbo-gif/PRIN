//! # prin-train
//!
//! Trainable components for PRIN (rebuild of PRINet 3.0 `nn/` internals),
//! built on the Burn autodiff backend and exposed to PyTorch via `prin-py`
//! bridges (Phase 4, WP-025).
//!
//! Implemented so far (WP-022 S1):
//!
//! - [`bands`] — [`bands::DiscreteDeltaThetaGamma`]: trainable discrete-time
//!   multi-rate hierarchical oscillator network with learnable intra-band
//!   coupling, PAC gating, and Stuart–Landau amplitude dynamics.
//! - [`layers`] — [`layers::ResonanceLayer`]: trainable single-layer
//!   extended-Kuramoto resonance primitive with learnable coupling, decay,
//!   input projection, and frequency modulation.
//!
//! Both modules expose a `Config` (validated hyperparameters), a `Params`
//! struct (explicit parameter tensors, for golden-reference tests and
//! checkpoint restoration outside [`burn::record`]), and a validated `State`
//! contract for the tensors `step`/`integrate` operate on.
//!
//! Not yet implemented (later Phase 4 work packages): feedforward/feedback
//! inhibition and the straight-through estimator (WP-023), phase
//! activations and Holomorphic Equilibrium Propagation (WP-023),
//! resonance-aware optimizers (WP-024), and the production PyTorch
//! `torch.autograd.Function` bridge (WP-025).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod bands;
pub mod error;
pub mod layers;

mod support;

pub use bands::DiscreteDeltaThetaGammaParams;
pub use error::TrainError;
pub use layers::ResonanceLayerParams;

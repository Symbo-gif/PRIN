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
//! - [`attention`] — [`attention::OscillatoryAttention`] (WP-026): multi-head
//!   attention with an additive oscillatory phase-coherence bias.
//! - [`phase_tracker`] — [`phase_tracker::PhaseTracker`] (WP-026): PRIN's
//!   primary contribution — a phase-based multi-object tracker built on
//!   [`bands::DiscreteDeltaThetaGamma`] dynamics and phase-coherence
//!   similarity matching.
//! - [`hybrid`] — [`hybrid::HybridPRINetV2`] (WP-026): the canonical hybrid
//!   oscillator + attention classification architecture, composing
//!   [`bands::DiscreteDeltaThetaGamma`] and [`attention::OscillatoryAttention`].
//! - [`slot_attention`] — [`slot_attention::SlotAttentionModule`],
//!   [`slot_attention::TemporalSlotAttentionMOT`] (WP-026): the non-oscillatory
//!   Slot Attention (Locatello et al. 2020) comparison baseline, the latter a
//!   direct head-to-head tracking baseline against [`phase_tracker::PhaseTracker`].
//! - [`ablation`] — [`ablation::PhaseTrackerFrozen`],
//!   [`ablation::PhaseTrackerStatic`], [`ablation::SlotAttentionNoGRU`],
//!   [`ablation::SlotAttentionFrozen`] (WP-026): structural ablation variants
//!   isolating which components drive temporal binding.
//! - [`allocation`] — [`allocation::AdaptiveOscillatorAllocator`],
//!   [`allocation::DynamicPhaseTracker`] (WP-026): task-complexity-driven
//!   adaptive oscillator-count allocation.
//!
//! `bands`/`layers` (Burn `Module`s) expose a `Config` (validated
//! hyperparameters), a `Params` struct (explicit parameter tensors, for
//! golden-reference tests and checkpoint restoration outside
//! [`burn::record`]), and a validated `State` contract for the tensors
//! `step`/`integrate` operate on; `activations::GatedPhaseActivation` and
//! `attention::OscillatoryAttention` follow the same pattern.
//! `inhibition`/`energy`/`hep` have no learnable parameters of their own
//! (see their module docs for what "trainable" means for each) and so
//! expose only a `Config`. `sync_gd`/`rip`/`scalr` are not `Module`s (they
//! *consume* gradients rather than holding trainable parameters of their
//! own); each exposes a `Config` and a serializable `State` snapshot for
//! deterministic resume, per [`feedback::OscillatorOptimizer`]'s docs.
//! [`allocation::DynamicPhaseTracker`] is deliberately not a `Module` either
//! (see its own module docs for why).
//!
//! WP-025 delivered the production PyTorch `torch.autograd.Function` bridge
//! for [`layers::ResonanceLayer`]/[`activations::GatedPhaseActivation`]
//! (`crates/prin-py/src/bindings/train.rs`). The WP-026 symbols above have
//! **no PyO3/Python bridge yet** — an explicit, evidence-backed carried-scope
//! item for a future WP/session, not a silent gap; see the WP-026 S1 handoff
//! note (`DOCS/experiments/`) for the full rationale.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod ablation;
pub mod activations;
pub mod allocation;
pub mod attention;
pub mod bands;
pub mod energy;
pub mod error;
pub mod feedback;
pub mod hep;
pub mod hybrid;
pub mod inhibition;
pub mod layers;
pub mod phase_tracker;
pub mod rip;
pub mod scalr;
pub mod slot_attention;
pub mod sync_gd;

mod support;

pub use activations::GatedPhaseActivationParams;
pub use attention::OscillatoryAttentionParams;
pub use bands::DiscreteDeltaThetaGammaParams;
pub use error::TrainError;
pub use feedback::{OrderParameter, OscillatorOptimizer, StepFeedback};
pub use layers::ResonanceLayerParams;
pub use rip::{Rip, RipConfig};
pub use scalr::{Scalr, ScalrConfig};
pub use sync_gd::{SyncGd, SyncGdConfig};

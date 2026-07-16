//! # prin-train
//!
//! Trainable components for PRIN (rebuild of PRINet 3.0 `nn/` internals), built
//! on the Burn autodiff backend and exposed to PyTorch via `prin-py` bridges:
//!
//! - `bands` — DiscreteDeltaThetaGamma: trainable discrete-time network with
//!   learnable coupling matrices, PAC depths, and frequency offsets.
//! - `layers` — ResonanceLayer, HierarchicalResonanceLayer, OscillatoryAttention,
//!   PhaseToRateConverter (soft/hard/annealed).
//! - `inhibition` — feedforward inhibition; feedback winner-take-all top-k with a
//!   custom straight-through-estimator backward (forward-hard/backward-soft).
//! - `activations` — dSiLU, HolomorphicActivation (complex tanh), PhaseActivation,
//!   GatedPhaseActivation.
//! - `hep` — Holomorphic Equilibrium Propagation: free + ±β nudge phases,
//!   gradient ≈ (1/2β)(E⁺ − E⁻), no BPTT.
//! - `optim` — SynchronizedGradientDescent, SCALR, RIP, AlternatingOptimizer
//!   (order-parameter feedback computed here; thin Python optimizer classes wrap).
//!
//! Implementation lands in Phase 4 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

//! # prin-dynamics
//!
//! Fundamental oscillator dynamics for PRIN:
//!
//! - [`state`] — oscillator state (struct-of-arrays), phase wrapping to `[0, 2π)`,
//!   atan2-safe phase differences, NaN/Inf guards, derivative/amplitude clamps,
//!   sort-based k-NN phase index.
//! - [`seed`] — deterministic counter-based [`Seed`] authority for all stochastic
//!   entry points (`Pcg64`; forward-compatible with counter-mode generators).
//! - [`models`] — Kuramoto (mean-field, pairwise, sparse k-NN), Stuart–Landau, and
//!   Hopf dynamics behind the `Dynamics` trait.
//! - [`integrate`] — Euler, RK4, adaptive RK45 (Dormand–Prince), exponential
//!   (direct/Krylov), and multi-rate sub-stepped integrators behind the
//!   `Integrator` trait.
//! - [`pac`] — phase–amplitude coupling: `A_fast = A₀·[1 + m·cos(φ_slow + offset)]`.
//! - [`coupling`] — coupling modes (mean-field, full matrix, sparse k-NN) and
//!   topology builders (all-to-all, ring, directed Watts–Strogatz small-world),
//!   all enum-dispatched.
//! - [`bands`] — continuous hierarchical band networks (ThetaGamma,
//!   DeltaThetaGamma). Trainable discrete variants live in `prin-train`.
//! - [`temporal`] — complex-phasor phase blending + EMA amplitude blending.
//!
//! Numerical hazard invariants preserved from PRINet 3.0 (see the project plan §7):
//! phase wrap via `% 2π` (not atan2 renormalization), amplitude clamp `[1e-6, 10]`,
//! derivative clamp `±1e4`, coupling normalization `1/N` vs `1/k` per mode.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod bands;
pub mod coupling;
pub mod integrate;
pub mod models;
pub mod pac;
pub mod seed;
pub mod state;
pub mod temporal;

pub use bands::{
    create_band_state, delta_theta_gamma_network, theta_gamma_network, BandError, BandNetwork,
    BandParams, PacPair,
};
pub use coupling::{CouplingError, CouplingMode, Topology};
pub use integrate::{
    integrate_fixed, AdaptiveResult, EulerIntegrator, ExponentialIntegrator, GuardPolicy,
    IntegrateError, Integrator, MultiRateIntegrator, MultiRateMethod, RK45Integrator,
    RK4Integrator,
};
pub use models::{Dynamics, HopfOscillator, KuramotoOscillator, StuartLandauOscillator};
pub use pac::{PacError, PhaseAmplitudeCoupling};
pub use seed::{Seed, SeedError};
pub use state::{OscillatorState, StateDerivatives, StateError};
pub use temporal::{ComplexPhasorBlender, EmaAmplitudeBlender, TemporalError, TemporalPropagator};

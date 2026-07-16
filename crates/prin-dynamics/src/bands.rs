//! Continuous hierarchical band networks.
//!
//! - ThetaGamma: 2-band, ~7-item binding capacity.
//! - DeltaThetaGamma: 3-band continuous ODE network.
//!
//! The trainable discrete-time variant (DiscreteDeltaThetaGamma) lives in
//! `prin-train::bands` because it requires autodiff.
//!
//! Implementation lands in Phase 2 (see `DOCS/PRIN_Project_Plan.md`).

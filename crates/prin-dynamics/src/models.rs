//! Oscillator models behind the `Dynamics` trait.
//!
//! - Kuramoto: mean-field `O(N)`, full pairwise `O(N²)`, sparse k-NN `O(N·k)`.
//! - Stuart–Landau: complex amplitude dynamics.
//! - Hopf: bifurcation-driven limit cycles.
//!
//! Coupling mode is an enum (see [`crate::coupling`]), never a string.
//!
//! Implementation lands in Phase 1 (see `DOCS/PRIN_Project_Plan.md`).

//! Numerical integrators behind the `Integrator` trait.
//!
//! - Euler, RK4, adaptive RK45.
//! - Exponential integrator: direct matrix-exp `O(D³)` and Krylov `O(D·m²)` with
//!   adaptive subspace dimension; φ₁(λ) → 1 limit handling preserved.
//! - Multi-rate sub-stepped RK4 for θ→γ frequency separation.
//!
//! Implementation lands in Phases 1–2 (see `DOCS/PRIN_Project_Plan.md`).

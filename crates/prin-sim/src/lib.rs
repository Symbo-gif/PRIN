//! # prin-sim
//!
//! OscilloSim sparse simulation engine for PRIN (rebuild of PRINet 3.0
//! `utils/oscillosim.py` and `core/propagation/sweep_utils.py`):
//!
//! - [`csr_coupling`] — CSR sparse coupling matrix with O(nnz) SpMV-based
//!   Kuramoto and Stuart–Landau coupling computations.
//! - [`engine`] — [`OscilloSim`] engine orchestrating state, sparse dynamics,
//!   integration, pruning, and trajectory recording.
//! - [`pruning`] — amplitude-threshold oscillator pruning with apply/restore
//!   mapping for dynamic system-size reduction.
//! - [`chimera`] — chimera-state detection metrics integrated with the CSR
//!   sparsity pattern as the spatial neighbor structure.
//! - [`sweep`] — rayon-parallel parameter sweeps over coupling strength,
//!   decay rate, and other axes with deterministic seeding and oscillation
//!   detection.
//!
//! ## Architecture
//!
//! `prin-sim` sits above `prin-dynamics` in the crate dependency graph:
//!
//! ```text
//! prin-sim
//! ├── prin-dynamics  (state, models, integrators, seed)
//! └── prin-metrics   (chimera, order, coherence)
//! ```
//!
//! The engine reuses `OscillatorState`, `StateDerivatives`, `Dynamics`,
//! `Integrator`, and `Seed` from `prin-dynamics`. It does **not** duplicate
//! any dynamics logic — the sparse models ([`SparseKuramoto`],
//! [`SparseStuartLandau`]) implement the `Dynamics` trait using CSR SpMV
//! instead of dense iteration.
//!
//! ## Numerical invariants
//!
//! All numerical guards (phase wrap, amplitude clamp, derivative clamp) are
//! inherited from `prin-dynamics`. The deterministic `Seed` flow is preserved:
//! no hidden RNG enters the simulation.
//!
//! ## CPU dispatch
//!
//! The hot loops in [`csr_coupling`] and [`engine`] (SpMV, row-sum, and
//! per-element derivative combination) run through the private `dispatch`
//! module's size-gated helpers: a sequential CPU reference path below a
//! tuned element-count threshold, and a `rayon`-parallel path at or above
//! it. `SparseKuramoto`, `SparseStuartLandau`, and `OscilloSim` share their
//! `SparseCoupling` via `Arc` rather than deep-cloning the CSR storage
//! (see `OscilloSim::coupling_arc`).
//!
//! ## Non-goals (this work package)
//!
//! GPU dispatch (Phase 3) and final scientific-campaign conclusions
//! (Phase 7) remain out of scope. `crates/prin-py` sweep/engine bindings and
//! `crates/prin-kernels` CPU-reference work, originally listed in the
//! WP-016 declaration, are moved to a future WP by plan amendment #20
//! (`DOCS/PRIN_Project_Plan.md` §8.3): WP-016 is scoped to `crates/prin-sim`
//! only.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod chimera;
pub mod csr_coupling;
mod dispatch;
pub mod engine;
pub mod error;
pub mod pruning;
pub mod sweep;

pub use chimera::{compute_chimera_metrics, trajectory_chimera_metrics, ChimeraMetrics};
pub use csr_coupling::SparseCoupling;
pub use engine::{apply_guards, OscilloSim, SparseKuramoto, SparseStuartLandau, Trajectory};
pub use error::SimError;
pub use pruning::{PruningResult, PruningStrategy};
pub use sweep::{detect_oscillation, run_sweep, SweepAxis, SweepConfig, SweepModel, SweepResult};

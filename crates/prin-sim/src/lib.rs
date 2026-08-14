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
//! ## Non-goals (this work package)
//!
//! Parameter sweeps, GPU dispatch, and final 1M-oscillator performance claims
//! are deferred to later work packages.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod chimera;
pub mod csr_coupling;
pub mod engine;
pub mod error;
pub mod pruning;

pub use chimera::{compute_chimera_metrics, trajectory_chimera_metrics, ChimeraMetrics};
pub use csr_coupling::SparseCoupling;
pub use engine::{apply_guards, OscilloSim, SparseKuramoto, SparseStuartLandau, Trajectory};
pub use error::SimError;
pub use pruning::{PruningResult, PruningStrategy};

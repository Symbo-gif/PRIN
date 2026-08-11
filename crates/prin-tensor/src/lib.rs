//! # prin-tensor
//!
//! Tensor decomposition for PRIN (rebuild of PRINet 3.0
//! `core/decomposition.py`):
//!
//! - [`tucker`] — Tucker/HOSVD decomposition (`PolyadicTensor`).
//! - [`cp`] — CP/PARAFAC decomposition via alternating least squares.
//! - [`utils`] — mode-n unfolding, mode-n product, and tensor arithmetic.
//!
//! Parity tolerance: `rtol = 1e-10` at float64 against the PRINet 3.0 golden
//! corpus (single-runtime verification).
//!
//! ## Numerics
//!
//! All decomposition paths run in f64. SVD is computed via `faer` (pure Rust,
//! no system dependencies). CP-ALS uses deterministic initialization through
//! the [`prin_dynamics::Seed`] authority for reproducible factor matrices.
//!
//! ## Invariants
//!
//! Tucker reconstruction is exact when all mode ranks equal the mode dimensions
//! (full-rank HOSVD). CP-ALS convergence is monitored via relative change in
//! the factor matrices; non-convergence returns a typed error.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod cp;
pub mod error;
pub mod tucker;
pub mod utils;

pub use cp::{cp_als, CPDecomposition, CPResult};
pub use error::TensorError;
pub use tucker::{hosvd, PolyadicTensor};

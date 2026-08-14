//! # prin-tensor
//!
//! Tensor decomposition for PRIN (rebuild of PRINet 3.0
//! `core/decomposition.py`):
//!
//! - [`tucker`] — Tucker/HOSVD decomposition (`PolyadicTensor`).
//! - [`cp`] — CP/PARAFAC decomposition via alternating least squares.
//! - [`utils`] — mode-n unfolding, mode-n product, and tensor arithmetic.
//!
//! Parity with the PRINet 3.0 reference is verified by integration tests in
//! `tests/parity_decomposition.rs` at `rtol = 1e-10` (float64, single-runtime).
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
//! the reconstruction error `‖X − X̂‖_F`; non-convergence returns a typed error.
//!
//! This crate defines no `strict-checks`-gated code of its own: `hosvd` and
//! `cp_als` validate finiteness of their inputs unconditionally (stricter by
//! default) rather than behind an opt-in feature flag, so there is no
//! `strict-checks` feature to declare here (contrast `prin-sim`, which
//! forwards the flag to `prin-dynamics`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod cp;
pub mod error;
pub mod tucker;
pub mod utils;

pub use cp::{cp_als, CPDecomposition, CPResult};
pub use error::TensorError;
pub use tucker::{hosvd, PolyadicTensor};

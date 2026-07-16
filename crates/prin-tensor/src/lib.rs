//! # prin-tensor
//!
//! Polyadic tensor decomposition for PRIN (rebuild of PRINet 3.0
//! `core/decomposition.py`):
//!
//! - Tucker/HOSVD (`PolyadicTensor`) — HOSVD via SVD (planned backend: `faer`).
//! - CP/PARAFAC (`CPDecomposition`) — via alternating least squares (ALS).
//!
//! Parity tolerance: `rtol = 1e-10` at float64 against the PRINet 3.0 golden
//! corpus.
//!
//! Implementation lands in Phase 2 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

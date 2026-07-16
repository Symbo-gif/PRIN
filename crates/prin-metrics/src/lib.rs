//! # prin-metrics
//!
//! Synchronization and chimera metrics for PRIN (rebuild of PRINet 3.0
//! `core/measurement.py`):
//!
//! - Kuramoto order parameter, mean phase coherence, phase coherence matrix, PSD.
//! - Sparse k-NN metric variants.
//! - Chimera metrics: local order parameter, bimodality index, chimera index,
//!   strength of incoherence, discontinuity measure.
//!
//! Invariants: order parameter ∈ `[0, 1]`; f32 compute with f64 accumulation for
//! order-parameter reductions (see the Performance Strategy in the project plan).
//!
//! Implementation lands in Phase 1 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

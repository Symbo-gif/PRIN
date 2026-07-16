//! # prin-sim
//!
//! The OscilloSim engine for PRIN (rebuild of PRINet 3.0 `utils/oscillosim.py`
//! and `core/propagation/sweep_utils.py`):
//!
//! - 1M+-oscillator simulation with CSR sparse coupling (SpMV coupling steps).
//! - Chimera detection using `prin-metrics`.
//! - Oscillator pruning and async pipelines.
//! - Grid parameter sweeps parallelized over rayon (target: ≥ 8× on a 16-core
//!   CPU vs the serial Python loop in 3.0).
//!
//! Implementation lands in Phase 2 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

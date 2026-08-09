//! # prin-metrics
//!
//! Synchronization and chimera metrics for PRIN (rebuild of PRINet 3.0
//! `core/measurement.py` and the Year-4-Q1 chimera utilities in
//! `utils/oscillosim.py`):
//!
//! - [`order`] — Kuramoto order parameter (scalar and complex) and
//!   inter-frame phase correlation.
//! - [`coherence`] — mean phase coherence, phase coherence matrix, and the
//!   sparse k-NN coherence approximation.
//! - [`spectral`] — power spectral density and concept-probability
//!   extraction.
//! - [`energy`] — dense and sparse synchronization energy.
//! - [`chimera`] — local order parameter, bimodality index, strength of
//!   incoherence, discontinuity measure (chimera number), chimera index, and
//!   temporal strength of incoherence.
//! - [`metastability()`] — temporal standard deviation of the order parameter
//!   (PRIN extension).
//! - [`knn`] — measurement-facing k-nearest-phase-neighbour index delegating
//!   to `prin-dynamics` (one algorithm, one implementation).
//!
//! ## Numerics
//!
//! All metrics run in f64, matching the `torch.float64` reference paths in
//! PRINet 3.0 (`order_parameter_traj` / `mean_phase_coherence_traj` in the
//! golden corpus). Single-runtime verification targets `rtol = 1e-10` (plan
//! §5); cross-platform corpus-regeneration comparisons use the registered
//! METRIC tolerance (`rtol = 1e-8`, amendment #16).
//!
//! Preserved numerical hazards: PRINet 3.0 computes the PSD resonance signal
//! through a `complex64` intermediate and the chimera utilities in
//! `torch.float32`. PRIN keeps the f64 reference path instead of reproducing
//! the truncation, so parity for those paths uses the documented f32-drift
//! tolerance (`1e-6`), consistent with plan amendment #14.
//!
//! ## Invariants
//!
//! Order parameters and correlation magnitudes are clamped to `[0, 1]` (the
//! exact mathematical range; floating-point accumulation can exceed it by
//! ~1 ulp). Mean phase coherence is clamped to `[-1, 1]` for the same
//! reason. The `C = (N r² − 1)/(N − 1)` identity between
//! [`mean_phase_coherence`] and [`kuramoto_order_parameter`] is
//! cross-checked in tests.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod chimera;
pub mod coherence;
pub mod energy;
pub mod error;
pub mod knn;
pub mod metastability;
pub mod order;
pub mod spectral;

pub use chimera::{
    bimodality_index, chimera_index, discontinuity_measure, local_order_parameter,
    strength_of_incoherence, strength_of_incoherence_temporal, BIMODALITY_CHIMERA_THRESHOLD,
    DEFAULT_CHIMERA_THRESHOLD,
};
pub use coherence::{mean_phase_coherence, phase_coherence_matrix, sparse_mean_phase_coherence};
pub use energy::{sparse_synchronization_energy, synchronization_energy};
pub use error::MetricError;
pub use knn::build_phase_knn;
pub use metastability::metastability;
pub use order::{
    inter_frame_phase_correlation, kuramoto_order_parameter, kuramoto_order_parameter_complex,
    order_parameter_series,
};
pub use spectral::{extract_concept_probabilities, power_spectral_density};

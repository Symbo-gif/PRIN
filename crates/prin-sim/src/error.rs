//! Typed errors for the OscilloSim simulation engine.
//!
//! Every fallible public entry point in `prin-sim` returns [`SimError`]. The
//! enum wraps the lower-level error types from `prin-dynamics`, `prin-metrics`,
//! and the sparse coupling layer so callers can match on the failure category
//! without importing every sub-crate error.

use thiserror::Error;

/// Errors raised by the OscilloSim engine and its components.
#[derive(Debug, Error)]
pub enum SimError {
    /// The oscillator population is empty.
    #[error("simulation requires n >= 1, got {n}")]
    EmptyPopulation {
        /// Offending population size.
        n: usize,
    },

    /// A dimension or length did not match the expected value.
    #[error("dimension mismatch: `{name}` expected {expected}, got {got}")]
    DimensionMismatch {
        /// Name of the offending dimension.
        name: &'static str,
        /// Expected value.
        expected: usize,
        /// Actual value.
        got: usize,
    },

    /// A value is not finite.
    #[error("non-finite value in `{name}` at index {index}: {value}")]
    NonFiniteValue {
        /// Name of the offending field.
        name: &'static str,
        /// Index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
    },

    /// The pruning threshold is outside the valid range.
    #[error("invalid pruning threshold: {value} (must be in [{min}, {max}])")]
    InvalidPruningThreshold {
        /// Offending threshold value.
        value: f64,
        /// Minimum permitted value.
        min: f64,
        /// Maximum permitted value.
        max: f64,
    },

    /// Pruning removed every oscillator.
    #[error("pruning removed all {n} oscillators; reduce the threshold")]
    AllPruned {
        /// Number of oscillators that were pruned.
        n: usize,
    },

    /// The coupling matrix has an invalid structure.
    #[error("invalid coupling matrix: {reason}")]
    InvalidCoupling {
        /// Description of the structural problem.
        reason: String,
    },

    /// A numeric routine received malformed or degenerate input.
    #[error("invalid input: {reason}")]
    InvalidInput {
        /// Description of the problem.
        reason: String,
    },

    /// An error from the dynamics layer.
    #[error("dynamics error: {0}")]
    Dynamics(#[from] prin_dynamics::StateError),

    /// An error from the integrator layer.
    #[error("integration error: {0}")]
    Integration(#[from] prin_dynamics::IntegrateError),

    /// An error from the metrics layer.
    #[error("metric error: {0}")]
    Metric(#[from] prin_metrics::MetricError),

    /// An error from the sparse matrix layer.
    #[error("sparse coupling error: {reason}")]
    SparseCoupling {
        /// Description of the failure.
        reason: String,
    },

    /// An error from the fused mean-field RK4 kernel dispatch layer
    /// (`prin_kernels::mean_field_rk4`).
    #[error("mean-field kernel error: {0}")]
    MeanFieldKernel(#[from] prin_kernels::mean_field_rk4::MeanFieldRk4Error),

    /// An error from the fused discrete-step kernel dispatch layer
    /// (`prin_kernels::discrete_step`).
    #[error("discrete-step kernel error: {0}")]
    DiscreteStepKernel(#[from] prin_kernels::discrete_step::DiscreteStepError),

    /// An error from the sparse k-NN coupling kernel dispatch layer
    /// (`prin_kernels::sparse_knn`).
    #[error("sparse k-NN kernel error: {0}")]
    SparseKnnKernel(#[from] prin_kernels::sparse_knn::SparseKnnError),
}

impl SimError {
    /// Construct an [`SimError::InvalidInput`] from any string-like reason.
    pub fn invalid_input(reason: impl Into<String>) -> Self {
        Self::InvalidInput {
            reason: reason.into(),
        }
    }
}

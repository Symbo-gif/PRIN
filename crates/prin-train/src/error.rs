//! Typed errors for trainable-primitive construction and state contracts.

use thiserror::Error;

/// Errors raised by [`crate::bands`] and [`crate::layers`] module construction,
/// parameter validation, and state contracts.
#[derive(Debug, Error, PartialEq)]
pub enum TrainError {
    /// A band or oscillator population was configured with zero size.
    #[error("{name} requires at least one oscillator, got 0")]
    EmptyBand {
        /// Name of the offending band/population.
        name: &'static str,
    },

    /// A tensor did not have the expected shape.
    #[error("{name} expected shape {expected:?}, got {got:?}")]
    ShapeMismatch {
        /// Name of the offending tensor.
        name: &'static str,
        /// Expected shape.
        expected: Vec<usize>,
        /// Actual shape.
        got: Vec<usize>,
    },

    /// A scalar hyperparameter was non-finite.
    #[error("non-finite parameter `{name}`: {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// A timestep was non-finite or non-positive.
    #[error("invalid timestep dt = {value}, must be finite and > 0")]
    InvalidTimestep {
        /// Offending value.
        value: f64,
    },

    /// (`strict-checks`) A tensor contained a non-finite value.
    #[error("non-finite value in `{name}`")]
    NonFiniteState {
        /// Name of the offending tensor.
        name: &'static str,
    },

    /// A feedback-inhibition top-`k` winner count was zero.
    #[error("k must be >= 1, got {k}")]
    InvalidTopK {
        /// Offending value.
        k: usize,
    },

    /// A sparsity fraction fell outside `(0, 1]`.
    #[error("sparsity must be in (0, 1], got {value}")]
    InvalidSparsity {
        /// Offending value.
        value: f64,
    },

    /// A Holomorphic Equilibrium Propagation nudge strength `beta` was
    /// non-positive or non-finite.
    #[error("beta must be finite and > 0, got {value}")]
    InvalidBeta {
        /// Offending value.
        value: f64,
    },

    /// An integration step count was zero.
    #[error("{name} must be >= 1, got {value}")]
    InvalidStepCount {
        /// Name of the offending parameter.
        name: &'static str,
        /// Offending value.
        value: usize,
    },

    /// An optimizer learning rate was negative or non-finite.
    #[error("Invalid learning rate: {value}")]
    InvalidLearningRate {
        /// Offending value.
        value: f64,
    },

    /// An optimizer momentum factor was negative or non-finite.
    #[error("Invalid momentum value: {value}")]
    InvalidMomentum {
        /// Offending value.
        value: f64,
    },

    /// An optimizer weight-decay coefficient was negative or non-finite.
    #[error("Invalid weight_decay value: {value}")]
    InvalidWeightDecay {
        /// Offending value.
        value: f64,
    },

    /// A `SyncGd` synchronization-penalty weight was negative or non-finite.
    #[error("Invalid sync_penalty value: {value}")]
    InvalidSyncPenalty {
        /// Offending value.
        value: f64,
    },

    /// A `SyncGd` critical order-parameter threshold fell outside `[0, 1]`.
    #[error("critical_order must be in [0, 1], got {value}")]
    InvalidCriticalOrder {
        /// Offending value.
        value: f64,
    },

    /// A `Rip` target amplitude was non-positive or non-finite.
    #[error("target_amplitude must be positive, got {value}")]
    InvalidTargetAmplitude {
        /// Offending value.
        value: f64,
    },

    /// A `Scalr` minimum learning-rate fraction fell outside `[0, 1]`.
    #[error("r_min must be in [0, 1], got {value}")]
    InvalidRMin {
        /// Offending value.
        value: f64,
    },

    /// A `Scalr` synchronization-sensitivity exponent was non-positive or
    /// non-finite.
    #[error("alpha must be positive, got {value}")]
    InvalidAlpha {
        /// Offending value.
        value: f64,
    },
}

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
}

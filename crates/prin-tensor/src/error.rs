//! Typed errors for tensor decomposition.

use thiserror::Error;

/// Errors raised by tensor decomposition operations.
///
/// Every public function validates its inputs at the boundary and returns a
/// typed variant; decomposition functions never panic on invalid input.
#[derive(Debug, Error, PartialEq)]
pub enum TensorError {
    /// An input tensor is empty (zero elements).
    #[error("tensor operation `{op}` requires a non-empty input")]
    EmptyInput {
        /// Name of the operation that rejected the input.
        op: &'static str,
    },

    /// An input value is not finite (NaN or infinite).
    #[error("tensor operation `{op}` encountered non-finite value at flat index {index}: {value}")]
    NonFiniteValue {
        /// Name of the operation that rejected the input.
        op: &'static str,
        /// Flat index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
    },

    /// A dimension is zero where a positive size is required.
    #[error("tensor operation `{op}` requires dimension {mode} > 0, got {size}")]
    ZeroDimension {
        /// Name of the operation.
        op: &'static str,
        /// Mode (axis) index.
        mode: usize,
        /// Offending dimension size.
        size: usize,
    },

    /// A rank specification is invalid (zero or exceeds the mode dimension).
    #[error("tensor operation `{op}` invalid rank {rank} for mode {mode} of dimension {dim}")]
    InvalidRank {
        /// Name of the operation.
        op: &'static str,
        /// Mode (axis) index.
        mode: usize,
        /// Requested rank.
        rank: usize,
        /// Dimension of the mode.
        dim: usize,
    },

    /// The number of components (CP rank) is invalid.
    #[error("tensor operation `{op}` requires at least 1 component, got {components}")]
    InvalidComponents {
        /// Name of the operation.
        op: &'static str,
        /// Requested number of components.
        components: usize,
    },

    /// Shape mismatch between operands.
    #[error("tensor operation `{op}` shape mismatch: expected {expected}, got {got}")]
    ShapeMismatch {
        /// Name of the operation.
        op: &'static str,
        /// Expected shape description.
        expected: String,
        /// Actual shape description.
        got: String,
    },

    /// ALS did not converge within the allowed iterations.
    #[error("tensor operation `{op}` did not converge after {iterations} iterations (final relative change {final_change:e})")]
    NonConvergence {
        /// Name of the operation.
        op: &'static str,
        /// Number of iterations performed.
        iterations: usize,
        /// Final relative change observed.
        final_change: f64,
    },

    /// A tolerance parameter is invalid (negative or NaN).
    #[error("tensor operation `{op}` invalid tolerance `{name}` = {value}")]
    InvalidTolerance {
        /// Name of the operation.
        op: &'static str,
        /// Name of the tolerance parameter.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// The maximum iteration count is invalid (zero).
    #[error("tensor operation `{op}` requires max_iter >= 1, got {max_iter}")]
    InvalidMaxIter {
        /// Name of the operation.
        op: &'static str,
        /// Offending value.
        max_iter: usize,
    },

    /// A mode index is out of range for the tensor.
    #[error("tensor operation `{op}` mode {mode} is out of range for tensor with {ndim} modes")]
    InvalidMode {
        /// Name of the operation.
        op: &'static str,
        /// Offending mode index.
        mode: usize,
        /// Number of modes in the tensor.
        ndim: usize,
    },

    /// A linear algebra operation failed (e.g., SVD did not converge).
    #[error("tensor operation `{op}` linear algebra failure: {message}")]
    LinearAlgebraFailed {
        /// Name of the operation.
        op: &'static str,
        /// Description of the failure.
        message: String,
    },

    /// The tensor order (number of modes) is invalid for the operation.
    #[error("tensor operation `{op}` requires at least {required} modes, got {got}")]
    InsufficientModes {
        /// Name of the operation.
        op: &'static str,
        /// Minimum number of modes required.
        required: usize,
        /// Actual number of modes.
        got: usize,
    },

    /// A mode-n product matrix has incompatible dimensions.
    #[error(
        "tensor operation `{op}` mode-{mode} product matrix has {got} rows, expected {expected}"
    )]
    ModeProductDimMismatch {
        /// Name of the operation.
        op: &'static str,
        /// Mode index.
        mode: usize,
        /// Expected number of rows (mode dimension).
        expected: usize,
        /// Actual number of rows.
        got: usize,
    },
}

/// Validate that every element of a slice is finite.
///
/// # Errors
///
/// Returns [`TensorError::NonFiniteValue`] for the first non-finite entry.
pub(crate) fn require_finite(op: &'static str, values: &[f64]) -> Result<(), TensorError> {
    for (index, &value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(TensorError::NonFiniteValue { op, index, value });
        }
    }
    Ok(())
}

/// Validate that a shape has no zero dimensions.
///
/// # Errors
///
/// Returns [`TensorError::ZeroDimension`] for the first zero-sized mode.
pub(crate) fn require_positive_dims(op: &'static str, shape: &[usize]) -> Result<(), TensorError> {
    for (mode, &size) in shape.iter().enumerate() {
        if size == 0 {
            return Err(TensorError::ZeroDimension { op, mode, size });
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn require_finite_accepts_finite_values() {
        assert!(require_finite("test", &[0.0, 1.0, -2.5]).is_ok());
    }

    #[test]
    fn require_finite_rejects_nan() {
        let err = require_finite("hosvd", &[0.0, f64::NAN]).unwrap_err();
        assert!(matches!(
            err,
            TensorError::NonFiniteValue {
                op: "hosvd",
                index: 1,
                ..
            }
        ));
    }

    #[test]
    fn require_finite_rejects_infinity() {
        let err = require_finite("cp_als", &[f64::INFINITY]).unwrap_err();
        assert!(matches!(
            err,
            TensorError::NonFiniteValue {
                op: "cp_als",
                index: 0,
                ..
            }
        ));
    }

    #[test]
    fn require_positive_dims_accepts_valid() {
        assert!(require_positive_dims("test", &[3, 4, 5]).is_ok());
    }

    #[test]
    fn require_positive_dims_rejects_zero() {
        let err = require_positive_dims("hosvd", &[3, 0, 5]).unwrap_err();
        assert_eq!(
            err,
            TensorError::ZeroDimension {
                op: "hosvd",
                mode: 1,
                size: 0,
            }
        );
    }

    #[test]
    fn error_display_messages() {
        let err = TensorError::EmptyInput { op: "hosvd" };
        assert_eq!(
            err.to_string(),
            "tensor operation `hosvd` requires a non-empty input"
        );

        let err = TensorError::NonConvergence {
            op: "cp_als",
            iterations: 500,
            final_change: 1e-3,
        };
        assert!(err.to_string().contains("did not converge"));
        assert!(err.to_string().contains("500"));
    }
}

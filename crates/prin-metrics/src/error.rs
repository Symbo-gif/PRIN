//! Typed errors for metric computation.

use thiserror::Error;

/// Errors raised by synchronization and chimera metric computations.
///
/// Every public metric validates its inputs at the boundary and returns a typed
/// variant; metric functions never panic on invalid input.
#[derive(Debug, Error, PartialEq)]
pub enum MetricError {
    /// The input population is empty.
    #[error("metric `{metric}` requires a non-empty input")]
    EmptyInput {
        /// Name of the metric that rejected the input.
        metric: &'static str,
    },

    /// An input value is not finite (NaN or infinite).
    #[error("metric `{metric}` encountered non-finite value at index {index}: {value}")]
    NonFiniteValue {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
    },

    /// Fewer oscillators than the metric requires.
    #[error("metric `{metric}` requires at least {required} oscillators, got {got}")]
    InsufficientOscillators {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Minimum number of oscillators required.
        required: usize,
        /// Number of oscillators supplied.
        got: usize,
    },

    /// Two inputs that must have equal length do not.
    #[error("metric `{metric}` length mismatch: {got} != {expected}")]
    LengthMismatch {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Expected length.
        expected: usize,
        /// Actual length.
        got: usize,
    },

    /// A neighbour index is out of range for the population size.
    #[error("metric `{metric}` neighbour index {index} out of range for n = {n}")]
    NeighbourOutOfRange {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Offending neighbour index value.
        index: usize,
        /// Population size.
        n: usize,
    },

    /// A neighbour count `k` is invalid for the population size `n`.
    #[error("metric `{metric}` invalid neighbour count k = {k} for n = {n}")]
    InvalidNeighborCount {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Offending neighbour count.
        k: usize,
        /// Population size.
        n: usize,
    },

    /// A neighbour row has a different length than the others.
    #[error("metric `{metric}` neighbour row {row} has {got} entries, expected {expected}")]
    NeighborRowLengthMismatch {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Row index with the wrong length.
        row: usize,
        /// Expected row length (length of the first row).
        expected: usize,
        /// Actual row length.
        got: usize,
    },

    /// A scalar parameter is outside its valid range or non-finite.
    #[error("metric `{metric}` invalid parameter `{name}` = {value}")]
    InvalidParameter {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Name of the offending parameter.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// A window size is invalid (zero).
    #[error("metric `{metric}` invalid window size {window}")]
    InvalidWindow {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Offending window size.
        window: usize,
    },

    /// A trajectory length is not a multiple of the oscillator count.
    #[error("metric `{metric}` trajectory length {len} is not a multiple of n = {n}")]
    TrajectoryShape {
        /// Name of the metric that rejected the input.
        metric: &'static str,
        /// Trajectory length in elements.
        len: usize,
        /// Oscillator count per snapshot.
        n: usize,
    },
}

/// Conversion of [`prin_dynamics::StateError`] into the metrics error surface.
///
/// Used by the delegated k-NN index builder ([`crate::build_phase_knn`]) so
/// the public API only exposes [`MetricError`].
pub(crate) trait StateErrorExt {
    /// Convert into a [`MetricError`] attributed to `metric`.
    fn into_metric(self, metric: &'static str) -> MetricError;
}

impl StateErrorExt for prin_dynamics::StateError {
    fn into_metric(self, metric: &'static str) -> MetricError {
        match self {
            prin_dynamics::StateError::NonFiniteValue { index, value, .. } => {
                MetricError::NonFiniteValue {
                    metric,
                    index,
                    value,
                }
            }
            prin_dynamics::StateError::EmptyPopulation => MetricError::EmptyInput { metric },
            other => MetricError::InvalidParameter {
                metric,
                name: "k",
                value: match other {
                    prin_dynamics::StateError::InvalidKNeighbors { k, .. } => k as f64,
                    _ => -1.0,
                },
            },
        }
    }
}

/// Validate that every element of `values` is finite.
///
/// # Errors
///
/// Returns [`MetricError::NonFiniteValue`] for the first non-finite entry.
pub(crate) fn require_finite(metric: &'static str, values: &[f64]) -> Result<(), MetricError> {
    for (index, &value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(MetricError::NonFiniteValue {
                metric,
                index,
                value,
            });
        }
    }
    Ok(())
}

/// Validate a neighbour index: `n` rows of equal length `k`, entries `< n`.
///
/// `k` must satisfy `1 <= k` when `require_nonempty_k` is set; `k < n` is
/// enforced whenever `n > 0`.
///
/// # Errors
///
/// Returns [`MetricError::LengthMismatch`] when the row count differs from
/// `n`, [`MetricError::NeighborRowLengthMismatch`] for ragged rows,
/// [`MetricError::InvalidNeighborCount`] for an invalid `k`, and
/// [`MetricError::NeighbourOutOfRange`] for out-of-range entries.
pub(crate) fn validate_neighbors(
    metric: &'static str,
    neighbors: &[Vec<usize>],
    n: usize,
    require_nonempty_k: bool,
) -> Result<usize, MetricError> {
    if neighbors.len() != n {
        return Err(MetricError::LengthMismatch {
            metric,
            expected: n,
            got: neighbors.len(),
        });
    }
    let k = neighbors.first().map_or(0, Vec::len);
    if require_nonempty_k && k == 0 {
        return Err(MetricError::InvalidNeighborCount { metric, k, n });
    }
    if n > 0 && k >= n {
        return Err(MetricError::InvalidNeighborCount { metric, k, n });
    }
    for (row, entries) in neighbors.iter().enumerate() {
        if entries.len() != k {
            return Err(MetricError::NeighborRowLengthMismatch {
                metric,
                row,
                expected: k,
                got: entries.len(),
            });
        }
        for &index in entries {
            if index >= n {
                return Err(MetricError::NeighbourOutOfRange { metric, index, n });
            }
        }
    }
    Ok(k)
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
        let err = require_finite("test", &[0.0, f64::NAN]).unwrap_err();
        assert!(matches!(
            err,
            MetricError::NonFiniteValue {
                metric: "test",
                index: 1,
                ..
            }
        ));
    }

    #[test]
    fn require_finite_rejects_infinity() {
        let err = require_finite("test", &[f64::INFINITY]).unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 0, .. }));
    }

    #[test]
    fn state_error_conversion_non_finite() {
        let err = prin_dynamics::StateError::NonFiniteValue {
            name: "phase",
            index: 3,
            value: f64::NAN,
        }
        .into_metric("build_phase_knn");
        assert!(matches!(
            err,
            MetricError::NonFiniteValue {
                metric: "build_phase_knn",
                index: 3,
                ..
            }
        ));
    }

    #[test]
    fn state_error_conversion_empty() {
        let err = prin_dynamics::StateError::EmptyPopulation.into_metric("build_phase_knn");
        assert_eq!(
            err,
            MetricError::EmptyInput {
                metric: "build_phase_knn"
            }
        );
    }

    #[test]
    fn state_error_conversion_invalid_k() {
        let err = prin_dynamics::StateError::InvalidKNeighbors { k: 5, n: 3 }
            .into_metric("build_phase_knn");
        assert_eq!(
            err,
            MetricError::InvalidParameter {
                metric: "build_phase_knn",
                name: "k",
                value: 5.0
            }
        );
    }

    #[test]
    fn state_error_conversion_other_variants() {
        let err = prin_dynamics::StateError::LengthMismatch {
            name: "phase",
            expected: 4,
            got: 3,
        }
        .into_metric("build_phase_knn");
        assert_eq!(
            err,
            MetricError::InvalidParameter {
                metric: "build_phase_knn",
                name: "k",
                value: -1.0
            }
        );
    }

    #[test]
    fn validate_neighbors_accepts_uniform_rows() {
        let neighbors = vec![vec![1, 2], vec![0, 2], vec![0, 1]];
        assert_eq!(validate_neighbors("test", &neighbors, 3, true).unwrap(), 2);
    }

    #[test]
    fn validate_neighbors_rejects_wrong_row_count() {
        let neighbors = vec![vec![1]];
        let err = validate_neighbors("test", &neighbors, 2, true).unwrap_err();
        assert!(matches!(err, MetricError::LengthMismatch { .. }));
    }

    #[test]
    fn validate_neighbors_rejects_ragged_rows() {
        let neighbors = vec![vec![1, 2], vec![0], vec![1]];
        let err = validate_neighbors("test", &neighbors, 3, true).unwrap_err();
        assert!(matches!(
            err,
            MetricError::NeighborRowLengthMismatch { row: 1, .. }
        ));
    }

    #[test]
    fn validate_neighbors_rejects_k_ge_n() {
        let neighbors = vec![vec![1, 2], vec![0, 2], vec![0, 1]];
        let err = validate_neighbors("test", &neighbors, 3, true).map(|_| ());
        // k = 2 < n = 3 is valid; build the failing case with k = n.
        assert!(err.is_ok());
        let bad = vec![vec![0, 1], vec![0, 1]];
        let err = validate_neighbors("test", &bad, 2, true).unwrap_err();
        assert!(matches!(err, MetricError::InvalidNeighborCount { .. }));
    }

    #[test]
    fn validate_neighbors_rejects_empty_k_when_required() {
        let neighbors: Vec<Vec<usize>> = vec![vec![], vec![]];
        let err = validate_neighbors("test", &neighbors, 2, true).unwrap_err();
        assert!(matches!(
            err,
            MetricError::InvalidNeighborCount { k: 0, .. }
        ));
    }

    #[test]
    fn validate_neighbors_allows_empty_k_when_optional() {
        let neighbors: Vec<Vec<usize>> = vec![vec![], vec![]];
        assert_eq!(validate_neighbors("test", &neighbors, 2, false).unwrap(), 0);
    }

    #[test]
    fn validate_neighbors_rejects_out_of_range_index() {
        let neighbors = vec![vec![5], vec![0]];
        let err = validate_neighbors("test", &neighbors, 2, true).unwrap_err();
        assert!(matches!(
            err,
            MetricError::NeighbourOutOfRange { index: 5, n: 2, .. }
        ));
    }
}

//! k-nearest-phase-neighbour index for measurement use.
//!
//! Rebuild of PRINet 3.0 `core/measurement.py::build_phase_knn`. The index
//! algorithm itself lives in `prin-dynamics` (one algorithm, one
//! implementation); this module provides the measurement-facing wrapper with
//! PRINet 3.0's user contract: `1 ≤ k < N`.

use crate::error::{MetricError, StateErrorExt};

/// Build a k-nearest-phase-neighbour index for measurement use.
///
/// Returns an index suitable for [`crate::sparse_mean_phase_coherence`],
/// [`crate::sparse_synchronization_energy`], [`crate::local_order_parameter`],
/// and [`crate::chimera_index`]: one row of `k` oscillator indices per
/// oscillator (the phase-nearest neighbours on the circle, excluding self).
/// The algorithm is delegated to
/// [`prin_dynamics::state::build_phase_knn_index`].
///
/// # Errors
///
/// Returns [`MetricError::InvalidNeighborCount`] for `k < 1` or `k >= n`,
/// [`MetricError::EmptyInput`] for an empty population, and the underlying
/// non-finiteness errors surfaced as [`MetricError::NonFiniteValue`].
///
/// # Example
///
/// ```
/// use prin_metrics::build_phase_knn;
///
/// let phase = [0.0_f64, 0.1, 3.0, 3.1];
/// let nbr = build_phase_knn(&phase, 1).unwrap();
/// // Nearest phase-neighbour of oscillator 0 is oscillator 1.
/// assert_eq!(nbr[0], vec![1]);
/// ```
pub fn build_phase_knn(phase: &[f64], k: usize) -> Result<Vec<Vec<usize>>, MetricError> {
    let n = phase.len();
    if n == 0 {
        return Err(MetricError::EmptyInput {
            metric: "build_phase_knn",
        });
    }
    if k < 1 || k >= n {
        return Err(MetricError::InvalidNeighborCount {
            metric: "build_phase_knn",
            k,
            n,
        });
    }
    prin_dynamics::state::build_phase_knn_index(phase, k)
        .map_err(|e| e.into_metric("build_phase_knn"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::TAU;

    #[test]
    fn build_phase_knn_returns_k_neighbours_without_self() {
        let phase = [0.1_f64, 0.9, 1.8, 2.6, 3.5, 4.4, 5.2, 6.0];
        let nbr = build_phase_knn(&phase, 3).unwrap();
        assert_eq!(nbr.len(), 8);
        for (i, row) in nbr.iter().enumerate() {
            assert_eq!(row.len(), 3);
            assert!(!row.contains(&i), "row {i} contains self");
            for &j in row {
                assert!(j < 8);
            }
        }
    }

    #[test]
    fn build_phase_knn_neighbours_are_phase_nearest() {
        // Phases spread around the full circle: sorted-ring neighbours are
        // the circular neighbours (i ± 1 mod N).
        let n = 6usize;
        let phase: Vec<f64> = (0..n)
            .map(|i| TAU * (i as f64) / (n as f64) + 0.05)
            .collect();
        let nbr = build_phase_knn(&phase, 2).unwrap();
        for (i, row) in nbr.iter().enumerate() {
            let mut expected = vec![(i + n - 1) % n, (i + 1) % n];
            expected.sort_unstable();
            let mut got = row.clone();
            got.sort_unstable();
            assert_eq!(got, expected, "oscillator {i}");
        }
    }

    #[test]
    fn build_phase_knn_wraps_around_sorted_ring() {
        // k = 1 uses the single right offset in sorted order, so the largest
        // phase wraps back to the smallest phase's oscillator.
        let phase = [0.05_f64, 1.0, 2.0, 3.0, 4.0, 5.0, 6.2];
        let nbr = build_phase_knn(&phase, 1).unwrap();
        assert_eq!(nbr[6], vec![0]);
        assert_eq!(nbr[0], vec![1]);
    }

    #[test]
    fn build_phase_knn_matches_prin_dynamics_index() {
        let phase = [
            0.2_f64, 1.1, 2.0, 2.9, 3.6, 4.4, 5.1, 5.9, 0.6, 1.7, 3.9, 5.5,
        ];
        let ours = build_phase_knn(&phase, 3).unwrap();
        let theirs = prin_dynamics::state::build_phase_knn_index(&phase, 3).unwrap();
        assert_eq!(ours, theirs);
    }

    #[test]
    fn build_phase_knn_validation() {
        assert!(matches!(
            build_phase_knn(&[], 1).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            build_phase_knn(&[0.0, 1.0], 0).unwrap_err(),
            MetricError::InvalidNeighborCount { k: 0, .. }
        ));
        assert!(matches!(
            build_phase_knn(&[0.0, 1.0], 2).unwrap_err(),
            MetricError::InvalidNeighborCount { k: 2, n: 2, .. }
        ));
        assert!(matches!(
            build_phase_knn(&[0.0, f64::NAN, 1.0], 1).unwrap_err(),
            MetricError::NonFiniteValue { index: 1, .. }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;
    use std::f64::consts::TAU;

    proptest! {
        #[test]
        fn build_phase_knn_invariants(
            phase in prop::collection::vec(0.0_f64..TAU, 3..=32),
            k_fraction in 0.1_f64..0.9,
        ) {
            let n = phase.len();
            let k = ((n as f64) * k_fraction).floor() as usize;
            prop_assume!((1..n).contains(&k));
            let nbr = build_phase_knn(&phase, k).unwrap();
            prop_assert_eq!(nbr.len(), n);
            for (i, row) in nbr.iter().enumerate() {
                prop_assert_eq!(row.len(), k);
                prop_assert!(!row.contains(&i));
                for &j in row {
                    prop_assert!(j < n);
                }
            }
        }
    }
}

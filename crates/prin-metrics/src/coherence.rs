//! Phase coherence metrics (full and sparse).
//!
//! Rebuild of PRINet 3.0 `core/measurement.py::mean_phase_coherence`,
//! `phase_coherence_matrix`, and `sparse_mean_phase_coherence`. All paths run
//! in f64 (PRINet computes these in `torch.float64`), so single-runtime
//! parity targets `rtol = 1e-10`.
//!
//! Identity preserved from PRINet 3.0: for `N ≥ 2`,
//! `C = (N·r² − 1) / (N − 1)` where `r` is the Kuramoto order parameter
//! (cross-checked in tests).

use num_complex::Complex64;
use rayon::prelude::*;

use crate::error::{require_finite, validate_neighbors, MetricError};

/// Compute the mean pairwise phase coherence.
///
/// `C = (2 / N(N−1)) Σ_{i<j} cos(φᵢ − φⱼ)`; values near `1` indicate
/// synchronization, values near `0` incoherence. The explicit upper-triangle
/// sum mirrors PRINet 3.0's masked `(cos_diff * mask).sum()` so reduction
/// noise stays minimal. The result is clamped to `[-1, 1]` (exact range;
/// floating-point accumulation can exceed it by ~1 ulp).
///
/// # Errors
///
/// Returns [`MetricError::InsufficientOscillators`] for fewer than two
/// oscillators and [`MetricError::NonFiniteValue`] for a non-finite phase.
///
/// # Example
///
/// ```
/// use prin_metrics::mean_phase_coherence;
///
/// let phase = [0.0_f64, 0.1, -0.1, 0.05];
/// let c = mean_phase_coherence(&phase).unwrap();
/// assert!(c > 0.9); // nearly synchronized
/// ```
pub fn mean_phase_coherence(phase: &[f64]) -> Result<f64, MetricError> {
    let n = phase.len();
    if n < 2 {
        return Err(MetricError::InsufficientOscillators {
            metric: "mean_phase_coherence",
            required: 2,
            got: n,
        });
    }
    require_finite("mean_phase_coherence", phase)?;
    let mut sum = 0.0_f64;
    for i in 0..n {
        for j in (i + 1)..n {
            sum += (phase[i] - phase[j]).cos();
        }
    }
    let n_pairs = (n * (n - 1)) as f64 / 2.0;
    Ok((sum / n_pairs).clamp(-1.0, 1.0))
}

/// Compute the full pairwise phase coherence matrix.
///
/// Returns `C[i, j] = cos(φᵢ − φⱼ)` in row-major order (length `N·N`),
/// usable for identifying clusters of synchronized oscillators.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for an empty slice and
/// [`MetricError::NonFiniteValue`] for a non-finite phase.
///
/// # Example
///
/// ```
/// use prin_metrics::phase_coherence_matrix;
///
/// let matrix = phase_coherence_matrix(&[0.0_f64, 0.0]).unwrap();
/// assert_eq!(matrix, vec![1.0, 1.0, 1.0, 1.0]);
/// ```
pub fn phase_coherence_matrix(phase: &[f64]) -> Result<Vec<f64>, MetricError> {
    if phase.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "phase_coherence_matrix",
        });
    }
    require_finite("phase_coherence_matrix", phase)?;
    Ok(phase
        .par_iter()
        .flat_map(|&pi| {
            phase
                .iter()
                .map(move |&pj| (pi - pj).cos())
                .collect::<Vec<_>>()
        })
        .collect())
}

/// Compute the sparse mean phase coherence (O(N·k) approximation).
///
/// For each oscillator `i`, the local coherence over its `k` neighbours is
/// `cᵢ = |1/k Σ_{j ∈ kNN(i)} exp(i(φⱼ − φᵢ))|`; the returned global
/// coherence is the mean of the `cᵢ`. This approximates
/// [`mean_phase_coherence`] at `O(N·k)` instead of `O(N²)`; the two agree at
/// `1` for fully synchronized phases but are otherwise distinct estimators.
/// Phase differences are wrapped to `(-π, π]` via
/// [`prin_dynamics::state::safe_phase_diff`] exactly as PRINet 3.0 does
/// (`atan2(sin Δ, cos Δ)`).
///
/// # Errors
///
/// Returns [`MetricError::InsufficientOscillators`] for fewer than two
/// oscillators, [`MetricError::NonFiniteValue`] for a non-finite phase, and
/// neighbour-index errors (see [`crate::error::MetricError`]) for malformed
/// `neighbors`.
///
/// # Example
///
/// ```
/// use prin_metrics::sparse_mean_phase_coherence;
///
/// let phase = vec![0.0_f64; 8]; // all equal → coherence 1
/// let neighbors: Vec<Vec<usize>> = (0..8)
///     .map(|i| vec![(i + 1) % 8, (i + 7) % 8])
///     .collect();
/// let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
/// assert!((c - 1.0).abs() < 1e-12);
/// ```
pub fn sparse_mean_phase_coherence(
    phase: &[f64],
    neighbors: &[Vec<usize>],
) -> Result<f64, MetricError> {
    let n = phase.len();
    if n < 2 {
        return Err(MetricError::InsufficientOscillators {
            metric: "sparse_mean_phase_coherence",
            required: 2,
            got: n,
        });
    }
    require_finite("sparse_mean_phase_coherence", phase)?;
    let k = validate_neighbors("sparse_mean_phase_coherence", neighbors, n, true)?;

    let total: f64 = phase
        .par_iter()
        .enumerate()
        .map(|(i, &phi_i)| {
            let acc: Complex64 = neighbors[i]
                .iter()
                .map(|&j| {
                    let delta = prin_dynamics::state::safe_phase_diff(phase[j], phi_i);
                    Complex64::new(delta.cos(), delta.sin())
                })
                .sum();
            (acc / (k as f64)).norm()
        })
        .sum();
    Ok((total / (n as f64)).min(1.0))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    fn ring_neighbors(n: usize, half: usize) -> Vec<Vec<usize>> {
        (0..n)
            .map(|i| {
                let mut row = Vec::with_capacity(2 * half);
                for d in 1..=half {
                    row.push((i + n - d) % n);
                    row.push((i + d) % n);
                }
                row
            })
            .collect()
    }

    #[test]
    fn coherence_synchronized_is_one() {
        let c = mean_phase_coherence(&[2.0_f64; 16]).unwrap();
        assert!((c - 1.0).abs() < 1e-14);
    }

    #[test]
    fn coherence_antiphase_is_minus_one() {
        let c = mean_phase_coherence(&[0.0, PI]).unwrap();
        assert!((c + 1.0).abs() < 1e-15);
    }

    #[test]
    fn coherence_matches_order_parameter_identity() {
        // C = (N r² − 1) / (N − 1) — independent cross-check of the pair sum.
        let phase = [0.2_f64, 1.1, 2.0, 2.9, 3.6, 4.4, 5.1, 5.9, 0.6, 1.7];
        let c = mean_phase_coherence(&phase).unwrap();
        let r = crate::order::kuramoto_order_parameter(&phase).unwrap();
        let n = phase.len() as f64;
        let expected = (n * r * r - 1.0) / (n - 1.0);
        assert!((c - expected).abs() < 1e-10, "c = {c}, expected {expected}");
    }

    #[test]
    fn coherence_rejects_single_oscillator() {
        let err = mean_phase_coherence(&[1.0]).unwrap_err();
        assert_eq!(
            err,
            MetricError::InsufficientOscillators {
                metric: "mean_phase_coherence",
                required: 2,
                got: 1
            }
        );
    }

    #[test]
    fn coherence_rejects_non_finite() {
        let err = mean_phase_coherence(&[0.0, f64::NEG_INFINITY]).unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 1, .. }));
    }

    #[test]
    fn coherence_is_clamped_to_closed_interval() {
        let c = mean_phase_coherence(&[0.0, 1e-17]).unwrap();
        assert!((-1.0..=1.0).contains(&c));
    }

    #[test]
    fn coherence_matrix_diagonal_and_symmetry() {
        let phase = [0.1_f64, 0.5, 1.2, 2.8];
        let m = phase_coherence_matrix(&phase).unwrap();
        assert_eq!(m.len(), 16);
        for i in 0..4 {
            assert!((m[i * 4 + i] - 1.0).abs() < 1e-15);
            for j in 0..4 {
                let expected = (phase[i] - phase[j]).cos();
                assert!((m[i * 4 + j] - expected).abs() < 1e-15);
                assert!((m[i * 4 + j] - m[j * 4 + i]).abs() < 1e-14);
            }
        }
    }

    #[test]
    fn coherence_matrix_rejects_empty_and_non_finite() {
        assert!(matches!(
            phase_coherence_matrix(&[]).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            phase_coherence_matrix(&[0.0, f64::NAN]).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn sparse_coherence_synchronized_is_one() {
        let phase = vec![0.9_f64; 12];
        let neighbors = ring_neighbors(12, 2);
        let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
        assert!((c - 1.0).abs() < 1e-14);
    }

    #[test]
    fn sparse_coherence_matches_hand_computed_case() {
        // N = 3, k = 1 with neighbour of i = (i + 1) mod 3.
        let phase = [0.0_f64, 1.0, 2.0];
        let neighbors = vec![vec![1], vec![2], vec![0]];
        let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
        // Each local coherence is |exp(iΔ)| = 1 for a single neighbour.
        assert!((c - 1.0).abs() < 1e-14);
    }

    #[test]
    fn sparse_coherence_two_cluster_state() {
        // Two anti-phase clusters of two; ring neighbours stay inside a
        // cluster for oscillators 0,1 (neighbours 1,0) and 2,3 (neighbours 3,2).
        let phase = [0.0_f64, 0.0, PI, PI];
        let neighbors = vec![vec![1], vec![0], vec![3], vec![2]];
        let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
        assert!((c - 1.0).abs() < 1e-14);
        // Full coherence of the same state: within-cluster pairs give +1,
        // cross-cluster pairs −1 → C = (2 − 4)/6 = −1/3 (matches the
        // (N r² − 1)/(N − 1) identity with r = 0).
        let full = mean_phase_coherence(&phase).unwrap();
        assert!((full + 1.0 / 3.0).abs() < 1e-14);
    }

    #[test]
    fn sparse_coherence_rejects_single_oscillator() {
        let err = sparse_mean_phase_coherence(&[0.0], &[vec![]]).unwrap_err();
        assert!(matches!(
            err,
            MetricError::InsufficientOscillators { required: 2, .. }
        ));
    }

    #[test]
    fn sparse_coherence_rejects_bad_neighbors() {
        let phase = [0.0_f64, 1.0, 2.0];
        // Wrong row count.
        let err = sparse_mean_phase_coherence(&phase, &[vec![1], vec![0]]).unwrap_err();
        assert!(matches!(err, MetricError::LengthMismatch { .. }));
        // Out-of-range index.
        let err = sparse_mean_phase_coherence(&phase, &[vec![7], vec![0], vec![1]]).unwrap_err();
        assert!(matches!(err, MetricError::NeighbourOutOfRange { .. }));
        // Empty neighbour rows.
        let err = sparse_mean_phase_coherence(&phase, &[vec![], vec![], vec![]]).unwrap_err();
        assert!(matches!(err, MetricError::InvalidNeighborCount { .. }));
    }

    #[test]
    fn sparse_coherence_rejects_non_finite_phase() {
        let err = sparse_mean_phase_coherence(&[0.0, f64::NAN, 1.0], &[vec![1], vec![0], vec![1]])
            .unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 1, .. }));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;
    use std::f64::consts::TAU;

    proptest! {
        #[test]
        fn coherence_in_closed_interval(
            phase in prop::collection::vec(0.0_f64..TAU, 2..=32),
        ) {
            let c = mean_phase_coherence(&phase).unwrap();
            prop_assert!((-1.0..=1.0).contains(&c), "c = {c}");
        }

        #[test]
        fn coherence_matches_identity(
            phase in prop::collection::vec(0.0_f64..TAU, 2..=24),
        ) {
            let c = mean_phase_coherence(&phase).unwrap();
            let r = crate::order::kuramoto_order_parameter(&phase).unwrap();
            let n = phase.len() as f64;
            let expected = (n * r * r - 1.0) / (n - 1.0);
            prop_assert!((c - expected).abs() < 1e-9, "c = {c}, expected {expected}");
        }

        #[test]
        fn sparse_coherence_in_unit_interval(
            phase in prop::collection::vec(0.0_f64..TAU, 4..=24),
        ) {
            let n = phase.len();
            let neighbors: Vec<Vec<usize>> = (0..n)
                .map(|i| vec![(i + 1) % n, (i + n - 1) % n])
                .collect();
            let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
            prop_assert!((0.0..=1.0).contains(&c), "c = {c}");
        }
    }
}

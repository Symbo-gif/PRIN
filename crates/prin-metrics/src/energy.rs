//! Synchronization energy (full and sparse).
//!
//! Rebuild of PRINet 3.0 `core/measurement.py::synchronization_energy` and
//! `sparse_synchronization_energy`. All paths run in f64 (PRINet computes
//! these in `torch.float64`), so single-runtime parity targets
//! `rtol = 1e-10`.
//!
//! Normalization semantics preserved from PRINet 3.0: the dense default uses
//! `1/N` off-diagonal coupling (zero diagonal), while the sparse variant uses
//! `K/k` per edge — the same `1/N` vs `1/k` distinction documented for the
//! dynamics crate.

use crate::error::{require_finite, validate_neighbors, MetricError};

/// Compute the dense synchronization energy.
///
/// `E(φ, A) = −Σ_{i,j} K_{ij} cos(φᵢ − φⱼ) Aᵢ Aⱼ`; lower energy indicates
/// greater synchronization. When `coupling_matrix` is `None`, uniform
/// all-to-all coupling `K_{ij} = 1/N` (off-diagonal) with zero diagonal is
/// used, matching PRINet 3.0's default. A supplied matrix is row-major
/// `N × N`.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty inputs,
/// [`MetricError::LengthMismatch`] for mismatched `phase`/`amplitude` or a
/// wrong-length matrix, [`MetricError::NonFiniteValue`] for non-finite
/// entries.
///
/// # Example
///
/// ```
/// use prin_metrics::synchronization_energy;
///
/// // Fully synchronized unit amplitudes: E = −Σ_{i≠j} (1/N) = −(N−1).
/// let e = synchronization_energy(&[0.0_f64; 4], &[1.0_f64; 4], None).unwrap();
/// assert!((e + 3.0).abs() < 1e-12);
/// ```
pub fn synchronization_energy(
    phase: &[f64],
    amplitude: &[f64],
    coupling_matrix: Option<&[f64]>,
) -> Result<f64, MetricError> {
    let n = phase.len();
    if n == 0 {
        return Err(MetricError::EmptyInput {
            metric: "synchronization_energy",
        });
    }
    if phase.len() != amplitude.len() {
        return Err(MetricError::LengthMismatch {
            metric: "synchronization_energy",
            expected: phase.len(),
            got: amplitude.len(),
        });
    }
    require_finite("synchronization_energy", phase)?;
    require_finite("synchronization_energy", amplitude)?;

    let mut energy = 0.0_f64;
    match coupling_matrix {
        Some(matrix) => {
            if matrix.len() != n * n {
                return Err(MetricError::LengthMismatch {
                    metric: "synchronization_energy",
                    expected: n * n,
                    got: matrix.len(),
                });
            }
            require_finite("synchronization_energy", matrix)?;
            for i in 0..n {
                for j in 0..n {
                    let k_ij = matrix[i * n + j];
                    if k_ij != 0.0 {
                        energy -= k_ij * (phase[i] - phase[j]).cos() * amplitude[i] * amplitude[j];
                    }
                }
            }
        }
        None => {
            let inv_n = 1.0 / (n as f64);
            for i in 0..n {
                for j in 0..n {
                    if i != j {
                        energy -= inv_n * (phase[i] - phase[j]).cos() * amplitude[i] * amplitude[j];
                    }
                }
            }
        }
    }
    Ok(energy)
}

/// Compute the sparse synchronization energy over k-NN edges (O(N·k)).
///
/// `E_sparse = −(K/k) Σ_i Σ_{j ∈ kNN(i)} cos(φᵢ − φⱼ) Aᵢ Aⱼ`, normalized so
/// the per-oscillator energy magnitude is comparable to the dense
/// [`synchronization_energy`]. Phase differences are wrapped to `(-π, π]`
/// via [`prin_dynamics::state::safe_phase_diff`] exactly as PRINet 3.0 does
/// before taking the cosine.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty inputs,
/// [`MetricError::LengthMismatch`] for mismatched `phase`/`amplitude`,
/// [`MetricError::NonFiniteValue`] for non-finite entries (including
/// `coupling_strength`), and neighbour-index errors for malformed
/// `neighbors`.
///
/// # Example
///
/// ```
/// use prin_metrics::sparse_synchronization_energy;
///
/// let phase = vec![0.0_f64; 6];
/// let amplitude = vec![1.0_f64; 6];
/// let neighbors: Vec<Vec<usize>> = (0..6)
///     .map(|i| vec![(i + 1) % 6, (i + 5) % 6])
///     .collect();
/// // Fully synchronized: E = −K·N.
/// let e = sparse_synchronization_energy(&phase, &amplitude, &neighbors, 1.0).unwrap();
/// assert!((e + 6.0).abs() < 1e-12);
/// ```
pub fn sparse_synchronization_energy(
    phase: &[f64],
    amplitude: &[f64],
    neighbors: &[Vec<usize>],
    coupling_strength: f64,
) -> Result<f64, MetricError> {
    let n = phase.len();
    if n == 0 {
        return Err(MetricError::EmptyInput {
            metric: "sparse_synchronization_energy",
        });
    }
    if phase.len() != amplitude.len() {
        return Err(MetricError::LengthMismatch {
            metric: "sparse_synchronization_energy",
            expected: phase.len(),
            got: amplitude.len(),
        });
    }
    if !coupling_strength.is_finite() {
        return Err(MetricError::NonFiniteValue {
            metric: "sparse_synchronization_energy",
            index: 0,
            value: coupling_strength,
        });
    }
    require_finite("sparse_synchronization_energy", phase)?;
    require_finite("sparse_synchronization_energy", amplitude)?;
    let k = validate_neighbors("sparse_synchronization_energy", neighbors, n, false)?;

    let k_eff = coupling_strength / (k.max(1)) as f64;
    let mut energy = 0.0_f64;
    for i in 0..n {
        for &j in &neighbors[i] {
            let delta = prin_dynamics::state::safe_phase_diff(phase[i], phase[j]);
            energy -= k_eff * delta.cos() * amplitude[i] * amplitude[j];
        }
    }
    Ok(energy)
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
    fn dense_energy_synchronized_unit_amplitudes() {
        let n = 8;
        let e = synchronization_energy(&vec![0.0; n], &vec![1.0; n], None).unwrap();
        // E = −Σ_{i≠j} (1/N)·1 = −N(N−1)/N = −(N−1).
        assert!((e + (n as f64 - 1.0)).abs() < 1e-13);
    }

    #[test]
    fn dense_energy_antiphase_pair() {
        let e = synchronization_energy(&[0.0, PI], &[1.0, 1.0], None).unwrap();
        // −(1/2)(cos(−π) + cos(π)) = −(1/2)(−2) = +1.
        assert!((e - 1.0).abs() < 1e-14);
    }

    #[test]
    fn dense_energy_explicit_matrix_matches_default() {
        let phase = [0.1_f64, 0.5, 1.2, 2.8];
        let amplitude = [1.0_f64, 0.8, 1.2, 0.9];
        let n = phase.len();
        let mut matrix = vec![1.0 / (n as f64); n * n];
        for i in 0..n {
            matrix[i * n + i] = 0.0;
        }
        let e_default = synchronization_energy(&phase, &amplitude, None).unwrap();
        let e_matrix = synchronization_energy(&phase, &amplitude, Some(&matrix)).unwrap();
        assert!((e_default - e_matrix).abs() < 1e-13);
    }

    #[test]
    fn dense_energy_rejects_bad_inputs() {
        assert!(matches!(
            synchronization_energy(&[], &[], None).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            synchronization_energy(&[0.0], &[1.0, 2.0], None).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
        assert!(matches!(
            synchronization_energy(&[0.0], &[f64::NAN], None).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            synchronization_energy(&[0.0, 1.0], &[1.0, 1.0], Some(&[0.0; 3])).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
        assert!(matches!(
            synchronization_energy(&[0.0, 1.0], &[1.0, 1.0], Some(&[0.0, 0.0, 0.0, f64::NAN]))
                .unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn sparse_energy_synchronized_is_minus_k_n() {
        let n = 6;
        let neighbors = ring_neighbors(n, 1); // k = 2
        let e =
            sparse_synchronization_energy(&vec![0.0; n], &vec![1.0; n], &neighbors, 1.5).unwrap();
        // E = −(K/k)·N·k = −K·N.
        assert!((e + 1.5 * (n as f64)).abs() < 1e-13);
    }

    #[test]
    fn sparse_energy_k_full_ratio_to_dense() {
        // With k = N−1 (all other oscillators) and K = 1, the sparse energy is
        // the dense default energy scaled by N/(N−1): dense uses 1/N per edge,
        // sparse uses K/k = 1/(N−1) per edge.
        let phase = [0.2_f64, 1.1, 2.0, 2.9, 3.6, 4.4, 5.1, 5.9];
        let amplitude = [1.0_f64, 1.1, 0.9, 1.0, 0.8, 1.2, 1.0, 0.9];
        let n = phase.len();
        let neighbors: Vec<Vec<usize>> = (0..n)
            .map(|i| (0..n).filter(|&j| j != i).collect())
            .collect();
        let e_sparse = sparse_synchronization_energy(&phase, &amplitude, &neighbors, 1.0).unwrap();
        let e_dense = synchronization_energy(&phase, &amplitude, None).unwrap();
        let ratio = (n as f64) / ((n - 1) as f64);
        assert!(
            (e_sparse - e_dense * ratio).abs() < 1e-12 * e_sparse.abs().max(1.0),
            "sparse {e_sparse}, dense·N/(N−1) {}",
            e_dense * ratio
        );
    }

    #[test]
    fn sparse_energy_zero_k_returns_zero() {
        let neighbors: Vec<Vec<usize>> = vec![vec![], vec![], vec![]];
        let e =
            sparse_synchronization_energy(&[0.0, 1.0, 2.0], &[1.0; 3], &neighbors, 2.0).unwrap();
        assert_eq!(e, 0.0);
    }

    #[test]
    fn sparse_energy_rejects_bad_inputs() {
        let neighbors = vec![vec![1], vec![0]];
        assert!(matches!(
            sparse_synchronization_energy(&[], &[], &[], 1.0).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            sparse_synchronization_energy(&[0.0, 1.0], &[1.0], &neighbors, 1.0).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
        assert!(matches!(
            sparse_synchronization_energy(&[0.0, 1.0], &[1.0, 1.0], &neighbors, f64::NAN)
                .unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            sparse_synchronization_energy(&[0.0, f64::NAN], &[1.0, 1.0], &neighbors, 1.0)
                .unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            sparse_synchronization_energy(&[0.0, 1.0], &[1.0, 1.0], &[vec![5], vec![0]], 1.0)
                .unwrap_err(),
            MetricError::NeighbourOutOfRange { .. }
        ));
    }
}

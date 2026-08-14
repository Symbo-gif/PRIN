//! CSR sparse coupling for large oscillator systems.
//!
//! [`SparseCoupling`] wraps a `sprs::CsMat<f64>` in compressed sparse row
//! format and provides the sparse matrix–vector products needed by Kuramoto-
//! style and Stuart–Landau–style coupling computations. Instead of materialising
//! the full `N × N` matrix (O(N²) memory), the CSR representation stores only
//! the non-zero entries (O(nnz) memory) and computes coupling contributions in
//! O(nnz) time per step.
//!
//! ## Coupling via trig decomposition
//!
//! For Kuramoto-style `sin(φ_j − φ_i)` coupling the product is *not* a plain
//! SpMV because the sine depends on both row and column indices. Using the
//! angle-difference identity
//!
//! ```text
//! sin(φ_j − φ_i) = sin φ_j cos φ_i − cos φ_j sin φ_i
//! ```
//!
//! the coupling sum decomposes into **two** standard SpMV operations:
//!
//! ```text
//! a = K · (r ⊙ sin φ)      b = K · (r ⊙ cos φ)
//! sin_sum_i  = cos φ_i · a_i − sin φ_i · b_i
//! cos_sum_i  = cos φ_i · b_i + sin φ_i · a_i
//! ```
//!
//! This is the key performance advantage: O(nnz) per step instead of O(N²).

use rayon::prelude::*;
use sprs::{CsMat, TriMat};

use crate::error::SimError;

/// CSR sparse coupling matrix for oscillator systems.
///
/// Stores an `N × N` coupling matrix in compressed sparse row format. Provides
/// SpMV-based coupling computations for Kuramoto and Stuart–Landau dynamics,
/// entry pruning, and memory measurement.
///
/// # Invariants
///
/// - The matrix is always square (`rows == cols == n`).
/// - All stored values are finite.
/// - The matrix is in CSR storage order.
#[derive(Clone, Debug)]
pub struct SparseCoupling {
    matrix: CsMat<f64>,
    n: usize,
}

impl SparseCoupling {
    /// Create a `SparseCoupling` from a pre-built CSR matrix.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the matrix is empty, non-square, or contains
    /// non-finite entries.
    pub fn new(matrix: CsMat<f64>) -> Result<Self, SimError> {
        let (rows, cols) = matrix.shape();
        if rows == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if rows != cols {
            return Err(SimError::DimensionMismatch {
                name: "coupling matrix",
                expected: rows,
                got: cols,
            });
        }
        for (i, &v) in matrix.data().iter().enumerate() {
            if !v.is_finite() {
                return Err(SimError::NonFiniteValue {
                    name: "coupling data",
                    index: i,
                    value: v,
                });
            }
        }
        Ok(Self { matrix, n: rows })
    }

    /// Build from raw CSR arrays.
    ///
    /// `indptr` has length `n + 1`, `indices` and `data` have length `nnz`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for dimension mismatches, non-finite values, or
    /// empty populations.
    pub fn from_csr(
        indptr: &[usize],
        indices: &[usize],
        data: &[f64],
        n: usize,
    ) -> Result<Self, SimError> {
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if indptr.len() != n + 1 {
            return Err(SimError::DimensionMismatch {
                name: "indptr",
                expected: n + 1,
                got: indptr.len(),
            });
        }
        let nnz = indptr[n];
        if indices.len() != nnz || data.len() != nnz {
            return Err(SimError::DimensionMismatch {
                name: "indices/data vs nnz",
                expected: nnz,
                got: indices.len(),
            });
        }
        for (i, &v) in data.iter().enumerate() {
            if !v.is_finite() {
                return Err(SimError::NonFiniteValue {
                    name: "coupling data",
                    index: i,
                    value: v,
                });
            }
        }
        let matrix = CsMat::new((n, n), indptr.to_vec(), indices.to_vec(), data.to_vec());
        Ok(Self { matrix, n })
    }

    /// Build from a dense row-major `N × N` matrix.
    ///
    /// Entries with absolute value below `threshold` are dropped.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for empty populations, non-square data, or
    /// non-finite entries.
    pub fn from_dense(dense: &[f64], n: usize, threshold: f64) -> Result<Self, SimError> {
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if dense.len() != n * n {
            return Err(SimError::DimensionMismatch {
                name: "dense matrix",
                expected: n * n,
                got: dense.len(),
            });
        }
        let mut tripmat = TriMat::new((n, n));
        for i in 0..n {
            for j in 0..n {
                let v = dense[i * n + j];
                if !v.is_finite() {
                    return Err(SimError::NonFiniteValue {
                        name: "dense matrix",
                        index: i * n + j,
                        value: v,
                    });
                }
                if v.abs() > threshold {
                    tripmat.add_triplet(i, j, v);
                }
            }
        }
        let matrix = tripmat.to_csr();
        Ok(Self { matrix, n })
    }

    /// Build a k-NN sparse coupling from phase-space nearest neighbours.
    ///
    /// Each oscillator couples to its `k` nearest phase neighbours with weight
    /// `strength / k`, matching the `SparseKnn` convention in `prin-dynamics`.
    /// The neighbour index is built via the sort-based O(N log N) algorithm
    /// from `prin-dynamics::state::build_phase_knn_index`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for empty populations, invalid `k`, or non-finite
    /// phases.
    pub fn from_knn(phases: &[f64], k: usize, strength: f64) -> Result<Self, SimError> {
        let n = phases.len();
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if k == 0 || k >= n {
            return Err(SimError::DimensionMismatch {
                name: "k",
                expected: n - 1,
                got: k,
            });
        }
        if !strength.is_finite() {
            return Err(SimError::NonFiniteValue {
                name: "strength",
                index: 0,
                value: strength,
            });
        }
        for (i, &p) in phases.iter().enumerate() {
            if !p.is_finite() {
                return Err(SimError::NonFiniteValue {
                    name: "phases",
                    index: i,
                    value: p,
                });
            }
        }

        let nbr_index =
            prin_dynamics::state::build_phase_knn_index(phases, k).map_err(SimError::Dynamics)?;
        let weight = strength / (k as f64);

        let mut tripmat = TriMat::new((n, n));
        for (i, nbrs) in nbr_index.iter().enumerate() {
            for &j in nbrs {
                tripmat.add_triplet(i, j, weight);
            }
        }
        let matrix = tripmat.to_csr();
        Ok(Self { matrix, n })
    }

    /// Build a ring-lattice coupling: each oscillator couples to `half_k`
    /// neighbours on each side with weight `strength / (2 * half_k)`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for empty populations or invalid `half_k`.
    pub fn from_ring(n: usize, half_k: usize, strength: f64) -> Result<Self, SimError> {
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        let degree = 2 * half_k;
        if degree == 0 || degree >= n {
            return Err(SimError::InvalidCoupling {
                reason: format!("degree {degree} must be in [1, {n})"),
            });
        }
        if !strength.is_finite() {
            return Err(SimError::NonFiniteValue {
                name: "strength",
                index: 0,
                value: strength,
            });
        }
        let weight = strength / (degree as f64);
        let mut tripmat = TriMat::new((n, n));
        for i in 0..n {
            for d in 1..=half_k {
                let left = (i + n - d) % n;
                let right = (i + d) % n;
                tripmat.add_triplet(i, left, weight);
                tripmat.add_triplet(i, right, weight);
            }
        }
        let matrix = tripmat.to_csr();
        Ok(Self { matrix, n })
    }

    /// Number of oscillators (matrix dimension).
    pub fn n_oscillators(&self) -> usize {
        self.n
    }

    /// Number of stored non-zero entries.
    pub fn nnz(&self) -> usize {
        self.matrix.nnz()
    }

    /// Borrow the underlying CSR matrix.
    pub fn as_csr(&self) -> &CsMat<f64> {
        &self.matrix
    }

    /// Sparsity ratio: fraction of zero entries in the full N×N matrix.
    pub fn sparsity(&self) -> f64 {
        let total = (self.n as f64) * (self.n as f64);
        1.0 - (self.matrix.nnz() as f64) / total
    }

    /// Approximate memory footprint in bytes.
    ///
    /// Counts the CSR data arrays (indptr, indices, data) only; does not
    /// include the `SparseCoupling` struct overhead.
    pub fn memory_bytes(&self) -> usize {
        let indptr_bytes = (self.n + 1) * std::mem::size_of::<usize>();
        let indices_bytes = self.matrix.nnz() * std::mem::size_of::<usize>();
        let data_bytes = self.matrix.nnz() * std::mem::size_of::<f64>();
        indptr_bytes + indices_bytes + data_bytes
    }

    /// Remove entries with absolute value at or below `threshold`.
    ///
    /// Returns a new [`SparseCoupling`] with the pruned matrix.
    pub fn prune(&self, threshold: f64) -> Result<Self, SimError> {
        let (rows, cols) = self.matrix.shape();
        let mut tripmat = TriMat::new((rows, cols));
        for (row_idx, row) in self.matrix.outer_iterator().enumerate() {
            for (col_idx, &val) in row.iter() {
                let _ = row_idx;
                if val.abs() > threshold {
                    tripmat.add_triplet(row_idx, col_idx, val);
                }
            }
        }
        let matrix = tripmat.to_csr();
        Self::new(matrix)
    }

    /// Compute Kuramoto-style sin/cos coupling sums via two SpMV operations.
    ///
    /// Given phases `φ`, amplitudes `r`, and coupling matrix `K`:
    ///
    /// ```text
    /// a = K · (r ⊙ sin φ)      b = K · (r ⊙ cos φ)
    /// sin_sum_i  = cos φ_i · a_i − sin φ_i · b_i
    /// cos_sum_i  = cos φ_i · b_i + sin φ_i · a_i
    /// ```
    ///
    /// Returns `(sin_sum, cos_sum)`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if `phases` or `amplitudes` has the wrong length.
    pub fn kuramoto_coupling(
        &self,
        phases: &[f64],
        amplitudes: &[f64],
    ) -> Result<(Vec<f64>, Vec<f64>), SimError> {
        let n = self.n;
        if phases.len() != n {
            return Err(SimError::DimensionMismatch {
                name: "phases",
                expected: n,
                got: phases.len(),
            });
        }
        if amplitudes.len() != n {
            return Err(SimError::DimensionMismatch {
                name: "amplitudes",
                expected: n,
                got: amplitudes.len(),
            });
        }

        let u: Vec<f64> = phases
            .par_iter()
            .zip(amplitudes.par_iter())
            .map(|(&p, &a)| {
                let (s, _c) = p.sin_cos();
                a * s
            })
            .collect();
        let v: Vec<f64> = phases
            .par_iter()
            .zip(amplitudes.par_iter())
            .map(|(&p, &a)| {
                let (_s, c) = p.sin_cos();
                a * c
            })
            .collect();

        let a_vec = spmv(&self.matrix, &u);
        let b_vec = spmv(&self.matrix, &v);

        let sin_sum: Vec<f64> = phases
            .par_iter()
            .zip(a_vec.par_iter())
            .zip(b_vec.par_iter())
            .map(|((&phi, &a_val), &b_val)| {
                let (si, ci) = phi.sin_cos();
                ci * a_val - si * b_val
            })
            .collect();
        let cos_sum: Vec<f64> = phases
            .par_iter()
            .zip(a_vec.par_iter())
            .zip(b_vec.par_iter())
            .map(|((&phi, &a_val), &b_val)| {
                let (si, ci) = phi.sin_cos();
                ci * b_val + si * a_val
            })
            .collect();
        Ok((sin_sum, cos_sum))
    }

    /// Compute Stuart–Landau-style diffusive coupling `C_i = Σ_j K_ij (z_j − z_i)`.
    ///
    /// Given complex phasors `z_j = r_j exp(i φ_j)`:
    ///
    /// ```text
    /// C_i = (K · z)_i − (K · 1)_i · z_i
    /// ```
    ///
    /// where `K · 1` is the row-sum vector. Returns `(C_re, C_im)`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if `phases` or `amplitudes` has the wrong length.
    pub fn stuart_landau_coupling(
        &self,
        phases: &[f64],
        amplitudes: &[f64],
    ) -> Result<(Vec<f64>, Vec<f64>), SimError> {
        let n = self.n;
        if phases.len() != n {
            return Err(SimError::DimensionMismatch {
                name: "phases",
                expected: n,
                got: phases.len(),
            });
        }
        if amplitudes.len() != n {
            return Err(SimError::DimensionMismatch {
                name: "amplitudes",
                expected: n,
                got: amplitudes.len(),
            });
        }

        let z_re: Vec<f64> = phases
            .par_iter()
            .zip(amplitudes.par_iter())
            .map(|(&p, &a)| {
                let (_s, c) = p.sin_cos();
                a * c
            })
            .collect();
        let z_im: Vec<f64> = phases
            .par_iter()
            .zip(amplitudes.par_iter())
            .map(|(&p, &a)| {
                let (s, _c) = p.sin_cos();
                a * s
            })
            .collect();

        let kz_re = spmv(&self.matrix, &z_re);
        let kz_im = spmv(&self.matrix, &z_im);

        let row_sums = row_sum(&self.matrix);

        let c_re: Vec<f64> = kz_re
            .par_iter()
            .zip(row_sums.par_iter())
            .zip(z_re.par_iter())
            .map(|((&kz, &rs), &zr)| kz - rs * zr)
            .collect();
        let c_im: Vec<f64> = kz_im
            .par_iter()
            .zip(row_sums.par_iter())
            .zip(z_im.par_iter())
            .map(|((&kz, &rs), &zi)| kz - rs * zi)
            .collect();
        Ok((c_re, c_im))
    }

    /// Extract the neighbor list from the CSR sparsity pattern.
    ///
    /// For each row `i`, returns the column indices of non-zero entries. This
    /// is used to feed spatial neighbor lists to `prin-metrics` chimera
    /// functions.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if any row has zero non-zero entries (an isolated
    /// oscillator cannot participate in neighbor-based metrics).
    pub fn neighbor_list(&self) -> Result<Vec<Vec<usize>>, SimError> {
        let mut neighbors = Vec::with_capacity(self.n);
        for (i, row) in self.matrix.outer_iterator().enumerate() {
            let row_nbrs: Vec<usize> = row.iter().map(|(j, _)| j).collect();
            if row_nbrs.is_empty() {
                return Err(SimError::InvalidCoupling {
                    reason: format!("oscillator {i} has no coupling entries (isolated)"),
                });
            }
            neighbors.push(row_nbrs);
        }
        Ok(neighbors)
    }

    /// Build a sub-matrix for a subset of oscillator indices.
    ///
    /// The returned matrix has dimension `kept.len() × kept.len()` and contains
    /// only the entries `K[kept[i], kept[j]]`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if `kept` is empty or contains out-of-range indices.
    pub fn submatrix(&self, kept: &[usize]) -> Result<Self, SimError> {
        let m = kept.len();
        if m == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        for (i, &idx) in kept.iter().enumerate() {
            if idx >= self.n {
                return Err(SimError::DimensionMismatch {
                    name: "submatrix index",
                    expected: self.n,
                    got: idx,
                });
            }
            let _ = i;
        }

        let mut tripmat = TriMat::new((m, m));
        for (new_i, &old_i) in kept.iter().enumerate() {
            let row = self
                .matrix
                .outer_view(old_i)
                .ok_or(SimError::SparseCoupling {
                    reason: format!("row {old_i} out of range"),
                })?;
            for (old_j, &val) in row.iter() {
                if let Some(new_j) = kept.iter().position(|&k| k == old_j) {
                    tripmat.add_triplet(new_i, new_j, val);
                }
            }
        }
        let matrix = tripmat.to_csr();
        Ok(Self { matrix, n: m })
    }
}

/// Sparse matrix–vector product `y = A · x` for a CSR matrix.
///
/// Uses rayon to parallelize the outer row loop via `par_bridge()` on the
/// CSR outer iterator. Each row's dot product is independent. Results are
/// placed by index to preserve ordering.
fn spmv(mat: &CsMat<f64>, x: &[f64]) -> Vec<f64> {
    let n = mat.rows();
    let mut y = vec![0.0_f64; n];
    let rows: Vec<_> = mat
        .outer_iterator()
        .enumerate()
        .par_bridge()
        .map(|(i, row)| {
            let mut acc = 0.0;
            for (j, &val) in row.iter() {
                acc += val * x[j];
            }
            (i, acc)
        })
        .collect();
    for (i, val) in rows {
        y[i] = val;
    }
    y
}

/// Compute the row-sum vector of a CSR matrix.
///
/// Uses rayon to parallelize the outer row loop via `par_bridge()`.
/// Results are placed by index to preserve ordering.
fn row_sum(mat: &CsMat<f64>) -> Vec<f64> {
    let n = mat.rows();
    let mut sums = vec![0.0_f64; n];
    let rows: Vec<_> = mat
        .outer_iterator()
        .enumerate()
        .par_bridge()
        .map(|(i, row)| (i, row.iter().map(|(_, &v)| v).sum()))
        .collect();
    for (i, val) in rows {
        sums[i] = val;
    }
    sums
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::TAU;

    fn ring_matrix(n: usize, half_k: usize, strength: f64) -> SparseCoupling {
        SparseCoupling::from_ring(n, half_k, strength).unwrap()
    }

    #[test]
    fn from_ring_basic() {
        let c = ring_matrix(6, 1, 2.0);
        assert_eq!(c.n_oscillators(), 6);
        assert_eq!(c.nnz(), 12);
    }

    #[test]
    fn from_csr_round_trip() {
        let indptr = vec![0, 2, 4, 6];
        let indices = vec![1, 2, 0, 2, 0, 1];
        let data = vec![0.5, 0.5, 0.5, 0.5, 0.5, 0.5];
        let c = SparseCoupling::from_csr(&indptr, &indices, &data, 3).unwrap();
        assert_eq!(c.n_oscillators(), 3);
        assert_eq!(c.nnz(), 6);
    }

    #[test]
    fn from_dense_with_threshold() {
        let dense = vec![0.0, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0];
        let c = SparseCoupling::from_dense(&dense, 3, 1e-12).unwrap();
        assert_eq!(c.nnz(), 4);
    }

    #[test]
    fn from_dense_threshold_drops_zeros() {
        let dense = vec![0.0; 9];
        let c = SparseCoupling::from_dense(&dense, 3, 0.0).unwrap();
        assert_eq!(c.nnz(), 0);
    }

    #[test]
    fn prune_removes_small_entries() {
        let c = ring_matrix(4, 1, 1.0);
        let pruned = c.prune(0.4).unwrap();
        assert!(pruned.nnz() <= c.nnz());
    }

    #[test]
    fn memory_bytes_positive() {
        let c = ring_matrix(10, 2, 1.0);
        assert!(c.memory_bytes() > 0);
    }

    #[test]
    fn sparsity_ring() {
        let c = ring_matrix(100, 2, 1.0);
        let expected_nnz = 100 * 4;
        let total = 100 * 100;
        let expected_sparsity = 1.0 - (expected_nnz as f64) / (total as f64);
        assert!((c.sparsity() - expected_sparsity).abs() < 1e-12);
    }

    #[test]
    fn kuramoto_coupling_synchronized() {
        let n = 8;
        let c = ring_matrix(n, 1, 1.0);
        let phases = vec![0.0; n];
        let amplitudes = vec![1.0; n];
        let (sin_sum, cos_sum) = c.kuramoto_coupling(&phases, &amplitudes).unwrap();
        for i in 0..n {
            assert!(sin_sum[i].abs() < 1e-12, "sin_sum[{i}] = {}", sin_sum[i]);
            assert!(cos_sum[i].abs() < 1e-12 || (cos_sum[i] - 2.0 * 0.5).abs() < 1e-12);
        }
    }

    #[test]
    fn kuramoto_coupling_dimension_mismatch() {
        let c = ring_matrix(4, 1, 1.0);
        let err = c.kuramoto_coupling(&[0.0; 3], &[1.0; 4]).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn stuart_landau_coupling_synchronized() {
        let n = 6;
        let c = ring_matrix(n, 1, 1.0);
        let phases = vec![0.0; n];
        let amplitudes = vec![1.0; n];
        let (c_re, c_im) = c.stuart_landau_coupling(&phases, &amplitudes).unwrap();
        for i in 0..n {
            assert!(c_re[i].abs() < 1e-12, "c_re[{i}] = {}", c_re[i]);
            assert!(c_im[i].abs() < 1e-12, "c_im[{i}] = {}", c_im[i]);
        }
    }

    #[test]
    fn neighbor_list_ring() {
        let c = ring_matrix(6, 1, 1.0);
        let nbrs = c.neighbor_list().unwrap();
        assert_eq!(nbrs.len(), 6);
        for row in &nbrs {
            assert_eq!(row.len(), 2);
        }
    }

    #[test]
    fn submatrix_ring() {
        let c = ring_matrix(6, 1, 1.0);
        let kept = vec![0, 2, 4];
        let sub = c.submatrix(&kept).unwrap();
        assert_eq!(sub.n_oscillators(), 3);
    }

    #[test]
    fn from_knn_basic() {
        let phases = vec![0.0, 0.5, 1.0, 1.5, 2.0, TAU - 0.5];
        let c = SparseCoupling::from_knn(&phases, 2, 1.0).unwrap();
        assert_eq!(c.n_oscillators(), 6);
        assert_eq!(c.nnz(), 12);
    }

    #[test]
    fn reject_empty_population() {
        let err = SparseCoupling::from_ring(0, 1, 1.0).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn reject_non_square() {
        let indptr = vec![0, 1, 2];
        let indices = vec![0, 1];
        let data = vec![1.0, 1.0];
        let err = SparseCoupling::from_csr(&indptr, &indices, &data, 1).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    // ── from_knn error paths ──────────────────────────────────────────────

    #[test]
    fn from_knn_empty_phases() {
        let err = SparseCoupling::from_knn(&[], 2, 1.0).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn from_knn_k_zero() {
        let phases = vec![0.0, 1.0, 2.0];
        let err = SparseCoupling::from_knn(&phases, 0, 1.0).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn from_knn_k_ge_n() {
        let phases = vec![0.0, 1.0, 2.0];
        let err = SparseCoupling::from_knn(&phases, 3, 1.0).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn from_knn_non_finite_strength() {
        let phases = vec![0.0, 1.0, 2.0, 3.0];
        let err = SparseCoupling::from_knn(&phases, 2, f64::INFINITY).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn from_knn_non_finite_phase() {
        let phases = vec![0.0, f64::NAN, 2.0, 3.0];
        let err = SparseCoupling::from_knn(&phases, 2, 1.0).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    // ── from_csr error paths ──────────────────────────────────────────────

    #[test]
    fn from_csr_n_zero() {
        let err = SparseCoupling::from_csr(&[0], &[], &[], 0).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn from_csr_indptr_length_mismatch() {
        let indptr = vec![0, 1]; // length 2, but n=3 expects length 4
        let indices = vec![0];
        let data = vec![1.0];
        let err = SparseCoupling::from_csr(&indptr, &indices, &data, 3).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn from_csr_indices_length_mismatch() {
        let indptr = vec![0, 2, 4, 6]; // nnz=6
        let indices = vec![1, 2, 0]; // only 3, expected 6
        let data = vec![1.0, 1.0, 1.0, 1.0, 1.0, 1.0];
        let err = SparseCoupling::from_csr(&indptr, &indices, &data, 3).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn from_csr_non_finite_data() {
        let indptr = vec![0, 1, 2];
        let indices = vec![0, 1];
        let data = vec![1.0, f64::NAN];
        let err = SparseCoupling::from_csr(&indptr, &indices, &data, 2).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    // ── from_dense error paths ────────────────────────────────────────────

    #[test]
    fn from_dense_n_zero() {
        let err = SparseCoupling::from_dense(&[], 0, 0.0).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn from_dense_length_mismatch() {
        let dense = vec![1.0, 2.0, 3.0]; // length 3, but n=2 expects 4
        let err = SparseCoupling::from_dense(&dense, 2, 0.0).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn from_dense_non_finite_entry() {
        let dense = vec![1.0, f64::INFINITY, 0.0, 1.0];
        let err = SparseCoupling::from_dense(&dense, 2, 0.0).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    // ── from_ring error paths ─────────────────────────────────────────────

    #[test]
    fn from_ring_non_finite_strength() {
        let err = SparseCoupling::from_ring(4, 1, f64::NAN).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn from_ring_degree_zero() {
        let err = SparseCoupling::from_ring(4, 0, 1.0).unwrap_err();
        assert!(matches!(err, SimError::InvalidCoupling { .. }));
    }

    #[test]
    fn from_ring_degree_ge_n() {
        let err = SparseCoupling::from_ring(4, 2, 1.0).unwrap_err();
        assert!(matches!(err, SimError::InvalidCoupling { .. }));
    }

    // ── new() error paths ─────────────────────────────────────────────────

    #[test]
    fn new_rejects_non_square_csr() {
        // Build a 2×3 CSR matrix
        let csr = {
            let mut t = TriMat::new((2, 3));
            t.add_triplet(0, 0, 1.0);
            t.add_triplet(1, 2, 1.0);
            t.to_csr()
        };
        let err = SparseCoupling::new(csr).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn new_rejects_empty_csr() {
        let csr = TriMat::new((0, 0)).to_csr();
        let err = SparseCoupling::new(csr).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn new_rejects_non_finite_data() {
        let mut tripmat = TriMat::new((2, 2));
        tripmat.add_triplet(0, 1, f64::NEG_INFINITY);
        tripmat.add_triplet(1, 0, 1.0);
        let csr = tripmat.to_csr();
        let err = SparseCoupling::new(csr).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    // ── submatrix edge cases ──────────────────────────────────────────────

    #[test]
    fn submatrix_empty_kept() {
        let c = ring_matrix(6, 1, 1.0);
        let err = c.submatrix(&[]).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn submatrix_out_of_range_index() {
        let c = ring_matrix(6, 1, 1.0);
        let err = c.submatrix(&[0, 10]).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn submatrix_single_element() {
        let c = ring_matrix(6, 1, 1.0);
        let sub = c.submatrix(&[3]).unwrap();
        assert_eq!(sub.n_oscillators(), 1);
    }

    // ── kuramoto_coupling / stuart_landau_coupling mismatches ─────────────

    #[test]
    fn kuramoto_coupling_amplitudes_mismatch() {
        let c = ring_matrix(4, 1, 1.0);
        let err = c.kuramoto_coupling(&[0.0; 4], &[1.0; 3]).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn stuart_landau_coupling_phases_mismatch() {
        let c = ring_matrix(4, 1, 1.0);
        let err = c.stuart_landau_coupling(&[0.0; 3], &[1.0; 4]).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn stuart_landau_coupling_amplitudes_mismatch() {
        let c = ring_matrix(4, 1, 1.0);
        let err = c.stuart_landau_coupling(&[0.0; 4], &[1.0; 3]).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    // ── neighbor_list with isolated oscillator ────────────────────────────

    #[test]
    fn neighbor_list_isolated_oscillator() {
        // Build a 3×3 CSR where row 1 has no entries
        let mut tripmat = TriMat::new((3, 3));
        tripmat.add_triplet(0, 1, 1.0);
        tripmat.add_triplet(2, 0, 1.0);
        let csr = tripmat.to_csr();
        let c = SparseCoupling::new(csr).unwrap();
        let err = c.neighbor_list().unwrap_err();
        assert!(matches!(err, SimError::InvalidCoupling { .. }));
    }

    // ── prune edge cases ──────────────────────────────────────────────────

    #[test]
    fn prune_all_entries_removed_leaves_empty_then_errors() {
        let c = ring_matrix(4, 1, 0.1);
        // Prune with a very high threshold — all entries removed
        let pruned = c.prune(100.0);
        // The resulting matrix has 0 nnz, but SparseCoupling::new accepts it
        // as long as it is square and non-empty dimension
        assert!(pruned.is_ok());
        assert_eq!(pruned.unwrap().nnz(), 0);
    }

    #[test]
    fn prune_preserves_large_entries() {
        let c = ring_matrix(4, 1, 1.0);
        let pruned = c.prune(0.0).unwrap();
        assert_eq!(pruned.nnz(), c.nnz());
    }

    // ── from_knn weight check ─────────────────────────────────────────────

    #[test]
    fn from_knn_weight_matches_strength_over_k() {
        let phases = vec![0.0, 1.0, 2.0, 3.0, 4.0, 5.0];
        let strength = 3.0;
        let k = 2;
        let c = SparseCoupling::from_knn(&phases, k, strength).unwrap();
        let expected_weight = strength / (k as f64);
        // All entries should equal expected_weight
        for &v in c.as_csr().data() {
            assert!((v - expected_weight).abs() < 1e-12);
        }
    }

    // ── as_csr returns the inner matrix ───────────────────────────────────

    #[test]
    fn as_csr_returns_inner() {
        let c = ring_matrix(4, 1, 1.0);
        let csr = c.as_csr();
        assert_eq!(csr.rows(), 4);
        assert_eq!(csr.cols(), 4);
    }
}

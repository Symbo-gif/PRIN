//! CP/PARAFAC decomposition via Alternating Least Squares (ALS).
//!
//! The CP decomposition factorizes a tensor `X` into a sum of rank-1 tensors:
//!
//! ```text
//! X ≈ Σ_{r=1}^{R} λ_r · a_r^(0) ∘ a_r^(1) ∘ a_r^(2) ∘ ...
//! ```
//!
//! where `∘` denotes the outer product and `R` is the number of components
//! (CP rank). ALS solves for the factor matrices by iteratively fixing all
//! but one factor and solving a least-squares problem.
//!
//! # Determinism
//!
//! Initialization uses [`prin_dynamics::Seed`] for reproducible factor matrices.
//! Given the same seed and input, CP-ALS produces identical results across runs.

use ndarray::{ArrayD, IxDyn};
use prin_dynamics::Seed;
use serde::{Deserialize, Serialize};

use crate::error::TensorError;
use crate::utils::{flat_to_multi, mode_unfold, require_finite, require_positive_dims};

/// Result of a CP-ALS decomposition.
#[derive(Debug, Clone)]
pub struct CPResult {
    /// The decomposition.
    pub decomposition: CPDecomposition,
    /// Number of ALS iterations performed.
    pub iterations: usize,
    /// Final relative change in the reconstruction error `‖X − X̂‖_F`
    /// between the last two iterations (convergence diagnostic).
    pub final_relative_change: f64,
    /// Whether the algorithm converged (relative error change below tolerance).
    pub converged: bool,
}

/// A CP decomposition: weights + factor matrices.
///
/// The decomposition of a tensor `X` of shape `(I_0, I_1, ..., I_{N-1})` with
/// `R` components is:
/// - `weights`: a vector of length `R`
/// - `factors`: a vector of matrices `A^(n)` of shape `(I_n, R)`
///
/// Reconstruction: `X ≈ Σ_r weights[r] · factors[0][:,r] ∘ factors[1][:,r] ∘ ...`
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CPDecomposition {
    /// Component weights (length `R`).
    weights: Vec<f64>,
    /// Factor matrices, one per mode. `factors[n]` has shape `(I_n, R)`.
    factors: Vec<ndarray::Array2<f64>>,
}

impl CPDecomposition {
    /// Create a new `CPDecomposition` from weights and factor matrices.
    ///
    /// # Errors
    ///
    /// Returns [`TensorError::ShapeMismatch`] if dimensions are inconsistent.
    pub fn new(weights: Vec<f64>, factors: Vec<ndarray::Array2<f64>>) -> Result<Self, TensorError> {
        let r = weights.len();
        if r == 0 {
            return Err(TensorError::InvalidComponents {
                op: "CPDecomposition::new",
                components: 0,
            });
        }
        if factors.is_empty() {
            return Err(TensorError::InsufficientModes {
                op: "CPDecomposition::new",
                required: 2,
                got: 0,
            });
        }
        for (n, factor) in factors.iter().enumerate() {
            if factor.ncols() != r {
                return Err(TensorError::ShapeMismatch {
                    op: "CPDecomposition::new",
                    expected: format!("factor {n} with {r} columns (matching weights)"),
                    got: format!("{} columns", factor.ncols()),
                });
            }
        }
        Ok(Self { weights, factors })
    }

    /// The component weights.
    pub fn weights(&self) -> &[f64] {
        &self.weights
    }

    /// The factor matrices.
    pub fn factors(&self) -> &[ndarray::Array2<f64>] {
        &self.factors
    }

    /// The number of components (CP rank).
    pub fn n_components(&self) -> usize {
        self.weights.len()
    }

    /// The number of modes.
    pub fn ndim(&self) -> usize {
        self.factors.len()
    }

    /// The shape of the reconstructed tensor.
    pub fn shape(&self) -> Vec<usize> {
        self.factors.iter().map(|f| f.nrows()).collect()
    }

    /// Reconstruct the tensor from the CP decomposition.
    ///
    /// Computes `Σ_r weights[r] · factors[0][:,r] ∘ factors[1][:,r] ∘ ...`
    pub fn reconstruct(&self) -> ArrayD<f64> {
        let shape = self.shape();
        let r = self.n_components();
        let total: usize = shape.iter().product();
        let mut result = vec![0.0_f64; total];

        for comp in 0..r {
            let weight = self.weights[comp];
            // Compute the rank-1 tensor for this component via outer product.
            #[allow(clippy::needless_range_loop)]
            for idx in 0..total {
                let multi = flat_to_multi(idx, &shape);
                let mut val = weight;
                for (mode, factor) in self.factors.iter().enumerate() {
                    val *= factor[[multi[mode], comp]];
                }
                result[idx] += val;
            }
        }

        ArrayD::from_shape_vec(IxDyn(&shape), result).expect("shape is consistent")
    }
}

/// Compute the CP decomposition via Alternating Least Squares (ALS).
///
/// # Convergence
///
/// After each ALS sweep, all factor matrices are normalized (column norms
/// clamped at `1e-12`) and the weights absorb the product of all per-mode
/// column norms. Convergence is monitored via the relative change in the
/// reconstruction error `‖X − X̂‖_F` between successive iterations.
///
/// # Initialization
///
/// Factor matrices are initialized from [`prin_dynamics::Seed`] (uniform
/// `[0, 1)`). This is a deliberate PRIN design choice: the `Seed` authority
/// provides deterministic reproducibility across all PRIN numerics. The
/// PRINet 3.0 reference uses `torch.randn` (standard normal); the uniform
/// distribution is algebraically equivalent for ALS convergence.
///
/// # Arguments
///
/// * `tensor` — The input tensor of shape `(I_0, I_1, ..., I_{N-1})`.
/// * `n_components` — The number of components (CP rank) `R`.
/// * `seed` — Deterministic seed for factor initialization.
/// * `max_iter` — Maximum number of ALS iterations.
/// * `tol` — Convergence tolerance on relative change in reconstruction error.
///
/// # Errors
///
/// - [`TensorError::EmptyInput`] if the tensor has zero elements.
/// - [`TensorError::NonFiniteValue`] if any element is NaN or infinite.
/// - [`TensorError::ZeroDimension`] if any mode has dimension 0.
/// - [`TensorError::InvalidComponents`] if `n_components == 0`.
/// - [`TensorError::InvalidTolerance`] if `tol` is negative or NaN.
/// - [`TensorError::InvalidMaxIter`] if `max_iter == 0`.
/// - [`TensorError::NonConvergence`] if ALS does not converge within `max_iter`.
///
/// # Examples
///
/// ```
/// use ndarray::{ArrayD, IxDyn};
/// use prin_dynamics::Seed;
/// use prin_tensor::cp_als;
///
/// let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
/// let tensor = ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap();
/// let seed = Seed::new(42, 0);
/// let result = cp_als(&tensor, 3, &seed, 100, 1e-10).unwrap();
/// assert!(result.converged);
/// ```
pub fn cp_als(
    tensor: &ArrayD<f64>,
    n_components: usize,
    seed: &Seed,
    max_iter: usize,
    tol: f64,
) -> Result<CPResult, TensorError> {
    let op = "cp_als";
    let shape = tensor.shape();
    let ndim = shape.len();

    // Validate inputs.
    if tensor.is_empty() {
        return Err(TensorError::EmptyInput { op });
    }
    require_finite(
        op,
        tensor
            .as_slice()
            .ok_or_else(|| TensorError::ShapeMismatch {
                op,
                expected: "contiguous tensor".to_string(),
                got: "non-contiguous tensor".to_string(),
            })?,
    )?;
    require_positive_dims(op, shape)?;

    if n_components == 0 {
        return Err(TensorError::InvalidComponents { op, components: 0 });
    }
    if ndim < 2 {
        return Err(TensorError::InsufficientModes {
            op,
            required: 2,
            got: ndim,
        });
    }
    if !tol.is_finite() || tol < 0.0 {
        return Err(TensorError::InvalidTolerance {
            op,
            name: "tol",
            value: tol,
        });
    }
    if max_iter == 0 {
        return Err(TensorError::InvalidMaxIter { op, max_iter: 0 });
    }

    let r = n_components;

    // Initialize factor matrices from the Seed (uniform [0,1)).
    let mut local_seed = seed.clone();
    let mut factors: Vec<ndarray::Array2<f64>> = Vec::with_capacity(ndim);
    for &dim in shape.iter() {
        let mut factor = ndarray::Array2::zeros((dim, r));
        for col in 0..r {
            for row in 0..dim {
                let val = local_seed.next_f64();
                factor[[row, col]] = val;
            }
        }
        factors.push(factor);
    }

    let mut prev_error = f64::INFINITY;
    let mut iterations = 0;
    let mut converged = false;
    let mut final_change = f64::INFINITY;
    let mut weights = vec![1.0_f64; r];

    for iter in 0..max_iter {
        iterations = iter + 1;

        // Update each factor matrix via ALS.
        for mode in 0..ndim {
            let other_modes: Vec<usize> = (0..ndim).filter(|&m| m != mode).collect();
            let kr = khatri_rao_product(&factors, &other_modes);

            let mut gram_product = ndarray::Array2::eye(r);
            for &m in &other_modes {
                let gram = factors[m].t().dot(&factors[m]);
                gram_product *= &gram;
            }

            let unfolded = mode_unfold(tensor, mode)?;
            let ut_kr = unfolded.dot(&kr);
            let gram_inv = invert_matrix(&gram_product)?;
            factors[mode] = ut_kr.dot(&gram_inv);
        }

        // Normalize ALL factors (column norms clamped at 1e-12) and
        // accumulate weights as the product of all per-mode column norms.
        weights = vec![1.0_f64; r];
        for factor in factors.iter_mut() {
            for col in 0..r {
                let norm: f64 = factor
                    .column(col)
                    .iter()
                    .map(|x| x * x)
                    .sum::<f64>()
                    .sqrt();
                let clamped = norm.max(1e-12);
                weights[col] *= clamped;
                for row in 0..factor.nrows() {
                    factor[[row, col]] /= clamped;
                }
            }
        }

        // Convergence: relative change in reconstruction error ‖X − X̂‖_F.
        let recon = reconstruct_weighted(&weights, &factors, shape);
        let error = frobenius_norm_diff(tensor, &recon);
        let change = if prev_error.is_finite() {
            (prev_error - error).abs() / prev_error.max(1e-12)
        } else {
            1.0
        };
        prev_error = error;
        final_change = change;

        if change < tol && iter > 0 {
            converged = true;
            break;
        }
    }

    if !converged {
        return Err(TensorError::NonConvergence {
            op,
            iterations,
            final_change,
        });
    }

    let decomposition = CPDecomposition::new(weights, factors)?;
    Ok(CPResult {
        decomposition,
        iterations,
        final_relative_change: final_change,
        converged,
    })
}

/// Compute the Khatri-Rao product of factor matrices for the given modes.
///
/// The Khatri-Rao product is the column-wise Kronecker product.
/// Given matrices A (I×R) and B (J×R), the result is (I*J × R).
fn khatri_rao_product(factors: &[ndarray::Array2<f64>], modes: &[usize]) -> ndarray::Array2<f64> {
    assert!(
        !modes.is_empty(),
        "khatri_rao_product requires at least one mode"
    );

    let r = factors[modes[0]].ncols();
    let first = &factors[modes[0]];
    let mut result = first.clone();

    for &mode in &modes[1..] {
        let factor = &factors[mode];
        let (rows_a, cols_a) = result.dim();
        let (rows_b, cols_b) = factor.dim();
        assert_eq!(cols_a, cols_b, "Khatri-Rao requires matching column counts");

        let mut new_result = ndarray::Array2::zeros((rows_a * rows_b, r));
        for col in 0..r {
            for i in 0..rows_a {
                for j in 0..rows_b {
                    new_result[[i * rows_b + j, col]] = result[[i, col]] * factor[[j, col]];
                }
            }
        }
        result = new_result;
    }

    result
}

/// Reconstruct a tensor from weights and normalized factor matrices.
fn reconstruct_weighted(
    weights: &[f64],
    factors: &[ndarray::Array2<f64>],
    shape: &[usize],
) -> ArrayD<f64> {
    let r = weights.len();
    let total: usize = shape.iter().product();
    let mut result = vec![0.0_f64; total];

    for comp in 0..r {
        #[allow(clippy::needless_range_loop)]
        for idx in 0..total {
            let multi = flat_to_multi(idx, shape);
            let mut val = weights[comp];
            for (mode, factor) in factors.iter().enumerate() {
                val *= factor[[multi[mode], comp]];
            }
            result[idx] += val;
        }
    }

    ArrayD::from_shape_vec(IxDyn(shape), result).expect("shape is consistent")
}

/// Compute the Frobenius norm of the difference of two tensors.
fn frobenius_norm_diff(a: &ArrayD<f64>, b: &ArrayD<f64>) -> f64 {
    a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| (x - y) * (x - y))
        .sum::<f64>()
        .sqrt()
}

/// Invert a small matrix using Gauss-Jordan elimination with partial pivoting.
fn invert_matrix(matrix: &ndarray::Array2<f64>) -> Result<ndarray::Array2<f64>, TensorError> {
    let n = matrix.nrows();
    assert_eq!(n, matrix.ncols(), "matrix must be square");

    // Augmented matrix [A | I].
    let mut aug = ndarray::Array2::zeros((n, 2 * n));
    for i in 0..n {
        for j in 0..n {
            aug[[i, j]] = matrix[[i, j]];
        }
        aug[[i, n + i]] = 1.0;
    }

    // Forward elimination with partial pivoting.
    for col in 0..n {
        // Find pivot.
        let mut max_row = col;
        let mut max_val = aug[[col, col]].abs();
        for row in (col + 1)..n {
            let val = aug[[row, col]].abs();
            if val > max_val {
                max_val = val;
                max_row = row;
            }
        }

        if max_val < 1e-14 {
            return Err(TensorError::LinearAlgebraFailed {
                op: "invert_matrix",
                message: format!("singular matrix at column {col}"),
            });
        }

        // Swap rows.
        if max_row != col {
            for j in 0..(2 * n) {
                let tmp = aug[[col, j]];
                aug[[col, j]] = aug[[max_row, j]];
                aug[[max_row, j]] = tmp;
            }
        }

        // Scale pivot row.
        let pivot = aug[[col, col]];
        for j in 0..(2 * n) {
            aug[[col, j]] /= pivot;
        }

        // Eliminate column.
        for row in 0..n {
            if row != col {
                let factor = aug[[row, col]];
                for j in 0..(2 * n) {
                    aug[[row, j]] -= factor * aug[[col, j]];
                }
            }
        }
    }

    // Extract inverse.
    let mut inv = ndarray::Array2::zeros((n, n));
    for i in 0..n {
        for j in 0..n {
            inv[[i, j]] = aug[[i, n + j]];
        }
    }

    Ok(inv)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::{ArrayD, IxDyn};

    #[test]
    fn cp_als_converges_on_rank1_tensor() {
        // Create a rank-1 tensor: outer product of three vectors.
        let a = ndarray::array![1.0, 2.0, 3.0];
        let b = ndarray::array![4.0, 5.0];
        let c = ndarray::array![6.0, 7.0, 8.0, 9.0];

        let mut data = vec![0.0_f64; 3 * 2 * 4];
        let mut idx = 0;
        for i in 0..3 {
            for j in 0..2 {
                for k in 0..4 {
                    data[idx] = a[i] * b[j] * c[k];
                    idx += 1;
                }
            }
        }
        let tensor = ArrayD::from_shape_vec(IxDyn(&[3, 2, 4]), data).unwrap();

        let seed = Seed::new(42, 0);
        let result = cp_als(&tensor, 1, &seed, 100, 1e-10).unwrap();
        assert!(result.converged);
        assert!(result.iterations <= 10);

        // Reconstruction should be close.
        let recon = result.decomposition.reconstruct();
        for (a, b) in tensor.iter().zip(recon.iter()) {
            assert!(
                (a - b).abs() < 1e-8,
                "rank-1 reconstruction error: {} vs {}",
                a,
                b
            );
        }
    }

    #[test]
    fn cp_als_rejects_empty_tensor() {
        let t = ArrayD::from_shape_vec(IxDyn(&[0, 3, 2]), vec![]).unwrap();
        let seed = Seed::new(0, 0);
        let err = cp_als(&t, 2, &seed, 100, 1e-10).unwrap_err();
        assert!(matches!(err, TensorError::EmptyInput { .. }));
    }

    #[test]
    fn cp_als_rejects_zero_components() {
        let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
        let t = ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap();
        let seed = Seed::new(0, 0);
        let err = cp_als(&t, 0, &seed, 100, 1e-10).unwrap_err();
        assert!(matches!(err, TensorError::InvalidComponents { .. }));
    }

    #[test]
    fn cp_als_rejects_negative_tolerance() {
        let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
        let t = ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap();
        let seed = Seed::new(0, 0);
        let err = cp_als(&t, 2, &seed, 100, -1e-10).unwrap_err();
        assert!(matches!(err, TensorError::InvalidTolerance { .. }));
    }

    #[test]
    fn cp_decomposition_reconstruct_shape() {
        let weights = vec![1.0, 2.0];
        let factors = vec![
            ndarray::Array2::ones((3, 2)),
            ndarray::Array2::ones((4, 2)),
            ndarray::Array2::ones((2, 2)),
        ];
        let cp = CPDecomposition::new(weights, factors).unwrap();
        let recon = cp.reconstruct();
        assert_eq!(recon.shape(), &[3, 4, 2]);
    }

    #[test]
    fn khatri_rao_product_shape() {
        let a = ndarray::Array2::ones((3, 2));
        let b = ndarray::Array2::ones((4, 2));
        let factors = vec![a, b];
        let kr = khatri_rao_product(&factors, &[0, 1]);
        assert_eq!(kr.dim(), (12, 2));
    }

    #[test]
    fn invert_matrix_identity() {
        let eye = ndarray::Array2::eye(3);
        let inv = invert_matrix(&eye).unwrap();
        for i in 0..3 {
            for j in 0..3 {
                let expected = if i == j { 1.0 } else { 0.0 };
                assert!((inv[[i, j]] - expected).abs() < 1e-14);
            }
        }
    }

    #[test]
    fn cp_als_seed_reproducibility() {
        let data: Vec<f64> = (0..24).map(|i| (i as f64) * 0.1).collect();
        let tensor = ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap();

        let seed = Seed::new(123, 0);
        let result1 = cp_als(&tensor, 2, &seed, 50, 1e-8).unwrap();
        let result2 = cp_als(&tensor, 2, &seed, 50, 1e-8).unwrap();

        // Same seed should produce identical results.
        assert_eq!(result1.iterations, result2.iterations);
        for (w1, w2) in result1
            .decomposition
            .weights()
            .iter()
            .zip(result2.decomposition.weights())
        {
            assert!((w1 - w2).abs() < 1e-14);
        }
    }
}

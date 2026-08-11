//! Tucker/HOSVD decomposition.
//!
//! The Tucker decomposition factorizes a tensor `X` into a core tensor `G` and
//! a set of factor matrices `U^(n)` (one per mode):
//!
//! ```text
//! X ≈ G ×₁ U^(0) ×₂ U^(1) ×₃ U^(2) ...
//! ```
//!
//! where `×ₙ` denotes the mode-`n` product. The Higher-Order SVD (HOSVD)
//! computes the factor matrices as the left singular vectors of each mode-`n`
//! unfolding, and the core tensor as the multilinear projection.
//!
//! # References
//!
//! - De Lathauwer, De Moor, Vandewalle (2000). "A Multilinear Singular Value
//!   Decomposition." *SIAM J. Matrix Anal. Appl.* 21(4), 1253–1278.

use ndarray::ArrayD;
use serde::{Deserialize, Serialize};

use crate::error::TensorError;
use crate::utils::{
    faer_mat_to_ndarray, mode_n_product, mode_unfold, ndarray_to_faer, require_finite,
    require_positive_dims,
};

/// A Tucker decomposition: core tensor + factor matrices.
///
/// The decomposition of a tensor `X` of shape `(I_0, I_1, ..., I_{N-1})` is:
/// - `core`: a tensor of shape `(R_0, R_1, ..., R_{N-1})` where `R_n ≤ I_n`
/// - `factors`: a vector of matrices `U^(n)` of shape `(I_n, R_n)`
///
/// Reconstruction: `X ≈ core ×₁ U^(0) ×₂ U^(1) ×₃ ...`
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolyadicTensor {
    /// Core tensor of shape `(R_0, R_1, ..., R_{N-1})`.
    core: ArrayD<f64>,
    /// Factor matrices, one per mode. `factors[n]` has shape `(I_n, R_n)`.
    factors: Vec<ndarray::Array2<f64>>,
}

impl PolyadicTensor {
    /// Create a new `PolyadicTensor` from a core tensor and factor matrices.
    ///
    /// # Errors
    ///
    /// Returns [`TensorError::ShapeMismatch`] if factor dimensions are
    /// inconsistent with the core tensor shape.
    pub fn new(core: ArrayD<f64>, factors: Vec<ndarray::Array2<f64>>) -> Result<Self, TensorError> {
        let core_shape = core.shape();
        if factors.len() != core.ndim() {
            return Err(TensorError::ShapeMismatch {
                op: "PolyadicTensor::new",
                expected: format!("{} factors (matching core ndim)", core.ndim()),
                got: format!("{} factors", factors.len()),
            });
        }
        for (n, (factor, &core_dim)) in factors.iter().zip(core_shape.iter()).enumerate() {
            if factor.ncols() != core_dim {
                return Err(TensorError::ShapeMismatch {
                    op: "PolyadicTensor::new",
                    expected: format!("factor {n} with {} columns (core dim {n})", core_dim),
                    got: format!("{} columns", factor.ncols()),
                });
            }
        }
        Ok(Self { core, factors })
    }

    /// The core tensor.
    pub fn core(&self) -> &ArrayD<f64> {
        &self.core
    }

    /// The factor matrices.
    pub fn factors(&self) -> &[ndarray::Array2<f64>] {
        &self.factors
    }

    /// The number of modes.
    pub fn ndim(&self) -> usize {
        self.core.ndim()
    }

    /// The shape of the reconstructed tensor `(I_0, I_1, ..., I_{N-1})`.
    pub fn shape(&self) -> Vec<usize> {
        self.factors.iter().map(|f| f.nrows()).collect()
    }

    /// The multilinear ranks `(R_0, R_1, ..., R_{N-1})`.
    pub fn ranks(&self) -> Vec<usize> {
        self.factors.iter().map(|f| f.ncols()).collect()
    }

    /// Reconstruct the tensor from the Tucker decomposition.
    ///
    /// Computes `G ×₁ U^(0) ×₂ U^(1) ×₃ ...` by successive mode-n products.
    pub fn reconstruct(&self) -> ArrayD<f64> {
        let mut result = self.core.clone();
        for (mode, factor) in self.factors.iter().enumerate() {
            result = mode_n_product(&result, factor, mode)
                .expect("dimensions are consistent by construction");
        }
        result
    }
}

/// Compute the Higher-Order SVD (HOSVD) of a tensor.
///
/// The HOSVD computes the Tucker decomposition with factor matrices given by
/// the left singular vectors of each mode-`n` unfolding (truncated to the
/// specified ranks). The core tensor is obtained by multilinear projection.
///
/// When `ranks` is `None`, the full-rank HOSVD is computed (each `R_n = I_n`),
/// which is an exact reconstruction.
///
/// # Arguments
///
/// * `tensor` — The input tensor of shape `(I_0, I_1, ..., I_{N-1})`.
/// * `ranks` — Optional multilinear ranks `(R_0, ..., R_{N-1})`. Each `R_n`
///   must satisfy `1 ≤ R_n ≤ I_n`. If `None`, full ranks are used.
///
/// # Errors
///
/// - [`TensorError::EmptyInput`] if the tensor has zero elements.
/// - [`TensorError::NonFiniteValue`] if any element is NaN or infinite.
/// - [`TensorError::ZeroDimension`] if any mode has dimension 0.
/// - [`TensorError::InvalidRank`] if any rank is 0 or exceeds the mode dimension.
/// - [`TensorError::InsufficientModes`] if the tensor has fewer than 2 modes.
///
/// # Examples
///
/// ```
/// use ndarray::{ArrayD, IxDyn};
/// use prin_tensor::hosvd;
///
/// let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
/// let tensor = ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap();
/// let tucker = hosvd(&tensor, None).unwrap();
/// let reconstructed = tucker.reconstruct();
/// // Full-rank HOSVD is exact.
/// for (a, b) in tensor.iter().zip(reconstructed.iter()) {
///     assert!((a - b).abs() < 1e-10);
/// }
/// ```
pub fn hosvd(tensor: &ArrayD<f64>, ranks: Option<&[usize]>) -> Result<PolyadicTensor, TensorError> {
    let op = "hosvd";
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

    if ndim < 2 {
        return Err(TensorError::InsufficientModes {
            op,
            required: 2,
            got: ndim,
        });
    }

    // Determine ranks.
    let ranks_vec: Vec<usize>;
    let ranks_slice = match ranks {
        Some(r) => {
            if r.len() != ndim {
                return Err(TensorError::ShapeMismatch {
                    op,
                    expected: format!("{} ranks (matching tensor ndim)", ndim),
                    got: format!("{} ranks", r.len()),
                });
            }
            for (mode, (&rank, &dim)) in r.iter().zip(shape.iter()).enumerate() {
                if rank == 0 || rank > dim {
                    return Err(TensorError::InvalidRank {
                        op,
                        mode,
                        rank,
                        dim,
                    });
                }
            }
            r
        }
        None => {
            // Full-rank HOSVD: rank_n = min(I_n, product_of_other_dims).
            ranks_vec = shape
                .iter()
                .enumerate()
                .map(|(mode, &dim)| {
                    let product_of_others: usize = shape
                        .iter()
                        .enumerate()
                        .filter(|&(k, _)| k != mode)
                        .map(|(_, s)| *s)
                        .product();
                    dim.min(product_of_others)
                })
                .collect();
            &ranks_vec
        }
    };

    // Compute factor matrices via SVD of each mode-n unfolding.
    let mut factors = Vec::with_capacity(ndim);
    for (mode, &rank) in ranks_slice.iter().enumerate() {
        let unfolded = mode_unfold(tensor, mode)?;
        let left_singular = thin_svd_left_vectors(&unfolded, rank)?;
        factors.push(left_singular);
    }

    // Compute core tensor: G = X ×₁ U^(0)ᵀ ×₂ U^(1)ᵀ ×₃ ...
    let mut core = tensor.clone();
    for (mode, factor) in factors.iter().enumerate() {
        let factor_t = factor.t().to_owned();
        core = mode_n_product(&core, &factor_t, mode)?;
    }

    PolyadicTensor::new(core, factors)
}

/// Compute the truncated left singular vectors of a matrix via faer SVD.
///
/// Returns the first `k` columns of U from the thin SVD of `matrix`.
fn thin_svd_left_vectors(
    matrix: &ndarray::Array2<f64>,
    k: usize,
) -> Result<ndarray::Array2<f64>, TensorError> {
    let faer_mat = ndarray_to_faer(matrix);
    let svd = faer_mat.thin_svd();

    // Extract U (left singular vectors). svd.u() returns a MatRef.
    let u_ref = svd.u();
    let nrows = u_ref.nrows();
    let ncols = u_ref.ncols();
    let u_full = faer_mat_to_ndarray(nrows, ncols, |r, c| u_ref.read(r, c));

    // Take first k columns (manual copy to avoid ndarray::s! which uses unsafe).
    let mut u_thin = ndarray::Array2::zeros((nrows, k));
    for j in 0..k {
        for i in 0..nrows {
            u_thin[[i, j]] = u_full[[i, j]];
        }
    }
    Ok(u_thin)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::{ArrayD, IxDyn};

    fn test_tensor_3x4x2() -> ArrayD<f64> {
        let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
        ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap()
    }

    #[test]
    fn hosvd_full_rank_reconstructs_exactly() {
        let t = test_tensor_3x4x2();
        let tucker = hosvd(&t, None).unwrap();
        let reconstructed = tucker.reconstruct();
        for (a, b) in t.iter().zip(reconstructed.iter()) {
            assert!((a - b).abs() < 1e-10, "full-rank HOSVD should be exact");
        }
    }

    #[test]
    fn hosvd_full_rank_shape_and_ranks() {
        let t = test_tensor_3x4x2();
        let tucker = hosvd(&t, None).unwrap();
        assert_eq!(tucker.shape(), vec![3, 4, 2]);
        assert_eq!(tucker.ranks(), vec![3, 4, 2]);
        assert_eq!(tucker.ndim(), 3);
    }

    #[test]
    fn hosvd_truncated_rank() {
        let t = test_tensor_3x4x2();
        let tucker = hosvd(&t, Some(&[2, 3, 1])).unwrap();
        assert_eq!(tucker.ranks(), vec![2, 3, 1]);
        assert_eq!(tucker.shape(), vec![3, 4, 2]);
        assert_eq!(tucker.core().shape(), &[2, 3, 1]);
    }

    #[test]
    fn hosvd_rank_one_approximation() {
        let t = test_tensor_3x4x2();
        let tucker = hosvd(&t, Some(&[1, 1, 1])).unwrap();
        assert_eq!(tucker.ranks(), vec![1, 1, 1]);
        assert_eq!(tucker.core().shape(), &[1, 1, 1]);
        let reconstructed = tucker.reconstruct();
        assert_eq!(reconstructed.shape(), t.shape());
    }

    #[test]
    fn hosvd_rejects_empty_tensor() {
        let t = ArrayD::from_shape_vec(IxDyn(&[0, 3, 2]), vec![]).unwrap();
        let err = hosvd(&t, None).unwrap_err();
        assert!(matches!(err, TensorError::EmptyInput { .. }));
    }

    #[test]
    fn hosvd_rejects_nan() {
        let data = vec![1.0, f64::NAN, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0];
        let t = ArrayD::from_shape_vec(IxDyn(&[2, 2, 2]), data).unwrap();
        let err = hosvd(&t, None).unwrap_err();
        assert!(matches!(err, TensorError::NonFiniteValue { .. }));
    }

    #[test]
    fn hosvd_rejects_invalid_rank() {
        let t = test_tensor_3x4x2();
        let err = hosvd(&t, Some(&[0, 4, 2])).unwrap_err();
        assert!(matches!(err, TensorError::InvalidRank { .. }));
        let err = hosvd(&t, Some(&[4, 4, 2])).unwrap_err();
        assert!(matches!(err, TensorError::InvalidRank { .. }));
    }

    #[test]
    fn hosvd_rejects_wrong_number_of_ranks() {
        let t = test_tensor_3x4x2();
        let err = hosvd(&t, Some(&[2, 3])).unwrap_err();
        assert!(matches!(err, TensorError::ShapeMismatch { .. }));
    }

    #[test]
    fn hosvd_rejects_1d_tensor() {
        let t = ArrayD::from_shape_vec(IxDyn(&[5]), vec![1.0, 2.0, 3.0, 4.0, 5.0]).unwrap();
        let err = hosvd(&t, None).unwrap_err();
        assert!(matches!(err, TensorError::InsufficientModes { .. }));
    }

    #[test]
    fn polyadic_tensor_new_validates() {
        let core = ArrayD::from_shape_vec(IxDyn(&[2, 3]), vec![1.0; 6]).unwrap();
        let factors = vec![
            ndarray::Array2::zeros((4, 2)),
            ndarray::Array2::zeros((5, 3)),
        ];
        let pt = PolyadicTensor::new(core, factors).unwrap();
        assert_eq!(pt.shape(), vec![4, 5]);
        assert_eq!(pt.ranks(), vec![2, 3]);
    }

    #[test]
    fn polyadic_tensor_new_rejects_mismatched_factors() {
        let core = ArrayD::from_shape_vec(IxDyn(&[2, 3]), vec![1.0; 6]).unwrap();
        let factors = vec![ndarray::Array2::zeros((4, 2))];
        let err = PolyadicTensor::new(core, factors).unwrap_err();
        assert!(matches!(err, TensorError::ShapeMismatch { .. }));
    }

    #[test]
    fn hosvd_2d_is_matrix_svd() {
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0];
        let matrix = ArrayD::from_shape_vec(IxDyn(&[2, 3]), data).unwrap();
        let tucker = hosvd(&matrix, None).unwrap();
        let reconstructed = tucker.reconstruct();
        for (a, b) in matrix.iter().zip(reconstructed.iter()) {
            assert!((a - b).abs() < 1e-10);
        }
    }

    #[test]
    fn hosvd_factor_orthogonality() {
        let t = test_tensor_3x4x2();
        let tucker = hosvd(&t, None).unwrap();
        for (mode, factor) in tucker.factors().iter().enumerate() {
            let gram = factor.t().dot(factor);
            let identity = ndarray::Array2::eye(factor.ncols());
            for ((i, j), &val) in gram.indexed_iter() {
                let expected: f64 = identity[[i, j]];
                assert!(
                    (val - expected).abs() < 1e-10,
                    "factor {mode} not orthonormal at ({i},{j}): {val} != {expected}"
                );
            }
        }
    }
}

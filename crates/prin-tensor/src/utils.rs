//! Tensor utilities: mode-n unfolding, mode-n product, and tensor arithmetic.
//!
//! These are the building blocks for Tucker/HOSVD and CP/PARAFAC decompositions.
//! All operations work on [`ndarray::ArrayD<f64>`] (dynamic-dimension tensors).

use ndarray::{ArrayD, IxDyn};

use crate::error::{self, TensorError};

/// Compute the mode-`n` unfolding (matricization) of a tensor.
///
/// Given a tensor of shape `(I_0, I_1, ..., I_{N-1})`, the mode-`n` unfolding
/// is a matrix of shape `(I_n, J)` where `J = ∏_{k≠n} I_k`. The column index
/// follows the Kiers convention (remaining modes in their original order).
///
/// # Errors
///
/// Returns [`TensorError::ZeroDimension`] if `mode >= tensor.ndim()`.
pub fn mode_unfold(tensor: &ArrayD<f64>, mode: usize) -> Result<ndarray::Array2<f64>, TensorError> {
    let ndim = tensor.ndim();
    if mode >= ndim {
        return Err(TensorError::ZeroDimension {
            op: "mode_unfold",
            mode,
            size: ndim,
        });
    }

    let shape = tensor.shape();
    let nrows = shape[mode];
    let ncols: usize = shape
        .iter()
        .enumerate()
        .filter(|&(k, _)| k != mode)
        .map(|(_, s)| *s)
        .product();

    // Build the unfolded matrix by iterating over all multi-indices.
    let mut matrix = ndarray::Array2::zeros((nrows, ncols));
    let total = tensor.len();
    for flat in 0..total {
        let multi = flat_to_multi(flat, shape);
        let row = multi[mode];
        // Column index: flatten all indices except mode.
        let col = multi_to_flat_excluding(&multi, shape, mode);
        matrix[[row, col]] = tensor[&multi[..]];
    }
    Ok(matrix)
}

/// Compute the mode-`n` product of a tensor with a matrix.
///
/// Given a tensor of shape `(I_0, ..., I_n, ..., I_{N-1})` and a matrix of
/// shape `(J, I_n)`, the result has shape `(I_0, ..., J, ..., I_{N-1})` with
/// mode `n` replaced by `J`.
///
/// # Errors
///
/// Returns [`TensorError::ModeProductDimMismatch`] if `matrix.ncols() != shape[mode]`.
pub fn mode_n_product(
    tensor: &ArrayD<f64>,
    matrix: &ndarray::Array2<f64>,
    mode: usize,
) -> Result<ArrayD<f64>, TensorError> {
    let shape = tensor.shape();
    let mode_dim = shape[mode];
    let (nrows, ncols) = matrix.dim();

    if ncols != mode_dim {
        return Err(TensorError::ModeProductDimMismatch {
            op: "mode_n_product",
            mode,
            expected: mode_dim,
            got: ncols,
        });
    }

    // Unfold, multiply, refold.
    let unfolded = mode_unfold(tensor, mode)?;
    // unfolded: (mode_dim, product_of_rest)
    // matrix: (nrows, ncols=mode_dim)
    // product: (nrows, product_of_rest)
    let product = matrix.dot(&unfolded);

    // Refold into the new shape.
    let mut new_shape: Vec<usize> = shape.to_vec();
    new_shape[mode] = nrows;
    let total: usize = new_shape.iter().product();

    let mut result = ArrayD::zeros(IxDyn(&new_shape));

    for flat in 0..total {
        let multi = flat_to_multi(flat, &new_shape);
        let row = multi[mode];
        let col = multi_to_flat_excluding(&multi, &new_shape, mode);
        result[&multi[..]] = product[[row, col]];
    }

    Ok(result)
}

/// Compute the Frobenius norm of a tensor.
pub fn frobenius_norm(tensor: &ArrayD<f64>) -> f64 {
    tensor.iter().map(|&x| x * x).sum::<f64>().sqrt()
}

/// Reconstruct a tensor from its mode-n unfolding.
pub fn refold(
    unfolded: &ndarray::Array2<f64>,
    mode: usize,
    original_shape: &[usize],
) -> ArrayD<f64> {
    let nrows = original_shape[mode];
    let ncols: usize = original_shape
        .iter()
        .enumerate()
        .filter(|&(k, _)| k != mode)
        .map(|(_, s)| *s)
        .product();
    debug_assert_eq!(unfolded.dim(), (nrows, ncols));

    let total: usize = original_shape.iter().product();
    let mut result = ArrayD::zeros(IxDyn(original_shape));

    for flat in 0..total {
        let multi = flat_to_multi(flat, original_shape);
        let row = multi[mode];
        let col = multi_to_flat_excluding(&multi, original_shape, mode);
        result[&multi[..]] = unfolded[[row, col]];
    }

    result
}

/// Convert a flat index to a multi-index (row-major / C order).
fn flat_to_multi(mut flat: usize, shape: &[usize]) -> Vec<usize> {
    let ndim = shape.len();
    let mut multi = vec![0; ndim];
    for d in (0..ndim).rev() {
        multi[d] = flat % shape[d];
        flat /= shape[d];
    }
    multi
}

/// Convert a multi-index to a flat index, excluding one mode.
///
/// The excluded mode's index is skipped; the remaining indices are flattened
/// in their original order.
fn multi_to_flat_excluding(multi: &[usize], shape: &[usize], exclude: usize) -> usize {
    let ndim = shape.len();
    // Compute strides for the reduced shape (excluding mode `exclude`).
    let reduced_shape: Vec<usize> = shape
        .iter()
        .enumerate()
        .filter(|&(k, _)| k != exclude)
        .map(|(_, s)| *s)
        .collect();
    let reduced_ndim = reduced_shape.len();

    // Compute strides (row-major) for the reduced shape.
    let mut strides = vec![1; reduced_ndim];
    for d in (0..reduced_ndim - 1).rev() {
        strides[d] = strides[d + 1] * reduced_shape[d + 1];
    }

    // Map multi-indices (skipping excluded mode) to reduced indices.
    let mut flat = 0;
    let mut reduced_idx = 0;
    #[allow(clippy::needless_range_loop)]
    for d in 0..ndim {
        if d == exclude {
            continue;
        }
        flat += multi[d] * strides[reduced_idx];
        reduced_idx += 1;
    }
    flat
}

/// Invert a permutation: if `perm[i] = j`, then `inv[j] = i`.
#[allow(dead_code)]
pub(crate) fn invert_permutation(perm: &[usize]) -> Vec<usize> {
    let mut inv = vec![0; perm.len()];
    for (i, &p) in perm.iter().enumerate() {
        inv[p] = i;
    }
    inv
}

/// Convert an [`ndarray::Array2<f64>`] to a [`faer::Mat<f64>`].
pub(crate) fn ndarray_to_faer(matrix: &ndarray::Array2<f64>) -> faer::Mat<f64> {
    let (nrows, ncols) = matrix.dim();
    // faer::Mat::from_fn takes |row, col|.
    faer::Mat::from_fn(nrows, ncols, |i, j| matrix[[i, j]])
}

/// Convert a faer matrix reference to an [`ndarray::Array2<f64>`].
///
/// `faer::MatRef::read(row, col)` reads element at (row, col).
pub(crate) fn faer_mat_to_ndarray(
    nrows: usize,
    ncols: usize,
    read: impl Fn(usize, usize) -> f64,
) -> ndarray::Array2<f64> {
    let mut array = ndarray::Array2::zeros((nrows, ncols));
    for i in 0..nrows {
        for j in 0..ncols {
            array[[i, j]] = read(i, j);
        }
    }
    array
}

/// Validate that every element of a slice is finite (re-export from error module).
pub(crate) fn require_finite(op: &'static str, values: &[f64]) -> Result<(), TensorError> {
    error::require_finite(op, values)
}

/// Validate that a shape has no zero dimensions (re-export from error module).
pub(crate) fn require_positive_dims(op: &'static str, shape: &[usize]) -> Result<(), TensorError> {
    error::require_positive_dims(op, shape)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::ArrayD;

    fn test_tensor_3x4x2() -> ArrayD<f64> {
        let data: Vec<f64> = (0..24).map(|i| i as f64).collect();
        ArrayD::from_shape_vec(IxDyn(&[3, 4, 2]), data).unwrap()
    }

    #[test]
    fn mode_unfold_shape_mode0() {
        let t = test_tensor_3x4x2();
        let unfolded = mode_unfold(&t, 0).unwrap();
        assert_eq!(unfolded.dim(), (3, 8));
    }

    #[test]
    fn mode_unfold_shape_mode1() {
        let t = test_tensor_3x4x2();
        let unfolded = mode_unfold(&t, 1).unwrap();
        assert_eq!(unfolded.dim(), (4, 6));
    }

    #[test]
    fn mode_unfold_shape_mode2() {
        let t = test_tensor_3x4x2();
        let unfolded = mode_unfold(&t, 2).unwrap();
        assert_eq!(unfolded.dim(), (2, 12));
    }

    #[test]
    fn unfold_refold_is_identity() {
        let t = test_tensor_3x4x2();
        for mode in 0..3 {
            let unfolded = mode_unfold(&t, mode).unwrap();
            let refolded = refold(&unfolded, mode, t.shape());
            assert_eq!(
                t, refolded,
                "unfold/refold roundtrip failed for mode {mode}"
            );
        }
    }

    #[test]
    fn mode_n_product_identity() {
        let t = test_tensor_3x4x2();
        for mode in 0..3 {
            let dim = t.shape()[mode];
            let identity = ndarray::Array2::eye(dim);
            let result = mode_n_product(&t, &identity, mode).unwrap();
            assert_eq!(t, result, "identity mode-{mode} product changed tensor");
        }
    }

    #[test]
    fn mode_n_product_shape() {
        let t = test_tensor_3x4x2();
        let matrix = ndarray::Array2::zeros((5, 4));
        let result = mode_n_product(&t, &matrix, 1).unwrap();
        assert_eq!(result.shape(), &[3, 5, 2]);
    }

    #[test]
    fn mode_n_product_dim_mismatch() {
        let t = test_tensor_3x4x2();
        let matrix = ndarray::Array2::zeros((5, 3));
        let err = mode_n_product(&t, &matrix, 1).unwrap_err();
        assert!(matches!(err, TensorError::ModeProductDimMismatch { .. }));
    }

    #[test]
    fn frobenius_norm_known_value() {
        let data: Vec<f64> = (1..=4).map(|i| i as f64).collect();
        let t = ArrayD::from_shape_vec(IxDyn(&[2, 2]), data).unwrap();
        let norm = frobenius_norm(&t);
        assert!((norm - 30.0_f64.sqrt()).abs() < 1e-14);
    }

    #[test]
    fn ndarray_faer_roundtrip() {
        let matrix = ndarray::array![[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]];
        let faer_mat = ndarray_to_faer(&matrix);
        let nrows = faer_mat.nrows();
        let ncols = faer_mat.ncols();
        let back = faer_mat_to_ndarray(nrows, ncols, |r, c| faer_mat.read(r, c));
        assert_eq!(matrix, back);
    }

    #[test]
    fn invert_permutation_is_involution() {
        let perm = vec![2, 0, 3, 1];
        let inv = invert_permutation(&perm);
        let double_inv = invert_permutation(&inv);
        assert_eq!(perm, double_inv);
    }

    #[test]
    fn flat_to_multi_correct() {
        let shape = vec![3, 4, 2];
        assert_eq!(flat_to_multi(0, &shape), vec![0, 0, 0]);
        assert_eq!(flat_to_multi(1, &shape), vec![0, 0, 1]);
        assert_eq!(flat_to_multi(2, &shape), vec![0, 1, 0]);
        assert_eq!(flat_to_multi(23, &shape), vec![2, 3, 1]);
    }
}

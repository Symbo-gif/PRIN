//! PyO3 bindings for the `prin-tensor` decomposition owners (WP-014) —
//! Bucket D of the WP-036 S1 compatibility surface (sub-pass 0141B).
//!
//! [`PolyadicTensor`](prin_tensor::PolyadicTensor) (Tucker / HOSVD) and
//! [`CPDecomposition`](prin_tensor::CPDecomposition) (CP / PARAFAC via ALS)
//! are non-differentiable batch algorithms. PRINet 3.0's
//! `core/decomposition.py` exposes them as stateful
//! `.decompose(tensor)` / `.reconstruct()` objects, not `nn.Module`s, so
//! these bridges carry no `torch.autograd.Function` and need no gradcheck.
//!
//! All numerics stay in `prin_tensor::{hosvd, cp_als}`; these wrappers only
//! marshal `float64` CPU DLPack tensors across the boundary (Coding Standards
//! §2.1 — no numerics in `prin-py`). The `float32` default `dtype` and the
//! `torch.randn` initializer of the PRINet 3.0 reference are documented
//! deviations owned by `prin-tensor` (`crates/prin-tensor/src/{tucker,cp}.rs`),
//! not re-litigated here.

use ndarray::{Array2, ArrayD, IxDyn};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::Seed;
use prin_tensor::{cp_als, hosvd, CPDecomposition, PolyadicTensor, TensorError};

use super::super::dlpack::{export_dlpack_f64, read_dlpack_f64};

/// Convert a [`TensorError`] into a Python `ValueError`.
fn tensor_err_to_py(err: TensorError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Raised when a decomposition result is read before `decompose()`.
fn not_decomposed() -> PyErr {
    PyValueError::new_err("no decomposition performed yet; call decompose() first")
}

/// Decode a `float64` CPU contiguous DLPack tensor of arbitrary rank into an
/// owned [`ArrayD`].
fn arrayd_from_dlpack(obj: &Bound<'_, PyAny>) -> PyResult<ArrayD<f64>> {
    let (shape, data) = read_dlpack_f64(obj)?;
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    ArrayD::from_shape_vec(IxDyn(&dims), data)
        .map_err(|e| PyValueError::new_err(format!("could not build a tensor of that shape: {e}")))
}

/// Export an [`ArrayD`] (C-order logical iteration) as a new `float64` DLPack
/// capsule.
fn export_arrayd(py: Python<'_>, arr: &ArrayD<f64>) -> PyResult<Py<PyAny>> {
    let shape: Vec<i64> = arr.shape().iter().map(|&d| d as i64).collect();
    let data: Vec<f64> = arr.iter().copied().collect();
    export_dlpack_f64(py, shape, data)
}

/// Export a 2-D factor matrix as a new `float64` DLPack capsule.
fn export_matrix(py: Python<'_>, m: &Array2<f64>) -> PyResult<Py<PyAny>> {
    let shape = vec![m.nrows() as i64, m.ncols() as i64];
    let data: Vec<f64> = m.iter().copied().collect();
    export_dlpack_f64(py, shape, data)
}

/// Export a length-`R` weight vector as a new `float64` DLPack capsule.
fn export_vector(py: Python<'_>, v: &[f64]) -> PyResult<Py<PyAny>> {
    export_dlpack_f64(py, vec![v.len() as i64], v.to_vec())
}

/// Per-mode multilinear rank for a shape: PRINet 3.0's `PolyadicTensor`
/// retains `min(rank, available)` singular vectors per mode, where the
/// available count is the mode-`n` unfolding rank `min(I_n, ∏_{k≠n} I_k)`.
fn clamped_ranks(shape: &[usize], rank: usize) -> Vec<usize> {
    shape
        .iter()
        .enumerate()
        .map(|(mode, &dim)| {
            let others: usize = shape
                .iter()
                .enumerate()
                .filter(|&(k, _)| k != mode)
                .map(|(_, s)| *s)
                .product();
            rank.min(dim.min(others)).max(1)
        })
        .collect()
}

// --- PolyadicTensor (Tucker / HOSVD) --------------------------------------

/// Stateful Tucker/HOSVD decomposition bridge over
/// [`prin_tensor::hosvd`]. Mirrors PRINet 3.0's
/// `PolyadicTensor(shape, rank).decompose(x)` / `.reconstruct()` object.
#[pyclass(name = "PolyadicTensorBridge", module = "prin._prin_core")]
pub struct PyPolyadicTensorBridge {
    shape: Vec<usize>,
    rank: usize,
    decomp: Option<PolyadicTensor>,
}

#[pymethods]
impl PyPolyadicTensorBridge {
    /// Configure (but do not run) a Tucker decomposition targeting `shape`
    /// with per-mode rank `rank`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `rank < 1` or any `shape` entry is zero
    /// (matching PRINet 3.0's `TensorDecompositionBase.__init__` guards).
    #[new]
    fn new(shape: Vec<usize>, rank: usize) -> PyResult<Self> {
        if rank < 1 {
            return Err(PyValueError::new_err(format!(
                "rank must be a positive integer, got {rank}"
            )));
        }
        if shape.iter().any(|&s| s < 1) {
            return Err(PyValueError::new_err(format!(
                "all shape dimensions must be positive, got {shape:?}"
            )));
        }
        Ok(Self {
            shape,
            rank,
            decomp: None,
        })
    }

    /// Configured per-mode rank.
    #[getter]
    fn rank(&self) -> usize {
        self.rank
    }

    /// Configured target tensor shape.
    #[getter]
    fn shape(&self) -> Vec<usize> {
        self.shape.clone()
    }

    /// Whether [`Self::decompose`] has been called successfully.
    #[getter]
    fn is_decomposed(&self) -> bool {
        self.decomp.is_some()
    }

    /// Run the HOSVD on `tensor` (a `float64` CPU contiguous DLPack tensor
    /// shaped exactly like the configured `shape`).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a dtype/device/shape mismatch or any
    /// [`prin_tensor::TensorError`] from [`prin_tensor::hosvd`].
    fn decompose(&mut self, tensor: &Bound<'_, PyAny>) -> PyResult<()> {
        let arr = arrayd_from_dlpack(tensor)?;
        if arr.shape() != self.shape.as_slice() {
            return Err(PyValueError::new_err(format!(
                "tensor shape {:?} does not match the configured shape {:?}",
                arr.shape(),
                self.shape
            )));
        }
        let ranks = clamped_ranks(&self.shape, self.rank);
        let pt = hosvd(&arr, Some(&ranks)).map_err(tensor_err_to_py)?;
        self.decomp = Some(pt);
        Ok(())
    }

    /// Reconstruct `G ×₁ U⁰ ×₂ U¹ …` as a new `float64` DLPack capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn reconstruct(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let pt = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        export_arrayd(py, &pt.reconstruct())
    }

    /// The core tensor `G` as a new `float64` DLPack capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn core(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let pt = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        export_arrayd(py, pt.core())
    }

    /// The orthogonal factor matrices `U⁰, U¹, …`, one `float64` DLPack
    /// capsule per mode.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn factors(&self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        let pt = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        pt.factors().iter().map(|f| export_matrix(py, f)).collect()
    }
}

// --- CPDecomposition (CP / PARAFAC via ALS) -------------------------------

/// Stateful CP/PARAFAC decomposition bridge over [`prin_tensor::cp_als`].
/// Mirrors PRINet 3.0's `CPDecomposition(shape, rank).decompose(x)` /
/// `.reconstruct()` object.
#[pyclass(name = "CPDecompositionBridge", module = "prin._prin_core")]
pub struct PyCPDecompositionBridge {
    shape: Vec<usize>,
    rank: usize,
    max_iter: usize,
    tol: f64,
    seed_counter: u64,
    seed_key: u64,
    decomp: Option<CPDecomposition>,
}

#[pymethods]
impl PyCPDecompositionBridge {
    /// Configure (but do not run) a CP decomposition targeting `shape` with
    /// `rank` rank-1 components.
    ///
    /// `seed_counter` / `seed_key` seed the deterministic factor
    /// initialization (Coding Standards §1.3); PRINet 3.0 used an unseeded
    /// `torch.randn`, a documented `prin-tensor` deviation.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `rank < 1`, any `shape` entry is zero,
    /// `max_iter < 1`, or `tol` is negative / non-finite.
    #[new]
    #[pyo3(signature = (shape, rank, max_iter=100, tol=1e-6, seed_counter=0, seed_key=0))]
    fn new(
        shape: Vec<usize>,
        rank: usize,
        max_iter: usize,
        tol: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        if rank < 1 {
            return Err(PyValueError::new_err(format!(
                "rank must be a positive integer, got {rank}"
            )));
        }
        if shape.iter().any(|&s| s < 1) {
            return Err(PyValueError::new_err(format!(
                "all shape dimensions must be positive, got {shape:?}"
            )));
        }
        if max_iter < 1 {
            return Err(PyValueError::new_err(format!(
                "max_iter must be >= 1, got {max_iter}"
            )));
        }
        if !tol.is_finite() || tol < 0.0 {
            return Err(PyValueError::new_err(format!(
                "tol must be finite and non-negative, got {tol}"
            )));
        }
        Ok(Self {
            shape,
            rank,
            max_iter,
            tol,
            seed_counter,
            seed_key,
            decomp: None,
        })
    }

    /// Configured number of rank-1 components.
    #[getter]
    fn rank(&self) -> usize {
        self.rank
    }

    /// Configured target tensor shape.
    #[getter]
    fn shape(&self) -> Vec<usize> {
        self.shape.clone()
    }

    /// Whether [`Self::decompose`] has been called successfully.
    #[getter]
    fn is_decomposed(&self) -> bool {
        self.decomp.is_some()
    }

    /// Fit the CP decomposition via ALS on `tensor` (a `float64` CPU
    /// contiguous DLPack tensor shaped exactly like the configured `shape`).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a dtype/device/shape mismatch or any
    /// [`prin_tensor::TensorError`] from [`prin_tensor::cp_als`] (including
    /// non-convergence within `max_iter`).
    fn decompose(&mut self, tensor: &Bound<'_, PyAny>) -> PyResult<()> {
        let arr = arrayd_from_dlpack(tensor)?;
        if arr.shape() != self.shape.as_slice() {
            return Err(PyValueError::new_err(format!(
                "tensor shape {:?} does not match the configured shape {:?}",
                arr.shape(),
                self.shape
            )));
        }
        let seed = Seed::new(self.seed_counter as u128, self.seed_key as u128);
        let result =
            cp_als(&arr, self.rank, &seed, self.max_iter, self.tol).map_err(tensor_err_to_py)?;
        self.decomp = Some(result.decomposition);
        Ok(())
    }

    /// Reconstruct `Σ_r λ_r · a_r ∘ b_r ∘ …` as a new `float64` DLPack
    /// capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn reconstruct(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let cp = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        export_arrayd(py, &cp.reconstruct())
    }

    /// The component weights `λ` (length `rank`) as a new `float64` DLPack
    /// capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn weights(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let cp = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        export_vector(py, cp.weights())
    }

    /// The factor matrices `A⁰, A¹, …` (each `[I_n, rank]`), one `float64`
    /// DLPack capsule per mode.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if called before [`Self::decompose`].
    fn factors(&self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        let cp = self.decomp.as_ref().ok_or_else(not_decomposed)?;
        cp.factors().iter().map(|f| export_matrix(py, f)).collect()
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPolyadicTensorBridge>()?;
    m.add_class::<PyCPDecompositionBridge>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clamped_ranks_truncates_to_unfolding_bound() {
        // shape (3, 4, 2): mode-0 unfolding rank = min(3, 8) = 3,
        // mode-1 = min(4, 6) = 4, mode-2 = min(2, 12) = 2.
        assert_eq!(clamped_ranks(&[3, 4, 2], 10), vec![3, 4, 2]);
        assert_eq!(clamped_ranks(&[3, 4, 2], 2), vec![2, 2, 2]);
        assert_eq!(clamped_ranks(&[3, 4, 2], 1), vec![1, 1, 1]);
    }

    #[test]
    fn polyadic_bridge_rejects_bad_config() {
        assert!(PyPolyadicTensorBridge::new(vec![4, 4], 0).is_err());
        assert!(PyPolyadicTensorBridge::new(vec![0, 4], 2).is_err());
        assert!(PyPolyadicTensorBridge::new(vec![4, 4], 2).is_ok());
    }

    #[test]
    fn cp_bridge_rejects_bad_config() {
        assert!(PyCPDecompositionBridge::new(vec![4, 4], 0, 100, 1e-6, 0, 0).is_err());
        assert!(PyCPDecompositionBridge::new(vec![4, 4], 2, 0, 1e-6, 0, 0).is_err());
        assert!(PyCPDecompositionBridge::new(vec![4, 4], 2, 100, -1.0, 0, 0).is_err());
        assert!(PyCPDecompositionBridge::new(vec![4, 4], 2, 100, f64::NAN, 0, 0).is_err());
        assert!(PyCPDecompositionBridge::new(vec![4, 4], 2, 100, 1e-6, 0, 0).is_ok());
    }

    #[test]
    fn bridges_start_undecomposed() {
        let pt = PyPolyadicTensorBridge::new(vec![4, 4], 2).unwrap();
        assert!(!pt.is_decomposed());
        assert_eq!(pt.rank(), 2);
        assert_eq!(pt.shape(), vec![4, 4]);

        let cp = PyCPDecompositionBridge::new(vec![4, 4], 3, 100, 1e-6, 0, 0).unwrap();
        assert!(!cp.is_decomposed());
        assert_eq!(cp.rank(), 3);
    }
}

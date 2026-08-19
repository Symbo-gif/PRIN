//! Shared PyO3/DLPack bridge helpers for `prin-train` Torch bridges
//! (Exec-WP-026 S1).
//!
//! WP-025's bridge (`train.rs`) hand-wrote rank-2-specific DLPack
//! decode/encode/checkpoint helpers. WP-026's modules need rank-2 **and**
//! rank-3 tensors and several share near-identical method shapes, so this
//! module generalizes those helpers to an arbitrary const-generic rank `D`
//! (Coding Standards §1.1, "one algorithm, one implementation") — every
//! bridge file in this crate, including `train.rs`'s own two WP-025 bridges,
//! calls these instead of re-deriving the pattern per module.

use burn::backend::{Autodiff, NdArray};
use burn::module::Module;
use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};
use burn::tensor::{Tensor, TensorData};
use prin_train::error::TrainError;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use super::super::dlpack::{export_dlpack_f64, read_dlpack_f64};

/// CPU autodiff backend every bridge in this crate uses: `NdArray<f64>`
/// matches `torch.autograd.gradcheck`'s float64 requirement exactly, and is
/// the same backend `prin-train`'s own gradient tests validate against.
pub(crate) type BridgeBackend = Autodiff<NdArray<f64>>;

/// Convert a [`TrainError`] into a Python `ValueError`.
pub(crate) fn train_err_to_py(err: TrainError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// The default device for [`BridgeBackend`].
pub(crate) fn device() -> <BridgeBackend as burn::tensor::backend::Backend>::Device {
    Default::default()
}

/// A leaf tensor plus the plain `(dims, data)` pair used to rebuild it inside
/// a `backward()` recompute.
pub(crate) type TensorWithData<const D: usize> = (Tensor<BridgeBackend, D>, Vec<usize>, Vec<f64>);

/// Decode a rank-`D` `float64` DLPack tensor as a gradient-tracked leaf
/// tensor, also returning the plain `(dims, data)` pair used to rebuild the
/// leaf inside a `backward()` recompute (see `train.rs`'s module docs for why
/// the recompute-on-backward design is required).
pub(crate) fn tensor_from_dlpack_with_data<const D: usize>(
    obj: &Bound<'_, PyAny>,
) -> PyResult<TensorWithData<D>> {
    let (shape, data) = read_dlpack_f64(obj)?;
    if shape.len() != D {
        return Err(PyValueError::new_err(format!(
            "expected a {D}-D tensor, got shape {shape:?}"
        )));
    }
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    let data_copy = data.clone();
    let tensor = Tensor::from_data(TensorData::new(data, dims.clone()), &device()).require_grad();
    Ok((tensor, dims, data_copy))
}

/// [`tensor_from_dlpack_with_data`] for an optional input (e.g.
/// `OscillatoryAttention`'s externally-supplied `phase`).
pub(crate) fn optional_tensor_from_dlpack_with_data<const D: usize>(
    obj: Option<&Bound<'_, PyAny>>,
) -> PyResult<Option<TensorWithData<D>>> {
    obj.map(tensor_from_dlpack_with_data::<D>).transpose()
}

/// Decode a rank-`D` `float64` DLPack tensor without gradient tracking and
/// without saving a plain-data copy, for bridge methods that are
/// non-differentiable end to end (e.g. `PhaseTracker::match_frames`,
/// `AdaptiveOscillatorAllocator::allocate`) — no `backward()` will ever be
/// called on their output, so there is nothing to recompute.
pub(crate) fn tensor_from_dlpack<const D: usize>(
    obj: &Bound<'_, PyAny>,
) -> PyResult<Tensor<BridgeBackend, D>> {
    let (shape, data) = read_dlpack_f64(obj)?;
    if shape.len() != D {
        return Err(PyValueError::new_err(format!(
            "expected a {D}-D tensor, got shape {shape:?}"
        )));
    }
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    Ok(Tensor::from_data(TensorData::new(data, dims), &device()))
}

/// Decode a rank-`D` `float64` DLPack tensor without gradient tracking (used
/// for an incoming cotangent, which must not itself carry a graph).
pub(crate) fn plain_tensor_from_dlpack<const D: usize>(
    obj: &Bound<'_, PyAny>,
    expected: [usize; D],
) -> PyResult<Tensor<BridgeBackend, D>> {
    let (shape, data) = read_dlpack_f64(obj)?;
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    if dims.as_slice() != expected {
        return Err(PyValueError::new_err(format!(
            "grad_output shape {dims:?} does not match the forward output shape {expected:?}"
        )));
    }
    Ok(Tensor::from_data(TensorData::new(data, dims), &device()))
}

/// Export a rank-`D` inner-backend (non-autodiff) tensor as a new DLPack
/// capsule.
pub(crate) fn export_tensor<const D: usize>(
    py: Python<'_>,
    tensor: Tensor<NdArray<f64>, D>,
) -> PyResult<Py<PyAny>> {
    let shape: Vec<i64> = tensor.dims().iter().map(|&d| d as i64).collect();
    let data = tensor
        .into_data()
        .to_vec::<f64>()
        .map_err(|e| PyValueError::new_err(format!("failed to read tensor data: {e:?}")))?;
    export_dlpack_f64(py, shape, data)
}

/// Deserialize checkpoint bytes into a Burn record, converting both a
/// structured `RecorderError` and an internal `burn-core` panic on malformed
/// bytes into a typed `ValueError`.
///
/// `bytes` is untrusted public-boundary input (Coding Standards §2.2):
/// `burn-core`'s `BinBytesRecorder` decoder panics (rather than returning
/// `Err`) on some malformed inputs, so this wraps the call in `catch_unwind`
/// to guarantee a clean `PyResult` at this FFI boundary instead of an
/// uncaught panic propagating into Python.
pub(crate) fn load_checkpoint_record<M: Module<BridgeBackend>>(
    bytes: &[u8],
) -> PyResult<M::Record> {
    let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
    let owned = bytes.to_vec();
    let dev = device();

    // Malformed-checkpoint panics are an expected, user-triggerable error
    // path here (not a bug), so the default panic hook's "thread panicked"
    // stderr noise is suppressed for the duration of this call. This briefly
    // touches the process-wide panic hook; `prin-py` does not spawn
    // background threads of its own, so the window where an unrelated
    // thread's panic message could be swallowed is not exercised in
    // practice.
    let previous_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(|_| {}));
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        Recorder::<BridgeBackend>::load(&recorder, owned, &dev)
    }));
    std::panic::set_hook(previous_hook);

    result
        .map_err(|_| {
            PyValueError::new_err("checkpoint deserialization failed: malformed record bytes")
        })?
        .map_err(|e| PyValueError::new_err(format!("checkpoint deserialization failed: {e}")))
}

/// Serialize `module`'s parameters to opaque, byte-exact checkpoint bytes
/// (`burn::record::BinBytesRecorder<DoublePrecisionSettings>`).
pub(crate) fn record_to_bytes<M: Module<BridgeBackend>>(module: &M) -> PyResult<Vec<u8>> {
    let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
    Recorder::<BridgeBackend>::record(&recorder, module.clone().into_record(), ())
        .map_err(|e| PyValueError::new_err(format!("checkpoint serialization failed: {e}")))
}

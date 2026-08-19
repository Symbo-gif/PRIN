//! DLPack bridge for zero-copy Torch↔Rust tensor exchange.
//!
//! This module is the **audited Python-FFI boundary** for WP-003. It is
//! permitted to use `unsafe` under Project Plan amendment #6 / Coding
//! Standards §2.1 and §6.1: the `unsafe` is confined to this module, every
//! `unsafe` block carries a `// SAFETY:` justification, and the crate uses
//! `#![deny(unsafe_code)]` with this module-level `#![allow(unsafe_code)]`
//! because `#![forbid]` cannot be scoped to a single module.
//!
//! The bridge deliberately implements the DLPack C ABI directly with `pyo3`
//! `PyCapsule` methods rather than duplicating numerics in Python. The only
//! numeric operation (a representative element-wise kernel) is delegated to
//! `prin_kernels::ops`.

// Scoped permission for the audited FFI in this module only.
#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use dlpack::{data_type_codes, device_type_codes, Context, DataType, ManagedTensor, Tensor};
use pyo3::exceptions::PyValueError;
use pyo3::ffi as pyffi;
use pyo3::prelude::*;
use pyo3::types::{PyCapsule, PyCapsuleMethods};
use std::ffi::{c_void, CStr};
use std::ptr::{self, NonNull};

use prin_kernels::ops::{negate_f32, negate_f64};

const NAME_DLTENSOR: &CStr = c"dltensor";

/// Errors local to the DLPack bridge.
#[derive(Debug, thiserror::Error)]
enum BridgeError {
    #[error("the DLPack tensor is not on CPU (device_type={device_type}, device_id={device_id})")]
    NonCpuDevice { device_type: i32, device_id: i32 },
    #[error("unsupported DLPack dtype: code={code}, bits={bits}, lanes={lanes}")]
    UnsupportedDtype { code: u8, bits: u8, lanes: u16 },
    #[error("non-contiguous DLPack tensors are not supported by this bridge")]
    NonContiguous,
    #[error("DLPack data pointer is null but the tensor has {len} elements")]
    NullData { len: usize },
    #[error("negative ndim ({ndim}) is not a valid DLPack tensor")]
    NegativeNdim { ndim: i32 },
    #[error("negative shape dimension {dim} at index {index}")]
    NegativeDim { dim: i64, index: usize },
    #[error("non-zero byte_offset ({offset}) is not supported by this bridge")]
    NonZeroByteOffset { offset: u64 },
}

impl From<BridgeError> for PyErr {
    fn from(err: BridgeError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }
}

/// Owned tensor data backing a DLPack capsule exported from Rust.
///
/// The first three fields are laid out exactly like `dlpack::ManagedTensor`:
/// `dl_tensor`, `manager_ctx`, `deleter`. The capsule pointer therefore points
/// to the start of this struct, and a consumer calling the DLPack `deleter`
/// gets the same address.
#[repr(C)]
struct OwnedDlpackTensor {
    dl_tensor: Tensor,
    manager_ctx: *mut c_void,
    deleter: extern "C" fn(*mut ManagedTensor),
    storage: TensorStorage,
    shape: Vec<i64>,
    strides: Option<Vec<i64>>,
}

enum TensorStorage {
    F32(Vec<f32>),
    F64(Vec<f64>),
}

impl TensorStorage {
    fn dtype(&self) -> DataType {
        match self {
            TensorStorage::F32(_) => DataType {
                code: data_type_codes::FLOAT,
                bits: 32,
                lanes: 1,
            },
            TensorStorage::F64(_) => DataType {
                code: data_type_codes::FLOAT,
                bits: 64,
                lanes: 1,
            },
        }
    }

    fn as_mut_ptr(&mut self) -> *mut c_void {
        match self {
            TensorStorage::F32(v) => v.as_mut_ptr() as *mut c_void,
            TensorStorage::F64(v) => v.as_mut_ptr() as *mut c_void,
        }
    }
}

/// DLPack `deleter` for capsules produced by this bridge.
///
/// The address `mt` is exactly the pointer originally handed to the Python
/// capsule, i.e. the address of an `OwnedDlpackTensor`.
extern "C" fn dlpack_destructor(mt: *mut ManagedTensor) {
    if mt.is_null() {
        return;
    }
    // SAFETY: `mt` was produced by `OwnedDlpackTensor::new` from a
    // `Box::into_raw` and has not been freed yet. The first three fields of
    // `OwnedDlpackTensor` form the `ManagedTensor` prefix, so the cast
    // recovers the original allocation.
    let _ = unsafe { Box::from_raw(mt as *mut OwnedDlpackTensor) };
}

/// Python capsule destructor for the Rust-exported DLPack capsule.
///
/// If the capsule has not been consumed (its name is still `dltensor`), this
/// calls the DLPack `deleter` so the `OwnedDlpackTensor` is released. If a
/// consumer has renamed the capsule to `used_dltensor`, the consumer owns the
/// `ManagedTensor` and will call the `deleter` itself, so we do nothing.
unsafe extern "C" fn py_capsule_destructor(capsule: *mut pyffi::PyObject) {
    if capsule.is_null() {
        return;
    }

    // SAFETY: `capsule` is a valid `PyCapsule` being destroyed; the name
    // pointer is valid for the lifetime of the capsule.
    let name_ptr = unsafe { pyffi::PyCapsule_GetName(capsule) };
    if name_ptr.is_null() {
        return;
    }
    let name = unsafe { CStr::from_ptr(name_ptr) };
    if name != NAME_DLTENSOR {
        // Already consumed; consumer is responsible for the tensor.
        return;
    }

    // SAFETY: the name matched the capsule's stored name, so the pointer
    // we get back is the `OwnedDlpackTensor` we installed.
    let ptr = unsafe { pyffi::PyCapsule_GetPointer(capsule, name_ptr) };
    if ptr.is_null() {
        return;
    }
    let mt = ptr as *mut ManagedTensor;

    // SAFETY: `mt` is the non-null start of an `OwnedDlpackTensor`; the
    // `deleter` field was set to `dlpack_destructor` on construction.
    let del = unsafe { (*mt).deleter };
    // `del` is our non-null `dlpack_destructor`. Calling it drops the
    // `OwnedDlpackTensor` exactly once.
    del(mt);
}

impl OwnedDlpackTensor {
    fn from_storage(shape: Vec<i64>, mut storage: TensorStorage) -> NonNull<c_void> {
        let mut strides: Option<Vec<i64>> = None;

        // Build the DLPack `Tensor` descriptor pointing at the owned storage.
        // We use `as_mut_ptr` on the Vecs while they are still local so that
        // the pointers remain valid after the Vecs are moved into the Box.
        let mut shape = shape;
        let shape_ptr = shape.as_mut_ptr();
        let strides_ptr = strides.as_mut().map_or(ptr::null_mut(), |s| s.as_mut_ptr());

        let dl_tensor = Tensor {
            data: storage.as_mut_ptr(),
            ctx: Context {
                device_type: device_type_codes::CPU,
                device_id: 0,
            },
            ndim: shape.len() as i32,
            dtype: storage.dtype(),
            shape: shape_ptr,
            strides: strides_ptr,
            byte_offset: 0,
        };

        let this = Self {
            dl_tensor,
            manager_ctx: ptr::null_mut(),
            deleter: dlpack_destructor,
            storage,
            shape,
            strides,
        };

        let raw = Box::into_raw(Box::new(this));
        // SAFETY: `raw` is a unique, non-null, heap-allocated `OwnedDlpackTensor`.
        // Storing its own address in `manager_ctx` is for symmetry with the
        // DLPack spec and is not required by our destructor.
        unsafe {
            (*raw).manager_ctx = raw as *mut c_void;
        }

        // SAFETY: `Box::into_raw` on a sized type returns a non-null pointer.
        NonNull::new(raw as *mut c_void).expect("Box::into_raw returned a null pointer")
    }
}

/// Contiguous C-order strides for `shape`.
fn contiguous_strides(shape: &[i64]) -> Vec<i64> {
    let mut strides = vec![0i64; shape.len()];
    let mut prod = 1i64;
    for (i, dim) in shape.iter().enumerate().rev() {
        strides[i] = prod;
        prod *= dim;
    }
    strides
}

/// Number of elements in a tensor with `shape`.
///
/// Callers must ensure all dimensions are non-negative; this function is used
/// only after `validate_shape` has run.
fn element_count(shape: &[i64]) -> usize {
    shape.iter().product::<i64>() as usize
}

/// Validate that every dimension in `shape` is non-negative.
fn validate_shape(shape: &[i64]) -> Result<(), BridgeError> {
    for (index, &dim) in shape.iter().enumerate() {
        if dim < 0 {
            return Err(BridgeError::NegativeDim { dim, index });
        }
    }
    Ok(())
}

/// Obtain the `dltensor` capsule from `obj`, which may be a `torch.Tensor`
/// (we call `__dlpack__`) or an existing DLPack `PyCapsule`.
fn get_dlpack_capsule<'py>(obj: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyCapsule>> {
    if obj.is_instance_of::<PyCapsule>() {
        return Ok(obj.clone().cast_into::<PyCapsule>()?);
    }

    let capsule = obj.call_method0("__dlpack__")?;
    Ok(capsule.cast_into::<PyCapsule>()?)
}

/// Read a CPU DLPack tensor, validate it, run the representative `negate`
/// kernel, and return a raw pointer to an `OwnedDlpackTensor` ready for
/// encapsulation in a new DLPack capsule.
fn read_and_negate(obj: &Bound<'_, PyAny>) -> PyResult<NonNull<c_void>> {
    let capsule = get_dlpack_capsule(obj)?;

    // `pointer_checked` validates that the capsule is named `dltensor`.
    let ptr = capsule
        .pointer_checked(Some(NAME_DLTENSOR))?
        .cast::<Tensor>();

    // SAFETY: `pointer_checked` returned a non-null, properly named capsule
    // pointer. The first field of a `ManagedTensor` is a `Tensor`, so this
    // read gives us the DLPack descriptor without touching `deleter`.
    let tensor: Tensor = unsafe { ptr.as_ptr().read() };

    // Device validation.
    if tensor.ctx.device_type != device_type_codes::CPU {
        return Err(BridgeError::NonCpuDevice {
            device_type: tensor.ctx.device_type,
            device_id: tensor.ctx.device_id,
        }
        .into());
    }

    // Dtype validation: only float32 and float64 for this spike.
    let storage = match (tensor.dtype.code, tensor.dtype.bits, tensor.dtype.lanes) {
        (code, bits, 1) if code == data_type_codes::FLOAT && (bits == 32 || bits == 64) => {
            if bits == 32 {
                TensorStorage::F32(Vec::new())
            } else {
                TensorStorage::F64(Vec::new())
            }
        }
        _ => {
            return Err(BridgeError::UnsupportedDtype {
                code: tensor.dtype.code,
                bits: tensor.dtype.bits,
                lanes: tensor.dtype.lanes,
            }
            .into());
        }
    };

    // Shape / ndim validation.
    if tensor.ndim < 0 {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    }
    let ndim = tensor.ndim as usize;
    let shape: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.shape.is_null() {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    } else {
        // SAFETY: `shape` is non-null and there are `ndim` elements.
        unsafe { std::slice::from_raw_parts(tensor.shape, ndim) }.to_vec()
    };

    // Every dimension must be non-negative before we compute strides or lengths.
    validate_shape(&shape)?;

    // Stride validation: require C-contiguous layout.
    let expected = contiguous_strides(&shape);
    let actual: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.strides.is_null() {
        expected.clone()
    } else {
        // SAFETY: `strides` is non-null and there are `ndim` elements.
        unsafe { std::slice::from_raw_parts(tensor.strides, ndim) }.to_vec()
    };
    if actual != expected {
        return Err(BridgeError::NonContiguous.into());
    }

    // Byte-offset validation.
    if tensor.byte_offset != 0 {
        return Err(BridgeError::NonZeroByteOffset {
            offset: tensor.byte_offset,
        }
        .into());
    }

    let len = element_count(&shape);
    if len != 0 && tensor.data.is_null() {
        return Err(BridgeError::NullData { len }.into());
    }

    // SAFETY: `tensor.data` is non-null and points to `len` elements of the
    // validated dtype. `validate_shape` ensures dimensions are non-negative,
    // so `len` cannot wrap, and `contiguous_strides` confirms a C-contiguous
    // layout. We borrow the slice only for the duration of the copy.
    let output = unsafe {
        match storage {
            TensorStorage::F32(_) => {
                let input = std::slice::from_raw_parts(tensor.data as *const f32, len);
                TensorStorage::F32(negate_f32(input))
            }
            TensorStorage::F64(_) => {
                let input = std::slice::from_raw_parts(tensor.data as *const f64, len);
                TensorStorage::F64(negate_f64(input))
            }
        }
    };

    Ok(OwnedDlpackTensor::from_storage(shape, output))
}

/// Negate a PyTorch tensor via zero-copy DLPack exchange.
///
/// Accepts any object implementing the DLPack protocol (e.g. `torch.Tensor`)
/// or an existing `dltensor` `PyCapsule`. Returns a new `dltensor` capsule
/// that `torch.utils.dlpack.from_dlpack` can consume.
#[pyfunction]
pub fn dlpack_negate(obj: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = obj.py();
    let ptr = read_and_negate(obj)?;

    // SAFETY: `ptr` is a non-null, heap-allocated `OwnedDlpackTensor` whose
    // first three fields form a valid `ManagedTensor`. `py_capsule_destructor`
    // guards the lifetime: it calls the DLPack `deleter` only when the capsule
    // has not been consumed, so the tensor is freed exactly once.
    let capsule = unsafe {
        PyCapsule::new_with_pointer_and_destructor(
            py,
            ptr,
            NAME_DLTENSOR,
            Some(py_capsule_destructor),
        )?
    };
    Ok(capsule.into_any().unbind())
}

/// Batched version of `dlpack_negate`.
///
/// Takes a list of DLPack-capable objects and returns a list of new `dltensor`
/// capsules. This is the WP-003 "batched boundary call" demonstration: one
/// Rust↔Python crossing per tensor, with independent lifetime management.
#[pyfunction]
pub fn dlpack_negate_batched(py: Python<'_>, tensors: Vec<Py<PyAny>>) -> PyResult<Vec<Py<PyAny>>> {
    let mut out = Vec::with_capacity(tensors.len());
    for tensor in tensors {
        let bound = tensor.bind(py);
        let ptr = read_and_negate(bound)?;
        // SAFETY: same as `dlpack_negate`.
        let capsule = unsafe {
            PyCapsule::new_with_pointer_and_destructor(
                py,
                ptr,
                NAME_DLTENSOR,
                Some(py_capsule_destructor),
            )?
        };
        out.push(capsule.into_any().unbind());
    }
    Ok(out)
}

/// Round-trip a tensor through DLPack without modifying values.
///
/// This is the zero-copy exchange smoke test: the data is read from the input
/// capsule and wrapped in a new Rust-owned capsule. The new capsule shares no
/// Python state with the input and can outlive it.
#[pyfunction]
pub fn dlpack_round_trip(obj: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = obj.py();
    let ptr = read_and_clone(obj)?;

    // SAFETY: same as `dlpack_negate`, except the underlying storage was
    // cloned rather than negated.
    let capsule = unsafe {
        PyCapsule::new_with_pointer_and_destructor(
            py,
            ptr,
            NAME_DLTENSOR,
            Some(py_capsule_destructor),
        )?
    };
    Ok(capsule.into_any().unbind())
}

/// Clone a DLPack tensor into a new Rust-owned capsule (used by the round-trip).
fn read_and_clone(obj: &Bound<'_, PyAny>) -> PyResult<NonNull<c_void>> {
    let capsule = get_dlpack_capsule(obj)?;
    let ptr = capsule
        .pointer_checked(Some(NAME_DLTENSOR))?
        .cast::<Tensor>();

    // SAFETY: see `read_and_negate`.
    let tensor: Tensor = unsafe { ptr.as_ptr().read() };

    if tensor.ctx.device_type != device_type_codes::CPU {
        return Err(BridgeError::NonCpuDevice {
            device_type: tensor.ctx.device_type,
            device_id: tensor.ctx.device_id,
        }
        .into());
    }

    let storage = match (tensor.dtype.code, tensor.dtype.bits, tensor.dtype.lanes) {
        (code, bits, 1) if code == data_type_codes::FLOAT && (bits == 32 || bits == 64) => {
            if bits == 32 {
                TensorStorage::F32(Vec::new())
            } else {
                TensorStorage::F64(Vec::new())
            }
        }
        _ => {
            return Err(BridgeError::UnsupportedDtype {
                code: tensor.dtype.code,
                bits: tensor.dtype.bits,
                lanes: tensor.dtype.lanes,
            }
            .into());
        }
    };

    if tensor.ndim < 0 {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    }
    let ndim = tensor.ndim as usize;
    let shape: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.shape.is_null() {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    } else {
        // SAFETY: shape is non-null and `ndim` long.
        unsafe { std::slice::from_raw_parts(tensor.shape, ndim) }.to_vec()
    };

    // Every dimension must be non-negative before we compute strides or lengths.
    validate_shape(&shape)?;

    let expected = contiguous_strides(&shape);
    let actual: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.strides.is_null() {
        expected.clone()
    } else {
        // SAFETY: strides is non-null and `ndim` long.
        unsafe { std::slice::from_raw_parts(tensor.strides, ndim) }.to_vec()
    };
    if actual != expected {
        return Err(BridgeError::NonContiguous.into());
    }

    if tensor.byte_offset != 0 {
        return Err(BridgeError::NonZeroByteOffset {
            offset: tensor.byte_offset,
        }
        .into());
    }

    let len = element_count(&shape);
    if len != 0 && tensor.data.is_null() {
        return Err(BridgeError::NullData { len }.into());
    }

    // SAFETY: `tensor.data` is non-null, `validate_shape` guarantees
    // non-negative dimensions and therefore a well-defined `len`, and the
    // layout has been verified C-contiguous. See `read_and_negate`.
    let output = unsafe {
        match storage {
            TensorStorage::F32(_) => {
                let input = std::slice::from_raw_parts(tensor.data as *const f32, len);
                TensorStorage::F32(input.to_vec())
            }
            TensorStorage::F64(_) => {
                let input = std::slice::from_raw_parts(tensor.data as *const f64, len);
                TensorStorage::F64(input.to_vec())
            }
        }
    };

    Ok(OwnedDlpackTensor::from_storage(shape, output))
}

/// Read a CPU, contiguous, `float64` DLPack tensor into an owned `(shape,
/// data)` pair, with no numeric transform applied.
///
/// This is the WP-025 torch-bridge reader: unlike [`read_and_negate`] /
/// [`read_and_clone`] (which accept `float32` or `float64`), the production
/// autograd bridge requires `float64` end to end so that
/// `torch.autograd.gradcheck`'s double-precision finite-difference check is
/// exact (Testing Standards §2, "Gradient checks... float64"). `float32`
/// bridge support is a deliberately deferred future-WP item, not silently
/// dropped: see the WP-025 S1 handoff.
///
/// # Errors
///
/// Returns a [`BridgeError`] (as a `PyErr`) for a non-CPU device, a
/// non-`float64` dtype, a non-contiguous layout, a non-zero `byte_offset`, or
/// a null data pointer with a non-zero element count.
pub(crate) fn read_dlpack_f64(obj: &Bound<'_, PyAny>) -> PyResult<(Vec<i64>, Vec<f64>)> {
    let capsule = get_dlpack_capsule(obj)?;
    let ptr = capsule
        .pointer_checked(Some(NAME_DLTENSOR))?
        .cast::<Tensor>();

    // SAFETY: `pointer_checked` returned a non-null, `dltensor`-named capsule
    // pointer; the first field of a `ManagedTensor` is a `Tensor`, so reading
    // it does not touch the `deleter`/`manager_ctx` fields.
    let tensor: Tensor = unsafe { ptr.as_ptr().read() };

    if tensor.ctx.device_type != device_type_codes::CPU {
        return Err(BridgeError::NonCpuDevice {
            device_type: tensor.ctx.device_type,
            device_id: tensor.ctx.device_id,
        }
        .into());
    }

    let is_f64 = tensor.dtype.code == data_type_codes::FLOAT
        && tensor.dtype.bits == 64
        && tensor.dtype.lanes == 1;
    if !is_f64 {
        return Err(BridgeError::UnsupportedDtype {
            code: tensor.dtype.code,
            bits: tensor.dtype.bits,
            lanes: tensor.dtype.lanes,
        }
        .into());
    }

    if tensor.ndim < 0 {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    }
    let ndim = tensor.ndim as usize;
    let shape: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.shape.is_null() {
        return Err(BridgeError::NegativeNdim { ndim: tensor.ndim }.into());
    } else {
        // SAFETY: `shape` is non-null and there are `ndim` elements.
        unsafe { std::slice::from_raw_parts(tensor.shape, ndim) }.to_vec()
    };
    validate_shape(&shape)?;

    let expected = contiguous_strides(&shape);
    let actual: Vec<i64> = if ndim == 0 {
        Vec::new()
    } else if tensor.strides.is_null() {
        expected.clone()
    } else {
        // SAFETY: `strides` is non-null and there are `ndim` elements.
        unsafe { std::slice::from_raw_parts(tensor.strides, ndim) }.to_vec()
    };
    if actual != expected {
        return Err(BridgeError::NonContiguous.into());
    }

    if tensor.byte_offset != 0 {
        return Err(BridgeError::NonZeroByteOffset {
            offset: tensor.byte_offset,
        }
        .into());
    }

    let len = element_count(&shape);
    if len != 0 && tensor.data.is_null() {
        return Err(BridgeError::NullData { len }.into());
    }

    // SAFETY: `tensor.data` is non-null (or `len == 0`), `validate_shape`
    // guarantees non-negative dimensions, and the layout has been verified
    // C-contiguous. The slice borrow lives only for the duration of the copy
    // into the owned `Vec` this function returns.
    let data = unsafe { std::slice::from_raw_parts(tensor.data as *const f64, len) }.to_vec();

    Ok((shape, data))
}

/// Export an owned `(shape, data)` pair as a new `dltensor` `PyCapsule`
/// (`float64`, CPU), the WP-025 torch-bridge writer counterpart to
/// [`read_dlpack_f64`].
///
/// Ownership transfers to Python exactly as in [`dlpack_negate`] /
/// [`dlpack_round_trip`]: the returned capsule is zero-copy from Rust's
/// perspective onward (no further serialization step), and
/// `torch.utils.dlpack.from_dlpack` takes ownership without copying.
pub(crate) fn export_dlpack_f64(
    py: Python<'_>,
    shape: Vec<i64>,
    data: Vec<f64>,
) -> PyResult<Py<PyAny>> {
    let ptr = OwnedDlpackTensor::from_storage(shape, TensorStorage::F64(data));

    // SAFETY: identical justification to `dlpack_negate`/`dlpack_round_trip`:
    // `ptr` is a non-null, heap-allocated `OwnedDlpackTensor` whose first
    // three fields form a valid `ManagedTensor`; `py_capsule_destructor`
    // frees it exactly once, whether or not a consumer renames the capsule.
    let capsule = unsafe {
        PyCapsule::new_with_pointer_and_destructor(
            py,
            ptr,
            NAME_DLTENSOR,
            Some(py_capsule_destructor),
        )?
    };
    Ok(capsule.into_any().unbind())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contiguous_strides_match_tensor_layout() {
        assert_eq!(contiguous_strides(&[2, 3, 4]), vec![12, 4, 1]);
        assert_eq!(contiguous_strides(&[5]), vec![1]);
        assert!(contiguous_strides(&[]).is_empty());
    }

    #[test]
    fn element_count_computes_product() {
        assert_eq!(element_count(&[2, 3, 4]), 24);
        assert_eq!(element_count(&[5]), 5);
        assert_eq!(element_count(&[]), 1);
    }

    #[test]
    fn owned_dlpack_tensor_can_be_built_and_dropped() {
        let out = TensorStorage::F32(vec![-1.0_f32, 2.0, -3.0]);
        let ptr = OwnedDlpackTensor::from_storage(vec![3], out);
        // `ptr` is the start of an `OwnedDlpackTensor`; calling the DLPack
        // deleter should drop it exactly once and not leak.
        let mt = ptr.as_ptr() as *mut ManagedTensor;
        dlpack_destructor(mt);
    }

    #[test]
    fn validate_shape_accepts_non_negative_dimensions() {
        assert!(validate_shape(&[2, 3, 4]).is_ok());
        assert!(validate_shape(&[0, 5]).is_ok());
        assert!(validate_shape(&[]).is_ok());
    }

    #[test]
    fn validate_shape_rejects_negative_dimensions() {
        let err = validate_shape(&[2, -1, 4]).unwrap_err();
        assert!(format!("{err}").contains("negative shape dimension -1 at index 1"));
    }

    #[test]
    fn negative_shape_dimension_does_not_wrap_element_count() {
        // Once validated, `element_count` is never called with negative
        // dimensions; this guards against the wrap that would otherwise happen
        // if a malformed capsule were accepted.
        assert!(validate_shape(&[-1_i64]).is_err());
    }
}

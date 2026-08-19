//! PyO3 `torch.autograd.Function` bridges for `prin-train` (WP-025).
//!
//! Every bridge in this module follows the same shape:
//!
//! - A `*Bridge` `#[pyclass]` owns a Burn `Module` built on
//!   `Autodiff<NdArray<f64>>` — the same backend `prin-train`'s own gradient
//!   tests already use (`bands.rs`/`layers.rs`/`activations.rs`
//!   `TestAutodiffBackend`). Parameters live only in Rust; they are trained by
//!   the WP-024 `OscillatorOptimizer` implementations (`Rip`/`Scalr`/`SyncGd`),
//!   not by `torch.optim`, so the bridge exposes only the differentiable
//!   input/output boundary a larger PyTorch model needs to chain gradients
//!   through (Coding Standards §3.2: "boundary crossings are batched — one
//!   call per integration, not per step").
//! - `forward(x)` decodes `x` from a DLPack capsule (`float64` CPU,
//!   [`super::super::dlpack::read_dlpack_f64`]), runs the *entire* Rust
//!   forward pass in one call (`ResonanceLayer::forward` already loops
//!   `n_steps` internally in Rust — no per-step Python↔Rust crossing), and
//!   returns `(output_capsule, ctx)`.
//! - `ctx` is a `*Ctx` `#[pyclass]` holding what `backward(grad_output)`
//!   needs: a cloned handle to the layer (cheap — Burn `Module` parameters
//!   are `Rc`-shared) and the plain (non-graph-tracked) input values. Burn's
//!   autodiff graph is consumed by its own `.backward()` traversal (no
//!   `retain_graph` equivalent: a second `.backward()` against a graph
//!   already walked once returns `None` from `Tensor::grad` — confirmed
//!   empirically during S1), so `backward()` rebuilds a fresh
//!   `require_grad()` leaf from the saved input values and **re-runs the
//!   forward pass** before seeding the reverse pass
//!   (`(output * grad_output).sum().backward()`, the standard
//!   vector-Jacobian-product trick, matching every existing gradient test in
//!   this crate). This recompute-on-backward is required, not incidental:
//!   `torch.autograd.gradcheck`'s analytical Jacobian calls `backward()` once
//!   per output element against the *same* saved forward pass (PyTorch's own
//!   `retain_graph=True` contract), so a single-use context would fail every
//!   gradcheck in this module's test suite. It is also the same
//!   recompute-for-memory tradeoff `torch.utils.checkpoint` makes
//!   deliberately, not a defect — see the WP-025 S1 handoff for the resulting
//!   benchmark evidence. Lifetime safety here means `ctx` needs no unsafe
//!   pointer bookkeeping at all: everything it holds is an owned, safe Rust
//!   value living exactly as long as the Python-side `ctx` object does
//!   (`#[pyclass(unsendable)]`: Burn's `NdArray` tensors are not `Send`, and
//!   every PyO3 call is already GIL-serialized, so a Python-thread-confined
//!   class is the correct, zero-`unsafe` way to hold them) — this module
//!   introduces no new `unsafe` code; all DLPack FFI is delegated to the
//!   already-audited `dlpack` module, Project Plan amendment #6.
//! - `state_dict()` / `load_state_dict()` expose checkpoint support by
//!   delegating entirely to `burn::record` (`BinBytesRecorder<
//!   DoublePrecisionSettings>`), the same mechanism
//!   `layers.rs::record_roundtrip_preserves_parameters` already tests — no
//!   new serialization numerics.
//!
//! Two bridges are delivered this session: [`PyResonanceLayerBridge`]
//! (multi-tensor matrix/vector parameters, `n_steps`-step integration) and
//! [`PyGatedPhaseActivationBridge`] (small per-feature vector parameters,
//! single elementwise pass). Together they exercise both structural shapes
//! WP-026's `PhaseTracker`/`HybridPRINetV2` will need to compose. Bridging
//! `prin-train`'s remaining components (`bands::DiscreteDeltaThetaGamma`,
//! `energy::HolomorphicEnergy`, `hep::HolomorphicEp`,
//! `inhibition::FeedbackInhibition`) is an explicit out-of-scope discovery
//! for a future WP (see the WP-025 S1 handoff) — this module establishes the
//! reusable pattern, not an exhaustive port.

use burn::backend::{Autodiff, NdArray};
use burn::module::Module;
use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};
use burn::tensor::{Tensor, TensorData};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use prin_dynamics::Seed;
use prin_train::activations::{GatedPhaseActivation, GatedPhaseActivationConfig};
use prin_train::error::TrainError;
use prin_train::layers::{ResonanceLayer, ResonanceLayerConfig};

use super::super::dlpack::{export_dlpack_f64, read_dlpack_f64};

/// CPU autodiff backend every WP-025 bridge uses: `NdArray<f64>` matches
/// `torch.autograd.gradcheck`'s float64 requirement exactly, and is the same
/// backend `prin-train`'s own gradient tests already validate against
/// (`TestAutodiffBackend` in `bands.rs`/`layers.rs`/`activations.rs`).
type BridgeBackend = Autodiff<NdArray<f64>>;

fn train_err_to_py(err: TrainError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

fn device() -> <BridgeBackend as burn::tensor::backend::Backend>::Device {
    Default::default()
}

/// Decode a 2-D `float64` DLPack tensor as a gradient-tracked leaf tensor,
/// also returning the plain `(dims, data)` pair used to rebuild the leaf
/// inside `backward()`.
///
/// Forward callers need both the `Tensor` (for the immediate forward pass)
/// and a plain copy of the same values (saved in the `*Ctx` for the
/// recompute-on-backward design — see the module docs). Reading the DLPack
/// capsule once and cloning the resulting `Vec<f64>` here (DV-021 S3-exec
/// remediation) avoids the previous `tensor.clone().into_data().to_vec()`
/// round-trip, which re-extracted the same values through the autodiff
/// backend's data-conversion path after the tensor had already been built.
fn tensor2_from_dlpack_with_data(
    obj: &Bound<'_, PyAny>,
) -> PyResult<(Tensor<BridgeBackend, 2>, Vec<usize>, Vec<f64>)> {
    let (shape, data) = read_dlpack_f64(obj)?;
    if shape.len() != 2 {
        return Err(PyValueError::new_err(format!(
            "expected a 2-D tensor [batch, features], got shape {shape:?}"
        )));
    }
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    let data_copy = data.clone();
    let tensor = Tensor::from_data(TensorData::new(data, dims.clone()), &device()).require_grad();
    Ok((tensor, dims, data_copy))
}

/// Decode a 2-D `float64` DLPack tensor without gradient tracking (used for
/// the incoming `grad_output` cotangent, which must not itself carry a
/// graph).
fn plain_tensor2_from_dlpack(
    obj: &Bound<'_, PyAny>,
    expected: [usize; 2],
) -> PyResult<Tensor<BridgeBackend, 2>> {
    let (shape, data) = read_dlpack_f64(obj)?;
    let dims: Vec<usize> = shape.iter().map(|&d| d as usize).collect();
    if dims.as_slice() != expected {
        return Err(PyValueError::new_err(format!(
            "grad_output shape {dims:?} does not match the forward output shape {expected:?}"
        )));
    }
    Ok(Tensor::from_data(TensorData::new(data, dims), &device()))
}

/// Export a 2-D inner-backend (non-autodiff) tensor as a new DLPack capsule.
fn export_tensor2(py: Python<'_>, tensor: Tensor<NdArray<f64>, 2>) -> PyResult<Py<PyAny>> {
    let shape: Vec<i64> = tensor.dims().iter().map(|&d| d as i64).collect();
    let data = tensor
        .into_data()
        .to_vec::<f64>()
        .map_err(|e| PyValueError::new_err(format!("failed to read tensor data: {e:?}")))?;
    export_dlpack_f64(py, shape, data)
}

// --- ResonanceLayer bridge -------------------------------------------------

/// Backward context for one [`PyResonanceLayerBridge::forward`] call.
///
/// Re-callable: see the module docs for why `backward()` recomputes the
/// forward pass from the saved layer/input rather than reusing a stored
/// graph.
#[pyclass(name = "ResonanceLayerCtx", module = "prin._prin_core", unsendable)]
pub struct PyResonanceLayerCtx {
    layer: ResonanceLayer<BridgeBackend>,
    out_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyResonanceLayerCtx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// `grad_output` is the upstream cotangent (`d(loss)/d(output)`), a
    /// `float64` CPU tensor shaped like the forward output. Returns
    /// `d(loss)/d(x)` as a new DLPack capsule. May be called more than once
    /// (with different `grad_output` values) against the same saved forward
    /// pass — see the module docs for why this recomputes the forward pass
    /// internally on every call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong dtype/device/shape,
    /// or if the gradient graph unexpectedly has no entry for `x` (would
    /// indicate an internal bridge defect, not a user error).
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor2_from_dlpack(grad_output, self.out_shape)?;

        let x = Tensor::from_data(
            TensorData::new(self.x_data.clone(), self.x_shape.clone()),
            &device(),
        )
        .require_grad();
        let output = self
            .layer
            .forward(x.clone())
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_x = x.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor2(py, grad_x)
    }
}

/// Trainable single-layer Kuramoto resonance primitive, bridged to
/// `torch.autograd.Function` via DLPack (WP-025).
///
/// Wraps [`prin_train::layers::ResonanceLayer`]; see that module's docs for
/// the exact per-step formula. Parameters (`coupling`, `decay`,
/// `input_proj`, `modulation`, `base_frequency`) live in Rust and are
/// trained by a WP-024 `OscillatorOptimizer`, not by `torch.optim` — this
/// bridge only makes `forward`/`backward` on `x` differentiable so a larger
/// PyTorch model can chain gradients through it.
#[pyclass(name = "ResonanceLayerBridge", module = "prin._prin_core", unsendable)]
pub struct PyResonanceLayerBridge {
    layer: ResonanceLayer<BridgeBackend>,
    n_dims: usize,
}

#[pymethods]
impl PyResonanceLayerBridge {
    /// Construct with seeded-random parameters (see
    /// [`ResonanceLayerConfig::init`] for the exact initialization scheme).
    #[new]
    #[pyo3(signature = (n_oscillators, n_dims, n_steps=10, dt=0.01, decay_rate=0.1, freq_adaptation_rate=0.01, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_oscillators: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let cfg = ResonanceLayerConfig::with_params(
            n_oscillators,
            n_dims,
            n_steps,
            dt,
            decay_rate,
            freq_adaptation_rate,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let layer = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { layer, n_dims })
    }

    /// Number of coupled oscillators (the output feature width).
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.layer.n_oscillators()
    }

    /// Input feature dimension.
    #[getter]
    fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Run the full `n_steps`-step forward pass for one batched boundary
    /// call. `x` is a `[batch, n_dims]` `float64` CPU DLPack-compatible
    /// tensor. Returns `(output_capsule, ctx)`, where `output` is
    /// `[batch, n_oscillators]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input,
    /// a shape other than `[batch, n_dims]`, or a `prin-train` validation
    /// failure (see [`prin_train::error::TrainError`]).
    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyResonanceLayerCtx>)> {
        let (x, x_shape, x_data) = tensor2_from_dlpack_with_data(x)?;
        if x_shape[1] != self.n_dims {
            return Err(PyValueError::new_err(format!(
                "expected x shape [batch, {}], got {:?}",
                self.n_dims, x_shape
            )));
        }
        let output = self.layer.forward(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor2(py, output.inner())?;
        let ctx = PyResonanceLayerCtx {
            layer: self.layer.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Serialize the layer's parameters to opaque, byte-exact checkpoint
    /// bytes (`burn::record::BinBytesRecorder<DoublePrecisionSettings>` —
    /// the same mechanism `layers.rs`'s
    /// `record_roundtrip_preserves_parameters` test already validates).
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<BridgeBackend>::record(&recorder, self.layer.clone().into_record(), ())
                .map_err(|e| {
                    PyValueError::new_err(format!("checkpoint serialization failed: {e}"))
                })?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`].
    ///
    /// Loads into a clone of the current layer and validates the result's
    /// parameter shapes against this layer's `n_oscillators`/`n_dims`
    /// (WP025-F1) before committing; on failure `self` is left completely
    /// unchanged (`Module::load_record` does not mutate the layer it was
    /// called on — it consumes an owned clone and returns a new value, so a
    /// rejected candidate is simply dropped).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// layer's parameter shapes.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<ResonanceLayer<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this layer is configured for \
                 n_oscillators={}, n_dims={} ({e})",
                self.layer.n_oscillators(),
                self.layer.n_dims(),
            ))
        })?;
        self.layer = candidate;
        Ok(())
    }
}

/// Deserialize checkpoint bytes into a Burn record, converting both a
/// structured `RecorderError` and an internal `burn-core` panic on malformed
/// bytes into a typed `ValueError`.
///
/// `bytes` is untrusted public-boundary input (Coding Standards §2.2):
/// `burn-core`'s `BinBytesRecorder` decoder panics (rather than returning
/// `Err`) on some malformed inputs (confirmed empirically during S1 —
/// `UnexpectedEnd` from `bincode`), so this wraps the call in
/// `catch_unwind` to guarantee a clean `PyResult` at this FFI boundary
/// instead of an uncaught panic propagating into Python.
fn load_checkpoint_record<M: Module<BridgeBackend>>(bytes: &[u8]) -> PyResult<M::Record> {
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

// --- GatedPhaseActivation bridge --------------------------------------------

/// Backward context for one [`PyGatedPhaseActivationBridge::forward`] call.
/// See [`PyResonanceLayerCtx`] for the recompute-on-backward contract.
#[pyclass(
    name = "GatedPhaseActivationCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyGatedPhaseActivationCtx {
    layer: GatedPhaseActivation<BridgeBackend>,
    out_shape: [usize; 2],
    z_shape: Vec<usize>,
    z_data: Vec<f64>,
}

#[pymethods]
impl PyGatedPhaseActivationCtx {
    /// Run the Rust backward pass for the saved forward call. See
    /// [`PyResonanceLayerCtx::backward`] for the general contract.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor2_from_dlpack(grad_output, self.out_shape)?;

        let z = Tensor::from_data(
            TensorData::new(self.z_data.clone(), self.z_shape.clone()),
            &device(),
        )
        .require_grad();
        let output = self
            .layer
            .forward(z.clone())
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_z = z.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor2(py, grad_z)
    }
}

/// Phase activation with a learnable per-feature gate, bridged to
/// `torch.autograd.Function` via DLPack (WP-025).
///
/// Wraps [`prin_train::activations::GatedPhaseActivation`]: `y = σ(w_g·z +
/// b_g) · phase_activation(z)`. Gate parameters live in Rust (see
/// [`PyResonanceLayerBridge`]'s docs for the same training-ownership split).
#[pyclass(
    name = "GatedPhaseActivationBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyGatedPhaseActivationBridge {
    layer: GatedPhaseActivation<BridgeBackend>,
}

#[pymethods]
impl PyGatedPhaseActivationBridge {
    /// Construct with zero-initialized gate weight/bias, matching PRINet
    /// 3.0's `nn.Parameter(torch.zeros(n_dims))` (deterministic; see
    /// [`GatedPhaseActivationConfig::init`]).
    #[new]
    fn new(n_dims: usize) -> PyResult<Self> {
        let cfg = GatedPhaseActivationConfig::new(n_dims).map_err(train_err_to_py)?;
        let layer = cfg.init::<BridgeBackend>(&device());
        Ok(Self { layer })
    }

    /// Input/output feature dimension.
    #[getter]
    fn n_dims(&self) -> usize {
        self.layer.n_dims()
    }

    /// Run the forward pass for one batched boundary call. `z` is a
    /// `[batch, n_dims]` `float64` CPU DLPack-compatible tensor. Returns
    /// `(output_capsule, ctx)` with the same `[batch, n_dims]` shape.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input
    /// or a shape other than `[batch, n_dims]`.
    fn forward(
        &self,
        py: Python<'_>,
        z: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyGatedPhaseActivationCtx>)> {
        let (z, z_shape, z_data) = tensor2_from_dlpack_with_data(z)?;
        if z_shape[1] != self.layer.n_dims() {
            return Err(PyValueError::new_err(format!(
                "expected z shape [batch, {}], got {:?}",
                self.layer.n_dims(),
                z_shape
            )));
        }
        let output = self.layer.forward(z).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor2(py, output.inner())?;
        let ctx = PyGatedPhaseActivationCtx {
            layer: self.layer.clone(),
            out_shape,
            z_shape,
            z_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Serialize gate parameters to checkpoint bytes. See
    /// [`PyResonanceLayerBridge::state_dict`].
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<BridgeBackend>::record(&recorder, self.layer.clone().into_record(), ())
                .map_err(|e| {
                    PyValueError::new_err(format!("checkpoint serialization failed: {e}"))
                })?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`]. See
    /// [`PyResonanceLayerBridge::load_state_dict`] for the shape-validated,
    /// rollback-safe load contract (WP025-F1).
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<GatedPhaseActivation<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this layer is configured for \
                 n_dims={} ({e})",
                self.layer.n_dims(),
            ))
        })?;
        self.layer = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyResonanceLayerBridge>()?;
    m.add_class::<PyResonanceLayerCtx>()?;
    m.add_class::<PyGatedPhaseActivationBridge>()?;
    m.add_class::<PyGatedPhaseActivationCtx>()?;
    Ok(())
}

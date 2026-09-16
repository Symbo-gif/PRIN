//! PyO3 `torch.autograd.Function` bridges for `prin-train` (WP-025).
//!
//! Every bridge in this module follows the same shape:
//!
//! - A `*Bridge` `#[pyclass]` owns a Burn `Module` built on
//!   `Autodiff<NdArray<f64>>` — the same backend `prin-train`'s own gradient
//!   tests already use (`bands.rs`/`layers.rs`/`activations.rs`
//!   `TestAutodiffBackend`). For PyTorch-trainable layers, `nn.Parameter`
//!   tensors are the canonical optimizer-visible values: each batched forward
//!   imports them into a Burn module and backward returns Burn-computed input
//!   and parameter VJPs (Coding Standards §3.2).
//! - `forward(x)` decodes `x` from a DLPack capsule (`float64` CPU,
//!   [`super::train_support::tensor_from_dlpack_with_data`]), runs the
//!   *entire* Rust forward pass in one call (`ResonanceLayer::forward`
//!   already loops `n_steps` internally in Rust — no per-step Python↔Rust
//!   crossing), and returns `(output_capsule, ctx)`.
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
//!
//! The DLPack decode/encode/checkpoint helpers this module originally
//! defined inline were generalized to arbitrary tensor rank and moved to
//! [`super::train_support`] during Exec-WP-026 S1, so the six new bridge
//! modules in this crate (`attention`, `phase_tracker`, `hybrid`,
//! `slot_attention`, `ablation`, `allocation`) could reuse them instead of
//! re-deriving this module's ~150 lines of boilerplate per module. This is a
//! behavior-preserving refactor: every function body below is unchanged
//! except for calling the shared, rank-generic helpers at `D = 2`.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use prin_dynamics::Seed;
use prin_train::activations::{GatedPhaseActivation, GatedPhaseActivationConfig};
use prin_train::layers::{ResonanceLayer, ResonanceLayerConfig, ResonanceLayerParams};

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

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
    /// `float64` CPU tensor shaped like the forward output. Returns the VJPs
    /// for `x` and all five optimizer-visible parameter tensors. May be called more than once
    /// (with different `grad_output` values) against the same saved forward
    /// pass — see the module docs for why this recomputes the forward pass
    /// internally on every call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong dtype/device/shape,
    /// or if the gradient graph unexpectedly has no entry for `x` (would
    /// indicate an internal bridge defect, not a user error).
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Vec<Py<PyAny>>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;

        let x = Tensor::from_data(
            burn::tensor::TensorData::new(self.x_data.clone(), self.x_shape.clone()),
            &device(),
        )
        .require_grad();
        let output = self
            .layer
            .forward(x.clone())
            .expect("shape already validated by the saved forward call");

        let grads = (output * grad_output).sum().backward();
        let params = self.layer.parameter_tensors();
        macro_rules! grad_or_zeros {
            ($tensor:expr) => {
                $tensor
                    .grad(&grads)
                    .unwrap_or_else(|| Tensor::zeros($tensor.dims(), &$tensor.device()))
            };
        }

        Ok(vec![
            export_tensor::<2>(
                py,
                x.grad(&grads).ok_or_else(|| {
                    PyValueError::new_err("internal error: missing ResonanceLayer input VJP")
                })?,
            )?,
            export_tensor::<2>(py, grad_or_zeros!(params.coupling))?,
            export_tensor::<1>(py, grad_or_zeros!(params.decay))?,
            export_tensor::<2>(py, grad_or_zeros!(params.input_proj).transpose())?,
            export_tensor::<2>(py, grad_or_zeros!(params.modulation))?,
            export_tensor::<1>(py, grad_or_zeros!(params.base_frequency))?,
        ])
    }
}

/// Trainable single-layer Kuramoto resonance primitive, bridged to
/// `torch.autograd.Function` via DLPack (WP-025).
///
/// Wraps [`prin_train::layers::ResonanceLayer`]; see that module's docs for
/// the exact per-step formula. The Python `nn.Parameter` tensors are canonical:
/// every forward imports their current values, Rust owns all numerical work,
/// and backward returns Burn-computed VJPs for the input and all parameters.
#[pyclass(name = "ResonanceLayerBridge", module = "prin._prin_core", unsendable)]
pub struct PyResonanceLayerBridge {
    config: ResonanceLayerConfig,
    layer: ResonanceLayer<BridgeBackend>,
}

impl PyResonanceLayerBridge {
    /// The owned Rust layer, for in-crate consumers that drive its dynamics
    /// directly (e.g. the `train_layers` HEP gradient estimator). Not exposed
    /// to Python.
    pub(crate) fn layer(&self) -> &ResonanceLayer<BridgeBackend> {
        &self.layer
    }
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
        Ok(Self { config: cfg, layer })
    }

    /// Number of coupled oscillators (the output feature width).
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.layer.n_oscillators()
    }

    /// Input feature dimension.
    #[getter]
    fn n_dims(&self) -> usize {
        self.config.n_dims
    }

    /// Return the current Rust parameter values in PyTorch-compatible layout.
    fn parameter_values(&self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        let params = self.layer.parameter_tensors();
        Ok(vec![
            export_tensor::<2>(py, params.coupling.inner())?,
            export_tensor::<1>(py, params.decay.inner())?,
            export_tensor::<2>(py, params.input_proj.transpose().inner())?,
            export_tensor::<2>(py, params.modulation.inner())?,
            export_tensor::<1>(py, params.base_frequency.inner())?,
        ])
    }

    /// Replace the Rust working copy from the five canonical PyTorch tensors.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for the wrong count, rank, dtype, device, or shape.
    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        if weights.len() != 5 {
            return Err(PyValueError::new_err(format!(
                "expected 5 weight tensors, got {}",
                weights.len()
            )));
        }
        let rank1 = |i: usize| tensor_from_dlpack_with_data::<1>(&weights[i]).map(|v| v.0);
        let rank2 = |i: usize| tensor_from_dlpack_with_data::<2>(&weights[i]).map(|v| v.0);
        let input_proj = rank2(2)?;
        self.layer = self
            .config
            .init_from_params(ResonanceLayerParams {
                coupling: rank2(0)?,
                decay: rank1(1)?,
                input_proj: Tensor::from_data(input_proj.transpose().into_data(), &device()),
                modulation: rank2(3)?,
                base_frequency: rank1(4)?,
            })
            .map_err(train_err_to_py)?;
        Ok(())
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
        &mut self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
        weights: Vec<Bound<'_, PyAny>>,
    ) -> PyResult<(Py<PyAny>, Py<PyResonanceLayerCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        if x_shape[1] != self.config.n_dims {
            return Err(PyValueError::new_err(format!(
                "expected x shape [batch, {}], got {:?}",
                self.config.n_dims, x_shape
            )));
        }
        self.load_torch_weights(weights)?;
        let output = self.layer.forward(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyResonanceLayerCtx {
            layer: self.layer.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Per-batch-row Kuramoto order parameter after the full `n_steps`
    /// integration — PRINet 3.0's `ResonanceLayer.get_order_parameter`
    /// monitoring hook. `x` is `[batch, n_dims]`; returns a `[batch]`
    /// `float64` tensor. Non-differentiable (synchronization monitoring
    /// only, matching the reference).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input,
    /// a shape other than `[batch, n_dims]`, or a `prin-train` /
    /// `prin-metrics` failure.
    fn order_parameter(
        &mut self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
        weights: Vec<Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let (x, x_shape, _x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        if x_shape[1] != self.config.n_dims {
            return Err(PyValueError::new_err(format!(
                "expected x shape [batch, {}], got {:?}",
                self.config.n_dims, x_shape
            )));
        }
        self.load_torch_weights(weights)?;
        let state = self.layer.init_state(x).map_err(train_err_to_py)?;
        let n_steps = self.layer.n_steps();
        let final_state = self
            .layer
            .integrate(state, n_steps)
            .map_err(train_err_to_py)?;
        let phase = final_state.phase().clone().inner();
        let dims = phase.dims();
        let (batch, n) = (dims[0], dims[1]);
        let data = phase
            .into_data()
            .to_vec::<f64>()
            .map_err(|e| PyValueError::new_err(format!("failed to read phase data: {e:?}")))?;
        let mut r = Vec::with_capacity(batch);
        for b in 0..batch {
            let row = &data[b * n..(b + 1) * n];
            r.push(
                prin_metrics::kuramoto_order_parameter(row)
                    .map_err(|e| PyValueError::new_err(format!("{e}")))?,
            );
        }
        crate::dlpack::export_dlpack_f64(py, vec![batch as i64], r)
    }

    /// Serialize the layer's parameters to opaque, byte-exact checkpoint
    /// bytes (`burn::record::BinBytesRecorder<DoublePrecisionSettings>` —
    /// the same mechanism `layers.rs`'s
    /// `record_roundtrip_preserves_parameters` test already validates).
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.layer)?;
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
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;

        let z = Tensor::from_data(
            burn::tensor::TensorData::new(self.z_data.clone(), self.z_shape.clone()),
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
        export_tensor::<2>(py, grad_z)
    }
}

/// Phase activation with a learnable per-feature gate, bridged to
/// `torch.autograd.Function` via DLPack (WP-025).
///
/// Wraps [`prin_train::activations::GatedPhaseActivation`]: `y = σ(w_g·z +
/// b_g) · phase_activation(z)`. Gate parameters live in Rust. Unlike
/// [`PyResonanceLayerBridge`], this bridge does not accept canonical PyTorch
/// parameter tensors and returns only the input VJP.
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
        let (z, z_shape, z_data) = tensor_from_dlpack_with_data::<2>(z)?;
        if z_shape[1] != self.layer.n_dims() {
            return Err(PyValueError::new_err(format!(
                "expected z shape [batch, {}], got {:?}",
                self.layer.n_dims(),
                z_shape
            )));
        }
        let output = self.layer.forward(z).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
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
        let bytes = record_to_bytes(&self.layer)?;
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

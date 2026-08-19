//! PyO3 `torch.autograd.Function` bridge for
//! [`prin_train::hybrid::HybridPRINetV2`] (Exec-WP-026 S1).
//!
//! Single differentiable `forward(x)` — the whole multi-layer
//! attention+dynamics+classifier pass is one Rust call, matching the
//! `train.rs` "one call per integration" batching rule. See `attention.rs`'s
//! module docs for why `dropout` must be `0.0`: `HybridPRINetV2` owns its own
//! `Dropout` field (used in its FFN blocks) in addition to composing
//! `OscillatoryAttention` (which owns another), so the same stochastic-mask
//! / recompute-on-backward hazard applies transitively.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use prin_dynamics::Seed;
use prin_train::hybrid::{HybridPRINetV2, HybridPRINetV2Config};

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

/// Backward context for one [`PyHybridPRINetV2Bridge::forward`] call. See
/// `train.rs`'s module docs for the recompute-on-backward contract.
#[pyclass(name = "HybridPRINetV2Ctx", module = "prin._prin_core", unsendable)]
pub struct PyHybridPRINetV2Ctx {
    net: HybridPRINetV2<BridgeBackend>,
    out_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyHybridPRINetV2Ctx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// # Errors
    ///
    /// See `train.rs`'s `ResonanceLayerCtx::backward`.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;

        let x = Tensor::from_data(
            burn::tensor::TensorData::new(self.x_data.clone(), self.x_shape.clone()),
            &device(),
        )
        .require_grad();
        let output = self
            .net
            .forward(x.clone())
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_x = x.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_x)
    }
}

/// PRIN's canonical hybrid oscillator + attention classification
/// architecture, bridged to `torch.autograd.Function` via DLPack.
///
/// Wraps [`prin_train::hybrid::HybridPRINetV2`]. See the module docs for why
/// `dropout` is restricted to `0.0`.
#[pyclass(name = "HybridPRINetV2Bridge", module = "prin._prin_core", unsendable)]
pub struct PyHybridPRINetV2Bridge {
    net: HybridPRINetV2<BridgeBackend>,
}

#[pymethods]
impl PyHybridPRINetV2Bridge {
    /// Construct with seeded-random parameters (see
    /// [`HybridPRINetV2Config::init`]).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for invalid hyperparameters (see
    /// [`HybridPRINetV2Config::with_params`]) or a non-zero `dropout` (see
    /// the module docs).
    #[new]
    #[pyo3(signature = (
        n_input, n_classes, d_model=64, n_heads=4, n_layers=2, n_delta=4, n_theta=8, n_gamma=32,
        n_discrete_steps=5, coupling_strength=2.0, pac_depth=0.3, dropout=0.0,
        seed_counter=0, seed_key=0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_input: usize,
        n_classes: usize,
        d_model: usize,
        n_heads: usize,
        n_layers: usize,
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_discrete_steps: usize,
        coupling_strength: f64,
        pac_depth: f64,
        dropout: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        if dropout != 0.0 {
            return Err(PyValueError::new_err(
                "HybridPRINetV2Bridge requires dropout=0.0 (see attention.rs's module docs: \
                 HybridPRINetV2 owns a Dropout field directly and composes OscillatoryAttention, \
                 which owns another; both draw from an unseeded backend RNG under autodiff)",
            ));
        }
        let cfg = HybridPRINetV2Config::with_params(
            n_input,
            n_classes,
            d_model,
            n_heads,
            n_layers,
            dropout,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            coupling_strength,
            pac_depth,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let net = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { net })
    }

    /// Input feature dimension.
    #[getter]
    fn n_input(&self) -> usize {
        self.net.n_input()
    }

    /// Number of output classes.
    #[getter]
    fn n_classes(&self) -> usize {
        self.net.n_classes()
    }

    /// Total oscillator/token count.
    #[getter]
    fn n_tokens(&self) -> usize {
        self.net.n_tokens()
    }

    /// Forward pass. `x` is `[batch, n_input]`; returns `(output_capsule,
    /// ctx)`, `output` shaped `[batch, n_classes]` (log-probabilities).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch (see
    /// [`prin_train::hybrid::HybridPRINetV2::forward`]).
    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyHybridPRINetV2Ctx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let output = self.net.forward(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyHybridPRINetV2Ctx {
            net: self.net.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Serialize parameters to checkpoint bytes.
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.net)?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`],
    /// rejecting a shape mismatch and leaving `self` unchanged on failure
    /// (WP025-F1 contract).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// network's `n_input`/`n_classes`/`n_tokens`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<HybridPRINetV2<BridgeBackend>>(bytes)?;
        let candidate = self.net.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this network is configured for n_input={}, \
                 n_classes={}, n_tokens={} ({e})",
                self.net.n_input(),
                self.net.n_classes(),
                self.net.n_tokens(),
            ))
        })?;
        self.net = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyHybridPRINetV2Bridge>()?;
    m.add_class::<PyHybridPRINetV2Ctx>()?;
    Ok(())
}

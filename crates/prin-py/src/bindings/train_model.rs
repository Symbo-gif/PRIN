//! PyO3 bridge for the WP-036A full model container (sub-pass 0144A4).
//!
//! One PRINet-3.0-compatible symbol lands here, thin marshalling over
//! [`prin_train::model::PRINetModel`] (Coding Standards §2.1 — no numerics in
//! `prin-py`):
//!
//! - [`PyPRINetModelBridge`] — [`prin_train::model::PRINetModel`]: an input
//!   `ResonanceLayer`, `n_layers - 1` stacked `ResonanceLayer`s, a `LayerNorm`
//!   after each, a concept-readout `Linear`, a logit clamp, and a final
//!   `log_softmax`.
//!
//! The differentiable bridge follows the recompute-on-backward contract
//! [`super::train`]'s module docs establish: `forward` runs the whole Rust pass
//! in one boundary crossing and returns `(output_capsule, ctx)`;
//! `ctx.backward(grad_output_capsule)` rebuilds a fresh `require_grad` leaf from
//! the saved plain values, re-runs the forward pass, and seeds the reverse pass
//! with `(output · grad_output).sum().backward()`. No new `unsafe`; all DLPack
//! FFI is delegated to the audited `dlpack` module.

use burn::module::Module;
use burn::tensor::{Tensor, TensorData};
use prin_dynamics::Seed;
use prin_train::layers::ResonanceLayerParams;
use prin_train::model::{LayerNormWeights, PRINetModel, PRINetModelConfig, PRINetModelParams};
use prin_train::LinearWeights;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

/// Rebuild a `[batch, n]` gradient-tracked leaf from saved plain values.
fn leaf_2d(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(TensorData::new(data.to_vec(), shape.to_vec()), &device()).require_grad()
}

fn no_input_grad() -> PyErr {
    PyValueError::new_err("internal error: no gradient recorded for the PRINetModel input")
}

/// Decode a rank-1 `float64` DLPack tensor as a plain (non-leaf) tensor.
fn rank1(obj: &Bound<'_, PyAny>) -> PyResult<Tensor<BridgeBackend, 1>> {
    let (tensor, _, _) = tensor_from_dlpack_with_data::<1>(obj)?;
    Ok(tensor)
}

/// Decode a rank-2 `float64` DLPack tensor as a plain (non-leaf) tensor.
fn rank2(obj: &Bound<'_, PyAny>) -> PyResult<Tensor<BridgeBackend, 2>> {
    let (tensor, _, _) = tensor_from_dlpack_with_data::<2>(obj)?;
    Ok(tensor)
}

/// Decode a rank-2 tensor and transpose it (PyTorch `[out, in]` layout to the
/// `[in, out]` a resonance projection expects), rebuilding a fresh leaf so a
/// later `require_grad` inside `init_from_params` does not touch a non-leaf.
fn rank2_transposed(obj: &Bound<'_, PyAny>) -> PyResult<Tensor<BridgeBackend, 2>> {
    let tensor = rank2(obj)?;
    Ok(Tensor::from_data(tensor.transpose().into_data(), &device()))
}

/// Decode one resonance layer's five weight tensors, starting at `weights[i]`.
///
/// Order: `coupling`, `decay`, `input_proj.weight` (PyTorch `[n_osc, n_dims]`),
/// `modulation`, `base_frequency`.
fn resonance_params(
    weights: &[Bound<'_, PyAny>],
    i: usize,
) -> PyResult<ResonanceLayerParams<BridgeBackend>> {
    Ok(ResonanceLayerParams {
        coupling: rank2(&weights[i])?,
        decay: rank1(&weights[i + 1])?,
        input_proj: rank2_transposed(&weights[i + 2])?,
        modulation: rank2(&weights[i + 3])?,
        base_frequency: rank1(&weights[i + 4])?,
    })
}

/// Backward context for one [`PyPRINetModelBridge::forward`] call.
#[pyclass(name = "PRINetModelCtx", module = "prin._prin_core", unsendable)]
pub struct PyPRINetModelCtx {
    model: PRINetModel<BridgeBackend>,
    out_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyPRINetModelCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let output = self
            .model
            .forward(x.clone())
            .expect("saved PRINetModel forward shape remains valid");
        let grads = (output * grad_output).sum().backward();
        export_tensor::<2>(py, x.grad(&grads).ok_or_else(no_input_grad)?)
    }
}

/// Full trainable PRINet model bridge.
#[pyclass(name = "PRINetModelBridge", module = "prin._prin_core", unsendable)]
pub struct PyPRINetModelBridge {
    model: PRINetModel<BridgeBackend>,
    config: PRINetModelConfig,
}

#[pymethods]
impl PyPRINetModelBridge {
    #[new]
    #[pyo3(signature = (n_resonances=64, n_dims=256, n_concepts=10, n_layers=4, n_steps=10, dt=0.01, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_resonances: usize,
        n_dims: usize,
        n_concepts: usize,
        n_layers: usize,
        n_steps: usize,
        dt: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let config =
            PRINetModelConfig::with_params(n_resonances, n_dims, n_concepts, n_layers, n_steps, dt)
                .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter.into(), seed_key.into());
        let model = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { model, config })
    }

    #[getter]
    fn n_resonances(&self) -> usize {
        self.config.n_resonances
    }

    #[getter]
    fn n_dims(&self) -> usize {
        self.config.n_dims
    }

    #[getter]
    fn n_concepts(&self) -> usize {
        self.config.n_concepts
    }

    #[getter]
    fn n_layers(&self) -> usize {
        self.config.n_layers
    }

    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPRINetModelCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let output = self.model.forward(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyPRINetModelCtx {
            model: self.model.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Replace every parameter from a flat list of `7 * n_layers + 2` DLPack
    /// tensors, in the order:
    ///
    /// - for each of the `n_layers` resonance layers (input layer first, then
    ///   the `n_layers - 1` stacked layers): `coupling`, `decay`,
    ///   `input_proj.weight` (PyTorch `[n_osc, n_dims]`), `modulation`,
    ///   `base_frequency`;
    /// - for each of the `n_layers` `LayerNorm`s: `weight` (`γ`), `bias` (`β`);
    /// - the concept-readout `Linear`: `weight` (PyTorch `[n_concepts,
    ///   n_resonances]`), `bias`.
    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        let n_layers = self.config.n_layers;
        let expected = 7 * n_layers + 2;
        if weights.len() != expected {
            return Err(PyValueError::new_err(format!(
                "expected {expected} weight tensors for n_layers={n_layers}, got {}",
                weights.len()
            )));
        }

        let mut cursor = 0usize;
        let input_layer = resonance_params(&weights, cursor)?;
        cursor += 5;
        let mut stacked = Vec::with_capacity(n_layers - 1);
        for _ in 0..n_layers - 1 {
            stacked.push(resonance_params(&weights, cursor)?);
            cursor += 5;
        }
        let mut layer_norms = Vec::with_capacity(n_layers);
        for _ in 0..n_layers {
            layer_norms.push(LayerNormWeights {
                gamma: rank1(&weights[cursor])?,
                beta: rank1(&weights[cursor + 1])?,
            });
            cursor += 2;
        }
        let concept_proj = LinearWeights {
            weight: rank2(&weights[cursor])?,
            bias: rank1(&weights[cursor + 1])?,
        };

        self.model = self
            .config
            .init_from_params(PRINetModelParams {
                input_layer,
                stacked,
                layer_norms,
                concept_proj,
            })
            .map_err(train_err_to_py)?;
        Ok(())
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        Ok(PyBytes::new(py, &record_to_bytes(&self.model)?))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PRINetModel<BridgeBackend>>(bytes)?;
        let candidate = self.model.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.model = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPRINetModelBridge>()?;
    m.add_class::<PyPRINetModelCtx>()?;
    Ok(())
}

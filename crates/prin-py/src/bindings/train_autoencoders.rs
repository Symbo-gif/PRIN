//! PyO3 bridges for the WP-036A phase-to-rate and autoencoder family
//! (sub-pass 0144A2).
//!
//! Three PRINet-3.0-compatible symbols land here, all thin marshalling over
//! [`prin_train::autoencoders`] (Coding Standards §2.1 — no numerics in
//! `prin-py`):
//!
//! - [`PyPhaseToRateConverterBridge`] —
//!   [`prin_train::autoencoders::PhaseToRateConverter`] (learnable temperature)
//! - [`PyPhaseToRateAutoencoderBridge`] —
//!   [`prin_train::autoencoders::PhaseToRateAutoencoder`]
//! - [`PyDenseAutoencoderBridge`] —
//!   [`prin_train::autoencoders::DenseAutoencoder`]
//!
//! Every differentiable bridge follows the recompute-on-backward contract
//! [`super::train`]'s module docs establish: `forward` runs the whole Rust
//! pass in one boundary crossing and returns `(*output_capsules, ctx)`;
//! `ctx.backward(*grad_output_capsules)` rebuilds fresh `require_grad` leaves
//! from the saved plain values, re-runs the forward pass, and seeds the
//! reverse pass with `(output · grad_output).sum().backward()`. No new
//! `unsafe`; all DLPack FFI is delegated to the audited `dlpack` module.
//!
//! The autoencoders' `Linear` stacks, `softplus`/`relu`/`log_softmax`, and the
//! `phase_to_rate` softmax use only `burn-tensor` elementwise/reduction ops
//! (not `B::sigmoid`/`B::tanh`), so they do **not** inherit the DV-018
//! `f32`-internal precision floor; forward-parity tolerances are set from the
//! measured deltas in `tests/test_autoencoders.py`.

use burn::module::Module;
use burn::tensor::Tensor;
use prin_dynamics::Seed;
use prin_train::autoencoders::{
    DenseAutoencoder, DenseAutoencoderConfig, DenseAutoencoderParams, LinearWeights,
    PhaseToRateAutoencoder, PhaseToRateAutoencoderConfig, PhaseToRateAutoencoderParams,
    PhaseToRateConverter, PhaseToRateConverterConfig, PhaseToRateMode,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

/// Rebuild a `[batch, n]` gradient-tracked leaf from saved plain values.
fn leaf_2d(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

fn no_input_grad() -> PyErr {
    PyValueError::new_err("internal error: no gradient recorded for an autoencoder input")
}

/// Decode one `(weight, bias)` capsule pair into [`LinearWeights`].
fn decode_linear_weights(
    weight: &Bound<'_, PyAny>,
    bias: &Bound<'_, PyAny>,
) -> PyResult<LinearWeights<BridgeBackend>> {
    let (weight, _, _) = tensor_from_dlpack_with_data::<2>(weight)?;
    let (bias, _, _) = tensor_from_dlpack_with_data::<1>(bias)?;
    Ok(LinearWeights { weight, bias })
}

// --- PhaseToRateConverter ---------------------------------------------

/// Backward context for one [`PyPhaseToRateConverterBridge::forward`] call.
#[pyclass(
    name = "PhaseToRateConverterCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseToRateConverterCtx {
    converter: PhaseToRateConverter<BridgeBackend>,
    out_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amplitude_shape: Vec<usize>,
    amplitude_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseToRateConverterCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let phase = leaf_2d(&self.phase_shape, &self.phase_data);
        let amplitude = leaf_2d(&self.amplitude_shape, &self.amplitude_data);
        let output = self
            .converter
            .forward(phase.clone(), amplitude.clone())
            .expect("saved forward shapes remain valid");
        let grads = (output * grad_output).sum().backward();
        let phase_grad = phase.grad(&grads).ok_or_else(no_input_grad)?;
        let amplitude_grad = amplitude.grad(&grads).ok_or_else(no_input_grad)?;
        Ok((
            export_tensor::<2>(py, phase_grad)?,
            export_tensor::<2>(py, amplitude_grad)?,
        ))
    }
}

/// Trainable phase-to-rate converter bridge.
#[pyclass(
    name = "PhaseToRateConverterBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseToRateConverterBridge {
    converter: PhaseToRateConverter<BridgeBackend>,
}

#[pymethods]
impl PyPhaseToRateConverterBridge {
    #[new]
    #[pyo3(signature = (n_oscillators, mode="soft", sparsity=0.1, initial_temperature=1.0))]
    fn new(
        n_oscillators: usize,
        mode: &str,
        sparsity: f64,
        initial_temperature: f64,
    ) -> PyResult<Self> {
        let mode = PhaseToRateMode::parse(mode).map_err(train_err_to_py)?;
        let converter = PhaseToRateConverterConfig::with_params(
            n_oscillators,
            mode,
            sparsity,
            initial_temperature,
        )
        .map_err(train_err_to_py)?
        .init::<BridgeBackend>(&device());
        Ok(Self { converter })
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.converter.n_oscillators()
    }

    #[getter]
    fn mode(&self) -> &'static str {
        self.converter.mode().as_str()
    }

    #[getter]
    fn sparsity(&self) -> f64 {
        self.converter.sparsity()
    }

    fn forward(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseToRateConverterCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, amplitude_shape, amplitude_data) =
            tensor_from_dlpack_with_data::<2>(amplitude)?;
        let output = self
            .converter
            .forward(phase, amplitude)
            .map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyPhaseToRateConverterCtx {
            converter: self.converter.clone(),
            out_shape,
            phase_shape,
            phase_data,
            amplitude_shape,
            amplitude_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.converter)?;
        Ok(PyBytes::new(py, &bytes))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseToRateConverter<BridgeBackend>>(bytes)?;
        let candidate = self.converter.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.converter = candidate;
        Ok(())
    }
}

// --- PhaseToRateAutoencoder ------------------------------------------

/// Backward context for [`PyPhaseToRateAutoencoderBridge::forward`].
#[pyclass(
    name = "PhaseToRateAutoencoderCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseToRateAutoencoderCtx {
    layer: PhaseToRateAutoencoder<BridgeBackend>,
    recon_shape: [usize; 2],
    rates_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseToRateAutoencoderCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_recon: &Bound<'_, PyAny>,
        grad_rates: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let grad_recon = plain_tensor_from_dlpack::<2>(grad_recon, self.recon_shape)?;
        let grad_rates = plain_tensor_from_dlpack::<2>(grad_rates, self.rates_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let (recon, rates) = self
            .layer
            .forward(x.clone())
            .expect("saved forward shapes remain valid");
        let grads = ((recon * grad_recon).sum() + (rates * grad_rates).sum()).backward();
        let grad_x = x.grad(&grads).ok_or_else(no_input_grad)?;
        export_tensor::<2>(py, grad_x)
    }
}

/// Backward context for [`PyPhaseToRateAutoencoderBridge::classify`].
#[pyclass(
    name = "PhaseToRateAutoencoderClassifyCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseToRateAutoencoderClassifyCtx {
    layer: PhaseToRateAutoencoder<BridgeBackend>,
    out_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseToRateAutoencoderClassifyCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let output = self
            .layer
            .classify(x.clone())
            .expect("saved forward shapes remain valid");
        let grads = (output * grad_output).sum().backward();
        let grad_x = x.grad(&grads).ok_or_else(no_input_grad)?;
        export_tensor::<2>(py, grad_x)
    }
}

/// Phase-to-rate autoencoder bridge.
#[pyclass(
    name = "PhaseToRateAutoencoderBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseToRateAutoencoderBridge {
    layer: PhaseToRateAutoencoder<BridgeBackend>,
    config: PhaseToRateAutoencoderConfig,
}

#[pymethods]
impl PyPhaseToRateAutoencoderBridge {
    #[new]
    #[pyo3(signature = (n_input, n_oscillators, hidden=256, n_classes=10, sparsity=0.1, mode="soft", seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_input: usize,
        n_oscillators: usize,
        hidden: usize,
        n_classes: usize,
        sparsity: f64,
        mode: &str,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let mode = PhaseToRateMode::parse(mode).map_err(train_err_to_py)?;
        let config = PhaseToRateAutoencoderConfig::with_params(
            n_input,
            n_oscillators,
            hidden,
            n_classes,
            sparsity,
            mode,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let layer = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { layer, config })
    }

    #[getter]
    fn n_input(&self) -> usize {
        self.layer.n_input()
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.layer.n_oscillators()
    }

    #[getter]
    fn n_classes(&self) -> usize {
        self.layer.n_classes()
    }

    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyPhaseToRateAutoencoderCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let (recon, rates) = self.layer.forward(x).map_err(train_err_to_py)?;
        let recon_shape = recon.dims();
        let rates_shape = rates.dims();
        let recon_capsule = export_tensor::<2>(py, recon.inner())?;
        let rates_capsule = export_tensor::<2>(py, rates.inner())?;
        let ctx = PyPhaseToRateAutoencoderCtx {
            layer: self.layer.clone(),
            recon_shape,
            rates_shape,
            x_shape,
            x_data,
        };
        Ok((recon_capsule, rates_capsule, Py::new(py, ctx)?))
    }

    fn classify(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseToRateAutoencoderClassifyCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let output = self.layer.classify(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyPhaseToRateAutoencoderClassifyCtx {
            layer: self.layer.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Replace every `Linear` weight/bias (PyTorch layout) and the bottleneck
    /// temperature from a flat list of 15 DLPack tensors, in the order
    /// `encoder_phase.{0,1}`, `encoder_amp.{0,1}`, `decoder.{0,1}` (each
    /// `weight` then `bias`), `classifier` (`weight` then `bias`), then the
    /// converter `temperature` (shape `[1]`).
    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        if weights.len() != 15 {
            return Err(PyValueError::new_err(format!(
                "expected 15 weight tensors, got {}",
                weights.len()
            )));
        }
        let lw = |i: usize| decode_linear_weights(&weights[i], &weights[i + 1]);
        let (temperature, _, _) = tensor_from_dlpack_with_data::<1>(&weights[14])?;
        let params = PhaseToRateAutoencoderParams {
            encoder_phase: [lw(0)?, lw(2)?],
            encoder_amp: [lw(4)?, lw(6)?],
            decoder: [lw(8)?, lw(10)?],
            classifier: lw(12)?,
            temperature,
        };
        self.layer = self
            .config
            .init_from_params(params)
            .map_err(train_err_to_py)?;
        Ok(())
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.layer)?;
        Ok(PyBytes::new(py, &bytes))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseToRateAutoencoder<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

// --- DenseAutoencoder ------------------------------------------------

/// Backward context for [`PyDenseAutoencoderBridge::forward`].
#[pyclass(name = "DenseAutoencoderCtx", module = "prin._prin_core", unsendable)]
pub struct PyDenseAutoencoderCtx {
    layer: DenseAutoencoder<BridgeBackend>,
    recon_shape: [usize; 2],
    codes_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyDenseAutoencoderCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_recon: &Bound<'_, PyAny>,
        grad_codes: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let grad_recon = plain_tensor_from_dlpack::<2>(grad_recon, self.recon_shape)?;
        let grad_codes = plain_tensor_from_dlpack::<2>(grad_codes, self.codes_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let (recon, codes) = self
            .layer
            .forward(x.clone())
            .expect("saved forward shapes remain valid");
        let grads = ((recon * grad_recon).sum() + (codes * grad_codes).sum()).backward();
        let grad_x = x.grad(&grads).ok_or_else(no_input_grad)?;
        export_tensor::<2>(py, grad_x)
    }
}

/// Backward context for [`PyDenseAutoencoderBridge::classify`].
#[pyclass(
    name = "DenseAutoencoderClassifyCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDenseAutoencoderClassifyCtx {
    layer: DenseAutoencoder<BridgeBackend>,
    out_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyDenseAutoencoderClassifyCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let output = self
            .layer
            .classify(x.clone())
            .expect("saved forward shapes remain valid");
        let grads = (output * grad_output).sum().backward();
        let grad_x = x.grad(&grads).ok_or_else(no_input_grad)?;
        export_tensor::<2>(py, grad_x)
    }
}

/// Dense-MLP autoencoder baseline bridge.
#[pyclass(
    name = "DenseAutoencoderBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDenseAutoencoderBridge {
    layer: DenseAutoencoder<BridgeBackend>,
    config: DenseAutoencoderConfig,
}

#[pymethods]
impl PyDenseAutoencoderBridge {
    #[new]
    #[pyo3(signature = (n_input, n_bottleneck, hidden=256, n_classes=10, seed_counter=0, seed_key=0))]
    fn new(
        n_input: usize,
        n_bottleneck: usize,
        hidden: usize,
        n_classes: usize,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let config = DenseAutoencoderConfig::with_params(n_input, n_bottleneck, hidden, n_classes)
            .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let layer = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { layer, config })
    }

    #[getter]
    fn n_input(&self) -> usize {
        self.layer.n_input()
    }

    #[getter]
    fn n_bottleneck(&self) -> usize {
        self.layer.n_bottleneck()
    }

    #[getter]
    fn n_classes(&self) -> usize {
        self.layer.n_classes()
    }

    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyDenseAutoencoderCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let (recon, codes) = self.layer.forward(x).map_err(train_err_to_py)?;
        let recon_shape = recon.dims();
        let codes_shape = codes.dims();
        let recon_capsule = export_tensor::<2>(py, recon.inner())?;
        let codes_capsule = export_tensor::<2>(py, codes.inner())?;
        let ctx = PyDenseAutoencoderCtx {
            layer: self.layer.clone(),
            recon_shape,
            codes_shape,
            x_shape,
            x_data,
        };
        Ok((recon_capsule, codes_capsule, Py::new(py, ctx)?))
    }

    fn classify(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyDenseAutoencoderClassifyCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let output = self.layer.classify(x).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyDenseAutoencoderClassifyCtx {
            layer: self.layer.clone(),
            out_shape,
            x_shape,
            x_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Replace every `Linear` weight/bias (PyTorch layout) from a flat list of
    /// 10 DLPack tensors, in the order `encoder.{0,1}`, `decoder.{0,1}`,
    /// `classifier` (each `weight` then `bias`).
    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        if weights.len() != 10 {
            return Err(PyValueError::new_err(format!(
                "expected 10 weight tensors, got {}",
                weights.len()
            )));
        }
        let lw = |i: usize| decode_linear_weights(&weights[i], &weights[i + 1]);
        let params = DenseAutoencoderParams {
            encoder: [lw(0)?, lw(2)?],
            decoder: [lw(4)?, lw(6)?],
            classifier: lw(8)?,
        };
        self.layer = self
            .config
            .init_from_params(params)
            .map_err(train_err_to_py)?;
        Ok(())
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.layer)?;
        Ok(PyBytes::new(py, &bytes))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<DenseAutoencoder<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPhaseToRateConverterBridge>()?;
    m.add_class::<PyPhaseToRateConverterCtx>()?;
    m.add_class::<PyPhaseToRateAutoencoderBridge>()?;
    m.add_class::<PyPhaseToRateAutoencoderCtx>()?;
    m.add_class::<PyPhaseToRateAutoencoderClassifyCtx>()?;
    m.add_class::<PyDenseAutoencoderBridge>()?;
    m.add_class::<PyDenseAutoencoderCtx>()?;
    m.add_class::<PyDenseAutoencoderClassifyCtx>()?;
    Ok(())
}

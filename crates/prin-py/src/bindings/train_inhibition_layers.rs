//! PyO3 bridges for the WP-036A inhibition and sparsification family.
//!
//! All numerical work delegates to `prin-train`; this module only validates
//! and marshals float64 CPU tensors through the audited DLPack boundary.

use burn::module::Module;
use burn::tensor::Tensor;
use prin_dynamics::Seed;
use prin_train::inhibition_layers::{
    DentateGyrusConverter, DentateGyrusConverterConfig, DgLayer, DgLayerConfig,
    FeedforwardInhibition, FeedforwardInhibitionConfig,
};
use prin_train::losses::{SparsityRegularizationLoss, SparsityRegularizationLossConfig};
use prin_train::weight_init::{oscillatory_weight_init, zero_bias, OscillatoryWeightKind};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

fn leaf_2d(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

fn two_input_grads(
    py: Python<'_>,
    first: Tensor<BridgeBackend, 2>,
    second: Tensor<BridgeBackend, 2>,
    output: Tensor<BridgeBackend, 2>,
    grad_output: Tensor<BridgeBackend, 2>,
) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
    let grads = (output * grad_output).sum().backward();
    let first_grad = first.grad(&grads).ok_or_else(no_input_grad)?;
    let second_grad = second.grad(&grads).ok_or_else(no_input_grad)?;
    Ok((
        export_tensor::<2>(py, first_grad)?,
        export_tensor::<2>(py, second_grad)?,
    ))
}

fn no_input_grad() -> PyErr {
    PyValueError::new_err("internal error: no gradient recorded for an inhibition-layer input")
}

#[pyclass(
    name = "FeedforwardInhibitionCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyFeedforwardInhibitionCtx {
    ffi: FeedforwardInhibition,
    out_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amplitude_shape: Vec<usize>,
    amplitude_data: Vec<f64>,
}

#[pymethods]
impl PyFeedforwardInhibitionCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let phase = leaf_2d(&self.phase_shape, &self.phase_data);
        let amplitude = leaf_2d(&self.amplitude_shape, &self.amplitude_data);
        let output = self
            .ffi
            .gate(phase.clone(), amplitude.clone())
            .expect("saved forward shapes remain valid");
        two_input_grads(py, phase, amplitude, output, grad_output)
    }
}

/// Parameter-free phase-delay / exponential-decay FFI bridge.
#[pyclass(
    name = "FeedforwardInhibitionBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyFeedforwardInhibitionBridge {
    ffi: FeedforwardInhibition,
}

#[pymethods]
impl PyFeedforwardInhibitionBridge {
    #[new]
    #[pyo3(signature = (delay_steps=1, tau=0.05, delay_fraction=0.1))]
    fn new(delay_steps: usize, tau: f64, delay_fraction: f64) -> PyResult<Self> {
        let ffi = FeedforwardInhibitionConfig::with_params(delay_steps, tau, delay_fraction)
            .map_err(train_err_to_py)?
            .init();
        Ok(Self { ffi })
    }

    #[getter]
    fn delay_steps(&self) -> usize {
        self.ffi.delay_steps()
    }

    #[getter]
    fn tau(&self) -> f64 {
        self.ffi.tau()
    }

    fn forward(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyFeedforwardInhibitionCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, amplitude_shape, amplitude_data) =
            tensor_from_dlpack_with_data::<2>(amplitude)?;
        let output = self.ffi.gate(phase, amplitude).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyFeedforwardInhibitionCtx {
            ffi: self.ffi,
            out_shape,
            phase_shape,
            phase_data,
            amplitude_shape,
            amplitude_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }
}

#[pyclass(
    name = "DentateGyrusConverterCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDentateGyrusConverterCtx {
    converter: DentateGyrusConverter,
    n_integration_steps: usize,
    out_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amplitude_shape: Vec<usize>,
    amplitude_data: Vec<f64>,
}

#[pymethods]
impl PyDentateGyrusConverterCtx {
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
            .convert(phase.clone(), amplitude.clone(), self.n_integration_steps)
            .expect("saved forward shapes remain valid");
        two_input_grads(py, phase, amplitude, output, grad_output)
    }
}

/// Dentate-gyrus FFI → EMA → FBI conversion bridge.
#[pyclass(
    name = "DentateGyrusConverterBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDentateGyrusConverterBridge {
    converter: DentateGyrusConverter,
}

#[pymethods]
impl PyDentateGyrusConverterBridge {
    #[new]
    #[pyo3(signature = (n_oscillators, k=None, target_sparsity=0.1, ffi_delay=1, ffi_tau=0.05, fbi_delay=20, fbi_temperature=1.0, integration_alpha=0.95))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_oscillators: usize,
        k: Option<usize>,
        target_sparsity: f64,
        ffi_delay: usize,
        ffi_tau: f64,
        fbi_delay: usize,
        fbi_temperature: f64,
        integration_alpha: f64,
    ) -> PyResult<Self> {
        let converter = DentateGyrusConverterConfig::with_params(
            n_oscillators,
            k,
            target_sparsity,
            ffi_delay,
            ffi_tau,
            fbi_delay,
            fbi_temperature,
            integration_alpha,
        )
        .map_err(train_err_to_py)?
        .init();
        Ok(Self { converter })
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.converter.n_oscillators()
    }

    fn forward(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        n_integration_steps: usize,
    ) -> PyResult<(Py<PyAny>, Py<PyDentateGyrusConverterCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, amplitude_shape, amplitude_data) =
            tensor_from_dlpack_with_data::<2>(amplitude)?;
        let output = self
            .converter
            .convert(phase, amplitude, n_integration_steps)
            .map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyDentateGyrusConverterCtx {
            converter: self.converter,
            n_integration_steps,
            out_shape,
            phase_shape,
            phase_data,
            amplitude_shape,
            amplitude_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }
}

#[pyclass(name = "DGLayerCtx", module = "prin._prin_core", unsendable)]
pub struct PyDgLayerCtx {
    layer: DgLayer<BridgeBackend>,
    out_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amplitude_shape: Vec<usize>,
    amplitude_data: Vec<f64>,
}

#[pymethods]
impl PyDgLayerCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let phase = leaf_2d(&self.phase_shape, &self.phase_data);
        let amplitude = leaf_2d(&self.amplitude_shape, &self.amplitude_data);
        let output = self
            .layer
            .forward(phase.clone(), amplitude.clone())
            .expect("saved forward shapes remain valid");
        two_input_grads(py, phase, amplitude, output, grad_output)
    }
}

/// Trainable dentate-gyrus layer bridge.
#[pyclass(name = "DGLayerBridge", module = "prin._prin_core", unsendable)]
pub struct PyDgLayerBridge {
    layer: DgLayer<BridgeBackend>,
}

#[pymethods]
impl PyDgLayerBridge {
    #[new]
    #[pyo3(signature = (n_input, top_k=8, ffi_delay=2, fbi_delay=20, n_integration_steps=5))]
    fn new(
        n_input: usize,
        top_k: usize,
        ffi_delay: usize,
        fbi_delay: usize,
        n_integration_steps: usize,
    ) -> PyResult<Self> {
        let layer =
            DgLayerConfig::with_params(n_input, top_k, ffi_delay, fbi_delay, n_integration_steps)
                .map_err(train_err_to_py)?
                .init::<BridgeBackend>(&device());
        Ok(Self { layer })
    }

    #[getter]
    fn n_input(&self) -> usize {
        self.layer.n_input()
    }

    #[getter]
    fn top_k(&self) -> usize {
        self.layer.top_k()
    }

    fn forward(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyDgLayerCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, amplitude_shape, amplitude_data) =
            tensor_from_dlpack_with_data::<2>(amplitude)?;
        let output = self
            .layer
            .forward(phase, amplitude)
            .map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyDgLayerCtx {
            layer: self.layer.clone(),
            out_shape,
            phase_shape,
            phase_data,
            amplitude_shape,
            amplitude_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.layer)?;
        Ok(PyBytes::new(py, &bytes))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<DgLayer<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

#[pyclass(
    name = "SparsityRegularizationLossCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySparsityRegularizationLossCtx {
    loss: SparsityRegularizationLoss,
    activations_shape: Vec<usize>,
    activations_data: Vec<f64>,
}

#[pymethods]
impl PySparsityRegularizationLossCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<1>(grad_output, [1])?;
        let activations = leaf_2d(&self.activations_shape, &self.activations_data);
        let output = self.loss.forward(activations.clone());
        let grads = (output * grad_output).sum().backward();
        let grad = activations.grad(&grads).ok_or_else(no_input_grad)?;
        export_tensor::<2>(py, grad)
    }
}

/// Sigmoid-surrogate L0 density-penalty bridge.
#[pyclass(
    name = "SparsityRegularizationLossBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySparsityRegularizationLossBridge {
    loss: SparsityRegularizationLoss,
}

#[pymethods]
impl PySparsityRegularizationLossBridge {
    #[new]
    #[pyo3(signature = (target_sparsity=0.9, temperature=0.1))]
    fn new(target_sparsity: f64, temperature: f64) -> PyResult<Self> {
        let loss = SparsityRegularizationLossConfig::with_params(target_sparsity, temperature)
            .map_err(train_err_to_py)?
            .init();
        Ok(Self { loss })
    }

    #[getter]
    fn target_sparsity(&self) -> f64 {
        self.loss.target_sparsity()
    }

    #[getter]
    fn temperature(&self) -> f64 {
        self.loss.temperature()
    }

    fn forward(
        &self,
        py: Python<'_>,
        activations: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PySparsityRegularizationLossCtx>)> {
        let (activations, activations_shape, activations_data) =
            tensor_from_dlpack_with_data::<2>(activations)?;
        let output = self.loss.forward(activations);
        let capsule = export_tensor::<1>(py, output.inner())?;
        let ctx = PySparsityRegularizationLossCtx {
            loss: self.loss,
            activations_shape,
            activations_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }
}

/// Thin bridge for oscillator-aware parameter initialization.
#[pyclass(
    name = "OscillatoryWeightInitBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyOscillatoryWeightInitBridge;

#[pymethods]
impl PyOscillatoryWeightInitBridge {
    #[new]
    fn new() -> Self {
        Self
    }

    #[allow(clippy::too_many_arguments)]
    fn matrix(
        &self,
        py: Python<'_>,
        parameter: &Bound<'_, PyAny>,
        coupling: bool,
        coupling_scale: f64,
        proj_gain: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Py<PyAny>> {
        let (parameter, _, _) = tensor_from_dlpack_with_data::<2>(parameter)?;
        let kind = if coupling {
            OscillatoryWeightKind::Coupling
        } else {
            OscillatoryWeightKind::Projection
        };
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let output = oscillatory_weight_init(parameter, kind, coupling_scale, proj_gain, &mut seed)
            .map_err(train_err_to_py)?;
        export_tensor::<2>(py, output.inner())
    }

    fn bias(&self, py: Python<'_>, parameter: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let (parameter, _, _) = tensor_from_dlpack_with_data::<1>(parameter)?;
        export_tensor::<1>(py, zero_bias(parameter).inner())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyFeedforwardInhibitionBridge>()?;
    m.add_class::<PyFeedforwardInhibitionCtx>()?;
    m.add_class::<PyDentateGyrusConverterBridge>()?;
    m.add_class::<PyDentateGyrusConverterCtx>()?;
    m.add_class::<PyDgLayerBridge>()?;
    m.add_class::<PyDgLayerCtx>()?;
    m.add_class::<PySparsityRegularizationLossBridge>()?;
    m.add_class::<PySparsityRegularizationLossCtx>()?;
    m.add_class::<PyOscillatoryWeightInitBridge>()?;
    Ok(())
}

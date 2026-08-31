//! Thin DLPack bridges for hierarchical, PAC, and discrete trainable layers.
//!
//! All numerical work delegates to [`prin_train::hierarchical_layers`]. Each
//! backward context saves plain input values, rebuilds fresh autodiff leaves,
//! recomputes the complete Rust forward pass, and applies a cotangent VJP.

use burn::module::Module;
use burn::tensor::{Tensor, TensorData};
use prin_dynamics::Seed;
use prin_train::bands::DiscreteDeltaThetaGammaParams;
use prin_train::hierarchical_layers::{
    DiscreteDeltaThetaGammaLayer, DiscreteDeltaThetaGammaLayerConfig,
    DiscreteDeltaThetaGammaLayerParams, HierarchicalResonanceLayer,
    HierarchicalResonanceLayerConfig, HierarchicalResonanceLayerParams,
    PhaseAmplitudeCouplingLayer, PhaseAmplitudeCouplingLayerConfig, ProjectionWeights,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

fn leaf_2d(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(TensorData::new(data.to_vec(), shape.to_vec()), &device()).require_grad()
}

fn no_input_grad(name: &'static str) -> PyErr {
    PyValueError::new_err(format!(
        "internal error: no gradient recorded for hierarchical-layer input `{name}`"
    ))
}

fn projection(obj: &Bound<'_, PyAny>) -> PyResult<ProjectionWeights<BridgeBackend>> {
    let (weight, _, _) = tensor_from_dlpack_with_data::<2>(obj)?;
    Ok(ProjectionWeights { weight })
}

/// Backward context for [`PyHierarchicalResonanceLayerBridge`].
#[pyclass(
    name = "HierarchicalResonanceLayerCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyHierarchicalResonanceLayerCtx {
    layer: HierarchicalResonanceLayer<BridgeBackend>,
    output_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyHierarchicalResonanceLayerCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_amplitude: &Bound<'_, PyAny>,
        grad_phase: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let grad_amplitude = plain_tensor_from_dlpack::<2>(grad_amplitude, self.output_shape)?;
        let grad_phase = plain_tensor_from_dlpack::<2>(grad_phase, self.output_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let (amplitude, phase) = self
            .layer
            .forward(x.clone())
            .expect("saved hierarchical forward shape remains valid");
        let grads = ((amplitude * grad_amplitude).sum() + (phase * grad_phase).sum()).backward();
        export_tensor::<2>(py, x.grad(&grads).ok_or_else(|| no_input_grad("x"))?)
    }
}

/// Rust-owned continuous three-band hierarchical layer bridge.
#[pyclass(
    name = "HierarchicalResonanceLayerBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyHierarchicalResonanceLayerBridge {
    config: HierarchicalResonanceLayerConfig,
    layer: HierarchicalResonanceLayer<BridgeBackend>,
}

#[pymethods]
impl PyHierarchicalResonanceLayerBridge {
    #[new]
    #[pyo3(signature = (n_delta=8, n_theta=16, n_gamma=64, n_dims=256, n_steps=10, dt=0.01, coupling_strength=2.0, pac_depth=0.3, sparse_k=None, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        coupling_strength: f64,
        pac_depth: f64,
        sparse_k: Option<usize>,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let config = HierarchicalResonanceLayerConfig::with_params(
            n_delta,
            n_theta,
            n_gamma,
            n_dims,
            n_steps,
            dt,
            coupling_strength,
            pac_depth,
            sparse_k,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter.into(), seed_key.into());
        let layer = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { config, layer })
    }

    #[getter]
    fn n_delta(&self) -> usize {
        self.config.n_delta
    }

    #[getter]
    fn n_theta(&self) -> usize {
        self.config.n_theta
    }

    #[getter]
    fn n_gamma(&self) -> usize {
        self.config.n_gamma
    }

    #[getter]
    fn n_total(&self) -> usize {
        self.config.n_total()
    }

    #[getter]
    fn n_dims(&self) -> usize {
        self.config.n_dims
    }

    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyHierarchicalResonanceLayerCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let (amplitude, phase) = self.layer.forward(x).map_err(train_err_to_py)?;
        let output_shape = amplitude.dims();
        let amplitude_capsule = export_tensor::<2>(py, amplitude.inner())?;
        let phase_capsule = export_tensor::<2>(py, phase.inner())?;
        let ctx = PyHierarchicalResonanceLayerCtx {
            layer: self.layer.clone(),
            output_shape,
            x_shape,
            x_data,
        };
        Ok((amplitude_capsule, phase_capsule, Py::new(py, ctx)?))
    }

    fn load_torch_weights(
        &mut self,
        proj_delta: &Bound<'_, PyAny>,
        proj_theta: &Bound<'_, PyAny>,
        proj_gamma: &Bound<'_, PyAny>,
        pac_depth_dt: &Bound<'_, PyAny>,
        pac_depth_tg: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let (pac_depth_dt, _, _) = tensor_from_dlpack_with_data::<1>(pac_depth_dt)?;
        let (pac_depth_tg, _, _) = tensor_from_dlpack_with_data::<1>(pac_depth_tg)?;
        self.layer = self
            .config
            .init_from_params(HierarchicalResonanceLayerParams {
                proj_delta: projection(proj_delta)?,
                proj_theta: projection(proj_theta)?,
                proj_gamma: projection(proj_gamma)?,
                pac_depth_dt,
                pac_depth_tg,
            })
            .map_err(train_err_to_py)?;
        Ok(())
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        Ok(PyBytes::new(py, &record_to_bytes(&self.layer)?))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<HierarchicalResonanceLayer<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

/// Backward context for [`PyPhaseAmplitudeCouplingLayerBridge`].
#[pyclass(
    name = "PhaseAmplitudeCouplingLayerCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseAmplitudeCouplingLayerCtx {
    layer: PhaseAmplitudeCouplingLayer<BridgeBackend>,
    output_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amplitude_shape: Vec<usize>,
    amplitude_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseAmplitudeCouplingLayerCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.output_shape)?;
        let phase = leaf_2d(&self.phase_shape, &self.phase_data);
        let amplitude = leaf_2d(&self.amplitude_shape, &self.amplitude_data);
        let output = self
            .layer
            .forward(phase.clone(), amplitude.clone())
            .expect("saved PAC forward shapes remain valid");
        let grads = (output * grad_output).sum().backward();
        Ok((
            export_tensor::<2>(
                py,
                phase
                    .grad(&grads)
                    .ok_or_else(|| no_input_grad("slow_phase"))?,
            )?,
            export_tensor::<2>(
                py,
                amplitude
                    .grad(&grads)
                    .ok_or_else(|| no_input_grad("fast_amplitude"))?,
            )?,
        ))
    }
}

/// Rust-owned learnable PAC bridge.
#[pyclass(
    name = "PhaseAmplitudeCouplingLayerBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseAmplitudeCouplingLayerBridge {
    layer: PhaseAmplitudeCouplingLayer<BridgeBackend>,
}

#[pymethods]
impl PyPhaseAmplitudeCouplingLayerBridge {
    #[new]
    #[pyo3(signature = (initial_depth=0.3))]
    fn new(initial_depth: f64) -> PyResult<Self> {
        let layer = PhaseAmplitudeCouplingLayerConfig::with_depth(initial_depth)
            .map_err(train_err_to_py)?
            .init::<BridgeBackend>(&device());
        Ok(Self { layer })
    }

    fn forward(
        &self,
        py: Python<'_>,
        slow_phase: &Bound<'_, PyAny>,
        fast_amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseAmplitudeCouplingLayerCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(slow_phase)?;
        let (amplitude, amplitude_shape, amplitude_data) =
            tensor_from_dlpack_with_data::<2>(fast_amplitude)?;
        let output = self
            .layer
            .forward(phase, amplitude)
            .map_err(train_err_to_py)?;
        let output_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyPhaseAmplitudeCouplingLayerCtx {
            layer: self.layer.clone(),
            output_shape,
            phase_shape,
            phase_data,
            amplitude_shape,
            amplitude_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        Ok(PyBytes::new(py, &record_to_bytes(&self.layer)?))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseAmplitudeCouplingLayer<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

/// Backward context for [`PyDiscreteDeltaThetaGammaLayerBridge`].
#[pyclass(
    name = "DiscreteDeltaThetaGammaLayerCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDiscreteDeltaThetaGammaLayerCtx {
    layer: DiscreteDeltaThetaGammaLayer<BridgeBackend>,
    output_shape: [usize; 2],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
}

#[pymethods]
impl PyDiscreteDeltaThetaGammaLayerCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.output_shape)?;
        let x = leaf_2d(&self.x_shape, &self.x_data);
        let output = self
            .layer
            .forward(x.clone())
            .expect("saved discrete-layer input shape remains valid");
        let grads = (output * grad_output).sum().backward();
        export_tensor::<2>(py, x.grad(&grads).ok_or_else(|| no_input_grad("x"))?)
    }
}

/// Rust-owned discrete three-band layer bridge.
#[pyclass(
    name = "DiscreteDeltaThetaGammaLayerBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDiscreteDeltaThetaGammaLayerBridge {
    config: DiscreteDeltaThetaGammaLayerConfig,
    layer: DiscreteDeltaThetaGammaLayer<BridgeBackend>,
}

#[pymethods]
impl PyDiscreteDeltaThetaGammaLayerBridge {
    #[new]
    #[pyo3(signature = (n_delta=8, n_theta=16, n_gamma=64, n_dims=256, n_steps=10, dt=0.01, coupling_strength=2.0, pac_depth=0.3, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        coupling_strength: f64,
        pac_depth: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let config = DiscreteDeltaThetaGammaLayerConfig::with_params(
            n_delta,
            n_theta,
            n_gamma,
            n_dims,
            n_steps,
            dt,
            coupling_strength,
            pac_depth,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter.into(), seed_key.into());
        let layer = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { config, layer })
    }

    #[getter]
    fn n_total(&self) -> usize {
        self.config.n_total()
    }

    #[getter]
    fn n_dims(&self) -> usize {
        self.config.n_dims
    }

    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyDiscreteDeltaThetaGammaLayerCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<2>(x)?;
        let output = self.layer.forward(x).map_err(train_err_to_py)?;
        let output_shape = output.dims();
        let capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyDiscreteDeltaThetaGammaLayerCtx {
            layer: self.layer.clone(),
            output_shape,
            x_shape,
            x_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        if weights.len() != 15 {
            return Err(PyValueError::new_err(format!(
                "expected 15 weight tensors, got {}",
                weights.len()
            )));
        }
        let rank1 = |i: usize| tensor_from_dlpack_with_data::<1>(&weights[i]).map(|v| v.0);
        let rank2 = |i: usize| tensor_from_dlpack_with_data::<2>(&weights[i]).map(|v| v.0);
        let rank2_transposed = |i: usize| {
            rank2(i).map(|tensor| Tensor::from_data(tensor.transpose().into_data(), &device()))
        };
        let dynamics = DiscreteDeltaThetaGammaParams {
            delta_freq: rank1(2)?,
            theta_freq: rank1(3)?,
            gamma_freq: rank1(4)?,
            w_delta: rank2(5)?,
            w_theta: rank2(6)?,
            w_gamma: rank2(7)?,
            w_pac_dt: rank2_transposed(8)?,
            b_pac_dt: rank1(9)?,
            w_pac_tg: rank2_transposed(10)?,
            b_pac_tg: rank1(11)?,
            mu_delta: rank2(12)?,
            mu_theta: rank2(13)?,
            mu_gamma: rank2(14)?,
        };
        self.layer = self
            .config
            .init_from_params(DiscreteDeltaThetaGammaLayerParams {
                proj_phase: projection(&weights[0])?,
                proj_amplitude: projection(&weights[1])?,
                dynamics,
            })
            .map_err(train_err_to_py)?;
        Ok(())
    }

    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        Ok(PyBytes::new(py, &record_to_bytes(&self.layer)?))
    }

    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<DiscreteDeltaThetaGammaLayer<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(train_err_to_py)?;
        self.layer = candidate;
        Ok(())
    }
}

/// Rust-owned standalone discrete three-band *network* bridge (no in/out
/// projections — that is [`PyDiscreteDeltaThetaGammaLayerBridge`]).
///
/// Mirrors PRINet 3.0 `core.propagation.networks.DiscreteDeltaThetaGamma`.
/// The canonical trainable parameters live on the Python `nn.Module` (13
/// tensors: per-band frequencies, intra-band coupling, PAC gate weights /
/// biases, and per-band `μ`); each `step` / `integrate` call pushes the
/// current values through [`Self::load_torch_weights`] and then runs the
/// Rust forward. `step` / `integrate` are non-differentiable end to end
/// (the Python wrapper populates parameter `.grad` with a value-preserving
/// mirror term, matching the WP-036B E4 layer-mirror pattern);
/// `order_parameters` / `pac_index` are pure diagnostics.
#[pyclass(
    name = "DiscreteDeltaThetaGammaBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDiscreteDeltaThetaGammaBridge {
    config: prin_train::bands::DiscreteDeltaThetaGammaConfig,
    net: prin_train::bands::DiscreteDeltaThetaGamma<BridgeBackend>,
}

#[pymethods]
impl PyDiscreteDeltaThetaGammaBridge {
    #[new]
    #[pyo3(signature = (n_delta=8, n_theta=16, n_gamma=64, coupling_strength=2.0, pac_depth=0.3, delta_freq=2.0, theta_freq=6.0, gamma_freq=40.0, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        coupling_strength: f64,
        pac_depth: f64,
        delta_freq: f64,
        theta_freq: f64,
        gamma_freq: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let config = prin_train::bands::DiscreteDeltaThetaGammaConfig::with_params(
            n_delta,
            n_theta,
            n_gamma,
            coupling_strength,
            pac_depth,
            delta_freq,
            theta_freq,
            gamma_freq,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter.into(), seed_key.into());
        let net = config.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { config, net })
    }

    #[getter]
    fn n_delta(&self) -> usize {
        self.config.n_delta
    }

    #[getter]
    fn n_theta(&self) -> usize {
        self.config.n_theta
    }

    #[getter]
    fn n_gamma(&self) -> usize {
        self.config.n_gamma
    }

    #[getter]
    fn n_total(&self) -> usize {
        self.config.n_total()
    }

    /// Replace the network parameters from the Python `nn.Module` mirrors.
    ///
    /// Order: `delta_freq, theta_freq, gamma_freq` (rank 1); `w_delta,
    /// w_theta, w_gamma` (rank 2); `w_pac_dt` (rank 2, `[n_theta, 2*n_delta]`
    /// — transposed here to the Rust `[2*n_delta, n_theta]` layout), `b_pac_dt`
    /// (rank 1); `w_pac_tg` (rank 2, transposed), `b_pac_tg` (rank 1);
    /// `mu_delta, mu_theta, mu_gamma` (rank 2, `[1, 1]`).
    fn load_torch_weights(&mut self, weights: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        if weights.len() != 13 {
            return Err(PyValueError::new_err(format!(
                "expected 13 weight tensors, got {}",
                weights.len()
            )));
        }
        let rank1 = |i: usize| tensor_from_dlpack_with_data::<1>(&weights[i]).map(|v| v.0);
        let rank2 = |i: usize| tensor_from_dlpack_with_data::<2>(&weights[i]).map(|v| v.0);
        let rank2_transposed = |i: usize| {
            rank2(i).map(|tensor| Tensor::from_data(tensor.transpose().into_data(), &device()))
        };
        let params = DiscreteDeltaThetaGammaParams {
            delta_freq: rank1(0)?,
            theta_freq: rank1(1)?,
            gamma_freq: rank1(2)?,
            w_delta: rank2(3)?,
            w_theta: rank2(4)?,
            w_gamma: rank2(5)?,
            w_pac_dt: rank2_transposed(6)?,
            b_pac_dt: rank1(7)?,
            w_pac_tg: rank2_transposed(8)?,
            b_pac_tg: rank1(9)?,
            mu_delta: rank2(10)?,
            mu_theta: rank2(11)?,
            mu_gamma: rank2(12)?,
        };
        self.net = self
            .config
            .init_from_params(params)
            .map_err(train_err_to_py)?;
        Ok(())
    }

    /// Advance one macro step. Returns `(new_phase, new_amplitude)` capsules.
    fn step(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        dt: f64,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let (phase, _, _) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, _, _) = tensor_from_dlpack_with_data::<2>(amplitude)?;
        let state =
            prin_train::bands::DiscreteBandState::new(phase, amplitude).map_err(train_err_to_py)?;
        let next = self.net.step(state, dt).map_err(train_err_to_py)?;
        let (p, a) = next.into_parts();
        Ok((
            export_tensor::<2>(py, p.inner())?,
            export_tensor::<2>(py, a.inner())?,
        ))
    }

    /// Advance `n_steps` macro steps. Returns `(final_phase, final_amplitude)`.
    fn integrate(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        n_steps: usize,
        dt: f64,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let (phase, _, _) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, _, _) = tensor_from_dlpack_with_data::<2>(amplitude)?;
        let state =
            prin_train::bands::DiscreteBandState::new(phase, amplitude).map_err(train_err_to_py)?;
        let next = self
            .net
            .integrate(state, n_steps, dt)
            .map_err(train_err_to_py)?;
        let (p, a) = next.into_parts();
        Ok((
            export_tensor::<2>(py, p.inner())?,
            export_tensor::<2>(py, a.inner())?,
        ))
    }

    /// Per-band Kuramoto order parameters `(r_delta, r_theta, r_gamma)`.
    fn order_parameters(&self, phase: &Bound<'_, PyAny>) -> PyResult<(f64, f64, f64)> {
        let (phase, _, _) = tensor_from_dlpack_with_data::<2>(phase)?;
        self.net.order_parameters(phase).map_err(train_err_to_py)
    }

    /// PAC modulation indices `(pac_dt, pac_tg)`.
    fn pac_index(
        &self,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(f64, f64)> {
        let (phase, _, _) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amplitude, _, _) = tensor_from_dlpack_with_data::<2>(amplitude)?;
        self.net
            .pac_index(phase, amplitude)
            .map_err(train_err_to_py)
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyHierarchicalResonanceLayerBridge>()?;
    m.add_class::<PyHierarchicalResonanceLayerCtx>()?;
    m.add_class::<PyPhaseAmplitudeCouplingLayerBridge>()?;
    m.add_class::<PyPhaseAmplitudeCouplingLayerCtx>()?;
    m.add_class::<PyDiscreteDeltaThetaGammaLayerBridge>()?;
    m.add_class::<PyDiscreteDeltaThetaGammaLayerCtx>()?;
    m.add_class::<PyDiscreteDeltaThetaGammaBridge>()?;
    Ok(())
}

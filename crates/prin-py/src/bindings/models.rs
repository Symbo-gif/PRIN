//! PyO3 bindings for `prin_dynamics::models` (Dynamics trait implementors).

use pyo3::prelude::*;

use prin_dynamics::models::{Dynamics, HopfOscillator, KuramotoOscillator, StuartLandauOscillator};

use super::coupling::PyCouplingMode;
use super::state::{state_err_to_py, PyOscillatorState, PyStateDerivatives};

/// Kuramoto coupled oscillator model.
#[pyclass(
    name = "KuramotoOscillator",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyKuramotoOscillator {
    pub(crate) inner: KuramotoOscillator,
}

#[pymethods]
impl PyKuramotoOscillator {
    #[new]
    fn py_new(
        n_oscillators: usize,
        coupling_strength: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        coupling_mode: &PyCouplingMode,
    ) -> PyResult<Self> {
        let inner = KuramotoOscillator::new(
            n_oscillators,
            coupling_strength,
            decay_rate,
            freq_adaptation_rate,
            coupling_mode.inner.clone(),
        )
        .map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }
    #[getter]
    fn coupling_strength(&self) -> f64 {
        self.inner.coupling_strength()
    }
    #[getter]
    fn decay_rate(&self) -> f64 {
        self.inner.decay_rate()
    }
    #[getter]
    fn freq_adaptation_rate(&self) -> f64 {
        self.inner.freq_adaptation_rate()
    }

    fn compute_derivatives(&self, state: &PyOscillatorState) -> PyResult<PyStateDerivatives> {
        let deriv = self
            .inner
            .compute_derivatives(&state.inner)
            .map_err(state_err_to_py)?;
        Ok(PyStateDerivatives { inner: deriv })
    }

    fn __repr__(&self) -> String {
        format!(
            "KuramotoOscillator(n={}, K={}, λ={}, γ={})",
            self.inner.n_oscillators(),
            self.inner.coupling_strength(),
            self.inner.decay_rate(),
            self.inner.freq_adaptation_rate(),
        )
    }
}

/// Stuart–Landau coupled oscillator model (Hopf normal form).
#[pyclass(
    name = "StuartLandauOscillator",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyStuartLandauOscillator {
    pub(crate) inner: StuartLandauOscillator,
}

#[pymethods]
impl PyStuartLandauOscillator {
    #[new]
    fn py_new(
        n_oscillators: usize,
        coupling_strength: f64,
        bifurcation_param: f64,
        coupling_mode: &PyCouplingMode,
    ) -> PyResult<Self> {
        let inner = StuartLandauOscillator::new(
            n_oscillators,
            coupling_strength,
            bifurcation_param,
            coupling_mode.inner.clone(),
        )
        .map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }
    #[getter]
    fn coupling_strength(&self) -> f64 {
        self.inner.coupling_strength()
    }
    #[getter]
    fn bifurcation_param(&self) -> f64 {
        self.inner.bifurcation_param()
    }

    fn compute_derivatives(&self, state: &PyOscillatorState) -> PyResult<PyStateDerivatives> {
        let deriv = self
            .inner
            .compute_derivatives(&state.inner)
            .map_err(state_err_to_py)?;
        Ok(PyStateDerivatives { inner: deriv })
    }

    fn __repr__(&self) -> String {
        format!(
            "StuartLandauOscillator(n={}, K={}, μ={})",
            self.inner.n_oscillators(),
            self.inner.coupling_strength(),
            self.inner.bifurcation_param(),
        )
    }
}

/// Hopf bifurcation oscillator with polar amplitude-phase dynamics.
#[pyclass(
    name = "HopfOscillator",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyHopfOscillator {
    pub(crate) inner: HopfOscillator,
}

#[pymethods]
impl PyHopfOscillator {
    #[new]
    fn py_new(
        n_oscillators: usize,
        coupling_strength: f64,
        bifurcation_param: f64,
        freq_adaptation_rate: f64,
        coupling_mode: &PyCouplingMode,
    ) -> PyResult<Self> {
        let inner = HopfOscillator::new(
            n_oscillators,
            coupling_strength,
            bifurcation_param,
            freq_adaptation_rate,
            coupling_mode.inner.clone(),
        )
        .map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }
    #[getter]
    fn coupling_strength(&self) -> f64 {
        self.inner.coupling_strength()
    }
    #[getter]
    fn bifurcation_param(&self) -> f64 {
        self.inner.bifurcation_param()
    }
    #[getter]
    fn freq_adaptation_rate(&self) -> f64 {
        self.inner.freq_adaptation_rate()
    }

    fn compute_derivatives(&self, state: &PyOscillatorState) -> PyResult<PyStateDerivatives> {
        let deriv = self
            .inner
            .compute_derivatives(&state.inner)
            .map_err(state_err_to_py)?;
        Ok(PyStateDerivatives { inner: deriv })
    }

    fn __repr__(&self) -> String {
        format!(
            "HopfOscillator(n={}, K={}, μ={}, γ={})",
            self.inner.n_oscillators(),
            self.inner.coupling_strength(),
            self.inner.bifurcation_param(),
            self.inner.freq_adaptation_rate(),
        )
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyKuramotoOscillator>()?;
    m.add_class::<PyStuartLandauOscillator>()?;
    m.add_class::<PyHopfOscillator>()?;
    Ok(())
}

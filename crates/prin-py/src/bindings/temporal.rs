//! PyO3 bindings for `prin_dynamics::temporal`.

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::temporal::{
    ComplexPhasorBlender, EmaAmplitudeBlender, TemporalError, TemporalPropagator,
};

fn temporal_err_to_py(err: TemporalError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Complex-phasor phase blender.
///
/// Blends two phase arrays by converting to unit phasors, taking a weighted
/// complex average, and extracting the resultant phase via `atan2`.
///
/// `alpha` weights the **new** frame. PRINet 3.0's
/// `TemporalPhasePropagator.carry_strength` weights the **carried** frame, so
/// `alpha = 1 - carry_strength`.
#[pyclass(
    name = "ComplexPhasorBlender",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyComplexPhasorBlender {
    inner: ComplexPhasorBlender,
}

#[pymethods]
impl PyComplexPhasorBlender {
    #[new]
    fn py_new(alpha: f64) -> PyResult<Self> {
        Ok(Self {
            inner: ComplexPhasorBlender::new(alpha).map_err(temporal_err_to_py)?,
        })
    }

    #[getter]
    fn alpha(&self) -> f64 {
        self.inner.alpha()
    }

    fn set_alpha(&mut self, value: f64) -> PyResult<()> {
        self.inner.set_alpha(value).map_err(temporal_err_to_py)
    }

    fn blend<'py>(
        &self,
        py: Python<'py>,
        new_phases: PyReadonlyArray1<f64>,
        old_phases: PyReadonlyArray1<f64>,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let np = new_phases
            .as_slice()
            .map_err(|_| PyValueError::new_err("new_phases must be contiguous"))?;
        let op = old_phases
            .as_slice()
            .map_err(|_| PyValueError::new_err("old_phases must be contiguous"))?;
        let result = self.inner.blend(np, op).map_err(temporal_err_to_py)?;
        Ok(PyArray1::from_vec(py, result))
    }

    fn blend_scalar(&self, new_phase: f64, old_phase: f64) -> PyResult<f64> {
        self.inner
            .blend_scalar(new_phase, old_phase)
            .map_err(temporal_err_to_py)
    }

    fn __repr__(&self) -> String {
        format!("ComplexPhasorBlender(alpha={})", self.inner.alpha())
    }
}

/// Exponential moving average (EMA) amplitude blender.
///
/// `A_blend = α·A_new + (1-α)·A_old`, clamped to `[1e-6, 10]`.
///
/// `alpha` weights the **new** frame. PRINet 3.0's
/// `TemporalPhasePropagator.amplitude_decay` weights the **carried** frame, so
/// `alpha = 1 - amplitude_decay`.
#[pyclass(
    name = "EmaAmplitudeBlender",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyEmaAmplitudeBlender {
    inner: EmaAmplitudeBlender,
}

#[pymethods]
impl PyEmaAmplitudeBlender {
    #[new]
    fn py_new(alpha: f64) -> PyResult<Self> {
        Ok(Self {
            inner: EmaAmplitudeBlender::new(alpha).map_err(temporal_err_to_py)?,
        })
    }

    #[getter]
    fn alpha(&self) -> f64 {
        self.inner.alpha()
    }

    fn set_alpha(&mut self, value: f64) -> PyResult<()> {
        self.inner.set_alpha(value).map_err(temporal_err_to_py)
    }

    #[getter]
    fn amp_min(&self) -> f64 {
        self.inner.amp_min()
    }

    #[getter]
    fn amp_max(&self) -> f64 {
        self.inner.amp_max()
    }

    fn blend<'py>(
        &self,
        py: Python<'py>,
        new_amplitudes: PyReadonlyArray1<f64>,
        old_amplitudes: PyReadonlyArray1<f64>,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let na = new_amplitudes
            .as_slice()
            .map_err(|_| PyValueError::new_err("new_amplitudes must be contiguous"))?;
        let oa = old_amplitudes
            .as_slice()
            .map_err(|_| PyValueError::new_err("old_amplitudes must be contiguous"))?;
        let result = self.inner.blend(na, oa).map_err(temporal_err_to_py)?;
        Ok(PyArray1::from_vec(py, result))
    }

    fn __repr__(&self) -> String {
        format!("EmaAmplitudeBlender(alpha={})", self.inner.alpha())
    }
}

/// Temporal propagator: combines complex-phasor phase blending with EMA
/// amplitude blending, maintaining a running state across frames.
///
/// The running state corresponds to PRINet 3.0's `prev_phase`/`prev_amplitude`
/// and the `propagate` argument to its `input_phase`/`input_amplitude`, with
/// `alpha = 1 - carry_strength` (phase) and `alpha = 1 - amplitude_decay`
/// (amplitude).
#[pyclass(
    name = "TemporalPropagator",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyTemporalPropagator {
    inner: TemporalPropagator,
}

#[pymethods]
impl PyTemporalPropagator {
    #[new]
    fn py_new(alpha: f64) -> PyResult<Self> {
        Ok(Self {
            inner: TemporalPropagator::new(alpha).map_err(temporal_err_to_py)?,
        })
    }

    /// Create with separate blending factors for phase and amplitude.
    #[staticmethod]
    fn with_separate_alpha(phase_alpha: f64, amplitude_alpha: f64) -> PyResult<Self> {
        Ok(Self {
            inner: TemporalPropagator::with_separate_alpha(phase_alpha, amplitude_alpha)
                .map_err(temporal_err_to_py)?,
        })
    }

    #[getter]
    fn phase_alpha(&self) -> f64 {
        self.inner.phase_alpha()
    }

    #[getter]
    fn amplitude_alpha(&self) -> f64 {
        self.inner.amplitude_alpha()
    }

    fn is_initialized(&self) -> bool {
        self.inner.is_initialized()
    }

    fn propagate_init(
        &mut self,
        phases: PyReadonlyArray1<f64>,
        amplitudes: PyReadonlyArray1<f64>,
    ) -> PyResult<()> {
        let p = phases
            .as_slice()
            .map_err(|_| PyValueError::new_err("phases must be contiguous"))?;
        let a = amplitudes
            .as_slice()
            .map_err(|_| PyValueError::new_err("amplitudes must be contiguous"))?;
        self.inner.propagate_init(p, a).map_err(temporal_err_to_py)
    }

    #[allow(clippy::type_complexity)]
    fn propagate<'py>(
        &mut self,
        py: Python<'py>,
        phases: PyReadonlyArray1<f64>,
        amplitudes: PyReadonlyArray1<f64>,
    ) -> PyResult<(Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>)> {
        let p = phases
            .as_slice()
            .map_err(|_| PyValueError::new_err("phases must be contiguous"))?;
        let a = amplitudes
            .as_slice()
            .map_err(|_| PyValueError::new_err("amplitudes must be contiguous"))?;
        let (bp, ba) = self.inner.propagate(p, a).map_err(temporal_err_to_py)?;
        Ok((PyArray1::from_vec(py, bp), PyArray1::from_vec(py, ba)))
    }

    fn reset(&mut self) {
        self.inner.reset();
    }

    fn __repr__(&self) -> String {
        format!(
            "TemporalPropagator(phase_alpha={}, amplitude_alpha={}, initialized={})",
            self.inner.phase_alpha(),
            self.inner.amplitude_alpha(),
            self.inner.is_initialized()
        )
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyComplexPhasorBlender>()?;
    m.add_class::<PyEmaAmplitudeBlender>()?;
    m.add_class::<PyTemporalPropagator>()?;
    Ok(())
}

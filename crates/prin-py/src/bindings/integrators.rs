//! PyO3 bindings for `prin_dynamics::integrate` (Euler, RK4, RK45, Exponential,
//! MultiRate integrators).

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;

use prin_dynamics::integrate::{
    integrate_fixed, AdaptiveResult, EulerIntegrator, ExponentialIntegrator, IntegrateError,
    Integrator, MultiRateIntegrator, MultiRateMethod, RK45Integrator, RK4Integrator,
};
use prin_dynamics::models::Dynamics;

use super::models::{PyHopfOscillator, PyKuramotoOscillator, PyStuartLandauOscillator};
use super::state::PyOscillatorState;

fn integrate_err_to_py(err: IntegrateError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Extract `&dyn Dynamics` from a Python object (any of the three model classes).
fn extract_dynamics(ob: &Bound<'_, PyAny>) -> PyResult<Box<dyn Dynamics>> {
    if let Ok(m) = ob.extract::<PyRef<'_, PyKuramotoOscillator>>() {
        return Ok(Box::new(m.inner.clone()));
    }
    if let Ok(m) = ob.extract::<PyRef<'_, PyStuartLandauOscillator>>() {
        return Ok(Box::new(m.inner.clone()));
    }
    if let Ok(m) = ob.extract::<PyRef<'_, PyHopfOscillator>>() {
        return Ok(Box::new(m.inner.clone()));
    }
    Err(PyValueError::new_err(
        "expected a KuramotoOscillator, StuartLandauOscillator, or HopfOscillator",
    ))
}

fn state_list_to_py(py: Python<'_>, traj: Vec<OscillatorState>) -> PyResult<Py<PyList>> {
    let items: Vec<Py<PyAny>> = traj
        .into_iter()
        .map(|s| {
            PyOscillatorState { inner: s }
                .into_pyobject(py)
                .map(|o| o.unbind().into_any())
        })
        .collect::<PyResult<Vec<_>>>()?;
    PyList::new(py, items).map(|l| l.unbind())
}

use prin_dynamics::state::OscillatorState;

// ---------------------------------------------------------------------------
// Euler integrator
// ---------------------------------------------------------------------------

/// Forward Euler integrator (first order).
#[pyclass(name = "EulerIntegrator", module = "prin._prin_core")]
pub struct PyEulerIntegrator {
    inner: EulerIntegrator,
}

#[pymethods]
impl PyEulerIntegrator {
    #[new]
    fn py_new() -> Self {
        Self {
            inner: EulerIntegrator::new(),
        }
    }

    /// Advance state by one timestep dt.
    fn step(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        dt: f64,
    ) -> PyResult<PyOscillatorState> {
        let dyn_model = extract_dynamics(model)?;
        let new_state = self
            .inner
            .step(dyn_model.as_ref(), &state.inner, dt)
            .map_err(integrate_err_to_py)?;
        Ok(PyOscillatorState { inner: new_state })
    }

    /// Integrate for n_steps fixed timesteps.
    ///
    /// Returns ``(final_state, trajectory)`` where trajectory is a list of
    /// states (one per step) if ``record_trajectory`` is true, else None.
    #[pyo3(signature = (model, state, n_steps, dt, record_trajectory=false))]
    fn integrate_fixed(
        &mut self,
        py: Python<'_>,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
    ) -> PyResult<(PyOscillatorState, Option<Py<PyList>>)> {
        let dyn_model = extract_dynamics(model)?;
        let (final_state, trajectory) = integrate_fixed(
            &mut self.inner,
            dyn_model.as_ref(),
            &state.inner,
            n_steps,
            dt,
            record_trajectory,
        )
        .map_err(integrate_err_to_py)?;
        let traj_objs = match trajectory {
            Some(traj) => Some(state_list_to_py(py, traj)?),
            None => None,
        };
        Ok((PyOscillatorState { inner: final_state }, traj_objs))
    }

    fn __repr__(&self) -> &'static str {
        "EulerIntegrator()"
    }
}

// ---------------------------------------------------------------------------
// RK4 integrator
// ---------------------------------------------------------------------------

/// Classic fourth-order Runge–Kutta integrator.
#[pyclass(name = "RK4Integrator", module = "prin._prin_core")]
pub struct PyRK4Integrator {
    inner: RK4Integrator,
}

#[pymethods]
impl PyRK4Integrator {
    #[new]
    fn py_new() -> Self {
        Self {
            inner: RK4Integrator::new(),
        }
    }

    /// Advance state by one timestep dt.
    fn step(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        dt: f64,
    ) -> PyResult<PyOscillatorState> {
        let dyn_model = extract_dynamics(model)?;
        let new_state = self
            .inner
            .step(dyn_model.as_ref(), &state.inner, dt)
            .map_err(integrate_err_to_py)?;
        Ok(PyOscillatorState { inner: new_state })
    }

    /// Integrate for n_steps fixed timesteps.
    #[pyo3(signature = (model, state, n_steps, dt, record_trajectory=false))]
    fn integrate_fixed(
        &mut self,
        py: Python<'_>,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
    ) -> PyResult<(PyOscillatorState, Option<Py<PyList>>)> {
        let dyn_model = extract_dynamics(model)?;
        let (final_state, trajectory) = integrate_fixed(
            &mut self.inner,
            dyn_model.as_ref(),
            &state.inner,
            n_steps,
            dt,
            record_trajectory,
        )
        .map_err(integrate_err_to_py)?;
        let traj_objs = match trajectory {
            Some(traj) => Some(state_list_to_py(py, traj)?),
            None => None,
        };
        Ok((PyOscillatorState { inner: final_state }, traj_objs))
    }

    fn __repr__(&self) -> &'static str {
        "RK4Integrator()"
    }
}

// ---------------------------------------------------------------------------
// RK45 (adaptive Dormand–Prince) integrator
// ---------------------------------------------------------------------------

/// Result of an adaptive RK45 integration.
#[pyclass(
    name = "AdaptiveResult",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyAdaptiveResult {
    inner: AdaptiveResult,
}

#[pymethods]
impl PyAdaptiveResult {
    /// Final oscillator state.
    #[getter]
    fn final_state(&self) -> PyOscillatorState {
        PyOscillatorState {
            inner: self.inner.final_state.clone(),
        }
    }

    /// Number of accepted steps.
    #[getter]
    fn accepted_steps(&self) -> usize {
        self.inner.accepted_steps
    }

    /// Number of rejected steps.
    #[getter]
    fn rejected_steps(&self) -> usize {
        self.inner.rejected_steps
    }

    /// Final timestep used.
    #[getter]
    fn final_dt(&self) -> f64 {
        self.inner.final_dt
    }

    /// Recorded trajectory (list of states), or None.
    #[getter]
    fn trajectory(&self, py: Python<'_>) -> PyResult<Option<Py<PyList>>> {
        match &self.inner.trajectory {
            Some(traj) => {
                let items: Vec<Py<PyAny>> = traj
                    .iter()
                    .map(|s| {
                        PyOscillatorState { inner: s.clone() }
                            .into_pyobject(py)
                            .map(|o| o.unbind().into_any())
                    })
                    .collect::<PyResult<Vec<_>>>()?;
                Ok(Some(PyList::new(py, items)?.unbind()))
            }
            None => Ok(None),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "AdaptiveResult(accepted={}, rejected={}, final_dt={:.2e})",
            self.inner.accepted_steps, self.inner.rejected_steps, self.inner.final_dt
        )
    }
}

/// Adaptive Dormand–Prince (DOPRI5) integrator.
#[pyclass(name = "RK45Integrator", module = "prin._prin_core")]
pub struct PyRK45Integrator {
    inner: RK45Integrator,
}

#[pymethods]
impl PyRK45Integrator {
    #[new]
    #[pyo3(signature = (rtol=1e-6, atol=1e-8, max_steps=100_000))]
    fn py_new(rtol: f64, atol: f64, max_steps: usize) -> PyResult<Self> {
        let inner = RK45Integrator::new(rtol, atol, max_steps).map_err(integrate_err_to_py)?;
        Ok(Self { inner })
    }

    /// Advance state by one timestep dt (using the adaptive controller).
    fn step(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        dt: f64,
    ) -> PyResult<PyOscillatorState> {
        let dyn_model = extract_dynamics(model)?;
        let new_state = self
            .inner
            .step(dyn_model.as_ref(), &state.inner, dt)
            .map_err(integrate_err_to_py)?;
        Ok(PyOscillatorState { inner: new_state })
    }

    /// Adaptive integration over ``t_span`` with initial step ``dt_init``.
    #[pyo3(signature = (model, state, t_span, dt_init, record_trajectory=false))]
    fn integrate_adaptive(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        t_span: f64,
        dt_init: f64,
        record_trajectory: bool,
    ) -> PyResult<PyAdaptiveResult> {
        let dyn_model = extract_dynamics(model)?;
        let result = self
            .inner
            .integrate_adaptive(
                dyn_model.as_ref(),
                &state.inner,
                t_span,
                dt_init,
                record_trajectory,
            )
            .map_err(integrate_err_to_py)?;
        Ok(PyAdaptiveResult { inner: result })
    }

    /// Integrate for n_steps fixed timesteps (using the adaptive controller).
    #[pyo3(signature = (model, state, n_steps, dt, record_trajectory=false))]
    fn integrate_fixed(
        &mut self,
        py: Python<'_>,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
    ) -> PyResult<(PyOscillatorState, Option<Py<PyList>>)> {
        let dyn_model = extract_dynamics(model)?;
        let (final_state, trajectory) = integrate_fixed(
            &mut self.inner,
            dyn_model.as_ref(),
            &state.inner,
            n_steps,
            dt,
            record_trajectory,
        )
        .map_err(integrate_err_to_py)?;
        let traj_objs = match trajectory {
            Some(traj) => Some(state_list_to_py(py, traj)?),
            None => None,
        };
        Ok((PyOscillatorState { inner: final_state }, traj_objs))
    }

    fn __repr__(&self) -> &'static str {
        "RK45Integrator()"
    }
}

// ---------------------------------------------------------------------------
// Exponential integrator
// ---------------------------------------------------------------------------

/// Exponential integrator for stiff oscillator dynamics.
///
/// Uses the exponential Euler method with Jacobian computed via forward
/// finite differences. Supports direct Padé(13) scaling-and-squaring for
/// small systems and Krylov–Arnoldi approximation for larger ones.
#[pyclass(name = "ExponentialIntegrator", module = "prin._prin_core")]
pub struct PyExponentialIntegrator {
    inner: ExponentialIntegrator,
}

#[pymethods]
impl PyExponentialIntegrator {
    #[new]
    #[pyo3(signature = (dim, krylov_rank=16, max_direct_dim=150, stiff_mode=false, stiff_cond_threshold=20.0, max_krylov_stiff=48))]
    fn py_new(
        dim: usize,
        krylov_rank: usize,
        max_direct_dim: usize,
        stiff_mode: bool,
        stiff_cond_threshold: f64,
        max_krylov_stiff: usize,
    ) -> PyResult<Self> {
        let inner = if stiff_mode {
            ExponentialIntegrator::with_stiff_mode(
                dim,
                krylov_rank,
                max_direct_dim,
                true,
                stiff_cond_threshold,
                max_krylov_stiff,
            )
        } else {
            ExponentialIntegrator::new(dim, krylov_rank, max_direct_dim)
        }
        .map_err(integrate_err_to_py)?;
        Ok(Self { inner })
    }

    /// Advance state by one timestep dt.
    fn step(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        dt: f64,
    ) -> PyResult<PyOscillatorState> {
        let dyn_model = extract_dynamics(model)?;
        let new_state = self
            .inner
            .step(dyn_model.as_ref(), &state.inner, dt)
            .map_err(integrate_err_to_py)?;
        Ok(PyOscillatorState { inner: new_state })
    }

    /// Integrate for n_steps with optional Jacobian caching.
    #[pyo3(signature = (model, state, n_steps, dt, record_trajectory=false, recompute_jacobian_every=1))]
    #[allow(clippy::too_many_arguments)]
    fn integrate(
        &mut self,
        py: Python<'_>,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
        recompute_jacobian_every: usize,
    ) -> PyResult<(PyOscillatorState, Option<Py<PyList>>)> {
        let dyn_model = extract_dynamics(model)?;
        let (final_state, trajectory) = self
            .inner
            .integrate(
                dyn_model.as_ref(),
                &state.inner,
                n_steps,
                dt,
                record_trajectory,
                recompute_jacobian_every,
            )
            .map_err(integrate_err_to_py)?;
        let traj_objs = match trajectory {
            Some(traj) => Some(state_list_to_py(py, traj)?),
            None => None,
        };
        Ok((PyOscillatorState { inner: final_state }, traj_objs))
    }

    /// System dimensionality (3N).
    #[getter]
    fn dim(&self) -> usize {
        self.inner.dim()
    }

    /// Krylov subspace rank.
    #[getter]
    fn krylov_rank(&self) -> usize {
        self.inner.krylov_rank()
    }

    /// Whether the Krylov path is used for the current dimension.
    #[getter]
    fn use_krylov(&self) -> bool {
        self.inner.use_krylov()
    }

    /// Whether adaptive stiff-mode Krylov is enabled.
    #[getter]
    fn stiff_mode(&self) -> bool {
        self.inner.stiff_mode()
    }

    fn __repr__(&self) -> String {
        format!(
            "ExponentialIntegrator(dim={}, krylov_rank={}, use_krylov={}, stiff_mode={})",
            self.inner.dim(),
            self.inner.krylov_rank(),
            self.inner.use_krylov(),
            self.inner.stiff_mode(),
        )
    }
}

// ---------------------------------------------------------------------------
// Multi-rate integrator
// ---------------------------------------------------------------------------

/// Multi-rate ODE integrator for hierarchical oscillator systems.
///
/// Divides each outer timestep into ``sub_steps`` inner RK4 or Euler steps,
/// allowing fast oscillators to be integrated with finer time resolution.
#[pyclass(name = "MultiRateIntegrator", module = "prin._prin_core")]
pub struct PyMultiRateIntegrator {
    inner: MultiRateIntegrator,
}

#[pymethods]
impl PyMultiRateIntegrator {
    #[new]
    #[pyo3(signature = (sub_steps=10, method="rk4"))]
    fn py_new(sub_steps: usize, method: &str) -> PyResult<Self> {
        let m = match method.to_lowercase().as_str() {
            "rk4" => MultiRateMethod::RK4,
            "euler" => MultiRateMethod::Euler,
            _ => {
                return Err(PyValueError::new_err(format!(
                    "method must be 'rk4' or 'euler', got '{method}'"
                )));
            }
        };
        let inner = MultiRateIntegrator::with_method(sub_steps, m).map_err(integrate_err_to_py)?;
        Ok(Self { inner })
    }

    /// Advance state by one timestep dt (with sub-stepping).
    fn step(
        &mut self,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        dt: f64,
    ) -> PyResult<PyOscillatorState> {
        let dyn_model = extract_dynamics(model)?;
        let new_state = self
            .inner
            .step(dyn_model.as_ref(), &state.inner, dt)
            .map_err(integrate_err_to_py)?;
        Ok(PyOscillatorState { inner: new_state })
    }

    /// Integrate for n_steps outer steps with sub-stepping.
    #[pyo3(signature = (model, state, n_steps, dt, record_trajectory=false))]
    fn integrate(
        &mut self,
        py: Python<'_>,
        model: &Bound<'_, PyAny>,
        state: &PyOscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
    ) -> PyResult<(PyOscillatorState, Option<Py<PyList>>)> {
        let dyn_model = extract_dynamics(model)?;
        let (final_state, trajectory) = self
            .inner
            .integrate(
                dyn_model.as_ref(),
                &state.inner,
                n_steps,
                dt,
                record_trajectory,
            )
            .map_err(integrate_err_to_py)?;
        let traj_objs = match trajectory {
            Some(traj) => Some(state_list_to_py(py, traj)?),
            None => None,
        };
        Ok((PyOscillatorState { inner: final_state }, traj_objs))
    }

    /// Number of sub-steps per outer step.
    #[getter]
    fn sub_steps(&self) -> usize {
        self.inner.sub_steps()
    }

    /// Inner integration method (``"rk4"`` or ``"euler"``).
    #[getter]
    fn method(&self) -> &'static str {
        match self.inner.method() {
            MultiRateMethod::RK4 => "rk4",
            MultiRateMethod::Euler => "euler",
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "MultiRateIntegrator(sub_steps={}, method={:?})",
            self.inner.sub_steps(),
            self.inner.method(),
        )
    }
}

/// Register integrator types into a module.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyEulerIntegrator>()?;
    m.add_class::<PyRK4Integrator>()?;
    m.add_class::<PyRK45Integrator>()?;
    m.add_class::<PyAdaptiveResult>()?;
    m.add_class::<PyExponentialIntegrator>()?;
    m.add_class::<PyMultiRateIntegrator>()?;
    Ok(())
}

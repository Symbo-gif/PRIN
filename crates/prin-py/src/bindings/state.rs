//! PyO3 bindings for `prin_dynamics::state` and `prin_dynamics::seed`.

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyList;

use prin_dynamics::seed::Seed;
use prin_dynamics::state::{
    OscillatorState, StateDerivatives, StateError, AMPLITUDE_MAX, AMPLITUDE_MIN, DERIV_CLAMP,
    SPARSE_EPS, TAU,
};

pub(crate) fn state_err_to_py(err: StateError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Oscillator state as a struct-of-arrays: phase, amplitude, natural frequency.
///
/// Phase is wrapped to `[0, 2π)`, amplitude is clamped to `[1e-6, 10]`.
#[pyclass(
    name = "OscillatorState",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyOscillatorState {
    pub(crate) inner: OscillatorState,
}

#[pymethods]
impl PyOscillatorState {
    #[new]
    #[pyo3(signature = (phase, amplitude, frequency, freq_band=None))]
    fn py_new(
        phase: PyReadonlyArray1<f64>,
        amplitude: PyReadonlyArray1<f64>,
        frequency: PyReadonlyArray1<f64>,
        freq_band: Option<PyReadonlyArray1<u32>>,
    ) -> PyResult<Self> {
        let p = phase
            .as_slice()
            .map_err(|_| PyTypeError::new_err("phase must be contiguous"))?;
        let a = amplitude
            .as_slice()
            .map_err(|_| PyTypeError::new_err("amplitude must be contiguous"))?;
        let f = frequency
            .as_slice()
            .map_err(|_| PyTypeError::new_err("frequency must be contiguous"))?;
        let fb = match freq_band {
            Some(ref arr) => Some(
                arr.as_slice()
                    .map_err(|_| PyTypeError::new_err("freq_band must be contiguous"))?
                    .to_vec(),
            ),
            None => None,
        };
        let inner = OscillatorState::new(p.to_vec(), a.to_vec(), f.to_vec(), fb)
            .map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    /// Number of oscillators.
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }

    /// Number of distinct frequency bands (0 if no bands assigned).
    #[getter]
    fn n_bands(&self) -> usize {
        self.inner.n_bands()
    }

    /// Phase array (copy).
    #[getter]
    fn phase<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.phase.clone())
    }

    /// Amplitude array (copy).
    #[getter]
    fn amplitude<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.amplitude.clone())
    }

    /// Frequency array (copy).
    #[getter]
    fn frequency<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.frequency.clone())
    }

    /// Frequency band labels (copy), or None.
    #[getter]
    fn freq_band<'py>(&self, py: Python<'py>) -> Option<Bound<'py, PyArray1<u32>>> {
        self.inner
            .freq_band
            .as_ref()
            .map(|v| PyArray1::from_vec(py, v.clone()))
    }

    /// Create a random initial state.
    #[staticmethod]
    #[pyo3(signature = (n, freq_range, seed))]
    fn create_random(n: usize, freq_range: (f64, f64), seed: &mut PySeed) -> PyResult<Self> {
        let inner = OscillatorState::create_random(n, freq_range, &mut seed.inner)
            .map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    /// Create a fully synchronized initial state.
    #[staticmethod]
    fn create_synchronized(n: usize, base_frequency: f64) -> PyResult<Self> {
        let inner =
            OscillatorState::create_synchronized(n, base_frequency).map_err(state_err_to_py)?;
        Ok(Self { inner })
    }

    /// Build the k-nearest-phase-neighbour index.
    fn phase_knn_index(&self, py: Python<'_>, k: usize) -> PyResult<Py<PyList>> {
        let idx = self.inner.phase_knn_index(k).map_err(state_err_to_py)?;
        let items: Vec<Py<PyAny>> = idx
            .into_iter()
            .map(|v| PyArray1::from_vec(py, v).into_any().unbind())
            .collect();
        PyList::new(py, items).map(|l| l.unbind())
    }

    fn __repr__(&self) -> String {
        format!(
            "OscillatorState(n_oscillators={}, n_bands={})",
            self.inner.n_oscillators(),
            self.inner.n_bands()
        )
    }

    fn __len__(&self) -> usize {
        self.inner.n_oscillators()
    }
}

/// Time derivatives of oscillator state: dphase/dt, damplitude/dt, dfrequency/dt.
#[pyclass(
    name = "StateDerivatives",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyStateDerivatives {
    pub(crate) inner: StateDerivatives,
}

#[pymethods]
impl PyStateDerivatives {
    /// dphase/dt array (copy).
    #[getter]
    fn dphase<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.dphase.clone())
    }

    /// damplitude/dt array (copy).
    #[getter]
    fn damplitude<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.damplitude.clone())
    }

    /// dfrequency/dt array (copy).
    #[getter]
    fn dfrequency<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        PyArray1::from_vec(py, self.inner.dfrequency.clone())
    }

    fn __repr__(&self) -> String {
        format!("StateDerivatives(n={})", self.inner.dphase.len())
    }
}

/// Deterministic counter-based seed authority for all PRIN randomness.
///
/// A `Seed` is a `(counter, key)` pair producing a reproducible stream
/// via PCG64.
#[pyclass(name = "Seed", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone)]
pub struct PySeed {
    pub(crate) inner: Seed,
}

#[pymethods]
impl PySeed {
    #[new]
    fn py_new(counter: u128, key: u128) -> Self {
        Self {
            inner: Seed::new(counter, key),
        }
    }

    /// Current counter position.
    #[getter]
    fn counter(&self) -> u128 {
        self.inner.counter()
    }

    /// Stream key.
    #[getter]
    fn key(&self) -> u128 {
        self.inner.key()
    }

    /// Advance the seed by `delta` outputs without drawing them.
    fn jump(&mut self, delta: u128) -> PyResult<()> {
        self.inner
            .jump(delta)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Draw the next f64 uniformly in [0, 1).
    fn next_f64(&mut self) -> f64 {
        self.inner.next_f64()
    }

    /// Draw the next f64 uniformly in [lo, hi).
    fn next_f64_range(&mut self, lo: f64, hi: f64) -> PyResult<f64> {
        self.inner
            .next_f64_range(lo, hi)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Draw the next u64.
    fn next_u64(&mut self) -> u64 {
        use rand::RngCore;
        self.inner.next_u64()
    }

    fn __repr__(&self) -> String {
        format!(
            "Seed(counter={}, key={})",
            self.inner.counter(),
            self.inner.key()
        )
    }
}

/// Register state/seed types and functions into a module.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyOscillatorState>()?;
    m.add_class::<PyStateDerivatives>()?;
    m.add_class::<PySeed>()?;
    m.add("TAU", TAU)?;
    m.add("AMPLITUDE_MIN", AMPLITUDE_MIN)?;
    m.add("AMPLITUDE_MAX", AMPLITUDE_MAX)?;
    m.add("DERIV_CLAMP", DERIV_CLAMP)?;
    m.add("SPARSE_EPS", SPARSE_EPS)?;
    Ok(())
}

//! PyO3 bindings for `prin_dynamics::bands`.

use numpy::PyArray1;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::bands::{
    create_band_state, delta_theta_gamma_network, theta_gamma_network, BandError, BandNetwork,
    BandParams, PacPair,
};
use prin_dynamics::coupling::CouplingMode;
use prin_dynamics::models::Dynamics;
use prin_dynamics::pac::PhaseAmplitudeCoupling;

use super::coupling::PyCouplingMode;
use super::state::PySeed;

fn band_err_to_py(err: BandError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Per-band dynamical parameters for a hierarchical band network.
///
/// `freq_adaptation_rate` defaults to `0.0` (frozen natural frequencies) and
/// `coupling_mode` defaults to mean-field. Pass
/// `CouplingMode.sparse_knn(k=...)` to match the PRINet 3.0 reference band
/// networks.
#[pyclass(name = "BandParams", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone)]
pub struct PyBandParams {
    pub(crate) inner: BandParams,
}

#[pymethods]
impl PyBandParams {
    #[new]
    #[pyo3(signature = (coupling_strength, decay_rate, freq_adaptation_rate=0.0, coupling_mode=None))]
    fn py_new(
        coupling_strength: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        coupling_mode: Option<&PyCouplingMode>,
    ) -> PyResult<Self> {
        let mode = coupling_mode
            .map(|m| m.inner.clone())
            .unwrap_or(CouplingMode::MeanField);
        Ok(Self {
            inner: BandParams::with_coupling(
                coupling_strength,
                decay_rate,
                freq_adaptation_rate,
                mode,
            )
            .map_err(band_err_to_py)?,
        })
    }

    #[getter]
    fn coupling_strength(&self) -> f64 {
        self.inner.coupling_strength
    }

    #[getter]
    fn decay_rate(&self) -> f64 {
        self.inner.decay_rate
    }

    #[getter]
    fn freq_adaptation_rate(&self) -> f64 {
        self.inner.freq_adaptation_rate
    }

    #[getter]
    fn coupling_mode(&self) -> PyCouplingMode {
        PyCouplingMode {
            inner: self.inner.coupling_mode.clone(),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "BandParams(coupling_strength={}, decay_rate={}, freq_adaptation_rate={}, coupling_mode={})",
            self.inner.coupling_strength,
            self.inner.decay_rate,
            self.inner.freq_adaptation_rate,
            match &self.inner.coupling_mode {
                CouplingMode::MeanField => "mean_field",
                CouplingMode::Full { .. } => "full",
                CouplingMode::SparseKnn { .. } => "sparse_knn",
            }
        )
    }
}

/// A slow→fast PAC coupling pair.
///
/// Adjacent pairs (delta→theta, theta→gamma) are the standard hierarchy, but
/// any strictly slow→fast pair (`slow_band < fast_band`) is permitted.
#[pyclass(name = "PacPair", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone)]
pub struct PyPacPair {
    inner: PacPair,
}

#[pymethods]
impl PyPacPair {
    #[new]
    fn py_new(
        slow_band: usize,
        fast_band: usize,
        modulation_depth: f64,
        phase_offset: f64,
    ) -> PyResult<Self> {
        let pac = PhaseAmplitudeCoupling::new(modulation_depth)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self {
            inner: PacPair::new(slow_band, fast_band, pac, phase_offset).map_err(band_err_to_py)?,
        })
    }

    #[getter]
    fn slow_band(&self) -> usize {
        self.inner.slow_band
    }

    #[getter]
    fn fast_band(&self) -> usize {
        self.inner.fast_band
    }

    #[getter]
    fn modulation_depth(&self) -> f64 {
        self.inner.pac.modulation_depth()
    }

    #[getter]
    fn phase_offset(&self) -> f64 {
        self.inner.phase_offset
    }

    fn __repr__(&self) -> String {
        format!(
            "PacPair(slow_band={}, fast_band={}, modulation_depth={}, phase_offset={})",
            self.inner.slow_band,
            self.inner.fast_band,
            self.inner.pac.modulation_depth(),
            self.inner.phase_offset
        )
    }
}

/// Continuous hierarchical band network.
///
/// Oscillators are partitioned into frequency bands (labelled 0, 1, …, B−1
/// from slowest to fastest). Intra-band dynamics are Kuramoto with the
/// per-band `CouplingMode` from `BandParams`; cross-band interactions are PAC
/// (slow phase → fast amplitude).
#[pyclass(name = "BandNetwork", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone)]
pub struct PyBandNetwork {
    inner: BandNetwork,
}

#[pymethods]
impl PyBandNetwork {
    #[new]
    fn py_new(
        band_sizes: Vec<usize>,
        band_params: Vec<PyRef<'_, PyBandParams>>,
        pac_pairs: Vec<PyRef<'_, PyPacPair>>,
    ) -> PyResult<Self> {
        let params: Vec<BandParams> = band_params.iter().map(|p| p.inner.clone()).collect();
        let pairs: Vec<PacPair> = pac_pairs.iter().map(|p| p.inner.clone()).collect();
        Ok(Self {
            inner: BandNetwork::new(band_sizes, params, pairs).map_err(band_err_to_py)?,
        })
    }

    /// Build a theta–gamma (2-band) network.
    #[staticmethod]
    #[pyo3(signature = (n_theta, n_gamma, theta_params, gamma_params, pac_modulation_depth, phase_offset=0.0))]
    fn theta_gamma(
        n_theta: usize,
        n_gamma: usize,
        theta_params: &PyBandParams,
        gamma_params: &PyBandParams,
        pac_modulation_depth: f64,
        phase_offset: f64,
    ) -> PyResult<Self> {
        let pac = PhaseAmplitudeCoupling::new(pac_modulation_depth)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self {
            inner: theta_gamma_network(
                n_theta,
                n_gamma,
                theta_params.inner.clone(),
                gamma_params.inner.clone(),
                pac,
                phase_offset,
            )
            .map_err(band_err_to_py)?,
        })
    }

    /// Build a delta–theta–gamma (3-band) network.
    #[staticmethod]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (n_delta, n_theta, n_gamma, delta_params, theta_params, gamma_params, pac_dt_depth, pac_tg_depth, offset_dt=0.0, offset_tg=0.0))]
    fn delta_theta_gamma(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        delta_params: &PyBandParams,
        theta_params: &PyBandParams,
        gamma_params: &PyBandParams,
        pac_dt_depth: f64,
        pac_tg_depth: f64,
        offset_dt: f64,
        offset_tg: f64,
    ) -> PyResult<Self> {
        let pac_dt = PhaseAmplitudeCoupling::new(pac_dt_depth)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let pac_tg = PhaseAmplitudeCoupling::new(pac_tg_depth)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self {
            inner: delta_theta_gamma_network(
                n_delta,
                n_theta,
                n_gamma,
                delta_params.inner.clone(),
                theta_params.inner.clone(),
                gamma_params.inner.clone(),
                pac_dt,
                pac_tg,
                offset_dt,
                offset_tg,
            )
            .map_err(band_err_to_py)?,
        })
    }

    /// Number of frequency bands.
    fn n_bands(&self) -> usize {
        self.inner.n_bands()
    }

    /// Total oscillator count across all bands.
    fn total_oscillators(&self) -> usize {
        self.inner.total_oscillators()
    }

    /// Oscillator count for band `b`.
    fn band_size(&self, b: usize) -> PyResult<usize> {
        if b >= self.inner.n_bands() {
            return Err(PyValueError::new_err(format!(
                "band index {b} out of range (network has {} bands)",
                self.inner.n_bands()
            )));
        }
        Ok(self.inner.band_size(b))
    }

    /// All band sizes as a list.
    fn band_sizes(&self) -> Vec<usize> {
        self.inner.band_sizes().to_vec()
    }

    /// Theoretical working-memory capacity (fast/slow frequency ratio).
    ///
    /// Requires an `OscillatorState` with valid `freq_band` labels.
    fn theoretical_capacity(&self, state: &super::state::PyOscillatorState) -> PyResult<usize> {
        self.inner
            .theoretical_capacity(&state.inner)
            .map_err(band_err_to_py)
    }

    /// Compute derivatives for a band-network state.
    ///
    /// Returns `(dphase, damplitude, dfrequency)` as numpy arrays.
    #[allow(clippy::type_complexity)]
    fn compute_derivatives<'py>(
        &self,
        py: Python<'py>,
        state: &super::state::PyOscillatorState,
    ) -> PyResult<(
        Bound<'py, PyArray1<f64>>,
        Bound<'py, PyArray1<f64>>,
        Bound<'py, PyArray1<f64>>,
    )> {
        let derivs = self
            .inner
            .compute_derivatives(&state.inner)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok((
            PyArray1::from_vec(py, derivs.dphase),
            PyArray1::from_vec(py, derivs.damplitude),
            PyArray1::from_vec(py, derivs.dfrequency),
        ))
    }

    fn __repr__(&self) -> String {
        format!(
            "BandNetwork(n_bands={}, total_oscillators={}, band_sizes={:?})",
            self.inner.n_bands(),
            self.inner.total_oscillators(),
            self.inner.band_sizes()
        )
    }
}

/// Create an oscillator state for a band network with random phases and
/// per-band uniform frequency ranges.
#[pyfunction]
#[pyo3(signature = (network, freq_ranges, seed))]
pub fn create_band_state_py(
    _py: Python<'_>,
    network: &PyBandNetwork,
    freq_ranges: Vec<(f64, f64)>,
    seed: &PySeed,
) -> PyResult<super::state::PyOscillatorState> {
    let mut seed_clone = seed.inner.clone();
    let state = create_band_state(&network.inner, &freq_ranges, &mut seed_clone)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(super::state::PyOscillatorState { inner: state })
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyBandParams>()?;
    m.add_class::<PyPacPair>()?;
    m.add_class::<PyBandNetwork>()?;
    m.add_function(wrap_pyfunction!(create_band_state_py, m)?)?;
    Ok(())
}

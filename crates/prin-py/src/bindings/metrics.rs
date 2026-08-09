//! PyO3 bindings for `prin_metrics` (order, coherence, spectral, energy, chimera,
//! metastability, k-NN).

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;

use prin_metrics::error::MetricError;

fn metric_err_to_py(err: MetricError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

// ---------------------------------------------------------------------------
// Order parameters
// ---------------------------------------------------------------------------

/// Kuramoto order parameter ``r = |1/N Σᵢ exp(iφᵢ)|``.
#[pyfunction]
fn kuramoto_order_parameter(phase: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::kuramoto_order_parameter(p).map_err(metric_err_to_py)
}

/// Complex Kuramoto order parameter ``Z = 1/N Σᵢ exp(iφᵢ)``.
///
/// Returns ``(real, imag)`` tuple.
#[pyfunction]
fn kuramoto_order_parameter_complex(phase: PyReadonlyArray1<f64>) -> PyResult<(f64, f64)> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let z = prin_metrics::kuramoto_order_parameter_complex(p).map_err(metric_err_to_py)?;
    Ok((z.re, z.im))
}

/// Circular inter-frame phase correlation.
#[pyfunction]
fn inter_frame_phase_correlation(
    phase_t: PyReadonlyArray1<f64>,
    phase_t_prev: PyReadonlyArray1<f64>,
) -> PyResult<f64> {
    let pt = phase_t
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase_t must be contiguous"))?;
    let pp = phase_t_prev
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase_t_prev must be contiguous"))?;
    prin_metrics::inter_frame_phase_correlation(pt, pp).map_err(metric_err_to_py)
}

/// Per-snapshot Kuramoto order parameter of a phase trajectory.
///
/// ``trajectory`` is flat row-major ``T × n``.
#[pyfunction]
fn order_parameter_series<'py>(
    py: Python<'py>,
    trajectory: PyReadonlyArray1<f64>,
    n: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let t = trajectory
        .as_slice()
        .map_err(|_| PyValueError::new_err("trajectory must be contiguous"))?;
    let series = prin_metrics::order_parameter_series(t, n).map_err(metric_err_to_py)?;
    Ok(PyArray1::from_vec(py, series))
}

// ---------------------------------------------------------------------------
// Coherence
// ---------------------------------------------------------------------------

/// Mean pairwise phase coherence.
#[pyfunction]
fn mean_phase_coherence(phase: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::mean_phase_coherence(p).map_err(metric_err_to_py)
}

/// Full N×N phase coherence matrix (flat row-major).
#[pyfunction]
fn phase_coherence_matrix<'py>(
    py: Python<'py>,
    phase: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let mat = prin_metrics::phase_coherence_matrix(p).map_err(metric_err_to_py)?;
    Ok(PyArray1::from_vec(py, mat))
}

/// Sparse k-NN mean phase coherence.
#[pyfunction]
fn sparse_mean_phase_coherence(
    phase: PyReadonlyArray1<f64>,
    neighbors: Vec<Vec<usize>>,
) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::sparse_mean_phase_coherence(p, &neighbors).map_err(metric_err_to_py)
}

// ---------------------------------------------------------------------------
// Spectral
// ---------------------------------------------------------------------------

/// Power spectral density of the resonance state.
#[pyfunction]
#[pyo3(signature = (amplitude, phase, n_freq_bins=None))]
fn power_spectral_density<'py>(
    py: Python<'py>,
    amplitude: PyReadonlyArray1<f64>,
    phase: PyReadonlyArray1<f64>,
    n_freq_bins: Option<usize>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let a = amplitude
        .as_slice()
        .map_err(|_| PyValueError::new_err("amplitude must be contiguous"))?;
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let result =
        prin_metrics::power_spectral_density(a, p, n_freq_bins).map_err(metric_err_to_py)?;
    Ok(PyArray1::from_vec(py, result))
}

/// Extract concept probabilities from the resonance state.
#[pyfunction]
#[pyo3(signature = (amplitude, phase, concept_frequencies, concept_bandwidths, n_freq_bins=None))]
fn extract_concept_probabilities<'py>(
    py: Python<'py>,
    amplitude: PyReadonlyArray1<f64>,
    phase: PyReadonlyArray1<f64>,
    concept_frequencies: PyReadonlyArray1<f64>,
    concept_bandwidths: PyReadonlyArray1<f64>,
    n_freq_bins: Option<usize>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let a = amplitude
        .as_slice()
        .map_err(|_| PyValueError::new_err("amplitude must be contiguous"))?;
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let cf = concept_frequencies
        .as_slice()
        .map_err(|_| PyValueError::new_err("concept_frequencies must be contiguous"))?;
    let cb = concept_bandwidths
        .as_slice()
        .map_err(|_| PyValueError::new_err("concept_bandwidths must be contiguous"))?;
    let result = prin_metrics::extract_concept_probabilities(a, p, cf, cb, n_freq_bins)
        .map_err(metric_err_to_py)?;
    Ok(PyArray1::from_vec(py, result))
}

// ---------------------------------------------------------------------------
// Energy
// ---------------------------------------------------------------------------

/// Dense synchronization energy.
#[pyfunction]
#[pyo3(signature = (phase, amplitude, coupling_matrix=None))]
fn synchronization_energy(
    phase: PyReadonlyArray1<f64>,
    amplitude: PyReadonlyArray1<f64>,
    coupling_matrix: Option<PyReadonlyArray1<f64>>,
) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let a = amplitude
        .as_slice()
        .map_err(|_| PyValueError::new_err("amplitude must be contiguous"))?;
    // Copy the matrix data to avoid borrow lifetime issues.
    let mat_owned: Option<Vec<f64>> = match coupling_matrix {
        Some(m) => Some(
            m.as_slice()
                .map_err(|_| PyValueError::new_err("coupling_matrix must be contiguous"))?
                .to_vec(),
        ),
        None => None,
    };
    prin_metrics::synchronization_energy(p, a, mat_owned.as_deref()).map_err(metric_err_to_py)
}

/// Sparse k-NN synchronization energy.
#[pyfunction]
fn sparse_synchronization_energy(
    phase: PyReadonlyArray1<f64>,
    amplitude: PyReadonlyArray1<f64>,
    neighbors: Vec<Vec<usize>>,
    coupling_strength: f64,
) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let a = amplitude
        .as_slice()
        .map_err(|_| PyValueError::new_err("amplitude must be contiguous"))?;
    prin_metrics::sparse_synchronization_energy(p, a, &neighbors, coupling_strength)
        .map_err(metric_err_to_py)
}

// ---------------------------------------------------------------------------
// Chimera
// ---------------------------------------------------------------------------

/// Local Kuramoto order parameter for each oscillator.
#[pyfunction]
fn local_order_parameter<'py>(
    py: Python<'py>,
    phase: PyReadonlyArray1<f64>,
    neighbors: Vec<Vec<usize>>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let r = prin_metrics::local_order_parameter(p, &neighbors).map_err(metric_err_to_py)?;
    Ok(PyArray1::from_vec(py, r))
}

/// Sarle's bimodality coefficient.
#[pyfunction]
fn bimodality_index(values: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let v = values
        .as_slice()
        .map_err(|_| PyValueError::new_err("values must be contiguous"))?;
    prin_metrics::bimodality_index(v).map_err(metric_err_to_py)
}

/// Strength of incoherence (Gopal et al. 2014).
#[pyfunction]
fn strength_of_incoherence(phase: PyReadonlyArray1<f64>, window_size: usize) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::strength_of_incoherence(p, window_size).map_err(metric_err_to_py)
}

/// Discontinuity measure (chimera number η).
///
/// Returns ``(coherence_mask, eta)`` where mask is a list of bools.
#[pyfunction]
fn discontinuity_measure(
    phase: PyReadonlyArray1<f64>,
    threshold_ratio: f64,
) -> PyResult<(Vec<bool>, usize)> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::discontinuity_measure(p, threshold_ratio).map_err(metric_err_to_py)
}

/// Chimera index χ ∈ [0, 1].
#[pyfunction]
fn chimera_index(
    phase: PyReadonlyArray1<f64>,
    neighbors: Vec<Vec<usize>>,
    threshold: f64,
) -> PyResult<f64> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    prin_metrics::chimera_index(p, &neighbors, threshold).map_err(metric_err_to_py)
}

/// Time-averaged strength of incoherence over a trajectory.
///
/// ``trajectory`` is a list of per-snapshot phase arrays.
#[pyfunction]
fn strength_of_incoherence_temporal(
    trajectory: Vec<Vec<f64>>,
    window_size: usize,
    discard_transient: usize,
) -> PyResult<f64> {
    prin_metrics::strength_of_incoherence_temporal(&trajectory, window_size, discard_transient)
        .map_err(metric_err_to_py)
}

/// Bimodality chimera threshold constant (5/9).
#[pyfunction]
fn bimodality_chimera_threshold() -> f64 {
    prin_metrics::BIMODALITY_CHIMERA_THRESHOLD
}

/// Default chimera threshold constant.
#[pyfunction]
fn default_chimera_threshold() -> f64 {
    prin_metrics::DEFAULT_CHIMERA_THRESHOLD
}

// ---------------------------------------------------------------------------
// Metastability
// ---------------------------------------------------------------------------

/// Metastability: temporal std of the Kuramoto order parameter.
///
/// ``trajectory`` is flat row-major ``T × n``.
#[pyfunction]
fn metastability(trajectory: PyReadonlyArray1<f64>, n: usize) -> PyResult<f64> {
    let t = trajectory
        .as_slice()
        .map_err(|_| PyValueError::new_err("trajectory must be contiguous"))?;
    prin_metrics::metastability(t, n).map_err(metric_err_to_py)
}

// ---------------------------------------------------------------------------
// k-NN
// ---------------------------------------------------------------------------

/// Build k-nearest-phase-neighbour index.
///
/// Returns a list of numpy arrays of neighbour indices.
#[pyfunction]
fn build_phase_knn<'py>(
    py: Python<'py>,
    phase: PyReadonlyArray1<f64>,
    k: usize,
) -> PyResult<Py<PyList>> {
    let p = phase
        .as_slice()
        .map_err(|_| PyValueError::new_err("phase must be contiguous"))?;
    let idx = prin_metrics::build_phase_knn(p, k).map_err(metric_err_to_py)?;
    let items: Vec<Py<PyAny>> = idx
        .into_iter()
        .map(|v| PyArray1::from_vec(py, v).into_any().unbind())
        .collect();
    PyList::new(py, items).map(|l| l.unbind())
}

/// Register all metric functions into a module.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Order
    m.add_function(wrap_pyfunction!(kuramoto_order_parameter, m)?)?;
    m.add_function(wrap_pyfunction!(kuramoto_order_parameter_complex, m)?)?;
    m.add_function(wrap_pyfunction!(inter_frame_phase_correlation, m)?)?;
    m.add_function(wrap_pyfunction!(order_parameter_series, m)?)?;

    // Coherence
    m.add_function(wrap_pyfunction!(mean_phase_coherence, m)?)?;
    m.add_function(wrap_pyfunction!(phase_coherence_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_mean_phase_coherence, m)?)?;

    // Spectral
    m.add_function(wrap_pyfunction!(power_spectral_density, m)?)?;
    m.add_function(wrap_pyfunction!(extract_concept_probabilities, m)?)?;

    // Energy
    m.add_function(wrap_pyfunction!(synchronization_energy, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_synchronization_energy, m)?)?;

    // Chimera
    m.add_function(wrap_pyfunction!(local_order_parameter, m)?)?;
    m.add_function(wrap_pyfunction!(bimodality_index, m)?)?;
    m.add_function(wrap_pyfunction!(strength_of_incoherence, m)?)?;
    m.add_function(wrap_pyfunction!(discontinuity_measure, m)?)?;
    m.add_function(wrap_pyfunction!(chimera_index, m)?)?;
    m.add_function(wrap_pyfunction!(strength_of_incoherence_temporal, m)?)?;
    m.add_function(wrap_pyfunction!(bimodality_chimera_threshold, m)?)?;
    m.add_function(wrap_pyfunction!(default_chimera_threshold, m)?)?;

    // Metastability
    m.add_function(wrap_pyfunction!(metastability, m)?)?;

    // k-NN
    m.add_function(wrap_pyfunction!(build_phase_knn, m)?)?;

    Ok(())
}

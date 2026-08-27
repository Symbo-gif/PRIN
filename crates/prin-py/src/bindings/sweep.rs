//! Thin list/scalar PyO3 bindings for `prin-sim` compatibility owners.

use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::Seed;
use prin_sim::compat::{
    build_knn_neighbors as build_neighbors_owner, coupling_to_csr, coupling_to_dense,
    csr_coupling_step as csr_step_owner, phase_to_rate as phase_to_rate_owner,
    sparse_coupling_matrix as sparse_matrix_owner, sparse_knn_coupling_step as sparse_step_owner,
    sweep_coupling_params as sweep_owner, CouplingParamSweepConfig, KnnNeighbors, PhaseToRateMode,
};
use prin_sim::{detect_oscillation as detect_owner, SparseCoupling};

fn value_error(error: impl core::fmt::Display) -> PyErr {
    PyValueError::new_err(error.to_string())
}

fn seed(counter: u64, key: u64) -> Seed {
    Seed::new(counter as u128, key as u128)
}

/// Build `k` deterministic, unique, non-self neighbors for every oscillator.
///
/// Returns a flattened row-major ``(n_oscillators, k)`` list of neighbor
/// indices. Randomness comes only from the ``seed_counter``/``seed_key`` pair
/// through ``prin_dynamics::Seed``; the same pair always produces the same
/// table. PRINet 3.0 used ``torch.Generator`` streams with a different sampling
/// order, so the same scalar seed value does not guarantee the same neighbor
/// topology across implementations. Compare PRIN topologies through this
/// function or the public ``prin.kernels.build_knn_neighbors`` wrapper.
///
/// # Errors
///
/// Returns ``ValueError`` when ``n_oscillators < 2``, ``k == 0``,
/// ``k >= n_oscillators``, or the requested shape overflows.
#[pyfunction]
#[pyo3(signature = (n_oscillators, k=8, seed_counter=0, seed_key=0))]
fn build_knn_neighbors(
    n_oscillators: usize,
    k: usize,
    seed_counter: u64,
    seed_key: u64,
) -> PyResult<Vec<usize>> {
    build_neighbors_owner(n_oscillators, k, seed(seed_counter, seed_key))
        .map(|neighbors| neighbors.indices().to_vec())
        .map_err(value_error)
}

/// Generate a dense random coupling matrix from a sparse PRINet 3.0-style draw.
///
/// An edge is retained when a uniform draw exceeds ``sparsity``; retained
/// magnitudes are half-normal draws scaled by ``coupling_strength / N``.
/// The diagonal is always zero. In symmetric mode the upper-triangle mask is
/// mirrored and opposite-direction magnitudes are averaged. Randomness is
/// derived only from ``seed_counter``/``seed_key``.
///
/// # Errors
///
/// Returns ``ValueError`` for an empty population, ``sparsity`` outside
/// ``[0, 1)``, a non-finite ``coupling_strength``, shape overflow, or sparse
/// owner construction failure.
#[pyfunction]
#[pyo3(signature = (n_oscillators, sparsity=0.9, coupling_strength=1.0, symmetric=true, seed_counter=0, seed_key=0))]
fn sparse_coupling_matrix(
    n_oscillators: usize,
    sparsity: f64,
    coupling_strength: f64,
    symmetric: bool,
    seed_counter: u64,
    seed_key: u64,
) -> PyResult<Vec<f64>> {
    sparse_matrix_owner(
        n_oscillators,
        sparsity,
        coupling_strength,
        symmetric,
        seed(seed_counter, seed_key),
    )
    .map(|coupling| coupling_to_dense(&coupling))
    .map_err(value_error)
}

/// Generate a CSR random coupling matrix from a sparse PRINet 3.0-style draw.
///
/// Uses the same retention and magnitude rules as ``sparse_coupling_matrix``
/// but returns owned CSR arrays ``(crow_indices, col_indices, values)``
/// instead of a dense row-major vector. These arrays can be passed directly to
/// ``csr_coupling_step`` or to ``torch.sparse_csr_tensor``.
///
/// # Errors
///
/// Returns ``ValueError`` for the same input violations as
/// ``sparse_coupling_matrix``.
#[pyfunction]
#[pyo3(signature = (n_oscillators, sparsity=0.95, coupling_strength=1.0, symmetric=true, seed_counter=0, seed_key=0))]
fn sparse_coupling_matrix_csr(
    n_oscillators: usize,
    sparsity: f64,
    coupling_strength: f64,
    symmetric: bool,
    seed_counter: u64,
    seed_key: u64,
) -> PyResult<(Vec<usize>, Vec<usize>, Vec<f64>)> {
    sparse_matrix_owner(
        n_oscillators,
        sparsity,
        coupling_strength,
        symmetric,
        seed(seed_counter, seed_key),
    )
    .map(|coupling| {
        let csr = coupling_to_csr(&coupling);
        (csr.indptr, csr.indices, csr.data)
    })
    .map_err(value_error)
}

/// Compute Kuramoto sine corrections from a CSR coupling matrix.
///
/// Evaluates ``sum_j W[i,j] * sin(phase[j] - phase[i])`` for each oscillator
/// using the supplied CSR arrays. The ``crow_indices`` length must be
/// ``n + 1`` where ``n`` is the square matrix dimension.
///
/// # Errors
///
/// Returns ``ValueError`` for an empty ``crow_indices``, CSR construction
/// failure, shape mismatch, or non-finite ``phase`` values.
#[pyfunction]
fn csr_coupling_step(
    phase: Vec<f64>,
    crow_indices: Vec<usize>,
    col_indices: Vec<usize>,
    values: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let n = crow_indices
        .len()
        .checked_sub(1)
        .ok_or_else(|| PyValueError::new_err("crow_indices must be non-empty"))?;
    let coupling =
        SparseCoupling::from_csr(&crow_indices, &col_indices, &values, n).map_err(value_error)?;
    csr_step_owner(&phase, &coupling).map_err(value_error)
}

/// Compute sparse k-NN phase corrections from a flattened neighbor table.
///
/// ``neighbors`` is a row-major ``(n_oscillators, k)`` table. The archived
/// compatibility formula is ``K/k * sum_j sin(phase[j] - phase[i])`` and does
/// not use amplitude values, but ``amplitude`` is still validated for length
/// and finiteness.
///
/// # Errors
///
/// Returns ``ValueError`` for an empty or mismatched neighbor table,
/// length/finiteness violations, or invalid ``coupling_strength``.
#[pyfunction]
#[pyo3(signature = (phase, amplitude, neighbors, coupling_strength=2.0))]
fn sparse_knn_coupling_step(
    phase: Vec<f64>,
    amplitude: Vec<f64>,
    neighbors: Vec<usize>,
    coupling_strength: f64,
) -> PyResult<Vec<f64>> {
    if phase.is_empty() || neighbors.is_empty() || neighbors.len() % phase.len() != 0 {
        return Err(PyValueError::new_err(
            "neighbors must be a non-empty flattened (n, k) table",
        ));
    }
    let table = KnnNeighbors::from_indices(phase.len(), neighbors.len() / phase.len(), neighbors)
        .map_err(value_error)?;
    sparse_step_owner(&phase, &amplitude, &table, coupling_strength).map_err(value_error)
}

/// Sweep coupling strength ``K`` and PAC depth ``m`` over the audited dynamics.
///
/// Returns one dictionary per ``(K, m)`` Cartesian pair with keys ``"K"``,
/// ``"m"``, ``"r_delta"``, ``"r_theta"``, and ``"r_gamma"``. Each point is
/// integrated with the same ``seed`` so the result grid is deterministic. The
/// Rust owner is the continuous ``prin_dynamics::BandNetwork`` design; RK4
/// integration and final order parameters are delegated to
/// ``prin-dynamics`` and ``prin-metrics``.
///
/// # Errors
///
/// Returns ``ValueError`` for an empty or invalid parameter grid,
/// ``n_steps == 0``, non-positive ``dt``, or delegated integration/metric
/// failures.
#[pyfunction]
#[pyo3(signature = (n_oscillators=64, k_values=None, m_values=None, n_steps=100, dt=0.01, seed_counter=0, seed_key=0))]
#[allow(clippy::too_many_arguments)]
fn sweep_coupling_params(
    n_oscillators: usize,
    k_values: Option<Vec<f64>>,
    m_values: Option<Vec<f64>>,
    n_steps: usize,
    dt: f64,
    seed_counter: u64,
    seed_key: u64,
) -> PyResult<Vec<HashMap<&'static str, f64>>> {
    let config = CouplingParamSweepConfig {
        n_oscillators,
        k_values: k_values.unwrap_or_else(|| vec![0.5, 1.0, 2.0, 4.0]),
        m_values: m_values.unwrap_or_else(|| vec![0.1, 0.3, 0.5, 0.7]),
        n_steps,
        dt,
    };
    sweep_owner(&config, seed(seed_counter, seed_key))
        .map(|results| {
            results
                .into_iter()
                .map(|result| {
                    HashMap::from([
                        ("K", result.coupling_strength),
                        ("m", result.pac_depth),
                        ("r_delta", result.r_delta),
                        ("r_theta", result.r_theta),
                        ("r_gamma", result.r_gamma),
                    ])
                })
                .collect()
        })
        .map_err(value_error)
}

/// Detect destabilizing oscillations in an order-parameter history.
///
/// Splits ``r_history`` into overlapping windows of length ``window`` and
/// compares the windowed variance against ``threshold``. Returns ``True`` when
/// a window exceeds the threshold, indicating an oscillatory instability.
///
/// # Errors
///
/// Returns ``ValueError`` for an empty ``r_history`` (the owner rejects this),
/// non-finite values, ``window == 0``, or a negative/non-finite ``threshold``.
#[pyfunction]
#[pyo3(signature = (r_history, window=20, threshold=0.01))]
fn detect_oscillation(r_history: Vec<f64>, window: usize, threshold: f64) -> PyResult<bool> {
    if let Some((index, value)) = r_history
        .iter()
        .enumerate()
        .find(|(_, value)| !value.is_finite())
    {
        return Err(PyValueError::new_err(format!(
            "non-finite value in r_history at index {index}: {value}"
        )));
    }
    if window == 0 {
        return Err(PyValueError::new_err("window must be positive"));
    }
    if !threshold.is_finite() || threshold < 0.0 {
        return Err(PyValueError::new_err(format!(
            "threshold must be finite and non-negative, got {threshold}"
        )));
    }
    Ok(detect_owner(&r_history, window, threshold))
}

/// Convert phase/amplitude rows to sparse winner-take-all rates.
///
/// First computes the instantaneous rate ``amplitude * (1 + cos(phase)) / 2``
/// and then applies a soft (temperature-scaled softmax), hard (top-k), or
/// annealed (sigmoid blend of soft and hard) winner-take-all rule.
///
/// # Errors
///
/// Returns ``ValueError`` for empty/mismatched inputs, non-finite or negative
/// amplitudes, ``sparsity`` outside ``[0, 1]``, ``temperature <= 0``, or an
/// unknown ``mode`` string.
#[pyfunction]
#[pyo3(signature = (phase, amplitude, mode="soft", sparsity=0.1, temperature=1.0))]
fn phase_to_rate(
    phase: Vec<f64>,
    amplitude: Vec<f64>,
    mode: &str,
    sparsity: f64,
    temperature: f64,
) -> PyResult<Vec<f64>> {
    let mode = match mode {
        "soft" => PhaseToRateMode::Soft,
        "hard" => PhaseToRateMode::Hard,
        "annealed" => PhaseToRateMode::Annealed,
        other => {
            return Err(PyValueError::new_err(format!(
                "Unknown phase_to_rate mode '{other}'. Use 'soft', 'hard', or 'annealed'."
            )))
        }
    };
    phase_to_rate_owner(&phase, &amplitude, mode, sparsity, temperature).map_err(value_error)
}

/// Register sparse-coupling and sweep compatibility functions.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(build_knn_neighbors, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_coupling_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_coupling_matrix_csr, m)?)?;
    m.add_function(wrap_pyfunction!(csr_coupling_step, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_knn_coupling_step, m)?)?;
    m.add_function(wrap_pyfunction!(sweep_coupling_params, m)?)?;
    m.add_function(wrap_pyfunction!(detect_oscillation, m)?)?;
    m.add_function(wrap_pyfunction!(phase_to_rate, m)?)?;
    Ok(())
}

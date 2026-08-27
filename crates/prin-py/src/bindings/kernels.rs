//! Thin list/scalar PyO3 bindings for the authoritative CPU compatibility kernels.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_kernels::compat::{
    cross_band_coupling_cpu, fused_discrete_step_cpu, fused_discrete_step_full_cpu,
    fused_sub_step_rk4_cpu, hierarchical_order_parameter_cpu, multi_rate_derivatives_cpu,
    multi_rate_rk4_step_cpu, CompatDynamicsParams, DenseDiscreteParams,
};
use prin_kernels::mean_field_rk4::{step_cpu, MeanFieldRk4Params};
use prin_kernels::pac::{pac_modulate_cpu, PacParams};
use prin_kernels::sparse_knn::{sparse_knn_derivatives_cpu, SparseKnnGraph, SparseKnnParams};

fn value_error(error: impl core::fmt::Display) -> PyErr {
    PyValueError::new_err(error.to_string())
}

fn require_finite(name: &str, values: &[f32]) -> PyResult<()> {
    if let Some((index, value)) = values
        .iter()
        .enumerate()
        .find(|(_, value)| !value.is_finite())
    {
        return Err(PyValueError::new_err(format!(
            "non-finite value in {name} at index {index}: {value}"
        )));
    }
    Ok(())
}

fn fixed3<T>(name: &str, values: Vec<T>) -> PyResult<[T; 3]> {
    values.try_into().map_err(|values: Vec<T>| {
        PyValueError::new_err(format!(
            "{name} must contain exactly 3 values, got {}",
            values.len()
        ))
    })
}

fn graph_from_rows(n: usize, neighbors: Vec<u32>) -> PyResult<SparseKnnGraph> {
    if n == 0 || neighbors.is_empty() || neighbors.len() % n != 0 {
        return Err(PyValueError::new_err(format!(
            "neighbors must be a non-empty flattened (n, k) table for n={n}, got {} values",
            neighbors.len()
        )));
    }
    let k = neighbors.len() / n;
    let indptr = (0..=n)
        .map(|row| {
            u32::try_from(row * k)
                .map_err(|_| PyValueError::new_err("neighbor table is too large for u32 CSR"))
        })
        .collect::<PyResult<Vec<_>>>()?;
    SparseKnnGraph::from_csr(n, indptr, neighbors).map_err(value_error)
}

#[pyfunction]
fn pytorch_mean_field_rk4_step(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    k: f32,
    decay: f32,
    gamma: f32,
    dt: f32,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>)> {
    require_finite("phase", &phase)?;
    require_finite("amplitude", &amplitude)?;
    require_finite("frequency", &frequency)?;
    step_cpu(
        &phase,
        &amplitude,
        &frequency,
        &MeanFieldRk4Params {
            k,
            decay,
            gamma,
            dt,
        },
    )
    .map_err(value_error)
}

#[pyfunction]
fn pytorch_sparse_knn_coupling(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    neighbors: Vec<u32>,
    k: f32,
    decay: f32,
    gamma: f32,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>)> {
    let graph = graph_from_rows(phase.len(), neighbors)?;
    sparse_knn_derivatives_cpu(
        &phase,
        &amplitude,
        &frequency,
        &graph,
        &SparseKnnParams { k, decay, gamma },
    )
    .map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (slow_phase, fast_amplitude, modulation_depth, amp_min=1e-6, amp_max=10.0))]
fn pytorch_pac_modulation(
    slow_phase: Vec<f32>,
    fast_amplitude: Vec<f32>,
    modulation_depth: f32,
    amp_min: f32,
    amp_max: f32,
) -> PyResult<Vec<f32>> {
    pac_modulate_cpu(
        &slow_phase,
        &fast_amplitude,
        &PacParams {
            modulation_depth,
            phase_offset: 0.0,
            amp_min,
            amp_max,
        },
    )
    .map_err(value_error)
}

#[pyfunction]
fn pytorch_hierarchical_order_param(phase: Vec<f32>, band_sizes: Vec<usize>) -> PyResult<Vec<f32>> {
    hierarchical_order_parameter_cpu(&phase, &band_sizes).map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (phase, amplitude, frequency, k, decay, gamma, dt, sub_steps, mean_field=true))]
#[allow(clippy::too_many_arguments)]
fn pytorch_multi_rate_rk4_step(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    k: f32,
    decay: f32,
    gamma: f32,
    dt: f32,
    sub_steps: usize,
    mean_field: bool,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>)> {
    multi_rate_rk4_step_cpu(
        &phase,
        &amplitude,
        &frequency,
        &CompatDynamicsParams { k, decay, gamma },
        dt,
        sub_steps,
        mean_field,
    )
    .map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (phase, amplitude, frequency, freq_band, k, decay, gamma, band_frequencies=None))]
#[allow(clippy::too_many_arguments)]
fn pytorch_multi_rate_derivatives(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    freq_band: Vec<u8>,
    k: f32,
    decay: f32,
    gamma: f32,
    band_frequencies: Option<Vec<f32>>,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>)> {
    let bands = fixed3(
        "band_frequencies",
        band_frequencies.unwrap_or_else(|| vec![2.0, 6.0, 40.0]),
    )?;
    multi_rate_derivatives_cpu(
        &phase,
        &amplitude,
        &frequency,
        &freq_band,
        &CompatDynamicsParams { k, decay, gamma },
        bands,
    )
    .map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (phase, amplitude, frequency, freq_band, k, decay, gamma, dt, sub_steps_per_band=None))]
#[allow(clippy::too_many_arguments)]
fn pytorch_fused_sub_step_rk4(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    freq_band: Vec<u8>,
    k: f32,
    decay: f32,
    gamma: f32,
    dt: f32,
    sub_steps_per_band: Option<Vec<usize>>,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>)> {
    let steps = fixed3(
        "sub_steps_per_band",
        sub_steps_per_band.unwrap_or_else(|| vec![1, 3, 20]),
    )?;
    fused_sub_step_rk4_cpu(
        &phase,
        &amplitude,
        &frequency,
        &freq_band,
        &CompatDynamicsParams { k, decay, gamma },
        dt,
        steps,
    )
    .map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (slow_phase, fast_phase, fast_amplitude, parent_idx, modulation_depth=0.3, epsilon=1e-6))]
fn pytorch_cross_band_coupling(
    slow_phase: Vec<f32>,
    fast_phase: Vec<f32>,
    fast_amplitude: Vec<f32>,
    parent_idx: Vec<usize>,
    modulation_depth: f32,
    epsilon: f32,
) -> PyResult<(Vec<f32>, Vec<f32>)> {
    cross_band_coupling_cpu(
        &slow_phase,
        &fast_phase,
        &fast_amplitude,
        &parent_idx,
        modulation_depth,
        epsilon,
        10.0,
    )
    .map_err(value_error)
}

#[allow(clippy::too_many_arguments)]
fn dense_params(mu_delta: f32, mu_theta: f32, mu_gamma: f32, dt: f32) -> DenseDiscreteParams {
    DenseDiscreteParams {
        mu: [mu_delta, mu_theta, mu_gamma],
        dt,
        amp_min: 1e-6,
        amp_max: 10.0,
    }
}

#[pyfunction]
#[pyo3(signature = (phase, amplitude, freq_delta, freq_theta, freq_gamma, w_delta, w_theta, w_gamma, mu_delta, mu_theta, mu_gamma, n_delta, n_theta, n_gamma, dt=0.01))]
#[allow(clippy::too_many_arguments)]
fn pytorch_fused_discrete_step(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    freq_delta: Vec<f32>,
    freq_theta: Vec<f32>,
    freq_gamma: Vec<f32>,
    w_delta: Vec<f32>,
    w_theta: Vec<f32>,
    w_gamma: Vec<f32>,
    mu_delta: f32,
    mu_theta: f32,
    mu_gamma: f32,
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
    dt: f32,
) -> PyResult<(Vec<f32>, Vec<f32>)> {
    let total = n_delta
        .checked_add(n_theta)
        .and_then(|value| value.checked_add(n_gamma))
        .ok_or_else(|| PyValueError::new_err("band-size sum overflow"))?;
    if total == 0 || phase.len() % total != 0 {
        return Err(PyValueError::new_err(
            "phase length must be divisible by the total band size",
        ));
    }
    fused_discrete_step_cpu(
        &phase,
        &amplitude,
        phase.len() / total,
        [&freq_delta, &freq_theta, &freq_gamma],
        [&w_delta, &w_theta, &w_gamma],
        [n_delta, n_theta, n_gamma],
        &dense_params(mu_delta, mu_theta, mu_gamma, dt),
    )
    .map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (phase, amplitude, freq_delta, freq_theta, freq_gamma, w_delta, w_theta, w_gamma, w_pac_dt_weight, w_pac_dt_bias, w_pac_tg_weight, w_pac_tg_bias, mu_delta, mu_theta, mu_gamma, dt=0.01, n_delta=4, n_theta=8, n_gamma=32))]
#[allow(clippy::too_many_arguments)]
fn pytorch_fused_discrete_step_full(
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    freq_delta: Vec<f32>,
    freq_theta: Vec<f32>,
    freq_gamma: Vec<f32>,
    w_delta: Vec<f32>,
    w_theta: Vec<f32>,
    w_gamma: Vec<f32>,
    w_pac_dt_weight: Vec<f32>,
    w_pac_dt_bias: Vec<f32>,
    w_pac_tg_weight: Vec<f32>,
    w_pac_tg_bias: Vec<f32>,
    mu_delta: f32,
    mu_theta: f32,
    mu_gamma: f32,
    dt: f32,
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
) -> PyResult<(Vec<f32>, Vec<f32>)> {
    let total = n_delta
        .checked_add(n_theta)
        .and_then(|value| value.checked_add(n_gamma))
        .ok_or_else(|| PyValueError::new_err("band-size sum overflow"))?;
    if total == 0 || phase.len() % total != 0 {
        return Err(PyValueError::new_err(
            "phase length must be divisible by the total band size",
        ));
    }
    fused_discrete_step_full_cpu(
        &phase,
        &amplitude,
        phase.len() / total,
        [&freq_delta, &freq_theta, &freq_gamma],
        [&w_delta, &w_theta, &w_gamma],
        [&w_pac_dt_weight, &w_pac_tg_weight],
        [&w_pac_dt_bias, &w_pac_tg_bias],
        [n_delta, n_theta, n_gamma],
        &dense_params(mu_delta, mu_theta, mu_gamma, dt),
    )
    .map_err(value_error)
}

/// Register kernel compatibility functions.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pytorch_mean_field_rk4_step, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_sparse_knn_coupling, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_pac_modulation, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_hierarchical_order_param, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_multi_rate_rk4_step, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_multi_rate_derivatives, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_fused_sub_step_rk4, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_cross_band_coupling, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_fused_discrete_step, m)?)?;
    m.add_function(wrap_pyfunction!(pytorch_fused_discrete_step_full, m)?)?;
    Ok(())
}

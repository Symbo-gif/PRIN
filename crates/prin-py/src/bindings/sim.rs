//! PyO3 bindings for the reference-faithful `OscilloSim` rebuild and the
//! Year-4-Q1 topology / initial-condition / statistics owners in `prin-sim`.
//!
//! These back the `prin.simulation` and `prin.y4q1_tools` compatibility
//! surfaces that WP-036C S1 (`0144M5`) ports the `test_y4q1*` acceptance suite
//! against. All numerical authority stays in `prin_sim::oscillo_compat` /
//! `prin_sim::y4q1_stats`; this module only marshals Python `<->` Rust types.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_sim::oscillo_compat::{
    chimera_initial_condition as chimera_ic_owner, cosine_coupling_kernel as cosine_kernel_owner,
    gaussian_bump_ic as gaussian_bump_owner, half_sync_half_random_ic as half_sync_owner,
    ring_indices, small_world_indices, CompatCoupling, CompatIntegrator, OscilloCompat,
    OscilloCompatConfig,
};
use prin_sim::y4q1_stats::{
    bootstrap_ci as bootstrap_owner, cohens_d as cohens_d_owner,
    spatial_correlation as spatial_corr_owner, welch_t_test as welch_owner,
};

fn value_error(error: impl core::fmt::Display) -> PyErr {
    PyValueError::new_err(error.to_string())
}

type RunOutput = (
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    f64,
    f64,
    Option<Vec<Vec<f64>>>,
);

/// Run a reference-faithful `OscilloSim` simulation.
///
/// `mode` must already be resolved (`"auto"` mapped by the Python caller) and be
/// one of ``mean_field`` / ``sparse_knn`` / ``csr`` / ``ring`` / ``small_world``;
/// `integrator` is ``euler`` or ``rk4``. `coupling_weights`, when given, is a
/// row-major ``(N, k)`` buffer. Returns
/// ``(final_phase, final_amplitude, order_parameter, wall_time_s, throughput,
/// trajectory_phase)``.
///
/// # Errors
///
/// Returns ``ValueError`` for an unknown mode/integrator string, an empty
/// population, a malformed weight or initial buffer, a non-positive ``dt``, or a
/// zero ``record_interval``.
#[pyfunction]
#[pyo3(signature = (
    n, coupling_strength, mode, k_neighbors, sparsity, mu, freq_mean, freq_std,
    phase_lag, p_rewire, integrator, seed, n_steps, dt, record_trajectory,
    record_interval, coupling_weights=None, initial_phase=None,
    initial_amplitude=None
))]
#[allow(clippy::too_many_arguments)]
fn oscillo_compat_run(
    n: usize,
    coupling_strength: f64,
    mode: &str,
    k_neighbors: usize,
    sparsity: f64,
    mu: f64,
    freq_mean: f64,
    freq_std: f64,
    phase_lag: f64,
    p_rewire: f64,
    integrator: &str,
    seed: u64,
    n_steps: usize,
    dt: f64,
    record_trajectory: bool,
    record_interval: usize,
    coupling_weights: Option<Vec<f64>>,
    initial_phase: Option<Vec<f64>>,
    initial_amplitude: Option<Vec<f64>>,
) -> PyResult<RunOutput> {
    let cfg = OscilloCompatConfig {
        n,
        coupling_strength,
        mode: CompatCoupling::parse(mode).map_err(value_error)?,
        k_neighbors,
        sparsity,
        mu,
        freq_mean,
        freq_std,
        phase_lag,
        p_rewire,
        integrator: CompatIntegrator::parse(integrator).map_err(value_error)?,
        coupling_weights,
        seed,
    };
    let sim = OscilloCompat::new(cfg).map_err(value_error)?;
    let out = sim
        .run(
            n_steps,
            dt,
            record_trajectory,
            record_interval,
            initial_phase,
            initial_amplitude,
        )
        .map_err(value_error)?;
    Ok((
        out.final_phase,
        out.final_amplitude,
        out.order_parameter,
        out.wall_time_s,
        out.throughput,
        out.trajectory_phase,
    ))
}

/// Row-major ``(N, k)`` ring-lattice neighbour indices.
///
/// # Errors
///
/// Returns ``ValueError`` when ``k`` is odd, ``k < 2``, or ``k >= N``.
#[pyfunction]
fn ring_topology_indices(n: usize, k: usize) -> PyResult<Vec<i64>> {
    ring_indices(n, k)
        .map(|v| v.into_iter().map(|x| x as i64).collect())
        .map_err(value_error)
}

/// Row-major ``(N, k)`` Watts–Strogatz small-world neighbour indices.
///
/// # Errors
///
/// Returns ``ValueError`` when ``k`` is odd, ``k < 2``, or ``k >= N``.
#[pyfunction]
fn small_world_topology_indices(
    n: usize,
    k: usize,
    p_rewire: f64,
    seed: u64,
) -> PyResult<Vec<i64>> {
    small_world_indices(n, k, p_rewire, seed)
        .map(|v| v.into_iter().map(|x| x as i64).collect())
        .map_err(value_error)
}

/// Length-``k`` normalised cosine coupling-kernel row (Abrams & Strogatz).
///
/// # Errors
///
/// Returns ``ValueError`` when ``k == 0``.
#[pyfunction]
fn cosine_coupling_kernel_row(n: usize, k: usize, a: f64) -> PyResult<Vec<f64>> {
    cosine_kernel_owner(n, k, a).map_err(value_error)
}

/// Single-humped chimera initial condition ``(N,)``.
#[pyfunction]
fn chimera_initial_condition(n: usize, seed: u64) -> Vec<f64> {
    chimera_ic_owner(n, seed)
}

/// Smooth Gaussian-bump initial condition ``(N,)`` wrapped to ``[0, 2π)``.
#[pyfunction]
#[pyo3(signature = (n, a0, sigma_ratio, phi0, noise_amp, seed))]
fn gaussian_bump_ic(
    n: usize,
    a0: f64,
    sigma_ratio: f64,
    phi0: f64,
    noise_amp: f64,
    seed: u64,
) -> Vec<f64> {
    gaussian_bump_owner(n, a0, sigma_ratio, phi0, noise_amp, seed)
}

/// Half-synchronised / half-random initial condition ``(N,)``.
#[pyfunction]
#[pyo3(signature = (n, sync_phase, noise_amp, seed))]
fn half_sync_half_random_ic(n: usize, sync_phase: f64, noise_amp: f64, seed: u64) -> Vec<f64> {
    half_sync_owner(n, sync_phase, noise_amp, seed)
}

/// Percentile bootstrap CI for the mean:
/// ``(mean, ci_lower, ci_upper, ci_width, se)``.
///
/// # Errors
///
/// Returns ``ValueError`` for empty ``values`` or ``n_bootstrap == 0``.
#[pyfunction]
#[pyo3(signature = (values, n_bootstrap=10_000, alpha=0.05, seed=42))]
fn y4q1_bootstrap_ci(
    values: Vec<f64>,
    n_bootstrap: usize,
    alpha: f64,
    seed: u64,
) -> PyResult<(f64, f64, f64, f64, f64)> {
    bootstrap_owner(&values, n_bootstrap, alpha, seed).map_err(value_error)
}

/// Cohen's ``d`` effect size (pooled standard deviation).
#[pyfunction]
fn y4q1_cohens_d(group_a: Vec<f64>, group_b: Vec<f64>) -> f64 {
    cohens_d_owner(&group_a, &group_b)
}

/// Welch's t-test: ``(t_stat, p_value, cohens_d, mean_diff)``.
///
/// # Errors
///
/// Returns ``ValueError`` when either group has fewer than two samples.
#[pyfunction]
fn y4q1_welch_t_test(group_a: Vec<f64>, group_b: Vec<f64>) -> PyResult<(f64, f64, f64, f64)> {
    welch_owner(&group_a, &group_b).map_err(value_error)
}

/// Spatial autocorrelation for lags ``0 ..= max_lag`` (clipped to ``N / 2``).
#[pyfunction]
#[pyo3(signature = (values, max_lag=50))]
fn y4q1_spatial_correlation(values: Vec<f64>, max_lag: usize) -> Vec<f64> {
    spatial_corr_owner(&values, max_lag)
}

/// Register the OscilloSim-compat and Year-4-Q1 owner functions.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(oscillo_compat_run, m)?)?;
    m.add_function(wrap_pyfunction!(ring_topology_indices, m)?)?;
    m.add_function(wrap_pyfunction!(small_world_topology_indices, m)?)?;
    m.add_function(wrap_pyfunction!(cosine_coupling_kernel_row, m)?)?;
    m.add_function(wrap_pyfunction!(chimera_initial_condition, m)?)?;
    m.add_function(wrap_pyfunction!(gaussian_bump_ic, m)?)?;
    m.add_function(wrap_pyfunction!(half_sync_half_random_ic, m)?)?;
    m.add_function(wrap_pyfunction!(y4q1_bootstrap_ci, m)?)?;
    m.add_function(wrap_pyfunction!(y4q1_cohens_d, m)?)?;
    m.add_function(wrap_pyfunction!(y4q1_welch_t_test, m)?)?;
    m.add_function(wrap_pyfunction!(y4q1_spatial_correlation, m)?)?;
    Ok(())
}

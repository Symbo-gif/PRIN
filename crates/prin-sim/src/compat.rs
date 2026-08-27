//! CPU compatibility helpers for the WP-036 0141C public surface.
//!
//! The functions in this module preserve the one-dimensional PRINet 3.0
//! compatibility formulas while delegating owned numerical work to the audited
//! Rust implementations in `prin-dynamics`, `prin-kernels`, `prin-metrics`, and
//! [`SparseCoupling`]. Every stochastic entry point requires an explicit
//! [`Seed`]; this module never creates hidden randomness.

use std::f64::consts::TAU;

use prin_dynamics::{
    create_band_state, delta_theta_gamma_network, integrate_fixed, BandError, BandParams,
    CouplingMode, IntegrateError, PhaseAmplitudeCoupling, RK4Integrator, Seed, StateError,
};
use prin_kernels::sparse_knn::{
    sparse_knn_derivatives_cpu, SparseKnnError, SparseKnnGraph, SparseKnnParams,
};
use prin_metrics::{kuramoto_order_parameter, MetricError};
use thiserror::Error;

use crate::{SimError, SparseCoupling};

/// Errors returned by the WP-036 compatibility helpers.
#[derive(Debug, Error)]
pub enum CompatError {
    /// A required slice or parameter grid is empty.
    #[error("`{name}` must not be empty")]
    EmptyInput {
        /// Name of the empty input.
        name: &'static str,
    },
    /// Two one-dimensional inputs have different lengths.
    #[error("length mismatch: `{name}` expected {expected}, got {got}")]
    LengthMismatch {
        /// Name of the offending input.
        name: &'static str,
        /// Required length.
        expected: usize,
        /// Actual length.
        got: usize,
    },
    /// A scalar or slice element is not finite.
    #[error("non-finite value in `{name}` at index {index}: {value}")]
    NonFiniteValue {
        /// Name of the offending input.
        name: &'static str,
        /// Element index, or zero for a scalar.
        index: usize,
        /// Offending value.
        value: f64,
    },
    /// A finite scalar lies outside its permitted range.
    #[error("invalid `{name}` value {value}: expected {expected}")]
    InvalidRange {
        /// Name of the offending parameter.
        name: &'static str,
        /// Offending value.
        value: f64,
        /// Human-readable permitted range.
        expected: &'static str,
    },
    /// The requested neighbor count is invalid for the population.
    #[error("invalid neighbor count k={k} for n={n}; expected 1 <= k < n")]
    InvalidNeighborCount {
        /// Population size.
        n: usize,
        /// Requested neighbors per oscillator.
        k: usize,
    },
    /// An arithmetic size computation overflowed.
    #[error("size overflow while computing `{name}`")]
    SizeOverflow {
        /// Name of the overflowing allocation or shape.
        name: &'static str,
    },
    /// A floating-point value cannot be represented by an owned f32 kernel.
    #[error("`{name}` value at index {index} is outside the finite f32 range: {value}")]
    F32Range {
        /// Name of the offending input.
        name: &'static str,
        /// Element index, or zero for a scalar.
        index: usize,
        /// Offending value.
        value: f64,
    },
    /// Error from `prin-sim`'s sparse coupling owner.
    #[error(transparent)]
    Simulation(#[from] SimError),
    /// Error from `prin-dynamics` state construction.
    #[error(transparent)]
    State(#[from] StateError),
    /// Error from `prin-dynamics` band construction.
    #[error(transparent)]
    Band(#[from] BandError),
    /// Error from `prin-dynamics` PAC construction.
    #[error(transparent)]
    Pac(#[from] prin_dynamics::PacError),
    /// Error from `prin-dynamics` integration.
    #[error(transparent)]
    Integration(#[from] IntegrateError),
    /// Error from `prin-metrics` order-parameter evaluation.
    #[error(transparent)]
    Metric(#[from] MetricError),
    /// Error from the authoritative sparse k-NN CPU kernel.
    #[error(transparent)]
    SparseKnn(#[from] SparseKnnError),
}

/// Winner-take-all mode used by [`phase_to_rate`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PhaseToRateMode {
    /// Temperature-scaled softmax of the instantaneous rates.
    Soft,
    /// Preserve only the largest `max(1, floor(N * sparsity))` rates.
    Hard,
    /// Blend soft and hard outputs with `sigmoid(1 / max(T, 1e-6) - 1)`.
    Annealed,
}

/// Owned CSR representation of a [`SparseCoupling`].
#[derive(Clone, Debug, PartialEq)]
pub struct CsrRepresentation {
    /// Square matrix dimension.
    pub n: usize,
    /// CSR row pointers, of length `n + 1`.
    pub indptr: Vec<usize>,
    /// CSR column indices, one per stored value.
    pub indices: Vec<usize>,
    /// CSR values, one per stored column index.
    pub data: Vec<f64>,
}

/// Validated random neighbor table returned by [`build_knn_neighbors`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KnnNeighbors {
    n: usize,
    k: usize,
    indices: Vec<usize>,
}

impl KnnNeighbors {
    /// Construct a validated flattened row-major neighbor table.
    ///
    /// # Errors
    ///
    /// Returns [`CompatError`] unless `n >= 2`, `1 <= k < n`, the flattened
    /// length is exactly `n * k`, and every index is in range and non-self.
    pub fn from_indices(n: usize, k: usize, indices: Vec<usize>) -> Result<Self, CompatError> {
        if n < 2 || k == 0 || k >= n {
            return Err(CompatError::InvalidNeighborCount { n, k });
        }
        let expected = n
            .checked_mul(k)
            .ok_or(CompatError::SizeOverflow { name: "neighbors" })?;
        if indices.len() != expected {
            return Err(CompatError::LengthMismatch {
                name: "neighbors",
                expected,
                got: indices.len(),
            });
        }
        for (row, values) in indices.chunks_exact(k).enumerate() {
            for (position, &index) in values.iter().enumerate() {
                if index >= n || index == row || values[..position].contains(&index) {
                    return Err(CompatError::InvalidRange {
                        name: "neighbor index",
                        value: index as f64,
                        expected: "an in-range, unique, non-self index per row",
                    });
                }
            }
        }
        Ok(Self { n, k, indices })
    }

    /// Population size represented by this table.
    pub fn n(&self) -> usize {
        self.n
    }

    /// Number of neighbors in every row.
    pub fn k(&self) -> usize {
        self.k
    }

    /// Flattened row-major neighbor indices, with shape `n × k`.
    pub fn indices(&self) -> &[usize] {
        &self.indices
    }

    /// Neighbor row for oscillator `i`.
    ///
    /// # Errors
    ///
    /// Returns [`CompatError::InvalidRange`] when `i >= n`.
    pub fn row(&self, i: usize) -> Result<&[usize], CompatError> {
        if i >= self.n {
            return Err(CompatError::InvalidRange {
                name: "row",
                value: i as f64,
                expected: "an index below n",
            });
        }
        Ok(&self.indices[i * self.k..(i + 1) * self.k])
    }
}

/// Configuration for [`sweep_coupling_params`].
#[derive(Clone, Debug, PartialEq)]
pub struct CouplingParamSweepConfig {
    /// Total requested oscillator count; each band receives
    /// `max(2, floor(n_oscillators / 3))` oscillators, matching the archive.
    pub n_oscillators: usize,
    /// Coupling strengths `K`, iterated in outer-loop order.
    pub k_values: Vec<f64>,
    /// PAC modulation depths `m`, iterated in inner-loop order.
    pub m_values: Vec<f64>,
    /// Number of RK4 integration steps per pair.
    pub n_steps: usize,
    /// Positive integration timestep.
    pub dt: f64,
}

/// Final per-band order parameters for one `(K, m)` sweep pair.
#[derive(Clone, Debug, PartialEq)]
pub struct CouplingParamSweepResult {
    /// Intra-band coupling strength.
    pub coupling_strength: f64,
    /// Delta→theta and theta→gamma PAC depth.
    pub pac_depth: f64,
    /// Final delta-band Kuramoto order parameter.
    pub r_delta: f64,
    /// Final theta-band Kuramoto order parameter.
    pub r_theta: f64,
    /// Final gamma-band Kuramoto order parameter.
    pub r_gamma: f64,
}

/// Convert one-dimensional phase/amplitude values to sparse rates.
///
/// First computes `r_i = amplitude_i * (1 + cos(phase_i)) / 2`, then applies
/// the archived soft, hard, or annealed winner-take-all rule.
///
/// # Errors
///
/// Returns [`CompatError`] for empty or mismatched inputs, non-finite values,
/// negative amplitudes, `sparsity` outside `[0, 1]`, or non-positive
/// `temperature`.
pub fn phase_to_rate(
    phase: &[f64],
    amplitude: &[f64],
    mode: PhaseToRateMode,
    sparsity: f64,
    temperature: f64,
) -> Result<Vec<f64>, CompatError> {
    validate_same_nonempty(phase, amplitude, "amplitude")?;
    validate_finite("phase", phase)?;
    validate_finite("amplitude", amplitude)?;
    if let Some(&value) = amplitude.iter().find(|&&value| value < 0.0) {
        return Err(CompatError::InvalidRange {
            name: "amplitude",
            value,
            expected: "non-negative values",
        });
    }
    validate_closed_unit("sparsity", sparsity)?;
    validate_positive("temperature", temperature)?;

    let instantaneous: Vec<f64> = phase
        .iter()
        .zip(amplitude)
        .map(|(&p, &a)| a * (1.0 + p.cos()) / 2.0)
        .collect();
    let active = ((instantaneous.len() as f64 * sparsity) as usize).max(1);

    match mode {
        PhaseToRateMode::Soft => Ok(softmax(&instantaneous, temperature)),
        PhaseToRateMode::Hard => Ok(hard_topk(&instantaneous, active)),
        PhaseToRateMode::Annealed => {
            let soft = softmax(&instantaneous, temperature);
            let hard = hard_topk(&instantaneous, active);
            let blend = sigmoid(1.0 / temperature.max(1e-6) - 1.0);
            Ok(soft
                .into_iter()
                .zip(hard)
                .map(|(s, h)| (1.0 - blend) * s + blend * h)
                .collect())
        }
    }
}

/// Build `k` random, unique, non-self neighbors for every oscillator.
///
/// Rows are sampled without replacement using an explicit deterministic
/// [`Seed`]. The output has flattened shape `n_oscillators × k`.
///
/// # Errors
///
/// Returns [`CompatError::InvalidNeighborCount`] unless
/// `n_oscillators >= 2` and `1 <= k < n_oscillators`, or
/// [`CompatError::SizeOverflow`] if the flattened shape overflows.
pub fn build_knn_neighbors(
    n_oscillators: usize,
    k: usize,
    mut seed: Seed,
) -> Result<KnnNeighbors, CompatError> {
    if n_oscillators < 2 || k == 0 || k >= n_oscillators {
        return Err(CompatError::InvalidNeighborCount {
            n: n_oscillators,
            k,
        });
    }
    let capacity = n_oscillators
        .checked_mul(k)
        .ok_or(CompatError::SizeOverflow { name: "neighbors" })?;
    let mut indices = Vec::with_capacity(capacity);
    for i in 0..n_oscillators {
        let mut candidates: Vec<usize> = (0..n_oscillators).filter(|&j| j != i).collect();
        for position in 0..k {
            let remaining = candidates.len() - position;
            let offset = (seed.next_f64() * remaining as f64) as usize;
            candidates.swap(position, position + offset);
        }
        indices.extend_from_slice(&candidates[..k]);
    }
    Ok(KnnNeighbors {
        n: n_oscillators,
        k,
        indices,
    })
}

/// Generate an archived-style random sparse coupling matrix.
///
/// An edge is retained when a uniform draw exceeds `sparsity`; retained
/// magnitudes are half-normal draws scaled by `coupling_strength / N`. The
/// diagonal is zero. In symmetric mode the upper-triangle mask is mirrored and
/// opposite-direction magnitudes are averaged, matching the archived dense and
/// CSR generators. Randomness comes only from the supplied [`Seed`].
///
/// # Errors
///
/// Returns [`CompatError`] for an empty population, `sparsity` outside
/// `[0, 1)`, a non-finite coupling strength, shape overflow, or sparse owner
/// construction failure.
pub fn sparse_coupling_matrix(
    n_oscillators: usize,
    sparsity: f64,
    coupling_strength: f64,
    symmetric: bool,
    mut seed: Seed,
) -> Result<SparseCoupling, CompatError> {
    if n_oscillators == 0 {
        return Err(SimError::EmptyPopulation { n: 0 }.into());
    }
    if !sparsity.is_finite() || !(0.0..1.0).contains(&sparsity) {
        return Err(CompatError::InvalidRange {
            name: "sparsity",
            value: sparsity,
            expected: "a finite value in [0, 1)",
        });
    }
    validate_finite_scalar("coupling_strength", coupling_strength)?;
    let len = n_oscillators
        .checked_mul(n_oscillators)
        .ok_or(CompatError::SizeOverflow {
            name: "coupling matrix",
        })?;

    let mask_draws: Vec<f64> = (0..len).map(|_| seed.next_f64()).collect();
    let mut magnitudes = Vec::with_capacity(len);
    while magnitudes.len() < len {
        let u1 = seed.next_f64().max(f64::MIN_POSITIVE);
        let u2 = seed.next_f64();
        let radius = (-2.0 * u1.ln()).sqrt();
        magnitudes.push((radius * (TAU * u2).cos()).abs());
        if magnitudes.len() < len {
            magnitudes.push((radius * (TAU * u2).sin()).abs());
        }
    }

    let scale = coupling_strength / n_oscillators as f64;
    let mut dense = vec![0.0; len];
    if symmetric {
        for i in 0..n_oscillators {
            for j in (i + 1)..n_oscillators {
                if mask_draws[i * n_oscillators + j] > sparsity {
                    let value = scale
                        * (magnitudes[i * n_oscillators + j] + magnitudes[j * n_oscillators + i])
                        / 2.0;
                    dense[i * n_oscillators + j] = value;
                    dense[j * n_oscillators + i] = value;
                }
            }
        }
    } else {
        for i in 0..n_oscillators {
            for j in 0..n_oscillators {
                if i != j && mask_draws[i * n_oscillators + j] > sparsity {
                    dense[i * n_oscillators + j] = scale * magnitudes[i * n_oscillators + j];
                }
            }
        }
    }
    Ok(SparseCoupling::from_dense(&dense, n_oscillators, 0.0)?)
}

/// Materialize a [`SparseCoupling`] as a dense row-major `N × N` vector.
pub fn coupling_to_dense(coupling: &SparseCoupling) -> Vec<f64> {
    let n = coupling.n_oscillators();
    let mut dense = vec![0.0; n * n];
    for (i, row) in coupling.as_csr().outer_iterator().enumerate() {
        for (j, &value) in row.iter() {
            dense[i * n + j] = value;
        }
    }
    dense
}

/// Copy a [`SparseCoupling`] into owned CSR arrays.
pub fn coupling_to_csr(coupling: &SparseCoupling) -> CsrRepresentation {
    let matrix = coupling.as_csr();
    CsrRepresentation {
        n: coupling.n_oscillators(),
        indptr: matrix.indptr().raw_storage().to_vec(),
        indices: matrix.indices().to_vec(),
        data: matrix.data().to_vec(),
    }
}

/// Compute the archived amplitude-one Kuramoto correction from CSR coupling.
///
/// Delegates to [`SparseCoupling::kuramoto_coupling`] with unit amplitudes and
/// returns its sine correction.
///
/// # Errors
///
/// Returns [`CompatError`] for a shape mismatch or non-finite phase.
pub fn csr_coupling_step(
    phase: &[f64],
    coupling: &SparseCoupling,
) -> Result<Vec<f64>, CompatError> {
    if phase.len() != coupling.n_oscillators() {
        return Err(CompatError::LengthMismatch {
            name: "phase",
            expected: coupling.n_oscillators(),
            got: phase.len(),
        });
    }
    validate_finite("phase", phase)?;
    let amplitudes = vec![1.0; phase.len()];
    Ok(coupling.kuramoto_coupling(phase, &amplitudes)?.0)
}

/// Compute the archived sparse k-NN phase correction.
///
/// The archived function accepts `amplitude` but its formula is exactly
/// `K/k * sum_j sin(phase_j - phase_i)` and does not use amplitude values.
/// This wrapper still validates the compatibility argument, then delegates that
/// phase correction to [`sparse_knn_derivatives_cpu`] with unit amplitudes,
/// zero frequencies, decay, and adaptation.
///
/// # Errors
///
/// Returns [`CompatError`] for shape, finiteness, f32-range, graph, or kernel
/// validation failures.
pub fn sparse_knn_coupling_step(
    phase: &[f64],
    amplitude: &[f64],
    neighbors: &KnnNeighbors,
    coupling_strength: f64,
) -> Result<Vec<f64>, CompatError> {
    validate_same_nonempty(phase, amplitude, "amplitude")?;
    if phase.len() != neighbors.n {
        return Err(CompatError::LengthMismatch {
            name: "neighbors",
            expected: phase.len(),
            got: neighbors.n,
        });
    }
    validate_finite("phase", phase)?;
    validate_finite("amplitude", amplitude)?;
    validate_finite_scalar("coupling_strength", coupling_strength)?;

    let phase32 = to_f32("phase", phase)?;
    let coupling32 = scalar_to_f32("coupling_strength", coupling_strength)?;
    let mut indptr = Vec::with_capacity(neighbors.n + 1);
    let mut indices = Vec::with_capacity(neighbors.indices.len());
    indptr.push(0u32);
    for row in neighbors.indices.chunks_exact(neighbors.k) {
        for &j in row {
            indices.push(u32::try_from(j).map_err(|_| CompatError::SizeOverflow {
                name: "neighbor index",
            })?);
        }
        indptr.push(
            u32::try_from(indices.len()).map_err(|_| CompatError::SizeOverflow {
                name: "neighbor edges",
            })?,
        );
    }
    let graph = SparseKnnGraph::from_csr(neighbors.n, indptr, indices)?;
    let ones = vec![1.0_f32; phase.len()];
    let zeros = vec![0.0_f32; phase.len()];
    let params = SparseKnnParams {
        k: coupling32,
        decay: 0.0,
        gamma: 0.0,
    };
    let (correction, _, _) = sparse_knn_derivatives_cpu(&phase32, &ones, &zeros, &graph, &params)?;
    Ok(correction.into_iter().map(f64::from).collect())
}

/// Sweep coupling strength `K` and PAC depth `m` through the audited
/// delta–theta–gamma dynamics owner.
///
/// Every grid point starts from an identical clone of the explicit [`Seed`],
/// matching the archived sweep's same-seed initial-state comparison. The Rust
/// owner is the continuous [`prin_dynamics::BandNetwork`] design adopted by
/// Project Plan amendment #19; RK4 integration and final order parameters are
/// delegated to `prin-dynamics` and `prin-metrics` respectively.
///
/// # Errors
///
/// Returns [`CompatError`] for an empty/invalid grid, invalid simulation
/// parameters, or delegated dynamics/integration/metric failures.
pub fn sweep_coupling_params(
    config: &CouplingParamSweepConfig,
    seed: Seed,
) -> Result<Vec<CouplingParamSweepResult>, CompatError> {
    validate_sweep_config(config)?;
    let n_per_band = (config.n_oscillators / 3).max(2);
    let capacity = config
        .k_values
        .len()
        .checked_mul(config.m_values.len())
        .ok_or(CompatError::SizeOverflow {
            name: "sweep result grid",
        })?;
    let mut results = Vec::with_capacity(capacity);

    for &coupling_strength in &config.k_values {
        for &pac_depth in &config.m_values {
            let band = BandParams::with_coupling(
                coupling_strength,
                0.1,
                0.01,
                CouplingMode::SparseKnn { k: None },
            )?;
            let network = delta_theta_gamma_network(
                n_per_band,
                n_per_band,
                n_per_band,
                band.clone(),
                band.clone(),
                band,
                PhaseAmplitudeCoupling::new(pac_depth)?,
                PhaseAmplitudeCoupling::new(pac_depth)?,
                0.0,
                0.0,
            )?;
            let mut point_seed = seed.clone();
            let state = create_band_state(
                &network,
                &[(1.0, 4.0), (4.0, 8.0), (30.0, 50.0)],
                &mut point_seed,
            )?;
            let mut integrator = RK4Integrator::new();
            let (final_state, _) = integrate_fixed(
                &mut integrator,
                &network,
                &state,
                config.n_steps,
                config.dt,
                false,
            )?;
            let delta_end = n_per_band;
            let theta_end = 2 * n_per_band;
            results.push(CouplingParamSweepResult {
                coupling_strength,
                pac_depth,
                r_delta: kuramoto_order_parameter(&final_state.phase[..delta_end])?,
                r_theta: kuramoto_order_parameter(&final_state.phase[delta_end..theta_end])?,
                r_gamma: kuramoto_order_parameter(&final_state.phase[theta_end..])?,
            });
        }
    }
    Ok(results)
}

fn validate_sweep_config(config: &CouplingParamSweepConfig) -> Result<(), CompatError> {
    if config.n_oscillators == 0 {
        return Err(SimError::EmptyPopulation { n: 0 }.into());
    }
    if config.k_values.is_empty() {
        return Err(CompatError::EmptyInput { name: "k_values" });
    }
    if config.m_values.is_empty() {
        return Err(CompatError::EmptyInput { name: "m_values" });
    }
    validate_finite("k_values", &config.k_values)?;
    for &value in &config.m_values {
        validate_closed_unit("m_values", value)?;
    }
    if config.n_steps == 0 {
        return Err(CompatError::InvalidRange {
            name: "n_steps",
            value: 0.0,
            expected: "a positive integer",
        });
    }
    validate_positive("dt", config.dt)
}

fn validate_same_nonempty(
    first: &[f64],
    second: &[f64],
    second_name: &'static str,
) -> Result<(), CompatError> {
    if first.is_empty() {
        return Err(CompatError::EmptyInput { name: "phase" });
    }
    if second.len() != first.len() {
        return Err(CompatError::LengthMismatch {
            name: second_name,
            expected: first.len(),
            got: second.len(),
        });
    }
    Ok(())
}

fn validate_finite(name: &'static str, values: &[f64]) -> Result<(), CompatError> {
    if let Some((index, &value)) = values
        .iter()
        .enumerate()
        .find(|(_, value)| !value.is_finite())
    {
        return Err(CompatError::NonFiniteValue { name, index, value });
    }
    Ok(())
}

fn validate_finite_scalar(name: &'static str, value: f64) -> Result<(), CompatError> {
    if !value.is_finite() {
        return Err(CompatError::NonFiniteValue {
            name,
            index: 0,
            value,
        });
    }
    Ok(())
}

fn validate_closed_unit(name: &'static str, value: f64) -> Result<(), CompatError> {
    if !value.is_finite() || !(0.0..=1.0).contains(&value) {
        return Err(CompatError::InvalidRange {
            name,
            value,
            expected: "a finite value in [0, 1]",
        });
    }
    Ok(())
}

fn validate_positive(name: &'static str, value: f64) -> Result<(), CompatError> {
    if !value.is_finite() || value <= 0.0 {
        return Err(CompatError::InvalidRange {
            name,
            value,
            expected: "a finite positive value",
        });
    }
    Ok(())
}

fn softmax(values: &[f64], temperature: f64) -> Vec<f64> {
    let max = values.iter().copied().fold(f64::NEG_INFINITY, f64::max) / temperature;
    let exp: Vec<f64> = values
        .iter()
        .map(|&value| (value / temperature - max).exp())
        .collect();
    let sum: f64 = exp.iter().sum();
    exp.into_iter().map(|value| value / sum).collect()
}

fn hard_topk(values: &[f64], k: usize) -> Vec<f64> {
    let mut order: Vec<usize> = (0..values.len()).collect();
    order.sort_unstable_by(|&left, &right| {
        values[right]
            .total_cmp(&values[left])
            .then_with(|| left.cmp(&right))
    });
    let mut output = vec![0.0; values.len()];
    for index in order.into_iter().take(k) {
        output[index] = values[index];
    }
    output
}

fn sigmoid(value: f64) -> f64 {
    if value >= 0.0 {
        1.0 / (1.0 + (-value).exp())
    } else {
        let exp = value.exp();
        exp / (1.0 + exp)
    }
}

fn to_f32(name: &'static str, values: &[f64]) -> Result<Vec<f32>, CompatError> {
    values
        .iter()
        .enumerate()
        .map(|(index, &value)| {
            let converted = value as f32;
            if converted.is_finite() {
                Ok(converted)
            } else {
                Err(CompatError::F32Range { name, index, value })
            }
        })
        .collect()
}

fn scalar_to_f32(name: &'static str, value: f64) -> Result<f32, CompatError> {
    to_f32(name, &[value]).map(|values| values[0])
}

#[cfg(test)]
mod tests {
    use std::collections::HashSet;
    use std::f64::consts::{FRAC_PI_2, PI};

    use approx::assert_relative_eq;

    use super::*;

    fn seed(key: u128) -> Seed {
        Seed::new(0, key)
    }

    fn sample_sweep() -> CouplingParamSweepConfig {
        CouplingParamSweepConfig {
            n_oscillators: 6,
            k_values: vec![0.5, 1.0],
            m_values: vec![0.1, 0.4],
            n_steps: 1,
            dt: 0.001,
        }
    }

    #[test]
    fn phase_to_rate_soft_matches_exact_formula() {
        let output = phase_to_rate(
            &[0.0, FRAC_PI_2, PI],
            &[2.0, 2.0, 2.0],
            PhaseToRateMode::Soft,
            0.1,
            1.0,
        )
        .unwrap();
        let raw = [2.0_f64, 1.0, 0.0];
        let denominator: f64 = raw.iter().map(|value| value.exp()).sum();
        for (actual, value) in output.iter().zip(raw) {
            assert_relative_eq!(*actual, value.exp() / denominator, epsilon = 1e-14);
        }
        assert_relative_eq!(output.iter().sum::<f64>(), 1.0, epsilon = 1e-14);
    }

    #[test]
    fn phase_to_rate_hard_and_annealed_match_archive() {
        let phase = [PI, FRAC_PI_2, 0.0, PI];
        let amplitude = [1.0; 4];
        let hard = phase_to_rate(&phase, &amplitude, PhaseToRateMode::Hard, 0.5, 2.0).unwrap();
        assert_eq!(hard, vec![0.0, 0.5, 1.0, 0.0]);

        let annealed =
            phase_to_rate(&phase, &amplitude, PhaseToRateMode::Annealed, 0.5, 2.0).unwrap();
        let soft = phase_to_rate(&phase, &amplitude, PhaseToRateMode::Soft, 0.5, 2.0).unwrap();
        let blend = sigmoid(-0.5);
        for i in 0..4 {
            assert_relative_eq!(annealed[i], (1.0 - blend) * soft[i] + blend * hard[i]);
        }

        let sharp = phase_to_rate(&phase, &amplitude, PhaseToRateMode::Annealed, 0.0, 0.5).unwrap();
        assert!(sharp.iter().all(|value| value.is_finite() && *value >= 0.0));
    }

    #[test]
    fn phase_to_rate_rejects_every_invalid_input_class() {
        assert!(matches!(
            phase_to_rate(&[], &[], PhaseToRateMode::Soft, 0.1, 1.0),
            Err(CompatError::EmptyInput { .. })
        ));
        assert!(matches!(
            phase_to_rate(&[0.0], &[], PhaseToRateMode::Soft, 0.1, 1.0),
            Err(CompatError::LengthMismatch { .. })
        ));
        assert!(matches!(
            phase_to_rate(&[f64::NAN], &[1.0], PhaseToRateMode::Soft, 0.1, 1.0),
            Err(CompatError::NonFiniteValue { .. })
        ));
        assert!(matches!(
            phase_to_rate(&[0.0], &[f64::INFINITY], PhaseToRateMode::Soft, 0.1, 1.0),
            Err(CompatError::NonFiniteValue { .. })
        ));
        assert!(matches!(
            phase_to_rate(&[0.0], &[-1.0], PhaseToRateMode::Soft, 0.1, 1.0),
            Err(CompatError::InvalidRange {
                name: "amplitude",
                ..
            })
        ));
        for sparsity in [-0.1, 1.1, f64::NAN] {
            assert!(matches!(
                phase_to_rate(&[0.0], &[1.0], PhaseToRateMode::Soft, sparsity, 1.0),
                Err(CompatError::InvalidRange {
                    name: "sparsity",
                    ..
                })
            ));
        }
        for temperature in [0.0, -1.0, f64::INFINITY] {
            assert!(matches!(
                phase_to_rate(&[0.0], &[1.0], PhaseToRateMode::Soft, 0.1, temperature),
                Err(CompatError::InvalidRange {
                    name: "temperature",
                    ..
                })
            ));
        }
    }

    #[test]
    fn knn_neighbors_are_seeded_unique_and_non_self() {
        let first = build_knn_neighbors(12, 4, seed(7)).unwrap();
        let same = build_knn_neighbors(12, 4, seed(7)).unwrap();
        let different = build_knn_neighbors(12, 4, seed(8)).unwrap();
        assert_eq!(first, same);
        assert_ne!(first, different);
        assert_eq!(first.n(), 12);
        assert_eq!(first.k(), 4);
        assert_eq!(first.indices().len(), 48);
        for i in 0..first.n() {
            let row = first.row(i).unwrap();
            assert!(!row.contains(&i));
            assert_eq!(row.iter().copied().collect::<HashSet<_>>().len(), first.k());
        }
        assert!(matches!(
            first.row(12),
            Err(CompatError::InvalidRange { .. })
        ));
    }

    #[test]
    fn knn_neighbors_from_indices_validates_rows() {
        let table = KnnNeighbors::from_indices(3, 2, vec![1, 2, 0, 2, 0, 1]).unwrap();
        assert_eq!(table.row(1).unwrap(), &[0, 2]);
        assert!(KnnNeighbors::from_indices(3, 2, vec![1, 1, 0, 2, 0, 1]).is_err());
        assert!(KnnNeighbors::from_indices(3, 2, vec![0, 2, 0, 2, 0, 1]).is_err());
        assert!(KnnNeighbors::from_indices(3, 2, vec![1, 3, 0, 2, 0, 1]).is_err());
        assert!(KnnNeighbors::from_indices(3, 2, vec![1, 2]).is_err());
    }

    #[test]
    fn knn_neighbors_reject_invalid_counts_and_overflow() {
        for (n, k) in [(0, 1), (1, 1), (4, 0), (4, 4)] {
            assert!(matches!(
                build_knn_neighbors(n, k, seed(1)),
                Err(CompatError::InvalidNeighborCount { .. })
            ));
        }
        assert!(matches!(
            build_knn_neighbors(usize::MAX, 2, seed(1)),
            Err(CompatError::SizeOverflow { .. })
        ));
    }

    #[test]
    fn sparse_matrix_is_deterministic_symmetric_and_convertible() {
        let first = sparse_coupling_matrix(8, 0.25, 2.0, true, seed(42)).unwrap();
        let same = sparse_coupling_matrix(8, 0.25, 2.0, true, seed(42)).unwrap();
        let different = sparse_coupling_matrix(8, 0.25, 2.0, true, seed(43)).unwrap();
        let dense = coupling_to_dense(&first);
        assert_eq!(dense, coupling_to_dense(&same));
        assert_ne!(dense, coupling_to_dense(&different));
        for i in 0..8 {
            assert_eq!(dense[i * 8 + i], 0.0);
            for j in 0..8 {
                assert_eq!(dense[i * 8 + j], dense[j * 8 + i]);
                assert!(dense[i * 8 + j] >= 0.0);
            }
        }
        let csr = coupling_to_csr(&first);
        assert_eq!(csr.n, 8);
        assert_eq!(csr.indptr.len(), 9);
        assert_eq!(csr.indices.len(), csr.data.len());
        assert_eq!(csr.data.len(), first.nnz());
        let rebuilt =
            SparseCoupling::from_csr(&csr.indptr, &csr.indices, &csr.data, csr.n).unwrap();
        assert_eq!(coupling_to_dense(&rebuilt), dense);
    }

    #[test]
    fn sparse_matrix_directed_zero_and_singleton_paths() {
        let directed = sparse_coupling_matrix(7, 0.0, -1.0, false, seed(9)).unwrap();
        let dense = coupling_to_dense(&directed);
        assert!(dense.iter().any(|&value| value < 0.0));
        assert!((0..7).all(|i| dense[i * 7 + i] == 0.0));
        assert!(dense.chunks_exact(7).enumerate().any(|(i, row)| row
            .iter()
            .enumerate()
            .any(|(j, &v)| i != j && v != dense[j * 7 + i])));

        let zero = sparse_coupling_matrix(3, 0.0, 0.0, false, seed(9)).unwrap();
        assert_eq!(zero.nnz(), 0);
        let singleton = sparse_coupling_matrix(1, 0.5, 1.0, true, seed(9)).unwrap();
        assert_eq!(coupling_to_dense(&singleton), vec![0.0]);
    }

    #[test]
    fn sparse_matrix_rejects_invalid_inputs_and_overflow() {
        assert!(matches!(
            sparse_coupling_matrix(0, 0.5, 1.0, true, seed(1)),
            Err(CompatError::Simulation(SimError::EmptyPopulation { .. }))
        ));
        for sparsity in [-0.1, 1.0, f64::NAN] {
            assert!(matches!(
                sparse_coupling_matrix(2, sparsity, 1.0, true, seed(1)),
                Err(CompatError::InvalidRange {
                    name: "sparsity",
                    ..
                })
            ));
        }
        assert!(matches!(
            sparse_coupling_matrix(2, 0.5, f64::NAN, true, seed(1)),
            Err(CompatError::NonFiniteValue { .. })
        ));
        assert!(matches!(
            sparse_coupling_matrix(usize::MAX, 0.5, 1.0, true, seed(1)),
            Err(CompatError::SizeOverflow { .. })
        ));
    }

    #[test]
    fn csr_coupling_step_matches_closed_form() {
        let coupling =
            SparseCoupling::from_dense(&[0.0, 2.0, 0.0, 3.0, 0.0, 4.0, 5.0, 0.0, 0.0], 3, 0.0)
                .unwrap();
        let phase = [0.0, FRAC_PI_2, PI];
        let actual = csr_coupling_step(&phase, &coupling).unwrap();
        let expected = [2.0, 3.0 * (-FRAC_PI_2).sin() + 4.0 * FRAC_PI_2.sin(), 0.0];
        for (a, e) in actual.iter().zip(expected) {
            assert_relative_eq!(*a, e, epsilon = 1e-12);
        }
        assert!(matches!(
            csr_coupling_step(&phase[..2], &coupling),
            Err(CompatError::LengthMismatch { .. })
        ));
        assert!(matches!(
            csr_coupling_step(&[0.0, f64::NAN, 0.0], &coupling),
            Err(CompatError::NonFiniteValue { .. })
        ));
    }

    #[test]
    fn sparse_knn_step_matches_archived_phase_only_formula() {
        let neighbors = KnnNeighbors {
            n: 3,
            k: 2,
            indices: vec![1, 2, 0, 2, 0, 1],
        };
        let phase = [0.0, FRAC_PI_2, PI];
        let first = sparse_knn_coupling_step(&phase, &[1.0, 2.0, 3.0], &neighbors, 2.0).unwrap();
        let second = sparse_knn_coupling_step(&phase, &[9.0, 8.0, 7.0], &neighbors, 2.0).unwrap();
        assert_eq!(
            first, second,
            "archived compatibility amplitude is intentionally unused"
        );
        let expected = [1.0, 0.0, -1.0];
        for (actual, expected) in first.iter().zip(expected) {
            assert_relative_eq!(*actual, expected, epsilon = 2e-7);
        }
    }

    #[test]
    fn sparse_knn_step_rejects_boundary_errors() {
        let neighbors = build_knn_neighbors(3, 1, seed(2)).unwrap();
        assert!(matches!(
            sparse_knn_coupling_step(&[], &[], &neighbors, 1.0),
            Err(CompatError::EmptyInput { .. })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0], &[], &neighbors, 1.0),
            Err(CompatError::LengthMismatch {
                name: "amplitude",
                ..
            })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0], &[1.0], &neighbors, 1.0),
            Err(CompatError::LengthMismatch {
                name: "neighbors",
                ..
            })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0, f64::NAN, 1.0], &[1.0; 3], &neighbors, 1.0),
            Err(CompatError::NonFiniteValue { name: "phase", .. })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0; 3], &[1.0, f64::NAN, 1.0], &neighbors, 1.0),
            Err(CompatError::NonFiniteValue {
                name: "amplitude",
                ..
            })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0; 3], &[1.0; 3], &neighbors, f64::INFINITY),
            Err(CompatError::NonFiniteValue { .. })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[f64::MAX; 3], &[1.0; 3], &neighbors, 1.0),
            Err(CompatError::F32Range { name: "phase", .. })
        ));
        assert!(matches!(
            sparse_knn_coupling_step(&[0.0; 3], &[1.0; 3], &neighbors, f64::MAX),
            Err(CompatError::F32Range {
                name: "coupling_strength",
                ..
            })
        ));
    }

    #[test]
    fn coupling_param_sweep_has_order_shape_ranges_and_seed_determinism() {
        let config = sample_sweep();
        let first = sweep_coupling_params(&config, seed(100)).unwrap();
        let same = sweep_coupling_params(&config, seed(100)).unwrap();
        let different = sweep_coupling_params(&config, seed(101)).unwrap();
        assert_eq!(first, same);
        assert_ne!(first, different);
        assert_eq!(first.len(), 4);
        assert_eq!(
            first
                .iter()
                .map(|result| (result.coupling_strength, result.pac_depth))
                .collect::<Vec<_>>(),
            vec![(0.5, 0.1), (0.5, 0.4), (1.0, 0.1), (1.0, 0.4)]
        );
        for result in first {
            assert!((0.0..=1.0).contains(&result.r_delta));
            assert!((0.0..=1.0).contains(&result.r_theta));
            assert!((0.0..=1.0).contains(&result.r_gamma));
        }
    }

    #[test]
    fn coupling_param_sweep_rejects_invalid_configuration() {
        let mut config = sample_sweep();
        config.n_oscillators = 0;
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::Simulation(SimError::EmptyPopulation { .. }))
        ));
        config = sample_sweep();
        config.k_values.clear();
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::EmptyInput { name: "k_values" })
        ));
        config = sample_sweep();
        config.m_values.clear();
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::EmptyInput { name: "m_values" })
        ));
        config = sample_sweep();
        config.k_values[0] = f64::NAN;
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::NonFiniteValue {
                name: "k_values",
                ..
            })
        ));
        config = sample_sweep();
        config.m_values[0] = 1.1;
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::InvalidRange {
                name: "m_values",
                ..
            })
        ));
        config = sample_sweep();
        config.n_steps = 0;
        assert!(matches!(
            sweep_coupling_params(&config, seed(1)),
            Err(CompatError::InvalidRange {
                name: "n_steps",
                ..
            })
        ));
        for dt in [0.0, f64::NAN] {
            config = sample_sweep();
            config.dt = dt;
            assert!(matches!(
                sweep_coupling_params(&config, seed(1)),
                Err(CompatError::InvalidRange { name: "dt", .. })
            ));
        }
    }
}

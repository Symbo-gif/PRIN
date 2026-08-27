//! PRINet 3.0 CPU-reference compatibility kernels.
//!
//! These functions preserve the archived PyTorch fallback formulas while
//! providing validated, typed Rust boundaries. State and arithmetic use `f32`;
//! reductions reuse the crate's authoritative helpers where the formulas are
//! mathematically identical.

use thiserror::Error;

use crate::mean_field_rk4::{
    mean_field_derivatives_into, order_param, step_cpu, wrap_phase, MeanFieldRk4Params,
};

/// Three-vector output used by the compatibility integration functions.
pub type CompatStateOutput = (Vec<f32>, Vec<f32>, Vec<f32>);

/// Two-vector output used by the dense discrete compatibility functions.
pub type CompatDiscreteOutput = (Vec<f32>, Vec<f32>);

/// Shared Kuramoto/Stuart–Landau parameters for compatibility integration.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CompatDynamicsParams {
    /// Coupling strength `K`.
    pub k: f32,
    /// Linear amplitude decay rate.
    pub decay: f32,
    /// Frequency-adaptation rate.
    pub gamma: f32,
}

/// Parameters for the dense three-band discrete compatibility functions.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct DenseDiscreteParams {
    /// Stuart–Landau growth parameter for delta, theta, and gamma.
    pub mu: [f32; 3],
    /// Positive integration timestep.
    pub dt: f32,
    /// Minimum output amplitude, inclusive.
    pub amp_min: f32,
    /// Maximum output amplitude, inclusive.
    pub amp_max: f32,
}

/// Errors returned by PRINet 3.0 compatibility kernels.
#[derive(Debug, Error)]
pub enum CompatError {
    /// Slices that describe the same population have different lengths.
    #[error("length mismatch for {name}: expected {expected}, got {got}")]
    LengthMismatch {
        /// Logical input group.
        name: &'static str,
        /// Required length.
        expected: usize,
        /// Actual length.
        got: usize,
    },
    /// A required input population is empty.
    #[error("{name} must be non-empty")]
    EmptyInput {
        /// Empty input name.
        name: &'static str,
    },
    /// An input or parameter contains a non-finite value.
    #[error("non-finite value in {name} at index {index}: {value}")]
    NonFinite {
        /// Input or parameter name.
        name: &'static str,
        /// Offending flat index.
        index: usize,
        /// Offending value.
        value: f32,
    },
    /// A frequency-band label is not delta, theta, or gamma.
    #[error("invalid band label at index {index}: {label} (expected 0, 1, or 2)")]
    InvalidBandLabel {
        /// Offending label index.
        index: usize,
        /// Offending label.
        label: u8,
    },
    /// A parent index does not address the slow population.
    #[error("parent index at position {position} is {index}, but slow length is {len}")]
    IndexOutOfBounds {
        /// Position in the parent-index array.
        position: usize,
        /// Offending parent index.
        index: usize,
        /// Slow population length.
        len: usize,
    },
    /// A matrix, batch, or band dimension is inconsistent.
    #[error("dimension mismatch for {name}: expected {expected}, got {got}")]
    DimensionMismatch {
        /// Input whose dimensions are invalid.
        name: &'static str,
        /// Required flattened element count.
        expected: usize,
        /// Actual flattened element count.
        got: usize,
    },
    /// A scalar parameter violates its range contract.
    #[error("invalid parameter {name}: {value}")]
    InvalidParameter {
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f32,
    },
    /// One or more sub-step counts are zero.
    #[error("sub-step count for band {band} must be positive")]
    InvalidSubsteps {
        /// Band index, or zero for a uniform sub-step count.
        band: usize,
    },
    /// The amplitude clamp bounds are non-finite or inverted.
    #[error("invalid amplitude clamp [{min}, {max}]")]
    InvalidClampRange {
        /// Clamp minimum.
        min: f32,
        /// Clamp maximum.
        max: f32,
    },
    /// An internal size calculation overflowed `usize`.
    #[error("dimension overflow while validating {name}")]
    DimensionOverflow {
        /// Dimension being calculated.
        name: &'static str,
    },
    /// The reused authoritative mean-field step rejected its parameters.
    #[error("mean-field compatibility step failed: {0}")]
    MeanField(#[from] crate::mean_field_rk4::MeanFieldRk4Error),
}

fn require_nonempty(name: &'static str, values: &[f32]) -> Result<(), CompatError> {
    if values.is_empty() {
        Err(CompatError::EmptyInput { name })
    } else {
        Ok(())
    }
}

fn finite_slice(name: &'static str, values: &[f32]) -> Result<(), CompatError> {
    if let Some((index, &value)) = values
        .iter()
        .enumerate()
        .find(|(_, value)| !value.is_finite())
    {
        return Err(CompatError::NonFinite { name, index, value });
    }
    Ok(())
}

fn finite_scalar(name: &'static str, value: f32) -> Result<(), CompatError> {
    if value.is_finite() {
        Ok(())
    } else {
        Err(CompatError::NonFinite {
            name,
            index: 0,
            value,
        })
    }
}

fn validate_dynamics(params: &CompatDynamicsParams) -> Result<(), CompatError> {
    finite_scalar("k", params.k)?;
    finite_scalar("decay", params.decay)?;
    finite_scalar("gamma", params.gamma)
}

fn validate_state(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
) -> Result<usize, CompatError> {
    require_nonempty("phase", phase)?;
    for (name, values) in [("amplitude", amplitude), ("frequency", frequency)] {
        if values.len() != phase.len() {
            return Err(CompatError::LengthMismatch {
                name,
                expected: phase.len(),
                got: values.len(),
            });
        }
    }
    finite_slice("phase", phase)?;
    finite_slice("amplitude", amplitude)?;
    finite_slice("frequency", frequency)?;
    Ok(phase.len())
}

fn validate_labels(labels: &[u8], n: usize) -> Result<(), CompatError> {
    if labels.len() != n {
        return Err(CompatError::LengthMismatch {
            name: "freq_band",
            expected: n,
            got: labels.len(),
        });
    }
    if let Some((index, &label)) = labels.iter().enumerate().find(|(_, label)| **label > 2) {
        return Err(CompatError::InvalidBandLabel { index, label });
    }
    Ok(())
}

fn validate_clamp(min: f32, max: f32) -> Result<(), CompatError> {
    if !min.is_finite() || !max.is_finite() || min > max {
        Err(CompatError::InvalidClampRange { min, max })
    } else {
        Ok(())
    }
}

/// Compute the unweighted Kuramoto order-parameter magnitude for each band.
///
/// `phase` is a concatenation of bands in the order described by `band_sizes`.
/// Each reduction evaluates `|mean(exp(i * phase))|` with `f64` accumulation,
/// matching the PRINet 3.0 fallback's explicit float64 complex conversion.
///
/// # Errors
///
/// Returns [`CompatError`] for empty inputs/bands, non-finite phases, a zero
/// band size, an overflowing size sum, or a sum that differs from `phase.len()`.
pub fn hierarchical_order_parameter_cpu(
    phase: &[f32],
    band_sizes: &[usize],
) -> Result<Vec<f32>, CompatError> {
    require_nonempty("phase", phase)?;
    finite_slice("phase", phase)?;
    if band_sizes.is_empty() {
        return Err(CompatError::EmptyInput { name: "band_sizes" });
    }
    let mut offset = 0usize;
    let mut output = Vec::with_capacity(band_sizes.len());
    for (band, &size) in band_sizes.iter().enumerate() {
        if size == 0 {
            return Err(CompatError::InvalidSubsteps { band });
        }
        let end = offset
            .checked_add(size)
            .ok_or(CompatError::DimensionOverflow { name: "band_sizes" })?;
        if end > phase.len() {
            return Err(CompatError::DimensionMismatch {
                name: "band_sizes",
                expected: end,
                got: phase.len(),
            });
        }
        let (mut real, mut imag) = (0.0_f64, 0.0_f64);
        for &p in &phase[offset..end] {
            let (sin, cos) = f64::from(p).sin_cos();
            real += cos;
            imag += sin;
        }
        let scale = 1.0 / size as f64;
        output.push(((real * scale).hypot(imag * scale)) as f32);
        offset = end;
    }
    if offset != phase.len() {
        return Err(CompatError::DimensionMismatch {
            name: "band_sizes",
            expected: offset,
            got: phase.len(),
        });
    }
    Ok(output)
}

fn all_pairs_derivatives(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &CompatDynamicsParams,
) -> CompatStateOutput {
    let n = phase.len();
    let n_inv = 1.0 / n as f32;
    let mut dphase = Vec::with_capacity(n);
    let mut damp = Vec::with_capacity(n);
    let mut dfreq = Vec::with_capacity(n);
    for i in 0..n {
        let mut sin_sum = 0.0_f32;
        let mut cos_sum = 0.0_f32;
        for j in 0..n {
            let (sin, cos) = (phase[j] - phase[i]).sin_cos();
            sin_sum += sin;
            cos_sum += cos;
        }
        let sin_mean = sin_sum * n_inv;
        let cos_mean = cos_sum * n_inv;
        dphase.push(frequency[i] + params.k * sin_mean);
        damp.push(-params.decay * amplitude[i] + params.k * cos_mean);
        dfreq.push(params.gamma * sin_mean * n_inv);
    }
    (dphase, damp, dfreq)
}

fn single_all_pairs_rk4(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &CompatDynamicsParams,
    dt: f32,
) -> CompatStateOutput {
    let n = phase.len();
    let (k1p, k1a, k1f) = all_pairs_derivatives(phase, amplitude, frequency, params);
    let stage = |kp: &[f32], ka: &[f32], kf: &[f32], scale: f32| {
        let mut p = Vec::with_capacity(n);
        let mut a = Vec::with_capacity(n);
        let mut f = Vec::with_capacity(n);
        for i in 0..n {
            p.push(wrap_phase(phase[i] + scale * kp[i]));
            a.push((amplitude[i] + scale * ka[i]).max(0.0));
            f.push(frequency[i] + scale * kf[i]);
        }
        (p, a, f)
    };
    let (p2, a2, f2) = stage(&k1p, &k1a, &k1f, 0.5 * dt);
    let (k2p, k2a, k2f) = all_pairs_derivatives(&p2, &a2, &f2, params);
    let (p3, a3, f3) = stage(&k2p, &k2a, &k2f, 0.5 * dt);
    let (k3p, k3a, k3f) = all_pairs_derivatives(&p3, &a3, &f3, params);
    let (p4, a4, f4) = stage(&k3p, &k3a, &k3f, dt);
    let (k4p, k4a, k4f) = all_pairs_derivatives(&p4, &a4, &f4, params);
    let sixth = dt / 6.0;
    let mut out = (
        Vec::with_capacity(n),
        Vec::with_capacity(n),
        Vec::with_capacity(n),
    );
    for i in 0..n {
        out.0.push(wrap_phase(
            phase[i] + sixth * (k1p[i] + 2.0 * k2p[i] + 2.0 * k3p[i] + k4p[i]),
        ));
        out.1.push(
            (amplitude[i] + sixth * (k1a[i] + 2.0 * k2a[i] + 2.0 * k3a[i] + k4a[i])).max(0.0),
        );
        out.2
            .push(frequency[i] + sixth * (k1f[i] + 2.0 * k2f[i] + 2.0 * k3f[i] + k4f[i]));
    }
    out
}

/// Perform repeated inner RK4 steps within one outer timestep.
///
/// When `mean_field` is true, this delegates each inner step to the crate's
/// authoritative [`step_cpu`]. When false, it applies the archived all-pairs
/// fallback, including its `1/N` pair averages and frequency adaptation.
///
/// # Errors
///
/// Returns [`CompatError`] for invalid state, non-finite parameters, non-positive
/// `dt`, or zero `sub_steps`.
pub fn multi_rate_rk4_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &CompatDynamicsParams,
    dt: f32,
    sub_steps: usize,
    mean_field: bool,
) -> Result<CompatStateOutput, CompatError> {
    validate_state(phase, amplitude, frequency)?;
    validate_dynamics(params)?;
    finite_scalar("dt", dt)?;
    if dt <= 0.0 {
        return Err(CompatError::InvalidParameter {
            name: "dt",
            value: dt,
        });
    }
    if sub_steps == 0 {
        return Err(CompatError::InvalidSubsteps { band: 0 });
    }
    let inner_dt = dt / sub_steps as f32;
    let (mut p, mut a, mut f) = (phase.to_vec(), amplitude.to_vec(), frequency.to_vec());
    for _ in 0..sub_steps {
        if mean_field {
            (p, a, f) = step_cpu(
                &p,
                &a,
                &f,
                &MeanFieldRk4Params {
                    k: params.k,
                    decay: params.decay,
                    gamma: params.gamma,
                    dt: inner_dt,
                },
            )?;
        } else {
            (p, a, f) = single_all_pairs_rk4(&p, &a, &f, params, inner_dt);
        }
    }
    Ok((p, a, f))
}

/// Compute global mean-field derivatives using band-selected frequencies.
///
/// `frequency` is validated for compatibility with the historical signature;
/// as in PRINet 3.0, derivative `dphase` uses `band_frequencies[freq_band[i]]`
/// instead of that base-frequency value.
///
/// # Errors
///
/// Returns [`CompatError`] for invalid state, labels, parameters, or band
/// frequencies.
pub fn multi_rate_derivatives_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    freq_band: &[u8],
    params: &CompatDynamicsParams,
    band_frequencies: [f32; 3],
) -> Result<CompatStateOutput, CompatError> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_labels(freq_band, n)?;
    validate_dynamics(params)?;
    finite_slice("band_frequencies", &band_frequencies)?;
    let selected: Vec<f32> = freq_band
        .iter()
        .map(|&band| band_frequencies[usize::from(band)])
        .collect();
    let mut output = (
        Vec::with_capacity(n),
        Vec::with_capacity(n),
        Vec::with_capacity(n),
    );
    mean_field_derivatives_into(
        phase,
        amplitude,
        &selected,
        &MeanFieldRk4Params {
            k: params.k,
            decay: params.decay,
            gamma: params.gamma,
            dt: 1.0,
        },
        1.0 / n as f32,
        &mut output.0,
        &mut output.1,
        &mut output.2,
    );
    Ok(output)
}

#[allow(clippy::too_many_arguments)]
fn frozen_order_derivatives(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &CompatDynamicsParams,
    order: (f32, f32),
    n_inv: f32,
) -> CompatStateOutput {
    let mut output = (
        Vec::with_capacity(phase.len()),
        Vec::with_capacity(phase.len()),
        Vec::with_capacity(phase.len()),
    );
    for i in 0..phase.len() {
        let (sin, cos) = phase[i].sin_cos();
        let r_sin = order.1 * cos - order.0 * sin;
        let r_cos = order.0 * cos + order.1 * sin;
        output.0.push(frequency[i] + params.k * r_sin);
        output
            .1
            .push(-params.decay * amplitude[i] + params.k * r_cos);
        output.2.push(params.gamma * params.k * r_sin * n_inv);
    }
    output
}

/// Apply fused per-band-count RK4 sub-stepping with a global mean field.
///
/// The global order parameter is recomputed once per fused sub-step and frozen
/// across that sub-step's four RK stages, exactly as in the PRINet 3.0 CPU
/// fallback. A band is active for the first `sub_steps_per_band[band]` passes.
///
/// # Errors
///
/// Returns [`CompatError`] for invalid state, labels, parameters, non-positive
/// timestep, or a zero per-band sub-step count.
pub fn fused_sub_step_rk4_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    freq_band: &[u8],
    params: &CompatDynamicsParams,
    dt: f32,
    sub_steps_per_band: [usize; 3],
) -> Result<CompatStateOutput, CompatError> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_labels(freq_band, n)?;
    validate_dynamics(params)?;
    finite_scalar("dt", dt)?;
    if dt <= 0.0 {
        return Err(CompatError::InvalidParameter {
            name: "dt",
            value: dt,
        });
    }
    for (band, &count) in sub_steps_per_band.iter().enumerate() {
        if count == 0 {
            return Err(CompatError::InvalidSubsteps { band });
        }
    }
    let max_sub = *sub_steps_per_band.iter().max().unwrap_or(&0);
    let inner_dt: Vec<f32> = freq_band
        .iter()
        .map(|&band| dt / sub_steps_per_band[usize::from(band)] as f32)
        .collect();
    let n_inv = 1.0 / n as f32;
    let (mut p, mut a, mut f) = (phase.to_vec(), amplitude.to_vec(), frequency.to_vec());
    for step in 0..max_sub {
        let order = order_param(&p, &a, n_inv);
        let (k1p, k1a, k1f) = frozen_order_derivatives(&p, &a, &f, params, order, n_inv);
        let stage = |kp: &[f32], ka: &[f32], kf: &[f32], factor: f32| {
            let mut state = (
                Vec::with_capacity(n),
                Vec::with_capacity(n),
                Vec::with_capacity(n),
            );
            for i in 0..n {
                let scale = factor * inner_dt[i];
                state.0.push(wrap_phase(p[i] + scale * kp[i]));
                state.1.push((a[i] + scale * ka[i]).max(0.0));
                state.2.push(f[i] + scale * kf[i]);
            }
            state
        };
        let (p2, a2, f2) = stage(&k1p, &k1a, &k1f, 0.5);
        let (k2p, k2a, k2f) = frozen_order_derivatives(&p2, &a2, &f2, params, order, n_inv);
        let (p3, a3, f3) = stage(&k2p, &k2a, &k2f, 0.5);
        let (k3p, k3a, k3f) = frozen_order_derivatives(&p3, &a3, &f3, params, order, n_inv);
        let (p4, a4, f4) = stage(&k3p, &k3a, &k3f, 1.0);
        let (k4p, k4a, k4f) = frozen_order_derivatives(&p4, &a4, &f4, params, order, n_inv);
        for i in 0..n {
            if step < sub_steps_per_band[usize::from(freq_band[i])] {
                let sixth = inner_dt[i] / 6.0;
                p[i] = wrap_phase(p[i] + sixth * (k1p[i] + 2.0 * k2p[i] + 2.0 * k3p[i] + k4p[i]));
                a[i] = (a[i] + sixth * (k1a[i] + 2.0 * k2a[i] + 2.0 * k3a[i] + k4a[i])).max(0.0);
                f[i] += sixth * (k1f[i] + 2.0 * k2f[i] + 2.0 * k3f[i] + k4f[i]);
            }
        }
    }
    Ok((p, a, f))
}

/// Modulate fast amplitudes using an explicit slow-parent index per oscillator.
///
/// The returned tuple is `(modulated_amplitude, unchanged_fast_phase)`, with
/// `A_i' = clamp(A_i * (1 + m*cos(parent_phase-fast_phase_i)), amp_min, amp_max)`.
///
/// # Errors
///
/// Returns [`CompatError`] for empty/mismatched/non-finite inputs, invalid
/// parent indices, modulation depth outside `[0, 1]`, or invalid clamp bounds.
pub fn cross_band_coupling_cpu(
    slow_phase: &[f32],
    fast_phase: &[f32],
    fast_amplitude: &[f32],
    parent_idx: &[usize],
    modulation_depth: f32,
    amp_min: f32,
    amp_max: f32,
) -> Result<(Vec<f32>, Vec<f32>), CompatError> {
    require_nonempty("slow_phase", slow_phase)?;
    require_nonempty("fast_phase", fast_phase)?;
    for (name, values) in [("fast_amplitude", fast_amplitude)] {
        if values.len() != fast_phase.len() {
            return Err(CompatError::LengthMismatch {
                name,
                expected: fast_phase.len(),
                got: values.len(),
            });
        }
    }
    if parent_idx.len() != fast_phase.len() {
        return Err(CompatError::LengthMismatch {
            name: "parent_idx",
            expected: fast_phase.len(),
            got: parent_idx.len(),
        });
    }
    finite_slice("slow_phase", slow_phase)?;
    finite_slice("fast_phase", fast_phase)?;
    finite_slice("fast_amplitude", fast_amplitude)?;
    finite_scalar("modulation_depth", modulation_depth)?;
    if !(0.0..=1.0).contains(&modulation_depth) {
        return Err(CompatError::InvalidParameter {
            name: "modulation_depth",
            value: modulation_depth,
        });
    }
    validate_clamp(amp_min, amp_max)?;
    let mut output = Vec::with_capacity(fast_phase.len());
    for (position, (&parent, (&phase, &amplitude))) in parent_idx
        .iter()
        .zip(fast_phase.iter().zip(fast_amplitude))
        .enumerate()
    {
        let parent_phase = *slow_phase
            .get(parent)
            .ok_or(CompatError::IndexOutOfBounds {
                position,
                index: parent,
                len: slow_phase.len(),
            })?;
        output.push(
            (amplitude * (1.0 + modulation_depth * (parent_phase - phase).cos()))
                .clamp(amp_min, amp_max),
        );
    }
    Ok((output, fast_phase.to_vec()))
}

fn validate_dense<'a>(
    phase: &[f32],
    amplitude: &[f32],
    batch_size: usize,
    frequencies: [&'a [f32]; 3],
    weights: [&'a [f32]; 3],
    band_sizes: [usize; 3],
    params: &DenseDiscreteParams,
) -> Result<usize, CompatError> {
    if batch_size == 0 {
        return Err(CompatError::EmptyInput { name: "batch" });
    }
    for (band, &size) in band_sizes.iter().enumerate() {
        if size == 0 {
            return Err(CompatError::InvalidSubsteps { band });
        }
    }
    let n = band_sizes
        .iter()
        .try_fold(0usize, |sum, &size| sum.checked_add(size))
        .ok_or(CompatError::DimensionOverflow { name: "band_sizes" })?;
    let expected_state = batch_size
        .checked_mul(n)
        .ok_or(CompatError::DimensionOverflow { name: "batch_size" })?;
    for (name, values) in [("phase", phase), ("amplitude", amplitude)] {
        if values.len() != expected_state {
            return Err(CompatError::DimensionMismatch {
                name,
                expected: expected_state,
                got: values.len(),
            });
        }
        finite_slice(name, values)?;
    }
    for band in 0..3 {
        if frequencies[band].len() != band_sizes[band] {
            return Err(CompatError::DimensionMismatch {
                name: "frequency",
                expected: band_sizes[band],
                got: frequencies[band].len(),
            });
        }
        let matrix_len = band_sizes[band]
            .checked_mul(band_sizes[band])
            .ok_or(CompatError::DimensionOverflow { name: "weight" })?;
        if weights[band].len() != matrix_len {
            return Err(CompatError::DimensionMismatch {
                name: "weight",
                expected: matrix_len,
                got: weights[band].len(),
            });
        }
        finite_slice("frequency", frequencies[band])?;
        finite_slice("weight", weights[band])?;
        finite_scalar("mu", params.mu[band])?;
    }
    finite_scalar("dt", params.dt)?;
    if params.dt <= 0.0 {
        return Err(CompatError::InvalidParameter {
            name: "dt",
            value: params.dt,
        });
    }
    validate_clamp(params.amp_min, params.amp_max)?;
    Ok(n)
}

fn dense_base_step(
    phase: &[f32],
    amplitude: &[f32],
    batch_size: usize,
    frequencies: [&[f32]; 3],
    weights: [&[f32]; 3],
    band_sizes: [usize; 3],
    params: &DenseDiscreteParams,
) -> CompatDiscreteOutput {
    let n: usize = band_sizes.iter().sum();
    let mut out_phase = vec![0.0; phase.len()];
    let mut out_amp = vec![0.0; amplitude.len()];
    let mut offset = 0;
    for band in 0..3 {
        let size = band_sizes[band];
        for batch in 0..batch_size {
            let base = batch * n + offset;
            for i in 0..size {
                let mut coupling = 0.0_f32;
                for j in 0..size {
                    coupling +=
                        weights[band][i * size + j] * (phase[base + j] - phase[base + i]).sin();
                }
                out_phase[base + i] = wrap_phase(
                    phase[base + i]
                        + core::f32::consts::TAU * frequencies[band][i] * params.dt
                        + params.dt * coupling,
                );
                let a = amplitude[base + i];
                out_amp[base + i] = (a + params.dt * a * (params.mu[band] - a * a))
                    .clamp(params.amp_min, params.amp_max);
            }
        }
        offset += size;
    }
    (out_phase, out_amp)
}

/// Execute the dense PRINet 3.0 fused discrete fallback on flattened batches.
///
/// `phase` and `amplitude` use row-major `(batch_size, sum(band_sizes))`
/// storage. Frequencies are per-band vectors and weights are row-major square
/// per-band matrices. Coupling uses `sum_j W[i,j] * sin(phase[j]-phase[i])`.
///
/// # Errors
///
/// Returns [`CompatError`] for invalid batch/band dimensions, non-finite data,
/// non-positive `dt`, or invalid amplitude clamps.
pub fn fused_discrete_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    batch_size: usize,
    frequencies: [&[f32]; 3],
    weights: [&[f32]; 3],
    band_sizes: [usize; 3],
    params: &DenseDiscreteParams,
) -> Result<CompatDiscreteOutput, CompatError> {
    validate_dense(
        phase,
        amplitude,
        batch_size,
        frequencies,
        weights,
        band_sizes,
        params,
    )?;
    Ok(dense_base_step(
        phase,
        amplitude,
        batch_size,
        frequencies,
        weights,
        band_sizes,
        params,
    ))
}

fn sigmoid(value: f32) -> f32 {
    if value >= 0.0 {
        1.0 / (1.0 + (-value).exp())
    } else {
        let exp = value.exp();
        exp / (1.0 + exp)
    }
}

/// Execute the full dense fallback with learned sigmoid PAC projections.
///
/// PAC matrices are row-major with shapes `(n_theta, 2*n_delta)` and
/// `(n_gamma, 2*n_theta)`; each representation concatenates all cosine values
/// followed by all sine values of the newly advanced slow-band phase. PAC gates
/// multiply theta/gamma amplitudes before their Stuart–Landau updates.
///
/// # Errors
///
/// Returns [`CompatError`] for any base-step validation error or invalid PAC
/// matrix/bias dimensions and values.
#[allow(clippy::too_many_arguments)]
pub fn fused_discrete_step_full_cpu(
    phase: &[f32],
    amplitude: &[f32],
    batch_size: usize,
    frequencies: [&[f32]; 3],
    weights: [&[f32]; 3],
    pac_weights: [&[f32]; 2],
    pac_biases: [&[f32]; 2],
    band_sizes: [usize; 3],
    params: &DenseDiscreteParams,
) -> Result<CompatDiscreteOutput, CompatError> {
    let n = validate_dense(
        phase,
        amplitude,
        batch_size,
        frequencies,
        weights,
        band_sizes,
        params,
    )?;
    for pair in 0..2 {
        let expected_weight = band_sizes[pair + 1]
            .checked_mul(2)
            .and_then(|value| value.checked_mul(band_sizes[pair]))
            .ok_or(CompatError::DimensionOverflow { name: "pac_weight" })?;
        if pac_weights[pair].len() != expected_weight {
            return Err(CompatError::DimensionMismatch {
                name: "pac_weight",
                expected: expected_weight,
                got: pac_weights[pair].len(),
            });
        }
        if pac_biases[pair].len() != band_sizes[pair + 1] {
            return Err(CompatError::DimensionMismatch {
                name: "pac_bias",
                expected: band_sizes[pair + 1],
                got: pac_biases[pair].len(),
            });
        }
        finite_slice("pac_weight", pac_weights[pair])?;
        finite_slice("pac_bias", pac_biases[pair])?;
    }
    let (new_phase, mut new_amp) = dense_base_step(
        phase,
        amplitude,
        batch_size,
        frequencies,
        weights,
        band_sizes,
        params,
    );
    let offsets = [0, band_sizes[0], band_sizes[0] + band_sizes[1]];
    for pair in 0..2 {
        let slow_size = band_sizes[pair];
        let fast_size = band_sizes[pair + 1];
        for batch in 0..batch_size {
            let slow_base = batch * n + offsets[pair];
            let fast_base = batch * n + offsets[pair + 1];
            for fast in 0..fast_size {
                let row = &pac_weights[pair][fast * 2 * slow_size..(fast + 1) * 2 * slow_size];
                let mut projection = pac_biases[pair][fast];
                for slow in 0..slow_size {
                    projection += row[slow] * new_phase[slow_base + slow].cos();
                    projection += row[slow_size + slow] * new_phase[slow_base + slow].sin();
                }
                let gated = amplitude[fast_base + fast] * sigmoid(projection);
                new_amp[fast_base + fast] = (gated
                    + params.dt * gated * (params.mu[pair + 1] - gated * gated))
                    .clamp(params.amp_min, params.amp_max);
            }
        }
    }
    Ok((new_phase, new_amp))
}

#[cfg(test)]
mod tests {
    use super::*;

    const DYNAMICS: CompatDynamicsParams = CompatDynamicsParams {
        k: 0.7,
        decay: 0.1,
        gamma: 0.02,
    };

    const DENSE: DenseDiscreteParams = DenseDiscreteParams {
        mu: [0.2, 0.3, 0.4],
        dt: 0.01,
        amp_min: 1e-6,
        amp_max: 10.0,
    };

    fn assert_close(actual: &[f32], expected: &[f32], epsilon: f32) {
        assert_eq!(actual.len(), expected.len());
        for (a, e) in actual.iter().zip(expected) {
            assert!((a - e).abs() <= epsilon, "{a} != {e}");
        }
    }

    #[test]
    fn hierarchical_matches_archived_formula() {
        let phase = [0.0, core::f32::consts::PI, 0.2, 0.2];
        let output = hierarchical_order_parameter_cpu(&phase, &[2, 2]).unwrap();
        assert!(output[0] < 1e-7);
        assert!((output[1] - 1.0).abs() < 1e-6);
    }

    #[test]
    fn multi_rate_mean_field_reuses_repeated_authority_steps() {
        let state = ([0.1, 1.0], [1.0, 0.8], [0.2, -0.1]);
        let actual =
            multi_rate_rk4_step_cpu(&state.0, &state.1, &state.2, &DYNAMICS, 0.02, 2, true)
                .unwrap();
        let p = MeanFieldRk4Params {
            k: 0.7,
            decay: 0.1,
            gamma: 0.02,
            dt: 0.01,
        };
        let first = step_cpu(&state.0, &state.1, &state.2, &p).unwrap();
        let expected = step_cpu(&first.0, &first.1, &first.2, &p).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn all_pairs_zero_coupling_has_archived_closed_form() {
        let output = multi_rate_rk4_step_cpu(
            &[0.1],
            &[1.0],
            &[0.25],
            &CompatDynamicsParams {
                k: 0.0,
                decay: 0.0,
                gamma: 0.0,
            },
            0.2,
            1,
            false,
        )
        .unwrap();
        assert_close(&output.0, &[0.15], 1e-6);
        assert_eq!(output.1, vec![1.0]);
        assert_eq!(output.2, vec![0.25]);
    }

    #[test]
    fn derivatives_override_base_frequency_and_match_identity() {
        let output = multi_rate_derivatives_cpu(
            &[0.0, 0.0, 0.0],
            &[1.0; 3],
            &[99.0; 3],
            &[0, 1, 2],
            &CompatDynamicsParams {
                k: 0.0,
                decay: 0.5,
                gamma: 0.0,
            },
            [2.0, 6.0, 40.0],
        )
        .unwrap();
        assert_eq!(output.0, vec![2.0, 6.0, 40.0]);
        assert_eq!(output.1, vec![-0.5; 3]);
        assert_eq!(output.2, vec![0.0; 3]);
    }

    #[test]
    fn fused_sub_step_is_deterministic_and_preserves_invariants() {
        let args = (
            &[0.1, 1.2, 2.3][..],
            &[1.0, 0.8, 1.2][..],
            &[0.2, 0.4, 0.6][..],
        );
        let a = fused_sub_step_rk4_cpu(
            args.0,
            args.1,
            args.2,
            &[0, 1, 2],
            &DYNAMICS,
            0.02,
            [1, 2, 3],
        )
        .unwrap();
        let b = fused_sub_step_rk4_cpu(
            args.0,
            args.1,
            args.2,
            &[0, 1, 2],
            &DYNAMICS,
            0.02,
            [1, 2, 3],
        )
        .unwrap();
        assert_eq!(a, b);
        assert!(a
            .0
            .iter()
            .all(|p| (0.0..core::f32::consts::TAU).contains(p)));
        assert!(a.1.iter().all(|value| value.is_finite() && *value >= 0.0));
        assert!(a.2.iter().all(|value| value.is_finite()));
    }

    #[test]
    fn cross_band_matches_archived_formula_and_clamps() {
        let output = cross_band_coupling_cpu(
            &[0.0, core::f32::consts::PI],
            &[0.0, 0.0],
            &[2.0, 2.0],
            &[0, 1],
            0.5,
            1.5,
            2.5,
        )
        .unwrap();
        assert_close(&output.0, &[2.5, 1.5], 1e-6);
        assert_eq!(output.1, vec![0.0, 0.0]);
    }

    type DenseTestInputs = (Vec<f32>, Vec<f32>, [Vec<f32>; 3], [Vec<f32>; 3], [usize; 3]);

    fn dense_inputs() -> DenseTestInputs {
        (
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0, 0.8, 1.2, 0.7],
            [vec![2.0], vec![6.0], vec![40.0, 41.0]],
            [vec![0.0], vec![0.0], vec![0.0, 0.2, 0.3, 0.0]],
            [1, 1, 2],
        )
    }

    #[test]
    fn dense_step_matches_direct_archived_formula() {
        let (phase, amp, freq, weight, sizes) = dense_inputs();
        let freq_ref = [&freq[0][..], &freq[1][..], &freq[2][..]];
        let weight_ref = [&weight[0][..], &weight[1][..], &weight[2][..]];
        let output =
            fused_discrete_step_cpu(&phase, &amp, 1, freq_ref, weight_ref, sizes, &DENSE).unwrap();
        let expected_p0 = wrap_phase(phase[0] + core::f32::consts::TAU * 2.0 * 0.01);
        let expected_a0 = 1.0 + 0.01 * (0.2 - 1.0);
        assert_close(&output.0[..1], &[expected_p0], 1e-6);
        assert_close(&output.1[..1], &[expected_a0], 1e-6);
    }

    #[test]
    fn full_step_zero_projection_uses_half_sigmoid_gate() {
        let (phase, amp, freq, weight, sizes) = dense_inputs();
        let pac_w = [vec![0.0; 2], vec![0.0; 4]];
        let pac_b = [vec![0.0], vec![0.0; 2]];
        let output = fused_discrete_step_full_cpu(
            &phase,
            &amp,
            1,
            [&freq[0], &freq[1], &freq[2]],
            [&weight[0], &weight[1], &weight[2]],
            [&pac_w[0], &pac_w[1]],
            [&pac_b[0], &pac_b[1]],
            sizes,
            &DENSE,
        )
        .unwrap();
        let gated = amp[1] * 0.5;
        let expected = gated + DENSE.dt * gated * (DENSE.mu[1] - gated * gated);
        assert_close(&output.1[1..2], &[expected], 1e-6);
        assert_eq!(
            output,
            fused_discrete_step_full_cpu(
                &phase,
                &amp,
                1,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &weight[2]],
                [&pac_w[0], &pac_w[1]],
                [&pac_b[0], &pac_b[1]],
                sizes,
                &DENSE,
            )
            .unwrap()
        );
    }

    #[test]
    fn validation_errors_cover_public_boundaries() {
        assert!(matches!(
            hierarchical_order_parameter_cpu(&[], &[1]),
            Err(CompatError::EmptyInput { .. })
        ));
        assert!(matches!(
            hierarchical_order_parameter_cpu(&[0.0], &[]),
            Err(CompatError::EmptyInput { .. })
        ));
        assert!(matches!(
            hierarchical_order_parameter_cpu(&[0.0], &[0]),
            Err(CompatError::InvalidSubsteps { .. })
        ));
        assert!(matches!(
            hierarchical_order_parameter_cpu(&[0.0], &[2]),
            Err(CompatError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            hierarchical_order_parameter_cpu(&[0.0, 1.0], &[1]),
            Err(CompatError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            multi_rate_rk4_step_cpu(&[0.0], &[], &[0.0], &DYNAMICS, 0.1, 1, true),
            Err(CompatError::LengthMismatch { .. })
        ));
        assert!(matches!(
            multi_rate_rk4_step_cpu(&[0.0], &[1.0], &[0.0], &DYNAMICS, 0.0, 1, true),
            Err(CompatError::InvalidParameter { .. })
        ));
        assert!(matches!(
            multi_rate_rk4_step_cpu(&[0.0], &[1.0], &[0.0], &DYNAMICS, 0.1, 0, true),
            Err(CompatError::InvalidSubsteps { .. })
        ));
        assert!(matches!(
            multi_rate_derivatives_cpu(&[0.0], &[1.0], &[0.0], &[3], &DYNAMICS, [2.0, 6.0, 40.0]),
            Err(CompatError::InvalidBandLabel { .. })
        ));
        assert!(matches!(
            fused_sub_step_rk4_cpu(&[0.0], &[1.0], &[0.0], &[0], &DYNAMICS, 0.1, [1, 0, 1]),
            Err(CompatError::InvalidSubsteps { band: 1 })
        ));
        assert!(matches!(
            cross_band_coupling_cpu(&[0.0], &[0.0], &[1.0], &[1], 0.3, 0.0, 1.0),
            Err(CompatError::IndexOutOfBounds { .. })
        ));
        assert!(matches!(
            cross_band_coupling_cpu(&[0.0], &[0.0], &[1.0], &[0], 1.1, 0.0, 1.0),
            Err(CompatError::InvalidParameter { .. })
        ));
        assert!(matches!(
            cross_band_coupling_cpu(&[0.0], &[0.0], &[1.0], &[0], 0.3, 2.0, 1.0),
            Err(CompatError::InvalidClampRange { .. })
        ));
    }

    #[test]
    fn dense_validation_rejects_dimensions_and_nonfinite_values() {
        let (phase, amp, freq, weight, sizes) = dense_inputs();
        assert!(matches!(
            fused_discrete_step_cpu(
                &phase,
                &amp,
                0,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &weight[2]],
                sizes,
                &DENSE
            ),
            Err(CompatError::EmptyInput { .. })
        ));
        assert!(matches!(
            fused_discrete_step_cpu(
                &phase[..3],
                &amp,
                1,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &weight[2]],
                sizes,
                &DENSE
            ),
            Err(CompatError::DimensionMismatch { .. })
        ));
        let bad_weight = [0.0];
        assert!(matches!(
            fused_discrete_step_cpu(
                &phase,
                &amp,
                1,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &bad_weight],
                sizes,
                &DENSE
            ),
            Err(CompatError::DimensionMismatch { .. })
        ));
        let mut bad = DENSE;
        bad.dt = f32::NAN;
        assert!(matches!(
            fused_discrete_step_cpu(
                &phase,
                &amp,
                1,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &weight[2]],
                sizes,
                &bad
            ),
            Err(CompatError::NonFinite { .. })
        ));
        let pac_w = [vec![0.0; 1], vec![0.0; 4]];
        let pac_b = [vec![0.0], vec![0.0; 2]];
        assert!(matches!(
            fused_discrete_step_full_cpu(
                &phase,
                &amp,
                1,
                [&freq[0], &freq[1], &freq[2]],
                [&weight[0], &weight[1], &weight[2]],
                [&pac_w[0], &pac_w[1]],
                [&pac_b[0], &pac_b[1]],
                sizes,
                &DENSE
            ),
            Err(CompatError::DimensionMismatch {
                name: "pac_weight",
                ..
            })
        ));
    }
}

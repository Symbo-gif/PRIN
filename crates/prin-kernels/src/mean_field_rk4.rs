//! Mean-field Kuramoto RK4 step: a CPU reference and a single-source CubeCL
//! kernel set for CUDA, wgpu, and CPU-SIMD backends.
//!
//! The CPU implementation in [`step_cpu`] is the numerical authority. The CubeCL
//! path in [`cubecl`] (enabled by the `cuda` or `wgpu` features) uses the same
//! algorithm and is checked against the CPU reference in kernel-equivalence
//! tests.

use thiserror::Error;

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
pub mod cubecl;

/// Parameters for the mean-field Kuramoto step.
///
/// PRINet 3.0 uses `K` for coupling strength, `decay` (lambda) for amplitude
/// damping, `gamma` for frequency adaptation, and `dt` for the timestep.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct MeanFieldRk4Params {
    /// Coupling strength `K`.
    pub k: f32,
    /// Amplitude decay rate `lambda`.
    pub decay: f32,
    /// Frequency adaptation rate `gamma`.
    pub gamma: f32,
    /// Timestep `dt`.
    pub dt: f32,
}

/// Output of a mean-field RK4 step: updated `(phase, amplitude, frequency)`.
pub type MeanFieldRk4Output = (Vec<f32>, Vec<f32>, Vec<f32>);

/// Errors raised by the mean-field RK4 kernels.
#[derive(Debug, Error)]
pub enum MeanFieldRk4Error {
    /// Input buffers have inconsistent lengths.
    #[error("input length mismatch: phase={phase}, amplitude={amp}, frequency={freq}")]
    LengthMismatch {
        /// Phase buffer length.
        phase: usize,
        /// Amplitude buffer length.
        amp: usize,
        /// Frequency buffer length.
        freq: usize,
    },
    /// Empty oscillator population.
    #[error("oscillator population is empty")]
    EmptyPopulation,
    /// Non-finite parameter value.
    #[error("non-finite parameter: {name} = {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// Invalid parameter value.
    #[error("invalid parameter: {name} = {value}")]
    InvalidParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// Device backend read-back failed.
    #[error("device backend read-back failed")]
    BackendReadError,
}

/// Wrap `phase` to `[0, 2 * pi)` using Euclidean remainder.
fn wrap_phase(phase: f32) -> f32 {
    phase.rem_euclid(core::f32::consts::TAU)
}

/// Clamp amplitude to `>= 0.0`.
fn clamp_amp(amp: f32) -> f32 {
    amp.max(0.0)
}

/// Validate that the three state buffers have the same length.
fn validate_state(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
) -> Result<usize, MeanFieldRk4Error> {
    if phase.len() != amplitude.len() || phase.len() != frequency.len() {
        return Err(MeanFieldRk4Error::LengthMismatch {
            phase: phase.len(),
            amp: amplitude.len(),
            freq: frequency.len(),
        });
    }
    if phase.is_empty() {
        return Err(MeanFieldRk4Error::EmptyPopulation);
    }
    Ok(phase.len())
}

/// Validate that a scalar parameter is finite and, when requested, strictly
/// positive.
fn validate_param(
    name: &'static str,
    value: f32,
    must_be_positive: bool,
) -> Result<(), MeanFieldRk4Error> {
    if !value.is_finite() {
        return Err(MeanFieldRk4Error::NonFiniteParameter { name, value });
    }
    if must_be_positive && value <= 0.0 {
        return Err(MeanFieldRk4Error::InvalidParameter { name, value });
    }
    Ok(())
}

/// Compute the mean-field order parameter `Z = (1/N) * sum(amp * e^{i*phase})`.
///
/// Returns `(Re(Z), Im(Z))` without using an explicit `atan2`, matching the
/// algebraic identity in PRINet 3.0's Triton kernel.
fn order_param(phase: &[f32], amplitude: &[f32], n_inv: f32) -> (f32, f32) {
    let mut z_real = 0.0_f32;
    let mut z_imag = 0.0_f32;
    for (p, a) in phase.iter().zip(amplitude) {
        let (s, c) = p.sin_cos();
        z_real += *a * c;
        z_imag += *a * s;
    }
    (z_real * n_inv, z_imag * n_inv)
}

/// Compute the mean-field Kuramoto derivatives at the given state.
///
/// The output is `(dphi, dr, domega)`.
fn mean_field_derivatives(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
    n_inv: f32,
) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    let (zx, zy) = order_param(phase, amplitude, n_inv);

    let mut dphi = Vec::with_capacity(phase.len());
    let mut dr = Vec::with_capacity(phase.len());
    let mut domega = Vec::with_capacity(phase.len());

    for (p, a, f) in phase
        .iter()
        .zip(amplitude.iter())
        .zip(frequency.iter())
        .map(|((p, a), f)| (p, a, f))
    {
        let (s, c) = p.sin_cos();
        let r_sin = zy * c - zx * s;
        let r_cos = zx * c + zy * s;
        dphi.push(f + params.k * r_sin);
        dr.push(-params.decay * a + params.k * r_cos);
        domega.push(params.gamma * params.k * r_sin * n_inv);
    }

    (dphi, dr, domega)
}

/// One fourth-order Runge-Kutta step for the mean-field Kuramoto model.
///
/// This is the CPU reference path. It matches the PRINet 3.0 PyTorch fallback
/// `pytorch_mean_field_rk4_step` (phase wrap to `[0, 2pi)` and amplitude clamp
/// `>= 0` at each RK stage and the final weighted sum).
///
/// # Arguments
///
/// * `phase` - Current phase angles in radians, shape `(N,)`.
/// * `amplitude` - Current amplitudes, shape `(N,)`.
/// * `frequency` - Natural frequencies, shape `(N,)`.
/// * `params` - Model parameters.
///
/// # Returns
///
/// Updated `(phase, amplitude, frequency)` after one RK4 step.
///
/// # Errors
///
/// Returns [`MeanFieldRk4Error`] on invalid inputs or parameters.
pub fn step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<MeanFieldRk4Output, MeanFieldRk4Error> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_param("k", params.k, false)?;
    validate_param("decay", params.decay, false)?;
    validate_param("gamma", params.gamma, false)?;
    validate_param("dt", params.dt, true)?;

    let n_inv = 1.0 / n as f32;
    let half_dt = params.dt * 0.5;
    let sixth_dt = params.dt / 6.0;

    // k1 = f(state)
    let (k1_p, k1_a, k1_f) = mean_field_derivatives(phase, amplitude, frequency, params, n_inv);

    // k2 = f(state + 0.5 * dt * k1)
    let mut s2_p = Vec::with_capacity(n);
    let mut s2_a = Vec::with_capacity(n);
    let mut s2_f = Vec::with_capacity(n);
    for i in 0..n {
        s2_p.push(wrap_phase(phase[i] + half_dt * k1_p[i]));
        s2_a.push(clamp_amp(amplitude[i] + half_dt * k1_a[i]));
        s2_f.push(frequency[i] + half_dt * k1_f[i]);
    }
    let (k2_p, k2_a, k2_f) = mean_field_derivatives(&s2_p, &s2_a, &s2_f, params, n_inv);

    // k3 = f(state + 0.5 * dt * k2)
    let mut s3_p = Vec::with_capacity(n);
    let mut s3_a = Vec::with_capacity(n);
    let mut s3_f = Vec::with_capacity(n);
    for i in 0..n {
        s3_p.push(wrap_phase(phase[i] + half_dt * k2_p[i]));
        s3_a.push(clamp_amp(amplitude[i] + half_dt * k2_a[i]));
        s3_f.push(frequency[i] + half_dt * k2_f[i]);
    }
    let (k3_p, k3_a, k3_f) = mean_field_derivatives(&s3_p, &s3_a, &s3_f, params, n_inv);

    // k4 = f(state + dt * k3)
    let mut s4_p = Vec::with_capacity(n);
    let mut s4_a = Vec::with_capacity(n);
    let mut s4_f = Vec::with_capacity(n);
    for i in 0..n {
        s4_p.push(wrap_phase(phase[i] + params.dt * k3_p[i]));
        s4_a.push(clamp_amp(amplitude[i] + params.dt * k3_a[i]));
        s4_f.push(frequency[i] + params.dt * k3_f[i]);
    }
    let (k4_p, k4_a, k4_f) = mean_field_derivatives(&s4_p, &s4_a, &s4_f, params, n_inv);

    // Final weighted sum.
    let mut out_p = Vec::with_capacity(n);
    let mut out_a = Vec::with_capacity(n);
    let mut out_f = Vec::with_capacity(n);
    for i in 0..n {
        let new_p =
            wrap_phase(phase[i] + sixth_dt * (k1_p[i] + 2.0 * k2_p[i] + 2.0 * k3_p[i] + k4_p[i]));
        let new_a = clamp_amp(
            amplitude[i] + sixth_dt * (k1_a[i] + 2.0 * k2_a[i] + 2.0 * k3_a[i] + k4_a[i]),
        );
        let new_f = frequency[i] + sixth_dt * (k1_f[i] + 2.0 * k2_f[i] + 2.0 * k3_f[i] + k4_f[i]);
        out_p.push(new_p);
        out_a.push(new_a);
        out_f.push(new_f);
    }

    Ok((out_p, out_a, out_f))
}

#[cfg(test)]
mod tests {
    use super::*;

    const DEFAULT_PARAMS: MeanFieldRk4Params = MeanFieldRk4Params {
        k: 2.0,
        decay: 0.1,
        gamma: 0.01,
        dt: 0.01,
    };

    #[test]
    fn cpu_step_perserves_invariants_for_small_n() {
        let phase = vec![0.1_f32, 1.2, 2.3, 3.4, 4.5];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.5_f32, -0.5, 0.2, -0.2, 0.0];

        let (out_p, out_a, out_f) = step_cpu(&phase, &amp, &freq, &DEFAULT_PARAMS).unwrap();

        assert_eq!(out_p.len(), 5);
        assert_eq!(out_a.len(), 5);
        assert_eq!(out_f.len(), 5);

        for p in &out_p {
            assert!(*p >= 0.0);
            assert!(*p < core::f32::consts::TAU);
        }
        for a in &out_a {
            assert!(*a >= 0.0);
            assert!(a.is_finite());
        }
    }

    #[test]
    fn cpu_step_zero_coupling_is_free_run() {
        let mut params = DEFAULT_PARAMS;
        params.k = 0.0;
        let n = 8;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amp = vec![1.0_f32; n];
        let freq: Vec<_> = (0..n).map(|i| 0.1 * (i as f32 - 3.5)).collect();

        let (out_p, out_a, out_f) = step_cpu(&phase, &amp, &freq, &params).unwrap();

        for i in 0..n {
            assert!((out_p[i] - wrap_phase(phase[i] + params.dt * freq[i])).abs() < 1e-6);
            assert!((out_a[i] - (amp[i] * (1.0 - params.decay * params.dt)).max(0.0)).abs() < 1e-6);
            assert!((out_f[i] - freq[i]).abs() < 1e-6);
        }
    }

    #[test]
    fn cpu_step_rejects_mismatched_lengths() {
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let err = step_cpu(&phase, &amp, &freq, &DEFAULT_PARAMS).unwrap_err();
        assert!(matches!(err, MeanFieldRk4Error::LengthMismatch { .. }));
    }

    #[test]
    fn cpu_step_rejects_empty() {
        let phase: Vec<f32> = vec![];
        let err = step_cpu(&phase, &phase, &phase, &DEFAULT_PARAMS).unwrap_err();
        assert!(matches!(err, MeanFieldRk4Error::EmptyPopulation));
    }

    #[test]
    fn cpu_step_rejects_non_finite_dt() {
        let mut params = DEFAULT_PARAMS;
        params.dt = f32::NAN;
        let err = step_cpu(&[0.0], &[1.0], &[0.0], &params).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::NonFiniteParameter { name: "dt", .. }
        ));
    }

    #[test]
    fn cpu_step_phase_wrap_keeps_small_dt_stable() {
        // Starting just below 2pi with a positive derivative should wrap back.
        let phase = vec![core::f32::consts::TAU - 0.001];
        let amp = vec![1.0];
        let freq = vec![1.0];
        let (out_p, _, _) = step_cpu(&phase, &amp, &freq, &DEFAULT_PARAMS).unwrap();
        assert!(out_p[0] >= 0.0);
        assert!(out_p[0] < core::f32::consts::TAU);
    }
}

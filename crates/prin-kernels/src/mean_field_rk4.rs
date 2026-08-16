//! Mean-field Kuramoto RK4 step: a CPU reference and a single-source CubeCL
//! kernel set for CUDA, wgpu, and CPU-SIMD backends.
//!
//! The CPU implementation in [`step_cpu`] is the numerical authority. The
//! CubeCL path in [`cubecl`] (enabled by the `cuda` or `wgpu` features) uses
//! the same algorithm and is checked against the CPU reference in
//! kernel-equivalence tests.
//!
//! # Buffer management
//!
//! Both paths support preallocated buffer pools (`MeanFieldRk4Buffers` for
//! CPU, `CubeclBufferPool` for GPU) that eliminate per-step heap/device
//! allocations. Use [`step_cpu_with_pool`] / `step_cubecl_with_pool` (in the
//! `cubecl` submodule) for repeated stepping.

use thiserror::Error;

use crate::buffers::MeanFieldRk4Buffers;

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
    /// The requested compute backend (wgpu/CUDA) is not available on this host.
    #[error("backend unavailable: {name}")]
    BackendUnavailable {
        /// Backend name.
        name: &'static str,
    },
    /// Preallocated buffer pool was sized for a different oscillator count.
    #[error("buffer pool capacity ({capacity}) does not match oscillator count ({actual})")]
    PoolSizeMismatch {
        /// Oscillator count the pool was allocated for.
        capacity: usize,
        /// Oscillator count derived from the input slices.
        actual: usize,
    },
    /// Device-event profiling of a kernel launch sequence failed.
    #[error("device profiling failed: {message}")]
    ProfilingFailed {
        /// Underlying `cubecl` profiling error message.
        message: String,
    },
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
///
/// The per-term products are accumulated in `f64` (Coding Standards §2.2:
/// "f64 for reference paths and accumulations of reductions") before the
/// final `n_inv` normalization and downcast to `f32`, so this reference stays
/// accurate at large `N` where a naive `f32` running sum loses precision. The
/// GPU path's [`cubecl::order_param_block_reduce`](super::mean_field_rk4::cubecl)
/// kernel implements the same algorithm hierarchically: each cube block
/// computes an `f32` partial sum in shared memory, and the host finishes the
/// reduction over the (small) per-block partials in `f64` — this is the
/// single authoritative order-parameter algorithm used by both the CPU
/// reference path and every GPU backend (one algorithm, one implementation).
pub(crate) fn order_param(phase: &[f32], amplitude: &[f32], n_inv: f32) -> (f32, f32) {
    let mut z_real = 0.0_f64;
    let mut z_imag = 0.0_f64;
    for (p, a) in phase.iter().zip(amplitude) {
        let (s, c) = p.sin_cos();
        z_real += f64::from(*a) * f64::from(c);
        z_imag += f64::from(*a) * f64::from(s);
    }
    let n_inv = f64::from(n_inv);
    ((z_real * n_inv) as f32, (z_imag * n_inv) as f32)
}

/// Compute the mean-field Kuramoto derivatives, pushing results into the
/// provided output `Vec`s (which must be empty on entry).
#[allow(clippy::too_many_arguments)]
fn mean_field_derivatives_into(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
    n_inv: f32,
    dphi: &mut Vec<f32>,
    dr: &mut Vec<f32>,
    domega: &mut Vec<f32>,
) {
    let (zx, zy) = order_param(phase, amplitude, n_inv);

    for ((p, a), f) in phase.iter().zip(amplitude).zip(frequency) {
        let (s, c) = p.sin_cos();
        let r_sin = zy * c - zx * s;
        let r_cos = zx * c + zy * s;
        dphi.push(f + params.k * r_sin);
        dr.push(-params.decay * *a + params.k * r_cos);
        domega.push(params.gamma * params.k * r_sin * n_inv);
    }
}

/// One fourth-order Runge-Kutta step for the mean-field Kuramoto model.
///
/// This is the CPU reference path. It matches the PRINet 3.0 PyTorch fallback
/// `pytorch_mean_field_rk4_step` (phase wrap to `[0, 2pi)` and amplitude clamp
/// `>= 0` at each RK stage and the final weighted sum).
///
/// For repeated stepping, prefer [`step_cpu_with_pool`] which reuses
/// preallocated buffers and avoids per-step heap allocations.
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

    let mut pool = MeanFieldRk4Buffers::new(n);
    step_cpu_with_pool(phase, amplitude, frequency, params, &mut pool)
}

/// One fourth-order Runge-Kutta step using preallocated CPU buffers.
///
/// Identical to [`step_cpu`] but reuses the caller-provided
/// [`MeanFieldRk4Buffers`] to avoid per-step heap allocations. The pool's
/// buffers are cleared and refilled on each call; the allocated capacity is
/// preserved across calls.
///
/// # Errors
///
/// Returns [`MeanFieldRk4Error`] on invalid inputs or parameters.
pub fn step_cpu_with_pool(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
    pool: &mut MeanFieldRk4Buffers,
) -> Result<MeanFieldRk4Output, MeanFieldRk4Error> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_param("k", params.k, false)?;
    validate_param("decay", params.decay, false)?;
    validate_param("gamma", params.gamma, false)?;
    validate_param("dt", params.dt, true)?;

    if pool.capacity() != n {
        return Err(MeanFieldRk4Error::PoolSizeMismatch {
            capacity: pool.capacity(),
            actual: n,
        });
    }

    pool.clear();

    let n_inv = 1.0 / n as f32;
    let half_dt = params.dt * 0.5;
    let sixth_dt = params.dt / 6.0;

    // k1 = f(state)
    mean_field_derivatives_into(
        phase,
        amplitude,
        frequency,
        params,
        n_inv,
        &mut pool.k1_phase,
        &mut pool.k1_amp,
        &mut pool.k1_freq,
    );

    // Build stage-2 state into the pool stage buffers: base + 0.5*dt*k1.
    for i in 0..n {
        pool.stage_phase
            .push(wrap_phase(phase[i] + half_dt * pool.k1_phase[i]));
        pool.stage_amp
            .push(clamp_amp(amplitude[i] + half_dt * pool.k1_amp[i]));
        pool.stage_freq
            .push(frequency[i] + half_dt * pool.k1_freq[i]);
    }

    // k2 = f(stage-2 state)
    mean_field_derivatives_into(
        &pool.stage_phase,
        &pool.stage_amp,
        &pool.stage_freq,
        params,
        n_inv,
        &mut pool.k2_phase,
        &mut pool.k2_amp,
        &mut pool.k2_freq,
    );

    // Build stage-3 state: base + 0.5*dt*k2.
    // We need a temporary because we read stage_* (k1-based) and write
    // stage_* (k2-based) — can't do both on the same Vec.
    let mut tmp_phase = Vec::with_capacity(n);
    let mut tmp_amp = Vec::with_capacity(n);
    let mut tmp_freq = Vec::with_capacity(n);
    for i in 0..n {
        tmp_phase.push(wrap_phase(phase[i] + half_dt * pool.k2_phase[i]));
        tmp_amp.push(clamp_amp(amplitude[i] + half_dt * pool.k2_amp[i]));
        tmp_freq.push(frequency[i] + half_dt * pool.k2_freq[i]);
    }
    pool.stage_phase.clear();
    pool.stage_amp.clear();
    pool.stage_freq.clear();
    pool.stage_phase.extend_from_slice(&tmp_phase);
    pool.stage_amp.extend_from_slice(&tmp_amp);
    pool.stage_freq.extend_from_slice(&tmp_freq);

    // k3 = f(stage-3 state)
    mean_field_derivatives_into(
        &pool.stage_phase,
        &pool.stage_amp,
        &pool.stage_freq,
        params,
        n_inv,
        &mut pool.k3_phase,
        &mut pool.k3_amp,
        &mut pool.k3_freq,
    );

    // Build stage-4 state: base + dt*k3.
    tmp_phase.clear();
    tmp_amp.clear();
    tmp_freq.clear();
    for i in 0..n {
        tmp_phase.push(wrap_phase(phase[i] + params.dt * pool.k3_phase[i]));
        tmp_amp.push(clamp_amp(amplitude[i] + params.dt * pool.k3_amp[i]));
        tmp_freq.push(frequency[i] + params.dt * pool.k3_freq[i]);
    }
    pool.stage_phase.clear();
    pool.stage_amp.clear();
    pool.stage_freq.clear();
    pool.stage_phase.extend_from_slice(&tmp_phase);
    pool.stage_amp.extend_from_slice(&tmp_amp);
    pool.stage_freq.extend_from_slice(&tmp_freq);

    // k4 = f(stage-4 state)
    mean_field_derivatives_into(
        &pool.stage_phase,
        &pool.stage_amp,
        &pool.stage_freq,
        params,
        n_inv,
        &mut pool.k4_phase,
        &mut pool.k4_amp,
        &mut pool.k4_freq,
    );

    // Final weighted sum: base + dt/6 * (k1 + 2*k2 + 2*k3 + k4).
    for i in 0..n {
        let new_p = wrap_phase(
            phase[i]
                + sixth_dt
                    * (pool.k1_phase[i]
                        + 2.0 * pool.k2_phase[i]
                        + 2.0 * pool.k3_phase[i]
                        + pool.k4_phase[i]),
        );
        let new_a = clamp_amp(
            amplitude[i]
                + sixth_dt
                    * (pool.k1_amp[i]
                        + 2.0 * pool.k2_amp[i]
                        + 2.0 * pool.k3_amp[i]
                        + pool.k4_amp[i]),
        );
        let new_f = frequency[i]
            + sixth_dt
                * (pool.k1_freq[i]
                    + 2.0 * pool.k2_freq[i]
                    + 2.0 * pool.k3_freq[i]
                    + pool.k4_freq[i]);
        pool.out_phase.push(new_p);
        pool.out_amp.push(new_a);
        pool.out_freq.push(new_f);
    }

    Ok((
        pool.out_phase.clone(),
        pool.out_amp.clone(),
        pool.out_freq.clone(),
    ))
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
        let phase = vec![core::f32::consts::TAU - 0.001];
        let amp = vec![1.0];
        let freq = vec![1.0];
        let (out_p, _, _) = step_cpu(&phase, &amp, &freq, &DEFAULT_PARAMS).unwrap();
        assert!(out_p[0] >= 0.0);
        assert!(out_p[0] < core::f32::consts::TAU);
    }

    #[test]
    fn cpu_rk4_amplitude_error_scales_like_dt_to_the_fifth() {
        let decay = 1.0_f32;
        let phase = vec![0.0_f32];
        let amplitude = vec![1.0_f32];
        let frequency = vec![0.0_f32];

        let run = |dt: f32| {
            let params = MeanFieldRk4Params {
                k: 0.0,
                decay,
                gamma: 0.0,
                dt,
            };
            let (_, out_a, _) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
            let exact = (-decay * dt).exp();
            (out_a[0] - exact).abs()
        };

        let e_coarse = run(0.2);
        let e_fine = run(0.1);
        assert!(e_coarse > 0.0 && e_fine > 0.0);
        let ratio = e_coarse / e_fine;
        assert!(
            ratio > 15.0 && ratio < 60.0,
            "expected RK4 local error ratio ~32, got {ratio}"
        );
    }

    #[test]
    fn step_cpu_with_pool_matches_step_cpu() {
        let n = 64;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amp: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let freq: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let (ref_p, ref_a, ref_f) = step_cpu(&phase, &amp, &freq, &params).unwrap();

        let mut pool = MeanFieldRk4Buffers::new(n);
        let (pool_p, pool_a, pool_f) =
            step_cpu_with_pool(&phase, &amp, &freq, &params, &mut pool).unwrap();

        assert_eq!(ref_p, pool_p);
        assert_eq!(ref_a, pool_a);
        assert_eq!(ref_f, pool_f);
    }

    #[test]
    fn step_cpu_with_pool_reuse_across_steps() {
        let n = 32;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amp = vec![1.0_f32; n];
        let freq: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let mut pool = MeanFieldRk4Buffers::new(n);

        let mut cur_p = phase;
        let mut cur_a = amp;
        let mut cur_f = freq;
        for _ in 0..10 {
            let (new_p, new_a, new_f) =
                step_cpu_with_pool(&cur_p, &cur_a, &cur_f, &params, &mut pool).unwrap();
            cur_p = new_p;
            cur_a = new_a;
            cur_f = new_f;
        }

        for p in &cur_p {
            assert!(*p >= 0.0 && *p < core::f32::consts::TAU);
        }
        for a in &cur_a {
            assert!(*a >= 0.0 && a.is_finite());
        }
        for f in &cur_f {
            assert!(f.is_finite());
        }
    }

    #[test]
    fn step_cpu_with_pool_rejects_size_mismatch() {
        let pool_n = 4;
        let call_n = 64;
        let phase = vec![0.1_f32; call_n];
        let amp = vec![1.0_f32; call_n];
        let freq = vec![0.0_f32; call_n];
        let mut pool = MeanFieldRk4Buffers::new(pool_n);
        let err = step_cpu_with_pool(&phase, &amp, &freq, &DEFAULT_PARAMS, &mut pool).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::PoolSizeMismatch {
                capacity: 4,
                actual: 64,
            }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    const TAU: f32 = core::f32::consts::TAU;

    fn any_params() -> impl Strategy<Value = MeanFieldRk4Params> {
        (
            0.0_f32..=2.0_f32,
            0.0_f32..=0.5_f32,
            -0.1_f32..=0.1_f32,
            0.001_f32..=0.05_f32,
        )
            .prop_map(|(k, decay, gamma, dt)| MeanFieldRk4Params {
                k,
                decay,
                gamma,
                dt,
            })
    }

    fn any_state(n: usize) -> impl Strategy<Value = (Vec<f32>, Vec<f32>, Vec<f32>)> {
        (
            proptest::collection::vec(0.0_f32..TAU, n),
            proptest::collection::vec(0.0_f32..=1.0_f32, n),
            proptest::collection::vec(-1.0_f32..=1.0_f32, n),
        )
            .prop_map(|(phase, amp, freq)| (phase, amp, freq))
    }

    fn zero_coupling_params(mut params: MeanFieldRk4Params) -> MeanFieldRk4Params {
        params.k = 0.0;
        params
    }

    #[test]
    fn phase_and_amplitude_invariants_are_preserved() {
        let config = ProptestConfig::with_cases(64);
        proptest!(config, |(n in 1usize..=64, params in any_params(), state in any_state(64))| {
            let (phase, amplitude, frequency) = state;
            let phase = phase[..n].to_vec();
            let amplitude = amplitude[..n].to_vec();
            let frequency = frequency[..n].to_vec();

            let (out_p, out_a, out_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();

            for p in &out_p {
                prop_assert!(*p >= 0.0);
                prop_assert!(*p < TAU);
            }
            for a in &out_a {
                prop_assert!(*a >= 0.0);
                prop_assert!(a.is_finite());
            }
            for f in &out_f {
                prop_assert!(f.is_finite());
            }
        });
    }

    #[test]
    fn zero_coupling_is_free_run() {
        let config = ProptestConfig::with_cases(64);
        proptest!(config, |(n in 2usize..=32, params in any_params().prop_map(zero_coupling_params), state in any_state(32))| {
            let (phase, amplitude, frequency) = state;
            let phase = phase[..n].to_vec();
            let amplitude = amplitude[..n].to_vec();
            let frequency = frequency[..n].to_vec();

            let (out_p, out_a, out_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();

            for i in 0..n {
                let expected_p = wrap_phase(phase[i] + params.dt * frequency[i]);
                let x = params.decay * params.dt;
                let expected_a = amplitude[i] * (-x).exp();
                let expected_f = frequency[i];

                prop_assert!((out_p[i] - expected_p).abs() < 1e-5, "phase mismatch at {}", i);
                prop_assert!((out_a[i] - expected_a).abs() < 1e-5, "amplitude mismatch at {}", i);
                prop_assert!((out_f[i] - expected_f).abs() < 1e-6, "frequency mismatch at {}", i);
            }
        });
    }

    #[test]
    fn order_parameter_magnitude_is_bounded() {
        let config = ProptestConfig::with_cases(64);
        proptest!(config, |(n in 2usize..=32, state in any_state(32))| {
            let (phase, amplitude, _frequency) = state;
            let phase = phase[..n].to_vec();
            let amplitude = amplitude[..n].to_vec();
            let n_inv = 1.0 / n as f32;

            let (zx, zy) = order_param(&phase, &amplitude, n_inv);
            let mean_amp = amplitude.iter().sum::<f32>() * n_inv;
            let z_norm_sq = zx * zx + zy * zy;

            prop_assert!(z_norm_sq <= mean_amp * mean_amp + 1e-6);
        });
    }

    #[test]
    fn pool_matches_fresh_allocation_across_random_inputs() {
        let config = ProptestConfig::with_cases(32);
        proptest!(config, |(n in 1usize..=64, params in any_params(), state in any_state(64))| {
            let (phase, amplitude, frequency) = state;
            let phase = phase[..n].to_vec();
            let amplitude = amplitude[..n].to_vec();
            let frequency = frequency[..n].to_vec();

            let (ref_p, ref_a, ref_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
            let mut pool = MeanFieldRk4Buffers::new(n);
            let (pool_p, pool_a, pool_f) =
                step_cpu_with_pool(&phase, &amplitude, &frequency, &params, &mut pool).unwrap();

            prop_assert!(ref_p == pool_p);
            prop_assert!(ref_a == pool_a);
            prop_assert!(ref_f == pool_f);
        });
    }
}

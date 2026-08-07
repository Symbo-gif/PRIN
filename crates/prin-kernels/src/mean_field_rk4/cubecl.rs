//! Single-source CubeCL implementation of the mean-field RK4 step.
//!
//! This module is enabled by the `cuda` or `wgpu` features. It contains the
//! `#[cube]` kernels and the runtime launch code. The CPU reference in
//! [`super::step_cpu`] remains the numerical authority; this path is checked
//! against it in the kernel-equivalence tests.
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `N * size_of::<f32>()` bytes. Those
//! handles are created by `ComputeClient::create` or `ComputeClient::empty`,
//! so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use cubecl::prelude::*;
use cubecl::server::Handle;

use super::{validate_param, validate_state, MeanFieldRk4Error, MeanFieldRk4Params};

/// Full CubeCL step output: `(phase, amplitude, frequency)` plus a report.
pub type StepCubeclOutput = (super::MeanFieldRk4Output, StepReport);

/// Scalar timing and backend metadata for one CubeCL step.
#[derive(Clone, Debug, PartialEq)]
pub struct StepReport {
    /// Backend runtime name, e.g. `"wgpu<wgsl>"` or `"cuda"`.
    pub backend_name: String,
    /// Wall-clock time for the whole step, including host reductions.
    pub wall_time_seconds: f64,
    /// Number of launches dispatched (4 stage kernels + 1 finalize kernel).
    pub launch_count: u32,
}

/// One RK4 stage: compute the derivative of `s = base + dt_scale * k_prev` and
/// the next intermediate state `s_next = base + next_dt_scale * k`.
///
/// `z_real` and `z_imag` are the order parameter of `s`, computed by the host
/// from the previous stage's `s_next`. This keeps the prototype free of
/// device-side global reductions, which are a future optimization (see WP-018).
#[cube(launch)]
fn mean_field_rk4_stage<F: Float + CubeElement>(
    base_phase: &Array<F>,
    base_amp: &Array<F>,
    base_freq: &Array<F>,
    k_prev_phase: &Array<F>,
    k_prev_amp: &Array<F>,
    k_prev_freq: &Array<F>,
    dt_scale: F,
    next_dt_scale: F,
    z_real: F,
    z_imag: F,
    k: F,
    decay: F,
    gamma: F,
    n_inv: F,
    k_phase: &mut Array<F>,
    k_amp: &mut Array<F>,
    k_freq: &mut Array<F>,
    s_next_phase: &mut Array<F>,
    s_next_amp: &mut Array<F>,
    s_next_freq: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < base_phase.len() {
        let bp = base_phase[i];
        let ba = base_amp[i];
        let bf = base_freq[i];
        let kpp = k_prev_phase[i];
        let kpa = k_prev_amp[i];
        let kpf = k_prev_freq[i];

        let two_pi = F::new(core::f32::consts::TAU);
        let s_p_raw = bp + dt_scale * kpp;
        let s_p = s_p_raw - (s_p_raw / two_pi).floor() * two_pi;
        let s_a = (ba + dt_scale * kpa).max(F::new(0.0_f32));
        let s_f = bf + dt_scale * kpf;

        let (s, c) = (s_p.sin(), s_p.cos());
        let r_sin = z_imag * c - z_real * s;
        let r_cos = z_real * c + z_imag * s;

        k_phase[i] = s_f + k * r_sin;
        k_amp[i] = -decay * s_a + k * r_cos;
        k_freq[i] = gamma * k * r_sin * n_inv;

        let s_next_p_raw = bp + next_dt_scale * k_phase[i];
        s_next_phase[i] = s_next_p_raw - (s_next_p_raw / two_pi).floor() * two_pi;
        s_next_amp[i] = (ba + next_dt_scale * k_amp[i]).max(F::new(0.0_f32));
        s_next_freq[i] = bf + next_dt_scale * k_freq[i];
    }
}

/// Final RK4 weighted sum: `base + dt/6 * (k1 + 2*k2 + 2*k3 + k4)`.
#[cube(launch)]
fn mean_field_rk4_finalize<F: Float + CubeElement>(
    base_phase: &Array<F>,
    base_amp: &Array<F>,
    base_freq: &Array<F>,
    k1_phase: &Array<F>,
    k2_phase: &Array<F>,
    k3_phase: &Array<F>,
    k4_phase: &Array<F>,
    k1_amp: &Array<F>,
    k2_amp: &Array<F>,
    k3_amp: &Array<F>,
    k4_amp: &Array<F>,
    k1_freq: &Array<F>,
    k2_freq: &Array<F>,
    k3_freq: &Array<F>,
    k4_freq: &Array<F>,
    dt: F,
    out_phase: &mut Array<F>,
    out_amp: &mut Array<F>,
    out_freq: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < base_phase.len() {
        let two_pi = F::new(core::f32::consts::TAU);
        let dt6 = dt / F::new(6.0_f32);
        let two = F::new(2.0_f32);

        let p =
            base_phase[i] + dt6 * (k1_phase[i] + two * (k2_phase[i] + k3_phase[i]) + k4_phase[i]);
        let a = base_amp[i] + dt6 * (k1_amp[i] + two * (k2_amp[i] + k3_amp[i]) + k4_amp[i]);
        let f = base_freq[i] + dt6 * (k1_freq[i] + two * (k2_freq[i] + k3_freq[i]) + k4_freq[i]);

        out_phase[i] = p - (p / two_pi).floor() * two_pi;
        out_amp[i] = a.max(F::new(0.0_f32));
        out_freq[i] = f;
    }
}

/// Build an [`ArrayArg`] from a [`Handle`] whose length is `n` `f32`s.
///
/// # Safety
///
/// `handle` must refer to a device allocation of at least `n * size_of::<f32>()`
/// bytes. All handles in this module come from `client.create_from_slice` or
/// `client.empty(byte_len)`, so the invariant holds.
fn array_arg<R: Runtime>(handle: &Handle, n: usize) -> ArrayArg<R> {
    // SAFETY: see function-level safety note.
    unsafe { ArrayArg::from_raw_parts(handle.clone(), n) }
}

/// Read one `f32` buffer back from the device.
fn read_f32s<R: Runtime>(
    client: &ComputeClient<R>,
    handle: &Handle,
    _n: usize,
) -> Result<Vec<f32>, MeanFieldRk4Error> {
    let bytes = client
        .read_one(handle.clone())
        .map_err(|_| MeanFieldRk4Error::BackendReadError)?;
    Ok(f32::from_bytes(&bytes).to_vec())
}

/// Read the three state buffers and return `(phase, amplitude, frequency)`.
fn read_state<R: Runtime>(
    client: &ComputeClient<R>,
    phase_h: &Handle,
    amp_h: &Handle,
    freq_h: &Handle,
    n: usize,
) -> Result<super::MeanFieldRk4Output, MeanFieldRk4Error> {
    Ok((
        read_f32s(client, phase_h, n)?,
        read_f32s(client, amp_h, n)?,
        read_f32s(client, freq_h, n)?,
    ))
}

/// Compute the order parameter on the host.
///
/// This is a temporary stand-in for a device-side reduction (see WP-018).
fn order_param_host(phase: &[f32], amplitude: &[f32], n_inv: f32) -> (f32, f32) {
    let mut z_real = 0.0_f32;
    let mut z_imag = 0.0_f32;
    for (p, a) in phase.iter().zip(amplitude) {
        let (s, c) = p.sin_cos();
        z_real += *a * c;
        z_imag += *a * s;
    }
    (z_real * n_inv, z_imag * n_inv)
}

/// Execute one mean-field RK4 step on a CubeCL runtime.
///
/// The implementation is generic over `R: Runtime`; concrete entry points
/// are provided by `try_step_wgpu` and `try_step_cuda`.
pub fn step_cubecl<R: Runtime>(
    client: &ComputeClient<R>,
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_param("k", params.k, false)?;
    validate_param("decay", params.decay, false)?;
    validate_param("gamma", params.gamma, false)?;
    validate_param("dt", params.dt, true)?;

    let n_inv = 1.0_f32 / n as f32;
    let half_dt = params.dt * 0.5;
    let byte_len = n * core::mem::size_of::<f32>();

    // Helper to create an output handle of the right size.
    let empty = || client.empty(byte_len);

    // Device handles.
    let base_phase_h = client.create_from_slice(f32::as_bytes(phase));
    let base_amp_h = client.create_from_slice(f32::as_bytes(amplitude));
    let base_freq_h = client.create_from_slice(f32::as_bytes(frequency));
    let k_zero_h = client.create_from_slice(f32::as_bytes(&vec![0.0_f32; n]));

    let k1_phase_h = empty();
    let k1_amp_h = empty();
    let k1_freq_h = empty();

    let k2_phase_h = empty();
    let k2_amp_h = empty();
    let k2_freq_h = empty();

    let k3_phase_h = empty();
    let k3_amp_h = empty();
    let k3_freq_h = empty();

    let k4_phase_h = empty();
    let k4_amp_h = empty();
    let k4_freq_h = empty();

    let s_next_phase_h = empty();
    let s_next_amp_h = empty();
    let s_next_freq_h = empty();

    let out_phase_h = empty();
    let out_amp_h = empty();
    let out_freq_h = empty();

    let cube_dim = CubeDim::new_1d(256);
    let cube_count = CubeCount::Static(n.div_ceil(256).max(1) as u32, 1, 1);

    let start = std::time::Instant::now();

    // Stage 1: dt_scale = 0, next_dt_scale = 0.5*dt.
    let (zr, zi) = order_param_host(phase, amplitude, n_inv);
    mean_field_rk4_stage::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(&base_phase_h, n),
        array_arg(&base_amp_h, n),
        array_arg(&base_freq_h, n),
        array_arg(&k_zero_h, n),
        array_arg(&k_zero_h, n),
        array_arg(&k_zero_h, n),
        0.0_f32,
        half_dt,
        zr,
        zi,
        params.k,
        params.decay,
        params.gamma,
        n_inv,
        array_arg(&k1_phase_h, n),
        array_arg(&k1_amp_h, n),
        array_arg(&k1_freq_h, n),
        array_arg(&s_next_phase_h, n),
        array_arg(&s_next_amp_h, n),
        array_arg(&s_next_freq_h, n),
    );

    // Stage 2.
    let (s2_p, s2_a, _s2_f) =
        read_state(client, &s_next_phase_h, &s_next_amp_h, &s_next_freq_h, n)?;
    let (zr, zi) = order_param_host(&s2_p, &s2_a, n_inv);
    mean_field_rk4_stage::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(&base_phase_h, n),
        array_arg(&base_amp_h, n),
        array_arg(&base_freq_h, n),
        array_arg(&k1_phase_h, n),
        array_arg(&k1_amp_h, n),
        array_arg(&k1_freq_h, n),
        half_dt,
        half_dt,
        zr,
        zi,
        params.k,
        params.decay,
        params.gamma,
        n_inv,
        array_arg(&k2_phase_h, n),
        array_arg(&k2_amp_h, n),
        array_arg(&k2_freq_h, n),
        array_arg(&s_next_phase_h, n),
        array_arg(&s_next_amp_h, n),
        array_arg(&s_next_freq_h, n),
    );

    // Stage 3.
    let (s3_p, s3_a, _s3_f) =
        read_state(client, &s_next_phase_h, &s_next_amp_h, &s_next_freq_h, n)?;
    let (zr, zi) = order_param_host(&s3_p, &s3_a, n_inv);
    mean_field_rk4_stage::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(&base_phase_h, n),
        array_arg(&base_amp_h, n),
        array_arg(&base_freq_h, n),
        array_arg(&k2_phase_h, n),
        array_arg(&k2_amp_h, n),
        array_arg(&k2_freq_h, n),
        half_dt,
        params.dt,
        zr,
        zi,
        params.k,
        params.decay,
        params.gamma,
        n_inv,
        array_arg(&k3_phase_h, n),
        array_arg(&k3_amp_h, n),
        array_arg(&k3_freq_h, n),
        array_arg(&s_next_phase_h, n),
        array_arg(&s_next_amp_h, n),
        array_arg(&s_next_freq_h, n),
    );

    // Stage 4.
    let (s4_p, s4_a, _s4_f) =
        read_state(client, &s_next_phase_h, &s_next_amp_h, &s_next_freq_h, n)?;
    let (zr, zi) = order_param_host(&s4_p, &s4_a, n_inv);
    mean_field_rk4_stage::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(&base_phase_h, n),
        array_arg(&base_amp_h, n),
        array_arg(&base_freq_h, n),
        array_arg(&k3_phase_h, n),
        array_arg(&k3_amp_h, n),
        array_arg(&k3_freq_h, n),
        params.dt,
        0.0_f32,
        zr,
        zi,
        params.k,
        params.decay,
        params.gamma,
        n_inv,
        array_arg(&k4_phase_h, n),
        array_arg(&k4_amp_h, n),
        array_arg(&k4_freq_h, n),
        array_arg(&s_next_phase_h, n),
        array_arg(&s_next_amp_h, n),
        array_arg(&s_next_freq_h, n),
    );

    // Final weighted sum.
    mean_field_rk4_finalize::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(&base_phase_h, n),
        array_arg(&base_amp_h, n),
        array_arg(&base_freq_h, n),
        array_arg(&k1_phase_h, n),
        array_arg(&k2_phase_h, n),
        array_arg(&k3_phase_h, n),
        array_arg(&k4_phase_h, n),
        array_arg(&k1_amp_h, n),
        array_arg(&k2_amp_h, n),
        array_arg(&k3_amp_h, n),
        array_arg(&k4_amp_h, n),
        array_arg(&k1_freq_h, n),
        array_arg(&k2_freq_h, n),
        array_arg(&k3_freq_h, n),
        array_arg(&k4_freq_h, n),
        params.dt,
        array_arg(&out_phase_h, n),
        array_arg(&out_amp_h, n),
        array_arg(&out_freq_h, n),
    );

    let report = StepReport {
        backend_name: R::name(client).to_string(),
        wall_time_seconds: start.elapsed().as_secs_f64(),
        launch_count: 5,
    };

    let out_phase = read_f32s(client, &out_phase_h, n)?;
    let out_amp = read_f32s(client, &out_amp_h, n)?;
    let out_freq = read_f32s(client, &out_freq_h, n)?;

    Ok(((out_phase, out_amp, out_freq), report))
}

#[cfg(feature = "wgpu")]
/// Run the mean-field RK4 step on the wgpu runtime.
pub fn try_step_wgpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    let device = WgpuDevice::DefaultDevice;
    let client = WgpuRuntime::client(&device);
    step_cubecl(&client, phase, amplitude, frequency, params)
}

#[cfg(feature = "cpu")]
/// Run the mean-field RK4 step on the CubeCL CPU runtime.
pub fn try_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
    use cubecl::cpu::{CpuDevice, CpuRuntime};
    let device = CpuDevice;
    let client = CpuRuntime::client(&device);
    step_cubecl(&client, phase, amplitude, frequency, params)
}

#[cfg(feature = "cuda")]
/// Run the mean-field RK4 step on the CUDA runtime.
pub fn try_step_cuda(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
    use cubecl::cuda::{CudaDevice, CudaRuntime};
    let device = CudaDevice::default();
    let client = CudaRuntime::client(&device);
    step_cubecl(&client, phase, amplitude, frequency, params)
}

#[cfg(all(test, feature = "wgpu"))]
mod tests {
    use super::*;
    use crate::mean_field_rk4::{step_cpu, MeanFieldRk4Params};

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_small_n() {
        let n = 64;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_step_wgpu(&phase, &amplitude, &frequency, &params).unwrap();

        assert_eq!(report.backend_name, "wgpu<wgsl>");
        eprintln!("N=1M wgpu step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_at_one_million() {
        let n = 1_000_000_usize;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * (i % 64) as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * ((i % 64) as f32 - 32.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_step_wgpu(&phase, &amplitude, &frequency, &params).unwrap();

        assert_eq!(report.backend_name, "wgpu<wgsl>");
        eprintln!("N=1M wgpu step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_rejects_mismatched_lengths() {
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        let err = try_step_wgpu(&phase, &amp, &freq, &params).unwrap_err();
        assert!(matches!(err, MeanFieldRk4Error::LengthMismatch { .. }));
    }

    #[test]
    fn wgpu_rejects_empty_population() {
        let phase: Vec<f32> = vec![];
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        let err = try_step_wgpu(&phase, &phase, &phase, &params).unwrap_err();
        assert!(matches!(err, MeanFieldRk4Error::EmptyPopulation));
    }

    #[test]
    fn wgpu_rejects_non_finite_dt() {
        let mut params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        params.dt = f32::NAN;
        let phase = vec![0.0_f32];
        let err = try_step_wgpu(&phase, &phase, &phase, &params).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::NonFiniteParameter { name: "dt", .. }
        ));
    }

    #[test]
    fn wgpu_rejects_negative_dt() {
        let mut params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        params.dt = -0.01;
        let phase = vec![0.0_f32];
        let err = try_step_wgpu(&phase, &phase, &phase, &params).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::InvalidParameter { name: "dt", .. }
        ));
    }
}

#[cfg(all(test, feature = "cpu"))]
mod tests_cpu {
    use super::*;
    use crate::mean_field_rk4::{step_cpu, MeanFieldRk4Params};

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    #[test]
    fn cpu_matches_cpu_reference_for_small_n() {
        let n = 64;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((out_p, out_a, out_f), report) =
            try_step_cpu(&phase, &amplitude, &frequency, &params).unwrap();

        assert_eq!(report.backend_name, "cpu");
        eprintln!("N={n} cpu step report: {report:?}");
        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }
}

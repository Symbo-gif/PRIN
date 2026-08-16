//! Single-source CubeCL implementation of the fused three-band discrete step.
//!
//! This module is enabled by the `cuda` or `wgpu` features. It contains the
//! `#[cube]` kernels and the runtime launch code. The CPU reference in
//! [`super::discrete_step_cpu`] remains the numerical authority; this path is
//! checked against it in the kernel-equivalence tests below.
//!
//! ## Reusable hierarchical reductions
//!
//! Two block-reduction kernels are each launched multiple times across the
//! fused path instead of being duplicated per band/pair:
//!
//! - `complex_order_reduce` computes a band's mean-field order parameter
//!   `Z = (1/N_b) * sum(amp[i] * e^{i*phase[i]})` — structurally identical to
//!   `mean_field_rk4::cubecl::order_param_block_reduce` (same two-barrier
//!   shared-memory design, reused here as the proven-correct pattern rather
//!   than re-derived; see that kernel's doc comment for the CubeCL
//!   CPU-backend data-race rationale). Called once per band (3 times per
//!   step).
//! - `real_sum_reduce` computes a plain sum for the PAC slow-phase mean —
//!   structurally identical to [`crate::pac::cubecl`]'s
//!   `pac_phase_sum_block_reduce`. Called once per PAC pair (2 times per
//!   step).
//!
//! Both finish their reduction with an `f64` host accumulator (Coding
//! Standards §2.2), matching `super::mean_f64` on the CPU reference path
//! exactly.
//!
//! ## Launch sequence (10 launches per step)
//!
//! 1. `complex_order_reduce` (delta's `Z`)
//! 2. `band_euler_step` (delta)
//! 3. `real_sum_reduce` (mean of delta's new phase)
//! 4. `pac_gate` (theta's gated amplitude)
//! 5. `complex_order_reduce` (theta's `Z`, from the gated amplitude)
//! 6. `band_euler_step` (theta)
//! 7. `real_sum_reduce` (mean of theta's new phase)
//! 8. `pac_gate` (gamma's gated amplitude)
//! 9. `complex_order_reduce` (gamma's `Z`, from the gated amplitude)
//! 10. `band_euler_step` (gamma)
//!
//! No buffer pool is used this session (each band's device handles are
//! created fresh via `client.create_from_slice`/`client.empty`), matching the
//! precedent set by `sparse_knn`/`pac` (WP-019 S1 handoff, "Out-of-scope
//! discoveries") — a future performance WP can add pooling if profiling shows
//! per-call allocation dominating.
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `len * size_of::<f32>()` bytes. Those
//! handles are created by `ComputeClient::create_from_slice` or
//! `ComputeClient::empty`, so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use cubecl::prelude::*;
use cubecl::profile::TimingMethod as CubeclTimingMethod;
use cubecl::server::Handle;

use super::{
    band_offsets, validate_bands, validate_params, validate_state, BandStepParams,
    DiscreteStepError, DiscreteStepParams, DELTA,
};
use crate::buffers::num_blocks_for;
pub use crate::mean_field_rk4::cubecl::TimingMethod;

/// Full CubeCL step output: `(phase, amplitude, frequency)` plus a report.
pub type StepCubeclOutput = (super::DiscreteStepOutput, StepReport);

/// Scalar timing and backend metadata for one fused discrete step.
#[derive(Clone, Debug, PartialEq)]
pub struct StepReport {
    /// Backend runtime name, e.g. `"wgpu<wgsl>"` or `"cuda"`.
    pub backend_name: String,
    /// Time for the profiled kernel-launch sequence, in seconds. See
    /// [`crate::mean_field_rk4::cubecl::TimingMethod`] for how this is
    /// measured.
    pub wall_time_seconds: f64,
    /// How [`Self::wall_time_seconds`] was measured.
    pub timing_method: TimingMethod,
    /// Number of kernel launches dispatched (10 — see the module
    /// documentation's launch sequence).
    pub launch_count: u32,
}

/// Level 1 of the hierarchical order-parameter reduction: each 256-thread
/// cube block reduces its slice of `amp[i] * e^{i*phase[i]}` terms into one
/// `(real, imag)` `f32` partial-sum pair. See the module documentation.
#[cube(launch)]
fn complex_order_reduce<F: Float + CubeElement>(
    phase: &Array<F>,
    amp: &Array<F>,
    block_real: &mut Array<F>,
    block_imag: &mut Array<F>,
) {
    let tid = UNIT_POS as usize;
    let i = ABSOLUTE_POS;

    let mut real_sh = SharedMemory::<F>::new(256usize);
    let mut imag_sh = SharedMemory::<F>::new(256usize);

    if i < phase.len() {
        let p = phase[i];
        let a = amp[i];
        real_sh[tid] = a * p.cos();
        imag_sh[tid] = a * p.sin();
    } else {
        real_sh[tid] = F::new(0.0_f32);
        imag_sh[tid] = F::new(0.0_f32);
    }
    sync_cube();

    if tid == 0usize {
        let mut real_acc = F::new(0.0_f32);
        let mut imag_acc = F::new(0.0_f32);
        for j in 0..256usize {
            real_acc += real_sh[j];
            imag_acc += imag_sh[j];
        }
        block_real[CUBE_POS] = real_acc;
        block_imag[CUBE_POS] = imag_acc;
    }
    sync_cube();
}

/// Level 1 of the hierarchical mean-phase reduction: each 256-thread cube
/// block reduces its slice of `values[i]` into one `f32` partial sum. See the
/// module documentation.
#[cube(launch)]
fn real_sum_reduce<F: Float + CubeElement>(values: &Array<F>, block_sum: &mut Array<F>) {
    let tid = UNIT_POS as usize;
    let i = ABSOLUTE_POS;

    let mut sum_sh = SharedMemory::<F>::new(256usize);

    if i < values.len() {
        sum_sh[tid] = values[i];
    } else {
        sum_sh[tid] = F::new(0.0_f32);
    }
    sync_cube();

    if tid == 0usize {
        let mut acc = F::new(0.0_f32);
        for j in 0..256usize {
            acc += sum_sh[j];
        }
        block_sum[CUBE_POS] = acc;
    }
    sync_cube();
}

/// One Euler evaluation of a band's intra-band Kuramoto/Stuart–Landau
/// derivative and update, given the band's precomputed order parameter
/// `(z_real, z_imag)`.
#[cube(launch)]
fn band_euler_step<F: Float + CubeElement>(
    phase: &Array<F>,
    amp: &Array<F>,
    freq: &Array<F>,
    z_real: F,
    z_imag: F,
    k: F,
    decay: F,
    gamma: F,
    dt: F,
    n_inv: F,
    out_phase: &mut Array<F>,
    out_amp: &mut Array<F>,
    out_freq: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < phase.len() {
        let p = phase[i];
        let a = amp[i];
        let f = freq[i];

        let s = p.sin();
        let c = p.cos();
        let r_sin = z_imag * c - z_real * s;
        let r_cos = z_real * c + z_imag * s;

        let dphi = f + k * r_sin;
        let dr = -decay * a + k * r_cos;
        let dfreq = gamma * k * r_sin * n_inv;

        let two_pi = F::new(core::f32::consts::TAU);
        let new_p_raw = p + dt * dphi;
        out_phase[i] = new_p_raw - (new_p_raw / two_pi).floor() * two_pi;
        out_amp[i] = (a + dt * dr).max(F::new(0.0_f32));
        out_freq[i] = f + dt * dfreq;
    }
}

/// Broadcast the host-computed scalar `modulation` factor across `amp`,
/// clamped to `[amp_min, amp_max]` — the PAC gate applied to a fast band's
/// pre-step amplitude.
#[cube(launch)]
fn pac_gate<F: Float + CubeElement>(
    amp: &Array<F>,
    modulation: F,
    amp_min: F,
    amp_max: F,
    out: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < amp.len() {
        out[i] = (amp[i] * modulation).clamp(amp_min, amp_max);
    }
}

/// Build an [`ArrayArg`] from a [`Handle`] whose length is `n` `f32`s.
///
/// # Safety
///
/// `handle` must refer to a device allocation of at least `n *
/// size_of::<f32>()` bytes. All handles in this module come from
/// `client.create_from_slice` or `client.empty(byte_len)` sized to exactly
/// `n * size_of::<f32>()` bytes.
fn array_arg<R: Runtime>(handle: &Handle, n: usize) -> ArrayArg<R> {
    // SAFETY: see function-level safety note.
    unsafe { ArrayArg::from_raw_parts(handle.clone(), n) }
}

/// Read one `f32` buffer back from the device.
fn read_f32s<R: Runtime>(
    client: &ComputeClient<R>,
    handle: &Handle,
) -> Result<Vec<f32>, DiscreteStepError> {
    let bytes = client
        .read_one(handle.clone())
        .map_err(|_| DiscreteStepError::BackendReadError)?;
    Ok(f32::from_bytes(&bytes).to_vec())
}

/// Compute a band's order parameter via the hierarchical device reduction,
/// finished with an `f64` accumulator on the host.
fn complex_order_reduce_device<R: Runtime>(
    client: &ComputeClient<R>,
    phase_h: &Handle,
    amp_h: &Handle,
    n: usize,
) -> Result<(f32, f32), DiscreteStepError> {
    let num_blocks = num_blocks_for(n);
    let block_real_h = client.empty(num_blocks * core::mem::size_of::<f32>());
    let block_imag_h = client.empty(num_blocks * core::mem::size_of::<f32>());

    complex_order_reduce::launch::<f32, R>(
        client,
        CubeCount::Static(num_blocks as u32, 1, 1),
        CubeDim::new_1d(256),
        array_arg(phase_h, n),
        array_arg(amp_h, n),
        array_arg(&block_real_h, num_blocks),
        array_arg(&block_imag_h, num_blocks),
    );

    let block_real = read_f32s(client, &block_real_h)?;
    let block_imag = read_f32s(client, &block_imag_h)?;
    let mut real_sum = 0.0_f64;
    let mut imag_sum = 0.0_f64;
    for (&r, &im) in block_real.iter().zip(&block_imag) {
        real_sum += f64::from(r);
        imag_sum += f64::from(im);
    }
    let n_inv = 1.0_f64 / n as f64;
    Ok(((real_sum * n_inv) as f32, (imag_sum * n_inv) as f32))
}

/// Compute `mean(values)` via the hierarchical device reduction, finished
/// with an `f64` accumulator on the host.
fn real_mean_reduce_device<R: Runtime>(
    client: &ComputeClient<R>,
    values_h: &Handle,
    n: usize,
) -> Result<f32, DiscreteStepError> {
    let num_blocks = num_blocks_for(n);
    let block_sum_h = client.empty(num_blocks * core::mem::size_of::<f32>());

    real_sum_reduce::launch::<f32, R>(
        client,
        CubeCount::Static(num_blocks as u32, 1, 1),
        CubeDim::new_1d(256),
        array_arg(values_h, n),
        array_arg(&block_sum_h, num_blocks),
    );

    let block_sums = read_f32s(client, &block_sum_h)?;
    let mut sum = 0.0_f64;
    for &s in &block_sums {
        sum += f64::from(s);
    }
    Ok((sum / n as f64) as f32)
}

/// Launch one band's Euler-step kernel.
#[allow(clippy::too_many_arguments)]
fn launch_band_euler_step<R: Runtime>(
    client: &ComputeClient<R>,
    phase_h: &Handle,
    amp_h: &Handle,
    freq_h: &Handle,
    zr: f32,
    zi: f32,
    band: &BandStepParams,
    dt: f32,
    n_inv: f32,
    out_phase_h: &Handle,
    out_amp_h: &Handle,
    out_freq_h: &Handle,
    n: usize,
) {
    band_euler_step::launch::<f32, R>(
        client,
        CubeCount::Static(n.div_ceil(256).max(1) as u32, 1, 1),
        CubeDim::new_1d(256),
        array_arg(phase_h, n),
        array_arg(amp_h, n),
        array_arg(freq_h, n),
        zr,
        zi,
        band.k,
        band.decay,
        band.gamma,
        dt,
        n_inv,
        array_arg(out_phase_h, n),
        array_arg(out_amp_h, n),
        array_arg(out_freq_h, n),
    );
}

/// Execute one fused three-band discrete step on a CubeCL runtime.
///
/// See [`super`] and this module's documentation for the algorithm and
/// launch sequence.
///
/// # Errors
///
/// Returns [`DiscreteStepError`] on invalid inputs/parameters, a device
/// read-back failure, or a profiling failure.
pub fn discrete_step_cubecl<R: Runtime>(
    client: &ComputeClient<R>,
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<StepCubeclOutput, DiscreteStepError> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_bands(band_sizes, n)?;
    validate_params(params)?;

    let offsets = band_offsets(band_sizes);

    let profiled = client.profile(
        move || -> Result<super::DiscreteStepOutput, DiscreteStepError> {
            // Band 0 (delta): no incoming PAC gate.
            let n_delta = band_sizes[DELTA];
            let d_r = offsets[DELTA]..offsets[DELTA] + n_delta;
            let delta_phase_h = client.create_from_slice(f32::as_bytes(&phase[d_r.clone()]));
            let delta_amp_h = client.create_from_slice(f32::as_bytes(&amplitude[d_r.clone()]));
            let delta_freq_h = client.create_from_slice(f32::as_bytes(&frequency[d_r.clone()]));

            let (zr, zi) =
                complex_order_reduce_device(client, &delta_phase_h, &delta_amp_h, n_delta)?;

            let delta_out_phase_h = client.empty(n_delta * core::mem::size_of::<f32>());
            let delta_out_amp_h = client.empty(n_delta * core::mem::size_of::<f32>());
            let delta_out_freq_h = client.empty(n_delta * core::mem::size_of::<f32>());
            launch_band_euler_step(
                client,
                &delta_phase_h,
                &delta_amp_h,
                &delta_freq_h,
                zr,
                zi,
                &params.bands[DELTA],
                params.dt,
                1.0 / n_delta as f32,
                &delta_out_phase_h,
                &delta_out_amp_h,
                &delta_out_freq_h,
                n_delta,
            );

            let mut out_phase_parts = vec![read_f32s(client, &delta_out_phase_h)?];
            let mut out_amp_parts = vec![read_f32s(client, &delta_out_amp_h)?];
            let mut out_freq_parts = vec![read_f32s(client, &delta_out_freq_h)?];

            let mut prev_out_phase_h = delta_out_phase_h;
            let mut prev_n = n_delta;

            for pair in 0..2 {
                let slow = pair;
                let fast = pair + 1;
                let n_fast = band_sizes[fast];
                let f_r = offsets[fast]..offsets[fast] + n_fast;

                let mean_slow_new_phase =
                    real_mean_reduce_device(client, &prev_out_phase_h, prev_n)?;
                let modulation = 1.0_f32
                    + params.pac[slow].modulation_depth
                        * (mean_slow_new_phase + params.pac[slow].phase_offset).cos();

                let fast_amp_h = client.create_from_slice(f32::as_bytes(&amplitude[f_r.clone()]));
                let gated_amp_h = client.empty(n_fast * core::mem::size_of::<f32>());
                pac_gate::launch::<f32, R>(
                    client,
                    CubeCount::Static(n_fast.div_ceil(256).max(1) as u32, 1, 1),
                    CubeDim::new_1d(256),
                    array_arg(&fast_amp_h, n_fast),
                    modulation,
                    params.amp_min,
                    params.amp_max,
                    array_arg(&gated_amp_h, n_fast),
                );

                let fast_phase_h = client.create_from_slice(f32::as_bytes(&phase[f_r.clone()]));
                let fast_freq_h = client.create_from_slice(f32::as_bytes(&frequency[f_r.clone()]));
                let (zr, zi) =
                    complex_order_reduce_device(client, &fast_phase_h, &gated_amp_h, n_fast)?;

                let fast_out_phase_h = client.empty(n_fast * core::mem::size_of::<f32>());
                let fast_out_amp_h = client.empty(n_fast * core::mem::size_of::<f32>());
                let fast_out_freq_h = client.empty(n_fast * core::mem::size_of::<f32>());
                launch_band_euler_step(
                    client,
                    &fast_phase_h,
                    &gated_amp_h,
                    &fast_freq_h,
                    zr,
                    zi,
                    &params.bands[fast],
                    params.dt,
                    1.0 / n_fast as f32,
                    &fast_out_phase_h,
                    &fast_out_amp_h,
                    &fast_out_freq_h,
                    n_fast,
                );

                out_phase_parts.push(read_f32s(client, &fast_out_phase_h)?);
                out_amp_parts.push(read_f32s(client, &fast_out_amp_h)?);
                out_freq_parts.push(read_f32s(client, &fast_out_freq_h)?);

                prev_out_phase_h = fast_out_phase_h;
                prev_n = n_fast;
            }

            Ok((
                out_phase_parts.concat(),
                out_amp_parts.concat(),
                out_freq_parts.concat(),
            ))
        },
        "discrete_step",
    );

    let (result, profile_duration) = profiled.map_err(|e| DiscreteStepError::ProfilingFailed {
        message: e.to_string(),
    })?;
    let out = result?;

    let timing_method = if profile_duration.timing_method() == CubeclTimingMethod::Device {
        TimingMethod::Device
    } else {
        TimingMethod::System
    };
    let ticks = cubecl::future::block_on(profile_duration.resolve());

    let report = StepReport {
        backend_name: R::name(client).to_string(),
        wall_time_seconds: ticks.duration().as_secs_f64(),
        timing_method,
        launch_count: 10,
    };

    Ok((out, report))
}

#[cfg(feature = "wgpu")]
/// Run the fused discrete step on the wgpu runtime.
pub fn try_discrete_step_wgpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<StepCubeclOutput, DiscreteStepError> {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = WgpuDevice::DefaultDevice;
        WgpuRuntime::client(&device)
    }))
    .map_err(|_| DiscreteStepError::BackendUnavailable { name: "wgpu" })?;
    discrete_step_cubecl(&client, phase, amplitude, frequency, band_sizes, params)
}

#[cfg(feature = "cpu")]
/// Run the fused discrete step on the CubeCL CPU runtime.
pub fn try_discrete_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<StepCubeclOutput, DiscreteStepError> {
    use cubecl::cpu::{CpuDevice, CpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CpuDevice;
        CpuRuntime::client(&device)
    }))
    .map_err(|_| DiscreteStepError::BackendUnavailable { name: "cpu" })?;
    discrete_step_cubecl(&client, phase, amplitude, frequency, band_sizes, params)
}

#[cfg(feature = "cuda")]
/// Run the fused discrete step on the CUDA runtime.
pub fn try_discrete_step_cuda(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<StepCubeclOutput, DiscreteStepError> {
    use cubecl::cuda::{CudaDevice, CudaRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CudaDevice::default();
        CudaRuntime::client(&device)
    }))
    .map_err(|_| DiscreteStepError::BackendUnavailable { name: "cuda" })?;
    discrete_step_cubecl(&client, phase, amplitude, frequency, band_sizes, params)
}

/// Automatically select the best available backend and execute one fused
/// discrete step.
///
/// Tries each backend from [`auto_detect_order`](crate::backend::auto_detect_order)
/// in priority order (CUDA → wgpu → CPU). Falls back to the native CPU
/// reference [`super::discrete_step_cpu`] if no CubeCL backend is available.
pub fn discrete_step_auto(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<StepCubeclOutput, DiscreteStepError> {
    #[cfg(feature = "wgpu")]
    if let Ok(output) = try_discrete_step_wgpu(phase, amplitude, frequency, band_sizes, params) {
        return Ok(output);
    }

    #[cfg(feature = "cuda")]
    if let Ok(output) = try_discrete_step_cuda(phase, amplitude, frequency, band_sizes, params) {
        return Ok(output);
    }

    #[cfg(feature = "cpu")]
    if let Ok(output) = try_discrete_step_cpu(phase, amplitude, frequency, band_sizes, params) {
        return Ok(output);
    }

    let start = std::time::Instant::now();
    let out = super::discrete_step_cpu(phase, amplitude, frequency, band_sizes, params)?;
    let report = StepReport {
        backend_name: "cpu-native".to_string(),
        wall_time_seconds: start.elapsed().as_secs_f64(),
        timing_method: TimingMethod::System,
        launch_count: 0,
    };
    Ok((out, report))
}

#[cfg(all(test, feature = "wgpu"))]
mod tests {
    use super::*;
    use crate::discrete_step::{discrete_step_cpu, BandStepParams, PacGateParams};

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    fn default_params() -> DiscreteStepParams {
        DiscreteStepParams {
            bands: [
                BandStepParams {
                    k: 1.0,
                    decay: 0.1,
                    gamma: 0.01,
                },
                BandStepParams {
                    k: 1.5,
                    decay: 0.15,
                    gamma: 0.005,
                },
                BandStepParams {
                    k: 0.5,
                    decay: 0.2,
                    gamma: 0.0,
                },
            ],
            pac: [
                PacGateParams {
                    modulation_depth: 0.3,
                    phase_offset: 0.0,
                },
                PacGateParams {
                    modulation_depth: 0.4,
                    phase_offset: 0.2,
                },
            ],
            amp_min: 1e-6,
            amp_max: 10.0,
            dt: 0.01,
        }
    }

    fn make_state(band_sizes: [usize; 3]) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
        let n: usize = band_sizes.iter().sum();
        let phase: Vec<_> = (0..n)
            .map(|i| (0.05 * i as f32).rem_euclid(core::f32::consts::TAU))
            .collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
        (phase, amplitude, frequency)
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_small_n() {
        let band_sizes = [8usize, 16, 32];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_discrete_step_wgpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        assert_eq!(report.backend_name, "wgpu<wgsl>");
        assert_eq!(report.launch_count, 10);
        assert!(report.wall_time_seconds >= 0.0);
        eprintln!("band_sizes={band_sizes:?} wgpu discrete-step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_non_block_aligned_bands() {
        // None of the three band sizes are multiples of 256, exercising the
        // partial-last-block mask in every reduction kernel.
        let band_sizes = [300usize, 777, 513];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_discrete_step_wgpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        eprintln!("band_sizes={band_sizes:?} wgpu discrete-step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_at_large_n() {
        let band_sizes = [2_048usize, 16_384, 65_536];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_discrete_step_wgpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        eprintln!("band_sizes={band_sizes:?} wgpu discrete-step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_rejects_mismatched_lengths() {
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let err =
            try_discrete_step_wgpu(&phase, &amp, &freq, [1, 1, 2], &default_params()).unwrap_err();
        assert!(matches!(err, DiscreteStepError::LengthMismatch { .. }));
    }

    #[test]
    fn wgpu_rejects_empty_band() {
        let (phase, amp, freq) = make_state([1, 1, 1]);
        let err =
            try_discrete_step_wgpu(&phase, &amp, &freq, [0, 1, 2], &default_params()).unwrap_err();
        assert!(matches!(err, DiscreteStepError::EmptyBand { band: 0 }));
    }

    #[test]
    fn wgpu_rejects_non_positive_dt() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.dt = -0.01;
        let err = try_discrete_step_wgpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::InvalidParameter { name: "dt", .. }
        ));
    }

    #[test]
    fn wgpu_returns_typed_error_when_backend_unavailable() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        match try_discrete_step_wgpu(&phase, &amp, &freq, [2, 2, 2], &default_params()) {
            Ok(_) | Err(DiscreteStepError::BackendUnavailable { .. }) => {}
            Err(e) => panic!("unexpected wgpu error: {e}"),
        }
    }
}

#[cfg(all(test, feature = "cpu"))]
mod tests_cpu {
    use super::*;
    use crate::discrete_step::{discrete_step_cpu, BandStepParams, PacGateParams};

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    fn default_params() -> DiscreteStepParams {
        DiscreteStepParams {
            bands: [
                BandStepParams {
                    k: 1.0,
                    decay: 0.1,
                    gamma: 0.01,
                },
                BandStepParams {
                    k: 1.5,
                    decay: 0.15,
                    gamma: 0.005,
                },
                BandStepParams {
                    k: 0.5,
                    decay: 0.2,
                    gamma: 0.0,
                },
            ],
            pac: [
                PacGateParams {
                    modulation_depth: 0.3,
                    phase_offset: 0.0,
                },
                PacGateParams {
                    modulation_depth: 0.4,
                    phase_offset: 0.2,
                },
            ],
            amp_min: 1e-6,
            amp_max: 10.0,
            dt: 0.01,
        }
    }

    fn make_state(band_sizes: [usize; 3]) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
        let n: usize = band_sizes.iter().sum();
        let phase: Vec<_> = (0..n)
            .map(|i| (0.05 * i as f32).rem_euclid(core::f32::consts::TAU))
            .collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
        (phase, amplitude, frequency)
    }

    #[test]
    fn cpu_backend_matches_cpu_reference_multi_block() {
        // N=600 per band forces multiple 256-thread cube blocks in every
        // reduction, exercising the partial last-block mask.
        let band_sizes = [600usize, 600, 600];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((out_p, out_a, out_f), report) =
            try_discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        assert_eq!(report.backend_name, "cpu");
        assert_eq!(report.launch_count, 10);
        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    /// Regression-style coverage for the reductions' multi-block combine:
    /// repeated calls must be deterministic (guards against the class of
    /// data race documented on `order_param_block_reduce`/
    /// `pac_phase_sum_block_reduce`). Reuses a single client across repeats
    /// (matching the `pac::cubecl` precedent) rather than the
    /// catch-unwind-guarded `try_discrete_step_cpu` wrapper, so the test
    /// exercises only the launch sequence's determinism, not per-call device
    /// initialization cost.
    #[test]
    fn cpu_backend_is_deterministic_across_repeated_calls() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let device = CpuDevice;
        let client = CpuRuntime::client(&device);

        let band_sizes = [300usize, 400, 500];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (first_p, first_a, first_f) =
            discrete_step_cubecl(&client, &phase, &amp, &freq, band_sizes, &params)
                .unwrap()
                .0;
        for _ in 0..5 {
            let (p, a, f) = discrete_step_cubecl(&client, &phase, &amp, &freq, band_sizes, &params)
                .unwrap()
                .0;
            assert_eq!(p, first_p);
            assert_eq!(a, first_a);
            assert_eq!(f, first_f);
        }
    }

    #[test]
    fn discrete_step_auto_falls_back_to_available_backend() {
        let band_sizes = [4usize, 4, 4];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (ref_p, ref_a, ref_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((auto_p, auto_a, auto_f), report) =
            discrete_step_auto(&phase, &amp, &freq, band_sizes, &params).unwrap();

        assert_allclose(&auto_p, &ref_p, 1e-5, 1e-6);
        assert_allclose(&auto_a, &ref_a, 1e-5, 1e-6);
        assert_allclose(&auto_f, &ref_f, 1e-5, 1e-6);
        assert!(!report.backend_name.is_empty());
        assert!(report.wall_time_seconds >= 0.0);
    }

    #[test]
    fn cubecl_pool_rejects_size_mismatch_via_population_check() {
        let (phase, amp, freq) = make_state([2, 3, 4]);
        let err =
            try_discrete_step_cpu(&phase, &amp, &freq, [2, 3, 5], &default_params()).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::PopulationMismatch {
                expected: 10,
                got: 9
            }
        ));
    }
}

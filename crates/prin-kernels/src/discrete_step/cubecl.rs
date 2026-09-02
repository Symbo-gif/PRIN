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
//! No buffer pool is used (each step's device handles are created fresh via
//! `client.empty`), matching the precedent set by `sparse_knn`/`pac` (WP-019
//! S1 handoff, "Out-of-scope discoveries") — a future performance WP can add
//! pooling if profiling shows per-call allocation dominating.
//!
//! ## Device-resident dispatch (WP-036E)
//!
//! [`discrete_step_device`] runs the whole sequence on a
//! [`DiscreteStepDeviceState`] whose `(phase, amplitude, frequency)` buffers —
//! held **per band** — stay on the device across steps, so a caller holding
//! CubeCL device handles steps with **no host transfer**.
//! [`discrete_step_cubecl`] is the thin upload→`discrete_step_device`→download
//! wrapper — one algorithm, one implementation (Coding Standards §1). The
//! launch sequence (and `launch_count = 10`) is unchanged: `delta`'s order
//! parameter was already a device reduction, so no stage gained a launch.
//! Per-band standalone buffers (not `offset`-sliced views of one concatenated
//! buffer) are required because wgpu rejects sub-buffer bindings that violate
//! `min_storage_buffer_offset_alignment`.
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `len * size_of::<f32>()` bytes. Those
//! handles are created by `ComputeClient::create_from_slice` or
//! `ComputeClient::empty`, so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use core::marker::PhantomData;

use cubecl::prelude::*;
use cubecl::profile::TimingMethod as CubeclTimingMethod;
use cubecl::server::Handle;

use super::{
    band_offsets, validate_bands, validate_params, validate_state, BandStepParams,
    DiscreteStepError, DiscreteStepParams, DELTA, GAMMA, THETA,
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

/// Device-resident `(phase, amplitude, frequency)` state for the fused
/// three-band discrete step, held **per band** as CubeCL device [`Handle`]s
/// that persist across steps.
///
/// Per-band standalone allocations (rather than `offset`-sliced views of one
/// concatenated buffer) keep every kernel binding at buffer offset 0 — wgpu's
/// `min_storage_buffer_offset_alignment` (32 bytes on DX12) rejects the
/// arbitrary sub-buffer offsets a non-block-aligned band split would need.
///
/// [`discrete_step_device`] reads the base state from here and, on success,
/// replaces the handles with the stepped state.
/// [`DiscreteStepDeviceState::upload`] is the one-shot host→device constructor
/// the thin [`discrete_step_cubecl`] wrapper uses; [`to_host`](Self::to_host)
/// concatenates the bands back slow→fast.
#[derive(Clone, Debug)]
pub struct DiscreteStepDeviceState<R: Runtime> {
    /// Per-band oscillator counts `[delta, theta, gamma]`.
    pub band_sizes: [usize; 3],
    /// Per-band `phase` buffers, indexed by [`DELTA`]/[`THETA`]/[`GAMMA`].
    pub phase: [Handle; 3],
    /// Per-band `amplitude` buffers.
    pub amplitude: [Handle; 3],
    /// Per-band `frequency` buffers.
    pub frequency: [Handle; 3],
    runtime: PhantomData<R>,
}

impl<R: Runtime> DiscreteStepDeviceState<R> {
    /// Assemble a device state from per-band buffers the caller already holds
    /// on the device (no transfer).
    pub fn from_parts(
        band_sizes: [usize; 3],
        phase: [Handle; 3],
        amplitude: [Handle; 3],
        frequency: [Handle; 3],
    ) -> Self {
        Self {
            band_sizes,
            phase,
            amplitude,
            frequency,
            runtime: PhantomData,
        }
    }

    /// Total oscillator count `N` (sum of the three band sizes).
    pub fn n(&self) -> usize {
        self.band_sizes.iter().sum()
    }

    /// Upload the concatenated slow→fast host state, splitting it into the
    /// three per-band device buffers.
    pub fn upload(
        client: &ComputeClient<R>,
        phase: &[f32],
        amplitude: &[f32],
        frequency: &[f32],
        band_sizes: [usize; 3],
    ) -> Self {
        let offsets = band_offsets(band_sizes);
        let split = |src: &[f32]| {
            [DELTA, THETA, GAMMA].map(|b| {
                client
                    .create_from_slice(f32::as_bytes(&src[offsets[b]..offsets[b] + band_sizes[b]]))
            })
        };
        Self {
            band_sizes,
            phase: split(phase),
            amplitude: split(amplitude),
            frequency: split(frequency),
            runtime: PhantomData,
        }
    }

    /// Download the current state, concatenated slow→fast.
    ///
    /// # Errors
    ///
    /// Returns [`DiscreteStepError::BackendReadError`] on a device read-back
    /// failure.
    pub fn to_host(
        &self,
        client: &ComputeClient<R>,
    ) -> Result<super::DiscreteStepOutput, DiscreteStepError> {
        let cat = |hs: &[Handle; 3]| -> Result<Vec<f32>, DiscreteStepError> {
            let mut v = Vec::with_capacity(self.n());
            for h in hs {
                v.extend_from_slice(&read_f32s(client, h)?);
            }
            Ok(v)
        };
        Ok((
            cat(&self.phase)?,
            cat(&self.amplitude)?,
            cat(&self.frequency)?,
        ))
    }
}

/// Execute one fused three-band discrete step on device-resident buffers, with
/// **no host transfer** — one algorithm, one implementation (Coding Standards
/// §1): [`discrete_step_cubecl`] is the thin upload→this→download wrapper.
///
/// On success `state`'s per-band handles are replaced with the stepped state.
/// Each band reads its own input handles and writes freshly allocated output
/// handles (input and output never alias). The `#[cube]` kernels and the
/// 10-launch sequence are byte-for-byte those the host-slice path launches.
///
/// # Errors
///
/// Returns [`DiscreteStepError`] on invalid `band_sizes`/parameters, a device
/// read-back failure inside a reduction, or a profiling failure.
pub fn discrete_step_device<R: Runtime>(
    client: &ComputeClient<R>,
    state: &mut DiscreteStepDeviceState<R>,
    params: &DiscreteStepParams,
) -> Result<StepReport, DiscreteStepError> {
    let band_sizes = state.band_sizes;
    validate_bands(band_sizes, state.n())?;
    validate_params(params)?;

    let in_phase = state.phase.clone();
    let in_amp = state.amplitude.clone();
    let in_freq = state.frequency.clone();

    let elem = core::mem::size_of::<f32>();
    let out_phase: [Handle; 3] = band_sizes.map(|nb| client.empty(nb * elem));
    let out_amp: [Handle; 3] = band_sizes.map(|nb| client.empty(nb * elem));
    let out_freq: [Handle; 3] = band_sizes.map(|nb| client.empty(nb * elem));
    let fin_phase = out_phase.clone();
    let fin_amp = out_amp.clone();
    let fin_freq = out_freq.clone();

    let profiled = client.profile(
        move || -> Result<(), DiscreteStepError> {
            // Band 0 (delta): no incoming PAC gate.
            let n_delta = band_sizes[DELTA];
            let (zr, zi) =
                complex_order_reduce_device(client, &in_phase[DELTA], &in_amp[DELTA], n_delta)?;
            launch_band_euler_step(
                client,
                &in_phase[DELTA],
                &in_amp[DELTA],
                &in_freq[DELTA],
                zr,
                zi,
                &params.bands[DELTA],
                params.dt,
                1.0 / n_delta as f32,
                &fin_phase[DELTA],
                &fin_amp[DELTA],
                &fin_freq[DELTA],
                n_delta,
            );

            let mut prev_out_phase = fin_phase[DELTA].clone();
            let mut prev_n = n_delta;

            for pair in 0..2 {
                let slow = pair;
                let fast = pair + 1;
                let n_fast = band_sizes[fast];

                let mean_slow_new_phase = real_mean_reduce_device(client, &prev_out_phase, prev_n)?;
                let modulation = 1.0_f32
                    + params.pac[slow].modulation_depth
                        * (mean_slow_new_phase + params.pac[slow].phase_offset).cos();

                let gated_amp_h = client.empty(n_fast * elem);
                pac_gate::launch::<f32, R>(
                    client,
                    CubeCount::Static(n_fast.div_ceil(256).max(1) as u32, 1, 1),
                    CubeDim::new_1d(256),
                    array_arg(&in_amp[fast], n_fast),
                    modulation,
                    params.amp_min,
                    params.amp_max,
                    array_arg(&gated_amp_h, n_fast),
                );

                let (zr, zi) =
                    complex_order_reduce_device(client, &in_phase[fast], &gated_amp_h, n_fast)?;
                launch_band_euler_step(
                    client,
                    &in_phase[fast],
                    &gated_amp_h,
                    &in_freq[fast],
                    zr,
                    zi,
                    &params.bands[fast],
                    params.dt,
                    1.0 / n_fast as f32,
                    &fin_phase[fast],
                    &fin_amp[fast],
                    &fin_freq[fast],
                    n_fast,
                );

                prev_out_phase = fin_phase[fast].clone();
                prev_n = n_fast;
            }

            Ok(())
        },
        "discrete_step",
    );

    let (result, profile_duration) = profiled.map_err(|e| DiscreteStepError::ProfilingFailed {
        message: e.to_string(),
    })?;
    result?;

    let timing_method = if profile_duration.timing_method() == CubeclTimingMethod::Device {
        TimingMethod::Device
    } else {
        TimingMethod::System
    };
    let ticks = cubecl::future::block_on(profile_duration.resolve());

    state.phase = out_phase;
    state.amplitude = out_amp;
    state.frequency = out_freq;

    Ok(StepReport {
        backend_name: R::name(client).to_string(),
        wall_time_seconds: ticks.duration().as_secs_f64(),
        timing_method,
        launch_count: 10,
    })
}

/// Execute one fused three-band discrete step on a CubeCL runtime.
///
/// Thin host-slice wrapper: uploads the concatenated `(phase, amplitude,
/// frequency)` state, runs [`discrete_step_device`], and downloads the
/// stepped state. Behaviour is identical to the pre-WP-036E per-call path.
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

    let mut state =
        DiscreteStepDeviceState::upload(client, phase, amplitude, frequency, band_sizes);
    let report = discrete_step_device(client, &mut state, params)?;
    let out = state.to_host(client)?;
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
    #[cfg(feature = "cuda")]
    if let Ok(output) = try_discrete_step_cuda(phase, amplitude, frequency, band_sizes, params) {
        return Ok(output);
    }

    #[cfg(feature = "wgpu")]
    if let Ok(output) = try_discrete_step_wgpu(phase, amplitude, frequency, band_sizes, params) {
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

    /// wgpu kernel-equivalence for `discrete_step_device` (WP-036E S1) against
    /// the CPU reference, at non-block-aligned band sizes.
    #[test]
    fn wgpu_device_dispatch_matches_cpu_reference() {
        use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
        use std::panic::{catch_unwind, AssertUnwindSafe};

        let Ok(client) = catch_unwind(AssertUnwindSafe(|| {
            WgpuRuntime::client(&WgpuDevice::DefaultDevice)
        })) else {
            return; // No wgpu adapter — `_auto` covers the fallback.
        };

        let band_sizes = [300usize, 777, 513];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        let mut state = DiscreteStepDeviceState::<WgpuRuntime>::upload(
            &client, &phase, &amp, &freq, band_sizes,
        );
        let report = discrete_step_device(&client, &mut state, &params).unwrap();
        assert_eq!(report.launch_count, 10);
        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();

        assert_allclose(&dev_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&dev_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&dev_f, &cpu_f, 1e-5, 1e-6);
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

    /// Kernel-equivalence for the device-`Handle` entry point (WP-036E S1):
    /// `discrete_step_device` on a per-band device-resident state, across a
    /// multi-step loop (`to_host` only at the end), vs the CPU reference. Band
    /// sizes are non-block-aligned.
    #[test]
    fn device_dispatch_matches_cpu_reference_across_a_stepping_loop() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let client = CpuRuntime::client(&CpuDevice);

        let band_sizes = [300usize, 400, 500];
        let (mut phase, mut amp, mut freq) = make_state(band_sizes);
        let params = default_params();

        let mut state =
            DiscreteStepDeviceState::<CpuRuntime>::upload(&client, &phase, &amp, &freq, band_sizes);

        for step in 0..4 {
            let report = discrete_step_device(&client, &mut state, &params).unwrap();
            assert_eq!(report.launch_count, 10, "step {step}");
            let (rp, ra, rf) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
            (phase, amp, freq) = (rp, ra, rf);
        }

        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();
        assert_allclose(&dev_p, &phase, 1e-5, 1e-6);
        assert_allclose(&dev_a, &amp, 1e-5, 1e-6);
        assert_allclose(&dev_f, &freq, 1e-5, 1e-6);

        // The re-expressed host wrapper agrees bit-for-bit with one device step.
        let (p0, a0, f0) = make_state(band_sizes);
        let mut one =
            DiscreteStepDeviceState::<CpuRuntime>::upload(&client, &p0, &a0, &f0, band_sizes);
        discrete_step_device(&client, &mut one, &params).unwrap();
        let one_host = one.to_host(&client).unwrap();
        let ((wp, wa, wf), _) =
            discrete_step_cubecl(&client, &p0, &a0, &f0, band_sizes, &params).unwrap();
        assert_eq!((wp, wa, wf), one_host);
    }

    #[test]
    fn device_dispatch_rejects_bad_bands_and_params() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let client = CpuRuntime::client(&CpuDevice);

        // Population mismatch is caught by the host wrapper before upload.
        let (phase, amp, freq) = make_state([4, 4, 4]);
        let err = discrete_step_cubecl(&client, &phase, &amp, &freq, [4, 4, 5], &default_params())
            .unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::PopulationMismatch {
                expected: 13,
                got: 12
            }
        ));

        // A non-finite parameter is caught by `discrete_step_device` itself.
        let mut state =
            DiscreteStepDeviceState::<CpuRuntime>::upload(&client, &phase, &amp, &freq, [4, 4, 4]);
        let mut bad = default_params();
        bad.dt = -1.0;
        let err = discrete_step_device(&client, &mut state, &bad).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::InvalidParameter { name: "dt", .. }
        ));
    }

    /// `DiscreteStepDeviceState::from_parts` adopts caller-held per-band
    /// handle triples with no transfer: rebuilt from another state's handles
    /// it reads back byte-identical (slow→fast concatenation).
    #[test]
    fn device_state_from_parts_adopts_per_band_handles() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let client = CpuRuntime::client(&CpuDevice);

        let band_sizes = [3usize, 5, 7];
        let (phase, amp, freq) = make_state(band_sizes);
        let uploaded =
            DiscreteStepDeviceState::<CpuRuntime>::upload(&client, &phase, &amp, &freq, band_sizes);

        let adopted = DiscreteStepDeviceState::<CpuRuntime>::from_parts(
            band_sizes,
            uploaded.phase.clone(),
            uploaded.amplitude.clone(),
            uploaded.frequency.clone(),
        );
        assert_eq!(adopted.n(), 15);

        let (p, a, f) = adopted.to_host(&client).unwrap();
        assert_eq!(p, phase);
        assert_eq!(a, amp);
        assert_eq!(f, freq);
    }
}

#[cfg(all(test, feature = "cuda"))]
mod tests_cuda {
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

    /// First CUDA kernel-equivalence evidence for the fused discrete step
    /// (WP-021): previously this backend was compile-only (DV-001/DV-005 —
    /// no CUDA hardware on the CI/dev hosts of record). This host has a
    /// working CUDA device, so this closes the equivalence gap for real.
    #[test]
    fn cuda_backend_matches_cpu_reference_multi_block() {
        let band_sizes = [600usize, 600, 600];
        let (phase, amp, freq) = make_state(band_sizes);
        let params = default_params();

        let (cpu_p, cpu_a, cpu_f) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        let ((out_p, out_a, out_f), report) =
            try_discrete_step_cuda(&phase, &amp, &freq, band_sizes, &params).unwrap();

        assert_eq!(report.backend_name, "cuda");
        assert_eq!(report.launch_count, 10);
        eprintln!("N={} cuda discrete-step report: {report:?}", phase.len());
        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cuda_backend_rejects_population_mismatch() {
        let (phase, amp, freq) = make_state([2, 3, 4]);
        let err =
            try_discrete_step_cuda(&phase, &amp, &freq, [2, 3, 5], &default_params()).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::PopulationMismatch {
                expected: 10,
                got: 9
            }
        ));
    }

    /// CUDA kernel-equivalence for `discrete_step_device` (WP-036E S1): a
    /// per-band device-resident state, `to_host` only at the end of a
    /// multi-step loop.
    #[test]
    fn cuda_device_dispatch_matches_cpu_reference_across_a_stepping_loop() {
        use cubecl::cuda::{CudaDevice, CudaRuntime};
        let client = CudaRuntime::client(&CudaDevice::default());

        let band_sizes = [600usize, 700, 800];
        let (mut phase, mut amp, mut freq) = make_state(band_sizes);
        let params = default_params();

        let mut state = DiscreteStepDeviceState::<CudaRuntime>::upload(
            &client, &phase, &amp, &freq, band_sizes,
        );

        for _ in 0..3 {
            let report = discrete_step_device(&client, &mut state, &params).unwrap();
            assert_eq!(report.launch_count, 10);
            let (rp, ra, rf) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
            (phase, amp, freq) = (rp, ra, rf);
        }

        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();
        assert_allclose(&dev_p, &phase, 1e-5, 1e-6);
        assert_allclose(&dev_a, &amp, 1e-5, 1e-6);
        assert_allclose(&dev_f, &freq, 1e-5, 1e-6);
    }
}

#[cfg(all(test, feature = "cuda", feature = "wgpu"))]
mod tests_priority {
    use super::*;
    use crate::discrete_step::{BandStepParams, PacGateParams};

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

    /// Regression test for the WP-021 dispatch-priority fix: `discrete_step_auto`
    /// must select CUDA before wgpu when both are available, matching
    /// `backend::auto_detect_order()`'s documented CUDA > wgpu > CPU priority
    /// (previously the function tried wgpu first, so CUDA was silently
    /// unreachable through auto-dispatch on any host with both backends).
    #[test]
    fn discrete_step_auto_prefers_cuda_over_wgpu_when_both_available() {
        let band_sizes = [8usize, 8, 8];
        let n: usize = band_sizes.iter().sum();
        let phase: Vec<_> = (0..n).map(|i| 0.05 * i as f32).collect();
        let amp: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let freq: Vec<_> = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        let params = default_params();

        try_discrete_step_cuda(&phase, &amp, &freq, band_sizes, &params)
            .expect("this test requires a working CUDA backend on the host");

        let (_, report) = discrete_step_auto(&phase, &amp, &freq, band_sizes, &params).unwrap();
        assert_eq!(report.backend_name, "cuda");
    }
}

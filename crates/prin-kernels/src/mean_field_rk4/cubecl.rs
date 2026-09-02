//! Single-source CubeCL implementation of the mean-field RK4 step.
//!
//! This module is enabled by the `cuda` or `wgpu` features. It contains the
//! `#[cube]` kernels and the runtime launch code. The CPU reference in
//! [`super::step_cpu`] remains the numerical authority; this path is checked
//! against it in the kernel-equivalence tests.
//!
//! ## Device-resident dispatch (WP-036E)
//!
//! [`step_cubecl_device`] runs the whole 4-stage sequence on a
//! [`MeanFieldDeviceState`] whose `(phase, amplitude, frequency)` buffers stay
//! on the device across steps — a caller holding CubeCL device handles steps
//! with **no host transfer**. [`step_cubecl_with_pool`] and [`step_cubecl`]
//! are the thin host-slice wrappers over it (upload → `step_cubecl_device` →
//! download); one algorithm, one implementation (Coding Standards §1). Because
//! the device path has no host-resident input slice for stage 1, stage 1 takes
//! its order parameter from the same device reduction stages 2–4 use, so the
//! step dispatches **9** launches, not 8 — see [`StepReport::launch_count`].
//!
//! ## Hierarchical device-side order-parameter reduction
//!
//! Each RK4 stage needs the mean-field order parameter `Z` of the
//! *intermediate* state produced by the previous stage. Prior to WP-018, that
//! intermediate state was read back to the host in full (three `N`-length
//! buffers) so the host could recompute `Z` with `super::order_param` — an
//! `O(N)` host round-trip on every one of the three interior stages.
//! `order_param_block_reduce` replaces that with a two-level hierarchical
//! reduction:
//!
//! 1. **Device (level 1):** each 256-thread cube block reduces its slice of
//!    `amp[i] * e^{i*phase[i]}` terms into one `(real, imag)` `f32` partial
//!    sum via shared memory — `ceil(N / 256)` pairs total.
//! 2. **Host (level 2):** the host reads back only those `ceil(N / 256)`
//!    pairs (not the full state) and finishes the reduction with an `f64`
//!    accumulator (Coding Standards §2.2), matching the CPU reference
//!    algorithm. Neither this project's local wgpu backend (DX12; `f64` is
//!    gated behind the Vulkan-only, opt-in `SHADER_F64` feature) nor most
//!    consumer GPUs expose a portable device-side `f64`, so the numerically
//!    sensitive final accumulation runs on the host, which always has real
//!    IEEE 754 double-precision hardware.
//!
//! This keeps the per-stage host transfer at `O(N / 256)` instead of `O(N)`
//! and eliminates the wasted `frequency` read-back the pre-WP-018 prototype
//! performed (order parameter only ever depends on phase and amplitude).
//!
//! ## Device-event timing
//!
//! [`step_cubecl_with_pool`] wraps the whole launch sequence in
//! `ComputeClient::profile`, which uses hardware device timestamps where the
//! backend supports them (Benchmarking and Reproducibility Standards §2.2:
//! "GPU timing uses device-side events/synchronization, never wall-clock
//! around async launches"). [`StepReport::timing_method`] records whether the
//! reported [`StepReport::wall_time_seconds`] came from real device events
//! ([`TimingMethod::Device`]) or a host wall-clock fallback
//! ([`TimingMethod::System`], used by backends with no device timers, e.g.
//! the CubeCL CPU runtime).
//!
//! ## Buffer management
//!
//! [`step_cubecl_with_pool`] and [`step_cubecl_device`] reuse preallocated
//! device [`Handle`]s from a [`CubeclBufferPool`] (k1–k4, stage, the zeroed
//! `k_zero`, and the reduction partials), eliminating per-step
//! `client.empty()` calls for the working set. The device path allocates only
//! the three finalize-output handles per step (moved into the
//! [`MeanFieldDeviceState`]); the host-slice path additionally uploads the
//! base state each call. The original [`step_cubecl`] allocates a fresh pool
//! per call and is retained for one-shot use.
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `len * size_of::<f32>()` bytes. Those
//! handles are created by `ComputeClient::create` or `ComputeClient::empty`,
//! so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use core::marker::PhantomData;

use cubecl::prelude::*;
use cubecl::profile::TimingMethod as CubeclTimingMethod;
use cubecl::server::Handle;

use super::{step_cpu, validate_param, validate_state, MeanFieldRk4Error, MeanFieldRk4Params};
use crate::buffers::CubeclBufferPool;

/// Full CubeCL step output: `(phase, amplitude, frequency)` plus a report.
pub type StepCubeclOutput = (super::MeanFieldRk4Output, StepReport);

/// How [`StepReport::wall_time_seconds`] was measured.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TimingMethod {
    /// Hardware device timestamps captured around the kernel-launch sequence
    /// via `ComputeClient::profile` — accurate GPU execution time.
    Device,
    /// Host wall-clock fallback, used when the backend has no device-side
    /// timers (e.g. the CubeCL CPU runtime, or a wgpu adapter without
    /// timestamp-query support).
    System,
}

impl core::fmt::Display for TimingMethod {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            TimingMethod::Device => f.write_str("device"),
            TimingMethod::System => f.write_str("system"),
        }
    }
}

/// Scalar timing and backend metadata for one CubeCL step.
#[derive(Clone, Debug, PartialEq)]
pub struct StepReport {
    /// Backend runtime name, e.g. `"wgpu<wgsl>"` or `"cuda"`.
    pub backend_name: String,
    /// Time for the profiled kernel-launch sequence, in seconds.
    ///
    /// When [`Self::timing_method`] is [`TimingMethod::Device`], this comes
    /// from hardware device timestamps captured by `ComputeClient::profile`.
    /// Otherwise it is a host wall-clock fallback. See the module
    /// documentation for details.
    pub wall_time_seconds: f64,
    /// How [`Self::wall_time_seconds`] was measured.
    pub timing_method: TimingMethod,
    /// Number of kernel launches dispatched.
    ///
    /// Since WP-036E the step runs device-resident ([`step_cubecl_device`],
    /// which the host-slice wrappers delegate to), so every stage — stage 1
    /// included — takes its order parameter from a device-side
    /// `order_param_block_reduce` reduction: **9** = 4 RK4 stage kernels + 4
    /// order-parameter reductions (one per stage) + 1 finalize kernel. Before
    /// WP-036E stage 1 read its order parameter from the caller's host slice
    /// and the count was 8. The native-CPU fallback in [`step_auto`] reports
    /// `0` (no kernel launches).
    pub launch_count: u32,
}

/// One RK4 stage: compute the derivative of `s = base + dt_scale * k_prev` and
/// the next intermediate state `s_next = base + next_dt_scale * k`.
///
/// `z_real` and `z_imag` are the order parameter of `s`, computed either from
/// the host-resident input state (stage 1) or by [`order_param_device`]'s
/// hierarchical device-side reduction (stages 2-4).
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

/// Level 1 of the hierarchical order-parameter reduction (see module docs):
/// each 256-thread cube block reduces its slice of `amp[i] * e^{i*phase[i]}`
/// terms into one `(real, imag)` `f32` partial-sum pair, and writes it to
/// `block_real[CUBE_POS]` / `block_imag[CUBE_POS]`. Threads past the end of
/// `phase` (the last block may be partially empty) contribute zero.
///
/// Every thread writes its one term into shared memory, a `sync_cube()`
/// barrier makes all 256 terms visible before thread 0 sums them serially,
/// and a second `sync_cube()` after thread 0's write keeps every thread in
/// the block from racing ahead into the *next* cube block's iteration (the
/// CubeCL CPU runtime schedules cube blocks as sequential iterations of the
/// same 256 persistent worker threads) until that write has actually
/// happened — without it, threads 1..255 have no more work after the first
/// barrier and can start reusing this same shared-memory buffer for the next
/// block while thread 0 is still reading it, a real, observed data race.
/// 256 scalar adds is negligible work on real GPU hardware — the parallel win
/// of this level is the gather from `n` down to `n.div_ceil(256)` partials,
/// not the final in-block combine — and two barriers (instead of an 8-level
/// halving tree, each level needing its own) avoids most of the CubeCL CPU
/// runtime's per-barrier thread-synchronization cost, which otherwise
/// dominates this kernel's `cpu`-feature test runtime.
#[cube(launch)]
fn order_param_block_reduce<F: Float + CubeElement>(
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

/// DV-003: CUDA-only level-2 f64 finalize kernel.
///
/// Takes the `num_blocks` partial-sum pairs from [`order_param_block_reduce`]
/// and accumulates them in `f64` on device, writing the final `(zr, zi)` as
/// `f32` to a 2-element output buffer. This eliminates the host read-back of
/// `2 * num_blocks` f32s per stage — only 2 f32s are read back instead.
///
/// Gated behind `#[cfg(feature = "cuda")]` because device `f64` is not
/// portable: wgpu DX12 lacks `SHADER_F64` (Vulkan-only), and most consumer
/// GPUs don't expose a portable device-side `f64`. The wgpu/CPU path keeps
/// the host `f64` combine in [`order_param_device`].
#[cfg(feature = "cuda")]
#[cube(launch)]
fn order_param_finalize_f64(
    block_real: &Array<f32>,
    block_imag: &Array<f32>,
    out: &mut Array<f32>,
    n_inv: f32,
) {
    if UNIT_POS == 0u32 {
        let mut real_sum: f64 = 0.0;
        let mut imag_sum: f64 = 0.0;
        let len = block_real.len();
        for j in 0..len {
            real_sum += f64::cast_from(block_real[j]);
            imag_sum += f64::cast_from(block_imag[j]);
        }
        let n_inv64 = f64::cast_from(n_inv);
        out[0] = f32::cast_from(real_sum * n_inv64);
        out[1] = f32::cast_from(imag_sum * n_inv64);
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
/// `client.empty(byte_len)`, so the invariant holds. Callers of
/// `step_cubecl_with_pool` are protected by an explicit `pool.capacity() == n`
/// check that runs before any `array_arg` call.
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

/// Compute the mean-field order parameter of a device-resident `(phase, amp)`
/// pair via the two-level hierarchical reduction described in the module
/// documentation: [`order_param_block_reduce`] on the device, finished with
/// an `f64` accumulator.
///
/// ## DV-003: on-device f64 combine (CUDA only)
///
/// On CUDA, the level-2 f64 accumulation runs on device via
/// [`order_param_finalize_f64`] — only 2 f32s `(zr, zi)` are read back
/// instead of `2 * num_blocks` f32s. On wgpu/CPU, the level-2 f64
/// accumulation runs on the host (device `f64` is not portable: wgpu DX12
/// lacks `SHADER_F64`).
#[allow(clippy::too_many_arguments)]
fn order_param_device<R: Runtime>(
    client: &ComputeClient<R>,
    reduce_cube_count: &CubeCount,
    cube_dim: CubeDim,
    phase_h: &Handle,
    amp_h: &Handle,
    block_real_h: &Handle,
    block_imag_h: &Handle,
    num_blocks: usize,
    n: usize,
    n_inv: f32,
) -> Result<(f32, f32), MeanFieldRk4Error> {
    order_param_block_reduce::launch::<f32, R>(
        client,
        reduce_cube_count.clone(),
        cube_dim,
        array_arg(phase_h, n),
        array_arg(amp_h, n),
        array_arg(block_real_h, num_blocks),
        array_arg(block_imag_h, num_blocks),
    );

    // DV-003: on-device f64 finalize on CUDA — read back only 2 f32s.
    #[cfg(feature = "cuda")]
    {
        return order_param_device_cuda_or_host::<R>(
            client,
            block_real_h,
            block_imag_h,
            num_blocks,
            n_inv,
        );
    }

    // Host f64 combine (wgpu/CPU path, or non-CUDA fallback).
    #[allow(unreachable_code)]
    {
        let block_real = read_f32s(client, block_real_h, num_blocks)?;
        let block_imag = read_f32s(client, block_imag_h, num_blocks)?;

        let mut real_sum = 0.0_f64;
        let mut imag_sum = 0.0_f64;
        for (&r, &im) in block_real.iter().zip(&block_imag) {
            real_sum += f64::from(r);
            imag_sum += f64::from(im);
        }
        let n_inv64 = f64::from(n_inv);
        Ok(((real_sum * n_inv64) as f32, (imag_sum * n_inv64) as f32))
    }
}

/// DV-003 helper: on CUDA, launch the on-device f64 finalize kernel and read
/// back only 2 f32s. On non-CUDA runtimes (when the CUDA feature is compiled
/// in but the runtime is wgpu/CPU), fall back to the host f64 combine.
#[cfg(feature = "cuda")]
fn order_param_device_cuda_or_host<R: Runtime>(
    client: &ComputeClient<R>,
    block_real_h: &Handle,
    block_imag_h: &Handle,
    num_blocks: usize,
    n_inv: f32,
) -> Result<(f32, f32), MeanFieldRk4Error> {
    // At runtime, check if this is actually a CUDA client. The CubeCL type
    // system doesn't give us a direct way to check, so we use the backend
    // name. If it's CUDA, use the on-device finalize; otherwise host.
    let backend = R::name(client);
    if backend == "cuda" {
        let out_byte_len = 2 * core::mem::size_of::<f32>();
        let out_h = client.empty(out_byte_len);
        order_param_finalize_f64::launch::<R>(
            client,
            CubeCount::Static(1, 1, 1),
            CubeDim::new_1d(1),
            array_arg(block_real_h, num_blocks),
            array_arg(block_imag_h, num_blocks),
            array_arg(&out_h, 2),
            n_inv,
        );
        let result = read_f32s(client, &out_h, 2)?;
        Ok((result[0], result[1]))
    } else {
        // Host f64 combine fallback (wgpu/CPU runtime with CUDA feature compiled in).
        let block_real = read_f32s(client, block_real_h, num_blocks)?;
        let block_imag = read_f32s(client, block_imag_h, num_blocks)?;
        let mut real_sum = 0.0_f64;
        let mut imag_sum = 0.0_f64;
        for (&r, &im) in block_real.iter().zip(&block_imag) {
            real_sum += f64::from(r);
            imag_sum += f64::from(im);
        }
        let n_inv64 = f64::from(n_inv);
        Ok(((real_sum * n_inv64) as f32, (imag_sum * n_inv64) as f32))
    }
}

/// Launch one RK4 stage kernel.
#[allow(clippy::too_many_arguments)]
fn launch_stage<R: Runtime>(
    client: &ComputeClient<R>,
    cube_count: &CubeCount,
    cube_dim: CubeDim,
    base_phase_h: &Handle,
    base_amp_h: &Handle,
    base_freq_h: &Handle,
    k_prev_phase_h: &Handle,
    k_prev_amp_h: &Handle,
    k_prev_freq_h: &Handle,
    dt_scale: f32,
    next_dt_scale: f32,
    zr: f32,
    zi: f32,
    params: &MeanFieldRk4Params,
    n_inv: f32,
    k_phase_h: &Handle,
    k_amp_h: &Handle,
    k_freq_h: &Handle,
    s_next_phase_h: &Handle,
    s_next_amp_h: &Handle,
    s_next_freq_h: &Handle,
    n: usize,
) {
    mean_field_rk4_stage::launch::<f32, R>(
        client,
        cube_count.clone(),
        cube_dim,
        array_arg(base_phase_h, n),
        array_arg(base_amp_h, n),
        array_arg(base_freq_h, n),
        array_arg(k_prev_phase_h, n),
        array_arg(k_prev_amp_h, n),
        array_arg(k_prev_freq_h, n),
        dt_scale,
        next_dt_scale,
        zr,
        zi,
        params.k,
        params.decay,
        params.gamma,
        n_inv,
        array_arg(k_phase_h, n),
        array_arg(k_amp_h, n),
        array_arg(k_freq_h, n),
        array_arg(s_next_phase_h, n),
        array_arg(s_next_amp_h, n),
        array_arg(s_next_freq_h, n),
    );
}

/// Execute one mean-field RK4 step on a CubeCL runtime, allocating all device
/// handles fresh.
///
/// For repeated stepping, prefer [`step_cubecl_with_pool`] which reuses
/// preallocated device handles.
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

    let pool = CubeclBufferPool::<R>::new(client, n);
    step_cubecl_with_pool(client, phase, amplitude, frequency, params, &pool)
}

/// Device-resident `(phase, amplitude, frequency)` state for the mean-field
/// RK4 step, held as CubeCL device [`Handle`]s that persist across steps.
///
/// [`step_cubecl_device`] reads the base state from here and, on success,
/// replaces the three handles with the stepped state — a caller stepping in a
/// loop never touches the host. [`MeanFieldDeviceState::upload`] is the
/// one-shot host→device constructor the thin [`step_cubecl_with_pool`] wrapper
/// uses; [`MeanFieldDeviceState::to_host`] downloads the current state.
#[derive(Clone, Debug)]
pub struct MeanFieldDeviceState<R: Runtime> {
    /// Oscillator count `N`.
    pub n: usize,
    /// `phase` buffer — `N` `f32`s.
    pub phase: Handle,
    /// `amplitude` buffer — `N` `f32`s.
    pub amplitude: Handle,
    /// `frequency` buffer — `N` `f32`s.
    pub frequency: Handle,
    runtime: PhantomData<R>,
}

impl<R: Runtime> MeanFieldDeviceState<R> {
    /// Assemble a device state from buffers the caller already holds on the
    /// device (no transfer).
    pub fn from_parts(n: usize, phase: Handle, amplitude: Handle, frequency: Handle) -> Self {
        Self {
            n,
            phase,
            amplitude,
            frequency,
            runtime: PhantomData,
        }
    }

    /// Upload host state buffers to the device.
    pub fn upload(
        client: &ComputeClient<R>,
        phase: &[f32],
        amplitude: &[f32],
        frequency: &[f32],
    ) -> Self {
        Self {
            n: phase.len(),
            phase: client.create_from_slice(f32::as_bytes(phase)),
            amplitude: client.create_from_slice(f32::as_bytes(amplitude)),
            frequency: client.create_from_slice(f32::as_bytes(frequency)),
            runtime: PhantomData,
        }
    }

    /// Download the current `(phase, amplitude, frequency)` state to host
    /// `Vec<f32>`s.
    ///
    /// # Errors
    ///
    /// Returns [`MeanFieldRk4Error::BackendReadError`] on a device read-back
    /// failure.
    pub fn to_host(
        &self,
        client: &ComputeClient<R>,
    ) -> Result<super::MeanFieldRk4Output, MeanFieldRk4Error> {
        Ok((
            read_f32s(client, &self.phase, self.n)?,
            read_f32s(client, &self.amplitude, self.n)?,
            read_f32s(client, &self.frequency, self.n)?,
        ))
    }
}

/// Execute one mean-field RK4 step on device-resident buffers, with **no host
/// transfer** — one algorithm, one implementation (Coding Standards §1):
/// [`step_cubecl_with_pool`] and [`step_cubecl`] are the thin
/// upload→this→download wrappers.
///
/// On success `state`'s three handles are replaced with the stepped state
/// (the old handles are freed). The `#[cube]` kernels launched here are
/// byte-for-byte those the host-slice path launches.
///
/// Unlike the pre-WP-036E host path, **stage 1 also takes its order parameter
/// from a device reduction** (there is no host-resident input slice to read it
/// from), so the sequence dispatches 9 launches — see
/// [`StepReport::launch_count`]. The whole sequence is timed via
/// `ComputeClient::profile` (device-event timing where the backend supports
/// it).
///
/// # Errors
///
/// Returns [`MeanFieldRk4Error`] for a non-finite/invalid parameter, an empty
/// population, a [`CubeclBufferPool`] sized for a different `N`, a device
/// read-back failure inside the order-parameter reduction, or a profiling
/// failure.
pub fn step_cubecl_device<R: Runtime>(
    client: &ComputeClient<R>,
    state: &mut MeanFieldDeviceState<R>,
    params: &MeanFieldRk4Params,
    pool: &CubeclBufferPool<R>,
) -> Result<StepReport, MeanFieldRk4Error> {
    validate_param("k", params.k, false)?;
    validate_param("decay", params.decay, false)?;
    validate_param("gamma", params.gamma, false)?;
    validate_param("dt", params.dt, true)?;

    let n = state.n;
    if n == 0 {
        return Err(MeanFieldRk4Error::EmptyPopulation);
    }
    if pool.capacity() != n {
        return Err(MeanFieldRk4Error::PoolSizeMismatch {
            capacity: pool.capacity(),
            actual: n,
        });
    }

    let n_inv = 1.0_f32 / n as f32;
    let half_dt = params.dt * 0.5;
    let num_blocks = pool.num_blocks();

    let base_phase_h = state.phase.clone();
    let base_amp_h = state.amplitude.clone();
    let base_freq_h = state.frequency.clone();

    let byte_len = n * core::mem::size_of::<f32>();
    let out_phase_h = client.empty(byte_len);
    let out_amp_h = client.empty(byte_len);
    let out_freq_h = client.empty(byte_len);
    let fin_phase = out_phase_h.clone();
    let fin_amp = out_amp_h.clone();
    let fin_freq = out_freq_h.clone();

    let cube_dim = CubeDim::new_1d(256);
    let cube_count = CubeCount::Static(n.div_ceil(256).max(1) as u32, 1, 1);
    let reduce_cube_count = CubeCount::Static(num_blocks as u32, 1, 1);

    let profiled = client.profile(
        move || -> Result<(), MeanFieldRk4Error> {
            // Stage 1: dt_scale = 0, next_dt_scale = 0.5*dt. Device-resident,
            // there is no host-resident input slice for `super::order_param`,
            // so stage 1 takes its order parameter from the same hierarchical
            // device reduction stages 2-4 use (+1 launch vs the pre-WP-036E
            // host path -> launch_count 9).
            let (zr, zi) = order_param_device(
                client,
                &reduce_cube_count,
                cube_dim,
                &base_phase_h,
                &base_amp_h,
                &pool.block_real,
                &pool.block_imag,
                num_blocks,
                n,
                n_inv,
            )?;
            launch_stage::<R>(
                client,
                &cube_count,
                cube_dim,
                &base_phase_h,
                &base_amp_h,
                &base_freq_h,
                &pool.k_zero,
                &pool.k_zero,
                &pool.k_zero,
                0.0,
                half_dt,
                zr,
                zi,
                params,
                n_inv,
                &pool.k1_phase,
                &pool.k1_amp,
                &pool.k1_freq,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.stage_freq,
                n,
            );

            // Stage 2.
            let (zr, zi) = order_param_device(
                client,
                &reduce_cube_count,
                cube_dim,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.block_real,
                &pool.block_imag,
                num_blocks,
                n,
                n_inv,
            )?;
            launch_stage::<R>(
                client,
                &cube_count,
                cube_dim,
                &base_phase_h,
                &base_amp_h,
                &base_freq_h,
                &pool.k1_phase,
                &pool.k1_amp,
                &pool.k1_freq,
                half_dt,
                half_dt,
                zr,
                zi,
                params,
                n_inv,
                &pool.k2_phase,
                &pool.k2_amp,
                &pool.k2_freq,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.stage_freq,
                n,
            );

            // Stage 3.
            let (zr, zi) = order_param_device(
                client,
                &reduce_cube_count,
                cube_dim,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.block_real,
                &pool.block_imag,
                num_blocks,
                n,
                n_inv,
            )?;
            launch_stage::<R>(
                client,
                &cube_count,
                cube_dim,
                &base_phase_h,
                &base_amp_h,
                &base_freq_h,
                &pool.k2_phase,
                &pool.k2_amp,
                &pool.k2_freq,
                half_dt,
                params.dt,
                zr,
                zi,
                params,
                n_inv,
                &pool.k3_phase,
                &pool.k3_amp,
                &pool.k3_freq,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.stage_freq,
                n,
            );

            // Stage 4.
            let (zr, zi) = order_param_device(
                client,
                &reduce_cube_count,
                cube_dim,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.block_real,
                &pool.block_imag,
                num_blocks,
                n,
                n_inv,
            )?;
            launch_stage::<R>(
                client,
                &cube_count,
                cube_dim,
                &base_phase_h,
                &base_amp_h,
                &base_freq_h,
                &pool.k3_phase,
                &pool.k3_amp,
                &pool.k3_freq,
                params.dt,
                0.0,
                zr,
                zi,
                params,
                n_inv,
                &pool.k4_phase,
                &pool.k4_amp,
                &pool.k4_freq,
                &pool.stage_phase,
                &pool.stage_amp,
                &pool.stage_freq,
                n,
            );

            // Final weighted sum, written into the fresh output handles.
            mean_field_rk4_finalize::launch::<f32, R>(
                client,
                cube_count.clone(),
                cube_dim,
                array_arg(&base_phase_h, n),
                array_arg(&base_amp_h, n),
                array_arg(&base_freq_h, n),
                array_arg(&pool.k1_phase, n),
                array_arg(&pool.k2_phase, n),
                array_arg(&pool.k3_phase, n),
                array_arg(&pool.k4_phase, n),
                array_arg(&pool.k1_amp, n),
                array_arg(&pool.k2_amp, n),
                array_arg(&pool.k3_amp, n),
                array_arg(&pool.k4_amp, n),
                array_arg(&pool.k1_freq, n),
                array_arg(&pool.k2_freq, n),
                array_arg(&pool.k3_freq, n),
                array_arg(&pool.k4_freq, n),
                params.dt,
                array_arg(&fin_phase, n),
                array_arg(&fin_amp, n),
                array_arg(&fin_freq, n),
            );

            Ok(())
        },
        "mean_field_rk4_step",
    );

    let (result, profile_duration) = profiled.map_err(|e| MeanFieldRk4Error::ProfilingFailed {
        message: e.to_string(),
    })?;
    result?;

    let timing_method = if profile_duration.timing_method() == CubeclTimingMethod::Device {
        TimingMethod::Device
    } else {
        TimingMethod::System
    };
    let ticks = cubecl::future::block_on(profile_duration.resolve());

    state.phase = out_phase_h;
    state.amplitude = out_amp_h;
    state.frequency = out_freq_h;

    Ok(StepReport {
        backend_name: R::name(client).to_string(),
        wall_time_seconds: ticks.duration().as_secs_f64(),
        timing_method,
        launch_count: 9,
    })
}

/// Execute one mean-field RK4 step using preallocated device buffers.
///
/// Thin host-slice wrapper: uploads `(phase, amplitude, frequency)` to a
/// [`MeanFieldDeviceState`], runs [`step_cubecl_device`] against the caller's
/// [`CubeclBufferPool`], and downloads the stepped state. Behaviour matches
/// the pre-WP-036E per-call path (the launch sequence is unchanged bar stage
/// 1's order-parameter reduction now running on-device — numerically within
/// the kernel-equivalence tolerance, `launch_count` 8 → 9).
///
/// # Errors
///
/// Returns [`MeanFieldRk4Error`] on invalid inputs or parameters, a pool size
/// mismatch, a device read-back failure, or a profiling failure.
pub fn step_cubecl_with_pool<R: Runtime>(
    client: &ComputeClient<R>,
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
    pool: &CubeclBufferPool<R>,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
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

    let mut state = MeanFieldDeviceState::upload(client, phase, amplitude, frequency);
    let report = step_cubecl_device(client, &mut state, params, pool)?;
    let out = state.to_host(client)?;
    Ok((out, report))
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
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = WgpuDevice::DefaultDevice;
        WgpuRuntime::client(&device)
    }))
    .map_err(|_| MeanFieldRk4Error::BackendUnavailable { name: "wgpu" })?;
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
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CpuDevice;
        CpuRuntime::client(&device)
    }))
    .map_err(|_| MeanFieldRk4Error::BackendUnavailable { name: "cpu" })?;
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
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CudaDevice::default();
        CudaRuntime::client(&device)
    }))
    .map_err(|_| MeanFieldRk4Error::BackendUnavailable { name: "cuda" })?;
    step_cubecl(&client, phase, amplitude, frequency, params)
}

/// Automatically select the best available backend and execute one RK4 step.
///
/// Tries each backend from [`auto_detect_order`](crate::backend::auto_detect_order) in priority order
/// (CUDA → wgpu → CPU). The first backend that initialises successfully
/// is used. If no CubeCL backend is available (none compiled in, or all
/// failed at runtime), falls back to the native CPU reference [`step_cpu`],
/// which is always available.
///
/// This is the main entry point for callers that want automatic backend
/// selection without manually managing the priority list.
pub fn step_auto(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    params: &MeanFieldRk4Params,
) -> Result<StepCubeclOutput, MeanFieldRk4Error> {
    #[cfg(feature = "cuda")]
    if let Ok(output) = try_step_cuda(phase, amplitude, frequency, params) {
        return Ok(output);
    }

    #[cfg(feature = "wgpu")]
    if let Ok(output) = try_step_wgpu(phase, amplitude, frequency, params) {
        return Ok(output);
    }

    #[cfg(feature = "cpu")]
    if let Ok(output) = try_step_cpu(phase, amplitude, frequency, params) {
        return Ok(output);
    }

    let start = std::time::Instant::now();
    let out = step_cpu(phase, amplitude, frequency, params)?;
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
        assert_eq!(report.launch_count, 9); // WP-036E: stage-1 order param now device-side
        assert!(report.wall_time_seconds >= 0.0);
        eprintln!("N={n} wgpu step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_non_block_aligned_n() {
        // N=1000 is not a multiple of the 256-thread cube block, so the last
        // reduction block is partially empty. This exercises the
        // `i < phase.len()` masking in `order_param_block_reduce`.
        let n = 1000;
        let phase: Vec<_> = (0..n).map(|i| 0.07 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 1.5,
            decay: 0.2,
            gamma: 0.02,
            dt: 0.02,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((gpu_p, gpu_a, gpu_f), report) =
            try_step_wgpu(&phase, &amplitude, &frequency, &params).unwrap();

        eprintln!("N={n} wgpu step report: {report:?}");
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

    #[test]
    fn wgpu_returns_typed_error_when_backend_unavailable() {
        let phase = vec![0.0_f32; 8];
        let amplitude = vec![1.0_f32; 8];
        let frequency = vec![0.0_f32; 8];
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        match try_step_wgpu(&phase, &amplitude, &frequency, &params) {
            Ok(_) | Err(MeanFieldRk4Error::BackendUnavailable { .. }) => {}
            Err(e) => panic!("unexpected wgpu error: {e}"),
        }
    }

    /// wgpu kernel-equivalence for `step_cubecl_device` (WP-036E S1) against
    /// the CPU reference, at a non-block-aligned `N`.
    #[test]
    fn wgpu_device_dispatch_matches_cpu_reference() {
        use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
        use std::panic::{catch_unwind, AssertUnwindSafe};

        let Ok(client) = catch_unwind(AssertUnwindSafe(|| {
            WgpuRuntime::client(&WgpuDevice::DefaultDevice)
        })) else {
            return; // No wgpu adapter — the `_auto` path covers the fallback.
        };

        let n = 1000usize;
        let phase: Vec<f32> = (0..n)
            .map(|i| (0.07 * i as f32).rem_euclid(core::f32::consts::TAU))
            .collect();
        let amplitude: Vec<f32> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
        let frequency: Vec<f32> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 1.5,
            decay: 0.2,
            gamma: 0.02,
            dt: 0.02,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();

        let pool = CubeclBufferPool::<WgpuRuntime>::new(&client, n);
        let mut state =
            MeanFieldDeviceState::<WgpuRuntime>::upload(&client, &phase, &amplitude, &frequency);
        let report = step_cubecl_device(&client, &mut state, &params, &pool).unwrap();
        assert_eq!(report.launch_count, 9);
        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();

        assert_allclose(&dev_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&dev_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&dev_f, &cpu_f, 1e-5, 1e-6);
    }
}

// `TimingMethod` is not feature-gated, but the `wgpu`/`cpu` test modules are;
// a display-coverage test lives here, unconditionally, so it runs (and
// counts toward coverage) under every feature combination that enables any
// backend, not just whichever of `tests`/`tests_cpu` happens to be compiled.
#[cfg(all(test, any(feature = "cpu", feature = "cuda", feature = "wgpu")))]
mod tests_common {
    use super::TimingMethod;

    #[test]
    fn timing_method_display_matches_variant() {
        assert_eq!(TimingMethod::Device.to_string(), "device");
        assert_eq!(TimingMethod::System.to_string(), "system");
    }
}

#[cfg(all(test, feature = "cpu"))]
mod tests_cpu {
    use super::*;
    use crate::mean_field_rk4::{step_cpu, MeanFieldRk4Params};

    /// Regression test for a genuine CubeCL CPU-backend data race: without a
    /// closing `sync_cube()` in [`order_param_block_reduce`] after thread 0's
    /// final write, the CPU runtime's per-worker block-iteration scheduling
    /// let threads 1..255 race ahead into the *next* cube block's iteration
    /// (reusing the same shared-memory buffer) while thread 0 was still
    /// reading it for the current block — non-deterministic, observed by
    /// diffing device block partials against a host-computed per-block sum
    /// across repeated runs. `N=300` forces `num_blocks=2` on the 256-thread
    /// cube so this exercises the multi-block path.
    #[test]
    fn order_param_device_matches_host_per_block_sums_for_multi_block_n() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let device = CpuDevice;
        let client = CpuRuntime::client(&device);

        let n = 300usize;
        let phase: Vec<_> = (0..n).map(|i| 0.03 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.2 + 0.001 * i as f32).collect();
        let n_inv = 1.0_f32 / n as f32;

        let (host_zr, host_zi) = crate::mean_field_rk4::order_param(&phase, &amplitude, n_inv);

        let pool = CubeclBufferPool::<CpuRuntime>::new(&client, n);
        let num_blocks = pool.num_blocks();
        assert_eq!(num_blocks, 2, "N=300 must span 2 cube blocks of 256");
        let phase_h = client.create_from_slice(f32::as_bytes(&phase));
        let amp_h = client.create_from_slice(f32::as_bytes(&amplitude));
        let cube_dim = CubeDim::new_1d(256);
        let reduce_cube_count = CubeCount::Static(num_blocks as u32, 1, 1);

        for _ in 0..5 {
            let (dev_zr, dev_zi) = order_param_device(
                &client,
                &reduce_cube_count,
                cube_dim,
                &phase_h,
                &amp_h,
                &pool.block_real,
                &pool.block_imag,
                num_blocks,
                n,
                n_inv,
            )
            .unwrap();

            assert!(
                (host_zr - dev_zr).abs() < 1e-5,
                "zr mismatch: host={host_zr} dev={dev_zr}"
            );
            assert!(
                (host_zi - dev_zi).abs() < 1e-5,
                "zi mismatch: host={host_zi} dev={dev_zi}"
            );
        }
    }

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
        assert_eq!(report.launch_count, 9); // WP-036E: stage-1 order param now device-side
        eprintln!("N={n} cpu step report: {report:?}");
        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cpu_matches_cpu_reference_for_non_block_aligned_n() {
        let n = 300;
        let phase: Vec<_> = (0..n).map(|i| 0.03 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.2 + 0.001 * i as f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 0.8,
            decay: 0.15,
            gamma: 0.005,
            dt: 0.015,
        };

        let (cpu_p, cpu_a, cpu_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((out_p, out_a, out_f), report) =
            try_step_cpu(&phase, &amplitude, &frequency, &params).unwrap();

        eprintln!("N={n} cpu step report: {report:?}");
        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cubecl_pool_rejects_size_mismatch() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let device = CpuDevice;
        let client = CpuRuntime::client(&device);

        let pool_n = 4;
        let call_n = 4096;
        let pool = CubeclBufferPool::<CpuRuntime>::new(&client, pool_n);
        assert_eq!(pool.capacity(), pool_n);

        let phase = vec![0.1_f32; call_n];
        let amp = vec![1.0_f32; call_n];
        let freq = vec![0.0_f32; call_n];
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let err = step_cubecl_with_pool(&client, &phase, &amp, &freq, &params, &pool).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::PoolSizeMismatch {
                capacity: 4,
                actual: 4096,
            }
        ));
    }

    #[test]
    fn step_auto_falls_back_to_available_backend() {
        let n = 32;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let (ref_p, ref_a, ref_f) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
        let ((auto_p, auto_a, auto_f), report) =
            step_auto(&phase, &amplitude, &frequency, &params).unwrap();

        assert_allclose(&auto_p, &ref_p, 1e-5, 1e-6);
        assert_allclose(&auto_a, &ref_a, 1e-5, 1e-6);
        assert_allclose(&auto_f, &ref_f, 1e-5, 1e-6);
        assert!(!report.backend_name.is_empty());
        assert!(report.wall_time_seconds >= 0.0);
    }

    fn seed_state(n: usize) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
        let phase = (0..n)
            .map(|i| (0.03 * i as f32).rem_euclid(core::f32::consts::TAU))
            .collect();
        let amplitude = (0..n).map(|i| 0.2 + 0.001 * i as f32).collect();
        let frequency = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        (phase, amplitude, frequency)
    }

    /// Kernel-equivalence for the device-`Handle` entry point (WP-036E S1):
    /// `step_cubecl_device` against a fresh-per-step CPU-reference RK4, with
    /// state kept device-resident across a multi-step loop (`to_host` only at
    /// the end), at a non-block-aligned `N`. Also pins the 9-launch count and
    /// checks the re-expressed host wrapper agrees bit-for-bit with a single
    /// device step.
    #[test]
    fn device_dispatch_matches_cpu_reference_across_a_stepping_loop() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let client = CpuRuntime::client(&CpuDevice);

        let n = 300usize;
        let (mut phase, mut amplitude, mut frequency) = seed_state(n);
        let params = MeanFieldRk4Params {
            k: 1.5,
            decay: 0.12,
            gamma: 0.008,
            dt: 0.01,
        };

        let pool = CubeclBufferPool::<CpuRuntime>::new(&client, n);
        let mut state =
            MeanFieldDeviceState::<CpuRuntime>::upload(&client, &phase, &amplitude, &frequency);

        for step in 0..4 {
            let report = step_cubecl_device(&client, &mut state, &params, &pool).unwrap();
            assert_eq!(report.launch_count, 9, "step {step}");
            let (rp, ra, rf) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
            (phase, amplitude, frequency) = (rp, ra, rf);
        }

        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();
        assert_allclose(&dev_p, &phase, 1e-5, 1e-6);
        assert_allclose(&dev_a, &amplitude, 1e-5, 1e-6);
        assert_allclose(&dev_f, &frequency, 1e-5, 1e-6);

        // The re-expressed host wrapper == one device step from the same input.
        let (p0, a0, f0) = seed_state(n);
        let mut one = MeanFieldDeviceState::<CpuRuntime>::upload(&client, &p0, &a0, &f0);
        step_cubecl_device(&client, &mut one, &params, &pool).unwrap();
        let one_host = one.to_host(&client).unwrap();
        let ((wrap_p, wrap_a, wrap_f), wrap_report) =
            step_cubecl_with_pool(&client, &p0, &a0, &f0, &params, &pool).unwrap();
        assert_eq!(wrap_report.launch_count, 9);
        assert_eq!((wrap_p, wrap_a, wrap_f), one_host);
    }

    #[test]
    fn device_dispatch_rejects_pool_mismatch_and_non_finite_param() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let client = CpuRuntime::client(&CpuDevice);

        let n = 32usize;
        let (phase, amplitude, frequency) = seed_state(n);
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        let mut state =
            MeanFieldDeviceState::<CpuRuntime>::upload(&client, &phase, &amplitude, &frequency);

        let wrong_pool = CubeclBufferPool::<CpuRuntime>::new(&client, n + 1);
        let err = step_cubecl_device(&client, &mut state, &params, &wrong_pool).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::PoolSizeMismatch { capacity, actual } if capacity == n + 1 && actual == n
        ));

        let pool = CubeclBufferPool::<CpuRuntime>::new(&client, n);
        let bad = MeanFieldRk4Params {
            dt: f32::NAN,
            ..params
        };
        let err = step_cubecl_device(&client, &mut state, &bad, &pool).unwrap_err();
        assert!(matches!(
            err,
            MeanFieldRk4Error::NonFiniteParameter { name: "dt", .. }
        ));
    }
}

#[cfg(all(test, feature = "cuda"))]
mod tests_cuda {
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

    /// First CUDA kernel-equivalence evidence for the fused mean-field RK4
    /// step (WP-021): previously this backend was compile-only (DV-001/DV-005
    /// — no CUDA hardware on the CI/dev hosts of record). This host has a
    /// working CUDA device, so this closes the equivalence gap for real.
    #[test]
    fn cuda_matches_cpu_reference_for_small_n() {
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
            try_step_cuda(&phase, &amplitude, &frequency, &params).unwrap();

        assert_eq!(report.backend_name, "cuda");
        assert_eq!(report.launch_count, 9); // WP-036E: stage-1 order param now device-side
        eprintln!("N={n} cuda step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cuda_matches_cpu_reference_at_one_million() {
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
            try_step_cuda(&phase, &amplitude, &frequency, &params).unwrap();

        assert_eq!(report.backend_name, "cuda");
        eprintln!("N=1M cuda step report: {report:?}");
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cuda_rejects_mismatched_lengths() {
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        let err = try_step_cuda(&phase, &amp, &freq, &params).unwrap_err();
        assert!(matches!(err, MeanFieldRk4Error::LengthMismatch { .. }));
    }

    /// CUDA kernel-equivalence for `step_cubecl_device` (WP-036E S1): state
    /// held device-resident across a stepping loop, `to_host` only at the end.
    #[test]
    fn cuda_device_dispatch_matches_cpu_reference_across_a_stepping_loop() {
        use cubecl::cuda::{CudaDevice, CudaRuntime};
        let client = CudaRuntime::client(&CudaDevice::default());

        let n = 4096usize;
        let mut phase: Vec<f32> = (0..n)
            .map(|i| (0.02 * (i % 311) as f32).rem_euclid(core::f32::consts::TAU))
            .collect();
        let mut amplitude: Vec<f32> = (0..n).map(|i| 0.5 + 0.3 * (i as f32 / n as f32)).collect();
        let mut frequency: Vec<f32> = (0..n).map(|i| 0.01 * ((i % 97) as f32 - 48.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        let pool = CubeclBufferPool::<CudaRuntime>::new(&client, n);
        let mut state =
            MeanFieldDeviceState::<CudaRuntime>::upload(&client, &phase, &amplitude, &frequency);

        for _ in 0..3 {
            let report = step_cubecl_device(&client, &mut state, &params, &pool).unwrap();
            assert_eq!(report.launch_count, 9);
            let (rp, ra, rf) = step_cpu(&phase, &amplitude, &frequency, &params).unwrap();
            (phase, amplitude, frequency) = (rp, ra, rf);
        }

        let (dev_p, dev_a, dev_f) = state.to_host(&client).unwrap();
        assert_allclose(&dev_p, &phase, 1e-5, 1e-6);
        assert_allclose(&dev_a, &amplitude, 1e-5, 1e-6);
        assert_allclose(&dev_f, &frequency, 1e-5, 1e-6);
    }
}

#[cfg(all(test, feature = "cuda", feature = "wgpu"))]
mod tests_priority {
    use super::*;
    use crate::mean_field_rk4::MeanFieldRk4Params;

    /// Regression test for the WP-021 dispatch-priority fix: `step_auto` must
    /// select CUDA before wgpu when both backends are available and compiled
    /// in, matching `backend::auto_detect_order()`'s documented CUDA > wgpu >
    /// CPU preference (previously `step_auto` tried wgpu first, so CUDA was
    /// silently unreachable through the auto-dispatch entry point on any host
    /// where both backends initialise successfully).
    #[test]
    fn step_auto_prefers_cuda_over_wgpu_when_both_available() {
        let n = 32;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        try_step_cuda(&phase, &amplitude, &frequency, &params)
            .expect("this test requires a working CUDA backend on the host");

        let (_, report) = step_auto(&phase, &amplitude, &frequency, &params).unwrap();
        assert_eq!(report.backend_name, "cuda");
    }
}

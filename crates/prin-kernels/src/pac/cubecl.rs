//! Single-source CubeCL implementation of PAC modulation.
//!
//! Two kernel launches (see the module documentation in [`super`]):
//! `pac_phase_sum_block_reduce` (hierarchical sum reduction of `slow_phase`,
//! mirroring `mean_field_rk4::cubecl`'s `order_param_block_reduce`) followed
//! by a host-side mean/cosine finish and `pac_modulate` (elementwise
//! broadcast + clamp). The CPU reference in [`super::pac_modulate_cpu`]
//! remains the numerical authority; this path is checked against it in the
//! kernel-equivalence tests below.
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `len * size_of::<f32>()` bytes. Those
//! handles are created by `ComputeClient::create_from_slice` or
//! `ComputeClient::empty`, so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use cubecl::prelude::*;
use cubecl::server::Handle;

use super::{validate_inputs, PacError, PacParams};
use crate::buffers::num_blocks_for;

/// Level 1 of the hierarchical mean-phase reduction: each 256-thread cube
/// block reduces its slice of `phase[i]` into one `f32` partial sum, written
/// to `block_sum[CUBE_POS]`. Threads past the end of `phase` contribute zero.
///
/// Structurally identical to
/// [`crate::mean_field_rk4::cubecl::order_param_block_reduce`] but for a
/// single real-valued array instead of a complex weighted sum; see that
/// kernel's doc comment for the two-barrier synchronization rationale (a
/// genuine CubeCL CPU-backend data race was found and fixed there — the same
/// pattern is reused here as the proven-correct design, not re-derived).
#[cube(launch)]
fn pac_phase_sum_block_reduce<F: Float + CubeElement>(phase: &Array<F>, block_sum: &mut Array<F>) {
    let tid = UNIT_POS as usize;
    let i = ABSOLUTE_POS;

    let mut sum_sh = SharedMemory::<F>::new(256usize);

    if i < phase.len() {
        sum_sh[tid] = phase[i];
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

/// Broadcast the host-computed scalar `modulation` factor across
/// `fast_amplitude`, clamped to `[amp_min, amp_max]`.
#[cube(launch)]
fn pac_modulate<F: Float + CubeElement>(
    fast_amplitude: &Array<F>,
    modulation: F,
    amp_min: F,
    amp_max: F,
    out: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < fast_amplitude.len() {
        out[i] = (fast_amplitude[i] * modulation).clamp(amp_min, amp_max);
    }
}

/// Build an [`ArrayArg`] from a [`Handle`] whose length is `n` `f32`s.
///
/// # Safety
///
/// `handle` must refer to a device allocation of at least `n *
/// size_of::<f32>()` bytes. All handles in this module come from
/// `client.create_from_slice` or `client.empty(byte_len)`.
fn array_arg<R: Runtime>(handle: &Handle, n: usize) -> ArrayArg<R> {
    // SAFETY: see function-level safety note.
    unsafe { ArrayArg::from_raw_parts(handle.clone(), n) }
}

/// Read one `f32` buffer back from the device.
fn read_f32s<R: Runtime>(client: &ComputeClient<R>, handle: &Handle) -> Result<Vec<f32>, PacError> {
    let bytes = client
        .read_one(handle.clone())
        .map_err(|_| PacError::BackendReadError)?;
    Ok(f32::from_bytes(&bytes).to_vec())
}

/// Compute `mean(slow_phase)` via the hierarchical device reduction,
/// finishing with an `f64` accumulator on the host (Coding Standards §2.2),
/// matching [`super::modulation_factor`]'s CPU-side precision exactly.
fn mean_slow_phase_device<R: Runtime>(
    client: &ComputeClient<R>,
    slow_phase: &[f32],
) -> Result<f32, PacError> {
    let n = slow_phase.len();
    let num_blocks = num_blocks_for(n);
    let phase_h = client.create_from_slice(f32::as_bytes(slow_phase));
    let block_sum_h = client.empty(num_blocks * core::mem::size_of::<f32>());

    let cube_dim = CubeDim::new_1d(256);
    let cube_count = CubeCount::Static(num_blocks as u32, 1, 1);

    pac_phase_sum_block_reduce::launch::<f32, R>(
        client,
        cube_count,
        cube_dim,
        array_arg(&phase_h, n),
        array_arg(&block_sum_h, num_blocks),
    );

    let block_sums = read_f32s(client, &block_sum_h)?;
    let mut sum = 0.0_f64;
    for &s in &block_sums {
        sum += f64::from(s);
    }
    Ok((sum / n as f64) as f32)
}

/// Execute PAC modulation on a CubeCL runtime.
///
/// # Errors
///
/// Returns [`PacError`] on invalid inputs (empty slices, non-finite values,
/// an inverted clamp range) or a device read-back failure.
pub fn pac_modulate_cubecl<R: Runtime>(
    client: &ComputeClient<R>,
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    validate_inputs(slow_phase, fast_amplitude, params)?;

    let mean = mean_slow_phase_device(client, slow_phase)?;
    let modulation = 1.0_f32 + params.modulation_depth * (mean + params.phase_offset).cos();

    let n_fast = fast_amplitude.len();
    let fast_h = client.create_from_slice(f32::as_bytes(fast_amplitude));
    let out_h = client.empty(core::mem::size_of_val(fast_amplitude));

    let cube_dim = CubeDim::new_1d(256);
    let cube_count = CubeCount::Static(n_fast.div_ceil(256).max(1) as u32, 1, 1);

    pac_modulate::launch::<f32, R>(
        client,
        cube_count,
        cube_dim,
        array_arg(&fast_h, n_fast),
        modulation,
        params.amp_min,
        params.amp_max,
        array_arg(&out_h, n_fast),
    );

    read_f32s(client, &out_h)
}

#[cfg(feature = "wgpu")]
/// Run PAC modulation on the wgpu runtime.
pub fn try_pac_modulate_wgpu(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = WgpuDevice::DefaultDevice;
        WgpuRuntime::client(&device)
    }))
    .map_err(|_| PacError::BackendUnavailable { name: "wgpu" })?;
    pac_modulate_cubecl(&client, slow_phase, fast_amplitude, params)
}

#[cfg(feature = "cpu")]
/// Run PAC modulation on the CubeCL CPU runtime.
pub fn try_pac_modulate_cpu(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    use cubecl::cpu::{CpuDevice, CpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CpuDevice;
        CpuRuntime::client(&device)
    }))
    .map_err(|_| PacError::BackendUnavailable { name: "cpu" })?;
    pac_modulate_cubecl(&client, slow_phase, fast_amplitude, params)
}

#[cfg(feature = "cuda")]
/// Run PAC modulation on the CUDA runtime.
pub fn try_pac_modulate_cuda(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    use cubecl::cuda::{CudaDevice, CudaRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CudaDevice::default();
        CudaRuntime::client(&device)
    }))
    .map_err(|_| PacError::BackendUnavailable { name: "cuda" })?;
    pac_modulate_cubecl(&client, slow_phase, fast_amplitude, params)
}

/// Automatically select the best available backend and apply PAC modulation.
///
/// Tries each backend from [`auto_detect_order`](crate::backend::auto_detect_order)
/// in priority order (CUDA → wgpu → CPU). Falls back to the native CPU
/// reference [`super::pac_modulate_cpu`] if no CubeCL backend is available.
pub fn pac_modulate_auto(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    #[cfg(feature = "wgpu")]
    if let Ok(output) = try_pac_modulate_wgpu(slow_phase, fast_amplitude, params) {
        return Ok(output);
    }

    #[cfg(feature = "cuda")]
    if let Ok(output) = try_pac_modulate_cuda(slow_phase, fast_amplitude, params) {
        return Ok(output);
    }

    #[cfg(feature = "cpu")]
    if let Ok(output) = try_pac_modulate_cpu(slow_phase, fast_amplitude, params) {
        return Ok(output);
    }

    super::pac_modulate_cpu(slow_phase, fast_amplitude, params)
}

#[cfg(all(test, feature = "wgpu"))]
mod tests {
    use super::*;
    use crate::pac::pac_modulate_cpu;

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
        let slow: Vec<_> = (0..37).map(|i| 0.05 * i as f32).collect();
        let fast: Vec<_> = (0..64).map(|i| 0.5 + 0.1 * i as f32).collect();
        let params = PacParams {
            modulation_depth: 0.6,
            phase_offset: 0.2,
            amp_min: 1e-6,
            amp_max: 10.0,
        };

        let cpu_out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        let gpu_out = try_pac_modulate_wgpu(&slow, &fast, &params).unwrap();

        assert_allclose(&gpu_out, &cpu_out, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_non_block_aligned_n() {
        let n_slow = 1000;
        let n_fast = 777;
        let slow: Vec<_> = (0..n_slow).map(|i| 0.01 * i as f32).collect();
        let fast: Vec<_> = (0..n_fast).map(|i| 0.2 + 0.01 * i as f32).collect();
        let params = PacParams {
            modulation_depth: 0.3,
            phase_offset: -0.4,
            amp_min: 1e-6,
            amp_max: 10.0,
        };

        let cpu_out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        let gpu_out = try_pac_modulate_wgpu(&slow, &fast, &params).unwrap();

        assert_allclose(&gpu_out, &cpu_out, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_at_large_n() {
        let n = 100_000;
        let slow: Vec<_> = (0..n).map(|i| 0.001 * (i % 6283) as f32).collect();
        let fast: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let params = PacParams {
            modulation_depth: 1.0,
            phase_offset: 0.0,
            amp_min: 1e-6,
            amp_max: 10.0,
        };

        let cpu_out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        let gpu_out = try_pac_modulate_wgpu(&slow, &fast, &params).unwrap();

        assert_allclose(&gpu_out, &cpu_out, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_rejects_empty_slow_phase() {
        let params = PacParams::new(0.5);
        let err = try_pac_modulate_wgpu(&[], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::EmptySlowPhase));
    }

    #[test]
    fn wgpu_rejects_non_finite_input() {
        let params = PacParams::new(0.5);
        let err = try_pac_modulate_wgpu(&[0.0, f32::NAN], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::NonFiniteSlowPhase { .. }));
    }

    #[test]
    fn wgpu_returns_typed_error_when_backend_unavailable() {
        let params = PacParams::new(0.5);
        match try_pac_modulate_wgpu(&[0.0; 8], &[1.0; 8], &params) {
            Ok(_) | Err(PacError::BackendUnavailable { .. }) => {}
            Err(e) => panic!("unexpected wgpu error: {e}"),
        }
    }
}

#[cfg(all(test, feature = "cpu"))]
mod tests_cpu {
    use super::*;
    use crate::pac::pac_modulate_cpu;

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    #[test]
    fn cpu_backend_matches_cpu_reference_multi_block() {
        // N=600 forces 3 cube blocks (256-thread), exercising the partial
        // last-block mask in pac_phase_sum_block_reduce.
        let n = 600;
        let slow: Vec<_> = (0..n).map(|i| 0.01 * i as f32).collect();
        let fast: Vec<_> = (0..n).map(|i| 0.3 + 0.002 * i as f32).collect();
        let params = PacParams {
            modulation_depth: 0.4,
            phase_offset: 0.1,
            amp_min: 1e-6,
            amp_max: 10.0,
        };

        let cpu_out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        let out = try_pac_modulate_cpu(&slow, &fast, &params).unwrap();

        assert_allclose(&out, &cpu_out, 1e-5, 1e-6);
    }

    /// Regression-style coverage for the reduction's multi-block combine:
    /// repeated calls must be deterministic (guards against the class of
    /// data race documented on `order_param_block_reduce`).
    #[test]
    fn cpu_backend_reduction_is_deterministic_across_repeated_calls() {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        let device = CpuDevice;
        let client = CpuRuntime::client(&device);

        let n = 300usize;
        let slow: Vec<_> = (0..n).map(|i| 0.02 * i as f32).collect();
        let expected = {
            let sum: f64 = slow.iter().map(|&p| f64::from(p)).sum();
            (sum / n as f64) as f32
        };

        for _ in 0..5 {
            let mean = mean_slow_phase_device(&client, &slow).unwrap();
            assert!(
                (mean - expected).abs() < 1e-4,
                "mean mismatch: got {mean}, expected {expected}"
            );
        }
    }

    #[test]
    fn pac_modulate_auto_falls_back_to_available_backend() {
        let slow: Vec<_> = (0..40).map(|i| 0.05 * i as f32).collect();
        let fast: Vec<_> = (0..40).map(|i| 0.5 + 0.02 * i as f32).collect();
        let params = PacParams::new(0.4);

        let ref_out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        let auto_out = pac_modulate_auto(&slow, &fast, &params).unwrap();

        assert_allclose(&auto_out, &ref_out, 1e-5, 1e-6);
    }
}

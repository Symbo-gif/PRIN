//! Single-source CubeCL implementation of the sparse k-NN coupling
//! derivative kernel.
//!
//! This module is enabled by the `cuda`, `wgpu`, or `cpu` feature. It
//! contains the `#[cube]` gather kernel and the runtime launch code. The CPU
//! reference in [`super::sparse_knn_derivatives_cpu`] remains the numerical
//! authority; this path is checked against it in the kernel-equivalence
//! tests below.
//!
//! ## Gather kernel, not SpMV decomposition
//!
//! `prin_sim::csr_coupling::SparseCoupling::kuramoto_coupling` computes the
//! same sparse Kuramoto coupling via two dense sparse matrix–vector products
//! (a trig-identity decomposition). That is the right shape for a
//! general-purpose, potentially high-degree CSR matrix on CPU (it reuses
//! `rayon`-dispatched row folds). This kernel instead launches **one GPU
//! thread per oscillator**, each of which walks its own CSR row
//! (`indptr[i]..indptr[i+1]`) directly: for the `N = 16K, k = 14` k-NN target
//! this WP's acceptance criteria name, the fixed, small per-row degree makes
//! the extra CSR row lookup cheaper than two full-array SpMV passes plus a
//! combine pass, and it keeps the per-edge trig-identity algebra identical
//! between the CPU reference and every GPU backend (no separate
//! precompute-then-gather kernel needed).
//!
//! ## Buffer management
//!
//! Every launch allocates its handles fresh via `client.create_from_slice`/
//! `client.empty`; there is no preallocated buffer pool for this kernel (a
//! single launch per call, unlike `mean_field_rk4`'s 8-launch RK4 sequence,
//! makes per-step allocation overhead proportionally far smaller — see the
//! S1 handoff note's "Out-of-scope discoveries" for the deferred pooling
//! candidate).
//!
//! SAFETY: All `unsafe` blocks are confined to `ArrayArg::from_raw_parts` with
//! handles whose lengths are exactly `len * size_of::<T>()` bytes. Those
//! handles are created by `ComputeClient::create_from_slice` or
//! `ComputeClient::empty`, so the length contract holds.

#![allow(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]

use cubecl::prelude::*;
use cubecl::server::Handle;

use super::{validate_param, validate_state, SparseKnnError, SparseKnnGraph, SparseKnnParams};

/// Full CubeCL sparse k-NN output: `(dphase, damplitude, dfrequency)`.
pub type SparseKnnCubeclOutput = super::SparseKnnOutput;

/// Sparse k-NN coupling derivative kernel: one thread per oscillator, gathering
/// over its CSR row.
///
/// See the module documentation for the gather-vs-SpMV design rationale and
/// [`super::sparse_knn_derivatives_cpu`]'s doc comment for the formula (this
/// kernel computes the identical per-edge trig-identity algebra).
#[cube(launch)]
fn sparse_knn_coupling<F: Float + CubeElement>(
    phase: &Array<F>,
    amplitude: &Array<F>,
    frequency: &Array<F>,
    indptr: &Array<u32>,
    indices: &Array<u32>,
    k: F,
    decay: F,
    gamma: F,
    dphase: &mut Array<F>,
    damplitude: &mut Array<F>,
    dfrequency: &mut Array<F>,
) {
    let i = ABSOLUTE_POS;
    if i < phase.len() {
        let row_start = indptr[i];
        let row_end = indptr[i + 1usize];
        let degree = row_end - row_start;

        let phi_i = phase[i];
        let si = phi_i.sin();
        let ci = phi_i.cos();

        let mut sin_sum = F::new(0.0_f32);
        let mut cos_sum = F::new(0.0_f32);
        let mut inv_degree = F::new(0.0_f32);

        if degree > 0u32 {
            let weight = k / F::cast_from(degree);
            inv_degree = F::new(1.0_f32) / F::cast_from(degree);
            for e in row_start..row_end {
                let j = indices[e as usize] as usize;
                let phi_j = phase[j];
                let sj = phi_j.sin();
                let cj = phi_j.cos();
                let diff_sin = sj * ci - cj * si;
                let diff_cos = cj * ci + sj * si;
                let amp_j = amplitude[j];
                sin_sum += weight * diff_sin * amp_j;
                cos_sum += weight * diff_cos * amp_j;
            }
        }

        dphase[i] = frequency[i] + sin_sum;
        damplitude[i] = -decay * amplitude[i] + cos_sum;
        dfrequency[i] = gamma * sin_sum * inv_degree;
    }
}

/// Build an [`ArrayArg`] from a [`Handle`] whose length is `n` `f32`s.
///
/// # Safety
///
/// `handle` must refer to a device allocation of at least `n *
/// size_of::<f32>()` bytes. All handles in this module come from
/// `client.create_from_slice`, so the invariant holds.
fn array_arg<R: Runtime>(handle: &Handle, n: usize) -> ArrayArg<R> {
    // SAFETY: see function-level safety note.
    unsafe { ArrayArg::from_raw_parts(handle.clone(), n) }
}

/// Build an [`ArrayArg`] for a `u32` handle of length `n`.
///
/// # Safety
///
/// Same contract as [`array_arg`], for `u32` elements.
fn array_arg_u32<R: Runtime>(handle: &Handle, n: usize) -> ArrayArg<R> {
    // SAFETY: see function-level safety note.
    unsafe { ArrayArg::from_raw_parts(handle.clone(), n) }
}

/// Read one `f32` buffer back from the device.
fn read_f32s<R: Runtime>(
    client: &ComputeClient<R>,
    handle: &Handle,
) -> Result<Vec<f32>, SparseKnnError> {
    let bytes = client
        .read_one(handle.clone())
        .map_err(|_| SparseKnnError::BackendReadError)?;
    Ok(f32::from_bytes(&bytes).to_vec())
}

/// Execute the sparse k-NN coupling derivative kernel on a CubeCL runtime.
///
/// # Errors
///
/// Returns [`SparseKnnError`] on invalid inputs, a graph/state size
/// mismatch, non-finite parameters, or a device read-back failure.
pub fn sparse_knn_coupling_cubecl<R: Runtime>(
    client: &ComputeClient<R>,
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnCubeclOutput, SparseKnnError> {
    let n = validate_state(phase, amplitude, frequency, graph)?;
    validate_param("k", params.k)?;
    validate_param("decay", params.decay)?;
    validate_param("gamma", params.gamma)?;

    let phase_h = client.create_from_slice(f32::as_bytes(phase));
    let amp_h = client.create_from_slice(f32::as_bytes(amplitude));
    let freq_h = client.create_from_slice(f32::as_bytes(frequency));
    let indptr_h = client.create_from_slice(u32::as_bytes(graph.indptr()));
    let indices_len = graph.nnz().max(1);
    let indices_h = if graph.nnz() > 0 {
        client.create_from_slice(u32::as_bytes(graph.indices()))
    } else {
        client.create_from_slice(u32::as_bytes(&[0u32]))
    };
    let dphase_h = client.empty(n * core::mem::size_of::<f32>());
    let damp_h = client.empty(n * core::mem::size_of::<f32>());
    let dfreq_h = client.empty(n * core::mem::size_of::<f32>());

    let cube_dim = CubeDim::new_1d(256);
    let cube_count = CubeCount::Static(n.div_ceil(256).max(1) as u32, 1, 1);

    sparse_knn_coupling::launch::<f32, R>(
        client,
        cube_count,
        cube_dim,
        array_arg(&phase_h, n),
        array_arg(&amp_h, n),
        array_arg(&freq_h, n),
        array_arg_u32(&indptr_h, n + 1),
        array_arg_u32(&indices_h, indices_len),
        params.k,
        params.decay,
        params.gamma,
        array_arg(&dphase_h, n),
        array_arg(&damp_h, n),
        array_arg(&dfreq_h, n),
    );

    let dphase = read_f32s(client, &dphase_h)?;
    let damplitude = read_f32s(client, &damp_h)?;
    let dfrequency = read_f32s(client, &dfreq_h)?;

    Ok((dphase, damplitude, dfrequency))
}

#[cfg(feature = "wgpu")]
/// Run the sparse k-NN coupling kernel on the wgpu runtime.
pub fn try_sparse_knn_coupling_wgpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnCubeclOutput, SparseKnnError> {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = WgpuDevice::DefaultDevice;
        WgpuRuntime::client(&device)
    }))
    .map_err(|_| SparseKnnError::BackendUnavailable { name: "wgpu" })?;
    sparse_knn_coupling_cubecl(&client, phase, amplitude, frequency, graph, params)
}

#[cfg(feature = "cpu")]
/// Run the sparse k-NN coupling kernel on the CubeCL CPU runtime.
pub fn try_sparse_knn_coupling_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnCubeclOutput, SparseKnnError> {
    use cubecl::cpu::{CpuDevice, CpuRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CpuDevice;
        CpuRuntime::client(&device)
    }))
    .map_err(|_| SparseKnnError::BackendUnavailable { name: "cpu" })?;
    sparse_knn_coupling_cubecl(&client, phase, amplitude, frequency, graph, params)
}

#[cfg(feature = "cuda")]
/// Run the sparse k-NN coupling kernel on the CUDA runtime.
pub fn try_sparse_knn_coupling_cuda(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnCubeclOutput, SparseKnnError> {
    use cubecl::cuda::{CudaDevice, CudaRuntime};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    let client = catch_unwind(AssertUnwindSafe(|| {
        let device = CudaDevice::default();
        CudaRuntime::client(&device)
    }))
    .map_err(|_| SparseKnnError::BackendUnavailable { name: "cuda" })?;
    sparse_knn_coupling_cubecl(&client, phase, amplitude, frequency, graph, params)
}

/// Automatically select the best available backend and evaluate the sparse
/// k-NN coupling derivative.
///
/// Tries each backend from [`auto_detect_order`](crate::backend::auto_detect_order)
/// in priority order (CUDA → wgpu → CPU). Falls back to the native CPU
/// reference [`super::sparse_knn_derivatives_cpu`] if no CubeCL backend is
/// available.
pub fn sparse_knn_coupling_auto(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnCubeclOutput, SparseKnnError> {
    #[cfg(feature = "cuda")]
    if let Ok(output) = try_sparse_knn_coupling_cuda(phase, amplitude, frequency, graph, params) {
        return Ok(output);
    }

    #[cfg(feature = "wgpu")]
    if let Ok(output) = try_sparse_knn_coupling_wgpu(phase, amplitude, frequency, graph, params) {
        return Ok(output);
    }

    #[cfg(feature = "cpu")]
    if let Ok(output) = try_sparse_knn_coupling_cpu(phase, amplitude, frequency, graph, params) {
        return Ok(output);
    }

    super::sparse_knn_derivatives_cpu(phase, amplitude, frequency, graph, params)
}

#[cfg(all(test, feature = "wgpu"))]
mod tests {
    use super::*;
    use crate::sparse_knn::sparse_knn_derivatives_cpu;

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    fn ring_graph(n: usize, half_k: usize) -> SparseKnnGraph {
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for i in 0..n {
            for d in 1..=half_k {
                indices.push(((i + n - d) % n) as u32);
                indices.push(((i + d) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_small_n() {
        let n = 64;
        let graph = ring_graph(n, 7); // k = 14 total (7 each side).
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };

        let (cpu_p, cpu_a, cpu_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (gpu_p, gpu_a, gpu_f) =
            try_sparse_knn_coupling_wgpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_for_non_block_aligned_n_with_variable_degree() {
        // N=1000 is not a multiple of the 256-thread cube block, and degree
        // varies per row (star + ring hybrid): node 0 has high degree, most
        // nodes have degree 2, and a few are isolated (degree 0).
        let n = 1000;
        let mut indptr = vec![0u32];
        let mut indices = Vec::new();
        for i in 0..n {
            if i == 0 {
                for j in 1..20 {
                    indices.push(j as u32);
                }
            } else if i % 37 == 0 {
                // Isolated node: no neighbors.
            } else {
                indices.push(((i + n - 1) % n) as u32);
                indices.push(((i + 1) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        let graph = SparseKnnGraph::from_csr(n, indptr, indices).unwrap();

        // Phase is wrapped to [0, 2*pi), matching how phase is always
        // maintained between simulation steps (`mean_field_rk4::wrap_phase`);
        // large unwrapped angles amplify GPU-vs-host trig range-reduction
        // precision differences well beyond this kernel's own correctness.
        let tau = core::f32::consts::TAU;
        let phase: Vec<_> = (0..n).map(|i| (0.03 * i as f32).rem_euclid(tau)).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        let params = SparseKnnParams {
            k: 1.5,
            decay: 0.2,
            gamma: 0.02,
        };

        let (cpu_p, cpu_a, cpu_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (gpu_p, gpu_a, gpu_f) =
            try_sparse_knn_coupling_wgpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_matches_cpu_reference_at_n_16k_k_14() {
        // The WP-019 acceptance target shape.
        let n = 16_000;
        let half_k = 7;
        let graph = ring_graph(n, half_k);
        let phase: Vec<_> = (0..n).map(|i| 0.01 * (i % 628) as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.02 * ((i % 100) as f32 - 50.0)).collect();
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };

        let (cpu_p, cpu_a, cpu_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (gpu_p, gpu_a, gpu_f) =
            try_sparse_knn_coupling_wgpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_eq!(graph.degree(0), 2 * half_k);
        assert_allclose(&gpu_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&gpu_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&gpu_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn wgpu_rejects_mismatched_lengths() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };
        let err = try_sparse_knn_coupling_wgpu(&phase, &amp, &freq, &graph, &params).unwrap_err();
        assert!(matches!(err, SparseKnnError::LengthMismatch { .. }));
    }

    #[test]
    fn wgpu_rejects_graph_size_mismatch() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 6];
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };
        let err =
            try_sparse_knn_coupling_wgpu(&phase, &phase, &phase, &graph, &params).unwrap_err();
        assert!(matches!(err, SparseKnnError::GraphSizeMismatch { .. }));
    }

    #[test]
    fn wgpu_rejects_non_finite_k() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let params = SparseKnnParams {
            k: f32::NAN,
            decay: 0.1,
            gamma: 0.01,
        };
        let err =
            try_sparse_knn_coupling_wgpu(&phase, &phase, &phase, &graph, &params).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::NonFiniteParameter { name: "k", .. }
        ));
    }

    #[test]
    fn wgpu_returns_typed_error_when_backend_unavailable() {
        let graph = ring_graph(8, 1);
        let phase = vec![0.0_f32; 8];
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };
        match try_sparse_knn_coupling_wgpu(&phase, &phase, &phase, &graph, &params) {
            Ok(_) | Err(SparseKnnError::BackendUnavailable { .. }) => {}
            Err(e) => panic!("unexpected wgpu error: {e}"),
        }
    }
}

#[cfg(all(test, feature = "cpu"))]
mod tests_cpu {
    use super::*;
    use crate::sparse_knn::sparse_knn_derivatives_cpu;

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    fn ring_graph(n: usize, half_k: usize) -> SparseKnnGraph {
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for i in 0..n {
            for d in 1..=half_k {
                indices.push(((i + n - d) % n) as u32);
                indices.push(((i + d) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
    }

    #[test]
    fn cpu_backend_matches_cpu_reference() {
        let n = 300;
        let graph = ring_graph(n, 3);
        let phase: Vec<_> = (0..n).map(|i| 0.03 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.2 + 0.001 * i as f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        let params = SparseKnnParams {
            k: 0.8,
            decay: 0.15,
            gamma: 0.005,
        };

        let (cpu_p, cpu_a, cpu_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (out_p, out_a, out_f) =
            try_sparse_knn_coupling_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cpu_backend_handles_all_isolated_graph() {
        // Every row empty (k=0 style graph): coupling contributes nothing.
        let n = 16;
        let graph = SparseKnnGraph::from_csr(n, vec![0u32; n + 1], vec![]).unwrap();
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude = vec![1.0_f32; n];
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - 8.0)).collect();
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };

        let (out_p, out_a, out_f) =
            try_sparse_knn_coupling_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        for i in 0..n {
            assert!((out_p[i] - frequency[i]).abs() < 1e-6);
            assert!((out_a[i] - (-params.decay * amplitude[i])).abs() < 1e-6);
            assert_eq!(out_f[i], 0.0);
        }
    }

    #[test]
    fn sparse_knn_coupling_auto_falls_back_to_available_backend() {
        let n = 32;
        let graph = ring_graph(n, 2);
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.05 * (i as f32 - n as f32 / 2.0)).collect();
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };

        let (ref_p, ref_a, ref_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (auto_p, auto_a, auto_f) =
            sparse_knn_coupling_auto(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_allclose(&auto_p, &ref_p, 1e-5, 1e-6);
        assert_allclose(&auto_a, &ref_a, 1e-5, 1e-6);
        assert_allclose(&auto_f, &ref_f, 1e-5, 1e-6);
    }
}

#[cfg(all(test, feature = "cuda"))]
mod tests_cuda {
    use super::*;
    use crate::sparse_knn::sparse_knn_derivatives_cpu;

    fn assert_allclose(actual: &[f32], expected: &[f32], rtol: f32, atol: f32) {
        for (a, e) in actual.iter().zip(expected) {
            assert!(
                (a - e).abs() <= atol + rtol * e.abs(),
                "mismatch: actual {a}, expected {e}"
            );
        }
    }

    fn ring_graph(n: usize, half_k: usize) -> SparseKnnGraph {
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for i in 0..n {
            for d in 1..=half_k {
                indices.push(((i + n - d) % n) as u32);
                indices.push(((i + d) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
    }

    /// First CUDA kernel-equivalence evidence for the sparse k-NN coupling
    /// derivative (WP-021): previously this backend was compile-only
    /// (DV-001/DV-005 — no CUDA hardware on the CI/dev hosts of record). This
    /// host has a working CUDA device, so this closes the equivalence gap for
    /// real.
    #[test]
    fn cuda_backend_matches_cpu_reference() {
        let n = 300;
        let graph = ring_graph(n, 3);
        let phase: Vec<_> = (0..n).map(|i| 0.03 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|i| 0.2 + 0.001 * i as f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.01 * (i as f32 - n as f32 / 2.0)).collect();
        let params = SparseKnnParams {
            k: 0.8,
            decay: 0.15,
            gamma: 0.005,
        };

        let (cpu_p, cpu_a, cpu_f) =
            sparse_knn_derivatives_cpu(&phase, &amplitude, &frequency, &graph, &params).unwrap();
        let (out_p, out_a, out_f) =
            try_sparse_knn_coupling_cuda(&phase, &amplitude, &frequency, &graph, &params).unwrap();

        assert_allclose(&out_p, &cpu_p, 1e-5, 1e-6);
        assert_allclose(&out_a, &cpu_a, 1e-5, 1e-6);
        assert_allclose(&out_f, &cpu_f, 1e-5, 1e-6);
    }

    #[test]
    fn cuda_backend_rejects_mismatched_lengths() {
        let n = 8;
        let graph = ring_graph(n, 1);
        let phase = vec![0.0_f32; n];
        let amplitude = vec![1.0_f32; n + 1];
        let frequency = vec![0.0_f32; n];
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };
        let err = try_sparse_knn_coupling_cuda(&phase, &amplitude, &frequency, &graph, &params)
            .unwrap_err();
        assert!(matches!(err, SparseKnnError::LengthMismatch { .. }));
    }
}

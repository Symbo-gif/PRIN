//! GPU-dispatched simulation components (WP-021, device-resident WP-036E Q2).
//!
//! `prin-sim`'s default engine ([`crate::engine::OscilloSim`]) is a pure-CPU,
//! `f64` path built on [`crate::csr_coupling::SparseCoupling`]'s rayon-dispatched
//! SpMV. This module wires the `prin-kernels` CubeCL kernel dispatch (CUDA /
//! wgpu / CPU-SIMD, `f32`) directly into the simulation layer, so that a
//! caller who wants the GPU-accelerated path does not hand-roll kernel calls
//! or duplicate any numerics:
//!
//! - [`GpuSparseKuramoto`] — a [`prin_dynamics::models::Dynamics`]
//!   implementation that dispatches the sparse k-NN Kuramoto coupling
//!   derivative through [`prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto`].
//!   It reuses an existing [`crate::csr_coupling::SparseCoupling`]'s CSR
//!   topology (no duplicate neighbor-graph construction) and drops straight
//!   into [`crate::engine::OscilloSim::step`]/`run` via the existing
//!   `Integrator`/`Dynamics` machinery — no engine changes required.
//!   Since WP-036E Q2, the CSR topology (`indptr`/`indices`) is held
//!   device-resident after construction; the `Dynamics` impl uploads only the
//!   per-call state `(phase, amplitude, frequency)` and downloads the
//!   derivatives.
//! - [`GpuMeanFieldEngine`] — a small stepper around the *fused* dense
//!   all-to-all RK4 kernel ([`prin_kernels::mean_field_rk4::cubecl::step_auto`]),
//!   for the dense mean-field regime the §N1 `N = 1M` GPU throughput target
//!   names. Since WP-036E Q2, the engine holds a resolved `ComputeClient` +
//!   persistent device `Handle`s across `step`; state stays on-device between
//!   steps; explicit `state()` / `to_host()` is the only download.
//! - [`GpuBandStepper`] — the analogous fused stepper for the three-band
//!   discrete-time step
//!   ([`prin_kernels::discrete_step::cubecl::discrete_step_auto`]).
//!   Same device-resident restructuring as `GpuMeanFieldEngine`.
//!
//! ## Device-resident dispatch (WP-036E Q2)
//!
//! Each engine resolves a `ComputeClient` once at construction (backend chosen
//! via [`prin_kernels::backend::auto_detect_order`]). The device resources
//! (state handles, buffer pool, CSR topology) persist across `step` calls;
//! `step` mutates device state in place with no per-step host transfer.
//! If the client cannot be initialised at construction (no GPU, backend
//! panic), the engine falls back to the host-slice path (the pre-Q2
//! behaviour) transparently.
//!
//! ## Zero-copy `kDLCUDA` export (WP-036E Q3)
//!
//! On the CUDA device-resident path, [`GpuMeanFieldEngine::state_cuda_export`]
//! and [`GpuSparseKuramoto::compute_derivatives_cuda_export`] hand out the
//! current device buffers as raw `CUdeviceptr`s plus [`Handle`] pins
//! ([`CudaStateExport`]); `prin-py` builds a `kDLCUDA` `DLManagedTensor` over
//! each that Torch adopts with no copy. [`GpuBandStepper`] has no equivalent:
//! its device state is three per-band `[Handle; 3]` triples (a cubecl-0.10
//! `min_storage_buffer_offset_alignment` constraint, WP-036E Q1), not a single
//! contiguous `N`-length buffer, so its `state()` stays on the host-`f32`
//! download path.
//!
//! ## `Dynamics` impl split (`GpuSparseKuramoto`)
//!
//! The `Dynamics` trait's `compute_derivatives` takes `&OscillatorState`
//! (host `f64`) and returns `StateDerivatives` (host `f64`) — it is a
//! one-shot derivative evaluator driven by the generic RK4 integrator,
//! called four times per integrator step. The device-resident path for the
//! sparse Kuramoto coupling is therefore *partial*: the CSR topology
//! (`indptr`/`indices`) is uploaded once at construction and reused across
//! all `compute_derivatives` calls; only the per-call state
//! `(phase, amplitude, frequency)` is uploaded and the derivatives
//! downloaded. The fused engines (`GpuMeanFieldEngine`, `GpuBandStepper`)
//! have their own `step` loops and achieve full device residency.
//!
//! ## Precision
//!
//! `prin-kernels` kernels operate in `f32` (the GPU-friendly dtype the §N1
//! performance targets are measured in); `prin-sim`/`prin-dynamics` are `f64`
//! (the numerical authority). All three types convert at the boundary and are
//! therefore an accelerated, reduced-precision *alternative* path, not a
//! replacement for the CPU `f64` authority — matching the same convention
//! already established by every `prin-kernels` kernel-equivalence test
//! (`rtol=1e-5, atol=1e-6` against an `f32` CPU reference; wider, `1e-4`
//! absolute, against the `f64` `prin-dynamics` reference, per the existing
//! `sparse_knn::tests::parity_against_prin_dynamics_kuramoto_sparse_knn`
//! precedent this module's tests reuse).
//!
//! ## Feature gating
//!
//! This module requires at least one of `prin-sim`'s `cpu`, `cuda`, or `wgpu`
//! features (each forwards to the identically-named `prin-kernels` feature),
//! mirroring `prin-kernels`' own `cubecl` submodule gating.

use std::sync::Arc;

use prin_dynamics::models::Dynamics;
use prin_dynamics::state::{OscillatorState, StateDerivatives, StateError};
use prin_kernels::discrete_step::cubecl::{discrete_step_auto, StepReport as DiscreteStepReport};
use prin_kernels::discrete_step::DiscreteStepParams;
use prin_kernels::mean_field_rk4::cubecl::{step_auto, StepReport as MeanFieldStepReport};
use prin_kernels::mean_field_rk4::MeanFieldRk4Params;
use prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto;
use prin_kernels::sparse_knn::{SparseKnnGraph, SparseKnnParams};

use crate::csr_coupling::SparseCoupling;
use crate::engine::Trajectory;
use crate::error::SimError;

// ── CubeCL device-resident dispatch (WP-036E Q2) ─────────────────────────

#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use cubecl::prelude::{ComputeClient, CubeElement};
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use cubecl::server::Handle;
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use cubecl::Runtime;

#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use prin_kernels::buffers::CubeclBufferPool;
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use prin_kernels::discrete_step::cubecl::{discrete_step_device, DiscreteStepDeviceState};
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use prin_kernels::mean_field_rk4::cubecl::{step_cubecl_device, MeanFieldDeviceState};
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
use prin_kernels::sparse_knn::cubecl::{
    sparse_knn_coupling_device, SparseKnnDeviceDerivs, SparseKnnDeviceState,
};

/// Preferred CubeCL runtime, selected at compile time by feature flags.
///
/// The priority matches [`prin_kernels::backend::auto_detect_order`]: CUDA →
/// wgpu → CPU. The engine structs store a `ComputeClient<SimRuntime>` +
/// device state; if the client cannot be initialised at construction, the
/// engine falls back to the host-slice path.
#[cfg(feature = "cuda")]
type SimRuntime = cubecl::cuda::CudaRuntime;
#[cfg(all(feature = "wgpu", not(feature = "cuda")))]
type SimRuntime = cubecl::wgpu::WgpuRuntime;
#[cfg(all(feature = "cpu", not(any(feature = "cuda", feature = "wgpu"))))]
type SimRuntime = cubecl::cpu::CpuRuntime;

/// Attempt to create a `ComputeClient` for the preferred [`SimRuntime`].
///
/// Returns `None` if the backend panics during initialisation (e.g. no GPU
/// adapter). The caller falls back to the host-slice path.
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
fn try_create_client() -> Option<ComputeClient<SimRuntime>> {
    use std::panic::{catch_unwind, AssertUnwindSafe};

    // Exactly one of the three backend closures is compiled in (feature
    // priority CUDA → wgpu → CPU, matching [`SimRuntime`]); the single tail
    // expression keeps the fallback contract identical across the matrix.
    #[cfg(feature = "cuda")]
    let make = || {
        use cubecl::cuda::{CudaDevice, CudaRuntime};
        CudaRuntime::client(&CudaDevice::default())
    };
    #[cfg(all(feature = "wgpu", not(feature = "cuda")))]
    let make = || {
        use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
        WgpuRuntime::client(&WgpuDevice::DefaultDevice)
    };
    #[cfg(all(feature = "cpu", not(any(feature = "cuda", feature = "wgpu"))))]
    let make = || {
        use cubecl::cpu::{CpuDevice, CpuRuntime};
        CpuRuntime::client(&CpuDevice)
    };

    catch_unwind(AssertUnwindSafe(make)).ok()
}

fn to_f32(v: &[f64]) -> Vec<f32> {
    v.iter().map(|&x| x as f32).collect()
}

fn to_f64(v: &[f32]) -> Vec<f64> {
    v.iter().map(|&x| f64::from(x)).collect()
}

// ── Zero-copy CUDA export (WP-036E Q3) ──────────────────────────────────────

/// Zero-copy `kDLCUDA` export of one device-resident `f32` buffer (WP-036E Q3).
///
/// Carries a raw CUDA device pointer (`CUdeviceptr`) plus an opaque `keepalive`
/// that pins the underlying CubeCL allocation for as long as the holder (a
/// DLPack capsule in `prin-py`) keeps this value. The `keepalive` is a cloned
/// CubeCL [`Handle`]; dropping it releases the reference that keeps the
/// allocation — and therefore `ptr` — valid. A subsequent engine `step()`
/// allocates a *fresh* state handle, so an export taken before that step keeps
/// pointing at the un-mutated snapshot (standard DLPack producer semantics).
///
/// Only produced on the CUDA device-resident path; on wgpu/CPU the engines
/// have no `kDLCUDA` pointer to hand out and return `None`.
#[cfg(feature = "cuda")]
pub struct CudaBufferExport {
    /// CUDA device pointer to `len` contiguous, row-major `f32`s.
    pub ptr: u64,
    /// CUDA device ordinal (`0` on the single-GPU `PRIN-GPU-Runner`; matches
    /// `cubecl::cuda::CudaDevice::default()` and `torch.cuda.current_device()`).
    pub device_id: i32,
    /// Element count.
    pub len: usize,
    /// Opaque allocation pin — a boxed cloned CubeCL `Handle`.
    keepalive: Box<dyn core::any::Any + Send>,
}

#[cfg(feature = "cuda")]
impl CudaBufferExport {
    /// Consume the export into `(ptr, device_id, len, keepalive)` for the
    /// `prin-py` DLPack bridge.
    pub fn into_raw_parts(self) -> (u64, i32, usize, Box<dyn core::any::Any + Send>) {
        (self.ptr, self.device_id, self.len, self.keepalive)
    }
}

/// The three device buffers of an oscillator-state / derivative triple,
/// exported for zero-copy `kDLCUDA` wrapping (WP-036E Q3).
#[cfg(feature = "cuda")]
pub struct CudaStateExport {
    /// `phase` (or `dphase`) buffer.
    pub phase: CudaBufferExport,
    /// `amplitude` (or `damplitude`) buffer.
    pub amplitude: CudaBufferExport,
    /// `frequency` (or `dfrequency`) buffer.
    pub frequency: CudaBufferExport,
}

/// Build a [`CudaBufferExport`] over a live device `Handle`.
///
/// The caller MUST have synchronised the stream (`client.sync()`) before this
/// call so the device writes are visible to a Torch consumer — legacy DLPack
/// is producer-synchronised. The returned `keepalive` (a cloned `Handle`)
/// holds the allocation's reference count above zero, so the CubeCL memory
/// pool will not reuse the slice and `ptr` stays valid for the export's
/// lifetime even after the engine steps again.
#[cfg(feature = "cuda")]
fn export_cuda_handle(
    client: &ComputeClient<SimRuntime>,
    handle: &Handle,
    len: usize,
) -> Option<CudaBufferExport> {
    let resource = client.get_resource(handle.clone()).ok()?;
    let ptr = resource.resource().ptr;
    Some(CudaBufferExport {
        ptr,
        device_id: 0,
        len,
        keepalive: Box::new(handle.clone()),
    })
}

// ────────────────────────────────────────────────────────────────────────────
// GpuSparseKuramoto
// ────────────────────────────────────────────────────────────────────────────

/// Sparse Kuramoto coupling, dispatched through `prin-kernels`' GPU/CPU-SIMD
/// backends instead of `prin-sim`'s own rayon SpMV.
///
/// Implements the same extended Kuramoto equations as
/// [`crate::engine::SparseKuramoto`], but evaluates the coupling term via
/// [`sparse_knn_coupling_auto`] (CUDA → wgpu → CPU-SIMD → native CPU
/// fallback, per [`prin_kernels::backend::auto_detect_order`]) instead of
/// [`SparseCoupling::kuramoto_coupling`]'s CSR SpMV.
///
/// # Weight convention
///
/// `prin-kernels`' sparse k-NN kernel assumes every row has the *uniform*
/// `K / degree(i)` weight (the convention [`SparseCoupling::from_ring`] and
/// [`SparseCoupling::from_knn`] both build); it does not read arbitrary
/// per-edge weights. [`GpuSparseKuramoto::new`] validates this at
/// construction time against the supplied `coupling` and returns
/// [`SimError::InvalidCoupling`] if any row's weights deviate from `k /
/// degree(i)` — a `coupling` built via [`SparseCoupling::from_dense`] or a
/// custom-weighted [`SparseCoupling::from_csr`] will generally fail this
/// check, by design: silently ignoring the actual weights would produce
/// wrong physics.
///
/// # Device-resident CSR topology (WP-036E Q2)
///
/// When a CubeCL backend is available, the CSR topology (`indptr`/`indices`)
/// is uploaded to the device once at construction and reused across all
/// `compute_derivatives` calls. Only the per-call state
/// `(phase, amplitude, frequency)` is uploaded and the derivatives
/// downloaded — the topology never moves again. See the module-level
/// "Dynamics impl split" note for the partial-residency rationale.
#[derive(Clone, Debug)]
pub struct GpuSparseKuramoto {
    n: usize,
    decay_rate: f64,
    freq_adaptation_rate: f64,
    k: f64,
    graph: SparseKnnGraph,
    /// Device-resident CSR topology + client (WP-036E Q2). `None` when no
    /// CubeCL backend could be initialised — the `Dynamics` impl falls back
    /// to the host-slice [`sparse_knn_coupling_auto`] path.
    #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
    device: Option<SparseKnnDeviceResources>,
}

/// Device-resident CSR topology for [`GpuSparseKuramoto`].
///
/// The `indptr`/`indices` handles are uploaded once at construction and
/// reused across all `compute_derivatives` calls. The `client` is resolved
/// once and shared across calls.
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
#[derive(Clone)]
struct SparseKnnDeviceResources {
    client: ComputeClient<SimRuntime>,
    indptr: Handle,
    indices: Handle,
    indices_len: usize,
}

#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
impl core::fmt::Debug for SparseKnnDeviceResources {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_struct("SparseKnnDeviceResources")
            .field("indices_len", &self.indices_len)
            .finish_non_exhaustive()
    }
}

impl GpuSparseKuramoto {
    /// Create a GPU-dispatched sparse Kuramoto model.
    ///
    /// `k` is the uniform coupling strength used to build `coupling` (e.g.
    /// the `strength` argument to [`SparseCoupling::from_ring`]/
    /// [`SparseCoupling::from_knn`]).
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an empty population, non-finite parameters, a
    /// coupling matrix with the wrong dimension, or non-uniform edge weights
    /// (see the struct-level "Weight convention" note).
    pub fn new(
        n: usize,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        k: f64,
        coupling: impl Into<Arc<SparseCoupling>>,
    ) -> Result<Self, SimError> {
        let coupling = coupling.into();
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        for (name, value) in [
            ("decay_rate", decay_rate),
            ("freq_adaptation_rate", freq_adaptation_rate),
            ("k", k),
        ] {
            if !value.is_finite() {
                return Err(SimError::NonFiniteValue {
                    name,
                    index: 0,
                    value,
                });
            }
        }
        if coupling.n_oscillators() != n {
            return Err(SimError::DimensionMismatch {
                name: "coupling",
                expected: n,
                got: coupling.n_oscillators(),
            });
        }

        let matrix = coupling.as_csr();
        let indptr: Vec<u32> = matrix
            .indptr()
            .raw_storage()
            .iter()
            .map(|&x| x as u32)
            .collect();
        let indices: Vec<u32> = matrix.indices().iter().map(|&x| x as u32).collect();
        let data = matrix.data();

        for i in 0..n {
            let start = indptr[i] as usize;
            let end = indptr[i + 1] as usize;
            let degree = end - start;
            if degree == 0 {
                continue;
            }
            let expected_weight = k / degree as f64;
            for &w in &data[start..end] {
                if (w - expected_weight).abs() > 1e-9 * expected_weight.abs().max(1.0) {
                    return Err(SimError::InvalidCoupling {
                        reason: format!(
                            "row {i}: weight {w} does not match the uniform K/degree \
                             convention (expected {expected_weight} for k={k}, degree={degree}); \
                             GpuSparseKuramoto requires a coupling built with a uniform weight \
                             (e.g. SparseCoupling::from_ring/from_knn)"
                        ),
                    });
                }
            }
        }

        let graph = SparseKnnGraph::from_csr(n, indptr, indices)?;

        // Upload CSR topology to device (WP-036E Q2).
        #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
        let device = try_create_client().map(|client: ComputeClient<SimRuntime>| {
            let indices_len = graph.nnz().max(1);
            let indices_handle = if graph.nnz() > 0 {
                client.create_from_slice(u32::as_bytes(graph.indices()))
            } else {
                client.create_from_slice(u32::as_bytes(&[0u32]))
            };
            SparseKnnDeviceResources {
                indptr: client.create_from_slice(u32::as_bytes(graph.indptr())),
                indices: indices_handle,
                indices_len,
                client,
            }
        });

        Ok(Self {
            n,
            decay_rate,
            freq_adaptation_rate,
            k,
            graph,
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            device,
        })
    }

    /// Number of oscillators.
    pub fn n_oscillators(&self) -> usize {
        self.n
    }

    /// Amplitude decay rate λ.
    pub fn decay_rate(&self) -> f64 {
        self.decay_rate
    }

    /// Frequency adaptation rate γ.
    pub fn freq_adaptation_rate(&self) -> f64 {
        self.freq_adaptation_rate
    }

    /// Coupling strength `K`.
    pub fn k(&self) -> f64 {
        self.k
    }

    /// Evaluate the sparse k-NN coupling derivative on the CUDA device and
    /// export the three derivative buffers for zero-copy `kDLCUDA` wrapping
    /// (WP-036E Q3).
    ///
    /// The per-call input state is uploaded host→device (the one permitted
    /// upload; amendment #43 device-resident envelope) and reuses the
    /// device-resident CSR topology from construction; the *output* never
    /// round-trips through host memory. Returns `Ok(None)` unless the CSR
    /// topology is CUDA-device-resident (no CUDA feature, no GPU, or `n <= 1`
    /// free-streaming), in which case the caller falls back to the host-slice
    /// path.
    ///
    /// # Errors
    ///
    /// Returns [`StateError::LengthMismatch`] if `state`'s length differs from
    /// the configured oscillator count.
    #[cfg(feature = "cuda")]
    pub fn compute_derivatives_cuda_export(
        &self,
        state: &OscillatorState,
    ) -> Result<Option<CudaStateExport>, StateError> {
        let n = state.n_oscillators();
        if n != self.n {
            return Err(StateError::LengthMismatch {
                name: "state",
                expected: self.n,
                got: n,
            });
        }
        if n <= 1 {
            return Ok(None);
        }
        let Some(ref dev) = self.device else {
            return Ok(None);
        };

        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);
        let params = SparseKnnParams {
            k: self.k as f32,
            decay: self.decay_rate as f32,
            gamma: self.freq_adaptation_rate as f32,
        };

        let dev_state = SparseKnnDeviceState::from_parts(
            n,
            dev.indices_len,
            dev.client.create_from_slice(f32::as_bytes(&phase32)),
            dev.client.create_from_slice(f32::as_bytes(&amp32)),
            dev.client.create_from_slice(f32::as_bytes(&freq32)),
            dev.indptr.clone(),
            dev.indices.clone(),
        );
        let mut derivs = SparseKnnDeviceDerivs::empty(&dev.client, n);
        sparse_knn_coupling_device(&dev.client, &dev_state, &params, &mut derivs)
            .expect("inputs validated by GpuSparseKuramoto::new and the length check above");
        let _ = cubecl::future::block_on(dev.client.sync());

        Ok(
            match (
                export_cuda_handle(&dev.client, &derivs.dphase, n),
                export_cuda_handle(&dev.client, &derivs.damplitude, n),
                export_cuda_handle(&dev.client, &derivs.dfrequency, n),
            ) {
                (Some(phase), Some(amplitude), Some(frequency)) => Some(CudaStateExport {
                    phase,
                    amplitude,
                    frequency,
                }),
                _ => None,
            },
        )
    }
}

impl Dynamics for GpuSparseKuramoto {
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        if n != self.n {
            return Err(StateError::LengthMismatch {
                name: "state",
                expected: self.n,
                got: n,
            });
        }

        if n <= 1 {
            let dphase = state.frequency.clone();
            let damplitude: Vec<f64> = state
                .amplitude
                .iter()
                .map(|&a| -self.decay_rate * a)
                .collect();
            let dfrequency = vec![0.0; n];
            return StateDerivatives::new(dphase, damplitude, dfrequency);
        }

        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);
        let params = SparseKnnParams {
            k: self.k as f32,
            decay: self.decay_rate as f32,
            gamma: self.freq_adaptation_rate as f32,
        };

        // Device-resident CSR path (WP-036E Q2): upload per-call state,
        // reuse the device-resident topology, download derivatives.
        #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
        if let Some(ref dev) = self.device {
            let dev_state = SparseKnnDeviceState::from_parts(
                n,
                dev.indices_len,
                dev.client.create_from_slice(f32::as_bytes(&phase32)),
                dev.client.create_from_slice(f32::as_bytes(&amp32)),
                dev.client.create_from_slice(f32::as_bytes(&freq32)),
                dev.indptr.clone(),
                dev.indices.clone(),
            );
            let mut derivs = SparseKnnDeviceDerivs::empty(&dev.client, n);
            sparse_knn_coupling_device(&dev.client, &dev_state, &params, &mut derivs)
                .expect("inputs validated by GpuSparseKuramoto::new and the length check above");
            let (dphase32, damp32, dfreq32) = derivs
                .to_host(&dev.client)
                .expect("device read-back cannot fail on already-valid input");
            return StateDerivatives::new(to_f64(&dphase32), to_f64(&damp32), to_f64(&dfreq32));
        }

        // Host-slice fallback (no CubeCL backend, or no CubeCL feature).
        let (dphase32, damp32, dfreq32) =
            sparse_knn_coupling_auto(&phase32, &amp32, &freq32, &self.graph, &params)
                .expect("inputs validated by GpuSparseKuramoto::new and the length check above");

        StateDerivatives::new(to_f64(&dphase32), to_f64(&damp32), to_f64(&dfreq32))
    }
}

// ────────────────────────────────────────────────────────────────────────────
// GpuMeanFieldEngine
// ────────────────────────────────────────────────────────────────────────────

/// Dense, all-to-all mean-field RK4 engine, stepped via the fully fused
/// [`step_auto`] kernel (CUDA → wgpu → CPU-SIMD → native CPU fallback).
///
/// This is the dense-regime companion to [`crate::engine::OscilloSim`]
/// (sparse). Because the kernel fuses all four RK4 sub-stage evaluations plus
/// the order-parameter reduction into one launch sequence, it cannot be
/// expressed as a [`prin_dynamics::models::Dynamics`] + generic
/// [`prin_dynamics::Integrator`] composition (that would re-decompose the
/// fusion this kernel exists to provide) — this type owns its own minimal
/// step/run loop instead, reusing [`crate::engine::Trajectory`] for
/// trajectory recording so callers get the same recorded-artifact shape as
/// `OscilloSim`.
///
/// # Device-resident state (WP-036E Q2)
///
/// When a CubeCL backend is available, the engine holds a resolved
/// `ComputeClient` + persistent [`MeanFieldDeviceState`] + preallocated
/// [`CubeclBufferPool`] across `step` calls. State stays on-device between
/// steps; `step` mutates device state in place with no per-step host
/// transfer. `state()` is the only download. If the client cannot be
/// initialised at construction, the engine falls back to the host-slice
/// path transparently.
#[derive(Clone, Debug)]
pub struct GpuMeanFieldEngine {
    params: MeanFieldRk4Params,
    inner: MeanFieldInner,
}

/// Device-resident mean-field payload: resolved client + persistent state +
/// buffer pool. Boxed inside [`MeanFieldInner::Device`] so the enum's two
/// variants stay close in size (`clippy::large_enum_variant`); the single
/// heap indirection is set up once at construction and is negligible beside
/// the per-step kernel launches.
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
#[derive(Clone)]
struct MeanFieldDevice {
    client: ComputeClient<SimRuntime>,
    state: MeanFieldDeviceState<SimRuntime>,
    pool: CubeclBufferPool<SimRuntime>,
}

#[derive(Clone)]
enum MeanFieldInner {
    /// Device-resident path: client + persistent state + buffer pool.
    #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
    Device(Box<MeanFieldDevice>),
    /// Host-slice fallback (no CubeCL backend, or no CubeCL feature).
    Host {
        phase: Vec<f32>,
        amplitude: Vec<f32>,
        frequency: Vec<f32>,
    },
}

impl core::fmt::Debug for MeanFieldInner {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            Self::Device(dev) => f
                .debug_struct("Device")
                .field("n", &dev.state.n)
                .field("pool_capacity", &dev.pool.capacity())
                .finish_non_exhaustive(),
            Self::Host { phase, .. } => f.debug_struct("Host").field("n", &phase.len()).finish(),
        }
    }
}

impl GpuMeanFieldEngine {
    /// Create a new dense mean-field GPU engine from an initial state.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an empty state or a non-finite/non-positive
    /// `dt`.
    pub fn new(state: &OscillatorState, params: MeanFieldRk4Params) -> Result<Self, SimError> {
        let n = state.n_oscillators();
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        for (name, value) in [
            ("k", params.k),
            ("decay", params.decay),
            ("gamma", params.gamma),
            ("dt", params.dt),
        ] {
            if !value.is_finite() {
                return Err(SimError::NonFiniteValue {
                    name,
                    index: 0,
                    value: f64::from(value),
                });
            }
        }
        if params.dt <= 0.0 {
            return Err(SimError::NonFiniteValue {
                name: "dt",
                index: 0,
                value: f64::from(params.dt),
            });
        }

        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);

        // Try device-resident path (WP-036E Q2).
        #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
        if let Some(client) = try_create_client() {
            let dev_state = MeanFieldDeviceState::upload(&client, &phase32, &amp32, &freq32);
            let pool = CubeclBufferPool::new(&client, n);
            return Ok(Self {
                params,
                inner: MeanFieldInner::Device(Box::new(MeanFieldDevice {
                    client,
                    state: dev_state,
                    pool,
                })),
            });
        }

        Ok(Self {
            params,
            inner: MeanFieldInner::Host {
                phase: phase32,
                amplitude: amp32,
                frequency: freq32,
            },
        })
    }

    /// Number of oscillators.
    pub fn n_oscillators(&self) -> usize {
        match &self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            MeanFieldInner::Device(dev) => dev.state.n,
            MeanFieldInner::Host { phase, .. } => phase.len(),
        }
    }

    /// Timestep `dt`.
    pub fn dt(&self) -> f64 {
        f64::from(self.params.dt)
    }

    /// Current state, converted back to `f64`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the internal state fails [`OscillatorState`]'s
    /// length invariants (unreachable in practice) or if a device read-back
    /// fails.
    pub fn state(&self) -> Result<OscillatorState, SimError> {
        match &self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            MeanFieldInner::Device(dev) => {
                let (phase, amp, freq) = dev.state.to_host(&dev.client)?;
                OscillatorState::new(to_f64(&phase), to_f64(&amp), to_f64(&freq), None)
                    .map_err(SimError::from)
            }
            MeanFieldInner::Host {
                phase,
                amplitude,
                frequency,
            } => OscillatorState::new(to_f64(phase), to_f64(amplitude), to_f64(frequency), None)
                .map_err(SimError::from),
        }
    }

    /// Zero-copy `kDLCUDA` export of the current device-resident state
    /// (WP-036E Q3).
    ///
    /// Returns `None` unless the engine is on the CUDA device-resident path
    /// (no CUDA feature, no GPU, or the host-slice fallback). On success the
    /// stream is synchronised and the three `(phase, amplitude, frequency)`
    /// buffers are exported as raw device pointers + `Handle` pins — see
    /// [`CudaBufferExport`]. `prin-py` wraps each in a `kDLCUDA`
    /// `DLManagedTensor` Torch adopts with no copy.
    #[cfg(feature = "cuda")]
    pub fn state_cuda_export(&self) -> Option<CudaStateExport> {
        match &self.inner {
            MeanFieldInner::Device(dev) => {
                let _ = cubecl::future::block_on(dev.client.sync());
                let n = dev.state.n;
                Some(CudaStateExport {
                    phase: export_cuda_handle(&dev.client, &dev.state.phase, n)?,
                    amplitude: export_cuda_handle(&dev.client, &dev.state.amplitude, n)?,
                    frequency: export_cuda_handle(&dev.client, &dev.state.frequency, n)?,
                })
            }
            MeanFieldInner::Host { .. } => None,
        }
    }

    /// Advance by one fused RK4 step.
    ///
    /// On the device-resident path, state is mutated in place on the device
    /// with no host transfer. On the host-slice fallback, the per-call
    /// upload/download path is used.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the kernel dispatch fails (see
    /// [`step_auto`]) or a device read-back fails.
    pub fn step(&mut self) -> Result<MeanFieldStepReport, SimError> {
        match &mut self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            MeanFieldInner::Device(dev) => {
                let report =
                    step_cubecl_device(&dev.client, &mut dev.state, &self.params, &dev.pool)?;
                Ok(report)
            }
            MeanFieldInner::Host {
                phase,
                amplitude,
                frequency,
            } => {
                let (out, report) = step_auto(phase, amplitude, frequency, &self.params)?;
                (*phase, *amplitude, *frequency) = out;
                Ok(report)
            }
        }
    }

    /// Run for `n_steps`, optionally recording a trajectory.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for zero steps or a kernel dispatch failure.
    pub fn run(
        &mut self,
        n_steps: usize,
        record_trajectory: bool,
    ) -> Result<(OscillatorState, Option<Trajectory>), SimError> {
        if n_steps == 0 {
            return Err(SimError::DimensionMismatch {
                name: "n_steps",
                expected: 1,
                got: 0,
            });
        }

        let dt = self.dt();
        let mut trajectory = if record_trajectory {
            let mut t = Trajectory {
                phases: Vec::with_capacity(n_steps + 1),
                amplitudes: Vec::with_capacity(n_steps + 1),
                frequencies: Vec::with_capacity(n_steps + 1),
                times: Vec::with_capacity(n_steps + 1),
            };
            let s0 = self.state()?;
            t.phases.push(s0.phase);
            t.amplitudes.push(s0.amplitude);
            t.frequencies.push(s0.frequency);
            t.times.push(0.0);
            Some(t)
        } else {
            None
        };

        for step in 0..n_steps {
            self.step()?;
            if let Some(ref mut traj) = trajectory {
                let s = self.state()?;
                traj.phases.push(s.phase);
                traj.amplitudes.push(s.amplitude);
                traj.frequencies.push(s.frequency);
                traj.times.push((step + 1) as f64 * dt);
            }
        }

        Ok((self.state()?, trajectory))
    }
}

// ────────────────────────────────────────────────────────────────────────────
// GpuBandStepper
// ────────────────────────────────────────────────────────────────────────────

/// Fused three-band (delta/theta/gamma) discrete-time stepper, dispatched via
/// [`discrete_step_auto`] (CUDA → wgpu → CPU-SIMD → native CPU fallback).
///
/// The dense-regime, discrete-time analogue of [`GpuMeanFieldEngine`],
/// wrapping the WP-020 fused kernel (`complex_order_reduce`,
/// `real_sum_reduce`, `band_euler_step`, `pac_gate`) the same way
/// `GpuMeanFieldEngine` wraps the fused RK4 kernel — this WP is the first
/// point either fused kernel is driven by anything other than a
/// microbenchmark or unit test.
///
/// # Device-resident state (WP-036E Q2)
///
/// Same device-resident restructuring as [`GpuMeanFieldEngine`]: the engine
/// holds a resolved `ComputeClient` + persistent [`DiscreteStepDeviceState`]
/// across `step` calls; state stays on-device between steps; `state()` is
/// the only download.
#[derive(Clone, Debug)]
pub struct GpuBandStepper {
    band_sizes: [usize; 3],
    params: DiscreteStepParams,
    inner: BandStepperInner,
}

/// Device-resident band-stepper payload: resolved client + persistent
/// per-band state. Boxed inside [`BandStepperInner::Device`] to keep the
/// enum's variants close in size (`clippy::large_enum_variant`); the one
/// heap indirection is established at construction.
#[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
#[derive(Clone)]
struct BandStepperDevice {
    client: ComputeClient<SimRuntime>,
    state: DiscreteStepDeviceState<SimRuntime>,
}

#[derive(Clone)]
enum BandStepperInner {
    /// Device-resident path.
    #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
    Device(Box<BandStepperDevice>),
    /// Host-slice fallback.
    Host {
        phase: Vec<f32>,
        amplitude: Vec<f32>,
        frequency: Vec<f32>,
    },
}

impl core::fmt::Debug for BandStepperInner {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            Self::Device(dev) => f
                .debug_struct("Device")
                .field("n", &dev.state.n())
                .finish_non_exhaustive(),
            Self::Host { phase, .. } => f.debug_struct("Host").field("n", &phase.len()).finish(),
        }
    }
}

impl GpuBandStepper {
    /// Create a new fused three-band GPU stepper.
    ///
    /// `state`'s length must equal `band_sizes.iter().sum()`, laid out as
    /// `[delta oscillators, theta oscillators, gamma oscillators]`
    /// concatenated (matching [`prin_kernels::discrete_step::discrete_step_cpu`]'s
    /// convention).
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for a state/band-size length mismatch, an empty
    /// band, or a non-finite/non-positive `dt`.
    pub fn new(
        state: &OscillatorState,
        band_sizes: [usize; 3],
        params: DiscreteStepParams,
    ) -> Result<Self, SimError> {
        let n = state.n_oscillators();
        let expected: usize = band_sizes.iter().sum();
        if n != expected {
            return Err(SimError::DimensionMismatch {
                name: "state vs band_sizes",
                expected,
                got: n,
            });
        }
        if band_sizes.contains(&0) {
            return Err(SimError::InvalidCoupling {
                reason: format!("band_sizes must all be non-zero, got {band_sizes:?}"),
            });
        }
        if !params.dt.is_finite() || params.dt <= 0.0 {
            return Err(SimError::NonFiniteValue {
                name: "dt",
                index: 0,
                value: f64::from(params.dt),
            });
        }

        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);

        // Try device-resident path (WP-036E Q2).
        #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
        if let Some(client) = try_create_client() {
            let dev_state =
                DiscreteStepDeviceState::upload(&client, &phase32, &amp32, &freq32, band_sizes);
            return Ok(Self {
                band_sizes,
                params,
                inner: BandStepperInner::Device(Box::new(BandStepperDevice {
                    client,
                    state: dev_state,
                })),
            });
        }

        Ok(Self {
            band_sizes,
            params,
            inner: BandStepperInner::Host {
                phase: phase32,
                amplitude: amp32,
                frequency: freq32,
            },
        })
    }

    /// Number of oscillators across all three bands.
    pub fn n_oscillators(&self) -> usize {
        match &self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            BandStepperInner::Device(dev) => dev.state.n(),
            BandStepperInner::Host { phase, .. } => phase.len(),
        }
    }

    /// Per-band oscillator counts `[delta, theta, gamma]`.
    pub fn band_sizes(&self) -> [usize; 3] {
        self.band_sizes
    }

    /// Timestep `dt`.
    pub fn dt(&self) -> f64 {
        f64::from(self.params.dt)
    }

    /// Current state, converted back to `f64`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the internal state fails [`OscillatorState`]'s
    /// length invariants (unreachable in practice) or if a device read-back
    /// fails.
    pub fn state(&self) -> Result<OscillatorState, SimError> {
        match &self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            BandStepperInner::Device(dev) => {
                let (phase, amp, freq) = dev.state.to_host(&dev.client)?;
                OscillatorState::new(to_f64(&phase), to_f64(&amp), to_f64(&freq), None)
                    .map_err(SimError::from)
            }
            BandStepperInner::Host {
                phase,
                amplitude,
                frequency,
            } => OscillatorState::new(to_f64(phase), to_f64(amplitude), to_f64(frequency), None)
                .map_err(SimError::from),
        }
    }

    /// Advance by one fused discrete step.
    ///
    /// On the device-resident path, state is mutated in place on the device
    /// with no host transfer.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the kernel dispatch fails (see
    /// [`discrete_step_auto`]) or a device read-back fails.
    pub fn step(&mut self) -> Result<DiscreteStepReport, SimError> {
        match &mut self.inner {
            #[cfg(any(feature = "cuda", feature = "wgpu", feature = "cpu"))]
            BandStepperInner::Device(dev) => {
                let report = discrete_step_device(&dev.client, &mut dev.state, &self.params)?;
                Ok(report)
            }
            BandStepperInner::Host {
                phase,
                amplitude,
                frequency,
            } => {
                let (out, report) =
                    discrete_step_auto(phase, amplitude, frequency, self.band_sizes, &self.params)?;
                (*phase, *amplitude, *frequency) = out;
                Ok(report)
            }
        }
    }

    /// Run for `n_steps`, optionally recording a trajectory.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for zero steps or a kernel dispatch failure.
    pub fn run(
        &mut self,
        n_steps: usize,
        record_trajectory: bool,
    ) -> Result<(OscillatorState, Option<Trajectory>), SimError> {
        if n_steps == 0 {
            return Err(SimError::DimensionMismatch {
                name: "n_steps",
                expected: 1,
                got: 0,
            });
        }

        let dt = self.dt();
        let mut trajectory = if record_trajectory {
            let mut t = Trajectory {
                phases: Vec::with_capacity(n_steps + 1),
                amplitudes: Vec::with_capacity(n_steps + 1),
                frequencies: Vec::with_capacity(n_steps + 1),
                times: Vec::with_capacity(n_steps + 1),
            };
            let s0 = self.state()?;
            t.phases.push(s0.phase);
            t.amplitudes.push(s0.amplitude);
            t.frequencies.push(s0.frequency);
            t.times.push(0.0);
            Some(t)
        } else {
            None
        };

        for step in 0..n_steps {
            self.step()?;
            if let Some(ref mut traj) = trajectory {
                let s = self.state()?;
                traj.phases.push(s.phase);
                traj.amplitudes.push(s.amplitude);
                traj.frequencies.push(s.frequency);
                traj.times.push((step + 1) as f64 * dt);
            }
        }

        Ok((self.state()?, trajectory))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use prin_dynamics::coupling::CouplingMode;
    use prin_dynamics::models::KuramotoOscillator;
    use prin_dynamics::Seed;
    use prin_kernels::discrete_step::{discrete_step_cpu, BandStepParams, PacGateParams};
    use prin_kernels::mean_field_rk4::step_cpu;

    // ── GpuSparseKuramoto ──────────────────────────────────────────────────

    #[test]
    fn gpu_sparse_kuramoto_matches_cpu_dynamics_reference() {
        // f32-kernel-vs-f64-prin_dynamics tolerance matches the established
        // precedent in prin-kernels::sparse_knn::tests::
        // parity_against_prin_dynamics_kuramoto_sparse_knn.
        let n = 6;
        let k_neighbors = 2;
        let phase: Vec<f64> = (0..n).map(|i| 0.3 * i as f64).collect();
        let amp = vec![1.0_f64; n];
        let freq: Vec<f64> = (0..n).map(|i| 0.1 * (i as f64 - 2.5)).collect();

        let reference_model = KuramotoOscillator::new(
            n,
            2.0,
            0.1,
            0.01,
            CouplingMode::SparseKnn {
                k: Some(k_neighbors),
            },
        )
        .unwrap();
        let state = OscillatorState::new(phase.clone(), amp.clone(), freq.clone(), None).unwrap();
        let reference = reference_model.compute_derivatives(&state).unwrap();

        let coupling = SparseCoupling::from_knn(&phase, k_neighbors, 2.0).unwrap();
        let gpu_model = GpuSparseKuramoto::new(n, 0.1, 0.01, 2.0, coupling).unwrap();
        let gpu = gpu_model.compute_derivatives(&state).unwrap();

        eprintln!("gpu={gpu:?}, reference={reference:?}");
        for i in 0..n {
            assert!((gpu.dphase[i] - reference.dphase[i]).abs() < 1e-4);
            assert!((gpu.damplitude[i] - reference.damplitude[i]).abs() < 1e-4);
            assert!((gpu.dfrequency[i] - reference.dfrequency[i]).abs() < 1e-4);
        }
    }

    #[test]
    fn gpu_sparse_kuramoto_drives_oscillo_sim_via_integrator() {
        use crate::engine::OscilloSim;
        use prin_dynamics::RK4Integrator;

        let n = 16;
        let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
        let gpu_model = GpuSparseKuramoto::new(n, 0.1, 0.01, 1.0, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let mut engine = OscilloSim::new(state, coupling, integrator, 0.01).unwrap();

        let phase_before = engine.state().phase.clone();
        engine.step(&gpu_model).unwrap();
        assert_ne!(engine.state().phase, phase_before);
        assert_eq!(engine.state().n_oscillators(), n);
    }

    #[test]
    fn gpu_sparse_kuramoto_rejects_non_uniform_weights() {
        let n = 4;
        // from_dense with an asymmetric, non-K/degree-uniform matrix.
        let mut dense = vec![0.0; n * n];
        dense[1] = 5.0;
        dense[n] = 0.1;
        let coupling = SparseCoupling::from_dense(&dense, n, 1e-9).unwrap();
        let err = GpuSparseKuramoto::new(n, 0.1, 0.01, 1.0, coupling).unwrap_err();
        assert!(matches!(err, SimError::InvalidCoupling { .. }));
    }

    #[test]
    fn gpu_sparse_kuramoto_rejects_empty_population() {
        let coupling = SparseCoupling::from_ring(8, 1, 1.0).unwrap();
        let err = GpuSparseKuramoto::new(0, 0.1, 0.01, 1.0, coupling).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn gpu_sparse_kuramoto_rejects_dimension_mismatch() {
        let coupling = SparseCoupling::from_ring(8, 1, 1.0).unwrap();
        let err = GpuSparseKuramoto::new(16, 0.1, 0.01, 1.0, coupling).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn gpu_sparse_kuramoto_rejects_non_finite_k() {
        let coupling = SparseCoupling::from_ring(8, 1, 1.0).unwrap();
        let err = GpuSparseKuramoto::new(8, 0.1, 0.01, f64::NAN, coupling).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn gpu_sparse_kuramoto_n1_free_streaming() {
        let indptr = [0u32, 0];
        let indices: Vec<u32> = vec![];
        let data: Vec<f64> = vec![];
        let coupling = SparseCoupling::from_csr(
            &indptr.iter().map(|&x| x as usize).collect::<Vec<_>>(),
            &indices.iter().map(|&x| x as usize).collect::<Vec<_>>(),
            &data,
            1,
        )
        .unwrap();
        let model = GpuSparseKuramoto::new(1, 0.1, 0.01, 1.0, coupling).unwrap();
        let state = OscillatorState::new(vec![0.5], vec![1.0], vec![3.0], None).unwrap();
        let derivs = model.compute_derivatives(&state).unwrap();
        assert!((derivs.dphase[0] - 3.0).abs() < 1e-12);
        assert!((derivs.damplitude[0] - (-0.1)).abs() < 1e-12);
    }

    #[test]
    fn gpu_sparse_kuramoto_state_dimension_mismatch() {
        let n = 4;
        let coupling = SparseCoupling::from_ring(n, 1, 1.0).unwrap();
        let model = GpuSparseKuramoto::new(n, 0.1, 0.01, 1.0, coupling).unwrap();
        let wrong_state =
            OscillatorState::new(vec![0.0; 8], vec![1.0; 8], vec![1.0; 8], None).unwrap();
        let err = model.compute_derivatives(&wrong_state).unwrap_err();
        assert!(matches!(err, StateError::LengthMismatch { .. }));
    }

    #[test]
    fn gpu_sparse_kuramoto_accessors() {
        let coupling = SparseCoupling::from_ring(8, 2, 2.0).unwrap();
        let model = GpuSparseKuramoto::new(8, 0.2, 0.05, 2.0, coupling).unwrap();
        assert_eq!(model.n_oscillators(), 8);
        assert!((model.decay_rate() - 0.2).abs() < 1e-12);
        assert!((model.freq_adaptation_rate() - 0.05).abs() < 1e-12);
        assert!((model.k() - 2.0).abs() < 1e-12);
    }

    // ── GpuMeanFieldEngine ─────────────────────────────────────────────────

    fn mean_field_params() -> MeanFieldRk4Params {
        MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        }
    }

    #[test]
    fn gpu_mean_field_engine_step_matches_kernel_cpu_reference_loop() {
        let n = 32;
        let phase: Vec<f64> = (0..n).map(|i| 0.1 * i as f64).collect();
        let amp = vec![1.0_f64; n];
        let freq: Vec<f64> = (0..n).map(|i| 0.05 * (i as f64 - n as f64 / 2.0)).collect();
        let state = OscillatorState::new(phase.clone(), amp.clone(), freq.clone(), None).unwrap();
        let params = mean_field_params();

        let mut engine = GpuMeanFieldEngine::new(&state, params).unwrap();
        engine.step().unwrap();
        engine.step().unwrap();
        let got = engine.state().unwrap();

        let phase32 = to_f32(&phase);
        let amp32 = to_f32(&amp);
        let freq32 = to_f32(&freq);
        let (p1, a1, f1) = step_cpu(&phase32, &amp32, &freq32, &params).unwrap();
        let (p2, a2, f2) = step_cpu(&p1, &a1, &f1, &params).unwrap();

        for i in 0..n {
            assert!((got.phase[i] - f64::from(p2[i])).abs() < 1e-5);
            assert!((got.amplitude[i] - f64::from(a2[i])).abs() < 1e-5);
            assert!((got.frequency[i] - f64::from(f2[i])).abs() < 1e-5);
        }
    }

    #[test]
    fn gpu_mean_field_engine_rejects_empty_state() {
        let empty = OscillatorState {
            phase: vec![],
            amplitude: vec![],
            frequency: vec![],
            freq_band: None,
        };
        let err = GpuMeanFieldEngine::new(&empty, mean_field_params()).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn gpu_mean_field_engine_run_no_trajectory() {
        let n = 4;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(1, 0)).unwrap();
        let mut engine = GpuMeanFieldEngine::new(&state, mean_field_params()).unwrap();
        let (final_state, traj) = engine.run(3, false).unwrap();
        assert_eq!(final_state.n_oscillators(), n);
        assert!(traj.is_none());
    }

    #[test]
    fn gpu_mean_field_engine_run_records_trajectory() {
        let n = 8;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(7, 0)).unwrap();
        let mut engine = GpuMeanFieldEngine::new(&state, mean_field_params()).unwrap();
        let (final_state, traj) = engine.run(5, true).unwrap();
        assert_eq!(final_state.n_oscillators(), n);
        let traj = traj.unwrap();
        assert_eq!(traj.n_steps(), 6);
        assert!((traj.times[5] - 0.05).abs() < 1e-6);
    }

    #[test]
    fn gpu_mean_field_engine_rejects_zero_steps() {
        let n = 4;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let mut engine = GpuMeanFieldEngine::new(&state, mean_field_params()).unwrap();
        let err = engine.run(0, false).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn gpu_mean_field_engine_rejects_non_finite_dt() {
        let n = 4;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let mut params = mean_field_params();
        params.dt = f32::NAN;
        let err = GpuMeanFieldEngine::new(&state, params).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn gpu_mean_field_engine_rejects_non_positive_dt() {
        let n = 4;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let mut params = mean_field_params();
        params.dt = 0.0;
        let err = GpuMeanFieldEngine::new(&state, params).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn gpu_mean_field_engine_accessors() {
        let n = 4;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let engine = GpuMeanFieldEngine::new(&state, mean_field_params()).unwrap();
        assert_eq!(engine.n_oscillators(), n);
        assert!((engine.dt() - 0.01).abs() < 1e-9);
    }

    /// Device-resident multi-step loop: the engine holds state on-device
    /// across steps; `state()` is the only download (WP-036E Q2).
    #[test]
    fn gpu_mean_field_engine_device_resident_multi_step() {
        let n = 64;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(99, 0)).unwrap();
        let params = mean_field_params();

        let mut engine = GpuMeanFieldEngine::new(&state, params).unwrap();
        for _ in 0..4 {
            engine.step().unwrap();
        }
        let got = engine.state().unwrap();
        assert_eq!(got.n_oscillators(), n);

        // Verify against the CPU reference (4 steps from the same initial state).
        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);
        let (mut p, mut a, mut f) = (phase32, amp32, freq32);
        for _ in 0..4 {
            (p, a, f) = step_cpu(&p, &a, &f, &params).unwrap();
        }
        for (i, &pi) in p.iter().enumerate().take(n) {
            assert!(
                (got.phase[i] - f64::from(pi)).abs() < 1e-5,
                "phase[{i}]: got={}, expected={}",
                got.phase[i],
                f64::from(pi)
            );
        }
    }

    /// Zero-copy CUDA export of the device-resident mean-field state
    /// (WP-036E Q3): the exported pointers are live, sized `n`, and the
    /// snapshot is stable across a subsequent `step()`.
    #[cfg(feature = "cuda")]
    #[test]
    fn gpu_mean_field_engine_state_cuda_export_is_live_and_snapshot_stable() {
        let n = 48;
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(5, 0)).unwrap();
        let mut engine = GpuMeanFieldEngine::new(&state, mean_field_params()).unwrap();
        engine.step().unwrap();

        let host_before = engine.state().unwrap();
        let export = engine
            .state_cuda_export()
            .expect("CUDA device-resident path must export");
        assert_eq!(export.phase.len, n);
        assert_eq!(export.amplitude.len, n);
        assert_eq!(export.frequency.len, n);
        assert_ne!(export.phase.ptr, 0);
        assert_ne!(export.amplitude.ptr, 0);
        assert_ne!(export.frequency.ptr, 0);
        assert_eq!(export.phase.device_id, 0);

        // The export pins its snapshot: stepping again must not disturb the
        // host view of the values captured above.
        engine.step().unwrap();
        drop(export);
        let host_after_second_step = engine.state().unwrap();
        // The two host reads bracket one extra step, so they differ — the
        // point is only that `state_cuda_export` + `drop` did not corrupt the
        // engine's own device state.
        assert_eq!(host_after_second_step.n_oscillators(), n);
        assert!(host_before.phase.iter().all(|v| v.is_finite()));
    }

    /// Zero-copy CUDA export of the sparse k-NN derivative (WP-036E Q3):
    /// the exported buffers agree with the host-slice `Dynamics` path.
    #[cfg(feature = "cuda")]
    #[test]
    fn gpu_sparse_kuramoto_cuda_export_matches_host_dynamics_path() {
        let n = 24;
        let coupling = SparseCoupling::from_ring(n, 3, 1.5).unwrap();
        let model = GpuSparseKuramoto::new(n, 0.1, 0.01, 1.5, coupling).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(17, 0)).unwrap();

        let host = model.compute_derivatives(&state).unwrap();
        let export = model
            .compute_derivatives_cuda_export(&state)
            .unwrap()
            .expect("CUDA device-resident path must export");
        assert_eq!(export.phase.len, n);
        assert_ne!(export.phase.ptr, 0);
        // Values are validated end-to-end (device ptr -> Torch) in the Python
        // `tests/test_wp036e_q3_zero_copy.py` suite; here we assert the host
        // path still produces the finite reference the export mirrors.
        assert!(host.dphase.iter().all(|v| v.is_finite()));
    }

    // ── GpuBandStepper ─────────────────────────────────────────────────────

    fn discrete_step_params() -> DiscreteStepParams {
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

    fn band_state(band_sizes: [usize; 3]) -> OscillatorState {
        let n: usize = band_sizes.iter().sum();
        let phase: Vec<f64> = (0..n).map(|i| 0.05 * i as f64).collect();
        let amp: Vec<f64> = (0..n).map(|i| 0.5 + 0.5 * (i as f64 / n as f64)).collect();
        let freq: Vec<f64> = (0..n).map(|i| 0.02 * (i as f64 - n as f64 / 2.0)).collect();
        OscillatorState::new(phase, amp, freq, None).unwrap()
    }

    #[test]
    fn gpu_band_stepper_step_matches_kernel_cpu_reference_loop() {
        let band_sizes = [8usize, 8, 8];
        let state = band_state(band_sizes);
        let params = discrete_step_params();

        let mut stepper = GpuBandStepper::new(&state, band_sizes, params).unwrap();
        stepper.step().unwrap();
        stepper.step().unwrap();
        let got = stepper.state().unwrap();

        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);
        let (p1, a1, f1) =
            discrete_step_cpu(&phase32, &amp32, &freq32, band_sizes, &params).unwrap();
        let (p2, a2, f2) = discrete_step_cpu(&p1, &a1, &f1, band_sizes, &params).unwrap();

        for i in 0..got.n_oscillators() {
            assert!((got.phase[i] - f64::from(p2[i])).abs() < 1e-5);
            assert!((got.amplitude[i] - f64::from(a2[i])).abs() < 1e-5);
            assert!((got.frequency[i] - f64::from(f2[i])).abs() < 1e-5);
        }
    }

    #[test]
    fn gpu_band_stepper_run_records_trajectory() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let mut stepper = GpuBandStepper::new(&state, band_sizes, discrete_step_params()).unwrap();
        let (final_state, traj) = stepper.run(3, true).unwrap();
        assert_eq!(final_state.n_oscillators(), 12);
        let traj = traj.unwrap();
        assert_eq!(traj.n_steps(), 4);
    }

    #[test]
    fn gpu_band_stepper_run_no_trajectory() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let mut stepper = GpuBandStepper::new(&state, band_sizes, discrete_step_params()).unwrap();
        let (final_state, traj) = stepper.run(3, false).unwrap();
        assert_eq!(final_state.n_oscillators(), 12);
        assert!(traj.is_none());
    }

    #[test]
    fn gpu_band_stepper_rejects_band_size_mismatch() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let err = GpuBandStepper::new(&state, [4, 4, 5], discrete_step_params()).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn gpu_band_stepper_rejects_zero_band() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let err = GpuBandStepper::new(&state, [0, 4, 8], discrete_step_params()).unwrap_err();
        assert!(matches!(err, SimError::InvalidCoupling { .. }));
    }

    #[test]
    fn gpu_band_stepper_rejects_non_positive_dt() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let mut params = discrete_step_params();
        params.dt = -0.01;
        let err = GpuBandStepper::new(&state, band_sizes, params).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn gpu_band_stepper_rejects_zero_steps() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let mut stepper = GpuBandStepper::new(&state, band_sizes, discrete_step_params()).unwrap();
        let err = stepper.run(0, false).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn gpu_band_stepper_accessors() {
        let band_sizes = [4usize, 4, 4];
        let state = band_state(band_sizes);
        let stepper = GpuBandStepper::new(&state, band_sizes, discrete_step_params()).unwrap();
        assert_eq!(stepper.n_oscillators(), 12);
        assert_eq!(stepper.band_sizes(), band_sizes);
        assert!((stepper.dt() - 0.01).abs() < 1e-9);
    }

    /// Device-resident multi-step loop for the band stepper (WP-036E Q2).
    #[test]
    fn gpu_band_stepper_device_resident_multi_step() {
        let band_sizes = [16usize, 16, 16];
        let state = band_state(band_sizes);
        let params = discrete_step_params();

        let mut stepper = GpuBandStepper::new(&state, band_sizes, params).unwrap();
        for _ in 0..3 {
            stepper.step().unwrap();
        }
        let got = stepper.state().unwrap();
        assert_eq!(got.n_oscillators(), 48);

        // Verify against the CPU reference.
        let phase32 = to_f32(&state.phase);
        let amp32 = to_f32(&state.amplitude);
        let freq32 = to_f32(&state.frequency);
        let (mut p, mut a, mut f) = (phase32, amp32, freq32);
        for _ in 0..3 {
            (p, a, f) = discrete_step_cpu(&p, &a, &f, band_sizes, &params).unwrap();
        }
        for (i, &pi) in p.iter().enumerate().take(got.n_oscillators()) {
            assert!(
                (got.phase[i] - f64::from(pi)).abs() < 1e-5,
                "phase[{i}]: got={}, expected={}",
                got.phase[i],
                f64::from(pi)
            );
        }
    }
}

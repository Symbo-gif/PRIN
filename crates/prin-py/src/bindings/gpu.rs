//! PyO3 bindings for `prin-sim`'s GPU engine types (WP-036D / `0144I1`).
//!
//! Exposes [`GpuSparseKuramoto`], [`GpuMeanFieldEngine`], and
//! [`GpuBandStepper`] behind `#[cfg(any(feature = "cuda", feature = "wgpu"))]`.
//! The binding is marshalling and dispatch only — numerical authority stays
//! in the existing CubeCL kernels via `prin-sim`. Inputs cross the PyO3
//! boundary as CPU `float32` DLPack capsules (the GPU-engine dtype); results
//! cross as CPU `float32` capsules, or — on the CUDA device-resident path
//! (WP-036E Q3) — as zero-copy `kDLCUDA` capsules over the engine's live
//! device buffers (`export_dlpack_f32_cuda`). `GpuBandStepper` keeps the CPU
//! `float32` result path: its device state is three per-band `[Handle; 3]`
//! triples (a cubecl-0.10 buffer-offset-alignment constraint, WP-036E Q1),
//! not one contiguous `N`-length buffer.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::models::Dynamics;
use prin_dynamics::state::OscillatorState;
use prin_kernels::discrete_step::DiscreteStepParams;
use prin_kernels::mean_field_rk4::MeanFieldRk4Params;
use prin_sim::gpu::{GpuBandStepper, GpuMeanFieldEngine, GpuSparseKuramoto};
use prin_sim::SparseCoupling;

#[cfg(feature = "cuda")]
use crate::dlpack::export_dlpack_f32_cuda;
use crate::dlpack::{export_dlpack_f32, read_dlpack_f32};
#[cfg(feature = "cuda")]
use prin_sim::gpu::CudaStateExport;

fn sim_err(err: impl core::fmt::Display) -> PyErr {
    PyValueError::new_err(err.to_string())
}

fn to_f32(v: &[f64]) -> Vec<f32> {
    v.iter().map(|&x| x as f32).collect()
}

fn to_f64(v: &[f32]) -> Vec<f64> {
    v.iter().map(|&x| f64::from(x)).collect()
}

/// Build a [`GpuSparseKuramoto`] whose k-NN coupling topology is derived from a
/// phase vector entirely in Rust (via [`SparseCoupling::from_knn`]), so the
/// Python caller never constructs coupling indices or weights.
///
/// This is the topology-construction counterpart the WP-036D `0144I2` device
/// dispatch needs: `python/prin/_torch_compat.py`'s sparse k-NN
/// `compute_derivatives` path only has the current phase, `n`, `k`, and the
/// scalar model parameters — not a CSR triple — and computing the k-NN graph
/// with `K / degree` weights on the Python side would be Python numerics
/// (Coding Standards §1.2). Factored out of [`PyGpuSparseKuramoto::from_knn_phase`]
/// so the feature-gated Rust test can exercise it without a DLPack capsule.
fn build_gpu_sparse_from_knn_phase(
    n: usize,
    k_neighbors: usize,
    coupling_strength: f64,
    decay_rate: f64,
    freq_adaptation_rate: f64,
    phase: &[f64],
) -> PyResult<GpuSparseKuramoto> {
    let coupling =
        SparseCoupling::from_knn(phase, k_neighbors, coupling_strength).map_err(sim_err)?;
    GpuSparseKuramoto::new(
        n,
        decay_rate,
        freq_adaptation_rate,
        coupling_strength,
        coupling,
    )
    .map_err(sim_err)
}

fn build_oscillator_state(
    phase_data: &[f32],
    amp_data: &[f32],
    freq_data: &[f32],
) -> PyResult<OscillatorState> {
    OscillatorState::new(
        to_f64(phase_data),
        to_f64(amp_data),
        to_f64(freq_data),
        None,
    )
    .map_err(sim_err)
}

/// Wrap a [`CudaStateExport`]'s three device buffers as zero-copy `kDLCUDA`
/// DLPack capsules (WP-036E Q3). Each capsule owns the `Handle` pin that keeps
/// the CUDA allocation alive; Torch's `from_dlpack` adopts the pointer with no
/// copy.
#[cfg(feature = "cuda")]
fn export_cuda_state(
    py: Python<'_>,
    export: CudaStateExport,
) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
    let mk = |buf: prin_sim::gpu::CudaBufferExport| -> PyResult<Py<PyAny>> {
        let (ptr, device_id, len, pin) = buf.into_raw_parts();
        export_dlpack_f32_cuda(py, ptr, device_id, vec![len as i64], pin)
    };
    Ok((
        mk(export.phase)?,
        mk(export.amplitude)?,
        mk(export.frequency)?,
    ))
}

fn export_state_as_f32(
    py: Python<'_>,
    state: &OscillatorState,
) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
    let n = state.n_oscillators();
    let shape = vec![n as i64];
    let phase = export_dlpack_f32(py, shape.clone(), to_f32(&state.phase))?;
    let amp = export_dlpack_f32(py, shape.clone(), to_f32(&state.amplitude))?;
    let freq = export_dlpack_f32(py, shape, to_f32(&state.frequency))?;
    Ok((phase, amp, freq))
}

// ────────────────────────────────────────────────────────────────────────────
// PyGpuSparseKuramoto
// ────────────────────────────────────────────────────────────────────────────

/// PyO3 wrapper around [`GpuSparseKuramoto`] — sparse Kuramoto coupling
/// dispatched through `prin-kernels`' GPU/CPU-SIMD backends.
///
/// The constructor takes the CSR coupling topology as flat index/data lists
/// (matching `SparseCoupling::from_csr` convention) plus the scalar model
/// parameters. `compute_derivatives` accepts three `float32` DLPack tensors
/// (phase, amplitude, frequency) and returns three `float32` DLPack capsules
/// (d_phase, d_amplitude, d_frequency).
#[pyclass(name = "GpuSparseKuramoto")]
pub struct PyGpuSparseKuramoto {
    inner: GpuSparseKuramoto,
}

#[pymethods]
impl PyGpuSparseKuramoto {
    /// Create a GPU-dispatched sparse Kuramoto model.
    ///
    /// `crow_indices` / `col_indices` / `values` define the CSR coupling
    /// topology (matching `SparseCoupling::from_csr` convention). `k` is the
    /// uniform coupling strength — edge weights must match `K / degree(i)`.
    #[new]
    #[pyo3(signature = (n, decay_rate, freq_adaptation_rate, k, crow_indices, col_indices, values))]
    fn new(
        n: usize,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        k: f64,
        crow_indices: Vec<usize>,
        col_indices: Vec<usize>,
        values: Vec<f64>,
    ) -> PyResult<Self> {
        let coupling =
            SparseCoupling::from_csr(&crow_indices, &col_indices, &values, n).map_err(sim_err)?;
        let inner = GpuSparseKuramoto::new(n, decay_rate, freq_adaptation_rate, k, coupling)
            .map_err(sim_err)?;
        Ok(Self { inner })
    }

    /// Build a GPU-dispatched sparse Kuramoto model from a phase vector.
    ///
    /// The k-NN coupling topology (`k_neighbors` nearest phase neighbours per
    /// oscillator, uniform `coupling_strength / k_neighbors` edge weight) is
    /// built in Rust via `SparseCoupling::from_knn` — the Python caller supplies
    /// only the current phase (as a `float32` DLPack tensor) and the scalar
    /// model parameters, never coupling indices or weights.
    #[staticmethod]
    #[pyo3(signature = (
        n, k_neighbors, coupling_strength, decay_rate, freq_adaptation_rate, phase,
    ))]
    fn from_knn_phase(
        n: usize,
        k_neighbors: usize,
        coupling_strength: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        phase: &Bound<'_, PyAny>,
    ) -> PyResult<Self> {
        let (_, p_data) = read_dlpack_f32(phase)?;
        let inner = build_gpu_sparse_from_knn_phase(
            n,
            k_neighbors,
            coupling_strength,
            decay_rate,
            freq_adaptation_rate,
            &to_f64(&p_data),
        )?;
        Ok(Self { inner })
    }

    /// Compute derivatives via the GPU sparse k-NN kernel.
    ///
    /// Accepts three `float32` DLPack tensors (phase, amplitude, frequency).
    /// On the CUDA device-resident path (WP-036E Q3) the three derivative
    /// buffers are returned as zero-copy `kDLCUDA` capsules — the CSR topology
    /// stays device-resident and the output never round-trips through host
    /// memory. Otherwise (wgpu / CPU-SIMD / no GPU) three CPU `float32` DLPack
    /// capsules are returned, as before.
    fn compute_derivatives(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        frequency: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
        let (p_shape, p_data) = read_dlpack_f32(phase)?;
        let (a_shape, a_data) = read_dlpack_f32(amplitude)?;
        let (f_shape, f_data) = read_dlpack_f32(frequency)?;

        if p_shape != a_shape || p_shape != f_shape {
            return Err(PyValueError::new_err(format!(
                "shape mismatch: phase={p_shape:?}, amplitude={a_shape:?}, frequency={f_shape:?}"
            )));
        }

        let state = build_oscillator_state(&p_data, &a_data, &f_data)?;

        #[cfg(feature = "cuda")]
        if let Some(export) = self
            .inner
            .compute_derivatives_cuda_export(&state)
            .map_err(sim_err)?
        {
            return export_cuda_state(py, export);
        }

        let deriv = self.inner.compute_derivatives(&state).map_err(sim_err)?;

        let n = deriv.dphase.len();
        let shape = vec![n as i64];
        let out_p = export_dlpack_f32(py, shape.clone(), to_f32(&deriv.dphase))?;
        let out_a = export_dlpack_f32(py, shape.clone(), to_f32(&deriv.damplitude))?;
        let out_f = export_dlpack_f32(py, shape, to_f32(&deriv.dfrequency))?;
        Ok((out_p, out_a, out_f))
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }

    #[getter]
    fn decay_rate(&self) -> f64 {
        self.inner.decay_rate()
    }

    #[getter]
    fn freq_adaptation_rate(&self) -> f64 {
        self.inner.freq_adaptation_rate()
    }

    #[getter]
    fn k(&self) -> f64 {
        self.inner.k()
    }
}

// ────────────────────────────────────────────────────────────────────────────
// PyGpuMeanFieldEngine
// ────────────────────────────────────────────────────────────────────────────

/// PyO3 wrapper around [`GpuMeanFieldEngine`] — dense, all-to-all mean-field
/// RK4 engine stepped via the fully fused `prin-kernels` kernel.
///
/// The constructor takes the initial state as three `float32` DLPack tensors
/// plus scalar RK4 parameters. `step()` advances one fused RK4 step; `state()`
/// returns the current state as three `float32` DLPack capsules.
#[pyclass(name = "GpuMeanFieldEngine")]
pub struct PyGpuMeanFieldEngine {
    inner: GpuMeanFieldEngine,
}

#[pymethods]
impl PyGpuMeanFieldEngine {
    /// Create a new dense mean-field GPU engine from initial state tensors.
    #[new]
    #[pyo3(signature = (phase, amplitude, frequency, k, decay, gamma, dt))]
    fn new(
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        frequency: &Bound<'_, PyAny>,
        k: f32,
        decay: f32,
        gamma: f32,
        dt: f32,
    ) -> PyResult<Self> {
        let (_, p_data) = read_dlpack_f32(phase)?;
        let (_, a_data) = read_dlpack_f32(amplitude)?;
        let (_, f_data) = read_dlpack_f32(frequency)?;

        let state = build_oscillator_state(&p_data, &a_data, &f_data)?;
        let params = MeanFieldRk4Params {
            k,
            decay,
            gamma,
            dt,
        };
        let inner = GpuMeanFieldEngine::new(&state, params).map_err(sim_err)?;
        Ok(Self { inner })
    }

    /// Advance by one fused RK4 step.
    ///
    /// Returns a dict with `backend_name`, `wall_time_seconds`,
    /// `timing_method`, and `launch_count`.
    fn step(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let report = self.inner.step().map_err(sim_err)?;
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("backend_name", report.backend_name)?;
        dict.set_item("wall_time_seconds", report.wall_time_seconds)?;
        dict.set_item("timing_method", format!("{}", report.timing_method))?;
        dict.set_item("launch_count", report.launch_count)?;
        Ok(dict.into_any().unbind())
    }

    /// Current state as three DLPack capsules `(phase, amplitude, frequency)`.
    ///
    /// On the CUDA device-resident path (WP-036E Q3) these are zero-copy
    /// `kDLCUDA` capsules over the engine's live device buffers (a stable
    /// snapshot — the next `step()` allocates fresh handles). Otherwise they
    /// are CPU `float32` capsules downloaded from the device.
    fn state(&self, py: Python<'_>) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
        #[cfg(feature = "cuda")]
        if let Some(export) = self.inner.state_cuda_export() {
            return export_cuda_state(py, export);
        }
        let state = self.inner.state().map_err(sim_err)?;
        export_state_as_f32(py, &state)
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }

    #[getter]
    fn dt(&self) -> f64 {
        self.inner.dt()
    }
}

// ────────────────────────────────────────────────────────────────────────────
// PyGpuBandStepper
// ────────────────────────────────────────────────────────────────────────────

/// PyO3 wrapper around [`GpuBandStepper`] — fused three-band (delta/theta/
/// gamma) discrete-time stepper dispatched via `prin-kernels`.
///
/// The constructor takes the initial state as three `float32` DLPack tensors,
/// the per-band oscillator counts, and the per-band / PAC parameters.
/// `step()` advances one fused discrete step; `state()` returns the current
/// state as three `float32` DLPack capsules.
#[pyclass(name = "GpuBandStepper")]
pub struct PyGpuBandStepper {
    inner: GpuBandStepper,
}

#[pymethods]
impl PyGpuBandStepper {
    /// Create a new fused three-band GPU stepper.
    ///
    /// `band_sizes` is a 3-element list `[delta, theta, gamma]`. Per-band
    /// parameters are passed as flat lists of 3 floats each (one per band,
    /// in delta/theta/gamma order): `ks`, `decays`, `gammas`. PAC parameters
    /// are two flat lists of 2 floats each: `pac_modulation_depths` and
    /// `pac_phase_offsets` (index 0 = delta→theta, 1 = theta→gamma).
    #[new]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        phase, amplitude, frequency, band_sizes,
        ks, decays, gammas,
        pac_modulation_depths, pac_phase_offsets,
        amp_min, amp_max, dt,
    ))]
    fn new(
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
        frequency: &Bound<'_, PyAny>,
        band_sizes: [usize; 3],
        ks: [f32; 3],
        decays: [f32; 3],
        gammas: [f32; 3],
        pac_modulation_depths: [f32; 2],
        pac_phase_offsets: [f32; 2],
        amp_min: f32,
        amp_max: f32,
        dt: f32,
    ) -> PyResult<Self> {
        let (_, p_data) = read_dlpack_f32(phase)?;
        let (_, a_data) = read_dlpack_f32(amplitude)?;
        let (_, f_data) = read_dlpack_f32(frequency)?;

        let state = build_oscillator_state(&p_data, &a_data, &f_data)?;
        let params = DiscreteStepParams {
            bands: [
                prin_kernels::discrete_step::BandStepParams {
                    k: ks[0],
                    decay: decays[0],
                    gamma: gammas[0],
                },
                prin_kernels::discrete_step::BandStepParams {
                    k: ks[1],
                    decay: decays[1],
                    gamma: gammas[1],
                },
                prin_kernels::discrete_step::BandStepParams {
                    k: ks[2],
                    decay: decays[2],
                    gamma: gammas[2],
                },
            ],
            pac: [
                prin_kernels::discrete_step::PacGateParams {
                    modulation_depth: pac_modulation_depths[0],
                    phase_offset: pac_phase_offsets[0],
                },
                prin_kernels::discrete_step::PacGateParams {
                    modulation_depth: pac_modulation_depths[1],
                    phase_offset: pac_phase_offsets[1],
                },
            ],
            amp_min,
            amp_max,
            dt,
        };
        let inner = GpuBandStepper::new(&state, band_sizes, params).map_err(sim_err)?;
        Ok(Self { inner })
    }

    /// Advance by one fused discrete step.
    ///
    /// Returns a dict with `backend_name`, `wall_time_seconds`,
    /// `timing_method`, and `launch_count`.
    fn step(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let report = self.inner.step().map_err(sim_err)?;
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("backend_name", report.backend_name)?;
        dict.set_item("wall_time_seconds", report.wall_time_seconds)?;
        dict.set_item("timing_method", format!("{}", report.timing_method))?;
        dict.set_item("launch_count", report.launch_count)?;
        Ok(dict.into_any().unbind())
    }

    /// Current state as three `float32` DLPack capsules
    /// `(phase, amplitude, frequency)`.
    fn state(&self, py: Python<'_>) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
        let state = self.inner.state().map_err(sim_err)?;
        export_state_as_f32(py, &state)
    }

    #[getter]
    fn n_oscillators(&self) -> usize {
        self.inner.n_oscillators()
    }

    #[getter]
    fn band_sizes(&self) -> [usize; 3] {
        self.inner.band_sizes()
    }

    #[getter]
    fn dt(&self) -> f64 {
        self.inner.dt()
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Registration
// ────────────────────────────────────────────────────────────────────────────

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGpuSparseKuramoto>()?;
    m.add_class::<PyGpuMeanFieldEngine>()?;
    m.add_class::<PyGpuBandStepper>()?;
    Ok(())
}

// ────────────────────────────────────────────────────────────────────────────
// Tests (Rust-level, feature-gated)
// ────────────────────────────────────────────────────────────────────────────

#[cfg(all(test, any(feature = "cuda", feature = "wgpu")))]
mod tests {
    use super::*;
    use prin_dynamics::coupling::CouplingMode;
    use prin_dynamics::models::KuramotoOscillator;
    use prin_kernels::discrete_step::{BandStepParams, PacGateParams};
    use prin_kernels::mean_field_rk4::MeanFieldRk4Params;
    use prin_sim::csr_coupling::SparseCoupling;

    const GPU_RTOL: f32 = 1e-5;
    const GPU_ATOL: f32 = 1e-6;

    fn approx_eq_f32(a: &[f32], b: &[f32], label: &str) {
        assert_eq!(a.len(), b.len(), "{label}: length mismatch");
        for (i, (&va, &vb)) in a.iter().zip(b).enumerate() {
            let diff = (va - vb).abs();
            let tol = GPU_ATOL + GPU_RTOL * vb.abs();
            assert!(
                diff <= tol,
                "{label}[{i}]: |{va} - {vb}| = {diff} > tol {tol}",
            );
        }
    }

    // ── GpuSparseKuramoto ──────────────────────────────────────────────

    #[test]
    fn gpu_sparse_kuramoto_binding_compute_derivatives_f32_round_trip() {
        let n = 8;
        let k_neighbors = 2;
        let phase: Vec<f64> = (0..n).map(|i| 0.3 * i as f64).collect();
        let amp = vec![1.0_f64; n];
        let freq: Vec<f64> = (0..n).map(|i| 0.1 * (i as f64 - 2.5)).collect();

        let coupling = SparseCoupling::from_knn(&phase, k_neighbors, 2.0).unwrap();
        let csr = coupling.as_csr();
        let crow_indices: Vec<usize> = csr.indptr().raw_storage().to_vec();
        let col_indices: Vec<usize> = csr.indices().to_vec();
        let values: Vec<f64> = csr.data().to_vec();

        let model =
            PyGpuSparseKuramoto::new(n, 0.1, 0.01, 2.0, crow_indices, col_indices, values).unwrap();

        assert_eq!(model.n_oscillators(), n);
        assert_eq!(model.k(), 2.0);

        let state = OscillatorState::new(phase.clone(), amp.clone(), freq.clone(), None).unwrap();
        let deriv = model.inner.compute_derivatives(&state).unwrap();

        let f32_phase: Vec<f32> = to_f32(&phase);
        let f32_amp: Vec<f32> = to_f32(&amp);
        let f32_freq: Vec<f32> = to_f32(&freq);
        let expected_dphase = to_f32(&deriv.dphase);
        let expected_damp = to_f32(&deriv.damplitude);
        let expected_dfreq = to_f32(&deriv.dfrequency);

        let result_dphase = to_f32(&deriv.dphase);
        let result_damp = to_f32(&deriv.damplitude);
        let result_dfreq = to_f32(&deriv.dfrequency);

        approx_eq_f32(&result_dphase, &expected_dphase, "dphase");
        approx_eq_f32(&result_damp, &expected_damp, "damplitude");
        approx_eq_f32(&result_dfreq, &expected_dfreq, "dfrequency");

        let _ = (f32_phase, f32_amp, f32_freq);
    }

    #[test]
    fn gpu_sparse_kuramoto_binding_agrees_with_cpu_reference() {
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
        let csr = coupling.as_csr();
        let crow_indices: Vec<usize> = csr.indptr().raw_storage().to_vec();
        let col_indices: Vec<usize> = csr.indices().to_vec();
        let values: Vec<f64> = csr.data().to_vec();

        let gpu_model =
            PyGpuSparseKuramoto::new(n, 0.1, 0.01, 2.0, crow_indices, col_indices, values).unwrap();
        let gpu_deriv = gpu_model.inner.compute_derivatives(&state).unwrap();

        let ref_dphase_f32 = to_f32(&reference.dphase);
        let gpu_dphase_f32 = to_f32(&gpu_deriv.dphase);
        approx_eq_f32(&gpu_dphase_f32, &ref_dphase_f32, "gpu vs cpu dphase");
    }

    #[test]
    fn gpu_sparse_kuramoto_from_knn_phase_matches_cpu_reference() {
        let n = 8;
        let k_neighbors = 3;
        let phase: Vec<f64> = (0..n).map(|i| 0.3 * i as f64).collect();
        let amp = vec![1.0_f64; n];
        let freq: Vec<f64> = (0..n).map(|i| 0.1 * (i as f64 - 2.5)).collect();
        let state = OscillatorState::new(phase.clone(), amp, freq, None).unwrap();

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
        let reference = reference_model.compute_derivatives(&state).unwrap();

        let phase_derived =
            build_gpu_sparse_from_knn_phase(n, k_neighbors, 2.0, 0.1, 0.01, &phase).unwrap();
        assert_eq!(phase_derived.n_oscillators(), n);
        assert_eq!(phase_derived.k(), 2.0);
        let gpu = phase_derived.compute_derivatives(&state).unwrap();

        // f32 GPU kernel vs f64 prin-dynamics reference: the wider `1e-4`
        // absolute tolerance the `prin-sim` gpu module documents for exactly
        // this comparison (`gpu_sparse_kuramoto_matches_cpu_dynamics_reference`).
        for i in 0..n {
            assert!(
                (gpu.dphase[i] - reference.dphase[i]).abs() < 1e-4,
                "dphase[{i}]: {} vs {}",
                gpu.dphase[i],
                reference.dphase[i],
            );
            assert!((gpu.damplitude[i] - reference.damplitude[i]).abs() < 1e-4);
            assert!((gpu.dfrequency[i] - reference.dfrequency[i]).abs() < 1e-4);
        }
    }

    // ── GpuMeanFieldEngine ─────────────────────────────────────────────

    #[test]
    fn gpu_mean_field_engine_binding_step_and_state_f32() {
        let n = 16;
        let phase: Vec<f32> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amp = vec![1.0_f32; n];
        let freq: Vec<f32> = (0..n).map(|i| 0.05 * (i as f32 - 4.0)).collect();

        let state =
            OscillatorState::new(to_f64(&phase), to_f64(&amp), to_f64(&freq), None).unwrap();
        let params = MeanFieldRk4Params {
            k: 1.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };
        let mut engine = GpuMeanFieldEngine::new(&state, params).unwrap();

        assert_eq!(engine.n_oscillators(), n);

        let report = engine.step().unwrap();
        assert!(report.launch_count > 0);

        let new_state = engine.state().unwrap();
        let new_phase_f32 = to_f32(&new_state.phase);
        let new_amp_f32 = to_f32(&new_state.amplitude);

        assert_eq!(new_phase_f32.len(), n);
        assert_eq!(new_amp_f32.len(), n);

        for i in 0..n {
            assert!(
                (new_phase_f32[i] - phase[i]).abs() > 0.0 || (new_amp_f32[i] - amp[i]).abs() > 0.0,
                "step should modify state (at least some elements)"
            );
        }
    }

    // ── GpuBandStepper ─────────────────────────────────────────────────

    #[test]
    fn gpu_band_stepper_binding_step_and_state_f32() {
        let band_sizes = [4usize, 4, 4];
        let n: usize = band_sizes.iter().sum();
        let phase: Vec<f32> = (0..n).map(|i| 0.2 * i as f32).collect();
        let amp = vec![0.8_f32; n];
        let freq: Vec<f32> = (0..n).map(|i| 0.01 * i as f32).collect();

        let state =
            OscillatorState::new(to_f64(&phase), to_f64(&amp), to_f64(&freq), None).unwrap();
        let params = DiscreteStepParams {
            bands: [
                BandStepParams {
                    k: 1.0,
                    decay: 0.1,
                    gamma: 0.01,
                },
                BandStepParams {
                    k: 0.5,
                    decay: 0.05,
                    gamma: 0.005,
                },
                BandStepParams {
                    k: 0.2,
                    decay: 0.02,
                    gamma: 0.002,
                },
            ],
            pac: [
                PacGateParams {
                    modulation_depth: 0.3,
                    phase_offset: 0.0,
                },
                PacGateParams {
                    modulation_depth: 0.2,
                    phase_offset: 0.1,
                },
            ],
            amp_min: 0.0,
            amp_max: 2.0,
            dt: 0.01,
        };
        let mut stepper = GpuBandStepper::new(&state, band_sizes, params).unwrap();

        assert_eq!(stepper.n_oscillators(), n);
        assert_eq!(stepper.band_sizes(), band_sizes);

        let report = stepper.step().unwrap();
        assert!(report.launch_count > 0);

        let new_state = stepper.state().unwrap();
        assert_eq!(new_state.n_oscillators(), n);
    }
}

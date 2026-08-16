//! GPU-dispatched simulation components (WP-021).
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
//! - [`GpuMeanFieldEngine`] — a small stepper around the *fused* dense
//!   all-to-all RK4 kernel ([`prin_kernels::mean_field_rk4::cubecl::step_auto`]),
//!   for the dense mean-field regime the §N1 `N = 1M` GPU throughput target
//!   names. The kernel fuses the entire RK4 sub-step sequence in one launch
//!   set, so it cannot be expressed as a [`prin_dynamics::models::Dynamics`]
//!   (which evaluates one derivative at a time) — this type is the fused
//!   analogue of [`crate::engine::OscilloSim`] for that regime.
//! - [`GpuBandStepper`] — the analogous fused stepper for the three-band
//!   discrete-time step
//!   ([`prin_kernels::discrete_step::cubecl::discrete_step_auto`]).
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

fn to_f32(v: &[f64]) -> Vec<f32> {
    v.iter().map(|&x| x as f32).collect()
}

fn to_f64(v: &[f32]) -> Vec<f64> {
    v.iter().map(|&x| f64::from(x)).collect()
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
#[derive(Clone, Debug)]
pub struct GpuSparseKuramoto {
    n: usize,
    decay_rate: f64,
    freq_adaptation_rate: f64,
    k: f64,
    graph: SparseKnnGraph,
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

        Ok(Self {
            n,
            decay_rate,
            freq_adaptation_rate,
            k,
            graph,
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

        // Length/graph-size preconditions are validated by `new` and the
        // early `n != self.n` check above; `sparse_knn_coupling_auto` always
        // falls back to the native CPU reference (which cannot fail on
        // already-valid input), so a kernel-layer error here would indicate
        // a logic bug in this wrapper, not a runtime condition callers can
        // recover from.
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
#[derive(Clone, Debug)]
pub struct GpuMeanFieldEngine {
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    params: MeanFieldRk4Params,
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

        Ok(Self {
            phase: to_f32(&state.phase),
            amplitude: to_f32(&state.amplitude),
            frequency: to_f32(&state.frequency),
            params,
        })
    }

    /// Number of oscillators.
    pub fn n_oscillators(&self) -> usize {
        self.phase.len()
    }

    /// Timestep `dt`.
    pub fn dt(&self) -> f64 {
        f64::from(self.params.dt)
    }

    /// Current state, converted back to `f64`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the internal `f32` state somehow fails
    /// [`OscillatorState`]'s length invariants (unreachable in practice: the
    /// three buffers are always resized together).
    pub fn state(&self) -> Result<OscillatorState, SimError> {
        OscillatorState::new(
            to_f64(&self.phase),
            to_f64(&self.amplitude),
            to_f64(&self.frequency),
            None,
        )
        .map_err(SimError::from)
    }

    /// Advance by one fused RK4 step.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the kernel dispatch fails (see
    /// [`step_auto`]).
    pub fn step(&mut self) -> Result<MeanFieldStepReport, SimError> {
        let (out, report) = step_auto(&self.phase, &self.amplitude, &self.frequency, &self.params)?;
        (self.phase, self.amplitude, self.frequency) = out;
        Ok(report)
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
            t.phases.push(to_f64(&self.phase));
            t.amplitudes.push(to_f64(&self.amplitude));
            t.frequencies.push(to_f64(&self.frequency));
            t.times.push(0.0);
            Some(t)
        } else {
            None
        };

        for step in 0..n_steps {
            self.step()?;
            if let Some(ref mut traj) = trajectory {
                traj.phases.push(to_f64(&self.phase));
                traj.amplitudes.push(to_f64(&self.amplitude));
                traj.frequencies.push(to_f64(&self.frequency));
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
#[derive(Clone, Debug)]
pub struct GpuBandStepper {
    phase: Vec<f32>,
    amplitude: Vec<f32>,
    frequency: Vec<f32>,
    band_sizes: [usize; 3],
    params: DiscreteStepParams,
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

        Ok(Self {
            phase: to_f32(&state.phase),
            amplitude: to_f32(&state.amplitude),
            frequency: to_f32(&state.frequency),
            band_sizes,
            params,
        })
    }

    /// Number of oscillators across all three bands.
    pub fn n_oscillators(&self) -> usize {
        self.phase.len()
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
    /// Returns [`SimError`] if the internal `f32` state somehow fails
    /// [`OscillatorState`]'s length invariants (unreachable in practice).
    pub fn state(&self) -> Result<OscillatorState, SimError> {
        OscillatorState::new(
            to_f64(&self.phase),
            to_f64(&self.amplitude),
            to_f64(&self.frequency),
            None,
        )
        .map_err(SimError::from)
    }

    /// Advance by one fused discrete step.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the kernel dispatch fails (see
    /// [`discrete_step_auto`]).
    pub fn step(&mut self) -> Result<DiscreteStepReport, SimError> {
        let (out, report) = discrete_step_auto(
            &self.phase,
            &self.amplitude,
            &self.frequency,
            self.band_sizes,
            &self.params,
        )?;
        (self.phase, self.amplitude, self.frequency) = out;
        Ok(report)
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
            t.phases.push(to_f64(&self.phase));
            t.amplitudes.push(to_f64(&self.amplitude));
            t.frequencies.push(to_f64(&self.frequency));
            t.times.push(0.0);
            Some(t)
        } else {
            None
        };

        for step in 0..n_steps {
            self.step()?;
            if let Some(ref mut traj) = trajectory {
                traj.phases.push(to_f64(&self.phase));
                traj.amplitudes.push(to_f64(&self.amplitude));
                traj.frequencies.push(to_f64(&self.frequency));
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
        // `OscillatorState`'s own constructors reject n=0; its fields are
        // public, so an empty state is only reachable via direct struct
        // construction (mirroring how `OscilloSim::new` defensively checks
        // the same condition in `engine.rs`).
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
        // `dt` round-trips through `f32` (the kernel's native precision), so
        // the accumulated time carries f32 rounding error, not f64 precision.
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
}

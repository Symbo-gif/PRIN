//! OscilloSim simulation engine.
//!
//! [`OscilloSim`] orchestrates large-scale oscillator simulation by combining:
//!
//! - A [`SparseCoupling`] CSR matrix for O(nnz) coupling computations.
//! - A dynamics model ([`SparseKuramoto`] or [`SparseStuartLandau`]) that
//!   implements `prin_dynamics::Dynamics` using the sparse coupling.
//! - A `prin_dynamics::Integrator` for time-stepping (Euler, RK4, RK45).
//!
//! The engine reuses the state, integrator, and numerical guards from
//! `prin-dynamics` — it does not duplicate any dynamics logic.
//!
//! ## Usage
//!
//! ```rust,no_run
//! use prin_sim::{OscilloSim, SparseCoupling, SparseKuramoto};
//! use prin_dynamics::{OscillatorState, RK4Integrator, Integrator};
//!
//! # fn main() -> Result<(), prin_sim::SimError> {
//! let coupling = SparseCoupling::from_ring(100, 4, 1.0)?;
//! let model = SparseKuramoto::new(100, 0.1, 0.01, coupling.clone())?;
//! let state = OscillatorState::create_random(100, (0.5, 5.0), &mut prin_dynamics::Seed::new(0, 0))?;
//! let mut engine = OscilloSim::new(state, coupling, Box::new(RK4Integrator::new()), 0.01)?;
//! let (final_state, traj) = engine.run(&model, 1000, true)?;
//! # Ok(())
//! # }
//! ```

use std::sync::Arc;

use prin_dynamics::models::Dynamics;
use prin_dynamics::state::{
    clamp_amplitude, wrap_phase, OscillatorState, StateDerivatives, StateError,
};
use prin_dynamics::Integrator;
use serde::{Deserialize, Serialize};

use crate::csr_coupling::SparseCoupling;
use crate::dispatch::{map_dispatch, zip_map_dispatch};
use crate::error::SimError;

/// Validate that `dt` is finite and positive.
fn validate_dt(dt: f64) -> Result<(), SimError> {
    if !dt.is_finite() || dt <= 0.0 {
        return Err(SimError::NonFiniteValue {
            name: "dt",
            index: 0,
            value: dt,
        });
    }
    Ok(())
}

// ────────────────────────────────────────────────────────────────────────────
// Sparse dynamics models
// ────────────────────────────────────────────────────────────────────────────

/// Kuramoto oscillator model with CSR sparse coupling.
///
/// Implements the same extended Kuramoto equations as
/// [`prin_dynamics::KuramotoOscillator`] but uses a [`SparseCoupling`] matrix
/// for the inter-oscillator coupling term, giving O(nnz) per-step cost instead
/// of O(N²).
///
/// The coupling weights are encoded in the CSR matrix entries, so there is no
/// separate `coupling_strength` field. The matrix should be built with the
/// desired normalisation (e.g. `K / k` for k-NN, `K / N` for all-to-all).
#[derive(Clone, Debug)]
pub struct SparseKuramoto {
    n: usize,
    decay_rate: f64,
    freq_adaptation_rate: f64,
    coupling: Arc<SparseCoupling>,
}

impl SparseKuramoto {
    /// Create a sparse Kuramoto model.
    ///
    /// `coupling` accepts either an owned [`SparseCoupling`] or an
    /// `Arc<SparseCoupling>`; passing the same `Arc` used by an [`OscilloSim`]
    /// (e.g. via [`OscilloSim::coupling_arc`]) shares the CSR storage instead
    /// of deep-cloning it (WP016-F7).
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an empty population, non-finite parameters,
    /// or a coupling matrix with the wrong dimension.
    pub fn new(
        n: usize,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        coupling: impl Into<Arc<SparseCoupling>>,
    ) -> Result<Self, SimError> {
        let coupling = coupling.into();
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if !decay_rate.is_finite() {
            return Err(SimError::NonFiniteValue {
                name: "decay_rate",
                index: 0,
                value: decay_rate,
            });
        }
        if !freq_adaptation_rate.is_finite() {
            return Err(SimError::NonFiniteValue {
                name: "freq_adaptation_rate",
                index: 0,
                value: freq_adaptation_rate,
            });
        }
        if coupling.n_oscillators() != n {
            return Err(SimError::DimensionMismatch {
                name: "coupling",
                expected: n,
                got: coupling.n_oscillators(),
            });
        }
        Ok(Self {
            n,
            decay_rate,
            freq_adaptation_rate,
            coupling,
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

    /// Borrow the coupling matrix.
    pub fn coupling(&self) -> &SparseCoupling {
        &self.coupling
    }
}

impl Dynamics for SparseKuramoto {
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

        let (sin_sum, cos_sum) = self
            .coupling
            .kuramoto_coupling(&state.phase, &state.amplitude)
            .expect("state dimension already validated against coupling");

        let inv_n = 1.0 / (n as f64);
        let dphase: Vec<f64> = zip_map_dispatch(&state.frequency, &sin_sum, |&f, &s| f + s);
        let damplitude: Vec<f64> = zip_map_dispatch(&state.amplitude, &cos_sum, |&a, &c| {
            -self.decay_rate * a + c
        });
        let dfrequency: Vec<f64> =
            map_dispatch(&sin_sum, |&s| self.freq_adaptation_rate * s * inv_n);

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

/// Stuart–Landau oscillator model with CSR sparse coupling.
///
/// Implements the same complex-amplitude dynamics as
/// [`prin_dynamics::StuartLandauOscillator`] but uses a [`SparseCoupling`]
/// matrix for the diffusive coupling term `C_i = Σ_j K_ij (z_j − z_i)`.
#[derive(Clone, Debug)]
pub struct SparseStuartLandau {
    n: usize,
    bifurcation_param: f64,
    coupling: Arc<SparseCoupling>,
}

impl SparseStuartLandau {
    /// Create a sparse Stuart–Landau model.
    ///
    /// `coupling` accepts either an owned [`SparseCoupling`] or an
    /// `Arc<SparseCoupling>`; passing the same `Arc` used by an [`OscilloSim`]
    /// (e.g. via [`OscilloSim::coupling_arc`]) shares the CSR storage instead
    /// of deep-cloning it (WP016-F7).
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an empty population, non-finite parameters,
    /// or a coupling matrix with the wrong dimension.
    pub fn new(
        n: usize,
        bifurcation_param: f64,
        coupling: impl Into<Arc<SparseCoupling>>,
    ) -> Result<Self, SimError> {
        let coupling = coupling.into();
        if n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if !bifurcation_param.is_finite() {
            return Err(SimError::NonFiniteValue {
                name: "bifurcation_param",
                index: 0,
                value: bifurcation_param,
            });
        }
        if coupling.n_oscillators() != n {
            return Err(SimError::DimensionMismatch {
                name: "coupling",
                expected: n,
                got: coupling.n_oscillators(),
            });
        }
        Ok(Self {
            n,
            bifurcation_param,
            coupling,
        })
    }

    /// Number of oscillators.
    pub fn n_oscillators(&self) -> usize {
        self.n
    }

    /// Hopf bifurcation parameter μ.
    pub fn bifurcation_param(&self) -> f64 {
        self.bifurcation_param
    }

    /// Borrow the coupling matrix.
    pub fn coupling(&self) -> &SparseCoupling {
        &self.coupling
    }
}

impl Dynamics for SparseStuartLandau {
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
            let mu = self.bifurcation_param;
            let dphase = state.frequency.clone();
            let damplitude: Vec<f64> = state
                .amplitude
                .iter()
                .map(|&r| mu * r - r * r * r)
                .collect();
            let dfrequency = vec![0.0; n];
            return StateDerivatives::new(dphase, damplitude, dfrequency);
        }

        let (c_re, c_im) = self
            .coupling
            .stuart_landau_coupling(&state.phase, &state.amplitude)
            .expect("state dimension already validated against coupling");

        let mu = self.bifurcation_param;
        let dfrequency = vec![0.0; n];

        let inputs: Vec<(f64, f64, f64, f64, f64)> = state
            .amplitude
            .iter()
            .zip(state.phase.iter())
            .zip(state.frequency.iter())
            .zip(c_re.iter())
            .zip(c_im.iter())
            .map(|((((&r, &phi), &omega), &cr), &ci)| (r, phi, omega, cr, ci))
            .collect();

        let results: Vec<(f64, f64)> = map_dispatch(&inputs, |&(r_i, phi_i, omega_i, cr, ci)| {
            let z_re = r_i * phi_i.cos();
            let z_im = r_i * phi_i.sin();

            let dz_re = mu * z_re - omega_i * z_im - (r_i * r_i) * z_re + cr;
            let dz_im = mu * z_im + omega_i * z_re - (r_i * r_i) * z_im + ci;

            let rot_re = phi_i.cos();
            let rot_im = -phi_i.sin();
            let w_re = dz_re * rot_re - dz_im * rot_im;
            let w_im = dz_re * rot_im + dz_im * rot_re;

            let dr = w_re;
            let safe_r = r_i.max(1e-8);
            let dphi = w_im / safe_r;
            (dphi, dr)
        });

        let (dphase, damplitude): (Vec<f64>, Vec<f64>) = results.into_iter().unzip();

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Trajectory recording
// ────────────────────────────────────────────────────────────────────────────

/// Recorded simulation trajectory.
///
/// Stores the oscillator state at each recorded step. Memory usage is
/// `n_steps × n_oscillators × 3 × 8` bytes (phase, amplitude, frequency as
/// f64).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Trajectory {
    /// Phase at each recorded step: `phases[step][oscillator]`.
    pub phases: Vec<Vec<f64>>,

    /// Amplitude at each recorded step.
    pub amplitudes: Vec<Vec<f64>>,

    /// Frequency at each recorded step.
    pub frequencies: Vec<Vec<f64>>,

    /// Simulation time at each recorded step.
    pub times: Vec<f64>,
}

impl Trajectory {
    /// Number of recorded steps.
    pub fn n_steps(&self) -> usize {
        self.times.len()
    }

    /// Number of oscillators (from the first recorded step, or 0 if empty).
    pub fn n_oscillators(&self) -> usize {
        self.phases.first().map_or(0, |p| p.len())
    }

    /// Approximate memory footprint in bytes.
    pub fn memory_bytes(&self) -> usize {
        let n = self.n_steps();
        let m = self.n_oscillators();
        n * m * 3 * std::mem::size_of::<f64>() + n * std::mem::size_of::<f64>()
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Engine
// ────────────────────────────────────────────────────────────────────────────

/// The OscilloSim simulation engine.
///
/// Orchestrates large-scale oscillator simulation by combining sparse coupling,
/// dynamics, integration, and optional pruning. The engine is the single entry
/// point for running simulations — it manages state transitions, applies
/// numerical guards, and records trajectories.
///
/// ## State flow
///
/// 1. **Pruning** (if enabled): reduce the system to active oscillators.
/// 2. **Integration step**: advance the (possibly reduced) state by `dt`.
/// 3. **Restore** (if pruned): expand back to the full system.
/// 4. **Record**: optionally append the state to the trajectory.
///
/// All RNG flows through the deterministic [`prin_dynamics::Seed`] — there is
/// no hidden randomness.
pub struct OscilloSim {
    state: OscillatorState,
    coupling: Arc<SparseCoupling>,
    integrator: Box<dyn Integrator>,
    dt: f64,
}

impl OscilloSim {
    /// Create a new simulation engine.
    ///
    /// `coupling` accepts either an owned [`SparseCoupling`] or an
    /// `Arc<SparseCoupling>`. To share the same coupling matrix with a
    /// [`SparseKuramoto`]/[`SparseStuartLandau`] model without deep-cloning
    /// the CSR storage (WP016-F7), construct an `Arc<SparseCoupling>` once,
    /// pass it here, and pass [`OscilloSim::coupling_arc`] (or another
    /// `Arc::clone` of the same value) to the model constructor.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an invalid timestep, empty population, or
    /// pruning validation failure.
    pub fn new(
        state: OscillatorState,
        coupling: impl Into<Arc<SparseCoupling>>,
        integrator: Box<dyn Integrator>,
        dt: f64,
    ) -> Result<Self, SimError> {
        let coupling = coupling.into();
        if state.n_oscillators() == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if coupling.n_oscillators() != state.n_oscillators() {
            return Err(SimError::DimensionMismatch {
                name: "coupling vs state",
                expected: state.n_oscillators(),
                got: coupling.n_oscillators(),
            });
        }
        validate_dt(dt)?;

        Ok(Self {
            state,
            coupling,
            integrator,
            dt,
        })
    }

    /// Current oscillator state.
    pub fn state(&self) -> &OscillatorState {
        &self.state
    }

    /// Current timestep.
    pub fn dt(&self) -> f64 {
        self.dt
    }

    /// Set the timestep.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an invalid timestep.
    pub fn set_dt(&mut self, dt: f64) -> Result<(), SimError> {
        validate_dt(dt)?;
        self.dt = dt;
        Ok(())
    }

    /// Borrow the coupling matrix.
    pub fn coupling(&self) -> &SparseCoupling {
        &self.coupling
    }

    /// Clone the shared coupling handle (O(1) refcount bump, no CSR data
    /// copy) for passing to a [`SparseKuramoto`]/[`SparseStuartLandau`]
    /// model constructor (WP016-F7).
    pub fn coupling_arc(&self) -> Arc<SparseCoupling> {
        Arc::clone(&self.coupling)
    }

    /// Advance the simulation by one timestep.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for dynamics or integration failures.
    pub fn step(&mut self, model: &dyn Dynamics) -> Result<(), SimError> {
        self.state = self
            .integrator
            .step(model, &self.state, self.dt)
            .map_err(SimError::Integration)?;
        Ok(())
    }

    /// Run the simulation for `n_steps` timesteps.
    ///
    /// If `record_trajectory` is true, the state is recorded at every step
    /// (including the initial state at time 0).
    ///
    /// Returns the final state and (optionally) the full trajectory.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for zero steps, dynamics failures, or integration
    /// errors.
    pub fn run(
        &mut self,
        model: &dyn Dynamics,
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

        let mut trajectory = if record_trajectory {
            let mut t = Trajectory {
                phases: Vec::with_capacity(n_steps + 1),
                amplitudes: Vec::with_capacity(n_steps + 1),
                frequencies: Vec::with_capacity(n_steps + 1),
                times: Vec::with_capacity(n_steps + 1),
            };
            t.phases.push(self.state.phase.clone());
            t.amplitudes.push(self.state.amplitude.clone());
            t.frequencies.push(self.state.frequency.clone());
            t.times.push(0.0);
            Some(t)
        } else {
            None
        };

        for step in 0..n_steps {
            self.step(model)?;
            if let Some(ref mut traj) = trajectory {
                traj.phases.push(self.state.phase.clone());
                traj.amplitudes.push(self.state.amplitude.clone());
                traj.frequencies.push(self.state.frequency.clone());
                traj.times.push((step + 1) as f64 * self.dt);
            }
        }

        Ok((self.state.clone(), trajectory))
    }

    /// Approximate memory footprint of the engine state in bytes.
    pub fn memory_bytes(&self) -> usize {
        let n = self.state.n_oscillators();
        let state_bytes = n * 3 * std::mem::size_of::<f64>();
        let coupling_bytes = self.coupling.memory_bytes();
        state_bytes + coupling_bytes
    }
}

/// Apply numerical guards to an oscillator state: wrap phases, clamp amplitudes.
///
/// This is a convenience function for post-integration cleanup. The integrators
/// in `prin-dynamics` already apply these guards, so this is only needed when
/// implementing custom integration loops.
pub fn apply_guards(state: &mut OscillatorState) {
    for p in &mut state.phase {
        *p = wrap_phase(*p);
    }
    for a in &mut state.amplitude {
        *a = clamp_amplitude(*a);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use prin_dynamics::{RK4Integrator, Seed};
    use std::f64::consts::TAU;

    fn make_engine(n: usize, dt: f64) -> (OscilloSim, SparseKuramoto) {
        let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let engine = OscilloSim::new(state, coupling, integrator, dt).unwrap();
        (engine, model)
    }

    #[test]
    fn engine_step_advances_state() {
        let (mut engine, model) = make_engine(16, 0.01);
        let phase_before = engine.state().phase.clone();
        engine.step(&model).unwrap();
        assert_ne!(engine.state().phase, phase_before);
    }

    #[test]
    fn engine_run_records_trajectory() {
        let (mut engine, model) = make_engine(8, 0.01);
        let (final_state, traj) = engine.run(&model, 10, true).unwrap();
        assert_eq!(final_state.n_oscillators(), 8);
        let traj = traj.unwrap();
        assert_eq!(traj.n_steps(), 11);
        assert_eq!(traj.n_oscillators(), 8);
        assert!((traj.times[10] - 0.1).abs() < 1e-12);
    }

    #[test]
    fn engine_run_no_trajectory() {
        let (mut engine, model) = make_engine(8, 0.01);
        let (_, traj) = engine.run(&model, 5, false).unwrap();
        assert!(traj.is_none());
    }

    #[test]
    fn engine_zero_steps_error() {
        let (mut engine, model) = make_engine(8, 0.01);
        let err = engine.run(&model, 0, false).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn engine_deterministic() {
        let (mut e1, m1) = make_engine(16, 0.01);
        let (mut e2, m2) = make_engine(16, 0.01);
        let (_, t1) = e1.run(&m1, 50, true).unwrap();
        let (_, t2) = e2.run(&m2, 50, true).unwrap();
        assert_eq!(t1.unwrap().phases, t2.unwrap().phases);
    }

    #[test]
    fn sparse_kuramoto_n1_free_streaming() {
        let coupling = SparseCoupling::from_ring(1, 0, 0.0).unwrap_err();
        assert!(matches!(coupling, SimError::InvalidCoupling { .. }));
    }

    #[test]
    fn sparse_kuramoto_dimension_mismatch() {
        let coupling = SparseCoupling::from_ring(8, 1, 1.0).unwrap();
        let err = SparseKuramoto::new(16, 0.1, 0.01, coupling).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn sparse_stuart_landau_basic() {
        let n = 8;
        let coupling = SparseCoupling::from_ring(n, 2, 0.5).unwrap();
        let model = SparseStuartLandau::new(n, 1.0, coupling).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let derivs = model.compute_derivatives(&state).unwrap();
        assert_eq!(derivs.n_oscillators(), n);
    }

    #[test]
    fn trajectory_memory_bytes() {
        let (mut engine, model) = make_engine(8, 0.01);
        let (_, traj) = engine.run(&model, 10, true).unwrap();
        let traj = traj.unwrap();
        assert!(traj.memory_bytes() > 0);
    }

    #[test]
    fn engine_memory_bytes_positive() {
        let (engine, _) = make_engine(8, 0.01);
        assert!(engine.memory_bytes() > 0);
    }

    #[test]
    fn apply_guards_wraps_phases() {
        let mut state = OscillatorState::new(
            vec![TAU + 0.1, -0.1],
            vec![
                prin_dynamics::state::AMPLITUDE_MAX,
                prin_dynamics::state::AMPLITUDE_MIN,
            ],
            vec![1.0, 1.0],
            None,
        )
        .unwrap();
        apply_guards(&mut state);
        assert!((state.phase[0] - 0.1).abs() < 1e-12);
        assert!((state.phase[1] - (TAU - 0.1)).abs() < 1e-12);
        assert!((state.amplitude[0] - 10.0).abs() < 1e-12);
        assert!((state.amplitude[1] - 1e-6).abs() < 1e-12);
    }

    #[test]
    fn engine_with_low_amplitude_state() {
        let n = 8;
        let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let mut amplitudes = vec![1.0; n];
        amplitudes[0] = prin_dynamics::state::AMPLITUDE_MIN;
        amplitudes[3] = prin_dynamics::state::AMPLITUDE_MIN;
        let state = OscillatorState::new(vec![0.0; n], amplitudes, vec![1.0; n], None).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let mut engine = OscilloSim::new(state, coupling, integrator, 0.01).unwrap();
        engine.step(&model).unwrap();
        assert_eq!(engine.state().n_oscillators(), n);
    }

    #[test]
    fn set_dt_validates() {
        let (mut engine, _) = make_engine(8, 0.01);
        assert!(engine.set_dt(0.05).is_ok());
        assert!(engine.set_dt(-1.0).is_err());
        assert!(engine.set_dt(f64::NAN).is_err());
    }

    // ── SparseStuartLandau error paths ────────────────────────────────────

    #[test]
    fn sparse_stuart_landau_n_zero() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseStuartLandau::new(0, 1.0, coupling).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn sparse_stuart_landau_non_finite_bifurcation() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseStuartLandau::new(4, f64::NAN, coupling).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn sparse_stuart_landau_coupling_dimension_mismatch() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseStuartLandau::new(8, 1.0, coupling).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn sparse_stuart_landau_n1_free_streaming() {
        // n=1: no coupling needed, just the intrinsic dynamics
        // from_ring(1, 0, _) fails because degree=0 is invalid, so build manually
        let indptr = vec![0, 0];
        let indices: Vec<usize> = vec![];
        let data: Vec<f64> = vec![];
        let coupling = SparseCoupling::from_csr(&indptr, &indices, &data, 1).unwrap();
        let model = SparseStuartLandau::new(1, 1.0, coupling).unwrap();
        let state = OscillatorState::new(vec![0.5], vec![1.0], vec![2.0], None).unwrap();
        let derivs = model.compute_derivatives(&state).unwrap();
        // n<=1: dphase = frequency, damplitude = mu*r - r^3, dfrequency = 0
        assert!((derivs.dphase[0] - 2.0).abs() < 1e-12);
        assert!((derivs.damplitude[0] - (1.0 * 1.0 - 1.0 * 1.0 * 1.0)).abs() < 1e-12);
        assert!((derivs.dfrequency[0]).abs() < 1e-12);
    }

    #[test]
    fn sparse_stuart_landau_state_dimension_mismatch() {
        let n = 4;
        let coupling = SparseCoupling::from_ring(n, 1, 1.0).unwrap();
        let model = SparseStuartLandau::new(n, 1.0, coupling).unwrap();
        let wrong_state =
            OscillatorState::new(vec![0.0; 8], vec![1.0; 8], vec![1.0; 8], None).unwrap();
        let err = model.compute_derivatives(&wrong_state).unwrap_err();
        assert!(matches!(err, StateError::LengthMismatch { .. }));
    }

    // ── SparseKuramoto error paths ────────────────────────────────────────

    #[test]
    fn sparse_kuramoto_n_zero() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseKuramoto::new(0, 0.1, 0.01, coupling).unwrap_err();
        assert!(matches!(err, SimError::EmptyPopulation { .. }));
    }

    #[test]
    fn sparse_kuramoto_non_finite_decay_rate() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseKuramoto::new(4, f64::INFINITY, 0.01, coupling).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn sparse_kuramoto_non_finite_freq_adaptation_rate() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let err = SparseKuramoto::new(4, 0.1, f64::NAN, coupling).unwrap_err();
        assert!(matches!(err, SimError::NonFiniteValue { .. }));
    }

    #[test]
    fn sparse_kuramoto_n1_derivatives() {
        let indptr = vec![0, 0];
        let indices: Vec<usize> = vec![];
        let data: Vec<f64> = vec![];
        let coupling = SparseCoupling::from_csr(&indptr, &indices, &data, 1).unwrap();
        let model = SparseKuramoto::new(1, 0.1, 0.01, coupling).unwrap();
        let state = OscillatorState::new(vec![0.5], vec![1.0], vec![3.0], None).unwrap();
        let derivs = model.compute_derivatives(&state).unwrap();
        // n<=1: dphase = frequency, damplitude = -decay*r, dfrequency = 0
        assert!((derivs.dphase[0] - 3.0).abs() < 1e-12);
        assert!((derivs.damplitude[0] - (-0.1 * 1.0)).abs() < 1e-12);
        assert!((derivs.dfrequency[0]).abs() < 1e-12);
    }

    #[test]
    fn sparse_kuramoto_state_dimension_mismatch() {
        let n = 4;
        let coupling = SparseCoupling::from_ring(n, 1, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling).unwrap();
        let wrong_state =
            OscillatorState::new(vec![0.0; 8], vec![1.0; 8], vec![1.0; 8], None).unwrap();
        let err = model.compute_derivatives(&wrong_state).unwrap_err();
        assert!(matches!(err, StateError::LengthMismatch { .. }));
    }

    // ── OscilloSim::new error paths ───────────────────────────────────────

    #[test]
    fn oscillo_sim_new_coupling_state_mismatch() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let state = OscillatorState::create_random(8, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let result = OscilloSim::new(state, coupling, integrator, 0.01);
        assert!(matches!(
            result.err(),
            Some(SimError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn oscillo_sim_new_invalid_dt() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let state = OscillatorState::create_random(4, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let result = OscilloSim::new(state, coupling, integrator, 0.0);
        assert!(matches!(
            result.err(),
            Some(SimError::NonFiniteValue { .. })
        ));
    }

    #[test]
    fn oscillo_sim_new_infinite_dt() {
        let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
        let state = OscillatorState::create_random(4, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let result = OscilloSim::new(state, coupling, integrator, f64::INFINITY);
        assert!(matches!(
            result.err(),
            Some(SimError::NonFiniteValue { .. })
        ));
    }

    // ── SparseKuramoto / SparseStuartLandau accessors ─────────────────────

    #[test]
    fn sparse_kuramoto_accessors() {
        let coupling = SparseCoupling::from_ring(8, 2, 1.0).unwrap();
        let model = SparseKuramoto::new(8, 0.2, 0.05, coupling.clone()).unwrap();
        assert_eq!(model.n_oscillators(), 8);
        assert!((model.decay_rate() - 0.2).abs() < 1e-12);
        assert!((model.freq_adaptation_rate() - 0.05).abs() < 1e-12);
        assert_eq!(model.coupling().n_oscillators(), 8);
    }

    #[test]
    fn sparse_stuart_landau_accessors() {
        let coupling = SparseCoupling::from_ring(8, 2, 1.0).unwrap();
        let model = SparseStuartLandau::new(8, 1.5, coupling.clone()).unwrap();
        assert_eq!(model.n_oscillators(), 8);
        assert!((model.bifurcation_param() - 1.5).abs() < 1e-12);
        assert_eq!(model.coupling().n_oscillators(), 8);
    }

    // ── Engine with Stuart-Landau model ───────────────────────────────────

    #[test]
    fn engine_run_stuart_landau() {
        let n = 8;
        let coupling = SparseCoupling::from_ring(n, 2, 0.5).unwrap();
        let model = SparseStuartLandau::new(n, 1.0, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let mut engine = OscilloSim::new(state, coupling, integrator, 0.01).unwrap();
        let (final_state, traj) = engine.run(&model, 10, true).unwrap();
        assert_eq!(final_state.n_oscillators(), n);
        let traj = traj.unwrap();
        assert_eq!(traj.n_steps(), 11);
    }

    // ── Trajectory accessors ──────────────────────────────────────────────

    #[test]
    fn trajectory_empty_n_oscillators() {
        let traj = Trajectory {
            phases: vec![],
            amplitudes: vec![],
            frequencies: vec![],
            times: vec![],
        };
        assert_eq!(traj.n_steps(), 0);
        assert_eq!(traj.n_oscillators(), 0);
    }

    // ── Engine with Euler integrator ──────────────────────────────────────

    #[test]
    fn engine_with_euler_integrator() {
        use prin_dynamics::EulerIntegrator;
        let n = 8;
        let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let integrator = Box::new(EulerIntegrator::new());
        let mut engine = OscilloSim::new(state, coupling, integrator, 0.001).unwrap();
        engine.step(&model).unwrap();
        assert_eq!(engine.state().n_oscillators(), n);
    }
}

//! Numerical integrators behind the [`Integrator`] trait.
//!
//! - [`EulerIntegrator`]: forward Euler (first order), matching PRINet 3.0
//!   `_step_euler`.
//! - [`RK4Integrator`]: classic fourth-order Runge–Kutta, matching PRINet 3.0
//!   `_step_rk4`.
//! - [`RK45Integrator`]: adaptive Dormand–Prince (DOPRI5) with embedded
//!   fourth/fifth-order error estimate and PI step-size control. This is a new
//!   PRIN capability (PRINet 3.0 has no adaptive integrator).
//! - [`ExponentialIntegrator`]: exponential Euler via matrix exponential
//!   (direct Padé scaling-and-squaring or Krylov–Arnoldi), with φ₁ computed
//!   via the augmented-matrix identity. Handles stiff linear modes exactly.
//!   New in WP-012.
//! - [`MultiRateIntegrator`]: sub-stepped RK4/Euler for hierarchical
//!   frequency-band systems. Different bands can be integrated at different
//!   effective time resolutions. New in WP-012.
//!
//! All integrators use **explicit reusable buffers** (pre-allocated workspace
//! vectors sized to `3N`) to avoid per-step heap allocation, and apply the
//! PRINet 3.0 numerical guards: phase wrap to `[0, 2π)`, amplitude clamp to
//! `[AMPLITUDE_MIN, AMPLITUDE_MAX]`, and derivative clamp `±DERIV_CLAMP`
//! (applied inside [`StateDerivatives::new`]).
//!
//! # Parity notes
//!
//! Euler and RK4 are faithful ports of PRINet 3.0's `_step_euler` and
//! `_step_rk4` (`oscillator_models.py`). Intermediate RK4 stages are built
//! without phase wrapping (matching PRINet's `_make_state`); all phase-dependent
//! operations in the models are `2π`-periodic, so wrapping vs not wrapping
//! intermediate phase produces identical derivatives. The final state wraps
//! phase and clamps amplitude exactly as PRINet does. RK45 is a new capability
//! with no PRINet counterpart; its acceptance is the tolerance-property test
//! (error scales with the requested tolerance).

use ndarray::Array2;
use thiserror::Error;

use crate::models::Dynamics;
use crate::state::{clamp_amplitude, wrap_phase, OscillatorState, StateDerivatives, StateError};

/// Safety factor for adaptive step-size scaling.
const SAFETY: f64 = 0.9;
/// Minimum step-size shrink factor per rejected step.
const MIN_FACTOR: f64 = 0.2;
/// Maximum step-size growth factor per accepted step.
const MAX_FACTOR: f64 = 5.0;
/// Exponent for fifth-order error estimate: `error^(-1/order)`.
const ERR_EXPONENT: f64 = -1.0 / 5.0;
/// Minimum step size before declaring step-size underflow.
const MIN_DT: f64 = 1e-14;

/// Errors raised by integrator construction and execution.
#[derive(Debug, Error)]
pub enum IntegrateError {
    /// The timestep is non-finite or non-positive.
    #[error("invalid timestep: dt={dt}")]
    InvalidTimestep {
        /// The offending timestep.
        dt: f64,
    },

    /// The relative or absolute tolerance is non-finite or non-positive.
    #[error("invalid tolerance: {param}={value}")]
    InvalidTolerance {
        /// Name of the offending tolerance parameter (`"rtol"` or `"atol"`).
        param: &'static str,
        /// The offending tolerance value.
        value: f64,
    },

    /// The number of integration steps is zero.
    #[error("number of steps must be positive, got 0")]
    ZeroSteps,

    /// A dynamics evaluation failed.
    #[error("dynamics evaluation failed: {0}")]
    Dynamics(#[from] StateError),

    /// Adaptive integration did not meet tolerance within the step budget.
    #[error("adaptive integration did not meet tolerance within {max_steps} steps")]
    ToleranceNotMet {
        /// The exhausted step budget.
        max_steps: usize,
    },

    /// The adaptive step size dropped below the minimum.
    #[error("adaptive step size dropped below minimum {min_dt}")]
    StepSizeUnderflow {
        /// The minimum step-size floor.
        min_dt: f64,
    },

    /// A non-finite value was produced during integration under `strict-checks`.
    #[error("non-finite value in `{field}` at index {index}: {value}")]
    NonFiniteValue {
        /// Name of the offending field.
        field: &'static str,
        /// Index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
    },

    /// The system dimension is not positive.
    #[error("system dimension must be positive, got {dim}")]
    InvalidDim {
        /// The offending dimension.
        dim: usize,
    },

    /// The Krylov subspace rank is too small.
    #[error("krylov_rank must be >= 2, got {rank}")]
    InvalidKrylovRank {
        /// The offending Krylov rank.
        rank: usize,
    },

    /// The LU decomposition encountered a singular matrix.
    #[error("LU decomposition failed: singular matrix")]
    LinearSolveFailed,
}

/// Trait for time integrators of oscillator dynamics.
///
/// Implementations advance an [`OscillatorState`] forward in time using a
/// [`Dynamics`] model. Fixed-step integrators (Euler, RK4) use `dt` directly;
/// the adaptive [`RK45Integrator`] additionally provides
/// [`RK45Integrator::integrate_adaptive`].
pub trait Integrator {
    /// Advance `state` by one timestep `dt` using `model`.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError`] for an invalid timestep, a dynamics evaluation
    /// failure, or (under `strict-checks`) a non-finite result.
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError>;
}

/// Validate that `dt` is finite and positive.
fn validate_dt(dt: f64) -> Result<(), IntegrateError> {
    if !dt.is_finite() || dt <= 0.0 {
        return Err(IntegrateError::InvalidTimestep { dt });
    }
    Ok(())
}

/// Build an intermediate (non-final) state from a base state and a scaled
/// derivative increment.
///
/// Phase is **not** wrapped (matching PRINet 3.0 `_make_state`); all
/// phase-dependent model operations are `2π`-periodic so this is exact.
/// Amplitude is clamped to `[AMPLITUDE_MIN, AMPLITUDE_MAX]`. `freq_band` is
/// omitted from intermediate states (it does not enter the dynamics).
#[allow(clippy::too_many_arguments)]
fn make_intermediate_state(
    base: &OscillatorState,
    dphase: &[f64],
    damplitude: &[f64],
    dfrequency: &[f64],
    scale: f64,
    phase_buf: &mut Vec<f64>,
    amp_buf: &mut Vec<f64>,
    freq_buf: &mut Vec<f64>,
) -> OscillatorState {
    let n = base.phase.len();
    phase_buf.clear();
    phase_buf.reserve(n);
    amp_buf.clear();
    amp_buf.reserve(n);
    freq_buf.clear();
    freq_buf.reserve(n);
    for i in 0..n {
        phase_buf.push(base.phase[i] + scale * dphase[i]);
        amp_buf.push(clamp_amplitude(base.amplitude[i] + scale * damplitude[i]));
        freq_buf.push(base.frequency[i] + scale * dfrequency[i]);
    }
    OscillatorState {
        phase: phase_buf.clone(),
        amplitude: amp_buf.clone(),
        frequency: freq_buf.clone(),
        freq_band: None,
    }
}

/// Build the final (output) state from computed arrays, applying phase wrap,
/// amplitude clamp, and carrying `freq_band` from the base state.
fn make_final_state(
    base: &OscillatorState,
    phase: Vec<f64>,
    amplitude: Vec<f64>,
    frequency: Vec<f64>,
) -> Result<OscillatorState, IntegrateError> {
    let phase: Vec<f64> = phase.into_iter().map(wrap_phase).collect();
    let amplitude: Vec<f64> = amplitude.into_iter().map(clamp_amplitude).collect();
    let state = OscillatorState {
        phase,
        amplitude,
        frequency,
        freq_band: base.freq_band.clone(),
    };
    check_finite(&state)?;
    Ok(state)
}

/// Under `strict-checks`, verify every state component is finite and return
/// a typed error if not. Under non-strict, only amplitude is repaired (via
/// `clamp_amplitude` in `make_final_state`); non-finite phase or frequency
/// values pass through silently and are only caught under `strict-checks`.
fn check_finite(state: &OscillatorState) -> Result<(), IntegrateError> {
    #[cfg(feature = "strict-checks")]
    {
        for (i, &v) in state.phase.iter().enumerate() {
            if !v.is_finite() {
                return Err(IntegrateError::NonFiniteValue {
                    field: "phase",
                    index: i,
                    value: v,
                });
            }
        }
        for (i, &v) in state.amplitude.iter().enumerate() {
            if !v.is_finite() {
                return Err(IntegrateError::NonFiniteValue {
                    field: "amplitude",
                    index: i,
                    value: v,
                });
            }
        }
        for (i, &v) in state.frequency.iter().enumerate() {
            if !v.is_finite() {
                return Err(IntegrateError::NonFiniteValue {
                    field: "frequency",
                    index: i,
                    value: v,
                });
            }
        }
    }
    #[cfg(not(feature = "strict-checks"))]
    {
        let _ = state;
    }
    Ok(())
}

/// Forward Euler integrator (first order).
///
/// Faithful port of PRINet 3.0 `_step_euler`:
///
/// ```text
/// φ_{n+1} = wrap(φ_n + h · dφ/dt)
/// r_{n+1} = clamp(r_n + h · dr/dt)
/// ω_{n+1} = ω_n + h · dω/dt
/// ```
#[derive(Clone, Debug)]
pub struct EulerIntegrator {
    /// Reusable derivative-evaluation buffer (flat `3N`).
    deriv_buf: Vec<f64>,
}

impl EulerIntegrator {
    /// Create a new Euler integrator with empty buffers (sized on first use).
    #[must_use]
    pub fn new() -> Self {
        Self {
            deriv_buf: Vec::new(),
        }
    }

    /// Create a new Euler integrator with buffers pre-sized for `n` oscillators.
    #[must_use]
    pub fn with_capacity(n: usize) -> Self {
        Self {
            deriv_buf: Vec::with_capacity(3 * n),
        }
    }
}

impl Default for EulerIntegrator {
    fn default() -> Self {
        Self::new()
    }
}

impl Integrator for EulerIntegrator {
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError> {
        validate_dt(dt)?;
        let k1 = model.compute_derivatives(state)?;
        let n = state.phase.len();
        self.deriv_buf.clear();
        self.deriv_buf.reserve(3 * n);
        // Flatten (dphase, damplitude, dfrequency) into the reusable buffer.
        self.deriv_buf.extend_from_slice(&k1.dphase);
        self.deriv_buf.extend_from_slice(&k1.damplitude);
        self.deriv_buf.extend_from_slice(&k1.dfrequency);

        let dphase = &self.deriv_buf[..n];
        let damplitude = &self.deriv_buf[n..2 * n];
        let dfrequency = &self.deriv_buf[2 * n..];

        let phase: Vec<f64> = (0..n).map(|i| state.phase[i] + dt * dphase[i]).collect();
        let amplitude: Vec<f64> = (0..n)
            .map(|i| state.amplitude[i] + dt * damplitude[i])
            .collect();
        let frequency: Vec<f64> = (0..n)
            .map(|i| state.frequency[i] + dt * dfrequency[i])
            .collect();

        make_final_state(state, phase, amplitude, frequency)
    }
}

/// Classic fourth-order Runge–Kutta integrator (RK4).
///
/// Faithful port of PRINet 3.0 `_step_rk4`:
///
/// ```text
/// k1 = f(y_n)
/// k2 = f(y_n + h/2 · k1)
/// k3 = f(y_n + h/2 · k2)
/// k4 = f(y_n + h   · k3)
/// y_{n+1} = y_n + h/6 · (k1 + 2k2 + 2k3 + k4)
/// ```
///
/// Intermediate stages are built without phase wrapping (matching PRINet's
/// `_make_state`); all model phase operations are `2π`-periodic so this is
/// exact. The four derivative evaluations and intermediate state arrays use
/// explicit reusable buffers.
#[derive(Clone, Debug)]
pub struct RK4Integrator {
    /// Flat `3N` buffer for k1.
    k1: Vec<f64>,
    /// Flat `3N` buffer for k2.
    k2: Vec<f64>,
    /// Flat `3N` buffer for k3.
    k3: Vec<f64>,
    /// Flat `3N` buffer for k4.
    k4: Vec<f64>,
    /// Reusable intermediate-state phase buffer.
    phase_buf: Vec<f64>,
    /// Reusable intermediate-state amplitude buffer.
    amp_buf: Vec<f64>,
    /// Reusable intermediate-state frequency buffer.
    freq_buf: Vec<f64>,
}

impl RK4Integrator {
    /// Create a new RK4 integrator with empty buffers (sized on first use).
    #[must_use]
    pub fn new() -> Self {
        Self {
            k1: Vec::new(),
            k2: Vec::new(),
            k3: Vec::new(),
            k4: Vec::new(),
            phase_buf: Vec::new(),
            amp_buf: Vec::new(),
            freq_buf: Vec::new(),
        }
    }

    /// Create a new RK4 integrator with buffers pre-sized for `n` oscillators.
    #[must_use]
    pub fn with_capacity(n: usize) -> Self {
        let cap = 3 * n;
        Self {
            k1: Vec::with_capacity(cap),
            k2: Vec::with_capacity(cap),
            k3: Vec::with_capacity(cap),
            k4: Vec::with_capacity(cap),
            phase_buf: Vec::with_capacity(n),
            amp_buf: Vec::with_capacity(n),
            freq_buf: Vec::with_capacity(n),
        }
    }

    /// Flatten a [`StateDerivatives`] into a reusable `3N` buffer.
    fn flatten(&mut self, deriv: &StateDerivatives, n: usize) {
        self.k1.clear();
        self.k1.reserve(3 * n);
        self.k1.extend_from_slice(&deriv.dphase);
        self.k1.extend_from_slice(&deriv.damplitude);
        self.k1.extend_from_slice(&deriv.dfrequency);
    }
}

impl Default for RK4Integrator {
    fn default() -> Self {
        Self::new()
    }
}

impl Integrator for RK4Integrator {
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError> {
        validate_dt(dt)?;
        let n = state.phase.len();
        let half = 0.5 * dt;
        let sixth = dt / 6.0;

        // k1 = f(y_n)
        let d1 = model.compute_derivatives(state)?;
        self.flatten(&d1, n);
        let k1 = self.k1.clone();

        // k2 = f(y_n + h/2 · k1)
        let s2 = make_intermediate_state(
            state,
            &k1[..n],
            &k1[n..2 * n],
            &k1[2 * n..],
            half,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d2 = model.compute_derivatives(&s2)?;
        self.k2.clear();
        self.k2.reserve(3 * n);
        self.k2.extend_from_slice(&d2.dphase);
        self.k2.extend_from_slice(&d2.damplitude);
        self.k2.extend_from_slice(&d2.dfrequency);
        let k2 = self.k2.clone();

        // k3 = f(y_n + h/2 · k2)
        let s3 = make_intermediate_state(
            state,
            &k2[..n],
            &k2[n..2 * n],
            &k2[2 * n..],
            half,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d3 = model.compute_derivatives(&s3)?;
        self.k3.clear();
        self.k3.reserve(3 * n);
        self.k3.extend_from_slice(&d3.dphase);
        self.k3.extend_from_slice(&d3.damplitude);
        self.k3.extend_from_slice(&d3.dfrequency);
        let k3 = self.k3.clone();

        // k4 = f(y_n + h · k3)
        let s4 = make_intermediate_state(
            state,
            &k3[..n],
            &k3[n..2 * n],
            &k3[2 * n..],
            dt,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d4 = model.compute_derivatives(&s4)?;
        self.k4.clear();
        self.k4.reserve(3 * n);
        self.k4.extend_from_slice(&d4.dphase);
        self.k4.extend_from_slice(&d4.damplitude);
        self.k4.extend_from_slice(&d4.dfrequency);
        let k4 = &self.k4;

        // y_{n+1} = y_n + h/6 · (k1 + 2k2 + 2k3 + k4)
        let phase: Vec<f64> = (0..n)
            .map(|i| state.phase[i] + sixth * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]))
            .collect();
        let amplitude: Vec<f64> = (0..n)
            .map(|i| {
                state.amplitude[i]
                    + sixth * (k1[n + i] + 2.0 * k2[n + i] + 2.0 * k3[n + i] + k4[n + i])
            })
            .collect();
        let frequency: Vec<f64> = (0..n)
            .map(|i| {
                state.frequency[i]
                    + sixth
                        * (k1[2 * n + i]
                            + 2.0 * k2[2 * n + i]
                            + 2.0 * k3[2 * n + i]
                            + k4[2 * n + i])
            })
            .collect();

        make_final_state(state, phase, amplitude, frequency)
    }
}

/// Result of an adaptive [`RK45Integrator`] integration.
#[derive(Clone, Debug)]
pub struct AdaptiveResult {
    /// Final oscillator state after integration.
    pub final_state: OscillatorState,
    /// Recorded trajectory (one entry per accepted step), if requested.
    pub trajectory: Option<Vec<OscillatorState>>,
    /// Number of accepted steps.
    pub accepted_steps: usize,
    /// Number of rejected (step-size-too-large) steps.
    pub rejected_steps: usize,
    /// Final timestep used.
    pub final_dt: f64,
}

/// Adaptive Dormand–Prince (DOPRI5) integrator with embedded fourth/fifth-order
/// error estimate.
///
/// This is a **new PRIN capability** (PRINet 3.0 has no adaptive integrator).
/// It uses the Dormand–Prince 5(4) coefficients with FSAL (First Same As Last)
/// and standard error-based step-size control:
///
/// ```text
/// err_norm = sqrt( mean( ((y5 - y4) / (atol + rtol · max(|y|, |y5|)))^2 ) )
/// ```
///
/// If `err_norm ≤ 1` the step is accepted and `dt` is grown; otherwise the step
/// is rejected and `dt` is shrunk. The scaling factor is
/// `clamp(SAFETY · err_norm^(-1/5), MIN_FACTOR, MAX_FACTOR)`.
#[derive(Clone, Debug)]
pub struct RK45Integrator {
    /// Relative tolerance.
    rtol: f64,
    /// Absolute tolerance.
    atol: f64,
    /// Maximum number of (accepted + rejected) steps before giving up.
    max_steps: usize,
    /// Flat `3N` buffers for the seven DOPRI5 stages k1..k7.
    ks: [Vec<f64>; 7],
    /// Reusable intermediate-state phase buffer.
    phase_buf: Vec<f64>,
    /// Reusable intermediate-state amplitude buffer.
    amp_buf: Vec<f64>,
    /// Reusable intermediate-state frequency buffer.
    freq_buf: Vec<f64>,
    /// Reusable `3N` error buffer.
    err_buf: Vec<f64>,
    /// Reusable `3N` fifth-order solution buffer.
    y5_buf: Vec<f64>,
    /// Whether `ks[0]` holds a valid FSAL cache (k7 from the previous accepted
    /// step within the *current* `integrate_adaptive` call). Invalidated at the
    /// start of each call so that a reused integrator recomputes k1 for the new
    /// initial state.
    fsal_valid: bool,
}

impl RK45Integrator {
    /// Create a new adaptive RK45 integrator.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError`] if `rtol` or `atol` is non-finite or
    /// non-positive, or if `max_steps` is zero.
    pub fn new(rtol: f64, atol: f64, max_steps: usize) -> Result<Self, IntegrateError> {
        if !rtol.is_finite() || rtol <= 0.0 {
            return Err(IntegrateError::InvalidTolerance {
                param: "rtol",
                value: rtol,
            });
        }
        if !atol.is_finite() || atol < 0.0 {
            return Err(IntegrateError::InvalidTolerance {
                param: "atol",
                value: atol,
            });
        }
        if max_steps == 0 {
            return Err(IntegrateError::ZeroSteps);
        }
        Ok(Self {
            rtol,
            atol,
            max_steps,
            ks: std::array::from_fn(|_| Vec::new()),
            phase_buf: Vec::new(),
            amp_buf: Vec::new(),
            freq_buf: Vec::new(),
            err_buf: Vec::new(),
            y5_buf: Vec::new(),
            fsal_valid: false,
        })
    }

    /// Relative tolerance.
    #[must_use]
    pub fn rtol(&self) -> f64 {
        self.rtol
    }

    /// Absolute tolerance.
    #[must_use]
    pub fn atol(&self) -> f64 {
        self.atol
    }

    /// Maximum step budget.
    #[must_use]
    pub fn max_steps(&self) -> usize {
        self.max_steps
    }

    /// Flatten a [`StateDerivatives`] into one of the stage buffers.
    fn flatten_into(&mut self, deriv: &StateDerivatives, n: usize, idx: usize) {
        let buf = &mut self.ks[idx];
        buf.clear();
        buf.reserve(3 * n);
        buf.extend_from_slice(&deriv.dphase);
        buf.extend_from_slice(&deriv.damplitude);
        buf.extend_from_slice(&deriv.dfrequency);
    }

    /// Build an intermediate state for DOPRI5 stage `j` from the base state and
    /// weighted prior stages.
    #[allow(clippy::too_many_arguments)]
    fn stage_state(
        ks: &[Vec<f64>],
        base: &OscillatorState,
        weights: &[(usize, f64)],
        h: f64,
        n: usize,
        phase_buf: &mut Vec<f64>,
        amp_buf: &mut Vec<f64>,
        freq_buf: &mut Vec<f64>,
    ) -> OscillatorState {
        phase_buf.clear();
        phase_buf.reserve(n);
        amp_buf.clear();
        amp_buf.reserve(n);
        freq_buf.clear();
        freq_buf.reserve(n);
        for i in 0..n {
            let mut dp = base.phase[i];
            let mut da = base.amplitude[i];
            let mut df = base.frequency[i];
            for &(stage, w) in weights {
                dp += h * w * ks[stage][i];
                da += h * w * ks[stage][n + i];
                df += h * w * ks[stage][2 * n + i];
            }
            phase_buf.push(dp);
            amp_buf.push(clamp_amplitude(da));
            freq_buf.push(df);
        }
        OscillatorState {
            phase: phase_buf.clone(),
            amplitude: amp_buf.clone(),
            frequency: freq_buf.clone(),
            freq_band: None,
        }
    }

    /// Compute the normalised error norm for a candidate step.
    fn error_norm(&self, base: &[f64], y5: &[f64], err: &[f64]) -> f64 {
        let n = base.len();
        let mut sum = 0.0_f64;
        for i in 0..n {
            let sc = self.atol + self.rtol * base[i].abs().max(y5[i].abs());
            sum += (err[i] / sc) * (err[i] / sc);
        }
        (sum / n as f64).sqrt()
    }

    /// Integrate `model` from `state` over `t_span` time units with adaptive
    /// step sizing, starting from `dt_init`.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError`] for an invalid initial timestep, a dynamics
    /// evaluation failure, step-size underflow, or exhaustion of the step
    /// budget.
    pub fn integrate_adaptive(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        t_span: f64,
        dt_init: f64,
        record_trajectory: bool,
    ) -> Result<AdaptiveResult, IntegrateError> {
        validate_dt(dt_init)?;
        if !t_span.is_finite() || t_span <= 0.0 {
            return Err(IntegrateError::InvalidTimestep { dt: t_span });
        }
        // Invalidate FSAL cache at the start of each integration so a reused
        // integrator recomputes k1 for the new initial state (WP008-F1).
        self.fsal_valid = false;
        let n = state.phase.len();
        let mut current = state.clone();
        let mut t = 0.0_f64;
        let mut dt = dt_init.min(t_span);
        let mut accepted = 0_usize;
        let mut rejected = 0_usize;
        let mut trajectory: Option<Vec<OscillatorState>> = if record_trajectory {
            Some(Vec::new())
        } else {
            None
        };

        // DOPRI5 Butcher tableau coefficients (Dormand–Prince 5(4)).
        // c values (stage time fractions).
        // a coefficients (stage coupling).
        // b5 (fifth-order weights), b4 (fourth-order weights).
        const A21: f64 = 1.0 / 5.0;
        const A31: f64 = 3.0 / 40.0;
        const A32: f64 = 9.0 / 40.0;
        const A41: f64 = 44.0 / 45.0;
        const A42: f64 = -56.0 / 15.0;
        const A43: f64 = 32.0 / 9.0;
        const A51: f64 = 19_372.0 / 6561.0;
        const A52: f64 = -25_260.0 / 2187.0;
        const A53: f64 = 64_448.0 / 6561.0;
        const A54: f64 = -212.0 / 729.0;
        const A61: f64 = 9017.0 / 3168.0;
        const A62: f64 = -355.0 / 33.0;
        const A63: f64 = 46_732.0 / 5247.0;
        const A64: f64 = 49.0 / 176.0;
        const A65: f64 = -5103.0 / 18_656.0;
        const A71: f64 = 35.0 / 384.0;
        const A73: f64 = 500.0 / 1113.0;
        const A74: f64 = 125.0 / 192.0;
        const A75: f64 = -2187.0 / 6784.0;
        const A76: f64 = 11.0 / 84.0;
        // Fifth-order solution weights (b5 = a7* for FSAL).
        // Fourth-order solution weights (b4) for error estimate.
        const B41: f64 = 5179.0 / 57_600.0;
        const B43: f64 = 7571.0 / 16_695.0;
        const B44: f64 = 393.0 / 640.0;
        const B45: f64 = -92_097.0 / 339_200.0;
        const B46: f64 = 187.0 / 2100.0;
        const B47: f64 = 1.0 / 40.0;

        let mut steps_total = 0_usize;
        while t < t_span {
            if steps_total >= self.max_steps {
                return Err(IntegrateError::ToleranceNotMet {
                    max_steps: self.max_steps,
                });
            }
            steps_total += 1;
            if dt < MIN_DT {
                return Err(IntegrateError::StepSizeUnderflow { min_dt: MIN_DT });
            }
            let h = dt.min(t_span - t);

            // Flatten current state into a 3N slice for error computation.
            let base_flat: Vec<f64> = {
                let mut v = Vec::with_capacity(3 * n);
                v.extend_from_slice(&current.phase);
                v.extend_from_slice(&current.amplitude);
                v.extend_from_slice(&current.frequency);
                v
            };

            // k1 = f(y_n) — FSAL: reuse k7 from previous accepted step when valid.
            if !self.fsal_valid || self.ks[0].len() != 3 * n {
                let d1 = model.compute_derivatives(&current)?;
                self.flatten_into(&d1, n, 0);
            }

            // k2 = f(y_n + h · A21 · k1)
            let s2 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A21)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d2 = model.compute_derivatives(&s2)?;
            self.flatten_into(&d2, n, 1);

            // k3 = f(y_n + h · (A31·k1 + A32·k2))
            let s3 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A31), (1, A32)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d3 = model.compute_derivatives(&s3)?;
            self.flatten_into(&d3, n, 2);

            // k4 = f(y_n + h · (A41·k1 + A42·k2 + A43·k3))
            let s4 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A41), (1, A42), (2, A43)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d4 = model.compute_derivatives(&s4)?;
            self.flatten_into(&d4, n, 3);

            // k5 = f(y_n + h · (A51·k1 + A52·k2 + A53·k3 + A54·k4))
            let s5 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A51), (1, A52), (2, A53), (3, A54)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d5 = model.compute_derivatives(&s5)?;
            self.flatten_into(&d5, n, 4);

            // k6 = f(y_n + h · (A61·k1 + ... + A65·k5))
            let s6 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A61), (1, A62), (2, A63), (3, A64), (4, A65)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d6 = model.compute_derivatives(&s6)?;
            self.flatten_into(&d6, n, 5);

            // k7 = f(y_n + h · (A71·k1 + A73·k3 + A74·k4 + A75·k5 + A76·k6))
            let s7 = Self::stage_state(
                &self.ks,
                &current,
                &[(0, A71), (2, A73), (3, A74), (4, A75), (5, A76)],
                h,
                n,
                &mut self.phase_buf,
                &mut self.amp_buf,
                &mut self.freq_buf,
            );
            let d7 = model.compute_derivatives(&s7)?;
            self.flatten_into(&d7, n, 6);

            // Fifth-order solution: y5 = y_n + h · (A71·k1 + A73·k3 + A74·k4 + A75·k5 + A76·k6)
            // (k7 = f(y5) for FSAL, but we computed k7 = f(s7) where s7 uses the same weights.)
            self.y5_buf.clear();
            self.y5_buf.reserve(3 * n);
            for i in 0..n {
                self.y5_buf.push(
                    current.phase[i]
                        + h * (A71 * self.ks[0][i]
                            + A73 * self.ks[2][i]
                            + A74 * self.ks[3][i]
                            + A75 * self.ks[4][i]
                            + A76 * self.ks[5][i]),
                );
            }
            for i in 0..n {
                self.y5_buf.push(
                    current.amplitude[i]
                        + h * (A71 * self.ks[0][n + i]
                            + A73 * self.ks[2][n + i]
                            + A74 * self.ks[3][n + i]
                            + A75 * self.ks[4][n + i]
                            + A76 * self.ks[5][n + i]),
                );
            }
            for i in 0..n {
                self.y5_buf.push(
                    current.frequency[i]
                        + h * (A71 * self.ks[0][2 * n + i]
                            + A73 * self.ks[2][2 * n + i]
                            + A74 * self.ks[3][2 * n + i]
                            + A75 * self.ks[4][2 * n + i]
                            + A76 * self.ks[5][2 * n + i]),
                );
            }

            // Fourth-order solution: y4 = y_n + h · (B41·k1 + B43·k3 + B44·k4 + B45·k5 + B46·k6 + B47·k7)
            // Error = y5 - y4
            self.err_buf.clear();
            self.err_buf.reserve(3 * n);
            for i in 0..n {
                let y4 = current.phase[i]
                    + h * (B41 * self.ks[0][i]
                        + B43 * self.ks[2][i]
                        + B44 * self.ks[3][i]
                        + B45 * self.ks[4][i]
                        + B46 * self.ks[5][i]
                        + B47 * self.ks[6][i]);
                self.err_buf.push(self.y5_buf[i] - y4);
            }
            for i in 0..n {
                let y4 = current.amplitude[i]
                    + h * (B41 * self.ks[0][n + i]
                        + B43 * self.ks[2][n + i]
                        + B44 * self.ks[3][n + i]
                        + B45 * self.ks[4][n + i]
                        + B46 * self.ks[5][n + i]
                        + B47 * self.ks[6][n + i]);
                self.err_buf.push(self.y5_buf[n + i] - y4);
            }
            for i in 0..n {
                let y4 = current.frequency[i]
                    + h * (B41 * self.ks[0][2 * n + i]
                        + B43 * self.ks[2][2 * n + i]
                        + B44 * self.ks[3][2 * n + i]
                        + B45 * self.ks[4][2 * n + i]
                        + B46 * self.ks[5][2 * n + i]
                        + B47 * self.ks[6][2 * n + i]);
                self.err_buf.push(self.y5_buf[2 * n + i] - y4);
            }

            let err_n = self.error_norm(&base_flat, &self.y5_buf, &self.err_buf);

            if err_n <= 1.0 {
                // Accept step.
                t += h;
                accepted += 1;
                let phase: Vec<f64> = self.y5_buf[..n].to_vec();
                let amplitude: Vec<f64> = self.y5_buf[n..2 * n].to_vec();
                let frequency: Vec<f64> = self.y5_buf[2 * n..].to_vec();
                current = make_final_state(&current, phase, amplitude, frequency)?;
                // FSAL: k1 for next step = k7 of this step.
                self.ks[0] = self.ks[6].clone();
                self.fsal_valid = true;
                if let Some(ref mut traj) = trajectory {
                    traj.push(current.clone());
                }
                // Grow step size (proposed next dt; remaining-time clamp
                // happens at the top of the next iteration via `h`).
                let factor = if err_n == 0.0 {
                    MAX_FACTOR
                } else {
                    (SAFETY * err_n.powf(ERR_EXPONENT)).clamp(MIN_FACTOR, MAX_FACTOR)
                };
                dt = (dt * factor).max(MIN_DT);
                if t >= t_span {
                    break;
                }
            } else {
                // Reject step; shrink and retry.
                rejected += 1;
                let factor = (SAFETY * err_n.powf(ERR_EXPONENT)).clamp(MIN_FACTOR, 1.0);
                dt = (dt * factor).max(MIN_DT);
                // Invalidate FSAL cache — k1 must be recomputed.
                self.ks[0].clear();
                self.fsal_valid = false;
            }
        }

        Ok(AdaptiveResult {
            final_state: current,
            trajectory,
            accepted_steps: accepted,
            rejected_steps: rejected,
            final_dt: dt,
        })
    }
}

impl Integrator for RK45Integrator {
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError> {
        // A single fixed-size DOPRI5 step (fifth-order solution, no adaptation).
        validate_dt(dt)?;
        let n = state.phase.len();

        const A21: f64 = 1.0 / 5.0;
        const A31: f64 = 3.0 / 40.0;
        const A32: f64 = 9.0 / 40.0;
        const A41: f64 = 44.0 / 45.0;
        const A42: f64 = -56.0 / 15.0;
        const A43: f64 = 32.0 / 9.0;
        const A51: f64 = 19_372.0 / 6561.0;
        const A52: f64 = -25_260.0 / 2187.0;
        const A53: f64 = 64_448.0 / 6561.0;
        const A54: f64 = -212.0 / 729.0;
        const A61: f64 = 9017.0 / 3168.0;
        const A62: f64 = -355.0 / 33.0;
        const A63: f64 = 46_732.0 / 5247.0;
        const A64: f64 = 49.0 / 176.0;
        const A65: f64 = -5103.0 / 18_656.0;
        const A71: f64 = 35.0 / 384.0;
        const A73: f64 = 500.0 / 1113.0;
        const A74: f64 = 125.0 / 192.0;
        const A75: f64 = -2187.0 / 6784.0;
        const A76: f64 = 11.0 / 84.0;

        let d1 = model.compute_derivatives(state)?;
        self.flatten_into(&d1, n, 0);

        let s2 = Self::stage_state(
            &self.ks,
            state,
            &[(0, A21)],
            dt,
            n,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d2 = model.compute_derivatives(&s2)?;
        self.flatten_into(&d2, n, 1);

        let s3 = Self::stage_state(
            &self.ks,
            state,
            &[(0, A31), (1, A32)],
            dt,
            n,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d3 = model.compute_derivatives(&s3)?;
        self.flatten_into(&d3, n, 2);

        let s4 = Self::stage_state(
            &self.ks,
            state,
            &[(0, A41), (1, A42), (2, A43)],
            dt,
            n,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d4 = model.compute_derivatives(&s4)?;
        self.flatten_into(&d4, n, 3);

        let s5 = Self::stage_state(
            &self.ks,
            state,
            &[(0, A51), (1, A52), (2, A53), (3, A54)],
            dt,
            n,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d5 = model.compute_derivatives(&s5)?;
        self.flatten_into(&d5, n, 4);

        let s6 = Self::stage_state(
            &self.ks,
            state,
            &[(0, A61), (1, A62), (2, A63), (3, A64), (4, A65)],
            dt,
            n,
            &mut self.phase_buf,
            &mut self.amp_buf,
            &mut self.freq_buf,
        );
        let d6 = model.compute_derivatives(&s6)?;
        self.flatten_into(&d6, n, 5);

        // Fifth-order solution: y5 = y_n + h · (A71·k1 + A73·k3 + A74·k4 + A75·k5 + A76·k6)
        let phase: Vec<f64> = (0..n)
            .map(|i| {
                state.phase[i]
                    + dt * (A71 * self.ks[0][i]
                        + A73 * self.ks[2][i]
                        + A74 * self.ks[3][i]
                        + A75 * self.ks[4][i]
                        + A76 * self.ks[5][i])
            })
            .collect();
        let amplitude: Vec<f64> = (0..n)
            .map(|i| {
                state.amplitude[i]
                    + dt * (A71 * self.ks[0][n + i]
                        + A73 * self.ks[2][n + i]
                        + A74 * self.ks[3][n + i]
                        + A75 * self.ks[4][n + i]
                        + A76 * self.ks[5][n + i])
            })
            .collect();
        let frequency: Vec<f64> = (0..n)
            .map(|i| {
                state.frequency[i]
                    + dt * (A71 * self.ks[0][2 * n + i]
                        + A73 * self.ks[2][2 * n + i]
                        + A74 * self.ks[3][2 * n + i]
                        + A75 * self.ks[4][2 * n + i]
                        + A76 * self.ks[5][2 * n + i])
            })
            .collect();

        make_final_state(state, phase, amplitude, frequency)
    }
}

/// Integrate `model` from `state` for `n_steps` fixed steps of size `dt`,
/// optionally recording the trajectory.
///
/// This is the fixed-step driver for [`EulerIntegrator`] and [`RK4Integrator`].
///
/// # Errors
///
/// Returns [`IntegrateError`] for zero steps, an invalid timestep, or a
/// dynamics/numerical-guard failure.
pub fn integrate_fixed(
    integrator: &mut dyn Integrator,
    model: &dyn Dynamics,
    state: &OscillatorState,
    n_steps: usize,
    dt: f64,
    record_trajectory: bool,
) -> Result<(OscillatorState, Option<Vec<OscillatorState>>), IntegrateError> {
    if n_steps == 0 {
        return Err(IntegrateError::ZeroSteps);
    }
    validate_dt(dt)?;
    let mut current = state.clone();
    let mut trajectory: Option<Vec<OscillatorState>> = if record_trajectory {
        Some(Vec::with_capacity(n_steps))
    } else {
        None
    };
    for _ in 0..n_steps {
        current = integrator.step(model, &current, dt)?;
        if let Some(ref mut traj) = trajectory {
            traj.push(current.clone());
        }
    }
    Ok((current, trajectory))
}

// ======================================================================
// WP-012 S1: Exponential and multi-rate integrators
// ======================================================================

// --- Padé(13) coefficients for the diagonal approximant to exp(x). ---
//
// c_j = c_{j-1} · (p − j + 1) / (j · (2p − j + 1))  with p = 13, c_0 = 1.
// Theta_13 from Higham (2005): maximum 1-norm for which the backward error
// of the (13,13) Padé approximant is ≤ 2^{-53}.
const PADE13: [f64; 14] = [
    1.0,
    1.0 / 2.0,
    3.0 / 25.0,
    11.0 / 600.0,
    11.0 / 5_520.0,
    3.0 / 18_400.0,
    1.0 / 96_600.0,
    1.0 / 1_932_000.0,
    1.0 / 48_944_000.0,
    1.0 / 1_585_785_600.0,
    1.0 / 67_395_888_000.0,
    1.0 / 3_953_892_096_000.0,
    1.0 / 355_850_288_640_000.0,
    1.0 / 64_764_752_532_480_000.0,
];
const THETA_13: f64 = 5.371_920_351_148_152;

// --- Matrix helpers (private) ---

/// Compute the 1-norm of a square matrix (maximum absolute column sum).
fn mat_norm1(a: &Array2<f64>) -> f64 {
    let n = a.ncols();
    (0..n)
        .map(|j| (0..a.nrows()).map(|i| a[[i, j]].abs()).sum::<f64>())
        .fold(0.0_f64, f64::max)
}

/// Solve AX = B via LU decomposition with partial pivoting.
///
/// Returns the solution X or [`IntegrateError::LinearSolveFailed`] if a
/// pivot is too small (singular or near-singular A).
fn lu_solve(a: &Array2<f64>, b: &Array2<f64>) -> Result<Array2<f64>, IntegrateError> {
    let n = a.nrows();
    let nrhs = b.ncols();
    debug_assert_eq!(a.ncols(), n);
    debug_assert_eq!(b.nrows(), n);

    // Build augmented matrix [A | B].
    let mut aug = Array2::<f64>::zeros((n, n + nrhs));
    for i in 0..n {
        for j in 0..n {
            aug[[i, j]] = a[[i, j]];
        }
        for j in 0..nrhs {
            aug[[i, n + j]] = b[[i, j]];
        }
    }

    // Forward elimination with partial pivoting.
    for col in 0..n {
        let mut max_val = aug[[col, col]].abs();
        let mut max_row = col;
        for row in (col + 1)..n {
            let val = aug[[row, col]].abs();
            if val > max_val {
                max_val = val;
                max_row = row;
            }
        }
        if max_row != col {
            for j in 0..(n + nrhs) {
                let tmp = aug[[col, j]];
                aug[[col, j]] = aug[[max_row, j]];
                aug[[max_row, j]] = tmp;
            }
        }
        let pivot = aug[[col, col]];
        if pivot.abs() < 1e-30 {
            return Err(IntegrateError::LinearSolveFailed);
        }
        for row in (col + 1)..n {
            let factor = aug[[row, col]] / pivot;
            for j in col..(n + nrhs) {
                let t = aug[[col, j]];
                aug[[row, j]] -= factor * t;
            }
        }
    }

    // Back substitution.
    let mut x = Array2::<f64>::zeros((n, nrhs));
    for col in (0..n).rev() {
        let diag = aug[[col, col]];
        if diag.abs() < 1e-30 {
            return Err(IntegrateError::LinearSolveFailed);
        }
        for rhs in 0..nrhs {
            let mut sum = aug[[col, n + rhs]];
            for j in (col + 1)..n {
                sum -= aug[[col, j]] * x[[j, rhs]];
            }
            x[[col, rhs]] = sum / diag;
        }
    }
    Ok(x)
}

/// Compute exp(A) via scaling-and-squaring with the (13,13) Padé approximant.
///
/// Reference: Higham, N. J. (2005). *The Scaling and Squaring Method for the
/// Matrix Exponential Revisited.* SIAM J. Matrix Anal. Appl., 26(4), 1179–1193.
///
/// # Errors
///
/// Returns [`IntegrateError::LinearSolveFailed`] if the Padé denominator
/// `V − U` is singular or near-singular.
fn matrix_exp(a: &Array2<f64>) -> Result<Array2<f64>, IntegrateError> {
    let n = a.nrows();
    let norm = mat_norm1(a);
    let s = if norm <= THETA_13 {
        0_usize
    } else {
        (norm / THETA_13).log2().ceil().max(0.0) as usize
    };
    let scale = 2.0_f64.powi(-(s as i32));

    // A_scaled = A / 2^s
    let a_s = a.mapv(|x| x * scale);

    // Powers: A², A⁴, A⁶, A⁸, A¹⁰, A¹²
    let a2 = a_s.dot(&a_s);
    let a4 = a2.dot(&a2);
    let a6 = a2.dot(&a4);
    let a8 = a4.dot(&a4);
    let a10 = a4.dot(&a6);
    let a12 = a6.dot(&a6);
    let eye = Array2::<f64>::eye(n);

    // U = A_s · (b₁I + b₃A² + b₅A⁴ + b₇A⁶ + b₉A⁸ + b₁₁A¹⁰ + b₁₃A¹²)
    let u_arg = eye.clone() * PADE13[1]
        + a2.clone() * PADE13[3]
        + a4.clone() * PADE13[5]
        + a6.clone() * PADE13[7]
        + a8.clone() * PADE13[9]
        + a10.clone() * PADE13[11]
        + a12.clone() * PADE13[13];
    let u = a_s.dot(&u_arg);

    // V = b₀I + b₂A² + b₄A⁴ + b₆A⁶ + b₈A⁸ + b₁₀A¹⁰ + b₁₂A¹²
    let v = eye * PADE13[0]
        + a2 * PADE13[2]
        + a4 * PADE13[4]
        + a6 * PADE13[6]
        + a8 * PADE13[8]
        + a10 * PADE13[10]
        + a12 * PADE13[12];

    // r = (V − U)⁻¹ (V + U)
    let n_mat = &v + &u;
    let d_mat = &v - &u;
    let mut r = lu_solve(&d_mat, &n_mat)?;

    // Repeated squaring.
    for _ in 0..s {
        r = r.dot(&r);
    }
    Ok(r)
}

/// Compute φ₁(A) = A⁻¹(exp(A) − I) via the augmented-matrix identity.
///
/// Constructs the 2D×2D matrix `M = [A I; 0 0]` and extracts the top-right
/// D×D block of exp(M), which equals φ₁(A). This avoids eigendecomposition
/// and handles the λ→0 limit stably.
///
/// # Errors
///
/// Returns [`IntegrateError::LinearSolveFailed`] if the internal matrix
/// exponential encounters a singular Padé denominator.
fn phi1_matrix(a: &Array2<f64>) -> Result<Array2<f64>, IntegrateError> {
    let d = a.nrows();
    let dim = 2 * d;
    let mut m = Array2::<f64>::zeros((dim, dim));
    for i in 0..d {
        for j in 0..d {
            m[[i, j]] = a[[i, j]];
        }
        m[[i, d + i]] = 1.0;
    }
    let exp_m = matrix_exp(&m)?;
    let mut phi1 = Array2::<f64>::zeros((d, d));
    for i in 0..d {
        for j in 0..d {
            phi1[[i, j]] = exp_m[[i, d + j]];
        }
    }
    Ok(phi1)
}

/// Build the Jacobian ∂f/∂y at the current state via forward finite differences.
///
/// Uses ε = √(machine_eps) ≈ 1.49×10⁻⁸. Requires D = 3N dynamics evaluations.
fn build_jacobian_fd(
    model: &dyn Dynamics,
    state: &OscillatorState,
    f_y: &[f64],
) -> Result<Array2<f64>, IntegrateError> {
    let n = state.phase.len();
    let d = 3 * n;
    let eps = f64::EPSILON.sqrt();

    let mut jac = Array2::<f64>::zeros((d, d));
    let y_base = state_to_vec(state);

    for j in 0..d {
        let mut y_p = y_base.clone();
        y_p[j] += eps;

        // Construct perturbed state (phase not wrapped — dynamics are 2π-periodic;
        // amplitude clamped to valid range).
        let pert = OscillatorState {
            phase: y_p[..n].to_vec(),
            amplitude: y_p[n..2 * n].iter().copied().map(clamp_amplitude).collect(),
            frequency: y_p[2 * n..].to_vec(),
            freq_band: state.freq_band.clone(),
        };
        let fp = model.compute_derivatives(&pert)?;

        for i in 0..n {
            jac[[i, j]] = (fp.dphase[i] - f_y[i]) / eps;
        }
        for i in 0..n {
            jac[[n + i, j]] = (fp.damplitude[i] - f_y[n + i]) / eps;
        }
        for i in 0..n {
            jac[[2 * n + i, j]] = (fp.dfrequency[i] - f_y[2 * n + i]) / eps;
        }
    }
    Ok(jac)
}

/// Flatten an [`OscillatorState`] into a `3N` vector `[phase, amplitude, frequency]`.
fn state_to_vec(state: &OscillatorState) -> Vec<f64> {
    let n = state.phase.len();
    let mut v = Vec::with_capacity(3 * n);
    v.extend_from_slice(&state.phase);
    v.extend_from_slice(&state.amplitude);
    v.extend_from_slice(&state.frequency);
    v
}

/// Unflatten a `3N` vector back into an [`OscillatorState`], applying phase
/// wrap, amplitude clamp, and carrying `freq_band` from `reference`.
fn vec_to_state(v: &[f64], reference: &OscillatorState) -> Result<OscillatorState, IntegrateError> {
    let n = reference.phase.len();
    let phase: Vec<f64> = v[..n].iter().copied().map(wrap_phase).collect();
    let amplitude: Vec<f64> = v[n..2 * n].iter().copied().map(clamp_amplitude).collect();
    let frequency = v[2 * n..].to_vec();
    let state = OscillatorState {
        phase,
        amplitude,
        frequency,
        freq_band: reference.freq_band.clone(),
    };
    check_finite(&state)?;
    Ok(state)
}

/// Matrix-vector product for raw slices: returns A·v.
fn mat_vec(a: &Array2<f64>, v: &[f64]) -> Vec<f64> {
    let n = a.nrows();
    let m = a.ncols();
    debug_assert_eq!(m, v.len());
    (0..n)
        .map(|i| (0..m).map(|j| a[[i, j]] * v[j]).sum::<f64>())
        .collect()
}

/// Arnoldi iteration with modified Gram-Schmidt.
///
/// Returns `(Q, H, beta, actual_m)` where:
/// - `Q` is D×m (Krylov basis vectors as columns),
/// - `H` is (m+1)×m (upper Hessenberg),
/// - `beta = ‖v‖`,
/// - `actual_m` is the number of Krylov vectors computed (may be < m on
///   lucky breakdown).
fn arnoldi(a: &Array2<f64>, v: &[f64], m: usize) -> (Array2<f64>, Array2<f64>, f64, usize) {
    let d = a.nrows();
    let m = m.min(d);
    let mut q = Array2::<f64>::zeros((d, m + 1));
    let mut h = Array2::<f64>::zeros((m + 1, m));

    let beta: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
    if beta < 1e-30 {
        return (q, h, beta, 0);
    }
    for i in 0..d {
        q[[i, 0]] = v[i] / beta;
    }

    let mut actual_m = m;
    for j in 0..m {
        // w = A · q[:, j]
        let mut w = vec![0.0_f64; d];
        for i in 0..d {
            let mut s = 0.0;
            for k in 0..d {
                s += a[[i, k]] * q[[k, j]];
            }
            w[i] = s;
        }
        // Modified Gram-Schmidt.
        for i in 0..=j {
            let mut hij = 0.0;
            for k in 0..d {
                hij += q[[k, i]] * w[k];
            }
            h[[i, j]] = hij;
            for k in 0..d {
                w[k] -= hij * q[[k, i]];
            }
        }
        let h_next: f64 = w.iter().map(|x| x * x).sum::<f64>().sqrt();
        h[[j + 1, j]] = h_next;
        if j < m - 1 {
            if h_next < 1e-14 {
                actual_m = j + 1;
                break;
            }
            for i in 0..d {
                q[[i, j + 1]] = w[i] / h_next;
            }
        }
    }
    (q, h, beta, actual_m)
}

/// Approximate exp(hA)v via Arnoldi–Krylov iteration.
///
/// Constructs a Krylov basis Q and Hessenberg H, then computes
/// `‖v‖ · Q_m · exp(h·H_m) · e₁`.
///
/// # Errors
///
/// Returns [`IntegrateError::LinearSolveFailed`] if the small matrix
/// exponential encounters a singular Padé denominator.
fn krylov_exp_vec(
    a: &Array2<f64>,
    h: f64,
    v: &[f64],
    m: usize,
) -> Result<Vec<f64>, IntegrateError> {
    let d = a.nrows();
    let (q, hh, beta, am) = arnoldi(a, v, m);
    if am == 0 {
        return Ok(vec![0.0; d]);
    }
    // Small matrix exponential: exp(h · H_m).
    let mut hm = Array2::<f64>::zeros((am, am));
    for i in 0..am {
        for j in 0..am {
            hm[[i, j]] = hh[[i, j]];
        }
    }
    let exp_hh = matrix_exp(&hm.mapv(|x| x * h))?;

    // e₁
    let mut result = vec![0.0_f64; d];
    for i in 0..d {
        let mut s = 0.0;
        for k in 0..am {
            s += q[[i, k]] * exp_hh[[k, 0]];
        }
        result[i] = beta * s;
    }
    Ok(result)
}

/// Approximate h·φ₁(hA)v via augmented Krylov.
///
/// Uses the Arnoldi relation and computes φ₁ on the small Hessenberg matrix
/// via the augmented-matrix identity.
///
/// # Errors
///
/// Returns [`IntegrateError::LinearSolveFailed`] if the internal matrix
/// exponential encounters a singular Padé denominator.
fn krylov_phi1_vec(
    a: &Array2<f64>,
    h: f64,
    v: &[f64],
    m: usize,
) -> Result<Vec<f64>, IntegrateError> {
    let d = a.nrows();
    let (q, hh, beta, am) = arnoldi(a, v, m);
    if am == 0 {
        return Ok(vec![0.0; d]);
    }
    let mut hm = Array2::<f64>::zeros((am, am));
    for i in 0..am {
        for j in 0..am {
            hm[[i, j]] = hh[[i, j]];
        }
    }
    let hhm = hm.mapv(|x| x * h);
    let phi1_hh = phi1_matrix(&hhm)?;

    let mut result = vec![0.0_f64; d];
    for i in 0..d {
        let mut s = 0.0;
        for k in 0..am {
            s += q[[i, k]] * phi1_hh[[k, 0]];
        }
        result[i] = h * beta * s;
    }
    Ok(result)
}

// ======================================================================
// ExponentialIntegrator
// ======================================================================

/// Exponential integrator for stiff oscillator dynamics.
///
/// Implements the exponential Euler method:
///
/// ```text
/// y_{n+1} = exp(hA) y_n + h φ₁(hA) g(y_n)
/// ```
///
/// where `A = ∂f/∂y` (Jacobian via forward finite differences) and
/// `g(y) = f(y) − Ay` is the nonlinear remainder.
///
/// Two computation paths:
///
/// 1. **Direct** (`dim ≤ max_direct_dim`): full matrix exponential via
///    Padé(13) scaling-and-squaring, φ₁ via augmented-matrix identity.
/// 2. **Krylov** (`dim > max_direct_dim` or `stiff_mode`): Arnoldi iteration
///    of rank `krylov_rank`, reducing cost from O(D³) to O(D·m²).
///
/// In `stiff_mode`, the Krylov dimension is adapted based on the estimated
/// 1-norm condition number of the Jacobian.
#[derive(Clone, Debug)]
pub struct ExponentialIntegrator {
    /// System dimensionality (3N).
    dim: usize,
    /// Krylov subspace rank.
    krylov_rank: usize,
    /// Threshold above which the Krylov path is used.
    max_direct_dim: usize,
    /// Whether adaptive stiff-mode Krylov is enabled.
    stiff_mode: bool,
    /// Condition-number threshold for adaptive Krylov dimension.
    stiff_cond_threshold: f64,
    /// Maximum Krylov dimension in stiff mode.
    max_krylov_stiff: usize,
}

impl ExponentialIntegrator {
    /// Create a new exponential integrator.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError::InvalidDim`] if `dim < 1`, or
    /// [`IntegrateError::InvalidKrylovRank`] if `krylov_rank < 2`.
    pub fn new(
        dim: usize,
        krylov_rank: usize,
        max_direct_dim: usize,
    ) -> Result<Self, IntegrateError> {
        if dim < 1 {
            return Err(IntegrateError::InvalidDim { dim });
        }
        if krylov_rank < 2 {
            return Err(IntegrateError::InvalidKrylovRank { rank: krylov_rank });
        }
        Ok(Self {
            dim,
            krylov_rank: krylov_rank.min(dim),
            max_direct_dim,
            stiff_mode: false,
            stiff_cond_threshold: 20.0,
            max_krylov_stiff: 48,
        })
    }

    /// Create a new exponential integrator with stiff-mode options.
    ///
    /// # Errors
    ///
    /// Same as [`new`](Self::new).
    pub fn with_stiff_mode(
        dim: usize,
        krylov_rank: usize,
        max_direct_dim: usize,
        stiff_mode: bool,
        stiff_cond_threshold: f64,
        max_krylov_stiff: usize,
    ) -> Result<Self, IntegrateError> {
        let mut s = Self::new(dim, krylov_rank, max_direct_dim)?;
        s.stiff_mode = stiff_mode;
        s.stiff_cond_threshold = stiff_cond_threshold;
        s.max_krylov_stiff = max_krylov_stiff;
        Ok(s)
    }

    /// System dimensionality.
    #[must_use]
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Krylov subspace rank.
    #[must_use]
    pub fn krylov_rank(&self) -> usize {
        self.krylov_rank
    }

    /// Whether the Krylov path is used for the current dimension.
    #[must_use]
    pub fn use_krylov(&self) -> bool {
        self.dim > self.max_direct_dim
    }

    /// Whether adaptive stiff-mode Krylov is enabled.
    #[must_use]
    pub fn stiff_mode(&self) -> bool {
        self.stiff_mode
    }

    /// Estimate the 1-norm condition number of `a` via LU.
    fn estimate_cond1(a: &Array2<f64>) -> f64 {
        let norm_a = mat_norm1(a);
        let n = a.nrows();
        let identity = Array2::<f64>::eye(n);
        match lu_solve(a, &identity) {
            Ok(a_inv) => norm_a * mat_norm1(&a_inv),
            Err(_) => f64::MAX,
        }
    }

    /// Select Krylov dimension adaptively based on Jacobian stiffness.
    fn adaptive_krylov_dim(&self, a: &Array2<f64>) -> usize {
        let cond = Self::estimate_cond1(a);
        let adaptive = (cond / self.stiff_cond_threshold.max(1e-8)) as usize + self.krylov_rank;
        adaptive
            .max(self.krylov_rank)
            .min(self.max_krylov_stiff.min(self.dim))
    }

    /// Perform one exponential integration step.
    fn exp_step(
        &self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
        jacobian: &Array2<f64>,
    ) -> Result<OscillatorState, IntegrateError> {
        let y = state_to_vec(state);
        let d = y.len();

        // f(y) and nonlinear remainder g(y) = f(y) − A·y.
        let deriv = model.compute_derivatives(state)?;
        let mut f_y = Vec::with_capacity(d);
        f_y.extend_from_slice(&deriv.dphase);
        f_y.extend_from_slice(&deriv.damplitude);
        f_y.extend_from_slice(&deriv.dfrequency);
        let ay = mat_vec(jacobian, &y);
        let g_y: Vec<f64> = (0..d).map(|i| f_y[i] - ay[i]).collect();

        let h = dt;
        let (exp_ha_y, phi1_g): (Vec<f64>, Vec<f64>) = if self.stiff_mode {
            let rank = self.adaptive_krylov_dim(jacobian);
            (
                krylov_exp_vec(jacobian, h, &y, rank)?,
                krylov_phi1_vec(jacobian, h, &g_y, rank)?,
            )
        } else if self.use_krylov() {
            (
                krylov_exp_vec(jacobian, h, &y, self.krylov_rank)?,
                krylov_phi1_vec(jacobian, h, &g_y, self.krylov_rank)?,
            )
        } else {
            let ha = jacobian.mapv(|x| x * h);
            let exp_ha = matrix_exp(&ha)?;
            let phi1_ha = phi1_matrix(&ha)?;
            let exp_y = mat_vec(&exp_ha, &y);
            let p1_g = mat_vec(&phi1_ha, &g_y);
            let p1_g_scaled: Vec<f64> = p1_g.iter().map(|x| h * x).collect();
            (exp_y, p1_g_scaled)
        };

        let y_new: Vec<f64> = (0..d).map(|i| exp_ha_y[i] + phi1_g[i]).collect();
        vec_to_state(&y_new, state)
    }

    /// Integrate for multiple steps with optional Jacobian caching.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError`] for invalid timestep, zero steps, or
    /// dynamics evaluation failure.
    pub fn integrate(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
        recompute_jacobian_every: usize,
    ) -> Result<(OscillatorState, Option<Vec<OscillatorState>>), IntegrateError> {
        if n_steps == 0 {
            return Err(IntegrateError::ZeroSteps);
        }
        validate_dt(dt)?;
        let d = 3 * state.phase.len();
        if d != self.dim {
            return Err(IntegrateError::InvalidDim { dim: d });
        }
        let recompute = recompute_jacobian_every.max(1);

        let mut current = state.clone();
        let mut trajectory = if record_trajectory {
            Some(Vec::with_capacity(n_steps))
        } else {
            None
        };
        let mut cached_j: Option<Array2<f64>> = None;

        for i in 0..n_steps {
            if cached_j.is_none() || i % recompute == 0 {
                let y = state_to_vec(&current);
                let d = y.len();
                let deriv = model.compute_derivatives(&current)?;
                let mut f_y = Vec::with_capacity(d);
                f_y.extend_from_slice(&deriv.dphase);
                f_y.extend_from_slice(&deriv.damplitude);
                f_y.extend_from_slice(&deriv.dfrequency);
                cached_j = Some(build_jacobian_fd(model, &current, &f_y)?);
            }
            let jac = cached_j.as_ref().unwrap();
            current = self.exp_step(model, &current, dt, jac)?;
            if let Some(ref mut traj) = trajectory {
                traj.push(current.clone());
            }
        }
        Ok((current, trajectory))
    }
}

impl Integrator for ExponentialIntegrator {
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError> {
        validate_dt(dt)?;
        let d = 3 * state.phase.len();
        if d != self.dim {
            return Err(IntegrateError::InvalidDim { dim: d });
        }
        let deriv = model.compute_derivatives(state)?;
        let mut f_y = Vec::with_capacity(d);
        f_y.extend_from_slice(&deriv.dphase);
        f_y.extend_from_slice(&deriv.damplitude);
        f_y.extend_from_slice(&deriv.dfrequency);
        let jac = build_jacobian_fd(model, state, &f_y)?;
        self.exp_step(model, state, dt, &jac)
    }
}

// ======================================================================
// MultiRateIntegrator
// ======================================================================

/// Integration method for the [`MultiRateIntegrator`] inner sub-steps.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MultiRateMethod {
    /// Classic fourth-order Runge–Kutta.
    RK4,
    /// Forward Euler.
    Euler,
}

/// Multi-rate ODE integrator for hierarchical oscillator systems.
///
/// Implements **uniform sub-stepping**: the outer timestep `dt` is divided
/// into `sub_steps` inner RK4 (or Euler) steps of size `dt / sub_steps`,
/// applied to every oscillator in the state (matching the PRINet 3.0
/// reference implementation). This resolves the fastest-varying partition
/// without the outer step accumulating excess error on slower components.
///
/// Band-aware scheduling (different sub-step counts per `freq_band`) is a
/// deferred capability, not implemented here — see Project Plan §8.3
/// amendment #18.
#[derive(Clone, Debug)]
pub struct MultiRateIntegrator {
    /// Number of sub-steps per outer step.
    sub_steps: usize,
    /// Inner integration method.
    method: MultiRateMethod,
}

impl MultiRateIntegrator {
    /// Create a new multi-rate integrator with the given sub-step count.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError::ZeroSteps`] if `sub_steps < 1`.
    pub fn new(sub_steps: usize) -> Result<Self, IntegrateError> {
        if sub_steps < 1 {
            return Err(IntegrateError::ZeroSteps);
        }
        Ok(Self {
            sub_steps,
            method: MultiRateMethod::RK4,
        })
    }

    /// Create a new multi-rate integrator with a specified inner method.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError::ZeroSteps`] if `sub_steps < 1`.
    pub fn with_method(sub_steps: usize, method: MultiRateMethod) -> Result<Self, IntegrateError> {
        if sub_steps < 1 {
            return Err(IntegrateError::ZeroSteps);
        }
        Ok(Self { sub_steps, method })
    }

    /// Number of sub-steps per outer step.
    #[must_use]
    pub fn sub_steps(&self) -> usize {
        self.sub_steps
    }

    /// Inner integration method.
    #[must_use]
    pub fn method(&self) -> MultiRateMethod {
        self.method
    }

    /// Integrate for multiple outer steps with sub-stepping.
    ///
    /// # Errors
    ///
    /// Returns [`IntegrateError`] for zero steps, invalid timestep, or
    /// dynamics evaluation failure.
    pub fn integrate(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
    ) -> Result<(OscillatorState, Option<Vec<OscillatorState>>), IntegrateError> {
        if n_steps == 0 {
            return Err(IntegrateError::ZeroSteps);
        }
        validate_dt(dt)?;
        let mut current = state.clone();
        let mut trajectory = if record_trajectory {
            Some(Vec::with_capacity(n_steps))
        } else {
            None
        };
        for _ in 0..n_steps {
            current = self.step(model, &current, dt)?;
            if let Some(ref mut traj) = trajectory {
                traj.push(current.clone());
            }
        }
        Ok((current, trajectory))
    }
}

impl Integrator for MultiRateIntegrator {
    fn step(
        &mut self,
        model: &dyn Dynamics,
        state: &OscillatorState,
        dt: f64,
    ) -> Result<OscillatorState, IntegrateError> {
        validate_dt(dt)?;
        let inner_dt = dt / (self.sub_steps as f64);
        let mut current = state.clone();
        match self.method {
            MultiRateMethod::RK4 => {
                let mut rk4 = RK4Integrator::with_capacity(state.phase.len());
                for _ in 0..self.sub_steps {
                    current = rk4.step(model, &current, inner_dt)?;
                }
            }
            MultiRateMethod::Euler => {
                let mut euler = EulerIntegrator::with_capacity(state.phase.len());
                for _ in 0..self.sub_steps {
                    current = euler.step(model, &current, inner_dt)?;
                }
            }
        }
        Ok(current)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    use proptest::prelude::*;
    use std::f64::consts::FRAC_PI_2;

    use crate::coupling::CouplingMode;
    use crate::models::{KuramotoOscillator, StuartLandauOscillator};
    use crate::state::{OscillatorState, TAU};

    /// Single uncoupled oscillator (K=0, λ=0, γ=0): dφ/dt = ω, dr/dt = 0, dω/dt = 0.
    /// The frequency `omega` is carried by the state, not the model.
    fn uncoupled(n: usize, _omega: f64) -> KuramotoOscillator {
        KuramotoOscillator::new(n, 0.0, 0.0, 0.0, crate::coupling::CouplingMode::MeanField).unwrap()
    }

    fn make_state(n: usize, phase: f64, amp: f64, freq: f64) -> OscillatorState {
        OscillatorState::new(vec![phase; n], vec![amp; n], vec![freq; n], None).unwrap()
    }

    // ------------------------------------------------------------------
    // Euler
    // ------------------------------------------------------------------

    #[test]
    fn euler_single_oscillator_constant_frequency() {
        let model = uncoupled(1, 2.0);
        let state = make_state(1, 0.0, 1.0, 2.0);
        let mut euler = EulerIntegrator::new();
        let result = euler.step(&model, &state, 0.1).unwrap();
        // φ = wrap(0 + 0.1·2) = 0.2; r = 1.0; ω = 2.0
        assert_relative_eq!(result.phase[0], 0.2, epsilon = 1e-12);
        assert_relative_eq!(result.amplitude[0], 1.0, epsilon = 1e-12);
        assert_relative_eq!(result.frequency[0], 2.0, epsilon = 1e-12);
    }

    #[test]
    fn euler_phase_wraps_to_0_2pi() {
        let model = uncoupled(1, 10.0);
        let state = make_state(1, 6.0, 1.0, 10.0);
        let mut euler = EulerIntegrator::new();
        let result = euler.step(&model, &state, 1.0).unwrap();
        // φ = wrap(6 + 10) = wrap(16) = 16 - 2π ≈ 9.716...
        assert!(result.phase[0] >= 0.0 && result.phase[0] < TAU);
        assert_relative_eq!(result.phase[0], 16.0 % TAU, epsilon = 1e-12);
    }

    #[test]
    fn euler_rejects_invalid_dt() {
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut euler = EulerIntegrator::new();
        assert!(matches!(
            euler.step(&model, &state, 0.0).unwrap_err(),
            IntegrateError::InvalidTimestep { dt: 0.0 }
        ));
        assert!(matches!(
            euler.step(&model, &state, -1.0).unwrap_err(),
            IntegrateError::InvalidTimestep { dt: -1.0 }
        ));
        assert!(matches!(
            euler.step(&model, &state, f64::NAN).unwrap_err(),
            IntegrateError::InvalidTimestep { .. }
        ));
        assert!(matches!(
            euler.step(&model, &state, f64::INFINITY).unwrap_err(),
            IntegrateError::InvalidTimestep { .. }
        ));
    }

    // ------------------------------------------------------------------
    // RK4
    // ------------------------------------------------------------------

    #[test]
    fn rk4_single_oscillator_exact_for_linear() {
        // For dφ/dt = ω (constant), RK4 is exact: φ = φ0 + dt·ω.
        let model = uncoupled(1, 3.0);
        let state = make_state(1, 0.5, 1.0, 3.0);
        let mut rk4 = RK4Integrator::new();
        let result = rk4.step(&model, &state, 0.1).unwrap();
        assert_relative_eq!(result.phase[0], 0.5 + 0.1 * 3.0, epsilon = 1e-12);
        assert_relative_eq!(result.amplitude[0], 1.0, epsilon = 1e-12);
        assert_relative_eq!(result.frequency[0], 3.0, epsilon = 1e-12);
    }

    #[test]
    fn rk4_matches_euler_for_constant_derivative() {
        // When the derivative is constant (uncoupled, no amplitude decay),
        // RK4 and Euler produce identical results.
        let model = uncoupled(2, 1.5);
        let state = make_state(2, 0.3, 1.0, 1.5);
        let mut euler = EulerIntegrator::new();
        let mut rk4 = RK4Integrator::new();
        let se = euler.step(&model, &state, 0.05).unwrap();
        let sr = rk4.step(&model, &state, 0.05).unwrap();
        for i in 0..2 {
            assert_relative_eq!(se.phase[i], sr.phase[i], epsilon = 1e-14);
            assert_relative_eq!(se.amplitude[i], sr.amplitude[i], epsilon = 1e-14);
            assert_relative_eq!(se.frequency[i], sr.frequency[i], epsilon = 1e-14);
        }
    }

    #[test]
    fn rk4_order_h4_convergence() {
        // For a nonlinear ODE, RK4 error should scale as h^4.
        // We use a single oscillator with amplitude decay: dr/dt = -λ·r.
        // The exact solution is r(t) = r0·exp(-λ·t).
        // RK4 error at time T with step h: |r_h - r_exact| ∝ h^4.
        let model = KuramotoOscillator::new(
            1,
            0.0,
            1.0, // decay_rate λ = 1
            0.0,
            crate::coupling::CouplingMode::MeanField,
        )
        .unwrap();
        let r0 = 1.0_f64;
        let state = make_state(1, 0.0, r0, 0.0);
        let t_final = 0.1_f64;
        let r_exact = r0 * (-t_final).exp();

        let h_vals = [0.1, 0.05, 0.025];
        let mut errors = [0.0_f64; 3];
        for (idx, &h) in h_vals.iter().enumerate() {
            let n_steps = (t_final / h).round() as usize;
            let mut rk4 = RK4Integrator::new();
            let (final_state, _) =
                integrate_fixed(&mut rk4, &model, &state, n_steps, h, false).unwrap();
            errors[idx] = (final_state.amplitude[0] - r_exact).abs();
        }
        // error ratio should be ≈ 2^4 = 16 (coarse/fine).
        let ratio1 = errors[0] / errors[1];
        let ratio2 = errors[1] / errors[2];
        assert!(
            ratio1 > 8.0 && ratio1 < 32.0,
            "RK4 order broken: ratio1 = {ratio1}, errors = {errors:?}"
        );
        assert!(
            ratio2 > 8.0 && ratio2 < 32.0,
            "RK4 order broken: ratio2 = {ratio2}, errors = {errors:?}"
        );
    }

    #[test]
    fn rk4_freq_band_preserved() {
        let model = uncoupled(3, 1.0);
        let state = OscillatorState::new(
            vec![0.0, 0.1, 0.2],
            vec![1.0; 3],
            vec![1.0; 3],
            Some(vec![0, 1, 2]),
        )
        .unwrap();
        let mut rk4 = RK4Integrator::new();
        let result = rk4.step(&model, &state, 0.01).unwrap();
        assert_eq!(result.freq_band, Some(vec![0, 1, 2]));
    }

    #[test]
    fn rk4_rejects_invalid_dt() {
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut rk4 = RK4Integrator::new();
        assert!(rk4.step(&model, &state, 0.0).is_err());
        assert!(rk4.step(&model, &state, -0.01).is_err());
    }

    // ------------------------------------------------------------------
    // RK45 adaptive
    // ------------------------------------------------------------------

    #[test]
    fn rk45_tolerance_property() {
        // Tighter tolerance → smaller error. We integrate a nonlinear ODE
        // (amplitude decay dr/dt = -λ·r) and compare against the exact
        // solution r(t) = r0·exp(-λ·t).
        let model =
            KuramotoOscillator::new(1, 0.0, 1.0, 0.0, crate::coupling::CouplingMode::MeanField)
                .unwrap();
        let state = make_state(1, 0.0, 1.0, 0.0);
        let t_final = 0.5_f64;
        let r_exact = (-t_final).exp();

        let mut rk45_loose = RK45Integrator::new(1e-3, 1e-5, 10_000).unwrap();
        let res_loose = rk45_loose
            .integrate_adaptive(&model, &state, t_final, 0.01, false)
            .unwrap();
        let err_loose = (res_loose.final_state.amplitude[0] - r_exact).abs();

        let mut rk45_tight = RK45Integrator::new(1e-8, 1e-10, 10_000).unwrap();
        let res_tight = rk45_tight
            .integrate_adaptive(&model, &state, t_final, 0.01, false)
            .unwrap();
        let err_tight = (res_tight.final_state.amplitude[0] - r_exact).abs();

        assert!(
            err_tight < err_loose,
            "tighter tolerance should reduce error: loose={err_loose}, tight={err_tight}"
        );
        // Global error for adaptive DOPRI5 is O(rtol·t_span/h) ≈ O(rtol·n_steps).
        // With rtol=1e-8 and ~50 steps, expect err < ~1e-5.
        assert!(
            err_tight < 1e-4,
            "tight tolerance error should be small: {err_tight}"
        );
        assert!(
            res_tight.accepted_steps >= res_loose.accepted_steps,
            "tighter tolerance should need at least as many steps"
        );
    }

    #[test]
    fn rk45_step_matches_fixed_dopri5() {
        // The Integrator::step path should match one step of the adaptive path
        // when the adaptive path accepts the full step in one go (loose tolerance).
        let model =
            KuramotoOscillator::new(2, 1.0, 0.1, 0.01, crate::coupling::CouplingMode::MeanField)
                .unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
        let mut rk45_step = RK45Integrator::new(1e-6, 1e-8, 100).unwrap();
        let s1 = rk45_step.step(&model, &state, 0.01).unwrap();

        // Adaptive with a loose tolerance should accept the single step.
        let mut rk45_adapt = RK45Integrator::new(1e-2, 1e-4, 100).unwrap();
        let res = rk45_adapt
            .integrate_adaptive(&model, &state, 0.01, 0.01, false)
            .unwrap();
        assert_eq!(
            res.accepted_steps, 1,
            "loose tolerance should accept one step"
        );
        for i in 0..2 {
            assert_relative_eq!(s1.phase[i], res.final_state.phase[i], epsilon = 1e-14);
            assert_relative_eq!(
                s1.amplitude[i],
                res.final_state.amplitude[i],
                epsilon = 1e-14
            );
        }
    }

    #[test]
    fn rk45_trajectory_recorded() {
        let model = uncoupled(2, 1.0);
        let state = make_state(2, 0.0, 1.0, 1.0);
        let mut rk45 = RK45Integrator::new(1e-6, 1e-8, 1000).unwrap();
        let res = rk45
            .integrate_adaptive(&model, &state, 0.1, 0.01, true)
            .unwrap();
        assert!(res.trajectory.is_some());
        assert!(!res.trajectory.as_ref().unwrap().is_empty());
        assert_eq!(res.trajectory.as_ref().unwrap().len(), res.accepted_steps);
    }

    #[test]
    fn rk45_rejects_invalid_tolerances() {
        // WP008-F5: assert the specific InvalidTolerance variant, not just is_err().
        assert!(matches!(
            RK45Integrator::new(0.0, 1e-8, 100).unwrap_err(),
            IntegrateError::InvalidTolerance {
                param: "rtol",
                value: 0.0
            }
        ));
        assert!(matches!(
            RK45Integrator::new(1e-6, f64::NAN, 100).unwrap_err(),
            IntegrateError::InvalidTolerance { param: "atol", .. }
        ));
        assert!(matches!(
            RK45Integrator::new(1e-6, 1e-8, 0).unwrap_err(),
            IntegrateError::ZeroSteps
        ));
        // Negative atol is also invalid.
        assert!(matches!(
            RK45Integrator::new(1e-6, -1e-8, 100).unwrap_err(),
            IntegrateError::InvalidTolerance { param: "atol", .. }
        ));
    }

    #[test]
    fn rk45_tolerance_not_met_error() {
        // A very small step budget with a tight tolerance on a long span.
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut rk45 = RK45Integrator::new(1e-12, 1e-14, 5).unwrap();
        let err = rk45.integrate_adaptive(&model, &state, 1.0, 0.001, false);
        assert!(matches!(err, Err(IntegrateError::ToleranceNotMet { .. })));
    }

    // ------------------------------------------------------------------
    // WP008-F1: FSAL cache invalidation on integrator reuse
    // ------------------------------------------------------------------

    #[test]
    fn rk45_fsal_cache_invalidated_on_reuse() {
        // Reusing an RK45Integrator across two integrate_adaptive calls with
        // different initial states (same n) must produce identical results to
        // fresh integrators. Before the fix, the stale k7 from the first call
        // was used as k1 for the first step of the second call.
        let model =
            KuramotoOscillator::new(2, 1.0, 0.1, 0.01, crate::coupling::CouplingMode::MeanField)
                .unwrap();
        let state_a =
            OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
        let state_b =
            OscillatorState::new(vec![1.2, 0.3], vec![0.9, 1.5], vec![2.0, 1.0], None).unwrap();
        let t_span = 0.05_f64;
        let dt_init = 0.01_f64;

        // Reused integrator: two sequential calls with different states.
        let mut reused = RK45Integrator::new(1e-8, 1e-10, 10_000).unwrap();
        let res_reused_a = reused
            .integrate_adaptive(&model, &state_a, t_span, dt_init, false)
            .unwrap();
        let res_reused_b = reused
            .integrate_adaptive(&model, &state_b, t_span, dt_init, false)
            .unwrap();

        // Fresh integrators: one per call.
        let mut fresh_a = RK45Integrator::new(1e-8, 1e-10, 10_000).unwrap();
        let res_fresh_a = fresh_a
            .integrate_adaptive(&model, &state_a, t_span, dt_init, false)
            .unwrap();
        let mut fresh_b = RK45Integrator::new(1e-8, 1e-10, 10_000).unwrap();
        let res_fresh_b = fresh_b
            .integrate_adaptive(&model, &state_b, t_span, dt_init, false)
            .unwrap();

        // Reused results must match fresh results bit-for-bit.
        for i in 0..2 {
            assert_relative_eq!(
                res_reused_a.final_state.phase[i],
                res_fresh_a.final_state.phase[i],
                epsilon = 0.0
            );
            assert_relative_eq!(
                res_reused_a.final_state.amplitude[i],
                res_fresh_a.final_state.amplitude[i],
                epsilon = 0.0
            );
            assert_relative_eq!(
                res_reused_a.final_state.frequency[i],
                res_fresh_a.final_state.frequency[i],
                epsilon = 0.0
            );
            assert_relative_eq!(
                res_reused_b.final_state.phase[i],
                res_fresh_b.final_state.phase[i],
                epsilon = 0.0
            );
            assert_relative_eq!(
                res_reused_b.final_state.amplitude[i],
                res_fresh_b.final_state.amplitude[i],
                epsilon = 0.0
            );
            assert_relative_eq!(
                res_reused_b.final_state.frequency[i],
                res_fresh_b.final_state.frequency[i],
                epsilon = 0.0
            );
        }
        assert_eq!(res_reused_b.accepted_steps, res_fresh_b.accepted_steps);
        assert_eq!(res_reused_b.rejected_steps, res_fresh_b.rejected_steps);
    }

    // ------------------------------------------------------------------
    // WP008-F2: NonFiniteValue error path under strict-checks
    // ------------------------------------------------------------------

    /// A dynamics model that returns non-finite derivatives, bypassing
    /// `StateDerivatives::new` guards by constructing the struct directly.
    /// Used to exercise the `IntegrateError::NonFiniteValue` path in
    /// `check_finite` under `strict-checks`.
    #[cfg(feature = "strict-checks")]
    struct NanDynamics;

    #[cfg(feature = "strict-checks")]
    impl Dynamics for NanDynamics {
        fn compute_derivatives(
            &self,
            state: &OscillatorState,
        ) -> Result<StateDerivatives, StateError> {
            let n = state.phase.len();
            Ok(StateDerivatives {
                dphase: vec![f64::NAN; n],
                damplitude: vec![0.0; n],
                dfrequency: vec![0.0; n],
            })
        }
    }

    #[cfg(feature = "strict-checks")]
    #[test]
    fn strict_check_non_finite_value_error() {
        // WP008-F2: under strict-checks, a non-finite phase produced by the
        // integrator must be caught by check_finite and returned as
        // IntegrateError::NonFiniteValue.
        let model = NanDynamics;
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut euler = EulerIntegrator::new();
        let err = euler.step(&model, &state, 0.01).unwrap_err();
        assert!(matches!(
            err,
            IntegrateError::NonFiniteValue {
                field: "phase",
                index: 0,
                ..
            }
        ));
    }

    #[cfg(feature = "strict-checks")]
    #[test]
    fn strict_check_non_finite_value_rk4() {
        // WP008-F2: same path via RK4.
        let model = NanDynamics;
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut rk4 = RK4Integrator::new();
        let err = rk4.step(&model, &state, 0.01).unwrap_err();
        assert!(matches!(
            err,
            IntegrateError::NonFiniteValue {
                field: "phase",
                index: 0,
                ..
            }
        ));
    }

    // ------------------------------------------------------------------
    // integrate_fixed driver
    // ------------------------------------------------------------------

    #[test]
    fn integrate_fixed_rejects_zero_steps() {
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut euler = EulerIntegrator::new();
        assert!(matches!(
            integrate_fixed(&mut euler, &model, &state, 0, 0.01, false).unwrap_err(),
            IntegrateError::ZeroSteps
        ));
    }

    #[test]
    fn integrate_fixed_records_trajectory() {
        let model = uncoupled(2, 1.0);
        let state = make_state(2, 0.0, 1.0, 1.0);
        let mut rk4 = RK4Integrator::new();
        let (final_state, traj) = integrate_fixed(&mut rk4, &model, &state, 5, 0.01, true).unwrap();
        assert!(traj.is_some());
        assert_eq!(traj.as_ref().unwrap().len(), 5);
        // Final state equals last trajectory entry.
        assert_eq!(final_state, traj.as_ref().unwrap()[4]);
    }

    #[test]
    fn integrate_fixed_no_trajectory() {
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut euler = EulerIntegrator::new();
        let (_, traj) = integrate_fixed(&mut euler, &model, &state, 3, 0.01, false).unwrap();
        assert!(traj.is_none());
    }

    // ------------------------------------------------------------------
    // Invariants (property tests)
    // ------------------------------------------------------------------

    proptest! {
        #[test]
        fn prop_phase_in_range_after_rk4_step(
            phase in 0.0f64..TAU,
            omega in -5.0f64..5.0f64,
            dt in 0.001f64..0.1,
        ) {
            let model = uncoupled(1, omega);
            let state = make_state(1, phase, 1.0, omega);
            let mut rk4 = RK4Integrator::new();
            let result = rk4.step(&model, &state, dt)?;
            prop_assert!(result.phase[0] >= 0.0 && result.phase[0] < TAU);
            prop_assert!(result.amplitude[0] >= 0.0 && result.amplitude[0] <= 10.0);
        }

        #[test]
        fn prop_rk4_order_h4(
            h in 0.02f64..0.08,
        ) {
            // Amplitude decay: r(t) = r0·exp(-λ·t). Error ∝ h^4.
            let model = KuramotoOscillator::new(1, 0.0, 1.0, 0.0, crate::coupling::CouplingMode::MeanField).unwrap();
            let state = make_state(1, 0.0, 1.0, 0.0);
            // Use a multiple of h as t_final so the step count is exact.
            let n_h = 4_usize;
            let t_final = n_h as f64 * h;
            let r_exact = (-t_final).exp();

            let mut rk4_h = RK4Integrator::new();
            let (s_h, _) = integrate_fixed(&mut rk4_h, &model, &state, n_h, h, false)?;
            let err_h = (s_h.amplitude[0] - r_exact).abs();

            let h2 = h / 2.0;
            let n_h2 = 2 * n_h;
            let mut rk4_h2 = RK4Integrator::new();
            let (s_h2, _) = integrate_fixed(&mut rk4_h2, &model, &state, n_h2, h2, false)?;
            let err_h2 = (s_h2.amplitude[0] - r_exact).abs();

            // Error ratio should be near 16 (2^4). Allow [8, 40] for rounding.
            if err_h2 > 1e-15 {
                let ratio = err_h / err_h2;
                prop_assert!(ratio > 8.0 && ratio < 40.0, "ratio = {ratio}, err_h = {err_h}, err_h2 = {err_h2}");
            }
        }

        #[test]
        fn prop_rk45_error_within_tolerance(
            rtol in 1e-6f64..1e-3,
        ) {
            let model = KuramotoOscillator::new(1, 0.0, 1.0, 0.0, crate::coupling::CouplingMode::MeanField).unwrap();
            let state = make_state(1, 0.0, 1.0, 0.0);
            let t_final = 0.5f64;
            let r_exact = (-t_final).exp();
            let mut rk45 = RK45Integrator::new(rtol, rtol * 1e-2, 10_000)?;
            let res = rk45.integrate_adaptive(&model, &state, t_final, 0.01, false)?;
            let err = (res.final_state.amplitude[0] - r_exact).abs();
            // Global error for adaptive DOPRI5 scales as O(rtol * n_steps).
            // With t_final=0.5 and typical steps ~50-500, allow err < 1000*rtol.
            prop_assert!(err < 1000.0 * rtol, "err = {err}, rtol = {rtol}");
        }
    }

    #[test]
    fn euler_with_capacity_matches_new() {
        let model = uncoupled(2, 1.0);
        let state = make_state(2, 0.0, 1.0, 1.0);
        let mut a = EulerIntegrator::new();
        let mut b = EulerIntegrator::with_capacity(2);
        let sa = a.step(&model, &state, 0.01).unwrap();
        let sb = b.step(&model, &state, 0.01).unwrap();
        assert_eq!(sa, sb);
    }

    #[test]
    fn rk4_with_capacity_matches_new() {
        let model = uncoupled(2, 1.0);
        let state = make_state(2, 0.0, 1.0, 1.0);
        let mut a = RK4Integrator::new();
        let mut b = RK4Integrator::with_capacity(2);
        let sa = a.step(&model, &state, 0.01).unwrap();
        let sb = b.step(&model, &state, 0.01).unwrap();
        assert_eq!(sa, sb);
    }

    #[test]
    fn rk45_getters() {
        let rk45 = RK45Integrator::new(1e-6, 1e-8, 500).unwrap();
        assert_relative_eq!(rk45.rtol(), 1e-6);
        assert_relative_eq!(rk45.atol(), 1e-8);
        assert_eq!(rk45.max_steps(), 500);
    }

    #[test]
    fn euler_amplitude_clamped() {
        // Large negative amplitude derivative should clamp to AMPLITUDE_MIN.
        let model =
            KuramotoOscillator::new(1, 0.0, 100.0, 0.0, crate::coupling::CouplingMode::MeanField)
                .unwrap();
        let state = make_state(1, 0.0, 0.001, 0.0);
        let mut euler = EulerIntegrator::new();
        let result = euler.step(&model, &state, 1.0).unwrap();
        assert!(result.amplitude[0] >= 1e-6);
    }

    #[test]
    fn rk45_step_size_grows_on_easy_step() {
        // For a trivial ODE, the step should grow after acceptance.
        // We use a large t_span so the final dt is not clamped to 0 by the
        // remaining-time clamp.
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut rk45 = RK45Integrator::new(1e-6, 1e-8, 100).unwrap();
        let res = rk45
            .integrate_adaptive(&model, &state, 10.0, 0.001, false)
            .unwrap();
        assert!(
            res.final_dt > 0.001,
            "step should grow: final_dt = {}",
            res.final_dt
        );
        assert_eq!(res.rejected_steps, 0);
    }

    /// Dummy test to silence unused import of FRAC_PI_2 if not referenced elsewhere.
    #[test]
    fn _const_pi_half_used() {
        assert_relative_eq!(FRAC_PI_2, std::f64::consts::FRAC_PI_2);
    }

    // ------------------------------------------------------------------
    // WP-012: Matrix operations
    // ------------------------------------------------------------------

    #[test]
    fn matrix_exp_zero_is_identity() {
        let z = Array2::<f64>::zeros((4, 4));
        let e = matrix_exp(&z).unwrap();
        for i in 0..4 {
            for j in 0..4 {
                let expected = if i == j { 1.0 } else { 0.0 };
                assert_relative_eq!(e[[i, j]], expected, epsilon = 1e-12);
            }
        }
    }

    #[test]
    fn phi1_zero_is_identity() {
        let z = Array2::<f64>::zeros((3, 3));
        let p = phi1_matrix(&z).unwrap();
        for i in 0..3 {
            for j in 0..3 {
                let expected = if i == j { 1.0 } else { 0.0 };
                assert_relative_eq!(p[[i, j]], expected, epsilon = 1e-10);
            }
        }
    }

    #[test]
    fn matrix_exp_diagonal() {
        // exp(diag(a,b)) = diag(exp(a), exp(b))
        let mut d = Array2::<f64>::zeros((2, 2));
        d[[0, 0]] = 1.0;
        d[[1, 1]] = -0.5;
        let e = matrix_exp(&d).unwrap();
        assert_relative_eq!(e[[0, 0]], 1.0_f64.exp(), epsilon = 1e-10);
        assert_relative_eq!(e[[1, 1]], (-0.5_f64).exp(), epsilon = 1e-10);
        assert_relative_eq!(e[[0, 1]], 0.0, epsilon = 1e-12);
        assert_relative_eq!(e[[1, 0]], 0.0, epsilon = 1e-12);
    }

    #[test]
    fn krylov_exp_vec_matches_direct_small() {
        // For a small system, Krylov exp(hA)v should match direct.
        let d = 6;
        let mut a = Array2::<f64>::zeros((d, d));
        // Simple diagonal-dominant matrix.
        for i in 0..d {
            a[[i, i]] = -(i as f64 + 1.0) * 0.1;
            if i + 1 < d {
                a[[i, i + 1]] = 0.05;
            }
        }
        let v: Vec<f64> = (0..d).map(|i| (i as f64 + 1.0) * 0.1).collect();
        let h = 0.01;

        // Direct.
        let ha = a.mapv(|x| x * h);
        let exp_ha = matrix_exp(&ha).unwrap();
        let direct = mat_vec(&exp_ha, &v);

        // Krylov.
        let krylov = krylov_exp_vec(&a, h, &v, d).unwrap();

        for i in 0..d {
            assert_relative_eq!(direct[i], krylov[i], epsilon = 1e-6);
        }
    }

    // ------------------------------------------------------------------
    // WP-012: ExponentialIntegrator
    // ------------------------------------------------------------------

    #[test]
    fn exp_integrator_init_valid() {
        let ei = ExponentialIntegrator::new(30, 16, 150).unwrap();
        assert_eq!(ei.dim(), 30);
        assert_eq!(ei.krylov_rank(), 16);
        assert!(!ei.use_krylov());
    }

    #[test]
    fn exp_integrator_invalid_dim() {
        assert!(matches!(
            ExponentialIntegrator::new(0, 16, 150).unwrap_err(),
            IntegrateError::InvalidDim { dim: 0 }
        ));
    }

    #[test]
    fn exp_integrator_invalid_krylov_rank() {
        assert!(matches!(
            ExponentialIntegrator::new(30, 1, 150).unwrap_err(),
            IntegrateError::InvalidKrylovRank { rank: 1 }
        ));
    }

    #[test]
    fn exp_integrator_step_finite_kuramoto() {
        let n = 5;
        let model = KuramotoOscillator::new(n, 2.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5, 2.0],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5, 1.2],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        let result = ei.step(&model, &state, 0.01).unwrap();
        for i in 0..n {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
            assert!(result.frequency[i].is_finite());
            assert!(result.phase[i] >= 0.0 && result.phase[i] < TAU);
            assert!(result.amplitude[i] >= 1e-6);
        }
    }

    #[test]
    fn exp_integrator_step_finite_stuart_landau() {
        let n = 4;
        let model =
            StuartLandauOscillator::new(n, 1.0, 1.0, CouplingMode::Full { matrix: None }).unwrap();
        let state =
            OscillatorState::new(vec![0.0, 0.2, 0.4, 0.6], vec![1.0; n], vec![1.0; n], None)
                .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        let result = ei.step(&model, &state, 0.01).unwrap();
        for i in 0..n {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
        }
    }

    #[test]
    fn exp_integrator_integrate_trajectory() {
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        let (final_state, traj) = ei.integrate(&model, &state, 5, 0.01, true, 1).unwrap();
        assert!(traj.is_some());
        assert_eq!(traj.as_ref().unwrap().len(), 5);
        for i in 0..n {
            assert!(final_state.phase[i].is_finite());
        }
    }

    #[test]
    fn exp_integrator_integrate_no_trajectory() {
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        let (_, traj) = ei.integrate(&model, &state, 3, 0.01, false, 1).unwrap();
        assert!(traj.is_none());
    }

    #[test]
    fn exp_integrator_recompute_jacobian() {
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        let (final_state, _) = ei.integrate(&model, &state, 10, 0.01, false, 5).unwrap();
        for i in 0..n {
            assert!(final_state.phase[i].is_finite());
            assert!(final_state.amplitude[i].is_finite());
        }
    }

    #[test]
    fn exp_integrator_rejects_invalid_dt() {
        let n = 2;
        let model = uncoupled(n, 1.0);
        let state = make_state(n, 0.0, 1.0, 1.0);
        let mut ei = ExponentialIntegrator::new(3 * n, 16, 150).unwrap();
        assert!(matches!(
            ei.step(&model, &state, 0.0).unwrap_err(),
            IntegrateError::InvalidTimestep { .. }
        ));
        assert!(matches!(
            ei.step(&model, &state, -0.01).unwrap_err(),
            IntegrateError::InvalidTimestep { .. }
        ));
    }

    #[test]
    fn exp_integrator_stiff_mode() {
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::with_stiff_mode(3 * n, 4, 0, true, 20.0, 48).unwrap();
        assert!(ei.stiff_mode());
        let result = ei.step(&model, &state, 0.01).unwrap();
        for i in 0..n {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
        }
    }

    #[test]
    fn exp_integrator_krylov_path() {
        // Force Krylov by setting max_direct_dim = 0.
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut ei = ExponentialIntegrator::new(3 * n, 8, 0).unwrap();
        assert!(ei.use_krylov());
        let result = ei.step(&model, &state, 0.01).unwrap();
        for i in 0..n {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
        }
    }

    // ------------------------------------------------------------------
    // WP-012: MultiRateIntegrator
    // ------------------------------------------------------------------

    #[test]
    fn multi_rate_init_valid() {
        let mri = MultiRateIntegrator::new(10).unwrap();
        assert_eq!(mri.sub_steps(), 10);
        assert_eq!(mri.method(), MultiRateMethod::RK4);
    }

    #[test]
    fn multi_rate_init_zero_substeps() {
        assert!(matches!(
            MultiRateIntegrator::new(0).unwrap_err(),
            IntegrateError::ZeroSteps
        ));
    }

    #[test]
    fn multi_rate_substeps_1_matches_rk4() {
        // With sub_steps=1, MultiRate should match RK4 exactly.
        let model = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
        let mut mri = MultiRateIntegrator::new(1).unwrap();
        let mut rk4 = RK4Integrator::new();
        let s_mri = mri.step(&model, &state, 0.01).unwrap();
        let s_rk4 = rk4.step(&model, &state, 0.01).unwrap();
        for i in 0..2 {
            assert_relative_eq!(s_mri.phase[i], s_rk4.phase[i], epsilon = 1e-14);
            assert_relative_eq!(s_mri.amplitude[i], s_rk4.amplitude[i], epsilon = 1e-14);
            assert_relative_eq!(s_mri.frequency[i], s_rk4.frequency[i], epsilon = 1e-14);
        }
    }

    #[test]
    fn multi_rate_output_shape() {
        let n = 8;
        let model = KuramotoOscillator::new(n, 2.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(vec![0.1; n], vec![1.0; n], vec![1.0; n], None).unwrap();
        let mut mri = MultiRateIntegrator::new(5).unwrap();
        let result = mri.step(&model, &state, 0.001).unwrap();
        assert_eq!(result.phase.len(), n);
        assert_eq!(result.amplitude.len(), n);
        assert_eq!(result.frequency.len(), n);
    }

    #[test]
    fn multi_rate_convergence_order() {
        // Multi-rate with RK4 sub-steps should preserve h^4 convergence.
        let model = KuramotoOscillator::new(1, 0.0, 1.0, 0.0, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(vec![0.0], vec![1.0], vec![0.0], None).unwrap();
        let t_final = 0.1_f64;
        let r_exact = (-t_final).exp();

        let sub_steps = 4_usize;
        let h_outer_vals = [0.1, 0.05, 0.025];
        let mut errors = [0.0_f64; 3];
        for (idx, &h_outer) in h_outer_vals.iter().enumerate() {
            let n_outer = (t_final / h_outer).round() as usize;
            let mut mri = MultiRateIntegrator::new(sub_steps).unwrap();
            let (final_state, _) = mri
                .integrate(&model, &state, n_outer, h_outer, false)
                .unwrap();
            errors[idx] = (final_state.amplitude[0] - r_exact).abs();
        }
        // Inner dt = h_outer / sub_steps. Halving h_outer halves inner dt.
        // RK4 error ∝ h_inner^4, so ratio ≈ 2^4 = 16.
        let ratio1 = errors[0] / errors[1];
        let ratio2 = errors[1] / errors[2];
        assert!(
            ratio1 > 8.0 && ratio1 < 32.0,
            "multi-rate RK4 order broken: ratio1={ratio1}, errors={errors:?}"
        );
        assert!(
            ratio2 > 8.0 && ratio2 < 32.0,
            "multi-rate RK4 order broken: ratio2={ratio2}, errors={errors:?}"
        );
    }

    #[test]
    fn multi_rate_integrate_trajectory() {
        let n = 4;
        let model = KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0, 1.5],
            vec![1.0; n],
            vec![1.0, 2.0, 1.5, 0.5],
            None,
        )
        .unwrap();
        let mut mri = MultiRateIntegrator::new(3).unwrap();
        let (final_state, traj) = mri.integrate(&model, &state, 5, 0.01, true).unwrap();
        assert!(traj.is_some());
        assert_eq!(traj.as_ref().unwrap().len(), 5);
        for i in 0..n {
            assert!(final_state.phase[i].is_finite());
        }
    }

    #[test]
    fn multi_rate_euler_method() {
        let n = 2;
        let model = uncoupled(n, 1.0);
        let state = make_state(n, 0.0, 1.0, 1.0);
        let mut mri = MultiRateIntegrator::with_method(5, MultiRateMethod::Euler).unwrap();
        let result = mri.step(&model, &state, 0.01).unwrap();
        for i in 0..n {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
        }
    }

    #[test]
    fn multi_rate_rejects_invalid_dt() {
        let model = uncoupled(1, 1.0);
        let state = make_state(1, 0.0, 1.0, 1.0);
        let mut mri = MultiRateIntegrator::new(5).unwrap();
        assert!(matches!(
            mri.step(&model, &state, 0.0).unwrap_err(),
            IntegrateError::InvalidTimestep { .. }
        ));
    }

    #[test]
    fn multi_rate_freq_band_preserved() {
        let n = 3;
        let model = uncoupled(n, 1.0);
        let state = OscillatorState::new(
            vec![0.0, 0.1, 0.2],
            vec![1.0; n],
            vec![1.0; n],
            Some(vec![0, 1, 2]),
        )
        .unwrap();
        let mut mri = MultiRateIntegrator::new(3).unwrap();
        let result = mri.step(&model, &state, 0.01).unwrap();
        assert_eq!(result.freq_band, Some(vec![0, 1, 2]));
    }

    // ------------------------------------------------------------------
    // WP012-F3: matrix_exp propagates LU failure as typed error
    // ------------------------------------------------------------------

    #[test]
    fn matrix_exp_singular_denominator_returns_typed_error() {
        // Construct a matrix where V − U is singular.
        // A matrix with all entries equal to a large value causes the Padé
        // numerator and denominator to become nearly identical, making V−U
        // near-singular.
        let n = 2;
        let big = 1e15;
        let mut a = Array2::<f64>::zeros((n, n));
        for i in 0..n {
            for j in 0..n {
                a[[i, j]] = big;
            }
        }
        // The LU decomposition should fail on this near-singular denominator.
        let result = matrix_exp(&a);
        // Either it succeeds (numerically lucky) or returns LinearSolveFailed.
        // The key invariant: it must NOT silently return identity.
        if let Ok(ref e) = result {
            // If it succeeded, the result must NOT be the identity matrix.
            let is_identity = (0..n).all(|i| {
                (0..n).all(|j| {
                    let expected = if i == j { 1.0 } else { 0.0 };
                    (e[[i, j]] - expected).abs() < 1e-10
                })
            });
            assert!(
                !is_identity,
                "matrix_exp must not silently return identity on singular input"
            );
        }
        // If Err, it should be LinearSolveFailed.
        if let Err(ref e) = result {
            assert!(matches!(e, IntegrateError::LinearSolveFailed));
        }
    }

    // ------------------------------------------------------------------
    // WP012-F5: ExponentialIntegrator validates dim against state
    // ------------------------------------------------------------------

    #[test]
    fn exp_integrator_dim_mismatch_returns_typed_error() {
        let n = 2;
        let model = uncoupled(n, 1.0);
        let state = make_state(n, 0.0, 1.0, 1.0);
        // dim=9 (3*3) but state has 2 oscillators (3*2=6)
        let mut ei = ExponentialIntegrator::new(9, 4, 150).unwrap();
        assert!(matches!(
            ei.step(&model, &state, 0.01).unwrap_err(),
            IntegrateError::InvalidDim { .. }
        ));
    }

    #[test]
    fn exp_integrator_integrate_dim_mismatch_returns_typed_error() {
        let n = 2;
        let model = uncoupled(n, 1.0);
        let state = make_state(n, 0.0, 1.0, 1.0);
        let mut ei = ExponentialIntegrator::new(9, 4, 150).unwrap();
        assert!(matches!(
            ei.integrate(&model, &state, 5, 0.01, false, 1).unwrap_err(),
            IntegrateError::InvalidDim { .. }
        ));
    }
}

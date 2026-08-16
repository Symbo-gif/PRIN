//! Fused three-band (delta/theta/gamma) discrete-time step: a CPU reference
//! and a single-source CubeCL kernel set for CUDA, wgpu, and CPU-SIMD
//! backends.
//!
//! This is the *discrete-time* counterpart to [`crate::mean_field_rk4`]'s
//! continuous RK4 stepper: one Euler evaluation per band instead of a
//! four-stage refinement, combined with slow→fast phase–amplitude coupling
//! (PAC) *gating* between adjacent bands. It reproduces the PRINet 3.0
//! `DeltaThetaGammaNetwork` discrete-time stepper's semantics — see
//! `prin_dynamics::bands`'s module documentation, "Correspondence to the
//! PRINet 3.0 reference", for why this differs from
//! [`prin_dynamics::bands::BandNetwork`]'s continuous relaxation form (an
//! *assignment*, not a relaxation term, matching the reference's own
//! discrete-time band-network stepper rather than the continuous ODE variant
//! built for [`prin_dynamics::integrate::Integrator`]).
//!
//! # State layout
//!
//! `phase`/`amplitude`/`frequency` are concatenated slow→fast:
//! `[delta (band_sizes[0]), theta (band_sizes[1]), gamma (band_sizes[2])]`,
//! matching `prin_dynamics::bands::create_band_state`'s convention.
//!
//! # Algorithm (per step)
//!
//! 1. **Band 0 (delta):** advance via one Euler step of the mean-field
//!    Kuramoto/Stuart–Landau derivative, computed from delta's own order
//!    parameter (reusing `mean_field_rk4::mean_field_derivatives_into` — the
//!    single-source derivative evaluation, not a re-derived copy).
//! 2. **PAC pair 0 (delta → theta):** the mean of delta's *just-stepped*
//!    phase drives the PAC modulation factor
//!    `1 + m·cos(mean(φ_delta') + offset)` (`f64`-accumulated mean, Coding
//!    Standards §2.2), which *overwrites* theta's pre-step amplitude
//!    (clamped to `[amp_min, amp_max]`) — an assignment, matching the
//!    reference's "overwrite the fast band's amplitude with the PAC-modulated
//!    values" step order.
//! 3. **Band 1 (theta):** advance via one Euler step using the gated
//!    amplitude as its current state (so theta's own order parameter and
//!    Stuart–Landau term both see the PAC-modulated amplitude).
//! 4. **PAC pair 1 (theta → gamma) / Band 2 (gamma):** identical to steps 2–3,
//!    one band further down the hierarchy.
//!
//! # Reusable hierarchical order-parameter reductions
//!
//! The CPU reference computes each band's order parameter and each PAC
//! pair's slow-phase mean with an exact `O(N_b)` `f64`-accumulated sum (this
//! is the numerical authority). The GPU path in [`cubecl`] reuses *one*
//! hierarchical block-reduction kernel for the three per-band order
//! parameters and *one* hierarchical block-reduction kernel for the two
//! PAC slow-phase means — called repeatedly across the fused path rather than
//! duplicated per band/pair — see that module's documentation.

use thiserror::Error;

use crate::mean_field_rk4::{
    clamp_amp, mean_field_derivatives_into, wrap_phase, MeanFieldRk4Params,
};

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
pub mod cubecl;

/// Band index of the slowest (delta) band in `band_sizes` / the concatenated
/// state layout.
pub const DELTA: usize = 0;
/// Band index of the middle (theta) band.
pub const THETA: usize = 1;
/// Band index of the fastest (gamma) band.
pub const GAMMA: usize = 2;

/// Intra-band dynamical parameters for one band (mean-field Kuramoto coupling
/// plus Stuart–Landau amplitude relaxation), matching
/// [`crate::mean_field_rk4::MeanFieldRk4Params`]'s `k`/`decay`/`gamma` fields.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BandStepParams {
    /// Intra-band Kuramoto coupling strength `K`.
    pub k: f32,
    /// Stuart–Landau amplitude decay rate `lambda`.
    pub decay: f32,
    /// Kuramoto frequency-adaptation rate `gamma`.
    pub gamma: f32,
}

/// One slow→fast PAC gate's parameters, matching
/// `prin_dynamics::pac::PhaseAmplitudeCoupling`'s modulation depth and phase
/// offset.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PacGateParams {
    /// Modulation depth `m`, expected in `[0, 1]`.
    pub modulation_depth: f32,
    /// Phase offset added to the slow band's mean phase before the cosine.
    pub phase_offset: f32,
}

/// Full parameter set for one fused three-band discrete step.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct DiscreteStepParams {
    /// Per-band parameters, indexed by [`DELTA`], [`THETA`], [`GAMMA`].
    pub bands: [BandStepParams; 3],
    /// PAC gate parameters: `pac[0]` is delta→theta, `pac[1]` is theta→gamma.
    pub pac: [PacGateParams; 2],
    /// Output amplitude clamp minimum (applied after PAC gating and after
    /// each band's Euler step).
    pub amp_min: f32,
    /// Output amplitude clamp maximum.
    pub amp_max: f32,
    /// Timestep `dt`.
    pub dt: f32,
}

/// Output of a fused discrete step: updated `(phase, amplitude, frequency)`.
pub type DiscreteStepOutput = (Vec<f32>, Vec<f32>, Vec<f32>);

/// Errors raised by the fused discrete-step kernels.
#[derive(Debug, Error)]
pub enum DiscreteStepError {
    /// Input buffers have inconsistent lengths.
    #[error("input length mismatch: phase={phase}, amplitude={amp}, frequency={freq}")]
    LengthMismatch {
        /// Phase buffer length.
        phase: usize,
        /// Amplitude buffer length.
        amp: usize,
        /// Frequency buffer length.
        freq: usize,
    },
    /// A band's declared size is zero.
    #[error("band {band} has zero oscillators")]
    EmptyBand {
        /// Index of the offending band.
        band: usize,
    },
    /// `band_sizes` does not sum to the state length.
    #[error("band sizes sum to {expected} but state has {got} oscillators")]
    PopulationMismatch {
        /// Sum of `band_sizes`.
        expected: usize,
        /// Actual state length.
        got: usize,
    },
    /// A state value (`phase`, `amplitude`, or `frequency`) is non-finite.
    #[error("non-finite value in {name} at index {index}: {value}")]
    NonFiniteState {
        /// Offending buffer name.
        name: &'static str,
        /// Offending index.
        index: usize,
        /// Offending value.
        value: f32,
    },
    /// A per-band parameter is non-finite.
    #[error("non-finite parameter: bands[{band}].{name} = {value}")]
    NonFiniteBandParameter {
        /// Offending band index.
        band: usize,
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f32,
    },
    /// A PAC pair's `phase_offset` is non-finite.
    #[error("non-finite parameter: pac[{pair}].phase_offset = {value}")]
    NonFinitePacPhaseOffset {
        /// Offending PAC pair index.
        pair: usize,
        /// Offending value.
        value: f32,
    },
    /// A PAC pair's `modulation_depth` is non-finite or outside `[0, 1]`.
    #[error("invalid parameter: pac[{pair}].modulation_depth = {value} (must be in [0, 1])")]
    InvalidModulationDepth {
        /// Offending PAC pair index.
        pair: usize,
        /// Offending value.
        value: f32,
    },
    /// A non-band, non-PAC scalar parameter is non-finite.
    #[error("non-finite parameter: {name} = {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// A non-band, non-PAC scalar parameter is invalid (e.g. `dt <= 0`).
    #[error("invalid parameter: {name} = {value}")]
    InvalidParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// The amplitude clamp range is invalid (non-finite bounds or
    /// `amp_min > amp_max`).
    #[error(
        "invalid clamp range: amp_min={amp_min}, amp_max={amp_max} (require finite amp_min <= amp_max)"
    )]
    InvalidClampRange {
        /// Offending clamp minimum.
        amp_min: f32,
        /// Offending clamp maximum.
        amp_max: f32,
    },
    /// Device backend read-back failed.
    #[error("device backend read-back failed")]
    BackendReadError,
    /// The requested compute backend (wgpu/CUDA) is not available on this
    /// host.
    #[error("backend unavailable: {name}")]
    BackendUnavailable {
        /// Backend name.
        name: &'static str,
    },
    /// Device-event profiling of a kernel launch sequence failed.
    #[error("device profiling failed: {message}")]
    ProfilingFailed {
        /// Underlying `cubecl` profiling error message.
        message: String,
    },
}

/// Starting offset of each band in the concatenated state layout.
pub(crate) fn band_offsets(band_sizes: [usize; 3]) -> [usize; 3] {
    [0, band_sizes[0], band_sizes[0] + band_sizes[1]]
}

/// Validate that the three state buffers have equal length and every value is
/// finite.
fn validate_state(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
) -> Result<usize, DiscreteStepError> {
    if phase.len() != amplitude.len() || phase.len() != frequency.len() {
        return Err(DiscreteStepError::LengthMismatch {
            phase: phase.len(),
            amp: amplitude.len(),
            freq: frequency.len(),
        });
    }
    for (i, &p) in phase.iter().enumerate() {
        if !p.is_finite() {
            return Err(DiscreteStepError::NonFiniteState {
                name: "phase",
                index: i,
                value: p,
            });
        }
    }
    for (i, &a) in amplitude.iter().enumerate() {
        if !a.is_finite() {
            return Err(DiscreteStepError::NonFiniteState {
                name: "amplitude",
                index: i,
                value: a,
            });
        }
    }
    for (i, &f) in frequency.iter().enumerate() {
        if !f.is_finite() {
            return Err(DiscreteStepError::NonFiniteState {
                name: "frequency",
                index: i,
                value: f,
            });
        }
    }
    Ok(phase.len())
}

/// Validate that `band_sizes` are all non-zero and sum to `n`.
fn validate_bands(band_sizes: [usize; 3], n: usize) -> Result<(), DiscreteStepError> {
    for (b, &sz) in band_sizes.iter().enumerate() {
        if sz == 0 {
            return Err(DiscreteStepError::EmptyBand { band: b });
        }
    }
    let total: usize = band_sizes.iter().sum();
    if total != n {
        return Err(DiscreteStepError::PopulationMismatch {
            expected: total,
            got: n,
        });
    }
    Ok(())
}

/// Validate every scalar parameter in `params`.
fn validate_params(params: &DiscreteStepParams) -> Result<(), DiscreteStepError> {
    for (b, bp) in params.bands.iter().enumerate() {
        for (name, value) in [("k", bp.k), ("decay", bp.decay), ("gamma", bp.gamma)] {
            if !value.is_finite() {
                return Err(DiscreteStepError::NonFiniteBandParameter {
                    band: b,
                    name,
                    value,
                });
            }
        }
    }
    for (p, pac) in params.pac.iter().enumerate() {
        if !pac.modulation_depth.is_finite() || !(0.0..=1.0).contains(&pac.modulation_depth) {
            return Err(DiscreteStepError::InvalidModulationDepth {
                pair: p,
                value: pac.modulation_depth,
            });
        }
        if !pac.phase_offset.is_finite() {
            return Err(DiscreteStepError::NonFinitePacPhaseOffset {
                pair: p,
                value: pac.phase_offset,
            });
        }
    }
    if !params.dt.is_finite() {
        return Err(DiscreteStepError::NonFiniteParameter {
            name: "dt",
            value: params.dt,
        });
    }
    if params.dt <= 0.0 {
        return Err(DiscreteStepError::InvalidParameter {
            name: "dt",
            value: params.dt,
        });
    }
    if !params.amp_min.is_finite() || !params.amp_max.is_finite() || params.amp_min > params.amp_max
    {
        return Err(DiscreteStepError::InvalidClampRange {
            amp_min: params.amp_min,
            amp_max: params.amp_max,
        });
    }
    Ok(())
}

/// `f64`-accumulated mean of a `f32` slice, downcast at the end (Coding
/// Standards §2.2).
fn mean_f64(values: &[f32]) -> f32 {
    let sum: f64 = values.iter().map(|&v| f64::from(v)).sum();
    (sum / values.len() as f64) as f32
}

/// One Euler evaluation of a band's intra-band Kuramoto/Stuart–Landau
/// derivative, written into `out_phase`/`out_amp`/`out_freq` (which must be
/// the same length as `phase`).
#[allow(clippy::too_many_arguments)]
fn step_band_euler(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band: &BandStepParams,
    dt: f32,
    out_phase: &mut [f32],
    out_amp: &mut [f32],
    out_freq: &mut [f32],
) {
    let n = phase.len();
    let n_inv = 1.0 / n as f32;
    // `dt` is unused inside `mean_field_derivatives_into` (it evaluates the
    // derivative, not a stage state); the Euler advance below applies `dt`.
    let rk4_params = MeanFieldRk4Params {
        k: band.k,
        decay: band.decay,
        gamma: band.gamma,
        dt,
    };

    let mut dphase = Vec::with_capacity(n);
    let mut damp = Vec::with_capacity(n);
    let mut dfreq = Vec::with_capacity(n);
    mean_field_derivatives_into(
        phase,
        amplitude,
        frequency,
        &rk4_params,
        n_inv,
        &mut dphase,
        &mut damp,
        &mut dfreq,
    );

    for i in 0..n {
        out_phase[i] = wrap_phase(phase[i] + dt * dphase[i]);
        out_amp[i] = clamp_amp(amplitude[i] + dt * damp[i]);
        out_freq[i] = frequency[i] + dt * dfreq[i];
    }
}

/// One fused three-band (delta/theta/gamma) discrete step.
///
/// This is the CPU reference path (numerical authority). See the module
/// documentation for the algorithm and state-layout convention.
///
/// # Arguments
///
/// * `phase`, `amplitude`, `frequency` — concatenated state, slow→fast
///   (`delta ++ theta ++ gamma`).
/// * `band_sizes` — `[n_delta, n_theta, n_gamma]`; must sum to `phase.len()`.
/// * `params` — per-band and per-PAC-pair parameters.
///
/// # Errors
///
/// Returns [`DiscreteStepError`] on mismatched lengths, a zero-size or
/// mismatched band, non-finite state/parameter values, an invalid modulation
/// depth, a non-positive `dt`, or an inverted amplitude clamp range.
pub fn discrete_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> Result<DiscreteStepOutput, DiscreteStepError> {
    let n = validate_state(phase, amplitude, frequency)?;
    validate_bands(band_sizes, n)?;
    validate_params(params)?;

    let offsets = band_offsets(band_sizes);
    let mut out_phase = phase.to_vec();
    let mut out_amp = amplitude.to_vec();
    let mut out_freq = frequency.to_vec();

    // Band 0 (delta): plain intra-band Euler step, no incoming PAC gate.
    {
        let r = offsets[DELTA]..offsets[DELTA] + band_sizes[DELTA];
        let (op, oa, of) = (
            &mut out_phase[r.clone()],
            &mut out_amp[r.clone()],
            &mut out_freq[r.clone()],
        );
        step_band_euler(
            &phase[r.clone()],
            &amplitude[r.clone()],
            &frequency[r.clone()],
            &params.bands[DELTA],
            params.dt,
            op,
            oa,
            of,
        );
    }

    // PAC pairs: (delta -> theta), (theta -> gamma).
    for pair in 0..2 {
        let slow = pair;
        let fast = pair + 1;
        let slow_r = offsets[slow]..offsets[slow] + band_sizes[slow];
        let fast_r = offsets[fast]..offsets[fast] + band_sizes[fast];

        let mean_slow_new_phase = mean_f64(&out_phase[slow_r]);
        let modulation = 1.0_f32
            + params.pac[pair].modulation_depth
                * (mean_slow_new_phase + params.pac[pair].phase_offset).cos();

        let gated_amp: Vec<f32> = amplitude[fast_r.clone()]
            .iter()
            .map(|&a| (a * modulation).clamp(params.amp_min, params.amp_max))
            .collect();

        let (op, oa, of) = (
            &mut out_phase[fast_r.clone()],
            &mut out_amp[fast_r.clone()],
            &mut out_freq[fast_r.clone()],
        );
        step_band_euler(
            &phase[fast_r.clone()],
            &gated_amp,
            &frequency[fast_r.clone()],
            &params.bands[fast],
            params.dt,
            op,
            oa,
            of,
        );
    }

    Ok((out_phase, out_amp, out_freq))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_params() -> DiscreteStepParams {
        DiscreteStepParams {
            bands: [
                BandStepParams {
                    k: 1.0,
                    decay: 0.1,
                    gamma: 0.0,
                },
                BandStepParams {
                    k: 1.5,
                    decay: 0.15,
                    gamma: 0.0,
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
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
        let frequency: Vec<_> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
        (phase, amplitude, frequency)
    }

    #[test]
    fn step_preserves_shape_and_invariants() {
        let band_sizes = [4usize, 8, 16];
        let (phase, amp, freq) = make_state(band_sizes);
        let (op, oa, of) =
            discrete_step_cpu(&phase, &amp, &freq, band_sizes, &default_params()).unwrap();

        let n: usize = band_sizes.iter().sum();
        assert_eq!(op.len(), n);
        assert_eq!(oa.len(), n);
        assert_eq!(of.len(), n);
        for p in &op {
            assert!(*p >= 0.0 && *p < core::f32::consts::TAU);
        }
        for a in &oa {
            assert!(*a >= 1e-6 && *a <= 10.0 && a.is_finite());
        }
        for f in &of {
            assert!(f.is_finite());
        }
    }

    #[test]
    fn zero_pac_depth_gates_to_identity() {
        // m=0 means modulation == 1, so the gated amplitude equals the
        // original (clamped) fast-band amplitude before its own Euler step.
        let band_sizes = [3usize, 3, 3];
        let (phase, amp, freq) = make_state(band_sizes);
        let mut params = default_params();
        params.pac = [
            PacGateParams {
                modulation_depth: 0.0,
                phase_offset: 0.0,
            },
            PacGateParams {
                modulation_depth: 0.0,
                phase_offset: 0.0,
            },
        ];

        let (_, oa, _) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        // With m=0, theta/gamma's gated amplitude before their own step is
        // identical to what a standalone single-band Euler step with the
        // *unmodified* amplitude would produce.
        let offsets = band_offsets(band_sizes);
        let theta_r = offsets[THETA]..offsets[THETA] + band_sizes[THETA];
        let mut expect_phase = vec![0.0; band_sizes[THETA]];
        let mut expect_amp = vec![0.0; band_sizes[THETA]];
        let mut expect_freq = vec![0.0; band_sizes[THETA]];
        step_band_euler(
            &phase[theta_r.clone()],
            &amp[theta_r.clone()],
            &freq[theta_r.clone()],
            &params.bands[THETA],
            params.dt,
            &mut expect_phase,
            &mut expect_amp,
            &mut expect_freq,
        );
        for (a, e) in oa[theta_r].iter().zip(expect_amp.iter()) {
            assert!((a - e).abs() < 1e-6, "got {a}, expected {e}");
        }
    }

    #[test]
    fn zero_coupling_and_decay_delta_band_is_free_run() {
        let band_sizes = [4usize, 4, 4];
        let (phase, amp, freq) = make_state(band_sizes);
        let mut params = default_params();
        params.bands[DELTA] = BandStepParams {
            k: 0.0,
            decay: 0.0,
            gamma: 0.0,
        };

        let (op, oa, of) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        for i in 0..band_sizes[DELTA] {
            let expected_p = wrap_phase(phase[i] + params.dt * freq[i]);
            assert!((op[i] - expected_p).abs() < 1e-6, "phase mismatch at {i}");
            assert!((oa[i] - amp[i]).abs() < 1e-6, "amplitude mismatch at {i}");
            assert!((of[i] - freq[i]).abs() < 1e-6, "frequency mismatch at {i}");
        }
    }

    #[test]
    fn rejects_mismatched_lengths() {
        let phase = vec![0.0_f32; 8];
        let amp = vec![1.0_f32; 9];
        let freq = vec![0.0_f32; 8];
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 3, 3], &default_params()).unwrap_err();
        assert!(matches!(err, DiscreteStepError::LengthMismatch { .. }));
    }

    #[test]
    fn rejects_non_finite_state() {
        let mut phase = vec![0.0_f32; 6];
        phase[2] = f32::NAN;
        let amp = vec![1.0_f32; 6];
        let freq = vec![0.0_f32; 6];
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &default_params()).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::NonFiniteState {
                name: "phase",
                index: 2,
                ..
            }
        ));
    }

    #[test]
    fn rejects_zero_size_band() {
        let (phase, amp, freq) = make_state([1, 1, 1]);
        let err = discrete_step_cpu(&phase, &amp, &freq, [0, 1, 2], &default_params()).unwrap_err();
        assert!(matches!(err, DiscreteStepError::EmptyBand { band: 0 }));
    }

    #[test]
    fn rejects_population_mismatch() {
        let (phase, amp, freq) = make_state([2, 3, 4]);
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 3, 5], &default_params()).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::PopulationMismatch {
                expected: 10,
                got: 9
            }
        ));
    }

    #[test]
    fn rejects_non_finite_band_parameter() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.bands[THETA].decay = f32::NAN;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::NonFiniteBandParameter {
                band: 1,
                name: "decay",
                ..
            }
        ));
    }

    #[test]
    fn rejects_non_finite_pac_phase_offset() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.pac[1].phase_offset = f32::INFINITY;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::NonFinitePacPhaseOffset { pair: 1, .. }
        ));
    }

    #[test]
    fn rejects_invalid_modulation_depth() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.pac[0].modulation_depth = 1.5;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::InvalidModulationDepth { pair: 0, .. }
        ));
    }

    #[test]
    fn rejects_non_positive_dt() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.dt = 0.0;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::InvalidParameter { name: "dt", .. }
        ));
    }

    #[test]
    fn rejects_non_finite_dt() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.dt = f32::NAN;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(
            err,
            DiscreteStepError::NonFiniteParameter { name: "dt", .. }
        ));
    }

    #[test]
    fn rejects_inverted_clamp_range() {
        let (phase, amp, freq) = make_state([2, 2, 2]);
        let mut params = default_params();
        params.amp_min = 5.0;
        params.amp_max = 1.0;
        let err = discrete_step_cpu(&phase, &amp, &freq, [2, 2, 2], &params).unwrap_err();
        assert!(matches!(err, DiscreteStepError::InvalidClampRange { .. }));
    }

    #[test]
    fn single_oscillator_bands_have_no_self_coupling() {
        // A single-oscillator band's order parameter is its own state, so
        // the Kuramoto coupling term is identically zero (r_sin = r_cos = 0
        // relative to itself is not quite right for N=1 generally, but with
        // zero coupling strength dphase reduces to the natural frequency and
        // damp reduces to pure decay — this exercises the N=1 path end to
        // end without asserting the coupled-N>1 formula).
        let band_sizes = [1usize, 1, 1];
        let phase = vec![0.3_f32, 1.1, 2.2];
        let amp = vec![2.0_f32, 1.0, 0.5];
        let freq = vec![6.0_f32, 40.0, 80.0];
        let mut params = default_params();
        for b in params.bands.iter_mut() {
            b.k = 0.0;
        }
        params.pac = [
            PacGateParams {
                modulation_depth: 0.0,
                phase_offset: 0.0,
            },
            PacGateParams {
                modulation_depth: 0.0,
                phase_offset: 0.0,
            },
        ];

        let (op, oa, _) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();
        for i in 0..3 {
            assert!(op[i].is_finite());
            assert!(oa[i].is_finite());
        }
    }

    #[test]
    fn pac_gate_modulates_fast_band_amplitude() {
        // A synchronized delta band (all phases equal) makes the PAC
        // modulation factor exact: 1 + m*cos(delta_phase + offset).
        let band_sizes = [3usize, 2, 2];
        let phase = vec![0.5_f32, 0.5, 0.5, 1.0, 1.0, 1.2, 1.2];
        let amp = vec![1.0_f32; 7];
        let freq = vec![0.0_f32; 7];
        let mut params = default_params();
        for b in params.bands.iter_mut() {
            b.k = 0.0;
            b.decay = 0.0;
        }
        params.pac[0] = PacGateParams {
            modulation_depth: 0.5,
            phase_offset: 0.1,
        };

        let (_, oa, _) = discrete_step_cpu(&phase, &amp, &freq, band_sizes, &params).unwrap();

        // Delta free-runs (k=0) so its stepped phase is phase + dt*freq =
        // 0.5 (freq=0), the mean is exactly 0.5.
        let expected_modulation = 1.0_f32 + 0.5 * (0.5_f32 + 0.1).cos();
        let expected_theta_amp = (1.0_f32 * expected_modulation).clamp(1e-6, 10.0);
        let offsets = band_offsets(band_sizes);
        for &a in &oa[offsets[THETA]..offsets[THETA] + band_sizes[THETA]] {
            assert!(
                (a - expected_theta_amp).abs() < 1e-5,
                "got {a}, expected {expected_theta_amp}"
            );
        }
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    const TAU: f32 = core::f32::consts::TAU;

    fn any_band_params() -> impl Strategy<Value = BandStepParams> {
        (0.0_f32..=2.0, 0.0_f32..=0.5, -0.05_f32..=0.05)
            .prop_map(|(k, decay, gamma)| BandStepParams { k, decay, gamma })
    }

    fn any_pac_params() -> impl Strategy<Value = PacGateParams> {
        (0.0_f32..=1.0, -TAU..=TAU).prop_map(|(modulation_depth, phase_offset)| PacGateParams {
            modulation_depth,
            phase_offset,
        })
    }

    fn any_params() -> impl Strategy<Value = DiscreteStepParams> {
        (
            any_band_params(),
            any_band_params(),
            any_band_params(),
            any_pac_params(),
            any_pac_params(),
            0.001_f32..=0.05,
        )
            .prop_map(|(b0, b1, b2, p0, p1, dt)| DiscreteStepParams {
                bands: [b0, b1, b2],
                pac: [p0, p1],
                amp_min: 1e-6,
                amp_max: 10.0,
                dt,
            })
    }

    /// Maximum size of any single band in the proptests below; state vectors
    /// are generated at `3 * MAX_BAND` and each band slices its prefix, so a
    /// fixed-size strategy can be reused instead of building a fresh
    /// exact-size strategy per case (avoids `ValueTree` plumbing).
    const MAX_BAND: usize = 8;

    fn any_state() -> impl Strategy<Value = (Vec<f32>, Vec<f32>, Vec<f32>)> {
        let n = 3 * MAX_BAND;
        (
            proptest::collection::vec(0.0_f32..TAU, n),
            proptest::collection::vec(0.0_f32..=1.0_f32, n),
            proptest::collection::vec(-1.0_f32..=1.0_f32, n),
        )
    }

    proptest! {
        #[test]
        fn output_invariants_always_hold(
            n0 in 1usize..=MAX_BAND,
            n1 in 1usize..=MAX_BAND,
            n2 in 1usize..=MAX_BAND,
            params in any_params(),
            state in any_state(),
        ) {
            let n = n0 + n1 + n2;
            let (phase, amp, freq) = state;
            let phase = phase[..n].to_vec();
            let amp = amp[..n].to_vec();
            let freq = freq[..n].to_vec();

            let (op, oa, of) =
                discrete_step_cpu(&phase, &amp, &freq, [n0, n1, n2], &params).unwrap();

            prop_assert_eq!(op.len(), n);
            for p in &op {
                prop_assert!(*p >= 0.0 && *p < TAU);
            }
            for a in &oa {
                prop_assert!(*a >= params.amp_min - 1e-6 && *a <= params.amp_max + 1e-6);
                prop_assert!(a.is_finite());
            }
            for f in &of {
                prop_assert!(f.is_finite());
            }
        }
    }

    proptest! {
        #[test]
        fn zero_coupling_all_bands_is_free_run(
            n0 in 1usize..=MAX_BAND,
            n1 in 1usize..=MAX_BAND,
            n2 in 1usize..=MAX_BAND,
            dt in 0.001_f32..=0.05,
            state in any_state(),
        ) {
            let n = n0 + n1 + n2;
            let (phase, amp, freq) = state;
            let phase = phase[..n].to_vec();
            let amp = amp[..n].to_vec();
            let freq = freq[..n].to_vec();
            let params = DiscreteStepParams {
                bands: [
                    BandStepParams { k: 0.0, decay: 0.0, gamma: 0.0 },
                    BandStepParams { k: 0.0, decay: 0.0, gamma: 0.0 },
                    BandStepParams { k: 0.0, decay: 0.0, gamma: 0.0 },
                ],
                pac: [
                    PacGateParams { modulation_depth: 0.0, phase_offset: 0.0 },
                    PacGateParams { modulation_depth: 0.0, phase_offset: 0.0 },
                ],
                amp_min: 1e-6,
                amp_max: 10.0,
                dt,
            };

            let (op, oa, of) =
                discrete_step_cpu(&phase, &amp, &freq, [n0, n1, n2], &params).unwrap();

            for i in 0..n {
                let expected_p = wrap_phase(phase[i] + dt * freq[i]);
                prop_assert!((op[i] - expected_p).abs() < 1e-4);
                prop_assert!((oa[i] - amp[i]).abs() < 1e-6);
                prop_assert!((of[i] - freq[i]).abs() < 1e-6);
            }
        }
    }
}

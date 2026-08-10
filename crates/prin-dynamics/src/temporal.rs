//! Temporal propagation across frames: complex-phasor phase blending plus EMA
//! amplitude blending.
//!
//! - [`ComplexPhasorBlender`]: blends phases by converting to unit phasors
//!   `z = e^{iφ}`, taking a weighted complex average, and extracting the
//!   resultant phase via `atan2`. This correctly handles the circular nature
//!   of phase (e.g. blending 0.1 and 2π−0.1 gives ≈0, not π).
//! - [`EmaAmplitudeBlender`]: exponential moving average for amplitudes.
//! - [`TemporalPropagator`]: combines both, maintaining a running blended
//!   state across frames.
//!
//! Implementation lands in Phase 2 (see `DOCS/PRIN_Project_Plan.md`).

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::state::{wrap_phase, AMPLITUDE_MAX, AMPLITUDE_MIN};

/// Errors raised by temporal propagation operations.
#[derive(Debug, Error)]
pub enum TemporalError {
    /// The blending factor α is outside the permitted range `(0, 1]`.
    #[error("blending_factor must be in (0, 1], got {value}")]
    InvalidBlendingFactor {
        /// Offending blending factor.
        value: f64,
    },

    /// An input slice is empty.
    #[error("temporal propagation requires non-empty `{name}`")]
    EmptyInput {
        /// Name of the offending slice.
        name: &'static str,
    },

    /// Input slices have mismatched lengths.
    #[error("length mismatch: `{name_a}` has {len_a}, `{name_b}` has {len_b}")]
    LengthMismatch {
        /// First slice name.
        name_a: &'static str,
        /// First slice length.
        len_a: usize,
        /// Second slice name.
        name_b: &'static str,
        /// Second slice length.
        len_b: usize,
    },

    /// A value is not finite.
    #[error("non-finite value in `{name}` at index {index}: {value}")]
    NonFiniteValue {
        /// Name of the offending field.
        name: &'static str,
        /// Index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
    },

    /// The propagator has not been initialized (no prior frame).
    #[error("temporal propagator has no prior state; call propagate_init or propagate first")]
    Uninitialized,

    /// The state size changed between frames.
    #[error("state size changed: propagator expects {expected} oscillators, got {got}")]
    StateSizeChanged {
        /// Expected size from initialization.
        expected: usize,
        /// Actual size of the new frame.
        got: usize,
    },
}

/// Complex-phasor phase blender.
///
/// Blends two phase arrays by converting to unit phasors, taking a weighted
/// complex average, and extracting the resultant phase:
///
/// ```text
/// z_new = e^{i·φ_new}
/// z_old = e^{i·φ_old}
/// z_blend = α·z_new + (1-α)·z_old
/// φ_blend = atan2(Im(z_blend), Re(z_blend))
/// ```
///
/// This correctly handles circular phase averaging (e.g. blending phases near
/// 0 and 2π yields a result near 0, not near π).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ComplexPhasorBlender {
    /// Blending factor α ∈ (0, 1]. Higher = more weight on the new frame.
    alpha: f64,
}

impl ComplexPhasorBlender {
    /// Create a new phasor blender with blending factor `alpha`.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `alpha` is not
    /// finite or outside `(0, 1]`.
    pub fn new(alpha: f64) -> Result<Self, TemporalError> {
        if !alpha.is_finite() || alpha <= 0.0 || alpha > 1.0 {
            return Err(TemporalError::InvalidBlendingFactor { value: alpha });
        }
        Ok(Self { alpha })
    }

    /// Current blending factor.
    pub fn alpha(&self) -> f64 {
        self.alpha
    }

    /// Set the blending factor.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `value` is not
    /// finite or outside `(0, 1]`.
    pub fn set_alpha(&mut self, value: f64) -> Result<(), TemporalError> {
        if !value.is_finite() || value <= 0.0 || value > 1.0 {
            return Err(TemporalError::InvalidBlendingFactor { value });
        }
        self.alpha = value;
        Ok(())
    }

    /// Blend `new_phases` with `old_phases` using complex-phasor interpolation.
    ///
    /// Both slices must have the same length and contain only finite values.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError`] for empty inputs, length mismatches, or
    /// non-finite values.
    pub fn blend(&self, new_phases: &[f64], old_phases: &[f64]) -> Result<Vec<f64>, TemporalError> {
        if new_phases.is_empty() {
            return Err(TemporalError::EmptyInput { name: "new_phases" });
        }
        if new_phases.len() != old_phases.len() {
            return Err(TemporalError::LengthMismatch {
                name_a: "new_phases",
                len_a: new_phases.len(),
                name_b: "old_phases",
                len_b: old_phases.len(),
            });
        }

        let alpha = self.alpha;
        let beta = 1.0 - alpha;
        let mut result = Vec::with_capacity(new_phases.len());

        for (i, (&new_p, &old_p)) in new_phases.iter().zip(old_phases.iter()).enumerate() {
            if !new_p.is_finite() {
                return Err(TemporalError::NonFiniteValue {
                    name: "new_phases",
                    index: i,
                    value: new_p,
                });
            }
            if !old_p.is_finite() {
                return Err(TemporalError::NonFiniteValue {
                    name: "old_phases",
                    index: i,
                    value: old_p,
                });
            }

            // Convert to unit phasors
            let z_new_re = new_p.cos();
            let z_new_im = new_p.sin();
            let z_old_re = old_p.cos();
            let z_old_im = old_p.sin();

            // Weighted blend
            let z_blend_re = alpha * z_new_re + beta * z_old_re;
            let z_blend_im = alpha * z_new_im + beta * z_old_im;

            // Extract blended phase
            let blended = z_blend_im.atan2(z_blend_re);
            result.push(wrap_phase(blended));
        }

        Ok(result)
    }

    /// Blend a single new phase with a single old phase.
    ///
    /// Convenience method for scalar blending.
    pub fn blend_scalar(&self, new_phase: f64, old_phase: f64) -> Result<f64, TemporalError> {
        if !new_phase.is_finite() {
            return Err(TemporalError::NonFiniteValue {
                name: "new_phase",
                index: 0,
                value: new_phase,
            });
        }
        if !old_phase.is_finite() {
            return Err(TemporalError::NonFiniteValue {
                name: "old_phase",
                index: 0,
                value: old_phase,
            });
        }

        let alpha = self.alpha;
        let beta = 1.0 - alpha;

        let z_re = alpha * new_phase.cos() + beta * old_phase.cos();
        let z_im = alpha * new_phase.sin() + beta * old_phase.sin();

        Ok(wrap_phase(z_im.atan2(z_re)))
    }
}

/// Exponential moving average (EMA) amplitude blender.
///
/// `A_blend = α·A_new + (1-α)·A_old`
///
/// Output amplitudes are clamped to `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EmaAmplitudeBlender {
    /// Blending factor α ∈ (0, 1].
    alpha: f64,
    /// Amplitude clamp minimum.
    amp_min: f64,
    /// Amplitude clamp maximum.
    amp_max: f64,
}

impl EmaAmplitudeBlender {
    /// Create a new EMA blender with blending factor `alpha` and the standard
    /// PRIN amplitude clamp `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `alpha` is not
    /// finite or outside `(0, 1]`.
    pub fn new(alpha: f64) -> Result<Self, TemporalError> {
        Self::with_clamp(alpha, AMPLITUDE_MIN, AMPLITUDE_MAX)
    }

    /// Create a new EMA blender with a custom amplitude clamp range.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `alpha` is not
    /// finite or outside `(0, 1]`.
    pub fn with_clamp(alpha: f64, amp_min: f64, amp_max: f64) -> Result<Self, TemporalError> {
        if !alpha.is_finite() || alpha <= 0.0 || alpha > 1.0 {
            return Err(TemporalError::InvalidBlendingFactor { value: alpha });
        }
        Ok(Self {
            alpha,
            amp_min,
            amp_max,
        })
    }

    /// Current blending factor.
    pub fn alpha(&self) -> f64 {
        self.alpha
    }

    /// Set the blending factor.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `value` is not
    /// finite or outside `(0, 1]`.
    pub fn set_alpha(&mut self, value: f64) -> Result<(), TemporalError> {
        if !value.is_finite() || value <= 0.0 || value > 1.0 {
            return Err(TemporalError::InvalidBlendingFactor { value });
        }
        self.alpha = value;
        Ok(())
    }

    /// Amplitude clamp minimum.
    pub fn amp_min(&self) -> f64 {
        self.amp_min
    }

    /// Amplitude clamp maximum.
    pub fn amp_max(&self) -> f64 {
        self.amp_max
    }

    /// Blend `new_amplitudes` with `old_amplitudes` using EMA.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError`] for empty inputs, length mismatches, or
    /// non-finite values.
    pub fn blend(
        &self,
        new_amplitudes: &[f64],
        old_amplitudes: &[f64],
    ) -> Result<Vec<f64>, TemporalError> {
        if new_amplitudes.is_empty() {
            return Err(TemporalError::EmptyInput {
                name: "new_amplitudes",
            });
        }
        if new_amplitudes.len() != old_amplitudes.len() {
            return Err(TemporalError::LengthMismatch {
                name_a: "new_amplitudes",
                len_a: new_amplitudes.len(),
                name_b: "old_amplitudes",
                len_b: old_amplitudes.len(),
            });
        }

        let alpha = self.alpha;
        let beta = 1.0 - alpha;
        let mut result = Vec::with_capacity(new_amplitudes.len());

        for (i, (&new_a, &old_a)) in new_amplitudes.iter().zip(old_amplitudes.iter()).enumerate() {
            if !new_a.is_finite() {
                return Err(TemporalError::NonFiniteValue {
                    name: "new_amplitudes",
                    index: i,
                    value: new_a,
                });
            }
            if !old_a.is_finite() {
                return Err(TemporalError::NonFiniteValue {
                    name: "old_amplitudes",
                    index: i,
                    value: old_a,
                });
            }

            let blended = alpha * new_a + beta * old_a;
            let clamped = clamp_amp(blended, self.amp_min, self.amp_max);
            result.push(clamped);
        }

        Ok(result)
    }
}

/// Temporal propagator: combines complex-phasor phase blending with EMA
/// amplitude blending, maintaining a running state across frames.
///
/// # Usage
///
/// 1. Create with a blending factor `α`.
/// 2. Call [`propagate`](TemporalPropagator::propagate) for each new frame.
///    The first call initializes the running state; subsequent calls blend
///    with the previous blended state.
/// 3. Access the current blended state via [`current_phases`] and
///    [`current_amplitudes`].
///
/// [`current_phases`]: TemporalPropagator::current_phases
/// [`current_amplitudes`]: TemporalPropagator::current_amplitudes
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TemporalPropagator {
    /// Phase blender.
    phase_blender: ComplexPhasorBlender,
    /// Amplitude blender.
    amplitude_blender: EmaAmplitudeBlender,
    /// Running blended phases (set after first `propagate` call).
    running_phases: Option<Vec<f64>>,
    /// Running blended amplitudes.
    running_amplitudes: Option<Vec<f64>>,
}

impl TemporalPropagator {
    /// Create a new temporal propagator with blending factor `alpha`.
    ///
    /// Both phase and amplitude blending use the same `alpha`. Use
    /// [`with_separate_alpha`](Self::with_separate_alpha) for independent
    /// control.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if `alpha` is not
    /// finite or outside `(0, 1]`.
    pub fn new(alpha: f64) -> Result<Self, TemporalError> {
        Ok(Self {
            phase_blender: ComplexPhasorBlender::new(alpha)?,
            amplitude_blender: EmaAmplitudeBlender::new(alpha)?,
            running_phases: None,
            running_amplitudes: None,
        })
    }

    /// Create a temporal propagator with separate blending factors for phase
    /// and amplitude.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError::InvalidBlendingFactor`] if either factor is
    /// not finite or outside `(0, 1]`.
    pub fn with_separate_alpha(
        phase_alpha: f64,
        amplitude_alpha: f64,
    ) -> Result<Self, TemporalError> {
        Ok(Self {
            phase_blender: ComplexPhasorBlender::new(phase_alpha)?,
            amplitude_blender: EmaAmplitudeBlender::new(amplitude_alpha)?,
            running_phases: None,
            running_amplitudes: None,
        })
    }

    /// Phase blending factor.
    pub fn phase_alpha(&self) -> f64 {
        self.phase_blender.alpha()
    }

    /// Amplitude blending factor.
    pub fn amplitude_alpha(&self) -> f64 {
        self.amplitude_blender.alpha()
    }

    /// Whether the propagator has been initialized (at least one
    /// `propagate` call).
    pub fn is_initialized(&self) -> bool {
        self.running_phases.is_some()
    }

    /// Current blended phases, or `None` if not yet initialized.
    pub fn current_phases(&self) -> Option<&[f64]> {
        self.running_phases.as_deref()
    }

    /// Current blended amplitudes, or `None` if not yet initialized.
    pub fn current_amplitudes(&self) -> Option<&[f64]> {
        self.running_amplitudes.as_deref()
    }

    /// Initialize the running state without blending (sets the running state
    /// to the given frame).
    ///
    /// Use this when you want the first frame to pass through unmodified.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError`] for empty inputs, length mismatches, or
    /// non-finite values.
    pub fn propagate_init(
        &mut self,
        phases: &[f64],
        amplitudes: &[f64],
    ) -> Result<(), TemporalError> {
        validate_frame(phases, amplitudes)?;
        self.running_phases = Some(phases.iter().copied().map(wrap_phase).collect());
        self.running_amplitudes = Some(amplitudes.to_vec());
        Ok(())
    }

    /// Propagate a new frame, blending with the running state.
    ///
    /// On the first call, the running state is initialized to the input
    /// (no blending). On subsequent calls, the input is blended with the
    /// running state using the configured blending factors.
    ///
    /// Returns the blended `(phases, amplitudes)`.
    ///
    /// # Errors
    ///
    /// Returns [`TemporalError`] for empty inputs, length mismatches,
    /// non-finite values, or state size changes between frames.
    pub fn propagate(
        &mut self,
        phases: &[f64],
        amplitudes: &[f64],
    ) -> Result<(Vec<f64>, Vec<f64>), TemporalError> {
        validate_frame(phases, amplitudes)?;

        match (&self.running_phases, &self.running_amplitudes) {
            (Some(old_p), Some(old_a)) => {
                if phases.len() != old_p.len() {
                    return Err(TemporalError::StateSizeChanged {
                        expected: old_p.len(),
                        got: phases.len(),
                    });
                }

                let blended_p = self.phase_blender.blend(phases, old_p)?;
                let blended_a = self.amplitude_blender.blend(amplitudes, old_a)?;

                self.running_phases = Some(blended_p.clone());
                self.running_amplitudes = Some(blended_a.clone());

                Ok((blended_p, blended_a))
            }
            _ => {
                // First call: initialize
                let wrapped: Vec<f64> = phases.iter().copied().map(wrap_phase).collect();
                let amps = amplitudes.to_vec();
                self.running_phases = Some(wrapped.clone());
                self.running_amplitudes = Some(amps.clone());
                Ok((wrapped, amps))
            }
        }
    }

    /// Reset the propagator, discarding the running state.
    pub fn reset(&mut self) {
        self.running_phases = None;
        self.running_amplitudes = None;
    }
}

/// Validate a frame's phases and amplitudes.
fn validate_frame(phases: &[f64], amplitudes: &[f64]) -> Result<(), TemporalError> {
    if phases.is_empty() {
        return Err(TemporalError::EmptyInput { name: "phases" });
    }
    if phases.len() != amplitudes.len() {
        return Err(TemporalError::LengthMismatch {
            name_a: "phases",
            len_a: phases.len(),
            name_b: "amplitudes",
            len_b: amplitudes.len(),
        });
    }
    for (i, &p) in phases.iter().enumerate() {
        if !p.is_finite() {
            return Err(TemporalError::NonFiniteValue {
                name: "phases",
                index: i,
                value: p,
            });
        }
    }
    for (i, &a) in amplitudes.iter().enumerate() {
        if !a.is_finite() {
            return Err(TemporalError::NonFiniteValue {
                name: "amplitudes",
                index: i,
                value: a,
            });
        }
    }
    Ok(())
}

/// Clamp an amplitude to `[min, max]`, repairing non-finite values.
fn clamp_amp(amp: f64, min: f64, max: f64) -> f64 {
    if amp.is_nan() {
        return min;
    }
    if amp.is_infinite() {
        return if amp.is_sign_positive() { max } else { min };
    }
    amp.clamp(min, max)
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    use std::f64::consts::{PI, TAU};

    // --- ComplexPhasorBlender ---

    #[test]
    fn phasor_blender_alpha_one_returns_new() {
        let blender = ComplexPhasorBlender::new(1.0).unwrap();
        let new_p = [1.0, 2.0, 3.0];
        let old_p = [0.5, 1.5, 2.5];
        let result = blender.blend(&new_p, &old_p).unwrap();
        for (i, (&r, &n)) in result.iter().zip(new_p.iter()).enumerate() {
            assert_relative_eq!(r, wrap_phase(n), epsilon = 1e-12);
            let _ = i; // index used in loop
        }
    }

    #[test]
    fn phasor_blender_handles_wrap_around() {
        // Blending phase near 0 with phase near 2π should give ~0, not ~π
        let blender = ComplexPhasorBlender::new(0.5).unwrap();
        let result = blender.blend_scalar(0.1, TAU - 0.1).unwrap();
        // Should be close to 0 (wrapped), not close to π
        assert!(
            !(0.5..=TAU - 0.5).contains(&result),
            "wrap-around blend gave {result}, expected near 0 or 2π"
        );
    }

    #[test]
    fn phasor_blender_opposite_phases_gives_finite_result() {
        // Blending 0 and π with equal weight: the phasors nearly cancel.
        // The result is determined by floating-point residuals in cos(π)/sin(π),
        // so we only check that the output is finite and wrapped, not a specific value.
        let blender = ComplexPhasorBlender::new(0.5).unwrap();
        let result = blender.blend_scalar(0.0, PI).unwrap();
        assert!(result.is_finite());
        assert!(result >= 0.0);
        assert!(result < TAU + 1e-10);
    }

    #[test]
    fn phasor_blender_same_phase_preserved() {
        let blender = ComplexPhasorBlender::new(0.3).unwrap();
        let result = blender.blend_scalar(1.5, 1.5).unwrap();
        assert_relative_eq!(result, wrap_phase(1.5), epsilon = 1e-12);
    }

    #[test]
    fn phasor_blender_rejects_invalid_alpha() {
        assert!(ComplexPhasorBlender::new(0.0).is_err());
        assert!(ComplexPhasorBlender::new(-0.1).is_err());
        assert!(ComplexPhasorBlender::new(1.1).is_err());
        assert!(ComplexPhasorBlender::new(f64::NAN).is_err());
        assert!(ComplexPhasorBlender::new(f64::INFINITY).is_err());
    }

    #[test]
    fn phasor_blender_set_alpha_validates() {
        let mut b = ComplexPhasorBlender::new(0.5).unwrap();
        assert!(b.set_alpha(0.8).is_ok());
        assert_relative_eq!(b.alpha(), 0.8, epsilon = 1e-12);
        assert!(b.set_alpha(0.0).is_err());
        assert_relative_eq!(b.alpha(), 0.8, epsilon = 1e-12);
    }

    #[test]
    fn phasor_blender_empty_input_rejected() {
        let b = ComplexPhasorBlender::new(0.5).unwrap();
        assert!(b.blend(&[], &[1.0]).is_err());
    }

    #[test]
    fn phasor_blender_length_mismatch_rejected() {
        let b = ComplexPhasorBlender::new(0.5).unwrap();
        assert!(b.blend(&[1.0, 2.0], &[1.0]).is_err());
    }

    #[test]
    fn phasor_blender_non_finite_rejected() {
        let b = ComplexPhasorBlender::new(0.5).unwrap();
        assert!(b.blend(&[f64::NAN], &[1.0]).is_err());
        assert!(b.blend(&[1.0], &[f64::INFINITY]).is_err());
    }

    #[test]
    fn phasor_blender_scalar_non_finite_rejected() {
        let b = ComplexPhasorBlender::new(0.5).unwrap();
        assert!(b.blend_scalar(f64::NAN, 1.0).is_err());
        assert!(b.blend_scalar(1.0, f64::NAN).is_err());
    }

    // --- EmaAmplitudeBlender ---

    #[test]
    fn ema_blender_alpha_one_returns_new() {
        let b = EmaAmplitudeBlender::new(1.0).unwrap();
        let result = b.blend(&[2.0, 3.0], &[1.0, 1.0]).unwrap();
        assert_relative_eq!(result[0], 2.0, epsilon = 1e-12);
        assert_relative_eq!(result[1], 3.0, epsilon = 1e-12);
    }

    #[test]
    fn ema_blender_half_half() {
        let b = EmaAmplitudeBlender::new(0.5).unwrap();
        let result = b.blend(&[4.0], &[2.0]).unwrap();
        assert_relative_eq!(result[0], 3.0, epsilon = 1e-12);
    }

    #[test]
    fn ema_blender_clamps_output() {
        let b = EmaAmplitudeBlender::new(0.5).unwrap();
        // (0.5 * 100 + 0.5 * 100) = 100 → clamped to AMPLITUDE_MAX
        let result = b.blend(&[100.0], &[100.0]).unwrap();
        assert_relative_eq!(result[0], AMPLITUDE_MAX, epsilon = 1e-12);
    }

    #[test]
    fn ema_blender_with_clamp() {
        let b = EmaAmplitudeBlender::with_clamp(0.5, 0.5, 5.0).unwrap();
        let result = b.blend(&[10.0], &[0.1]).unwrap();
        // 0.5*10 + 0.5*0.1 = 5.05 → clamped to 5.0
        assert_relative_eq!(result[0], 5.0, epsilon = 1e-12);
    }

    #[test]
    fn ema_blender_rejects_invalid_alpha() {
        assert!(EmaAmplitudeBlender::new(0.0).is_err());
        assert!(EmaAmplitudeBlender::new(1.1).is_err());
    }

    #[test]
    fn ema_blender_empty_rejected() {
        let b = EmaAmplitudeBlender::new(0.5).unwrap();
        assert!(b.blend(&[], &[1.0]).is_err());
    }

    #[test]
    fn ema_blender_length_mismatch_rejected() {
        let b = EmaAmplitudeBlender::new(0.5).unwrap();
        assert!(b.blend(&[1.0, 2.0], &[1.0]).is_err());
    }

    #[test]
    fn ema_blender_non_finite_rejected() {
        let b = EmaAmplitudeBlender::new(0.5).unwrap();
        assert!(b.blend(&[f64::NAN], &[1.0]).is_err());
        assert!(b.blend(&[1.0], &[f64::INFINITY]).is_err());
    }

    // --- TemporalPropagator ---

    #[test]
    fn propagator_first_call_initializes() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        assert!(!prop.is_initialized());
        let (p, a) = prop.propagate(&[1.0, 2.0], &[3.0, 4.0]).unwrap();
        assert!(prop.is_initialized());
        assert_relative_eq!(p[0], wrap_phase(1.0), epsilon = 1e-12);
        assert_relative_eq!(p[1], wrap_phase(2.0), epsilon = 1e-12);
        assert_relative_eq!(a[0], 3.0, epsilon = 1e-12);
        assert_relative_eq!(a[1], 4.0, epsilon = 1e-12);
    }

    #[test]
    fn propagator_second_call_blends() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        let _ = prop.propagate(&[0.0], &[2.0]).unwrap();
        let (p, a) = prop.propagate(&[1.0], &[4.0]).unwrap();

        // Phase: blend(1.0, 0.0, α=0.5) via phasor
        let expected_p = ComplexPhasorBlender::new(0.5)
            .unwrap()
            .blend_scalar(1.0, 0.0)
            .unwrap();
        assert_relative_eq!(p[0], expected_p, epsilon = 1e-12);

        // Amplitude: EMA(4.0, 2.0, α=0.5) = 3.0
        assert_relative_eq!(a[0], 3.0, epsilon = 1e-12);
    }

    #[test]
    fn propagator_propagate_init_sets_state() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        prop.propagate_init(&[1.0, 2.0], &[3.0, 4.0]).unwrap();
        assert!(prop.is_initialized());
        let phases = prop.current_phases().unwrap();
        assert_relative_eq!(phases[0], wrap_phase(1.0), epsilon = 1e-12);
    }

    #[test]
    fn propagator_reset_clears_state() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        let _ = prop.propagate(&[1.0], &[2.0]).unwrap();
        assert!(prop.is_initialized());
        prop.reset();
        assert!(!prop.is_initialized());
        assert!(prop.current_phases().is_none());
    }

    #[test]
    fn propagator_state_size_change_rejected() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        let _ = prop.propagate(&[1.0, 2.0], &[3.0, 4.0]).unwrap();
        let err = prop.propagate(&[1.0], &[2.0]).unwrap_err();
        assert!(matches!(err, TemporalError::StateSizeChanged { .. }));
    }

    #[test]
    fn propagator_empty_input_rejected() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        assert!(prop.propagate(&[], &[]).is_err());
    }

    #[test]
    fn propagator_length_mismatch_rejected() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        assert!(prop.propagate(&[1.0, 2.0], &[1.0]).is_err());
    }

    #[test]
    fn propagator_non_finite_rejected() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        assert!(prop.propagate(&[f64::NAN], &[1.0]).is_err());
        assert!(prop.propagate(&[1.0], &[f64::INFINITY]).is_err());
    }

    #[test]
    fn propagator_separate_alpha() {
        let prop = TemporalPropagator::with_separate_alpha(0.8, 0.2).unwrap();
        assert_relative_eq!(prop.phase_alpha(), 0.8, epsilon = 1e-12);
        assert_relative_eq!(prop.amplitude_alpha(), 0.2, epsilon = 1e-12);
    }

    #[test]
    fn propagator_multiple_frames_converge() {
        // With repeated propagation of the same frame, the running state
        // should converge to that frame
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        let target_phase = 1.0_f64;
        let target_amp = 5.0_f64;

        // Initialize far from target
        let _ = prop.propagate(&[0.0], &[1.0]).unwrap();

        // Propagate target many times
        for _ in 0..50 {
            let _ = prop.propagate(&[target_phase], &[target_amp]).unwrap();
        }

        let p = prop.current_phases().unwrap();
        let a = prop.current_amplitudes().unwrap();
        assert_relative_eq!(p[0], wrap_phase(target_phase), epsilon = 1e-6);
        assert_relative_eq!(a[0], target_amp, epsilon = 1e-6);
    }

    // --- Serialization ---

    #[test]
    fn phasor_blender_serialization() {
        let b = ComplexPhasorBlender::new(0.7).unwrap();
        let json = serde_json::to_string(&b).unwrap();
        let restored: ComplexPhasorBlender = serde_json::from_str(&json).unwrap();
        assert_eq!(b, restored);
    }

    #[test]
    fn ema_blender_serialization() {
        let b = EmaAmplitudeBlender::new(0.3).unwrap();
        let json = serde_json::to_string(&b).unwrap();
        let restored: EmaAmplitudeBlender = serde_json::from_str(&json).unwrap();
        assert_eq!(b, restored);
    }

    #[test]
    fn propagator_serialization_preserves_state() {
        let mut prop = TemporalPropagator::new(0.5).unwrap();
        let _ = prop.propagate(&[1.0, 2.0], &[3.0, 4.0]).unwrap();
        let json = serde_json::to_string(&prop).unwrap();
        let restored: TemporalPropagator = serde_json::from_str(&json).unwrap();
        assert_eq!(prop, restored);
        assert!(restored.is_initialized());
    }

    // --- clamp_amp ---

    #[test]
    fn clamp_amp_repairs_non_finite() {
        assert_relative_eq!(clamp_amp(f64::NAN, 1e-6, 10.0), 1e-6, epsilon = 1e-12);
        assert_relative_eq!(clamp_amp(f64::INFINITY, 1e-6, 10.0), 10.0, epsilon = 1e-12);
        assert_relative_eq!(
            clamp_amp(f64::NEG_INFINITY, 1e-6, 10.0),
            1e-6,
            epsilon = 1e-12
        );
        assert_relative_eq!(clamp_amp(5.0, 1e-6, 10.0), 5.0, epsilon = 1e-12);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use crate::state::TAU;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn phasor_blend_output_is_wrapped(
            alpha in 0.01f64..=1.0,
            p1 in -100.0f64..100.0,
            p2 in -100.0f64..100.0,
        ) {
            let b = ComplexPhasorBlender::new(alpha).unwrap();
            let result = b.blend_scalar(p1, p2).unwrap();
            prop_assert!(result >= 0.0);
            prop_assert!(result < TAU + 1e-10);
        }
    }

    proptest! {
        #[test]
        fn ema_blend_output_in_clamp_range(
            alpha in 0.01f64..=1.0,
            a1 in 0.001f64..100.0,
            a2 in 0.001f64..100.0,
        ) {
            let b = EmaAmplitudeBlender::new(alpha).unwrap();
            let result = b.blend(&[a1], &[a2]).unwrap();
            prop_assert!(result[0] >= AMPLITUDE_MIN);
            prop_assert!(result[0] <= AMPLITUDE_MAX);
        }
    }

    proptest! {
        #[test]
        fn propagator_converges_to_constant_input(
            alpha in 0.2f64..=1.0,
            target_phase in 0.0f64..TAU,
            target_amp in 0.1f64..5.0,
        ) {
            let mut prop = TemporalPropagator::new(alpha).unwrap();
            // Initialize
            let _ = prop.propagate(&[0.0], &[1.0]).unwrap();
            // Propagate same target many times — enough for (1-α)^n < 1e-6
            for _ in 0..200 {
                let _ = prop.propagate(&[target_phase], &[target_amp]).unwrap();
            }
            let p = prop.current_phases().unwrap();
            let a = prop.current_amplitudes().unwrap();
            let wp = wrap_phase(target_phase);
            let phase_err = (p[0] - wp).abs().min(TAU - (p[0] - wp).abs());
            prop_assert!(phase_err < 1e-3, "phase err {phase_err}");
            prop_assert!((a[0] - target_amp).abs() < 1e-3, "amp err {}", (a[0] - target_amp).abs());
        }
    }

    proptest! {
        #[test]
        fn phase_continuity_small_perturbation(
            alpha in 0.1f64..=1.0,
            base_phase in 0.0f64..TAU,
        ) {
            let b = ComplexPhasorBlender::new(alpha).unwrap();
            let eps = 1e-10;
            let r1 = b.blend_scalar(base_phase, base_phase + 0.5).unwrap();
            let r2 = b.blend_scalar(base_phase + eps, base_phase + 0.5).unwrap();
            // Results should be very close (continuous)
            let diff = (r1 - r2).abs();
            let wrapped_diff = diff.min(TAU - diff);
            prop_assert!(wrapped_diff < 1e-6, "discontinuity: {wrapped_diff}");
        }
    }
}

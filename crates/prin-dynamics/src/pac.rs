//! Phase–amplitude coupling (PAC).
//!
//! Slow→fast modulation: `A_fast = A₀·[1 + m·cos(φ_slow + offset)]`.
//! Direct port of PRINet 3.0 `core/propagation/coupling.py`.
//!
//! The [`PhaseAmplitudeCoupling`] struct computes cross-frequency coupling
//! where the phase of a slow oscillator band modulates the amplitude of a
//! fast oscillator band. The mean slow-band phase drives a single modulation
//! factor that is broadcast across all fast oscillators, and the result is
//! clamped to the standard PRIN amplitude range `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::state::{AMPLITUDE_MAX, AMPLITUDE_MIN};

/// Errors raised by phase–amplitude coupling operations.
#[derive(Debug, Error)]
pub enum PacError {
    /// The modulation depth `m` is outside the permitted closed range `[0, 1]`.
    #[error("modulation_depth must be in [0, 1], got {value}")]
    InvalidModulationDepth {
        /// Offending modulation depth.
        value: f64,
    },

    /// A slice is empty.
    #[error("phase–amplitude coupling requires non-empty `{name}`")]
    EmptyInput {
        /// Name of the offending slice.
        name: &'static str,
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

    /// The phase offset is not finite.
    #[error("non-finite phase_offset: {value}")]
    InvalidPhaseOffset {
        /// Offending phase offset.
        value: f64,
    },
}

/// Phase–amplitude coupling between oscillator bands.
///
/// Implements cross-frequency coupling where the phase of a slow
/// oscillator band modulates the amplitude of a fast oscillator band:
///
/// `A_fast(t) = A_0 · [1 + m · cos(φ_slow(t) + φ_offset)]`
///
/// where `m` is the modulation depth and `φ_offset` is a phase offset.
///
/// The modulation uses the **mean** slow-band phase, matching PRINet 3.0
/// `PhaseAmplitudeCoupling.modulate`. Output amplitudes are clamped to
/// `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
///
/// # Example
///
/// ```
/// use prin_dynamics::pac::PhaseAmplitudeCoupling;
///
/// let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
/// let slow_phase = [0.0_f64, 1.0, 2.0, 3.0];
/// let fast_amp = [1.0_f64, 2.0, 3.0, 4.0];
/// let out = pac.modulate(&slow_phase, &fast_amp, 0.0).unwrap();
/// assert_eq!(out.len(), 4);
/// ```
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PhaseAmplitudeCoupling {
    /// Modulation depth `m ∈ [0, 1]`.
    modulation_depth: f64,
    /// Amplitude clamp minimum (matches `AMPLITUDE_MIN`).
    amp_min: f64,
    /// Amplitude clamp maximum (matches `AMPLITUDE_MAX`).
    amp_max: f64,
}

impl PhaseAmplitudeCoupling {
    /// Create a new PAC with modulation depth `m` and the standard PRIN
    /// amplitude clamp `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
    ///
    /// # Errors
    ///
    /// Returns [`PacError::InvalidModulationDepth`] if `modulation_depth`
    /// is not finite or outside `[0, 1]`.
    pub fn new(modulation_depth: f64) -> Result<Self, PacError> {
        Self::with_clamp(modulation_depth, AMPLITUDE_MIN, AMPLITUDE_MAX)
    }

    /// Create a new PAC with a custom amplitude clamp range.
    ///
    /// # Errors
    ///
    /// Returns [`PacError::InvalidModulationDepth`] if `modulation_depth`
    /// is not finite or outside `[0, 1]`.
    pub fn with_clamp(modulation_depth: f64, amp_min: f64, amp_max: f64) -> Result<Self, PacError> {
        if !modulation_depth.is_finite() || !(0.0..=1.0).contains(&modulation_depth) {
            return Err(PacError::InvalidModulationDepth {
                value: modulation_depth,
            });
        }
        Ok(Self {
            modulation_depth,
            amp_min,
            amp_max,
        })
    }

    /// Current modulation depth `m`.
    pub fn modulation_depth(&self) -> f64 {
        self.modulation_depth
    }

    /// Set the modulation depth `m`.
    ///
    /// # Errors
    ///
    /// Returns [`PacError::InvalidModulationDepth`] if `value` is not finite
    /// or outside `[0, 1]`.
    pub fn set_modulation_depth(&mut self, value: f64) -> Result<(), PacError> {
        if !value.is_finite() || !(0.0..=1.0).contains(&value) {
            return Err(PacError::InvalidModulationDepth { value });
        }
        self.modulation_depth = value;
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

    /// Apply PAC modulation to fast-band amplitudes.
    ///
    /// Each fast oscillator's amplitude is modulated by the mean phase
    /// of the slow band:
    ///
    /// `A_out = A_in · [1 + m · cos(mean(φ_slow) + offset)]`
    ///
    /// The modulation factor is broadcast across all fast oscillators.
    /// Output amplitudes are clamped to `[amp_min, amp_max]`.
    ///
    /// # Arguments
    ///
    /// * `slow_phase` — phase of slow oscillators, any length `≥ 1`.
    /// * `fast_amplitude` — amplitude of fast oscillators, any length `≥ 1`.
    /// * `phase_offset` — phase offset for modulation.
    ///
    /// # Errors
    ///
    /// Returns [`PacError`] if `slow_phase` or `fast_amplitude` is empty,
    /// if any value is non-finite, or if `phase_offset` is non-finite.
    pub fn modulate(
        &self,
        slow_phase: &[f64],
        fast_amplitude: &[f64],
        phase_offset: f64,
    ) -> Result<Vec<f64>, PacError> {
        if slow_phase.is_empty() {
            return Err(PacError::EmptyInput { name: "slow_phase" });
        }
        if fast_amplitude.is_empty() {
            return Err(PacError::EmptyInput {
                name: "fast_amplitude",
            });
        }
        if !phase_offset.is_finite() {
            return Err(PacError::InvalidPhaseOffset {
                value: phase_offset,
            });
        }

        // Compute mean slow phase (over the oscillator dimension).
        let mut sum = 0.0_f64;
        for (i, &p) in slow_phase.iter().enumerate() {
            if !p.is_finite() {
                return Err(PacError::NonFiniteValue {
                    name: "slow_phase",
                    index: i,
                    value: p,
                });
            }
            sum += p;
        }
        let mean_slow = sum / (slow_phase.len() as f64);

        // Modulation factor: 1 + m · cos(mean_slow + offset).
        let modulation = 1.0 + self.modulation_depth * (mean_slow + phase_offset).cos();

        // Broadcast modulation across fast oscillators and clamp.
        let mut out = Vec::with_capacity(fast_amplitude.len());
        for (i, &a) in fast_amplitude.iter().enumerate() {
            if !a.is_finite() {
                return Err(PacError::NonFiniteValue {
                    name: "fast_amplitude",
                    index: i,
                    value: a,
                });
            }
            let modulated = a * modulation;
            out.push(clamp_amplitude_to(modulated, self.amp_min, self.amp_max));
        }
        Ok(out)
    }
}

impl Default for PhaseAmplitudeCoupling {
    fn default() -> Self {
        // Default matches PRINet 3.0: m = 0.3, clamp (1e-6, 10.0).
        Self {
            modulation_depth: 0.3,
            amp_min: AMPLITUDE_MIN,
            amp_max: AMPLITUDE_MAX,
        }
    }
}

/// Clamp an amplitude to `[min, max]`, repairing non-finite values.
///
/// `NaN` becomes `min`; `+Inf` becomes `max`; `-Inf` becomes `min`.
fn clamp_amplitude_to(amp: f64, min: f64, max: f64) -> f64 {
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

    #[test]
    fn default_matches_prinet() {
        let pac = PhaseAmplitudeCoupling::default();
        assert_relative_eq!(pac.modulation_depth(), 0.3, epsilon = 1e-12);
        assert_relative_eq!(pac.amp_min(), AMPLITUDE_MIN, epsilon = 1e-12);
        assert_relative_eq!(pac.amp_max(), AMPLITUDE_MAX, epsilon = 1e-12);
    }

    #[test]
    fn new_validates_modulation_depth() {
        assert!(PhaseAmplitudeCoupling::new(0.0).is_ok());
        assert!(PhaseAmplitudeCoupling::new(1.0).is_ok());
        assert!(PhaseAmplitudeCoupling::new(0.5).is_ok());
        assert!(PhaseAmplitudeCoupling::new(-0.1).is_err());
        assert!(PhaseAmplitudeCoupling::new(1.1).is_err());
        assert!(PhaseAmplitudeCoupling::new(f64::NAN).is_err());
        assert!(PhaseAmplitudeCoupling::new(f64::INFINITY).is_err());
    }

    #[test]
    fn set_modulation_depth_validates() {
        let mut pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        assert!(pac.set_modulation_depth(0.7).is_ok());
        assert_relative_eq!(pac.modulation_depth(), 0.7, epsilon = 1e-12);
        assert!(pac.set_modulation_depth(2.0).is_err());
        assert_relative_eq!(pac.modulation_depth(), 0.7, epsilon = 1e-12);
    }

    #[test]
    fn modulate_basic_matches_prinet_reference() {
        // PRINet 3.0 reference: m=0.5, slow=[0,1,2,3], fast=[1,2,3,4], offset=0
        // mean_slow = 1.5, modulation = 1 + 0.5*cos(1.5) = 1.0353686008338514
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let slow = [0.0_f64, 1.0, 2.0, 3.0];
        let fast = [1.0_f64, 2.0, 3.0, 4.0];
        let out = pac.modulate(&slow, &fast, 0.0).unwrap();
        let expected = [
            1.0353686008338514,
            2.070737201667703,
            3.1061058025015544,
            4.141474403335406,
        ];
        assert_eq!(out.len(), 4);
        for (a, &e) in out.iter().zip(expected.iter()) {
            assert_relative_eq!(*a, e, epsilon = 1e-12);
        }
    }

    #[test]
    fn modulate_with_offset_matches_prinet_reference() {
        // PRINet 3.0 reference: m=0.5, slow=[0,1,2,3], fast=[1,2,3,4], offset=0.5
        // modulation = 1 + 0.5*cos(2.0) = 0.7919265817264288
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let slow = [0.0_f64, 1.0, 2.0, 3.0];
        let fast = [1.0_f64, 2.0, 3.0, 4.0];
        let out = pac.modulate(&slow, &fast, 0.5).unwrap();
        let expected = [
            0.7919265817264288,
            1.5838531634528576,
            2.3757797451792864,
            3.1677063269057153,
        ];
        for (a, &e) in out.iter().zip(expected.iter()) {
            assert_relative_eq!(*a, e, epsilon = 1e-12);
        }
    }

    #[test]
    fn modulate_default_depth_matches_prinet_reference() {
        // PRINet 3.0 default: m=0.3, slow=[0,1,2,3], fast=[1,2,3,4], offset=0
        // modulation = 1 + 0.3*cos(1.5) = 1.021221160500311
        let pac = PhaseAmplitudeCoupling::default();
        let slow = [0.0_f64, 1.0, 2.0, 3.0];
        let fast = [1.0_f64, 2.0, 3.0, 4.0];
        let out = pac.modulate(&slow, &fast, 0.0).unwrap();
        let expected = [
            1.021221160500311,
            2.042442321000622,
            3.063663481500933,
            4.084884642001244,
        ];
        for (a, &e) in out.iter().zip(expected.iter()) {
            assert_relative_eq!(*a, e, epsilon = 1e-12);
        }
    }

    #[test]
    fn modulate_different_sizes_matches_prinet_reference() {
        // PRINet 3.0: m=0.5, slow=[0,1,2] (mean=1.0), fast=[1,2,3,4,5], offset=0
        // modulation = 1 + 0.5*cos(1.0) = 1.2701511529340699
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let slow = [0.0_f64, 1.0, 2.0];
        let fast = [1.0_f64, 2.0, 3.0, 4.0, 5.0];
        let out = pac.modulate(&slow, &fast, 0.0).unwrap();
        let expected = [
            1.2701511529340699,
            2.5403023058681398,
            3.8104534588022094,
            5.0806046117362795,
            6.35075576467035,
        ];
        assert_eq!(out.len(), 5);
        for (a, &e) in out.iter().zip(expected.iter()) {
            assert_relative_eq!(*a, e, epsilon = 1e-12);
        }
    }

    #[test]
    fn modulate_single_oscillator_matches_prinet_reference() {
        // PRINet 3.0: m=0.5, slow=[0.5], fast=[2.0], offset=0.3
        // modulation = 1 + 0.5*cos(0.8) = 1.3483533546735826
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let out = pac.modulate(&[0.5], &[2.0], 0.3).unwrap();
        assert_relative_eq!(out[0], 2.6967067093471653, epsilon = 1e-12);
    }

    #[test]
    fn modulate_max_depth_matches_prinet_reference() {
        // PRINet 3.0: m=1.0, slow=[0], fast=[5], offset=0 → 5*(1+cos(0)) = 10
        let pac = PhaseAmplitudeCoupling::new(1.0).unwrap();
        let out = pac.modulate(&[0.0], &[5.0], 0.0).unwrap();
        assert_relative_eq!(out[0], 10.0, epsilon = 1e-12);
    }

    #[test]
    fn modulate_zero_depth_is_identity() {
        // PRINet 3.0: m=0.0, slow=[1.0], fast=[3.0], offset=0.5 → 3.0
        let pac = PhaseAmplitudeCoupling::new(0.0).unwrap();
        let out = pac.modulate(&[1.0], &[3.0], 0.5).unwrap();
        assert_relative_eq!(out[0], 3.0, epsilon = 1e-12);
    }

    #[test]
    fn modulate_clamps_large_amplitude() {
        // PRINet 3.0: m=0.5, slow=[0,1], fast=[100,200], offset=0 → clamped to 10
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let out = pac.modulate(&[0.0, 1.0], &[100.0, 200.0], 0.0).unwrap();
        assert_relative_eq!(out[0], AMPLITUDE_MAX, epsilon = 1e-12);
        assert_relative_eq!(out[1], AMPLITUDE_MAX, epsilon = 1e-12);
    }

    #[test]
    fn modulate_clamps_tiny_amplitude() {
        // PRINet 3.0: m=0.5, slow=[0,1], fast=[1e-8,1e-9], offset=0 → clamped to 1e-6
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let out = pac.modulate(&[0.0, 1.0], &[1e-8, 1e-9], 0.0).unwrap();
        assert_relative_eq!(out[0], AMPLITUDE_MIN, epsilon = 1e-12);
        assert_relative_eq!(out[1], AMPLITUDE_MIN, epsilon = 1e-12);
    }

    #[test]
    fn modulate_rejects_empty_slow_phase() {
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let err = pac.modulate(&[], &[1.0], 0.0).unwrap_err();
        assert!(matches!(err, PacError::EmptyInput { name: "slow_phase" }));
    }

    #[test]
    fn modulate_rejects_empty_fast_amplitude() {
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let err = pac.modulate(&[0.0], &[], 0.0).unwrap_err();
        assert!(matches!(
            err,
            PacError::EmptyInput {
                name: "fast_amplitude"
            }
        ));
    }

    #[test]
    fn modulate_rejects_non_finite_slow_phase() {
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let err = pac.modulate(&[0.0, f64::NAN], &[1.0], 0.0).unwrap_err();
        assert!(matches!(
            err,
            PacError::NonFiniteValue {
                name: "slow_phase",
                index: 1,
                ..
            }
        ));
    }

    #[test]
    fn modulate_rejects_non_finite_fast_amplitude() {
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let err = pac
            .modulate(&[0.0], &[1.0, f64::INFINITY], 0.0)
            .unwrap_err();
        assert!(matches!(
            err,
            PacError::NonFiniteValue {
                name: "fast_amplitude",
                index: 1,
                ..
            }
        ));
    }

    #[test]
    fn modulate_rejects_non_finite_phase_offset() {
        let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
        let err = pac.modulate(&[0.0], &[1.0], f64::NAN).unwrap_err();
        assert!(matches!(err, PacError::InvalidPhaseOffset { .. }));
    }

    #[test]
    fn with_clamp_allows_custom_range() {
        let pac = PhaseAmplitudeCoupling::with_clamp(0.5, 0.01, 5.0).unwrap();
        let out = pac.modulate(&[0.0], &[100.0], 0.0).unwrap();
        assert_relative_eq!(out[0], 5.0, epsilon = 1e-12);
        let out2 = pac.modulate(&[0.0], &[0.001], 0.0).unwrap();
        assert_relative_eq!(out2[0], 0.01, epsilon = 1e-12);
    }

    #[test]
    fn serialization_roundtrip() {
        let pac = PhaseAmplitudeCoupling::new(0.7).unwrap();
        let json = serde_json::to_string(&pac).unwrap();
        let restored: PhaseAmplitudeCoupling = serde_json::from_str(&json).unwrap();
        assert_eq!(pac, restored);
    }

    #[test]
    fn clamp_amplitude_to_repairs_non_finite() {
        assert_relative_eq!(
            clamp_amplitude_to(f64::NAN, 1e-6, 10.0),
            1e-6,
            epsilon = 1e-12
        );
        assert_relative_eq!(
            clamp_amplitude_to(f64::INFINITY, 1e-6, 10.0),
            10.0,
            epsilon = 1e-12
        );
        assert_relative_eq!(
            clamp_amplitude_to(f64::NEG_INFINITY, 1e-6, 10.0),
            1e-6,
            epsilon = 1e-12
        );
        assert_relative_eq!(clamp_amplitude_to(5.0, 1e-6, 10.0), 5.0, epsilon = 1e-12);
    }

    #[test]
    fn modulate_preserves_clamp_invariant() {
        let pac = PhaseAmplitudeCoupling::new(1.0).unwrap();
        let slow = [0.0_f64; 3];
        let fast = [0.5_f64, 5.0, 50.0];
        let out = pac.modulate(&slow, &fast, 0.0).unwrap();
        for &a in &out {
            assert!(a >= AMPLITUDE_MIN);
            assert!(a <= AMPLITUDE_MAX);
        }
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn modulate_output_in_clamp_range(
            m in 0.0f64..=1.0,
            offset in -core::f64::consts::TAU..core::f64::consts::TAU,
            n_slow in 1usize..=16,
            n_fast in 1usize..=16,
        ) {
            let pac = PhaseAmplitudeCoupling::new(m).unwrap();
            let slow: Vec<f64> = (0..n_slow).map(|i| (i as f64) * 0.3).collect();
            let fast: Vec<f64> = (0..n_fast).map(|i| ((i + 1) as f64) * 0.5).collect();
            let out = pac.modulate(&slow, &fast, offset).unwrap();
            prop_assert_eq!(out.len(), n_fast);
            for &a in &out {
                prop_assert!(a.is_finite());
                prop_assert!(a >= AMPLITUDE_MIN);
                prop_assert!(a <= AMPLITUDE_MAX);
            }
        }
    }

    proptest! {
        #[test]
        fn zero_depth_is_identity(
            offset in -10.0f64..=10.0,
            n_slow in 1usize..=8,
            n_fast in 1usize..=8,
        ) {
            let pac = PhaseAmplitudeCoupling::new(0.0).unwrap();
            let slow: Vec<f64> = (0..n_slow).map(|i| (i as f64) * 0.7).collect();
            let fast: Vec<f64> = (0..n_fast).map(|i| ((i + 1) as f64) * 0.3).collect();
            let out = pac.modulate(&slow, &fast, offset).unwrap();
            for (a, &f) in out.iter().zip(fast.iter()) {
                let clamped = f.clamp(AMPLITUDE_MIN, AMPLITUDE_MAX);
                prop_assert!((a - clamped).abs() < 1e-12);
            }
        }
    }
}

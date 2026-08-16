//! Phase–amplitude coupling (PAC) modulation: a CPU reference and (behind
//! the `cpu`/`cuda`/`wgpu` features) a single-source CubeCL kernel set for
//! CUDA, wgpu, and CPU-SIMD backends.
//!
//! Slow→fast modulation: `A_fast = A0 * [1 + m * cos(mean(phase_slow) + offset)]`,
//! matching `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate` (`f64`,
//! CPU-only) — this crate provides the `f32` GPU-dispatchable counterpart.
//! See the crate's S1 handoff note for the parity-evidence disposition
//! (cross-crate equivalence test in this module's `tests`).
//!
//! # Two-stage kernel
//!
//! 1. **Reduction:** the mean slow-band phase is a single scalar shared by
//!    every fast oscillator. The [`cubecl`] submodule's
//!    `pac_phase_sum_block_reduce` kernel mirrors `mean_field_rk4::cubecl`'s
//!    `order_param_block_reduce` hierarchical design (one `f32` partial sum
//!    per 256-thread cube block; the host finishes the reduction and the
//!    `cos` in `f64` before downcasting to `f32` — Coding Standards §2.2),
//!    but reduces a single real-valued array (`phase_slow`) instead of a
//!    complex weighted sum.
//! 2. **Broadcast + clamp:** the `pac_modulate` kernel multiplies every
//!    fast-band amplitude by the host-computed scalar modulation factor and
//!    clamps to `[amp_min, amp_max]`.

use thiserror::Error;

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
pub mod cubecl;

/// Parameters for PAC modulation.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PacParams {
    /// Modulation depth `m`, expected in `[0, 1]` (not enforced here; see
    /// `prin_dynamics::pac::PhaseAmplitudeCoupling::new` for the validated
    /// constructor this crate's callers are expected to have already gone
    /// through).
    pub modulation_depth: f32,
    /// Phase offset added to the mean slow phase before the cosine.
    pub phase_offset: f32,
    /// Output amplitude clamp minimum.
    pub amp_min: f32,
    /// Output amplitude clamp maximum.
    pub amp_max: f32,
}

impl PacParams {
    /// PAC parameters with the standard PRIN amplitude clamp
    /// (`prin_dynamics::state::AMPLITUDE_MIN`/`AMPLITUDE_MAX`, matching
    /// `PhaseAmplitudeCoupling::default`'s clamp range) and the given
    /// modulation depth and zero phase offset.
    pub fn new(modulation_depth: f32) -> Self {
        Self {
            modulation_depth,
            phase_offset: 0.0,
            amp_min: prin_dynamics::state::AMPLITUDE_MIN as f32,
            amp_max: prin_dynamics::state::AMPLITUDE_MAX as f32,
        }
    }
}

/// Errors raised by the PAC modulation kernels.
#[derive(Debug, Error)]
pub enum PacError {
    /// `slow_phase` is empty.
    #[error("PAC modulation requires non-empty slow_phase")]
    EmptySlowPhase,
    /// `fast_amplitude` is empty.
    #[error("PAC modulation requires non-empty fast_amplitude")]
    EmptyFastAmplitude,
    /// A `slow_phase` value is non-finite.
    #[error("non-finite value in slow_phase at index {index}: {value}")]
    NonFiniteSlowPhase {
        /// Offending index.
        index: usize,
        /// Offending value.
        value: f32,
    },
    /// A `fast_amplitude` value is non-finite.
    #[error("non-finite value in fast_amplitude at index {index}: {value}")]
    NonFiniteFastAmplitude {
        /// Offending index.
        index: usize,
        /// Offending value.
        value: f32,
    },
    /// A scalar parameter is non-finite.
    #[error("non-finite parameter: {name} = {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// The amplitude clamp range is invalid (`amp_min > amp_max`).
    #[error(
        "invalid clamp range: amp_min={amp_min}, amp_max={amp_max} (require amp_min <= amp_max)"
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
    /// The requested compute backend (wgpu/CUDA) is not available on this host.
    #[error("backend unavailable: {name}")]
    BackendUnavailable {
        /// Backend name.
        name: &'static str,
    },
}

/// Validate PAC inputs; returns nothing (side-effecting checks only).
fn validate_inputs(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<(), PacError> {
    if slow_phase.is_empty() {
        return Err(PacError::EmptySlowPhase);
    }
    if fast_amplitude.is_empty() {
        return Err(PacError::EmptyFastAmplitude);
    }
    for (i, &p) in slow_phase.iter().enumerate() {
        if !p.is_finite() {
            return Err(PacError::NonFiniteSlowPhase { index: i, value: p });
        }
    }
    for (i, &a) in fast_amplitude.iter().enumerate() {
        if !a.is_finite() {
            return Err(PacError::NonFiniteFastAmplitude { index: i, value: a });
        }
    }
    if !params.modulation_depth.is_finite() {
        return Err(PacError::NonFiniteParameter {
            name: "modulation_depth",
            value: params.modulation_depth,
        });
    }
    if !params.phase_offset.is_finite() {
        return Err(PacError::NonFiniteParameter {
            name: "phase_offset",
            value: params.phase_offset,
        });
    }
    if !params.amp_min.is_finite() || !params.amp_max.is_finite() {
        return Err(PacError::InvalidClampRange {
            amp_min: params.amp_min,
            amp_max: params.amp_max,
        });
    }
    if params.amp_min > params.amp_max {
        return Err(PacError::InvalidClampRange {
            amp_min: params.amp_min,
            amp_max: params.amp_max,
        });
    }
    Ok(())
}

/// Compute the scalar modulation factor `1 + m * cos(mean(slow_phase) + offset)`.
///
/// The mean accumulates in `f64` (Coding Standards §2.2) before downcasting
/// to `f32`; the cosine and final combine are `f32`, matching the GPU path's
/// host-side finish exactly (see the module documentation).
fn modulation_factor(slow_phase: &[f32], params: &PacParams) -> f32 {
    let mut sum = 0.0_f64;
    for &p in slow_phase {
        sum += f64::from(p);
    }
    let mean = (sum / slow_phase.len() as f64) as f32;
    1.0 + params.modulation_depth * (mean + params.phase_offset).cos()
}

/// Apply PAC modulation to fast-band amplitudes on the CPU (numerical
/// authority).
///
/// `A_out_i = clamp(A_fast_i * [1 + m * cos(mean(phase_slow) + offset)], amp_min, amp_max)`.
///
/// The modulation factor is broadcast across every fast oscillator, matching
/// `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate`'s semantics.
///
/// # Errors
///
/// Returns [`PacError`] if `slow_phase` or `fast_amplitude` is empty, any
/// value or parameter is non-finite, or the clamp range is inverted.
pub fn pac_modulate_cpu(
    slow_phase: &[f32],
    fast_amplitude: &[f32],
    params: &PacParams,
) -> Result<Vec<f32>, PacError> {
    validate_inputs(slow_phase, fast_amplitude, params)?;
    let modulation = modulation_factor(slow_phase, params);
    Ok(fast_amplitude
        .iter()
        .map(|&a| (a * modulation).clamp(params.amp_min, params.amp_max))
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn modulate_basic_matches_closed_form() {
        let params = PacParams {
            modulation_depth: 0.5,
            phase_offset: 0.0,
            amp_min: -100.0,
            amp_max: 100.0,
        };
        let slow = [0.0_f32, 1.0, 2.0, 3.0];
        let fast = [1.0_f32, 2.0, 3.0, 4.0];
        let out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
        // mean_slow = 1.5, modulation = 1 + 0.5*cos(1.5)
        let expected_modulation = 1.0 + 0.5 * 1.5_f32.cos();
        for (o, f) in out.iter().zip(fast.iter()) {
            assert_relative_eq!(*o, f * expected_modulation, epsilon = 1e-5);
        }
    }

    #[test]
    fn modulate_clamps_output() {
        let params = PacParams {
            modulation_depth: 0.5,
            phase_offset: 0.0,
            amp_min: 1e-6,
            amp_max: 10.0,
        };
        let out = pac_modulate_cpu(&[0.0, 1.0], &[100.0, 200.0], &params).unwrap();
        assert_relative_eq!(out[0], 10.0, epsilon = 1e-6);
        assert_relative_eq!(out[1], 10.0, epsilon = 1e-6);

        let out2 = pac_modulate_cpu(&[0.0, 1.0], &[1e-8, 1e-9], &params).unwrap();
        assert_relative_eq!(out2[0], 1e-6, epsilon = 1e-9);
        assert_relative_eq!(out2[1], 1e-6, epsilon = 1e-9);
    }

    #[test]
    fn zero_depth_is_identity_within_clamp() {
        let params = PacParams {
            modulation_depth: 0.0,
            phase_offset: 0.5,
            amp_min: -100.0,
            amp_max: 100.0,
        };
        let out = pac_modulate_cpu(&[1.0], &[3.0], &params).unwrap();
        assert_relative_eq!(out[0], 3.0, epsilon = 1e-6);
    }

    #[test]
    fn new_uses_standard_clamp() {
        let params = PacParams::new(0.3);
        assert_relative_eq!(params.modulation_depth, 0.3, epsilon = 1e-6);
        assert_relative_eq!(
            params.amp_min,
            prin_dynamics::state::AMPLITUDE_MIN as f32,
            epsilon = 1e-9
        );
        assert_relative_eq!(
            params.amp_max,
            prin_dynamics::state::AMPLITUDE_MAX as f32,
            epsilon = 1e-9
        );
    }

    #[test]
    fn rejects_empty_slow_phase() {
        let params = PacParams::new(0.5);
        let err = pac_modulate_cpu(&[], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::EmptySlowPhase));
    }

    #[test]
    fn rejects_empty_fast_amplitude() {
        let params = PacParams::new(0.5);
        let err = pac_modulate_cpu(&[0.0], &[], &params).unwrap_err();
        assert!(matches!(err, PacError::EmptyFastAmplitude));
    }

    #[test]
    fn rejects_non_finite_slow_phase() {
        let params = PacParams::new(0.5);
        let err = pac_modulate_cpu(&[0.0, f32::NAN], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::NonFiniteSlowPhase { index: 1, .. }));
    }

    #[test]
    fn rejects_non_finite_fast_amplitude() {
        let params = PacParams::new(0.5);
        let err = pac_modulate_cpu(&[0.0], &[1.0, f32::INFINITY], &params).unwrap_err();
        assert!(matches!(
            err,
            PacError::NonFiniteFastAmplitude { index: 1, .. }
        ));
    }

    #[test]
    fn rejects_non_finite_modulation_depth() {
        let mut params = PacParams::new(0.5);
        params.modulation_depth = f32::NAN;
        let err = pac_modulate_cpu(&[0.0], &[1.0], &params).unwrap_err();
        assert!(matches!(
            err,
            PacError::NonFiniteParameter {
                name: "modulation_depth",
                ..
            }
        ));
    }

    #[test]
    fn rejects_non_finite_phase_offset() {
        let mut params = PacParams::new(0.5);
        params.phase_offset = f32::NAN;
        let err = pac_modulate_cpu(&[0.0], &[1.0], &params).unwrap_err();
        assert!(matches!(
            err,
            PacError::NonFiniteParameter {
                name: "phase_offset",
                ..
            }
        ));
    }

    #[test]
    fn rejects_inverted_clamp_range() {
        let params = PacParams {
            modulation_depth: 0.5,
            phase_offset: 0.0,
            amp_min: 5.0,
            amp_max: 0.01,
        };
        let err = pac_modulate_cpu(&[0.0], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::InvalidClampRange { .. }));
    }

    #[test]
    fn rejects_non_finite_clamp_bounds() {
        let params = PacParams {
            modulation_depth: 0.5,
            phase_offset: 0.0,
            amp_min: f32::NAN,
            amp_max: 1.0,
        };
        let err = pac_modulate_cpu(&[0.0], &[1.0], &params).unwrap_err();
        assert!(matches!(err, PacError::InvalidClampRange { .. }));
    }

    #[test]
    fn allows_equal_clamp_bounds() {
        let params = PacParams {
            modulation_depth: 0.5,
            phase_offset: 0.0,
            amp_min: 2.0,
            amp_max: 2.0,
        };
        let out = pac_modulate_cpu(&[0.0], &[100.0], &params).unwrap();
        assert_relative_eq!(out[0], 2.0, epsilon = 1e-9);
    }

    // ── Cross-crate parity: prin_dynamics::pac::PhaseAmplitudeCoupling ─────

    #[test]
    fn parity_against_prin_dynamics_phase_amplitude_coupling() {
        use prin_dynamics::pac::PhaseAmplitudeCoupling;

        let m = 0.5_f64;
        let offset = 0.3_f64;
        let slow64 = [0.0_f64, 1.0, 2.0, 3.0];
        let fast64 = [1.0_f64, 2.0, 3.0, 4.0];

        let reference = PhaseAmplitudeCoupling::new(m).unwrap();
        let expected = reference.modulate(&slow64, &fast64, offset).unwrap();

        let slow32: Vec<f32> = slow64.iter().map(|&p| p as f32).collect();
        let fast32: Vec<f32> = fast64.iter().map(|&a| a as f32).collect();
        let params = PacParams {
            modulation_depth: m as f32,
            phase_offset: offset as f32,
            amp_min: prin_dynamics::state::AMPLITUDE_MIN as f32,
            amp_max: prin_dynamics::state::AMPLITUDE_MAX as f32,
        };
        let out = pac_modulate_cpu(&slow32, &fast32, &params).unwrap();

        for i in 0..expected.len() {
            assert!(
                (f64::from(out[i]) - expected[i]).abs() < 1e-4,
                "index {i}: prin-kernels={}, prin-dynamics={}",
                out[i],
                expected[i]
            );
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
            m in 0.0f32..=1.0,
            offset in -core::f32::consts::TAU..core::f32::consts::TAU,
            n_slow in 1usize..=16,
            n_fast in 1usize..=16,
        ) {
            let params = PacParams {
                modulation_depth: m,
                phase_offset: offset,
                amp_min: 1e-6,
                amp_max: 10.0,
            };
            let slow: Vec<f32> = (0..n_slow).map(|i| (i as f32) * 0.3).collect();
            let fast: Vec<f32> = (0..n_fast).map(|i| ((i + 1) as f32) * 0.5).collect();
            let out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
            prop_assert_eq!(out.len(), n_fast);
            for &a in &out {
                prop_assert!(a.is_finite());
                prop_assert!(a >= params.amp_min);
                prop_assert!(a <= params.amp_max);
            }
        }
    }

    proptest! {
        #[test]
        fn zero_depth_is_identity_within_clamp(
            offset in -10.0f32..=10.0,
            n_slow in 1usize..=8,
            n_fast in 1usize..=8,
        ) {
            let params = PacParams {
                modulation_depth: 0.0,
                phase_offset: offset,
                amp_min: 1e-6,
                amp_max: 10.0,
            };
            let slow: Vec<f32> = (0..n_slow).map(|i| (i as f32) * 0.7).collect();
            let fast: Vec<f32> = (0..n_fast).map(|i| ((i + 1) as f32) * 0.3).collect();
            let out = pac_modulate_cpu(&slow, &fast, &params).unwrap();
            for (a, &f) in out.iter().zip(fast.iter()) {
                let clamped = f.clamp(params.amp_min, params.amp_max);
                prop_assert!((a - clamped).abs() < 1e-5);
            }
        }
    }
}

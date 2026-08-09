//! Kuramoto order parameters and inter-frame phase correlation.
//!
//! Rebuild of PRINet 3.0 `core/measurement.py::kuramoto_order_parameter`,
//! `kuramoto_order_parameter_complex`, and `inter_frame_phase_correlation`.
//! All reductions run in f64 (PRINet computes these in `torch.float64`), so
//! single-runtime parity targets `rtol = 1e-10`.

use num_complex::Complex64;

use crate::error::{require_finite, MetricError};

/// Compute the Kuramoto order parameter `r = |1/N Σᵢ exp(iφᵢ)|`.
///
/// `r = 0` indicates incoherence and `r = 1` full phase synchronization. The
/// result is clamped to `[0, 1]`: the exact value lies in that interval, but
/// floating-point accumulation can exceed it by ~1 ulp (WP-010 acceptance
/// invariant `R ∈ [0, 1]`).
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for an empty slice and
/// [`MetricError::NonFiniteValue`] for a non-finite phase.
///
/// # Example
///
/// ```
/// use prin_metrics::kuramoto_order_parameter;
///
/// let synchronized = vec![0.5_f64; 100];
/// let r = kuramoto_order_parameter(&synchronized).unwrap();
/// assert!((r - 1.0).abs() < 1e-12);
/// ```
pub fn kuramoto_order_parameter(phase: &[f64]) -> Result<f64, MetricError> {
    let z = kuramoto_order_parameter_complex(phase)?;
    Ok(z.norm().min(1.0))
}

/// Compute the complex Kuramoto order parameter `Z = 1/N Σᵢ exp(iφᵢ)`.
///
/// Returns the full complex mean field `Z = r·exp(iψ)` where `r` is the
/// synchronization magnitude and `ψ` the mean phase. Unlike
/// [`kuramoto_order_parameter`], no clamping is applied to the complex value.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for an empty slice and
/// [`MetricError::NonFiniteValue`] for a non-finite phase.
///
/// # Example
///
/// ```
/// use num_complex::Complex64;
/// use prin_metrics::kuramoto_order_parameter_complex;
///
/// let phase = [0.0_f64, 0.0];
/// let z = kuramoto_order_parameter_complex(&phase).unwrap();
/// assert!((z - Complex64::new(1.0, 0.0)).norm() < 1e-12);
/// ```
pub fn kuramoto_order_parameter_complex(phase: &[f64]) -> Result<Complex64, MetricError> {
    if phase.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "kuramoto_order_parameter_complex",
        });
    }
    require_finite("kuramoto_order_parameter_complex", phase)?;
    let acc: Complex64 = phase
        .iter()
        .map(|&p| Complex64::new(p.cos(), p.sin()))
        .sum();
    Ok(acc / (phase.len() as f64))
}

/// Compute the circular inter-frame phase correlation.
///
/// `ρ = |⟨exp(i(φ_t − φ_{t−1}))⟩|` measures how consistently phase
/// differences are preserved between consecutive snapshots: `ρ ≈ 1` for a
/// uniform phase advance (binding pattern preserved), `ρ ≈ 0` for
/// reassignment. The result is clamped to `[0, 1]` (same invariant guard as
/// [`kuramoto_order_parameter`]).
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty slices,
/// [`MetricError::LengthMismatch`] for differing shapes, and
/// [`MetricError::NonFiniteValue`] for non-finite phases.
///
/// # Example
///
/// ```
/// use prin_metrics::inter_frame_phase_correlation;
///
/// let prev = [0.1_f64, 1.4, 2.9];
/// let curr = [0.12_f64, 1.42, 2.92]; // uniform advance → ρ = 1
/// let rho = inter_frame_phase_correlation(&curr, &prev).unwrap();
/// assert!((rho - 1.0).abs() < 1e-12);
/// ```
pub fn inter_frame_phase_correlation(
    phase_t: &[f64],
    phase_t_prev: &[f64],
) -> Result<f64, MetricError> {
    if phase_t.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "inter_frame_phase_correlation",
        });
    }
    if phase_t.len() != phase_t_prev.len() {
        return Err(MetricError::LengthMismatch {
            metric: "inter_frame_phase_correlation",
            expected: phase_t.len(),
            got: phase_t_prev.len(),
        });
    }
    require_finite("inter_frame_phase_correlation", phase_t)?;
    require_finite("inter_frame_phase_correlation", phase_t_prev)?;
    let acc: Complex64 = phase_t
        .iter()
        .zip(phase_t_prev.iter())
        .map(|(&curr, &prev)| {
            let delta = curr - prev;
            Complex64::new(delta.cos(), delta.sin())
        })
        .sum();
    Ok((acc / (phase_t.len() as f64)).norm().min(1.0))
}

/// Compute the per-snapshot Kuramoto order parameter of a phase trajectory.
///
/// `trajectory` is a flat row-major `T × n` layout (`T` snapshots of `n`
/// phases). Returns one order parameter per snapshot, clamped to `[0, 1]`
/// like [`kuramoto_order_parameter`].
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty input or `n == 0`,
/// [`MetricError::TrajectoryShape`] when `trajectory.len()` is not a multiple
/// of `n`, and [`MetricError::NonFiniteValue`] for non-finite phases.
///
/// # Example
///
/// ```
/// use prin_metrics::order_parameter_series;
///
/// // Two snapshots of two oscillators: in-phase, then anti-phase.
/// let traj = [0.0_f64, 0.0, 0.0, std::f64::consts::PI];
/// let series = order_parameter_series(&traj, 2).unwrap();
/// assert!((series[0] - 1.0).abs() < 1e-12);
/// assert!(series[1] < 1e-12);
/// ```
pub fn order_parameter_series(trajectory: &[f64], n: usize) -> Result<Vec<f64>, MetricError> {
    if n == 0 || trajectory.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "order_parameter_series",
        });
    }
    if trajectory.len() % n != 0 {
        return Err(MetricError::TrajectoryShape {
            metric: "order_parameter_series",
            len: trajectory.len(),
            n,
        });
    }
    require_finite("order_parameter_series", trajectory)?;
    trajectory
        .chunks_exact(n)
        .map(kuramoto_order_parameter)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::{FRAC_PI_2, PI, TAU};

    #[test]
    fn order_parameter_synchronized_is_one() {
        let phase = vec![1.234; 64];
        let r = kuramoto_order_parameter(&phase).unwrap();
        assert!((r - 1.0).abs() < 1e-14);
    }

    #[test]
    fn order_parameter_equally_spaced_is_zero() {
        // Σ exp(i·2πk/N) = 0 for the N-th roots of unity (N >= 2).
        for n in 2..=12usize {
            let phase: Vec<f64> = (0..n).map(|k| TAU * (k as f64) / (n as f64)).collect();
            let r = kuramoto_order_parameter(&phase).unwrap();
            assert!(r < 1e-12, "n = {n}: r = {r}");
        }
    }

    #[test]
    fn order_parameter_antiphase_is_zero() {
        let r = kuramoto_order_parameter(&[0.0, PI]).unwrap();
        assert!(r < 1e-15);
    }

    #[test]
    fn order_parameter_single_oscillator_is_one() {
        let r = kuramoto_order_parameter(&[2.5]).unwrap();
        assert!((r - 1.0).abs() < 1e-15);
    }

    #[test]
    fn order_parameter_is_clamped_to_unit_interval() {
        let r = kuramoto_order_parameter(&[0.0, 1e-16, -1e-16]).unwrap();
        assert!((0.0..=1.0).contains(&r));
    }

    #[test]
    fn order_parameter_rejects_empty() {
        let err = kuramoto_order_parameter(&[]).unwrap_err();
        assert_eq!(
            err,
            MetricError::EmptyInput {
                metric: "kuramoto_order_parameter_complex"
            }
        );
    }

    #[test]
    fn order_parameter_rejects_non_finite() {
        let err = kuramoto_order_parameter(&[0.0, f64::NAN]).unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 1, .. }));
    }

    #[test]
    fn order_parameter_complex_matches_scalar_magnitude() {
        let phase = [0.1_f64, 0.5, 1.2, 2.8, 4.0, 5.5, 6.1, 3.3];
        let z = kuramoto_order_parameter_complex(&phase).unwrap();
        let r = kuramoto_order_parameter(&phase).unwrap();
        assert!((z.norm().min(1.0) - r).abs() < 1e-15);
    }

    #[test]
    fn order_parameter_complex_argument_is_mean_phase_when_synchronized() {
        let z = kuramoto_order_parameter_complex(&[0.7; 8]).unwrap();
        assert!((z.arg() - 0.7).abs() < 1e-14);
    }

    #[test]
    fn order_parameter_invariant_under_global_phase_shift() {
        let phase = [0.2_f64, 1.1, 2.0, 2.9, 3.6, 4.4, 5.1, 5.9];
        let r0 = kuramoto_order_parameter(&phase).unwrap();
        let shifted: Vec<f64> = phase.iter().map(|&p| p + 1.37).collect();
        let r1 = kuramoto_order_parameter(&shifted).unwrap();
        assert!((r0 - r1).abs() < 1e-12);
    }

    #[test]
    fn inter_frame_uniform_advance_is_one() {
        let prev = [0.1_f64, 2.0, 4.4];
        let curr = [0.35_f64, 2.25, 4.65];
        let rho = inter_frame_phase_correlation(&curr, &prev).unwrap();
        assert!((rho - 1.0).abs() < 1e-14);
    }

    #[test]
    fn inter_frame_quadrature_scatter_is_zero() {
        // Half the population advances by +π/2, half by −π/2 → mean of ±i = 0.
        let prev = [0.0_f64, 1.0, 2.0, 3.0];
        let curr = [FRAC_PI_2, 1.0 + FRAC_PI_2, 2.0 - FRAC_PI_2, 3.0 - FRAC_PI_2];
        let rho = inter_frame_phase_correlation(&curr, &prev).unwrap();
        assert!(rho < 1e-14);
    }

    #[test]
    fn inter_frame_rejects_shape_mismatch() {
        let err = inter_frame_phase_correlation(&[0.0, 1.0], &[0.0]).unwrap_err();
        assert!(matches!(err, MetricError::LengthMismatch { .. }));
    }

    #[test]
    fn inter_frame_rejects_empty() {
        let err = inter_frame_phase_correlation(&[], &[]).unwrap_err();
        assert!(matches!(err, MetricError::EmptyInput { .. }));
    }

    #[test]
    fn inter_frame_rejects_non_finite() {
        let err = inter_frame_phase_correlation(&[0.0, f64::INFINITY], &[0.0, 0.0]).unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 1, .. }));
        let err = inter_frame_phase_correlation(&[0.0, 0.0], &[f64::NAN, 0.0]).unwrap_err();
        assert!(matches!(err, MetricError::NonFiniteValue { index: 0, .. }));
    }

    #[test]
    fn series_matches_per_snapshot_order_parameter() {
        let traj = [0.0_f64, 0.0, 0.0, PI, 0.1, 0.5, 1.2, 2.8];
        let series = order_parameter_series(&traj, 2).unwrap();
        assert_eq!(series.len(), 4);
        for (t, &r) in series.iter().enumerate() {
            let expected = kuramoto_order_parameter(&traj[t * 2..t * 2 + 2]).unwrap();
            assert!((r - expected).abs() < 1e-15);
        }
    }

    #[test]
    fn series_rejects_bad_shapes() {
        assert!(matches!(
            order_parameter_series(&[], 2).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            order_parameter_series(&[0.0], 0).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            order_parameter_series(&[0.0, 1.0, 2.0], 2).unwrap_err(),
            MetricError::TrajectoryShape { .. }
        ));
        assert!(matches!(
            order_parameter_series(&[0.0, f64::NAN], 2).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn order_parameter_in_unit_interval(
            phase in prop::collection::vec(0.0_f64..std::f64::consts::TAU, 1..=48)
        ) {
            let r = kuramoto_order_parameter(&phase).unwrap();
            prop_assert!((0.0..=1.0).contains(&r), "r = {r}");
        }

        #[test]
        fn order_parameter_shift_invariant(
            phase in prop::collection::vec(0.0_f64..std::f64::consts::TAU, 2..=32),
            shift in -10.0_f64..10.0,
        ) {
            let r0 = kuramoto_order_parameter(&phase).unwrap();
            let shifted: Vec<f64> = phase.iter().map(|&p| p + shift).collect();
            let r1 = kuramoto_order_parameter(&shifted).unwrap();
            prop_assert!((r0 - r1).abs() < 1e-9, "r0 = {r0}, r1 = {r1}");
        }

        #[test]
        fn order_parameter_permutation_invariant(
            phase in prop::collection::vec(0.0_f64..std::f64::consts::TAU, 2..=32),
            seed in any::<u64>(),
        ) {
            use std::collections::hash_map::DefaultHasher;
            use std::hash::{Hash, Hasher};
            let r0 = kuramoto_order_parameter(&phase).unwrap();
            // Deterministic Fisher–Yates shuffle keyed by `seed`.
            let mut permuted = phase.clone();
            let mut hasher = DefaultHasher::new();
            seed.hash(&mut hasher);
            let mut state = hasher.finish();
            for i in (1..permuted.len()).rev() {
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                let j = (state >> 33) as usize % (i + 1);
                permuted.swap(i, j);
            }
            let r1 = kuramoto_order_parameter(&permuted).unwrap();
            prop_assert!((r0 - r1).abs() < 1e-12);
        }

        #[test]
        fn inter_frame_in_unit_interval(
            (phase, delta) in (2usize..=32).prop_flat_map(|n| {
                (
                    prop::collection::vec(0.0_f64..std::f64::consts::TAU, n),
                    prop::collection::vec(-6.0_f64..6.0, n),
                )
            }),
        ) {
            let curr: Vec<f64> = phase.iter().zip(&delta).map(|(p, d)| p + d).collect();
            let rho = inter_frame_phase_correlation(&curr, &phase).unwrap();
            prop_assert!((0.0..=1.0).contains(&rho), "rho = {rho}");
        }
    }
}

//! Metastability of synchronization.
//!
//! Metastability is a PRIN extension with no direct PRINet 3.0 analogue. In
//! the oscillator literature it is the temporal standard deviation of the
//! Kuramoto order parameter `r(t)`: high values indicate a system that
//! fluctuates between synchronized and desynchronized states (metastable
//! switching), while low values indicate a steady level of synchrony.
//!
//! Because every `r(t) ∈ [0, 1]`, metastability is bounded by `0.5` (the
//! population standard deviation of a two-point distribution at the interval
//! extremes); this invariant is asserted in the property tests.

use crate::error::MetricError;
use crate::order::order_parameter_series;

/// Compute the metastability of a phase trajectory.
///
/// Metastability is the population standard deviation of the per-snapshot
/// Kuramoto order parameter over `trajectory` (flat row-major `T × n`
/// layout). Returns `0.0` for a single snapshot.
///
/// # Errors
///
/// Returns the same errors as [`order_parameter_series`]: empty input,
/// `n == 0`, a trajectory length not divisible by `n`, and non-finite
/// phases.
///
/// # Example
///
/// ```
/// use prin_metrics::metastability;
///
/// // A trajectory whose order parameter is constant has zero metastability.
/// let traj = vec![0.0_f64, 0.0, 0.0, 0.0]; // two synchronized snapshots
/// let m = metastability(&traj, 2).unwrap();
/// assert_eq!(m, 0.0);
/// ```
pub fn metastability(trajectory: &[f64], n: usize) -> Result<f64, MetricError> {
    let series = order_parameter_series(trajectory, n)?;
    let t = series.len();
    if t < 2 {
        return Ok(0.0);
    }
    let mean = series.iter().sum::<f64>() / (t as f64);
    let var = series.iter().map(|&r| (r - mean) * (r - mean)).sum::<f64>() / (t as f64);
    Ok(var.sqrt())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    #[test]
    fn metastability_constant_series_is_zero() {
        // Three synchronized snapshots → r = 1 at each → metastability 0.
        let traj = vec![0.0_f64, 0.0, 0.0, 0.0, 0.0, 0.0];
        assert_eq!(metastability(&traj, 2).unwrap(), 0.0);
    }

    #[test]
    fn metastability_single_snapshot_is_zero() {
        assert_eq!(metastability(&[0.0, 1.0], 2).unwrap(), 0.0);
    }

    #[test]
    fn metastability_two_state_switching() {
        // Alternating fully-synchronized (r = 1) and fully-antiphase (r = 0)
        // snapshots of two oscillators → population std of {1, 0} = 0.5.
        let traj = vec![0.0_f64, 0.0, 0.0, PI, 0.0, 0.0, 0.0, PI];
        let m = metastability(&traj, 2).unwrap();
        assert!((m - 0.5).abs() < 1e-12, "{m}");
    }

    #[test]
    fn metastability_rejects_bad_shapes() {
        assert!(matches!(
            metastability(&[], 2).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            metastability(&[0.0, 1.0, 2.0], 2).unwrap_err(),
            MetricError::TrajectoryShape { .. }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    fn trajectory_strategy() -> impl Strategy<Value = (Vec<f64>, usize)> {
        (2usize..=8, 1usize..=8).prop_flat_map(|(n, snapshots)| {
            prop::collection::vec(0.0_f64..std::f64::consts::TAU, n * snapshots)
                .prop_map(move |traj| (traj, n))
        })
    }

    proptest! {
        #[test]
        fn metastability_bounded_by_half((traj, n) in trajectory_strategy()) {
            let m = metastability(&traj, n).unwrap();
            prop_assert!((0.0..=0.5).contains(&m), "m = {m}");
        }
    }
}

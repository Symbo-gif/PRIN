//! Oscillator pruning for large-system simulation.
//!
//! When simulating 1M+ oscillators, many may have negligible amplitude or be
//! phase-locked and contribute nothing to the dynamics. [`PruningStrategy`]
//! selects which oscillators to remove; [`PruningResult`] records the mapping
//! so the reduced state can be expanded back to the full system.
//!
//! Pruning is applied **before** each integration step and the result is
//! inverted **after** the step to restore the full state. The coupling matrix
//! is also reduced via [`crate::SparseCoupling::submatrix`] so that SpMV operations
//! run on the smaller system.

use prin_dynamics::OscillatorState;
use serde::{Deserialize, Serialize};

use crate::error::SimError;

/// Strategy for selecting oscillators to prune.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub enum PruningStrategy {
    /// No pruning — all oscillators are retained.
    #[default]
    None,

    /// Remove oscillators whose amplitude is at or below `threshold`.
    ///
    /// The threshold must be in `[0, AMPLITUDE_MAX]`. Oscillators with
    /// amplitude exactly equal to the threshold are pruned.
    AmplitudeThreshold(f64),
}

impl PruningStrategy {
    /// Validate that the strategy parameters are within the permitted range.
    ///
    /// # Errors
    ///
    /// Returns [`SimError::InvalidPruningThreshold`] for out-of-range values.
    pub fn validate(&self) -> Result<(), SimError> {
        match self {
            Self::None => Ok(()),
            Self::AmplitudeThreshold(t) => {
                if !t.is_finite() || *t < 0.0 || *t > prin_dynamics::state::AMPLITUDE_MAX {
                    return Err(SimError::InvalidPruningThreshold {
                        value: *t,
                        min: 0.0,
                        max: prin_dynamics::state::AMPLITUDE_MAX,
                    });
                }
                Ok(())
            }
        }
    }

    /// Determine which oscillators to keep and which to prune.
    ///
    /// # Errors
    ///
    /// Returns [`SimError::AllPruned`] if every oscillator would be removed.
    pub fn select(&self, state: &OscillatorState) -> Result<PruningResult, SimError> {
        match self {
            Self::None => {
                let n = state.n_oscillators();
                Ok(PruningResult {
                    kept_indices: (0..n).collect(),
                    pruned_indices: Vec::new(),
                })
            }
            Self::AmplitudeThreshold(threshold) => {
                let mut kept = Vec::new();
                let mut pruned = Vec::new();
                for (i, &a) in state.amplitude.iter().enumerate() {
                    if a <= *threshold {
                        pruned.push(i);
                    } else {
                        kept.push(i);
                    }
                }
                if kept.is_empty() {
                    return Err(SimError::AllPruned {
                        n: state.n_oscillators(),
                    });
                }
                Ok(PruningResult {
                    kept_indices: kept,
                    pruned_indices: pruned,
                })
            }
        }
    }
}

/// Result of applying a pruning strategy: the kept and pruned index sets.
///
/// Use [`apply`](PruningResult::apply) to extract the reduced state and
/// [`restore`](PruningResult::restore) to expand back to the full system.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PruningResult {
    /// Indices of oscillators that are retained (in ascending order).
    pub kept_indices: Vec<usize>,

    /// Indices of oscillators that were pruned (in ascending order).
    pub pruned_indices: Vec<usize>,
}

impl PruningResult {
    /// Number of oscillators retained.
    pub fn n_kept(&self) -> usize {
        self.kept_indices.len()
    }

    /// Number of oscillators pruned.
    pub fn n_pruned(&self) -> usize {
        self.pruned_indices.len()
    }

    /// Total oscillator count (kept + pruned).
    pub fn n_total(&self) -> usize {
        self.kept_indices.len() + self.pruned_indices.len()
    }

    /// Whether any oscillators were pruned.
    pub fn is_pruned(&self) -> bool {
        !self.pruned_indices.is_empty()
    }

    /// Extract the reduced state containing only the kept oscillators.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if `state` has a different length than
    /// [`n_total`](Self::n_total).
    pub fn apply(&self, state: &OscillatorState) -> Result<OscillatorState, SimError> {
        let n = state.n_oscillators();
        if n != self.n_total() {
            return Err(SimError::DimensionMismatch {
                name: "state for pruning",
                expected: self.n_total(),
                got: n,
            });
        }

        let phase: Vec<f64> = self.kept_indices.iter().map(|&i| state.phase[i]).collect();
        let amplitude: Vec<f64> = self
            .kept_indices
            .iter()
            .map(|&i| state.amplitude[i])
            .collect();
        let frequency: Vec<f64> = self
            .kept_indices
            .iter()
            .map(|&i| state.frequency[i])
            .collect();
        let freq_band = state
            .freq_band
            .as_ref()
            .map(|fb| self.kept_indices.iter().map(|&i| fb[i]).collect());

        OscillatorState::new(phase, amplitude, frequency, freq_band).map_err(SimError::Dynamics)
    }

    /// Restore a reduced state back to the full system.
    ///
    /// Pruned oscillators are filled with the provided `default_amplitude`
    /// (typically `0.0` or `AMPLITUDE_MIN`), zero phase, and their original
    /// frequency from `original_state`.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] if the reduced state has a different length than
    /// [`n_kept`](Self::n_kept).
    pub fn restore(
        &self,
        reduced: &OscillatorState,
        original_state: &OscillatorState,
        default_amplitude: f64,
    ) -> Result<OscillatorState, SimError> {
        let n_kept = self.n_kept();
        if reduced.n_oscillators() != n_kept {
            return Err(SimError::DimensionMismatch {
                name: "reduced state",
                expected: n_kept,
                got: reduced.n_oscillators(),
            });
        }
        let n_total = self.n_total();

        let mut phase = vec![0.0; n_total];
        let mut amplitude = vec![default_amplitude; n_total];
        let mut frequency = original_state.frequency.clone();
        let freq_band = original_state.freq_band.clone();

        for (new_i, &old_i) in self.kept_indices.iter().enumerate() {
            phase[old_i] = reduced.phase[new_i];
            amplitude[old_i] = reduced.amplitude[new_i];
            frequency[old_i] = reduced.frequency[new_i];
        }

        OscillatorState::new(phase, amplitude, frequency, freq_band).map_err(SimError::Dynamics)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_state(amplitudes: &[f64]) -> OscillatorState {
        let n = amplitudes.len();
        OscillatorState::new(vec![0.0; n], amplitudes.to_vec(), vec![1.0; n], None).unwrap()
    }

    #[test]
    fn no_pruning_keeps_all() {
        let state = make_state(&[1.0, 2.0, 3.0]);
        let strategy = PruningStrategy::None;
        let result = strategy.select(&state).unwrap();
        assert_eq!(result.n_kept(), 3);
        assert_eq!(result.n_pruned(), 0);
        assert!(!result.is_pruned());
    }

    #[test]
    fn amplitude_threshold_prunes_low() {
        let state = make_state(&[0.001, 1.0, 0.0001, 2.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();
        assert_eq!(result.n_kept(), 2);
        assert_eq!(result.n_pruned(), 2);
        assert_eq!(result.kept_indices, vec![1, 3]);
        assert_eq!(result.pruned_indices, vec![0, 2]);
    }

    #[test]
    fn all_pruned_is_error() {
        let state = make_state(&[0.001, 0.002]);
        let strategy = PruningStrategy::AmplitudeThreshold(1.0);
        let err = strategy.select(&state).unwrap_err();
        assert!(matches!(err, SimError::AllPruned { .. }));
    }

    #[test]
    fn invalid_threshold_rejected() {
        let strategy = PruningStrategy::AmplitudeThreshold(-1.0);
        let err = strategy.validate().unwrap_err();
        assert!(matches!(err, SimError::InvalidPruningThreshold { .. }));
    }

    #[test]
    fn apply_and_restore_round_trip() {
        let state = make_state(&[0.001, 1.0, 0.0001, 2.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();

        let reduced = result.apply(&state).unwrap();
        assert_eq!(reduced.n_oscillators(), 2);
        assert_eq!(reduced.amplitude, vec![1.0, 2.0]);

        let restored = result.restore(&reduced, &state, 0.0).unwrap();
        assert_eq!(restored.n_oscillators(), 4);
        assert!((restored.amplitude[0] - prin_dynamics::state::AMPLITUDE_MIN).abs() < 1e-12);
        assert_eq!(restored.amplitude[1], 1.0);
        assert!((restored.amplitude[2] - prin_dynamics::state::AMPLITUDE_MIN).abs() < 1e-12);
        assert_eq!(restored.amplitude[3], 2.0);
    }

    #[test]
    fn restore_dimension_mismatch() {
        let state = make_state(&[1.0, 2.0, 3.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.5);
        let result = strategy.select(&state).unwrap();

        let wrong = make_state(&[1.0, 2.0]);
        let err = result.restore(&wrong, &state, 0.0).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn apply_dimension_mismatch() {
        let state = make_state(&[1.0, 2.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.5);
        let result = strategy.select(&state).unwrap();

        let wrong = make_state(&[1.0, 2.0, 3.0]);
        let err = result.apply(&wrong).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn default_strategy_is_none() {
        assert_eq!(PruningStrategy::default(), PruningStrategy::None);
    }

    #[test]
    fn threshold_at_boundary_prunes() {
        let state = make_state(&[0.5, 0.5, 1.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.5);
        let result = strategy.select(&state).unwrap();
        assert_eq!(result.n_pruned(), 2);
        assert_eq!(result.kept_indices, vec![2]);
    }

    #[test]
    fn validate_nan_threshold() {
        let strategy = PruningStrategy::AmplitudeThreshold(f64::NAN);
        let err = strategy.validate().unwrap_err();
        assert!(matches!(err, SimError::InvalidPruningThreshold { .. }));
    }

    #[test]
    fn validate_above_max_threshold() {
        let strategy =
            PruningStrategy::AmplitudeThreshold(prin_dynamics::state::AMPLITUDE_MAX + 1.0);
        let err = strategy.validate().unwrap_err();
        assert!(matches!(err, SimError::InvalidPruningThreshold { .. }));
    }

    #[test]
    fn validate_infinity_threshold() {
        let strategy = PruningStrategy::AmplitudeThreshold(f64::INFINITY);
        let err = strategy.validate().unwrap_err();
        assert!(matches!(err, SimError::InvalidPruningThreshold { .. }));
    }

    #[test]
    fn validate_none_strategy_ok() {
        let strategy = PruningStrategy::None;
        assert!(strategy.validate().is_ok());
    }

    #[test]
    fn validate_valid_threshold_ok() {
        let strategy = PruningStrategy::AmplitudeThreshold(0.5);
        assert!(strategy.validate().is_ok());
    }

    #[test]
    fn n_total_and_accessors() {
        let state = make_state(&[0.001, 1.0, 0.0001, 2.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();
        assert_eq!(result.n_total(), 4);
        assert_eq!(result.n_kept(), 2);
        assert_eq!(result.n_pruned(), 2);
        assert!(result.is_pruned());
    }

    #[test]
    fn no_pruning_is_not_pruned() {
        let state = make_state(&[1.0, 2.0, 3.0]);
        let strategy = PruningStrategy::None;
        let result = strategy.select(&state).unwrap();
        assert!(!result.is_pruned());
        assert_eq!(result.n_total(), 3);
    }

    #[test]
    fn apply_with_freq_band() {
        let n = 4;
        let state = OscillatorState::new(
            vec![0.0; n],
            vec![0.001, 1.0, 0.0001, 2.0],
            vec![1.0, 2.0, 3.0, 4.0],
            Some(vec![10, 20, 30, 40]),
        )
        .unwrap();
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();
        let reduced = result.apply(&state).unwrap();
        assert_eq!(reduced.n_oscillators(), 2);
        assert_eq!(reduced.frequency, vec![2.0, 4.0]);
        assert!(reduced.freq_band.is_some());
        assert_eq!(reduced.freq_band.as_ref().unwrap(), &vec![20, 40]);
    }

    #[test]
    fn restore_with_freq_band() {
        let n = 4;
        let state = OscillatorState::new(
            vec![0.0; n],
            vec![0.001, 1.0, 0.0001, 2.0],
            vec![1.0, 2.0, 3.0, 4.0],
            Some(vec![10, 20, 30, 40]),
        )
        .unwrap();
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();
        let reduced = result.apply(&state).unwrap();
        let restored = result.restore(&reduced, &state, 0.0).unwrap();
        assert_eq!(restored.n_oscillators(), 4);
        assert!(restored.freq_band.is_some());
        assert_eq!(restored.freq_band.as_ref().unwrap(), &vec![10, 20, 30, 40]);
    }

    #[test]
    fn pruning_serialization_round_trip() {
        let state = make_state(&[0.001, 1.0, 0.0001, 2.0]);
        let strategy = PruningStrategy::AmplitudeThreshold(0.01);
        let result = strategy.select(&state).unwrap();
        let json = serde_json::to_string(&result).unwrap();
        let deserialized: PruningResult = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized, result);
    }

    #[test]
    fn strategy_serialization_round_trip() {
        let s1 = PruningStrategy::None;
        let json = serde_json::to_string(&s1).unwrap();
        let d1: PruningStrategy = serde_json::from_str(&json).unwrap();
        assert_eq!(d1, PruningStrategy::None);

        let s2 = PruningStrategy::AmplitudeThreshold(0.5);
        let json = serde_json::to_string(&s2).unwrap();
        let d2: PruningStrategy = serde_json::from_str(&json).unwrap();
        assert_eq!(d2, PruningStrategy::AmplitudeThreshold(0.5));
    }
}

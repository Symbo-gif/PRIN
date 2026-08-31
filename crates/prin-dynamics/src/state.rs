//! Oscillator state as a struct-of-arrays: phase, amplitude, natural frequency.
//!
//! Provides phase wrapping to `[0, 2π)`, atan2-safe phase differences, NaN/Inf
//! guards (behind the `strict-checks` feature), derivative clamping (±1e4),
//! amplitude clamping `[1e-6, 10]`, and the sort-based k-NN phase index
//! (`O(N log N)`, rayon parallel sort).
//!
//! Numerical invariants preserved from PRINet 3.0 (see the project plan §5):
//! phase wrap via `% 2π`, amplitude clamp `[1e-6, 10]`, derivative clamp `±1e4`,
//! and sparse-coupling numerical stability `SPARSE_EPS`.

use std::collections::HashSet;

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::seed::Seed;

/// One full circle in radians.
pub const TAU: f64 = core::f64::consts::TAU;

/// Minimum permitted oscillator amplitude.
pub const AMPLITUDE_MIN: f64 = 1e-6;

/// Maximum permitted oscillator amplitude.
pub const AMPLITUDE_MAX: f64 = 10.0;

/// Symmetric bound for oscillator derivative magnitudes.
pub const DERIV_CLAMP: f64 = 1e4;

/// Epsilon guard for sparse-coupling numerical stability.
pub const SPARSE_EPS: f64 = 1e-8;

/// Errors raised by oscillator-state construction and helpers.
#[derive(Debug, Error)]
pub enum StateError {
    /// The oscillator population is empty.
    #[error("oscillator population is empty")]
    EmptyPopulation,

    /// A field does not have the expected length.
    #[error("field `{name}` length {got} does not match expected {expected}")]
    LengthMismatch {
        /// Name of the field with the wrong length.
        name: &'static str,
        /// Expected length.
        expected: usize,
        /// Actual length.
        got: usize,
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

    /// A value is outside the permitted closed range.
    #[error("out-of-range value in `{name}` at index {index}: {value} (allowed [{min}, {max}])")]
    OutOfRange {
        /// Name of the offending field.
        name: &'static str,
        /// Index of the offending value.
        index: usize,
        /// Offending value.
        value: f64,
        /// Permitted minimum.
        min: f64,
        /// Permitted maximum.
        max: f64,
    },

    /// The requested k-NN count is not valid for the population size.
    #[error("invalid k-NN count: k={k} must be less than N={n}")]
    InvalidKNeighbors {
        /// Requested neighbour count.
        k: usize,
        /// Population size.
        n: usize,
    },

    /// The frequency range for random state creation is invalid.
    #[error("invalid frequency range: [{lo}, {hi}]")]
    InvalidFrequencyRange {
        /// Lower bound.
        lo: f64,
        /// Upper bound.
        hi: f64,
    },
}

/// Container for the full state of a coupled oscillator system.
///
/// State is stored as struct-of-arrays: one contiguous vector per scalar field.
/// Batched variants will be built on top of this type in later work packages.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct OscillatorState {
    /// Phase of each oscillator, in radians and wrapped to `[0, 2π)`.
    pub phase: Vec<f64>,

    /// Amplitude of each oscillator, in `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
    pub amplitude: Vec<f64>,

    /// Natural frequency of each oscillator.
    pub frequency: Vec<f64>,

    /// Optional integer frequency-band label per oscillator.
    pub freq_band: Option<Vec<u32>>,
}

impl OscillatorState {
    /// Construct an oscillator state from its parts.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] if:
    /// - any of the main arrays is empty,
    /// - the arrays have mismatched lengths,
    /// - `freq_band` (if provided) has a mismatched length,
    /// - with `strict-checks` enabled, a value is non-finite or outside the
    ///   permitted amplitude range.
    ///
    /// Without `strict-checks`, non-finite and out-of-range values are repaired
    /// by the clamp and repair guards to match PRINet 3.0 behaviour.
    pub fn new(
        phase: Vec<f64>,
        amplitude: Vec<f64>,
        frequency: Vec<f64>,
        freq_band: Option<Vec<u32>>,
    ) -> Result<Self, StateError> {
        let n = phase.len();
        if n == 0 {
            return Err(StateError::EmptyPopulation);
        }
        if amplitude.len() != n {
            return Err(StateError::LengthMismatch {
                name: "amplitude",
                expected: n,
                got: amplitude.len(),
            });
        }
        if frequency.len() != n {
            return Err(StateError::LengthMismatch {
                name: "frequency",
                expected: n,
                got: frequency.len(),
            });
        }
        if let Some(ref band) = freq_band {
            if band.len() != n {
                return Err(StateError::LengthMismatch {
                    name: "freq_band",
                    expected: n,
                    got: band.len(),
                });
            }
        }

        let phase: Vec<_> = phase
            .into_iter()
            .enumerate()
            .map(|(i, p)| {
                let p = guard_finite_value(p, i, "phase")?;
                Ok(wrap_phase(p))
            })
            .collect::<Result<Vec<_>, _>>()?;

        let amplitude: Vec<_> = amplitude
            .into_iter()
            .enumerate()
            .map(|(i, a)| guard_amplitude_value(a, i, "amplitude"))
            .collect::<Result<Vec<_>, _>>()?;

        let frequency: Vec<_> = frequency
            .into_iter()
            .enumerate()
            .map(|(i, f)| guard_finite_value(f, i, "frequency"))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            phase,
            amplitude,
            frequency,
            freq_band,
        })
    }

    /// Number of oscillators in the system.
    pub fn n_oscillators(&self) -> usize {
        self.phase.len()
    }

    /// Number of distinct frequency bands.
    ///
    /// Returns `0` when `freq_band` is `None`.
    pub fn n_bands(&self) -> usize {
        match self.freq_band {
            None => 0,
            Some(ref band) => band.iter().collect::<HashSet<_>>().len(),
        }
    }

    /// Create a random initial oscillator state.
    ///
    /// Phase is uniform on `[0, 2π)`, amplitude is fixed to `1.0`, and frequency
    /// is uniform on `[lo, hi)` from `freq_range`.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] for an empty population, an invalid
    /// `freq_range`, or a non-finite parameter.
    pub fn create_random(
        n: usize,
        freq_range: (f64, f64),
        seed: &mut Seed,
    ) -> Result<Self, StateError> {
        if n == 0 {
            return Err(StateError::EmptyPopulation);
        }
        let (lo, hi) = freq_range;
        if !(lo.is_finite() && hi.is_finite() && lo < hi) {
            return Err(StateError::InvalidFrequencyRange { lo, hi });
        }

        let phase: Vec<_> = (0..n).map(|_| TAU * seed.next_f64()).collect();
        let amplitude = vec![1.0; n];
        let frequency: Vec<_> = (0..n)
            .map(|_| {
                seed.next_f64_range(lo, hi)
                    .map_err(|_| StateError::InvalidFrequencyRange { lo, hi })
            })
            .collect::<Result<Vec<_>, _>>()?;

        Self::new(phase, amplitude, frequency, None)
    }

    /// Create a fully synchronized initial state.
    ///
    /// All oscillators start at phase `0.0`, unit amplitude, and the same base
    /// frequency.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] for an empty population or a non-finite
    /// `base_frequency`.
    pub fn create_synchronized(n: usize, base_frequency: f64) -> Result<Self, StateError> {
        if n == 0 {
            return Err(StateError::EmptyPopulation);
        }
        if !base_frequency.is_finite() {
            return Err(StateError::NonFiniteValue {
                name: "base_frequency",
                index: 0,
                value: base_frequency,
            });
        }
        Self::new(vec![0.0; n], vec![1.0; n], vec![base_frequency; n], None)
    }

    /// Build the k-nearest-phase-neighbour index for this state.
    ///
    /// See [`build_phase_knn_index`] for details.
    pub fn phase_knn_index(&self, k: usize) -> Result<Vec<Vec<usize>>, StateError> {
        build_phase_knn_index(&self.phase, k)
    }
}

/// Wrap a phase scalar to `[0, 2π)` using Euclidean remainder.
pub fn wrap_phase(phase: f64) -> f64 {
    phase.rem_euclid(TAU)
}

/// Wrap a phase slice to `[0, 2π)` elementwise.
pub fn wrap_phases(phases: &[f64]) -> Vec<f64> {
    phases.iter().copied().map(wrap_phase).collect()
}

/// Compute the wrapped, atan2-safe phase difference from `b` to `a`.
///
/// The result lies in `[-π, π]`. This is the shortest signed angular distance
/// on the circle, equivalent to `atan2(sin(a - b), cos(a - b))`.
pub fn safe_phase_diff(a: f64, b: f64) -> f64 {
    let raw = a - b;
    raw.sin().atan2(raw.cos())
}

/// Elementwise [`safe_phase_diff`] for two equal-length phase slices.
///
/// # Errors
///
/// Returns [`StateError::LengthMismatch`] if the slices have different lengths.
pub fn safe_phase_diffs(a: &[f64], b: &[f64]) -> Result<Vec<f64>, StateError> {
    if a.len() != b.len() {
        return Err(StateError::LengthMismatch {
            name: "safe_phase_diffs",
            expected: a.len(),
            got: b.len(),
        });
    }
    Ok(a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| safe_phase_diff(x, y))
        .collect())
}

/// Clamp arbitrary values to a symmetric finite interval.
///
/// This is the Rust owner for PRINet 3.0's compatibility helper
/// ``_clamp_finite``: non-finite values become zero and finite values are
/// clamped to ``[-limit, limit]``.
///
/// # Errors
///
/// Returns [`StateError::OutOfRange`] when `limit` is non-finite or negative.
pub fn clamp_finite(values: &[f64], limit: f64) -> Result<Vec<f64>, StateError> {
    if !limit.is_finite() || limit < 0.0 {
        return Err(StateError::OutOfRange {
            name: "limit",
            index: 0,
            value: limit,
            min: 0.0,
            max: f64::MAX,
        });
    }
    Ok(values
        .iter()
        .map(|&value| {
            if value.is_finite() {
                value.clamp(-limit, limit)
            } else {
                0.0
            }
        })
        .collect())
}

/// Clamp an amplitude scalar to `[AMPLITUDE_MIN, AMPLITUDE_MAX]`.
///
/// Non-finite inputs are repaired to the nearest bound: `NaN` becomes
/// `AMPLITUDE_MIN`; `+Inf` becomes `AMPLITUDE_MAX`; `-Inf` becomes
/// `AMPLITUDE_MIN`.
pub fn clamp_amplitude(amp: f64) -> f64 {
    if amp.is_nan() {
        return AMPLITUDE_MIN;
    }
    if amp.is_infinite() {
        return if amp.is_sign_positive() {
            AMPLITUDE_MAX
        } else {
            AMPLITUDE_MIN
        };
    }
    amp.clamp(AMPLITUDE_MIN, AMPLITUDE_MAX)
}

/// Clamp a derivative scalar to `[-DERIV_CLAMP, DERIV_CLAMP]`.
///
/// Non-finite inputs are repaired: `NaN` becomes `0.0`; `±Inf` becomes the
/// corresponding signed clamp bound.
pub fn clamp_derivative(d: f64) -> f64 {
    if d.is_nan() {
        return 0.0;
    }
    if d.is_infinite() {
        return d.signum() * DERIV_CLAMP;
    }
    d.clamp(-DERIV_CLAMP, DERIV_CLAMP)
}

/// Validate and, if non-strict, repair an amplitude value.
///
/// With `strict-checks` enabled, non-finite or out-of-range values return a
/// typed [`StateError`]. Otherwise the value is clamped and repaired.
pub fn guard_amplitude(amp: f64) -> Result<f64, StateError> {
    guard_amplitude_value(amp, 0, "amplitude")
}

/// Validate and, if non-strict, repair a derivative value.
///
/// With `strict-checks` enabled, non-finite or out-of-range values return a
/// typed [`StateError`]. Otherwise the value is clamped and repaired.
pub fn guard_derivative(d: f64) -> Result<f64, StateError> {
    guard_derivative_value(d, 0, "derivative")
}

/// Validate and, if non-strict, repair a slice of derivative values.
///
/// With `strict-checks` enabled, non-finite or out-of-range values return a
/// typed [`StateError`]. Otherwise the values are clamped and repaired.
pub fn guard_derivatives(derivatives: &[f64], name: &'static str) -> Result<Vec<f64>, StateError> {
    derivatives
        .iter()
        .enumerate()
        .map(|(i, &d)| guard_derivative_value(d, i, name))
        .collect()
}

/// Container for oscillator state time derivatives: `dphase/dt`, `damplitude/dt`, `dfrequency/dt`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct StateDerivatives {
    /// Time derivative of phase (`dφ/dt`) for each oscillator.
    pub dphase: Vec<f64>,

    /// Time derivative of amplitude (`dr/dt`) for each oscillator.
    pub damplitude: Vec<f64>,

    /// Time derivative of frequency (`dω/dt`) for each oscillator.
    pub dfrequency: Vec<f64>,
}

impl StateDerivatives {
    /// Construct a new derivatives container after validating lengths and numerical guards.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] if:
    /// - `dphase` is empty,
    /// - `damplitude` or `dfrequency` does not match `dphase` length,
    /// - with `strict-checks` enabled, a value is non-finite or outside `[-1e4, 1e4]`.
    pub fn new(
        dphase: Vec<f64>,
        damplitude: Vec<f64>,
        dfrequency: Vec<f64>,
    ) -> Result<Self, StateError> {
        let n = dphase.len();
        if n == 0 {
            return Err(StateError::EmptyPopulation);
        }
        if damplitude.len() != n {
            return Err(StateError::LengthMismatch {
                name: "damplitude",
                expected: n,
                got: damplitude.len(),
            });
        }
        if dfrequency.len() != n {
            return Err(StateError::LengthMismatch {
                name: "dfrequency",
                expected: n,
                got: dfrequency.len(),
            });
        }

        let dphase = guard_derivatives(&dphase, "dphase")?;
        let damplitude = guard_derivatives(&damplitude, "damplitude")?;
        let dfrequency = guard_derivatives(&dfrequency, "dfrequency")?;

        Ok(Self {
            dphase,
            damplitude,
            dfrequency,
        })
    }

    /// Number of oscillators in the system.
    pub fn n_oscillators(&self) -> usize {
        self.dphase.len()
    }
}

/// Build the k-nearest-phase-neighbour index on the phase circle.
///
/// Uses a sort-based `O(N log N)` algorithm: sort phases, then for each
/// oscillator take `k/2` left and `k - k/2` right neighbours in sorted order
/// (wrapping around the ring). The returned outer vector has length `N`; each
/// inner vector contains `k` original oscillator indices.
///
/// `k = 0` is allowed and returns an empty neighbour list for every oscillator.
/// `k >= N` is an error.
///
/// # Errors
///
/// Returns [`StateError`] for an empty population, a non-finite phase, or
/// `k >= N`.
pub fn build_phase_knn_index(phase: &[f64], k: usize) -> Result<Vec<Vec<usize>>, StateError> {
    let n = phase.len();
    if n == 0 {
        return Err(StateError::EmptyPopulation);
    }
    if k > 0 && k >= n {
        return Err(StateError::InvalidKNeighbors { k, n });
    }
    for (i, &p) in phase.iter().enumerate() {
        if !p.is_finite() {
            return Err(StateError::NonFiniteValue {
                name: "phase",
                index: i,
                value: p,
            });
        }
    }

    let half_k = k / 2;
    let mut offsets: Vec<isize> = (1..=half_k).map(|i| -(i as isize)).collect();
    offsets.extend((1..=(k - half_k)).map(|i| i as isize));

    let mut indexed: Vec<(usize, f64)> = phase.iter().copied().enumerate().collect();
    indexed.par_sort_by(|a, b| a.1.total_cmp(&b.1).then_with(|| a.0.cmp(&b.0)));

    let sorted_idx: Vec<usize> = indexed.iter().map(|(i, _)| *i).collect();
    let mut positions = vec![0; n];
    for (pos, &(orig, _)) in indexed.iter().enumerate() {
        positions[orig] = pos;
    }

    let n_isize = n as isize;
    let mut neighbors = Vec::with_capacity(n);
    for &pos in &positions {
        let pos = pos as isize;
        let mut row = Vec::with_capacity(k);
        for &off in &offsets {
            let nbr_pos = (pos + off).rem_euclid(n_isize) as usize;
            row.push(sorted_idx[nbr_pos]);
        }
        neighbors.push(row);
    }
    Ok(neighbors)
}

#[cfg(feature = "strict-checks")]
fn guard_finite_value(value: f64, index: usize, name: &'static str) -> Result<f64, StateError> {
    if !value.is_finite() {
        return Err(StateError::NonFiniteValue { name, index, value });
    }
    Ok(value)
}

#[cfg(not(feature = "strict-checks"))]
fn guard_finite_value(value: f64, _index: usize, _name: &'static str) -> Result<f64, StateError> {
    if value.is_finite() {
        Ok(value)
    } else {
        Ok(0.0)
    }
}

#[cfg(feature = "strict-checks")]
fn guard_amplitude_value(amp: f64, index: usize, name: &'static str) -> Result<f64, StateError> {
    if !amp.is_finite() {
        return Err(StateError::NonFiniteValue {
            name,
            index,
            value: amp,
        });
    }
    if !(AMPLITUDE_MIN..=AMPLITUDE_MAX).contains(&amp) {
        return Err(StateError::OutOfRange {
            name,
            index,
            value: amp,
            min: AMPLITUDE_MIN,
            max: AMPLITUDE_MAX,
        });
    }
    Ok(amp)
}

#[cfg(not(feature = "strict-checks"))]
fn guard_amplitude_value(amp: f64, _index: usize, _name: &'static str) -> Result<f64, StateError> {
    Ok(clamp_amplitude(amp))
}

#[cfg(feature = "strict-checks")]
fn guard_derivative_value(d: f64, index: usize, name: &'static str) -> Result<f64, StateError> {
    if !d.is_finite() {
        return Err(StateError::NonFiniteValue {
            name,
            index,
            value: d,
        });
    }
    if !(-DERIV_CLAMP..=DERIV_CLAMP).contains(&d) {
        return Err(StateError::OutOfRange {
            name,
            index,
            value: d,
            min: -DERIV_CLAMP,
            max: DERIV_CLAMP,
        });
    }
    Ok(d)
}

#[cfg(not(feature = "strict-checks"))]
fn guard_derivative_value(d: f64, _index: usize, _name: &'static str) -> Result<f64, StateError> {
    Ok(clamp_derivative(d))
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn clamp_finite_repairs_non_finite_and_bounds_finite_values() {
        let values = [1.0, f64::NAN, f64::INFINITY, f64::NEG_INFINITY, 1e5, -1e5];
        assert_eq!(
            clamp_finite(&values, 100.0).unwrap(),
            [1.0, 0.0, 0.0, 0.0, 100.0, -100.0]
        );
    }

    #[test]
    fn clamp_finite_rejects_invalid_limits() {
        assert!(clamp_finite(&[1.0], -1.0).is_err());
        assert!(clamp_finite(&[1.0], f64::NAN).is_err());
    }

    #[test]
    fn new_accepts_n1() {
        let s = OscillatorState::new(vec![0.1], vec![1.0], vec![0.5], None).unwrap();
        assert_eq!(s.n_oscillators(), 1);
        assert_eq!(s.phase, [0.1]);
        assert_eq!(s.amplitude, [1.0]);
        assert_eq!(s.frequency, [0.5]);
    }

    #[test]
    fn new_rejects_mismatched_lengths() {
        let err = OscillatorState::new(vec![0.0, 0.0], vec![1.0], vec![0.5], None).unwrap_err();
        assert!(matches!(
            err,
            StateError::LengthMismatch {
                name: "amplitude",
                ..
            }
        ));
    }

    #[test]
    fn new_rejects_empty() {
        let err = OscillatorState::new(vec![], vec![], vec![], None).unwrap_err();
        assert!(matches!(err, StateError::EmptyPopulation));
    }

    #[test]
    fn new_rejects_freq_band_length_mismatch() {
        let err =
            OscillatorState::new(vec![0.0], vec![1.0], vec![0.5], Some(vec![0, 1])).unwrap_err();
        assert!(matches!(
            err,
            StateError::LengthMismatch {
                name: "freq_band",
                ..
            }
        ));
    }

    #[test]
    fn create_synchronized_uses_base_frequency() {
        let s = OscillatorState::create_synchronized(8, 2.5).unwrap();
        assert_eq!(s.phase, vec![0.0; 8]);
        assert_eq!(s.amplitude, vec![1.0; 8]);
        assert_eq!(s.frequency, vec![2.5; 8]);
    }

    #[test]
    fn create_random_uses_seed() {
        let mut seed = Seed::new(123, 0);
        let s = OscillatorState::create_random(16, (0.1, 10.0), &mut seed).unwrap();
        assert_eq!(s.n_oscillators(), 16);
        assert!(s.amplitude.iter().all(|&a| (a - 1.0).abs() < 1e-12));
        assert!(s.phase.iter().all(|&p| (0.0..TAU).contains(&p)));
        assert!(s.frequency.iter().all(|&f| (0.1..10.0).contains(&f)));
    }

    #[test]
    fn create_random_is_reproducible() {
        let mut a = Seed::new(42, 7);
        let mut b = Seed::new(42, 7);
        let s1 = OscillatorState::create_random(32, (0.5, 5.0), &mut a).unwrap();
        let s2 = OscillatorState::create_random(32, (0.5, 5.0), &mut b).unwrap();
        assert_eq!(s1, s2);
    }

    #[test]
    fn wrap_phase_maps_to_tau_interval() {
        assert_relative_eq!(wrap_phase(-0.1), TAU - 0.1, epsilon = 1e-12);
        assert_relative_eq!(wrap_phase(TAU + 0.1), 0.1, epsilon = 1e-12);
        assert_relative_eq!(wrap_phase(TAU), 0.0, epsilon = 1e-12);
        assert_relative_eq!(wrap_phase(0.0), 0.0, epsilon = 1e-12);
    }

    #[test]
    fn safe_phase_diff_is_shortest_angular_distance() {
        assert_relative_eq!(safe_phase_diff(0.1, 0.0), 0.1, epsilon = 1e-12);
        assert_relative_eq!(safe_phase_diff(0.0, 0.1), -0.1, epsilon = 1e-12);
        assert_relative_eq!(safe_phase_diff(0.1, TAU - 0.1), 0.2, epsilon = 1e-12);
        assert_relative_eq!(safe_phase_diff(TAU - 0.1, 0.1), -0.2, epsilon = 1e-12);
    }

    #[test]
    fn clamp_amplitude_repairs_and_clamps() {
        assert_relative_eq!(clamp_amplitude(0.0), AMPLITUDE_MIN, epsilon = 1e-15);
        assert_relative_eq!(clamp_amplitude(20.0), AMPLITUDE_MAX, epsilon = 1e-15);
        assert_relative_eq!(clamp_amplitude(5.0), 5.0, epsilon = 1e-15);
        assert!(clamp_amplitude(f64::NAN).is_finite());
        assert_eq!(clamp_amplitude(f64::INFINITY), AMPLITUDE_MAX);
        assert_eq!(clamp_amplitude(f64::NEG_INFINITY), AMPLITUDE_MIN);
    }

    #[test]
    fn clamp_derivative_repairs_and_clamps() {
        assert_relative_eq!(clamp_derivative(0.0), 0.0, epsilon = 1e-15);
        assert_relative_eq!(clamp_derivative(2e4), DERIV_CLAMP, epsilon = 1e-15);
        assert_relative_eq!(clamp_derivative(-2e4), -DERIV_CLAMP, epsilon = 1e-15);
        assert_relative_eq!(clamp_derivative(100.0), 100.0, epsilon = 1e-15);
        assert_eq!(clamp_derivative(f64::NAN), 0.0);
        assert_eq!(clamp_derivative(f64::INFINITY), DERIV_CLAMP);
        assert_eq!(clamp_derivative(f64::NEG_INFINITY), -DERIV_CLAMP);
    }

    #[test]
    fn knn_index_returns_k_neighbours_per_oscillator() {
        let phase = vec![0.0, 0.5, 1.0, 1.5, 2.0];
        let nbrs = build_phase_knn_index(&phase, 2).unwrap();
        assert_eq!(nbrs.len(), 5);
        for row in &nbrs {
            assert_eq!(row.len(), 2);
            assert!(!row.is_empty());
        }
    }

    #[test]
    fn knn_index_k_zero_returns_empty_rows() {
        let phase = vec![0.0, 1.0, 2.0];
        let nbrs = build_phase_knn_index(&phase, 0).unwrap();
        assert_eq!(nbrs, vec![Vec::<usize>::new(); 3]);
    }

    #[test]
    fn knn_index_rejects_invalid_k() {
        let phase = vec![0.0, 1.0, 2.0];
        let err = build_phase_knn_index(&phase, 3).unwrap_err();
        assert!(matches!(err, StateError::InvalidKNeighbors { k: 3, n: 3 }));
    }

    #[test]
    fn knn_index_wraps_across_tau() {
        let phase = vec![TAU - 0.1, 0.0, 0.1];
        let nbrs = build_phase_knn_index(&phase, 1).unwrap();
        // Sorted order is [0.0 (orig 1), 0.1 (orig 2), TAU-0.1 (orig 0)].
        // Each oscillator takes its right neighbour, wrapping around.
        assert_eq!(nbrs[0][0], 1);
        assert_eq!(nbrs[1][0], 2);
        assert_eq!(nbrs[2][0], 0);
    }

    #[test]
    fn n_bands_counts_unique_labels() {
        let s = OscillatorState::new(
            vec![0.0; 6],
            vec![1.0; 6],
            vec![1.0; 6],
            Some(vec![0, 1, 0, 2, 1, 2]),
        )
        .unwrap();
        assert_eq!(s.n_bands(), 3);
    }

    #[test]
    fn n_bands_zero_without_freq_band() {
        let s = OscillatorState::create_synchronized(4, 1.0).unwrap();
        assert_eq!(s.n_bands(), 0);
    }

    #[test]
    fn new_rejects_mismatched_frequency_length() {
        let err =
            OscillatorState::new(vec![0.0, 0.0], vec![1.0, 1.0], vec![0.5], None).unwrap_err();
        assert!(matches!(
            err,
            StateError::LengthMismatch {
                name: "frequency",
                ..
            }
        ));
    }

    #[test]
    fn create_random_rejects_empty_population() {
        let mut seed = Seed::new(0, 0);
        let err = OscillatorState::create_random(0, (0.1, 10.0), &mut seed).unwrap_err();
        assert!(matches!(err, StateError::EmptyPopulation));
    }

    #[test]
    fn create_random_rejects_invalid_frequency_range() {
        let mut seed = Seed::new(0, 0);
        let err = OscillatorState::create_random(4, (10.0, 0.1), &mut seed).unwrap_err();
        assert!(matches!(err, StateError::InvalidFrequencyRange { .. }));
    }

    #[test]
    fn create_synchronized_rejects_empty_population() {
        let err = OscillatorState::create_synchronized(0, 1.0).unwrap_err();
        assert!(matches!(err, StateError::EmptyPopulation));
    }

    #[test]
    fn create_synchronized_rejects_non_finite_base_frequency() {
        let err = OscillatorState::create_synchronized(4, f64::NAN).unwrap_err();
        assert!(matches!(
            err,
            StateError::NonFiniteValue {
                name: "base_frequency",
                ..
            }
        ));
    }

    #[test]
    fn phase_knn_index_delegates_to_build_index() {
        let s = OscillatorState::create_synchronized(5, 1.0).unwrap();
        let nbrs = s.phase_knn_index(2).unwrap();
        assert_eq!(nbrs.len(), 5);
        for row in &nbrs {
            assert_eq!(row.len(), 2);
        }
    }

    #[test]
    fn safe_phase_diffs_rejects_mismatched_lengths() {
        let err = safe_phase_diffs(&[0.0, 0.0], &[0.0]).unwrap_err();
        assert!(matches!(
            err,
            StateError::LengthMismatch {
                name: "safe_phase_diffs",
                ..
            }
        ));
    }

    #[test]
    fn safe_phase_diffs_elementwise() {
        let a = vec![0.1, TAU - 0.1];
        let b = vec![0.0, 0.1];
        let d = safe_phase_diffs(&a, &b).unwrap();
        assert_relative_eq!(d[0], 0.1, epsilon = 1e-12);
        assert_relative_eq!(d[1], -0.2, epsilon = 1e-12);
    }

    #[test]
    fn wrap_phases_elementwise() {
        let phases = vec![-0.1, TAU + 0.1, TAU];
        let wrapped = wrap_phases(&phases);
        assert_relative_eq!(wrapped[0], TAU - 0.1, epsilon = 1e-12);
        assert_relative_eq!(wrapped[1], 0.1, epsilon = 1e-12);
        assert_relative_eq!(wrapped[2], 0.0, epsilon = 1e-12);
    }

    #[test]
    fn knn_index_rejects_empty_phase() {
        let err = build_phase_knn_index(&[], 0).unwrap_err();
        assert!(matches!(err, StateError::EmptyPopulation));
    }

    #[test]
    fn knn_index_rejects_non_finite_phase() {
        let err = build_phase_knn_index(&[0.0, f64::NAN], 1).unwrap_err();
        assert!(matches!(
            err,
            StateError::NonFiniteValue { name: "phase", .. }
        ));
    }

    #[test]
    #[cfg(not(feature = "strict-checks"))]
    fn non_strict_guard_amplitude_returns_clamped() {
        assert_eq!(guard_amplitude(0.0).unwrap(), AMPLITUDE_MIN);
        assert_eq!(guard_amplitude(f64::NAN).unwrap(), AMPLITUDE_MIN);
        assert_eq!(guard_amplitude(20.0).unwrap(), AMPLITUDE_MAX);
        assert_eq!(guard_amplitude(1.0).unwrap(), 1.0);
    }

    #[test]
    #[cfg(not(feature = "strict-checks"))]
    fn non_strict_guard_derivative_returns_clamped() {
        assert_eq!(guard_derivative(0.0).unwrap(), 0.0);
        assert_eq!(guard_derivative(f64::NAN).unwrap(), 0.0);
        assert_eq!(guard_derivative(2e4).unwrap(), DERIV_CLAMP);
        assert_eq!(guard_derivative(-2e4).unwrap(), -DERIV_CLAMP);
    }

    #[test]
    #[cfg(feature = "strict-checks")]
    fn strict_guard_amplitude_rejects_out_of_range() {
        let err = guard_amplitude(0.0).unwrap_err();
        assert!(matches!(
            err,
            StateError::OutOfRange {
                name: "amplitude",
                ..
            }
        ));
        assert!(guard_amplitude(1.0).is_ok());
    }

    #[test]
    #[cfg(feature = "strict-checks")]
    fn strict_guard_derivative_rejects_out_of_range() {
        let err = guard_derivative(2e4).unwrap_err();
        assert!(matches!(
            err,
            StateError::OutOfRange {
                name: "derivative",
                ..
            }
        ));
        assert!(guard_derivative(0.0).is_ok());
    }

    #[test]
    #[cfg(feature = "strict-checks")]
    fn strict_guard_derivative_rejects_non_finite() {
        let err = guard_derivative(f64::NAN).unwrap_err();
        assert!(matches!(
            err,
            StateError::NonFiniteValue {
                name: "derivative",
                ..
            }
        ));
        assert!(guard_derivative(f64::INFINITY).is_err());
    }

    #[test]
    #[cfg(feature = "strict-checks")]
    fn strict_new_rejects_non_finite_phase() {
        let err = OscillatorState::new(vec![f64::NAN], vec![1.0], vec![0.5], None).unwrap_err();
        assert!(matches!(
            err,
            StateError::NonFiniteValue { name: "phase", .. }
        ));
    }

    #[test]
    #[cfg(feature = "strict-checks")]
    fn strict_new_rejects_non_finite_amplitude() {
        let err = OscillatorState::new(vec![0.0], vec![f64::NAN], vec![0.5], None).unwrap_err();
        assert!(matches!(
            err,
            StateError::NonFiniteValue {
                name: "amplitude",
                ..
            }
        ));
    }

    #[test]
    #[cfg(not(feature = "strict-checks"))]
    fn non_strict_new_repairs_non_finite_phase() {
        let s = OscillatorState::new(vec![f64::NAN], vec![1.0], vec![0.5], None).unwrap();
        assert_eq!(s.phase, [0.0]);
    }

    #[test]
    #[cfg(not(feature = "strict-checks"))]
    fn non_strict_new_clamps_amplitude() {
        let s = OscillatorState::new(vec![0.0], vec![0.0], vec![0.5], None).unwrap();
        assert_eq!(s.amplitude, [AMPLITUDE_MIN]);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::collection::vec;
    use proptest::prelude::*;

    fn any_phase() -> impl Strategy<Value = f64> {
        0.0f64..TAU
    }

    proptest! {
        #[test]
        fn wrap_phase_maps_to_tau_interval(p in -1e6f64..=1e6f64) {
            prop_assume!(p.is_finite());
            let w = wrap_phase(p);
            prop_assert!(w.is_finite());
            prop_assert!(w >= 0.0);
            prop_assert!(w < TAU);
        }
    }

    proptest! {
        #[test]
        fn safe_phase_diff_in_closed_pi_interval(a in any_phase(), b in any_phase()) {
            let d = safe_phase_diff(a, b);
            prop_assert!(d.is_finite());
            prop_assert!(d >= -core::f64::consts::PI);
            prop_assert!(d <= core::f64::consts::PI);
        }
    }

    proptest! {
        #[test]
        fn clamp_amplitude_is_finite_and_in_range(amp in any::<f64>()) {
            let c = clamp_amplitude(amp);
            prop_assert!(c.is_finite());
            prop_assert!(c >= AMPLITUDE_MIN);
            prop_assert!(c <= AMPLITUDE_MAX);
        }
    }

    proptest! {
        #[test]
        fn clamp_derivative_is_finite_and_in_range(d in any::<f64>()) {
            let c = clamp_derivative(d);
            prop_assert!(c.is_finite());
            prop_assert!(c >= -DERIV_CLAMP);
            prop_assert!(c <= DERIV_CLAMP);
        }
    }

    proptest! {
        #[test]
        fn create_random_is_reproducible(
            n in 1usize..=64,
            counter in any::<u128>(),
            key in any::<u128>(),
            lo in 0.01f64..=100.0,
            hi in 0.02f64..=200.0,
        ) {
            prop_assume!(lo < hi);
            let mut a = Seed::new(counter, key);
            let mut b = Seed::new(counter, key);
            let s1 = OscillatorState::create_random(n, (lo, hi), &mut a).unwrap();
            let s2 = OscillatorState::create_random(n, (lo, hi), &mut b).unwrap();
            prop_assert!(s1 == s2);
            prop_assert!(s1.phase.iter().all(|&p| (0.0..TAU).contains(&p)));
            prop_assert!(s1.frequency.iter().all(|&f| (lo..hi).contains(&f)));
            prop_assert!(s1.amplitude.iter().all(|&a| (a - 1.0).abs() < 1e-12));
        }
    }

    prop_compose! {
        fn knn_input()(n in 2usize..=32)
                      (k in 0usize..n,
                       phase in vec(0.0f64..TAU, n..=n),
                       n in Just(n))
                      -> (usize, usize, Vec<f64>) {
            (n, k, phase)
        }
    }

    proptest! {
        #[test]
        fn knn_index_has_k_entries_and_no_self((n, k, phase) in knn_input()) {
            let nbrs = build_phase_knn_index(&phase, k).unwrap();
            prop_assert_eq!(nbrs.len(), n);
            for (i, row) in nbrs.iter().enumerate() {
                prop_assert_eq!(row.len(), k);
                for &j in row {
                    prop_assert!(j < n);
                }
                prop_assert!(!row.contains(&i));
            }
        }
    }

    prop_compose! {
        fn valid_state()(n in 1usize..=32)
                       (phase in vec(0.0f64..TAU, n..=n),
                        amp in vec(AMPLITUDE_MIN..=AMPLITUDE_MAX, n..=n),
                        freq in vec(-10.0f64..=10.0, n..=n),
                        n in Just(n))
                       -> (usize, Vec<f64>, Vec<f64>, Vec<f64>) {
            (n, phase, amp, freq)
        }
    }

    proptest! {
        #[test]
        fn new_accepts_random_valid_state((n, phase, amp, freq) in valid_state()) {
            let s = OscillatorState::new(phase, amp, freq, None).unwrap();
            prop_assert_eq!(s.n_oscillators(), n);
        }
    }
}

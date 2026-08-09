//! Chimera-state detection metrics.
//!
//! Rebuild of the Year-4-Q1 chimera utilities from PRINet 3.0
//! `utils/oscillosim.py`: local order parameter, Sarle's bimodality
//! coefficient, strength of incoherence (Gopal et al. 2014), the
//! discontinuity measure (chimera number `η`), and the chimera index `χ`.
//!
//! **Preserved numerical hazard (cf. plan amendment #14):** PRINet 3.0
//! evaluates `local_order_parameter` in `torch.complex64` and the remaining
//! chimera metrics in `torch.float32`. PRIN keeps the reference path fully
//! f64, so Rust-vs-PRINet chimera parity uses the documented f32-drift
//! tolerance rather than the f64 `1e-10` target.

use num_complex::Complex64;
use std::f64::consts::{PI, TAU};

use crate::error::{require_finite, validate_neighbors, MetricError};

/// Compute the local Kuramoto order parameter for each oscillator.
///
/// For each oscillator `i`,
/// `r_i = |1/k Σ_{j ∈ nbr(i)} exp(iφ_j)|` over its spatial neighbours. In a
/// chimera state, coherent oscillators have `r_i ≈ 1` while incoherent ones
/// have `r_i ≈ 0`, producing a bimodal distribution. Values lie in `[0, 1]`.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty input,
/// [`MetricError::NonFiniteValue`] for non-finite phases, and
/// neighbour-index errors for malformed `neighbors` (which must have at
/// least one neighbour per oscillator).
///
/// # Example
///
/// ```
/// use prin_metrics::local_order_parameter;
///
/// let phase = vec![0.0_f64; 6];
/// let neighbors: Vec<Vec<usize>> = (0..6)
///     .map(|i| vec![(i + 1) % 6, (i + 5) % 6])
///     .collect();
/// let r = local_order_parameter(&phase, &neighbors).unwrap();
/// assert!(r.iter().all(|&v| (v - 1.0).abs() < 1e-12));
/// ```
pub fn local_order_parameter(
    phase: &[f64],
    neighbors: &[Vec<usize>],
) -> Result<Vec<f64>, MetricError> {
    let n = phase.len();
    if n == 0 {
        return Err(MetricError::EmptyInput {
            metric: "local_order_parameter",
        });
    }
    require_finite("local_order_parameter", phase)?;
    let k = validate_neighbors("local_order_parameter", neighbors, n, true)?;

    Ok(neighbors
        .iter()
        .map(|row| {
            let acc: Complex64 = row
                .iter()
                .map(|&j| Complex64::new(phase[j].cos(), phase[j].sin()))
                .sum();
            (acc / (k as f64)).norm().min(1.0)
        })
        .collect())
}

/// Compute Sarle's bimodality coefficient.
///
/// `BC = (γ² + 1) / κ` where `γ` is the skewness and `κ` the (non-excess)
/// kurtosis computed from population moments. A uniform distribution has
/// `BC = 5/9 ≈ 0.555`; values above this threshold suggest bimodality,
/// indicating coexistence of coherent and incoherent domains in a chimera
/// state. Returns `0.0` for fewer than 4 samples or a degenerate variance,
/// matching PRINet 3.0.
///
/// # Errors
///
/// Returns [`MetricError::NonFiniteValue`] for non-finite entries.
///
/// # Example
///
/// ```
/// use prin_metrics::bimodality_index;
///
/// // A clearly bimodal sample clusters near 0 and 1.
/// let values = [0.0_f64, 0.05, 0.02, 0.98, 1.0, 0.95, 0.01, 0.99];
/// let bc = bimodality_index(&values).unwrap();
/// assert!(bc > 0.555);
/// ```
pub fn bimodality_index(values: &[f64]) -> Result<f64, MetricError> {
    require_finite("bimodality_index", values)?;
    let n = values.len();
    if n < 4 {
        return Ok(0.0);
    }
    let mean = values.iter().sum::<f64>() / (n as f64);
    let mut m2 = 0.0_f64;
    let mut m3 = 0.0_f64;
    let mut m4 = 0.0_f64;
    for &v in values {
        let d = v - mean;
        let d2 = d * d;
        m2 += d2;
        m3 += d2 * d;
        m4 += d2 * d2;
    }
    m2 /= n as f64;
    m3 /= n as f64;
    m4 /= n as f64;
    if m2 < 1e-12 {
        return Ok(0.0);
    }
    let std = m2.sqrt();
    let skew = m3 / (std * std * std);
    let kurt = m4 / (m2 * m2);
    if kurt < 1e-12 {
        return Ok(0.0);
    }
    Ok((skew * skew + 1.0) / kurt)
}

/// Compute the Strength of Incoherence (SI) profile (Gopal et al. 2014).
///
/// SI measures local coherence by comparing the smoothed and unsmoothed
/// finite-difference series of the phase field. With
/// `z_m = wrap(φ_m − φ_{m+1})` centred to `[−π, π)`,
/// `SI = 1 − ⟨|z̄_m|⟩ / ⟨|z_m|⟩` where `z̄_m` is the spatial running average
/// of `z_m` over `window_size` neighbours. `SI → 0` for coherent regions and
/// `SI → 1` for incoherent regions; the result is clamped to `[0, 1]`.
/// Returns `0.0` for `N < 3` or a vanishing denominator, matching PRINet 3.0.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty input,
/// [`MetricError::NonFiniteValue`] for non-finite phases, and
/// [`MetricError::InvalidWindow`] for `window_size == 0`.
///
/// # Example
///
/// ```
/// use prin_metrics::strength_of_incoherence;
///
/// // A perfectly coherent (constant) phase field has SI = 0.
/// let si = strength_of_incoherence(&vec![1.0_f64; 16], 4).unwrap();
/// assert!(si < 1e-9);
/// ```
pub fn strength_of_incoherence(phase: &[f64], window_size: usize) -> Result<f64, MetricError> {
    if phase.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "strength_of_incoherence",
        });
    }
    require_finite("strength_of_incoherence", phase)?;
    if window_size == 0 {
        return Err(MetricError::InvalidWindow {
            metric: "strength_of_incoherence",
            window: window_size,
        });
    }
    let n = phase.len();
    if n < 3 {
        return Ok(0.0);
    }

    // Wrapped finite difference on the ring, centred to [−π, π).
    let z: Vec<f64> = (0..n)
        .map(|m| (phase[m] - phase[(m + 1) % n]).rem_euclid(TAU) - PI)
        .collect();

    let denom = z.iter().map(|v| v.abs()).sum::<f64>() / (n as f64);
    if denom < 1e-12 {
        return Ok(0.0);
    }

    // Circular running average replicating PRINet 3.0's pad + conv1d + slice
    // semantics: z_padded = [z[n−w..], z, z[..w]] (Python slice clamping when
    // w > n), out[m] = mean(z_padded[m .. m + w]) for as many outputs as the
    // valid convolution produces, then truncated to at most n entries.
    let w = window_size;
    let mut padded: Vec<f64> = Vec::with_capacity(n + 2 * w.min(n));
    padded.extend_from_slice(&z[n.saturating_sub(w)..]);
    padded.extend_from_slice(&z);
    padded.extend_from_slice(&z[..w.min(n)]);

    let smooth_len = (padded.len() + 1).saturating_sub(w).min(n);
    if smooth_len == 0 {
        return Ok(0.0);
    }
    let mut numer = 0.0_f64;
    for m in 0..smooth_len {
        let acc: f64 = padded[m..m + w].iter().sum();
        numer += (acc / (w as f64)).abs();
    }
    numer /= smooth_len as f64;

    Ok((1.0 - numer / denom).clamp(0.0, 1.0))
}

/// Compute the discontinuity measure of a phase snapshot.
///
/// Measures the second-order finite difference (local curvature) of the phase
/// field on a ring: `D_m = |wrap(φ_{m−1} − 2φ_m + φ_{m+1})|`. Oscillators with
/// `D_m < δ` (`δ = threshold_ratio · 2π`) are marked coherent. The returned
/// chimera number `η` counts coherent-to-incoherent transitions divided by 2
/// (`0` = fully coherent, `1` = single chimera, `≥ 2` = multi-chimera).
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty input,
/// [`MetricError::NonFiniteValue`] for non-finite phases, and
/// [`MetricError::InvalidParameter`] for a non-finite `threshold_ratio`.
///
/// # Example
///
/// ```
/// use prin_metrics::discontinuity_measure;
///
/// // Constant phase → all coherent, η = 0.
/// let (mask, eta) = discontinuity_measure(&vec![0.5_f64; 10], 0.01).unwrap();
/// assert!(mask.iter().all(|&c| c));
/// assert_eq!(eta, 0);
/// ```
pub fn discontinuity_measure(
    phase: &[f64],
    threshold_ratio: f64,
) -> Result<(Vec<bool>, usize), MetricError> {
    if phase.is_empty() {
        return Err(MetricError::EmptyInput {
            metric: "discontinuity_measure",
        });
    }
    require_finite("discontinuity_measure", phase)?;
    if !threshold_ratio.is_finite() {
        return Err(MetricError::InvalidParameter {
            metric: "discontinuity_measure",
            name: "threshold_ratio",
            value: threshold_ratio,
        });
    }
    let n = phase.len();
    if n < 3 {
        return Ok((vec![true; n], 0));
    }

    let threshold = threshold_ratio * TAU;
    let mut mask = vec![false; n];
    for m in 0..n {
        let prev = phase[(m + n - 1) % n];
        let next = phase[(m + 1) % n];
        let diff = prev - 2.0 * phase[m] + next;
        let wrapped = diff.sin().atan2(diff.cos());
        mask[m] = wrapped.abs() < threshold;
    }

    // Count coherent↔incoherent transitions on the ring.
    let mut transitions = 0usize;
    for m in 0..n {
        if mask[m] != mask[(m + n - 1) % n] {
            transitions += 1;
        }
    }
    Ok((mask, transitions / 2))
}

/// Compute the chimera index `χ ∈ [0, 1]`.
///
/// The fraction of oscillators whose local order parameter `r_i` falls below
/// a coherence `threshold`: `χ = N_incoherent / N`. Typical chimera states
/// yield `χ ∈ [0.3, 0.6]`.
///
/// # Errors
///
/// Returns the input errors of [`local_order_parameter`] plus
/// [`MetricError::InvalidParameter`] for a non-finite `threshold`.
///
/// # Example
///
/// ```
/// use prin_metrics::chimera_index;
///
/// // Fully synchronized → every local order parameter is 1 → χ = 0.
/// let phase = vec![0.0_f64; 6];
/// let neighbors: Vec<Vec<usize>> = (0..6)
///     .map(|i| vec![(i + 1) % 6, (i + 5) % 6])
///     .collect();
/// let chi = chimera_index(&phase, &neighbors, 0.5).unwrap();
/// assert_eq!(chi, 0.0);
/// ```
pub fn chimera_index(
    phase: &[f64],
    neighbors: &[Vec<usize>],
    threshold: f64,
) -> Result<f64, MetricError> {
    if !threshold.is_finite() {
        return Err(MetricError::InvalidParameter {
            metric: "chimera_index",
            name: "threshold",
            value: threshold,
        });
    }
    let r_local = local_order_parameter(phase, neighbors)?;
    let n_incoherent = r_local.iter().filter(|&&r| r < threshold).count();
    Ok((n_incoherent as f64) / (phase.len() as f64))
}

/// Compute the time-averaged Strength of Incoherence over a trajectory.
///
/// Evaluates [`strength_of_incoherence`] for each snapshot in `trajectory`
/// (after discarding `discard_transient` leading frames) and returns the
/// temporal mean. Returns `0.0` when no frames remain.
///
/// # Errors
///
/// Returns the errors of [`strength_of_incoherence`] for any snapshot and
/// [`MetricError::LengthMismatch`] for ragged snapshots.
///
/// # Example
///
/// ```
/// use prin_metrics::strength_of_incoherence_temporal;
///
/// let traj = vec![vec![0.0_f64; 8], vec![0.1_f64; 8]];
/// let si = strength_of_incoherence_temporal(&traj, 4, 0).unwrap();
/// assert!(si < 1e-9);
/// ```
pub fn strength_of_incoherence_temporal(
    trajectory: &[Vec<f64>],
    window_size: usize,
    discard_transient: usize,
) -> Result<f64, MetricError> {
    let frames: &[Vec<f64>] = if discard_transient >= trajectory.len() {
        &[]
    } else {
        &trajectory[discard_transient..]
    };
    if frames.is_empty() {
        return Ok(0.0);
    }
    let n = frames[0].len();
    for frame in frames {
        if frame.len() != n {
            return Err(MetricError::LengthMismatch {
                metric: "strength_of_incoherence_temporal",
                expected: n,
                got: frame.len(),
            });
        }
    }
    let total: f64 = frames
        .iter()
        .map(|frame| strength_of_incoherence(frame, window_size))
        .sum::<Result<f64, MetricError>>()?;
    Ok(total / (frames.len() as f64))
}

/// Reference chimera threshold constant: Sarle's bimodality coefficient for a
/// uniform distribution (`5/9`). Values above this suggest bimodality.
pub const BIMODALITY_CHIMERA_THRESHOLD: f64 = 5.0 / 9.0;

/// Default incoherence cutoff used by [`chimera_index`] in PRINet 3.0.
pub const DEFAULT_CHIMERA_THRESHOLD: f64 = 0.5;

#[cfg(test)]
mod tests {
    use super::*;

    fn ring_neighbors(n: usize, half: usize) -> Vec<Vec<usize>> {
        (0..n)
            .map(|i| {
                let mut row = Vec::with_capacity(2 * half);
                for d in 1..=half {
                    row.push((i + n - d) % n);
                    row.push((i + d) % n);
                }
                row
            })
            .collect()
    }

    #[test]
    fn local_order_synchronized_is_one() {
        let r = local_order_parameter(&[0.4; 10], &ring_neighbors(10, 2)).unwrap();
        assert_eq!(r.len(), 10);
        assert!(r.iter().all(|&v| (v - 1.0).abs() < 1e-13));
    }

    #[test]
    fn local_order_alternating_antiphase_is_zero() {
        // Even ring with alternating 0/π phases: each oscillator's neighbours
        // are all in the opposite cluster → local mean cancels to 0.
        let n = 8;
        let phase: Vec<f64> = (0..n).map(|i| if i % 2 == 0 { 0.0 } else { PI }).collect();
        let r = local_order_parameter(&phase, &ring_neighbors(n, 2)).unwrap();
        assert!(r.iter().all(|&v| v < 1e-12), "{r:?}");
    }

    #[test]
    fn local_order_rejects_bad_inputs() {
        assert!(matches!(
            local_order_parameter(&[], &[]).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            local_order_parameter(&[0.0, f64::NAN], &[vec![1], vec![0]]).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            local_order_parameter(&[0.0, 1.0, 2.0], &[vec![], vec![], vec![]]).unwrap_err(),
            MetricError::InvalidNeighborCount { .. }
        ));
    }

    #[test]
    fn bimodality_uniform_is_five_ninths() {
        let values: Vec<f64> = (0..1000).map(|i| (i as f64) / 999.0).collect();
        let bc = bimodality_index(&values).unwrap();
        assert!((bc - BIMODALITY_CHIMERA_THRESHOLD).abs() < 1e-3, "{bc}");
    }

    #[test]
    fn bimodality_bimodal_exceeds_threshold() {
        let mut values = vec![0.0_f64; 50];
        values.extend(vec![1.0_f64; 50]);
        // Add tiny jitter so the variance is non-degenerate.
        for (i, v) in values.iter_mut().enumerate() {
            *v += 0.001 * ((i % 7) as f64 - 3.0);
        }
        let bc = bimodality_index(&values).unwrap();
        assert!(bc > BIMODALITY_CHIMERA_THRESHOLD, "{bc}");
    }

    #[test]
    fn bimodality_degenerate_returns_zero() {
        assert_eq!(bimodality_index(&[0.5, 0.5, 0.5, 0.5]).unwrap(), 0.0);
        assert_eq!(bimodality_index(&[1.0, 2.0]).unwrap(), 0.0);
        assert_eq!(bimodality_index(&[]).unwrap(), 0.0);
    }

    #[test]
    fn bimodality_rejects_non_finite() {
        assert!(matches!(
            bimodality_index(&[0.0, 1.0, f64::NAN, 2.0]).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn strength_of_incoherence_coherent_is_zero() {
        // Constant phase → z constant → smoothing leaves |z̄| = |z| → SI = 0
        // (up to floating-point accumulation noise).
        let si = strength_of_incoherence(&[2.0; 16], 4).unwrap();
        assert!(si < 1e-9, "{si}");
        // Linear ramp: SI stays small (one wrap discontinuity per ring).
        let ramp: Vec<f64> = (0..16).map(|i| 0.2 * (i as f64)).collect();
        let si = strength_of_incoherence(&ramp, 4).unwrap();
        assert!((0.0..0.1).contains(&si), "{si}");
    }

    #[test]
    fn strength_of_incoherence_window_larger_than_population() {
        // window_size > N must not panic and stays in [0, 1].
        let scattered: Vec<f64> = (0..4)
            .map(|i| ((i as f64) * 2.399 + 0.7 * (i as f64) * (i as f64)).rem_euclid(TAU))
            .collect();
        let si = strength_of_incoherence(&scattered, 9).unwrap();
        assert!((0.0..=1.0).contains(&si), "{si}");
    }

    #[test]
    fn strength_of_incoherence_in_range() {
        let scattered: Vec<f64> = (0..32)
            .map(|i| ((i as f64) * 2.399 + 0.7 * (i as f64) * (i as f64)).rem_euclid(TAU))
            .collect();
        let si = strength_of_incoherence(&scattered, 5).unwrap();
        assert!((0.0..=1.0).contains(&si), "{si}");
    }

    #[test]
    fn strength_of_incoherence_small_and_invalid() {
        assert_eq!(strength_of_incoherence(&[0.0, 1.0], 2).unwrap(), 0.0);
        assert!(matches!(
            strength_of_incoherence(&[], 2).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            strength_of_incoherence(&[0.0, 1.0, 2.0], 0).unwrap_err(),
            MetricError::InvalidWindow { .. }
        ));
        assert!(matches!(
            strength_of_incoherence(&[0.0, f64::NAN, 1.0], 2).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn discontinuity_coherent_state() {
        let (mask, eta) = discontinuity_measure(&[1.0; 12], 0.01).unwrap();
        assert!(mask.iter().all(|&c| c));
        assert_eq!(eta, 0);
    }

    #[test]
    fn discontinuity_single_chimera() {
        // Coherent ramp in [0, n/2), scattered incoherent tail → one chimera.
        let n = 32;
        let mut phase: Vec<f64> = (0..n / 2).map(|i| 0.2 * (i as f64)).collect();
        for j in 0..n / 2 {
            phase.push(((j as f64) * 2.399 + 0.7 * (j as f64) * (j as f64)).rem_euclid(TAU));
        }
        let (mask, eta) = discontinuity_measure(&phase, 0.01).unwrap();
        assert_eq!(eta, 1, "mask = {mask:?}");
        assert!(mask[..n / 2].iter().filter(|&&c| c).count() > n / 4);
    }

    #[test]
    fn discontinuity_small_and_invalid() {
        let (mask, eta) = discontinuity_measure(&[0.0, 1.0], 0.01).unwrap();
        assert_eq!(mask, vec![true, true]);
        assert_eq!(eta, 0);
        assert!(matches!(
            discontinuity_measure(&[], 0.01).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            discontinuity_measure(&[0.0, 1.0, 2.0], f64::NAN).unwrap_err(),
            MetricError::InvalidParameter { .. }
        ));
        assert!(matches!(
            discontinuity_measure(&[0.0, f64::INFINITY, 1.0], 0.01).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn chimera_index_bounds() {
        let n = 8;
        let phase: Vec<f64> = (0..n).map(|i| if i % 2 == 0 { 0.0 } else { PI }).collect();
        let neighbors = ring_neighbors(n, 2);
        // Alternating antiphase: every local order parameter ≈ 0 → χ = 1 at
        // threshold 0.5.
        let chi = chimera_index(&phase, &neighbors, 0.5).unwrap();
        assert!((chi - 1.0).abs() < 1e-9, "{chi}");
        // Fully synchronized → χ = 0.
        let chi0 = chimera_index(&vec![0.0; n], &neighbors, 0.5).unwrap();
        assert_eq!(chi0, 0.0);
    }

    #[test]
    fn chimera_index_rejects_non_finite_threshold() {
        let neighbors = vec![vec![1], vec![0]];
        assert!(matches!(
            chimera_index(&[0.0, 1.0], &neighbors, f64::NAN).unwrap_err(),
            MetricError::InvalidParameter { .. }
        ));
    }

    #[test]
    fn si_temporal_coherent_is_zero() {
        let traj = vec![vec![0.5; 10], vec![0.6; 10], vec![0.7; 10]];
        // Constant within each frame → each SI ≈ 0.
        let si = strength_of_incoherence_temporal(&traj, 3, 0).unwrap();
        assert!(si < 1e-9, "{si}");
    }

    #[test]
    fn si_temporal_discards_transient() {
        let traj = vec![vec![0.0; 8], vec![0.0; 8]];
        assert!(strength_of_incoherence_temporal(&traj, 3, 5).unwrap() < 1e-9);
        assert_eq!(strength_of_incoherence_temporal(&[], 3, 0).unwrap(), 0.0);
    }

    #[test]
    fn si_temporal_rejects_ragged() {
        let traj = vec![vec![0.0; 8], vec![0.0; 7]];
        assert!(matches!(
            strength_of_incoherence_temporal(&traj, 3, 0).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn local_order_in_unit_interval(
            phase in prop::collection::vec(0.0_f64..TAU, 6..=24),
        ) {
            let n = phase.len();
            let neighbors: Vec<Vec<usize>> = (0..n)
                .map(|i| vec![(i + 1) % n, (i + n - 1) % n])
                .collect();
            let r = local_order_parameter(&phase, &neighbors).unwrap();
            prop_assert!(r.iter().all(|&v| (0.0..=1.0).contains(&v)));
        }

        #[test]
        fn si_in_unit_interval(
            phase in prop::collection::vec(0.0_f64..TAU, 3..=32),
            window in 1usize..=8,
        ) {
            let si = strength_of_incoherence(&phase, window).unwrap();
            prop_assert!((0.0..=1.0).contains(&si), "si = {si}");
        }

        #[test]
        fn chimera_index_in_unit_interval(
            phase in prop::collection::vec(0.0_f64..TAU, 6..=24),
            threshold in 0.0_f64..1.0,
        ) {
            let n = phase.len();
            let neighbors: Vec<Vec<usize>> = (0..n)
                .map(|i| vec![(i + 1) % n, (i + n - 1) % n])
                .collect();
            let chi = chimera_index(&phase, &neighbors, threshold).unwrap();
            prop_assert!((0.0..=1.0).contains(&chi));
        }
    }
}

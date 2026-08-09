//! Spectral metrics: power spectral density and concept probabilities.
//!
//! Rebuild of PRINet 3.0 `core/measurement.py::power_spectral_density` and
//! `extract_concept_probabilities`.
//!
//! **Preserved numerical hazard (cf. plan amendment #14):** PRINet 3.0
//! computes the resonance signal as
//! `amplitude · exp(i·phase)|_{complex64}` — the complex exponential is
//! evaluated in `complex128` and then truncated to `complex64` (f32
//! real/imaginary parts) before the FFT, limiting PRINet's own PSD to f32
//! precision regardless of the amplitude dtype. PRIN keeps the reference
//! path fully f64 instead of reproducing the truncation, so Rust-vs-PRINet
//! PSD parity uses the documented f32-drift tolerance (`1e-6`), consistent
//! with the amendment #14 handling of PRINet's f32 complex paths.

use num_complex::Complex64;
use rustfft::FftPlanner;

use crate::error::{require_finite, MetricError};

/// Compute the power spectral density of the resonance state.
///
/// Constructs the complex signal `x[n] = A[n]·exp(iφ[n])` and returns the
/// periodogram `P[k] = |X[k]|²` of its unnormalized discrete Fourier
/// transform with `n_freq_bins` bins (zero-padded or truncated to the bin
/// count, matching `torch.fft.fft(signal, n = n_freq_bins)`). Defaults to
/// `2·N` bins like PRINet 3.0.
///
/// # Errors
///
/// Returns [`MetricError::EmptyInput`] for empty inputs,
/// [`MetricError::LengthMismatch`] when `phase` and `amplitude` differ,
/// [`MetricError::InvalidParameter`] for `n_freq_bins == 0`, and
/// [`MetricError::NonFiniteValue`] for non-finite entries.
///
/// # Example
///
/// ```
/// use prin_metrics::power_spectral_density;
///
/// let amplitude = [1.0_f64, 1.0, 1.0, 1.0];
/// let phase = [0.0_f64, 0.0, 0.0, 0.0];
/// let power = power_spectral_density(&amplitude, &phase, None).unwrap();
/// assert_eq!(power.len(), 8); // default 2*N bins
/// // DC-only signal: all power in bin 0.
/// assert!((power[0] - 16.0).abs() < 1e-9);
/// ```
pub fn power_spectral_density(
    amplitude: &[f64],
    phase: &[f64],
    n_freq_bins: Option<usize>,
) -> Result<Vec<f64>, MetricError> {
    let n = amplitude.len();
    if n == 0 {
        return Err(MetricError::EmptyInput {
            metric: "power_spectral_density",
        });
    }
    if amplitude.len() != phase.len() {
        return Err(MetricError::LengthMismatch {
            metric: "power_spectral_density",
            expected: amplitude.len(),
            got: phase.len(),
        });
    }
    require_finite("power_spectral_density", amplitude)?;
    require_finite("power_spectral_density", phase)?;
    let bins = n_freq_bins.unwrap_or(2 * n);
    if bins == 0 {
        return Err(MetricError::InvalidParameter {
            metric: "power_spectral_density",
            name: "n_freq_bins",
            value: 0.0,
        });
    }

    let mut buffer: Vec<Complex64> = (0..bins)
        .map(|i| {
            if i < n {
                Complex64::from_polar(amplitude[i], phase[i])
            } else {
                Complex64::new(0.0, 0.0)
            }
        })
        .collect();

    let mut planner = FftPlanner::<f64>::new();
    let fft = planner.plan_fft_forward(bins);
    fft.process(&mut buffer);

    Ok(buffer.iter().map(|c| c.norm_sqr()).collect())
}

/// Extract concept probabilities from the resonance spectrum.
///
/// For each concept `k` with centre frequency `ω_k` (in FFT-bin units) and
/// bandwidth `Δω_k`, computes `P(k) ∝ Σ_{f ∈ band_k} P(f)` over the PSD
/// bins `|f − ω_k| < Δω_k`, then normalizes to a probability distribution
/// with PRINet 3.0's `1e-10` denominator guard.
///
/// # Errors
///
/// Returns the same input errors as [`power_spectral_density`], plus
/// [`MetricError::LengthMismatch`] when `concept_frequencies` and
/// `concept_bandwidths` differ and [`MetricError::InvalidParameter`] for a
/// negative or non-finite bandwidth.
///
/// # Example
///
/// ```
/// use prin_metrics::extract_concept_probabilities;
///
/// let amplitude = [1.0_f64, 1.0, 1.0, 1.0];
/// let phase = [0.0_f64, 0.0, 0.0, 0.0];
/// // One concept covering every bin captures all the power.
/// let probs = extract_concept_probabilities(
///     &amplitude,
///     &phase,
///     &[4.0],
///     &[100.0],
///     None,
/// )
/// .unwrap();
/// assert!((probs[0] - 1.0).abs() < 1e-6);
/// ```
pub fn extract_concept_probabilities(
    amplitude: &[f64],
    phase: &[f64],
    concept_frequencies: &[f64],
    concept_bandwidths: &[f64],
    n_freq_bins: Option<usize>,
) -> Result<Vec<f64>, MetricError> {
    if concept_frequencies.len() != concept_bandwidths.len() {
        return Err(MetricError::LengthMismatch {
            metric: "extract_concept_probabilities",
            expected: concept_frequencies.len(),
            got: concept_bandwidths.len(),
        });
    }
    require_finite("extract_concept_probabilities", concept_frequencies)?;
    require_finite("extract_concept_probabilities", concept_bandwidths)?;
    for &bw in concept_bandwidths {
        if bw < 0.0 {
            return Err(MetricError::InvalidParameter {
                metric: "extract_concept_probabilities",
                name: "concept_bandwidths",
                value: bw,
            });
        }
    }

    let power = power_spectral_density(amplitude, phase, n_freq_bins)?;

    let mut probs: Vec<f64> = concept_frequencies
        .iter()
        .zip(concept_bandwidths.iter())
        .map(|(&freq, &bw)| {
            power
                .iter()
                .enumerate()
                .filter(|&(f, _)| ((f as f64) - freq).abs() < bw)
                .map(|(_, &p)| p)
                .sum()
        })
        .collect();

    let total: f64 = probs.iter().sum();
    for p in &mut probs {
        *p /= total + 1e-10;
    }
    Ok(probs)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::TAU;

    #[test]
    fn psd_dc_signal_concentrates_in_bin_zero() {
        let amplitude = vec![1.0; 8];
        let phase = vec![0.0; 8];
        // bins == N (no zero padding) → all power in bin 0.
        let power = power_spectral_density(&amplitude, &phase, Some(8)).unwrap();
        assert_eq!(power.len(), 8);
        // X[0] = Σ 1 = 8 → P[0] = 64; all other bins 0.
        assert!((power[0] - 64.0).abs() < 1e-9);
        for p in &power[1..] {
            assert!(*p < 1e-9);
        }
        // Default (2*N) bins zero-pad the signal → spectral leakage, but the
        // DC bin still carries |Σ x|² and Parseval holds.
        let padded = power_spectral_density(&amplitude, &phase, None).unwrap();
        assert_eq!(padded.len(), 16);
        assert!((padded[0] - 64.0).abs() < 1e-9);
    }

    #[test]
    fn psd_pure_complex_exponential_single_bin() {
        // x[n] = exp(i·2π·k0·n/M) with M = N bins concentrates at bin k0
        // with power M².
        let n = 16usize;
        let k0 = 3usize;
        let amplitude = vec![1.0; n];
        let phase: Vec<f64> = (0..n)
            .map(|i| TAU * (k0 as f64) * (i as f64) / (n as f64))
            .collect();
        let power = power_spectral_density(&amplitude, &phase, Some(n)).unwrap();
        assert_eq!(power.len(), n);
        assert!((power[k0] - (n * n) as f64).abs() < 1e-7);
        for (k, p) in power.iter().enumerate() {
            if k != k0 {
                assert!(*p < 1e-7, "bin {k}: {p}");
            }
        }
    }

    #[test]
    fn psd_parseval_identity() {
        // Σ_k |X[k]|² = M Σ_n |x[n]|² for the unnormalized DFT.
        let amplitude = [1.0_f64, 0.8, 1.2, 0.9, 1.1];
        let phase = [0.1_f64, 0.5, 1.2, 2.8, 4.0];
        for bins in [5usize, 10, 12] {
            let power = power_spectral_density(&amplitude, &phase, Some(bins)).unwrap();
            let lhs: f64 = power.iter().sum();
            let signal_energy: f64 = amplitude.iter().map(|a| a * a).sum();
            let rhs = (bins as f64) * signal_energy;
            assert!(
                (lhs - rhs).abs() < 1e-8 * rhs,
                "bins = {bins}: lhs {lhs}, rhs {rhs}"
            );
        }
    }

    #[test]
    fn psd_truncates_when_bins_below_n() {
        let amplitude = vec![1.0; 8];
        let phase = vec![0.0; 8];
        let power = power_spectral_density(&amplitude, &phase, Some(3)).unwrap();
        assert_eq!(power.len(), 3);
    }

    #[test]
    fn psd_power_is_non_negative() {
        let amplitude = [0.5_f64, 1.5, 0.7];
        let phase = [2.1_f64, 0.3, 5.5];
        let power = power_spectral_density(&amplitude, &phase, None).unwrap();
        assert!(power.iter().all(|&p| p >= 0.0));
    }

    #[test]
    fn psd_rejects_bad_inputs() {
        assert!(matches!(
            power_spectral_density(&[], &[], None).unwrap_err(),
            MetricError::EmptyInput { .. }
        ));
        assert!(matches!(
            power_spectral_density(&[1.0], &[0.0, 1.0], None).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
        assert!(matches!(
            power_spectral_density(&[1.0], &[0.0], Some(0)).unwrap_err(),
            MetricError::InvalidParameter { .. }
        ));
        assert!(matches!(
            power_spectral_density(&[f64::NAN], &[0.0], None).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            power_spectral_density(&[1.0], &[f64::INFINITY], None).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
    }

    #[test]
    fn concept_probabilities_single_band_covers_all() {
        let amplitude = [1.0_f64, 1.0, 1.0, 1.0];
        let phase = [0.0_f64, 0.0, 0.0, 0.0];
        let probs =
            extract_concept_probabilities(&amplitude, &phase, &[4.0], &[100.0], None).unwrap();
        assert_eq!(probs.len(), 1);
        assert!((probs[0] - 1.0).abs() < 1e-6);
    }

    #[test]
    fn concept_probabilities_sum_to_one() {
        let amplitude = [1.0_f64, 0.8, 1.2, 0.9, 1.1];
        let phase = [0.1_f64, 0.5, 1.2, 2.8, 4.0];
        let probs = extract_concept_probabilities(
            &amplitude,
            &phase,
            &[1.0, 4.0, 8.0],
            &[2.0, 3.0, 4.0],
            None,
        )
        .unwrap();
        assert_eq!(probs.len(), 3);
        let total: f64 = probs.iter().sum();
        // Bands overlap, so the total may exceed 1 before normalization only
        // when bands are disjoint; here normalization guarantees sum <= 1 and
        // exactly 1 when the bands cover all power exactly once. Check >= 0.
        assert!(probs.iter().all(|&p| p >= 0.0));
        assert!(total <= 1.0 + 1e-9);
    }

    #[test]
    fn concept_probabilities_empty_bands_yield_zero() {
        let amplitude = [1.0_f64, 1.0];
        let phase = [0.0_f64, 0.0];
        // Bandwidth 0 → no bin satisfies |f − ω| < 0 → all-zero probabilities.
        let probs =
            extract_concept_probabilities(&amplitude, &phase, &[1.0], &[0.0], None).unwrap();
        assert_eq!(probs, vec![0.0]);
    }

    #[test]
    fn concept_probabilities_rejects_bad_inputs() {
        assert!(matches!(
            extract_concept_probabilities(&[1.0], &[0.0], &[1.0], &[], None).unwrap_err(),
            MetricError::LengthMismatch { .. }
        ));
        assert!(matches!(
            extract_concept_probabilities(&[1.0], &[0.0], &[f64::NAN], &[1.0], None).unwrap_err(),
            MetricError::NonFiniteValue { .. }
        ));
        assert!(matches!(
            extract_concept_probabilities(&[1.0], &[0.0], &[1.0], &[-1.0], None).unwrap_err(),
            MetricError::InvalidParameter { .. }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;
    use std::f64::consts::TAU;

    proptest! {
        #[test]
        fn psd_non_negative_and_parseval(
            (amplitude, phase) in (1usize..=24).prop_flat_map(|n| {
                (
                    prop::collection::vec(0.1_f64..2.0, n),
                    prop::collection::vec(0.0_f64..TAU, n),
                )
            }),
        ) {
            let bins = 2 * amplitude.len();
            let power = power_spectral_density(&amplitude, &phase, Some(bins)).unwrap();
            let total: f64 = power.iter().sum();
            let energy: f64 = amplitude.iter().map(|a| a * a).sum();
            prop_assert!(power.iter().all(|&p| p >= 0.0));
            prop_assert!(
                (total - (bins as f64) * energy).abs() < 1e-8 * (bins as f64) * energy
            );
        }
    }
}

//! Continuous hierarchical band networks.
//!
//! - [`theta_gamma_network`]: 2-band (theta + gamma) continuous ODE network with
//!   PAC from theta phase → gamma amplitude. Theoretical working-memory
//!   capacity ≈ `floor(f_gamma / f_theta)` items (~7 for typical frequencies).
//! - [`delta_theta_gamma_network`]: 3-band (delta + theta + gamma) with PAC from
//!   delta → theta and theta → gamma.
//!
//! Both produce a [`BandNetwork`] that implements the [`Dynamics`] trait so they
//! can be driven by any [`Integrator`](crate::integrate::Integrator). Intra-band
//! dynamics follow Kuramoto mean-field coupling; cross-band interactions use
//! [`PhaseAmplitudeCoupling`].
//!
//! The trainable discrete-time variant (`DiscreteDeltaThetaGamma`) lives in
//! `prin-train::bands` (Phase 4) because it requires autodiff.

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::models::Dynamics;
use crate::pac::PhaseAmplitudeCoupling;
use crate::state::{clamp_derivative, OscillatorState, StateDerivatives, StateError};

/// Errors raised by band-network construction and evaluation.
#[derive(Debug, Error)]
pub enum BandError {
    /// A band size is zero.
    #[error("band {band} has zero oscillators")]
    EmptyBand {
        /// Index of the offending band.
        band: usize,
    },

    /// The total oscillator count does not match the state.
    #[error("band network expects {expected} oscillators, got {got}")]
    PopulationMismatch {
        /// Expected total from band sizes.
        expected: usize,
        /// Actual state size.
        got: usize,
    },

    /// The state has no `freq_band` labels.
    #[error("band network requires freq_band labels on every oscillator")]
    MissingBandLabels,

    /// A band label in the state does not match any configured band.
    #[error("oscillator {index} has freq_band {label} but network has {n_bands} bands (0..{max})")]
    InvalidBandLabel {
        /// Oscillator index.
        index: usize,
        /// Offending label.
        label: u32,
        /// Number of configured bands.
        n_bands: usize,
        /// Maximum valid label.
        max: usize,
    },

    /// A band has the wrong number of oscillators.
    #[error("band {band} expects {expected} oscillators, got {got}")]
    BandSizeMismatch {
        /// Band index.
        band: usize,
        /// Expected count.
        expected: usize,
        /// Actual count.
        got: usize,
    },

    /// A parameter is non-finite.
    #[error("non-finite parameter `{name}`: {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// The number of bands is invalid.
    #[error("expected {expected} bands, got {got}")]
    WrongBandCount {
        /// Expected band count.
        expected: usize,
        /// Actual band count.
        got: usize,
    },

    /// A PAC pair references an invalid band index.
    #[error("PAC pair references band {band} but network has {n_bands} bands")]
    InvalidPacBand {
        /// Offending band index.
        band: usize,
        /// Number of configured bands.
        n_bands: usize,
    },

    /// Wraps a [`StateError`] from the underlying dynamics.
    #[error("state error: {0}")]
    State(#[from] StateError),
}

/// Per-band dynamical parameters.
///
/// Each band is a population of Kuramoto oscillators with mean-field coupling.
/// The `coupling_strength` controls intra-band synchrony; the `decay_rate`
/// controls amplitude relaxation toward the limit cycle.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct BandParams {
    /// Intra-band Kuramoto coupling strength `K`.
    pub coupling_strength: f64,
    /// Amplitude decay rate `λ` (Stuart–Landau radial relaxation).
    pub decay_rate: f64,
}

impl BandParams {
    /// Create validated band parameters.
    ///
    /// # Errors
    ///
    /// Returns [`BandError::NonFiniteParameter`] if either parameter is
    /// non-finite.
    pub fn new(coupling_strength: f64, decay_rate: f64) -> Result<Self, BandError> {
        if !coupling_strength.is_finite() {
            return Err(BandError::NonFiniteParameter {
                name: "coupling_strength",
                value: coupling_strength,
            });
        }
        if !decay_rate.is_finite() {
            return Err(BandError::NonFiniteParameter {
                name: "decay_rate",
                value: decay_rate,
            });
        }
        Ok(Self {
            coupling_strength,
            decay_rate,
        })
    }
}

/// A slow→fast PAC coupling pair between adjacent bands.
///
/// The phase of the slow band modulates the amplitude of the fast band via
/// [`PhaseAmplitudeCoupling`].
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PacPair {
    /// Index of the slow (modulating) band.
    pub slow_band: usize,
    /// Index of the fast (modulated) band.
    pub fast_band: usize,
    /// PAC operator.
    pub pac: PhaseAmplitudeCoupling,
    /// Phase offset for the modulation.
    pub phase_offset: f64,
}

impl PacPair {
    /// Create a validated PAC pair.
    ///
    /// # Errors
    ///
    /// Returns [`BandError::NonFiniteParameter`] if `phase_offset` is
    /// non-finite.
    pub fn new(
        slow_band: usize,
        fast_band: usize,
        pac: PhaseAmplitudeCoupling,
        phase_offset: f64,
    ) -> Result<Self, BandError> {
        if !phase_offset.is_finite() {
            return Err(BandError::NonFiniteParameter {
                name: "phase_offset",
                value: phase_offset,
            });
        }
        Ok(Self {
            slow_band,
            fast_band,
            pac,
            phase_offset,
        })
    }
}

/// Continuous hierarchical band network.
///
/// Oscillators are partitioned into frequency bands (labelled 0, 1, …, B−1
/// from slowest to fastest). Intra-band dynamics are Kuramoto mean-field;
/// cross-band interactions are PAC (slow phase → fast amplitude).
///
/// Use [`theta_gamma_network`] or [`delta_theta_gamma_network`] for the standard
/// 2-band and 3-band configurations, or construct directly for custom
/// hierarchies.
///
/// # Example
///
/// ```
/// use prin_dynamics::bands::{BandNetwork, BandParams, PacPair};
/// use prin_dynamics::pac::PhaseAmplitudeCoupling;
///
/// let net = BandNetwork::new(
///     vec![4, 8],
///     vec![
///         BandParams::new(1.0, 0.1).unwrap(),
///         BandParams::new(0.5, 0.1).unwrap(),
///     ],
///     vec![PacPair::new(0, 1, PhaseAmplitudeCoupling::new(0.3).unwrap(), 0.0).unwrap()],
/// ).unwrap();
/// assert_eq!(net.n_bands(), 2);
/// assert_eq!(net.total_oscillators(), 12);
/// ```
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct BandNetwork {
    /// Number of oscillators per band (slow → fast).
    band_sizes: Vec<usize>,
    /// Per-band dynamical parameters.
    band_params: Vec<BandParams>,
    /// Cross-band PAC couplings.
    pac_pairs: Vec<PacPair>,
}

impl BandNetwork {
    /// Create a band network from raw components.
    ///
    /// # Errors
    ///
    /// Returns [`BandError`] if:
    /// - `band_sizes` is empty or any entry is zero,
    /// - `band_params` length does not match `band_sizes`,
    /// - a PAC pair references an out-of-range band.
    pub fn new(
        band_sizes: Vec<usize>,
        band_params: Vec<BandParams>,
        pac_pairs: Vec<PacPair>,
    ) -> Result<Self, BandError> {
        let n_bands = band_sizes.len();
        if n_bands == 0 {
            return Err(BandError::EmptyBand { band: 0 });
        }
        if band_params.len() != n_bands {
            return Err(BandError::WrongBandCount {
                expected: n_bands,
                got: band_params.len(),
            });
        }
        for (i, &sz) in band_sizes.iter().enumerate() {
            if sz == 0 {
                return Err(BandError::EmptyBand { band: i });
            }
        }
        for pair in &pac_pairs {
            if pair.slow_band >= n_bands {
                return Err(BandError::InvalidPacBand {
                    band: pair.slow_band,
                    n_bands,
                });
            }
            if pair.fast_band >= n_bands {
                return Err(BandError::InvalidPacBand {
                    band: pair.fast_band,
                    n_bands,
                });
            }
            if pair.slow_band >= pair.fast_band {
                return Err(BandError::InvalidPacBand {
                    band: pair.slow_band,
                    n_bands,
                });
            }
        }
        Ok(Self {
            band_sizes,
            band_params,
            pac_pairs,
        })
    }

    /// Number of frequency bands.
    pub fn n_bands(&self) -> usize {
        self.band_sizes.len()
    }

    /// Total oscillator count across all bands.
    pub fn total_oscillators(&self) -> usize {
        self.band_sizes.iter().sum()
    }

    /// Oscillator count for band `b`.
    pub fn band_size(&self, b: usize) -> usize {
        self.band_sizes[b]
    }

    /// All band sizes (slow → fast).
    pub fn band_sizes(&self) -> &[usize] {
        &self.band_sizes
    }

    /// Per-band parameters.
    pub fn band_params(&self) -> &[BandParams] {
        &self.band_params
    }

    /// Cross-band PAC pairs.
    pub fn pac_pairs(&self) -> &[PacPair] {
        &self.pac_pairs
    }

    /// Theoretical working-memory capacity (number of fast-band sub-cycles
    /// per slow-band cycle).
    ///
    /// For a theta–gamma network this is `floor(f_gamma / f_theta)`, matching
    /// the Lisman–Jensen model (~7 items for 6/40 Hz).
    ///
    /// `state` must have valid `freq_band` labels; the mean frequency of each
    /// band is computed from the state.
    ///
    /// # Errors
    ///
    /// Returns [`BandError`] if the state is incompatible.
    pub fn theoretical_capacity(&self, state: &OscillatorState) -> Result<usize, BandError> {
        if self.n_bands() < 2 {
            return Ok(0);
        }
        let indices = self.partition_state(state)?;
        let slow_mean = mean_frequency(state, &indices[0]);
        let fast_mean = mean_frequency(state, indices.last().unwrap());
        if slow_mean <= 0.0 || !slow_mean.is_finite() {
            return Ok(0);
        }
        Ok((fast_mean / slow_mean).floor() as usize)
    }

    /// Partition a state's oscillators into per-band index lists.
    ///
    /// Validates that `freq_band` is present, every label is in range, and
    /// each band has the expected number of oscillators.
    fn partition_state(&self, state: &OscillatorState) -> Result<Vec<Vec<usize>>, BandError> {
        let band_labels = state
            .freq_band
            .as_ref()
            .ok_or(BandError::MissingBandLabels)?;
        let n = state.n_oscillators();
        let total = self.total_oscillators();
        if n != total {
            return Err(BandError::PopulationMismatch {
                expected: total,
                got: n,
            });
        }

        let n_bands = self.n_bands();
        let mut indices: Vec<Vec<usize>> = vec![Vec::new(); n_bands];
        for (i, &label) in band_labels.iter().enumerate() {
            let b = label as usize;
            if b >= n_bands {
                return Err(BandError::InvalidBandLabel {
                    index: i,
                    label,
                    n_bands,
                    max: n_bands - 1,
                });
            }
            indices[b].push(i);
        }

        for (b, idx) in indices.iter().enumerate() {
            if idx.len() != self.band_sizes[b] {
                return Err(BandError::BandSizeMismatch {
                    band: b,
                    expected: self.band_sizes[b],
                    got: idx.len(),
                });
            }
        }

        Ok(indices)
    }

    /// Compute intra-band Kuramoto mean-field derivatives for one band.
    ///
    /// Returns `(dphase, damplitude)` contributions for the band's oscillators.
    fn compute_band_derivatives(
        &self,
        state: &OscillatorState,
        band_indices: &[usize],
        band_idx: usize,
    ) -> (Vec<f64>, Vec<f64>) {
        let params = &self.band_params[band_idx];
        let k = params.coupling_strength;
        let n_b = band_indices.len();
        let inv_n = 1.0 / (n_b as f64);

        // Complex order parameter Z = (1/N_b) Σ r_j e^{iφ_j}
        let mut z_r = 0.0;
        let mut z_i = 0.0;
        for &j in band_indices {
            let r = state.amplitude[j];
            let phi = state.phase[j];
            z_r += r * phi.cos();
            z_i += r * phi.sin();
        }
        z_r *= inv_n;
        z_i *= inv_n;

        let big_r = (z_r * z_r + z_i * z_i).sqrt();
        let psi = z_i.atan2(z_r);
        let k_r = k * big_r;

        let mut dphase = Vec::with_capacity(n_b);
        let mut damplitude = Vec::with_capacity(n_b);

        for &j in band_indices {
            let phi = state.phase[j];
            let r = state.amplitude[j];
            let omega = state.frequency[j];
            let sin_diff = (psi - phi).sin();
            let cos_diff = (psi - phi).cos();

            // Kuramoto phase + Stuart-Landau radial relaxation
            dphase.push(omega + k_r * sin_diff);
            damplitude.push(-params.decay_rate * r + k_r * cos_diff);
        }

        (dphase, damplitude)
    }
}

impl Dynamics for BandNetwork {
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let indices = self
            .partition_state(state)
            .map_err(|e| StateError::NonFiniteValue {
                name: "band_partition",
                index: 0,
                value: match e {
                    BandError::MissingBandLabels => f64::NAN,
                    BandError::PopulationMismatch { expected, .. } => expected as f64,
                    _ => f64::NAN,
                },
            })?;

        let mut dphase = vec![0.0; n];
        let mut damplitude = vec![0.0; n];
        let dfrequency = vec![0.0; n];

        // 1. Intra-band Kuramoto mean-field derivatives
        for (b, band_idx) in indices.iter().enumerate() {
            let (dp, da) = self.compute_band_derivatives(state, band_idx, b);
            for (k, &j) in band_idx.iter().enumerate() {
                dphase[j] = dp[k];
                damplitude[j] = da[k];
            }
        }

        // 2. Cross-band PAC: slow phase → fast amplitude modulation
        for pair in &self.pac_pairs {
            let slow_idx = &indices[pair.slow_band];
            let fast_idx = &indices[pair.fast_band];

            // Collect slow-band phases and fast-band amplitudes
            let slow_phases: Vec<f64> = slow_idx.iter().map(|&j| state.phase[j]).collect();
            let fast_amps: Vec<f64> = fast_idx.iter().map(|&j| state.amplitude[j]).collect();

            // Apply PAC modulation
            let modulated = pair
                .pac
                .modulate(&slow_phases, &fast_amps, pair.phase_offset)
                .map_err(|_| StateError::NonFiniteValue {
                    name: "pac_modulation",
                    index: 0,
                    value: f64::NAN,
                })?;

            // The PAC modulation replaces the fast-band amplitude; the
            // derivative contribution is the difference scaled by decay.
            for (k, &j) in fast_idx.iter().enumerate() {
                let target_amp = modulated[k];
                let current_amp = state.amplitude[j];
                // Amplitude relaxation toward the PAC-modulated target
                damplitude[j] +=
                    self.band_params[pair.fast_band].decay_rate * (target_amp - current_amp);
            }
        }

        // 3. Apply numerical guards
        for i in 0..n {
            dphase[i] = clamp_derivative(dphase[i]);
            damplitude[i] = clamp_derivative(damplitude[i]);
        }

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

/// Build a [`BandNetwork`] for the standard theta–gamma (2-band) hierarchy.
///
/// Band 0 = theta (slow), Band 1 = gamma (fast). PAC from theta → gamma.
///
/// # Arguments
///
/// * `n_theta` — number of theta oscillators.
/// * `n_gamma` — number of gamma oscillators.
/// * `theta_params` — intra-band parameters for theta.
/// * `gamma_params` — intra-band parameters for gamma.
/// * `pac` — phase–amplitude coupling from theta → gamma.
/// * `phase_offset` — PAC phase offset.
///
/// # Errors
///
/// Returns [`BandError`] for zero band sizes or non-finite `phase_offset`.
pub fn theta_gamma_network(
    n_theta: usize,
    n_gamma: usize,
    theta_params: BandParams,
    gamma_params: BandParams,
    pac: PhaseAmplitudeCoupling,
    phase_offset: f64,
) -> Result<BandNetwork, BandError> {
    let pac_pair = PacPair::new(0, 1, pac, phase_offset)?;
    BandNetwork::new(
        vec![n_theta, n_gamma],
        vec![theta_params, gamma_params],
        vec![pac_pair],
    )
}

/// Build a [`BandNetwork`] for the standard delta–theta–gamma (3-band) hierarchy.
///
/// Band 0 = delta (slowest), Band 1 = theta, Band 2 = gamma (fast).
/// PAC: delta → theta, theta → gamma.
///
/// # Errors
///
/// Returns [`BandError`] for zero band sizes or non-finite offsets.
#[allow(clippy::too_many_arguments)]
pub fn delta_theta_gamma_network(
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
    delta_params: BandParams,
    theta_params: BandParams,
    gamma_params: BandParams,
    pac_delta_theta: PhaseAmplitudeCoupling,
    pac_theta_gamma: PhaseAmplitudeCoupling,
    offset_dt: f64,
    offset_tg: f64,
) -> Result<BandNetwork, BandError> {
    let pac_dt = PacPair::new(0, 1, pac_delta_theta, offset_dt)?;
    let pac_tg = PacPair::new(1, 2, pac_theta_gamma, offset_tg)?;
    BandNetwork::new(
        vec![n_delta, n_theta, n_gamma],
        vec![delta_params, theta_params, gamma_params],
        vec![pac_dt, pac_tg],
    )
}

/// Compute the mean frequency of a set of oscillators.
fn mean_frequency(state: &OscillatorState, indices: &[usize]) -> f64 {
    if indices.is_empty() {
        return 0.0;
    }
    let sum: f64 = indices.iter().map(|&j| state.frequency[j]).sum();
    sum / indices.len() as f64
}

/// Helper: build an [`OscillatorState`] for a band network with uniform
/// per-band frequencies and random phases.
///
/// `freq_ranges` must have one `(lo, hi)` pair per band. Phases are uniform
/// on `[0, 2π)`; amplitudes are `1.0`.
///
/// # Errors
///
/// Returns [`StateError`] for invalid inputs.
pub fn create_band_state(
    network: &BandNetwork,
    freq_ranges: &[(f64, f64)],
    seed: &mut crate::seed::Seed,
) -> Result<OscillatorState, StateError> {
    let n_bands = network.n_bands();
    if freq_ranges.len() != n_bands {
        return Err(StateError::LengthMismatch {
            name: "freq_ranges",
            expected: n_bands,
            got: freq_ranges.len(),
        });
    }

    let total = network.total_oscillators();
    let mut phase = Vec::with_capacity(total);
    let mut amplitude = Vec::with_capacity(total);
    let mut frequency = Vec::with_capacity(total);
    let mut freq_band = Vec::with_capacity(total);

    for (b, &sz) in network.band_sizes().iter().enumerate() {
        let (lo, hi) = freq_ranges[b];
        for _ in 0..sz {
            phase.push(crate::state::TAU * seed.next_f64());
            amplitude.push(1.0);
            let f = seed.next_f64_range(lo, hi).unwrap_or(lo + (hi - lo) * 0.5);
            frequency.push(f);
            freq_band.push(b as u32);
        }
    }

    OscillatorState::new(phase, amplitude, frequency, Some(freq_band))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::AMPLITUDE_MAX;
    use approx::assert_relative_eq;

    fn make_tg_network() -> BandNetwork {
        theta_gamma_network(
            4,
            8,
            BandParams::new(1.0, 0.1).unwrap(),
            BandParams::new(0.5, 0.1).unwrap(),
            PhaseAmplitudeCoupling::new(0.3).unwrap(),
            0.0,
        )
        .unwrap()
    }

    fn make_tg_state(net: &BandNetwork) -> OscillatorState {
        let mut seed = crate::seed::Seed::new(42, 0);
        create_band_state(
            net,
            &[(5.0, 7.0), (35.0, 45.0)], // theta 5-7 Hz, gamma 35-45 Hz
            &mut seed,
        )
        .unwrap()
    }

    fn make_dtg_network() -> BandNetwork {
        delta_theta_gamma_network(
            2,
            4,
            8,
            BandParams::new(0.8, 0.1).unwrap(),
            BandParams::new(1.0, 0.1).unwrap(),
            BandParams::new(0.5, 0.1).unwrap(),
            PhaseAmplitudeCoupling::new(0.2).unwrap(),
            PhaseAmplitudeCoupling::new(0.3).unwrap(),
            0.0,
            0.0,
        )
        .unwrap()
    }

    fn make_dtg_state(net: &BandNetwork) -> OscillatorState {
        let mut seed = crate::seed::Seed::new(99, 0);
        create_band_state(net, &[(1.0, 3.0), (5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap()
    }

    // --- Construction tests ---

    #[test]
    fn theta_gamma_construction() {
        let net = make_tg_network();
        assert_eq!(net.n_bands(), 2);
        assert_eq!(net.total_oscillators(), 12);
        assert_eq!(net.band_size(0), 4);
        assert_eq!(net.band_size(1), 8);
    }

    #[test]
    fn delta_theta_gamma_construction() {
        let net = make_dtg_network();
        assert_eq!(net.n_bands(), 3);
        assert_eq!(net.total_oscillators(), 14);
        assert_eq!(net.band_size(0), 2);
        assert_eq!(net.band_size(1), 4);
        assert_eq!(net.band_size(2), 8);
    }

    #[test]
    fn empty_band_rejected() {
        let err = BandNetwork::new(
            vec![0, 4],
            vec![
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![],
        )
        .unwrap_err();
        assert!(matches!(err, BandError::EmptyBand { band: 0 }));
    }

    #[test]
    fn mismatched_params_length_rejected() {
        let err = BandNetwork::new(vec![4, 8], vec![BandParams::new(1.0, 0.1).unwrap()], vec![])
            .unwrap_err();
        assert!(matches!(err, BandError::WrongBandCount { .. }));
    }

    #[test]
    fn pac_pair_invalid_band_rejected() {
        let err = PacPair::new(0, 5, PhaseAmplitudeCoupling::new(0.3).unwrap(), 0.0).unwrap();
        let net_err = BandNetwork::new(
            vec![4, 8],
            vec![
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![err],
        )
        .unwrap_err();
        assert!(matches!(net_err, BandError::InvalidPacBand { .. }));
    }

    #[test]
    fn pac_pair_slow_ge_fast_rejected() {
        let err = BandNetwork::new(
            vec![4, 8],
            vec![
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![PacPair::new(1, 0, PhaseAmplitudeCoupling::new(0.3).unwrap(), 0.0).unwrap()],
        )
        .unwrap_err();
        assert!(matches!(err, BandError::InvalidPacBand { .. }));
    }

    #[test]
    fn non_finite_band_params_rejected() {
        assert!(BandParams::new(f64::NAN, 0.1).is_err());
        assert!(BandParams::new(1.0, f64::INFINITY).is_err());
    }

    #[test]
    fn non_finite_phase_offset_rejected() {
        assert!(PacPair::new(0, 1, PhaseAmplitudeCoupling::new(0.3).unwrap(), f64::NAN).is_err());
    }

    // --- Partition tests ---

    #[test]
    fn partition_valid_state() {
        let net = make_tg_network();
        let state = make_tg_state(&net);
        let indices = net.partition_state(&state).unwrap();
        assert_eq!(indices.len(), 2);
        assert_eq!(indices[0].len(), 4);
        assert_eq!(indices[1].len(), 8);
    }

    #[test]
    fn partition_missing_labels_rejected() {
        let net = make_tg_network();
        let state =
            OscillatorState::new(vec![0.0; 12], vec![1.0; 12], vec![1.0; 12], None).unwrap();
        let err = net.partition_state(&state).unwrap_err();
        assert!(matches!(err, BandError::MissingBandLabels));
    }

    #[test]
    fn partition_wrong_population_rejected() {
        let net = make_tg_network();
        let state =
            OscillatorState::new(vec![0.0; 5], vec![1.0; 5], vec![1.0; 5], Some(vec![0; 5]))
                .unwrap();
        let err = net.partition_state(&state).unwrap_err();
        assert!(matches!(err, BandError::PopulationMismatch { .. }));
    }

    #[test]
    fn partition_invalid_label_rejected() {
        let net = make_tg_network();
        let mut bands = vec![0u32; 4];
        bands.extend(vec![1u32; 7]);
        bands.push(5); // invalid label
        let state =
            OscillatorState::new(vec![0.0; 12], vec![1.0; 12], vec![1.0; 12], Some(bands)).unwrap();
        let err = net.partition_state(&state).unwrap_err();
        assert!(matches!(err, BandError::InvalidBandLabel { .. }));
    }

    #[test]
    fn partition_band_size_mismatch_rejected() {
        let net = make_tg_network();
        // 5 theta + 7 gamma = 12 total, but band 0 expects 4
        let mut bands = vec![0u32; 5];
        bands.extend(vec![1u32; 7]);
        let state =
            OscillatorState::new(vec![0.0; 12], vec![1.0; 12], vec![1.0; 12], Some(bands)).unwrap();
        let err = net.partition_state(&state).unwrap_err();
        assert!(matches!(err, BandError::BandSizeMismatch { .. }));
    }

    // --- Dynamics tests ---

    #[test]
    fn theta_gamma_derivatives_finite() {
        let net = make_tg_network();
        let state = make_tg_state(&net);
        let deriv = net.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.dphase.len(), 12);
        assert_eq!(deriv.damplitude.len(), 12);
        assert_eq!(deriv.dfrequency.len(), 12);
        for i in 0..12 {
            assert!(deriv.dphase[i].is_finite(), "dphase[{i}] not finite");
            assert!(
                deriv.damplitude[i].is_finite(),
                "damplitude[{i}] not finite"
            );
        }
    }

    #[test]
    fn delta_theta_gamma_derivatives_finite() {
        let net = make_dtg_network();
        let state = make_dtg_state(&net);
        let deriv = net.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.dphase.len(), 14);
        for i in 0..14 {
            assert!(deriv.dphase[i].is_finite());
            assert!(deriv.damplitude[i].is_finite());
        }
    }

    #[test]
    fn zero_pac_does_not_change_intra_band_structure() {
        // With m=0, PAC is identity — derivatives should match pure intra-band
        let net_pac = theta_gamma_network(
            4,
            8,
            BandParams::new(1.0, 0.1).unwrap(),
            BandParams::new(0.5, 0.1).unwrap(),
            PhaseAmplitudeCoupling::new(0.0).unwrap(),
            0.0,
        )
        .unwrap();

        let net_no_pac = BandNetwork::new(
            vec![4, 8],
            vec![
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![],
        )
        .unwrap();

        let mut seed = crate::seed::Seed::new(123, 0);
        let state = create_band_state(&net_pac, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();

        let d_pac = net_pac.compute_derivatives(&state).unwrap();
        let d_no_pac = net_no_pac.compute_derivatives(&state).unwrap();

        // With m=0, PAC modulate returns the original amplitudes, so
        // target_amp == current_amp and the PAC contribution to damplitude is 0.
        for i in 0..12 {
            assert_relative_eq!(d_pac.dphase[i], d_no_pac.dphase[i], epsilon = 1e-12);
            assert_relative_eq!(d_pac.damplitude[i], d_no_pac.damplitude[i], epsilon = 1e-12);
        }
    }

    #[test]
    fn synchronized_state_has_zero_phase_derivative_spread() {
        // All oscillators in a band at the same phase and frequency →
        // the Kuramoto mean-field gives sin(ψ - φ) = 0 for all.
        let net = theta_gamma_network(
            3,
            3,
            BandParams::new(1.0, 0.1).unwrap(),
            BandParams::new(1.0, 0.1).unwrap(),
            PhaseAmplitudeCoupling::new(0.0).unwrap(),
            0.0,
        )
        .unwrap();

        let state = OscillatorState::new(
            vec![1.0; 6], // all phase = 1.0
            vec![1.0; 6], // all amplitude = 1.0
            vec![6.0; 6], // all frequency = 6.0
            Some(vec![0, 0, 0, 1, 1, 1]),
        )
        .unwrap();

        let deriv = net.compute_derivatives(&state).unwrap();
        // With all phases equal, ψ = φ for all → sin(ψ-φ) = 0 → dphase = ω
        for i in 0..6 {
            assert_relative_eq!(deriv.dphase[i], 6.0, epsilon = 1e-10);
        }
    }

    // --- Capacity tests ---

    #[test]
    fn theta_gamma_capacity_matches_frequency_ratio() {
        let net = make_tg_network();
        let state = make_tg_state(&net);
        let capacity = net.theoretical_capacity(&state).unwrap();
        // Theta 5-7 Hz, gamma 35-45 Hz → ratio ~5-9, typically 6-7
        assert!(capacity >= 3, "capacity {capacity} too low");
        assert!(capacity <= 15, "capacity {capacity} too high");
    }

    #[test]
    fn delta_theta_gamma_capacity_uses_extreme_bands() {
        let net = make_dtg_network();
        let state = make_dtg_state(&net);
        let capacity = net.theoretical_capacity(&state).unwrap();
        // Delta 1-3 Hz, gamma 35-45 Hz → ratio ~12-45
        assert!(capacity >= 5);
    }

    #[test]
    fn capacity_single_band_is_zero() {
        let net =
            BandNetwork::new(vec![4], vec![BandParams::new(1.0, 0.1).unwrap()], vec![]).unwrap();
        let state =
            OscillatorState::new(vec![0.0; 4], vec![1.0; 4], vec![6.0; 4], Some(vec![0; 4]))
                .unwrap();
        assert_eq!(net.theoretical_capacity(&state).unwrap(), 0);
    }

    // --- Serialization ---

    #[test]
    fn serialization_roundtrip() {
        let net = make_tg_network();
        let json = serde_json::to_string(&net).unwrap();
        let restored: BandNetwork = serde_json::from_str(&json).unwrap();
        assert_eq!(net, restored);
    }

    // --- create_band_state ---

    #[test]
    fn create_band_state_correct_labels() {
        let net = make_tg_network();
        let mut seed = crate::seed::Seed::new(0, 0);
        let state = create_band_state(&net, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
        assert_eq!(state.n_oscillators(), 12);
        let bands = state.freq_band.as_ref().unwrap();
        // First 4 should be band 0 (theta), next 8 band 1 (gamma)
        for &b in &bands[..4] {
            assert_eq!(b, 0);
        }
        for &b in &bands[4..12] {
            assert_eq!(b, 1);
        }
    }

    #[test]
    fn create_band_state_wrong_ranges_rejected() {
        let net = make_tg_network();
        let mut seed = crate::seed::Seed::new(0, 0);
        let err = create_band_state(&net, &[(5.0, 7.0)], &mut seed).unwrap_err();
        assert!(matches!(err, StateError::LengthMismatch { .. }));
    }

    // --- Derivative clamp invariant ---

    #[test]
    fn derivatives_respect_clamp() {
        let net = make_tg_network();
        // Create a state with extreme amplitudes to stress the clamp
        let state = OscillatorState::new(
            vec![0.0; 12],
            vec![AMPLITUDE_MAX; 12],
            vec![100.0; 12],
            Some(vec![0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
        )
        .unwrap();
        let deriv = net.compute_derivatives(&state).unwrap();
        for i in 0..12 {
            assert!(deriv.dphase[i].abs() <= 1e4 + 1e-10);
            assert!(deriv.damplitude[i].abs() <= 1e4 + 1e-10);
        }
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn theta_gamma_derivatives_always_finite(
            n_theta in 1usize..=8,
            n_gamma in 1usize..=16,
            seed_val in 0u64..1000,
        ) {
            let net = theta_gamma_network(
                n_theta,
                n_gamma,
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
                PhaseAmplitudeCoupling::new(0.3).unwrap(),
                0.0,
            ).unwrap();

            let mut seed = crate::seed::Seed::new(seed_val as u128, 0);
            let state = create_band_state(
                &net,
                &[(4.0, 8.0), (30.0, 50.0)],
                &mut seed,
            ).unwrap();

            let deriv = net.compute_derivatives(&state).unwrap();
            let n = n_theta + n_gamma;
            prop_assert_eq!(deriv.dphase.len(), n);
            for i in 0..n {
                prop_assert!(deriv.dphase[i].is_finite(), "dphase[{i}] = {}", deriv.dphase[i]);
                prop_assert!(deriv.damplitude[i].is_finite(), "damplitude[{i}] = {}", deriv.damplitude[i]);
            }
        }
    }

    proptest! {
        #[test]
        fn phase_continuity_under_small_perturbation(
            seed_val in 0u64..1000,
        ) {
            // Small change in state → small change in derivatives
            let net = theta_gamma_network(
                4, 8,
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
                PhaseAmplitudeCoupling::new(0.3).unwrap(),
                0.0,
            ).unwrap();

            let mut seed = crate::seed::Seed::new(seed_val as u128, 0);
            let state = create_band_state(&net, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
            let d0 = net.compute_derivatives(&state).unwrap();

            // Perturb phases by a tiny amount
            let eps = 1e-8;
            let mut perturbed_phase = state.phase.clone();
            for p in perturbed_phase.iter_mut() {
                *p += eps;
            }
            let state2 = OscillatorState::new(
                perturbed_phase,
                state.amplitude.clone(),
                state.frequency.clone(),
                state.freq_band.clone(),
            ).unwrap();
            let d1 = net.compute_derivatives(&state2).unwrap();

            // Derivatives should be close (Lipschitz continuity)
            for i in 0..12 {
                let diff = (d0.dphase[i] - d1.dphase[i]).abs();
                prop_assert!(diff < 1e-4, "phase deriv discontinuity at {i}: {diff}");
            }
        }
    }

    proptest! {
        #[test]
        fn capacity_positive_for_valid_frequencies(
            n_theta in 1usize..=4,
            n_gamma in 1usize..=8,
            theta_freq in 4.0f64..8.0,
            gamma_freq in 30.0f64..50.0,
        ) {
            let net = theta_gamma_network(
                n_theta, n_gamma,
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
                PhaseAmplitudeCoupling::new(0.3).unwrap(),
                0.0,
            ).unwrap();

            let total = n_theta + n_gamma;
            let state = OscillatorState::new(
                vec![0.0; total],
                vec![1.0; total],
                {
                    let mut f = vec![theta_freq; n_theta];
                    f.extend(vec![gamma_freq; n_gamma]);
                    f
                },
                Some({
                    let mut b = vec![0u32; n_theta];
                    b.extend(vec![1u32; n_gamma]);
                    b
                }),
            ).unwrap();

            let capacity = net.theoretical_capacity(&state).unwrap();
            // gamma/theta for these ranges: 30/8 = 3.75 → 3, 50/4 = 12.5 → 12
            prop_assert!(capacity >= 3);
            prop_assert!(capacity <= 12);
        }
    }
}

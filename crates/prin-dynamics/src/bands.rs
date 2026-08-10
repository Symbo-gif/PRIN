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
//! dynamics are evaluated by [`KuramotoOscillator`] on the band's sub-state, so
//! every [`CouplingMode`] (mean-field, full pairwise, sparse k-NN) is available
//! per band; cross-band interactions use [`PhaseAmplitudeCoupling`].
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! PRINet 3.0's `ThetaGammaNetwork` / `DeltaThetaGammaNetwork` are *steppers*:
//! they hold one `KuramotoOscillator` (`coupling_mode="sparse_knn"`) per band,
//! step the slow band, overwrite the fast band's amplitudes with the PAC-
//! modulated values, and then advance the fast band with a `MultiRateIntegrator`
//! whose `sub_steps` is `floor(f_fast / f_slow)`.
//!
//! [`BandNetwork`] instead exposes the hierarchy as a single continuous ODE
//! right-hand side over the concatenated state, so it composes with every PRIN
//! [`Integrator`](crate::integrate::Integrator) rather than embedding one. The
//! consequences, recorded as Project Plan amendment #19, are:
//!
//! - **Intra-band terms are identical** to the reference for the configured
//!   [`CouplingMode`] (verified in `tests/parity_bands.rs` against
//!   `prinet==3.0.0`).
//! - **PAC is a relaxation term, not an assignment.** The reference replaces
//!   `A_fast` with `A_fast·[1 + m·cos(mean(φ_slow) + offset)]` between band
//!   steps; the continuous form adds `λ_fast·(A_target − A_fast)` to
//!   `dA_fast/dt`, which relaxes toward the same target on the band's own
//!   amplitude timescale.
//! - **Sub-stepping is the integrator's job.** The reference's per-band
//!   `sub_steps` is reproduced by driving a `BandNetwork` with
//!   [`MultiRateIntegrator`](crate::integrate::MultiRateIntegrator); the ratio
//!   itself is available as [`BandNetwork::theoretical_capacity`].
//!
//! The trainable discrete-time variant (`DiscreteDeltaThetaGamma`) lives in
//! `prin-train::bands` (Phase 4) because it requires autodiff.

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::coupling::CouplingMode;
use crate::models::{Dynamics, KuramotoOscillator};
use crate::pac::PhaseAmplitudeCoupling;
use crate::state::{clamp_derivative, OscillatorState, StateDerivatives, StateError};

/// Errors raised by band-network construction and evaluation.
#[derive(Debug, Error)]
pub enum BandError {
    /// The band list itself is empty (no bands were configured).
    #[error("band network requires at least one band, got an empty band list")]
    NoBands,

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
/// Each band is a population of [`KuramotoOscillator`]s. The
/// `coupling_strength` controls intra-band synchrony, `decay_rate` controls
/// amplitude relaxation toward the limit cycle, `freq_adaptation_rate` is the
/// Kuramoto frequency-adaptation rate `γ`, and `coupling_mode` selects how the
/// intra-band coupling term is evaluated.
///
/// [`BandParams::new`] keeps the PRIN default of mean-field coupling with
/// `γ = 0` (frozen natural frequencies); [`BandParams::with_coupling`] exposes
/// the full [`KuramotoOscillator`] parameterisation, including the
/// `sparse_knn` mode used by the PRINet 3.0 reference networks.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct BandParams {
    /// Intra-band Kuramoto coupling strength `K`.
    pub coupling_strength: f64,
    /// Amplitude decay rate `λ` (Stuart–Landau radial relaxation).
    pub decay_rate: f64,
    /// Kuramoto frequency-adaptation rate `γ`.
    pub freq_adaptation_rate: f64,
    /// Intra-band coupling evaluation mode.
    pub coupling_mode: CouplingMode,
}

impl BandParams {
    /// Create validated band parameters with mean-field coupling and no
    /// frequency adaptation (`γ = 0`).
    ///
    /// # Errors
    ///
    /// Returns [`BandError::NonFiniteParameter`] if either parameter is
    /// non-finite.
    pub fn new(coupling_strength: f64, decay_rate: f64) -> Result<Self, BandError> {
        Self::with_coupling(coupling_strength, decay_rate, 0.0, CouplingMode::MeanField)
    }

    /// Create validated band parameters with an explicit frequency-adaptation
    /// rate and [`CouplingMode`].
    ///
    /// Use `CouplingMode::SparseKnn { k }` to match the PRINet 3.0
    /// `ThetaGammaNetwork` / `DeltaThetaGammaNetwork` reference configuration.
    ///
    /// # Errors
    ///
    /// Returns [`BandError::NonFiniteParameter`] if any parameter is
    /// non-finite. The `coupling_mode` is validated against the band's
    /// oscillator count when the [`BandNetwork`] is constructed.
    pub fn with_coupling(
        coupling_strength: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        coupling_mode: CouplingMode,
    ) -> Result<Self, BandError> {
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
        if !freq_adaptation_rate.is_finite() {
            return Err(BandError::NonFiniteParameter {
                name: "freq_adaptation_rate",
                value: freq_adaptation_rate,
            });
        }
        Ok(Self {
            coupling_strength,
            decay_rate,
            freq_adaptation_rate,
            coupling_mode,
        })
    }

    /// Build the [`KuramotoOscillator`] that evaluates this band's intra-band
    /// dynamics for a population of `n` oscillators.
    ///
    /// The model is a plain value type (five scalars plus the coupling mode),
    /// so constructing it per derivative evaluation costs `O(1)` for
    /// `MeanField`/`SparseKnn` and `O(n²)` for an explicit
    /// `Full { matrix: Some(..) }` — the same order as evaluating that mode.
    fn model(&self, n: usize) -> Result<KuramotoOscillator, StateError> {
        KuramotoOscillator::new(
            n,
            self.coupling_strength,
            self.decay_rate,
            self.freq_adaptation_rate,
            self.coupling_mode.clone(),
        )
    }
}

/// A slow→fast PAC coupling pair.
///
/// The phase of the slow band modulates the amplitude of the fast band via
/// [`PhaseAmplitudeCoupling`]. Adjacent pairs (delta→theta, theta→gamma) are
/// the standard hierarchy and the only ones the PRINet 3.0 reference networks
/// build, but any strictly slow→fast pair (`slow_band < fast_band`) is
/// permitted so that non-adjacent couplings such as delta→gamma can be
/// studied; [`BandNetwork::new`] rejects `slow_band >= fast_band`.
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
    /// - `band_sizes` is empty ([`BandError::NoBands`]) or any entry is zero
    ///   ([`BandError::EmptyBand`]),
    /// - `band_params` length does not match `band_sizes`,
    /// - a band's [`CouplingMode`] is invalid for that band's oscillator count,
    /// - a PAC pair references an out-of-range band or is not strictly
    ///   slow→fast.
    pub fn new(
        band_sizes: Vec<usize>,
        band_params: Vec<BandParams>,
        pac_pairs: Vec<PacPair>,
    ) -> Result<Self, BandError> {
        let n_bands = band_sizes.len();
        if n_bands == 0 {
            return Err(BandError::NoBands);
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
            // Reject an unusable coupling mode (e.g. sparse k ≥ band size) at
            // construction time rather than at the first derivative evaluation.
            band_params[i].model(sz)?;
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

    /// Compute the intra-band Kuramoto derivatives for one band.
    ///
    /// The band's oscillators are lifted into a standalone [`OscillatorState`]
    /// and handed to a [`KuramotoOscillator`] configured from the band's
    /// [`BandParams`], so the band dynamics are the crate's single Kuramoto
    /// implementation evaluated on `N_b` oscillators — not a second copy of it.
    fn compute_band_derivatives(
        &self,
        state: &OscillatorState,
        band_indices: &[usize],
        band_idx: usize,
    ) -> Result<StateDerivatives, StateError> {
        let params = &self.band_params[band_idx];
        let sub = band_sub_state(state, band_indices);
        params.model(band_indices.len())?.compute_derivatives(&sub)
    }
}

/// Lift a band's oscillators into a standalone [`OscillatorState`].
///
/// Built by direct field construction rather than [`OscillatorState::new`] so
/// the band model sees exactly the values the caller supplied: integrator stage
/// states deliberately carry unwrapped phases (see `make_intermediate_state` in
/// [`crate::integrate`]), and re-wrapping here would change the phase sort order
/// that `CouplingMode::SparseKnn` uses to pick neighbours.
fn band_sub_state(state: &OscillatorState, band_indices: &[usize]) -> OscillatorState {
    OscillatorState {
        phase: band_indices.iter().map(|&j| state.phase[j]).collect(),
        amplitude: band_indices.iter().map(|&j| state.amplitude[j]).collect(),
        frequency: band_indices.iter().map(|&j| state.frequency[j]).collect(),
        freq_band: None,
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
        let mut dfrequency = vec![0.0; n];

        // 1. Intra-band Kuramoto derivatives (per-band CouplingMode)
        for (b, band_idx) in indices.iter().enumerate() {
            let d = self.compute_band_derivatives(state, band_idx, b)?;
            for (k, &j) in band_idx.iter().enumerate() {
                dphase[j] = d.dphase[k];
                damplitude[j] = d.damplitude[k];
                dfrequency[j] = d.dfrequency[k];
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
            dfrequency[i] = clamp_derivative(dfrequency[i]);
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
    fn no_bands_rejected_with_dedicated_variant() {
        // WP013-F5: an empty band *list* is not "band 0 has zero oscillators".
        let err = BandNetwork::new(vec![], vec![], vec![]).unwrap_err();
        assert!(matches!(err, BandError::NoBands));
        assert_eq!(
            err.to_string(),
            "band network requires at least one band, got an empty band list"
        );
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
    fn non_adjacent_pac_pair_accepted() {
        // WP013-F5: adjacency is the standard hierarchy, not a constraint.
        // A delta→gamma (0→2) pair skipping theta is a valid configuration.
        let net = BandNetwork::new(
            vec![2, 4, 8],
            vec![
                BandParams::new(0.8, 0.1).unwrap(),
                BandParams::new(1.0, 0.1).unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![PacPair::new(0, 2, PhaseAmplitudeCoupling::new(0.3).unwrap(), 0.0).unwrap()],
        )
        .unwrap();
        assert_eq!(net.pac_pairs().len(), 1);
        assert_eq!(net.pac_pairs()[0].slow_band, 0);
        assert_eq!(net.pac_pairs()[0].fast_band, 2);

        let mut seed = crate::seed::Seed::new(7, 0);
        let state =
            create_band_state(&net, &[(1.0, 3.0), (5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
        let deriv = net.compute_derivatives(&state).unwrap();
        for i in 0..14 {
            assert!(deriv.damplitude[i].is_finite());
        }
    }

    #[test]
    fn non_finite_band_params_rejected() {
        assert!(BandParams::new(f64::NAN, 0.1).is_err());
        assert!(BandParams::new(1.0, f64::INFINITY).is_err());
        assert!(
            BandParams::with_coupling(1.0, 0.1, f64::NAN, CouplingMode::MeanField).is_err(),
            "non-finite freq_adaptation_rate must be rejected"
        );
    }

    // --- Coupling-mode dispatch (WP013-F2) ---

    #[test]
    fn band_params_defaults_to_mean_field_without_frequency_adaptation() {
        let p = BandParams::new(1.0, 0.1).unwrap();
        assert_eq!(p.coupling_mode, CouplingMode::MeanField);
        assert_relative_eq!(p.freq_adaptation_rate, 0.0, epsilon = 1e-15);
    }

    #[test]
    fn band_derivatives_match_standalone_kuramoto_per_mode() {
        // The band model is the crate's Kuramoto implementation restricted to
        // the band's oscillators: with PAC depth 0 the composed derivatives
        // must equal a standalone KuramotoOscillator on each band sub-state.
        for mode in [
            CouplingMode::MeanField,
            CouplingMode::Full { matrix: None },
            CouplingMode::SparseKnn { k: Some(2) },
        ] {
            let theta = BandParams::with_coupling(2.0, 0.1, 0.01, mode.clone()).unwrap();
            let gamma = BandParams::with_coupling(2.0, 0.1, 0.01, mode.clone()).unwrap();
            let net = theta_gamma_network(
                4,
                8,
                theta.clone(),
                gamma.clone(),
                PhaseAmplitudeCoupling::new(0.0).unwrap(),
                0.0,
            )
            .unwrap();

            let mut seed = crate::seed::Seed::new(2024, 0);
            let state = create_band_state(&net, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
            let composed = net.compute_derivatives(&state).unwrap();

            for (band, params) in [(0usize, &theta), (1usize, &gamma)] {
                let indices: Vec<usize> = (0..state.n_oscillators())
                    .filter(|&i| state.freq_band.as_ref().unwrap()[i] as usize == band)
                    .collect();
                let sub = band_sub_state(&state, &indices);
                let model = KuramotoOscillator::new(
                    indices.len(),
                    params.coupling_strength,
                    params.decay_rate,
                    params.freq_adaptation_rate,
                    params.coupling_mode.clone(),
                )
                .unwrap();
                let expected = model.compute_derivatives(&sub).unwrap();
                for (k, &j) in indices.iter().enumerate() {
                    assert_relative_eq!(composed.dphase[j], expected.dphase[k], epsilon = 1e-14);
                    assert_relative_eq!(
                        composed.damplitude[j],
                        expected.damplitude[k],
                        epsilon = 1e-14
                    );
                    assert_relative_eq!(
                        composed.dfrequency[j],
                        expected.dfrequency[k],
                        epsilon = 1e-14
                    );
                }
            }
        }
    }

    #[test]
    fn coupling_modes_produce_different_dynamics() {
        // A regression guard that the mode is actually dispatched, not ignored.
        let build = |mode: CouplingMode| {
            theta_gamma_network(
                4,
                8,
                BandParams::with_coupling(2.0, 0.1, 0.0, mode.clone()).unwrap(),
                BandParams::with_coupling(2.0, 0.1, 0.0, mode).unwrap(),
                PhaseAmplitudeCoupling::new(0.3).unwrap(),
                0.0,
            )
            .unwrap()
        };
        let mean_field = build(CouplingMode::MeanField);
        let sparse = build(CouplingMode::SparseKnn { k: Some(2) });

        let mut seed = crate::seed::Seed::new(31, 0);
        let state = create_band_state(&mean_field, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
        let d_mf = mean_field.compute_derivatives(&state).unwrap();
        let d_sk = sparse.compute_derivatives(&state).unwrap();

        let max_diff = d_mf
            .dphase
            .iter()
            .zip(d_sk.dphase.iter())
            .map(|(a, b)| (a - b).abs())
            .fold(0.0_f64, f64::max);
        assert!(
            max_diff > 1e-6,
            "mean-field and sparse k-NN gave identical derivatives (max diff {max_diff})"
        );
    }

    #[test]
    fn frequency_adaptation_propagates_to_dfrequency() {
        let net = theta_gamma_network(
            4,
            8,
            BandParams::with_coupling(2.0, 0.1, 0.05, CouplingMode::MeanField).unwrap(),
            BandParams::with_coupling(2.0, 0.1, 0.05, CouplingMode::MeanField).unwrap(),
            PhaseAmplitudeCoupling::new(0.3).unwrap(),
            0.0,
        )
        .unwrap();
        let mut seed = crate::seed::Seed::new(11, 0);
        let state = create_band_state(&net, &[(5.0, 7.0), (35.0, 45.0)], &mut seed).unwrap();
        let deriv = net.compute_derivatives(&state).unwrap();
        assert!(
            deriv.dfrequency.iter().any(|d| d.abs() > 1e-12),
            "γ > 0 must produce non-zero dfrequency"
        );

        // γ = 0 (the BandParams::new default) keeps frequencies frozen.
        let frozen = make_tg_network();
        let d0 = frozen.compute_derivatives(&state).unwrap();
        for d in &d0.dfrequency {
            assert_relative_eq!(*d, 0.0, epsilon = 1e-15);
        }
    }

    #[test]
    fn invalid_sparse_k_rejected_at_construction() {
        // k must be < band size; band 0 has 4 oscillators.
        let err = BandNetwork::new(
            vec![4, 8],
            vec![
                BandParams::with_coupling(1.0, 0.1, 0.0, CouplingMode::SparseKnn { k: Some(9) })
                    .unwrap(),
                BandParams::new(0.5, 0.1).unwrap(),
            ],
            vec![],
        )
        .unwrap_err();
        assert!(matches!(err, BandError::State(_)), "got {err:?}");
    }

    #[test]
    fn single_oscillator_band_has_no_self_coupling() {
        // Delegating to KuramotoOscillator adopts its N ≤ 1 contract:
        // dφ = ω, dr = −λr, dω = 0 (an isolated oscillator does not couple
        // to itself through the order parameter).
        let net = theta_gamma_network(
            1,
            1,
            BandParams::new(2.0, 0.25).unwrap(),
            BandParams::new(2.0, 0.25).unwrap(),
            PhaseAmplitudeCoupling::new(0.0).unwrap(),
            0.0,
        )
        .unwrap();
        let state = OscillatorState::new(
            vec![0.3, 1.7],
            vec![1.5, 2.5],
            vec![6.0, 40.0],
            Some(vec![0, 1]),
        )
        .unwrap();
        let d = net.compute_derivatives(&state).unwrap();
        assert_relative_eq!(d.dphase[0], 6.0, epsilon = 1e-12);
        assert_relative_eq!(d.dphase[1], 40.0, epsilon = 1e-12);
        assert_relative_eq!(d.damplitude[0], -0.25 * 1.5, epsilon = 1e-12);
        assert_relative_eq!(d.damplitude[1], -0.25 * 2.5, epsilon = 1e-12);
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
    fn capacity_zero_for_non_positive_slow_frequency() {
        let net = make_tg_network();
        let state = OscillatorState::new(
            vec![0.0; 12],
            vec![1.0; 12],
            {
                let mut f = vec![0.0; 4]; // slow band mean frequency = 0
                f.extend(vec![40.0; 8]);
                f
            },
            Some(vec![0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
        )
        .unwrap();
        assert_eq!(net.theoretical_capacity(&state).unwrap(), 0);
    }

    #[test]
    fn mean_frequency_of_empty_index_set_is_zero() {
        let net = make_tg_network();
        let state = make_tg_state(&net);
        assert_relative_eq!(mean_frequency(&state, &[]), 0.0, epsilon = 1e-15);
    }

    #[test]
    fn accessors_expose_configuration() {
        let net = make_dtg_network();
        assert_eq!(net.band_params().len(), 3);
        assert_relative_eq!(net.band_params()[0].coupling_strength, 0.8, epsilon = 1e-12);
        assert_relative_eq!(net.band_params()[2].decay_rate, 0.1, epsilon = 1e-12);
        assert_eq!(net.pac_pairs().len(), 2);
        assert_eq!(net.pac_pairs()[0].slow_band, 0);
        assert_eq!(net.pac_pairs()[1].fast_band, 2);
        assert_eq!(net.band_sizes(), &[2, 4, 8]);
    }

    // --- Integration (requires freq_band on every stage state) ---

    #[test]
    fn band_network_integrates_with_rk4() {
        use crate::integrate::{integrate_fixed, RK4Integrator};

        let net = make_tg_network();
        let state = make_tg_state(&net);
        let mut rk4 = RK4Integrator::new();
        let (result, _) = integrate_fixed(&mut rk4, &net, &state, 5, 0.01, false).unwrap();
        assert_eq!(result.n_oscillators(), 12);
        assert_eq!(result.freq_band, state.freq_band);
        for i in 0..12 {
            assert!(result.phase[i].is_finite());
            assert!(result.amplitude[i].is_finite());
        }
    }

    #[test]
    fn band_network_integrates_with_multi_rate() {
        use crate::integrate::MultiRateIntegrator;

        let net = make_tg_network();
        let state = make_tg_state(&net);
        // sub_steps mirrors the PRINet reference's floor(f_fast / f_slow).
        let sub_steps = net.theoretical_capacity(&state).unwrap().max(1);
        let mut integrator = MultiRateIntegrator::new(sub_steps).unwrap();
        let result = {
            use crate::integrate::Integrator;
            integrator.step(&net, &state, 0.01).unwrap()
        };
        assert_eq!(result.freq_band, state.freq_band);
        for i in 0..12 {
            assert!(result.phase[i].is_finite());
        }
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

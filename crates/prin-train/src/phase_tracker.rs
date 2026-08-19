//! Phase-based multi-object tracker: PRIN's primary contribution.
//!
//! [`PhaseTracker`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.hybrid.PhaseTracker`: detections are encoded into phase/amplitude
//! oscillator states, evolved through [`crate::bands::DiscreteDeltaThetaGamma`]
//! dynamics, and matched across frames by phase-coherence similarity.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! ```text
//! (phase, amp) = encode(detections)         // MLP: Linear→ReLU→Linear(→Softplus for amp)
//! phase'       = evolve(phase, amp)          // DiscreteDeltaThetaGamma.integrate
//! sim(a, b)    = mean_k cos(phase_a[k] − phase_b[k])   // phase_similarity
//! matches      = greedy_assign(sim, threshold)          // descending-similarity greedy match
//! ```
//!
//! This is a line-for-line port of `PhaseTracker.encode`/`.evolve`/
//! `.phase_similarity`/`.forward`/`.track_sequence` (`nn/hybrid.py`).
//!
//! **Documented reformulation — `phase_similarity`.** The PRINet 3.0
//! reference computes this via `torch.complex64` (`exp(iφ)`, L2-normalized,
//! real part of the inner product). Burn has no complex-tensor autodiff (the
//! same constraint [`crate::energy`]/[`crate::hep`] document), so this port
//! computes the mathematically identical real-valued reduction directly:
//! since every `|exp(iφ_k)| = 1`, the L2 norm of each `n_osc`-length complex
//! vector is exactly `√n_osc`, so `Re(z_a_norm · z̄_b_norm) = (Σ_k
//! cos(φ_a[k] − φ_b[k])) / (√n_osc + ε)²` — computed here on the real cosine
//! sum directly, preserving the reference's exact `ε`-regularized
//! normalization (not simplified to `1/n_osc`) so golden-value parity holds
//! to the same tolerance as a complex-tensor implementation would achieve.
//!
//! The detection encoder MLP (`Linear`→`ReLU`→`Linear`, optionally
//! `Softplus`) uses [`burn::nn::Linear`] with weights seeded via
//! `crate::support::seeded_linear` — see that function's docs for why
//! [`burn::nn::LinearConfig::init`] is not used.
//!
//! Greedy frame-to-frame matching (`forward`, `track_sequence`) is
//! non-differentiable host-side bookkeeping (identical in kind to PRINet
//! 3.0's `.item()`-per-element Python loop): `crate::support::greedy_match_by_similarity`.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::phase_tracker::PhaseTrackerConfig;
//!
//! type Backend = NdArray<f32>;
//!
//! let cfg = PhaseTrackerConfig::new(4).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let tracker = cfg.init::<Backend>(&device, &mut seed);
//!
//! let dets_t = Tensor::<Backend, 2>::ones([3, 4], &device);
//! let dets_t1 = Tensor::<Backend, 2>::ones([3, 4], &device);
//! let (matches, sim) = tracker.forward(dets_t, dets_t1).unwrap();
//! assert_eq!(matches.len(), 3);
//! assert_eq!(sim.dims(), [3, 3]);
//! ```

use burn::module::Module;
use burn::nn::Linear;
use burn::tensor::activation::{relu, softplus};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::bands::{DiscreteBandState, DiscreteDeltaThetaGamma, DiscreteDeltaThetaGammaConfig};
use crate::error::TrainError;
use crate::support::{
    check_dims, greedy_match_by_similarity, phase_coherence_similarity, seeded_linear, to_f64_vec,
};

pub(crate) const DET_HIDDEN: usize = 64;
/// Matches PRINet 3.0's `_EPS` used in `phase_similarity`'s normalization.
pub(crate) const PHASE_SIM_EPS: f64 = 1e-6;

/// The result of [`PhaseTracker::track_sequence`]: per-frame phase history
/// and identity-preservation statistics across a detection sequence.
///
/// Mirrors PRINet 3.0's `track_sequence` return dict.
#[derive(Debug, Clone)]
pub struct TrackingResult<B: Backend> {
    /// Per-frame phase tensors, one per input frame, each `[N_det, n_osc]`.
    pub phase_history: Vec<Tensor<B, 2>>,
    /// Per-transition match indices (frame `t` → frame `t+1`), `-1` if
    /// unmatched. Length `T - 1`.
    pub identity_matches: Vec<Vec<i64>>,
    /// Fraction of matchable detections successfully matched across the
    /// whole sequence, in `[0, 1]`.
    pub identity_preservation: f64,
    /// Per-transition mean best-match similarity.
    pub per_frame_similarity: Vec<f64>,
    /// Per-transition mean circular phase correlation `ρ ∈ [0, 1]` (empty
    /// entries recorded as `0.0` when no detections matched that
    /// transition).
    pub per_frame_phase_correlation: Vec<f64>,
}

/// Validated hyperparameters for [`PhaseTracker`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `n_delta=4, n_theta=8,
/// n_gamma=16, n_discrete_steps=5, match_threshold=0.3`.
#[derive(Clone, Debug, PartialEq)]
pub struct PhaseTrackerConfig {
    /// Per-detection input feature dimension.
    pub detection_dim: usize,
    /// Delta-band oscillators.
    pub n_delta: usize,
    /// Theta-band oscillators.
    pub n_theta: usize,
    /// Gamma-band oscillators.
    pub n_gamma: usize,
    /// Dynamics steps per frame.
    pub n_discrete_steps: usize,
    /// Minimum phase similarity for a valid match.
    pub match_threshold: f64,
}

impl PhaseTrackerConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(detection_dim: usize) -> Result<Self, TrainError> {
        Self::with_params(detection_dim, 4, 8, 16, 5, 0.3)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `detection_dim` or any band size
    /// is zero, [`TrainError::InvalidStepCount`] if `n_discrete_steps` is
    /// zero, or [`TrainError::InvalidMatchThreshold`] if `match_threshold` is
    /// non-finite.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        detection_dim: usize,
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_discrete_steps: usize,
        match_threshold: f64,
    ) -> Result<Self, TrainError> {
        if detection_dim == 0 {
            return Err(TrainError::EmptyBand {
                name: "detection_dim",
            });
        }
        // Reuses DiscreteDeltaThetaGammaConfig's own band-size validation.
        let _ = DiscreteDeltaThetaGammaConfig::new(n_delta, n_theta, n_gamma)?;
        if n_discrete_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_discrete_steps",
                value: n_discrete_steps,
            });
        }
        if !match_threshold.is_finite() {
            return Err(TrainError::InvalidMatchThreshold {
                value: match_threshold,
            });
        }
        Ok(Self {
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
        })
    }

    /// Total oscillator count across all three bands.
    pub fn n_osc(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Initialize a [`PhaseTracker`] with parameters drawn from the
    /// project's deterministic [`Seed`] (Coding Standards §1.3).
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> PhaseTracker<B> {
        let n_osc = self.n_osc();
        let det_to_phase = [
            seeded_linear::<B>(self.detection_dim, DET_HIDDEN, true, device, seed),
            seeded_linear::<B>(DET_HIDDEN, n_osc, true, device, seed),
        ];
        let det_to_amp = [
            seeded_linear::<B>(self.detection_dim, DET_HIDDEN, true, device, seed),
            seeded_linear::<B>(DET_HIDDEN, n_osc, true, device, seed),
        ];
        let dynamics = DiscreteDeltaThetaGammaConfig::new(self.n_delta, self.n_theta, self.n_gamma)
            .expect("band sizes already validated by PhaseTrackerConfig::with_params")
            .init::<B>(device, seed);

        PhaseTracker {
            det_to_phase,
            det_to_amp,
            dynamics,
            n_osc,
            n_discrete_steps: self.n_discrete_steps,
            match_threshold: self.match_threshold,
        }
    }
}

/// Phase-based multi-object tracker (PRIN's primary contribution).
///
/// See the module docs for the exact formula. Construct via
/// [`PhaseTrackerConfig::init`].
#[derive(Module, Debug)]
pub struct PhaseTracker<B: Backend> {
    det_to_phase: [Linear<B>; 2],
    det_to_amp: [Linear<B>; 2],
    dynamics: DiscreteDeltaThetaGamma<B>,
    n_osc: usize,
    n_discrete_steps: usize,
    match_threshold: f64,
}

impl<B: Backend> PhaseTracker<B> {
    /// Total oscillator count across all three bands.
    pub fn n_osc(&self) -> usize {
        self.n_osc
    }

    /// Minimum phase similarity for a valid match.
    pub fn match_threshold(&self) -> f64 {
        self.match_threshold
    }

    /// The dynamics module's own trainable [`DiscreteDeltaThetaGamma`],
    /// exposed so ablation variants ([`crate::ablation::PhaseTrackerFrozen`])
    /// can build a frozen-dynamics copy via [`Self::with_dynamics`].
    pub fn dynamics(&self) -> &DiscreteDeltaThetaGamma<B> {
        &self.dynamics
    }

    /// Rebuild this tracker with a replacement dynamics module (e.g. after
    /// [`burn::module::Module::no_grad`]), keeping the detection encoder
    /// unchanged. Used by [`crate::ablation::PhaseTrackerFrozen`].
    pub fn with_dynamics(mut self, dynamics: DiscreteDeltaThetaGamma<B>) -> Self {
        self.dynamics = dynamics;
        self
    }

    /// Encode detections into `(phase, amplitude)` oscillator embeddings.
    ///
    /// `detections` has shape `[N, detection_dim]`; returns two tensors each
    /// `[N, n_osc]`.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `detections`'s width does
    /// not match the configured `detection_dim`.
    pub fn encode(
        &self,
        detections: Tensor<B, 2>,
    ) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let d_in = self.det_to_phase[0].weight.val().dims()[0];
        check_dims("detections", [detections.dims()[1]], [d_in])?;

        let phase_raw =
            self.det_to_phase[1].forward(relu(self.det_to_phase[0].forward(detections.clone())));
        let phase = phase_raw.remainder_scalar(std::f64::consts::TAU);
        let amp_raw = self.det_to_amp[1].forward(relu(self.det_to_amp[0].forward(detections)));
        let amp = softplus(amp_raw, 1.0);
        Ok((phase, amp))
    }

    /// Evolve a `(phase, amplitude)` state through `n_discrete_steps`
    /// of dynamics.
    ///
    /// # Errors
    ///
    /// See [`DiscreteDeltaThetaGamma::integrate`].
    pub fn evolve(
        &self,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let state = DiscreteBandState::new(phase, amplitude)?;
        let evolved = self
            .dynamics
            .integrate(state, self.n_discrete_steps, 0.01)?;
        Ok(evolved.into_parts())
    }

    /// Phase-coherence similarity matrix: `sim[a, b] = mean_k
    /// cos(phase_a[a,k] − phase_b[b,k])`, exactly matching PRINet 3.0's
    /// ε-regularized complex-cosine-similarity formula (see module docs).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `phase_a` and `phase_b` do
    /// not share the same oscillator width.
    pub fn phase_similarity(
        &self,
        phase_a: Tensor<B, 2>,
        phase_b: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let n = phase_a.dims()[1];
        check_dims("phase_b", [phase_b.dims()[1]], [n])?;
        Ok(phase_coherence_similarity(
            phase_a,
            phase_b,
            n,
            PHASE_SIM_EPS,
        ))
    }

    /// Match detections across two consecutive frames.
    ///
    /// Returns `(matches, similarity)`: `matches[i]` is the index in
    /// `detections_t1` matched to detection `i` in `detections_t`, or `-1`
    /// if unmatched; `similarity` is the full `[N_t, N_t1]` matrix.
    ///
    /// # Errors
    ///
    /// See [`Self::encode`], [`Self::evolve`], [`Self::phase_similarity`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        let (phase_t, amp_t) = self.encode(detections_t)?;
        let (phase_t1, _amp_t1) = self.encode(detections_t1)?;
        let (phase_t_evolved, _) = self.evolve(phase_t, amp_t)?;
        let sim = self.phase_similarity(phase_t_evolved, phase_t1)?;
        let matches = greedy_match_by_similarity(&sim, self.match_threshold);
        Ok((matches, sim))
    }

    /// Track objects across a sequence of frames.
    ///
    /// Processes each consecutive pair of frames and accumulates
    /// identity-preservation statistics — see [`TrackingResult`].
    ///
    /// # Errors
    ///
    /// See [`Self::encode`], [`Self::evolve`], [`Self::phase_similarity`].
    pub fn track_sequence(
        &self,
        frame_detections: Vec<Tensor<B, 2>>,
    ) -> Result<TrackingResult<B>, TrainError> {
        let mut phase_history = Vec::with_capacity(frame_detections.len());
        let mut identity_matches = Vec::new();
        let mut per_frame_sim = Vec::new();
        let mut per_frame_rho = Vec::new();
        let mut total_matches: usize = 0;
        let mut total_possible: usize = 0;

        for (t, dets) in frame_detections.into_iter().enumerate() {
            let (phase_t, _amp_t) = self.encode(dets)?;

            if t == 0 {
                phase_history.push(phase_t);
                continue;
            }

            let prev_phase = phase_history
                .last()
                .expect("t > 0 implies a prior frame")
                .clone();
            let prev_amp = Tensor::ones_like(&prev_phase);
            let (evolved_phase, _) = self.evolve(prev_phase, prev_amp)?;

            let sim = self.phase_similarity(evolved_phase.clone(), phase_t.clone())?;
            let n_prev = evolved_phase.dims()[0];
            let n_curr = phase_t.dims()[0];
            let n_match = n_prev.min(n_curr);

            let matches = greedy_match_by_similarity(&sim, self.match_threshold);
            let n_matched = matches.iter().filter(|&&m| m >= 0).count();
            total_matches += n_matched;
            total_possible += n_match;

            let mean_sim = if n_prev == 0 {
                0.0
            } else {
                let (max_sims, _) = sim.clone().max_dim_with_indices(1);
                to_f64_vec(max_sims.squeeze::<1>(1)).iter().sum::<f64>() / n_prev as f64
            };
            per_frame_sim.push(mean_sim);

            let rho = if n_matched > 0 {
                let matched_prev_idx: Vec<usize> = matches
                    .iter()
                    .enumerate()
                    .filter(|(_, &m)| m >= 0)
                    .map(|(i, _)| i)
                    .collect();
                let matched_curr_idx: Vec<usize> = matches
                    .iter()
                    .filter(|&&m| m >= 0)
                    .map(|&m| m as usize)
                    .collect();

                let prev_phase_vals = to_f64_vec(evolved_phase.clone());
                let curr_phase_vals = to_f64_vec(phase_t.clone());
                let n_osc = self.n_osc;

                let mut rho_sum = 0.0;
                for (row_i, &pi) in matched_prev_idx.iter().enumerate() {
                    let ci = matched_curr_idx[row_i];
                    let mut re = 0.0;
                    let mut im = 0.0;
                    for k in 0..n_osc {
                        let diff =
                            curr_phase_vals[ci * n_osc + k] - prev_phase_vals[pi * n_osc + k];
                        re += diff.cos();
                        im += diff.sin();
                    }
                    re /= n_osc as f64;
                    im /= n_osc as f64;
                    rho_sum += (re * re + im * im).sqrt();
                }
                rho_sum / matched_prev_idx.len() as f64
            } else {
                0.0
            };
            per_frame_rho.push(rho);

            identity_matches.push(matches);
            phase_history.push(phase_t);
        }

        let identity_preservation = total_matches as f64 / total_possible.max(1) as f64;

        Ok(TrackingResult {
            phase_history,
            identity_matches,
            identity_preservation,
            per_frame_similarity: per_frame_sim,
            per_frame_phase_correlation: per_frame_rho,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn small_config() -> PhaseTrackerConfig {
        PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.3).unwrap()
    }

    fn seeded_tracker<B: Backend>(device: &B::Device) -> PhaseTracker<B> {
        let mut seed = Seed::new(11, 0);
        small_config().init(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn zero_detection_dim_rejected() {
        assert!(matches!(
            PhaseTrackerConfig::new(0).unwrap_err(),
            TrainError::EmptyBand {
                name: "detection_dim"
            }
        ));
    }

    #[test]
    fn zero_band_size_rejected() {
        assert!(matches!(
            PhaseTrackerConfig::with_params(4, 0, 3, 4, 2, 0.3).unwrap_err(),
            TrainError::EmptyBand { name: "delta" }
        ));
    }

    #[test]
    fn zero_discrete_steps_rejected() {
        assert!(matches!(
            PhaseTrackerConfig::with_params(4, 2, 3, 4, 0, 0.3).unwrap_err(),
            TrainError::InvalidStepCount { .. }
        ));
    }

    #[test]
    fn non_finite_threshold_rejected() {
        assert!(matches!(
            PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, f64::NAN).unwrap_err(),
            TrainError::InvalidMatchThreshold { .. }
        ));
    }

    // --- Construction ---

    #[test]
    fn seeded_init_produces_expected_sizes() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        assert_eq!(tracker.n_osc(), 9);
        assert!((tracker.match_threshold() - 0.3).abs() < 1e-15);
    }

    #[test]
    fn same_seed_gives_identical_parameters() {
        let mut s1 = Seed::new(5, 0);
        let mut s2 = Seed::new(5, 0);
        let t1 = small_config().init::<TestBackend>(&device(), &mut s1);
        let t2 = small_config().init::<TestBackend>(&device(), &mut s2);
        let w1 = t1.det_to_phase[0]
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let w2 = t2.det_to_phase[0]
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(w1, w2);
    }

    // --- encode / evolve / phase_similarity ---

    #[test]
    fn encode_returns_expected_shapes_wrapped_phase_and_positive_amplitude() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let dets = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.1, -0.2, 0.3, 0.4, 1.0, 2.0, -1.0, 0.5], vec![2, 4]),
            &dev,
        );
        let (phase, amp) = tracker.encode(dets).unwrap();
        assert_eq!(phase.dims(), [2, 9]);
        assert_eq!(amp.dims(), [2, 9]);
        let p = phase.to_data().to_vec::<f64>().unwrap();
        let a = amp.to_data().to_vec::<f64>().unwrap();
        for v in p {
            assert!((0.0..std::f64::consts::TAU).contains(&v));
        }
        for v in a {
            assert!(v > 0.0 && v.is_finite());
        }
    }

    #[test]
    fn encode_rejects_wrong_detection_dim() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let dets = Tensor::<TestBackend, 2>::ones([2, 3], &dev);
        let err = tracker.encode(dets).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "detections",
                ..
            }
        ));
    }

    #[test]
    fn phase_similarity_identical_phases_gives_similarity_one() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.1; 9 * 2], vec![2, 9]),
            &dev,
        );
        let sim = tracker.phase_similarity(phase.clone(), phase).unwrap();
        let data = sim.to_data().to_vec::<f64>().unwrap();
        for (i, v) in data.iter().enumerate() {
            let row = i / 2;
            let col = i % 2;
            if row == col {
                assert!((v - 1.0).abs() < 1e-6, "diagonal similarity {v} not ~1.0");
            }
        }
    }

    #[test]
    fn phase_similarity_opposite_phases_gives_similarity_near_negative_one() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let phase_a = Tensor::<TestBackend, 2>::zeros([1, 9], &dev);
        let phase_b = Tensor::<TestBackend, 2>::full([1, 9], std::f64::consts::PI, &dev);
        let sim = tracker.phase_similarity(phase_a, phase_b).unwrap();
        let v = sim.to_data().to_vec::<f64>().unwrap()[0];
        assert!((v - (-1.0)).abs() < 1e-6, "similarity {v} not ~-1.0");
    }

    #[test]
    fn phase_similarity_rejects_mismatched_oscillator_width() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let a = Tensor::<TestBackend, 2>::zeros([1, 9], &dev);
        let b = Tensor::<TestBackend, 2>::zeros([1, 5], &dev);
        let err = tracker.phase_similarity(a, b).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "phase_b",
                ..
            }
        ));
    }

    // --- forward / track_sequence ---

    #[test]
    fn forward_matches_within_bounds_and_similarity_shape() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let mut seed = Seed::new(1, 1);
        let dets_t =
            crate::support::seeded_uniform::<TestBackend, 2>([3, 4], -1.0, 1.0, &dev, &mut seed);
        let dets_t1 =
            crate::support::seeded_uniform::<TestBackend, 2>([3, 4], -1.0, 1.0, &dev, &mut seed);
        let (matches, sim) = tracker.forward(dets_t, dets_t1).unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);
        for m in matches {
            assert!(m == -1 || (0..3).contains(&m));
        }
    }

    #[test]
    fn track_sequence_preservation_in_unit_interval_and_history_length_matches() {
        let tracker = seeded_tracker::<TestBackend>(&device());
        let dev = device();
        let mut seed = Seed::new(2, 2);
        let frames: Vec<_> = (0..4)
            .map(|_| {
                crate::support::seeded_uniform::<TestBackend, 2>([3, 4], -1.0, 1.0, &dev, &mut seed)
            })
            .collect();
        let result = tracker.track_sequence(frames).unwrap();
        assert_eq!(result.phase_history.len(), 4);
        assert_eq!(result.identity_matches.len(), 3);
        assert_eq!(result.per_frame_similarity.len(), 3);
        assert_eq!(result.per_frame_phase_correlation.len(), 3);
        assert!((0.0..=1.0).contains(&result.identity_preservation));
        for rho in &result.per_frame_phase_correlation {
            assert!((0.0..=1.0 + 1e-9).contains(rho));
        }
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_encoder_and_dynamics_parameters() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let tracker = small_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let dets = Tensor::<TestAutodiffBackend, 2>::ones([2, 4], &dev).require_grad();

        let (phase, amp) = tracker.encode(dets).unwrap();
        let (evolved_phase, evolved_amp) = tracker.evolve(phase, amp).unwrap();
        let loss = evolved_phase.sum() + evolved_amp.sum();
        let grads = loss.backward();

        for grad in [
            tracker.det_to_phase[0]
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            tracker.det_to_amp[0]
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    // --- Serialization ---

    #[test]
    fn record_roundtrip_preserves_parameters() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let tracker = seeded_tracker::<TestBackend>(&dev);
        let before = tracker.det_to_phase[0]
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<TestBackend>::record(&recorder, tracker.clone().into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let restored = tracker.load_record(record);

        let after = restored.det_to_phase[0]
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(before, after);
        assert_eq!(restored.n_osc(), 9);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use burn::backend::NdArray;
    use proptest::prelude::*;

    type TestBackend = NdArray<f64>;

    proptest! {
        #[test]
        fn phase_similarity_always_in_range(
            nd in 1usize..=3,
            nt in 1usize..=3,
            ng in 1usize..=3,
            n_a in 1usize..=4,
            n_b in 1usize..=4,
            seed_val in 0u64..1000,
        ) {
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let tracker = PhaseTrackerConfig::with_params(3, nd, nt, ng, 1, 0.3)
                .unwrap()
                .init::<TestBackend>(&dev, &mut seed);
            let n_total = tracker.n_osc();

            let mut pseed = Seed::new(seed_val as u128, 1);
            let phase_a = crate::support::seeded_uniform::<TestBackend, 2>([n_a, n_total], 0.0, std::f64::consts::TAU, &dev, &mut pseed);
            let phase_b = crate::support::seeded_uniform::<TestBackend, 2>([n_b, n_total], 0.0, std::f64::consts::TAU, &dev, &mut pseed);

            let sim = tracker.phase_similarity(phase_a, phase_b).unwrap();
            let data = sim.to_data().to_vec::<f64>().unwrap();
            for v in &data {
                prop_assert!(v.is_finite());
                prop_assert!(*v >= -1.0 - 1e-9 && *v <= 1.0 + 1e-9);
            }
        }
    }
}

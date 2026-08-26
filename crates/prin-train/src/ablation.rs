//! Structural ablation variants isolating which components drive temporal
//! binding, for the Q1.7-class temporal-advantage benchmarks.
//!
//! Burn `Module` rebuild of PRINet 3.0's `nn.ablation_variants`:
//!
//! - [`PhaseTrackerFrozen`] (PT-frozen) — [`crate::phase_tracker::PhaseTracker`]
//!   with its [`crate::bands::DiscreteDeltaThetaGamma`] dynamics frozen
//!   (`requires_grad=False`); the detection encoder stays trainable.
//! - [`PhaseTrackerStatic`] (PT-static) — no coupling: independent
//!   fixed-frequency phase advance, no Kuramoto interaction.
//! - [`SlotAttentionNoGRU`] (SA-no-GRU) — [`crate::slot_attention::TemporalSlotAttentionMOT`]
//!   without temporal GRU carry-over: slots re-initialize from scratch every
//!   frame.
//! - [`SlotAttentionFrozen`] (SA-frozen) — `TemporalSlotAttentionMOT` with
//!   every parameter frozen (the untrained baseline paired with PT-frozen).
//!
//! **Not ported — `create_ablation_tracker` factory.** PRINet 3.0's
//! `create_ablation_tracker(variant: str, ...)` returns one of six
//! structurally different `nn.Module` subclasses behind Python's duck
//! typing. Rust's static type system has no direct equivalent (the six
//! variants' `forward`/`track_sequence` signatures genuinely differ — e.g.
//! [`crate::phase_tracker::PhaseTracker::forward`] takes no [`Seed`],
//! [`crate::slot_attention::SlotAttentionModule::forward`] must); a
//! string-keyed factory would need to erase these differences behind a
//! trait object with no caller in this WP's scope. Callers construct the
//! specific variant type they want directly (`PhaseTrackerFrozen::new`,
//! etc.) — strictly more precise than the reference's runtime string
//! dispatch, not less capable. Recorded as a deliberate, justified API
//! adaptation, not a silently dropped symbol.

use burn::module::Module;
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::bands::DiscreteDeltaThetaGamma;
use crate::error::TrainError;
use crate::phase_tracker::{PhaseTracker, PhaseTrackerConfig, TrackingResult};
use crate::slot_attention::{
    cosine_similarity, SlotAttentionModule, SlotAttentionModuleConfig, TemporalSlotAttentionMOT,
    TemporalSlotAttentionMOTConfig,
};
use crate::support::{check_dims, greedy_match_by_similarity, seeded_linear, wrap_floor};

// =========================================================================
// PhaseTracker ablation variants
// =========================================================================

/// [`PhaseTracker`] with frozen [`DiscreteDeltaThetaGamma`] coupling weights
/// (PT-frozen): tests whether training the oscillatory dynamics matters, or
/// whether their untrained structure already suffices.
///
/// The detection encoder remains trainable — only `dynamics` is frozen.
#[derive(Module, Debug)]
pub struct PhaseTrackerFrozen<B: Backend> {
    inner: PhaseTracker<B>,
}

impl<B: Backend> PhaseTrackerFrozen<B> {
    /// Construct from a [`PhaseTrackerConfig`], freezing the dynamics
    /// module's gradients immediately after seeded initialization.
    pub fn new(cfg: &PhaseTrackerConfig, device: &B::Device, seed: &mut Seed) -> Self {
        let inner = cfg.init::<B>(device, seed);
        let frozen_dynamics: DiscreteDeltaThetaGamma<B> = inner.dynamics().clone().no_grad();
        Self {
            inner: inner.with_dynamics(frozen_dynamics),
        }
    }

    /// The wrapped tracker (encoder trainable, dynamics frozen).
    pub fn inner(&self) -> &PhaseTracker<B> {
        &self.inner
    }

    /// See [`PhaseTracker::forward`].
    ///
    /// # Errors
    ///
    /// See [`PhaseTracker::forward`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        self.inner.forward(detections_t, detections_t1)
    }

    /// See [`PhaseTracker::track_sequence`].
    ///
    /// # Errors
    ///
    /// See [`PhaseTracker::track_sequence`].
    pub fn track_sequence(
        &self,
        frame_detections: Vec<Tensor<B, 2>>,
    ) -> Result<TrackingResult<B>, TrainError> {
        self.inner.track_sequence(frame_detections)
    }
}

/// [`PhaseTracker`] with no coupling (PT-static): independent fixed-frequency
/// phase advance, no Kuramoto interaction between oscillators. Tests whether
/// coupling matters or independent phase evolution already suffices.
///
/// Shares [`PhaseTracker`]'s detection-encoder architecture (trainable) but
/// fully reimplements `evolve` with a fixed, non-learnable per-band
/// frequency buffer — matching PRINet 3.0's own full reimplementation
/// (`PhaseTrackerStatic` does not wrap `PhaseTracker`).
#[derive(Module, Debug)]
pub struct PhaseTrackerStatic<B: Backend> {
    det_to_phase: [burn::nn::Linear<B>; 2],
    det_to_amp: [burn::nn::Linear<B>; 2],
    /// Fixed per-oscillator frequencies (delta=2.0, theta=6.0, gamma=40.0
    /// Hz), stored as a non-trainable [`burn::module::Param`] (never
    /// `.require_grad()`-enabled) so it still round-trips through
    /// [`burn::module::Module::into_record`]/`load_record` — a raw
    /// (non-`Param`) `Tensor` field would silently discard its value on
    /// that path (`ConstantRecord` serializes to nothing).
    frequencies: burn::module::Param<Tensor<B, 1>>,
    n_osc: usize,
    n_discrete_steps: usize,
    match_threshold: f64,
}

impl<B: Backend> PhaseTrackerStatic<B> {
    /// Construct from a [`PhaseTrackerConfig`] (reusing its validated
    /// detection/band/step/threshold fields; the dynamics-specific fields
    /// are unused since this variant has no learnable dynamics).
    pub fn new(cfg: &PhaseTrackerConfig, device: &B::Device, seed: &mut Seed) -> Self {
        let n_osc = cfg.n_osc();
        let det_to_phase = [
            seeded_linear::<B>(
                cfg.detection_dim,
                crate::phase_tracker::DET_HIDDEN,
                true,
                device,
                seed,
            ),
            seeded_linear::<B>(crate::phase_tracker::DET_HIDDEN, n_osc, true, device, seed),
        ];
        let det_to_amp = [
            seeded_linear::<B>(
                cfg.detection_dim,
                crate::phase_tracker::DET_HIDDEN,
                true,
                device,
                seed,
            ),
            seeded_linear::<B>(crate::phase_tracker::DET_HIDDEN, n_osc, true, device, seed),
        ];
        let mut freqs = Vec::with_capacity(n_osc);
        freqs.extend(std::iter::repeat_n(2.0, cfg.n_delta));
        freqs.extend(std::iter::repeat_n(6.0, cfg.n_theta));
        freqs.extend(std::iter::repeat_n(40.0, cfg.n_gamma));
        let frequencies = burn::module::Param::initialized(
            Default::default(),
            Tensor::from_data(burn::tensor::TensorData::new(freqs, vec![n_osc]), device),
        );

        Self {
            det_to_phase,
            det_to_amp,
            frequencies,
            n_osc,
            n_discrete_steps: cfg.n_discrete_steps,
            match_threshold: cfg.match_threshold,
        }
    }

    /// Total oscillator count.
    pub fn n_osc(&self) -> usize {
        self.n_osc
    }

    /// Validate that the detection-encoder and `frequencies` parameter
    /// tensors' current shapes still match this tracker's declared `n_osc`
    /// configuration. See
    /// [`crate::layers::ResonanceLayer::validate_shapes`] for why this check
    /// is necessary after a checkpoint load.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first tensor whose
    /// shape does not match.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        let n = self.n_osc;
        check_dims(
            "det_to_phase[1].weight",
            self.det_to_phase[1].weight.val().dims(),
            [crate::phase_tracker::DET_HIDDEN, n],
        )?;
        check_dims(
            "det_to_amp[1].weight",
            self.det_to_amp[1].weight.val().dims(),
            [crate::phase_tracker::DET_HIDDEN, n],
        )?;
        check_dims("frequencies", self.frequencies.val().dims(), [n])?;
        Ok(())
    }

    /// Encode detections into `(phase, amplitude)`, identical formula to
    /// [`PhaseTracker::encode`].
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `detections`'s width does not
    /// match the configured `detection_dim`.
    pub fn encode(
        &self,
        detections: Tensor<B, 2>,
    ) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let d_in = self.det_to_phase[0].weight.val().dims()[0];
        check_dims("detections", [detections.dims()[1]], [d_in])?;

        let phase_raw = self.det_to_phase[1].forward(burn::tensor::activation::relu(
            self.det_to_phase[0].forward(detections.clone()),
        ));
        let phase = phase_raw.remainder_scalar(std::f64::consts::TAU);
        let amp_raw = self.det_to_amp[1].forward(burn::tensor::activation::relu(
            self.det_to_amp[0].forward(detections),
        ));
        let amp = burn::tensor::activation::softplus(amp_raw, 1.0);
        Ok((phase, amp))
    }

    /// Advance `phase` for [`Self::n_osc`]-wide fixed frequencies over
    /// `n_discrete_steps` steps of `dt=0.01`, with no coupling term.
    /// `amplitude` passes through unchanged (matching the reference).
    pub fn evolve(
        &self,
        mut phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> (Tensor<B, 2>, Tensor<B, 2>) {
        let dt = 0.01;
        let freqs = self.frequencies.val().unsqueeze::<2>();
        for _ in 0..self.n_discrete_steps {
            phase = wrap_floor(
                phase + freqs.clone().mul_scalar(std::f64::consts::TAU * dt),
                std::f64::consts::TAU,
            );
        }
        (phase, amplitude)
    }

    /// Phase-coherence similarity, identical formula to
    /// [`PhaseTracker::phase_similarity`].
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `phase_a`/`phase_b` do not
    /// share an oscillator width.
    pub fn phase_similarity(
        &self,
        phase_a: Tensor<B, 2>,
        phase_b: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let n = phase_a.dims()[1];
        check_dims("phase_b", [phase_b.dims()[1]], [n])?;
        Ok(crate::support::phase_coherence_similarity(
            phase_a,
            phase_b,
            n,
            crate::phase_tracker::PHASE_SIM_EPS,
        ))
    }

    /// Match detections across two consecutive frames — same greedy-matching
    /// contract as [`PhaseTracker::forward`].
    ///
    /// # Errors
    ///
    /// See [`Self::encode`], [`Self::phase_similarity`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        let (phase_t, amp_t) = self.encode(detections_t)?;
        let (phase_t1, _) = self.encode(detections_t1)?;
        let (phase_t_evolved, _) = self.evolve(phase_t, amp_t);
        let sim = self.phase_similarity(phase_t_evolved, phase_t1)?;
        let matches = greedy_match_by_similarity(&sim, self.match_threshold);
        Ok((matches, sim))
    }

    /// Track objects across a sequence of frames — same contract as
    /// [`PhaseTracker::track_sequence`], but `per_frame_phase_correlation`
    /// is always empty (matching the reference, which omits that
    /// computation for this variant).
    ///
    /// # Errors
    ///
    /// See [`Self::encode`], [`Self::phase_similarity`].
    pub fn track_sequence(
        &self,
        frame_detections: Vec<Tensor<B, 2>>,
    ) -> Result<TrackingResult<B>, TrainError> {
        let mut phase_history = Vec::with_capacity(frame_detections.len());
        let mut identity_matches = Vec::new();
        let mut per_frame_sim = Vec::new();
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
            let (evolved_phase, _) = self.evolve(prev_phase, prev_amp);

            let sim = self.phase_similarity(evolved_phase.clone(), phase_t.clone())?;
            let n_prev = evolved_phase.dims()[0];
            let n_curr = phase_t.dims()[0];
            let n_match = n_prev.min(n_curr);

            let matches = greedy_match_by_similarity(&sim, self.match_threshold);
            let n_matched = matches.iter().filter(|&&m| m >= 0).count();
            total_matches += n_matched;
            total_possible += n_match;

            let (max_sims, _) = sim.max_dim_with_indices(1);
            let mean_sim = if n_prev == 0 {
                0.0
            } else {
                crate::support::to_f64_vec(max_sims.squeeze::<1>(1))
                    .iter()
                    .sum::<f64>()
                    / n_prev as f64
            };
            per_frame_sim.push(mean_sim);

            identity_matches.push(matches);
            phase_history.push(phase_t);
        }

        let identity_preservation = total_matches as f64 / total_possible.max(1) as f64;
        Ok(TrackingResult {
            phase_history,
            identity_matches,
            identity_preservation,
            per_frame_similarity: per_frame_sim,
            per_frame_phase_correlation: Vec::new(),
        })
    }
}

// =========================================================================
// SlotAttention ablation variants
// =========================================================================

/// [`TemporalSlotAttentionMOT`] without GRU carry-over (SA-no-GRU): slots
/// are re-initialized from scratch every frame. Tests whether temporal
/// recurrence is necessary for identity preservation, or per-frame slot
/// attention alone suffices.
#[derive(Module, Debug)]
pub struct SlotAttentionNoGRU<B: Backend> {
    det_encoder: [burn::nn::Linear<B>; 2],
    slot_attention: SlotAttentionModule<B>,
    num_slots: usize,
    match_threshold: f64,
}

impl<B: Backend> SlotAttentionNoGRU<B> {
    /// Construct from a [`TemporalSlotAttentionMOTConfig`] (reusing its
    /// validated fields; the temporal-GRU-specific behavior is simply never
    /// invoked).
    pub fn new(cfg: &TemporalSlotAttentionMOTConfig, device: &B::Device, seed: &mut Seed) -> Self {
        let sd = cfg.slot_dim;
        let det_encoder = [
            seeded_linear::<B>(cfg.detection_dim, sd, true, device, seed),
            seeded_linear::<B>(sd, sd, true, device, seed),
        ];
        let slot_attention = SlotAttentionModuleConfig::with_params(
            cfg.num_slots,
            sd,
            sd,
            cfg.num_iterations,
            sd.max(128),
            1e-8,
        )
        .expect("fields already validated by TemporalSlotAttentionMOTConfig::with_params")
        .init::<B>(device, seed);
        Self {
            det_encoder,
            slot_attention,
            num_slots: cfg.num_slots,
            match_threshold: cfg.match_threshold,
        }
    }

    /// Validate that the detection-encoder tensors' shapes and the nested
    /// [`crate::slot_attention::SlotAttentionModule`]'s own parameters still
    /// match this tracker's declared configuration. See
    /// [`crate::layers::ResonanceLayer::validate_shapes`] for why this check
    /// is necessary after a checkpoint load.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first tensor whose
    /// shape does not match.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        check_dims(
            "det_encoder[1].weight",
            self.det_encoder[1].weight.val().dims(),
            [
                self.det_encoder[0].weight.val().dims()[1],
                self.slot_attention.slot_dim(),
            ],
        )?;
        self.slot_attention.validate_shapes()
    }

    /// Process a frame, always ignoring `prev_slots` (fresh slots every
    /// call — the ablated behavior).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `detections`'s width does not
    /// match this tracker's `detection_dim`.
    pub fn process_frame(
        &self,
        detections: Tensor<B, 2>,
        seed: &mut Seed,
    ) -> Result<Tensor<B, 3>, TrainError> {
        let d_in = self.det_encoder[0].weight.val().dims()[0];
        check_dims("detections", [detections.dims()[1]], [d_in])?;
        let features = self.det_encoder[1]
            .forward(burn::tensor::activation::relu(
                self.det_encoder[0].forward(detections),
            ))
            .unsqueeze::<3>();
        self.slot_attention.forward(features, seed)
    }

    /// Cosine similarity between two `[1, k, d]` slot sets.
    pub fn slot_similarity(&self, slots_a: Tensor<B, 3>, slots_b: Tensor<B, 3>) -> Tensor<B, 2> {
        cosine_similarity(slots_a.squeeze::<2>(0), slots_b.squeeze::<2>(0))
    }

    /// Match detections across two consecutive frames.
    ///
    /// # Errors
    ///
    /// See [`Self::process_frame`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
        seed: &mut Seed,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        let slots_t = self.process_frame(detections_t, seed)?;
        let slots_t1 = self.process_frame(detections_t1, seed)?;
        let sim = self.slot_similarity(slots_t, slots_t1);
        let matches = greedy_match_by_similarity(&sim, self.match_threshold);
        Ok((matches, sim))
    }

    /// Track a sequence of frames with independent (no-carry-over) slots per
    /// frame. Returns `(slot_history, identity_matches, identity_preservation,
    /// per_frame_similarity)`.
    ///
    /// # Errors
    ///
    /// See [`Self::process_frame`].
    #[allow(clippy::type_complexity)]
    pub fn track_sequence(
        &self,
        frame_detections: Vec<Tensor<B, 2>>,
        seed: &mut Seed,
    ) -> Result<(Vec<Tensor<B, 3>>, Vec<Vec<i64>>, f64, Vec<f64>), TrainError> {
        let mut slot_history = Vec::with_capacity(frame_detections.len());
        let mut identity_matches = Vec::new();
        let mut per_frame_sim = Vec::new();
        let mut total_matches: usize = 0;
        let mut total_possible: usize = 0;

        let mut prev_slots: Option<Tensor<B, 3>> = None;
        for dets in frame_detections {
            let slots = self.process_frame(dets, seed)?;
            slot_history.push(slots.clone());

            if let Some(prev) = prev_slots {
                let sim = self.slot_similarity(prev, slots.clone());
                let matches = greedy_match_by_similarity(&sim, self.match_threshold);
                let n_matched = matches.iter().filter(|&&m| m >= 0).count();
                total_matches += n_matched;
                total_possible += self.num_slots;

                let (max_sims, _) = sim.max_dim_with_indices(1);
                let mean_sim = crate::support::to_f64_vec(max_sims.squeeze::<1>(1))
                    .iter()
                    .sum::<f64>()
                    / self.num_slots as f64;
                per_frame_sim.push(mean_sim);
                identity_matches.push(matches);
            }
            prev_slots = Some(slots);
        }

        let preservation = total_matches as f64 / total_possible.max(1) as f64;
        Ok((slot_history, identity_matches, preservation, per_frame_sim))
    }
}

/// [`TemporalSlotAttentionMOT`] with every parameter frozen (SA-frozen): the
/// untrained SA baseline paired with [`PhaseTrackerFrozen`] for symmetric
/// ablation design.
#[derive(Module, Debug)]
pub struct SlotAttentionFrozen<B: Backend> {
    inner: TemporalSlotAttentionMOT<B>,
}

impl<B: Backend> SlotAttentionFrozen<B> {
    /// Construct from a [`TemporalSlotAttentionMOTConfig`], freezing every
    /// parameter's gradient immediately after seeded initialization.
    pub fn new(cfg: &TemporalSlotAttentionMOTConfig, device: &B::Device, seed: &mut Seed) -> Self {
        Self {
            inner: cfg.init::<B>(device, seed).no_grad(),
        }
    }

    /// The wrapped, fully-frozen tracker.
    pub fn inner(&self) -> &TemporalSlotAttentionMOT<B> {
        &self.inner
    }

    /// See [`TemporalSlotAttentionMOT::forward`].
    ///
    /// # Errors
    ///
    /// See [`TemporalSlotAttentionMOT::forward`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
        seed: &mut Seed,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        self.inner.forward(detections_t, detections_t1, seed)
    }

    /// See [`TemporalSlotAttentionMOT::track_sequence`].
    ///
    /// # Errors
    ///
    /// See [`TemporalSlotAttentionMOT::track_sequence`].
    #[allow(clippy::type_complexity)]
    pub fn track_sequence(
        &self,
        frame_detections: Vec<Tensor<B, 2>>,
        seed: &mut Seed,
    ) -> Result<(Vec<Tensor<B, 3>>, Vec<Vec<i64>>, f64, Vec<f64>), TrainError> {
        self.inner.track_sequence(frame_detections, seed)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    // --- PhaseTrackerFrozen ---

    #[test]
    fn phase_tracker_frozen_dynamics_does_not_require_grad() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let cfg = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.3).unwrap();
        let mut seed = Seed::new(1, 0);
        let tracker = PhaseTrackerFrozen::<TestAutodiffBackend>::new(&cfg, &dev, &mut seed);
        assert!(!tracker.inner().dynamics().w_delta_requires_grad());
    }

    #[test]
    fn phase_tracker_frozen_forward_matches_bounds() {
        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.3).unwrap();
        let mut seed = Seed::new(2, 0);
        let tracker = PhaseTrackerFrozen::<TestBackend>::new(&cfg, &dev, &mut seed);
        let dets_t = Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.1;
        let dets_t1 = Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.2;
        let (matches, sim) = tracker.forward(dets_t, dets_t1).unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);
    }

    #[test]
    fn phase_tracker_frozen_track_sequence() {
        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.3).unwrap();
        let mut seed = Seed::new(10, 0);
        let tracker = PhaseTrackerFrozen::<TestBackend>::new(&cfg, &dev, &mut seed);
        let frames = vec![
            Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.1,
            Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.2,
        ];
        let result = tracker.track_sequence(frames).unwrap();
        assert_eq!(result.phase_history.len(), 2);
        assert!((0.0..=1.0).contains(&result.identity_preservation));
    }

    // --- PhaseTrackerStatic ---

    #[test]
    fn phase_tracker_static_validate_shapes_passes_for_freshly_initialized_tracker() {
        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 1, 1, 1, 1, 0.3).unwrap();
        let mut seed = Seed::new(30, 0);
        let tracker = PhaseTrackerStatic::<TestBackend>::new(&cfg, &dev, &mut seed);
        assert!(tracker.validate_shapes().is_ok());
    }

    /// WP025-F1 regression (prin-train level): loading a well-formed record
    /// from a differently-configured tracker must be caught by
    /// `validate_shapes`.
    #[test]
    fn phase_tracker_static_validate_shapes_detects_mismatch_after_loading_a_differently_configured_record(
    ) {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 1, 1, 1, 1, 0.3).unwrap();
        let mut seed = Seed::new(31, 0);
        let target = PhaseTrackerStatic::<TestBackend>::new(&cfg, &dev, &mut seed);
        let donor_cfg = PhaseTrackerConfig::with_params(4, 1, 1, 3, 1, 0.3).unwrap();
        let mut seed2 = Seed::new(32, 0);
        let donor = PhaseTrackerStatic::<TestBackend>::new(&donor_cfg, &dev, &mut seed2);

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes = Recorder::<TestBackend>::record(&recorder, donor.into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let candidate = target.load_record(record);

        assert!(candidate.validate_shapes().is_err());
    }

    #[test]
    fn phase_tracker_static_evolve_advances_by_fixed_frequency_only() {
        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 1, 1, 1, 1, 0.3).unwrap();
        let mut seed = Seed::new(3, 0);
        let tracker = PhaseTrackerStatic::<TestBackend>::new(&cfg, &dev, &mut seed);
        assert_eq!(tracker.n_osc(), 3);

        let phase = Tensor::<TestBackend, 2>::zeros([1, 3], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 3], &dev);
        let (new_phase, new_amp) = tracker.evolve(phase, amp.clone());
        let p = new_phase.to_data().to_vec::<f64>().unwrap();
        // delta=2.0, theta=6.0, gamma=40.0 Hz, one step of dt=0.01.
        let expected = [
            std::f64::consts::TAU * 2.0 * 0.01,
            std::f64::consts::TAU * 6.0 * 0.01,
            std::f64::consts::TAU * 40.0 * 0.01,
        ];
        for (v, e) in p.iter().zip(expected.iter()) {
            assert!((v - e).abs() < 1e-10, "{v} vs {e}");
        }
        // Amplitude passes through unchanged.
        assert_eq!(
            new_amp.to_data().to_vec::<f64>().unwrap(),
            amp.to_data().to_vec::<f64>().unwrap()
        );
    }

    #[test]
    fn phase_tracker_static_forward_and_track_sequence() {
        let dev = device();
        let cfg = PhaseTrackerConfig::with_params(4, 1, 1, 2, 2, 0.3).unwrap();
        let mut seed = Seed::new(4, 0);
        let tracker = PhaseTrackerStatic::<TestBackend>::new(&cfg, &dev, &mut seed);
        let dets_t = Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.1;
        let dets_t1 = Tensor::<TestBackend, 2>::ones([3, 4], &dev) * 0.2;
        let (matches, sim) = tracker.forward(dets_t.clone(), dets_t1.clone()).unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);

        let result = tracker.track_sequence(vec![dets_t, dets_t1]).unwrap();
        assert_eq!(result.phase_history.len(), 2);
        assert!(result.per_frame_phase_correlation.is_empty());
    }

    #[test]
    fn phase_tracker_static_gradients_flow_to_encoder_only() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let cfg = PhaseTrackerConfig::with_params(4, 1, 1, 1, 1, 0.3).unwrap();
        let mut seed = Seed::new(5, 0);
        let tracker = PhaseTrackerStatic::<TestAutodiffBackend>::new(&cfg, &dev, &mut seed);
        let dets = Tensor::<TestAutodiffBackend, 2>::ones([2, 4], &dev).require_grad();

        let (phase, amp) = tracker.encode(dets).unwrap();
        let (evolved_phase, _) = tracker.evolve(phase, amp);
        let loss = evolved_phase.sum();
        let grads = loss.backward();

        let grad = tracker.det_to_phase[0]
            .weight
            .val()
            .grad(&grads)
            .map(|g| g.to_data().to_vec::<f64>().unwrap())
            .expect("gradient must be present");
        assert!(grad.iter().all(|v| v.is_finite()));
    }

    // --- SlotAttentionNoGRU ---

    #[test]
    fn slot_attention_no_gru_validate_shapes_passes_for_freshly_initialized_tracker() {
        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(60, 0);
        let tracker = SlotAttentionNoGRU::<TestBackend>::new(&cfg, &dev, &mut seed);
        assert!(tracker.validate_shapes().is_ok());
    }

    /// WP025-F1 regression (prin-train level): loading a well-formed record
    /// from a differently-configured tracker must be caught by
    /// `validate_shapes`.
    #[test]
    fn slot_attention_no_gru_validate_shapes_detects_mismatch_after_loading_a_differently_configured_record(
    ) {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(61, 0);
        let target = SlotAttentionNoGRU::<TestBackend>::new(&cfg, &dev, &mut seed);
        let donor_cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 12, 2, 0.3).unwrap();
        let mut seed2 = Seed::new(62, 0);
        let donor = SlotAttentionNoGRU::<TestBackend>::new(&donor_cfg, &dev, &mut seed2);

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes = Recorder::<TestBackend>::record(&recorder, donor.into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let candidate = target.load_record(record);

        assert!(candidate.validate_shapes().is_err());
    }

    #[test]
    fn slot_attention_no_gru_ignores_prev_slots() {
        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(6, 0);
        let tracker = SlotAttentionNoGRU::<TestBackend>::new(&cfg, &dev, &mut seed);

        let dets = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1;
        let mut s1 = Seed::new(1, 0);
        let out1 = tracker.process_frame(dets.clone(), &mut s1).unwrap();
        let mut s2 = Seed::new(1, 0);
        let out2 = tracker.process_frame(dets, &mut s2).unwrap();
        // Same seed state => same fresh-init output (no dependency on any
        // "previous" state, since none is threaded through at all).
        assert_eq!(
            out1.to_data().to_vec::<f64>().unwrap(),
            out2.to_data().to_vec::<f64>().unwrap()
        );
    }

    #[test]
    fn slot_attention_no_gru_forward_and_track_sequence() {
        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(7, 0);
        let tracker = SlotAttentionNoGRU::<TestBackend>::new(&cfg, &dev, &mut seed);

        let dets_t = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1;
        let dets_t1 = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.2;
        let (matches, sim) = tracker
            .forward(dets_t.clone(), dets_t1.clone(), &mut seed)
            .unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);

        let (history, id_matches, preservation, sims) = tracker
            .track_sequence(vec![dets_t, dets_t1], &mut seed)
            .unwrap();
        assert_eq!(history.len(), 2);
        assert_eq!(id_matches.len(), 1);
        assert_eq!(sims.len(), 1);
        assert!((0.0..=1.0).contains(&preservation));
    }

    // --- SlotAttentionFrozen ---

    #[test]
    fn slot_attention_frozen_forward_matches_bounds() {
        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(8, 0);
        let tracker = SlotAttentionFrozen::<TestBackend>::new(&cfg, &dev, &mut seed);
        let dets_t = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1;
        let dets_t1 = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.2;
        let (matches, sim) = tracker.forward(dets_t, dets_t1, &mut seed).unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);
    }

    #[test]
    fn slot_attention_frozen_does_not_require_grad() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(9, 0);
        let tracker = SlotAttentionFrozen::<TestAutodiffBackend>::new(&cfg, &dev, &mut seed);
        assert!(!tracker.inner().project_k_requires_grad());
    }

    #[test]
    fn slot_attention_frozen_track_sequence() {
        let dev = device();
        let cfg = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap();
        let mut seed = Seed::new(11, 0);
        let tracker = SlotAttentionFrozen::<TestBackend>::new(&cfg, &dev, &mut seed);
        let frames = vec![
            Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1,
            Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.2,
        ];
        let (history, matches, preservation, sims) =
            tracker.track_sequence(frames, &mut seed).unwrap();
        assert_eq!(history.len(), 2);
        assert_eq!(matches.len(), 1);
        assert_eq!(sims.len(), 1);
        assert!((0.0..=1.0).contains(&preservation));
    }
}

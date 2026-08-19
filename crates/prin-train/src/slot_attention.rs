//! Slot Attention baseline for object-centric learning comparison.
//!
//! [`SlotAttentionModule`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.slot_attention.SlotAttentionModule` (Locatello et al. 2020): a
//! non-oscillatory, iterative competitive-attention baseline.
//! [`TemporalSlotAttentionMOT`] extends it with GRU-based temporal slot
//! carry-over for multi-frame tracking — the direct comparison baseline
//! against [`crate::phase_tracker::PhaseTracker`] this WP's mission calls
//! for (`nn.slot_attention.TemporalSlotAttentionMOT`).
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! Per [`SlotAttentionModule::forward`] iteration (`nn/slot_attention.py`):
//!
//! ```text
//! k, v         = project_k(norm_inputs(x)), project_v(norm_inputs(x))   // once, shared
//! slots        = slot_mu + exp(slot_log_sigma)·N(0,1)                  // once, initial
//! for _ in 0..num_iterations:
//!     q          = project_q(norm_slots(slots))
//!     attn       = softmax(k·qᵀ / √slot_dim, dim=slots)                // competition
//!     attn_w     = attn / (Σ_points attn + ε)
//!     updates    = attn_wᵀ · v
//!     slots      = GRU(updates, slots)
//!     slots      = slots + mlp(norm_mlp(slots))
//! ```
//!
//! This is a line-for-line port of `SlotAttentionModule.forward`.
//!
//! **Stochastic forward entry point.** Unlike every other `forward` in this
//! crate, slot initialization draws fresh noise (`torch.randn_like`) on
//! *every* call, not only at construction — so [`SlotAttentionModule::forward`]
//! and [`TemporalSlotAttentionMOT::process_frame`] take `&mut Seed` directly
//! (Coding Standards §1.3: "deterministic seeding threaded through every
//! stochastic entry point"), via `crate::support::seeded_standard_normal`.
//!
//! Standard GRU/`Linear`/`LayerNorm` plumbing uses [`burn::nn`], weights
//! seeded via `crate::support::seeded_linear`/`crate::support::seeded_gru`
//! — see [`crate::attention`]'s module docs for why `Config::init` is not
//! used. `slot_mu`'s PRINet 3.0 init is `N(0, 0.02²)`; this port draws
//! uniform on `[-0.02·√3, 0.02·√3]` (matching variance `0.02²`) via
//! `crate::support::seeded_uniform` — same "only the initial scale is
//! load-bearing" precedent as [`crate::layers`]'s coupling init.
//!
//! Not ported: `SlotAttentionCLEVRN` (CLEVR-N scene+query classification
//! adapter). This WP's "SlotAttention comparison baseline" mission text
//! refers to head-to-head tracking comparison against `PhaseTracker`
//! (`TemporalSlotAttentionMOT`'s own documented purpose); `SlotAttentionCLEVRN`
//! serves a different, CLEVR-N-classification comparison this WP's
//! non-goals explicitly exclude ("confirmatory temporal CLEVR conclusions").
//! Recorded as an explicit out-of-scope discovery for a future WP.

use burn::module::{Module, Param};
use burn::nn::gru::Gru;
use burn::nn::{LayerNorm, LayerNormConfig, Linear};
use burn::tensor::activation::{relu, softmax};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{
    check_dims, greedy_match_by_similarity, seeded_gru, seeded_linear, seeded_standard_normal,
    seeded_uniform,
};

/// Validated hyperparameters for [`SlotAttentionModule`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `num_iterations=3,
/// hidden_dim=max(slot_dim,128), eps=1e-8`.
#[derive(Clone, Debug, PartialEq)]
pub struct SlotAttentionModuleConfig {
    /// Number of slots (object representations).
    pub num_slots: usize,
    /// Dimensionality of each slot vector.
    pub slot_dim: usize,
    /// Dimensionality of input features.
    pub input_dim: usize,
    /// Number of iterative refinement steps.
    pub num_iterations: usize,
    /// Hidden dimension for the slot-update MLP.
    pub hidden_dim: usize,
    /// Small constant for numerical stability.
    pub eps: f64,
}

impl SlotAttentionModuleConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(num_slots: usize, slot_dim: usize, input_dim: usize) -> Result<Self, TrainError> {
        Self::with_params(num_slots, slot_dim, input_dim, 3, slot_dim.max(128), 1e-8)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `num_slots`, `slot_dim`,
    /// `input_dim`, or `hidden_dim` is zero, or
    /// [`TrainError::InvalidStepCount`] if `num_iterations` is zero.
    pub fn with_params(
        num_slots: usize,
        slot_dim: usize,
        input_dim: usize,
        num_iterations: usize,
        hidden_dim: usize,
        eps: f64,
    ) -> Result<Self, TrainError> {
        for (name, value) in [
            ("num_slots", num_slots),
            ("slot_dim", slot_dim),
            ("input_dim", input_dim),
            ("hidden_dim", hidden_dim),
        ] {
            if value == 0 {
                return Err(TrainError::EmptyBand { name });
            }
        }
        if num_iterations == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "num_iterations",
                value: num_iterations,
            });
        }
        Ok(Self {
            num_slots,
            slot_dim,
            input_dim,
            num_iterations,
            hidden_dim,
            eps,
        })
    }

    /// Initialize a [`SlotAttentionModule`] with parameters drawn from the
    /// project's deterministic [`Seed`] (Coding Standards §1.3).
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> SlotAttentionModule<B> {
        let sd = self.slot_dim;
        let bound = 0.02 * 3f64.sqrt();
        let slot_mu = Param::initialized(
            Default::default(),
            seeded_uniform::<B, 3>([1, 1, sd], -bound, bound, device, seed).require_grad(),
        );
        let slot_log_sigma = Param::initialized(
            Default::default(),
            Tensor::<B, 3>::zeros([1, 1, sd], device).require_grad(),
        );

        SlotAttentionModule {
            slot_mu,
            slot_log_sigma,
            norm_inputs: LayerNormConfig::new(self.input_dim).init::<B>(device),
            norm_slots: LayerNormConfig::new(sd).init::<B>(device),
            norm_mlp: LayerNormConfig::new(sd).init::<B>(device),
            project_k: seeded_linear::<B>(self.input_dim, sd, false, device, seed),
            project_v: seeded_linear::<B>(self.input_dim, sd, false, device, seed),
            project_q: seeded_linear::<B>(sd, sd, false, device, seed),
            gru: seeded_gru::<B>(sd, sd, device, seed),
            mlp: [
                seeded_linear::<B>(sd, self.hidden_dim, true, device, seed),
                seeded_linear::<B>(self.hidden_dim, sd, true, device, seed),
            ],
            num_slots: self.num_slots,
            slot_dim: sd,
            input_dim: self.input_dim,
            num_iterations: self.num_iterations,
            eps: self.eps,
            scale: (sd as f64).powf(-0.5),
        }
    }
}

/// Slot Attention mechanism with iterative competitive binding.
///
/// See the module docs for the exact formula. Construct via
/// [`SlotAttentionModuleConfig::init`].
#[derive(Module, Debug)]
pub struct SlotAttentionModule<B: Backend> {
    slot_mu: Param<Tensor<B, 3>>,
    slot_log_sigma: Param<Tensor<B, 3>>,
    norm_inputs: LayerNorm<B>,
    norm_slots: LayerNorm<B>,
    norm_mlp: LayerNorm<B>,
    project_k: Linear<B>,
    project_v: Linear<B>,
    project_q: Linear<B>,
    gru: Gru<B>,
    mlp: [Linear<B>; 2],
    num_slots: usize,
    slot_dim: usize,
    input_dim: usize,
    num_iterations: usize,
    eps: f64,
    scale: f64,
}

impl<B: Backend> SlotAttentionModule<B> {
    /// Number of slots.
    pub fn num_slots(&self) -> usize {
        self.num_slots
    }

    /// Slot dimensionality.
    pub fn slot_dim(&self) -> usize {
        self.slot_dim
    }

    /// Run Slot Attention on input features.
    ///
    /// `inputs` has shape `[batch, n, input_dim]`; returns slots
    /// `[batch, num_slots, slot_dim]`.
    ///
    /// Draws fresh slot-initialization noise from `seed` (see module docs).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `inputs`'s last dimension is
    /// not this module's configured `input_dim`.
    pub fn forward(
        &self,
        inputs: Tensor<B, 3>,
        seed: &mut Seed,
    ) -> Result<Tensor<B, 3>, TrainError> {
        let [batch, _n, d_in] = inputs.dims();
        check_dims("inputs", [d_in], [self.input_dim])?;
        let (k_slots, sd) = (self.num_slots, self.slot_dim);
        let device = inputs.device();

        let inputs_n = self.norm_inputs.forward(inputs);
        let key = self.project_k.forward(inputs_n.clone());
        let value = self.project_v.forward(inputs_n);

        let mu = self
            .slot_mu
            .val()
            .repeat_dim(0, batch)
            .repeat_dim(1, k_slots);
        let sigma = self
            .slot_log_sigma
            .val()
            .exp()
            .repeat_dim(0, batch)
            .repeat_dim(1, k_slots);
        let noise = seeded_standard_normal::<B, 3>([batch, k_slots, sd], &device, seed);
        let mut slots = mu + sigma * noise;

        for _ in 0..self.num_iterations {
            let slots_prev = slots.clone();
            let slots_n = self.norm_slots.forward(slots);
            let q = self.project_q.forward(slots_n);

            let attn_logits = key.clone().matmul(q.swap_dims(1, 2)).mul_scalar(self.scale);
            let attn = softmax(attn_logits, 2);
            let attn_sum = attn.clone().sum_dim(1);
            let attn_weights = attn / (attn_sum + self.eps);
            let updates = attn_weights.swap_dims(1, 2).matmul(value.clone());

            let updates_flat = updates.reshape([batch * k_slots, 1, sd]);
            let prev_flat = slots_prev.reshape([batch * k_slots, 1, sd]);
            let gru_out = self.gru.forward(updates_flat, Some(prev_flat));
            slots = gru_out.reshape([batch, k_slots, sd]);

            let mlp_in = self.norm_mlp.forward(slots.clone());
            let mlp_out = self.mlp[1].forward(relu(self.mlp[0].forward(mlp_in)));
            slots = slots + mlp_out;
        }

        Ok(slots)
    }
}

/// Validated hyperparameters for [`TemporalSlotAttentionMOT`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `num_slots=8,
/// slot_dim=64, num_iterations=3, match_threshold=0.3`.
#[derive(Clone, Debug, PartialEq)]
pub struct TemporalSlotAttentionMOTConfig {
    /// Per-detection input feature dimension.
    pub detection_dim: usize,
    /// Number of object slots (max tracked objects).
    pub num_slots: usize,
    /// Slot representation dimension.
    pub slot_dim: usize,
    /// Slot Attention iterations per frame.
    pub num_iterations: usize,
    /// Minimum similarity for a valid identity match.
    pub match_threshold: f64,
}

impl TemporalSlotAttentionMOTConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(detection_dim: usize) -> Result<Self, TrainError> {
        Self::with_params(detection_dim, 8, 64, 3, 0.3)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `detection_dim`, `num_slots`, or
    /// `slot_dim` is zero, [`TrainError::InvalidStepCount`] if
    /// `num_iterations` is zero, or [`TrainError::InvalidMatchThreshold`] if
    /// `match_threshold` is non-finite.
    pub fn with_params(
        detection_dim: usize,
        num_slots: usize,
        slot_dim: usize,
        num_iterations: usize,
        match_threshold: f64,
    ) -> Result<Self, TrainError> {
        if detection_dim == 0 {
            return Err(TrainError::EmptyBand {
                name: "detection_dim",
            });
        }
        // Reuses SlotAttentionModuleConfig's own validation for the rest.
        let _ = SlotAttentionModuleConfig::with_params(
            num_slots,
            slot_dim,
            slot_dim,
            num_iterations,
            slot_dim.max(128),
            1e-8,
        )?;
        if !match_threshold.is_finite() {
            return Err(TrainError::InvalidMatchThreshold {
                value: match_threshold,
            });
        }
        Ok(Self {
            detection_dim,
            num_slots,
            slot_dim,
            num_iterations,
            match_threshold,
        })
    }

    /// Initialize a [`TemporalSlotAttentionMOT`] with parameters drawn from
    /// the project's deterministic [`Seed`] (Coding Standards §1.3).
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> TemporalSlotAttentionMOT<B> {
        let sd = self.slot_dim;
        let det_encoder = [
            seeded_linear::<B>(self.detection_dim, sd, true, device, seed),
            seeded_linear::<B>(sd, sd, true, device, seed),
        ];
        let slot_attention = SlotAttentionModuleConfig::with_params(
            self.num_slots,
            sd,
            sd,
            self.num_iterations,
            sd.max(128),
            1e-8,
        )
        .expect("hyperparameters already validated by TemporalSlotAttentionMOTConfig::with_params")
        .init::<B>(device, seed);
        let temporal_gru = seeded_gru::<B>(sd, sd, device, seed);
        let temporal_norm = LayerNormConfig::new(sd).init::<B>(device);

        TemporalSlotAttentionMOT {
            det_encoder,
            slot_attention,
            temporal_gru,
            temporal_norm,
            num_slots: self.num_slots,
            slot_dim: sd,
            match_threshold: self.match_threshold,
        }
    }
}

/// Temporal Slot Attention for multi-frame object tracking — the direct
/// comparison baseline against [`crate::phase_tracker::PhaseTracker`].
///
/// See the module docs for the exact formula. Construct via
/// [`TemporalSlotAttentionMOTConfig::init`].
#[derive(Module, Debug)]
pub struct TemporalSlotAttentionMOT<B: Backend> {
    det_encoder: [Linear<B>; 2],
    slot_attention: SlotAttentionModule<B>,
    temporal_gru: Gru<B>,
    temporal_norm: LayerNorm<B>,
    num_slots: usize,
    slot_dim: usize,
    match_threshold: f64,
}

impl<B: Backend> TemporalSlotAttentionMOT<B> {
    /// Number of object slots.
    pub fn num_slots(&self) -> usize {
        self.num_slots
    }

    /// Slot dimensionality.
    pub fn slot_dim(&self) -> usize {
        self.slot_dim
    }

    /// Minimum similarity for a valid identity match.
    pub fn match_threshold(&self) -> f64 {
        self.match_threshold
    }

    /// Whether the inner `SlotAttentionModule`'s `project_k` weight
    /// currently requires grad — crate-internal introspection for
    /// [`crate::ablation::SlotAttentionFrozen`]'s regression test (confirms
    /// [`burn::module::Module::no_grad`] actually froze every parameter).
    #[cfg(test)]
    pub(crate) fn project_k_requires_grad(&self) -> bool {
        self.slot_attention.project_k.weight.val().is_require_grad()
    }

    /// Process one frame's detections and return updated slots
    /// `[1, num_slots, slot_dim]`, carrying `prev_slots` forward via GRU when
    /// supplied.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `detections`'s width does not
    /// match this tracker's `detection_dim`.
    pub fn process_frame(
        &self,
        detections: Tensor<B, 2>,
        prev_slots: Option<Tensor<B, 3>>,
        seed: &mut Seed,
    ) -> Result<Tensor<B, 3>, TrainError> {
        let d_in = self.det_encoder[0].weight.val().dims()[0];
        check_dims("detections", [detections.dims()[1]], [d_in])?;

        let features = self.det_encoder[1]
            .forward(relu(self.det_encoder[0].forward(detections)))
            .unsqueeze::<3>();
        let new_slots = self.slot_attention.forward(features, seed)?;

        let slots = match prev_slots {
            Some(prev) => {
                let (k, sd) = (self.num_slots, self.slot_dim);
                let updated = self.temporal_gru.forward(
                    new_slots.reshape([k, 1, sd]),
                    Some(prev.reshape([k, 1, sd])),
                );
                self.temporal_norm.forward(updated.reshape([1, k, sd]))
            }
            None => new_slots,
        };
        Ok(slots)
    }

    /// Cosine similarity between two slot sets, each `[1, k, d]` (the shape
    /// [`Self::process_frame`] always returns).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `slots_a`/`slots_b`'s leading
    /// dimension is not `1`.
    pub fn slot_similarity(
        &self,
        slots_a: Tensor<B, 3>,
        slots_b: Tensor<B, 3>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        check_dims("slots_a", [slots_a.dims()[0]], [1])?;
        check_dims("slots_b", [slots_b.dims()[0]], [1])?;
        Ok(cosine_similarity(
            slots_a.squeeze::<2>(0),
            slots_b.squeeze::<2>(0),
        ))
    }

    /// Match detections across two consecutive frames.
    ///
    /// # Errors
    ///
    /// See [`Self::process_frame`], [`Self::slot_similarity`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
        seed: &mut Seed,
    ) -> Result<(Vec<i64>, Tensor<B, 2>), TrainError> {
        let slots_t = self.process_frame(detections_t, None, seed)?;
        let slots_t1 = self.process_frame(detections_t1, Some(slots_t.clone()), seed)?;
        let sim = self.slot_similarity(slots_t, slots_t1)?;
        let matches = greedy_match_by_similarity(&sim, self.match_threshold);
        Ok((matches, sim))
    }

    /// Track objects across a sequence of frames, mirroring
    /// [`crate::phase_tracker::PhaseTracker::track_sequence`]'s return shape
    /// (module docs: `slot_history` instead of `phase_history`, no
    /// `per_frame_phase_correlation`).
    ///
    /// # Errors
    ///
    /// See [`Self::process_frame`], [`Self::slot_similarity`].
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
            let slots = self.process_frame(dets, prev_slots.clone(), seed)?;
            slot_history.push(slots.clone());

            if let Some(prev) = prev_slots {
                let sim = self.slot_similarity(prev, slots.clone())?;
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

/// Row-wise cosine similarity between `a: [k_a, d]` and `b: [k_b, d]`,
/// returning `[k_a, k_b]`. Shared by [`TemporalSlotAttentionMOT`] and
/// [`crate::ablation::SlotAttentionNoGRU`] (both PRINet 3.0 references
/// L2-normalize then matmul identically).
pub(crate) fn cosine_similarity<B: Backend>(a: Tensor<B, 2>, b: Tensor<B, 2>) -> Tensor<B, 2> {
    let a_norm = l2_normalize(a);
    let b_norm = l2_normalize(b);
    a_norm.matmul(b_norm.swap_dims(0, 1))
}

fn l2_normalize<B: Backend>(x: Tensor<B, 2>) -> Tensor<B, 2> {
    let norm = x.clone().powf_scalar(2.0).sum_dim(1).sqrt();
    x / norm
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

    fn small_sa_config() -> SlotAttentionModuleConfig {
        SlotAttentionModuleConfig::with_params(3, 8, 5, 2, 16, 1e-8).unwrap()
    }

    // --- Config validation ---

    #[test]
    fn slot_attention_zero_sizes_rejected() {
        assert!(matches!(
            SlotAttentionModuleConfig::new(0, 8, 5).unwrap_err(),
            TrainError::EmptyBand { name: "num_slots" }
        ));
    }

    #[test]
    fn slot_attention_zero_iterations_rejected() {
        assert!(matches!(
            SlotAttentionModuleConfig::with_params(3, 8, 5, 0, 16, 1e-8).unwrap_err(),
            TrainError::InvalidStepCount { .. }
        ));
    }

    #[test]
    fn slot_attention_accessors_report_configured_sizes() {
        let mut seed = Seed::new(0, 0);
        let sa = small_sa_config().init::<TestBackend>(&device(), &mut seed);
        assert_eq!(sa.num_slots(), 3);
        assert_eq!(sa.slot_dim(), 8);
    }

    #[test]
    fn mot_config_new_uses_prinet_3_0_defaults() {
        let cfg = TemporalSlotAttentionMOTConfig::new(4).unwrap();
        assert_eq!(cfg.num_slots, 8);
        assert_eq!(cfg.slot_dim, 64);
        assert_eq!(cfg.num_iterations, 3);
        assert!((cfg.match_threshold - 0.3).abs() < 1e-15);
    }

    #[test]
    fn mot_config_zero_detection_dim_rejected() {
        assert!(matches!(
            TemporalSlotAttentionMOTConfig::with_params(0, 8, 64, 3, 0.3).unwrap_err(),
            TrainError::EmptyBand {
                name: "detection_dim"
            }
        ));
    }

    #[test]
    fn mot_config_non_finite_threshold_rejected() {
        assert!(matches!(
            TemporalSlotAttentionMOTConfig::with_params(4, 8, 64, 3, f64::NAN).unwrap_err(),
            TrainError::InvalidMatchThreshold { .. }
        ));
    }

    #[test]
    fn mot_accessors_report_configured_sizes() {
        let mut seed = Seed::new(1, 0);
        let mot = small_mot_config().init::<TestBackend>(&device(), &mut seed);
        assert_eq!(mot.num_slots(), 3);
        assert_eq!(mot.slot_dim(), 8);
        assert!((mot.match_threshold() - 0.3).abs() < 1e-15);
    }

    // --- SlotAttentionModule forward ---

    #[test]
    fn slot_attention_forward_returns_expected_shape_and_finite() {
        let mut seed = Seed::new(1, 0);
        let sa = small_sa_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let inputs = Tensor::<TestBackend, 3>::ones([2, 6, 5], &dev) * 0.3;
        let out = sa.forward(inputs, &mut seed).unwrap();
        assert_eq!(out.dims(), [2, 3, 8]);
        let data = out.to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite()));
    }

    #[test]
    fn slot_attention_forward_rejects_wrong_input_dim() {
        let mut seed = Seed::new(2, 0);
        let sa = small_sa_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let inputs = Tensor::<TestBackend, 3>::ones([2, 6, 4], &dev);
        let err = sa.forward(inputs, &mut seed).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "inputs", .. }
        ));
    }

    #[test]
    fn slot_attention_forward_is_stochastic_across_seed_state() {
        let mut seed = Seed::new(3, 0);
        let sa = small_sa_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let inputs = Tensor::<TestBackend, 3>::ones([1, 4, 5], &dev) * 0.2;

        let mut s1 = Seed::new(100, 0);
        let out1 = sa.forward(inputs.clone(), &mut s1).unwrap();
        let mut s2 = Seed::new(200, 0);
        let out2 = sa.forward(inputs, &mut s2).unwrap();

        let d1 = out1.to_data().to_vec::<f64>().unwrap();
        let d2 = out2.to_data().to_vec::<f64>().unwrap();
        assert_ne!(d1, d2, "different seeds should give different slot noise");
    }

    #[test]
    fn slot_attention_forward_is_reproducible_for_same_seed() {
        let mut seed = Seed::new(4, 0);
        let sa = small_sa_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let inputs = Tensor::<TestBackend, 3>::ones([1, 4, 5], &dev) * 0.2;

        let mut s1 = Seed::new(77, 0);
        let out1 = sa.forward(inputs.clone(), &mut s1).unwrap();
        let mut s2 = Seed::new(77, 0);
        let out2 = sa.forward(inputs, &mut s2).unwrap();

        assert_eq!(
            out1.to_data().to_vec::<f64>().unwrap(),
            out2.to_data().to_vec::<f64>().unwrap()
        );
    }

    // --- Gradient reference tests ---

    #[test]
    fn slot_attention_gradients_flow_to_every_parameter() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let sa = small_sa_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let inputs = Tensor::<TestAutodiffBackend, 3>::ones([2, 6, 5], &dev).require_grad() * 0.3;

        let mut fseed = Seed::new(55, 0);
        let out = sa.forward(inputs, &mut fseed).unwrap();
        let loss = out.sum();
        let grads = loss.backward();

        for grad in [
            sa.project_k
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            sa.slot_mu
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            sa.gru
                .update_gate
                .input_transform
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            sa.mlp[0]
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    // --- TemporalSlotAttentionMOT ---

    fn small_mot_config() -> TemporalSlotAttentionMOTConfig {
        TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3).unwrap()
    }

    #[test]
    fn mot_process_frame_shape() {
        let mut seed = Seed::new(5, 0);
        let mot = small_mot_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let dets = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1;
        let slots = mot.process_frame(dets, None, &mut seed).unwrap();
        assert_eq!(slots.dims(), [1, 3, 8]);
    }

    #[test]
    fn mot_forward_matches_within_bounds() {
        let mut seed = Seed::new(6, 0);
        let mot = small_mot_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let dets_t = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.1;
        let dets_t1 = Tensor::<TestBackend, 2>::ones([5, 4], &dev) * 0.15;
        let (matches, sim) = mot.forward(dets_t, dets_t1, &mut seed).unwrap();
        assert_eq!(matches.len(), 3);
        assert_eq!(sim.dims(), [3, 3]);
        for m in matches {
            assert!(m == -1 || (0..3).contains(&m));
        }
    }

    #[test]
    fn mot_track_sequence_history_and_preservation() {
        let mut seed = Seed::new(7, 0);
        let mot = small_mot_config().init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let frames: Vec<_> = (0..4)
            .map(|i| Tensor::<TestBackend, 2>::ones([5, 4], &dev) * (0.1 * (i as f64 + 1.0)))
            .collect();
        let (history, matches, preservation, sims) = mot.track_sequence(frames, &mut seed).unwrap();
        assert_eq!(history.len(), 4);
        assert_eq!(matches.len(), 3);
        assert_eq!(sims.len(), 3);
        assert!((0.0..=1.0).contains(&preservation));
    }

    #[test]
    fn mot_process_frame_rejects_wrong_detection_dim() {
        let mut seed = Seed::new(8, 0);
        let mot = small_mot_config().init::<TestBackend>(&device(), &mut seed);
        let dets = Tensor::<TestBackend, 2>::ones([5, 3], &device());
        let err = mot.process_frame(dets, None, &mut seed).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "detections",
                ..
            }
        ));
    }

    // --- cosine_similarity ---

    #[test]
    fn cosine_similarity_identical_rows_gives_one() {
        let dev = device();
        let a = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![1.0, 2.0, 3.0], vec![1, 3]),
            &dev,
        );
        let sim = cosine_similarity(a.clone(), a);
        let v = sim.to_data().to_vec::<f64>().unwrap()[0];
        assert!((v - 1.0).abs() < 1e-10);
    }
}

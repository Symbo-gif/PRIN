//! Rust-native training pipeline for [`PhaseTracker`]/
//! [`TemporalSlotAttentionMOT`] on temporal CLEVR-N sequences (WP-027,
//! extended WP-031): a direct port of PRINet 3.0's `TemporalTrainer`
//! (`utils/temporal_training.py:454-869`) and `train_multi_seed`
//! (`:904-948`), entirely in Rust per Project Plan §4 rule 2 ("the Python
//! layer contains no numerics") — the Python trainable API (`crates/prin-py`)
//! is a thin orchestration wrapper around [`train_phase_tracker`], not a
//! reimplementation.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! - **Optimizer**: Adam (`burn::optim::Adam`), matching
//!   `torch.optim.Adam(model.parameters(), lr, weight_decay)`.
//! - **Learning-rate schedule**: linear warmup over `warmup_epochs`, then
//!   cosine annealing to `lr * 0.01` over the remaining epochs — a faithful
//!   *structural* port of `_warmup_lr` + `CosineAnnealingLR(T_max=max_epochs,
//!   eta_min=lr*0.01)` (`:518-523`, `:511-516`). **Documented deviation**:
//!   the reference's `CosineAnnealingLR` is a stateful PyTorch scheduler
//!   whose `.step()` call count (not the epoch index) drives its internal
//!   cosine phase, which after the warmup/no-op interaction at exactly
//!   `epoch == warmup_epochs` produces an LR trajectory offset by up to one
//!   epoch from `cos(pi * (epoch - warmup_epochs) / (max_epochs -
//!   warmup_epochs))` used here. This does not change what the schedule
//!   *is* (linear warmup then cosine decay to `1%` of `lr`), only the exact
//!   epoch a given LR value is used on — immaterial to convergence and not
//!   worth reproducing PyTorch's specific scheduler step-counting quirk for.
//! - **Loss**: [`crate::losses::hungarian_similarity_loss`] +
//!   `0.1 * `[`crate::losses::temporal_smoothness_loss`], computed on
//!   [`PhaseTracker::forward`]'s/[`TemporalSlotAttentionMOT::forward`]'s
//!   differentiable similarity matrix — never on `track_sequence`'s output
//!   — matching `_train_step_pt`/`_train_step_sa` (`:540-627`).
//! - **Gradient clipping**: Burn's built-in `GradientClippingConfig::Norm`.
//!   **Documented deviation**: Burn clips each parameter tensor's gradient
//!   by its own L2 norm independently; PyTorch's
//!   `nn.utils.clip_grad_norm_` computes one *global* L2 norm across every
//!   parameter and scales all of them by the same factor. Both bound
//!   gradient magnitude for training stability; the global-vs-per-tensor
//!   distinction does not affect this WP's acceptance criterion (reaching
//!   the registered validation IP score).
//! - **Early stopping**: smoothed (moving-average) validation loss with
//!   patience, best-model restore — direct port of `train`
//!   (`:780-869`), using `PhaseTracker`/`TemporalSlotAttentionMOT`'s derived
//!   `Clone` impl in place of the reference's
//!   `copy.deepcopy(model.state_dict())` snapshot/restore.
//! - **Evaluation**: [`PhaseTracker::track_sequence`]/
//!   [`TemporalSlotAttentionMOT::track_sequence`] compute
//!   `identity_preservation`; loss-for-reporting is recomputed via the same
//!   differentiable path as training, under `model.valid()` (Burn's
//!   no-autodiff-graph inference mode, the equivalent of the reference's
//!   `@torch.no_grad()` on `evaluate`); `idsw`/`tfr` come from
//!   [`crate::temporal_metrics::identity_switches`]/
//!   [`crate::temporal_metrics::track_fragmentation_rate`] over the returned
//!   identity-match history, matching `evaluate`'s own calls to those same
//!   functions (`:716-717`).
//! - **`count_parameters`/`TrainingSnapshot`/`train_multi_seed`** (WP-031):
//!   see each item's own docs for its exact reference correspondence.

use burn::grad_clipping::GradientClippingConfig;
use burn::module::{AutodiffModule, Module, ModuleVisitor, ParamId};
use burn::optim::{AdamConfig, GradientsParams, Optimizer};
use burn::tensor::backend::{AutodiffBackend, Backend};
use burn::tensor::Tensor;
use prin_dynamics::Seed;
use prin_metrics::order::kuramoto_order_parameter;

use crate::dataset::SequenceData;
use crate::error::TrainError;
use crate::losses::{hungarian_similarity_loss, temporal_smoothness_loss};
use crate::phase_tracker::PhaseTracker;
use crate::slot_attention::TemporalSlotAttentionMOT;
use crate::support::{seeded_uniform, to_f64_vec};
use crate::temporal_metrics::{identity_switches, track_fragmentation_rate};

/// Weight of [`temporal_smoothness_loss`] in the combined training loss,
/// matching the reference's hardcoded `0.1` (`temporal_training.py:580,625`).
const SMOOTHNESS_WEIGHT: f64 = 0.1;

/// Minimum absolute detection-vector sum for a frame to be considered
/// non-degenerate (fully occluded), matching the reference's `1e-8`
/// threshold (`temporal_training.py:566`).
const DEGENERATE_FRAME_THRESHOLD: f64 = 1e-8;

/// Reference `TemporalTrainer.__init__`'s default `snapshot_epochs`
/// (`temporal_training.py:495`).
const DEFAULT_SNAPSHOT_EPOCHS: [usize; 5] = [0, 10, 25, 50, 100];

/// Validated hyperparameters for [`train_phase_tracker`]/
/// [`train_temporal_slot_attention_mot`].
///
/// Defaults ([`Self::default`]) match PRINet 3.0's `TemporalTrainer.__init__`
/// (`temporal_training.py:485-498`): `lr=3e-4, weight_decay=0.0,
/// max_epochs=100, patience=10, smoothing_window=5, warmup_epochs=5,
/// grad_clip=1.0, snapshot_epochs=(0,10,25,50,100)`.
#[derive(Clone, Debug, PartialEq)]
pub struct TemporalTrainerConfig {
    /// Base learning rate (post-warmup peak).
    pub lr: f64,
    /// Adam weight-decay coefficient.
    pub weight_decay: f64,
    /// Maximum training epochs.
    pub max_epochs: usize,
    /// Early-stopping patience, in epochs of no smoothed-validation-loss
    /// improvement.
    pub patience: usize,
    /// Moving-average window (epochs) for the early-stopping validation
    /// loss signal.
    pub smoothing_window: usize,
    /// Linear-warmup epoch count.
    pub warmup_epochs: usize,
    /// Gradient-clipping L2-norm threshold (see module docs for the
    /// per-tensor-vs-global caveat).
    pub grad_clip: f64,
    /// Epochs at which to capture a [`TrainingSnapshot`] (plus a trailing
    /// snapshot at the final epoch, if not already in this set — matching
    /// `train`'s `:862-867`).
    pub snapshot_epochs: Vec<usize>,
}

impl Default for TemporalTrainerConfig {
    fn default() -> Self {
        Self {
            lr: 3e-4,
            weight_decay: 0.0,
            max_epochs: 100,
            patience: 10,
            smoothing_window: 5,
            warmup_epochs: 5,
            grad_clip: 1.0,
            snapshot_epochs: DEFAULT_SNAPSHOT_EPOCHS.to_vec(),
        }
    }
}

impl TemporalTrainerConfig {
    /// Validate hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidLearningRate`] if `lr` is non-positive
    /// or non-finite, [`TrainError::NonFiniteParameter`] if `weight_decay`
    /// is negative/non-finite or `grad_clip` is non-positive/non-finite, or
    /// [`TrainError::InvalidStepCount`] if `max_epochs` is zero.
    pub fn validate(&self) -> Result<(), TrainError> {
        if !self.lr.is_finite() || self.lr <= 0.0 {
            return Err(TrainError::InvalidLearningRate { value: self.lr });
        }
        if !self.weight_decay.is_finite() || self.weight_decay < 0.0 {
            return Err(TrainError::NonFiniteParameter {
                name: "weight_decay",
                value: self.weight_decay,
            });
        }
        if self.max_epochs == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "max_epochs",
                value: self.max_epochs,
            });
        }
        if !self.grad_clip.is_finite() || self.grad_clip <= 0.0 {
            return Err(TrainError::NonFiniteParameter {
                name: "grad_clip",
                value: self.grad_clip,
            });
        }
        Ok(())
    }

    /// Effective learning rate for `epoch` (0-indexed): linear warmup to
    /// `lr`, then cosine anneal to `lr * 0.01` — see module docs for the
    /// exact-step-count caveat versus PyTorch's `CosineAnnealingLR`.
    fn lr_at(&self, epoch: usize) -> f64 {
        if self.warmup_epochs > 0 && epoch < self.warmup_epochs {
            return self.lr * (epoch + 1) as f64 / self.warmup_epochs as f64;
        }
        let remaining = (self.max_epochs.saturating_sub(self.warmup_epochs)).max(1);
        let t = (epoch.saturating_sub(self.warmup_epochs)).min(remaining) as f64;
        let eta_min = self.lr * 0.01;
        eta_min
            + (self.lr - eta_min) * (1.0 + (std::f64::consts::PI * t / remaining as f64).cos())
                / 2.0
    }
}

/// Validation metrics for one dataset pass, matching the reference
/// `evaluate`'s return dict (`temporal_training.py:685-747`).
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct ValMetrics {
    /// Mean training-loss-formula value (for reporting/early-stopping).
    pub loss: f64,
    /// Mean `identity_preservation` across the dataset.
    pub ip: f64,
    /// Mean identity-switch count across the dataset (a per-sequence mean of
    /// [`crate::temporal_metrics::identity_switches`]'s integer count, hence
    /// `f64`, matching the reference's `total_idsw / n` division).
    pub idsw: f64,
    /// Mean track-fragmentation rate across the dataset.
    pub tfr: f64,
}

/// Captured training state at a specific epoch.
///
/// Direct port of PRINet 3.0's `TrainingSnapshot` dataclass
/// (`temporal_training.py:391-415`). `phase_coherence` is only ever
/// nonzero for [`train_phase_tracker`] (the reference gates its computation
/// on `_is_phase_tracker()`); `slot_entropy` is declared in the reference
/// dataclass but its computation is never actually implemented anywhere in
/// `_capture_snapshot` (a reference-side dead field, for either tracker) —
/// this port preserves that gap rather than inventing an entropy formula
/// the reference itself never specified, and always reports `0.0`.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct TrainingSnapshot {
    /// Epoch number.
    pub epoch: usize,
    /// Training loss.
    pub train_loss: f64,
    /// Validation loss.
    pub val_loss: f64,
    /// Validation identity preservation.
    pub val_ip: f64,
    /// Validation identity switches (mean across the validation set,
    /// truncated to an integer — matching the reference's `int(...)` cast).
    pub val_idsw: i64,
    /// Gradient L2 norm from the most recent training step.
    pub gradient_norm: f64,
    /// Parameter L2 norm at snapshot time.
    pub param_norm: f64,
    /// Mean Kuramoto order parameter of the dynamics evolved from a random
    /// phase (PhaseTracker only; always `0.0` for SlotAttention).
    pub phase_coherence: f64,
    /// Always `0.0` — see struct docs.
    pub slot_entropy: f64,
}

/// Complete training-run result, matching the reference `TrainingResult`
/// dataclass (`temporal_training.py:418-446`).
#[derive(Clone, Debug, Default, PartialEq)]
pub struct TrainingResult {
    /// Final epoch's mean training loss.
    pub final_train_loss: f64,
    /// Final (best-restored) validation loss.
    pub final_val_loss: f64,
    /// Final (best-restored) validation identity preservation.
    pub final_val_ip: f64,
    /// Best smoothed validation loss observed.
    pub best_val_loss: f64,
    /// Epoch at which the best smoothed validation loss was observed.
    pub best_epoch: usize,
    /// Total epochs actually run (may be `< max_epochs` on early stop).
    pub total_epochs: usize,
    /// Total wall-clock training time, in seconds.
    pub wall_time_s: f64,
    /// Captured training-dynamics snapshots (see [`TemporalTrainerConfig::snapshot_epochs`]).
    pub snapshots: Vec<TrainingSnapshot>,
    /// Per-epoch mean training loss.
    pub train_losses: Vec<f64>,
    /// Per-epoch validation loss.
    pub val_losses: Vec<f64>,
    /// Per-epoch validation identity preservation.
    pub val_ips: Vec<f64>,
}

/// Model parameter counts, with complex-aware adjustment.
///
/// Direct port of `count_parameters`'s return dict (`temporal_training.py:344-383`).
/// **Reformulation note**: the reference's `complex_adjusted` doubles the
/// count of any `torch.complex64` parameter, for fair comparison between
/// PhaseTracker (whose *reference* Kuramoto coupling uses complex
/// arithmetic) and SlotAttention (all real-valued). PRIN's Burn models have
/// no complex-tensor parameters at all — [`crate::phase_tracker`]'s module
/// docs document the real-valued reformulation of `phase_similarity` that
/// makes this possible — so `complex_adjusted` always equals `total` here;
/// the field is retained for API parity and so that a future complex-valued
/// model would not need a breaking signature change.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct ParameterCounts {
    /// Total parameter element count.
    pub total: usize,
    /// Element count of parameters with `requires_grad` set.
    pub trainable: usize,
    /// Element count of parameters without `requires_grad` (frozen).
    pub frozen: usize,
    /// `total`, complex-doubled where applicable — always equal to `total`
    /// in this port (see struct docs).
    pub complex_adjusted: usize,
}

struct ParamCountVisitor {
    total: usize,
    trainable: usize,
    frozen: usize,
}

impl<B: Backend> ModuleVisitor<B> for ParamCountVisitor {
    fn visit_float<const D: usize>(&mut self, _id: ParamId, tensor: &Tensor<B, D>) {
        let n = tensor.shape().num_elements();
        self.total += n;
        if tensor.is_require_grad() {
            self.trainable += n;
        } else {
            self.frozen += n;
        }
    }
}

/// Count `module`'s parameters, with complex-aware counting (see
/// [`ParameterCounts`] for why `complex_adjusted == total` in this port).
///
/// Direct port of `count_parameters` (`temporal_training.py:344-383`).
pub fn count_parameters<B: Backend, M: Module<B>>(module: &M) -> ParameterCounts {
    let mut visitor = ParamCountVisitor {
        total: 0,
        trainable: 0,
        frozen: 0,
    };
    module.visit(&mut visitor);
    ParameterCounts {
        total: visitor.total,
        trainable: visitor.trainable,
        frozen: visitor.frozen,
        complex_adjusted: visitor.total,
    }
}

struct ParamNormVisitor {
    sq_sum: f64,
}

impl<B: Backend> ModuleVisitor<B> for ParamNormVisitor {
    fn visit_float<const D: usize>(&mut self, _id: ParamId, tensor: &Tensor<B, D>) {
        let sq: Tensor<B, 1> = tensor.clone().powf_scalar(2.0).sum();
        self.sq_sum += sq
            .into_data()
            .to_vec::<f64>()
            .expect("sum reduces to one element")[0];
    }
}

/// Total L2 norm of `module`'s parameters.
///
/// Direct port of `TemporalTrainer._compute_param_norm`
/// (`temporal_training.py:533-538`).
pub fn compute_param_norm<B: Backend, M: Module<B>>(module: &M) -> f64 {
    let mut visitor = ParamNormVisitor { sq_sum: 0.0 };
    module.visit(&mut visitor);
    visitor.sq_sum.sqrt()
}

struct GradNormVisitor<'a> {
    grads: &'a GradientsParams,
    sq_sum: f64,
}

impl<'a, B: AutodiffBackend> ModuleVisitor<B> for GradNormVisitor<'a> {
    fn visit_float<const D: usize>(&mut self, id: ParamId, _tensor: &Tensor<B, D>) {
        if let Some(grad) = self.grads.get::<B::InnerBackend, D>(id) {
            let sq: Tensor<B::InnerBackend, 1> = grad.powf_scalar(2.0).sum();
            self.sq_sum += sq
                .into_data()
                .to_vec::<f64>()
                .expect("sum reduces to one element")[0];
        }
    }
}

/// Total L2 norm of `module`'s gradients recorded in `grads`.
///
/// Direct port of `TemporalTrainer._compute_gradient_norm`
/// (`temporal_training.py:525-531`).
pub fn compute_gradient_norm<B: AutodiffBackend, M: Module<B>>(
    module: &M,
    grads: &GradientsParams,
) -> f64 {
    let mut visitor = GradNormVisitor { grads, sq_sum: 0.0 };
    module.visit(&mut visitor);
    visitor.sq_sum.sqrt()
}

/// A sequence's detections at frame `t` as a tensor, or `None` if the frame
/// is degenerate (every feature within [`DEGENERATE_FRAME_THRESHOLD`] of
/// zero — fully occluded), matching the reference's skip check
/// (`temporal_training.py:566`).
fn non_degenerate_frame<B: Backend>(
    seq: &SequenceData,
    t: usize,
    device: &B::Device,
) -> Option<Tensor<B, 2>> {
    let abs_sum: f64 = seq.frames[t].iter().map(|v| v.abs()).sum();
    if abs_sum < DEGENERATE_FRAME_THRESHOLD {
        None
    } else {
        Some(seq.frame_tensor::<B>(t, device))
    }
}

/// One training step over a single sequence: direct port of `_train_step_pt`
/// (`temporal_training.py:540-582`).
///
/// Returns `None` if every transition was degenerate (no gradient to take).
fn train_step_pt<B: AutodiffBackend>(
    model: &PhaseTracker<B>,
    seq: &SequenceData,
    device: &B::Device,
) -> Option<Tensor<B, 1>> {
    let mut total_loss: Option<Tensor<B, 1>> = None;
    let mut sim_history: Vec<Tensor<B, 2>> = Vec::new();
    let mut n_transitions = 0usize;

    for t in 1..seq.n_frames {
        let (Some(dets_prev), Some(dets_curr)) = (
            non_degenerate_frame::<B>(seq, t - 1, device),
            non_degenerate_frame::<B>(seq, t, device),
        ) else {
            continue;
        };

        let (_matches, sim) = model
            .forward(dets_prev, dets_curr)
            .expect("shapes are constructed to match the tracker's detection_dim");
        let loss = hungarian_similarity_loss(sim.clone(), seq.n_objects);
        total_loss = Some(match total_loss {
            Some(acc) => acc + loss,
            None => loss,
        });
        sim_history.push(sim);
        n_transitions += 1;
    }

    let n_transitions = n_transitions as f64;
    total_loss.map(|acc| {
        let mean_loss = acc.div_scalar(n_transitions);
        if sim_history.len() >= 2 {
            let smoothness = temporal_smoothness_loss(&sim_history);
            mean_loss + smoothness.mul_scalar(SMOOTHNESS_WEIGHT)
        } else {
            mean_loss
        }
    })
}

/// One training step over a single sequence: direct port of `_train_step_sa`
/// (`temporal_training.py:584-627`). Unlike [`train_step_pt`], this does
/// **not** skip degenerate frames (the reference's SA branch has no such
/// guard) and chains `prev_slots` across the whole sequence via
/// [`TemporalSlotAttentionMOT::process_frame`].
///
/// Returns `None` if every transition's matchable block was empty (no
/// gradient to take).
fn train_step_sa<B: AutodiffBackend>(
    model: &TemporalSlotAttentionMOT<B>,
    seq: &SequenceData,
    device: &B::Device,
    seed: &mut Seed,
) -> Option<Tensor<B, 1>> {
    let mut total_loss: Option<Tensor<B, 1>> = None;
    let mut sim_history: Vec<Tensor<B, 2>> = Vec::new();
    let mut n_transitions = 0usize;
    let mut prev_slots: Option<Tensor<B, 3>> = None;

    for t in 0..seq.n_frames {
        let dets = seq.frame_tensor::<B>(t, device);
        let slots = model
            .process_frame(dets, prev_slots.clone(), seed)
            .expect("frame shapes are constructed to match the tracker's detection_dim");

        if let Some(prev) = prev_slots {
            let sim = model
                .slot_similarity(prev, slots.clone())
                .expect("process_frame always returns [1, k, d] slots");
            let [rows, cols] = sim.dims();
            if rows.min(cols).min(seq.n_objects) > 0 {
                let loss = hungarian_similarity_loss(sim.clone(), seq.n_objects);
                total_loss = Some(match total_loss {
                    Some(acc) => acc + loss,
                    None => loss,
                });
                sim_history.push(sim);
                n_transitions += 1;
            }
        }
        prev_slots = Some(slots);
    }

    let n_transitions = n_transitions as f64;
    total_loss.map(|acc| {
        let mean_loss = acc.div_scalar(n_transitions);
        if sim_history.len() >= 2 {
            let smoothness = temporal_smoothness_loss(&sim_history);
            mean_loss + smoothness.mul_scalar(SMOOTHNESS_WEIGHT)
        } else {
            mean_loss
        }
    })
}

/// Evaluate `model` on `data`: mean loss (same formula as training, for
/// reporting), mean `identity_preservation`, mean identity switches, and
/// mean track-fragmentation rate. Direct port of `evaluate`
/// (`temporal_training.py:685-747`), restricted to the PhaseTracker branch.
pub fn evaluate_phase_tracker<B: Backend>(
    model: &PhaseTracker<B>,
    data: &[SequenceData],
    device: &B::Device,
) -> ValMetrics {
    if data.is_empty() {
        return ValMetrics::default();
    }

    let mut total_loss = 0.0;
    let mut total_ip = 0.0;
    let mut total_idsw = 0.0;
    let mut total_tfr = 0.0;

    for seq in data {
        let frames = seq.frame_tensors::<B>(device);
        let result = model
            .track_sequence(frames)
            .expect("sequence frames are constructed to match the tracker's detection_dim");
        total_ip += result.identity_preservation;
        total_idsw += identity_switches(&result.identity_matches, seq.n_objects) as f64;
        total_tfr += track_fragmentation_rate(&result.identity_matches, seq.n_objects);

        let mut loss_sum = 0.0;
        let mut n_trans = 0usize;
        for t in 1..seq.n_frames {
            let (Some(dets_prev), Some(dets_curr)) = (
                non_degenerate_frame::<B>(seq, t - 1, device),
                non_degenerate_frame::<B>(seq, t, device),
            ) else {
                continue;
            };
            let (_matches, sim) = model
                .forward(dets_prev, dets_curr)
                .expect("shapes are constructed to match the tracker's detection_dim");
            let loss = hungarian_similarity_loss(sim, seq.n_objects);
            loss_sum += loss.into_data().to_vec::<f64>().unwrap()[0];
            n_trans += 1;
        }
        total_loss += loss_sum / n_trans.max(1) as f64;
    }

    let n = data.len() as f64;
    ValMetrics {
        loss: total_loss / n,
        ip: total_ip / n,
        idsw: total_idsw / n,
        tfr: total_tfr / n,
    }
}

/// Evaluate `model` on `data` — the [`TemporalSlotAttentionMOT`] counterpart
/// of [`evaluate_phase_tracker`]. Direct port of `evaluate`
/// (`temporal_training.py:685-747`), SA branch: the reporting-loss loop
/// re-runs [`TemporalSlotAttentionMOT::process_frame`] on each
/// `(t-1, t)` pair independently (`prev_slots=None` each time), *not*
/// chained across the sequence — matching the reference's `:730-736`
/// exactly (a deliberate difference from `train_step_sa`'s chained
/// training-time slots, already present in the reference).
pub fn evaluate_temporal_slot_attention_mot<B: Backend>(
    model: &TemporalSlotAttentionMOT<B>,
    data: &[SequenceData],
    device: &B::Device,
    seed: &mut Seed,
) -> ValMetrics {
    if data.is_empty() {
        return ValMetrics::default();
    }

    let mut total_loss = 0.0;
    let mut total_ip = 0.0;
    let mut total_idsw = 0.0;
    let mut total_tfr = 0.0;

    for seq in data {
        let frames = seq.frame_tensors::<B>(device);
        let (_history, identity_matches, ip, _sims) = model
            .track_sequence(frames, seed)
            .expect("sequence frames are constructed to match the tracker's detection_dim");
        total_ip += ip;
        total_idsw += identity_switches(&identity_matches, seq.n_objects) as f64;
        total_tfr += track_fragmentation_rate(&identity_matches, seq.n_objects);

        let mut loss_sum = 0.0;
        let mut n_trans = 0usize;
        for t in 1..seq.n_frames {
            let (Some(dets_prev), Some(dets_curr)) = (
                non_degenerate_frame::<B>(seq, t - 1, device),
                non_degenerate_frame::<B>(seq, t, device),
            ) else {
                continue;
            };
            let prev_slots_eval = model
                .process_frame(dets_prev, None, seed)
                .expect("shapes are constructed to match the tracker's detection_dim");
            let curr_slots_eval = model
                .process_frame(dets_curr, Some(prev_slots_eval.clone()), seed)
                .expect("shapes are constructed to match the tracker's detection_dim");
            let sim = model
                .slot_similarity(prev_slots_eval, curr_slots_eval)
                .expect("process_frame always returns [1, k, d] slots");
            let loss = hungarian_similarity_loss(sim, seq.n_objects);
            loss_sum += loss.into_data().to_vec::<f64>().unwrap()[0];
            n_trans += 1;
        }
        total_loss += loss_sum / n_trans.max(1) as f64;
    }

    let n = data.len() as f64;
    ValMetrics {
        loss: total_loss / n,
        ip: total_ip / n,
        idsw: total_idsw / n,
        tfr: total_tfr / n,
    }
}

/// Mean Kuramoto order parameter of `model`'s dynamics, evolved one step
/// from a uniform-random initial phase — the phase-coherence component of
/// [`TrainingSnapshot`]. Direct port of the PT branch of `_capture_snapshot`
/// (`temporal_training.py:763-777`); returns `0.0` on any failure (matching
/// the reference's `except Exception: snap.phase_coherence = 0.0`).
fn capture_phase_coherence<B: Backend>(
    model: &PhaseTracker<B>,
    device: &B::Device,
    seed: &mut Seed,
) -> f64 {
    let n_osc = model.n_osc();
    let test_phase = seeded_uniform::<B, 2>([1, n_osc], 0.0, std::f64::consts::TAU, device, seed);
    let test_amp = Tensor::<B, 2>::ones([1, n_osc], device);
    match model.evolve(test_phase, test_amp) {
        Ok((evolved_phase, _)) => {
            let phases = to_f64_vec(evolved_phase);
            kuramoto_order_parameter(&phases).unwrap_or(0.0)
        }
        Err(_) => 0.0,
    }
}

/// Early-stopping bookkeeping shared by [`train_phase_tracker`] and
/// [`train_temporal_slot_attention_mot`] — the smoothed-validation-loss
/// patience logic common to `train`'s loop body (`temporal_training.py:826-844`),
/// factored once per Coding Standards §1.1 rather than duplicated across
/// both trainer functions.
struct EarlyStopState {
    best_val_loss: f64,
    best_epoch: usize,
    patience_counter: usize,
    val_loss_history: Vec<f64>,
}

impl EarlyStopState {
    fn new() -> Self {
        Self {
            best_val_loss: f64::INFINITY,
            best_epoch: 0,
            patience_counter: 0,
            val_loss_history: Vec::new(),
        }
    }

    /// Record `val_loss` for `epoch`; returns `true` if this epoch is a new
    /// best (i.e. the caller should snapshot the model as the restore
    /// point).
    fn update(&mut self, epoch: usize, val_loss: f64, smoothing_window: usize) -> bool {
        self.val_loss_history.push(val_loss);
        let smoothed = if self.val_loss_history.len() >= smoothing_window {
            let start = self.val_loss_history.len() - smoothing_window;
            self.val_loss_history[start..].iter().sum::<f64>() / smoothing_window as f64
        } else {
            val_loss
        };

        if smoothed < self.best_val_loss - 1e-6 {
            self.best_val_loss = smoothed;
            self.best_epoch = epoch;
            self.patience_counter = 0;
            true
        } else {
            self.patience_counter += 1;
            false
        }
    }

    fn should_stop(&self, patience: usize) -> bool {
        self.patience_counter >= patience
    }
}

/// Train `model` on `train_data`, validating on `val_data`, per `config`.
///
/// Returns the best-validation-loss model (early-stopping restore point)
/// together with the full training history. `seed` drives
/// [`TrainingSnapshot::phase_coherence`]'s random probe phase (see
/// `capture_phase_coherence`) — the only stochastic entry point in this
/// otherwise-deterministic training loop.
///
/// # Errors
///
/// Returns an error if `config` fails [`TemporalTrainerConfig::validate`].
pub fn train_phase_tracker<B: AutodiffBackend>(
    mut model: PhaseTracker<B>,
    config: &TemporalTrainerConfig,
    train_data: &[SequenceData],
    val_data: &[SequenceData],
    device: &B::Device,
    seed: &mut Seed,
) -> Result<(PhaseTracker<B>, TrainingResult), TrainError> {
    config.validate()?;

    let mut optimizer = AdamConfig::new()
        .with_grad_clipping(Some(GradientClippingConfig::Norm(config.grad_clip as f32)))
        .init::<B, PhaseTracker<B>>();

    let mut result = TrainingResult::default();
    let mut best_model: Option<PhaseTracker<B>> = None;
    let mut early_stop = EarlyStopState::new();
    let t0 = std::time::Instant::now();

    for epoch in 0..config.max_epochs {
        let lr = config.lr_at(epoch);

        let mut total_train_loss = 0.0;
        let mut last_grad_norm = 0.0;
        for seq in train_data {
            if let Some(loss_tensor) = train_step_pt(&model, seq, device) {
                let loss_val = loss_tensor.clone().into_data().to_vec::<f64>().unwrap()[0];
                let grads = loss_tensor.backward();
                let grads_params = GradientsParams::from_grads(grads, &model);
                last_grad_norm = compute_gradient_norm(&model, &grads_params);
                model = optimizer.step(lr, model, grads_params);
                total_train_loss += loss_val;
            }
        }
        let train_loss = total_train_loss / train_data.len().max(1) as f64;
        result.train_losses.push(train_loss);

        let inner_model = model.valid();
        let val_metrics = evaluate_phase_tracker(&inner_model, val_data, device);
        result.val_losses.push(val_metrics.loss);
        result.val_ips.push(val_metrics.ip);

        if config.snapshot_epochs.contains(&epoch) {
            result.snapshots.push(TrainingSnapshot {
                epoch,
                train_loss,
                val_loss: val_metrics.loss,
                val_ip: val_metrics.ip,
                val_idsw: val_metrics.idsw as i64,
                gradient_norm: last_grad_norm,
                param_norm: compute_param_norm(&model),
                phase_coherence: capture_phase_coherence(&inner_model, device, seed),
                slot_entropy: 0.0,
            });
        }

        let is_new_best = early_stop.update(epoch, val_metrics.loss, config.smoothing_window);
        if is_new_best {
            best_model = Some(model.clone());
        }
        if early_stop.should_stop(config.patience) {
            break;
        }
    }

    if let Some(best) = best_model {
        model = best;
    }

    let inner_model = model.valid();
    let final_val = evaluate_phase_tracker(&inner_model, val_data, device);

    result.final_train_loss = result.train_losses.last().copied().unwrap_or(0.0);
    result.final_val_loss = final_val.loss;
    result.final_val_ip = final_val.ip;
    result.best_val_loss = early_stop.best_val_loss;
    result.best_epoch = early_stop.best_epoch;
    result.total_epochs = result.train_losses.len();
    result.wall_time_s = t0.elapsed().as_secs_f64();

    let last_epoch = result.total_epochs.saturating_sub(1);
    if result.total_epochs > 0 && !config.snapshot_epochs.contains(&last_epoch) {
        result.snapshots.push(TrainingSnapshot {
            epoch: last_epoch,
            train_loss: result.final_train_loss,
            val_loss: final_val.loss,
            val_ip: final_val.ip,
            val_idsw: final_val.idsw as i64,
            gradient_norm: 0.0,
            param_norm: compute_param_norm(&model),
            phase_coherence: capture_phase_coherence(&inner_model, device, seed),
            slot_entropy: 0.0,
        });
    }

    Ok((model, result))
}

/// Train `model` on `train_data`, validating on `val_data`, per `config` —
/// the [`TemporalSlotAttentionMOT`] counterpart of [`train_phase_tracker`].
/// `seed` drives every stochastic entry point: the SA tracker's per-call
/// slot-initialization noise ([`crate::slot_attention`]'s module docs) in
/// every `process_frame`/`forward`/`track_sequence` call this function
/// makes.
///
/// # Errors
///
/// Returns an error if `config` fails [`TemporalTrainerConfig::validate`].
pub fn train_temporal_slot_attention_mot<B: AutodiffBackend>(
    mut model: TemporalSlotAttentionMOT<B>,
    config: &TemporalTrainerConfig,
    train_data: &[SequenceData],
    val_data: &[SequenceData],
    device: &B::Device,
    seed: &mut Seed,
) -> Result<(TemporalSlotAttentionMOT<B>, TrainingResult), TrainError> {
    config.validate()?;

    let mut optimizer = AdamConfig::new()
        .with_grad_clipping(Some(GradientClippingConfig::Norm(config.grad_clip as f32)))
        .init::<B, TemporalSlotAttentionMOT<B>>();

    let mut result = TrainingResult::default();
    let mut best_model: Option<TemporalSlotAttentionMOT<B>> = None;
    let mut early_stop = EarlyStopState::new();
    let t0 = std::time::Instant::now();

    for epoch in 0..config.max_epochs {
        let lr = config.lr_at(epoch);

        let mut total_train_loss = 0.0;
        let mut last_grad_norm = 0.0;
        for seq in train_data {
            if let Some(loss_tensor) = train_step_sa(&model, seq, device, seed) {
                let loss_val = loss_tensor.clone().into_data().to_vec::<f64>().unwrap()[0];
                let grads = loss_tensor.backward();
                let grads_params = GradientsParams::from_grads(grads, &model);
                last_grad_norm = compute_gradient_norm(&model, &grads_params);
                model = optimizer.step(lr, model, grads_params);
                total_train_loss += loss_val;
            }
        }
        let train_loss = total_train_loss / train_data.len().max(1) as f64;
        result.train_losses.push(train_loss);

        let inner_model = model.valid();
        let val_metrics =
            evaluate_temporal_slot_attention_mot(&inner_model, val_data, device, seed);
        result.val_losses.push(val_metrics.loss);
        result.val_ips.push(val_metrics.ip);

        if config.snapshot_epochs.contains(&epoch) {
            result.snapshots.push(TrainingSnapshot {
                epoch,
                train_loss,
                val_loss: val_metrics.loss,
                val_ip: val_metrics.ip,
                val_idsw: val_metrics.idsw as i64,
                gradient_norm: last_grad_norm,
                param_norm: compute_param_norm(&model),
                phase_coherence: 0.0,
                slot_entropy: 0.0,
            });
        }

        let is_new_best = early_stop.update(epoch, val_metrics.loss, config.smoothing_window);
        if is_new_best {
            best_model = Some(model.clone());
        }
        if early_stop.should_stop(config.patience) {
            break;
        }
    }

    if let Some(best) = best_model {
        model = best;
    }

    let inner_model = model.valid();
    let final_val = evaluate_temporal_slot_attention_mot(&inner_model, val_data, device, seed);

    result.final_train_loss = result.train_losses.last().copied().unwrap_or(0.0);
    result.final_val_loss = final_val.loss;
    result.final_val_ip = final_val.ip;
    result.best_val_loss = early_stop.best_val_loss;
    result.best_epoch = early_stop.best_epoch;
    result.total_epochs = result.train_losses.len();
    result.wall_time_s = t0.elapsed().as_secs_f64();

    let last_epoch = result.total_epochs.saturating_sub(1);
    if result.total_epochs > 0 && !config.snapshot_epochs.contains(&last_epoch) {
        result.snapshots.push(TrainingSnapshot {
            epoch: last_epoch,
            train_loss: result.final_train_loss,
            val_loss: final_val.loss,
            val_ip: final_val.ip,
            val_idsw: final_val.idsw as i64,
            gradient_norm: 0.0,
            param_norm: compute_param_norm(&model),
            phase_coherence: 0.0,
            slot_entropy: 0.0,
        });
    }

    Ok((model, result))
}

/// Aggregated results across multiple training seeds.
///
/// Direct port of `MultiSeedResult` (`temporal_training.py:877-901`), minus
/// `mean_idsw`/`mean_tfr`: the reference declares those two fields but
/// `train_multi_seed`'s actual body (`:926-947`) never computes or assigns
/// them (a reference-side dead-field gap, the same class as
/// [`TrainingSnapshot::slot_entropy`]) — omitted here rather than always
/// reporting a fabricated `0.0` for fields the reference itself never
/// populates.
#[derive(Clone, Debug, Default, PartialEq)]
pub struct MultiSeedResult {
    /// Name of the model being evaluated (for reporting).
    pub model_name: String,
    /// Seeds used for each independent run.
    pub seeds: Vec<u64>,
    /// Per-seed training result, in `seeds` order.
    pub per_seed: Vec<TrainingResult>,
    /// Mean final validation IP across seeds.
    pub mean_ip: f64,
    /// Sample standard deviation (`ddof=1`) of final validation IP across
    /// seeds.
    pub std_ip: f64,
    /// Mean epochs-to-convergence across seeds.
    pub mean_epochs: f64,
    /// Mean wall-clock training time across seeds, in seconds.
    pub mean_wall_time: f64,
}

/// Train a model across multiple seeds for statistical reliability.
///
/// Direct port of `train_multi_seed` (`temporal_training.py:904-948`).
/// **Structural deviation**: the reference calls `torch.manual_seed(seed)`
/// then an argument-less `model_factory()`, relying on that just-set global
/// RNG state to make construction reproducible; this project threads
/// randomness explicitly (Project Plan §4 rule 3), so `model_factory` takes
/// a `&mut Seed` directly — the same "explicit `Seed` in place of an
/// implicit global" pattern already established by every other stochastic
/// entry point in this crate.
///
/// `train_fn` is [`train_phase_tracker`] or
/// [`train_temporal_slot_attention_mot`] (or any function with a matching
/// signature), letting this stay one generic implementation shared by both
/// trackers rather than two near-duplicate aggregation loops.
///
/// # Errors
///
/// Propagates the first error `train_fn` returns for any seed.
#[allow(clippy::too_many_arguments)]
pub fn train_multi_seed<B, M>(
    model_name: &str,
    mut model_factory: impl FnMut(&mut Seed) -> M,
    config: &TemporalTrainerConfig,
    train_data: &[SequenceData],
    val_data: &[SequenceData],
    seeds: &[u64],
    device: &B::Device,
    mut train_fn: impl FnMut(
        M,
        &TemporalTrainerConfig,
        &[SequenceData],
        &[SequenceData],
        &B::Device,
        &mut Seed,
    ) -> Result<(M, TrainingResult), TrainError>,
) -> Result<MultiSeedResult, TrainError>
where
    B: AutodiffBackend,
{
    let mut result = MultiSeedResult {
        model_name: model_name.to_string(),
        seeds: seeds.to_vec(),
        ..Default::default()
    };

    for &seed_val in seeds {
        let mut seed = Seed::new(seed_val as u128, 0);
        let model = model_factory(&mut seed);
        let (_trained, tr) = train_fn(model, config, train_data, val_data, device, &mut seed)?;
        result.per_seed.push(tr);
    }

    let ips: Vec<f64> = result.per_seed.iter().map(|r| r.final_val_ip).collect();
    result.mean_ip = ips.iter().sum::<f64>() / ips.len().max(1) as f64;
    result.std_ip = if ips.len() >= 2 {
        let mean = result.mean_ip;
        (ips.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / (ips.len() - 1) as f64).sqrt()
    } else {
        0.0
    };

    let epochs: Vec<f64> = result
        .per_seed
        .iter()
        .map(|r| r.total_epochs as f64)
        .collect();
    result.mean_epochs = epochs.iter().sum::<f64>() / epochs.len().max(1) as f64;

    let times: Vec<f64> = result.per_seed.iter().map(|r| r.wall_time_s).collect();
    result.mean_wall_time = times.iter().sum::<f64>() / times.len().max(1) as f64;

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dataset::{generate_dataset, TemporalClevrNConfig};
    use crate::phase_tracker::PhaseTrackerConfig;
    use crate::slot_attention::TemporalSlotAttentionMOTConfig;
    use burn::backend::{Autodiff, NdArray};

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestAutodiffBackend as Backend>::Device {
        Default::default()
    }

    // --- Config validation ---

    #[test]
    fn default_config_is_valid() {
        assert!(TemporalTrainerConfig::default().validate().is_ok());
    }

    #[test]
    fn default_config_matches_reference_snapshot_epochs() {
        assert_eq!(
            TemporalTrainerConfig::default().snapshot_epochs,
            vec![0, 10, 25, 50, 100]
        );
    }

    #[test]
    fn non_positive_lr_rejected() {
        let cfg = TemporalTrainerConfig {
            lr: 0.0,
            ..TemporalTrainerConfig::default()
        };
        assert!(matches!(
            cfg.validate().unwrap_err(),
            TrainError::InvalidLearningRate { .. }
        ));
    }

    #[test]
    fn zero_max_epochs_rejected() {
        let cfg = TemporalTrainerConfig {
            max_epochs: 0,
            ..TemporalTrainerConfig::default()
        };
        assert!(matches!(
            cfg.validate().unwrap_err(),
            TrainError::InvalidStepCount {
                name: "max_epochs",
                ..
            }
        ));
    }

    #[test]
    fn negative_grad_clip_rejected() {
        let cfg = TemporalTrainerConfig {
            grad_clip: -1.0,
            ..TemporalTrainerConfig::default()
        };
        assert!(matches!(
            cfg.validate().unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "grad_clip",
                ..
            }
        ));
    }

    // --- LR schedule ---

    #[test]
    fn lr_schedule_ramps_up_during_warmup() {
        let cfg = TemporalTrainerConfig {
            lr: 1.0,
            warmup_epochs: 4,
            max_epochs: 20,
            ..TemporalTrainerConfig::default()
        };
        assert!((cfg.lr_at(0) - 0.25).abs() < 1e-9);
        assert!((cfg.lr_at(1) - 0.5).abs() < 1e-9);
        assert!((cfg.lr_at(3) - 1.0).abs() < 1e-9);
    }

    #[test]
    fn lr_schedule_decays_after_warmup() {
        let cfg = TemporalTrainerConfig {
            lr: 1.0,
            warmup_epochs: 0,
            max_epochs: 10,
            ..TemporalTrainerConfig::default()
        };
        let start = cfg.lr_at(0);
        let mid = cfg.lr_at(5);
        let end = cfg.lr_at(9);
        assert!(start > mid && mid > end, "{start} {mid} {end}");
        assert!(end >= cfg.lr * 0.01 - 1e-9);
    }

    // --- count_parameters / compute_param_norm ---

    #[test]
    fn count_parameters_totals_are_consistent() {
        let _guard = crate::support::autodiff_test_guard();
        let mut seed = Seed::new(1, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let counts = count_parameters(&model);
        assert_eq!(counts.total, counts.trainable + counts.frozen);
        assert!(counts.total > 0);
        // No complex-valued parameters in this port (see ParameterCounts docs).
        assert_eq!(counts.complex_adjusted, counts.total);
    }

    #[test]
    fn compute_param_norm_is_positive_and_finite() {
        let _guard = crate::support::autodiff_test_guard();
        let mut seed = Seed::new(2, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let norm = compute_param_norm(&model);
        assert!(norm.is_finite());
        assert!(norm > 0.0);
    }

    #[test]
    fn count_parameters_matches_between_pt_and_sa_shapes() {
        let _guard = crate::support::autodiff_test_guard();
        let mut seed = Seed::new(3, 0);
        let pt = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let mut seed2 = Seed::new(4, 0);
        let sa = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed2);
        assert!(count_parameters(&pt).total > 0);
        assert!(count_parameters(&sa).total > 0);
    }

    // --- End-to-end smoke: PhaseTracker ---

    fn small_dataset(n_seqs: usize, base_seed: u128) -> Vec<SequenceData> {
        let cfg = TemporalClevrNConfig::new(3, 6).unwrap();
        generate_dataset(n_seqs, &cfg, base_seed)
    }

    #[test]
    fn phase_tracker_training_runs_and_produces_valid_metrics() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let mut seed = Seed::new(1, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);

        let train_data = small_dataset(4, 1000);
        let val_data = small_dataset(2, 9000);

        let cfg = TemporalTrainerConfig {
            max_epochs: 3,
            patience: 3,
            warmup_epochs: 1,
            smoothing_window: 2,
            snapshot_epochs: vec![0, 2],
            ..TemporalTrainerConfig::default()
        };

        let mut train_seed = Seed::new(500, 0);
        let (_trained, result) =
            train_phase_tracker(model, &cfg, &train_data, &val_data, &dev, &mut train_seed)
                .unwrap();

        assert!(result.total_epochs >= 1);
        assert_eq!(result.train_losses.len(), result.total_epochs);
        assert_eq!(result.val_losses.len(), result.total_epochs);
        assert!((0.0..=1.0).contains(&result.final_val_ip));
        assert!(result.final_train_loss.is_finite());
        assert!(result.final_val_loss.is_finite());
        assert!(result.wall_time_s >= 0.0);
        assert!(!result.snapshots.is_empty());
        assert_eq!(result.snapshots[0].epoch, 0);
        for snap in &result.snapshots {
            assert!(snap.param_norm.is_finite() && snap.param_norm > 0.0);
            assert!(snap.gradient_norm.is_finite());
            assert!((-1.0 - 1e-6..=1.0 + 1e-6).contains(&snap.phase_coherence));
        }
    }

    #[test]
    fn invalid_config_is_rejected_before_training() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let mut seed = Seed::new(2, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);
        let cfg = TemporalTrainerConfig {
            lr: -1.0,
            ..TemporalTrainerConfig::default()
        };
        let mut train_seed = Seed::new(1, 0);
        let err = train_phase_tracker(model, &cfg, &[], &[], &dev, &mut train_seed).unwrap_err();
        assert!(matches!(err, TrainError::InvalidLearningRate { .. }));
    }

    #[test]
    fn evaluate_phase_tracker_on_empty_dataset_returns_default_metrics() {
        let dev: <TestBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(3, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&dev, &mut seed);
        let metrics = evaluate_phase_tracker(&model, &[], &dev);
        assert_eq!(metrics, ValMetrics::default());
    }

    #[test]
    fn evaluate_phase_tracker_reports_idsw_and_tfr() {
        let dev: <TestBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(4, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&dev, &mut seed);
        let data = small_dataset(2, 42);
        let metrics = evaluate_phase_tracker(&model, &data, &dev);
        assert!(metrics.idsw >= 0.0);
        assert!(metrics.tfr >= 1.0 - 1e-9);
    }

    // --- End-to-end smoke: TemporalSlotAttentionMOT ---

    #[test]
    fn slot_attention_training_runs_and_produces_valid_metrics() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let mut seed = Seed::new(5, 0);
        let model = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);

        let train_data = small_dataset(3, 2000);
        let val_data = small_dataset(2, 8000);

        let cfg = TemporalTrainerConfig {
            max_epochs: 3,
            patience: 3,
            warmup_epochs: 1,
            smoothing_window: 2,
            snapshot_epochs: vec![0],
            ..TemporalTrainerConfig::default()
        };

        let mut train_seed = Seed::new(600, 0);
        let (_trained, result) = train_temporal_slot_attention_mot(
            model,
            &cfg,
            &train_data,
            &val_data,
            &dev,
            &mut train_seed,
        )
        .unwrap();

        assert!(result.total_epochs >= 1);
        assert!((0.0..=1.0).contains(&result.final_val_ip));
        assert!(result.final_train_loss.is_finite());
        assert!(!result.snapshots.is_empty());
        for snap in &result.snapshots {
            // Reference gap: SA branch never computes phase_coherence/slot_entropy.
            assert_eq!(snap.phase_coherence, 0.0);
            assert_eq!(snap.slot_entropy, 0.0);
        }
    }

    #[test]
    fn evaluate_slot_attention_on_empty_dataset_returns_default_metrics() {
        let dev: <TestBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(6, 0);
        let model = TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3)
            .unwrap()
            .init::<TestBackend>(&dev, &mut seed);
        let mut eval_seed = Seed::new(7, 0);
        let metrics = evaluate_temporal_slot_attention_mot(&model, &[], &dev, &mut eval_seed);
        assert_eq!(metrics, ValMetrics::default());
    }

    // --- train_multi_seed ---

    #[test]
    fn train_multi_seed_aggregates_across_seeds() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let train_data = small_dataset(3, 3000);
        let val_data = small_dataset(2, 7000);
        let cfg = TemporalTrainerConfig {
            max_epochs: 2,
            patience: 2,
            warmup_epochs: 1,
            smoothing_window: 2,
            snapshot_epochs: vec![],
            ..TemporalTrainerConfig::default()
        };

        let result = train_multi_seed::<TestAutodiffBackend, PhaseTracker<TestAutodiffBackend>>(
            "phase_tracker",
            |seed| {
                PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
                    .unwrap()
                    .init(&dev, seed)
            },
            &cfg,
            &train_data,
            &val_data,
            &[11, 22, 33],
            &dev,
            train_phase_tracker,
        )
        .unwrap();

        assert_eq!(result.model_name, "phase_tracker");
        assert_eq!(result.seeds, vec![11, 22, 33]);
        assert_eq!(result.per_seed.len(), 3);
        assert!((0.0..=1.0).contains(&result.mean_ip));
        assert!(result.std_ip >= 0.0);
        assert!(result.mean_epochs > 0.0);
        assert!(result.mean_wall_time >= 0.0);
    }

    #[test]
    fn train_multi_seed_propagates_errors() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let cfg = TemporalTrainerConfig {
            lr: -1.0,
            ..TemporalTrainerConfig::default()
        };
        let err = train_multi_seed::<TestAutodiffBackend, PhaseTracker<TestAutodiffBackend>>(
            "phase_tracker",
            |seed| {
                PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
                    .unwrap()
                    .init(&dev, seed)
            },
            &cfg,
            &[],
            &[],
            &[1],
            &dev,
            train_phase_tracker,
        )
        .unwrap_err();
        assert!(matches!(err, TrainError::InvalidLearningRate { .. }));
    }

    #[test]
    fn train_multi_seed_single_seed_has_zero_std() {
        let _guard = crate::support::autodiff_test_guard();
        let dev = device();
        let train_data = small_dataset(2, 4000);
        let val_data = small_dataset(1, 9500);
        let cfg = TemporalTrainerConfig {
            max_epochs: 1,
            patience: 1,
            warmup_epochs: 0,
            smoothing_window: 1,
            snapshot_epochs: vec![],
            ..TemporalTrainerConfig::default()
        };
        let result = train_multi_seed::<TestAutodiffBackend, PhaseTracker<TestAutodiffBackend>>(
            "pt",
            |seed| {
                PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
                    .unwrap()
                    .init(&dev, seed)
            },
            &cfg,
            &train_data,
            &val_data,
            &[1],
            &dev,
            train_phase_tracker,
        )
        .unwrap();
        assert_eq!(result.std_ip, 0.0);
    }
}

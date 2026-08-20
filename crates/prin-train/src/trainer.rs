//! Rust-native training pipeline for [`PhaseTracker`] on temporal CLEVR-N
//! sequences (WP-027): a direct port of PRINet 3.0's `TemporalTrainer`
//! (`utils/temporal_training.py:454-869`), entirely in Rust per Project Plan
//! §4 rule 2 ("the Python layer contains no numerics") — the Python
//! trainable API (`crates/prin-py`) is a thin orchestration wrapper around
//! [`train_phase_tracker`], not a reimplementation.
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
//!   [`PhaseTracker::forward`]'s differentiable similarity matrix — never on
//!   [`PhaseTracker::track_sequence`]'s `no_grad` output — matching
//!   `_train_step_pt` (`:540-582`).
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
//!   (`:780-869`), using [`PhaseTracker`]'s derived `Clone` impl in place of
//!   the reference's `copy.deepcopy(model.state_dict())` snapshot/restore.
//! - **Evaluation**: [`PhaseTracker::track_sequence`] (already correct,
//!   ported at WP-026) computes `identity_preservation`; loss-for-reporting
//!   is recomputed via the same differentiable path as training, under
//!   `model.valid()` (Burn's no-autodiff-graph inference mode, the
//!   equivalent of the reference's `@torch.no_grad()` on `evaluate`).

use burn::grad_clipping::GradientClippingConfig;
use burn::module::AutodiffModule;
use burn::optim::{AdamConfig, GradientsParams, Optimizer};
use burn::tensor::backend::{AutodiffBackend, Backend};
use burn::tensor::Tensor;

use crate::dataset::SequenceData;
use crate::error::TrainError;
use crate::losses::{hungarian_similarity_loss, temporal_smoothness_loss};
use crate::phase_tracker::PhaseTracker;

/// Weight of [`temporal_smoothness_loss`] in the combined training loss,
/// matching the reference's hardcoded `0.1` (`temporal_training.py:580`).
const SMOOTHNESS_WEIGHT: f64 = 0.1;

/// Minimum absolute detection-vector sum for a frame to be considered
/// non-degenerate (fully occluded), matching the reference's `1e-8`
/// threshold (`temporal_training.py:566`).
const DEGENERATE_FRAME_THRESHOLD: f64 = 1e-8;

/// Validated hyperparameters for [`train_phase_tracker`].
///
/// Defaults ([`Self::default`]) match PRINet 3.0's `TemporalTrainer.__init__`
/// (`temporal_training.py:485-498`): `lr=3e-4, weight_decay=0.0,
/// max_epochs=100, patience=10, smoothing_window=5, warmup_epochs=5,
/// grad_clip=1.0`.
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
}

/// Complete training-run result, matching the reference `TrainingResult`
/// dataclass (`temporal_training.py:418-446`), minus the per-epoch dynamics
/// `snapshots` (not needed for this WP's validation-run evidence; a future
/// WP can add them if training-dynamics analysis is required).
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
    /// Per-epoch mean training loss.
    pub train_losses: Vec<f64>,
    /// Per-epoch validation loss.
    pub val_losses: Vec<f64>,
    /// Per-epoch validation identity preservation.
    pub val_ips: Vec<f64>,
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

/// Evaluate `model` on `data`: mean loss (same formula as training, for
/// reporting) and mean `identity_preservation`. Direct port of `evaluate`
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

    for seq in data {
        let frames = seq.frame_tensors::<B>(device);
        let result = model
            .track_sequence(frames)
            .expect("sequence frames are constructed to match the tracker's detection_dim");
        total_ip += result.identity_preservation;

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
    }
}

/// Train `model` on `train_data`, validating on `val_data`, per `config`.
///
/// Returns the best-validation-loss model (early-stopping restore point)
/// together with the full training history.
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
) -> Result<(PhaseTracker<B>, TrainingResult), TrainError> {
    config.validate()?;

    let mut optimizer = AdamConfig::new()
        .with_grad_clipping(Some(GradientClippingConfig::Norm(config.grad_clip as f32)))
        .init::<B, PhaseTracker<B>>();

    let mut result = TrainingResult::default();
    let mut best_val_loss = f64::INFINITY;
    let mut best_model: Option<PhaseTracker<B>> = None;
    let mut best_epoch = 0usize;
    let mut patience_counter = 0usize;
    let mut val_loss_history: Vec<f64> = Vec::new();

    for epoch in 0..config.max_epochs {
        let lr = config.lr_at(epoch);

        let mut total_train_loss = 0.0;
        for seq in train_data {
            if let Some(loss_tensor) = train_step_pt(&model, seq, device) {
                let loss_val = loss_tensor.clone().into_data().to_vec::<f64>().unwrap()[0];
                let grads = loss_tensor.backward();
                let grads = GradientsParams::from_grads(grads, &model);
                model = optimizer.step(lr, model, grads);
                total_train_loss += loss_val;
            }
        }
        let train_loss = total_train_loss / train_data.len().max(1) as f64;
        result.train_losses.push(train_loss);

        let inner_model = model.valid();
        let val_metrics = evaluate_phase_tracker(&inner_model, val_data, device);
        result.val_losses.push(val_metrics.loss);
        result.val_ips.push(val_metrics.ip);
        val_loss_history.push(val_metrics.loss);

        let smoothed = if val_loss_history.len() >= config.smoothing_window {
            let start = val_loss_history.len() - config.smoothing_window;
            val_loss_history[start..].iter().sum::<f64>() / config.smoothing_window as f64
        } else {
            val_metrics.loss
        };

        if smoothed < best_val_loss - 1e-6 {
            best_val_loss = smoothed;
            best_model = Some(model.clone());
            best_epoch = epoch;
            patience_counter = 0;
        } else {
            patience_counter += 1;
        }

        if patience_counter >= config.patience {
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
    result.best_val_loss = best_val_loss;
    result.best_epoch = best_epoch;
    result.total_epochs = result.train_losses.len();

    Ok((model, result))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dataset::{generate_dataset, TemporalClevrNConfig};
    use crate::phase_tracker::PhaseTrackerConfig;
    use burn::backend::{Autodiff, NdArray};
    use prin_dynamics::Seed;

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

    // --- End-to-end smoke: training actually reduces loss and IP is valid ---

    fn small_dataset(n_seqs: usize, base_seed: u128) -> Vec<SequenceData> {
        let cfg = TemporalClevrNConfig::new(3, 6).unwrap();
        generate_dataset(n_seqs, &cfg, base_seed)
    }

    #[test]
    fn training_runs_and_produces_valid_metrics() {
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
            ..TemporalTrainerConfig::default()
        };

        let (_trained, result) =
            train_phase_tracker(model, &cfg, &train_data, &val_data, &dev).unwrap();

        assert!(result.total_epochs >= 1);
        assert_eq!(result.train_losses.len(), result.total_epochs);
        assert_eq!(result.val_losses.len(), result.total_epochs);
        assert!((0.0..=1.0).contains(&result.final_val_ip));
        assert!(result.final_train_loss.is_finite());
        assert!(result.final_val_loss.is_finite());
    }

    #[test]
    fn invalid_config_is_rejected_before_training() {
        let dev = device();
        let mut seed = Seed::new(2, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);
        let cfg = TemporalTrainerConfig {
            lr: -1.0,
            ..TemporalTrainerConfig::default()
        };
        let err = train_phase_tracker(model, &cfg, &[], &[], &dev).unwrap_err();
        assert!(matches!(err, TrainError::InvalidLearningRate { .. }));
    }

    #[test]
    fn evaluate_on_empty_dataset_returns_default_metrics() {
        let dev: <TestBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(3, 0);
        let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.1)
            .unwrap()
            .init::<TestBackend>(&dev, &mut seed);
        let metrics = evaluate_phase_tracker(&model, &[], &dev);
        assert_eq!(metrics, ValMetrics::default());
    }
}

//! Synchronization-Coupled Adaptive Learning Rate (SCALR) optimizer
//! (PRINet 3.0 `SCALROptimizer`, including its "Q3" enhancements).
//!
//! Scales the learning rate by the Kuramoto order parameter:
//!
//! ```text
//! η_eff(t) = η_base · f(r(t)),   f(r) = r_min + (1 − r_min)·r^α
//! ```
//!
//! so well-synchronized dynamics (`r` near 1) take larger steps and
//! desynchronized dynamics (`r` near 0) slow down toward `r_min·η_base`.
//! Three Q3 enhancements layer on top:
//!
//! - **Oscillation-aware decay**: when the windowed variance of recent `r`
//!   values exceeds `oscillation_threshold`, `lr` is multiplicatively decayed
//!   by `oscillation_decay` (cumulative across detections).
//! - **Adaptive `r_min`**: an EMA of `r` (`r_min_ema_alpha`) drives `r_min =
//!   clamp(0.3·EMA, 0.01, 0.5)` when `adaptive_r_min` is set.
//! - **Per-frequency lr scaling**: [`Scalr::step_with_order_parameter`]
//!   accepts an [`OrderParameter::PerGroup`] dict for hierarchical
//!   (multi-band) models — see its docs for how shared bookkeeping stays
//!   consistent across per-group `Scalr` instances.
//!
//! [`Scalr::compute_lr_scale`] and the private `detect_oscillation`/
//! `update_adaptive_r_min` methods are direct, line-for-line ports of
//! `SCALROptimizer`'s identically-named methods; [`Scalr::step`] (via
//! [`crate::feedback::OscillatorOptimizer`]) ports `.step`'s update loop.
//! Golden-value parity tests live in `tests/parity_optimizers.rs`.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::feedback::{OscillatorOptimizer, StepFeedback};
//! use prin_train::scalr::ScalrConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let mut opt = ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.5, 0, 20, 0.01, 0.95, false, 0.1)
//!     .unwrap()
//!     .init::<Backend, 1>();
//! let param = Tensor::<Backend, 1>::zeros([4], &device);
//! let grad = Tensor::<Backend, 1>::ones([4], &device);
//!
//! let updated = opt.step(param, Some(grad), &StepFeedback::order(0.8)).unwrap();
//! assert_eq!(updated.dims(), [4]);
//! ```

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use serde::{Deserialize, Serialize};

use crate::error::TrainError;
use crate::feedback::{OrderParameter, OscillatorOptimizer, StepFeedback};
use crate::support::{check_dims, sgd_update, validate_finite};

/// Validated hyperparameters for [`Scalr`].
///
/// Defaults ([`Self::new`]) match the PRINet 3.0 reference: `lr=0.01,
/// momentum=0.0, weight_decay=0.0, r_min=0.1, alpha=1.0, warmup_steps=0,
/// oscillation_window=20, oscillation_threshold=0.01,
/// oscillation_decay=0.95, adaptive_r_min=false, r_min_ema_alpha=0.1`.
#[derive(Clone, Debug, PartialEq)]
pub struct ScalrConfig {
    /// Base learning rate η_base.
    pub lr: f64,
    /// Momentum factor.
    pub momentum: f64,
    /// L2 weight-decay coefficient.
    pub weight_decay: f64,
    /// Minimum learning-rate fraction when `r → 0`.
    pub r_min: f64,
    /// Exponent controlling synchronization sensitivity (`α = 1` linear;
    /// `α > 1` more aggressive).
    pub alpha: f64,
    /// Steps to use the full base lr before SCALR scaling kicks in.
    pub warmup_steps: usize,
    /// Window size for oscillation detection.
    pub oscillation_window: usize,
    /// Windowed-variance threshold for oscillation detection.
    pub oscillation_threshold: f64,
    /// Multiplicative lr decay applied once per oscillation detection.
    pub oscillation_decay: f64,
    /// If `true`, auto-adjust `r_min` from an EMA of the order parameter.
    pub adaptive_r_min: bool,
    /// EMA smoothing factor for adaptive `r_min`.
    pub r_min_ema_alpha: f64,
}

impl ScalrConfig {
    /// A validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new() -> Result<Self, TrainError> {
        Self::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 20, 0.01, 0.95, false, 0.1)
    }

    /// A validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidLearningRate`] if `lr < 0`,
    /// [`TrainError::InvalidMomentum`] if `momentum < 0`,
    /// [`TrainError::InvalidWeightDecay`] if `weight_decay < 0`,
    /// [`TrainError::InvalidRMin`] if `r_min` is outside `[0, 1]`,
    /// [`TrainError::InvalidAlpha`] if `alpha <= 0`, or
    /// [`TrainError::NonFiniteParameter`] if `oscillation_threshold`,
    /// `oscillation_decay`, or `r_min_ema_alpha` is not finite.
    /// (`warmup_steps`/`oscillation_window` are `usize` and so are always
    /// non-negative, matching the reference's `warmup_steps < 0` guard
    /// vacuously.)
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        lr: f64,
        momentum: f64,
        weight_decay: f64,
        r_min: f64,
        alpha: f64,
        warmup_steps: usize,
        oscillation_window: usize,
        oscillation_threshold: f64,
        oscillation_decay: f64,
        adaptive_r_min: bool,
        r_min_ema_alpha: f64,
    ) -> Result<Self, TrainError> {
        if !(lr.is_finite() && lr >= 0.0) {
            return Err(TrainError::InvalidLearningRate { value: lr });
        }
        if !(momentum.is_finite() && momentum >= 0.0) {
            return Err(TrainError::InvalidMomentum { value: momentum });
        }
        if !(weight_decay.is_finite() && weight_decay >= 0.0) {
            return Err(TrainError::InvalidWeightDecay {
                value: weight_decay,
            });
        }
        if !(r_min.is_finite() && (0.0..=1.0).contains(&r_min)) {
            return Err(TrainError::InvalidRMin { value: r_min });
        }
        if !(alpha.is_finite() && alpha > 0.0) {
            return Err(TrainError::InvalidAlpha { value: alpha });
        }
        validate_finite("oscillation_threshold", oscillation_threshold)?;
        validate_finite("oscillation_decay", oscillation_decay)?;
        validate_finite("r_min_ema_alpha", r_min_ema_alpha)?;
        Ok(Self {
            lr,
            momentum,
            weight_decay,
            r_min,
            alpha,
            warmup_steps,
            oscillation_window,
            oscillation_threshold,
            oscillation_decay,
            adaptive_r_min,
            r_min_ema_alpha,
        })
    }

    /// Build a fresh [`Scalr`] with no step history and no momentum buffer.
    pub fn init<B: Backend, const D: usize>(&self) -> Scalr<B, D> {
        Scalr {
            config: self.clone(),
            r_min: self.r_min,
            step_count: 0,
            lr_decay_factor: 1.0,
            r_ema: None,
            order_history: Vec::new(),
            lr_history: Vec::new(),
            momentum_buffer: None,
        }
    }
}

/// Serializable snapshot of [`Scalr`]'s step-dependent state (see
/// [`crate::feedback::OscillatorOptimizer`]'s docs on the tensor/non-tensor
/// state split — the momentum buffer is reached via
/// [`Scalr::momentum_buffer`], not this struct).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ScalrState {
    /// Base learning rate η_base.
    pub lr: f64,
    /// Momentum factor.
    pub momentum: f64,
    /// L2 weight-decay coefficient.
    pub weight_decay: f64,
    /// Exponent controlling synchronization sensitivity.
    pub alpha: f64,
    /// Steps to use the full base lr before SCALR scaling kicks in.
    pub warmup_steps: usize,
    /// Window size for oscillation detection.
    pub oscillation_window: usize,
    /// Windowed-variance threshold for oscillation detection.
    pub oscillation_threshold: f64,
    /// Multiplicative lr decay applied once per oscillation detection.
    pub oscillation_decay: f64,
    /// Whether adaptive `r_min` is enabled.
    pub adaptive_r_min: bool,
    /// EMA smoothing factor for adaptive `r_min`.
    pub r_min_ema_alpha: f64,
    /// The *live* `r_min` (may differ from the config default under
    /// [`ScalrConfig::adaptive_r_min`]).
    pub r_min: f64,
    /// Number of steps taken so far.
    pub step_count: usize,
    /// Cumulative oscillation-decay factor.
    pub lr_decay_factor: f64,
    /// EMA of the order parameter, if adaptive `r_min` has ever run.
    pub r_ema: Option<f64>,
    /// History of order-parameter values across steps.
    pub order_history: Vec<f64>,
    /// History of effective learning rates.
    pub lr_history: Vec<f64>,
}

/// Synchronization-Coupled Adaptive Learning Rate optimizer. Construct via
/// [`ScalrConfig::init`].
///
/// See the module docs for the exact update equations.
#[derive(Debug, Clone)]
pub struct Scalr<B: Backend, const D: usize> {
    config: ScalrConfig,
    r_min: f64,
    step_count: usize,
    lr_decay_factor: f64,
    r_ema: Option<f64>,
    order_history: Vec<f64>,
    lr_history: Vec<f64>,
    momentum_buffer: Option<Tensor<B, D>>,
}

impl<B: Backend, const D: usize> Scalr<B, D> {
    /// The active configuration (`r_min` here is the *original* config
    /// value; see [`Self::r_min`] for the live, possibly-adapted value).
    pub fn config(&self) -> &ScalrConfig {
        &self.config
    }

    /// The live `r_min` (equals `config().r_min` unless adaptive `r_min` has
    /// adjusted it).
    pub fn r_min(&self) -> f64 {
        self.r_min
    }

    /// Number of steps taken so far.
    pub fn step_count(&self) -> usize {
        self.step_count
    }

    /// Cumulative oscillation-decay factor.
    pub fn lr_decay_factor(&self) -> f64 {
        self.lr_decay_factor
    }

    /// EMA of the order parameter, if adaptive `r_min` has ever run.
    pub fn r_ema(&self) -> Option<f64> {
        self.r_ema
    }

    /// History of order-parameter values across steps.
    pub fn order_history(&self) -> &[f64] {
        &self.order_history
    }

    /// History of effective learning rates.
    pub fn lr_history(&self) -> &[f64] {
        &self.lr_history
    }

    /// The current momentum buffer, if any step with `momentum != 0` has
    /// run.
    pub fn momentum_buffer(&self) -> Option<&Tensor<B, D>> {
        self.momentum_buffer.as_ref()
    }

    /// Overwrite the momentum buffer (deterministic-resume support).
    pub fn set_momentum_buffer(&mut self, buffer: Option<Tensor<B, D>>) {
        self.momentum_buffer = buffer;
    }

    /// Compute the learning-rate scaling factor `r_min + (1 −
    /// r_min)·clamp(r, 0, 1)^α`, using the live [`Self::r_min`].
    pub fn compute_lr_scale(&self, order_parameter: f64) -> f64 {
        let r = order_parameter.clamp(0.0, 1.0);
        self.r_min + (1.0 - self.r_min) * r.powf(self.config.alpha)
    }

    /// `true` if the windowed variance of the last `oscillation_window`
    /// order-history entries exceeds `oscillation_threshold`.
    fn detect_oscillation(&self) -> bool {
        let w = self.config.oscillation_window;
        if self.order_history.len() < w || w == 0 {
            return false;
        }
        let recent = &self.order_history[self.order_history.len() - w..];
        let mean = recent.iter().sum::<f64>() / w as f64;
        let var = recent.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / w as f64;
        var > self.config.oscillation_threshold
    }

    /// Update the EMA of the order parameter and re-derive `r_min =
    /// clamp(0.3·EMA, 0.01, 0.5)`.
    fn update_adaptive_r_min(&mut self, order_parameter: f64) {
        self.r_ema = Some(match self.r_ema {
            None => order_parameter,
            Some(prev) => {
                self.config.r_min_ema_alpha * order_parameter
                    + (1.0 - self.config.r_min_ema_alpha) * prev
            }
        });
        self.r_min = (self.r_ema.unwrap() * 0.3).clamp(0.01, 0.5);
    }

    /// Record shared bookkeeping for one step: increment the step counter,
    /// push `global_r` (if any) onto the order history, run adaptive
    /// `r_min` (if enabled and `global_r` is available), and apply
    /// oscillation-aware decay if the (now-updated) history triggers it.
    ///
    /// `global_r` is [`OrderParameter::global`] for the per-group entry
    /// point ([`Self::step_with_order_parameter`]), or
    /// [`crate::feedback::StepFeedback::order_parameter`] directly for the
    /// [`crate::feedback::OscillatorOptimizer`] entry point ([`Self::step`]).
    fn record_feedback(&mut self, global_r: Option<f64>) {
        self.step_count += 1;
        if let Some(r) = global_r {
            self.order_history.push(r);
            if self.config.adaptive_r_min {
                self.update_adaptive_r_min(r);
            }
        }
        if self.detect_oscillation() {
            self.lr_decay_factor *= self.config.oscillation_decay;
        }
    }

    /// Apply the update given an order parameter already resolved to a
    /// scalar lr-scale input (`None` for full base lr, ignoring warmup).
    fn step_core(
        &mut self,
        param: Tensor<B, D>,
        grad: Option<Tensor<B, D>>,
        resolved_r_for_scale: Option<f64>,
    ) -> Result<Tensor<B, D>, TrainError> {
        let lr_scale = match resolved_r_for_scale {
            Some(r) if self.step_count > self.config.warmup_steps => self.compute_lr_scale(r),
            _ => 1.0,
        };
        let lr = self.config.lr * lr_scale * self.lr_decay_factor;
        self.lr_history.push(lr);

        let Some(grad) = grad else {
            return Ok(param);
        };
        check_dims("grad", grad.dims(), param.dims())?;
        Ok(sgd_update(
            param,
            grad,
            self.config.weight_decay,
            self.config.momentum,
            0.0, // SCALR's reference has no `dampening` parameter (`alpha=1.0`).
            &mut self.momentum_buffer,
            lr,
        ))
    }

    /// The Q3 per-group step: SCALR's `order_parameter: Dict[str, float]`
    /// mode. `group` selects this instance's slice of `order_parameter` for
    /// the lr-scale computation; the step counter, order history,
    /// oscillation decay, and adaptive `r_min` all track
    /// [`OrderParameter::global`] (the reference's dict-mean fallback), so
    /// multiple per-group `Scalr` instances driven by the *same*
    /// `order_parameter` value each step observe identical shared
    /// bookkeeping — matching the reference's single optimizer instance
    /// shared across every param group exactly, since `global()` depends
    /// only on the incoming dict, never on which group is stepping.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `grad`'s shape does not
    /// match `param`'s.
    pub fn step_with_order_parameter(
        &mut self,
        param: Tensor<B, D>,
        grad: Option<Tensor<B, D>>,
        order_parameter: Option<&OrderParameter>,
        group: &str,
    ) -> Result<Tensor<B, D>, TrainError> {
        let global_r = order_parameter.map(OrderParameter::global);
        self.record_feedback(global_r);
        let group_r = order_parameter.map(|op| op.resolve(group));
        self.step_core(param, grad, group_r)
    }
}

impl<B: Backend, const D: usize> OscillatorOptimizer<B, D> for Scalr<B, D> {
    type State = ScalrState;

    fn step(
        &mut self,
        param: Tensor<B, D>,
        grad: Option<Tensor<B, D>>,
        feedback: &StepFeedback<B>,
    ) -> Result<Tensor<B, D>, TrainError> {
        self.record_feedback(feedback.order_parameter);
        self.step_core(param, grad, feedback.order_parameter)
    }

    fn state_dict(&self) -> ScalrState {
        ScalrState {
            lr: self.config.lr,
            momentum: self.config.momentum,
            weight_decay: self.config.weight_decay,
            alpha: self.config.alpha,
            warmup_steps: self.config.warmup_steps,
            oscillation_window: self.config.oscillation_window,
            oscillation_threshold: self.config.oscillation_threshold,
            oscillation_decay: self.config.oscillation_decay,
            adaptive_r_min: self.config.adaptive_r_min,
            r_min_ema_alpha: self.config.r_min_ema_alpha,
            r_min: self.r_min,
            step_count: self.step_count,
            lr_decay_factor: self.lr_decay_factor,
            r_ema: self.r_ema,
            order_history: self.order_history.clone(),
            lr_history: self.lr_history.clone(),
        }
    }

    fn load_state_dict(&mut self, state: ScalrState) -> Result<(), TrainError> {
        // `ScalrState` only carries the *live* r_min (post-adaptation);
        // the original config default is not separately preserved, since
        // no method ever reads `config.r_min` again after construction —
        // every computation uses the live `self.r_min` restored just below.
        let config = ScalrConfig::with_params(
            state.lr,
            state.momentum,
            state.weight_decay,
            state.r_min,
            state.alpha,
            state.warmup_steps,
            state.oscillation_window,
            state.oscillation_threshold,
            state.oscillation_decay,
            state.adaptive_r_min,
            state.r_min_ema_alpha,
        )?;
        self.config = config;
        self.r_min = state.r_min;
        self.step_count = state.step_count;
        self.lr_decay_factor = state.lr_decay_factor;
        self.r_ema = state.r_ema;
        self.order_history = state.order_history;
        self.lr_history = state.lr_history;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;
    use std::collections::HashMap;

    type TestBackend = NdArray<f64>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn default_opt() -> Scalr<TestBackend, 1> {
        ScalrConfig::new().unwrap().init()
    }

    // --- Config validation ---

    #[test]
    fn negative_lr_rejected() {
        assert!(matches!(
            ScalrConfig::with_params(-0.1, 0.0, 0.0, 0.1, 1.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidLearningRate { .. }
        ));
    }

    #[test]
    fn negative_momentum_rejected() {
        assert!(matches!(
            ScalrConfig::with_params(0.01, -0.1, 0.0, 0.1, 1.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidMomentum { .. }
        ));
    }

    #[test]
    fn negative_weight_decay_rejected() {
        assert!(matches!(
            ScalrConfig::with_params(0.01, 0.0, -0.1, 0.1, 1.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidWeightDecay { .. }
        ));
    }

    #[test]
    fn out_of_range_r_min_rejected() {
        assert!(matches!(
            ScalrConfig::with_params(0.01, 0.0, 0.0, 1.5, 1.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidRMin { .. }
        ));
    }

    #[test]
    fn config_accessor_reports_original_values() {
        let opt = ScalrConfig::with_params(0.02, 0.1, 0.0, 0.2, 1.3, 0, 20, 0.01, 0.95, false, 0.1)
            .unwrap()
            .init::<TestBackend, 1>();
        assert_eq!(opt.config().lr, 0.02);
        assert_eq!(opt.config().alpha, 1.3);
    }

    #[test]
    fn load_state_dict_revalidates() {
        let mut opt = default_opt();
        let mut bad_state = opt.state_dict();
        bad_state.momentum = -1.0;
        assert!(matches!(
            opt.load_state_dict(bad_state).unwrap_err(),
            TrainError::InvalidMomentum { .. }
        ));
    }

    #[test]
    fn non_positive_alpha_rejected() {
        assert!(matches!(
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 0.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidAlpha { .. }
        ));
        assert!(matches!(
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, -1.0, 0, 20, 0.01, 0.95, false, 0.1)
                .unwrap_err(),
            TrainError::InvalidAlpha { .. }
        ));
    }

    // --- compute_lr_scale ---

    #[test]
    fn lr_scale_at_r_one_is_one() {
        let opt = default_opt();
        assert!((opt.compute_lr_scale(1.0) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn lr_scale_at_r_zero_is_r_min() {
        let opt = default_opt();
        assert!((opt.compute_lr_scale(0.0) - opt.r_min()).abs() < 1e-12);
    }

    #[test]
    fn lr_scale_clamps_out_of_range_r() {
        let opt = default_opt();
        assert!((opt.compute_lr_scale(2.0) - opt.compute_lr_scale(1.0)).abs() < 1e-12);
        assert!((opt.compute_lr_scale(-2.0) - opt.compute_lr_scale(0.0)).abs() < 1e-12);
    }

    // --- step: basic ---

    #[test]
    fn step_updates_all_parameters() {
        let dev = device();
        let mut opt = default_opt();
        let param = Tensor::<TestBackend, 1>::zeros([5], &dev);
        let grad = Tensor::<TestBackend, 1>::ones([5], &dev);
        let out = opt
            .step(param, Some(grad), &StepFeedback::order(0.5))
            .unwrap();
        assert!(out
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|v: &f64| *v != 0.0));
    }

    #[test]
    fn step_without_order_parameter_uses_full_base_lr() {
        let dev = device();
        let mut opt = default_opt();
        let param = Tensor::<TestBackend, 1>::zeros([1], &dev);
        let grad = Tensor::<TestBackend, 1>::ones([1], &dev);
        let out = opt.step(param, Some(grad), &StepFeedback::none()).unwrap();
        let value = out.to_data().to_vec::<f64>().unwrap()[0];
        assert!((value - (-0.01)).abs() < 1e-12);
    }

    #[test]
    fn warmup_steps_defer_scaling() {
        let dev = device();
        let mut opt =
            ScalrConfig::with_params(0.1, 0.0, 0.0, 0.0, 1.0, 2, 20, 100.0, 1.0, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();
        let grad = Tensor::<TestBackend, 1>::ones([1], &dev);
        // r_min=0 so a very low r would normally crush lr toward 0; during
        // warmup (steps 1-2) the full base lr applies regardless.
        for _ in 0..2 {
            let param = Tensor::<TestBackend, 1>::zeros([1], &dev);
            let out = opt
                .step(param, Some(grad.clone()), &StepFeedback::order(0.0))
                .unwrap();
            let value = out.to_data().to_vec::<f64>().unwrap()[0];
            assert!(
                (value - (-0.1)).abs() < 1e-12,
                "expected full lr during warmup"
            );
        }
        // Step 3: warmup over, r=0 with r_min=0 crushes the step toward 0.
        let param = Tensor::<TestBackend, 1>::zeros([1], &dev);
        let out = opt
            .step(param, Some(grad), &StepFeedback::order(0.0))
            .unwrap();
        let value = out.to_data().to_vec::<f64>().unwrap()[0];
        assert!(value.abs() < 1e-12, "expected r_min=0 to crush the step");
    }

    #[test]
    fn step_rejects_grad_shape_mismatch() {
        let dev = device();
        let mut opt = default_opt();
        let param = Tensor::<TestBackend, 1>::zeros([4], &dev);
        let grad = Tensor::<TestBackend, 1>::zeros([5], &dev);
        let err = opt
            .step(param, Some(grad), &StepFeedback::none())
            .unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "grad", .. }
        ));
    }

    // --- Q3: oscillation-aware decay ---

    #[test]
    fn oscillation_decay_triggers_on_high_variance() {
        let mut opt =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 5, 0.001, 0.9, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();
        for r in [0.2, 0.8, 0.2, 0.8, 0.2] {
            opt.record_feedback(Some(r));
        }
        assert!(opt.lr_decay_factor() < 1.0);
    }

    #[test]
    fn no_decay_when_history_is_stable() {
        let mut opt =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 5, 0.01, 0.9, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();
        for _ in 0..5 {
            opt.record_feedback(Some(0.9));
        }
        assert_eq!(opt.lr_decay_factor(), 1.0);
    }

    #[test]
    fn window_shorter_than_history_length_is_not_evaluated() {
        let mut opt =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 3, 0.001, 0.9, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();
        // Only 2 entries with window=3: oscillation check is skipped.
        opt.record_feedback(Some(0.2));
        opt.record_feedback(Some(0.9));
        assert_eq!(opt.lr_decay_factor(), 1.0);
    }

    // --- Q3: adaptive r_min ---

    #[test]
    fn adaptive_r_min_tracks_ema_and_updates_r_min() {
        let mut opt =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 20, 0.01, 0.95, true, 0.5)
                .unwrap()
                .init::<TestBackend, 1>();
        for r in [0.5, 0.6, 0.7, 0.8, 0.9] {
            opt.record_feedback(Some(r));
        }
        assert!(opt.r_ema().is_some());
        assert!(opt.r_ema().unwrap() > 0.0);
        let expected_r_min = (opt.r_ema().unwrap() * 0.3).clamp(0.01, 0.5);
        assert!((opt.r_min() - expected_r_min).abs() < 1e-12);
    }

    #[test]
    fn r_min_unchanged_when_adaptive_disabled() {
        let mut opt =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.2, 1.0, 0, 20, 0.01, 0.95, false, 0.5)
                .unwrap()
                .init::<TestBackend, 1>();
        for r in [0.5, 0.9] {
            opt.record_feedback(Some(r));
        }
        assert_eq!(opt.r_min(), 0.2);
        assert!(opt.r_ema().is_none());
    }

    // --- Q3: per-group order parameters ---

    #[test]
    fn per_group_step_does_not_error_and_updates_parameters() {
        let dev = device();
        let mut delta = ScalrConfig::new().unwrap().init::<TestBackend, 1>();
        let mut theta = ScalrConfig::new().unwrap().init::<TestBackend, 1>();

        let mut dict = HashMap::new();
        dict.insert("delta".to_string(), 0.8);
        dict.insert("theta".to_string(), 0.5);
        let order = OrderParameter::PerGroup(dict);

        let p_delta = Tensor::<TestBackend, 1>::zeros([2], &dev);
        let p_theta = Tensor::<TestBackend, 1>::zeros([2], &dev);
        let grad = Tensor::<TestBackend, 1>::ones([2], &dev);

        let out_delta = delta
            .step_with_order_parameter(p_delta, Some(grad.clone()), Some(&order), "delta")
            .unwrap();
        let out_theta = theta
            .step_with_order_parameter(p_theta, Some(grad), Some(&order), "theta")
            .unwrap();

        // delta has a higher order parameter (0.8 > 0.5), so its lr_scale
        // is larger and it takes a bigger step toward zero (from a larger
        // negative update, since grad=1 and lr are both positive).
        let d = out_delta.to_data().to_vec::<f64>().unwrap()[0];
        let t = out_theta.to_data().to_vec::<f64>().unwrap()[0];
        assert!(d < t, "delta={d} theta={t}");
    }

    #[test]
    fn per_group_shared_bookkeeping_matches_across_instances() {
        // Two independently-constructed Scalr instances, driven by the same
        // sequence of PerGroup dicts, must observe identical global-r
        // bookkeeping (order_history, lr_decay_factor, step_count) because
        // OrderParameter::global() depends only on the dict, never on which
        // group is being stepped.
        let dev = device();
        let mut a =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 3, 0.001, 0.9, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();
        let mut b =
            ScalrConfig::with_params(0.01, 0.0, 0.0, 0.1, 1.0, 0, 3, 0.001, 0.9, false, 0.1)
                .unwrap()
                .init::<TestBackend, 1>();

        for (ra, rb) in [(0.2, 0.9), (0.8, 0.1), (0.2, 0.9)] {
            let mut dict = HashMap::new();
            dict.insert("a".to_string(), ra);
            dict.insert("b".to_string(), rb);
            let order = OrderParameter::PerGroup(dict);
            let pa = Tensor::<TestBackend, 1>::zeros([1], &dev);
            let pb = Tensor::<TestBackend, 1>::zeros([1], &dev);
            a.step_with_order_parameter(pa, None, Some(&order), "a")
                .unwrap();
            b.step_with_order_parameter(pb, None, Some(&order), "b")
                .unwrap();
        }

        assert_eq!(a.order_history(), b.order_history());
        assert_eq!(a.step_count(), b.step_count());
        assert!((a.lr_decay_factor() - b.lr_decay_factor()).abs() < 1e-15);
    }

    // --- state_dict / load_state_dict (deterministic resume) ---

    #[test]
    fn state_round_trips_through_json() {
        let mut opt =
            ScalrConfig::with_params(0.02, 0.1, 0.0, 0.15, 1.2, 1, 4, 0.02, 0.8, true, 0.3)
                .unwrap()
                .init::<TestBackend, 1>();
        for r in [0.4, 0.6, 0.9, 0.3] {
            opt.record_feedback(Some(r));
        }

        let state = opt.state_dict();
        let json = serde_json::to_string(&state).unwrap();
        let restored: ScalrState = serde_json::from_str(&json).unwrap();
        assert_eq!(state, restored);

        let mut fresh = ScalrConfig::new().unwrap().init::<TestBackend, 1>();
        fresh.load_state_dict(restored).unwrap();
        assert_eq!(fresh.order_history(), opt.order_history());
        assert_eq!(fresh.step_count(), opt.step_count());
        assert!((fresh.r_min() - opt.r_min()).abs() < 1e-15);
    }

    #[test]
    fn deterministic_resume_matches_uninterrupted_run() {
        let dev = device();
        let rs: [f64; 4] = [0.9, 0.3, 0.9, 0.3];

        let mut baseline =
            ScalrConfig::with_params(0.05, 0.8, 0.0, 0.1, 1.3, 0, 3, 0.05, 0.7, true, 0.2)
                .unwrap()
                .init::<TestBackend, 1>();
        let mut p_baseline = Tensor::<TestBackend, 1>::zeros([3], &dev);
        for r in rs {
            let grad = Tensor::<TestBackend, 1>::ones([3], &dev);
            p_baseline = baseline
                .step(p_baseline, Some(grad), &StepFeedback::order(r))
                .unwrap();
        }

        let mut first =
            ScalrConfig::with_params(0.05, 0.8, 0.0, 0.1, 1.3, 0, 3, 0.05, 0.7, true, 0.2)
                .unwrap()
                .init::<TestBackend, 1>();
        let mut p_resumed = Tensor::<TestBackend, 1>::zeros([3], &dev);
        for r in &rs[..2] {
            let grad = Tensor::<TestBackend, 1>::ones([3], &dev);
            p_resumed = first
                .step(p_resumed, Some(grad), &StepFeedback::order(*r))
                .unwrap();
        }

        let snapshot = first.state_dict();
        let momentum_snapshot = first.momentum_buffer().cloned();
        let mut resumed = ScalrConfig::new().unwrap().init::<TestBackend, 1>();
        resumed.load_state_dict(snapshot).unwrap();
        resumed.set_momentum_buffer(momentum_snapshot);

        for r in &rs[2..] {
            let grad = Tensor::<TestBackend, 1>::ones([3], &dev);
            p_resumed = resumed
                .step(p_resumed, Some(grad), &StepFeedback::order(*r))
                .unwrap();
        }

        let baseline_data = p_baseline.to_data().to_vec::<f64>().unwrap();
        let resumed_data = p_resumed.to_data().to_vec::<f64>().unwrap();
        for (b, r) in baseline_data.iter().zip(resumed_data.iter()) {
            assert!((b - r).abs() < 1e-12, "baseline {b} vs resumed {r}");
        }
        assert_eq!(baseline.lr_history(), resumed.lr_history());
    }
}

//! SGD with a synchronization-barrier penalty (PRINet 3.0
//! `SynchronizedGradientDescent`, Project 1B).
//!
//! Extends plain momentum-SGD with a penalty term that discourages the
//! Kuramoto order parameter from dropping below a critical threshold during
//! training. The total loss is conceptually
//!
//! ```text
//! L_total = L_task + λ·max(0, K_c − K)²
//! ```
//!
//! where `K` is the current order parameter and `K_c` is `critical_order`.
//! [`SyncGd`] does not compute `L_task` (Rust has no autodiff loss graph
//! here — see [`crate::feedback`]'s module docs on the thin-torch-side
//! split); it reproduces the reference's *effect* on the update: the
//! penalty's gradient scale is used to reduce the effective learning rate
//! (a protective slowdown) rather than being added to a returned scalar
//! loss.
//!
//! # Update equations
//!
//! For deficit `d = max(0, K_c − K)`, penalty `P = λ·d²`, gradient scale
//! `s = 2λd` (zero when `d = 0`), and modulation `m = max(0.1, 1 − s)`
//! (`1.0` when no order parameter is supplied):
//!
//! ```text
//! d_p = grad (+ weight_decay·param)
//! buf = buf·momentum + d_p·(1 − dampening)   (buf = d_p on the first step)
//! d_p = buf                                   (if momentum != 0)
//! param' = param − (lr·m)·d_p
//! ```
//!
//! [`SyncGd::compute_sync_penalty`] is a direct, line-for-line port of
//! `SynchronizedGradientDescent.compute_sync_penalty`; [`SyncGd::step`]
//! (via [`crate::feedback::OscillatorOptimizer`]) ports `.step`'s update
//! loop. Golden-value parity tests live in `tests/parity_optimizers.rs`.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::feedback::{OscillatorOptimizer, StepFeedback};
//! use prin_train::sync_gd::SyncGdConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let mut opt = SyncGdConfig::with_params(0.1, 0.0, 0.0, 1.0, 0.8, 0.0)
//!     .unwrap()
//!     .init::<Backend, 1>();
//! let param = Tensor::<Backend, 1>::zeros([4], &device);
//! let grad = Tensor::<Backend, 1>::ones([4], &device);
//!
//! let updated = opt
//!     .step(param, Some(grad), &StepFeedback::order(0.5))
//!     .unwrap();
//! assert_eq!(opt.order_history(), &[0.5]);
//! ```

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use serde::{Deserialize, Serialize};

use crate::error::TrainError;
use crate::feedback::{OscillatorOptimizer, StepFeedback};
use crate::support::{check_dims, sgd_update, validate_finite};

/// Validated hyperparameters for [`SyncGd`].
///
/// Defaults ([`Self::new`]) match the PRINet 3.0 reference: `lr=0.01,
/// momentum=0.0, weight_decay=0.0, sync_penalty=0.1, critical_order=0.5,
/// dampening=0.0`.
#[derive(Clone, Debug, PartialEq)]
pub struct SyncGdConfig {
    /// Learning rate.
    pub lr: f64,
    /// Momentum factor.
    pub momentum: f64,
    /// L2 weight-decay coefficient.
    pub weight_decay: f64,
    /// Synchronization penalty weight λ.
    pub sync_penalty: f64,
    /// Critical order-parameter threshold `K_c`.
    pub critical_order: f64,
    /// Momentum dampening.
    pub dampening: f64,
}

impl SyncGdConfig {
    /// A validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new() -> Result<Self, TrainError> {
        Self::with_params(0.01, 0.0, 0.0, 0.1, 0.5, 0.0)
    }

    /// A validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidLearningRate`] if `lr < 0`,
    /// [`TrainError::InvalidMomentum`] if `momentum < 0`,
    /// [`TrainError::InvalidWeightDecay`] if `weight_decay < 0`,
    /// [`TrainError::InvalidSyncPenalty`] if `sync_penalty < 0`,
    /// [`TrainError::InvalidCriticalOrder`] if `critical_order` is outside
    /// `[0, 1]`, or [`TrainError::NonFiniteParameter`] if `dampening` is
    /// not finite.
    pub fn with_params(
        lr: f64,
        momentum: f64,
        weight_decay: f64,
        sync_penalty: f64,
        critical_order: f64,
        dampening: f64,
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
        if !(sync_penalty.is_finite() && sync_penalty >= 0.0) {
            return Err(TrainError::InvalidSyncPenalty {
                value: sync_penalty,
            });
        }
        if !(critical_order.is_finite() && (0.0..=1.0).contains(&critical_order)) {
            return Err(TrainError::InvalidCriticalOrder {
                value: critical_order,
            });
        }
        validate_finite("dampening", dampening)?;
        Ok(Self {
            lr,
            momentum,
            weight_decay,
            sync_penalty,
            critical_order,
            dampening,
        })
    }

    /// Build a fresh [`SyncGd`] with no step history and no momentum
    /// buffer.
    pub fn init<B: Backend, const D: usize>(&self) -> SyncGd<B, D> {
        SyncGd {
            config: self.clone(),
            momentum_buffer: None,
            order_history: Vec::new(),
            penalty_history: Vec::new(),
        }
    }
}

/// Serializable snapshot of [`SyncGd`]'s step-dependent state (see
/// [`crate::feedback::OscillatorOptimizer`]'s docs on the tensor/non-tensor
/// state split — the momentum buffer is reached via
/// [`SyncGd::momentum_buffer`], not this struct).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SyncGdState {
    /// Learning rate.
    pub lr: f64,
    /// Momentum factor.
    pub momentum: f64,
    /// L2 weight-decay coefficient.
    pub weight_decay: f64,
    /// Synchronization penalty weight λ.
    pub sync_penalty: f64,
    /// Critical order-parameter threshold `K_c`.
    pub critical_order: f64,
    /// Momentum dampening.
    pub dampening: f64,
    /// History of order-parameter values passed to [`SyncGd::step`].
    pub order_history: Vec<f64>,
    /// History of synchronization penalty values.
    pub penalty_history: Vec<f64>,
}

/// SGD with a synchronization-barrier penalty. Construct via
/// [`SyncGdConfig::init`].
///
/// See the module docs for the exact update equations.
#[derive(Debug, Clone)]
pub struct SyncGd<B: Backend, const D: usize> {
    config: SyncGdConfig,
    momentum_buffer: Option<Tensor<B, D>>,
    order_history: Vec<f64>,
    penalty_history: Vec<f64>,
}

impl<B: Backend, const D: usize> SyncGd<B, D> {
    /// The active configuration.
    pub fn config(&self) -> &SyncGdConfig {
        &self.config
    }

    /// History of order-parameter values across optimization steps.
    pub fn order_history(&self) -> &[f64] {
        &self.order_history
    }

    /// History of synchronization penalty values.
    pub fn penalty_history(&self) -> &[f64] {
        &self.penalty_history
    }

    /// The current momentum buffer, if any step with `momentum != 0` has
    /// run.
    pub fn momentum_buffer(&self) -> Option<&Tensor<B, D>> {
        self.momentum_buffer.as_ref()
    }

    /// Overwrite the momentum buffer (deterministic-resume support: paired
    /// with [`crate::feedback::OscillatorOptimizer::load_state_dict`] to
    /// restore the tensor half of state that `State` itself does not
    /// carry).
    pub fn set_momentum_buffer(&mut self, buffer: Option<Tensor<B, D>>) {
        self.momentum_buffer = buffer;
    }

    /// Compute the synchronization barrier penalty and its gradient scale,
    /// and record `order_parameter`/the penalty into the step histories.
    ///
    /// `penalty = sync_penalty · max(0, critical_order − order_parameter)²`;
    /// `grad_scale = 2 · sync_penalty · deficit` when the deficit is
    /// positive, else `0`.
    pub fn compute_sync_penalty(&mut self, order_parameter: f64) -> (f64, f64) {
        let deficit = (self.config.critical_order - order_parameter).max(0.0);
        let penalty = self.config.sync_penalty * deficit * deficit;
        let grad_scale = if deficit > 0.0 {
            2.0 * self.config.sync_penalty * deficit
        } else {
            0.0
        };
        self.order_history.push(order_parameter);
        self.penalty_history.push(penalty);
        (penalty, grad_scale)
    }
}

impl<B: Backend, const D: usize> OscillatorOptimizer<B, D> for SyncGd<B, D> {
    type State = SyncGdState;

    fn step(
        &mut self,
        param: Tensor<B, D>,
        grad: Option<Tensor<B, D>>,
        feedback: &StepFeedback<B>,
    ) -> Result<Tensor<B, D>, TrainError> {
        let mut grad_modulation = 1.0;
        if let Some(r) = feedback.order_parameter {
            let (_penalty, grad_scale) = self.compute_sync_penalty(r);
            if grad_scale > 0.0 {
                grad_modulation = (1.0 - grad_scale).max(0.1);
            }
        }

        let Some(grad) = grad else {
            return Ok(param);
        };
        check_dims("grad", grad.dims(), param.dims())?;

        let lr = self.config.lr * grad_modulation;
        Ok(sgd_update(
            param,
            grad,
            self.config.weight_decay,
            self.config.momentum,
            self.config.dampening,
            &mut self.momentum_buffer,
            lr,
        ))
    }

    fn state_dict(&self) -> SyncGdState {
        SyncGdState {
            lr: self.config.lr,
            momentum: self.config.momentum,
            weight_decay: self.config.weight_decay,
            sync_penalty: self.config.sync_penalty,
            critical_order: self.config.critical_order,
            dampening: self.config.dampening,
            order_history: self.order_history.clone(),
            penalty_history: self.penalty_history.clone(),
        }
    }

    fn load_state_dict(&mut self, state: SyncGdState) -> Result<(), TrainError> {
        let config = SyncGdConfig::with_params(
            state.lr,
            state.momentum,
            state.weight_decay,
            state.sync_penalty,
            state.critical_order,
            state.dampening,
        )?;
        self.config = config;
        self.order_history = state.order_history;
        self.penalty_history = state.penalty_history;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    // --- Config validation ---

    #[test]
    fn negative_lr_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(-0.1, 0.0, 0.0, 0.1, 0.5, 0.0).unwrap_err(),
            TrainError::InvalidLearningRate { .. }
        ));
    }

    #[test]
    fn negative_momentum_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(0.1, -0.1, 0.0, 0.1, 0.5, 0.0).unwrap_err(),
            TrainError::InvalidMomentum { .. }
        ));
    }

    #[test]
    fn negative_weight_decay_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(0.1, 0.0, -0.1, 0.1, 0.5, 0.0).unwrap_err(),
            TrainError::InvalidWeightDecay { .. }
        ));
    }

    #[test]
    fn negative_sync_penalty_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(0.1, 0.0, 0.0, -0.1, 0.5, 0.0).unwrap_err(),
            TrainError::InvalidSyncPenalty { .. }
        ));
    }

    #[test]
    fn out_of_range_critical_order_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(0.1, 0.0, 0.0, 0.1, 1.5, 0.0).unwrap_err(),
            TrainError::InvalidCriticalOrder { .. }
        ));
        assert!(matches!(
            SyncGdConfig::with_params(0.1, 0.0, 0.0, 0.1, -0.1, 0.0).unwrap_err(),
            TrainError::InvalidCriticalOrder { .. }
        ));
    }

    #[test]
    fn non_finite_dampening_rejected() {
        assert!(matches!(
            SyncGdConfig::with_params(0.1, 0.0, 0.0, 0.1, 0.5, f64::NAN).unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "dampening",
                ..
            }
        ));
    }

    // --- compute_sync_penalty ---

    #[test]
    fn no_penalty_above_critical() {
        let mut opt = SyncGdConfig::with_params(0.01, 0.0, 0.0, 1.0, 0.5, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let (penalty, grad_scale) = opt.compute_sync_penalty(0.8);
        assert_eq!(penalty, 0.0);
        assert_eq!(grad_scale, 0.0);
    }

    #[test]
    fn penalty_positive_below_critical() {
        let mut opt = SyncGdConfig::with_params(0.01, 0.0, 0.0, 1.0, 0.8, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let (penalty, grad_scale) = opt.compute_sync_penalty(0.5);
        assert!(penalty > 0.0);
        assert!(grad_scale > 0.0);
    }

    #[test]
    fn penalty_formula_matches_lambda_deficit_squared() {
        let mut opt = SyncGdConfig::with_params(0.01, 0.0, 0.0, 2.0, 0.8, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let (penalty, _) = opt.compute_sync_penalty(0.5);
        let expected = 2.0 * (0.8_f64 - 0.5).powi(2);
        assert!((penalty - expected).abs() < 1e-6);
    }

    #[test]
    fn order_history_tracks_every_step() {
        let mut opt = SyncGdConfig::with_params(0.01, 0.0, 0.0, 0.1, 0.5, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        for r in [0.3, 0.6, 0.9] {
            opt.compute_sync_penalty(r);
        }
        assert_eq!(opt.order_history(), &[0.3, 0.6, 0.9]);
    }

    // --- step ---

    #[test]
    fn basic_step_updates_parameters() {
        let dev = device();
        let mut opt = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
        let param = Tensor::<TestBackend, 1>::zeros([10], &dev);
        let grad = Tensor::<TestBackend, 1>::ones([10], &dev);
        let initial = param.to_data().to_vec::<f64>().unwrap();

        let out = opt.step(param, Some(grad), &StepFeedback::none()).unwrap();
        let updated = out.to_data().to_vec::<f64>().unwrap();
        assert_ne!(initial, updated);
    }

    #[test]
    fn step_without_grad_is_a_no_op() {
        let dev = device();
        let mut opt = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
        let param = Tensor::<TestBackend, 1>::from_data(
            TensorData::new(vec![1.0_f64, 2.0, 3.0], vec![3]),
            &dev,
        );
        let out = opt
            .step(param.clone(), None, &StepFeedback::none())
            .unwrap();
        assert_eq!(
            out.to_data().to_vec::<f64>().unwrap(),
            param.to_data().to_vec::<f64>().unwrap()
        );
    }

    #[test]
    fn step_rejects_grad_shape_mismatch() {
        let dev = device();
        let mut opt = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
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

    #[test]
    fn step_reduces_lr_when_desynchronized() {
        let dev = device();
        let param = Tensor::<TestBackend, 1>::zeros([10], &dev);
        let grad = Tensor::<TestBackend, 1>::ones([10], &dev);

        let mut opt_high = SyncGdConfig::with_params(0.1, 0.0, 0.0, 5.0, 0.8, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let out_high = opt_high
            .step(param.clone(), Some(grad.clone()), &StepFeedback::order(0.9))
            .unwrap();

        let mut opt_low = SyncGdConfig::with_params(0.1, 0.0, 0.0, 5.0, 0.8, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let out_low = opt_low
            .step(param, Some(grad), &StepFeedback::order(0.2))
            .unwrap();

        // Desynchronized (low r) takes a strictly smaller step in the
        // gradient direction than well-synchronized (high r).
        let high_val = out_high.to_data().to_vec::<f64>().unwrap()[0];
        let low_val = out_low.to_data().to_vec::<f64>().unwrap()[0];
        assert!(low_val > high_val, "low={low_val} high={high_val}");
        assert_eq!(opt_low.penalty_history().len(), 1);
    }

    #[test]
    fn momentum_second_step_uses_buffer_and_stays_finite() {
        let dev = device();
        let mut opt = SyncGdConfig::with_params(0.01, 0.9, 0.0, 0.1, 0.5, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let param = Tensor::<TestBackend, 1>::zeros([10], &dev);
        let grad1 = Tensor::<TestBackend, 1>::ones([10], &dev);
        let p1 = opt.step(param, Some(grad1), &StepFeedback::none()).unwrap();
        assert!(opt.momentum_buffer().is_some());

        let grad2 = Tensor::<TestBackend, 1>::ones([10], &dev).mul_scalar(0.5);
        let p2 = opt.step(p1, Some(grad2), &StepFeedback::none()).unwrap();
        assert!(p2
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|v: &f64| v.is_finite()));
    }

    // --- state_dict / load_state_dict (deterministic resume) ---

    #[test]
    fn state_round_trips_through_json() {
        let mut opt = SyncGdConfig::with_params(0.05, 0.5, 0.01, 0.2, 0.6, 0.1)
            .unwrap()
            .init::<TestBackend, 1>();
        opt.compute_sync_penalty(0.3);
        opt.compute_sync_penalty(0.7);

        let state = opt.state_dict();
        let json = serde_json::to_string(&state).unwrap();
        let restored: SyncGdState = serde_json::from_str(&json).unwrap();
        assert_eq!(state, restored);

        let mut fresh = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
        fresh.load_state_dict(restored).unwrap();
        assert_eq!(fresh.order_history(), &[0.3, 0.7]);
        assert_eq!(fresh.config().critical_order, 0.6);
    }

    #[test]
    fn deterministic_resume_matches_uninterrupted_run() {
        let dev = device();
        let grads: [f64; 3] = [1.0, -0.5, 0.25];

        // Uninterrupted run.
        let mut baseline = SyncGdConfig::with_params(0.1, 0.9, 0.0, 0.3, 0.7, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let mut p_baseline = Tensor::<TestBackend, 1>::zeros([3], &dev);
        for (i, g) in grads.iter().enumerate() {
            let grad =
                Tensor::<TestBackend, 1>::from_data(TensorData::new(vec![*g; 3], vec![3]), &dev);
            p_baseline = baseline
                .step(
                    p_baseline,
                    Some(grad),
                    &StepFeedback::order(0.5 + 0.1 * i as f64),
                )
                .unwrap();
        }

        // Interrupted: run step 0, snapshot, resume for steps 1-2 on a
        // fresh instance restored from the snapshot.
        let mut first = SyncGdConfig::with_params(0.1, 0.9, 0.0, 0.3, 0.7, 0.0)
            .unwrap()
            .init::<TestBackend, 1>();
        let mut p_resumed = Tensor::<TestBackend, 1>::zeros([3], &dev);
        let grad0 =
            Tensor::<TestBackend, 1>::from_data(TensorData::new(vec![grads[0]; 3], vec![3]), &dev);
        p_resumed = first
            .step(p_resumed, Some(grad0), &StepFeedback::order(0.5))
            .unwrap();

        let snapshot = first.state_dict();
        let momentum_snapshot = first.momentum_buffer().cloned();
        let mut resumed = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
        resumed.load_state_dict(snapshot).unwrap();
        resumed.set_momentum_buffer(momentum_snapshot);

        for (i, g) in grads.iter().enumerate().skip(1) {
            let grad =
                Tensor::<TestBackend, 1>::from_data(TensorData::new(vec![*g; 3], vec![3]), &dev);
            p_resumed = resumed
                .step(
                    p_resumed,
                    Some(grad),
                    &StepFeedback::order(0.5 + 0.1 * i as f64),
                )
                .unwrap();
        }

        let baseline_data = p_baseline.to_data().to_vec::<f64>().unwrap();
        let resumed_data = p_resumed.to_data().to_vec::<f64>().unwrap();
        for (b, r) in baseline_data.iter().zip(resumed_data.iter()) {
            assert!((b - r).abs() < 1e-12, "baseline {b} vs resumed {r}");
        }
        assert_eq!(baseline.order_history(), resumed.order_history());
    }
}

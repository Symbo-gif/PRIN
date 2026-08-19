//! Order-parameter feedback shared by the oscillator-aware optimizers
//! ([`crate::sync_gd`], [`crate::rip`], [`crate::scalr`]), and the "thin
//! torch-side optimizer contract" all three implement.
//!
//! PRINet 3.0's synchronized optimizers (`nn/optimizers.py`) read the
//! network's instantaneous Kuramoto order parameter (or, for SCALR's Q3
//! hierarchical mode, per-frequency-band order parameters) each `step()`
//! call and fold it into the update — a barrier penalty
//! ([`crate::sync_gd::SyncGd`]), a learning-rate scale
//! ([`crate::scalr::Scalr`]), or (via phase/amplitude rather than a scalar
//! order parameter) a Hebbian coupling delta ([`crate::rip::Rip`]).
//! [`StepFeedback`] is the shared per-step input type; [`OrderParameter`] is
//! SCALR's richer global-or-per-group value; [`OscillatorOptimizer`] is the
//! shared step/state-dict contract. Per the Rebuild Planning Document's
//! `nn/optimizers.py` mapping ("SCALR/RIP/SyncGD need order-parameter
//! feedback → Rust computes metrics, Python optimizer classes stay thin"),
//! this trait is the seam a future thin `torch.optim.Optimizer` wrapper
//! (WP-025) marshals tensors through: every numerical decision here is
//! computed in Rust, so the Python side stays a thin per-parameter loop.

use std::collections::HashMap;

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use serde::de::DeserializeOwned;
use serde::Serialize;

use crate::error::TrainError;

/// The Kuramoto order parameter fed into a [`crate::scalr::Scalr`] step:
/// either a single value applied to every parameter group, or a per-group
/// dictionary (PRINet 3.0 SCALR's Q3 "per-frequency lr scaling",
/// `Union[float, Dict[str, float]]`).
#[derive(Clone, Debug, PartialEq)]
pub enum OrderParameter {
    /// A single order parameter applied to every group.
    Global(f64),
    /// Per-group order parameters, keyed by group name.
    PerGroup(HashMap<String, f64>),
}

impl OrderParameter {
    /// Resolve the order parameter to use for the named group.
    ///
    /// Mirrors `SCALROptimizer.step`'s dict resolution: an unknown group
    /// name (including every name when `self` is [`Self::Global`], which
    /// has no groups) falls back to [`Self::global`].
    pub fn resolve(&self, group: &str) -> f64 {
        match self {
            OrderParameter::Global(r) => *r,
            OrderParameter::PerGroup(map) => *map.get(group).unwrap_or(&self.global()),
        }
    }

    /// The group-independent fallback value: PRINet 3.0's
    /// `sum(order_parameter.values()) / max(len(order_parameter), 1)` for a
    /// dict, or the value itself for a scalar. Used both as the per-group
    /// fallback in [`Self::resolve`] and as the value SCALR's shared
    /// bookkeeping (step count, order history, oscillation decay, adaptive
    /// `r_min`) tracks regardless of which group is being stepped.
    pub fn global(&self) -> f64 {
        match self {
            OrderParameter::Global(r) => *r,
            OrderParameter::PerGroup(map) if map.is_empty() => 0.0,
            OrderParameter::PerGroup(map) => map.values().sum::<f64>() / map.len() as f64,
        }
    }
}

/// Feedback available to an oscillator-aware optimizer step: whatever
/// subset of the network's instantaneous coherence state PRINet 3.0's
/// reference `step()` methods accept. Every field is optional because the
/// reference defaults every feedback argument to `None` (plain gradient
/// descent when no oscillator state is supplied).
#[derive(Clone, Debug, Default)]
pub struct StepFeedback<B: Backend> {
    /// Global Kuramoto order parameter ([`crate::sync_gd::SyncGd`],
    /// [`crate::scalr::Scalr`]'s [`OscillatorOptimizer`] entry point). For
    /// SCALR's per-group dict mode, use
    /// [`crate::scalr::Scalr::step_with_order_parameter`] instead, which
    /// takes an [`OrderParameter`] directly.
    pub order_parameter: Option<f64>,
    /// Per-oscillator phase, shape `[batch, n_oscillators]`
    /// ([`crate::rip::Rip`]).
    pub phase: Option<Tensor<B, 2>>,
    /// Per-oscillator amplitude, shape `[batch, n_oscillators]`
    /// ([`crate::rip::Rip`]).
    pub amplitude: Option<Tensor<B, 2>>,
}

impl<B: Backend> StepFeedback<B> {
    /// No feedback: plain gradient descent.
    pub fn none() -> Self {
        Self::default()
    }

    /// A global order parameter, no phase/amplitude.
    pub fn order(order_parameter: f64) -> Self {
        Self {
            order_parameter: Some(order_parameter),
            ..Self::default()
        }
    }

    /// Phase/amplitude for a Hebbian update, no order parameter.
    pub fn phase_amplitude(phase: Tensor<B, 2>, amplitude: Tensor<B, 2>) -> Self {
        Self {
            phase: Some(phase),
            amplitude: Some(amplitude),
            ..Self::default()
        }
    }
}

/// The uniform contract every oscillator-aware optimizer implements: apply
/// one update to a single parameter tensor given its gradient and whatever
/// oscillator feedback the algorithm uses, and expose a serializable state
/// snapshot for deterministic checkpoint/resume.
///
/// This is the seam a future thin `torch.optim.Optimizer` subclass
/// (WP-025) bridges to: the Python side stays a thin per-parameter loop
/// over `torch.Tensor`s; every numerical decision (lr scaling, barrier
/// penalties, Hebbian deltas) is computed here. Momentum buffers (where the
/// optimizer has one) are plain [`Tensor`] fields outside `State` — the
/// same split PRIN already uses for trainable-module checkpoints
/// (`burn::record`) — reached via each optimizer's own accessors; `State`
/// covers exactly the step-dependent scalar/history bookkeeping that has no
/// natural Burn-tensor home.
pub trait OscillatorOptimizer<B: Backend, const D: usize> {
    /// The serializable state snapshot type for [`Self::state_dict`] /
    /// [`Self::load_state_dict`].
    type State: Serialize + DeserializeOwned;

    /// Apply one update to `param` given its gradient `grad` (`None` when
    /// the parameter received no gradient this step, matching PRINet 3.0's
    /// `if p.grad is None: continue`) and any available oscillator
    /// feedback.
    ///
    /// # Errors
    ///
    /// Returns a [`TrainError`] if `grad`'s shape does not match `param`'s.
    fn step(
        &mut self,
        param: Tensor<B, D>,
        grad: Option<Tensor<B, D>>,
        feedback: &StepFeedback<B>,
    ) -> Result<Tensor<B, D>, TrainError>;

    /// Snapshot the optimizer's step-dependent state (hyperparameters, step
    /// counters, histories, adaptive thresholds) for deterministic
    /// checkpoint/resume.
    fn state_dict(&self) -> Self::State;

    /// Restore step-dependent state from a snapshot produced by
    /// [`Self::state_dict`].
    ///
    /// # Errors
    ///
    /// Returns a [`TrainError`] if `state`'s hyperparameters are invalid
    /// (the same validation [`Self::state_dict`]'s originating constructor
    /// applied, re-run because a deserialized `State` is untrusted input at
    /// a public boundary).
    fn load_state_dict(&mut self, state: Self::State) -> Result<(), TrainError>;
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;

    #[test]
    fn global_resolve_ignores_group_name() {
        let order = OrderParameter::Global(0.42);
        assert_eq!(order.resolve("anything"), 0.42);
        assert_eq!(order.resolve(""), 0.42);
    }

    #[test]
    fn global_of_global_is_the_value_itself() {
        assert_eq!(OrderParameter::Global(0.7).global(), 0.7);
    }

    #[test]
    fn per_group_resolve_falls_back_to_mean_for_unknown_group() {
        let mut map = HashMap::new();
        map.insert("a".to_string(), 0.2);
        map.insert("b".to_string(), 0.8);
        let order = OrderParameter::PerGroup(map);
        assert_eq!(order.resolve("a"), 0.2);
        assert_eq!(order.resolve("b"), 0.8);
        assert!((order.resolve("unknown") - 0.5).abs() < 1e-12);
        assert!((order.global() - 0.5).abs() < 1e-12);
    }

    #[test]
    fn per_group_empty_map_resolves_to_zero() {
        let order = OrderParameter::PerGroup(HashMap::new());
        assert_eq!(order.global(), 0.0);
        assert_eq!(order.resolve("anything"), 0.0);
    }

    #[test]
    fn step_feedback_constructors() {
        let none = StepFeedback::<TestBackend>::none();
        assert!(none.order_parameter.is_none());
        assert!(none.phase.is_none());
        assert!(none.amplitude.is_none());

        let order = StepFeedback::<TestBackend>::order(0.6);
        assert_eq!(order.order_parameter, Some(0.6));
        assert!(order.phase.is_none());

        let device = Default::default();
        let phase = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.1_f64, 0.2], vec![1, 2]),
            &device,
        );
        let amplitude = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![1.0_f64, 1.0], vec![1, 2]),
            &device,
        );
        let pa = StepFeedback::phase_amplitude(phase, amplitude);
        assert!(pa.order_parameter.is_none());
        assert!(pa.phase.is_some());
        assert!(pa.amplitude.is_some());
    }
}

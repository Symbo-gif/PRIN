//! Resonance-Induced Plasticity (RIP) optimizer (PRINet 3.0 `RIPOptimizer`).
//!
//! Implements a Hebbian-style update rule for a square coupling matrix,
//! driven by phase coherence between connected oscillators:
//!
//! ```text
//! ΔK[i,j] = η · cos(φ[i] − φ[j]) · |r[j]| · (r_target − r[i])
//! ```
//!
//! optionally combined with a plain gradient-descent component when a
//! gradient is supplied. The coupling matrix's diagonal is always zeroed
//! after a Hebbian update (no self-coupling).
//!
//! **Documented deviation — fixed square shape.** PRINet 3.0's
//! `RIPOptimizer` is a generic `torch.optim.Optimizer` whose `step` accepts
//! any parameter list and silently skips the Hebbian term for any parameter
//! that is not a square 2-D tensor matching `phase`'s width ("This
//! optimizer updates only coupling-type parameters", `nn/optimizers.py`
//! docstring) while still applying the plain gradient-descent component to
//! every parameter. [`Rip`] instead fixes `n_oscillators` at construction
//! ([`RipConfig`]) — matching the class's own stated single-purpose
//! contract, and letting Rust's type system guarantee the coupling shape
//! statically — and returns a typed [`TrainError::ShapeMismatch`] if a
//! caller passes a mismatched `phase`/`amplitude` instead of silently
//! skipping the Hebbian term, per Coding Standards §2.2 ("validate public
//! inputs at every public boundary"). The Hebbian formula and the
//! plain-gradient/diagonal-zeroing behavior are otherwise a direct port.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::feedback::{OscillatorOptimizer, StepFeedback};
//! use prin_train::rip::RipConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let mut opt = RipConfig::with_params(8, 0.1, 1.0).unwrap().init::<Backend>();
//! let coupling = Tensor::<Backend, 2>::zeros([8, 8], &device);
//! let phase = Tensor::<Backend, 2>::zeros([1, 8], &device);
//! let amplitude = Tensor::<Backend, 2>::ones([1, 8], &device);
//!
//! let updated = opt
//!     .step(coupling, None, &StepFeedback::phase_amplitude(phase, amplitude))
//!     .unwrap();
//! assert_eq!(updated.dims(), [8, 8]);
//! ```

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use serde::{Deserialize, Serialize};

use crate::error::TrainError;
use crate::feedback::{OscillatorOptimizer, StepFeedback};
use crate::support::check_dims;

/// Validated hyperparameters for [`Rip`].
#[derive(Clone, Debug, PartialEq)]
pub struct RipConfig {
    /// Number of oscillators the coupling matrix couples (matrix is
    /// `[n_oscillators, n_oscillators]`).
    pub n_oscillators: usize,
    /// Learning rate η.
    pub lr: f64,
    /// Target amplitude `r_target` for the Hebbian rule.
    pub target_amplitude: f64,
}

impl RipConfig {
    /// A validated configuration with PRINet 3.0's default hyperparameters
    /// (`lr=0.01, target_amplitude=1.0`).
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(n_oscillators: usize) -> Result<Self, TrainError> {
        Self::with_params(n_oscillators, 0.01, 1.0)
    }

    /// A validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` is zero,
    /// [`TrainError::InvalidLearningRate`] if `lr < 0`, or
    /// [`TrainError::InvalidTargetAmplitude`] if `target_amplitude <= 0`.
    pub fn with_params(
        n_oscillators: usize,
        lr: f64,
        target_amplitude: f64,
    ) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        if !(lr.is_finite() && lr >= 0.0) {
            return Err(TrainError::InvalidLearningRate { value: lr });
        }
        if !(target_amplitude.is_finite() && target_amplitude > 0.0) {
            return Err(TrainError::InvalidTargetAmplitude {
                value: target_amplitude,
            });
        }
        Ok(Self {
            n_oscillators,
            lr,
            target_amplitude,
        })
    }

    /// Build a [`Rip`] optimizer.
    pub fn init<B: Backend>(&self) -> Rip<B> {
        Rip {
            config: self.clone(),
            _backend: std::marker::PhantomData,
        }
    }
}

/// Serializable snapshot of [`Rip`]'s configuration. `Rip` itself holds no
/// step-dependent state beyond its hyperparameters (the reference
/// `RIPOptimizer` tracks no history/momentum), so this is exactly
/// [`RipConfig`].
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct RipState {
    /// Number of oscillators.
    pub n_oscillators: usize,
    /// Learning rate η.
    pub lr: f64,
    /// Target amplitude `r_target`.
    pub target_amplitude: f64,
}

/// Resonance-Induced Plasticity optimizer. Construct via
/// [`RipConfig::init`].
///
/// See the module docs for the exact Hebbian update equation.
#[derive(Debug, Clone)]
pub struct Rip<B: Backend> {
    config: RipConfig,
    _backend: std::marker::PhantomData<B>,
}

impl<B: Backend> Rip<B> {
    /// The active configuration.
    pub fn config(&self) -> &RipConfig {
        &self.config
    }

    /// Apply the Hebbian coupling update to `coupling`, given the
    /// batch-mean `phase`/`amplitude` (each `[batch, n_oscillators]`), then
    /// zero the diagonal.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `coupling` is not
    /// `[n_oscillators, n_oscillators]` or `phase`/`amplitude`'s width is
    /// not `n_oscillators`, or if `phase` and `amplitude` do not share a
    /// shape.
    fn apply_hebbian(
        &self,
        coupling: Tensor<B, 2>,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let n = self.config.n_oscillators;
        check_dims("coupling", coupling.dims(), [n, n])?;
        let p_dims = phase.dims();
        check_dims("phase", p_dims, [p_dims[0], n])?;
        check_dims("amplitude", amplitude.dims(), p_dims)?;
        let device = coupling.device();

        // Batch-mean phase/amplitude, PRINet 3.0's `phase.mean(dim=0)`.
        let ph = phase.mean_dim(0); // [1, n]
        let amp = amplitude.mean_dim(0); // [1, n]

        let ph_row = ph.clone().reshape([1, n]);
        let ph_col = ph.reshape([n, 1]);
        let cos_coherence = (ph_row - ph_col).cos(); // [n, n]

        let amp_j = amp.clone().reshape([1, n]);
        let deficit = amp
            .reshape([n, 1])
            .mul_scalar(-1.0)
            .add_scalar(self.config.target_amplitude); // [n, 1]

        let delta = (cos_coherence * amp_j * deficit).mul_scalar(self.config.lr);
        let updated = coupling + delta;

        // Zero the diagonal (no self-coupling): multiply by a zero-diagonal
        // mask rather than an in-place `fill_diagonal_`, matching the
        // functional-tensor style used throughout `prin-train`.
        let mask = Tensor::<B, 2>::ones([n, n], &device) - Tensor::<B, 2>::eye(n, &device);
        Ok(updated * mask)
    }
}

impl<B: Backend> OscillatorOptimizer<B, 2> for Rip<B> {
    type State = RipState;

    fn step(
        &mut self,
        param: Tensor<B, 2>,
        grad: Option<Tensor<B, 2>>,
        feedback: &StepFeedback<B>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let mut updated = param;
        if let Some(grad) = grad {
            check_dims("grad", grad.dims(), updated.dims())?;
            updated = updated - grad.mul_scalar(self.config.lr);
        }
        if let (Some(phase), Some(amplitude)) = (&feedback.phase, &feedback.amplitude) {
            updated = self.apply_hebbian(updated, phase.clone(), amplitude.clone())?;
        }
        Ok(updated)
    }

    fn state_dict(&self) -> RipState {
        RipState {
            n_oscillators: self.config.n_oscillators,
            lr: self.config.lr,
            target_amplitude: self.config.target_amplitude,
        }
    }

    fn load_state_dict(&mut self, state: RipState) -> Result<(), TrainError> {
        self.config =
            RipConfig::with_params(state.n_oscillators, state.lr, state.target_amplitude)?;
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
    fn zero_oscillators_rejected() {
        assert!(matches!(
            RipConfig::new(0).unwrap_err(),
            TrainError::EmptyBand {
                name: "oscillators"
            }
        ));
    }

    #[test]
    fn negative_lr_rejected() {
        assert!(matches!(
            RipConfig::with_params(5, -0.01, 1.0).unwrap_err(),
            TrainError::InvalidLearningRate { .. }
        ));
    }

    #[test]
    fn non_positive_target_amplitude_rejected() {
        assert!(matches!(
            RipConfig::with_params(5, 0.01, 0.0).unwrap_err(),
            TrainError::InvalidTargetAmplitude { .. }
        ));
        assert!(matches!(
            RipConfig::with_params(5, 0.01, -1.0).unwrap_err(),
            TrainError::InvalidTargetAmplitude { .. }
        ));
    }

    // --- step: plain gradient component ---

    #[test]
    fn basic_step_with_gradient_updates_parameters() {
        let dev = device();
        let mut opt = RipConfig::new(10).unwrap().init::<TestBackend>();
        let param = Tensor::<TestBackend, 2>::zeros([10, 10], &dev);
        let grad = Tensor::<TestBackend, 2>::ones([10, 10], &dev);
        let out = opt.step(param, Some(grad), &StepFeedback::none()).unwrap();
        assert!(out
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|v: &f64| (v + 0.01).abs() < 1e-12));
    }

    #[test]
    fn step_without_grad_or_feedback_is_a_no_op() {
        let dev = device();
        let mut opt = RipConfig::new(4).unwrap().init::<TestBackend>();
        let param = Tensor::<TestBackend, 2>::from_data(
            TensorData::new((0..16).map(|i| i as f64).collect::<Vec<_>>(), vec![4, 4]),
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

    // --- Hebbian update ---

    #[test]
    fn hebbian_update_zeroes_diagonal() {
        let dev = device();
        let mut opt = RipConfig::with_params(8, 0.1, 1.0)
            .unwrap()
            .init::<TestBackend>();
        let coupling = Tensor::<TestBackend, 2>::zeros([8, 8], &dev);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 8], &dev); // all synchronized
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 8], &dev);

        let updated = opt
            .step(
                coupling,
                None,
                &StepFeedback::phase_amplitude(phase, amplitude),
            )
            .unwrap();
        let data = updated.to_data().to_vec::<f64>().unwrap();
        for i in 0..8 {
            assert!(data[i * 8 + i].abs() < 1e-12, "diagonal[{i}] not zeroed");
        }
    }

    #[test]
    fn hebbian_update_synchronized_phase_at_target_amplitude_is_zero() {
        // phase all-equal => cos_coherence == 1 everywhere; amplitude ==
        // target => deficit == 0 everywhere => delta == 0 everywhere, and
        // the diagonal mask leaves the (already-zero) result unchanged.
        let dev = device();
        let mut opt = RipConfig::with_params(5, 0.5, 1.0)
            .unwrap()
            .init::<TestBackend>();
        let coupling = Tensor::<TestBackend, 2>::zeros([5, 5], &dev);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 5], &dev);
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 5], &dev);

        let updated = opt
            .step(
                coupling,
                None,
                &StepFeedback::phase_amplitude(phase, amplitude),
            )
            .unwrap();
        for v in updated.to_data().to_vec::<f64>().unwrap() {
            assert!(v.abs() < 1e-12, "expected zero delta, got {v}");
        }
    }

    #[test]
    fn hebbian_and_gradient_components_are_additive() {
        let dev = device();
        let mut opt = RipConfig::with_params(4, 0.1, 1.0)
            .unwrap()
            .init::<TestBackend>();
        let coupling = Tensor::<TestBackend, 2>::zeros([4, 4], &dev);
        let grad = Tensor::<TestBackend, 2>::ones([4, 4], &dev);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 4], &dev);
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 4], &dev);

        let combined = opt
            .clone()
            .step(
                coupling.clone(),
                Some(grad.clone()),
                &StepFeedback::phase_amplitude(phase.clone(), amplitude.clone()),
            )
            .unwrap();
        let grad_only = opt
            .clone()
            .step(coupling.clone(), Some(grad), &StepFeedback::none())
            .unwrap();
        let hebbian_only = opt
            .step(
                coupling,
                None,
                &StepFeedback::phase_amplitude(phase, amplitude),
            )
            .unwrap();

        // grad_only is -lr everywhere (including the diagonal, since no
        // Hebbian branch runs to mask it); hebbian_only is zero here
        // (synchronized, at-target case). Off-diagonal, combined must equal
        // their sum; on the diagonal, combined is always forced to zero by
        // the Hebbian branch's mask (PRINet 3.0's `p.fill_diagonal_(0.0)`
        // applies to the *final* `p`, after the grad step already ran) —
        // exactly the documented "zero the diagonal of the final p"
        // behavior, not an additive-sum property.
        let c = combined.to_data().to_vec::<f64>().unwrap();
        let g = grad_only.to_data().to_vec::<f64>().unwrap();
        let h = hebbian_only.to_data().to_vec::<f64>().unwrap();
        for i in 0..4 {
            for j in 0..4 {
                let idx = i * 4 + j;
                if i == j {
                    assert!(c[idx].abs() < 1e-12, "diagonal[{i}] not zeroed: {}", c[idx]);
                } else {
                    assert!((c[idx] - (g[idx] + h[idx])).abs() < 1e-12);
                }
            }
        }
    }

    #[test]
    fn hebbian_rejects_non_square_coupling() {
        let dev = device();
        let mut opt = RipConfig::new(4).unwrap().init::<TestBackend>();
        let coupling = Tensor::<TestBackend, 2>::zeros([3, 4], &dev);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 4], &dev);
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let err = opt
            .step(
                coupling,
                None,
                &StepFeedback::phase_amplitude(phase, amplitude),
            )
            .unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "coupling",
                ..
            }
        ));
    }

    #[test]
    fn hebbian_rejects_phase_width_mismatch() {
        let dev = device();
        let mut opt = RipConfig::new(4).unwrap().init::<TestBackend>();
        let coupling = Tensor::<TestBackend, 2>::zeros([4, 4], &dev);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 5], &dev);
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 5], &dev);
        let err = opt
            .step(
                coupling,
                None,
                &StepFeedback::phase_amplitude(phase, amplitude),
            )
            .unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
    }

    // --- state_dict / load_state_dict ---

    #[test]
    fn state_round_trips_through_json() {
        let opt = RipConfig::with_params(6, 0.2, 0.9)
            .unwrap()
            .init::<TestBackend>();
        let state = opt.state_dict();
        let json = serde_json::to_string(&state).unwrap();
        let restored: RipState = serde_json::from_str(&json).unwrap();
        assert_eq!(state, restored);

        let mut fresh = RipConfig::new(1).unwrap().init::<TestBackend>();
        fresh.load_state_dict(restored).unwrap();
        assert_eq!(fresh.config().n_oscillators, 6);
        assert_eq!(fresh.config().lr, 0.2);
    }

    #[test]
    fn load_state_dict_revalidates() {
        let opt = RipConfig::new(4).unwrap().init::<TestBackend>();
        let mut bad_state = opt.state_dict();
        bad_state.lr = -1.0;
        let mut fresh = RipConfig::new(4).unwrap().init::<TestBackend>();
        assert!(matches!(
            fresh.load_state_dict(bad_state).unwrap_err(),
            TrainError::InvalidLearningRate { .. }
        ));
    }
}

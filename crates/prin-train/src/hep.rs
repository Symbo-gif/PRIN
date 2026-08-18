//! ±β Holomorphic Equilibrium Propagation (HEP) trainer.
//!
//! Burn rebuild of PRINet 3.0's `nn/hep.py::HolomorphicEPTrainer`, scoped to
//! its physics-level gradient estimator (the model-specific parts — a
//! `concept_proj` classification head, `named_parameters()` iteration over an
//! arbitrary model, and the SGD parameter update in `train_step` — are
//! model/optimizer concerns deferred to WP-027 and WP-024 respectively; see
//! "Scope" below).
//!
//! hEP estimates gradients from **equilibrium energy differences** rather
//! than backpropagation through time:
//!
//! 1. **Free phase**: run [`crate::layers::ResonanceLayer`] dynamics to
//!    equilibrium with no nudge (β = 0).
//! 2. **Positive nudge phase**: run to equilibrium while nudging the
//!    amplitude toward a target direction at strength `+β`.
//! 3. **Negative nudge phase**: same, at strength `−β`.
//! 4. **Coupling gradient**: the coupling matrix's energy is holomorphic in
//!    the (real, zero-phase — see below) oscillator state, so its gradient
//!    has the closed form `∂E/∂K[i,j] = -Re(z_i* z_j)`; evaluating this at
//!    the ±β equilibria and taking the symmetric difference gives
//!    [`HolomorphicEp::coupling_gradient`]:
//!
//! ```text
//! ∇_K L ≈ (1 / 2β) · (E_coupling(z⁺β) − E_coupling(z⁻β))
//!       = (1 / 2β) · (outer(amp⁻β) − outer(amp⁺β))   [outer(a) = mean_batch(aᵀa)]
//! ```
//!
//! # Preserved reference behavior — zero-phase complex state
//!
//! PRINet 3.0's `compute_hep_gradients` builds `z` from the equilibrium
//! amplitude with the phase forced to zero (`z = amp * exp(i·0)`) before
//! computing energies, even though the equilibrium itself has a genuine
//! nonzero phase. This is not a numerical-precision hazard in the amendment
//! #14/#16/#17 sense — it is literally what the reference's hEP gradient
//! estimator computes — so [`HolomorphicEp::coupling_gradient`] preserves it
//! exactly via [`crate::activations::ComplexTensor::from_real`] rather than
//! carrying the equilibrium's actual phase into the energy evaluation.
//!
//! # Scope: generalized nudge target
//!
//! PRINet 3.0's nudge computes `target_direction` from a concrete
//! `concept_proj` linear layer (`target_onehot @ concept_proj.weight`).
//! `prin-train` does not yet own a classification head (WP-027, "trainable
//! stack integration and Phase 4 gate"), so [`HolomorphicEp::run_to_equilibrium`]
//! takes the nudge target direction as an explicit `[batch, n_oscillators]`
//! tensor supplied by the caller — the physics-level ±β equilibrium
//! primitive this module implements generalizes over any concrete
//! target-direction source, including a future `concept_proj` layer.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::hep::HolomorphicEpConfig;
//! use prin_train::layers::ResonanceLayerConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let mut seed = Seed::new(0, 0);
//! let layer = ResonanceLayerConfig::new(4, 6)
//!     .unwrap()
//!     .init::<Backend>(&device, &mut seed);
//! let hep = HolomorphicEpConfig::with_params(0.1, 5, 3).unwrap().init();
//!
//! let x = Tensor::<Backend, 2>::ones([2, 6], &device);
//! let target_direction = Tensor::<Backend, 2>::ones([2, 4], &device);
//! let grad = hep.coupling_gradient(&layer, x, target_direction).unwrap();
//! assert_eq!(grad.dims(), [4, 4]);
//! ```

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;

use crate::activations::ComplexTensor;
use crate::energy::HolomorphicEnergy;
use crate::error::TrainError;
use crate::layers::{ResonanceLayer, ResonanceState};
use crate::support::check_dims;

/// Validated hyperparameters for [`HolomorphicEp`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `free_steps=50,
/// nudge_steps=20`.
#[derive(Clone, Debug, PartialEq)]
pub struct HolomorphicEpConfig {
    /// Nudge strength. Smaller `beta` gives more accurate but noisier
    /// gradients. PRINet 3.0's documented typical range: `[0.01, 0.5]`.
    pub beta: f64,
    /// Integration steps for the free-phase equilibrium.
    pub free_steps: usize,
    /// Integration steps for each nudge-phase equilibrium.
    pub nudge_steps: usize,
}

impl HolomorphicEpConfig {
    /// A validated configuration with PRINet 3.0's default step counts.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidBeta`] if `beta` is non-finite or not
    /// strictly positive.
    pub fn new(beta: f64) -> Result<Self, TrainError> {
        Self::with_params(beta, 50, 20)
    }

    /// A validated configuration with explicit step counts.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidBeta`] if `beta` is non-finite or not
    /// strictly positive, or [`TrainError::InvalidStepCount`] if either step
    /// count is zero.
    pub fn with_params(
        beta: f64,
        free_steps: usize,
        nudge_steps: usize,
    ) -> Result<Self, TrainError> {
        if !beta.is_finite() || beta <= 0.0 {
            return Err(TrainError::InvalidBeta { value: beta });
        }
        if free_steps < 1 {
            return Err(TrainError::InvalidStepCount {
                name: "free_steps",
                value: free_steps,
            });
        }
        if nudge_steps < 1 {
            return Err(TrainError::InvalidStepCount {
                name: "nudge_steps",
                value: nudge_steps,
            });
        }
        Ok(Self {
            beta,
            free_steps,
            nudge_steps,
        })
    }

    /// Build a [`HolomorphicEp`] from this configuration.
    pub fn init(&self) -> HolomorphicEp {
        HolomorphicEp {
            beta: self.beta,
            free_steps: self.free_steps,
            nudge_steps: self.nudge_steps,
        }
    }
}

/// ±β Holomorphic Equilibrium Propagation gradient estimator.
///
/// See the module docs for the estimator and its two documented scoping
/// decisions. Construct via [`HolomorphicEpConfig::init`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HolomorphicEp {
    beta: f64,
    free_steps: usize,
    nudge_steps: usize,
}

impl HolomorphicEp {
    /// Nudge strength.
    pub fn beta(&self) -> f64 {
        self.beta
    }

    /// Free-phase integration step count.
    pub fn free_steps(&self) -> usize {
        self.free_steps
    }

    /// Nudge-phase integration step count.
    pub fn nudge_steps(&self) -> usize {
        self.nudge_steps
    }

    /// Run `layer` dynamics for `n_steps`, optionally nudging the amplitude
    /// toward `target_direction` at strength `nudge_beta` after every step:
    /// `amplitude += nudge_beta · dt · target_direction`.
    ///
    /// # Errors
    ///
    /// Propagates [`TrainError::ShapeMismatch`] from [`ResonanceLayer::init_state`]
    /// / [`ResonanceLayer::step`], or returns it directly if a supplied
    /// nudge direction's shape does not match the running amplitude's.
    pub fn run_to_equilibrium<B: Backend>(
        &self,
        layer: &ResonanceLayer<B>,
        x: Tensor<B, 2>,
        n_steps: usize,
        nudge: Option<(f64, Tensor<B, 2>)>,
    ) -> Result<ResonanceState<B>, TrainError> {
        let mut state = layer.init_state(x)?;
        for _ in 0..n_steps {
            state = layer.step(state)?;
            if let Some((nudge_beta, ref direction)) = nudge {
                let (phase, amplitude, frequency) = state.into_parts();
                check_dims("nudge_direction", direction.dims(), amplitude.dims())?;
                let nudged = amplitude + direction.clone().mul_scalar(nudge_beta * layer.dt());
                state = ResonanceState::new(phase, nudged, frequency)?;
            }
        }
        Ok(state)
    }

    /// Physics energy (β=0, no task term) of the free-phase equilibrium —
    /// a diagnostic analogue of PRINet 3.0's `free_loss`, which used
    /// task-specific `concept_proj` logits this crate does not yet own (see
    /// the module docs' "Scope" section).
    ///
    /// The equilibrium's phase is forced to zero before energy evaluation,
    /// preserving PRINet 3.0's reference behavior — see the module docs'
    /// "Preserved reference behavior" section.
    ///
    /// # Errors
    ///
    /// See [`Self::run_to_equilibrium`] and [`HolomorphicEnergy::forward`].
    pub fn free_energy<B: Backend>(
        &self,
        layer: &ResonanceLayer<B>,
        x: Tensor<B, 2>,
        energy: &HolomorphicEnergy,
        coupling: Tensor<B, 2>,
    ) -> Result<Tensor<B, 1>, TrainError> {
        let free = self.run_to_equilibrium(layer, x, self.free_steps, None)?;
        let amp = free.into_parts().1;
        energy.forward(ComplexTensor::from_real(amp), coupling, None, 0.0)
    }

    /// Closed-form ±β coupling-gradient estimate.
    ///
    /// Runs the positive- and negative-nudge equilibria and evaluates
    /// PRINet 3.0's analytic outer-product formula:
    ///
    /// ```text
    /// ∇_K L ≈ (outer(amp⁻β) − outer(amp⁺β)) / (2β),  outer(a) = mean_batch(aᵀa)
    /// ```
    ///
    /// # Errors
    ///
    /// See [`Self::run_to_equilibrium`].
    pub fn coupling_gradient<B: Backend>(
        &self,
        layer: &ResonanceLayer<B>,
        x: Tensor<B, 2>,
        target_direction: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let pos = self.run_to_equilibrium(
            layer,
            x.clone(),
            self.nudge_steps,
            Some((self.beta, target_direction.clone())),
        )?;
        let neg = self.run_to_equilibrium(
            layer,
            x,
            self.nudge_steps,
            Some((-self.beta, target_direction)),
        )?;
        let amp_pos = pos.into_parts().1;
        let amp_neg = neg.into_parts().1;

        let batch_pos = amp_pos.dims()[0] as f64;
        let batch_neg = amp_neg.dims()[0] as f64;
        let outer_pos = amp_pos
            .clone()
            .transpose()
            .matmul(amp_pos)
            .div_scalar(batch_pos);
        let outer_neg = amp_neg
            .clone()
            .transpose()
            .matmul(amp_neg)
            .div_scalar(batch_neg);

        Ok((outer_neg - outer_pos).div_scalar(2.0 * self.beta))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;
    use prin_dynamics::Seed;

    type TestBackend = NdArray<f64>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn small_layer<B: Backend>(device: &B::Device) -> ResonanceLayer<B> {
        let mut seed = Seed::new(41, 0);
        crate::layers::ResonanceLayerConfig::new(4, 3)
            .unwrap()
            .init(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn non_positive_beta_rejected() {
        assert!(matches!(
            HolomorphicEpConfig::new(0.0).unwrap_err(),
            TrainError::InvalidBeta { value } if value == 0.0
        ));
        assert!(matches!(
            HolomorphicEpConfig::new(-0.1).unwrap_err(),
            TrainError::InvalidBeta { .. }
        ));
        assert!(matches!(
            HolomorphicEpConfig::new(f64::NAN).unwrap_err(),
            TrainError::InvalidBeta { .. }
        ));
    }

    #[test]
    fn zero_step_counts_rejected() {
        assert!(matches!(
            HolomorphicEpConfig::with_params(0.1, 0, 20).unwrap_err(),
            TrainError::InvalidStepCount {
                name: "free_steps",
                value: 0
            }
        ));
        assert!(matches!(
            HolomorphicEpConfig::with_params(0.1, 50, 0).unwrap_err(),
            TrainError::InvalidStepCount {
                name: "nudge_steps",
                value: 0
            }
        ));
    }

    #[test]
    fn default_config_matches_reference_step_counts() {
        let cfg = HolomorphicEpConfig::new(0.1).unwrap();
        assert_eq!(cfg.free_steps, 50);
        assert_eq!(cfg.nudge_steps, 20);
    }

    // --- Accessors ---

    #[test]
    fn accessors_report_resolved_values() {
        let hep = HolomorphicEpConfig::with_params(0.2, 7, 4).unwrap().init();
        assert!((hep.beta() - 0.2).abs() < 1e-15);
        assert_eq!(hep.free_steps(), 7);
        assert_eq!(hep.nudge_steps(), 4);
    }

    // --- run_to_equilibrium ---

    #[test]
    fn run_to_equilibrium_without_nudge_matches_plain_integrate() {
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.1, 5, 3).unwrap().init();
        let x = Tensor::<TestBackend, 2>::ones([2, 3], &dev);

        let via_hep = hep.run_to_equilibrium(&layer, x.clone(), 5, None).unwrap();
        let state = layer.init_state(x).unwrap();
        let via_layer = layer.integrate(state, 5).unwrap();

        let a = via_hep
            .amplitude()
            .clone()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let b = via_layer
            .amplitude()
            .clone()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        for (x, y) in a.iter().zip(b.iter()) {
            assert!((x - y).abs() < 1e-12);
        }
    }

    #[test]
    fn positive_nudge_increases_amplitude_relative_to_free_run() {
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.2, 5, 5).unwrap().init();
        let x = Tensor::<TestBackend, 2>::ones([1, 3], &dev);
        let direction = Tensor::<TestBackend, 2>::ones([1, 4], &dev);

        let free = hep.run_to_equilibrium(&layer, x.clone(), 5, None).unwrap();
        let pos = hep
            .run_to_equilibrium(&layer, x, 5, Some((hep.beta(), direction)))
            .unwrap();

        let a_free: f64 = free
            .amplitude()
            .clone()
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .sum();
        let a_pos: f64 = pos
            .amplitude()
            .clone()
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .sum();
        assert!(
            a_pos > a_free,
            "positive nudge toward a positive direction should raise total amplitude"
        );
    }

    #[test]
    fn nudge_direction_shape_mismatch_rejected() {
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.1, 3, 3).unwrap().init();
        let x = Tensor::<TestBackend, 2>::ones([1, 3], &dev);
        let wrong_direction = Tensor::<TestBackend, 2>::ones([1, 2], &dev); // n_oscillators=4, not 2.
        let err = hep
            .run_to_equilibrium(&layer, x, 2, Some((0.1, wrong_direction)))
            .unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "nudge_direction",
                ..
            }
        ));
    }

    // --- free_energy ---

    #[test]
    fn free_energy_is_finite() {
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.1, 5, 3).unwrap().init();
        let energy = crate::energy::HolomorphicEnergyConfig::new(4)
            .unwrap()
            .init();
        let x = Tensor::<TestBackend, 2>::ones([2, 3], &dev);
        let coupling = Tensor::<TestBackend, 2>::zeros([4, 4], &dev);
        let e = hep.free_energy(&layer, x, &energy, coupling).unwrap();
        assert!(e.into_scalar().is_finite());
    }

    // --- coupling_gradient: shape / finiteness / closed-form regression ---

    #[test]
    fn coupling_gradient_has_expected_shape_and_is_finite() {
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.1, 5, 4).unwrap().init();
        let x = Tensor::<TestBackend, 2>::ones([3, 3], &dev);
        let direction = Tensor::<TestBackend, 2>::ones([3, 4], &dev);
        let grad = hep.coupling_gradient(&layer, x, direction).unwrap();
        assert_eq!(grad.dims(), [4, 4]);
        for v in grad.to_data().to_vec::<f64>().unwrap() {
            assert!(v.is_finite());
        }
    }

    #[test]
    fn coupling_gradient_matches_manual_outer_product_reference() {
        // Independent reimplementation of PRINet 3.0's
        // `grad = -(outer_pos - outer_neg) / (2*beta)` from the same ±beta
        // equilibrium amplitudes, computed by hand outside the tensor ops
        // `coupling_gradient` itself uses.
        let dev = device();
        let layer = small_layer::<TestBackend>(&dev);
        let hep = HolomorphicEpConfig::with_params(0.15, 4, 3).unwrap().init();
        let x = Tensor::<TestBackend, 2>::ones([2, 3], &dev);
        let direction = Tensor::<TestBackend, 2>::ones([2, 4], &dev);

        let pos = hep
            .run_to_equilibrium(
                &layer,
                x.clone(),
                hep.nudge_steps(),
                Some((hep.beta(), direction.clone())),
            )
            .unwrap();
        let neg = hep
            .run_to_equilibrium(
                &layer,
                x.clone(),
                hep.nudge_steps(),
                Some((-hep.beta(), direction.clone())),
            )
            .unwrap();
        let amp_pos = pos.amplitude().clone().to_data().to_vec::<f64>().unwrap();
        let amp_neg = neg.amplitude().clone().to_data().to_vec::<f64>().unwrap();
        let n = 4usize;
        let batch = 2usize;

        let mut manual = vec![0.0_f64; n * n];
        for i in 0..n {
            for j in 0..n {
                let mut op = 0.0;
                let mut on = 0.0;
                for b in 0..batch {
                    op += amp_pos[b * n + i] * amp_pos[b * n + j];
                    on += amp_neg[b * n + i] * amp_neg[b * n + j];
                }
                op /= batch as f64;
                on /= batch as f64;
                manual[i * n + j] = (on - op) / (2.0 * hep.beta());
            }
        }

        let grad = hep
            .coupling_gradient(&layer, x, direction)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        for (g, m) in grad.iter().zip(manual.iter()) {
            assert!((g - m).abs() < 1e-9, "{g} vs {m}");
        }
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use burn::backend::NdArray;
    use prin_dynamics::Seed;
    use proptest::prelude::*;

    type TestBackend = NdArray<f64>;

    proptest! {
        #[test]
        fn coupling_gradient_always_finite(
            n_osc in 1usize..=5,
            n_dims in 1usize..=4,
            batch in 1usize..=3,
            seed_val in 0u64..1000,
        ) {
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let layer = crate::layers::ResonanceLayerConfig::new(n_osc, n_dims)
                .unwrap()
                .init::<TestBackend>(&dev, &mut seed);
            let hep = HolomorphicEpConfig::with_params(0.1, 3, 3).unwrap().init();

            let mut xseed = Seed::new(seed_val as u128, 1);
            let x = crate::support::seeded_uniform::<TestBackend, 2>(
                [batch, n_dims], -1.0, 1.0, &dev, &mut xseed,
            );
            let mut dseed = Seed::new(seed_val as u128, 2);
            let direction = crate::support::seeded_uniform::<TestBackend, 2>(
                [batch, n_osc], -1.0, 1.0, &dev, &mut dseed,
            );

            let grad = hep.coupling_gradient(&layer, x, direction).unwrap();
            prop_assert_eq!(grad.dims(), [n_osc, n_osc]);
            for v in grad.to_data().to_vec::<f64>().unwrap() {
                prop_assert!(v.is_finite());
            }
        }
    }
}

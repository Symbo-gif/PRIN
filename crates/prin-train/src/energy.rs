//! Holomorphic energy function for complex oscillator states.
//!
//! Burn rebuild of PRINet 3.0's `nn/hep.py::HolomorphicEnergy`. The energy of
//! a batch of complex oscillator states `z` (shape `[batch, n_oscillators]`,
//! carried as a [`crate::activations::ComplexTensor`]) under a real coupling
//! matrix `K` (shape `[n_oscillators, n_oscillators]`) is:
//!
//! ```text
//! E_coupling = -Σᵢⱼ K[i,j]·Re(z_i* · z_j)   (per batch element)
//! E_self     =  Σᵢ (|z_i|² - 1)²             (drives toward unit amplitude)
//! E_task     =  β · task_loss                 (optional, only when β ≠ 0)
//! E          =  mean_batch(E_coupling + E_self + E_task)
//! ```
//!
//! `E_coupling` and `E_self` are holomorphic in `z` (in the true-complex
//! sense the PRINet 3.0 docstring claims), enabling the closed-form coupling
//! gradient `∂E_coupling/∂K[i,j] = -Re(z_i* z_j)` that [`crate::hep`] uses
//! directly rather than deriving it through backpropagation.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::activations::ComplexTensor;
//! use prin_train::energy::HolomorphicEnergyConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let energy = HolomorphicEnergyConfig::new(4).unwrap().init();
//! let z = ComplexTensor::from_real(Tensor::<Backend, 2>::ones([2, 4], &device));
//! let coupling = Tensor::<Backend, 2>::zeros([4, 4], &device);
//! let e = energy.forward(z, coupling, None, 0.0).unwrap();
//! assert_eq!(e.dims(), [1]);
//! ```

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;

use crate::activations::ComplexTensor;
use crate::error::TrainError;
use crate::support::check_dims;

/// Validated hyperparameters for [`HolomorphicEnergy`].
#[derive(Clone, Debug, PartialEq)]
pub struct HolomorphicEnergyConfig {
    /// Number of complex oscillators.
    pub n_oscillators: usize,
}

impl HolomorphicEnergyConfig {
    /// A validated configuration.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` is zero.
    pub fn new(n_oscillators: usize) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        Ok(Self { n_oscillators })
    }

    /// Build a [`HolomorphicEnergy`] from this configuration.
    pub fn init(&self) -> HolomorphicEnergy {
        HolomorphicEnergy {
            n_oscillators: self.n_oscillators,
        }
    }
}

/// Holomorphic energy function for complex oscillator states.
///
/// See the module docs for the exact energy decomposition. Construct via
/// [`HolomorphicEnergyConfig::init`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HolomorphicEnergy {
    n_oscillators: usize,
}

impl HolomorphicEnergy {
    /// Number of complex oscillators.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Compute the scalar (batch-averaged) holomorphic energy.
    ///
    /// `task_loss`, when given, is a per-batch-element loss of shape
    /// `[batch, 1]`; it is added as `β·task_loss` only when `beta != 0.0`
    /// (matching PRINet 3.0's `if beta != 0.0 and target_logits is not None
    /// and target_labels is not None`, with `task_loss` standing in for the
    /// reference's inline `cross_entropy(target_logits, target_labels)` —
    /// the concrete classification head that produces `target_logits` is
    /// model-level and deferred to WP-027, so this energy function accepts
    /// an already-computed task loss rather than a hardcoded projection).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `coupling` is not
    /// `[n_oscillators, n_oscillators]`, if `z`'s width is not
    /// `n_oscillators`, or if `task_loss` (when given) does not have shape
    /// `[batch, 1]`.
    pub fn forward<B: Backend>(
        &self,
        z: ComplexTensor<B>,
        coupling: Tensor<B, 2>,
        task_loss: Option<Tensor<B, 2>>,
        beta: f64,
    ) -> Result<Tensor<B, 1>, TrainError> {
        let n = self.n_oscillators;
        check_dims("coupling", coupling.dims(), [n, n])?;
        let (re, im) = z.into_parts();
        let batch = re.dims()[0];
        check_dims("re", re.dims(), [batch, n])?;
        check_dims("im", im.dims(), [batch, n])?;

        // Re(z_conj * (z @ K^T)) = re*(re@K^T) + im*(im@K^T); see module docs.
        let coupling_t = coupling.transpose();
        let ct_re = re.clone().matmul(coupling_t.clone());
        let ct_im = im.clone().matmul(coupling_t);
        let coupling_energy = (re.clone() * ct_re + im.clone() * ct_im)
            .sum_dim(1)
            .mul_scalar(-1.0);

        let abs_sq = re.powf_scalar(2.0) + im.powf_scalar(2.0);
        let self_energy = abs_sq.sub_scalar(1.0).powf_scalar(2.0).sum_dim(1);

        let mut energy = coupling_energy + self_energy; // [batch, 1]

        if beta != 0.0 {
            if let Some(task) = task_loss {
                check_dims("task_loss", task.dims(), [batch, 1])?;
                energy = energy + task.mul_scalar(beta);
            }
        }

        Ok(energy.mean())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::TensorData;
    use prin_dynamics::Seed;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    // --- Config validation ---

    #[test]
    fn zero_oscillators_rejected() {
        assert!(matches!(
            HolomorphicEnergyConfig::new(0).unwrap_err(),
            TrainError::EmptyBand {
                name: "oscillators"
            }
        ));
    }

    // --- Accessors ---

    #[test]
    fn n_oscillators_accessor_reports_config_value() {
        let energy = HolomorphicEnergyConfig::new(5).unwrap().init();
        assert_eq!(energy.n_oscillators(), 5);
    }

    // --- Shape guards ---

    #[test]
    fn forward_rejects_wrong_coupling_shape() {
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([2, 3], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([2, 3], &dev);
        let err = energy.forward(z, coupling, None, 0.0).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "coupling",
                ..
            }
        ));
    }

    #[test]
    fn forward_rejects_wrong_z_width() {
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([2, 4], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([3, 3], &dev);
        let err = energy.forward(z, coupling, None, 0.0).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "re", .. }));
    }

    #[test]
    fn forward_rejects_wrong_task_loss_shape() {
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([2, 3], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([3, 3], &dev);
        let bad_task = Tensor::<TestBackend, 2>::ones([2, 2], &dev);
        let err = energy
            .forward(z, coupling, Some(bad_task), 1.0)
            .unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "task_loss",
                ..
            }
        ));
    }

    // --- Energy properties ---

    #[test]
    fn self_energy_is_zero_at_unit_amplitude_with_no_coupling() {
        // |z_i| = 1 for all i (re=1, im=0) and K=0 => E_coupling=0, E_self=0.
        let energy = HolomorphicEnergyConfig::new(4).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([3, 4], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([4, 4], &dev);
        let e = energy.forward(z, coupling, None, 0.0).unwrap();
        assert!(e.into_scalar().abs() < 1e-12);
    }

    #[test]
    fn self_energy_grows_away_from_unit_amplitude() {
        let energy = HolomorphicEnergyConfig::new(2).unwrap().init();
        let dev = device();
        let coupling = Tensor::<TestBackend, 2>::zeros([2, 2], &dev);

        let near = ComplexTensor::from_real(Tensor::<TestBackend, 2>::full([1, 2], 1.1, &dev));
        let far = ComplexTensor::from_real(Tensor::<TestBackend, 2>::full([1, 2], 3.0, &dev));
        let e_near = energy
            .forward(near, coupling.clone(), None, 0.0)
            .unwrap()
            .into_scalar();
        let e_far = energy
            .forward(far, coupling, None, 0.0)
            .unwrap()
            .into_scalar();
        assert!(e_far > e_near, "self-energy should grow with |amplitude-1|");
    }

    #[test]
    fn task_energy_ignored_when_beta_is_zero() {
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([2, 3], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([3, 3], &dev);
        let task = Tensor::<TestBackend, 2>::full([2, 1], 1000.0, &dev);

        let with_task = energy
            .forward(z.clone(), coupling.clone(), Some(task), 0.0)
            .unwrap()
            .into_scalar();
        let without_task = energy
            .forward(z, coupling, None, 0.0)
            .unwrap()
            .into_scalar();
        assert!((with_task - without_task).abs() < 1e-12);
    }

    #[test]
    fn task_energy_added_when_beta_nonzero() {
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::ones([2, 3], &dev));
        let coupling = Tensor::<TestBackend, 2>::zeros([3, 3], &dev);
        let task = Tensor::<TestBackend, 2>::full([2, 1], 2.0, &dev);

        let e = energy
            .forward(z, coupling, Some(task), 0.5)
            .unwrap()
            .into_scalar();
        // E_self = 0 (unit amplitude), E_coupling = 0 (K=0), E_task = 0.5*2.0.
        assert!((e - 1.0).abs() < 1e-12);
    }

    #[test]
    fn coupling_energy_matches_closed_form_scalar_case() {
        // n=1: E_coupling = -K[0,0] * re^2 (im=0), no averaging ambiguity
        // (batch=1).
        let energy = HolomorphicEnergyConfig::new(1).unwrap().init();
        let dev = device();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::full([1, 1], 2.0, &dev));
        let coupling = Tensor::<TestBackend, 2>::full([1, 1], 0.5, &dev);
        let e = energy
            .forward(z, coupling, None, 0.0)
            .unwrap()
            .into_scalar();
        // E_coupling = -0.5*4 = -2.0; E_self = (4-1)^2 = 9.0; total = 7.0.
        assert!((e - 7.0).abs() < 1e-12);
    }

    // --- Closed-form coupling gradient vs. autodiff / finite difference ---

    #[test]
    fn coupling_energy_gradient_matches_closed_form_outer_product() {
        // ∂E_coupling/∂K[i,j] = -mean_batch(Re(z_i*) z_j); for real z
        // (im=0) this reduces to -mean_batch(re_i * re_j), the exact
        // outer-product formula `crate::hep` uses directly. Gradcheck it two
        // ways: against Burn autodiff on the energy function, and against a
        // central finite difference — both float64.
        let dev: <TestBackend as Backend>::Device = Default::default();
        let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
        let mut seed = Seed::new(31, 0);
        let re_data: Vec<f64> = (0..6)
            .map(|_| seed.next_f64_range(-2.0, 2.0).unwrap())
            .collect();
        let batch = 2usize;
        let n = 3usize;

        let base_coupling = vec![0.1_f64, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];
        let i = 0usize;
        let j = 1usize;

        let energy_for = |k_ij: f64| -> f64 {
            let mut c = base_coupling.clone();
            c[i * n + j] = k_ij;
            let coupling =
                Tensor::<TestBackend, 2>::from_data(TensorData::new(c, vec![n, n]), &dev);
            let re = Tensor::<TestBackend, 2>::from_data(
                TensorData::new(re_data.clone(), vec![batch, n]),
                &dev,
            );
            let z = ComplexTensor::from_real(re);
            energy
                .forward(z, coupling, None, 0.0)
                .unwrap()
                .into_scalar()
        };

        let eps = 1e-6;
        let numerical = (energy_for(base_coupling[i * n + j] + eps)
            - energy_for(base_coupling[i * n + j] - eps))
            / (2.0 * eps);

        // Closed form: -mean_batch(re_i * re_j).
        let mut sum = 0.0;
        for b in 0..batch {
            sum += re_data[b * n + i] * re_data[b * n + j];
        }
        let closed_form = -sum / batch as f64;

        assert!(
            (closed_form - numerical).abs() < 1e-3,
            "closed form {closed_form} vs finite-difference {numerical}"
        );

        // Cross-check against Burn autodiff on the same energy function.
        let dev_ad: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut c = base_coupling.clone();
        c[i * n + j] = base_coupling[i * n + j];
        let coupling_ad =
            Tensor::<TestAutodiffBackend, 2>::from_data(TensorData::new(c, vec![n, n]), &dev_ad)
                .require_grad();
        let re_ad = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(re_data.clone(), vec![batch, n]),
            &dev_ad,
        );
        let z_ad = ComplexTensor::from_real(re_ad);
        let e = energy
            .forward(z_ad, coupling_ad.clone(), None, 0.0)
            .unwrap();
        let grads = e.backward();
        let grad_ij = coupling_ad
            .grad(&grads)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap()[i * n + j];

        assert!(
            (closed_form - grad_ij).abs() < 1e-8,
            "closed form {closed_form} vs autodiff {grad_ij}"
        );
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
        fn forward_always_finite(
            n in 1usize..=5,
            batch in 1usize..=4,
            seed_val in 0u64..1000,
        ) {
            let energy = HolomorphicEnergyConfig::new(n).unwrap().init();
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let re = crate::support::seeded_uniform::<TestBackend, 2>([batch, n], -3.0, 3.0, &dev, &mut seed);
            let im = crate::support::seeded_uniform::<TestBackend, 2>([batch, n], -3.0, 3.0, &dev, &mut seed);
            let coupling = crate::support::seeded_uniform::<TestBackend, 2>([n, n], -1.0, 1.0, &dev, &mut seed);
            let z = ComplexTensor::new(re, im).unwrap();
            let e = energy.forward(z, coupling, None, 0.0).unwrap();
            prop_assert!(e.into_scalar().is_finite());
        }
    }
}

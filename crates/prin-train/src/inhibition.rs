//! Feedback inhibition with a hard-forward / soft-backward straight-through
//! estimator (STE).
//!
//! [`FeedbackInhibition`] is the trainable half of PRINet 3.0's
//! `core/propagation/inhibition.py`: [`FeedbackInhibition::compete`] enforces
//! top-`k` winner-take-all (WTA) sparsity — hard top-`k` selection in the
//! forward pass, softmax-weighted scores in the backward pass, so gradients
//! flow through a discrete selection. `FeedforwardInhibition` (the reference's
//! deterministic, parameter-free phase-delay gate) and `DentateGyrusConverter`
//! (the FFI→integration→FBI pipeline built on top of both) have no learnable
//! parameters and no differentiability concern of their own — out of WP-023
//! scope, which is specifically the "trainable half" (feedback inhibition and
//! its STE).
//!
//! # STE construction
//!
//! For rates `r` of shape `[batch, n]`, top-`k` count `k`, and softmax
//! temperature `T`:
//!
//! ```text
//! soft_scores = softmax(r / T)
//! hard_mask[i] = 1 if i is one of the k largest entries of r, else 0
//! output = hard_mask·r + (soft_scores·r − stop_grad(soft_scores·r))
//! ```
//!
//! The `stop_grad` (Burn [`Tensor::detach`]) term is numerically zero in the
//! forward pass (`soft_scores·r − soft_scores·r == 0`), so `forward(output)
//! == hard_mask·r` exactly — the "hard-forward" identity checked by
//! `compete_forward_equals_hard_topk_selection` in the test module. `hard_mask`
//! itself is built fresh from `topk`'s (non-differentiable) indices, so Burn's
//! autodiff treats it as a constant: the backward pass differentiates
//! `hard_mask·r` (contributing `hard_mask` itself, elementwise) plus the live
//! `soft_scores·r` term (contributing its full softmax Jacobian) — the
//! "soft-backward" half. This is a line-for-line port of PRINet 3.0's
//! `FeedbackInhibition.compete` STE, not a simplified/alternative STE
//! formulation.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::inhibition::FeedbackInhibitionConfig;
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let fbi = FeedbackInhibitionConfig::with_params(8, Some(3), 0.1, 1.0)
//!     .unwrap()
//!     .init();
//! let rates = Tensor::<Backend, 2>::ones([2, 8], &device);
//! let sparse = fbi.compete(rates).unwrap();
//! assert_eq!(sparse.dims(), [2, 8]);
//! ```

use burn::tensor::activation::softmax;
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;

use crate::error::TrainError;
use crate::support::{check_dims, validate_finite};

/// Validated hyperparameters for [`FeedbackInhibition`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `sparsity=0.1,
/// temperature=1.0`, `k` derived from `sparsity`.
#[derive(Clone, Debug, PartialEq)]
pub struct FeedbackInhibitionConfig {
    /// Number of oscillators/units the inhibition operates over.
    pub n_oscillators: usize,
    /// Explicit top-`k` winner count. When `None`, `k` is derived from
    /// `sparsity` at [`Self::init`] time.
    pub k: Option<usize>,
    /// Target sparsity (fraction of active units), used when `k` is `None`.
    pub sparsity: f64,
    /// Softmax temperature for the soft (backward-pass) scores.
    pub temperature: f64,
}

impl FeedbackInhibitionConfig {
    /// A validated configuration with PRINet 3.0's default hyperparameters
    /// (`sparsity=0.1, temperature=1.0`, `k` derived from `sparsity`).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` is zero.
    pub fn new(n_oscillators: usize) -> Result<Self, TrainError> {
        Self::with_params(n_oscillators, None, 0.1, 1.0)
    }

    /// A validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` is zero,
    /// [`TrainError::InvalidTopK`] if `k` is `Some(0)`,
    /// [`TrainError::InvalidSparsity`] if `sparsity` is outside `(0, 1]`, or
    /// [`TrainError::NonFiniteParameter`] if `temperature` is not finite.
    pub fn with_params(
        n_oscillators: usize,
        k: Option<usize>,
        sparsity: f64,
        temperature: f64,
    ) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        if let Some(k) = k {
            if k < 1 {
                return Err(TrainError::InvalidTopK { k });
            }
        }
        if !(sparsity > 0.0 && sparsity <= 1.0) {
            return Err(TrainError::InvalidSparsity { value: sparsity });
        }
        validate_finite("temperature", temperature)?;
        Ok(Self {
            n_oscillators,
            k,
            sparsity,
            temperature,
        })
    }

    /// Build a [`FeedbackInhibition`], resolving `k` from `sparsity` when
    /// unset: `k = min(n_oscillators, max(1, floor(n_oscillators *
    /// sparsity)))` (PRINet 3.0's `max(1, int(N * sparsity))`; `int()`
    /// truncation and `floor` coincide for the non-negative products this
    /// config admits). `temperature` is floored at `1e-8`, matching PRINet
    /// 3.0's `max(temperature, 1e-8)`.
    pub fn init(&self) -> FeedbackInhibition {
        let n = self.n_oscillators;
        let k = self
            .k
            .unwrap_or_else(|| (((n as f64) * self.sparsity) as usize).max(1))
            .min(n);
        FeedbackInhibition {
            n_oscillators: n,
            k,
            temperature: self.temperature.max(1e-8),
        }
    }
}

/// Trainable feedback inhibition: top-`k` winner-take-all competition with a
/// hard-forward / soft-backward STE.
///
/// See the module docs for the exact STE construction. Construct via
/// [`FeedbackInhibitionConfig::init`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct FeedbackInhibition {
    n_oscillators: usize,
    k: usize,
    temperature: f64,
}

impl FeedbackInhibition {
    /// Number of oscillators/units.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Resolved top-`k` winner count.
    pub fn k(&self) -> usize {
        self.k
    }

    /// Softmax temperature.
    pub fn temperature(&self) -> f64 {
        self.temperature
    }

    /// Apply top-`k` winner-take-all competition.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `rates`'s width is not
    /// [`Self::n_oscillators`].
    pub fn compete<B: Backend>(&self, rates: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let dims = rates.dims();
        check_dims("rates", dims, [dims[0], self.n_oscillators])?;
        let [batch, n] = dims;
        let device = rates.device();

        let soft_scores = softmax(rates.clone().div_scalar(self.temperature), 1);
        let (_topk_vals, topk_idx) = rates.clone().topk_with_indices(self.k, 1);

        let zeros = Tensor::<B, 2>::zeros([batch, n], &device);
        let ones = Tensor::<B, 2>::ones([batch, self.k], &device);
        let hard_mask = zeros.scatter(1, topk_idx, ones);

        let soft_selected = soft_scores * rates.clone();
        let hard_selected = hard_mask * rates;
        Ok(hard_selected.clone() + (soft_selected.clone() - soft_selected.detach()))
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
            FeedbackInhibitionConfig::new(0).unwrap_err(),
            TrainError::EmptyBand {
                name: "oscillators"
            }
        ));
    }

    #[test]
    fn zero_k_rejected() {
        assert!(matches!(
            FeedbackInhibitionConfig::with_params(8, Some(0), 0.1, 1.0).unwrap_err(),
            TrainError::InvalidTopK { k: 0 }
        ));
    }

    #[test]
    fn out_of_range_sparsity_rejected() {
        assert!(matches!(
            FeedbackInhibitionConfig::with_params(8, None, 0.0, 1.0).unwrap_err(),
            TrainError::InvalidSparsity { .. }
        ));
        assert!(matches!(
            FeedbackInhibitionConfig::with_params(8, None, 1.5, 1.0).unwrap_err(),
            TrainError::InvalidSparsity { .. }
        ));
    }

    #[test]
    fn non_finite_temperature_rejected() {
        assert!(matches!(
            FeedbackInhibitionConfig::with_params(8, None, 0.1, f64::NAN).unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "temperature",
                ..
            }
        ));
    }

    // --- k resolution ---

    #[test]
    fn explicit_k_is_used_directly() {
        let fbi = FeedbackInhibitionConfig::with_params(10, Some(4), 0.1, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi.k(), 4);
    }

    #[test]
    fn k_derived_from_sparsity_floors_and_floors_at_one() {
        // floor(10*0.1) = 1, matches int(N*sparsity).
        let fbi = FeedbackInhibitionConfig::with_params(10, None, 0.1, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi.k(), 1);
        // floor(10*0.35) = 3.
        let fbi35 = FeedbackInhibitionConfig::with_params(10, None, 0.35, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi35.k(), 3);
        // Vanishingly small sparsity still floors at k=1, not 0.
        let fbi_tiny = FeedbackInhibitionConfig::with_params(10, None, 0.001, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi_tiny.k(), 1);
    }

    #[test]
    fn k_clamped_to_n_oscillators() {
        let fbi = FeedbackInhibitionConfig::with_params(5, Some(100), 0.1, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi.k(), 5);
    }

    #[test]
    fn temperature_floored_at_epsilon() {
        let fbi = FeedbackInhibitionConfig::with_params(5, None, 0.1, 0.0)
            .unwrap()
            .init();
        assert!((fbi.temperature() - 1e-8).abs() < 1e-15);
    }

    // --- Accessors ---

    #[test]
    fn accessors_report_resolved_values() {
        let fbi = FeedbackInhibitionConfig::with_params(6, Some(2), 0.1, 1.0)
            .unwrap()
            .init();
        assert_eq!(fbi.n_oscillators(), 6);
        assert_eq!(fbi.k(), 2);
        assert!((fbi.temperature() - 1.0).abs() < 1e-15);
    }

    // --- Shape guard ---

    #[test]
    fn compete_rejects_wrong_width() {
        let fbi = FeedbackInhibitionConfig::new(6).unwrap().init();
        let dev = device();
        let rates = Tensor::<TestBackend, 2>::ones([2, 5], &dev);
        let err = fbi.compete(rates).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "rates", .. }
        ));
    }

    // --- STE identity: forward == hard top-k selection ---

    #[test]
    fn compete_forward_equals_hard_topk_selection() {
        let fbi = FeedbackInhibitionConfig::with_params(6, Some(2), 0.1, 1.0)
            .unwrap()
            .init();
        let dev = device();
        let rates = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.1_f64, 5.0, 0.3, 9.0, 0.2, 4.5], vec![1, 6]),
            &dev,
        );
        let out = fbi
            .compete(rates)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        // The two largest entries (indices 1 and 3, values 5.0 and 9.0) are
        // the only nonzero entries in the forward pass; everything else is
        // exactly zero (the soft term cancels its own detached copy).
        let expected = [0.0, 5.0, 0.0, 9.0, 0.0, 0.0];
        for (got, want) in out.iter().zip(expected.iter()) {
            assert!((got - want).abs() < 1e-12, "{got} vs {want}");
        }
    }

    #[test]
    fn compete_selects_exactly_k_nonzero_entries_property() {
        let fbi = FeedbackInhibitionConfig::with_params(8, Some(3), 0.1, 1.0)
            .unwrap()
            .init();
        let dev = device();
        let mut seed = Seed::new(4, 0);
        let rates =
            crate::support::seeded_uniform::<TestBackend, 2>([3, 8], 0.0, 10.0, &dev, &mut seed);
        let out = fbi.compete(rates).unwrap();
        let dims = out.dims();
        let data = out.to_data().to_vec::<f64>().unwrap();
        for row in 0..dims[0] {
            let nonzero = data[row * dims[1]..(row + 1) * dims[1]]
                .iter()
                .filter(|v| v.abs() > 1e-12)
                .count();
            assert_eq!(nonzero, 3, "row {row} did not select exactly k winners");
        }
    }

    #[test]
    fn compete_output_never_negative_for_nonnegative_rates() {
        let fbi = FeedbackInhibitionConfig::new(8).unwrap().init();
        let dev = device();
        let mut seed = Seed::new(17, 0);
        let rates =
            crate::support::seeded_uniform::<TestBackend, 2>([4, 8], 0.0, 3.0, &dev, &mut seed);
        let out = fbi.compete(rates).unwrap();
        for v in out.to_data().to_vec::<f64>().unwrap() {
            assert!(v >= -1e-12, "competed output {v} is negative");
        }
    }

    // --- Gradient reference tests ---

    #[test]
    fn compete_gradients_are_finite_and_flow_through_rates() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let fbi = FeedbackInhibitionConfig::with_params(6, Some(2), 0.1, 1.0)
            .unwrap()
            .init();
        let rates = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.1_f64, 5.0, 0.3, 9.0, 0.2, 4.5], vec![1, 6]),
            &dev,
        )
        .require_grad();

        let out = fbi.compete(rates.clone()).unwrap();
        let loss = out.sum();
        let grads = loss.backward();
        let grad = rates
            .grad(&grads)
            .expect("gradient must flow to rates through the STE")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert!(grad.iter().all(|v| v.is_finite()));
        // At least one gradient component is genuinely nonzero (the soft
        // term is never uniformly flat for non-uniform inputs), i.e. the
        // backward pass is not a silent no-op.
        assert!(grad.iter().any(|v| v.abs() > 1e-9));
    }

    #[test]
    fn compete_gradient_matches_central_finite_difference() {
        let _guard = crate::support::autodiff_test_guard();
        // `hard_mask` is piecewise-constant (a step function of `rates`), so
        // the *raw* `compete` output has zero true derivative almost
        // everywhere at a non-winning index — finite-differencing it
        // directly would test the wrong thing (and would also silently
        // measure zero on a non-Autodiff backend, since `detach()` is a
        // documented no-op there). At a non-winning index the STE's
        // *analytic* gradient reduces exactly to the closed-form soft
        // term's Jacobian (`hard_mask` contributes 0 at that index), so this
        // gradchecks the soft term directly: `d/d(rates_j)
        // sum(softmax(rates/T) * rates)`.
        let dev: <TestBackend as Backend>::Device = Default::default();
        let temperature = 1.0;
        let base = [0.1_f64, 0.2, 9.0, 0.3]; // index 2 is the sole top-1 winner.

        let soft_sum_for = |perturbed_index1: f64| -> f64 {
            let mut data = base.to_vec();
            data[1] = perturbed_index1;
            let rates =
                Tensor::<TestBackend, 2>::from_data(TensorData::new(data, vec![1, 4]), &dev);
            let soft = softmax(rates.clone().div_scalar(temperature), 1) * rates;
            soft.sum().into_scalar()
        };

        let eps = 1e-6;
        let numerical = (soft_sum_for(base[1] + eps) - soft_sum_for(base[1] - eps)) / (2.0 * eps);

        let dev_ad: <TestAutodiffBackend as Backend>::Device = Default::default();
        let fbi_ad = FeedbackInhibitionConfig::with_params(4, Some(1), 0.1, temperature)
            .unwrap()
            .init();
        let rates_ad = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(base.to_vec(), vec![1, 4]),
            &dev_ad,
        )
        .require_grad();
        let out = fbi_ad.compete(rates_ad.clone()).unwrap();
        let loss = out.sum();
        let grads = loss.backward();
        let analytic = rates_ad
            .grad(&grads)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap()[1];

        assert!(
            (analytic - numerical).abs() < 1e-3,
            "analytic {analytic} vs finite-difference {numerical}"
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
        fn compete_always_selects_at_most_k_and_is_finite(
            n in 2usize..=10,
            batch in 1usize..=4,
            k in 1usize..=10,
            seed_val in 0u64..1000,
        ) {
            let k = k.min(n);
            let fbi = FeedbackInhibitionConfig::with_params(n, Some(k), 0.1, 1.0)
                .unwrap()
                .init();
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let rates = crate::support::seeded_uniform::<TestBackend, 2>(
                [batch, n], 0.0, 5.0, &dev, &mut seed,
            );
            let out = fbi.compete(rates).unwrap();
            let dims = out.dims();
            let data = out.to_data().to_vec::<f64>().unwrap();
            for row in 0..dims[0] {
                let nonzero = data[row * n..(row + 1) * n]
                    .iter()
                    .filter(|v| v.abs() > 1e-9)
                    .count();
                prop_assert!(nonzero <= k);
            }
            for v in &data {
                prop_assert!(v.is_finite());
            }
        }
    }
}

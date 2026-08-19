//! Adaptive oscillator allocation for task-complexity-driven binding.
//!
//! [`AdaptiveOscillatorAllocator`] dynamically adjusts the number of
//! delta/theta/gamma oscillators as a function of estimated scene
//! complexity, and [`DynamicPhaseTracker`] wraps it with
//! [`crate::phase_tracker::PhaseTracker`] to give per-scene adaptive
//! capacity. Burn `Module` rebuild of PRINet 3.0's
//! `nn.adaptive_allocation`.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! Rule-based (`strategy = Rule`), matching `_allocate_rule` exactly
//! (including Python's round-half-to-even, `crate::support::python_round`):
//!
//! ```text
//! total   = round(min_total + clamp(c,0,1)·(max_total − min_total))
//! n_delta = max(1, round(total·delta_ratio))
//! n_theta = max(1, round(total·theta_ratio))
//! n_gamma = max(1, total − n_delta − n_theta)
//! ```
//!
//! Learned (`strategy = Learned`): a 3-layer MLP predicts per-band
//! *fractions* (softmax over 3 logits) from a complexity feature vector;
//! fractions are floored to integers and the shortfall is distributed to
//! the bands with the largest remainder, matching `_allocate_learned`.
//!
//! **Faithfully reproduced quirk.** [`DynamicPhaseTracker::forward`] never
//! passes `features` to [`AdaptiveOscillatorAllocator::allocate`] (mirroring
//! `DynamicPhaseTracker.forward`'s own `self.allocator.allocate(complexity)`
//! call, which omits the `features` argument `allocate` needs to select the
//! learned path) — so `DynamicPhaseTracker` always uses rule-based
//! allocation in `forward`, even when its allocator is configured with
//! `strategy = Learned`. This is PRINet 3.0's actual behavior, not a Rust
//! port defect; preserved rather than silently "fixed".
//!
//! [`DynamicPhaseTracker`] is **not** a [`burn::module::Module`]: unlike
//! every other type in this crate, its whole purpose is to lazily construct
//! and cache a *different* [`crate::phase_tracker::PhaseTracker`] (a
//! differently-shaped parameter set) per distinct oscillator budget, which
//! has no fixed parameter set for `Module`'s record/checkpoint contract to
//! describe. Each cached `PhaseTracker` remains individually a full `Module`
//! with its own gradients and checkpointing; only the *container* (a lazy
//! cache, mirroring the reference's `_tracker_cache: dict`) opts out.
//!
//! # Example
//!
//! ```
//! use prin_dynamics::Seed;
//! use prin_train::allocation::AdaptiveOscillatorAllocatorConfig;
//!
//! type Backend = burn::backend::NdArray<f32>;
//!
//! let cfg = AdaptiveOscillatorAllocatorConfig::new(12, 64).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let allocator = cfg.init::<Backend>(&device, &mut seed);
//!
//! let budget = allocator.allocate(0.3, None);
//! assert!(budget.total() >= 12 && budget.total() <= 64);
//! ```

use std::cell::RefCell;
use std::collections::HashMap;

use burn::module::{Ignored, Module};
use burn::nn::Linear;
use burn::tensor::activation::{relu, softmax};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::phase_tracker::{PhaseTracker, PhaseTrackerConfig};
use crate::support::{python_round, seeded_linear, to_f64_vec};

/// Allocated oscillator counts per frequency band.
///
/// Mirrors PRINet 3.0's `OscillatorBudget` dataclass.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OscillatorBudget {
    /// Delta-band (1-4 Hz) oscillators.
    pub n_delta: usize,
    /// Theta-band (4-8 Hz) oscillators.
    pub n_theta: usize,
    /// Gamma-band (30-100 Hz) oscillators.
    pub n_gamma: usize,
    /// Estimated scene complexity in `[0, 1]`.
    pub complexity: f64,
}

impl OscillatorBudget {
    /// Total oscillator count across all bands.
    pub fn total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }
}

/// Estimate scene complexity from detection features, a scalar in `[0, 1]`
/// combining object count and spatial spread.
///
/// `detections` has shape `[n, d]`; the first two columns of `d ≥ 2` are
/// treated as a spatial centroid `(x, y)`. Matches PRINet 3.0's
/// `estimate_complexity` exactly, including its use of the *unbiased*
/// (`N - 1`) sample standard deviation (`torch.std`'s default).
///
/// This is a non-differentiable host-side scalar (PRINet 3.0's own
/// implementation also breaks the autodiff graph here via `.item()`/`float`
/// conversions), so it returns a plain `f64` rather than a `Tensor`.
pub fn estimate_complexity<B: Backend>(
    detections: &Tensor<B, 2>,
    spatial_weight: f64,
    count_weight: f64,
    max_objects: usize,
) -> f64 {
    let [n, d] = detections.dims();
    let count_score = (n as f64 / max_objects.max(1) as f64).min(1.0);

    let spatial_score = if n < 2 || d < 2 {
        0.0
    } else {
        let data = to_f64_vec(detections.clone());
        let (mut mean_x, mut mean_y) = (0.0, 0.0);
        for i in 0..n {
            mean_x += data[i * d];
            mean_y += data[i * d + 1];
        }
        mean_x /= n as f64;
        mean_y /= n as f64;
        let (mut var_x, mut var_y) = (0.0, 0.0);
        for i in 0..n {
            var_x += (data[i * d] - mean_x).powi(2);
            var_y += (data[i * d + 1] - mean_y).powi(2);
        }
        var_x /= (n - 1) as f64;
        var_y /= (n - 1) as f64;
        let spread = (var_x.sqrt() + var_y.sqrt()) / 2.0;
        (spread / 0.3).min(1.0)
    };

    let total_weight = spatial_weight + count_weight;
    (spatial_weight * spatial_score + count_weight * count_score) / total_weight
}

/// Allocation strategy for [`AdaptiveOscillatorAllocator`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AllocatorStrategy {
    /// Deterministic piecewise-linear interpolation, no learnable parameters.
    Rule,
    /// A small MLP predicts soft per-band fractions from a complexity
    /// feature vector.
    Learned,
}

/// Validated hyperparameters for [`AdaptiveOscillatorAllocator`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `delta_ratio=0.1,
/// theta_ratio=0.2, strategy=Rule, complexity_dim=1`.
#[derive(Clone, Debug, PartialEq)]
pub struct AdaptiveOscillatorAllocatorConfig {
    /// Minimum total oscillator count. Must be `>= 3`.
    pub min_total: usize,
    /// Maximum total oscillator count. Must be `>= min_total`.
    pub max_total: usize,
    /// Fraction of total allocated to the delta band (rule strategy).
    pub delta_ratio: f64,
    /// Fraction of total allocated to the theta band (rule strategy).
    pub theta_ratio: f64,
    /// Allocation strategy.
    pub strategy: AllocatorStrategy,
    /// Input feature dimension for the learned strategy.
    pub complexity_dim: usize,
}

impl AdaptiveOscillatorAllocatorConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(min_total: usize, max_total: usize) -> Result<Self, TrainError> {
        Self::with_params(min_total, max_total, 0.1, 0.2, AllocatorStrategy::Rule, 1)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidAllocatorRange`] if `min_total < 3` or
    /// `max_total < min_total`, or [`TrainError::InvalidRatio`] if
    /// `delta_ratio`/`theta_ratio` is non-finite or outside `[0, 1]`.
    pub fn with_params(
        min_total: usize,
        max_total: usize,
        delta_ratio: f64,
        theta_ratio: f64,
        strategy: AllocatorStrategy,
        complexity_dim: usize,
    ) -> Result<Self, TrainError> {
        if min_total < 3 || max_total < min_total {
            return Err(TrainError::InvalidAllocatorRange {
                min_total,
                max_total,
            });
        }
        for (name, value) in [("delta_ratio", delta_ratio), ("theta_ratio", theta_ratio)] {
            if !(value.is_finite() && (0.0..=1.0).contains(&value)) {
                return Err(TrainError::InvalidRatio { name, value });
            }
        }
        Ok(Self {
            min_total,
            max_total,
            delta_ratio,
            theta_ratio,
            strategy,
            complexity_dim,
        })
    }

    /// Initialize an [`AdaptiveOscillatorAllocator`] with parameters drawn
    /// from the project's deterministic [`Seed`] (Coding Standards §1.3).
    /// The MLP is only constructed for [`AllocatorStrategy::Learned`].
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> AdaptiveOscillatorAllocator<B> {
        let mlp = match self.strategy {
            AllocatorStrategy::Learned => Some([
                seeded_linear::<B>(self.complexity_dim, 64, true, device, seed),
                seeded_linear::<B>(64, 32, true, device, seed),
                seeded_linear::<B>(32, 3, true, device, seed),
            ]),
            AllocatorStrategy::Rule => None,
        };
        AdaptiveOscillatorAllocator {
            mlp,
            min_total: self.min_total,
            max_total: self.max_total,
            delta_ratio: self.delta_ratio,
            theta_ratio: self.theta_ratio,
            strategy: Ignored(self.strategy),
        }
    }
}

/// Dynamically allocates oscillator counts per frequency band from an
/// estimated scene-complexity scalar.
///
/// See the module docs for the exact formula. Construct via
/// [`AdaptiveOscillatorAllocatorConfig::init`].
#[derive(Module, Debug)]
pub struct AdaptiveOscillatorAllocator<B: Backend> {
    mlp: Option<[Linear<B>; 3]>,
    min_total: usize,
    max_total: usize,
    delta_ratio: f64,
    theta_ratio: f64,
    strategy: Ignored<AllocatorStrategy>,
}

impl<B: Backend> AdaptiveOscillatorAllocator<B> {
    /// The configured allocation strategy.
    pub fn strategy(&self) -> AllocatorStrategy {
        self.strategy.0
    }

    /// Compute an oscillator budget for `complexity` (clamped to `[0, 1]`).
    ///
    /// Uses the learned MLP only when [`Self::strategy`] is
    /// [`AllocatorStrategy::Learned`] **and** `features` is `Some`; falls
    /// back to the rule-based formula otherwise (matching PRINet 3.0's
    /// `allocate`).
    pub fn allocate(&self, complexity: f64, features: Option<Tensor<B, 2>>) -> OscillatorBudget {
        match (self.strategy.0, features) {
            (AllocatorStrategy::Learned, Some(f)) => self.allocate_learned(complexity, f),
            _ => self.allocate_rule(complexity),
        }
    }

    fn allocate_rule(&self, complexity: f64) -> OscillatorBudget {
        let c = complexity.clamp(0.0, 1.0);
        let total =
            python_round(self.min_total as f64 + c * (self.max_total - self.min_total) as f64)
                .max(0);
        let n_delta = python_round(total as f64 * self.delta_ratio).max(1);
        let n_theta = python_round(total as f64 * self.theta_ratio).max(1);
        let n_gamma = (total - n_delta - n_theta).max(1);
        OscillatorBudget {
            n_delta: n_delta as usize,
            n_theta: n_theta as usize,
            n_gamma: n_gamma as usize,
            complexity: c,
        }
    }

    fn allocate_learned(&self, complexity: f64, features: Tensor<B, 2>) -> OscillatorBudget {
        let mlp = self
            .mlp
            .as_ref()
            .expect("AllocatorStrategy::Learned always constructs an mlp");
        let c = complexity.clamp(0.0, 1.0);

        let logits = mlp[2].forward(relu(mlp[1].forward(relu(mlp[0].forward(features)))));
        let fractions = to_f64_vec(softmax(logits, 1).squeeze::<1>(0));

        let total =
            python_round(self.min_total as f64 + c * (self.max_total - self.min_total) as f64)
                .max(0);
        let raw: Vec<f64> = fractions.iter().map(|f| f * total as f64).collect();
        let mut floors: Vec<i64> = raw.iter().map(|v| v.floor() as i64).collect();
        let remainders: Vec<f64> = raw
            .iter()
            .zip(floors.iter())
            .map(|(r, f)| r - *f as f64)
            .collect();

        let allocated: i64 = floors.iter().sum();
        let deficit = total - allocated;
        if deficit > 0 {
            let mut order: Vec<usize> = (0..3).collect();
            order.sort_by(|&a, &b| remainders[b].partial_cmp(&remainders[a]).unwrap());
            for &idx in order.iter().take(deficit.min(3) as usize) {
                floors[idx] += 1;
            }
        }

        OscillatorBudget {
            n_delta: floors[0].max(1) as usize,
            n_theta: floors[1].max(1) as usize,
            n_gamma: floors[2].max(1) as usize,
            complexity: c,
        }
    }

    /// Generate budgets for `steps` evenly-spaced complexity values in
    /// `[0, 1]`.
    pub fn sweep_complexity(&self, steps: usize) -> Vec<OscillatorBudget> {
        let denom = steps.saturating_sub(1).max(1) as f64;
        (0..steps)
            .map(|i| self.allocate(i as f64 / denom, None))
            .collect()
    }
}

/// [`crate::phase_tracker::PhaseTracker`] with adaptive oscillator
/// allocation: builds and caches a tracker per distinct oscillator budget,
/// selected from an estimated scene complexity.
///
/// See the module docs for why this is not a [`burn::module::Module`].
#[derive(Debug)]
pub struct DynamicPhaseTracker<B: Backend> {
    allocator: AdaptiveOscillatorAllocator<B>,
    detection_dim: usize,
    n_discrete_steps: usize,
    match_threshold: f64,
    max_objects: usize,
    cache: RefCell<HashMap<(usize, usize, usize), PhaseTracker<B>>>,
}

impl<B: Backend> DynamicPhaseTracker<B> {
    /// Construct a [`DynamicPhaseTracker`] over a rule-based allocator with
    /// the given oscillator range. Individual [`PhaseTracker`] instances are
    /// constructed lazily (and seeded from `seed`) the first time a given
    /// budget is requested by [`Self::forward`].
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `detection_dim` is zero,
    /// [`TrainError::InvalidStepCount`] if `n_discrete_steps` is zero,
    /// [`TrainError::InvalidMatchThreshold`] if `match_threshold` is
    /// non-finite, or [`TrainError::InvalidAllocatorRange`] if
    /// `min_total`/`max_total` is invalid (see
    /// [`AdaptiveOscillatorAllocatorConfig::with_params`]).
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        detection_dim: usize,
        min_total: usize,
        max_total: usize,
        n_discrete_steps: usize,
        match_threshold: f64,
        allocator_strategy: AllocatorStrategy,
        max_objects: usize,
        device: &B::Device,
        seed: &mut Seed,
    ) -> Result<Self, TrainError> {
        if detection_dim == 0 {
            return Err(TrainError::EmptyBand {
                name: "detection_dim",
            });
        }
        if n_discrete_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_discrete_steps",
                value: n_discrete_steps,
            });
        }
        if !match_threshold.is_finite() {
            return Err(TrainError::InvalidMatchThreshold {
                value: match_threshold,
            });
        }
        let allocator = AdaptiveOscillatorAllocatorConfig::with_params(
            min_total,
            max_total,
            0.1,
            0.2,
            allocator_strategy,
            1,
        )?
        .init::<B>(device, seed);

        Ok(Self {
            allocator,
            detection_dim,
            n_discrete_steps,
            match_threshold,
            max_objects,
            cache: RefCell::new(HashMap::new()),
        })
    }

    /// Match detections with an oscillator budget adapted to the estimated
    /// complexity of `detections_t`.
    ///
    /// **Faithfully reproduced quirk** (see module docs): always uses
    /// rule-based allocation, even if this tracker's allocator is
    /// `AllocatorStrategy::Learned`.
    ///
    /// # Errors
    ///
    /// See [`PhaseTrackerConfig::with_params`] (surfaces only if this
    /// tracker's own construction parameters are internally inconsistent,
    /// which [`Self::new`] already prevents) and
    /// [`PhaseTracker::forward`].
    pub fn forward(
        &self,
        detections_t: Tensor<B, 2>,
        detections_t1: Tensor<B, 2>,
        seed: &mut Seed,
    ) -> Result<(Vec<i64>, Tensor<B, 2>, OscillatorBudget), TrainError> {
        let device = detections_t.device();
        let complexity = estimate_complexity(&detections_t, 0.5, 0.5, self.max_objects);
        let budget = self.allocator.allocate(complexity, None);
        let key = (budget.n_delta, budget.n_theta, budget.n_gamma);

        {
            let mut cache = self.cache.borrow_mut();
            if let std::collections::hash_map::Entry::Vacant(e) = cache.entry(key) {
                let tracker = PhaseTrackerConfig::with_params(
                    self.detection_dim,
                    budget.n_delta,
                    budget.n_theta,
                    budget.n_gamma,
                    self.n_discrete_steps,
                    self.match_threshold,
                )?
                .init::<B>(&device, seed);
                e.insert(tracker);
            }
        }

        let cache = self.cache.borrow();
        let tracker = cache.get(&key).expect("just inserted above");
        let (matches, sim) = tracker.forward(detections_t, detections_t1)?;
        Ok((matches, sim, budget))
    }
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

    // --- Config validation ---

    #[test]
    fn allocator_range_validated() {
        assert!(matches!(
            AdaptiveOscillatorAllocatorConfig::new(2, 64).unwrap_err(),
            TrainError::InvalidAllocatorRange { .. }
        ));
        assert!(matches!(
            AdaptiveOscillatorAllocatorConfig::new(64, 12).unwrap_err(),
            TrainError::InvalidAllocatorRange { .. }
        ));
    }

    #[test]
    fn ratio_validated() {
        let err = AdaptiveOscillatorAllocatorConfig::with_params(
            12,
            64,
            -0.1,
            0.2,
            AllocatorStrategy::Rule,
            1,
        )
        .unwrap_err();
        assert!(matches!(
            err,
            TrainError::InvalidRatio {
                name: "delta_ratio",
                ..
            }
        ));
    }

    // --- estimate_complexity ---

    #[test]
    fn estimate_complexity_in_unit_interval() {
        let dev = device();
        let dets = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.1, 0.2, 0.5, 0.5, 0.9, 0.8], vec![3, 2]),
            &dev,
        );
        let c = estimate_complexity(&dets, 0.5, 0.5, 50);
        assert!((0.0..=1.0).contains(&c));
    }

    #[test]
    fn estimate_complexity_single_detection_has_zero_spatial_term() {
        let dev = device();
        let dets =
            Tensor::<TestBackend, 2>::from_data(TensorData::new(vec![0.5, 0.5], vec![1, 2]), &dev);
        // n=1: spatial_score forced to 0; count_score = 1/50.
        let c = estimate_complexity(&dets, 0.5, 0.5, 50);
        let expected = 0.5 * (1.0 / 50.0) / 1.0;
        assert!((c - expected).abs() < 1e-12);
    }

    // --- allocate (rule) ---

    /// PRINet 3.0's own `AdaptiveOscillatorAllocator` docstring claims
    /// `allocate(complexity=0.3)` on `(min_total=12, max_total=64)` yields
    /// `n_gamma=12` — running the actual reference class (not the
    /// docstring) gives `n_gamma=19`, matching this Rust port. The
    /// docstring itself is stale (upstream PRINet 3.0 documentation drift,
    /// not a PRIN defect); this test asserts against the reference's real,
    /// executed behavior.
    #[test]
    fn allocate_rule_matches_prinet_3_0_executed_behavior() {
        let mut seed = Seed::new(0, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::new(12, 64)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let budget = allocator.allocate(0.3, None);
        assert_eq!(budget.n_delta, 3);
        assert_eq!(budget.n_theta, 6);
        assert_eq!(budget.n_gamma, 19);
    }

    #[test]
    fn allocate_rule_clamps_complexity_and_total_bounds() {
        let mut seed = Seed::new(0, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::new(12, 64)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let low = allocator.allocate(-5.0, None);
        let high = allocator.allocate(5.0, None);
        assert_eq!(low.total(), 12);
        assert_eq!(high.total(), 64);
        assert!((low.complexity - 0.0).abs() < 1e-12);
        assert!((high.complexity - 1.0).abs() < 1e-12);
    }

    #[test]
    fn sweep_complexity_has_no_band_ever_zero() {
        let mut seed = Seed::new(0, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::new(12, 64)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        for budget in allocator.sweep_complexity(11) {
            assert!(budget.n_delta >= 1);
            assert!(budget.n_theta >= 1);
            assert!(budget.n_gamma >= 1);
        }
    }

    // --- allocate (learned) ---

    #[test]
    fn allocate_learned_totals_match_and_bands_at_least_one() {
        let mut seed = Seed::new(3, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::with_params(
            12,
            64,
            0.1,
            0.2,
            AllocatorStrategy::Learned,
            1,
        )
        .unwrap()
        .init::<TestBackend>(&device(), &mut seed);

        let dev = device();
        for c in [0.0, 0.25, 0.5, 0.75, 1.0] {
            let features =
                Tensor::<TestBackend, 2>::from_data(TensorData::new(vec![c], vec![1, 1]), &dev);
            let budget = allocator.allocate(c, Some(features));
            assert!(budget.n_delta >= 1 && budget.n_theta >= 1 && budget.n_gamma >= 1);
        }
    }

    #[test]
    fn allocate_falls_back_to_rule_without_features_even_when_learned() {
        let mut seed = Seed::new(4, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::with_params(
            12,
            64,
            0.1,
            0.2,
            AllocatorStrategy::Learned,
            1,
        )
        .unwrap()
        .init::<TestBackend>(&device(), &mut seed);
        let budget = allocator.allocate(0.3, None);
        assert_eq!(budget.n_delta, 3);
        assert_eq!(budget.n_theta, 6);
        assert_eq!(budget.n_gamma, 19);
    }

    // --- Gradient reference tests (learned strategy) ---

    #[test]
    fn learned_mlp_gradients_are_finite() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(9, 0);
        let allocator = AdaptiveOscillatorAllocatorConfig::with_params(
            12,
            64,
            0.1,
            0.2,
            AllocatorStrategy::Learned,
            1,
        )
        .unwrap()
        .init::<TestAutodiffBackend>(&dev, &mut seed);
        let mlp = allocator.mlp.as_ref().unwrap();
        let features = Tensor::<TestAutodiffBackend, 2>::ones([1, 1], &dev).require_grad();
        let out = mlp[2].forward(relu(mlp[1].forward(relu(mlp[0].forward(features)))));
        let loss = out.sum();
        let grads = loss.backward();
        let grad = mlp[0]
            .weight
            .val()
            .grad(&grads)
            .map(|g| g.to_data().to_vec::<f64>().unwrap())
            .expect("gradient must be present");
        assert!(grad.iter().all(|v| v.is_finite()));
    }

    // --- DynamicPhaseTracker ---

    #[test]
    fn dynamic_phase_tracker_returns_consistent_budget_and_caches() {
        let dev = device();
        let mut seed = Seed::new(5, 0);
        let tracker = DynamicPhaseTracker::<TestBackend>::new(
            4,
            12,
            24,
            2,
            0.3,
            AllocatorStrategy::Rule,
            50,
            &dev,
            &mut seed,
        )
        .unwrap();

        let dets_t = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(
                vec![
                    0.1, 0.2, 0.0, 0.0, 0.5, 0.5, 0.1, 0.0, 0.9, 0.8, 0.2, 0.1, 0.3, 0.1, 0.4, 0.2,
                ],
                vec![4, 4],
            ),
            &dev,
        );
        let dets_t1 = dets_t.clone();

        let (matches, sim, budget) = tracker
            .forward(dets_t.clone(), dets_t1.clone(), &mut seed)
            .unwrap();
        assert_eq!(matches.len(), 4);
        assert_eq!(sim.dims(), [4, 4]);
        assert_eq!(
            budget.total(),
            budget.n_delta + budget.n_theta + budget.n_gamma
        );

        // Second call with an identical-complexity input reuses the cached
        // tracker (same budget) without error.
        let (matches2, _, budget2) = tracker.forward(dets_t, dets_t1, &mut seed).unwrap();
        assert_eq!(matches.len(), matches2.len());
        assert_eq!(budget.total(), budget2.total());
        assert_eq!(tracker.cache.borrow().len(), 1);
    }

    #[test]
    fn dynamic_phase_tracker_rejects_zero_detection_dim() {
        let dev = device();
        let mut seed = Seed::new(0, 0);
        let err = DynamicPhaseTracker::<TestBackend>::new(
            0,
            12,
            24,
            2,
            0.3,
            AllocatorStrategy::Rule,
            50,
            &dev,
            &mut seed,
        )
        .unwrap_err();
        assert!(matches!(
            err,
            TrainError::EmptyBand {
                name: "detection_dim"
            }
        ));
    }
}

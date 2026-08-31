//! Typed errors for trainable-primitive construction and state contracts.

use thiserror::Error;

/// Errors raised by [`crate::bands`] and [`crate::layers`] module construction,
/// parameter validation, and state contracts.
#[derive(Debug, Error, PartialEq)]
pub enum TrainError {
    /// A band or oscillator population was configured with zero size.
    #[error("{name} requires at least one oscillator, got 0")]
    EmptyBand {
        /// Name of the offending band/population.
        name: &'static str,
    },

    /// A tensor did not have the expected shape.
    #[error("{name} expected shape {expected:?}, got {got:?}")]
    ShapeMismatch {
        /// Name of the offending tensor.
        name: &'static str,
        /// Expected shape.
        expected: Vec<usize>,
        /// Actual shape.
        got: Vec<usize>,
    },

    /// A scalar hyperparameter was non-finite.
    #[error("non-finite parameter `{name}`: {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// A named scalar hyperparameter was not strictly positive.
    #[error("{name} must be finite and > 0, got {value}")]
    InvalidPositiveParameter {
        /// Parameter name.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// A timestep was non-finite or non-positive.
    #[error("invalid timestep dt = {value}, must be finite and > 0")]
    InvalidTimestep {
        /// Offending value.
        value: f64,
    },

    /// (`strict-checks`) A tensor contained a non-finite value.
    #[error("non-finite value in `{name}`")]
    NonFiniteState {
        /// Name of the offending tensor.
        name: &'static str,
    },

    /// A feedback-inhibition top-`k` winner count was zero.
    #[error("k must be >= 1, got {k}")]
    InvalidTopK {
        /// Offending value.
        k: usize,
    },

    /// A sparsity fraction fell outside `(0, 1]`.
    #[error("sparsity must be in (0, 1], got {value}")]
    InvalidSparsity {
        /// Offending value.
        value: f64,
    },

    /// A Holomorphic Equilibrium Propagation nudge strength `beta` was
    /// non-positive or non-finite.
    #[error("beta must be finite and > 0, got {value}")]
    InvalidBeta {
        /// Offending value.
        value: f64,
    },

    /// An integration step count was zero.
    #[error("{name} must be >= 1, got {value}")]
    InvalidStepCount {
        /// Name of the offending parameter.
        name: &'static str,
        /// Offending value.
        value: usize,
    },

    /// An optimizer learning rate was negative or non-finite.
    #[error("Invalid learning rate: {value}")]
    InvalidLearningRate {
        /// Offending value.
        value: f64,
    },

    /// An optimizer momentum factor was negative or non-finite.
    #[error("Invalid momentum value: {value}")]
    InvalidMomentum {
        /// Offending value.
        value: f64,
    },

    /// An optimizer weight-decay coefficient was negative or non-finite.
    #[error("Invalid weight_decay value: {value}")]
    InvalidWeightDecay {
        /// Offending value.
        value: f64,
    },

    /// A `SyncGd` synchronization-penalty weight was negative or non-finite.
    #[error("Invalid sync_penalty value: {value}")]
    InvalidSyncPenalty {
        /// Offending value.
        value: f64,
    },

    /// A `SyncGd` critical order-parameter threshold fell outside `[0, 1]`.
    #[error("critical_order must be in [0, 1], got {value}")]
    InvalidCriticalOrder {
        /// Offending value.
        value: f64,
    },

    /// A `Rip` target amplitude was non-positive or non-finite.
    #[error("target_amplitude must be positive, got {value}")]
    InvalidTargetAmplitude {
        /// Offending value.
        value: f64,
    },

    /// A `Scalr` minimum learning-rate fraction fell outside `[0, 1]`.
    #[error("r_min must be in [0, 1], got {value}")]
    InvalidRMin {
        /// Offending value.
        value: f64,
    },

    /// A `Scalr` synchronization-sensitivity exponent was non-positive or
    /// non-finite.
    #[error("alpha must be positive, got {value}")]
    InvalidAlpha {
        /// Offending value.
        value: f64,
    },

    /// A multi-head attention `d_model` was not evenly divisible by
    /// `n_heads`.
    #[error("d_model ({d_model}) must be divisible by n_heads ({n_heads})")]
    IndivisibleHeads {
        /// Model dimension.
        d_model: usize,
        /// Number of attention heads.
        n_heads: usize,
    },

    /// A dropout probability fell outside `[0, 1)`.
    #[error("dropout must be in [0, 1), got {value}")]
    InvalidDropout {
        /// Offending value.
        value: f64,
    },

    /// A named fraction/ratio hyperparameter fell outside `[0, 1]` or was
    /// non-finite.
    #[error("{name} must be finite and in [0, 1], got {value}")]
    InvalidRatio {
        /// Name of the offending hyperparameter.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// An [`crate::allocation::AdaptiveOscillatorAllocator`] total-oscillator
    /// range was invalid: `min_total < 3` or `max_total < min_total`.
    #[error(
        "invalid allocator range: min_total={min_total} (must be >= 3), \
         max_total={max_total} (must be >= min_total)"
    )]
    InvalidAllocatorRange {
        /// Configured minimum total oscillator count.
        min_total: usize,
        /// Configured maximum total oscillator count.
        max_total: usize,
    },

    /// A match/similarity threshold hyperparameter was non-finite.
    #[error("match_threshold must be finite, got {value}")]
    InvalidMatchThreshold {
        /// Offending value.
        value: f64,
    },

    /// An [`crate::allocation::AdaptiveOscillatorAllocator`] checkpoint was
    /// loaded from a donor with a different [`crate::allocation::AllocatorStrategy`]
    /// than the target. `Option<[burn::nn::Linear<B>; 3]>`'s `load_record`
    /// silently keeps `self`'s `Some`/`None` variant on a mismatch, so
    /// without this explicit check the strategy disagreement is
    /// undetectable from the loaded value alone.
    #[error(
        "allocator strategy mismatch: module is {module_strategy} but \
         checkpoint is {checkpoint_strategy}"
    )]
    StrategyMismatch {
        /// Target allocator's strategy (before load).
        module_strategy: &'static str,
        /// Donor checkpoint's strategy (inferred from `mlp` presence).
        checkpoint_strategy: &'static str,
    },

    /// A [`crate::stats`] routine received fewer than the minimum number of
    /// samples its formula requires (e.g. Welch's t-test needs at least 2
    /// observations per group to estimate a variance).
    #[error("{name} requires at least {min} samples, got {got}")]
    InsufficientSamples {
        /// Name of the offending input.
        name: &'static str,
        /// Minimum required sample count.
        min: usize,
        /// Actual sample count.
        got: usize,
    },

    /// A [`crate::stats::bootstrap_ci`] significance level was not in the
    /// open interval `(0, 1)`.
    #[error("alpha must be finite and in (0, 1), got {value}")]
    InvalidSignificanceLevel {
        /// Offending value.
        value: f64,
    },

    /// A [`crate::stats::bootstrap_ci`] resample count was zero.
    #[error("n_bootstrap must be >= 1, got {value}")]
    InvalidBootstrapCount {
        /// Offending value.
        value: usize,
    },

    /// A [`crate::adversarial`] perturbation budget (`epsilon`) or step size
    /// (`alpha`) was non-positive or non-finite.
    #[error("{name} must be finite and > 0, got {value}")]
    InvalidPerturbationBudget {
        /// Name of the offending hyperparameter (`epsilon` or `alpha`).
        name: &'static str,
        /// Offending value.
        value: f64,
    },
}

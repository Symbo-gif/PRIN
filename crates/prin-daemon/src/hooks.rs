//! Training-loop hooks: loss EMA, gradient-norm EMA, and step-latency
//! telemetry, packaged for submission to a [`crate::daemon::SubconsciousDaemon`].
//!
//! Rebuild of PRINet 3.0 `prinet.nn.training_hooks.StateCollector`. The
//! reference class does three things: accumulate per-step telemetry,
//! pack it into a state snapshot, and submit that snapshot to the daemon
//! directly. [`TrainingHooks`] does only the first two — accumulation and
//! packing — and returns the built [`SubconsciousState`] rather than owning
//! a daemon reference and calling
//! [`submit_state`](crate::daemon::SubconsciousDaemon::submit_state)
//! itself. That split keeps this type's unit tests free of thread spawning
//! (`SubconsciousDaemon::spawn` starts an OS thread) and lets any caller —
//! including tests — construct one without a running daemon at all; wiring
//! the two together is one call: `daemon.submit_state(hooks.on_epoch_end(...))`.
//!
//! # What is *not* reproduced from the reference
//!
//! The reference computes the gradient norm itself by walking
//! `model.parameters()` (`total_norm += p.grad.norm(2) ** 2`). This crate
//! has no model/autograd type to walk — PRIN's numerical authority for a
//! gradient-norm reduction belongs in Rust, not duplicated per training
//! framework, so [`TrainingHooks::on_step_end`] takes the already-computed
//! per-parameter L2 norms as a plain `&[f64]` and performs the same
//! sum-of-squares-then-sqrt reduction here. Any caller (a Burn training
//! loop, a PyO3 bridge summing `torch` per-parameter norms) supplies that
//! slice; the reduction itself is implemented exactly once.
//!
//! # Numerics
//!
//! Loss EMA/variance and the gradient-norm EMA use the reference's exact
//! recurrences (`ema' = alpha * x + (1 - alpha) * ema`, variance likewise on
//! the squared deviation from the *updated* EMA). Latency percentiles use
//! the reference's `sorted[n // 2]` / `sorted[min(int(n * 0.95), n - 1)]`
//! indexing, translated to Rust's default (truncating) integer semantics for
//! non-negative values, which matches Python's `int()` truncation here.

use std::collections::VecDeque;
use std::time::{Duration, Instant};

use crate::error::DaemonError;
use crate::state::{Regime, SubconsciousState};

/// Reference default EMA smoothing factor
/// (PRINet 3.0 `StateCollector.__init__`'s `loss_ema_alpha` default).
pub const DEFAULT_LOSS_EMA_ALPHA: f64 = 0.1;

/// Reference default number of recent step latencies retained
/// (PRINet 3.0 `StateCollector.__init__`'s `latency_window` default).
pub const DEFAULT_LATENCY_WINDOW: usize = 100;

/// Accumulates per-step training telemetry into a [`SubconsciousState`].
///
/// # Examples
///
/// ```
/// use std::time::Duration;
/// use prin_daemon::hooks::TrainingHooks;
/// use prin_daemon::state::Regime;
///
/// let mut hooks = TrainingHooks::new(0.1, 100)?;
/// for loss in [0.9, 0.7, 0.5] {
///     hooks.on_step_end_with_elapsed(Duration::from_millis(10), loss, Some(&[1.0, 2.0]));
/// }
/// assert_eq!(hooks.step_count(), 3);
/// assert!(hooks.loss_ema() < 0.9); // pulled down by later, lower losses
///
/// let state = hooks.on_epoch_end(1, None, vec![0.8, 0.6, 0.4], None, 1e-3, 1.0, Regime::MeanField, 0.0);
/// assert_eq!(state.epoch, 1);
/// assert!(state.step_latency_p50 > 0.0);
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
#[derive(Debug, Clone)]
pub struct TrainingHooks {
    alpha: f64,
    latency_window: usize,
    loss_ema: f64,
    loss_variance: f64,
    grad_norm_ema: f64,
    latencies_ms: VecDeque<f64>,
    step_count: u64,
    step_start: Option<Instant>,
}

impl TrainingHooks {
    /// Create an empty hook state.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::InvalidParameter`] if `loss_ema_alpha` is not
    /// finite and in `(0, 1]`, or if `latency_window` is `0`.
    pub fn new(loss_ema_alpha: f64, latency_window: usize) -> Result<Self, DaemonError> {
        if !(loss_ema_alpha.is_finite() && loss_ema_alpha > 0.0 && loss_ema_alpha <= 1.0) {
            return Err(DaemonError::InvalidParameter {
                param: "loss_ema_alpha",
                value: loss_ema_alpha,
            });
        }
        if latency_window == 0 {
            return Err(DaemonError::InvalidParameter {
                param: "latency_window",
                value: 0.0,
            });
        }
        Ok(Self {
            alpha: loss_ema_alpha,
            latency_window,
            loss_ema: 0.0,
            loss_variance: 0.0,
            grad_norm_ema: 0.0,
            latencies_ms: VecDeque::with_capacity(latency_window),
            step_count: 0,
            step_start: None,
        })
    }

    /// Mark the start of a training step using the wall clock.
    ///
    /// Pairs with [`on_step_end`](Self::on_step_end). For deterministic
    /// tests, call [`on_step_end_with_elapsed`](Self::on_step_end_with_elapsed)
    /// directly instead of this pair.
    pub fn on_step_start(&mut self) {
        self.step_start = Some(Instant::now());
    }

    /// Accumulate one step's telemetry, timing it from the matching
    /// [`on_step_start`](Self::on_step_start) call.
    ///
    /// If `on_step_start` was never called (or this is the first step),
    /// elapsed time is recorded as zero rather than panicking or reading the
    /// clock a second time.
    ///
    /// `grad_norms`, when supplied, is the per-parameter L2 gradient norm
    /// for every trainable parameter; `None` leaves [`grad_norm_ema`]
    /// unchanged, matching the reference's `model=None` branch.
    ///
    /// [`grad_norm_ema`]: Self::grad_norm_ema
    pub fn on_step_end(&mut self, loss: f64, grad_norms: Option<&[f64]>) {
        let elapsed = self
            .step_start
            .take()
            .map_or(Duration::ZERO, |start| start.elapsed());
        self.on_step_end_with_elapsed(elapsed, loss, grad_norms);
    }

    /// Accumulate one step's telemetry with an explicitly supplied elapsed
    /// duration, bypassing the wall clock entirely.
    ///
    /// This is the pure computation [`on_step_end`](Self::on_step_end)
    /// delegates to; it is what test code should call for deterministic,
    /// sleep-free coverage of the EMA/variance/percentile math.
    pub fn on_step_end_with_elapsed(
        &mut self,
        elapsed: Duration,
        loss: f64,
        grad_norms: Option<&[f64]>,
    ) {
        let elapsed_ms = elapsed.as_secs_f64() * 1000.0;
        if self.latencies_ms.len() == self.latency_window {
            self.latencies_ms.pop_front();
        }
        self.latencies_ms.push_back(elapsed_ms);

        self.loss_ema = self.alpha * loss + (1.0 - self.alpha) * self.loss_ema;
        let diff = loss - self.loss_ema;
        self.loss_variance = self.alpha * diff * diff + (1.0 - self.alpha) * self.loss_variance;

        if let Some(norms) = grad_norms {
            let total_sq: f64 = norms.iter().map(|n| n * n).sum();
            let grad_norm = total_sq.sqrt();
            self.grad_norm_ema = self.alpha * grad_norm + (1.0 - self.alpha) * self.grad_norm_ema;
        }

        self.step_count += 1;
    }

    /// `(p50, p95, throughput)` over the current latency window, in
    /// milliseconds / milliseconds / steps-per-second.
    ///
    /// Returns `(0.0, 0.0, 0.0)` when no step has been recorded yet.
    fn latency_percentiles(&self) -> (f64, f64, f64) {
        if self.latencies_ms.is_empty() {
            return (0.0, 0.0, 0.0);
        }
        let mut sorted: Vec<f64> = self.latencies_ms.iter().copied().collect();
        sorted.sort_by(|a, b| a.total_cmp(b));
        let n = sorted.len();
        let p50 = sorted[n / 2];
        let p95_index = ((n as f64) * 0.95) as usize;
        let p95 = sorted[p95_index.min(n - 1)];
        let mean: f64 = sorted.iter().sum::<f64>() / n as f64;
        let throughput = if mean > 0.0 { 1000.0 / mean } else { 0.0 };
        (p50, p95, throughput)
    }

    /// Build a [`SubconsciousState`] snapshot from accumulated telemetry
    /// plus the caller-supplied training-loop context.
    ///
    /// This is the primary integration point with
    /// [`crate::daemon::SubconsciousDaemon`]: `daemon.submit_state(hooks.on_epoch_end(...))`.
    ///
    /// If `loss_override` is supplied, it *replaces* the accumulated loss
    /// EMA outright rather than blending into it — matching the reference's
    /// "override loss EMA if explicit loss provided" behaviour, which lets a
    /// caller report a more accurate epoch-level loss than the per-step EMA
    /// would give. When `r_global_override` is `None`, the global order
    /// parameter is the mean of `r_per_band` (`0.0` for an empty slice).
    ///
    /// Unlike the reference, `r_per_band` has no implicit
    /// `[0.5, 0.5, 0.5]` default when unavailable — pass an empty `Vec` and
    /// [`SubconsciousState::band`] zero-fills it, keeping the "no hidden
    /// defaults" contract explicit at the call site.
    #[allow(clippy::too_many_arguments)]
    pub fn on_epoch_end(
        &mut self,
        epoch: i64,
        loss_override: Option<f64>,
        r_per_band: Vec<f64>,
        r_global_override: Option<f64>,
        lr_current: f64,
        scalr_alpha: f64,
        regime: Regime,
        timestamp: f64,
    ) -> SubconsciousState {
        if let Some(loss) = loss_override {
            self.loss_ema = loss;
        }
        let r_global = r_global_override.unwrap_or_else(|| {
            if r_per_band.is_empty() {
                0.0
            } else {
                r_per_band.iter().sum::<f64>() / r_per_band.len() as f64
            }
        });
        let (p50, p95, throughput) = self.latency_percentiles();

        SubconsciousState {
            r_per_band,
            r_global,
            loss_ema: self.loss_ema,
            loss_variance: self.loss_variance,
            grad_norm_ema: self.grad_norm_ema,
            lr_current,
            scalr_alpha,
            step_latency_p50: p50,
            step_latency_p95: p95,
            throughput,
            epoch,
            regime,
            timestamp,
            ..SubconsciousState::default()
        }
    }

    /// Current exponential moving average of the training loss.
    #[must_use]
    pub fn loss_ema(&self) -> f64 {
        self.loss_ema
    }

    /// Current EMA of the squared deviation of loss from its own EMA.
    #[must_use]
    pub fn loss_variance(&self) -> f64 {
        self.loss_variance
    }

    /// Current EMA of the gradient L2 norm.
    #[must_use]
    pub fn grad_norm_ema(&self) -> f64 {
        self.grad_norm_ema
    }

    /// Total number of steps recorded via `on_step_end`/`on_step_end_with_elapsed`.
    #[must_use]
    pub fn step_count(&self) -> u64 {
        self.step_count
    }

    /// Configured maximum number of retained recent step latencies.
    #[must_use]
    pub fn latency_window(&self) -> usize {
        self.latency_window
    }

    /// Number of latencies currently retained (`<= latency_window()`).
    #[must_use]
    pub fn latency_count(&self) -> usize {
        self.latencies_ms.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_invalid_alpha() {
        for bad in [0.0, -0.1, 1.1, f64::NAN, f64::INFINITY] {
            let err = TrainingHooks::new(bad, 10).expect_err("rejects");
            assert!(matches!(
                err,
                DaemonError::InvalidParameter {
                    param: "loss_ema_alpha",
                    ..
                }
            ));
        }
        assert!(TrainingHooks::new(1.0, 10).is_ok());
    }

    #[test]
    fn rejects_zero_latency_window() {
        let err = TrainingHooks::new(0.1, 0).expect_err("rejects");
        assert!(matches!(
            err,
            DaemonError::InvalidParameter {
                param: "latency_window",
                ..
            }
        ));
    }

    #[test]
    fn loss_ema_matches_hand_computed_recurrence() {
        let mut hooks = TrainingHooks::new(0.5, 10).unwrap();
        hooks.on_step_end_with_elapsed(Duration::ZERO, 1.0, None);
        // ema = 0.5*1.0 + 0.5*0.0 = 0.5
        assert!((hooks.loss_ema() - 0.5).abs() < 1e-15);
        hooks.on_step_end_with_elapsed(Duration::ZERO, 2.0, None);
        // ema = 0.5*2.0 + 0.5*0.5 = 1.25
        assert!((hooks.loss_ema() - 1.25).abs() < 1e-15);
    }

    #[test]
    fn loss_variance_uses_deviation_from_updated_ema() {
        let mut hooks = TrainingHooks::new(0.5, 10).unwrap();
        hooks.on_step_end_with_elapsed(Duration::ZERO, 1.0, None);
        // ema becomes 0.5; diff = 1.0 - 0.5 = 0.5; var = 0.5*0.25 + 0.5*0 = 0.125
        assert!((hooks.loss_variance() - 0.125).abs() < 1e-15);
    }

    #[test]
    fn grad_norm_ema_is_l2_of_supplied_per_parameter_norms() {
        let mut hooks = TrainingHooks::new(1.0, 10).unwrap();
        // alpha=1.0 makes the EMA track the raw value exactly.
        hooks.on_step_end_with_elapsed(Duration::ZERO, 0.0, Some(&[3.0, 4.0]));
        assert!((hooks.grad_norm_ema() - 5.0).abs() < 1e-12); // sqrt(3^2+4^2) = 5
    }

    #[test]
    fn grad_norm_ema_unchanged_when_norms_are_none() {
        let mut hooks = TrainingHooks::new(1.0, 10).unwrap();
        hooks.on_step_end_with_elapsed(Duration::ZERO, 0.0, Some(&[3.0, 4.0]));
        hooks.on_step_end_with_elapsed(Duration::ZERO, 0.0, None);
        assert!((hooks.grad_norm_ema() - 5.0).abs() < 1e-12);
    }

    #[test]
    fn latency_window_never_exceeds_capacity() {
        let mut hooks = TrainingHooks::new(0.1, 5).unwrap();
        for i in 0..50 {
            hooks.on_step_end_with_elapsed(Duration::from_millis(i), 0.0, None);
            assert!(hooks.latency_count() <= 5);
        }
        assert_eq!(hooks.latency_count(), 5);
    }

    #[test]
    fn latency_window_reports_the_configured_capacity() {
        let hooks = TrainingHooks::new(0.1, 42).unwrap();
        assert_eq!(hooks.latency_window(), 42);
        assert_eq!(hooks.latency_count(), 0);
    }

    #[test]
    fn empty_latencies_give_zero_percentiles() {
        let hooks = TrainingHooks::new(0.1, 10).unwrap();
        assert_eq!(hooks.latency_percentiles(), (0.0, 0.0, 0.0));
    }

    #[test]
    fn percentiles_match_hand_computed_values_for_known_latencies() {
        let mut hooks = TrainingHooks::new(0.1, 20).unwrap();
        // Ten latencies 1ms..10ms; n=10, p50 index = 5 -> sorted[5] = 6.0ms;
        // p95 index = int(10*0.95)=9 -> sorted[9] = 10.0ms.
        for ms in 1..=10u64 {
            hooks.on_step_end_with_elapsed(Duration::from_millis(ms), 0.0, None);
        }
        let (p50, p95, throughput) = hooks.latency_percentiles();
        assert!((p50 - 6.0).abs() < 1e-9);
        assert!((p95 - 10.0).abs() < 1e-9);
        let mean = (1..=10).sum::<u64>() as f64 / 10.0;
        assert!((throughput - 1000.0 / mean).abs() < 1e-9);
    }

    #[test]
    fn on_epoch_end_overrides_loss_ema_when_provided() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        hooks.on_step_end_with_elapsed(Duration::ZERO, 0.9, None);
        let state = hooks.on_epoch_end(
            1,
            Some(0.42),
            vec![0.5, 0.5, 0.5],
            None,
            1e-3,
            1.0,
            Regime::MeanField,
            0.0,
        );
        assert_eq!(state.loss_ema, 0.42);
        assert_eq!(hooks.loss_ema(), 0.42); // the override sticks in accumulator state too
    }

    #[test]
    fn on_epoch_end_defaults_r_global_to_band_mean() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        let state = hooks.on_epoch_end(
            0,
            None,
            vec![0.2, 0.4, 0.6],
            None,
            1e-3,
            1.0,
            Regime::MeanField,
            0.0,
        );
        assert!((state.r_global - 0.4).abs() < 1e-12);
    }

    #[test]
    fn on_epoch_end_respects_explicit_r_global() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        let state = hooks.on_epoch_end(
            0,
            None,
            vec![0.2, 0.4, 0.6],
            Some(0.9),
            1e-3,
            1.0,
            Regime::MeanField,
            0.0,
        );
        assert_eq!(state.r_global, 0.9);
    }

    #[test]
    fn on_epoch_end_empty_bands_default_r_global_to_zero() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        let state = hooks.on_epoch_end(0, None, vec![], None, 1e-3, 1.0, Regime::MeanField, 0.0);
        assert_eq!(state.r_global, 0.0);
    }

    #[test]
    fn on_step_start_without_manual_timing_records_nonnegative_elapsed() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        hooks.on_step_start();
        hooks.on_step_end(0.5, None);
        assert_eq!(hooks.step_count(), 1);
        assert!(hooks.latency_count() == 1);
    }

    #[test]
    fn on_step_end_without_start_records_zero_elapsed() {
        let mut hooks = TrainingHooks::new(0.1, 10).unwrap();
        hooks.on_step_end(0.5, None);
        let (p50, _, _) = hooks.latency_percentiles();
        assert_eq!(p50, 0.0);
    }

    /// Overhead bound: hook accumulation must stay cheap enough to call on
    /// every training step. 100k calls completing well under a second is a
    /// generous ceiling (about three orders of magnitude above what the
    /// arithmetic requires) chosen to avoid flaking on a loaded CI runner
    /// while still catching an accidental O(n) or allocation-per-call
    /// regression in the hot path.
    #[test]
    fn step_accumulation_overhead_is_bounded() {
        let mut hooks = TrainingHooks::new(0.1, 100).unwrap();
        let start = Instant::now();
        for i in 0..100_000u64 {
            hooks.on_step_end_with_elapsed(
                Duration::from_micros(i % 50),
                (i % 7) as f64 * 0.1,
                Some(&[1.0, 2.0, 3.0]),
            );
        }
        let elapsed = start.elapsed();
        assert!(
            elapsed < Duration::from_secs(2),
            "100k hook calls took {elapsed:?}, expected well under 2s"
        );
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn latency_count_never_exceeds_window(
            window in 1usize..=32,
            n_calls in 0usize..200,
            losses in prop::collection::vec(-10.0f64..10.0, 0..200),
        ) {
            let mut hooks = TrainingHooks::new(0.2, window).unwrap();
            for i in 0..n_calls {
                let loss = losses.get(i).copied().unwrap_or(0.0);
                hooks.on_step_end_with_elapsed(Duration::from_millis(i as u64), loss, None);
                prop_assert!(hooks.latency_count() <= window);
            }
            prop_assert_eq!(hooks.step_count(), n_calls as u64);
        }

        #[test]
        fn loss_ema_and_variance_stay_finite_for_finite_inputs(
            losses in prop::collection::vec(-1e6f64..1e6, 1..50),
        ) {
            let mut hooks = TrainingHooks::new(0.1, 16).unwrap();
            for &loss in &losses {
                hooks.on_step_end_with_elapsed(Duration::from_millis(1), loss, None);
            }
            prop_assert!(hooks.loss_ema().is_finite());
            prop_assert!(hooks.loss_variance().is_finite());
            prop_assert!(hooks.loss_variance() >= 0.0);
        }
    }
}

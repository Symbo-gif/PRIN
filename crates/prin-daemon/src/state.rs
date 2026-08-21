//! Subconscious controller state and control-signal types.
//!
//! Rebuild of PRINet 3.0 `prinet/core/subconscious.py`
//! ([`SubconsciousState`], [`ControlSignals`]). The thread-safe
//! `ControlSignalBuffer` of the reference module is deliberately **not** part
//! of this work package — the daemon runtime and its lock-free control buffer
//! are WP-029 scope (session 0113).
//!
//! # Numerical contract
//!
//! PRINet 3.0 packs the state snapshot with
//! `np.array([...], dtype=np.float32)`: every element is computed in Python
//! `float` (IEEE-754 binary64) and then rounded once to binary32. This module
//! reproduces that exactly — all arithmetic is `f64`, with a single `as f32`
//! narrowing per element (both round to nearest, ties to even). Control
//! signals are decoded from `float32` values and widened back to `f64`, which
//! is what `float(np.float32(...))` does in the reference.
//!
//! Two Python-specific behaviours are preserved deliberately:
//!
//! * the timestamp reduction uses Python's `%` semantics (result carries the
//!   sign of the divisor), reproduced with [`f64::rem_euclid`];
//! * `np.clip` propagates NaN, so the control-signal clamps here propagate NaN
//!   rather than collapsing it to a bound.

use serde::{Deserialize, Serialize};

use crate::error::DaemonError;

/// Fixed dimensionality of the flattened state vector fed to the controller.
///
/// PRINet 3.0 `prinet.core.subconscious.STATE_DIM`.
pub const STATE_DIM: usize = 32;

/// Fixed dimensionality of the control-signal output tensor.
///
/// PRINet 3.0 `prinet.core.subconscious.CONTROL_DIM`.
pub const CONTROL_DIM: usize = 8;

/// Number of leading elements of the state vector that carry data; the
/// remaining `STATE_DIM - STATE_PAYLOAD` elements are zero padding.
pub const STATE_PAYLOAD: usize = 19;

/// Divisor applied to `gpu_temp` before packing (PRINet 3.0 `gpu_temp / 100.0`).
pub const GPU_TEMP_SCALE: f64 = 100.0;

/// Divisor applied to `throughput` before packing (PRINet 3.0 `/ 1e4`).
pub const THROUGHPUT_SCALE: f64 = 1e4;

/// Divisor applied to `epoch` before packing (PRINet 3.0 `/ 1e4`).
pub const EPOCH_SCALE: f64 = 1e4;

/// Divisor applied to the regime index before packing (PRINet 3.0 `/ 2.0`).
pub const REGIME_SCALE: f64 = 2.0;

/// Seconds per day, used to reduce `timestamp` to a fraction of a day
/// (PRINet 3.0 `(timestamp % 86400.0) / 86400.0`).
pub const SECONDS_PER_DAY: f64 = 86_400.0;

/// Lower clamp on the decoded learning-rate multiplier
/// (PRINet 3.0 `np.clip(flat[2], 0.1, 10.0)`).
pub const LR_MULTIPLIER_MIN: f64 = 0.1;

/// Upper clamp on the decoded learning-rate multiplier
/// (PRINet 3.0 `np.clip(flat[2], 0.1, 10.0)`).
pub const LR_MULTIPLIER_MAX: f64 = 10.0;

/// Lower clamp on the decoded alert level
/// (PRINet 3.0 `np.clip(flat[6], 0.0, 1.0)`).
pub const ALERT_LEVEL_MIN: f64 = 0.0;

/// Upper clamp on the decoded alert level
/// (PRINet 3.0 `np.clip(flat[6], 0.0, 1.0)`).
pub const ALERT_LEVEL_MAX: f64 = 1.0;

/// Active coupling regime reported by the training loop.
///
/// PRINet 3.0 encodes this as a bare string keyed through `_REGIME_MAP`;
/// PRIN uses a closed enum (Coding Standards §2.2, "enums for closed sets")
/// and confines the string handling to [`Regime::from_name`] /
/// [`Regime::from_name_or_default`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Regime {
    /// Mean-field coupling (`"mean_field"`, index 0).
    #[default]
    MeanField,
    /// Sparse k-NN coupling (`"sparse_knn"`, index 1).
    SparseKnn,
    /// All-to-all coupling (`"full"`, index 2).
    Full,
}

impl Regime {
    /// The regime's integer index in the packed state vector.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::state::Regime;
    ///
    /// assert_eq!(Regime::MeanField.index(), 0);
    /// assert_eq!(Regime::SparseKnn.index(), 1);
    /// assert_eq!(Regime::Full.index(), 2);
    /// ```
    #[must_use]
    pub fn index(self) -> u8 {
        match self {
            Regime::MeanField => 0,
            Regime::SparseKnn => 1,
            Regime::Full => 2,
        }
    }

    /// The regime's PRINet 3.0 name.
    #[must_use]
    pub fn name(self) -> &'static str {
        match self {
            Regime::MeanField => "mean_field",
            Regime::SparseKnn => "sparse_knn",
            Regime::Full => "full",
        }
    }

    /// Parse a PRINet 3.0 regime name.
    ///
    /// Returns `None` for any name outside `_REGIME_MAP`.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::state::Regime;
    ///
    /// assert_eq!(Regime::from_name("sparse_knn"), Some(Regime::SparseKnn));
    /// assert_eq!(Regime::from_name("chimera"), None);
    /// ```
    #[must_use]
    pub fn from_name(name: &str) -> Option<Self> {
        match name {
            "mean_field" => Some(Regime::MeanField),
            "sparse_knn" => Some(Regime::SparseKnn),
            "full" => Some(Regime::Full),
            _ => None,
        }
    }

    /// Parse a regime name, falling back to [`Regime::MeanField`].
    ///
    /// This reproduces PRINet 3.0's `_REGIME_MAP.get(self.regime, 0)`, which
    /// silently encodes an unrecognised regime name as index 0.
    #[must_use]
    pub fn from_name_or_default(name: &str) -> Self {
        Regime::from_name(name).unwrap_or_default()
    }
}

/// Compressed system snapshot handed to the subconscious controller.
///
/// Field order and normalisation match PRINet 3.0
/// `prinet.core.subconscious.SubconsciousState` exactly; see
/// [`SubconsciousState::to_tensor`] for the packed layout.
///
/// # Examples
///
/// ```
/// use prin_daemon::state::{Regime, SubconsciousState, STATE_DIM};
///
/// let state = SubconsciousState {
///     r_global: 0.5,
///     regime: Regime::SparseKnn,
///     ..SubconsciousState::default()
/// };
/// let vector = state.to_tensor()?;
/// assert_eq!(vector.len(), STATE_DIM);
/// assert_eq!(vector[3], 0.5_f32);
/// assert_eq!(vector[17], 0.5_f32); // regime index 1 / 2.0
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubconsciousState {
    /// Per-band Kuramoto order parameters `[r_δ, r_θ, r_γ]`.
    ///
    /// Shorter vectors are zero-filled and longer vectors truncated when
    /// packing, matching the reference implementation.
    pub r_per_band: Vec<f64>,
    /// Global (all-band) order parameter.
    pub r_global: f64,
    /// Exponential moving average of the training loss.
    pub loss_ema: f64,
    /// Variance of the training loss over the recent window.
    pub loss_variance: f64,
    /// EMA of the gradient L2 norm.
    pub grad_norm_ema: f64,
    /// Current learning rate.
    pub lr_current: f64,
    /// Current SCALR coupling-strength modifier.
    pub scalr_alpha: f64,
    /// GPU temperature in degrees Celsius.
    pub gpu_temp: f64,
    /// GPU utilisation fraction in `[0, 1]`.
    pub gpu_util: f64,
    /// GPU VRAM utilisation fraction in `[0, 1]`.
    pub vram_pct: f64,
    /// CPU utilisation fraction in `[0, 1]`.
    pub cpu_util: f64,
    /// Median step latency in seconds.
    pub step_latency_p50: f64,
    /// 95th-percentile step latency in seconds.
    pub step_latency_p95: f64,
    /// Training throughput in samples per second.
    pub throughput: f64,
    /// Current epoch index.
    pub epoch: i64,
    /// Active coupling regime.
    pub regime: Regime,
    /// Unix timestamp of the snapshot, in seconds.
    pub timestamp: f64,
}

impl Default for SubconsciousState {
    /// PRINet 3.0's dataclass field defaults.
    ///
    /// The reference `SubconsciousState.default()` additionally stamps
    /// `time.time()` into `timestamp`; PRIN keeps the Rust core free of hidden
    /// clock reads, so wall-clock stamping is the caller's responsibility.
    fn default() -> Self {
        Self {
            r_per_band: vec![0.0, 0.0, 0.0],
            r_global: 0.0,
            loss_ema: 0.0,
            loss_variance: 0.0,
            grad_norm_ema: 0.0,
            lr_current: 1e-3,
            scalr_alpha: 1.0,
            gpu_temp: 0.0,
            gpu_util: 0.0,
            vram_pct: 0.0,
            cpu_util: 0.0,
            step_latency_p50: 0.0,
            step_latency_p95: 0.0,
            throughput: 0.0,
            epoch: 0,
            regime: Regime::MeanField,
            timestamp: 0.0,
        }
    }
}

impl SubconsciousState {
    /// Per-band order parameter at `index`, or `0.0` when absent.
    #[must_use]
    pub fn band(&self, index: usize) -> f64 {
        self.r_per_band.get(index).copied().unwrap_or(0.0)
    }

    /// Timestamp reduced to a fraction of a day in `[0, 1)`.
    ///
    /// Uses Euclidean remainder so that negative timestamps behave as Python's
    /// `%` operator does (`-1.0 % 86400.0 == 86399.0`).
    #[must_use]
    pub fn timestamp_fraction(&self) -> f64 {
        self.timestamp.rem_euclid(SECONDS_PER_DAY) / SECONDS_PER_DAY
    }

    /// Pack this snapshot into the fixed-size controller input vector.
    ///
    /// Layout (32 `f32` elements, PRINet 3.0
    /// `SubconsciousState.to_tensor`):
    ///
    /// | Index | Value |
    /// |---|---|
    /// | 0–2 | `r_per_band[0..3]` (zero-filled when shorter) |
    /// | 3 | `r_global` |
    /// | 4–8 | `loss_ema`, `loss_variance`, `grad_norm_ema`, `lr_current`, `scalr_alpha` |
    /// | 9–12 | `gpu_temp / 100`, `gpu_util`, `vram_pct`, `cpu_util` |
    /// | 13–15 | `step_latency_p50`, `step_latency_p95`, `throughput / 1e4` |
    /// | 16–18 | `epoch / 1e4`, `regime_index / 2`, `timestamp_fraction` |
    /// | 19–31 | zero padding |
    ///
    /// # Errors
    ///
    /// With the `strict-checks` feature enabled, returns
    /// [`DaemonError::NonFiniteValue`] when any contributing field is NaN or
    /// infinite. Without it — matching PRINet 3.0 — non-finite values are
    /// packed unchanged and this call cannot fail.
    pub fn to_tensor(&self) -> Result<[f32; STATE_DIM], DaemonError> {
        let payload = [
            ("r_per_band[0]", self.band(0)),
            ("r_per_band[1]", self.band(1)),
            ("r_per_band[2]", self.band(2)),
            ("r_global", self.r_global),
            ("loss_ema", self.loss_ema),
            ("loss_variance", self.loss_variance),
            ("grad_norm_ema", self.grad_norm_ema),
            ("lr_current", self.lr_current),
            ("scalr_alpha", self.scalr_alpha),
            ("gpu_temp", self.gpu_temp / GPU_TEMP_SCALE),
            ("gpu_util", self.gpu_util),
            ("vram_pct", self.vram_pct),
            ("cpu_util", self.cpu_util),
            ("step_latency_p50", self.step_latency_p50),
            ("step_latency_p95", self.step_latency_p95),
            ("throughput", self.throughput / THROUGHPUT_SCALE),
            ("epoch", self.epoch as f64 / EPOCH_SCALE),
            ("regime", f64::from(self.regime.index()) / REGIME_SCALE),
            ("timestamp", self.timestamp_fraction()),
        ];

        let mut packed = [0.0_f32; STATE_DIM];
        for (slot, (name, value)) in packed.iter_mut().zip(payload) {
            *slot = guard_finite(value, name)? as f32;
        }
        Ok(packed)
    }
}

/// Control suggestions produced by the subconscious controller.
///
/// Rebuild of PRINet 3.0 `prinet.core.subconscious.ControlSignals`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ControlSignals {
    /// Lower bound suggested for the coupling strength `K`.
    pub suggested_k_min: f64,
    /// Upper bound suggested for the coupling strength `K`.
    pub suggested_k_max: f64,
    /// Multiplicative learning-rate adjustment, centred at `1.0`.
    pub lr_multiplier: f64,
    /// Preference weight for the mean-field regime.
    pub regime_mf_weight: f64,
    /// Preference weight for the sparse k-NN regime.
    pub regime_sk_weight: f64,
    /// Preference weight for the full-coupling regime.
    pub regime_full_weight: f64,
    /// Alert level in `[0, 1]`; `0` is nominal, `1` requests intervention.
    pub alert_level: f64,
    /// Suggested coupling-mode index, as a raw logit.
    pub coupling_mode_suggestion: f64,
}

impl Default for ControlSignals {
    /// PRINet 3.0's no-op defaults: `K ∈ [0.5, 5.0]`, unit LR multiplier, and
    /// a near-uniform regime preference.
    fn default() -> Self {
        Self {
            suggested_k_min: 0.5,
            suggested_k_max: 5.0,
            lr_multiplier: 1.0,
            regime_mf_weight: 0.33,
            regime_sk_weight: 0.33,
            regime_full_weight: 0.34,
            alert_level: 0.0,
            coupling_mode_suggestion: 0.0,
        }
    }
}

impl ControlSignals {
    /// Decode control signals from a controller output tensor.
    ///
    /// `values` is the flattened `float32` model output; only the first
    /// [`CONTROL_DIM`] elements are read, matching PRINet 3.0's `ravel()`
    /// plus positional unpacking. The learning-rate multiplier is clamped to
    /// `[0.1, 10.0]` and the alert level to `[0, 1]`; as in NumPy, a NaN
    /// input propagates through the clamp rather than snapping to a bound.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::ControlTooShort`] when fewer than
    /// [`CONTROL_DIM`] elements are supplied.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::state::ControlSignals;
    ///
    /// let raw = [0.5_f32, 5.0, 42.0, 0.2, 0.3, 0.5, 2.0, -1.0];
    /// let ctrl = ControlSignals::from_tensor(&raw)?;
    /// assert_eq!(ctrl.lr_multiplier, 10.0); // clamped
    /// assert_eq!(ctrl.alert_level, 1.0); // clamped
    /// assert_eq!(ctrl.coupling_mode_suggestion, -1.0); // raw logit
    /// # Ok::<(), prin_daemon::DaemonError>(())
    /// ```
    pub fn from_tensor(values: &[f32]) -> Result<Self, DaemonError> {
        let flat: &[f32] = values
            .get(..CONTROL_DIM)
            .ok_or(DaemonError::ControlTooShort {
                expected: CONTROL_DIM,
                got: values.len(),
            })?;
        Ok(Self {
            suggested_k_min: f64::from(flat[0]),
            suggested_k_max: f64::from(flat[1]),
            lr_multiplier: f64::from(clip(
                flat[2],
                LR_MULTIPLIER_MIN as f32,
                LR_MULTIPLIER_MAX as f32,
            )),
            regime_mf_weight: f64::from(flat[3]),
            regime_sk_weight: f64::from(flat[4]),
            regime_full_weight: f64::from(flat[5]),
            alert_level: f64::from(clip(
                flat[6],
                ALERT_LEVEL_MIN as f32,
                ALERT_LEVEL_MAX as f32,
            )),
            coupling_mode_suggestion: f64::from(flat[7]),
        })
    }

    /// Decode control signals from `f64` values.
    ///
    /// Each element is first narrowed to `f32`, reproducing PRINet 3.0's
    /// `np.asarray(arr, dtype=np.float32)` cast before unpacking.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::ControlTooShort`] when fewer than
    /// [`CONTROL_DIM`] elements are supplied.
    pub fn from_tensor_f64(values: &[f64]) -> Result<Self, DaemonError> {
        let narrowed: Vec<f32> = values.iter().map(|v| *v as f32).collect();
        Self::from_tensor(&narrowed)
    }

    /// Pack these control signals back into a `float32` tensor.
    ///
    /// Element order matches [`ControlSignals::from_tensor`].
    #[must_use]
    pub fn to_tensor(&self) -> [f32; CONTROL_DIM] {
        [
            self.suggested_k_min as f32,
            self.suggested_k_max as f32,
            self.lr_multiplier as f32,
            self.regime_mf_weight as f32,
            self.regime_sk_weight as f32,
            self.regime_full_weight as f32,
            self.alert_level as f32,
            self.coupling_mode_suggestion as f32,
        ]
    }

    /// The regime with the highest preference weight.
    ///
    /// Ties resolve to the earliest regime in mean-field → sparse-k-NN → full
    /// order, matching PRINet 3.0's `max(weights, key=weights.get)` over an
    /// insertion-ordered dict. A NaN weight never wins, because every
    /// comparison against NaN is false.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::state::{ControlSignals, Regime};
    ///
    /// let ctrl = ControlSignals {
    ///     regime_mf_weight: 0.2,
    ///     regime_sk_weight: 0.5,
    ///     regime_full_weight: 0.3,
    ///     ..ControlSignals::default()
    /// };
    /// assert_eq!(ctrl.preferred_regime(), Regime::SparseKnn);
    /// ```
    #[must_use]
    pub fn preferred_regime(&self) -> Regime {
        let mut best = Regime::MeanField;
        let mut best_weight = self.regime_mf_weight;
        if self.regime_sk_weight > best_weight {
            best = Regime::SparseKnn;
            best_weight = self.regime_sk_weight;
        }
        if self.regime_full_weight > best_weight {
            best = Regime::Full;
        }
        best
    }

    /// Whether every control signal is finite (no NaN, no infinity).
    #[must_use]
    pub fn is_finite(&self) -> bool {
        self.to_tensor().iter().all(|v| v.is_finite())
    }
}

/// NumPy-compatible clamp, evaluated in `f32`.
///
/// Two reference behaviours are reproduced here. Bounds are applied by
/// comparison, so a NaN input survives the clamp instead of snapping to a
/// bound; and the comparison happens in binary32, because NumPy treats the
/// Python `float` bounds of `np.clip(flat[2], 0.1, 10.0)` as weak scalars
/// (NEP 50) and keeps the float32 operand's dtype. Clamping `0.1` in `f64`
/// and widening afterwards would yield `0.1`, whereas the reference yields
/// `float(np.float32(0.1)) == 0.10000000149011612`.
fn clip(value: f32, lo: f32, hi: f32) -> f32 {
    if value < lo {
        lo
    } else if value > hi {
        hi
    } else {
        value
    }
}

#[cfg(feature = "strict-checks")]
fn guard_finite(value: f64, name: &'static str) -> Result<f64, DaemonError> {
    if value.is_finite() {
        Ok(value)
    } else {
        Err(DaemonError::NonFiniteValue { name, value })
    }
}

#[cfg(not(feature = "strict-checks"))]
fn guard_finite(value: f64, _name: &'static str) -> Result<f64, DaemonError> {
    Ok(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn state_default_matches_reference_dataclass_defaults() {
        let state = SubconsciousState::default();
        assert_eq!(state.r_per_band, vec![0.0, 0.0, 0.0]);
        assert_eq!(state.lr_current, 1e-3);
        assert_eq!(state.scalr_alpha, 1.0);
        assert_eq!(state.epoch, 0);
        assert_eq!(state.regime, Regime::MeanField);
        assert_eq!(state.timestamp, 0.0);
    }

    #[test]
    fn default_state_packs_to_expected_vector() {
        let packed = SubconsciousState::default().to_tensor().expect("packs");
        assert_eq!(packed.len(), STATE_DIM);
        assert_eq!(packed[7], 1e-3_f32); // lr_current
        assert_eq!(packed[8], 1.0_f32); // scalr_alpha
        for (index, value) in packed.iter().enumerate() {
            if index != 7 && index != 8 {
                assert_eq!(*value, 0.0_f32, "index {index}");
            }
        }
    }

    #[test]
    fn payload_normalisation_matches_reference_scales() {
        let state = SubconsciousState {
            r_per_band: vec![0.1, 0.2, 0.3],
            r_global: 0.4,
            loss_ema: 1.5,
            loss_variance: 0.25,
            grad_norm_ema: 3.5,
            lr_current: 2e-4,
            scalr_alpha: 1.25,
            gpu_temp: 70.0,
            gpu_util: 0.9,
            vram_pct: 0.75,
            cpu_util: 0.5,
            step_latency_p50: 0.011,
            step_latency_p95: 0.023,
            throughput: 12_500.0,
            epoch: 250,
            regime: Regime::Full,
            timestamp: 86_400.0 + 43_200.0,
        };
        let packed = state.to_tensor().expect("packs");
        assert_eq!(packed[9], 0.7_f32); // 70 / 100
        assert_eq!(packed[15], 1.25_f32); // 12500 / 1e4
        assert_eq!(packed[16], 0.025_f32); // 250 / 1e4
        assert_eq!(packed[17], 1.0_f32); // regime index 2 / 2
        assert_eq!(packed[18], 0.5_f32); // midday
    }

    #[test]
    fn short_and_long_band_vectors_are_tolerated() {
        let short = SubconsciousState {
            r_per_band: vec![0.25],
            ..SubconsciousState::default()
        };
        let packed = short.to_tensor().expect("packs");
        assert_eq!(packed[0], 0.25_f32);
        assert_eq!(packed[1], 0.0_f32);
        assert_eq!(packed[2], 0.0_f32);

        let long = SubconsciousState {
            r_per_band: vec![0.1, 0.2, 0.3, 0.4],
            ..SubconsciousState::default()
        };
        let packed = long.to_tensor().expect("packs");
        assert_eq!(packed[2], 0.3_f32);
        assert_eq!(packed[3], 0.0_f32); // r_global, not the fourth band
    }

    #[test]
    fn padding_region_is_always_zero() {
        let state = SubconsciousState {
            r_per_band: vec![1.0, 1.0, 1.0],
            r_global: 1.0,
            throughput: 1e6,
            epoch: 9_999,
            ..SubconsciousState::default()
        };
        let packed = state.to_tensor().expect("packs");
        assert!(packed[STATE_PAYLOAD..].iter().all(|v| *v == 0.0));
    }

    #[test]
    fn negative_timestamp_uses_python_modulo_semantics() {
        let state = SubconsciousState {
            timestamp: -1.0,
            ..SubconsciousState::default()
        };
        assert!((state.timestamp_fraction() - 86_399.0 / 86_400.0).abs() < 1e-15);
    }

    #[test]
    fn timestamp_fraction_is_always_in_unit_interval() {
        for ts in [-1e9, -86_400.0, 0.0, 1.0, 86_399.999, 1.7e9] {
            let state = SubconsciousState {
                timestamp: ts,
                ..SubconsciousState::default()
            };
            let frac = state.timestamp_fraction();
            assert!((0.0..1.0).contains(&frac), "timestamp {ts} gave {frac}");
        }
    }

    #[test]
    fn regime_names_and_indices_round_trip() {
        for regime in [Regime::MeanField, Regime::SparseKnn, Regime::Full] {
            assert_eq!(Regime::from_name(regime.name()), Some(regime));
        }
        assert_eq!(Regime::from_name_or_default("nonsense"), Regime::MeanField);
        assert_eq!(Regime::default(), Regime::MeanField);
    }

    #[cfg(not(feature = "strict-checks"))]
    #[test]
    fn non_finite_fields_pass_through_without_strict_checks() {
        let state = SubconsciousState {
            r_global: f64::NAN,
            loss_ema: f64::INFINITY,
            ..SubconsciousState::default()
        };
        let packed = state.to_tensor().expect("packs");
        assert!(packed[3].is_nan());
        assert!(packed[4].is_infinite());
    }

    #[cfg(feature = "strict-checks")]
    #[test]
    fn non_finite_fields_are_rejected_under_strict_checks() {
        let state = SubconsciousState {
            r_global: f64::NAN,
            ..SubconsciousState::default()
        };
        let err = state.to_tensor().expect_err("strict rejects NaN");
        assert!(matches!(
            err,
            DaemonError::NonFiniteValue {
                name: "r_global",
                ..
            }
        ));
    }

    #[test]
    fn control_defaults_match_reference() {
        let ctrl = ControlSignals::default();
        assert_eq!(ctrl.suggested_k_min, 0.5);
        assert_eq!(ctrl.suggested_k_max, 5.0);
        assert_eq!(ctrl.lr_multiplier, 1.0);
        assert_eq!(ctrl.regime_full_weight, 0.34);
        assert!(ctrl.is_finite());
    }

    #[test]
    fn control_from_tensor_requires_full_width() {
        let err = ControlSignals::from_tensor(&[0.0; CONTROL_DIM - 1]).expect_err("too short");
        assert!(matches!(
            err,
            DaemonError::ControlTooShort {
                expected: CONTROL_DIM,
                got: 7
            }
        ));
    }

    #[test]
    fn control_from_tensor_ignores_trailing_elements() {
        let mut raw = [0.0_f32; CONTROL_DIM + 4];
        raw[0] = 1.5;
        let ctrl = ControlSignals::from_tensor(&raw).expect("decodes");
        assert_eq!(ctrl.suggested_k_min, 1.5);
    }

    #[test]
    fn control_clamps_match_numpy_clip_including_nan() {
        let mut raw = [0.0_f32; CONTROL_DIM];
        raw[2] = -5.0;
        raw[6] = -0.5;
        let low = ControlSignals::from_tensor(&raw).expect("decodes");
        // The lower LR bound is clamped in binary32, as NumPy does.
        assert_eq!(low.lr_multiplier, f64::from(LR_MULTIPLIER_MIN as f32));
        assert_ne!(low.lr_multiplier, LR_MULTIPLIER_MIN);
        assert_eq!(low.alert_level, ALERT_LEVEL_MIN);

        raw[2] = f32::NAN;
        raw[6] = f32::NAN;
        let nan = ControlSignals::from_tensor(&raw).expect("decodes");
        assert!(nan.lr_multiplier.is_nan());
        assert!(nan.alert_level.is_nan());
        assert!(!nan.is_finite());
    }

    #[test]
    fn control_from_f64_narrows_before_decoding() {
        // 0.1 is not representable in binary32; the reference casts first.
        let ctrl = ControlSignals::from_tensor_f64(&[0.1, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            .expect("decodes");
        assert_eq!(ctrl.suggested_k_min, f64::from(0.1_f32));
        assert_ne!(ctrl.suggested_k_min, 0.1_f64);
    }

    #[test]
    fn control_tensor_round_trips_within_f32_precision() {
        let ctrl = ControlSignals {
            suggested_k_min: 0.75,
            suggested_k_max: 4.25,
            lr_multiplier: 1.5,
            regime_mf_weight: 0.125,
            regime_sk_weight: 0.375,
            regime_full_weight: 0.5,
            alert_level: 0.25,
            coupling_mode_suggestion: -2.0,
        };
        let decoded = ControlSignals::from_tensor(&ctrl.to_tensor()).expect("decodes");
        assert_eq!(decoded, ctrl);
    }

    #[test]
    fn preferred_regime_resolves_ties_to_the_earliest_regime() {
        let uniform = ControlSignals {
            regime_mf_weight: 0.5,
            regime_sk_weight: 0.5,
            regime_full_weight: 0.5,
            ..ControlSignals::default()
        };
        assert_eq!(uniform.preferred_regime(), Regime::MeanField);

        let full = ControlSignals {
            regime_mf_weight: 0.1,
            regime_sk_weight: 0.2,
            regime_full_weight: 0.7,
            ..ControlSignals::default()
        };
        assert_eq!(full.preferred_regime(), Regime::Full);
    }

    #[test]
    fn preferred_regime_ignores_nan_weights() {
        let ctrl = ControlSignals {
            regime_mf_weight: 0.4,
            regime_sk_weight: f64::NAN,
            regime_full_weight: 0.1,
            ..ControlSignals::default()
        };
        assert_eq!(ctrl.preferred_regime(), Regime::MeanField);
    }

    #[test]
    fn clip_leaves_interior_values_untouched() {
        assert_eq!(clip(0.5_f32, 0.0, 1.0), 0.5);
        assert_eq!(clip(2.0_f32, 0.0, 1.0), 1.0);
        assert_eq!(clip(-2.0_f32, 0.0, 1.0), 0.0);
        assert!(clip(f32::NAN, 0.0, 1.0).is_nan());
    }
}

//! Statistical utilities for rigorous multi-seed benchmarking (WP-031): a
//! direct port of PRINet 3.0's `bootstrap_ci`/`cohens_d`/`welch_t_test`/
//! `compute_p_value` (`utils/y4q1_tools.py:474-490,743-840`).
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! [`cohens_d`] and the Welch t-statistic/degrees-of-freedom formula in
//! [`welch_t_test`] are closed-form and ported exactly. The reference's
//! p-value comes from `scipy.stats.ttest_ind(..., equal_var=False)`; this
//! port computes the identical two-tailed Student's-t p-value directly via
//! the regularized incomplete beta function (`student_t_two_tailed_p_value`,
//! the standard `1 - CDF(|t|)` relation used by every Student's-t
//! implementation, including scipy's own C implementation), rather than
//! depend on an external stats crate — see
//! `tools/wp031_stats_fixture.py`/`tests/parity_stats.rs` for byte-level
//! validation against real `scipy.stats.ttest_ind` output.
//!
//! [`bootstrap_ci`]'s *formula* (percentile-method bootstrap) is a direct
//! port of `bootstrap_ci` (`y4q1_tools.py:743-781`); its *resampling stream*
//! draws from this project's counter-based [`Seed`] rather than
//! `numpy.random.RandomState`, the same "structural, not bit-parity" port
//! class as [`crate::dataset::generate_temporal_clevr_n`] (see that module's
//! docs for the full rationale) — RNG-stream parity with `numpy` is
//! architecturally out of scope, but the percentile-method formula itself is
//! pinned by this module's hand-computed tests.

use prin_dynamics::Seed;

use crate::error::TrainError;

/// Result of [`bootstrap_ci`]: a percentile-method bootstrap confidence
/// interval for the mean of a sample.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BootstrapCi {
    /// Sample mean of the original (non-resampled) values.
    pub mean: f64,
    /// Lower bound of the `(1 - alpha)` confidence interval.
    pub ci_lower: f64,
    /// Upper bound of the `(1 - alpha)` confidence interval.
    pub ci_upper: f64,
    /// `ci_upper - ci_lower`.
    pub ci_width: f64,
    /// Standard error: the standard deviation of the bootstrap resample
    /// means.
    pub se: f64,
}

/// Result of [`welch_t_test`]: Welch's unequal-variances two-sample t-test.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct WelchTTest {
    /// Welch t-statistic.
    pub t_stat: f64,
    /// Two-tailed p-value.
    pub p_value: f64,
    /// Cohen's d effect size (see [`cohens_d`]).
    pub cohens_d: f64,
    /// `mean(group_a) - mean(group_b)`.
    pub mean_diff: f64,
}

/// Compute a percentile-method bootstrap confidence interval for the mean of
/// `values`.
///
/// Direct port of `bootstrap_ci` (`y4q1_tools.py:743-781`) — see module docs
/// for the RNG-stream caveat (the percentile-method *formula* is exact; the
/// resample draws come from [`Seed`], not `numpy.random.RandomState`).
///
/// # Errors
///
/// Returns [`TrainError::InsufficientSamples`] if `values` is empty,
/// [`TrainError::InvalidBootstrapCount`] if `n_bootstrap` is zero, or
/// [`TrainError::InvalidSignificanceLevel`] if `alpha` is not finite and in
/// `(0, 1)`.
pub fn bootstrap_ci(
    values: &[f64],
    n_bootstrap: usize,
    alpha: f64,
    seed: &mut Seed,
) -> Result<BootstrapCi, TrainError> {
    if values.is_empty() {
        return Err(TrainError::InsufficientSamples {
            name: "values",
            min: 1,
            got: 0,
        });
    }
    if n_bootstrap == 0 {
        return Err(TrainError::InvalidBootstrapCount { value: n_bootstrap });
    }
    if !(alpha.is_finite() && 0.0 < alpha && alpha < 1.0) {
        return Err(TrainError::InvalidSignificanceLevel { value: alpha });
    }

    let n = values.len();
    let mut means = Vec::with_capacity(n_bootstrap);
    for _ in 0..n_bootstrap {
        let mut sum = 0.0;
        for _ in 0..n {
            let idx = if n == 1 {
                0
            } else {
                (seed.next_f64_range(0.0, n as f64).unwrap_or(0.0) as usize).min(n - 1)
            };
            sum += values[idx];
        }
        means.push(sum / n as f64);
    }

    let mean = values.iter().sum::<f64>() / n as f64;
    let lo = percentile(&means, 100.0 * alpha / 2.0);
    let hi = percentile(&means, 100.0 * (1.0 - alpha / 2.0));
    let se = std_dev(&means, 0);

    Ok(BootstrapCi {
        mean,
        ci_lower: lo,
        ci_upper: hi,
        ci_width: hi - lo,
        se,
    })
}

/// Linear-interpolation percentile, matching `numpy.percentile`'s default
/// (`interpolation="linear"`) method used by the reference's
/// `np.percentile(means, ...)` calls.
fn percentile(values: &[f64], pct: f64) -> f64 {
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).expect("bootstrap means are finite"));
    let n = sorted.len();
    if n == 1 {
        return sorted[0];
    }
    let rank = (pct / 100.0) * (n - 1) as f64;
    let lo = rank.floor() as usize;
    let hi = rank.ceil() as usize;
    if lo == hi {
        sorted[lo]
    } else {
        let frac = rank - lo as f64;
        sorted[lo] * (1.0 - frac) + sorted[hi] * frac
    }
}

/// Population (`ddof`-adjustable) standard deviation, matching
/// `numpy.ndarray.std(ddof=...)`.
fn std_dev(values: &[f64], ddof: usize) -> f64 {
    let n = values.len();
    if n <= ddof {
        return 0.0;
    }
    let mean = values.iter().sum::<f64>() / n as f64;
    let var = values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / (n - ddof) as f64;
    var.sqrt()
}

/// Cohen's d effect size (pooled standard deviation):
///
/// ```text
/// d = (mean(A) - mean(B)) / s_p,   s_p = sqrt(((n_A-1)*var_A + (n_B-1)*var_B) / (n_A+n_B-2))
/// ```
///
/// Direct port of `cohens_d` (`y4q1_tools.py:784-812`). Returns `0.0` if
/// either group has fewer than 2 samples or the pooled standard deviation is
/// below `1e-12` (matching the reference's own degenerate-input guards
/// exactly, rather than a typed error — this is a deliberate reference
/// convention this port preserves for drop-in behavioral parity, since
/// `cohens_d` is also called internally by [`welch_t_test`] on the same
/// already-validated inputs).
pub fn cohens_d(group_a: &[f64], group_b: &[f64]) -> f64 {
    let (n_a, n_b) = (group_a.len(), group_b.len());
    if n_a < 2 || n_b < 2 {
        return 0.0;
    }
    let var_a = variance(group_a, 1);
    let var_b = variance(group_b, 1);
    let pooled =
        (((n_a - 1) as f64 * var_a + (n_b - 1) as f64 * var_b) / (n_a + n_b - 2) as f64).sqrt();
    if pooled < 1e-12 {
        return 0.0;
    }
    (mean(group_a) - mean(group_b)) / pooled
}

fn mean(values: &[f64]) -> f64 {
    values.iter().sum::<f64>() / values.len() as f64
}

/// Sample (`ddof`-adjustable) variance, matching `numpy.ndarray.var(ddof=...)`.
fn variance(values: &[f64], ddof: usize) -> f64 {
    let n = values.len();
    let m = mean(values);
    values.iter().map(|v| (v - m).powi(2)).sum::<f64>() / (n - ddof) as f64
}

/// Welch's two-sample t-test (unequal variances), with Cohen's d effect
/// size.
///
/// Direct port of `welch_t_test` (`y4q1_tools.py:815-840`); also implements
/// [`compute_p_value`]'s `scipy.stats.ttest_ind(..., equal_var=False).pvalue`
/// call (`y4q1_tools.py:474-490`) exactly, since both wrap the identical
/// scipy call — see module docs for the p-value derivation.
///
/// # Errors
///
/// Returns [`TrainError::InsufficientSamples`] if either group has fewer
/// than 2 observations (Welch's degrees-of-freedom formula requires
/// `n - 1 >= 1` per group).
pub fn welch_t_test(group_a: &[f64], group_b: &[f64]) -> Result<WelchTTest, TrainError> {
    let (n_a, n_b) = (group_a.len(), group_b.len());
    if n_a < 2 {
        return Err(TrainError::InsufficientSamples {
            name: "group_a",
            min: 2,
            got: n_a,
        });
    }
    if n_b < 2 {
        return Err(TrainError::InsufficientSamples {
            name: "group_b",
            min: 2,
            got: n_b,
        });
    }

    let (mean_a, mean_b) = (mean(group_a), mean(group_b));
    let (var_a, var_b) = (variance(group_a, 1), variance(group_b, 1));
    let (na, nb) = (n_a as f64, n_b as f64);
    let a_term = var_a / na;
    let b_term = var_b / nb;
    let se = (a_term + b_term).sqrt();

    let t_stat = if se > 0.0 {
        (mean_a - mean_b) / se
    } else {
        0.0
    };
    let df = if a_term > 0.0 || b_term > 0.0 {
        (a_term + b_term).powi(2) / (a_term.powi(2) / (na - 1.0) + b_term.powi(2) / (nb - 1.0))
    } else {
        na + nb - 2.0
    };
    let p_value = student_t_two_tailed_p_value(t_stat, df);

    Ok(WelchTTest {
        t_stat,
        p_value,
        cohens_d: cohens_d(group_a, group_b),
        mean_diff: mean_a - mean_b,
    })
}

/// Compute a two-sample Welch's t-test two-tailed p-value only.
///
/// Direct port of `compute_p_value` (`y4q1_tools.py:474-490`), a thinner
/// reference-duplicate of [`welch_t_test`] retained here purely as a
/// same-shape convenience wrapper (matching the reference API surface) —
/// see [`welch_t_test`] for the full statistic.
///
/// # Errors
///
/// See [`welch_t_test`].
pub fn compute_p_value(accs_a: &[f64], accs_b: &[f64]) -> Result<f64, TrainError> {
    welch_t_test(accs_a, accs_b).map(|r| r.p_value)
}

/// Two-tailed Student's-t p-value for a t-statistic with `df` degrees of
/// freedom: `P(|T| >= |t_stat|)`, computed via the regularized incomplete
/// beta function relation `p = I_x(df/2, 1/2)`, `x = df / (df + t_stat^2)` —
/// the standard closed-form Student's-t survival function (the same relation
/// scipy's own C implementation of `stdtr` uses internally).
fn student_t_two_tailed_p_value(t_stat: f64, df: f64) -> f64 {
    if !t_stat.is_finite() || !df.is_finite() || df <= 0.0 {
        return f64::NAN;
    }
    let x = df / (df + t_stat * t_stat);
    regularized_incomplete_beta(df / 2.0, 0.5, x).clamp(0.0, 1.0)
}

/// Log of the gamma function via the Lanczos approximation (g=7, 9-term
/// coefficients), accurate to double precision — a standard, widely-used
/// numerical algorithm (Numerical Recipes §6.1) with no external dependency.
fn log_gamma(x: f64) -> f64 {
    const COEF: [f64; 9] = [
        0.999_999_999_999_809_9,
        676.520_368_121_885_1,
        -1_259.139_216_722_402_8,
        771.323_428_777_653_1,
        -176.615_029_162_140_6,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_312e-7,
    ];
    if x < 0.5 {
        // Reflection formula: Gamma(x) * Gamma(1-x) = pi / sin(pi*x).
        (std::f64::consts::PI / (std::f64::consts::PI * x).sin()).ln() - log_gamma(1.0 - x)
    } else {
        let x = x - 1.0;
        let g = 7.0;
        let mut a = COEF[0];
        let t = x + g + 0.5;
        for (i, &c) in COEF.iter().enumerate().skip(1) {
            a += c / (x + i as f64);
        }
        0.5 * (2.0 * std::f64::consts::PI).ln() + (x + 0.5) * t.ln() - t + a.ln()
    }
}

/// Continued-fraction evaluation for the regularized incomplete beta
/// function (Numerical Recipes §6.4, `betacf`).
fn betacf(a: f64, b: f64, x: f64) -> f64 {
    const MAX_ITER: usize = 200;
    const EPS: f64 = 3.0e-16;
    const FP_MIN: f64 = 1.0e-300;

    let qab = a + b;
    let qap = a + 1.0;
    let qam = a - 1.0;
    let mut c = 1.0;
    let mut d = 1.0 - qab * x / qap;
    if d.abs() < FP_MIN {
        d = FP_MIN;
    }
    d = 1.0 / d;
    let mut h = d;

    for m in 1..=MAX_ITER {
        let mf = m as f64;
        let m2 = 2.0 * mf;

        let aa = mf * (b - mf) * x / ((qam + m2) * (a + m2));
        d = 1.0 + aa * d;
        if d.abs() < FP_MIN {
            d = FP_MIN;
        }
        c = 1.0 + aa / c;
        if c.abs() < FP_MIN {
            c = FP_MIN;
        }
        d = 1.0 / d;
        h *= d * c;

        let aa = -(a + mf) * (qab + mf) * x / ((a + m2) * (qap + m2));
        d = 1.0 + aa * d;
        if d.abs() < FP_MIN {
            d = FP_MIN;
        }
        c = 1.0 + aa / c;
        if c.abs() < FP_MIN {
            c = FP_MIN;
        }
        d = 1.0 / d;
        let del = d * c;
        h *= del;

        if (del - 1.0).abs() < EPS {
            break;
        }
    }
    h
}

/// Regularized incomplete beta function `I_x(a, b)` (Numerical Recipes §6.4,
/// `betai`).
fn regularized_incomplete_beta(a: f64, b: f64, x: f64) -> f64 {
    if x <= 0.0 {
        return 0.0;
    }
    if x >= 1.0 {
        return 1.0;
    }
    let bt =
        (log_gamma(a + b) - log_gamma(a) - log_gamma(b) + a * x.ln() + b * (1.0 - x).ln()).exp();
    if x < (a + 1.0) / (a + b + 2.0) {
        bt * betacf(a, b, x) / a
    } else {
        1.0 - bt * betacf(b, a, 1.0 - x) / b
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- bootstrap_ci ---

    #[test]
    fn bootstrap_ci_constant_values_gives_zero_width() {
        let mut seed = Seed::new(1, 0);
        let ci = bootstrap_ci(&[5.0, 5.0, 5.0, 5.0], 500, 0.05, &mut seed).unwrap();
        assert!((ci.mean - 5.0).abs() < 1e-12);
        assert!((ci.ci_lower - 5.0).abs() < 1e-12);
        assert!((ci.ci_upper - 5.0).abs() < 1e-12);
        assert!(ci.ci_width.abs() < 1e-12);
        assert!(ci.se.abs() < 1e-12);
    }

    #[test]
    fn bootstrap_ci_single_value_gives_zero_width() {
        let mut seed = Seed::new(2, 0);
        let ci = bootstrap_ci(&[3.5], 100, 0.05, &mut seed).unwrap();
        assert!((ci.mean - 3.5).abs() < 1e-12);
        assert!((ci.ci_lower - 3.5).abs() < 1e-12);
        assert!((ci.ci_upper - 3.5).abs() < 1e-12);
    }

    #[test]
    fn bootstrap_ci_widens_with_dispersion() {
        let mut seed = Seed::new(3, 0);
        let low_var = bootstrap_ci(&[9.9, 10.0, 10.1], 2000, 0.05, &mut seed).unwrap();
        let mut seed2 = Seed::new(3, 0);
        let high_var = bootstrap_ci(&[0.0, 10.0, 20.0], 2000, 0.05, &mut seed2).unwrap();
        assert!(high_var.ci_width > low_var.ci_width);
        assert!((low_var.mean - 10.0).abs() < 1e-9);
        assert!((high_var.mean - 10.0).abs() < 1e-9);
    }

    #[test]
    fn bootstrap_ci_bounds_are_ordered_and_contain_mean_region() {
        let mut seed = Seed::new(4, 0);
        let ci = bootstrap_ci(&[1.0, 2.0, 3.0, 4.0, 5.0], 5000, 0.05, &mut seed).unwrap();
        assert!(ci.ci_lower <= ci.mean + 1e-9);
        assert!(ci.ci_upper >= ci.mean - 1e-9);
        assert!(ci.ci_lower <= ci.ci_upper);
    }

    #[test]
    fn bootstrap_ci_same_seed_is_deterministic() {
        let mut s1 = Seed::new(7, 0);
        let mut s2 = Seed::new(7, 0);
        let a = bootstrap_ci(&[1.0, 2.0, 3.0], 200, 0.1, &mut s1).unwrap();
        let b = bootstrap_ci(&[1.0, 2.0, 3.0], 200, 0.1, &mut s2).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn bootstrap_ci_rejects_empty_values() {
        let mut seed = Seed::new(8, 0);
        assert!(matches!(
            bootstrap_ci(&[], 100, 0.05, &mut seed).unwrap_err(),
            TrainError::InsufficientSamples { name: "values", .. }
        ));
    }

    #[test]
    fn bootstrap_ci_rejects_zero_n_bootstrap() {
        let mut seed = Seed::new(9, 0);
        assert!(matches!(
            bootstrap_ci(&[1.0], 0, 0.05, &mut seed).unwrap_err(),
            TrainError::InvalidBootstrapCount { value: 0 }
        ));
    }

    #[test]
    fn bootstrap_ci_rejects_out_of_range_alpha() {
        let mut seed = Seed::new(10, 0);
        assert!(matches!(
            bootstrap_ci(&[1.0, 2.0], 100, 1.5, &mut seed).unwrap_err(),
            TrainError::InvalidSignificanceLevel { .. }
        ));
        let mut seed = Seed::new(11, 0);
        assert!(matches!(
            bootstrap_ci(&[1.0, 2.0], 100, 0.0, &mut seed).unwrap_err(),
            TrainError::InvalidSignificanceLevel { .. }
        ));
    }

    #[test]
    fn percentile_hand_computed_linear_interpolation() {
        // numpy.percentile([1,2,3,4], 50) == 2.5 (linear interpolation).
        assert!((percentile(&[1.0, 2.0, 3.0, 4.0], 50.0) - 2.5).abs() < 1e-12);
        // numpy.percentile([1,2,3,4], 0) == 1, 100 == 4.
        assert!((percentile(&[1.0, 2.0, 3.0, 4.0], 0.0) - 1.0).abs() < 1e-12);
        assert!((percentile(&[1.0, 2.0, 3.0, 4.0], 100.0) - 4.0).abs() < 1e-12);
    }

    // --- cohens_d ---

    #[test]
    fn cohens_d_identical_groups_gives_zero() {
        let d = cohens_d(&[1.0, 2.0, 3.0], &[1.0, 2.0, 3.0]);
        assert!(d.abs() < 1e-12);
    }

    #[test]
    fn cohens_d_hand_computed_value() {
        // a = [1,2,3] mean=2 var(ddof=1)=1; b = [4,5,6] mean=5 var(ddof=1)=1.
        // pooled = sqrt(((2*1)+(2*1))/4) = 1. d = (2-5)/1 = -3.
        let d = cohens_d(&[1.0, 2.0, 3.0], &[4.0, 5.0, 6.0]);
        assert!((d - (-3.0)).abs() < 1e-9, "d={d}");
    }

    #[test]
    fn cohens_d_below_min_samples_returns_zero() {
        assert_eq!(cohens_d(&[1.0], &[1.0, 2.0, 3.0]), 0.0);
        assert_eq!(cohens_d(&[1.0, 2.0], &[]), 0.0);
    }

    #[test]
    fn cohens_d_zero_pooled_variance_returns_zero() {
        let d = cohens_d(&[5.0, 5.0, 5.0], &[5.0, 5.0, 5.0]);
        assert_eq!(d, 0.0);
    }

    // --- welch_t_test / compute_p_value ---

    #[test]
    fn welch_t_test_identical_groups_gives_near_zero_t_and_p_near_one() {
        let r = welch_t_test(&[1.0, 2.0, 3.0, 4.0], &[1.0, 2.0, 3.0, 4.0]).unwrap();
        assert!(r.t_stat.abs() < 1e-9, "t={}", r.t_stat);
        assert!((r.p_value - 1.0).abs() < 1e-6, "p={}", r.p_value);
        assert!(r.mean_diff.abs() < 1e-12);
    }

    #[test]
    fn welch_t_test_clearly_separated_groups_gives_small_p_value() {
        let a = [10.0, 10.1, 9.9, 10.05, 9.95];
        let b = [0.0, 0.1, -0.1, 0.05, -0.05];
        let r = welch_t_test(&a, &b).unwrap();
        assert!(r.t_stat > 0.0);
        assert!(r.p_value < 1e-4, "p={}", r.p_value);
        assert!(r.cohens_d > 5.0);
    }

    #[test]
    fn welch_t_test_rejects_too_few_samples() {
        assert!(matches!(
            welch_t_test(&[1.0], &[1.0, 2.0]).unwrap_err(),
            TrainError::InsufficientSamples {
                name: "group_a",
                ..
            }
        ));
        assert!(matches!(
            welch_t_test(&[1.0, 2.0], &[1.0]).unwrap_err(),
            TrainError::InsufficientSamples {
                name: "group_b",
                ..
            }
        ));
    }

    #[test]
    fn compute_p_value_matches_welch_t_test_p_value() {
        let a = [1.0, 2.0, 3.0, 4.0, 5.0];
        let b = [2.0, 4.0, 6.0, 8.0, 10.0];
        let expected = welch_t_test(&a, &b).unwrap().p_value;
        let actual = compute_p_value(&a, &b).unwrap();
        assert_eq!(expected, actual);
    }

    #[test]
    fn welch_t_test_p_value_is_symmetric_under_group_swap() {
        let a = [1.0, 5.0, 3.0, 9.0];
        let b = [2.0, 2.0, 8.0, 1.0];
        let r_ab = welch_t_test(&a, &b).unwrap();
        let r_ba = welch_t_test(&b, &a).unwrap();
        assert!((r_ab.p_value - r_ba.p_value).abs() < 1e-9);
        assert!((r_ab.t_stat + r_ba.t_stat).abs() < 1e-9);
    }

    // --- student_t_two_tailed_p_value / regularized_incomplete_beta ---

    #[test]
    fn student_t_p_value_at_t_zero_is_one() {
        assert!((student_t_two_tailed_p_value(0.0, 10.0) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn student_t_p_value_matches_known_table_values() {
        // Two-tailed critical values: t=2.228, df=10 -> p ~= 0.05 (textbook
        // t-table entry for alpha=0.05 two-tailed at df=10).
        let p = student_t_two_tailed_p_value(2.228, 10.0);
        assert!((p - 0.05).abs() < 1e-3, "p={p}");
        // t=1.960, df=1e6 (~normal) -> p ~= 0.05.
        let p_large_df = student_t_two_tailed_p_value(1.959_964, 1_000_000.0);
        assert!((p_large_df - 0.05).abs() < 1e-3, "p={p_large_df}");
    }

    #[test]
    fn regularized_incomplete_beta_symmetric_midpoint_is_half() {
        // I_0.5(a, a) == 0.5 for any a (symmetric beta distribution).
        assert!((regularized_incomplete_beta(2.0, 2.0, 0.5) - 0.5).abs() < 1e-9);
        assert!((regularized_incomplete_beta(5.0, 5.0, 0.5) - 0.5).abs() < 1e-9);
    }

    #[test]
    fn regularized_incomplete_beta_boundary_values() {
        assert_eq!(regularized_incomplete_beta(2.0, 3.0, 0.0), 0.0);
        assert_eq!(regularized_incomplete_beta(2.0, 3.0, 1.0), 1.0);
    }

    #[test]
    fn log_gamma_matches_factorial_for_integers() {
        // Gamma(n) = (n-1)!  =>  log_gamma(5) = ln(4!) = ln(24).
        assert!((log_gamma(5.0) - 24.0_f64.ln()).abs() < 1e-9);
        assert!((log_gamma(1.0) - 0.0).abs() < 1e-9);
        // Gamma(0.5) = sqrt(pi).
        assert!((log_gamma(0.5) - std::f64::consts::PI.sqrt().ln()).abs() < 1e-9);
    }
}

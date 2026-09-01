//! Statistical utilities for the Year-4-Q1.2 rigorous-benchmarking surface
//! (`prinet.utils.y4q1_tools`: `bootstrap_ci`, `cohens_d`, `welch_t_test`,
//! `spatial_correlation`).
//!
//! These are the owned Rust numerics behind the `prin.y4q1_tools` compatibility
//! wrappers WP-036C S1 (`0144M5`) needs. The Welch t-test p-value uses the
//! regularized incomplete beta function (Lentz's continued fraction) rather
//! than a SciPy dependency; the bootstrap resampler draws from a deterministic
//! [`prin_dynamics::Seed`] so `bootstrap_ci` is reproducible for a fixed seed.

use prin_dynamics::Seed;

use crate::error::SimError;

/// Sample mean of a slice (`0.0` for an empty slice).
fn mean(xs: &[f64]) -> f64 {
    if xs.is_empty() {
        return 0.0;
    }
    xs.iter().sum::<f64>() / xs.len() as f64
}

/// Unbiased (ddof = 1) sample variance.
fn var_ddof1(xs: &[f64]) -> f64 {
    let n = xs.len();
    if n < 2 {
        return 0.0;
    }
    let m = mean(xs);
    xs.iter().map(|&x| (x - m) * (x - m)).sum::<f64>() / (n as f64 - 1.0)
}

/// Linear-interpolation percentile (matches `numpy.percentile` default method).
fn percentile_linear(sorted: &[f64], q: f64) -> f64 {
    if sorted.is_empty() {
        return f64::NAN;
    }
    if sorted.len() == 1 {
        return sorted[0];
    }
    let rank = q / 100.0 * (sorted.len() as f64 - 1.0);
    let lo = rank.floor() as usize;
    let hi = rank.ceil() as usize;
    if lo == hi {
        return sorted[lo];
    }
    let frac = rank - lo as f64;
    sorted[lo] * (1.0 - frac) + sorted[hi] * frac
}

/// Natural log of the gamma function (Lanczos approximation, g = 7).
fn ln_gamma(x: f64) -> f64 {
    const G: f64 = 7.0;
    const C: [f64; 9] = [
        0.999_999_999_999_809_9,
        676.520_368_121_885_1,
        -1_259.139_216_722_402_8,
        771.323_428_777_653_1,
        -176.615_029_162_140_6,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_311_6e-7,
    ];
    if x < 0.5 {
        // Reflection formula.
        std::f64::consts::PI.ln() - (std::f64::consts::PI * x).sin().ln() - ln_gamma(1.0 - x)
    } else {
        let x = x - 1.0;
        let mut a = C[0];
        let t = x + G + 0.5;
        for (i, &c) in C.iter().enumerate().skip(1) {
            a += c / (x + i as f64);
        }
        0.5 * (2.0 * std::f64::consts::PI).ln() + (x + 0.5) * t.ln() - t + a.ln()
    }
}

/// Regularized incomplete beta function `I_x(a, b)` (Numerical Recipes `betai`).
fn betai(a: f64, b: f64, x: f64) -> f64 {
    if x <= 0.0 {
        return 0.0;
    }
    if x >= 1.0 {
        return 1.0;
    }
    let ln_beta = ln_gamma(a + b) - ln_gamma(a) - ln_gamma(b);
    let front = (a * x.ln() + b * (1.0 - x).ln() + ln_beta).exp();
    if x < (a + 1.0) / (a + b + 2.0) {
        front * betacf(a, b, x) / a
    } else {
        1.0 - front * betacf(b, a, 1.0 - x) / b
    }
}

/// Lentz's continued fraction for the incomplete beta function.
fn betacf(a: f64, b: f64, x: f64) -> f64 {
    const TINY: f64 = 1e-30;
    const EPS: f64 = 3e-12;
    let qab = a + b;
    let qap = a + 1.0;
    let qam = a - 1.0;
    let mut c = 1.0;
    let mut d = 1.0 - qab * x / qap;
    if d.abs() < TINY {
        d = TINY;
    }
    d = 1.0 / d;
    let mut h = d;
    for m in 1..200 {
        let m = m as f64;
        let m2 = 2.0 * m;
        let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
        d = 1.0 + aa * d;
        if d.abs() < TINY {
            d = TINY;
        }
        c = 1.0 + aa / c;
        if c.abs() < TINY {
            c = TINY;
        }
        d = 1.0 / d;
        h *= d * c;
        let aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
        d = 1.0 + aa * d;
        if d.abs() < TINY {
            d = TINY;
        }
        c = 1.0 + aa / c;
        if c.abs() < TINY {
            c = TINY;
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

/// Percentile bootstrap confidence interval for the mean.
///
/// Returns `(mean, ci_lower, ci_upper, ci_width, se)` where the CI is the
/// `alpha/2` … `1 − alpha/2` percentile band of `n_bootstrap` resample means
/// and `se` is the standard deviation of those means.
///
/// # Errors
///
/// Returns [`SimError::InvalidCoupling`] for an empty `values` slice or a
/// non-positive `n_bootstrap`.
pub fn bootstrap_ci(
    values: &[f64],
    n_bootstrap: usize,
    alpha: f64,
    seed: u64,
) -> Result<(f64, f64, f64, f64, f64), SimError> {
    if values.is_empty() || n_bootstrap == 0 {
        return Err(SimError::InvalidCoupling {
            reason: "bootstrap_ci requires non-empty values and n_bootstrap >= 1".to_string(),
        });
    }
    let n = values.len();
    let mut s = Seed::new(seed as u128, 0x626f_6f74);
    let mut means: Vec<f64> = Vec::with_capacity(n_bootstrap);
    for _ in 0..n_bootstrap {
        let mut acc = 0.0;
        for _ in 0..n {
            let j = ((s.next_f64() * n as f64) as usize).min(n - 1);
            acc += values[j];
        }
        means.push(acc / n as f64);
    }
    means.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let lo = percentile_linear(&means, 100.0 * alpha / 2.0);
    let hi = percentile_linear(&means, 100.0 * (1.0 - alpha / 2.0));
    let mm = mean(&means);
    let se = (means.iter().map(|&x| (x - mm) * (x - mm)).sum::<f64>() / n_bootstrap as f64).sqrt();
    Ok((mean(values), lo, hi, hi - lo, se))
}

/// Cohen's `d` effect size with pooled standard deviation.
///
/// Positive means `group_a > group_b`. Returns `0.0` when either group has
/// fewer than two samples or the pooled standard deviation is degenerate.
pub fn cohens_d(group_a: &[f64], group_b: &[f64]) -> f64 {
    let (na, nb) = (group_a.len(), group_b.len());
    if na < 2 || nb < 2 {
        return 0.0;
    }
    let va = var_ddof1(group_a);
    let vb = var_ddof1(group_b);
    let pooled = (((na - 1) as f64 * va + (nb - 1) as f64 * vb) / (na + nb - 2) as f64).sqrt();
    if pooled < 1e-12 {
        return 0.0;
    }
    (mean(group_a) - mean(group_b)) / pooled
}

/// Welch's t-test.
///
/// Returns `(t_stat, p_value, cohens_d, mean_diff)` with a two-tailed
/// `p_value` from the Student-t survival function (Welch–Satterthwaite degrees
/// of freedom). Matches `scipy.stats.ttest_ind(a, b, equal_var=False)` for the
/// statistic and p-value.
///
/// # Errors
///
/// Returns [`SimError::InvalidCoupling`] when either group has fewer than two
/// samples.
pub fn welch_t_test(group_a: &[f64], group_b: &[f64]) -> Result<(f64, f64, f64, f64), SimError> {
    let (na, nb) = (group_a.len(), group_b.len());
    if na < 2 || nb < 2 {
        return Err(SimError::InvalidCoupling {
            reason: "welch_t_test requires >= 2 samples per group".to_string(),
        });
    }
    let (ma, mb) = (mean(group_a), mean(group_b));
    let (va, vb) = (var_ddof1(group_a), var_ddof1(group_b));
    let sa = va / na as f64;
    let sb = vb / nb as f64;
    let denom = (sa + sb).sqrt();
    let mean_diff = ma - mb;
    let d = cohens_d(group_a, group_b);

    if denom < 1e-300 {
        let p = if mean_diff.abs() < 1e-300 { 1.0 } else { 0.0 };
        return Ok((0.0, p, d, mean_diff));
    }
    let t = mean_diff / denom;
    let df = (sa + sb).powi(2) / (sa * sa / (na as f64 - 1.0) + sb * sb / (nb as f64 - 1.0));
    // Two-tailed p = I_{df/(df+t^2)}(df/2, 1/2).
    let x = df / (df + t * t);
    let p = betai(df / 2.0, 0.5, x).clamp(0.0, 1.0);
    Ok((t, p, d, mean_diff))
}

/// Spatial autocorrelation of a 1-D field for lags `0 ..= max_lag`.
///
/// `max_lag` is clipped to `N / 2`. A degenerate (zero-variance) field returns
/// `[1.0, 0.0, 0.0, …]` with the original (unclipped) `max_lag + 1` length,
/// matching the reference.
pub fn spatial_correlation(values: &[f64], max_lag: usize) -> Vec<f64> {
    let n = values.len();
    let m = mean(values);
    let centered: Vec<f64> = values.iter().map(|&v| v - m).collect();
    let var = centered.iter().map(|&v| v * v).sum::<f64>() / n.max(1) as f64;
    if var < 1e-12 {
        let mut out = vec![0.0; max_lag + 1];
        out[0] = 1.0;
        return out;
    }
    let capped = max_lag.min(n / 2);
    (0..=capped)
        .map(|lag| {
            // torch.roll(v, lag): out[i] = v[(i - lag) mod n].
            let acc: f64 = (0..n)
                .map(|i| centered[i] * centered[(i + n - lag % n) % n])
                .sum();
            acc / n as f64 / var
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bootstrap_constant_is_narrow() {
        let (m, lo, hi, w, _se) = bootstrap_ci(&[3.0; 20], 2000, 0.05, 42).unwrap();
        assert!((m - 3.0).abs() < 1e-12);
        assert!(w < 1e-10);
        assert!(lo <= m && m <= hi);
    }

    #[test]
    fn bootstrap_reproducible() {
        let a = bootstrap_ci(&[1.0, 2.0, 3.0], 5000, 0.05, 99).unwrap();
        let b = bootstrap_ci(&[1.0, 2.0, 3.0], 5000, 0.05, 99).unwrap();
        assert_eq!(a.1, b.1);
        assert_eq!(a.2, b.2);
    }

    #[test]
    fn cohens_d_signs() {
        assert!(cohens_d(&[10.0, 11.0, 12.0], &[0.0, 1.0, 2.0]) > 0.0);
        assert!(cohens_d(&[1.0, 2.0, 3.0], &[1.0, 2.0, 3.0]).abs() < 1e-10);
        assert_eq!(cohens_d(&[1.0], &[2.0, 3.0]), 0.0);
        assert!(
            cohens_d(
                &[10.0, 10.1, 10.2, 9.9, 10.05],
                &[0.0, 0.1, -0.1, 0.05, -0.05]
            )
            .abs()
                > 0.8
        );
    }

    #[test]
    fn welch_identical_high_p() {
        let (t, p, _d, md) = welch_t_test(&[1.0, 2.0, 3.0, 4.0], &[1.0, 2.0, 3.0, 4.0]).unwrap();
        assert!(t.abs() < 1e-12);
        assert!(p > 0.05);
        assert!(md.abs() < 1e-12);
    }

    #[test]
    fn welch_separated_low_p() {
        let a = [100.0, 100.1, 100.2, 99.9, 100.05];
        let b = [0.0, 0.1, -0.1, 0.05, -0.05];
        let (_t, p, _d, md) = welch_t_test(&a, &b).unwrap();
        assert!(p < 0.001, "p = {p}");
        assert!(md > 0.0);
    }

    #[test]
    fn spatial_corr_lag0_is_one() {
        let v: Vec<f64> = (0..100).map(|i| ((i * 7 % 13) as f64) - 6.0).collect();
        let c = spatial_correlation(&v, 10);
        assert!((c[0] - 1.0).abs() < 1e-9);
        assert_eq!(c.len(), 11);
    }

    #[test]
    fn spatial_corr_constant() {
        let c = spatial_correlation(&[1.0; 50], 5);
        assert_eq!(c[0], 1.0);
        assert!(c[1..].iter().all(|&x| x == 0.0));
    }

    #[test]
    fn spatial_corr_clips_max_lag() {
        let v: Vec<f64> = (0..20).map(|i| (i as f64).sin()).collect();
        assert_eq!(spatial_correlation(&v, 100).len(), 11);
    }
}

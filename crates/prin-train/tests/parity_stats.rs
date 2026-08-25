//! Parity for [`prin_train::stats::welch_t_test`] against real
//! `scipy.stats.ttest_ind(equal_var=False)`.
//!
//! `tools/wp031_stats_fixture.py` runs a fixed set of two-group float
//! samples — engineered to cover clearly separated groups, identical
//! groups, unequal sample sizes, unequal variances, near-zero-variance
//! groups, and negative values — through the real `scipy.stats.ttest_ind`
//! (Project Plan §6 Phase 5, session brief "Statistical routines match
//! trusted references"), and commits the inputs plus scipy's own
//! `statistic`/`pvalue` output as
//! `crates/prin-train/tests/data/welch_t_test_reference_cases.json`. This
//! test replays the identical inputs through
//! [`prin_train::stats::welch_t_test`] and asserts `t_stat`/`p_value` match
//! within tight tolerance.
//!
//! Regenerate the fixture with:
//! `.venv/Scripts/python tools/wp031_stats_fixture.py` (`scipy` is a base
//! dependency; no extra required).

use prin_train::stats::welch_t_test;
use serde::Deserialize;

const FIXTURE: &str = include_str!("data/welch_t_test_reference_cases.json");

// Tight tolerance: both sides compute the same closed-form Welch
// t-statistic and the same Student's-t survival function (this port's own
// regularized-incomplete-beta implementation vs. scipy's `stdtr` C
// implementation), so any real discrepancy shows up far above float noise.
const RTOL: f64 = 1e-9;
const ATOL: f64 = 1e-12;

#[derive(Deserialize)]
struct Case {
    name: String,
    group_a: Vec<f64>,
    group_b: Vec<f64>,
    t_stat: f64,
    p_value: f64,
}

fn cases() -> Vec<Case> {
    serde_json::from_str(FIXTURE).expect("fixture parses as JSON")
}

fn assert_close(actual: f64, expected: f64, what: &str, scenario: &str) {
    let diff = (actual - expected).abs();
    let tol = ATOL + RTOL * expected.abs();
    assert!(
        diff <= tol,
        "{scenario}: {what}: actual {actual:.17e}, expected {expected:.17e}, diff {diff:.3e} > tol {tol:.3e}"
    );
}

#[test]
fn welch_t_test_matches_scipy_stats_ttest_ind() {
    let loaded = cases();
    assert!(!loaded.is_empty(), "fixture must not be empty");

    for case in &loaded {
        let result = welch_t_test(&case.group_a, &case.group_b)
            .unwrap_or_else(|e| panic!("{}: welch_t_test failed: {e}", case.name));
        assert_close(result.t_stat, case.t_stat, "t_stat", &case.name);
        assert_close(result.p_value, case.p_value, "p_value", &case.name);
    }
}

//! Parity for [`prin_daemon::mot::MotAccumulator`] against the real
//! `py-motmetrics` package.
//!
//! `tools/wp030_mot_fixture.py` replays a fixed set of oid/hid/distance
//! sequences — engineered to cover clean matches, misses, false positives,
//! an identity switch, an occlusion reappearance that must *not* count as a
//! switch, a `max_switch_time` boundary, rectangular per-frame shapes, an
//! empty frame, an all-forbidden-pairing frame, and an IoU-bbox-derived
//! distance matrix — through `motmetrics.MOTAccumulator` and
//! `motmetrics.metrics`, and commits the inputs plus the reference's own
//! MOTA/MOTP/IDF1/switch/FP/miss output as
//! `crates/prin-daemon/tests/data/mot_reference_cases.json`. This test
//! replays the identical inputs through
//! [`prin_daemon::mot::MotAccumulator`] and asserts its summary matches
//! within tight tolerance (Project Plan §6, "MOT metrics match motmetrics
//! reference").
//!
//! Regenerate the fixture with:
//! `.venv/Scripts/python tools/wp030_mot_fixture.py` (requires the `mot`
//! extra: `pip install -e ".[mot]"`).

use prin_daemon::mot::MotAccumulator;
use serde_json::Value;

const FIXTURE: &str = include_str!("data/mot_reference_cases.json");

// Tight tolerance: both sides compute the same closed-form arithmetic
// (sums, ratios, one Hungarian assignment) over the same f64 inputs, so any
// real discrepancy shows up far above float noise.
const RTOL: f64 = 1e-9;
const ATOL: f64 = 1e-12;

fn fixture() -> Value {
    serde_json::from_str(FIXTURE).expect("fixture parses as JSON")
}

/// Decode a metric value that may be a plain JSON number or one of the
/// non-finite tags `tools/wp030_mot_fixture.py` writes in their place
/// (`"NaN"`, `"Infinity"`, `"-Infinity"`) because bare non-finite tokens are
/// not valid JSON.
fn expected_f64(value: &Value) -> f64 {
    match value {
        Value::Number(n) => n.as_f64().expect("finite JSON number"),
        Value::String(s) => match s.as_str() {
            "NaN" => f64::NAN,
            "Infinity" => f64::INFINITY,
            "-Infinity" => f64::NEG_INFINITY,
            other => panic!("unrecognised non-finite tag: {other}"),
        },
        other => panic!("expected a number or non-finite tag, got {other}"),
    }
}

fn assert_close(actual: f64, expected: f64, what: &str, scenario: &str) {
    if expected.is_nan() {
        assert!(
            actual.is_nan(),
            "{scenario}: {what}: expected NaN, got {actual}"
        );
        return;
    }
    if expected.is_infinite() {
        assert_eq!(actual, expected, "{scenario}: {what}");
        return;
    }
    let diff = (actual - expected).abs();
    let tol = ATOL + RTOL * expected.abs();
    assert!(
        diff <= tol,
        "{scenario}: {what}: actual {actual:.17e}, expected {expected:.17e}, diff {diff:.3e} > tol {tol:.3e}"
    );
}

fn dist_matrix(frame: &Value) -> Vec<Vec<f64>> {
    frame["dists"]
        .as_array()
        .expect("dists array")
        .iter()
        .map(|row| {
            row.as_array()
                .expect("dists row")
                .iter()
                .map(|v| v.as_f64().unwrap_or(f64::NAN)) // `null` -> NaN (forbidden pairing)
                .collect()
        })
        .collect()
}

fn ids(value: &Value) -> Vec<u64> {
    value
        .as_array()
        .expect("id array")
        .iter()
        .map(|v| v.as_u64().expect("non-negative id"))
        .collect()
}

#[test]
fn fixture_has_the_expected_scenario_count() {
    let scenarios = fixture()["scenarios"].as_array().unwrap().len();
    assert_eq!(scenarios, 10);
}

#[test]
fn every_scenario_matches_the_motmetrics_reference_summary() {
    let doc = fixture();
    let scenarios = doc["scenarios"].as_array().expect("scenarios array");
    assert!(!scenarios.is_empty(), "fixture must not be empty");

    for scenario in scenarios {
        let name = scenario["name"].as_str().expect("scenario name");
        let mut acc = match scenario["max_switch_time"].as_u64() {
            Some(max_span) => MotAccumulator::with_max_switch_time(max_span),
            None => MotAccumulator::new(),
        };

        for (frame_id, frame) in scenario["frames"].as_array().unwrap().iter().enumerate() {
            let oids = ids(&frame["oids"]);
            let hids = ids(&frame["hids"]);
            let dists = dist_matrix(frame);
            acc.update(frame_id as u64, &oids, &hids, &dists)
                .unwrap_or_else(|e| panic!("{name}: frame {frame_id}: {e}"));
        }

        let summary = acc.summary();
        let expected = &scenario["expected"];

        assert_close(summary.mota, expected_f64(&expected["mota"]), "mota", name);
        assert_close(summary.motp, expected_f64(&expected["motp"]), "motp", name);
        assert_close(summary.idf1, expected_f64(&expected["idf1"]), "idf1", name);
        assert_eq!(
            summary.num_switches,
            expected["num_switches"].as_u64().unwrap(),
            "{name}: num_switches"
        );
        assert_eq!(
            summary.num_false_positives,
            expected["num_false_positives"].as_u64().unwrap(),
            "{name}: num_false_positives"
        );
        assert_eq!(
            summary.num_misses,
            expected["num_misses"].as_u64().unwrap(),
            "{name}: num_misses"
        );
    }
}

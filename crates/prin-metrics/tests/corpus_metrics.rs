//! Golden-corpus parity for order parameter and mean phase coherence.
//!
//! Compares [`prin_metrics::kuramoto_order_parameter`] and
//! [`prin_metrics::mean_phase_coherence`] against the
//! `order_parameter_traj` / `mean_phase_coherence_traj` arrays stored in the
//! PRINet-3.0-generated golden trajectory corpus (`parity/corpus`), from
//! which six representative cases were extracted into
//! `tests/data/corpus_metric_cases.json`.
//!
//! Tolerance: the registered METRIC tolerance for cross-platform
//! corpus-regeneration comparisons, `rtol = 1e-8, atol = 1e-12`
//! (`python/prin/parity/schema.py`, Project Plan amendment #16). PRINet
//! computes both metrics in `torch.float64`, and the corpus was authored on
//! the same platform family, so single-runtime drift is typically far below
//! this bound; the registered bound is asserted here because the fixture is
//! a corpus-regeneration artefact.

use prin_metrics::{kuramoto_order_parameter, mean_phase_coherence};
use serde_json::Value;

const FIXTURE: &str = include_str!("data/corpus_metric_cases.json");

// Registered METRIC tolerance (python/prin/parity/schema.py, amendment #16).
const METRIC_RTOL: f64 = 1e-8;
const METRIC_ATOL: f64 = 1e-12;

fn fixture() -> Value {
    serde_json::from_str(FIXTURE).expect("fixture parses")
}

fn vec_f64(v: &Value) -> Vec<f64> {
    v.as_array()
        .expect("array")
        .iter()
        .map(|x| x.as_f64().expect("f64 entry"))
        .collect()
}

fn assert_allclose(actual: f64, expected: f64, what: &str) {
    let diff = (actual - expected).abs();
    let tol = METRIC_ATOL + METRIC_RTOL * expected.abs();
    assert!(
        diff <= tol,
        "{what}: actual {actual:.17e}, expected {expected:.17e}, diff {diff:.3e} > tol {tol:.3e}"
    );
}

fn case_ids() -> Vec<String> {
    fixture()["cases"]
        .as_array()
        .expect("cases")
        .iter()
        .map(|c| c["case_id"].as_str().expect("case_id").to_string())
        .collect()
}

#[test]
fn corpus_fixture_contains_expected_cases() {
    let ids = case_ids();
    assert_eq!(ids.len(), 6);
    assert!(ids.iter().any(|id| id.starts_with("kuramoto_mean_field")));
    assert!(ids.iter().any(|id| id.starts_with("kuramoto_sparse_knn")));
    assert!(ids.iter().any(|id| id.starts_with("hopf_")));
    assert!(ids.iter().any(|id| id.starts_with("stuart_landau_full")));
}

#[test]
fn corpus_order_parameter_matches_prinet_at_registered_tolerance() {
    let fx = fixture();
    let mut snapshots = 0usize;
    for case in fx["cases"].as_array().expect("cases") {
        let case_id = case["case_id"].as_str().expect("case_id");
        let n = case["n_oscillators"].as_u64().expect("n") as usize;
        let phase_traj = case["phase_traj"].as_array().expect("phase_traj");
        let expected = vec_f64(&case["order_parameter_traj"]);
        assert_eq!(
            phase_traj.len(),
            expected.len(),
            "{case_id}: snapshot count"
        );
        for (t, snapshot) in phase_traj.iter().enumerate() {
            let phase: Vec<f64> = snapshot
                .as_array()
                .expect("snapshot")
                .iter()
                .map(|x| x.as_f64().expect("phase"))
                .collect();
            assert_eq!(phase.len(), n, "{case_id}: snapshot {t} width");
            let r = kuramoto_order_parameter(&phase).unwrap();
            assert!(
                (0.0..=1.0).contains(&r),
                "{case_id} snapshot {t}: R ∈ [0, 1] invariant violated: {r}"
            );
            assert_allclose(r, expected[t], &format!("{case_id}.order_parameter[{t}]"));
            snapshots += 1;
        }
    }
    assert_eq!(snapshots, 126, "6 cases × 21 snapshots");
}

#[test]
fn corpus_mean_phase_coherence_matches_prinet_at_registered_tolerance() {
    let fx = fixture();
    let mut snapshots = 0usize;
    for case in fx["cases"].as_array().expect("cases") {
        let case_id = case["case_id"].as_str().expect("case_id");
        let n = case["n_oscillators"].as_u64().expect("n") as usize;
        let phase_traj = case["phase_traj"].as_array().expect("phase_traj");
        let expected = vec_f64(&case["mean_phase_coherence_traj"]);
        assert_eq!(
            phase_traj.len(),
            expected.len(),
            "{case_id}: snapshot count"
        );
        for (t, snapshot) in phase_traj.iter().enumerate() {
            let phase: Vec<f64> = snapshot
                .as_array()
                .expect("snapshot")
                .iter()
                .map(|x| x.as_f64().expect("phase"))
                .collect();
            assert_eq!(phase.len(), n, "{case_id}: snapshot {t} width");
            let c = mean_phase_coherence(&phase).unwrap();
            assert!(
                (-1.0..=1.0).contains(&c),
                "{case_id} snapshot {t}: C ∈ [-1, 1] invariant violated: {c}"
            );
            assert_allclose(
                c,
                expected[t],
                &format!("{case_id}.mean_phase_coherence[{t}]"),
            );
            snapshots += 1;
        }
    }
    assert_eq!(snapshots, 126, "6 cases × 21 snapshots");
}

#[test]
fn corpus_coherence_order_parameter_identity_holds() {
    // Independent cross-check on golden data: C = (N r² − 1)/(N − 1). This
    // verifies the two PRINet-authored corpus arrays are mutually consistent
    // with the PRIN implementations at the single-runtime target.
    let fx = fixture();
    for case in fx["cases"].as_array().expect("cases") {
        let case_id = case["case_id"].as_str().expect("case_id");
        let n = case["n_oscillators"].as_u64().expect("n") as usize;
        let order = vec_f64(&case["order_parameter_traj"]);
        let coherence = vec_f64(&case["mean_phase_coherence_traj"]);
        for (t, (&r, &c)) in order.iter().zip(coherence.iter()).enumerate() {
            let expected = ((n as f64) * r * r - 1.0) / ((n as f64) - 1.0);
            let diff = (c - expected).abs();
            assert!(
                diff <= 1e-9 + 1e-8 * expected.abs(),
                "{case_id}[{t}]: C = {c}, identity gives {expected}, diff {diff}"
            );
        }
    }
}

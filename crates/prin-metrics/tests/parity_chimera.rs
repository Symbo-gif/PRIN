//! Rust-vs-PRINet 3.0.0 chimera-metric parity tests (`utils/oscillosim.py`).
//!
//! Reference values live in `tests/data/prinet_reference_chimera.json`,
//! produced by an ad-hoc helper running `prinet==3.0.0` on
//! `torch==2.13.0+cpu` (provenance recorded in the file). Inputs are
//! hard-coded in the helper, so the references are fully determined.
//!
//! Tolerance policy (Project Plan §5, amendment #14): PRINet 3.0 evaluates
//! `local_order_parameter` in `torch.complex64` and the remaining chimera
//! utilities in `torch.float32`. PRIN keeps the f64 reference path, so these
//! comparisons use the documented f32-drift tolerance (`rtol/atol = 1e-6`)
//! rather than the f64 `1e-10` single-runtime target. The discontinuity
//! mask and chimera number `η` are discrete and must match exactly.

use prin_metrics::{
    bimodality_index, chimera_index, discontinuity_measure, local_order_parameter,
    strength_of_incoherence, strength_of_incoherence_temporal,
};
use serde_json::Value;

const FIXTURE: &str = include_str!("data/prinet_reference_chimera.json");

const F32_HAZARD_RTOL: f64 = 1e-6;
const F32_HAZARD_ATOL: f64 = 1e-6;

fn fixture() -> Value {
    serde_json::from_str(FIXTURE).expect("fixture parses")
}

fn scalar(v: &Value) -> f64 {
    v.as_f64().expect("scalar")
}

fn vec_f64(v: &Value) -> Vec<f64> {
    v.as_array()
        .expect("array")
        .iter()
        .map(|x| x.as_f64().expect("f64 entry"))
        .collect()
}

fn vec_usize(v: &Value) -> Vec<usize> {
    v.as_array()
        .expect("array")
        .iter()
        .map(|x| x.as_u64().expect("usize entry") as usize)
        .collect()
}

fn vec_bool(v: &Value) -> Vec<bool> {
    v.as_array()
        .expect("array")
        .iter()
        .map(|x| x.as_bool().expect("bool entry"))
        .collect()
}

fn ring_rows(flat: &[usize], shape: &[usize]) -> Vec<Vec<usize>> {
    let n = shape[0];
    let k = shape[1];
    assert_eq!(flat.len(), n * k);
    flat.chunks_exact(k).map(<[usize]>::to_vec).collect()
}

fn assert_allclose(actual: f64, expected: f64, rtol: f64, atol: f64, what: &str) {
    let diff = (actual - expected).abs();
    let tol = atol + rtol * expected.abs();
    assert!(
        diff <= tol,
        "{what}: actual {actual}, expected {expected}, diff {diff} > tol {tol}"
    );
}

#[test]
fn parity_local_order_parameter_matches_prinet_f32_path() {
    let fx = fixture();
    let phase = vec_f64(&fx["phase"]);
    let shape: Vec<usize> = fx["nbr_ring_shape"]
        .as_array()
        .expect("shape")
        .iter()
        .map(|x| x.as_u64().expect("usize") as usize)
        .collect();
    let neighbors = ring_rows(&vec_usize(&fx["nbr_ring_flat"]), &shape);

    let r = local_order_parameter(&phase, &neighbors).unwrap();
    let expected = vec_f64(&fx["local_order_parameter"]);
    assert_eq!(r.len(), expected.len());
    for (i, (a, e)) in r.iter().zip(expected.iter()).enumerate() {
        assert_allclose(
            *a,
            *e,
            F32_HAZARD_RTOL,
            F32_HAZARD_ATOL,
            &format!("local_order_parameter[{i}]"),
        );
        assert!((0.0..=1.0).contains(a), "r_i ∈ [0, 1] invariant");
    }
}

#[test]
fn parity_bimodality_index_matches_prinet_f32_path() {
    let fx = fixture();

    // Bimodality of the PRINet local-order-parameter values (exact fixture
    // inputs): isolates the f32-vs-f64 moment arithmetic.
    let r_local = vec_f64(&fx["local_order_parameter"]);
    let bc = bimodality_index(&r_local).unwrap();
    assert_allclose(
        bc,
        scalar(&fx["bimodality_index"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "bimodality_index(r_local)",
    );

    // Bimodality of the uniform control sample.
    let uniform = vec_f64(&fx["bimodality_uniform_values"]);
    let bc_uniform = bimodality_index(&uniform).unwrap();
    assert_allclose(
        bc_uniform,
        scalar(&fx["bimodality_index_uniform"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "bimodality_index(uniform)",
    );

    // Degenerate controls return exactly 0.0 in both implementations.
    assert_eq!(bimodality_index(&[0.7; 8]).unwrap(), 0.0);
    assert_eq!(
        scalar(&fx["bimodality_index_constant"]),
        0.0,
        "PRINet constant-input control"
    );
    assert_eq!(bimodality_index(&[0.1, 0.9]).unwrap(), 0.0);
    assert_eq!(scalar(&fx["bimodality_index_short"]), 0.0);
}

#[test]
fn parity_strength_of_incoherence_matches_prinet_f32_path() {
    let fx = fixture();
    let phase = vec_f64(&fx["phase"]);
    let si = strength_of_incoherence(&phase, 5).unwrap();
    assert_allclose(
        si,
        scalar(&fx["strength_of_incoherence_w5"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "strength_of_incoherence(window=5)",
    );
}

#[test]
fn parity_discontinuity_measure_matches_prinet_exactly() {
    // The mask and η are discrete; f32/f64 curvature differences do not flip
    // any element for this fixture (all D values are far from the threshold).
    let fx = fixture();
    let phase = vec_f64(&fx["phase"]);
    let (mask, eta) = discontinuity_measure(&phase, 0.01).unwrap();
    assert_eq!(mask, vec_bool(&fx["discontinuity_mask"]), "coherent mask");
    assert_eq!(eta, fx["discontinuity_eta"].as_u64().expect("eta") as usize);
}

#[test]
fn parity_chimera_index_matches_prinet() {
    let fx = fixture();
    let phase = vec_f64(&fx["phase"]);
    let shape: Vec<usize> = fx["nbr_ring_shape"]
        .as_array()
        .expect("shape")
        .iter()
        .map(|x| x.as_u64().expect("usize") as usize)
        .collect();
    let neighbors = ring_rows(&vec_usize(&fx["nbr_ring_flat"]), &shape);
    let chi = chimera_index(&phase, &neighbors, 0.5).unwrap();
    // χ is a count ratio; no fixture r_i lies near the 0.5 cutoff, so the
    // f32/f64 difference cannot change the count.
    assert_allclose(
        chi,
        scalar(&fx["chimera_index_t05"]),
        1e-12,
        1e-15,
        "chimera_index(threshold=0.5)",
    );
    assert!((0.0..=1.0).contains(&chi), "χ ∈ [0, 1] invariant");
}

#[test]
fn parity_strength_of_incoherence_temporal_matches_prinet_f32_path() {
    let fx = fixture();
    let flat = vec_f64(&fx["si_temporal_traj"]);
    let shape: Vec<usize> = fx["si_temporal_shape"]
        .as_array()
        .expect("shape")
        .iter()
        .map(|x| x.as_u64().expect("usize") as usize)
        .collect();
    let (t, n) = (shape[0], shape[1]);
    assert_eq!(flat.len(), t * n);
    let traj: Vec<Vec<f64>> = flat.chunks_exact(n).map(<[f64]>::to_vec).collect();

    let si = strength_of_incoherence_temporal(&traj, 4, 1).unwrap();
    assert_allclose(
        si,
        scalar(&fx["si_temporal_w4_d1"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "strength_of_incoherence_temporal(window=4, discard=1)",
    );
}

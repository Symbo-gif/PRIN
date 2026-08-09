//! Rust-vs-PRINet 3.0.0 metrics parity tests (`core/measurement.py` family).
//!
//! Reference values live in `tests/data/prinet_reference_metrics.json`,
//! produced by an ad-hoc helper running `prinet==3.0.0` on
//! `torch==2.13.0+cpu` (provenance recorded in the file; WP-009 parity_pac
//! precedent). Inputs are hard-coded in the helper, so the references are
//! fully determined by the pinned environment.
//!
//! Tolerance policy (Project Plan §5, amendments #14 and #16):
//! - PRINet f64 reference paths (order parameter, mean phase coherence,
//!   coherence matrix, synchronization energy, sparse coherence/energy,
//!   inter-frame correlation): asserted at `rtol = 1e-10, atol = 1e-12`,
//!   the WP-010 single-runtime metric acceptance target.
//! - PSD and concept probabilities: PRINet truncates the resonance signal to
//!   `complex64` before the FFT (preserved f32 hazard); asserted at
//!   `rtol = 1e-6, atol = 1e-6`, consistent with the amendment #14 handling
//!   of PRINet's f32 complex paths.

use prin_metrics::{
    extract_concept_probabilities, inter_frame_phase_correlation, kuramoto_order_parameter,
    kuramoto_order_parameter_complex, mean_phase_coherence, phase_coherence_matrix,
    power_spectral_density, sparse_mean_phase_coherence, sparse_synchronization_energy,
    synchronization_energy,
};
use serde_json::Value;

const FIXTURE: &str = include_str!("data/prinet_reference_metrics.json");

const F64_RTOL: f64 = 1e-10;
const F64_ATOL: f64 = 1e-12;
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

fn rows_from_flat(flat: &[usize], n: usize, k: usize) -> Vec<Vec<usize>> {
    assert_eq!(flat.len(), n * k);
    flat.chunks_exact(k).map(<[usize]>::to_vec).collect()
}

fn assert_allclose_scalar(actual: f64, expected: f64, rtol: f64, atol: f64, what: &str) {
    let diff = (actual - expected).abs();
    let tol = atol + rtol * expected.abs();
    assert!(
        diff <= tol,
        "{what}: actual {actual}, expected {expected}, diff {diff} > tol {tol}"
    );
}

fn assert_allclose_vec(actual: &[f64], expected: &[f64], rtol: f64, atol: f64, what: &str) {
    assert_eq!(actual.len(), expected.len(), "{what}: length mismatch");
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert_allclose_scalar(*a, *e, rtol, atol, &format!("{what}[{i}]"));
    }
}

#[test]
fn parity_order_parameter_matches_prinet_f64() {
    let fx = fixture();
    for case in ["case_m1", "case_m2"] {
        let c = &fx[case];
        let phase = vec_f64(&c["phase"]);
        let r = kuramoto_order_parameter(&phase).unwrap();
        assert_allclose_scalar(
            r,
            scalar(&c["order_parameter"]),
            F64_RTOL,
            F64_ATOL,
            &format!("{case}.order_parameter"),
        );
        assert!((0.0..=1.0).contains(&r), "R ∈ [0, 1] invariant");
    }
}

#[test]
fn parity_order_parameter_complex_matches_prinet_f64() {
    let fx = fixture();
    let c = &fx["case_m1"];
    let phase = vec_f64(&c["phase"]);
    let z = kuramoto_order_parameter_complex(&phase).unwrap();
    assert_allclose_scalar(
        z.re,
        scalar(&c["order_parameter_complex_re"]),
        F64_RTOL,
        F64_ATOL,
        "case_m1.order_parameter_complex_re",
    );
    assert_allclose_scalar(
        z.im,
        scalar(&c["order_parameter_complex_im"]),
        F64_RTOL,
        F64_ATOL,
        "case_m1.order_parameter_complex_im",
    );
}

#[test]
fn parity_mean_phase_coherence_matches_prinet_f64() {
    let fx = fixture();
    for case in ["case_m1", "case_m2"] {
        let c = &fx[case];
        let phase = vec_f64(&c["phase"]);
        let coherence = mean_phase_coherence(&phase).unwrap();
        assert_allclose_scalar(
            coherence,
            scalar(&c["mean_phase_coherence"]),
            F64_RTOL,
            F64_ATOL,
            &format!("{case}.mean_phase_coherence"),
        );
    }
}

#[test]
fn parity_phase_coherence_matrix_matches_prinet_f64() {
    let fx = fixture();
    let c = &fx["case_m1"];
    let phase = vec_f64(&c["phase"]);
    let matrix = phase_coherence_matrix(&phase).unwrap();
    let expected = vec_f64(&c["phase_coherence_matrix"]);
    assert_allclose_vec(
        &matrix,
        &expected,
        F64_RTOL,
        F64_ATOL,
        "case_m1.phase_coherence_matrix",
    );
}

#[test]
fn parity_synchronization_energy_matches_prinet_f64() {
    let fx = fixture();
    let m1 = &fx["case_m1"];
    let phase = vec_f64(&m1["phase"]);
    let amplitude = vec_f64(&m1["amplitude"]);

    let e_default = synchronization_energy(&phase, &amplitude, None).unwrap();
    assert_allclose_scalar(
        e_default,
        scalar(&m1["synchronization_energy_default"]),
        F64_RTOL,
        F64_ATOL,
        "case_m1.synchronization_energy_default",
    );

    let matrix = vec_f64(&m1["coupling_matrix"]);
    let e_matrix = synchronization_energy(&phase, &amplitude, Some(&matrix)).unwrap();
    assert_allclose_scalar(
        e_matrix,
        scalar(&m1["synchronization_energy_matrix"]),
        F64_RTOL,
        F64_ATOL,
        "case_m1.synchronization_energy_matrix",
    );

    let m2 = &fx["case_m2"];
    let phase2 = vec_f64(&m2["phase"]);
    let amplitude2 = vec_f64(&m2["amplitude"]);
    let e2 = synchronization_energy(&phase2, &amplitude2, None).unwrap();
    assert_allclose_scalar(
        e2,
        scalar(&m2["synchronization_energy_default"]),
        F64_RTOL,
        F64_ATOL,
        "case_m2.synchronization_energy_default",
    );
}

#[test]
fn parity_inter_frame_phase_correlation_matches_prinet_f64() {
    let fx = fixture();
    for case in ["case_m1", "case_m2"] {
        let c = &fx[case];
        let phase = vec_f64(&c["phase"]);
        let prev = vec_f64(&c["phase_prev"]);
        let rho = inter_frame_phase_correlation(&phase, &prev).unwrap();
        assert_allclose_scalar(
            rho,
            scalar(&c["inter_frame_phase_correlation"]),
            F64_RTOL,
            F64_ATOL,
            &format!("{case}.inter_frame_phase_correlation"),
        );
        assert!((0.0..=1.0).contains(&rho), "ρ ∈ [0, 1] invariant");
    }
}

#[test]
fn parity_psd_matches_prinet_at_f32_hazard_tolerance() {
    // PRINet truncates exp(iφ) to complex64 before the FFT (preserved
    // numerical hazard, cf. amendment #14); the f64 PRIN path matches at the
    // documented f32-drift tolerance.
    let fx = fixture();
    let m1 = &fx["case_m1"];
    let phase = vec_f64(&m1["phase"]);
    let amplitude = vec_f64(&m1["amplitude"]);

    let psd = power_spectral_density(&amplitude, &phase, None).unwrap();
    assert_allclose_vec(
        &psd,
        &vec_f64(&m1["psd_default_bins"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "case_m1.psd_default_bins",
    );

    let psd12 = power_spectral_density(&amplitude, &phase, Some(12)).unwrap();
    assert_allclose_vec(
        &psd12,
        &vec_f64(&m1["psd_bins_12"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "case_m1.psd_bins_12",
    );

    let m2 = &fx["case_m2"];
    let phase2 = vec_f64(&m2["phase"]);
    let amplitude2 = vec_f64(&m2["amplitude"]);
    let psd2 = power_spectral_density(&amplitude2, &phase2, None).unwrap();
    assert_allclose_vec(
        &psd2,
        &vec_f64(&m2["psd_default_bins"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "case_m2.psd_default_bins",
    );
}

#[test]
fn parity_concept_probabilities_match_prinet_at_f32_hazard_tolerance() {
    let fx = fixture();
    let m1 = &fx["case_m1"];
    let phase = vec_f64(&m1["phase"]);
    let amplitude = vec_f64(&m1["amplitude"]);
    let probs =
        extract_concept_probabilities(&amplitude, &phase, &[2.0, 5.0, 9.0], &[1.5, 1.0, 2.0], None)
            .unwrap();
    assert_allclose_vec(
        &probs,
        &vec_f64(&m1["concept_probabilities"]),
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "case_m1.concept_probabilities",
    );
}

#[test]
fn parity_sparse_mean_phase_coherence_matches_prinet_f64() {
    let fx = fixture();
    let s = &fx["sparse"];
    let phase = vec_f64(&s["phase"]);
    let n = phase.len();

    for (k, key) in [(3usize, "k3"), (11usize, "k11")] {
        let neighbors = rows_from_flat(&vec_usize(&s[format!("nbr_idx_{key}")]), n, k);
        let c = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
        assert_allclose_scalar(
            c,
            scalar(&s[format!("sparse_mean_phase_coherence_{key}")]),
            F64_RTOL,
            F64_ATOL,
            &format!("sparse.sparse_mean_phase_coherence_{key}"),
        );
        assert!((0.0..=1.0).contains(&c), "sparse coherence ∈ [0, 1]");
    }
}

#[test]
fn parity_sparse_synchronization_energy_matches_prinet_f64() {
    let fx = fixture();
    let s = &fx["sparse"];
    let phase = vec_f64(&s["phase"]);
    let amplitude = vec_f64(&s["amplitude"]);
    let n = phase.len();

    for (k, key) in [(3usize, "k3"), (11usize, "k11")] {
        let neighbors = rows_from_flat(&vec_usize(&s[format!("nbr_idx_{key}")]), n, k);
        let e = sparse_synchronization_energy(&phase, &amplitude, &neighbors, 1.5).unwrap();
        assert_allclose_scalar(
            e,
            scalar(&s[format!("sparse_synchronization_energy_{key}")]),
            F64_RTOL,
            F64_ATOL,
            &format!("sparse.sparse_synchronization_energy_{key}"),
        );
    }
}

#[test]
fn parity_sparse_full_agreement_for_synchronized_phases() {
    // Sparse/full variants agree where mathematically equivalent: for fully
    // synchronized phases both the full mean phase coherence and the sparse
    // coherence over the PRINet k-NN index equal exactly 1.
    let fx = fixture();
    let s = &fx["sparse"];
    let phase = vec![0.7_f64; 12];
    let full = mean_phase_coherence(&phase).unwrap();
    assert_allclose_scalar(full, 1.0, F64_RTOL, F64_ATOL, "full synchronized coherence");

    let n = phase.len();
    let neighbors = rows_from_flat(&vec_usize(&s["nbr_idx_k3"]), n, 3);
    let sparse = sparse_mean_phase_coherence(&phase, &neighbors).unwrap();
    assert_allclose_scalar(
        sparse,
        1.0,
        F64_RTOL,
        F64_ATOL,
        "sparse synchronized coherence",
    );
}

#[test]
fn parity_sparse_energy_ratio_to_full_at_k_n_minus_1() {
    // Sparse energy with k = N−1 and K = 1 covers every off-diagonal edge at
    // weight 1/(N−1), while the dense default uses 1/N: the energies differ by
    // exactly N/(N−1). This is the normalization-consistency agreement
    // analogue of the sparse/full equivalence test in `prin-dynamics`.
    let fx = fixture();
    let s = &fx["sparse"];
    let phase = vec_f64(&s["phase"]);
    let amplitude = vec_f64(&s["amplitude"]);
    let n = phase.len();

    let full = synchronization_energy(&phase, &amplitude, None).unwrap();
    let neighbors: Vec<Vec<usize>> = (0..n)
        .map(|i| (0..n).filter(|&j| j != i).collect())
        .collect();
    let sparse = sparse_synchronization_energy(&phase, &amplitude, &neighbors, 1.0).unwrap();
    let ratio = (n as f64) / ((n - 1) as f64);
    assert_allclose_scalar(
        sparse,
        full * ratio,
        F64_RTOL,
        F64_ATOL,
        "sparse/full energy ratio",
    );
}

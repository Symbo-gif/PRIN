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
//!
//! **Deliberate, scoped non-parity for `strength_of_incoherence[_temporal]`
//! (Project Plan amendment #24, EMA-001 M-F1):** PRINet 3.0's
//! `oscillosim.py:876-878` computes the per-pair wrapped phase difference as
//! `remainder(diff, 2*pi) - pi`, which maps a raw difference of `0` to `-pi`
//! instead of `0` -- an upstream defect against its own documented "Centre
//! to [-pi, pi]" contract, independently confirmed by `math-audit-mcp`'s Z3
//! adapter (`EVIDENCE/math-audit/`, claim `PW-02`). PRIN's Rust
//! implementation was originally a bug-for-bug port of this formula and so
//! matched the PRINet fixture; EMA-001 M-F1 corrected `chimera.rs`'s
//! `centred_wrap` to actually satisfy its documented contract
//! (`d=0 => z=0`), which is a one-off correctness fix, not a "preserved
//! numerical hazard" (Project Plan §5) in the amendment #14/#16/#17 sense --
//! those document *equally valid* f32-vs-f64 or convention choices, whereas
//! this is a formula defect present in both implementations relative to
//! their own stated intent. `parity_strength_of_incoherence_matches_prinet_f32_path`
//! and `parity_strength_of_incoherence_temporal_matches_prinet_f32_path`
//! below therefore no longer assert byte-parity with the PRINet fixture for
//! these two metrics specifically; instead they positively demonstrate that
//! the fixture's values are reproduced by PRINet's *actual* (buggy) wrap
//! formula, so the divergence is attributable to exactly this one
//! documented, intentional fix and nothing else.

use prin_metrics::{
    bimodality_index, chimera_index, discontinuity_measure, local_order_parameter,
    strength_of_incoherence, strength_of_incoherence_temporal,
};
use serde_json::Value;
use std::f64::consts::{PI, TAU};

const FIXTURE: &str = include_str!("data/prinet_reference_chimera.json");

const F32_HAZARD_RTOL: f64 = 1e-6;
const F32_HAZARD_ATOL: f64 = 1e-6;

fn fixture() -> Value {
    serde_json::from_str(FIXTURE).expect("fixture parses")
}

/// Reimplementation of `strength_of_incoherence` using PRINet 3.0's actual
/// (pre-EMA-001-M-F1) wrap formula `remainder(diff, 2*pi) - pi`
/// (`oscillosim.py:876-878`) instead of the corrected centred wrap. Mirrors
/// `crates/prin-metrics/src/chimera.rs`'s windowing/smoothing logic exactly;
/// only the per-pair wrap step differs. Used solely to demonstrate that the
/// PRINet fixture's `strength_of_incoherence*` values are explained by this
/// specific upstream defect, not by an unrelated divergence.
fn prinet_buggy_strength_of_incoherence(phase: &[f64], window_size: usize) -> f64 {
    let n = phase.len();
    if n < 3 {
        return 0.0;
    }
    let buggy_wrap = |diff: f64| diff.rem_euclid(TAU) - PI;
    let z: Vec<f64> = (0..n)
        .map(|m| buggy_wrap(phase[m] - phase[(m + 1) % n]))
        .collect();

    let denom = z.iter().map(|v| v.abs()).sum::<f64>() / (n as f64);
    if denom < 1e-12 {
        return 0.0;
    }

    let w = window_size;
    let mut padded: Vec<f64> = Vec::with_capacity(n + 2 * w.min(n));
    padded.extend_from_slice(&z[n.saturating_sub(w)..]);
    padded.extend_from_slice(&z);
    padded.extend_from_slice(&z[..w.min(n)]);

    let smooth_len = (padded.len() + 1).saturating_sub(w).min(n);
    if smooth_len == 0 {
        return 0.0;
    }
    let mut numer = 0.0_f64;
    for m in 0..smooth_len {
        let acc: f64 = padded[m..m + w].iter().sum();
        numer += (acc / (w as f64)).abs();
    }
    numer /= smooth_len as f64;

    (1.0 - numer / denom).clamp(0.0, 1.0)
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
    // See the module doc: PRINet 3.0's own wrap formula is defective
    // (EMA-001 M-F1), so PRIN's corrected implementation is intentionally
    // not byte-parity with the fixture here.
    let fx = fixture();
    let phase = vec_f64(&fx["phase"]);
    let expected = scalar(&fx["strength_of_incoherence_w5"]);

    // Positive evidence: PRINet's actual (buggy) wrap formula, applied to
    // the same inputs, reproduces the fixture within the documented f32
    // tolerance -- confirming the fixture embeds the upstream defect.
    let si_prinet_buggy = prinet_buggy_strength_of_incoherence(&phase, 5);
    assert_allclose(
        si_prinet_buggy,
        expected,
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "prinet_buggy_strength_of_incoherence(window=5) vs PRINet fixture",
    );

    // PRIN's corrected implementation stays in-range but no longer matches
    // the buggy fixture.
    let si = strength_of_incoherence(&phase, 5).unwrap();
    assert!((0.0..=1.0).contains(&si), "SI ∈ [0, 1] invariant: {si}");
    assert!(
        (si - expected).abs() > 1e-3,
        "corrected SI ({si}) unexpectedly matches the buggy PRINet fixture ({expected}); \
         the M-F1 fix may have been lost"
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
    // See the module doc: same EMA-001 M-F1 scoped non-parity as
    // `parity_strength_of_incoherence_matches_prinet_f32_path`.
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
    let expected = scalar(&fx["si_temporal_w4_d1"]);

    // Positive evidence: the buggy per-frame formula, averaged the same way
    // strength_of_incoherence_temporal averages it, reproduces the fixture.
    let discard = 1usize;
    let frames = &traj[discard..];
    let si_prinet_buggy = frames
        .iter()
        .map(|frame| prinet_buggy_strength_of_incoherence(frame, 4))
        .sum::<f64>()
        / (frames.len() as f64);
    assert_allclose(
        si_prinet_buggy,
        expected,
        F32_HAZARD_RTOL,
        F32_HAZARD_ATOL,
        "prinet_buggy temporal mean(window=4, discard=1) vs PRINet fixture",
    );

    let si = strength_of_incoherence_temporal(&traj, 4, discard).unwrap();
    assert!((0.0..=1.0).contains(&si), "SI ∈ [0, 1] invariant: {si}");
    assert!(
        (si - expected).abs() > 1e-3,
        "corrected temporal SI ({si}) unexpectedly matches the buggy PRINet fixture ({expected}); \
         the M-F1 fix may have been lost"
    );
}

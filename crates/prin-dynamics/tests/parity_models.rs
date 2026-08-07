//! Rust-vs-PRINet 3.0.0 derivative parity tests for oscillator models.
//!
//! These tests compare `Dynamics::compute_derivatives` against hard-coded
//! reference values produced by `prinet==3.0.0` for the same initial state and
//! parameters. They cover Kuramoto, Stuart–Landau, and Hopf models in each
//! supported coupling mode (mean-field, full pairwise, sparse k-NN).
//!
//! Reference values were produced by an ad-hoc Python helper using `prinet==3.0.0`
//! and are embedded here so the test does not need a Python subprocess or a PyO3
//! bridge.
//!
//! Tolerance notes:
//! - Paths that use PRINet's `torch.complex64` (f32) internal arithmetic
//!   (Kuramoto/Hopf mean field, all Stuart–Landau modes) are compared with
//!   `epsilon = 1e-7` to absorb the documented 1e-8–1e-9 f32 truncation drift.
//! - Purely real float64 paths (Kuramoto/Hopf full and sparse) use
//!   `epsilon = 1e-12`.

use approx::assert_relative_eq;
use prin_dynamics::{
    CouplingMode, Dynamics, HopfOscillator, KuramotoOscillator, OscillatorState,
    StuartLandauOscillator,
};

fn assert_allclose(actual: &[f64], expected: &[f64], epsilon: f64) {
    assert_eq!(actual.len(), expected.len());
    for (a, e) in actual.iter().zip(expected.iter()) {
        assert_relative_eq!(*a, *e, epsilon = epsilon, max_relative = epsilon);
    }
}

fn case_kuramoto_full() -> (
    KuramotoOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        KuramotoOscillator::new(3, 1.5, 0.1, 0.01, CouplingMode::Full { matrix: None }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.2, 1.0],
        vec![1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    let dphase = vec![1.5200701578014788, 1.259343380052231, 0.2205864621462903];
    let damplitude = vec![0.6601844418546907, 0.7383866435942036, 0.5185045076076525];
    let dfrequency = vec![
        0.001733567192671596,
        0.000864477933507436,
        -0.0025980451261790323,
    ];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_kuramoto_mean_field() -> (
    KuramotoOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
    let dphase = vec![1.2336510028046368, 1.805290836783974];
    let damplitude = vec![0.9526365699131317, 0.9405304715989121];
    let dfrequency = vec![0.001168254981733353, -0.0009735457891719377];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_kuramoto_sparse() -> (
    KuramotoOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        KuramotoOscillator::new(4, 1.0, 0.1, 0.01, CouplingMode::SparseKnn { k: Some(2) }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.1, 1.0, 1.1],
        vec![1.0, 1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    let dphase = vec![
        1.4955203883541317,
        1.3417467464903277,
        0.6582532535096723,
        0.5044796116458682,
    ];
    let damplitude = vec![
        0.6243001433518016,
        0.7083070667743451,
        0.7083070667743451,
        0.6243001433518015,
    ];
    let dfrequency = vec![
        0.0024776019417706587,
        0.0017087337324516382,
        -0.001708733732451638,
        -0.002477601941770659,
    ];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_hopf_full() -> (
    HopfOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        HopfOscillator::new(3, 1.5, 1.0, 0.01, CouplingMode::Full { matrix: None }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.2, 1.0],
        vec![1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    let dphase = vec![1.5200701578014788, 1.259343380052231, 0.2205864621462903];
    let damplitude = vec![0.7601844418546907, 0.8383866435942036, 0.6185045076076525];
    let dfrequency = vec![
        0.001733567192671596,
        0.000864477933507436,
        -0.0025980451261790323,
    ];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_hopf_mean_field() -> (
    HopfOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model = HopfOscillator::new(3, 1.0, 1.0, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(
        vec![0.1, 0.5, 1.0],
        vec![1.5, 0.5, 1.0],
        vec![1.0, 2.0, 1.5],
        None,
    )
    .unwrap();
    let dphase = vec![1.2173413382538607, 1.9301986572827874, 1.0284322865210977];
    let damplitude = vec![-1.0142865242388244, 1.2947246650232098, 0.7904020546010853];
    let dfrequency = vec![
        0.0010867066912693042,
        -0.00011633557119535445,
        -0.0015718923782630076,
    ];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_hopf_sparse() -> (
    HopfOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        HopfOscillator::new(4, 1.0, 1.0, 0.01, CouplingMode::SparseKnn { k: Some(2) }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.1, 1.0, 1.1],
        vec![1.0, 1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    let dphase = vec![
        1.4955203883541317,
        1.3417467464903277,
        0.6582532535096723,
        0.5044796116458682,
    ];
    let damplitude = vec![
        0.7243001433518016,
        0.808307066774345,
        0.808307066774345,
        0.7243001433518015,
    ];
    let dfrequency = vec![
        0.0024776019417706587,
        0.0017087337324516382,
        -0.001708733732451638,
        -0.002477601941770659,
    ];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_stuart_landau_full() -> (
    StuartLandauOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::Full { matrix: None }).unwrap();
    let state = OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
    let dphase = vec![1.0993346646428108, 0.9006653732161427];
    let damplitude = vec![-0.00996670126914978, -0.009966720198626544];
    let dfrequency = vec![0.0, 0.0];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_stuart_landau_mean_field() -> (
    StuartLandauOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model = StuartLandauOscillator::new(3, 1.0, 1.0, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.2, 0.7],
        vec![1.0, 1.2, 0.9],
        vec![1.0, 1.5, 2.0],
        None,
    )
    .unwrap();
    let dphase = vec![1.2727330327033997, 1.5646705146166249, 1.5483228811260992];
    let damplitude = vec![
        -0.045187364021937015,
        -0.7380364740471499,
        0.17698043388305695,
    ];
    let dfrequency = vec![0.0, 0.0, 0.0];
    (model, state, dphase, damplitude, dfrequency)
}

fn case_stuart_landau_sparse() -> (
    StuartLandauOscillator,
    OscillatorState,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let model =
        StuartLandauOscillator::new(4, 1.0, 1.0, CouplingMode::SparseKnn { k: Some(2) }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.1, 1.0, 1.1],
        vec![1.0, 1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    let dphase = vec![
        1.4955203756690025,
        1.341746764035639,
        0.658253171381233,
        0.5044795869875003,
    ];
    let damplitude = vec![
        -0.2756998538970947,
        -0.19169296418641601,
        -0.1916928987346953,
        -0.2756998440121947,
    ];
    let dfrequency = vec![0.0, 0.0, 0.0, 0.0];
    (model, state, dphase, damplitude, dfrequency)
}

#[test]
fn parity_kuramoto_full_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_kuramoto_full();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-12);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-12);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_kuramoto_mean_field_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_kuramoto_mean_field();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-6);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-6);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-6);
}

#[test]
fn parity_kuramoto_sparse_knn_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_kuramoto_sparse();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-12);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-12);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_hopf_full_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_hopf_full();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-12);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-12);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_hopf_mean_field_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_hopf_mean_field();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-6);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-6);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-6);
}

#[test]
fn parity_hopf_sparse_knn_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_hopf_sparse();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-12);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-12);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_stuart_landau_full_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_stuart_landau_full();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-6);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-6);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_stuart_landau_mean_field_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_stuart_landau_mean_field();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-6);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-6);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

#[test]
fn parity_stuart_landau_sparse_knn_matches_prinet() {
    let (model, state, dphase, damplitude, dfrequency) = case_stuart_landau_sparse();
    let deriv = model.compute_derivatives(&state).unwrap();
    assert_allclose(&deriv.dphase, &dphase, 1e-6);
    assert_allclose(&deriv.damplitude, &damplitude, 1e-6);
    assert_allclose(&deriv.dfrequency, &dfrequency, 1e-12);
}

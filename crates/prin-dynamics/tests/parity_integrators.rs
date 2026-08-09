//! Rust-vs-PRINet 3.0.0 trajectory parity tests for the basic integrators.
//!
//! These tests compare `EulerIntegrator::step` and `RK4Integrator::step`
//! against hard-coded reference trajectories produced by `prinet==3.0.0` using
//! `torch.float64` for the same initial state, parameters, and timestep.
//!
//! Reference values were produced by an ad-hoc Python helper using
//! `prinet==3.0.0` with `dtype=torch.float64` and are embedded here so the test
//! does not need a Python subprocess or a PyO3 bridge.
//!
//! Tolerance notes:
//! - Paths that use PRINet's `torch.complex64` (f32) internal arithmetic for
//!   the mean-field order parameter (Kuramoto/Hopf mean field, all Stuart–
//!   Landau modes) accumulate ~1e-8 per-step drift from a fully f64 reference.
//!   These are compared with `rtol=1e-6, atol=1e-8` per the parity program
//!   (Plan §5) and the documented f32-complex numerical hazard (amendment #14).
//! - Purely real float64 paths (Kuramoto/Hopf full pairwise) use
//!   `rtol=1e-10, atol=1e-12` since both sides are fully f64.
//! - Multi-step trajectories (n=5, n=10) accumulate drift proportionally;
//!   mean-field/f32 paths use `rtol=1e-5, atol=1e-7` for n≥5.

use approx::assert_relative_eq;
use prin_dynamics::{
    integrate_fixed, CouplingMode, EulerIntegrator, HopfOscillator, Integrator, KuramotoOscillator,
    OscillatorState, RK4Integrator, StuartLandauOscillator,
};

/// Assert each element of `actual` is close to `expected` within `rtol`/`atol`.
fn assert_trajectory_close(actual: &[f64], expected: &[f64], rtol: f64, atol: f64) {
    assert_eq!(actual.len(), expected.len());
    for (a, e) in actual.iter().zip(expected.iter()) {
        assert_relative_eq!(*a, *e, max_relative = rtol, epsilon = atol);
    }
}

// ==================================================================
// Case 1: Kuramoto mean-field, N=2, f32-complex path
// ==================================================================

fn case_kuramoto_mean_field() -> (KuramotoOscillator, OscillatorState) {
    let model = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
    (model, state)
}

#[test]
fn parity_euler_kuramoto_mean_field_1_step() {
    let (model, state) = case_kuramoto_mean_field();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 1, 0.01, false).unwrap();
    let expected_phase = vec![0.11233651002804637, 0.5180529083678398];
    let expected_amp = vec![1.0095263656991313, 1.2094053047159892];
    let expected_freq = vec![1.0000116825498173, 1.9999902645421084];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-6, 1e-8);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-6, 1e-8);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-6, 1e-8);
}

#[test]
fn parity_euler_kuramoto_mean_field_5_steps() {
    let (model, state) = case_kuramoto_mean_field();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.16218507562813603, 0.5898113954460598];
    let expected_amp = vec![1.0483148865767595, 1.2477325825549626];
    let expected_freq = vec![1.0000609194103305, 1.9999490619588691];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

#[test]
fn parity_euler_kuramoto_mean_field_10_steps() {
    let (model, state) = case_kuramoto_mean_field();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 10, 0.01, false).unwrap();
    let expected_phase = vec![0.22562730120846886, 0.6784815854103957];
    let expected_amp = vec![1.0983721734446534, 1.2972638803373522];
    let expected_freq = vec![1.0001281087126133, 1.9998924311936859];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

#[test]
fn parity_rk4_kuramoto_mean_field_1_step() {
    let (model, state) = case_kuramoto_mean_field();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 1, 0.01, false).unwrap();
    let expected_phase = vec![0.11236152581823791, 0.5180304000874283];
    let expected_amp = vec![1.009560469774311, 1.2094405565734074];
    let expected_freq = vec![1.0000118073346775, 1.9999901522459202];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-6, 1e-8);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-6, 1e-8);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-6, 1e-8);
}

#[test]
fn parity_rk4_kuramoto_mean_field_5_steps() {
    let (model, state) = case_kuramoto_mean_field();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.16230835118142806, 0.5896997462390872];
    let expected_amp = vec![1.048491864562966, 1.2479150333739775];
    let expected_freq = vec![1.0000615341930557, 1.999948505051389];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

#[test]
fn parity_rk4_kuramoto_mean_field_10_steps() {
    let (model, state) = case_kuramoto_mean_field();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 10, 0.01, false).unwrap();
    let expected_phase = vec![0.2258692568973796, 0.6782606676729674];
    let expected_amp = vec![1.0987434149146857, 1.297645329569501];
    let expected_freq = vec![1.0001293149940906, 1.999891329561543];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

// ==================================================================
// Case 2: Kuramoto full pairwise, N=3, pure f64 path
// ==================================================================

fn case_kuramoto_full() -> (KuramotoOscillator, OscillatorState) {
    let model =
        KuramotoOscillator::new(3, 1.5, 0.1, 0.01, CouplingMode::Full { matrix: None }).unwrap();
    let state = OscillatorState::new(
        vec![0.0, 0.2, 1.0],
        vec![1.0, 1.0, 1.0],
        vec![1.0, 1.0, 1.0],
        None,
    )
    .unwrap();
    (model, state)
}

#[test]
fn parity_euler_kuramoto_full_5_steps() {
    let (model, state) = case_kuramoto_full();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.07580641625289414, 0.262849779904348, 1.0112194314205918];
    let expected_amp = vec![1.0340244059108838, 1.0377558269620997, 1.0272363245036653];
    let expected_freq = vec![1.0000860156307572, 1.0000428297311361, 0.9998707400774695];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-10, 1e-12);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-10, 1e-12);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-10, 1e-12);
}

#[test]
fn parity_rk4_kuramoto_full_5_steps() {
    let (model, state) = case_kuramoto_full();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.0757608130310706, 0.2628227432371084, 1.0112636748778356];
    let expected_amp = vec![1.0342828343586996, 1.0379714608174897, 1.0275666718678558];
    let expected_freq = vec![1.0000858621984179, 1.0000427389022504, 0.9998708896985965];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-10, 1e-12);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-10, 1e-12);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-10, 1e-12);
}

// ==================================================================
// Case 3: Hopf mean-field, N=3, f32-complex path
// ==================================================================

fn case_hopf_mean_field() -> (HopfOscillator, OscillatorState) {
    let model = HopfOscillator::new(3, 1.0, 1.0, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(
        vec![0.1, 0.5, 1.0],
        vec![1.5, 0.5, 1.0],
        vec![1.0, 2.0, 1.5],
        None,
    )
    .unwrap();
    (model, state)
}

#[test]
fn parity_euler_hopf_mean_field_5_steps() {
    let (model, state) = case_hopf_mean_field();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.16131425912275404, 0.5960540530020532, 1.0520147277056051];
    let expected_amp = vec![1.4549053829255207, 0.5653557315463567, 1.0384939783662945];
    let expected_freq = vec![1.000055830854061, 1.9999930619758093, 1.4999222072807088];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

#[test]
fn parity_rk4_hopf_mean_field_5_steps() {
    let (model, state) = case_hopf_mean_field();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.16141936831563583, 0.5959428156599229, 1.0521454767286278];
    let expected_amp = vec![1.4560701390692503, 0.5655124474761858, 1.038254672630105];
    let expected_freq = vec![1.000056199827825, 1.9999927770876091, 1.4999223665059267];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-5, 1e-7);
}

// ==================================================================
// Case 4: Stuart–Landau full pairwise, N=2, f32-complex path
// ==================================================================

fn case_stuart_landau_full() -> (StuartLandauOscillator, OscillatorState) {
    let model =
        StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::Full { matrix: None }).unwrap();
    let state = OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
    (model, state)
}

#[test]
fn parity_euler_stuart_landau_full_5_steps() {
    let (model, state) = case_stuart_landau_full();
    let mut euler = EulerIntegrator::new();
    let (result, _) = integrate_fixed(&mut euler, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.05487027249974499, 0.24512972772434033];
    let expected_amp = vec![0.9995401563206873, 0.9995401570685088];
    let expected_freq = vec![1.0, 1.0];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-10, 1e-12);
}

#[test]
fn parity_rk4_stuart_landau_full_5_steps() {
    let (model, state) = case_stuart_landau_full();
    let mut rk4 = RK4Integrator::new();
    let (result, _) = integrate_fixed(&mut rk4, &model, &state, 5, 0.01, false).unwrap();
    let expected_phase = vec![0.05484692729106905, 0.24515307341740405];
    let expected_amp = vec![0.9995489646455709, 0.9995489646948075];
    let expected_freq = vec![1.0, 1.0];
    assert_trajectory_close(&result.phase, &expected_phase, 1e-5, 1e-7);
    assert_trajectory_close(&result.amplitude, &expected_amp, 1e-5, 1e-7);
    assert_trajectory_close(&result.frequency, &expected_freq, 1e-10, 1e-12);
}

// ==================================================================
// RK4 order-of-convergence property (h^4) — parity with theoretical order
// ==================================================================

#[test]
fn parity_rk4_order_h4_on_amplitude_decay() {
    // For dr/dt = -λ·r (Kuramoto K=0, decay=λ), RK4 error ∝ h^4.
    // Exact: r(t) = r0·exp(-λ·t).
    let model = KuramotoOscillator::new(1, 0.0, 1.0, 0.0, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.0], vec![1.0], vec![0.0], None).unwrap();
    let t_final = 0.1_f64;
    let r_exact = (-t_final).exp();

    let h_vals = [0.1, 0.05, 0.025];
    let mut errors = [0.0_f64; 3];
    for (idx, &h) in h_vals.iter().enumerate() {
        let n_steps = (t_final / h).round() as usize;
        let mut rk4 = RK4Integrator::new();
        let (final_state, _) =
            integrate_fixed(&mut rk4, &model, &state, n_steps, h, false).unwrap();
        errors[idx] = (final_state.amplitude[0] - r_exact).abs();
    }
    // ratio ≈ 2^4 = 16
    let ratio1 = errors[0] / errors[1];
    let ratio2 = errors[1] / errors[2];
    assert!(
        ratio1 > 8.0 && ratio1 < 32.0,
        "RK4 order broken: ratio1={ratio1}"
    );
    assert!(
        ratio2 > 8.0 && ratio2 < 32.0,
        "RK4 order broken: ratio2={ratio2}"
    );
}

// ==================================================================
// RK45 tolerance property — tighter tolerance → smaller error
// ==================================================================

#[test]
fn parity_rk45_tolerance_property_on_amplitude_decay() {
    let model = KuramotoOscillator::new(1, 0.0, 1.0, 0.0, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.0], vec![1.0], vec![0.0], None).unwrap();
    let t_final = 0.5_f64;
    let r_exact = (-t_final).exp();

    let mut rk45_loose = prin_dynamics::RK45Integrator::new(1e-3, 1e-5, 10_000).unwrap();
    let res_loose = rk45_loose
        .integrate_adaptive(&model, &state, t_final, 0.01, false)
        .unwrap();
    let err_loose = (res_loose.final_state.amplitude[0] - r_exact).abs();

    let mut rk45_tight = prin_dynamics::RK45Integrator::new(1e-8, 1e-10, 10_000).unwrap();
    let res_tight = rk45_tight
        .integrate_adaptive(&model, &state, t_final, 0.01, false)
        .unwrap();
    let err_tight = (res_tight.final_state.amplitude[0] - r_exact).abs();

    assert!(
        err_tight < err_loose,
        "tighter tolerance should reduce error: loose={err_loose}, tight={err_tight}"
    );
    assert!(
        err_tight < 1e-4,
        "tight tolerance error should be small: {err_tight}"
    );
    assert!(res_tight.accepted_steps >= res_loose.accepted_steps);
}

// ==================================================================
// Error path tests — typed failures
// ==================================================================

#[test]
fn parity_integrator_invalid_dt_returns_typed_error() {
    let model = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
    let mut euler = EulerIntegrator::new();
    let mut rk4 = RK4Integrator::new();
    assert!(matches!(
        euler.step(&model, &state, 0.0).unwrap_err(),
        prin_dynamics::IntegrateError::InvalidTimestep { .. }
    ));
    assert!(matches!(
        rk4.step(&model, &state, -1.0).unwrap_err(),
        prin_dynamics::IntegrateError::InvalidTimestep { .. }
    ));
}

#[test]
fn parity_integrate_fixed_zero_steps_returns_typed_error() {
    let model = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
    let state = OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();
    let mut euler = EulerIntegrator::new();
    assert!(matches!(
        integrate_fixed(&mut euler, &model, &state, 0, 0.01, false).unwrap_err(),
        prin_dynamics::IntegrateError::ZeroSteps
    ));
}

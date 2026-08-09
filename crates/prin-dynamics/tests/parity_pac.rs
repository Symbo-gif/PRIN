//! Rust-vs-PRINet 3.0.0 phase–amplitude coupling (PAC) parity tests.
//!
//! These tests compare `PhaseAmplitudeCoupling::modulate` against hard-coded
//! reference values produced by `prinet==3.0.0`'s
//! `PhaseAmplitudeCoupling.modulate` for the same inputs.
//!
//! Reference values were produced by an ad-hoc Python helper using
//! `prinet==3.0.0` and are embedded here so the test does not need a Python
//! subprocess or a PyO3 bridge.
//!
//! Tolerance notes:
//! - PRINet 3.0 computes PAC in `torch.float32` (default dtype), producing
//!   up to ~1e-7 drift from a fully f64 reference. The Rust implementation
//!   uses f64 throughout, so comparisons use `epsilon = 1e-6` to absorb the
//!   documented f32 truncation drift (consistent with amendment #14).

use approx::assert_relative_eq;
use prin_dynamics::pac::PhaseAmplitudeCoupling;

fn assert_allclose(actual: &[f64], expected: &[f64], epsilon: f64) {
    assert_eq!(actual.len(), expected.len());
    for (a, e) in actual.iter().zip(expected.iter()) {
        assert_relative_eq!(*a, *e, epsilon = epsilon, max_relative = epsilon);
    }
}

#[test]
fn parity_pac_basic_modulation_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0,1,2,3], fast=[1,2,3,4], offset=0
    // mean_slow = 1.5, modulation = 1 + 0.5*cos(1.5) = 1.0353686008338514 (f64)
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let slow = [0.0_f64, 1.0, 2.0, 3.0];
    let fast = [1.0_f64, 2.0, 3.0, 4.0];
    let out = pac.modulate(&slow, &fast, 0.0).unwrap();
    let expected = [
        1.0353686008338514,
        2.070737201667703,
        3.1061058025015544,
        4.141474403335406,
    ];
    assert_allclose(&out, &expected, 1e-6);
}

#[test]
fn parity_pac_with_offset_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0,1,2,3], fast=[1,2,3,4], offset=0.5
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let slow = [0.0_f64, 1.0, 2.0, 3.0];
    let fast = [1.0_f64, 2.0, 3.0, 4.0];
    let out = pac.modulate(&slow, &fast, 0.5).unwrap();
    let expected = [
        0.7919265817264288,
        1.5838531634528576,
        2.3757797451792864,
        3.1677063269057153,
    ];
    assert_allclose(&out, &expected, 1e-6);
}

#[test]
fn parity_pac_default_depth_matches_prinet() {
    // PRINet 3.0 default: m=0.3, slow=[0,1,2,3], fast=[1,2,3,4], offset=0
    let pac = PhaseAmplitudeCoupling::default();
    let slow = [0.0_f64, 1.0, 2.0, 3.0];
    let fast = [1.0_f64, 2.0, 3.0, 4.0];
    let out = pac.modulate(&slow, &fast, 0.0).unwrap();
    let expected = [
        1.021221160500311,
        2.042442321000622,
        3.063663481500933,
        4.084884642001244,
    ];
    assert_allclose(&out, &expected, 1e-6);
}

#[test]
fn parity_pac_different_sizes_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0,1,2] (mean=1.0), fast=[1,2,3,4,5], offset=0
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let slow = [0.0_f64, 1.0, 2.0];
    let fast = [1.0_f64, 2.0, 3.0, 4.0, 5.0];
    let out = pac.modulate(&slow, &fast, 0.0).unwrap();
    let expected = [
        1.2701511529340699,
        2.5403023058681398,
        3.8104534588022094,
        5.0806046117362795,
        6.35075576467035,
    ];
    assert_allclose(&out, &expected, 1e-6);
}

#[test]
fn parity_pac_single_oscillator_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0.5], fast=[2.0], offset=0.3
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let out = pac.modulate(&[0.5], &[2.0], 0.3).unwrap();
    assert_relative_eq!(
        out[0],
        2.6967067093471653,
        epsilon = 1e-6,
        max_relative = 1e-6
    );
}

#[test]
fn parity_pac_max_depth_matches_prinet() {
    // PRINet 3.0: m=1.0, slow=[0], fast=[5], offset=0 → 5*(1+cos(0)) = 10
    let pac = PhaseAmplitudeCoupling::new(1.0).unwrap();
    let out = pac.modulate(&[0.0], &[5.0], 0.0).unwrap();
    assert_relative_eq!(out[0], 10.0, epsilon = 1e-6, max_relative = 1e-6);
}

#[test]
fn parity_pac_zero_depth_matches_prinet() {
    // PRINet 3.0: m=0.0, slow=[1.0], fast=[3.0], offset=0.5 → 3.0
    let pac = PhaseAmplitudeCoupling::new(0.0).unwrap();
    let out = pac.modulate(&[1.0], &[3.0], 0.5).unwrap();
    assert_relative_eq!(out[0], 3.0, epsilon = 1e-6, max_relative = 1e-6);
}

#[test]
fn parity_pac_clamps_large_amplitude_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0,1], fast=[100,200], offset=0 → clamped to 10
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let out = pac.modulate(&[0.0, 1.0], &[100.0, 200.0], 0.0).unwrap();
    assert_relative_eq!(out[0], 10.0, epsilon = 1e-6, max_relative = 1e-6);
    assert_relative_eq!(out[1], 10.0, epsilon = 1e-6, max_relative = 1e-6);
}

#[test]
fn parity_pac_clamps_tiny_amplitude_matches_prinet() {
    // PRINet 3.0: m=0.5, slow=[0,1], fast=[1e-8,1e-9], offset=0 → clamped to 1e-6
    let pac = PhaseAmplitudeCoupling::new(0.5).unwrap();
    let out = pac.modulate(&[0.0, 1.0], &[1e-8, 1e-9], 0.0).unwrap();
    assert_relative_eq!(out[0], 1e-6, epsilon = 1e-6, max_relative = 1e-6);
    assert_relative_eq!(out[1], 1e-6, epsilon = 1e-6, max_relative = 1e-6);
}

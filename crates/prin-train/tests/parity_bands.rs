//! Rust-vs-PRINet-3.0.0 golden-value parity test for
//! [`DiscreteDeltaThetaGamma::step`].
//!
//! `prin-train` has no complex-tensor autodiff and no PRINet `nn.Module`
//! object to call end-to-end (Burn has neither), so — matching the
//! `prin-dynamics` `tests/parity_bands.rs` precedent — the reference values
//! below are transcribed directly from PRINet 3.0's
//! `core.propagation.networks.DiscreteDeltaThetaGamma.step` formula
//! (`nd=nt=ng=2`, `batch=1`) and evaluated independently in plain
//! `torch==2.13.0+cpu` float64.
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp022_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-021 precedent).

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::bands::{
    DiscreteBandState, DiscreteDeltaThetaGammaConfig, DiscreteDeltaThetaGammaParams,
};

type TestBackend = NdArray<f64>;

/// Real f64 on both sides, but Burn's `matmul`/`sum_dim` reduction order
/// differs from torch's, compounding across the multi-op PAC-gate/amplitude
/// chain (the `prin-dynamics` `parity_bands.rs` `FULL_RTOL`/`FULL_ATOL`
/// precedent for the same class of discrepancy). Measured worst case on this
/// fixture: `1.65e-8` absolute.
const RTOL: f64 = 1e-7;
const ATOL: f64 = 5e-8;

fn assert_close(actual: &[f64], expected: &[f64], rtol: f64, atol: f64) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert!(
            (a - e).abs() <= atol || (a - e).abs() <= rtol * e.abs(),
            "index {i}: actual {a:.17e} vs expected {e:.17e} \
             (abs {:.3e} > atol {atol:.3e})",
            (a - e).abs()
        );
    }
}

fn tensor2(
    values: &[f64],
    shape: [usize; 2],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 2> {
    Tensor::from_data(TensorData::new(values.to_vec(), shape.to_vec()), device)
}

fn tensor1(
    values: &[f64],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 1> {
    Tensor::from_data(TensorData::new(values.to_vec(), vec![values.len()]), device)
}

#[test]
fn discrete_delta_theta_gamma_step_matches_prinet_3_0() {
    let device = Default::default();

    let phase = [0.3, 1.1, 2.0, 4.2, 0.7, 5.5];
    let amp = [1.0, 0.8, 1.2, 0.9, 1.1, 0.6];
    let w_delta = [0.0, 0.5, -0.3, 0.0];
    let w_theta = [0.0, 0.2, 0.4, 0.0];
    let w_gamma = [0.0, -0.1, 0.6, 0.0];
    let w_pac_dt = [0.1, -0.2, 0.3, 0.1, -0.1, 0.2, 0.05, -0.05];
    let b_pac_dt = [0.3, 0.3];
    let w_pac_tg = [0.2, -0.1, -0.2, 0.15, 0.1, 0.1, -0.05, 0.2];
    let b_pac_tg = [0.3, 0.3];
    let mu_delta = 1.0;
    let mu_theta = 1.2;
    let mu_gamma = 0.8;
    let expected_phase = [
        0.42925048659808934,
        1.2278157744162903,
        2.3786081112384143,
        4.573757132815497,
        3.2142702874806703,
        1.736065803345264,
    ];
    let expected_amp = [
        1.0,
        0.80288,
        0.7509849165208528,
        0.4968727034861509,
        0.6348770017590317,
        0.3355452131148443,
    ];

    let cfg =
        DiscreteDeltaThetaGammaConfig::with_params(2, 2, 2, 2.0, 0.3, 2.0, 6.0, 40.0).unwrap();
    let params = DiscreteDeltaThetaGammaParams {
        delta_freq: tensor1(&[2.0, 2.0], &device),
        theta_freq: tensor1(&[6.0, 6.0], &device),
        gamma_freq: tensor1(&[40.0, 40.0], &device),
        w_delta: tensor2(&w_delta, [2, 2], &device),
        w_theta: tensor2(&w_theta, [2, 2], &device),
        w_gamma: tensor2(&w_gamma, [2, 2], &device),
        w_pac_dt: tensor2(&w_pac_dt, [4, 2], &device),
        b_pac_dt: tensor1(&b_pac_dt, &device),
        w_pac_tg: tensor2(&w_pac_tg, [4, 2], &device),
        b_pac_tg: tensor1(&b_pac_tg, &device),
        mu_delta: tensor2(&[mu_delta], [1, 1], &device),
        mu_theta: tensor2(&[mu_theta], [1, 1], &device),
        mu_gamma: tensor2(&[mu_gamma], [1, 1], &device),
    };
    let net = cfg.init_from_params(params).unwrap();

    let state = DiscreteBandState::new(
        tensor2(&phase, [1, 6], &device),
        tensor2(&amp, [1, 6], &device),
    )
    .unwrap();
    let next = net.step(state, 0.01).unwrap();

    let actual_phase = next.phase().clone().to_data().to_vec::<f64>().unwrap();
    let actual_amp = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();

    assert_close(&actual_phase, &expected_phase, RTOL, ATOL);
    assert_close(&actual_amp, &expected_amp, RTOL, ATOL);
}

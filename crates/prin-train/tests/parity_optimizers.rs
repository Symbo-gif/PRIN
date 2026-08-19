//! Rust-vs-PRINet-3.0.0 golden-value parity tests for
//! [`SyncGd`](prin_train::sync_gd::SyncGd), [`Rip`](prin_train::rip::Rip),
//! and [`Scalr`](prin_train::scalr::Scalr).
//!
//! Calls the actual PRINet 3.0 `SynchronizedGradientDescent`,
//! `RIPOptimizer`, and `SCALROptimizer` classes directly (WP-023
//! `parity_inhibition.rs` precedent), not a formula retranscription.
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp024_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-023 precedent). `torch==2.13.0+cpu`,
//! float64.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::feedback::{OrderParameter, OscillatorOptimizer, StepFeedback};
use prin_train::rip::RipConfig;
use prin_train::scalr::ScalrConfig;
use prin_train::sync_gd::SyncGdConfig;

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-9;
const ATOL: f64 = 1e-12;

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

fn assert_scalar_close(actual: f64, expected: f64, rtol: f64, atol: f64) {
    assert!(
        (actual - expected).abs() <= atol || (actual - expected).abs() <= rtol * expected.abs(),
        "actual {actual:.17e} vs expected {expected:.17e}"
    );
}

fn tensor1(
    values: &[f64],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 1> {
    Tensor::from_data(TensorData::new(values.to_vec(), vec![values.len()]), device)
}

// ---------------------------------------------------------------------------
// 1. SynchronizedGradientDescent.step (SyncGd)
// ---------------------------------------------------------------------------

#[test]
fn sync_gd_step_matches_prinet_3_0() {
    let device = Default::default();

    let param0 = [0.5, -0.3, 1.2, -0.8, 0.1];
    let grad1 = [1.0, -0.5, 0.25, 0.75, -1.0];
    let expected_after_step1 = [0.48995, -0.29497, 1.1973799999999999, -0.80742, 0.10999];
    let expected_penalty1 = 0.18000000000000005;
    let grad2 = [-0.2, 0.4, -0.6, 0.1, 0.3];
    let expected_after_step2 = [
        0.417059045,
        -0.285434527,
        1.226722358,
        -0.8824733220000001,
        0.172801009,
    ];
    let expected_penalty2 = 0.0;
    let expected_order_history = [0.5, 0.9];

    let mut opt = SyncGdConfig::with_params(0.1, 0.9, 0.01, 2.0, 0.8, 0.1)
        .unwrap()
        .init::<TestBackend, 1>();

    let p = tensor1(&param0, &device);
    let g1 = tensor1(&grad1, &device);
    let p = opt.step(p, Some(g1), &StepFeedback::order(0.5)).unwrap();
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_after_step1,
        RTOL,
        ATOL,
    );
    assert_scalar_close(opt.penalty_history()[0], expected_penalty1, RTOL, ATOL);

    let g2 = tensor1(&grad2, &device);
    let p = opt.step(p, Some(g2), &StepFeedback::order(0.9)).unwrap();
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_after_step2,
        RTOL,
        ATOL,
    );
    assert_scalar_close(opt.penalty_history()[1], expected_penalty2, RTOL, ATOL);
    assert_eq!(opt.order_history(), &expected_order_history);
}

// ---------------------------------------------------------------------------
// 2. RIPOptimizer.step (Rip) — Hebbian coupling update
// ---------------------------------------------------------------------------

#[test]
fn rip_step_matches_prinet_3_0() {
    let device = Default::default();

    #[rustfmt::skip]
    let coupling0 = [
        0.0, 0.1, -0.2, 0.3,
        0.1, 0.0, 0.4, -0.1,
        -0.2, 0.4, 0.0, 0.2,
        0.3, -0.1, 0.2, 0.0,
    ];
    #[rustfmt::skip]
    let grad = [
        0.0, 0.05, -0.05, 0.02,
        0.05, 0.0, 0.01, -0.03,
        -0.05, 0.01, 0.0, 0.04,
        0.02, -0.03, 0.04, 0.0,
    ];
    let phase = [0.1, -0.4, 0.8, -0.2];
    let amplitude = [0.9, 1.3, 1.0, 1.5];
    #[rustfmt::skip]
    let expected_coupling = [
        0.0, 0.15845143982744908, -0.1441094687629307, 0.3819802840213045,
        0.0742035138859733, 0.0, 0.3907528449104665, -0.12340199733523728,
        -0.16246568125775843, 0.41684260323278705, 0.0, 0.22441813835208838,
        0.24441182958721724, -0.17044519307161687, 0.1595818616479116, 0.0,
    ];

    let mut opt = RipConfig::with_params(4, 0.2, 1.2)
        .unwrap()
        .init::<TestBackend>();
    let coupling = Tensor::<TestBackend, 2>::from_data(
        TensorData::new(coupling0.to_vec(), vec![4, 4]),
        &device,
    );
    let grad =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(grad.to_vec(), vec![4, 4]), &device);
    let phase =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(phase.to_vec(), vec![1, 4]), &device);
    let amplitude = Tensor::<TestBackend, 2>::from_data(
        TensorData::new(amplitude.to_vec(), vec![1, 4]),
        &device,
    );

    let out = opt
        .step(
            coupling,
            Some(grad),
            &StepFeedback::phase_amplitude(phase, amplitude),
        )
        .unwrap();

    assert_close(
        &out.to_data().to_vec::<f64>().unwrap(),
        &expected_coupling,
        RTOL,
        ATOL,
    );
}

// ---------------------------------------------------------------------------
// 3a. SCALROptimizer.step basic (Scalr) — lr scaling + warmup + momentum
// ---------------------------------------------------------------------------

#[test]
fn scalr_step_basic_matches_prinet_3_0() {
    let device = Default::default();

    let param0 = [1.0, -1.0, 0.5];
    let grad1 = [0.5, -0.5, 0.25];
    let expected_after_step1 = [0.975, -0.975, 0.4875];
    let expected_lr1 = 0.05;
    let grad2 = [-0.2, 0.3, -0.1];
    let expected_after_step2 = [0.9721033074783618, -0.9735516537391808, 0.4860516537391809];
    let expected_lr2 = 0.014483462608190868;
    let grad3 = [0.1, 0.1, -0.2];
    let expected_after_step3 = [0.9636817421731207, -0.9741994664549686, 0.4899385300339076];
    let expected_lr3 = 0.03239063578938874;
    let expected_order_history = [0.9, 0.3, 0.7];

    let mut opt =
        ScalrConfig::with_params(0.05, 0.8, 0.0, 0.15, 1.5, 1, 20, 0.01, 0.95, false, 0.1)
            .unwrap()
            .init::<TestBackend, 1>();

    let p = tensor1(&param0, &device);
    let p = opt
        .step(p, Some(tensor1(&grad1, &device)), &StepFeedback::order(0.9))
        .unwrap();
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_after_step1,
        RTOL,
        ATOL,
    );
    assert_scalar_close(opt.lr_history()[0], expected_lr1, RTOL, ATOL);

    let p = opt
        .step(p, Some(tensor1(&grad2, &device)), &StepFeedback::order(0.3))
        .unwrap();
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_after_step2,
        RTOL,
        ATOL,
    );
    assert_scalar_close(opt.lr_history()[1], expected_lr2, RTOL, ATOL);

    let p = opt
        .step(p, Some(tensor1(&grad3, &device)), &StepFeedback::order(0.7))
        .unwrap();
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_after_step3,
        RTOL,
        ATOL,
    );
    assert_scalar_close(opt.lr_history()[2], expected_lr3, RTOL, ATOL);
    assert_eq!(opt.order_history(), &expected_order_history);
}

// ---------------------------------------------------------------------------
// 3b. SCALROptimizer oscillation-aware decay + adaptive r_min
// ---------------------------------------------------------------------------

#[test]
fn scalr_oscillation_and_adaptive_r_min_matches_prinet_3_0() {
    let device = Default::default();

    let expected_lr_decay_factor = 0.6400000000000001;
    let expected_r_ema = 0.68097;
    let expected_r_min = 0.20429099999999997;
    let expected_final_param = [1.93846024352];

    let mut opt = ScalrConfig::with_params(0.02, 0.0, 0.0, 0.1, 1.0, 0, 4, 0.02, 0.8, true, 0.3)
        .unwrap()
        .init::<TestBackend, 1>();

    let mut p = tensor1(&[2.0], &device);
    for r in [0.9, 0.2, 0.9, 0.2, 0.9] {
        let grad = tensor1(&[1.0], &device);
        p = opt.step(p, Some(grad), &StepFeedback::order(r)).unwrap();
    }

    assert_scalar_close(opt.lr_decay_factor(), expected_lr_decay_factor, RTOL, ATOL);
    assert_scalar_close(opt.r_ema().unwrap(), expected_r_ema, RTOL, ATOL);
    assert_scalar_close(opt.r_min(), expected_r_min, RTOL, ATOL);
    assert_close(
        &p.to_data().to_vec::<f64>().unwrap(),
        &expected_final_param,
        RTOL,
        ATOL,
    );
}

// ---------------------------------------------------------------------------
// 4. OrderParameter dict resolution (SCALR Q3 per-frequency lr scaling) —
//    pure-formula parity, no PRINet 3.0 call needed: PRINet 3.0's
//    resolution is `sum(values())/max(len(),1)` global fallback plus a
//    direct dict lookup, reproduced exactly by `OrderParameter::{global,
//    resolve}`.
// ---------------------------------------------------------------------------

#[test]
fn order_parameter_dict_resolution_matches_reference_formula() {
    use std::collections::HashMap;

    let mut dict = HashMap::new();
    dict.insert("delta".to_string(), 0.8);
    dict.insert("theta".to_string(), 0.6);
    dict.insert("gamma".to_string(), 0.4);
    let order = OrderParameter::PerGroup(dict);

    // PRINet 3.0: sum(order_parameter.values()) / max(len(order_parameter), 1)
    let expected_global = (0.8 + 0.6 + 0.4) / 3.0;
    assert_scalar_close(order.global(), expected_global, RTOL, ATOL);
    assert_scalar_close(order.resolve("delta"), 0.8, RTOL, ATOL);
    assert_scalar_close(order.resolve("theta"), 0.6, RTOL, ATOL);
    // Unknown group falls back to the global mean.
    assert_scalar_close(order.resolve("unknown"), expected_global, RTOL, ATOL);
}

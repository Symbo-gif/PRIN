//! Rust-vs-PRINet-3.0.0 golden-value parity test for the core Kuramoto step
//! formula inside [`ResonanceLayer::step`](prin_train::layers::ResonanceLayer::step).
//!
//! This validates the dynamics `prin-train::layers` documents as a
//! line-for-line port of `nn.layers.ResonanceLayer.forward`'s loop body — the
//! documented deviation is the input-to-initial-state projection, not the
//! step formula itself (see `crates/prin-train/src/layers.rs` module docs).
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp022_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-021 precedent). `torch==2.13.0+cpu`,
//! float64.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::layers::{ResonanceLayerConfig, ResonanceLayerParams, ResonanceState};

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-10;
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
fn resonance_layer_step_matches_prinet_3_0() {
    let device = Default::default();

    let phase = [0.2, 1.5, 4.0];
    let amp = [1.0, 0.8, 1.3];
    let freq = [5.0, 6.0, 7.0];
    let coupling_raw = [0.0, 0.3, -0.2, 0.4, 0.0, 0.1, -0.1, 0.2, 0.0];
    let decay = [0.1, 0.15, 0.05];
    let modulation = [0.0, 0.02, -0.01, 0.03, 0.0, 0.01, -0.02, 0.01, 0.0];
    let expected_phase = [0.2522536118134613, 1.5582239441586292, 4.069093898796357];
    let expected_amp = [1.000557987345339, 0.7988164594561331, 1.2990666006500413];
    let expected_freq = [5.000002337108355, 5.999997887339231, 6.999998297506503];

    let cfg = ResonanceLayerConfig::with_params(3, 1, 1, 0.01, 0.1, 0.01).unwrap();
    let params = ResonanceLayerParams {
        coupling: tensor2(&coupling_raw, [3, 3], &device),
        decay: tensor1(&decay, &device),
        // input_proj is unused by `step` (only `init_state`/`forward`
        // touch it); n_dims=1 keeps the fixture minimal.
        input_proj: tensor2(&[0.0, 0.0, 0.0], [1, 3], &device),
        modulation: tensor2(&modulation, [3, 3], &device),
        base_frequency: tensor1(&[0.0, 0.0, 0.0], &device),
    };
    let layer = cfg.init_from_params(params).unwrap();

    let state = ResonanceState::new(
        tensor2(&phase, [1, 3], &device),
        tensor2(&amp, [1, 3], &device),
        tensor2(&freq, [1, 3], &device),
    )
    .unwrap();
    let next = layer.step(state).unwrap();

    let actual_phase = next.phase().clone().to_data().to_vec::<f64>().unwrap();
    let actual_amp = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();
    let actual_freq = next.frequency().clone().to_data().to_vec::<f64>().unwrap();

    assert_close(&actual_phase, &expected_phase, RTOL, ATOL);
    assert_close(&actual_amp, &expected_amp, RTOL, ATOL);
    assert_close(&actual_freq, &expected_freq, RTOL, ATOL);
}

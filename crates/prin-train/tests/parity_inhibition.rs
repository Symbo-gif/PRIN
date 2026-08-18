//! Rust-vs-PRINet-3.0.0 golden-value parity test for
//! [`FeedbackInhibition::compete`](prin_train::inhibition::FeedbackInhibition::compete).
//!
//! Calls the actual PRINet 3.0 `FeedbackInhibition` class directly (not a
//! formula retranscription — `compete` takes plain tensors and has no
//! trainable parameters of its own, unlike WP-022's `ResonanceLayer`, which
//! needed a from-scratch port because Burn has no complex-tensor autodiff).
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp023_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-022 precedent). `torch==2.13.0+cpu`,
//! float64.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::inhibition::FeedbackInhibitionConfig;

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

#[test]
fn feedback_inhibition_compete_matches_prinet_3_0() {
    let device = Default::default();

    let rates = [0.1, 5.0, 0.3, 9.0, 0.2, 4.5];
    let expected = [0.0, 5.0, 0.0, 9.0, 0.0, 0.0];

    let fbi = FeedbackInhibitionConfig::with_params(6, Some(2), 0.1, 1.0)
        .unwrap()
        .init();
    let rates_tensor =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(rates.to_vec(), vec![1, 6]), &device);
    let out = fbi
        .compete(rates_tensor)
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();

    assert_close(&out, &expected, RTOL, ATOL);
}

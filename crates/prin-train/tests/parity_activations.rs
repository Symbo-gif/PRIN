//! Rust-vs-PRINet-3.0.0 golden-value parity test for
//! [`d_silu`](prin_train::activations::d_silu) and
//! [`phase_activation`](prin_train::activations::phase_activation).
//!
//! Calls the actual PRINet 3.0 `dSiLU`/`PhaseActivation` classes directly.
//! Tolerance is looser than a typical parity test (`rtol=1e-6`, not
//! `1e-10`+): `burn-tensor` 0.16.1's default `sigmoid` op downcasts through
//! `f32` internally even on an `NdArray<f64>` backend, giving `d_silu` (and
//! everything built on it) a confirmed ~1e-7-relative precision floor — see
//! the "Confirmed upstream precision floor" section of
//! `crates/prin-train/src/activations.rs`'s `d_silu` rustdoc for the full
//! evidence. This is a third-party numerical-precision constraint, not a
//! parity defect in the port itself.
//!
//! Includes one input (`x = -3.0`) where `dSiLU(x)` is negative, exercising
//! the floored-modulo wrap (`crate::support::wrap_floor`) that
//! `phase_activation` needs and Burn's `remainder_scalar` does not provide
//! on its own.
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp023_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-022 precedent). `torch==2.13.0+cpu`,
//! float64.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::activations::{d_silu, phase_activation};

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-6;
const ATOL: f64 = 1e-6;

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
fn d_silu_matches_prinet_3_0() {
    let device = Default::default();

    let xs = [-3.0, -1.0, 0.0, 0.5, 2.0, 4.0, 12.0];
    let expected_d_silu = [
        -0.08810410601516963,
        0.07232948812851325,
        0.5,
        0.7399611873026518,
        1.0907842487848955,
        1.0526646148910728,
        1.0000675854676138,
    ];

    let xs_tensor =
        Tensor::<TestBackend, 1>::from_data(TensorData::new(xs.to_vec(), vec![xs.len()]), &device);
    let out = d_silu(xs_tensor).to_data().to_vec::<f64>().unwrap();

    assert_close(&out, &expected_d_silu, RTOL, ATOL);
}

#[test]
fn phase_activation_matches_prinet_3_0() {
    let device = Default::default();

    let xs = [-3.0, -1.0, 0.0, 0.5, 2.0, 4.0, 12.0];
    let expected_phase_activation = [
        6.195081201164417,
        0.07232948812851325,
        0.5,
        0.7399611873026518,
        1.0907842487848955,
        1.0526646148910728,
        1.0000675854676138,
    ];

    let n = xs.len();
    let xs_tensor =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(xs.to_vec(), vec![1, n]), &device);
    let out = phase_activation(xs_tensor)
        .to_data()
        .to_vec::<f64>()
        .unwrap();

    assert_close(&out, &expected_phase_activation, RTOL, ATOL);
}

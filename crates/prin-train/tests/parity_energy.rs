//! Rust-vs-PRINet-3.0.0 golden-value parity test for the coupling and
//! self-energy terms of
//! [`HolomorphicEnergy::forward`](prin_train::energy::HolomorphicEnergy::forward).
//!
//! PRINet 3.0's `HolomorphicEnergy` operates on genuinely complex
//! (`torch.complex64`) oscillator states; `prin-train::energy` carries the
//! same state as a [`ComplexTensor`](prin_train::activations::ComplexTensor)
//! `(re, im)` pair of `f64` tensors (Burn has no complex-tensor autodiff —
//! same constraint documented throughout this crate, e.g.
//! `crates/prin-train/src/layers.rs`). The reference generation script uses
//! `torch.complex128`, not the trainer's actual `complex64`, specifically so
//! this test isolates "is the energy formula ported correctly" from "does
//! the f32-vs-f64 complex hazard appear" (that hazard is a separate,
//! already-governed class — Project Plan amendment #14 — not something a
//! formula-correctness parity test should conflate). The task-energy term
//! (`beta != 0.0`) is untested here: `crate::energy::tests` covers it
//! directly (`task_energy_ignored_when_beta_is_zero`,
//! `task_energy_added_when_beta_nonzero`) since PRINet 3.0 computes it from
//! a `concept_proj` classification head this crate does not yet own (see
//! `crates/prin-train/src/hep.rs` module docs' "Scope" section).
//!
//! Reference generation:
//! `DOCS/test_and_benchmark_results/wp023_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-022 precedent). `torch==2.13.0+cpu`,
//! `complex128`.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::activations::ComplexTensor;
use prin_train::energy::HolomorphicEnergyConfig;

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-10;
const ATOL: f64 = 1e-12;

fn assert_close(actual: f64, expected: f64, rtol: f64, atol: f64) {
    let diff = (actual - expected).abs();
    assert!(
        diff <= atol || diff <= rtol * expected.abs(),
        "actual {actual:.17e} vs expected {expected:.17e} (abs {diff:.3e} > atol {atol:.3e})"
    );
}

fn tensor2(
    values: &[f64],
    shape: [usize; 2],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 2> {
    Tensor::from_data(TensorData::new(values.to_vec(), shape.to_vec()), device)
}

#[test]
fn holomorphic_energy_per_batch_matches_prinet_3_0() {
    let device = Default::default();

    let re = [0.6, -0.3, 1.1, 0.2, 0.9, -0.4];
    let im = [0.1, 0.4, -0.2, -0.3, 0.05, 0.6];
    let coupling = [0.0, 0.2, -0.1, 0.3, 0.0, 0.15, -0.05, 0.1, 0.0];
    let expected_per_batch_energy = [1.2904, 0.98345625];

    let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
    let coupling_tensor = tensor2(&coupling, [3, 3], &device);

    // Evaluated one batch row at a time so `forward`'s batch-mean matches
    // PRINet 3.0's per-batch-element energy exactly (mean of one element).
    for batch in 0..2 {
        let re_row = &re[batch * 3..(batch + 1) * 3];
        let im_row = &im[batch * 3..(batch + 1) * 3];
        let z = ComplexTensor::new(
            tensor2(re_row, [1, 3], &device),
            tensor2(im_row, [1, 3], &device),
        )
        .unwrap();
        let e = energy
            .forward(z, coupling_tensor.clone(), None, 0.0)
            .unwrap()
            .into_scalar();
        assert_close(e, expected_per_batch_energy[batch], RTOL, ATOL);
    }
}

#[test]
fn holomorphic_energy_batch_mean_matches_prinet_3_0() {
    let device = Default::default();

    let re = [0.6, -0.3, 1.1, 0.2, 0.9, -0.4];
    let im = [0.1, 0.4, -0.2, -0.3, 0.05, 0.6];
    let coupling = [0.0, 0.2, -0.1, 0.3, 0.0, 0.15, -0.05, 0.1, 0.0];
    let expected_mean_energy = 1.136928125;

    let energy = HolomorphicEnergyConfig::new(3).unwrap().init();
    let z =
        ComplexTensor::new(tensor2(&re, [2, 3], &device), tensor2(&im, [2, 3], &device)).unwrap();
    let coupling_tensor = tensor2(&coupling, [3, 3], &device);

    let e = energy
        .forward(z, coupling_tensor, None, 0.0)
        .unwrap()
        .into_scalar();

    assert_close(e, expected_mean_energy, RTOL, ATOL);
}

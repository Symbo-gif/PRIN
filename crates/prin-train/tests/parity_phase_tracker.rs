//! Rust-vs-PRINet-3.0.0 golden-value parity test for
//! [`PhaseTracker::phase_similarity`].
//!
//! Reference generation: `DOCS/test_and_benchmark_results/wp026_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-025 precedent) — calls the actual
//! `prinet.nn.hybrid.PhaseTracker.phase_similarity` method directly (it is
//! parameter-free, so no weight transcription is needed).

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_dynamics::Seed;
use prin_train::phase_tracker::PhaseTrackerConfig;

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-6;
const ATOL: f64 = 1e-6;

fn assert_close(actual: &[f64], expected: &[f64], rtol: f64, atol: f64) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert!(
            (a - e).abs() <= atol || (a - e).abs() <= rtol * e.abs(),
            "index {i}: actual {a:.17e} vs expected {e:.17e} (abs {:.3e} > atol {atol:.3e})",
            (a - e).abs()
        );
    }
}

#[test]
fn phase_similarity_matches_prinet_3_0() {
    let device = Default::default();
    let mut seed = Seed::new(0, 0);
    // n_osc = 1 + 1 + 3 = 5, matching the reference's PhaseTracker(n_delta=1,
    // n_theta=1, n_gamma=3). phase_similarity does not read any tracker
    // parameter, only n_osc via its input shapes.
    let tracker = PhaseTrackerConfig::with_params(4, 1, 1, 3, 1, 0.3)
        .unwrap()
        .init::<TestBackend>(&device, &mut seed);

    let phase_a = [0.1, 1.2, 2.3, 3.4, 4.5, 5.5, 0.5, 1.5, 2.5, 3.5];
    // 3.14159 (not `std::f64::consts::PI`) matches the exact value used when
    // these golden values were generated against PRINet 3.0.
    #[allow(clippy::approx_constant)]
    let phase_b = [
        0.0, 0.0, 0.0, 0.0, 0.0, 3.14159, 2.0, 1.0, 0.5, 6.0, 0.1, 1.2, 2.3, 3.4, 4.5,
    ];
    let expected_sim = [
        -0.09730152785778046,
        -0.1862037181854248,
        0.9999992251396179,
        -0.01612211763858795,
        -0.1955282837152481,
        0.6516302824020386,
    ];

    let a =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(phase_a.to_vec(), vec![2, 5]), &device);
    let b =
        Tensor::<TestBackend, 2>::from_data(TensorData::new(phase_b.to_vec(), vec![3, 5]), &device);

    let sim = tracker.phase_similarity(a, b).unwrap();
    let actual = sim.to_data().to_vec::<f64>().unwrap();

    assert_close(&actual, &expected_sim, RTOL, ATOL);
}

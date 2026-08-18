//! Regression test for WP022-F2 (`022-wp022-audit.md` §3.8): confirms
//! `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` are nameable in
//! explicit type annotations via the crate root, not only via their
//! `bands`/`layers` submodule paths.

use burn::backend::NdArray;
use prin_train::{DiscreteDeltaThetaGammaParams, ResonanceLayerParams};

type TestBackend = NdArray<f64>;

#[test]
fn params_are_nameable_at_crate_root() {
    fn accepts_bands_params(_: DiscreteDeltaThetaGammaParams<TestBackend>) {}
    fn accepts_layers_params(_: ResonanceLayerParams<TestBackend>) {}

    let _ = accepts_bands_params;
    let _ = accepts_layers_params;
}

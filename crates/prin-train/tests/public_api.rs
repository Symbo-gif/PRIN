//! Regression test for WP022-F2 (`022-wp022-audit.md` §3.8): confirms
//! `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` are nameable in
//! explicit type annotations via the crate root, not only via their
//! `bands`/`layers` submodule paths.
//!
//! Extended for WP023-F1 (`023-wp023-audit.md` §3.8/§4): the same guarantee
//! must hold for every subsequently added `Params` re-export, starting with
//! `GatedPhaseActivationParams`.

use burn::backend::NdArray;
use prin_train::{DiscreteDeltaThetaGammaParams, GatedPhaseActivationParams, ResonanceLayerParams};

type TestBackend = NdArray<f64>;

#[test]
fn params_are_nameable_at_crate_root() {
    fn accepts_bands_params(_: DiscreteDeltaThetaGammaParams<TestBackend>) {}
    fn accepts_layers_params(_: ResonanceLayerParams<TestBackend>) {}
    fn accepts_gated_phase_activation_params(_: GatedPhaseActivationParams<TestBackend>) {}

    let _ = accepts_bands_params;
    let _ = accepts_layers_params;
    let _ = accepts_gated_phase_activation_params;
}

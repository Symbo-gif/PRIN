//! Regression test for WP022-F2 (`022-wp022-audit.md` §3.8): confirms
//! `DiscreteDeltaThetaGammaParams` and `ResonanceLayerParams` are nameable in
//! explicit type annotations via the crate root, not only via their
//! `bands`/`layers` submodule paths.
//!
//! Extended for WP023-F1 (`023-wp023-audit.md` §3.8/§4): the same guarantee
//! must hold for every subsequently added `Params` re-export, starting with
//! `GatedPhaseActivationParams`.
//!
//! Extended again for WP-024: the same guarantee applies to the
//! `sync_gd`/`rip`/`scalr`/`feedback` re-exports (`SyncGd`, `Rip`, `Scalr`,
//! `OrderParameter`, `OscillatorOptimizer`, `StepFeedback`) — nameable and
//! usable via the crate root, not only via their submodule paths.
//!
//! Extended again for WP-026: `OscillatoryAttentionParams`.

use burn::backend::NdArray;
use prin_train::{
    DiscreteDeltaThetaGammaParams, GatedPhaseActivationParams, OrderParameter, OscillatorOptimizer,
    OscillatoryAttentionParams, ResonanceLayerParams, Rip, RipConfig, Scalr, ScalrConfig,
    StepFeedback, SyncGd, SyncGdConfig,
};

type TestBackend = NdArray<f64>;

#[test]
fn params_are_nameable_at_crate_root() {
    fn accepts_bands_params(_: DiscreteDeltaThetaGammaParams<TestBackend>) {}
    fn accepts_layers_params(_: ResonanceLayerParams<TestBackend>) {}
    fn accepts_gated_phase_activation_params(_: GatedPhaseActivationParams<TestBackend>) {}
    fn accepts_attention_params(_: OscillatoryAttentionParams<TestBackend>) {}

    let _ = accepts_bands_params;
    let _ = accepts_layers_params;
    let _ = accepts_gated_phase_activation_params;
    let _ = accepts_attention_params;
}

#[test]
fn optimizers_are_nameable_and_usable_at_crate_root() {
    fn accepts_sync_gd(_: SyncGd<TestBackend, 1>) {}
    fn accepts_rip(_: Rip<TestBackend>) {}
    fn accepts_scalr(_: Scalr<TestBackend, 1>) {}
    fn accepts_feedback(_: StepFeedback<TestBackend>) {}
    fn accepts_order_parameter(_: OrderParameter) {}

    let sync_gd = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
    let rip = RipConfig::new(4).unwrap().init::<TestBackend>();
    let scalr = ScalrConfig::new().unwrap().init::<TestBackend, 1>();
    accepts_sync_gd(sync_gd);
    accepts_rip(rip);
    accepts_scalr(scalr);
    accepts_feedback(StepFeedback::none());
    accepts_order_parameter(OrderParameter::Global(0.5));

    // The trait itself must be reachable at the crate root too (it is what
    // callers need in scope to invoke `.step`/`.state_dict` generically).
    fn requires_trait<B: burn::tensor::backend::Backend, const D: usize, O>(_: &O)
    where
        O: OscillatorOptimizer<B, D>,
    {
    }
    let opt = SyncGdConfig::new().unwrap().init::<TestBackend, 1>();
    requires_trait::<TestBackend, 1, _>(&opt);
}

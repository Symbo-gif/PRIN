//! Property-based invariants for the subconscious controller primitives.
//!
//! Four families are covered:
//!
//! * **State packing** — shape, padding, and determinism hold for any finite
//!   telemetry, and the timestamp reduction always lands in `[0, 1)`.
//! * **Control decoding** — the documented clamps hold for every input, and
//!   `preferred_regime` always names a regime with a maximal weight.
//! * **Backend selection** — the choice is always available, the fallback
//!   ladder is strictly descending and CPU-terminated, and the whole function
//!   is a pure function of its inputs.
//! * **ONNX inspection robustness** — arbitrary byte strings either decode or
//!   produce a typed error; the reader never panics and never recurses without
//!   bound.

use proptest::prelude::*;

use prin_daemon::backend::{
    select_backend, Backend, SelectionReason, BACKEND_PRIORITY, PROVIDER_CPU, PROVIDER_DIRECTML,
    PROVIDER_VITISAI,
};
use prin_daemon::onnx::inspect_onnx_bytes;
use prin_daemon::state::{
    ControlSignals, Regime, SubconsciousState, ALERT_LEVEL_MAX, ALERT_LEVEL_MIN, CONTROL_DIM,
    LR_MULTIPLIER_MAX, LR_MULTIPLIER_MIN, STATE_DIM, STATE_PAYLOAD,
};

/// Finite `f64` telemetry values spanning several orders of magnitude.
fn finite() -> impl Strategy<Value = f64> {
    prop_oneof![
        -1e6..1e6_f64,
        -1.0..1.0_f64,
        (-1e-8..1e-8_f64),
        (-1e12..1e12_f64),
    ]
}

fn arb_regime() -> impl Strategy<Value = Regime> {
    prop_oneof![
        Just(Regime::MeanField),
        Just(Regime::SparseKnn),
        Just(Regime::Full),
    ]
}

prop_compose! {
    fn arb_state()(
        bands in prop::collection::vec(finite(), 0..6),
        r_global in finite(),
        loss_ema in finite(),
        loss_variance in finite(),
        grad_norm_ema in finite(),
        lr_current in finite(),
        scalr_alpha in finite(),
        gpu_temp in finite(),
        gpu_util in finite(),
        vram_pct in finite(),
        cpu_util in finite(),
        step_latency_p50 in finite(),
        step_latency_p95 in finite(),
        throughput in finite(),
        epoch in -1_000_000_i64..1_000_000,
        regime in arb_regime(),
        timestamp in -2e9..2e9_f64,
    ) -> SubconsciousState {
        SubconsciousState {
            r_per_band: bands,
            r_global,
            loss_ema,
            loss_variance,
            grad_norm_ema,
            lr_current,
            scalr_alpha,
            gpu_temp,
            gpu_util,
            vram_pct,
            cpu_util,
            step_latency_p50,
            step_latency_p95,
            throughput,
            epoch,
            regime,
            timestamp,
        }
    }
}

/// Every non-empty subset of the three supported providers, in ORT order.
fn arb_providers() -> impl Strategy<Value = Vec<String>> {
    prop::collection::vec(
        prop_oneof![
            Just(PROVIDER_VITISAI.to_string()),
            Just(PROVIDER_DIRECTML.to_string()),
            Just(PROVIDER_CPU.to_string()),
            Just("TensorrtExecutionProvider".to_string()),
        ],
        0..5,
    )
}

fn arb_requested() -> impl Strategy<Value = Option<Backend>> {
    prop_oneof![
        Just(None),
        Just(Some(Backend::Npu)),
        Just(Some(Backend::DirectMl)),
        Just(Some(Backend::Cpu)),
    ]
}

proptest! {
    #[test]
    fn state_packing_is_total_and_padding_stays_zero(state in arb_state()) {
        let packed = state.to_tensor().expect("finite telemetry packs");
        prop_assert_eq!(packed.len(), STATE_DIM);
        for value in &packed[STATE_PAYLOAD..] {
            prop_assert_eq!(*value, 0.0_f32);
        }
    }

    #[test]
    fn state_packing_is_deterministic(state in arb_state()) {
        let first = state.to_tensor().expect("packs");
        let second = state.clone().to_tensor().expect("packs");
        prop_assert_eq!(first, second);
    }

    #[test]
    fn timestamp_fraction_is_a_unit_interval_fraction(timestamp in -1e15..1e15_f64) {
        let state = SubconsciousState { timestamp, ..SubconsciousState::default() };
        let fraction = state.timestamp_fraction();
        prop_assert!((0.0..1.0).contains(&fraction), "fraction {} out of range", fraction);
    }

    #[test]
    fn control_decoding_respects_the_documented_clamps(
        raw in prop::array::uniform8(-1e6..1e6_f32)
    ) {
        let control = ControlSignals::from_tensor(&raw).expect("decodes");
        prop_assert!(control.lr_multiplier >= f64::from(LR_MULTIPLIER_MIN as f32));
        prop_assert!(control.lr_multiplier <= LR_MULTIPLIER_MAX);
        prop_assert!(control.alert_level >= ALERT_LEVEL_MIN);
        prop_assert!(control.alert_level <= ALERT_LEVEL_MAX);
        // Unclamped channels pass through as exact float32 widenings.
        prop_assert_eq!(control.suggested_k_min, f64::from(raw[0]));
        prop_assert_eq!(control.coupling_mode_suggestion, f64::from(raw[7]));
    }

    #[test]
    fn control_decoding_rejects_every_short_input(
        len in 0_usize..CONTROL_DIM
    ) {
        let raw = vec![0.0_f32; len];
        prop_assert!(ControlSignals::from_tensor(&raw).is_err());
    }

    #[test]
    fn preferred_regime_always_names_a_maximal_weight(
        mf in -10.0..10.0_f64,
        sk in -10.0..10.0_f64,
        full in -10.0..10.0_f64,
    ) {
        let control = ControlSignals {
            regime_mf_weight: mf,
            regime_sk_weight: sk,
            regime_full_weight: full,
            ..ControlSignals::default()
        };
        let best = control.preferred_regime();
        let weight = match best {
            Regime::MeanField => mf,
            Regime::SparseKnn => sk,
            Regime::Full => full,
        };
        prop_assert!(weight >= mf && weight >= sk && weight >= full);
    }

    #[test]
    fn control_signals_round_trip_through_float32(
        raw in prop::array::uniform8(-1e3..1e3_f32)
    ) {
        let control = ControlSignals::from_tensor(&raw).expect("decodes");
        let again = ControlSignals::from_tensor(&control.to_tensor()).expect("decodes");
        prop_assert_eq!(control, again);
    }

    #[test]
    fn backend_selection_is_pure_and_the_ladder_is_well_formed(
        providers in arb_providers(),
        requested in arb_requested(),
    ) {
        let first = select_backend(&providers, requested);
        let second = select_backend(&providers, requested);
        match (first, second) {
            (Ok(a), Ok(b)) => {
                // Purity: same inputs, same decision.
                prop_assert_eq!(&a, &b);

                // The chosen backend is one ONNX Runtime actually registered.
                prop_assert!(providers.iter().any(|p| p == a.backend.provider()));

                // The ladder starts at the choice, descends strictly, and
                // contains only available backends.
                prop_assert_eq!(a.attempt_order.first(), Some(&a.backend));
                for pair in a.attempt_order.windows(2) {
                    prop_assert!(pair[0].priority() < pair[1].priority());
                }
                for entry in &a.attempt_order {
                    prop_assert!(providers.iter().any(|p| p == entry.provider()));
                }

                // Whenever the CPU provider is registered the ladder ends there.
                if providers.iter().any(|p| p == PROVIDER_CPU) {
                    prop_assert_eq!(a.attempt_order.last(), Some(&Backend::Cpu));
                }

                // An honoured request is exactly the requested backend.
                if a.reason == SelectionReason::Requested {
                    prop_assert_eq!(Some(a.backend), requested);
                }

                // Without a request the choice is the highest-priority
                // available backend.
                if a.reason != SelectionReason::Requested {
                    let best = BACKEND_PRIORITY
                        .into_iter()
                        .find(|b| providers.iter().any(|p| p == b.provider()));
                    prop_assert_eq!(Some(a.backend), best);
                }
            }
            (Err(_), Err(_)) => {
                // Failure only when no supported provider is present.
                let any_supported = providers
                    .iter()
                    .any(|p| BACKEND_PRIORITY.into_iter().any(|b| b.provider() == p));
                prop_assert!(!any_supported);
            }
            _ => prop_assert!(false, "selection was not deterministic"),
        }
    }

    #[test]
    fn backend_names_round_trip(index in 0_usize..3) {
        let backend = BACKEND_PRIORITY[index];
        prop_assert_eq!(Backend::parse(backend.name()).expect("parses"), backend);
    }

    #[test]
    fn onnx_inspection_never_panics_on_arbitrary_bytes(
        bytes in prop::collection::vec(any::<u8>(), 0..512)
    ) {
        // Either a decode or a typed error — never a panic, hang, or overflow.
        let _ = inspect_onnx_bytes(&bytes);
    }

    #[test]
    fn onnx_inspection_never_panics_on_truncated_valid_prefixes(
        cut in 0_usize..64
    ) {
        // A well-formed header truncated at an arbitrary point.
        let full = [
            0x08, 0x0a, 0x12, 0x07, b'p', b'y', b't', b'o', b'r', b'c', b'h', 0x3a, 0x00,
        ];
        let end = cut.min(full.len());
        let _ = inspect_onnx_bytes(&full[..end]);
    }
}

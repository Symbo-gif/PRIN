//! Rust-vs-PRINet 3.0.0 parity for the subconscious controller I/O types.
//!
//! `SubconsciousState.to_tensor` and `ControlSignals.from_tensor` are pure
//! float32 packing/unpacking with no iterative numerics, so parity here is
//! asserted **bit-exactly**: every expected element is the exact IEEE-754
//! binary32 pattern produced by `prinet==3.0.0`, embedded as
//! `f32::from_bits`. There is no tolerance to register — a single ULP of
//! drift is a failure.
//!
//! Reference values were produced by an ad-hoc helper importing
//! `prinet.core.subconscious` from the archived
//! `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main` tree, and
//! are embedded here so the test needs neither a Python subprocess nor a
//! PyO3 bridge (same convention as
//! `crates/prin-dynamics/tests/parity_models.rs`).
//!
//! The cases deliberately exercise the reference's quirks: binary32 rounding
//! of `1e-3`/`1e-4`, Python's sign-of-divisor `%` on a negative timestamp,
//! an unrecognised regime name collapsing to index 0, a short `r_per_band`
//! list, NumPy's NEP 50 weak-scalar clipping of the learning-rate multiplier,
//! and insertion-order tie-breaking in `preferred_regime`.

use prin_daemon::state::{ControlSignals, Regime, SubconsciousState, CONTROL_DIM, STATE_DIM};

/// Assert bit-exact equality against the reference vector.
fn assert_bit_exact(actual: &[f32; STATE_DIM], expected: &[f32; STATE_DIM], case: &str) {
    for (index, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert_eq!(
            a.to_bits(),
            e.to_bits(),
            "case `{case}` element {index}: got {a:?} (0x{:08x}), expected {e:?} (0x{:08x})",
            a.to_bits(),
            e.to_bits()
        );
    }
}

#[test]
fn state_default_dataclass_matches_reference_bit_for_bit() {
    // prinet: SubconsciousState().to_tensor()
    let mut expected = [0.0_f32; STATE_DIM];
    expected[7] = f32::from_bits(0x3a83_126f); // lr_current 1e-3 in binary32
    expected[8] = f32::from_bits(0x3f80_0000); // scalr_alpha 1.0
    let actual = SubconsciousState::default().to_tensor().expect("packs");
    assert_bit_exact(&actual, &expected, "default_dataclass");
}

#[test]
fn state_realistic_telemetry_matches_reference_bit_for_bit() {
    // prinet: SubconsciousState(r_per_band=[0.8125, 0.640625, 0.421875],
    //   r_global=0.625, loss_ema=1.5, loss_variance=0.25, grad_norm_ema=3.5,
    //   lr_current=2e-4, scalr_alpha=1.25, gpu_temp=71.5, gpu_util=0.9,
    //   vram_pct=0.75, cpu_util=0.5, step_latency_p50=0.011,
    //   step_latency_p95=0.023, throughput=12500.0, epoch=250,
    //   regime="sparse_knn", timestamp=1_755_000_000.0).to_tensor()
    let mut expected = [0.0_f32; STATE_DIM];
    for (slot, bits) in expected.iter_mut().zip([
        0x3f50_0000_u32, // 0.8125
        0x3f24_0000,     // 0.640625
        0x3ed8_0000,     // 0.421875
        0x3f20_0000,     // 0.625
        0x3fc0_0000,     // 1.5
        0x3e80_0000,     // 0.25
        0x4060_0000,     // 3.5
        0x3951_b717,     // 2e-4
        0x3fa0_0000,     // 1.25
        0x3f37_0a3d,     // 71.5 / 100
        0x3f66_6666,     // 0.9
        0x3f40_0000,     // 0.75
        0x3f00_0000,     // 0.5
        0x3c34_3958,     // 0.011
        0x3cbc_6a7f,     // 0.023
        0x3fa0_0000,     // 12500 / 1e4
        0x3ccc_cccd,     // 250 / 1e4
        0x3f00_0000,     // regime index 1 / 2
        0x3f00_0000,     // 1_755_000_000 % 86400 / 86400
    ]) {
        *slot = f32::from_bits(bits);
    }

    let state = SubconsciousState {
        r_per_band: vec![0.8125, 0.640625, 0.421875],
        r_global: 0.625,
        loss_ema: 1.5,
        loss_variance: 0.25,
        grad_norm_ema: 3.5,
        lr_current: 2e-4,
        scalr_alpha: 1.25,
        gpu_temp: 71.5,
        gpu_util: 0.9,
        vram_pct: 0.75,
        cpu_util: 0.5,
        step_latency_p50: 0.011,
        step_latency_p95: 0.023,
        throughput: 12_500.0,
        epoch: 250,
        regime: Regime::SparseKnn,
        timestamp: 1_755_000_000.0,
    };
    assert_bit_exact(&state.to_tensor().expect("packs"), &expected, "realistic");
}

#[test]
fn state_irrational_values_and_negative_timestamp_match_reference_bit_for_bit() {
    // prinet: SubconsciousState(r_per_band=[0.1, 0.2, 0.3], r_global=1/3,
    //   loss_ema=0.123456789, loss_variance=1e-9, grad_norm_ema=1e9,
    //   lr_current=math.pi, scalr_alpha=math.e, gpu_temp=37.77,
    //   gpu_util=1/7, vram_pct=0.999999, cpu_util=1e-7,
    //   step_latency_p50=0.0009765625, step_latency_p95=1/6,
    //   throughput=98765.4321, epoch=123456, regime="full",
    //   timestamp=-1.0).to_tensor()
    let mut expected = [0.0_f32; STATE_DIM];
    for (slot, bits) in expected.iter_mut().zip([
        0x3dcc_cccd_u32, // 0.1
        0x3e4c_cccd,     // 0.2
        0x3e99_999a,     // 0.3
        0x3eaa_aaab,     // 1/3
        0x3dfc_d6ea,     // 0.123456789
        0x3089_705f,     // 1e-9
        0x4e6e_6b28,     // 1e9
        0x4049_0fdb,     // pi
        0x402d_f854,     // e
        0x3ec1_61e5,     // 37.77 / 100
        0x3e12_4925,     // 1/7
        0x3f7f_ffef,     // 0.999999
        0x33d6_bf95,     // 1e-7
        0x3a80_0000,     // 0.0009765625
        0x3e2a_aaab,     // 1/6
        0x411e_0652,     // 98765.4321 / 1e4
        0x4145_8794,     // 123456 / 1e4
        0x3f80_0000,     // regime index 2 / 2
        0x3f7f_ff3e,     // (-1 % 86400) / 86400 — Python modulo semantics
    ]) {
        *slot = f32::from_bits(bits);
    }

    let state = SubconsciousState {
        r_per_band: vec![0.1, 0.2, 0.3],
        r_global: 1.0 / 3.0,
        loss_ema: 0.123_456_789,
        loss_variance: 1e-9,
        grad_norm_ema: 1e9,
        lr_current: std::f64::consts::PI,
        scalr_alpha: std::f64::consts::E,
        gpu_temp: 37.77,
        gpu_util: 1.0 / 7.0,
        vram_pct: 0.999_999,
        cpu_util: 1e-7,
        step_latency_p50: 0.000_976_562_5,
        step_latency_p95: 1.0 / 6.0,
        throughput: 98_765.432_1,
        epoch: 123_456,
        regime: Regime::Full,
        timestamp: -1.0,
    };
    assert_bit_exact(&state.to_tensor().expect("packs"), &expected, "irrational");
}

#[test]
fn state_short_band_vector_and_unknown_regime_match_reference_bit_for_bit() {
    // prinet: SubconsciousState(r_per_band=[0.5], r_global=0.5,
    //   regime="chimera", timestamp=86399.5).to_tensor()
    // "chimera" is outside _REGIME_MAP, so the reference encodes index 0.
    let mut expected = [0.0_f32; STATE_DIM];
    expected[0] = f32::from_bits(0x3f00_0000); // 0.5
    expected[3] = f32::from_bits(0x3f00_0000); // 0.5
    expected[7] = f32::from_bits(0x3a83_126f); // lr_current default 1e-3
    expected[8] = f32::from_bits(0x3f80_0000); // scalr_alpha default 1.0
    expected[17] = 0.0; // unknown regime → index 0
    expected[18] = f32::from_bits(0x3f7f_ff9f); // 86399.5 / 86400

    let state = SubconsciousState {
        r_per_band: vec![0.5],
        r_global: 0.5,
        regime: Regime::from_name_or_default("chimera"),
        timestamp: 86_399.5,
        ..SubconsciousState::default()
    };
    assert_bit_exact(&state.to_tensor().expect("packs"), &expected, "short_bands");
}

/// Reference decode: `(input, expected fields, expected preferred regime)`.
struct ControlCase {
    name: &'static str,
    input: [f32; CONTROL_DIM],
    expected: [f64; CONTROL_DIM],
    preferred: Regime,
}

#[test]
fn control_decode_matches_reference_values_and_clamps() {
    let cases = [
        ControlCase {
            name: "identity",
            input: [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875],
            expected: [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875],
            preferred: Regime::Full,
        },
        ControlCase {
            name: "clipped_high",
            input: [0.25, 9.75, 42.0, 0.2, 0.3, 0.5, 7.5, -3.25],
            expected: [
                0.25,
                9.75,
                10.0,
                0.200_000_002_980_232_24,
                0.300_000_011_920_928_96,
                0.5,
                1.0,
                -3.25,
            ],
            preferred: Regime::Full,
        },
        ControlCase {
            name: "clipped_low",
            input: [-1.0, 0.0, -5.0, 0.1, 0.1, 0.8, -0.5, 2.0],
            expected: [
                -1.0,
                0.0,
                // NumPy clips in binary32: float(np.float32(0.1)).
                0.100_000_001_490_116_12,
                0.100_000_001_490_116_12,
                0.100_000_001_490_116_12,
                0.800_000_011_920_929,
                0.0,
                2.0,
            ],
            preferred: Regime::Full,
        },
        ControlCase {
            name: "irrational",
            input: [
                0.1,
                3.3,
                0.9999,
                1.0 / 3.0,
                1.0 / 3.0,
                1.0 / 3.0,
                0.6666666,
                1e-8,
            ],
            expected: [
                0.100_000_001_490_116_12,
                3.299_999_952_316_284,
                0.999_899_983_406_066_9,
                0.333_333_343_267_440_8,
                0.333_333_343_267_440_8,
                0.333_333_343_267_440_8,
                0.666_666_626_930_236_8,
                9.999_999_939_225_29e-9,
            ],
            // Three-way tie resolves to the first key of the reference dict.
            preferred: Regime::MeanField,
        },
    ];

    for case in cases {
        let decoded = ControlSignals::from_tensor(&case.input).expect("decodes");
        let actual = [
            decoded.suggested_k_min,
            decoded.suggested_k_max,
            decoded.lr_multiplier,
            decoded.regime_mf_weight,
            decoded.regime_sk_weight,
            decoded.regime_full_weight,
            decoded.alert_level,
            decoded.coupling_mode_suggestion,
        ];
        for (index, (a, e)) in actual.iter().zip(case.expected.iter()).enumerate() {
            assert_eq!(
                a.to_bits(),
                e.to_bits(),
                "case `{}` field {index}: got {a:?}, expected {e:?}",
                case.name
            );
        }
        assert_eq!(
            decoded.preferred_regime(),
            case.preferred,
            "case `{}` preferred regime",
            case.name
        );
    }
}

#[test]
fn control_defaults_match_the_reference_dataclass() {
    // prinet: ControlSignals().to_tensor()
    let expected = [0.5_f32, 5.0, 1.0, 0.33, 0.33, 0.34, 0.0, 0.0];
    let actual = ControlSignals::default().to_tensor();
    for (index, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert_eq!(a.to_bits(), e.to_bits(), "default field {index}");
    }
    // The reference's default weights make `full` the preferred regime.
    assert_eq!(ControlSignals::default().preferred_regime(), Regime::Full);
}

#[test]
fn regime_indices_match_the_reference_map() {
    // prinet: _REGIME_MAP = {"mean_field": 0, "sparse_knn": 1, "full": 2}
    assert_eq!(Regime::from_name("mean_field").map(Regime::index), Some(0));
    assert_eq!(Regime::from_name("sparse_knn").map(Regime::index), Some(1));
    assert_eq!(Regime::from_name("full").map(Regime::index), Some(2));
    assert_eq!(Regime::from_name_or_default("").index(), 0);
}

#[test]
fn dimensions_match_the_reference_constants() {
    // prinet: STATE_DIM = 32, CONTROL_DIM = 8
    assert_eq!(STATE_DIM, 32);
    assert_eq!(CONTROL_DIM, 8);
}

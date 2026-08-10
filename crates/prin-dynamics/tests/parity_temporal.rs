//! Rust-vs-PRINet 3.0.0 parity tests for temporal propagation.
//!
//! WP-013 acceptance requires temporal golden trajectories and phase-continuity
//! guards. These tests compare [`TemporalPropagator`], [`ComplexPhasorBlender`],
//! and [`EmaAmplitudeBlender`] against hard-coded reference values produced by
//! `prinet==3.0.0`'s `TemporalPhasePropagator.propagate`
//! (`torch==2.13.0+cpu`, `dtype=torch.float64`) and embedded here.
//!
//! # Parameter mapping (WP013-F6)
//!
//! PRINet weights the *carried* frame, PRIN weights the *new* frame:
//!
//! ```text
//! ComplexPhasorBlender::alpha = 1 − TemporalPhasePropagator.carry_strength
//! EmaAmplitudeBlender::alpha  = 1 − TemporalPhasePropagator.amplitude_decay
//! ```
//!
//! The references below were generated with `carry_strength = 0.2` and
//! `amplitude_decay = 0.3`, so the propagator under test uses
//! `phase_alpha = 0.8` and `amplitude_alpha = 0.7`. Passing these tests *is*
//! the verification of that mapping: the complementary parameter is the only
//! one that reproduces the reference values.
//!
//! # Tolerances
//!
//! PRINet's phase blend runs in `torch.float64` (`prev_phase.to(torch.float64)`)
//! and its amplitude blend in the input dtype, so both sides are fully f64
//! here — no `complex64` hazard applies. Comparisons use `rtol=1e-12,
//! atol=1e-12`; measured worst-case drift is ~1 ulp.
//!
//! Phases are compared as points on the circle (shortest signed distance
//! modulo 2π): `0` and `2π` are the same phase, and near-cancelling phasor
//! blends can land on either side of the wrap point.
//!
//! Reference generation: `DOCS/test_and_benchmark_results/`
//! `wp013_generate_prinet_references.py` (ad-hoc, gitignored, WP-009/WP-010
//! precedent).

use prin_dynamics::state::TAU;
use prin_dynamics::{ComplexPhasorBlender, EmaAmplitudeBlender, TemporalPropagator};

const RTOL: f64 = 1e-12;
const ATOL: f64 = 1e-12;

/// PRINet `carry_strength` used to generate the references.
const CARRY_STRENGTH: f64 = 0.2;
/// PRINet `amplitude_decay` used to generate the references.
const AMPLITUDE_DECAY: f64 = 0.3;

fn phase_alpha() -> f64 {
    1.0 - CARRY_STRENGTH
}

fn amplitude_alpha() -> f64 {
    1.0 - AMPLITUDE_DECAY
}

fn assert_close(actual: &[f64], expected: &[f64]) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert!(
            (a - e).abs() <= ATOL || (a - e).abs() <= RTOL * e.abs(),
            "index {i}: actual {a:.17e} vs expected {e:.17e}"
        );
    }
}

/// Compare phases on the circle: `|a − e|` reduced modulo `2π` to `[0, π]`.
fn assert_phases_close(actual: &[f64], expected: &[f64]) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        let raw = (a - e).abs() % TAU;
        let circular = raw.min(TAU - raw);
        assert!(
            circular <= ATOL,
            "index {i}: actual {a:.17e} vs expected {e:.17e} (circular {circular:.3e})"
        );
    }
}

// ------------------------------------------------------------------
// Fixtures — identical to the reference generator
// ------------------------------------------------------------------

const PREV_PHASE: [f64; 4] = [0.10, 1.90, 3.40, 6.10];
const PREV_AMP: [f64; 4] = [1.00, 2.50, 0.40, 1.75];
const INPUT_PHASE: [f64; 4] = [0.90, 2.60, 5.90, 0.05];
const INPUT_AMP: [f64; 4] = [2.00, 1.00, 0.90, 3.20];

// ==================================================================
// 1. Single blend
// ==================================================================

#[test]
fn parity_single_blend_matches_prinet_propagate() {
    let phase_blender = ComplexPhasorBlender::new(phase_alpha()).unwrap();
    let amp_blender = EmaAmplitudeBlender::new(amplitude_alpha()).unwrap();

    // PRIN's "new" frame is PRINet's "input" frame; PRIN's "old" frame is
    // PRINet's "prev" frame.
    let blended_phase = phase_blender.blend(&INPUT_PHASE, &PREV_PHASE).unwrap();
    let blended_amp = amp_blender.blend(&INPUT_AMP, &PREV_AMP).unwrap();

    let expected_phase = [
        0.7484353595573168,
        2.4656125850362054,
        5.7150487277994655,
        0.0035663191018894297,
    ];
    let expected_amplitude = [1.7, 1.45, 0.75, 2.7649999999999997];

    assert_phases_close(&blended_phase, &expected_phase);
    assert_close(&blended_amp, &expected_amplitude);
}

#[test]
fn parity_propagator_reproduces_prinet_single_blend() {
    let mut prop =
        TemporalPropagator::with_separate_alpha(phase_alpha(), amplitude_alpha()).unwrap();
    // The running state plays the role of PRINet's `prev_*` frame.
    prop.propagate_init(&PREV_PHASE, &PREV_AMP).unwrap();
    let (phase, amp) = prop.propagate(&INPUT_PHASE, &INPUT_AMP).unwrap();

    let expected_phase = [
        0.7484353595573168,
        2.4656125850362054,
        5.7150487277994655,
        0.0035663191018894297,
    ];
    let expected_amplitude = [1.7, 1.45, 0.75, 2.7649999999999997];

    assert_phases_close(&phase, &expected_phase);
    assert_close(&amp, &expected_amplitude);
}

// ==================================================================
// 2. Golden 5-frame sequence
// ==================================================================

#[test]
fn parity_golden_five_frame_sequence() {
    // Each frame rotates the input phase by 0.7 rad and scales the input
    // amplitude by 1.1, chaining the blended output as the next carry frame —
    // exactly the loop the reference generator ran through PRINet.
    let mut prop =
        TemporalPropagator::with_separate_alpha(phase_alpha(), amplitude_alpha()).unwrap();
    prop.propagate_init(&PREV_PHASE, &PREV_AMP).unwrap();

    let expected_phase: [[f64; 4]; 5] = [
        [
            0.7484353595573168,
            2.4656125850362054,
            5.7150487277994655,
            0.0035663191018894297,
        ],
        [
            1.439900342646065,
            3.142717515459853,
            0.15131683064291074,
            0.6075393430279942,
        ],
        [
            2.1385104920277973,
            3.8389685052976787,
            0.8544495948648255,
            1.2913901498832612,
        ],
        [
            2.83828480055896,
            4.53835915555556,
            1.554957401851444,
            1.9887526125737625,
        ],
        [
            3.5382481683728093,
            5.238260236480101,
            2.255039800601234,
            2.6883241045903166,
        ],
    ];
    let expected_amplitude: [[f64; 4]; 5] = [
        [1.7, 1.45, 0.75, 2.7649999999999997],
        [2.05, 1.205, 0.918, 3.2935],
        [2.309, 1.2085000000000001, 1.0377, 3.6984500000000002],
        [
            2.5561000000000003,
            1.2942500000000003,
            1.1498400000000002,
            4.090975,
        ],
        [
            2.816570000000001,
            1.4131450000000005,
            1.2673350000000003,
            4.506876500000001,
        ],
    ];

    let mut input_phase = INPUT_PHASE.to_vec();
    let mut input_amp = INPUT_AMP.to_vec();

    for frame in 0..5 {
        let (phase, amp) = prop.propagate(&input_phase, &input_amp).unwrap();
        assert_phases_close(&phase, &expected_phase[frame]);
        assert_close(&amp, &expected_amplitude[frame]);

        for p in input_phase.iter_mut() {
            *p = prin_dynamics::state::wrap_phase(*p + 0.7);
        }
        for a in input_amp.iter_mut() {
            *a = (*a * 1.1).clamp(1e-6, 10.0);
        }
    }
}

// ==================================================================
// 3. Wrap-around and clamp behaviour
// ==================================================================

#[test]
fn parity_wrap_around_blend_matches_prinet() {
    // carry_strength = 0.5 → alpha = 0.5. Phases straddling the 0 / 2π seam.
    let blender = ComplexPhasorBlender::new(0.5).unwrap();
    let prev = [TAU - 0.1, 0.05, 3.0];
    let input = [0.1, TAU - 0.05, 3.2];
    let blended = blender.blend(&input, &prev).unwrap();

    // PRINet returned [5.57898681919053e-17, 6.283185307179586, 3.1]; the
    // second value is 2π, i.e. the same point on the circle as the first.
    let expected_phase = [5.57898681919053e-17, TAU, 3.1];
    assert_phases_close(&blended, &expected_phase);

    // The circular mean of ±0.1 about the seam is 0 (mod 2π), not π.
    for &b in &blended[..2] {
        let d = b.min(TAU - b);
        assert!(
            d < 1e-12,
            "wrap-around blend landed at {b}, not on the seam"
        );
    }
}

#[test]
fn parity_amplitude_clamp_matches_prinet() {
    // amplitude_decay = 0.5 → alpha = 0.5. Both sides clamp to [1e-6, 10].
    let blender = EmaAmplitudeBlender::new(0.5).unwrap();
    let prev = [9.0, 1e-6];
    let input = [20.0, 1e-9];
    let blended = blender.blend(&input, &prev).unwrap();

    // 0.5·20 + 0.5·9 = 14.5 → 10.0; 0.5·1e-9 + 0.5·1e-6 ≈ 5.005e-7 → 1e-6.
    let expected_amplitude = [10.0, 1e-06];
    assert_close(&blended, &expected_amplitude);
}

// ==================================================================
// 4. The mapping is directional
// ==================================================================

#[test]
fn parity_reversed_convention_does_not_match() {
    // Guards WP013-F6: using PRINet's carry_strength directly as PRIN's alpha
    // (instead of its complement) must not reproduce the reference.
    let wrong = ComplexPhasorBlender::new(CARRY_STRENGTH).unwrap();
    let blended = wrong.blend(&INPUT_PHASE, &PREV_PHASE).unwrap();
    let expected_phase = [
        0.7484353595573168,
        2.4656125850362054,
        5.7150487277994655,
        0.0035663191018894297,
    ];
    let matches = blended
        .iter()
        .zip(expected_phase.iter())
        .all(|(a, e)| (a - e).abs() < 1e-6);
    assert!(
        !matches,
        "alpha = carry_strength reproduced the reference; the documented \
         alpha = 1 − carry_strength mapping would then be ambiguous"
    );
}

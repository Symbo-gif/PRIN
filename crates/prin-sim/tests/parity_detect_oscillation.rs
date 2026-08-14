//! Parity test: `prin_sim::sweep::detect_oscillation` vs the archived
//! PRINet 3.0 `core/propagation/sweep_utils.py::detect_oscillation`.
//!
//! `reference_detect_oscillation` below is a line-by-line Rust transcription
//! of the archived Python function (`DOCS/archive and reference from
//! PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/sweep_utils.py`,
//! lines 20-48), used only as the parity oracle for this test — it is not
//! imported or built by PRIN (WP016-F3).

use prin_sim::sweep::detect_oscillation;

/// Rust transcription of the archived PRINet 3.0 `detect_oscillation`.
///
/// ```python
/// def detect_oscillation(r_history, window=20, threshold=0.01):
///     if len(r_history) < window:
///         return False
///     recent = r_history[-window:]
///     mean = sum(recent) / len(recent)
///     var = sum((v - mean) ** 2 for v in recent) / len(recent)
///     return var > threshold
/// ```
///
/// `window == 0` is excluded from the parity comparison below: Python's
/// `r_history[-0:]` slices the *entire* list (since `-0 == 0`), which is a
/// well-known slicing footgun rather than intentional behaviour, and no call
/// site anywhere in PRIN or PRINet 3.0 invokes `detect_oscillation` with
/// `window = 0`. The Rust production implementation intentionally returns
/// `false` for `window == 0` instead of reproducing the footgun.
fn reference_detect_oscillation(r_history: &[f64], window: usize, threshold: f64) -> bool {
    if r_history.len() < window {
        return false;
    }
    let start = if window == 0 {
        0
    } else {
        r_history.len() - window
    };
    let recent = &r_history[start..];
    let mean: f64 = recent.iter().sum::<f64>() / recent.len() as f64;
    let var: f64 = recent.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / recent.len() as f64;
    var > threshold
}

/// The PRINet 3.0 docstring example: `detect_oscillation([0.8, 0.2, 0.9,
/// 0.1] * 5, window=10)` is `True`.
#[test]
fn matches_prinet_docstring_example() {
    let history: Vec<f64> = [0.8, 0.2, 0.9, 0.1]
        .iter()
        .cycle()
        .take(20)
        .copied()
        .collect();
    assert!(reference_detect_oscillation(&history, 10, 0.01));
    assert_eq!(
        detect_oscillation(&history, 10, 0.01),
        reference_detect_oscillation(&history, 10, 0.01)
    );
}

#[test]
fn matches_reference_on_stable_history() {
    let history = vec![0.8_f64; 30];
    assert_eq!(
        detect_oscillation(&history, 20, 0.01),
        reference_detect_oscillation(&history, 20, 0.01)
    );
    assert!(!detect_oscillation(&history, 20, 0.01));
}

#[test]
fn matches_reference_on_oscillating_history() {
    let history: Vec<f64> = (0..30).map(|i| (i as f64 * 0.5).sin()).collect();
    assert_eq!(
        detect_oscillation(&history, 20, 0.01),
        reference_detect_oscillation(&history, 20, 0.01)
    );
    assert!(detect_oscillation(&history, 20, 0.01));
}

#[test]
fn matches_reference_on_short_history() {
    let history = vec![0.5, 0.6, 0.7];
    assert_eq!(
        detect_oscillation(&history, 20, 0.01),
        reference_detect_oscillation(&history, 20, 0.01)
    );
}

#[test]
fn matches_reference_on_empty_history() {
    let history: Vec<f64> = vec![];
    assert_eq!(
        detect_oscillation(&history, 20, 0.01),
        reference_detect_oscillation(&history, 20, 0.01)
    );
}

#[test]
fn matches_reference_exact_window_boundary() {
    let history: Vec<f64> = (0..20).map(|i| i as f64 * 0.01).collect();
    assert_eq!(history.len(), 20);
    assert_eq!(
        detect_oscillation(&history, 20, 1e-6),
        reference_detect_oscillation(&history, 20, 1e-6)
    );
}

/// Sweep a broad grid of window sizes, thresholds, and history shapes
/// (excluding `window == 0`, see module docs) and assert byte-identical
/// Boolean output between the Rust production implementation and the
/// PRINet 3.0 reference transcription.
#[test]
fn matches_reference_across_grid() {
    let histories: Vec<Vec<f64>> = vec![
        vec![],
        vec![1.0],
        vec![0.5; 5],
        (0..15).map(|i| i as f64 * 0.1).collect(),
        (0..50)
            .map(|i| (i as f64 * 0.3).sin() * 0.5 + 0.5)
            .collect(),
        (0..100)
            .map(|i| if i % 2 == 0 { 0.9 } else { 0.1 })
            .collect(),
        vec![0.0; 40],
        (0..40).map(|i| 1.0 - (i as f64) * 1e-6).collect(),
    ];
    let windows = [1usize, 2, 5, 10, 20, 30, 50, 100];
    let thresholds = [0.0_f64, 1e-6, 0.001, 0.01, 0.1, 1.0];

    for history in &histories {
        for &window in &windows {
            for &threshold in &thresholds {
                assert_eq!(
                    detect_oscillation(history, window, threshold),
                    reference_detect_oscillation(history, window, threshold),
                    "mismatch for history len={}, window={window}, threshold={threshold}",
                    history.len()
                );
            }
        }
    }
}

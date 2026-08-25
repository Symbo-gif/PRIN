//! Integration test: [`TrainingHooks`] wired end-to-end into a running
//! [`SubconsciousDaemon`].
//!
//! Unit tests in `src/hooks.rs` cover the EMA/percentile math in isolation
//! (no thread spawning); this test proves the other half of "daemon
//! integration" — that a [`SubconsciousState`] built by
//! [`TrainingHooks::on_epoch_end`] survives
//! [`SubconsciousDaemon::submit_state`], gets packed and run through an
//! [`InferenceBackend`], and the resulting [`ControlSignals`] come back out
//! through [`SubconsciousDaemon::get_control`] — the same "exactly two
//! non-blocking calls" integration surface `daemon.rs`'s own module docs
//! describe.

use std::time::{Duration, Instant};

use prin_daemon::daemon::{DaemonConfig, SubconsciousDaemon};
use prin_daemon::hooks::TrainingHooks;
use prin_daemon::state::{Regime, CONTROL_DIM, STATE_DIM};

fn wait_for<F: Fn() -> bool>(condition: F, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while !condition() && Instant::now() < deadline {
        std::thread::sleep(Duration::from_millis(5));
    }
    condition()
}

#[test]
fn training_hooks_state_flows_through_the_daemon_to_a_control_signal() {
    let mut hooks = TrainingHooks::new(0.1, 50).expect("valid hook config");

    for step in 0..10u64 {
        hooks.on_step_end_with_elapsed(
            Duration::from_millis(step + 1),
            1.0 / (step as f64 + 1.0),
            Some(&[1.0, 2.0, 0.5]),
        );
    }
    let state = hooks.on_epoch_end(
        1,
        None,
        vec![0.8, 0.6, 0.4],
        None,
        1e-3,
        1.0,
        Regime::SparseKnn,
        0.0,
    );
    assert!(state.step_latency_p50 > 0.0);
    assert!(state.grad_norm_ema > 0.0);

    let config = DaemonConfig {
        interval: Duration::from_millis(10),
        warmup: false,
        ..DaemonConfig::default()
    };
    // A trivial backend that reflects the state's r_global into every
    // control-signal element, so the assertion below can prove this
    // specific submission was the one processed, not just "some" submission.
    let backend = Box::new(|input: &[f32; STATE_DIM]| {
        let r_global = input[3];
        Ok::<_, prin_daemon::DaemonError>([r_global; CONTROL_DIM])
    });
    let mut daemon =
        SubconsciousDaemon::spawn(backend, config, None).expect("daemon thread spawns");

    let expected_r_global = state.r_global;
    daemon.submit_state(state);

    let processed = wait_for(|| daemon.inference_count() >= 1, Duration::from_secs(2));
    assert!(processed, "daemon never processed the submitted state");

    let control = daemon.get_control();
    assert!(
        (control.suggested_k_min - expected_r_global).abs() < 1e-6,
        "control signal does not reflect the submitted state's r_global"
    );

    assert!(daemon.stop(Duration::from_secs(2)));
}

#[test]
fn hooks_built_state_is_rejected_under_strict_checks_when_loss_is_non_finite() {
    // Cross-check that TrainingHooks composes correctly with the existing
    // strict-checks finiteness guard on `SubconsciousState::to_tensor`
    // (Coding Standards §2.2) rather than duplicating that validation.
    let mut hooks = TrainingHooks::new(0.1, 10).expect("valid hook config");
    let state = hooks.on_epoch_end(
        0,
        Some(f64::NAN),
        vec![0.5],
        None,
        1e-3,
        1.0,
        Regime::MeanField,
        0.0,
    );
    assert!(state.loss_ema.is_nan());

    #[cfg(feature = "strict-checks")]
    {
        let err = state.to_tensor().expect_err("strict-checks rejects NaN");
        assert!(matches!(
            err,
            prin_daemon::DaemonError::NonFiniteValue {
                name: "loss_ema",
                ..
            }
        ));
    }
    #[cfg(not(feature = "strict-checks"))]
    {
        let packed = state.to_tensor().expect("packs without strict-checks");
        assert!(packed[4].is_nan()); // loss_ema slot
    }
}

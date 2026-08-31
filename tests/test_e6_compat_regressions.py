"""Focused regressions for 0144E6 subconscious compatibility behavior.

These cover the defensive / non-happy-path branches of
``prin.subconscious_compat`` and ``prin.training_hooks.collect_system_state``
that the strict-ported ``test_acceptance_subconscious`` suite exercises only
indirectly, so the changed surface stays reviewable while the host's
coverage instrumentation is unavailable (see the 0144E handoff).
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from prin.subconscious_compat import (
    ControlSignals,
    SubconsciousDaemon,
    SubconsciousState,
    backend_info,
    collect_system_state,
    detect_best_backend,
)


def test_control_signals_wrapper_is_read_only() -> None:
    """Assigning to a wrapped ``ControlSignals`` field raises, matching Rust."""
    ctrl = ControlSignals(alert_level=0.5)
    with pytest.raises(AttributeError):
        ctrl.alert_level = 0.9  # type: ignore[misc]
    assert "alert_level" in repr(ctrl)


def test_subconscious_state_wrapper_setattr_delegates() -> None:
    """Wrapper attribute writes reach the Rust owner's setters."""
    state = SubconsciousState()
    state.epoch = 7  # type: ignore[misc]
    state.regime = "full"  # type: ignore[misc]
    assert state.epoch == 7
    assert state.regime == "full"
    assert "epoch=7" in repr(state)


def test_subconscious_state_missing_core_raises_attributeerror() -> None:
    """The ``__getattr__`` guard avoids infinite recursion before init."""
    bare = SubconsciousState.__new__(SubconsciousState)
    with pytest.raises(AttributeError):
        _ = bare.epoch


def test_control_signals_from_tensor_accepts_any_float_dtype() -> None:
    """``from_tensor`` ravels and casts, so float32 / 2-D / lists all decode."""
    row = ControlSignals.from_tensor([0.5, 5.0, 1.0, 0.3, 0.3, 0.4, 0.1, 0.0])
    assert row.is_finite()
    two_d = ControlSignals.from_tensor(np.zeros((1, 8), dtype=np.float32))
    assert two_d.lr_multiplier == pytest.approx(0.1)  # np.clip lower bound


def test_collect_system_state_explicit_args_roundtrip() -> None:
    """Explicit telemetry args are stored verbatim; the vector packs finite."""
    state = collect_system_state(
        r_per_band=[0.2, 0.3, 0.4],
        r_global=0.3,
        loss_ema=1.0,
        epoch=9,
        regime="sparse_knn",
    )
    assert state.r_per_band == [0.2, 0.3, 0.4]
    assert state.epoch == 9
    assert state.regime == "sparse_knn"
    assert state.timestamp <= time.time()
    z = state.to_tensor()
    assert z.shape == (32,)
    assert np.all(np.isfinite(z))


def test_backend_probes_agree_with_daemon_layer() -> None:
    """The npu_backend-shaped probes reduce to the Rust-backed daemon probe."""
    assert detect_best_backend() in {"npu", "directml", "cpu"}
    info = backend_info()
    assert set(info) >= {
        "ort_available",
        "available_eps",
        "best_backend",
        "npu_firmware_found",
    }
    assert isinstance(info["available_eps"], list)


def test_daemon_aborts_cleanly_on_unloadable_model(tmp_path: object) -> None:
    """A present-but-invalid model file makes ``run`` abort without inferences."""
    bad = tmp_path / "not-a-model.onnx"  # type: ignore[operator]
    bad.write_bytes(b"not onnx")
    daemon = SubconsciousDaemon(bad, backend="cpu", interval=0.1, warmup=False)
    daemon.start()
    daemon.submit_state(SubconsciousState.default())
    time.sleep(0.5)
    daemon.stop(timeout=3.0)
    assert not daemon.is_alive()
    assert daemon.inference_count == 0

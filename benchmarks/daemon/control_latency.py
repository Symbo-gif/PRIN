"""`SubconsciousDaemon.get_control()` read latency (p50/p95) via the native
Python binding.

Rust-backed successor to PRINet 3.0's `subconscious_benchmark.py`. Complements
the pure-Rust pilot in `EVIDENCE/0125-wp032-s1-daemon-latency.json`
(`crates/prin-daemon/examples/control_buffer_pilot.rs`) by measuring the same
lock-free control buffer through the Python call boundary applications
actually use.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from prin.daemon import CONTROL_DIM, SubconsciousDaemon, SubconsciousState

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_INTERVAL_MS = 5
_DEFAULT_WAIT_TIMEOUT_S = 2.0


def _identity_callback(packed: np.ndarray) -> np.ndarray:
    """Trivial CPU callback: no ONNX inference, just satisfies the daemon contract."""
    return np.zeros(CONTROL_DIM, dtype=np.float32)


def _wait_for_inference(daemon: SubconsciousDaemon, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while daemon.inference_count == 0 and time.monotonic() < deadline:
        time.sleep(0.005)


@register(
    "daemon",
    "control_latency",
    summary="SubconsciousDaemon.get_control() read latency (p50/p95), Python binding",
)
def daemon_control_latency(config: BenchmarkConfig) -> dict[str, Any]:
    """Measure ``get_control()`` latency after one warmed-up inference.

    ``config.params`` may override ``interval_ms`` and ``wait_timeout_s``.
    """
    interval_ms = int(config.params.get("interval_ms", _DEFAULT_INTERVAL_MS))
    wait_timeout_s = float(config.params.get("wait_timeout_s", _DEFAULT_WAIT_TIMEOUT_S))

    daemon = SubconsciousDaemon(
        _identity_callback, interval_ms=interval_ms, warmup=False
    )
    try:
        daemon.submit_state(SubconsciousState())
        _wait_for_inference(daemon, wait_timeout_s)
        if daemon.inference_count == 0:
            raise RuntimeError(
                f"no inference completed within {wait_timeout_s}s "
                f"(interval_ms={interval_ms}); daemon.error_count={daemon.error_count}"
            )

        stats, _ = timed_run(
            daemon.get_control, iterations=config.iterations, warmup=config.warmup
        )
    finally:
        daemon.stop(timeout_ms=2_000)

    return {
        "benchmark": "daemon_control_latency",
        "backend": "host CPU",
        "dtype": "ControlSignals fields are f64; timing samples are seconds",
        "interval_ms": interval_ms,
        "p50_s": stats.median_s,
        "p95_s": stats.p95_s,
        "max_s": stats.max_s,
        "timing": stats.to_dict(),
    }

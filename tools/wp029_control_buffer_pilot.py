"""WP-029 S1 latency pilot: PRINet 3.0's `ControlSignalBuffer` under contention.

Measures p50/p95/max read latency of the archived PRINet 3.0
``prinet.core.subconscious.ControlSignalBuffer`` (a single ``threading.Lock``
guarding both ``update`` and ``latest``) under concurrent writer contention,
using the same protocol as
``crates/prin-daemon/examples/control_buffer_pilot.rs`` (writer thread count,
reads-per-trial, and steady-state warm-up delay), so the two numbers are a
genuine cross-language "before" data point for the WP-029 acceptance
criterion ("p50/p95 instrumentation is valid and latency pilot improves on
3.0") and Benchmarking Standards §2.4's tracked "Daemon latency: lower p95
than 3.0" target.

This is a pilot, not a scientific benchmark (Development Workflow Standards
§3, S1 exit criteria: "no scientific conclusion claims from pilots"): one
process, one host, wall-clock timing via :func:`time.perf_counter_ns`.

Usage:
    python tools/wp029_control_buffer_pilot.py
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import threading
import time
from pathlib import Path
from typing import Any

# The archived PRINet 3.0 reference is installed editable in the project
# venv (see `pyproject.toml`'s dev extras / parity job setup); this pilot
# measures that installation directly rather than a reimplementation.
from prinet.core.subconscious import ControlSignalBuffer, ControlSignals

_DEFAULT_OUTPUT = Path("EVIDENCE") / "0113-wp029-s1-control-buffer-pilot.json"
_WRITER_THREADS = 4
_READS_PER_TRIAL = 20_000
_WARMUP_SECONDS = 0.05


def _percentile(sorted_samples: list[int], pct: float) -> int:
    """Nearest-rank percentile over already-sorted nanosecond samples.

    Args:
        sorted_samples: Latency samples in nanoseconds, ascending.
        pct: Percentile in ``[0, 1]``.

    Returns:
        The sample at the nearest rank, or ``0`` for an empty input.
    """
    if not sorted_samples:
        return 0
    rank = round((len(sorted_samples) - 1) * pct)
    return sorted_samples[min(rank, len(sorted_samples) - 1)]


def measure_reference_control_signal_buffer() -> dict[str, int]:
    """Measure PRINet 3.0's ``ControlSignalBuffer.latest()`` under contention.

    Spawns :data:`_WRITER_THREADS` background writers continuously calling
    ``update``, then takes :data:`_READS_PER_TRIAL` timed ``latest()`` calls
    on the main thread once the writers have reached steady state.

    Returns:
        ``{"p50_ns", "p95_ns", "max_ns"}`` over the observed read latencies.
    """
    buffer = ControlSignalBuffer()
    stop = threading.Event()

    def _writer(index: int) -> None:
        """Continuously publish updates until `stop` is set."""
        n = 0.0
        while not stop.is_set():
            n = (n + 1.0) % 1000.0
            buffer.update(
                ControlSignals(alert_level=n, coupling_mode_suggestion=float(index))
            )

    writers = [
        threading.Thread(target=_writer, args=(i,), daemon=True)
        for i in range(_WRITER_THREADS)
    ]
    for writer in writers:
        writer.start()

    time.sleep(_WARMUP_SECONDS)

    samples: list[int] = []
    for _ in range(_READS_PER_TRIAL):
        start = time.perf_counter_ns()
        _ = buffer.latest()
        samples.append(time.perf_counter_ns() - start)

    stop.set()
    for writer in writers:
        writer.join(timeout=2.0)

    samples.sort()
    return {
        "p50_ns": _percentile(samples, 0.50),
        "p95_ns": _percentile(samples, 0.95),
        "max_ns": samples[-1],
    }


def _environment() -> dict[str, Any]:
    """Capture the environment fields Benchmarking Standards §1 requires."""
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the pilot and write the evidence JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Path where the evidence JSON will be written.",
    )
    args = parser.parse_args(argv)

    result = {
        "pilot": "wp029-s1-control-buffer",
        "protocol": {
            "writer_threads": _WRITER_THREADS,
            "reads_per_trial": _READS_PER_TRIAL,
            "warmup_seconds": _WARMUP_SECONDS,
        },
        "environment": _environment(),
        "prinet_3_0_reference": measure_reference_control_signal_buffer(),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"Evidence written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

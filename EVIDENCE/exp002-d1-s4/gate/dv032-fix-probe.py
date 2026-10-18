"""Evidence probe for DV-032's owed fix: choose a contention-robust metric.

The registered fix path is "convert each to a seeded frame-count /
pytest-benchmark case with an explicit tolerance".  Testing Standards section 7
item 2 requires a finite bound to be sized from cited evidence, so this probe
MEASURES candidate metrics rather than assuming one is robust, and checks each
for non-vacuity with a negative control.

Candidate metrics for "the daemon should not significantly affect CPU-bound work":

  wall_block   the CURRENT design: a baseline block, then a daemon block, medians
               compared.  Expected to be load-sensitive (the observed defect).
  wall_paired  baseline and daemon samples interleaved pair-by-pair, median of
               per-pair ratios.  Both arms see the same instantaneous load.
  process      time.process_time() -- documented as excluding time spent waiting
               for other processes, so expected immune to external contention.
  thread       time.thread_time() -- the calling thread only, so also excludes
               the daemon's own threads.  Expected immune but possibly VACUOUS.

Each is measured under two host conditions (quiet, and loaded with one busy
process per logical CPU) and against three daemon arms:

  baseline  no daemon at all
  idle      daemon running, no states submitted during the window (what the
            current test actually measures -- the daemon blocks on its queue)
  heavy     daemon running AND fed a state per iteration, so it does real ONNX
            inference work throughout the window -- the NEGATIVE CONTROL that a
            robust metric must still detect.

Run:  .venv/Scripts/python.exe -I <this file> [--reps N] [--loaded-only]
"""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from statistics import median

REPO = Path(r"C:\dev\PRIN")
sys.path.insert(0, str(REPO / "python"))

WORK_N = 1_000_000
SAMPLES = 5


def dummy_work(n: int) -> float:
    """The same CPU-bound workload the test uses."""
    total = 0.0
    for i in range(n):
        total += math.sin(float(i))
    return total


class Load:
    """Spawn and reap one busy process per logical CPU."""

    def __init__(self) -> None:
        """Create the holder; no process is started until :meth:`__enter__`."""
        self.procs: list[subprocess.Popen[bytes]] = []

    def __enter__(self) -> Load:
        """Start one busy process per logical CPU and wait for the load to settle.

        Returns:
            This instance, so it can be used as a context manager.
        """
        n = os.cpu_count() or 4
        for _ in range(n):
            self.procs.append(
                subprocess.Popen(  # fixed argv, no shell
                    [sys.executable, "-c", "while True:\n    pass"]
                )
            )
        time.sleep(3.0)  # let the load settle before measuring
        return self

    def __exit__(self, *exc: object) -> None:
        """Kill every spawned busy process and wait for it to be reaped."""
        for p in self.procs:
            p.kill()
        for p in self.procs:
            p.wait(timeout=10)
        self.procs.clear()
        time.sleep(2.0)


def cpu_percent() -> float:
    """Return whole-host CPU utilisation over a half-second sample.

    Returns:
        A percentage, or ``nan`` when ``psutil`` is unavailable, so a missing
        sampler degrades the report instead of aborting the probe.
    """
    try:
        import psutil

        return float(psutil.cpu_percent(interval=0.5))
    except Exception:
        return float("nan")


def measure(arm: str, model: Path, reps: int) -> dict[str, float]:
    """Return wall_block/wall_paired/process/thread ratios for one daemon arm.

    ``arm`` is one of ``idle`` or ``heavy``; ``baseline`` is measured inside.
    """
    from prin.subconscious_compat import (
        SubconsciousDaemon,
        SubconsciousState,
    )

    dummy_work(WORK_N)  # warm-up, per the WP-036G hardening

    # ---- baseline: no daemon -------------------------------------------
    b_wall, b_proc, b_thread = [], [], []
    for _ in range(reps):
        w0, p0, t0 = time.perf_counter(), time.process_time(), time.thread_time()
        dummy_work(WORK_N)
        b_wall.append(time.perf_counter() - w0)
        b_proc.append(time.process_time() - p0)
        b_thread.append(time.thread_time() - t0)

    daemon = SubconsciousDaemon(model, backend="cpu", interval=0.5, warmup=True)
    daemon.start()
    time.sleep(0.5)
    try:
        for _ in range(3):
            daemon.submit_state(SubconsciousState.default())

        d_wall, d_proc, d_thread, paired = [], [], [], []
        for _ in range(reps):
            if arm == "heavy":
                daemon.submit_state(SubconsciousState.default())
            w0, p0, t0 = time.perf_counter(), time.process_time(), time.thread_time()
            dummy_work(WORK_N)
            d_wall.append(time.perf_counter() - w0)
            d_proc.append(time.process_time() - p0)
            d_thread.append(time.thread_time() - t0)

            # paired: a baseline sample immediately after, same load window
            w1 = time.perf_counter()
            dummy_work(WORK_N)
            paired.append((time.perf_counter() - w1) / max(d_wall[-1], 1e-9))
    finally:
        daemon.stop(timeout=5.0)

    return {
        "wall_block": median(d_wall) / max(median(b_wall), 1e-9),
        "wall_paired": 1.0 / max(median(paired), 1e-9),
        "process": median(d_proc) / max(median(b_proc), 1e-9),
        "thread": median(d_thread) / max(median(b_thread), 1e-9),
    }


def main() -> int:
    """Compare candidate metrics under both host conditions and both daemon arms.

    Returns:
        The process exit status; always 0, since this instrument only reports.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=SAMPLES)
    ap.add_argument("--loaded-only", action="store_true")
    args = ap.parse_args()

    from prin.subconscious_compat import SubconsciousController

    with tempfile.TemporaryDirectory() as td:
        model = SubconsciousController().export_to_onnx(Path(td) / "c.onnx")

        conditions = ["loaded"] if args.loaded_only else ["quiet", "loaded"]
        results: dict[str, dict[str, dict[str, float]]] = {}

        for cond in conditions:
            print(f"\n===== condition: {cond} =====", flush=True)
            if cond == "loaded":
                with Load():
                    print(f"  host cpu during load: {cpu_percent():.1f}%", flush=True)
                    results[cond] = {
                        arm: measure(arm, model, args.reps) for arm in ("idle", "heavy")
                    }
            else:
                print(f"  host cpu: {cpu_percent():.1f}%", flush=True)
                results[cond] = {
                    arm: measure(arm, model, args.reps) for arm in ("idle", "heavy")
                }

    metrics = ("wall_block", "wall_paired", "process", "thread")
    print("\n\n===== ratio table (1.00 = no measured overhead) =====")
    print(
        f"{'condition':<10} {'metric':<12} {'idle arm':>10} {'heavy arm':>10} "
        f"{'detects heavy?':>15}"
    )
    for cond, arms in results.items():
        for m in metrics:
            idle, heavy = arms["idle"][m], arms["heavy"][m]
            detects = "YES" if heavy > idle * 1.15 else "no"
            print(f"{cond:<10} {m:<12} {idle:>10.3f} {heavy:>10.3f} {detects:>15}")
        print()

    print("Interpretation guide:")
    print("  * A usable metric is STABLE for the idle arm across quiet and loaded")
    print("    (robust to external contention) AND shows heavy > idle (non-vacuous).")
    print("  * wall_block reproducing a large idle ratio under load confirms the")
    print("    registered DV-032 defect rather than asserting it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

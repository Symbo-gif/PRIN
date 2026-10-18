"""Size the evidence-based bound for the DV-032 replacement assertion.

The probe established that the daemon's throughput shadow (~1.1%) is ~27x below
the old 30% allowance, so no wall-clock ratio can carry signal.  The replacement
therefore bounds the daemon's OWN resource cost directly, which is deterministic
given the fixed controller model and the fixed default state.

Method: submit K states, let the main thread SLEEP while the daemon drains them,
and take the process CPU-time delta over that window.  A sleeping main thread
contributes ~0 CPU, so the delta is the daemon's own CPU cost.  Measured under
both a quiet host and a host saturated with one busy process per logical CPU, so
the bound is sized from observed variance rather than guessed (section 7 item 2).

Also measures the deterministic completion counts the replacement asserts.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from statistics import median

sys.path.insert(0, r"C:\dev\PRIN\python")

K = 200  # inferences per measurement window
REPS = 5


class Load:
    def __init__(self) -> None:
        self.procs: list[subprocess.Popen[bytes]] = []

    def __enter__(self) -> "Load":
        for _ in range(os.cpu_count() or 4):
            self.procs.append(
                subprocess.Popen([sys.executable, "-c", "while True:\n    pass"])
            )
        time.sleep(3.0)
        return self

    def __exit__(self, *exc: object) -> None:
        for p in self.procs:
            p.kill()
        for p in self.procs:
            p.wait(timeout=10)
        self.procs.clear()
        time.sleep(2.0)


def cpu_percent() -> float:
    try:
        import psutil

        return float(psutil.cpu_percent(interval=0.5))
    except Exception:
        return float("nan")


def measure_daemon_cpu(model: Path, reps: int) -> tuple[list[float], int, int]:
    """Return per-inference daemon CPU-ms samples, plus inferences and errors."""
    from prin.subconscious_compat import SubconsciousDaemon, SubconsciousState

    daemon = SubconsciousDaemon(model, backend="cpu", interval=0.5, warmup=True)
    daemon.start()
    time.sleep(0.5)
    samples: list[float] = []
    try:
        for _ in range(reps):
            n0 = daemon._inferences
            c0 = time.process_time()
            w0 = time.perf_counter()
            for _ in range(K):
                daemon.submit_state(SubconsciousState.default())
            # Drain: sleep until the daemon has consumed everything submitted.
            while daemon._inferences - n0 < K:
                time.sleep(0.005)
                if time.perf_counter() - w0 > 60.0:
                    break
            cpu_ms = (time.process_time() - c0) * 1000.0
            done = daemon._inferences - n0
            samples.append(cpu_ms / max(done, 1))
        return samples, daemon._inferences, daemon._errors
    finally:
        daemon.stop(timeout=5.0)


def main() -> int:
    from prin.subconscious_compat import SubconsciousController

    with tempfile.TemporaryDirectory() as td:
        model = SubconsciousController().export_to_onnx(Path(td) / "c.onnx")

        all_samples: dict[str, list[float]] = {}
        for cond in ("quiet", "loaded"):
            print(f"\n===== condition: {cond} =====", flush=True)
            if cond == "loaded":
                with Load():
                    print(f"  host cpu: {cpu_percent():.1f}%", flush=True)
                    s, inf, err = measure_daemon_cpu(model, REPS)
            else:
                print(f"  host cpu: {cpu_percent():.1f}%", flush=True)
                s, inf, err = measure_daemon_cpu(model, REPS)
            all_samples[cond] = s
            print(f"  inferences completed: {inf}   errors: {err}")
            print(f"  daemon CPU ms per inference: "
                  f"min {min(s):.4f}  median {median(s):.4f}  max {max(s):.4f}")

    quiet = all_samples["quiet"]
    loaded = all_samples["loaded"]
    worst = max(max(quiet), max(loaded))
    print("\n===== bound sizing =====")
    print(f"  quiet  median {median(quiet):.4f} ms   max {max(quiet):.4f} ms")
    print(f"  loaded median {median(loaded):.4f} ms   max {max(loaded):.4f} ms")
    print(f"  worst observed across both conditions: {worst:.4f} ms")
    for mult in (2.0, 3.0, 5.0, 10.0):
        print(f"  x{mult:<4} worst = {worst * mult:8.3f} ms")
    print("\nA bound must sit above the loaded worst case with real margin, and")
    print("low enough that a genuine daemon regression (e.g. a heavier model or a")
    print("busy-wait loop) would exceed it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

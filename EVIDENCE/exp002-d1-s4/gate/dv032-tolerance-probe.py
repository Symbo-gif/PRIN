"""Size the tolerance for the DV-032 replacement assertion, from measurement.

The replacement keeps the original test's structure and its intended property but
changes the CLOCK from wall time to process CPU time, which by definition
excludes time spent waiting for other processes -- the mechanism that produced
the observed 22.07.  Testing Standards section 7 item 2 requires the bound to be
sized from cited evidence plus margin, so this measures the ratio's distribution
under a quiet host and under a saturated one, in the exact shape the test uses.

Drain waits on the queue being EMPTY (bounded by a deadline), never on a target
inference count: submit_state drops the oldest state when the queue is full, so a
count-based drain target is unreachable and would spin to the cap.

Run: .venv/Scripts/python.exe -I <this file> [--reps N]
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

sys.path.insert(0, r"C:\dev\PRIN\python")

WORK_N = 1_000_000


def dummy_work(n: int) -> float:
    total = 0.0
    for i in range(n):
        total += math.sin(float(i))
    return total


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


def one_rep(model: Path) -> tuple[float, float, int, int]:
    """One repetition; returns (cpu_ratio, wall_ratio, inferences, errors)."""
    from prin.subconscious_compat import SubconsciousDaemon, SubconsciousState

    daemon = SubconsciousDaemon(model, backend="cpu", interval=0.5, warmup=True)
    dummy_work(WORK_N)  # warm-up

    base_cpu, base_wall = [], []
    for _ in range(3):
        c0, w0 = time.process_time(), time.perf_counter()
        dummy_work(WORK_N)
        base_cpu.append(time.process_time() - c0)
        base_wall.append(time.perf_counter() - w0)

    daemon.start()
    try:
        time.sleep(0.5)
        for _ in range(3):
            daemon.submit_state(SubconsciousState.default())
        dummy_work(WORK_N)
        d_cpu, d_wall = [], []
        for _ in range(7):
            c0, w0 = time.process_time(), time.perf_counter()
            dummy_work(WORK_N)
            d_cpu.append(time.process_time() - c0)
            d_wall.append(time.perf_counter() - w0)
        deadline = time.perf_counter() + 10.0
        while daemon._state_queue.qsize() > 0 and time.perf_counter() < deadline:
            time.sleep(0.01)
        inferences, errors = daemon._inferences, daemon._errors
    finally:
        daemon.stop(timeout=5.0)

    dummy_work(WORK_N)
    for _ in range(4):
        c0, w0 = time.process_time(), time.perf_counter()
        dummy_work(WORK_N)
        base_cpu.append(time.process_time() - c0)
        base_wall.append(time.perf_counter() - w0)

    cpu_ratio = median(d_cpu) / max(median(base_cpu), 1e-9)
    wall_ratio = median(d_wall) / max(median(base_wall), 1e-9)
    return cpu_ratio, wall_ratio, inferences, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    args = ap.parse_args()

    from prin.subconscious_compat import SubconsciousController

    with tempfile.TemporaryDirectory() as td:
        model = SubconsciousController().export_to_onnx(Path(td) / "c.onnx")
        out: dict[str, list[tuple[float, float]]] = {}
        errs = 0
        for cond in ("quiet", "loaded"):
            print(f"\n===== condition: {cond} =====", flush=True)
            rows: list[tuple[float, float]] = []
            if cond == "loaded":
                with Load():
                    print(f"  host cpu: {cpu_percent():.1f}%", flush=True)
                    for i in range(args.reps):
                        c, w, inf, e = one_rep(model)
                        errs += e
                        rows.append((c, w))
                        print(f"  rep {i + 1}: cpu_ratio {c:.4f}  wall_ratio {w:.4f}  "
                              f"inferences {inf}  errors {e}", flush=True)
            else:
                print(f"  host cpu: {cpu_percent():.1f}%", flush=True)
                for i in range(args.reps):
                    c, w, inf, e = one_rep(model)
                    errs += e
                    rows.append((c, w))
                    print(f"  rep {i + 1}: cpu_ratio {c:.4f}  wall_ratio {w:.4f}  "
                          f"inferences {inf}  errors {e}", flush=True)
            out[cond] = rows

    print("\n\n===== distribution =====")
    print(f"{'condition':<8} {'metric':<10} {'min':>8} {'median':>8} {'max':>8}")
    worst_cpu = 0.0
    worst_wall = 0.0
    for cond, rows in out.items():
        cs = [r[0] for r in rows]
        ws = [r[1] for r in rows]
        worst_cpu = max(worst_cpu, max(cs))
        worst_wall = max(worst_wall, max(ws))
        print(f"{cond:<8} {'cpu':<10} {min(cs):>8.4f} {median(cs):>8.4f} {max(cs):>8.4f}")
        print(f"{cond:<8} {'wall':<10} {min(ws):>8.4f} {median(ws):>8.4f} {max(ws):>8.4f}")
    print(f"\ntotal daemon errors across all reps: {errs}")
    print(f"worst cpu_ratio observed  : {worst_cpu:.4f}")
    print(f"worst wall_ratio observed : {worst_wall:.4f}")
    print("\nThe wall column is the CURRENT metric; the cpu column is the")
    print("proposed one.  Compare their spread under load directly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

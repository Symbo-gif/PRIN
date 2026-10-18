"""Verify the negative control actually engaged the daemon.

The metric probe reported that NO candidate metric detects the "heavy" arm. Two
explanations imply opposite fixes, so they must be distinguished by measurement:

  (a) the daemon ran real inferences but they are genuinely negligible next to
      ~100 ms of _dummy_work  -> the test is a pure NOISE detector and no timing
      metric can rescue it;
  (b) the heavy arm never engaged the daemon (queue full, stop-event, session
      init failure) -> the probe was broken and its conclusion is void.

This is the same class of error as the earlier negctl.py PYTHONPATH bug, where a
negative control measured nothing and falsely reported "DID NOT FAIL".
"""

from __future__ import annotations

import math
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, r"C:\dev\PRIN\python")

WORK_N = 1_000_000


def dummy_work(n: int) -> float:
    """Run the same CPU-bound workload the test under study uses.

    Args:
        n: Number of ``math.sin`` iterations.

    Returns:
        The accumulator, so the work cannot be optimised away.
    """
    total = 0.0
    for i in range(n):
        total += math.sin(float(i))
    return total


def main() -> int:
    """Report the daemon's real inference cost and what it does in the window.

    Returns:
        The process exit status; always 0, since this instrument only reports.
    """
    from prin.subconscious_compat import (
        SubconsciousController,
        SubconsciousDaemon,
        SubconsciousState,
    )

    with tempfile.TemporaryDirectory() as td:
        model = SubconsciousController().export_to_onnx(Path(td) / "c.onnx")

        # Cost of one unit of the main-thread workload, for scale comparison.
        dummy_work(WORK_N)
        t0 = time.perf_counter()
        dummy_work(WORK_N)
        work_cost = time.perf_counter() - t0
        print(f"_dummy_work(1_000_000) wall cost : {work_cost * 1000:.2f} ms")

        daemon = SubconsciousDaemon(model, backend="cpu", interval=0.5, warmup=True)
        daemon.start()
        time.sleep(0.5)
        print(f"session initialised              : {daemon._session is not None}")
        print(f"inferences before submits        : {daemon._inferences}")
        print(f"errors                           : {daemon._errors}")

        # Cost of ONE inference, measured directly.
        n0 = daemon._inferences
        t0 = time.perf_counter()
        for _ in range(200):
            daemon.submit_state(SubconsciousState.default())
            # give the daemon thread a chance to consume it
            time.sleep(0.001)
        submit_wall = time.perf_counter() - t0
        time.sleep(1.0)
        n1 = daemon._inferences
        print(f"submitted 200 states in          : {submit_wall * 1000:.1f} ms")
        print(f"inferences actually completed    : {n1 - n0}")
        print(f"errors after submits             : {daemon._errors}")
        if n1 > n0:
            print(
                f"mean wall per submit+inference   : {submit_wall / 200 * 1000:.3f} ms"
            )
            print(
                f"ratio of one inference to one "
                f"_dummy_work : {(submit_wall / 200) / work_cost:.4f}"
            )

        # What the current test actually does: submit 3, then time 7 work units.
        daemon2 = SubconsciousDaemon(model, backend="cpu", interval=0.5, warmup=True)
        daemon2.start()
        time.sleep(0.5)
        for _ in range(3):
            daemon2.submit_state(SubconsciousState.default())
        before = daemon2._inferences
        t0 = time.perf_counter()
        for _ in range(7):
            dummy_work(WORK_N)
        window = time.perf_counter() - t0
        after = daemon2._inferences
        daemon2.stop(timeout=5.0)
        print()
        print("== the current test's measurement window ==")
        print(f"window wall time                 : {window * 1000:.1f} ms")
        print(f"inferences during window         : {after - before}")
        print(f"queue size left                  : {daemon2._state_queue.qsize()}")
        print()
        print("If 'inferences during window' is 0, the daemon does NO work while")
        print("the test measures, so the assertion can only ever detect host noise.")

    daemon.stop(timeout=5.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

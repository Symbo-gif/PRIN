#!/usr/bin/env python3
"""DV-003 host-residual probe for the CUDA mean-field RK4 step (WP036E-F1).

Times ``core.GpuMeanFieldEngine.step()`` on a 262,144-oscillator CUDA engine
and compares the outer wall time against the returned ``StepReport`` duration.
Records that the CUDA ``timing_method`` is ``system`` (``cubecl-cuda`` 0.10.0
has no device-event timing) and that the host residual is bounded and small.

Run on ``PRIN-GPU-Runner`` after ``maturin develop --release --features cuda``.
"""

from __future__ import annotations

import statistics
import time
from typing import Any

import prin._prin_core as core
import torch

N = 262_144
WARMUP = 5
MEASURED = 20


def main() -> int:
    """Print the median outer wall / StepReport / residual over ``MEASURED`` steps."""
    # One host upload at construction (amendment #43 device-resident envelope):
    # the constructor takes CPU f32; the engine holds device buffers thereafter.
    gen = torch.Generator().manual_seed(7)
    phase = (torch.rand(N, generator=gen) * 6.283).to(torch.float32)
    amp = (0.5 + torch.rand(N, generator=gen)).to(torch.float32)
    freq = (0.01 * (torch.rand(N, generator=gen) - 0.5)).to(torch.float32)

    engine = core.GpuMeanFieldEngine(phase, amp, freq, 2.0, 0.1, 0.01, 0.01)

    for _ in range(WARMUP):
        engine.step()

    outer: list[float] = []
    inner: list[float] = []
    report: Any = {}
    for _ in range(MEASURED):
        start = time.perf_counter()
        report = engine.step()
        outer.append(time.perf_counter() - start)
        inner.append(float(report["wall_time_seconds"]))

    med_outer = statistics.median(outer)
    med_inner = statistics.median(inner)
    print(
        f"backend {report['backend_name']}; timing {report['timing_method']}; "
        f"launches {report['launch_count']}"
    )
    print(f"median outer wall       {med_outer:.10f} s")
    print(f"median StepReport       {med_inner:.10f} s")
    print(f"median residual         {med_outer - med_inner:.10f} s")
    print(f"wall / StepReport       {med_outer / med_inner:.7f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

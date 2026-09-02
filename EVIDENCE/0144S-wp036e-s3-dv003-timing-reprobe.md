# 0144S / WP-036E S3 — DV-003 timing re-probe (finding WP036E-F1)

**Session:** `0144S` (WP-036E S3 remediation)
**Date:** 2026-09-02
**Host:** `PRIN-GPU-Runner` — NVIDIA GeForce RTX 4060 (8188 MiB), driver 595.95;
Python 3.14.0; `torch 2.11.0+cu128`; `prin 0.3.0` rebuilt
`maturin develop --release --features cuda` at S3 HEAD.

## Purpose

`0144R` audit action item 5 — re-run the DV-003 residual probe after the S3
remediation and record it against **plan amendment #44**. The probe confirms
two things the amendment rests on:

1. the CUDA `StepReport` `timing_method` is **`system`**, not a device event
   (the WP036E-F1 root cause — `cubecl-cuda` 0.10.0 hard-registers
   `TimingMethod::System`);
2. the host residual (outer wall minus the profiled `StepReport` duration) is
   **bounded and small** — far under the historical ≈25 ms vs 388 µs
   dispatch-overhead gap DV-003 recorded.

## Method

`tools/dv003_timing_probe.py` (committed alongside this file): a
262,144-oscillator CUDA `core.GpuMeanFieldEngine` (one host `f32` upload of the
initial state at construction — the amendment-#43 device-resident envelope),
5 warm-up `step()`s, then 20 measured `step()`s with `time.perf_counter`
around `step()` and the returned `StepReport["wall_time_seconds"]`.

## Result (representative run; 4 consecutive runs agree)

```
backend cuda; timing system; launches 9
median outer wall       0.0006494000 s
median StepReport       0.0006171500 s
median residual         0.0000322500 s
wall / StepReport       1.0522564
```

Residual across four runs: 0.0287–0.0389 ms; ratio 1.049–1.052; `timing_method`
`system` and `launch_count` 9 every run.

## Reading

- **`timing system`** — `StepReport.timing_method` is `TimingMethod::System`
  on the CUDA path, exactly as `cubecl-cuda-0.10.0/src/runtime.rs:169-174`
  (`DeviceProperties::new(..., TimingMethod::System)`) forces. Genuine
  device-event timing is unreachable through CubeCL 0.10's public API
  (plan amendment #44).
- **residual ≈ 0.03 ms**, ratio ≈ 1.05 — the host dispatch/sync overhead
  around the profiled 9-launch sequence is bounded and small (the on-device
  CUDA `f64` combine + batched read-backs from `0144Q2` removed the per-stage
  `2·num_blocks` read-backs that dominated the historical figure). Consistent
  with — and tighter than — the `0144R` probe (0.155 ms residual, ratio
  1.058); the absolute magnitude tracks GPU clock state and the measurement
  path, the **conclusion is identical**: bounded residual, `system` timing.

DV-003 is `PARTIALLY CLOSED by WP-036E` (plan amendment #44): the on-device
combine and the bounded residual are delivered; genuine CUDA device-event
timing is re-gated to a `cubecl` release exposing `TimingMethod::Device` for
the CUDA runtime, or a dedicated vendored-shim WP.

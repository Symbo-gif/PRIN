# Session 0144Q2 — WP-036E S1 (sub-pass 2/3): `prin-sim` persistent device buffers + DV-003 on-device combine

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S1 — Coding
**Predecessor:** [0144Q1 — Coding (sub-pass 1/3)](0144Q1-wp036e-s1-prin-kernels-device-handle-dispatch-layer.md)
**Successor:** [0144Q3 — Coding (sub-pass 3/3)](0144Q3-wp036e-s1-prin-py-export-zero-copy-dlpack-torch-compat-test-activation.md)
**Authority:** Project Plan §6/§8, amendments #38/#43, and
[`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md).
The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Make `prin-sim`'s three GPU engines device-resident: hold a CubeCL
`ComputeClient` + persistent device `Handle`s across `step`, with an explicit
`to_host()` the only download, and CSR topology device-resident after
construction. Move the `mean_field_rk4` level-2 `f64` combine on-device on CUDA
(**DV-003**) with batched read-backs and whole-sequence `StepReport`
device-event timing.

## Scope

- `crates/prin-sim/src/gpu.rs`:
  - `GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper` restructured
    to own the `0144Q1` device-state structs + a resolved `ComputeClient`
    (backend chosen once at construction via `auto_detect_order`). `step`
    mutates device state in place; no per-step host transfer.
  - Explicit `to_host()` / `state()` performs the single download.
  - The `Dynamics` impl for `GpuSparseKuramoto` retains its host-slice
    signature (it is a one-shot derivative evaluator driven by the generic
    integrator); the device-resident path is the engine `step` loop. Document
    the split.
- On-device `f64` level-2 combine: a CUDA-only `#[cube]` reduction finalising
  the order parameter in device `f64` (wgpu DX12 keeps the documented host
  `f64` combine — `SHADER_F64` is Vulkan-only). Batch the 8-launch-sequence
  result read-backs. `StepReport` records device-event timing over the whole
  sequence; the DV-003 host-overhead gap is closed or bounded with evidence
  on `PRIN-GPU-Runner`.

## Contract

- GPU (f32 kernel) vs CPU (f64 reference) within `rtol=1e-5, atol=1e-6`, or a
  per-test annotation + Parity Report entry.
- Deterministic `Seed` preserved; tests in tandem with every behaviour.
- No new `prin` public symbol; `unsafe` only in the amendment-#8-audited
  modules; numerical authority in Rust.
- `≥95%` coverage on changed first-party lines.

## Gates

As `0144Q1`, plus `cargo test -p prin-sim --features cuda` /
`--features wgpu` / `--features cpu`; device-event timing evidence recorded in
the S1 handoff.

## Non-goals

`prin-py` / Python / DLPack (→ `0144Q3`); `test_sparse_vram_subquadratic`
(→ `0144Q3`); a wgpu device-`f64` path (hardware-gated); the S2 audit.

## Exit

All gates green; engines hold device state across `step`; DV-003 gap closed or
bounded with recorded evidence; commit at the green local gate; hand to
`0144Q3`.

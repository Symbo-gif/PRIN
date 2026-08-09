Kernel Architecture
===================

PRIN replaces PRINet 3.0's three separate kernel implementations
(`utils/triton_kernels.py`, `utils/cuda_kernels.py`,
`utils/fused_kernels.py`) with a single-source CubeCL kernel set that
compiles to CUDA, Metal, Vulkan, and CPU SIMD at wheel-build time — no
runtime nvcc/MSVC JIT.

Phase 0 spike — fused mean-field RK4
------------------------------------

`prin-kernels` currently implements the first single-source kernel:

- CPU reference: `crates/prin-kernels/src/mean_field_rk4.rs`
- CubeCL dispatch: `crates/prin-kernels/src/mean_field_rk4/cubecl.rs`

The CPU reference (`step_cpu`) is the numerical authority. The CubeCL path
(`step_cubecl`) is generic over `R: Runtime` and is exposed through
runtime-specific entry points:

- `try_step_cpu` — CubeCL CPU runtime (headless/CI-friendly, ``--features cpu``).
- `try_step_wgpu` — wgpu/WGSL runtime (``--features wgpu``).
- `try_step_cuda` — CUDA runtime (``--features cuda``).

The public types are:

- `MeanFieldRk4Params` — coupling `k`, amplitude damping `decay`, frequency
  adaptation `gamma`, timestep `dt`.
- `MeanFieldRk4Error` — typed errors for length mismatches, empty populations,
  invalid parameters, device read-back failures, and unavailable backends.
- `StepReport` — backend name, host wall-clock seconds, and number of launches
  (device-side event timing is a Phase 3 optimization; performance claims may
  not be published from the wall-clock prototype).

Validation
----------

- `cargo test -p prin-kernels --features cpu` runs the CubeCL CPU
  kernel-equivalence tests on every CI platform.
- `cargo test -p prin-kernels --features wgpu,cpu` runs the wgpu
  kernel-equivalence tests at N=64 and N=1M against the CPU reference
  (`rtol=1e-5`, `atol=1e-6`).
- Property tests (``proptest``) cover phase wrap, amplitude clamp,
  zero-coupling identity, RK4 local-error scaling, and order-parameter bounds.
- The CUDA path is gated by the ``[gpu]``-triggered `gpu.yml` self-hosted runner
  workflow.

Future work (Phase 3)
---------------------

The full production suite in Phase 3 extends the mean-field RK4 pattern to:

- Sparse k-NN coupling.
- PAC modulation.
- Fused discrete step (phase advance + PAC gating + Stuart–Landau in one
  launch).
- Hierarchical device-side order-parameter reductions (replacing the host
  reductions used in the Phase 0 spike).

Rust API reference for `prin-kernels` is published on `docs.rs
<https://docs.rs/prin-kernels/latest/prin_kernels/>`_.

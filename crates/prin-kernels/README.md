# prin-kernels

Single-source fused kernels for PRIN (CubeCL: CUDA / Metal / Vulkan / CPU SIMD),
replacing PRINet 3.0's triple implementation
(`utils/triton_kernels.py`, `utils/cuda_kernels.py`, `utils/fused_kernels.py`).

Kernels: fused mean-field RK4, sparse k-NN coupling, PAC modulation, fused
discrete step, hierarchical order-parameter reduction. All precompiled at
wheel-build time — no runtime nvcc/MSVC JIT.

Feature flags: `cpu` (CubeCL CPU runtime, headless/CI-friendly), `cuda`, `wgpu`.
Kernel-equivalence tests compare every GPU/CPU kernel against the CPU reference
across shapes and dtypes.

## Phase 0 status

`src/ops.rs` provides simple element-wise CPU kernels (`negate_f32`,
`negate_f64`) used by the WP-003 PyO3/DLPack bridge spike to demonstrate that
the Rust core owns the numerics while the Python layer only marshals tensors.

`src/mean_field_rk4.rs` and `src/mean_field_rk4/cubecl.rs` are the WP-004 Phase 0
fused mean-field RK4 spike:

- CPU reference [`step_cpu`](src/mean_field_rk4.rs) is the numerical authority.
- Single-source CubeCL kernels dispatch to `cpu`, `wgpu`, or `cuda` through
  `try_step_cpu`, `try_step_wgpu`, and `try_step_cuda`.
- `MeanFieldRk4Error` carries typed input/parameter/backend errors, including
  `BackendUnavailable` when a GPU runtime is not present.
- `StepReport` records backend name, host wall-clock time, and launch count
  (device-event timing is a Phase 3 optimization).
- Kernel-equivalence tests validate wgpu and CubeCL-CPU against the CPU reference
  at N=64 and N=1M; property tests cover phase wrap, amplitude clamp,
  zero-coupling identity, RK4 local-error scaling, and order-parameter bounds.

The production fused-kernel suite (sparse k-NN coupling, PAC, fused discrete
step, hierarchical reductions) lands in Phase 3 (WP-017…WP-021).

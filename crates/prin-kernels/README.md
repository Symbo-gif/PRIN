# prin-kernels

Single-source fused kernels for PRIN (CubeCL: CUDA / Metal / Vulkan / CPU SIMD),
replacing PRINet 3.0's triple implementation
(`utils/triton_kernels.py`, `utils/cuda_kernels.py`, `utils/fused_kernels.py`).

Kernels: fused mean-field RK4, sparse k-NN coupling, PAC modulation, fused
discrete step, hierarchical order-parameter reduction. All precompiled at
wheel-build time — no runtime nvcc/MSVC JIT.

Feature flags: `cuda`, `wgpu`. Kernel-equivalence tests compare every GPU kernel
against the CPU reference across shapes and dtypes.

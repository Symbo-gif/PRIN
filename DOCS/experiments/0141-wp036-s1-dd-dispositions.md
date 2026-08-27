# WP-036 S1 D-D per-symbol dispositions

**Date:** 2026-08-27  
**Status:** Proposed in S1 under mandatory session-0142 S2 audit veto  
**Authority:** Plan amendments #31/#32 and
`WP-036-S1-execution-plan-and-decomposition.md` §3.2

## Decision rule

A legacy GPU/Triton/CUDA symbol receives a real PRIN binding when an audited
Rust CPU owner exists. A path that PRIN deliberately does not rebuild receives
a documented, typed, fail-closed disposition; availability predicates return
`False`. No Python numerical implementation is introduced.

## Disposition table

| # | PRINet 3.0 symbol | WP-036 disposition | Delivery pass |
|---:|---|---|---|
| 1 | `triton_available` | Predicate returning `False` | 0141A |
| 2 | `triton_fused_mean_field_rk4_step` | `BackendUnavailableError` stub; migrate to CPU binding or Rust dispatch | 0141A |
| 3 | `triton_sparse_knn_coupling` | `BackendUnavailableError` stub; migrate to CPU binding or Rust dispatch | 0141A |
| 4 | `triton_pac_modulation` | `BackendUnavailableError` stub; migrate to CPU binding or Rust dispatch | 0141A |
| 5 | `triton_hierarchical_order_param` | `BackendUnavailableError` stub; migrate to CPU binding or Rust dispatch | 0141A |
| 6 | `triton_fused_discrete_step` | `BackendUnavailableError` stub; migrate to CPU binding or Rust dispatch | 0141A |
| 7 | `cuda_fused_kernel_available` | Predicate returning `False` | 0141A |
| 8 | `fused_discrete_step_cuda` | `BackendUnavailableError` stub; use Rust CUDA/wgpu/CPU dispatch | 0141A |
| 9 | `pytorch_mean_field_rk4_step` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 10 | `pytorch_sparse_knn_coupling` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 11 | `pytorch_pac_modulation` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 12 | `pytorch_hierarchical_order_param` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 13 | `pytorch_multi_rate_rk4_step` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 14 | `pytorch_multi_rate_derivatives` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 15 | `pytorch_fused_sub_step_rk4` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 16 | `pytorch_cross_band_coupling` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 17 | `pytorch_fused_discrete_step` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 18 | `pytorch_fused_discrete_step_full` | Real binding over the authoritative `prin-kernels` CPU reference | 0141C |
| 19 | `csr_coupling_step` | Real binding over the existing Rust sparse-coupling owner | 0141C |
| 20 | `sparse_knn_coupling_step` | Real binding over the existing Rust sparse-coupling owner | 0141C |
| 21 | `build_knn_neighbors` | Real binding over the existing Rust k-NN owner | 0141C |
| 22 | `sparse_coupling_matrix` | Real binding over the existing Rust sparse-coupling owner | 0141C |
| 23 | `sparse_coupling_matrix_csr` | Real binding over the existing Rust sparse-coupling owner | 0141C |
| 24 | `AsyncCPUGPUPipeline` | CPU-synchronous orchestration shim if faithful; otherwise typed disposition | 0141D |
| 25 | `MixedPrecisionTrainer` | Faithful non-numeric orchestration shim or typed disposition | 0141D |
| 26 | `LargeScaleOscillatorSystem` | Real wrapper over the existing simulation owner | 0141D |
| 27 | `BatchedRK45Solver` | Real wrapper over `prin.dynamics.RK45Integrator` | 0141D |
| 28 | `FixedStepRK4Solver` | Real wrapper over `prin.dynamics.RK4Integrator` | 0141D |
| 29 | `SolverResult` | Real result wrapper shared by the solver compatibility surface | 0141D |
| 30 | `gradient_checkpoint_integration` | Thin orchestration wrapper over checkpointing and Rust integration | 0141D |

## S2 veto questions

Session 0142 must independently confirm that each “real binding” row names an
existing Rust numerical owner, that no stub masks an available faithful owner,
and that the 0141D conditional rows resolve to either a tested orchestration
implementation or an explicit Migration Guide disposition before WP-036 S1
closes.

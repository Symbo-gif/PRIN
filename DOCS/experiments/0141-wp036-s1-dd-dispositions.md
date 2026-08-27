# WP-036 S1 D-D per-symbol dispositions

**Date:** 2026-08-27 (extended by sub-pass 0141B)  
**Status:** Proposed in S1 under mandatory session-0142 S2 audit veto  
**Authority:** Plan amendments #31/#32 and
`WP-036-S1-execution-plan-and-decomposition.md` §3.2; the 0141B descope
decision (maintainer-approved, 2026-08-27) recorded in
`0141-wp036-s1-handoff.md` §0141B.

## Decision rule

A legacy GPU/Triton/CUDA symbol receives a real PRIN binding when an audited
Rust CPU owner exists. A path that PRIN deliberately does not rebuild receives
a documented, typed, fail-closed disposition; availability predicates return
`False`. No Python numerical implementation is introduced.

**0141B extension.** The 0141B brief's Bucket E enumeration assumed twelve
`nn/layers.py` / `core/propagation/inhibition.py` symbols had a `prin-train`
owner. Repository grep at 0141B start (`crates/**/*.rs`) shows they do not:
WP-014/022/023 rebuilt only `PolyadicTensor`/`CPDecomposition`,
`ResonanceLayer`, `DiscreteDeltaThetaGamma`, `FeedbackInhibition`, the WP-023
activations, `HolomorphicEnergy`, and `HolomorphicEp`. The WP-023 audit (§line
83) confirms `FeedforwardInhibition`/`DentateGyrusConverter` were deliberately
excluded. In PRINet 3.0 the twelve are **trainable `nn.Module`s** (`nn.Linear`
projections, `nn.Parameter` modulation depths); a faithful binding needs
net-new trainable Rust numerics + autodiff, which the 0141B brief prohibits
("thin marshalling only", "no numerics added"). Per D-2.2 (maintainer-approved)
they receive a documented deferral disposition + Migration-Guide row here,
S2 veto retained. They are re-bucketed from Bucket E to "deferred rebuild";
0141D/0141E must account for them (not silently drop) and the maintainer
must declare the WP that owns the rebuild.

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

## 0141B additions — trainable `nn/layers.py` / `inhibition.py` with no Rust owner

Documented deferral dispositions (D-2.2). Each has an entry in the Migration
Guide "deferred rebuild (no Rust owner)" table. `prin.__all__` does not gain
these in 0141B; 0141E resolves the full 172-symbol surface and must not drop
them silently.

| # | PRINet 3.0 symbol | WP-036 disposition | Delivery pass |
|---:|---|---|---|
| 31 | `FeedforwardInhibition` | Deferred rebuild — parameter-free gate, excluded from WP-023 (023 audit §Non-goals); needs a `prin-dynamics`/`prin-train` rebuild | future WP (maintainer to declare) |
| 32 | `DentateGyrusConverter` | Deferred rebuild — FFI→integration→FBI pipeline, excluded from WP-023 | future WP |
| 33 | `DGLayer` | Deferred rebuild — trainable wrapper over `DentateGyrusConverter` | future WP |
| 34 | `oscillatory_weight_init` | Deferred rebuild — `nn/layers.py` init helper, no Rust owner | future WP |
| 35 | `PhaseToRateConverter` | Deferred rebuild — trainable `nn.Module`, no Rust owner | future WP |
| 36 | `PhaseToRateAutoencoder` | Deferred rebuild — trainable `nn.Module`, no Rust owner | future WP |
| 37 | `DenseAutoencoder` | Deferred rebuild — trainable `nn.Module`, no Rust owner | future WP |
| 38 | `SparsityRegularizationLoss` | Deferred rebuild — trainable-loss `nn.Module`, no Rust owner | future WP |
| 39 | `HierarchicalResonanceLayer` | Deferred rebuild — trainable `nn.Module` over `DeltaThetaGammaNetwork` w/ learnable projections + PAC depths | future WP |
| 40 | `PhaseAmplitudeCouplingLayer` | Deferred rebuild — trainable `nn.Module` over `PhaseAmplitudeCoupling` w/ learnable modulation depth | future WP |
| 41 | `PRINetModel` | Deferred rebuild — top-level trainable model, no Rust owner | future WP |
| 42 | `compile_model` | Deferred rebuild — `torch.compile` helper, no Rust owner | future WP |

## S2 veto questions

Session 0142 must independently confirm that each “real binding” row names an
existing Rust numerical owner, that no stub masks an available faithful owner,
and that the 0141D conditional rows resolve to either a tested orchestration
implementation or an explicit Migration Guide disposition before WP-036 S1
closes. For the 0141B additions (rows 31–42), 0142 must confirm no `prin-train`
owner was overlooked, that the deferral is faithful to the WP-023 audit's
exclusion of `FeedforwardInhibition`/`DentateGyrusConverter`, and that a WP is
declared to own the trainable-layer rebuild before WP-036 S1 closes at 0141E.

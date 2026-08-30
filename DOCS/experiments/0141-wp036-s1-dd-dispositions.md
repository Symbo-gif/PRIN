# WP-036 S1 D-D per-symbol dispositions

**Date:** 2026-08-27 (extended by sub-passes 0141B, 0141D1; finalised at 0141E)  
**Status:** FINAL for S1 — proposed under mandatory session-0142 S2 audit veto  
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
| 27 | `BatchedRK45Solver` | **Delivered (real):** thin wrapper over `prin.dynamics.RK45Integrator.integrate_adaptive`. `min_dt`/`safety_factor`/`max_step_increase`/`compiled` accepted but advisory/inert (Migration Guide D2/D3). | 0141D1 |
| 28 | `FixedStepRK4Solver` | **Delivered (real):** thin wrapper over `prin.dynamics.RK4Integrator.integrate_fixed`. `compiled` accepted but inert. | 0141D1 |
| 29 | `SolverResult` | **Delivered (real):** faithful `@dataclass` port. `n_function_evals` is a stage estimate (Migration Guide D1). | 0141D1 |
| 30 | `gradient_checkpoint_integration` | **Delivered (real, documented deviation):** segmented fixed-step RK4 over the Rust integrator; final state bit-identical to an un-segmented call. `torch.utils.checkpoint` behaviour is inert because the compat integrator surface is not a `torch.autograd.Function` (Migration Guide D4). | 0141D1 |

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

## 0141D split — sub-pass 0141D1 delivered, 0141D2 carries the remainder

Per the 0141D brief ("Expected work" item 3) and Development Workflow §7, Bucket
G (~45 symbols across ~6 reference modules) exceeds one reviewable commit range
and is split:

- **0141D1 (delivered):** the PRINet 3.0 `utils/cuda_kernels.py` solver family
  (`SolverResult`, `BatchedRK45Solver`, `FixedStepRK4Solver`,
  `gradient_checkpoint_integration` — rows 27–30 above, all **real**) plus the
  self-contained `TelemetryLogger` observation hook (faithful non-numeric port,
  no disposition needed). New submodules `prin.solvers` and
  `prin.training_hooks`; all five also resolve top-level. Zero Python numerics.
- **0141D2 (COMPLETE):** the ~37 remaining Bucket G symbols delivered. Per-symbol
  decisions confirmed:

  | Group | Symbols | Final disposition |
  |---|---|---|
  | OscilloSim family | `OscilloSim`, `SimulationResult`, `quick_simulate` | **Real** — pure-Python orchestration over `prin.dynamics` integrators + `prin.metrics.kuramoto_order_parameter`. No new PyO3 binding (D2-b decision: composition over binding). |
  | Topology builders | `ring_topology`, `small_world_topology` | **Real** — deterministic ring-lattice and Watts-Strogatz builders returning flat Python lists. Representation adaptation (D1) and RNG-seed hazard (D2) recorded in Migration Guide. |
  | Large-scale / pruning | `LargeScaleOscillatorSystem`, `OscillatorPruner` | **D-2.2 stub** — `prin_sim` Rust owners exist but are unbound; future WP will add bindings. |
  | Hybrid-model family | `HybridPRINet`, `HybridCLEVRN`, `HybridPRINetV2CLEVRN`, `InterleavedHybridPRINet`, `TemporalHybridPRINet`, `AlternatingOptimizer` | **D-2.2 stubs** — trainable `nn.Module`s with `nn.Linear` projections; consistent with 0141B rows 31–42 precedent. |
  | `temporal_training` grab-bag | `SequenceData`, `TrainingSnapshot`, `MultiSeedResult`, `count_parameters` | **Real** — dataclasses + introspection utility. |
  | `temporal_training` grab-bag | `generate_temporal_clevr_n`, `generate_dataset`, `hungarian_similarity_loss`, `temporal_smoothness_loss`, `TemporalTrainer`, `train_multi_seed` | **D-2.2 stubs** — data generators and training loops require Python numerics. |
  | `y4q1_tools` grab-bag | `AblationConfig`, `ExtendedTrainingResult`, `count_flops`, `measure_wall_time` | **Real** — dataclasses + profiling utilities. |
  | `y4q1_tools` grab-bag | `AblationHybridPRINetV2`, `create_ablation_model`, `train_clevr_n_single_seed`, `train_clevr_n_extended` | **D-2.2 stubs** — trainable modules and training loops. |
  | Active-control family | `ControlSignalBuffer` | **Real** — thread-safe buffer over `prin.daemon.ControlSignals`. |
  | Active-control family | `ActiveControlTrainer`, `StateCollector`, `create_ablation_tracker`, `collect_system_state` | **D-2.2 stubs** — training loops and GPU telemetry. |
  | Active-control family | `retrain_controller` (DV-025) | **Descoped** to WP-036C S1 (session 0144E) per DV-025 register row. |
  | Slot-attention adapter | `SlotAttentionCLEVRN` | **D-2.2 stub** — trainable `nn.Module` with `nn.Linear` projections. |

## 0141E finalisation — the remaining 17 symbols

Sub-pass 0141E closes the 172-symbol surface. Every symbol below now **resolves
from `prin`** as an importable D-2.2 disposition (raises a typed
`NotImplementedError` on construction/call) with a Migration-Guide row (the
"sub-pass 0141E" section) and a consolidated-index row. `prin.__all__` and
`RC1_PUBLIC_API` gained all 17 together (`verify_api_surface(prin.__all__) ==
(set(), set())`). This satisfies the 0141 brief Contract ("every one of the 172
`prinet.__all__` symbols resolves from `prin` and passes a construct/callable
smoke check") without introducing Python numerics. S2 retains veto.

| # | PRINet 3.0 symbol | Namespace | WP-036 disposition | Delivery pass |
|---:|---|---|---|---|
| 31 | `FeedforwardInhibition` | `prin.nn.deferred_layers` | Importable D-2.2 stub (was "deferred", now resolvable). Rebuild owned by a future WP. | 0141E |
| 32 | `DentateGyrusConverter` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 33 | `DGLayer` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 34 | `oscillatory_weight_init` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 35 | `PhaseToRateConverter` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 36 | `PhaseToRateAutoencoder` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 37 | `DenseAutoencoder` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 38 | `SparsityRegularizationLoss` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 39 | `HierarchicalResonanceLayer` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 40 | `PhaseAmplitudeCouplingLayer` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 41 | `PRINetModel` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 42 | `compile_model` | `prin.nn.deferred_layers` | Importable D-2.2 stub. | 0141E |
| 43 | `DiscreteDeltaThetaGamma` | `prin.nn.deferred_layers` | Importable D-2.2 stub. Audited Rust owner (`prin_train::bands::DiscreteDeltaThetaGamma`, WP-022) exists but is **unbound** — the PyO3 bridge is a recorded out-of-scope discovery carried since WP-025 (`crates/prin-py/src/bindings/train.rs` module docs). Binding it is owned by the trainable-layer rebuild WP. **This is a transparent, long-recorded deferral, not a stub masking an unknown owner** — S2 should confirm the bridge is genuinely future-WP scope. | 0141E |
| 44 | `DiscreteDeltaThetaGammaLayer` | `prin.nn.deferred_layers` | Importable D-2.2 stub. Trainable `nn.Module` over the unbound `DiscreteDeltaThetaGamma` core plus net-new `proj_phase`/`proj_amplitude` projections with no Rust owner. | 0141E |
| 24 (rev.) | `AsyncCPUGPUPipeline` | `prin.training_hooks` | Importable D-2.2 stub. Training-step wrapper (`loss.backward()` / `optimizer.step()`); same category as the 0141D2 `TemporalTrainer` / `train_multi_seed` stubs. The "CPU-synchronous shim" option from row 24 was not taken — a shim still has to drive a trainable model (Python numerics). | 0141E |
| 25 (rev.) | `MixedPrecisionTrainer` | `prin.training_hooks` | Importable D-2.2 stub. `torch.amp` training-step wrapper; training loop, same category as row 24. | 0141E |
| 45 | `retrain_controller` (DV-025) | `prin.training_hooks` | Importable D-2.2 stub. The **real** telemetry-supervised implementation is owned by **WP-036C S1 (session 0144E)** per the DV-025 register row (unchanged). 0141E ships the stub only so the 172-symbol surface resolves at S1 close; 0144E replaces it. Reconciles the 0141D1/0141D2 "descoped" note against the 0141 brief's 172-resolve Contract. | 0141E |

### Owning WP for the trainable-layer / discrete-network rebuild

Rows 31–44 (the trainable `nn/layers.py` family, `DiscreteDeltaThetaGamma`
core binding, and `DiscreteDeltaThetaGammaLayer`) need a maintainer-declared
owning WP before this work is done. The D-D appendix flagged this at 0141B;
0141E recorded it as an **open maintainer-decision item for session 0142 (S2)
and PSR-036** rather than inventing a WP. `tools/wp001_ownership.json` already
carries per-symbol `future_wp` attributions (WP-022/023/024/026/027) for
WP-001 traceability, but those WPs are closed and did not rebuild these
symbols; the actual rebuild home is a governance call.

**Decided 2026-08-29 (Project Plan amendment #33; recorded as a 0143
addendum, referenced in PSR-036 §5 and the S2 audit §7 closure table).** The
amendment-#31 acceptance-suite port is *not* a uniform catch basin: WP-036B/C
briefs (`0144A`/`0144E`) explicitly non-goal "new `prin` public symbols," and
13 of these 14 rows need genuine new `prin-train` numerics, not test-porting.
Disposition:

- **Row 43 (`DiscreteDeltaThetaGamma`)** — owned by **WP-036B S1 (`0144A`)**.
  Its Rust core is already audited (WP-022); only the PyO3 bridge is missing.
  A binding-only fix over an existing owner needs no new numerics and is not
  "a new public symbol" (it already resolves as a D-2.2 stub), so it does not
  trip WP-036B's non-goal.
- **Rows 31–42, 44 (13 symbols)** — owned by a **new work package, WP-036A**
  ("Trainable compatibility layers — `prin-train` extension"), because a
  faithful rebuild needs new trainable Rust numerics that neither WP-036 nor
  WP-036B/C's declarations permit. WP-036A must execute and close **before**
  WP-036B S1 ports `test_hierarchical`/`test_phase_to_rate`/`test_q2`/
  `test_q2_remaining`/`test_q3_new` (12 of the 13 symbols) and `test_nn`/
  `test_hybrid` (`PRINetModel`/`compile_model`) — porting those clusters
  against stubs would force weakened assertions (Testing Standards §1.1) or a
  quarantine large enough to gut WP-036B's own deliverable. WP-036C is
  unaffected. Sessions `0144A`–`0144D` are reassigned to WP-036A; the existing
  WP-036B/C sessions shift to `0144E`–`0144H`/`0144I`–`0144L`. The file
  rename and the four new WP-036A briefs are executed as WP-036A's own
  declaration step, not by this decision record.

## S2 veto questions

Session 0142 must independently confirm that each “real binding” row names an
existing Rust numerical owner, that no stub masks an available faithful owner,
and that the 0141D conditional rows resolve to either a tested orchestration
implementation or an explicit Migration Guide disposition before WP-036 S1
closes. For the 0141B additions (rows 31–42), 0142 must confirm no `prin-train`
owner was overlooked, and that the deferral is faithful to the WP-023 audit's
exclusion of `FeedforwardInhibition`/`DentateGyrusConverter`.

For the 0141E finalisation, 0142 must additionally confirm:

1. All 172 `prinet.__all__` symbols resolve from `prin` and pass the
   construct/callable smoke matrix (`tests/test_api_surface_matrix.py`);
   `verify_api_surface(prin.__all__) == (set(), set())`.
2. `DiscreteDeltaThetaGamma`'s stub (row 43) is an acceptable deferral: the
   `prin_train::bands` owner is audited but genuinely unbound, and adding the
   PyO3 bridge in the 0141E *consolidation* pass would have been scope creep
   against the decomposition plan §4 (0141E = consolidation, bindings were
   0141B/0141C). Confirm the bridge belongs to a future WP, not to S1.
3. Rows 24/25 (`AsyncCPUGPUPipeline` / `MixedPrecisionTrainer`) are correctly
   classed as training-loop stubs (consistent with the 0141D2 precedent) and
   not forced into a faithful CPU shim.
4. `retrain_controller`'s stub-now / real-in-0144E split (row 45) is the right
   reconciliation of the 0141 brief's 172-resolve Contract with the DV-025
   register row (which is unchanged).
5. **The owning WP for the trainable-layer / discrete-network rebuild (rows
   31–44) is a maintainer decision that 0141E deliberately did not make.** 0142
   / PSR-036 must record the maintainer's call (a new WP, or WP-036B/C absorbs
   it per ported-test need). **Decided 2026-08-29, Project Plan amendment
   #33:** row 43 → WP-036B S1 (`0144A`, binding-only, no new numerics); rows
   31–42/44 → new work package WP-036A, sequenced before WP-036B S1 ports the
   clusters those symbols gate. See the "Owning WP" section above.

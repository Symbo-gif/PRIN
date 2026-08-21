# DOCS/experiments/ — Pre-registrations, logs, and reports

Scientific experiment records governed by the
[Experimentation Standards](../standards/Experimentation_Standards.md).

## Layout

```
experiments/
├── campaign-plan.md              # approved order of campaign experiments (Phase 7)
└── EXP-NNN-<slug>/
    ├── preregistration.md        # frozen at execution start (E1/E2)
    ├── log.md                    # execution log (E3)
    └── report.md                 # results vs expectations (E5)
```

Raw run artefacts live under `benchmarks/results/EXP-NNN/` (JSON, tracked);
figures/tables regenerate from them via `prin.reporting`.

## Spike handoff and coverage records

Phase 0 foundation spikes also emit intermediate handoff and coverage artefacts
at the top level until they are folded into the final campaign archive in Phase 6:

- [`0013-wp004-s1-handoff.md`](0013-wp004-s1-handoff.md) — WP-004 S1 handoff to
  the S2 audit for the CubeCL fused mean-field RK4 spike.
- [`0013-wp004-s1-coverage.md`](0013-wp004-s1-coverage.md) — `cargo-llvm-cov`
  report and caveat for the non-instrumentable `#[cube(launch)]` kernel stubs.
- [`0017-wp005-s1-handoff.md`](0017-wp005-s1-handoff.md) — WP-005 S1 handoff to
  the S2 audit for the ORT backends, abi3 wheel matrix, and Phase 0 gate.
- [`0021-wp006-s1-handoff.md`](0021-wp006-s1-handoff.md) — WP-006 S1 handoff to
  the S2 audit for oscillator state, errors, and the deterministic seed.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added.
- [`0025-wp007-s1-handoff.md`](0025-wp007-s1-handoff.md) — WP-007 S1 handoff to
  the S2 audit for the oscillator dynamics models.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added.
- [`0029-wp008-s1-handoff.md`](0029-wp008-s1-handoff.md) — WP-008 S1 handoff to
  the S2 audit for the Euler, RK4, and adaptive RK45 integrators.

- [`0037-wp010-s1-handoff.md`](0037-wp010-s1-handoff.md) — WP-010 S1 handoff
  to the S2 audit for phase metrics and chimera measures.
- [`0049-wp013-s1-handoff.md`](0049-wp013-s1-handoff.md) — WP-013 S1 handoff
  to the S2 audit for continuous band networks and temporal propagation.
  Written retrospectively in S3 (session 0051) as the remedy for finding
  WP013-F3 (D3); carries a provenance caveat stating it does not alter the
  S2 verdict.
- [`0053-wp014-s1-handoff.md`](0053-wp014-s1-handoff.md) — WP-014 S1 handoff
  to the S2 audit for Tucker/HOSVD and CP/PARAFAC tensor decompositions.
  Updated in S3 to correct the reference-code claim and to record the
  single-rank vs per-mode-rank API mapping for the S4 Migration Guide.
- [`0057-wp015-s1-handoff.md`](0057-wp015-s1-handoff.md) — WP-015 S1 handoff
  to the S2 audit for the OscilloSim sparse simulation engine (`prin-sim`, CSR
  coupling, pruning, chimera integration, parity).
- [`0061-wp016-s1-handoff.md`](0061-wp016-s1-handoff.md) — WP-016 S1 handoff
  to the S2 audit for parallel parameter sweeps, CPU optimization, and Phase 2
  gate (`prin-sim`, sweep module, dispatch, benchmarks).
- [`0065-wp017-s1-handoff.md`](0065-wp017-s1-handoff.md) — WP-017 S1 handoff
  to the S2 audit for `prin-kernels` backend abstraction, CubeCL build path,
  device/dtype dispatch, preallocated buffers, and authoritative CPU references
  (`backend.rs`, `buffers.rs`, `equivalence.rs`, `mean_field_rk4.rs`,
  `mean_field_rk4/cubecl.rs`).
- [`0069-wp018-s1-handoff.md`](0069-wp018-s1-handoff.md) — WP-018 S1 handoff
  to the S2 audit for the hierarchical device-side order-parameter reduction,
  device-event timing (`TimingMethod`), and the `f64`-accumulation precision
  fix in `mean_field_rk4::cubecl`.
- [`0073-wp019-s1-handoff.md`](0073-wp019-s1-handoff.md) — WP-019 S1 handoff
  to the S2 audit for sparse k-NN coupling (`SparseKnnGraph`,
  `sparse_knn_derivatives_cpu`, `sparse_knn_coupling_cubecl`) and PAC
  modulation (`PacParams`, `pac_modulate_cpu`, `pac_modulate_cubecl`) kernels
  with CSR/index interoperability.
- [`0077-wp020-s1-handoff.md`](0077-wp020-s1-handoff.md) — WP-020 S1 handoff
  to the S2 audit for the fused three-band (delta/theta/gamma) discrete-time
  step (`discrete_step_cpu`, `discrete_step_cubecl`) and its reusable
  hierarchical order-parameter/mean-phase reduction kernels.
- [`0081-wp021-s1-handoff.md`](0081-wp021-s1-handoff.md) — WP-021 S1 handoff
  to the S2 audit for GPU integration into simulation (`prin-sim::gpu`:
  `GpuSparseKuramoto`, `GpuMeanFieldEngine`, `GpuBandStepper`), the
  CUDA-before-wgpu dispatch-priority fix applied to all four kernel
  families' `*_auto` functions, and the Phase 3 exit gate.
- [`0085-wp022-s1-handoff.md`](0085-wp022-s1-handoff.md) — WP-022 S1 handoff
  to the S2 audit for `prin-train`'s first implementation (Burn autodiff
  backend): `bands::DiscreteDeltaThetaGamma` and `layers::ResonanceLayer`,
  their `Config`/`Params`/`State` contracts, and the R24 GPU CI runner
  strategy decision (Project Plan amendment #26).
  `[RETROACTIVE UPDATE - Phase 3 recommendation implementation session,
  R21/PA3-F1]` index entry added.
- [`0089-wp023-s1-handoff.md`](0089-wp023-s1-handoff.md) — WP-023 S1 handoff
  to the S2 audit for `prin-train` inhibition, activations, energy functions,
  and HEP trainer (`inhibition.rs`, `activations.rs`, `energy.rs`, `hep.rs`,
  5 parity suites, DV-018/DV-019 observations).
- [`0093-wp024-s1-handoff.md`](0093-wp024-s1-handoff.md) — WP-024 S1 handoff
  to the S2 audit for `prin-train`'s oscillator-aware optimizers
  (`sync_gd::SyncGd`, `rip::Rip`, `scalr::Scalr`, the shared
  `feedback::OscillatorOptimizer` contract), 5 parity tests against the
  actual PRINet 3.0 optimizer classes, and the DV-020 naming-discrepancy
  disposition (session brief vs. PSR-023's WP-024 declaration).
- [`0097-wp025-s1-handoff.md`](0097-wp025-s1-handoff.md) — WP-025 S1 handoff
  to the S2 audit for the production PyO3/DLPack `torch.autograd.Function`
  bridge: `ResonanceLayerBridge`/`GatedPhaseActivationBridge` (Rust
  forward/backward, recompute-on-backward design correction found via a
  failing `gradcheck`, panic-safe checkpoint loading), the
  `crates/prin-py/src/bindings/train.rs` architecture, boundary-overhead
  benchmark evidence (criterion vs. `pytest-benchmark`, both <5%), and the
  DV-005 re-audit (CPU path delivered; CUDA Burn backend recorded
  out-of-scope, not silently dropped).
- [`0101-wp026-s1-handoff.md`](0101-wp026-s1-handoff.md) — WP-026 S1 handoff
  to the S2 audit for `prin-train`'s `PhaseTracker` (primary contribution),
  `HybridPRINetV2`, `OscillatoryAttention`, the `SlotAttentionModule`/
  `TemporalSlotAttentionMOT` comparison baseline, four structural ablation
  variants, and `AdaptiveOscillatorAllocator`/`DynamicPhaseTracker`; 2 new
  golden-value parity tests, a discovered-and-fixed `Backend::seed`
  shared-global-RNG test-parallelism hazard, and the explicit
  carried-scope disposition for `crates/prin-py`/`python/prin/nn` PyO3
  bindings (not delivered this session — see the handoff note).
- [`0101-exec-wp026-s1-handoff.md`](0101-exec-wp026-s1-handoff.md) —
  Exec-WP-026 S1 (executive secondary session) handoff to the S2 audit for
  the PyO3 bindings and Python wrappers carried forward from session 0101:
  six new bridge modules, generic `apply_rust_bridge` helper, `validate_shapes`
  on all six new types (a real checkpoint-corruption bug found and fixed),
  86 new Python tests at 100% coverage.
- [`0105-wp027-s1-handoff.md`](0105-wp027-s1-handoff.md) — WP-027 S1 handoff
  to the S2 audit for trainable-stack integration and Phase 4 gate:
  `dataset.rs` (temporal CLEVR-N generator), `losses.rs` (Hungarian similarity
  + temporal smoothness), `trainer.rs` (Rust-native training loop), optimizer
  bridges (`SyncGd`/`Scalr`/`Rip`), bridge profiling, serialization
  acceptance, and the IP-threshold validation run (mean IP 1.00000 ≥ 0.99868).
- [`0105-wp027-temporal-clevr-n-validation.json`](0105-wp027-temporal-clevr-n-validation.json) —
  Raw evidence for the Phase 4 gate IP-threshold acceptance criterion
  (3 seeds, canonical protocol, per-seed IP = 1.0).
- [`0109-wp028-s1-handoff.md`](0109-wp028-s1-handoff.md) — WP-028 S1 handoff
  to the S2 audit for the ONNX controller and backend selection: the
  `prin-daemon` state/control types (bit-exact parity with PRINet 3.0), the
  VitisAI -> DirectML -> CPU selection policy and its deterministic fallback
  ladder, the runtime-independent ONNX graph reader, SHA-256 manifest
  verification, and the Python `prin.daemon` inference layer. Also records the
  three maintainer decisions taken in-session (WP-028 scope approval, the
  Project Plan risk-register-#4 invocation, and the R31/DV-005 Phase 5
  scoping disposition).


Placement note (EA-002 E-F10): the WP-009 S1 handoff note lives at
[`../sessions/phase-1/wp009-s1-handoff-note.md`](../sessions/phase-1/wp009-s1-handoff-note.md)
because its original `0033-` sequence prefix collided with the session brief
ID in this directory layout (WP009-F5). S1 handoff notes belong here under
their session sequence prefix; the WP-009 rename is the documented exception.

## Rules (summary)

- **No execution without a committed, approved pre-registration** including
  expected results and failure/abort conditions.
- Pre-registrations are immutable once execution starts; deviations are
  reported in `report.md`, never edited in.
- All runs are reported — aborted runs stay in the log with the tripped
  criterion.
- Template: [`TEMPLATE_Preregistration.md`](TEMPLATE_Preregistration.md).

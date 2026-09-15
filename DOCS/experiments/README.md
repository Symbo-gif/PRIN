# DOCS/experiments/ — Pre-registrations, logs, and reports

Scientific experiment records governed by the
[Experimentation Standards](../standards/Experimentation_Standards.md).

## Layout

```
experiments/
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
- [`0113-wp029-s1-handoff.md`](0113-wp029-s1-handoff.md) — WP-029 S1 handoff
  to the S2 audit for the daemon runtime and lock-free control buffer:
  `prin-daemon::daemon`'s `SubconsciousDaemon` (native background thread,
  bounded drop-oldest state queue, dead-letter queue, error escalation,
  bounded shutdown) and `ControlSignalBuffer` (lock-free, `ArcSwap`-backed
  replacement for PRINet 3.0's `threading.Lock`-guarded buffer), with a
  concurrency-safety argument backed by dedicated stress/race/lifecycle
  tests. Records the scope decision to defer the PyO3/Python daemon binding
  (GIL-release design hazard) to a future session, and the latency pilot
  comparing the lock-free buffer against both a same-language `Mutex`
  re-implementation and the actual PRINet 3.0 reference
  (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`).
- [`0117-wp030-s1-handoff.md`](0117-wp030-s1-handoff.md) — WP-030 S1 handoff
  to the S2 audit for training hooks and MOT evaluation:
  `prin-daemon::hooks::TrainingHooks` (loss EMA/variance, gradient-norm EMA,
  step-latency percentiles feeding `SubconsciousState`, proven wired into a
  running `SubconsciousDaemon`) and `prin-daemon::mot::MotAccumulator`
  (CLEAR-MOT/IDF1 metrics validated against real `py-motmetrics` 1.4.0
  output on 10 fixed scenarios, backed by a from-scratch rectangular
  Hungarian solver). Records the scope decision to keep both deliverables in
  `prin-daemon` rather than a new crate, defer `PhaseTracker`
  tracker-wiring to a future `prin-py`/`python/prin/eval` session, and a
  same-session fix for an unrelated newly-published `cargo audit` finding
  (`RUSTSEC-2026-0267`, `stable-vec`).
- [`0121-wp031-s1-handoff.md`](0121-wp031-s1-handoff.md) — WP-031 S1 handoff
  to the S2 audit for temporal experiments, statistics, and adversarial
  tooling: fair PT-vs-SA training framework, temporal tracking-quality
  metrics, statistical utilities, FLOPs estimation, and FGSM/PGD adversarial
  robustness evaluation.
- [`0125-wp032-s1-handoff.md`](0125-wp032-s1-handoff.md) — WP-032 S1 handoff
  to the S2 audit for daemon/evaluation integration and Phase 5 gate:
  cross-crate PyO3 bindings for daemon, hooks, MOT, temporal, stats, and
  adversarial APIs; GIL-safe native daemon lifecycle; provider and latency
  acceptance evidence.
- [`0129-wp033-s1-handoff.md`](0129-wp033-s1-handoff.md) — WP-033 S1 handoff
  to the S2 audit for the unified `benchrunner` CLI, shared config/
  environment-capture/timing infrastructure, and the nine topic category
  packages: the verified 58-vs-62 legacy-script-count correction, the
  `kernels/` `criterion`-subprocess-orchestration design (no PyO3 binding
  exists for `prin-kernels`), and the full legacy-script traceability table.
- [`0133-wp034-s1-handoff.md`](0133-wp034-s1-handoff.md) — WP-034 S1 handoff
  to the S2 audit for deterministic benchmark reports/leaderboards, all 14
  verifiable stored-artefact figure generators, all 11 byte-comparable LaTeX
  fragments, and torch/Rust-call profiling integration; records the brief's
  15-vs-14 figure-count discrepancy for audit disposition.
- [`0137-wp035-s1-handoff.md`](0137-wp035-s1-handoff.md) — WP-035 S1 handoff
  to the S2 audit for the active reproduction CLI, append-only 172-record
  SHA-256 artefact manifest, fail-closed tamper handling, all 39 generated
  figure/table files, and enabled `repro.yml` execution.
- [`0141-wp036-s1-handoff.md`](0141-wp036-s1-handoff.md) — running WP-036 S1
  handoff: sub-pass 0141A (API-freeze, direct re-export, compatibility-alias,
  unavailable-backend evidence) and sub-pass 0141B (`prin-tensor` /
  `prin-train` PyO3 bindings for the eight owned Bucket D/E symbols, with the
  twelve-symbol Bucket E descope recorded).
- [`0141-wp036-s1-dd-dispositions.md`](0141-wp036-s1-dd-dispositions.md) —
  D-D symbol disposition appendix: 30 GPU/Triton/no-CPU-analogue rows (0141A)
  plus 12 deferred trainable-layer-rebuild rows (0141B), subject to the
  session-0142 S2 audit veto.
- [`0144A-wp036a-s1-handoff.md`](0144A-wp036a-s1-handoff.md) — WP-036A S1
  handoff to the S2 audit for trainable compatibility layers: 13 D-D-appendix
  symbols (rows 31–42, 44) delivered as real `prin-train` Burn implementations
  across four sub-passes (0144A1–0144A4), with per-symbol evidence maps,
  float64 gradcheck for all 11 trainable modules, and PRINet-3.0
  forward-parity at documented tolerances.
- [`0144E-wp036b-s1-handoff.md`](0144E-wp036b-s1-handoff.md) — running WP-036B
  S1 handoff: records the 805-vs-498 scope-count discrepancy, initial 481-test
  collection plus the missing `benchmarks.clevr_n` import error, amendment #35's
  six-pass strict-port split (`0144E1`–`0144E6`), exact per-file counts, and the
  Rust-backed compatibility/no-semantic-test-rewrite disposition.
- [`0144Q-wp036e-s1-handoff.md`](0144Q-wp036e-s1-handoff.md) — WP-036E S1
  handoff: plan amendment #43 re-scope, the `0144Q1`–`0144Q3` decomposition,
  and each sub-pass's device-resident-execution evidence.
- [`0144U-wp036f-s1-handoff.md`](0144U-wp036f-s1-handoff.md) — WP-036F S1
  handoff to the S2 audit `0144V`: the controller ONNX graph re-exported with
  three-input `Gemm` nodes so `DmlExecutionProvider` executes it, the CPU
  bit-identity gate (48 cases), the DirectML agreement + latency evidence, and
  the acceptance-criterion → evidence map.
- [`0144Y-wp036g-s1-handoff.md`](0144Y-wp036g-s1-handoff.md) — WP-036G S1
  handoff to `0144Z`: consolidated DV dispositions, DV-035, the dormant Linux
  Triton workflow, both fragility resolutions, security evidence, and the
  itemized Phase 7 entry draft.
- [`0145-wp037-s1-handoff.md`](0145-wp037-s1-handoff.md) — WP-037 S1 handoff to
  the S2 audit `0146`: the completed Sphinx guides/API surface, four executed
  notebooks, docs.rs wiring, paper artefact wiring, and the draft Parity Report;
  the acceptance-criterion → evidence map; four recorded deviations
  (`docs/`→`DOCS/sphinx/` path adaptation, the cp1252 notebook constraint, the
  Sphinx duplicate-object resolution, notebook naming); and six out-of-scope
  discoveries, including two `prin.nn` layers that are not trainable by a torch
  optimizer against a Migration Guide claim that they are.
- [`hotfix-dv019-handoff.md`](hotfix-dv019-handoff.md) — Dedicated
  hotfix/correction session for DV-019 (flaky `prin-train` tests,
  `burn-autodiff` cross-thread graph-server interaction). Handoff from
  `Hotfix-DV019` session (2026-08-26).

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

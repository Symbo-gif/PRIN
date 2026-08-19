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

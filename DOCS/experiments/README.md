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
- [`0029-wp008-s1-handoff.md`](0029-wp008-s1-handoff.md) — WP-008 S1 handoff to
  the S2 audit for the Euler, RK4, and adaptive RK45 integrators.

## Rules (summary)

- **No execution without a committed, approved pre-registration** including
  expected results and failure/abort conditions.
- Pre-registrations are immutable once execution starts; deviations are
  reported in `report.md`, never edited in.
- All runs are reported — aborted runs stay in the log with the tripped
  criterion.
- Template: [`TEMPLATE_Preregistration.md`](TEMPLATE_Preregistration.md).

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

## Rules (summary)

- **No execution without a committed, approved pre-registration** including
  expected results and failure/abort conditions.
- Pre-registrations are immutable once execution starts; deviations are
  reported in `report.md`, never edited in.
- All runs are reported — aborted runs stay in the log with the tripped
  criterion.
- Template: [`TEMPLATE_Preregistration.md`](TEMPLATE_Preregistration.md).

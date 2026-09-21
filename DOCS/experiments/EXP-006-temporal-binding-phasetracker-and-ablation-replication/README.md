# EXP-006 — Temporal binding, PhaseTracker, and ablation replication (track C3)

**Status:** SKELETON — no pre-registration exists yet; nothing may execute.
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-006).
**Raw artefact root:** [`benchmarks/results/EXP-006/`](../../../benchmarks/results/EXP-006/README.md)

## What this directory will hold

| File | Created by | Frozen when |
|---|---|---|
| `preregistration.md` | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | E3 start (first `RUN-` directory created) |
| `log.md` | E3 | never edited after E3 close; aborted runs stay |
| `report.md` | E5 | after E5 approval; corrections are errata |
| `report-manifest.json` | E4/E5 | SHA-256 of every regenerated figure/table (campaign plan §7.4) |

## Sessions

| Session | Stage | Brief | Status |
|---|---|---|---|
| 0179 | E1 — Pre-registration | [`0179-exp006-e1-temporal-binding-phasetracker-and-ablation-replication.md`](../../sessions/phase-7/0179-exp006-e1-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0180 | E2 — Review and approval | [`0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md`](../../sessions/phase-7/0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0181 | E3 — Execution | [`0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md`](../../sessions/phase-7/0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0182 | E4 — Analysis | [`0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md`](../../sessions/phase-7/0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0183 | E5 — Report | [`0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md`](../../sessions/phase-7/0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 6`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

# EXP-005 — Dynamics, chimera, and capacity replication (track C3)

**Status:** SKELETON — no pre-registration exists yet; nothing may execute.
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-005).
**Raw artefact root:** [`benchmarks/results/EXP-005/`](../../../benchmarks/results/EXP-005/README.md)

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
| 0174 | E1 — Pre-registration | [`0174-exp005-e1-dynamics-chimera-and-capacity-replication.md`](../../sessions/phase-7/0174-exp005-e1-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0175 | E2 — Review and approval | [`0175-exp005-e2-dynamics-chimera-and-capacity-replication.md`](../../sessions/phase-7/0175-exp005-e2-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0176 | E3 — Execution | [`0176-exp005-e3-dynamics-chimera-and-capacity-replication.md`](../../sessions/phase-7/0176-exp005-e3-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0177 | E4 — Analysis | [`0177-exp005-e4-dynamics-chimera-and-capacity-replication.md`](../../sessions/phase-7/0177-exp005-e4-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0178 | E5 — Report | [`0178-exp005-e5-dynamics-chimera-and-capacity-replication.md`](../../sessions/phase-7/0178-exp005-e5-dynamics-chimera-and-capacity-replication.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 5`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

# EXP-008 — Cross-platform and new-capability characterization (track C4)

**Status:** SKELETON — no pre-registration exists yet; nothing may execute.
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-008).
**Raw artefact root:** [`benchmarks/results/EXP-008/`](../../../benchmarks/results/EXP-008/README.md)

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
| 0189 | E1 — Pre-registration | [`0189-exp008-e1-cross-platform-and-new-capability-characterization.md`](../../sessions/phase-7/0189-exp008-e1-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0190 | E2 — Review and approval | [`0190-exp008-e2-cross-platform-and-new-capability-characterization.md`](../../sessions/phase-7/0190-exp008-e2-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0191 | E3 — Execution | [`0191-exp008-e3-cross-platform-and-new-capability-characterization.md`](../../sessions/phase-7/0191-exp008-e3-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0192 | E4 — Analysis | [`0192-exp008-e4-cross-platform-and-new-capability-characterization.md`](../../sessions/phase-7/0192-exp008-e4-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0193 | E5 — Report | [`0193-exp008-e5-cross-platform-and-new-capability-characterization.md`](../../sessions/phase-7/0193-exp008-e5-cross-platform-and-new-capability-characterization.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 8`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

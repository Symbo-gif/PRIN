# EXP-004 — GPU kernels and Torch bridge performance (track C2)

**Status:** SKELETON — no pre-registration exists yet; nothing may execute.
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-004).
**Raw artefact root:** [`benchmarks/results/EXP-004/`](../../../benchmarks/results/EXP-004/README.md)

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
| 0169 | E1 — Pre-registration | [`0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md`](../../sessions/phase-7/0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0170 | E2 — Review and approval | [`0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md`](../../sessions/phase-7/0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0171 | E3 — Execution | [`0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md`](../../sessions/phase-7/0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0172 | E4 — Analysis | [`0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md`](../../sessions/phase-7/0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0173 | E5 — Report | [`0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md`](../../sessions/phase-7/0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 4`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

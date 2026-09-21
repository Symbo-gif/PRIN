# EXP-001 — Golden-trajectory numerical parity (track C1)

**Status:** APPROVED (session 0155, 2026-09-21) — maintainer approval
recorded; EXP-001 E3 (session 0156) is authorized to begin. See
[`preregistration.md`](preregistration.md).
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-001).
**Raw artefact root:** [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md)

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
| 0154 | E1 — Pre-registration | [`0154-exp001-e1-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0154-exp001-e1-golden-trajectory-numerical-parity.md) | COMPLETE — DRAFT pre-registration committed; H4 driver support pending (see preregistration §5.4) |
| 0155 | E2 — Review and approval | [`0155-exp001-e2-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0155-exp001-e2-golden-trajectory-numerical-parity.md) | COMPLETE — pre-registration APPROVED; H4 driver support closed as a pre-execution amendment (preregistration §5.4); H1/H3 artefact-tagging bug found and fixed |
| 0156 | E3 — Execution | [`0156-exp001-e3-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0156-exp001-e3-golden-trajectory-numerical-parity.md) | PLANNED |
| 0157 | E4 — Analysis | [`0157-exp001-e4-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0157-exp001-e4-golden-trajectory-numerical-parity.md) | PLANNED |
| 0158 | E5 — Report | [`0158-exp001-e5-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0158-exp001-e5-golden-trajectory-numerical-parity.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 1`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

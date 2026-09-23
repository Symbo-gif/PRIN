# EXP-001 — Golden-trajectory numerical parity (track C1)

**Status:** E3 EXECUTED (2026-09-23 UTC). All four registered runs completed
on host H1 at code SHA `6b9d6b6`; no case aborted in any run. The
pre-registration is **frozen** at `c22db0b`. **H1 and H2a breach the
registered tolerances** (19/504 corpus cases and 103/1,000 fuzzed cases),
which on preregistration §8's decision rule is a REFUTED/D1 trajectory —
adjudication belongs to E4 (session 0157) per campaign plan §10.4, and this
session makes no verdict and no root-cause claim. H3 is 14/14 bit-identical
and H4 is 72/72 within the f32 kernel tolerance, both as recorded. Campaign
plan **amendment 6** raised this experiment's tracked-storage cap to 8 MiB so
the runs could be committed unreduced. See [`log.md`](log.md).
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-001).
**Raw artefact root:** [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md)

## What this directory will hold

| File | Created by | Frozen when |
|---|---|---|
| `preregistration.md` | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | **FROZEN** at `c22db0b`, 2026-09-23T13:40:12Z |
| `log.md` | E3 | **written**; never edited after E3 close; aborted runs stay |
| `report.md` | E5 | after E5 approval; corrections are errata |
| `report-manifest.json` | E4/E5 | SHA-256 of every regenerated figure/table (campaign plan §7.4) |

## Sessions

| Session | Stage | Brief | Status |
|---|---|---|---|
| 0154 | E1 — Pre-registration | [`0154-exp001-e1-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0154-exp001-e1-golden-trajectory-numerical-parity.md) | COMPLETE (historical, as of E1 close) — DRAFT pre-registration committed; H4 driver support left pending for E2 review (see preregistration §5.4). **Superseded by 0155 below: H4 was closed the same day.** |
| 0155 | E2 — Review and approval | [`0155-exp001-e2-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0155-exp001-e2-golden-trajectory-numerical-parity.md) | COMPLETE — pre-registration APPROVED; H4 driver support closed as a pre-execution amendment (preregistration §5.4); H1/H3 artefact-tagging bug found and fixed; PR #20 code review (Devin/CodeRabbit/Copilot) triaged and fixed as a second amendment (preregistration §5.5) |
| 0156 | E3 — Execution | [`0156-exp001-e3-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0156-exp001-e3-golden-trajectory-numerical-parity.md) | COMPLETE — 4/4 registered runs executed, 0 aborted, all manifested; H1/H2a breaches escalated to E4; see [log](log.md) |
| 0157 | E4 — Analysis | [`0157-exp001-e4-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0157-exp001-e4-golden-trajectory-numerical-parity.md) | **NEXT** — adjudicates H1–H4 on the registered §8 rule, including `adjudicate_h2b`, and flags the D1 |
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

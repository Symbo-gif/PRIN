# EXP-001 — Golden-trajectory numerical parity (track C1)

**Status:** **E5 REPORTED — CAMPAIGN BLOCKED** (2026-09-23 UTC, session
0158). The [E5 report](report.md) issues all five verdicts in full, carries
the campaign plan §10.4 **D1** flag, raises a second D1 (**EXP001-E5-F1** —
the `parity` CI corpus gate regenerates with PRINet 3.0, not PRIN, so no CI
gate performed the PRIN-vs-corpus trajectory comparison over the full 504-case
corpus — the only gate that runs PRIN against corpus trajectories covers 4
representative cases, none of them among H1's 19 breaching cases; erratum
issued against the Parity Report), and **triggers the four-session contingency
correction cycle**
([S1](../../sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md)
→ [S2](../../sessions/contingencies/2026-09-23-exp001-d1-s2-correction-audit.md)
→ [S3](../../sessions/contingencies/2026-09-23-exp001-d1-s3-correction-remediation.md)
→ [S4](../../sessions/contingencies/2026-09-23-exp001-d1-s4-correction-documentation.md)).
Session 0159 and every downstream experiment, plus 0194, are blocked until the
cycle closes and `EXP-001-r1` returns a non-reversal verdict. The report was
**verified and accepted by the maintainer (MichaelMaillet) on 2026-09-23 UTC**,
and the E1–E5 pull request is approved. This record is immutable from here;
corrections are errata.

**Prior status (E4, retained):** E4 ANALYSED (2026-09-23 UTC). The frozen pre-registration §8
decision rule has been applied to all four immutable E3 run artefacts at code
SHA `6b9d6b6`; no case aborted in any run. The pre-registration is **frozen**
at `c22db0b`. Verdicts: **H1 `REFUTED` (485/504)** and **H2a `REFUTED`
(897/1,000)** — together a **campaign plan §10.4 D1**; **H2b `CONFIRMED`**
(both metrics' 95 % bootstrap CIs strictly inside ±δ over 657 contributing
cases), **H3 `CONFIRMED`** (14/14 bit-identical), **H4 `CONFIRMED`** (72/72
within the f32 kernel tolerance on CUDA). Per §10.4 item 2, session 0158 (E5)
still completes and reports the negatives in full, then blocks session 0159
(EXP-002 E1) until the four contingency correction sessions close; EXP-001 is
then re-run as `EXP-001-r1`. No root cause is claimed by E3 or E4. Campaign
plan **amendment 6** raised this experiment's tracked-storage cap to 8 MiB so
the runs could be committed unreduced. Regeneration was verified from a clean checkout of the E4 commit:
`verify_manifest` passes on all four raw runs and the generator reproduces both
output digests and the whole `report-manifest.json` byte for byte (campaign plan
§7.4 step 5). See [`analysis.md`](analysis.md) and [`log.md`](log.md).
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-001).
**Raw artefact root:** [`benchmarks/results/EXP-001/`](../../../benchmarks/results/EXP-001/README.md)

## What this directory will hold

| File | Created by | Frozen when |
|---|---|---|
| `preregistration.md` | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | **FROZEN** at `c22db0b`, 2026-09-23T13:40:12Z |
| `log.md` | E3 | **written**; never edited after E3 close; aborted runs stay |
| `analysis/exp001_e4_analysis.py` | E4 | **committed**; the registered §8 decision rule and every E4 output generator (campaign plan §7.4 item 2) |
| `analysis.md` | E4 | **written**; the E4 adjudication record, deviations, threats, and D1 declaration |
| `report.md` | E5 | **written** (session 0158); corrections are errata, never edits |
| `report-manifest.json` | E4/E5 | **written at E4**; SHA-256 of every regenerated output plus each input run manifest, the per-hypothesis verdicts, and the D1 flag (campaign plan §7.4 item 4) |

## Sessions

| Session | Stage | Brief | Status |
|---|---|---|---|
| 0154 | E1 — Pre-registration | [`0154-exp001-e1-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0154-exp001-e1-golden-trajectory-numerical-parity.md) | COMPLETE (historical, as of E1 close) — DRAFT pre-registration committed; H4 driver support left pending for E2 review (see preregistration §5.4). **Superseded by 0155 below: H4 was closed the same day.** |
| 0155 | E2 — Review and approval | [`0155-exp001-e2-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0155-exp001-e2-golden-trajectory-numerical-parity.md) | COMPLETE — pre-registration APPROVED; H4 driver support closed as a pre-execution amendment (preregistration §5.4); H1/H3 artefact-tagging bug found and fixed; PR #20 code review (Devin/CodeRabbit/Copilot) triaged and fixed as a second amendment (preregistration §5.5) |
| 0156 | E3 — Execution | [`0156-exp001-e3-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0156-exp001-e3-golden-trajectory-numerical-parity.md) | COMPLETE — 4/4 registered runs executed, 0 aborted, all manifested; H1/H2a breaches escalated to E4; see [log](log.md) |
| 0157 | E4 — Analysis | [`0157-exp001-e4-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0157-exp001-e4-golden-trajectory-numerical-parity.md) | COMPLETE — H1/H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`; **D1 raised**; analysis code + `report-manifest.json` committed; see [`analysis.md`](analysis.md) |
| 0158 | E5 — Report | [`0158-exp001-e5-golden-trajectory-numerical-parity.md`](../../sessions/phase-7/0158-exp001-e5-golden-trajectory-numerical-parity.md) | **COMPLETE (report issued; exit gate open on the correction cycle)** — all five verdicts reported in full, D1 flag carried, finding EXP001-E5-F1 raised, Parity Report erratum issued, correction cycle triggered; **0159 blocked**; report **verified and accepted by the maintainer (MichaelMaillet) on 2026-09-23 UTC** (report §13) and carried to `main` by **PR #23** (report §14). See [`report.md`](report.md) |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 1`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

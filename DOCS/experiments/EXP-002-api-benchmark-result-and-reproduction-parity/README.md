# EXP-002 — API, benchmark-result, and reproduction parity (track C1)

**Status:** DRAFT — E1 preparation in progress; nothing may execute.
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-002).
**Raw artefact root:** [`benchmarks/results/EXP-002/`](../../../benchmarks/results/EXP-002/README.md)

## Current artefacts

| File | Created by | Frozen when |
|---|---|---|
| `preregistration.md` | E1, lead-authored ([`preregistration.md`](preregistration.md)) | E3 start (first `RUN-` directory created) |
| `e1-handoff.md` | E1 ([`e1-handoff.md`](e1-handoff.md)) | living handoff skeleton until E1 close |
| `log.md` | E3 | never edited after E3 close; aborted runs stay |
| `report.md` | E5 | after E5 approval; corrections are errata |
| `report-manifest.json` | E4/E5 | SHA-256 of every regenerated figure/table (campaign plan §7.4) |

The lead-authored collection driver is
[`benchmarks/campaign/exp002_driver.py`](../../../benchmarks/campaign/exp002_driver.py);
its synthetic regression tests are
[`tests/test_exp002_driver.py`](../../../tests/test_exp002_driver.py). The
driver refuses admission while `preregistration.md` is DRAFT; no E3 run,
pilot, or real reference-input collection is authorized.

## Sessions

| Session | Stage | Brief | Status |
|---|---|---|---|
| 0159 | E1 — Pre-registration | [`0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | IN_PROGRESS |
| 0160 | E2 — Review and approval | [`0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0161 | E3 — Execution | [`0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0162 | E4 — Analysis | [`0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0163 | E5 — Report | [`0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md) | PLANNED |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 2`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

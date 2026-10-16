# EXP-002 D1 S3 — Correction remediation

**Status:** IN PROGRESS (S2 complete; S3 started 2026-10-16 UTC on `hotfix/exp002-d1-figure-parity` from `5ba0129e`)
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`)
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC
**Predecessor:** [S2 — correction audit](2026-10-14-exp002-d1-s2-correction-audit.md)
**Successor:** [S4 — correction documentation](2026-10-14-exp002-d1-s4-correction-documentation.md)
**Governing record:** [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §8

## Expectation

Resolve every correction-audit finding, append closure evidence, and obtain a CLEAN delta re-audit; execute no new feature work.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Rules specific to this correction

- Mandatory session (Development Workflow §3): S3 executes even if S2 finds zero deviations, recording a no-change closure and independent delta verification.
- Work only on S2's findings, in severity order D1 → D4, each commit naming its finding ID.
- A finding that cannot or should not be fixed requires an approved Project Plan §8.3 or campaign-plan §14.2 amendment, cross-referenced from the finding. The trajectory moves only by amendment.
- The `EXP-002` record and its raw artefacts under `benchmarks/results/EXP-002/RUN-*` stay immutable. Any correction to the issued E5 report is an **erratum appended to it**, never an edit to its verdicts, tolerances, normalization policies, digests, or protocol (Experimentation Standards §1.3, §4).
- The delta re-audit must re-verify both the pre-fix failing reproduction and the post-fix passing parity tests, plus the immutability of the `EXP-002` record.

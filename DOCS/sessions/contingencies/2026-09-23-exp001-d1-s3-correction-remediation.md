# EXP-001 D1 S3 — Correction remediation

**Status:** OPEN — blocked on S2\
**Triggering deviation:** `EXP-001 H1/H2a REFUTED` (campaign plan §10.4 D1) and
`EXP001-E5-F1` (D1)\
**Blocked numbered session:** `0159`\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC\
**Predecessor:** [S2 — correction audit](2026-09-23-exp001-d1-s2-correction-audit.md)

## Expectation

Resolve every correction-audit finding, append closure evidence, and obtain a
CLEAN delta re-audit; execute no new feature work.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Rules specific to this correction

- Work only on S2's findings, in severity order D1 → D4, each commit naming
  its finding ID.
- A finding that cannot or should not be fixed requires an approved plan or
  campaign-plan amendment, cross-referenced from the finding. The trajectory
  moves only by amendment.
- The EXP-001 record and its raw artefacts stay immutable. Any correction to
  the issued E5 report is an **erratum appended to it**, never an edit to its
  verdicts, tolerances, digests, or protocol (Experimentation Standards
  §1.3/§4).
- The delta re-audit must re-run the pre-fix reproduction and the new parity
  gate, not only the changed unit tests.

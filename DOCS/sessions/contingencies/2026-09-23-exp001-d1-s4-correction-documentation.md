# EXP-001 D1 S4 — Correction documentation

**Status:** OPEN — blocked on S3\
**Triggering deviation:** `EXP-001 H1/H2a REFUTED` (campaign plan §10.4 D1) and
`EXP001-E5-F1` (D1)\
**Blocked numbered session:** `0159`\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC\
**Predecessor:** [S3 — correction remediation](2026-09-23-exp001-d1-s3-correction-remediation.md)

## Expectation

Update affected READMEs/changelog/reports/experiment protocol-deviation
records, close the deviation ledger entry, and authorize return to the blocked
session.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Closure checklist specific to this correction

1. **Project State Report** issued for the correction, carrying the deviation
   ledger rows for the EXP-001 D1 and `EXP001-E5-F1` with their final status.
   This PSR is also where the EXP-001 E5 report is announced (Experimentation
   Standards §2 E5).
2. **Registers updated:** `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`,
   `DOCS/sessions/SESSION_REGISTER.md` (contingency table row set to
   COMPLETE), `DOCS/sessions/phase-7/README.md`,
   `DOCS/experiments/README.md`, and this directory's README
   ("Closed corrections").
3. **Parity Report** brought into line with what the corrected evidence
   actually supports, and the E5 erratum resolved or superseded there; a
   CHANGELOG line records it (campaign plan §12 item 6).
4. **Erratum pointer appended** to the EXP-001 E5 report naming
   `EXP-001-r1`. The E5 record's verdicts, digests, and artefacts are **not**
   edited.
5. **`EXP-001-r1` authorized**: a new experiment record with a new
   pre-registration (E1) and new run directories, per campaign plan §10.4
   item 4. The re-run does not reuse EXP-001's run IDs or artefacts.
6. **Return to `0159` is authorized only after** step 5's E5 verdict is not a
   reversal, or the maintainer records a Project Plan §8.3 amendment
   accepting a changed conclusion with full justification (campaign plan
   §10.4 item 5). S4 closing on its own does **not** release `0159`; state
   that explicitly in the PSR.
7. **CI-green evidence** for the merged correction recorded with
   `tools/check_ci_green.py <merge-SHA>` output pasted in, per amendment #45.

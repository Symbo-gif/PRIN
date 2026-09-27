# EXP-001 D1 S4 — Correction documentation

**Status:** COMPLETE (2026-09-27 UTC; closure record in `DOCS/audits/2026-09-24-exp001-d1-correction-audit.md` §S4)\
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

**Closure checklist completed (2026-09-27 UTC):**

1. **PSR-039 issued:** `DOCS/reports/039-project-state.md` — carries deviation
   ledger rows for EXP-001 D1 (H1/H2a RESOLVED) and EXP001-E5-F1 (RESOLVED),
   announces the EXP-001 E5 report, and explicitly states session 0159 stays
   BLOCKED until `EXP-001-r1` returns a non-reversal verdict.
2. **Registers updated:**
   - `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — correction cycle resolved
     note appended; 0159 block conditions restated.
   - `DOCS/sessions/SESSION_REGISTER.md` — `EXP-001-D1` contingency row set to
     **COMPLETE 2026-09-27 UTC**.
   - `DOCS/sessions/phase-7/README.md` — correction cycle COMPLETE note.
   - `DOCS/experiments/README.md` — EXP-001 E5 status updated with correction
     cycle completion and `EXP-001-r1` authorization.
   - `DOCS/sessions/contingencies/README.md` — EXP-001 D1 moved to "Closed
     corrections."
3. **Parity Report aligned:** S1 already updated `DOCS/sphinx/parity_report.rst`
   with the root-cause explanation and correction-cycle status; no further
   changes needed. CHANGELOG line recorded.
4. **Erratum E-3 appended** to the EXP-001 E5 report (`report.md` §15) naming
   `EXP-001-r1`. The E5 record's verdicts, digests, and artefacts are **not**
   edited.
5. **`EXP-001-r1` authorized:** new experiment record created at
   `DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/README.md`
   with inherited campaign plan rules, key differences from EXP-001, and the
   blocking condition stated.
6. **Return to 0159:** explicitly stated in PSR-039 §5, erratum E-3, and all
   register updates that S4 closing on its own does **not** release 0159.
   Session 0159 stays BLOCKED until `EXP-001-r1`'s E5 verdict is not a
   reversal, or the maintainer records a Plan §8.3 amendment.
7. **CI-green evidence:** PR #24 not yet merged; `check_ci_green.py
   <merge-SHA>` to be recorded by the next governed session after merge.

**Artefacts committed:**
- `DOCS/reports/039-project-state.md` (new)
- `DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/README.md` (new)
- `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/report.md` (erratum E-3)
- `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/README.md` (status update)
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (correction resolved note)
- `DOCS/sessions/SESSION_REGISTER.md` (contingency row COMPLETE)
- `DOCS/sessions/phase-7/README.md` (correction COMPLETE note)
- `DOCS/sessions/contingencies/README.md` (moved to Closed corrections)
- `DOCS/experiments/README.md` (EXP-001 status update)
- `DOCS/audits/2026-09-24-exp001-d1-correction-audit.md` (S4 closure appended)
- `CHANGELOG.md` (S4 entry)

**Handoff:** The correction cycle is documentation-complete. Next maintainer
action: merge PR #24, record CI-green evidence, declare `EXP-001-r1` E1 session.
Session `0159` remains **BLOCKED**.

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

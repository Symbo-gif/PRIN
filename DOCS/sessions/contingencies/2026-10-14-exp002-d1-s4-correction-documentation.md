# EXP-002 D1 S4 — Correction documentation

**Status:** OPEN — blocked on S3
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`)
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC
**Predecessor:** [S3 — correction remediation](2026-10-14-exp002-d1-s3-correction-remediation.md)
**Governing record:** [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §8

## Expectation

Update affected READMEs/changelog/reports/experiment protocol-deviation records, close the deviation ledger entry, and authorize return to the blocked session.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Closure checklist specific to this correction

1. **Project State Report** issued for the correction (`DOCS/reports/041-project-state.md` or the next sequential PSR), carrying the cumulative deviation-ledger rows for the `EXP-002` D1 (`H3 REFUTED`) and any S2 findings with their final status, validated with `tools/check_deviation_ledger.py`. This PSR is also where the `EXP-002` E5 report is formally announced (Experimentation Standards §2 E5; campaign plan §10.4 item 3).
2. **Registers updated:** `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (verified with `tools/check_dv_register_gates.py`), `DOCS/sessions/SESSION_REGISTER.md` (`EXP-002-D1` contingency row set to `COMPLETE`), `DOCS/sessions/phase-7/README.md`, `DOCS/experiments/README.md`, and `DOCS/sessions/contingencies/README.md` (move `EXP-002 D1` from `"Open corrections"` to `"Closed corrections"`).
3. **Parity Report (`DOCS/sphinx/parity_report.rst`)** updated to reflect what the corrected evidence supports, and a `CHANGELOG.md` entry added (campaign plan §12 item 6; verified with a clean `sphinx.cmd.build -W` build into a fresh directory).
4. **Erratum pointer appended** to `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md` (§15) naming **`EXP-002-r1`**. The `EXP-002` record's verdicts, digests, and raw artefacts are **never** edited.
5. **`EXP-002-r1` authorized:** create a new experiment record skeleton `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md` with a new pre-registration (E1) and new `RUN-` directories, per campaign plan §10.4 item 4. The re-run never reuses `EXP-002`'s run IDs or artefacts.
6. **Return to `0164` is authorized only after** `EXP-002-r1`'s E5 verdict is not a reversal and is verified/accepted by the maintainer, or the maintainer records a Project Plan §8.3 amendment accepting a changed conclusion with full justification (campaign plan §10.4 item 5). **S4 closing on its own does not release `0164`**; state that explicitly in the PSR and registers.
7. **Full local gate evidence** recorded verbatim under the Plan amendment #48 local-validation regime (plus hosted CI evidence if a hosted window is active).

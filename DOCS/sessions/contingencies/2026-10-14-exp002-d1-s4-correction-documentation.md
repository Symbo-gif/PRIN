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
5. **`EXP-002-r1` authorized:** create a new experiment record skeleton `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md` with a new pre-registration (E1) and new `RUN-` directories, per campaign plan §10.4 item 4. The re-run never reuses `EXP-002`'s run IDs or artefacts. **Carry `EXP002D1-S2-F1` into this authorization** (see "Carried from S3" below): the authorization must require `EXP-002-r1`'s E1/E2 to register how its two H3 comparison policies are read.
6. **Return to `0164` is authorized only after** `EXP-002-r1`'s E5 verdict is not a reversal and is verified/accepted by the maintainer, or the maintainer records a Project Plan §8.3 amendment accepting a changed conclusion with full justification (campaign plan §10.4 item 5). **S4 closing on its own does not release `0164`**; state that explicitly in the PSR and registers.
7. **Full local gate evidence** recorded verbatim under the Plan amendment #48 local-validation regime (plus hosted CI evidence if a hosted window is active).

## Carried from S3 — `EXP002D1-S2-F1` (D3): register both H3 policies in `EXP-002-r1`

S3 resolved this finding by **assignment**, not by plan amendment (correction
audit §S3). Nothing in the `EXP-002` record changes. S4 must carry the following
into the `EXP-002-r1` authorization (closure item 5) so that the new record's
pre-registration (E1) and review (E2) register both comparison policies
deliberately rather than inherit a disagreement.

**What S2 established** ([`both-policies-post-fix.txt`](../../../EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt)).
On the corrected generator the approved §5.4 policy gives **39/39 equal** and the
§11.3 sensitivity policy gives **14/39 equal**. All 25 residuals are classified,
0 unclassified, and all are writer or host properties:

- 14 PDFs differ only in the Info **key set** (reference: 3 keys, including a
  wall-clock `CreationDate`; PRIN: 4 fixed keys, including `ModDate`);
- 11 `.tex` tables differ only in **line terminators** (reference: CRLF, from its
  text-mode writer on Windows; PRIN: LF).

**What `EXP-002-r1` must therefore do:**

1. **Name the deciding rule.** State in the pre-registration which comparison
   policy decides H3 and what status the other has (for example: §5.4 as the sole
   primary, with §11.3 retained as a disclosed writer-property sensitivity; or a
   corrected sensitivity policy that canonicalizes the two writer properties).
   S3 does not choose; the choice belongs to the new record.
2. **Replace or restate the §11.3 item 1 clause.** `EXP-002`'s clause ("if the two
   verdicts differ, E5 must state that H3's verdict depends on a comparison
   amendment made after outcome exposure, and must not report either verdict
   alone") was written for a state in which both policies refuted. Under a
   corrected generator it would turn a writer property into a policy-dependent
   verdict. `EXP-002-r1` must say, **before any r1 data exist**, what a
   disagreement means.
3. **Fix the choice before the first `RUN-` directory exists** (`EXP-002` froze
   its protocol at the first `RUN-` creation in session `0161`), and **disclose
   outcome exposure**: the choice is made with knowledge of `EXP-002`'s results
   and of S1/S2's residual classification, as `EXP-002`'s own E1/E2 disclosed
   for its amendments.
4. **Do not chase §11.3 equality by changing a writer.** PRIN's fixed PDF
   metadata is what makes H4 (raw determinism) hold, so it must not be altered;
   the frozen reference must not be altered either.
5. **Never edit `EXP-002`'s frozen `preregistration.md`.** The change lives only
   in the new record.

**No amendment is requested.** Campaign plan §10.4 item 4 already requires a new
pre-registration for the re-run, and that document is the governed place for this
registration. If `EXP-002-r1`'s E1 or E2 finds that the choice cannot be made
inside a pre-registration (for instance, if §10.4 item 5's "not a reversal" test
itself would need reinterpreting), that is an amendment matter: draft it for
maintainer approval, do not adopt it.

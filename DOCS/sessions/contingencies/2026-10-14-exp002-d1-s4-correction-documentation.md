# EXP-002 D1 S4 — Correction documentation

**Status:** COMPLETE (2026-10-16 UTC; closure record in [`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../audits/2026-10-15-exp002-d1-correction-audit.md) `## S4 — closure`, and "S4 completion and handoff" below)
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`) — **still BLOCKED; this session's closure does not release them**
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
7. **Full local gate evidence** recorded verbatim under the Plan amendment #48 local-validation regime (plus hosted CI evidence if a hosted window is active). **Carry S3's observation O-1** ("Carried from S3 — O-1" below): the required full suite did not exit 0 on this host in either of S3's runs.

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

## Carried from S3 — observation O-1 and the third `python/PT` location

**O-1: the required full suite has not given an exit 0 in one pass on this host.**
S3 ran `pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300
--durations=20` twice at the shipped notebook bounds. Run 1 failed
`tests/test_exp002_driver.py::TestCheckRunComplete::test_wrong_parent_rejected` on a
Windows `WinError 5` rename inside `.pytest_basetemp`; run 2 failed
`tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`
(ratio 2.18 against 1.30, the host-timing-sensitive node DV-032 registers). Both pass
alone, neither touches this change, and `EXP002D1-S2-F2`'s notebook timeout fired in
neither (correction audit §S3.7, §S3.9 item 9; evidence in
[`EVIDENCE/exp002-d1-s3/gate/`](../../../EVIDENCE/exp002-d1-s3/gate/README.md)).
S4's gate must **record its own full-suite result at its actual exit status**, must
not describe a rerun-until-green as a pass, and must either run with the IDE and
security tooling quiet (recording that) or ask the maintainer to decide the
severity of O-1 and the §S3.9 item 9 options. S3 added no skip, xfail, deselection or
tolerance and S4 must not either.

**`EXP002D1-S2-F8` has a third location.** `EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py:142`
(`python/PT`, LOW) matches the class the maintainer ratified for two other
locations. S3 did not ratify it and did not edit S2's instrument; the PSR should
carry it for the maintainer's decision.

## Carried from S3 — observation O-2

**O-2: the S3 cold-review loop did not converge within its four-round cap.** Round 4
returned 13 CONFIRMED claims (two medium, in S3's own gate scripts; none in the
correction, a frozen artefact or a test). All were fixed and re-verified by measurement,
but no fifth round was run, so those fixes have had no cold review. S4's own review
should cover `EVIDENCE/exp002-d1-s3/` (the gate scripts `closing_gate.sh`,
`final_legs.sh`, `delta_reaudit.sh`, `diagnostic_suite_run.sh`, `cold-review/launch_round.sh`
and the records they write) and the comment change in `tests/test_notebooks.py`.
`closing_gate.sh` changed after the run it recorded and has not been re-run end to end
(correction audit §S3.9 items 11 and 12). Severity D4; S4's ledger should register it.

## S4 completion and handoff (2026-10-16 UTC)

Added by S4. The checklist above is unchanged; this section records what was
delivered against it and hands off what remains.

**Closure checklist — all seven items delivered.**

1. **PSR-041 issued** — [`DOCS/reports/041-project-state.md`](../../reports/041-project-state.md).
   It carries the cumulative deviation-ledger delta inheriting PSR-040 §3 with
   the `EXP-002` D1 (`EXP002-D1-H3`, D1) row, all eight
   `EXP002D1-S2-F1`..`-F8` rows at their final §S3.1 status, the O-1 and O-2
   rows, the third `EXP002D1-S2-F8` location, and the one finding S4's own
   review raised. It formally announces the EXP-002 E5 report
   (Experimentation Standards §2 E5; campaign plan §10.4 item 3). Validated with
   `tools/check_deviation_ledger.py DOCS/reports/040-project-state.md
   DOCS/reports/041-project-state.md`.
2. **Registers updated** — `SESSION_REGISTER.md` (entry-point line and the
   `EXP-002-D1` contingency row set to `COMPLETE`), `phase-7/README.md`,
   `DOCS/experiments/README.md` (dated entry plus the `EXP-002-r1` record-root
   row), `contingencies/README.md` (EXP-002 D1 moved to "Closed corrections"),
   and `DEFERRED_VALIDATION_REGISTER.md` (a dated amendment-#52 section).
   **No new DV row was opened**: O-1's closure evidence is a hosted run in this
   same session, not validation deferred to a future work package or phase,
   which is what that register consolidates. DV-032 was deliberately **not**
   widened — it registers host-sensitive *timing ratios*, while the Windows
   `WinError 5` rename is the `AGENTS.md`-documented pytest temporary-directory
   contention class. All four governance checkers exit 0.
3. **Parity Report aligned** — [`parity_report.rst`](../../sphinx/parity_report.rst)
   gained a dated 2026-10-16 update admonition (the 2026-10-14 erratum is
   retained verbatim) and its `REFERENCE-HISTORICAL` label row and two
   reproduction-artefact rows were corrected to what the fixed generator
   supports. **The honesty rule holds throughout: the corrected generator equals
   the frozen reference under the approved §5.4 policy (39/39) and is 14/39
   under the §11.3 sensitivity policy (all 25 residuals writer or host
   properties, 0 unclassified), but `EXP-002`'s verdict stays `H3 REFUTED` and
   nothing written here confirms H3.** CHANGELOG entry added; verified by a
   `sphinx.cmd.build -W --keep-going` run from a deleted `DOCS/sphinx/_build`.
4. **Erratum appended** — erratum **2** in the EXP-002 E5 report §15, naming
   `EXP-002-r1`. **Append-only, proven by `git diff --numstat`: 2 added, 0
   deleted.** No verdict, tolerance, normalization policy, digest, protocol,
   `preregistration.md` or `benchmarks/results/EXP-002/` file was touched.
5. **`EXP-002-r1` authorized** — record skeleton at
   [`EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md`](../../experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md),
   carrying `EXP002D1-S2-F1` exactly as the "Carried from S3" section above
   states (all five of its requirements, verbatim in substance). It **names the
   open decision** — which H3 comparison policy decides, the status of the
   other, replacement of the §11.3 item 1 clause, outcome-exposure disclosure,
   fixing the choice before the first `RUN-` directory exists, and no writer
   changes to chase §11.3 equality — and records it as an **explicit open item
   needing the maintainer's approval before r1's E1 starts**. **S4 did not
   choose the deciding rule.** No experiment was executed and **no `RUN-`
   directory was created**.
6. **The non-release statement is explicit** in PSR-041 (§1, §5, §6), in every
   register touched, in the erratum, in the `EXP-002-r1` skeleton, and in the
   audit's S4 section: **S4 closing, the merge of PR #34, and the re-enabling of
   the hosted workflows do NOT release session `0164`** (nor `0165`–`0194`).
7. **Gate evidence recorded verbatim** in
   [`EVIDENCE/exp002-d1-s4/`](../../../EVIDENCE/exp002-d1-s4/README.md), with
   the hosted evidence named there and in the audit's S4 section.

**The three carried items — dispositions.**

- **O-1 (the required full suite).** Recorded as **D3** per Development
  Workflow §5. The standard's D2 ("breaks a normative standard … quality gates")
  was considered and rejected: the tests themselves all pass, each failure is a
  host-contention artefact on a test unrelated to this change and passing in
  isolation, so the repository does not break the standard — the host prevents
  demonstrating it, which is §5's D3 "divergence between plan text and
  justified reality". S4 ran the required full suite **once** and recorded its
  **actual exit status**; no rerun-until-green was performed and none is
  described as a pass. Closure evidence is named as an independent hosted
  full-suite run at the PR #34 head commit (Plan amendment #52). Operating
  guidance for the maintainer is recorded in PSR-041 §5 and the audit's S4
  section: run the local gate with IDE and security tooling quiet, and exclude
  `.pytest_basetemp` from IDE workspace scanning and security-software real-time
  scanning. **No process belonging to the maintainer was stopped or killed, and
  S4 cannot change those settings itself.**
- **O-2 (the unreviewed round-4 fixes).** **RESOLVED (D4).** The missing review
  was performed read-only, by measurement, on the committed S3 fixes
  (`closing_gate.sh`, `final_legs.sh`, `delta_reaudit.sh`,
  `diagnostic_suite_run.sh`, `cold-review/launch_round.sh`,
  `docstring_only_check.py`, and the `b08dd574` comment change), reproducing
  every suspected defect with a command and classifying it CONFIRMED / REFUTED /
  NOT REPRODUCIBLE exactly as `EVIDENCE/exp002-d1-s3/cold-review/triage.md`
  does. **One CONFIRMED defect**: `final_legs.sh`'s grep-based leg aggregation
  (`grep -a '^# exit code' FILE | grep -qv ': 0$' && overall=1`) **fails open** —
  when the record file is missing, empty, or holds no marker line, the second
  `grep` sees no input and returns 1, so `overall` stays 0 and a leg that
  produced no record reads as passing. It is the same class round 4 fixed for
  the Snyk leg alone (T4-2); five sibling legs still had it. **Latent**: every
  committed S3 record was verified to carry its marker, so no recorded S3 result
  was masked. S3's file was **not edited**; a corrected copy with fail-closed
  aggregation supersedes it in `EVIDENCE/exp002-d1-s4/`, with a red-before and
  green-after demonstration. Everything else in the round-4 fix set verified as
  claimed (see the bundle's `o2-review/triage.md`).
- **`EXP002D1-S2-F8`'s third location.** **RATIFIED** as an accepted, visible
  LOW. All four ratification conditions were verified by reading the file and
  reproducing the finding, and a Coding Standards §6.2 threat assessment is
  recorded in the audit's S4 section in the same form as §S2.14 and §S3.4.
  **This is not a suppression**: nothing was added to `.snyk`, no ignore or
  severity exclusion was created, and S2's file was not edited. The finding is
  re-checked every cycle.

**Plan amendment #52 adopted** (4D), on the maintainer's verbatim authority,
with #50's footprint mirrored: `DOCS/PRIN_Project_Plan.md` §8.3 (row plus an
"Amendment #52 authority" block), Development Workflow and Audit Standards §3
item 11, `CLAUDE.md`, `.claude/CLAUDE.md`, and a dated section in
`DEFERRED_VALIDATION_REGISTER.md`. `AGENTS.md` needed no change — a grep
confirms amendment #50 never touched it (it cites only #49). No other Plan or
campaign-plan amendment was found necessary, so none was drafted.

**Handoff — what remains, and whose it is.**

1. **The maintainer declares `EXP-002-r1` E1.** It cannot start until the open
   H3 comparison-policy decision in that record is approved.
2. **DV-047 gates r1's E3**: rebuild `python/prin/_prin_core.pyd`, remove the
   stale `prin_core.pth`, and record the new `.pyd` SHA-256 in the driver.
3. **Session `0164` and `0165`–`0194` stay BLOCKED** until r1's E5 verdict is a
   non-reversal, verified and accepted by the maintainer, or a Project Plan
   §8.3 amendment is adopted.
4. **Hosted workflows stay enabled** under amendment #52 until `0194` closes or
   the maintainer says otherwise; the disabling is then recorded.
5. **O-1's closure evidence** is the hosted full-suite run at the PR #34 head
   commit. Because `main` is PR-only, a post-merge record cannot be committed
   here, so the run's verbatim result (workflow, run ID, head SHA, conclusion)
   is reported in the session record and should be entered by the next governed
   session, which is also where a DV row should be opened if that run did not
   pass.

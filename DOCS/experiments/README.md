# DOCS/experiments/ — Pre-registrations, logs, and reports

Scientific experiment records governed by the
[Experimentation Standards](../standards/Experimentation_Standards.md).

## Phase 7 campaign plan

[`campaign-plan.md`](campaign-plan.md) is the approved, frozen campaign-level
artefact required by Experimentation Standards §3: the EXP-001…EXP-008
registry in Session Register order, dependency graph, owners, hardware/backend
matrix, seed policy, shared artefact schema and run-directory rule, budgets,
statistics policy, stop/escalation rules, registered gaps (DV-036/038/039),
and the maintainer approval record (session 0153, Campaign E0). Every
pre-registration inherits its §5–§10 rules. It contains no hypotheses and no
results.

DV-036's pre-0156 CI correction (campaign plan §11.6 / amendments 3 and 4)
**closed on 2026-09-23 UTC** with a wholly green nightly `35847692136`; it
was never EXP-001 execution or a reference-host performance result, and
DV-036's reference-host re-baseline gates before 0168 and 0173 remain open.

**EXP-001 E3 executed on 2026-09-23 UTC (session 0156).** All four
registered runs completed with no aborted case; H3 and H4 came in as
predicted, while **H1 (19/504) and H2a (103/1,000) breach the registered
tolerances** — a REFUTED/D1 trajectory under preregistration §8, escalated
to E4 (session 0157) for adjudication per campaign plan §10.4. See
[EXP-001's execution log](EXP-001-golden-trajectory-numerical-parity/log.md).

**EXP-001 E4 adjudicated on 2026-09-23 UTC (session 0157) — campaign plan
§10.4 D1 raised.** Applying the frozen §8 rule: **H1 `REFUTED`**,
**H2a `REFUTED`**, **H2b `CONFIRMED`**, **H3 `CONFIRMED`**,
**H4 `CONFIRMED`**. Session 0158 (E5) still completes and reports the
negatives in full, then blocks session 0159 and every downstream experiment
until the four contingency correction sessions close; EXP-001 is then re-run
as a new record, `EXP-001-r1`. No root cause is claimed at E4. See
[EXP-001's E4 analysis record](EXP-001-golden-trajectory-numerical-parity/analysis.md).

**EXP-001 E5 reported on 2026-09-23 UTC (session 0158) — the campaign is
BLOCKED.** The [E5 report](EXP-001-golden-trajectory-numerical-parity/report.md)
issues all five verdicts in full — **H1 `REFUTED` (485/504)**, **H2a `REFUTED`
(897/1,000)**, H2b/H3/H4 `CONFIRMED` — carries the §10.4 **D1** flag, and
triggers the four-session contingency correction cycle
([S1](../sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md)
→ [S2](../sessions/contingencies/2026-09-23-exp001-d1-s2-correction-audit.md)
→ [S3](../sessions/contingencies/2026-09-23-exp001-d1-s3-correction-remediation.md)
→ [S4](../sessions/contingencies/2026-09-23-exp001-d1-s4-correction-documentation.md)).
It also raises a second D1, **EXP001-E5-F1**: the `parity` CI gate did not
exercise PRIN (erratum issued). **Correction cycle COMPLETE 2026-09-27 UTC**
(S1–S4 all closed; S2 **PASS**, S3 delta re-audit **CLEAN**). `EXP-001-r1`
authorized as a new experiment record
([`EXP-001-r1`](EXP-001-r1-golden-trajectory-numerical-parity/README.md)) per
campaign plan §10.4 item 4. **Session 0159 and every experiment downstream of
EXP-001, plus 0194, remain BLOCKED** until `EXP-001-r1` returns a non-reversal
verdict. PR #24 merged as `149cf2d88ab6be401951b63d1d7e8fad209f52a5`
(2026-09-28 UTC); all six required workflows are green. `EXP-001-r1` E1
entry evidence and its draft protocol are linked from the re-run record.
`EXP-001-r1` E2 (2026-09-28 UTC) independently re-verified E1's claims
(zero discrepancies) and the maintainer approved the sample-size,
statistics-rule, and storage-budget gates; the **E2 follow-up H4 method was
APPROVED 2026-09-29 UTC**, closing the last §10 entry gate. DV-041's binding
capability closed on PR #25/required CI; DV-043 merged to `main` as `9b79d2e`
(PR #26) with a green forced-nightly `bench-regression` (`36525353031`
attempt 2); DV-044 closed through its own S1→S4 cycle; and
`M = 9b79d2e…` was incorporated with `check_ci_green.py` green on all six
required workflows (see `e2-review.md` §8 in the re-run record).
**`EXP-001-r1` E3 EXECUTED 2026-09-29 UTC**: the pre-registration froze at its
first `RUN-` creation at `F = 5d5ae35…` and all six registered runs executed
from the clean campaign checkout `R = 5d5ae35…` — 72-case wgpu kernel-path
(`wgpu<wgsl>` proven per case), 72-case CUDA kernel-path, 504-case corpus,
2× 14-case repeatability and the 1,000-draw fuzz leg. Zero aborts, all
manifested; see the [E3 log](EXP-001-r1-golden-trajectory-numerical-parity/log.md).
**`EXP-001-r1` E4 ANALYSED 2026-09-29 UTC — all five hypotheses `CONFIRMED`,
campaign plan §10.4 D1 flag NOT raised (a non-reversal detection)**: H1
504/504 accepted (485 native-parity + 19 explained-dv007, zero unexplained
breaches), H2a **978 pointwise + 22 characterized**, H2b both metrics' 95 % CIs
strictly inside ±δ on 657 contributors each, H3 14/14 byte-identical in both
invocations with identical separate-run projections, H4 72/72 on **each** of
CUDA and wgpu with zero failed derivative elements; see the
[E4 analysis record](EXP-001-r1-golden-trajectory-numerical-parity/analysis.md).
**E4 does not release 0159** — §10.4 item 5 keys the release to E5's verdict,
so session 0159 and every experiment downstream of EXP-001, plus 0194, remain
**BLOCKED** until `EXP-001-r1` E5 reports.
**`EXP-001-r1` E5 REPORTED 2026-09-29 UTC — non-reversal; no D1 correction
cycle is triggered.** The [E5 report](EXP-001-r1-golden-trajectory-numerical-parity/report.md)
restates all five `CONFIRMED` verdicts against §3's frozen predictions, reports
both 72-case H4 GPU legs in full, and records PD-1…PD-6 — including PD-5, the
`149cf2d..M` baseline delta §10 item 5 requires (23 files, 2,253 insertions,
34 deletions: exactly DV-041/PR #25 and DV-043/PR #26 plus their documentation,
with `R` identified as the experiment's distinct source SHA rather than a second
mid-experiment `main` change) — ten threats to validity including §4.2's
clamp-trip limitation restated for the 22 characterized cases, and the complete
artefact index. Regeneration was re-verified in the E5 checkout at `46fea62`:
all four committed output digests reproduced byte-identically. EXP-001's own
record gains append-only erratum **E-4** and the Parity Report gains a dated
admonition; **neither revises EXP-001's `REFUTED` verdicts**, which stand
exactly as issued. **The §10.4 item 5 release condition is met, but the release
takes effect only on the maintainer's verification of that report (§13), which
is E5's exit gate and is not yet recorded** — so 0159, EXP-002 … EXP-008 and
0194 remain **BLOCKED** until then. *(Superseded later the same day by the
verification entry immediately below; retained because this index accumulates
dated entries rather than rewriting them.)* Nothing was pushed; §12 item 3 makes
the E5 PR carry the whole r1 E1–E5 range, and opening it awaits authorization.
**`EXP-001-r1` E5 VERIFIED AND ACCEPTED 2026-09-29 UTC — THE CAMPAIGN BLOCK IS
LIFTED.** MichaelMaillet verified and accepted the report (its §13 block is
completed), so E5's exit gate is met and **session 0159 (EXP-002 E1), every
experiment downstream of EXP-001, and 0194 are RELEASED** under campaign plan
§10.4 item 5. No D1 correction cycle is triggered and no Project Plan §8.3
amendment was needed, because a confirmed parity result is not a changed
conclusion. Opening the E1–E5 pull request is authorized but **not yet done** —
nothing has been pushed. `EXP-002` may now begin in campaign plan §3's
dependency order. *(Dated correction, 2026-10-11 UTC: the E1–E5 pull
request was subsequently opened and merged as **PR #28**; the sentence
above is retained as its point-in-time record.)*

**EXP-002 E1 PREPARATION IN PROGRESS — session 0159, 2026-10-11 UTC.** The
lead-authored DRAFT pre-registration
([`EXP-002` record](EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md))
and the necessary E1 collection driver
(`benchmarks/campaign/exp002_driver.py`, with synthetic-fixture regression
tests) are in place on `campaign/0159-exp002-e1`. Project Plan amendment
#49 adopted supervised-local-validation timeout governance within the
declared 0159 scope. Scientific approval belongs to session 0160; no
EXP-002 execution, pilot or reference-input collection has run and the
final full local gate is pending. *(Dated correction, 2026-10-11 UTC,
PR33-F10: the final local gate then completed on checkpoint `63145325` —
FAST, FULL, Sphinx and the governance battery all exit 0
(`EVIDENCE/0159/verification/final-6314532/`). The branch was published as
PR #33, whose seven review sources are adjudicated in
[`PR033-multi-review-audit.md`](../audits/PR033-multi-review-audit.md); that
round amended the DRAFT protocol (its section 11) and the driver, and the
maintainer approved the gitleaks checksum exception. EXP-002 remains
DRAFT, with no execution.)*

**EXP-002 APPROVED AT E2 — sessions 0159 and 0160 COMPLETE, 2026-10-12 UTC.**
The maintainer accepted the E1 exit and delegated the E2 decisions, recorded
with their reasons in
[`e2-review.md`](EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md).
Session 0161 (E3) is READY under that record's §8 entry checklist. No EXP-002
experiment leg has executed. *(Dated update, 2026-10-12 UTC: E3 then executed —
see the next entry; this paragraph is retained as its point-in-time record.)*

**EXP-002 E3 EXECUTED — session 0161, 2026-10-12 UTC.** All five registered legs
(`api`, `conclusions`, `reference`, `prin`, `repeatability`) ran once each at source
`fae24c4`, in the registered order, through the committed driver
`benchmarks/campaign/exp002_driver.py`: five immutable, manifested `RUN-` directories under
`benchmarks/results/EXP-002/`, every exit code 0, **0 aborted, no rerun, no D1 condition**,
aggregate CPU wall 63.821 s against the 12 h cap. The protocol froze at the first `RUN-`
(2026-10-12T21:27:05Z). Each record was validated independently for structure and identity;
**no hypothesis verdict was computed** and no observation payload was examined — adjudication,
the H3 dual-policy report and any D1 determination belong to E4 (session 0162, now READY). The
generated publication roots are retained, unmodified and untracked, until the E5 report is accepted.
Record: [`log.md`](EXP-002-api-benchmark-result-and-reproduction-parity/log.md) and the
[E3-to-E4 handoff](EXP-002-api-benchmark-result-and-reproduction-parity/README.md#e3-to-e4-handoff-session-0161-2026-10-12-utc).

**EXP-002 E4 ANALYSED — session 0162, 2026-10-13 UTC — H1, H2, H4 `CONFIRMED`; H3 `REFUTED` (both policies); D1 flag RAISED.** The registered analysis module [`analysis/exp002_e4_analysis.py`](EXP-002-api-benchmark-result-and-reproduction-parity/analysis/exp002_e4_analysis.py) was committed and pushed (`3731fc2`) before any real record was analysed, then applied the frozen decision rules to the five E3 records (all admissible, 0 aborted; two runs byte-identical): **H1 `CONFIRMED`** (`175/175` `api_symbols` resolved, `172/172` `legacy_api_names` owned, `0` duplicate/removed/unexpected, frozen sets empty), **H2 `CONFIRMED`** (`62/62` `claim_comparator_records` agree across `C01`–`C05`), **H3 `REFUTED`** (`21/39` `generated_files` equal under the approved §5.4 policy, `18/39` differing: `.pdf` and `.png` of figures 5, 7, 8, 9, 10, 11, 12, 14, and 15, while all `11/11` tables match each other and the archived tables; also `REFUTED` at `5/39` under the §11.3 sensitivity policy), and **H4 `CONFIRMED`** (`39/39` `generated_files` raw-identical across two PRIN processes, canonical projections equal). Record: [`analysis.md`](EXP-002-api-benchmark-result-and-reproduction-parity/analysis.md) and [`report-manifest.json`](EXP-002-api-benchmark-result-and-reproduction-parity/report-manifest.json).

**EXP-002 E5 REPORTED — session 0163, 2026-10-14 UTC — D1 RAISED ON H3; CAMPAIGN BLOCKED AT SESSION 0164.** The [E5 report](EXP-002-api-benchmark-result-and-reproduction-parity/report.md) issues all verdicts in full (**H1 `CONFIRMED`**, **H2 `CONFIRMED`**, **H3 `REFUTED` (D1)** under both the approved `21/39` and sensitivity `5/39` policies, **H4 `CONFIRMED`**), verifies the retained publication bytes (`39/39` per run) and input snapshots (`172/172` per run) first against their manifested digests, regenerates the 7 E4 analysis outputs and `report-manifest.json` (`6b15dcc1…68781`) byte-identically (`8/8`) in a clean detached worktree outside the repository, completes the protocol §8.2 reconstruction (`39/39` PRIN-arm raw files and `39/39` normalized/sensitivity digests on both arms; `25/39` reference-arm raw files due to the unpinned reference PDF `CreationDate` timestamp, recorded as a reconstruction limitation under §11.3 item 2), and confirms zero discrepancies on an independent recount. It opens (and does not execute) the four-session conditional correction cycle **`EXP-002-D1`** ([`2026-10-14-exp002-d1-s1..s4`](../sessions/contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md)), adds an erratum admonition to the Parity Report, and sets session **`0164` (EXP-003 E1) to `BLOCKED`** (with every later campaign session `0165`–`0194` inheriting the block under campaign plan §3.3 and §10.4 items 2–5 until S1→S4 close and `EXP-002-r1` returns a non-reversal verdict, or a Plan §8.3 amendment is adopted). The report was **verified and accepted by the maintainer
(MichaelMaillet) 2026-10-15 UTC** and the `EXP-002-D1` S1 correction scope was
approved as written (`report.md` §14); acceptance does not release `0164`.

**`EXP-002-D1` CORRECTION CYCLE COMPLETE — S4 CLOSED 2026-10-16 UTC; `EXP-002-r1`
AUTHORIZED; SESSION `0164` STILL BLOCKED.** All four contingency sessions ran in
strict S1→S4 order
([`2026-10-14-exp002-d1-s1..s4`](../sessions/contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md);
closure record in the
[correction audit](../audits/2026-10-15-exp002-d1-correction-audit.md)
`## S4 — closure`). The root cause of H3's refutation was on the **PRIN side**:
the WP-034 port of nine figure generators dropped or re-encoded **34 drawing
arguments**, and controlled substitution on the frozen `prinet==3.0.0` reference
explains every differing byte with **0 unexplained** — so campaign plan §10.4
item 3 (the "the 3.0 conclusion was itself the erroneous side" route) was **not**
invoked. S2 audited (`PASS-WITH-FINDINGS`: one D2, one D3, six D4, **no D1**);
S3 dispositioned every open finding with a `CLEAN` delta re-audit; S4 issued
**PSR-041** ([`041-project-state.md`](../reports/041-project-state.md)), updated
every register, added a dated 2026-10-16 update to the
[Parity Report](../sphinx/parity_report.rst), and appended **append-only erratum
2** naming `EXP-002-r1` to the [E5 report](EXP-002-api-benchmark-result-and-reproduction-parity/report.md)
§15.

On the corrected generator the approved §5.4 comparison policy gives **39/39
equal** and the §11.3 pre-exposure sensitivity policy gives **14/39 equal**, with
all **25** residuals classified, **0 unclassified**, and every one a writer or
host property (14 PDFs differing only in the Info **key set** — the reference
writes 3 keys including a wall-clock `CreationDate`, PRIN 4 fixed keys including
`ModDate`; 11 `.tex` tables differing only in **line terminators** — reference
CRLF from its text-mode writer on Windows, PRIN LF).

**`EXP-002`'s verdicts are unchanged: H1 `CONFIRMED`, H2 `CONFIRMED`, H4
`CONFIRMED`, and H3 `REFUTED`.** That verdict was computed from immutable,
manifested `RUN-` artefacts at the source the record froze; the generator was
corrected *after* E3, so a later correction cannot retroactively change it.
`EXP-002`'s frozen `preregistration.md`, tolerances, normalization policies,
digests and everything under `benchmarks/results/EXP-002/` are never edited.
**Nothing in this correction confirms H3 — only `EXP-002-r1` can produce a new
verdict.**

Per campaign plan §10.4 item 4 the experiment is therefore re-run as a **new
record**, [`EXP-002-r1`](EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md),
authorized at S4 with a new pre-registration and new run IDs, never reusing
`EXP-002`'s run IDs or artefacts. **This is a record skeleton only: no r1
E-stage has run, no `RUN-` directory exists, and no r1 run is authorized by this
closure** — the maintainer declares each E-stage session in turn. Audit finding
**`EXP002D1-S2-F1`** (D3) is carried into that authorization: because the two
registered H3 comparison policies now point at different verdicts on a corrected
generator, r1's E1/E2 must deliberately register which policy decides H3, what
status the other has, and what a disagreement means — replacing or restating
`EXP-002`'s §11.3 item 1 clause in the new record, fixed **before its first
`RUN-` directory exists**, with outcome exposure disclosed, and **without
altering either writer** to chase §11.3 equality (PRIN's fixed PDF metadata is
what makes H4 hold). **S4 does not choose that rule**; it is an open item
requiring the maintainer's approval before r1's E1 starts. `EXP-002-r1`'s E3 is
additionally gated by **DV-047** (rebuild `python/prin/_prin_core.pyd` and record
its new SHA-256 so a new observation does not record stale-binary provenance).

**Plan amendment #52** was adopted on the maintainer's authority: the seven
hosted check workflows (`rust`, `python`, `parity`, `repro`, `snyk`, `gpu`,
`nightly`) are re-enabled and stay active until the campaign's experimentation is
complete — the close of session `0194` (Campaign E6 synthesis), or earlier on
maintainer instruction — superseding amendment #48's "hosted checks disabled"
rule and amendment #50's EXP-002-only window. Hosted results are additional
evidence recorded verbatim (workflow, run ID, head SHA, conclusion, link) for the
exact SHA they ran on; the Windows full local gate stays **mandatory and
authoritative**, local results are never described as "CI green", and a hosted
run does not establish behaviour on platforms it did not run on. A red hosted
check is triaged and recorded, never waived, skipped, deselected or hidden. The
branch ruleset is unchanged and this is **not** the amendment #48 lift.

**Session `0164` (EXP-003 E1) and every later campaign session (`0165`–`0194`)
remain `BLOCKED`.** The S4 closure, the merge of PR #34 and the re-enabling of
the hosted workflows do **not** release them; under campaign plan §10.4 item 5
release requires `EXP-002-r1`'s E5 verdict to be a non-reversal, verified and
accepted by the maintainer, or a Project Plan §8.3 amendment accepting a changed
conclusion with full justification.

**`EXP-002-r1` E1 PREPARED — 2026-10-20 UTC (branch `campaign/exp002-r1-e1`,
baseline `M = 5677858c15d784d881b23d43dff5029d199b0a18`).** Following the merge
of PR #34 (`305416fb`) and PR #35 (`5677858c`, closing DV-045 and completing
the Ubuntu-24.04/Node-24 workflow migration with 31/31 check runs green and two
consecutive wholly green scheduled `nightly.yml` runs `39203786555` and
`39373976832`), the maintainer authorized `EXP-002-r1` E1 and ratified three
governing decisions: (1) the **Re-run (`-r1`/`-rN`) Namespace & Evidence
Isolation Rule** (campaign plan §7.1, §10.4 item 4, amendment #10), binding
`EXP-002-r1` to disjoint roots (`benchmarks/results/EXP-002-r1/`,
`DOCS/test_and_benchmark_results/EXP-002-r1/`, `EVIDENCE/exp002-r1-e1/`..`e5/`)
and `exp002_r1_` module basenames while grandfathering `EXP-001-r1`'s shared
`benchmarks/results/EXP-001/` directory; (2) the **`EXP002D1-S2-F1` H3
comparison-policy decision**, registering the approved §5.4 policy as the sole
primary decision rule for H3 and retaining the §11.3 pre-exposure policy as a
reported, non-gating writer-property diagnostic requiring 0 unclassified
residuals (with outcome exposure disclosed); and (3) **DV-047 closure**
(stale `.venv/Lib/site-packages/prin_core.pth` removed, `python/prin/_prin_core.pyd`
rebuilt from clean `main` at `5677858c`, and its SHA-256 pinned in
`benchmarks/campaign/exp002_r1_driver.py` and `preregistration.md` §1.1).
`preregistration.md` remains `DRAFT`; no E3 execution or `RUN-` creation
occurred at E1, and sessions `0164`–`0194` remain `BLOCKED`.

**`EXP-002-r1` E2 APPROVED — 2026-10-21 UTC (branch `campaign/exp002-r1-e2`, PR #37).**
Independent review, S4 retro-audit of `EXP002D1-S4-F2`/`F3`, and Lean 4 / Z3
formal verification of comparison policies completed (`e2-review.md`). The
maintainer ratified decisions 1–11, approved the protocol, and authorized E3
execution. Pre-registration froze at `F = 10ac3c04f44a1f68869c94c1dfae1c1c1a189460`.

**`EXP-002-r1` E3 EXECUTED — 2026-10-21 UTC (branch `campaign/exp002-r1-e3`, PR #38).**
All five registered runs completed cleanly at source
`R = e65076eb7ae97100d40ea32c60229dd40ed51033` through `exp002_r1_driver.py`:
five immutable `RUN-` directories under `benchmarks/results/EXP-002-r1/`, 0
aborts, 0 reruns, CPU wall time ~20 s. Retained publication and input roots
captured under `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/`. No verdicts
were computed at E3; handoff passed to E4.

**`EXP-002-r1` E4 ANALYSED — 2026-10-21 / 2026-10-22 UTC (branch `campaign/exp002-r1-e4`, PR #40).**
The analysis module `analysis/exp002_r1_e4_analysis.py` and its 176 synthetic unit
tests were committed and applied to the five E3 records: **H1 `CONFIRMED`**
(`175/175` symbols, `172/172` owned), **H2 `CONFIRMED`** (`62/62` archival
predicates preserved), **H3 `CONFIRMED`** under the primary §5.4 policy
(`39/39` publication files equal), **H4 `CONFIRMED`** (`39/39` raw-byte
identical determinism). The diagnostic §11.3 policy yielded `14/39` equal, with
all 25 residuals classified (`14` `pdf_info_keyset`, `11`
`tex_crlf_line_terminator`, `0` unclassified). Campaign plan §10.4 D1 flag was
**NOT RAISED (`False`)**. All seven analysis outputs and `report-manifest.json`
(`6cd12f2d…`) were generated and committed.

**`EXP-002-r1` E5 REPORTED — 2026-10-22 UTC (branch `campaign/exp002-r1-e5`).**
The [E5 report](EXP-002-r1-api-benchmark-result-and-reproduction-parity/report.md)
issues all verdicts in full, confirms **non-reversal** (`H1 CONFIRMED`, `H2
CONFIRMED`, `H3 CONFIRMED` [primary §5.4], `H4 CONFIRMED`, `D1 = False`), verifies
retained bytes (`39/39` publication files and `172/172` inputs per run),
regenerates all analysis deliverables byte-identically (`8/8`) in a clean
detached worktree outside the repository, completes clean-checkout
reconstruction (`39/39` PRIN raw files, `39/39` normalized/sensitivity digests),
and appends Erratum 3 to predecessor `EXP-002/report.md` §15. **The campaign plan
§10.4 item 5 exit condition is met, but release of session `0164` (EXP-003 E1) and
downstream sessions `0165`–`0194` remains BLOCKED pending formal maintainer
verification and acceptance of this report.**

## Layout

```
experiments/
├── campaign-plan.md              # Phase 7 campaign plan (E0, session 0153)
└── EXP-NNN[-rN]-<slug>/
    ├── README.md                 # skeleton: status, sessions, inherited rules (E0)
    ├── preregistration.md        # frozen at execution start (E1/E2)
    ├── log.md                    # execution log (E3)
    ├── analysis/                 # committed E4 analysis code (campaign plan §7.4 item 2)
    ├── analysis.md               # E4 analysis record: verdicts, deviations, threats
    ├── report.md                 # results vs expectations (E5)
    └── report-manifest.json      # SHA-256 of regenerated figures/tables (E4/E5)
```

Analysis scripts under `analysis/` must carry **globally unique file names**
(prefix with the campaign id, e.g. `exp001_e4_analysis.py`,
`exp002_r1_e4_analysis.py`). The record roots
are sibling directories without `__init__.py`, so the `mypy DOCS/experiments/
--strict` local/CI gate derives bare module names from file names and aborts
with `Duplicate module named ...` (not a typing error) if two campaigns ship the
same basename; `--explicit-package-bases` does not help.
`tests/test_campaign_quality_gates.py` enforces this (PR32-F12).

Raw run artefacts live under `benchmarks/results/EXP-NNN/RUN-<UTC>-<SHA>-<label>/`
(JSON, tracked, one per-run `manifest.json`; campaign plan §7); figures/tables
regenerate from them via `prin.reporting`. Under the **Re-run (`-r1`/`-rN`)
Namespace & Evidence Isolation Rule** (campaign plan §7.1, amendment #10), every
re-run from `EXP-002-r1` onward uses its own disjoint raw-artefact directory
(`benchmarks/results/EXP-NNN-rN/`), generated-output directory
(`DOCS/test_and_benchmark_results/EXP-NNN-rN/`), stage-labelled evidence
directories (`EVIDENCE/expNNN-rN-e1/`..`e5/`), and `expNNN_rN_` driver/test/analysis
module prefix (`EXP-001-r1` is grandfathered in `benchmarks/results/EXP-001/`
with `-r1-` run labels).

| Experiment | Track | Record root |
|---|---|---|
| EXP-001 | C1 | [`EXP-001-golden-trajectory-numerical-parity/`](EXP-001-golden-trajectory-numerical-parity/README.md) |
| EXP-001-r1 | C1 | [`EXP-001-r1-golden-trajectory-numerical-parity/`](EXP-001-r1-golden-trajectory-numerical-parity/README.md) — **COMPLETE: E5 VERIFIED AND ACCEPTED 2026-09-29 UTC. All five hypotheses `CONFIRMED`, D1 not raised (non-reversal); 0159 and every experiment downstream of EXP-001, plus 0194, are RELEASED. E1–E5 PR authorized, not yet opened** *(dated correction, 2026-10-11: opened and merged as PR #28)* |
| EXP-002 | C1 | [`EXP-002-api-benchmark-result-and-reproduction-parity/`](EXP-002-api-benchmark-result-and-reproduction-parity/README.md) — **E5 VERIFIED AND ACCEPTED 2026-10-15 UTC (reported 2026-10-14 UTC): H1, H2, H4 `CONFIRMED`; H3 `REFUTED` (`21/39` approved, `5/39` sensitivity) — campaign plan §10.4 D1 RAISED. Correction cycle `EXP-002-D1` CLOSED 2026-10-16 UTC (S1→S4); these verdicts are UNCHANGED and immutable — erratum 2 in `report.md` §15 points at the re-run. Session `0164` and downstream campaign sessions remain BLOCKED** |
| EXP-002-r1 | C1 | [`EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md) — **E5 REPORTED 2026-10-22 UTC (`campaign/exp002-r1-e5`): NON-REVERSAL VERDICT (H1, H2, H3 [§5.4 primary], H4 `CONFIRMED`; D1 flag `False`; §11.3 diagnostic 25/25 residuals classified, 0 unclassified). Retained bytes verified (39/39, 172/172); clean-worktree regeneration 8/8 identical; clean-checkout reconstruction 39/39 matched. Erratum 3 added to EXP-002 report §15; Parity Report updated. Session `0164` and downstream sessions `0165`–`0194` remain BLOCKED pending maintainer verification and acceptance** |
| EXP-003 | C2 | [`EXP-003-cpu-scaling-and-sweep-performance/`](EXP-003-cpu-scaling-and-sweep-performance/README.md) |
| EXP-004 | C2 | [`EXP-004-gpu-kernels-and-torch-bridge-performance/`](EXP-004-gpu-kernels-and-torch-bridge-performance/README.md) |
| EXP-005 | C3 | [`EXP-005-dynamics-chimera-and-capacity-replication/`](EXP-005-dynamics-chimera-and-capacity-replication/README.md) |
| EXP-006 | C3 | [`EXP-006-temporal-binding-phasetracker-and-ablation-replication/`](EXP-006-temporal-binding-phasetracker-and-ablation-replication/README.md) |
| EXP-007 | C3 | [`EXP-007-daemon-mot-and-adversarial-replication/`](EXP-007-daemon-mot-and-adversarial-replication/README.md) |
| EXP-008 | C4 | [`EXP-008-cross-platform-and-new-capability-characterization/`](EXP-008-cross-platform-and-new-capability-characterization/README.md) |

## Spike handoff and coverage records

Phase 0 foundation spikes also emit intermediate handoff and coverage artefacts
at the top level until they are folded into the final campaign archive in Phase 6:

- [`0013-wp004-s1-handoff.md`](0013-wp004-s1-handoff.md) — WP-004 S1 handoff to
  the S2 audit for the CubeCL fused mean-field RK4 spike.
- [`0013-wp004-s1-coverage.md`](0013-wp004-s1-coverage.md) — `cargo-llvm-cov`
  report and caveat for the non-instrumentable `#[cube(launch)]` kernel stubs.
- [`0017-wp005-s1-handoff.md`](0017-wp005-s1-handoff.md) — WP-005 S1 handoff to
  the S2 audit for the ORT backends, abi3 wheel matrix, and Phase 0 gate.
- [`0021-wp006-s1-handoff.md`](0021-wp006-s1-handoff.md) — WP-006 S1 handoff to
  the S2 audit for oscillator state, errors, and the deterministic seed.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added.
- [`0025-wp007-s1-handoff.md`](0025-wp007-s1-handoff.md) — WP-007 S1 handoff to
  the S2 audit for the oscillator dynamics models.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added.
- [`0029-wp008-s1-handoff.md`](0029-wp008-s1-handoff.md) — WP-008 S1 handoff to
  the S2 audit for the Euler, RK4, and adaptive RK45 integrators.

- [`0037-wp010-s1-handoff.md`](0037-wp010-s1-handoff.md) — WP-010 S1 handoff
  to the S2 audit for phase metrics and chimera measures.
- [`0049-wp013-s1-handoff.md`](0049-wp013-s1-handoff.md) — WP-013 S1 handoff
  to the S2 audit for continuous band networks and temporal propagation.
  Written retrospectively in S3 (session 0051) as the remedy for finding
  WP013-F3 (D3); carries a provenance caveat stating it does not alter the
  S2 verdict.
- [`0053-wp014-s1-handoff.md`](0053-wp014-s1-handoff.md) — WP-014 S1 handoff
  to the S2 audit for Tucker/HOSVD and CP/PARAFAC tensor decompositions.
  Updated in S3 to correct the reference-code claim and to record the
  single-rank vs per-mode-rank API mapping for the S4 Migration Guide.
- [`0057-wp015-s1-handoff.md`](0057-wp015-s1-handoff.md) — WP-015 S1 handoff
  to the S2 audit for the OscilloSim sparse simulation engine (`prin-sim`, CSR
  coupling, pruning, chimera integration, parity).
- [`0061-wp016-s1-handoff.md`](0061-wp016-s1-handoff.md) — WP-016 S1 handoff
  to the S2 audit for parallel parameter sweeps, CPU optimization, and Phase 2
  gate (`prin-sim`, sweep module, dispatch, benchmarks).
- [`0065-wp017-s1-handoff.md`](0065-wp017-s1-handoff.md) — WP-017 S1 handoff
  to the S2 audit for `prin-kernels` backend abstraction, CubeCL build path,
  device/dtype dispatch, preallocated buffers, and authoritative CPU references
  (`backend.rs`, `buffers.rs`, `equivalence.rs`, `mean_field_rk4.rs`,
  `mean_field_rk4/cubecl.rs`).
- [`0069-wp018-s1-handoff.md`](0069-wp018-s1-handoff.md) — WP-018 S1 handoff
  to the S2 audit for the hierarchical device-side order-parameter reduction,
  device-event timing (`TimingMethod`), and the `f64`-accumulation precision
  fix in `mean_field_rk4::cubecl`.
- [`0073-wp019-s1-handoff.md`](0073-wp019-s1-handoff.md) — WP-019 S1 handoff
  to the S2 audit for sparse k-NN coupling (`SparseKnnGraph`,
  `sparse_knn_derivatives_cpu`, `sparse_knn_coupling_cubecl`) and PAC
  modulation (`PacParams`, `pac_modulate_cpu`, `pac_modulate_cubecl`) kernels
  with CSR/index interoperability.
- [`0077-wp020-s1-handoff.md`](0077-wp020-s1-handoff.md) — WP-020 S1 handoff
  to the S2 audit for the fused three-band (delta/theta/gamma) discrete-time
  step (`discrete_step_cpu`, `discrete_step_cubecl`) and its reusable
  hierarchical order-parameter/mean-phase reduction kernels.
- [`0081-wp021-s1-handoff.md`](0081-wp021-s1-handoff.md) — WP-021 S1 handoff
  to the S2 audit for GPU integration into simulation (`prin-sim::gpu`:
  `GpuSparseKuramoto`, `GpuMeanFieldEngine`, `GpuBandStepper`), the
  CUDA-before-wgpu dispatch-priority fix applied to all four kernel
  families' `*_auto` functions, and the Phase 3 exit gate.
- [`0085-wp022-s1-handoff.md`](0085-wp022-s1-handoff.md) — WP-022 S1 handoff
  to the S2 audit for `prin-train`'s first implementation (Burn autodiff
  backend): `bands::DiscreteDeltaThetaGamma` and `layers::ResonanceLayer`,
  their `Config`/`Params`/`State` contracts, and the R24 GPU CI runner
  strategy decision (Project Plan amendment #26).
  `[RETROACTIVE UPDATE - Phase 3 recommendation implementation session,
  R21/PA3-F1]` index entry added.
- [`0089-wp023-s1-handoff.md`](0089-wp023-s1-handoff.md) — WP-023 S1 handoff
  to the S2 audit for `prin-train` inhibition, activations, energy functions,
  and HEP trainer (`inhibition.rs`, `activations.rs`, `energy.rs`, `hep.rs`,
  5 parity suites, DV-018/DV-019 observations).
- [`0093-wp024-s1-handoff.md`](0093-wp024-s1-handoff.md) — WP-024 S1 handoff
  to the S2 audit for `prin-train`'s oscillator-aware optimizers
  (`sync_gd::SyncGd`, `rip::Rip`, `scalr::Scalr`, the shared
  `feedback::OscillatorOptimizer` contract), 5 parity tests against the
  actual PRINet 3.0 optimizer classes, and the DV-020 naming-discrepancy
  disposition (session brief vs. PSR-023's WP-024 declaration).
- [`0097-wp025-s1-handoff.md`](0097-wp025-s1-handoff.md) — WP-025 S1 handoff
  to the S2 audit for the production PyO3/DLPack `torch.autograd.Function`
  bridge: `ResonanceLayerBridge`/`GatedPhaseActivationBridge` (Rust
  forward/backward, recompute-on-backward design correction found via a
  failing `gradcheck`, panic-safe checkpoint loading), the
  `crates/prin-py/src/bindings/train.rs` architecture, boundary-overhead
  benchmark evidence (criterion vs. `pytest-benchmark`, both <5%), and the
  DV-005 re-audit (CPU path delivered; CUDA Burn backend recorded
  out-of-scope, not silently dropped).
- [`0101-wp026-s1-handoff.md`](0101-wp026-s1-handoff.md) — WP-026 S1 handoff
  to the S2 audit for `prin-train`'s `PhaseTracker` (primary contribution),
  `HybridPRINetV2`, `OscillatoryAttention`, the `SlotAttentionModule`/
  `TemporalSlotAttentionMOT` comparison baseline, four structural ablation
  variants, and `AdaptiveOscillatorAllocator`/`DynamicPhaseTracker`; 2 new
  golden-value parity tests, a discovered-and-fixed `Backend::seed`
  shared-global-RNG test-parallelism hazard, and the explicit
  carried-scope disposition for `crates/prin-py`/`python/prin/nn` PyO3
  bindings (not delivered this session — see the handoff note).
- [`0101-exec-wp026-s1-handoff.md`](0101-exec-wp026-s1-handoff.md) —
  Exec-WP-026 S1 (executive secondary session) handoff to the S2 audit for
  the PyO3 bindings and Python wrappers carried forward from session 0101:
  six new bridge modules, generic `apply_rust_bridge` helper, `validate_shapes`
  on all six new types (a real checkpoint-corruption bug found and fixed),
  86 new Python tests at 100% coverage.
- [`0105-wp027-s1-handoff.md`](0105-wp027-s1-handoff.md) — WP-027 S1 handoff
  to the S2 audit for trainable-stack integration and Phase 4 gate:
  `dataset.rs` (temporal CLEVR-N generator), `losses.rs` (Hungarian similarity
  + temporal smoothness), `trainer.rs` (Rust-native training loop), optimizer
  bridges (`SyncGd`/`Scalr`/`Rip`), bridge profiling, serialization
  acceptance, and the IP-threshold validation run (mean IP 1.00000 ≥ 0.99868).
- [`0105-wp027-temporal-clevr-n-validation.json`](0105-wp027-temporal-clevr-n-validation.json) —
  Raw evidence for the Phase 4 gate IP-threshold acceptance criterion
  (3 seeds, canonical protocol, per-seed IP = 1.0).
- [`0109-wp028-s1-handoff.md`](0109-wp028-s1-handoff.md) — WP-028 S1 handoff
  to the S2 audit for the ONNX controller and backend selection: the
  `prin-daemon` state/control types (bit-exact parity with PRINet 3.0), the
  VitisAI -> DirectML -> CPU selection policy and its deterministic fallback
  ladder, the runtime-independent ONNX graph reader, SHA-256 manifest
  verification, and the Python `prin.daemon` inference layer. Also records the
  three maintainer decisions taken in-session (WP-028 scope approval, the
  Project Plan risk-register-#4 invocation, and the R31/DV-005 Phase 5
  scoping disposition).
- [`0113-wp029-s1-handoff.md`](0113-wp029-s1-handoff.md) — WP-029 S1 handoff
  to the S2 audit for the daemon runtime and lock-free control buffer:
  `prin-daemon::daemon`'s `SubconsciousDaemon` (native background thread,
  bounded drop-oldest state queue, dead-letter queue, error escalation,
  bounded shutdown) and `ControlSignalBuffer` (lock-free, `ArcSwap`-backed
  replacement for PRINet 3.0's `threading.Lock`-guarded buffer), with a
  concurrency-safety argument backed by dedicated stress/race/lifecycle
  tests. Records the scope decision to defer the PyO3/Python daemon binding
  (GIL-release design hazard) to a future session, and the latency pilot
  comparing the lock-free buffer against both a same-language `Mutex`
  re-implementation and the actual PRINet 3.0 reference
  (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`).
- [`0117-wp030-s1-handoff.md`](0117-wp030-s1-handoff.md) — WP-030 S1 handoff
  to the S2 audit for training hooks and MOT evaluation:
  `prin-daemon::hooks::TrainingHooks` (loss EMA/variance, gradient-norm EMA,
  step-latency percentiles feeding `SubconsciousState`, proven wired into a
  running `SubconsciousDaemon`) and `prin-daemon::mot::MotAccumulator`
  (CLEAR-MOT/IDF1 metrics validated against real `py-motmetrics` 1.4.0
  output on 10 fixed scenarios, backed by a from-scratch rectangular
  Hungarian solver). Records the scope decision to keep both deliverables in
  `prin-daemon` rather than a new crate, defer `PhaseTracker`
  tracker-wiring to a future `prin-py`/`python/prin/eval` session, and a
  same-session fix for an unrelated newly-published `cargo audit` finding
  (`RUSTSEC-2026-0267`, `stable-vec`).
- [`0121-wp031-s1-handoff.md`](0121-wp031-s1-handoff.md) — WP-031 S1 handoff
  to the S2 audit for temporal experiments, statistics, and adversarial
  tooling: fair PT-vs-SA training framework, temporal tracking-quality
  metrics, statistical utilities, FLOPs estimation, and FGSM/PGD adversarial
  robustness evaluation.
- [`0125-wp032-s1-handoff.md`](0125-wp032-s1-handoff.md) — WP-032 S1 handoff
  to the S2 audit for daemon/evaluation integration and Phase 5 gate:
  cross-crate PyO3 bindings for daemon, hooks, MOT, temporal, stats, and
  adversarial APIs; GIL-safe native daemon lifecycle; provider and latency
  acceptance evidence.
- [`0129-wp033-s1-handoff.md`](0129-wp033-s1-handoff.md) — WP-033 S1 handoff
  to the S2 audit for the unified `benchrunner` CLI, shared config/
  environment-capture/timing infrastructure, and the nine topic category
  packages: the verified 58-vs-62 legacy-script-count correction, the
  `kernels/` `criterion`-subprocess-orchestration design (no PyO3 binding
  exists for `prin-kernels`), and the full legacy-script traceability table.
- [`0133-wp034-s1-handoff.md`](0133-wp034-s1-handoff.md) — WP-034 S1 handoff
  to the S2 audit for deterministic benchmark reports/leaderboards, all 14
  verifiable stored-artefact figure generators, all 11 byte-comparable LaTeX
  fragments, and torch/Rust-call profiling integration; records the brief's
  15-vs-14 figure-count discrepancy for audit disposition.
- [`0137-wp035-s1-handoff.md`](0137-wp035-s1-handoff.md) — WP-035 S1 handoff
  to the S2 audit for the active reproduction CLI, append-only 172-record
  SHA-256 artefact manifest, fail-closed tamper handling, all 39 generated
  figure/table files, and enabled `repro.yml` execution.
- [`0141-wp036-s1-handoff.md`](0141-wp036-s1-handoff.md) — running WP-036 S1
  handoff: sub-pass 0141A (API-freeze, direct re-export, compatibility-alias,
  unavailable-backend evidence) and sub-pass 0141B (`prin-tensor` /
  `prin-train` PyO3 bindings for the eight owned Bucket D/E symbols, with the
  twelve-symbol Bucket E descope recorded).
- [`0141-wp036-s1-dd-dispositions.md`](0141-wp036-s1-dd-dispositions.md) —
  D-D symbol disposition appendix: 30 GPU/Triton/no-CPU-analogue rows (0141A)
  plus 12 deferred trainable-layer-rebuild rows (0141B), subject to the
  session-0142 S2 audit veto.
- [`0144A-wp036a-s1-handoff.md`](0144A-wp036a-s1-handoff.md) — WP-036A S1
  handoff to the S2 audit for trainable compatibility layers: 13 D-D-appendix
  symbols (rows 31–42, 44) delivered as real `prin-train` Burn implementations
  across four sub-passes (0144A1–0144A4), with per-symbol evidence maps,
  float64 gradcheck for all 11 trainable modules, and PRINet-3.0
  forward-parity at documented tolerances.
- [`0144E-wp036b-s1-handoff.md`](0144E-wp036b-s1-handoff.md) — running WP-036B
  S1 handoff: records the 805-vs-498 scope-count discrepancy, initial 481-test
  collection plus the missing `benchmarks.clevr_n` import error, amendment #35's
  six-pass strict-port split (`0144E1`–`0144E6`), exact per-file counts, and the
  Rust-backed compatibility/no-semantic-test-rewrite disposition.
- [`0144Q-wp036e-s1-handoff.md`](0144Q-wp036e-s1-handoff.md) — WP-036E S1
  handoff: plan amendment #43 re-scope, the `0144Q1`–`0144Q3` decomposition,
  and each sub-pass's device-resident-execution evidence.
- [`0144U-wp036f-s1-handoff.md`](0144U-wp036f-s1-handoff.md) — WP-036F S1
  handoff to the S2 audit `0144V`: the controller ONNX graph re-exported with
  three-input `Gemm` nodes so `DmlExecutionProvider` executes it, the CPU
  bit-identity gate (48 cases), the DirectML agreement + latency evidence, and
  the acceptance-criterion → evidence map.
- [`0144Y-wp036g-s1-handoff.md`](0144Y-wp036g-s1-handoff.md) — WP-036G S1
  handoff to `0144Z`: consolidated DV dispositions, DV-035, the dormant Linux
  Triton workflow, both fragility resolutions, security evidence, and the
  itemized Phase 7 entry draft.
- [`0145-wp037-s1-handoff.md`](0145-wp037-s1-handoff.md) — WP-037 S1 handoff to
  the S2 audit `0146`: the completed Sphinx guides/API surface, four executed
  notebooks, docs.rs wiring, paper artefact wiring, and the draft Parity Report;
  the acceptance-criterion → evidence map; four recorded deviations
  (`docs/`→`DOCS/sphinx/` path adaptation, the cp1252 notebook constraint, the
  Sphinx duplicate-object resolution, notebook naming); and six out-of-scope
  discoveries, including two `prin.nn` layers that were not then trainable by a
  torch optimizer against a Migration Guide claim that they were (WP037-F1;
  fixed by the WP-037 S3 corrective delta).
- [`hotfix-dv019-handoff.md`](hotfix-dv019-handoff.md) — Dedicated
  hotfix/correction session for DV-019 (flaky `prin-train` tests,
  `burn-autodiff` cross-thread graph-server interaction). Handoff from
  `Hotfix-DV019` session (2026-08-26).

Placement note (EA-002 E-F10): the WP-009 S1 handoff note lives at
[`../sessions/phase-1/wp009-s1-handoff-note.md`](../sessions/phase-1/wp009-s1-handoff-note.md)
because its original `0033-` sequence prefix collided with the session brief
ID in this directory layout (WP009-F5). S1 handoff notes belong here under
their session sequence prefix; the WP-009 rename is the documented exception.

## Rules (summary)

- **The campaign plan governs all eight experiments**: pre-register against
  its §2.1 reconciled targets, its §5 hardware matrix, §6 seeds, §7 artefact
  layout, §8 budget caps, §9 statistics, and §10 abort/D1 rules.

- **No execution without a committed, approved pre-registration** including
  expected results and failure/abort conditions.
- Pre-registrations are immutable once execution starts; deviations are
  reported in `report.md`, never edited in.
- All runs are reported — aborted runs stay in the log with the tripped
  criterion.
- Template: [`TEMPLATE_Preregistration.md`](TEMPLATE_Preregistration.md).

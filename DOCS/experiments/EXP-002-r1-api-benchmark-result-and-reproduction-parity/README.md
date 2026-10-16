# EXP-002-r1 — API, benchmark-result, and reproduction parity, re-run (track C1)

**Status:** **AUTHORIZED — RECORD SKELETON ONLY. No E-stage has run.**
Created by the `EXP-002-D1` S4 correction-documentation session
(2026-10-16 UTC) under campaign plan §10.4 item 4. **No pre-registration
exists yet, no `RUN-` directory exists, no driver has been authored or frozen,
and no observation has been collected.** E1 may begin only when the maintainer
declares the E1 session *and* the open decision in
["Open decision this record must settle before E1"](#open-decision-this-record-must-settle-before-e1)
below is approved.

**Drafting AI pair:** Qwen3.8-max (this skeleton). Every later E-stage document
names its own drafting AI pair and records the maintainer's verification
(campaign plan §12 item 7; Experimentation Standards §4).

**Predecessor:** [`EXP-002`](../EXP-002-api-benchmark-result-and-reproduction-parity/README.md)
(E5 reported 2026-10-14 UTC, verified and accepted 2026-10-15 UTC; H1, H2, H4
`CONFIRMED`; **H3 `REFUTED`**, campaign plan §10.4 **D1** raised).
**Correction cycle:** [`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../audits/2026-10-15-exp002-d1-correction-audit.md)
(S1 complete, S2 `PASS-WITH-FINDINGS`, S3 delta re-audit `CLEAN`, S4 closure
appended).
**Campaign plan row:** [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-002 / C1
(this re-run inherits that row's reconciled targets; it is not a new registry
entry and no session number changes).

This is a **new experiment record** per campaign plan §10.4 item 4. The
original `EXP-002` record is **immutable**: its verdicts, tolerances,
normalization policies, digests, protocol, `preregistration.md` and everything
under `benchmarks/results/EXP-002/` are never edited, and its only post-issue
change is the dated erratum pointer in `report.md` §15 that names this record.
**r1 does not revise `EXP-002`'s `H3 REFUTED` verdict.** Only r1's own E4/E5,
applying r1's own frozen decision rule to r1's own new runs, can produce a new
verdict.

## Why a re-run exists

`EXP-002`'s H3 was refuted on the **PRIN side**: the WP-034 port of nine figure
generators dropped or re-encoded **34 drawing arguments**, so 18 of the 39
registered publication files (the `.pdf` and `.png` of figures 5, 7, 8, 9, 10,
11, 12, 14, 15) differed from an independent render by the frozen
`prinet==3.0.0` reference generator. The `EXP-002-D1` correction cycle fixed
the port and attributed every differing byte by controlled substitution on the
frozen reference, with **0 unexplained** — so campaign plan §10.4 item 3 (the
"the 3.0 conclusion was itself defective" route, which needs an EMA-style
mathematical audit) was **not** invoked and is not available to r1.

On the corrected generator, measured after the fix
([`EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt`](../../../EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt)):

| Comparison policy | Result on the corrected generator |
|---|---|
| Approved §5.4 policy | **39/39 equal** |
| §11.3 pre-exposure sensitivity policy | **14/39 equal** |

All **25** residuals under the sensitivity policy are classified, **0
unclassified**, and every one is a writer or host property rather than a
scientific difference:

- **14 PDFs** differ only in the Info **key set** — the reference writes 3 keys
  including a wall-clock `CreationDate`; PRIN writes 4 fixed keys including
  `ModDate`. PRIN's fixed metadata is what makes its H4 (raw determinism) hold.
- **11 `.tex` tables** differ only in **line terminators** — the reference's
  text-mode writer on Windows emits CRLF; PRIN emits LF.

`EXP-002`'s own verdict is unchanged by any of this and stays `H3 REFUTED`.

## Open decision this record must settle before E1

**This skeleton deliberately does not choose the deciding rule.** Carrying audit
finding **`EXP002D1-S2-F1`** (D3, `ASSIGNED` by S3 to S4 and to this record;
correction audit §S3.3), the choice belongs to r1's own pre-registration and
review, and — because it determines what a `REFUTED`/`CONFIRMED` H3 means — it
**requires the maintainer's approval before r1's E1 starts**. S4 records the
question; it does not answer it.

E1/E2 must register, deliberately rather than by inheritance:

1. **Name the deciding rule.** State which comparison policy decides H3 and
   what status the other has — for example §5.4 as the sole primary with §11.3
   retained as a disclosed writer-property sensitivity, **or** a corrected
   sensitivity policy that canonicalizes the two writer properties. S3 did not
   choose; S4 does not choose.
2. **Replace or restate the §11.3 item 1 clause.** `EXP-002`'s clause ("if the
   two verdicts differ, E5 must state that H3's verdict depends on a comparison
   amendment made after outcome exposure, and must not report either verdict
   alone") was drafted for the pre-correction state, in which *both* policies
   refuted. Under a corrected generator it would turn a writer property into a
   policy-dependent verdict. r1 must say, **before any r1 data exist**, what a
   disagreement between the two policies means.
3. **Fix the choice before the first `RUN-` directory exists.** `EXP-002` froze
   its protocol at its first `RUN-` creation in session `0161`
   (2026-10-12T21:27:05Z); campaign plan §12 item 4 gives r1 the same freeze
   semantics. The choice must be committed and approved before that point.
4. **Disclose outcome exposure.** The choice is made with knowledge of
   `EXP-002`'s results and of S1/S2's residual classification, exactly as
   `EXP-002`'s own E1/E2 disclosed for its amendments. The disclosure belongs in
   the pre-registration header and is repeated in E5.
5. **Do not chase §11.3 equality by changing a writer.** PRIN's fixed PDF
   metadata is what makes H4 (raw determinism) hold, so it must not be altered;
   the frozen `prinet==3.0.0` reference must not be altered either.
6. **Never edit `EXP-002`'s frozen `preregistration.md`.** Any change lives only
   in this record.

**No amendment is requested by this skeleton.** Campaign plan §10.4 item 4
already requires a new pre-registration for the re-run, and that document is the
governed place for this registration. If r1's E1 or E2 finds the choice cannot be
made inside a pre-registration — for instance if §10.4 item 5's "not a reversal"
test would itself need reinterpreting — that is an amendment matter: **draft it
for maintainer approval, do not adopt it.**

## Rules inherited from the campaign plan

- This experiment **does not reuse** `EXP-002`'s run IDs or artefacts (campaign
  plan §10.4 item 4). Every raw artefact goes to a **new**
  `RUN-<UTC>-<SHA>-<label>/` directory with its own per-run `manifest.json`
  (§7.1–§7.3); `EXP-002`'s five existing `RUN-` directories are never appended
  to, edited, or re-manifested.
- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and cite
  the reconciliation — including amendment #51's **14 verifiable figures**
  (figures 2–15; there was never a figure 1), giving the registered reproduction
  target of **14 figures × 2 formats + 11 tables = 39 generated files** against
  the 172-record `paper/artefact_manifest.json`. Hardware only from §5; seeds
  per §6 (`seed_key = 2`, as `EXP-002` used — a new `seed_key` is an E1
  decision that must be stated, not inherited silently); artefact layout per §7;
  budget caps per §8; statistics per §9; abort/D1 rules per §10.
- One E-stage per session, no stage collapsing (§12 item 2); each stage commits
  locally on its own `campaign/exp002-r1-<stage>` branch (§12 item 3); drivers
  are authored in E1 with tests in tandem and Snyk Code, approved in E2, and
  **frozen at E3 start** (§12 item 1).
- Exploratory analyses appear only under an "Exploratory" heading and never feed
  a verdict (§12 item 5). Errata follow Experimentation Standards §4: erratum in
  the experiment report **and** the Parity Report, plus a CHANGELOG line (§12
  item 6).
- Analysis scripts under `analysis/` carry **globally unique** file names
  (prefix `exp002_r1_`): the record roots are sibling directories without
  `__init__.py`, so `mypy DOCS/experiments/ --strict` aborts on a duplicate bare
  module name (`tests/test_campaign_quality_gates.py` enforces this, PR32-F12).
  `EXP-002`'s `exp002_e4_analysis.py` already occupies the `exp002_` prefix.
- **Raw-artefact root is an E1 decision, not an inheritance.** The `EXP-001-r1`
  precedent shared `benchmarks/results/EXP-001/` with the original record, new
  runs being distinguishable by their own SHA and timestamp; campaign plan §7.1
  also permits a distinct root. E1 must state which applies here and register
  the §8 storage budget consequence (a shared root counts against `EXP-002`'s
  existing allocation; a new root needs its own). Nothing is created by this
  skeleton.

## Carried obligations that gate r1's stages

| Obligation | Source | Gate |
|---|---|---|
| Rebuild `python/prin/_prin_core.pyd` and remove the stale `prin_core.pth`, recording the new `.pyd` SHA-256 in the driver, so a new observation does not record stale-binary provenance | **DV-047** (OPEN) | **before r1's E3 run** |
| Settle the open decision above and register both H3 comparison policies deliberately | **`EXP002D1-S2-F1`** (D3, `ASSIGNED`) | **before r1's E1 starts** (maintainer approval) and frozen **before the first `RUN-`** |
| `cargo audit` is red on 9 transitive advisories; a hosted `audit` job is visible again under amendment #52 and a red hosted check is triaged and recorded, never waived | **DV-045** (OPEN) | recorded at every stage's gate |
| `gpu-cuda` intermittently fails `flops::tests::measure_wall_time_calls_warmup_and_runs_exact_counts`; re-check on every `gpu-cuda` run while hosted workflows are enabled | **DV-046** (OPEN) | each hosted `gpu-cuda` run |
| The required full suite has not been demonstrated green in one pass on the maintainer host (Windows `WinError 5` rename in `.pytest_basetemp`; DV-032's host-timing ratio). Run the local gate with IDE and security tooling quiet where possible, record the actual exit status, and never describe a rerun-until-green as a pass | **O-1** (correction audit §S3.9 item 9; PSR-041 ledger) | every stage's local gate |

## Blocking condition — IN FORCE

Session **`0164`** (EXP-003 E1) and every later campaign session
(**`0165`–`0194`**) are **BLOCKED** under campaign plan §3.3 and §10.4 items
2–5 until this experiment's E5 verdict **is not a reversal** and is
**verified and accepted by the maintainer**, or the maintainer records a Project
Plan §8.3 amendment accepting a changed conclusion with full justification.

**The `EXP-002-D1` S4 closure, the merge of PR #34, and the re-enabling of the
hosted workflows under Plan amendment #52 do NOT release `0164`** (nor
`0165`–`0194`). Neither does the creation of this record, nor any later E1, E2,
E3 or E4 stage: §10.4 item 5 keys the release to E5's verdict and the
maintainer's acceptance of it. The `EXP-001-r1` precedent is explicit that a
correction merge, E1 completion, E2 approval, E3 execution and E4's clean exit
each release nothing on their own.

**No r1 run is authorized by this skeleton**, and no experiment session may
start from it. The maintainer declares each E-stage session in turn.

## What this directory will hold

| File | Created by | Frozen when |
|---|---|---|
| `README.md` | **S4 (this file)** | Updated as the experiment progresses |
| `preregistration.md` | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | At the first `RUN-` creation (campaign plan §12 item 4); never edited after freeze |
| `e1-handoff.md` | E1 | Entry and verification evidence record |
| `e2-review.md` | E2 | Independent-review and maintainer-decision record |
| `log.md` | E3 | Never edited after E3 close |
| `analysis/` | E4 | Committed **before** adjudication (§7.4 item 2); never edited to change a verdict |
| `analysis.md` | E4 | Never edited after E4 close; corrections are errata |
| `report.md` | E5 | Never edited after issue; corrections are errata |
| `report-manifest.json` | E4/E5 | SHA-256 of regenerated outputs plus every input run manifest |

None of these except `README.md` exists yet.

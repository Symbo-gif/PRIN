# PRIN Project State Report — Cycle 041

**Date:** 2026-10-16 UTC
**Cycle:** 041 (EXP-002 D1 correction documentation — campaign plan §10.4)
**Completed sessions:** Contingency correction cycle `EXP-002-D1` — S1
(2026-10-15 UTC), S2 (2026-10-15 UTC), S3 (2026-10-16 UTC), S4 (2026-10-16
UTC). No planned session `0001`–`0198` and no campaign E-stage is completed by
this cycle; `0164` remains **BLOCKED**, not started.
**Author:** Qwen3.8-max (AI pair)
**Git state:** `hotfix/exp002-d1-figure-parity` @ `71d1c59071f1935e4c70975355d5289abec6e337`
plus this report's own commit (a commit cannot name itself). PR #34 carries the
whole `fd8854ed..` correction range to `main`; **its push and merge are
authorized by the maintainer for this session** (chat authorization A1,
2026-10-16 UTC). **No merge commit SHA is stated anywhere in this repository:**
`main` is PR-only, so a post-merge record cannot be committed here, and campaign
plan §12 item 3 assigns the merge SHA to the next governed session.
**Status:** **ISSUED** — local validation complete under the Plan amendment #48
regime, with the seven hosted check workflows re-enabled by **Plan amendment
#52** from 2026-10-16 UTC. Windows x86_64 only; **Linux and macOS were not
tested locally**. Hosted runs are additional evidence for the exact SHA they ran
on and establish nothing about platforms they did not exercise.

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 7 — Experimentation campaign. The campaign is **BLOCKED**
  at session `0164` (EXP-003 E1), and every later campaign session
  (`0165`–`0194`) inherits the block (campaign plan §3.3, §10.4 items 2–5).
- **This cycle delivered:** the fourth and final session of the `EXP-002-D1`
  conditional correction cycle that campaign plan §10.4 mandates. S1 established
  the root cause of H3's refutation **on the PRIN side** — the WP-034 port of
  nine figure generators dropped or re-encoded **34 drawing arguments** — and
  attributed every differing byte by controlled substitution on the frozen
  `prinet==3.0.0` reference, with **0 unexplained**, so campaign plan §10.4
  item 3 (the "the 3.0 conclusion was itself the erroneous side" route, which
  requires an EMA-style mathematical audit) was **not** invoked. S2 audited the
  range and returned **`PASS-WITH-FINDINGS`** (one D2, one D3, six D4, **no
  D1**, no systemic drift), verifying all five brief-specific items by
  independent re-execution. S3 dispositioned every open finding with a
  **`CLEAN`** delta re-audit. S4 (this cycle) issues this PSR, updates every
  register, aligns the Parity Report, appends the E5 erratum pointer, authorizes
  `EXP-002-r1`, performs the cold review that S3's four-round cap left owing,
  and adopts Plan amendment #52.
- **EXP-002 E5 report formally announced** (Experimentation Standards §2 E5;
  campaign plan §10.4 item 3). The E5 report
  (`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md`)
  was issued 2026-10-14 UTC by session `0163` and **verified and accepted by the
  maintainer (MichaelMaillet) 2026-10-15 UTC**. Verdicts: **H1 `CONFIRMED`**
  (`175/175` `api_symbols`, `172/172` `legacy_api_names`), **H2 `CONFIRMED`**
  (`62/62` `claim_comparator_records`), **H4 `CONFIRMED`** (`39/39`
  raw-byte-identical across two PRIN processes), and **H3 `REFUTED`** (`21/39`
  `generated_files` equal under the approved §5.4 policy, `5/39` under the §11.3
  pre-exposure sensitivity policy) — the D1 that opened this correction cycle.
- **What the correction changed, and what it did not.** On the corrected
  generator the approved §5.4 policy gives **39/39 equal** and the §11.3
  sensitivity policy gives **14/39 equal**, with all **25** residuals classified,
  **0 unclassified**, and every one a writer or host property (14 PDFs differing
  only in the Info **key set**; 11 `.tex` tables differing only in **line
  terminators**). **`EXP-002`'s verdicts are nevertheless unchanged and
  immutable: H3 stays `REFUTED`.** That verdict was computed from immutable,
  manifested `RUN-` artefacts at the source the record froze, and the generator
  was corrected *after* E3, so a later correction cannot retroactively change
  it. **Nothing in this cycle confirms H3, and no statement here should be read
  as doing so; only `EXP-002-r1` can produce a new H3 verdict.** `EXP-002`'s
  frozen `preregistration.md`, tolerances, normalization policies, digests,
  protocol and everything under `benchmarks/results/EXP-002/` are untouched; its
  only post-issue change is append-only erratum **2** in `report.md` §15
  (`git diff --numstat`: **2 added, 0 deleted**).
- **`EXP-002-r1` authorized** as a new experiment record per campaign plan
  §10.4 item 4
  (`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md`):
  new pre-registration, new run IDs, never reusing `EXP-002`'s run IDs or
  artefacts. **This is a record skeleton only.** No E-stage has run, no
  pre-registration exists, **no `RUN-` directory was created**, and no r1 run is
  authorized by this closure. Audit finding `EXP002D1-S2-F1` is carried into it
  (§3 below), and **the deciding rule is deliberately not chosen here** — see §5.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS. Plan amendment **#52** is
  adopted this cycle (§4); amendments #48 (local-validation regime), #49
  (supervised local validation) and #50 (the EXP-002-only hosted window, now
  superseded by #52) remain in force as amended.
- **Audit:** `DOCS/audits/2026-10-15-exp002-d1-correction-audit.md` — S2 verdict
  **`PASS-WITH-FINDINGS`**; S3 delta re-audit **`CLEAN`**; S3 verdict
  **`S3 COMPLETE, with residuals O-1 and O-2`**; **`## S4 — closure` appended
  this cycle** (pure append, 0 deleted lines). All eight S2 findings are
  dispositioned; the two S3 observations and the one S4 finding are carried in
  §3 below.
- **Session Register:** the `EXP-002-D1` contingency row is set to
  **COMPLETE 2026-10-16 UTC** and `contingencies/README.md` moves it to "Closed
  corrections", leaving "Open corrections" empty. Session `0164` stays
  **BLOCKED** (§5).

---

## 2. Metric trends

This is a **documentation-and-evidence cycle**: the measured change set over
`6b55c6ba..71d1c590` is **29 files, 0 `.rs`, 0 dependency manifests, 0
first-party `.py`, 0 `.github/` workflow files**
(`EVIDENCE/exp002-d1-s4/gate/change-set.txt`). Three conditional gate legs are
therefore **not run, by measurement rather than by assumption**:
`cargo fmt`/`clippy`/`test` (no Rust changed), `cargo audit`/`pip-audit`/Snyk
Open Source (no dependency manifest changed; `cargo audit` is separately red on
**DV-045**, out of this cycle's bounded scope), and per-change Python coverage
(no first-party Python changed, so there are no changed executable lines to
cover).

| Metric | Previous (PSR-040) | Current (PSR-041) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1,604 passed, 0 failed, 1 ignored | **not re-measured — no Rust source changed** (0 `.rs` files in the diff). PSR-040's figure is the last measurement and is **not** re-claimed as current | 100% where defined |
| Python fast suite (`tests/ -m "not slow and not gpu"`) | 5,667 passed / 184 skipped (full, leg 25) | **4,044 passed, 178 skipped, 55 deselected, 59 warnings in 2,122.53 s (0:35:22), exit 0** — the required **clean single pass** | 100% — **MET** |
| Python **required full suite** (`tests/ parity/`) | 5,667 passed / 184 skipped / 0 failed, exit 0 | **6,331 passed, 184 skipped, 0 failed, 61 warnings in 6,189.62 s (1:43:09), exit 0** — run **ONCE**, recorded at its actual exit status, **no rerun-until-green**; 0 `FAILED`/`ERROR` lines; 5 faulthandler 300 s stack dumps, each followed by a pass (amendment #49: a dump is not a kill and not proof of a hang) | 100% — **MET** |
| Coverage (new/changed code) | not measured — DV-033 OPEN | **not applicable this cycle** — 0 first-party Python lines changed, so there is no changed-code coverage to measure. **DV-033 stays OPEN** | ≥95% — **NOT MET (unmeasured, DV-033)** |
| Docstring coverage (interrogate) | 97.6% | **97.6%** (1,011 statements, 987 documented, 24 missing), exit 0 | ≥95% overall, 100% public — **MET** |
| Parity cases passing / total defined | `parity/` 2,144 passed / 1 skipped | **inside the required full-suite run** (`tests/ parity/`, 6,331 passed / 0 failed). A separate parity-only count was not taken this cycle, so none is claimed | 100% at tolerance — **MET** |
| Clippy/ruff/mypy/bandit/audit findings | 0 findings | **0 findings**: `ruff check` "All checks passed!"; `ruff format --check` 370 files + 3 files (`DOCS/experiments/`, source-only include) already formatted; `mypy --strict` no issues in 62 (`python/prin`) and 3 (`DOCS/experiments/`) source files; `bandit` 27,882 LOC and 3,901 LOC (evidence dirs), both exit 0 | 0 — **MET** |
| Snyk Code (`--severity-threshold=low`) | 0 HIGH / 0 MEDIUM / 97 LOW | **0 HIGH / 0 MEDIUM / 97 LOW** (Total issues 97, Ignored 0), `snyk whoami` → `Symbo-gif` verified first. The **three** ratified `python/PT` LOW locations are all present and visible: `changed_line_coverage.py:98`, `decomposition_rerun_check.py:92`, `snyk_sarif_filter.py:142` | 0 medium+ — **MET** |
| Secret scanning (pinned gitleaks 8.30.1) | no leaks | **no leaks** — full history **776 commits**, ~104.18 MB in 27.9 s; `--staged` 0 commits, no leaks | 0 leaks — **MET** |
| Sphinx `-W --keep-going` from a **deleted** `_build` | build succeeded | **build succeeded**, exit 0 | 0 warnings — **MET** |
| Benchmark regression gates | not exercised (nightly paused) | **not exercised locally.** Amendment #52 re-enables `nightly.yml` from 2026-10-16; **DV-036** and its reference-host re-baseline gates before `0168`/`0173` stay OPEN and are closed by nothing in this cycle | none tripped |
| Governance checkers | all exit 0 | **all exit 0** — global-session registration (18 Executive Audit reports), DV-register gates (**47** DV rows against **198** session-register entries), skipif probes (no registration-probe guards) | pass |
| `check_deviation_ledger.py` | 039→040: exit 0 (142 → 146 rows) | **040→041: exit 0 (146 → 159 rows)** | pass |
| EXP-002 frozen-artefact integrity | `verify_manifest` 5/5, input manifest `300cdc09…cce5` | **`TOTAL FAILURES: 0`**, exit 0 — the frozen input manifest recomputes to the pinned `300cdc09…cce5` and `verify_manifest(reference results, INPUT_MANIFEST)` passes on **172** records | 0 failures — **MET** |
| Delta re-audit | `CLEAN` | **`CLEAN`** — pre-fix reproduction **18 failed / 75 passed** and **10 failed** (both must fail, exit 1); module restored byte-identically; post-fix **103 passed**, exit 0; `# overall: 0` | regression reproduces then vanishes |
| Evidence index self-checks | s1 12, s2 30, s3 129 files; 0/0 each | **s1 12, s2 30, s3 129 files, each 0 unindexed / 0 dangling**; s4 reported with the final pass | 0 unindexed, 0 dangling |
| Cold review | S3: four rounds (the cap), loop **did not converge** → O-2 | **S4 performed the review O-2 owed**, by measurement: **1 CONFIRMED defect** (`EXP002D1-S4-F1`, D2, **latent**), superseded by a fail-closed copy; **12** checks verified the round-4 fixes as claimed; **1** claim REFUTED as a defect | 0 unreviewed fixes |

---

## 3. Deviation ledger (cumulative)

### 3.1–3.4 (unchanged)

Sections 3.1–3.3 of PSR-039 and §3.4 of PSR-040 are carried forward unchanged;
see those reports. No earlier finding is reopened by this delta.

### 3.5 EXP-002 D1 corrective cumulative-ledger delta (2026-10-16 UTC)

**Cumulative ledger delta:** Inherit PSR-040 §3 (which inherits PSR-039 §3,
which inherits PSR-038 §3); append the thirteen rows below. No inherited row's
summary is changed, and no inherited ID is restated. Historical PSRs remain
unchanged.

Two carried items are noted rather than silently restated: **`S2-F3`** and
**`S2-F4`** (both D4, `CARRIED(2)` in PSR-040) are now past Development Workflow
§5's "a finding may be carried at most once (D4 only); anything older becomes D2
automatically" limit. Their existing dispositions (an API-freeze decision and a
future-WP disposition) are retained and unchanged, and the escalation is
**flagged for the maintainer in §5** rather than applied unilaterally in a
documentation cycle that touches neither symbol.

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| EXP002-D1-H3 | 041 | D1 | EXP-002 H3 `REFUTED`: 18/39 generated files differ from the frozen `prinet==3.0.0` reference generator (21/39 equal under the approved §5.4 policy, 5/39 under the §11.3 sensitivity policy) | AMENDED | Root cause on the PRIN side (34 drawing arguments dropped or re-encoded by the WP-034 port), fixed and re-proved; 0 unexplained bytes. The E5 verdict is **immutable and stays `REFUTED`**; `EXP-002-r1` is authorized as a new record and only it can produce a new verdict. Correction audit §S1.3, §S3.8; erratum 2 in `report.md` §15 |
| EXP002D1-S2-F1 | 041 | D3 | The two registered H3 comparison policies disagree about the verdict on a corrected generator (approved §5.4 gives 39/39 equal, §11.3 sensitivity gives 14/39) | AMENDED | **ASSIGNED** by S3, **carried into the `EXP-002-r1` authorization by S4**: its E1/E2 must deliberately register which policy decides H3, the status of the other, and what a disagreement means, before its first `RUN-` directory exists and with outcome exposure disclosed. No amendment; `EXP-002`'s frozen pre-registration is never edited. **The deciding rule is an open item for the maintainer — S4 did not choose it.** Correction audit §S3.3; `EXP-002-r1/README.md` |
| EXP002D1-S2-F2 | 041 | D2 | The required full suite was red on a notebook cell timeout of 900 s that was not sized from in-suite evidence | FIXED | Route (a): per-notebook cell bounds re-sized from cited evidence (`BOUND_MARGIN` × the largest *completed* contended duration, rounded up), tied to it by an equality test in both directions. No test deselected, skipped, xfailed or shortened; no assertion changed. The timeout did not recur. **S4's full-suite run confirms the bounds under real contention**: notebook 02 took 1,199.85 s and notebook 01 594.63 s against bounds of 10,800 s and 2,700 s. Correction audit §S3.2 |
| EXP002D1-S2-F3 | 041 | D4 | The local `snyk` CLI credentials had expired, blocking the CLI route to the §6.2 Snyk Code gate | FIXED | Maintainer re-authenticated; `snyk whoami` verified before the CLI was relied on (`Symbo-gif`, exit 0, snyk 1.1306.2). The blocked state is retained in the record rather than overwritten (amendment #48 item 2). Correction audit §S2.14 |
| EXP002D1-S2-F4 | 041 | D4 | A committed S1 evidence file was not indexed by its own README | FIXED | README row added (+1, −0); the evidence file's bytes untouched; `index_selfcheck.py` reports 12 files, 0 unindexed / 0 dangling. Correction audit §S3.1 |
| EXP002D1-S2-F5 | 041 | D4 | The fast-gate module docstring understated its own scope ("byte-material" arguments, when all 34 registered divergences are pinned) | FIXED | Docstring corrected; AST identical outside it, proved mechanically; 34/34 still pinned. Correction audit §S3.1 |
| EXP002D1-S2-F6 | 041 | D4 | One known argument infidelity survived the fix (the reference's fig13 per-series `label`) | FIXED | Restored for argument-faithfulness, with byte-immateriality **re-proved** rather than assumed: 93 parity tests pass, artist-level equivalence 14/14 EQUAL, and all 28 figure files raw-byte identical before and after, against a negative control differing on exactly the 18 D1 files. S4's delta re-audit reproduces the red/green again (18 failed / 75 passed pre-fix, 103 passed post-fix). Correction audit §S3.1 |
| EXP002D1-S2-F7 | 041 | D4 | An absolute claim in the touched module docstring was imprecise ("no scientific quantity is recomputed") | FIXED | Reworded to list the derived quantities by kind, explicitly not exhaustively; the first rewording was itself an over-claim and was corrected after cold review. Both commits docstring-only. Correction audit §S3.1 |
| EXP002D1-S2-F8 | 041 | D4 | Two residual Snyk Code `python/PT` (CWE-23) LOW findings in S2's own audit instruments | AMENDED | **RATIFIED** by the maintainer 2026-10-16 UTC with a recorded Coding Standards §6.2 threat assessment; remediated twice on the `PR23-F1` pattern and proved non-vacuous, **not suppressed** (nothing added to `.snyk`, no ignore or severity exclusion). Stays visible and is re-checked every cycle — S4's rescan reports both. Correction audit §S2.14, §S3.4 |
| EXP002D1-S2-F8-L3 | 041 | D4 | A third same-class Snyk Code `python/PT` LOW finding at `EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py:142`, written after S2's own CLI scan so no S2 scan could have reported it | AMENDED | **RATIFIED at S4** under the maintainer's 2026-10-16 authorization, all four ratification conditions verified by reading the file and reproducing the finding; §6.2 threat assessment recorded in the correction audit's `## S4 — closure`. **Not a suppression**: `.snyk` unchanged, no ignore, S2's file not edited. Re-checked every cycle; S4's rescan reports it |
| EXP002D1-S3-O1 | 041 | D3 | The required full suite had not produced an exit 0 in one pass on the maintainer host (S3: two runs, two different single host-contention failures, each passing alone) | AMENDED | **The premise is discharged by measurement, not by a policy change.** S4 ran the required full suite **exactly once** and it **exited 0** — 6,331 passed / 184 skipped / 0 failed in 1:43:09, tree clean before and after, **no rerun-until-green and nothing deselected, skipped or weakened**. It passed **under heavy contention**, which is the stronger result: host CPU median **96.5 %** (84 of 111 samples ≥ 90 %), pytest receiving a median **0.192 CPU-s per wall-second**, with `Devin.exe` (3,845 CPU-s), `mc-fw-host.exe` (2,979), `java.exe` (976) and `MsMpEng.exe` (98) among the non-PRIN consumers. **Note this diverges from decision 4A, which anticipated the local record staying at exit 1** and named a hosted pass as the closure evidence; the hosted corroboration is still obtained and reported in the session record. **The contention sensitivity is not cured** — the operating guidance in §5 stands, and a recurrence is a new observation, not a regression of this one. Correction audit §S3.7, §S3.9 item 9, `## S4 — closure` |
| EXP002D1-S3-O2 | 041 | D4 | S3's cold-review loop reached its four-round cap, leaving round 4's fixes without a further cold review | FIXED | S4 performed the owed review **read-only and by measurement** on the committed round-4 fixes, reproducing every suspected defect with a command and classifying it CONFIRMED / REFUTED / NOT REPRODUCIBLE as S3's triage does. Result: 1 CONFIRMED defect (below), 12 checks verifying the fixes as claimed, 1 claim REFUTED as a defect. `EVIDENCE/exp002-d1-s4/o2-review/triage.md` |
| EXP002D1-S4-F1 | 041 | D2 | `final_legs.sh` aggregated five legs with `grep -a MARKER FILE \| grep -qv OK && overall=1`, which **fails open**: with no input lines `grep -qv` exits 1, so a leg whose record is missing, empty, or holds no marker line reads as PASSING | FIXED | Found by S4's O-2 review and reproduced over seven record shapes. The same class round 4 fixed for the Snyk leg alone (S3 triage T4-2); five grep-aggregated siblings were left unchanged. **Latent**: a fail-closed check re-applied to all seven committed S3 records gives 0 failures, so **no recorded S3 result was masked**. S3's file is **not edited**; a corrected copy using a fail-closed `require_marker` helper supersedes it, with a red-before and green-after demonstration, and **S4's own gate ran the corrected copy**. Severity reasoning and the D4 alternative considered are in §5. `EVIDENCE/exp002-d1-s4/o2-review/` |

---

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| **#52** | Development Workflow and Audit Standards §3 ("Local-validation regime", new item 11) / `.github/workflows/*` (enable state only) / `CLAUDE.md`, `.claude/CLAUDE.md` / `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` / `EXP-002-D1` S4 and every campaign session through `0194` | Re-enables the seven hosted check workflows on the maintainer's authority and keeps them active **until the campaign's experimentation is complete** — the close of the campaign plan's final experiment session `0194` (Campaign E6 synthesis), or the maintainer's earlier instruction, whichever is first. Supersedes amendment #48's "hosted checks disabled" rule and amendment #50's EXP-002-only window from the effective date. Hosted results are verbatim additional evidence for the exact SHA they ran on; the Windows full local gate stays **mandatory and authoritative**; local results are never called "CI green"; a hosted run does not establish behaviour on platforms it did not run on; a red hosted check is triaged and recorded, never waived, skipped, deselected or hidden. **Not applied:** the ruleset 22150076 `required_status_checks` rule stays removed, no `v*` tag is pushed, no blocked session is released. **Not the amendment #48 lift:** Linux/macOS and the three-OS wheel matrix stay suspended, not satisfied (DoD items 2 and 4) | maintainer approval (MichaelMaillet, 2026-10-16 UTC), verbatim: *"authorize hosted workflows to merge and keep active until experimentation is complete"* |

No other Plan or campaign-plan amendment was found necessary this cycle, so none
was drafted. Amendment #52's footprint mirrors #50's: `grep -rn "amendment #50"`
was run across `CLAUDE.md`, `.claude/CLAUDE.md`, `AGENTS.md`, the Plan, the
standards and the registers, and the equivalent short exception or update was
added in each place #50 touched. **`AGENTS.md` needed no change** — #50 never
touched it (it cites only #49). Historical session, audit and frozen
experiment-record text was not edited, and **no file under `.github/` was
modified**.

---

## 5. Risks and blockers

- **Session `0164` (EXP-003 E1) remains BLOCKED, and so does every later
  campaign session (`0165`–`0194`).** Stated explicitly here and in every
  register this cycle touched: **S4 closing, the merge of PR #34, and the
  re-enabling of the hosted workflows under amendment #52 do NOT release them.**
  Under campaign plan §10.4 item 5 release requires `EXP-002-r1`'s E5 verdict to
  be a non-reversal, **verified and accepted by the maintainer**, or a Project
  Plan §8.3 amendment accepting a changed conclusion with full justification. The
  `EXP-001-r1` precedent is explicit that a correction merge, E1 completion, E2
  approval, E3 execution and E4's clean exit each release nothing on their own.
- **An open scientific decision gates `EXP-002-r1` E1, and it is the
  maintainer's.** Because the two registered H3 comparison policies now point at
  different verdicts on a corrected generator, r1's pre-registration must name
  which policy decides H3, what status the other has, and what a disagreement
  means — replacing or restating `EXP-002`'s §11.3 item 1 clause, fixed **before
  the first `RUN-` directory exists**, with outcome exposure disclosed, and
  **without altering either writer** to chase §11.3 equality (PRIN's fixed PDF
  metadata is what makes H4 hold). **S4 deliberately did not choose this rule**;
  it is recorded as an explicit open item in `EXP-002-r1/README.md` requiring the
  maintainer's approval before E1 starts. Choosing it inside a documentation
  session, after outcome exposure and without that approval, is exactly the
  failure mode `EXP002D1-S2-F1` was raised to prevent.
- **The local gate is contention-sensitive, and that is not cured by one green
  run.** O-1's premise is discharged (§3.5) — the required full suite exited 0 in
  a single pass — but it did so while the host sat at a **median 96.5 % CPU** with
  pytest receiving **0.192 CPU-s per wall-second**, and S3 observed two red runs
  on two *different* single tests. So the risk of recurrence is real and the
  F2 bounds are what absorbed it. **Operating guidance for the maintainer (S4
  cannot change these settings, and stopped or killed no process belonging to the
  maintainer):** run the local gate with the IDE and security tooling quiet, and
  **exclude `.pytest_basetemp` from IDE workspace scanning and from
  security-software real-time scanning**. `AGENTS.md` mandates that exact
  in-repo basetemp name (reporting's pytest-only output allowlist recognizes it,
  not suffixed variants), so the directory cannot simply be moved outside the
  workspace. A recurrence should be raised as a **new** observation.
- **O-1's hosted corroboration cannot be committed here.** Amendment #52 makes a
  hosted full-suite run at the PR #34 head commit possible, but `main` is
  PR-only, so no post-merge record can be committed and a second push would
  change the head SHA and restart the very checks being awaited. The run's
  verbatim result (workflow, run ID, head SHA, conclusion) is therefore reported
  in the **session record**; the next governed session should enter it alongside
  the merge SHA (campaign plan §12 item 3).
- **DV-032 was deliberately NOT widened, and no new DV row was opened.** O-1's
  `WinError 5` rename is a different class from DV-032's host-sensitive *timing
  ratios* — it is the `AGENTS.md`-documented pytest temporary-directory
  contention class — and widening DV-032 would merge two distinct mechanisms
  under one disposition. No DV row was opened because the register consolidates
  "work … whose full validation is assigned to a future Work Package or phase",
  while O-1's evidence was obtained in this session.
- **PR #34 not yet merged at the time of writing.** Its push and merge are
  authorized by the maintainer for this session (A1). The merge commit SHA and
  the hosted run results are recorded in the session report, not here.
- **DV-045, DV-046, DV-047 stay OPEN** and are re-exposed to hosted runs by
  amendment #52: `cargo audit` is red on nine transitive advisories (**DV-045**,
  out of this cycle's bounded scope — no dependency, advisory ignore or audit
  configuration was changed, and a red hosted `audit` job is triaged and
  recorded, never waived); `gpu-cuda` has an intermittent `flops` failure
  (**DV-046**, re-checked on every `gpu-cuda` run while workflows are enabled);
  and `python/prin/_prin_core.pyd` is stale relative to campaign source
  (**DV-047**), whose re-audit gate — rebuild and record the new `.pyd` SHA-256 —
  is carried into the `EXP-002-r1` authorization as a precondition of its E3.
- **`S2-F3` / `S2-F4` are past Development Workflow §5's one-carry limit** (both
  D4 at `CARRIED(2)`; §5 makes anything older D2 automatically). Their existing
  dispositions are retained and this cycle touches neither symbol, so the
  escalation is **flagged for the maintainer rather than applied unilaterally**
  in a documentation cycle.
- **DV-033** (per-change Python coverage on this host) stays OPEN; this cycle
  adds no first-party Python lines, so it neither closes nor worsens it.
  **DV-034** (single self-hosted `PRIN-GPU-Runner` SPOF) stays OPEN — re-enabling
  `gpu.yml` does not remove the dependency, and with the required-status-check
  rule still removed `gpu-cuda`/`gpu-wgpu` are recorded evidence rather than a
  hard merge gate. The runner was verified **online and idle** before the push.
  **DV-036**, `DV036-F5` at `0166` and the re-baseline gates before
  `0168`/`0173` stay OPEN and remain additionally gated behind the campaign
  block.
- **Native push protection remains disabled** (pre-existing, flagged since
  amendment #48; DV-009 records that GitHub native secret scanning is
  unavailable on this repository). As the compensating control the pinned,
  checksum-verified gitleaks 8.30.1 ran over the **full history (776 commits,
  104.18 MB)** and `--staged` before the push: **no leaks**.
- **Linux/macOS and the three-OS wheel matrix stay suspended, not satisfied**
  (DoD items 2 and 4). Amendment #52 re-enables hosted checks; it is **not** the
  amendment #48 lift, and hosted Linux/macOS results do not re-validate those
  items.

---

## 6. Next work package declaration

**No new WP is declared.** The next action is the maintainer's, in this order:

1. **Merge PR #34** (authorized for this session), then record the merge SHA,
   `tools/check_ci_green.py <merge-SHA>` output and the hosted full-suite result
   in the next governed session's entry evidence (campaign plan §12 item 3).
2. **Settle the open `EXP-002-r1` H3 comparison-policy decision** (§5) — which
   policy decides, the status of the other, and what a disagreement means.
3. **Declare `EXP-002-r1` E1.** It cannot start before step 2, and its E3 is
   additionally gated by **DV-047**.
4. **Session `0164` and `0165`–`0194` stay BLOCKED** until `EXP-002-r1`'s E5
   verdict is a non-reversal, verified and accepted by the maintainer, or a
   Project Plan §8.3 amendment is adopted.
5. **Hosted workflows stay enabled** under amendment #52 until `0194` closes or
   the maintainer instructs otherwise; the disabling is then recorded.

---

## 7. Verification

This is the **local gate under Plan amendment #48**, as extended by amendment
#52: **not** a green `origin/main` CI result, Windows x86_64 only, **Linux and
macOS not tested locally**. Every command is recorded verbatim with its UTC
start/end, exit code and `git rev-parse HEAD` in
[`EVIDENCE/exp002-d1-s4/gate/`](../../EVIDENCE/exp002-d1-s4/gate/), indexed by
[`EVIDENCE/exp002-d1-s4/README.md`](../../EVIDENCE/exp002-d1-s4/README.md), and
narrated in the correction audit's `## S4 — closure` §S4.7. Legs ran **strictly
sequentially** — pytest never concurrent with cargo or with another pytest
(`AGENTS.md`) — and **before** any hosted workflow was enabled, so a self-hosted
runner on this machine could not compete with the local gate. Tools: Python
3.14.0, pytest 9.1.1, ruff, mypy, snyk 1.1306.2, gitleaks 8.30.1, on
`MINGW64_NT-10.0-26300`.

**Executed and green (every leg exit 0):** the two required suites (fast
**4,044 passed / 178 skipped / 55 deselected**, 0:35:22; full **6,331 passed /
184 skipped / 0 failed**, 1:43:09, run **once**); `ruff check` and both
`ruff format --check` forms (370 + 3 files already formatted); three
`mypy --strict` legs (62 and 3 source files, no issues); `interrogate`
**97.6 %**; `bandit` over 27,882 and 3,901 LOC; the three governance checkers
that do not need this report (18 EA reports; 47 DV rows against 198 session
entries; no probe guards); Sphinx `-W --keep-going` from a **deleted** `_build`
(**build succeeded**); pinned gitleaks over the full history (**776 commits,
104.18 MB, no leaks**) and `--staged` (**no leaks**); Snyk Code CLI
(**0 HIGH / 0 MEDIUM / 97 LOW**, `snyk whoami` verified first, all three
ratified `python/PT` locations visible); `verify_manifest` (**TOTAL FAILURES:
0**; input manifest recomputes to the pinned `300cdc09…cce5`; 172 records PASS);
the delta re-audit (**`CLEAN`**: 18 failed / 75 passed and 10 failed pre-fix,
module restored byte-identically, 103 passed post-fix); and the index
self-checks of `exp002-d1-s1`/`-s2`/`-s3` (12 / 30 / 129 files, **0 unindexed,
0 dangling** each). `check_deviation_ledger.py 040 041` and the `exp002-d1-s4`
index self-check run in the final pass, after this report exists.

**Not run, by measurement rather than assumption** (the change set is
documentation and evidence only — **0 `.rs`, 0 dependency manifests, 0
first-party `.py`, 0 workflow files**; `gate/change-set.txt`): `cargo
fmt`/`clippy`/`test` and `cargo llvm-cov`/`cargo doc`; `cargo audit`,
`pip-audit` and Snyk Open Source (`cargo audit` is separately red on **DV-045**,
out of scope, and no dependency or audit configuration was touched); and
per-change Python coverage (no changed executable lines). **Snyk Code through
the MCP route was not used** — no Snyk MCP tool was exposed in this session, so
it is recorded as **not run**, never as passed or as blocked-and-therefore-clean;
the CLI leg, which Coding Standards §6.4 also permits, completed.

**Nothing was weakened to obtain any result above:** no test skipped, deselected
or xfailed, no assertion or tolerance changed, no lint or security suppression
added, and **no process belonging to the maintainer stopped or killed**.

**Immutability, before and after** (`EVIDENCE/exp002-d1-s4/immutability.sh`,
range `6b55c6ba..HEAD`, run before the records were committed and again on the
final commit): the EXP-002 record changed **only** by the §15 erratum append
(**+2, −0**, `report.md` the only file); `benchmarks/results/EXP-002/`,
`.github/`, `Cargo.toml`, `Cargo.lock` and `pyproject.toml` are **empty**;
`EVIDENCE/exp002-d1-s1/`, `-s2/` and `-s3/` are **unedited**; this correction
audit is a **pure append (0 deleted lines)**; and the S4 brief's closure
checklist and carried sections are **byte-identical** (7,921 bytes both sides
after trailing-blank-line normalisation), its only two deleted lines being the
Status and Blocked-numbered-session headers this session is directed to update.

**Hosted evidence (Plan amendment #52).** The seven check workflows were enabled
with `gh workflow enable` — **no file under `.github/` was modified**, verified
by the empty `.github/` diff above, so enabling required no workflow edit and no
STOP condition was reached. The listings before and after are recorded in
[`gate/workflows-before.txt`](../../EVIDENCE/exp002-d1-s4/gate/workflows-before.txt)
and [`gate/workflows-after.txt`](../../EVIDENCE/exp002-d1-s4/gate/workflows-after.txt).
The branch ruleset was not touched and no required check was added, removed or
marked non-required. **Hosted run results are recorded in the session report,
not in this repository**, because `main` is PR-only and a post-merge commit is
not possible. **No hosted result is described as "CI green" for the local gate,
and no hosted run is cited as evidence about a platform it did not exercise.**

See §5 for retained open items and
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../audits/2026-10-15-exp002-d1-correction-audit.md)
`## S4 — closure` for the full closure record.

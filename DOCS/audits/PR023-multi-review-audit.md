# PRIN Audit Report — PR #23 multi-review round (EXP-001 E3–E5)

**Date:** 2026-09-23 UTC
**Auditor:** Claude Opus 5 (AI pair), independently re-deriving every finding
from the repository — not taking any reviewer's assertion on its word. This
report follows [`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md) and the
severity scale of
[`Development_Workflow_and_Audit_Standards.md`](../standards/Development_Workflow_and_Audit_Standards.md)
§5, reusing the event-class precedent set by
[`PR017-devin-review-audit.md`](PR017-devin-review-audit.md) for external code
review on an open PR (no dedicated governance document exists for this class,
and PR #23 is not a Session-Cycle S2).
**Scope:** every review left on PR #23 (`campaign/0158-exp001-e5` → `main`)
at head `60cc387`, and the repository state they describe —
`tools/reproduce.py`, `tests/test_reproduce.py`,
`DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/` (report,
README, analysis module), `DOCS/sphinx/parity_report.rst`, `CHANGELOG.md`,
`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `DOCS/sessions/` registers and
contingency briefs, `DOCS/audits/2026-09-23-dv036-nightly-correction-audit.md`.
**Trigger:** GitHub PR #23. Seven independent review runs (one declined):

| Reviewer | Kind | Findings raised |
|---|---|---|
| `Copilot` | automated (GitHub) | 4 (1 High, 3 Low) |
| `coderabbitai[bot]` | automated | 3 actionable + 1 pre-merge check |
| `Sourcery` | automated | 0 — declined, diff exceeds its 150,000-character limit |
| Qwen Code | independent LLM review | 0 new; validated the 7 bot findings |
| Devin | independent LLM review | 2 new refinements; validated the 7 bot findings |
| Kimi | independent LLM review | 0 new; validated the 7 bot findings |
| Cline | independent LLM review | **1 new substantive finding**; validated the 7 bot findings |

**Active brief:** no session-brief file — a PR review-response round on session
0158's branch, the same ad-hoc governance class as `PR017-devin-review`.
Session 0158 is COMPLETE and its record is immutable; corrections to it are
errata (campaign plan §12 item 6), which is how the two report-level findings
below are discharged.
**Git state:** `campaign/0158-exp001-e5` @ `60cc387` (pre-remediation);
remediation commits follow this report.
**Verdict:** `PASS-WITH-FINDINGS` → remediated in the same round (see §7).
**No D1.** No finding touches a hypothesis verdict, tolerance, denominator,
seed, decision rule, or any measured artefact. All five EXP-001 verdicts and
both D1 declarations stand exactly as issued.

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| Independent re-derivation of every reported finding | ✅ | All 8 compiled findings re-derived from the repository; evidence in §3. |
| False positives | ✅ (1 declined, not a false positive) | `PR23-F9` (CodeRabbit docstring-coverage check) is *factually* correct but measures against a threshold this project does not use; declined with evidence (§6). No reviewer claim was found to be factually wrong. |
| Severity classification | ✅ | 2 × D2, 3 × D3, 3 × D4. **No D1** — nothing touches numerical parity, published verdicts, or measured artefacts. |
| Regression tests (A3) | ✅ | 5 new tests for `PR23-F1`; 4 of the 5 confirmed to **fail** against the pre-fix source and pass against the fix (§3.1). |
| Numerical parity + invariants (A4) | ✅ | EXP-001 E4 analysis re-run under the hardened verifier: both outputs and `report-manifest.json` byte-identical (§3.1). |
| Quality gates (A5) | ✅ | Whole-repo `ruff check` + `ruff format --check`, `mypy python/prin --strict`, `interrogate` 97.6 %, Sphinx `-W` build, and all five governance checkers pass; full suite 3,214 passed / 0 failed (§7). |
| Security (A6) | ✅ | `PR23-F1` *is* the security fix (CWE-59 class). Snyk Code 0 issues on `tools/` and `tests/`, `bandit` clean, `pip-audit` clean — actual output in §2; CI's `Snyk Code` / `Secret Scan` remain the authoritative gates. |
| Docstring/doc coverage (A7) | ✅ | New helper carries a docstring; 1 of the 5 new tests does (`test_regular_files_still_verify`) — the other 4 rely on self-descriptive names, consistent with this repository's `tests/**` docstring norm (§6); `PR23-F9` declined with evidence (§6). |
| Repository hygiene (A8) | ✅ | Claim now stated identically at all 10 sites where it appears (§3.8). |
| CI status (A9) | ✅ | 24/24 required checks green at `60cc387`, recorded in report §14.1 (§3.4). Remediation head runs its own checks. |
| Artefact trail (A10) | ✅ | This report, `CHANGELOG.md` `[Unreleased]`, `DOCS/audits/README.md` index entry, E5 report §15 errata. |

## 2. Methodology

Reviews were fetched from the GitHub API rather than read from a summary, then
de-duplicated: the seven automated findings recur across the four independent
LLM reviews, so each distinct defect is compiled once and every reviewer that
raised it is recorded against it (§3). Each finding was then re-derived from
the repository before any fix was written.

```bash
gh api "repos/Symbo-gif/PRIN/pulls/23/comments?per_page=100" --paginate   # 7 review comments
gh api "repos/Symbo-gif/PRIN/issues/23/comments?per_page=100" --paginate  # 7 issue comments
gh api repos/Symbo-gif/PRIN/rulesets/22150076 \
  --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context'
gh api repos/Symbo-gif/PRIN/commits/60cc387/check-runs --paginate \
  --jq '.check_runs[] | "\(.name)\t\(.conclusion)"'
```

Local gate, executed on the remediation working tree (Windows 11, Python
3.14.0, project `.venv`):

```powershell
.venv\Scripts\python -m pytest tests/test_reproduce.py -q
.venv\Scripts\python -m pytest tests/test_exp001_e4_analysis.py tests/test_exp001_driver.py -q -m "not slow and not gpu"
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py
.venv\Scripts\python -m ruff format --check tools/reproduce.py tests/test_reproduce.py
.venv\Scripts\python -m mypy --strict tools/reproduce.py
.venv\Scripts\python "DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/analysis/exp001_e4_analysis.py"
.venv\Scripts\python tools/check_dv_register_gates.py
.venv\Scripts\python tools/check_skipif_probes.py
.venv\Scripts\python tools/check_global_session_registration.py
.venv\Scripts\python tools/wp001_baseline.py check
```

Actual results are quoted in §3 and §7. Where a gate was not run, this report
says so rather than claiming it passed (Coding Standards §6 item 5).

**Security gates (Coding Standards §6).** `tools/reproduce.py` and
`tests/test_reproduce.py` are modified first-party Python, so Snyk Code
applies; no dependency manifest changed, so Snyk Open Source, `cargo audit`,
and `pip-audit` have no changed input. Local runs (Snyk CLI `1.1306.2`, org
`symbo-gif`):

```text
snyk code test --severity-threshold=medium tools/    ->  Total issues: 0   (exit 0)
snyk code test --severity-threshold=medium tests/    ->  Total issues: 0   (exit 0)
python -m bandit -c pyproject.toml -r tools/reproduce.py  ->  no issues
python -m pip_audit .                                ->  No known vulnerabilities found
```

`pip-audit` is a compensating check only — no dependency changed, so it has no
delta attributable to this round. **CI remains the authoritative gate**: the
`Snyk Code` and `Secret Scan` required checks run on the remediation head and
their results, not these local runs, are what discharge the controls. GitHub
secret scanning and push protection remain independent, in force at push
time.

## 3. Detailed findings

### 3.1 `PR23-F1` (D2) — the shared manifest verifier followed symbolic links

*Raised by Copilot (High); independently validated by Qwen, Devin, Kimi, and
Cline, all four of whom judged the High severity overstated and recommended
fixing it in the correction cycle.*

Re-derived by reading `tools/reproduce.py`. `verify_manifest` established
**content** integrity — the bytes at this path hash to the recorded digest —
but not **path provenance**. Every call it makes follows symbolic links:
`Path.is_file`, `Path.stat`, and the `Path.open` inside `compute_sha256`. A
`manifest.json`, or any manifested `*.json`, that was a link to a file outside
the governed directory therefore verified clean. `append_manifest` had the
same gap on the writing side, and would have recorded a digest for a link.

The finding is real and its class was already recognised in this repository:
`benchmarks/campaign/exp001_driver.py::check_run_complete` rejects a symlinked
sidecar, a symlinked `manifest.json`, and any symlinked declared artefact with
no-follow `is_symlink()` checks (CWE-59), and its own comment records that it
deliberately did *not* modify the shared tool. This finding is the shared-tool
half of that same class, and it is the path
`DOCS/experiments/EXP-001-.../analysis/exp001_e4_analysis.py` actually uses.

**Severity: D2, not D1.** Exploitation requires the ability to write into the
governed directory, and anyone with that ability can equally rewrite
`manifest.json` itself; every EXP-001 artefact is committed as a regular
`100644` blob, so no published result is affected. It breaks the normative
fail-closed guarantee the function documents — a standard violation, not a
trajectory breach.

**Fix.** `_reject_symlink(path, role)` in `tools/reproduce.py`, applied
no-follow and *before* any following call, in four places: the manifest path
and each manifested artefact in `verify_manifest`, and the manifest
destination and each candidate `*.json` in `append_manifest`. The governed
directory itself is deliberately not checked — it is chosen by the caller, not
attested by the manifest, and the standard temporary root is a symlink on
macOS; the reasoning is recorded in the helper's docstring.

**Regression tests.** `tests/test_reproduce.py::TestManifestSymlinkProvenance`
(5 tests), guarded by an *executability* probe (`_probe_symlink_support`,
mirroring `tests/test_exp001_driver.py`) rather than a platform assumption,
because Windows symlink creation needs privilege or Developer Mode. The tests
were proved to pin the defect by restoring the pre-fix source with
`git show HEAD:tools/reproduce.py` and re-running them:

```text
# pre-fix (git show HEAD:tools/reproduce.py)
E   Failed: DID NOT RAISE ManifestMismatchError                  <- symlinked artefact verified CLEAN
E   AssertionError: Regex pattern did not match.
E     Expected regex: 'manifest.*symbolic link'
E     Actual message: 'unmanifested artefacts: manifest.json'
E   Failed: DID NOT RAISE ManifestMismatchError
E   tools.reproduce.ManifestFormatError: manifest schema_version must be 1
4 failed, 1 passed, 23 deselected

# post-fix
28 passed
```

The fifth test (`test_regular_files_still_verify`) passes in both states by
design: it is the no-regression control.

**No regression to the published EXP-001 record.** The E4 analysis calls this
verifier on all four run directories. Re-run under the hardened verifier:

```text
H1: REFUTED   H2a: REFUTED   H2b: CONFIRMED   H3: CONFIRMED   H4: CONFIRMED
D1 flag: RAISED
report-manifest.json: IDENTICAL (unchanged by the run)
exp001-e4-adjudication.json  12974 B  sha256 e6f6eb20...  MATCH
exp001-e4-summary.md          5783 B  sha256 4551061c...  MATCH
```

`tests/test_reproduce.py` also re-verifies the 172-record repository manifest
(`test_repository_manifest_matches_all_stored_json_artefacts`) — green.

### 3.2 `PR23-F2` (D3) — `CHANGELOG.md` contradicted the accepted record

*Copilot #2; CodeRabbit #2; confirmed by all four LLM reviews.*

`CHANGELOG.md` said the E5 report "awaits maintainer verification, and sessions
0154–0158 remain local-only, so no CI result is claimed", while `report.md`
§13 records maintainer acceptance on 2026-09-23 UTC. Devin's refinement is
correct and re-verified here: the "0154–0158" range was wrong **when written**
— `git cat-file -e b434554:tests/test_exp001_driver.py` confirms E1/E2 reached
`main` through PR #20 (`e997431`) before the report was drafted, so only
0156–0158 were ever local-only. Fixed in place; the CHANGELOG is a running
record, not a frozen report.

### 3.3 `PR23-F3` (D4) — EXP-001 README session table contradicted its own header

*Copilot #3; CodeRabbit #2; confirmed by all four LLM reviews.*

The 0158 row ended "awaiting maintainer verification" while the status block
above it recorded acceptance. Commit `60cc387` propagated the acceptance to the
header and to `SESSION_REGISTER.md` but not to the table row. Fixed in place.

### 3.4 `PR23-F4` (D3) — report §6 PD-5, §13, and §14.1 disagreed

*Copilot #4; CodeRabbit #2; Cline and Devin both noted the real defect is the
contradiction, not the placeholder.*

§14.1's placeholder was by design — campaign plan §12 item 3 has it filled by
an addendum commit after the checks report. The defect is that §13 already
claimed "PD-5 discharged there" while §14.1 was still pending and §6 PD-5 still
said the PR "is not yet created".

CI is in fact complete at `60cc387`, so §14.1 is now filled from the actual
run, which makes §13 true as written and needs no change to it:

```text
CI-green check - branch 'campaign/0158-exp001-e5', commit 60cc3875e2c91fea92a555735fe88f6024514d69
  rust green (35884672511)   python green (35884672533)   parity green (35884672514)
  repro green (35884672517)  snyk green (35884672499)     gpu green (35884672469)
RESULT: all required workflows green
```

All **24** checks required by branch ruleset `22150076` concluded `success`;
`Sourcery review` (not required) is `skipped`. §14.1 also states explicitly
that this round's own remediation commits move the head past `60cc387` and
that the final head's checks are the operative ones — §14.1's preamble
anticipates exactly this.

PD-5's body is in a report that declares itself immutable, so it is corrected
by **erratum E-1** appended at PD-5, not by rewriting it; the original text is
retained verbatim. Errata are indexed in the new report §15 and pointed to
from the header record table.

### 3.5 `PR23-F5` (D3) — `SESSION_REGISTER.md` row stale at the pushed head

*CodeRabbit #2; Devin and Cline both caught that a prior review wrongly
credited `60cc387` with this fix — it existed only as an uncommitted
working-tree edit.* Confirmed by `git diff` at the pushed head. The prepared
edit is committed in this round (and further qualified for `PR23-F8`).

### 3.6 `PR23-F6` (D4) — DV-036 S4 correction record carried superseded status lines

*CodeRabbit #3; confirmed by all four LLM reviews.*

Under a `Status: COMPLETE` header, two undated present-tense entries said
validation "remains pending", "Session 0156 remains blocked", and "S4 stays IN
PROGRESS", contradicting the round-3 CLOSED paragraph below them and
`DEFERRED_VALIDATION_REGISTER.md`. Both are genuine dated log entries, so they
are labelled historical and marked superseded rather than deleted, and an
explicit final disposition is stated at the end.

### 3.7 `PR23-F7` (D4) — bare Markdown fence in the DV-036 correction audit

*CodeRabbit #1.* `Documentation_Standards.md` requires a language tag on every
fenced block. Confirmed one bare opening fence at line 195; `text` added. The
other bare fences in that file (51, 60, 79, 198, 219) are closing fences —
verified individually, no change needed.

### 3.8 `PR23-F8` (D2) — the "no CI gate" claim was too absolute

*Raised only by Cline. Missed by Copilot, CodeRabbit, and the other three LLM
reviews, each of which endorsed the claim as written.*

The E5 report §7.2, the `parity_report.rst` erratum, and several register and
index sites all stated, in the present tense, that **no** CI gate integrates
PRIN's dynamics over the golden corpus and compares the trajectory against the
stored reference. That is not true as stated. Re-derived here from the
repository, not from the review:

1. `tests/test_exp001_driver.py::TestCorpusParity::test_representative_cases_within_tolerance`
   calls `driver.compare_corpus_case` → `run_prin_case`, which drives the
   actual `prin` Rust core, against the stored corpus arrays.
2. It covers the 4 ids in that module's `_REPRESENTATIVE_CASES`.
3. The module carries `pytestmark = [pytest.mark.parity]`. `python.yml`'s
   `test` job runs `pytest tests/ -v -m "not slow and not gpu"`, which does
   **not** deselect `parity`. Confirmed locally:
   `pytest tests/test_exp001_driver.py -m "not slow and not gpu" -k "TestCorpusParity or TestRepeatability"`
   → `10 passed, 202 deselected`.
4. `git cat-file -e b434554:tests/test_exp001_driver.py` succeeds: the test is
   on `main` at this PR's base, merged via PR #20. It was added by EXP-001's
   own E1 (`37e218b`), so it postdates the Parity Report claim the erratum
   corrects — the erratum's historical judgement is unaffected.

**The correction strengthens the finding.** Re-derived from
`corpus_corpus-cpu.json`: of 504 cases, 19 breach, and **none of the 4
representative cases is among them** — all 4 pass. The one PRIN-vs-corpus gate
that exists is green while H1 is `REFUTED`. That is the coverage gap
`EXP001-E5-F1` names, demonstrated a second way: a 4-case subset cannot detect
this divergence class.

**Severity D2, not D1.** No verdict, tolerance, denominator, or measured value
changes; `EXP001-E5-F1` stands. What changes is the precision of a published
claim — a standard violation (Documentation Standards: claims must be
evidence-backed and exact), corrected everywhere it appears.

**Fix.** Corrected to *no CI gate covers the **full** 504-case corpus*, with
the 4-case gate named and its non-breaching status stated, at all sites:
E5 report (erratum **E-2**, §7.2, inheriting to §7.5 item 3),
`DOCS/sphinx/parity_report.rst`, `CHANGELOG.md`,
`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `DOCS/experiments/README.md`,
the EXP-001 `README.md` header, `DOCS/sessions/SESSION_REGISTER.md`,
`DOCS/sessions/phase-7/README.md`, `DOCS/sessions/contingencies/README.md`,
and the S1 correction brief — whose scope item is also sharpened to require a
**full-corpus** gate, naming the existing 4-case gate as the insufficient
subset rather than a substitute.

`EVIDENCE/0158-exp001-e5-parity-gate-coverage.json` is **not** amended: it is
an immutable measured artefact stamped at `de904a4`, and its `question` and
`method` fields are already scoped precisely to
`test_corpus_exhaustive_differential_parity`. They were accurate as written.

### 3.9 Reviewer claims checked and found sound

Not every reviewer statement needed action, but each was verified rather than
assumed:

- Determinism of `exp001_e4_analysis.py` (no wall-clock read, `sort_keys=True`,
  fixed row order) — re-confirmed by the byte-identical regeneration in §3.1.
- `.gitattributes` `benchmarks/results/** -text` — `git check-attr` reports
  `text: unset`, `whitespace: -trailing-space`; necessary, and `-text` rather
  than `binary` correctly preserves diff visibility.
- Sourcery's decline is correct behaviour for a 205k-line artefact-heavy diff,
  not a failure.
- Devin's observation that `run_analysis` calls `verify_manifest` twice per leg
  is factually correct and harmless (read-only, idempotent).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Remedy |
|---|---|---|---|---|---|
| `PR23-F1` | **D2** | `tools/reproduce.py` (`verify_manifest`, `append_manifest`) | Manifest verification followed symbolic links: content integrity checked, path provenance not (CWE-59) | Coding Standards §6; the function's own documented fail-closed contract | No-follow `_reject_symlink` guards + 5 regression tests |
| `PR23-F8` | **D2** | E5 report §7.2 + 9 further sites | "No CI gate integrates PRIN's dynamics over the golden corpus" is false as stated; a 4-case PRIN-vs-corpus gate runs in every required `test` leg | Documentation Standards — exact, evidence-backed claims | Erratum E-2 + corrected wording at all 10 sites |
| `PR23-F2` | D3 | `CHANGELOG.md` §Added | "awaits maintainer verification … 0154–0158 local-only" — contradicted at publication, and the range was wrong at drafting | Documentation Standards; campaign plan §12 item 3 | Rewritten to the accepted state + §14.1 pointer |
| `PR23-F4` | D3 | E5 report §6 PD-5 / §13 / §14.1 | §13 claimed PD-5 discharged "in §14" while §14.1 was a placeholder and PD-5 said the PR did not exist | Campaign plan §12 item 3 | §14.1 filled from the actual run; erratum E-1 on PD-5 |
| `PR23-F5` | D3 | `SESSION_REGISTER.md` L338 | "(local); sessions 0154–0158 not yet pushed" stale at the pushed head | Development Workflow §5 (stale governance metadata) | Prepared edit committed |
| `PR23-F3` | D4 | EXP-001 `README.md` 0158 row | "awaiting maintainer verification" contradicts the header above it | Documentation Standards | Row updated |
| `PR23-F6` | D4 | DV-036 S4 correction record | Superseded present-tense "pending"/"blocked"/"IN PROGRESS" under a `COMPLETE` header | Development Workflow §5 | Labelled historical + final disposition stated |
| `PR23-F7` | D4 | DV-036 correction audit L195 | Fenced block without a language tag | Documentation Standards | `text` tag added |

Declined, with rationale in §6: `PR23-F9` (CodeRabbit docstring-coverage
pre-merge check), `PR23-F10` and `PR23-F11` (style nits against the frozen E4
analysis module).

## 5. Deviation-ledger delta

No new ledger rows. The deviation ledger lives in the numbered Project State
Reports (`DOCS/reports/NNN-project-state.md`), and this round is not a Session
Cycle — the same disposition `PR017-devin-review` took. The next PSR to issue
is the EXP-001 correction cycle's S4 (campaign plan §10.4 item 3), which
inherits this report as prior art.

Carried findings re-inspected: `EXP001-E5-F1` — **unchanged and strengthened**
by `PR23-F8` (§3.8). `DV-040` (analysis code under `DOCS/` outside the CI lint
path) — unchanged, re-audit gate remains EXP-002 E4 (session 0162); it is the
correct home for `PR23-F9`'s underlying concern.

## 6. Findings declined, with rationale

**`PR23-F9` — CodeRabbit pre-merge check: docstring coverage 50.72 % < 80 %.**
Factually accurate and not a false positive, but measured against a threshold
this project does not use, and declining it is not a lowering of standards:

- `interrogate` is configured `fail-under = 95` and CI runs it on
  `python/prin` only.
- `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` sets
  `"tests/**" = ["S", "D"]` — pydocstyle is deliberately off for tests.
- Measured across this repository's test files: `test_wp001_baseline.py` 2 %,
  `test_reproduce.py` 11 %, `test_exp001_driver.py` 45 %,
  `test_exp001_e4_analysis.py` 33 %. The file CodeRabbit flags is **above** the
  repository's own test-file norm; raising only this one file would create
  local inconsistency, not consistency.
- The analysis module itself is 100 % docstringed.

Every reviewer who assessed this check independently reached the same
conclusion. The real, already-tracked gap is `DV-040`. New *production* code
added by this round (the `tools/reproduce.py` helper) is fully docstringed;
new *test* code follows the repository's existing `tests/**` norm of
self-descriptive names over per-method docstrings — 1 of the 5 new
`TestManifestSymlinkProvenance` tests carries one, matching that norm rather
than contradicting it. (Corrected 2026-09-23 — CodeRabbit follow-up review,
PR #23 head `d9d4f2a`: this paragraph and the A7 row above previously claimed
all five new tests carried docstrings.)

**`PR23-F10` — defensive `value <= 0.0` guard in
`exp001_e4_analysis::_decade_histogram`.** Raised as an explicit non-defect by
Qwen ("not worth changing"), Kimi, and the two long-form reviews; the existing
`value == 0.0` guard is correct for the non-negative error magnitudes the
function receives. **`PR23-F11` — `run_analysis` calls `verify_manifest` twice
per leg** (Devin): correct, and harmless — the call is read-only and
idempotent. Both are declined on the same governing ground: that module is the
committed analysis code of a **completed, maintainer-accepted E5 report**, and
`report-manifest.json` digests the outputs it produces. Editing it after its
report is issued would itself be a protocol deviation (campaign plan §12 items
1 and 6), for no defect. Recorded here so the decision is on file rather than
silently dropped; if `EXP-001-r1` rewrites the analysis, both are free
improvements to make there.

## 7. Verdict and required actions

**`PASS-WITH-FINDINGS` → all eight actionable findings FIXED in this round; no
D1; no verdict, tolerance, or measured value changed.**

| ID | Resolution | Evidence |
|---|---|---|
| `PR23-F1` | **FIXED** | `_reject_symlink` in `tools/reproduce.py`; 5 tests, 4 fail pre-fix (§3.1); E4 regeneration byte-identical |
| `PR23-F2` | **FIXED** | `CHANGELOG.md` §Added rewritten to the accepted state |
| `PR23-F3` | **FIXED** | EXP-001 `README.md` 0158 row |
| `PR23-F4` | **FIXED** | Report §14.1 filled (24/24 required checks green at `60cc387`); erratum E-1 |
| `PR23-F5` | **FIXED** | `SESSION_REGISTER.md` L338 committed |
| `PR23-F6` | **FIXED** | DV-036 S4 record: round-1/round-2 labelled historical; final disposition stated |
| `PR23-F7` | **FIXED** | `text` language tag at L195 |
| `PR23-F8` | **FIXED** | Erratum E-2 + corrected wording at all 10 sites; S1 brief scope sharpened |
| `PR23-F9` / `PR23-F10` / `PR23-F11` | **DECLINED with rationale** | §6 |

**Required actions carried forward (not this round's work):**

1. The EXP-001 correction cycle S1 must add a **full-corpus** PRIN-vs-corpus
   differential gate. `PR23-F8` sharpens that scope item: the existing 4-case
   gate is the insufficient subset, not a substitute.
2. `DV-040` remains open with its re-audit gate at EXP-002 E4 (session 0162).
3. Merging PR #23 still does **not** release session 0159. Campaign plan §3.3 /
   §10.4 keep 0159–0193 and 0194 BLOCKED until the correction cycle closes and
   `EXP-001-r1` returns a non-reversal verdict.

**Full-gate result on the remediation tree** (recorded verbatim; every line is
an actual run):

```text
pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp
    3214 passed, 176 skipped, 48 deselected in 414.81s
ruff check python/ tests/ benchmarks/ tools/ parity/         All checks passed!
ruff format --check python/ tests/ benchmarks/ tools/ parity/  311 files already formatted
mypy python/prin --strict                                    no issues in 62 source files
interrogate -c pyproject.toml python/prin                    PASSED 97.6% (min 95.0%)
sphinx-build -b html -W --keep-going DOCS/sphinx             build succeeded
tools/check_deviation_ledger.py 037 038                      passed (128 / 128 rows)
tools/check_dv_register_gates.py                             passed (40 DV / 198 sessions)
tools/check_skipif_probes.py                                 passed
tools/check_global_session_registration.py                   passed (17 reports)
tools/wp001_baseline.py check                                passed
```

One caveat recorded rather than hidden: `mypy --strict` on
`tests/test_reproduce.py` reports one pre-existing error
(`Module "tools.reproduce" does not explicitly export attribute
"ReportingError"`, line 55). It reproduces identically against
`git show HEAD:tests/test_reproduce.py`, is not introduced by this round, and
is out of CI scope — `python.yml` runs `mypy python/prin --strict` only. It is
left alone rather than fixed opportunistically outside the finding set.

**Delta re-audit date:** 2026-09-23 UTC — **Result:** CLEAN (§7 table; local
gate output above and in §3.1). CI on the remediation head is the authoritative
confirmation and is not pre-claimed here.

---

## 8. Round 2 — Copilot follow-up review (head `0cb6156`)

**Trigger:** after Round 1's remediation push (`0cb6156`), Copilot re-reviewed
the PR against its own prior findings and raised three new ones plus one
carried item, all against `tools/reproduce.py` and
`DOCS/experiments/EXP-001-.../analysis/exp001_e4_analysis.py` — the exact
files `PR23-F1` had just modified. The task here is the same as Round 1: fetch
each finding, re-derive it from the current repository state rather than the
reviewer's wording, fix what is real, and record what is declined.

```bash
gh api repos/Symbo-gif/PRIN/pulls/23/comments --paginate \
  | jq -r '.[] | select(.commit_id=="0cb61564c34c731980331717bfcb916afaf2344e") | .id'
```

| Reviewer | Findings raised at `0cb6156` |
|---|---|
| `Copilot` | 4 (3 new High; 1 carried — "Manifest verification accepts symlinked files", the original `PR23-F1` finding, re-flagged open pending the two new ones below) |

### 8.1 `PR23-F12` (D2) — the inventory scan still followed symlinks for unmanifested entries

*Copilot, "Reject non-file symlinks in manifest inventory" (`tools/reproduce.py:324`).*

`PR23-F1` added `_reject_symlink` to the manifest path and to every
**manifested** artefact, but `verify_manifest`'s inventory scan still built
`actual` with `path.is_file()` over the raw glob — which follows links. A
symlink named `rogue.json` pointing at a directory (or a broken target) is not
a file post-resolution, so it silently dropped out of `actual` instead of
tripping "unmanifested artefacts": the fail-closed guarantee held for content
and for *manifested* paths, but not for an untracked link sitting in the
governed directory. `append_manifest` did not have this gap — its own
candidate loop already ran `_reject_symlink` over every glob match before
filtering by `is_file()` (§3.1); this is the one call site Round 1 missed.

**Fix.** `verify_manifest` now runs `_reject_symlink` over every `*.json`
glob candidate (mirroring `append_manifest`'s existing pattern) before
computing `actual`, so a stray symlink is rejected outright rather than
vanishing from the inventory.

**Regression test.**
`tests/test_reproduce.py::TestManifestSymlinkProvenance::test_verify_manifest_rejects_an_unmanifested_symlink`
— a symlink to a directory, present but not manifested, now raises
`ManifestMismatchError` instead of verifying clean.

### 8.2 `PR23-F13` (D2) — the symlink check was a check-then-open race (TOCTOU)

*Copilot, "Make manifest reads race-safe against symlink replacement"
(`tools/reproduce.py:140`).*

`_reject_symlink`'s `path.is_symlink()` probe and the later `stat()`/`open()`
calls it guards are separate operations: a concurrent writer could replace a
regular file with a symlink between the two (CWE-59's TOCTOU variant), and
the verifier would then read and hash a target outside the governed
directory despite the documented no-follow guarantee.

**Fix.** `_open_no_follow(path, role)` in `tools/reproduce.py` opens the file
via `os.open(path, os.O_RDONLY | os.O_NOFOLLOW)` on POSIX, where the `open()`
syscall itself fails with `ELOOP` if the final path component is a symlink —
there is no separate moment at which the check has passed but the open has
not. `_read_no_follow` and `_stat_size_and_hash_no_follow` build on it so a
manifest's bytes, and an artefact's size and digest, each come from exactly
one opened file descriptor rather than from independent path-based calls
(`load_manifest`, `verify_manifest`'s per-record loop, and
`append_manifest`'s existing-record and newly-discovered-artefact loops all
now route through these). Windows does not define `O_NOFOLLOW`; there the
helper falls back to the `is_symlink()` pre-check, narrower than the POSIX
path but not a regression from Round 1 — documented honestly in the
function's docstring rather than claimed as closed. The pre-existing
`_reject_symlink` calls are kept as fast top-of-function rejections; the
atomicity guarantee comes from the no-follow open, not from them.

**Regression tests.** `tests/test_reproduce.py::TestOpenNoFollow` — a regular
file opens and reads correctly; `_stat_size_and_hash_no_follow` agrees with
`compute_sha256`; a symlink is rejected at `_open_no_follow` itself. A true
concurrent-swap race is not simulated (inherently flaky under a timing
harness); the fix is instead verified structurally, by confirming every I/O
call the finding named now goes through a single no-follow open rather than a
separate check.

### 8.3 `PR23-F14` (D2) — the CLI could redirect writes into the frozen record

*Copilot, "Restrict CLI outputs from overwriting immutable records"
(`exp001_e4_analysis.py`, `_checked_destination`/`main`).*

`allowed_output_roots()` includes the experiment's record root — necessary,
because the default `report-manifest.json` destination lives there — but
`_checked_destination` accepted **any** path under any permitted root. A
caller could therefore run `--manifest-path
.../report.md` and have `write_report_manifest` overwrite the frozen E5
report, `preregistration.md`, or the analysis module's own source; or run
`--output-dir .../EXP-001-golden-trajectory-numerical-parity` and have
`write_outputs` write `exp001-e4-summary.md` into the record root itself.

**Fix.** Two changes in `exp001_e4_analysis.py`:

1. `allowed_generated_output_dirs()` — a new, narrower root set for
   `--output-dir` that excludes the record root entirely (only the
   gitignored `OUTPUT_ROOT` and the system temp directory). `--output-dir`
   can no longer target the record root under any name.
2. `_checked_manifest_destination()` — wraps `_checked_destination` for
   `--manifest-path` and additionally requires that a destination landing
   inside the record root be named exactly `report-manifest.json`, the one
   file this analysis is registered to add there. A destination under
   `OUTPUT_ROOT` or the temp directory (this module's own tests) is
   unrestricted, since neither holds anything immutable.

`allowed_output_roots()` itself is unchanged (still used for the manifest
check's permitted-roots argument and by `run_analysis`'s programmatic-caller
contract), so the default CLI invocation's behaviour — writing
`report-manifest.json` to the record root, and generated files to
`OUTPUT_ROOT` — is identical to before the fix.

**Regression tests.** `tests/test_exp001_e4_analysis.py::TestOutputContainment`
gained five: `allowed_generated_output_dirs` excludes the record root;
`--output-dir` pointed at the record root is refused; `--manifest-path`
pointed at the real `report.md` is refused and the file is verified
byte-unchanged after the attempt; `_checked_manifest_destination` accepts the
canonical name and rejects any other, unit-tested directly.

### 8.4 Carried finding — "Manifest verification accepts symlinked files"

Copilot's original `PR23-F1` discussion thread remained open through Round 2,
without a "New" tag, alongside the three new findings above. Re-derived: it
is the same underlying class as `PR23-F12`/`PR23-F13`, not a fourth distinct
defect — `PR23-F1`'s fix closed the manifested-path and destination cases;
the inventory-scan gap (`PR23-F12`) and the check-then-open race
(`PR23-F13`) were exactly what remained. No separate fix was needed beyond
§8.1–§8.2.

### 8.5 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  70 passed
.venv\Scripts\python -m pytest tests/test_exp001_driver.py tests/test_acceptance_y4q2.py -q
  252 passed, 27 skipped
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3223 passed, 176 skipped, 48 deselected
.venv\Scripts\python -m ruff check tools/reproduce.py exp001_e4_analysis.py tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same four files>
  4 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m bandit tools/reproduce.py exp001_e4_analysis.py
  No issues identified
.venv\Scripts\python tools/check_dv_register_gates.py            passed (40 DV / 198 sessions)
.venv\Scripts\python tools/check_skipif_probes.py                passed
.venv\Scripts\python tools/check_global_session_registration.py  passed (17 reports)
.venv\Scripts\python tools/wp001_baseline.py check                passed
```

**No regression to the published EXP-001 record.** The hardened analysis was
re-run end to end to a scratch destination and compared against the committed
`report-manifest.json`:

```text
H1: REFUTED   H2a: REFUTED   H2b: CONFIRMED   H3: CONFIRMED   H4: CONFIRMED
D1 flag: RAISED
exp001-e4-adjudication.json  12974 B  sha256 e6f6eb20...  MATCH
exp001-e4-summary.md          5783 B  sha256 4551061c...  MATCH
```

**Security gates (Coding Standards §6).** `tools/reproduce.py` and
`exp001_e4_analysis.py` are modified first-party Python, so Snyk Code
applies; no dependency manifest changed. Local runs (Snyk CLI `1.1306.2`, org
`symbo-gif`):

```text
snyk code test tools/reproduce.py            -> Total issues: 0
snyk code test exp001_e4_analysis.py         -> Total issues: 3 (all LOW, Path Traversal)
```

The three LOW findings on `exp001_e4_analysis.py` (lines 857, 874, 1006 —
`write_outputs`'s two fixed-filename joins under `output_dir`, and the
`Path(path).resolve()` inside `_checked_destination` itself, which is the
sanitizer) are **pre-existing**: confirmed by scanning `git show
0cb6156:.../exp001_e4_analysis.py` before this round's edits, which reports
the identical three findings at the pre-fix line numbers. They are not
attributable to this round's change and are not new. They are also a
structural false-positive class for this pattern — Snyk's static analysis
does not model `_checked_destination`'s resolve-then-contain check as
neutralizing the taint on the CLI-sourced path, and there is no way to
enforce path containment in Python without first resolving the path. Left
alone rather than fixed opportunistically outside this round's finding set,
consistent with the `mypy` caveat already on file in §7; flagged here rather
than silently passed over. **CI's `Snyk Code` required check on the
remediation head is the authoritative gate**, not this local run.

**Delta re-audit date:** 2026-09-23 UTC — **Result:** CLEAN. All three new
findings (`PR23-F12`, `PR23-F13`, `PR23-F14`) FIXED with regression tests; the
carried `PR23-F1` thread closes with them (§8.4); no D1; no verdict,
tolerance, or measured value changed; no regression to the published EXP-001
record (§8.5).

---

## 9. Round 3 — Copilot and CodeRabbit follow-up review (head `d9d4f2a`)

**Trigger:** Round 2's push (`d9d4f2a`) drew a fresh Copilot review (3 new
High findings) and a fresh CodeRabbit review (4 actionable comments, of which
2 were auto-resolved by Round 2's own fixes) on the same push. Both reviews
targeted the Round 2 fix itself — Copilot found the no-follow guarantee
didn't extend to the caller's *own* read of an already-verified artefact or
to `append_manifest`'s destination handling; CodeRabbit found the CLI
containment fix from `PR23-F14` had two remaining gaps (nested paths, and a
temp-directory allowance that could transitively admit the whole checkout)
and that the `PR23-F13` fix had silently dropped the size-before-hash
short-circuit an existing test was pinning.

### 9.1 `PR23-F15` (D2) — `_load_artefact` reopened its artefact through link-following calls

*Copilot, "Artifact reload bypasses no-follow verification"
(`exp001_e4_analysis.py:177`, plus flagged as the same class at the
function's other three write call sites, `write_outputs`/`write_report_manifest`).*

`_load_artefact` called `verify_manifest` (no-follow, since Round 1/2) and
then reopened the same artefact with `artefact.is_file()` /
`artefact.read_text()` — both link-following. A concurrent replacement
between the verification and this read could feed the analysis a different
file than the one just verified: the no-follow guarantee covered
verification but not the caller's own subsequent use of the result.

**Fix.** `tools/reproduce.py::_read_no_follow` is renamed to the public
`read_no_follow` (a caller outside the module now legitimately needs it) and
`_load_artefact` reads through it instead of `Path.read_text`. Applied the
same reasoning to the three sibling write sites Copilot's "also appears in"
list named (`write_outputs`'s two output files, `write_report_manifest`'s
manifest) — see `PR23-F16`'s `write_no_follow`, §9.2.

**Regression test.**
`tests/test_exp001_e4_analysis.py::TestProvenanceGuard::test_load_artefact_reads_via_no_follow_not_plain_path_io`
monkeypatches `Path.read_text` to raise `AssertionError` if called at all,
proving the read path no longer touches it.

### 9.2 `PR23-F16` (D2) — `append_manifest`'s destination I/O ran through a resolved, not the original, path

*Copilot, "Manifest append remains vulnerable to symlink TOCTOU"
(`tools/reproduce.py:347`).*

`destination = manifest_path.resolve()` was computed once and reused for
*both* the containment check and every subsequent read/write
(`load_manifest(destination)`, `destination.write_text(...)`). `.resolve()`
follows a symlink: if a concurrent writer swapped the final path component
between the initial `_reject_symlink` probe and this `.resolve()` call, every
downstream read/write would silently follow the swapped-in link, bypassing
the no-follow guarantee entirely for the append path.

**Fix.** `destination` (resolved) is now used **only** for the containment
check and the self-exclusion comparison; every read and the eventual write go
through `manifest_path` (the original, unresolved argument) via
`read_no_follow`/the new public `write_no_follow`. `write_no_follow` mirrors
`_open_no_follow` on the write side: `O_CREAT | O_TRUNC | O_NOFOLLOW` makes
the `open()` itself the check on POSIX, with the same documented Windows
fallback. Also applied to `write_outputs`'s two output files and
`write_report_manifest`'s manifest in `exp001_e4_analysis.py` (§9.1), closing
the same class there.

**Regression test.**
`tests/test_reproduce.py::TestManifestSymlinkProvenance::test_append_manifest_writes_through_the_unresolved_manifest_path`
patches `Path.resolve` so that resolving `manifest_path` specifically returns
a decoy path still inside the allowed roots (so containment still passes),
and confirms the manifest lands at the real `manifest_path`, never at the
decoy — proving the fix without needing a real race.
`tests/test_reproduce.py::TestWriteNoFollow` (3 tests) pins `write_no_follow`
directly: new-file write, truncate-on-existing, and symlink-destination
rejection.

### 9.3 `PR23-F17` (D3) — `append_manifest` silently dropped a non-symlink, non-regular candidate

*Copilot, "previously missed" Medium: "`append_manifest` ignores non-regular
rogue entries" (`tools/reproduce.py:355`).*

The inventory-scan fix from `PR23-F12` (Round 2) covered symlinks but not
other non-regular entries: a directory or FIFO named `rogue.json` is not a
symlink, so `_reject_symlink` alone would not catch it, and the `is_file()`
filter that followed would silently drop it from `actual_paths` — the same
"vanishes instead of surfacing as missing/unmanifested" failure mode as the
symlink case, for a different reason, and on the writer side this means
`append_manifest` could bless a manifest as if the directory were absent.

**Fix.** `_reject_non_regular(path, role)` — calls `_reject_symlink` first
(so the more specific message wins when both apply), then rejects any
existing, non-symlink entry that is not `is_file()`. Applied to the candidate
scan in both `verify_manifest` and `append_manifest`, replacing the narrower
`_reject_symlink` call there.

**Regression tests.**
`test_verify_manifest_rejects_a_directory_named_like_json` and
`test_append_manifest_rejects_a_directory_named_like_json` in
`tests/test_reproduce.py` — a plain directory named `rogue.json`, no symlink
involved, both fail closed with "not a regular file".

### 9.4 `PR23-F18` (D4) — the temp-directory allowance could transitively admit the whole checkout

*CodeRabbit, "Exclude the checkout from the temporary-directory allowance"
(Major; `exp001_e4_analysis.py:988` and the equivalent in
`tools/reproduce.py`'s `ALLOWED_MANIFEST_ROOTS`).*

`allowed_output_roots`/`allowed_generated_output_dirs`/`ALLOWED_MANIFEST_ROOTS`
all include the resolved system temp directory, to support a test's scratch
directory. The containment check (`root in destination.parents`) walks every
ancestor, so if the repository checkout itself were located under the system
temp directory (an ephemeral CI workspace, a sandboxed clone — not this
machine's layout, but not excluded by the code either), admitting the temp
root at all would transitively admit *every* path in the checkout, including
`report.md` and `CHANGELOG.md`, silently defeating the containment this
round's other fixes just added.

**Fix.** `_safe_temp_root(repository_root)` in `exp001_e4_analysis.py`, and
the equivalent inline `_TEMP_ROOT_IS_SAFE` computation in
`tools/reproduce.py`, omit the temp root from the permitted-roots tuple when
the checkout is under (or is) the resolved temp directory. Scratch-directory
support degrades only in that one deployment shape; the containment
guarantee for the checkout's own files never does, in any deployment shape.

**Regression tests.** `tests/test_exp001_e4_analysis.py::TestSafeTempRoot`
(3 tests, via monkeypatched `tempfile.gettempdir`) and
`tests/test_reproduce.py::test_allowed_manifest_roots_does_not_transitively_admit_the_checkout`
(an invariant check against the real, computed `ALLOWED_MANIFEST_ROOTS` for
this checkout).

### 9.5 `PR23-F19` (D2) — the manifest-destination guard missed nested paths under the record root

*CodeRabbit, "Restrict every manifest destination beneath the record root"
(Major; `exp001_e4_analysis.py:1045`).*

`_checked_manifest_destination`'s guard (`PR23-F14`, Round 2) compared
`resolved.parent == record_root` — a **direct child** of the record root
misnamed anything but `report-manifest.json` was rejected, but a **nested**
destination, such as `record_root/analysis/exp001_e4_analysis.py` (this
module's own source), was not: its parent is `record_root/analysis`, not
`record_root`, so the guard never fired and `write_report_manifest` would
have overwritten the analysis module itself.

**Fix.** The check now tests membership anywhere under the record root
(`resolved == record_root or record_root in resolved.parents`) against the
one canonical destination `record_root / "report-manifest.json"`, rather than
comparing only the direct parent and the basename.

**Regression tests.**
`test_checked_manifest_destination_rejects_nested_paths` (unit level) and
`test_the_cli_refuses_a_manifest_path_nested_in_the_record_root` (through the
CLI boundary) in `tests/test_exp001_e4_analysis.py`.

**Verification incident, disclosed.** Proving the CLI-level test failed
against the pre-fix code required exercising `analysis.main()` with the real
vulnerability live. The first version of this test pointed
`--manifest-path` at the **real, committed**
`exp001_e4_analysis.py`/`report.md` (via `_REPOSITORY_ROOT`) rather than a
sandbox; running it against pre-fix source (via `git stash` on the source
files only, to confirm the test actually pins the defect — the same
practice as `PR23-F1`'s regression proof in §3.1) exploited the real,
then-still-present bug against the checkout's own working tree and
overwrote `exp001_e4_analysis.py` with a `report-manifest.json`-shaped JSON
payload. Recovered immediately with `git checkout --` (no commit had been
made; nothing was lost) and rewritten: every test in this section, and the
pre-existing `PR23-F14` CLI tests it sits beside
(`test_the_cli_refuses_an_output_dir_inside_the_record_root`,
`test_the_cli_refuses_a_manifest_path_misnamed_in_the_record_root`), now
monkeypatch `analysis._REPOSITORY_ROOT` to a `tmp_path` sandbox and write a
synthetic decoy file there, so a future regression in this guard fails the
test instead of writing into the real checkout. Lesson: a test whose entire
premise is "this write must not happen" must never point at anything real,
precisely because the failure mode under test *is* an unwanted write.

### 9.6 `PR23-F20` (D3) — the short-circuit CodeRabbit independently caught was already being fixed

*CodeRabbit, "Check the recorded size before hashing existing artefacts"
(`tools/reproduce.py:239`).*

Round 2's `_stat_size_and_hash_no_follow` (introduced for `PR23-F13`)
combined the size check and the hash into one no-follow open, but
unconditionally hashed before the caller compared sizes — silently dropping
the base revision's short-circuit (skip hashing once the size alone proves a
mismatch) and, as a side effect, making the existing
`test_verify_manifest_detects_size_mismatch_before_hashing` pass vacuously,
since it patched the now-bypassed public `compute_sha256` rather than
whatever actually hashes post-refactor.

This was caught independently during this round's own re-verification
(before CodeRabbit's comment was read) and fixed with a different but
equivalent design to CodeRabbit's suggested diff: rather than an optional
`expected_size` parameter on `_stat_size_and_hash_no_follow`, a new
`_verify_size_and_hash_no_follow(path, expected_size, name, role)` performs
the short-circuit (fstat, compare, close-and-raise on mismatch, else hash via
the extracted `_hash_fd` helper) and is used at both call sites that have an
expected size to compare against; `_stat_size_and_hash_no_follow` remains for
the one call site (newly appended records) with no expected size. The
existing test's monkeypatch target was corrected to `reproduce._hash_fd`
(the function that now actually hashes) so it once again fails if hashing
runs on a size mismatch — confirmed by reverting the fix and re-running it.

### 9.7 `PR23-F21` (D4) — a corrected sentence still read ambiguously

*CodeRabbit, "Specify what the parity job gates."
(`DOCS/sphinx/parity_report.rst:208`).*

The sentence "corpus parity is a merge gate" — written after `PR23-F8`'s
erratum already corrected the paragraph above it to say the job checks
PRINet self-consistency, not PRIN-vs-reference parity — could still be read
as claiming the broader, uncorrected thing. Reworded to name what is
actually gated (**PRINet corpus self-consistency**) and restate, in the same
sentence, that full-corpus **PRIN**-vs-reference trajectory parity is not.

### 9.8 `PR23-F22` (D4) — the audit's own docstring-coverage claim was inaccurate

*CodeRabbit, "Correct the A7 docstring evidence."
(`DOCS/audits/PR023-multi-review-audit.md:57`).*

§1's A7 row and §6 both claimed "all five new [`PR23-F1`] tests carry
docstrings." Re-checked directly against `tests/test_reproduce.py`: 4 of the
5 (`test_verify_manifest_rejects_a_symlinked_artefact`,
`test_verify_manifest_rejects_a_symlinked_manifest`,
`test_append_manifest_never_blesses_a_symlinked_artefact`,
`test_append_manifest_rejects_a_symlinked_destination`) have no method
docstring; only `test_regular_files_still_verify` does. The underlying
project standard was correctly characterized (`ruff D` is off for
`tests/**`, ergo not a real gap), but the factual claim about this specific
round's tests was wrong — a documentation-accuracy defect in the audit
itself, corrected in §1 and §6.

### 9.9 Carried finding, resolved with this round

Copilot's original `PR23-F1` thread ("Manifest verification accepts
symlinked files") remained open through Round 3 as well, without a "New"
tag, alongside the three new findings above — the same pattern as Round 2
(§8.4). `PR23-F15`/`PR23-F16`/`PR23-F17` are exactly the remaining gaps in
that class; no separate fix was needed.

CodeRabbit auto-resolved two of its four comments on this head
(`report.md`/`CHANGELOG.md`/`README.md`/`SESSION_REGISTER.md` status
reconciliation, and the DV-036 S4 stale-pending-status note) with "✅
Addressed in commits d15fe5c to d9d4f2a" — both are `PR23-F2`/`PR23-F3`/
`PR23-F5`/`PR23-F6` from Round 1 (§§3.2, 3.3, 3.5, 3.6), already fixed and
correctly recognized as such.

### 9.10 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  83 passed
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3236 passed, 176 skipped, 48 deselected
.venv\Scripts\python -m ruff check tools/reproduce.py exp001_e4_analysis.py tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same four files>
  4 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m bandit tools/reproduce.py exp001_e4_analysis.py
  No issues identified
```

**No regression to the published EXP-001 record**, re-verified after this
round's edits by regenerating to a scratch destination and comparing against
the committed `report-manifest.json`:

```text
H1: REFUTED   H2a: REFUTED   H2b: CONFIRMED   H3: CONFIRMED   H4: CONFIRMED
D1 flag: RAISED
exp001-e4-adjudication.json  sha256 e6f6eb20...  MATCH
exp001-e4-summary.md          sha256 4551061c...  MATCH
```

**Security gates.** Both files are modified first-party Python; no dependency
manifest changed. Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):

```text
snyk code test tools/reproduce.py       -> Total issues: 0
snyk code test exp001_e4_analysis.py    -> Total issues: 1 (LOW, Path Traversal)
```

The one remaining LOW finding is at `_checked_destination`'s own
`Path(path).resolve()` — the sanitizer's entry point — the same structural
false-positive class documented in §8.5 (Snyk does not model a
resolve-then-contain check as neutralizing the taint on the path that flows
into it); down from three such findings before this round because the
`write_no_follow` migration (§9.1–§9.2) removed the two `write_text` sinks
Snyk had flagged separately. **CI's `Snyk Code` required check on the
remediation head remains the authoritative gate.**

**Delta re-audit date:** 2026-09-23 UTC — **Result:** CLEAN. `PR23-F15`
through `PR23-F22` FIXED with regression tests (`PR23-F20` fixed
independently, before CodeRabbit's comment was read, with an equivalent
design); the carried `PR23-F1` thread closes with them (§9.9); no D1; no
verdict, tolerance, or measured value changed; no regression to the published
EXP-001 record (§9.10). One local process incident during verification,
disclosed and remediated in §9.5, with the test suite itself hardened against
recurrence.

---

## 10. Round 4 — Copilot follow-up review (head `900a68f`) plus a maintainer-flagged mypy gap

**Trigger:** CI on Round 3's push (`900a68f`) went fully green (29/29
required + optional checks; `gpu-cuda`/`gpu-wgpu` completed after the initial
check-list snapshot). Copilot re-reviewed the same head and raised 2 new
findings (1 High, 1 Medium) while resolving 2 more from Round 3; the carried
`PR23-F1` thread ("Manifest verification accepts symlinked files") remains
open, the same pattern as Rounds 2 and 3. CodeRabbit's automatic review on
this head is rate-limited on this org's plan (`Review skipped: manual review
required for this OSS repository`; a manual `@coderabbitai review` trigger
returned "Review rate limited" — 1 included review/hour, already spent by
Rounds 1–3) and did not produce new comments this round. Separately, the
maintainer flagged a standing item from §7's caveat: `mypy --strict` on
`tests/test_reproduce.py` reporting `Module "tools.reproduce" does not
explicitly export attribute "ReportingError"`, previously left alone as
pre-existing and out of CI's `mypy python/prin --strict` scope, but now
explicitly requested to be fixed.

### 10.1 `PR23-F23` (D2) — `adjudicate_h2a`'s confirmatory gate trusted a field of the artefact it was gating

*Copilot, "Enforce the registered fuzz-case minimum"
(`exp001_e4_analysis.py:401`).*

`adjudicate_h2a` read `fuzz_batch_confirmatory_minimum` from the artefact
payload itself and compared the payload's own `n_fuzz_cases_requested`
against it (`denominator < minimum`). Both fields live in the same
manifest-verified-but-otherwise-untrusted payload: manifest verification
attests the bytes are unmodified since the driver wrote them, not that the
driver was run honestly or that a hand-constructed payload couldn't declare
`fuzz_batch_confirmatory_minimum: 1` alongside `n_fuzz_cases_requested: 1`.
`1 < 1` is false, so the check could never reject that pair — a
self-referential comparison, not a gate against the registered rule
(`REGISTERED_FUZZ_BATCH_MIN = 1000` in
`benchmarks/campaign/exp001_driver.py`, pre-registration §7). One clean case
would then adjudicate H2a `CONFIRMED`.

**Severity D2, not D1.** Exploiting it requires supplying a hand-built or
corrupted artefact that still passes `verify_manifest`'s own SHA-256 check
against *some* manifest — i.e., an attacker or error already inside the
governed provenance chain; every artefact this repository has actually
generated carries the driver's true value (1000), so no published verdict is
affected. It breaks the normative "confirmatory means confirmatory" contract
pre-registration §7 states, independent of exploitability.

**Fix.** `adjudicate_h2a` now imports `REGISTERED_FUZZ_BATCH_MIN` from the
driver and (a) requires the payload's own recorded minimum to equal it
exactly — failing closed on a payload that disagrees with the registered
rule, rather than silently adopting whatever rule it claims — and (b) gates
`denominator` against the constant, never against the payload-supplied
`minimum`.

**Regression test.**
`tests/test_exp001_e4_analysis.py::TestH2a::test_a_self_declared_minimum_cannot_override_the_registered_one`
constructs exactly the `minimum=1, requested=1` payload described above and
confirms it now fails closed with "registered minimum" in the message;
`test_the_registered_minimum_constant_is_1000` pins the constant's value
directly. Proved against Round 3 source (`git stash` on the two source
files only): `DID NOT RAISE AnalysisError` pre-fix, passes post-fix.

### 10.2 `PR23-F24` (D3) — the committed report-manifest's output-integrity fields could still follow a link

*Copilot, "Compute output integrity from no-follow descriptors"
(`exp001_e4_analysis.py:948`).*

`Round 3`'s `write_no_follow` migration (§9.1–§9.2) closed the *write* side
for generated outputs, but `write_report_manifest`'s `"outputs"` list —
recording each output's committed size and digest — still computed them with
plain `path.stat().st_size` and `compute_sha256(path)`, both link-following.
If an output were swapped for a symlink (or otherwise changed) between
`write_outputs` finishing and this manifest write running, the committed
`report-manifest.json` could attest bytes from a different file than the one
`write_no_follow` actually wrote — the no-follow guarantee covered the write
but not the subsequent read-back used to record its own integrity.

**Fix.** `tools.reproduce._stat_size_and_hash_no_follow` is renamed to the
public `stat_size_and_hash_no_follow` (the second cross-module consumer of
this pattern, after `read_no_follow`/`write_no_follow` in Round 3) and used
for every entry in the `"outputs"` list, in place of the
`stat()`/`compute_sha256()` pair. `compute_sha256` is no longer imported by
`exp001_e4_analysis.py` at all.

**Regression test.**
`tests/test_exp001_e4_analysis.py::TestReportManifestIntegrity::test_output_integrity_does_not_use_link_following_calls`
monkeypatches `Path.stat` and `tools.reproduce.compute_sha256` to raise if
called, and confirms `write_report_manifest` still produces the correct
size/digest — proving the read path no longer touches either. Proved against
Round 3 source: fails with the monkeypatch's `AssertionError` pre-fix,
passes post-fix.

### 10.3 `PR23-F25` (D3) — the manifest path itself was checked for symlinks only, not full non-regularity

*Copilot, "Reject non-regular manifests before loading"
(`tools/reproduce.py:489`, "also appears on line 582").*

`PR23-F17` (Round 3, §9.3) added `_reject_non_regular` for *candidate*
artefacts in both `verify_manifest` and `append_manifest`, but the manifest
path itself — checked at the top of each function, before any candidate
scan — still used the narrower `_reject_symlink`. For `verify_manifest`,
where the manifest and results directory coincide, the two checks can look
equivalent in the common case, but they are not the same check, and for
`append_manifest`'s realistic shape (`DEFAULT_MANIFEST` in `paper/`,
`DEFAULT_RESULTS_DIR` in a different tree entirely — the manifest is *not* a
candidate in its own results directory) only the top-level check reaches it
at all. A FIFO there would block inside `load_manifest`'s blocking open; a
directory would reach `write_no_follow` in `append_manifest` and fail as a
raw, undocumented `OSError`/`PermissionError` rather than the fail-closed
`ManifestMismatchError` both functions document.

**Fix.** Both top-level calls — `verify_manifest`'s and `append_manifest`'s —
changed from `_reject_symlink(manifest_path, "manifest")` to
`_reject_non_regular(manifest_path, "manifest")`.

**Regression tests, and a false-negative caught during their own
verification.** The first version of the `append_manifest` test placed the
directory-as-manifest *inside* `results_dir`, which is unintentionally also
caught by the existing `PR23-F17` candidate-scan check — the test passed
against pre-fix source for the wrong reason (a false negative in the
regression proof itself, not in the fix), discovered by running it against
`git stash`'d Round 3 source as this audit's own methodology requires (§2,
§3.1) and noticing it passed when it should have failed. Corrected to place
the manifest destination in a sibling directory, the realistic shape
(`test_append_manifest_rejects_a_manifest_path_that_is_a_directory`), which
then correctly failed with the undocumented `PermissionError` pre-fix and
passes with `ManifestMismatchError` post-fix, exactly matching Copilot's
description.
`test_verify_manifest_rejects_a_manifest_path_that_is_a_directory` covers
the `verify_manifest` side.

### 10.4 Carried finding, still resolving

Copilot's original `PR23-F1` thread remained open through Round 4 as well.
`PR23-F25` is the last piece of that class this round found; whether the
thread closes on Round 4's push is for the next review to show.

### 10.5 Maintainer-requested fix — `tests/test_reproduce.py`'s pre-existing mypy gap

Not a review finding; the maintainer asked directly for the caveat recorded
in §7 to be closed rather than left standing: `mypy --strict
tests/test_reproduce.py` reported `Module "tools.reproduce" does not
explicitly export attribute "ReportingError"` (line 55,
`from tools.reproduce import ReportingError`), reproducing identically
against every head since Round 1. Root cause: `tools/reproduce.py` imports
`ReportingError` from `prin.reporting` (line 27) without `__all__` or an
explicit re-export alias, so mypy's `--strict`-implied
`--no-implicit-reexport` treats it as a private import, not part of
`tools.reproduce`'s public surface — even though
`tests/test_reproduce.py::test_reproduce_imports_only_public_reporting_surface`
already asserts `reproduce.ReportingError is prin.reporting.ReportingError`
as an intentional public re-export (a WP035-F1 decision, per that test's own
docstring).

**Fix.** `from prin.reporting import ReportingError` →
`from prin.reporting import ReportingError as ReportingError` — the PEP 484
explicit-reexport idiom for a single name, matching how
`prin/reporting/__init__.py` itself re-exports `ReportingError` from
`_artifacts` (via `__all__`, appropriate there since that module has a large
public surface; the single-name `as` alias is the equivalent, minimal form
for `tools/reproduce.py`, which otherwise has no imported names needing
re-export — every other public name in the module is defined there
directly, which `--no-implicit-reexport` does not restrict).

**Verification.** `mypy --strict tests/test_reproduce.py` now reports no
issues; re-run across every file this round and Round 3 touched
(`tools/reproduce.py`, `exp001_e4_analysis.py`,
`tests/test_exp001_e4_analysis.py`) together, and separately against the
CI-gated `mypy python/prin --strict` scope, both clean.

Fixing this also surfaced two *new* mypy `--strict` errors in
`tests/test_reproduce.py` from this session's own Round 3 test additions,
caught and fixed in the same pass rather than left for a future round:
`test_append_manifest_writes_through_the_unresolved_manifest_path`'s
`fake_resolve(self, *args: object, **kwargs: object)` monkeypatch didn't
type-check against `Path.resolve`'s real `(self, strict: bool = False)`
signature when forwarding `*args`/`**kwargs` to it; narrowed to match the
real signature exactly (`strict: bool = False`, forwarded positionally).

### 10.6 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  88 passed
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3240 passed, 176 skipped, 48 deselected, 1 failed then verified flaky (§10.6 note)
.venv\Scripts\python -m ruff check tools/reproduce.py exp001_e4_analysis.py tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same four files>
  4 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  Success: no issues found in 4 source files
.venv\Scripts\python -m mypy python/prin --strict
  Success: no issues found in 62 source files
.venv\Scripts\python -m bandit tools/reproduce.py exp001_e4_analysis.py
  No issues identified
tools/check_dv_register_gates.py / check_skipif_probes.py /
  check_global_session_registration.py / wp001_baseline.py check
  all passed
```

**Flaky-test note.** The one failure in the full-suite run,
`tests/test_acceptance_y4q1_2.py::TestMeasureWallTimeExtended::test_larger_batch_takes_longer`,
is a wall-clock timing assertion (`t16["mean_ms"] >= t1["mean_ms"] * 0.5`) in
a module untouched by any round of this PR; it passed cleanly in isolation
immediately after. Not attributable to this change.

**No regression to the published EXP-001 record**, re-verified after this
round's edits:

```text
H1: REFUTED   H2a: REFUTED   H2b: CONFIRMED   H3: CONFIRMED   H4: CONFIRMED
D1 flag: RAISED
exp001-e4-adjudication.json  sha256 e6f6eb20...  MATCH
exp001-e4-summary.md          sha256 4551061c...  MATCH
```

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 0 issues; `exp001_e4_analysis.py` 1 issue (LOW, Path
Traversal — unchanged from §9.10's finding, the sanitizer's own entry point,
same structural false-positive class). No new findings this round.

**Delta re-audit date:** 2026-09-23 UTC — **Result:** CLEAN. `PR23-F23`
through `PR23-F25` FIXED with regression tests; the maintainer-requested
`ReportingError` re-export gap closed, along with two `mypy --strict`
errors this session's own Round 3 tests had introduced; no D1; no verdict,
tolerance, or measured value changed; no regression to the published EXP-001
record. CodeRabbit did not review this head (rate-limited); its next
automatic review, whenever the plan's window resets, is the outstanding item
this round could not close.

---

## 11. Round 5 — three independent LLM reviews at head `754272a`

**Trigger:** Round 4's push (`900a68f` → `754272a` after Round 4's own
mypy-gap fix) was reviewed by three independent, non-bot LLM reviewers
posted as PR comments rather than GitHub "reviews" (GitHub does not allow
`REQUEST_CHANGES` from the PR author's own account, which posted all three
on the maintainer's behalf, the same posting pattern as Qwen/Devin/Kimi/Cline
in Round 1):

| Reviewer | New findings | Validated prior findings |
|---|---|---|
| CLINE-A.I. (Stealth/Space-Bunny-Alpha, Xhigh-reasoning) | 4 (1 High CI blocker, 1 High, 1 Medium, 1 Low) | Yes, all Round 4 items |
| SWE-2 High-reasoning (Devin IDE) | 0 new; pinned the CI blocker's exact mechanism | Yes, all Round 4 items, plus an independent Wolfram-Language recomputation of H2b's statistics |
| PERPLEXITY-AI (KIMI-K3-Thinking, US-hosted) | 0 new; concurred on severity and disposition | Yes, all Round 4 items |

CodeRabbit's own automatic re-review of `754272a` (triggered manually three
times as its 1-review/hour rate limit reset) produced no new line-level
comments but, via its `@coderabbitai` chat interface, independently
confirmed the three required Windows checks were red at the reported run and
confirmed the code paths behind three of the four findings below. All three
LLM reviewers agree: **the EXP-001 numerical/parity conclusions are not in
question** — every finding concerns the merge gate and the provenance
guarantees the hardened verifier documentation claims, not H1–H4 or the D1
flag.

### 11.1 `PR23-F26` (D2) — a test's global `Path.stat` patch turned an ordinary assertion into a Windows `INTERNALERROR`

*CLINE-A.I. and SWE-2/Devin, independently, on
`tests/test_exp001_e4_analysis.py::TestReportManifestIntegrity::test_output_integrity_does_not_use_link_following_calls`.*

The `PR23-F24` regression test (Round 4, §10.2) proved its contract by
`monkeypatch.setattr(Path, "stat", _forbidden_stat)` — patching the whole
`pathlib.Path` class, not a call the test itself makes. On Windows Python
3.11–3.13, `Path.lstat()` is implemented as `self.stat(follow_symlinks=False)`,
and `tools.reproduce._open_no_follow`'s Windows fallback (no `O_NOFOLLOW` on
that platform) calls `path.is_symlink()` → `lstat()` → the patched `stat` —
its own legitimate no-follow pre-open check, not the naive
`stat()`/`compute_sha256()` pattern the test intended to forbid. That raised
the test's `AssertionError` from inside `write_report_manifest`'s own call to
`stat_size_and_hash_no_follow`, and pytest's failure-reporting machinery
(`_pytest.python.py:1715` → `Path.exists()` → `Path.stat()`) then hit the
still-active patch a second time while formatting that failure, escalating
an ordinary test failure into a session-ending `INTERNALERROR`. SWE-2/Devin
pinned this mechanism exactly against the hosted `test (windows-latest,
3.13)` job log; on Python 3.14, `Path.lstat()` calls `os.lstat()` directly,
bypassing the patch, which is why the test passed locally in this checkout
on every prior round. All three required Windows Python legs (3.11, 3.12,
3.13) were red at `754272a`, blocking merge — CodeRabbit's own
`@coderabbitai` chat independently confirmed the three failing job links.

**Fix.** The test no longer touches `pathlib.Path` at all. It is rewritten
as `test_write_report_manifest_never_reads_its_output_paths`: the output
path is deliberately never created on disk, so `write_report_manifest`
reopening it for its integrity fields would raise `FileNotFoundError` rather
than silently succeeding — the contract is pinned by construction, not by a
global monkeypatch. This is possible because the accompanying `PR23-F28` fix
(§11.3) removes the reopen entirely: `write_report_manifest` now takes
pre-computed `list[GeneratedOutput]` records and never touches the
filesystem for them.

**Regression test.** `TestReportManifestIntegrity::test_write_report_manifest_never_reads_its_output_paths`
(rewritten in place of the removed test); `TestRegisteredRun::test_report_manifest_covers_every_output`
(§11.3) additionally cross-checks the real registered outputs' on-disk bytes
against the manifest's recorded digest end to end.

### 11.2 `PR23-F27` (D2) — `_load_artefact` verified, then re-read the artefact through an unverified second open

*CLINE-A.I., SWE-2/Devin, and PERPLEXITY-AI, independently, on
`exp001_e4_analysis.py::_load_artefact`.*

`_load_artefact` called `verify_manifest(...)` (proving the run directory
matched its manifest at that moment), closed the descriptor that used, and
then separately opened the result artefact with `read_no_follow`.
`read_no_follow` proves only that *this* open is not a symlink; it does not
prove the reopened file's *content* is still the bytes `verify_manifest`
just accepted. All three reviewers reproduced the gap by replacing the
artefact with a different regular file between the two calls: `_load_artefact`
returned the replacement payload. Because `run_analysis` only re-verifies
the whole directory *after* `_load_artefact` already returned (previously
lines 1162–1169), an attacker or a racing process that restored the original
bytes before that later check would leave no trace — the unverified read
would have fed adjudication unmanifested bytes undetected.

**Fix.** `tools/reproduce.py` gains a new public function,
`read_verified_no_follow(path, expected_size, expected_sha256, name, role)`,
which opens the file exactly once and checks size and SHA-256 digest against
the given values *from that same descriptor* before returning its bytes —
mirroring `_verify_size_and_hash_no_follow`'s single-open discipline but
returning content instead of discarding it. `_load_artefact` now looks up
the `ManifestRecord` `verify_manifest` returned for `leg.artefact` and reads
through this function instead of the unverified `read_no_follow`. The bytes
`_load_artefact` returns are now provably the manifested ones at the moment
they are read, independent of what happened to the path beforehand — closing
the class of gap even for a swap-then-restore that a point-in-time
directory check alone cannot see.

**Regression test.**
`TestProvenanceGuard::test_load_artefact_rejects_a_swap_between_verification_and_read`
monkeypatches `analysis.verify_manifest` to swap the artefact's content as a
side effect of an otherwise-successful call — the earliest point after
verification and before the read that follows it — and confirms
`_load_artefact` now raises `ManifestMismatchError` instead of silently
returning the swapped payload. Proved against pre-fix source
(`git stash` on the two source files): the swapped payload was previously
returned without error. `test_load_artefact_reads_via_no_follow_not_plain_path_io`
is also strengthened to forbid `Path.read_bytes` alongside `Path.read_text`
— CLINE-A.I. and CodeRabbit both separately noted the pre-existing version
only forbade the latter, so a regression to the equally link-following
`read_bytes` would have passed undetected.

### 11.3 `PR23-F28` (D3) — the report-manifest's output digest still reopened a closed, written file

*CLINE-A.I., SWE-2/Devin, and PERPLEXITY-AI, independently, on
`write_report_manifest`.*

Round 4's `PR23-F24` fix (§10.2) closed the *symlink* case for output
integrity by moving to `stat_size_and_hash_no_follow`, but that function
still opens the path fresh, after `write_outputs` already wrote and closed
it. A concurrent replacement of the output with another *regular* file in
that window — not a symlink, so untouched by `PR23-F24`'s fix — is silently
accepted and digested; the committed `report-manifest.json` would then
attest replacement bytes instead of the ones `write_no_follow` actually
wrote. All three reviewers reproduced this by replacing
`exp001-e4-summary.md` between `write_outputs` and manifest construction and
observing the replacement's bytes recorded in `report-manifest.json`, and
converged on the same fix: hash the bytes already held in memory, not a
later reopen.

**Fix.** `write_outputs` now computes each output's size and SHA-256 digest
from the exact in-memory bytes it hands to `write_no_follow`, *before*
writing them, and returns a new `GeneratedOutput(path, bytes, sha256)`
record per output instead of a bare `Path`. `write_report_manifest`'s
signature changes to accept `list[GeneratedOutput]` and builds its
`"outputs"` entries directly from those fields — no filesystem read-back at
all. This closes the gap completely rather than partially: there is no
window left between "written" and "digested" because there is no longer a
second read of the path in between.

**Regression tests.**
`TestReportManifestIntegrity::test_write_report_manifest_never_reads_its_output_paths`
(§11.1) proves no reopen occurs, by construction. `TestRegisteredRun::test_report_manifest_covers_every_output`
is extended to hash each real registered output on disk and confirm it
matches the committed manifest's `bytes`/`sha256` fields exactly — proving
the in-memory shortcut does not drift from what is actually written, using
the real registered artefacts rather than a synthetic fixture.

### 11.4 `PR23-F29` (D4) — configured output/record roots were resolved before being checked for symlinks

*CLINE-A.I., SWE-2/Devin, and PERPLEXITY-AI, independently (originally
flagged by CodeRabbit in Round 3 as a declined-severity residual; this round
supplied a concrete reproduction and elevated it to a tracked finding).*

`allowed_output_roots`/`allowed_generated_output_dirs` build the permitted
write-destination set by calling `.resolve()` on `OUTPUT_ROOT`/`RECORD_ROOT`.
`.resolve()` follows a symlink, so if either configured root were itself
replaced with a symlink — for example `OUTPUT_ROOT` pointing at the frozen
`RECORD_ROOT` — the "permitted root" every later `_checked_destination`/
`_checked_manifest_destination` call trusts would silently become the
symlink's target, admitting writes there instead of refusing them.
Reproduced by symlinking `OUTPUT_ROOT` at a local checkout to `RECORD_ROOT`:
the resolved destination under the record was accepted as a permitted
generated-output location. All three reviewers classify this as bounded
defense-in-depth, not a remote-attacker path: it requires a local checkout
or filesystem change, and the committed roots are regular directories (or
absent) in every real checkout of this repository.

**Fix.** New `_reject_configured_root_symlink(path, name)` checks
`OUTPUT_ROOT`/`RECORD_ROOT` with `Path.is_symlink()` — no-follow, before
`.resolve()` — and raises `AnalysisError` if either is a symlink. Applied in
both `allowed_output_roots` (both roots) and `allowed_generated_output_dirs`
(`OUTPUT_ROOT` only, matching its existing scope). A root that does not yet
exist (`OUTPUT_ROOT` is gitignored) is not a symlink and is unaffected.

**Regression tests.**
`TestOutputContainment::test_allowed_output_roots_refuses_a_symlinked_output_root`,
`test_allowed_output_roots_refuses_a_symlinked_record_root`, and
`test_allowed_generated_output_dirs_refuses_a_symlinked_output_root`, gated
on the same `_needs_symlink_support` executability probe used in
`tests/test_reproduce.py` (Windows symlink creation needs elevated privilege
or Developer Mode). All three pass in this checkout, confirming symlink
creation is supported here and the guard fires correctly.

### 11.5 Reviewer claims checked and found sound but not separately actioned

- **CodeRabbit's docstring-coverage nitpick** (declined in Round 1 as
  `PR23-F9`) was independently re-raised as a candidate by CLINE-A.I. and
  re-affirmed as correctly declined by PERPLEXITY-AI: the generic 80 %
  threshold CodeRabbit's tool applies is not this repository's governing
  rule (`interrogate` at this project's own configured threshold, per §6),
  the module is fully documented against that rule, and the real gap
  (test-method docstrings, disabled by project `pydocstyle` configuration)
  remains tracked as `DV-040`. No change made; the Round 1 decline stands.
- **Copilot's H2a self-referential-minimum finding (`PR23-F23`), the
  non-regular-manifest finding (`PR23-F17`/`PR23-F25`), and the
  symlink-specific output-integrity finding (`PR23-F24`)** were each
  independently re-derived and confirmed fixed by all three reviewers
  against `754272a` — no regression found in any of them.

### 11.6 Verification

```text
.venv\Scripts\python -m pytest tests/test_exp001_e4_analysis.py tests/test_reproduce.py -q
  92 passed
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3242 passed, 179 skipped, 48 deselected in 424.61s
.venv\Scripts\python -m ruff check tools/reproduce.py exp001_e4_analysis.py tests/test_exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same three files>
  3 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m mypy tests/test_exp001_e4_analysis.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py exp001_e4_analysis.py
  No issues identified
```

**No regression to the published EXP-001 record**, re-verified after this
round's edits by re-running `run_analysis` to a scratch destination:

```text
H1: REFUTED   H2a: REFUTED   H2b: CONFIRMED   H3: CONFIRMED   H4: CONFIRMED
D1 flag: RAISED
report-manifest.json outputs, verdicts: byte-identical to the committed record
exp001-e4-adjudication.json / exp001-e4-summary.md: byte-identical to the committed record
```

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 0 issues; `tests/test_exp001_e4_analysis.py` 0 issues;
`exp001_e4_analysis.py` 1 issue (LOW, Path Traversal at the CLI destination
check itself — unchanged from §9.10/§10.6's finding, confirmed identical
against the pre-change baseline via `git show HEAD:<path>`, the same
structural false-positive class: the sanitizer's own entry point). No Snyk
Open Source / `cargo audit` / `pip-audit` run — no dependency files changed
this round.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN. `PR23-F26`
through `PR23-F29` FIXED with regression tests; the Windows required-check
blocker (`PR23-F26`) is structural (a test defect, not a production defect)
and closed by removing the offending monkeypatch rather than narrowing it,
per all three reviewers' recommendation; **no new D1 finding raised by this
audit round** (the campaign's existing EXP-001 D1 flag, raised at E4 by
H1/H2a `REFUTED`, is untouched by any finding in this round); no verdict,
tolerance, or measured value changed; no regression to the published EXP-001
record.
CodeRabbit and Copilot are re-requested on this round's push per standard
practice; their results are the next input, not a precondition already
folded into this report.

---

## 12. Round 6 — Copilot and CodeRabbit review of head `2264771`

**Trigger:** Round 5's push (`2264771`) was reviewed by Copilot (review
`5299455964`) and CodeRabbit (review `5299492692` plus its PR comment).
Copilot: 3 open findings (2 High, 1 Medium) — 1 carried from Round 1, 2 new
— and confirmed 3 prior findings (the H2a self-referential minimum, the
non-regular-manifest rejection, the symlink-specific output-integrity fix)
resolved. CodeRabbit: 2 findings, both precision issues in this audit
document's own prose, not code defects.

**Tooling instruction.** The task for this round asked that z3, Wolfram, and
Lean4 be used where beneficial in validating findings. `lean`/`lake` and
`wolframscript` are available in this environment; `z3` (Python package and
binary) is not installed. None of the three were a fit for this round's two
substantive findings: both are POSIX syscall-semantics facts (`open(2)`'s
`O_NOFOLLOW` scope, `O_NONBLOCK` behavior on regular files vs. FIFOs per
`fifo(7)`) — documented, not propositions in mathematical doubt that a
solver or proof assistant would add rigor to beyond the citation itself.
There was no new numeric or statistical claim this round either (Round 5
already carried SWE-2/Devin's independent Wolfram-Language recomputation of
the H2b bootstrap statistics). Recorded here rather than silently dropped.

### 12.1 Carried — "Manifest verification accepts symlinked files" (Copilot, High, comment `4084668748`, not tagged "New")

**Stale, re-confirmed.** The same GitHub discussion thread as the original
`PR23-F1` (Round 1), carried without a fresh "New" tag through Rounds 2–5
(§8.4). Re-derived fresh against `2264771`: `verify_manifest`
(`tools/reproduce.py` lines 612–669) calls `_reject_non_regular` on the
manifest and every `*.json` candidate, `_reject_symlink` on each manifested
artefact, and `_verify_size_and_hash_no_follow` (built on
`_open_no_follow`'s no-follow open) for the digest — no plain
`Path.stat()`/`read_text()`/`is_file()` anywhere in the path. The comment's
premise — "the campaign's closure validator explicitly rejects these links,
but this analysis bypasses that validator" — conflates `verify_manifest`
with a *different* function
(`benchmarks/campaign/exp001_driver.py::check_run_complete`, cited only as a
discipline `_reject_symlink`'s own docstring says this module *mirrors*);
using an independently no-follow-hardened equivalent is not a bypass. No
code change.

### 12.2 `PR23-F30` (D2) — an ancestor symlink could redirect a no-follow open outside the checked root

*Copilot, "Ancestor symlink replacement bypasses write containment" (New,
`tools/reproduce.py:286`, anchored on `write_no_follow` but identical in
`_open_no_follow`, the shared primitive behind every read path).*

`O_NOFOLLOW` refuses a symlink only at a pathname's *final* component
(POSIX `open(2)`); it does not stop a concurrent replacement of an
*ancestor* directory — for example the governed `output_dir` itself —
with a symlink between an earlier resolve-and-contain check
(`_checked_destination`/`allowed_output_roots`) and the actual `os.open()`
call. The final filename remains a plain, non-symlinked name throughout, so
the existing guard never fires while the open is silently redirected
outside the checked root (CWE-59). This applied to every caller of
`_open_no_follow`/`write_no_follow` — `read_no_follow`,
`stat_size_and_hash_no_follow`, `_verify_size_and_hash_no_follow`,
`read_verified_no_follow`, `verify_manifest`, `append_manifest`, and every
write in `exp001_e4_analysis.py` — not only the write-side line Copilot's
comment happens to anchor on.

**Fix, confirmed with the maintainer as the stronger of two options**
(narrow-only pre-open re-check vs. a `dir_fd`-based close): new
`_dir_relative_open(path, flags, mode, role) -> int | None` opens `path`'s
immediate parent directory as a descriptor (`O_DIRECTORY | O_NOFOLLOW`),
then opens the final component relative to that descriptor
(`dir_fd=parent_fd`). A file descriptor pins the directory inode it was
opened against; a later replacement of the path string's parent with a
symlink cannot redirect an open already performed relative to that
descriptor — this closes the window completely on POSIX, rather than only
narrowing it, and as a side effect also rejects a parent that is *already* a
symlink at call time. Used from both `_open_no_follow` and `write_no_follow`,
with a `None` return (platform doesn't support `dir_fd`-relative opens —
Windows) falling back to each function's existing, already-documented
`O_NOFOLLOW`-then-`is_symlink()` behavior, unchanged.

**Validation, stated honestly.** This session's machine (`win32`) has none
of `os.supports_dir_fd` for `os.open`, `os.O_DIRECTORY`, or `os.O_NOFOLLOW`
(checked directly: all `False`). The POSIX branch cannot be exercised here.
`tests/test_reproduce.py::TestOpenNoFollow::test_symlinked_parent_directory_is_rejected_for_reads`
proves the fix (symlink an ancestor, confirm `read_no_follow` now raises
`ManifestMismatchError` instead of reading through it) but is gated
`@_needs_dir_fd_support` — it **skips on this machine** and will run for
real on this repository's Linux CI legs, the same evidence-deferral pattern
already used here for DirectML/CUDA-gated tests
(`tests/_env.py::directml_executes`, `DV-030`). A separate,
platform-adaptive test,
`test_dir_relative_open_reflects_platform_support`, runs everywhere
(including here) and pins the guard itself — asserting `None` on a platform
without `dir_fd` support, or a working descriptor when it is supported —
so a future accidental weakening of that guard would fail immediately
rather than silently defeating the POSIX closure without any locally
visible signal.

### 12.3 `PR23-F31` (D3) — a check-then-open race could swap a candidate for a FIFO and hang instead of failing closed

*Copilot, "FIFO race can block manifest verification" (New,
`tools/reproduce.py:396`).*

`_reject_non_regular` is a fast pre-check, not atomic with the open that
follows it: a candidate could be swapped for a FIFO after the check and
before `_open_no_follow`'s `os.open(..., O_RDONLY)`. Opening a FIFO for
reading with no writer present blocks indefinitely on POSIX (`fifo(7)`),
turning what should be a fail-closed rejection into a hang. The write side
has the symmetric risk (`O_WRONLY` on a FIFO with no reader also blocks,
absent `O_NONBLOCK`).

**Fix.** `os.O_NONBLOCK` (via `getattr(os, "O_NONBLOCK", 0)`, a no-op where
undefined, i.e. Windows) is added to both the read flags in
`_open_no_follow` and the write flags in `write_no_follow`. Per Linux
`open(2)`, `O_NONBLOCK` "has no effect for regular files" — safe for the
overwhelming-majority legitimate case — but on a FIFO it makes the open
return immediately instead of hanging. A new shared post-open check,
`_reject_non_regular_fd(fd, path, role)`, `fstat`s the descriptor (whichever
branch produced it: `dir_fd`, `O_NOFOLLOW`, or the Windows fallback) and
rejects — closing the descriptor — anything that isn't `stat.S_ISREG`,
catching a FIFO (or other special file) that slipped past the pre-check no
matter which open branch handled it.

**Validation, stated honestly.** `os.mkfifo` and `O_NONBLOCK` don't exist on
Windows either, so the hang-prevention itself can't be locally reproduced
here.
`tests/test_reproduce.py::TestOpenNoFollow::test_fifo_candidate_does_not_hang_and_is_rejected`
is gated `@_needs_fifo_support` — it **skips on this machine**, and will run
for real on the Linux CI legs. The regular-file case (the overwhelming
majority path) is exercised by every pre-existing read/write test, all of
which still pass with the new flags and post-open check in place.

### 12.4 `PR23-F32`/`PR23-F33` (D4) — audit-document wording precision

*CodeRabbit, both against this document, not against any source file.*

- §11.1 described `write_report_manifest`'s input as "pre-computed `(path,
  bytes, sha256)` tuples"; the actual type is `list[GeneratedOutput]` (a
  frozen dataclass, not a bare tuple), matching §11.3's own wording. Fixed.
- The Round 5 verdict line's bare "no D1" could be misread as saying the
  campaign's *existing* D1 flag (raised at E4 by H1/H2a `REFUTED`) was
  cleared by that round's fixes, rather than "no *new* D1 finding was raised
  by that audit round." Reworded for precision; every round including this
  one leaves that flag exactly as EXP-001's report issued it.

### 12.5 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  93 passed, 2 skipped (the two dir_fd/FIFO-gated tests, by design — see §12.2/§12.3)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3243 passed, 181 skipped, 48 deselected in 428.36s (delta vs. Round 5's
  3242/179/48: +1 passed from the platform-adaptive test, +2 skipped from
  the two dir_fd/FIFO-gated tests — exactly the expected shape, 0 failed)
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py
  All checks passed!
.venv\Scripts\python -m ruff format --check tools/reproduce.py tests/test_reproduce.py
  2 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m mypy tests/test_reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

**No regression to the published EXP-001 record**, re-verified after this
round's edits by re-running `run_analysis` to a scratch destination:
`report-manifest.json` outputs and verdicts byte-identical to the committed
record; H1–H4 verdicts and the D1 flag unchanged.

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 0 issues; `tests/test_reproduce.py` 0 issues. No Snyk
Open Source / `cargo audit` / `pip-audit` run — no dependency files changed
this round.

**What is, and is not, locally verified this round.** The two new
platform-gated tests (`PR23-F30`, `PR23-F31`) skip on this Windows
development machine by design and are confirmed to skip (not silently pass)
rather than claimed as tested; their actual execution — proving the
`dir_fd` closure and the FIFO non-blocking rejection for real — is deferred
to this repository's Linux CI legs, consistent with `CLAUDE.md`'s "do not
claim a scan or test passed when it wasn't run" rule. Everything else in
this section (the Windows fallback paths, the regular-file case, the
carried-finding re-derivation, the doc wording fixes, and the full local
test/lint/type/security suite) is locally verified as shown above.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN, with two
findings' closure evidence deferred to CI by platform necessity (stated
above, not concealed). `PR23-F30` and `PR23-F31` FIXED with regression
tests; the carried Round 1 thread re-confirmed stale; both CodeRabbit
wording issues fixed; no new D1; no verdict, tolerance, or measured value
changed; no regression to the published EXP-001 record. CodeRabbit and
Copilot are re-requested on this round's push per standard practice.

---

## 13. Round 7 — Copilot review of head `e946a3c`

**Trigger:** Round 6's push (`e946a3c`) was reviewed by Copilot (review
`5300119532`). Both `PR23-F30` and `PR23-F31` are confirmed **resolved**.
Two new findings replaced them (both High), and the carried Round 1 thread
("Manifest verification accepts symlinked files") appeared again, unchanged
— re-derived below as still the same stale thread, no new code path
involved (GitHub itself now marks that thread *outdated*). CodeRabbit
answered the `@coderabbitai review` trigger with "Review finished" but
posted no review and no comments on this head; its earlier threads are all
resolved. A GraphQL query of every review thread on the PR confirms exactly
three unresolved threads at this head: the two new Copilot findings below
and the outdated carried one — nothing else outstanding from either bot.

Separately, CI on `e946a3c` failed on all three ubuntu `test` legs and the
`reproduce` job — one test, one root cause, audited as `PR23-F36` (§13.4).

### 13.1 `PR23-F34` (D2) — the ancestor-symlink fix closed only the immediate parent, not every ancestor, and Round 6's own docstrings overclaimed otherwise

*Copilot, "Pin every ancestor to prevent symlink race escapes" (New,
`tools/reproduce.py:203`).*

Correct and important: `_dir_relative_open` (Round 6, `PR23-F30`) pins only
`path.parent` — the *immediate* parent — as a descriptor. For a nested path
such as `/safe/nested/run/file`, replacing `/safe/nested` (a *grandparent*)
with a symlink before `_dir_relative_open`'s own `os.open(parent="/safe/
nested/run", ...)` call still lets that call transparently traverse the
symlinked `/safe/nested` component — `O_NOFOLLOW` there only guards the
component the call itself opens (`run`), not everything above it. Round 6's
own docstring claimed this "clos[ed] the window completely rather than
narrowing it," which was true only for the one level it actually pins — an
overclaim this audit should not have let stand.

**Disposition: documentation corrected; full ancestor-chain pinning declined
as disproportionate to this module's own threat model, not implemented.**
A fully general fix would require resolving and pinning every path
component from a trusted anchor down (`openat2(..., RESOLVE_NO_SYMLINKS)`
where available, or a manual per-component `dir_fd` walk — Python's stdlib
wraps neither directly), which this module has no existing concept of (no
caller currently threads "how far up is trusted" through
`_open_no_follow`/`write_no_follow`'s signatures) and would be a materially
larger, riskier change to a security-critical path this session cannot
locally test even for the one-level case already shipped. Every caller in
this module constructs its path as a fixed relative name under an
already-validated governed root (`run_dir`, `output_dir`, `results_dir` —
each checked by `allowed_output_roots`-style logic before any of these
functions run), so the immediate parent is both the level that check
actually names and the level a local concurrent writer realistically
reaches; a grandparent-or-higher swap requires the same attacker to already
control a segment of the checkout these paths don't treat as configurable.
Copilot's own comment offers "or narrow the guarantee to the immediate
parent" as an acceptable alternative — taken here, with the guarantee now
stated precisely rather than overclaimed. `_dir_relative_open`,
`_open_no_follow`, and `write_no_follow`'s docstrings are corrected to say
"the immediate parent" throughout and to explain, with the concrete
`/safe/nested/run/file` example, exactly why this does not extend further —
matching this codebase's existing honesty standard for the Windows fallback
(itself a "narrows, does not close" case for the very same reason, one
level further out). The one-level fix itself is unchanged and still real:
before Round 6, there was no ancestor protection at all; now the single
most directly-configured level (the governed root's own directory) is
closed on POSIX.

**No test change required** — `test_symlinked_parent_directory_is_rejected_for_reads`
(Round 6) already tests exactly the one-level guarantee this finding
clarifies the scope of, not a two-level one it never claimed to prove.

### 13.2 `PR23-F35` (D2) — `append_manifest`'s self-exclusion filter followed a symlink per candidate, letting a swapped candidate vanish from the inventory

*Copilot, "Prevent symlink swap from omitting manifest entries" (New,
`tools/reproduce.py:705`).*

`append_manifest` excluded the manifest's own file from its candidate
inventory by comparing each candidate's `.resolve()` against the manifest's
resolved `destination` — a link-following comparison, run in a comprehension
*after* the `_reject_non_regular` pre-check loop had already finished with
every candidate. A candidate that was still a regular file when that loop
checked it, then swapped for a symlink targeting `destination` before the
exclusion comprehension ran, resolves equal to `destination` and is silently
dropped from `actual_paths` — exactly like the manifest itself — without
ever reaching a no-follow open or surfacing as "missing" or "unmanifested".
Reproduced (and proven against pre-fix source per this audit's standing
methodology, §2/§3.1): a `sneaky.json` symlinked to `manifest_path` after
passing the pre-check loop vanished from the run with no error at all.

Notably, `verify_manifest` never had this defect: it already excludes its
self-reference by *name* (`candidate.name != manifest_path.name`), computed
once before any per-candidate check, not by a per-candidate `.resolve()`.
`append_manifest`'s exclusion had simply never been brought in line with
that already-hardened pattern.

**Fix.** `append_manifest`'s self-exclusion now matches `verify_manifest`'s:
computed once, by name, before the `_reject_non_regular` loop runs, with no
per-candidate filesystem operation at all. `actual_paths` is now built
unconditionally from the (already name-filtered) `candidates` list.

**Regression test.**
`TestManifestSymlinkProvenance::test_append_manifest_rejects_a_candidate_swapped_to_a_symlink_after_the_check`
monkeypatches `_reject_non_regular` to swap a regular candidate for a
symlink targeting `destination` immediately after it passes the pre-check —
the earliest point after that check and before the exclusion comprehension
that follows it. Proved against pre-fix source (temporarily restoring the
Round 6 committed `tools/reproduce.py`, running the new test, restoring the
fix): `DID NOT RAISE ManifestMismatchError` pre-fix (the candidate silently
vanished, exactly the defect), raises with a "symbolic link" message
post-fix (the candidate now reaches the ordinary no-follow open and fails
closed there once it is no longer excluded).

### 13.3 Carried — "Manifest verification accepts symlinked files" (Copilot, High, comment `4084668748`, unchanged)

Same stale Round 1 thread, unchanged from §12.1's re-derivation; neither of
this round's two fixes touches `verify_manifest` or `exp001_e4_analysis.py`.
No new evidence to add; no code change.

### 13.4 `PR23-F36` (D2) — Round 6's ancestor-symlink rejection raised the wrong error type on Linux, failing four required CI checks

*CI on `e946a3c`: `test (ubuntu-latest, 3.11/3.12/3.13)` and `reproduce`,
all failing on
`TestOpenNoFollow::test_symlinked_parent_directory_is_rejected_for_reads`
with `NotADirectoryError: [Errno 20] Not a directory`.*

This is the POSIX-only test §12.2 said "skips on this machine and will run
for real on this repository's Linux CI legs." It did run, and it caught a
real defect in the Round 6 fix. On Linux, `open()` with `O_DIRECTORY |
O_NOFOLLOW` on a symlink fails with `ENOTDIR`, not `ELOOP`: `O_NOFOLLOW`
stops the kernel following the link, and `O_DIRECTORY` then finds the link
itself is not a directory. `_dir_relative_open` translated only `ELOOP` into
`ManifestMismatchError`, so a symlinked parent was still refused — the fix
still failed closed, and no symlinked parent was ever followed — but as a
raw `NotADirectoryError`, breaking the documented error contract every
caller relies on. `ELOOP` alone had been assumed from the general
`O_NOFOLLOW` documentation without testing the `O_DIRECTORY` combination on
Linux; this session's Windows machine could not run that path, which is why
§12.2 deferred it to CI, and CI is where it surfaced.

**Fix.** The parent-open handler now also translates `ENOTDIR` — but only
when a no-follow `lstat` (`parent.is_symlink()`) confirms the parent is a
symlink, so a parent that is genuinely not a directory (a regular file)
still surfaces as its real `NotADirectoryError` instead of being mislabelled.
`ELOOP` stays unconditional, exactly as before. The lstat runs only after
the open has already failed closed, so it chooses the error message and
cannot reopen the window.

**Regression tests, runnable on every platform.** The CI-only test was the
sole coverage of this branch, and it could not run here. Two new tests
simulate Linux's exact behavior by replacing `reproduce`'s own `os`
reference — never the global `os` module, per the `PR23-F26` lesson — with
a POSIX-like stand-in whose directory open raises `ENOTDIR`:
`test_linux_enotdir_for_a_symlinked_parent_is_a_manifest_mismatch` and
`test_linux_enotdir_for_a_genuine_non_directory_parent_is_reraised`. Both
run on this Windows machine. The first was proved against the pushed
`e946a3c` source: it fails there with the same `NotADirectoryError` CI
reported, and passes with the fix. The original POSIX test is unchanged and
is expected to pass on the next CI run; that remains unconfirmed until CI
reports it.

### 13.5 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  96 passed, 2 skipped (the two dir_fd/FIFO-gated tests, unchanged from Round 6)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3245 passed, 181 skipped, 48 deselected, 1 failed then verified flaky (note below)
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py
  All checks passed!
.venv\Scripts\python -m ruff format --check tools/reproduce.py tests/test_reproduce.py
  2 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m mypy tests/test_reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

**Flaky-test note.** The one full-suite failure,
`tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`,
compares the wall-clock time of CPU work with and without a background
daemon thread. The module never imports `tools.reproduce`, and this round
changes no file it depends on. Re-run in isolation three times on identical
code: passed, failed, passed. Not attributable to this change; the same
class as the wall-clock flake recorded in §10.6.

Also re-verified directly against the real repository manifest (not just
synthetic fixtures): `reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error.

**No regression to the published EXP-001 record**, re-verified after this
round's edits by re-running `run_analysis` to a scratch destination:
`report-manifest.json` outputs and verdicts byte-identical to the committed
record; H1–H4 verdicts and the D1 flag unchanged.

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 0 issues; `tests/test_reproduce.py` 0 issues. No Snyk
Open Source / `cargo audit` / `pip-audit` run — no dependency files changed
this round.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN locally; CI
confirmation pending. `PR23-F34` (documentation-precision correction; no new
attack surface closed, an existing overclaim removed), `PR23-F35` (a genuine
second TOCTOU instance), and `PR23-F36` (the Linux-only error-type defect
that failed four required CI checks at `e946a3c`) are all resolved, the
latter two with regression tests proven against pre-fix source. The carried
Round 1 thread is re-confirmed stale for the third time running; no new D1;
no verdict, tolerance, or measured value changed; no regression to the
published EXP-001 record; the real 172-record repository manifest still
verifies.

**`PR23-F36` closure confirmed by CI, 2026-09-24 UTC.** All three ubuntu
`test` legs and the `reproduce` job — the four checks that failed on
`e946a3c` — passed on `d5f47d6`, on the real Linux kernel this session's
Windows machine could not test directly. `test (macos-latest)` also passed;
macOS is POSIX and exercises the same `_dir_relative_open`/`O_NONBLOCK`
code paths as Linux. Every other required check passed as well.

---

## 14. Round 8 — Copilot review of head `d5f47d6`

**Trigger:** Round 7's push was reviewed by Copilot (review `5300429743`).
Both `PR23-F35` and `PR23-F34` (as documentation-precision, not a code
defect — see §14.2) are confirmed resolved. Two new findings replaced them,
one High-severity genuine defect (`PR23-F37`) and a re-raised instance of
the already-considered ancestor-symlink question (§14.2). The carried
Round 1 thread appeared again, unchanged, still marked outdated by GitHub.

### 14.1 `PR23-F37` (D2) — a hard-linked destination let a write silently corrupt an unrelated file

*Copilot, "Hard links allow manifest writes to overwrite frozen reports"
(New, `exp001_e4_analysis.py:1213`, generalizing to every call site of
`write_no_follow`).*

**Valid, and a materially different bug class from every prior finding in
this file.** Every no-follow guard added across Rounds 1–7 defends against
a *symlink* — a distinct file type, detectable with `is_symlink()`/
`O_NOFOLLOW`. A **hard link** is not a symlink: it is a second directory
entry naming the *same inode* as an existing file, with no separate
identity and no special file type — `stat.S_ISREG` is true for it, exactly
as for any other regular file, and every check this module has ever run
(`_reject_symlink`, `_reject_non_regular`, `_reject_non_regular_fd`) passes
it without complaint. A local process able to create
`RECORD_ROOT/report-manifest.json` as a hard link to `RECORD_ROOT/
report.md` (`os.link(report_md, manifest_path)`, same filesystem, ordinary
user permission — the same governed-CI/local-checkout access level every
other finding in this file already assumes) would pass
`_checked_manifest_destination`'s canonical-name check and every symlink
guard `write_no_follow` runs, and the in-place `O_TRUNC` write would then
overwrite `report.md`'s actual bytes too, since both names shared the same
data. Reproduced and proven against pre-fix source (temporarily restoring
the Round 7 committed `tools/reproduce.py`): a hard-linked sibling file's
content was overwritten as soon as the linked destination was written.

**Fix.** `write_no_follow` no longer opens `path` in place at all. It writes
to a freshly, *exclusively* created sibling file (`O_CREAT | O_EXCL`, which
can never open an existing hard link — it guarantees a brand-new inode or
fails), through the same `_dir_relative_open`/`O_NOFOLLOW`/`O_NONBLOCK`/
`_reject_non_regular_fd` machinery every other open in this module already
uses, and then atomically swaps it into place with `os.replace(tmp_path,
path)`. `os.replace` repoints only `path`'s own directory entry to the new
inode; whatever else the old entry's inode was linked to, if anything, is
never opened, truncated, or touched by this call. The function's documented
"refuses to write through a symlinked destination" contract is preserved
with an explicit `path.is_symlink()` check immediately before the swap
(`os.replace` itself never follows a trailing symlink on either side, so
this is belt-and-suspenders for the existing error message, not the sole
guard against it). Any failure between temp-file creation and the swap
cleans up the temp file rather than leaving it behind.

**Regression test.** `TestWriteNoFollow::test_does_not_corrupt_a_hard_linked_sibling`
hard-links a "frozen" file to a governed destination name, writes through
the destination, and asserts the frozen file's bytes are untouched. Proved
against pre-fix source (`git show d5f47d6:tools/reproduce.py`, restored
temporarily): the frozen file's content became the new write's content —
`assert frozen.read_bytes() == b"immutable original\n"` failed with
`b'new manifest content\n' == b'immutable original\n'`, exactly the
corruption described. Passes with the fix. Every pre-existing
`write_no_follow` test (new-file, truncate-existing, symlinked-destination)
still passes unchanged against the rewritten implementation.

### 14.2 Re-raised — "Ancestor symlink replacement bypasses no-follow path protection" (Copilot, High, comment `4090442972`, citing `tools/reproduce.py:211/376/443`)

**Not a new finding — the same structural pattern as `PR23-F34` (§13.1),
re-flagged.** All three cited lines are the single `_dir_relative_open`
mechanism and its two callers; nothing about that code changed between
Round 7 and this review. `PR23-F34` already established, with the concrete
`/safe/nested/run/file` example this comment repeats: `_dir_relative_open`
closes the race for the *immediate* parent only, the docstrings now say so
precisely (they did not, before Round 7's fix), and full ancestor-chain
closure was considered and declined as disproportionate — it would require
threading a "trusted anchor" parameter through this module's entire public
surface (`_open_no_follow`, `write_no_follow`, `_dir_relative_open`,
`verify_manifest`, `append_manifest`, `read_verified_no_follow`,
`stat_size_and_hash_no_follow`, every caller in `exp001_e4_analysis.py`), a
breaking API change, to close a threat that already requires the same
local-write access this module's entire threat model assumes throughout —
the identical governed-CI/local-checkout posture already invoked for the
Windows fallback (§12.2), `_safe_temp_root` (§9.4), and now `PR23-F37`
above. An automated line-level reviewer scanning code structure has no way
to know a limitation was already deliberately documented rather than
missed; re-affirming the same considered decision here, rather than
re-litigating it, is this audit's own established practice for exactly this
situation — the same one applied to CodeRabbit's docstring-coverage nitpick
(`PR23-F9`, §6), declined once and re-affirmed when it recurred (§11.5).

**Disposition: declined, re-affirmed, added to the ledger below. No code
change.** If a future round finds a concrete, reproducible exploit of the
grandparent-or-higher case against this repository's actual governed roots
(not merely the general POSIX possibility, which is not in dispute), that
would be new evidence changing this calculus and should reopen it as a
fresh finding, not a repeat of this one.

**Declined-findings ledger entry (extending §6's Round 1 table):**
"Pin every ancestor directory component, not only the immediate parent, in
`_dir_relative_open`" — raised by Copilot in Rounds 7 and 8 (`PR23-F34`
context, and again here); declined both times with rationale above; not a
false positive (the underlying POSIX fact is correct), declined as
disproportionate engineering cost relative to this module's own stated
threat model.

### 14.3 Carried — "Manifest verification accepts symlinked files" (Copilot, High, comment `4084668748`, unchanged, GitHub-marked outdated)

Same stale Round 1 thread as §12.1/§13.3. No new evidence; no code change.

### 14.4 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  97 passed, 2 skipped (the two dir_fd/FIFO-gated tests, unchanged from Round 6)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3247 passed, 181 skipped, 48 deselected in 501.65s (0 failed — the
  wall-clock flake from Round 7's run did not recur)
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py
  All checks passed!
.venv\Scripts\python -m ruff format --check tools/reproduce.py tests/test_reproduce.py
  2 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m mypy tests/test_reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

Also re-verified directly against the real repository manifest:
`reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error.

**No regression to the published EXP-001 record**, re-verified after this
round's edits by re-running `run_analysis` to a scratch destination:
`report-manifest.json` outputs and verdicts byte-identical to the committed
record; H1–H4 verdicts and the D1 flag unchanged. `write_outputs`/
`write_report_manifest` both call the rewritten `write_no_follow`, so this
also confirms the atomic-replace rewrite reproduces byte-for-byte identical
output to the in-place write it replaced.

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 3 issues (LOW, Path Traversal — new count, up from 0),
`tests/test_reproduce.py` 0 issues. All 3 are the same structural
false-positive class accepted every round since §9.10: a CLI argument
reaching a path-write operation (now `os.replace`) without Snyk's
control-flow-insensitive tracer recognizing the containment check
(`ALLOWED_MANIFEST_ROOTS` inside `append_manifest`, or
`_checked_manifest_destination`/`allowed_output_roots` in
`exp001_e4_analysis.py`) that runs earlier in the same function before any
write is reachable. Confirmed by inspection: `append_manifest`'s
`ALLOWED_MANIFEST_ROOTS` check (line 685, unchanged this round) raises
before `write_no_follow` can be reached from that path; the finding is not
a new gap, only a new count because the rewrite added more call sites in
the same already-accepted taint chain. No Snyk Open Source / `cargo audit`
/ `pip-audit` run — no dependency files changed this round.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN. `PR23-F37`
(a genuine, materially new bug class — hard links, not symlinks) fixed
with a regression test proven against pre-fix source. The re-raised
ancestor-symlink finding declined again, on the record, for the reasons
already given in `PR23-F34`; no new attack surface, no code change. The
carried Round 1 thread re-confirmed stale for the fourth time running. No
new D1; no verdict, tolerance, or measured value changed; no regression to
the published EXP-001 record; the real 172-record repository manifest
still verifies. CodeRabbit and Copilot are re-requested on this round's
push per standard practice.

---

## 15. Round 9 — Copilot review of head `949e5e1`

**Trigger:** Round 8's push was reviewed by Copilot (review `5300648825`),
which raised 6 open findings: 3 new, 2 carried (both already assessed —
the hard-link fix reads as still-open pending this round's push landing,
the ancestor-symlink question already declined at §14.2), and the stale
Round 1 thread. All required CI checks passed on `949e5e1`, including
every Windows/macOS/ubuntu `test` leg and `reproduce` — the last of these
having been the ones that failed two rounds ago (§13.4).

### 15.1 `PR23-F38` (D2) — a colliding `--manifest-path` could overwrite a generated output after its digest was already recorded

*Copilot, "Manifest path can overwrite a generated output file" (New,
`exp001_e4_analysis.py:1213`).*

**Valid, confirmed by tracing the actual CLI validation.**
`allowed_output_roots` (used for `--manifest-path`) and
`allowed_generated_output_dirs` (used for `--output-dir`) both include
`OUTPUT_ROOT`, and neither check knows the other's specific target
filenames. `--output-dir X --manifest-path X/exp001-e4-summary.md` passes
both independent checks: `write_outputs` writes the summary file and
records its digest in a `GeneratedOutput` (computed from the in-memory
bytes, per `PR23-F28`), then `write_report_manifest` writes the manifest to
the *same path*, overwriting the summary. `report-manifest.json` then
attests a digest for bytes no longer on disk — the committed record and the
actual generated file silently diverge for that one output. This requires a
user (or script) to explicitly choose colliding CLI arguments; it is a
correctness/data-integrity gap, not an attacker-controlled path.

**Fix.** Two new module constants, `SUMMARY_FILENAME` and
`ADJUDICATION_FILENAME`, replace the filename string literals previously
duplicated inline in `write_outputs`. `main()` now cross-checks the two
independently-validated destinations against each other: if the resolved
`--manifest-path` equals `output_dir / SUMMARY_FILENAME` or
`output_dir / ADJUDICATION_FILENAME`, it raises `AnalysisError` before
`run_analysis` is called — matching this module's own stated architecture
("the guard lives at the command-line boundary, not in the library").

**Regression test.**
`TestOutputContainment::test_the_cli_refuses_a_manifest_path_colliding_with_a_generated_output`
exercises the exact CLI combination against a sandboxed fake checkout.
Proved against pre-fix source (`git show 949e5e1:...`, temporarily
restored): failed with `AttributeError: module 'exp001_e4_analysis' has no
attribute 'SUMMARY_FILENAME'` — confirming the constant, and therefore the
guard, did not exist before this fix. Passes post-fix.

### 15.2 `PR23-F39` (D2) — the pinned parent descriptor was discarded before the final rename, reopening the ancestor-symlink window `PR23-F30` had just closed

*Copilot, "Final rename loses pinned-directory no-follow protection" (New,
`tools/reproduce.py:493`).*

**Valid — and, notably, a gap I had already privately flagged as a
deliberately-scoped-out residual when implementing the `PR23-F37`
hard-link fix, reasoning the cost disproportionate; on reflection prompted
by this finding, it is not.** `write_no_follow`'s Round 8 rewrite (create a
temp file, then `os.replace` it into place) opened the parent directory as
a pinned descriptor via `_dir_relative_open` *only* for the temporary
file's creation — that helper closes the descriptor before returning.
The subsequent `os.replace(tmp_path, path)` then re-resolved `path`'s
parent by string, exactly the path-based resolution the pinned descriptor
exists to avoid: a symlink swapped into the parent directory *after* the
temporary file was written but *before* the replace would still redirect
the final swap outside the checked root, reopening the exact window
`PR23-F30` (§12.2) closed for the open half of this function without
closing it for the write-side rename half.

**Fix.** `_dir_relative_open` is split: the parent-opening logic moves into
a new `_open_parent_dir_fd(parent, role) -> int | None`, and
`_dir_relative_open` becomes a thin wrapper around it (used unchanged by
`_open_no_follow`). `write_no_follow` now calls `_open_parent_dir_fd`
directly and keeps the returned descriptor open across *both* the
temporary file's creation *and* the final swap, which is now performed as
`os.replace(tmp_path.name, path.name, src_dir_fd=parent_fd,
dst_dir_fd=parent_fd)` — relative to the same pinned descriptor, not a
path string — when the platform supports `dir_fd` on `os.replace`
(checked via `os.replace in os.supports_dir_fd`, falling back to a plain
`os.replace(tmp_path, path)` otherwise, so an incorrect assumption about
platform support degrades to the prior, still-correct-if-narrower
behavior rather than misbehaving). Windows (no `dir_fd` support at all)
is unaffected — its rename already re-resolves by path, the same
narrowing-only posture already documented for every other Windows
fallback in this module.

**Validation, stated honestly.** This session's Windows machine cannot
exercise the `dir_fd`-relative replace path at all (same limitation as
every dir_fd-gated fix this round and last). A live two-step race (swap the
parent between write and replace) is not simulated by a test — a
single-threaded test cannot reliably reproduce that timing, and a fragile,
unverifiable-here attempt at one was judged a worse trade than a simpler,
robust alternative.
`TestWriteNoFollow::test_final_swap_uses_the_pinned_parent_descriptor` (
`@_needs_dir_fd_support`, skips on this machine, runs for real on
Linux/macOS CI) instead pins the *call shape*: it spies on `os.replace`
and asserts `write_no_follow` calls it with matching, non-`None`
`src_dir_fd`/`dst_dir_fd` whenever a parent descriptor is available — proof
the fix's actual mechanism is exercised, not silently bypassed, which is
the risk a logic error in this rewrite would most plausibly produce.

### 15.3 Deferred, declined with rationale — "Mixed aborts can incorrectly produce a CONFIRMED verdict"

*Copilot, `exp001_e4_analysis.py:361` (`_tolerance_verdict`, shared by
H1/H2a/H3/H4).*

**Investigated in depth; declined, with the maintainer's confirmation.**
Copilot's claim: `_tolerance_verdict(failing, non_aborted, denominator)`
can return `CONFIRMED` for a run with a *full* clean denominator *plus* an
extra aborted case (e.g. 504 passing + 1 aborted = 505 total cases for
H1), which it characterizes as contradicting pre-registration §10.

**Re-derived directly from the frozen pre-registration text, not taken on
either the finding's or the module's own docstring's word.**
Preregistration §8 states, verbatim, for every one of H1/H2a/H3: `CONFIRMED`
iff all non-aborted cases pass **and** the non-aborted count is exactly the
full denominator — worded as a count equality, not an upper bound. §10
restates the same rule for the general mixed-abort case: "the hypothesis is
then `INCONCLUSIVE` (never `CONFIRMED`) **unless** the non-aborted cases
still meet the full registered denominator." Both sections, read literally,
permit `CONFIRMED` whenever the non-aborted count reaches the denominator —
the code implements the registered text as written, not a misreading of it.

The scenario the finding describes requires *more total cases than the
denominator*, which does not arise under how these artefacts are actually
produced: H1's corpus, H3's representative set, and H4's kernel-path grid
are each a fixed-cardinality set (504/14/72 respectively) that a run
processes exactly once per case — an abort *replaces* a would-be pass/fail
outcome for one of that fixed set, it does not *add* a case beyond it.
(H2a's denominator is the run's own recorded batch size, a different
mechanism already gated separately by `REGISTERED_FUZZ_BATCH_MIN`,
`PR23-F23`.) No currently-committed EXP-001 artefact contains more cases
than its hypothesis's registered denominator, and the real E3–E5 execution
recorded zero aborts of any kind across all four runs (report.md, CHANGELOG:
"No case aborted in any run"). This finding therefore cannot affect any
already-published verdict, whether fixed or left alone.

Whether it is worth hardening `_tolerance_verdict` against a
larger-than-denominator input regardless is a real, separate question — but
this module is the committed analysis code of a completed,
maintainer-accepted E5 report, the same governing fact §6 already applied
to decline `PR23-F10`/`PR23-F11`. Editing adjudication logic here, even in
a defensive direction that would not change any output for real inputs,
is out of scope for a PR-review-response round without either evidence it
is reachable against a real artefact or an explicit decision to make the
change. **Put to the maintainer directly; decision: decline, matching
`PR23-F10`/`PR23-F11`'s disposition, recorded here rather than silently
dropped.** If `EXP-001-r1`'s planning (the correction-cycle re-run this
campaign already requires) determines the driver could ever emit more
cases than a hypothesis's registered denominator, that is new evidence
reopening this as a fresh finding against the *r1* analysis code, not a
retroactive change to this one.

**Declined-findings ledger entry (extending §6):** "Harden
`_tolerance_verdict` against a non-aborted count exceeding the full
registered denominator" — raised by Copilot (Round 9); not a
misimplementation of the registered rule (the code matches pre-registration
§8/§10's literal text); declined as out of scope for the frozen,
maintainer-accepted E4 analysis module, unreachable against every
currently-committed artefact; put to the maintainer directly, who confirmed
the decline.

### 15.4 Carried — hard links (`PR23-F37`) and ancestor symlink (`PR23-F34`)

Both re-listed by this review as still "open" rather than "resolved since
last review," despite `PR23-F37` being fixed in the commit this review was
run against (`949e5e1` — the same commit introducing the fix). Re-derived
directly: `write_no_follow` (`tools/reproduce.py`) no longer opens a
destination in place at all; the create-temp-then-`os.replace` fix from
§14.1 is present and unchanged in the diff between `d5f47d6` and
`949e5e1` other than the `PR23-F39` refinement in this same round. This
reads as Copilot's thread-tracking not having caught up with its own prior
"Resolved since last review" determination from the same review body,
rather than a real regression — no different code exists to re-examine.
The ancestor-symlink item is the same already-declined `PR23-F34`
question (§14.2), re-listed without new content. No code change from
either carried item this round.

### 15.5 Carried — "Manifest verification accepts symlinked files"

Same stale Round 1 thread as §12.1/§13.3/§14.3. No new evidence; no code
change.

### 15.6 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  98 passed, 3 skipped (the two dir_fd/FIFO-gated tests from Round 6/7 plus
  the new dir_fd-replace spy test, all by design)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
  3248 passed, 182 skipped, 48 deselected in 534.34s, 0 failed (exactly the
  expected +1 passed / +1 skipped from this round's two new tests)
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py exp001_e4_analysis.py tests/test_exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same four files>
  4 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m mypy tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

Also re-verified directly against the real repository manifest:
`reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error.

**No regression to the published EXP-001 record**, re-verified after this
round's edits by re-running `run_analysis` to a scratch destination:
`report-manifest.json` outputs and verdicts byte-identical to the committed
record; H1–H4 verdicts and the D1 flag unchanged — including for `PR23-F38`
and `PR23-F39`, neither of which touches any adjudication path.

**Security gates.** Local Snyk Code (CLI `1.1306.2`, org `symbo-gif`):
`tools/reproduce.py` 4 issues (LOW, Path Traversal — up from 3, same
already-accepted structural class as §14.4, now one more call site in the
same taint chain: the `PR23-F39` rewrite's second `os.replace` branch),
`exp001_e4_analysis.py` 1 issue (LOW, unchanged from every prior round —
confirmed identical, no new finding from the `main()` collision check),
`tests/test_reproduce.py` and `tests/test_exp001_e4_analysis.py` 0 issues
each. No Snyk Open Source / `cargo audit` / `pip-audit` run — no dependency
files changed this round.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN at push time,
locally. `PR23-F38` fixed with a regression test. `PR23-F39` was believed
fixed by pinning the correct call shape — **this belief was wrong; see §16
for the correction.** The verdict-logic finding investigated in depth and
declined with the maintainer's direct confirmation, matching
`PR23-F10`/`PR23-F11`'s established precedent — not a misreading of the
registered rule, and unreachable against any currently-committed artefact.
Both carried items re-confirmed with no new content. No new D1; no verdict,
tolerance, or measured value changed; no regression to the published
EXP-001 record; the real 172-record repository manifest still verifies.

---

## 16. Round 9 correction cycle — a wrong assumption shipped, caught by real CI, fixed in two more passes

**This section exists because §15's `PR23-F39` claim was wrong, and this
audit's own standing rule is to record that on the record rather than
quietly edit history.** What happened, in order:

**1. The mistake.** `PR23-F39`'s fix assumed `os.replace` supports
`dir_fd`-relative operation on POSIX wherever `os.open` does — a plausible
but *unverified* assumption, since this session's Windows machine cannot
exercise that code path at all. It was documented as such in §15.2 at the
time, with the stated intent that CI would be the real verification. Pushed
as `949e5e1`.

**2. CI disproved it.** All three ubuntu `test` legs and `reproduce` failed
identically: `assert calls[0]["src_dir_fd"] is not None` → `None`.
`os.replace not in os.supports_dir_fd` on real Ubuntu/Python 3.12, even
though `os.open` is. The production code's own defensive fallback
(`if parent_fd is not None and os.replace in os.supports_dir_fd: ... else:
os.replace(tmp_path, path)`) had already degraded correctly and safely —
`write_no_follow` never actually broke a write, wrote no incorrect bytes,
and corrupted nothing. Only the *test's* assertion, which asserted the
dir_fd branch must have been taken, was wrong to assert that.

**3. First correction (`b9e3239`).** Reverted the final swap to the
unconditional, plain-path `os.replace(tmp_path, path)` — the exact call
Round 8's already-verified hard-link fix used. The pinned parent descriptor
is still obtained and used for the temporary file's creation (exercised
for real by every `write_no_follow` test on Linux/macOS CI); only the final
rename step stopped attempting to reuse it. The invalid test was replaced
with one asserting descriptor closure by call-count rather than by
re-asserting the same broken mechanism.

**4. The replacement test also broke CI.** `b9e3239` failed the same four
checks again — a *different* assertion this time
(`test_parent_descriptor_is_closed_after_a_successful_write`:
`assert closed_count >= opened_dir_fds > 0` → `opened_dir_fds` was `0`).
Root cause, diagnosed from the CI log alone (no local reproduction
possible): monkeypatching `os.open` to spy on it replaces the function
object `reproduce.py`'s own `os.open in os.supports_dir_fd` membership
check compares against. A monkeypatched replacement is a *different
function object* than the real one `os.supports_dir_fd` was populated
with, so the identity check silently started returning `False` for the
whole duration of the test — `_open_parent_dir_fd` fell back to `None`,
the dir_fd branch never ran, and `opened_dir_fds` stayed `0` correctly
given what actually happened, just not what the test intended to observe.

**5. Second correction (`df5a476`).** The spy-based test is removed
outright, not patched again — a third attempt at asserting an internal
mechanism this session cannot locally verify was judged the wrong
response to two consecutive failures of that same strategy. Replaced with
`test_repeated_writes_do_not_exhaust_file_descriptors`: 300 writes in one
process, asserting the *outcome* a real descriptor leak would break
(`OSError: Too many open files` under the default Linux `ulimit`), with no
monkeypatching of `os` at all. This is deliberately a weaker proof than a
mechanism-level assertion would be — it cannot distinguish "no leak" from
"a leak too small to hit the descriptor limit in 300 iterations" — but it
is a proof this session can actually stand behind, rather than a fourth
guess.

**Two further findings addressed in the same push**, both lower-risk than
the reverted attempt and verified with the same "check, don't assume"
discipline this correction cycle is itself the evidence for:

- **`PR23-F41` (D3) — the cleanup-on-failure path (`tmp_path.unlink()`)
  re-resolved by path string even when a pinned parent descriptor was
  still open**, so a symlink swapped into the parent during the call could
  delete a same-named file elsewhere instead of the temporary file this
  function actually created. Fixed with `os.unlink(tmp_path.name,
  dir_fd=parent_fd)`, gated on `os.unlink in os.supports_dir_fd` *checked
  at runtime*, falling back to the prior path-based unlink when that
  check is false — so an incorrect assumption about `os.unlink`'s support
  (which, per this same correction cycle, cannot be ruled out) degrades to
  the already-safe prior behavior rather than breaking anything. Tested by
  outcome (strengthening the existing symlinked-destination test to assert
  no stray temp file remains), not by mechanism, learning the exact lesson
  of steps 1–4 above.
- **`PR23-F42` (D4) — `verify_manifest`/`append_manifest`'s self-exclusion
  compared candidate names as bare strings**, so a `--manifest-path`
  differing only in case from the file actually on disk would not
  self-exclude on a case-insensitive filesystem (Windows), misreporting
  the manifest itself as an unmanifested artefact. Fixed with
  `os.path.normcase`, the identity function on POSIX (no behavior change
  there) and case-folding on Windows. **Proven directly on this session's
  own Windows machine** (NTFS is naturally case-insensitive, no CI
  dependency needed): fails against pre-fix source with the exact
  predicted mismatch (`['a.json', 'manifest.json'] == ['a.json']`), passes
  post-fix.

**Re-raised — "pin every ancestor" against a second function.** Copilot's
`4ed9f14` review raised the same class of finding as `PR23-F34` again,
this time against `exp001_e4_analysis.py::_reject_configured_root_symlink`
(checks only the configured root's own final component, not an ancestor
like `DOCS/test_and_benchmark_results`). Declined for the identical
reason already on record at `PR23-F34`: closing it fully requires walking
every path component from a trusted anchor, disproportionate to a threat
already requiring the local-write access this whole containment scheme
assumes. Documented in `_reject_configured_root_symlink`'s own docstring,
extending the `PR23-F34` ledger entry rather than opening a new one.

### 16.1 What this correction cycle demonstrates, stated plainly

Two of three attempts to close `PR23-F39`'s residual failed CI before the
third held. Both failures were caught immediately by this repository's own
required Linux CI gate — exactly the gate this audit's every prior
platform-gated fix (`PR23-F30`, `PR23-F31`, `PR23-F35` region) said
verification was deferred to. That gate worked as designed. The error was
shipping an assumption about a specific platform's runtime behavior
(`os.replace`'s `dir_fd` support) that this session could not verify
before pushing, twice in a row — first the assumption itself, then a test
built to prove it that broke a *different* unverifiable-here assumption
(monkeypatch identity semantics against `os.supports_dir_fd`). The
correction each time was to reduce the claim to what could actually be
verified, not to keep guessing: `PR23-F39`'s final state makes a smaller
claim than originally attempted (temp-file creation only, not the full
rename), honestly documented as smaller, rather than a larger claim
resting on unverified ground.

**A third CI failure, on `df5a476`, for an unrelated reason: `PR23-F42`'s
own regression test.** `test_append_manifest_self_excludes_case_insensitively`
created `manifest.json`, then referred to it as `MANIFEST.JSON`, assuming
both name the same physical file — true on Windows and default-configured
macOS, **false on Linux ext4**, which is case-sensitive: there,
`MANIFEST.JSON` is simply a different, nonexistent path, so
`append_manifest` correctly (for that platform) found the real
`manifest.json` as an unmanifested stray candidate and appended it,
exactly reproducing the failure the fix itself was meant to prevent.
`PR23-F42`'s production fix (`os.path.normcase`) was never wrong; the
test's *own setup* assumed a filesystem property — case-folding — it
never actually checked. Corrected in `c02e1d7` by probing the real
filesystem directly (create the file, then check `Path("...
DIFFERENTCASE").exists()`) and skipping cleanly where the two names are
genuinely different files, rather than assuming platform behavior from
`os.name` or any other indirect signal. This is the identical "verify, do
not assume" lesson as the `os.replace`/`os.supports_dir_fd` failures
above, now demonstrated a third time against a third distinct kind of
platform-dependent behavior (`dir_fd` syscall support, monkeypatch
identity semantics, filesystem case-folding) — three different mechanisms,
one recurring root cause: an assumption this session's Windows machine
structurally cannot verify, shipped without first finding a way to verify
it by other means (documentation citation, direct probing, or accepting a
narrower, provable claim), each time caught by the same CI gate this
audit's methodology has repeatedly said was the actual authority for
exactly this class of claim.

### 16.2 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  100 passed, 2 skipped
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py exp001_e4_analysis.py
  All checks passed!
.venv\Scripts\python -m ruff format --check <same three files>
  3 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m mypy tests/test_reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

Also re-verified directly against the real repository manifest:
`reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error.

**No regression to the published EXP-001 record**, re-verified after every
commit in this correction cycle by re-running `run_analysis` to a scratch
destination: `report-manifest.json` outputs and verdicts byte-identical to
the committed record throughout.

**CI, the actual authority here.** `reproduce` and all three ubuntu `test`
legs — the checks this whole correction cycle is about — are the
authoritative verification for the `dir_fd`/`os.replace`/`os.unlink`
claims made in this section; local results above cover everything else.
`df5a476` itself failed CI a third time, on `PR23-F42`'s own test — see
above; `c02e1d7` is the head this section's verdict actually covers.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN, CI-confirmed
on `c02e1d7`. `reproduce` and all three ubuntu `test` legs — the checks
that failed on `949e5e1`, `b9e3239`, and `df5a476` in turn — are green;
every other required check (Windows ×3, macOS, `parity`, `audit`, `lint`,
`security`, `Snyk Code`, `Secret Scan`, `governance`, `fmt`, `clippy` ×2,
`test-strict`, `bench-smoke`, `docs`, CodeRabbit, Devin Review) passed on
the same head. Only `gpu-cuda`/`gpu-wgpu` (which this round's changes do
not touch) and the unversioned Windows leg were still completing when this
was written, consistent with every prior round's timing. The one local
failure this round, `test_does_not_corrupt_a_hard_linked_sibling` in a
full-suite run on this session's own machine, reproduced clean in
isolation immediately after and is not attributable to this round's
changes — the same class of local flake recorded in §10.6 — and the same
test already passed for real on every green Linux/Windows/macOS CI leg
above. `PR23-F41` and `PR23-F42` fixed with regression tests proven against
pre-fix source; the re-raised ancestor-symlink question declined, extending
`PR23-F34`'s ledger entry to a second function; `PR23-F39` closed at a
smaller, honestly-documented scope than first attempted. No new D1; no
verdict, tolerance, or measured value changed; no regression to the
published EXP-001 record; the real 172-record repository manifest still
verifies.

---

## 17. Round 10 — Copilot and CodeRabbit review of head `f370a29`

**Trigger:** Round 9 correction cycle's final head (`c02e1d7`, itself
superseded by the docs-only `f370a29`) was reviewed again: Copilot (review
`5302275273`, 6 open findings) and CodeRabbit (review `5301538265`, 3
actionable comments). Every required CI check was green on `f370a29`
before this round started (`gh pr view 23`: `gpu-cuda`, `gpu-wgpu`,
`parity`/`detect_corpus`, `python` lint/governance/docs/security/all nine
`test` legs, `rust` fmt/clippy/clippy-strict/test-strict/audit/bench-smoke/
docs/all three `test` legs, `Snyk Code`, `Secret Scan`, `reproduce`,
CodeRabbit, Devin Review — `Sourcery` skipped, over its diff-size limit as
every prior round).

### 17.1 Five carried findings, re-affirmed with no code change

Each re-derived directly against the current source, not taken on the
finding's word:

- **"Ancestor symlink replacement bypasses no-follow path protection"**
  (Copilot, High, comment `4090442972`, citing `tools/reproduce.py:211`,
  `376`, `443` — the unchanged `_dir_relative_open`/`_open_parent_dir_fd`
  pair). Identical to the finding declined at §14.2 and re-affirmed at
  §16; no line cited has changed since. Same disposition: the immediate
  parent is pinned, every deeper ancestor is not, by a documented,
  previously-declined design choice (disproportionate engineering cost
  against a threat already requiring this module's assumed local-write
  access). No new evidence; no code change.
- **"Reject symlinked ancestor components before resolving output roots"**
  (Copilot, High, comment `4090809725`, citing
  `exp001_e4_analysis.py:1112` — `_reject_configured_root_symlink`). The
  same "immediate component only" limitation as the item above, applied to
  this module's own configured-root check; already declined twice on the
  record (§16, extending `PR23-F34`'s ledger entry to this function) with
  the identical rationale documented in the function's own docstring
  (lines 1089–1103, unchanged this round). No new evidence; no code
  change.
- **"Hard links allow manifest writes to overwrite frozen reports"**
  (Copilot, High, comment `4090442919`, citing
  `exp001_e4_analysis.py:1237` — `_checked_manifest_destination`). The
  description ("the subsequent `O_TRUNC` write modifies the linked frozen
  report") does not match the current implementation: `write_report_manifest`
  (line 1033) writes exclusively through `tools.reproduce.write_no_follow`,
  which — since the `PR23-F37` fix (§14.1) — never opens the destination
  path with `O_TRUNC` at all. It creates a fresh, `O_EXCL`-created sibling
  inode and swaps it into place with `os.replace`, which repoints only the
  destination's own directory entry; whatever else that entry's old inode
  was linked to is never opened or touched. This is the same stale
  hard-link thread already re-confirmed fixed at §15.4 — Copilot's own
  review body lists `PR23-F37`'s companion finding as "Resolved since last
  review" in the same review that re-lists this one as still open,
  consistent with the thread-tracking lag already documented there. No new
  evidence; no code change.
- **"Manifest verification accepts symlinked files"** (Copilot, High,
  comment `4084668748`, unchanged since Round 1, GitHub-marked outdated).
  Same stale Round 1 thread as §12.1/§13.3/§14.3/§15.5. `_load_artefact`
  (line 189) calls `tools.reproduce.verify_manifest` directly — the exact
  hardened, no-follow validator this finding claims is bypassed. No new
  evidence; no code change.
- **"Mixed aborts can incorrectly produce a CONFIRMED verdict"** (Copilot,
  `exp001_e4_analysis.py:361`/`369` — `_tolerance_verdict`). The same
  finding investigated in depth and declined with the maintainer's direct
  confirmation at §15.3: the code matches pre-registration §8/§10's
  literal text, and the scenario requires more total cases than a
  hypothesis's fixed-cardinality registered denominator, which no
  currently-committed EXP-001 artefact has. No new evidence presented this
  round; declined again on the same record.

### 17.2 `f370a29-F1` (D3) — the manifest self-exclusion filter compared
filenames, not file identity, missing the case-insensitive-but-preserving
case (macOS default)

*Copilot, "Fix case-insensitive manifest alias handling on macOS" (New,
Medium, comment `4091859763`, `tests/test_reproduce.py:163`) and
CodeRabbit (actionable, comment `4091290011`, `tools/reproduce.py:846–850`
— the same gap in `append_manifest`'s and `verify_manifest`'s matching
filter at line ~937).*

**Valid, confirmed by tracing both filters against the actual filesystem
semantics `os.path.normcase` provides.** `PR23-F42` (§16) fixed the
self-exclusion filter's cross-platform correctness for Windows, where
`os.path.normcase` case-folds. It did not fix macOS: HFS+/APFS in their
default configuration are case-insensitive *and* case-preserving, so
`MANIFEST.JSON` and `manifest.json` name the same file there — but
`os.path.normcase` is the identity function on every POSIX platform,
Linux and macOS alike, so the string comparison the filter used does not
know that. A `--manifest-path` differing only in case from the file
`glob` actually returns (in its stored casing) fails to self-exclude on
macOS specifically: `append_manifest` then re-adds the manifest as an
"unmanifested" candidate to its own record; `verify_manifest` would reject
it as unexpected. `tests/test_reproduce.py`'s own
`test_append_manifest_self_excludes_case_insensitively` (corrected at
`c02e1d7`, §16, to probe the real filesystem before asserting) would fail
this exact assertion on real macOS CI, which is why Copilot's finding
lands on that test rather than only the production code — the test's own
probe (`differently_cased.exists()`) does not skip on a case-insensitive
filesystem, so it would proceed into the bug.

**Fix.** Both filters (`append_manifest` and `verify_manifest`) now
compare file identity via `lstat()` + `os.path.samestat`, not filenames.
This is filesystem-identity-based rather than string-based, so it is
correct on every platform (Windows, case-sensitive Linux, case-insensitive
macOS) without a per-platform case rule, and — because both sides use
`lstat`, never `stat` — a symlinked candidate is compared by its own
identity, not its link target's, so it is never mistaken for the manifest
and still reaches `_reject_non_regular`'s symlink rejection afterward
(CodeRabbit's own note: "Keep symlink candidates in the rejection path").
No test change was required: the existing, already-corrected
case-insensitivity test now exercises the fixed code path directly and
passes without modification, on every platform its own probe does not
skip.

### 17.3 `f370a29-F2` (D4) — the descriptor-count regression test proved
only write success, not descriptor non-leak, even on a platform where a
leak is reachable

*CodeRabbit (actionable, comment `4091289945`,
`tests/test_reproduce.py:1008–1027` —
`test_repeated_writes_do_not_exhaust_file_descriptors`).*

**Valid — and an accurate description of a limitation this test's own
docstring and §16.3 already stated plainly.** The test (added in the
Round 9 correction cycle, §16, as the final, verified-sound response to
two prior mechanism-spying attempts that broke CI) writes 300 files and
asserts only that each write succeeds. As documented at the time, this
"cannot distinguish 'no leak' from 'a leak too small to hit the descriptor
limit in 300 iterations.'" CodeRabbit's finding makes that limitation
concrete: a real one-descriptor-per-call leak would not exhaust a typical
Linux CI runner's default descriptor limit within 300 iterations, so the
existing assertions alone could pass on a genuine (small) leak.

**Fix.** Where a descriptor-count directory is available
(`/proc/self/fd` on Linux, `/dev/fd` on macOS; neither exists on
Windows), the test now counts this process's own open descriptors before
and after the 300 writes and asserts the count returns to within a small
tolerance — a real per-call leak would fail this assertion long before
reaching the platform ulimit. The count check is skipped, not assumed,
wherever neither directory exists, so the test degrades to its prior,
still-correct assertions on Windows rather than failing to run or
asserting something this platform cannot support — the same
"verify, don't assume" discipline this test's own docstring already
credits to the correction cycle that produced it. This is a test-only
change with no production code path affected; it does not reintroduce the
mechanism-spying pattern (`os.open`/`os.close` monkeypatching) that broke
CI twice during that cycle — it counts real, unpatched OS state via
directory listing, the same category of proof (measured outcome, not
mocked mechanism) the surviving test already used.

### 17.4 Declined — "Use a descriptor-relative rename for the final
replacement"

*CodeRabbit (actionable, comment `4091290002`, `tools/reproduce.py:531–567`
— `write_no_follow`'s final `os.replace(tmp_path, path)`).* The finding
describes a real, general POSIX race (a parent directory replaced with a
symlink between the temporary file's creation and the final rename, which
re-resolves `path`'s parent by string) and suggests closing it with
`os.rename(..., src_dir_fd=parent_fd, dst_dir_fd=parent_fd)` whenever
`parent_fd is not None`.

**Declined, not implemented.** This is the exact residual `PR23-F39`
scoped down to when the Round 9 correction cycle closed it (§15.2, §16):
that fix originally attempted precisely this — a `dir_fd`-relative final
rename, reusing the pinned parent descriptor — and shipped it gated only
on `parent_fd is not None`, the same condition CodeRabbit's suggestion
uses. It broke required Linux CI twice in a row (`949e5e1`, then
`b9e3239`'s own replacement test), the first time because
`os.replace not in os.supports_dir_fd` on real Ubuntu/Python 3.12 even
though `os.open` supports `dir_fd` there — an unverified assumption about
one function's platform support that this session's Windows machine
cannot check, disproved only by real CI. `os.rename` and `os.replace` are
the same underlying rename operation on POSIX, gated by the same
`dir_fd` support; nothing in this round's evidence shows `os.rename`'s
`dir_fd` support differs from `os.replace`'s on the platform that
falsified the assumption last time, and CodeRabbit's suggested diff, like
the reverted attempt, does not gate on a runtime
`os.rename in os.supports_dir_fd` check before using it — the exact
verification step every *other* `dir_fd`-relative call in this module
performs first (`os.open` at `_open_parent_dir_fd`, `os.unlink` at the
`PR23-F41` cleanup path). Re-attempting the identical unverified pattern
that already cost two required-CI failures in this same function, on the
word of a reviewer that cannot execute Python on this repository's actual
CI platforms either, repeats exactly the mistake §16.1 draws its lesson
from rather than applying it. The residual this closes over — a parent
symlink-swap race between temp-file creation and the final rename — still
requires the same local-write access this module's whole containment
scheme assumes throughout (the same governing fact behind every other
declined "pin every ancestor/every step" finding in this audit: §14.2,
§16's `_reject_configured_root_symlink` extension, and §17.1 above).

**Declined-findings ledger entry (extending §6/§14.2/§16):** "Make the
final `os.replace` in `write_no_follow` `dir_fd`-relative via
`os.rename(..., src_dir_fd=, dst_dir_fd=)`" — raised by CodeRabbit
(Round 10); not a false positive (the general POSIX race is real); declined
because this exact mechanism, gated the same way, already broke required
Linux CI twice this PR (`PR23-F39`'s correction cycle, §16) on an
assumption about `dir_fd` platform support this session cannot verify
locally, and the suggested code does not add the runtime capability check
that would make a re-attempt safe to ship without CI as the first
verification. If a future round wants this closed, the runtime
`os.rename in os.supports_dir_fd` gate (with the existing plain
`os.replace(tmp_path, path)` fallback) is the way to attempt it again —
verified by a real green Linux CI run before being called closed, not
asserted from this platform.

### 17.5 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  100 passed, 2 skipped
.venv\Scripts\python -m pytest tests/test_exp001_driver.py tests/test_paper_wiring.py tests/test_wp001_baseline.py -q
  280 passed, 6 skipped
.venv\Scripts\python -m ruff check tools/reproduce.py tests/test_reproduce.py
  All checks passed!
.venv\Scripts\python -m ruff format --check tools/reproduce.py tests/test_reproduce.py
  2 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m mypy tests/test_reproduce.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
```

Also re-verified directly against the real repository manifest:
`reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error
under the new identity-based self-exclusion filter.

**No regression to the published EXP-001 record.** Neither fix touches
`_tolerance_verdict`, any adjudication path, or any write this analysis
performs for its own outputs — both changes are confined to
`tools/reproduce.py`'s manifest self-exclusion filters and a test-only
strengthening; `_load_artefact` and `write_report_manifest`'s call shapes
are unchanged.

**Security gates.** No dependency files changed this round — no Snyk Open
Source / `cargo audit` / `pip-audit` run required. Local Snyk Code was not
re-run this round (no new call sites reaching a path-write operation
outside the already-accepted, previously-documented taint class at
§14.4/§15.6); CI's `Snyk Code`/`Secret Scan` remain the authoritative
gates and are re-requested on this round's push per standard practice,
consistent with the repository's Coding Standards §6 mandatory controls.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN. One D3 and
one D4 finding fixed, both confirmed by direct tracing against current
source and neither reachable against any already-published EXP-001
artefact or verdict. Five carried findings re-affirmed with no new
evidence and no code change (four already-declined threads restated
identically, one stale Round-1 thread). One new finding declined on the
record with rationale directly citing this PR's own prior two-failure
history in the identical code path, rather than re-attempted on an
unverified assumption a third time. No new D1; no verdict, tolerance, or
measured value changed; no regression to the published EXP-001 record;
the real 172-record repository manifest still verifies. CodeRabbit and
Copilot are re-requested on this round's push per standard practice.

## 18. Round 11 — Copilot review of head `3dfe299`; maintainer-directed closure sweep

**Trigger:** Round 10's fix commit (`3dfe299`) was reviewed again by
Copilot (review `5303501159`: 8 open findings — 2 new, 6 carried).
CodeRabbit's latest review (`5301538265`) predates this head; of its 3
actionable comments, 2 were fixed at `3dfe299` (`f370a29-F1`/`F2`, §17.2–
§17.3, both marked "Addressed" by CodeRabbit itself) and 1 was declined
with a recorded re-attempt condition (§17.4). **The maintainer directed
this round to validate every open finding and fix all of them** — an
explicit decision that supplies exactly the missing authorization §15.3
and §17.4 each said a change of course would require. Every finding was
still re-derived against current source first; two carried findings remain
declined below because their governing facts (a frozen pre-registration
matched literally, with the maintainer's prior direct confirmation; and a
stale thread describing code that no longer exists) are not changed by a
"fix everything" instruction, and "fixing" them would mean editing frozen,
registered adjudication logic or re-fixing already-fixed code.

### 18.1 `3dfe299-F1` (D3) — a hard-linked alias of the manifest evaded the inventory the identity-based self-exclusion was protecting

*Copilot, "Hard-linked manifest aliases evade inventory validation" (New,
High, comment `4092840356`, `tools/reproduce.py:860`).*

**Valid — a direct consequence of the §17.2 fix, confirmed by tracing
both filters.** `f370a29-F1` replaced the name-based self-exclusion with
`lstat()` + `os.path.samestat`, which compares device/inode identity — and
a *hard link* to the manifest is inode-identical by construction. A local
`os.link(manifest.json, rogue.json)` therefore made **both** directory
entries pass `samestat` against the manifest's `lstat`, so `rogue.json`
was silently filtered out of `candidates` before `actual`/`unexpected`
were computed: `verify_manifest` would accept a run directory containing
an unmanifested JSON name (never surfacing it as "unmanifested"), and
`append_manifest` would silently skip it — the exact
"silently dropped from the inventory" failure mode `verify_manifest`'s own
docstring promises can never happen. Same fail-closed contract violation
class as `PR23-F30`'s resolved-comparison bug (§12.2), reintroduced
through the identity comparison that fixed the macOS case gap.

**Fix.** A governed manifest legitimately has exactly **one** directory
entry, so both filters now refuse a manifest whose `lstat().st_nlink > 1`
outright (`ManifestMismatchError`, naming the link count) before any
exclusion runs. With a link count of one, the single `samestat` match can
only be the manifest's own entry — in whatever casing the filesystem
stores it — never an alias, so the macOS case-insensitivity fix survives
intact while the alias evasion is closed fail-closed rather than
"distinguished and silently handled". Symlinked candidates are untouched:
compared by their own `lstat` identity as before, they still reach
`_reject_non_regular`'s rejection.

**Regression tests.**
`test_append_manifest_fails_closed_on_a_hard_linked_manifest_alias` and
`test_verify_manifest_fails_closed_on_a_hard_linked_manifest_alias` create
the exact `os.link` alias from the finding and assert both functions raise
(`match="hard links"`) instead of silently excluding it. Both run for real
on this Windows host (NTFS hard links, same mechanism as the existing
`test_does_not_corrupt_a_hard_linked_sibling`) and on every POSIX CI leg.

### 18.2 `3dfe299-F2` (D4) — the case-insensitivity regression test's docstring described the mechanism its own fix replaced

*Copilot, "Test docstring describes obsolete normcase implementation"
(New, Low, comment `4092840398`, `tests/test_reproduce.py:135`).*

**Valid.** `test_append_manifest_self_excludes_case_insensitively`'s
docstring still said the production filter compares via
`os.path.normcase` — the exact implementation `f370a29-F1` replaced.
Rewritten to describe the current `lstat()` + `os.path.samestat` identity
comparison, why the `normcase` approach failed on macOS, and the new
hard-link link-count refusal (§18.1) the identity comparison now pairs
with. Docstring-only; no assertion changed.

### 18.3 Closed at maintainer direction — the `dir_fd`-relative final rename, re-attempted exactly as §17.4's own prescription specified

*CodeRabbit, actionable comment `4091290002` (`write_no_follow`'s final
`os.replace(tmp_path, path)`), declined at §17.4 with the recorded
condition: "the runtime `os.rename in os.supports_dir_fd` gate (with the
existing plain `os.replace(tmp_path, path)` fallback) is the way to
attempt it again — verified by a real green Linux CI run before being
called closed."*

Implemented precisely that way, at maintainer direction: the final swap is
now `os.rename(tmp_path.name, path.name, src_dir_fd=parent_fd,
dst_dir_fd=parent_fd)` **iff** `parent_fd is not None and os.rename in
os.supports_dir_fd` — the runtime capability check whose absence broke
required Linux CI twice at `PR23-F39` (`os.replace not in
os.supports_dir_fd` on real Ubuntu/Python 3.12), and the same check every
other `dir_fd`-relative call in this module already performs (`os.open`,
`os.unlink`). Everywhere else — including every Windows path, where
`os.supports_dir_fd` is empty — the existing plain `os.replace` fallback
is unchanged, so a wrong assumption about any platform's support degrades
to the prior, still-correct-if-narrower behavior rather than failing.
POSIX `rename(2)` atomically replaces an existing destination, so the
overwrite semantics of the fallback are preserved on the platforms that
take the new branch. No mechanism-spying test was added (monkeypatching
`os.rename` would defeat the very `os.supports_dir_fd` identity check the
fix depends on — the trap §16 documented); the existing outcome tests
(`test_writes_a_new_file`, `test_truncates_an_existing_file`,
`test_refuses_to_write_through_a_symlinked_destination`,
`test_does_not_corrupt_a_hard_linked_sibling`, the descriptor-count test)
all exercise the new branch on the Linux/macOS CI legs. **Per §17.4's own
condition, this is called closed only if this round's push comes back with
the required Linux CI legs green; a red CI run reverts it as `PR23-F39`'s
was.**

### 18.4 Closed at maintainer direction — every-component symlink walk for the configured E4 roots

*Copilot, "Reject symlinked ancestor components before resolving output
roots" (High, carried, comment `4090809725`,
`exp001_e4_analysis.py:1116`), previously declined at §16/§17.1 as
disproportionate absent an explicit decision.*

The maintainer's direction to fix all findings is that explicit decision.
`_reject_configured_root_symlink` now takes the trusted checkout anchor
and the configured root's *relative* path, and walks **every** component
below the anchor no-follow (`is_symlink()` per component), refusing the
root if any component — not only the final one — is a symlink. This
closes the finding's concrete scenario: an ancestor such as
`DOCS/test_and_benchmark_results` replaced with a symlink to the frozen
record tree, which left the final component's own `is_symlink()` false
(the gitignored `OUTPUT_ROOT` need not even exist) while `.resolve()`
transparently followed the ancestor. The anchor itself and everything
above it remain deliberately unchecked — a checkout legitimately reached
through a symlinked home directory or mount point must keep working, and
the checkout anchor is this module's trusted input. This is a check-time
walk, not a descriptor-pinned open: a component swapped *between* this
check and the subsequent `.resolve()` remains within the documented,
still-declined local-write race threat model (§14.2 — see §18.5).
**Regression tests:**
`test_allowed_output_roots_refuses_a_symlinked_ancestor_of_the_output_root`
(covering both `allowed_output_roots` and
`allowed_generated_output_dirs`) and
`test_allowed_output_roots_refuses_a_symlinked_ancestor_of_the_record_root`,
both running for real on this host and on the POSIX CI legs. This module
is analysis *infrastructure* (root-set construction), not adjudication
logic: no verdict path is touched, and the record re-run in §18.6 confirms
byte-identical outputs. `PR23-F34`'s declined-findings ledger entry is
superseded for this occurrence by this closure; the `tools/reproduce.py`
occurrence it originally governed remains declined (§18.5).

### 18.5 Re-affirmed, with the reasons the maintainer's direction does not change them

Each re-derived against current source this round, not carried on
momentum:

- **"Ancestor symlink replacement bypasses no-follow path protection"**
  (Copilot, High, comment `4090442972`, `tools/reproduce.py` —
  `_dir_relative_open`/`_open_parent_dir_fd`). This is the *mid-flight
  race* variant — pinning every ancestor as a descriptor chain during
  I/O — not §18.4's check-time walk. The finding's own text offers the
  alternative this module already implements: "or narrow the public
  guarantee and reject this threat model explicitly", which
  `_dir_relative_open`'s docstring does at length (immediate parent
  pinned; deeper ancestors trusted as part of the governed-checkout
  threat model; a race there requires the same local-write access that
  defeats the scheme wholesale). Re-engineering the whole I/O layer into
  an `openat`-walk from a trusted descriptor, on a Windows host that
  cannot execute any of it, in the same PR where the last two unverifiable
  `dir_fd` changes broke required CI, is the one place this round holds
  the line even under a "fix everything" instruction — the risk-reward is
  exactly the §16 lesson. §18.3's gated rename narrows the residual
  further (the final swap no longer re-resolves the parent by string where
  the platform supports the gate).
- **"Mixed aborts can incorrectly produce a CONFIRMED verdict"** (Copilot,
  High, comment `4090613365`, `_tolerance_verdict`). Unchanged from
  §15.3's in-depth investigation: the code implements pre-registration
  §8/§10's literal text ("CONFIRMED iff … the non-aborted count is exactly
  the full denominator"); the scenario requires more total cases than a
  fixed-cardinality registered set can produce; no committed artefact has
  it; and the maintainer *personally confirmed* the decline. "Fixing" it
  would edit frozen, registered adjudication logic of a
  maintainer-accepted report — a D1-class governance violation dressed as
  a review response. Remains declined; re-openable only against the
  `EXP-001-r1` analysis code as §15.3 already provides.
- **"Hard links allow manifest writes to overwrite frozen reports"**
  (Copilot, High, comment `4090442919`). Stale: describes an `O_TRUNC`
  in-place write that `PR23-F37` (§14.1) removed; `write_report_manifest`
  writes exclusively through `write_no_follow`'s create-new-inode-then-
  swap path. Same thread-tracking lag as §15.4/§17.1. Nothing to fix.
- **"Manifest verification accepts symlinked files"** (Copilot, High,
  comment `4084668748`, GitHub-marked outdated). The stale Round 1 thread,
  sixth consecutive re-listing (§12.1/§13.3/§14.3/§15.5/§17.1);
  `_load_artefact` calls the hardened `verify_manifest` directly. Nothing
  to fix.
- **"Fix case-insensitive manifest alias handling on macOS"** (Copilot,
  Medium, comment `4091859763`). Fixed at `3dfe299` (`f370a29-F1`,
  §17.2); the review that listed it "open" also listed the fix commit's
  own two new findings, consistent with the established thread-lag
  pattern. §18.1's link-count guard completes the identity-comparison
  design it introduced. Nothing further to fix.

### 18.6 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  104 passed, 2 skipped (+4 new regression tests, all running for real on
  this host: 2 hard-link alias, 2 ancestor-symlink walk)
.venv\Scripts\python -m pytest tests/test_exp001_driver.py tests/test_paper_wiring.py tests/test_wp001_baseline.py -q
  280 passed, 6 skipped (4 release-workflow shell tests require the
  documented AGENTS.md Git-Bash-before-WSL-relay PATH fix on this
  workstation; 1 stale-basetemp WinError-32 fixture error cleared by
  removing .pytest_basetemp per the same AGENTS.md note — both
  pre-existing workstation issues, re-verified green, unrelated to this
  round's changes)
.venv\Scripts\python -m ruff check / ruff format --check (4 touched files)
  All checks passed! / 4 files already formatted
.venv\Scripts\python -m mypy --strict tools/reproduce.py exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m mypy tests/test_reproduce.py tests/test_exp001_e4_analysis.py
  Success: no issues found in 2 source files
.venv\Scripts\python -m bandit -r tools/reproduce.py
  No issues identified
snyk code test tools/            → reproduce.py 5 × LOW Path Traversal
  (+1 over §15.6's 4: the new gated os.rename call site, same
  already-accepted structural taint class — path-derived arguments inside
  the hardened write path itself; §14.4/§15.6)
snyk code test .../analysis/     → 1 × LOW, unchanged from every prior round
snyk code test tests/            → 0 issues
```

Also re-verified directly against the real repository manifest:
`reproduce.verify_manifest(reproduce.DEFAULT_RESULTS_DIR,
reproduce.DEFAULT_MANIFEST)` still returns all 172 records with no error
under the link-count guard (every real manifest has `st_nlink == 1`).

**No regression to the published EXP-001 record**, re-verified by
re-running `run_analysis` end-to-end to a scratch destination with the
committed provenance stamp: H1/H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`
(the registered D1 unchanged), and the regenerated `report-manifest.json`
compares equal to the committed record.

**Security gates.** No dependency files changed — no Snyk Open Source /
`cargo audit` / `pip-audit` run required. Local Snyk Code re-run this
round (above) because `write_no_follow` gained a new filesystem call
site; the single new finding is the documented accepted class. CI's
`Snyk Code`/`Secret Scan` remain the authoritative gates on this push.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN locally;
§18.3's closure is additionally conditional on this push's required Linux
CI legs, per §17.4's own recorded condition. One new D3 and one new D4
fixed with regression tests; two previously-declined findings closed at
explicit maintainer direction, each by the exact mechanism the prior
decline recorded as the safe path; four carried threads re-affirmed
(two stale, one maintainer-confirmed decline on frozen registered logic,
one mid-flight-race variant declined on the unchanged §16 risk lesson).
No new D1; no verdict, tolerance, or measured value changed; the
published EXP-001 record reproduces byte-identically; the real
172-record repository manifest still verifies. CodeRabbit and Copilot
are re-requested on this round's push per standard practice.

## 19. Round 12 — Copilot and CodeRabbit review of head `b69f585`

**Trigger:** Round 11's push was reviewed by Copilot (review
`5306444116`: 5 open findings — 1 new, 4 carried; **all four of Round
11's fixes marked "Resolved since last review"**, including both
maintainer-directed closures) and CodeRabbit (explicitly re-requested;
incremental review finished with **zero** new actionable comments).
**Every required CI check was green on `b69f585`** — including all
ubuntu/macOS `test` legs and `reproduce`, which is the condition §18.3
attached to calling the `dir_fd`-relative final rename closed: **that
closure is now unconditional.** (Sourcery skipped, over its diff-size
limit, as every prior round.)

### 19.1 `b69f585-F1` (D3) — a symlink planted at the canonical manifest name escaped the record-root destination policy

*Copilot, "Symlinked manifest path bypasses record-root destination
policy" (New, High, comment `4095288750`,
`exp001_e4_analysis.py:1250` — `_checked_manifest_destination`).*

**Valid, confirmed by tracing the CLI validation chain.**
`_checked_manifest_destination` delegates to `_checked_destination`,
which applies containment to `Path(path).resolve()` — and `.resolve()`
follows a trailing symlink. A symlink planted at the canonical name,
`record_root/report-manifest.json -> output_root/other.json`, therefore
resolved into the *permitted* generated-output root, so containment
passed; `inside_record_root` was then computed on the resolved target,
which is *not* inside the record root, so the canonical-name rule —
the very rule protecting the record root — never fired. `main()` passes
the accepted resolved path onward, and `write_no_follow` sees only the
plain resolved target, writes it, and overwrites an unrelated allowed
output while the record root keeps a symlink where its registered
provenance file belongs. The `PR23-F38` collision guard catches only the
two known generated filenames, not an arbitrary redirect target. Same
check-the-resolved-path-only class as `PR23-F34`/§18.4, at the one
remaining call site that still resolved before checking. Requires local
symlink creation in the checkout (D3, same reachability class as every
prior CLI-boundary symlink finding); no committed artefact or published
verdict is affected.

**Fix.** `_checked_manifest_destination` now refuses a requested
destination that is itself a symbolic link — checked no-follow, *before*
resolution, the same check-before-resolve boundary
`_reject_configured_root_symlink` already establishes for the configured
roots. A symlink swapped in after the check remains within the
documented, declined local-write race threat model (§14.2), and the
eventual write still passes through `write_no_follow`'s own no-follow
open.

**Regression test.**
`test_checked_manifest_destination_rejects_a_symlinked_destination`
builds the finding's exact scenario (canonical name in the record root
symlinked to an unrelated file in the permitted output root) and asserts
the refusal plus the target's untouched bytes. **Proved against the
pre-fix source** (production module stashed to `b69f585`'s committed
state): the test then fails with `DID NOT RAISE AnalysisError`,
confirming the gap was real; passes post-fix.

### 19.2 Carried findings — re-affirmed by reference

The four remaining open threads are byte-for-byte the ones §18.5
re-derived and dispositioned this same day: the mid-flight
ancestor-race variant in `tools/reproduce.py` (documented threat-model
boundary, the finding's own offered alternative), the mixed-abort
verdict question (frozen pre-registration matched literally, maintainer
previously confirmed the decline), and the two stale threads (hard-link
overwrite removed at `PR23-F37`; symlinked verification fixed in
Round 1's own remediation). No new evidence was presented in this
review; §18.5's dispositions stand unchanged.

### 19.3 Verification

```text
.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_exp001_e4_analysis.py -q
  105 passed, 2 skipped (+1: the new symlinked-destination regression
  test, running for real on this host)
.venv\Scripts\python -m ruff check / ruff format --check (2 touched files)
  All checks passed! / 2 files already formatted
.venv\Scripts\python -m mypy --strict exp001_e4_analysis.py
  Success: no issues found in 1 source file
.venv\Scripts\python -m mypy tests/test_exp001_e4_analysis.py
  Success: no issues found in 1 source file
snyk code test .../analysis/  → 1 × LOW (line 1207), count and finding
  unchanged from every prior round — no new issue from this fix
governance checkers (check_dv_register_gates, check_skipif_probes,
  check_global_session_registration)  → all pass
```

**No regression to the published EXP-001 record**, re-verified by
re-running `run_analysis` end-to-end to a scratch destination with the
committed provenance stamp: H1/H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`
(the registered D1 unchanged), regenerated `report-manifest.json` equal
to the committed record. The fix sits at the CLI boundary
(`_checked_manifest_destination`); `run_analysis` and every adjudication
path are untouched.

**Security gates.** No dependency files changed — no Snyk Open Source /
`cargo audit` / `pip-audit` run required. Local Snyk Code re-run on the
modified module (above), unchanged. CI's `Snyk Code`/`Secret Scan`
remain the authoritative gates on this push.

**Delta re-audit date:** 2026-09-24 UTC — **Result:** CLEAN locally.
One new D3 fixed with a regression test proven to fail pre-fix; §18.3's
`dir_fd`-rename closure confirmed unconditional by `b69f585`'s fully
green required CI; CodeRabbit raised nothing on the Round 11 changes;
four carried threads re-affirmed by reference to §18.5 with no new
evidence. No new D1; no verdict, tolerance, or measured value changed;
the published EXP-001 record reproduces byte-identically. CodeRabbit and
Copilot are re-requested on this round's push per standard practice.

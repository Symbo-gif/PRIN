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

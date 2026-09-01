# PRIN Executive Testing and CI Audit Governance and Methodology

**Status:** Normative. This document establishes the governance, scope,
methodology, findings classification, remediation protocols, and reporting
requirements for **Executive Testing and CI Audit (ETCA) Sessions** in the
PRIN project.

**Relationship to existing governance:** This document extends — and never
overrides — the [Executive Audit Governance and Methodology](Executive_Audit_Governance_and_Methodology.md),
[Executive Mathematical Audit Governance and Methodology](Executive_Mathematical_Audit_Governance_and_Methodology.md),
[Executive Documentation Audit Governance and Methodology](Executive_Documentation_Audit_Governance_and_Methodology.md),
[Development Workflow and Audit Standards](Development_Workflow_and_Audit_Standards.md),
[Testing Standards](Testing_Standards.md),
[Benchmarking and Reproducibility Standards](Benchmarking_and_Reproducibility_Standards.md),
[Coding Standards](Coding_Standards.md),
[Versioning and Release Standards](Versioning_and_Release_Standards.md), and
[Official Project Plan](../PRIN_Project_Plan.md). It is registered by Project
Plan amendment #42, following the same "global session, outside the planned
sequence" registration precedent established for Executive Audit (EA) sessions
by amendment #15 and Executive Mathematical Audit (EMA) sessions by
amendment #23.

---

## 1. Purpose and Scope

An **Executive Audit Session** (EA) verifies the full project across 10
dimensions (E1–E10), of which **E3 (Test Suite & Parity Corpus)** and
**E9 (CI/CD & Build Infrastructure)** are two dimensions among many — sampled,
not exhausted, because an EA session must also cover mathematics, architecture,
security, documentation, evidence, governance, benchmarks, and roadmap in the
same pass. An **Executive Mathematical Audit** (EMA) independently re-derives
mathematical claims; an **Executive Documentation Audit** (EDA) systematically
verifies documentation artefacts. None of the three is purpose-built for the
deep, systematic inspection of **test-suite health and CI-gate effectiveness**
that a large phase of test-heavy work packages produces.

An **Executive Testing and CI Audit (ETCA) Session** fills that gap. It is a
project-level audit dedicated to **systematic verification that the test suite
and the CI/CD gate machinery actually do their job** — that every mandated
test layer exists and passes, that coverage and parity obligations are met,
that governed skips and quarantines are properly tracked, that every CI
workflow runs and *fails on the violation it is meant to catch* rather than
sitting green while inert, and that the local gate a session reproduces is
equivalent to the CI gate that is the authoritative merge control. ETCA
sessions:

1. Verify that every test layer the [Testing Standards](Testing_Standards.md)
   §2 mandates (Rust unit, `proptest` property, kernel equivalence, Python
   API, parity/differential, `gradcheck`, GPU integration, reproducibility,
   benchmarks) **exists for the audited scope and passes**, with command
   evidence — not a recollected count.
2. Detect **test-suite drift** — unexplained skips, `xfail` creep, weakened
   assertions or loosened tolerances without the required PR sign-off and
   Parity Report entry, quarantined flaky tests with no tracked issue,
   test-in-tandem gaps (source commits without their tests), coverage
   regressions, and reference/fixture dependencies that pass locally but fail
   in a clean environment.
3. Detect **CI-gate drift** — a workflow that no longer runs, a required gate
   step that has been silently disabled or reordered behind an earlier
   failing step, a gate whose command as written does not fail on the
   condition it is supposed to catch, a `[RETROACTIVE]`/hotfix change to a
   workflow that was never retro-audited, branch-protection required-check
   sets that no longer match the workflow set, and benchmark-regression gates
   that record baselines but never compare against them.
4. Verify **push/CI cadence compliance** (Development Workflow §3 "Push and
   CI cadence", amendment #28) — that each cycle's S4 commit was pushed, that
   CI ran and went green on the pushed S1–S4 range, and that the current
   `origin/main` CI state is actually green (not merely "the last session
   said the local gate passed").
5. **Do not replace** EA sessions' E3/E9 dimensions or the per-cycle S2/S3/S4
   sessions' own test and gate obligations. ETCA is an additional,
   independent verification layer applied at a coarser granularity —
   typically mid-phase or at phase boundaries — when the volume of
   test and CI change produced by a string of work packages warrants a
   dedicated, focused audit.

### 1.1 When an ETCA session is warranted

An ETCA session is warranted when:

1. **Mid-phase audit point:** A phase has produced a large volume of test
   and/or CI change across multiple work packages (typically 5+ WPs, 50+
   commits, or a net test-count change of 25%+), and a dedicated
   test/CI-quality check would provide value before the phase closes.
2. **Phase boundary:** At phase close, complementing the EA session's E3/E9
   dimensions with a deeper, test-and-CI-focused audit.
3. **CI-health trigger:** `origin/main` CI has been red or partially red for
   more than one push, or a workflow/gate change landed as a hotfix and owes
   a retro-audit.
4. **Maintainer discretion:** The maintainer requests a test/CI audit at any
   point — e.g. after a strict-port campaign, a large acceptance-suite
   addition, a CI-runner topology change, or when local-gate/CI divergence is
   suspected.

This first ETCA session (ETCA-001) is triggered by conditions 1 and 3: Phase 6
has produced eight completed work packages (WP-033 through WP-036D) plus the
WP-036C acceptance-suite port, ~120 commits since EA-006, a net Python-test
change from ~1,770 to ~2,970 collected tests (the largest single test delta in
project history), ~2,000 new lines of first-party Rust, and a CI/runner
topology that has changed three times; and `origin/main` CI is red across
`python` (all matrix legs), `repro`, and the `rust` self-hosted Windows leg.

---

## 2. Audit Dimensions

An ETCA session examines the test suite and CI machinery across 8 dimensions:

| ID | Dimension | Assessment Scope |
|---|---|---|
| **T1** | **Test Suite Inventory & Health** | Test counts by layer (Rust unit/`proptest`, Python API/acceptance, parity) reconcile with the latest PSR metric trends; the full default gate (`cargo test --workspace`, `pytest -m "not slow and not gpu"`) passes with command evidence; `strict-checks` Rust tests pass; no `xfail`; every failing or erroring test is a recorded finding. |
| **T2** | **Test-in-Tandem & Coverage Compliance** | Every S1 commit in the audited scope touching `crates/**` or `python/**` source has corresponding test changes in the same commit range (Testing Standards §1.2); new/changed code coverage ≥95% and non-decreasing overall (Testing Standards §4); coverage-tooling availability and any coverage-measurement deferral is tracked. |
| **T3** | **Specialized Test Layers** | For every primitive/bridge/kernel/invariant the audited scope touches: `proptest` invariants for touched invariants, `torch.autograd.gradcheck` (float64) for touched `autograd.Function` bridges, kernel-equivalence tests for touched kernels, explicit `Seed`-type seeding for stochastic tests (Testing Standards §1.5, §2). Missing required layers are findings. |
| **T4** | **Parity & Differential Testing** | Golden-corpus currency; the exhaustive differential parity suite (`parity/`, 504/510 cases) present and passing; hypothesis fuzzing intact; PRINet 3.0 reference-availability disposition stated per new primitive (Development Workflow §3 S1 exit criteria, R15); every tolerance annotation carries a PR note, reviewer sign-off, and a Parity Report entry (Testing Standards §3). |
| **T5** | **Governed Skips, Flaky Tests & Quarantine** | Every `skip`/`skipif`/`importorskip` maps to a reference guard, a DV-register item, or an approved plan amendment, with a reason string naming its governing item; the central skip layer (`tests/conftest.py`) is auditable in one place and does not edit ported test text; every quarantined flaky test has a linked issue/DV item and dated maintainer approval (Testing Standards §1.4); no assertion was weakened to make a gate green (Testing Standards §1.1, §1.4). |
| **T6** | **CI/CD Workflow Coverage & Gate Effectiveness** | Every workflow the [`.github/workflows/README.md`](../../.github/workflows/README.md) inventory names is present and triggered as intended; every mandated gate step (`cargo fmt`/`clippy -D`/`ruff`/`ruff format`/`mypy --strict`/`interrogate`/`bandit`/`cargo audit`/`pip-audit`/`check_deviation_ledger.py`/`check_dv_register_gates.py`/`check_no_python_numerics.py`/Sphinx `-W`/Snyk/Gitleaks) **runs and exits non-zero on a real violation** — verified by reproducing each command's exit code, not by trusting a green check; no required gate is unreachable behind an earlier failing step in the same job; branch-protection required-check sets match the workflow set. |
| **T7** | **Benchmark Regression Gates & Reproducibility Pipeline** | The `criterion` + `pytest-benchmark` regression gates that Testing Standards §2 requires ("fail on >10% slowdown") are implemented as *enforcing* CI steps (a baseline that is only written, never compared, is a finding); `repro.yml` (`tools/reproduce.py --verify-manifest` + `test_reproduce.py`) runs and passes; the "full suite runs nightly and on release tags" obligation (Testing Standards §4) has an actual `schedule:`d workflow or a recorded, dated deferral. |
| **T8** | **Test Evidence, Traceability & Local/CI Gate Equivalence** | PSR metric-trend tables and S2/S3/S4 verification blocks quote *real* command outputs and exit codes (a printed `ERROR:`/nonzero exit reported as "passed" is a finding); the canonical local verification one-liner (`AGENTS.md`) and the CI gate use equivalent commands and produce equivalent results on a clean checkout; `origin/main` CI state is verified live (`gh run list`) and any red/partial/awaiting-runner condition is a finding or an explicitly dispositioned external-infrastructure item. |

---

## 3. Severity Classification

ETCA findings use the same D1–D4 scale as Executive Audits
(`Executive_Audit_Governance_and_Methodology.md` §3), with test-and-CI-specific
definitions:

| Severity | Definition | Required Response |
|---|---|---|
| **D1 — Trajectory Breach** | A test that asserts incorrect behavior (a weakened assertion, a loosened tolerance without governance, an `xfail` masking a real defect), a green CI gate that would not catch the violation it exists to catch on a real regression, a merged/pushed range whose CI never ran and which is known to contain a correctness or security regression, or a parity-corpus/reproducibility guarantee that no longer holds. | Immediate fix required. Freezes progress on the affected subsystem until resolved. |
| **D2 — Subsystem Deviation** | A mandated test layer missing for touched scope; a source change in the audited range without its tests (test-in-tandem breach); a required CI gate command that exits non-zero as written (the gate is red), or that is unreachable behind an earlier failing step; a test that fails in a clean CI environment because of an undeclared local dependency; a quarantined flaky test with no tracked issue. | Fix in the remediation step before the audit session closes. |
| **D3 — Process / Quality Deviation** | A CI workflow that does not run (external infra or misconfiguration) with no wired fallback; a benchmark-regression gate that records but never compares; the nightly full-suite obligation unmet with no dated deferral; an S4 push that never happened; a coverage-measurement gap that is not tracked; a governed skip whose reason string does not name its governing item. | Fix in the remediation step or log with an explicit future WP/DV placeholder and dated disposition. |
| **D4 — Hygiene / Documentation** | A stale workflow comment, a local/CI command-string drift that does not change the pass/fail outcome, a PSR verification-block wording that overstates a genuinely-passing gate, a `tests/README.md` count that is slightly off, or a cosmetic marker inconsistency. | Fix during the remediation / documentation alignment step. |

---

## 4. Executive Testing and CI Audit Workflow Lifecycle

An ETCA Session proceeds through 7 mandatory sequential tasks, mirroring the
EA lifecycle (`Executive_Audit_Governance_and_Methodology.md` §4):

```
Task 1: Governance & Methodology Definition (this document, first session)
   │     or confirmation of existing methodology (subsequent sessions)
   ▼
Task 2: Scope Delineation & Test/CI Inventory
   │     (audit window; enumerate test layers, workflows, gates, skips,
   │      benchmark gates, and the live origin/main CI state)
   ▼
Task 3: Multi-Dimension Audit Execution (T1–T8)
   │     (reproduce every gate command's exit code; run the suites;
   │      pull CI logs; classify every failure)
   ▼
Task 4: Executive Testing and CI Audit Report Compilation
   │
   ▼
Task 5: Remediation Planning (Immediate vs Pass-Forward)
   │
   ▼
Task 6: Remediation Execution & Verification
   │
   ▼
Task 7: Final Documentation, Session Register/Traceability, Git Commit
```

**Governance principles** (identical intent to EA §2, restated for the
test-and-CI-audit context):

1. **Evidence-based verification.** Every finding is backed by a reproduced
   command with its real exit code, a CI run log, a test output, or a direct
   file inspection — never by a green check mark alone and never by a prior
   session's assertion.
2. **A gate is only real if it fails.** For every required CI gate, the ETCA
   session confirms the command exits non-zero on a real violation (by
   reproducing it, or by inspecting a historical failing run). A gate that
   is green because it never actually evaluates the condition, or is
   unreachable behind an earlier failing step, is a D2 finding regardless of
   the workflow's overall conclusion.
3. **Local gate ≡ CI gate.** The canonical local verification one-liner and
   the CI workflow set must be command-equivalent and produce equivalent
   results on a clean checkout. Divergence is a finding, because it means
   "the local gate passed" cannot be trusted as a proxy for "CI will pass".
4. **No silent gaps.** A missing test layer, an unexplained skip, an unpushed
   S4 range, or a non-running workflow is always recorded as a finding, never
   treated as acceptable and never omitted from the report.
5. **Clean verification gate.** An ETCA session cannot close until every
   D1/D2 finding is `FIXED` or `AMENDED`, matching EA §2.5 and Development
   Workflow Standards §1's "deviations never accumulate" principle. A finding
   that is a pure external-infrastructure condition (billing, runner
   availability, hosted-runner disk) follows the DV-014/DV-022/DV-024
   precedent: it is passed forward with a dated disposition and, where
   possible, a wired fallback, not left as an untracked red.

---

## 5. Reporting and Artifact Rules

1. **Executive Testing and CI Audit Report:** saved as
   `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_NNN.md` using
   `DOCS/audits/TEMPLATE_Executive_Testing_and_CI_Audit_Report.md`. Findings
   use the `T-FN` identifier prefix (distinct from EA's `E-FN`, EMA's `M-FN`,
   and EDA's `D-FN`) to keep the four audit types' finding histories
   independently traceable.
2. **Session registration:** ETCA sessions are global sessions, registered in
   `DOCS/sessions/SESSION_REGISTER.md` under a dedicated "Global sessions —
   Executive Testing and CI Audits" section, outside the planned 0001–0198
   sequence, following the identical precedent plan amendment #15 established
   for EA sessions (`ETCA-NNN` identifiers, never renumbering planned
   sessions).
3. **Remediation plan:** embedded in the ETCA report or saved alongside it if
   extensive, identical convention to EA §5.2. An ETCA session is read-only
   with respect to first-party source: a finding that requires a source or
   test-code fix is planned, not executed, and is handed to a dedicated
   remediation session or the owning WP's S2/S3 — matching the EDA §4.1
   precedent. Purely additive CI-configuration and workflow fixes, and
   one-line documentation corrections, may be executed in Task 6 under the
   R21/R27 "one-line documentation edit defaults to fix now" precedent.
4. **Project State Report:** cross-referenced or updated to reflect ETCA
   conclusions, identical convention to EA §5.4.
5. **Recurrence:** an ETCA session is warranted at the points described in
   §1.1. At minimum, one ETCA session per phase when the phase produces 5+
   work packages, 50+ commits, or a 25%+ net test-count change; and one at
   every phase boundary, alongside the EA session.
6. **Closing checklist:** As a global session outside every WP-N S4
   checklist, an ETCA session's own file changes are not otherwise swept by
   R7's documentation-accuracy net (Documentation Standards §7). Before this
   session closes, it must therefore itself: (a) add or update a
   `CHANGELOG.md` `[Unreleased]` entry for every user-visible change the
   session makes (governance document, template, workflow/config fix), and
   (b) run the relevant quality gates (`ruff check`/`ruff format --check`/
   `mypy --strict` for Python; `cargo fmt --check`/`cargo clippy -- -D
   warnings` for Rust) on every file it newly commits, before Task 7 (Final
   Documentation, Session Register/Traceability, Git Commit).
7. **Deferral requires a recorded rationale** (per Documentation Standards §7
   item 9's phase-closing requirement, applied here to this session type's
   own closing checklist). If this checklist identifies a genuine gap in
   this session's required artefacts, the session must fix it before closing
   or record an explicit, reviewable rationale for deferring it — a bare
   "recommended for next session" note is not sufficient.

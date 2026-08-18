# PRIN Phase Analytics Methodology

**Status:** Normative for all phase-level analytics sessions. This methodology
governs the comprehensive, scientifically rigorous assessment of a completed
PRIN roadmap phase. It is the first analytics-specific governance document and
establishes the framework for all subsequent phase analytics.

**Relationship to existing governance:** This methodology extends — and never
overrides — the [Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md),
the [Experimentation Standards](../standards/Experimentation_Standards.md),
the [Coding Standards](../standards/Coding_Standards.md), the
[Testing Standards](../standards/Testing_Standards.md), the
[Documentation Standards](../standards/Documentation_Standards.md), the
[Benchmarking and Reproducibility Standards](../standards/Benchmarking_and_Reproducibility_Standards.md),
the [Versioning and Release Standards](../standards/Versioning_and_Release_Standards.md),
and the [Official Project Plan](../PRIN_Project_Plan.md). Where this document
and the standards diverge, the standards win.

---

## 1. Purpose and scope

A **Phase Analytics Session** is a retrospective, evidence-based assessment of
an entire completed roadmap phase. It is distinct from — and complementary to —
the per-cycle S2 audit:

| Dimension | Per-cycle S2 audit | Phase analytics session |
|---|---|---|
| Temporal scope | One work package, one Session Cycle | One entire roadmap phase (all WPs, all cycles) |
| Purpose | Detect and correct deviations from the planned trajectory | Synthesize, scrutinize, and rate the phase's cumulative engineering achievements, quality, evidence, and governance health |
| Temporal mode | Prospective / in-cycle correction | Retrospective / post-completion assessment |
| Output | Audit Report (`DOCS/audits/`) with D1–D4 findings | Phase Analytics Report (`DOCS/ANALYTICS/phase-N/`) with dimension scores, evidence index, and recommendations |
| Authority | Findings block feature work until resolved | Recommendations inform the next phase's planning; they do not block unless they surface an unresolved D1 |

A phase analytics session is convened **after** the phase's final S4
documentation session closes and the phase exit gate is declared green (or
red, with a documented resolution path).

## 2. Principles

1. **Evidence-based, always.** Every claim, score, and recommendation traces
   to a committed artefact: a file citation, a command output, a test result,
   a coverage number, a scan report, a git SHA, or an audit finding. No claim
   rests on recollection or assertion. This mirrors S2 audit principle 4
   (Development Workflow Standards §1).
2. **Scientific rigor.** The assessment applies the same standards of
   falsifiability, reproducibility, and claim-evidence matching that govern
   PRIN's experimentation (Experimentation Standards §1). Recommendations are
   falsifiable: each states what evidence would weaken or overturn it.
3. **Independent verification.** The analytics session re-executes or
   re-inspects key evidence rather than trusting prior reports. Where
   re-execution is infeasible (e.g., GPU hardware not available), the
   limitation is documented and the claim is scoped accordingly.
4. **Comprehensive coverage.** The assessment examines every dimension the
   phase touched: data, documentation, testing, coding, evidence, governance,
   security, architecture, and phase-specific deliverables. No dimension is
   omitted because it was "clean" — clean dimensions are scored and cited too.
5. **Deviation-aware.** The assessment uses the cumulative deviation ledger
   and amendment log as primary inputs. Patterns across findings (recurring
   severity classes, repeated root causes) are analyzed, not just listed.
6. **Forward-looking.** The assessment produces actionable recommendations for
   the next phase, grounded in observed weaknesses and strengths. It does not
   merely describe the past; it improves the future.
7. **No silent overrides.** If the analytics session discovers an unresolved
   deviation or a standards violation that prior audits missed, it is recorded
   as a new finding in the deviation ledger format (D1–D4) and escalated per
   the Development Workflow Standards. The analytics session does not absorb
   deviations by reclassifying them.

## 3. Assessment dimensions

Every phase analytics session assesses the following dimensions. Each
dimension receives a **score** (see §4) and a narrative backed by evidence.

| ID | Dimension | Assessment focus | Primary evidence sources |
|---|---|---|---|
| P1 | **Data and parity artefacts** | Corpus completeness, coverage matrix, schema/manifest integrity, SHA-256 verification, reproducibility from reference, fixture quality, data governance | `parity/`, `python/prin/parity/`, `EVIDENCE/`, corpus manifests, differential test results |
| P2 | **Documentation** | Standards completeness and adherence, audit/report/template artefact trail, README coverage, CHANGELOG accuracy, Sphinx build, docstring/rustdoc coverage, Migration Guide, session briefs, traceability matrix | `DOCS/standards/`, `DOCS/audits/`, `DOCS/reports/`, `DOCS/sessions/`, directory READMEs, `CHANGELOG.md`, Sphinx build output, interrogate/cargo doc results |
| P3 | **Testing** | Test count, layer coverage (unit/property/parity/gradcheck/kernel-equivalence/integration), coverage gates, test-in-tandem adherence, marker discipline, test quality (mutation/edge cases), flakiness, regression tests for fixes | `tests/`, `parity/`, Rust test modules, coverage reports, audit A3 findings |
| P4 | **Coding and architecture** | Architecture conformance (crate layering, one-algorithm-one-implementation, no numerics in Python, explicit state/seeding), code quality gates (fmt/clippy/ruff/mypy), `unsafe` discipline, error handling, naming conventions, dependency hygiene, feature flag correctness | `crates/`, `python/prin/`, `Cargo.toml`, `pyproject.toml`, audit A2/A5/A6 findings, quality gate outputs |
| P5 | **Evidence and verification** | Scan completeness (Snyk Code/Open Source, cargo audit, pip-audit, bandit, Gitleaks), CI workflow coverage and green status, verification command reproducibility, evidence file integrity, independent re-execution results | `EVIDENCE/`, `.github/workflows/`, scan outputs, CI run records, `AGENTS.md` one-liner results |
| P6 | **Governance and process** | Session Cycle adherence (S1→S2→S3→S4 order, no skips), deviation ledger completeness, amendment process discipline, plan-standards-code consistency, scope discipline, artefact trail integrity, traceability matrix coverage | `DOCS/sessions/SESSION_REGISTER.md`, `DOCS/sessions/TRACEABILITY.md`, `DOCS/audits/`, `DOCS/reports/`, plan amendment log, deviation ledger |
| P7 | **Security** | `unsafe` confinement, input validation, secret scanning, dependency advisory status, supply-chain controls, runtime code generation prohibition, branch protection | Audit A6 findings, `cargo audit`, `pip-audit`, Snyk scans, Gitleaks, `.gitleaks.toml`, branch protection records |
| P8 | **Phase exit criteria** | Phase-specific exit gate verdict, spike go/no-go decisions, deliverable completeness vs. plan §6, deferred items documented with re-audit gates | Phase exit gate evidence, plan §6 exit criteria, plan amendments for deferrals |
| P9 | **Risk and deferred validation** | Risk register accuracy, deferred validation items (with re-audit gates), inherited advisories, platform/hardware limitations, blockers for next phase | Plan §7 risk register, plan amendment deferrals, project state report risk sections |

## 4. Scoring framework

Each dimension is scored on a 5-point ordinal scale. Scores are assigned from
evidence, not impression. The score must be justified with at least three
cited evidence points.

| Score | Label | Definition |
|---|---|---|
| 5 | **Exemplary** | Exceeds the standard. All gates green, evidence is reproducible and independently verified, no findings, forward-looking improvements identified. Sets a benchmark for future phases. |
| 4 | **Strong** | Meets the standard fully. All gates green, evidence is complete and cited, findings (if any) are all resolved. Minor improvements recommended. |
| 3 | **Adequate** | Meets the standard with caveats. Gates green but with approved amendments/deferrals. Evidence present but with gaps in independent verification. Recommendations address the caveats. |
| 2 | **Marginal** | Partially meets the standard. Some gates green, some deferred. Evidence incomplete or not independently verified. Multiple unresolved or recurring findings. Recommendations are mandatory. |
| 1 | **Deficient** | Does not meet the standard. Gates failing or evidence absent. Unresolved D1/D2 findings. Blocks progression until remediated. |

### 4.1 Aggregate phase verdict

| Aggregate condition | Phase verdict |
|---|---|
| All dimensions ≥ 4, no dimension < 3 | **PASS — EXCELLENT** |
| All dimensions ≥ 3, no dimension < 2 | **PASS — SATISFACTORY** |
| Any dimension = 2, no dimension = 1 | **PASS — CONDITIONAL** (mandatory recommendations) |
| Any dimension = 1 | **FAIL** (blocks next phase; remediation required) |

## 5. Assessment procedure

### 5.1 Inputs (read before assessment begins)

1. The Official Project Plan (`DOCS/PRIN_Project_Plan.md`), including the
   phase's scope, exit criteria, and amendment log.
2. All standards documents (`DOCS/standards/`).
3. All audit reports for the phase's cycles (`DOCS/audits/`).
4. All project state reports for the phase's cycles (`DOCS/reports/`).
5. The session register and traceability matrix
   (`DOCS/sessions/SESSION_REGISTER.md`, `DOCS/sessions/TRACEABILITY.md`).
6. All session briefs for the phase (`DOCS/sessions/phase-N/`).
7. The cumulative deviation ledger (from the latest project state report).
8. All evidence files (`EVIDENCE/`).
9. The actual repository state (code, tests, configs, CI workflows).
10. The CHANGELOG for the phase's release entries.
11. **Snyk verification channel, checked explicitly** (Phase 2 analytics R18;
    resolved by Phase 3 recommendation R23): before relying on any Snyk
    Code/Snyk Open Source result, confirm whether the Snyk MCP tool is
    available in this session's environment. **Maintainer decision (R23,
    Phase 3 recommendation implementation, 2026-08-18):** Snyk MCP was
    unavailable across 4 consecutive Executive Audit sessions and 2
    consecutive phase-analytics sessions, with the Snyk CLI serving as a
    fully effective compensating control throughout (consistent, evidence-
    backed results in every one of those sessions); the maintainer confirmed
    the Snyk-CLI-only posture is intentional and permanent. This is
    therefore no longer a standing tooling-access-gap escalation: if Snyk
    MCP happens to be available in a given session, prefer it and record
    that fact; otherwise run the Snyk CLI directly and cite its version,
    date, and command output as the position of record. State the channel
    actually used (MCP or CLI) explicitly in the session's evidence table
    either way.

### 5.2 Execution

1. **Inventory.** Produce a complete artefact inventory for the phase: every
   file added/modified, every test, every audit, every report, every
   amendment, every evidence file. Cite paths and line counts.
2. **Dimension assessment.** For each dimension P1–P9:
   a. State the dimension's requirements (from the standards and plan).
   b. List the evidence examined (with file citations and command outputs).
   c. Assess conformance against the requirements.
   d. Identify strengths, weaknesses, and patterns.
   e. Assign a score with justification.
3. **Cross-dimensional analysis.** Identify patterns across dimensions:
   recurring root causes, systemic strengths, systemic weaknesses, and
   correlations (e.g., does documentation quality correlate with audit
   finding count?).
4. **Independent verification.** Re-execute a representative subset of the
   verification one-liner (`AGENTS.md`) and compare results to the latest
   project state report. Document any discrepancies.
5. **Recommendations.** Produce actionable, prioritized recommendations for
   the next phase. Each recommendation states: the dimension it addresses,
   the evidence that motivates it, the recommended action, and what evidence
   would confirm it is addressed.
6. **Verdict.** Assign the aggregate phase verdict per §4.1.

### 5.3 Output

The phase analytics session produces:

1. **Phase Analytics Report** at
   `DOCS/ANALYTICS/phase-N/phase-N-analytics-report.md` — the comprehensive
   assessment document.
2. **Evidence Index** at
   `DOCS/ANALYTICS/phase-N/phase-N-evidence-index.md` — a structured index of
   every evidence artefact cited in the report, with file path, SHA (where
   applicable), and the dimension(s) it supports.
3. **Recommendations Register** at
   `DOCS/ANALYTICS/phase-N/phase-N-recommendations.md` — the prioritized
   recommendations for the next phase, formatted for tracking.

### 5.4 Amendment and versioning

This methodology is normative. Amendments follow the same review bar as the
project plan: pull request, maintainer approval, a row in the plan's amendment
log, and a note in `CHANGELOG.md`.

## 6. Scientific integrity rules

These rules adapt the Experimentation Standards §4 to the analytics context:

1. **No cherry-picking.** All dimensions are assessed and scored; none are
   omitted because they are "clean" or "trivial."
2. **No retroactive scoring.** Scores are assigned from the evidence at the
   time of assessment. If new evidence emerges later, a supplementary
   assessment is appended, not a retroactive edit.
3. **Claim-evidence matching.** Every claim in the report has a citation. The
   evidence index is the authoritative cross-reference.
4. **Limitations stated.** Where independent verification was infeasible
   (hardware, platform, access), the limitation is stated and the claim is
   scoped. No claim is made beyond its evidence.
5. **AI assistance disclosed.** The report states which analyses were drafted
   by the AI pair and verified by the maintainer, per Experimentation
   Standards §4.
6. **Errata.** If a claim in the report is later invalidated, an erratum is
   appended to the report and noted in `CHANGELOG.md`.

## 7. Relationship to the Session Cycle

A phase analytics session is **not** a Session Cycle session (S1–S4). It does
not produce code, does not follow the S1→S4 order, and does not produce an
audit report. It is a retrospective assessment that:

- Consumes the outputs of all Session Cycles in the phase.
- May surface new findings (recorded in the deviation ledger format).
- Produces recommendations that inform the next phase's WP declarations and
  session briefs.
- Is convened at the discretion of the maintainer after the phase exit gate.

If the analytics session surfaces an unresolved D1/D2 finding, the normal
Session Cycle remediation process is triggered (hotfix or next-cycle S3),
independent of the analytics session itself.

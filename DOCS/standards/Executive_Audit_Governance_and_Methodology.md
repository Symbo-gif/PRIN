# PRIN Executive Audit Governance and Methodology

**Status:** Normative. This document establishes the governance, scope, criteria, methodology, findings classification, remediation protocols, and reporting requirements for **Executive Audit Sessions** in the PRIN project.

**Relationship to existing governance:** This document extends—and never overrides—the [Development Workflow and Audit Standards](Development_Workflow_and_Audit_Standards.md), [Coding Standards](Coding_Standards.md), [Testing Standards](Testing_Standards.md), [Documentation Standards](Documentation_Standards.md), [Benchmarking and Reproducibility Standards](Benchmarking_and_Reproducibility_Standards.md), [Experimentation Standards](Experimentation_Standards.md), [Versioning and Release Standards](Versioning_and_Release_Standards.md), and [Official Project Plan](../PRIN_Project_Plan.md).

---

## 1. Purpose and Scope

An **Executive Audit Session** is a holistic, multi-domain, project-level audit. Unlike per-cycle S2 audits (which focus on a single Work Package) or Phase Analytics sessions (which synthesize a completed phase), an Executive Audit scrutinizes the **entire codebase, mathematical core, software architecture, security posture, test suite, documentation, evidence chain, and governance history**.

The Executive Audit evaluates compliance across 10 core audit dimensions:

| ID | Dimension | Assessment Scope |
|---|---|---|
| **E1** | **Mathematical & Oscillator Dynamics Core** | Formulation correctness, ODE integration, phase wrapping, amplitude/derivative clamps, numerical guards, deterministic seed authority, k-NN spatial indexing, floating-point precision, and parity tolerances. |
| **E2** | **Codebase & Architecture Conformance** | Crate layering (`prin-dynamics`, `prin-kernels`, `_prin_core`, `prin`), FFI/PyO3/DLPack bridge safety, "no numerics in Python" enforcement, `strict-checks` feature flags, typed error enums, and unsafe isolation. |
| **E3** | **Test Suite & Parity Corpus** | Test count, test-in-tandem compliance, unit/property tests (`proptest`), differential parity harness, coverage gates (≥95%), and edge-case handling. |
| **E4** | **Security & Supply Chain** | Snyk Code, Snyk SCA, `cargo audit`, `pip-audit`, Bandit, Ruff security rules, secret scanning, dependency vulnerability management, and supply chain controls. |
| **E5** | **Standards & Documentation Adherence** | Directory README completeness, API docstrings/rustdoc coverage (`interrogate` 100% public, `cargo doc` 0 warnings), Sphinx HTML build, CHANGELOG accuracy, Migration Guide, and document formatting. |
| **E6** | **Evidence, Baselines & Analytics Integrity** | SHA-256 evidence integrity, baseline script outputs, evidence index accuracy, and analytics report consistency. |
| **E7** | **Session Cycle & Governance Traceability** | S1–S4 Session Cycle adherence across all cycles (001–006+), deviation ledger completeness, plan amendment logging, session register entries, and traceability matrix alignment. |
| **E8** | **Performance, Benchmarking & Reproducibility** | Benchmark suite health, FLOPs/time scaling analysis, memory usage, hardware constraints, and execution reproducibility. |
| **E9** | **CI/CD & Build Infrastructure** | GitHub Actions workflow coverage (`python.yml`, `rust.yml`, `snyk.yml`, `parity.yml`, `repro.yml`, `release.yml`, `gpu.yml`), build matrix validation, feature flag testing in CI, and wheel distribution checks. |
| **E10**| **Roadmap, Risks & Future Session Handoff** | Plan §6/§7 alignment, Phase 0 and Phase 1 roadmap status, pass-forward issue logging with explicit future session/WP placeholders, and risk register updates. |

---

## 2. Governance Principles for Executive Audits

1. **Full-Spectrum Verification:** Executive audits must execute real commands, run test suites, check security tools, and verify artifacts directly. Unverifiable assertions are non-conforming.
2. **Strict Trajectory Compliance:** Any divergence from `DOCS/PRIN_Project_Plan.md` or normative standards is classified as a deviation (D1–D4).
3. **Mandatory Remediation:** All actionable findings must either be fixed immediately in the session or formally passed forward to explicit future Work Packages with documented placeholders.
4. **Retroactive Documentation Authority:** For initial executive audits, retroactive documentation updates to past session logs, READMEs, or CHANGELOG entries are permitted to correct omissions from historical sessions, provided they are clearly tagged as `[RETROACTIVE UPDATE - Executive Audit NNN]`.
5. **Clean Verification Gate:** An executive audit cannot close until all required verification commands pass cleanly without unapproved errors or warnings.
6. **Snyk verification channel (Phase 2 analytics R18; resolved by Phase 3 recommendation R23):** At the start of every Executive Audit session, check Snyk MCP tool availability before relying on any Snyk result. **Maintainer decision (R23, Phase 3 recommendation implementation, 2026-08-18):** after Snyk MCP was unavailable across 4 consecutive Executive Audit sessions with the Snyk CLI serving as a fully effective compensating control throughout, the maintainer confirmed the Snyk-CLI-only posture is intentional and permanent — this is no longer a standing tooling-access-gap escalation. If Snyk MCP happens to be available in a given session, prefer it and record that fact; otherwise run the Snyk CLI directly, citing its version, date, and command output as the position of record rather than re-asserting a prior session's finding as if freshly run.

---

## 3. Severity Classification and Deviation Ledger

Every issue identified during an executive audit is assigned a unique ID (`E-FN`) and classified under the standard PRIN severity scale:

| Severity | Definition | Required Response |
|---|---|---|
| **D1 — Trajectory Breach** | Violates core architectural rules, mathematical correctness, security requirements, or published reproducibility guarantees. | Immediate fix required. Freezes progress until resolved. |
| **D2 — Subsystem Deviation** | Missing required tests, guard checks, fallback logic, or strict-mode checks. | Fix in remediation step before audit session closure. |
| **D3 — Process / Quality Deviation** | Gaps in CI workflow coverage, missing benchmark assertions, or incomplete documentation gates. | Fix in remediation step or log with explicit future WP placeholder. |
| **D4 — Hygiene / Documentation** | Formatting inconsistencies, missing README sections, or minor docstring/comment gaps. | Fix during remediation / documentation alignment step. |

---

## 4. Executive Audit Workflow Lifecycle

An Executive Audit Session proceeds through 7 mandatory sequential tasks:

```
Task 1: Governance & Methodology Definition
   │
   ▼
Task 2: Full Multi-Domain Audit Execution (E1–E10)
   │
   ▼
Task 3: Executive Audit Report Compilation
   │
   ▼
Task 4: Remediation Planning (Immediate vs Pass-Forward)
   │
   ▼
Task 5: Remediation Execution & Retroactive Documentation Updates
   │
   ▼
Task 6: Verification Suite Execution (Tests, Linters, Audits, Docs)
   │
   ▼
Task 7: Final Documentation, Session Logging, Git Commit & Push
```

---

## 5. Reporting and Artifact Rules

1. **Executive Audit Report:** Saved as `DOCS/audits/EXECUTIVE_AUDIT_REPORT_NNN.md` using `DOCS/audits/TEMPLATE_Executive_Audit_Report.md`.
2. **Remediation Plan:** Embedded in the Executive Audit Report or saved alongside it if extensive.
3. **Session Register & Traceability:** Updated in `DOCS/sessions/SESSION_REGISTER.md` and `DOCS/sessions/TRACEABILITY.md`.
4. **Project State Report:** Cross-referenced or updated to reflect executive audit conclusions.
5. **Closing checklist (Phase 2 analytics R16):** As a global session outside every WP-N S4
   checklist, an Executive Audit session's own file changes are not otherwise swept by R7's
   documentation-accuracy net (Documentation Standards §7). Before this session closes, it must
   therefore itself: (a) add or update a `CHANGELOG.md` `[Unreleased]` entry for every user-visible
   change the session makes (fix, governance document, tooling), and (b) run the relevant quality
   gates (`ruff check`/`ruff format --check`/`mypy --strict` for Python; `cargo fmt --check`/
   `cargo clippy -- -D warnings` for Rust) on every file it newly commits, before Task 7 (Final
   Documentation, Session Logging, Git Commit & Push). This closes the gap PA2-F2 traced to
   EMA-001 (a global session whose `CHANGELOG.md` entry was omitted because no WP-N S4 checklist
   ever ran against it).
6. **Deferral requires a recorded rationale (Phase 4 analytics R27).** If
   this checklist (or any other part of the session's own closing review)
   identifies a genuine gap in this session's required artefacts, the
   session must fix it before closing or record an explicit, reviewable
   rationale for deferring it — a bare "recommended for next session" note
   is not sufficient. Same rule and rationale as Documentation Standards §7
   item 9's phase-closing requirement, applied here to this session type's
   own closing checklist.

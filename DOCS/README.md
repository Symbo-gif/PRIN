# DOCS/ — PRIN governance, planning, and documentation

Single documentation tree for PRIN (Windows filesystems are case-insensitive,
so a separate lowercase `docs/` cannot coexist with `DOCS/`; see the
Documentation Standards §3).

## Contents

| Item | Purpose |
|---|---|
| [`PRIN_Project_Plan.md`](PRIN_Project_Plan.md) | **The official project plan** — mission, requirements, architecture, parity program, phased roadmap (incl. Phase 7 campaign), Session Cycle methodology (§8.1), amendment log, definition of done |
| [`standards/Development_Workflow_and_Audit_Standards.md`](standards/Development_Workflow_and_Audit_Standards.md) | **The Session Cycle** — self-auditing workflow (S1 code → S2 audit → S3 remediate → S4 document), deviation classification and correction |
| [`standards/Coding_Standards.md`](standards/Coding_Standards.md) | Normative Rust + Python coding standards, incl. security standards (§6) |
| [`standards/Testing_Standards.md`](standards/Testing_Standards.md) | Normative testing, tolerance, and coverage standards |
| [`standards/Documentation_Standards.md`](standards/Documentation_Standards.md) | Normative documentation standards |
| [`standards/Benchmarking_and_Reproducibility_Standards.md`](standards/Benchmarking_and_Reproducibility_Standards.md) | Normative benchmarking and reproducibility standards |
| [`standards/Experimentation_Standards.md`](standards/Experimentation_Standards.md) | Normative scientific experimentation standards — pre-registration (expected results + failure conditions before execution), campaign rules, integrity rules |
| [`standards/Versioning_and_Release_Standards.md`](standards/Versioning_and_Release_Standards.md) | Normative versioning, CI/CD, and release standards |
| [`audits/`](audits/README.md) | Per-cycle Audit Reports (S2) and S3 closure evidence |
| [`baselines/`](baselines/README.md) | Immutable measured repository/API baseline artefacts |
| [`reports/`](reports/README.md) | Per-cycle Project State Reports (S4) + template — the latest report is the authoritative trajectory position |
| [`experiments/`](experiments/README.md) | Experiment pre-registrations, execution logs, and reports + template |
| [`sessions/`](sessions/README.md) | **Complete Session Execution Plan** — 198 individually addressable briefs from WP-001 through stable `1.0.0`, master register, traceability matrix, and conditional correction templates |
| [`ANALYTICS/`](ANALYTICS/README.md) | Phase-level analytics sessions — comprehensive, scientifically rigorous retrospective assessment of each completed roadmap phase (methodology, dimension scores, evidence index, recommendations) |
| [`sphinx/`](sphinx/README.md) | The Sphinx documentation site (ReadTheDocs) |
| `archive and reference from PRINet 3.0/` | **Archived PRINet 3.0.0 — reference and planning material only.** Nothing in it is imported, executed, or built by PRIN |
| `test_and_benchmark_results/` | Generated benchmark reports (gitignored; canonical artefacts in `benchmarks/results/`) |

## Current state

- Latest Project State Report: [`022-project-state.md`](reports/022-project-state.md) —
  WP-022 S4 closure (Phase 4 first WP: trainable bands and resonance
  primitives), WP-023 declaration.
- Latest Audit Report: [`022-wp022-audit.md`](audits/022-wp022-audit.md) —
  `PASS-WITH-FINDINGS` (two D4 findings), S3 delta re-audit **CLEAN**.
- Latest Phase Analytics: [`ANALYTICS/phase-3/phase-3-analytics-report.md`](ANALYTICS/phase-3/phase-3-analytics-report.md) —
  Phase 3 **PASS — SATISFACTORY**.

Operational checklists mirroring the Session Cycle live in
`.windsurf/workflows/` (`/coding-session`, `/audit-session`,
`/remediation-session`, `/documentation-session`, `/experiment-session`);
the standards documents are authoritative if they diverge.

## Amendment process

Governance documents are normative. Amendments follow the same review bar as
code: pull request, maintainer approval, a row in the plan's amendment log
(§8.3), updates to affected session briefs/register/traceability, and a note in
`CHANGELOG.md`.

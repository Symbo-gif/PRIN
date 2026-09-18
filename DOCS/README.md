# DOCS/ — PRIN governance, planning, and documentation

Single documentation tree for PRIN (Windows filesystems are case-insensitive,
so a separate lowercase `docs/` cannot coexist with `DOCS/`; see the
Documentation Standards §3).

## Navigation Map

```
DOCS/
├── PRIN_Project_Plan.md          ← THE plan: mission, roadmap, amendments
├── standards/                    ← Normative engineering standards (12 docs)
│   ├── Development_Workflow...   ← The Session Cycle (S1→S2→S3→S4)
│   ├── Coding_Standards          ← Rust + Python + security
│   ├── Testing_Standards         ← Test layers, tolerances, coverage
│   ├── Documentation_Standards   ← API docs, S4 closure, readability (ERA)
│   ├── Executive_*_Governance... ← EA, EMA, EDA, ETCA, ERA audit governance
│   └── ...
├── sessions/                     ← 198 session briefs + register + traceability
│   ├── SESSION_REGISTER.md       ← Master session order and status
│   ├── TRACEABILITY.md           ← Symbol-to-session mapping
│   └── phase-N/                  ← Per-phase brief directories
├── audits/                       ← S2 audit reports (one per WP) + executive audits
├── reports/                      ← S4 Project State Reports + DV Register
├── ANALYTICS/                    ← Phase-level retrospective assessments
├── experiments/                  ← Pre-registrations, execution logs, handoffs
├── baselines/                    ← Immutable baseline artefacts (WP-001)
├── sphinx/                       ← Sphinx site source (ReadTheDocs)
├── devtools/                     ← Code-intelligence subsystem docs
└── archive and reference.../     ← PRINet 3.0 reference (read-only)
```

**Where to start:**
- **What is the project doing?** → `PRIN_Project_Plan.md`
- **How does work flow?** → `standards/Development_Workflow_and_Audit_Standards.md`
- **Where are we now?** → `reports/` (latest `NNN-project-state.md`)
- **What was audited?** → `audits/` (per-WP reports + executive audits)
- **What is planned next?** → `sessions/SESSION_REGISTER.md`
- **How did a phase go?** → `ANALYTICS/phase-N/`

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
| [`devtools/`](devtools/visualization-mcp.md) | Local codebase visualization + runtime-observability MCP subsystem (`tools/code-intelligence/`) — a well-isolated developer-tooling add-on outside the Session Cycle; see the plan, architecture, security, implementation-report, and troubleshooting docs there |

## Current state

- Latest Project State Report: [`037-project-state.md`](reports/037-project-state.md) —
  WP-037 S4 closure, all eight S2 findings closed or governed (CLEAN delta
  re-audit), canonical-parameter trainability restored, WP-038 declaration.
- Latest Audit Report: [`037-wp037-audit.md`](audits/037-wp037-audit.md) —
  S2 `FAIL` (eight findings), S3 corrective remediation, delta re-audit
  **CLEAN**.
- Latest Phase Analytics: [`ANALYTICS/phase-5/phase-5-analytics-report.md`](ANALYTICS/phase-5/phase-5-analytics-report.md) —
  Phase 5 **PASS — SATISFACTORY**.

Operational checklists mirroring the Session Cycle live in
`.windsurf/workflows/` (`/coding-session`, `/audit-session`,
`/remediation-session`, `/documentation-session`, `/experiment-session`);
the standards documents are authoritative if they diverge.

## Amendment process

Governance documents are normative. Amendments follow the same review bar as
code: pull request, maintainer approval, a row in the plan's amendment log
(§8.3), updates to affected session briefs/register/traceability, and a note in
`CHANGELOG.md`.

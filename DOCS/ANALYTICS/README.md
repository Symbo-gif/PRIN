# DOCS/ANALYTICS/ — Phase Analytics

Phase-level analytics sessions that comprehensively and with scientific rigor
assess a completed PRIN roadmap phase's engineering achievements, quality,
evidence, and governance health. Distinct from — and complementary to — the
per-cycle S2 audit (see the
[Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md)).

## Methodology

[`ANALYTICS_METHODOLOGY.md`](ANALYTICS_METHODOLOGY.md) — the normative
methodology for all phase analytics sessions. Established in the Phase 0
analytics session (the first analytics session for this project). It defines:

- 9 assessment dimensions (P1–P9): data, documentation, testing, coding,
  evidence, governance, security, exit criteria, and risk.
- A 5-point scoring framework (1=Deficient to 5=Exemplary) with an aggregate
  phase verdict (PASS-EXCELLENT / PASS-SATISFACTORY / PASS-CONDITIONAL / FAIL).
- An evidence-based assessment procedure with independent re-verification.
- Scientific integrity rules adapted from the Experimentation Standards.

## Phase reports

| Phase | Report | Verdict | Date |
|---|---|---|---|
| 0 — Foundation | [`phase-0/phase-0-analytics-report.md`](phase-0/phase-0-analytics-report.md) | **PASS — EXCELLENT** | 2026-08-07 |
| 1 — Dynamics core | [`phase-1/phase-1-analytics-report.md`](phase-1/phase-1-analytics-report.md) | **PASS — EXCELLENT** | 2026-08-09 |
| 2 — Advanced numerics and simulation | [`phase-2/phase-2-analytics-report.md`](phase-2/phase-2-analytics-report.md) | **PASS — SATISFACTORY** | 2026-08-15 |
| 3 — GPU kernels | [`phase-3/phase-3-analytics-report.md`](phase-3/phase-3-analytics-report.md) | **PASS — SATISFACTORY** | 2026-08-18 |

## Companion files

Each phase report has two companion files in its phase directory:

- **Evidence index** (`phase-N-evidence-index.md`) — structured index of every
  evidence artefact cited in the report.
- **Recommendations register** (`phase-N-recommendations.md`) — prioritized
  recommendations for the next phase.

## Rules

- Analytics reports are committed artefacts; they are not edited after
  issuance except to append an erratum.
- If an analytics session surfaces an unresolved D1/D2 finding, the normal
  Session Cycle remediation process is triggered, independent of the
  analytics session.
- Analytics recommendations inform but do not block the next phase unless
  they surface an unresolved deviation.
- The methodology is normative; amendments follow the same review bar as
  the project plan.

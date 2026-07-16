---
description: Run a pre-registered experiment (E1–E5) per the Experimentation Standards
---

Authoritative definition: `DOCS/standards/Experimentation_Standards.md`. No
experiment executes without a committed, maintainer-approved pre-registration.

1. Read `DOCS/sessions/SESSION_REGISTER.md`, the active numbered E-stage
   brief, its predecessor evidence, and the approved campaign plan. State the
   global session ID, EXP ID/track, and **only the active stage** (E1–E5).
   Never collapse multiple E stages into one session.
2. Confirm eligibility: campaign experiments require Phases 0–6 complete and
   audited; ad-hoc experiments still require full pre-registration.
3. If the active stage is **E1 Pre-register**, create
   `DOCS/experiments/EXP-NNN-<slug>/preregistration.md` from
   `TEMPLATE_Preregistration.md`. All sections mandatory — especially
   quantitative hypotheses, expected results (direction + magnitude + basis),
   falsification conditions per hypothesis, and run-level abort criteria.
4. If active stage is **E2 Approval**, obtain independent review and maintainer
   approval recorded in the header. The document freezes when E3 starts.
5. If active stage is **E3 Execute**, run only via `benchrunner`/committed drivers; artefacts to
   `benchmarks/results/EXP-NNN/` with full environment capture (SHA, versions,
   hardware, backend, dtype, seeds). Maintain
   `DOCS/experiments/EXP-NNN-<slug>/log.md` (timestamps, anomalies, any abort
   trips). Never delete aborted runs.
6. If active stage is **E4 Analyze**, follow the pre-registered analysis plan
   exactly; commit analysis code; regenerate figures/tables via
   `prin.reporting` (SHA-256 manifest). Extra analyses go under an
   "Exploratory" heading.
7. If active stage is **E5 Report**, write `report.md`: per-hypothesis verdict
   (CONFIRMED / REFUTED / INCONCLUSIVE) with effect size + CI, an
   expected-vs-observed table, protocol deviations, threats to validity,
   artefact index.
8. If a result contradicts a published PRINet 3.0 conclusion (tracks C1–C3)
   or a normative requirement, block the listed successor and insert all four
   conditional correction sessions from `DOCS/sessions/contingencies/`.
9. End after the active brief's exit gate. Update register statuses only from
   committed evidence; proceed only to the listed successor.

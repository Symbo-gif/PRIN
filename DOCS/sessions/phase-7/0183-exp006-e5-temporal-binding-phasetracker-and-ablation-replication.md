# Session 0183 — EXP-006 / C3 E5: Report — Temporal binding, PhaseTracker, and ablation replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-006 / C3  
**Session type:** E5 — Report  
**Predecessor:** [0182 — Analysis](0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md)  
**Successor:** [0184 — Pre-registration](0184-exp007-e1-daemon-mot-and-adversarial-replication.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Replicate temporal CLEVR-N identity-preservation/IP results, PhaseTracker comparisons, and ablation orderings under matched budgets.

## Contract

- **Acceptance:** PhaseTracker reaches at least 3.0 IP scores and registered baseline/ablation ordering with predeclared effect-size intervals.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** PhaseTracker reaches at least 3.0 IP scores and registered baseline/ablation ordering with predeclared effect-size intervals.
- **Failure/abort boundary to formalize:** Conclusion/order reversal is D1; budget mismatch, data leakage, failed seed count, or training instability beyond abort threshold invalidates runs.
- **Raw artefact root:** `benchmarks/results/EXP-006/`
- **Record root:** `DOCS/experiments/EXP-006-temporal-binding-phasetracker-and-ablation-replication/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-006-temporal-binding-phasetracker-and-ablation-replication/report.md` with per-hypothesis CONFIRMED / REFUTED /
   INCONCLUSIVE verdict, effect size, CI, and exact evidence link.
2. Include side-by-side expected-vs-observed results, all aborts/exclusions,
   protocol deviations, exploratory findings, threats to validity, AI-assistance
   disclosure, and complete artefact index.
3. Trigger and close a D1 correction cycle before proceeding if a C1–C3
   published conclusion or any normative requirement is contradicted.
4. Obtain maintainer verification and announce the report for campaign synthesis.

## Prohibited

Spin, omitted runs, conclusion inflation, or proceeding with an unresolved D1.

## Exit gate

Approved report and any required correction-cycle evidence are committed; the
next registered experiment may begin.

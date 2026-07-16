# Session 0180 — EXP-006 / C3 E2: Review and approval — Temporal binding, PhaseTracker, and ablation replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-006 / C3  
**Session type:** E2 — Review and approval  
**Predecessor:** [0179 — Pre-registration](0179-exp006-e1-temporal-binding-phasetracker-and-ablation-replication.md)  
**Successor:** [0181 — Execution](0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md)  
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

- E1 draft is committed; no execution or result inspection has occurred.

## Expected work — independent review

1. Review falsifiability, quantitative decision rules, expected-result basis,
   failure/abort criteria, fairness controls, power/seed count, statistics,
   hardware feasibility, and artefact plan.
2. Resolve review findings before approval; log every pre-execution amendment.
3. Record maintainer name/date and set status APPROVED; freeze content at the
   instant E3 starts.

## Prohibited

Approval with missing expected results/failure conditions, or execution before
signed approval.

## Exit gate

Approved pre-registration is committed and frozen; E3 is authorized.

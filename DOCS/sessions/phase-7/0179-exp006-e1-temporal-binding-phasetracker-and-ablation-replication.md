# Session 0179 — EXP-006 / C3 E1: Pre-registration — Temporal binding, PhaseTracker, and ablation replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-006 / C3  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0178 — Report](0178-exp005-e5-dynamics-chimera-and-capacity-replication.md)  
**Successor:** [0180 — Review and approval](0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md)  
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-006-temporal-binding-phasetracker-and-ablation-replication/preregistration.md` from the template.
2. State quantitative, falsifiable H1…Hn; expected direction, magnitude/range,
   and basis independently for each hypothesis.
3. Convert the registered expectation and failure boundary above into exact
   decision rules, abort criteria, controls, sample/seed plan, alpha, effect
   sizes, CIs, multiple-comparison correction, analysis code/outputs, and budget.
4. Distinguish negative results from invalid/aborted runs and define how both are reported.

## Prohibited

No experiment execution, pilot outcome inspection, post-hoc hypothesis, or
analysis selected after seeing results.

## Exit gate

A complete DRAFT pre-registration is committed and handed to E2.

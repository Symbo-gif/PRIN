# Session 0181 — EXP-006 / C3 E3: Execution — Temporal binding, PhaseTracker, and ablation replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-006 / C3  
**Session type:** E3 — Execution  
**Predecessor:** [0180 — Review and approval](0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md)  
**Successor:** [0182 — Analysis](0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md)  
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

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-006-temporal-binding-phasetracker-and-ablation-replication/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

# Session 0182 — EXP-006 / C3 E4: Analysis — Temporal binding, PhaseTracker, and ablation replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-006 / C3  
**Session type:** E4 — Analysis  
**Predecessor:** [0181 — Execution](0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md)  
**Successor:** [0183 — Report](0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md)  
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

- E3 log closes execution; raw artefacts are immutable and manifest-verified.

## Expected work — registered analysis

1. Execute the frozen analysis plan exactly; calculate registered effect sizes,
   95% CIs, tests, corrections, and hypothesis decision rules.
2. Regenerate all tables/figures deterministically from raw JSON artefacts.
3. Put any unregistered analysis under an explicit `Exploratory` heading; it
   cannot alter confirmatory verdicts.
4. Preserve negative/inconclusive results and quantify protocol deviations and threats.

## Prohibited

Outcome-driven exclusions, new confirmatory tests, HARKing, p-hacking, or raw
artefact mutation.

## Exit gate

Reproducible analysis outputs and manifest are committed; hand off to E5.

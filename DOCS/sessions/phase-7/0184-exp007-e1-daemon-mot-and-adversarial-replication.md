# Session 0184 — EXP-007 / C3 E1: Pre-registration — Daemon, MOT, and adversarial replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-007 / C3  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0183 — Report](0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md)  
**Successor:** [0185 — Review and approval](0185-exp007-e2-daemon-mot-and-adversarial-replication.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Replicate daemon latency/control behavior, MOT metrics, and FGSM/PGD robustness outcomes.

## Contract

- **Acceptance:** MOT matches motmetrics/3.0 references, daemon p95 improves, and robustness direction/effect is preserved under registered attacks.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** MOT matches motmetrics/3.0 references, daemon p95 improves, and robustness direction/effect is preserved under registered attacks.
- **Failure/abort boundary to formalize:** Published conclusion reversal or F5 failure is D1; provider fallback ambiguity, attack-bound violation, or invalid MOT fixture aborts.
- **Raw artefact root:** `benchmarks/results/EXP-007/`
- **Record root:** `DOCS/experiments/EXP-007-daemon-mot-and-adversarial-replication/`

## Entry conditions

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-007-daemon-mot-and-adversarial-replication/preregistration.md` from the template.
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

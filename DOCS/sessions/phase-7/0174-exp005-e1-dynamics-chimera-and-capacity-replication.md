# Session 0174 — EXP-005 / C3 E1: Pre-registration — Dynamics, chimera, and capacity replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-005 / C3  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0173 — Report](0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md)  
**Successor:** [0175 — Review and approval](0175-exp005-e2-dynamics-chimera-and-capacity-replication.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Replicate chimera phase diagrams, coupling-topology effects, synchronization/capacity analyses, and tensor-derived conclusions.

## Contract

- **Acceptance:** Registered phase boundaries, effect directions, and capacity conclusions reproduce within predeclared statistical/numerical intervals.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** Registered phase boundaries, effect directions, and capacity conclusions reproduce within predeclared statistical/numerical intervals.
- **Failure/abort boundary to formalize:** A published conclusion reversal is D1; insufficient coverage, failed controls, or invalid chaotic-window diagnostics aborts inference.
- **Raw artefact root:** `benchmarks/results/EXP-005/`
- **Record root:** `DOCS/experiments/EXP-005-dynamics-chimera-and-capacity-replication/`

## Entry conditions

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-005-dynamics-chimera-and-capacity-replication/preregistration.md` from the template.
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

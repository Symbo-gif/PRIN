# Session 0176 — EXP-005 / C3 E3: Execution — Dynamics, chimera, and capacity replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-005 / C3  
**Session type:** E3 — Execution  
**Predecessor:** [0175 — Review and approval](0175-exp005-e2-dynamics-chimera-and-capacity-replication.md)  
**Successor:** [0177 — Analysis](0177-exp005-e4-dynamics-chimera-and-capacity-replication.md)  
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

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-005-dynamics-chimera-and-capacity-replication/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

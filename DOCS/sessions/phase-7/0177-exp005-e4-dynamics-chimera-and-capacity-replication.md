# Session 0177 — EXP-005 / C3 E4: Analysis — Dynamics, chimera, and capacity replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-005 / C3  
**Session type:** E4 — Analysis  
**Predecessor:** [0176 — Execution](0176-exp005-e3-dynamics-chimera-and-capacity-replication.md)  
**Successor:** [0178 — Report](0178-exp005-e5-dynamics-chimera-and-capacity-replication.md)  
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

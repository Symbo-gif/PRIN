# Session 0192 — EXP-008 / C4 E4: Analysis — Cross-platform and new-capability characterization

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-008 / C4  
**Session type:** E4 — Analysis  
**Predecessor:** [0191 — Execution](0191-exp008-e3-cross-platform-and-new-capability-characterization.md)  
**Successor:** [0193 — Report](0193-exp008-e5-cross-platform-and-new-capability-characterization.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Characterize Metal/wgpu, DirectML/VitisAI, compiler-free wheels, and expanded large-scale PRIN capabilities unavailable in 3.0.

## Contract

- **Acceptance:** Pre-registered capability-specific predictions hold with parity-safe behavior; platform support satisfies N2/N4/F5.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** Pre-registered capability-specific predictions hold with parity-safe behavior; platform support satisfies N2/N4/F5.
- **Failure/abort boundary to formalize:** Violation of N2/N4/F5 is D1; new-capability hypothesis misses are reported negative unless they breach a normative requirement; unavailable hardware is inconclusive, not silently skipped.
- **Raw artefact root:** `benchmarks/results/EXP-008/`
- **Record root:** `DOCS/experiments/EXP-008-cross-platform-and-new-capability-characterization/`

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

# Session 0189 — EXP-008 / C4 E1: Pre-registration — Cross-platform and new-capability characterization

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-008 / C4  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0188 — Report](0188-exp007-e5-daemon-mot-and-adversarial-replication.md)  
**Successor:** [0190 — Review and approval](0190-exp008-e2-cross-platform-and-new-capability-characterization.md)  
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-008-cross-platform-and-new-capability-characterization/preregistration.md` from the template.
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

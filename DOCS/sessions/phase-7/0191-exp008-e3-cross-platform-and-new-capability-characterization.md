# Session 0191 — EXP-008 / C4 E3: Execution — Cross-platform and new-capability characterization

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-008 / C4  
**Session type:** E3 — Execution  
**Predecessor:** [0190 — Review and approval](0190-exp008-e2-cross-platform-and-new-capability-characterization.md)  
**Successor:** [0192 — Analysis](0192-exp008-e4-cross-platform-and-new-capability-characterization.md)  
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

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-008-cross-platform-and-new-capability-characterization/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

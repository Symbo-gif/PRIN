# Session 0161 — EXP-002 / C1 E3: Execution — API, benchmark-result, and reproduction parity

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-002 / C1  
**Session type:** E3 — Execution  
**Predecessor:** [0160 — Review and approval](0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md)  
**Successor:** [0162 — Analysis](0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Public API mapping, legacy benchmark conclusion equivalence, and byte-comparable figure/table regeneration.

## Contract

- **Acceptance:** 175+ mapped symbols pass; all historical scientific conclusion orderings remain unchanged; 15 figures/11 tables match the manifest.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** 175+ mapped symbols pass; all historical scientific conclusion orderings remain unchanged; 15 figures/11 tables match the manifest.
- **Failure/abort boundary to formalize:** Missing symbols, changed scientific conclusions, or unexplained artefact mismatch is a D1; corrupt source artefacts abort.
- **Raw artefact root:** `benchmarks/results/EXP-002/`
- **Record root:** `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`

## Entry conditions

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

# Session 0156 — EXP-001 / C1 E3: Execution — Golden-trajectory numerical parity

**Status:** COMPLETE  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-001 / C1  
**Session type:** E3 — Execution  
**Predecessor:** [0155 — Review and approval](0155-exp001-e2-golden-trajectory-numerical-parity.md)  
**Successor:** [0157 — Analysis](0157-exp001-e4-golden-trajectory-numerical-parity.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Full corpus and hypothesis-fuzzed trajectory/metric/decomposition parity across supported CPU and accelerated paths.

## Contract

- **Acceptance:** All non-chaotic cases satisfy registered tolerances; chaotic cases preserve registered distributional conclusions; bit-level seeded repeatability holds.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** All non-chaotic cases satisfy registered tolerances; chaotic cases preserve registered distributional conclusions; bit-level seeded repeatability holds.
- **Failure/abort boundary to formalize:** Any unexplained tolerance breach, invariant violation, or cross-run seed mismatch is a D1; environment/schema/manifest failure aborts a run.
- **Raw artefact root:** `benchmarks/results/EXP-001/`
- **Record root:** `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/`

## Entry conditions

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

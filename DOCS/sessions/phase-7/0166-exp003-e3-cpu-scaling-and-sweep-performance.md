# Session 0166 — EXP-003 / C2 E3: Execution — CPU scaling and sweep performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-003 / C2  
**Session type:** E3 — Execution  
**Predecessor:** [0165 — Review and approval](0165-exp003-e2-cpu-scaling-and-sweep-performance.md)  
**Successor:** [0167 — Analysis](0167-exp003-e4-cpu-scaling-and-sweep-performance.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

CPU SIMD/rayon dynamics, simulation scaling through N=1M, and 16-core sweep throughput against 3.0 PyTorch.

## Contract

- **Acceptance:** Eligible CPU kernels achieve ≥2× and parameter sweeps ≥8× on controlled same-hardware comparisons without parity loss.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** Eligible CPU kernels achieve ≥2× and parameter sweeps ≥8× on controlled same-hardware comparisons without parity loss.
- **Failure/abort boundary to formalize:** Failure of a normative N1 target is a D1 unless amended; thermal throttling, background load, or parity failure aborts timing.
- **Raw artefact root:** `benchmarks/results/EXP-003/`
- **Record root:** `DOCS/experiments/EXP-003-cpu-scaling-and-sweep-performance/`

## Entry conditions

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-003-cpu-scaling-and-sweep-performance/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

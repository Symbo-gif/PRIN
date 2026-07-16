# Session 0171 — EXP-004 / C2 E3: Execution — GPU kernels and Torch bridge performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-004 / C2  
**Session type:** E3 — Execution  
**Predecessor:** [0170 — Review and approval](0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md)  
**Successor:** [0172 — Analysis](0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

CUDA/wgpu kernels, N=1M fused RK4, N=16K k-NN, fused discrete step, and trainable bridge overhead.

## Contract

- **Acceptance:** GPU workloads meet or exceed registered 3.0 baselines; training parity is ±10%; bridge overhead <5% with correctness intact.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** GPU workloads meet or exceed registered 3.0 baselines; training parity is ±10%; bridge overhead <5% with correctness intact.
- **Failure/abort boundary to formalize:** Normative target miss or correctness drift is a D1; unavailable backend, asynchronous timing error, or throttling aborts affected runs.
- **Raw artefact root:** `benchmarks/results/EXP-004/`
- **Record root:** `DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/`

## Entry conditions

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

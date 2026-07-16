# Session 0172 — EXP-004 / C2 E4: Analysis — GPU kernels and Torch bridge performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-004 / C2  
**Session type:** E4 — Analysis  
**Predecessor:** [0171 — Execution](0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md)  
**Successor:** [0173 — Report](0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md)  
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

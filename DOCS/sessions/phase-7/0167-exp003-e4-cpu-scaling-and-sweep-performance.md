# Session 0167 — EXP-003 / C2 E4: Analysis — CPU scaling and sweep performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-003 / C2  
**Session type:** E4 — Analysis  
**Predecessor:** [0166 — Execution](0166-exp003-e3-cpu-scaling-and-sweep-performance.md)  
**Successor:** [0168 — Report](0168-exp003-e5-cpu-scaling-and-sweep-performance.md)  
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

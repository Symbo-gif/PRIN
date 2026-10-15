# Session 0164 — EXP-003 / C2 E1: Pre-registration — CPU scaling and sweep performance

**Status:** BLOCKED — EXP-002 raised a campaign plan §10.4 D1 on H3 at E5 (session 0163, 2026-10-14 UTC); this session is released only after the four contingency correction sessions close and `EXP-002-r1` returns a non-reversal verdict (campaign plan §3.3, §10.4 items 2–5; see [`EXP-002/report.md`](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §8)
**Roadmap phase:** 7 — Experimentation campaign and stable release
**Execution unit:** EXP-003 / C2
**Session type:** E1 — Pre-registration
**Predecessor:** [0163 — Report](0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md)
**Successor:** [0165 — Review and approval](0165-exp003-e2-cpu-scaling-and-sweep-performance.md)
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-003-cpu-scaling-and-sweep-performance/preregistration.md` from the template.
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

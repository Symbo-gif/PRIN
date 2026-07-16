# Session 0187 — EXP-007 / C3 E4: Analysis — Daemon, MOT, and adversarial replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-007 / C3  
**Session type:** E4 — Analysis  
**Predecessor:** [0186 — Execution](0186-exp007-e3-daemon-mot-and-adversarial-replication.md)  
**Successor:** [0188 — Report](0188-exp007-e5-daemon-mot-and-adversarial-replication.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Replicate daemon latency/control behavior, MOT metrics, and FGSM/PGD robustness outcomes.

## Contract

- **Acceptance:** MOT matches motmetrics/3.0 references, daemon p95 improves, and robustness direction/effect is preserved under registered attacks.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** MOT matches motmetrics/3.0 references, daemon p95 improves, and robustness direction/effect is preserved under registered attacks.
- **Failure/abort boundary to formalize:** Published conclusion reversal or F5 failure is D1; provider fallback ambiguity, attack-bound violation, or invalid MOT fixture aborts.
- **Raw artefact root:** `benchmarks/results/EXP-007/`
- **Record root:** `DOCS/experiments/EXP-007-daemon-mot-and-adversarial-replication/`

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

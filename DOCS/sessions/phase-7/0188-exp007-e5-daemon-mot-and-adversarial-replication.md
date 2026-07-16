# Session 0188 — EXP-007 / C3 E5: Report — Daemon, MOT, and adversarial replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-007 / C3  
**Session type:** E5 — Report  
**Predecessor:** [0187 — Analysis](0187-exp007-e4-daemon-mot-and-adversarial-replication.md)  
**Successor:** [0189 — Pre-registration](0189-exp008-e1-cross-platform-and-new-capability-characterization.md)  
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

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-007-daemon-mot-and-adversarial-replication/report.md` with per-hypothesis CONFIRMED / REFUTED /
   INCONCLUSIVE verdict, effect size, CI, and exact evidence link.
2. Include side-by-side expected-vs-observed results, all aborts/exclusions,
   protocol deviations, exploratory findings, threats to validity, AI-assistance
   disclosure, and complete artefact index.
3. Trigger and close a D1 correction cycle before proceeding if a C1–C3
   published conclusion or any normative requirement is contradicted.
4. Obtain maintainer verification and announce the report for campaign synthesis.

## Prohibited

Spin, omitted runs, conclusion inflation, or proceeding with an unresolved D1.

## Exit gate

Approved report and any required correction-cycle evidence are committed; the
next registered experiment may begin.

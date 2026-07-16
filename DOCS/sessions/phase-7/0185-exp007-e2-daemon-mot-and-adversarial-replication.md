# Session 0185 — EXP-007 / C3 E2: Review and approval — Daemon, MOT, and adversarial replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-007 / C3  
**Session type:** E2 — Review and approval  
**Predecessor:** [0184 — Pre-registration](0184-exp007-e1-daemon-mot-and-adversarial-replication.md)  
**Successor:** [0186 — Execution](0186-exp007-e3-daemon-mot-and-adversarial-replication.md)  
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

- E1 draft is committed; no execution or result inspection has occurred.

## Expected work — independent review

1. Review falsifiability, quantitative decision rules, expected-result basis,
   failure/abort criteria, fairness controls, power/seed count, statistics,
   hardware feasibility, and artefact plan.
2. Resolve review findings before approval; log every pre-execution amendment.
3. Record maintainer name/date and set status APPROVED; freeze content at the
   instant E3 starts.

## Prohibited

Approval with missing expected results/failure conditions, or execution before
signed approval.

## Exit gate

Approved pre-registration is committed and frozen; E3 is authorized.

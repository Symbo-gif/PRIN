# Session 0186 — EXP-007 / C3 E3: Execution — Daemon, MOT, and adversarial replication

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-007 / C3  
**Session type:** E3 — Execution  
**Predecessor:** [0185 — Review and approval](0185-exp007-e2-daemon-mot-and-adversarial-replication.md)  
**Successor:** [0187 — Analysis](0187-exp007-e4-daemon-mot-and-adversarial-replication.md)  
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

- E2 approval is recorded; exact code SHA/environment and capacity are ready.

## Expected work — execution only

1. Execute committed benchrunner/experiment drivers exactly as registered.
2. Capture version/SHA, OS, CPU/GPU/VRAM, backend, dtype, config, seed, timing,
   and dependency environment in every append-only run artefact.
3. Maintain `DOCS/experiments/EXP-007-daemon-mot-and-adversarial-replication/log.md` with timestamps, operator, run IDs, anomalies,
   abort trips, and reruns; never delete an aborted run.
4. Stop and escalate on registered abort/D1 conditions; do not improvise protocol changes.

## Prohibited

Changing hypotheses/analysis, cherry-picking seeds, deleting failures, manual
artefact edits, or interpreting results during execution.

## Exit gate

All registered runs or justified aborts are logged; raw artefacts and manifest
are complete and immutable. Hand off to E4.

# Session 0049 — WP-013 S1: Coding — Continuous band networks and temporal propagation

**Status:** READY  
**Roadmap phase:** 2 — Advanced numerics and simulation  
**Execution unit:** WP-013  
**Session type:** S1 — Coding  
**Predecessor:** [0048 — Documentation](0048-wp012-s4-exponential-and-multi-rate-integrators.md)  
**Successor:** [0050 — Audit](0050-wp013-s2-continuous-band-networks-and-temporal-propagation.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement continuous delta/theta/gamma network hierarchy, PAC interactions, and complex-phasor temporal blending.

## Contract

- **Acceptance:** Band/temporal golden trajectories and capacity invariants pass; phase continuity and guards are property-tested.
- **Non-goals:** Trainable discrete bands or model training.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- Coding, Testing, Documentation, Benchmarking/Reproducibility, and Security provisions relevant to this scope

## Entry conditions

- The preceding S4 (or campaign synthesis for WP-039) is closed and committed.
- WP-013 scope, acceptance criteria, and non-goals have maintainer approval.
- No unresolved D1/D2 finding exists; any carried D4 is explicitly in this scope.

## Expected work

1. Establish failing/characterization tests before or in tandem with each behavior.
2. Implement only the declared scope; keep numerical authority in Rust and backend dispatch in `prin-kernels` where applicable.
3. Add unit, property, parity, gradient, kernel-equivalence, integration, security, and performance tests as the touched behavior requires.
4. Validate public inputs, use typed errors, document all public API, preserve deterministic Seed flow, and capture benchmark environments.
5. Record out-of-scope discoveries for a later WP; do not expand scope silently.

## Required evidence and outputs

- Code and tests in the same S1 commit range; ≥95% coverage on new/changed code.
- Relevant golden cases and invariants green at registered tolerances.
- `cargo fmt`, clippy `-D warnings`, Rust tests/rustdoc; ruff, mypy strict,
  interrogate, bandit, pytest, dependency audits as applicable.
- Benchmark before/after evidence for performance work; no scientific conclusion claims from pilots.
- An S1 handoff note mapping each acceptance criterion to evidence.

## Prohibited

- Deferred tests, weakened assertions/tolerances, undocumented public API, duplicated Python numerics, hidden RNG, unapproved `unsafe`, scope creep, or unregistered experimentation.

## Exit gate

All S1 gates are green and every acceptance criterion is evidence-mapped. Hand
off to the mandatory S2 audit; S1 may not self-certify completion.

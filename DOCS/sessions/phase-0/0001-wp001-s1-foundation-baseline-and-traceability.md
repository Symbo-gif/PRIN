# Session 0001 — WP-001 S1: Coding — Foundation baseline and traceability

**Status:** READY (bootstrap approval: Project Plan amendment #2)  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-001  
**Session type:** S1 — Coding  
**Predecessor:** Project execution start  
**Successor:** [0002 — Audit](0002-wp001-s2-foundation-baseline-and-traceability.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Create repository-state inventory, PRINet 3.0 public-API traceability matrix, metadata consistency checks, and baseline quality/security measurements.

## Contract

- **Acceptance:** Baseline automation is tested; every 3.0 module/public symbol has an assigned future WP; scaffold, CI, packaging, and governance gaps are recorded without implementing numerics.
- **Non-goals:** Numerical algorithms, performance conclusions, or golden data generation.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- Project Plan §6.1 bootstrap declaration and the archived Rebuild Planning Document §2/§6 inventory (there is no prior Project State Report)
- `DOCS/sessions/SESSION_REGISTER.md` and this first session brief
- Coding, Testing, Documentation, Benchmarking/Reproducibility, and Security provisions relevant to this scope

## Entry conditions

- This is the bootstrap exception: no preceding cycle/S4 exists.
- WP-001 scope, acceptance criteria, and non-goals are approved in Project Plan §6.1 (amendment #2).
- Existing scaffold/governance is treated as baseline input to inventory—not as pre-certified compliant work.
- No known unresolved D1/D2 has been suppressed; WP-001 must discover and record baseline gaps.

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

# Session 0105 — WP-027 S1: Coding — Trainable-stack integration and Phase 4 gate

**Status:** COMPLETE  
**Roadmap phase:** 4 — Trainable stack and Torch bridge  
**Execution unit:** WP-027  
**Session type:** S1 — Coding  
**Predecessor:** [0104 — Documentation](0104-wp026-s4-phasetracker-hybrid-baselines-and-allocation.md)  
**Successor:** [0106 — Audit](0106-wp027-s2-trainable-stack-integration-and-phase-4-gate.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Run controlled temporal CLEVR-N integration, full gradcheck, bridge profiling, serialization, and trainable API acceptance.

## Contract

- **Acceptance:** PhaseTracker reaches at least the registered 3.0 IP threshold in validation runs; gradchecks green; bridge overhead <5%; Phase 4 tag gate passes without treating pilot data as campaign evidence.
- **Non-goals:** Final scientific publication claims.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- Coding, Testing, Documentation, Benchmarking/Reproducibility, and Security provisions relevant to this scope
- **DV-021 and DV-005** (`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`) — both
  concretely checkpointed to this session (WP-025 S3-exec register review,
  2026-08-19) rather than left as an unassigned "future WP": DV-021 is the
  WP-025 Torch-bridge boundary-overhead gap this session's own acceptance
  criterion ("bridge overhead <5%") and mission text ("bridge profiling")
  already cover — a verified, evidence-backed performance investigation
  (`crates/prin-py/src/bindings/train.rs` commit `e720a24`) ruled out a
  Rust-side glue-code fix and narrowed the gap to
  `torch.autograd.Function.apply()`/`from_dlpack()` fixed dispatch cost, so
  this session's profiling should start from that evidence rather than
  re-deriving it. DV-005 is the CUDA Burn backend scope decision (no
  `cuda`/`wgpu` Burn feature exists in the workspace as of that review) —
  this Phase 4 gate is the natural point to decide whether it enters Phase 5
  scope, same consolidation pattern R24 used for the GPU CI runner strategy
  at WP-022 S1.

## Entry conditions

- The preceding S4 (or campaign synthesis for WP-039) is closed and committed.
- WP-027 scope, acceptance criteria, and non-goals have maintainer approval.
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

# Session 0141 — WP-036 S1: Coding — API completion, acceptance suite, and migration

**Status:** PLANNED  
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1  
**Execution unit:** WP-036  
**Session type:** S1 — Coding  
**Predecessor:** [0140 — Documentation](0140-wp035-s4-reproduction-pipeline-and-manifest.md)  
**Successor:** [0141A — sub-pass 1/5](0141A-wp036-s1a-freeze-machinery-and-reexport-surface.md)  
**Authority:** Project Plan §6/§8 and **amendments #31 and #32**; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Decomposition (amendment #32):** WP-036 S1 is executed as five sequential
> S1 coding sub-passes `0141A`–`0141E` (dependency-ordered), all feeding the
> single S2 audit `0142`. This brief remains the governing WP-036 S1 contract;
> its acceptance criteria are satisfied in aggregate across the sub-passes and
> verified whole at `0141E`. See
> [`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md).

> **Scope note (amendment #31):** WP-036 was split into WP-036 / WP-036B /
> WP-036C. This session delivers the **compatibility surface, freeze
> machinery, stubs, DV-012 bindings, and Migration Guide symbol table only**.
> The ~1,670-test acceptance-suite port is WP-036B (`0144A`–`0144D`) and
> WP-036C (`0144E`–`0144H`). See
> [`WP-036-execution-plan-and-decomposition.md`](WP-036-execution-plan-and-decomposition.md).

## Mission

Deliver the `prin` PRINet-3.0-compatible symbol surface (all 172
`prinet.__all__` symbols resolve from `prin`), `prin._deprecation` freeze and
deprecation machinery, `.pyi` stubs, the DV-012 `prin-py` sweep/engine PyO3
bindings, and the consolidated symbol-by-symbol Migration Guide table.
New-symbol unit/property/gradient tests only — no acceptance-suite port.

## Contract

- **Acceptance:** Every one of the 172 `prinet.__all__` symbols resolves from
  `prin` and passes a construct/callable smoke check; `verify_api_surface`
  regression test green against PRIN's RC1 `__all__`; the Migration Guide table
  is machine-checked against `DOCS/baselines/wp001_api_traceability.md`; no
  silent removals; no Python numerics (Coding Standards §2.1 — thin wrappers
  over Rust owners only). D-D (per-symbol disposition of the ~30 inherently
  GPU/Triton/CUDA symbols) is decided here subject to S2 audit veto.
- **Non-goals:** The acceptance-suite port (WP-036B/C); behavioral parity
  beyond smoke checks (that is proven by the ported suite); final documentation
  prose or release publishing; a CUDA Burn backend (DV-005 stays a scoping
  decision in the PSR).

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- Coding, Testing, Documentation, Benchmarking/Reproducibility, and Security provisions relevant to this scope

## Entry conditions

- The preceding S4 (or campaign synthesis for WP-039) is closed and committed.
- WP-036 scope, acceptance criteria, and non-goals have maintainer approval.
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

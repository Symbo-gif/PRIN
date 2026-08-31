# Session 0144E1 — WP-036B S1 (sub-pass 1/6): Core and utils strict port

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E — Coding (decomposed)](0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md)
**Successor:** [0144E2 — phases, hierarchical, and phase-to-rate](0144E2-wp036b-s1-phases-hierarchical-and-phase-to-rate-strict-port.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_core.py` (106 functions / 1,125 lines) and `test_utils.py`
(19 functions / 237 lines): **125 functions / 1,362 lines** total.

## Contract

- Copy both reference files under stable `tests/` names and adapt imports only.
  Assertions, expected values, parametrization, call order, and semantics remain
  unchanged (Testing Standards §1.1).
- Fix missing compatibility behavior in the owning Rust crate, exposed through
  thin PyO3/Python delegation; no Python numerics and no semantic-test adapter.
- Preserve the existing governed tolerance/backend-availability mechanisms;
  neither permits weakened assertions or unapproved skips.
- **Non-goals:** all `0144E2`–`0144E6` files, WP-036C clusters, public-symbol
  expansion, final S1 consolidation, S2 audit.

## Required reading

- The 0144E parent brief, amendment #35, and the adopted decomposition plan
- Testing Standards §1.1 and Development Workflow §3/§7
- Latest Project State Report and cumulative deviation ledger
- Running handoff `DOCS/experiments/0144E-wp036b-s1-handoff.md`
- The two reference files and applicable Rust/PyO3 compatibility owners

## Entry conditions

Amendment #35 is adopted; WP-036A is closed; no unresolved D1/D2 exists.

## Expected work

1. Copy the two files and make import-only adaptations.
2. Record a reference-vs-port diff proving no semantic test rewrite.
3. Run collection and execution; fix product behavior only through Rust-backed
   owners with same-pass regression/coverage evidence.
4. Run applicable local quality/security gates; ≥95% changed-code coverage.
5. Append file counts, results, annotations, guards, and discoveries to the
   running handoff.

## Prohibited

Assertion/value/parametrization rewrites, Python numerics, test-local behavior
shims, deferred tests, unapproved skips, undocumented tolerance changes, hidden
RNG, unapproved `unsafe`, scope creep, or push.

## Exit gate

All 125 assigned reference functions are accounted for and the sub-pass local
gate is green. Commit locally only; proceed to `0144E2`.

# Session 0144E3 — WP-036B S1 (sub-pass 3/6): Q2 and Q2-remaining strict port

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E2 — phases, hierarchical, and phase-to-rate](0144E2-wp036b-s1-phases-hierarchical-and-phase-to-rate-strict-port.md)
**Successor:** [0144E4 — q3_new, nn, and scalr_enhanced](0144E4-wp036b-s1-q3-nn-and-scalr-enhanced-strict-port.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_q2.py` (67 functions / 915 lines) and
`test_q2_remaining.py` (51 / 807): **118 functions / 1,722 lines** total.

## Contract

The copied tests receive import adaptations only; assertions and semantics are
unchanged. Product gaps are repaired through owning Rust implementations plus
thin PyO3/Python delegation, never through Python numerics or test-local shims.
Existing preserved-hazard tolerance and backend-availability rules remain the
only governed exceptions. **Non-goals:** other WP-036B/WP-036C files, public API
expansion, consolidation, or audit.

## Required reading

The 0144E brief; amendment #35/decomposition plan; Testing Standards §1.1;
latest PSR/ledger; running handoff; both reference files and applicable
Rust-backed compatibility owners.

## Entry conditions

`0144E2` is committed at its green local gate; no unresolved D1/D2 exists.

## Expected work

1. Copy/import-adapt both files; retain semantic-diff evidence.
2. Collect and execute all 118 source functions.
3. Repair implementation behavior in Rust-backed owners with same-pass tests
   and ≥95% changed-code coverage.
4. Run applicable local quality/security gates.
5. Append per-file counts/results/annotations/guards/discoveries to the handoff.

## Prohibited

Semantic-test rewrites, assertion weakening, Python numerics, test-local
behavior shims, deferred tests, unapproved skips/tolerances, hidden RNG,
unapproved `unsafe`, scope creep, or push.

## Exit gate

All 118 assigned functions are accounted for and the local gate is green.
Commit locally only; proceed to `0144E4`.

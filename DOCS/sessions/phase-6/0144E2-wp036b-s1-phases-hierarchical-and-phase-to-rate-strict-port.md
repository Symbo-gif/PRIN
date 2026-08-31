# Session 0144E2 — WP-036B S1 (sub-pass 2/6): Phases, hierarchical, and phase-to-rate strict port

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E1 — core and utils](0144E1-wp036b-s1-core-and-utils-strict-port.md)
**Successor:** [0144E3 — q2 and q2_remaining](0144E3-wp036b-s1-q2-and-q2-remaining-strict-port.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_phases.py` (30 functions / 389 lines),
`test_hierarchical.py` (43 / 604), and `test_phase_to_rate.py` (22 / 343):
**95 functions / 1,336 lines** total.

## Contract

- Copy the three files and adapt imports only; preserve every semantic assertion
  and expected value under Testing Standards §1.1.
- Missing behavior is rebuilt in Rust-backed owners and exposed via thin
  marshalling/delegation. This pass may complete the already-public standalone
  `DiscreteDeltaThetaGamma` binding assigned by amendment #33 when the strict
  tests first require it; that is compatibility behavior, not a new symbol.
- Existing hazard tolerance and backend-availability governance remains exact.
- **Non-goals:** test-body adaptation, later clusters, new public symbols,
  WP-036C, S2 audit.

## Required reading

The 0144E brief; amendment #35 and decomposition plan; Testing Standards §1.1;
latest PSR/ledger; running handoff; reference files; WP-036A handoff and the
Rust/PyO3 owners for phases, hierarchical layers, and phase-to-rate.

## Entry conditions

`0144E1` is committed at its green local gate; no unresolved D1/D2 exists.

## Expected work

1. Copy/import-adapt the three reference files and retain diff evidence.
2. Collect and execute all 95 functions.
3. Repair compatibility gaps through Rust-backed layers with same-pass tests,
   applicable gradcheck/parity evidence, and ≥95% changed-code coverage.
4. Run applicable local quality/security gates.
5. Append complete per-file evidence to the running handoff.

## Prohibited

Semantic-test rewrites, Python numerics, test-local compatibility algorithms,
deferred tests, weakened assertions, unapproved skips/tolerances, hidden RNG,
unapproved `unsafe`, scope creep, or push.

## Exit gate

All 95 assigned functions are accounted for and the local gate is green.
Commit locally only; proceed to `0144E3`.

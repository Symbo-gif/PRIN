# Session 0144E4 — WP-036B S1 (sub-pass 4/6): Q3-new, NN, and SCALR-enhanced strict port

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E3 — q2 and q2_remaining](0144E3-wp036b-s1-q2-and-q2-remaining-strict-port.md)
**Successor:** [0144E5 — hybrid and clevr_n](0144E5-wp036b-s1-hybrid-and-clevr-n-strict-port.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_q3_new.py` (31 functions / 389 lines), `test_nn.py`
(30 / 712), and `test_scalr_enhanced.py` (14 / 649):
**75 functions / 1,750 lines** total.

## Contract

Copy the three tests with import-only adaptation and unchanged assertions.
Rebuild missing model/optimizer compatibility through Rust-backed owners and
thin PyO3/Python delegation; do not implement numerics or semantic adapters in
Python/tests. Existing tolerance/backend rules remain exact. **Non-goals:**
other clusters, new symbols, consolidation, and S2 audit.

## Required reading

The 0144E brief; amendment #35/decomposition plan; Testing Standards §1.1;
latest PSR/ledger; running handoff; the three reference files; WP-036/WP-036A
handoffs and applicable `prin-train`/PyO3 owners.

## Entry conditions

`0144E3` is committed at its green local gate; no unresolved D1/D2 exists.

## Expected work

1. Copy/import-adapt the three files; retain semantic-diff evidence.
2. Collect and execute all 75 source functions.
3. Repair Rust-backed compatibility behavior with same-pass regression,
   parity/gradcheck where applicable, and ≥95% changed-code coverage.
4. Run applicable local quality/security gates.
5. Append complete per-file evidence to the handoff.

## Prohibited

Semantic-test rewrites, assertion weakening, Python numerics, test-local
algorithms, deferred tests, unapproved skips/tolerances, hidden RNG, unapproved
`unsafe`, scope creep, or push.

## Exit gate

All 75 assigned functions are accounted for and the local gate is green.
Commit locally only; proceed to `0144E5`.

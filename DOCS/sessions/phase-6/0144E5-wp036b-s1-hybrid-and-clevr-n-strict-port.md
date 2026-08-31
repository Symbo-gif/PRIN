# Session 0144E5 — WP-036B S1 (sub-pass 5/6): Hybrid and CLEVR-N strict port

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E4 — q3_new, nn, and scalr_enhanced](0144E4-wp036b-s1-q3-nn-and-scalr-enhanced-strict-port.md)
**Successor:** [0144E6 — subconscious and consolidation](0144E6-wp036b-s1-subconscious-and-consolidation.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_hybrid.py` (19 functions / 907 lines) and `test_clevr_n.py`
(17 / 403): **36 functions / 1,310 lines** total, including resolution of the
verified collection blocker `ModuleNotFoundError: benchmarks.clevr_n`.

## Contract

- Copy/import-adapt both reference files; assertions and semantics remain
  unchanged under Testing Standards §1.1.
- Rebuild the missing `benchmarks.clevr_n` compatibility behavior through the
  appropriate Rust-backed implementation and thin support/delegation layer so
  all 17 source tests collect. Do not patch the copied test around the import.
- Repair all other compatibility gaps in Rust-backed owners. No Python numerics
  or test-local semantic adapter.
- **Non-goals:** subconscious/consolidation, WP-036C, new public symbols, audit.

## Required reading

The 0144E brief; amendment #35/decomposition plan; Testing Standards §1.1;
latest PSR/ledger; running handoff; both reference files; current benchmark,
hybrid, CLEVR-N, `prin-train`, and PyO3 ownership paths.

## Entry conditions

`0144E4` is committed at its green local gate; no unresolved D1/D2 exists.

## Expected work

1. Copy/import-adapt both files and retain semantic-diff evidence.
2. Restore Rust-backed CLEVR-N compatibility support and prove all 17
   `test_clevr_n.py` functions collect.
3. Execute all 36 functions and repair product behavior through owning layers.
4. Run same-pass tests, ≥95% changed-code coverage, and applicable local
   quality/security gates.
5. Append blocker resolution and per-file evidence to the handoff.

## Prohibited

Catching/removing the missing import in the test, semantic-test rewrites,
assertion weakening, Python numerics, deferred tests, unapproved skips or
tolerances, hidden RNG, unapproved `unsafe`, scope creep, or push.

## Exit gate

All 36 assigned functions collect and are accounted for; local gate green.
Commit locally only; proceed to `0144E6`.

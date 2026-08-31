# Session 0144E6 — WP-036B S1 (sub-pass 6/6): Subconscious strict port and consolidation

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144E5 — hybrid and clevr_n](0144E5-wp036b-s1-hybrid-and-clevr-n-strict-port.md)
**Successor:** [0144F — Audit](0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#35, and [`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port `test_subconscious.py` (**49 functions / 1,090 lines**) and
consolidate the complete 13-file WP-036B S1 port: **498 functions / 8,570
reference lines** across `0144E1`–`0144E6`.

## Contract

- Copy/import-adapt `test_subconscious.py`; assertions and semantics remain
  unchanged. Repair compatibility behavior through Rust-backed owners and thin
  PyO3/Python delegation only.
- Reconcile every reference file/function against the source inventory. The
  initial 481 collected + `test_clevr_n` import error is discrepancy evidence,
  not authority to omit any of the 498 source functions.
- Run the complete ported 13-file subset and retain reference-vs-port diff
  evidence proving import-only adaptation, except separately identified
  governed hazard annotations/backend guards.
- Finalize the running S1 handoff: per-file source count, collected/executed
  result, tolerance annotations, availability guards, compatibility fixes,
  and out-of-scope discoveries.
- **Non-goals:** S2 self-certification, WP-036C, final S4 prose/release work.

## Required reading

The 0144E brief; amendment #35/decomposition plan; Testing Standards §1.1;
latest PSR/ledger; all prior sub-pass handoff entries; all 13 reference/ported
file diffs; applicable subconscious Rust/PyO3 owners.

## Entry conditions

`0144E1`–`0144E5` are committed at green local gates; `test_clevr_n.py` now
collects all 17 source functions; no unresolved D1/D2 exists.

## Expected work

1. Strict-port and execute the 49 subconscious functions.
2. Repair product behavior only through Rust-backed compatibility layers with
   same-pass tests and ≥95% changed-code coverage.
3. Run complete collection/execution for all 13 ported files and applicable
   full Rust/Python quality and security gates.
4. Diff all copied tests against reference and account for all 498 functions.
5. Complete `DOCS/experiments/0144E-wp036b-s1-handoff.md` and hand off the
   contiguous range to `0144F`.

## Prohibited

Semantic-test rewrites, assertion weakening/deletion, Python numerics,
test-local behavior shims, missing-function write-off, deferred tests,
unapproved skips/tolerances, hidden RNG, unapproved `unsafe`, scope creep,
push, or S1 self-certification.

## Exit gate

All 498 reference functions are evidence-mapped; the complete strict-ported
subset and local gates are green. Commit locally only. Hand off
`0144E`+`0144E1`–`0144E6` to the mandatory read-only S2 audit `0144F`.

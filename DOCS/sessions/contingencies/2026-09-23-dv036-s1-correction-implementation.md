# DV-036 S1 — Correction implementation

**Status:** COMPLETE (local stage)\
**Triggering deviation:** `DV036-F1 / DV036-F2`  
**Blocked numbered session:** `0156`

## Expectation

Declare a correction WP scoped only to the triggering deviation; reproduce it with a failing regression/parity test, implement the root-cause fix with tests in tandem, and run all affected gates.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Approved scope and acceptance

MichaelMaillet, 2026-09-23 UTC: same-job fixed-reference correction approved;
hotfix-branch push, PR, and nightly testing authorized. Campaign plan §11.6
and amendment 3 govern. Sources: `.github/workflows/nightly.yml`,
`tools/check_bench_regression.py`, and regression tests. No oscillator,
EXP-001 driver, hypothesis, tolerance, or campaign sample change.

DV036-F1 (D2): stale cross-host cached benchmark evidence is not a controlled
like-for-like comparison (Benchmarking Standards §2.2). DV036-F2 (D2): the
checker accepts missing/malformed/non-finite or unmatched evidence as a pass
(Coding Standards §1.4; Testing Standards §2 regression-gate obligation).

Acceptance: fixed reference SHA and candidate measured on one host with
matched toolchains/dependencies; all eight Rust targets and Python benchmark
selection retained; 10% threshold unchanged; fail-closed completeness tests;
>=95% changed-code coverage; affected local/security gates green; fresh
whole-nightly success required for closure. No automatic baseline promotion.
No main merge or E3 authorization is claimed by implementation completion.

**Evidence:** implementation commit `8bcea55`; see the [correction audit](../../audits/2026-09-23-dv036-nightly-correction-audit.md) and the [EXP-001 execution log](../../experiments/EXP-001-golden-trajectory-numerical-parity/log.md).

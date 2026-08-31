# WP-036B S1 (session 0144E) — execution plan and decomposition

**Status:** ADOPTED (2026-08-31, MichaelMaillet). Recorded as **Plan
amendment #35**. Maintainer selected **Decompose strict port**: six sequential
S1 coding sub-passes `0144E1`–`0144E6` feed the single S2 audit `0144F`;
Testing Standards §1.1 remains literal — adapt imports only and leave assertions
unchanged — while missing compatibility behavior is rebuilt through Rust-backed
layers rather than hidden by semantic test rewrites. Not itself an execution
contract; the governing contracts are the 0144E brief, amendments #31/#33/#35,
and the six sub-pass briefs `0144E1`–`0144E6`.

**Prepared for:** session 0144E (WP-036B S1 — acceptance-suite port: core,
dynamics, model stack, subconscious).  
**Author:** AI pair.  
**Date:** 2026-08-31.  
**Authority:** Project Plan §6/§8 and amendments #31/#33; Development Workflow
and Audit Standards §7; Testing Standards §1.1.

---

## 1. Why this document exists

The prospective 0144E brief estimated the 13 assigned PRINet 3.0 reference
files at approximately 805 `def test_` functions and treated WP-036B as one S1
coding session. Repository verification at session start established a different
but still oversized contract: **498 test functions across 8,570 lines**.
Collect-only reached **481 collected tests**, then `test_clevr_n.py` failed
during import because `benchmarks.clevr_n` is missing.

The count correction does not reduce the normative contract. Testing Standards
§1.1 says that the PRINet 3.0 suite defines the public API and that a port adapts
imports only, never weakens assertions. A single 8,570-line strict port plus the
Rust-backed compatibility work exposed by collection/execution is not a
reviewable S1 range. Continuing in one pass would force scope creep (D3 under
Development Workflow §7), deferred tests, or semantic edits to the acceptance
suite. The approved response is to decompose the strict port, not relax it.

## 2. Verified scope inventory

Reference root:
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/`.

| Reference file | `def test_` | Lines | Assigned sub-pass |
|---|---:|---:|---|
| `test_core.py` | 106 | 1,125 | `0144E1` |
| `test_utils.py` | 19 | 237 | `0144E1` |
| `test_phases.py` | 30 | 389 | `0144E2` |
| `test_hierarchical.py` | 43 | 604 | `0144E2` |
| `test_phase_to_rate.py` | 22 | 343 | `0144E2` |
| `test_q2.py` | 67 | 915 | `0144E3` |
| `test_q2_remaining.py` | 51 | 807 | `0144E3` |
| `test_q3_new.py` | 31 | 389 | `0144E4` |
| `test_nn.py` | 30 | 712 | `0144E4` |
| `test_scalr_enhanced.py` | 14 | 649 | `0144E4` |
| `test_hybrid.py` | 19 | 907 | `0144E5` |
| `test_clevr_n.py` | 17 | 403 | `0144E5` |
| `test_subconscious.py` | 49 | 1,090 | `0144E6` |
| **Total** | **498** | **8,570** | — |

The initial `pytest --collect-only` discrepancy is explicit evidence, not a
scope reduction: **481 tests collected plus one collection error** in
`test_clevr_n.py`, caused by the missing `benchmarks.clevr_n` import. The source
inventory above remains authoritative for expected function counts; every one
of the 498 reference functions remains assigned.

## 3. Adopted strategic disposition — Decompose strict port

1. **Strict test text.** Each reference test is copied under a stable `tests/`
   name. Changes to the semantic test body are prohibited. Only imports are
   adapted from `prinet` to `prin` (and to the corresponding PRIN-owned support
   path). Assertions, expected values, parametrization, call order, and test
   meaning stay unchanged.
2. **Compatibility gaps are implementation work.** A failure or collection gap
   caused by absent behavior is fixed in the owning Rust crate and exposed via
   a thin PyO3/Python delegation layer. No Python numerical reimplementation is
   introduced. Completing the already-public `DiscreteDeltaThetaGamma` binding
   and rebuilding support needed by `benchmarks.clevr_n` are examples of
   compatibility behavior, not permission to rewrite tests.
3. **No semantic-test rewrite.** Adapters that translate API shape belong in
   the compatibility layer, not inside copied acceptance tests. A test that
   would require more than import adaptation stays failing until the product
   behavior is made compatible or an out-of-scope discovery is governed.
4. **Existing exception governance is unchanged.** A tolerance change is
   permitted only when attributable solely to amendments #14/#16/#17/#25 and
   must carry a per-test annotation plus Parity Report entry. GPU/Triton-only
   cases follow the reference's availability guard. Neither mechanism permits
   assertion deletion, weakened logic, or an unapproved skip.
5. **One audit range.** Each sub-pass commits at its own green local gate. The
   contiguous `0144E`+`0144E1`–`0144E6` range feeds the single mandatory S2
   audit `0144F`; push cadence remains amendment #28.

## 4. Adopted decomposition

| Sub-pass | Reference files | Functions | Lines | Focus |
|---|---|---:|---:|---|
| `0144E1` | core + utils | 125 | 1,362 | foundational API and utility behavior |
| `0144E2` | phases + hierarchical + phase-to-rate | 95 | 1,336 | dynamics composition and the standalone `DiscreteDeltaThetaGamma` binding where first required |
| `0144E3` | q2 + q2_remaining | 118 | 1,722 | second-quarter compatibility cluster |
| `0144E4` | q3_new + nn + scalr_enhanced | 75 | 1,750 | model/optimizer compatibility cluster |
| `0144E5` | hybrid + clevr_n | 36 | 1,310 | hybrid/CLEVR-N behavior, including the missing `benchmarks.clevr_n` compatibility support |
| `0144E6` | subconscious + consolidation | 49 | 1,090 | controller cluster, complete 498-test accounting, full subset gate, S1 handoff |

Every pass runs the relevant copied subset and all tests for any changed
first-party implementation, keeps changed code at ≥95% line coverage, and runs
applicable Rust/Python quality and security gates. Snyk Code is required for
modified supported first-party source; dependency scans run only if manifests
change. This governance-only amendment does not itself execute those coding
gates.

## 5. Amendment #35 recording

Amendment #35 adds six planned sub-sessions without renumbering the integer
sequence or the surrounding `0144A`–`0144L` block. The link chain becomes:

`0144E` → `0144E1` → `0144E2` → `0144E3` → `0144E4` → `0144E5` → `0144E6` → `0144F`.

Planned session count changes from **220 to 226**. `0144F` audits the aggregate
strict port and independently diffs every copied test against its reference,
allowing only governed import adaptations and explicitly recorded tolerance or
backend-availability annotations.

## 6. Risks and controls

- **R1 — collection count can obscure uncollected tests.** Control: retain the
  per-file source count table and reconcile all 498 functions in `0144E6`; do
  not treat 481 as the contract total.
- **R2 — compatibility adapters drift into Python numerics.** Control: numerical
  authority remains in Rust; Python/PyO3 layers are thin delegation and
  marshalling only; S2 inspects ownership.
- **R3 — pressure to edit tests after failures.** Control: copied-file diff is a
  per-pass gate and an explicit `0144F` audit action. Product behavior changes,
  not semantic-test changes.
- **R4 — `test_clevr_n` remains invisible while import is broken.** Control:
  `0144E5` owns the missing `benchmarks.clevr_n` compatibility support and must
  demonstrate successful collection of all 17 source functions.
- **R5 — consolidation omits earlier failures.** Control: `0144E6` runs the
  complete 13-file ported subset and produces a file-by-file accounting table
  for all 498 functions, tolerances, backend guards, and discoveries.

## 7. Next step

Execute `0144E1` (core + utils). Preserve Testing Standards §1.1 literally,
rebuild any missing compatibility behavior through Rust-backed layers, append
evidence to `DOCS/experiments/0144E-wp036b-s1-handoff.md`, and commit locally
only when the sub-pass gate is green.

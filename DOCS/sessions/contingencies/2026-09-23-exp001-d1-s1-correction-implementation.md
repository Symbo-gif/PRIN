# EXP-001 D1 S1 — Correction implementation

**Status:** OPEN — not started\
**Triggering deviation:** `EXP-001 H1/H2a REFUTED` (campaign plan §10.4 D1) and
`EXP001-E5-F1` (D1)\
**Blocked numbered session:** `0159` (EXP-002 E1), and every experiment
downstream of EXP-001 in campaign plan §3.2, plus `0194`\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC\
**Governing record:** [EXP-001 E5 report](../../experiments/EXP-001-golden-trajectory-numerical-parity/report.md)
§7–§8; [E4 analysis](../../experiments/EXP-001-golden-trajectory-numerical-parity/analysis.md);
[E3 log](../../experiments/EXP-001-golden-trajectory-numerical-parity/log.md)

## Expectation

Declare a correction WP scoped only to the triggering deviation; reproduce it
with a failing regression/parity test, implement the root-cause fix with tests
in tandem, and run all affected gates.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## What triggered this cycle

Two independent D1 conditions, both raised on committed, manifest-verified
evidence at code SHA `6b9d6b6`:

1. **H1 `REFUTED`** — 19 of 504 golden-corpus cases breach the registered
   trajectory/metric tolerances when the `prin` Rust core is re-integrated
   from each case's stored initial state. Worst absolute error `2.008567e-07`;
   17 of 19 failures are `stuart_landau/full`.
2. **H2a `REFUTED`** — 103 of 1,000 hypothesis-fuzzed cases breach within the
   registered shadowing horizon (steps `0..min(20, n_steps)`), in 12 of 14
   grid cells. **33 of those breach at or above `1e-3`**, the largest
   `2.654853e+01` — a magnitude population H1 does not contain.
3. **`EXP001-E5-F1`** — the `parity` CI job's
   `test_corpus_exhaustive_differential_parity` regenerates each corpus case
   with **PRINet 3.0**, not with PRIN, so it is a reference self-consistency
   check; no CI gate integrates PRIN's dynamics over the **full** corpus (all
   504 cases) and compares the trajectories. The only gate that runs PRIN
   against corpus trajectories at all,
   `tests/test_exp001_driver.py::TestCorpusParity::test_representative_cases_within_tolerance`,
   covers 4 representative cases, **none of which is among H1's 19 breaching
   cases** — it is green while H1 is `REFUTED`, which is the coverage gap
   itself, not a counterexample to it. The Parity Report's published
   VALIDATION claim to the contrary is unsupported. Evidence:
   [`EVIDENCE/0158-exp001-e5-parity-gate-coverage.json`](../../../EVIDENCE/0158-exp001-e5-parity-gate-coverage.json)
   (4/4 H1-failing cases: CI comparison PASS, PRIN-vs-corpus breach).

**No root cause is claimed by E3, E4, or E5.** Establishing one is this
session's work.

## Scope (to be approved by the maintainer before work starts)

In scope:

- Reproduce both refutations as failing tests before any fix lands
  (Development Workflow §3; Testing Standards §1.3): at minimum one failing
  `prin`-vs-corpus case per breaching grid cell, and one failing case drawn
  from H2a's large-magnitude population.
- Determine and fix the root cause of the divergence, **or** establish under
  campaign plan §10.4 item 3 that the PRINet 3.0 conclusion is itself the
  defective side — which requires an EMA-style mathematical audit claim,
  Z3/SymPy-verified where applicable, and is not discharged by inspection.
- Close `EXP001-E5-F1`: add a real **full-corpus** PRIN-vs-corpus differential
  gate to the `parity` CI job (the existing 4-case
  `tests/test_exp001_driver.py::TestCorpusParity` gate is the subset this
  finding shows is insufficient, not a substitute), correct
  `parity/test_parity_differential.py::test_corpus_exhaustive_differential_parity`'s
  docstring, and correct the Parity Report text the E5 erratum flags.
- Coding Standards §6: Snyk Code on new/modified first-party source; Snyk Open
  Source and the ecosystem-native audits on any dependency change; local gate
  (`ruff`, `ruff format`, `mypy --strict`, `interrogate`, `bandit`, coverage)
  on changed code.

Out of scope (explicitly, to keep the correction bounded):

- Any change to EXP-001's frozen pre-registration, its committed raw
  artefacts, its E4 analysis outputs, or their digests. The EXP-001 record is
  immutable and stays as issued (campaign plan §10.4 item 4).
- Any campaign experiment execution. `EXP-001-r1` is authorized by S4, not
  here.
- Any performance, feature, or refactoring work unrelated to the two D1s.

## Acceptance

- Both refutations reproduced by committed failing tests **before** the fix.
- Root cause identified with evidence, or the §10.4 item 3 alternative
  established to its own stricter standard.
- A PRIN-vs-corpus differential gate runs in the `parity` workflow and is red
  on the pre-fix tree and green on the post-fix tree, with that transition
  recorded.
- All affected gates green locally; CI remains the authoritative merge gate.
- Neither implementation completion nor a green local run authorizes the merge,
  `EXP-001-r1`, or the release of session `0159`.

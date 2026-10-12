# benchmarks/campaign/ — Phase 7 campaign experiment drivers

Campaign-plan §7 drivers that collect the pre-registered evidence for the C1
golden-trajectory parity experiments. These drivers write raw run artefacts
(`RUN-<UTC>-<SHA>-<label>/` directories with a `campaign-metadata.json`
sidecar and a per-run `manifest.json`) under `benchmarks/results/`.

## Drivers

| File | Experiment record | Role |
|---|---|---|
| `exp001_driver.py` | [`EXP-001`](../../DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/README.md) (E5 reported 2026-09-23; H1/H2a `REFUTED`, D1 raised) | Predecessor driver and the shared primitives both records build on (run-directory contract, campaign-metadata writer, environment capture, closure gate). Its default behavior is unchanged: `check_run_complete` still expects `EXP-001` unless a caller explicitly names another identity via `expected_exp_id`. |
| `exp001_r1_driver.py` | [`EXP-001-r1`](../../DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/README.md) — **E2 follow-up H4 method APPROVED 2026-09-29 UTC; NOT FROZEN; E3 BLOCKED on DV-043/DV-044 and clean M/R source identity** | New, separately identified correction re-run protocol (positive DV-007 explanations, fixed ill-conditioned-case characterization, provenance pins, storage caps). |
| `exp002_driver.py` | [`EXP-002`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/README.md) — **APPROVED at E2 (2026-10-12); E3 (0161) READY under the e2-review.md entry checklist** | Lead-authored E1 collection driver for the API census (H1), the 62-predicate historical-conclusion census (H2), and the three publication reproduction arms (H3/H4). Five registered CLI modes (`api`, `conclusions`, `reference`, `prin`, `repeatability`); refuses to run while the pre-registration is DRAFT. Regression tests: [`tests/test_exp002_driver.py`](../../tests/test_exp002_driver.py) (synthetic fixtures only). |

`EXP-001-r1` E3 execution must not run before the remaining gates
recorded in the pre-registration close: the follow-up wgpu H4 method was
approved 2026-09-29 UTC (`e2-review.md` §8), but DV-043's merge/CI/nightly
closure, DV-044's governed correction, and the clean M/R execution
identity are still open. The new wgpu leg has mocked synthetic tests
([`tests/test_exp001_r1_driver.py`](../../tests/test_exp001_r1_driver.py))
and a live single-configuration synthetic N=8 wgpu dispatch smoke on H1.
The previously registered predecessor H4 regression tests also run
through their original driver; no EXP-001-r1 E3 run has executed.

**Currency note (2026-10-11, session 0159):** `exp002_driver.py` is the
lead-authored E1 collection driver for EXP-002. The pre-registration is
**DRAFT** — the driver refuses admission until 0160 records dated
maintainer scientific approval — and no EXP-002 execution, pilot, or real
reference-input collection has run. Its regression coverage uses synthetic
fixtures only (fake `prin` namespaces, fabricated conclusion JSON, mocked
renderers/snapshots/git); see `tests/test_exp002_driver.py`. The
lead-authored maintainer-review packet for 0160 is
[`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review-packet.md`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review-packet.md)
(PREPARED FOR REVIEW — NOT APPROVED). *PR #33 review round (2026-10-11,
`DOCS/audits/PR033-multi-review-audit.md`):* tables are now compared after
CRLF-to-LF canonicalization and PDFs after removing the four registered Info
entries (both pending E2 approval); closure re-derives pre-registration
provenance from git and checks each mode's observation schema; reservation
never leaves an unrecorded RUN directory; admission covers the whole
checkout. The driver still refuses to run while the protocol is DRAFT.
*Session 0160 (2026-10-12):* the protocol is APPROVED at E2 and both
comparison amendments were approved; the driver also records a pre-exposure
`sensitivity_sha256` per publication file (E2 decision 9). It admits only
the APPROVED, committed protocol on a clean checkout, and E3 (0161) runs
only under the `e2-review.md` §8 entry checklist.

**Dated delta for the `EXP-001-r1` row above (2026-10-11, session 0159):**
the row's "E3 BLOCKED" wording is its point-in-time record. Since then
DV-043 closed (merged `9b79d2e`, PR #26, with required CI green and a
green nightly `bench-regression`), the `EXP-001-r1` E5 report was accepted
by the maintainer on 2026-09-29 UTC (all five hypotheses `CONFIRMED`,
non-reversal verdict — releasing session 0159 per campaign plan §10.4
item 5), and the r1 range merged to `main` as **PR #28**
`32cfed8a0b4d915a04e18efbfadd146a2ecb7e32` (historical merge-check capture:
`EVIDENCE/ea007/exp001-r1-merge-ci-green.log`). The row is retained
unedited as the state at writing.

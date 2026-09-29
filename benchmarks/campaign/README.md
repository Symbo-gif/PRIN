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

`EXP-001-r1` E3 execution must not run before the remaining gates
recorded in the pre-registration close: the follow-up wgpu H4 method was
approved 2026-09-29 UTC (`e2-review.md` §8), but DV-043's merge/CI/nightly
closure, DV-044's governed correction, and the clean M/R execution
identity are still open. The new wgpu leg has mocked synthetic tests
([`tests/test_exp001_r1_driver.py`](../../tests/test_exp001_r1_driver.py))
and a live single-configuration synthetic N=8 wgpu dispatch smoke on H1.
The previously registered predecessor H4 regression tests also run
through their original driver; no EXP-001-r1 E3 run has executed.

# benchmarks/campaign/ — Phase 7 campaign experiment drivers

Campaign-plan §7 drivers that collect the pre-registered evidence for the C1
golden-trajectory parity experiments. These drivers write raw run artefacts
(`RUN-<UTC>-<SHA>-<label>/` directories with a `campaign-metadata.json`
sidecar and a per-run `manifest.json`) under `benchmarks/results/`.

## Drivers

| File | Experiment record | Role |
|---|---|---|
| `exp001_driver.py` | [`EXP-001`](../../DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/README.md) (E5 reported 2026-09-23; H1/H2a `REFUTED`, D1 raised) | Predecessor driver and the shared primitives both records build on (run-directory contract, campaign-metadata writer, environment capture, closure gate). Its default behavior is unchanged: `check_run_complete` still expects `EXP-001` unless a caller explicitly names another identity via `expected_exp_id`. |
| `exp001_r1_driver.py` | [`EXP-001-r1`](../../DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/README.md) — **E1 COMPLETE, DRAFT; E2 review pending** | New, separately identified correction re-run protocol (positive DV-007 explanations, fixed ill-conditioned-case characterization, provenance pins, storage caps). |

`EXP-001-r1` E3 execution must not run before E2 approval and resolution of
the required wgpu-coverage and shared-storage budget gates recorded in the
draft pre-registration. The E1 state is validated only by synthetic tests,
[`tests/test_exp001_r1_driver.py`](../../tests/test_exp001_r1_driver.py),
which stub both numerical implementations; no registered workload was
executed.

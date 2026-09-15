# tests/ — pytest acceptance suite

The PRIN pytest suite (51 files, ~3,000 tests) is the **acceptance contract**
for PRIN: it defines the public API. The WP-036B + WP-036C strict ports have
adapted 37 PRINet 3.0 reference files (1,670 `def test_` functions, ~24,000
reference lines) with import-only changes (`prinet.*` → `prin.*`). Assertions
remain unchanged except for separately governed post-port hardening documented
in the Deferred Validation Register (Testing Standards §1.1).

## WP-036B ported acceptance suite (13 files, 498 tests)

| Port file | `def test_` | Passed | Skipped | Reference guard |
|---|---:|---:|---:|---|
| `test_acceptance_core.py` | 106 | 106 | 0 | — |
| `test_acceptance_utils.py` | 19 | 19 | 0 | — |
| `test_acceptance_phases.py` | 30 | 30 | 0 | — |
| `test_acceptance_hierarchical.py` | 43 | 41 | 2 | 2 CUDA `skipif` (2 `@pytest.mark.gpu`) |
| `test_acceptance_phase_to_rate.py` | 22 | 21 | 1 | 1 CUDA `skipif` (1 `@pytest.mark.gpu`) |
| `test_acceptance_q2.py` | 67 | 65 | 2 | 1 CUDA `skipif` (1 `@pytest.mark.gpu`) + 1 DV-030 `skip` |
| `test_acceptance_q2_remaining.py` | 51 | 48 | 3 | 2 CUDA `skipif` (2 `@pytest.mark.gpu`) + 1 `skip` (`@pytest.mark.gpu`) |
| `test_acceptance_q3_new.py` | 31 | 31 | 0 | — |
| `test_acceptance_nn.py` | 30 | 30 | 0 | — |
| `test_acceptance_scalr_enhanced.py` | 14 | 14 | 0 | — |
| `test_acceptance_hybrid.py` | 19 | 19 | 0 | — |
| `test_acceptance_clevr_n.py` | 17 | 17 | 0 | — |
| `test_acceptance_subconscious.py` | 49 | 48 | 1 | 1 `psutil`-absent |
| **Total** | **498** | **489** | **9** | 7 `gpu` + 1 DV-030 `skip` + 1 psutil |

WP-036G S1 removed DV-032's quarantine from
`test_no_gpu_throughput_regression` after hardening it with fixed work, warm-up,
and a seven-sample relative-median gate. The original `<1.30` acceptance limit
is unchanged; three consecutive isolated runs passed on the maintainer host.

**Marker policy:** Tests that require a GPU carry both
`@pytest.mark.skipif(not torch.cuda.is_available(), ...)` (the reference guard)
**and** `@pytest.mark.gpu`. On a CPU-only host the `skipif` fires and the test
is skipped; on the self-hosted CUDA runner (`PRIN-GPU-Runner`, selected by
`-m gpu`) the test runs for real. Seven of the original eight CUDA guards are
activated; the eighth (`test_sparse_vram_subquadratic`) carries an explicit
`@pytest.mark.skip(reason="deferred to DV-030 ...")` because the sparse-vs-full
VRAM ratio cannot be verified while the coupling matrix lives in Rust host
memory (DV-030). WP-036E (sessions `0144Q`–`0144T`) adds 5 further
`@pytest.mark.gpu` tests in `test_wp036e_q3_zero_copy.py` (kDLCUDA capsule
export, deterministic export, snapshot stability, sparse k-NN CUDA dispatch,
device-end-to-end hook); the file's 6th test is a default-gate CPU regression
check, not `gpu`-marked. **Total: 12 `@pytest.mark.gpu` tests** (7 ported
acceptance + 5 WP-036E), selected by `pytest -m gpu`. The 1 psutil skip
matches `pytest.skip("psutil not installed")` in the reference. No test
carries `@pytest.mark.xfail`; no assertion is weakened; no tolerance
annotation was required beyond the Parity Report entries for the GPU sparse
k-NN f32 dispatch (`DOCS/sphinx/parity_report.rst`).

## WP-036C ported acceptance suite (24 files, 1,172 tests)

| Port file | `def test_` | Passed | Skipped | Reference guard |
|---|---:|---:|---:|---|
| `test_acceptance_integration_q3.py` | 19 | 19 | 0 | — |
| `test_acceptance_y2q1.py` | 44 | 44 | 0 | — |
| `test_acceptance_y2q2.py` | 30 | 30 | 0 | — |
| `test_acceptance_y2q3.py` | 48 | 45 | 3 | 2 DV-031 `skip` (FFI-panic, WP-036E) + 1 DV-031 `skip` (CUDA exec) |
| `test_acceptance_y2q4.py` | 28 | 28 | 0 | — |
| `test_acceptance_y3q1.py` | 40 | 40 | 0 | — |
| `test_acceptance_y3q2.py` | 38 | 38 | 0 | — |
| `test_acceptance_y3q3.py` | 32 | 32 | 0 | — |
| `test_acceptance_y3q4.py` | 32 | 32 | 0 | — |
| `test_acceptance_y3q45.py` | 23 | 23 | 0 | — |
| `test_acceptance_y3q49.py` | 55 | 24 | 31 | DV-031(A) `skip` (unbuilt Phase-6 deliverables) |
| `test_acceptance_y4q1.py` | 61 | 61 | 0 | — |
| `test_acceptance_y4q1_2.py` | 78 | 74 | 0 | 4 `slow` deselected |
| `test_acceptance_y4q1_3.py` | 49 | 48 | 1 | 1 DV-031 `skip` (RNG-regime, parity_report.rst) |
| `test_acceptance_y4q1_4.py` | 52 | 52 | 0 | — |
| `test_acceptance_y4q1_5.py` | 60 | 60 | 0 | — |
| `test_acceptance_y4q1_7.py` | 84 | 84 | 0 | — |
| `test_acceptance_y4q1_8.py` | 148 | 83 | 65 | 65 `skip` (reference: benchmark artefacts absent) |
| `test_acceptance_y4q1_9.py` | 52 | 47 | 5 | 5 `skip` (reference: benchmark artefacts absent) |
| `test_acceptance_y4q2.py` | 71 | 40 | 31 | DV-031(A) `skip` (unbuilt Phase-6 deliverables) + reference skips |
| `test_acceptance_y4q3.py` | 47 | 36 | 11 | DV-031(A) `skip` (unbuilt deliverables) + version `skip` (amdt #41) |
| `test_acceptance_y4q4.py` | 57 | 20 | 37 | DV-031(A) `skip` (unbuilt deliverables) + version `skip` (amdt #41) |
| `test_acceptance_triton_kernels.py` | 55 | 22 | 33 | 33 `skip` (reference: Triton requires Linux) |
| `test_acceptance_gpu.py` | 48 | 41 | 7 | 7 DV-031(B) `skip` (CUDA exec, WP-036E) |
| **Total** | **1,172** | **794** | **378** | — |

**Combined ported suite: 37 files, 1,670 tests** (WP-036B: 498 + WP-036C: 1,172).
Full default gate (`-m "not slow and not gpu"`): **2,774 passed, 202 skipped,
0 failed** (WP-036F `0144W` adds +9 `test_wp036f_reexport.py` error-path tests
over the WP-036E baseline of 2,765).

**WP-036C marker policy:** Governed skips are applied via a single
`tests/conftest.py` `pytest_collection_modifyitems` hook — no ported test file
is edited (assertions + text byte-unchanged). Skip categories:

- **DV-031(A):** Tests asserting the existence of benchmark campaign artefacts,
  notebooks, paper, or docs files that are unbuilt Phase-6 deliverables
  (deferred to WP-038).
- **DV-031(B):** Tests requiring GPU execution paths the current architecture
  does not yet provide (CUDA execution tests, FFI-panic ctx-on-autograd-worker
  tests) — deferred to WP-036E.
- **Plan amendment #41:** Version/classifier/citation tests asserting PRINet 3.0
  version numbering — PRIN is independently versioned; re-pointed at WP-038.
- **RNG-regime** (`y4q1_3`): One test whose pass/fail hinges on a specific
  random draw from PRIN's deterministic `Seed` stream vs PRINet 3.0's
  `torch.Generator` — preserved hazard, `parity_report.rst` entry.
- **Reference `skip`:** `y4q1_8` (×65), `y4q1_9` (×5), `triton_kernels` (×33)
  carry reference-text `pytest.skip(...)` calls preserved verbatim (benchmark
  artefacts absent; Triton requires Linux).

Run the full ported subset:

```bash
pytest tests/test_acceptance_*.py -v
```

Run the ported subset:

```bash
pytest tests/test_acceptance_*.py -v --basetemp=.pytest_basetemp
```

Run the GPU subset (self-hosted runner):

```bash
pytest tests/ -v -m gpu -rs --basetemp=.pytest_basetemp
```

## Additional PRIN-specific suites (per the Testing Standards)

- `test_wp001_baseline.py` — 44 fail-closed metadata, session-ledger,
  traceability, CI, release-guard, and security-control tests. Validates that
  `rust-toolchain.toml` includes `rustfmt` and `clippy`, optionally `llvm-tools`
  for `cargo-llvm-cov`.
- `test_dynamics_bindings.py` — 90 tests across 19 test classes covering the
  WP-011/WP-012 PyO3 bindings for dynamics and metrics: constants (4), Seed (6),
  OscillatorState (8), StateDerivatives (1), CouplingMode (5), Topology (3),
  Models (6: all 3 models × mean_field/full/sparse), Integrators (10: step,
  integrate_fixed, adaptive, trajectory, all models, error, repr),
  `TestExponentialIntegrator` and `TestMultiRateIntegrator` (WP-012: 21 tests
  covering constructor validation, direct/Krylov paths, stiff mode, RK4/Euler
  sub-stepping, trajectory recording, and typed-error propagation), PAC (2),
  Metrics (22: order 6, coherence 3, spectral 2, energy 2, chimera 7,
  metastability 1, k-NN 1), and module re-exports (2).
- `test_wp013_bands_temporal.py` — 44 tests covering the WP-013 PyO3 bindings
  for continuous hierarchical band networks and temporal propagation:
  `BandParams`/`with_coupling` (per-band coupling modes incl. the PRINet 3.0
  reference's `sparse_knn`), `PacPair` (incl. non-adjacent delta→gamma cascade),
  `BandNetwork` construction/validation/state partitioning/`Dynamics`
  derivatives/capacity/PAC identity, `create_band_state_py`, the
  `BandError::NoBands` distinct message, RK4 + `MultiRateIntegrator`
  integration of a `BandNetwork`, `ComplexPhasorBlender`/`EmaAmplitudeBlender`/
  `TemporalPropagator` construction/blending/wrap-around/clamp saturation, and
  the `alpha = 1 − carry_strength` parameter mapping (36 from S1, 8 from S3
  covering the coupling-mode surface).
- `test_parity_*.py` — fast unit tests for `prin.parity` schema, loader,
  manifest, harness, and Hypothesis strategies.
- `test_dlpack_bridge.py` — CPU round-trip, batched boundary, dtype/device
  validation, ownership/error-path, and `pytest-benchmark` latency tests for
  the WP-003 PyO3/DLPack bridge (marker `slow` for the benchmark cases).
- `test_ort_backends.py` — 31 tests for the ONNX Runtime provider probe
  (`prin._ort`): provider selection, provider-list construction (including
  VitisAI firmware resolution), session creation with CPU fallback, error
  paths, and the real subconscious-controller model load (skipped when
  `onnxruntime` is not installed).
- `test_phase0_gate.py` — 28 tests for the Phase 0 exit-gate consolidation
  (`prin._phase0`): corpus, wheel-matrix, spike-decision (including a
  regression test that the ORT amendment #13 is present in the plan text),
  ORT-evidence, and aggregate gate-report checks.
- `test_gradcheck_*.py` — `torch.autograd.gradcheck` (float64) for every
  `autograd.Function` bridge.
- `test_train_bridge_optim.py` — 13 tests for the WP-027 optimizer bridges
  (`SyncGd`/`Scalr`/`Rip` correctness, state-dict round trip, error boundaries).
- `test_train_pipeline.py` — 4 tests for the WP-027 training pipeline
  (`prin.train.train_phase_tracker` end-to-end, reproducibility, error handling).
- `test_train_bridge_phase_tracker.py` — extended with composed "full gradcheck"
  (`encode → evolve → phase_similarity`) and benchmark class (WP-027).
- `test_gpu_*.py` — GPU integration tests, marker `gpu` (opt-in, self-hosted
  runner, `[gpu]` commit-message trigger).
- `test_wp036d_gpu_dispatch.py` — 15 WP-036D GPU dispatch unit tests
  (predicate, CPU-path golden-value, marshalling round-trip, sparse k-NN
  CubeCL dispatch, batched dispatch, CUDA device assertions).
- `test_wp036e_q3_zero_copy.py` — 6 WP-036E export zero-copy tests
  (5 `@pytest.mark.gpu` CUDA: kDLCUDA capsule export, deterministic
  export, snapshot stability, sparse k-NN CUDA dispatch, device-end-to-end
  hook; 1 default-gate CPU regression).
- `test_wp036f_reexport.py` — 30 WP-036F tests for the re-exported
  controller graph (`tools/wp036f_reexport_controller.py`,
  `tools/wp036f_provider_latency.py`): three-input `Gemm` structure and
  zero-bias values, the idempotent transform and its `--check` verifier,
  CPU bit-identity vs the bias-stripped and pristine-archive graphs over the
  48-case set, and — `skipif` `DmlExecutionProvider` is not registered — that
  DirectML rejects the pre-transform graph and executes the re-exported one
  within `rtol=1e-5, atol=1e-6` of CPU. Not `@pytest.mark.gpu` (DirectML is a
  default-gate provider on the Windows host). The `0144W` S3 remediation added
  nine error-path / drift-branch tests (`TestTransformErrorPaths`,
  `TestCheckDriftBranches`, `TestProviderLatencyToolEdgeCases`), taking scoped
  changed-code coverage of both tool modules to 100% (WP036F-F1).
- `test_benchrunner.py` — WP-033 tests for the unified `benchrunner` CLI and
  its nine category packages (`../benchmarks/`): shared config/timing/
  registry/result-writer infrastructure, the ≥10-measured-iteration timing
  rule (Benchmarking and Reproducibility Standards §2.2), JSON schema
  compatibility with legacy PRINet 3.0 field names, and CLI dispatch. One
  `slow`-marked test runs the real `cargo bench -p prin-kernels` subprocess
  end to end.
- `test_reporting_profiler.py` — 59 WP-034 tests for `prin.reporting`
  benchmark reports/leaderboards/SCALR summaries and the `PRINetProfiler`:
  deterministic Markdown (caller-supplied UTC timestamp, byte-stable output),
  legacy schema preservation, Markdown escaping, output-path confinement,
  leaderboard ranking/tie-breaking, malformed-JSON isolation, profiler
  lifecycle/state validation, explicit Rust-backed operation labels, Chrome
  trace export, and `profile_training_loop` forward/backward without RNG
  mutation.
- `test_publication_generation.py` — 13 WP-034 tests covering all 14 figure
  generators, all 11 LaTeX table generators, regeneration from the stored
  PRINet 3.0 JSON artefacts, exact LaTeX byte comparison, deterministic
  normalized PNG/PDF bytes, schema/missing-artefact errors, and output-path
  confinement.
- Differential parity tests live in `../parity/`.
- Rust unit/property tests live next to each crate (`cargo test`).

Run locally:

```bash
pytest tests/ -v -m "not slow and not gpu"
```

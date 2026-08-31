# tests/ — pytest acceptance suite

The PRIN pytest suite (50 files, ~1,788 tests) is the **acceptance contract**
for PRIN: it defines the public API. The WP-036B strict port has adapted 13
PRINet 3.0 reference files (498 `def test_` functions, 8,085 reference lines)
with import-only changes (`prinet.*` → `prin.*`); assertions are unchanged
(Testing Standards §1.1).

## WP-036B ported acceptance suite (13 files, 498 tests)

| Port file | `def test_` | Passed | Skipped | Reference guard |
|---|---:|---:|---:|---|
| `test_acceptance_core.py` | 106 | 106 | 0 | — |
| `test_acceptance_utils.py` | 19 | 19 | 0 | — |
| `test_acceptance_phases.py` | 30 | 30 | 0 | — |
| `test_acceptance_hierarchical.py` | 43 | 41 | 2 | 2 CUDA `skipif` |
| `test_acceptance_phase_to_rate.py` | 22 | 21 | 1 | 1 CUDA `skipif` |
| `test_acceptance_q2.py` | 67 | 65 | 2 | 2 CUDA `skipif` |
| `test_acceptance_q2_remaining.py` | 51 | 48 | 3 | 3 CUDA `skipif` |
| `test_acceptance_q3_new.py` | 31 | 31 | 0 | — |
| `test_acceptance_nn.py` | 30 | 30 | 0 | — |
| `test_acceptance_scalr_enhanced.py` | 14 | 14 | 0 | — |
| `test_acceptance_hybrid.py` | 19 | 19 | 0 | — |
| `test_acceptance_clevr_n.py` | 17 | 17 | 0 | — |
| `test_acceptance_subconscious.py` | 49 | 48 | 1 | 1 `psutil`-absent |
| **Total** | **498** | **489** | **9** | 8 CUDA + 1 psutil |

**Marker policy:** The 8 CUDA skips are `@pytest.mark.skipif(not
torch.cuda.is_available(), ...)` guards matching the reference files exactly;
they will activate when the GPU execution path (WP-036D) is delivered. The
1 psutil skip matches `pytest.skip("psutil not installed")` in the reference.
No test carries `@pytest.mark.xfail`; no assertion is weakened; no tolerance
annotation was required (zero numerical-parity deviations from the ported
suite). Run the ported subset:

```bash
pytest tests/test_acceptance_*.py -v --basetemp=.pytest_basetemp
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

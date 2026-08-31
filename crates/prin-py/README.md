# prin-py

PyO3 extension crate for PRIN — the only crate that links Python. Built with
maturin into the `prin._prin_core` extension module inside the `prin` wheel.

WP-001 upgraded the compatible PyO3/rust-numpy pair to 0.29.0 and set the
workspace MSRV to Rust 1.83. WP-003 added the DLPack bridge
(`src/dlpack.rs`), which exposes `dlpack_negate`, `dlpack_negate_batched`, and
`dlpack_round_trip` for zero-copy Torch↔Rust tensor exchange. The `dlpack`
module is the audited Python-FFI boundary (Project Plan amendment #6 / Coding
Standards §2.1): it is the only module in this crate permitted to use `unsafe`,
under `#![deny(unsafe_op_in_unsafe_fn)]` with a `// SAFETY:` comment on every
`unsafe` block. Rust-backed forward/backward autograd bridges and the full
trainable stack land in Phase 4 (WP-022…WP-027).

WP-011 (Phase 1 Python API and dynamics integration) added PyO3 bindings for
the complete Phase 1 dynamics and metrics surface:

- **`bindings/state.rs`** — `PyOscillatorState`, `PyStateDerivatives`, `PySeed`,
  and numeric constants (`TAU`, `AMPLITUDE_MIN`, `AMPLITUDE_MAX`, `DERIV_CLAMP`,
  `SPARSE_EPS`).
- **`bindings/models.rs`** — `PyKuramotoOscillator`, `PyStuartLandauOscillator`,
  `PyHopfOscillator`.
- **`bindings/integrators.rs`** — `PyEulerIntegrator`, `PyRK4Integrator`,
  `PyRK45Integrator`, `PyAdaptiveResult`.
- **`bindings/coupling.rs`** — `PyCouplingMode`, `PyTopology`,
  `PyPhaseAmplitudeCoupling`.
- **`bindings/metrics.rs`** — 22 `#[pyfunction]`s covering the full
  `prin-metrics` surface (order, coherence, spectral, energy, chimera,
  metastability, k-NN).

All bindings are pure delegation — no Python numerics; numerical authority
remains in `prin-dynamics` and `prin-metrics`. The Python re-export modules
`python/prin/dynamics.py` (18 symbols) and `python/prin/metrics.py` (22 symbols)
provide ergonomic access. Type stubs at `python/prin/_prin_core.pyi` cover all
new symbols. 69 Python acceptance tests in `tests/test_dynamics_bindings.py`
exercise all binding paths.

WP-025 (Production Torch autograd bridge) added `bindings/train.rs`, the
differentiable PyO3/DLPack bridge exposing `prin-train`'s Rust forward/backward
to Python via `torch.autograd.Function`:

- **`bindings/train.rs`** — `PyResonanceLayerBridge` / `PyGatedPhaseActivationBridge`
  (and their `*Ctx` backward contexts): each bridge reads a DLPack capsule,
  runs the `prin-train` Rust forward (multi-step Kuramoto integration or
  gated phase activation), and returns a DLPack capsule plus a Rust context
  whose `backward` runs the Rust backward pass. Forward and backward each
  cross the boundary exactly once per call (Coding Standards §3.2). Checkpoint
  loading (`load_state_dict`) validates the decoded record's shapes against
  the current layer's configuration and raises a typed `ValueError` on
  mismatch, never panicking (WP025-F1 fix).
- **`dlpack.rs`** — two additive helpers (`read_dlpack_f64` / `export_dlpack_f64`)
  reusing the validated-shape → `contiguous_strides` → `element_count` →
  `std::slice::from_raw_parts` pattern from the WP-003 functions; no new
  `unsafe` blocks.
- **`python/prin/nn/__init__.py`** — `ResonanceLayer` and `GatedPhaseActivation`
  `torch.nn.Module` wrappers (the user-facing API), with `rust_state_dict` /
  `load_rust_state_dict` checkpoint methods. 31 Python tests in
  `tests/test_train_bridge.py` (27 fast + 2 slow-marked benchmarks + 2
  shape-mismatch regression tests), all passing `torch.autograd.gradcheck`
  in float64. Type stubs in `python/prin/_prin_core.pyi` cover all new symbols.

WP-012 (Exponential and multi-rate integrators) extended `bindings/integrators.rs`
with `PyExponentialIntegrator` (direct/Krylov exponential Euler; constructor
validates `dim`/`krylov_rank` and raises `ValueError` on `IntegrateError`) and
`PyMultiRateIntegrator` (uniform RK4/Euler sub-stepping; the inner
`MultiRateMethod` is exposed as a `"rk4"` / `"euler"` string argument rather
than a separate `#[pyclass]`). `python/prin/dynamics.py` `__all__` grew from 18
to 20 symbols; `python/prin/_prin_core.pyi` stubs and 21 new Python acceptance
tests in `tests/test_dynamics_bindings.py` (`TestExponentialIntegrator`,
`TestMultiRateIntegrator`) landed in the same S3 remediation commit
(`62deb43`, finding WP012-F1).

WP-013 (Continuous band networks and temporal propagation) added two new
binding modules:

- **`bindings/bands.rs`** — `PyBandParams` (per-band Kuramoto configuration,
  including the `with_coupling` constructor that exposes the PRINet 3.0
  reference's `sparse_knn` mode), `PyPacPair` (slow→fast cross-frequency PAC
  link; any strictly slow→fast pair is permitted, including the delta→gamma
  cascade), `PyBandNetwork` (single continuous ODE right-hand side implementing
  the dynamics trait, so it composes with every PRIN integrator rather than
  embedding one — Project Plan amendment #19), and the `create_band_state_py`
  free function. `PyBandError` maps `BandError` variants to `ValueError`.
- **`bindings/temporal.rs`** — `PyComplexPhasorBlender`,
  `PyEmaAmplitudeBlender`, and `PyTemporalPropagator`, with the
  `alpha = 1 − carry_strength` / `alpha = 1 − amplitude_decay` mapping to the
  PRINet 3.0 reference documented on each PyO3 class and applied in
  `crates/prin-dynamics/tests/parity_temporal.rs` (finding WP013-F6).

`python/prin/dynamics.py` `__all__` grew from 20 to 27 symbols (adding
`BandNetwork`, `BandParams`, `PacPair`, `create_band_state_py`,
`ComplexPhasorBlender`, `EmaAmplitudeBlender`, and `TemporalPropagator`);
`python/prin/_prin_core.pyi` stubs and 44 Python acceptance tests in
`tests/test_wp013_bands_temporal.py` cover all binding paths (36 from S1, 8
from S3 covering the coupling-mode surface).

Exec-WP-026 S1 (executive secondary session addressing WP-026 S1's own
deliberate scope deferral — see `DOCS/experiments/0101-exec-wp026-s1-handoff.md`)
added PyO3/DLPack bridges for the six new `prin-train` modules WP-026 S1
delivered without their Python-facing surface:

- **`bindings/train_support.rs`** (new) — generalizes WP-025's rank-2-specific
  DLPack decode/encode/checkpoint helpers to arbitrary tensor rank `D` via
  const generics, so every bridge module below (and `train.rs`'s own two
  WP-025 bridges, refactored to call these) reuses one implementation instead
  of re-deriving the pattern per module.
- **`bindings/attention.rs`**, **`bindings/hybrid.rs`** — `OscillatoryAttentionBridge`,
  `HybridPRINetV2Bridge`: single differentiable `forward`, following the
  WP-025 `train.rs` pattern exactly. Both constructors reject a non-zero
  `dropout`: `burn::nn::Dropout` draws from an unseeded backend RNG under
  autodiff, which breaks `torch.autograd.gradcheck` determinism and the
  recompute-on-backward contract (discovered and documented this session).
- **`bindings/phase_tracker.rs`** — `PhaseTrackerBridge`: `encode`/`evolve`/
  `phase_similarity` are differentiable (multi-output vector-Jacobian-product,
  generalizing the single-output case); `match_frames` (renamed from `forward`)
  and `track_sequence` are non-differentiable evaluation utilities (greedy
  frame-to-frame matching has no gradient) exposed as plain PyO3 methods, not
  `torch.autograd.Function`s.
- **`bindings/slot_attention.rs`** — `SlotAttentionModuleBridge`,
  `TemporalSlotAttentionMOTBridge`: both draw fresh stochastic noise from a
  caller-supplied `Seed` on every call (not just at construction); each `*Ctx`
  snapshots a clone of the `Seed` value from immediately before the original
  forward call and re-clones that snapshot for every `backward()` recompute,
  reproducing bit-identical noise (`Seed` is deterministic and `Clone`).
- **`bindings/ablation.rs`** — `PhaseTrackerFrozenBridge`/`SlotAttentionFrozenBridge`
  expose an `.inner` accessor returning a fresh `PhaseTrackerBridge`/
  `TemporalSlotAttentionMOTBridge` over a clone of the wrapped tracker, reusing
  every differentiable method those types already implement rather than
  re-deriving them; `PhaseTrackerStaticBridge`/`SlotAttentionNoGRUBridge`
  fully reimplement their own differentiable methods (their Rust types don't
  wrap the base type either).
- **`bindings/allocation.rs`** — `AdaptiveOscillatorAllocatorBridge`,
  `DynamicPhaseTrackerBridge`, `OscillatorBudget`, `estimate_complexity`: all
  non-differentiable (oscillator counts are discrete `floor`/`round` outputs).

A real correctness bug was found and fixed during this session:
`Module::load_record`'s `constant!` macro (Burn) leaves plain `usize` fields
(e.g. `n_osc`, `d_model`) **completely untouched** by a checkpoint load — only
`Param<Tensor>` fields take on the record's values. The initial
`load_state_dict` implementations compared a post-load field to itself (an
unconditional pass), so a shape-mismatched checkpoint would corrupt a
module's `Param` tensors silently. Fixed by adding `validate_shapes()` to
each affected `prin-train` type (mirroring WP025-F1's precedent exactly) and
having every `load_state_dict` call it before committing; caught by this
session's own checkpoint-mismatch-rejection tests, not by inspection.

`python/prin/nn/_bridge.py` (new) provides one generic
`torch.autograd.Function`-backed `apply_rust_bridge` helper covering
arbitrary tensor input/output arity, so the Python wrapper classes in
`python/prin/nn/{attention,phase_tracker,hybrid,slot_attention,ablation,
allocation}.py` (new) are each a few lines of glue per differentiable method
instead of a bespoke `torch.autograd.Function` subclass. `python/prin/_prin_core.pyi`
stubs and 86 new Python tests across six new `tests/test_train_bridge_*.py`
files (100% coverage on every new `python/prin/nn` file) cover all binding
paths, including `torch.autograd.gradcheck` (float64) for every differentiable
entry point and checkpoint round-trip/shape-mismatch-rejection for every
`Module`-backed bridge.

### WP-027: Optimizer bridges and trainer entry (sessions 0105–0108)

- **`bindings/optim.rs`** — `SyncGdBridge`, `ScalrBridge`, `RipBridge`:
  non-differentiable optimizer-step bridges wrapping `prin-train`'s
  `sync_gd_step`/`scalr_step`/`rip_step`. State dict round-trips via JSON.
- **`bindings/trainer.rs`** — `train_phase_tracker` PyO3 entry point running
  the Rust-native trainer end to end; `TrainingResult` pyclass.
- **`python/prin/nn/optimizers.py`** — `SyncGd`/`Scalr`/`Rip`
  `torch.optim.Optimizer` subclasses (13 tests).
- **`python/prin/train.py`** — thin Python entry point for the Rust-native
  trainer (4 tests).
- **`python/prin/_prin_core.pyi`** — +103 lines of stubs for `TrainingResult`,
  `train_phase_tracker`, `SyncGdBridge`, `ScalrBridge`, `RipBridge`.

### WP-036A: Trainable compatibility layer bridges (sessions 0144A–0144A4)

Four new binding modules delivering PyO3/DLPack `torch.autograd.Function`
bridges for the 13 D-D-appendix trainable-layer symbols (WP-036A):

- **`bindings/train_inhibition_layers.rs`** — `FeedforwardInhibitionBridge`,
  `DentateGyrusConverterBridge`, `DGLayerBridge`,
  `SparsityRegularizationLossBridge`, `OscillatoryWeightInitBridge` (5
  bridges, 4 differentiable + 1 non-differentiable init function).
- **`bindings/train_autoencoders.rs`** — `PhaseToRateConverterBridge`,
  `PhaseToRateAutoencoderBridge` (forward + classify),
  `DenseAutoencoderBridge` (forward + classify) (3 bridges, all
  differentiable).
- **`bindings/train_hierarchical_layers.rs`** —
  `HierarchicalResonanceLayerBridge`, `PhaseAmplitudeCouplingLayerBridge`,
  `DiscreteDeltaThetaGammaLayerBridge` (3 bridges, all differentiable).
- **`bindings/train_model.rs`** — `PRINetModelBridge` (1 differentiable
  bridge).

All bridges follow the established WP-025/Exec-WP-026 pattern: thin DLPack
marshalling wrappers, no numerics in `prin-py`, `#![deny(unsafe_code)]`
unchanged. `python/prin/_prin_core.pyi` stubs cover all 12 new bridge
classes plus their `*Ctx` backward contexts. 52 new Python tests across
four new `tests/test_{inhibition_layers,autoencoders,hierarchical_layers,
model}.py` files, all with float64 `torch.autograd.gradcheck` and
PRINet-3.0 forward-parity at documented tolerances.

Type stubs are maintained at `python/prin/_prin_core.pyi` and regenerated
whenever the extension API changes.

### WP-036D: GPU execution path (sessions 0144I–0144L)

- **`bindings/gpu.rs`** (new, feature-gated `#[cfg(any(feature = "cuda",
  feature = "wgpu"))]`) — PyO3 wrappers over `prin-sim`'s GPU simulation
  engines: `GpuSparseKuramoto` (sparse k-NN coupling, including the
  `from_knn_phase` constructor that builds the CSR topology in Rust so the
  Python dispatch constructs no coupling weights), `GpuMeanFieldEngine`
  (mean-field RK4/exponential integration), `GpuBandStepper` (hierarchical
  band-network stepping). All are thin marshalling — numerical authority
  remains in `prin-kernels` (CubeCL) and `prin-sim`.
- **`dlpack.rs`** — two additive `f32` helpers (`read_dlpack_f32` /
  `export_dlpack_f32`) mirroring the audited `f64` patterns verbatim
  (identical SAFETY justifications, no new `unsafe` blocks). Per plan
  amendment #37 the marshalling boundary is CPU `float32` DLPack; the GPU
  compute runs on-device via CubeCL backend selection.
- **`python/prin/_torch_compat.py`** — `_is_gpu` predicate; `_gpu_f32` /
  `_from_gpu` CPU-float32 DLPack marshalling helpers; a GPU dispatch branch
  in `OscillatorModel.compute_derivatives` routing a CUDA sparse k-NN input
  to `GpuSparseKuramoto.from_knn_phase` → CubeCL sparse k-NN kernel. CPU
  path byte-for-byte unchanged.
- **`python/prin/_prin_core.pyi`** — stubs for `GpuSparseKuramoto`,
  `GpuMeanFieldEngine`, `GpuBandStepper`, `read_dlpack_f32`,
  `export_dlpack_f32`.
- 15-test dispatch unit suite (`tests/test_wp036d_gpu_dispatch.py`) covering
  the predicate, CPU-path golden-value identity, marshalling round-trip,
  real sparse k-NN CubeCL dispatch, batched dispatch, and CUDA-guarded
  device assertions. 7 acceptance tests carry `@pytest.mark.gpu` and pass
  on the self-hosted CUDA runner; the eighth (`test_sparse_vram_subquadratic`)
  is deferred to DV-030 (device-resident buffers).

### WP-028: Daemon bindings (sessions 0109–0112)

- **`bindings/daemon.rs`** — PyO3 surface for the `prin-daemon` crate:
  `SubconsciousState`, `ControlSignals`, `BackendSelection`,
  `select_execution_backend`, `backend_provider_names`, `backend_priority`,
  `backend_provider_options`, `npu_firmware_candidates`, `resolve_npu_firmware`,
  `model_sha256`, `inspect_onnx_model`, `verify_model_manifest`,
  `validate_controller_model`, and eight module constants (`STATE_DIM`,
  `CONTROL_DIM`, etc.).
- **`python/prin/daemon.py`** — `SubconsciousController` (ONNX inference),
  `create_session` (fallback ladder), `select_backend`, `detect_best_backend`,
  `npu_available`, `directml_available`, `backend_info`,
  `verify_model_artefacts`, `default_model_path`, `OrtUnavailableError`.
- **`python/prin/_prin_core.pyi`** — +135 lines of stubs for every new class,
  function, and constant.
- 106 new Python tests (`tests/test_daemon_backend.py`,
  `tests/test_daemon_controller.py`) and 82 differential parity tests
  (`parity/test_parity_subconscious.py`).

Build for development:

```bash
maturin develop -m crates/prin-py/Cargo.toml
```

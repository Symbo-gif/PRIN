Migration Guide (PRINet 3.0 → PRIN)
===================================

.. note::
   Written incrementally as symbols land; finalized in Phase 6. Contains the
   symbol-by-symbol mapping table for all 175+ PRINet 3.0 public exports and
   numerical tolerance notes.

New PRIN-only symbols
---------------------

The following symbols are new in PRIN and have no direct PRINet 3.0 equivalent:

- ``prin.parity`` — golden-trajectory corpus, manifest/loader, differential
  harness, and Hypothesis strategies used by the numerical parity program
  (project plan §5).
- ``prin.dlpack`` — zero-copy DLPack tensor exchange between PyTorch and the
  PRIN Rust core (``negate``, ``negate_batched``, ``round_trip``). PRINet 3.0
  performed all computation in Python; PRIN moves numerics to Rust and crosses
  the boundary via DLPack capsules, so this module has no 3.0 counterpart. The
  CPU round-trip and batched boundary paths are validated in WP-003; the CUDA
  round-trip and ``<5%`` training-step overhead target are deferred to the
  Phase 4 trainable-stack work (project plan amendment #7).
- ``prin-kernels::mean_field_rk4`` — single-source CubeCL fused mean-field RK4
  kernel set with CPU/wgpu/cuda dispatch. PRINet 3.0 kept separate
  Triton/CUDA/PyTorch-fallback kernel files; PRIN collapses them into one
  Rust/CubeCL implementation (Phase 0 spike, production suite in Phase 3). The
  Rust public API has no direct PRINet 3.0 Python equivalent at this phase.
- ``prin._ort`` — ONNX Runtime execution-provider probe for the subconscious
  controller (CPU/DirectML/VitisAI with graceful fallback). PRINet 3.0 ran the
  controller in-process with no provider abstraction; PRIN introduces backend
  selection and fallback as a Phase 0 spike, with the full daemon runtime owned
  by WP-028. This is an internal module (underscore prefix) not re-exported from
  ``prin.__all__``.
- ``prin._phase0`` — Phase 0 exit-gate evidence consolidation. Validates the
  three foundation spikes, the golden-trajectory corpus, the abi3 wheel matrix,
  and the recorded go/no-go decisions before the Phase 0 pre-release tag. This
  is an internal module (underscore prefix) not re-exported from
  ``prin.__all__``.
- ``prin-dynamics`` oscillator state and seed (WP-006) — Rust struct-of-arrays
  ``OscillatorState``, deterministic counter-based ``Seed`` authority on
  ``Pcg64``, typed ``StateError``/``SeedError``, numerical guards/clamps
  (phase wrap to ``[0, 2π)``, ``atan2``-safe phase differences, amplitude clamp
  ``[1e-6, 10]``, derivative clamp ``±1e4``), and sort-based phase k-NN index.
  Replaces PRINet 3.0's Python oscillator state in ``core/propagation/oscillator_state.py``.
- ``prin-dynamics`` oscillator models (WP-007) — Rust ``Dynamics`` trait and
  ``KuramotoOscillator``, ``StuartLandauOscillator``, and ``HopfOscillator``
  models with enum-dispatched ``CouplingMode`` (``MeanField``, ``Full``,
  ``SparseKnn``) and ``StateDerivatives`` (``dphase``/``damplitude``/``dfrequency``).
  Replaces PRINet 3.0's Python models in
  ``core/propagation/oscillator_models.py``. The Rust implementation uses ``f64``
  real and ``Complex64`` arithmetic; PRINet 3.0 uses ``torch.complex64`` (f32)
  internally for mean-field order parameters and Stuart–Landau complex amplitudes,
  producing up to ~``1e-7`` per-step drift on the affected paths. This is accepted
  as a preserved numerical hazard (Project Plan §5, amendment #14); derivative
  parity tests use a ``1e-6`` tolerance for affected paths and ``1e-12`` for pure
  float64 paths (see the Parity Report). Python bindings for these models are
  deferred to WP-011 (Phase 1 Python API and dynamics integration).

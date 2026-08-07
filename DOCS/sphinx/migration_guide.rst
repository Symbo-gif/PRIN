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

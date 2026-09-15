Architecture Guide
==================

Overview
--------

**PRIN** (Phase-Resonance Interference Network) is the from-scratch rebuild of
the **PRINet 3.0** research prototype. It processes information through coupled
oscillator dynamics, polyadic tensor decomposition, and phase synchronization,
exposed as a PyTorch-compatible Python API.

The defining architectural rule: **all numerics live in the compiled Rust
core** (``prin._prin_core``, built from the ``crates/`` workspace). The Python
package ``prin`` provides API ergonomics, PyTorch autograd bridges (via
DLPack), plotting, orchestration, and parity tooling — and contains no
numerical reimplementation. This is not a convention; it is enforced twice:

* ``tools/check_no_python_numerics.py`` runs in the CI governance job and
  fails on arithmetic in the Python layer outside an allow-listed module set.
* ``tests/test_no_python_numerics.py`` is an AST regression over the same rule.

The consequence for a reader of this documentation: when a Python docstring and
a Rust rustdoc disagree about what an algorithm computes, **the Rust is
authoritative** and the Python is a marshalling defect.

Workspace layout
----------------

Eight crates, one Python package:

.. code-block:: text

   crates/
   ├── prin-dynamics/     # oscillator state, models, coupling, PAC, integrators, bands
   ├── prin-tensor/       # polyadic (CP / Tucker) tensor decomposition
   ├── prin-metrics/      # order parameter, coherence, spectral, chimera metrics
   ├── prin-sim/          # simulation orchestration, sweeps, OscilloSim
   ├── prin-kernels/      # fused discrete-step / mean-field / sparse-kNN kernels
   ├── prin-train/        # trainable stack: layers, attention, hybrid, bands,
   │                      #   optimizers (SCALR / RIP / SyncGD), HEP, slot attention
   ├── prin-daemon/       # subconscious controller: ONNX inference, EP selection
   └── prin-py/           # PyO3 bindings — thin marshalling only, zero numerics

   python/prin/
   ├── dynamics.py, metrics.py, kernels.py, solvers.py, tensor.py, simulation.py
   ├── _torch_compat.py   # internal Torch-facing compatibility facade
   ├── nn/                # torch.nn.Module wrappers over the Rust-backed bridges
   ├── daemon.py, subconscious_compat.py, training_hooks.py, temporal_training.py
   ├── parity/            # golden-corpus loader, manifest, differential harness
   └── reporting/, eval/, experiments/

Crate layering is a plan rule (Project Plan §4), not a preference: a crate may
depend only on crates below it. ``prin-dynamics`` is the base; ``prin-py`` is
the only crate that knows Python exists. Every crate carries
``#![forbid(unsafe_code)]`` or ``#![deny(unsafe_code)]`` plus
``#![warn(missing_docs)]``, and CI builds rustdoc under
``RUSTDOCFLAGS="-D warnings"``, so an undocumented public item is a build
failure (Documentation Standards §2.1).

Data flow
---------

How one forward pass travels from Python to Rust and back:

1. A Python ``torch.nn.Module`` wrapper (for example
   ``prin.nn.ResonanceLayer``, ``DiscreteDeltaThetaGammaLayer``,
   ``OscillatoryAttention``) marshals float32/float64 CPU tensors to the Rust
   bridge through ``prin.nn._bridge.apply_rust_bridge``.
2. The bridge (``crates/prin-py/src/bindings/*.rs``) converts tensors via
   **DLPack** — no copy for a contiguous CPU tensor — calls the owning
   ``prin-train`` / ``prin-dynamics`` routine, and returns the results together
   with a recompute closure for the backward pass.
3. ``torch.autograd.Function`` orchestration in Python stitches the forward and
   VJP calls into the autograd graph. Rust/Burn returns input VJPs and, for the
   canonical-parameter bridges, parameter VJPs as well. ``ResonanceLayer`` and
   ``DiscreteDeltaThetaGammaLayer`` synchronize their canonical
   ``torch.nn.Parameter`` values into Rust on every forward; other modules may
   retain Rust-owned parameters checkpointed through
   ``rust_state_dict()`` / ``load_rust_state_dict()``.

.. code-block:: text

   torch.Tensor ──DLPack──► prin-py binding ──► prin-train / prin-dynamics
        ▲                                                │
        │                                                │ forward + VJP closure
        └────────────── autograd.Function ◄──────────────┘

Two properties follow, and both are load-bearing for the parity program:

* **No Python fallback path.** If the Rust owner is unavailable, the call
  raises a typed error rather than silently substituting a different
  algorithm. GPU- and Triton-only PRINet 3.0 symbols are documented
  availability stubs whose predicates probe *executability*, not registration
  (Testing Standards §1.6).
* **Determinism is explicit.** All stochastic construction routes through the
  Rust ``Seed`` type (counter/key halves). There is no hidden RNG in the Python
  layer, and no global seed state.

Device and backend dispatch
---------------------------

Backend selection lives in ``prin-kernels`` (CubeCL single-source kernels with
a CPU reference) and ``prin-daemon`` (ONNX Runtime execution providers). The
Python layer never chooses an algorithm based on the device; it forwards a
device handle and the Rust owner dispatches.

Current status, with the governing Deferred Validation item:

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - Path
     - State
     - Register item
   * - CPU (all platforms)
     - Complete; the reference every tolerance is measured against.
     - —
   * - CUDA device-resident
     - On-device ``f64`` combine with bounded host residual delivered
       (WP-036E). Genuine device-event timing is re-gated on a CubeCL
       ``TimingMethod::Device`` CUDA release.
     - DV-003 (partially closed, amendment #44)
   * - Zero-copy kernel input
     - Bidirectional zero-copy re-gated on a CubeCL external-memory API.
     - DV-030 (partially closed, amendment #43)
   * - DirectML (controller graph)
     - **Closed** at WP-036F: the re-exported three-input-``Gemm`` ONNX graph
       executes on ``DmlExecutionProvider``, bit-identical to the reference on
       CPU and within ``rtol=1e-5, atol=1e-6`` of CPU.
     - DV-006 (DirectML half closed)
   * - VitisAI / Ryzen AI NPU
     - Hardware-gated; no XDNA device on the maintainer host and the Ryzen AI
       SDK ships VitisAI only as a CPython 3.12 wheel.
     - DV-006 (standing-external)

See :doc:`api/daemon` for the execution-provider selection policy and
:doc:`kernel_architecture` for the single-source kernel design.

Compatibility surface
---------------------

Every symbol in the frozen PRINet 3.0 public API (``prinet.__all__``, 172
names) resolves from ``prin``. Each maps to one of:

* a real Rust-backed implementation;
* a thin Python composition over Rust-backed layers;
* a documented availability stub for a GPU/Triton-only symbol with no CPU
  analogue; or
* a typed ``NotImplementedError`` stub whose owning work package is named.

The authoritative per-symbol disposition table is :doc:`migration_guide`,
machine-checked by ``tools/wp036_migration_table.py`` against
``DOCS/baselines/wp001_api_traceability.md``. ``prin.__all__`` currently
carries 175 names — the 172 compatibility symbols plus PRIN-only additions —
and ``verify_api_surface(prin.__all__)`` returns ``(set(), set())``.

Where PRIN deliberately diverges from the reference, the divergence is recorded
rather than smoothed over. Two examples:

* ``prin-metrics::chimera::strength_of_incoherence`` is **not** parity-matched
  to the PRINet 3.0 fixture: the reference's wrap-centring formula is an
  upstream defect (EMA-001 M-F1, Z3-confirmed), so PRIN's corrected
  implementation is authoritative (Project Plan amendment #25).
* ``HierarchicalResonanceLayer`` is implemented fully batched
  (``[batch, n_total]``) rather than reproducing the reference's per-sample
  Python loop — a documented "better design" note (amendment #34, D-5).

Determinism and parity
----------------------

Parity against ``prinet==3.0.0`` is verified on a versioned golden-trajectory
corpus under ``parity/`` at ``rtol=1e-6``, ``atol=1e-8`` for trajectories and
``rtol=2e-6`` for cross-platform corpus regeneration of derived metrics
(amendments #16, #17). The differential CI job installs the reference editable
and replays the corpus on every push.

The preserved numerical hazards — phase wrap ``% 2π``, amplitude clamp
``[1e-6, 10]``, derivative clamp ``±1e4``, coupling normalization ``1/N`` vs
``1/k``, the ``φ₁(λ)→1`` limit, the straight-through estimator's
forward-hard/backward-soft identity, and the reference's ``torch.complex64``
internal arithmetic — are enumerated in Project Plan §5 and measured in
:doc:`parity_report`.

Versioning
----------

PRIN is independently versioned toward ``1.0.0-rc1``; it is **not** a
continuation of PRINet 3.0's numbering (Project Plan amendment #41). The
version is stated once, in ``pyproject.toml``, and the workspace
``Cargo.toml``, ``prin.__version__``, ``prin.core_version()``,
``CITATION.cff``, and this documentation site's ``|release|`` are all derived
from or checked against it.

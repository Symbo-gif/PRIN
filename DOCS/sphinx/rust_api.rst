Rust API Reference (docs.rs)
============================

PRIN's numerical authority is a Cargo workspace of eight crates. The Python
pages under :doc:`api/core` document the API you call; this page documents
where the implementations behind it are published.

.. admonition:: Publication status
   :class: important

   The ``prin-*`` crates are **not yet on crates.io**, so the docs.rs URLs
   below do not resolve at the time of writing. ``release.yml``'s
   ``publish-crates`` job is still the pre-WP-005 guard step
   (``echo "Workspace crate publication remains disabled until ..."`), and
   enabling it is RC1 work under WP-038. Each crate already carries its
   ``documentation`` key and a ``[package.metadata.docs.rs]`` build
   configuration, so the pages appear on the first successful publication
   without further change.

   Until then the authoritative rendered rustdoc is a local build, which is
   also what CI gates on (``rust.yml``'s ``docs`` job, ``cargo doc --workspace
   --no-deps`` under ``RUSTDOCFLAGS="-D warnings"``):

   .. code-block:: bash

      RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --open

Crates
------

.. list-table::
   :header-rows: 1
   :widths: 20 56 24

   * - Crate
     - Scope
     - docs.rs
   * - ``prin-dynamics``
     - Oscillator state and models (Kuramoto, Stuart–Landau, Hopf), coupling
       modes and topologies, phase–amplitude coupling, integrators
       (Euler / RK4 / RK45 / exponential / multi-rate), hierarchical band
       networks, temporal propagation. The base of the layering.
     - `docs.rs/prin-dynamics <https://docs.rs/prin-dynamics>`_
   * - ``prin-metrics``
     - Order parameters, phase coherence, power spectral density, chimera
       metrics, sparse k-NN variants.
     - `docs.rs/prin-metrics <https://docs.rs/prin-metrics>`_
   * - ``prin-tensor``
     - Polyadic tensor decomposition: Tucker / HOSVD (``PolyadicTensor``) and
       CP / PARAFAC (ALS).
     - `docs.rs/prin-tensor <https://docs.rs/prin-tensor>`_
   * - ``prin-kernels``
     - Single-source CubeCL fused kernels — mean-field RK4, sparse k-NN
       coupling, PAC, fused discrete step, hierarchical reductions — with a
       CPU SIMD reference for every kernel.
     - `docs.rs/prin-kernels <https://docs.rs/prin-kernels>`_
   * - ``prin-sim``
     - The ``OscilloSim`` engine: CSR sparse coupling, chimera detection,
       pruning, and integration orchestration for large oscillator systems.
     - `docs.rs/prin-sim <https://docs.rs/prin-sim>`_
   * - ``prin-train``
     - Trainable components: resonance layers, ``DiscreteDeltaThetaGamma``,
       inhibition / straight-through estimators, activations, the HEP trainer,
       resonance-aware optimizers (SCALR / RIP / SyncGD), datasets, losses,
       statistics, FLOP accounting.
     - `docs.rs/prin-train <https://docs.rs/prin-train>`_
   * - ``prin-daemon``
     - Subconscious controller: state / control buffers, the native daemon
       thread, ONNX inference with NPU / DirectML / CPU backend detection.
     - `docs.rs/prin-daemon <https://docs.rs/prin-daemon>`_
   * - ``prin-py``
     - PyO3 bindings — the only crate that links Python. Published as the
       ``prin._prin_core`` extension module inside the wheel, **not** as a
       crates.io crate, so it has no docs.rs page. Its Rust side is documented
       by ``cargo doc -p prin-py`` and its Python surface by :doc:`api/core`.
     - —

docs.rs build configuration
---------------------------

Each published crate pins the feature set docs.rs should build, because the
default (all-features) build would either hide the guarded paths or fail on a
builder without GPU toolchains:

.. list-table::
   :header-rows: 1
   :widths: 26 26 48

   * - Crate
     - Setting
     - Why
   * - ``prin-dynamics``, ``prin-metrics``, ``prin-tensor``, ``prin-train``,
       ``prin-daemon``
     - ``all-features = true``
     - Their features (``strict-checks``, ``npu``) are plain ``cfg`` flags with
       no vendor-toolchain requirement, so an all-features build documents the
       guarded clamp / finite paths and the VitisAI-gated paths a reader cannot
       otherwise reach.
   * - ``prin-kernels``
     - ``features = ["cpu"]``
     - ``cuda`` and ``wgpu`` pull in CubeCL backends that need vendor
       toolchains the docs.rs builder does not have. The single-source design
       means the ``cpu`` build documents the same kernel bodies; only the
       backend dispatch is ``#[cfg]``-gated.
   * - ``prin-sim``
     - ``features = ["strict-checks", "cpu"]``
     - Same GPU-toolchain constraint, plus the forwarded ``strict-checks``
       guards ``prin-sim`` inherits from ``prin-dynamics``.

Documentation coverage gate
---------------------------

Every crate carries ``#![warn(missing_docs)]`` at the crate root
(``#![deny(unsafe_code)]`` for ``prin-kernels`` and ``prin-py``,
``#![forbid(unsafe_code)]`` for the rest), and CI builds rustdoc with
``RUSTDOCFLAGS="-D warnings"``. An undocumented public item is therefore a
build failure, not a lint — Documentation Standards §2.1's 100 %-of-public-items
threshold is mechanically enforced rather than reviewed.

Crate-level docs (each ``lib.rs``) state the crate's scope, its PRINet 3.0
rebuild target, and the preserved numerical invariants it is responsible for.
Math notation in rustdoc follows the paper: φ for phase, ω for natural
frequency, *K* for coupling strength, *R* for the order parameter.

Reading order
-------------

If you are new to the Rust side:

1. ``prin_dynamics::state`` — ``OscillatorState`` and the clamp / wrap
   invariants everything else assumes.
2. ``prin_dynamics::models`` — the oscillator right-hand sides.
3. ``prin_dynamics::coupling`` — ``CouplingMode`` and ``Topology``
   (mirrored in :doc:`coupling_topologies`).
4. ``prin_dynamics::bands`` — ``BandNetwork`` and
   ``theoretical_capacity`` (mirrored in :doc:`capacity_analysis`).
5. ``prin_kernels`` — how the same math becomes a fused kernel with a CPU
   reference (:doc:`kernel_architecture`).
6. ``prin_py::bindings`` — how a ``torch.Tensor`` reaches any of the above
   (:doc:`architecture`).

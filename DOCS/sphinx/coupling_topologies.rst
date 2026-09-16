Coupling Topologies API Reference
=================================

Every PRIN oscillator model takes a coupling specification that says how each
oscillator is influenced by the others. There are **two distinct surfaces**,
and mixing them up is the most common source of confusion:

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Surface
     - Coupling type
     - Use when
   * - Rust core (:mod:`prin.dynamics`)
     - ``CouplingMode`` value: ``mean_field()``, ``full(matrix=...)``,
       ``sparse_knn(k=...)``
     - You want float64 reference semantics, an explicit interaction matrix, or
       an integrator you drive yourself.
   * - Simulator (:class:`prin.simulation.OscilloSim`)
     - ``coupling_mode`` **string**: ``"auto"``, ``"mean_field"``, ``"csr"``,
       ``"ring"``, ``"small_world"``, ``"sparse_knn"``
     - You want a batched, ``torch.Tensor``-facing run with throughput
       reporting and trajectory recording.

``"full"`` is **not** a valid ``OscilloSim`` mode — it raises ``ValueError:
Unknown coupling_mode 'full'; expected one of ['auto', 'csr', 'mean_field',
'ring', 'small_world', 'sparse_knn']``. A dense custom interaction matrix is
only reachable through the core's ``CouplingMode.full``.

All modes are implemented in Rust (``crates/prin-dynamics/src/coupling.rs``);
Python only selects one.

Core modes (``CouplingMode``)
-----------------------------

``mean_field``
~~~~~~~~~~~~~~

Every oscillator couples to the population mean phase. Cost is ``O(N)`` per
step. This is the right choice for global synchronization studies and the
cheapest mode at large *N*.

``full``
~~~~~~~~

All-to-all pairwise coupling, ``O(N²)`` per step. Use for small populations
where the exact interaction matrix matters — phase-diagram sweeps at fixed *N*,
or a hand-built graph.

``sparse_knn``
~~~~~~~~~~~~~~

Each oscillator couples only to its *k* nearest neighbours in phase space; the
neighbour set is rebuilt each step. Cost is ``O(Nk)``. This is the scalable
mode for large populations.

Degenerate arguments are **rejected, not silently repaired**:

.. code-block:: python

   from prin.dynamics import CouplingMode, KuramotoOscillator, OscillatorState, Seed

   for bad_k, n in [(0, 8), (4, 1), (100, 8)]:
       try:
           KuramotoOscillator(n, 2.0, 0.1, 0.0, CouplingMode.sparse_knn(k=bad_k))
       except ValueError as exc:
           print(f"k={bad_k}, N={n}: {exc}")

The invariant is ``1 <= k < N``. A single-oscillator network has no neighbours
and must use ``mean_field()`` or ``full()``.

Constructing a model
~~~~~~~~~~~~~~~~~~~~

``KuramotoOscillator`` takes five required arguments, positionally or by
keyword; ``coupling_mode`` is a ``CouplingMode`` value, never a string:

.. code-block:: python

   from prin.dynamics import CouplingMode, KuramotoOscillator, OscillatorState, Seed

   model = KuramotoOscillator(
       4096,            # n_oscillators
       1.5,             # coupling_strength  (K)
       0.1,             # decay_rate
       0.0,             # freq_adaptation_rate
       CouplingMode.sparse_knn(k=16),
   )
   state = OscillatorState.create_random(4096, (1.0, 5.0), Seed(0, 42))
   derivatives = model.compute_derivatives(state)     # dphase / damplitude / dfrequency

Custom interaction matrices
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``CouplingMode.full`` accepts an explicit matrix as a **flat row-major
``float64`` NumPy array of length ``N * N``**. Passing a 2-D array raises
``TypeError``; passing the wrong length raises
``ValueError: field 'coupling_matrix' length 15 does not match expected 16``.

.. code-block:: python

   import numpy as np
   from prin.dynamics import CouplingMode, KuramotoOscillator, OscillatorState, RK4Integrator, Seed

   n = 32
   weights = np.zeros((n, n))
   weights[: n // 2, : n // 2] = 1.0        # two clusters, no inter-cluster edges
   weights[n // 2 :, n // 2 :] = 1.0

   model = KuramotoOscillator(
       n, 2.0, 0.1, 0.0,
       CouplingMode.full(matrix=np.ascontiguousarray(weights.ravel())),
   )
   state = OscillatorState.create_random(n, (1.0, 5.0), Seed(0, 42))
   integrator = RK4Integrator()
   for _ in range(50):
       state = integrator.step(model, state, 0.01)

A worked two-cluster example, including the adjacency visualization, is in
``notebooks/03_custom_coupling.ipynb``.

``Topology`` builders
~~~~~~~~~~~~~~~~~~~~~

:class:`prin.dynamics.Topology` builds a coupling matrix from a graph
specification. ``build_matrix`` returns the same flat row-major layout that
``CouplingMode.full`` consumes, so the two compose directly:

.. code-block:: python

   from prin.dynamics import Topology, Seed

   Topology.all_to_all().build_matrix(8, 2.0).shape              # (64,)  — 56 non-zero
   Topology.ring(4).build_matrix(8, 2.0).shape                   # (64,)  — 32 non-zero
   Topology.small_world(4, 0.3, Seed(0, 42)).build_matrix(8, 2.0)  # (64,)

Simulator modes (``OscilloSim``)
--------------------------------

.. code-block:: python

   from prin import OscilloSim

   sim = OscilloSim(n_oscillators=256, coupling_strength=2.5,
                    coupling_mode="small_world", k_neighbors=8,
                    p_rewire=0.2, integrator="rk4", seed=0)
   result = sim.run(n_steps=200, dt=0.01)
   print(sim.coupling_mode)          # the *resolved* mode
   print(sim.state_summary())

.. list-table::
   :header-rows: 1
   :widths: 20 14 66

   * - Mode
     - Cost / step
     - Notes
   * - ``"mean_field"``
     - ``O(N)``
     - Couples to the population mean phase.
   * - ``"ring"``
     - ``O(Nk)``
     - Each oscillator couples to ``k_neighbors`` lattice neighbours.
   * - ``"small_world"``
     - ``O(Nk)``
     - Watts–Strogatz ring with rewiring probability ``p_rewire``; the
       rewiring RNG is the deterministic Rust ``Seed``, so a given
       ``(N, k, p_rewire, seed)`` always produces the same graph.
   * - ``"sparse_knn"``
     - ``O(Nk)``
     - Phase-space *k*-nearest neighbours, rebuilt each step.
   * - ``"csr"``
     - ``O(nnz)``
     - Compressed-sparse-row random coupling at the given ``sparsity``.
   * - ``"auto"``
     - —
     - Resolved once at construction from ``n_oscillators``; see below.

``"auto"`` resolution thresholds (verified against |release|):

.. code-block:: python

   from prin import OscilloSim

   for n in (8, 999, 1000, 99_999, 100_000):
       print(n, OscilloSim(n_oscillators=n, coupling_mode="auto").coupling_mode)
   # 8 csr / 999 csr / 1000 sparse_knn / 99999 sparse_knn / 100000 mean_field

That is: ``csr`` below 1 000 oscillators, ``sparse_knn`` from 1 000 up to
99 999, ``mean_field`` at 100 000 and above.

Per-edge coupling weights
~~~~~~~~~~~~~~~~~~~~~~~~~

``coupling_weights`` supplies an ``(N, k)`` weight tensor for the
neighbour-based modes. It is only meaningful where a neighbour set exists;
passing one with a mode that has no ``k`` columns raises
``ValueError: dimension mismatch: 'coupling_weights' expected 0, got ...``.

The Abrams–Strogatz cosine kernel produces exactly such a tensor:

.. code-block:: python

   from prin import OscilloSim
   from prin.simulation import cosine_coupling_kernel

   weights = cosine_coupling_kernel(64, 8, A=0.995)     # (64, 8) float32
   sim = OscilloSim(n_oscillators=64, coupling_strength=2.0, coupling_mode="ring",
                    k_neighbors=8, coupling_weights=weights, seed=0)
   result = sim.run(n_steps=20, dt=0.01)

Neighbour-index tensors
~~~~~~~~~~~~~~~~~~~~~~~

:func:`prin.ring_topology` and :func:`prin.small_world_topology` build the
``(N, k)`` ``int64`` neighbour-index tensors that the chimera diagnostics take:

.. code-block:: python

   import numpy as np
   import torch
   from prin import local_order_parameter, ring_topology, small_world_topology
   from prin.simulation import chimera_index, strength_of_incoherence

   neighbours = ring_topology(256, 6)                   # (256, 6) int64
   small_world_topology(256, 6, p_rewire=0.3, seed=0)   # (256, 6) int64

   phase_np = np.asarray(torch.rand(256) * 2 * torch.pi, dtype=np.float64)
   nbr_list = neighbours.detach().cpu().tolist()
   local_r = local_order_parameter(phase_np, nbr_list)  # (256,)
   phase_t = torch.from_numpy(phase_np)
   chimera_index(phase_t, neighbours)                    # float, threshold=0.5
   strength_of_incoherence(phase_t, window_size=10)      # 0-dim tensor

A custom topology is, at this level, just an ``(N, k)`` integer tensor of
neighbour indices — build one with ``torch.randint`` or from an adjacency
matrix and every diagnostic above accepts it unchanged.

.. admonition:: ``strength_of_incoherence`` is deliberately not parity-matched
   :class: caution

   PRINet 3.0's wrap-centring formula for the strength of incoherence is an
   upstream defect (EMA-001 M-F1, Z3-confirmed). PRIN's corrected
   implementation in ``prin-metrics::chimera`` is authoritative and the
   resulting fixture divergence is **not** a preserved numerical hazard
   (Project Plan amendment #25). Do not "fix" a mismatch against the 3.0
   fixture here.

Hierarchical band networks
--------------------------

``HierarchicalResonanceLayer`` and ``DiscreteDeltaThetaGamma`` partition
oscillators into δ / θ / γ bands. Intra-band dynamics use the per-band coupling
strength; cross-band interaction is phase–amplitude coupling, where the slow
band's mean phase modulates the fast band's amplitude.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Meaning
   * - ``coupling_strength``
     - Intra-band Kuramoto gain *K*.
   * - ``pac_depth``
     - Modulation depth ∈ [0, 1] for ``DiscreteDeltaThetaGamma`` (a single
       scalar).
   * - ``pac_depth_dt`` / ``pac_depth_tg``
     - δ→θ and θ→γ modulation depths. On ``HierarchicalResonanceLayer`` these
       are the two learnable ``nn.Parameter``s —
       ``[n for n, _ in layer.named_parameters()]`` returns exactly
       ``['pac_depth_dt', 'pac_depth_tg']``.
   * - ``n_delta``, ``n_theta``, ``n_gamma``
     - Per-band oscillator counts; ``n_total`` is their sum (the output width).
   * - ``sparse_k``
     - Optional; switches intra-band coupling to sparse k-NN.

Per-band order parameters are in ``[0, 1]``:

.. code-block:: python

   import torch
   from prin.nn import DiscreteDeltaThetaGamma, HierarchicalResonanceLayer

   layer = HierarchicalResonanceLayer(n_delta=4, n_theta=8, n_gamma=32,
                                      n_dims=64, n_steps=5)
   amplitudes = layer(torch.randn(8, 64))                    # (8, 44)
   amplitudes, phases = layer(torch.randn(8, 64), return_phase=True)

   net = DiscreteDeltaThetaGamma(n_delta=4, n_theta=8, n_gamma=32)
   phase = torch.rand(16, net.n_total) * 2 * torch.pi
   r_delta, r_theta, r_gamma = net.order_parameters(phase)   # each in [0, 1]

Continuous vs discrete band networks
------------------------------------

``prin-dynamics::bands::BandNetwork`` exposes the hierarchy as a **single
continuous ODE right-hand side** over the concatenated state, so it composes
with every PRIN integrator rather than embedding one. PRINet 3.0's band
networks were *steppers* — a per-band ``KuramotoOscillator`` plus a fixed
``sub_steps`` count. The consequences are recorded as Project Plan amendment
#19:

* **Intra-band terms are identical** to the reference for the configured
  coupling mode (verified in ``crates/prin-dynamics/tests/parity_bands.rs``
  against ``prinet==3.0.0``).
* **PAC is a relaxation term, not an assignment.** The reference replaces
  ``A_fast`` with ``A_fast · [1 + m·cos(mean(φ_slow) + offset)]`` between band
  steps; the continuous form adds ``λ_fast · (A_target − A_fast)`` to
  ``dA_fast/dt``, relaxing toward the same target on the band's own amplitude
  timescale.
* **Sub-stepping is the integrator's job.** The reference's per-band
  ``sub_steps`` is reproduced by driving a ``BandNetwork`` with
  :class:`prin.dynamics.MultiRateIntegrator`. The ratio itself is
  ``BandNetwork.theoretical_capacity`` — see :doc:`capacity_analysis`.

The trainable discrete-time variant ``DiscreteDeltaThetaGamma`` lives in
``prin-train::bands`` because it requires autodiff.

Choosing a mode
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Situation
     - Recommendation
   * - Global synchronization, large *N*
     - ``mean_field`` — ``O(N)`` and the analytically tractable case.
   * - Spatially extended chimera states
     - ``ring`` with a modest *k*; chimeras are a nearest-neighbour phenomenon.
   * - Large *N* with local structure
     - ``sparse_knn`` (adaptive) or ``small_world`` (fixed graph with
       shortcuts).
   * - Exact interaction matrix, small *N*
     - ``CouplingMode.full(matrix=...)`` on the core surface.
   * - Quick throughput measurement
     - ``OscilloSim(coupling_mode="auto")`` and read ``result.throughput`` —
       then record the environment with it.

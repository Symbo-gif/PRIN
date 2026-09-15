Getting Started
===============

.. note::
   Every code block on this page was executed against PRIN |release| on
   CPython 3.14 / torch 2.11 (CPU) during WP-037 S1 (session ``0145``).
   Documentation Standards §1.4 requires examples to run; the printed values
   below are the real output of those runs, not illustrations.

PRIN is the from-scratch Rust + Python rebuild of PRINet 3.0. Coupled
oscillators, band networks, tensor decompositions, and the trainable layers
are all implemented in the Rust workspace; the Python package is a thin typed
API over them. You write ordinary PyTorch code and the numerics never leave
Rust.

Installation
------------

Released wheel:

.. code-block:: bash

   pip install prin

Development install (builds the Rust core with ``maturin``):

.. code-block:: bash

   git clone https://github.com/Symbo-gif/PRIN.git
   cd PRIN
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # Linux / macOS
   pip install maturin
   maturin develop -m crates/prin-py/Cargo.toml
   pip install -e ".[dev]"

Verify the installation
-----------------------

``prin.__version__`` is the Python distribution version;
``prin.core_version()`` is the version of the compiled Rust extension the
interpreter actually loaded. They must agree — a mismatch means a stale
``_prin_core`` against updated Python sources.

.. code-block:: python

   import prin

   print(prin.__version__)                 # 0.3.0
   print(prin.core_version())              # 0.3.0
   print(len(prin.__all__))                # 175

Every symbol in the frozen PRINet 3.0 public API resolves from ``prin``. The
freeze is checked mechanically:

.. code-block:: python

   from prin._deprecation import verify_api_surface

   print(verify_api_surface(prin.__all__))  # (set(), set())

The two sets are ``(missing, unexpected)``; both empty means the RC1 public
surface matches the frozen contract exactly.

Tutorial 1 — one-line large-scale simulation
--------------------------------------------

``quick_simulate`` runs a Kuramoto / Stuart–Landau network and reports
throughput. ``coupling_mode="auto"`` picks the coupling representation from
``n_oscillators``: CSR below 1 000, sparse k-NN up to 100 000, mean-field
above.

.. code-block:: python

   from prin import quick_simulate

   res = quick_simulate(n_oscillators=2000, n_steps=200, seed=0)
   print(res.coupling_mode)              # sparse_knn
   print(round(res.throughput))          # 13671334  oscillator-steps / second
   print(len(res.order_parameter))       # 21  (recorded every 10 steps)

``SimulationResult`` carries ``final_phase``, ``final_amplitude``,
``order_parameter`` (the recorded *R* series), ``wall_time_s``,
``throughput``, ``n_oscillators``, ``n_steps``, ``coupling_mode``, ``device``,
and ``trajectory_phase`` (populated only when you ask for it).

.. admonition:: Throughput is environment-specific
   :class: caution

   The number above was measured on the maintainer's workstation. Benchmarking
   and Reproducibility Standards require the environment to travel with any
   quoted timing, so treat printed throughputs as illustrations of the API,
   never as results. The governed measurements live in
   ``benchmarks/results/`` with their environment block.

Tutorial 2 — recording a trajectory
-----------------------------------

``OscilloSim`` is the configurable simulator. ``record_trajectory=True``
returns the phase matrix at every ``record_interval`` steps.

.. code-block:: python

   import matplotlib.pyplot as plt
   from prin import OscilloSim

   sim = OscilloSim(n_oscillators=256, coupling_strength=3.0,
                    coupling_mode="mean_field", seed=0)
   res = sim.run(n_steps=300, dt=0.01, record_trajectory=True, record_interval=10)

   print(res.trajectory_phase.shape)     # torch.Size([31, 256])
   print(sim.state_summary())
   # {'n_oscillators': 256, 'coupling_mode': 'mean_field',
   #  'coupling_strength': 3.0, 'mu': 1.0, 'phase_lag': 0.0,
   #  'device': 'cpu', 'dtype': 'torch.float32'}

   fig, axes = plt.subplots(1, 2, figsize=(9, 3))
   axes[0].imshow(res.trajectory_phase.T, aspect="auto", cmap="hsv")
   axes[0].set(xlabel="recorded step", ylabel="oscillator")
   axes[1].plot(res.order_parameter)
   axes[1].set(xlabel="recorded step", ylabel="order parameter $R$")
   plt.show()

Note that ``order_parameter`` and ``trajectory_phase`` are indexed by
*recorded* step, not by integration step: 300 steps at
``record_interval=10`` give 31 records (including the initial state).

Tutorial 3 — the synchronization transition
-------------------------------------------

Sweep the coupling strength *K* and watch the order parameter *R* rise through
the Kuramoto transition. The critical coupling scales with the spread of
natural frequencies, so the sweep below narrows ``freq_std`` from its default
of ``0.5`` to ``0.05`` to bring :math:`K_c` into a compact range.

.. code-block:: python

   import matplotlib.pyplot as plt
   import numpy as np
   from prin import OscilloSim

   ks = np.linspace(0.0, 2.0, 9)
   rs = [
       OscilloSim(n_oscillators=256, coupling_strength=float(k),
                  coupling_mode="mean_field", freq_mean=5.0, freq_std=0.05,
                  seed=0).run(n_steps=1200, dt=0.01).order_parameter[-1]
       for k in ks
   ]
   print([round(r, 3) for r in rs])
   # [0.057, 0.093, 0.2, 0.472, 0.813, 0.931, 0.969, 0.978, 0.984]

   plt.plot(ks, rs, marker="o")
   plt.xlabel("coupling strength $K$")
   plt.ylabel("final order parameter $R$")
   plt.show()

With the default ``freq_std=0.5`` the same sweep needs
``np.linspace(0.0, 16.0, 9)`` and transitions near :math:`K \approx 6\text{–}8``
(:math:`R` goes 0.025 → 0.379 → 0.824 → 0.974).

.. admonition:: ``OscilloSim`` coupling strength is not the textbook Kuramoto *K*
   :class: important

   ``OscilloSim`` is a line-for-line port of the PRINet 3.0 simulator, whose
   step equations scale the coupling term differently from the textbook
   mean-field Kuramoto model. At ``freq_std=0.5`` the simulator needs
   :math:`K \approx 8` to synchronize, whereas the Rust core's
   ``KuramotoOscillator`` in mean-field mode synchronizes at :math:`K = 1` for
   a comparable spread. Both are correct in their own frame — verified
   differentially against ``prinet==3.0.0`` during WP-037 S1, where PRIN and
   the reference agreed to within 0.04 in *R* across the whole sweep. Do not
   compare an ``OscilloSim`` *K* against a ``KuramotoOscillator`` *K*, and do
   not compare either against the analytic :math:`K_c = 2/(\pi g(0))`.

Tutorial 4 — the float64 Rust core directly
-------------------------------------------

``prin.dynamics`` re-exports the compiled core types. They are NumPy
``float64`` and are the reference against which every tolerance in the
:doc:`parity_report` is measured. Deterministic construction goes through the
``Seed`` type — there is no hidden RNG anywhere in the stack.

.. code-block:: python

   import numpy as np
   import torch
   from prin import kuramoto_order_parameter
   from prin.dynamics import (
       CouplingMode,
       KuramotoOscillator,
       OscillatorState,
       RK4Integrator,
       Seed,
   )

   model = KuramotoOscillator(64, 2.0, 0.1, 0.0, CouplingMode.mean_field())
   state = OscillatorState.create_random(64, (1.0, 5.0), Seed(0, 42))
   integrator = RK4Integrator()

   for _ in range(200):
       state = integrator.step(model, state, 0.01)

   print(state.phase.dtype)              # float64
   r = kuramoto_order_parameter(torch.from_numpy(state.phase))
   print(round(float(r), 6))             # 0.968879

``KuramotoOscillator`` takes five required arguments —
``(n_oscillators, coupling_strength, decay_rate, freq_adaptation_rate,
coupling_mode)`` — and ``coupling_mode`` is a ``CouplingMode`` value, not a
string. For a custom interaction graph, ``CouplingMode.full`` takes a **flat
row-major** ``float64`` array of length :math:`N^2`:

.. code-block:: python

   n = 32
   weights = np.zeros((n, n))
   weights[: n // 2, : n // 2] = 1.0      # two clusters
   weights[n // 2 :, n // 2 :] = 1.0

   model = KuramotoOscillator(
       n, 2.0, 0.1, 0.0,
       CouplingMode.full(matrix=np.ascontiguousarray(weights.ravel())),
   )

See :doc:`coupling_topologies` for the full mode catalogue.

Tutorial 5 — a trainable band network
-------------------------------------

``prin.nn`` modules are ordinary ``torch.nn.Module``s. ``DiscreteDeltaThetaGamma``
is the discrete-time δ/θ/γ network: its per-band frequencies, intra-band
coupling matrices, PAC gates, and amplitude growth rates are ``nn.Parameter``s,
and every ``step`` pushes them into the Rust owner before running the Rust
forward.

.. code-block:: python

   import torch
   from prin.nn import DiscreteDeltaThetaGamma

   net = DiscreteDeltaThetaGamma(n_delta=4, n_theta=8, n_gamma=32)
   print(net.n_total)                    # 44

   phase = torch.rand(16, net.n_total) * 2 * torch.pi
   amplitude = torch.ones(16, net.n_total)

   phase, amplitude = net.step(phase, amplitude, dt=0.01)
   print(phase.shape)                    # torch.Size([16, 44])

   loss = phase.sum() + amplitude.sum()
   loss.backward()
   print(sum(p.grad is not None for p in net.parameters()))   # 13

   r_delta, r_theta, r_gamma = net.order_parameters(phase)
   print([round(float(r.mean()), 3) for r in (r_delta, r_theta, r_gamma)])
   # [0.979, 0.938, 0.912]

.. admonition:: Not every layer exposes torch-owned parameters
   :class: caution

   The layer family is not uniform in where its weights live.
   ``DiscreteDeltaThetaGamma`` and ``HierarchicalResonanceLayer`` declare real
   ``nn.Parameter``s that a torch optimizer can update.
   ``DiscreteDeltaThetaGammaLayer`` and ``ResonanceLayer`` keep their weights
   inside the Rust bridge: gradients still flow to the *input* (so they compose
   inside a larger differentiable model), but ``parameters()`` is empty or
   disconnected from ``forward``, and ``rust_state_dict()`` returns them as
   opaque bytes. Check ``sum(p.numel() for p in layer.parameters())`` before
   handing a layer to an optimizer. This asymmetry is recorded as an
   out-of-scope discovery in the WP-037 S1 handoff note
   (``DOCS/experiments/0145-wp037-s1-handoff.md``) for audit classification.

Tutorial 6 — phase-to-rate readout
----------------------------------

.. code-block:: python

   import torch
   from prin.nn import PhaseToRateConverter

   conv = PhaseToRateConverter(n_oscillators=44, mode="soft", sparsity=0.1)
   rates = conv(torch.randn(8, 44), torch.ones(8, 44))
   print(rates.shape)                    # torch.Size([8, 44])
   print(rates.requires_grad)            # True

``mode="soft"`` is fully differentiable; ``mode="hard"`` is a straight-through
estimator over a non-differentiable top-k selection, matching the reference
(Project Plan amendment #34, disposition D-3).

Migrating from ``prinet``
-------------------------

PRIN keeps the PRINet 3.0 public API. In most code you only change the import
root:

.. code-block:: python

   # old
   from prinet import KuramotoOscillator, PRINetModel

   # new
   from prin import KuramotoOscillator, PRINetModel

Symbols that moved namespace, changed signature, or were dispositioned as
documented stubs are listed row by row in the :doc:`migration_guide`, which is
machine-checked against ``DOCS/baselines/wp001_api_traceability.md`` by
``tools/wp036_migration_table.py``.

Two namespace changes trip people up most often:

* ``CouplingMode``, ``Seed``, ``RK4Integrator``, and the other core types are
  in :mod:`prin.dynamics`, not at the top level.
* ``chimera_index``, ``cosine_coupling_kernel``, and
  ``strength_of_incoherence`` are in :mod:`prin.simulation`, not at the top
  level.

Next steps
----------

* :doc:`architecture` — the two-layer design and how a tensor reaches Rust.
* :doc:`coupling_topologies` — the coupling-mode catalogue.
* :doc:`capacity_analysis` — θ/γ binding capacity.
* ``notebooks/`` — four runnable tutorials; see :doc:`notebooks`.
* :doc:`parity_report` — every measured deviation from PRINet 3.0.

Simulation API (``prin.simulation``)
====================================

The ``prinet.utils.oscillosim`` rebuild: a batched, ``torch.Tensor``-facing
Kuramoto / Stuart–Landau network simulator plus the coupling-topology and
chimera-diagnostic helpers that surround it. ``OscilloSim`` orchestrates
state construction, neighbour-index building, and stepping; the arithmetic it
calls is owned by the Rust core (``prin-dynamics``, ``prin-kernels``) and by
:mod:`prin.topology`.

:mod:`prin.simulation_experiments` holds the Year-4-Q1.8 benchmark scaffolding
(heterogeneous natural frequencies, multi-scale topologies, evolutionary
coupling updates, conduction-delay matrices) that the chimera experiments are
built from.

Runtime budget: the defaults (``n_oscillators=1000``, ``euler``) are chosen so
that every example in :doc:`../getting_started` and in
``notebooks/01_oscillosim_quickstart.ipynb`` runs in seconds on CPU.

.. automodule:: prin.simulation
   :members:

.. automodule:: prin.simulation_experiments
   :members:
   :no-index:

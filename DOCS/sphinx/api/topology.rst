Topology API (``prin.topology``)
================================

PRINet 3.0-compatible coupling-topology builders. Thin wrappers that
construct ``(N, k)`` neighbour-index tensors for ring and Watts–Strogatz
small-world topologies; the discrete index arithmetic and the deterministic
rewiring RNG are owned by the Rust core (``ring_topology_indices`` /
``small_world_topology_indices`` in ``prin._prin_core``).

A custom topology is just an ``(N, k)`` integer tensor of neighbour indices —
see :doc:`../coupling_topologies` for the full topology catalogue and
``notebooks/03_custom_coupling.ipynb`` for a worked two-cluster example.

.. automodule:: prin.topology
   :members:

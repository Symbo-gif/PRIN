PRIN — Phase-Resonance Interference Network
===========================================

PRIN is a scientific ML framework built on coupled-oscillator dynamics
(Kuramoto, Stuart–Landau, Hopf), hierarchical δ/θ/γ band networks with
phase–amplitude coupling, polyadic tensor decomposition, and
PyTorch-compatible trainable layers for temporal object binding and
multi-object tracking. It is the from-scratch Rust + Python rebuild of
PRINet 3.0.

All numerical authority lives in the Rust workspace (``prin-dynamics``,
``prin-metrics``, ``prin-tensor``, ``prin-kernels``, ``prin-sim``,
``prin-train``, ``prin-daemon``) behind the ``prin-py`` PyO3 bridge; the
Python package is a thin, fully typed API layer with no numerics of its own.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   getting_started
   architecture
   coupling_topologies
   capacity_analysis
   migration_guide
   kernel_architecture
   parity_report
   notebooks
   paper

.. toctree::
   :maxdepth: 2
   :caption: Python API reference

   api/core
   api/dynamics
   api/simulation
   api/kernels
   api/solvers
   api/metrics
   api/topology
   api/nn
   api/tensor
   api/train
   api/daemon
   api/subconscious
   api/dlpack
   api/datasets
   api/temporal
   api/eval
   api/experiments
   api/adversarial
   api/experiment_tools
   api/reporting
   api/parity
   api/utils
   api/compat

.. toctree::
   :maxdepth: 2
   :caption: Rust API reference

   rust_api

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

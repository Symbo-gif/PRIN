Utilities API (``prinet.utils`` → PRIN)
=======================================

PRINet 3.0 collected its non-model helpers in a ``prinet.utils`` package
(``oscillosim``, ``datasets``, ``temporal_metrics``, ``temporal_training``,
``fused_kernels``, ``triton_kernels``, ``cuda_kernels``, ``profiler``,
``benchmark_reporting``, ``figure_generation``, ``table_generation``,
``npu_backend``, ``adversarial_tools``, ``y4q1_tools``, ``statistics``,
``flops``, ``adversarial``). PRIN has **no ``prin.utils`` module**: the
package was dissolved during the rebuild so that each helper lives beside the
Rust crate that owns its numerics, and the flat ``prin`` namespace re-exports
the public names (Project Plan §4 rule 2, "one algorithm, one
implementation"; Documentation Standards §2.2).

This page is the lookup index for that dissolution. Every row is the
documented disposition in :doc:`../migration_guide`; the per-module reference
pages carry the autodoc.

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - PRINet 3.0 module
     - PRIN owner
     - Reference page
   * - ``prinet.utils.oscillosim``
     - :mod:`prin.simulation`, :mod:`prin.simulation_experiments`
     - :doc:`simulation`
   * - ``prinet.utils.fused_kernels``
     - :mod:`prin.kernels` (``pytorch_*`` CPU references)
     - :doc:`kernels`
   * - ``prinet.utils.triton_kernels``
     - :mod:`prin._compat` availability stubs (``triton_available()`` → ``False``)
     - :doc:`compat`
   * - ``prinet.utils.cuda_kernels`` (solver family)
     - :mod:`prin.solvers`
     - :doc:`solvers`
   * - ``prinet.utils.cuda_kernels`` (fused steps)
     - :mod:`prin.kernels`
     - :doc:`kernels`
   * - ``prinet.utils.datasets``
     - :mod:`prin.datasets`
     - :doc:`datasets`
   * - ``prinet.utils.temporal_metrics``
     - :mod:`prin.temporal_metrics`, :mod:`prin.eval`
     - :doc:`temporal`, :doc:`eval`
   * - ``prinet.utils.temporal_training``
     - :mod:`prin.temporal_training`
     - :doc:`temporal`
   * - ``prinet.utils.statistics``
     - :mod:`prin.experiments` (``bootstrap_ci``, ``welch_t_test``, ``cohens_d``)
     - :doc:`experiments`
   * - ``prinet.utils.flops``
     - :mod:`prin.experiments`, :mod:`prin.reporting.profiler`
     - :doc:`experiments`, :doc:`reporting`
   * - ``prinet.utils.adversarial``
     - :mod:`prin.adversarial_tools`, :mod:`prin.experiments`
     - :doc:`adversarial`, :doc:`experiments`
   * - ``prinet.utils.adversarial_tools``
     - :mod:`prin.adversarial_tools`
     - :doc:`adversarial`
   * - ``prinet.utils.profiler``
     - :mod:`prin.reporting.profiler`
     - :doc:`reporting`
   * - ``prinet.utils.benchmark_reporting``
     - :mod:`prin.reporting.benchmark_reporting`
     - :doc:`reporting`
   * - ``prinet.utils.figure_generation``
     - :mod:`prin.reporting.figure_generation`
     - :doc:`reporting`
   * - ``prinet.utils.table_generation``
     - :mod:`prin.reporting.table_generation`
     - :doc:`reporting`
   * - ``prinet.utils.npu_backend``
     - :mod:`prin.daemon`, :mod:`prin.subconscious_compat`
     - :doc:`daemon`, :doc:`subconscious`
   * - ``prinet.utils.y4q1_tools``
     - :mod:`prin.y4q1_tools`
     - :doc:`experiment_tools`

Dynamics, metric, topology, and trainable-stack helpers that PRINet 3.0 kept
outside ``prinet.utils`` have their own pages: :doc:`dynamics`,
:doc:`metrics`, :doc:`topology`, :doc:`train`, :doc:`nn`, :doc:`tensor`,
:doc:`dlpack`, :doc:`parity`.

.. toctree::
   :maxdepth: 1
   :caption: Utility module reference

   simulation
   kernels
   solvers
   datasets
   temporal
   adversarial
   experiment_tools
   subconscious
   compat

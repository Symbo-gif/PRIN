Reporting API (``prin.reporting``)
==================================

Publication figure and table generation, benchmark reporting, and profiling.
Everything here is **deterministic rendering of stored benchmark values**: no
scientific quantity is recomputed, nothing is sampled, and the matplotlib
backend is forced to ``Agg`` with a fixed 2000-01-01 PDF date so that a
regenerated artefact is byte-comparable to the one the governed SHA-256
manifest was built from.

The output-root constants are part of the contract, not an implementation
detail — the ported acceptance suite imports them directly
(``from prin.reporting.figure_generation import DEFAULT_OUTPUT_DIR``), and
``tests/test_paper_wiring.py`` pins them to the ``paper/`` tree. See
:doc:`../paper` for the artefact pipeline.

.. automodule:: prin.reporting
   :members:

Submodules
----------

.. automodule:: prin.reporting.figure_generation
   :members:
   :no-index:

.. automodule:: prin.reporting.table_generation
   :members:
   :no-index:

.. automodule:: prin.reporting.benchmark_reporting
   :members:
   :no-index:

.. automodule:: prin.reporting.profiler
   :members:
   :no-index:

.. automodule:: prin.reporting._artifacts
   :members:
   :no-index:

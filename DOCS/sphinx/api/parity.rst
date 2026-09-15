Parity API (``prin.parity``)
============================

The golden-corpus differential harness that backs the parity CI job and every
tolerance quoted in :doc:`../parity_report`.

``prin.parity.schema`` owns the registered tolerances — ``METRIC_RTOL`` and
``METRIC_ATOL`` — and the corpus record types. Those constants are the single
place a tolerance may be changed, and changing one requires a PR note, reviewer
sign-off, and a Parity Report entry (Testing Standards §3). They are not
re-exported at package level, so the submodule section below is where they are
documented.

``prin.parity.strategies`` holds the ``hypothesis`` strategies the fuzzing leg
draws from (``seed_strategy``, ``model_strategy``, ``n_oscillators_strategy``,
``n_steps_strategy``, ``dt_strategy``, ``coupling_strategy``,
``coupling_strength_strategy``, ``integrator_strategy``,
``model_parameters_strategy``).

.. automodule:: prin.parity
   :members:

Submodules
----------

.. automodule:: prin.parity.schema
   :members:
   :no-index:

.. automodule:: prin.parity.loader
   :members:
   :no-index:

.. automodule:: prin.parity.manifest
   :members:
   :no-index:

.. automodule:: prin.parity.harness
   :members:
   :no-index:

.. automodule:: prin.parity.strategies
   :members:
   :no-index:

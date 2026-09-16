Temporal API (``prin.temporal_metrics``, ``prin.temporal_training``)
====================================================================

The temporal-binding half of the PRINet 3.0 surface, split the way the
reference split it: measurement in :mod:`prin.temporal_metrics`, training in
:mod:`prin.temporal_training`.

:mod:`prin.temporal_metrics` — Year-4-Q1.7 multi-object-tracking metrics:
identity switches, track fragmentation, identity overcount, mostly-tracked /
mostly-lost, track duration, recovery speed, binding robustness, and
temporal smoothness. The evaluation-facing wrappers that return a single
metrics bundle live in :mod:`prin.eval`.

:mod:`prin.temporal_training` — the unified temporal training framework used
for the fair PhaseTracker-vs-SlotAttention comparison: the CLEVR-N temporal
sequence generators, the Hungarian similarity-matching and temporal-smoothness
losses, and the complex-aware parameter helpers. It is a faithful port
(Testing Standards §1.1); the numerics it needs are owned by
``prin_train::dataset``, ``prin_train::losses``, ``prin_train::trainer``, and
``prin_train::temporal_metrics`` in Rust.

.. automodule:: prin.temporal_metrics
   :members:

.. automodule:: prin.temporal_training
   :members:
   :no-index:

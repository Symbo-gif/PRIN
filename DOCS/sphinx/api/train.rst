Training API (``prin.train``, ``prin.training_hooks``)
======================================================

Rust-native trainable-stack orchestration entry points (WP-027) and the
PRINet 3.0-compatible observation / active-control hook surface.

:mod:`prin.train` is a thin Python wrapper around the Rust-native temporal
CLEVR-N training pipeline (``crates/prin-train/src/trainer.rs``: Adam, linear
warmup + cosine learning-rate schedule, gradient clipping, early stopping).
All numerics run in Rust (Project Plan §4 rule 2 — no Python numerics).

:mod:`prin.training_hooks` performs bookkeeping only: accumulating telemetry
records and buffering control signals for the observation / control surface
that PRINet 3.0 exposed as ``prinet.nn.training_hooks`` and
``prinet.core.subconscious``. The controller that consumes those signals is
:doc:`subconscious`.

For the trainable ``torch.nn.Module`` layers themselves see :doc:`nn`; for the
``torch.autograd`` bridges over the Rust kernels see :doc:`dlpack` and
:doc:`compat`.

.. automodule:: prin.train
   :members:

.. automodule:: prin.training_hooks
   :members:
   :no-index:

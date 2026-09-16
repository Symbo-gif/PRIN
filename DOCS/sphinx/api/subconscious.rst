Subconscious Compatibility API (``prin.subconscious_compat``)
=============================================================

Single acceptance owner for the four PRINet 3.0 reference modules the
``test_subconscious`` suite imports: ``prinet.core.subconscious`` (the
``SubconsciousState`` / ``ControlSignals`` data types and the thread-safe
controller), ``prinet.nn.subconscious_model`` (the inference half),
``prinet.core.control_buffer``, and ``prinet.core.control_buffer_pool``.

The control transformation itself is not in Python. It is the re-exported
three-input-``Gemm`` ONNX controller graph in ``models/subconscious_controller.onnx``,
executed by the Rust ``prin-daemon`` crate through ONNX Runtime; see
:doc:`daemon` for the execution-provider selection policy, the WP-036F
DirectML discharge, and the bit-identity evidence.

This module contributes only what Rust cannot reach — the ``onnxruntime``
session object, the control-buffer bookkeeping, and the typed errors that
report an unavailable provider. The VitisAI / Ryzen AI NPU path stays
hardware-gated (DV-006, standing-external disposition); the DirectML path is
closed.

.. automodule:: prin.subconscious_compat
   :members:
   :exclude-members: SubconsciousState, ControlSignals, BackendType

``SubconsciousState``, ``ControlSignals``, and ``BackendType`` are excluded here
and documented on :doc:`daemon`, which is where ``prin`` re-exports them from;
describing them on both pages makes every cross-reference to them ambiguous,
which ``sphinx-build -W`` reports as "more than one target found".

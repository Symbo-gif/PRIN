Daemon API (prin.daemon)
========================

Subconscious controller: ONNX inference and execution-provider selection.
Rebuild of PRINet 3.0 ``prinet.utils.npu_backend`` and the inference half
of ``prinet.nn.subconscious_model``. Every numeric transformation and every
selection decision lives in the Rust ``prin-daemon`` crate and is reached
through ``prin._prin_core``; this module contributes only what Rust cannot
reach — the ``onnxruntime`` session object and the environment/filesystem
values that feed the Rust functions.

The ONNX session is created in Python rather than in Rust by Project Plan
§7 risk register #4: the VitisAI execution provider ships only inside the
Ryzen AI SDK's custom ONNX Runtime Python wheel and DirectML only as a
platform-specific wheel, so neither is reachable from the ``ort`` crate's
prebuilt binaries.

.. automodule:: prin.daemon
   :members:
   :undoc-members:

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

Controller graph — three-input ``Gemm`` re-export (WP-036F)
-----------------------------------------------------------------

``models/subconscious_controller.onnx`` originates unchanged from PRINet 3.0,
whose PyTorch export emitted two-input ``Gemm`` nodes (no bias term — the
``nn.Linear`` biases were zero-initialised and never trained). ONNX Runtime's
``DmlExecutionProvider`` fuses ``Gemm`` + ``Relu`` into a ``DmlFusedGemm``
node whose schema requires three inputs, so it rejected the graph with
``InvalidGraph: ... input size 2 not in range [min=3, max=3]`` and the daemon
fell back to CPU on every DirectML host (Project Plan amendment #13).

WP-036F (session ``0144U``) re-exported the graph with an explicit
zero-valued ``float32`` bias per layer (``net.0.bias`` / ``net.3.bias`` /
``net.6.bias``). Because ``Gemm`` computes ``Y = α·A'·B' + β·C`` with
``β = 1`` and ``C = 0``, the graph's function is unchanged — it is
bit-identical to the pre-transform graph on ``CPUExecutionProvider`` over the
48-case differential set (``max_abs_diff = 0.0``). ``DmlExecutionProvider``
now executes the re-exported graph directly and agrees with the CPU provider
at ``max_abs_diff = 7.15e-7``, within ``rtol=1e-5, atol=1e-6``. DirectML
inference latency on this ~50 K-parameter MLP is dispatch-bound and higher
than CPU (batch 48, median of 500 warm calls: CPU ≈ 0.033 ms,
DirectML ≈ 0.27 ms); this is recorded, not a regression — the daemon's
backend-selection policy is unchanged and does not select DirectML for the
controller by default. Regenerate or re-verify with
``tools/wp036f_reexport_controller.py`` (``--check`` fails on any drift);
provider/latency evidence is
``EVIDENCE/0144U-wp036f-s1-controller-provider-report.json``.

This closed the DirectML half of DV-006 (WP-036F S4, ``0144X``). The
VitisAI / Ryzen AI NPU half stays open, hardware-gated (no XDNA NPU on the
maintainer host; the Ryzen AI SDK ships VitisAI only as a CPython 3.12
wheel).

.. automodule:: prin.daemon
   :members:

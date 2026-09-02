"""Shared hardware/runtime capability probes for environment-gated tests.

ETCA-002 finding T-F3 / governance G4: a ``skipif`` guarding a hardware or
runtime feature must probe **executability** (attempt the operation), not
**registration**. ``onnxruntime.get_available_providers()`` returns every
provider *compiled into the wheel* — on a GitHub-hosted ``windows-latest``
runner ``onnxruntime-directml`` registers ``DmlExecutionProvider`` even though
no DirectML-capable adapter is present, so a
``"DmlExecutionProvider" not in ort.get_available_providers()`` guard does not
fire and the guarded test runs and hard-fails.

``directml_executes()`` builds a one-node session pinned to
``DmlExecutionProvider`` and runs it: it is ``True`` only on a host where
DirectML actually executes a graph (the maintainer host, ``PRIN-GPU-Runner``),
``False`` on a hosted runner with the provider registered but no device — so
the test *skips* there instead of failing, and *runs* on the real-GPU runner.
"""

from __future__ import annotations

import functools

_DML = "DmlExecutionProvider"


@functools.lru_cache(maxsize=1)
def directml_executes() -> bool:
    """Whether ``DmlExecutionProvider`` can actually execute a graph on this host."""
    try:
        import numpy as np
        import onnx
        import onnxruntime as ort
    except ImportError:
        return False

    if _DML not in ort.get_available_providers():
        return False

    try:
        graph = onnx.helper.make_graph(
            [onnx.helper.make_node("Identity", ["x"], ["y"])],
            "directml_probe",
            [onnx.helper.make_tensor_value_info("x", onnx.TensorProto.FLOAT, [1])],
            [onnx.helper.make_tensor_value_info("y", onnx.TensorProto.FLOAT, [1])],
        )
        model = onnx.helper.make_model(
            graph, opset_imports=[onnx.helper.make_opsetid("", 13)]
        )
        session = ort.InferenceSession(model.SerializeToString(), providers=[_DML])
        if session.get_providers()[:1] != [_DML]:
            return False
        session.run(None, {"x": np.zeros(1, dtype=np.float32)})
    except Exception:
        return False
    return True

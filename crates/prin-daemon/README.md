# prin-daemon

Subconscious controller for PRIN: native daemon thread, lock-free control-signal
ring buffer, and ONNX inference (`ort`) with VitisAI → DirectML → CPU backend
detection. Runs `models/subconscious_controller.onnx`.

Rebuild target for PRINet 3.0 `core/subconscious*.py` and
`utils/npu_backend.py`.

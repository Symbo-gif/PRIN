# models/

Pre-trained model artefacts.

- `subconscious_controller.onnx` (18 KB) — the ONNX graph for the
  pre-trained subconscious controller, copied unchanged from PRINet 3.0 and
  consumed by `prin-daemon` on CPU / DirectML / Ryzen AI NPU backends.
- `subconscious_controller.onnx.data` (86 KB) — external tensor data
  companion for the above graph. The two files together total ~104 KB.

Both files are exempt from the `*.onnx` and `*.onnx.data` gitignore rules and
are validated against the SHA-256 manifest by `tools/reproduce.py`.

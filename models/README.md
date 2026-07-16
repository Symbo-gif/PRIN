# models/

Pre-trained model artefacts.

- `subconscious_controller.onnx` (104 KB) — the pre-trained subconscious
  controller, copied unchanged from PRINet 3.0 and consumed by `prin-daemon`
  on CPU / DirectML / Ryzen AI NPU backends. Validated against the SHA-256
  manifest by `tools/reproduce.py`.

Only this file is exempt from the `*.onnx` gitignore rule.

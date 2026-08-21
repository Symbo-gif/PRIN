# models/

Pre-trained model artefacts.

- `subconscious_controller.onnx` (18 KB) — the ONNX graph for the
  pre-trained subconscious controller, copied unchanged from PRINet 3.0 and
  consumed by `prin-daemon` on CPU / DirectML / Ryzen AI NPU backends.
- `subconscious_controller.onnx.data` (86 KB) — external tensor data
  companion for the above graph. The two files together total ~104 KB.

- `manifest.json` — the SHA-256 + size manifest covering both files
  (WP-028). It is the authority for the integrity check that
  `prin_daemon::model::ModelManifest::verify` and
  `prin.daemon.verify_model_artefacts` run before any ONNX session is created,
  and `prin.daemon.SubconsciousController` looks its expected digest up here
  automatically.

Both model files are exempt from the `*.onnx` and `*.onnx.data` gitignore
rules. `tools/reproduce.py` will consume the same manifest when the Phase 6
reproducibility pipeline lands.

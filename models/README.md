# models/

Pre-trained model artefacts.

- `subconscious_controller.onnx` (19 KB) — the ONNX graph for the
  pre-trained subconscious controller, consumed by `prin-daemon` on
  CPU / DirectML / Ryzen AI NPU backends. The graph originates unchanged from
  PRINet 3.0; **WP-036F (session 0144U)** re-exported it with three-input
  `Gemm` nodes — an explicit zero-valued `float32` bias per layer
  (`net.0.bias` / `net.3.bias` / `net.6.bias`, all zeros) — so ONNX Runtime's
  `DmlExecutionProvider` accepts it (its `DmlFusedGemm` fusion rejects the
  two-input `Gemm` form). The transform adds a zero bias, so the graph's
  function is unchanged: it is bit-identical to the pre-transform graph on
  `CPUExecutionProvider` over the 48-case differential set. Regenerate or
  verify with `tools/wp036f_reexport_controller.py`
  (`--check` fails on any drift). The pristine pre-transform graph is
  preserved at
  `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/models/`.
  `DmlExecutionProvider` executes the re-exported graph and agrees with the
  CPU provider within `rtol=1e-5, atol=1e-6` (WP-036F S4, session `0144X`,
  closed the DirectML half of DV-006); the Ryzen AI NPU (VitisAI) half stays
  open, hardware-gated.
- `subconscious_controller.onnx.data` (86 KB) — external tensor data
  companion for the above graph (the three MLP weight matrices). The bias
  tensors are stored inline in the `.onnx` file, so this companion is
  byte-identical to the PRINet 3.0 original. The two files together total
  ~105 KB.

- `manifest.json` — the SHA-256 + size manifest covering both files
  (WP-028). It is the authority for the integrity check that
  `prin_daemon::model::ModelManifest::verify` and
  `prin.daemon.verify_model_artefacts` run before any ONNX session is created,
  and `prin.daemon.SubconsciousController` looks its expected digest up here
  automatically.

Both model files are exempt from the `*.onnx` and `*.onnx.data` gitignore
rules. `tools/reproduce.py` will consume the same manifest when the Phase 6
reproducibility pipeline lands.

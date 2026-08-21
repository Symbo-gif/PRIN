# prin-daemon

Subconscious controller for PRIN. Rebuild target for PRINet 3.0
`core/subconscious*.py` and `utils/npu_backend.py`; drives
`models/subconscious_controller.onnx`.

## Delivered (WP-028)

| Module | Contents |
|---|---|
| `state` | `SubconsciousState`, `ControlSignals`, `Regime`, `STATE_DIM = 32`, `CONTROL_DIM = 8` — PRINet 3.0's exact float32 packing, normalisation, and clamping semantics (bit-exact parity, `tests/parity_subconscious.rs`) |
| `backend` | `Backend`, `select_backend`, `provider_options`, `resolve_firmware` — VitisAI → DirectML → CPU priority, explicit-override handling, and the deterministic CPU-terminated fallback ladder |
| `onnx` | `inspect_onnx_file` — runtime-independent decoding of an ONNX `ModelProto`'s graph inputs, outputs, opsets, ops, and external-data references |
| `model` | `ModelManifest`, `verify_sha256`, `ControllerModel::validate` — SHA-256 integrity against `models/manifest.json`, external-data completeness, and the `state_vector`/`control_signals` graph contract |

The crate performs no inference itself. ONNX Runtime sessions are created
through the Python `onnxruntime` bindings in `python/prin/daemon.py`, per
Project Plan §7 risk register #4: the VitisAI execution provider ships only
inside the Ryzen AI SDK's custom ONNX Runtime Python wheel and DirectML only as
a platform-specific wheel, so neither is reachable from the `ort` crate's
prebuilt binaries. The `npu` cargo feature stays reserved for a future native
binding.

## Not yet delivered

The native daemon thread, its lifecycle, and the lock-free control-signal ring
buffer (PRINet 3.0's `ControlSignalBuffer` and `subconscious_daemon.py`) are
**WP-029** scope and are deliberately absent from this crate today.

## Features

| Feature | Effect |
|---|---|
| `strict-checks` | `SubconsciousState::to_tensor` returns `DaemonError::NonFiniteValue` for NaN/infinite telemetry instead of packing it unchanged |
| `npu` | Reserved for a future native `ort` binding; currently a no-op |

# prin-daemon

Subconscious controller for PRIN. Rebuild target for PRINet 3.0
`core/subconscious*.py`, `core/subconscious_daemon.py`, and
`utils/npu_backend.py`; drives `models/subconscious_controller.onnx`.

## Delivered (WP-028)

| Module | Contents |
|---|---|
| `state` | `SubconsciousState`, `ControlSignals`, `Regime`, `STATE_DIM = 32`, `CONTROL_DIM = 8` — PRINet 3.0's exact float32 packing, normalisation, and clamping semantics (bit-exact parity, `tests/parity_subconscious.rs`) |
| `backend` | `Backend`, `select_backend`, `provider_options`, `resolve_firmware` — VitisAI → DirectML → CPU priority, explicit-override handling, and the deterministic CPU-terminated fallback ladder |
| `onnx` | `inspect_onnx_file` — runtime-independent decoding of an ONNX `ModelProto`'s graph inputs, outputs, opsets, ops, and external-data references |
| `model` | `ModelManifest`, `verify_sha256`, `ControllerModel::validate` — SHA-256 integrity against `models/manifest.json`, external-data completeness, and the `state_vector`/`control_signals` graph contract |

## Delivered (WP-029)

| Module | Contents |
|---|---|
| `daemon` | `SubconsciousDaemon` — the native background thread; `ControlSignalBuffer` — a lock-free (`ArcSwap`-based) replacement for PRINet 3.0's `threading.Lock`-guarded buffer; `InferenceBackend` — the pluggable inference seam; `DaemonConfig`, `DaemonStats`, `DeadLetterEntry`, `EscalationEvent`/`EscalationCallback` |

The crate performs no inference itself. ONNX Runtime sessions are created
through the Python `onnxruntime` bindings in `python/prin/daemon.py`, per
Project Plan §7 risk register #4: the VitisAI execution provider ships only
inside the Ryzen AI SDK's custom ONNX Runtime Python wheel and DirectML only as
a platform-specific wheel, so neither is reachable from the `ort` crate's
prebuilt binaries. The `npu` cargo feature stays reserved for a future native
binding. `daemon::InferenceBackend` is the seam a Python-backed
`SubconsciousController` session is wired in through — that wiring (a PyO3
binding whose background thread calls back into a Python `SubconsciousController`
under the GIL) is **not yet delivered**; see the WP-029 S1 handoff note
(`DOCS/experiments/0113-wp029-s1-handoff.md`) for the scope decision and the
GIL-release design the follow-up needs.

## Features

| Feature | Effect |
|---|---|
| `strict-checks` | `SubconsciousState::to_tensor` returns `DaemonError::NonFiniteValue` for NaN/infinite telemetry instead of packing it unchanged; an unpackable submitted state is recorded as a `SubconsciousDaemon` inference error instead of reaching the backend |
| `npu` | Reserved for a future native `ort` binding; currently a no-op |

## Benchmarks and pilots

| File | Purpose |
|---|---|
| `benches/control_buffer.rs` | `criterion` comparison: `ControlSignalBuffer` (lock-free) vs. a `Mutex`-guarded re-implementation of the PRINet 3.0 design, under 0/1/4 writer-thread contention |
| `examples/control_buffer_pilot.rs` | Manual p50/p95/max latency pilot for the same two implementations (`cargo run --release --example control_buffer_pilot -p prin-daemon`) |
| `tools/wp029_control_buffer_pilot.py` (repo root) | The same protocol run against the actual archived PRINet 3.0 `ControlSignalBuffer`, for a genuine cross-language "before" data point |
| `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` | Combined pilot evidence with methodology and environment capture |

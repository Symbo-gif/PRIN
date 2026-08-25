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

## Delivered (WP-030)

| Module | Contents |
|---|---|
| `hooks` | `TrainingHooks` — the WP-030 rebuild of PRINet 3.0's `prinet.nn.training_hooks.StateCollector`: loss EMA/variance, gradient-norm EMA (from caller-supplied per-parameter L2 norms), and step-latency p50/p95/throughput, packaged into a `SubconsciousState` for `daemon.submit_state(hooks.on_epoch_end(...))` |
| `mot` | `MotAccumulator`, `MotSummary`, `BBox`/`iou_distance_matrix`, `generate_linear_sequence`/`generate_crowded_sequence` — the CLEAR-MOT/IDF1 core of PRINet 3.0's `prinet.nn.mot_evaluation`, validated against real `py-motmetrics` output (`tests/parity_mot.rs`); deterministic synthetic sequence generators built on `prin_dynamics::Seed` |
| `assignment` (private) | Rectangular Hungarian/Kuhn–Munkres assignment solver `mot::MotAccumulator` uses for per-frame and global (IDF1) identity matching |

`mot` deliberately does not reproduce the reference module's end-to-end
`evaluate_tracking(sequence, tracker, ...)` loop: `crates/README.md`'s
layering places `prin-train` (where `PhaseTracker` lives) and `prin-daemon`
at the same tier, so wiring a real tracker's hypotheses into this
accumulator is a Python orchestration concern (`python/prin/eval`), not a
Rust one — see `DOCS/experiments/0117-wp030-s1-handoff.md`.

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
| `benches/training_hooks.rs` | `criterion` per-call cost of `TrainingHooks::on_step_end_with_elapsed`/`on_epoch_end`; `hooks.rs`'s `step_accumulation_overhead_is_bounded` unit test is the actual overhead bound (100k calls under 2s), this bench is pilot evidence only |
| `tools/wp030_mot_fixture.py` (repo root) | Generates `tests/data/mot_reference_cases.json` by replaying fixed oid/hid/distance sequences through the real `py-motmetrics` package |

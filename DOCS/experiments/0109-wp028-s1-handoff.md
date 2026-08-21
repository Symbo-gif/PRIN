# Session 0109 — WP-028 S1 Handoff Note

**Session:** 0109 — WP-028 S1: Coding — ONNX controller and backend selection
**Date:** 2026-08-21
**Status:** S1 delivered; handoff to S2 audit (session 0110)

## Mission recap

"Implement controller state/control types, ONNX model validation, provider
detection (VitisAI→DirectML→CPU), and deterministic fallback."
Contract (`DOCS/sessions/phase-5/0109-wp028-s1-onnx-controller-and-backend-selection.md`):
outputs match 3.0 references across available providers; missing-provider
paths fall back safely; model SHA-256 is verified. Non-goals: background
runtime/threading.

## Entry conditions

| Condition | Status |
|---|---|
| Preceding S4 closed and committed | Yes — session 0108 (WP-027 S4) closed at `0163c85`; working tree clean at session start |
| WP-028 scope/acceptance/non-goals have maintainer approval | **Obtained in-session, 2026-08-21.** PSR-027 §7 recorded approval as *pending*; the maintainer approved the declared scope with the explicit deferrals recorded under "Scope decision" below |
| No unresolved D1/D2 finding | Yes — PSR-027 §3: WP-027 S2 recorded zero findings; no D1/D2 open |

## Maintainer decisions taken this session

Three decisions were maintainer-approval-class and were obtained before any
code was written.

1. **WP-028 scope** — approved as declared in PSR-027 §7, with explicit,
   recorded deferrals (below).
2. **ONNX execution path** — Project Plan §7 risk register #4 is **invoked**:
   session creation and inference stay on the Python `onnxruntime` path; the
   `ort` crate stays behind the reserved `npu` cargo feature. Evidence for the
   "EP coverage lags" condition is in "Why not the `ort` crate" below.
3. **R31 / DV-005 (CUDA Burn backend)** — the Phase 5 scoping decision R31
   assigns to this session: **defer out of Phase 5, re-gate at Phase 6
   (WP-036)**. Recorded in `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`;
   R31 closed, DV-005 remains OPEN with a concrete next gate.

## Scope decision (record per "do not expand scope silently")

Declared scope (PSR-027 §7): controller state/control types, ONNX model
validation, provider detection (VitisAI→DirectML→CPU), deterministic
fallback. Everything below sits inside that scope. Three symbols that
`DOCS/baselines/wp001_api_traceability.md` maps to WP-028 are **deferred with
maintainer approval**, because each belongs to a declared non-goal or to a
later WP's mission:

| Deferred symbol | Reason | Target |
|---|---|---|
| `ControlSignalBuffer` | Thread-safe buffer — WP-028's declared non-goal ("background runtime/threading") | **WP-029** (session 0113), whose mission is the lock-free control buffer |
| `SubconsciousController.export_to_onnx` / `.quantize_onnx` | PyTorch-side export and INT8 quantisation, i.e. training-stack work | **WP-030** (session 0117, training hooks) |
| `retrain_controller` | Supervised retraining from telemetry — training-stack work | **WP-030** |

WP-028 delivers the **inference** half of `SubconsciousController` under that
name (`prin.daemon.SubconsciousController`), documented in its own docstring
as the inference path with the training half named as WP-030 scope.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-daemon/src/state.rs` | **New.** `SubconsciousState`, `ControlSignals`, `Regime`, `STATE_DIM`, `CONTROL_DIM`, `STATE_PAYLOAD`, and the normalisation/clamp constants — PRINet 3.0's exact float32 packing and decode semantics. |
| `crates/prin-daemon/src/backend.rs` | **New.** `Backend`, `BackendSelection`, `SelectionReason`, `select_backend`, `provider_options`, `VitisAiConfig`, `firmware_candidates`, `resolve_firmware` — the VitisAI→DirectML→CPU priority policy and the deterministic fallback ladder. |
| `crates/prin-daemon/src/onnx.rs` | **New.** `OnnxModelInfo`, `TensorSpec`, `Dim`, `OpsetId`, `InitializerSpec`, `inspect_onnx_bytes`, `inspect_onnx_file` — a bounded, total ONNX `ModelProto` reader over the eleven message fields the controller contract needs. |
| `crates/prin-daemon/src/model.rs` | **New.** `sha256_file`, `sha256_file_with_size`, `verify_sha256`, `ModelManifest`, `ControllerModel::validate`, `validate_controller_contract`, `validate_external_data`. |
| `crates/prin-daemon/src/error.rs` | **New.** `DaemonError` — 18 typed variants; no `panic!`/`unwrap`/`expect` in library code. |
| `crates/prin-daemon/src/lib.rs` | Replaced the Phase-5 placeholder with module wiring, crate-level docs, scope boundaries, and a runnable crate example. |
| `crates/prin-daemon/Cargo.toml` | Added `sha2`; added `tempfile` (dev); added the `strict-checks` feature; recorded why the `ort` dependency stays reserved. |
| `crates/prin-daemon/tests/parity_subconscious.rs` | **New.** 8 bit-exact parity tests against `prinet==3.0.0`. |
| `crates/prin-daemon/tests/proptest_properties.rs` | **New.** 11 property suites: packing totality/determinism, clamp invariants, selection purity and ladder well-formedness, ONNX-reader robustness on arbitrary bytes. |
| `crates/prin-daemon/tests/integration_controller_model.rs` | **New.** 7 tests against the real `models/` artefacts. |
| `crates/prin-daemon/README.md` | Rewritten: delivered vs. WP-029 scope, features, and the risk-register-#4 rationale (the previous text claimed a daemon thread and ring buffer that do not exist). |
| `crates/prin-py/src/bindings/daemon.rs` | **New.** PyO3 surface: `SubconsciousState`, `ControlSignals`, `BackendSelection`, `select_execution_backend`, `backend_provider_names`, `backend_priority`, `backend_provider_options`, `npu_firmware_candidates`, `resolve_npu_firmware`, `model_sha256`, `inspect_onnx_model`, `verify_model_manifest`, `validate_controller_model`, and eight module constants. |
| `crates/prin-py/src/bindings/mod.rs`, `src/lib.rs` | Registered the new binding module. |
| `python/prin/daemon.py` | **New.** `SubconsciousController` (ONNX inference), `create_session` (fallback ladder), `select_backend`, `detect_best_backend`, `npu_available`, `directml_available`, `backend_info`, `verify_model_artefacts`, `default_model_path`, `OrtUnavailableError`, and the documented environment-variable contract. |
| `python/prin/_prin_core.pyi` | Stubs for every new class, function, and constant. |
| `python/prin/__init__.py` | Added `prin.daemon` to the subpackage list. |
| `models/manifest.json` | **New.** SHA-256 + size manifest for the two committed controller artefacts. |
| `models/README.md` | Records the manifest and its two consumers. |
| `Cargo.toml` | `sha2` and `tempfile` added to `[workspace.dependencies]` with justification. |
| `pyproject.toml` | `parity/test_parity_subconscious.py` added to the existing `E402`/`I001` per-file-ignore group (same entry pattern as `test_parity_differential.py`). |
| `tests/test_daemon_backend.py` | **New.** 83 tests: state/control types, selection over every provider subset, provider options, firmware resolution, model validation, `backend_info`, and the ORT-absent paths. |
| `tests/test_daemon_controller.py` | **New.** 23 tests: construction, inference, batch behaviour, the fallback ladder against a live runtime, and cross-provider agreement. |
| `parity/test_parity_subconscious.py` | **New.** 82 differential tests against the archived `prinet` 3.0.0. |
| `EVIDENCE/0109-wp028-s1-controller-provider-report.json` | **New.** Machine-readable provider, validation, parity, and agreement evidence for this host. |

## Parity-evidence disposition (Development Workflow Standards §3, S1 exit item)

**A directly comparable PRINet 3.0 reference exists for every new numerical
primitive in this WP, and parity evidence is included in this S1 commit.**

Verification of the claim, not an assertion:

```
$ ls "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/subconscious.py"        # 357 lines
$ ls "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/utils/npu_backend.py"        # 346 lines
$ ls "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/nn/subconscious_model.py"    # 437 lines
$ .venv/Scripts/python.exe -c "import prinet; print(prinet.__file__)"
C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\src\prinet\__init__.py
```

| Primitive | Reference | Parity evidence |
|---|---|---|
| `SubconsciousState::to_tensor` | `prinet.core.subconscious.SubconsciousState.to_tensor` | Bit-exact, 4 embedded Rust cases + 60 live differential cases |
| `ControlSignals::from_tensor` / `preferred_regime` / `is_finite` | `prinet.core.subconscious.ControlSignals` | Exact on every field, 4 embedded Rust cases + 134 live differential cases |
| Backend priority / provider chains / VitisAI option keys | `prinet.utils.npu_backend` | `parity/test_parity_subconscious.py::TestBackendSelectionParity`, compared against `_build_provider_list` and `detect_best_backend` |
| Full inference pipeline | `prinet` state encode → ORT session → `prinet` decode | Bit-exact on the CPU provider, 48 differential cases |
| `retrain_controller` | `prinet.nn.subconscious_model.retrain_controller` | **Not implemented this WP** — deferred to WP-030 with maintainer approval (see "Scope decision"); no parity evidence is owed by WP-028 |

Two reference behaviours proved subtle enough to be worth naming, because
neither is reproduced by a naïve port:

* **Python modulo.** `timestamp % 86400.0` takes the sign of the *divisor* in
  Python, so a negative timestamp yields a positive fraction. Rust's `%` takes
  the sign of the dividend; the port uses `f64::rem_euclid`. Pinned by
  `state_irrational_values_and_negative_timestamp_match_reference_bit_for_bit`
  (timestamp `-1.0`).
* **NumPy NEP 50 weak-scalar clipping.** `np.clip(flat[2], 0.1, 10.0)` on a
  `float32` operand keeps `float32`, so the reference's lower bound is
  `float(np.float32(0.1)) = 0.10000000149011612`, not `0.1`. Clipping in `f64`
  and widening afterwards diverges in the last bits. The port clips in `f32`.
  Pinned by the `clipped_low` case in
  `control_decode_matches_reference_values_and_clamps`.

## Why not the `ort` crate (Project Plan §7 risk register #4)

Risk register #4 provides for keeping the NPU path in Python `onnxruntime` if
`ort` lacks VitisAI EP parity, and `crates/prin-daemon/Cargo.toml` reserved the
`npu` feature "if EP coverage lags". The condition holds, on evidence gathered
this session:

| Check | Result |
|---|---|
| `cargo info ort` | Latest published version is `2.0.0-rc.13` — a pre-release; `2.0.0-rc.10` in the local registry declares `directml` and `vitis` features but its `download-binaries` default pulls pyke's prebuilt ONNX Runtime, which carries neither provider |
| Ryzen AI SDK 1.7.0 layout (`C:\Program Files\RyzenAI\1.7.0`) | VitisAI ships as `onnxruntime_vitisai-1.23.2-cp312-cp312-win_amd64.whl` — a CPython-tagged **Python wheel**; DirectML ships as a `.nupkg`. Neither is a C library the `ort` crate can link without a bespoke build |
| Project venv | Python 3.14; the `cp312` VitisAI wheel is not installable in it |

Adopting `ort` would therefore have added a pre-release dependency and a
build-time binary download (a reproducibility and clean-build regression)
*without* reaching either accelerator. The decision keeps all numerics and all
selection policy in Rust and confines Python to the session object.

## Acceptance-criterion evidence map

### AC1 — "Outputs match 3.0 references across available providers"

| Evidence | Result |
|---|---|
| `parity/test_parity_subconscious.py` (82 tests) | State vectors **bit-identical** to `prinet` 3.0.0 across 60 cases; control decode identical on every field across 134 cases; full pipeline bit-identical on the CPU provider across 48 cases |
| `crates/prin-daemon/tests/parity_subconscious.rs` (8 tests) | Rust-side bit-exact parity, no tolerance registered — one ULP of drift fails |
| `tests/test_daemon_controller.py::TestCrossProviderAgreement` | Outputs agree across every provider that can execute the graph on this host, at `rtol=1e-5, atol=1e-6` |
| `EVIDENCE/0109-wp028-s1-controller-provider-report.json` | `reference_parity.max_abs_output_diff_vs_reference = 0.0`; `cross_provider_agreement` = CPU, bit-identical |

**Honest statement of provider coverage on this host.** The available
providers are `DmlExecutionProvider` and `CPUExecutionProvider`. Only CPU can
*execute* this graph: DirectML fuses `Gemm`+`Relu` into a `DmlFusedGemm` node
that rejects the two-input form PyTorch exported —

```
InvalidGraph: ... ("fused op (#0 'node_Gemm_144') + (#1 'node_relu')",
DmlFusedGemm, "com.microsoft.dml", -1) ... has input size 2 not in range [min=3, max=3]
```

— which is the condition Project Plan amendment #13 already records from
WP-005 ("DirectML graph execution falls back to CPU on the current Windows
host"). The archived reference fails identically. VitisAI is not registered
(the host CPU is a Ryzen 7 8700F, which has no XDNA NPU, and the SDK's VitisAI
wheel is `cp312`-only). AC1 is therefore **met over the providers that can
execute**, and the cross-provider comparison harness is written so that it
widens automatically on a host where an accelerator can take the graph. The
remaining gap is hardware/runtime availability, not implementation, and it is
already governed by amendment #13's re-audit gate; see "Deferred items".

### AC2 — "Missing-provider paths fall back safely"

| Evidence | Result |
|---|---|
| `select_backend` property test (`proptest_properties.rs`) | Over arbitrary provider subsets and requests: the choice is always available, the ladder starts at the choice, descends strictly by priority, contains only available backends, and ends at CPU whenever CPU is registered; the function is pure |
| `tests/test_daemon_controller.py::TestDeterministicFallback` | Requesting `npu` on this host yields a working CPU session rather than an exception; every backend request yields a usable session |
| `EVIDENCE/...json` `session_attempts` | `npu` → `cpu`; `directml` → `cpu`; `cpu` → `cpu` — all three with active provider `CPUExecutionProvider`, no errors |
| `parity/...::test_prin_falls_back_where_the_reference_raises` | The reference **raises** `InvalidGraph` on DirectML; PRIN lands on CPU deterministically |
| `parity/...::test_prin_reports_a_degraded_selection_where_the_reference_is_silent` | The reference silently returns a CPU session labelled `npu`; PRIN records `reason = "requested_unavailable"`, `is_degraded = True` |

### AC3 — "Model SHA-256 is verified"

| Evidence | Result |
|---|---|
| `models/manifest.json` | Covers both artefacts with digest and size |
| `ModelManifest::verify` | Digest and size come from **one** streaming pass (`sha256_file_with_size`), so a digest can never be paired with a size read from a different revision |
| `verify_sha256` | Rejects a malformed expectation (`InvalidDigest`) before hashing — a corrupt manifest entry cannot pass vacuously; `ModelManifest::from_json` rejects an empty file list for the same reason |
| `integration_controller_model.rs` | The committed graph hashes to `3396bfdd…4102`, matching WP-005's `EVIDENCE/0017-wp005-s1-ort-probe.json` |
| `tests/test_daemon_backend.py::TestModelValidation` | Manifest digests re-derived independently with `hashlib`; tampered and missing artefacts detected; wrong and malformed digests rejected |
| `SubconsciousController.__init__` | Looks the digest up in the model directory's manifest and verifies **before** the graph is parsed or a session is opened |

### Non-goal compliance

No thread, no `std::thread`, no ring buffer, and no `ControlSignalBuffer`
anywhere in the change set:

```
$ grep -rn "thread::spawn\|std::thread\|AtomicUsize" crates/prin-daemon/src       python/prin/daemon.py crates/prin-py/src/bindings/daemon.rs
(no matches)

$ grep -rn "ControlSignalBuffer" crates/prin-daemon/src python/prin/daemon.py
crates/prin-daemon/src/lib.rs:32://!   control-signal ring buffer (PRINet 3.0's `ControlSignalBuffer` and
crates/prin-daemon/src/state.rs:5://! `ControlSignalBuffer` of the reference module is deliberately **not** part
```

Both `ControlSignalBuffer` hits are prose in doc comments recording the
deferral; no such type exists in the crate.

## Gate evidence (2026-08-21, this host)

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean (exit 0)
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings   # clean
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps               # 0 warnings
cargo test --workspace -- --test-threads=1                              # 1266 passed, 0 failed, 1 ignored
cargo test --workspace --features strict-checks                          # 44 result lines, 0 failed
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/       # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 72 files already formatted
.venv\Scripts\mypy python/prin --strict                                  # 28 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin        # 100.0% (262/262)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml          # 0 issues (3405 lines)
.venv\Scripts\python -m pip_audit .                                      # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt        # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu"          # 547 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/                            # 1147 passed
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # succeeded, 0 warnings
.venv\Scripts\python tools/wp001_baseline.py check                       # WP-001 baseline validation passed
```

**Test-count deltas** (baseline re-measured on this host by stashing the
change set: 1144 passed / 1 ignored, matching PSR-027 exactly):

| Suite | Before | After | Delta |
|---|---|---|---|
| `cargo test --workspace` | 1144 | **1266** | +122 — all `prin-daemon`: 81 unit, 15 doctest, 8 parity, 11 property, 7 integration |
| `pytest tests/ -m "not slow and not gpu"` | 441 | **547** | +106 (83 `test_daemon_backend.py`, 23 `test_daemon_controller.py`) |
| `pytest tests/ parity/` | 959 | **1147** | +188 (the 106 above plus 82 differential parity tests) |

### Coverage on new/changed code (`cargo llvm-cov`, merged over all test binaries)

| File | Regions | Functions | Lines |
|---|---|---|---|
| `crates/prin-daemon/src/backend.rs` | 99.50% | 100.00% | 100.00% |
| `crates/prin-daemon/src/model.rs` | 96.52% | 97.78% | 99.53% |
| `crates/prin-daemon/src/onnx.rs` | 95.49% | 95.45% | 99.38% |
| `crates/prin-daemon/src/state.rs` | 99.05% | 100.00% | 100.00% |
| **prin-daemon total** | **96.90%** | **97.93%** | **99.66%** |
| `python/prin/daemon.py` (pytest-cov) | — | — | **100%** (204/204 statements) |

All ≥95% on every metric.

### Snyk (Coding Standards §6, mandatory control)

`snyk code test` — **BLOCKED**, not passed:

```
ERROR   Authentication error (SNYK-0005) ... Status: 401 Unauthorized
```

This is the standing local-scan condition recorded since WP-001 (R23,
maintainer decision 2026-08-18: Snyk-CLI-only accepted as permanent; CI is the
authoritative gate). Reported as blocked per Coding Standards §6 item 5.
Snyk Open Source is N/A for Cargo; no new Python runtime dependency was added,
and `pip-audit` is clean on both requirement sets.

## Design notes worth an auditor's attention

### The ONNX reader is hand-written, and why

`prost` + `onnx.proto` needs `protoc` at build time; the `onnx` Python package
is not reachable from Rust. The reader decodes exactly eleven message types'
worth of named fields (tabulated in the module docs) and skips everything else
by wire type. It is total by construction: no recursion is driven by input
(unknown nested messages are *skipped*, never descended into), every length is
bounds-checked with `checked_add`, varints are capped at ten bytes, and every
failure is a `DaemonError::MalformedOnnx` carrying a byte offset. Field
numbers were taken from the installed `onnx` package's descriptors, not from
memory:

```
$ .venv/Scripts/python.exe -c "import onnx.onnx_pb as P; [print(f.number, f.name) for f in P.GraphProto.DESCRIPTOR.fields]"
```

Robustness is pinned by a proptest over arbitrary byte strings plus explicit
tests for truncation, overlong varints, reserved field number 0, group wire
types, non-UTF-8 strings, `u64::MAX` field lengths, and field numbers beyond
`u32`.

### The fallback ladder is stronger than the reference's

PRINet 3.0's `create_session` has no fallback at all: an unexecutable provider
propagates the ORT error, and an *unregistered* provider silently yields a CPU
session still labelled `npu`. PRIN computes the ladder in Rust from the
provider list alone — so it is pure, reproducible, strictly descending, and
CPU-terminating — and reports the backend it actually landed on plus a
`SelectionReason`. Both differences are asserted in the parity suite rather
than left implicit.

### Broad `except Exception` in `create_session`

Deliberate and bounded. ONNX Runtime's provider failures (`InvalidGraph`,
`Fail`, `EPFail`, …) all derive directly from `Exception` with no common base,
and a native EP can fail in ways no narrower clause catches; a broad clause is
what makes the fallback deterministic. It wraps only session construction,
records and logs every failure, re-raises with the full failure list when the
ladder is exhausted, and does not catch `BaseException`.

## Numerical finding recorded (not a defect)

ONNX Runtime selects a different float32 GEMM path for a **single-row** batch.
On this graph, `B = 1` differs from the same row inside a larger batch by one
float32 ULP (max absolute 1.19e-7, max relative 1.56e-7); every batch size
from 2 upwards is **bit-identical** to the full batch. Measured values are in
`EVIDENCE/...json` (`batch_size_sensitivity_max_abs_diff_vs_full_batch`).
Registered tolerance for single-vs-batched comparison: `rtol=1e-6, atol=1e-7`,
documented on `SubconsciousController.predict_batch` and pinned by
`test_only_the_single_row_batch_differs`. This does not affect the parity
claims, which compare like batch sizes.

## Out-of-scope discoveries (logged, not acted on)

1. **Version-string drift.** `Cargo.toml` and `pyproject.toml` both read
   `0.3.0-alpha.1`, but PSR-027 §6 states "The version in
   `Cargo.toml`/`pyproject.toml` is already at `0.5.0-alpha.1` (bumped at the
   Phase 3 exit, WP-021 S4)". `python/prin/__init__.py` also carries
   `0.3.0-alpha.1`. Either the Phase-3-exit bump never landed or PSR-027 §6 is
   inaccurate. This touches release governance (Versioning and Release
   Standards §1) and the pending `v0.5.0-alpha.1` tag, so it is **not** fixed
   from this session. Recommended owner: WP-028 S3, or the maintainer action
   that creates the Phase 4 tag.
2. **`prin.daemon` is absent from the Sphinx API pages.** Adding it is
   Documentation-session work; recorded for **WP-028 S4 (session 0112)**,
   together with the `CHANGELOG.md` entry, `crates/README.md` row expansion,
   `DOCS/sphinx/migration_guide.rst` symbol mappings for the deliberate
   API deviations (`clone_state` vs `clone`, the `create_session` return tuple,
   `SelectionReason`), and `DOCS/experiments/README.md` / session-register
   currency.
3. **DV-019 (flaky `gradients_flow_to_every_parameter`) did not recur** in any
   of this session's `cargo test --workspace` runs. R28's dedicated
   hotfix/correction session had not been opened when this session began;
   `bands.rs` is WP-022's frozen scope and was not touched here.

## Handoff to S2 (session 0110)

Suggested audit focus, in descending order of risk:

1. **The hand-written ONNX reader** (`onnx.rs`) — it parses untrusted input.
   Re-derive the field numbers from `onnx.proto`; re-run the proptest with a
   raised case count; confirm no panic path exists.
2. **The parity golden values** — regenerate them from `prinet` 3.0.0
   independently rather than trusting the embedded literals, and confirm the
   two subtle behaviours (Python modulo, NEP 50 clipping) are genuinely
   required rather than coincidental.
3. **AC1's provider-coverage statement** — confirm the DirectML failure is the
   amendment-#13 condition and not a defect in `create_session`, and judge
   whether the CPU-only execution coverage needs a deferred-validation entry
   of its own.
4. **The risk-register-#4 invocation** — confirm the `ort`/Ryzen AI evidence
   above and whether the decision warrants a plan amendment rather than
   resting on risk register #4 as written.
5. **Scope deferrals** — confirm the three deferred traceability symbols are
   correctly assigned to WP-029/WP-030 and that
   `DOCS/baselines/wp001_api_traceability.md` should be updated at S4 to point
   at those WPs.

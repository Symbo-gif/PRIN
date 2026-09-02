# Session 0144U / WP-036F S1 handoff

**Date:** 2026-09-02
**Session:** 0144U — WP-036F S1: Coding — DirectML controller-graph execution
**Status:** S1 delivered, committed locally (per amendment #28 cadence — the
WP-036F `0144U`–`0144X` range pushes once at S4). Handoff to the mandatory S2
audit `0144V`. S1 does not self-certify.
**Predecessor:** `0144T` (WP-036E S4) — closed and committed.
**Successor:** `0144V` (WP-036F S2 audit).

---

## 1. Session-start protocol (Development Workflow §6)

Read: PSR-036E (`DOCS/reports/036e-project-state.md`); the `0144U` brief and
`WP-036E-036F-036G-execution-plan-and-decomposition.md` §3 (WP-036F) / §7 (R3);
Project Plan §3.1 F5, §7 R4, amendments #13/#38; Development Workflow §3/§7;
Testing Standards §1/§3; `DEFERRED_VALIDATION_REGISTER.md` DV-006 (and DV-025
for the boundary); `DOCS/audits/028-wp028-audit.md` A1;
`DOCS/experiments/0109-wp028-s1-handoff.md`;
`EVIDENCE/0109-wp028-s1-controller-provider-report.json`; the controller export
path owner (`crates/prin-daemon/`, `python/prin/daemon.py`,
`models/subconscious_controller.onnx`); `tests/test_daemon_controller.py`.

## 2. S1-start repository verification

### Entry conditions — met

| Condition | Evidence |
|---|---|
| WP-036E S4 (`0144T`) closed and committed | `git log`: `b7d3ee7` (WP-036E S4 doc) … working tree clean at session start |
| No unresolved D1/D2 finding | PSR-036E §3: WP036E-F1 AMENDED (amdt #44), F2/F3/F4 FIXED; delta re-audit CLEAN |
| WP-036F scope/acceptance/non-goals approved | Plan amendment #38; PSR-036E §6 hand-off. Maintainer directed execution of this session (MichaelMaillet, 2026-09-02). |
| `DmlExecutionProvider` available; state recorded | `onnxruntime` 1.24.4; `ort.get_available_providers()` → `['DmlExecutionProvider', 'CPUExecutionProvider']`. `VitisAIExecutionProvider` **not** registered (Ryzen AI 1.7.0 ships VitisAI as `cp312`; project venv is CPython 3.14) — the NPU half of DV-006 stays OPEN, hardware/wheel-gated, per the brief non-goals. |

### The failure being fixed (reproduced this session)

`ort.InferenceSession("models/subconscious_controller.onnx",
providers=["DmlExecutionProvider"])` on the **pre-transform** graph:

```
InvalidGraph: ... ("fused op (#0 'node_Gemm_144') + (#1 'node_relu')",
DmlFusedGemm, "com.microsoft.dml", -1) ... has input size 2 not in range [min=3, max=3]
```

The committed graph has three `Gemm` nodes, each with **2 inputs**
(`state_vector`/`relu`/`relu_1`, and `net.{0,3,6}.weight`), `transB=1`,
`alpha=beta=1`. DirectML fuses `Gemm`+`Relu` into `DmlFusedGemm`, whose schema
requires 3 inputs. The PyTorch model (`nn.Linear`, `bias=True`, biases
zero-initialised and never trained) exported without the bias term. The
archived PRINet 3.0 reference graph is byte-identical (`sha256 3396bfdd…4102`)
and fails identically — a runtime/graph condition, not a PRIN defect (matches
amendment #13's WP-005 finding).

## 3. What landed

Graph-transform pass over the committed artefact (there is no first-party
PyTorch export path — `export_to_onnx` is DV-025 / WP-036C scope and explicitly
out of scope here), plus its verifier, tests, and evidence.

| File | Change |
|---|---|
| `tools/wp036f_reexport_controller.py` | **New.** `transform_graph(model)` returns a copy with every 2-input `Gemm` given a third input: a new inline zero-valued `float32` initializer `net.N.weight` → `net.N.bias` of length = out-features (`weight.dims[0]` since `transB=1`). Idempotent (a 3-input `Gemm` is skipped). `main` rewrites `models/subconscious_controller.onnx` + `models/manifest.json`; `--check` re-verifies arities, zero-bias values, transform fixed-point, and manifest currency, exit 1 on drift. |
| `tools/wp036f_provider_latency.py` | **New.** Writes `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`: environment, model sha/bytes/`Gemm` arities, the pristine-vs-re-exported CPU differential (48 cases, bit-identity), DirectML execution + agreement (`rtol=1e-5, atol=1e-6`), and DirectML-vs-CPU median inference latency. |
| `models/subconscious_controller.onnx` | **Regenerated.** 18,270 → 19,428 bytes; `sha256 3396bfdd…4102` → `d7d7935b70b3faab7af303be088bd82698f2140ff27a9d9f74a811d609d8341a`. Three inline zero biases added; every other node, initializer, opset (18), IR version (10), producer, graph name, and the `.onnx.data` external reference unchanged. |
| `models/subconscious_controller.onnx.data` | **Unchanged** (`sha256 35e7eb09…d2597`) — the bias tensors are inline; the weight companion is byte-identical to the PRINet 3.0 original. |
| `models/manifest.json` | New `.onnx` digest + size; `description` records the WP-036F re-export and the regeneration tool. |
| `models/README.md` | Rewritten `subconscious_controller.onnx` entry: origin, the WP-036F transform, the bit-identity guarantee, the regen tool, the pristine-archive pointer. |
| `crates/prin-daemon/tests/integration_controller_model.rs` | The three hard-coded `3396bfdd…4102` digest literals and the `18_270` byte size updated to the re-exported values, with a comment explaining the WP-036F re-export and that `EVIDENCE/0017-wp005-s1-ort-probe.json` is left as the historical pre-transform record. No other assertion changed (`Gemm` count still 3; contract, external-data, producer, graph-name assertions unaffected). |
| `tests/test_wp036f_reexport.py` | **New, 21 tests.** Committed-artefact structure (3-input `Gemm`, inline `float32` zero bias, unchanged I/O), the transform function (idempotency, stripped-graph rebuild, error paths), `main` round-trip and `--check` drift detection, **R3 CPU bit-identity** (vs an in-memory bias-stripped copy *and* vs the pristine archive graph over the 48-case set), DirectML execution + agreement (`skipif` `DmlExecutionProvider` absent), and the latency tool. |
| `tests/test_daemon_controller.py` | `TestCrossProviderAgreement` gains `test_directml_executes_the_reexported_graph` (`skipif` `DmlExecutionProvider` absent): asserts `"directml" in _executable_backends()`, that a `SubconsciousController(backend="directml")` activates `DmlExecutionProvider`, and that its batch output matches CPU within `rtol=1e-5, atol=1e-6`. The existing `_executable_backends()` probe already widens the other cross-provider tests automatically. |
| `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json` | **New** (regenerable). |
| `EVIDENCE/README.md`, `tools/README.md`, `tests/README.md`, `DOCS/experiments/README.md` | Currency for the new artefacts/tests. |
| `CHANGELOG.md`, `DOCS/sessions/SESSION_REGISTER.md`, `DOCS/sessions/phase-6/README.md`, the `0144U` brief | S1 status + change record. |

### Why "add a zero bias" is mathematically identical

`Gemm` computes `Y = alpha·A'·B' + beta·C`. `beta` is already `1.0`; the new
`C` is all zeros, so `Y_ij = (A'·B')_ij + 0.0`, which is exact in IEEE-754 for
every finite value. Verified empirically: the re-exported graph is
**bit-identical** to the pre-transform graph on `CPUExecutionProvider` over the
48-case differential set — `np.array_equal` on the `uint32` views, `max_abs_diff
== 0.0` — both against an in-memory bias-stripped copy and against the pristine
archived PRINet 3.0 graph. This is the R3 acceptance gate, satisfied *before*
any DirectML claim.

## 4. Acceptance-criterion → evidence map (for `0144V`)

| `0144U` acceptance criterion | Status / evidence |
|---|---|
| Re-exported graph **mathematically identical** — 48-case CPU differential, bit-identical, before any DirectML claim | **Met.** `tests/test_wp036f_reexport.py::TestMathematicalIdentity` (2 tests: vs bias-stripped copy, vs pristine archive); `EVIDENCE/0144U-…json` `pre_transform_differential.bit_identical = true`, `max_abs_diff = 0.0`, arities `[2,2,2] → [3,3,3]`. |
| `DmlExecutionProvider` executes the re-exported graph on the project host | **Met.** `tests/test_wp036f_reexport.py::TestDirectMLExecution`; `tests/test_daemon_controller.py::TestCrossProviderAgreement::test_directml_executes_the_reexported_graph`; `EVIDENCE/0144U-…json` `directml.executes = true`, `active_providers[0] = "DmlExecutionProvider"`. Registered providers recorded: `DmlExecutionProvider`, `CPUExecutionProvider`. |
| DirectML outputs agree with CPU within Testing Standards §3 tolerance across the case set; `TestCrossProviderAgreement` widens automatically | **Met.** `rtol=1e-5, atol=1e-6`; measured `max_abs_diff_vs_cpu = 7.15e-07` (max rel ~1.2e-6). `_executable_backends()` already probes at run time, so the two existing cross-provider tests now also exercise DirectML with no code change. |
| DirectML vs CPU provider latency measured and recorded | **Met.** `EVIDENCE/0144U-…json` `latency_ms_median_batch48`: CPU ≈ 0.034 ms, DirectML ≈ 0.285 ms (batch 48, median of 500 warm calls). DirectML is ~8× slower on this ~50 K-parameter MLP — dispatch/copy overhead dominates a graph this small; recorded as-is, not a regression (the daemon's backend-selection logic and its choice of provider are out of scope). |
| Committed graph artefact + checksum regenerated; 3.0-reference fixture updated consistently | **Met.** `models/subconscious_controller.onnx` + `models/manifest.json` regenerated; `tools/wp036f_reexport_controller.py --check` green; the Rust integration test's hard-coded digest/size updated; no 3.0-reference *comparison fixture* consumes the digest (the parity suite compares the reference runtime against the committed graph, both post-transform, so it is unaffected — re-run green). |
| ≥95% coverage on new/changed first-party code | Manual review (DV-033 — `coverage`/`pytest-cov` segfault on this host; CI codecov authoritative). The two new tools' public surface — `transform_graph` (idempotent + add + both error paths), `_bias_name`, `_gemm_out_features`, `_check` (clean + every drift branch), `_write_manifest`, `main` (rewrite + `--check` pass + `--check` fail), `build_report` (DirectML present + absent), `_pre_transform_check`, `_median_latency_ms`, `_infer` — is exercised by `tests/test_wp036f_reexport.py`. The Rust change is literal constants in a test file. |
| Numerical authority unaffected; no `prin.__all__` / `FROZEN_PUBLIC_API` change | **Held.** No `prin` public symbol added (`python/prin/_prin_core.pyi` untouched; the tools are not part of `prin`). `check_no_python_numerics.py` scope unchanged (the tools construct a zero constant and call ONNX Runtime — no numerical algorithm). The graph is a controller *inference* artefact, not PRIN numerics. |
| DV-006 DirectML half closable; amendment #13 WP-005 DirectML deferral dischargeable | Evidence in place for `0144V` to adjudicate; DV-006 register row + amendment #13 status to be updated at WP-036F S4 (`0144X`) per the plan. |

## 5. Gates (all green, local — 2026-09-02, project host)

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | clean |
| `cargo test --workspace` | pass (0 `FAILED`); `prin-daemon` integration + parity re-run green with the new digest |
| `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | clean |
| `ruff check python/ tests/ benchmarks/ tools/` | All checks passed |
| `ruff format --check python/ tests/ benchmarks/ tools/` | 241 files already formatted |
| `mypy python/prin --strict` | Success, 62 files (tools/ out of `mypy` scope per the local gate; tools are typed) |
| `interrogate -c pyproject.toml python/prin` | 97.6% (≥95%) |
| `bandit -r python/prin -c pyproject.toml` | 0 issues |
| `pytest tests/ -m "not slow and not gpu"` | **2765 passed, 202 skipped, 0 failed** (was 2743/202 at `0144T` — +21 `test_wp036f_reexport.py` + 1 `test_daemon_controller.py`) |
| `pytest parity/test_parity_subconscious.py` | pass (reference runtime vs committed graph, both post-transform) |
| `cargo audit` | exit 0; 3 allowed warnings (DV-008 `paste`, DV-017 `bincode`, `chacha20` yanked) — no `Cargo.toml` change |
| `pip-audit .` | No known vulnerabilities |
| `snyk code test` (`tools/wp036f_reexport_controller.py`, `tools/wp036f_provider_latency.py`, `tests/test_wp036f_reexport.py`; org `symbo-gif`, `--severity-threshold=low`) | **0 issues** each |
| Snyk Open Source | not triggered — no dependency or manifest change (`Cargo.toml`/`Cargo.lock`/`pyproject.toml`/requirements unchanged) |
| `tools/wp036f_reexport_controller.py --check` | `OK: 3 Gemm nodes, all three-input; manifest current` |

## 6. Invariants held

No controller *algorithm* change — only a zero-bias graph edit, proven
bit-identical on CPU. No daemon-runtime or backend-selection-logic change. No
NPU/VitisAI work. No DV-025 symbol touched. No weakened assertion or loosened
tolerance (the `rtol=1e-5, atol=1e-6` DirectML comparison is the standing
Testing Standards §3 GPU-vs-CPU default, already used by
`TestCrossProviderAgreement`). Deterministic — the tools add no RNG; the
differential batches are `np.random.default_rng(20260902)`-seeded. No
`prin.__all__` / `FROZEN_PUBLIC_API` / `.pyi` change.

## 7. Out-of-scope discoveries (logged, not acted on)

1. **`EVIDENCE/0017-wp005-s1-ort-probe.json` records the pre-transform digest**
   (`3396bfdd…`). It is an immutable historical WP-005 artefact (EA-002 E-F1;
   `test_phase0_gate.py` asserts it is never mutated by a test run) and is
   correctly left unchanged — the phase-0 gate reads only `can_run`, not the
   digest. If a future session wants a current ORT probe artefact it should
   write a new `NNNN-`-prefixed file, not edit this one.
2. **DirectML is slower than CPU for this graph** (~8×). Expected for a
   ~50 K-parameter MLP where host↔device copy and dispatch dominate. If the
   daemon ever needs the controller on an accelerator for throughput, a batched
   / persistent-io-binding path would be the lever — a daemon-runtime concern,
   out of this WP's scope.
3. **VitisAI / Ryzen AI NPU half of DV-006 stays OPEN.** `npu_available()` is
   `False` on this host: the SDK's VitisAI wheel is `cp312`, the venv is
   CPython 3.14. The NPU firmware overlay *is* present
   (`…/RyzenAI/1.7.0/…/phoenix/1x4.xclbin`), so the only blockers are the
   provider wheel and (per the brief) XDNA NPU silicon. Hardware/wheel-gated,
   same class as DV-001; unchanged by this WP.

## 8. Handoff to S2 (`0144V`)

Suggested audit focus, descending risk:

1. **R3 — graph semantics.** Independently re-run the 48-case CPU differential
   (pristine archive vs committed) and confirm bit-identity; inspect the three
   new initializers (`net.{0,3,6}.bias`, `float32`, all-zero, inline) and
   confirm no other node/initializer/attribute/opset/IO changed
   (`git`-diff the decoded protos, or `onnx.checker` + a structural diff).
2. **DirectML claim.** Re-create the session on `DmlExecutionProvider`, confirm
   `active_providers[0] == "DmlExecutionProvider"` (not a silent CPU fallback),
   and re-measure agreement.
3. **Digest propagation.** Confirm every consumer of the old digest is updated
   (`grep -rn 3396bfdd` → only the immutable `EVIDENCE/0017` and `DOCS`
   history) and that `manifest.json` ↔ file ↔ Rust test ↔ Python
   `verify_model_artefacts()` all agree.
4. **Coverage.** Per DV-033, confirm the manual-review coverage argument for
   the two tools against CI codecov once `python.yml` runs at S4.
5. **Scope.** Confirm no daemon-runtime / backend-selection / algorithm change
   crept in, and that the NPU half correctly stays OPEN.

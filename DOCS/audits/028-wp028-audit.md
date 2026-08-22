# PRIN Audit Report — Cycle 028 / WP-028

**Date:** 2026-08-22
**Auditor:** Claude Sonnet 5 (AI pair)
**Scope:** WP-028 "ONNX controller and backend selection" — `crates/prin-daemon/src/{state,backend,onnx,model,error,lib}.rs` (new crate contents); `crates/prin-daemon/tests/{parity_subconscious,proptest_properties,integration_controller_model}.rs` (new); `crates/prin-py/src/bindings/daemon.rs`, `crates/prin-py/src/bindings/mod.rs`, `crates/prin-py/src/lib.rs` (new bindings + registration); `python/prin/daemon.py` (new); `python/prin/_prin_core.pyi`, `python/prin/__init__.py` (stubs/exports); `models/manifest.json`, `models/README.md` (new evidence artefact); `tests/test_daemon_backend.py`, `tests/test_daemon_controller.py` (new); `parity/test_parity_subconscious.py` (new); `Cargo.toml`, `crates/prin-daemon/Cargo.toml`, `pyproject.toml` (dependency/config additions); `DOCS/experiments/0109-wp028-s1-handoff.md`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (evidence/governance updates); `EVIDENCE/0109-wp028-s1-controller-provider-report.json` (new evidence artefact)
**Sessions:** 0109 (S1 — Coding) implementation; 0110 (S2 — Audit) this audit
**Active brief:** `DOCS/sessions/phase-5/0110-wp028-s2-onnx-controller-and-backend-selection.md`
**Git state:** `main` @ `3588aa622ade272149c423808bb0e4cfba9a4afa` (single S1 commit; branch is 1 commit ahead of `origin/main` — nothing pushed this cycle, per the Push and CI cadence); working tree clean at audit time
**Verdict:** **PASS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All 33 changed/new files match the S1 handoff's declared scope table; three traceability symbols (`ControlSignalBuffer`, `export_to_onnx`/`quantize_onnx`, `retrain_controller`) are explicitly deferred to WP-029/WP-030 with maintainer approval, not silently dropped |
| Plan/architecture conformance (A2) | ✅ | Zero `unsafe`; `#![forbid(unsafe_code)]`; zero numerics in Python (`daemon.py` is pure orchestration); zero environment reads in Rust (confirmed by grep); risk register #4 and amendment #13 both independently verified to say exactly what the S1 handoff claims |
| Tests in tandem + coverage (A3) | ✅ | `backend.rs` 99.50%/100%/100%, `model.rs` 96.52%/97.78%/99.53%, `onnx.rs` 95.16–95.49%/95.45%/99.38%, `state.rs` 99.05%/100%/100% (all ≥95%; onnx.rs region-count has a small proptest-driven run-to-run variance, discussed in §3.3, that does not affect the gate); 122 `prin-daemon` Rust tests (81 unit + 15 doctest + 8 parity + 11 property + 7 integration), 106 new Python tests, all independently reproduced green |
| Numerical parity + invariants (A4) | ✅ | Every embedded "bit-exact" golden value in `parity_subconscious.rs` independently regenerated from the live `prinet==3.0.0` reference and matched bit-for-bit; ONNX field numbers independently verified against the installed `onnx` package's descriptors; model SHA-256 independently recomputed and matched the manifest and WP-005's evidence |
| Quality gates (A5) | ✅ | fmt/clippy (default + `strict-checks`)/ruff/ruff-format/mypy --strict all independently reproduced clean |
| Security (A6) | ✅ | Zero `unsafe`; bandit 0 issues (3405 lines); `cargo audit` exit 0 with the same 2 pre-existing allowed advisories (`paste`/DV-008, `bincode`/DV-017); `pip-audit` clean; no `eval`/`exec`/`pickle`/`shell=True`; hand-written ONNX parser is total (proptest fuzzes arbitrary bytes, never panics) |
| Docstring/doc coverage (A7) | ✅ | interrogate 100% (262/262); rustdoc clean under `RUSTDOCFLAGS=-D warnings`; `.pyi` stubs present for every new PyO3 symbol; Sphinx build clean (0 warnings) — `prin.daemon`'s absence from the Sphinx API pages is an explicitly logged out-of-scope discovery assigned to S4, not a doc-coverage gap |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/`unimplemented!`/`panic!` in library code; every `.unwrap()`/`.expect()` is confined to `#[cfg(test)]` modules; session register correctly shows 0109 COMPLETE, 0110–0112 PLANNED |
| CI status (A9) | ✅ (local-gate stand-in) | Nothing pushed yet this cycle (amendment #28 cadence); every gate independently reproduced locally, all green; DV-024 (self-hosted runner offline) is an unrelated, already-recorded external condition and does not bear on this S2 |
| Artefact trail (A10) | ✅ | PSR-027, S1 handoff note, `EVIDENCE/0109-...json`, and `DEFERRED_VALIDATION_REGISTER.md`'s DV-005/DV-006 updates are all present, cross-referenced, and consistent with each other |

**Verdict rationale:** zero D1–D3 findings across all ten checklist dimensions; no D4 is raised either, since the one imprecision found (a 0.33-percentage-point proptest-driven coverage-number drift, §3.3) does not misstate compliance against any gate. Per Development Workflow and Audit Standards §5, zero findings yields `PASS`.

---

## 2. Methodology

All commands executed on Windows (local host), Python 3.14.0, Rust toolchain per `rust-toolchain.toml`, `.venv` per the project's committed environment. Every claim below is backed by command output captured during this audit session (2026-08-22).

```powershell
# Format and lint
cargo fmt --all -- --check                                                    # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0, clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0, clean

# Tests
cargo test --workspace -- --test-threads=1                                    # exit 0; prin-daemon: 81 unit + 7 integration + 8 parity + 11 property + 15 doctest = 122
cargo test --workspace --features strict-checks                               # exit 0, 0 failures

# Coverage (new/changed Rust, all test binaries merged: lib + integration + parity + proptest)
cargo llvm-cov -p prin-daemon --show-missing-lines
# backend.rs 99.50%/100.00%/100.00%; model.rs 96.52%/97.78%/99.53%;
# onnx.rs 95.16%/95.45%/99.38% (region count varies ±0.3pp run to run
# from proptest's unseeded case generation); state.rs 99.05%/100.00%/100.00%

# Security
cargo audit                                                                    # exit 0; 2 allowed warnings (paste RUSTSEC-2024-0436/DV-008, bincode RUSTSEC-2025-0141/DV-017)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # All checks passed!
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 72 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues found in 28 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (262/262)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml               # 0 issues (3405 lines)
.venv\Scripts\python -m pip_audit .                                           # No known vulnerabilities found

# Python tests
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu"               # 547 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/                                 # 1147 passed
.venv\Scripts\python -m pytest tests/test_daemon_backend.py tests/test_daemon_controller.py --cov=prin.daemon --cov-report=term-missing
# python/prin/daemon.py: 204/204 statements, 100%

# Sphinx (fresh output directory, per Documentation Standards §7 item 3)
rm -rf DOCS/sphinx/_build
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings

# WP-001 baseline
.venv\Scripts\python tools/wp001_baseline.py check                            # WP-001 baseline validation passed

# Independent re-derivation of onnx.proto field numbers (against the installed `onnx` package)
.venv\Scripts\python -c "import onnx.onnx_pb as P; ..."                       # all 11 field numbers match onnx.rs's module-doc table exactly

# Independent re-derivation of parity golden values (against the archived prinet==3.0.0)
.venv\Scripts\python -c "from prinet.core.subconscious import SubconsciousState, ControlSignals; ..."
# every embedded f32::from_bits literal in parity_subconscious.rs matched bit-for-bit; every ControlSignals.from_tensor clamp/decode value matched exactly

# Independent SHA-256 re-verification of committed model artefacts
certutil -hashfile models/subconscious_controller.onnx SHA256       # 3396bfdd...4102 — matches manifest.json and EVIDENCE/0017-wp005-s1-ort-probe.json
certutil -hashfile models/subconscious_controller.onnx.data SHA256  # 35e7eb09...d2597 — matches manifest.json

# Governance cross-checks
grep -n "risk register" DOCS/PRIN_Project_Plan.md                              # risk #4 text confirmed verbatim
grep -n "amendment #13\|DirectML" DOCS/PRIN_Project_Plan.md                    # amendment #13 text confirmed verbatim
grep -rn "unsafe\|eval(\|exec(\|pickle\.\|shell=True" crates/prin-daemon/src python/prin/daemon.py crates/prin-py/src/bindings/daemon.rs
# only the crate-level #![forbid(unsafe_code)] declaration; no other match
grep -rn "\.unwrap()\|\.expect(\|panic!" crates/prin-daemon/src/*.rs
# every hit is inside a #[cfg(test)] mod tests block
```

---

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

The S1 commit (`3588aa6`) touches exactly the 33 files the handoff note's scope table declares (verified via `git show --stat 3588aa6` against the table in `DOCS/experiments/0109-wp028-s1-handoff.md`). No undeclared file is present; no declared file is missing.

The WP declaration (PSR-027 §7 / session brief 0109) named four deliverables — controller state/control types, ONNX model validation, provider detection (VitisAI→DirectML→CPU), deterministic fallback — and all four are present:

| Deliverable | Files | Verified |
|---|---|---|
| Controller state/control types | `crates/prin-daemon/src/state.rs` | ✅ `SubconsciousState`, `ControlSignals`, `Regime`, `STATE_DIM=32`, `CONTROL_DIM=8` |
| ONNX model validation | `crates/prin-daemon/src/{onnx,model}.rs` | ✅ hand-written total protobuf reader + SHA-256/contract validation |
| Provider detection | `crates/prin-daemon/src/backend.rs` | ✅ `Backend`, `select_backend`, VitisAI→DirectML→CPU priority |
| Deterministic fallback | `backend.rs::select_backend`, `python/prin/daemon.py::create_session` | ✅ pure, CPU-terminated ladder; property-tested |

Three `wp001_api_traceability.md`-mapped symbols are explicitly out of this WP's scope with a stated reason and target WP each: `ControlSignalBuffer` (non-goal "background runtime/threading" → WP-029), `SubconsciousController.export_to_onnx`/`.quantize_onnx` and `retrain_controller` (training-stack work → WP-030). `grep -rn "thread::spawn\|std::thread\|AtomicUsize\|ControlSignalBuffer"` against every new file returns only two doc-comment prose mentions of `ControlSignalBuffer` recording the deferral — no such type or threading primitive exists in the delivered code. This is a documented scope decision, not silent scope creep, and it carries the "Maintainer decisions taken this session" record required by Development Workflow and Audit Standards §3 (parity-evidence disposition / scope discipline).

The `python/prin/train.py`-class addition-beyond-scope pattern from earlier cycles does not recur here: every new file maps directly onto a declared deliverable.

### 3.2 A2 — Plan/architecture conformance

**Crate layering and numerics.** `python/prin/daemon.py` was read in full: every arithmetic/decision function it defines (`select_backend`, `detect_best_backend`, `create_session`, `backend_info`, `SubconsciousController.predict*`) delegates to a `prin._prin_core` (Rust) call for the actual computation; the module's own code is limited to environment/filesystem lookups, ONNX Runtime session objects, and numpy dtype/shape plumbing around Rust calls. This matches the crate's own module doc claim ("the Python layer contains no numerics") and Coding Standards §2 rule 2.

**Unsafe.** `crates/prin-daemon/src/lib.rs:63` declares `#![forbid(unsafe_code)]`; `grep -rn "unsafe"` across every new/changed file in this WP returns only that one declaration. `crates/prin-py/src/bindings/daemon.rs` uses only safe PyO3 APIs (`PyArray1::from_slice`, `PyDict`/`PyList` builders) — no raw pointers, no `unsafe` block.

**Explicit state, no hidden globals.** `crates/prin-daemon/src/backend.rs`'s own module doc states it "reads no environment variables, so every decision is reproducible from its inputs alone"; `grep -rn "std::env\|env::var" crates/prin-daemon/src/*.rs` returns nothing, confirming the claim. All environment-variable handling (`PRIN_SUBCONSCIOUS_BACKEND`, `RYZEN_AI_INSTALLATION_PATH`, `XLNX_VART_FIRMWARE`, `PRIN_NPU_TARGET`, `PRIN_CONTROLLER_MODEL`) is confined to `python/prin/daemon.py`'s thin wrapper functions, which then pass concrete values into the pure Rust functions — the architecture Coding Standards §2 rule 3 calls for.

**Risk register #4 / amendment #13.** Both governance citations in the S1 handoff and commit message were independently verified against `DOCS/PRIN_Project_Plan.md` rather than trusted:
- §7 risk #4 reads verbatim: *"`ort` lacks VitisAI EP parity | Keep NPU path in Python `onnxruntime` (small, perf-uncritical)"* — exactly the condition and mitigation the handoff cites for keeping session creation in Python.
- Amendment #13 (§8.3, row 13) reads verbatim: *"the CPU fallback for the subconscious controller is proven on all CI platforms; DirectML graph execution falls back to CPU on the current Windows host; the VitisAI NPU runtime and DirectML parity are unavailable in Phase 0 and deferred to WP-028 (Phase 5 daemon) with a re-audit gate"* — this is exactly the condition WP-028 S1 re-audited with fresh evidence and re-gated (as DV-006) to WP-032 S1.

**`ort` crate decision evidence.** The S1 handoff's claim that `ort` 2.0.0-rc's prebuilt binaries carry neither DirectML nor VitisAI, and that the Ryzen AI SDK's VitisAI wheel is CPython-tagged (`cp312`) against a Python-3.14 project venv, is stated as a decision record with commands run in-session; this audit did not re-run those specific SDK-layout probes (they depend on this host's installed Ryzen AI SDK and are not safety-relevant to re-verify), but the *consequence* of the decision — zero `ort`/`unsafe`/native-binding code anywhere in the change set, and `npu` staying a reserved no-op feature — is directly confirmed by inspection of `crates/prin-daemon/Cargo.toml` (no `ort` dependency added) and `crates/prin-daemon/src/lib.rs`'s feature table.

### 3.3 A3 — Tests in tandem + coverage

**Coverage (new/changed Rust, independently re-measured, all test binaries merged via `cargo llvm-cov -p prin-daemon --show-missing-lines`, matching the handoff's own "merged over all test binaries" methodology):**

| File | Regions | Functions | Lines | Handoff claim | Match |
|---|---|---|---|---|---|
| `backend.rs` | 99.50% | 100.00% | 100.00% | 99.50%/100.00%/100.00% | exact |
| `model.rs` | 96.52% | 97.78% | 99.53% | 96.52%/97.78%/99.53% | exact |
| `onnx.rs` | 95.16% | 95.45% | 99.38% | 95.49%/95.45%/99.38% | functions/lines exact; regions off by 0.33pp |
| `state.rs` | 99.05% | 100.00% | 100.00% | 99.05%/100.00%/100.00% | exact |

The one non-exact figure — `onnx.rs` region coverage — is attributable to `proptest_properties.rs`'s two ONNX-fuzzing property tests (`onnx_inspection_never_panics_on_arbitrary_bytes`, `onnx_inspection_never_panics_on_truncated_valid_prefixes`), which are not given a fixed seed and therefore explore a different subset of the parser's branches on each run. This is expected, non-adversarial variance in property-based testing (the same class of drift the project has previously observed and accepted for other proptest-covered modules), not a fabricated or stale number: 95.16% still clears the ≥95% gate on every metric, and the *direction* of drift (this run measured slightly lower than the handoff's) means the audit's own reproduction is the more conservative of the two. No finding is raised.

**Test counts (independently reproduced):**
- `prin-daemon`: 81 unit + 7 integration + 8 parity + 11 property + 15 doctest = **122**, exactly matching the handoff's claimed delta breakdown.
- Rust workspace: `cargo test --workspace -- --test-threads=1` exit 0, zero `FAILED` markers anywhere in the log.
- Rust workspace under `strict-checks`: `cargo test --workspace --features strict-checks` exit 0, zero failures.
- Python fast suite: **547 passed, 8 deselected** — exact match.
- Python full suite (+parity): **1147 passed** — exact match.
- `python/prin/daemon.py` isolated coverage: **204/204 statements, 100%** — exact match.

**No weakened tests or tolerance drift detected.** Every new assertion inspected in `state.rs`, `backend.rs`, `onnx.rs`, `model.rs` tests uses either exact equality (bit-pattern comparison via `.to_bits()` for float parity, or plain `assert_eq!` for policy/typed-error behavior) or a narrowly registered tolerance with a stated reason (`rtol=1e-6, atol=1e-7` for the documented single-batch-row ULP effect; `rtol=1e-5, atol=1e-6` for cross-execution-provider Gemm reassociation). No existing test elsewhere in the repository was touched by this commit (`git show --stat` shows only new files plus the four small governance/registration edits listed in the header).

**Property-based robustness of the hand-written ONNX parser.** `proptest_properties.rs` fuzzes `inspect_onnx_bytes` with arbitrary byte strings (0–512 bytes) and truncated-valid-prefix inputs, asserting only "decode or typed error, never panic." Combined with the fixed-vector regression tests in `onnx.rs` itself (truncated varint, overlong varint, absurd `u64::MAX` length, field-number overflow, non-UTF-8 string, group wire type, zero field number), this is thorough coverage of the untrusted-input surface the S1 handoff itself flagged as the highest-risk area.

### 3.4 A4 — Numerical parity + invariants

**Independent regeneration of the embedded "bit-exact" golden values.** The S1 handoff's own suggested audit focus #2 asked the auditor to "regenerate them from `prinet` 3.0.0 independently rather than trusting the embedded literals." This audit did so: importing `prinet.core.subconscious` directly from the archived reference tree and re-running the "realistic," "irrational + negative timestamp," and all four `ControlSignals.from_tensor` clamp cases embedded in `crates/prin-daemon/tests/parity_subconscious.rs`. Every one of the 19 realistic-case float32 bit patterns, all 19 irrational-case bit patterns, and every field of the three non-trivial control-decode cases (`clipped_high`, `clipped_low`, `irrational`) matched the embedded Rust literals exactly, including the two subtle behaviours the handoff calls out by name:
- Python's sign-of-divisor `%` on `timestamp=-1.0` → `0x3f7fff3e` (86399/86400), reproduced by `f64::rem_euclid`.
- NumPy NEP 50 weak-scalar clipping of `np.clip(flat[2], 0.1, 10.0)` → `float(np.float32(0.1)) = 0.10000000149011612`, not `0.1`.

These are genuine, independently reproducible bit-exact matches, not fabricated literals — the audit's suggested-focus item is closed with direct evidence rather than trust.

**ONNX field-number table.** The eleven-field table in `onnx.rs`'s module doc was independently re-derived by importing the installed `onnx` package and enumerating `DESCRIPTOR.fields` for every message type the reader decodes (`ModelProto`, `OperatorSetIdProto`, `GraphProto`, `NodeProto`, `TensorProto`, `StringStringEntryProto`, `ValueInfoProto`, `TypeProto`, `TypeProto.Tensor`, `TensorShapeProto`, `TensorShapeProto.Dimension`), plus the two enum constants (`TensorProto.DataType.FLOAT = 1`, `TensorProto.DataLocation.EXTERNAL = 1`). Every field number and both constants match the module doc's table exactly.

**Model integrity (AC3).** `models/manifest.json`'s two recorded digests were independently recomputed from the committed files on disk (`certutil -hashfile ... SHA256`) and matched both the manifest and the digest recorded in WP-005's `EVIDENCE/0017-wp005-s1-ort-probe.json` (`3396bfdd...4102`), confirming the graph is unchanged since WP-005 and that the manifest is not self-referentially fabricated.

**AC1/AC2 evidence reproduced.** `tests/test_daemon_controller.py::TestCrossProviderAgreement` and `EVIDENCE/0109-wp028-s1-controller-provider-report.json` were both re-executed/re-inspected: on this host only `CPUExecutionProvider` can execute the graph (DirectML registers but fails with the `DmlFusedGemm` two-input-arity error the handoff quotes, and the archived reference fails identically), matching amendment #13's condition exactly. `proptest_properties.rs::backend_selection_is_pure_and_the_ladder_is_well_formed` independently confirms the fallback ladder is pure, strictly descending, contains only registered backends, and terminates at CPU whenever CPU is registered — over arbitrary provider subsets, not just the fixed cases in `backend.rs`'s unit tests.

### 3.5 A5 — Quality gates

All independently reproduced clean (commands and output in §2):
- `cargo fmt --all -- --check`: exit 0.
- `cargo clippy --workspace --all-targets -- -D warnings`: exit 0.
- `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings`: exit 0.
- `ruff check`: All checks passed!
- `ruff format --check`: 72 files already formatted.
- `mypy --strict`: 0 issues, 28 files.

### 3.6 A6 — Security

- **`unsafe` scan:** zero hits outside the single `#![forbid(unsafe_code)]` declaration in `lib.rs`.
- **Untrusted-input handling:** the hand-written ONNX reader (`onnx.rs`) is the only component in this WP that parses attacker-influenced bytes at a real trust boundary (a model file on disk). It is bounds-checked throughout (`checked_add` on every length computation, `get`/`get_mut` instead of indexing, a capped 10-byte varint loop, unknown fields skipped by wire type rather than recursed into), returns `DaemonError::MalformedOnnx` on every failure path, and is fuzzed by `proptest` over arbitrary bytes with a "never panics" invariant, independently re-run clean by this audit.
- **`eval`/`exec`/`pickle`/`shell=True`:** zero hits in `python/prin/daemon.py` or any new Rust source.
- **`cargo audit`:** exit 0; the same 2 pre-existing allowed advisories as every prior cycle (`paste` RUSTSEC-2024-0436/DV-008, `bincode` RUSTSEC-2025-0141/DV-017); no new advisory from the two new direct dependencies (`sha2`, `tempfile`, the latter dev-only).
- **`bandit`:** 0 issues across 3405 lines of Python (up from 2813 at PSR-027, i.e. `daemon.py` and its tests scanned clean).
- **`pip-audit`:** 0 vulnerabilities; no new Python runtime dependency was added (the S1 handoff's claim is confirmed — `daemon.py` imports only `numpy`, `pathlib`, stdlib, and the compiled `_prin_core` extension; `onnxruntime` is an optional extra already governed, imported lazily via `importlib.import_module` with a typed `OrtUnavailableError` fallback).
- **Dependency justification:** both new workspace dependencies (`sha2`, `tempfile`) carry an inline justification comment in `Cargo.toml`, satisfying Coding Standards §2.1's "justification in the PR description" requirement (recorded in-repo rather than only in a PR description, which is stronger).
- **Snyk Code:** the S1 handoff records `snyk code test` as **BLOCKED** (401 Unauthorized), the standing local-scan condition since WP-001 (R23, maintainer decision 2026-08-18: Snyk-CLI-only accepted as permanent; CI is the authoritative gate). This audit did not have Snyk credentials available either and cannot independently improve on that status; it is correctly reported as blocked, not claimed as passed, per Coding Standards §6 item 5 and §6.4.

### 3.7 A7 — Docstring/doc coverage

- **interrogate:** 100.0% (262/262) — up from 231/231 at PSR-027, reflecting `daemon.py`'s 31 new public symbols plus the crate's re-exports.
- **Rust `#![warn(missing_docs)]`:** every public item in `state.rs`, `backend.rs`, `onnx.rs`, `model.rs`, `error.rs` carries a doc comment (spot-checked extensively during source review; `cargo clippy -D warnings` and the crate's own `#![warn(missing_docs)]` would fail otherwise, and both are clean).
- **`.pyi` stubs:** present for every new PyO3 symbol registered in `crates/prin-py/src/bindings/daemon.rs::register` (confirmed by reading `python/prin/_prin_core.pyi`'s diff, +135 lines matching the binding module's exported classes/functions/constants).
- **Sphinx:** fresh-directory build (`rm -rf DOCS/sphinx/_build` before building, per Documentation Standards §7 item 3) succeeded with 0 warnings. `prin.daemon` is not yet on the Sphinx API pages; this is explicitly logged in the S1 handoff as an out-of-scope discovery assigned to session 0112 (WP-028 S4), consistent with Documentation Standards §7 item 9's deferral-requires-recorded-rationale rule (added at the Phase 4 recommendation-implementation session, R27) — not a doc-coverage gap in this S1/S2 cycle.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME/stub scan:** zero markers in any new file.
- **`unwrap`/`expect`/`panic!` scan:** every hit across `crates/prin-daemon/src/*.rs` is inside a `#[cfg(test)] mod tests` block; zero in library code paths, matching `error.rs`'s own module-doc claim ("the crate contains no `panic!`/`unwrap`/`expect` in library code paths").
- **`__all__` consistency:** `python/prin/daemon.py`'s `__all__` (39 entries) was checked against its actual public symbol set by inspection; every function/class defined at module level that is not underscore-prefixed appears in `__all__`, and every `__all__` entry resolves to a real symbol (either defined locally or re-exported from `prin._prin_core`).
- **Session register:** `DOCS/sessions/SESSION_REGISTER.md` rows 0109–0112 read COMPLETE/PLANNED/PLANNED/PLANNED — the correct state for an audit in progress.
- **No orphan files:** every new Rust file is wired into `lib.rs`'s module tree; `daemon.py` is registered in `python/prin/__init__.py`'s subpackage list; `bindings/daemon.rs` is registered in `bindings/mod.rs` and `src/lib.rs`.

### 3.9 A9 — CI status (local-gate stand-in)

Per amendment #28's push cadence, nothing has been pushed this cycle (`git status` shows the branch 1 commit ahead of `origin/main`, working tree clean) — S4 is the sole push point, so a live CI run cannot be checked at S2. All gates in §2 were independently reproduced locally with the same commands `rust.yml`/`python.yml` would run, all green. DV-024 (self-hosted `PRIN-GPU-Runner` offline) was reviewed and confirmed unrelated: it was discovered while verifying an *unrelated, prior* session's push (commit `237e1a7`, the Phase 4 recommendation-implementation session), predates this WP's S1 entirely, and does not bear on WP-028's local-gate evidence, which needs no self-hosted runner. No benchmark regression gate is defined for `prin-daemon`; none was tripped.

### 3.10 A10 — Artefact trail

- **PSR-027:** present at `DOCS/reports/027-project-state.md`, declares WP-028 in §7 with the exact scope/acceptance-criteria text this WP's session briefs quote.
- **S1 handoff:** present at `DOCS/experiments/0109-wp028-s1-handoff.md`, 370 lines, maps every acceptance criterion to specific evidence and states the parity-evidence disposition required by Development Workflow and Audit Standards §3 S1 exit criteria.
- **`EVIDENCE/0109-wp028-s1-controller-provider-report.json`:** present, machine-readable, and its contents (provider list, cross-provider agreement, batch-sensitivity figures, manifest digests) were spot-checked against the claims in the handoff and this audit's own independent measurements — consistent throughout.
- **Deviation ledger / register updates:** `DEFERRED_VALIDATION_REGISTER.md`'s DV-005 and DV-006 rows both carry a "re-audited ... at WP-028 S1 (session 0109, 2026-08-21)" entry with the maintainer's R31 disposition (DV-005: defer to WP-036) recorded; both are consistent with PSR-027 §5's prior "OPEN" status for these items and with this session's own re-reading of the Project Plan's risk register #4 and amendment #13 text.
- **Model manifest as evidence artefact:** `models/manifest.json` and `models/README.md` were added/updated in this same commit and independently verified (§3.4) rather than merely present.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| *(none)* | — | — | — | — | — |

No D1–D4 finding is raised. The single imprecision identified during independent reproduction — `onnx.rs`'s region-coverage figure drifting 0.33 percentage points from the handoff's claimed value, run to run, because `proptest_properties.rs`'s ONNX-fuzzing cases are unseeded — does not violate any coverage gate (both figures clear ≥95%) and is documented as expected proptest variance in §3.3 rather than escalated to a finding.

---

## 5. Deviation-ledger delta

**New findings added to the ledger:** none.

**Carried findings re-inspected:**

- **DV-005** (CUDA Burn backend): re-read the register entry; the R31 disposition ("defer out of Phase 5, re-gate at Phase 6 WP-036") this WP's S1 recorded is present, dated, and maintainer-approved (MichaelMaillet, 2026-08-21) exactly as claimed. This WP touches no Burn/CUDA code, so the item is unaffected by this WP's own delivery beyond the R31 checkpoint closure it performed. **Status: unchanged (OPEN, re-gated to WP-036).**
- **DV-006** (DirectML/VitisAI ONNX validation): re-read the register entry and independently re-confirmed its evidence — `EVIDENCE/0109-wp028-s1-controller-provider-report.json`'s `cross_provider_agreement`/`executable_backends` fields match this audit's own re-execution of `TestCrossProviderAgreement`, and amendment #13's plan text matches the register's characterization verbatim (§3.2). **Status: unchanged (OPEN, re-gated to WP-032 S1, whose brief already provides for justified hardware skips).**
- **DV-008** (`paste` advisory): re-checked (`cargo audit` exit 0). Unchanged.
- **DV-017** (`bincode` advisory): re-checked (`cargo audit` exit 0). Unchanged.
- **DV-024** (self-hosted runner offline): reviewed; confirmed pre-existing and unrelated to this WP (§3.9). Not re-checked for current runner status, since S2 does not depend on a live CI run this cycle.

---

## 6. Verdict and required actions

**Verdict: PASS**

Zero findings across all ten checklist dimensions, established with an unusually high degree of independent verification for a WP of this size and risk profile (a hand-written protobuf parser over untrusted input, and a security-relevant integrity-verification path):

- Every acceptance criterion is met or is a re-confirmation of an already-governed, hardware-blocked gap (DV-006), with fresh, independently-reproduced evidence rather than a stale claim.
- The bit-exact parity claims were not merely trusted — they were independently regenerated from the live PRINet 3.0 reference and matched exactly, closing the S1 handoff's own suggested audit focus #2.
- The ONNX field-number table was independently re-derived from the installed `onnx` package's descriptors and matched exactly, closing suggested audit focus #1's "re-derive the field numbers from `onnx.proto`" instruction.
- The model SHA-256 digests were independently recomputed from disk and matched both the manifest and WP-005's prior evidence, closing suggested audit focus #3's underlying integrity claim.
- Coverage clears ≥95% on every file by every metric; test counts, quality gates, and security scans all reproduce exactly (with one immaterial, explained proptest-variance exception on a single coverage figure).
- Scope discipline is exemplary: three traceability symbols are explicitly, individually deferred with named target WPs and maintainer approval rather than silently dropped or silently expanded into.

**S3 action list (mandatory zero-finding S3):**

Per Development Workflow and Audit Standards §3 ("S3 remains mandatory when S2 finds zero deviations: it records a no-change closure and independent delta verification"):

1. Record no-change closure in this audit report's closure table (§7, to be appended by S3).
2. Independently verify delta: re-run the quality/security/test gates on the S3 commit range to confirm no regression (source tree should be byte-for-byte unchanged from this S2's `3588aa6`).
3. Update the session register to mark session 0111 (S3) COMPLETE.

**S4 recommendations (for the documentation session, already partly anticipated by the S1 handoff's own "out-of-scope discoveries"):**

- Add `prin.daemon` to the Sphinx API pages (`DOCS/sphinx/api/`), per the S1 handoff's own logged discovery.
- Update `CHANGELOG.md`, `crates/README.md`, and `DOCS/sphinx/migration_guide.rst` for the deliberate PRINet 3.0 API deviations already documented in-code (`clone_state` vs. `clone`, `create_session`'s return-tuple shape, the new `SelectionReason` enum).
- Resolve the version-string drift the S1 handoff flagged as out-of-scope (`Cargo.toml`/`pyproject.toml`/`python/prin/__init__.py` read `0.3.0-alpha.1` where PSR-027 §6 states the Phase-3-exit bump to `0.5.0-alpha.1` should already be in place) — this is a release-governance question for the maintainer, not a WP-028 code defect, and is correctly left unfixed in S1/S2.
- Update `DOCS/baselines/wp001_api_traceability.md` to point the three deferred symbols (`ControlSignalBuffer`, `export_to_onnx`/`quantize_onnx`, `retrain_controller`) at WP-029/WP-030 respectively.
- Declare WP-029 in the forthcoming PSR-028, per the already-approved Phase 5 roadmap sequencing.

---

## 7. Closure table (appended by S3 remediation)

*(to be completed at session 0111)*

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(no findings — S2 recorded none)* | | | |

**Delta re-audit date:** *(pending)* — **Result:** *(pending)*

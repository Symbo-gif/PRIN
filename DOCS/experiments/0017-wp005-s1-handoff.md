# WP-005 S1 handoff to session 0018

**Session:** 0017 — S1 Coding
**Work package:** WP-005 — ORT backends, wheel matrix, and Phase 0 gate
**Date:** 2026-08-07
**Branch:** `feat/wp005-ort-backends-wheel-matrix-and-phase-0-gate`
**Pre-S1 baseline:** `e954c54` (`feat/wp004-cubecl-fused-rk4-spike` S4 closure)
**Implementation range:** `e954c54..HEAD` (this file's commit)
**Successor:** Session 0018 — mandatory read-only S2 audit

## 1. S1 author claim

The WP-005 S1 implementation and evidence outputs are complete to the author's
knowledge. The Coding Standards local gate is green, the ONNX Runtime provider
probe, the three-OS abi3 wheel smoke matrix, and the Phase 0 exit-gate
consolidation are in place, and the acceptance criteria are mapped below.

This claim is not an audit verdict or cycle-completion claim. Session status and
register updates are reserved for S4. Known host-side limitations (VitisAI
execution provider not installed, DirectML unable to execute this graph on this
host) are recorded as author observations for S2 classification.

## 2. Acceptance-to-evidence map

| WP-005 acceptance criterion | S1 evidence | Author assessment |
|---|---|---|
| ORT CPU provider loads and runs the subconscious controller | `prin._ort.probe_model("models/subconscious_controller.onnx")` returns `can_run=True`, `active_providers=["CPUExecutionProvider"]`, `output_shape=(1, 8)`; evidence at `EVIDENCE/0017-wp005-s1-ort-probe.json` | MET |
| DirectML/VitisAI providers are probed with graceful fallback to CPU | `prin._ort.try_create_session` selects `directml` when `DmlExecutionProvider` is listed, catches the `InvalidGraph`/`RuntimeError` from DirectML, and falls back to `CPUExecutionProvider`; unit tests cover all three backend priority paths (`npu`, `directml`, `cpu`) with fake ORT objects; VitisAI provider is not installed on this host, but the NPU firmware-resolution and provider-list branches are unit-tested | MET (with DirectML fall-back proven; VitisAI runtime not available on this host) |
| Three-OS abi3 wheel smoke matrix is configured | `.github/workflows/release.yml` includes `ubuntu-latest`, `windows-latest`, `macos-latest` and `universal2-apple-darwin`; `crates/prin-py/Cargo.toml` contains `abi3-py311`; `pyproject.toml` contains `Operating System :: OS Independent`; `_check_wheel_matrix` in `prin._phase0` reports all findings green | MET |
| Golden-trajectory corpus is committed and valid | `prin._phase0._check_corpus` reports `n_cases=504` and `cases_match=True` against `parity/corpus/manifest.json` | MET |
| Phase 0 spike go/no-go decisions are recorded | `DOCS/PRIN_Project_Plan.md` contains amendments #7 (DLPack), #11 (CubeCL), and #13 (ORT); `EVIDENCE/0017-wp005-s1-ort-probe.json` exists; `_check_spike_decisions` returns green | MET |
| Phase 0 tag gate is green | `EVIDENCE/0017-wp005-s1-phase0-gate.json` reports `ready=true` with all four checks (`corpus`, `ort`, `wheel_matrix`, `spike_decisions`) `ok` | MET |

## 3. Required evidence map

| Requirement | Evidence | Result |
|---|---|---|
| Tests in tandem | `tests/test_ort_backends.py` (31 tests) and `tests/test_phase0_gate.py` (28 tests) | PASS |
| Rust fmt | `cargo fmt --all -- --check` | PASS |
| Rust clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Rust tests | `cargo test --workspace` | PASS (19 tests) |
| Python ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` and `ruff format --check ...` | PASS |
| Python mypy | `mypy python/prin --strict` | PASS |
| Python doc coverage | `interrogate -c pyproject.toml python/prin` 100% | PASS |
| Python SAST | `bandit -r . -c pyproject.toml` | PASS |
| Python tests | `pytest tests/ parity/ --basetemp=.pytest_basetemp` | PASS (183 tests) |
| Python coverage | `pytest tests/ parity/ --cov=prin --cov-report=term-missing` | 99% total; new modules `prin._ort` and `prin._phase0` 100% |
| Python pip-audit | Root project and Sphinx requirements: no known vulnerabilities | PASS |
| Rust dependency audit | `cargo audit` — `paste` (RUSTSEC-2024-0436) is an allowed warning inherited via `cubecl`; no actionable fix available at this dependency level | PASS with inherited warning noted |
| Snyk Code | 9 low-severity findings, all in `DOCS/archive and reference from PRINet 3.0/` (historical, non-authoritative); 0 findings in `python/`, `tests/`, `tools/` active code | PASS for active code |
| Snyk Open Source | 0 issues | PASS |
| ORT probe evidence | `EVIDENCE/0017-wp005-s1-ort-probe.json` produced by `tools/wp005_ort_probe.py` | CAPTURED |
| Phase 0 gate evidence | `EVIDENCE/0017-wp005-s1-phase0-gate.json` produced by `tools/wp005_phase0_gate.py --refresh-ort` | CAPTURED |

## 4. Implementation summary

- **ONNX Runtime probe (`python/prin/_ort.py`):**
  - `probe_model` builds an `OrtProbeReport` with available providers, selected
    backend, active providers, I/O metadata, `can_run`, output shape, and error.
  - `select_best_backend` auto-detects `npu` (VitisAI) → `directml` → `cpu` and
    supports `PRIN_SUBCONSCIOUS_BACKEND` / `override`.
  - `build_provider_list` constructs ORT `providers` and `provider_options` for
    each backend, including VitisAI firmware and cache configuration.
  - `try_create_session` creates an `InferenceSession` and falls back to CPU when
    the preferred provider fails (e.g., DirectML graph incompatibility).
- **Phase 0 gate (`python/prin/_phase0.py`):**
  - `_check_corpus` validates the golden-trajectory corpus manifest and 504 cases.
  - `_check_ort` reads or refreshes the ORT probe evidence.
  - `_check_wheel_matrix` validates `.github/workflows/release.yml`,
    `crates/prin-py/Cargo.toml`, and `pyproject.toml` for the three-OS abi3
    wheel smoke configuration.
  - `_check_spike_decisions` confirms plan amendments #7, #11, and #13 are
    recorded and that the ORT evidence file exists.
  - `phase0_gate_report` aggregates all checks and `write_gate_report` serializes
    the `Phase0GateReport` to JSON.
- **CLI tools:**
  - `tools/wp005_ort_probe.py` runs `probe_model` and writes the evidence JSON.
  - `tools/wp005_phase0_gate.py` runs `phase0_gate_report --refresh-ort` and
    writes the gate report JSON.
- **CI / packaging wiring:**
  - `.github/workflows/release.yml` updated with Windows and macOS universal2
    targets, `manylinux: auto`, and a wheel smoke step.
  - `.github/workflows/python.yml` updated to build the Rust extension with
    `maturin develop` before running Python tests.
  - `pyproject.toml` `onnx` extra uses `onnxruntime` on non-Windows and
    `onnxruntime-directml` on Windows, plus `onnx>=1.15`.
  - `.gitignore` un-ignores `models/subconscious_controller.onnx` and its
    `.data` companion so the model can be tracked.

## 5. Out-of-scope discovery log

| Discovery | Why not implemented in S1 | Planned owner / next control |
|---|---|---|
| VitisAI NPU runtime validation | `VitisAIExecutionProvider` is not installed in the current `.venv`/ORT build; the NPU provider-list and firmware-resolution code paths are unit-tested with mocks | WP-028 / Phase 5 daemon runtime; `gpu.yml` or NPU runner |
| DirectML graph execution on this host | `DmlExecutionProvider` is listed by ORT but raises `InvalidGraph`/`RuntimeError` for this model; CPU fallback is proven and active | WP-028 / Phase 5; differential parity harness on DirectML-capable runner |
| macOS universal2 wheel build | No Apple Silicon build host in this environment; the `release.yml` matrix and `abi3-py311` feature are configured | CI `release.yml` |
| Phase 0 pre-release tag | Tagging is a release action, not S1 coding; the gate reports green | WP-039 / Phase 7 S4 or release workflow |

## 6. Handoff constraints

- Freeze the S1 source/evidence range for read-only inspection.
- Begin only session `0018-wp005-s2-ort-backends-wheel-matrix-and-phase-0-gate`
  via the audit flow.
- Do not remediate during S2.
- Do not update the session register, brief status, CHANGELOG, or Project State
  Report until their governed sessions.

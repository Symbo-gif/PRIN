# PRIN Audit Report — Cycle 005 / WP-005

**Date:** 2026-08-07
**Auditor:** Devin (AI pair)
**Scope:** WP-005 "ORT backends, wheel matrix, and Phase 0 gate" — `python/prin/_ort.py`, `python/prin/_phase0.py`, `tests/test_ort_backends.py`, `tests/test_phase0_gate.py`, `tools/wp005_ort_probe.py`, `tools/wp005_phase0_gate.py`, `.github/workflows/release.yml`, `.github/workflows/python.yml`, `pyproject.toml`, `.gitignore`, `models/subconscious_controller.onnx`, `models/subconscious_controller.onnx.data`, `AGENTS.md`
**Sessions:** 0017 S1 implementation; 0018 S2 this audit
**Active brief:** `DOCS/sessions/phase-0/0018-wp005-s2-ort-backends-wheel-matrix-and-phase-0-gate.md`
**Git state:** `feat/wp005-ort-backends-wheel-matrix` @ `4977604`
**Pre-S1 baseline:** `c8c443f` (WP-004 S4 closure)
**Implementation commits:** `4977604` — "feat(WP-005 S1): ORT backends, abi3 wheel matrix, and Phase 0 gate"
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-005 delivers the ONNX Runtime provider probe (`python/prin/_ort.py`), the Phase 0 exit-gate consolidation (`python/prin/_phase0.py`), supporting unit and integration tests, CLI tooling, packaging/CI wiring for a three-OS `abi3-py311` wheel matrix, and committed evidence that the subconscious controller model loads and runs with a CPU fallback. The S1 code and tests are written in tandem, Python quality and coverage gates are green, the golden-trajectory corpus is present and valid, and the security/dependency scans are clean.

The audit raises one D3 plan-drift finding on the unrecorded ORT go/no-go decision, one D3 CI/test-coverage finding on the real ORT integration being exercised on only one CI matrix cell, and two D4 hygiene findings on stale READMEs.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared ORT probe, wheel-matrix wiring, Phase 0 gate, evidence, and packaging updates; no daemon runtime or public release |
| Plan/architecture conformance (A2) | ⚠️ | Python layer contains no new numerics; ORT spike go/no-go is not recorded as a plan amendment #13 and the gate check does not validate the plan text (`WP005-F1`) |
| Tests in tandem + coverage (A3) | PASS | 31 tests in `tests/test_ort_backends.py`, 28 in `tests/test_phase0_gate.py`; `prin._ort` 100% line coverage, `prin._phase0` 100% coverage; overall 99% |
| Numerical parity + invariants (A4) | N/A | No new Rust numerics or parity primitives; the controller is treated as an opaque ONNX model during this spike |
| Quality gates (A5) | PASS | ruff, format, mypy `--strict`, interrogate, bandit, `cargo fmt`, `cargo clippy -D warnings`, `cargo test`, `RUSTDOCFLAGS=-D warnings cargo doc`, Sphinx `-W` all pass |
| Security (A6) | PASS | Snyk Code (medium+) and Snyk Open Source (low+) report 0 issues; pip-audit clean; `cargo audit` retains one allowed `paste` RUSTSEC-2024-0436 warning (amendment #9); no new `unsafe` |
| Docstring/doc coverage (A7) | PASS | `interrogate` 100% on `python/prin`; Sphinx build clean; two touched READMEs are stale (`WP005-F3`, `WP005-F4`) |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stubs in new source; `__all__` consistent; `models/README.md` and `tools/README.md` are stale |
| CI status (A9) | ⚠️ | `python.yml` and `release.yml` are green; the actual ORT probe is only exercised on `windows-latest` + Python 3.12 (`WP005-F2`) |
| Artefact trail (A10) | PASS | WP-004 S4 project state and audit are present; S1 handoff `DOCS/experiments/0017-wp005-s1-handoff.md` and evidence JSON are committed and consistent |

## 1.1 Acceptance reproduction

| WP-005 acceptance criterion | Independent result | Assessment |
|---|---|---|
| ORT CPU provider loads and runs the subconscious controller | `probe_model("models/subconscious_controller.onnx")` returns `can_run=True`, `active_providers=["CPUExecutionProvider"]`, `output_shape=(1, 8)`; evidence at `EVIDENCE/0017-wp005-s1-ort-probe.json` | MET |
| DirectML/VitisAI providers are probed with graceful fallback to CPU | `select_best_backend` picks `directml`; `try_create_session` catches the DirectML graph failure and falls back to `CPUExecutionProvider`; VitisAI runtime is not installed on this host but provider-list and firmware-resolution branches are unit-tested with mocks | MET (DirectML fallback proven; VitisAI runtime unavailable here) |
| Three-OS abi3 wheel smoke matrix is configured | `release.yml` covers `ubuntu-latest`, `windows-latest`, `macos-latest` plus `x86_64`, `aarch64`, `universal2-apple-darwin`; `prin-py/Cargo.toml` uses `abi3-py311`; `pyproject.toml` has `Operating System :: OS Independent`; `_check_wheel_matrix` reports green | MET |
| Golden-trajectory corpus is committed and valid | `_check_corpus` reports `n_cases=504`, `cases_match=True` against `parity/corpus/manifest.json` | MET |
| Phase 0 spike go/no-go decisions are recorded | Plan contains amendments #7 (DLPack) and #11 (CubeCL) but **no amendment #13** for ORT; `_check_spike_decisions` passes based only on the evidence file, not on plan text (`WP005-F1`) | **PARTIAL** |
| Phase 0 tag gate is green | `phase0_gate_report` returns `ready=True` with all four checks `ok` in `EVIDENCE/0017-wp005-s1-phase0-gate.json` | MET with caveat (spike_decisions check is incomplete; `WP005-F1`) |

---

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `torch`: 2.13.0+cpu
- `onnxruntime-directml` is installed in the `.venv` and lists `DmlExecutionProvider` and `CPUExecutionProvider`

### 2.2 Scope and artefact commands

```powershell
git log --oneline c8c443f..HEAD
git diff --stat c8c443f..HEAD
```

Key results:

```text
4977604 feat(WP-005 S1): ORT backends, abi3 wheel matrix, and Phase 0 gate
16 files changed, 1862 insertions(+), 5 deletions(-)
```

### 2.3 Python quality, test, and coverage commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

Key results:

```text
ruff check: All checks passed
ruff format --check: 40 files already formatted
mypy: Success: no issues found in 16 source files
interrogate: 100.0% (min 95.0%)
bandit: No issues identified
pytest tests/ -m "not slow and not gpu": 171 passed, 6 deselected
pytest tests/ parity/: 183 passed
coverage: prin._ort 100%, prin._phase0 100%, total 99%
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
sphinx: build succeeded
```

### 2.4 Rust quality, test, and documentation commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy -p prin-kernels --features wgpu,cpu --all-targets -- -D warnings
cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings
cargo test --workspace
cargo test -p prin-kernels --features cpu
cargo test -p prin-kernels --features wgpu,cpu
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy (workspace, wgpu+cpu, cuda): 0 warnings
cargo test --workspace: 19 Rust tests passed
cargo test -p prin-kernels --features cpu: 14 passed
cargo test -p prin-kernels --features wgpu,cpu: 21 passed
cargo doc -D warnings: 0 warnings
```

### 2.5 Dependency and security audit commands

```powershell
cargo audit
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

Key results:

```text
cargo audit: 0 vulnerabilities; 1 inherited paste (RUSTSEC-2024-0436) unmaintained warning (amendment #9)
Snyk Code: issueCount=0
Snyk Open Source: issueCount=0
```

### 2.6 WP-005 acceptance reproduction commands

```powershell
.venv\Scripts\python tools/wp005_ort_probe.py
.venv\Scripts\python tools/wp005_phase0_gate.py --refresh-ort
.venv\Scripts\python tools/wp001_baseline.py check
```

Key results:

```text
ORT probe complete: selected=directml, active=['CPUExecutionProvider'], can_run=True, output_shape=(1, 8)
Evidence written to: EVIDENCE\0017-wp005-s1-ort-probe.json

Phase 0 ready: True
Evidence written to: EVIDENCE\0017-wp005-s1-phase0-gate.json

WP-001 baseline validation passed.
```

---

## 3. Detailed findings

### 3.1 WP/session-brief scope conformance (A1)

The S1 commit adds exactly the artefacts declared in the WP-005 S1 brief and handoff: the ONNX Runtime provider probe, the Phase 0 gate aggregator, unit/integration tests, two CLI tools, the three-OS wheel matrix and packaging wiring, and the model/evidence files. It does not implement the daemon runtime or a public release. Scope is clean.

### 3.2 Plan/architecture conformance (A2)

The implementation keeps all numerics in the existing Rust core (no new math is introduced in Python). `prin._ort` is purely orchestration (provider selection, session creation, dummy-input inference, report generation) and `prin._phase0` is a read-only validator of committed artefacts. Crate layering and the "one algorithm, one implementation" rule are unaffected.

The gap is that the WP-005/Phase 0 ORT go/no-go decision is not recorded as plan amendment #13. `DOCS/PRIN_Project_Plan.md` ends at amendment #12, and `python/prin/_phase0.py` `_check_spike_decisions` treats `amendment_13_ort` as satisfied by the existence of the evidence file rather than by plan text. This allows the gate to pass while the trajectory amendment is absent (`WP005-F1`).

### 3.3 Tests in tandem + coverage (A3)

S1 adds `tests/test_ort_backends.py` and `tests/test_phase0_gate.py` in the same commit as the implementation. The fast suite covers provider selection, provider-list construction (including VitisAI firmware resolution), session creation with CPU fallback, error paths, and the Phase 0 gate checkers. Coverage on the two new modules is 100%, and overall coverage is 99% (the remaining 1% are pre-existing stub `__init__.py` files in `prin.eval`, `prin.experiments`, `prin.nn`, `prin.reporting`, and `prin.datasets`).

The Phase 0 gate tests do not currently assert that the plan text contains an ORT amendment, which mirrors the incomplete implementation (`WP005-F1` remedy).

### 3.4 Numerical parity + invariants (A4)

No new Rust numerics are introduced. The ONNX model is treated as an opaque artefact; the probe only confirms that it loads and returns the expected output shape `(1, 8)`. This is the declared spike scope, so no parity work is required for this WP.

### 3.5 Quality gates (A5)

All Python and Rust quality gates pass. `mypy --strict` reports 16 clean source files (up from 14 before this WP). `interrogate` reports 100% docstring coverage on `python/prin` (including the two new modules). `cargo clippy` with `-D warnings` is clean for the default workspace, `prin-kernels --features wgpu,cpu`, and `prin-kernels --features cuda`.

### 3.6 Security (A6)

- No new `unsafe` code is added (Python only).
- `bandit -r .` reports no issues.
- Snyk Code (medium+ threshold) reports 0 issues.
- Snyk Open Source (low+ threshold) reports 0 issues.
- `pip-audit .` and `pip-audit -r DOCS/sphinx/requirements.txt` report no known vulnerabilities.
- `cargo audit` reports one allowed inherited `paste` (RUSTSEC-2024-0436) warning, governed by plan amendment #9.
- No secrets were added; the model and `.data` files contain only ONNX weights.

### 3.7 Docstring/doc coverage (A7)

`interrogate` is 100% for `python/prin`, including the public and private symbols in `prin._ort` and `prin._phase0`. Sphinx builds without warnings. The touched directory READMEs (`models/README.md` and `tools/README.md`) are stale and do not describe the new `.onnx.data` file or the two new CLI tools (`WP005-F3`, `WP005-F4`).

### 3.8 Repository hygiene (A8)

No TODO/FIXME/stub markers were introduced in the new source. `__all__` is consistent in `prin._ort` and `prin._phase0`. The `.gitignore` correctly un-ignores both `models/subconscious_controller.onnx` and `models/subconscious_controller.onnx.data`. The stale READMEs are documented as `WP005-F3` and `WP005-F4`.

### 3.9 CI status (A9)

`.github/workflows/python.yml` was updated to build the Rust extension with `maturin develop` and to install `onnxruntime-directml` on `windows-latest` with Python 3.12. `.github/workflows/release.yml` was updated to smoke-test all non-`aarch64` wheels and to use `python -m pip install`.

The real ONNX Runtime integration (`test_probe_real_subconscious_model`) is only executed on one CI matrix cell because `onnxruntime` is not installed in the other cells and the test uses `pytest.importorskip`. This leaves the CPU-fallback acceptance unproven on Linux and on the other two Windows Python versions in CI (`WP005-F2`).

### 3.10 Artefact trail (A10)

The WP-004 S4 project state report (`DOCS/reports/004-project-state.md`) and audit (`DOCS/audits/004-wp004-audit.md`) are present and consistent. The WP-005 S1 handoff (`DOCS/experiments/0017-wp005-s1-handoff.md`) and evidence files (`EVIDENCE/0017-wp005-s1-ort-probe.json`, `EVIDENCE/0017-wp005-s1-phase0-gate.json`) are committed. The S2 reproduction wrote matching evidence with a fresh timestamp; the original S1 evidence files were then restored to preserve the S1 evidence baseline.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP005-F1 | D3 | `DOCS/PRIN_Project_Plan.md` §8.3 (no `\| 13 \|` row); `python/prin/_phase0.py:205-218` | The ORT go/no-go decision is not recorded as plan amendment #13, and `_check_spike_decisions` only checks for the evidence file rather than the plan text. The Phase 0 gate can therefore pass without the decision being approved in the plan. | Project Plan §8.3; Development Workflow and Audit Standards §3, A2 | Add amendment #13 to `DOCS/PRIN_Project_Plan.md` recording the WP-005/Phase 0 ORT decision (CPU fallback proven; DirectML graph incompatibility on this host; VitisAI runtime deferred to Phase 5/WP-028). Update `_check_spike_decisions` to require `\| 13 \|` and `ORT`/`ONNX`/`VitisAI` in the plan text plus the evidence file, and update `tests/test_phase0_gate.py` accordingly. |
| WP005-F2 | D3 | `.github/workflows/python.yml:53-55`; `tests/test_ort_backends.py:375-384` | The actual ORT model probe is only exercised in CI on `windows-latest` with Python 3.12. On Linux and on the other Windows Python cells, `test_probe_real_subconscious_model` is skipped because `onnxruntime` is not installed. | Testing Standards §2, A9 | Install the `onnx` extra (or platform-specific `onnxruntime`/`onnxruntime-directml`) in the `python.yml` test job for all matrix cells, or add a dedicated cross-platform ORT probe job that runs on `ubuntu-latest` and `windows-latest`. Ensure the real controller loads and falls back to CPU on all supported CI platforms. |
| WP005-F3 | D4 | `models/README.md:5-9` | README states the model is a single `subconscious_controller.onnx` (104 KB) and is the only `*.onnx` gitignore exemption. The committed artefact is an 18 KB `.onnx` file plus an 86 KB `.onnx.data` companion, and the `.data` file is also un-ignored. | Documentation Standards; A8 | Update `models/README.md` to mention `subconscious_controller.onnx.data`, explain the split (`onnx` + external data) and the combined size, and note that both files are exempted in `.gitignore`. |
| WP005-F4 | D4 | `tools/README.md:7-26` | The tools README does not list the WP-005 CLI tools `wp005_ort_probe.py` and `wp005_phase0_gate.py`. | Documentation Standards §7; A8 | Add entries for `wp005_ort_probe.py` and `wp005_phase0_gate.py` with a short description and example invocation. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP005-F1** (D3), **WP005-F2** (D3), **WP005-F3** (D4), **WP005-F4** (D4).

Carried findings re-inspected and unchanged by this WP:
- WP001-F8 (AMENDED) — GitHub secret scanning substitute remains in force.
- WP003-F1 (AMENDED) — `prin-py` Python-FFI `unsafe` exception remains in force.
- WP003-F3 (AMENDED) — WP-003/Phase 0 go/no-go documented as amendment #7.
- WP004-F1 (AMENDED) — inherited `paste` RUSTSEC-2024-0436 warning remains allowed under amendment #9; reconfirmed by `cargo audit`.
- WP004-F2 (AMENDED) — `#[cube(launch)]` non-instrumentability remains documented under amendment #10; no new CubeCL code in WP-005.
- WP004-F4 (AMENDED) — `prin-kernels` crate-level `unsafe` lint pattern remains under amendment #8.
- WP004-F5 (AMENDED) — Triton 3.0 direct comparison remains deferred to Phase 3/`gpu.yml` under amendment #11.

No open D1 or D2 findings are carried into WP-005.

---

## 6. Verdict and required actions

**Verdict:** `PASS-WITH-FINDINGS` — the WP-005 S1 implementation is in declared scope, the quality and security gates are green, the ORT CPU fallback and Phase 0 gate are proven, and the wheel matrix is correctly configured. The four findings above are not trajectory breaches (no D1/D2), but they must be addressed in S3 before the cycle can close.

**Ordered S3 action list:**

1. **WP005-F1:** Add WP-005/Phase 0 ORT go/no-go as plan amendment #13 in `DOCS/PRIN_Project_Plan.md`. Update `python/prin/_phase0.py::_check_spike_decisions` to verify the plan text contains the amendment, and extend `tests/test_phase0_gate.py` with a regression test that fails when the amendment is missing or the check is weak.
2. **WP005-F2:** Update `.github/workflows/python.yml` so the actual ORT probe runs on Linux and on all targeted Windows Python versions (e.g., by installing the `onnx` extra or the platform-specific runtime). Confirm `test_probe_real_subconscious_model` is no longer skipped in CI on `ubuntu-latest`.
3. **WP005-F3:** Update `models/README.md` to describe `subconscious_controller.onnx` plus `subconscious_controller.onnx.data` and the `.gitignore` exemption.
4. **WP005-F4:** Update `tools/README.md` to document `wp005_ort_probe.py` and `wp005_phase0_gate.py`.

After these fixes, run the full local one-liner, regenerate `EVIDENCE/0017-wp005-s1-phase0-gate.json`, and perform a delta re-audit.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP005-F1 | | | |
| WP005-F2 | | | |
| WP005-F3 | | | |
| WP005-F4 | | | |

**Delta re-audit date:** YYYY-MM-DD — **Result:**

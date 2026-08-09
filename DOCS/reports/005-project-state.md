# PRIN Project State Report — Cycle 005

**Date:** 2026-08-07
**Cycle:** 005 (WP-005 "ORT backends, wheel matrix, and Phase 0 gate")
**Completed sessions:** 0017–0020
**Author:** Devin (AI pair)
**Maintainer approval:** pending
**Git state:** `feat/wp005-ort-backends-wheel-matrix` @ `7dbf736` (pre-S4 documentation baseline)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 0 — Foundation (**5 of 5** phase-0 WPs complete). **Phase 0
  exit gate is GREEN.**
- **This cycle delivered:** The ONNX Runtime execution-provider probe
  (`python/prin/_ort.py`) for the subconscious controller (CPU/DirectML/VitisAI
  with graceful fallback), the Phase 0 exit-gate consolidation
  (`python/prin/_phase0.py`) validating the three foundation spikes, the
  golden-trajectory corpus, the abi3 wheel smoke matrix, and the recorded
  go/no-go decisions, the three-OS abi3 wheel matrix wiring in `release.yml`
  and `python.yml`, the committed pre-trained subconscious controller ONNX
  model, two CLI tools (`tools/wp005_ort_probe.py`,
  `tools/wp005_phase0_gate.py`), and 59 unit/integration tests. S3 closed all
  S2 findings (one plan amendment #13 and three direct fixes). S4 updated all
  affected READMEs, `CHANGELOG.md`, the Sphinx `migration_guide.rst`, the
  master `SESSION_REGISTER.md`, and this report.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendment #13 from
  WP-005 S3 is in force. No numerical implementation was introduced (the
  controller is treated as an opaque ONNX model during this spike).
- **Audit:** `DOCS/audits/005-wp005-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS` (four findings: F1–F2 D3, F3–F4 D4); S3 delta re-audit
  **CLEAN**, all findings resolved (four fixed, one of which also recorded as
  plan amendment #13).
- **Session Register:** 0017 (S1), 0018 (S2), 0019 (S3), 0020 (S4) marked
  **COMPLETE**; 0021 (WP-006 S1) marked **READY**.

### 1.1 Phase 0 exit-gate verdict

The Phase 0 exit gate is **GREEN**. The `phase0_gate_report` returns
`ready=True` with all four checks ok:

| Check | Result | Evidence |
|---|---|---|
| Corpus | 504 cases match manifest | `parity/corpus/manifest.json` |
| ORT probe | selected=directml, active=`['CPUExecutionProvider']`, can_run=True, output_shape=(1, 8) | `EVIDENCE/0017-wp005-s1-ort-probe.json` |
| Wheel matrix | three-OS abi3-py311 matrix, OS Independent classifier, wheel smoke step | `release.yml`, `prin-py/Cargo.toml`, `pyproject.toml` |
| Spike decisions | amendments #7 (DLPack), #11 (CubeCL), #13 (ORT) all present in plan text | `DOCS/PRIN_Project_Plan.md` §8.3 |

All three Phase 0 spikes meet their go/no-go criteria:
- **DLPack (WP-003, amendment #7):** CPU round-trip and batched boundary
  exchange validated; CUDA round-trip and `<5%` training-step overhead deferred
  to Phase 4.
- **CubeCL (WP-004, amendment #11):** PRINet 3.0 PyTorch reference and
  wgpu/CubeCL-CPU kernel-equivalence at N=1M validated; direct same-hardware
  Triton 3.0 comparison deferred to Phase 3 / `gpu.yml`.
- **ORT (WP-005, amendment #13):** CPU fallback for the subconscious controller
  proven on all CI platforms; DirectML graph execution falls back to CPU on
  the current Windows host; VitisAI NPU runtime and DirectML parity deferred to
  WP-028 (Phase 5 daemon) with a re-audit gate.

The golden-trajectory corpus (504 cases) is committed and valid. The three-OS
abi3 wheel matrix is configured and smoke-tested. Phase 0 is complete and ready
for the `v0.1.0-alpha.1` pre-release tag per the Versioning and Release
Standards.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 19/19 (workspace), 14/14 (`--features cpu`), 21/21 (`--features wgpu,cpu`) | 19/19, 14/14, 21/21 (unchanged — no new Rust code in WP-005) | 100% where defined |
| Python tests passing | 112 fast (6 deselected), 124 full | 172 fast (6 deselected), 184 full (tests + parity) | 100% |
| Coverage (changed code) | `prin-kernels` 88.21% line (amendment #10) | `prin._ort` 100%, `prin._phase0` 100%, total 99% | ≥95% |
| Docstring coverage (interrogate) | 100% public (79/79) | 100% public (104/104) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, 6 representative differential tests pass | 504 defined, 6 representative differential tests pass (unchanged) | 100% at tolerance when defined |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 warning (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code (medium+ threshold) | 0 | 0 medium/high findings | 0 at gate threshold |
| Snyk Open Source (low+ threshold) | 0 | 0 findings | 0 at gate threshold |
| Benchmark regression gates | N/A | none defined | none tripped |

**Verification commands run in S4:**

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python tools/wp001_baseline.py check
.venv\Scripts\python tools/wp005_ort_probe.py
.venv\Scripts\python tools/wp005_phase0_gate.py --refresh-ort
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy -p prin-kernels --features wgpu,cpu --all-targets -- -D warnings
cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings
cargo test --workspace
cargo test -p prin-kernels --features cpu
cargo test -p prin-kernels --features wgpu,cpu
cargo llvm-cov -p prin-kernels --features wgpu,cpu
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

S4 re-ran the full one-liner after all documentation edits (README sweep,
Sphinx `migration_guide.rst`, CHANGELOG, session register, and this report).
All quality, coverage, documentation, security, and parity gates remain green.

## 3. Deviation ledger (cumulative)

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| WP001-F1 | 001 | D1 | PyO3 dependency carried two RustSec advisories | FIXED | `13eac9e`; PyO3/rust-numpy 0.29.0 |
| WP001-F2 | 001 | D1 | `python.yml` did not audit all dependencies and suppressed failures | FIXED | `510e0c9`; project/docs Pip Audit gating |
| WP001-F3 | 001 | D1 | Long-lived crates.io token in `release.yml` | FIXED | `510e0c9`; pre-WP-005 guard |
| WP001-F4 | 001 | D2 | Traceability check was fail-open on symbol count | FIXED | `510e0c9`; exact 657 contract + mutation test |
| WP001-F5 | 001 | D2 | Duplicate session brief IDs could pass validation | FIXED | `510e0c9`; duplicate-ID regression test |
| WP001-F6 | 001 | D2 | Repro CI path was not explicitly guarded | FIXED | `510e0c9`; pre-WP-035 guard |
| WP001-F7 | 001 | D2 | Unready workspace crate publication was possible | FIXED | `510e0c9`; publication guard |
| WP001-F8 | 001 | D1 | GitHub secret scanning/push protection unavailable | AMENDED | Plan amendment #5; Gitleaks + branch-protection substitute |
| WP001-F9 | 001 | D4 | Sphinx had two warnings and a misattribution | FIXED | `510e0c9`; warning-free wheel-backed build |
| WP001-F10 | 001 | D2 | `main` was unprotected | FIXED | Hosted setting, 2026-08-06 |
| WP001-F11 | 001 | D2 | Linux Python/Repro jobs did not create explicit venvs | FIXED | `510e0c9`; explicit venvs in `python.yml`/`repro.yml` |
| WP002-F1 | 002 | D2 | Fast `tests/` suite was below 95% coverage on `prin.parity` | FIXED | `c7d8a25`; fast-suite regression tests, `prin.parity` 100% |
| WP002-F2 | 002 | D2 | Snyk Open Source reported 12 docs-dependency advisories | FIXED | `d6037b8`; pinned transitive minimums, Snyk/pip-audit 0 |
| WP002-F3 | 002 | D4 | Stale docstrings/PyPI references for `prin.parity` | FIXED | `d0b7207`; docstring, README, markers updated |
| WP002-F4 | 002 | D4 | `bandit -r parity/` flagged test `assert` | FIXED | `4da34da`; `parity/` and archive in `bandit` exclusions |
| WP003-F1 | 003 | D2 | `unsafe` in `prin-py` outside the `prin-kernels` exception | AMENDED | Plan amendment #6; Coding Standards §2.1/§6.1 Python-FFI exception |
| WP003-F2 | 003 | D2 | Missing shape-dimension sign validation before `std::slice::from_raw_parts` | FIXED | `b481078`; `BridgeError::NegativeDim`, `validate_shape`, Rust + Python regression tests |
| WP003-F3 | 003 | D3 | WP-003/Phase 0 go/no-go amendment not recorded | AMENDED | Plan amendment #7; CPU path validated, CUDA + `<5%` deferred to Phase 4 |
| WP003-F4 | 003 | D4 | Package docstring omits the new `prin.dlpack` module | FIXED | `b481078`; `python/prin/__init__.py` updated |
| WP003-F5 | 003 | D4 | `python/prin/dlpack.py` lacks `__all__` | FIXED | `b481078`; `__all__` added, ruff + baseline check pass |
| WP004-F1 | 004 | D2 | `paste` RUSTSEC-2024-0436 inherited from `cubecl` 0.10.0 | AMENDED | Plan amendment #9; re-check every cycle, upgrade when fixed upstream |
| WP004-F2 | 004 | D2 | `cargo-llvm-cov` line coverage 86.36% due to non-instrumentable `#[cube(launch)]` bodies | AMENDED | Plan amendment #10; instrumentable code ≥95%, kernel equivalence validates correctness |
| WP004-F3 | 004 | D2 | Missing `proptest` invariants for `step_cpu` | FIXED | Added proptest module + deterministic RK4 scaling test; `cargo test -p prin-kernels --features wgpu,cpu` passes 21 tests |
| WP004-F4 | 004 | D2 | `prin-kernels` crate-level unsafe lint relaxed without plan amendment | AMENDED | Plan amendment #8; `#![deny(unsafe_code)]` + module `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, `// SAFETY:` justifications |
| WP004-F5 | 004 | D3 | Direct same-hardware Triton 3.0 fused-kernel comparison blocked on Windows Python 3.14 | AMENDED | Plan amendment #11; PyTorch reference + wgpu/CPU equivalence validated, Triton timing deferred to Phase 3 / `gpu.yml` |
| WP004-F6 | 004 | D3 | `try_step_wgpu`/`try_step_cuda` could panic on missing backend | FIXED | `catch_unwind` + `MeanFieldRk4Error::BackendUnavailable` + regression test |
| WP004-F7 | 004 | D3 | Default CI did not run `cpu`/`wgpu` kernel-equivalence tests | FIXED + AMENDED | `rust.yml` runs `--features cpu`; `wgpu` deferred to headless GPU runner (amendment #12) |
| WP004-F8 | 004 | D3 | `StepReport.wall_time_seconds` used host wall-clock, not device events | FIXED | Documented prototype caveat in rustdoc; device-event timing is Phase 3 |
| WP004-F9 | 004 | D4 | Stale log message and READMEs omit `cpu`/WP-004 spike | FIXED | Corrected log label, updated `crates/prin-kernels/README.md` and `crates/README.md` |
| WP005-F1 | 005 | D3 | ORT go/no-go not recorded as plan amendment #13; gate check did not validate plan text | FIXED | Plan amendment #13; commit `fe5dc8b`; `_check_spike_decisions` requires `\| 13 \|` and ORT/ONNX/VitisAI in plan text; regression `test_missing_ort_amendment_in_plan` |
| WP005-F2 | 005 | D3 | Real ORT model probe only exercised on one CI matrix cell | FIXED | Commit `82db761`; `python.yml` installs `-e ".[dev,onnx]"` on every test matrix cell |
| WP005-F3 | 005 | D4 | `models/README.md` did not describe the split ONNX model files | FIXED | Commit `b5fc211`; README describes both `.onnx` and `.onnx.data` files and gitignore exemption |
| WP005-F4 | 005 | D4 | `tools/README.md` did not list the WP-005 CLI tools | FIXED | Commit `39cef38`; README lists `wp005_ort_probe.py` and `wp005_phase0_gate.py` |

No findings are carried.

## 4. Plan amendments this cycle

One new plan amendment introduced in WP-005 (the twelve approved amendments
from cycles 001–004 remain in force):

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| #13 | Project Plan §6 (WP-005/Phase 0) | Recorded the WP-005/Phase 0 ORT go/no-go: the CPU fallback for the subconscious controller is proven on all CI platforms; DirectML graph execution falls back to CPU on the current Windows host; the VitisAI NPU runtime and DirectML parity are unavailable in Phase 0 and deferred to WP-028 (Phase 5 daemon) with a re-audit gate. | maintainer approval |

## 5. Risks and blockers

- **Phase 0 complete:** All three foundation spikes (DLPack, CubeCL, ORT) meet
  their go/no-go criteria with approved amendments (#7, #11, #13). The
  golden-trajectory corpus (504 cases) is committed and valid. The three-OS
  abi3 wheel matrix is configured. Phase 0 is ready for the
  `v0.1.0-alpha.1` pre-release tag.
- **Deferred validation items:** CUDA DLPack round-trip and `<5%` training-step
  overhead (Phase 4, amendment #7); direct Triton 3.0 same-hardware comparison
  (Phase 3 / `gpu.yml`, amendment #11); VitisAI NPU runtime and DirectML parity
  (WP-028 / Phase 5, amendment #13); `wgpu` kernel-equivalence in CI
  (headless GPU runner, amendment #12).
- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at
  the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; Snyk Open
  Source reports no findings.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with
  `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp` on Windows;
  the directory is ignored by `.gitignore`.
- **GitHub native secret scanning:** Remains unavailable for this private
  repository. Amendment #5's substitute is in force; availability must be
  rechecked each cycle.
- **No current blockers** for starting WP-006 S1 once maintainer approval is
  recorded and the Phase 0 tag is applied.

## 6. Next work package declaration — WP-006

- **Title:** Oscillator state, errors, and deterministic seed.
- **Scope (files/crates/modules):** `crates/prin-dynamics` — struct-of-arrays
  oscillator state, phase wrap/safe difference, amplitude and derivative
  guards, typed errors, and the single counter-based `Seed` authority
  (Philox/PCG64).
- **Plan sections advanced:** §4 (architecture rules — explicit state,
  deterministic seeding), §6 Phase 1 (Dynamics core), §5 (numerical hazards —
  phase wrap `% 2π`, amplitude clamp `[1e-6, 10]`, derivative clamp `±1e4`).
- **Acceptance criteria:**
  - Unit/property/parity tests cover N=1, invalid shapes/ranges, wrap
    semantics, clamps, reproducibility, and `strict-checks` behavior.
  - ≥95% coverage on new/changed code; `cargo fmt`, clippy `-D warnings`,
    rustdoc `-D warnings`, ruff, mypy `--strict`, interrogate, bandit, pytest,
    dependency audits all clean.
  - Relevant golden cases and invariants green at registered tolerances.
  - No hidden global RNG; deterministic `Seed` threaded through every
    stochastic entry point.
- **Non-goals:** Dynamics equations, integrators, or hidden global RNG.
- **First session brief:** `DOCS/sessions/phase-1/0021-wp006-s1-oscillator-state-errors-and-deterministic-seed.md`
- **Maintainer approval:** pending

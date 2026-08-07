# PRIN Project State Report — Cycle 004

**Date:** 2026-08-07
**Cycle:** 004 (WP-004 "CubeCL fused mean-field RK4 spike")
**Completed sessions:** 0013–0016
**Author:** Devin (AI pair)
**Maintainer approval:** pending
**Git state:** `feat/wp004-cubecl-fused-rk4-spike` @ `e954c54` (pre-S4 baseline)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 0 — Foundation (4 of 5 phase-0 WPs complete).
- **This cycle delivered:** The CubeCL fused mean-field RK4 spike in
  `crates/prin-kernels` — a CPU reference `step_cpu`, single-source CubeCL
  kernels in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs`, runtime
  entry points `try_step_cpu`, `try_step_wgpu`, and `try_step_cuda`, typed
  `MeanFieldRk4Error` with a `BackendUnavailable` fallback, `StepReport`
  timing metadata, `proptest` invariants, and kernel-equivalence tests
  validating wgpu and CubeCL-CPU against the CPU reference at N=64 and
  N=1M. S3 closed all S2 findings (five plan amendments #8–#12 and direct
  fixes). S4 updated all affected READMEs, `CHANGELOG.md`, Sphinx
  `kernel_architecture.rst` and `migration_guide.rst`, rustdoc, the master
  `SESSION_REGISTER.md`, and this report.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #8–#12
  from WP-004 S3 are in force. No numerical implementation was introduced
  beyond the declared spike scope.
- **Audit:** `DOCS/audits/004-wp004-audit.md` — S2 verdict
  `PASS-WITH-FINDINGS` (nine findings: F1–F4 D2, F5–F8 D3, F9 D4); S3
  delta re-audit **CLEAN**, all findings resolved (three fixed, six
  approved-amended).
- **Session Register:** 0013 (S1), 0014 (S2), 0015 (S3), 0016 (S4) marked
  **COMPLETE**; 0017 (WP-005 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 9/9 (workspace default), 16/16 (`prin-kernels` wgpu+cpu) | 19/19 (`cargo test --workspace`), 14/14 (`prin-kernels --features cpu`), 21/21 (`prin-kernels --features wgpu,cpu`) | 100% where defined |
| Python tests passing | 112 fast, 124 full | 112 fast (6 deselected), 124 full | 100% |
| Coverage (changed code) | 100% (`prin.parity`, `prin.dlpack`) | `prin-kernels` 88.21% line / 88.40% region overall; `mean_field_rk4.rs` 99.67%, `ops.rs` 100%, `cubecl.rs` 80.42% (non-instrumentable `#[cube(launch)]` stubs; see amendment #10) | ≥95% instrumentable code per amendment #10 |
| Docstring coverage (interrogate) | 100% public | 100% public (79/79) | ≥95% overall, 100% public |
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
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp
.venv\Scripts\python tools/wp001_baseline.py check
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
Sphinx `kernel_architecture.rst`/`migration_guide.rst`, CHANGELOG, session
register, and this report). All quality, coverage, documentation, security,
and parity gates remain green.

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

No findings are carried.

## 4. Plan amendments this cycle

Five new plan amendments introduced in WP-004 (the seven approved amendments
from cycles 001–003 remain in force):

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| #8 | Coding Standards §2.1, §6.1 | Approved the same audited kernel-FFI `unsafe` pattern already used for `prin-py` for `prin-kernels`: crate-level `#![deny(unsafe_code)]`, module-level `#![allow(unsafe_code)]` with `#![deny(unsafe_op_in_unsafe_fn)]`, a `// SAFETY:` justification on every `unsafe` block, and second-reviewer sign-off recorded in the WP-004 S3 audit. This is the only permitted `unsafe` pattern outside the previously audited Python-FFI module. | maintainer approval |
| #9 | Project Plan §6 / Coding Standards §6.2 | Accepted the inherited `paste` RUSTSEC-2024-0436 warning as a transitive dependency of `cubecl` 0.10.0 with no upstream patch or replacement available at this dependency level; re-check every S3/S4 cycle and upgrade/patch as soon as a fixed `cubecl` release is available. | maintainer approval |
| #10 | Testing Standards §4 | Documented that `#[cube(launch)]` kernel launch bodies in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` are not instrumentable by `cargo-llvm-cov` on stable Rust; coverage for the file is reported as-is, the 93 uncovered lines are the two kernel stubs, and correctness is verified by kernel-equivalence tests. The instrumentable surrounding code (CPU reference, runtime launch, tests) remains at ≥95% line coverage. | maintainer approval |
| #11 | Project Plan §3.2 N1 / WP-004 acceptance criterion | Recorded the WP-004/Phase 0 go/no-go: the PRINet 3.0 PyTorch reference and the wgpu/CubeCL-CPU kernel-equivalence at N=1M are validated; the direct same-hardware Triton 3.0 fused-kernel comparison is deferred to a Linux/CUDA runner in Phase 3 or the `gpu.yml` workflow with evidence. | maintainer approval |
| #12 | Testing Standards §2 / Development Workflow and Audit Standards A9 | Added `cargo test -p prin-kernels --features cpu` to the default `rust.yml` matrix; the `wgpu` kernel-equivalence CI step is gated by availability of a headless GPU runner and remains in the opt-in `gpu.yml` / local validation path until such a runner is available. | maintainer approval |

## 5. Risks and blockers

- **Phase 0 spike go/no-go:** WP-004 CPU and wgpu kernel-equivalence are
  validated (amendments #10–#12). The direct Triton 3.0 same-hardware
  comparison and CUDA path validation are deferred to Phase 3 / `gpu.yml`.
  WP-005 (ORT backends, wheel matrix, Phase 0 gate) is the last Foundation WP.
- **Inherited `paste` advisory:** Carried per amendment #9; no upstream fix at
  the PRIN dependency level. Re-checked in S3/S4 with `cargo audit`; Snyk Open
  Source reports no findings.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with
  `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp` on Windows;
  the directory is ignored by `.gitignore`.
- **GitHub native secret scanning:** Remains unavailable for this private
  repository. Amendment #5's substitute is in force; availability must be
  rechecked each cycle.
- **No current blockers** for starting WP-005 S1 once maintainer approval is
  recorded.

## 6. Next work package declaration — WP-005

- **Title:** ORT backends, wheel matrix, and Phase 0 gate.
- **Scope (files/crates/modules):** ONNX Runtime provider probing
  (CPU/DirectML/VitisAI), three-OS abi3 wheel smoke matrix, Phase 0 go/no-go
  consolidation, golden-corpus readiness, and release/wheel guards.
- **Plan sections advanced:** §3.2 N5 (Distribution — prebuilt wheels), §6
  Phase 0 exit criteria, §9 DoD (pre-release gates).
- **Acceptance criteria:**
  - F5 (ONNX controller) fallback is proven on CPU/DirectML/VitisAI where
    available.
  - Wheels install without a compiler on Linux, Windows, and macOS.
  - All Phase 0 spike decisions are approved and recorded.
  - Golden corpus is committed and parity harness remains green.
  - Phase 0 tag/release gate is green.
- **Non-goals:** Daemon runtime implementation or public release.
- **First session brief:** `DOCS/sessions/phase-0/0017-wp005-s1-ort-backends-wheel-matrix-and-phase-0-gate.md`
- **Maintainer approval:** pending

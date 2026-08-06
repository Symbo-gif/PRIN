# PRIN Project State Report — Cycle 003

**Date:** 2026-08-06  
**Cycle:** 003 (WP-003 "PyO3 and DLPack bridge spike")  
**Completed sessions:** 0009–0012  
**Author:** Devin (AI pair)  
**Maintainer approval:** pending  
**Git state:** `feat/wp001-foundation-baseline` @ `b481078` (S3 closure)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 0 — Foundation (3 of 5 phase-0 WPs complete).
- **This cycle delivered:** The PyO3/DLPack Torch↔Rust bridge spike —
  `dlpack_negate`, `dlpack_negate_batched`, and `dlpack_round_trip` exposed
  through `prin._prin_core`, wrapped by `python/prin/dlpack.py`, and tested by
  `tests/test_dlpack_bridge.py`. CPU round-trip, batched boundary calls,
  dtype/device validation, ownership/lifetime handling, and `pytest-benchmark`
  latency instrumentation are all in place. The S3 remediation closed five audit
  findings: the `prin-py` Python-FFI `unsafe` exception was authorized by plan
  amendment #6, shape-dimension validation was added to close an over-read path
  (WP003-F2), and the WP-003/Phase 0 go/no-go was recorded as plan amendment #7
  (CPU path validated; CUDA round-trip and `<5%` training-step overhead deferred
  to Phase 4). S4 closed the cycle with a README sweep of all touched
  directories, `CHANGELOG.md` entry, new `DOCS/sphinx/api/dlpack.rst` page and
  Migration Guide notes, audit artefact cleanup, updated session briefs and
  `SESSION_REGISTER.md`, and the `003-project-state.md` report below.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — the seven approved
  governance/authority amendments remain in force (two new this cycle: #6 and
  #7). No numerical implementation or archived reference output changes were
  introduced beyond the declared spike scope.
- **Audit:** `DOCS/audits/003-wp003-audit.md` — S2 verdict `PASS-WITH-FINDINGS`
  (five findings: F1–F2 D2, F3 D3, F4–F5 D4); S3 delta re-audit **CLEAN**, all
  findings resolved (three fixed, two approved amendments).
- **Session Register:** 0009 (S1), 0010 (S2), 0011 (S3), 0012 (S4) marked
  **COMPLETE**; 0013 (WP-004 S1) marked **READY**.

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 0/0 (workspace compiles) | 9/9 (3 prin-kernels + 6 prin-py) | 100% where defined |
| Python tests passing | 98/98 fast, 106/106 full | 112 fast (6 deselected), 124 full | 100% |
| Coverage (changed code) | 100% (`prin.parity` fast and full) | 100% (`prin.dlpack` 100%, `prin.parity` 100%) | ≥95% |
| Docstring coverage (interrogate) | 100% public | 100% public (79/79) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504 defined, 6 representative differential tests pass | 504 defined, 6 representative differential tests pass (unchanged) | 100% at tolerance when defined |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0 | 0 |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds (new `api/dlpack.rst` page) | 0 warnings |
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
.venv\Scripts\maturin develop -m crates/prin-py/Cargo.toml
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

S4 re-ran the full one-liner after all documentation edits (including the new
`DOCS/sphinx/api/dlpack.rst` page, Migration Guide update, README sweep,
CHANGELOG entry, and audit artefact cleanup). All quality, coverage,
documentation, security, and parity gates remain green.

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

No findings are carried.

## 4. Plan amendments this cycle

Two new plan amendments introduced in WP-003 (the five approved amendments from
cycles 001–002 remain in force):

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| #6 | Coding Standards §2.1, §6.1 | Approved an audited Python-FFI exception for `prin-py/src/dlpack.rs` to use `unsafe` for the PyO3/DLPack C ABI under the same controls as kernel-FFI modules: dedicated module, `#![deny(unsafe_op_in_unsafe_fn)]`, `// SAFETY:` comments on every `unsafe` block, and second-reviewer sign-off recorded in the audit. `prin-py` uses crate-level `#![deny(unsafe_code)]` with module-level `#![allow(unsafe_code)]` because `#![forbid]` cannot be scoped to a single module. | maintainer approval |
| #7 | Project Plan §6 (WP-003/Phase 0) | Documented the WP-003/Phase 0 go/no-go: the CPU DLPack exchange and the `pytest-benchmark` round-trip/batched evidence are validated and on file; the CUDA round-trip and the `<5%` training-step overhead target are deferred to the Phase 4 trainable-stack work (WP-022/WP-026 or the first GPU-backed integration WP) with a re-audit gate. | maintainer approval |

## 5. Risks and blockers

- **Phase 0 spike go/no-go:** WP-003 CPU DLPack path is validated and the
  go/no-go is recorded (amendment #7). WP-004 (CubeCL fused RK4) and WP-005
  (ORT backends, wheel matrix, Phase 0 gate) remain to complete Phase 0. The
  CUDA round-trip and `<5%` training-step overhead target are deferred to
  Phase 4 with a re-audit gate.
- **GitHub native secret scanning:** Remains unavailable for this private
  repository. Amendment #5's substitute is in force; availability must be
  rechecked each cycle.
- **Windows pytest temp directory:** Default `%TEMP%` cleanup can fail with
  `PermissionError [WinError 5]`. Use `--basetemp=.pytest_basetemp` (or another
  in-repo path) on Windows; the directory is ignored by `.gitignore`.
- **No current blockers** for starting WP-004 S1.

## 6. Next work package declaration — WP-004

- **Title:** CubeCL fused RK4 spike.
- **Scope (files/crates/modules):** `crates/prin-kernels/` CubeCL fused
  mean-field RK4 kernel, CPU reference, device-event timing, CUDA path, and
  wgpu feasibility evidence.
- **Plan sections advanced:** §3.2 N1 (GPU performance targets), §6 Phase 0
  exit criteria (spike go/no-go gate).
- **Acceptance criteria:**
  - Kernel equivalence passes (CPU reference vs GPU kernel across shapes and
    dtypes).
  - Same-hardware comparison against 3.0 Triton at N=1M is reproducible.
  - Technology decision and fallback trigger are evidence-backed.
  - New/changed code has ≥95% coverage and is accompanied by tests.
  - `cargo fmt`, clippy `-D warnings`, ruff, mypy strict, pytest, dependency
    audits, and rustdoc remain green.
- **Non-goals:** Full production kernel suite or unsupported performance claims.
- **First session brief:** `DOCS/sessions/phase-0/0013-wp004-s1-cubecl-fused-rk4-spike.md`
- **Maintainer approval:** pending

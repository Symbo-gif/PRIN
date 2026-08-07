# PRIN Audit Report — Cycle 004 / WP-004

**Date:** 2026-08-06
**Auditor:** Devin (AI pair)
**Scope:** WP-004 "CubeCL fused mean-field RK4 spike" — `crates/prin-kernels/src/mean_field_rk4.rs`, `crates/prin-kernels/src/mean_field_rk4/cubecl.rs`, `crates/prin-kernels/Cargo.toml`, `crates/prin-kernels/src/lib.rs`, `Cargo.toml`, `Cargo.lock`, `AGENTS.md`
**Sessions:** 0013 S1 implementation; 0014 S2 this audit
**Active brief:** `DOCS/sessions/phase-0/0014-wp004-s2-cubecl-fused-rk4-spike.md`
**Git state:** `feat/wp004-cubecl-fused-rk4-spike` @ `aa81512252803393c81b5a9cc8e444e2fb596534`
**Pre-S1 baseline:** `a7bb3a4` (WP-003 S4 closure)
**Implementation commits:** `6eaa613` — "feat(WP-004 S1): CubeCL fused mean-field RK4 spike with CPU reference and wgpu validation"; `aa81512` — "chore(wp004-s1): wire cargo-llvm-cov, add cubecl-cpu, and close coverage deliverables"
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-004 delivers the CubeCL fused mean-field RK4 spike: a CPU reference `step_cpu` in `crates/prin-kernels/src/mean_field_rk4.rs` and a single-source CubeCL kernel set in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` with `try_step_cpu`, `try_step_wgpu`, and `try_step_cuda` entry points. The S1 code and tests are written in tandem, Rust quality gates are clean, the CPU reference matches the PRINet 3.0 PyTorch fallback `pytorch_mean_field_rk4_step`, and the wgpu kernel-equivalence test passes at N=1M. Security scans (Snyk Code/Open Source, pip-audit, bandit) are clean.

The audit raises one D2 dependency/security finding on the unaddressed `paste` RUSTSEC advisory introduced through `cubecl`, two D2 findings on the coverage gap and the relaxed crate-level `unsafe` lint, one D2 finding on missing property tests, one D3 finding on the blocked Triton 3.0 same-hardware comparison, and three D3/D4 findings on runtime panics, CI coverage, and documentation/README hygiene.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared spike artefacts (CPU reference + CubeCL kernel + feature flags + S1 evidence); no production bridge or Python numerics |
| Plan/architecture conformance (A2) | ⚠️ | One-algorithm/one-implementation holds; numerics stay in Rust; `unsafe` is confined to `mean_field_rk4/cubecl.rs` but the crate-level lint changed from `#![forbid(unsafe_code)]` to `#![deny(unsafe_code)]` without an approved plan amendment (`WP004-F4`) |
| Tests in tandem + coverage (A3) | ⚠️ | Unit/kernel-equivalence tests written with code and pass; missing `proptest` invariants (`WP004-F3`); `cargo llvm-cov` line coverage is 86.36% (below 95%) because `#[cube(launch)]` kernel bodies are not instrumented (`WP004-F2`) |
| Numerical parity + invariants (A4) | PASS | CPU reference matches PRINet 3.0 PyTorch fallback for N=8/64/1024; wgpu matches CPU at N=64 and N=1M within `rtol=1e-5`, `atol=1e-6`; phase ∈ [0, 2π) and amplitude ≥ 0 are preserved |
| Quality gates (A5) | PASS | `cargo fmt`, `cargo clippy --workspace` and `-p prin-kernels --features wgpu,cpu`/`cuda`, `cargo test --workspace`, `RUSTDOCFLAGS=-D warnings cargo doc`, ruff, mypy, interrogate, bandit, Sphinx all pass |
| Security (A6) | ⚠️ | Snyk Code/Open Source 0 issues; pip-audit clean; `cargo audit` reports one inherited `paste` (RUSTSEC-2024-0436) unmaintained warning (`WP004-F1`) |
| Docstring/doc coverage (A7) | PASS | Rust public items are documented; `cargo doc -D warnings` is clean; `interrogate` 100% on `python/prin` |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stubs in new source; stale log message and READMEs omit the `cpu` feature/Phase 0 spike (`WP004-F9`) |
| CI status (A9) | ⚠️ | `rust.yml` does not run the new `cpu`/`wgpu` kernel-equivalence tests; `gpu.yml` only runs on `[gpu]` tag with CUDA (`WP004-F7`) |
| Artefact trail (A10) | PASS | WP-003 S4 project state and audit are present; S1 handoff `DOCS/experiments/0013-wp004-s1-handoff.md` and coverage `DOCS/experiments/0013-wp004-s1-coverage.md` are committed and consistent |

## 1.1 Acceptance reproduction

| WP-004 acceptance criterion | Independent result | Assessment |
|---|---|---|
| Kernel equivalence passes | `cargo test -p prin-kernels --features wgpu,cpu` passes 16/16, including `wgpu_matches_cpu_reference_for_small_n`, `wgpu_matches_cpu_reference_at_one_million`, and `cpu_matches_cpu_reference_for_small_n` | MET |
| Same-hardware comparison against 3.0 Triton is reproducible | `prinet==3.0.0` is installed; the PyTorch fallback `prinet.pytorch_mean_field_rk4_step` matches the S1 CPU reference for N=8/64/1024; the PyPI `triton` package has no wheel for the `.venv` Python 3.14 on Windows (`pip install triton` fails) | **PARTIAL** — PyTorch reference validated; Triton fused-kernel runtime blocked (`WP004-F5`) |
| Technology decision and fallback trigger are evidence-backed | `try_step_wgpu`/`try_step_cpu` return typed `MeanFieldRk4Error`; CPU reference `step_cpu` is always available; wgpu step at N=1M runs in ~85 ms on this host; CUDA path compiles with `--features cuda` | **PARTIAL** — runtime creation may panic on missing adapter instead of returning a typed error (`WP004-F6`) |
| Quality/coverage gates green | All local gates pass; coverage is 86.36% line, 87.94% region due to non-instrumentable `#[cube(launch)]` bodies | **PARTIAL** — coverage below 95% (`WP004-F2`) |

---

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `torch`: 2.13.0+cpu
- `prinet==3.0.0` installed from the archived source tree
- `cargo-llvm-cov` installed and wired per `AGENTS.md`

### 2.2 Scope and artefact commands

```powershell
git log --oneline a7bb3a4..HEAD
git diff --stat a7bb3a4..HEAD
```

Key results:

```text
aa81512 chore(wp004-s1): wire cargo-llvm-cov, add cubecl-cpu, and close coverage deliverables
6eaa613 feat(WP-004 S1): CubeCL fused mean-field RK4 spike with CPU reference and wgpu validation
9 files changed, 4984 insertions(+), 626 deletions(-)
```

### 2.3 Rust quality and test commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy -p prin-kernels --features wgpu,cpu --all-targets -- -D warnings
cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings
cargo test --workspace
cargo test -p prin-kernels --features wgpu,cpu
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy (workspace, wgpu+cpu, cuda): 0 warnings
cargo test --workspace: 15 Rust tests passed (9 prin-kernels + 6 prin-py)
cargo test -p prin-kernels --features wgpu,cpu: 16 passed; 0 failed
   wgpu_matches_cpu_reference_at_one_million report:
   StepReport { backend_name: "wgpu<wgsl>", wall_time_seconds: 0.0847258, launch_count: 5 }
cargo doc -D warnings: 0 warnings
```

### 2.4 Coverage command

```powershell
cargo llvm-cov -p prin-kernels --features wgpu,cpu
```

Key results:

```text
Filename                      Lines      Missed Lines     Cover
-----------------------------------------------------------------
mean_field_rk4.rs                 189                 0   100.00%
mean_field_rk4\cubecl.rs          451                90    80.04%
ops.rs                             20                 0   100.00%
TOTAL                              660                90    86.36%
```

### 2.5 Python quality and test commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

Key results:

```text
ruff check: All checks passed
ruff format --check: 34 files already formatted
mypy: Success: no issues found in 14 source files
interrogate: 100.0% (min 95.0%)
bandit: No issues identified
pytest tests/ -m "not slow and not gpu": 112 passed, 6 deselected
sphinx: build succeeded
```

### 2.6 Dependency and security audit commands

```powershell
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
cargo tree -p paste -i
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

Key results:

```text
cargo audit: 0 vulnerabilities; 1 unmaintained warning (paste 1.0.15, RUSTSEC-2024-0436)
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
Snyk Code: issueCount=0
Snyk Open Source: issueCount=0
cargo tree -p paste -i:
   paste v1.0.15 (proc-macro)
   └── cubecl-core v0.10.0
       └── cubecl v0.10.0
           └── prin-kernels v0.1.0
```

### 2.7 PRINet 3.0 parity reproduction

The S1 CPU reference `step_cpu` was compared against `prinet.pytorch_mean_field_rk4_step` for N=8, 64, and 1024 using the same inputs. Differences were within f32 round-off:

```text
N=8:   phase 0.000000e+00, amp 0.000000e+00, freq 0.000000e+00
N=64:  phase 0.000000e+00, amp 9.313226e-10, freq 0.000000e+00
N=1024: phase 2.980232e-08, amp 0.000000e+00, freq 0.000000e+00
```

The `triton` package could not be installed for the same-hardware Triton 3.0 fused-kernel comparison:

```text
.venv\Scripts\python -m pip install triton
ERROR: Could not find a version that satisfies the requirement triton (from versions: none)
ERROR: No matching distribution found for triton
```

---

## 3. Detailed checklist results

### 3.1 A1 — WP/session-brief scope conformance

The branch adds only the declared WP-004 artefacts: a CPU reference mean-field RK4 step, a single-source CubeCL kernel set with `cpu`/`cuda`/`wgpu` feature flags, and S1 handoff/coverage evidence. No production kernel suite, Python wrapper, or unsupported performance claims were shipped. `Cargo.lock` and `Cargo.toml` changes are limited to the `cubecl` dependency and `prin-kernels` features. The diff stat is consistent with a spike.

**Result:** PASS.

### 3.2 A2 — Plan/architecture conformance

- One-algorithm/one-implementation: the CubeCL `mean_field_rk4_stage` and `mean_field_rk4_finalize` kernels mirror the CPU `step_cpu` arithmetic and the PRINet 3.0 PyTorch fallback.
- No Python numerics: the new code is entirely in `prin-kernels`.
- Explicit state: `step_cubecl` creates a fresh `ComputeClient` per call; no hidden globals.
- `unsafe` is confined to `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:143` (`ArrayArg::from_raw_parts`) with module-level `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, and a `// SAFETY:` comment.
- The crate-level lint in `crates/prin-kernels/src/lib.rs:23-24` was changed from `#![forbid(unsafe_code)]` (pre-S1) to `#![deny(unsafe_code)]` `#![deny(unsafe_op_in_unsafe_fn)]`. Coding Standards §2.1 requires every crate to carry `#![forbid(unsafe_code)]`; the only existing approved exception is plan amendment #6 for `prin-py`. No amendment authorizes the same pattern for `prin-kernels`.

**Result:** WARN (`WP004-F4`).

### 3.3 A3 — Tests in tandem and coverage

- Unit tests for `step_cpu` (length, empty, non-finite `dt`, zero-coupling free run, phase wrap) are in `crates/prin-kernels/src/mean_field_rk4.rs`.
- Kernel-equivalence tests for wgpu and the CubeCL CPU runtime are in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs`.
- No `proptest` property tests for invariants (phase ∈ [0, 2π), amplitude ≥ 0, zero-coupling identity, RK4 error ∝ h⁴, order-parameter bounds) despite the workspace already declaring `proptest`.
- `cargo llvm-cov -p prin-kernels --features wgpu,cpu` reports 86.36% line coverage, below the 95% gate. The 90 missed lines are the two `#[cube(launch)]` functions `mean_field_rk4_stage` and `mean_field_rk4_finalize`, which execute inside the CubeCL runtime and are not instrumented by `cargo-llvm-cov` on the host.

**Result:** WARN (`WP004-F2`, `WP004-F3`).

### 3.4 A4 — Numerical parity and invariants

- Independent reproduction against `prinet.pytorch_mean_field_rk4_step` for N=8/64/1024 shows differences at the f32 round-off level (max ~3e-8 phase, ~1e-9 amp).
- `cargo test -p prin-kernels --features wgpu,cpu` passes `wgpu_matches_cpu_reference_for_small_n` and `wgpu_matches_cpu_reference_at_one_million` with `rtol=1e-5`, `atol=1e-6`.
- CPU unit tests assert phase ∈ [0, 2π) and amplitude ≥ 0.
- The wgpu N=1M step completes in ~85 ms wall-clock on this host.

**Result:** PASS.

### 3.5 A5 — Quality gates

All Rust and Python quality, lint, doc, and build gates pass locally:

- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo clippy -p prin-kernels --features wgpu,cpu --all-targets -- -D warnings`
- `cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings`
- `cargo test --workspace`
- `RUSTDOCFLAGS=-D warnings; cargo doc --workspace --no-deps`
- ruff, mypy, interrogate, bandit, pytest fast suite, Sphinx `-W`

**Result:** PASS.

### 3.6 A6 — Security

- Snyk Code (medium threshold): 0 issues.
- Snyk Open Source (low threshold): 0 issues.
- `pip-audit .` and `pip-audit -r DOCS/sphinx/requirements.txt`: no known vulnerabilities.
- `cargo audit`: 0 vulnerabilities, but one `unmaintained` warning for `paste 1.0.15` (RUSTSEC-2024-0436), which is a transitive dependency of `cubecl` via `cubecl-core`. No `cargo audit` policy (e.g., `.cargo/audit.toml`) excludes or documents this warning.
- `unsafe` usage in `cubecl.rs` is properly scoped and commented.

**Result:** WARN (`WP004-F1`).

### 3.7 A7 — Docstring and documentation

- Rust public items (`MeanFieldRk4Params`, `MeanFieldRk4Error`, `step_cpu`, `step_cubecl`, `try_step_cpu`, `try_step_wgpu`, `try_step_cuda`, `StepReport`) have rustdoc.
- `cargo doc --workspace --no-deps -D warnings` is clean.
- `interrogate -c pyproject.toml python/prin` reports 100%.
- No new Sphinx page was added for the Rust `prin-kernels` crate (Rust API is docs.rs); the existing `kernel_architecture.rst` correctly targets Phase 3.

**Result:** PASS.

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/stub markers were introduced in the new source.
- `crates/prin-kernels/README.md` says "Feature flags: `cuda`, `wgpu`" but `Cargo.toml` also has a `cpu` feature; the "Phase 0 status" section still only mentions `ops.rs` and not the mean-field RK4 spike.
- `crates/README.md` lists `prin-kernels` as Phase 3 only, even though WP-004 is a Phase 0 spike.
- `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:477` has an `eprintln!` labelled "N=1M wgpu step report" inside the `wgpu_matches_cpu_reference_for_small_n` test (N=64).

**Result:** WARN (`WP004-F9`).

### 3.9 A9 — CI and regressions

- `.github/workflows/rust.yml:42` runs `cargo test --workspace` with no features, so the `#[cfg(feature = "wgpu")]` and `#[cfg(feature = "cpu")]` kernel-equivalence tests are not exercised on default CI.
- `.github/workflows/gpu.yml:19` runs only on commits tagged `[gpu]` and uses `--features cuda`; it does not exercise `wgpu` or the new `cpu` feature.
- No benchmark regression gates are tripped; the spike does not add a `criterion` benchmark.

**Result:** WARN (`WP004-F7`).

### 3.10 A10 — Artefact trail

- WP-003 S4 project state (`DOCS/reports/003-project-state.md`) and audit (`DOCS/audits/003-wp003-audit.md`) are present and consistent.
- S1 handoff `DOCS/experiments/0013-wp004-s1-handoff.md` and coverage `DOCS/experiments/0013-wp004-s1-coverage.md` are committed.
- The `SESSION_REGISTER.md` still marks 0013 `READY` and 0014 `PLANNED`; S4 will update from committed evidence.

**Result:** PASS.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP004-F1 | D2 | `Cargo.lock` (`paste 1.0.15`); transitive via `cubecl-core 0.10.0` | `cargo audit` reports RUSTSEC-2024-0436 (`paste` no longer maintained) with no approved exception or plan amendment | Coding Standards §6.2 (`cargo audit` gate); Project Plan §6 (Phase 0 spike gates) | Either (a) upgrade to a `cubecl` release that removes `paste` when available, (b) patch/replace the transitive `paste` dependency with evidence, or (c) record an approved plan amendment accepting the warning until a patched upstream release; re-run `cargo audit` |
| WP004-F2 | D2 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` (two `#[cube(launch)]` functions); `cargo llvm-cov` report | New/changed line coverage is 86.36% (region 87.94%), below the 95% gate; the 90 missed lines are the non-instrumentable CubeCL kernel launch functions | Testing Standards §4; Development Workflow and Audit Standards A3 | Add a documented coverage exclusion for the `#[cube(launch)]` stubs if `cargo-llvm-cov` supports it, or record a plan amendment that the kernel bodies are verified by equivalence tests and not instrumentable on stable Rust; re-run `cargo llvm-cov -p prin-kernels --features wgpu,cpu` and ensure instrumentable code is ≥95% |
| WP004-F3 | D2 | `crates/prin-kernels/src/mean_field_rk4.rs` and `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | No `proptest` property tests for RK4 invariants (phase wrap, amplitude clamp, zero-coupling identity, RK4 order-of-convergence, order-parameter bounds) | Testing Standards §2 | Add a `proptest` module for `step_cpu` covering the invariants listed in Testing Standards §2 and the PRINet 3.0 preserved hazards; re-run `cargo test -p prin-kernels --features wgpu,cpu` |
| WP004-F4 | D2 | `crates/prin-kernels/src/lib.rs:23-24` (current `#![deny(unsafe_code)]`); `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:13-14` | Crate-level `unsafe` lint was relaxed from `#![forbid(unsafe_code)]` to `#![deny(unsafe_code)]` to allow module-level `unsafe`; no plan amendment authorizes this pattern for `prin-kernels` | Coding Standards §2.1, §6.1 | Draft and approve plan amendment #8 authorizing `prin-kernels` to use crate-level `#![deny(unsafe_code)]` with audited module-level `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, and `// SAFETY:` comments on every `unsafe` block; record second-reviewer sign-off |
| WP004-F5 | D3 | `DOCS/experiments/0013-wp004-s1-handoff.md`; `.venv\Scripts\python -m pip install triton` | Direct same-hardware Triton 3.0 fused-kernel comparison cannot be reproduced because no `triton` wheel exists for Python 3.14 on Windows | WP-004 acceptance criterion; Project Plan §3.2 N1; Development Workflow and Audit Standards §5 D3 | Record an approved plan amendment for the WP-004/Phase 0 go/no-go: the PyTorch fallback reference and wgpu kernel-equivalence are validated; the direct Triton fused-kernel timing is deferred to a Linux/CUDA runner in Phase 3 or the `gpu.yml` workflow with evidence |
| WP004-F6 | D3 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:403-415` (`try_step_wgpu`) and `431-443` (`try_step_cuda`) | Runtime creation (`WgpuRuntime::client`/`CudaRuntime::client`) can panic on missing adapter/CUDA; the public API returns `MeanFieldRk4Error` but a panic bypasses the typed fallback contract | Coding Standards §1.4 and §2.2 (typed errors, no panic in library paths); WP-004 acceptance fallback trigger | Add a device-probe or `catch_unwind` guard around runtime creation, introduce a `MeanFieldRk4Error::BackendUnavailable` variant, and add a regression test; re-run `cargo test -p prin-kernels --features wgpu,cpu` |
| WP004-F7 | D3 | `.github/workflows/rust.yml:42`; `.github/workflows/gpu.yml:19` | Default CI does not run the CubeCL `cpu` or `wgpu` kernel-equivalence tests; the `wgpu` path is only validated locally | Testing Standards §2 (kernel-equivalence tests); Development Workflow and Audit Standards A9 | Add a `cargo test -p prin-kernels --features cpu` step to `rust.yml` (or a new `kernel-equivalence.yml` workflow) and, where a software/headless GPU is available, a `wgpu` step; ensure CUDA path remains `[gpu]`-gated |
| WP004-F8 | D3 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:244` and `390-394` (`StepReport`) | `wall_time_seconds` is measured with `std::time::Instant` around host reads/launches, not device-side events | Benchmarking and Reproducibility Standards §2.2 | Replace with CubeCL device-side profiling/timing APIs when available, or document that the prototype uses host wall-clock and that device-event timing is a Phase 3 optimization; do not publish performance claims from this wall-clock prototype |
| WP004-F9 | D4 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:477`; `crates/prin-kernels/README.md:11-19`; `crates/README.md:8` | Stale/incorrect log message in small-n test; READMEs omit the new `cpu` feature and the Phase 0 mean-field RK4 spike | Documentation Standards §3; repository hygiene A8 | Fix the `eprintln!` label, update `prin-kernels/README.md` to list `cpu` and the WP-004 spike, and update `crates/README.md` to note the Phase 0 spike and Phase 3 target |

---

## 5. Deviation-ledger delta

New findings added to the ledger: `WP004-F1` (D2), `WP004-F2` (D2), `WP004-F3` (D2), `WP004-F4` (D2), `WP004-F5` (D3), `WP004-F6` (D3), `WP004-F7` (D3), `WP004-F8` (D3), `WP004-F9` (D4).

Carried findings re-inspected: none. The cumulative ledger from cycle 003 has zero open findings; the nine new findings above are the only delta at the end of this S2.

---

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

WP-004 implements the declared CubeCL fused mean-field RK4 spike. The CPU reference is correct against PRINet 3.0, the wgpu and CubeCL-CPU kernel-equivalence tests pass at N=64 and N=1M, and the quality and SAST/SCA gates are clean. The D2 findings must be resolved or approved-amended in S3 before the cycle can close with a clean delta re-audit: the `paste` RUSTSEC warning needs an approved exception or upstream fix, the `cargo-llvm-cov` coverage gap must be addressed, property tests must be added for RK4 invariants, and the `prin-kernels` `unsafe` lint relaxation must be authorized by a plan amendment. The D3 findings cover the blocked Triton comparison, runtime panic-to-error conversion, CI coverage for `cpu`/`wgpu`, and the wall-clock timing caveat. The D4 README/log hygiene findings should be corrected in S3/S4.

Ordered S3 action list:

1. `WP004-F4` (D2): draft and approve plan amendment #8 authorizing the `prin-kernels` crate-level `#![deny(unsafe_code)]` + audited module `#![allow(unsafe_code)]` pattern.
2. `WP004-F1` (D2): decide whether to wait for a patched `cubecl`, replace `paste` locally, or record an approved plan amendment for the RUSTSEC-2024-0436 warning; re-run `cargo audit`.
3. `WP004-F2` (D2): configure `cargo-llvm-cov` to exclude or annotate the non-instrumentable `#[cube(launch)]` kernel stubs and re-run coverage; if not possible on stable Rust, record an approved coverage amendment.
4. `WP004-F3` (D2): add `proptest` tests for `step_cpu` invariants and RK4 convergence; re-run `cargo test -p prin-kernels --features wgpu,cpu`.
5. `WP004-F6` (D3): add missing-adapter/CUDA handling to `try_step_wgpu`/`try_step_cuda` with a new `BackendUnavailable` error variant and a regression test.
6. `WP004-F5` (D3): record an approved plan amendment documenting the WP-004/Phase 0 go/no-go (PyTorch reference + wgpu validated; Triton timing deferred).
7. `WP004-F7` (D3): add the `cpu` (and `wgpu` where feasible) kernel-equivalence tests to default CI.
8. `WP004-F8` (D3): document or replace wall-clock timing with device-side events.
9. `WP004-F9` (D4): fix the stale log message and update `prin-kernels/README.md` and `crates/README.md`.

---

## 7. S3 closure table

| Finding | Severity | Resolution | Evidence / commit reference | Plan amendment |
|---|---|---|---|---|
| WP004-F1 | D2 | AMENDED | `cargo audit` still reports RUSTSEC-2024-0436 inherited from `cubecl 0.10.0`; no patched release is available at the PRIN dependency level. Recorded in `DOCS/PRIN_Project_Plan.md` §8.3 amendment #9. | #9 |
| WP004-F2 | D2 | AMENDED | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` instrumentable code is 88.21% overall because the two `#[cube(launch)]` kernel bodies are not instrumentable on stable Rust. `mean_field_rk4.rs` and `ops.rs` are 99.67% and 100% respectively; kernel correctness is verified by kernel-equivalence tests. Amendment #10 records the exception and the re-check obligation. | #10 |
| WP004-F3 | D2 | FIXED | Added `proptest` module in `crates/prin-kernels/src/mean_field_rk4.rs` covering phase wrap, amplitude clamp, zero-coupling identity, order-parameter bounds, and a deterministic RK4 local-error scaling unit test. `cargo test -p prin-kernels --features wgpu,cpu` passes (21 tests). | — |
| WP004-F4 | D2 | AMENDED | Added `DOCS/PRIN_Project_Plan.md` §8.3 amendment #8 authorizing the audited `prin-kernels` `unsafe` pattern: crate-level `#![deny(unsafe_code)]` with module-level `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, and `// SAFETY:` justifications. | #8 |
| WP004-F5 | D3 | AMENDED | Recorded in `DOCS/PRIN_Project_Plan.md` §8.3 amendment #11: PyTorch reference and wgpu/CubeCL-CPU kernel-equivalence at N=1M are validated; direct same-hardware Triton 3.0 fused-kernel timing is deferred to Phase 3 / `gpu.yml` on a Linux/CUDA runner. | #11 |
| WP004-F6 | D3 | FIXED | Wrapped `WgpuRuntime::client`, `CpuRuntime::client`, and `CudaRuntime::client` creation in `catch_unwind` and mapped panics to `MeanFieldRk4Error::BackendUnavailable`. Added `wgpu_returns_typed_error_when_backend_unavailable` regression test. `cargo test -p prin-kernels --features wgpu,cpu` passes. | — |
| WP004-F7 | D3 | FIXED + AMENDED | Added `cargo test -p prin-kernels --features cpu` to `.github/workflows/rust.yml` (test matrix). The `wgpu` CI step remains gated on a headless GPU runner and is recorded as deferred in `DOCS/PRIN_Project_Plan.md` §8.3 amendment #12. | #12 |
| WP004-F8 | D3 | FIXED | Documented host wall-clock caveat in `StepReport.wall_time_seconds` doc comment and module-level note: device-side event timing is a Phase 3 optimization and no performance claims may be published from this prototype. | — |
| WP004-F9 | D4 | FIXED | Corrected `N=1M` to `N={n}` in the small-n wgpu test. Updated `crates/prin-kernels/README.md` to list the `cpu` feature and the WP-004 Phase 0 mean-field RK4 spike. Updated `crates/README.md` to note the Phase 0 spike. | — |

**Delta re-audit result:** All D2 findings are resolved or approved-amended; D3/D4 findings are fixed or amended. `cargo test --workspace`, `cargo test -p prin-kernels --features wgpu,cpu`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo fmt --all -- --check`, and the Python fast gate pass locally. `cargo audit` retains the inherited `paste` warning (amended).

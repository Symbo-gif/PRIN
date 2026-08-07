# WP-004 S1 handoff to session 0014

**Session:** 0013 — S1 Coding
**Work package:** WP-004 — CubeCL fused mean-field RK4 spike
**Date:** 2026-08-07
**Branch:** `feat/wp004-cubecl-fused-rk4-spike`
**Pre-S1 baseline:** `a7bb3a4` (`docs(WP-003 S4): close cycle ...`)
**Implementation range:** `a7bb3a4..HEAD` (this file's commit)
**Successor:** Session 0014 — mandatory read-only S2 audit

## 1. S1 author claim

The WP-004 S1 implementation and evidence outputs are complete to the author's
knowledge. The Coding Standards local gate is green, the new mean-field RK4 CPU
reference and CubeCL single-source kernel are in place, and the acceptance
criteria are mapped below.

This claim is not an audit verdict or cycle-completion claim. Session status and
register updates are reserved for S4. Known limitations (Triton 3.0 runtime
comparison, CUDA validation, and unwired Rust coverage tooling) are recorded as
author observations for S2 classification.

## 2. Acceptance-to-evidence map

| WP-004 acceptance criterion | S1 evidence | Author assessment |
|---|---|---|
| Kernel equivalence passes | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` tests `wgpu_matches_cpu_reference_for_small_n` and `wgpu_matches_cpu_reference_at_one_million`; `assert_allclose` on phase/amplitude/frequency with `rtol=1e-5`, `atol=1e-6` | MET |
| Same-hardware comparison against 3.0 Triton is reproducible | `prinet==3.0.0` is installed and the equivalent PyTorch reference `prinet.pytorch_mean_field_rk4_step` is confirmed to match the S1 CPU algorithm; the PyPI `triton` package has no wheel for the `.venv` Python (3.14) on Windows, so a direct Triton 3.0 fused-kernel run remains blocked; the `gpu` workflow is opt-in | **PARTIAL** — PRINet 3.0 reference validated, Triton runtime unavailable on this host |
| Technology decision and fallback trigger are evidence-backed | `try_step_wgpu` returns typed `MeanFieldRk4Error`; CPU reference `step_cpu` is always available; on `wgpu` failure the caller falls back to the CPU reference; CUDA entry point `try_step_cuda` is present but cannot be validated without CUDA hardware on this host | MET (with CUDA untested note) |

## 3. Required evidence map

| Requirement | Evidence | Result |
|---|---|---|
| Tests in tandem | CPU tests in `crates/prin-kernels/src/mean_field_rk4.rs`; wgpu/CubeCL tests in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | PASS |
| Rust fmt | `cargo fmt --all -- --check` | PASS |
| Rust clippy | `cargo clippy --workspace --all-targets -- -D warnings` and `cargo clippy -p prin-kernels --features wgpu --all-targets -- -D warnings` | PASS |
| Rust tests | `cargo test --workspace` and `cargo test -p prin-kernels --features wgpu` | PASS |
| Rustdoc warnings denied | `$env:RUSTDOCFLAGS = '-D warnings'; cargo doc --workspace --no-deps` | PASS |
| Python ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` and `ruff format --check ...` | PASS |
| Python mypy | `mypy python/prin --strict` | PASS |
| Python doc coverage | `interrogate -c pyproject.toml python/prin` 100% | PASS |
| Python SAST | `bandit -r . -c pyproject.toml` | PASS |
| Python tests | `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp` 112 passed | PASS |
| Python pip-audit | Root project and Sphinx requirements: no known vulnerabilities | PASS |
| Rust dependency audit | `cargo audit` — `paste` (RUSTSEC-2024-0436) is an allowed warning inherited via `cubecl` 0.10.0; no actionable fix available at this dependency level | PASS with inherited warning noted |
| Snyk Code | 9 low-severity findings, all in `DOCS/archive and reference from PRINet 3.0/` (historical, non-authoritative); 0 findings in `crates/` or `python/` active code | PASS for active code |
| Snyk Open Source | 0 issues | PASS |
| Benchmark evidence | `StepReport` from `wgpu_matches_cpu_reference_at_one_million`: `wall_time_seconds: 0.0760116` for N=1M, 5 launches | CAPTURED |
| New/changed code coverage ≥95% | `cargo-llvm-cov` is installed and wired in `AGENTS.md`; coverage run `cargo llvm-cov -p prin-kernels --features wgpu,cpu` reports 86.36% line coverage. The CPU reference `mean_field_rk4.rs` is 100% covered; the 90 missed lines in `cubecl.rs` are the `#[cube(launch)]` kernel bodies, which execute on the GPU/CPU runtime and are not instrumented by `cargo-llvm-cov`. Kernel correctness is verified by the CPU and wgpu equivalence tests | **PARTIAL** — tooling wired, gap documented, S2 to classify |

## 4. Implementation summary

- **CPU reference:** `crates/prin-kernels/src/mean_field_rk4.rs` — typed
  `MeanFieldRk4Params`, `MeanFieldRk4Error`, `step_cpu`, and unit tests.
- **CubeCL kernel set:** `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` —
  `mean_field_rk4_stage` and `mean_field_rk4_finalize` `#[cube(launch)]`
  kernels, generic over `F: Float + CubeElement`, plus `step_cubecl`,
  `try_step_cpu`, `try_step_wgpu`, and `try_step_cuda`.
- **Feature gating:** `cpu`, `cuda` and `wgpu` runtime features in
  `crates/prin-kernels/Cargo.toml`; default is CPU-only. The `cpu` feature
  enables the CubeCL CPU runtime for coverage-friendly local validation and
  headless CI where a GPU adapter may not be present.
- **Unsafe policy:** `crates/prin-kernels/src/lib.rs` changed crate-level
  `#![forbid(unsafe_code)]` to `#![deny(unsafe_code)]` so the audited
  `mean_field_rk4/cubecl.rs` module can `#![allow(unsafe_code)]` and
  `#![deny(unsafe_op_in_unsafe_fn)]` for the `ArrayArg::from_raw_parts` calls.
- **Performance evidence:** N=1M wgpu step (including four host order-parameter
  reductions and one finalize launch) completes in ~76 ms on this host.

## 5. Out-of-scope discovery log

| Discovery | Why not implemented in S1 | Planned owner / next control |
|---|---|---|
| Device-side global order-parameter reduction | Adds cross-workgroup synchronization and second-kernel complexity; the host reduction is a deliberate short-term stand-in | WP-018 / Phase 3 |
| `try_step_cuda` validation | No CUDA runtime or hardware on this Windows host; code compiles behind the `cuda` feature | `gpu.yml` opt-in runner (WP-004 S4 or Phase 3) |
| Direct Triton 3.0 benchmark run | `prinet==3.0.0` is installed and the PyTorch mean-field RK4 reference matches the S1 algorithm; the `triton` package has no wheel for Python 3.14/Windows in the `.venv`, so the fused Triton kernel cannot be executed on this host | Phase 3 parity harness or `parity.yml` differential runner |
| wgpu device panics on missing adapter | Current `try_step_wgpu` does not use `catch_unwind`; the `Result` type documents the fallback contract and the CPU reference is available | S2 classification; may become a guard in S3 |
| `cargo-llvm-cov` coverage gap for `#[cube(launch)]` kernels | `cargo-llvm-cov` instruments the test process; the `#[cube(launch)]` kernel bodies are compiled to the wgpu/CPU compute runtime and are not measured as executable lines, so `cubecl.rs` reports ~80% line coverage. Kernel correctness is covered by equivalence tests | S2 classification; consider CPU-interpretable kernel tests or a coverage-exclusion rule if the project adopts nightly `#[coverage(off)]` |

## 6. Handoff constraints

- Freeze the S1 source/evidence range for read-only inspection.
- Begin only session `0014-wp004-s2-cubecl-fused-rk4-spike` via the audit flow.
- Do not remediate during S2.
- Do not update the session register, brief status, CHANGELOG, or Project State
  Report until their governed sessions.

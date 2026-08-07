# Changelog

All notable changes to PRIN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository scaffold: Cargo workspace (8 crates), Python package layer,
  parity/benchmark/test/docs directories, CI workflow skeletons, and governance
  documents (`DOCS/`), per the official project plan
  (`DOCS/PRIN_Project_Plan.md`).
- Self-auditing execution methodology (plan amendment #1): Development Workflow
  and Audit Standards (Session Cycle S1 code → S2 audit → S3 remediate →
  S4 document, deviation ledger), Experimentation Standards (mandatory
  pre-registration with expected results and failure conditions, Phase 7
  campaign), artefact directories with templates (`DOCS/audits/`,
  `DOCS/reports/`, `DOCS/experiments/`), and operational session workflows
  (`.windsurf/workflows/`).
- Tightened quality gates: docstring coverage (ruff pydocstyle `D`/Google +
  `interrogate --fail-under 95`, rustdoc `-D warnings` CI job), Python SAST
  (`bandit`), and a dedicated security standard (Coding Standards §6).
- Complete prospective Session Execution Plan (`DOCS/sessions/`): 198
  individually addressable session briefs spanning 39 governed work packages,
  eight E1–E5 pre-registered experiments, campaign planning/synthesis, and
  stable-release closure; includes a master status register, requirement/risk/
  DoD traceability matrix, phase indexes, and conditional D1/D2 correction
  templates (plan amendment #2).
- WP-001 foundation baseline automation: deterministic repository inventory,
  complete ownership traceability for 43 PRINet 3.0 modules and 657 public-symbol
  rows (172 canonical top-level exports), fail-closed metadata/session validation,
  44 focused tests, and cycle audit/state evidence.
- Additive Snyk Code/Open Source and full-history Gitleaks CI, with matching
  repository-agent/editor secure-development guidance.
- WP-002 golden-trajectory corpus and differential harness: 504 seeded
  float64 cases covering every model (kuramoto, hopf, stuart_landau) ×
  coupling (full, mean_field, sparse_knn) × basic integrator (euler, rk4),
  versioned `CorpusManifest` with SHA-256 per-case digests, schema/manifest
  validators, `CorpusLoader`, differential pytest harness, and Hypothesis
  strategies in `python/prin/parity/` and `parity/`.
- WP-003 PyO3/DLPack bridge spike: zero-copy Torch↔Rust tensor exchange via
  `prin.dlpack` (`negate`, `negate_batched`, `round_trip`) backed by the
  `prin._prin_core` extension (`dlpack_negate`, `dlpack_negate_batched`,
  `dlpack_round_trip`); CPU round-trip, batched boundary calls, dtype/device
  validation, ownership/lifetime handling, and `pytest-benchmark` latency
  instrumentation in `tests/test_dlpack_bridge.py`; representative element-wise
  CPU kernels (`negate_f32`, `negate_f64`) in `prin-kernels::ops`.
- WP-004 CubeCL fused mean-field RK4 spike in `prin-kernels::mean_field_rk4`:
  CPU reference `step_cpu`, single-source CubeCL kernels for `cpu`/`wgpu`/`cuda`
  runtimes via `try_step_cpu`, `try_step_wgpu`, and `try_step_cuda`, typed
  `MeanFieldRk4Error` (including `BackendUnavailable`), `StepReport` with host
  wall-clock timing, and kernel-equivalence tests at N=64 and N=1M against the
  CPU reference; `proptest` coverage for phase wrap, amplitude clamp,
  zero-coupling identity, RK4 local-error scaling, and order-parameter bounds.

### Changed

- Repository-native plans, standards, code, configuration, Audit Reports, and
  Project State Reports replace retired VibeCheck state as current authority
  (plan amendments #3 and #4).
- Native GitHub secret scanning remains mandatory when available; while GitHub
  reports it unavailable for this private repository, amendment #5 requires a
  protected PR-only `main` and blocking full-history Gitleaks on every change.
- `pyproject.toml` and `.github/workflows/parity.yml` updated to install
  PRINet 3.0.0 from the archived source tree, add the `parity` optional-dependency
  group, and exclude `parity/` and the archive from `bandit` scans.
- `DOCS/sphinx/requirements.txt` now pins patched transitive minimums so that
  `pip-audit` and Snyk Open Source both report zero findings.
- Coding Standards §2.1 and §6.1 amended (plan amendment #6) to permit an
  audited Python-FFI `unsafe` module in `prin-py/src/dlpack.rs` under the same
  controls as kernel-FFI modules: dedicated module,
  `#![deny(unsafe_op_in_unsafe_fn)]`, `// SAFETY:` comments on every `unsafe`
  block, and second-reviewer sign-off. `prin-py` uses crate-level
  `#![deny(unsafe_code)]` with module-level `#![allow(unsafe_code)]` because
  `#![forbid]` cannot be scoped to a single module.
- Project Plan §6 amended (plan amendment #7) documenting the WP-003/Phase 0
  go/no-go: the CPU DLPack exchange and `pytest-benchmark` round-trip/batched
  evidence are validated; the CUDA round-trip and the `<5%` training-step
  overhead target are deferred to the Phase 4 trainable-stack work with a
  re-audit gate.
- Coding Standards §2.1/§6.1 amended (plan amendment #8) to authorize the same
  audited kernel-FFI `unsafe` pattern for `prin-kernels` already used for
  `prin-py`: crate-level `#![deny(unsafe_code)]` with module-level
  `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, and `// SAFETY:`
  justifications.
- Project Plan §6 / Coding Standards §6.2 amended (plan amendment #9) to accept
  the inherited `paste` RUSTSEC-2024-0436 warning via `cubecl` 0.10.0 while
  rechecking every cycle and upgrading when a patched release is available.
- Testing Standards §4 amended (plan amendment #10) documenting that
  `#[cube(launch)]` kernel bodies are not instrumentable by `cargo-llvm-cov` on
  stable Rust; kernel correctness is verified by kernel-equivalence tests and
  the instrumented surrounding code stays at ≥95% line coverage.
- Project Plan §3.2 N1 / WP-004 acceptance criterion amended (plan amendment
  #11): the PRINet 3.0 PyTorch reference and wgpu/CubeCL-CPU kernel-equivalence
  at N=1M are validated; the direct same-hardware Triton 3.0 fused-kernel timing
  is deferred to Phase 3 / the `gpu.yml` workflow.
- Testing Standards §2 / Development Workflow and Audit Standards A9 amended
  (plan amendment #12): added `cargo test -p prin-kernels --features cpu` to the
  default `rust.yml` matrix; the `wgpu` step stays in the opt-in `gpu.yml` /
  local validation path until a headless GPU runner is available.
- `rust-toolchain.toml` now includes `llvm-tools` so `cargo-llvm-cov` can measure
  `prin-kernels` coverage.
- `.github/workflows/rust.yml` now runs the CubeCL CPU kernel-equivalence tests
  (`cargo test -p prin-kernels --features cpu`) on every platform.

### Security

- Upgraded PyO3 and rust-numpy to 0.29.0, removing the audited RustSec advisory
  chain, and aligned the workspace MSRV to Rust 1.83.
- Enforced project/docs Pip Audit and Snyk dependency gates, removed long-lived
  crates.io token use, protected `main`, and added an approved single-fingerprint
  exception for an archived SHA-256 checksum misclassified as an API key.
- WP-003 S3: added `BridgeError::NegativeDim` and `validate_shape` to the
  DLPack bridge so `read_and_negate`/`read_and_clone` reject negative shape
  dimensions before `element_count` and `std::slice::from_raw_parts`, closing
  the over-read path from a malformed capsule (audit finding WP003-F2).

### Fixed

- Parity CI workflow: added empty-corpus guard so the job is skipped until
  `parity/` cases exist (pre-WP-001 fix).
- `Cargo.lock`: now tracked for reproducible CI dependency resolution
  (pre-WP-001 fix).
- Python test scaffold: added a minimal collection smoke test so an empty suite
  does not fail the `pytest` gate with exit code 5 (pre-WP-001 fix).
- Scaffold gate pass: confirmed all quality gates green at `v0.1.0` scaffold
  state (pre-WP-001 fix).

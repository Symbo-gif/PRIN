# Changelog

All notable changes to PRIN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Executive Audit Governance and Session 001 (EA-001)**:
  - Normative governance and methodology document `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` establishing project-level multi-domain audit criteria (E1–E10), deviation severities (D1–D4), remediation protocols, and reporting requirements.
  - Executive Audit Report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md` evaluating mathematics, architecture, test/parity suite, security, docs, evidence, governance, performance, CI/CD, and roadmap (`PASS-WITH-REMEDIATION`).
  - Operational workflow recipes `workflows/executive-audit.md` and `.windsurf/workflows/executive-audit.md`.
  - Executive audit report template `DOCS/audits/TEMPLATE_Executive_Audit_Report.md`.
  - Subpackage README index files added in `python/prin/eval/README.md`, `python/prin/experiments/README.md`, `python/prin/nn/README.md`, `python/prin/reporting/README.md`.
- WP-006 Oscillator state, errors, and deterministic seed in `prin-dynamics`:
  - Struct-of-arrays `OscillatorState` (`phase`, `amplitude`, `frequency`, optional `freq_band`) with `new`, `create_random`, `create_synchronized`, `n_oscillators`, and `n_bands`.
  - Counter-based deterministic `Seed` authority on `rand_pcg::Pcg64` with `(counter, key)` stream identity, `jump`, bounded `next_f64_range`, `RngCore` integration, and serde round-trip.
  - Phase and amplitude numerical guards: `% 2π` phase wrap (`wrap_phase`, `wrap_phases`), `atan2`-safe phase differences (`safe_phase_diff`, `safe_phase_diffs`), amplitude clamps `[1e-6, 10]` (`clamp_amplitude`, `guard_amplitude`), derivative clamps `±1e4` (`clamp_derivative`, `guard_derivative`), and sort-based phase k-NN index (`build_phase_knn_index`).
  - Typed error enumerations `StateError` and `SeedError` built with `thiserror`.
  - Opt-in `strict-checks` feature flag for strict guard validation versus default clamping/repair.
- WP-007 Oscillator dynamics models in `prin-dynamics`:
  - `Dynamics` trait with `compute_derivatives(&self, &OscillatorState) -> Result<StateDerivatives, StateError>` as the uniform interface for all oscillator models.
  - `KuramotoOscillator` — extended Kuramoto with amplitude decay and frequency adaptation; mean-field `O(N)` (complex order parameter `Z = R e^{iψ}`), full pairwise `O(N²)` (custom `N×N` matrix or uniform `K/N` with zero diagonal), and sparse k-NN `O(N·k)` coupling.
  - `StuartLandauOscillator` — complex-amplitude Hopf normal form with mean-field, full, and sparse k-NN coupling.
  - `HopfOscillator` — supercritical Hopf bifurcation in polar coordinates with `limit_cycle_amplitude = sqrt(μ)`; mean-field, full, and sparse k-NN coupling.
  - `CouplingMode` enum (`MeanField`, `Full { matrix }`, `SparseKnn { k }`) with enum-dispatched coupling semantics (no string dispatch); `Default` is `Full { matrix: None }`.
  - `StateDerivatives` struct-of-arrays (`dphase`, `damplitude`, `dfrequency`) with length validation and derivative guards honoring `strict-checks`.
  - Rust-vs-PRINet 3.0 derivative parity tests in `crates/prin-dynamics/tests/parity_models.rs` covering all three models and all coupling modes (`1e-12` for pure float64 paths, `1e-6` for f32-complex-affected paths).
- WP-008 Basic integrators in `prin-dynamics`:
  - `Integrator` trait (`step(&mut self, model, state, dt) -> Result<OscillatorState, IntegrateError>`) as the uniform interface for time integrators of oscillator dynamics.
  - `EulerIntegrator` — first-order explicit Euler with reusable derivative buffer.
  - `RK4Integrator` — classic fourth-order Runge–Kutta (order `h^4`) with explicit `k1`–`k4` reusable buffers.
  - `RK45Integrator` — adaptive Dormand–Prince RK45 with FSAL (First Same As Last) caching, PI step-size control (`clamp(SAFETY · err_norm^(-1/5), MIN_FACTOR, MAX_FACTOR)`), typed tolerance/step-budget errors, and `fsal_valid` invalidation on reuse/rejected steps.
  - `AdaptiveResult` struct (`final_state`, `accepted_steps`, `rejected_steps`, `final_dt`) returned by `RK45Integrator::integrate_adaptive`.
  - `integrate_fixed` free function for multi-step fixed-step integration with any `Integrator`.
  - `IntegrateError` enum with seven typed variants: `InvalidTimestep`, `InvalidTolerance`, `ZeroSteps`, `Dynamics`, `ToleranceNotMet`, `StepSizeUnderflow`, `NonFiniteValue` (the latter under `strict-checks`).
  - Rust-vs-PRINet 3.0 trajectory parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` (16 golden-trajectory cases) comparing Euler and RK4 against `torch.float64` reference values at `rtol=1e-6, atol=1e-8` (and tighter for pure f64 paths); RK4 order-`h^4` convergence and RK45 tolerance-property parity tests.
- WP-010 Phase metrics and chimera measures in `prin-metrics`:
  - `kuramoto_order_parameter`, `kuramoto_order_parameter_complex`, `inter_frame_phase_correlation`, `order_parameter_series` — order parameters in f64 matching PRINet 3.0 `torch.float64` reference paths.
  - `mean_phase_coherence`, `phase_coherence_matrix`, `sparse_mean_phase_coherence` — full and sparse k-NN phase coherence.
  - `power_spectral_density`, `extract_concept_probabilities` — rustfft-backed PSD and concept-probability extraction.
  - `synchronization_energy`, `sparse_synchronization_energy` — dense and sparse synchronization energy.
  - `local_order_parameter`, `bimodality_index`, `strength_of_incoherence`, `discontinuity_measure`, `chimera_index`, `strength_of_incoherence_temporal`, `BIMODALITY_CHIMERA_THRESHOLD`, `DEFAULT_CHIMERA_THRESHOLD` — full chimera metric set.
  - `metastability` — temporal standard deviation of the order parameter (PRIN extension, no PRINet analogue).
  - `build_phase_knn` — measurement-facing k-NN wrapper delegating to `prin-dynamics` (one algorithm, one implementation).
  - `MetricError` typed error enum (9 variants) with boundary validation on all public metrics.
  - `rustfft = "6.2"` (resolved 6.4.1) added to `[workspace.dependencies]` for PSD (pure-Rust, no advisories).
  - 145 new tests (104 unit/property + 22 parity/corpus + 19 doctests); coverage lines 99.53%, regions 96.28%, functions 100%.
  - Rust-vs-PRINet 3.0 parity at `rtol=1e-10` (f64 paths, measured ≤ 8.58e-16), `rtol=1e-8` (corpus, amendment #16), and `1e-6` (PSD/chimera f32-hazard paths, amendment #14).
- WP-009 PAC, coupling topologies, and phase k-NN in `prin-dynamics`:
  - `PhaseAmplitudeCoupling` struct implementing cross-frequency phase–amplitude coupling `A_fast = A₀·[1 + m·cos(φ_slow + offset)]` with mean slow-band phase, broadcast modulation, and amplitude clamp `[AMPLITUDE_MIN, AMPLITUDE_MAX]`; `new` / `with_clamp` constructors validate modulation depth `m ∈ [0, 1]` and clamp range finiteness/ordering.
  - `PacError` typed error enum with five variants: `InvalidModulationDepth`, `EmptyInput`, `NonFiniteValue`, `InvalidPhaseOffset`, `InvalidClampRange`.
  - `Topology` enum (`AllToAll`, `Ring { k_ring }`, `SmallWorld { k_ring, rewire_prob, seed }`) with `build_matrix` builders that produce `N × N` coupling matrices with `K / degree` per-edge normalization; `SmallWorld` is a directed Watts–Strogatz rewiring variant (outgoing edges only, deterministic `Seed`).
  - `CouplingError` typed error enum and `validate_coupling_matrix` helper for matrix length/finiteness validation.
  - `k_ring` clamped to the largest even number `≤ N - 1` in `Ring` and `SmallWorld` builders to preserve the `K / degree` energy invariant (total coupling energy per oscillator = `K`).
  - Explicit 1/N versus 1/k normalization tests (`sparse_knn_k_equals_n_minus_1_equals_full_default`, `normalization_one_over_n_explicit_in_mean_field`, `normalization_one_over_k_explicit_in_sparse`), sparse/full equivalence, and k-NN edge-property tests (5 edge-property tests + 1 proptest + topology equivalence).
  - Rust-vs-PRINet 3.0 PAC parity tests in `crates/prin-dynamics/tests/parity_pac.rs` (9 golden cases) comparing `PhaseAmplitudeCoupling::modulate` against hard-coded PRINet 3.0 reference values at `epsilon = 1e-6` (amendment #14 f32-truncation tolerance).

### Changed

- `[RETROACTIVE UPDATE - Executive Audit 002]` Correction of the two
  CHANGELOG lines below as originally drafted for EA-001: the claimed update
  registering Global Session 0025 as `EA-001 Executive Audit Session 001` in
  `DOCS/sessions/SESSION_REGISTER.md` / `TRACEABILITY.md` and advancing
  WP-007 S1 to Session 0026 was **never committed** (EA-001 commit `d1e6e0a`
  touched no session files; the register numbers WP-007 S1 as 0025). EA-002
  (finding E-F2, plan amendment #15) remediated this by registering EA-001
  and EA-002 in a dedicated "Global sessions — Executive Audits" section of
  `SESSION_REGISTER.md` outside the planned 0001–0198 sequence, and by
  appending a tagged correction appendix to
  `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md`.
- **Executive Audit Session 002 (EA-002)**:
  - Executive Audit Report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_002.md` covering Sessions 0025–0036 (WP-007..WP-009) plus full-project re-verification across E1–E10 (`PASS-WITH-REMEDIATION`, findings E-F1–E-F13).
  - Fixed `tests/test_phase0_gate.py::test_phase0_gate_integration_with_ort` to write refreshed ORT evidence to `tmp_path` instead of overwriting the committed `EVIDENCE/0017-wp005-s1-ort-probe.json` on every full test run (E-F1; root cause of the WP007-F4 drift).
  - Corrected `.snyk` archive exclude pattern to `DOCS/archive and reference from PRINet 3.0/**` (E-F3) and recorded the maintainer-approved acceptance of three low Snyk Code findings in `tools/wp001_baseline.py` with expiry 2026-11-06 (E-F4).
  - Registered EA-001/EA-002 as global sessions in `SESSION_REGISTER.md` (plan amendment #15) and appended a tagged correction appendix to the EA-001 report (E-F2).
  - Recorded maintainer approval for plan amendment #14, Project State Report 009, and the WP-010 declaration (E-F6).
  - Documentation accuracy fixes: `prin-dynamics` crate docs (E-F7), RK4 rustdoc typo (E-F8), `SmallWorld` rewiring docs (E-F9), `DOCS/experiments/README.md` and `DOCS/audits/README.md` indexes (E-F10, E-F11), parameterized executive-audit workflow recipes (E-F12), and Windows pytest concurrency guidance in `AGENTS.md` (E-F13).
- Project Plan §5 amended (plan amendment #14): documented PRINet 3.0's `torch.complex64` (f32) internal arithmetic for mean-field order parameters and Stuart–Landau complex amplitudes as a preserved numerical hazard with a `1e-6` derivative-level parity tolerance for affected model/coupling paths.

### Security

- (nothing yet)

### Fixed

- PR #6 CI remediation (first full execution of the pull-request gates, which had never run on the feature branch):
  - `python.yml` lint job now installs `hypothesis` so `mypy --strict` type-checks `prin.parity.strategies` against the real `st.composite` types; without it, CI saw an untyped decorator (`untyped-decorator` at `strategies.py:107`) while local venv runs always had hypothesis present.
  - `test_npu` in `tests/test_ort_backends.py` now uses `tmp_path` for the ORT cache directory instead of a hardcoded `/fake/cache` path that cannot be created at the filesystem root on Linux runners (`PermissionError`); the ubuntu test-matrix failures are fixed without changing Windows/macOS behavior.
  - `parity.yml` now creates an explicit virtual environment before `maturin develop` (mirroring `python.yml`); the job had been skipped by the corpus guard until PR #6, and its first real run failed because `maturin develop` requires a venv.
  - `parity.yml` runs the suite via `python -m pytest` instead of the bare `pytest` console script: `parity/` is not an installed package (no `__init__.py`), and only `python -m pytest` places the repository root on `sys.path`, which `from parity.generate_corpus import _run_case` requires. Reproduced and verified locally (bare `pytest parity/` fails with `ModuleNotFoundError: parity`; `python -m pytest parity/` passes 6/6).
- Project Plan §5 / Testing Standards §3 amended (plan amendment #16, maintainer-approved in EA-002): corpus differential-harness METRIC tolerance raised from `rtol=1e-10` to `rtol=1e-8` for cross-platform corpus-regeneration comparisons. PR #6's first ubuntu parity run measured PRINet 3.0 torch CPU reduction noise up to ~1.27e-9 relative on the derived metric arrays (`order_parameter_traj`, `mean_phase_coherence_traj`) between the Windows-authored corpus and Linux regeneration; trajectories passed at the unchanged `rtol=1e-6, atol=1e-8`. Single-runtime metric verification (WP-010/WP-014) still targets `rtol=1e-10`; corpus immutable; Parity Report EA-002 register entry documents the hazard.
- WP-008 S3 remediation (audit findings WP008-F1–F5, commit `f97ba5c`):
  - WP008-F1: Fixed FSAL cache invalidation in `RK45Integrator::integrate_adaptive` — added `fsal_valid: bool` flag invalidated at the start of each call and on rejected steps; regression test `rk45_fsal_cache_invalidated_on_reuse` asserts bit-identical results for reused vs fresh integrators.
  - WP008-F2: Added `NonFiniteValue` error-path test coverage under `strict-checks` (Euler and RK4) via a `NanDynamics` test helper; `integrate.rs` line coverage rose from 96.66% to 97.48%.
  - WP008-F3: Corrected `check_finite` doc comment to accurately describe non-strict behavior (amplitude repaired via `clamp_amplitude`; non-finite phase/frequency pass through silently and are only caught under `strict-checks`).
  - WP008-F4: Updated `lib.rs` `integrate` module doc to list only implemented integrators (Euler, RK4, adaptive RK45/Dormand–Prince); removed stale "exponential (direct + Krylov), and multi-rate sub-stepped RK4" text from the pre-S1 stub.
  - WP008-F5: Added `IntegrateError::InvalidTolerance { param, value }` variant; `RK45Integrator::new` now returns `InvalidTolerance` instead of reusing `InvalidTimestep` for tolerance validation; updated `rk45_rejects_invalid_tolerances` to assert the specific variant.
- WP-009 S3 remediation (audit findings WP009-F1–F7, commits `b4749ba`, `bf46cee`):
  - WP009-F1: Fixed `cargo fmt` failure on `coupling.rs` test comment indentation by restructuring the `topology_ring_basic` trailing comment.
  - WP009-F2: Strengthened `normalization_one_over_k_explicit_in_sparse` to assert the explicit `K/k` per-edge weight against the actual k-NN neighbour set (distinguishing 1/k from 1/N via a 1/N divergence check) plus a shared-neighbour `K/2` vs `K/3` = 3/2 ratio check, replacing the prior `is_finite()`-only assertions.
  - WP009-F3: Fixed `build_ring`/`build_small_world` odd-clamp normalization by clamping `k_ring` to the largest even number `≤ n-1` (new `clamp_ring_k` helper) so per-node degree == `k_ring` and the `K/degree`-per-edge energy invariant (total == `K`) holds; added regression tests for both builders.
  - WP009-F4: Added `amp_min`/`amp_max` finiteness and `amp_min <= amp_max` validation to `PhaseAmplitudeCoupling::with_clamp` via a new `PacError::InvalidClampRange` variant (prevents `f64::clamp` panic on inverted range); added inverted/non-finite/equal-bound regression tests.
  - WP009-F5: Corrected S1 handoff note factual errors (`pac.rs` expanded from stub, k-NN uses rayon `par_sort_by`, test count 198).
  - WP009-F6: Corrected `topology_ring_clamps_k_to_n_minus_1` test comment and added exact degree + per-edge weight + total-energy assertions.
  - WP009-F7: Documented the directed-rewiring interpretation of `build_small_world` in the module rustdoc and `Topology::SmallWorld` variant doc (outgoing-edge rewiring preserves out-degree and total edge count but not symmetry).

## [0.1.0-alpha.1] - 2026-08-07

Phase 0 (Foundation) pre-release. All three foundation spikes (DLPack,
CubeCL, ORT) meet their go/no-go criteria with approved amendments. The
golden-trajectory corpus (504 cases) is committed. The three-OS abi3 wheel
matrix is configured. See `DOCS/reports/005-project-state.md` for the
Phase 0 exit-gate verdict.

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
- WP-005 ONNX Runtime provider probe (`prin._ort`): detects available execution
  providers (VitisAI → DirectML → CPU priority), builds the provider list with
  VitisAI firmware/xclbin resolution, creates sessions with graceful CPU
  fallback when an accelerator cannot execute the graph, and proves the
  pre-trained subconscious controller loads and runs with output shape `(1, 8)`.
  Includes `OrtProbeReport`, `select_best_backend`, `build_provider_list`,
  `try_create_session`, `probe_model`, and `available_providers`.
- WP-005 Phase 0 exit-gate consolidation (`prin._phase0`): validates the three
  foundation spikes (DLPack, CubeCL, ORT), the 504-case golden-trajectory
  corpus, the three-OS abi3 wheel smoke matrix, and the recorded go/no-go
  decisions (plan amendments #7, #11, #13) before the Phase 0 pre-release tag.
  Includes `Phase0GateReport` and `phase0_gate_report`.
- WP-005 three-OS abi3 wheel matrix: `release.yml` covers `ubuntu-latest`,
  `windows-latest`, `macos-latest` plus `x86_64`, `aarch64`,
  `universal2-apple-darwin`; `prin-py/Cargo.toml` uses `abi3-py311`;
  `pyproject.toml` declares `Operating System :: OS Independent`; all
  non-`aarch64` wheels are smoke-tested with `python -m pip install`.
- WP-005 committed the pre-trained subconscious controller ONNX model
  (`models/subconscious_controller.onnx` + `.onnx.data`, ~104 KB total) and
  evidence files (`EVIDENCE/0017-wp005-s1-ort-probe.json`,
  `EVIDENCE/0017-wp005-s1-phase0-gate.json`).
- WP-005 CLI tools: `tools/wp005_ort_probe.py` (ORT provider probe) and
  `tools/wp005_phase0_gate.py` (Phase 0 gate checker with `--refresh-ort`).

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
- `.github/workflows/python.yml` now installs the `onnx` extra (`-e ".[dev,onnx]"`)
  on every test matrix cell so the real ORT model probe runs cross-platform
  instead of being skipped on Linux and non-3.12 Windows cells.
- `.github/workflows/release.yml` now smoke-tests all non-`aarch64` wheels with
  `python -m pip install` and covers the three-OS abi3 matrix.
- Project Plan §6 amended (plan amendment #13) documenting the WP-005/Phase 0
  ORT go/no-go: the CPU fallback for the subconscious controller is proven on
  all CI platforms; DirectML graph execution falls back to CPU on the current
  Windows host; the VitisAI NPU runtime and DirectML parity are unavailable in
  Phase 0 and deferred to WP-028 (Phase 5 daemon) with a re-audit gate.
- `models/README.md` and `tools/README.md` updated to describe the split ONNX
  model files and the two new WP-005 CLI tools (S3 fixes WP005-F3, WP005-F4).

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

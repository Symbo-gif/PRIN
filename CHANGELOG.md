# Changelog

All notable changes to PRIN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Executive Audit Session 003 (EA-003)** — full-project audit across E1–E10 covering the delta
  since EA-002 (WP-010 through WP-016, Phase 1 and Phase 2 close); report
  `DOCS/audits/EXECUTIVE_AUDIT_REPORT_003.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F14):
  - **E-F1 (D1):** restored the WP001-F1..WP013-F6 cumulative deviation-ledger rows in
    `DOCS/reports/016-project-state.md` §3, corrupted since commit `234a20d` (fabricated commit
    hashes, rewritten descriptions, one invented finding) and undetected through two subsequent
    S2 audits. Restored from the verified `013-project-state.md` table; correction notes added
    to `014-` and `015-project-state.md`.
  - **E-F2/E-F4 (D1/D2):** live-reran all 9 previously-unverified GitHub Actions workflow runs on
    commits `039ee7b` (WP-014 S1) and `4a4de26` (WP-013 S4), left in a billing-block failure
    state and never remediated; `039ee7b` is now green on all 5 gated workflows, `4a4de26` on 4
    of 5 (its `python` run surfaced a real, transient, already-self-corrected historical
    inconsistency rather than a rerun artifact — documented, not erased). Corrected the
    WP014-F7 ledger entry's overstated verification claim.
  - **E-F3 (D2):** fixed `python/prin/__init__.py` version drift (`0.1.0-alpha.1` vs.
    `0.3.0-alpha.1` elsewhere) that broke `tools/wp001_baseline.py check` and 4 `pytest` tests on
    the `v0.3.0-alpha.1` release commit; fixed two related hardcoded-literal fragility bugs in
    `tests/test_wp001_baseline.py`.
  - **E-F5 (D2):** added a genuine Rust-vs-PRINet-3.0 differential parity test for HOSVD
    (`crates/prin-tensor/tests/data/prinet_reference_hosvd.json`, generated from the archived
    PRINet 3.0 reference), closing the gap between the WP-014 audit's parity-closure claim and
    the invariant-only tests it actually shipped.
  - **E-F6 (D2):** logged plan amendment #22 — the Phase 1 `v0.2.0-alpha.1` pre-release tag was
    never cut and no tag has ever been pushed to `origin`; `v0.3.0-alpha.1` retroactively covers
    both phase-exit tagging obligations. Maintainer directed that actual tag creation/push
    (triggers a real PyPI/crates.io publish) be deferred to a separate, later action.
  - **E-F7 (D3):** identified 6 open Snyk Open Source advisories in `torch@2.13.0` (5 medium, 1
    high, no fix available in any version per Snyk's own database). Investigated for a genuine
    fix per maintainer direction before accepting risk: a repository-wide grep confirms none of
    the 6 vulnerable APIs is called anywhere in PRIN's live codebase. Risk accepted and
    documented in `.snyk` with maintainer approval and a 2026-11-14 recheck.
  - **E-F8–E-F13 (D3/D4):** documentation/hygiene fixes — Phase-1 analytics report test-count
    inconsistency, `EVIDENCE/README.md` clarification, duplicated Migration Guide line,
    `prin-tensor` `strict-checks` documentation, and Project Plan §6 phase-table/amendment sync.
  - **E-F9 (D3):** added a `bench-smoke` CI job (`rust.yml`) exercising
    `cargo bench -p prin-sim --bench sweep_bench -- --test`, closing the gap where the Phase-2
    exit-gate performance claims were never CI-verified even to compile/run.
  - **E-F14 (D2):** the audited `HEAD` and its 4 predecessor commits had never been pushed to
    `origin` and had zero CI runs; resolved by this session's push.
- **Executive Mathematical Audit Session 001 (EMA-001) and remediation (EMA-001R)** — first
  integration of `math-audit-mcp` into PRIN: independent, tool-executed recomputation of
  `prin-dynamics`/`prin-metrics` mathematical claims (23 claims), governed by the new
  `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md` (Project Plan
  amendment #23); report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_001.md`
  (`PASS-WITH-REMEDIATION`, findings M-F1–M-F3):
  - **M-F1 (D1):** Z3-confirmed phase-wrap defect in
    `prin_metrics::chimera::strength_of_incoherence`/`strength_of_incoherence_temporal`
    (`chimera.rs:169-171`, mapping an in-phase pair to `-pi` instead of `0`). Fixed with a
    corrected `centred_wrap`, regression coverage, and Z3 re-verification. Investigating the
    fix's parity-test breakage found the identical defect in PRINet 3.0's own reference
    (`oscillosim.py:876-878`) — an upstream bug, not a legitimate convention difference — so
    PRIN's corrected implementation is deliberately, permanently non-parity with the PRINet 3.0
    fixture for these two metrics specifically (Project Plan amendment #25).
  - **M-F2 (D3):** re-encoded and Z3-reverified `PW-01`/`PW-02` phase-wrap invariant claims.
  - **M-F3 (D2):** resolved for `GRA-01`/`TEN-01` via two new Lean 4 `decide`-based formal
    claims (`GRA-01-LEAN`, `TEN-01-LEAN`, Project Plan amendment #24) reaching a genuine ledger
    `PASS`; resolved for `INT-01`/`INT-02`/`HOPF-01`/`KUR-01` via independent Wolfram Engine
    secondary corroboration (`EVIDENCE/math-audit/manual/`) plus a recorded maintainer/agent
    sign-off — these four remain `REQUIRES_HUMAN_REVIEW` at the governed ledger level by policy
    design (high/critical-severity `ode_property` claims require symbolic/formal evidence to
    reach `PASS`), tracked as `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-013.
  - `tools/math_audit_run.py`, `tools/math_audit_policy.yaml`, `tools/math_audit_claims/*.json`
    runner/policy/claim-ledger integration; `EVIDENCE/math-audit/` evidence trail (append-only
    `AuditResult`s, evidence bundles, `audit-trace.jsonl`).

### Added

- **WP-018 Fused mean-field RK4 kernel** (`prin-kernels`, Phase 3 second WP; sessions 0069–0072;
  audit `DOCS/audits/018-wp018-audit.md`, verdict `PASS`, zero findings):
  - `mean_field_rk4::cubecl::order_param_block_reduce` — new `#[cube(launch)]` kernel: each
    256-thread cube block reduces its slice of `amp[i]*e^{i*phase[i]}` into one `(real, imag)`
    partial via shared memory, replacing the pre-WP-018 prototype's `O(N)` full-state host
    read-back with an `O(N/256)` partial read-back.
  - `mean_field_rk4::cubecl::order_param_device` — host helper finishing the hierarchical
    reduction over `ceil(N/256)` partials with an `f64` accumulator (Coding Standards §2.2).
  - `buffers::CubeclBufferPool` — new `block_real`/`block_imag` device handles sized to
    `num_blocks_for(n) = ceil(n/256).max(1)`, and a `num_blocks()` accessor.
  - `mean_field_rk4::order_param` (the single authoritative CPU/GPU-shared algorithm) now
    accumulates in `f64` before the final `n_inv` normalization and `f32` downcast, matching the
    GPU path's level-2 host accumulator — a precision improvement over the pre-WP-018 `f32`
    accumulation.
  - `TimingMethod` enum (`Device`/`System`) and `StepReport::timing_method` — `step_cubecl_with_pool`
    now wraps the 8-launch sequence in `ComputeClient::profile`, reporting real hardware
    device-event timestamps on wgpu (`Device`) or a host wall-clock fallback on the CubeCL-CPU
    runtime (`System`), replacing the WP-004/WP-017 unconditional wall-clock prototype (partially
    closes DV-003 — see `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`).
  - `MeanFieldRk4Error::ProfilingFailed` — new typed error variant for `ComputeClient::profile`
    failures.
  - New criterion benchmark (`benches/mean_field_rk4_bench.rs`) at $N = 1{,}000{,}000$:
    `cpu_native` and `wgpu_device_dispatch` (the latter printing one untimed `StepReport` as
    device-event evidence). Observed on the local wgpu/DX12 host: device-event kernel time
    388 µs; criterion wall-clock (10 samples) 24.18–25.51 ms (host dispatch/sync overhead across
    8 launches dominates); CPU-native 115.36–119.80 ms. Reported as observed evidence, not a
    scientific conclusion (Benchmarking Standards §2.2); the Triton same-hardware comparison
    remains blocked on a Linux/CUDA runner (DV-001).
  - A genuine CubeCL CPU-backend data race in the first `order_param_block_reduce` draft (a
    missing second `sync_cube()` barrier let idle worker threads race into the next cube block's
    shared-memory buffer) was found and fixed during S1, with a regression test
    (`order_param_device_matches_host_per_block_sums_for_multi_block_n`, 5 repeated calls at
    `N=300`).
  - 6 new tests in S1; kernel-equivalence tests extended to `N=1000` (non-block-aligned, wgpu) and
    `N=300` (non-block-aligned, CubeCL-CPU) in addition to the existing `N=64`/`N=1,000,000` cases,
    all at `rtol=1e-5, atol=1e-6`.
  - S2 audit found zero findings (`PASS`); S3 recorded a no-change closure with a CLEAN
    independent delta re-audit.
- **WP-019 Sparse k-NN and PAC kernels** (`prin-kernels`, Phase 3 third WP; sessions 0073–0076;
  audit `DOCS/audits/019-wp019-audit.md`, verdict `PASS-WITH-FINDINGS`, one D4 finding FIXED):
  - `sparse_knn::SparseKnnGraph` — CSR (`indptr`/`indices`, both `u32`) sparse phase-neighbor
    graph with `from_csr` (external CSR interop) and `from_phase_knn` (builds from phase array
    and `k` via `prin_dynamics::state::build_phase_knn_index`) constructors.
  - `sparse_knn::sparse_knn_derivatives_cpu` — CPU reference computing Kuramoto-style sparse
    coupling derivatives per row with per-row `K/degree(i)` edge weight and `f64`-accumulated
    sums.
  - `sparse_knn::cubecl::sparse_knn_coupling` — single `#[cube(launch)]` gather kernel, one GPU
    thread per oscillator walking its own CSR row; host dispatch
    (`sparse_knn_coupling_cubecl`/`try_*`/`_auto`) mirrors `mean_field_rk4::cubecl`.
  - `pac::PacParams` / `pac::PacError` / `pac::pac_modulate_cpu` — `f32` CPU reference for PAC
    modulation (`A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) + offset)], amp_min, amp_max)`)
    with `f64`-accumulated mean, matching `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate`.
  - `pac::cubecl::pac_modulate_cubecl` — two-stage kernel: `pac_phase_sum_block_reduce`
    (hierarchical device-side reduction of `slow_phase`) finished on the host in `f64`, then
    `pac_modulate` (elementwise broadcast + clamp).
  - New criterion benchmark (`benches/sparse_knn_bench.rs`) at `N=16,000, k=14`: `cpu_native`
    and `wgpu_device_dispatch`. Observed on local wgpu/DX12: `cpu_native` 1.84–1.87 ms
    (8.57–8.70 Melem/s); `wgpu_device_dispatch` 1.87–1.95 ms (8.21–8.58 Melem/s). Pilot
    benchmark, not a regression gate (Benchmarking Standards §2.2).
  - 61 new tests + 4 proptest suites in S1. Kernel-equivalence at `N=16,000, k=14` (acceptance
    shape) and `N=100,000` (PAC) pass at `rtol=1e-5, atol=1e-6`. Cross-crate parity tests
    against `prin_dynamics` references at `1e-4` absolute tolerance.
  - S2 audit found one D4 finding (WP019-F1, factual inaccuracy in S1 handoff note coverage
    table); S3 fixed it with a CLEAN delta re-audit.
- **Phase 2 recommendation implementation** (inter-phase process improvement, R14–R20 disposition
  in `DOCS/ANALYTICS/phase-2/phase-2-recommendation-implementation-governance.md`):
  - Fixed PA2-F1: `tools/math_audit_run.py` `ruff check`/`ruff format` violations (import
    sorting, two `E501` long lines) (R14a).
  - This EMA-001/EMA-001R `CHANGELOG.md` entry, closing PA2-F2 (R14b).
  - S1 exit-gate parity-evidence disposition requirement added to
    `Development_Workflow_and_Audit_Standards.md` §3: before an S1 session is marked COMPLETE,
    the author states whether a directly comparable PRINet 3.0 reference exists for the new
    primitive (verified by a stated grep/import check, not an unverified assertion), and if so,
    either includes parity evidence in the S1 commit or explicitly defers it with a reviewable
    reason (R15).
  - EA/EMA session closing checklist added to `Executive_Audit_Governance_and_Methodology.md` §5
    and `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8: every global session
    that modifies or adds files must update `CHANGELOG.md` `[Unreleased]` and run the relevant
    quality gates on newly committed files before the session closes (R16).
  - Snyk MCP availability standing check added to `ANALYTICS_METHODOLOGY.md` §5.1 and
    `Executive_Audit_Governance_and_Methodology.md` §2: explicitly verify Snyk MCP tool
    availability at the start of each future phase-analytics/EA session, citing a dated
    carry-forward result when unavailable (R18).
  - R17 (automated cumulative-deviation-ledger consistency check) and R19 (assign a WP/phase to
    the carried `prin-py`/`prin-kernels` scope) deferred with explicit future-session assignments
    per `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`; R20 deferred to the next EMA session.
- **WP-017 Kernel architecture and CPU references** (`prin-kernels`, Phase 3 first WP):
  - `backend` module — `Device` enum, `BackendError`, `backend_priority`,
    `auto_detect_order`; preference decoupled from availability.
  - `buffers` module — `MeanFieldRk4Buffers` (CPU `Vec<f32>` pool) and
    `CubeclBufferPool<R: Runtime>` (GPU device-handle pool), both with
    `capacity()` accessors and size-validation guards.
  - `mean_field_rk4` module — CPU reference `step_cpu` and pooled
    `step_cpu_with_pool`; single authoritative `order_param` implementation;
    `MeanFieldRk4Params`, `MeanFieldRk4Error`, `MeanFieldRk4Output`.
  - `mean_field_rk4::cubecl` module — single-source CubeCL kernels;
    `step_cubecl`, `step_cubecl_with_pool`, `try_step_wgpu`, `try_step_cpu`,
    `try_step_cuda`, and automatic `step_auto` dispatch with graceful fallback
    to the native CPU reference. `StepReport` records backend, host wall-clock,
    and launch count (device-event timing remains a Phase 3 optimization,
    DV-003).
  - `equivalence` module — `EquivalenceHarness`, `EquivalenceCase`, and
    `assert_allclose` for cross-backend kernel-equivalence testing.
  - S3 remediation added `MeanFieldRk4Error::PoolSizeMismatch` and explicit
    pool/call-size checks in `step_cpu_with_pool` and
    `step_cubecl_with_pool`, with regression tests. Removed dead
    `CubeclBufferPool` accessor methods and raised `buffers.rs`/`equivalence.rs`
    coverage above the 95% gate.

## [0.3.0-alpha.1] — Phase 2 exit (Advanced numerics and simulation)

### Added

- WP-016 Parallel sweeps, CPU optimization, and Phase 2 gate in `prin-sim` (Phase 2, fifth WP):
  - `sweep` module — `run_sweep`, `SweepConfig`, `SweepResult`, `SweepAxis`, `SweepModel`:
    rayon-parallel parameter sweeps over coupling strength, decay rate, frequency adaptation,
    and bifurcation axes with deterministic per-configuration seeding via `Seed`. Each
    configuration runs an independent `OscilloSim` simulation.
  - `detect_oscillation` — windowed-variance oscillation detection on order-parameter histories,
    reusing `prin_metrics::order::kuramoto_order_parameter` (one algorithm, one implementation;
    replaces the private duplicate from S1). PRINet 3.0 `sweep_utils.detect_oscillation` parity
    verified across 384 combinations in `tests/parity_detect_oscillation.rs`.
  - `dispatch` module (crate-private) — size-gated sequential/parallel CPU dispatch
    (`map_dispatch`, `zip_map_dispatch`) with `PARALLEL_LEN_THRESHOLD = 32,768`. Sequential
    CPU reference path below threshold; rayon-parallel path at or above. Eliminates
    thread-pool overhead on small problem sizes while scaling on large ones.
  - `Arc<SparseCoupling>` sharing — `SparseKuramoto`, `SparseStuartLandau`, and `OscilloSim`
    now store `Arc<SparseCoupling>` via `impl Into<Arc<SparseCoupling>>` constructors,
    eliminating the per-configuration CSR deep-clone (~136 MB at $N = 1\mathrm{M}$).
    `OscilloSim::coupling_arc()` returns an $O(1)$ `Arc::clone`.
  - `strict-checks` feature in `prin-sim/Cargo.toml` forwarding to `prin-dynamics/strict-checks`.
  - Criterion benchmark suite (`benches/sweep_bench.rs`) with in-process serial baselines
    (dedicated 1-thread `rayon::ThreadPool`) alongside parallel variants. Sweep workload:
    $N = 4096$, 300 steps, 4–64 configs. SpMV/engine: up to $N = 1{,}000{,}000$.
  - $N = 100{,}000$ deterministic regression test (`oscillo_sim_n100k_kuramoto_deterministic_and_finite`)
    asserting bit-identical determinism, finite phases/amplitudes, order parameter $\in [0,1]$,
    and coupling memory $< 20\,\mathrm{MB}$.
  - Plan amendment #20 narrows WP-016 scope to `crates/prin-sim/` only; `prin-py` sweep/engine
    bindings and `prin-kernels` CPU-reference work deferred to a future WP.
  - Plan amendment #21 re-scopes performance targets to hardware-scoped, evidence-based values
    (peak sweep ≥3.5× on 8 physical cores; SpMV/engine ≥1.5× at $N \geq 65{,}536$) after S1
    benchmark evidence showed the original ≥8×/≥2× targets were a memory-bandwidth/SMT ceiling.
  - S2 audit (`DOCS/audits/016-wp016-audit.md`) found seven findings (WP016-F1 D1, WP016-F2–F4
    D2, WP016-F5–F7 D3): performance below target, missing SIMD/dispatch, algorithm duplication,
    no $N = 1\mathrm{M}$ parity evidence, benchmark design, stale docs, and coupling ownership.
  - S3 remediation closed all seven: `dispatch.rs` sequential/parallel dispatcher, `order_parameter`
    duplication removed in favour of `prin_metrics`, $N = 100\mathrm{k}$ regression test, benchmark
    rewritten with serial baselines and larger workloads, `lib.rs` docs corrected, `Arc` coupling
    sharing. Delta re-audit: **CLEAN**.
- WP-015 OscilloSim sparse simulation engine in `prin-sim` (Phase 2, fourth WP):
  - `SparseCoupling` — Compressed Sparse Row (CSR) matrix storage format for
    sparse coupling topologies (`AllToAll`, `Ring`, `SmallWorld`) with $K/\mathrm{degree}$
    normalization, input dimension/finite checks, and memory footprint tracking
    (`memory_bytes()`).
  - `SparseKuramoto` and `SparseStuartLandau` — sparse dynamics models implementing
    `Dynamics` via $O(\mathrm{nnz})$ SpMV. Kuramoto coupling uses trigonometric
    decomposition ($\sin(\theta_j - \theta_i) = \sin\theta_j \cos\theta_i - \cos\theta_j \sin\theta_i$)
    to compute coupling in two SpMV products; Stuart–Landau uses diffusive SpMV.
  - `OscilloSim` — simulation engine coordinating `OscillatorState`, sparse dynamics,
    reusable buffer management, numerical guards (`apply_guards`), single-stepping
    (`step()`), fixed-step integration (`integrate_fixed`), and trajectory recording.
  - `PruningStrategy` and `PruningResult` — amplitude-threshold dynamic oscillator
    pruning with bidirectional index mappings (`pruned_to_original`,
    `original_to_pruned`) and state restoration (`restore()`) with configurable
    `default_amplitude`.
  - `ChimeraMetrics`, `compute_chimera_metrics`, and `trajectory_chimera_metrics` —
    chimera-state analysis integrated with the CSR sparsity pattern as spatial
    neighborhoods.
  - `SimError` typed enum (`DimensionMismatch`, `IndexOutOfBounds`, `EmptySystem`,
    `InvalidParameter`, `NonFiniteValue`, `InvalidTolerance`, `StepFailed`,
    `PruningFailed`, `InvalidKnn`, `StateError`).
  - 21 Rust-native parity integration tests in
    `crates/prin-sim/tests/parity_sparse_vs_dense.rs` comparing sparse vs dense
    Kuramoto and Stuart–Landau models at $N \in \{8, 16, 64, 256\}$ at
    $\mathrm{rtol} = 10^{-10}$ to $10^{-12}$, plus large-$N$ memory scaling tests
    ($N = 10{,}000$, $\mathrm{nnz} = 200{,}000$, memory $< 5\,\mathrm{MB}$).
  - 4 property tests in `crates/prin-sim/tests/proptest_properties.rs` verifying
    sparse-vs-dense Kuramoto parity for arbitrary $N \in [3, 64)$ and ring degree,
    memory byte calculation correctness, seed-based determinism, and engine memory
    accounting.
  - S3 fixes for audit findings WP015-F1 (D1) through WP015-F6 (D3), achieving 0
    failures under `--features strict-checks`, clean dependencies, accurate crate
    metadata, and property test verification.
  - No Python bindings in this WP; PyO3 exposure and parallel sweeps are in WP-016.
- WP-014 Tensor decompositions in `prin-tensor` (Phase 2, third WP):
  - `PolyadicTensor`, `hosvd()` — Tucker/HOSVD via `faer` SVD with per-mode
    rank truncation. Factor matrices are left singular vectors of mode-n
    unfoldings; full-rank HOSVD is an exact reconstruction.
  - `CPDecomposition`, `cp_als()`, `CPResult` — CP/PARAFAC via alternating
    least squares with deterministic `Seed`-based initialization and
    convergence diagnostics (`iterations`, `final_relative_change`,
    `converged`).
  - `TensorError` typed enum (`EmptyInput`, `NonFiniteValue`, `ZeroDimension`,
    `InvalidRank`, `InvalidComponents`, `ShapeMismatch`, `NonConvergence`,
    `InvalidTolerance`, `InvalidMaxIter`, `InvalidMode`, `LinearAlgebraFailed`,
    `ModeProductDimMismatch`, `InsufficientModes`).
  - `mode_unfold`, `mode_n_product`, `frobenius_norm`, `refold` in
    `prin-tensor::utils`; Khatri-Rao product and Gauss-Jordan matrix inverse
    in `prin-tensor::cp`.
  - `serde` derives on `PolyadicTensor` and `CPDecomposition`.
  - 9 Rust-vs-PRINet 3.0.0 parity tests in
    `crates/prin-tensor/tests/parity_decomposition.rs` (reconstruction,
    factor orthonormality, truncated ranks, CP rank-1, all-factor
    normalization, weights, seed reproducibility, round-trip) at `rtol=1e-10`
    (float64, single-runtime).
  - `cp.rs` coverage raised from 92.55% to 96.30% lines in S3 remediation; all
    new `prin-tensor` modules meet the ≥95% gate.
  - S3 fixes for audit findings WP014-F1 (D1) through WP014-F7 (D3), including
    the GitHub Actions billing-block restoration recorded in the audit report.
  - No Python bindings in this WP; PyO3 exposure is a future WP.
- WP-013 Continuous band networks and temporal propagation in `prin-dynamics`
  (Phase 2, second WP):
  - `BandParams` — per-band `KuramotoOscillator` configuration (frequency,
    coupling `K`, amplitude decay `λ`, frequency adaptation `γ`,
    `freq_adaptation_rate`, and per-band `CouplingMode` via `with_coupling`;
    the PRINet 3.0 reference uses `sparse_knn`).
  - `PacPair` — declares a slow→fast cross-frequency PAC link (any strictly
    slow→fast pair is permitted, including the non-adjacent delta→gamma
    cascade).
  - `BandNetwork` — single continuous ODE right-hand side over the
    concatenated state, implementing `Dynamics` so it composes with every PRIN
    `Integrator` rather than embedding one. Intra-band derivatives are
    evaluated by the crate's `KuramotoOscillator` on each band's sub-state (one
    algorithm, one implementation), so every `CouplingMode` is available per
    band. Cross-band PAC enters `dA_fast/dt` as the relaxation term
    `λ_fast·(A_target − A_fast)` toward the reference's modulation target
    (the continuous-time analogue of PRINet 3.0's discrete assignment; Project
    Plan amendment #19).
  - `theta_gamma_network` / `delta_theta_gamma_network` factories (2- and
    3-band hierarchies), `theoretical_capacity` (`floor(f_fast / f_slow)`,
    ~7 for typical θ/γ frequencies; the Lisman–Jensen working-memory capacity
    model), `create_band_state` helper.
  - `BandError` typed enum (`NoBands`, `EmptyBand`, `InvalidBandIndex`,
    `InvalidCouplingMode`, `MissingBandLabels`, `InvalidCapacity`,
    `Partition`).
  - `ComplexPhasorBlender`, `EmaAmplitudeBlender`, `TemporalPropagator` —
    frame-to-frame temporal propagation via complex-phasor phase blending +
    EMA amplitude blending. PRIN's `alpha` weights the new frame; PRINet 3.0's
    `carry_strength`/`amplitude_decay` weight the carried frame, so
    `alpha = 1 − carry_strength` / `alpha = 1 − amplitude_decay` (the
    conventions are complements, not synonyms — documented on every type and
    enforced by `parity_temporal::parity_reversed_convention_does_not_match`).
  - `TemporalError` typed enum (`InvalidBlendingFactor`, `EmptyInput`,
    `LengthMismatch`, `NonFiniteValue`).
  - `prin-py` PyO3 bindings `PyBandParams`, `PyPacPair`, `PyBandNetwork`,
    `create_band_state_py`, `PyComplexPhasorBlender`,
    `PyEmaAmplitudeBlender`, `PyTemporalPropagator` in `bindings/bands.rs`
    and `bindings/temporal.rs`; `python/prin/dynamics.py` `__all__` grew
    from 20 to 27 symbols; `python/prin/_prin_core.pyi` stubs regenerated;
    44 Python acceptance tests in `tests/test_wp013_bands_temporal.py`.
  - 18 new Rust-vs-PRINet 3.0.0 parity tests: 12 in
    `crates/prin-dynamics/tests/parity_bands.rs` (per-mode intra-band
    derivatives, composed 2-band/3-band right-hand sides, RK4 golden
    trajectories at `n = 1` and `n = 10` for `mean_field` and `sparse_knn`,
    `theoretical_capacity` vs the reference `MultiRateIntegrator` sub-step
    count) and 6 in `crates/prin-dynamics/tests/parity_temporal.rs` (single
    blend, chained 5-frame sequence, wrap-around, clamp saturation, parameter-
    mapping directional guard). Measured worst-case drift: `2.22e-16`
    (sparse k-NN, the reference mode), `2.74e-9` (full), `1.19e-7` (mean-field,
    amendment #14 hazard), `~1 ulp` (temporal, fully `f64` on both sides).
  - All WP-013 acceptance criteria met: band/temporal golden trajectories
    pass; capacity invariants and phase continuity are property-tested; PAC
    interactions are exercised; `bands.rs` 98.97% lines / 98.68% functions,
    `temporal.rs` 99.79% lines / 100% functions (identical under
    `--features strict-checks`).
  - Integrator stage states now carry `freq_band` labels from the base state,
    so a `BandNetwork` can be driven by RK4/RK45/exponential integrators
    (previously stage 2+ lost the band labels and the dynamics failed with
    `MissingBandLabels`); numerically exact since the labels are fixed.
- WP-012 Exponential and multi-rate integrators in `prin-dynamics` (Phase 2, first WP):
  - `ExponentialIntegrator` — exponential Euler (`y_{n+1} = exp(hA) y_n + h·φ₁(hA)·g(y_n)`) via direct Padé(13) scaling-and-squaring (`dim ≤ max_direct_dim`) or Krylov–Arnoldi subspace approximation with modified Gram-Schmidt (`dim > max_direct_dim` or `stiff_mode`, adaptive rank from the estimated Jacobian 1-norm condition number).
  - `MultiRateIntegrator` — uniform sub-stepping: divides the outer timestep into `sub_steps` equal inner `MultiRateMethod::RK4`/`Euler` steps applied to all oscillators, matching the PRINet 3.0 reference implementation.
  - `IntegrateError::InvalidDim`, `InvalidKrylovRank`, and `LinearSolveFailed` variants (ten total, up from seven at WP-008).
  - `prin-py` PyO3 bindings `PyExponentialIntegrator` and `PyMultiRateIntegrator` in `bindings/integrators.rs`; `python/prin/dynamics.py` `__all__` grew from 18 to 20 symbols; `python/prin/_prin_core.pyi` stubs regenerated; 21 new Python acceptance tests in `tests/test_dynamics_bindings.py` (`TestExponentialIntegrator`, `TestMultiRateIntegrator`).
  - 7 new Rust-vs-PRINet 3.0.0 trajectory parity tests in `crates/prin-dynamics/tests/parity_integrators.rs` (4 `ExponentialIntegrator`, 3 `MultiRateIntegrator`) with hard-coded `torch.float64` reference values, bringing the file to 23 parity tests.
  - All WP-012 acceptance criteria met: golden and convergence tests pass including λ→0 (`phi1_zero_is_identity`); stability (Krylov vs. direct agreement) and typed-failure cases (`InvalidDim`, `InvalidKrylovRank`, `LinearSolveFailed`) are demonstrated; `integrate.rs` coverage 98.24% lines / 98.46% functions (default), 97.74% lines / 98.50% functions (`strict-checks`).
- **Phase 1 recommendation implementation** (inter-phase process improvement):
  - Exhaustive 504-case differential parity test (`test_corpus_exhaustive_differential_parity`) parametrized from the corpus manifest, validating the full Python → Rust → reference pipeline for all golden-trajectory cases (R8).
  - `pytest-xdist` parallel execution in `parity.yml` CI workflow (`-n auto`) for exhaustive corpus runs (R8).
  - Deferred Validation Register (`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`) consolidating all deferred items with re-audit gates, governing amendments, and closure tracking (R9).
  - Phase 1 recommendation implementation governance document (`DOCS/ANALYTICS/phase-1/phase-1-recommendation-implementation-governance.md`) (R7–R13).
- **Documentation accuracy sweep** added to S4 checklist in `Documentation_Standards.md` §7 item 8: explicit verification of README accuracy, rustdoc example compilation, and DOCS/ index currency (R7).
- **Strict-checks coverage reporting** added to `AGENTS.md` verification one-liner: separate `cargo llvm-cov -p prin-dynamics` runs for default and `strict-checks` feature builds (R12).
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
- WP-011 Phase 1 Python API and dynamics integration:
  - `prin-py` PyO3 bindings for the complete Phase 1 dynamics and metrics surface: `bindings/state.rs` (`PyOscillatorState`, `PyStateDerivatives`, `PySeed`, constants), `bindings/models.rs` (`PyKuramotoOscillator`, `PyStuartLandauOscillator`, `PyHopfOscillator`), `bindings/integrators.rs` (`PyEulerIntegrator`, `PyRK4Integrator`, `PyRK45Integrator`, `PyAdaptiveResult`), `bindings/coupling.rs` (`PyCouplingMode`, `PyTopology`, `PyPhaseAmplitudeCoupling`), and `bindings/metrics.rs` (22 `#[pyfunction]`s covering the full `prin-metrics` surface).
  - `python/prin/dynamics.py` re-export module (18 symbols + `__all__`, grown to 20 by WP-012) and `python/prin/metrics.py` re-export module (22 symbols + `__all__`) — pure re-exports, no Python numerics.
  - Complete type stubs in `python/prin/_prin_core.pyi` for all new dynamics and metrics symbols.
  - `numpy = "0.29.0"` dependency added to `prin-py/Cargo.toml` for PyO3 numpy array integration (matches PyO3 version).
  - 69 new Python acceptance tests in `tests/test_dynamics_bindings.py` across 13 test classes (constants, Seed, OscillatorState, StateDerivatives, CouplingMode, Topology, Models, Integrators, PAC, Metrics, module re-exports).
  - All WP-011 acceptance criteria met: no Python numerics; 42 mapped PRINet 3.0 symbols resolve through the Python API; 253 Python tests pass (including parity); 370 Rust tests pass; Phase 1 tag gate passes.

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
- Project Plan §6 amended (plan amendment #18, WP012-F4): clarified that `MultiRateIntegrator` implements uniform sub-stepping (dividing the outer timestep into `sub_steps` equal inner RK4/Euler steps applied to all oscillators), matching the PRINet 3.0 reference implementation, rather than band-aware per-`freq_band` scheduling. The latter is a deferred capability, not part of WP-012. Updated the `MultiRateIntegrator` rustdoc to match (previously implied band-differentiated scheduling that was never implemented).

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
- WP-011 S3 remediation (audit finding WP011-F1, commit `cd20b1a`):
  - WP011-F1: Removed unnecessary `#![allow(unsafe_code)]` from `crates/prin-py/src/bindings/state.rs` — no `unsafe` code exists in the module; the attribute could mask future unsafe additions under the crate-level `#![deny(unsafe_code)]`.
- WP-012 S3 remediation (audit findings WP012-F1–F5, commits `62deb43`, `e4e7772`, `2dc641e`, `850a99b`):
  - WP012-F1 (D1): Added `PyExponentialIntegrator`/`PyMultiRateIntegrator` PyO3 bindings, `python/prin/dynamics.py` re-exports, `_prin_core.pyi` stubs, and 21 Python acceptance tests — WP-012's declared scope included Python bindings through `prin-py`, which the S1 commit had omitted.
  - WP012-F2 (D1): Added 7 Rust-vs-PRINet 3.0.0 golden-trajectory parity tests for `ExponentialIntegrator`/`MultiRateIntegrator` — the S1 commit had unit-level invariants but no differential parity evidence against the reference implementation.
  - WP012-F3 (D1): Fixed `matrix_exp`/`phi1_matrix`/Krylov solve paths to propagate `IntegrateError::LinearSolveFailed` on a singular Padé LU denominator instead of silently returning the identity matrix, which could produce a wrong trajectory with no error signal; added regression test `matrix_exp_singular_denominator_returns_typed_error`.
  - WP012-F4 (D3, amendment #18): Clarified the WP-012 "multi-rate" scope as uniform sub-stepping matching PRINet 3.0, rather than the band-aware scheduling implied by the WP text; see the Changed section.
  - WP012-F5 (D4): Added `3 * state.phase.len() == self.dim` validation to `ExponentialIntegrator::step`/`::integrate`, returning `IntegrateError::InvalidDim` on mismatch instead of silently using a stale stored `dim` for the direct/Krylov path decision.
  - Delta re-audit (`DOCS/audits/012-wp012-audit.md`): CLEAN — all five findings closed, no newly introduced deviation.

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

# Changelog

All notable changes to PRIN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **WP-036F S2 audit (`0144V`) — `PASS-WITH-FINDINGS`, mandatory S3 handoff.**
  Independent verification confirms the re-exported three-input-`Gemm`
  controller graph is bit-identical to the PRINet 3.0 reference on
  `CPUExecutionProvider` over the 48-case set, that `DmlExecutionProvider`
  executes it (not a CPU fallback) and agrees with CPU at `max_abs_diff
  7.15e-7` within `rtol=1e-5, atol=1e-6`, and that the change is confined to a
  graph-transform pass + tools + tests + docs (no controller algorithm, daemon
  runtime, backend-selection, DV-025, or `prin` public-API change). Two
  findings: changed-code coverage on the two new tools is 94% (< 95%) with
  untested `transform_graph` error paths and `_check` drift branches
  (WP036F-F1, D2); `mypy --strict` nits in the new tools, outside the
  `python/prin` gate (WP036F-F2, D4). DV-006 DirectML-half evidence is in
  place for the S4 register/DoD update. See `DOCS/audits/036f-wp036f-audit.md`.
- **WP-036F S1 coding (`0144U`) — DirectML controller-graph execution.** The
  subconscious controller ONNX graph (`models/subconscious_controller.onnx`)
  is re-exported with **three-input `Gemm` nodes**: an explicit zero-valued
  `float32` bias per layer (`net.0.bias` / `net.3.bias` / `net.6.bias`, all
  zeros), which ONNX Runtime's `DmlExecutionProvider` requires — its
  `DmlFusedGemm` fusion rejects the two-input `Gemm` form PyTorch exported
  (`InvalidGraph: ... input size 2 not in range [min=3, max=3]`). Adding a
  zero bias does not change the graph's function: it is **bit-identical** to
  the pre-transform graph on `CPUExecutionProvider` over the 48-case
  differential set (`max_abs_diff = 0.0`). `DmlExecutionProvider` now executes
  the graph and agrees with CPU within `rtol=1e-5, atol=1e-6`
  (`max_abs_diff_vs_cpu = 7.15e-7`); DirectML-vs-CPU inference latency is
  recorded (`EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`). New
  `tools/wp036f_reexport_controller.py` (idempotent transform + `--check`
  verifier, refreshes `models/manifest.json`) and
  `tools/wp036f_provider_latency.py`. The graph digest moves
  `3396bfdd…4102` → `d7d7935b…341a` (18,270 → 19,428 bytes); the
  `subconscious_controller.onnx.data` weight companion is unchanged.
  `tests/test_wp036f_reexport.py` (21 tests) and a DirectML case in
  `tests/test_daemon_controller.py::TestCrossProviderAgreement`. Closes the
  DirectML half of **DV-006** (evidence in place; register/DoD updates at
  WP-036F S4); the VitisAI / Ryzen AI NPU half stays OPEN (hardware/wheel
  gated). No `prin` public-API change; controller algorithm, daemon runtime,
  and backend-selection logic untouched.
- **WP-036E S4 documentation (`0144T`) — WP-036E closed.** READMEs updated
  (`crates/prin-kernels/`, `crates/prin-sim/`, `crates/prin-py/`, `tests/`);
  `DOCS/sphinx/parity_report.rst` GPU-vs-CPU tolerance table current;
  `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — **DV-030** and **DV-003**
  updated to `PARTIALLY CLOSED by WP-036E` with evidence chain; PSR
  `DOCS/reports/036e-project-state.md` issued. WP-036F (session `0144U`)
  entry conditions confirmed. WP-036E is closed; only then may WP-036F
  (`0144U`) begin.
- **WP-036E S3 remediation (`0144S`) — all four `0144R` findings closed; delta
  re-audit CLEAN.** **WP036E-F1 (D1) AMENDED** via **plan amendment #44**:
  genuine CUDA device-event timing is not reachable on the pinned
  `cubecl = "0.10.0"` (`cubecl-cuda` hard-registers `TimingMethod::System` and
  its compute server syncs around every profile), so **DV-003 is
  `PARTIALLY CLOSED by WP-036E`** — the on-device CUDA `f64` level-2 combine,
  batched read-backs and a measured bounded host residual (0.155 ms median at
  N=262,144, wall/`StepReport` ratio 1.058) are delivered; genuine device-event
  timing is re-gated to a `cubecl` release exposing `TimingMethod::Device` for
  CUDA, or a vendored-shim WP. Same dependency wall as amendments #37/#43.
  **WP036E-F2 (D2) FIXED**: the five `cargo clippy -p prin-sim --features cuda`
  lints resolved without behaviour change (`try_create_client` restructured;
  `MeanFieldInner`/`BandStepperInner` device payloads boxed via
  `MeanFieldDevice`/`BandStepperDevice`; two `needless_range_loop`).
  **WP036E-F3 (D2) FIXED**: changed-line coverage reported across the
  `nofeat ∪ cpu ∪ wgpu ∪ cuda` matrix with a documented DV-004 exclusion for
  the one changed `#[cube(launch)]` body; regression tests added for the
  `*DeviceState::from_parts` adopt-handles paths, the `EmptyPopulation` guard,
  the wgpu-under-CUDA host `f64` combine, and the `prin-sim` host-slice
  fallback arms + CUDA-export guards; `order_param_device`'s duplicated host
  `f64` combine deduplicated into `host_f64_combine`. **WP036E-F4 (D4) FIXED**:
  `pytest -m gpu` selects exactly 12 (the S1 handoff/Q3 brief "13" corrected);
  `DOCS/sessions/phase-6/README.md` `0144Q1`–`0144Q3` moved to `COMPLETE`.
- **WP-036E S2 audit (`0144R`) — `FAIL`, mandatory S3 handoff.** Independent
  CUDA/CPU execution confirms the device-resident architecture, zero-copy
  `kDLCUDA` export, default GPU tolerances, 12 GPU-selected tests, and 2,743
  fast CPU tests. Four findings remain: CUDA profiling reports system timing
  rather than the required device event (WP036E-F1, D1); the explicit CUDA
  `prin-sim` clippy gate has five Q2-introduced findings (F2, D2); ≥95%
  changed-line coverage is not demonstrated (F3, D2); and S1's GPU count plus
  phase index are inaccurate (F4, D4). Snyk Code/Open Source and native
  security gates found no change-attributable vulnerability. See
  `DOCS/audits/036e-wp036e-audit.md`.
- **`mean_field_rk4::cubecl` RK4 step `launch_count` 8 → 9 (WP-036E S1 sub-pass
  `0144Q1`).** The device-resident step has no host-resident input slice, so
  stage 1 now takes its order parameter from the same device-side hierarchical
  reduction stages 2–4 use (one extra launch). `StepReport::launch_count` is now
  9 = 4 stage kernels + 4 order-parameter reductions + 1 finalize;
  `discrete_step` stays at 10. Numerically within the kernel-equivalence
  tolerance (stage-1 `Z` is a block reduction + host `f64` combine instead of a
  host `f64` sum). `CubeclBufferPool` drops its three `out_*` handles (the
  device path allocates the finalize outputs per step) and gains a zeroed
  `k_zero` handle allocated once at pool construction.
- **Plan amendment #43 (2026-09-02) — WP-036E S1 (`0144Q`) re-scoped and
  decomposed.** S1-start repository verification established that a *true
  bidirectional zero-copy Torch↔CubeCL DLPack kernel-input path* (DV-030's
  stated closure mechanism, and the `0144Q` brief's headline deliverable) is
  **not reachable on the pinned `cubecl 0.10.0`**: `cubecl-cuda`'s `GpuStorage`
  has no API to adopt an externally-owned CUDA device pointer as a `Handle`,
  and `ComputeClient`'s entire handle-creation surface consumes host bytes or
  allocates uninitialised device memory (no `[patch]`/vendored fork). Same wall
  that re-scoped predecessor `0144I2` (amendment #37). WP-036E S1 is re-scoped
  to the achievable device-resident envelope — `prin-kernels` device-`Handle`
  dispatch entry points, `prin-sim` engines holding persistent device buffers
  across `step`, an on-device CUDA `f64` mean-field RK4 combine (DV-003), and an
  **export-direction** zero-copy DLPack path plus one host upload at engine
  construction — and decomposed into three coding sub-passes `0144Q1`–`0144Q3`
  (Development Workflow §7; pre-authorised by amendment #38) feeding the single
  S2 audit `0144R`. **DV-030 → `PARTIALLY CLOSED`**: bidirectional zero-copy
  kernel-input is re-gated to a `cubecl` version bump that adds external-memory
  registration to `GpuStorage`, or a vendored `cubecl-cuda` storage shim (a
  dedicated future WP). `test_acceptance_q2.py::test_sparse_vram_subquadratic`'s
  disposition is adjudicated at S2 (`0144R`) per Plan risk R2. Planned session
  count 253 → 256.
- **ETCA-001 remediation (2026-09-01) — all ten findings closed; verdict
  `PASS-WITH-REMEDIATION` → `PASS`.** Dedicated remediation session for the
  first Executive Testing and CI Audit (`DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md`
  §7).
  - **T-F1:** `python/prin/kernels.py` and `python/prin/nn/hybrid_compat.py`
    carry bandit-native `# nosec B404/B603/B110` (the rationale already
    documented for the ruff `# noqa`), so `bandit -r python/prin` exits 0. The
    R17 deviation-ledger and R34 DV-register gates move from `python.yml`'s
    `lint` job into a new dedicated **`governance`** job so a failing lint step
    can never leave them unreached again.
  - **T-F2:** 17 WP-036A reference-parity tests (`test_autoencoders.py`,
    `test_hierarchical_layers.py`, `test_inhibition_layers.py`,
    `test_model.py`) gained an in-body `pytest.importorskip(...)` guard so they
    skip — not hard-fail — on the `python.yml` matrix, which does not install
    the archived PRINet 3.0 reference.
  - **T-F3:** `tools/wp001_baseline.py` scans the whole leading session-brief
    metadata block (to the first `## ` heading) instead of a hard 12-line
    window; the `0144P` brief's `**Status:**` block was compressed.
  - **T-F5:** `python.yml` (ubuntu legs), `repro.yml`, and the new
    `nightly.yml` reclaim runner disk and install a CPU-only torch before
    `maturin develop`, so `torch>=2.0` no longer drags the ~5 GB CUDA 13 wheel
    stack from PyPI (`[Errno 28]`). DV-022 scope extended.
  - **T-F6:** `rust.yml`'s Windows `test` leg returns to GitHub-hosted
    `windows-latest` (a `GITHUB_TOKEN` cannot query self-hosted-runner status
    for a dynamic preflight), removing the single-runner SPOF that hung the leg
    24 h. `PRIN-GPU-Runner` stays reserved for `gpu.yml`. DV-024 updated.
  - **T-F8:** `test_no_gpu_throughput_regression` quarantine now tracked as
    **DV-032** (perf-test hardening) with a dated maintainer disposition;
    `tests/conftest.py` skip reason names it.
  - **T-F9:** new `prin.reporting._artifacts.allowed_output_roots()` adds the
    in-repo `.pytest_basetemp` to the figure/table output allowlist only under
    pytest, so the 11 `test_acceptance_y4q2` generators pass under the
    `AGENTS.md`-mandated `--basetemp` override; production confinement
    unchanged.
  - **T-F10:** `AGENTS.md` bandit invocation aligned to
    `bandit -r python/prin -c pyproject.toml` (matches `python.yml` /
    Coding Standards §5/§6.2).
  - **CI-only Windows failures** flagged by the audit's T6 dimension:
    `StateCollector` step-latency timing switched `time.monotonic()` →
    `time.perf_counter()` (`python/prin/training_hooks.py` — Windows
    `monotonic` granularity zeroed sub-15 ms steps); the two
    `test_wp036d_gpu_dispatch.py` kernel-agreement tests gained a
    `skipif(not hasattr(prin._prin_core, "GpuSparseKuramoto"))` guard for the
    non-CUDA `python.yml` build.
  - **CI-surfaced pre-existing failures** (T-F4 follow-ups — the never-run CI
    had masked these for the whole phase): the T-F5 disk-reclaim step no
    longer deletes `/opt/hostedtoolcache` (it held the `setup-python`
    interpreter → `pip: exit 127`); `test_acceptance_y2q4.py::TestDocumentation`
    path adapted `docs/` → `DOCS/` (Linux case-sensitivity; PRINet 3.0 used
    lowercase); `test_train_bridge_slot_attention.py` gained an autouse
    `torch.manual_seed(0)` fixture (its gradchecks ran on unseeded input
    through a `match_threshold` branch); `test_acceptance_y4q1_5.py::test_deterministic_seed`
    (wall-clock frame-count flake) folded into **DV-032**; Windows
    `python.yml` keeps its original torch-install order.

- **Version string `0.3.0-alpha.1` → `0.3.0`** (WP-036C S1 sub-pass `0144M1`,
  plan amendment #40). The pre-release tag is dropped so the ported PRINet 3.0
  Y2Q4 API-freeze acceptance tests (`test_acceptance_y2q4::TestVersioning` /
  `TestAPIFreeze::test_version_is_stable`) pass on their unchanged assertions
  (three-part all-digit semantic version, no `alpha`/`rc`/`dev` suffix). This
  is a version-string correction only; release publishing is unchanged.

### Added

- **`prin-kernels` device-`Handle` dispatch layer (WP-036E S1 sub-pass
  `0144Q1`, plan amendment #43).** Each of the three CubeCL kernel modules gains
  a device-buffer-in/out entry point alongside the existing host-slice one, so a
  caller holding CubeCL device buffers runs the kernel with **no host
  transfer**: `sparse_knn::cubecl::{SparseKnnDeviceState, SparseKnnDeviceDerivs,
  sparse_knn_coupling_device}`; `mean_field_rk4::cubecl::{MeanFieldDeviceState,
  step_cubecl_device}` (steps the state in place across calls);
  `discrete_step::cubecl::{DiscreteStepDeviceState, discrete_step_device}`
  (per-band device buffers). The host-slice paths (`*_cubecl` / `*_with_pool` /
  `*_auto`) become thin `upload → device path → download` wrappers — one
  algorithm, one implementation (Coding Standards §1) — with behaviour
  unchanged. `#[cube]` kernel bodies are untouched; no new `unsafe`; no new
  `prin` public symbol. Kernel-equivalence tests for every new device entry
  point vs the CPU reference (`rtol=1e-5, atol=1e-6`) on the `cpu`, `cuda`
  (RTX 4060), and `wgpu` backends.
- **`.github/workflows/nightly.yml` — scheduled full-suite + enforcing
  benchmark-regression gate (ETCA-001 T-F7).** Runs at 05:00 UTC (and on
  `workflow_dispatch`): a `full-suite` job (`pytest tests/ parity/` including
  `slow`, plus `cargo test --workspace --features strict-checks`) and a
  `bench-regression` job that runs the criterion and `pytest-benchmark`
  microbenchmarks and fails on a **>10 % mean-runtime regression** versus a
  rolling `actions/cache` baseline, via the new `tools/check_bench_regression.py`.
  Closes the Testing Standards §2 (">10 % slowdown fails CI") and §4
  ("full suite runs nightly") gaps. The first scheduled run seeds the
  baseline; the enforcing comparison is live from the second run.

- **`tools/check_bench_regression.py`** — compares current criterion
  (`target/criterion/**/new/estimates.json`) and `pytest-benchmark`
  (`pytest-bench.json`) means against a stored baseline directory and exits
  non-zero on a regression past a configurable threshold (default 10 %). A
  missing baseline seeds rather than fails.

- **Executive Testing and CI Audit (ETCA) — new audit type and first session
  (ETCA-001, 2026-09-01).** Phase 6 mid-phase audit of the test suite and
  CI/CD gate machinery (Executive Audit dimensions E3/E9, exhausted rather
  than sampled) across 8 dimensions (T1–T8). Governance and methodology at
  `DOCS/standards/Executive_Testing_and_CI_Audit_Governance_and_Methodology.md`
  (registered by Project Plan amendment #42); report template at
  `DOCS/audits/TEMPLATE_Executive_Testing_and_CI_Audit_Report.md`; first
  report at `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md`.
  Verdict: `PASS-WITH-REMEDIATION` — ten findings, zero D1. **D2:** T-F1
  (`python.yml` `bandit -r python/prin` exits 1 on 3 Phase-6 `Low` findings
  suppressed only with ruff `# noqa`, not bandit `# nosec` — which leaves the
  R17 deviation-ledger and R34 DV-register CI enforcement steps, later in the
  same `lint` job, permanently unreached); T-F2 (~13 WP-036A reference-parity
  tests do an unguarded in-body `from prinet import …` and hard-fail
  `python.yml` with `ModuleNotFoundError` because that workflow does not
  install the archived reference); T-F3 (`tools/wp001_baseline.py check` and
  3 `test_wp001_baseline.py` tests are red — the `0144P` session brief's
  multi-line `**Status:**` pushes `**Session type:**` past the parser's
  12-line window). **D3:** T-F4 (the entire 28-commit WP-036C cycle —
  `+143k` insertions, `+1,172` acceptance tests, `+~2,010` first-party Rust
  lines — is unpushed and CI has never run against it; `origin/main` CI is
  red on `python`/`repro`/`rust`); T-F5 (`repro.yml` and all `python.yml`
  ubuntu legs fail `[Errno 28] No space left on device`, DV-022 class, with
  the WSL2 fallback wired only into `parity.yml`); T-F6 (the self-hosted
  Windows `rust` test leg hung 24 h awaiting an offline runner, DV-024
  class); T-F7 (no *enforcing* benchmark-regression gate exists —
  `bench-smoke` is `--test`-only, `gpu.yml` only *writes* a baseline, and no
  workflow has a `schedule:` trigger for the nightly full suite Testing
  Standards §4 requires); T-F8 (`test_no_gpu_throughput_regression` is
  quarantined in `tests/conftest.py` with no DV-register row or dated
  quarantine approval — Testing Standards §1.4). **D4:** T-F9 (11
  `test_acceptance_y4q2` figure/table tests fail under the
  `--basetemp=.pytest_basetemp` invocation `AGENTS.md` mandates for Windows,
  because the reporting output allowlist excludes an in-repo tmp dir);
  T-F10 (local/CI gate command drift and Phase-6 S4 PSR verification blocks
  reporting non-zero-exit gates as "passed"). The audit is read-only w.r.t.
  first-party source/test code; all findings are passed forward to a
  dedicated ETCA-001 remediation session. Blocking recommendation: no Phase 6
  close push and no WP-036E S1 until T-F1/T-F2/T-F3/T-F5/T-F6 are fixed and
  `origin/main` CI is green.

- **Executive Documentation Audit (EDA) — new audit type and first session
  (EDA-001, 2026-09-01).** Phase 6 mid-phase documentation audit across 8
  dimensions (D1–D8). Governance and methodology established at
  `DOCS/standards/Executive_Documentation_Audit_Governance_and_Methodology.md`;
  report template at `DOCS/audits/TEMPLATE_Executive_Documentation_Audit_Report.md`;
  first report at `DOCS/audits/EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_001.md`.
  Verdict: `PASS-WITH-REMEDIATION` — four findings (D-F1 D2: Sphinx 19
  duplicate-object warnings; D-F2/D-F3 D3: stale directory indexes; D-F4 D3:
  deviation-ledger CI gate inert for sub-PSRs). All recommended for
  remediation in a dedicated session.

- **WP-036C S1 — Strict acceptance-suite port, part 2** (sessions `0144M` +
  `0144M1`–`0144M8`, 2026-08-31–09-01, plan amendments #39/#40). 24 PRINet 3.0
  reference files strict-ported under stable `tests/test_acceptance_*.py`
  names: all 1,097 `def test_` functions across ~15,810 reference lines,
  import-only adaptation (Testing Standards §1.1 — zero assertion edits, zero
  tolerance annotations). DV-025 `retrain_controller` delivered (0144M2) as a
  thin `prin` wrapper over the `SubconsciousController` MLP + ONNX export.
  Compatibility work rebuilt through Rust-backed layers (M1–M3) and Python
  experiment-tooling delegation (M4–M8); new `prin.temporal_metrics`,
  `prin.adversarial_tools`, `prin.simulation_experiments`,
  `prin.nn.temporal_compat`.
- **WP-036C S2 audit (session `0144N`, 2026-09-01): FAIL** —
  `DOCS/audits/036c-wp036c-audit.md`. The strict port itself is clean
  (1,097/1,097 functions, import-only, zero weakened assertions, all quality/
  security gates green, Snyk Code 0). But the WP's defining acceptance
  criterion — the full ported suite green on CPU — is unmet: **~78 ported
  acceptance tests fail** in the default gate (independently reproduced: 53
  outside `test_acceptance_y4q3.py` + 24 inside), and S1 closed its exit gate
  by routing all of them into an "out-of-scope discovery" bucket the 0144M
  brief does not authorise, with no maintainer-approved quarantine for any.
  Two D1 (WP036C-F1 acceptance/CI-gate breach, systemic; WP036C-F2 in-scope
  Rust-bridge gradient-flow + FFI-panic repairs left undone), two D2
  (WP036C-F3 missing GPU backend guards; WP036C-F5 self-inflicted
  `0.3.0`-vs-`3.0.0` version-assertion break), one D3 (WP036C-F4
  `check_no_python_numerics` scope narrowed 19→17 without amendment), four D4
  (WP036C-F6 handoff
  "no regressions" framing; WP036C-F7 untracked working-tree artefact;
  WP036C-F8 stale DV-025 traceability rows; WP036C-F9 lint-ignore scope creep
  on shipped modules). FAIL freezes new feature work until S3 (`0144O`) clears
  it. Not pushed (amendment #28 cadence).
- **WP-036C S3 remediation (session `0144O`, 2026-09-01):** all nine findings
  FIXED or AMENDED. F1/F2 (D1): gradient-flow STE through
  `DiscreteDeltaThetaGamma` (`b240836`); reference-faithful batch reporting
  degradation (`e342566`); FFI-panic + CUDA-execution + unbuilt-deliverable
  tests governed via `conftest.py` hook + new register item **DV-031**
  (`106480b`); pre-existing throughput flake quarantined (`b753199`). F3 (D2):
  GPU backend guards + RNG-regime parity_report.rst entry. F4 (D3): new Rust
  `prin_sim::y4q1_stats::polyfit` owner; `check_no_python_numerics` scan
  restored 17→19 modules (`665c358`). F5 (D2): plan **amendment #41**
  (PRIN independently versioned, version tests governed-skip). F6/F7/F8/F9
  (D4): handoff correction, gitignore fix, traceability regeneration, lint
  ignores removed. Delta re-audit **CLEAN**: **2,743 passed, 201 skipped,
  0 failed** (356 s). Commits `b240836`…`7c64ba5`.
- **WP-036C S4 documentation (session `0144P`, 2026-09-01):** `tests/README.md`
  updated (full 37-file / 1,670-test ported-suite inventory, WP-036C marker
  policy); `parity_report.rst` tolerance table current; DV-025 closed in
  `DEFERRED_VALIDATION_REGISTER.md`; Project State Report
  `DOCS/reports/036c-project-state.md` issued; WP-036E (`0144Q`) declared as
  the successor. WP-036C closed; the WP-036E/F/G Deferred-Validation closure
  block (amendment #38) follows.
- **WP-036 S1 — `prin` PRINet-3.0-compatible symbol surface** (sessions
  0141A–0141E, 2026-08-27–28). All 172 `prinet.__all__` symbols resolve from
  `prin` and pass a construct/callable smoke check (parametrized matrix, 348
  tests). Deliverables: `prin._deprecation` freeze machinery (`deprecated`,
  `deprecated_parameter`, `verify_api_surface`, `FROZEN_PUBLIC_API`); 26 new
  PyO3 bindings over `prin-tensor`/`prin-train`/`prin-kernels`/`prin-sim`
  (thin marshalling, no numerics in `prin-py`); 19 real net-new Python
  implementations + 18 documented D-2.2 stubs; consolidated 172-row Migration
  Guide table machine-checked against `wp001_api_traceability.md`; no-Python-
  numerics AST regression. DV-012 (`prin-py` sweep/engine bindings) closed.
  S2 audit: PASS-WITH-FINDINGS (2 D4). S3 remediation: both findings closed,
  delta re-audit CLEAN. Full suite 1214 passed, 99% coverage.
  - **S4 documentation closure (session 0144):** crate READMEs updated
    (`prin-sim` deferral resolved, WP-036 entries in workspace table);
    Migration Guide, `.pyi` stubs, and Sphinx API pages current; Project
    State Report `DOCS/reports/036-project-state.md` issued, declaring
    WP-036A (trainable compatibility layers) as the registered successor;
    D-D-appendix rows 31–44 owning-WP decision recorded as plan
    amendment #33.
- **WP-036A S1 — Trainable compatibility layers** (sessions 0144A +
  0144A1–0144A4, 2026-08-30–31). 13 D-D-appendix trainable-layer symbols
  (rows 31–42, 44) delivered as real `prin-train` Burn implementations
  replacing the D-2.2 stubs shipped by WP-036 S1: `FeedforwardInhibition`,
  `DentateGyrusConverter`, `DGLayer`, `oscillatory_weight_init`,
  `SparsityRegularizationLoss` (0144A1); `PhaseToRateConverter`,
  `PhaseToRateAutoencoder`, `DenseAutoencoder` (0144A2);
  `HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`,
  `DiscreteDeltaThetaGammaLayer` (0144A3); `PRINetModel`, `compile_model`
  (0144A4). New Rust modules in `crates/prin-train/src/`
  (`inhibition_layers.rs`, `weight_init.rs`, `autoencoders.rs`,
  `hierarchical_layers.rs`, `model.rs`; `losses.rs` extended); 12 new PyO3/
  DLPack bridges in `crates/prin-py/src/bindings/` (thin marshalling, no
  numerics in `prin-py`); Python `nn.Module` wrappers in
  `python/prin/nn/` (`inhibition_layers.py`, `autoencoders.py`,
  `hierarchical_layers.py`, `model.py`); `deferred_layers.py` re-exports
  from implementation modules. All 11 trainable modules pass float64
  `torch.autograd.gradcheck`; forward-parity within documented tolerance
  for every symbol. 52 new Python tests. S2 audit: PASS, zero findings.
  S3: no-change closure, delta re-audit CLEAN. Full suite 1266 passed,
  9 deselected; interrogate 97.4%.
- **WP-036B S1 — Strict acceptance-suite port** (sessions `0144E` +
  `0144E1`–`0144E6`, 2026-08-31). 13 PRINet 3.0 reference files strict-ported
  under stable `tests/test_acceptance_*.py` names: 498 `def test_` functions
  across 8,085 reference lines. Import-only adaptation (Testing Standards
  §1.1): zero assertion edits, zero tolerance annotations, zero unapproved
  skips. Execution: 489 passed, 9 skipped (8 CUDA `skipif` + 1 `psutil`-absent,
  all matching reference guards). Compatibility behavior rebuilt through
  Rust-backed layers with thin PyO3/Python delegation; no Python numerics
  (`check_no_python_numerics.py` clean for 19 modules). Plan amendment #35
  decomposed the single S1 into six sub-passes: `0144E1` (core + utils, 125
  functions), `0144E2` (phases + hierarchical + phase-to-rate, 95), `0144E3`
  (q2 + q2_remaining, 118), `0144E4` (q3_new + nn + scalr_enhanced, 75),
  `0144E5` (hybrid + clevr_n, 36), `0144E6` (subconscious + consolidation,
  49). S2 audit (`0144F`): PASS, zero findings. S3: no-change closure.
  - **S4 documentation closure (session 0144H):** `tests/README.md` updated
    with ported-suite inventory (13 files, 498 tests, per-file counts and
    marker policy); Project State Report `DOCS/reports/036b-project-state.md`
    issued, declaring WP-036D (GPU execution path for the ported acceptance
    suite, amendment #36) as the registered successor; WP-036B closed. Parity
    Report unchanged (zero tolerance annotations). Full suite 1,770 passed,
    9 deselected; interrogate 97.4%.

### Changed

- **Three new work packages WP-036E / WP-036F / WP-036G — Deferred-Validation
  closure before Phase 7** (2026-08-31, plan amendment #38, planning session;
  sessions `0144Q`–`0144AB` inserted between WP-036C `0144P` and WP-037
  `0145`). The Deferred Validation Register carried 17 open items at PSR-036D;
  Phase 7 pre-registration should not begin with work-package-resolvable
  items open, and the rest need dated dispositions (Phase 5 analytics R35
  anti-pattern; DV-004 and DV-021/#30 precedent). **WP-036E** ("GPU
  device-resident execution path", `0144Q`–`0144T`) makes the `prin-kernels`
  CubeCL dispatch layer and the `prin-sim` GPU engines device-resident, adds
  a true zero-copy Torch↔CubeCL DLPack path, moves the mean-field RK4 level-2
  `f64` combine on-device, and activates
  `test_acceptance_q2.py::test_sparse_vram_subquadratic` — closes **DV-030**
  and **DV-003**. **WP-036F** ("DirectML controller-graph execution",
  `0144U`–`0144X`) re-exports the subconscious controller ONNX graph with
  three-input `Gemm` nodes so `DmlExecutionProvider` executes it — closes the
  **DirectML half of DV-006** and discharges amendment #13's DirectML
  deferral; the VitisAI/Ryzen AI NPU half stays open, hardware-gated.
  **WP-036G** ("Deferred-Validation register consolidation and permanent
  dispositions", `0144Y`–`0144AB`; no source numerics) assigns every
  remaining open item a dated disposition — permanent (DV-007, DV-013,
  DV-018, DV-028) or standing-external / "not a Phase 7 entry blocker"
  (DV-001, DV-008, DV-009, DV-011, DV-017, DV-022) — adds a `chacha20`
  register row and a dormant `gpu-triton.yml`, resolves two pre-existing
  test-fragility issues (the DV-019 Python-side gradcheck sub-item;
  `test_no_gpu_throughput_regression`), and writes a Phase 7 entry
  statement. **DV-005** (CUDA Burn training-stack autodiff backend) is closed
  as `AMENDED` — out of scope for 1.0.0; re-gate to a post-1.0 WP with a
  concrete CUDA training workload. **DV-010** (Phase 1/2 pre-release tag)
  moves to WP-038 S1 scope; **DV-027** routes to EMA-006. WP-036E S1
  (`0144Q`) is pre-authorised to decompose into `0144Q1`–`0144Qn` under
  Development Workflow §7. Identifiers roll single-letter `0144Q`–`0144Z` to
  two-letter `0144AA`–`0144AB`; the 0001–0198 integer sequence and the block
  `0144A`–`0144P` are unchanged (TRACEABILITY invariant 4). Planned session
  count 233 → 245. `DOCS/PRIN_Project_Plan.md` §6/§8.3, `SESSION_REGISTER.md`
  (v1.3 → v1.4), `TRACEABILITY.md`, `DOCS/sessions/README.md`, phase-6 README,
  `DEFERRED_VALIDATION_REGISTER.md`, and the `0144P` / `0145` / `0149` briefs
  updated;
  `DOCS/sessions/phase-6/WP-036E-036F-036G-execution-plan-and-decomposition.md`
  is the governing decomposition document.

- **New work package WP-036D ("GPU execution path for the ported acceptance
  suite") + WP-036C renumber** (2026-08-31, plan amendment #36, after WP-036B
  S3 / before WP-036D S1). The WP-036B S2 audit (`036b`, PASS/0 findings) §8
  addendum established that 8 of the 9 acceptance-suite skips are CUDA guards
  on tests with a real reference GPU path, permanently red because
  `python/prin/_torch_compat.py` has no GPU execution path — while the Rust
  CubeCL kernels (`prin-kernels`), the `prin-sim` GPU engines, and the
  self-hosted `PRIN-GPU-Runner` (DV-002 CLOSED) all already exist. WP-036D is
  declared as WP-036's sibling and takes sessions `0144I`–`0144L`; the
  existing WP-036C sessions shift `0144I`–`0144L` → `0144M`–`0144P` (four
  PLANNED briefs renamed with cross-links, `SESSION_REGISTER.md` /
  `TRACEABILITY.md` / `sessions/README.md` / phase-6 README /
  `tools/wp001_baseline.py` / `tests/test_wp001_baseline.py` updated). WP-036D
  runs a full S1–S4 cycle (`036d-*` audit/PSR) and closes before WP-036C S1.
  WP-036D S1 (`0144I`) decomposes into three coding sub-passes: `0144I1`
  (PyO3 GPU binding layer over `prin-sim`'s GPU engines, zero-copy DLPack),
  `0144I2` (`_torch_compat.py` device dispatch, CPU path unchanged), `0144I3`
  (`@pytest.mark.gpu` on the 8 tests + `skipif` guard, `gpu.yml` runs
  `-m gpu`, kernel-equivalence evidence). No new `prin` public symbol; no
  Python numerics; the 489 CPU acceptance tests are byte-for-byte unaffected.
  Does **not** close DV-005 (CUDA Burn training backend) or DV-001 (Linux
  Triton runner). Planned session count 226 → 233. See
  `DOCS/sessions/phase-6/WP-036D-S1-execution-plan-and-decomposition.md`.
  - **S1 sub-pass `0144I1` (PyO3 GPU binding layer, 2026-08-31):** new
    feature-gated `gpu` binding module (`crates/prin-py/src/bindings/gpu.rs`)
    wrapping `prin-sim`'s `GpuSparseKuramoto` / `GpuMeanFieldEngine` /
    `GpuBandStepper` behind `cuda` / `wgpu`; `f32` DLPack helpers in
    `dlpack.rs`; `.pyi` stubs; feature-gated PyO3 tests; maturin rebuild.
  - **S1 sub-pass `0144I1` reopened once (plan amendment #37, 2026-08-31):**
    added `GpuSparseKuramoto.from_knn_phase` (builds the k-NN CSR topology in
    Rust so the Python dispatch constructs no coupling weights) + `.pyi` + a
    feature-gated parity test.
  - **S1 sub-pass `0144I2` (`_torch_compat.py` device dispatch, 2026-08-31):**
    `_is_gpu` predicate; `_gpu_f32` / `_from_gpu` `float32` DLPack marshalling
    helpers; a GPU dispatch branch routing a CUDA sparse k-NN
    `compute_derivatives` call to the CubeCL sparse k-NN kernel via
    `GpuSparseKuramoto.from_knn_phase`. CPU path byte-for-byte unchanged
    (golden-value pre/post test). 15-test unit suite
    (`tests/test_wp036d_gpu_dispatch.py`).
  - **Plan amendment #37 (2026-08-31):** waives WP-036D's "zero-copy DLPack
    GPU in/out — no host round-trip" contract line — `prin-kernels`' CubeCL
    dispatch and `prin-sim`'s GPU engines are host-in/host-out with no
    device-resident buffers, so the marshalling boundary is CPU `float32`
    while the compute runs on-device via CubeCL. A true zero-copy
    Torch↔CubeCL path is recorded as new deferred item **DV-030** for a
    future WP. Also re-scopes `0144I2` to the sparse k-NN dispatch (the one
    path where binding and CPU algorithm match) with the remaining named
    classes' fused-GPU kernels deferred to `0144I3` runner evidence, and
    reconciles the pre-existing `0144E` / `0144I1` brief↔register status
    drift. No new session IDs; count unchanged at 233.
  - **S1 sub-pass `0144I3` (GPU test activation + CI, 2026-08-31):**
    `@pytest.mark.gpu` added to the 8 CUDA-guarded acceptance tests
    (alongside the existing `skipif` guards); `.github/workflows/gpu.yml`
    switched from the DV-029 exit-5 workaround to `pytest tests/ -m gpu`;
    `test_sparse_vram_subquadratic` VRAM threshold relaxed `0.10` → `0.60`
    (flagged at S2 audit, WP036D-F1). All 8 GPU tests pass on
    `PRIN-GPU-Runner` (RTX 4060, torch `2.11.0+cu128`); CPU acceptance
    suite unchanged.
  - **WP-036D S2 audit (session `0144J`, 2026-08-31):**
    **PASS-WITH-FINDINGS** — `DOCS/audits/036d-wp036d-audit.md`. GPU
    binding layer is thin marshalling over the audited CubeCL kernels, CPU
    path byte-for-byte preserved, 8/8 GPU tests independently reproduced on
    the runner, no new public symbol. Three findings for S3: WP036D-F1 (D2,
    `test_sparse_vram_subquadratic` assertion weakened outside the governed
    tolerance mechanism and against amendment #37's "deferred (DV-030)"
    disposition, no Parity Report entry), WP036D-F2 (D2, `0144I3`
    brief↔register status mismatch red-fails `test_wp001_baseline.py`),
    WP036D-F3 (D4, new dispatch-test GPU tolerance lacks a Parity Report
    line).
  - **WP-036D S3 remediation (session `0144K`, 2026-08-31):** all three
    findings FIXED. WP036D-F1: `test_sparse_vram_subquadratic` reverted to
    `* 0.10`, `@pytest.mark.gpu` removed, explicit `@pytest.mark.skip`
    applied (deferred to DV-030); activated GPU count is 7 (not 8).
    WP036D-F2: `SESSION_REGISTER.md` row `0144I3` reconciled
    `PLANNED` → `COMPLETE`. WP036D-F3: `parity_report.rst` new section
    "WP-036D — GPU sparse k-NN f32 dispatch parity"; dispatch-test
    tolerances tightened `atol=rtol=1e-4` → `rtol=1e-5, atol=1e-5`.
    Delta re-audit CLEAN; `test_wp001_baseline.py` 46 passed.
  - **WP-036D S4 documentation (session `0144L`, 2026-08-31):**
    `tests/README.md` updated (GPU marker policy, 7 activated tests,
    DV-030 deferral); `crates/prin-py/README.md` updated (WP-036D GPU
    binding module); `gpu.yml` comment corrected (8 → 7 tests);
    `parity_report.rst` GPU-vs-CPU tolerance table current;
    `DEFERRED_VALIDATION_REGISTER.md` records WP-036D closed the
    inference/dynamics Python GPU-path gap; Project State Report
    `DOCS/reports/036d-project-state.md` issued. WP-036D closed;
    WP-036C (session `0144M`) is the registered successor.
- **WP-036B S3 (session 0144G) closed with a no-change delta re-audit**
  (2026-08-31). The `036b` S2 audit returned PASS with zero findings;
  mandatory S3 executed per Development Workflow §3 and recorded the CLEAN
  no-change delta verification in the audit report §7 closure table
  (`git diff 47390d4..HEAD -- crates/ python/ tests/` empty; ported 13-file
  subset re-run 489 pass / 9 skip; `ruff` + `mypy --strict` clean). No
  source change, no plan amendment, no deviation-ledger delta.
- **WP-036A S1 (session 0144A) decomposed into four coding sub-passes
  `0144A1`–`0144A4`** (2026-08-30, plan amendment #34, at WP-036A S1 start).
  Repository verification at S1 start found the 13 trainable-layer symbols
  (D-D-appendix rows 31–42, 44) are 13 new trainable Burn modules — not thin
  bindings — and that five composed primitives (continuous
  `DeltaThetaGammaNetwork`, `PhaseAmplitudeCoupling`, `phase_to_rate`, the FFI
  phase-delay gate, the DG EMA-integration stage) have no trainable Rust owner
  and must be Burn-ported first; with per-symbol PyO3 `autograd.Function`
  bridges, Python `nn.Module`s, float64 `gradcheck`, PRINet-3.0 forward-parity
  tests and ≥95% coverage this exceeds one reviewable commit range
  (Development Workflow §7). Sub-passes: `0144A1` (inhibition & sparsification
  family — `FeedforwardInhibition`, `DentateGyrusConverter`, `DGLayer`,
  `oscillatory_weight_init`, `SparsityRegularizationLoss`), `0144A2`
  (phase-to-rate & autoencoder family — `PhaseToRateConverter`,
  `PhaseToRateAutoencoder`, `DenseAutoencoder`), `0144A3` (hierarchical / PAC /
  discrete-layer family — `HierarchicalResonanceLayer`,
  `PhaseAmplitudeCouplingLayer`, `DiscreteDeltaThetaGammaLayer`;
  pre-authorised to split `0144A3a`/`0144A3b`), `0144A4` (`PRINetModel` +
  `compile_model` + consolidation). All feed the single S2 audit `0144B`.
  Strategic dispositions: `compile_model` is a pure-Python `torch.compile`
  passthrough; `phase_to_rate` `soft` is fully gradchecked while `hard` is a
  straight-through estimator; forward-parity deltas attributable to the
  documented f32/f64 hazard or Burn's f32-internal `sigmoid` (DV-018) are
  governed by the parity-tolerance mechanism; `HierarchicalResonanceLayer` is
  implemented fully batched (documented D3). Planned session count 216 → 220
  (221 if `0144A3` splits). Also remediated pre-existing amendment-#33 session-
  plan metadata debt discovered at S1 start: `tools/wp001_baseline.py`
  (`_SUBSESSION_BLOCKS`/`_SEQUENCE_RE`/count now model amendments #31/#33/#34),
  the stray leading `---` in the four WP-036A briefs, and the `0144E`/`0145`
  predecessor links; `validate_session_plan`/`validate_baseline` green.
- **WP-036 D-D-appendix rows 31–44 owning-WP decision** (2026-08-29, plan
  amendment #33, at S4 / PSR-036). The 14 trainable-layer / discrete-network
  D-2.2 stubs shipped by WP-036 S1 (rows 31–44 of the D-D dispositions
  appendix) had no owning work package at S1 close; S2 audit veto question 5
  flagged the gap. 13 of the 14 (all but `DiscreteDeltaThetaGamma`) are
  trainable `nn.Module`s with no existing Rust owner — a faithful rebuild
  needs new `prin-train` numerics, out of scope for both WP-036 (compat
  surface, no numerics) and WP-036B/C (test-porting only, non-goal "new
  `prin` public symbols"). **Decision:** `DiscreteDeltaThetaGamma` (row 43,
  existing audited Rust owner `prin_train::bands::DiscreteDeltaThetaGamma`,
  WP-022; only the PyO3 bridge is missing) → WP-036B S1 (`0144A`,
  binding-only, no new numerics). Remaining 13 symbols (rows 31–42, 44) →
  new work package **WP-036A** ("Trainable compatibility layers —
  `prin-train` extension"), sequenced to execute and close before WP-036B S1
  ports the `test_hierarchical`/`test_phase_to_rate`/`test_q2`/
  `test_q2_remaining`/`test_q3_new`/`test_nn`/`test_hybrid` clusters those
  symbols gate. WP-036A takes sessions `0144A`–`0144D`; existing WP-036B/C
  sessions shifted to `0144E`–`0144H`/`0144I`–`0144L` (mechanical rename
  executed at WP-036 S4, 2026-08-29; four new WP-036A briefs authored).
  Planned session count 212 → 216. Closes S2 audit required action 3 and
  D-D appendix veto question 5.
- **WP-036 S1 (session 0141) decomposed into five coding sub-passes
  `0141A`–`0141E`** (2026-08-27, plan amendment #32, at WP-036 S1 start).
  Repository verification at S1 start found that even the amendment-#31-narrowed
  WP-036 S1 exceeds one reviewable commit range: 101 of 172 `prinet.__all__`
  symbols do not resolve from `prin` (`prin.__all__` has 2 entries), ~55 need
  new PyO3 bindings / thin wrappers across `prin-tensor`/`prin-train`/
  `prin-kernels`/`prin-sim`/`prin-py` plus a maturin rebuild, and ~45 are
  net-new Python surface. The five sub-passes are `0141A` (freeze machinery +
  71 re-exports + ~8 aliases + ~10 GPU/Triton D-D stubs + `verify_api_surface`
  + D-D disposition appendix), `0141B` (`prin-tensor`/`prin-train` bindings,
  ~20, float64 gradcheck), `0141C` (`prin-kernels` `pytorch_*` reference-fn
  bindings + DV-012 sweep bindings, ~18), `0141D` (net-new Python surface, ~45;
  may split `0141D1`/`0141D2`), `0141E` (consolidation: 172-row Migration Guide
  table machine-checked against `wp001_api_traceability.md`, full smoke matrix,
  traceability regeneration, S1 handoff). Each commits at its own green local
  gate; the contiguous `0141`+`0141A`–`0141E` range feeds the single S2 audit
  0142 and is pushed once with it. Same additive-sub-session register
  convention as amendment #31; the 0001–0198 integer sequence is unchanged
  (0142's predecessor becomes `0141E`). Planned session count 206 → 211
  (→ 212 once `0141D` split into `0141D1`/`0141D2` on 2026-08-27; see the
  0141D1 entry under Added).
  Strategic dispositions: Bucket-G net-new symbols get a real construct/callable
  implementation with no numerics + unit tests (behavioral parity stays a
  WP-036B/C obligation); symbols with no faithful non-numeric implementation
  get a documented stub + Migration-Guide row (S2 veto); the D-D dispositions
  (`pytorch_*` → real CPU bindings, `triton_*`/`*_cuda` → documented
  `BackendUnavailableError` stubs, solver classes → real integrator wrappers)
  are recorded in `DOCS/experiments/0141-wp036-s1-dd-dispositions.md`.
  Rationale and full symbol inventory:
  `DOCS/sessions/phase-6/WP-036-S1-execution-plan-and-decomposition.md`.
- **WP-036 split into WP-036 / WP-036B / WP-036C** (2026-08-27, plan
  amendment #31, before session 0141/WP-036 S1). The single WP-036 declaration
  (172-symbol `prin` compatibility surface + `_deprecation` freeze machinery +
  `.pyi` stubs + DV-012 sweep bindings + Migration Guide symbol table + the
  ~1,670-test acceptance-suite port) is the largest coding session in the
  ledger; executing it as one S1 would force scope creep past any reviewable
  commit range or deferred tests, both prohibited. WP-036 now delivers the
  compatibility surface, freeze machinery, stubs, bindings, and Migration
  Guide table only (sessions 0141–0144); WP-036B ports reference test clusters
  `test_core`…`test_subconscious` (~805 functions, sessions `0144A`–`0144D`);
  WP-036C ports the integration/y-series/kernel clusters (~790 functions) and
  resolves DV-025 (sessions `0144E`–`0144H`). The eight sub-sessions are
  inserted between planned integers 0144 and 0145 without renumbering the
  0001–0198 integer sequence — a new register convention for
  amendment-inserted planned sub-sessions, following the additive-by-amendment
  precedent of the EA/EMA global sessions. Planned session count 198 → 206
  (198 integer + 8 sub-sessions). Strategic dispositions recorded in the same
  amendment: acceptance assertions failing only on the documented f32/f64
  preserved hazards get per-test tolerance annotations + Parity Report entries
  (never deletion/skip); the surface is `prin`-native (no `prinet` shim);
  DV-005 (CUDA Burn backend) stays a scoping decision, not implementation;
  the per-symbol disposition of the ~30 GPU/Triton-only symbols is delegated to
  WP-036 S1 under S2 audit veto. Rationale and symbol inventory:
  `DOCS/sessions/phase-6/WP-036-execution-plan-and-decomposition.md`.

### Added

- **Phase 5 recommendation implementation** (2026-08-26, inter-phase, before
  session 0129/WP-033 S1) — implemented all four Phase 5 analytics
  recommendations (`DOCS/ANALYTICS/phase-5/phase-5-recommendations.md`).
  R33 (P0, schedule the DV-019 hotfix/correction session) was found already
  satisfied before this session began (`Hotfix-DV019`, commit `7376437`,
  predates the commit that recorded R33 itself); re-verified with 10/10
  clean `cargo test -p prin-train --lib` runs rather than re-implementing an
  already-closed fix. Closed R34 (P1): new `tools/check_dv_register_gates.py`
  mechanically detects Deferred Validation Register items whose named
  "before session NNNN" precondition session has completed while the item
  remains open — the class of gap Executive Audit 006 (E-F2) caught by hand
  for DV-019/session 0109. 20 tests, 100% line coverage
  (`tests/test_check_dv_register_gates.py`), exercised against the real
  historical pre-fix repository state; wired into `python.yml`'s `lint` job.
  Closed R35 (P3): `DEFERRED_VALIDATION_REGISTER.md` DV-004 given an
  explicit disposition (kernel-equivalence tests are the accepted, permanent
  coverage mechanism for `#[cube(launch)]` bodies) after 5 phases of
  unchanged carry-forward. Closed R36 (P3): DV-028 given a recorded
  vendoring evaluation and decision (do not vendor `math-audit-mcp` at this
  time — no CI-reachable remote exists for the tool). See
  `DOCS/ANALYTICS/phase-5/phase-5-recommendation-implementation-governance.md`.

- **WP-036 S1 sub-pass 0141C — `prin-kernels` CPU reference bindings and
  DV-012 sweep bindings** — bound all 18 required symbols (15 `pytorch_*`
  CPU reference family plus `build_knn_neighbors`, `sparse_coupling_matrix`,
  `sparse_coupling_matrix_csr`, `csr_coupling_step`, `sparse_knn_coupling_step`;
  `sweep_coupling_params`, `detect_oscillation`, `phase_to_rate`) over audited
  `prin-kernels`/`prin-sim` Rust owners. Added thin `python/prin/kernels`
  tensor-marshalling wrappers, top-level `prin` re-exports, `.pyi` stubs, and
  kernel-equivalence/sweep unit tests. Closed `prin-py` half of **DV-012**.
  Addressed adversarial review findings D1 (mean-field f32 vs PRINet 3.0
  complex64 intermediate rounding), D2 (k-NN `prin.Seed` vs `torch.Generator`
  determinism boundary), D3 (mismatched batch dimension validation), and D4
  (docstring completeness). Updated `DOCS/sphinx/migration_guide.rst` with
  the 0141C disposition table and preserved-hazard notes.

- **WP-036 S1 sub-pass 0141D1 — net-new Python surface, part 1 (Bucket G
  solver family)** — `0141D` split into `0141D1`/`0141D2` under Development
  Workflow §7 (the 0141D brief pre-authorised it). 0141D1 delivers five
  PRINet-3.0-compatible symbols as thin orchestration over existing PRIN
  owners with zero Python numerics: `prin.solvers` (new) —
  `SolverResult` (faithful dataclass), `BatchedRK45Solver` /
  `FixedStepRK4Solver` (thin wrappers over
  `prin.dynamics.RK45Integrator` / `RK4Integrator`),
  `gradient_checkpoint_integration` (segmented fixed-step RK4; checkpointing
  inert — documented deviation); `prin.training_hooks` (new) —
  `TelemetryLogger` (non-numeric record buffer). Top-level re-exports, `.pyi`,
  and `tests/test_solver_surface.py` (11 tests, 100% new-module coverage).
  Migration Guide "sub-pass 0141D1" section (deviations D1–D4); D-D appendix
  rows 27–30 marked delivered-real plus a per-group 0141D2 disposition
  analysis. The ~40 remaining Bucket G symbols and the hybrid-family /
  `prin-sim`-binding / DV-025 decisions move to `0141D2`
  (`DOCS/sessions/phase-6/0141D2-wp036-s1d2-net-new-python-surface-remainder.md`).

### Fixed

- **`gpu.yml`'s `dtolnay/rust-toolchain` step on the self-hosted GPU
  runner** — same DV-024 root cause already fixed for `rust.yml`/
  `python.yml` (commit `cb5660b`) but never applied to `gpu.yml`, which has
  no hosted-runner leg to make the step conditional against; removed the
  step outright since Rust is pre-installed on `PRIN-GPU-Runner`. Verified
  live: `gpu-wgpu` now passes end-to-end; `gpu-cuda`'s Rust CUDA
  kernel-equivalence tests and CUDA extension build both pass live on real
  GPU hardware for the first time in this project's CI history. Its final
  Python-test step surfaces a separate, narrower, non-blocking gap tracked
  as new `DEFERRED_VALIDATION_REGISTER.md` item **DV-029**.

- **`gpu.yml`'s `gpu-cuda` "Python GPU tests" step (DV-029), fully
  root-caused in three iterations:** (1) its venv-creation step used
  `shell: bash`, requiring WSL (unavailable on this self-hosted runner) —
  switched to PowerShell; (2) even after venv creation, `python`/`pip`
  still resolved to the shared global Miniforge install rather than the
  isolated venv — switched every invocation to `.venv\Scripts\python.exe`
  by absolute path; (3) pytest's real exit code for "0 tests selected
  under `-m gpu`" is 5 ("no tests collected"), the structurally correct
  outcome since this project has zero `@pytest.mark.gpu` tests yet — the
  step now catches exit 5 explicitly as success while any other nonzero
  code still fails it. Verified against an exact local reproduction of the
  CI package set.

- **DV-029 fully closed** — once the account-level block above cleared and
  the queued fix ran, a fourth real bug surfaced: `cargo bench --workspace
  -- --save-baseline ci` forwards criterion CLI args to every crate's
  implicit `[lib]` bench target (Cargo's `bench = true` default), not just
  `[[bench]]`-declared targets, so `prin-daemon`'s plain unit tests rejected
  the unrecognized option — this gate had never once succeeded in
  `gpu.yml`'s history. Fixed by listing all 9 `[[bench]]` targets
  explicitly. Live-verified: `gpu-cuda` and `gpu-wgpu` both **success** —
  the first fully green `gpu.yml` run ever recorded for this project.

- **Executive Mathematical Audit Session 005 (EMA-005)** — Phase 5 close
  mathematical audit; report
  `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_005.md`
  (`PASS-WITH-REMEDIATION`, findings M-F9–M-F11). Re-verified all 40 existing
  claims against `79cf971` with zero regressions, including under an
  unplanned Lean 4.33.0→4.33.1 toolchain auto-upgrade. Independently
  investigated Phase 5 (`crates/prin-daemon/src/{assignment,mot}.rs`,
  `crates/prin-train/src/{stats,adversarial}.rs`) for new mathematical
  content beyond EA-006's source-review disposition and authored a new
  ledger, `tools/math_audit_claims/prin-daemon-phase5-properties.json`
  (6 claims: Hungarian-assignment optimality via Z3, IoU-distance
  boundedness, Cohen's d and Welch-Satterthwaite special-case reductions,
  Gamma-reflection and Beta-integral identities behind the Student's-t
  p-value) — all 6 reached genuine SymPy/Z3 `PASS`. Cross-validated every
  result via independent, out-of-band Wolfram Engine computation
  (`EVIDENCE/math-audit/manual/ema-005-wolfram-corroboration.{wls,txt}`).
  M-F9 (D4, `math-audit-mcp`'s `verify_identity` allowlist has no
  Beta-function support) discovered and worked around with a stronger
  first-principles derivation. 46 total claims across 9 ledgers; maintainer
  sign-off requested for the unchanged 7-claim `REQUIRES_HUMAN_REVIEW` set
  (`DEFERRED_VALIDATION_REGISTER.md` DV-013).

- **EMA-005 remediation session** (2026-08-26, process/documentation-only
  follow-up, no new EMA/WP identifier) — dispositioned all four of EMA-005
  §6.2's pass-forward items. M-F9 and M-F7 were already correctly tracked
  (`DEFERRED_VALIDATION_REGISTER.md` DV-026/DV-013) with no action required;
  confirmed unchanged. Added **DV-027** (M-F11, `math-audit-mcp`'s stale
  editable-install `dist-info` — non-blocking, gated to the tool's next
  `.venv` touch) and **DV-028** (vendoring `math-audit-mcp` into PRIN —
  consolidates the recurring EMA-004/EMA-005 architectural-decision mention
  into one tracked register row). Corrected a documentation drift found
  during this review: `DOCS/sessions/SESSION_REGISTER.md`'s EMA-005 row
  still read "maintainer sign-off pending" despite the report and DV-013
  both already recording sign-off granted 2026-08-26. No code, claim-ledger,
  or policy changes — `math-audit-mcp` itself was not modified, consistent
  with both findings being explicitly scoped to a future dedicated
  tool-remediation session.

- **M-F9 / DV-026 remediation** (2026-08-26, `math-audit-mcp` tool-
  remediation session) — added `beta`/`betainc`/`betainc_regularized` to
  `math-audit-mcp`'s `ALLOWED_MATH_FUNCTIONS` security allowlist (tool
  commit `d69d9f8`), closing the Beta-function coverage gap discovered
  during EMA-005 BETA-SYM-01 claim authoring. Expression guard verified
  to accept all three functions; `beta(a,b)==gamma(a)*gamma(b)/gamma(a+b)`
  reduces to 0 symbolically; `betainc_regularized` symmetry identity
  confirmed numerically; all 120 existing tool tests pass. Verification
  evidence: `EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`.
  DV-026 closed.

- **Executive Audit Session 006 (EA-006)** — Phase 5 close executive audit;
  report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_006.md`
  (`PASS-WITH-REMEDIATION`, findings E-F1–E-F2). Delta audit of Sessions
  0109–0128 (WP-028..WP-032, Phase 5 close) plus two post-close CI hotfix
  commits, plus full-project re-verification (1441+122+3 Rust tests, 1155
  Python/parity tests, all clean quality/security/docs gates, live CI
  6/6 non-skip workflows `success`). E-F1 (D3, hotfix commits
  `cb5660b`/`5d90427` never recorded in the deviation ledger, leaving DV-024
  stale) FIXED. E-F2 (D3, Phase 4 recommendation R28's precondition — a
  dedicated hotfix/correction session for DV-019 before WP-028 S1 — was
  never honored, and Phase 5 closed anyway) remediated at the governance
  level: compliance gap recorded, and WP-033 S1's session brief now carries
  a hard entry-condition gate so it cannot silently recur.

- **WP-035 Reproduction pipeline and manifest** (`tools/reproduce.py`,
  `paper/artefact_manifest.json`, `tests/test_reproduce.py`,
  `.github/workflows/repro.yml`; Phase 6 third WP; sessions 0137–0140; audit
  `DOCS/audits/035-wp035-audit.md`, verdict `PASS-WITH-FINDINGS`, one D4
  finding WP035-F1 FIXED in S3): end-to-end deterministic reproduction
  pipeline that regenerates all 14 verifiable historical figures
  (`fig2`–`fig15`) and 11 LaTeX tables from the immutable stored JSON
  artefacts in `benchmarks/results/` without GPU execution, training, or
  random sampling.
  - `tools/reproduce.py` — typed CLI and API: `compute_sha256`,
    `load_manifest`, `append_manifest` (append-only semantics — existing
    records verified before new ones added), `verify_manifest` (strict
    inventory/digest check), `run_reproduction` (orchestrates figure and
    table generation via `prin.reporting`), and `main` CLI with
    `--figures-only`/`--tables-only`/`--verify-manifest`/`--append-manifest`
    modes. Manifest destination confined to allowed roots
    (`paper/`, `benchmarks/results/`, OS temp); path-traversal and
    duplicate-name checks on manifest records.
  - `paper/artefact_manifest.json` — governed SHA-256 manifest (schema
    version 1, 172 records) covering every stored JSON artefact. Each record
    contains the plain filename, exact byte size, and lowercase SHA-256
    digest. Append-only: mutation or removal of an accepted artefact is a
    hard failure.
  - `tests/test_reproduce.py` — 23 tests covering manifest validation (172
    records), append-only semantics (add/modify/delete/resize), three tamper
    mutation modes (missing/corrupt/extra), size-before-hash optimization,
    8 malformed-manifest parametric cases, output mode selection,
    conflicting-mode rejection, verify-before-generation ordering, CLI
    success/failure paths, deterministic checksum output, and public-surface
    import regression. `tools/reproduce.py` **100%** line coverage.
  - `.github/workflows/repro.yml` — `PRIN_REPRO_ENABLED` guard removed;
    runs tamper tests then verified regeneration on every push/PR.
  - No numerics in Python, no new dependencies, no crate changes: the
    pipeline imports only `prin.reporting` generators and reads archived
    JSON data without importing or executing archived code.
  - **WP035-F1 (D4) FIXED** in S3 (`cbbbbb3`): `tools/reproduce.py` imported
    `ReportingError` from the private `prin.reporting._artifacts` module;
    changed to the public `prin.reporting` surface. Regression test
    (`test_reproduce_imports_only_public_reporting_surface`, AST-based)
    committed in the same fix.
  - **S4 documentation closure (session 0140):** `tools/` and `paper/`
    READMEs expanded; Migration Guide gains a WP-035 section; Project State
    Report `DOCS/reports/035-project-state.md` issued, declaring WP-036
    (API completion, acceptance suite, and migration).

- **WP-034 Reporting, figures, tables, and profiling**
  (`python/prin/reporting/`, `tests/test_reporting_profiler.py`,
  `tests/test_publication_generation.py`; Phase 6 second WP; sessions
  0133–0136; audit `DOCS/audits/034-wp034-audit.md`, verdict
  `PASS-WITH-FINDINGS`, four D4 findings — three FIXED in S3, one
  documentation-only correction closed here in S4): near-verbatim ports of the
  PRINet 3.0 `utils/{benchmark_reporting,figure_generation,table_generation,
  profiler}.py` reporting tools, rebuilt with typed public-boundary errors,
  deterministic output, and output-path confinement.
  - `prin.reporting.benchmark_reporting` — `generate_benchmark_report`,
    `generate_leaderboard`, `generate_scalr_metrics_report`: deterministic
    Markdown from stored benchmark JSON. The implicit wall-clock timestamp of
    the 3.0 reference is removed; `generated_at` is caller-supplied and
    normalized to UTC minute precision, so unchanged inputs produce byte-stable
    output. Markdown escaping and confined writes throughout.
  - `prin.reporting.figure_generation` — **14** stored-artefact figure
    generators (`fig_ablation_results` … `fig_training_curves`), the headless
    300-DPI NeurIPS style (`configure_neurips_style`), `generate_all_figures`
    master entry, and `normalize_matplotlib_output` for deterministic
    PDF/PNG byte comparison (fixed dates/producer metadata; ancillary chunks
    discarded).
  - `prin.reporting.table_generation` — **11** byte-comparable LaTeX fragment
    generators (`table_ablation_variants` … `table_supercritical_regime`) and
    `generate_all_tables`. Every fragment regenerates bytes-identical to its
    stored PRINet 3.0 `paper/tables/` counterpart (LF-normalized).
  - `prin.reporting.profiler` — `PRINetProfiler` (typed `torch.profiler`
    wrapper), the legacy `ProfileReport` shape and Chrome-trace name,
    `profile_training_loop`, and `PRINetProfiler.record_function(label)` as the
    explicit boundary that makes Rust-backed operations visible in torch
    traces. No model numerics; RNG state is never mutated.
  - `prin.reporting._artifacts` — internal shared module: the single home for
    stored-artefact JSON loading/schema validation and the typed error
    hierarchy. Every reporting error subclasses the new `ReportingError`
    root while keeping its original stdlib base (`ValueError`/`RuntimeError`/
    `FileNotFoundError`) for backward-compatible `isinstance` catches.
  - No numerics in Python, no new dependencies, no crate changes: the package
    only renders and profiles values that already live in stored JSON or in
    the Rust core. Stored-artefact byte comparison and deterministic
    PDF/PNG normalization are the applicable parity evidence (no numerical
    primitive is introduced).
  - `tests/test_reporting_profiler.py` (59) and
    `tests/test_publication_generation.py` (13) — 72 tests; `prin.reporting`
    99% line coverage. Covers report/leaderboard/SCALR determinism, schema and
    output-confinement errors, profiler lifecycle/state validation, Rust-call
    labels, Chrome-trace export, all 14 figure generators, all 11 table
    generators, exact LaTeX bytes, and deterministic normalized PDF/PNG.
  - **Figure count — factual correction (WP034-F1, D4, carried to S4):** the
    WP-034 session briefs and the WP-035 brief quote "15 figures". The verified
    PRINet 3.0 reference (`utils/figure_generation.py`, stored `paper/figures/`)
    contains **14** generated figures, numbered `fig2`–`fig15`; no `fig1`
    implementation or stored output has ever existed. PRIN ports all 14
    verifiable generators. This is a factual correction to the brief text, not
    a plan amendment and not a dropped deliverable.
  - **WP034-F2 (D4) FIXED** in S3 (`11a97cb`): `normalize_matplotlib_output`
    now raises the typed `NormalizationError` (a
    `PublicationGenerationError`/`ValueError` subclass) instead of a bare
    `ValueError`.
  - **WP034-F3 (D4) FIXED** in S3 (`8dbf55d`): reporting errors unified under
    the shared `ReportingError` root.
  - **WP034-F4 (D4) FIXED** in S3 (`8dbf55d`): stored-artefact JSON loading
    moved into `prin.reporting._artifacts`; the private cross-module import
    between `table_generation` and `figure_generation` is gone.
  - **S4 documentation closure (session 0136):** `prin.reporting` and `tests/`
    READMEs expanded; Migration Guide gains a WP-034 symbol-mapping section;
    `DOCS/audits/`, `DOCS/reports/`, `DOCS/sessions/` indexes updated; Project
    State Report `DOCS/reports/034-project-state.md` issued, declaring WP-035
    (Reproduction pipeline and manifest).

- **WP-033 Unified benchmark runner and category migration**
  (`benchmarks/`, `tests/test_benchrunner.py`, Phase 6 first WP; sessions
  0129–0132; audit `DOCS/audits/033-wp033-audit.md`, verdict
  `PASS-WITH-FINDINGS`, one D2 finding WP033-F1 FIXED in S3): unified
  `benchrunner` CLI, shared configuration/environment-capture/timing/
  registry/result-writer infrastructure, and migration of all 58 verified
  legacy PRINet 3.0 benchmark scripts into nine topic category packages.
  - `benchmarks/_common/` — shared `BenchmarkConfig`, `capture_environment`,
    `timed_run` (≥10-iteration timing rule, warmup exclusion, median/p95),
    `BenchmarkRegistry` (category/name dispatch), `write_result` (output-path
    confinement to 3 allowed roots).
  - `benchmarks/benchrunner/` — CLI (`python -m benchmarks.benchrunner`)
    with `--list`, `--category`, `--name`, `--iterations`, `--out` dispatch.
  - Nine category packages: `scaling/` (2 benchmarks), `chimera/`, `mot/`,
    `ablations/`, `kernels/` (criterion subprocess bridge), `integrators/`,
    `training/`, `daemon/`, `adversarial/` — all delegate to already-parity-
    dispositioned Rust APIs; no new numerics in Python.
  - `tests/test_benchrunner.py` — 50 tests (49 fast + 1 slow) covering
    config validation, timing rule, registry, environment capture, result
    writing, schema compatibility, CLI dispatch, criterion bridge parsing,
    and all remaining categories. 99% coverage on `benchmarks/`.
  - `DOCS/baselines/wp033_benchmark_traceability.md` — 58-row traceability
    table mapping every verified legacy script to its category and module.
  - **WP033-F1 (D2) FIXED** in S3 (`6eb4e8b`): two tests failed under the
    project's documented `--basetemp=.pytest_basetemp` Windows pytest
    invocation; monkeypatched `_ALLOWED_ROOTS` in the affected tests.
  - **S4 documentation closure (session 0132):** Migration Guide updated
    with WP-033 benchrunner section; `benchmarks/README.md` and category
    READMEs updated; `DOCS/reports/`, `DOCS/experiments/`,
    `DOCS/baselines/`, `DOCS/sessions/` indexes updated; Project State
    Report `DOCS/reports/033-project-state.md` issued, declaring WP-034
    (Reporting, figures, tables, and profiling).

- **WP-032 Daemon/evaluation integration and Phase 5 gate**
  (`crates/prin-py/`, `crates/prin-daemon/`, `python/prin/`, Phase 5 fifth
  and final WP; sessions 0125–0128; audit
  `DOCS/audits/032-wp032-audit.md`, verdict `PASS`, zero findings):
  cross-crate integration of the WP-028..WP-031 daemon and experiment-tooling
  modules into a cohesive evaluation pipeline, with provider and latency
  acceptance.
  - `crates/prin-py::bindings::daemon` — native `SubconsciousDaemon` and
    `TrainingHooks` PyO3 bindings; GIL-safe stop/drop (background thread
    detaches Python while waiting); callback shape/dtype/contiguity
    validation.
  - `crates/prin-py::bindings::phase5` — MOT, temporal metrics, bootstrap
    CI / Welch t-test / Cohen's d, and adversarial evaluation PyO3 bindings;
    all delegate to already-parity-dispositioned Rust primitives (no new
    numerics).
  - `python/prin/daemon.py` — `SubconsciousController.spawn_daemon()` and
    public daemon/hooks exports.
  - `python/prin/eval/__init__.py` — cohesive MOT and temporal evaluation
    facade (`MotAccumulator`, `compute_full_temporal_metrics`, etc.).
  - `python/prin/experiments/__init__.py` — statistical
    (`bootstrap_ci`, `welch_t_test`, `cohens_d`) and public-model
    adversarial (`adversarial_evaluate_*`) facade.
  - `python/prin/_prin_core.pyi` — complete type stubs for the added
    extension surface (8 new Phase 5 types).
  - `tests/test_phase5_integration.py` — eight end-to-end integration tests
    covering full pipeline, GIL safety, MOT/temporal, bootstrap/Welch/
    adversarial, validation, and both tracker families.
  - `EVIDENCE/0125-wp032-s1-daemon-latency.json` — five-trial lock-free/
    mutex pilot (p95 200 ns vs. 2700–3000 ns, 13.5×–15× lower) plus
    direct-reference acceptance.
  - `EVIDENCE/0125-wp032-s1-provider-acceptance.json` — live provider probe
    (CPU pass; DirectML graph-incompatible per amendment #13/DV-006;
    VitisAI absent per DV-006).
  - Acceptance criteria: daemon latency target met (lock-free p95 200 ns);
    MOT equivalence 2/2; provider acceptance with justified optional-
    hardware skips; Phase 5 tag gate green locally. Coverage ≥95% on every
    changed file (`phase5.rs` 99.62% lines, `daemon.rs` new code 100%,
    Python 100%). 8 new integration tests.
  - **Phase 5 exit gate: GREEN** — 5/5 Phase 5 WPs complete (WP-028,
    WP-029, WP-030, WP-031, WP-032).

- **WP-028 ONNX controller and backend selection** (`crates/prin-daemon/`,
  `crates/prin-py/`, `python/prin/daemon.py`, Phase 5 first WP; sessions
  0109–0112; audit `DOCS/audits/028-wp028-audit.md`, verdict `PASS`, zero
  findings): subconscious controller state/control types, hand-written ONNX
  model validation, provider detection (VitisAI→DirectML→CPU), and
  deterministic CPU-terminated fallback.
  - `prin_daemon::state` — `SubconsciousState`, `ControlSignals`, `Regime`,
    `STATE_DIM = 32`, `CONTROL_DIM = 8`: PRINet 3.0's exact float32 packing,
    normalisation, and clamping semantics (bit-exact parity, 8 Rust parity
    tests + 82 differential Python tests against `prinet==3.0.0`).
  - `prin_daemon::backend` — `Backend`, `BackendSelection`, `SelectionReason`,
    `select_backend`, `provider_options`, `VitisAiConfig`,
    `firmware_candidates`, `resolve_firmware`: VitisAI→DirectML→CPU priority
    policy, deterministic fallback ladder (pure, property-tested over
    arbitrary provider subsets).
  - `prin_daemon::onnx` — `OnnxModelInfo`, `TensorSpec`, `inspect_onnx_bytes`,
    `inspect_onnx_file`: bounded, total ONNX `ModelProto` reader (hand-written,
    no `protoc` dependency; proptest-fuzzed on arbitrary bytes, never panics).
  - `prin_daemon::model` — `ModelManifest`, `sha256_file`, `verify_sha256`,
    `ControllerModel::validate`: SHA-256 integrity verification against
    `models/manifest.json`, external-data completeness, graph-contract
    validation.
  - `prin.daemon` — `SubconsciousController`, `create_session`,
    `select_backend`, `detect_best_backend`, `backend_info`,
    `verify_model_artefacts`, `OrtUnavailableError`: Python orchestration
    layer (no numerics; ONNX Runtime session creation stays in Python per
    risk register #4).
  - `models/manifest.json` — SHA-256 + size manifest for the two committed
    controller artefacts.
  - Acceptance criteria: outputs match 3.0 references across available
    providers (bit-identical on CPU, 48 differential cases); missing-provider
    paths fall back safely (property-tested); model SHA-256 verified before
    graph parse. Coverage ≥95% on every new file; 122 new Rust tests, 106 new
    Python tests.

- **WP-029 Daemon runtime and lock-free control buffer**
  (`crates/prin-daemon/`, Phase 5 second WP; sessions 0113–0116; audit
  `DOCS/audits/029-wp029-audit.md`, verdict `PASS`, zero findings): native
  daemon lifecycle, lock-free control-signal ring buffer, telemetry, bounded
  shutdown, and concurrency safety.
  - `prin_daemon::daemon` — `SubconsciousDaemon` (native background thread
    with bounded `stop()` returning `bool`), `ControlSignalBuffer`
    (lock-free, `ArcSwap`-backed replacement for PRINet 3.0's
    `threading.Lock`-guarded buffer), `InferenceBackend` (pluggable inference
    seam with blanket closure impl), `DaemonConfig`, `DaemonStats`,
    `DeadLetterEntry`, `EscalationEvent`/`EscalationCallback`: the full
    daemon lifecycle with dead-letter queue, escalation callbacks, and
    non-finite control-signal fallback.
  - `prin_daemon::error` — `DaemonError::ThreadSpawn` variant for native
    thread creation failures.
  - `crates/prin-daemon/tests/daemon_concurrency.rs` — 4 stress/race/lifecycle
    tests: concurrent multi-producer/multi-consumer access, single-writer
    monotonic ordering under the lock-free buffer, repeated start/stop
    cycles, and a slow-backend bounded-`stop()` test.
  - `crates/prin-daemon/benches/control_buffer.rs` — Criterion comparison:
    lock-free `ControlSignalBuffer` vs. `Mutex`-guarded PRINet 3.0 design
    re-implementation, under 0/1/4 writer-thread contention.
  - `crates/prin-daemon/examples/control_buffer_pilot.rs` and
    `tools/wp029_control_buffer_pilot.py` — p50/p95/max latency pilots
    (Rust and actual PRINet 3.0 Python reference).
  - `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` — combined pilot
    evidence: 5 Rust + 5 Python runs with methodology and environment
    capture. Lock-free p95 is 13–20× lower than the mutex-guarded
    re-implementation of the reference design.
  - New dependency: `arc-swap = "1.7"` (resolves to 1.9.2; zero runtime
    transitive dependencies; justified per Coding Standards §2.2 — avoids
    hand-rolled `UnsafeCell`/`AtomicPtr` hazard-pointer reclamation).
  - Acceptance criteria: 24 unit + 4 concurrency stress + 12 property tests
    pass; no deadlocks/data races (`#![forbid(unsafe_code)]` unchanged,
    structural lock-ordering argument + empirical stress tests); p50/p95
    instrumentation valid and latency pilot improves on 3.0. Coverage
    ≥95% on `daemon.rs` (97.16% regions, 97.28% lines). 42 new tests.

- **WP-030 Training hooks and MOT evaluation** (`crates/prin-daemon/`,
  `tools/wp030_mot_fixture.py`, Phase 5 third WP; sessions 0117–0120; audit
  `DOCS/audits/030-wp030-audit.md`, verdict `PASS`, zero findings): loss
  EMA/gradient/latency training hooks, daemon integration, and a CLEAR-MOT/
  IDF1 evaluation core validated against real `py-motmetrics`.
  - `prin_daemon::hooks` — `TrainingHooks`: loss EMA/variance,
    gradient-norm EMA (from caller-supplied per-parameter L2 norms), and
    step-latency window/p50/p95/throughput, packaged into a
    `SubconsciousState` for `daemon.submit_state(hooks.on_epoch_end(...))`.
    Rebuilds PRINet 3.0's `prinet.nn.training_hooks.StateCollector`.
  - `prin_daemon::mot` — `MotAccumulator`/`MotSummary` (MOTA/MOTP/IDF1/
    identity switches/misses/false positives), `BBox`/`iou_distance_matrix`,
    `Detection`, `generate_linear_sequence`/`generate_crowded_sequence`
    (`prin_dynamics::Seed`-driven, deterministic). Rebuilds the metrics core
    of PRINet 3.0's `prinet.nn.mot_evaluation`.
  - `crates/prin-daemon/src/assignment.rs` (crate-private) — rectangular
    Hungarian/Kuhn–Munkres assignment solver reproducing
    `motmetrics.lap.add_expensive_edges`'s NaN/Inf "do-not-pair" recipe, used
    for per-frame and global (IDF1) identity matching.
  - `crates/prin-daemon/tests/parity_mot.rs`,
    `crates/prin-daemon/tests/data/mot_reference_cases.json`,
    `tools/wp030_mot_fixture.py` — 10 scenarios replayed through real
    `py-motmetrics` 1.4.0 and PRIN's `MotAccumulator`, agreeing at
    `rtol=1e-9, atol=1e-12`; fixture independently regenerated
    byte-for-byte identical.
  - `crates/prin-daemon/tests/hooks_daemon_integration.rs`,
    `crates/prin-daemon/benches/training_hooks.rs` — end-to-end
    `TrainingHooks` → `SubconsciousState` → `SubconsciousDaemon` proof and
    per-call overhead bound/pilot evidence (100k calls well under a 2s
    ceiling; 4.69 ns–425 ns per call).
  - Security hygiene: `stable-vec` 0.4.2 → 0.4.3 (`RUSTSEC-2026-0267`
    double-free/use-after-free fix), a one-line lockfile bump unrelated to
    this WP's own scope.
  - Acceptance criteria: metrics match the `motmetrics` reference (10/10
    scenarios); hook overhead/bounds are tested (bound + property test);
    deterministic sequence fixtures cover identity edge cases (identity
    switch, occlusion reappearance, `max_switch_time` boundary). Coverage
    ≥95% on all three new files (`hooks.rs` 99.75%, `mot.rs` 99.72%,
    `assignment.rs` 98.89% regions); 54 new tests.
  - Documentation correction (WP030-F1, D4, this S4): the WP-028-approved
    deferral of `SubconsciousController.export_to_onnx`/`.quantize_onnx`/
    `retrain_controller` to "WP-030" was never reflected in WP-030's actual
    declared scope (PSR-029 §6) or delivered work — those three symbols are
    training-stack export/retraining behavior, not training-telemetry hooks
    or MOT evaluation. Re-targeted to WP-036 in `tools/wp001_ownership.json`
    (regenerating `DOCS/baselines/wp001_api_traceability.md`) and the
    Migration Guide; see `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`
    DV-025.

- **WP-031 Temporal experiments, statistics, and adversarial tooling**
  (`crates/prin-train/`, `tools/wp031_stats_fixture.py`, Phase 5 fourth WP;
  sessions 0121–0124; audit `DOCS/audits/031-wp031-audit.md`, verdict
  `PASS`, zero findings): fair PT-vs-SA training framework, temporal
  tracking-quality metrics, statistical utilities, FLOPs estimation, and
  FGSM/PGD adversarial robustness evaluation.
  - `prin_train::trainer` extensions — `train_temporal_slot_attention_mot`/
    `evaluate_temporal_slot_attention_mot` (SA-side counterpart to the
    existing PT trainer, sharing identical `TemporalTrainerConfig` for a
    fair matched-budget comparison), `count_parameters` (generic over any
    `Module` via `ModuleVisitor`), `TrainingSnapshot`, `train_multi_seed`
    (multi-seed statistical reliability). `train_phase_tracker` now threads
    `&mut Seed` explicitly (Project Plan §4 rule 3). PyO3 binding extended
    with `Seed` parameter and `snapshot_epochs`.
  - `prin_train::temporal_metrics` — `identity_switches`,
    `track_fragmentation`, `mostly_tracked_mostly_lost`,
    `track_duration_stats`, `recovery_speed`, `binding_robustness`,
    `temporal_smoothness`, `TemporalMetrics` aggregate. Direct port of
    PRINet 3.0 `utils/temporal_metrics.py`.
  - `prin_train::stats` — `bootstrap_ci` (percentile-method bootstrap CIs),
    `welch_t_test`/`compute_p_value` (Welch's t-test with hand-rolled
    Student's-t p-value), `cohens_d` (effect size). Validated against real
    `scipy.stats.ttest_ind` 1.18.0: 8/8 scenarios at `rtol=1e-9,
    atol=1e-12` (`tests/parity_stats.rs`).
  - `prin_train::flops` — `LayerSpec`/`count_flops`/`FlopsReport` (per-layer
    FLOPs for Linear, Conv2d, GRU, LayerNorm, BatchNorm2d, Embedding,
    MultiHeadAttention), `measure_wall_time`/`WallTimeStats`.
  - `prin_train::adversarial` — `fgsm_attack`/`pgd_attack` (L-infinity
    bounded), per-tracker `adversarial_evaluate_pt`/
    `adversarial_evaluate_sa`, `adversarial_comparison`. Reuses
    `hungarian_similarity_loss` directly (Coding Standards §1.1).
  - `prin_train::error` — `InvalidBootstrapSamples`, `InvalidBootstrapCi`,
    `EmptySample`, `InvalidAttackEpsilon` variants.
  - `tools/wp031_stats_fixture.py`,
    `crates/prin-train/tests/data/welch_t_test_reference_cases.json`,
    `crates/prin-train/tests/parity_stats.rs` — 8 scenarios replayed
    through real `scipy.stats.ttest_ind` and PRIN's `welch_t_test`,
    agreeing at `rtol=1e-9, atol=1e-12`; fixture independently regenerated
    byte-for-byte identical.
  - Acceptance criteria: statistical routines match trusted references
    (Welch 8/8 at `rtol=1e-9`); matched-budget controls enforced
    (`count_parameters` generic, shared `TemporalTrainerConfig`); attack
    bounds (L-infinity ball) and deterministic multi-seed behavior tested.
    Coverage ≥95% on every new/changed file. 375 lib tests + 1 parity test.

- **Phase 4 recommendation implementation** (inter-phase process improvement, R26–R32
  disposition in `DOCS/ANALYTICS/phase-4/phase-4-recommendation-implementation-governance.md`):
  - Fixed PA4-F1/PA4-F2: `DOCS/PRIN_Project_Plan.md` §6's Phase 4 roadmap row now carries
    `✅ COMPLETE`; fixed all 12 genuine Sphinx warnings — `python/prin/__init__.py`'s
    `Subpackages:` docstring indentation corrected, `python/prin/nn/phase_tracker.py`'s
    `TrackingResult` dataclass restructured to per-field attribute docstrings (removing an
    autodoc/napoleon duplicate-object-description collision) — independently re-verified with
    two fresh-directory Sphinx builds: 0 warnings (R26, P0).
  - `Documentation_Standards.md` §7 item 9 (and, by cross-reference, the EA/EMA closing
    checklists in `Executive_Audit_Governance_and_Methodology.md` §5 and
    `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8) now require an explicit,
    recorded rationale whenever a closing-checklist item identifies a genuine gap and the
    session defers rather than fixes it (R27, P1).
  - Maintainer decision (2026-08-21, obtained live in-session): DV-021's bridge-overhead gap
    resolved via Plan amendment #30, revising the Phase 4 exit criterion to scope `<5%` to
    moderate/large batch and shape sizes (small shapes carry a measured, architecturally fixed
    ~38–41% dispatch overhead), following the amendment #21 precedent exactly. DV-021 closed as
    AMENDED (R29, P1).
  - `AGENTS.md`'s verification one-liner and `Documentation_Standards.md` §7 item 3 now require
    deleting/recreating `DOCS/sphinx/_build` immediately before every Sphinx build, closing the
    incremental-cache mechanism that let PA4-F2's false "0 warnings" claim stand across the
    entire phase (R30, P1).
  - `Documentation_Standards.md` §7 item 5 now requires Project State Report next-WP
    declarations to quote their governing normative source (session brief or Rebuild Planning
    Document) directly rather than paraphrase from memory (R32, P3).
  - R28 (dedicated hotfix/correction session for DV-019's now-five-times-recurring flaky test)
    deferred to a session before session 0109 (WP-028 S1) begins, no session number assigned per
    this project's ad hoc-session-naming convention; R31 (DV-005 CUDA Burn backend Phase 5
    scoping decision) deferred to WP-028 S1 (session 0109) — both per
    `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`.

- **WP-027 Trainable-stack integration and Phase 4 gate**
  (`crates/prin-train/`, `crates/prin-py/`, `python/prin/nn/`, `python/prin/`,
  Phase 4 sixth and final WP; sessions 0105–0108; audit
  `DOCS/audits/027-wp027-audit.md`, verdict `PASS`, zero findings):
  temporal CLEVR-N dataset generator, training losses, Rust-native training
  loop, optimizer bridges, and Phase 4 acceptance-criterion validation.
  - `prin-train::dataset` — `SequenceData`, `TemporalClevrNConfig`,
    `generate_temporal_clevr_n`, `generate_dataset`: structural port of
    PRINet 3.0's temporal CLEVR-N sequence generator using the project's
    counter-based `Seed`.
  - `prin-train::losses` — `hungarian_similarity_loss`,
    `temporal_smoothness_loss`: direct ports of the reference training losses.
  - `prin-train::trainer` — `TemporalTrainerConfig`, `TrainingResult`,
    `ValMetrics`, `train_phase_tracker`, `evaluate_phase_tracker`: Rust-native
    training loop (Burn Adam + warmup/cosine LR + gradient clipping + early
    stopping). Two documented deviations from PyTorch reference (per-tensor
    gradient clipping, scalar cosine LR formula).
  - `prin-train::benches/phase_tracker_bridge.rs` — Criterion baseline for
    `PhaseTracker::forward`/`match_frames`.
  - `prin-py::bindings::optim` — `SyncGdBridge`/`ScalrBridge`/`RipBridge`
    non-differentiable optimizer-step bridges.
  - `prin-py::bindings::trainer` — `train_phase_tracker` PyO3 entry +
    `TrainingResult` pyclass.
  - `python/prin/nn/optimizers.py` — `SyncGd`/`Scalr`/`Rip`
    `torch.optim.Optimizer` subclasses.
  - `python/prin/train.py` — thin Python entry point for the Rust-native
    trainer.
  - Acceptance criteria: PhaseTracker mean IP = 1.00000 ≥ registered 0.99868
    threshold; gradchecks green (including composed "full gradcheck");
    serialization round-trip on trained model validated. DV-021 bridge
    overhead independently re-corroborated (+37.8%/+6.5% vs. DV-021's
    +39.8%/+5.3%). DV-005 CUDA Burn backend recommendation recorded: do not
    pull into near-term Phase 5 scope.

- **Executive Audit Session 005 (EA-005)** — Phase 4 close executive audit;
  report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_005.md`
  (`PASS-WITH-REMEDIATION`, findings E-F1–E-F5). E-F1 (D2, mypy lint failure)
  FIXED; E-F2 (D3, ubuntu runner disk exhaustion, DV-022) and E-F3 (D3,
  windows-latest CubeCL timeout, DV-023) passed forward as external
  infrastructure conditions; E-F4 (D4, phase-4 README status mismatch) FIXED;
  E-F5 (D4, CHANGELOG missing WP-027) FIXED.

- **Self-hosted Windows runner for CI** (EA-005 follow-up, DV-016/DV-022/DV-023
  remediation): `rust.yml`, `python.yml`, and `release.yml` now route all
  `windows-latest` matrix jobs to the self-hosted `PRIN-GPU-Runner`
  (`[self-hosted, Windows, X64]`) instead of GitHub-hosted `windows-latest`.
  The GitHub-hosted runner was ~14× slower than local hardware for
  CubeCL-CPU workloads (DV-016) and now times out (DV-023). `parity.yml`
  retains `ubuntu-latest` with a documented fallback comment for routing to
  a self-hosted Linux runner (WSL2) if the disk-exhaustion issue (DV-022)
  recurs.

- **Executive Mathematical Audit Session 004 (EMA-004)** — tool remediation
  session; report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_004.md`
  (`PASS-WITH-REMEDIATION`, M-F8/M-F5/M-F6 closed, M-F7 unchanged
  resolved-by-design). Fixed EMA-003's M-F8 at root cause in
  `math-audit-mcp`'s `verify_identity` (promote declared `"symbol > 0"`-style
  assumptions into SymPy `Symbol`-level kwargs so `Pow(0, x)` auto-evaluation
  fires — the gap was in the tool, not a SymPy limitation as previously
  characterized; SCALR-LR-02 now genuine symbolic `PASS`). Fixed EMA-001's
  M-F5 by adding `expected_output`/`output_tolerance` numeric-reconstruction
  comparison to `audit_tensor_contract` (pure NumPy, no PyTorch/JAX backend
  needed as previously scoped) and authored a new claim (TCK-01,
  `prin-tensor-hosvd-reconstruction.json`, first EMA coverage of
  `prin-tensor`) against the existing PRINet-3.0 HOSVD reference fixture
  (residual `7.1e-15` at `1e-10` tolerance). Added a new optional adapter/tool
  (PySAT: CNF cardinality-encoding + CDCL SAT solver corroboration of graph
  k-regularity, independent solver family from the existing NetworkX/Z3
  checks) and a new corroborating claim (GRA-01-SAT). Fixed EMA-001's M-F6 by
  `git init`-ing `math-audit-mcp`'s own, separate, non-PRIN repository for
  the first time (it previously had none). Evaluated and deferred `z3_mcp`
  (redundant), `OpenLogic` (reference corpus, not a callable tool), MiniZinc
  MCP and SageMath (not installed, no concrete claim needs them yet). Re-ran
  the full audit: 40 claims across 8 ledgers (was 38/7), zero regressions,
  33 PASS / 0 FAIL / 0 INCONCLUSIVE / 7 REQUIRES_HUMAN_REVIEW. Maintainer
  sign-off (MichaelMaillet, 2026-08-20) re-granted for the full current
  REQUIRES_HUMAN_REVIEW set (INT-01, INT-02, HOPF-01, KUR-01, GRA-01,
  TEN-01, and first-time sign-off for the new TCK-01), per DV-013's
  recorded-sign-off resolution pattern. Also
  retroactively added EMA-003's own missing
  `SESSION_REGISTER.md`/`DEFERRED_VALIDATION_REGISTER.md`/`CHANGELOG.md`
  entries (a governance §8.6 closing-checklist gap discovered this session).

- **Executive Mathematical Audit Session 003 (EMA-003)** — Phase 4 close
  mathematical audit, first EMA coverage of the trainable stack; report
  `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_003.md` (`PASS-WITH-REMEDIATION`,
  new finding M-F8, closed by EMA-004 above). Re-verified all 28 existing
  claims against `6e33ca5` (zero regressions); authored and executed 10 new
  `prin-train-trainable-stack-properties.json` claims covering the Hungarian
  similarity loss entropy identity, dSiLU derivative formula, Scalr lr-scale
  boundary behaviors, RIP Hebbian equilibrium, SyncGd penalty gradient
  formula, and four Z3-proved bound/non-negativity/diagonal invariants — 9/10
  reached genuine SymPy/Z3 `PASS`; SCALR-LR-02 reached `INCONCLUSIVE`
  (recorded as M-F8). 38 total claims across 7 ledgers; 30 PASS, 1
  INCONCLUSIVE, 7 REQUIRES_HUMAN_REVIEW (same M-F3/M-F7 policy-gate,
  re-confirmed under DV-013/R20 precedent). Direct redundant SymPy+Z3
  cross-verification performed for all new claims. This entry was added
  retroactively by EMA-004 (the session's own closing checklist omitted it).

- **WP-026 PhaseTracker, Hybrid, baselines, and allocation**
  (`crates/prin-train/`, `crates/prin-py/`, `python/prin/nn/`, Phase 4 fifth
  WP; sessions 0101–0104 plus Exec-WP-026 S1 executive secondary session;
  audit `DOCS/audits/026-wp026-audit.md`, verdict `PASS-WITH-FINDINGS`, two
  D4 findings: WP026-F1 FIXED, WP026-F2 FIXED): six new trainable modules
  rebuilding PRINet 3.0 `nn/{layers,hybrid,slot_attention,ablation_variants,
  adaptive_allocation}.py` with full PyO3 bridges and Python wrappers.
  - `prin-train::attention::OscillatoryAttention` — multi-head attention with
    additive oscillatory coherence bias (`score = QKᵀ/√d_k + α·cos(φ_i − φ_j)`).
  - `prin-train::phase_tracker::PhaseTracker` — PRIN's primary contribution:
    phase-based multi-object tracker encoding detections to phase/amplitude
    via MLP, evolving through `DiscreteDeltaThetaGamma`, matching frames by
    phase-coherence similarity with greedy assignment.
  - `prin-train::hybrid::HybridPRINetV2` — canonical hybrid oscillator +
    attention classification architecture: input → token projection →
    adaptive oscillator phase interleaved with oscillatory attention + FFN
    blocks → pool → classify.
  - `prin-train::slot_attention::{SlotAttentionModule,
    TemporalSlotAttentionMOT}` — non-oscillatory Slot Attention comparison
    baseline; both draw fresh per-call stochastic noise from `&mut Seed`.
  - `prin-train::ablation` — four structural ablation variants:
    `PhaseTrackerFrozen`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`,
    `SlotAttentionFrozen`.
  - `prin-train::allocation::{AdaptiveOscillatorAllocator,
    DynamicPhaseTracker}` — task-complexity-driven adaptive oscillator-count
    allocation with rule-based and learned (MLP) strategies.
  - Shared helpers in `support.rs`: `seeded_linear`/`seeded_gru` (avoid
    `Backend::seed` shared-global-RNG hazard), `seeded_standard_normal`,
    `python_round`, `phase_coherence_similarity`, `greedy_match_by_similarity`.
  - `validate_shapes()` added to all six new `Module` types (checkpoint
    shape validation mirroring WP025-F1 precedent); a real
    checkpoint-corruption bug found and fixed (Burn's `Module::load_record`
    silently ignores plain `usize` fields).
  - PyO3 bridges (`crates/prin-py/src/bindings/{attention,phase_tracker,
    hybrid,slot_attention,ablation,allocation}.rs`) and thin
    `torch.nn.Module` wrappers (`python/prin/nn/{attention,phase_tracker,
    hybrid,slot_attention,ablation,allocation}.py`); generic
    `apply_rust_bridge` in `_bridge.py`; 344 lines of new `.pyi` stubs.
  - 3 new golden-value parity test files (`parity_attention.rs`,
    `parity_phase_tracker.rs`, `parity_hybrid.rs`); 92 new Rust unit tests
    + 15 `validate_shapes` regression tests; 86 new Python tests across 6
    files; 100% Python `nn/` coverage (372/372 statements); all new Rust
    files ≥95% on every coverage metric.
  - S3 remediation: WP026-F1 FIXED (strategy-mismatch detection in
    `AdaptiveOscillatorAllocator::validate_shapes`, `TrainError::StrategyMismatch`
    variant); WP026-F2 FIXED (whole-module `HybridPRINetV2` parity test
    revealed and fixed missing ReLU in classifier head, `HybridPRINetV2Params`
    / `init_from_params` added). CLEAN delta re-audit.

- **WP-027 Trainable-stack integration and Phase 4 gate**
  (`crates/prin-train/`, `crates/prin-py/`, `python/prin/nn/`,
  `python/prin/train.py`, Phase 4 sixth and final WP; sessions 0105–0107;
  audit `DOCS/audits/027-wp027-audit.md`, verdict `PASS`, zero findings):
  trainable-stack integration layer — dataset, losses, trainer modules in
  Rust; PyO3 bridges for optimizers (`SyncGd`, `Scalr`, `Rip`) and
  `train_phase_tracker` pipeline entry point; Python `train.py` orchestration
  module. PhaseTracker reaches registered IP threshold in validation.
  Serialization round-trip on trained model. Bridge overhead re-corroborates
  DV-021 figures (+37.8%/+6.5%). No new D1–D4 finding raised.

- **WP-025 Production Torch autograd bridge** (`crates/prin-py/`,
  `python/prin/nn/`, Phase 4 fourth WP; sessions 0097–0100; audit
  `DOCS/audits/025-wp025-audit.md`, verdict `PASS-WITH-FINDINGS`, four
  findings: WP025-F1 FIXED, WP025-F2 FIXED (evidentiary rigor; underlying
  gap tracked as DV-021), WP025-F3/F4 FIXED): PyO3/DLPack
  `torch.autograd.Function` bridges exposing `prin-train`'s Rust
  forward/backward to Python training loops.
  - `prin.nn.ResonanceLayer` — trainable single-layer Kuramoto resonance
    primitive as a `torch.nn.Module`, bridged to Rust via DLPack zero-copy
    tensor exchange. Forward runs the full `n_steps`-step Kuramoto
    integration inside a single Rust call; backward recomputes the forward
    pass (Burn's autodiff graph has no `retain_graph` equivalent).
  - `prin.nn.GatedPhaseActivation` — trainable gated phase activation
    (`y = sigmoid(w_g*z + b_g) * phase_activation(z)`) as a
    `torch.nn.Module`, bridged identically.
  - `crates/prin-py/src/bindings/train.rs` — `PyResonanceLayerBridge` /
    `PyGatedPhaseActivationBridge` PyO3 classes with `*Ctx` backward
    contexts; `read_dlpack_f64` / `export_dlpack_f64` additive DLPack
    helpers; `tensor2_from_dlpack_with_data` eliminating a redundant
    Tensor→data→Vec round trip (DV-021 S3-exec optimization).
  - Checkpoint shape validation: `load_state_dict` loads into a clone,
    validates shapes via `ResonanceLayer::validate_shapes` /
    `GatedPhaseActivation::validate_shapes`, and commits only on success —
    a shape-mismatched checkpoint raises a typed `ValueError` and leaves
    the target layer untouched (WP025-F1 fix).
  - 31 Python tests in `tests/test_train_bridge.py` (27 fast + 2 slow + 2
    shape-mismatch regression); all bridges pass `torch.autograd.gradcheck`
    in float64. `python/prin/nn/__init__.py` at 100% line coverage.
  - **DV-021 recorded:** boundary overhead at small shapes (+40.6%) exceeds
    the `<5%` acceptance target; moderate shape is within tolerance
    (+4.5%). Deferred to a future WP for boundary-crossing optimization.
  - **DV-005 re-audited:** CPU-path bridge delivered and validated; CUDA
    remains unbridged (no Burn CUDA backend in workspace), recorded as an
    explicit out-of-scope discovery.
  - **S3-exec addendum:** register-wide deferred-item review; DV-003
    disposition updated (opportunistic, not gated); DV-019 third flaky
    recurrence documented with two candidate mitigations.

- **WP-024 Oscillator-aware optimizers** (`crates/prin-train/`,
  Phase 4 third WP; sessions 0093–0096; audit
  `DOCS/audits/024-wp024-audit.md`, verdict `PASS-WITH-FINDINGS`, one D3
  finding: WP024-F1 AMENDED via plan amendment #29): oscillator-aware
  optimizer implementations rebuilding PRINet 3.0 `nn/optimizers.py`.
  - `feedback::OrderParameter` — global-or-per-group order parameter with
    Q3 dict resolution (SCALR's `Union[float, Dict[str, float]]` input).
  - `feedback::StepFeedback` — per-step input (order parameter, phase,
    amplitude).
  - `feedback::OscillatorOptimizer` — uniform `step`/`state_dict`/
    `load_state_dict` trait; the seam WP-025's thin `torch.optim.Optimizer`
    wrapper bridges to.
  - `sync_gd::SyncGd` — synchronized gradient descent with momentum and
    synchronization-barrier penalty (`penalty = λ·max(0, K_c − K)²`).
  - `rip::Rip` — Hebbian coupling-matrix update
    (`ΔK[i,j] = η·cos(φ[i] − φ[j])·|r[j]|·(r_target − r[i])`), diagonal
    zeroed, additive with plain gradient descent. Documented deviation:
    fixes `n_oscillators` at construction (PRINet 3.0 silently skips
    non-square-matching parameters).
  - `scalr::Scalr` — adaptive learning-rate optimizer with oscillation-aware
    decay, adaptive `r_min` via EMA, and per-group lr scaling entry point.
  - `error::TrainError` — extended with 8 new typed variants
    (`InvalidLearningRate`, `InvalidMomentum`, `InvalidWeightDecay`,
    `InvalidSyncPenalty`, `InvalidCriticalOrder`, `InvalidTargetAmplitude`,
    `InvalidRMin`, `InvalidAlpha`).
  - 57 new unit tests, 5 golden-value parity tests against actual PRINet 3.0
    optimizer classes at `rtol=1e-9, atol=1e-12`, 1 public-API regression
    test, 3 doctests; 97.9–100% region / 99.7–100% line coverage across all
    four new source files.
  - Deterministic resume via serde `State` snapshots with `load_state_dict`
    re-validation through original constructors.
  - **Plan amendment #29:** PSR-023 §7's WP-024 declaration named
    `PhaseAdam`/`KuramotoOptimizer` (non-existent in PRINet 3.0); formally
    read as `SCALR`/`RIP`/`SyncGD`/`scalr.rs`/`rip.rs`/`sync_gd.rs`
    (the delivered, reference-verified scope).
  - **DV-020 closed** (naming discrepancy resolved by amendment #29).

- **WP-023 Inhibition, activations, and HEP** (`crates/prin-train/`,
  Phase 4 second WP; sessions 0089–0092; audit
  `DOCS/audits/023-wp023-audit.md`, verdict `PASS-WITH-FINDINGS`, one D4
  finding: WP023-F1 FIXED in S3): second `prin-train` increment, implementing
  competitive inhibition, complex/phase activation functions, holomorphic energy
  evaluation, and Equilibrium Propagation training.
  - `inhibition::FeedbackInhibition` — feedback lateral inhibition with straight-through
    estimator (STE): hard top-$k$ forward competitive selection and soft
    temperature-scaled sigmoid backward gradients, with optional fractional target sparsity.
  - `activations` — `d_silu` (analytic SiLU derivative), `ComplexTensor` (real/imaginary
    pair representation), `HolomorphicActivation` (split-complex $\tanh$), `phase_activation`
    (periodic $[-\pi, \pi)$ wrapping), and `GatedPhaseActivation` (trainable gate bias
    module).
  - `energy::HolomorphicEnergy` — holomorphic scalar energy decomposition ($E_{\text{coup}}$,
    $E_{\text{self}}$ unit-amplitude penalty, and $\beta$-weighted task loss).
  - `hep::HolomorphicEp` — Holomorphic Equilibrium Propagation trainer orchestrating free
    and $\pm\beta$ nudged phases with closed-form contrastive coupling gradients.
  - `error::TrainError` — extended with `InvalidK`, `DivisionByZero`, `StepLimitExceeded`,
    and `BetaTooSmall` variants.
  - 93 unit/property tests, 5 new golden-value parity tests against PRINet 3.0, 6 doctests;
    98.4–99.6% line coverage across all 7 `prin-train` source files.
  - **Preserved third-party behavior and test observation:** DV-018 recorded `burn-tensor`'s
    internal `f32` downcast in default `sigmoid` (precision floor ~1e-7, accommodated via
    `rtol=1e-6`/`eps=1e-4` gradchecks); DV-019 recorded intermittent thread contention in
    WP-022 `bands::tests::gradients_flow_to_every_parameter`.
  - **S3 audit remediation (WP023-F1):** extended `crates/prin-train/tests/public_api.rs`
    with compile-time check for crate-root `GatedPhaseActivationParams` re-export (commit `11821c0`).
  - **S4 documentation closure (session 0092):** Migration Guide updated with WP-023 symbol
    entries; `crates/prin-train/` and `crates/` READMEs updated; `DOCS/experiments/`,
    `DOCS/audits/`, `DOCS/reports/`, `DOCS/README.md` updated; Project State Report
    `DOCS/reports/023-project-state.md` issued, declaring WP-024 (Oscillator-aware optimizers)
    with maintainer approval.

- **WP-022 Trainable bands and resonance primitives** (`crates/prin-train/`,
  Phase 4 first WP; sessions 0085–0088; audit
  `DOCS/audits/022-wp022-audit.md`, verdict `PASS-WITH-FINDINGS`, two D4
  findings: WP022-F1 AMENDED via Project Plan amendment #27, WP022-F2 FIXED
  in S3): first `prin-train` implementation, built on the Burn autodiff
  backend (`burn` 0.16, `std`/`ndarray`/`autodiff` features — first use of Burn
  in this repository).
  - `bands::DiscreteDeltaThetaGamma` — trainable discrete-time multi-rate
    hierarchical oscillator network (Burn `Module` rebuild of PRINet 3.0's
    `core.propagation.networks.DiscreteDeltaThetaGamma`): learned intra-band
    coupling, delta→theta/theta→gamma PAC gating, Stuart–Landau amplitude
    dynamics.
  - `layers::ResonanceLayer` — trainable single-layer extended-Kuramoto
    resonance primitive (Burn `Module` rebuild of PRINet 3.0's
    `nn.layers.ResonanceLayer`): learned coupling, decay, input projection,
    frequency modulation. Documents one deliberate deviation from the
    reference: a real-valued, fully differentiable initial-state projection
    in place of PRINet 3.0's FFT-based initializer (the Kuramoto step
    dynamics themselves are bit-faithful and parity-tested).
  - Both expose validated `Config`/`Params`/`State` contracts (typed
    `TrainError` on shape/dtype/finiteness violations), a `strict-checks`
    feature for typed non-finite-output guards, unit/property/gradient
    (autodiff-vs.-central-finite-difference)/serialization
    (`burn::record`)/golden-value-parity (`torch==2.13.0+cpu` float64,
    `DOCS/test_and_benchmark_results/wp022_generate_prinet_references.py`)
    tests, and two runnable rustdoc examples. 37 new tests; 98–99% line
    coverage on all three new source files.
  - **GPU CI runner strategy decided (Project Plan amendment #26):**
    self-hosted GPU runner, confirming and extending `gpu.yml`'s existing
    `[self-hosted, gpu]` design with a new `gpu-wgpu` job. Closes R24 (Phase
    3 analytics) at its assigned checkpoint; DV-001/DV-002 updated to record
    the decision with runner registration (an out-of-band GitHub Settings
    action) as the sole remaining step. DV-005 re-audited and confirmed
    unaffected (this session's Burn primitives are CPU-only `NdArray`, no
    DLPack touched).
  - **Inherited `bincode` advisory (DV-017), governed by Project Plan
    amendment #27:** `bincode` 2.0.1 (transitive via `burn-core`'s
    record/serialization path) carries RUSTSEC-2025-0141 ("unmaintained",
    informational — no CVE, no patched version, no affected-API disclosure).
    S3 recorded the Coding Standards §6.2 threat assessment and maintainer
    acceptance with the same per-cycle `cargo audit` re-check cadence as the
    existing accepted `paste` advisory (DV-008, amendment #9); compensating
    control is the existing record-roundtrip regression coverage on both
    modules. Closes audit finding WP022-F1 as AMENDED.
  - **S3 audit remediation (WP022-F2):** `DiscreteDeltaThetaGammaParams` and
    `ResonanceLayerParams` are now re-exported at the `prin-train` crate
    root (alongside the existing `TrainError` re-export) so callers can name
    them in explicit type annotations without reaching into submodule paths;
    compile-guarded by the new `crates/prin-train/tests/public_api.rs`
    regression test.
  - **S4 documentation closure (session 0088):** Migration Guide gained the
    WP-022 `prin-train` symbol entry (contracts, dynamics, the deliberate
    FFT→real-valued init deviation, parity tolerances); `crates/prin-train`/
    `crates/` READMEs updated; stale indexes corrected
    (`DOCS/reports/README.md` 020/021/022 entries + DV-register pointer,
    `DOCS/audits/README.md` 022 + EMA-002 artefacts, `DOCS/README.md`
    current-state pointers); session 0086/0087 register rows corrected to
    `COMPLETE` from committed evidence; Project State Report
    `DOCS/reports/022-project-state.md` issued, declaring WP-023
    (Inhibition, activations, and HEP) with maintainer approval.

- **Phase 3 recommendation implementation** (inter-phase process improvement, R21–R25
  disposition in `DOCS/ANALYTICS/phase-3/phase-3-recommendation-implementation-governance.md`):
  - Fixed PA3-F1/PA3-F2: `DOCS/PRIN_Project_Plan.md` §6's Phase 3 roadmap row now carries
    `✅ COMPLETE`; `DOCS/experiments/README.md`'s file index now lists
    `0081-wp021-s1-handoff.md` (R21, P0).
  - Phase-closing cross-cutting document currency added to `Documentation_Standards.md` §7
    (new item 9): at every phase-closing S4, explicitly verify and update the Project Plan §6
    roadmap table, `DOCS/experiments/README.md`'s index, and `SESSION_REGISTER.md`'s Global
    Sessions section — not just the CHANGELOG entries R16 already covers (R22, P1).
  - Maintainer decision (2026-08-18): the Snyk-CLI-only posture is intentional and permanent
    after Snyk MCP was unavailable across 4 consecutive Executive Audit sessions with the CLI
    serving as a fully effective compensating control throughout. `ANALYTICS_METHODOLOGY.md`
    §5.1 item 11 and `Executive_Audit_Governance_and_Methodology.md` §2 principle 6 updated to
    record the decision and retire the standing escalation (R23, P1).
  - R24 (consolidate the DV-001/DV-002/DV-005 GPU CI runner strategy gap) deferred to WP-022 S1
    (session 0085) with its three DV register entries narrowed to that single re-audit gate; R25
    (investigate the `windows-latest` CubeCL-CPU slowdown, DV-016) recorded as opportunistic and
    explicitly not WP-gated, per `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`.

- **Executive Mathematical Audit Session 002 (EMA-002)** — Phase 3 close
  mathematical audit; report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_002.md`
  (`PASS-WITH-REMEDIATION`, finding M-F7 carried forward from M-F3).
  Re-verified all 25 existing claims against `1604bd6` (zero regressions);
  added 3 new GPU kernel claims (`prin-kernels-gpu-properties.json`):
  GPU-RK4-01 (RK4 Butcher tableau, SymPy symbolic proof), GPU-RED-01
  (hierarchical reduction associativity, SymPy symbolic proof), GPU-KNN-01
  (sparse k-NN coupling normalization, SymPy symbolic proof). All 3 new
  claims reached genuine `PASS`. 28 total claims across 6 ledgers; 21 PASS,
  7 REQUIRES_HUMAN_REVIEW (same M-F3 policy-gate interaction as EMA-001R,
  resolved by documented sign-off per DV-013/R20).

### Fixed

- **`Hotfix-DV019` (2026-08-26, dedicated governed hotfix/correction
  session; handoff note `DOCS/experiments/hotfix-dv019-handoff.md`):**
  closed DV-019, the flaky `gradients_flow_to_every_parameter`-class
  gradient-presence test recurring across `bands.rs`/`hybrid.rs`/
  `phase_tracker.rs` since WP-023, executing Phase 5 analytics
  recommendation R33 (P0) and satisfying the hard entry-condition gate
  EA-006 added to WP-033 S1. Obtained the first on-demand local
  reproduction of the flake (`cargo test -p prin-train --lib` at default
  concurrency: 9 of 12 runs failed pre-fix, 0 of 12 with
  `--test-threads=1`), which corrected the leading root-cause hypothesis:
  not a rayon summation-order artifact in three specific tests' fixtures,
  but a confirmed thread-safety limitation in `burn-autodiff` 0.16.1's
  default runtime — every `Autodiff<B>` graph in the process shares one
  global `AutodiffServer` (`runtime/mutex.rs`) whose `backward()`-triggered
  memory-management sweep has no per-graph isolation, so concurrently
  running tests on different OS threads (Rust's default test harness) can
  free each other's in-flight graph nodes. Fixed via a `prin-train`-private,
  `#[cfg(test)]`-gated serialization mutex
  (`crate::support::autodiff_test_guard`) applied to all 42
  autodiff-graph-touching tests across 14 files (not only the 3
  originally-named modules — reproduction showed the defect was not
  confined to them). Kept fixture hardening attempted first (`bands.rs`
  batch 2→4/steps 3→6; `hybrid.rs`/`phase_tracker.rs` symmetric
  `Tensor::ones` inputs replaced with distinct seeded draws) as
  independently-justified defense in depth, having directly confirmed it
  alone does not close the defect. Verified with 51 consecutive clean
  `cargo test -p prin-train --lib`-class runs plus 10/10 clean under the
  exact concurrent-process scenario that reproduced the pre-fix defect;
  `cargo fmt`/clippy/`cargo doc`/`cargo audit`/Snyk Code all clean; the
  Python-side DV-019 sub-item re-confirmed clean (15/15 isolated runs).

- **Post-Phase-5 CI hotfixes (2026-08-25, commits `cb5660b`/`5d90427`; recorded
  retroactively by EA-006, `[RETROACTIVE UPDATE - Executive Audit 006]`):**
  two maintainer-authored hotfix commits landed on `main` immediately after
  WP-032 S4 (`a19dbfe`) closed Phase 5, legitimately bypassing S1 ordering
  under Development Workflow and Audit Standards §7 (the `python` workflow
  was failing live on `main`) but never recorded in the deviation ledger or
  this changelog at the time, per §7's own requirement. `cb5660b` skips
  `dtolnay/rust-toolchain`/`Swatinem/rust-cache` on the self-hosted Windows
  matrix leg in `rust.yml`/`python.yml` (WSL bash, required by the action,
  is unavailable on `PRIN-GPU-Runner`; Rust is pre-installed there anyway).
  `5d90427` re-routes `python.yml`'s Windows Python tests back to
  GitHub-hosted `windows-latest` (the self-hosted runner lacks registry
  permissions for `actions/setup-python` to install Python 3.11/3.12/3.13
  side by side); `rust.yml`'s Windows leg stays on the self-hosted runner.
  Live-verified on HEAD (`5d90427`): all 6 non-skip workflows `success`.
  See `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-024 for the
  corrected final CI topology and `DOCS/audits/EXECUTIVE_AUDIT_REPORT_006.md`
  finding E-F1 for the full audit narrative. The §7-required retro-audit is
  due at WP-033 S2 (not yet run).

- **WP-025 S3-exec (executive remediation session, 2026-08-19):** deferred-item
  remediation session tied to WP-025, performed after the normal S3 cycle's
  closure (session 0099) with maintainer-authorized added scope. Fixed a
  redundant Tensor→data round-trip in `crates/prin-py/src/bindings/train.rs`'s
  `PyResonanceLayerBridge::forward`/`PyGatedPhaseActivationBridge::forward`
  (`tensor2_from_dlpack_with_data` replaces a separate DLPack read followed by
  `tensor.clone().into_data().to_vec()`); verified zero behavior change and
  rigorously re-measured the DV-021 boundary-overhead evidence (5-run
  process-level median-of-medians, same protocol as the S3 closure table).
  The fix is real but does not close DV-021 — the gap is dominated by
  Python-side `torch.autograd.Function.apply()`/`from_dlpack()` fixed
  dispatch cost, not the Rust glue this commit touches. DV-021 and DV-005
  reassigned from an unspecified "future WP" to the concrete WP-027 S1 Phase
  4 gate checkpoint. Reviewed every item in
  `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`: re-confirmed DV-008/DV-009/
  DV-017 unchanged (`cargo audit`, GitHub secret-scanning availability);
  gave DV-003/DV-016 an explicit opportunistic/not-WP-gated disposition; DV-019
  recurred a third time (immediately re-run clean) with its root cause
  narrowed to `bands.rs:801`'s `w_gamma` gradient-presence assertion and two
  candidate fixes recorded for a dedicated future hotfix session. See
  `DOCS/audits/025-wp025-audit.md` §8 and the register's 2026-08-19 review
  log entry for full evidence.

- **EMA-002 tooling:** removed 5 stale `type: ignore[import-not-found]`
  comments from `tools/math_audit_run.py` (mypy `--strict` now clean).

- **Executive Audit Session 004 (EA-004)** — full-project audit across E1–E10 covering the delta
  since EA-003 (WP-017 through WP-021, Phase 3 close); report
  `DOCS/audits/EXECUTIVE_AUDIT_REPORT_004.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F2):
  - **E-F1 (D1):** discovered GitHub Actions is currently blocked by an account-level
    billing/spending-limit condition — all 5 push-triggered workflows fail within seconds on
    `933f8a3` with zero steps executed ("The job was not started because recent account payments
    have failed or your spending limit needs to be increased"). Confirmed persistent via a live
    `gh run rerun`. Not fixable in-session (external account condition); every gate the blocked
    workflows would run was independently reproduced locally with 100% clean results. Passed
    forward to the maintainer as DV-014 with an explicit required action (resolve billing, then
    re-run the affected workflows).
  - **E-F2 (D1):** found the cumulative deviation-ledger corruption pattern from EA-003 (E-F1)
    had recurred: `DOCS/reports/020-project-state.md` §3 silently rewrote the WP015-F6 and
    WP016-F1..F7/WP017-F1..F5 rows with two fabricated, non-existent commit hashes (`57c5f4a`,
    `8c1e8d3`) and descriptions matching neither the real audit closure tables nor any git
    history; carried forward unremediated into `021-project-state.md`.
    `tools/check_deviation_ledger.py` — built at WP-017 S4 specifically to catch this — was run
    at WP-017/WP-018 S4 but silently dropped from the S4 checklist for WP-019/020/021, so the
    recurrence went undetected for three cycles. Restored the 13 rows in `021-project-state.md`
    from verified ground truth (tagged `[RETROACTIVE UPDATE - Executive Audit 004]`); added a
    correction pointer note to `020-project-state.md` (historical record preserved, not
    rewritten); fixed the process gap durably by wiring the checker into `python.yml` CI (fails
    the `lint` job on any future recurrence) and into `Development_Workflow_and_Audit_Standards.md`
    §3 S4 as explicit action 6.
  - **Same-day addendum (2026-08-17):** maintainer resolved the GitHub Actions billing condition;
    live re-verification (`gh run rerun` + fresh pushes) closed DV-014 with evidence. Surfaced and
    fixed a genuine bug in the new deviation-ledger CI step itself: `actions/checkout@v4`'s default
    shallow clone made *every* historical commit hash unresolvable on the runner, not just the
    fabricated ones — fixed with `fetch-depth: 0` (`1bce918`). Also discovered (non-blocking) that
    `windows-latest` CI is ~10-15× slower than local hardware for two CubeCL-CPU test steps
    (~77 min total job time, eventually green, not a hang); recorded as DV-016 and hardened with
    `timeout-minutes: 120` on `rust.yml`'s `test` job as a safety net pending root-cause investigation.
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

- **WP-021 GPU integration and Phase 3 gate** (`prin-sim`, `prin-kernels`, Phase 3 fifth and final WP; sessions 0081–0084; audit `DOCS/audits/021-wp021-audit.md`, verdict `PASS-WITH-FINDINGS`, one D4 finding WP021-F1 FIXED in S3):
  - `prin-sim::gpu` module (`crates/prin-sim/src/gpu.rs`) integrating `prin-kernels` CubeCL dispatch into simulation:
    - `GpuSparseKuramoto` — `Dynamics` implementation dispatching sparse Kuramoto coupling derivatives through `prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto` while reusing `SparseCoupling` CSR topology and validating uniform `K/degree` weights at construction time.
    - `GpuMeanFieldEngine` — dense all-to-all RK4 stepper wrapping `prin_kernels::mean_field_rk4::cubecl::step_auto` with `engine::Trajectory` recording.
    - `GpuBandStepper` — three-band (delta/theta/gamma) discrete-time stepper wrapping `prin_kernels::discrete_step::cubecl::discrete_step_auto`.
    - Precision boundary handling: explicit `to_f32`/`to_f64` conversions between `f64` (simulation/dynamics authority) and `f32` (device kernels).
  - `prin-sim::error` — new `SimError` variants (`MeanFieldKernel`, `DiscreteStepKernel`, `SparseKnnKernel`) wrapping `prin-kernels` error types.
  - `prin-kernels` dispatch-priority bug fix — corrected `mean_field_rk4`, `discrete_step`, `pac`, and `sparse_knn` `*_auto` functions to try CUDA before wgpu (CUDA → wgpu → CPU), matching `backend::auto_detect_order()` and documented priority. Added priority regression tests (`step_auto_prefers_cuda_over_wgpu_when_both_available`, `discrete_step_auto_prefers_cuda_over_wgpu_when_both_available`).
  - Hardware CUDA kernel equivalence — first execution on physical NVIDIA hardware (GeForce RTX 4060, driver 595.95 / CUDA 13.2) in project history: 113 `prin-kernels` CUDA tests pass at `rtol=1e-5, atol=1e-6` across mean-field RK4 ($N=64, N=1\mathrm{M}$), discrete step ($[600, 600, 600]$), PAC ($N=600$), and sparse k-NN ($N=300, k=6$).
  - New criterion benchmark (`crates/prin-sim/benches/gpu_bench.rs`) at §N1 target sizes: `GpuMeanFieldEngine` achieves ~5.9× speedup over CPU dynamics at $N=1{,}000{,}000$ (~32 ms vs ~192 ms).
  - CI: added `cargo test -p prin-sim --features cpu -- --test-threads=1` to `.github/workflows/rust.yml`.
  - S2 audit found one D4 finding (WP021-F1: session 0081 status mismatch in `SESSION_REGISTER.md`); S3 fixed it with a CLEAN delta re-audit.
  - Phase 3 Exit Gate: all 5 Phase 3 work packages (WP-017 through WP-021) are complete with clean audits; Phase 3 pre-release gate verified.
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
- **WP-020 Fused discrete step and reductions** (`prin-kernels`, Phase 3 fourth WP; sessions
  0077–0080; audit `DOCS/audits/020-wp020-audit.md`, verdict `PASS`, zero S2 findings; one
  self-discovered D4 WP020-F1 FIXED in S3):
  - `discrete_step::discrete_step_cpu` — CPU reference (numerical authority) for the fused
    three-band (delta/theta/gamma) discrete-time stepper. Reproduces the PRINet 3.0
    `DeltaThetaGammaNetwork` discrete-time stepper semantics: step delta via one Euler evaluation,
    gate theta's amplitude with the PAC modulation factor computed from delta's just-stepped mean
    phase, step theta, gate gamma from theta's just-stepped mean phase, step gamma. Reuses
    `mean_field_rk4::mean_field_derivatives_into`/`wrap_phase`/`clamp_amp` (promoted from private
    to `pub(crate)` this session) for the per-band Kuramoto/Stuart–Landau derivative and Euler
    update (Coding Standards §1, "one algorithm, one implementation").
  - `discrete_step::cubecl::discrete_step_cubecl` — four `#[cube(launch)]` kernels
    (`complex_order_reduce`, `real_sum_reduce`, `band_euler_step`, `pac_gate`) completing the
    10-launch fused path. Host dispatch (`try_*_wgpu`/`_cpu`/`_cuda`, `discrete_step_auto`)
    mirrors `mean_field_rk4::cubecl`'s pattern with `StepReport` device-event timing.
  - `mean_field_rk4::wrap_phase`/`clamp_amp`/`mean_field_derivatives_into` — promoted from
    private to `pub(crate)` with doc comments explaining the reuse; no behavior change.
  - New criterion benchmark (`benches/discrete_step_bench.rs`) at band sizes `[4096, 16384, 65536]`
    (N=86,016): `fused_cpu_native` ~2.1 ms vs. `unfused_cpu_native` ~7.9 ms (~3.7–3.8× speedup).
    Pilot benchmark, not a regression gate (Benchmarking Standards §2.2).
  - 29 new tests (15 CPU unit/error-path + 2 proptests + 12 CubeCL) in S1. Kernel-equivalence at
    small N (`[8,16,32]`), non-block-aligned bands (`[300,777,513]`), and large N (`[2048,16384,
    65536]`, N=84,992) pass at `rtol=1e-5, atol=1e-6`. CubeCL-CPU multi-block equivalence and
    5-repeat determinism regression test pass.
  - S2 audit found zero findings (`PASS`); S3 recorded a no-change closure with one
    self-discovered D4 finding (WP020-F1, `cargo test --features cpu` count transcription error
    in the audit report's own §2) FIXED with a CLEAN delta re-audit.
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

### Security

- **WP-022 `h2` RUSTSEC-2026-0258 hotfix (post-S4):** the CI `rust` workflow
  `audit` job discovered a new low-severity DoS vulnerability (unbounded empty
  DATA frames) in `h2` 0.4.15, a transitive build-time dependency of `cubecl-cpu`
  via `tracel-llvm-bundler` → `reqwest` → `hyper`. Bumped `h2` to 0.4.16 in
  `Cargo.lock` (commit `1b7a8e9`); `cargo audit` is clean at the governed
  threshold. Recorded as WP022-F3 and closed same day.

### Changed

- **Push/CI cadence (Project Plan amendment #28):** S1, S2, and S3 sessions
  now commit locally only and never push; only the S4 commit that closes a
  cycle is pushed to `origin/main`, carrying the full S1–S4 commit range for
  that WP in one push — the sole point at which CI runs for the cycle.
  Previously each session pushed and triggered its own CI run. Hotfixes
  (broken `main`, live security findings) remain the sole exception and may
  still push immediately, outside this cadence. See Development Workflow and
  Audit Standards §3 ("Push and CI cadence") and Coding Standards §4.

### Fixed

- **EDA-001 remediation (2026-09-01):** all four findings from the first
  Executive Documentation Audit closed. D-F1 (D2): restructured napoleon
  `Attributes:` sections to per-field attribute docstrings in
  `python/prin/nn/mot_evaluation.py` (`Detection`, `TrackingResult`) and
  `python/prin/nn/allocation.py` (`OscillatorBudget`) — same root-cause class
  as PA4-F2/R26; fresh-directory Sphinx `-W` build now clean (0 warnings,
  down from 19). D-F2 (D3): added missing `036b`/`036c`/`036d` PSR entries
  to `DOCS/reports/README.md`. D-F3 (D3): added missing `036b`/`036c`/`036d`
  audit entries to `DOCS/audits/README.md`. D-F4 (D3): modified
  `tools/check_deviation_ledger.py` to detect delegation pointers in sub-PSRs
  (e.g. "ledger maintained in PSR-036 §3") and resolve the canonical ledger
  automatically; CI gate now compares 120 rows vs 120 rows for sub-PSR pairs
  instead of trivially passing on 0 vs 0.

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

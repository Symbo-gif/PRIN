---

# PRIN Project State Report — Cycle 036E

**Date:** 2026-09-02
**Cycle:** 036E (WP-036E "GPU device-resident execution path")
**Completed sessions:** 0144Q + 0144Q1–0144Q3 (S1), 0144R (S2), 0144S (S3),
0144T (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**8 of 8**
  phase-6 WPs now complete or closing: WP-033, WP-034, WP-035, WP-036,
  WP-036A, WP-036B, WP-036C, WP-036D, WP-036E).
- **This cycle delivered:**
  - **`prin-kernels` device-`Handle` dispatch layer** (`0144Q1`):
    `MeanFieldDeviceState<R>`, `SparseKnnDeviceState<R>`,
    `DiscreteStepDeviceState<R>` — device-resident `Handle`s for each
    algorithm's state; `step_cubecl_device`, `sparse_knn_coupling_device`,
    `discrete_step_device` run the full launch sequences without touching
    host memory. Host-slice wrappers (`step_auto` etc.) become thin
    upload → device-path → download wrappers (one algorithm, one
    implementation). `CubeclBufferPool` drops `out_*` handles, gains
    zeroed `k_zero`.
  - **`prin-sim` persistent device buffers + DV-003 on-device combine**
    (`0144Q2`): `GpuMeanFieldEngine` holds `ComputeClient` +
    `MeanFieldDeviceState` + `CubeclBufferPool` across `step()` — state
    stays on-device. `GpuBandStepper` analogously holds
    `DiscreteStepDeviceState`. `GpuSparseKuramoto` uploads CSR topology
    once at construction. On-device CUDA `f64` level-2 order-parameter
    combine (`order_param_finalize_f64`); batched read-backs (2
    `f32`/stage vs `2·num_blocks`). Five CUDA clippy lints fixed
    (WP036E-F2).
  - **`prin-py` export zero-copy DLPack + `_torch_compat` device path**
    (`0144Q3`): `CudaExternalF32` / `export_dlpack_f32_cuda` — CubeCL
    `Handle` → `kDLCUDA` DLPack capsule via
    `ComputeClient::get_resource(handle).ptr`, no host round-trip.
    `GpuMeanFieldEngine.state()` returns three `kDLCUDA` capsules.
    `_torch_compat.py` GPU branches route through the device path; CPU
    `else` byte-for-byte unchanged. `.pyi` stubs updated. 6-test
    zero-copy suite (5 `@pytest.mark.gpu` + 1 CPU regression).
  - **S2 audit** (`DOCS/audits/036e-wp036e-audit.md`): verdict FAIL
    (1 D1, 2 D2, 1 D4). Four findings: WP036E-F1 (CUDA device-event
    timing unreachable on `cubecl 0.10.0`), WP036E-F2 (5 CUDA clippy
    lints), WP036E-F3 (≥95% changed-line coverage not demonstrated),
    WP036E-F4 (GPU count 13→12 + phase index stale).
  - **S3 remediation** (`0144S`): all four findings resolved. F1
    AMENDED via **plan amendment #44** (DV-003 → `PARTIALLY CLOSED`,
    genuine device-event timing re-gated). F2/F3/F4 FIXED. Changed-line
    coverage 98.71% after DV-004 exclusion. Delta re-audit CLEAN.
  - **S4 documentation** (`0144T`): READMEs updated (`crates/prin-kernels/`,
    `crates/prin-sim/`, `crates/prin-py/`, `tests/`); `CHANGELOG.md`
    entry; `DOCS/sphinx/parity_report.rst` GPU-vs-CPU tolerance table
    + device-event timing note; `DEFERRED_VALIDATION_REGISTER.md` —
    DV-030 and DV-003 updated with S4 closure confirmation; this PSR
    issued.
  - **Plan amendments #43/#44** adopted and executed: #43 re-scoped
    DV-030 to `PARTIALLY CLOSED` and decomposed S1 into `0144Q1`–`0144Q3`;
    #44 re-scoped DV-003 to `PARTIALLY CLOSED` (device-event timing
    unreachable on `cubecl 0.10.0`).
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#44
  remain in force.
- **Audit:** `DOCS/audits/036e-wp036e-audit.md` — S2 verdict FAIL. S3
  remediation: F1 AMENDED (amendment #44), F2/F3/F4 FIXED, delta
  re-audit CLEAN. No unresolved D1/D2 finding exists.
- **Session Register:** 0144Q + 0144Q1–0144Q3 (S1), 0144R (S2), 0144S
  (S3), 0144T (S4) all marked COMPLETE; 0144U (WP-036F S1) is the
  registered successor.
- **WP-036E is CLOSED.**

---

## 2. Metric trends

| Metric | Previous (PSR-036D) | Current (PSR-036E) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1540 passed, 0 failed, 1 ignored | **1540 passed**, 0 failed, 1 ignored (unchanged) | 100% where defined |
| Rust tests passing (CUDA) | N/A | **All passed** (`cargo test --workspace --features cuda`) | 100% |
| Python tests passing (CPU fast) | 1784 passed, 2 skipped, 16 deselected | **2740 passed**, 202 skipped, 30 deselected | 100% (1 pre-existing timing flake under host contention, CI authoritative) |
| Python GPU tests (runner) | 7 passed | **12 passed**, 2963 deselected, 80.54s on RTX 4060 (+5 WP-036E Q3 zero-copy tests) | 100% on runner |
| Coverage (changed code) | 97.4% overall | **98.71%** changed-line after DV-004 exclusion (1224/1240); 97.22% raw (1224/1259) | ≥95% changed |
| Docstring coverage (interrogate) | 97.6% overall | **97.6%** overall (unchanged) | ≥95% overall |
| Parity cases passing | 498 acceptance + 7 GPU; 1 Parity Report entry | **498 acceptance + 12 GPU**; **2 Parity Report entries** (WP-036D GPU sparse k-NN + WP-036E device-resident kernel equivalence/timing) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 with 3 governed allowed warnings; bandit 0 findings | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** (fresh-directory build) | 0 warnings |
| `check_no_python_numerics.py` | clean (19 modules) | **clean (19 modules)** | clean |
| `verify_api_surface` | `(set(), set())` | **`(set(), set())`** — no new `prin` public symbol | `(set(), set())` |
| `check_dv_register_gates.py` | pass | **pass** (33 DV rows × 198 session entries) | pass |

**Verification commands re-run in S4 (2026-09-02, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0 / torch 2.11.0+cu128 / RTX 4060):**

```
cargo fmt --all -- --check                                                        # clean
cargo clippy --workspace --all-targets -- -D warnings                             # exit 0
cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings         # exit 0
cargo clippy -p prin-sim --features cuda --all-targets -- -D warnings             # exit 0
cargo test --workspace --features cuda                                            # all passed
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/               # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/      # 242 files already formatted
.venv\Scripts\mypy python/prin --strict                                           # 62 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin                # 97.6%, PASS
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml                  # 0 findings
cargo audit                                                                       # exit 0 (3 governed warnings)
.venv\Scripts\python tools/check_no_python_numerics.py                            # clean (19 modules)
.venv\Scripts\python tools/check_dv_register_gates.py                             # pass (33 DV rows, 198 sessions)
.venv\Scripts\python -c "import prin; ...verify_api_surface(prin.__all__)"       # (set(), set())
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 2740 passed, 202 skipped, 30 deselected
.venv\Scripts\python -m pytest tests/ -m gpu -rs --basetemp=.pytest_basetemp     # 12 passed, 2963 deselected, 80.54s
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html         # build succeeded (fresh dir)
```

---

## 3. Deviation ledger (cumulative)

### New findings this cycle

| ID | Severity | Status | Resolution |
|---|---|---|---|
| WP036E-F1 | D1 | **AMENDED** | Plan amendment #44: genuine CUDA device-event timing not reachable on `cubecl 0.10.0`; DV-003 → `PARTIALLY CLOSED`; on-device `f64` combine + bounded residual delivered; re-gated to CubeCL `TimingMethod::Device` CUDA release. |
| WP036E-F2 | D2 | **FIXED** | Five CUDA clippy lints resolved (`try_create_client` restructured; `MeanFieldInner`/`BandStepperInner` device payloads boxed; two `needless_range_loop`). Commit `0c6e8f4`. |
| WP036E-F3 | D2 | **FIXED** | Changed-line coverage 98.71% after DV-004 exclusion; 9 regression tests added; `host_f64_combine` deduplicated. Commit `03b6059`. |
| WP036E-F4 | D4 | **FIXED** | GPU count corrected (13→12); phase-6 index `0144Q1`–`0144Q3` → `COMPLETE`. Commit `cca5027`. |

### Cumulative ledger

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward. The WP-036E findings above are the most recent additions. All
previous findings from PSR-036/PSR-036A/PSR-036B/PSR-036C/PSR-036D remain
at their last recorded status.

---

## 4. Plan amendments this cycle

Two new amendments adopted and executed:

- **Amendment #43** (2026-09-02): WP-036E S1 (`0144Q`) re-scoped —
  bidirectional zero-copy Torch↔CubeCL DLPack kernel-input not reachable
  on `cubecl 0.10.0`; DV-030 → `PARTIALLY CLOSED`; S1 decomposed into
  `0144Q1`–`0144Q3`. Planned session count 253 → **256**.
- **Amendment #44** (2026-09-02): DV-003 → `PARTIALLY CLOSED by WP-036E`
  — genuine CUDA device-event timing not reachable on `cubecl 0.10.0`
  (`cubecl-cuda` hard-registers `TimingMethod::System`); on-device `f64`
  combine + bounded residual delivered and kept; re-gated to CubeCL
  `TimingMethod::Device` CUDA release or vendored shim WP.

---

## 5. Risks and blockers

- **DV-030 (device-resident GPU / zero-copy):** `PARTIALLY CLOSED` —
  device-resident buffers + device-`Handle` dispatch + on-device CUDA
  `f64` combine + export-direction zero-copy DLPack delivered;
  bidirectional zero-copy kernel-input re-gated to a `cubecl`
  external-memory API or vendored `cubecl-cuda` storage shim (dedicated
  future WP, not a Phase 7 entry blocker). `test_sparse_vram_subquadratic`
  retains its governed skip.
- **DV-003 (device-event timing):** `PARTIALLY CLOSED by WP-036E` —
  on-device CUDA `f64` combine + batched read-backs + bounded host
  residual delivered; genuine device-event timing re-gated to CubeCL
  `TimingMethod::Device` CUDA release.
- **DV-005 (CUDA Burn backend):** OPEN — `CLOSED as AMENDED` by
  amendment #38 (out of scope for 1.0.0). Standing disposition unchanged.
- **DV-001 (Linux Triton runner):** PARTIALLY VALIDATED — unchanged.
- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — allowed warnings per amendments #9/#27, re-verified this
  cycle (`cargo audit` exit 0).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action; routed to WP-038 S1.
- All other DV register items closed at or before PSR-036D remain closed;
  `tools/check_dv_register_gates.py` passes.
- No new risks introduced.

---

## 6. Next work package declaration — WP-036F

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144U-wp036f-s1-directml-controller-graph-execution.md`),
per Documentation Standards §7 item 5:

- **Title:** DirectML controller-graph execution.
- **Scope (files/crates/modules):** Re-export the subconscious controller
  ONNX graph with three-input `Gemm` nodes so `DmlExecutionProvider`
  executes it; extend cross-provider test coverage; record DirectML
  latency.
- **Plan sections advanced:** §6 (Phase 6 roadmap); amendment #13's
  deferred DirectML condition discharged.
- **Acceptance criteria:** Re-exported graph mathematically identical to
  current (differential test over 48-case set, CPU provider, bit-identical);
  `DmlExecutionProvider` executes it and agrees with CPU within tolerance;
  cross-provider harness widens automatically; F5 / DoD item 7 DirectML
  condition satisfied.
- **Non-goals:** VitisAI / Ryzen AI NPU execution (hardware-blocked);
  retraining/quantization symbols (DV-025, WP-036C scope); controller
  *algorithm* changes.
- **First session brief:**
  `DOCS/sessions/phase-6/0144U-wp036f-s1-directml-controller-graph-execution.md`
  (present in `SESSION_REGISTER.md` as `PLANNED`).
- **Maintainer approval:** Required before WP-036F S1 begins.

### WP-036F entry conditions

1. **WP-036E closed** — ✅ all S4 artefacts committed, all findings
   FIXED or AMENDED, delta re-audit CLEAN.
2. **No unresolved D1/D2 finding** — ✅ (WP036E-F1 AMENDED, WP036E-F2
   FIXED, WP036E-F3 FIXED, WP036E-F4 FIXED).
3. **Local gates green** — ✅ (CPU fast suite 2740 passed + 202 skipped;
   GPU 12/12 on runner; quality gates clean; docs build clean).
4. **`gpu.yml` run green** — CI authoritative at push.
5. **Maintainer approval** — pending.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(8/8 WPs complete or closing: WP-033, WP-034, WP-035, WP-036, WP-036A,
WP-036B, WP-036C, WP-036D, WP-036E; WP-036F is the registered successor).

**(b) `DOCS/experiments/README.md`:** Verified current.

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — 0144Q + 0144Q1–0144Q3 (S1), 0144R (S2), 0144S (S3),
0144T (S4) all marked COMPLETE; 0144U–0144X (WP-036F) marked PLANNED.

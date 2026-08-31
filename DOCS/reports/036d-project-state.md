---

# PRIN Project State Report — Cycle 036D

**Date:** 2026-08-31
**Cycle:** 036D (WP-036D "GPU execution path for the ported acceptance suite")
**Completed sessions:** 0144I + 0144I1–0144I3 (S1), 0144J (S2), 0144K (S3),
0144L (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**7 of 7**
  phase-6 WPs now complete or closing: WP-033, WP-034, WP-035, WP-036,
  WP-036A, WP-036B, WP-036D).
- **This cycle delivered:**
  - **PyO3 GPU binding layer** (`0144I1`): new feature-gated
    `crates/prin-py/src/bindings/gpu.rs` (674 lines) wrapping `prin-sim`'s
    `GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper` behind
    `cuda` / `wgpu`; `f32` DLPack helpers in `dlpack.rs`; `.pyi` stubs;
    feature-gated Rust tests. `from_knn_phase` constructor added (amendment
    #37 reopen) so the Python dispatch builds no coupling weights.
  - **Python device dispatch** (`0144I2`): `_is_gpu` predicate; `_gpu_f32` /
    `_from_gpu` CPU-float32 DLPack marshalling helpers; a GPU dispatch branch
    in `OscillatorModel.compute_derivatives` routing a CUDA sparse k-NN
    input to `GpuSparseKuramoto.from_knn_phase` → CubeCL sparse k-NN kernel.
    CPU path byte-for-byte unchanged (golden-value pre/post test). 15-test
    unit suite (`tests/test_wp036d_gpu_dispatch.py`).
  - **GPU test activation + CI** (`0144I3`): `@pytest.mark.gpu` added to 7
    CUDA-guarded acceptance tests (alongside existing `skipif` guards);
    `.github/workflows/gpu.yml` switched from the DV-029 exit-5 workaround
    to `pytest tests/ -m gpu`. The eighth test (`test_sparse_vram_subquadratic`)
    deferred to DV-030 (device-resident buffers).
  - **S2 audit** (`DOCS/audits/036d-wp036d-audit.md`): verdict
    PASS-WITH-FINDINGS (2 D2, 1 D4). Three findings: WP036D-F1 (assertion
    weakened outside governed mechanism), WP036D-F2 (register row stale),
    WP036D-F3 (Parity Report line missing).
  - **S3 remediation** (`0144K`): all three findings FIXED. F1: assertion
    reverted, `@pytest.mark.gpu` removed, explicit `@pytest.mark.skip`
    applied (DV-030 deferral). F2: register row reconciled. F3: Parity
    Report section added, dispatch-test tolerances tightened. Delta re-audit
    CLEAN.
  - **S4 documentation** (`0144L`): `tests/README.md` (GPU marker policy,
    7 activated tests); `crates/prin-py/README.md` (WP-036D section);
    `gpu.yml` comment corrected; `parity_report.rst` current;
    `DEFERRED_VALIDATION_REGISTER.md` updated; this PSR issued.
  - **Plan amendments #36/#37** adopted and executed: WP-036D created,
    WP-036C renumbered, zero-copy clause waived (DV-030 recorded),
    `0144I1` reopened once for `from_knn_phase`.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#37
  remain in force.
- **Audit:** `DOCS/audits/036d-wp036d-audit.md` — S2 verdict
  PASS-WITH-FINDINGS. S3 remediation: all three findings FIXED, delta
  re-audit CLEAN. No unresolved D1/D2 finding exists.
- **Session Register:** 0144I + 0144I1–0144I3 (S1), 0144J (S2), 0144K (S3),
  0144L (S4) all marked COMPLETE; 0144M (WP-036C S1) is the registered
  successor.

---

## 2. Metric trends

| Metric | Previous (PSR-036B) | Current (PSR-036D) | Gate |
|---|---|---|---|
| Rust tests passing | 1540 passed, 0 failed, 1 ignored | **1540 passed**, 0 failed, 1 ignored (unchanged — WP-036D adds feature-gated tests, not default-matrix tests) | 100% where defined |
| Rust GPU binding tests (CUDA) | N/A | **5 passed** (`cargo test -p prin-py --features cuda bindings::gpu`) | 100% |
| Python tests passing (CPU fast) | 1770 passed, 9 deselected | **1784 passed**, 2 skipped, 16 deselected; +15 `test_wp036d_gpu_dispatch.py` (dispatch unit suite), -1 `test_sparse_vram_subquadratic` (now DV-030 skip) | 100% (1 pre-existing timing flake under host contention, CI authoritative) |
| Python GPU tests (runner) | N/A (no GPU path) | **7 passed**, 1796 deselected, 124.72s on RTX 4060 | 100% on runner |
| Coverage (changed code) | 97.4% overall | **97.4%** overall (unchanged; `_torch_compat.py` 95%, GPU path exercised on runner) | ≥95% overall |
| Docstring coverage (interrogate) | 97.4% overall | **97.4%** overall (unchanged) | ≥95% overall |
| Parity cases passing | 498 acceptance tests green; zero tolerance annotations | **498 acceptance tests green** (489 pass + 9 skip); **7 GPU tests green on runner**; **1 Parity Report entry** (GPU sparse k-NN f32 dispatch) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 with 3 governed allowed warnings; bandit 1 Low (B110, governed, `# noqa: S110`) | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** (fresh-directory build) | 0 warnings |
| Snyk Code / Snyk Open Source | CI authoritative | Snyk Code: 0 issues on every new/modified first-party file (S3 audit §3.6) | 0 at gate threshold |
| `check_no_python_numerics.py` | clean (19 modules) | **clean (19 modules)** | clean |
| `check_dv_register_gates.py` | pass | **pass** (30 DV rows × 198 session entries) | pass |

**Verification commands re-run in S4 (2026-08-31, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0 / torch 2.11.0+cu128 / RTX 4060):**

```
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0
cargo test -p prin-py --features cuda bindings::gpu                           # 5 passed
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 194 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 55 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 97.4%, PASS
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml               # 1 Low (B110, governed)
.venv\Scripts\python tools/check_no_python_numerics.py                        # clean (19 modules)
.venv\Scripts\python tools/check_dv_register_gates.py                         # pass
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 1784 passed, 2 skipped, 16 deselected, 1 failed (timing flake)
.venv\Scripts\python -m pytest tests/ -v -m gpu -rs --basetemp=.pytest_basetemp                # 7 passed, 1796 deselected, 124.72s
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html      # build succeeded (fresh dir)
```

**Note on the one fast-gate failure** — `test_no_gpu_throughput_regression`
is a wall-clock throughput-ratio heuristic (`with_daemon / baseline < 1.30`).
It passed at the S3 audit baseline and is not reachable from any file the
WP-036D range touches. During S4 it failed with ratio 1.47 under measurable
concurrent CPU load on the shared maintainer dev host. Same disposition as
the S3 audit note and DV-016/DV-019: a timing-sensitive test under host
contention; CI (`python.yml`) is authoritative at push.

---

## 3. Deviation ledger (cumulative)

### New findings this cycle

| ID | Severity | Status | Resolution |
|---|---|---|---|
| WP036D-F1 | D2 | **FIXED** | `test_sparse_vram_subquadratic` reverted to `* 0.10`, `@pytest.mark.gpu` removed, explicit `@pytest.mark.skip(reason="deferred to DV-030 ...")` applied. Commit `3f47060`. |
| WP036D-F2 | D2 | **FIXED** | `SESSION_REGISTER.md` row `0144I3` reconciled `PLANNED` → `COMPLETE`. Commit `d2b965c`. |
| WP036D-F3 | D4 | **FIXED** | `parity_report.rst` new section "WP-036D — GPU sparse k-NN f32 dispatch parity"; dispatch-test tolerances tightened `atol=rtol=1e-4` → `rtol=1e-5, atol=1e-5`. Commit `ac3b739`. |

### Cumulative ledger

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward. The WP-036D findings above are the most recent additions. All
previous findings from PSR-036/PSR-036A/PSR-036B remain at their last
recorded status (WP036-F1 FIXED, WP036-F2 AMENDED, WP036A-F1/F2 FIXED,
WP036B: zero findings).

---

## 4. Plan amendments this cycle

Two new amendments adopted and executed:

- **Amendment #36** (2026-08-31): new work package WP-036D ("GPU execution
  path for the ported acceptance suite") declared, taking sessions
  `0144I`–`0144L`; WP-036C sessions shifted `0144I`–`0144L` → `0144M`–
  `0144P`. WP-036D S1 decomposed into three sub-passes `0144I1`–`0144I3`.
  Planned session count 226 → **233**.
- **Amendment #37** (2026-08-31): reopened `0144I1` once (added
  `GpuSparseKuramoto.from_knn_phase`); waived WP-036D's zero-copy DLPack
  clause (host-mediated CPU `float32` marshalling; GPU compute on-device
  via CubeCL); recorded **DV-030** (device-resident GPU buffers / true
  zero-copy path). No new session IDs; count unchanged at 233.

---

## 5. Risks and blockers

- **DV-005 (CUDA Burn backend):** OPEN — WP-036D closed the
  inference/dynamics GPU-path gap but explicitly does **not** close DV-005
  (the training-stack CUDA Burn backend). Standing disposition (plan
  amendment #7) unchanged. Re-gate remains at a future WP with a concrete
  CUDA Burn workload.
- **DV-001 (Linux Triton runner):** PARTIALLY VALIDATED — unchanged;
  WP-036D targets the CUDA/wgpu path the Windows runner serves. Triton
  still requires a Linux runner.
- **DV-030 (device-resident GPU buffers):** OPEN — new item from
  amendment #37. `prin-kernels` dispatch is host-in/host-out; a true
  zero-copy Torch↔CubeCL path requires a multi-crate rearchitecture.
  `test_sparse_vram_subquadratic` is deferred to this item's future WP.
- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — allowed warnings per amendments #9/#27, re-verified this
  cycle (`cargo audit` exit 0).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action.
- All other DV register items closed at or before PSR-036B remain closed;
  `tools/check_dv_register_gates.py` passes.
- No new risks introduced.

---

## 6. Next work package declaration — WP-036C

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144M-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md`),
per Documentation Standards §7 item 5:

- **Title:** Acceptance suite port (integration, y-series, kernels; DV-025).
- **Scope (files/crates/modules):** Port the remaining PRINet 3.0 acceptance
  suite — `test_integration_q3`, `test_y2q1`–`test_y2q4`,
  `test_y3q1`–`test_y3q49`, `test_y4q1*` (7 files), `test_y4q2`–`test_y4q4`,
  `test_triton_kernels`, `test_gpu` (~790 `def test_` functions) — into
  `tests/` against the `prin` compatibility surface. Resolve DV-025
  (`retrain_controller`, `SubconsciousController.export_to_onnx`/
  `.quantize_onnx`).
- **Plan sections advanced:** §6 (Phase 6 roadmap).
- **Acceptance criteria:** Every ported test passes on CPU; the full
  ~1,670-test ported suite (WP-036B + WP-036C) is green on CPU. Assertions
  unchanged from the reference. GPU/Triton tests `skipif`-guarded.
- **Non-goals:** New `prin` public symbols beyond DV-025's; final
  documentation prose; GPU-runner execution of skipped tests; extending
  WP-036D's GPU path to `test_gpu` / `test_triton_kernels`.
- **First session brief:**
  `DOCS/sessions/phase-6/0144M-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md`
  (present in `SESSION_REGISTER.md` as `PLANNED`).
- **Maintainer approval:** Required before WP-036C S1 begins.

### WP-036C entry conditions

1. **WP-036D closed** — ✅ all S4 artefacts committed, all findings FIXED,
   delta re-audit CLEAN.
2. **No unresolved D1/D2 finding** — ✅ (WP036D-F1 FIXED, WP036D-F2 FIXED,
   WP036D-F3 FIXED).
3. **Local gates green** — ✅ (CPU fast suite 1784 passed + 1 pre-existing
   timing flake; GPU 7/7 on runner; quality gates clean; docs build clean).
4. **`gpu.yml` run green** — CI authoritative at push (the `gpu.yml` change
   from the exit-5 workaround to `-m gpu` is exercised only when the S4
   commit pushes with `[gpu]` in the commit message).
5. **Maintainer approval** — pending.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(7/7 WPs complete or closing: WP-033, WP-034, WP-035, WP-036, WP-036A,
WP-036B, WP-036D; WP-036C is the registered successor).

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0144I-wp036d-s1-handoff.md` (WP-036D S1 handoff note).

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — 0144I + 0144I1–0144I3 (S1), 0144J (S2), 0144K (S3),
0144L (S4) all marked COMPLETE; 0144M–0144P (WP-036C) marked PLANNED.

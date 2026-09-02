# PRIN Audit Report — Cycle 036E / WP-036E

**Date:** 2026-09-02
**Auditor:** AI pair (Devin)
**Scope:** WP-036E "GPU device-resident execution path" — aggregate S1 range
`0923ea5^..0f94653`: `prin-kernels` device-`Handle` dispatch,
`prin-sim` persistent buffers and CUDA `f64` combine, `prin-py` CUDA DLPack
export, `_torch_compat.py`, tests, and governing artefacts.
**Sessions:** `0144Q` + `0144Q1`–`0144Q3` implementation; `0144R` this audit
**Active brief:** `DOCS/sessions/phase-6/0144R-wp036e-s2-gpu-device-resident-execution-path.md`
**Git state:** `main` @ `0f94653`
**Verdict:** FAIL

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Amendment #43's device-resident envelope is present. The VRAM test remains governed-skipped because the full-coupling denominator is not O(N²), which is the evidence-backed R2 disposition. DV-003's required device-event timing is not delivered (WP036E-F1). |
| Plan/architecture conformance (A2) | ✅ | Host APIs are thin upload → device dispatch → download wrappers; mean-field and band engines retain device state across `step`; sparse CSR remains resident; Python adds no numerics; DV-005/Triton/exponential-integrator boundaries are respected. |
| Tests in tandem + coverage (A3) | ⚠️ | S1 commits include corresponding equivalence, multi-step, CUDA export, parity, and lifetime tests. CUDA coverage reports 84.56% for `prin-kernels` and 94.95% for `prin-sim`; no changed-line report demonstrates the required ≥95% after excluding only DV-004 kernel bodies (WP036E-F3). |
| Numerical parity + invariants (A4) | ✅ | CUDA kernel and Python export tests pass at `rtol=1e-5, atol=1e-6`; no wider tolerance was introduced. Seven ported GPU acceptance tests remain green. |
| Quality gates (A5) | ❌ | Default workspace fmt/clippy pass, but the explicitly required `prin-sim --features cuda --all-targets -D warnings` gate fails on five S1-introduced lints (WP036E-F2). |
| Security (A6) | ✅ | Scoped Snyk Code scans: 0 issues at low threshold; Snyk Open Source: 0 issues; Bandit: 0 findings; `cargo audit`: exit 0 with three governed warnings; both `pip-audit` scans clean. No new unsafe operation kind; second-reviewer sign-off recorded below. |
| Docstring/doc coverage (A7) | ✅ | `interrogate` 97.6%; CUDA workspace rustdoc clean under `-D warnings`. |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub marker or public-API drift. Phase-6 index status and GPU-count evidence are stale/inaccurate (WP036E-F4). |
| CI status (A9) | ❌ | Amendment #28 correctly leaves the range unpushed, but local reproduction is not green because the required CUDA clippy gate fails. |
| Artefact trail (A10) | ⚠️ | S1 handoff and amendment trail exist, but the handoff reports 13 GPU-selected tests where collection and execution select 12 (WP036E-F4). |

The central architecture is sound and the numerical/device-residence tests pass.
The cycle nevertheless fails because CUDA device-event timing—the DV-003 closure
criterion—was not delivered, and the required feature-specific lint gate is red.
No source was changed during this S2 audit.

## 2. Methodology

Environment: Windows 11 self-hosted host `PRIN-GPU-Runner`; NVIDIA GeForce RTX
4060 (8188 MiB), driver 595.95; Python 3.14.0; torch `2.11.0+cu128`;
`torch.cuda.is_available() == True`; one CUDA device.

```powershell
# Range and hygiene
git diff --stat 6343416..HEAD
git diff --name-status 6343416..HEAD
git diff --check 6343416..HEAD
# -> 30 files, 3271 insertions, 327 deletions; diff-check clean

# A5: Rust quality
cargo fmt --all -- --check
# -> clean
cargo clippy --workspace --all-targets -- -D warnings
# -> clean
cargo clippy -p prin-kernels --features cuda --all-targets -- -D warnings
# -> clean
cargo clippy -p prin-sim --features cuda --all-targets -- -D warnings
# -> FAIL: 5 errors (needless_return, 2 large_enum_variant,
#    2 needless_range_loop)

# A3/A4: Rust tests and coverage
cargo test --workspace
cargo test --workspace --features cuda
# -> both pass; CUDA: prin-kernels 126, prin-py 15, prin-sim 193
cargo llvm-cov -p prin-kernels --features cuda --summary-only
# -> total line coverage 84.56%; changed files include buffers.rs 76.29%,
#    discrete_step/cubecl.rs 71.60%, mean_field_rk4/cubecl.rs 71.51%,
#    sparse_knn/cubecl.rs 68.92%
cargo llvm-cov -p prin-sim --features cuda --summary-only
# -> total line coverage 94.95%; gpu.rs 89.84%

# A3/A4: independent GPU and CPU acceptance execution
.venv\Scripts\python -m pytest tests/ -m gpu -rs `
  --basetemp=.pytest_basetemp_audit_gpu
# -> 12 passed, 2963 deselected (7 ported acceptance + 5 WP-036E tests)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" -q `
  -p no:cov --basetemp=.pytest_basetemp
# -> 2743 passed, 202 skipped, 30 deselected
# A first run used a non-governed basetemp name and correctly failed 11 output-
# confinement tests; rerunning with AGENTS.md's exact .pytest_basetemp passed.

# A5/A7: Python quality and documentation
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
# -> All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
# -> 240 files already formatted
.venv\Scripts\mypy python/prin --strict
# -> 62 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
# -> 97.6%, PASS
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps --features cuda
# -> clean

# A2/A8: architectural/public-surface gates
.venv\Scripts\python tools/check_no_python_numerics.py
# -> clean (19 modules)
.venv\Scripts\python -c "import prin; from prin._deprecation import verify_api_surface; print(verify_api_surface(prin.__all__))"
# -> (set(), set())
.venv\Scripts\python tools/wp001_baseline.py check
# -> passed
.venv\Scripts\python tools/check_dv_register_gates.py
# -> passed (33 DV rows, 198 integer-session entries)

# A6: security and dependencies
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
# -> 0 findings
cargo audit
# -> exit 0; governed warnings: bincode RUSTSEC-2025-0141,
#    paste RUSTSEC-2024-0436, chacha20 yanked
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# -> no known vulnerabilities (both)
# Snyk MCP, severity threshold low:
# code scans: crates/prin-kernels, crates/prin-sim, crates/prin-py,
#             python/prin -> 0 issues each
# Open Source: whole repository, all_projects=true, fail_on=all -> 0 issues
```

### Independent DV-003 timing probe

A 262,144-oscillator CUDA mean-field engine was warmed for five steps, then 20
steps were measured with Python `perf_counter` around `engine.step()` and the
returned `StepReport` duration recorded:

```text
backend cuda; timing system; launches 9
median outer wall       0.0028215000 s
median StepReport       0.0026663500 s
median residual         0.0001551500 s
wall / StepReport       1.0581882
```

The residual is bounded and much smaller than the historical ~25 ms vs 388 µs
gap, but this is **not device-event evidence**. The pinned dependency confirms
why: `cubecl-cuda-0.10.0/src/runtime.rs:169-174` registers
`TimingMethod::System`. Consequently `step_cubecl_device` maps CUDA profiling to
`prin_kernels::TimingMethod::System` at
`crates/prin-kernels/src/mean_field_rk4/cubecl.rs:863-877`.

## 3. Detailed findings

### 3.1 A1/A2 — Scope and architecture

Amendment #43 governs the original brief's infeasible bidirectional-zero-copy
language. Against that authority, the delivered architecture conforms:

- `sparse_knn_coupling_cubecl` uploads a `SparseKnnDeviceState`, invokes
  `sparse_knn_coupling_device`, then downloads only through `to_host`
  (`crates/prin-kernels/src/sparse_knn/cubecl.rs:356-364`). The equivalent
  mean-field host wrapper is explicit at
  `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:882-919`; discrete-step
  follows the same pattern.
- `GpuMeanFieldEngine` stores a `ComputeClient`, `MeanFieldDeviceState`, and
  `CubeclBufferPool`; `step()` calls `step_cubecl_device` without host transfer
  (`crates/prin-sim/src/gpu.rs:614-629,781-800`). `GpuBandStepper` analogously
  holds `DiscreteStepDeviceState` (`gpu.rs:882-896,1023-1037`).
- `GpuSparseKuramoto` uploads CSR `indptr`/`indices` once at construction and
  reuses those handles (`gpu.rs:273-307,396-411`). Its generic `Dynamics`
  interface remains intentionally per-call host-in/host-out, while the Python
  CUDA export path avoids output read-back; that split is documented.
- CUDA DLPack export obtains CubeCL's device resource pointer, pins a cloned
  `Handle`, synchronizes before export, and lets Torch adopt a `kDLCUDA`
  capsule (`gpu.rs:223-244,746-769`; `crates/prin-py/src/dlpack.rs:807-858`).
  The Python lifetime test confirms a pre-step export remains a stable snapshot.
- `_torch_compat.py` changed only explanatory docstrings during Q3; its CPU
  branch is unchanged in the aggregate S1 diff. Numerical authority remains in
  Rust and `verify_api_surface` reports no additions.
- No `prin-train`, Triton, or exponential-integrator-kernel implementation was
  added.

`test_sparse_vram_subquadratic` remains at its original `* 0.10` assertion and
is governed-skipped. This is accepted under amendment #43's explicit R2
adjudication: PRIN's full-coupling path allocates no O(N²) CUDA matrix, so
`torch.cuda.max_memory_allocated` cannot provide the intended denominator. A
relaxed ratio would weaken the test without validating its stated property.
DV-030 therefore remains partially closed and must retain its external-memory
API/vendor-shim re-gate.

### 3.2 A3/A4 — Tests, coverage, and parity

The commits pair behavior with tests:

- Q1 includes CPU/wgpu/CUDA device-entry equivalence and host-wrapper tests for
  sparse k-NN, mean-field RK4, and discrete step.
- Q2 includes multi-step residence tests and CUDA on-device-finalize coverage.
- Q3 includes `kDLCUDA` placement, deterministic export, snapshot lifetime,
  sparse CUDA-vs-CPU agreement, and CPU-path regression tests.

All CUDA numerical tests retain the Testing Standards §3 default
`rtol=1e-5, atol=1e-6`; no hazard annotation or Parity Report delta is needed.
The seven previously activated acceptance tests pass independently. The eighth
ported VRAM heuristic is not activated for the architecture reason above.

**WP036E-F3:** the required ≥95% changed-code coverage is not demonstrated. The
handoff delegates coverage to future CI, although amendment #28 prohibits a push
until S4 and the S1/S2 local gate must stand on its own. Fresh CUDA coverage is
84.56% for `prin-kernels` and 94.95% for `prin-sim`; relevant files are lower.
DV-004 permits excluding non-instrumentable `#[cube(launch)]` bodies, not all
uncovered host dispatch, validation, fallback, or export code. S3 must either
supply a changed-line report proving ≥95% after a documented DV-004-only
exclusion or add tests until the threshold is met.

### 3.3 A5/A9 — Quality gate and local CI substitute

Default fmt and workspace clippy pass, but the Q2 contract explicitly inherits
Q1's feature-specific clippy matrix. The CUDA `prin-sim` invocation fails:

- `gpu.rs:145`: `clippy::needless_return`;
- `gpu.rs:615`: `clippy::large_enum_variant` (`MeanFieldInner`, ~1432 vs 72 B);
- `gpu.rs:883`: `clippy::large_enum_variant` (`BandStepperInner`, ~664 vs 72 B);
- `gpu.rs:1374` and `gpu.rs:1600`: `clippy::needless_range_loop`.

`git blame` attributes all five lines to Q2 commit `de500b2`. The Q3 handoff's
statement that they were “pre-existing” means only pre-existing relative to Q3;
it does not make them pre-existing relative to the aggregate WP-036E S1 range.
This is WP036E-F2 and makes A9's local substitute red.

### 3.4 A6 — Security and unsafe second review

No new unsafe operation kind exists. The new capsule construction remains
inside the amendment-#6-audited `crates/prin-py/src/dlpack.rs` module under
`#![deny(unsafe_op_in_unsafe_fn)]`; its block at lines 844-857 has a specific
`// SAFETY:` lifetime justification. `prin-sim` uses safe CubeCL APIs and the
kernel modules retain their existing `ArrayArg::from_raw_parts` pattern.

**Mandatory second-reviewer sign-off:** APPROVED by the 0144R AI auditor for the
new `CudaExternalF32` / `export_dlpack_f32_cuda` surface. The review traced
ownership from `CudaBufferExport.keepalive` through `TensorStorage` to
`dlpack_destructor`, confirmed that a cloned `Handle` pins the allocation, and
confirmed the consumed-capsule name check prevents capsule-side double free.
The GPU lifetime/snapshot tests pass. This sign-off is limited to the
export-direction path authorized by amendment #43; it does not authorize
external CUDA-pointer import.

Scoped Snyk Code scans report zero issues even at low threshold. The whole-repo
scan reports five pre-existing low path-traversal findings in command-line
fixture/baseline tools, none in the functional WP-036E source or in the seven
lines Q0 added to `wp001_baseline.py`; there are zero medium+ findings and no
finding attributable to the device-resident implementation. Snyk Open Source
reports zero issues for the full repository. Native audits are as recorded in
§2.

### 3.5 A7/A8/A10 — Documentation, hygiene, and artefact trail

Rustdoc and interrogate pass. No TODO/FIXME/stub marker, new `prin` public
symbol, secret, or runtime code generation appears in the range. Plan amendment
#43, the three sub-pass briefs, S1 handoff, DV register changes, and commit range
are present and internally traceable.

**WP036E-F4:** two evidence/index inconsistencies remain:

1. The Q3 handoff and brief claim `pytest -m gpu` produced 13 passes, but fresh
   collection selects 12 tests: seven ported acceptance tests and five GPU tests
   in `test_wp036e_q3_zero_copy.py`. The file's sixth test is deliberately a
   default-gate CPU test and is not marked `gpu`.
2. `DOCS/sessions/phase-6/README.md:162-164` still marks Q1/Q2/Q3 `PLANNED`,
   while their briefs and the master register correctly say `COMPLETE`.

These do not change implementation acceptance but make the durable evidence
trail inaccurate.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP036E-F1 | D1 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:669-879`; pinned `cubecl-cuda` runtime `runtime.rs:169-174`; S1 handoff §DV-003 | CUDA `StepReport` records `timing_method=system`, not a device event. The measured residual is bounded (0.155 ms median at N=262,144), and the CUDA f64 combine is on-device, but DV-003's device-event closure criterion is unmet and the handoff contains no claimed full timing figures. | Project Plan §6/amendment #38 DV-003 closure; amendment #43 invariants; `0144Q2` Contract/Exit; `0144R` Expected audit item 6 | S3 either implement genuine CUDA-event timing for the full nine-launch sequence and remeasure device vs outer wall, or obtain a maintainer-approved amendment that records CubeCL 0.10's `TimingMethod::System`, preserves the measured residual, and re-gates actual CUDA-event timing to a concrete dependency/API milestone. Update DV-003 accordingly. |
| WP036E-F2 | D2 | `crates/prin-sim/src/gpu.rs:145,615,883,1374,1600` | Required CUDA feature clippy gate fails on five warnings, all introduced by Q2 commit `de500b2`. | Coding Standards §2.1/§5; Development Workflow §3 S1 local gate; `0144Q2` Gates (“As 0144Q1”) | Fix the five lints without changing behavior; rerun default plus `cpu`/`wgpu`/`cuda` feature clippy matrices. |
| WP036E-F3 | D2 | S1 handoff §§7–8; changed `prin-kernels`/`prin-sim` source | No evidence proves ≥95% changed-code coverage. Fresh CUDA file/total coverage is below 95%; the handoff's future-CI disposition does not satisfy the local S1/S2 gate. | Testing Standards §4/§5; Development Workflow §3 S1 exit; Q1/Q2/Q3 coverage contracts | Produce a changed-line coverage report with only documented DV-004 `#[cube]` exclusions; add tests for uncovered instrumentable changed lines until ≥95%, then rerun coverage. |
| WP036E-F4 | D4 | `DOCS/experiments/0144Q-wp036e-s1-handoff.md:335,371`; Q3 brief lines 135–140; `DOCS/sessions/phase-6/README.md:162-164` | GPU evidence says 13 selected/passed although exactly 12 are GPU-marked; phase index leaves Q1–Q3 `PLANNED`. | Development Workflow and Audit Standards §1.4/§6 artefact accuracy; A8/A10 | Correct the GPU count to 12 (7 acceptance + 5 Q3) and mark Q1–Q3 complete in the phase index. |

## 5. Deviation-ledger delta

New findings to add to the cumulative ledger at WP-036E S4:
`WP036E-F1` (D1), `WP036E-F2` (D2), `WP036E-F3` (D2), and `WP036E-F4`
(D4). No prior finding status changes during this read-only audit.

Deferred-validation adjudication:

- **DV-003:** remains open/partially closed pending WP036E-F1. The on-device
  CUDA `f64` combine is delivered and the host residual is now bounded, but
  genuine CUDA device-event timing is absent.
- **DV-030:** remains `PARTIALLY CLOSED` exactly as amendment #43 specifies.
  Device residence and export-direction zero-copy are delivered; external
  CUDA-pointer input adoption remains re-gated.
- **VRAM heuristic:** retain the governed skip and unmodified `* 0.10`
  assertion. Do not substitute a relaxed ratio for the missing O(N²) full-path
  denominator.

## 6. Verdict and required actions

**FAIL.** WP036E-F1 is a D1 trajectory breach: the work package was assigned
DV-003 closure through device-event timing, but the pinned CUDA runtime and the
actual report use system timing. WP036E-F2 and WP036E-F3 independently violate
normative local-gate and coverage requirements.

Ordered S3 (`0144S`) action list:

1. Resolve WP036E-F1 first: genuine CUDA-event implementation and measurement,
   or an approved amendment with a concrete re-gate; reconcile DV-003.
2. Resolve all five WP036E-F2 CUDA feature lints and rerun every feature matrix.
3. Resolve WP036E-F3 with changed-line evidence and tests to ≥95% for
   instrumentable changed code.
4. Correct WP036E-F4's count and phase-index statuses.
5. Re-run the 12-test GPU selection, full CPU suite, CUDA workspace tests,
   quality/docs/security gates, and the timing probe; append the closure table.

New feature work is frozen until S3 resolves or amends the D1 finding.

**Maintainer acknowledgment of the verdict:** pending — to be recorded before
S3 begins (Development Workflow and Audit Standards §6).

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP036E-F1 | PENDING | — | — |
| WP036E-F2 | PENDING | — | — |
| WP036E-F3 | PENDING | — | — |
| WP036E-F4 | PENDING | — | — |

**Delta re-audit date:** pending — **Result:** findings remain

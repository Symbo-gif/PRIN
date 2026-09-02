# Session 0144Q / WP-036E S1 running handoff

**Date:** 2026-09-02
**Status:** S1-start repository verification COMPLETE; **Plan amendment #43**
recorded (re-scope + decomposition into `0144Q1`–`0144Q3`); governance-doc
updates committed locally. **Sub-passes `0144Q1` (§7), `0144Q2` (handoff in the
`0144Q2` brief), and `0144Q3` (§8) all COMPLETE** — committed locally. The
contiguous `0144Q`+`0144Q1`–`0144Q3` range is ready for the S2 audit `0144R`.
S1 does not self-certify — `0144R` follows all three sub-passes.

---

## 1. Session-start protocol (Development Workflow §6)

Read: latest Project State Report (`036d-project-state.md`); the `0144Q` brief and
the WP-036E/F/G planning doc; Project Plan §6/§8 (amendments
#31/#33/#36/#37/#38); Development Workflow §3/§7; Testing Standards §1/§3;
`DEFERRED_VALIDATION_REGISTER.md` DV-003/DV-030/DV-001/DV-005; the WP-036D S1
handoff (`0144I-wp036d-s1-handoff.md`); the CubeCL kernel modules
(`crates/prin-kernels/src/{mean_field_rk4,sparse_knn,discrete_step}/cubecl.rs`),
`crates/prin-sim/src/gpu.rs`, `crates/prin-py/src/bindings/gpu.rs`.

## 2. S1-start repository verification

### Entry conditions — met

| Condition | Evidence |
|---|---|
| WP-036C S4 (`0144P`) closed and committed | `git log`: `fa427ad` (WP-036C S4) … `6343416`; `0144P` brief + register `COMPLETE` |
| `origin/main` CI green; no unresolved D1/D2 | ETCA-001 remediation `PASS` (SESSION_REGISTER); tree clean, up to date with `origin/main` |
| `PRIN-GPU-Runner` live and CUDA-capable | This workstation. `nvidia-smi`: RTX 4060, driver 595.95, CUDA 13.2. `python -c "import torch"`: `2.11.0+cu128`, `torch.cuda.is_available() == True`, `device_count() == 1`. `cargo build -p prin-kernels --features cuda` → exit 0 (~7 s incremental). |

### Blocking finding — the headline deliverable is not reachable on `cubecl 0.10.0`

The `0144Q` Contract requires *"a true zero-copy Torch↔CubeCL DLPack path … no
host round-trip"* (DV-030's stated closure mechanism). Verified against the
pinned dependency source:

- **`cubecl-cuda` 0.10.0 `GpuStorage`** (`src/compute/storage/gpu.rs`) — the CUDA
  memory backend — allocates every buffer itself via `cudarc malloc_async`/
  `malloc_sync`, tracked in an internal `HashMap<StorageId, …>`. There is **no
  API, public or internal, to adopt an externally-owned CUDA device pointer** as
  a `StorageHandle`/`Handle`.
- **`cubecl-runtime` 0.10.0 `ComputeClient`** (`src/client.rs`) — the entire
  handle-creation surface (`create`, `create_from_slice`, `create_tensor*`,
  `empty*`) consumes **host `Bytes`/`&[u8]`** or allocates uninitialised device
  memory. No `from_device_ptr` / `register_external` / DLPack import.
- Workspace pins `cubecl = "0.10.0"` (`Cargo.toml`), no `[patch]`, no vendored
  fork. No newer `cubecl` in the registry cache.

The only cubecl-0.10 route to a no-host-round-trip **kernel-input** path is a
device-to-device `cuMemcpyDtoD` from torch's DLPack device pointer into a
CubeCL-allocated `Handle` — which needs (a) a new direct `cudarc`/CUDA-driver
dependency in `prin-py`, (b) fresh `unsafe` FFI outside the amendment-#8-audited
kernel modules, and (c) torch↔CubeCL cross-stream synchronization. All three are
barred by the `0144Q` Contract (`unsafe` only in audited modules; no new public
dep-audit surface unbudgeted). This is the **identical architectural wall** that
re-scoped predecessor `0144I2` and produced amendment #37 / DV-030.

### What *is* reachable on cubecl 0.10 (verified)

| Capability | Route |
|---|---|
| **Export**-direction zero-copy DLPack | `ComputeClient::get_resource(handle)` (`client.rs:197`) → CUDA `GpuResource { ptr: u64, size }` exposes a handle's device pointer for a `kDLCUDA` `DLManagedTensor` torch wraps with no copy |
| Persistent device residence across `step` | engines hold `ComputeClient` + `Handle`s; `to_host()` explicit — no cubecl API gap |
| `prin-kernels` device-`Handle` dispatch entry points | the kernels already launch on `ArrayArg::from_raw_parts(handle, n)`; only the host-slice upload/download wrappers need splitting out |
| On-device `f64` RK4 level-2 combine (DV-003) | CUDA supports device `f64`; a CUDA-only `#[cube]` `f64` reduction. wgpu DX12 keeps the documented host `f64` combine (`SHADER_F64` is Vulkan-only) |

### `test_sparse_vram_subquadratic`

Per the `0144I3` evidence, its failure cause is that PRIN's "full" coupling mode
has **no O(N²) GPU kernel** (`_compute_derivatives_gpu` returns `None` for
`coupling_mode != "sparse_knn"` → CPU path), so `vram_full` ≈ 48–96 KB of
allocator/state overhead, not an N×N matrix. A device-resident **sparse** CSR
path shrinks the numerator but cannot move the denominator; the ratio stays
~0.5, not `< 0.10`. Its disposition (governed skip retained with the DV-030
residual / Parity-Report-annotated bound with evidence / new DV item with a
concrete gate) is **adjudicated at S2 (`0144R`)** — Plan risk R2, and the
`0144K`/WP036D-F1 precedent. Never a silently weakened assertion.

## 3. Maintainer decision and amendment #43

Maintainer selected **option A** (2026-09-02 `AskUserQuestion`): re-scope to the
achievable device-resident envelope, decompose `0144Q` into `0144Q1`–`0144Q3`,
re-scope DV-030 to `PARTIALLY CLOSED`. Recorded as **Plan amendment #43**.

Governance-doc changes committed this session:

| File | Change |
|---|---|
| `DOCS/PRIN_Project_Plan.md` | amendment #43 row (§8.3); §6 roadmap Phase 6 row DV-030 wording |
| `DOCS/sessions/SESSION_REGISTER.md` | amendment #43 block; count `253 → 256`; rows `0144Q1`–`0144Q3`; `0144Q` status note; sub-session chain |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | DV-030 → `PARTIALLY CLOSED` + residual re-gate; DV-003 → on-device CUDA `f64` combine at `0144Q2`; disposition-matrix rows |
| `DOCS/sessions/phase-6/WP-036E-S1-execution-plan-and-decomposition.md` | new — decomposition rationale + the verification table above |
| `DOCS/sessions/phase-6/0144Q{1,2,3}-*.md` | new sub-pass briefs |
| `DOCS/sessions/phase-6/0144Q-*.md` | Status/predecessor→`0144Q1`/authority note |
| `DOCS/sessions/phase-6/0144R-*.md` | predecessor → `0144Q3` |
| `DOCS/sessions/{README.md, phase-6/README.md}`, `DOCS/sessions/TRACEABILITY.md` | counts, chains, DV wording |
| `tools/wp001_baseline.py` | `0144Q1`–`0144Q3` in `_SUBSESSION_BLOCKS`; amendment #43 comment |
| `CHANGELOG.md` | `[Unreleased] → Changed` amendment #43 entry |

`tools/wp001_baseline.py check` → **passed**.

## 4. Design notes for the implementation sub-passes

### `0144Q1` — `prin-kernels` device-`Handle` dispatch layer

- `sparse_knn::cubecl` — simplest: `sparse_knn_coupling_cubecl` currently
  `create_from_slice` × (phase/amp/freq/indptr/indices) + `empty` × 3 outputs +
  1 launch + `read_f32s` × 3. Add `sparse_knn_coupling_device<R>(client, in_h:
  &SparseKnnDeviceState<R>, params, out_h: &mut SparseKnnDeviceDerivs<R>)` doing
  only the launch; host wrapper = upload + call + download.
- `mean_field_rk4::cubecl` — already handle-heavy via `CubeclBufferPool` and
  `order_param_device`. Add `step_cubecl_device<R>(client, state: &mut
  MeanFieldDeviceState<R>, params, pool)` running the 8-launch sequence writing
  back into `state` handles, no final `read_f32s`. **Stage 1's order parameter**
  currently comes from the host slice (`super::order_param`); device-resident,
  it must use `order_param_device` like stages 2–4 → `launch_count` goes 8 → 9.
  Document the change (or keep 8 by a documented "stage-1 uses the caller's
  last-known Z" contract — decide in `0144Q1`, note in the handoff).
- `discrete_step::cubecl` — hardest: the whole per-step body is a
  `client.profile(move || { … })` closure that captures the host slices and
  slices them per-band. A device entry point needs per-band input handles
  (three bands) — either a `DiscreteDeviceState<R>` with per-band handle
  triples, or one full-length handle triple plus `Handle::offset` slicing
  (verify cubecl 0.10 `ArrayArg` offset support first).
- Tests: kernel-equivalence for each device entry point vs the CPU reference
  (`rtol=1e-5, atol=1e-6`); the existing `*_cubecl`/`*_auto` tests stay
  unchanged and green (proves the host wrapper is behaviour-equivalent).
- Gate matrix: `--features cuda` / `wgpu` / `cpu` for clippy + test.

### `0144Q2` — `prin-sim` persistent buffers + DV-003

- `GpuSparseKuramoto`/`GpuMeanFieldEngine`/`GpuBandStepper` currently hold
  `Vec<f32>` + derive `Clone, Debug`. Device-resident: hold the `0144Q1` device
  state + a resolved `ComputeClient<R>` (pick backend once at construction via
  `backend::auto_detect_order`). This **breaks `Clone`/`Debug`** and introduces
  a generic `R` or an enum-of-backends — ripples into `prin-py`'s concrete
  `PyGpu*` wrappers. Consider a non-generic `enum GpuBackendClient { Cuda(...),
  Wgpu(...), Cpu(...) }` to keep `prin-py` monomorphic.
- `GpuSparseKuramoto: Dynamics` — `compute_derivatives(&self, …)` stays a
  one-shot host-slice evaluator for the generic-integrator path; the
  device-resident path is a new engine `step` loop. Document the split (the
  `0144Q2` brief already notes this).
- DV-003: CUDA-only `#[cube]` `f64` finalize reducing `block_real`/`block_imag`
  partials on-device; batch the read-backs across the 8-launch sequence; record
  `StepReport` device-event timing over the whole sequence on `PRIN-GPU-Runner`
  and put the device-event-vs-host-wallclock figures in this handoff.

### `0144Q3` — `prin-py` export zero-copy + `_torch_compat.py` + test activation

- `dlpack.rs`: `export_dlpack_f32_cuda(py, device_ptr, shape)` building a
  `kDLCUDA` `DLManagedTensor` (device_type 2) over `get_resource().ptr`; reuse
  the existing audited `unsafe` capsule patterns. `read_dlpack_f32` gains a
  CUDA-capsule branch returning the device pointer for the one-time
  construction upload.
- `bindings/gpu.rs`: `PyGpu*` own the persistent device buffers; `state()` /
  kernel outputs export zero-copy; `.pyi` updated; `#[cfg(all(test, feature =
  "cuda"))]` parity tests.
- `_torch_compat.py`: the `0144I2` GPU branches route through the device path;
  CPU `else` byte-for-byte unchanged; re-assert the golden pre/post CPU test.
- `test_sparse_vram_subquadratic`: per §2 — leave the `0144K` governed skip in
  place with an updated reason pointing at amendment #43's DV-030 residual, and
  let `0144R` adjudicate. Do **not** restore `* 0.10` as a red test.
- Gates: full CPU pytest (`-m "not slow and not gpu"`); `-m gpu` on the runner
  (7 WP-036D tests still green); `cargo test -p prin-py --features cuda`;
  maturin rebuild `--features cuda`; `pip-audit`; Snyk Code (+ Snyk OSS +
  `cargo audit` iff a `Cargo.toml` dep changes).

## 5. Acceptance-criterion → status map (for `0144R`)

| `0144Q` acceptance criterion | Status after this session |
|---|---|
| `test_sparse_vram_subquadratic` passes at `* 0.10` on the runner | **Re-scoped (amdt #43):** architecturally red for a device-resident sparse path; S2 adjudicates disposition |
| 7 WP-036D GPU tests still pass | Not yet re-run (no code change this session) — `0144Q3` gate |
| GPU f32 vs CPU f64 within `rtol=1e-5, atol=1e-6` | `0144Q1`/`0144Q2` kernel-equivalence tests |
| DV-003 host-overhead gap closed or bounded with evidence | `0144Q2` — on-device CUDA `f64` combine + device-event timing |
| CPU marshalling path + 489 CPU tests byte-for-byte unchanged | `0144Q3` golden pre/post |
| Numerical authority in Rust; no new `prin` public symbol; `unsafe` only in audited modules | held by all sub-passes; **the zero-copy-input path that would have needed new `unsafe` is out of scope (amdt #43)** |
| `≥95%` coverage on changed first-party code | per sub-pass; CI authoritative where `coverage.sysmon` segfaults (DV-033) |

## 6. Next step

Sub-pass `0144Q2` — `prin-sim` persistent device buffers + DV-003 on-device
CUDA `f64` combine. `0144Q1` is COMPLETE (§7).

---

## 7. `0144Q1` — `prin-kernels` device-`Handle` dispatch layer (COMPLETE, 2026-09-02)

**Commit:** local only (per amendment #28 cadence — the `0144Q`+`0144Q1`–`0144Q3`
range pushes once before `0144R`). Tree: `crates/prin-kernels/**` only.

### What landed

| Module | New public surface | Host-slice wrapper |
|---|---|---|
| `sparse_knn::cubecl` | `SparseKnnDeviceState<R>` (`upload` / `from_parts`), `SparseKnnDeviceDerivs<R>` (`empty` / `from_parts` / `to_host`), `sparse_knn_coupling_device<R>(client, &state, params, &mut derivs)` | `sparse_knn_coupling_cubecl` = `upload → device → to_host` (byte-identical behaviour; existing `*_cubecl`/`*_auto` tests unchanged and green) |
| `mean_field_rk4::cubecl` | `MeanFieldDeviceState<R>` (`upload` / `from_parts` / `to_host`), `step_cubecl_device<R>(client, &mut state, params, &pool) -> StepReport` (writes the stepped state back into `state`'s handles) | `step_cubecl_with_pool` = `upload → step_cubecl_device → to_host`; `step_cubecl` unchanged (delegates) |
| `discrete_step::cubecl` | `DiscreteStepDeviceState<R>` (`upload` / `from_parts` / `n` / `to_host`) holding **per-band** handle triples, `discrete_step_device<R>(client, &mut state, params) -> StepReport` | `discrete_step_cubecl` = `upload → device → to_host` |
| `buffers` | `CubeclBufferPool` drops `out_phase`/`out_amp`/`out_freq` (device path allocates the 3 finalize outputs per step and moves them into the state), gains a zeroed `k_zero` handle (one upload at pool construction) | — |

`SparseKnnError` gained one variant: `DeviceBufferMismatch { state, derivs }`.

### `launch_count` 8 → **9** for the mean-field RK4 device path (decision)

The device state has no host-resident input slice, so **stage 1 now takes its
order parameter from the same hierarchical `order_param_device` reduction stages
2–4 use** — one extra launch. `StepReport::launch_count` for `step_cubecl_device`
(and therefore the re-expressed `step_cubecl_with_pool` / `step_cubecl` /
`try_step_*`) is **9** = 4 stage kernels + 4 order-parameter reductions + 1
finalize. Documented on `StepReport::launch_count` and the module docs. Three
existing test assertions updated `8 → 9` (`wgpu`/`cpu`/`cuda`
`*_matches_cpu_reference_for_small_n`) — an expectation update to match a
deliberate, documented behaviour change, **not** a weakened assertion (still
exact equality; Testing Standards §5). Stage-1 Z is now a device block-reduction
+ host `f64` combine instead of a host `f64` sum over the full slice — within the
kernel-equivalence tolerance (`rtol=1e-5, atol=1e-6`), so every existing
`assert_allclose` stays green. `discrete_step` `launch_count` stays **10**
(delta's Z was already a device reduction).

### `discrete_step` device state is **per-band**, not one concatenated buffer

First attempt used one `N`-length handle per array + `Handle::offset_start`/
`offset_end` sub-views per band. This **works on the CubeCL CPU and CUDA
backends but wgpu (DX12) rejects it**: `min_storage_buffer_offset_alignment` is
32 bytes, and a non-block-aligned band split (e.g. `[300, 777, 513]`) needs
sub-buffer bindings at byte offsets 1200 / 4308 — `Validation Error … does not
respect … min_storage_buffer_offset_alignment`. It also regressed the existing
`wgpu_matches_cpu_reference_for_non_block_aligned_bands` test. Fix:
`DiscreteStepDeviceState` holds three `[Handle; 3]` per-band triples
(`create_from_slice` per band on upload, exactly what the pre-change closure
did); `to_host` concatenates slow→fast. Every kernel binding stays at buffer
offset 0. Recorded on the struct doc + module docs. **`0144Q2`'s `GpuBandStepper`
should hold the per-band triples too.**

### `offset` slicing verdict for `0144Q2`/`0144Q3`

`Handle::offset_start`/`offset_end` sub-views are **cubecl-0.10-supported on CPU
and CUDA** (used and tested here in the first `discrete_step` attempt) but **not
portable to wgpu** unless every offset is a multiple of 32 bytes (8 `f32`s). Use
per-buffer allocations where band/segment boundaries are arbitrary.

### Gates (all green, local)

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | clean |
| `cargo clippy -p prin-kernels --features cuda \| wgpu \| cpu --all-targets -- -D warnings` | clean (each) |
| `cargo test --workspace` | pass (no cubecl-feature tests here) |
| `cargo test -p prin-kernels --features cpu` | **138 pass** / 0 fail (incl. new `sparse_knn`/`mean_field_rk4`/`discrete_step` device tests) |
| `cargo test -p prin-kernels --features cuda` | **126 pass** / 0 fail (RTX 4060) |
| `cargo test -p prin-kernels --features wgpu` | **145 pass** / 0 fail (incl. the previously-failing non-block-aligned + backend-unavailable tests) |
| `RUSTDOCFLAGS='-D warnings' cargo doc -p prin-kernels --no-deps` | clean (also `--features cuda`/`wgpu`/`cpu`) |
| `cargo audit` | exit 0; 3 allowed warnings (DV-008 `paste`, DV-017 `bincode`, `chacha20` yanked) — no `Cargo.toml` change, no new advisory |
| `snyk code test crates/prin-kernels --severity-threshold=low` | **0 issues** (org `symbo-gif`) |

Coverage on changed non-`#[cube]` lines: CI-authoritative (DV-033 — local
`coverage.sysmon` segfault). New device entry points, `upload`/`to_host`/
`from_parts`, the `DeviceBufferMismatch`/pool-mismatch/non-finite-param error
paths, and multi-step device-resident loops are all exercised by the
cpu/cuda/wgpu test modules.

### Invariants held

No `#[cube]` kernel body changed. No new `unsafe` (the `array_arg` helpers and
their `// SAFETY:` notes are unchanged). No new `prin` public symbol
(`prin-kernels` is Rust; `check_no_python_numerics.py` / `verify_api_surface`
unaffected). CPU reference path untouched. Deterministic — the device paths add
no RNG.

### Carried to `0144Q2` / `0144R`

- `step_cubecl_device` allocates 3 finalize-output handles per step (moved into
  the state). A persistent-engine double-buffer swap is an available
  optimisation if `0144Q2` profiling shows it matters — not required for
  correctness.
- `order_param_device` still does a small host `f64` combine of the per-block
  partials each stage (4 per step now). The **on-device CUDA `f64` combine
  (DV-003)** is `0144Q2` scope.
- `test_sparse_vram_subquadratic` disposition unchanged — `0144R` adjudicates.

---

## 8. `0144Q3` — `prin-py` export zero-copy `kDLCUDA` + `_torch_compat.py` + test disposition (COMPLETE, 2026-09-02)

**Commit:** local only (per amendment #28 cadence — the `0144Q`+`0144Q1`–`0144Q3`
range pushes once before `0144R`). Tree: `crates/prin-sim/src/gpu.rs`,
`crates/prin-py/src/{dlpack.rs,bindings/gpu.rs}`, `python/prin/_torch_compat.py`,
`tests/test_acceptance_q2.py`, new `tests/test_wp036e_q3_zero_copy.py`.

### What landed

| Layer | Change |
|---|---|
| `prin-sim::gpu` (`#[cfg(feature = "cuda")]`) | `CudaBufferExport { ptr: u64, device_id: i32, len, keepalive: Box<dyn Any + Send> }` + `CudaStateExport`; `export_cuda_handle` reads `client.get_resource(handle.clone()).resource().ptr` after `client.sync()`. `GpuMeanFieldEngine::state_cuda_export()` and `GpuSparseKuramoto::compute_derivatives_cuda_export()` return `Some` only on the CUDA device-resident path. The `keepalive` is a **cloned CubeCL `Handle`** — its `Arc` refcount keeps the pool from reusing the slice, so `ptr` stays valid after the engine steps again (snapshot semantics). |
| `prin-py::dlpack` (`#[cfg(feature = "cuda")]`) | `TensorStorage::CudaExternalF32 { ptr, _pin }`; `OwnedDlpackTensor::from_storage_in(shape, storage, ctx)` generalises the CPU-only `from_storage`; `export_dlpack_f32_cuda(py, ptr, device_id, shape, pin)` builds a `kDLCUDA` (`device_type = 2`) `DLManagedTensor` over the device pointer. The existing audited `unsafe` capsule/deleter patterns are reused verbatim — the deleter drops the boxed `Handle`, releasing the pin. No new `unsafe` operation kinds. |
| `prin-py::bindings::gpu` | `PyGpuMeanFieldEngine::state()` and `PyGpuSparseKuramoto::compute_derivatives()` prefer the CUDA export (`export_cuda_state`) and fall back to the CPU-`f32` capsule path on wgpu / CPU-SIMD / no-GPU. `.pyi` signatures unchanged (`-> tuple[object, object, object]`); docstrings updated. `PyGpuBandStepper::state()` **stays CPU-`f32`** — its device state is three per-band `[Handle; 3]` triples (the cubecl-0.10 `min_storage_buffer_offset_alignment` constraint from `0144Q1`), not one contiguous `N`-length buffer. |
| `python/prin/_torch_compat.py` | `_gpu_f32` / `_from_gpu` / `KuramotoOscillator._compute_derivatives_gpu` **docstrings** updated to describe the amendment #43 envelope (one host upload in; zero-copy `kDLCUDA` out). **No code change** — the GPU branch already calls `engine.compute_derivatives(...)` then `_from_gpu(...)`, so the Rust-side switch to `kDLCUDA` output makes the return path zero-copy automatically (a CUDA input now stays on device end to end; a CPU input still lands on CPU via `_from_gpu`'s device restore). CPU `else` path byte-for-byte unchanged. |
| `tests/test_acceptance_q2.py` | `test_sparse_vram_subquadratic` skip **reason** updated to the amendment #43 DV-030 residual (device-resident buffers + export zero-copy delivered; PRIN "full" coupling has no O(N²) GPU kernel so `vram_full` is allocator/state overhead and the ratio stays ~0.5). **Still `@pytest.mark.skip`** — `0144R` adjudicates; `* 0.10` not restored as a red test (Plan risk R2). |

### `kDLCUDA` lifetime / snapshot contract

An exported `state()` / derivative capsule holds a cloned `Handle`. The next
`engine.step()` allocates *fresh* state handles (`0144Q1` finalize outputs are
moved into the state each step), so the pre-step export keeps its values —
verified by `test_mean_field_state_export_is_a_stable_snapshot` (Python) and
`gpu_mean_field_engine_state_cuda_export_is_live_and_snapshot_stable` (Rust).
The producer `client.sync()`s before handing out the pointer, satisfying the
legacy-DLPack producer-synchronised contract Torch expects for a bare
`kDLCUDA` capsule.

### `read_dlpack_f32` — no CUDA branch (amendment #43-consistent)

The `0144Q3` brief floated a `read_dlpack_f32` CUDA-capsule branch "for a
one-time device→device or host upload at engine construction". A true D→D
adopt is the barred path (needs a new `cudarc` dep + fresh `unsafe` outside
the audited modules — amendment #43 §2). The construction-time input therefore
stays a single host `f32` upload — exactly the "one host upload at
construction" the re-scoped envelope permits — and `read_dlpack_f32` is
unchanged. `_gpu_f32` (Torch `.cpu()` marshalling) already provides it.

### Gates (all green, local)

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | clean |
| `cargo clippy --workspace --all-targets -- -D warnings` (CI-authoritative) | clean |
| `cargo test --workspace` | pass |
| `cargo test --workspace --features cuda` (mirrors `gpu.yml`) | pass (incl. 2 new `prin-sim` `#[cfg(feature = "cuda")]` export tests on the RTX 4060) |
| `cargo test -p prin-sim -p prin-py --features cuda` | prin-sim **193** pass, prin-py lib **15** pass |
| `RUSTDOCFLAGS='-D warnings' cargo doc -p prin-sim -p prin-py --no-deps --features cuda` | clean |
| `ruff check python/ tests/ benchmarks/ tools/` / `ruff format --check` | clean |
| `pytest tests/ -m gpu -rs` (on `PRIN-GPU-Runner`) | **12 passed** (7 WP-036D acceptance + 5 `gpu`-marked in `test_wp036e_q3_zero_copy.py`). *Corrected from "13 / +6" per S2 audit `0144R` finding WP036E-F4: the file's sixth test (`test_cpu_compute_derivatives_still_cpu_and_finite`) is a deliberate default-gate CPU regression test and is not `@pytest.mark.gpu`.* |
| `pytest tests/ -m "not slow and not gpu"` | **2743 passed, 202 skipped** (0 failed) — the 489 CPU acceptance tests among them byte-for-byte unchanged; `test_wp036d_gpu_dispatch.py::test_cpu_compute_derivatives_unchanged` golden values intact |
| `cargo audit` | exit 0; 3 allowed warnings (DV-008 `paste`, DV-017 `bincode`, `chacha20` yanked) — no `Cargo.toml` change, no new advisory |
| `snyk code test crates/prin-py` / `crates/prin-sim` / `python/prin` (`--severity-threshold=low`, org `symbo-gif`) | **0 issues** each |
| `pip-audit` | pre-existing `pip`/`setuptools` build-tooling advisories only; **no Python dependency added or changed** by this sub-pass |

`Cargo.toml` / `Cargo.lock` unchanged → no new dependency-audit surface (Snyk
Open Source not triggered).

### Pre-existing latent lint (carried to `0144R`)

`cargo clippy -p prin-sim --features cuda --all-targets -- -D warnings` reports
5 findings (`needless_return` in `try_create_client`; `large_enum_variant` on
`MeanFieldInner`/`BandStepperInner`; two `needless_range_loop` in `0144Q2`
tests). All are **pre-existing** — reproduced identically with this sub-pass's
changes stashed — and this invocation is **not a CI gate** (`rust.yml` clippy
carries no GPU feature; `gpu.yml` runs `cargo test`, not clippy). The
`large_enum_variant` fix would box the hot-path `Device` variant (a `0144Q2`
architecture change). Left for `0144R` to adjudicate; this sub-pass adds no new
clippy findings under any invocation.

### Invariants held

No `#[cube]` kernel changed. No new `unsafe` operation kind — `dlpack.rs`
reuses its audited capsule/deleter pattern; `prin-sim` uses only safe
`cubecl` APIs (`get_resource`, `sync`, `Handle::clone`). No new `prin` public
symbol (`verify_api_surface` stays `(set(), set())` — the `.pyi` gains no
class or function). `check_no_python_numerics.py` unaffected (docstring-only
`_torch_compat.py` edit). CPU marshalling path + the 489 CPU acceptance tests
byte-for-byte unchanged. Deterministic — the export path adds no RNG.

### Acceptance-criterion → status map (for `0144R`)

| `0144Q3` criterion | Status |
|---|---|
| 489 CPU acceptance tests + `_torch_compat.py` CPU path byte-for-byte unchanged | held — docstring-only Python edit; golden `test_cpu_compute_derivatives_unchanged` re-run green in the `-m gpu` leg and the new `test_cpu_compute_derivatives_still_cpu_and_finite` in the default leg |
| 7 WP-036D GPU acceptance tests still pass on the runner | **pass** (`-m gpu` = 12 total; corrected per WP036E-F4) |
| No new `prin` public symbol; `unsafe` only in amendment-#8 modules | held — `.pyi` unchanged; new `unsafe`-adjacent code is in `dlpack.rs` reusing the audited pattern |
| export zero-copy verified on the runner | `kDLCUDA` `state()` / derivative capsules adopted by `torch.from_dlpack` as CUDA tensors; snapshot-stable; values match the CPU reference within `rtol=1e-5, atol=1e-6` |
| `test_sparse_vram_subquadratic` disposition | governed `skip` retained, reason → amendment #43 DV-030 residual; **`0144R` adjudicates** |
| `tests/README.md` GPU count | unchanged — `test_sparse_vram_subquadratic` did not activate; the new `test_wp036e_q3_zero_copy.py` is a WP-internal file (like `test_wp036d_gpu_dispatch.py`), not a ported reference file counted in that table |

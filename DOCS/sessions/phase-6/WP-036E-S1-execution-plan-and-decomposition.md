# WP-036E S1 (`0144Q`) — execution plan and decomposition

**Status:** ADOPTED (2026-09-02, MichaelMaillet — session `0144Q` `AskUserQuestion`
selection) and carried into authority by **Plan amendment #43**. Not an execution
contract; the governing contracts are the sub-pass briefs `0144Q1`–`0144Q3` and
the (re-scoped) parent brief `0144Q`.

---

## 1. Why this document exists

`0144Q` is pre-authorised by amendment #38 to decompose into `0144Q1`–`0144Qn`
under Development Workflow §7. Repository verification at S1 start (below)
confirms one reviewable commit range is exceeded **and** that the brief's
headline deliverable needs re-scoping. Both are recorded by **amendment #43**.

## 2. S1-start repository verification (2026-09-02)

| Check | Finding | Evidence |
|---|---|---|
| Entry: predecessor closed | WP-036C S4 (`0144P`) COMPLETE, pushed; `origin/main` CI green (ETCA-001 remediation). Tree clean. | `git log` `fa427ad`…`6343416`; SESSION_REGISTER ETCA-001 remediation row |
| GPU runner live | `PRIN-GPU-Runner` host = this workstation. RTX 4060, driver 595.95, CUDA 13.2, `torch 2.11.0+cu128`, `torch.cuda.is_available() == True`. `cargo build -p prin-kernels --features cuda` → exit 0 (~7 s incremental). | `nvidia-smi`; `python -c "import torch…"` |
| **Zero-copy Torch→CubeCL kernel input** | **NOT REACHABLE on `cubecl 0.10.0`.** `cubecl-cuda` `GpuStorage` has no API to adopt an external CUDA device pointer as a `Handle`; `ComputeClient::{create,create_from_slice,create_tensor*,empty*}` consume host bytes or allocate uninitialised device memory. Workspace pins `cubecl = "0.10.0"`, no `[patch]`, no vendored fork. | `~/.cargo/registry/.../cubecl-cuda-0.10.0/src/compute/storage/gpu.rs`; `cubecl-runtime-0.10.0/src/client.rs` |
| Export-direction zero-copy | **Reachable.** `ComputeClient::get_resource(handle)` → CUDA `GpuResource { ptr: u64, size }` exposes a handle's device pointer for a `kDLCUDA` DLPack capsule torch wraps with no copy. | `cubecl-runtime-0.10.0/src/client.rs:197`; `storage/gpu.rs` `GpuResource` |
| On-device `f64` RK4 combine (DV-003) | Reachable on **CUDA only** (device `f64` supported); wgpu DX12 keeps the documented host `f64` combine (`SHADER_F64` is Vulkan-only). | `mean_field_rk4/cubecl.rs` module docs |
| `test_sparse_vram_subquadratic @ *0.10` | Architecturally red regardless of a device-resident *sparse* path: PRIN "full" coupling mode has no O(N²) GPU kernel, so `vram_full` ≈ allocator/state overhead, not an N×N matrix. S2 (`0144R`) adjudicates (Plan risk R2). | `DOCS/experiments/0144I-wp036d-s1-handoff.md` §"Tolerance annotation" |

**Consequence:** the `0144Q` Contract clauses *"true zero-copy … no host
round-trip"* and *"`unsafe` only in the already kernel-FFI-audited modules"* are
not simultaneously satisfiable as written. Amendment #43 re-scopes DV-030 to
`PARTIALLY CLOSED` and re-scopes the S1 deliverable to the **device-resident
envelope** (persistent device buffers + device-`Handle` dispatch + on-device
CUDA `f64` combine + export zero-copy + one host upload at construction).

## 3. Decomposition

| Sub-pass | Scope | Crates | Feeds |
|---|---|---|---|
| `0144Q1` | `prin-kernels` device-`Handle`-in/out dispatch entry points for `sparse_knn` / `mean_field_rk4` / `discrete_step` alongside the host-slice ones; host path becomes a thin upload→device→download wrapper (one algorithm, one implementation); feature-gated `cuda`/`wgpu`/`cpu`; kernel-equivalence tests (`rtol=1e-5, atol=1e-6`). | `prin-kernels` | `0144R` |
| `0144Q2` | `prin-sim` `GpuSparseKuramoto`/`GpuMeanFieldEngine`/`GpuBandStepper` hold a `ComputeClient` + persistent device `Handle`s across `step`; `to_host()` the only download; CSR topology device-resident after construction. On-device CUDA `f64` `mean_field_rk4` level-2 combine + batched read-backs + whole-sequence `StepReport` device-event timing (**DV-003**). Tests in tandem; deterministic `Seed` preserved. | `prin-sim`, `prin-kernels` | `0144R` |
| `0144Q3` | `crates/prin-py/src/bindings/gpu.rs` + `dlpack.rs`: export-direction zero-copy DLPack (`get_resource().ptr` → `kDLCUDA` capsule); `PyGpu*` engines own the persistent device buffers; one host upload of initial state at construction; `.pyi` updated; `#[cfg(all(test, feature = "cuda"))]` parity tests. `python/prin/_torch_compat.py` GPU branches route through the device path; CPU `else` byte-for-byte unchanged (golden pre/post). `test_sparse_vram_subquadratic` disposition per §2 (S2 adjudicates). `tests/README.md` GPU count. | `prin-py`, Python | `0144R` |

Each sub-pass commits at its own green local gate. The contiguous
`0144Q`+`0144Q1`–`0144Q3` range feeds the single S2 audit `0144R` (predecessor
becomes `0144Q3`), pushed once per amendment #28 cadence.

## 4. Invariants held across all sub-passes

Numerical authority in Rust (`tools/check_no_python_numerics.py` clean); no new
`prin` public symbol (`verify_api_surface(prin.__all__) == (set(), set())`);
`unsafe` only in the amendment-#8-audited kernel-FFI modules; the CPU
marshalling path and the 489 CPU acceptance tests byte-for-byte unchanged;
deterministic `Seed`; `≥95%` coverage on changed first-party code (CI
authoritative where the local `coverage.sysmon` segfault applies, DV-033).

## 5. Planned-count impact

`253 → 256` (+3). No renumber of `0001`–`0198` or the `0144A`–`0144AB` block
(TRACEABILITY invariant 4 preserved).

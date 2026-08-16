# Session 0069 — WP-018 S1 Handoff Note

**Session:** 0069 — WP-018 S1: Coding — Fused mean-field RK4 kernel
**Date:** 2026-08-15
**Status:** S1 delivered; handoff to S2 audit (session 0070)

## Mission recap

"Productionize fused mean-field RK4 with hierarchical f64-accumulated
reductions and CUDA/wgpu dispatch." Scope (PSR-017 §7): `crates/prin-kernels/src/mean_field_rk4/cubecl.rs`
and supporting modules — hierarchical f64-accumulated device-side
order-parameter reductions, production-grade CUDA/wgpu dispatch, and
device-event timing. Non-goals: sparse k-NN or discrete-band step kernels
(not touched).

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | **Hierarchical device-side order-parameter reduction:** new `order_param_block_reduce` `#[cube(launch)]` kernel (each 256-thread cube block reduces its slice of `amp[i]*e^{i*phase[i]}` into one `(real, imag)` partial via shared memory) and `order_param_device` host helper that finishes the reduction over `ceil(N/256)` partials with an `f64` accumulator. Replaces the pre-WP-018 prototype's `O(N)` full-state host read-back (3 buffers × 3 interior stages) with an `O(N/256)` partial read-back. **Device-event timing:** `step_cubecl_with_pool` now wraps the whole 8-launch sequence in `ComputeClient::profile`; new `TimingMethod` enum (`Device`/`System`) and `StepReport::timing_method` field record whether the reported time is real hardware device timestamps or a host wall-clock fallback — replacing the unconditional wall-clock prototype from WP-004/WP-017 (DV-003). New `MeanFieldRk4Error::ProfilingFailed` variant. 6 new tests (equivalence at non-block-aligned N, multi-block reduction regression, timing-method display). |
| `crates/prin-kernels/src/buffers.rs` | `CubeclBufferPool<R>` gains `block_real`/`block_imag` device handles sized to `num_blocks_for(n) = ceil(n/256).max(1)` (not `n`) and a `num_blocks()` accessor; new `BLOCK_SIZE`/`num_blocks_for` items. 3 new tests. |
| `crates/prin-kernels/src/mean_field_rk4.rs` | `order_param` (the single authoritative CPU/GPU-shared algorithm) now accumulates in `f64` before the final `n_inv` normalization and `f32` downcast (Coding Standards §2.2: "f64 for reference paths and accumulations of reductions"), matching the GPU path's level-2 host accumulator — same algorithm, same output type, higher-precision internal accumulation. New `MeanFieldRk4Error::ProfilingFailed` variant. |
| `crates/prin-kernels/benches/mean_field_rk4_bench.rs` | **New** — criterion N=1M benchmark: `cpu_native` (always) and `wgpu_device_dispatch` (`--features wgpu`), the latter printing one untimed `StepReport` (device-event evidence) before the timed loop. |
| `crates/prin-kernels/Cargo.toml` | Added `[[bench]] mean_field_rk4_bench`. No dependency changes. |

## Acceptance criteria → evidence map

Acceptance criteria from session 0069 brief:

| Criterion | Verdict | Evidence |
|---|---|---|
| **All supported shapes/dtypes match CPU tolerance** | **GREEN** | Kernel-equivalence tests at `rtol=1e-5, atol=1e-6` (Testing Standards §3): wgpu N=64, N=1000 (non-block-aligned — 4 blocks, exercises the partial-last-block mask), N=1,000,000; CubeCL-CPU N=64, N=300 (non-block-aligned — 2 blocks). Only `f32` is a supported dtype for this kernel (unchanged from WP-004/WP-017; no dtype expansion was in scope). |
| **N=1M device-event benchmark meets approved Phase 0 target** | **PARTIAL** | Device-event timing is now real, not a prototype: `StepReport.timing_method` reports `Device` on wgpu (hardware timestamps via `ComputeClient::profile`) and `System` on the CubeCL-CPU/native fallback (`TimestampProfiler`, no hardware timers to read). N=1M evidence on this host (wgpu/DX12): device-event kernel time `388µs` (`StepReport`, untimed single call); criterion wall-clock (10 samples, includes host dispatch/sync overhead for the 8-launch sequence) `24.18–25.51 ms` (`40.06 Melem/s`) vs. CPU-native `115.36–119.80 ms` (`8.49 Melem/s`) — see `mean_field_rk4_bench` output. The Benchmarking Standards §2.4 target itself ("≥ Triton-fused parity") requires a same-hardware PRINet 3.0 Triton comparison, which remains blocked on a Linux/CUDA runner (**DV-001**, unchanged since WP-004; this session does not close it). |
| **No hidden synchronization defects** | **GREEN** | The pre-WP-018 prototype's per-stage host read-back of 3 full `N`-length buffers (order parameter recomputed from a full state copy) is replaced by a 2-level hierarchical reduction that transfers only `ceil(N/256)` partials per stage. `ComputeClient::profile` makes every synchronization point explicit and timed (`StepReport`) rather than implicit. **A genuine CPU-backend data race was found and fixed during this session** (see "Data race" below) — the acceptance criterion's own investigation surfaced exactly the class of defect it names. |

## Data race found and fixed (CubeCL CPU backend)

An early version of `order_param_block_reduce` used a single `sync_cube()`
barrier followed by thread 0 alone finishing the reduction and writing the
block result. Under `--features cpu` at `N=300` (2 cube blocks), this
produced **non-deterministic** wrong results for block 0 across repeated
runs (`-7.33`, `3.48`, `10.53`, ... vs. the correct `14.11`), while block 1
was always correct. Root cause: `cubecl-cpu 0.10.0` schedules cube blocks as
sequential iterations of the same 256 persistent worker threads
(`cubecl-cpu/src/compute/runner.rs`); with no barrier after thread 0's
final write, threads 1..255 (which have no more work after the first
barrier) raced ahead into the *next* block's iteration and began reusing the
same shared-memory buffer while thread 0 was still reading it for the
current block. Fix: a second `sync_cube()` after thread 0's write. Regression
test: `order_param_device_matches_host_per_block_sums_for_multi_block_n`
(5 repeated calls, N=300 forcing `num_blocks=2`).

This is a `cubecl-cpu` runtime characteristic, not a defect in the earlier
9-barrier tree-reduction design it replaced (that design also closed with a
post-combine barrier); the final design uses 2 barriers total (down from a
theoretical 9 for a full binary-tree reduction), which also fixed an
unrelated ~20x `cpu`-feature test slowdown (26s → ~1.3s for one N=64 step)
caused by the CubeCL CPU runtime's per-barrier thread-synchronization cost.

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Clippy (cpu) | `cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings` | PASS |
| Clippy (wgpu,cpu) | `cargo clippy -p prin-kernels --all-targets --features wgpu,cpu -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS |
| Workspace tests (strict) | `cargo test --workspace --features strict-checks` | PASS |
| `prin-kernels` (cpu) | `cargo test -p prin-kernels --features cpu` | PASS — 51 unit + 1 doctest |
| `prin-kernels` (wgpu,cpu) | `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` | PASS — 60 unit + 1 doctest |
| Rustdoc (workspace) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Rustdoc (cpu/wgpu,cpu/cuda) | `cargo doc -p prin-kernels --no-deps --features <cpu|wgpu,cpu|cuda>` | PASS — 0 warnings, all three combinations |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9); no new advisories |
| Snyk Code | `snyk code test crates/prin-kernels/src` and `.../benches` | PASS — 0 issues both |
| Snyk Open Source | Not run | No dependency/manifest changes this session (only a `[[bench]]` target added) |

## Coverage (new/changed code)

`cargo llvm-cov -p prin-kernels --features <cpu|wgpu,cpu>`:

| File | `cpu` lines | `wgpu,cpu` lines |
|---|---|---|
| `buffers.rs` | 100.00% | 100.00% |
| `mean_field_rk4.rs` | 99.56% | 99.78% |
| `equivalence.rs` (untouched) | 95.81% | 95.81% |
| `mean_field_rk4/cubecl.rs` (raw) | 76.73% | 80.76% |

`cubecl.rs`'s raw figure is below 95% for the same reason established at
WP-017 (plan amendment #10 / DV-004): the `#[cube(launch)]` kernel bodies
(`mean_field_rk4_stage`, `order_param_block_reduce`,
`mean_field_rk4_finalize` — 120 of the 143 missed `wgpu,cpu` lines) are not
instrumentable by `cargo-llvm-cov` on stable Rust; their correctness is
verified by the kernel-equivalence tests above, not line coverage.
Excluding those three kernel bodies, the **instrumentable** code is
**96.29%** covered under `--features wgpu,cpu` (620 lines, 23 missed) —
at or above the ≥95% gate. The 23 remaining instrumentable misses are:
multi-line-call closing-paren artifacts of `cargo-llvm-cov`'s per-line
attribution (`500, 538, 576`); the `MeanFieldRk4Error::ProfilingFailed`
construction inside `.map_err` (`637-638`), reachable only if
`ComputeClient::profile` itself fails, which none of the available backends
do in this environment; and `step_auto`'s final native-`step_cpu` fallback
(`731, 739-751`), reachable only when no CubeCL backend initializes at all —
not producible without physically disabling every backend, the same
pre-existing limitation as WP-017's equivalent fallback path.

## Benchmark evidence (N=1,000,000)

`cargo bench -p prin-kernels --bench mean_field_rk4_bench --features wgpu`
on this host (wgpu/DX12 backend; CPU: local dev machine, see workspace CI
environment capture for exact model):

| Path | Measurement | Value |
|---|---|---|
| `cpu_native` (criterion, 10 samples) | wall-clock | 115.36–119.80 ms (8.35–8.67 Melem/s) |
| `wgpu_device_dispatch` (criterion, 10 samples) | wall-clock (includes host dispatch/sync for all 8 launches) | 24.18–25.51 ms (39.21–41.35 Melem/s) |
| `wgpu` single untimed step | `StepReport` device-event time (`timing_method: Device`) | 388 µs |

The ~64x gap between the device-event figure (388 µs, actual GPU kernel
execution) and the criterion wall-clock figure (~25 ms) is host dispatch/sync
overhead across 8 launches and several small `read_one` round-trips per
step, not GPU compute time — a concrete, evidenced optimization target for a
future WP (e.g. batching the 3 reduction read-backs, or moving the final
`f64` combine on-device where a backend supports it). This is reported as
observed evidence, not a scientific conclusion (Testing Standards §2,
Benchmarking Standards §2.2). No scientific/performance conclusion is drawn
from this pilot beyond what is directly measured.

## Parity-evidence disposition

**Directly comparable PRINet 3.0 reference exists and was checked:**
`grep -n "def _reduce_order_param_kernel" "DOCS/archive and reference from
PRINet 3.0/PRINet-3.0.0-main/src/prinet/utils/triton_kernels.py"` — PRINet
3.0's Triton kernel does the same two-level structure (per-block
`tl.sum` partial, then `tl.atomic_add` into a single global scalar,
entirely on-device, `f32` throughout). No new parity case is added or
required this session: the underlying formula (`Z = (1/N) Σ amp·e^{iφ}`)
and the RK4 algorithm are unchanged from WP-007's already-parity-verified
implementation (`crates/prin-dynamics/tests/parity_models.rs`); this WP only
changes *how* the `O(N)` reduction is computed (host-serial →
device-hierarchical, `f64`-finished), which is a PRIN-internal
CPU-vs-GPU kernel-equivalence concern (covered by the tests above), not a
PRINet-3.0-vs-PRIN cross-implementation parity concern. One deliberate,
documented divergence from the PRINet 3.0 reference: PRIN's host-side `f64`
final combine over `ceil(N/256)` partials, vs. PRINet 3.0's device-side `f32`
atomic accumulate — chosen because (a) `f64` accumulation of reductions is
a Coding Standards §2.2 requirement PRINet 3.0's Triton kernel does not
itself satisfy, and (b) this project's local wgpu (DX12) backend has no
portable device-side `f64` (`SHADER_F64` is Vulkan-only and optional).

## Architecture decisions

1. **Two-level hierarchical reduction, not a full on-device tree.** Level 1
   (device): one `f32` partial sum pair per 256-thread cube block. Level 2
   (host): `f64` accumulation over the (small, `O(N/256)`) partials. A
   fully on-device design (matching PRINet 3.0's Triton `atomic_add`) was
   considered and rejected for this session: cross-platform device `f64` is
   not portably available (see Parity-evidence disposition), and an
   `f32` atomic accumulate would reproduce the exact precision concern
   Coding Standards §2.2 requires `f64` accumulation to avoid. The current
   design keeps the transfer volume improvement (`O(N)` → `O(N/256)`) while
   using real `f64` hardware for the numerically sensitive step. Moving the
   level-2 combine fully on-device (double-single/compensated `f32`
   emulation, or backend-conditional native `f64` where `SHADER_F64`/CUDA
   is available) is a candidate for a future WP.
2. **Single-thread-finishes-reduction over a binary tree, in-kernel.** An
   initial 8-level halving tree (9 `sync_cube()` barriers total) was
   replaced with "every thread writes once, one barrier, thread 0 sums all
   256 values serially, second barrier" after both a ~20x `cpu`-feature
   test slowdown and (independently) the multi-block data race documented
   above. 256 sequential scalar adds is negligible work on real GPU
   hardware; the parallelism that matters at this level is the `N → N/256`
   gather, not the final in-block combine.
3. **`TimingMethod` as a small local enum, not re-exporting `cubecl`'s.**
   `StepReport::timing_method` uses a two-variant local type rather than
   `cubecl_common::profile::TimingMethod` to avoid coupling this crate's
   public API to an external crate's type across a semver boundary; the
   conversion is a single equality check in `step_cubecl_with_pool`.

## Out-of-scope discoveries

- The pre-existing `step_auto` native-CPU-fallback branch (unreachable in
  any environment with a working CubeCL backend) has the same
  hard-to-cover characteristic as `mean_field_rk4::cubecl`'s other
  backend-unavailable paths; no action taken (pre-existing, not introduced
  by this session).
- A fully on-device (no host round-trip at all) order-parameter reduction,
  matching PRINet 3.0's Triton `atomic_add` design exactly, is possible on
  backends with native device `f64` (CUDA) or via `f32` compensated
  summation (portable). Not attempted this session (see Architecture
  decision 1); candidate for a future WP.
- `DV-001` (Triton same-hardware comparison) and `DV-005` (CUDA DLPack/
  compute validation) remain open, blocked on a Linux/CUDA runner; this
  session's CUDA dispatch path (`try_step_cuda`) is unchanged from WP-017
  and untested on this host, consistent with prior cycles.

# Session 0144Q3 — WP-036E S1 (sub-pass 3/3): `prin-py` export zero-copy DLPack, `_torch_compat.py` device path, test activation

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S1 — Coding
**Predecessor:** [0144Q2 — Coding (sub-pass 2/3)](0144Q2-wp036e-s1-prin-sim-persistent-device-buffers-dv003.md)
**Successor:** [0144R — Audit (WP-036E S2)](0144R-wp036e-s2-gpu-device-resident-execution-path.md)
**Authority:** Project Plan §6/§8, amendments #38/#43, and
[`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md).
The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Expose the `0144Q2` device-resident engines to Python with an **export-direction
zero-copy DLPack path**, upgrade the `_torch_compat.py` GPU dispatch branches to
route through the device path, and dispose of `test_sparse_vram_subquadratic`.

## Scope

- `crates/prin-py/src/dlpack.rs`: device-pointer variants of
  `read_dlpack_f32` / `export_dlpack_f32` — `export_dlpack_f32_cuda(ptr, shape)`
  builds a `kDLCUDA` `DLManagedTensor` over a CubeCL `Handle`'s device pointer
  (`ComputeClient::get_resource(...).ptr`) that torch wraps with no copy;
  `read_dlpack_f32` gains a CUDA-capsule branch that returns the device pointer
  for a one-time device→device or host upload at engine construction.
  `#[cfg(feature = "cuda")]`.
- `crates/prin-py/src/bindings/gpu.rs`: `PyGpuSparseKuramoto` /
  `PyGpuMeanFieldEngine` / `PyGpuBandStepper` own the persistent device
  buffers; construction does one host upload of the initial state; `state()` /
  kernel outputs are exported zero-copy as `kDLCUDA` capsules. `.pyi` updated.
  `#[cfg(all(test, feature = "cuda"))]` parity tests.
- `python/prin/_torch_compat.py`: the `0144I2` GPU dispatch branches route
  through the zero-copy device path; the CPU `else` branch is byte-for-byte
  unchanged; the golden-value pre/post CPU test is re-asserted.
- `test_acceptance_q2.py::test_sparse_vram_subquadratic`: disposition per
  amendment #43 §2(c) — governed skip retained with the DV-030 residual, **or**
  a Parity-Report-annotated bound with evidence, **or** a new DV item with a
  concrete gate. **S2 (`0144R`) adjudicates**; never a silently weakened
  assertion. `tests/README.md` GPU count updated only if the test activates.

## Contract

- The 489 CPU acceptance tests and the `_torch_compat.py` CPU path
  byte-for-byte unchanged (golden pre/post).
- The 7 GPU acceptance tests activated by WP-036D still pass on the runner.
- No new `prin` public symbol (`verify_api_surface` stays `(set(), set())`);
  `check_no_python_numerics.py` clean; `unsafe` only in the amendment-#8
  audited modules (the DLPack helpers reuse the existing audited `f64`
  patterns).
- `ruff` / `ruff format --check` / `mypy --strict` / `interrogate` / `bandit`
  clean; `≥95%` coverage on changed first-party code (CI authoritative per
  DV-033).

## Gates

Full CPU pytest suite (`-m "not slow and not gpu"`); `-m gpu` on the runner;
`cargo test -p prin-py --features cuda`; maturin rebuild `--features cuda` into
`.venv`; `pip-audit`; Snyk Code + (if `Cargo.toml` deps change) Snyk Open
Source + `cargo audit`.

## Non-goals

Bidirectional zero-copy kernel input (DV-030 residual, re-gated by amendment
#43); a wgpu device-`f64` path; `prin-train` / autodiff (DV-005); Triton
(DV-001); the exponential-integrator kernel; final documentation prose; the S2
audit.

## Exit

All gates green; export zero-copy verified on the runner; CPU suite
byte-for-byte unchanged; every acceptance criterion evidence-mapped in
`DOCS/experiments/0144Q-wp036e-s1-handoff.md`. Commit at the green local gate;
the `0144Q`+`0144Q1`–`0144Q3` range is ready for the S2 audit `0144R`.

---

## S1 Handoff (2026-09-02)

**Status:** COMPLETE — all gates green (full evidence in
`DOCS/experiments/0144Q-wp036e-s1-handoff.md` §8).

### Deliverables

1. **Export-direction zero-copy `kDLCUDA` DLPack:**
   - `prin-py::dlpack::export_dlpack_f32_cuda` builds a `kDLCUDA`
     (`device_type = 2`) `DLManagedTensor` over a CUDA device pointer, reusing
     the amendment-#8-audited capsule / deleter `unsafe` pattern (no new
     `unsafe` operation kind). `TensorStorage` gains a feature-gated
     `CudaExternalF32 { ptr, _pin }` variant; `from_storage_in` generalises the
     device context.
   - `prin-sim::gpu` (feature `cuda`) exposes `CudaBufferExport` /
     `CudaStateExport` via `GpuMeanFieldEngine::state_cuda_export()` and
     `GpuSparseKuramoto::compute_derivatives_cuda_export()`. The pointer comes
     from `ComputeClient::get_resource(handle.clone()).resource().ptr` after
     `client.sync()`; the capsule keep-alive is a **cloned CubeCL `Handle`**
     whose refcount pins the allocation (stable snapshot across the next
     `step()`).

2. **`PyGpu*` engines:** `PyGpuMeanFieldEngine::state()` and
   `PyGpuSparseKuramoto::compute_derivatives()` return zero-copy `kDLCUDA`
   capsules on the CUDA device-resident path, CPU `float32` capsules
   otherwise. `.pyi` signatures unchanged (no new `prin` public symbol);
   docstrings updated. `PyGpuBandStepper::state()` stays CPU `float32` —
   per-band `[Handle; 3]` device state is not one contiguous buffer
   (cubecl-0.10 offset-alignment constraint, `0144Q1`).

3. **`python/prin/_torch_compat.py`:** `_gpu_f32` / `_from_gpu` /
   `_compute_derivatives_gpu` docstrings updated for the amendment #43
   envelope (one host upload in, zero-copy `kDLCUDA` out). No code change —
   the existing GPU branch's return path becomes zero-copy automatically.
   CPU `else` path byte-for-byte unchanged; golden pre/post CPU test green.

4. **`read_dlpack_f32`:** no CUDA branch added — a true device→device adopt is
   the amendment-#43-barred path; construction-time input stays a single host
   `f32` upload (the permitted "one host upload at construction"). Recorded in
   the handoff.

5. **`test_sparse_vram_subquadratic`:** governed `@pytest.mark.skip` retained;
   reason updated to the amendment #43 DV-030 residual. **`0144R` adjudicates**
   the final disposition; `* 0.10` not restored as a red test (Plan risk R2).
   `tests/README.md` GPU count unchanged (the test did not activate).

6. **Tests:** 2 new `prin-sim` `#[cfg(feature = "cuda")]` export tests; new
   `tests/test_wp036e_q3_zero_copy.py` (6 tests — 5 `@pytest.mark.gpu` CUDA
   export/snapshot/parity + 1 default-gate CPU-path regression).

### Gates verified

`cargo fmt` / `clippy --workspace --all-targets` (CI-authoritative) /
`cargo test --workspace` / `cargo test --workspace --features cuda`
(mirrors `gpu.yml`, on the RTX 4060) / `cargo doc --features cuda` /
`ruff` + `ruff format --check` / `pytest -m gpu` (**12 passed** — 7 WP-036D +
5 `gpu`-marked in `test_wp036e_q3_zero_copy.py`; its 6th test is a default-gate
CPU regression test, not `gpu`-marked — corrected per S2 audit `0144R` finding
WP036E-F4) / `cargo audit` (exit 0, 3 allowed warnings, no `Cargo.toml` change) /
`snyk code test` on `prin-py` + `prin-sim` + `python/prin` (**0 issues**) /
`pip-audit` (pre-existing build-tooling advisories only; no Python dep
changed). Full CPU gate (`pytest -m "not slow and not gpu"`): **2743 passed,
202 skipped, 0 failed**.

### Handoff to `0144R` (S2 audit)

The contiguous `0144Q`+`0144Q1`–`0144Q3` range is complete and committed
locally. `0144R` adjudicates: the `test_sparse_vram_subquadratic` disposition
(Plan risk R2); the pre-existing `clippy -p prin-sim --features cuda
--all-targets` findings (5, all reproduced with this sub-pass stashed, not a
CI gate); and DV-003 full device-event-vs-wall-clock timing evidence
(`0144Q2` handoff).

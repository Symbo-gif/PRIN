# Session 0144Q3 — WP-036E S1 (sub-pass 3/3): `prin-py` export zero-copy DLPack, `_torch_compat.py` device path, test activation

**Status:** PLANNED
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

# Session 0144I / WP-036D S1 running handoff

**Date:** 2026-08-31 (sub-passes 0144I1 + 0144I2 complete)
**Status:** Sub-passes 0144I1 (incl. the amendment #37 reopen) and 0144I2
**COMPLETE** (committed locally at green gates; not pushed). Sub-pass 0144I3
remains. S1 does not self-certify — `0144J` (S2 audit) is next after all three
sub-passes.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report, the 0144I brief and its decomposition
(`WP-036D-S1-execution-plan-and-decomposition.md`), the 0144I1 sub-pass
brief, Project Plan §6/§8 (amendments #31/#33/#36), Development Workflow and
Audit Standards §3/§7, Testing Standards §1.1/§3, the audit
`036b-wp036b-audit.md` §8, and the WP-025 DLPack bridge precedent.

**Session ID/type:** 0144I — WP-036D S1 (Coding), sub-pass 0144I1.
**Planned output (0144I1):** PyO3 GPU binding layer over `prin-sim`'s GPU
engines, DLPack f32 helpers, `.pyi` updates, feature-gated tests, maturin
rebuild.

---

## Sub-pass 0144I1 — PyO3 GPU binding layer

### Deliverables

| # | Deliverable | Files | Status |
|---|---|---|---|
| 1 | Feature forwarding (`cuda`/`wgpu` → `prin-sim`) | `crates/prin-py/Cargo.toml` | ✅ |
| 2 | `read_dlpack_f32` / `export_dlpack_f32` helpers | `crates/prin-py/src/dlpack.rs` (new fns only) | ✅ |
| 3 | GPU binding module: `PyGpuSparseKuramoto`, `PyGpuMeanFieldEngine`, `PyGpuBandStepper` | `crates/prin-py/src/bindings/gpu.rs` (new file) | ✅ |
| 4 | Module wiring (feature-gated) | `crates/prin-py/src/bindings/mod.rs`, `crates/prin-py/src/lib.rs` | ✅ |
| 5 | `.pyi` stubs for all 3 GPU types | `python/prin/_prin_core.pyi` | ✅ |
| 6 | Feature-gated integration tests (4 tests) | `crates/prin-py/src/bindings/gpu.rs` `#[cfg(all(test, any(feature = "cuda", feature = "wgpu")))]` | ✅ |

### Design decisions

1. **DLPack f32 helpers are feature-gated** (`#[cfg(any(feature = "cuda", feature = "wgpu"))]`)
   to avoid dead-code warnings when building without GPU features. They are
   only consumed by the GPU binding module, which is itself feature-gated.

2. **`GpuSparseKuramoto` constructor takes CSR topology as flat lists**
   (`crow_indices`, `col_indices`, `values`) matching `SparseCoupling::from_csr`
   convention, plus scalar model parameters. This avoids exposing the
   `SparseCoupling` type to Python while preserving the exact topology the
   GPU kernel needs.

3. **`GpuMeanFieldEngine` and `GpuBandStepper` constructors take initial
   state as f32 DLPack tensors** plus scalar parameters. `step()` returns a
   dict with backend timing metadata. `state()` returns three f32 DLPack
   capsules `(phase, amplitude, frequency)`.

4. **`GpuBandStepper` constructor uses `#[allow(clippy::too_many_arguments)]`**
   since the 12 parameters (3 state tensors + band_sizes + 3×3 per-band
   params + 2×2 PAC params + amp_min/max + dt) are inherent to the fused
   three-band discrete-step API.

5. **No new `unsafe` blocks** in the binding module. The f32 DLPack helpers
   in `dlpack.rs` reuse the existing audited `unsafe` patterns (same SAFETY
   justifications as the `f64` counterparts).

6. **Numerical authority stays in Rust.** The binding is marshalling and
   dispatch only — no Python numerics. `check_no_python_numerics.py` stays
   clean.

### Quality gates

| Gate | Command | Result |
|---|---|---|
| `cargo fmt` | `cargo fmt --all -- --check` | ✅ clean |
| `clippy` (default) | `cargo clippy -p prin-py -- -D warnings` | ✅ clean |
| `clippy` (wgpu) | `cargo clippy -p prin-py --features wgpu -- -D warnings` | ✅ clean |
| GPU tests (wgpu) | `cargo test -p prin-py --features wgpu -- bindings::gpu::tests` | ✅ 4/4 pass |
| Workspace tests | `cargo test --workspace` | ✅ all pass |
| `ruff check` | `.venv\Scripts\ruff check python/prin/` | ✅ clean |
| `ruff format` | `.venv\Scripts\ruff format --check python/prin/_prin_core.pyi` | ✅ clean |
| `mypy --strict` | `.venv\Scripts\mypy python/prin/_prin_core.pyi --strict` | ✅ clean |
| CPU Python suite | `pytest tests/ -m "not slow and not gpu"` | ✅ 1724 pass / 9 skip |

### Pre-existing issue (not caused by this sub-pass)

`test_wp001_baseline::test_current_baseline_automation_is_green` fails with
"session 0144E: brief/register status mismatch" — a pre-existing register
status issue from the WP-036C renumber (amendment #36). Unrelated to 0144I1.

### Test evidence

```
running 4 tests
test bindings::gpu::tests::gpu_band_stepper_binding_step_and_state_f32 ... ok
test bindings::gpu::tests::gpu_mean_field_engine_binding_step_and_state_f32 ... ok
test bindings::gpu::tests::gpu_sparse_kuramoto_binding_agrees_with_cpu_reference ... ok
test bindings::gpu::tests::gpu_sparse_kuramoto_binding_compute_derivatives_f32_round_trip ... ok

test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 10 filtered out
```

### Non-goals confirmed (not touched)

- No `_torch_compat.py` changes (→ 0144I2)
- No test marker/`gpu.yml` changes (→ 0144I3)
- No `prin-train` / autodiff changes
- No new `prin` public symbols
- No edits to existing `dlpack.rs` functions
- No Triton changes
- No scope creep

### Next step

Sub-pass `0144I2` — Python device dispatch + DLPack marshalling in
`_torch_compat.py`.

---

## Sub-pass 0144I1 reopen — plan amendment #37 (2026-08-31)

`0144I2` execution surfaced that `0144I1`'s `GpuSparseKuramoto` binding needs
caller-supplied CSR topology, which the `_torch_compat.py` sparse k-NN path
can only build with Python numerics (Coding Standards §1.2). Per plan
amendment #37, `0144I1` was reopened for exactly one addition and re-closed.

| # | Deliverable | Files | Status |
|---|---|---|---|
| 1 | `GpuSparseKuramoto.from_knn_phase(n, k_neighbors, coupling_strength, decay_rate, freq_adaptation_rate, phase)` — builds the k-NN CSR topology in Rust via `SparseCoupling::from_knn` (a `f32` DLPack phase in; no Python-side coupling construction) | `crates/prin-py/src/bindings/gpu.rs` (`build_gpu_sparse_from_knn_phase` + `#[staticmethod]`) | ✅ |
| 2 | `.pyi` stub | `python/prin/_prin_core.pyi` | ✅ |
| 3 | Feature-gated Rust parity test (`from_knn_phase` vs `KuramotoOscillator` `SparseKnn` reference, `< 1e-4` abs — the `prin-sim` gpu-module precedent) | `crates/prin-py/src/bindings/gpu.rs` tests mod | ✅ |
| 4 | Pre-existing `map_clone` / `iter().copied().collect()` clippy nits in the `0144I1` feature-gated test code fixed (surfaced by `--all-targets` + `--features cuda`) | same file | ✅ |
| 5 | maturin rebuild `--features cuda` into `.venv` | — | ✅ |

**Gates:** `cargo fmt --all --check` clean; `cargo clippy --workspace --all-targets -- -D warnings` clean (also `-p prin-py --features cuda --all-targets`); `cargo test --workspace` all pass; `cargo test -p prin-py -p prin-sim --features cuda` all pass (the 5 `bindings::gpu` tests incl. the new one run the CubeCL **CUDA** kernel on the RTX 4060). Snyk Code on `gpu.rs` → 0 issues. No `Cargo.toml` change → no dependency audit triggered.

## Sub-pass 0144I2 — Python device dispatch + DLPack marshalling

### Deliverables

| # | Deliverable | Files | Status |
|---|---|---|---|
| 1 | `_is_gpu(tensor)` device-dispatch predicate | `python/prin/_torch_compat.py` | ✅ |
| 2 | `_gpu_f32(tensor)` / `_from_gpu(capsule, like)` `float32` DLPack marshalling helpers (amendment #37: CPU-`float32` boundary; compute on GPU via CubeCL) | same | ✅ |
| 3 | GPU dispatch branch in `OscillatorModel.compute_derivatives` → `KuramotoOscillator._compute_derivatives_gpu` (sparse k-NN → `GpuSparseKuramoto.from_knn_phase` → CubeCL sparse k-NN kernel; batched over rows; non-differentiable, matching the reference GPU tests). CPU `else` path unchanged. | same | ✅ |
| 4 | Device-preservation docstring notes for `_HierarchicalNetwork.step` / `DeltaThetaGammaNetwork`, `ExponentialIntegrator.step`, `gradient_checkpoint_integration`, `phase_to_rate` (CUDA inputs already carried on-device by `_tensor` / `_from_raw_rows`; fused-GPU kernels deferred) | same | ✅ |
| 5 | Unit tests: predicate; CPU-path golden-value pre/post identity (kur full/sparse, Stuart-Landau, Hopf, batched); marshalling round-trip; GPU sparse k-NN dispatch agrees with CPU reference (`atol=1e-4`); batched dispatch; `None` fallbacks (full coupling, `n<=1`, no binding); CUDA-guarded device assertion | `tests/test_wp036d_gpu_dispatch.py` (15 tests) | ✅ |

### Contract mapping (amendment #37 re-scope)

| 0144I2 brief clause | Outcome |
|---|---|
| `_is_gpu` predicate + per-class dispatch branches | ✅ predicate; ✅ real GPU branch for the sparse k-NN `compute_derivatives` path; other named classes are device-correct via existing marshalling, fused-GPU kernels **deferred** (amendment #37) |
| GPU branch: DLPack, run CubeCL kernel, **no host round-trip**, return GPU tensor directly | **waived by amendment #37** — CPU `float32` DLPack boundary (kernel layer is host-in/host-out); compute runs on GPU; `_from_gpu` returns the result on the caller's device. True zero-copy → **DV-030**. |
| CPU branch is the existing code verbatim; dedicated pre/post identity test | ✅ `if _is_gpu(state.phase)` guard only; `_is_gpu` is `False` for CPU → existing code path unchanged. `test_cpu_compute_derivatives_unchanged[*]` (golden values captured pre-change). |
| No Python numerics; `check_no_python_numerics.py` clean; `prin.__all__` / `FROZEN_PUBLIC_API` unchanged | ✅ `check_no_python_numerics.py` exit 0 (19 modules) + its 4 tests pass; no new public symbol; `_torch_compat.py` is a listed Rust-bridge module (no `@` matmul added). Topology built in Rust via `from_knn_phase`. |

### Gates

| Gate | Command | Result |
|---|---|---|
| `ruff check` | `ruff check python/ tests/ benchmarks/ tools/` | ✅ clean |
| `ruff format` | `ruff format --check python/prin/_torch_compat.py tests/test_wp036d_gpu_dispatch.py` | ✅ clean |
| `mypy --strict` | `mypy python/prin --strict` | ✅ 55 files, no issues (also the new test file) |
| `interrogate` | `interrogate -c pyproject.toml python/prin` | ✅ 97.4% (min 95) |
| `bandit` | `bandit -r python/prin -c pyproject.toml` | ✅ exit 0 (only the pre-existing Low B110 in `hybrid_compat.py`, `# noqa`) |
| no-python-numerics | `tools/check_no_python_numerics.py` + its 4 tests | ✅ exit 0 / 4 pass |
| CPU acceptance subset | `pytest tests/test_acceptance_*.py -m "not slow and not gpu"` (targeted 4 GPU-relevant files shown: 175 pass / 8 skip) | ✅ unchanged |
| Full CPU suite | `pytest tests/ -m "not slow and not gpu"` | 1778 pass / 11 skip / **3 pre-existing fail** (all `test_wp001_baseline.py`, confirmed identical on `git stash` = clean `c011f69`; two were `0144E`/`0144I1` brief↔register status drift, **reconciled by this sub-pass's housekeeping** — see below) |
| GPU dispatch (real kernel) | `test_gpu_sparse_knn_dispatch_hook_agrees_with_cpu_reference` | ✅ CubeCL sparse k-NN kernel; `max|Δ| ≈ 5e-7` vs f64 CPU reference |
| Rust `--features cuda` | `cargo test -p prin-py -p prin-sim --features cuda` | ✅ all pass (5 `bindings::gpu`) |
| Snyk Code | `snyk code test python/prin/`; `snyk code test .../bindings/gpu.rs` | ✅ 0 issues each |
| coverage ≥95% changed lines | pytest-cov / `coverage` | **BLOCKED** on this host (`coverage.sysmon` access-violation on Py 3.14 + torch import — the pre-recorded `wp036-coverage-tooling-blocked` condition). Manual review: every new function and both branches of the CPU/GPU guard are exercised except the `if _is_gpu(...) → gpu is not None → return` join and the CUDA device-assertion, which require CUDA-torch (deferred to `0144I3` runner). CI is authoritative. |

### Housekeeping (picked up because amendment #37 touches the register)

`tools/wp001_baseline.py::validate_session_plan` reported two **pre-existing**
`brief/register status mismatch` entries — `0144E` (parent brief left `PLANNED`
after its `0144E1`–`0144E6` decomposition closed; flagged in this handoff's
0144I1 section as "pre-existing … unrelated to 0144I1") and `0144I1` (brief
`COMPLETE`, register `PLANNED` after the 0144I1 commit). Both reconciled to
`COMPLETE`; `test_wp001_baseline.py` now green.

### Out-of-scope discoveries (for the `0144J` audit)

1. **The audit-036b §8 root-cause is half-right.** "GPU tensors are silently
   copied to CPU, computed, copied back … tests asserting `device.type ==
   'cuda'` would fail" — the *compute-location* half is correct, but
   `_tensor(value, like)` / `OscillatorState._from_raw_rows` already restore the
   caller's CUDA device on every result. So `test_gpu_forward`,
   `test_gpu_parity` (×2), `test_sparse_on_gpu`, `test_gpu_exponential_integrator`,
   `test_checkpoint_gpu_memory_budget`, `test_checkpoint_vram_stays_bounded`
   assert conditions the **pre-`0144I2`** code already satisfies once CUDA is
   present. Only `test_sparse_vram_subquadratic` genuinely fails (needs
   device-resident buffers — **DV-030**). The substantive `0144I2` gain is that
   `test_sparse_on_gpu`'s derivative now runs on the CubeCL GPU kernel rather
   than the CPU f64 path.
2. **No exponential-integrator CubeCL kernel exists** in `prin-kernels`
   (kernels: `mean_field_rk4`, `discrete_step`, `pac`, `sparse_knn`, `ops`).
   `ExponentialIntegrator.step` has no fused-GPU path regardless of DV-030.
3. **`test_acceptance_phase_to_rate.py::test_gpu_parity`** exercises the
   `prin.nn.autoencoders.PhaseToRateConverter` `nn.Module` directly, not
   `_torch_compat.phase_to_rate` — a GPU path for it is outside this brief's
   `_torch_compat.py` scope.
4. **torch is `2.13.0+cpu`** on the dev host and PyTorch ships no CUDA wheel for
   `2.13.0` (their CUDA index tops out at `2.11.0+cu128`). `torch.cuda.is_available()`
   is `False` here, so the 8 acceptance GPU tests and this sub-pass's CUDA-guarded
   unit test skip locally; the CubeCL CUDA kernels themselves **do** run on this
   host's RTX 4060 (via `cargo test --features cuda` and CubeCL's own backend
   selection inside the Python dispatch). Making `torch.cuda` available is a
   repo-wide dependency decision, out of scope for this sub-pass (maintainer
   directed keeping `2.13.0+cpu`).

### Next step

Sub-pass `0144I3` — `@pytest.mark.gpu` on the 8 tests (+ their `skipif`
guard), marker registration, `gpu.yml` `-m gpu`, GPU-runner kernel-equivalence
evidence (incl. the sparse k-NN dispatch and the `test_sparse_vram_subquadratic`
/ DV-030 disposition), full CPU suite re-run, S1 handoff close.

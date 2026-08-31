# WP-036D S1 (session 0144I) — execution plan and decomposition

**Status:** ADOPTED (2026-08-31, MichaelMaillet). Recorded as **Plan
amendment #36**. Maintainer selected the amendment-#33 disposition: a new
work package **WP-036D** ("GPU execution path for the ported acceptance
suite"), declared as WP-036's sibling in the same alphabetic-suffix family as
WP-036A/B/C, takes sessions `0144I`–`0144L`; the existing WP-036C sessions
shift `0144I`–`0144L` → `0144M`–`0144P` to make room. WP-036D S1 (session
`0144I`) is executed as **three sequential coding sub-passes** `0144I1`–
`0144I3`, all feeding the single S2 audit `0144J`. Not itself an execution
contract; the governing contracts are the `0144I` brief, amendment #36, and
the three sub-pass briefs `0144I1`–`0144I3`.

**Prepared for:** session 0144I (WP-036D S1 — GPU execution path for the
ported acceptance suite).
**Author:** AI pair.
**Date:** 2026-08-31.
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36; Development
Workflow and Audit Standards §7; Testing Standards §1.1, §3.

---

## 1. Why this document exists

The WP-036B S2 audit (`DOCS/audits/036b-wp036b-audit.md`) closed PASS with
zero findings, but its maintainer-requested §8 addendum ("GPU skip assessment
and remediation roadmap") establishes a concrete, bounded gap:

- **8 of the 9 acceptance-suite skips are CUDA-availability guards** on tests
  that exercise a real GPU execution path in the reference (`test_gpu_parity`,
  `test_gpu_forward`, `test_sparse_on_gpu`, `test_sparse_vram_subquadratic`,
  `test_gpu_exponential_integrator`, `test_checkpoint_gpu_memory_budget`,
  `test_checkpoint_vram_stays_bounded`, and the `phase_to_rate` GPU parity
  case). The guards match the reference files exactly and are **not** a port
  deviation — but they are permanently red on any CPU host because
  `python/prin/_torch_compat.py` has no GPU path at all: every compatibility
  function marshals to CPU float64 via `_numpy()`, calls the Rust CPU
  binding, and restores the caller's device. GPU tensors are silently
  copied to CPU, computed, and copied back.
- **The Rust GPU kernel layer already exists and is CI-tested.**
  `prin-kernels` ships CubeCL CUDA + wgpu kernels for mean-field RK4, sparse
  k-NN coupling, PAC, and discrete step; `prin-sim` exposes
  `GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper` behind the
  `cuda` / `wgpu` features; `gpu.yml` runs them on the self-hosted
  `PRIN-GPU-Runner` (Windows, CUDA, registered — DV-002 CLOSED).
- **The only gap is the PyO3 exposure and the Python-side device dispatch.**

Amendment #33 established the pattern exactly: an audit-surfaced roadmap gap
that is out of scope for the test-porting WPs (WP-036B/C non-goal: "New
`prin` public symbols"; "adapt imports only") and that must land in its own
S1–S4 cycle with its own Audit Report and Project State Report. WP-036D is
that cycle. It executes and closes **before** WP-036C (session `0144M`) so
that the 8 GPU tests are green — not skipped — for the remainder of Phase 6,
and so WP-036C's own `test_gpu.py` port can reuse the dispatch surface
rather than re-derive one.

## 2. Relationship to existing deferred items

- **DV-005 ("CUDA DLPack full validation" / CUDA Burn backend)** is a
  *training*-stack item: a CUDA Burn autodiff backend for `prin-train`, plus
  the `<5%` boundary-overhead target. WP-036D does **not** touch `prin-train`
  or autodiff and does not close DV-005; it addresses the *inference /
  dynamics* GPU path only. WP-036D S4 records the boundary explicitly so the
  two are not conflated.
- **DV-001 (Linux GPU runner for Triton)** is unaffected. WP-036D targets the
  CubeCL CUDA/wgpu path that the existing Windows runner already serves;
  `test_triton_kernels` stays `skipif`-guarded and remains DV-001's problem.

## 3. Adopted strategic disposition

1. **No new public `prin` symbol.** The 8 tests assert on the *existing*
   public classes (`DeltaThetaGammaNetwork`, `PhaseToRateConverter`, the q2
   sparse-coupling and `ExponentialIntegrator` paths, gradient-checkpoint
   helpers). WP-036D adds a GPU execution path *inside* those existing
   surfaces — a device-dispatch branch in `_torch_compat.py` — not a new
   name. `prin.__all__` and `FROZEN_PUBLIC_API` are unchanged;
   `verify_api_surface` stays `(set(), set())`.
2. **Numerical authority stays in Rust.** The GPU path calls the already-
   audited CubeCL kernels via new thin PyO3 bindings over `prin-sim`'s GPU
   engine types. No Python numerics; `tools/check_no_python_numerics.py`
   stays clean.
3. **Zero-copy GPU↔GPU.** The GPU path marshals via DLPack (not `_numpy()`),
   so a CUDA input tensor never round-trips through host memory.
4. **CPU path is untouched.** The 489 passing acceptance tests and every
   other CPU consumer keep the exact `_numpy()` → Rust CPU → `_tensor()`
   path. The dispatch branch is `if tensor.is_cuda: gpu else: cpu`; the
   `else` is the current code verbatim. No regression surface for CPU.
5. **Kernel equivalence is the parity contract.** GPU f32 kernel vs CPU f64
   reference within Testing Standards §3 GPU tolerances (`rtol=1e-5`,
   `atol=1e-6`); any wider tolerance is a per-test annotation + Parity
   Report entry under the amendment #14/#16/#17/#25 mechanism, never an
   assertion edit.
6. **One audit range.** Each sub-pass commits at its own green local gate.
   The contiguous `0144I`+`0144I1`–`0144I3` range feeds the single S2 audit
   `0144J`; push cadence is amendment #28 (the S4 push carries the batched
   range).
7. **Skips that legitimately remain stay `skipif`-guarded** — on a CPU-only
   dev host the 8 tests still skip; the marker (`@pytest.mark.gpu`) is what
   makes the self-hosted runner *select* them, and the guard is what makes a
   CPU host *skip* them. Both are kept.

## 4. Adopted decomposition

| Sub-pass | Focus | Deliverables |
|---|---|---|
| `0144I1` | **PyO3 GPU binding layer** (Phase A of the audit roadmap) | New `gpu` module under `crates/prin-py/src/bindings/` behind `#[cfg(feature = "cuda")]` / `#[cfg(feature = "wgpu")]`, wrapping `prin-sim`'s `GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper` (and the exponential-integrator GPU step); device-aware constructors; GPU step/forward methods that accept and return DLPack GPU tensors (zero-copy); `_prin_core.pyi` additions; `#[cfg(all(test, feature = "cuda"))]` / `wgpu` PyO3 integration tests; maturin rebuild. |
| `0144I2` | **Python device dispatch + DLPack marshalling** (Phase B) | `_is_gpu(tensor)` helper and per-class device-dispatch branches in `python/prin/_torch_compat.py` (`DeltaThetaGammaNetwork`, `PhaseToRateConverter`, the q2 sparse-coupling derivative path, `ExponentialIntegrator`, and the gradient-checkpoint frequency/VRAM-budget helpers); DLPack GPU marshalling helper (mirrors the WP-025 `read_dlpack_f64` pattern, f32 GPU variant); CPU path byte-for-byte unchanged; unit tests for the dispatch predicate and the CPU-path no-op; `check_no_python_numerics.py` stays clean. |
| `0144I3` | **Test activation, CI, and consolidation** (Phase C) | Add `@pytest.mark.gpu` to the 8 CUDA-guarded acceptance tests (marker *and* the existing `skipif` guard — the marker enables runner selection, the guard handles hardware absence); register the `gpu` marker in `pyproject.toml`; update `.github/workflows/gpu.yml` to run `pytest tests/ -v -m gpu` (replacing the documented "0 tests exist" exit-5 workaround); GPU-vs-CPU kernel-equivalence evidence at §3 tolerances; full ported acceptance suite re-run on CPU (still 489 pass / the 8 now marker-selected but skipped on CPU host); S1 handoff note mapping each of the 8 tests to its now-green GPU-runner evidence and each acceptance criterion to evidence. |

Every pass runs the relevant subset and all tests for any changed first-party
code, keeps changed code at ≥95% line coverage, and runs the applicable
Rust/Python quality and security gates. Snyk Code is required for modified
supported first-party source; dependency scans run only if manifests change.
This governance-only amendment does not itself execute those coding gates.

## 5. Amendment #36 recording

Amendment #36 adds one new WP (WP-036D) and seven new planned session
identifiers (`0144I`, `0144I1`–`0144I3`, `0144J`, `0144K`, `0144L` — of which
`0144I`–`0144L` are reused from the shifted WP-036C block) and renumbers the
four WP-036C briefs `0144I`–`0144L` → `0144M`–`0144P`. It does **not**
renumber the 0001–0198 integer sequence or touch 0145–0198 (TRACEABILITY
invariant 4 preserved). The link chain becomes:

`0144H` → `0144I` → `0144I1` → `0144I2` → `0144I3` → `0144J` → `0144K` →
`0144L` → `0144M` → `0144N` → `0144O` → `0144P` → `0145`.

Planned session count: **226 → 233** (+3 new sub-passes `0144I1`–`0144I3`, +4
renumber targets `0144M`–`0144P`; the `0144I`–`0144L` identifiers are reused
from the shifted WP-036C block). `0144J` audits the aggregate
`0144I`+`0144I1`–`0144I3` range and independently re-runs the GPU
kernel-equivalence suite plus the 8 activated tests on the self-hosted runner.

## 6. Risks and controls

- **R1 — GPU dispatch regresses the CPU path.** Control: the `else` branch is
  the current code unchanged; a dedicated test asserts the CPU path is
  byte-identical pre/post; the full 489-test CPU suite is a per-sub-pass gate.
- **R2 — GPU binding introduces Python numerics.** Control: bindings are thin
  marshalling over `prin-sim` GPU engines; `check_no_python_numerics.py` is a
  per-sub-pass gate; S2 inspects ownership.
- **R3 — f32 GPU kernel vs f64 CPU reference fails a byte-for-byte
  assertion.** Control: governed by the amendment #14/#16/#17/#25 tolerance
  mechanism — per-test annotation + Parity Report entry, never an assertion
  edit; the reference's own GPU tests already use `atol=1e-4`/`1e-5`.
- **R4 — the self-hosted runner is offline at audit time.** Control: `0144J`
  records runner state live (as WP-030 S4 did for DV-024); if offline, the
  8 tests' GPU evidence is the sub-pass `0144I3` run captured in the handoff,
  and S2 notes the CI re-confirmation as pending the next `gpu.yml` run.
- **R5 — scope creep into DV-005 (CUDA Burn training backend).** Control:
  §2 boundary is explicit and is a stated non-goal in every WP-036D brief;
  auditors treat any `prin-train`/autodiff change as D3 scope creep.

## 7. Next step

Execute `0144I1` (PyO3 GPU binding layer). Keep numerical authority in Rust,
marshal GPU tensors zero-copy via DLPack, leave the CPU path untouched,
append evidence to `DOCS/experiments/0144I-wp036d-s1-handoff.md`, and commit
locally only when the sub-pass gate is green.

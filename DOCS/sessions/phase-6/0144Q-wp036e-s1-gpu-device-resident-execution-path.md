# Session 0144Q — WP-036E S1: Coding — GPU device-resident execution path

**Status:** PLANNED — **decomposed into `0144Q1`–`0144Q3` and the headline
deliverable re-scoped by Plan amendment #43** (2026-09-02). S1-start repository
verification established that a *true zero-copy Torch↔CubeCL DLPack kernel-input
path* is not reachable on the pinned `cubecl 0.10.0` (no external-CUDA-pointer
`Handle` API); DV-030 is re-scoped to `PARTIALLY CLOSED` and the S1 deliverable
to the device-resident envelope (persistent device buffers + device-`Handle`
dispatch + on-device CUDA `f64` combine + **export**-direction zero-copy + one
host upload at engine construction). See
[`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md).
The Mission/Contract text below is retained verbatim for rationale; where it
says "true zero-copy … no host round-trip" read amendment #43's re-scope.
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S1 — Coding
**Predecessor:** [0144P — Documentation (WP-036C S4)](0144P-wp036c-s4-acceptance-suite-port-integration-y-series-kernels.md)
**Successor:** [0144Q1 — Coding (sub-pass 1/3)](0144Q1-wp036e-s1-prin-kernels-device-handle-dispatch-layer.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36/#37/#38/#43, and [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md) + [`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md). If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **New work package (Plan amendment #38).** `0144I2` / amendment #37
> established that no layer of the GPU stack holds device-resident state:
> `prin-kernels`' CubeCL dispatch functions take `&[f32]` host slices and
> return `Vec<f32>` host; `prin-sim`'s GPU engines store state as host
> `Vec<f32>`. Consequences: `test_acceptance_q2.py::test_sparse_vram_subquadratic`
> cannot pass (the coupling matrix is invisible to `torch.cuda`), and the
> mean-field RK4 level-2 `f64` combine runs host-side so host dispatch/sync
> overhead dominates the wall-clock figure (DV-003). WP-036E closes DV-030 and
> DV-003 in its own S1–S4 cycle, executing before WP-036F/WP-036G and WP-037.

## Mission

Make the GPU execution path device-resident end to end: `prin-kernels`
dispatch entry points that accept and return CubeCL device handles, `prin-sim`
GPU engines that hold persistent device buffers across `step` calls, an
on-device `f64` level-2 combine for `mean_field_rk4`, a true zero-copy
Torch↔CubeCL DLPack path in `crates/prin-py/src/bindings/gpu.rs`, and the
`python/prin/_torch_compat.py` GPU dispatch branches upgraded from
`0144I2`'s host-mediated CPU-float32 marshalling to the device path — with the
CPU path byte-for-byte unchanged. Activate
`test_acceptance_q2.py::test_sparse_vram_subquadratic` (assertion restored to
`vram_full * 0.10`, reverting `0144K`'s DV-030 `skip`).

## Contract

- **Acceptance:**
  - `test_sparse_vram_subquadratic` passes on the self-hosted
    `PRIN-GPU-Runner` (CUDA) with its assertion at `vram_full * 0.10` and its
    reference `skipif(not torch.cuda.is_available())` guard intact; it is the
    8th `@pytest.mark.gpu` acceptance test. `tests/README.md` GPU count 7 → 8.
  - The 7 GPU acceptance tests activated by WP-036D still pass on the runner.
  - GPU (f32 kernel) vs CPU (f64 reference) agreement is within Testing
    Standards §3 GPU tolerances (`rtol=1e-5`, `atol=1e-6`); any wider
    tolerance is a per-test annotation + Parity Report entry under the
    amendment #14/#16/#17/#25 mechanism, never an assertion edit.
  - Device-event timing for the fused mean-field RK4 8-launch sequence is
    recorded on `PRIN-GPU-Runner`; the DV-003 host dispatch/sync-overhead gap
    is closed, or bounded with evidence and a stated residual.
  - The CPU marshalling path in `_torch_compat.py` and the 489 CPU acceptance
    tests are byte-for-byte unchanged (golden-value pre/post test, as
    `0144I2` established).
  - Numerical authority stays in Rust (`tools/check_no_python_numerics.py`
    clean); no new `prin` public symbol
    (`verify_api_surface(prin.__all__) == (set(), set())`); `unsafe` only in
    the already kernel-FFI-audited modules under the amendment #8 pattern
    (`// SAFETY:` on every block, second-reviewer sign-off in S2).
  - `≥95%` coverage on new/changed first-party code; CPU coverage
    non-decreasing.
- **Non-goals:** A CUDA Burn autodiff backend for `prin-train` or any `<5%`
  boundary-overhead work (DV-005 — closed as `AMENDED` by amendment #38, out
  of scope); a `prin-kernels` exponential-integrator CubeCL kernel (none
  exists — the `ExponentialIntegrator` GPU test stays on the device-restoring
  marshalling path `0144I2` gave it); Triton (DV-001); `test_gpu.py` /
  `test_triton_kernels.py` changes (WP-036C already owns their port); any
  `prin.__all__` / `FROZEN_PUBLIC_API` change; final documentation prose;
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36/#37/#38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3/§7
- `DOCS/standards/Coding_Standards.md` §1 (one algorithm one implementation),
  §2.1/§6.1 (audited `unsafe` FFI pattern)
- `DOCS/standards/Testing_Standards.md` §1, §3 (GPU tolerances)
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-003, DV-030 (and DV-001,
  DV-005 for the boundary)
- `DOCS/reports/036d-project-state.md`; the cumulative deviation ledger
- `DOCS/audits/036d-wp036d-audit.md` and `DOCS/experiments/0144I-wp036d-s1-handoff.md`
- `crates/prin-kernels/src/{mean_field_rk4,sparse_knn,discrete_step}/cubecl.rs`;
  `crates/prin-sim/src/gpu*` (`GpuSparseKuramoto`/`GpuMeanFieldEngine`/`GpuBandStepper`);
  `crates/prin-py/src/bindings/gpu.rs` and `dlpack.rs`;
  `python/prin/_torch_compat.py`; `.github/workflows/gpu.yml`
- [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md) §3 (WP-036E scope), §7 (risks R1/R2)

## Entry conditions

- WP-036C S4 (`0144P`) is closed and committed; the full ~1,670-test ported
  acceptance suite is green on CPU and `test_gpu.py` is ported.
- No unresolved D1/D2 finding exists.
- WP-036E scope, acceptance criteria, and non-goals have maintainer approval
  (Plan amendment #38; PSR-036C §6 hand-off).
- The self-hosted `PRIN-GPU-Runner` is registered and CUDA-capable; its live
  state is confirmed at S1 start and recorded in the handoff note.

## Expected work

1. **`prin-kernels` device-handle dispatch layer.** Add `Handle`/device-buffer
   entry points alongside the existing host-slice functions; the host-slice
   path becomes a thin `upload → device path → download` wrapper (one
   algorithm, one implementation). Feature-gated (`cuda`/`wgpu`).
2. **`prin-sim` persistent device buffers.** `GpuSparseKuramoto` /
   `GpuMeanFieldEngine` / `GpuBandStepper` hold CubeCL device buffers across
   `step`; state stays on-device between steps; an explicit `to_host()` is the
   only download. CSR topology stays device-resident after
   `from_knn_phase`/construction.
3. **DV-003 on-device combine.** Move the `mean_field_rk4` level-2 `f64`
   combine on-device; batch result read-backs across the 8-launch sequence;
   record `StepReport` device-event timing over the whole sequence.
4. **`prin-py` zero-copy DLPack.** `crates/prin-py/src/bindings/gpu.rs`: a CUDA
   torch tensor → CubeCL device handle → kernel → CUDA torch tensor with no
   host round-trip; device-pointer variants of the `0144I1`
   `read_dlpack_f32`/`export_dlpack_f32` helpers; `.pyi` updated;
   `#[cfg(all(test, feature = "cuda"))]` parity tests.
5. **`_torch_compat.py` upgrade.** The GPU dispatch branches from `0144I2`
   route through the zero-copy device path; the CPU `else` branch is
   untouched; the golden-value pre/post CPU test is re-asserted.
6. **Test activation.** `test_sparse_vram_subquadratic` gains
   `@pytest.mark.gpu` alongside its `skipif`; the `0144K` `@pytest.mark.skip`
   and its DV-030 reason are removed; the assertion returns to `* 0.10`.
7. Tests in tandem with every behavior; deterministic `Seed` preserved;
   record every tolerance annotation and every out-of-scope discovery.

**S1 decomposition (pre-authorised, Plan amendment #38 / Development Workflow
§7).** If repository verification at S1 start shows the four-layer change
exceeds one reviewable commit range, decompose into sequential coding
sub-passes `0144Q1`–`0144Qn` (candidate: `prin-kernels` layer; `prin-sim`
buffers + DV-003 combine; `prin-py`/Python zero-copy + test activation), each
committing at its own green local gate and all feeding the single S2 audit
`0144R`; record the split via a follow-on amendment and update the register.

## Required evidence and outputs

- Code and tests in one S1 commit range (`0144Q` + any `0144Q1`–`0144Qn`);
  `≥95%` coverage on changed first-party code.
- `cargo fmt` / clippy `-D warnings` / `cargo test --workspace` /
  `cargo test -p prin-kernels -p prin-sim -p prin-py --features cuda` (and
  `--features wgpu` where applicable) / `cargo doc`; `ruff` / `ruff format
  --check` / `mypy --strict` / `interrogate` / `bandit` / `pytest` (CPU
  subset) / `cargo audit` / `pip-audit`; Snyk Code on modified supported
  source.
- GPU-vs-CPU kernel-equivalence evidence and device-event timings from
  `PRIN-GPU-Runner`; runner state recorded.
- Parity Report delta for any GPU-vs-CPU tolerance annotation.
- `DOCS/experiments/0144Q-wp036e-s1-handoff.md` mapping each acceptance
  criterion (incl. all 8 GPU tests) to evidence.

## Prohibited

- CPU-path regression; Python numerics; new public symbols; `prin-train` /
  autodiff changes (DV-005); weakened or deleted assertions; a silently
  loosened `test_sparse_vram_subquadratic` bound (if `< 10%` is not reached,
  S2 adjudicates a Parity-Report-annotated bound with evidence or a *new* DV
  item with a concrete gate — the `0144K`/WP036D-F1 precedent); undocumented
  tolerance drift; hidden RNG; unapproved `unsafe`; scope creep into DV-005 /
  Triton / the exponential-integrator kernel; unregistered experimentation.

## Exit gate

All S1 gates green; the 8 GPU acceptance tests pass on the runner and still
skip on a CPU host; the CPU suite is byte-for-byte unchanged; DV-003's
host-overhead gap is closed or bounded with evidence; every acceptance
criterion is evidence-mapped. Hand off to the mandatory S2 audit `0144R`.

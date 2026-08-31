# Session 0144I — WP-036D S1: Coding — GPU execution path for the ported acceptance suite

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S1 — Coding
**Predecessor:** [0144H — Documentation (WP-036B S4)](0144H-wp036b-s4-acceptance-suite-port-core-dynamics-model-stack.md)
**Successor:** [0144I1 — PyO3 GPU binding layer](0144I1-wp036d-s1-pyo3-gpu-binding-layer.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36, and [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md). If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **New work package (Plan amendment #36).** The WP-036B S2 audit
> (`DOCS/audits/036b-wp036b-audit.md` §8) established that 8 of the 9
> acceptance-suite skips are CUDA guards on tests with a real reference GPU
> path, red on every CPU host because `python/prin/_torch_compat.py` has no
> GPU execution path. The Rust CubeCL kernels (`prin-kernels`), the
> `prin-sim` GPU engines, and the self-hosted `PRIN-GPU-Runner` all already
> exist; only the PyO3 exposure and Python device dispatch are missing.
> WP-036D closes that gap in its own S1–S4 cycle, executing before the
> renumbered WP-036C (`0144M`–`0144P`). Decomposition into `0144I1`–`0144I3`
> is Plan amendment #36; see
> [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md).

## Mission

Give `python/prin/_torch_compat.py` a real GPU execution path so the 8
CUDA-guarded acceptance tests in the WP-036B ported files pass on the
self-hosted GPU runner instead of being permanently skipped — via new thin
PyO3 bindings over `prin-sim`'s GPU engine types, zero-copy DLPack GPU
marshalling, and a device-dispatch branch inside the existing public
compatibility surfaces. Delivered across the three sequential sub-passes
`0144I1`–`0144I3`.

The 8 tests (audit §8.1): `test_gpu_parity` and `test_gpu_forward`
(`test_acceptance_hierarchical.py`), `test_gpu_parity`
(`test_acceptance_phase_to_rate.py`), `test_sparse_on_gpu` and
`test_sparse_vram_subquadratic` (`test_acceptance_q2.py`),
`test_gpu_exponential_integrator`, `test_checkpoint_gpu_memory_budget`, and
`test_checkpoint_vram_stays_bounded` (`test_acceptance_q2_remaining.py`).

## Contract

- **Acceptance:** All 8 GPU-guarded acceptance tests pass on the self-hosted
  `PRIN-GPU-Runner` (CUDA) with `@pytest.mark.gpu` selecting them; each
  keeps its reference `skipif(not torch.cuda.is_available())` guard so a
  CPU-only host still skips it. The 489 CPU acceptance tests and every other
  CPU consumer are byte-for-byte unaffected (the dispatch `else` branch is
  the current code). GPU f32 kernel results agree with the CPU f64 reference
  within Testing Standards §3 GPU tolerances (`rtol=1e-5`, `atol=1e-6`); any
  wider tolerance is a per-test annotation + Parity Report entry under the
  amendment #14/#16/#17/#25 mechanism, never an assertion edit. Numerical
  authority stays in Rust; `tools/check_no_python_numerics.py` stays clean.
  `gpu.yml` runs `pytest tests/ -m gpu`.
- **Non-goals:** A CUDA Burn autodiff backend for `prin-train` or any
  `<5%` boundary-overhead work (DV-005 — training stack, explicitly out of
  scope); `test_gpu.py` / `test_triton_kernels.py` activation (WP-036C /
  DV-001); any new `prin` public symbol or change to `prin.__all__` /
  `FROZEN_PUBLIC_API`; Triton; final documentation prose; release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3/§7
- `DOCS/standards/Testing_Standards.md` §1, §3 (GPU tolerances)
- `DOCS/audits/036b-wp036b-audit.md` §8 (GPU skip assessment and roadmap)
- `DOCS/reports/036b-project-state.md` and the cumulative deviation ledger
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-001, DV-002, DV-005
- `crates/prin-kernels/` GPU kernels; `crates/prin-sim/` `gpu` module;
  `crates/prin-py/src/bindings/` (esp. the WP-025 `dlpack.rs` helpers);
  `.github/workflows/gpu.yml`; `python/prin/_torch_compat.py`
- [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md)

## Entry conditions

- WP-036B S4 (0144H) is closed and committed.
- No unresolved D1/D2 finding exists.
- WP-036D scope, acceptance criteria, and non-goals have maintainer approval
  (Plan amendment #36).
- The self-hosted `PRIN-GPU-Runner` is registered and CUDA-capable (DV-002
  CLOSED); its live state is confirmed at S1 start and recorded.

## Expected work

1. `0144I1` — PyO3 GPU binding layer over `prin-sim`'s GPU engines, DLPack
   GPU in/out, `.pyi` updates, `#[cfg(all(test, feature = "cuda"))]` PyO3
   tests, maturin rebuild.
2. `0144I2` — `_is_gpu` predicate + per-class device-dispatch branches in
   `_torch_compat.py`; DLPack f32 GPU marshalling helper; CPU path unchanged;
   dispatch/CPU-no-op unit tests.
3. `0144I3` — `@pytest.mark.gpu` on the 8 tests (marker + guard), marker
   registration, `gpu.yml` update, GPU-vs-CPU kernel-equivalence evidence,
   full CPU suite re-run, S1 handoff note.
4. Keep numerical authority in Rust; no Python numerics; deterministic `Seed`.
5. Record every tolerance annotation and every out-of-scope discovery.

## Required evidence and outputs

- Binding, dispatch, and test-activation commits in one S1 range
  (`0144I`+`0144I1`–`0144I3`).
- ≥95% coverage on changed first-party code; CPU coverage non-decreasing.
- `ruff` / `ruff format --check` / `mypy --strict` / `pytest` (CPU subset) /
  `bandit` / dependency audits; `cargo fmt` / clippy / `cargo test` and
  `cargo test --features cuda,wgpu` for the new bindings; Snyk Code on
  modified supported source.
- Parity Report delta for any GPU-vs-CPU tolerance annotation.
- `DOCS/experiments/0144I-wp036d-s1-handoff.md` mapping each of the 8 tests
  and each acceptance criterion to evidence, and recording runner state.

## Prohibited

- CPU-path regression, Python numerics, new public symbols, `prin-train` /
  autodiff changes, weakened or deleted assertions, undocumented tolerance
  drift, hidden RNG, unapproved `unsafe`, scope creep into WP-036C /
  DV-005 / Triton, or unregistered experimentation.

## Exit gate

All S1 gates green; the 8 GPU tests pass on the runner and still skip on a
CPU host; the CPU suite is unchanged; every acceptance criterion is
evidence-mapped. Hand off to the mandatory S2 audit `0144J`.

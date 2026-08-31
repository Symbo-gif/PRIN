# Session 0144I2 — WP-036D S1 (sub-pass 2/3): Python device dispatch and DLPack marshalling

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S1 — Coding
**Predecessor:** [0144I1 — PyO3 GPU binding layer](0144I1-wp036d-s1-pyo3-gpu-binding-layer.md)
**Successor:** [0144I3 — GPU test activation and CI](0144I3-wp036d-s1-gpu-test-activation-and-ci.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36, and [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Add device dispatch to `python/prin/_torch_compat.py` (Phase B of audit
`036b` §8.4): an `_is_gpu(tensor)` predicate and per-class dispatch branches
that route a CUDA input tensor to the `0144I1` GPU binding path and leave
every CPU input on the current `_numpy()` → Rust CPU → `_tensor()` path
**unchanged, byte for byte**.

## Contract

- Dispatch branches for exactly the classes the 8 GPU acceptance tests
  exercise: `DeltaThetaGammaNetwork` (`test_gpu_forward` / `test_gpu_parity`
  in `test_acceptance_hierarchical.py`), `PhaseToRateConverter`
  (`test_gpu_parity` in `test_acceptance_phase_to_rate.py`), the q2 sparse
  k-NN coupling-derivative path (`test_sparse_on_gpu` /
  `test_sparse_vram_subquadratic`), `ExponentialIntegrator`
  (`test_gpu_exponential_integrator`), and the gradient-checkpoint
  frequency / VRAM-budget helpers (`test_checkpoint_gpu_memory_budget` /
  `test_checkpoint_vram_stays_bounded`).
- The GPU branch marshals via DLPack (the `0144I1` f32 GPU helpers), runs the
  CubeCL kernel, and returns the GPU tensor directly — no `_numpy()`, no host
  round-trip; `tensor.device.type == "cuda"` holds on the result.
- The CPU branch is the existing code verbatim. A dedicated test asserts the
  CPU path output is identical pre/post this change for a representative
  input per touched class.
- No Python numerics; `tools/check_no_python_numerics.py` stays clean for all
  governed modules. `prin.__all__` / `FROZEN_PUBLIC_API` unchanged;
  `verify_api_surface(prin.__all__) == (set(), set())` re-confirmed.
- **Non-goals:** the Rust binding (`0144I1`, consumed here); `@pytest.mark.gpu`
  / `gpu.yml` (`0144I3`); `prin-train`; new public symbols; Triton;
  `test_gpu.py`.

## Required reading

- The 0144I parent brief and the decomposition plan; the `0144I1` handoff
- `python/prin/_torch_compat.py` (`_numpy` / `_tensor` marshalling, audit
  §8.2 quote) and the WP-036A `python/prin/nn/_bridge.py` dispatch precedent
- `DOCS/audits/036b-wp036b-audit.md` §8.2–§8.4
- `tools/check_no_python_numerics.py`; Testing Standards §1, §3

## Entry conditions

`0144I1` committed at its green gate; the GPU binding module imports.

## Expected work

1. Add `_is_gpu` and the per-class dispatch branches; keep the CPU `else`
   branch untouched.
2. Add DLPack GPU marshalling glue calling the `0144I1` bindings.
3. Unit tests: dispatch predicate; CPU-path parity pre/post; GPU-path device
   assertion (skipif-guarded on CUDA).
4. Run `ruff` / `ruff format --check` / `mypy --strict`,
   `check_no_python_numerics.py` + its 4 tests, the full CPU acceptance
   subset (still 489 pass / 9 skip), `bandit`, Snyk Code on the modified
   module; ≥95% coverage on changed lines.
5. Append evidence to `DOCS/experiments/0144I-wp036d-s1-handoff.md`.

## Prohibited

Any change to the CPU marshalling path, Python numerics, new public symbols,
`prin-train` changes, weakened assertions, hidden RNG, scope creep, or push.

## Exit gate

Device dispatch is in place, the CPU path is provably unchanged, the CPU
acceptance subset is still 489 pass / 9 skip, `check_no_python_numerics` is
clean, and the sub-pass local gate is green. Commit locally only; proceed to
`0144I3`.

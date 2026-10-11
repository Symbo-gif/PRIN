# PRIN Testing Standards

**Status:** Normative. No code merges without the tests required here.

---

## 1. Principles

1. **The PRINet 3.0 pytest suite (~1,670 tests) is the acceptance contract.**
   It defines the public API; adapt imports only, never weaken assertions.
2. **Tests are written in tandem with code** — same S1 coding session, same
   commits (Development Workflow Standards §3). A commit adding executable
   behavior without its tests is non-conforming; the S2 audit treats deferred
   tests as a D2 finding. "Tests later" does not exist in this project.
3. **Tests before implementation** for numerics: golden-corpus parity cases and
   property invariants are written (or identified) before the algorithm lands.
4. **Never delete or skip a failing test to make CI green.** Quarantine
   requires a linked issue and maintainer approval.
5. **Determinism.** Every stochastic test seeds explicitly through the `Seed`
   type; flaky tests are treated as bugs.
6. **A hardware/runtime `skipif` guard must probe executability, not
   registration** (ETCA-002 T-F3 / Plan amendment #45 G4). A guard that reads
   `"<EP>" in onnxruntime.get_available_providers()` (or any "is the feature
   *compiled in*" check) does **not** fire on a runner that has the wheel but
   no device, so the guarded test runs and hard-fails in CI. The guard must
   *attempt the operation* (build a one-node session on the provider and run
   it — `tests/_env.py::directml_executes()`; `torch.cuda.is_available()` is
   an accepted device probe) and must be verified to actually skip on a host
   lacking the feature. Hardware-gated tests carry a marker
   (`@pytest.mark.gpu` / `@pytest.mark.directml`) and run on the capable
   self-hosted runner, never silently no-op on a hosted one. The
   `governance` CI job greps for the registration anti-pattern
   (`tools/check_skipif_probes.py`).

## 2. Test layers (all mandatory where applicable)

| Layer | Framework | Requirement |
|---|---|---|
| Rust unit | `cargo test` | Per-module math correctness; edge cases: N=1, zero coupling, extreme K, empty k-NN; clamp/guard behavior under `strict-checks` |
| Rust property | `proptest` | Invariants: phase ∈ [0, 2π); order parameter ∈ [0, 1]; energy monotonicity where guaranteed; integrator order-of-convergence (RK4 error ∝ h⁴) |
| Kernel equivalence | `cargo test --features cuda,wgpu` | Every GPU kernel vs the CPU reference, all supported shapes/dtypes, within documented tolerance |
| Python API | `pytest` (`tests/`) | Ported acceptance suite + tests for all new public symbols |
| Parity | `pytest` differential job (`parity/`) | Old (`prinet==3.0.0`) vs new on the golden corpus + hypothesis fuzzing |
| Gradient checks | `torch.autograd.gradcheck`, float64 | Every `autograd.Function` bridge, forward and backward |
| GPU integration | marker `gpu`, self-hosted runner | Opt-in via `[gpu]` commit tag |
| Reproducibility | CI `repro.yml` | `tools/reproduce.py` output + SHA-256 manifest match |
| Benchmarks | `criterion` + `pytest-benchmark` | Regression gates: fail on >10% slowdown |

## 3. Numerical tolerances (from the parity program)

| Quantity | Tolerance |
|---|---|
| Trajectories (vs float64 reference) | `rtol=1e-6`, `atol=1e-8` |
| Chaotic regimes | Statistical comparison (order-parameter time series) beyond the shadowing horizon — never pointwise |
| Metrics / tensor decompositions (float64) | `rtol=2e-6`, `atol=1e-12` for cross-platform corpus-regeneration comparisons (amendments #16, #17); single-runtime verification targets `rtol=1e-10` where achievable |
| GPU kernel vs CPU reference (f32) | Documented per kernel; default `rtol=1e-5`, `atol=1e-6` |

Tolerance loosening requires a PR note, reviewer sign-off, and a Parity Report
entry.

## 4. Coverage and quality gates

- **≥95% line coverage for new/changed code** (codecov on `python.yml`;
  `cargo llvm-cov` once wired). Coverage may never decrease on `main`.
- Every bug fix ships a regression test that fails before the fix.
- Markers: `slow` (>5 s), `gpu`, `parity`. Default CI runs
  `-m "not slow and not gpu"`; the full suite runs nightly and on release tags.
- Tests must be independent and order-insensitive; no network access in unit
  tests; dataset-dependent tests use cached fixtures.

## 5. Audit hooks (Session Cycle S2)

The per-cycle audit verifies, with command evidence (checklist A3):

- Every S1 commit touching `crates/**` or `python/**` source has
  corresponding test changes in the same session's commit range (or a
  documented justification, e.g. pure refactor covered by existing tests).
- Coverage on new/changed code ≥95% and non-decreasing overall.
- Required specialized tests exist for the WP scope: parity cases for touched
  primitives, property tests for touched invariants, gradcheck for touched
  bridges, kernel-equivalence for touched kernels.
- No test was weakened: assertion deletions/tolerance loosenings in the diff
  require explicit reviewer sign-off recorded in the PR.

## 6. Commands

```bash
# Rust
cargo test --workspace
cargo test --workspace --features strict-checks

# Python (fast gate)
pytest tests/ -v -m "not slow and not gpu"

# Parity (requires prinet==3.0.0 installed)
pytest parity/ -v -m parity

# Full suite
pytest tests/ parity/ -v
```

## 7. Supervised local validation — timeout governance (Plan amendment #49)

Adopted 2026-10-11 within the existing session-0159 E1 scope. This section is
the normative policy for how required local validation runs are supervised;
Development Workflow and Audit Standards §3, Coding Standards §5, the
Benchmarking and Experimentation Standards, and `AGENTS.md` cross-reference it.

1. **Required checks run to completion.** Supervised local validation checks
   (the Coding Standards §5 local gate and the §6 suite invocations) run to
   their actual completion. No arbitrary whole-run wall-clock limit may kill
   a run that is demonstrably making productive progress.
2. **Finite bounds are workload- and evidence-based.** Where a finite bound
   is unavoidable or retained (an outer harness limit, an infrastructure
   ceiling), it is documented per workload and sized from cited
   completed/incomplete evidence for that workload, plus substantial margin
   for setup, instrumentation/coverage overhead, compilation, and host
   variability. A generic 30-minute bound on the full suite is unjustified by
   the evidence (the recorded completed no-coverage full runs took
   ~27–30 minutes). **90 minutes is an evidenced initial allowance for the
   full suite, not a universal ceiling**; coverage-instrumented and other
   heavier runs are sized separately from their own evidence.
3. **Stall diagnosis requires multiple observations.** Quiet output, a
   repeated stack sample, or a faulthandler `Timeout` message alone is not
   proof of a hang. A stall claim needs at least two timestamped observations
   and must distinguish process identity/status, whether the completed-work
   count is changing, stack contents, CPU-time and I/O counters, and the
   expected known behaviour of the node under observation. Diagnostics are
   retained; a guessed attribution is never recorded as cause.
4. **A wait expiring is not a process deadline or failure.** Expiry of a
   tool/agent wait is a property of the waiter, not of the subprocess. The
   session retains handles/PIDs/log offsets and resumes observation of the
   live run; it never starts a duplicate of a run that may still be live.
5. **Stop conditions are real faults.** A failing assertion, crash, deadlock,
   resource exhaustion, or work verified stalled under item 3 requires stop
   or escalation. Before termination the session preserves diagnostics, and
   any cleanup is restricted to the session-owned process tree — never a
   blanket kill of all `python`/`cargo` processes on the host.
6. **Incomplete is not pass.** A killed or incomplete run is recorded with
   its actual exit status and the scope it did not cover, and is never
   reported as a pass. No session may skip tests, weaken assertions, shorten
   scientific samples, or suppress warnings to obtain a green result.
7. **Purposeful timeouts are retained.** Operation-specific network,
   subprocess, and test timeouts, resource limits, and infrastructure
   ceilings are kept where useful. This policy removes indiscriminate
   whole-run limits, not per-operation timeouts.
8. **Scientific parameters are unchanged.** Experiment CPU/GPU/CI/storage
   budgets, abort criteria, benchmark and statistical targets, seeds, and
   tolerances are unaffected; only validation-run supervision changed.
9. **Claims still require completed evidence.** Scan, coverage, and platform
   claims require completed matching evidence; a longer budget does not
   retroactively satisfy an interrupted run (DV-033 remains OPEN — the
   interrupted coverage run claims no coverage total). The amendment #48
   local-validation regime remains in force and unaffected.

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
| Metrics / tensor decompositions (float64) | `rtol=1e-10` |
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

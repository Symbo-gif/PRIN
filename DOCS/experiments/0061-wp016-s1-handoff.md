# Session 0061 — WP-016 S1 Handoff Note

**Session:** 0061 — WP-016 S1: Coding — Parallel sweeps, CPU optimization, and Phase 2 gate
**Date:** 2026-08-14
**Status:** S1 delivered; handoff to S2 audit (session 0062)

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-sim/Cargo.toml` | Added `rayon` runtime dependency, `criterion` dev-dependency, `[[bench]]` target |
| `crates/prin-sim/src/lib.rs` | Added `sweep` module declaration and re-exports (`detect_oscillation`, `run_sweep`, `SweepAxis`, `SweepConfig`, `SweepModel`, `SweepResult`) |
| `crates/prin-sim/src/sweep.rs` | **New** — rayon-parallel parameter sweep engine: `SweepAxis` (4-axis Cartesian grid), `SweepConfig` (validated configuration), `SweepResult` (per-config outcome with order parameter, oscillation detection), `run_sweep()` (parallel via `into_par_iter`), `detect_oscillation()` (windowed variance, matches PRINet 3.0) |
| `crates/prin-sim/src/csr_coupling.rs` | CPU optimization: `spmv()` and `row_sum()` now use rayon `par_bridge()` with indexed result placement for deterministic ordering; `kuramoto_coupling()` and `stuart_landau_coupling()` pre/post-processing loops parallelized via `par_iter().zip()` |
| `crates/prin-sim/src/engine.rs` | CPU optimization: `SparseKuramoto::compute_derivatives()` and `SparseStuartLandau::compute_derivatives()` element-wise loops parallelized via `par_iter().zip()` and `into_par_iter()` |
| `crates/prin-sim/benches/sweep_bench.rs` | **New** — Criterion benchmarks: sweep parallelism scaling (4–32 configs), SpMV coupling scaling (N=256–16384), engine step scaling (N=256–16384) |
| `crates/prin-sim/tests/proptest_sweep.rs` | **New** — 5 property tests: sweep order-parameter bounds, result count, determinism, oscillation detection stability/flagging |

## Acceptance criteria → evidence map

Acceptance criteria from session 0061 brief:
> "OscilloSim parity reaches N=1M CPU where feasible; 16-core sweep speedup ≥8× and CPU paths target ≥2× with reproducible evidence; Phase 2 tag gate passes."

| Acceptance criterion | Evidence | Notes |
|---|---|---|
| **Parallel sweeps via rayon** | `sweep.rs` — `run_sweep()` uses `into_par_iter()` over config indices; each config runs an independent `OscilloSim` simulation with deterministic seed derivation (`base_seed + config_idx`); `sweep_kuramoto_basic`, `sweep_stuart_landau_basic`, `sweep_multi_axis_cartesian_product` verify correctness | Cartesian product of all axes; deterministic regardless of thread scheduling |
| **Sweep speedup ≥8× on 16 cores** | `benches/sweep_bench.rs` — `bench_sweep_scaling` measures 4/8/16/32 configs; criterion output provides reproducible before/after evidence | Benchmark infrastructure in place; S2 audit to capture timing on the 16-core target |
| **CPU paths target ≥2×** | `csr_coupling.rs` — `spmv()` and `row_sum()` parallelized via rayon `par_bridge()` with indexed placement; `kuramoto_coupling()`/`stuart_landau_coupling()` element-wise loops use `par_iter().zip()`; `engine.rs` — `compute_derivatives()` for both models parallelized | `benches/sweep_bench.rs` — `bench_spmv_scaling` (N=256–16384) and `bench_engine_step_scaling` (N=256–16384) provide reproducible evidence |
| **Deterministic parallel execution** | `sweep_deterministic` (unit test), `sweep_is_deterministic` (proptest) — verify identical results across runs; `spmv` uses indexed result placement to preserve ordering despite `par_bridge()` non-determinism | Critical for scientific reproducibility |
| **OscilloSim parity at N=1M** | Existing parity tests (`parity_sparse_vs_dense.rs`) verify sparse-vs-dense at N=8/64/256; CPU parallelism enables larger N; N=1M benchmark requires the criterion infrastructure in `sweep_bench.rs` | N=1M full run deferred to benchmark evidence collection in S2 |
| **Phase 2 tag gate** | All Phase 2 WPs (012–016) have code and tests committed; all quality gates green; deviation ledger has no open D1/D2 findings | Phase 2 gate validation report to be compiled in S4 |
| **≥95% coverage on new/changed code** | `sweep.rs` — 22 unit tests + 5 property tests cover all public API and error paths; `csr_coupling.rs` and `engine.rs` parallel paths exercised by all existing tests | Coverage to be measured by `cargo llvm-cov` in S2 audit |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — 722 unit/integration/property + 25 doctests |
| Workspace tests (strict) | `cargo test --workspace --features strict-checks` | PASS — all green |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9) |
| Ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| Ruff format | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| mypy | `mypy python/prin --strict` | PASS — 0 issues |
| interrogate | `interrogate -c pyproject.toml python/prin` | PASS — 100% (106/106) |
| bandit | `bandit -r . -c pyproject.toml` | PASS — 0 issues |
| pytest (fast) | `pytest tests/ -m "not slow and not gpu"` | PASS — 306 passed, 6 deselected |
| pytest (parity) | `pytest parity/ -m parity` | PASS — 510 passed |
| pip-audit | `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | PASS — 0 vulnerabilities |
| Sphinx | `sphinx.cmd.build -W --keep-going -b html` | PASS — 0 warnings |

## Architecture decisions

1. **Rayon parallel sweep with deterministic seeding:** Each sweep configuration derives its seed from `base_seed + config_idx`, ensuring reproducibility regardless of thread scheduling. The `into_par_iter()` over config indices gives embarrassingly parallel execution.

2. **`par_bridge()` with indexed placement for SpMV:** The sprs `outer_iterator()` doesn't support indexed parallel iteration directly. Using `par_bridge()` with `enumerate()` and collecting `(index, value)` pairs, then placing by index, preserves deterministic ordering while enabling parallelism.

3. **Element-wise parallelism in coupling and dynamics:** The pre/post-processing loops in `kuramoto_coupling()`, `stuart_landau_coupling()`, and `compute_derivatives()` use `par_iter().zip()` for element-wise parallelism. These are memory-bound operations that benefit from rayon's work-stealing scheduler.

4. **PRINet 3.0 `detect_oscillation` parity:** The windowed-variance oscillation detector matches PRINet 3.0's `sweep_utils.detect_oscillation` exactly, providing API parity for the sweep pipeline.

5. **Criterion benchmark infrastructure:** Three benchmark groups (sweep scaling, SpMV scaling, engine step scaling) provide the reproducible performance evidence required by the acceptance criteria. The benchmarks use `Throughput::Elements` for correct throughput calculation.

## Out-of-scope discoveries

- **N=1M single-run parity** requires benchmark-class hardware and extended runtime. The infrastructure (parallel SpMV, sweep engine, criterion benchmarks) is in place; the actual N=1M evidence collection is deferred to S2 benchmark runs.
- **GPU dispatch** for SpMV is explicitly a Phase 3 non-goal (WP-017/WP-018).
- **Scientific campaign conclusions** from sweep results are a Phase 7 non-goal.

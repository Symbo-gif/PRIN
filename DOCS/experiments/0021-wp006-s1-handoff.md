# WP-006 S1 handoff to session 0022

**Session:** 0021 — S1 Coding  
**Work package:** WP-006 — Oscillator state, errors, and deterministic seed  
**Date:** 2026-08-07  
**Branch:** `feat/wp006-oscillator-state`  
**Pre-S1 baseline:** `d7fb8c8` (WP-005 S4 closure)  
**Implementation range:** `d7fb8c8..531aa54`  
**Successor:** [Session 0022](../sessions/phase-1/0022-wp006-s2-oscillator-state-errors-and-deterministic-seed.md) — mandatory read-only S2 audit

## 1. S1 author claim

The WP-006 S1 implementation and evidence outputs are complete to the author's
knowledge. The new `prin-dynamics` `state` and `seed` modules implement the
struct-of-arrays oscillator state, phase wrapping, atan2-safe phase differences,
numerical guards, typed errors, and the counter-based `Seed` authority with
reproducible streams. Acceptance criteria are mapped below.

This claim is not an audit verdict or cycle-completion claim. Session status and
register updates are reserved for S4.

## 2. Acceptance-to-evidence map

| WP-006 acceptance criterion | S1 evidence | Author assessment |
|---|---|---|
| Struct-of-arrays oscillator state | `OscillatorState` fields `phase`, `amplitude`, `frequency`, optional `freq_band`; `new`, `create_random`, `create_synchronized`, `n_oscillators`, `n_bands` in `crates/prin-dynamics/src/state.rs` | MET |
| Phase wrap to `[0, 2π)` | `wrap_phase` and `wrap_phases` use `f64::rem_euclid(TAU);` unit and property tests for negative, >2π, and 2π inputs | MET |
| atan2-safe phase difference | `safe_phase_diff` and `safe_phase_diffs` use `raw.sin().atan2(raw.cos())`; unit tests for shortest angular distance and wrap cases | MET |
| Amplitude clamp `[1e-6, 10]` | `clamp_amplitude`, `guard_amplitude`; unit/property tests for in-range, out-of-range, NaN, and ±Inf | MET |
| Derivative clamp `±1e4` | `clamp_derivative`, `guard_derivative`; unit/property tests for in-range, out-of-range, NaN, and ±Inf | MET |
| Typed errors | `StateError` and `SeedError` enums with `thiserror` messages; all public constructors return `Result<_, StateError>` or `Result<_, SeedError>` | MET |
| `strict-checks` behavior | `#[cfg(feature = "strict-checks")]` guard functions return typed errors; non-strict build clamps/repairs; both builds covered by conditional tests | MET |
| Sort-based phase k-NN index | `build_phase_knn_index` uses `rayon` parallel sort, `O(N log N)`, with deterministic tie-breaking; unit and property tests for `k=0`, invalid `k`, wrap, and no-self | MET |
| Counter-based `Seed` authority | `Seed` on `Pcg64` with `(counter, key)` identity, `jump`, manual `f64` draw, `RngCore` impl, and serde round-trip | MET |
| Deterministic / reproducible | `create_random` with cloned `Seed` produces identical `OscillatorState`; `Seed` tests verify same `(counter, key)` streams; property tests for reproducibility | MET |
| No hidden global RNG | All randomness flows through the provided `&mut Seed`; no thread-local or global RNG introduced | MET |

## 3. Required evidence map

| Requirement | Evidence | Result |
|---|---|---|
| Tests in tandem | 55 Rust tests in `prin-dynamics` (unit + property) | PASS |
| ≥95% coverage on new/changed code | `cargo llvm-cov -p prin-dynamics`: **100% line coverage**, 98.46% region (default); `cargo llvm-cov -p prin-dynamics --features strict-checks`: **100% line coverage**, 98.79% region | PASS |
| `cargo fmt` | `cargo fmt --all -- --check` | PASS |
| `cargo clippy` | `cargo clippy --workspace --all-targets -- -D warnings` and `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| `cargo test` | `cargo test --workspace` (54 tests) and `cargo test --workspace --features strict-checks` (55 tests) | PASS |
| `cargo doc` | `$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps` | PASS |
| `cargo audit` | `cargo audit` — only inherited `paste` (RUSTSEC-2024-0436) warning via `cubecl`; no actionable new finding | PASS |
| Python ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` and `ruff format --check ...` | PASS |
| Python mypy | `mypy python/prin --strict` | PASS |
| Python doc coverage | `interrogate -c pyproject.toml python/prin` 100% | PASS |
| Python SAST | `bandit -r . -c pyproject.toml` | PASS |
| Python tests | `pytest tests/ parity/ --basetemp=.pytest_run` | 184 passed |
| Python coverage | `pytest tests/ parity/ --cov=prin` | 99% total; no new Python modules |
| pip-audit | Root project and `DOCS/sphinx/requirements.txt`: no known vulnerabilities | PASS |
| Snyk Code | `snyk_code_scan` on `C:\dev\PRIN` with `severity_threshold=medium` | 0 issues |
| Snyk Open Source | `snyk_sca_scan` on `C:\dev\PRIN` with `severity_threshold=low` | 0 issues |
| Sphinx docs | `sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | PASS |

## 4. Implementation summary

- **`crates/prin-dynamics/src/state.rs`:**
  - `OscillatorState` struct-of-arrays with `new`, `create_random`, `create_synchronized`.
  - `wrap_phase` / `wrap_phases` (Euclidean remainder to `[0, 2π)`).
  - `safe_phase_diff` / `safe_phase_diffs` (`atan2(sin(Δ), cos(Δ))`).
  - `clamp_amplitude`, `clamp_derivative`, `guard_amplitude`, `guard_derivative`.
  - `build_phase_knn_index` with `rayon` parallel sort and deterministic wrap.
  - `StateError` with typed variants for length mismatch, non-finite values,
    out-of-range values, invalid k-NN count, and invalid frequency range.
- **`crates/prin-dynamics/src/seed.rs`:**
  - `Seed` counter-based authority on `rand_pcg::Pcg64`.
  - `new(counter, key)` produces a deterministic stream at the requested offset.
  - `jump(delta)` for parallel reproducible streams.
  - `next_f64`, `next_f64_range`, `RngCore` implementation, and serde round-trip.
  - `SeedError` for counter overflow.
- **`crates/prin-dynamics/Cargo.toml`:**
  - Added `serde_json` dev-dependency for seed round-trip tests.
  - Default feature set changed to `[]` so `strict-checks` is opt-in, matching the
    `Testing_Standards` one-liner (`cargo test --workspace` and
    `cargo test --workspace --features strict-checks`).
- **`crates/prin-dynamics/src/lib.rs`:**
  - Added `pub mod seed;` and re-exported `Seed`, `SeedError`, `OscillatorState`,
    `StateError`.

## 5. Out-of-scope discovery log

| Discovery | Why not implemented in S1 | Planned owner / next control |
|---|---|---|
| Python bindings for `OscillatorState` and `Seed` | WP-006 S1 is Rust core only; PyO3 integration belongs to WP-011 / Phase 1 S4 or a later coupling session | WP-011 |
| Batched / 2-D oscillator state | Reference `OscillatorState` is 1-D; batched variants will be built on top in WP-009/010 | WP-009/010 |
| Dynamics equations and integrators | Explicitly out of scope per session brief; `prin-dynamics::models` and `prin-dynamics::integrate` remain placeholders | WP-007/008 |
| Deterministic benchmarks | No performance work package active yet; timing captured informally during test runs | WP-012+ |

## 6. Handoff constraints

- Freeze the S1 source/evidence range for read-only inspection.
- Begin only session `0022-wp006-s2-oscillator-state-errors-and-deterministic-seed`
  via the audit flow.
- Do not remediate during S2.
- Do not update the session register, brief status, CHANGELOG, or Project State
  Report until their governed sessions.

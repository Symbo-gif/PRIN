# PRIN Audit Report — Cycle 006 / WP-006

**Date:** 2026-08-07
**Auditor:** Devin (AI pair)
**Scope:** WP-006 "Oscillator state, errors, and deterministic seed" — `crates/prin-dynamics/src/state.rs`, `crates/prin-dynamics/src/seed.rs`, `crates/prin-dynamics/src/lib.rs`, `crates/prin-dynamics/Cargo.toml`
**Sessions:** 0021 S1 implementation; 0022 S2 this audit
**Active brief:** `DOCS/sessions/phase-1/0022-wp006-s2-oscillator-state-errors-and-deterministic-seed.md`
**Git state:** `feat/wp006-oscillator-state` @ `9153c7c`
**Pre-S1 baseline:** `d7fb8c8` (WP-005 S4 closure)
**S1 implementation range:** `d7fb8c8..531aa54`
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-006 delivers the struct-of-arrays `OscillatorState`, phase wrap and `atan2`-safe phase-difference helpers, amplitude/derivative clamp and guard functions, typed `StateError`/`SeedError`, a counter-based deterministic `Seed` authority on `rand_pcg::Pcg64`, and a sort-based phase k-NN index. The S1 code and tests are written in tandem, both default and `strict-checks` builds are green, and security/dependency scans are clean. Rust line coverage on the new `prin-dynamics` code is 100%, and the Python parity suite remains green.

The audit raises one **D2** numerical/contract finding on `Seed::next_f64_range`, one **D3** CI/test-coverage finding on the `strict-checks` feature not being exercised in `.github/workflows/rust.yml`, and one **D4** hygiene finding on an unrecorded post-S1 commit (`9153c7c`) that hardens the WP-001 baseline tool but appears on the WP-006 branch outside the declared S1 range.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared oscillator state, guards, typed errors, and `Seed` authority; dynamics/integrators/models remain placeholders per out-of-scope log |
| Plan/architecture conformance (A2) | PASS | Struct-of-arrays, no hidden global RNG, typed errors, `Pcg64`-based `Seed`, `strict-checks` opt-in; the `strict-checks` default changed from `default = ["strict-checks"]` to `default = []` to match the Testing_Standards one-liner |
| Tests in tandem + coverage (A3) | PASS | 54 unit/property tests in default `prin-dynamics`, 55 with `strict-checks`; `cargo llvm-cov` reports 100% line and ~98.5% region coverage on new code; Python suite 184 passed |
| Numerical parity + invariants (A4) | ⚠️ | Phase wrap, amplitude/derivative clamps, safe phase differences, and k-NN invariants are proven; `Seed::next_f64_range` can round to the documented half-open upper bound `hi` for the maximum 53-bit draw and suitable `lo/hi` (`WP006-F1`) |
| Quality gates (A5) | PASS | `cargo fmt`, `cargo clippy` (default + strict), `cargo doc -D warnings`, `ruff`, `mypy --strict`, `interrogate`, `bandit` all pass |
| Security (A6) | PASS | Snyk Code (medium+) and Snyk Open Source (low+) report 0 issues; `cargo audit` retains one allowed inherited `paste` RUSTSEC-2024-0436 warning; no new `unsafe`; `#![forbid(unsafe_code)]` in `prin-dynamics` |
| Docstring/doc coverage (A7) | PASS | All new public Rust symbols are documented; Sphinx build clean; `interrogate` 100% on `python/prin` |
| Repository hygiene (A8) | PASS | No TODO/FIXME/stub markers in new source; consistent naming; `__all__` not affected |
| CI status (A9) | ⚠️ | `.github/workflows/rust.yml` does not run `cargo test` or `cargo clippy` with `--features strict-checks`, so the feature-gated guard code is not exercised in the authoritative merge gate (`WP006-F2`) |
| Artefact trail (A10) | ⚠️ | WP-005 S4 project state and audit are present; S1 handoff `DOCS/experiments/0021-wp006-s1-handoff.md` is committed; post-S1 commit `9153c7c` hardens `tools/wp001_baseline.py` but is outside the declared WP-006 S1 range and not yet recorded as a hotfix (`WP006-F3`) |

## 1.1 Acceptance reproduction

| WP-006 acceptance criterion | Independent result | Assessment |
|---|---|---|
| Struct-of-arrays oscillator state | `OscillatorState` fields `phase`, `amplitude`, `frequency`, optional `freq_band`; `new`, `create_random`, `create_synchronized`, `n_oscillators`, `n_bands` present and tested | MET |
| Phase wrap to `[0, 2π)` | `wrap_phase` / `wrap_phases` use `f64::rem_euclid(TAU)`; unit/property tests for negative, >2π, and 2π inputs pass | MET |
| atan2-safe phase difference | `safe_phase_diff` / `safe_phase_diffs` use `raw.sin().atan2(raw.cos())`; unit/property tests for shortest signed distance and wrap cases pass | MET |
| Amplitude clamp `[1e-6, 10]` | `clamp_amplitude`, `guard_amplitude` with unit/property tests for in-range, out-of-range, NaN, ±Inf pass | MET |
| Derivative clamp `±1e4` | `clamp_derivative`, `guard_derivative` with unit/property tests for in-range, out-of-range, NaN, ±Inf pass | MET |
| Typed errors | `StateError` and `SeedError` enums with `thiserror`; all public constructors return `Result<_, StateError>` or `Result<_, SeedError>` | MET |
| `strict-checks` behavior | `#[cfg(feature = "strict-checks")]` guard functions return typed errors; non-strict build clamps/repairs; both builds covered by conditional tests | MET locally; not in CI (`WP006-F2`) |
| Sort-based phase k-NN index | `build_phase_knn_index` uses `rayon` parallel sort with deterministic tie-breaking; unit/property tests for `k=0`, invalid `k`, wrap, no-self pass | MET |
| Counter-based `Seed` authority | `Seed` on `Pcg64` with `(counter, key)` identity, `jump`, manual `f64` draw, `RngCore` impl, and serde round-trip pass | MET |
| Deterministic / reproducible | `create_random` with cloned `Seed` produces identical `OscillatorState`; `Seed` tests verify reproducible streams; property tests pass | MET |
| No hidden global RNG | All randomness in `prin-dynamics` flows through the provided `&mut Seed`; no thread-local or global RNG introduced | MET |

---

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `torch`: 2.13.0+cpu

### 2.2 Scope and artefact commands

```powershell
git log --oneline d7fb8c8..HEAD
git diff --stat d7fb8c8..531aa54
```

Key results:

```text
9153c7c Harden wp001_baseline against untrusted root/ownership paths.
6ef3924 docs(WP-006 S1): add S1 handoff and evidence mapping
531aa54 feat(prin-dynamics): WP-006 S1 oscillator state, guards, typed errors, and deterministic Seed

diff --stat d7fb8c8..531aa54:
 Cargo.lock                        |   1 +
 crates/prin-dynamics/Cargo.toml   |   3 +-
 crates/prin-dynamics/src/lib.rs   |   6 +
 crates/prin-dynamics/src/seed.rs  | 293 ++++++++++++
 crates/prin-dynamics/src/state.rs | 954 +++++++++++++++++++++++++++++-
 5 files changed, 1255 insertions(+), 2 deletions(-)
```

### 2.3 Python quality, test, and coverage commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

Key results:

```text
ruff check: All checks passed
ruff format --check: 40 files already formatted
mypy: Success: no issues found in 16 source files
interrogate: 100.0% (min 95.0%)
bandit: No issues identified
pytest tests/ -m "not slow and not gpu": 172 passed, 6 deselected
pytest tests/ parity/: 184 passed
coverage: 99% total; no new Python modules
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
sphinx: build succeeded
```

### 2.4 Rust quality, test, and documentation commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy (default): 0 warnings
cargo clippy (--features strict-checks): 0 warnings
cargo test --workspace: 73 Rust tests passed (54 in prin-dynamics, 13 in prin-kernels, 6 in _prin_core)
cargo test --workspace --features strict-checks: 74 Rust tests passed (55 in prin-dynamics)
cargo doc -D warnings: 0 warnings
```

### 2.5 Rust coverage commands

```powershell
cargo llvm-cov -p prin-dynamics --json --output-path target/llvm-cov/prin-dynamics-default.json
cargo llvm-cov -p prin-dynamics --features strict-checks --json --output-path target/llvm-cov/prin-dynamics-strict.json
```

Key results:

```text
Default build: lines 100%, functions 100%, instantiations 100%, regions 98.46%
Strict build:  lines 100%, functions 100%, instantiations 100%, regions 98.79%
```

The remaining uncovered regions are failure branches inside `assert!` and the complementary `#[cfg(not(feature = "strict-checks"))]` / `#[cfg(feature = "strict-checks")]` blocks, which are exercised in the separate feature build.

### 2.6 Dependency and security audit commands

```powershell
cargo audit
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

Key results:

```text
cargo audit: 0 vulnerabilities; 1 inherited paste (RUSTSEC-2024-0436) unmaintained warning (amendment #9)
Snyk Code: issueCount=0
Snyk Open Source: issueCount=0
```

### 2.7 WP-006 numerical-invariant reproduction

The `Seed::next_f64_range` half-open contract was checked with the same IEEE-754 arithmetic used by Rust:

```python
>>> lo, hi = 1.0, 2.0
>>> max_draw = float((1 << 53) - 1) / float(1 << 53)  # largest value next_f64() can return
>>> x = lo + max_draw * (hi - lo)
>>> x
2.0
>>> x >= hi
True
```

This shows that for the maximum 53-bit mantissa draw and a range such as `[1.0, 2.0)`, the expression `lo + next_f64() * (hi - lo)` can round to exactly `hi`, violating the documented `[lo, hi)` contract.

---

## 3. Detailed findings

### 3.1 WP/session-brief scope conformance (A1)

The S1 implementation adds exactly the artefacts declared in the WP-006 S1 brief: `OscillatorState`, phase wrapping, safe phase differences, amplitude/derivative guards, typed `StateError`/`SeedError`, and the counter-based `Seed` authority. The placeholders for `models`, `integrate`, `pac`, etc. remain with module-level docs and no implementation, consistent with the out-of-scope log.

### 3.2 Plan/architecture conformance (A2)

The implementation follows the plan §4 architecture rules:

- All numerics are in the Rust `prin-dynamics` crate; Python layer contains no new numerics.
- `OscillatorState` is a struct of arrays (`phase`, `amplitude`, `frequency`, optional `freq_band`).
- No hidden global RNG; all randomness is injected as `&mut Seed`.
- `Seed` uses `Pcg64` with `(counter, key)` identity, `jump`, and `RngCore`.
- `strict-checks` is a feature flag, now opt-in (`default = []`) so that `cargo test --workspace` and `cargo test --workspace --features strict-checks` both work as specified in `Testing_Standards.md`.

### 3.3 Tests in tandem + coverage (A3)

S1 adds tests in the same commit as the implementation (`531aa54`). The default `prin-dynamics` suite runs 54 unit/property tests, and the `strict-checks` build runs 55. Python tests for the project continue to pass (184 in the full suite). Rust line coverage on new `prin-dynamics` code is 100% in both feature configurations, with region coverage above the 95% gate (98.46% default, 98.79% strict). No test appears weakened or skipped.

### 3.4 Numerical parity + invariants (A4)

The phase wrap, amplitude/derivative clamps, safe phase differences, and k-NN invariants are verified by unit and property tests. The property tests confirm:

- `wrap_phase(p) ∈ [0, 2π)` for finite `p`.
- `safe_phase_diff(a, b) ∈ [-π, π]`.
- `clamp_amplitude(amp) ∈ [1e-6, 10]` and `clamp_derivative(d) ∈ [-1e4, 1e4]`.
- `create_random` produces reproducible `OscillatorState` and phase/frequency in expected ranges.

The gap is `Seed::next_f64_range`: its docstring promises a half-open interval `[lo, hi)`, but the naive affine transform `lo + next_f64() * (hi - lo)` can round to `hi` for the maximum 53-bit draw and certain `lo/hi` (e.g. `lo = 1.0, hi = 2.0`). The `create_random` proptest asserts `frequency.iter().all(|&f| (lo..hi).contains(&f))`, so this latent bug is a future test-flake risk. This is `WP006-F1`.

### 3.5 Quality gates (A5)

All quality gates pass:

- `cargo fmt --all -- --check`: clean
- `cargo clippy --workspace --all-targets -- -D warnings`: 0 warnings
- `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings`: 0 warnings
- `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`: 0 warnings
- `ruff`, `ruff format --check`, `mypy --strict`, `interrogate`, `bandit`: all clean

### 3.6 Security (A6)

- No new `unsafe` Rust code in `prin-dynamics`; `lib.rs` has `#![forbid(unsafe_code)]`.
- Snyk Code (medium+) and Snyk Open Source (low+) both report 0 issues.
- `cargo audit` reports only the inherited `paste` (RUSTSEC-2024-0436) warning, governed by plan amendment #9.
- `pip-audit` and `bandit` report no issues.

### 3.7 Docstring/doc coverage (A7)

`cargo doc -D warnings` is clean; all new public Rust symbols in `prin-dynamics` have doc comments. `interrogate` reports 100% docstring coverage for `python/prin` (no new Python modules). Sphinx builds without warnings.

### 3.8 Repository hygiene (A8)

No TODO/FIXME/stub markers are present in the new `state.rs` or `seed.rs` source. The new public symbols are re-exported cleanly from `crates/prin-dynamics/src/lib.rs`. The crate naming and style follow the Coding_Standards.

### 3.9 CI status (A9)

`.github/workflows/rust.yml` runs `cargo fmt`, `cargo clippy --workspace --all-targets`, `cargo test --workspace`, `cargo doc`, and `cargo audit`. However, it does **not** run `cargo test --workspace --features strict-checks` or `cargo clippy --workspace --all-targets --features strict-checks`. Because a significant portion of the WP-006 test code and guard behaviour is conditional on `#[cfg(feature = "strict-checks")]`, the authoritative merge gate does not exercise the strict build. This is `WP006-F2`.

### 3.10 Artefact trail (A10)

The WP-005 S4 project state report and audit are present. The WP-006 S1 handoff `DOCS/experiments/0021-wp006-s1-handoff.md` is committed and consistent with the source. However, the current branch HEAD (`9153c7c`) is outside the declared S1 implementation range (`d7fb8c8..531aa54`) and is a hardening change to `tools/wp001_baseline.py` and `tests/test_wp001_baseline.py`. It passes the baseline check but is not part of the WP-006 S1 evidence and has not yet been recorded as a hotfix. This is `WP006-F3`.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| **WP006-F1** | D2 | `crates/prin-dynamics/src/seed.rs:87-95` and `seed.rs:204-211` | `Seed::next_f64_range` documents a half-open interval `[lo, hi)` and warns that "the debug build may assert `lo < hi` and both finite", but it does neither. The affine transform `lo + next_f64() * (hi - lo)` can round to `hi` for the maximum 53-bit draw (reproduced with `lo = 1.0, hi = 2.0` → `x = 2.0`). This breaks the public API contract and is a latent test-flake risk for `create_random`'s frequency assertion. | Coding_Standards §2.2 (input validation at every public boundary); Testing_Standards A4 (numerical invariants preserved); `Seed` rustdoc | Validate `lo < hi` and finiteness in `next_f64_range` (either `Result`/`SeedError` or documented panic) and use a draw method that guarantees `x < hi`, such as `rand::distributions::Uniform`. Add a regression test covering the `lo = 1.0, hi = 2.0` / max-draw case, and correct or remove the false panic note in the docstring. |
| **WP006-F2** | D3 | `.github/workflows/rust.yml:29-44` | The `rust.yml` matrix tests and clippy only the default feature set. The `strict-checks` feature, which gates the `StateError`/`SeedError` strict guard paths and their dedicated tests, is not exercised in CI. | Testing_Standards §6 (local one-liner includes `cargo test --workspace --features strict-checks`); A9 (CI is the authoritative merge gate) | Add `cargo test --workspace --features strict-checks` and `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` to `.github/workflows/rust.yml` (e.g. as a separate `test-strict` job or an additional matrix step). |
| **WP006-F3** | D4 | `tools/wp001_baseline.py` and `tests/test_wp001_baseline.py` (commit `9153c7c`) | Commit `9153c7c` "Harden wp001_baseline against untrusted root/ownership paths" is on the `feat/wp006-oscillator-state` branch but is outside the declared WP-006 S1 implementation range (`d7fb8c8..531aa54`). It is a beneficial security hardening but is not in the S1 handoff and has not yet been recorded as a hotfix. | Development Workflow and Audit Standards §7 (hotfixes must be retro-audited and recorded in the next S2 and deviation ledger); A10 (artefact trail) | Record `9153c7c` as a WP-001 hotfix in the deviation ledger and perform a delta re-audit of the `wp001_baseline` changes (they pass `tools/wp001_baseline.py check`). Either rebase the commit onto the appropriate WP-001 maintenance branch or confirm it stays on the WP-006 branch with maintainer sign-off before S4. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP006-F1** (D2), **WP006-F2** (D3), **WP006-F3** (D4).

Carried findings re-inspected and unchanged by this WP:

- WP001-F8 (AMENDED) — GitHub secret scanning substitute remains in force.
- WP003-F1 (AMENDED) — `prin-py` Python-FFI `unsafe` exception remains in force.
- WP003-F3 (AMENDED) — WP-003/Phase 0 go/no-go documented as amendment #7.
- WP004-F1 (AMENDED) — inherited `paste` RUSTSEC-2024-0436 warning remains allowed under amendment #9; reconfirmed by `cargo audit`.
- WP004-F2 (AMENDED) — `#[cube(launch)]` non-instrumentability remains documented under amendment #10.
- WP004-F4 (AMENDED) — `prin-kernels` crate-level `unsafe` lint pattern remains under amendment #8.
- WP004-F5 (AMENDED) — Triton 3.0 direct comparison remains deferred to Phase 3/`gpu.yml` under amendment #11.
- WP005-F1–F4 (FIXED) — WP-005 S3 delta re-audit was CLEAN.

No open D1 findings are carried into WP-006.

---

## 6. Verdict and required actions

**Verdict:** `PASS-WITH-FINDINGS` — the WP-006 S1 implementation is in declared scope, the quality and security gates are green, and the new oscillator state and `Seed` authority are well tested. The three findings above are not trajectory breaches (no D1), but they must be addressed in S3 before the cycle can close.

**Ordered S3 action list:**

1. **WP006-F1:** Harden `Seed::next_f64_range` in `crates/prin-dynamics/src/seed.rs` so it (a) validates `lo < hi` and finiteness at the public boundary and (b) guarantees the result is strictly less than `hi` (e.g. by using `rand::distributions::Uniform` or a post-scale clamp that preserves the distribution). Correct the docstring, and add a regression test that fails on the current implementation for `lo = 1.0, hi = 2.0` at the maximum 53-bit draw.
2. **WP006-F2:** Update `.github/workflows/rust.yml` to run `cargo test --workspace --features strict-checks` and `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` in CI.
3. **WP006-F3:** Record the post-S1 hotfix `9153c7c` (`wp001_baseline` path validation) in the deviation ledger and confirm its disposition (rebase to WP-001 branch or keep on WP-006 branch with maintainer sign-off). Re-run `tools/wp001_baseline.py check` after any move.

After these fixes, re-run the full local one-liner and perform a delta re-audit.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP006-F1 | | | |
| WP006-F2 | | | |
| WP006-F3 | | | |

**Delta re-audit date:** — **Result:**

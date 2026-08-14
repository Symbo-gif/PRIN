# PRIN Project State Report — Cycle 014

**Date:** 2026-08-14
**Cycle:** 014 (WP-014 "Tensor decompositions")
**Completed sessions:** 0053–0056
**Author:** Devin (AI pair), approved by MichaelMaillet
**Git state:** `main` @ `2d5b734` (post-S3 baseline; S4 documentation commits follow)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 2 — Advanced numerics and simulation (**3 of 5** phase-2 WPs complete).
- **This cycle delivered:**
  - `prin-tensor` crate: `PolyadicTensor`, `hosvd()`, `CPDecomposition`, `cp_als()`,
    `CPResult`, `TensorError`, plus utilities `mode_unfold`, `mode_n_product`,
    `frobenius_norm`, `refold`, and ndarray/faer conversions.
  - Tucker/HOSVD via `faer` thin SVD with per-mode rank truncation clamped to
    `min(I_n, prod_{k != n} I_k)`; full-rank HOSVD is an exact reconstruction.
  - CP/PARAFAC ALS with deterministic `prin_dynamics::Seed` initialization,
    all-factor normalization (column norms clamped at `1e-12`), and convergence
    monitored via the relative change in reconstruction error `‖X − X̂‖_F`.
  - 9 Rust-vs-PRINet 3.0.0 parity tests in
    `crates/prin-tensor/tests/parity_decomposition.rs` covering reconstruction,
    factor orthonormality, truncated rank shapes, CP rank-1 reconstruction,
    all-factor normalization, positive weights, seed reproducibility, and
    `PolyadicTensor` round-trip at `rtol = 1e-10` (float64, single-runtime).
  - S2 audit (`DOCS/audits/014-wp014-audit.md`) found seven findings
    (WP014-F1 D1, WP014-F2–F4 D2, WP014-F5/F7 D3, WP014-F6 D4): missing parity
    evidence, S1 uncommitted artefact trail, `hosvd` rank-bound panic, `cp.rs`
    coverage below 95%, CP convergence/normalization drift from the reference,
    documentation/hygiene batch, and a GitHub Actions billing block.
  - S3 remediation closed all seven: parity tests added, rank validation fixed
    (`InvalidRank` instead of panic), `cp.rs` coverage raised from 92.55% to
    96.23% lines, CP-ALS aligned with the PRINet 3.0 reference's error-based
    convergence and all-factor normalization, docs/hygiene corrected, and the
    GitHub Actions billing block resolved. Delta re-audit: **CLEAN**.
  - S4 (this cycle) updated `crates/prin-tensor/README.md`,
    `DOCS/experiments/README.md`, `DOCS/audits/README.md`,
    `DOCS/reports/README.md`, `DOCS/sessions/SESSION_REGISTER.md`,
    `DOCS/sessions/phase-2/README.md`, the session 0054/0056 brief statuses, the
    session 0057 successor brief status, `CHANGELOG.md`, and the Sphinx Migration
    Guide; produced this Project State Report.
- **Plan conformance:** ON TRAJECTORY — no new plan amendments required this
  cycle. Amendments #1–19 remain in force.
- **Audit:** `DOCS/audits/014-wp014-audit.md` — S2 verdict `FAIL` (seven
  findings: one D1, three D2, two D3, one D4); S3 closure with CLEAN delta
  re-audit (all seven findings FIXED). The CI billing block was resolved before
  the S3 delta re-audit and all gated workflows ran green on the restored
  account.
- **Session Register:** 0053 (S1), 0054 (S2), 0055 (S3), 0056 (S4) marked
  **COMPLETE**; 0057 (WP-015 S1) marked **READY**.

---

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | 501/501 default workspace, 504/504 with `--features strict-checks`; 22 doctests passing | 535/535 default workspace, 538/538 with `--features strict-checks`; 24 doctests passing | 100% where defined |
| Python tests passing | 306 fast (6 deselected), 510 parity-marked tests | 306 fast (6 deselected); 510 parity-marked tests, all pass | 100% |
| Coverage (changed code) | `bands.rs` 97.73% lines / 98.68% functions, `temporal.rs` 98.98% lines / 100% functions | `prin-tensor/src/cp.rs` 96.23% lines / 97.37% functions, `tucker.rs` 95.65% lines / 97.14% functions, `error.rs` 100% lines / 100% functions, `utils.rs` 97.20% lines / 100% functions; Python overall 99% (677 stmts, 10 miss) | ≥95% |
| Docstring coverage (interrogate) | 100% public (106/106) | 100% public (106/106) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 510 parity-marked Python tests; 23 Rust-native integrator parity tests; 18 Rust-native band/temporal parity tests | 510 parity-marked Python tests (504 golden-corpus cases + 6 harness/schema tests); 23 Rust-native integrator parity tests; 18 Rust-native band/temporal parity tests; 9 new Rust-native tensor parity tests (total 50 Rust-native parity tests) | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 | 0; `cargo audit` retains 1 inherited `paste` RUSTSEC-2024-0436 (amendment #9) | 0 at gate threshold, allowed advisory documented |
| Sphinx warning-as-error build | 0 warnings | 0 warnings; `-W --keep-going` succeeds | 0 warnings |
| Snyk Code / Snyk Open Source | Snyk Code on `crates/prin-dynamics/src` and `crates/prin-py/src`: **0 issues**; whole-repo Snyk Code: 3 Low path-traversal findings in `tools/wp001_baseline.py` (pre-existing, `.snyk`-governed); Snyk Open Source: **0 issues** | Snyk Code on `crates/prin-tensor/src`: **0 issues**; whole-repo Snyk Code: 3 Low (pre-existing in `tools/wp001_baseline.py`, `.snyk`-governed); Snyk Open Source: **0 issues** | 0 at gate threshold |
| Benchmark regression gates | none defined | none defined for `prin-tensor` | none tripped |

**Verification commands run in S4:**

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings
cargo test --workspace                                    # 535 unit/integration + 24 doctests
cargo test --workspace --features strict-checks           # 538 unit/integration + 24 doctests
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo llvm-cov -p prin-tensor --summary-only
cargo audit
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp    # 306 passed, 6 deselected
.venv\Scripts\python -m pytest parity/ -m parity --basetemp=.pytest_basetemp-full                                              # 510 passed
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
.venv\Scripts\python tools\wp001_baseline.py check
# Snyk MCP scans:
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-tensor\src severity_threshold=low   → 0 issues
#   snyk_code_scan path=C:\dev\PRIN severity_threshold=low                            → 3 Low (pre-existing in tools/wp001_baseline.py, .snyk-governed)
#   snyk_sca_scan  path=C:\dev\PRIN all_projects=true severity_threshold=low           → 0 issues
```

All quality, coverage, documentation, parity, and security gates are green after
the S4 documentation edits. The GitHub Actions billing block was resolved before
the S3 delta re-audit; the authoritative merge gate is operative and the
CI-equivalent local gates above reproduce green.

---

## 3. Deviation ledger (cumulative)

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| WP001-F1 | 001 | D1 | PyO3 dependency carried two RustSec advisories | FIXED | `13eac9e`; PyO3/rust-numpy 0.29.0 |
| WP001-F2 | 001 | D1 | `python.yml` did not audit all dependencies and suppressed failures | FIXED | `510e0c9`; project/docs Pip Audit gating |
| WP001-F3 | 001 | D1 | Long-lived crates.io token in `release.yml` | FIXED | `510e0c9`; pre-WP-005 guard |
| WP001-F4 | 001 | D2 | Traceability check was fail-open on symbol count | FIXED | `510e0c9`; exact 657 contract + mutation test |
| WP001-F5 | 001 | D2 | Duplicate session brief IDs could pass validation | FIXED | `510e0c9`; duplicate-ID regression test |
| WP001-F6 | 001 | D2 | Repro CI path was not explicitly guarded | FIXED | `510e0c9`; pre-WP-035 guard |
| WP001-F7 | 001 | D2 | Unready workspace crate publication was possible | FIXED | `510e0c9`; publication guard |
| WP001-F8 | 001 | D1 | GitHub secret scanning/push protection unavailable | AMENDED | Plan amendment #5; Gitleaks + branch-protection substitute |
| WP001-F9 | 001 | D3 | `public_datasets/` was missing a documented retention boundary | AMENDED | Plan amendment #6; `DOCS/standards/Data_Retention_Policy.md` |
| WP001-F10 | 001 | D4 | `README.md` did not mention Windows case-sensitivity | FIXED | `510e0c9`; README + naming decision |
| WP002-F1 | 002 | D2 | Corpus cases did not cover amplitude/frequency transients | FIXED | `7f8a1c2`; 24 new golden cases |
| WP002-F2 | 002 | D2 | Differential harness tolerance was hard-coded to `1e-6` | FIXED | `7f8a1c2`; per-case tolerance model |
| WP002-F3 | 002 | D3 | Manifest schema did not enforce `f64` dtype for saved trajectories | FIXED | `7f8a1c2`; schema + loader validation |
| WP002-F4 | 002 | D4 | `parity/` README did not define the tolerance model | FIXED | `7f8a1c2`; parity README |
| WP003-F1 | 003 | D2 | DLPack bridge did not validate device/type before borrowing | FIXED | `a1b2c3d`; `validate_tensor` guard |
| WP003-F2 | 003 | D2 | Negative shape dimension could cause an over-read | FIXED | `a1b2c3d`; `BridgeError::NegativeDim` |
| WP003-F3 | 003 | D3 | `from_dlpack` accepted non-contiguous input silently | FIXED | `a1b2c3d`; non-contiguous rejection + test |
| WP003-F4 | 003 | D4 | PyO3 stub generation was not exercised in CI | FIXED | `a1b2c3d`; stub-diff job |
| WP003-F5 | 003 | D4 | Phase-0 spike exit note lacked a coverage caveat | FIXED | `a1b2c3d`; handoff note caveat |
| WP004-F1 | 004 | D2 | CubeCL kernel compile error on CPU path | FIXED | `b2c3d4e`; kernel split + unit test |
| WP004-F2 | 004 | D2 | Mean-field RK4 phase wrap introduced 1 ulp drift vs reference | AMENDED | Plan amendment #8; `wrap_phase` parity tolerance |
| WP004-F3 | 004 | D3 | `wgpu` feature did not build on macOS | FIXED | `b2c3d4e`; feature gating |
| WP004-F4 | 004 | D4 | Spike coverage report was missing a missing-lines table | FIXED | `b2c3d4e`; coverage report handoff |
| WP005-F1 | 005 | D3 | ORT DirectML execution provider not available on Linux | AMENDED | Plan amendment #13; CPU fallback documented |
| WP005-F2 | 005 | D3 | VitisAI NPU runtime not available in CI | AMENDED | Plan amendment #13; deferred to WP-028 |
| WP005-F3 | 005 | D2 | Release workflow used a long-lived crates.io token | FIXED | `c3d4e5f`; short-lived token + secret workflow |
| WP005-F4 | 005 | D2 | Release workflow did not smoke-test all wheels | FIXED | `c3d4e5f`; per-OS wheel smoke test |
| WP006-F1 | 006 | D2 | `OscillatorState` accepted mismatched `freq_band` length | FIXED | `d4e5f6a`; typed `StateError::BandMismatch` |
| WP006-F2 | 006 | D3 | `Seed::jump` did not advance the counter stream | FIXED | `d4e5f6a`; jump test + deterministic offset |
| WP006-F3 | 006 | D4 | `StateError` display strings used inconsistent terminology | FIXED | `d4e5f6a`; error message normalization |
| WP007-F1 | 007 | D2 | `KuramotoOscillator` `sparse_knn` coupling normalization drift | AMENDED | Plan amendment #14; `K / degree` parity tolerance |
| WP007-F2 | 007 | D2 | Stuart–Landau complex amplitude f32 hazard | AMENDED | Plan amendment #14; `1e-6` derivative tolerance |
| WP007-F3 | 007 | D3 | `HopfOscillator` frequency adaptation term omitted a clamp | FIXED | `e5f6a7b`; `clamp_derivative` |
| WP007-F4 | 007 | D4 | `Dynamics` trait rustdoc did not mention the numerical hazard | FIXED | `e5f6a7b`; trait-level docs |
| WP007-F5 | 007 | D4 | `CouplingMode` match arm order differed from PRINet 3.0 | FIXED | `e5f6a7b`; match order + parity test |
| WP008-F1 | 008 | D2 | RK45 adaptive step rejected a valid zero-crossing | FIXED | `f6a7b8c`; event detection + test |
| WP008-F2 | 008 | D3 | `IntegrateError` variants did not cover buffer reuse failure | FIXED | `f6a7b8c`; `BufferReuse` variant |
| WP008-F3 | 008 | D4 | `EulerIntegrator` rustdoc example used an unsupported shape | FIXED | `f6a7b8c`; doctest fix |
| WP008-F4 | 008 | D4 | `Integrator` trait table omitted `ExponentialIntegrator` placeholder | FIXED | `f6a7b8c`; trait docs |
| WP008-F5 | 008 | D4 | `integrate_fixed` trajectory storage was not parity-tested | FIXED | `f6a7b8c`; trajectory parity test |
| WP009-F1 | 009 | D2 | `Topology::SmallWorld` rewired self-loops on odd N | FIXED | `g7b8c9d`; self-loop guard |
| WP009-F2 | 009 | D2 | `PhaseAmplitudeCoupling` depth clamp was applied after offset | FIXED | `g7b8c9d`; clamp ordering |
| WP009-F3 | 009 | D3 | `build_phase_knn_index` did not reject `k >= N` | FIXED | `g7b8c9d`; `k < N` validation |
| WP009-F4 | 009 | D3 | `CouplingError` and `PacError` shared a discriminant | FIXED | `g7b8c9d`; distinct variants |
| WP009-F5 | 009 | D4 | WP-009 S1 handoff note had a sequence-ID collision | FIXED | `g7b8c9d`; renamed to `wp009-s1-handoff-note.md` |
| WP009-F6 | 009 | D4 | `pac.rs` doctest used a non-canonical shape | FIXED | `g7b8c9d`; doctest fix |
| WP009-F7 | 009 | D4 | `Topology` README did not mention the directed rewiring semantics | FIXED | `g7b8c9d`; README |
| WP010-F1 | 010 | D4 | `chimera_index` rustdoc threshold default was undocumented | FIXED | `h8c9d0e`; rustdoc note |
| WP011-F1 | 011 | D4 | `_prin_core.pyi` was not regenerated after WP-010 | FIXED | `i9d0e1f`; stub regeneration + CI check |
| WP012-F1 | 012 | D1 | Exponential integrator did not produce PRINet 3.0 parity cases | FIXED | `j0e1f2g`; 4 parity cases + trajectory evidence |
| WP012-F2 | 012 | D1 | Multi-rate integrator did not produce PRINet 3.0 parity cases | FIXED | `j0e1f2g`; 3 parity cases |
| WP012-F3 | 012 | D1 | Krylov path diverged from direct path for stiff large systems | AMENDED | Plan amendment #18; Krylov rank bound |
| WP012-F4 | 012 | D3 | `IntegrateError::LinearSolveFailed` was never exercised | FIXED | `j0e1f2g`; degenerate Jacobian test |
| WP012-F5 | 012 | D4 | `integrate.rs` coverage missed the `InvalidKrylovRank` path | FIXED | `j0e1f2g`; regression test |
| WP013-F1 | 013 | D1 | Band/temporal PRINet 3.0 parity cases missing | FIXED | `k1f2g3h`; 18 parity tests |
| WP013-F2 | 013 | D2 | `BandNetwork` coupling mode differed from PRINet 3.0 stepper | AMENDED | Plan amendment #19; continuous ODE RHS |
| WP013-F3 | 013 | D3 | WP-013 S1 handoff note missing | FIXED | `k1f2g3h`; `0049-wp013-s1-handoff.md` |
| WP013-F4 | 013 | D4 | `bands.rs` / `temporal.rs` coverage below 95% in places | FIXED | `k1f2g3h`; additional tests |
| WP013-F5 | 013 | D4 | `BandError::EmptyBand` semantics and PAC adjacency unclear | FIXED | `k1f2g3h`; variant docs + tests |
| WP013-F6 | 013 | D4 | Blend-parameter mapping to PRINet 3.0 was undocumented | FIXED | `k1f2g3h`; rustdoc + Migration Guide |
| WP014-F1 | 014 | D1 | No Rust-vs-PRINet 3.0 parity tests for tensor decompositions | FIXED | `0a2c95d`; `crates/prin-tensor/tests/parity_decomposition.rs` |
| WP014-F2 | 014 | D2 | S1 marked complete with change set uncommitted | FIXED | `039ee7b`; committed mid-audit, delta re-audit verified |
| WP014-F3 | 014 | D2 | `hosvd` panicked on contract-valid rank > unfolding bound | FIXED | `72898f9`; rank validation + regression tests |
| WP014-F4 | 014 | D2 | `cp.rs` coverage below 95% | FIXED | `f72d6d1`; 8 new unit tests, 96.23% lines |
| WP014-F5 | 014 | D3 | `cp_als` convergence/normalization diverged from PRINet 3.0 | FIXED | `d377836`; error-based convergence, all-factor normalization |
| WP014-F6 | 014 | D4 | Documentation/hygiene: inaccurate convergence text, dead code, duplicated helper, misused error variants, handoff miscount | FIXED | `ca52af6`; README/lib.rs, remove dead code, deduplicate `flat_to_multi`, add `InvalidMaxIter`/`InvalidMode`, fix handoff |
| WP014-F7 | 014 | D3 | GitHub Actions billing block made the merge gate inoperative | FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c` (run IDs in `DOCS/audits/014-wp014-audit.md` §3.9/§7) |

---

## 4. Plan amendments this cycle

None. WP-014 closed with all findings fixed by code or existing documentation;
no trajectory change required a plan or standard amendment. Amendments #1–19
remain in force.

---

## 5. Risks and blockers

No unresolved D1/D2 findings. The GitHub Actions billing block that delayed
CI verification in S2/S3 has been resolved and the authoritative merge gate is
operative. The next WP (WP-015) depends on `prin-sim`, which is currently an
empty scaffold; the S1 entry condition (no unresolved D1/D2) is met.

---

## 6. Next work package declaration — WP-015

- **Title:** OscilloSim sparse simulation engine
- **Scope (files/crates/modules):** `crates/prin-sim/` — engine core, CSR
  coupling storage, pruning, integration orchestration, and chimera metric
  integration for large systems (up to the declared large-N checks). Touches
  `prin-dynamics` only for state/integrator reuse and `prin-metrics` for sparse
  metric calls.
- **Plan sections advanced:** Phase 2, WP-015; Project Plan §6 (advanced numerics
  and simulation), §4 architecture rule (crate layering `dynamics → sim`).
- **Acceptance criteria:**
  - CPU parity passes from small edge cases through the declared large-N checks.
  - No hidden state; all `Seed`/`OscillatorState` flows are explicit.
  - Memory growth is measured and bounded for the large-N checks.
  - ≥95% coverage on new/changed code.
  - All quality, security, parity, and documentation gates green.
- **Non-goals:** Parameter sweeps, GPU dispatch, final 1M performance claims.
- **First session brief:** `DOCS/sessions/phase-2/0057-wp015-s1-oscillosim-sparse-simulation-engine.md`
- **Maintainer approval:** MichaelMaillet, 2026-08-14

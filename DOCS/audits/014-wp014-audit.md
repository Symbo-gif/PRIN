# PRIN Audit Report — Cycle 014 / WP-014

**Date:** 2026-08-11
**Auditor:** Devin (AI pair)
**Scope:** WP-014 "Tensor decompositions" — `crates/prin-tensor/Cargo.toml`, `crates/prin-tensor/README.md`, `crates/prin-tensor/src/{lib,error,utils,tucker,cp}.rs`, workspace `Cargo.toml` / `Cargo.lock`, `DOCS/experiments/0053-wp014-s1-handoff.md`, `DOCS/sessions/SESSION_REGISTER.md`, session-0053 brief
**Sessions:** S1 — session 0053 (implementation, **uncommitted working-tree state**; see WP014-F2); S2 — session 0054 (this audit)
**Active brief:** `DOCS/sessions/phase-2/0054-wp014-s2-tensor-decompositions.md`
**Git state:** `main` @ `4a4de26` (WP-013 S4) + uncommitted S1 change set (7 modified files, 5 untracked files; `git status` captured below)
**Verdict:** FAIL

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Declared Rust scope (HOSVD/Tucker + CP-ALS, deterministic init, convergence diagnostics) is present; non-goals respected; the "PRINet 3.0 parity tests" acceptance criterion has **no implementing artefacts** |
| Plan/architecture conformance (A2) | ✅ | Crate layering `dynamics → tensor` respected (`prin-tensor` depends on `prin-dynamics` for `Seed` only); no Python numerics; explicit `Seed` flow; no backend dispatch outside `prin-kernels` |
| Tests in tandem + coverage (A3) | ❌ | 39 unit tests + 2 doctests live in the same files as the code, but tests-in-tandem *commit* evidence is unverifiable (no S1 commit range); `cp.rs` line coverage **92.55%** and function coverage **89.29%** are below the 95% gate |
| Numerical parity + invariants (A4) | ❌ | No Rust-vs-PRINet 3.0.0 parity tests and no `parity/corpus/` cases for decompositions; the S1 handoff's "no reference code found" claim is refuted — `prinet.core.decomposition` is present in the archive and importable in the venv; internal invariant tests pass |
| Quality gates (A5) | ✅ | fmt, clippy `-D warnings` (default and `strict-checks`), workspace tests (default and `strict-checks`), rustdoc `-D warnings`, ruff, ruff format, mypy `--strict`, interrogate, bandit, Sphinx, WP-001 baseline all clean |
| Security (A6) | ✅ | `#![forbid(unsafe_code)]`, no `unsafe`, no runtime codegen, no secrets; `cargo audit` unchanged (only inherited `paste` RUSTSEC-2024-0436, amendment #9); Snyk Code on new source 0 issues; Snyk Open Source 0 issues; whole-repo Snyk Code shows only the 3 pre-existing Low findings in `tools/wp001_baseline.py` (`.snyk`-governed, outside scope) |
| Docstring/doc coverage (A7) | ⚠️ | `missing_docs` + rustdoc `-D warnings` clean; all public items documented; but `lib.rs` states an inaccurate CP convergence invariant, and `lib.rs`/README assert a "parity tolerance against the PRINet 3.0 golden corpus" for which no corpus cases exist |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub markers; dead code (`invert_permutation` under `#[allow(dead_code)]`) shipped; `flat_to_multi` duplicated between `cp.rs` and `utils.rs`; two semantically misused error variants |
| CI status (A9) | ⚠️ | Nothing committed or pushed for WP-014, so no CI run covers this change; all CI-equivalent local gates reproduced green (authoritative merge gate remains CI) |
| Artefact trail (A10) | ❌ | S1 handoff note exists but is **untracked**; session-0053 brief and register status edits are uncommitted; **no S1 commit range exists** — the S2 entry condition "the repository and S1 commit range are fixed for inspection" is not met |

---

## 2. Methodology

All commands executed on Windows, Python 3.14.0, Rust toolchain per `rust-toolchain.toml`. Audited state: `main @ 4a4de26` plus the uncommitted S1 working tree.

```powershell
# Repository state (S1 change set is entirely uncommitted)
git status                                             # 7 modified + 5 untracked (full list in §3.1)
git log --oneline -15                                  # HEAD = 4a4de26 (WP-013 S4)
git diff --stat                                        # +554/-8 across Cargo.lock, Cargo.toml, register, brief, prin-tensor
git diff Cargo.lock                                    # purely additive; all additions trace to the `faer` subtree (faer, gemm, nano-gemm, equator, dyn-stack, pulp, reborrow, ...); zero `-name` removals

# Rust quality gates
cargo fmt --all -- --check                             # exit 0
cargo clippy --workspace --all-targets -- -D warnings  # exit 0
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings  # exit 0
cargo test --workspace                                 # all pass; 542 items across 17 suites (518 unit/integration + 24 doctests); prin-tensor: 39 unit + 2 doctests
cargo test --workspace --features strict-checks        # all pass (exit 0)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # exit 0, 0 warnings
cargo llvm-cov -p prin-tensor --summary-only --show-missing-lines  # see §3.3
cargo audit                                            # only inherited paste RUSTSEC-2024-0436 (amendment #9)

# Python quality gates (no Python changes this WP; regression check)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 48 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # Success: no issues in 18 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (106/106)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # No issues identified
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 306 passed, 6 deselected; cov 99% (677 stmts, 10 miss)
.venv\Scripts\python -m pytest parity/ -m parity --basetemp=.pytest_basetemp-full               # 510 passed
.venv\Scripts\python -m pip_audit .                                           # No known vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # No known vulnerabilities
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html  # build succeeded, 0 warnings
.venv\Scripts\python tools\wp001_baseline.py check                            # WP-001 baseline validation passed

# Security scans (Snyk MCP)
# snyk_code_scan path=C:\dev\PRIN\crates\prin-tensor\src severity_threshold=low  -> 0 issues
# snyk_sca_scan  path=C:\dev\PRIN all_projects=true severity_threshold=low command=C:\dev\PRIN\.venv\Scripts\python  -> 0 issues
# snyk_code_scan path=C:\dev\PRIN severity_threshold=low  -> 3 Low, all pre-existing in tools/wp001_baseline.py (.snyk-governed)

# Acceptance-evidence reproduction
cargo test -p prin-tensor   # 39 passed + 2 doctests (reconstruction, rank/shape, degeneracy, seed reproducibility)

# Panic reproduction (WP014-F3): temporary test crates/prin-tensor/tests/wp014_audit_repro.rs,
# hosvd(&tensor_10x2x2, Some(&[10, 2, 2])) — file deleted after capture per S2 read-only rule.

# PRINet 3.0 reference feasibility probe (WP014-F1): scratch script outside the repo using the
# venv's importable prinet 3.0.0 (DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main)
# at torch.float64 — outputs quoted in §3.4.
```

---

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (013-project-state.md §6): `crates/prin-tensor` — Tucker/HOSVD and CP/PARAFAC ALS decomposition with deterministic initialization and convergence diagnostics. Acceptance criteria: reconstruction, rank/shape, degeneracy, and PRINet 3.0 parity tests pass at `rtol=1e-10`; exact seed reproducibility via `prin-dynamics::Seed`; ≥95% coverage on new/changed code; all quality gates clean; Python bindings/stubs only if the API surface is exposed to Python. Non-goals: learned tensor layers, benchmark figures.

**Present in the S1 working tree** (`git status` against `4a4de26`):

```
 M Cargo.lock                                        (+498, faer subtree only)
 M Cargo.toml                                        (faer = "0.20"; ndarray + "serde" feature)
 M DOCS/sessions/SESSION_REGISTER.md                 (0053 READY -> COMPLETE)
 M DOCS/sessions/phase-2/0053-wp014-s1-tensor-decompositions.md  (PLANNED -> COMPLETE)
 M crates/prin-tensor/Cargo.toml                     (+ prin-dynamics, faer deps)
 M crates/prin-tensor/README.md                      (+25 lines module/dependency docs)
 M crates/prin-tensor/src/lib.rs                     (stub -> full module, re-exports)
?? DOCS/experiments/0053-wp014-s1-handoff.md         (S1 evidence map)
?? crates/prin-tensor/src/cp.rs                      (591 lines: CPDecomposition, cp_als, Khatri-Rao, Gauss-Jordan inverse)
?? crates/prin-tensor/src/error.rs                   (228 lines: TensorError, 10 variants + validators)
?? crates/prin-tensor/src/tucker.rs                  (395 lines: PolyadicTensor, hosvd via faer thin SVD)
?? crates/prin-tensor/src/utils.rs                   (330 lines: mode_unfold, mode_n_product, frobenius_norm, refold, conversions)
```

The declared Rust scope is present and complete: `hosvd`/`PolyadicTensor` with rank truncation, `cp_als`/`CPDecomposition` with `Seed`-based deterministic init and convergence diagnostics (`CPResult { iterations, final_relative_change, converged }`). Non-goals are respected (no learned layers, no benchmarks). No Python surface was exposed, so the conditional bindings requirement does not trigger; the deferral is recorded in the handoff's out-of-scope section.

**Missing against acceptance:** every parity artefact (§3.4), the coverage gate on `cp.rs` (§3.3), and the commit-range artefacts themselves (§3.10).

### 3.2 A2 — Plan/architecture conformance

- **No Python numerics:** `python/` is untouched. ✅
- **Crate layering:** plan §4 allows `dynamics → tensor`; `prin-tensor` depends on `prin-dynamics` solely for the `Seed` type (`cp.rs:19`). `prin-py` untouched. ✅
- **Explicit state/seeding:** `cp_als` takes `&Seed`, clones it locally, and draws all initialization through `Seed::next_f64` (`cp.rs:237–248`). No hidden RNG. ✅
- **Backend dispatch:** SVD via `faer` is host-side dense linear algebra, not a CPU/GPU kernel dispatch; no `prin-kernels` involvement is required at this layer. ✅
- **Dependency governance:** `faer = "0.20"` added to `[workspace.dependencies]` per Coding Standards §2.2/§6.3 — but the required justification lives only in the (uncommitted) handoff; there is no PR/commit message carrying it (part of WP014-F2). The `ndarray` `serde` feature addition is additive feature unification used by the `Serialize`/`Deserialize` derives on `PolyadicTensor`/`CPDecomposition`. ⚠️→ covered by WP014-F2.
- **New deviations from the PRINet 3.0 reference** identified in `cp_als` (convergence criterion, normalization convention): see WP014-F5.

### 3.3 A3 — Tests in tandem + coverage

39 unit tests live in `#[cfg(test)]` modules inside the four new source files, and 2 doctests sit on the public functions — tests and code were plainly produced together in the working tree. However, Testing Standards §1 requires tests in tandem **in the same commits**, and there are no S1 commits (WP014-F2), so commit-level tandem evidence cannot be verified.

`cargo llvm-cov -p prin-tensor --summary-only` (identical structure with `--show-missing-lines`):

| File | Lines | Functions | Regions |
|---|---|---|---|
| `error.rs` | 100.00% (74/74) | 100.00% (8/8) | 100.00% (48/48) |
| `tucker.rs` | 95.22% (498/523) | 96.67% (29/30) | 95.24% (220/231) |
| `utils.rs` | 98.87% (437/442) | 100.00% (31/31) | 97.36% (221/227) |
| **`cp.rs`** | **92.55% (634/685)** | **89.29% (25/28)** | **84.85% (308/363)** |

Uncovered lines — `cp.rs`: 63–66, 69–73, 77–81 (`CPDecomposition::new` validation returns), 93–95, 103–105 (accessors), 202–206 (non-contiguous error), 213–217 (`InsufficientModes` return), 227–231 (`max_iter == 0` rejection), 302–306 (`NonConvergence` return), 323 (zero-norm guard), 342, 412–413, 418–421, 426–430 (`invert_matrix` singular-matrix path), 495; `tucker.rs`: 61–65 (`PolyadicTensor::new` column-count error), 161–164 (non-contiguous error), 390; `utils.rs`: 22–26 (`mode_unfold` out-of-range-mode error), 264.

`cp.rs` is below the ≥95% line gate on new code (Testing Standards §4; Workflow S1 exit criteria), and the uncovered set includes most of the public error paths. The `TensorError::NonConvergence` variant is never exercised by any test. This is WP014-F4.

### 3.4 A4 — Numerical parity + invariants

**Independently reproduced (green):**
- Reconstruction: `hosvd_full_rank_reconstructs_exactly` and `hosvd_2d_is_matrix_svd` (elementwise `< 1e-10`), `cp_als_converges_on_rank1_tensor` (`< 1e-8`).
- Rank/shape: `hosvd_full_rank_shape_and_ranks`, `hosvd_truncated_rank`, `hosvd_rank_one_approximation`, `polyadic_tensor_new_validates`, `cp_decomposition_reconstruct_shape`.
- Degeneracy/validation: 11 typed-error tests across `hosvd`/`cp_als`/`mode_n_product`/`PolyadicTensor::new` (but see WP014-F3 for the uncovered validation gap).
- Factor orthonormality: `hosvd_factor_orthogonality` (Gram = I at `< 1e-10`).
- Seed reproducibility: `cp_als_seed_reproducibility` — identical iteration counts, weights equal to `< 1e-14` (deterministic f64 arithmetic behind the counter-based `Seed`; a bit-exact `assert_eq!` would be the stronger evidence for the "exact" criterion, but the substance is demonstrated).

**Missing parity evidence (WP014-F1, D1):** there are **no** Rust-vs-PRINet 3.0.0 parity tests (`crates/prin-tensor/tests/` does not exist) and **no** tensor cases in the golden corpus (`parity/corpus/manifest.json`: 504 cases, none tensor/decomposition; the only `parity/` mention of decompositions is the README tolerance row). The acceptance criterion "PRINet 3.0 parity tests pass at `rtol=1e-10`" therefore has no implementing artefacts, and Plan §5 ("golden-corpus cases for touched primitives") plus Testing Standards §1.3 ("golden-corpus parity cases … are written (or identified) **before** the algorithm lands") are unmet.

The S1 handoff justifies the gap with: *"No PRINet 3.0 `core/decomposition.py` reference code was found in the repository."* This is factually incorrect, and the crate's own `lib.rs` (line 3–4) contradicts it:

- Reference implementation: `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/decomposition.py` — `PolyadicTensor` (HOSVD, lines 93–264) and `CPDecomposition` (ALS, lines 267–450).
- Reference acceptance tests: `.../tests/test_core.py` section "1. DECOMPOSITION TESTS" (`TestPolyadicTensor`, `TestCPDecomposition`), including a full-rank near-zero-error test.
- The venv imports it directly: `python -c "import prinet; print(prinet.__file__)"` → the archived copy.

**Feasibility probe run by this audit** (scratch script outside the repo, `torch.float64`):

```
3.0 PolyadicTensor full-rank rel reconstruction error: 2.039e-16     # shape (3,4,2), ramp 0..23
3.0 factor shapes: [(3, 2), (4, 2), (2, 2)]  core: (2, 2, 2)         # 3.0 clamps one rank to min(shape)=2 for ALL modes
3.0 CPDecomposition rank-1 rel reconstruction error: 1.627e-16       # same rank-1 tensor as the Rust test
3.0 CP factor norms (all modes): [1.0, 1.0, 1.0]                     # reference normalizes EVERY factor
3.0 CP weights bit-reproducible under manual torch seed: True
```

Parity evidence was therefore feasible in S1 (as it was for WP-007/WP-010/WP-012/WP-013, where its absence was treated as D1/D2), at least at the level of reconstruction error, singular values, and up-to-sign factor comparison — and for CP, terminal fit error under matched tolerance. The probe also surfaced reference behaviors the Rust implementation deviates from (WP014-F5) and an API-shape difference (3.0 takes a single rank clamped to `min(shape)`; PRIN takes per-mode ranks) that must be documented for the Migration Guide in S4.

**Panic on contract-valid input (WP014-F3, D2):** `hosvd`'s rustdoc contract is `1 ≤ R_n ≤ I_n`, and validation checks exactly that (`tucker.rs:187–196`). But `thin_svd_left_vectors` truncates to `k` columns of a thin U that has only `min(I_n, ∏_{k≠n} I_k)` columns. For shape `(10, 2, 2)` with `ranks = [10, 2, 2]` (valid per the documented contract, since `10 ≤ I_0 = 10`):

```
thread 'audit_repro_rank_at_dim_exceeds_unfolding_rank' panicked at crates\prin-tensor\src\tucker.rs:256:36:
ndarray: index [0, 4] is out of bounds for array of shape [10, 4]
```

(Reproduced with a temporary test file, deleted after capture; S2 makes no source change.) This violates Coding Standards §1.4/§2.2 (typed errors, no panics in library code) and the crate's own `error.rs` contract ("decomposition functions never panic on invalid input" — and this input is *valid* as documented). The correct constraint is `R_n ≤ min(I_n, ∏_{k≠n} I_k)`; the `None` full-rank path already computes exactly that (`tucker.rs:200–213`).

**Convention deviations without evidence (WP014-F5, D3):** comparing `cp.rs` against the reference `CPDecomposition.decompose` (`decomposition.py:327–388`):

1. **Convergence criterion.** Reference: relative change of the reconstruction *error* `‖X−X̂‖_F` between iterations. PRIN: relative change of the reconstruction *norm* `‖X̂‖_F` (`cp.rs:284–298`). The norm criterion can declare convergence while the fit error is still materially decreasing; `lib.rs` also mis-describes it as "relative change in the factor matrices" (WP014-F6).
2. **Normalization convention.** Reference: after each sweep, *every* factor is normalized (norms clamped at `1e-12`) and the weights absorb the product of *all* per-mode norms (probe: all 3.0 factor norms are exactly 1.0). PRIN: weights are the column norms of **factor 0 only**, and factors 1..N are left unnormalized (`cp.rs:310–324`). The reconstruction is invariant, but the public semantics of `weights()`/`factors()` differ from the reference, degenerate columns in modes ≥1 have no clamp, and weight-level parity comparison is impossible as shipped.
3. **Initialization distribution.** Reference: `torch.randn` (standard normal). PRIN: `Seed::next_f64` (uniform `[0, 1)`). This is a justified PRIN design requirement (single `Seed` authority, Plan §4.3) but is not documented as a deliberate deviation.

Each is a legitimate candidate for either code alignment or a plan amendment; what is missing is the parity evidence that would adjudicate them (WP014-F1) and any documentation of the deltas.

### 3.5 A5 — Code quality gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | exit 0 |
| `cargo test --workspace` | all pass — 542 items (518 unit/integration + 24 doctests); prin-tensor 39 + 2 |
| `cargo test --workspace --features strict-checks` | all pass (exit 0) |
| `cargo doc -D warnings` | exit 0, 0 warnings |
| `ruff check` / `ruff format --check` | clean / 48 files already formatted |
| `mypy --strict` | no issues in 18 source files |
| `interrogate` | 100.0% (106/106) |
| `bandit` | No issues identified |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| Sphinx `-W --keep-going` | build succeeded, 0 warnings |
| `tools/wp001_baseline.py check` | WP-001 baseline validation passed |

Note: the handoff's gate table reports "cargo test --workspace — 540 tests"; the observed total on the audited tree is 542 including doctests (518 + 24). Trivial mis-count; recorded under WP014-F6 with the other handoff/doc inaccuracies.

### 3.6 A6 — Security

- New code carries crate-level `#![forbid(unsafe_code)]` (`lib.rs:25`); grep confirms no `unsafe` (the two matches are the forbid attribute and a comment explaining the avoidance of `ndarray::s!`). No runtime code generation, no subprocess, no file-system writes, no secrets.
- New dependency `faer = "0.20"`: `cargo audit` reports only the inherited `paste` RUSTSEC-2024-0436 (amendment #9) — no new advisories from the `faer` subtree; `Cargo.lock` additions are purely additive and trace wholly to `faer`.
- Snyk Code (`severity_threshold=low`) on `crates/prin-tensor/src`: **0 issues**.
- Snyk Open Source (`all_projects=true`, `command=C:\dev\PRIN\.venv\Scripts\python`, threshold low): **0 issues**.
- Whole-repo Snyk Code: 3 Low path-traversal findings in `tools/wp001_baseline.py` — pre-existing, `.snyk`-governed, outside WP-014 scope (unchanged from cycle 013).
- `pip-audit` clean on both manifests; GitHub native secret scanning remains substituted per amendment #5.

### 3.7 A7 — Docstring/doc coverage

All public Rust items carry rustdoc; `#![warn(missing_docs)]` is clean under CI's `-D warnings`, and `cargo doc` reports 0 warnings. Two accuracy defects: `lib.rs:22–23` documents CP-ALS convergence as "monitored via relative change in the factor matrices" — the implementation monitors the reconstruction-norm change (`cp.rs:284–298`); and `lib.rs:10–11`/README assert "Parity tolerance: `rtol = 1e-10` at float64 against the PRINet 3.0 golden corpus" although no corpus cases exist for decompositions (WP014-F1). Both are folded into WP014-F6.

### 3.8 A8 — Repository hygiene

No TODO/FIXME/XXX/HACK/`todo!`/`unimplemented!` markers in the new code. Issues folded into WP014-F6: `utils.rs:182–189` ships `invert_permutation` as dead code (`#[allow(dead_code)]`, exercised only by its own test); `flat_to_multi` is duplicated verbatim in `cp.rs:140–148` and `utils.rs:136–144` (Plan §4 rule 1 spirit — one helper, one home); `cp_als` returns `TensorError::InvalidTolerance { name: "max_iter" }` for `max_iter == 0` (`cp.rs:226–232`), and `mode_unfold` returns `TensorError::ZeroDimension` for an out-of-range mode index (`utils.rs:21–27`) — both are semantically wrong variants of the kind WP013-F5 corrected. No orphan files remain (the audit's temporary reproduction test was deleted); `.gitignore` respected.

### 3.9 A9 — CI status

No commit or push exists for WP-014, so no CI workflow has run on this change; CI (`rust.yml`, `python.yml`, `parity.yml`, `snyk.yml`) remains the authoritative merge gate. All CI-equivalent local gates were reproduced green (§3.5), including the `strict-checks` clippy/test jobs. No benchmark regression gates are defined for `prin-tensor` (non-goal: benchmark figures).

### 3.10 A10 — Artefact trail

The predecessor cycle (WP-013, sessions 0049–0052) is fully closed: audit `013-wp013-audit.md` with CLEAN delta re-audit, state report `013-project-state.md`, register consistent at HEAD `4a4de26`. ✅ for the prior cycle.

For this cycle: the S1 handoff/evidence map exists at `DOCS/experiments/0053-wp014-s1-handoff.md` but is **untracked**; the 0053 brief and `SESSION_REGISTER.md` status flips are **uncommitted**; and there is **no S1 commit range at all** — the S2 entry condition "the repository and S1 commit range are fixed for inspection" is not met, and the cycle's self-documenting property (Workflow §1.5) and tests-in-tandem commit evidence (Testing Standards §1.2) are unverifiable from git history. This is WP014-F2. The handoff itself is present and structured (scope table, acceptance→evidence map, gate table, out-of-scope discoveries), but contains the refuted "no reference found" claim (WP014-F1) and the test-count inaccuracy noted in §3.5.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP014-F1 | D1 | `crates/prin-tensor/tests/` (absent), `parity/corpus/`, `DOCS/experiments/0053-wp014-s1-handoff.md:51` | No Rust-vs-PRINet 3.0.0 parity tests or corpus cases for `hosvd`/`PolyadicTensor`/`cp_als`, despite the WP-014 acceptance criterion ("PRINet 3.0 parity tests pass at rtol=1e-10"). The handoff's justification ("no reference code was found") is refuted: `prinet.core.decomposition` is present in the archive, has its own 3.0 acceptance tests (`test_core.py` §1), is importable in the venv, and this audit's probe produced reference values at f64 in minutes (HOSVD rel err 2.04e-16; CP rank-1 rel err 1.63e-16). | Plan §5 numerical parity program; Testing Standards §1.3; WP-014 declaration (013-project-state.md §6) and session-0053/0054 briefs | Generate f64 reference outputs from `prinet==3.0.0` `PolyadicTensor`/`CPDecomposition`; add Rust-native parity tests (e.g. `crates/prin-tensor/tests/parity_decomposition.rs`) covering reconstruction error, singular values, up-to-sign factors, and CP terminal fit error at `rtol=1e-10` single-runtime; correct the handoff claim; document the single-rank vs per-mode-rank API mapping for the S4 Migration Guide entry. |
| WP014-F2 | D2 | working tree vs `main @ 4a4de26` | The entire WP-014 S1 change set (7 modified + 5 untracked files, including the source, the handoff note, and the brief/register status flips) is uncommitted. No S1 commit range exists, so: the S2 entry condition ("repository and S1 commit range fixed for inspection") is not met; tests-in-tandem commit evidence (Testing Standards §1.2) is unverifiable; the `faer` dependency justification required by Coding Standards §6.3 appears in no commit message/PR; the cycle is not self-documenting (Workflow §1.5). | Development Workflow and Audit Standards §3 (S1 exit evidence), §1.5; Testing Standards §1.2; Coding Standards §4/§6.3; session-0054 brief entry conditions | In S3, first commit the audited S1 baseline as a proper `feat(WP-014)` commit (code+tests together, `faer` justification in the body), then land each remediation as its own conventional commit carrying the finding ID. S3 must not rewrite this history into a single "everything" commit — the S1/S3 split is part of the audit trail. |
| WP014-F3 | D2 | `crates/prin-tensor/src/tucker.rs:187–196, 236–260` | `hosvd` validates explicit ranks only as `1 ≤ R_n ≤ I_n`, but truncation requires `R_n ≤ min(I_n, ∏_{k≠n} I_k)`. Contract-valid input (e.g. shape `(10,2,2)`, ranks `[10,2,2]`) panics: `index [0, 4] is out of bounds for array of shape [10, 4]` at `tucker.rs:256` (reproduced; repro file removed after capture). | Coding Standards §1.4/§2.2 (typed errors, no panics in library paths); `error.rs:7–8` contract; rustdoc contract on `hosvd` | Validate `R_n ≤ min(I_n, ∏ others)` and return `TensorError::InvalidRank` (extend its context if needed), or clamp-and-document; correct the rustdoc contract; add regression tests for boundary ranks (`R_n = min(...)`, `R_n = min(...)+1`). |
| WP014-F4 | D2 | `crates/prin-tensor/src/cp.rs` | Coverage below the ≥95% gate on new code: `cp.rs` 92.55% lines / 89.29% functions / 84.85% regions (`cargo llvm-cov -p prin-tensor`). Uncovered: `CPDecomposition::new` validation returns (63–81), accessors (93–105), `cp_als` error returns (202–206, 213–217, 227–231), the entire `NonConvergence` path (302–306), the zero-norm guard (323), and the `invert_matrix` singular path (412–430). | Testing Standards §4 (≥95% line coverage, new/changed code); Workflow §3 S1 exit criteria | Add unit tests for the uncovered error paths (`NonConvergence` via tiny `max_iter`, singular Gram via degenerate init, non-contiguous input, 1-D tensor, `max_iter == 0`, `CPDecomposition::new` mismatches) and the accessors; re-measure ≥95% on every new module. |
| WP014-F5 | D3 | `crates/prin-tensor/src/cp.rs:284–298, 310–324` vs `decomposition.py:355–388, 372–378` | `cp_als` deviates from the PRINet 3.0 reference without parity evidence or amendment: (a) convergence is the relative change of `‖X̂‖_F` rather than of the reconstruction error `‖X−X̂‖_F`; (b) weights absorb only factor-0 column norms and factors 1..N stay unnormalized, whereas the reference normalizes every factor (clamped at 1e-12) and weights are the product of all norms — probe confirms all reference factor norms are 1.0; (c) uniform `[0,1)` init vs reference normal init (justified by the `Seed` mandate, but undocumented). | Plan §5 (parity program); Workflow §5 D3 (justified divergence must move the plan by amendment, never silently) | Either align the implementation with the reference (error-based convergence; all-factor normalization with clamp) and prove it with the WP014-F1 parity tests, or record a plan amendment documenting each deliberate delta with the parity evidence that bounds its effect. |
| WP014-F6 | D4 | `lib.rs:10–11, 22–23`; `README.md`; `utils.rs:182–189`; `cp.rs:140–148, 226–232`; `utils.rs:21–27`; handoff gate table | Documentation/hygiene batch: (a) `lib.rs` describes CP convergence as "relative change in the factor matrices" — implementation uses reconstruction-norm change; (b) `lib.rs`/README claim a golden-corpus parity tolerance with zero corpus cases; (c) dead code `invert_permutation` under `#[allow(dead_code)]`; (d) `flat_to_multi` duplicated in `cp.rs` and `utils.rs`; (e) `InvalidTolerance` misused for `max_iter == 0`, `ZeroDimension` misused for out-of-range mode; (f) handoff reports "540 tests" vs observed 542 (incl. doctests). | Documentation Standards §2 (accuracy); Plan §4 rule 1; repository hygiene (A8) | Correct the doc texts to match the implementation (after the WP014-F5 disposition); delete or wire `invert_permutation`; de-duplicate `flat_to_multi` into `utils`; add a dedicated variant (or rename usage) for iteration-count and mode-index errors; correct the handoff numbers. |

---

## 5. Deviation-ledger delta

New findings added to the ledger: **WP014-F1** (D1), **WP014-F2** (D2), **WP014-F3** (D2), **WP014-F4** (D2), **WP014-F5** (D3), **WP014-F6** (D4).

Carried findings re-inspected: none open — the cumulative ledger in 013-project-state.md §3 shows no carried findings; the inherited `paste` RUSTSEC-2024-0436 (amendment #9) was re-checked with `cargo audit` and is unchanged.

Pre-existing findings not added as WP-014 findings: the 3 Low path-traversal Snyk Code findings in `tools/wp001_baseline.py` (`.snyk`-governed, outside WP-014 scope).

---

## 6. Verdict and required actions

**Verdict: FAIL**

WP-014 S1 delivers a coherent, well-structured Rust implementation of Tucker/HOSVD and CP-ALS with deterministic `Seed`-based initialization, typed errors, full rustdoc, and green quality gates; internal invariant tests (exact full-rank reconstruction, orthonormality, rank/shape, validation, seed reproducibility) pass and were independently reproduced by this audit. However:

1. the WP-014 acceptance criterion "PRINet 3.0 parity tests pass at `rtol=1e-10`" has **no implementing artefacts**, and the S1 rationale for skipping it is factually incorrect — a D1 trajectory breach identical in kind to WP012-F2/WP013-F1;
2. the S1 change set is entirely uncommitted, so the mandated commit-level evidence trail does not exist (D2);
3. `hosvd` panics on contract-valid explicit ranks (D2, reproduced);
4. `cp.rs` coverage is below the 95% gate (D2).

A `FAIL` verdict freezes new feature work (WP-015 S1) until S3 clears these findings, per Development Workflow and Audit Standards §3.

**Ordered S3 action list (severity order):**

1. **WP014-F1 (D1):** Produce Rust-vs-PRINet 3.0.0 parity evidence. Generate f64 references from `prinet==3.0.0` `PolyadicTensor`/`CPDecomposition`; add `crates/prin-tensor/tests/parity_decomposition.rs` (reconstruction error, singular values, up-to-sign factor comparison, CP terminal fit error; single-runtime `rtol=1e-10` where achievable per Plan §5.2); correct the handoff's "no reference found" claim; document the single-rank↔per-mode-rank API mapping for S4.
2. **WP014-F3 (D2):** Fix the explicit-rank validation gap in `hosvd` (`R_n ≤ min(I_n, ∏ others)`), correct the rustdoc contract, and add boundary regression tests.
3. **WP014-F4 (D2):** Add the missing `cp.rs` tests (all validation returns, `NonConvergence`, singular-Gram path, accessors) to bring every new module to ≥95% lines/functions; re-run `cargo llvm-cov -p prin-tensor`.
4. **WP014-F2 (D2):** Establish the commit trail: commit the audited S1 baseline as `feat(WP-014)` with the `faer` justification in the message (code+tests together), then each S3 fix as its own finding-ID commit; commit the handoff note with its corrections.
5. **WP014-F5 (D3):** Align `cp_als` with the reference (error-based convergence criterion; all-factor normalization with `1e-12` clamp; documented init-distribution delta) or obtain a plan amendment for each deliberate delta, with parity evidence from action 1 adjudicating.
6. **WP014-F6 (D4):** Correct `lib.rs`/README convergence and parity-claim text, remove or wire `invert_permutation`, de-duplicate `flat_to_multi`, repair the two misused error variants, and fix the handoff test count.

After all D1–D2 findings are addressed (and F5 resolved by code or amendment), re-run the full A1–A10 checklist and append the closure table (§7) with a delta re-audit before entering S4 documentation.

**Maintainer acknowledgment of verdict:** pending — to be recorded here upon maintainer approval.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP014-F1 | | | |
| WP014-F2 | | | |
| WP014-F3 | | | |
| WP014-F4 | | | |
| WP014-F5 | | | |
| WP014-F6 | | | |

**Delta re-audit date:** — — **Result:** —

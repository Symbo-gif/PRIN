# PRIN Audit Report — Cycle 009 / WP-009

**Date:** 2026-08-08
**Auditor:** Devin (AI pair)
**Scope:** WP-009 "PAC, coupling topologies, and phase k-NN" — `crates/prin-dynamics/src/pac.rs`, `crates/prin-dynamics/src/coupling.rs`, `crates/prin-dynamics/src/models.rs` (test module), `crates/prin-dynamics/src/lib.rs`, `crates/prin-dynamics/tests/parity_pac.rs`
**Sessions:** 0033 (S1 implementation); 0034 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-1/0034-wp009-s2-pac-coupling-topologies-and-phase-k-nn.md`
**Git state:** `feat/wp006-oscillator-state` @ `7d0cbd1`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | PAC, topology enums/builders, k-NN edge-property tests all present; no undeclared files; rayon phase-sort k-NN already in `state.rs` from WP-006 |
| Plan/architecture conformance (A2) | ✅ | Numerics in Rust f64; `#![forbid(unsafe_code)]` preserved; no Python numerics; deterministic `Seed` for small-world rewiring; no new dependencies |
| Tests in tandem + coverage (A3) | ⚠️ | 198 tests pass (162 unit + 16 + 9 + 9 + 2 doctests); coverage pac.rs 100% / coupling.rs 100% lines; `normalization_one_over_k_explicit_in_sparse` only asserts `is_finite()` (WP009-F2) |
| Numerical parity + invariants (A4) | ⚠️ | 9 PAC parity tests pass; 1/N vs 1/k verified by `sparse_knn_k_equals_n_minus_1_equals_full_default`; ring/small-world normalization inconsistent when k_ring clamped to odd (WP009-F3) |
| Quality gates (A5) | ⚠️ | clippy, rustdoc, ruff, mypy, interrogate, bandit all clean; **`cargo fmt --check` fails** on `coupling.rs:339` (WP009-F1) |
| Security (A6) | ✅ | Snyk Code 0 issues; Snyk SCA 0 findings; `cargo audit` only inherited `paste` (amendment #9); `pip-audit` clean; no `unsafe`; no secrets |
| Docstring/doc coverage (A7) | ✅ | Rustdoc 100% public, 0 warnings; interrogate 100% (104/104); all new public API documented |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers in changed files; no orphan files; gitignore respected |
| CI status (A9) | ⚠️ | S1 commit not pushed; latest CI (c74550d) shows pre-existing `parity` (maturin build) and `python` failures unrelated to WP-009; `rust` and `snyk` workflows green |
| Artefact trail (A10) | ✅ | WP-008 audit `008-wp008-audit.md` and state report `008-project-state.md` exist; session register 0033 READY / 0034 PLANNED; S1 handoff note committed |

## 2. Methodology

Commands executed and environments used (every claim is evidence-backed):

```powershell
# Scope inspection
git show --stat 7d0cbd1
git diff c74550d..7d0cbd1 --stat
git diff c74550d..7d0cbd1 -- crates/prin-dynamics/src/models.rs
git diff c74550d..7d0cbd1 -- crates/prin-dynamics/src/lib.rs
git show c74550d:crates/prin-dynamics/src/pac.rs   # confirmed 6-line stub → 505 lines

# Quality gates
cargo fmt --all -- --check                           # FAIL (exit 1) — coupling.rs:339 comment indentation
cargo clippy --workspace --all-targets -- -D warnings # PASS (exit 0)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # PASS (exit 0)

# Tests
cargo test -p prin-dynamics                           # 162 unit + 16 + 9 + 9 + 2 doctests = 198 passed
cargo test -p prin-dynamics --features strict-checks  # 165 unit + 16 + 9 + 9 = 199 passed
cargo test --workspace                                # all green

# Coverage
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
#   pac.rs       100.00% lines /  99.79% regions
#   coupling.rs  100.00% lines /  98.75% regions
#   models.rs     98.34% lines /  97.98% regions
#   TOTAL         98.32% lines /  97.93% regions

# Python gates (no Python changed; full suite for regression)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/    # PASS
.venv\Scripts\mypy python/prin --strict                               # PASS (16 files)
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin     # 100% (104/104)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                 # PASS (0 issues)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp  # PASS

# Security
cargo audit                            # PASS (only inherited paste RUSTSEC-2024-0436, amendment #9)
.venv\Scripts\python -m pip_audit .    # PASS (no vulnerabilities)
# Snyk MCP:
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\src severity_threshold=low  → 0 issues
#   snyk_sca_scan path=C:\dev\PRIN all_projects=true severity_threshold=low           → 0 findings

# Hygiene
Select-String -Path <changed files> -Pattern "TODO|FIXME|HACK|stub|unimplemented|todo!|unreachable!"  # none found
Select-String -Path pac.rs,coupling.rs -Pattern "unsafe"  # none found

# CI
gh run list --branch feat/wp006-oscillator-state --limit 10  # rust ✓, snyk ✓, repro ✓; parity ✗ (maturin), python ✗ (pre-existing)
```

## 3. Detailed findings

### 3.1 A1 — Scope conformance

The S1 commit `7d0cbd1` touches exactly the declared scope: `pac.rs` (stub → full
implementation), `coupling.rs` (Topology enum + builders), `models.rs` (test module
additions), `lib.rs` (re-exports), and `tests/parity_pac.rs` (new parity file). No
undeclared files were shipped. No new dependencies were added (Cargo.toml unchanged).

The WP-009 declaration scope includes "rayon phase-sort k-NN index". The
`build_phase_knn_index` function in `state.rs` already uses `par_sort_by` (rayon
parallel sort) from WP-006; `state.rs` was not modified in this S1. The S1 session
added k-NN edge-property tests in `models.rs`, completing the acceptance criterion.
The rayon scope item was satisfied by prior work — no deficiency, though the S1
handoff note's claim that the sort is "sequential" is inaccurate (see WP009-F5).

### 3.2 A2 — Plan/architecture conformance

- **Numerics in Rust:** All PAC and topology computations use `f64` in Rust. No
  Python numerics duplicated. ✓
- **Crate layering:** `prin-dynamics` remains a leaf crate; no upward dependencies
  added. ✓
- **`#![forbid(unsafe_code)]`:** Preserved in `lib.rs:25`; no `unsafe` in new code. ✓
- **Deterministic seeding:** `Topology::SmallWorld` takes a `Seed` by value; rewiring
  uses `seed.next_f64()` (returns `f64`, PCG64-based). Determinism verified by
  `topology_small_world_deterministic_with_seed` and the `small_world_deterministic_same_seed`
  proptest. ✓
- **One algorithm, one implementation:** PAC is a single implementation in `pac.rs`;
  topologies are single implementations in `coupling.rs`. No duplication. ✓
- **No new dependencies:** `Cargo.toml` and `Cargo.lock` unchanged by the S1 commit. ✓

### 3.3 A3 — Tests in tandem + coverage

Tests were written in the same commit as the code (single S1 commit `7d0cbd1`).
Coverage on new/changed code:

| File | Lines | Cover | Regions | Cover |
|---|---|---|---|---|
| `pac.rs` | 267 | 100.00% | 470 | 99.79% |
| `coupling.rs` | 271 | 100.00% | 401 | 98.75% |
| `models.rs` | 1329 | 98.34% | 2375 | 97.98% |

All above the ≥95% gate. The 1 missed region in `pac.rs` is the
`PacError::InvalidPhaseOffset` display format (unreachable in normal flow). The 5
missed regions in `coupling.rs` are error-display paths.

**Finding WP009-F2 (D2):** The `normalization_one_over_k_explicit_in_sparse` test
(`models.rs`) claims to verify the 1/k normalization but only asserts `is_finite()`
on the derivative values — it does not check the actual normalization factor. The
companion `normalization_one_over_n_explicit_in_mean_field` test does verify specific
derivative values. The asymmetry means the 1/k path is under-tested relative to the
1/N path. The acceptance criterion "1/N versus 1/k is explicit" is still met by the
`sparse_knn_k_equals_n_minus_1_equals_full_default` test (which verifies the exact
`(N-1)/N` ratio), so this is a test-quality issue, not a criterion failure.

### 3.4 A4 — Numerical parity + invariants

**PAC parity:** 9 tests in `parity_pac.rs` compare against hard-coded PRINet 3.0
reference values at `epsilon = 1e-6` (amendment #14 f32-truncation tolerance). All
pass. Reference values were independently verified by hand-computation of the
modulation formula `A_out = A_in · [1 + m · cos(mean(φ_slow) + offset)]` — values
match to full f64 precision. The hard-coded-reference pattern is consistent with the
existing `parity_models.rs` and `parity_integrators.rs`.

**1/N vs 1/k normalization:** Verified by `sparse_knn_k_equals_n_minus_1_equals_full_default`
— the sparse/full coupling ratio is exactly `(N-1)/N` as expected (K/k vs K/N with
k=N-1). Also verified by `normalization_one_over_n_explicit_in_mean_field` (specific
derivative values for synchronized state).

**k-NN edge properties:** `knn_index_has_exact_k_neighbors_no_self_loops`,
`knn_index_neighbors_are_phase_nearest`, `knn_index_wraps_around_circle`,
`knn_index_symmetric_neighbor_property` all pass. The `state::proptests::knn_index_has_k_entries_and_no_self`
property test also passes.

**Sparse/full equivalence:** `sparse_knn_k_equals_n_minus_1_equals_full_default`
verifies the explicit normalization difference (not bit-identical equivalence, which
is correct since 1/k ≠ 1/N when k < N). `topology_all_to_all_matrix_matches_full_default`
verifies that the `AllToAll` topology matrix produces identical derivatives to
`CouplingMode::Full { matrix: None }`.

**Finding WP009-F3 (D3):** The `build_ring` function validates that `k_ring` is even
*before* clamping to `n-1`. When `k_ring > n-1` and `n-1` is odd (e.g., k_ring=10,
n=6 → clamped to 5), the weight is `K/5` but only `2*(5/2) = 4` edges are created
per node. The total coupling energy is `4·K/5 = 0.8K` instead of `K`, violating the
documented "K/degree per edge" normalization rule (degree=4, weight should be K/4).
The same issue exists in `build_small_world` (lines 256–257). The
`topology_ring_clamps_k_to_n_minus_1` test only checks `nonzero <= 4`, not the weight,
so this is not caught.

### 3.5 A5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | **FAIL** (exit 1) |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Rustdoc | `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | PASS |
| Ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| Mypy | `mypy python/prin --strict` | PASS |
| Interrogate | `interrogate -c pyproject.toml python/prin` | 100% |
| Bandit | `bandit -r . -c pyproject.toml` | PASS |

**Finding WP009-F1 (D2):** `cargo fmt --all -- --check` fails with a diff at
`coupling.rs:339` — a test comment is not properly indented (missing leading spaces
to align with the preceding `let weight` line). The S1 handoff note claimed this gate
passed with exit 0, which is inaccurate.

### 3.6 A6 — Security

| Scan | Result |
|---|---|
| Snyk Code (`crates/prin-dynamics/src`, low+) | 0 issues |
| Snyk SCA (all projects, low+) | 0 findings |
| `cargo audit` | Only inherited `paste` RUSTSEC-2024-0436 (amendment #9) |
| `pip-audit .` | No vulnerabilities |
| `unsafe` scan | None in `pac.rs` or `coupling.rs`; `#![forbid(unsafe_code)]` in `lib.rs` |
| Secret scan | No secrets in diff |

**Finding WP009-F4 (D3):** `PhaseAmplitudeCoupling::with_clamp` (`pac.rs:105`) does
not validate that `amp_min <= amp_max` or that either bound is finite. If called with
`amp_min > amp_max`, the downstream `clamp_amplitude_to` function calls
`f64::clamp(min, max)` which **panics** (per Rust std: "Panics if min > max"). The
`with_clamp_allows_custom_range` test only exercises valid ranges. No test covers the
inverted or non-finite clamp case.

### 3.7 A7 — Documentation coverage

- Rustdoc: 100% public API documented, 0 warnings with `-D warnings`. ✓
- Interrogate: 100% (104/104) Python public docstrings. ✓
- All new public types (`PhaseAmplitudeCoupling`, `PacError`, `Topology`,
  `CouplingError`) have module-level and item-level rustdoc. ✓
- Doctests: 2 pass (`pac.rs` example, `coupling.rs` example). ✓

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/HACK/XXX/stub markers in any changed file. ✓
- No `todo!()`/`unreachable!()`/`unimplemented!()` in production code. ✓
- No orphan files (all new files are in declared scope). ✓
- `.gitignore` respected (no build artefacts committed). ✓
- `__all__` N/A (Rust crate; Python unchanged). ✓

### 3.9 A9 — CI status

The S1 commit `7d0cbd1` has not been pushed to the remote; CI has not run on it. The
latest CI runs on `feat/wp006-oscillator-state` (from commit `c74550d`, 2026-08-07)
show:

| Workflow | Status | Notes |
|---|---|---|
| `rust` | ✅ success | fmt, clippy, clippy-strict, test (3 OS), test-strict |
| `snyk` | ✅ success | Snyk Code + SCA |
| `repro` | ✅ success | Reproducibility check |
| `parity` | ❌ failure | `maturin failed` — PyO3 build issue, pre-existing, not WP-009 |
| `python` | ❌ failure | Pre-existing, not WP-009 (no Python changed) |
| `gpu` | ⊘ skipped | No GPU runner |

The `parity` and `python` failures are infrastructure issues from the previous commit
and are not caused by WP-009 changes (which are Rust-only). The local equivalents of
all `rust` workflow gates have been verified by this audit (except `cargo fmt`, see
WP009-F1). The S1 commit should be pushed after WP009-F1 is remediated so CI can
validate.

### 3.10 A10 — Artefact trail

- WP-008 Audit Report: `DOCS/audits/008-wp008-audit.md` — exists, S3 closure table
  appended, CLEAN delta re-audit. ✓
- WP-008 Project State Report: `DOCS/reports/008-project-state.md` — exists, declares
  WP-009. ✓
- Session register: 0033 (S1) marked READY, 0034 (S2) marked PLANNED. ✓
- S1 handoff note: `DOCS/sessions/phase-1/0033-wp009-s1-handoff-note.md` — committed. ✓

**Finding WP009-F5 (D4):** The S1 handoff note contains three factual inaccuracies:
(a) `pac.rs` is described as "**New** — full PAC implementation" when it was actually
a 6-line stub expanded to 505 lines (the file existed at `c74550d`); (b) it states
"The existing `build_phase_knn_index` in `state.rs` uses sequential sort" when the
function actually uses `par_sort_by` (rayon parallel sort) since WP-006; (c) it
claims "196 tests" but the actual count is 198 (162 unit + 16 integrator parity + 9
model parity + 9 PAC parity + 2 doctests). These do not affect the acceptance
criteria but violate the evidence-based-claims principle (§1.4).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP009-F1 | D2 | `crates/prin-dynamics/src/coupling.rs:339` | `cargo fmt --check` fails — test comment not properly indented | Coding Standards §5 (quality gates clean) | Run `cargo fmt` to fix indentation; re-verify `--check` passes |
| WP009-F2 | D2 | `crates/prin-dynamics/src/models.rs:1756–1780` | `normalization_one_over_k_explicit_in_sparse` only asserts `is_finite()` — does not verify the 1/k normalization despite its name | S1 brief prohibited list ("weakened assertions"); Testing Standards | Add explicit ratio assertion (e.g., `d_k2_coupling / d_k3_coupling ≈ 3/2` for K/2 vs K/3) or assert specific derivative values |
| WP009-F3 | D3 | `crates/prin-dynamics/src/coupling.rs:214–220` (`build_ring`), `coupling.rs:256–257` (`build_small_world`) | When `k_ring` is clamped to an odd `n-1`, weight uses `K/k_ring` (odd) but only `2*(k_ring/2)` edges are created — violates "K/degree per edge" normalization | Plan §4 (architecture rules — normalization invariants); coupling.rs module docs | Clamp `k_ring` to the nearest even number ≤ `n-1`, or use `2*half` as the weight denominator |
| WP009-F4 | D3 | `crates/prin-dynamics/src/pac.rs:105–116` (`with_clamp`) | `with_clamp` does not validate `amp_min <= amp_max` or finiteness — `f64::clamp` panics if `min > max` | Coding Standards (public API input validation) | Add validation: `amp_min.is_finite() && amp_max.is_finite() && amp_min <= amp_max`; return a new `PacError::InvalidClampRange` variant; add regression test |
| WP009-F5 | D4 | `DOCS/sessions/phase-1/0033-wp009-s1-handoff-note.md` | Three factual errors: pac.rs was a stub (not "New"), k-NN uses rayon (not "sequential sort"), test count is 198 (not 196) | Development Workflow Standards §1.4 (evidence-based claims) | Correct the handoff note: pac.rs "expanded from stub", k-NN "already uses rayon `par_sort_by`", test count "198" |
| WP009-F6 | D4 | `crates/prin-dynamics/src/coupling.rs:376–379` | `topology_ring_clamps_k_to_n_minus_1` test comment says "we clamp before the odd check" but the code checks oddness *before* clamping; test only checks edge count, not weight | Testing Standards (test accuracy) | Fix comment to "odd check is before clamp"; add weight assertion to catch WP009-F3 |
| WP009-F7 | D4 | `crates/prin-dynamics/src/coupling.rs:240–280` (`build_small_world`) | Rewiring only rewires right-neighbour edges, producing a directed graph; standard Watts–Strogatz is undirected; module docs don't clarify | Documentation Standards (module docs should match standard algorithm) | Either maintain symmetry by rewiring both (i,j) and (j,i), or document that the topology is directed in the module rustdoc |

## 5. Deviation-ledger delta

New findings added to the ledger: WP009-F1, WP009-F2, WP009-F3, WP009-F4, WP009-F5,
WP009-F6, WP009-F7.

Carried findings re-inspected: none (no findings were carried into WP-009).

No D1 findings — verdict is PASS-WITH-FINDINGS.

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS**

No D1 (trajectory breach) findings. Two D2 (standard violation) findings must be
fixed in S3. Two D3 (plan drift) findings should be fixed in S3. Three D4 (cosmetic)
findings should be fixed in S3 or carried (max one carry).

The WP-009 acceptance criteria are met:
- ✅ Golden parity covers all modes (9 PAC parity + 9 model parity + 16 integrator
  parity, all green).
- ✅ 1/N versus 1/k is explicit (`sparse_knn_k_equals_n_minus_1_equals_full_default`
  verifies the exact ratio; `normalization_one_over_n_explicit_in_mean_field`
  verifies specific values).
- ✅ Sparse/full equivalence and k-NN edge properties pass (5 edge-property tests +
  1 proptest + topology equivalence test).

**Ordered S3 action list:**

1. **WP009-F1 (D2):** Run `cargo fmt` to fix `coupling.rs:339` comment indentation.
   Re-verify `cargo fmt --all -- --check` passes.
2. **WP009-F2 (D2):** Strengthen `normalization_one_over_k_explicit_in_sparse` —
   replace `is_finite()` assertions with an explicit K/k ratio check (e.g., compare
   k=2 vs k=3 coupling terms and assert the 3/2 ratio where neighbor sets overlap).
3. **WP009-F3 (D3):** Fix `build_ring` and `build_small_world` clamping — clamp
   `k_ring` to the nearest even number ≤ `n-1` (or use `2*half` as the weight
   denominator) so the "K/degree per edge" normalization is preserved. Add a test
   that verifies the weight when k_ring is clamped.
4. **WP009-F4 (D3):** Add `amp_min <= amp_max` and finiteness validation to
   `PhaseAmplitudeCoupling::with_clamp`; add a `PacError::InvalidClampRange` variant;
   add a regression test for the inverted-range case.
5. **WP009-F5 (D4):** Correct the S1 handoff note factual errors (pac.rs stub→full,
   rayon sort, test count 198).
6. **WP009-F6 (D4):** Fix the `topology_ring_clamps_k_to_n_minus_1` test comment and
   add a weight assertion (dependent on WP009-F3 fix).
7. **WP009-F7 (D4):** Either make `build_small_world` rewiring symmetric (rewire both
   directions) or document the directed interpretation in the module rustdoc.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP009-F1 | FIXED | `b4749ba` | `cargo fmt --all -- --check` → exit 0 (no diff). Restructured `topology_ring_basic` trailing comment so rustfmt produces clean output. |
| WP009-F2 | FIXED | `b4749ba` | `normalization_one_over_k_explicit_in_sparse` now asserts the explicit `K/k` per-edge weight against the actual `build_phase_knn_index` neighbour set for k=2 and k=3 (distinguishing 1/k from 1/N via a 1/N divergence check), plus a shared-neighbour `K/2` vs `K/3` = 3/2 ratio check. Replaces the prior `is_finite()`-only assertions. Test passes (`cargo test -p prin-dynamics --lib normalization`). |
| WP009-F3 | FIXED | `b4749ba` | New `clamp_ring_k` helper clamps `k_ring` to the largest even number `<= n-1`; `build_ring` and `build_small_world` use it so per-node degree == `k_ring` and the `K/degree`-per-edge energy invariant (row sum == K) holds. Regression tests `topology_ring_odd_clamp_preserves_k_over_degree_invariant` (n=6, k_ring=10 → effective 4, weight K/4, row sum K) and `topology_small_world_odd_clamp_preserves_edge_count_and_energy` (same clamp via the small-world path) pass. |
| WP009-F4 | FIXED | `b4749ba` | `PhaseAmplitudeCoupling::with_clamp` now validates `amp_min.is_finite() && amp_max.is_finite() && amp_min <= amp_max` and returns a new `PacError::InvalidClampRange { amp_min, amp_max }` variant (prevents the `f64::clamp` panic on inverted range). Regression tests `with_clamp_rejects_inverted_range`, `with_clamp_rejects_non_finite_bounds`, `with_clamp_allows_equal_bounds` pass. |
| WP009-F5 | FIXED | `bf46cee` | S1 handoff note corrected: `pac.rs` described as "expanded from 6-line stub" (not "New"); k-NN note states `build_phase_knn_index` "already uses rayon `par_sort_by` (parallel sort) since WP-006" (not "sequential sort"); test count corrected to 198 (not 196); `cargo fmt --check` gate row corrected from PASS to FAIL (fixed via WP009-F1). Correction banner added at note top. |
| WP009-F6 | FIXED | `b4749ba` | `topology_ring_clamps_k_to_n_minus_1` test comment corrected ("odd check is before clamp on the *input* k_ring; `clamp_ring_k` then makes the effective degree 4") and strengthened with exact degree (4), per-edge weight (K/4), and total-energy (row sum == K) assertions. |
| WP009-F7 | FIXED | `b4749ba` | `build_small_world` documented as a **directed** variant in both the function rustdoc and the `Topology::SmallWorld` variant doc: only the outgoing edge `mat[i, j]` is rewired, so `mat[i, j]` and `mat[j, i]` are not guaranteed equal after rewiring; per-node out-degree and total edge count are preserved. S1 handoff note #2 clarified to match. |

**Delta re-audit date:** 2026-08-08 — **Result:** CLEAN

### Delta re-audit methodology (S3)

All commands executed 2026-08-08 on `feat/wp006-oscillator-state` @ `bf46cee`
after the two remediation commits (`b4749ba`, `bf46cee`):

```powershell
# Quality gates (all green)
cargo fmt --all -- --check                            # PASS (exit 0, no diff)
cargo clippy --workspace --all-targets -- -D warnings # PASS (exit 0)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps  # PASS (exit 0)

# Tests (default + strict-checks + workspace)
cargo test -p prin-dynamics                            # 167 unit + 16 + 9 + 9 + 2 doctests = 203 passed
cargo test -p prin-dynamics --features strict-checks   # 170 unit + 16 + 9 + 9 = 204 passed
cargo test --workspace                                 # all green

# Coverage on changed code (>=95% gate)
cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only
#   coupling.rs  99.40% lines / 98.26% regions  (was 100% / 98.75%; new clamp_ring_k + tests)
#   pac.rs      100.00% lines / 99.03% regions  (was 100% / 99.79%; new InvalidClampRange path covered)
#   models.rs    98.24% lines / 97.70% regions  (was 98.34% / 97.98%; strengthened F2 test)
#   TOTAL        98.26% lines / 97.85% regions

# Python gates (no Python changed; full suite for regression)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/   # PASS
.venv\Scripts\python -m bandit -r . -c pyproject.toml                # PASS (0 issues)

# Security
cargo audit                            # PASS (only inherited paste RUSTSEC-2024-0436, amendment #9)
.venv\Scripts\python -m pip_audit .    # PASS (no vulnerabilities)
# Snyk MCP (authenticated, executed):
#   snyk_code_scan path=C:\dev\PRIN\crates\prin-dynamics\src severity_threshold=low  → 0 issues
#   snyk_sca_scan  path=C:\dev\PRIN all_projects=true severity_threshold=low
#                  command=C:\dev\PRIN\.venv\Scripts\python                            → 0 findings
```

### Delta re-audit verdict

- **A1 scope:** Remediation touched only declared WP-009 files
  (`coupling.rs`, `pac.rs`, `models.rs`) plus the S1 handoff note. No
  undeclared files, no new dependencies. ✓
- **A2 plan/architecture:** `#![forbid(unsafe_code)]` preserved; no `unsafe`
  added; f64 numerics; no Python numerics; deterministic `Seed` for
  small-world rewiring unchanged. ✓
- **A3 tests/coverage:** 5 new regression tests added (F3 ×2, F4 ×3 counting
  the equal-bound positive case); all changed code ≥95% lines. ✓
- **A4 parity/invariants:** 9 PAC parity + 9 model parity + 16 integrator
  parity all green; 1/N vs 1/k now explicitly asserted with the actual k-NN
  neighbour set (F2); K/degree energy invariant now asserted for the
  odd-clamp case (F3). ✓
- **A5 quality:** `cargo fmt --check`, clippy `-D warnings`, rustdoc
  `-D warnings` all exit 0. ✓
- **A6 security:** Snyk Code 0 issues; Snyk SCA 0 findings; `cargo audit`
  only inherited `paste` (amendment #9); `pip-audit` clean; no `unsafe`;
  no secrets. ✓
- **A7 docs:** Rustdoc 100% public, 0 warnings; new `PacError::InvalidClampRange`
  variant and `clamp_ring_k` documented; `Topology::SmallWorld` directed
  interpretation documented. ✓
- **A8 hygiene:** No TODO/FIXME/stub markers added; no orphan files. ✓
- **A9 CI:** Not yet pushed; local equivalents of all `rust` workflow gates
  green. Push after S4 to let CI validate. ✓ (pending push)
- **A10 artefact trail:** This closure table and the corrected handoff note
  complete the S3 artefact set. ✓

**All seven findings FIXED. No findings carried. Delta re-audit: CLEAN.**

WP-009 acceptance criteria remain met:
- ✅ Golden parity covers all modes (9 PAC + 9 model + 16 integrator parity).
- ✅ 1/N versus 1/k is explicit (F2 now asserts the explicit K/k weight and
  the 1/k-vs-1/N divergence on the actual neighbour set).
- ✅ Sparse/full equivalence and k-NN edge properties pass (5 edge-property
  tests + 1 proptest + topology equivalence test).
- ✅ K/degree normalization invariant now holds for the odd-clamp case (F3).

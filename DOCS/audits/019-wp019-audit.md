# PRIN Audit Report — Cycle 019 / WP-019

**Date:** 2026-08-16
**Auditor:** Claude Code (AI pair)
**Scope:** WP-019 "Sparse k-NN and PAC kernels" — `crates/prin-kernels/` (`sparse_knn.rs`, `sparse_knn/cubecl.rs`, `pac.rs`, `pac/cubecl.rs`, `lib.rs`, `benches/sparse_knn_bench.rs`, `Cargo.toml`)
**Sessions:** 0073 (S1 implementation); 0074 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-3/0074-wp019-s2-sparse-k-nn-and-pac-kernels.md`
**Git state:** `main` @ `2cf1491537f1ca945257d0797e2ba8369991bdff`
**Verdict:** **PASS-WITH-FINDINGS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope present (`git diff 13b56ae..2cf1491 --stat`); nothing undeclared shipped. Non-goal (fused trainable discrete step) untouched. |
| Plan/architecture conformance (A2) | ✅ | `prin-kernels` layering preserved; no new dependency on `prin-sim` (mentioned only in doc comments); `prin_dynamics::state::build_phase_knn_index` reused rather than re-implemented (one algorithm, one implementation); no Python numerics; f64-accumulated CPU reference paths. |
| Tests in tandem + coverage (A3) | ✅ | 61 new tests + 4 proptest suites, all in the S1 commit. `sparse_knn.rs` 98.08%, `pac.rs` 98.60% (both ≥95%). `sparse_knn/cubecl.rs` and `pac/cubecl.rs` raw figures below 95% for the same accepted DV-004 non-instrumentable-`#[cube(launch)]`-body reason as `mean_field_rk4/cubecl.rs`; both new files' `wgpu,cpu` raw figures (85.86%, 82.93%) are at or above the pre-existing baseline (80.76%). |
| Numerical parity + invariants (A4) | ✅ | wgpu/CubeCL-CPU kernel-equivalence at small N, non-block-aligned N (variable degree), N=16,000/k=14 (acceptance shape), and N=100,000 (PAC) all pass at `rtol=1e-5, atol=1e-6`, independently re-run. Two cross-crate parity tests against already-PRINet-3.0-verified `prin_dynamics` references pass at `1e-4` abs tolerance. Edge sizes (empty rows, all-isolated graph, non-uniform degree) and `K/degree(i)` normalization invariants covered. CUDA: compiles cleanly (`cargo build --features cuda --lib`); no CUDA runner available to execute (DV-002, pre-existing, unchanged). |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy (default, strict-checks, cpu, wgpu+cpu — all `-D warnings`), rustdoc (workspace + all three `prin-kernels` feature combinations), ruff check/format, mypy --strict all independently re-run clean. |
| Security (A6) | ✅ | No new unapproved `unsafe`; both new `cubecl.rs` files confine `unsafe` to `ArrayArg::from_raw_parts` with `// SAFETY:` justifications, matching the existing audited pattern. `cargo audit`: 1 pre-existing allowed `paste` advisory (DV-008), no new. `bandit`: 0 issues. Snyk Code (`crates/prin-kernels/src`): 0 issues, independently re-run. No dependency/manifest changes (`Cargo.toml` diff is a `[[bench]]` target only) — Snyk Open Source correctly not re-run. |
| Docstring/doc coverage (A7) | ✅ | `interrogate` 100.0% (106/106, no Python files touched). Rustdoc: 0 warnings under `-D warnings` for the workspace and all three `prin-kernels` feature combinations (`cpu`, `wgpu,cpu`, `cuda`). All new public items documented. |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub markers. Git tree clean, session register row 0073 = COMPLETE. One finding: the S1 handoff note's coverage evidence table contains a factually incorrect cell (WP019-F1). |
| CI status (A9) | ✅ | No `.github/workflows/*` files touched. Local reproduction of every test/coverage/quality command is exact-or-consistent with the S1 handoff note. No benchmark regression gate exists for `prin-kernels` (unchanged); the new pilot benchmark independently reproduced comparable timings. |
| Artefact trail (A10) | ✅ | Prior audit (`018-wp018-audit.md`, PASS) and PSR-018 consistent with this WP's declared scope and acceptance criteria. S1 handoff note (`DOCS/experiments/0073-wp019-s1-handoff.md`) present with a full acceptance-criterion evidence map (one cell inaccurate — see WP019-F1). |

## 2. Methodology

All commands executed on Windows (local dev machine, wgpu/DX12 backend), independently, without reference to the S1 handoff note's own command transcripts except to compare final figures. Git diff range: `13b56ae` (WP-018 S4, predecessor baseline) → `2cf1491` (WP-019 S1).

```powershell
# A1 — scope
git diff 13b56ae..2cf1491 --stat                                          # 10 files, matches declared scope exactly

# A5 — Quality gates
cargo fmt --all -- --check                                                # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                     # exit 0, clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings   # exit 0, clean
cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings         # exit 0, clean
cargo clippy -p prin-kernels --all-targets --features wgpu,cpu -- -D warnings    # exit 0, clean
cargo build -p prin-kernels --features cuda --lib                         # exit 0, clean (compile-only, DV-002)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps          # exit 0, 0 warnings
cargo doc -p prin-kernels --no-deps --features cpu                        # exit 0, 0 warnings
cargo doc -p prin-kernels --no-deps --features wgpu,cpu                   # exit 0, 0 warnings
cargo doc -p prin-kernels --no-deps --features cuda                       # exit 0, 0 warnings
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/     # All checks passed!
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 50 files already formatted
.venv\Scripts\python -m mypy python/prin --strict                         # Success: no issues found in 18 source files

# A3 — Tests
cargo test --workspace                                                    # all crates green, 0 failed
cargo test -p prin-kernels --features cpu                                 # 100 unit + 1 doctest passed
cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1        # 121 unit + 1 doctest passed

# A3 — Coverage
cargo llvm-cov -p prin-kernels --features cpu --summary-only
cargo llvm-cov -p prin-kernels --features wgpu,cpu --summary-only

# A6 — Security
cargo audit                                                                # 1 allowed warning (paste RUSTSEC-2024-0436)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                     # No issues identified
snyk code test crates/prin-kernels/src                                    # 0 issues (org symbo-gif)

# A7 — Documentation
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin         # 100.0% (106/106) PASSED

# A4 — Python tests (unaffected by this WP; re-run for non-regression)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 306 passed, 6 deselected

# A4/A9 — WP-specific acceptance evidence
cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1 wgpu_matches_cpu_reference_at_n_16k_k_14
cargo bench -p prin-kernels --bench sparse_knn_bench --features wgpu
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (session 0073/0074 brief, PSR-018 §7): `crates/prin-kernels/` — sparse phase-neighbor coupling and PAC modulation kernels with CSR/index interoperability, single-source CubeCL with CPU/wgpu/CUDA dispatch, continuing the WP-017/WP-018 architecture. Non-goals: fused trainable discrete step.

**Delivered** (`git diff 13b56ae..2cf1491 --stat`):

| File | Change | In scope? |
|---|---|---|
| `crates/prin-kernels/src/sparse_knn.rs` | New. `SparseKnnGraph` (CSR), `sparse_knn_derivatives_cpu` reference, 26 tests + 2 proptest suites | ✅ |
| `crates/prin-kernels/src/sparse_knn/cubecl.rs` | New. `sparse_knn_coupling` gather kernel + host dispatch, 10 tests | ✅ |
| `crates/prin-kernels/src/pac.rs` | New. `PacParams`, `pac_modulate_cpu` reference, 16 tests + 2 proptest suites | ✅ |
| `crates/prin-kernels/src/pac/cubecl.rs` | New. Two-stage reduce+broadcast kernel + host dispatch, 9 tests | ✅ |
| `crates/prin-kernels/src/lib.rs` | `pub mod sparse_knn; pub mod pac;` + module-doc entries | ✅ |
| `crates/prin-kernels/benches/sparse_knn_bench.rs` | New — criterion benchmark at N=16,000/k=14 | ✅ |
| `crates/prin-kernels/Cargo.toml` | `[[bench]]` target only; no dependency changes | ✅ |
| `DOCS/experiments/0073-wp019-s1-handoff.md` | S1 handoff note | ✅ |
| `DOCS/sessions/SESSION_REGISTER.md` | Session 0073 → COMPLETE | ✅ |
| `DOCS/sessions/phase-3/0073-...md` | Status field update | ✅ |

No undeclared work shipped. The non-goal area (fused trainable discrete step, WP-020's scope) is untouched. `prin-sim::csr_coupling` is referenced only in doc comments (design-rationale citations), not as a new dependency — confirmed no `prin-sim` entry was added to `Cargo.toml`.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** All new code lives in `prin-kernels`, the declared crate for GPU kernel work (Plan §6). No `prin-sim` dependency was added; `prin-dynamics` was already a declared (previously unused) dependency, now used for `build_phase_knn_index` and `AMPLITUDE_MIN`/`AMPLITUDE_MAX` — confirmed via `Cargo.toml` diff (no `[dependencies]` change) and `grep -rn "prin_sim" crates/prin-kernels/src` (doc comments only, no `use` statements).
- **One algorithm, one implementation:** `SparseKnnGraph::from_phase_knn` calls `prin_dynamics::state::build_phase_knn_index` rather than re-implementing k-NN search. `sparse_knn_coupling`'s gather kernel is architecturally distinct from (not a duplicate of) `prin_sim::csr_coupling::SparseCoupling::kuramoto_coupling`'s SpMV decomposition — a deliberate, documented design choice for the target shape's small near-uniform degree, not a duplication of the same algorithm (the SpMV path remains the right tool for general/high-degree CPU matrices; `prin-kernels` has no dependency on `prin-sim`, so no reverse-dependency was introduced).
- **No Python numerics:** No Python files touched.
- **f64 accumulation:** `sparse_knn_derivatives_cpu`'s per-row sums and `pac.rs`'s `modulation_factor` mean both accumulate in `f64` before downcasting (Coding Standards §2.2), confirmed by direct code read (`sparse_knn.rs:361-362`, `pac.rs:170`).
- **Explicit state/seeding:** No RNG introduced; deterministic data flow preserved.

### 3.3 A3 — Tests in tandem + coverage

**New tests in the S1 commit** (`2cf1491`, single commit — trivially in-tandem): 61 unit/error-path tests (26 `sparse_knn.rs` + 10 `sparse_knn/cubecl.rs` + 16 `pac.rs` + 9 `pac/cubecl.rs`) plus 4 proptest suites (2 per module). Verified by `cargo test -p prin-kernels --features cpu -- --list` and `--features wgpu,cpu -- --list`.

**Coverage** (`cargo llvm-cov -p prin-kernels`, independently re-run):

| File | `cpu` lines | `wgpu,cpu` lines | Gate |
|---|---|---|---|
| `sparse_knn.rs` | 98.08% | 98.08% | ≥95% ✅ |
| `pac.rs` | 98.60% | 98.60% | ≥95% ✅ |
| `sparse_knn/cubecl.rs` (raw) | 77.46% | 85.86% | See below |
| `pac/cubecl.rs` (raw) | 77.50% | 82.93% | See below |

Both `.rs` files' pure-CPU-reference coverage exceeds the ≥95% gate, exact match to the S1 handoff note's figures. The two `cubecl.rs` files' raw figures are below 95% for the same accepted reason established at WP-017/WP-018 (DV-004): the `#[cube(launch)]` kernel bodies (`sparse_knn_coupling`; `pac_phase_sum_block_reduce`, `pac_modulate`) are non-instrumentable by `cargo-llvm-cov` on stable Rust; correctness is verified by the kernel-equivalence tests (§3.4). Both files' `wgpu,cpu` raw figures (85.86%, 82.93%) are at or above `mean_field_rk4/cubecl.rs`'s own current raw figure under the identical feature combination (80.76%, re-measured this session, exact match to PSR-018) — i.e. proportionally more of this WP's new kernel-dispatch code is instrumented than the pre-existing accepted baseline.

No weakened tests or tolerance drift detected in the diff. All kernel-equivalence tests use `rtol=1e-5, atol=1e-6` (Testing Standards §3); cross-crate `f32`-vs-`f64` parity tests use `1e-4` absolute tolerance with a stated rationale (precision-boundary comparison, not same-precision GPU-vs-CPU), consistent with WP-018's own established precedent.

**Coverage evidence-table discrepancy — see WP019-F1** (§4): the S1 handoff note's coverage table states `pac/cubecl.rs`'s `cpu`-feature column as "— (not compiled without a GPU feature)". Independent re-measurement shows `pac/cubecl.rs` **is** compiled and covered (77.50% raw lines) under `--features cpu` alone, and `pac::cubecl::tests_cpu::*` tests execute under that feature set (confirmed via `cargo test -p prin-kernels --features cpu -- --list`). This does not affect the audit verdict on coverage (both figures independently reconfirmed as correctly falling under the DV-004 carve-out either way) but is a factual inaccuracy in a committed evidentiary artefact.

### 3.4 A4 — Numerical parity + invariants

**Kernel equivalence (GPU/CubeCL-CPU vs. CPU reference), independently re-run:**

| Test | Shape | Backend | Tolerance | Result |
|---|---|---|---|---|
| `sparse_knn::cubecl::tests::wgpu_matches_cpu_reference_for_small_n` | N=64, degree 14 | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `sparse_knn::cubecl::tests::wgpu_matches_cpu_reference_for_non_block_aligned_n_with_variable_degree` | N=1000, variable degree incl. isolated | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `sparse_knn::cubecl::tests::wgpu_matches_cpu_reference_at_n_16k_k_14` | **N=16,000, degree=14 (acceptance shape)** | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `sparse_knn::cubecl::tests_cpu::cpu_backend_matches_cpu_reference` | N=300 | CubeCL-CPU | `rtol=1e-5, atol=1e-6` | PASS |
| `sparse_knn::cubecl::tests_cpu::cpu_backend_handles_all_isolated_graph` | N=16, all-isolated (edge case) | CubeCL-CPU | exact (0-contribution) | PASS |
| `pac::cubecl::tests::wgpu_matches_cpu_reference_for_small_n` | slow N=37, fast N=64 | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `pac::cubecl::tests::wgpu_matches_cpu_reference_for_non_block_aligned_n` | slow N=1000, fast N=777 | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `pac::cubecl::tests::wgpu_matches_cpu_reference_at_large_n` | N=100,000 | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `pac::cubecl::tests_cpu::cpu_backend_matches_cpu_reference_multi_block` | N=600 (3 blocks) | CubeCL-CPU | `rtol=1e-5, atol=1e-6` | PASS |

**N=16K, k=14 acceptance criterion — independently reproduced:** `wgpu_matches_cpu_reference_at_n_16k_k_14` passes; benchmark evidence re-run this session (`cargo bench -p prin-kernels --bench sparse_knn_bench --features wgpu`): `cpu_native` 1.823–1.854 ms (8.63–8.78 Melem/s), `wgpu_device_dispatch` 1.892–1.969 ms (8.13–8.46 Melem/s) — consistent with the S1 handoff note's reported range (1.854–1.886 ms / 1.917–1.986 ms respectively), within normal run-to-run variance. Reported and treated as observed pilot evidence, not a scientific conclusion (Testing Standards §2), matching the WP's own framing; no regression gate is defined for this new benchmark.

**Edge sizes / normalization invariants — independently verified present:** empty-graph structural-invariant tests (`from_csr_rejects_empty`, etc.), all-isolated graphs (`cpu_backend_handles_all_isolated_graph`, `from_phase_knn_k_zero_isolates_all`), non-uniform per-row degree (star+ring hybrid, `wgpu_matches_cpu_reference_for_non_block_aligned_n_with_variable_degree`), single/uniform-degree cases, and the N=16K/k=14 shape. `K/degree(i)` normalization directly asserted by `matches_uniform_degree_k_normalization` (non-uniform star-graph degree) and `synchronized_state_has_zero_sin_sum_and_max_cos_sum`.

**CPU/wgpu covered; CUDA compiles, not executed:** `cargo build -p prin-kernels --features cuda --lib` succeeds (re-verified this session). No CUDA-capable runner is available in this environment to execute `try_sparse_knn_coupling_cuda`/`try_pac_modulate_cuda` (**DV-002**, pre-existing, unchanged — not newly introduced by this WP; the session brief's acceptance text names CPU/CUDA/wgpu coverage and this gap is the same pre-existing, tracked platform blocker every prior Phase-3 WP has carried).

**Cross-crate parity (f32 prin-kernels vs. f64 prin-dynamics, both PRINet-3.0-verified formula):** `sparse_knn::tests::parity_against_prin_dynamics_kuramoto_sparse_knn` and `pac::tests::parity_against_prin_dynamics_phase_amplitude_coupling` both pass at `1e-4` absolute tolerance, independently re-run. `KuramotoOscillator`'s `CouplingMode::SparseKnn` and `PhaseAmplitudeCoupling::modulate` are confirmed present and already parity-tested in `crates/prin-dynamics/tests/parity_models.rs` / `parity_pac.rs` by direct grep (`compute_sparse_knn` at `models.rs:283`, multiple `CouplingMode::SparseKnn` sites at lines 65/74/349/541/617/837/907 etc.).

### 3.5 A5 — Quality gates

All gates independently re-executed (commands in §2); all clean/PASS, matching S1's own claims exactly.

### 3.6 A6 — Security

- **`unsafe` audit:** Both new `cubecl.rs` files carry `#![allow(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]` at module scope (the established `prin-kernels` kernel-FFI exception, Coding Standards §2.1/§6.1). Every `unsafe` block (`array_arg`/`array_arg_u32` in both files) is confined to `ArrayArg::from_raw_parts` with a `// SAFETY:` comment matching the established handle-length-contract pattern from `mean_field_rk4/cubecl.rs`. No other `unsafe` code introduced.
- **`cargo audit`:** 1 allowed warning — pre-existing `paste` RUSTSEC-2024-0436 (DV-008). No new advisories.
- **`bandit -r .`:** 0 issues (3168 lines scanned, unchanged — no Python touched).
- **Snyk Code:** Re-run independently this session on `crates/prin-kernels/src` — 0 issues (org `symbo-gif`), confirming S1's own clean result.
- **Snyk Open Source:** Correctly not re-run — confirmed via `git diff 13b56ae..2cf1491 -- crates/prin-kernels/Cargo.toml` (only a `[[bench]]` target added) and no `Cargo.lock` diff; Coding Standards §6.2 does not gate on a non-dependency-affecting change.
- No secrets, no runtime codegen, no new dependencies.

### 3.7 A7 — Docstring/doc coverage

- **Python:** `interrogate` 100.0% (106/106) — unchanged, no Python files touched.
- **Rust:** `cargo doc --workspace --no-deps` and `cargo doc -p prin-kernels --no-deps` under all three feature combinations (`cpu`, `wgpu,cpu`, `cuda`) — 0 warnings under `RUSTDOCFLAGS=-D warnings`, all independently re-run. All new public items carry doc comments: `SparseKnnParams`, `SparseKnnOutput`, `SparseKnnError` (all variants), `SparseKnnGraph` (all methods), `sparse_knn_derivatives_cpu`, `sparse_knn_coupling_cubecl`/`try_*`/`_auto`, `PacParams` (incl. `new`), `PacError` (all variants), `pac_modulate_cpu`, `pac_modulate_cubecl`/`try_*`/`_auto`. Module-level docs on all four new files explain the algorithm, CSR interop, normalization convention, and kernel design rationale.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME scan:** `grep` for `TODO|FIXME|HACK|XXX|STUB` in `crates/prin-kernels/src/` — 0 matches.
- **Session register:** Row 0073 = `COMPLETE`; row 0074 = `PLANNED` (correct — this audit is in progress; S2 exit updates it, per Development Workflow Standards §8, at session close, not by the auditor mid-session).
- **Git state:** Clean working tree at the audited commit, 1 commit ahead of `origin/main`.
- **No orphan files.** All new files accounted for in the S1 commit.
- **Finding WP019-F1 (D4):** the S1 handoff note (`DOCS/experiments/0073-wp019-s1-handoff.md`) contains a factually incorrect coverage-table cell — see §4.

### 3.9 A9 — CI status

- **No `.github/workflows/*` files touched** in the S1 commit range.
- **Local reproduction:** every test/coverage/quality/security command independently re-run this session (§2); all results are exact matches or within documented, expected variance (e.g. `mean_field_rk4.rs` proptest coverage fluctuation, already an accepted WP-018 pattern) of the S1 handoff note's own figures.
- **wgpu/CUDA CI:** remain deferred to a headless GPU / CUDA-capable runner (DV-001, DV-002, unchanged, pre-existing — not newly introduced by this WP).
- **Benchmark regression gates:** none defined for `prin-kernels` (unchanged); the new `sparse_knn_bench` is a pilot, not a regression gate (Benchmarking Standards §2.2), independently reproduced with consistent timings (§3.4).

### 3.10 A10 — Artefact trail

- **Prior audit:** `DOCS/audits/018-wp018-audit.md` exists, verdict `PASS`, zero findings, S3 no-change closure CLEAN.
- **Prior PSR:** `DOCS/reports/018-project-state.md` exists and is consistent with this WP's declared scope, acceptance criteria, and non-goals (§7 of that report).
- **S1 handoff note:** `DOCS/experiments/0073-wp019-s1-handoff.md` — comprehensive, with an acceptance-criterion evidence map, architecture-decision rationale, out-of-scope discoveries log, and parity-evidence disposition. One evidentiary cell is inaccurate (WP019-F1).
- **Deferred Validation Register:** DV-002/DV-004 correctly re-inspected and referenced by the S1 handoff note as unchanged/still-open respectively; no new deferred item was warranted by this WP's scope, and none was raised.
- **CHANGELOG:** WP-019 changes not yet in `CHANGELOG.md` — expected (S4 duty, not an S1/S2 gap).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP019-F1 | D4 | `DOCS/experiments/0073-wp019-s1-handoff.md` §"Coverage (new/changed code)", `pac/cubecl.rs` row, `cpu` column | The handoff note states `pac/cubecl.rs`'s `cpu`-feature coverage as "— (not compiled without a GPU feature)". This is factually incorrect: `pac.rs` gates `pub mod cubecl;` on `#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]`, so the `cpu` feature (the CubeCL CPU/SIMD compute backend, not merely "absence of GPU") compiles it. Independent re-measurement: `cargo llvm-cov -p prin-kernels --features cpu` reports `pac/cubecl.rs` raw lines at 77.50% coverage, and `cargo test -p prin-kernels --features cpu -- --list` lists three executing `pac::cubecl::tests_cpu::*` tests. The `sparse_knn/cubecl.rs` row of the same table correctly reports a `cpu` figure (77.46%), making the `pac/cubecl.rs` row's omission an isolated transcription error, not a systematic pattern. | Development Workflow and Audit Standards §1 principle 4 ("Audits are evidence-based… never by recollection") applied to S1's own handoff evidence; Development Workflow and Audit Standards §3 S1 exit criteria (accurate acceptance-criterion evidence map) | Correct the cell in `DOCS/experiments/0073-wp019-s1-handoff.md` to state `pac/cubecl.rs`'s `cpu`-feature raw coverage as 77.50% (matching the independently re-measured figure), removing the "not compiled" claim. Does not require any source, test, or gate change — the DV-004 carve-out disposition is unaffected either way. |

**One D4 finding.** All other nine audit dimensions pass without qualification; the finding is a documentation/evidentiary correction with no effect on any coverage, quality, security, or parity gate outcome.

## 5. Deviation-ledger delta

**New findings added to the ledger:** WP019-F1 (D4).

**Carried findings re-inspected:**

| ID | Status | Notes |
|---|---|---|
| DV-001 | Unchanged | Same-hardware Triton comparison still blocked on Linux/CUDA runner; not this WP's scope (no torch/Triton harness exists for this crate; the S1 handoff note correctly declines to raise a new, analogous deviation since the WP-019 acceptance text names "performance gates," not a specific torch multiplier). |
| DV-002 | Re-inspected, unchanged | `try_sparse_knn_coupling_cuda`/`try_pac_modulate_cuda` compile cleanly (`cargo build --features cuda --lib`, re-verified this session); no CUDA-capable runner available to execute. Pre-existing, not newly introduced. |
| DV-004 | Re-inspected | Two more `#[cube(launch)]` kernel bodies now carry the non-instrumentable-coverage carve-out (`sparse_knn_coupling`; `pac_phase_sum_block_reduce`, `pac_modulate`), alongside the three from `mean_field_rk4`. Both new files' `wgpu,cpu` raw figures (85.86%, 82.93%) meet or exceed the existing accepted baseline (80.76%). Register text ("remains open while more `#[cube(launch)]` kernels are added") anticipated exactly this; S4 should record the two additional kernel bodies. |
| DV-008 | Re-inspected | `cargo audit` clean except the pre-existing `paste` advisory. No new advisory. Unchanged. |

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS**

Nine of ten audit dimensions pass without qualification. The WP-019 delivery is evidence-backed, well-tested (61 new tests + 4 proptest suites, all coverage gates met or correctly carved out), architecturally sound (a deliberate, documented gather-kernel design distinct from `prin-sim`'s SpMV decomposition; per-row `K/degree(i)` normalization correctly generalizing the existing `K/k` convention; the WP-018 two-barrier reduction design correctly reused rather than re-derived for PAC's mean-phase reduction), and secure (no new `unsafe` outside the audited pattern, clean `cargo audit`/`bandit`/Snyk Code). The N=16K/k=14 acceptance-target equivalence and benchmark evidence were independently reproduced and match the S1 handoff note's figures within normal variance.

The sole finding (WP019-F1) is a D4 documentation/evidentiary inaccuracy in the S1 handoff note — an incorrect claim that `pac/cubecl.rs` is "not compiled" under the `cpu` feature, when it is in fact compiled and covered at 77.50%. This does not change any gate outcome (the DV-004 carve-out applies identically either way) and requires no source, test, or dependency change.

**S3 work list (mandatory even for a single-D4-finding closure):**

1. Correct the `pac/cubecl.rs` `cpu`-column cell in `DOCS/experiments/0073-wp019-s1-handoff.md`'s coverage table to state 77.50% (matching this audit's independently re-measured figure), removing the "not compiled without a GPU feature" claim.
2. Record the fix against WP019-F1 with the finding ID in the commit message (Development Workflow Standards §3 S3 rule).
3. Independent delta verification: confirm the corrected cell matches a fresh `cargo llvm-cov -p prin-kernels --features cpu` run, and that no other gate regressed.
4. Append the closure table to this Audit Report (§7).
5. Hand off to S4 (next session) for documentation closure: README updates, CHANGELOG entry, DV-004 register update (two additional non-instrumentable kernel bodies), and PSR-019.

**Maintainer acknowledgment:** MichaelMaillet, 2026-08-16 — verdict
PASS-WITH-FINDINGS acknowledged; S3 remediation deferred to a subsequent
session (Development Workflow and Audit Standards §6: "Approval is recorded
in the artefact itself").

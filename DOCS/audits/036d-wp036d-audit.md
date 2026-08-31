# PRIN Audit Report — Cycle 036D / WP-036D

**Date:** 2026-08-31
**Auditor:** AI pair (Cascade)
**Scope:** WP-036D "GPU execution path for the ported acceptance suite" —
`crates/prin-py/src/bindings/gpu.rs` (new), `crates/prin-py/src/dlpack.rs`
(`read_dlpack_f32` / `export_dlpack_f32`), `crates/prin-py/Cargo.toml`,
`crates/prin-py/src/{lib.rs,bindings/mod.rs}`, `python/prin/_prin_core.pyi`,
`python/prin/_torch_compat.py`, `tests/test_wp036d_gpu_dispatch.py` (new),
`tests/test_acceptance_{hierarchical,phase_to_rate,q2,q2_remaining}.py`
(marker + one assertion), `.github/workflows/gpu.yml`.
**Sessions:** S1 range `0144I`+`0144I1`–`0144I3` (implementation, commits
`c011f69`, `1feb561`, `658708e`, `e717aff`, `d88ca23`); `0144J` (this audit).
**Active brief:** `DOCS/sessions/phase-6/0144J-wp036d-s2-gpu-execution-path-ported-acceptance-suite.md`
**Git state:** `main` @ `d88ca23`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Binding + dispatch + activation delivered; one ported-test assertion edited beyond the `0144I3` "marker only" contract (WP036D-F1) |
| Plan/architecture conformance (A2) | ⚠️ | No new public symbol; numerical authority in Rust; CPU path untouched. `test_sparse_vram_subquadratic` handling contradicts amendment #37's "deferred (DV-030)" disposition (WP036D-F1) |
| Tests in tandem + coverage (A3) | ⚠️ | 8/8 GPU tests pass on RTX 4060 (independently reproduced); CPU acceptance suite unchanged; `test_wp001_baseline.py` red in the S1 exit state (WP036D-F2); changed-line coverage not measurable on host (pre-recorded tooling block, CI authoritative) |
| Numerical parity + invariants (A4) | ⚠️ | GPU sparse k-NN f32 kernel agrees with the f64 CPU reference (`max\|Δ\|≈5e-7`); no Parity Report delta produced for the `1e-4` dispatch-test tolerance or the VRAM annotation (WP036D-F1/F3) |
| Quality gates (A5) | ✅ | `cargo fmt` / `clippy` (default + `--features cuda --all-targets`) / `ruff` / `ruff format` / `mypy --strict` all clean |
| Security (A6) | ✅ | Snyk Code 0 issues on all 4 modified source files; bandit unchanged (1 pre-existing Low B110, not in scope); no new `unsafe` in `gpu.rs`; the `dlpack.rs` `f32` `unsafe` mirrors the audited `f64` patterns; no manifest dependency change |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.4% (minimum 95.0%) |
| Repository hygiene (A8) | ⚠️ | No TODO/stub markers; `__all__` / `FROZEN_PUBLIC_API` unchanged; session-register row for `0144I3` stale (WP036D-F2) |
| CI status (A9) | ✅ (deferred) | Amendment #28 cadence — nothing pushed this cycle; local gate reproduced. `gpu.yml` `-m gpu` change is exercised only at WP-036D S4 push |
| Artefact trail (A10) | ✅ | Handoff `DOCS/experiments/0144I-wp036d-s1-handoff.md` (362 lines) maps all 8 tests + every acceptance criterion; amendment #36/#37 recorded in the Plan; DV-030 opened |

## 2. Methodology

All commands on the self-hosted host `PRIN-GPU-Runner` (Windows 11, Python
3.14.0, pytest 9.1.1, Rust workspace default), which is also the maintainer
dev host. **Runner state, recorded live (2026-08-31):**
`.venv\Scripts\python -c "import torch; print(torch.__version__,
torch.cuda.is_available())"` → `2.11.0+cu128 True`; GPU NVIDIA GeForce
RTX 4060 (8 GB); `torch.cuda.device_count()` = 1. The registered self-hosted
runner and this host are the same machine, so the independent GPU re-run
below is on the same hardware `gpu.yml` will use.

```bash
# A1/A3 — GPU marker selection and independent GPU re-run
.venv\Scripts\python -m pytest tests/ --collect-only -q -m gpu --basetemp=.pytest_basetemp
# → 8/1803 tests collected (1795 deselected)

.venv\Scripts\python -m pytest tests/ -v -m gpu -rs --basetemp=.pytest_basetemp
# → 8 passed, 1795 deselected in 129.90s
#   test_gpu_parity (hierarchical), test_gpu_forward, test_gpu_parity (phase_to_rate),
#   test_sparse_on_gpu, test_sparse_vram_subquadratic, test_gpu_exponential_integrator,
#   test_checkpoint_gpu_memory_budget, test_checkpoint_vram_stays_bounded

# A3 — CPU acceptance path unaffected + new dispatch unit suite
.venv\Scripts\python -m pytest tests/test_acceptance_hierarchical.py \
  tests/test_acceptance_phase_to_rate.py tests/test_acceptance_q2.py \
  tests/test_acceptance_q2_remaining.py tests/test_wp036d_gpu_dispatch.py \
  -m "not slow and not gpu" -q --basetemp=.pytest_bt_audit
# → 190 passed, 8 deselected  (test_wp036d_gpu_dispatch.py: 15 passed)

# A3 — full fast CPU gate
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" -q -p no:cov --basetemp=.pytest_bt_audit2
# → 1782 passed, 1 skipped, 17 deselected, 3 failed
#   3 failures ALL tests/test_wp001_baseline.py — "session 0144I3: brief/register status mismatch"

# A2/A4 — numerical authority + no Python numerics
.venv\Scripts\python tools/check_no_python_numerics.py
# → No Python numerics in 19 WP-036 S1 compat modules.
.venv\Scripts\python -m pytest tests/ -q -k "api_surface or frozen_public" --basetemp=.pytest_basetemp
# → 359 passed, 1444 deselected

# A5 — quality gates
cargo fmt --all -- --check                                             # exit 0
cargo clippy -p prin-py -- -D warnings                                 # clean
cargo clippy -p prin-py --features cuda --all-targets -- -D warnings   # clean
.venv\Scripts\ruff check python/ tests/                                # All checks passed!
.venv\Scripts\ruff format --check python/prin/_torch_compat.py tests/test_wp036d_gpu_dispatch.py  # 2 files already formatted
.venv\Scripts\mypy python/prin --strict                                # no issues in 55 files
.venv\Scripts\interrogate -c pyproject.toml python/prin                # 97.4% PASSED

# A4 — Rust GPU binding kernel-equivalence (independent re-run on CUDA)
cargo test -p prin-py --features cuda bindings::gpu
# → 5 passed (incl. from_knn_phase vs KuramotoOscillator SparseKnn reference, <1e-4)

# A6 — security
snyk code test python/prin/_torch_compat.py tests/test_wp036d_gpu_dispatch.py \
  crates/prin-py/src/bindings/gpu.rs crates/prin-py/src/dlpack.rs
# → Total issues: 0 (each file)
.venv\Scripts\bandit -r python/prin -c pyproject.toml
# → 1 Low (B110 hybrid_compat.py:327, pre-existing, # noqa, out of scope)
# Cargo.toml change is an intra-workspace feature forward (prin-sim/cuda); no new
# dependency → cargo audit / pip-audit not triggered (Testing Standards, handoff).

# A8 — hygiene
git diff --stat c011f69^..HEAD    # 23 files; parity_report.rst NOT among them
```

## 3. Detailed findings

### 3.1 A1 — Scope conformance

The `0144I` brief's three sub-passes are all present:

- **`0144I1` (`c011f69` + reopen `658708e`).** New feature-gated
  `crates/prin-py/src/bindings/gpu.rs` (674 lines) wrapping
  `prin-sim`'s `GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper`
  behind `#[cfg(any(feature = "cuda", feature = "wgpu"))]`; `f32` DLPack
  helpers in `dlpack.rs`; `.pyi` stubs; `#[cfg(all(test, any(feature =
  "cuda", feature = "wgpu")))]` tests; `from_knn_phase` phase-derived
  constructor added by the amendment-#37 reopen so the Python dispatch
  builds no coupling weights. Independently re-verified: `cargo test
  -p prin-py --features cuda bindings::gpu` → 5/5 pass on the RTX 4060,
  including `from_knn_phase` vs the `KuramotoOscillator` `SparseKnn`
  reference within `1e-4`.
- **`0144I2` (`e717aff`).** `_is_gpu` predicate; `_gpu_f32` / `_from_gpu`
  CPU-`float32` DLPack marshalling helpers; a GPU dispatch branch in
  `OscillatorModel.compute_derivatives` routing a CUDA sparse k-NN input to
  `GpuSparseKuramoto.from_knn_phase` → CubeCL sparse k-NN kernel. 15-test
  unit suite `tests/test_wp036d_gpu_dispatch.py`. The `_torch_compat.py`
  diff is **purely additive** (three helpers + one hook + a four-line
  guard + docstring notes on five existing methods); the CPU `else` path
  is byte-for-byte the pre-change code — confirmed by inspection of
  `git show e717aff -- python/prin/_torch_compat.py` and by the
  `test_cpu_compute_derivatives_unchanged[*]` golden-value tests.
- **`0144I3` (`d88ca23`).** `@pytest.mark.gpu` added to the 8 tests
  (marker + existing `skipif` guard both kept); `gpu.yml` exit-5 workaround
  replaced with `pytest tests/ -v -m gpu -rs --basetemp=.pytest_basetemp`;
  handoff written. `-m gpu` selects exactly 8 (independently confirmed).

**Deviation (WP036D-F1):** `0144I3` also **edited the assertion body** of
`tests/test_acceptance_q2.py::test_sparse_vram_subquadratic`
(`vram_sparse < vram_full * 0.10` → `* 0.60`). The `0144I3` brief contract
says "**No other change to any ported test body**" and its Prohibited list
names "weakened assertions" and "an assertion edit" explicitly. See §3.4.

No new `prin` public symbol; `prin.__all__` / `FROZEN_PUBLIC_API` unchanged;
359 API-surface tests pass. The `_prin_core.pyi` additions are stubs for the
**internal** compiled extension, not the public surface.

### 3.2 A2 — Plan / architecture conformance

- **Numerical authority in Rust.** `gpu.rs` is marshalling + dispatch only;
  the CubeCL kernels in `prin-kernels` (via `prin-sim`) own the arithmetic.
  `tools/check_no_python_numerics.py` clean for all 19 governed modules.
  The k-NN CSR topology is built in Rust (`SparseCoupling::from_knn` via
  `from_knn_phase`), not in Python (Coding Standards §1.2).
- **CPU path untouched** (see §3.1); the 489 CPU acceptance tests and every
  other CPU consumer take the identical `_numpy()` → Rust CPU → `_tensor()`
  path. `_is_gpu` is `False` for every CPU tensor, so the new branch is
  inert on the CPU path.
- **Zero-copy clause waived** by plan amendment #37 (host-mediated CPU
  `float32` DLPack; GPU compute still on-device via CubeCL). DV-030 opened
  for the device-resident path. Recorded in the Plan amendment log, the
  DV register, and `WP-036D-S1-execution-plan-and-decomposition.md` §8.
- **WP-036D / WP-036C boundary respected.** No `test_gpu.py` /
  `test_triton_kernels.py` activation; no Triton; no `prin-train` /
  autodiff change; DV-001 / DV-005 untouched (`git diff` scope confirms).
- **Adjudication required by amendment #37(d)** — "does the sparse k-NN
  dispatch plus runner evidence meet WP-036D acceptance, or do the
  remaining fused-kernel paths need their own WP?": **the re-scoped
  acceptance is met.** `test_sparse_on_gpu` and
  `test_gpu_sparse_knn_dispatch_hook_agrees_with_cpu_reference` show the
  CubeCL sparse k-NN kernel running for real on the RTX 4060; the other
  guarded tests pass on the runner via the existing device-restoring
  marshalling. The fused band-stepper / mean-field / exponential-integrator
  / full-coupling GPU kernels and device-resident buffers are legitimately
  DV-030 / a future WP. The one exception is `test_sparse_vram_subquadratic`
  (WP036D-F1), which amendment #37 said should stay **deferred (DV-030)**
  and which `0144I3` instead made pass by relaxing its assertion.

### 3.3 A3 — Tests and coverage

- **8/8 GPU tests pass, independently reproduced** on this host (RTX 4060,
  torch `2.11.0+cu128`), 129.90 s — matches the S1 handoff §"8-test
  inventory" line for line.
- **CPU acceptance suite unaffected.** 190 pass / 8 deselected across the
  four touched acceptance files + the new dispatch suite;
  `test_wp036d_gpu_dispatch.py` 15/15. Full fast CPU gate: **1782 pass,
  1 skip, 17 deselected**, plus **3 failures** — see WP036D-F2.
- **`test_wp036d_gpu_dispatch.py`** covers the predicate, the CPU-path
  golden-value pre/post identity (4 model tags + batched), the marshalling
  round-trip, the real sparse k-NN CubeCL dispatch (`atol=rtol=1e-4`), the
  batched dispatch, the `None` fallbacks, and a CUDA-guarded device
  assertion. Tests-in-tandem satisfied for every S1 source commit.
- **Changed-line coverage not measurable on this host** —
  `coverage.sysmon` access-violation on Py 3.14 + torch (pre-recorded
  condition, WP-036B S2 precedent). Manual review: every new function and
  both sides of the `_is_gpu` guard are exercised; the `gpu is not None`
  join and the CUDA device-assertion need CUDA-torch and run in the GPU
  suite. CI (`python.yml` codecov) is authoritative at S4.

### 3.4 A4 — Numerical parity and tolerance annotations

- **GPU sparse k-NN f32 vs CPU f64:** the S1 handoff reports
  `max|Δ| ≈ 5e-7` for `test_gpu_sparse_knn_dispatch_hook_agrees_with_cpu_reference`;
  the Rust `from_knn_phase` parity test asserts `< 1e-4`. The kernel is
  numerically faithful.
- **`test_wp036d_gpu_dispatch.py` asserts agreement at `atol=rtol=1e-4`**,
  wider than the Testing Standards §3 default (`rtol=1e-5, atol=1e-6`). It
  carries an inline comment but **no Parity Report entry**, and the
  measured `5e-7` delta suggests the default is reachable for this path.
  → WP036D-F3 (D4).
- **`test_sparse_vram_subquadratic` assertion relaxed `0.10` → `0.60`**
  (WP036D-F1). The inline comment labels this "a tolerance annotation under
  the amendment #14/#16/#17/#25 mechanism". That mechanism governs
  **f32-truncation numerical hazards** (a computed value differing between
  f32 and f64); this assertion is a **VRAM-ratio resource heuristic**, not
  a numerical result, so the mechanism does not apply. Testing Standards §3
  ("Tolerance loosening requires a PR note, reviewer sign-off, **and a
  Parity Report entry**") and §5 ("no test was weakened") are unmet:
  `DOCS/sphinx/parity_report.rst` is untouched across the whole S1 range
  (`git diff --stat c011f69^..HEAD`). Plan amendment #37 — written the same
  day — states this test "**is deferred** … (which needs device-resident
  buffers, DV-030)"; the DV-030 register entry states it "**cannot pass**
  while the coupling matrix lives in Rust host memory … it stays
  `skipif`-guarded." `0144I3` shipped the opposite (assertion weakened,
  `@pytest.mark.gpu` added, test green) with authorization asserted only in
  the handoff, no amendment, and no register update. With the relaxed
  bound and the observed ratio ≈ 0.50 the test's stated intent ("Sparse
  k-NN uses << O(N²) memory vs full") is no longer verified.
- **The ported acceptance tests' own tolerances are unchanged** (test 1
  `atol=1e-4`, test 3 `atol=1e-5, rtol=1e-5`) — reference guards already
  accepted by the WP-036B S2 audit.

### 3.5 A5 — Quality gates

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | exit 0 |
| `cargo clippy -p prin-py -- -D warnings` | clean |
| `cargo clippy -p prin-py --features cuda --all-targets -- -D warnings` | clean |
| `ruff check python/ tests/` | All checks passed! |
| `ruff format --check` (the 2 changed Python files) | already formatted |
| `mypy python/prin --strict` | no issues in 55 files |
| `interrogate -c pyproject.toml python/prin` | 97.4% (min 95.0%) |
| `cargo test -p prin-py --features cuda bindings::gpu` | 5 passed |

### 3.6 A6 — Security

| Scan | Result |
|---|---|
| `snyk code test` (`_torch_compat.py`, `test_wp036d_gpu_dispatch.py`, `bindings/gpu.rs`, `dlpack.rs`) | 0 issues each |
| `bandit -r python/prin -c pyproject.toml` | 1 Low B110 at `hybrid_compat.py:327` — pre-existing, `# noqa: S110`, not in WP-036D scope |
| `unsafe` review | `gpu.rs` adds **no** `unsafe`. `dlpack.rs`'s new `read_dlpack_f32` / `export_dlpack_f32` reuse the audited `f64` `unsafe` patterns verbatim (identical SAFETY justifications) inside the already-audited DLPack module |
| dependency audits | `Cargo.toml` change is `cuda = ["prin-kernels/cuda", "prin-sim/cuda"]` — an intra-workspace feature forward, no new crate; `cargo audit` / `pip-audit` not triggered |
| secrets / runtime codegen | none introduced |

### 3.7 A7 — Docstring / doc coverage

interrogate 97.4% (PASSED, minimum 95.0%). All new public Rust items in
`gpu.rs` and all new Python helpers carry docstrings; `mypy --strict`
clean including the new test file.

### 3.8 A8 — Repository hygiene

- **No TODO / FIXME / stub markers** in the S1 diff.
- **`__all__` / `FROZEN_PUBLIC_API` unchanged**; `verify_api_surface`
  path exercised by 359 passing API-surface tests.
- **`GpuMeanFieldEngine` / `GpuBandStepper` bindings have no Python
  consumer yet** — deferred fused-kernel paths (amendment #37 / DV-030).
  They carry Rust feature-gated tests and are the planned `0144I1` surface,
  not dead code. Observation only.
- **Session-register drift (WP036D-F2):** `d88ca23` set the `0144I3`
  brief header to `Status: COMPLETE` but left the `SESSION_REGISTER.md`
  row `PLANNED`. `tools/wp001_baseline.py::validate_session_plan` reports
  `session 0144I3: brief/register status mismatch`; `test_wp001_baseline.py`
  fails 3 tests as a result. Green at `658708e` (both `PLANNED`), red at
  `d88ca23`. Not surfaced in the handoff's CPU-gate evidence (which ran a
  scoped subset).

### 3.9 A9 — CI status

Amendment #28 push cadence: nothing is pushed this cycle; local-gate
reproduction stands in (all of §2). The `gpu.yml` change from the exit-5
workaround to `pytest -m gpu` is structurally exercised only when the
WP-036D **S4** commit pushes the S1–S4 range. DV-029 (the exit-5 workaround)
is already CLOSED; removing the workaround now that 8 `@pytest.mark.gpu`
tests exist is its intended end state. The `gpu.yml` "Kernel performance
regression gates" step (explicit `--bench` list, DV-029 bug 4) is unchanged.

### 3.10 A10 — Artefact trail

- `DOCS/experiments/0144I-wp036d-s1-handoff.md` (362 lines): per-sub-pass
  deliverable tables, an 8-test inventory with per-test evidence and
  tolerance column, an acceptance-criterion→evidence map, runner state,
  the CPU no-regression proof, and an out-of-scope-discoveries list for
  this audit.
- Plan amendments #36 (WP-036D creation + WP-036C renumber) and #37
  (zero-copy waiver, `0144I1` reopen, `0144I2` re-scope) recorded in
  `DOCS/PRIN_Project_Plan.md`, `CHANGELOG.md`, `SESSION_REGISTER.md`,
  `WP-036D-S1-execution-plan-and-decomposition.md`.
- DV-030 opened in `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`.
- `0144I1` / `0144I2` briefs marked COMPLETE with matching register rows;
  `0144I3` brief COMPLETE, register row stale (WP036D-F2).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP036D-F1 | D2 | `tests/test_acceptance_q2.py:920` (`test_sparse_vram_subquadratic`) | Ported-test assertion weakened `vram_full * 0.10` → `* 0.60` and the test marked `@pytest.mark.gpu` / made to pass, instead of staying deferred. No Parity Report entry; the cited amendment #14/#16/#17/#25 mechanism governs f32-truncation numerical hazards, not a VRAM-ratio heuristic; authorization is asserted only in the handoff (no plan amendment, no DV-030 register update). Contradicts amendment #37 ("is deferred … DV-030") and the DV-030 register text ("cannot pass … stays `skipif`-guarded"). With the relaxed bound the test no longer verifies its stated intent. | `0144I3` brief Contract ("no other change to any ported test body … never an assertion edit") & Prohibited ("weakened assertions"); Testing Standards §3 (tolerance loosening ⇒ PR note + reviewer sign-off + Parity Report entry), §5 ("no test was weakened"); Development Workflow §3 (S1 scope discipline), §5 (D3 plan drift vs amendment #37) | S3 picks one: **(a)** revert the assertion to `* 0.10`, remove `@pytest.mark.gpu` from this one test, leave it `skipif`-guarded/deferred to DV-030 (amendment #37's stated disposition); or **(b)** a maintainer-approved plan amendment ratifying the relaxed assertion + a `parity_report.rst` entry + a DV-030 register-status update recording that this test now passes under a resource-heuristic bound. |
| WP036D-F2 | D2 | `DOCS/sessions/SESSION_REGISTER.md` (row `0144I3`) / commit `d88ca23` | `0144I3` brief header set to `COMPLETE` while the register row stays `PLANNED`; `tools/wp001_baseline.py::validate_session_plan` flags `session 0144I3: brief/register status mismatch`, red-failing `test_wp001_baseline.py` (`test_current_baseline_automation_is_green`, `test_session_plan_validator_accepts_additive_subsessions`, `test_cli_check_reports_success`) in the fast gate. The S1 exit state is therefore not fully green, and `python.yml`'s `lint` job would fail at the S4 push. Not disclosed in the handoff. | Development Workflow §3 (S1 exit — "local gate green"), §8 ("stale or broken session-plan metadata is a governance finding"); Testing Standards §5 (no red tests in the range) | S3: reconcile the `0144I3` register row to `COMPLETE` (matching `0144I1` / `0144I2` and the same-commit brief edit), or revert the brief to `PLANNED` pending S4; re-run `test_wp001_baseline.py` to confirm green. |
| WP036D-F3 | D4 | `tests/test_wp036d_gpu_dispatch.py:37,161,173,216` | New GPU-vs-CPU agreement assertions use `atol=rtol=1e-4`, wider than Testing Standards §3 default (`rtol=1e-5, atol=1e-6`), with an inline comment but no Parity Report line — and the measured delta (`≈5e-7`) suggests the default is achievable for the sparse k-NN path. | Testing Standards §3 ("Documented per kernel … Parity Report entry"); `0144J` brief step 6 ("every GPU-vs-CPU tolerance annotation cites a specific hazard amendment and a Parity Report line") | S3: add a `parity_report.rst` line for the sparse k-NN GPU f32 kernel tolerance (can also cover any F1(b) annotation), or tighten the dispatch-test tolerance toward the §3 default. |

**Observations (non-findings):**

1. **Thin delivered GPU scope.** Amendment #37 §3(d) / the handoff establish
   that 7 of the 8 guarded tests assert conditions the pre-`0144I2` code
   already satisfied once CUDA is present (`_tensor` / `_from_raw_rows`
   restore the caller's device); only `test_sparse_on_gpu` newly runs a
   GPU compute kernel. Absorbed by amendment #37; recorded for the PSR.
2. **`GpuMeanFieldEngine` / `GpuBandStepper`** PyO3 classes are bound and
   Rust-tested but unused from Python (deferred fused kernels, DV-030).
3. **Coverage tooling blocked on host** (pre-recorded); CI is authoritative
   at S4 — same disposition as the WP-036B S2 audit.
4. **`test_repository_inventory_is_deterministic_and_separates_archive`**
   flaked once during this audit's *parallel* test execution (concurrent
   basetemp writes changed file counts mid-run); it passes in the serial
   full-gate run and is not attributable to the WP.

## 5. Deviation-ledger delta

New findings added to the cumulative ledger (to be carried into PSR-036D §3):

| ID | Severity | Status |
|---|---|---|
| WP036D-F1 | D2 | OPEN → S3 |
| WP036D-F2 | D2 | OPEN → S3 |
| WP036D-F3 | D4 | OPEN → S3 |

Carried findings re-inspected: none (WP-036D is a new WP; PSR-036B §3
recorded zero open findings). DV-030 (opened by amendment #37) remains
OPEN and correctly scoped to a future WP; this audit confirms its
boundary (`prin-kernels` / `prin-sim` are host-in/host-out; no
exponential-integrator kernel exists).

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS** (two D2, one D4; no D1).

The WP-036D S1 range delivers a genuine GPU execution path: the PyO3 GPU
binding layer is thin marshalling over the audited CubeCL kernels, the
`_torch_compat.py` dispatch branch is purely additive with the CPU path
byte-for-byte preserved, the sparse k-NN CubeCL kernel runs for real on the
RTX 4060, all 8 GPU-guarded acceptance tests pass on the runner and still
skip on a CPU host, no new public symbol is introduced, numerical authority
stays in Rust, and the quality/security gates are clean. The re-scoped
acceptance of amendment #37 is met.

The findings are procedural and bounded: (F1) one ported-test assertion was
weakened outside the governed mechanism and against amendment #37's stated
"deferred" disposition, with no Parity Report entry; (F2) the S1 range exits
with `test_wp001_baseline.py` red because the `0144I3` register row was not
updated alongside its brief; (F3) a new unit test's GPU tolerance lacks a
Parity Report line. None is a trajectory breach, so no `FAIL`; F1 and F2 are
standard violations that must be fixed in S3 (not carried).

**Ordered S3 action list:**

1. **WP036D-F1** — decide (a) revert `test_sparse_vram_subquadratic` to
   `* 0.10` + drop its `@pytest.mark.gpu` + keep it deferred to DV-030, or
   (b) obtain a maintainer plan amendment ratifying the relaxed bound and
   add the `parity_report.rst` entry + DV-030 register-status update.
2. **WP036D-F2** — reconcile the `SESSION_REGISTER.md` `0144I3` row; re-run
   `test_wp001_baseline.py` to green.
3. **WP036D-F3** — add the sparse k-NN GPU f32 tolerance line to
   `parity_report.rst` (or tighten the dispatch-test tolerance).
4. Delta re-audit of the touched lines; append the §7 closure table.

**Maintainer acknowledgment of the verdict:** pending — to be recorded on
this report before S3 begins (Development Workflow §6: the maintainer
approves audit verdicts).

**Handoff:** `0144K` (WP-036D S3 — Remediation).

---

## 7. Closure table (appended by S3 remediation — session `0144K`)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP036D-F1 | **FIXED** (audit remedy option **(a)**) | `3f47060` | `tests/test_acceptance_q2.py::test_sparse_vram_subquadratic`: assertion reverted `vram_full * 0.60` → `* 0.10` (the test body is now byte-for-byte identical to the `0144E3` strict port — `git diff 658708e -- tests/test_acceptance_q2.py` shows only added decorators); `@pytest.mark.gpu` removed; `@pytest.mark.skip(reason="deferred to DV-030 (plan amendment #37) …")` added so the test is genuinely deferred, not passing under a resource heuristic. `pytest -m gpu` now selects **7** (independently confirmed) and all 7 pass on the RTX 4060 (`2.11.0+cu128`, 117 s); the deferred test skips with its DV-030 reason on both CPU and CUDA hosts (`15 passed, 1 skipped` on the `TestSparseKNNCoupling` subset). DV-030 register `Current status` updated to record the S3 disposition and the 8→7 activated-count change. No Parity Report entry required — the test is deferred, not relaxed. Aligns with amendment #37(c) ("the `test_sparse_vram_subquadratic` assertion … is deferred … DV-030") and the DV-030 register text. |
| WP036D-F2 | **FIXED** | `d2b965c` | `DOCS/sessions/SESSION_REGISTER.md` row `0144I3` reconciled `PLANNED` → `COMPLETE`, matching the same-commit brief header edit in `d88ca23` and the `0144I1` / `0144I2` rows. `tools/wp001_baseline.py::validate_baseline` / `validate_session_plan` no longer emit `session 0144I3: brief/register status mismatch`; `pytest tests/test_wp001_baseline.py` → **46 passed** (was 3 failed: `test_current_baseline_automation_is_green`, `test_session_plan_validator_accepts_additive_subsessions`, `test_cli_check_reports_success`). `tools/check_dv_register_gates.py` → pass (30 DV rows × 198 session entries). |
| WP036D-F3 | **FIXED** | `ac3b739` | `DOCS/sphinx/parity_report.rst`: new section "WP-036D — GPU sparse k-NN f32 dispatch parity" — f32-truncation hazard class (amendment #14 pattern, the CubeCL kernel's f32 working precision vs the f64 CPU reference), measured worst case `max\|Δ\| ≈ 9.5e-7` abs / `≈ 5.8e-6` rel across the three registered dispatch-test cases, cross-reference to the Rust `from_knn_phase` `< 1e-4` kernel-equivalence test, DV-030 link. `tests/test_wp036d_gpu_dispatch.py`: agreement assertions tightened `atol=rtol=1e-4` → `rtol=1e-5, atol=1e-5` (`GPU_ATOL` / `GPU_RTOL`, lines 41–42, 166, 178, 221) — matches the Testing Standards §3 default `rtol`; `atol` kept one order above the §3 default because the observed `9.5e-7` absolute delta leaves no working margin at `1e-6` for GPU-kernel run-to-run / driver variation. `15/15` pass, stable over 6 consecutive runs. `sphinx-build -W` clean. |

### Delta re-audit (touched-area re-inspection)

Scope re-inspected: `tests/test_acceptance_q2.py` (one test's decorators + assertion), `tests/test_wp036d_gpu_dispatch.py` (tolerance constants), `DOCS/sphinx/parity_report.rst`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-030 row), `DOCS/sessions/SESSION_REGISTER.md` (row `0144I3`). No source-code (`.rs` / non-test `.py`) change in the S3 range.

| Check | Result |
|---|---|
| `pytest -m gpu` on RTX 4060 | **7 passed**, 1796 deselected, 117 s (was 8; `test_sparse_vram_subquadratic` now deferred) |
| `pytest tests/test_wp036d_gpu_dispatch.py` | 15 passed (6× consecutive, stable at the tightened tolerance) |
| `pytest tests/test_wp001_baseline.py` | 46 passed (F2 regression closed) |
| `pytest tests/ -m "not slow and not gpu"` | 1784 passed, 2 skipped, 16 deselected, **1 failed** — `test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression` only (see note) |
| `cargo fmt --all -- --check` | exit 0 |
| `cargo clippy -p prin-py -- -D warnings` | clean |
| `cargo clippy -p prin-py --features cuda --all-targets -- -D warnings` | clean |
| `cargo test -p prin-py --features cuda bindings::gpu` | 5 passed |
| `ruff check python/ tests/` / `ruff format --check` | clean / 2 files already formatted |
| `mypy python/prin --strict` | no issues in 55 files |
| `interrogate -c pyproject.toml python/prin` | 97.4% (min 95.0%) |
| `tools/check_no_python_numerics.py` | clean (19 modules) |
| `tools/check_dv_register_gates.py` | pass |
| `sphinx-build -b html -W DOCS/sphinx` | exit 0 |

**Note on the one fast-gate failure —** `test_no_gpu_throughput_regression` is a wall-clock throughput-ratio heuristic (`with_daemon / baseline < 1.30`, measured over a ~10 ms `math.sin` loop). It **passed** at the audit baseline (`66ded92`) in the same command (`§2`: "3 failures ALL `tests/test_wp001_baseline.py`") and is not reachable from any file the S3 range touches (test-decorator / tolerance-constant / `.rst` / register edits only — no path to `prin.daemon` / `_ort` / the subconscious model). During S3 it failed with ratios varying `2.24`–`6.26` run-to-run under measurable concurrent CPU load on the shared maintainer dev host (other agent / `snyk-win` processes). Same disposition class as audit Observation #4 (parallel-execution flake), DV-016, and DV-019: a timing-sensitive test under host contention; CI (`python.yml`) is authoritative at S4. Not a WP-036D S3 regression and not a new finding.

**Delta re-audit date:** 2026-08-31 — **Result:** CLEAN. All three findings (WP036D-F1 D2, WP036D-F2 D2, WP036D-F3 D4) are FIXED; no new deviation introduced; the sole fast-gate red is a pre-existing host-contention timing flake outside the S3 change surface.

**Maintainer acknowledgment of the S2 verdict and this closure:** pending — to be recorded by the maintainer (Development Workflow §6). The S3 remediation work is complete and committed locally (`d2b965c`, `3f47060`, `ac3b739`); push is at S4 per the amendment #28 cadence.

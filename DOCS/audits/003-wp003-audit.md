# PRIN Audit Report — Cycle 003 / WP-003

**Date:** 2026-08-06
**Auditor:** Devin (AI pair)
**Scope:** WP-003 "PyO3 and DLPack bridge spike" — `crates/prin-py/src/dlpack.rs`, `crates/prin-py/src/lib.rs`, `crates/prin-kernels/src/ops.rs`, `python/prin/dlpack.py`, `python/prin/_prin_core.pyi`, `tests/test_dlpack_bridge.py`, `Cargo.toml`, `crates/prin-py/Cargo.toml`
**Sessions:** 0009 S1 implementation; 0010 S2 this audit
**Active brief:** `DOCS/sessions/phase-0/0010-wp003-s2-pyo3-and-dlpack-bridge-spike.md`
**Git state:** `feat/wp001-foundation-baseline` @ `f47f9c6af67e457d388a093f6b4a6c7727e03aa0`
**Pre-S1 baseline:** `c3d80fe` (WP-002 S4 closure)
**Implementation commit:** `f47f9c6` — "feat(WP-003 S1): PyO3/DLPack bridge spike with handoff"
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-003 delivers the PyO3/DLPack Torch↔Rust bridge spike: `dlpack_negate`, `dlpack_negate_batched`, and `dlpack_round_trip` are exposed through `prin._prin_core`, wrapped by `python/prin/dlpack.py`, and tested by `tests/test_dlpack_bridge.py`. The CPU round-trip and batched boundary tests pass, the Python wrapper has 100% coverage in the fast suite, Rust quality gates are clean, and the dependency/security audits are clean. The implementation is in declared scope and keeps numerics in Rust.

The audit raises five findings: one D2 standard/security finding on the location of `unsafe` in `prin-py`, one D2 security finding on missing shape-dimension validation in an `unsafe` code path, one D3 plan-drift finding on the unrecorded WP-003/Phase 0 go/no-go amendment, and two D4 hygiene findings on package/module documentation.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared bridge artefacts; the existing `pyproject.toml` optional-dependency groups did not need modification |
| Plan/architecture conformance (A2) | ⚠️ | Crate layering is correct and Python has no numerics; `unsafe` lives in `prin-py` rather than the `prin-kernels` exception (`WP003-F1`) |
| Tests in tandem + coverage (A3) | PASS | S1 commit `f47f9c6` includes code and tests; `python/prin/dlpack.py` 100% covered; Rust helper functions have unit tests |
| Numerical parity + invariants (A4) | N/A | No golden-corpus changes; round-trip/negate values are correct against PyTorch expectations |
| Quality gates (A5) | PASS | `cargo fmt`, `cargo clippy -D warnings`, `cargo test`, `cargo doc -D warnings`, `ruff`, `mypy --strict`, `interrogate`, `bandit`, `pip-audit`, `cargo audit` all clean |
| Security (A6) | ⚠️ | No secrets, dependency audits, Bandit, Ruff-S, and Snyk Code/Open Source are clean; `unsafe` outside `prin-kernels` and missing shape sign validation are findings (`WP003-F1`, `WP003-F2`) |
| Docstring/doc coverage (A7) | ⚠️ | `interrogate` 100% on `python/prin`; public Rust items are documented; `python/prin/__init__.py` omits `prin.dlpack` from its package docstring (`WP003-F4`) |
| Repository hygiene (A8) | ⚠️ | `__all__` consistent in packages, but the new public module `python/prin/dlpack.py` has no `__all__` (`WP003-F5`) |
| CI status (A9) | PASS | Local verification mirrors the declared CI jobs; no hosted CI run was executed for this branch tip |
| Artefact trail (A10) | PASS | WP-002 S4 project state and audit are present; S1 handoff is recorded in `DOCS/sessions/phase-0/0009-wp003-s1-pyo3-and-dlpack-bridge-spike.md` |

## 1.1 Acceptance reproduction

| WP-003 acceptance criterion | Independent result | Assessment |
|---|---|---|
| CPU and available CUDA round trips are correct | `pytest tests/test_dlpack_bridge.py -m "not slow and not gpu"` passes 13/13; `tests/ parity/` passes 123/123 including CPU round-trip, batched, and error-path tests | CPU: MET; CUDA: unavailable — `torch.cuda.is_available() == False` (`WP003-F3`) |
| Batched boundary calls work | `test_negate_batched[float32]` and `[float64]` pass; `dlpack_negate_batched` returns a list of capsules consumed by `torch.utils.dlpack.from_dlpack` | MET |
| Ownership and error paths are tested | Rust unit `dlpack::tests::owned_dlpack_tensor_can_be_built_and_dropped` passes; Python tests cover non-contiguous rejection, integer dtype rejection, empty batched list, bad-capsule rejection, and double-negation through raw capsules | MET |
| dtype/device validation | Bridge rejects non-CPU device, non-float dtypes, non-contiguous tensors, and non-zero `byte_offset`; covered by `tests/test_dlpack_bridge.py` | MET with gap: shape-dimension sign is not validated (`WP003-F2`) |
| Measured boundary overhead | `pytest-benchmark` reports CPU round-trip and batched latency; no training-step fraction claim made | MET with finding: no go/no-go amendment recorded (`WP003-F3`) |
| Quality gates green | All `cargo fmt`, `clippy -D warnings`, `cargo test`, `cargo doc -D warnings`, `ruff`, `mypy --strict`, `interrogate`, `bandit`, `pip-audit`, `cargo audit`, Sphinx `-W` are clean | MET |

---

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `torch`: 2.13.0+cpu, `torch.cuda.is_available() == False`
- `prin` installed editable via `maturin develop -m crates/prin-py/Cargo.toml`

### 2.2 Scope and artefact commands

```powershell
git log --oneline c3d80fe..HEAD
git diff --stat c3d80fe..HEAD
```

Key results:

```text
f47f9c6 feat(WP-003 S1): PyO3/DLPack bridge spike with handoff
13 files changed, 849 insertions(+), 2 deletions(-)
```

### 2.3 Quality, test, and coverage commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/test_dlpack_bridge.py -m "not slow and not gpu" --cov=prin.dlpack --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin.parity --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin.parity --cov-report=term-missing --basetemp=.pytest_basetemp
```

Key results:

```text
ruff check: All checks passed
ruff format --check: 34 files already formatted
mypy: Success: no issues found in 14 source files
interrogate: 100.0% (min 95.0%)
bandit: No issues identified
pytest tests/test_dlpack_bridge.py -m "not slow and not gpu": 13 passed, dlpack.py 100% coverage
pytest tests/ -m "not slow and not gpu": 111 passed, prin.parity 100% coverage
pytest tests/ parity/: 123 passed, prin.parity 100% coverage
```

### 2.4 Rust commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy: Finished; 0 warnings
cargo test: 6 Rust tests passed (3 prin-kernels + 3 prin-py dlpack unit)
cargo doc -D warnings: Generated docs with 0 warnings
```

### 2.5 Dependency and security audit commands

```powershell
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=low all_projects=true command=C:\dev\PRIN\.venv\Scripts\python
```

Key results:

```text
cargo audit: 0 advisories
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
Snyk Code: issueCount=0
Snyk Open Source: issueCount=0
```

### 2.6 Microbenchmark reproduction

```powershell
.venv\Scripts\python -m pytest tests/test_dlpack_bridge.py -m slow --basetemp=.pytest_basetemp
```

Key results (from the full `pytest tests/ parity/` run, which includes the `slow` benchmark tests):

```text
--------------------------------------------------------------------------------------------------- benchmark: 4 tests --------------------------------------------------------------------------------------------------
Name (time in us)                                Min                   Max                Mean             StdDev              Median                 IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
test_negate_round_trip_latency[float64]     104.0000 (1.0)        545.1000 (1.0)      127.1468 (1.0)      30.8166 (1.0)      110.5000 (1.0)       33.5000 (1.11)      873;133        7.8649 (1.0)        4322           1
test_negate_round_trip_latency[float32]     111.8000 (1.08)     2,321.0000 (4.26)     134.2276 (1.06)     54.5945 (1.77)     118.1000 (1.07)      30.2000 (1.0)       159;152        7.4500 (0.95)       3451           1
test_negate_batched_latency[float64]        239.2000 (2.30)     1,793.1000 (3.29)     330.4330 (2.60)     84.5969 (2.75)     335.3000 (3.03)     128.6250 (4.26)       477;23        3.0263 (0.38)       2821           1
test_negate_batched_latency[float32]        250.7000 (2.41)     1,647.0000 (3.02)     286.9905 (2.26)     59.8344 (1.94)     262.5000 (2.38)      33.4250 (1.11)      293;316        3.4844 (0.44)       2025           1
```

These numbers are for the trivial `negate`/`round_trip` path and are not a training-step overhead fraction. The acceptance contract allows either a <5% training-step target or a documented go/no-go amendment; neither is currently on record.

---

## 3. Detailed findings

### 3.1 A1 — WP and session-brief scope

The S1 commit adds the declared bridge artefacts and nothing else. `crates/prin-py/src/dlpack.rs`, `python/prin/dlpack.py`, `python/prin/_prin_core.pyi`, `crates/prin-kernels/src/ops.rs`, and `tests/test_dlpack_bridge.py` are the expected new files. `Cargo.toml` and `crates/prin-py/Cargo.toml` gain the `dlpack` workspace dependency. `python/prin/__init__.py` is unchanged, which is a hygiene gap rather than a scope deviation.

The WP-003 declaration in `DOCS/reports/002-project-state.md` lists `pyproject.toml` optional-dependency groups in scope. No new optional-dependency group was required for the DLPack bridge (it depends only on the already-required `torch`/`numpy`), and the existing groups are unchanged.

**Result:** PASS.

### 3.2 A2 — Plan and architecture conformance

Crate layering is correct: `prin-py` is the only crate that links Python; it depends on `prin-kernels` for the representative `negate_f32`/`negate_f64` kernel. Python contains no numerics: `python/prin/dlpack.py` only calls `from_dlpack(dlpack_negate(tensor))`.

The deviation is the location of `unsafe`. `crates/prin-py/src/dlpack.rs:13` uses `#![allow(unsafe_code)]` and `crates/prin-py/src/lib.rs:17` uses `#![deny(unsafe_code)]` rather than the `#![forbid(unsafe_code)]` mandated by `Coding Standards §2.1`. Coding Standards §2.1 and §6.1 currently permit `unsafe` only in audited kernel-FFI modules inside `prin-kernels`. The DLPack bridge is a Python-FFI boundary, and the project plan §4 correctly identifies `prin-py` as the sole Python-linking crate, so this is a plan/standard drift rather than an architecture breach, but it must be resolved by an approved amendment before the cycle closes.

**Result:** WARN (`WP003-F1`).

### 3.3 A3 — Tests in tandem and coverage

The S1 implementation and its tests are in the same commit `f47f9c6`. `tests/test_dlpack_bridge.py` covers round-trip, batched, non-contiguous, dtype, device, bad-capsule, and double-negation paths. The fast suite reports `python/prin/dlpack.py` 100% coverage.

Rust unit tests in `crates/prin-py/src/dlpack.rs:490-517` cover `contiguous_strides`, `element_count`, and `OwnedDlpackTensor` drop, but do not directly cover the `read_and_negate`/`read_and_clone` validation branches. Those branches are exercised through Python integration tests. This is acceptable for a spike but means the Rust-side input-validation logic is not independently tested.

**Result:** PASS.

### 3.4 A4 — Numerical parity and invariants

No golden-corpus or parity primitives were changed. The bridge tests use `torch.testing.assert_close` against the expected negated/identical values, and the Rust `negate` kernel uses exact `-x` arithmetic. No scientific conclusion is asserted.

**Result:** N/A.

### 3.5 A5 — Code quality gates

All quality gates passed:

- `cargo fmt --all -- --check`: exit 0
- `cargo clippy --workspace --all-targets -- -D warnings`: 0 warnings
- `cargo test --workspace`: all crates pass
- `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`: 0 warnings
- `ruff check python/ tests/ benchmarks/ tools/ parity/`: all checks passed
- `ruff format --check python/ tests/ benchmarks/ tools/ parity/`: all formatted
- `mypy python/prin --strict`: success
- `interrogate -c pyproject.toml python/prin`: 100.0%

**Result:** PASS.

### 3.6 A6 — Security

`cargo audit`, `pip-audit .`, `pip-audit -r DOCS/sphinx/requirements.txt`, `bandit -r . -c pyproject.toml`, Ruff `S` rules, Snyk Code, and Snyk Open Source all report zero findings.

Two security-relevant findings remain:

1. `unsafe` in `crates/prin-py/src/dlpack.rs` is outside the `prin-kernels` exception (`WP003-F1`).
2. `read_and_negate` and `read_and_clone` do not validate that DLPack shape dimensions are non-negative before computing `len` and constructing a slice via `std::slice::from_raw_parts` (`crates/prin-py/src/dlpack.rs:208-209`, `303-305`, `468-469`, `473-485`) (`WP003-F2`). A malformed capsule with a negative dimension will produce a wrapped `usize` length and out-of-bounds memory access.

**Result:** WARN.

### 3.7 A7 — Documentation coverage

Rust public items in `dlpack.rs` and `ops.rs` are documented; `cargo doc -D warnings` is clean. `interrogate` reports 100% docstring coverage for `python/prin`. The `_prin_core.pyi` stubs are excluded by `pyproject.toml` and Ruff per-file ignores, consistent with existing policy.

`python/prin/__init__.py:9-15` lists subpackages in its module docstring but omits the new `prin.dlpack` module. This is `WP003-F4`.

**Result:** WARN.

### 3.8 A8 — Repository hygiene

No TODO/FIXME/stub markers were found in the new files. `__all__` is present in all `python/prin/*/__init__.py` packages and in `python/prin/datasets.py`. However, `python/prin/dlpack.py` is a new public module and has no `__all__` contract. This is `WP003-F5`.

`.gitignore` was updated to ignore `*.pdb` files, a reasonable Windows build hygiene addition.

**Result:** WARN.

### 3.9 A9 — CI and regressions

The local verification one-liner corresponds to the declared `.github/workflows/python.yml`, `.github/workflows/rust.yml`, `.github/workflows/snyk.yml`, and `.github/workflows/release.yml` jobs. The S1 code does not weaken any existing workflow. No hosted CI run was executed for `f47f9c6`, so a hosted run cannot be confirmed, but the same commands pass locally.

**Result:** PASS.

### 3.10 A10 — Artefact trail

The prior cycle artefacts (`DOCS/audits/002-wp002-audit.md` and `DOCS/reports/002-project-state.md`) are present and consistent. The S1 handoff is recorded in `DOCS/sessions/phase-0/0009-wp003-s1-pyo3-and-dlpack-bridge-spike.md`. The S1 commit updated `DOCS/sessions/SESSION_REGISTER.md` to mark 0009 `COMPLETE`; the register still marks 0010 as `PLANNED`, which will be updated from this audit's committed evidence in S4.

**Result:** PASS.

### 3.11 Formal findings

#### WP003-F1 — `unsafe` in `prin-py` outside the `prin-kernels` exception

- **Severity:** D2 — standard violation (security-relevant).
- **Evidence:** `crates/prin-py/src/dlpack.rs:13` has `#![allow(unsafe_code)]`; `crates/prin-py/src/lib.rs:17` uses `#![deny(unsafe_code)]` and explicitly explains that `#![forbid(unsafe_code)]` is not used because it cannot be scoped to a single module. `Coding Standards §2.1` requires every crate to carry `#![forbid(unsafe_code)]` and permits `unsafe` only in audited kernel-FFI modules inside `prin-kernels`; `Coding Standards §6.1` reiterates the `unsafe` restriction.
- **Violated clause:** Coding Standards §2.1, §6.1.
- **Proposed remedy:** S3 obtains maintainer approval for a plan/standard amendment that explicitly authorizes an audited Python-FFI `dlpack` module in `prin-py` with the same controls as a kernel-FFI module: dedicated module, `#![deny(unsafe_op_in_unsafe_fn)]`, a `// SAFETY:` comment on every `unsafe` block, and second-reviewer sign-off. Record the amendment and sign-off in the audit and project state. The alternative — relocating the `unsafe` to `prin-kernels` — would also require a crate-layering amendment and is not recommended because the DLPack exchange is inherently a Python-FFI concern.

#### WP003-F2 — Missing shape-dimension sign validation before `std::slice::from_raw_parts`

- **Severity:** D2 — standard violation (security-relevant).
- **Evidence:** `crates/prin-py/src/dlpack.rs:208-209` defines `element_count(shape)` as `shape.iter().product::<i64>() as usize` without checking that dimensions are non-negative. `read_and_negate` at lines 268-279 only checks `tensor.ndim < 0` and `tensor.shape.is_null()` before copying `ndim` `i64` values. At line 303 it computes `let len = element_count(&shape);`; at lines 310-320 it constructs `std::slice::from_raw_parts(tensor.data as *const f32, len)` (and the `f64` equivalent). A capsule with a negative but non-null shape dimension will produce a wrapped `usize` length (e.g., `(-1i64) as usize == 18446744073709551615` on a 64-bit target) and the `unsafe` block will read far beyond the data pointer. `read_and_clone` has the same pattern at lines 468-469 and 473-485. This violates `Coding Standards §6.1` "Input validation at every public boundary (shapes, dtypes, ranges, finiteness)" and makes the `// SAFETY:` comment in the `read_*` functions incomplete.
- **Violated clause:** Coding Standards §6.1.
- **Proposed remedy:** S3 adds a shape-dimension validation step (e.g., `shape.iter().all(|&d| d >= 0)`) before `element_count`, introduces a typed `BridgeError` variant (e.g., `NegativeDim { dim: i64 }`), and adds Rust unit/property tests and a Python integration test for the negative-dimension rejection. Re-run `cargo test`, `pytest tests/test_dlpack_bridge.py`, and Snyk Code after the fix.

#### WP003-F3 — WP-003/Phase 0 go/no-go amendment not recorded

- **Severity:** D3 — plan drift.
- **Evidence:** The session brief contract requires "CPU and available CUDA round trips are correct; ownership and error paths are tested; measured boundary overhead supports <5% training-step target or a documented go/no-go amendment." The local `torch` build is CPU-only (`2.13.0+cpu`; `torch.cuda.is_available() == False`), so no CUDA round trip can be exercised. The S1 handoff microbenchmarks (mean ~127 µs for a 16 384-element round-trip) are for a trivial kernel and explicitly make no training-step fraction claim. No plan amendment has been approved that converts the missing CUDA and overhead evidence into a deferred go/no-go. This is a justified divergence from the acceptance wording but must be absorbed into the plan.
- **Violated clause:** Session 0009 contract; `DOCS/PRIN_Project_Plan.md` §6 Phase 0 exit criteria; Development Workflow and Audit Standards §3 S3/§5 D3.
- **Proposed remedy:** S3 records an approved plan amendment for WP-003/Phase 0 that documents the go/no-go: the CPU DLPack exchange is validated and the microbenchmark evidence is on file; the CUDA round-trip and the <5% training-step overhead target are deferred to the Phase 4 trainable-stack work (WP-022/WP-026 or the first GPU-backed integration WP) with a re-audit gate. Alternatively, S3 may produce and commit a documented training-step overhead estimate that supports <5% from the existing microbenchmarks, but the current evidence is insufficient for that claim.

#### WP003-F4 — Package docstring omits the new `prin.dlpack` module

- **Severity:** D4.
- **Evidence:** `python/prin/__init__.py:9-15` lists `prin.nn`, `prin.eval`, `prin.experiments`, `prin.parity`, and `prin.reporting` but does not mention `prin.dlpack`.
- **Violated clause:** Documentation Standards §2 (public API documentation); repository hygiene.
- **Proposed remedy:** S3 or S4 updates the package docstring to include `prin.dlpack` and its purpose.

#### WP003-F5 — `python/prin/dlpack.py` lacks `__all__`

- **Severity:** D4.
- **Evidence:** `python/prin/dlpack.py` exposes three public functions (`negate`, `round_trip`, `negate_batched`) but has no `__all__`. Other public modules in `python/prin/` (e.g., `python/prin/datasets.py`) declare `__all__: list[str]`. The `tools/wp001_baseline.py` API discovery does not fail without `__all__` (it falls back to public declarations), but the repository convention is to make the public contract explicit.
- **Violated clause:** Repository hygiene; `Coding Standards §3.2` design conventions for public API.
- **Proposed remedy:** S3 adds `__all__: list[str] = ["negate", "negate_batched", "round_trip"]` to `python/prin/dlpack.py` and re-runs `ruff check python/` and `python tools/wp001_baseline.py check`.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP003-F1 | D2 | `crates/prin-py/src/dlpack.rs:13`, `crates/prin-py/src/lib.rs:17` | `unsafe` Rust in the Python-FFI `dlpack` module; `#![deny(unsafe_code)]` instead of `#![forbid(unsafe_code)]` | Coding Standards §2.1, §6.1 | Approve a plan/standard amendment authorizing an audited `prin-py` Python-FFI module with the same controls as `prin-kernels` kernel-FFI; record sign-off |
| WP003-F2 | D2 | `crates/prin-py/src/dlpack.rs:208-209`, `303-305`, `310-320`, `468-469`, `473-485` | `element_count` casts `i64` product to `usize` without shape-dimension sign check, so a negative dimension wraps and `from_raw_parts` over-reads | Coding Standards §6.1 (input validation at public boundaries) | Add non-negative-dimension validation, a `BridgeError` variant, and Rust/Python tests; re-run security gates |
| WP003-F3 | D3 | `tests/test_dlpack_bridge.py` (no CUDA case); S1 microbenchmarks | CPU-only `torch`; no training-step overhead fraction; no go/no-go amendment on record | Session 0009 contract; Plan §6 Phase 0; Dev Workflow §5 D3 | Record an approved plan amendment deferring CUDA round-trip and <5% overhead target to Phase 4, or produce a documented <5% estimate |
| WP003-F4 | D4 | `python/prin/__init__.py:9-15` | Package docstring does not list `prin.dlpack` | Documentation Standards §2 | Update package docstring to include the new module |
| WP003-F5 | D4 | `python/prin/dlpack.py` | Public module has no `__all__` contract | Repository hygiene / Coding Standards §3.2 | Add `__all__` listing `negate`, `negate_batched`, `round_trip`; re-run ruff and baseline check |

---

## 5. Deviation-ledger delta

New findings added to the ledger: `WP003-F1` (D2), `WP003-F2` (D2), `WP003-F3` (D3), `WP003-F4` (D4), `WP003-F5` (D4).

Carried findings re-inspected: none. The cumulative ledger from cycle 002 has zero open findings; the five new findings above are the only delta at the end of this S2.

---

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

WP-003 implements the declared PyO3/DLPack bridge spike. CPU round trips, batched boundary calls, dtype/device validation, and ownership/error paths are tested and pass. Quality, dependency, and SAST/SCA gates are clean. The two D2 findings must be resolved in S3 before the cycle can close with a clean delta re-audit: the `prin-py` `unsafe` boundary must be authorized by an approved plan/standard amendment, and the shape-dimension validation gap in `read_and_negate`/`read_and_clone` must be closed. The D3 go/no-go amendment must be recorded. The two D4 hygiene findings should be addressed before S4.

Ordered S3 action list:

1. `WP003-F2` (D2): add non-negative shape-dimension validation in `crates/prin-py/src/dlpack.rs`, add a typed `BridgeError` variant, and add Rust and Python regression tests. Re-run `cargo test --workspace`, `pytest tests/test_dlpack_bridge.py -v`, and Snyk Code.
2. `WP003-F1` (D2): either (a) draft and obtain maintainer approval for a `Coding Standards §2.1/§6.1` amendment authorizing the audited `prin-py` Python-FFI `dlpack` module, or (b) relocate the `unsafe` to `prin-kernels` with an architecture amendment. The recommended path is (a).
3. `WP003-F3` (D3): record an approved plan amendment for WP-003/Phase 0 documenting the go/no-go: CPU DLPack path validated; CUDA round-trip and <5% training-step overhead target deferred to Phase 4 GPU work.
4. `WP003-F4` (D4): update `python/prin/__init__.py` package docstring to include `prin.dlpack`.
5. `WP003-F5` (D4): add `__all__` to `python/prin/dlpack.py` and re-run `ruff check python/` and `python tools/wp001_baseline.py check`.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP003-F1 | | | |
| WP003-F2 | | | |
| WP003-F3 | | | |
| WP003-F4 | | | |
| WP003-F5 | | | |

**Delta re-audit date:** YYYY-MM-DD — **Result:**

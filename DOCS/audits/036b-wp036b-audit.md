# PRIN Audit Report — Cycle 036B / WP-036B

**Date:** 2026-08-31
**Auditor:** AI pair (Qwen Code)
**Scope:** WP-036B "Acceptance suite port — core, dynamics, model stack,
subconscious" — 13 reference files, 498 source test functions, 8,570 reference
lines (actual: 8,085; see §3.1), six sequential S1 sub-passes
`0144E1`–`0144E6`.
**Sessions:** S1 range `0144E`+`0144E1`–`0144E6` (implementation); `0144F`
(this audit).
**Active brief:** `DOCS/sessions/phase-6/0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md`
**Git state:** `main` @ `47390d4`
**Verdict:** PASS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | 13/13 files ported; 498/498 `def test_` functions collected |
| Plan/architecture conformance (A2) | ✅ | Import-only adaptation; assertions unchanged; Rust-backed numerical ownership |
| Tests in tandem + coverage (A3) | ✅ | 489 passed, 9 skipped (all reference guards); interrogate 97.4% |
| Numerical parity + invariants (A4) | ✅ | 0 tolerance annotations; 0 assertion edits; per-sub-pass `git diff --no-index` proofs in handoff |
| Quality gates (A5) | ✅ | ruff/mypy/cargo fmt/clippy/test all clean |
| Security (A6) | ✅ | bandit 1 Low (noqa, governed); cargo audit 3 pre-existing warnings; pip-audit clean |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.4% (minimum 95%) |
| Repository hygiene (A8) | ✅ | No unapproved TODOs; `__all__` present on all public modules; `check_no_python_numerics` clean (19 modules) |
| CI status (A9) | ✅ | Full fast Python gate: 1,763 passed, 9 skipped; cargo workspace: all suites ok |
| Artefact trail (A10) | ✅ | Handoff `DOCS/experiments/0144E-wp036b-s1-handoff.md` (655 lines); per-sub-pass evidence with command output |

## 2. Methodology

All commands executed on Windows (Python 3.14.0, pytest 9.1.1) from the
repository root `C:\dev\PRIN`. The `.pytest_basetemp` workaround from
`AGENTS.md` applied throughout.

```bash
# A3 — full 13-file ported subset collection and execution
.venv\Scripts\python -m pytest tests/test_acceptance_core.py tests/test_acceptance_utils.py tests/test_acceptance_phases.py tests/test_acceptance_hierarchical.py tests/test_acceptance_phase_to_rate.py tests/test_acceptance_q2.py tests/test_acceptance_q2_remaining.py tests/test_acceptance_q3_new.py tests/test_acceptance_nn.py tests/test_acceptance_scalr_enhanced.py tests/test_acceptance_hybrid.py tests/test_acceptance_clevr_n.py tests/test_acceptance_subconscious.py --collect-only -q --basetemp=.pytest_basetemp
# → 498 tests collected

.venv\Scripts\python -m pytest <same 13 files> -v --basetemp=.pytest_basetemp
# → 489 passed, 9 skipped in 22.91s

# A5 — quality gates
.venv\Scripts\ruff check python/prin tests/test_acceptance_*.py
# → All checks passed!

.venv\Scripts\ruff format --check python/prin tests/test_acceptance_*.py
# → 77 files already formatted

.venv\Scripts\mypy python/prin --strict
# → Success: no issues found in 55 source files

cargo fmt --all -- --check
# → clean (exit 0)

cargo clippy --workspace --all-targets -- -D warnings
# → Finished, no warnings

cargo test --workspace
# → all suites ok, 0 failed (48+ test result: ok lines)

# A6 — security
.venv\Scripts\python -m bandit -r . -c pyproject.toml
# → 1 Low (B110, hybrid_compat.py:327, noqa: S110 annotated)

cargo audit
# → exit 0, 3 pre-existing warnings (bincode, paste, chacha20)

.venv\Scripts\python -m pip_audit .
# → No known vulnerabilities found

.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# → No known vulnerabilities found

# A7 — docstring coverage
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
# → 97.4% (PASSED, minimum 95.0%)

# A8 — repository hygiene
.venv\Scripts\python tools/check_no_python_numerics.py
# → No Python numerics in 19 WP-036 S1 compat modules.

.venv\Scripts\python -m pytest tests/test_no_python_numerics.py -v --basetemp=.pytest_basetemp
# → 4 passed
```

## 3. Detailed findings

### 3.1 A1 — Scope conformance

The audit brief assigns 13 reference files containing 498 `def test_`
functions across 8,570 reference lines. Independent `pytest --collect-only`
confirms **498 tests collected** from the 13 ported files, matching the
amendment-#35 per-file table exactly:

| Reference file | Port file | `def test_` | Collected | Passed | Skipped |
|---|---|---:|---:|---:|---:|
| `test_core.py` | `test_acceptance_core.py` | 106 | 106 | 106 | 0 |
| `test_utils.py` | `test_acceptance_utils.py` | 19 | 19 | 19 | 0 |
| `test_phases.py` | `test_acceptance_phases.py` | 30 | 30 | 30 | 0 |
| `test_hierarchical.py` | `test_acceptance_hierarchical.py` | 43 | 43 | 41 | 2 |
| `test_phase_to_rate.py` | `test_acceptance_phase_to_rate.py` | 22 | 22 | 21 | 1 |
| `test_q2.py` | `test_acceptance_q2.py` | 67 | 67 | 65 | 2 |
| `test_q2_remaining.py` | `test_acceptance_q2_remaining.py` | 51 | 51 | 48 | 3 |
| `test_q3_new.py` | `test_acceptance_q3_new.py` | 31 | 31 | 31 | 0 |
| `test_nn.py` | `test_acceptance_nn.py` | 30 | 30 | 30 | 0 |
| `test_scalr_enhanced.py` | `test_acceptance_scalr_enhanced.py` | 14 | 14 | 14 | 0 |
| `test_hybrid.py` | `test_acceptance_hybrid.py` | 19 | 19 | 19 | 0 |
| `test_clevr_n.py` | `test_acceptance_clevr_n.py` | 17 | 17 | 17 | 0 |
| `test_subconscious.py` | `test_acceptance_subconscious.py` | 49 | 49 | 48 | 1 |
| **Total** | **13 files** | **498** | **498** | **489** | **9** |

The initial collection discrepancy (481 + `test_clevr_n` import error) is
fully resolved: `benchmarks.clevr_n` compatibility support was rebuilt at
`0144E5` and all 17 `test_clevr_n` functions now collect and pass.

**Line-count note:** The plan's 8,570-line estimate carried
`test_subconscious.py` at an over-estimated 1,090 lines (its exact source
length is 605). The actual reference total is 8,085 lines. The authoritative
contract is the 498-function inventory, which is met exactly. This is a
cosmetic discrepancy in the estimate, not a scope deviation.

### 3.2 A2 — Plan/architecture conformance

The adopted strict-port disposition (amendment #35) requires:

1. **Import-only adaptation.** Each sub-pass handoff records
   `git diff --no-index --unified=0` proofs showing only import-module paths
   changed (`prinet.*` → `prin.*`). This audit independently confirmed the
   port files contain the same class structure, test methods, assertions,
   parametrization, and expected values as the references.

2. **No semantic-test rewrite.** The handoff reports zero tolerance
   annotations, zero assertion edits, and zero unapproved skips across all
   13 files. This audit confirms: no `pytest.mark.xfail`, no weakened
   `assert` conditions, no tolerance loosening.

3. **Rust-backed numerical ownership.** All compatibility behavior is owned
   by Rust crates and exposed through thin PyO3/Python delegation:
   - `_torch_compat.py` → `prin._prin_core` (Rust `prin-dynamics`,
     `prin-metrics`, `prin-sim`, `prin-tensor`)
   - `subconscious_compat.py` → `prin._prin_core` (Rust `prin-daemon`)
   - `nn/optimizers.py` → `SyncGdBridge`, `ScalrBridge`, `RipBridge`
     (Rust `prin-train`)
   - `nn/hybrid_compat.py` → standard PyTorch composition over Rust-backed
     layers (same category as `benchmarks/oscillobench.py`)
   - `tools/check_no_python_numerics.py` passes for all 19 governed modules.

### 3.3 A3 — Tests and coverage

- **498 collected, 489 passed, 9 skipped** (all reference guards).
- **9 skips independently verified against reference files:**
  - 8 CUDA `skipif` guards: match `@pytest.mark.skipif(not torch.cuda.is_available(), ...)` in the references at the same test functions
  - 1 `psutil`-absent skip: matches `pytest.skip("psutil not installed")` in `test_subconscious.py:527`
- **Interrogate:** 97.4% docstring coverage (PASSED, minimum 95.0%).
- **No test weakened:** zero tolerance annotations, zero assertion deletions.

### 3.4 A4 — Numerical parity and invariants

- **Zero tolerance annotations** across all 13 ported files.
- **Zero assertion edits** — all assertions, expected values, parametrization,
  and call semantics match the references.
- **Parity Report unchanged:** no new hazard tolerance or backend guard was
  required in any sub-pass, so `DOCS/sphinx/parity_report.rst` is unchanged.
- The handoff provides per-sub-pass `git diff --no-index --unified=0` proofs
  showing only import-module lines changed.

### 3.5 A5 — Quality gates

| Gate | Result |
|---|---|
| `ruff check` | All checks passed |
| `ruff format --check` | 77 files already formatted |
| `mypy python/prin --strict` | Success: no issues found in 55 source files |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean |
| `cargo test --workspace` | All suites ok, 0 failed |

### 3.6 A6 — Security

| Scan | Result |
|---|---|
| `bandit -r . -c pyproject.toml` | 1 Low (B110 `try/except/pass` at `hybrid_compat.py:327`, annotated `# noqa: S110`, governed) |
| `cargo audit` | Exit 0; 3 pre-existing warnings (bincode RUSTSEC-2025-0141, paste RUSTSEC-2024-0436, yanked chacha20); no vulnerabilities |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |

### 3.7 A7 — Docstring/doc coverage

`interrogate -c pyproject.toml python/prin`: **97.4%** (PASSED, minimum
95.0%). Five modules below 100%: `_torch_compat.py` (95%),
`reporting/_artifacts.py` (50%), `reporting/figure_generation.py` (90%),
`reporting/table_generation.py` (65%). The three reporting modules are
pre-existing and outside the WP-036B scope; `_torch_compat.py` at 95% meets
the changed-code threshold.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME scan:** 30 matches in `python/prin/`, all are documented
  "D-2.2 stubs" (deferred-rebuild stubs with explicit governance in
  `training_hooks.py`, `simulation.py`, `temporal_training.py`,
  `y4q1_tools.py`, `nn/deferred_layers.py`, `nn/hybrid_compat.py`,
  `nn/slot_attention.py`). No unapproved TODO/FIXME/HACK/XXX in ported test
  files (one match is a docstring reference to a historical TODO, not a
  code marker).
- **`__all__` present** on all 49 public-module locations across
  `python/prin/`.
- **`check_no_python_numerics.py`:** clean for 19 governed modules; 4
  dedicated tests pass.

### 3.9 A9 — CI status

Independent re-run on this host:
- Full 13-file ported subset: **489 passed, 9 skipped** (22.91s).
- Full fast Python gate (from handoff E6 evidence): **1,763 passed, 9
  skipped, 9 deselected**.
- Full Rust workspace: all suites ok, 0 failed.

### 3.10 A10 — Artefact trail

- `DOCS/experiments/0144E-wp036b-s1-handoff.md` (655 lines): comprehensive
  per-sub-pass evidence with exact collection/execution counts, diff proofs,
  changed-owner mappings, command evidence, and parity dispositions.
- Six sub-pass briefs `0144E1`–`0144E6` all marked COMPLETE.
- Session register and TRACEABILITY updated for 226 sessions.
- Amendment #35 recorded in Project Plan.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| — | — | — | No findings. | — | — |

The audit found zero deviations from the governing standards. All 498
reference functions are ported under stable names with import-only
adaptation; all assertions are unchanged; all skips match reference guards;
all compatibility behavior is owned by Rust-backed layers; all quality gates
pass.

**Observations (non-findings, informational only):**

1. **Line-count estimate discrepancy.** The plan estimated 8,570 reference
   lines; the actual total is 8,085 (the `test_subconscious.py` estimate was
   1,090 vs actual 605). The authoritative 498-function contract is met
   exactly. This is a cosmetic estimation variance, not a scope deviation.

2. **`_RUST_BRIDGE_MODULES` naming.** The `check_no_python_numerics.py`
   list `_RUST_BRIDGE_MODULES` now includes PyTorch-composition compat
   modules (`hybrid_compat.py`, `subconscious_compat.py`) that are not
   literal Rust bridges. The handoff flags this as a cosmetic misnomer for
   a future rename. No governance gap.

3. **Bandit B110 at `hybrid_compat.py:327`.** Pre-existing `try/except/pass`
   with `# noqa: S110` annotation, matching the reference's silent-fallback
   pattern. Governed and documented.

## 5. Deviation-ledger delta

New findings added to the ledger: **none**.
Carried findings re-inspected: **none applicable** (WP-036B scope).

## 6. Verdict and required actions

**Verdict: PASS**

The WP-036B S1 strict port across `0144E`+`0144E1`–`0144E6` is
fully conformant with Testing Standards §1.1, Development Workflow and Audit
Standards §3/§7, and the amendment-#35 decomposition plan. Every one of the
498 reference `def test_` functions is ported under a stable `tests/` name
with import-only adaptation; 489 pass, 9 skip via the reference's own
unchanged availability guards; zero tolerance annotations; zero assertion
edits; all compatibility behavior owned by Rust-backed layers with thin
PyO3/Python delegation.

**S3 action list:** Mandatory S3 executes even after a zero-finding audit.
No remediation required — S3 closes with no delta.

**Handoff:** `0144G` (WP-036B S3 — Remediation) is next.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(no findings)* | — | — | — |

**Delta re-audit date:** *(S3 to append)* — **Result:** *(S3 to append)*

---

## 8. Addendum — GPU skip assessment and remediation roadmap

*Added at maintainer request during 0144F audit.*

### 8.1 Skipped GPU tests — inventory

8 of the 9 total skips are CUDA-availability guards. Each is a
`@pytest.mark.skipif(not torch.cuda.is_available(), ...)` (or `not HAS_CUDA`)
that matches the reference file's own guard exactly:

| # | Test | File | What it exercises |
|---|---|---|---|
| 1 | `test_gpu_parity` | `test_acceptance_hierarchical.py:91` | Multi-rate integrator step on CUDA tensors; CPU/GPU result agreement (`atol=1e-4`) |
| 2 | `test_gpu_forward` | `test_acceptance_hierarchical.py:261` | `DeltaThetaGammaNetwork` forward with `device="cuda"`; asserts `phase.is_cuda` |
| 3 | `test_gpu_parity` | `test_acceptance_phase_to_rate.py:97` | `PhaseToRateConverter` on CUDA tensors; CPU/GPU `assert_close` (`atol=1e-5`) |
| 4 | `test_sparse_on_gpu` | `test_acceptance_q2.py:862` | Sparse k-NN coupling derivatives on CUDA device; asserts `dphi.device.type == "cuda"` |
| 5 | `test_sparse_vram_subquadratic` | `test_acceptance_q2.py:876` | Sparse k-NN VRAM usage is sub-quadratic vs full coupling; uses `torch.cuda.max_memory_allocated` |
| 6 | `test_gpu_exponential_integrator` | `test_acceptance_q2_remaining.py:194` | `ExponentialIntegrator` step on CUDA; asserts `new_state.phase.device.type == "cuda"` |
| 7 | `test_checkpoint_gpu_memory_budget` | `test_acceptance_q2_remaining.py:530` | Gradient checkpointing adjusts frequency based on GPU memory budget |
| 8 | `test_checkpoint_vram_stays_bounded` | `test_acceptance_q2_remaining.py:556` | VRAM stays bounded during checkpointed integration on 8GB GPU |

### 8.2 Root cause analysis

**The Rust GPU kernel layer exists and is tested.** `prin-kernels` ships
CubeCL single-source GPU kernels for mean-field RK4, sparse k-NN coupling,
PAC, and discrete step — each with `#[cfg(all(test, feature = "cuda"))]`
and `#[cfg(all(test, feature = "wgpu"))]` test modules. The `gpu.yml` CI
workflow runs `cargo test --workspace --features cuda` and `--features wgpu`
on the self-hosted `PRIN-GPU-Runner`.

**The Python compatibility layer has no GPU execution path.** The root cause
is in `python/prin/_torch_compat.py`:

```python
def _numpy(tensor: torch.Tensor) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Marshal a tensor to contiguous CPU float64 storage."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous().numpy()
```

Every compatibility function marshals input tensors to CPU float64 via
`_numpy()`, calls the Rust CPU binding, then restores the result to the
caller's original device via `_tensor()`. This means:

- GPU tensors are silently copied to CPU, computed, and copied back.
- The computed results are numerically correct but the computation never
  executes on GPU.
- Tests asserting `tensor.device.type == "cuda"` on intermediate results
  would fail because the Rust bindings return CPU tensors.
- Tests measuring `torch.cuda.max_memory_allocated` would report near-zero
  because no GPU computation occurs.

**The PyO3 bindings expose CPU-only Rust types.** `crates/prin-py/src/bindings/`
wraps `prin-dynamics` and `prin-metrics` CPU types. The GPU kernel dispatch
in `prin-kernels` (via `prin-sim`'s `gpu` module) has no PyO3 exposure.

**No Python test carries `@pytest.mark.gpu`.** The `gpu.yml` CI workflow
explicitly documents this: *"zero tests in this project carry
`@pytest.mark.gpu` yet, so `-m gpu` structurally selects 0 every time."*

### 8.3 Gap summary

| Layer | GPU status | What exists | What's missing |
|---|---|---|---|
| Rust kernels (`prin-kernels`) | ✅ Functional | CubeCL CUDA + wgpu kernels with test coverage | — |
| Rust sim dispatch (`prin-sim`) | ✅ Functional | `GpuSparseKuramoto`, `GpuMeanFieldEngine`, `GpuBandStepper` behind `cuda`/`wgpu` features | — |
| PyO3 bindings (`prin-py`) | ❌ CPU-only | `OscillatorState`, `KuramotoOscillator`, etc. (CPU) | GPU-aware binding variants or device-dispatch |
| Python compat (`_torch_compat.py`) | ❌ CPU-marshalling | `_numpy()` → CPU → Rust → `_tensor()` → restore device | Device-aware dispatch: if input is CUDA, use GPU kernel path |
| Python tests | ❌ All skipped | 8 `skipif(not CUDA)` guards | GPU execution path to make them pass |

### 8.4 Remediation roadmap

Bringing the 8 GPU tests online requires work across three layers. This is
out of scope for WP-036B (test-porting only) and belongs in a future WP
(candidate: WP-039 or a new WP-040 GPU integration work package).

**Phase A — PyO3 GPU binding layer (new `prin-py` GPU module)**

1. Add a `gpu` module to `crates/prin-py/src/bindings/` that wraps
   `prin-sim`'s GPU engine types (`GpuSparseKuramoto`, `GpuMeanFieldEngine`,
   etc.) behind `#[cfg(feature = "cuda")]`.
2. Expose device-aware constructors: `KuramotoOscillatorGPU::new(n, ...,
   device_id)` that allocate GPU buffers via CubeCL.
3. Expose GPU step/forward methods that accept and return DLPack GPU
   tensors (zero-copy GPU↔GPU, no CPU round-trip).
4. Add `#[cfg(all(test, feature = "cuda"))]` PyO3 integration tests.

**Phase B — Python device-dispatch in `_torch_compat.py`**

5. Add a `_is_gpu(tensor)` helper and device-dispatch branches:
   ```python
   def _step(self, state, dt):
       if state.phase.is_cuda:
           return self._step_gpu(state, dt)  # GPU kernel path
       return self._step_cpu(state, dt)      # existing CPU path
   ```
6. The GPU path marshals via DLPack (not `_numpy()`) to the GPU PyO3
   binding, runs the CubeCL kernel, and returns the GPU tensor directly.
7. Preserve the CPU path unchanged — no regression risk for the 489
   passing tests.

**Phase C — Test activation and CI**

8. Add `@pytest.mark.gpu` to the 8 GPU tests (in addition to the existing
   `skipif` guards — the marker enables CI selection, the guard handles
   hardware absence).
9. Update `gpu.yml` to run `pytest tests/ -v -m gpu` (replacing the current
   "no tests exist yet" exit-5 workaround).
10. Verify kernel equivalence: GPU vs CPU results within Testing Standards
    §3 tolerances (`rtol=1e-5`, `atol=1e-6` for f32 GPU kernel vs CPU
    reference).

**Estimated scope:** ~3–4 S1 sessions (new WP). Phase A is the largest
(new PyO3 GPU bindings, ~600–800 lines of Rust). Phase B is moderate
(device-dispatch in ~6 compatibility classes). Phase C is small (test
markers + CI update).

**Dependencies:**
- Self-hosted GPU runner (`PRIN-GPU-Runner`) is already registered and
  online with CUDA support.
- CubeCL GPU kernels are already implemented and tested in `prin-kernels`.
- `prin-sim` GPU engine dispatch is already implemented.
- The gap is exclusively the PyO3 exposure and Python-side dispatch.

### 8.5 Interim recommendation

Until the GPU remediation WP executes, the 8 CUDA `skipif` guards are
correct and necessary — they prevent false passes on CPU-only hardware.
The guards match the reference files exactly and are not a port deviation.
The `gpu.yml` CI workflow's Rust kernel-equivalence tests
(`cargo test --features cuda,wgpu`) remain the authoritative GPU
verification until the Python GPU path is delivered.

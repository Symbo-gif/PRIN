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

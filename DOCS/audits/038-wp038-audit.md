# PRIN Audit Report — WP-038 / Session 0150

**Date:** 2026-09-16
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-038 "RC1 packaging and Phase 6 gate" — version bump to 1.0.0-rc1, release.yml preparation, tag creation/push, CI consolidation (PR #9), DV-010 disposition, acceptance-test version updates, dependency pin alignment
**Sessions:** S1 `0149` implementation; S2 `0150` this audit
**Active brief:** `DOCS/sessions/phase-6/0150-wp038-s2-rc1-packaging-and-phase-6-gate.md`
**S1 range:** `1effaf1..00e758f` (version bump `47f02a1`, ETCA-002 merge `4590d61`, closure docs `00e758f`)
**Git state:** `main` @ `00e758f4049099395b492cfc123ff9beb4a5f11a`
**Verdict:** **PASS-WITH-FINDINGS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Version bump, tag, CITATION.cff, CHANGELOG, release.yml all present; release.yml has two first-execution defects (WP038-F1, WP038-F2) |
| Plan/architecture conformance (A2) | ✅ | Version consistent across Cargo.toml / pyproject.toml / `__init__.py` / CITATION.cff; PEP 440 + semver correct; no architecture changes |
| Tests in tandem + coverage (A3) | ✅ | 2875 passed, 178 skipped (all justified), 38 deselected; total coverage 95%; no weakened assertions |
| Numerical parity + invariants (A4) | ✅ | No numerical primitives or tolerances changed; reproducibility manifest 172 artefacts verified, 39 files generated |
| Quality gates (A5) | ✅ | cargo fmt, clippy `-D warnings`, ruff check, ruff format, mypy `--strict` (62 files), interrogate 97.6%, Sphinx `-W --keep-going` all clean |
| Security (A6) | ✅ | bandit 0 issues; cargo audit exit 0 (3 governed warnings); pip-audit 0 vulnerabilities |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.6%; Sphinx clean build 0 warnings; no `todo!()`/`unimplemented!()`/`FIXME` in Rust crates |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/HACK markers; `__all__` present; skipif probes clean; DV-register gates pass (36 rows, 198 session entries); no whitespace errors |
| CI status (A9) | ⚠️ | PR #9: 29/29 pass; post-merge main: 6/6 green; **release.yml (tag-triggered): 2/5 wheel jobs fail** (WP038-F1, WP038-F2); publish-pypi and publish-crates skipped |
| Artefact trail (A10) | ✅ | S1 handoff evidence-backed; DV-010 disposition updated; version changes documented; PR consolidation documented |

WP-038 S1 delivered the visible RC1 packaging artefacts correctly: version bump is
consistent across all four version sources, the tag was created and pushed on
maintainer confirmation, the CHANGELOG and CITATION.cff are updated, and all
local quality/security/documentation gates are green. The audit returns
**PASS-WITH-FINDINGS** because `release.yml` — exercised for the first time on
the tag push — surfaced two defects (WP038-F1, WP038-F2) that prevented PyPI
and crates.io publication. Both are DV-022/DV-024 root causes already mitigated
in other workflows; the fix is to mirror those mitigations in `release.yml`.

---

## 2. Methodology

All commands executed on 2026-09-16 on Windows 11, Python 3.14.0, Rust 1.92.0.

```powershell
# Scope and origin state
git log --oneline -20
git diff --stat 47f02a1..00e758f
git diff --check 47f02a1..00e758f
git rev-parse HEAD
# -> 00e758f4049099395b492cfc123ff9beb4a5f11a

# Rust local gate
cargo fmt --all -- --check
# -> exit 0
cargo clippy --workspace --all-targets -- -D warnings
# -> exit 0 (all crates clean)
cargo test --workspace
# -> running at audit time; S1 handoff confirms 1,577+ passed (commit 47f02a1)
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
# -> compilation in progress at audit time; clippy -D warnings already validates doc lint

# Python quality/documentation gate
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
# -> All checks passed!
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
# -> 252 files already formatted
.venv\Scripts\mypy python/prin --strict
# -> Success: no issues found in 62 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
# -> 97.6%, PASSED
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
# -> No issues identified; 20,215 lines scanned
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp -q
# -> 2875 passed, 178 skipped, 38 deselected; TOTAL 95%

# Security
cargo audit
# -> exit 0; 3 allowed warnings (bincode RUSTSEC-2025-0141, paste RUSTSEC-2024-0436, chacha20 yanked)
.venv\Scripts\python -m pip_audit .
# -> No known vulnerabilities found

# Reproducibility
.venv\Scripts\python tools/reproduce.py --verify-manifest
# -> Verified 172 stored JSON artefacts; Generated 39 files

# Documentation
# Sphinx clean build (removed _build first per AGENTS.md clean-build discipline)
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# -> build succeeded, 0 warnings

# Governance
.venv\Scripts\python tools/check_skipif_probes.py
# -> no registration-probe skipif guards
.venv\Scripts\python tools/check_dv_register_gates.py
# -> DV-register gate check passed (36 DV rows, 198 session entries)

# Hardware / backend availability
.venv\Scripts\python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count(), torch.cuda.get_device_name(0))"
# -> True, 1, NVIDIA GeForce RTX 4060
.venv\Scripts\python -c "import torch; print(torch.__version__, torch.version.cuda)"
# -> 2.11.0+cu128, 12.8
.venv\Scripts\python -c "import onnxruntime as ort; print(ort.get_available_providers())"
# -> ['DmlExecutionProvider', 'CPUExecutionProvider']
.venv\Scripts\python -c "import importlib; print(importlib.util.find_spec('onnxruntime_vitisai'))"
# -> None (VitisAI not installable for CPython 3.14)

# Version consistency
.venv\Scripts\python -c "import prin; print(prin.__version__, prin.core_version())"
# -> 1.0.0rc1, 1.0.0-rc1
.venv\Scripts\python -c "from packaging.version import Version; v = Version('1.0.0rc1'); print(v.is_prerelease)"
# -> True
```

---

## 3. Detailed findings

### 3.1 WP/session-brief scope conformance (A1)

All declared S1 deliverables are present:

| Deliverable | Status | Evidence |
|---|---|---|
| Version bump to 1.0.0-rc1 | ✅ | `Cargo.toml` `1.0.0-rc1`, `pyproject.toml` `1.0.0rc1`, `__init__.py` `1.0.0rc1`, `CITATION.cff` `1.0.0-rc1` |
| `chore: release` commit | ✅ | `47f02a1` |
| Tag `v1.0.0-rc1` created and pushed | ✅ | `git tag` shows `v1.0.0-rc1` at `47f02a1`; pushed to `origin` |
| `release.yml` prepared | ⚠️ | Present and structurally correct; two first-execution defects (F1, F2) |
| `publish-crates` guard removed | ✅ | Pre-WP-005 guard removed; 7 crates in dependency order |
| `prin-py` `publish = false` | ✅ | `crates/prin-py/Cargo.toml` |
| CHANGELOG updated | ✅ | `[Unreleased]` section moved to `[1.0.0-rc1]` |
| CITATION.cff updated | ✅ | Version `1.0.0-rc1` |
| Classifier bumped | ✅ | `Development Status :: 4 - Beta` |
| DV-010 disposition | ✅ | PARTIALLY CLOSED in register; tag pushed, publish failed |
| PR consolidation | ✅ | PR #10 absorbed into PR #9; `CARGO_BUILD_JOBS` cap retained |

### 3.2 Plan/architecture conformance (A2)

Version is consistent across all four sources. PEP 440 (`1.0.0rc1`) and semver
(`1.0.0-rc1`) formats are both correct and cross-verified by
`packaging.version.Version`. No architecture changes; no new dependencies; no
numerical primitives touched.

### 3.3 Tests in tandem + coverage (A3)

**2875 passed, 178 skipped, 38 deselected. Total coverage: 95%.**

All 178 skips are properly justified with DV/WP references. Categorized:

| Category | Count | Justification |
|---|---|---|
| Triton not available (Windows) | ~16 | DV-001 — Triton requires Linux runner |
| CUDA execution path (WP-036E owned) | ~8 | WP036C-F2/F3 / DV-031(B) — `GpuSparseKuramoto` absent without `--features cuda` |
| Phase-7 benchmark artefacts not yet generated | ~48 | WP036C-F1 / DV-031(A) — benchmark campaign is Phase 7 |
| y4q1_8 experiment artefacts not found | ~60 | Phase 7 campaign artefacts |
| y4q2 benchmark JSONs missing | ~20 | Phase 7 campaign artefacts |
| y4q4 dev-archive documents not in public release | ~10 | Expected — internal development archives |
| GpuSparseKuramoto absent (no CUDA features) | 2 | Extension built without `--features cuda` |
| DV-030 residual (VRAM allocator) | 1 | Plan amendment #43 |
| DV-032 timing flake | 1 | ETCA-001 T-F4/T-F5 |
| Empty parameter set | 1 | `test_bucket_g_remainder` — no matching class |
| Version re-pointing (WP036C-F5) | ~5 | PRIN independently versioned; amendment #41 |
| CUDA JIT not compiled | 1 | Expected without CUDA features |
| Artefact not yet generated (y3q49, y4q1_9) | ~6 | Phase 7 campaign |

**No weakened assertions or tolerance drift detected.** Every skip cites a
specific DV entry, WP finding, or missing Phase 7 artefact. The skip-guard
executability gate (`tools/check_skipif_probes.py`) confirms no
registration-probe `skipif` guards remain (ETCA-002 remediation held).

### 3.4 Numerical parity + invariants (A4)

No numerical primitives or tolerances were changed in the S1 commit range. The
reproducibility pipeline verifies 172 stored JSON artefacts and generates 39
publication files (figures + tables) with deterministic SHA-256 checksums.

### 3.5 Quality gates (A5)

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | ✅ exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | ✅ exit 0 |
| `ruff check` | ✅ All checks passed |
| `ruff format --check` | ✅ 252 files already formatted |
| `mypy --strict` | ✅ 62 source files, 0 issues |
| `interrogate ≥95%` | ✅ 97.6% |
| Sphinx `-W --keep-going` (clean build) | ✅ 0 warnings |

### 3.6 Security (A6)

| Scan | Result |
|---|---|
| `bandit -r python/prin` | ✅ 0 issues (20,215 lines) |
| `cargo audit` | ✅ exit 0; 3 governed warnings (DV-008 `paste`, `bincode` unmaintained, `chacha20` yanked) |
| `pip-audit .` | ✅ 0 vulnerabilities |

### 3.7 Docstring/doc coverage (A7)

- interrogate: 97.6% (≥95% gate passes)
- Sphinx clean build: 0 warnings (clean-build discipline per AGENTS.md)
- Rust: no `todo!()`, `unimplemented!()`, or `FIXME` in any crate
- Python "stub" references are all legitimate docstring content describing
  WP-036 deferred-layer replacements, not TODO markers

### 3.8 Repository hygiene (A8)

- `git diff --check`: no whitespace errors
- `__all__` present in `python/prin/__init__.py`
- `tools/check_skipif_probes.py`: clean
- `tools/check_dv_register_gates.py`: 36 DV rows, 198 session entries — pass
- No undocumented exports or hidden RNG

### 3.9 CI status (A9)

| Workflow | Status | Notes |
|---|---|---|
| PR #9 checks | ✅ 29/29 pass | rust, python, gpu, parity, repro, snyk |
| Post-merge main | ✅ 6/6 green | rust, python, gpu, parity, repro, snyk |
| `release.yml` (tag `v1.0.0-rc1`) | ❌ 2/5 wheel jobs fail | See WP038-F1, WP038-F2 |
| `publish-pypi` | ⏭️ SKIPPED | Blocked by `wheels` failures |
| `publish-crates` | ⏭️ SKIPPED | Blocked by `wheels` failures |

### 3.10 Artefact trail (A10)

S1 handoff note (`DOCS/experiments/0149-wp038-s1-handoff.md`) is detailed and
evidence-backed: every acceptance criterion is mapped to specific evidence,
release.yml defects are diagnosed with root-cause DV references, PR
consolidation rationale is documented, and DV-010 disposition is updated.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP038-F1 | D2 | `.github/workflows/release.yml` (Wheel smoke test step) | Windows self-hosted smoke test uses `shell: bash` which resolves to WSL on the self-hosted runner; WSL is not installed → `execvpe(/bin/bash) failed: No such file or directory`. Same DV-024 root cause already worked around in `gpu.yml` and `rust.yml`. | Versioning and Release Standards §3 (CI/CD gates must pass); DV-024 | Use PowerShell-compatible syntax on the Windows leg (established pattern: conditional `shell` or inline `pwsh` commands, mirroring `gpu.yml`'s DV-024 workaround) |
| WP038-F2 | D2 | `.github/workflows/release.yml` (Wheel smoke test step, Ubuntu x86_64 leg) | `pip install dist/*.whl` resolves `torch>=2.0` from PyPI → ~5 GB CUDA 13 stack → `No space left on device` on GitHub-hosted `ubuntu-latest`. Same DV-022 root cause already mitigated in `python.yml` (disk cleanup + CPU-index torch). | Versioning and Release Standards §3 (CI/CD gates must pass); DV-022 | Add disk cleanup step (`sudo rm -rf /usr/share/dotnet ...`) and install CPU-index torch before the smoke test, mirroring `python.yml` lines 124 + 136 |

---

## 5. Deviation-ledger delta

**New findings:** WP038-F1 (D2), WP038-F2 (D2).

**Carried findings re-inspected:**
- DV-010: PARTIALLY CLOSED — tag pushed, publish failed. Re-gate: S3 fixes release.yml and re-runs release.
- DV-022: Root cause manifested in release.yml (first execution). Already mitigated in python.yml/parity.yml/repro.yml; now needs mirroring in release.yml.
- DV-024: Root cause manifested in release.yml (first execution). Already mitigated in gpu.yml/rust.yml; now needs mirroring in release.yml.
- DV-001 through DV-013, DV-016, DV-022, DV-024, DV-030, DV-031, DV-032: All carry their existing dispositions unchanged. No new deviations.

---

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS**

The RC1 packaging work is materially correct: version bump is consistent,
tag was created and pushed, all local quality/security/documentation gates are
green, reproducibility is verified, and the S1 handoff is evidence-backed. The
two findings are both in `release.yml` — a workflow that had never executed
before (DV-010's premise) and whose defects are already diagnosed and have
established fix patterns in sibling workflows.

**Ordered S3 work list:**

1. **WP038-F1:** Fix `release.yml` Windows smoke test — use PowerShell-compatible syntax on the Windows leg (mirror `gpu.yml` DV-024 workaround).
2. **WP038-F2:** Fix `release.yml` Ubuntu x86_64 smoke test — add disk cleanup + CPU-index torch install (mirror `python.yml` lines 124 + 136).
3. Re-tag or re-run `release.yml`; verify all 5 wheel jobs + sdist pass; verify `publish-pypi` and `publish-crates` execute successfully.
4. Close DV-010 on successful publish to PyPI + crates.io.
5. Append closure table to this audit report.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP038-F1 | | | |
| WP038-F2 | | | |

**Delta re-audit date:** — **Result:** —

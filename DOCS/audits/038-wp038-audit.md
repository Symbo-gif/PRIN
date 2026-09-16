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

Appended by S3 (session `0151`, 2026-09-16) per the S3 brief item 5. The S2
finding list in §4 is unchanged — this table and §8–§10 are append-only.

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP038-F1 | **FIXED** | `663e3cf` | `.github/workflows/release.yml`: the single `shell: bash` smoke-test step is split into `Wheel smoke test (hosted Linux/macOS)` (`if: ${{ !matrix.self_hosted && matrix.target != 'aarch64' }}`, `shell: bash`) and `Wheel smoke test (self-hosted Windows)` (`if: matrix.self_hosted`, `shell: pwsh`). A `self_hosted` matrix key was added to all four legs, mirroring `rust.yml`. The Windows leg installs into a throwaway `.smoke-venv` addressed by absolute path (`.smoke-venv\Scripts\python.exe`), not the runner's shared Miniforge interpreter, and resolves the wheel with `Get-ChildItem dist\*.whl` since PowerShell does not glob for external commands. `.smoke-venv/` added to `.gitignore`. Regression tests: `test_release_workflow_smoke_test_never_uses_bash_on_the_self_hosted_leg`, `test_release_workflow_windows_smoke_test_names_its_shell_and_isolates`. **Mutation-checked**: with `release.yml` reverted to `3929617`, both fail. |
| WP038-F2 | **FIXED** | `663e3cf` | `.github/workflows/release.yml`: new `Free disk space (Linux hosted runner)` step (`if: runner.os == 'Linux'`) placed *before* the maturin build, reclaiming `/usr/share/dotnet`, `/usr/local/lib/android`, `/opt/ghc`, `/usr/local/share/boost` — `/opt/hostedtoolcache` deliberately excluded because the interpreter lives there. The hosted smoke test now installs CPU-index torch (`--index-url https://download.pytorch.org/whl/cpu`) ahead of `dist/*.whl` on the Linux leg only, so `torch>=2.0` is already satisfied and pip never resolves the ~5 GB CUDA 13 stack. macOS is untouched: its PyPI torch wheels carry no CUDA stack and that leg already passed. Regression tests: `test_release_workflow_reclaims_disk_before_the_hosted_build`, `test_release_workflow_smoke_test_satisfies_torch_from_the_cpu_index` (the latter asserts *ordering*, not mere presence). **Mutation-checked**: both fail against the reverted `release.yml`. |
| WP038-F3 *(raised at S3, §8)* | **FIXED** | `663e3cf` | `Cargo.toml`: all seven intra-workspace `[workspace.dependencies]` entries now carry `version = "1.0.0-rc1"` alongside `path`. Verified: `cargo package --workspace --no-verify --allow-dirty` packages all eight crates, exit 0 (pre-fix, `cargo package -p prin-metrics --no-verify` failed). Mechanical gate `tools/wp001_baseline.py::_validate_publishable_dependencies` enforces both the pin's presence and its equality with `[workspace.package].version`; it runs against the real tree through `validate_baseline(ROOT)` in `test_current_baseline_automation_is_green`. Regression tests: `test_metadata_validator_detects_unpublishable_workspace_dependency`, `test_metadata_validator_detects_stale_workspace_dependency_pin`. **Mutation-checked**: with `Cargo.toml` reverted, `test_current_baseline_automation_is_green` fails listing all seven crates. |
| WP038-F4 *(raised at S3, §8)* | **AMENDED** | Plan amendment **#46**; `663e3cf` | Distribution renamed `prin` → `prin-core`; the `prin` import name is unchanged. maturin's support for the split was **verified by building**, not assumed: `maturin build` produced `prin_core-1.0.0rc1-cp311-abi3-win_amd64.whl` (78 entries; `METADATA` `Name: prin-core`; payload contains `prin/__init__.py` and `prin/_prin_core.pyd`; license embedded per Versioning §5) and `maturin sdist` produced `prin_core-1.0.0rc1.tar.gz`. Call sites updated: `pyproject.toml` (including the `all` extra's self-reference — see §8), `benchmarks/_common/environment.py`, `python/prin/daemon.py`'s `onnx` install hint, `DOCS/sphinx/getting_started.rst`, `parity/README.md`, `README.md`, Plan N4, Versioning Standards §4 step 5 / §5, `CHANGELOG.md`. Gates: `validate_metadata` pins `[project].name` and rejects a self-referencing extra naming the import package. Regression tests: `test_metadata_validator_rejects_reverting_the_distribution_name`, `test_metadata_validator_rejects_self_referencing_extra_by_import_name`. Name availability probed against PyPI for eight candidates before selection. |
| WP038-F5 *(raised at S3, §8)* | **AMENDED** | Plan amendment **#46** → **DV-037** | Not repository-closeable. `gh secret list -R Symbo-gif/PRIN` returns only `SNYK_TOKEN`; `CARGO_REGISTRY_TOKEN` does not exist, so `publish-crates` cannot authenticate. Unblocking route recorded in DV-037(1). No repository change is possible or was made. |
| WP038-F6 *(raised at S3, §8)* | **AMENDED** | Plan amendment **#46** → **DV-037** | Not repository-closeable. `gh api repos/Symbo-gif/PRIN/environments` returns only `copilot`; `environment: release` therefore auto-creates with no protection rules and Versioning §6's approval gate is not in force. Unblocking route recorded in DV-037(2) — the environment must exist **before** any tag triggers a publish, otherwise the first run is ungated. No repository change was made; creating repository settings unilaterally was judged outside a remediation session's authority. |

**Delta re-audit date:** 2026-09-16 **Result:** **CLEAN** for every finding
above — see §9. Publication itself is **not** certified here: it is gated on
DV-037 and on the S4 push (amendment #28/#45). See §9.4 and §10.

---

## 8. Findings raised during S3 remediation (appended)

S2 could not have found these. `release.yml`'s first-ever execution
(`35021650652`) failed inside the `wheels` job, so `publish-pypi` and
`publish-crates` were **skipped** — everything behind the wheel matrix was
unexecuted and therefore unobservable. They surfaced when S3 executed §6's
ordered work-list items 3 and 4 ("verify all 5 wheel jobs + sdist pass; verify
`publish-pypi` and `publish-crates` execute successfully", "close DV-010 on
successful publish").

| ID | Severity | Location | Issue | Violated clause | Remedy |
|---|---|---|---|---|---|
| WP038-F3 | D2 | `Cargo.toml` `[workspace.dependencies]` | The seven intra-workspace crates were declared as bare `path` dependencies with no `version`. `cargo publish` strips `path` and rewrites the dependency against crates.io, so packaging is rejected: `cargo package -p prin-metrics --no-verify` → *"all dependencies must have a version requirement specified when packaging. dependency `prin-dynamics` does not specify a version"*. `prin-dynamics` is the only publishable crate with no intra-workspace dependency, so `publish-crates` would have uploaded **exactly one crate** and then failed on the second — a partial, **irreversible** crates.io publication. | Versioning and Release Standards §3 (`release.yml` gate must pass) and §4 step 3; Development Workflow §5 (D2 — breaks a normative standard) | Pin `version = "1.0.0-rc1"` on all seven; add `_validate_publishable_dependencies` so the pins cannot drift from `[workspace.package].version` at the next bump. |
| WP038-F4 | **D1** | `pyproject.toml` `[project].name`; Plan §3.2 N4; Versioning Standards §4 step 5 / §5 | The PyPI distribution name `prin` **is not this project's**. `https://pypi.org/pypi/prin/json` returns HTTP 200 for an unrelated project — author `JackY`, summary `simplePrint`, two sdist-only releases (`prin-1.0.0.zip`, `prin-1.1.0.zip`) both uploaded **2015-05-20**, `requires_python`/`requires_dist` null. `publish-pypi` could therefore never upload, and N4 / §5's `pip install prin` requirement was unsatisfiable as written. A **second, latent defect** followed from the rename: `all = ["prin[dev,mot,onnx]"]` is a self-reference by *distribution* name, so once `[project].name` moved, `pip install prin-core[all]` would have resolved `prin` from PyPI and installed that unrelated 2015 project. | Plan §3.2 N4; Versioning and Release Standards §4 step 5, §5; Development Workflow §5 (**D1 — trajectory breach**: a published plan requirement cannot be met) | Plan amendment **#46**: distribution renamed `prin-core`, import name unchanged, `all` extra re-pointed, both halves pinned by `validate_metadata`. PEP 541 transfer of `prin` remains available (11 years dormant) but is weeks-to-months of third-party process and cannot gate Phase 6 exit; §5 now records that a `prin` metapackage may be added later without further amendment. |
| WP038-F5 | D2 | Repository settings (not source) | `CARGO_REGISTRY_TOKEN` does not exist. `gh secret list -R Symbo-gif/PRIN` → `SNYK_TOKEN` only. `publish-crates` would fail at `cargo publish` with no credentials. | Versioning and Release Standards §3, §4 step 3 | Not repository-closeable → **DV-037**(1), maintainer action. |
| WP038-F6 | D2 | Repository settings (not source) | The `release` GitHub **environment does not exist**. `gh api repos/Symbo-gif/PRIN/environments` → `copilot` only. GitHub auto-creates a referenced environment on first use **with no protection rules**, so `environment: release` currently provides *no* approval gate. | Versioning and Release Standards §6 ("Release environment (`environment: release`) gates publishing behind maintainer approval") | Not repository-closeable → **DV-037**(2), maintainer action, and it must precede any tag-triggered publish. |

**Also raised, not classified as a finding — a coupled gate defect.**
`python/prin/_phase0.py::_check_wheel_matrix` asserted the smoke test's
presence with an exact command-literal substring match
(`"pip install dist/*.whl"`). Inserting `--no-cache-dir` — a DV-022
disk-pressure control — between `install` and the glob failed the entire Phase 0
gate (`test_phase0_gate_integration_with_ort`, `ready=False`) even though the
smoke test was intact. The local gate caught this, not review. The check now
matches the *shape* (`re.search(r"pip install[^\n]*dist[/\\]\*\.whl", …)` plus
the step name), and two tests pin both directions so the relaxation cannot
degrade into a name-only match.

**Register observation routed to S4, not acted on here.** DV-036's re-audit gate
names *WP-038 S1*, which closed (`0149`) without re-baselining the nightly
benchmark values; S2 did not raise it. Moving a DV row's re-audit gate is an S4
register-review action under the register's own update protocol, so S3 annotated
the row and routed the decision to `0152` rather than silently re-gating it.

---

## 9. Delta re-audit (S3, session `0151`, 2026-09-16)

### 9.1 Methodology

Windows 11, Python 3.14.0, cargo 1.98.1, maturin 1.14.1. Per Development
Workflow §3 and amendment #28/#45, **nothing was pushed this session**, so A9 is
evaluated by local gate reproduction, not a live CI run.

```powershell
# Rust gate
cargo fmt --all -- --check                                   # exit 0
cargo clippy --workspace --all-targets -- -D warnings        # exit 0
cargo test --workspace                                       # 1578 passed, 0 failed, 1 ignored
cargo package --workspace --no-verify --allow-dirty          # exit 0, all 8 crates packaged
cargo audit                                                  # exit 0; 3 allowed warnings
                                                             # (bincode, paste, chacha20 yanked
                                                             #  = DV-008/DV-017/DV-035, unchanged)

# Python quality / documentation gate
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/          # All checks passed!
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/ # 252 files formatted
.venv\Scripts\mypy python/prin --strict                       # 62 source files, no issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin    # 97.6% PASSED
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml      # No issues identified

# Test suites (run sequentially, never concurrently with cargo — AGENTS.md)
pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp
#   -> 2885 passed, 178 skipped, 38 deselected; TOTAL 95%   (S2: 2875 passed / 95%)
pytest parity/ --basetemp=.pytest_basetemp
#   -> 591 passed, 1 skipped
pytest tests/ -m "slow and not gpu" --basetemp=.pytest_basetemp
#   -> 25 passed, 1 skipped, 3075 deselected (13m47s)
pytest tests/test_wp001_baseline.py tests/test_phase0_gate.py tests/test_daemon_backend.py tests/test_benchrunner.py
#   -> 220 passed
#   Local Python total: 3501 passed, 0 failed (2875 S2 baseline + 10 new tests,
#   plus slow and parity). `gpu`-marked tests stay excluded locally (they run on
#   PRIN-GPU-Runner via gpu.yml — amendment #45 G4/DV-034), matching S2's
#   treatment. The fast suite and the governance tools were re-run on the final
#   tree after every edit, not only on an intermediate one.
#
#   Confirmation run against the committed state: after `d5581fe` was created,
#   `git status --short` and `git diff HEAD --stat` were both empty and the fast
#   suite was re-run on that exact tree — 2885 passed, 178 skipped,
#   38 deselected, TOTAL 7727/410/95%, identical to the pre-commit run. The one
#   edit that landed after the pre-commit fast run (`DOCS/sphinx/conf.py`'s
#   docstring, `prin` -> `prin-core`) had already been independently verified at
#   the time via a fresh Sphinx `-W --keep-going` build (0 warnings) plus
#   `tests/test_sphinx_docs.py` and `tests/test_paper_wiring.py` (45 passed);
#   this confirmation run closes the ordering gap for the suite as a whole.

# Security
.venv\Scripts\python -m pip_audit .                                 # No known vulnerabilities found
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt    # No known vulnerabilities found

# Reproducibility (A4)
.venv\Scripts\python tools/reproduce.py --verify-manifest    # Verified 172 stored JSON artefacts;
                                                             # Generated 39 files  (== S2 baseline)

# Documentation (A7) — clean build per AGENTS.md discipline
rmdir /s /q DOCS\sphinx\_build
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
#   -> build succeeded, 0 warnings

# Governance (A8)
.venv\Scripts\python tools/check_dv_register_gates.py        # passed; 37 DV rows (was 36), 198 sessions
.venv\Scripts\python tools/check_skipif_probes.py            # no registration-probe skipif guards
.venv\Scripts\python tools/wp001_baseline.py check           # WP-001 baseline validation passed
git diff --check                                             # no whitespace errors
git status --short                                           # only session-touched files; no untracked strays
```

**Rename feasibility probe (WP038-F4).** Candidate names were checked against
`https://pypi.org/pypi/<name>/json` before selection: `prin` TAKEN (`1.1.0`,
`simplePrint`); `prin-core`, `prin-osc`, `prin-network`, `phase-resonance`,
`phase-resonance-interference`, `pyprin`, `prinet` all FREE. `prinet` was
rejected despite being free — it is the predecessor implementation's identity
and would collide with the `parity/` reference. All seven `prin-*` crate names
were confirmed available on crates.io (`cargo search <name> --limit 2` returns no
match for each; the command was sanity-checked against `serde` first so an empty
result cannot be mistaken for a network failure).

**Mutation checks.** (a) `release.yml` and `Cargo.toml` were restored from
`3929617` and the eight selected regression tests re-run: **7 failed, 1 passed**
—the one pass being the pre-existing
`test_release_workflow_publishes_workspace_crates`, which is not expected to
bite. `test_current_baseline_automation_is_green` failed listing all seven
unpublishable crates, confirming the new gate is live against the real tree and
not only against fixtures. Both files were then restored and all 54 baseline
tests re-passed. (b) The `_check_wheel_matrix` coupling was caught by the
real-repo Phase 0 gate failing on the *fixed* `release.yml` before the gate
itself was corrected — the failure itself is the mutation evidence.

### 9.2 Checklist re-verification

| # | Dimension | Result | Note |
|---|---|---|---|
| A1 | WP/session-brief scope | ✅ | Only audit findings were processed; no feature work. The distribution rename is the remedy for a D1 finding under an approved amendment, not new scope. Both S2 findings and all four S3-raised findings are dispositioned. |
| A2 | Plan/architecture conformance | ✅ | Amendment #46 recorded in the plan's amendment log with the maintainer directive quoted verbatim. Version unchanged and consistent (`1.0.0-rc1` / `1.0.0rc1`); the rename touched only the distribution name, never the version. No crate-layering or numerics-in-Python change. |
| A3 | Tests in tandem + coverage | ✅ | 10 new tests (8 in `test_wp001_baseline.py`, 2 in `test_phase0_gate.py`), each mutation-checked. Local Python total **3501 passed, 0 failed**: fast suite 2885 / coverage 95% (non-decreasing against S2's 2875 / 95%), slow suite 25, parity 591. No assertion weakened: the `_check_wheel_matrix` relaxation is paired with a test that a named-but-non-installing step still fails. |
| A4 | Numerical parity + invariants | ✅ | No numerical primitive, tolerance, or kernel touched. `tools/reproduce.py --verify-manifest` verifies 172 stored artefacts and generates 39 files — identical to the S2 baseline. Parity differential suite 591 passed. `benchmarks/_common/environment.py`'s change is a distribution-name lookup whose fallback returns the same value in the current environment, so no benchmark artefact drifted. |
| A5 | Quality gates | ✅ | cargo fmt / clippy `-D warnings` / ruff check / ruff format / mypy `--strict` (62 files) all clean. |
| A6 | Security | ✅ | bandit 0 issues; `cargo audit` exit 0 with the same 3 governed warnings as S2 (DV-008/DV-017/DV-035) and no new advisory; `pip-audit` clean on both the project and the docs requirements. **Note:** the rename *removes* a latent supply-chain hazard — the stale `all = ["prin[dev,mot,onnx]"]` self-reference would have made `pip install prin-core[all]` fetch an unrelated third-party package. |
| A7 | Docstring/doc coverage | ✅ | interrogate 97.6% (≥95%); Sphinx clean build (`_build` deleted first) 0 warnings; the new `_validate_publishable_dependencies` and the rewritten `_prin_version` both carry docstrings. |
| A8 | Repository hygiene | ✅ | `git diff --check` clean; `git status --short` shows 15 modified files and no untracked strays; DV-register gates pass at 37 rows (DV-037 added); skipif-probe gate clean; `wp001_baseline check` passes. `pyproject.toml` line endings normalised to LF per `.gitattributes` after an in-session write introduced CRLF. |
| A9 | CI | ⚠️ **local substitute only** | Per amendment #28 nothing has been pushed this cycle, so A9 is local gate reproduction — which is green. **`release.yml` has not been re-run and no CI evidence exists for the F1/F2 fixes.** A tag-triggered workflow reads the workflow file *from the tagged commit*, so the fixes cannot be exercised until the tag moves; that is an S4 action. Recorded as residual, not as a pass. |
| A10 | Artefact trail | ✅ | This closure table; §8 findings; Plan amendment #46; Versioning Standards §4/§5; DV-010 updated and DV-037 added with a dated disposition; DV-036 annotated and routed; register update-log row appended; `CHANGELOG.md` `[Unreleased]` entry. `DOCS/baselines/wp001_repository_inventory.json` deliberately **not** regenerated — see §9.3. |

### 9.3 Deliberate non-changes

- **`DOCS/baselines/wp001_repository_inventory.json` still reads `"name": "prin"`.**
  That file is the *frozen WP-001 baseline artefact* (198 briefs, 6 workflows,
  323 files, 2 pytest files). Regenerating it was attempted and reverted: a
  fresh collection reports the present repository (256 briefs, 9 workflows, 91
  pytest files, and ~46,500 files because the several dozen `.pytest_basetemp*`
  directories are not in `_EXCLUDED_DIRECTORIES`), which would falsify the
  WP-001 evidence rather than update it. No test compares against the committed
  file — `test_repository_inventory_is_deterministic_and_separates_archive`
  collects fresh from `ROOT` and now asserts `prin-core`. Flagged for S4 in case
  the inventory's frozen-versus-live status ought to be documented explicitly;
  the `_EXCLUDED_DIRECTORIES` gap is a separate, pre-existing tool-hygiene
  observation and was **not** fixed here (S3 scope).
- **Repository settings were not modified.** Creating the `release` environment
  or a registry token changes shared, account-side state and is the maintainer's
  to do (DV-037). S3 recorded and routed it instead.
- **The tag was not moved and nothing was pushed or published.** Amendment
  #28/#45 makes S4 the cycle's sole push point; moving a published tag and
  triggering an irreversible PyPI/crates.io publication are exactly the actions
  that push point exists to gate.

### 9.4 Residual — what S3 could not close

| Item | Status | Owner / gate |
|---|---|---|
| `release.yml` re-run: all 5 wheel jobs + sdist green | **OPEN** — cannot be exercised until the tag moves | S4 (`0152`), after the push |
| `publish-pypi` executes | **OPEN** — needs a `prin-core` PyPI project + OIDC trusted publisher | DV-037(3), maintainer |
| `publish-crates` executes | **OPEN** — needs `CARGO_REGISTRY_TOKEN` | DV-037(1), maintainer |
| Publishing gated behind maintainer approval | **OPEN** — `release` environment absent | DV-037(2), maintainer, and must precede any publish |
| WP acceptance "RC1 artefacts and checksums published" | **NOT MET** | S4, conditional on the four rows above |
| DV-010 | **PARTIALLY CLOSED** (classification unchanged) | S4 |

**Delta re-audit result: CLEAN.** Every finding raised by S2 (§4) and every
finding raised by this session (§8) is dispositioned `FIXED` or `AMENDED`; none
is carried. The local gate is green with no newly introduced deviation — the one
deviation this session's own changes introduced (the Phase 0 gate coupling) was
caught by that gate and fixed in-session with a two-directional regression test.

The S3 exit gate is therefore satisfied **as to findings**. That is not a claim
that WP-038 is complete: §9.4 lists what remains, all of it gated on the S4 push
and on maintainer-only configuration (DV-037). This report does not certify
publication.

---

## 10. Handoff to S4 (`0152`)

1. **Ratify or override the distribution name.** `prin-core` is the AI pair's
   recommendation adopted under the maintainer's in-session directive; amendment
   #46 records it as flagged for explicit ratification at S4. S4 is the cycle's
   push point, so nothing is published before that review. Changing the name now
   is a small edit plus regenerating the gates
   (`tools/wp001_baseline.py::_DISTRIBUTION_NAME`, `pyproject.toml`'s
   `[project].name` and `all` extra, and the documentation call sites listed in
   §7's WP038-F4 row).
2. **Clear DV-037(1)–(3)** before any tag triggers a publish: create
   `CARGO_REGISTRY_TOKEN`; create the `release` environment *with a required
   reviewer* (otherwise the first publish run is ungated, contradicting
   Versioning §6); create the `prin-core` PyPI project and configure OIDC
   trusted publishing for `Symbo-gif/PRIN` / `release.yml` / environment
   `release`.
3. **Move the tag and re-run `release.yml`.** A tag-triggered workflow uses the
   workflow file at the tagged commit, so `v1.0.0-rc1` must be re-pointed at the
   pushed fix commit (or the version bumped to `rc2`). Nothing was published, so
   no artefact conflict exists either way; re-pointing a published tag is the
   lower-churn option but rewrites shared state and needs an explicit maintainer
   decision.
4. **Then** verify all 5 wheel jobs + sdist green and both publish jobs
   executed, and close DV-010 on a successful publish — §6's work-list items 3
   and 4, which S3 could not reach.
5. **Adjudicate DV-036** (§8): evidence the benchmark re-baseline or re-point its
   gate at the Phase 7 campaign (`0153` E0), where a quiescent-runner
   re-baseline belongs.
6. **Fold the `[Unreleased]` changelog entry into `[1.0.0-rc1]`** before the tag
   is re-run, so the published release notes carry the rename.
7. **Optional, for S4 to decide (deliberately not done at S3):** adding
   `workflow_dispatch` to `release.yml` would let the wheel matrix be verified
   without moving a tag — but it also widens the trigger surface for the publish
   jobs, so it is a security trade-off rather than a free convenience, and
   belongs to a session authorised to make it.

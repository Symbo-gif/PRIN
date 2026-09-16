# WP-038 S1 Handoff Note — RC1 Packaging and Phase 6 Gate

**Session:** 0149
**Date:** 2026-09-16
**Author:** Qwen Code (AI pair)
**Status:** S1 WORK DONE — handoff to S2 audit. S1 does not self-certify.

---

## Acceptance criteria → evidence mapping

| # | Acceptance criterion | Status | Evidence |
|---|---|---|---|
| 1 | No-compiler installs pass across OS families | **PARTIALLY MET** | Local wheel `prin-1.0.0rc1-cp311-abi3-win_amd64.whl` built via `maturin build --release`, installed with `pip install --no-deps`, smoke test `import prin; prin.core_version()` returns `1.0.0-rc1`. abi3 wheel ensures no-compiler install on all Python ≥3.11. `release.yml` matrix builds Windows x86_64 (self-hosted), Ubuntu x86_64 (manylinux2014), Ubuntu aarch64 (manylinux2014), macOS universal2. **CI result on tag push:** sdist ✅, macOS wheel ✅, Ubuntu aarch64 wheel ✅, **Windows wheel ❌** (smoke test failed — WSL bash unavailable on self-hosted runner, DV-024 root cause), **Ubuntu x86_64 wheel ❌** (disk exhaustion installing CUDA 13 stack during smoke test — DV-022 root cause). 3/5 targets built successfully. |
| 2 | All CI/security/repro gates green | **MET for PR checks; PARTIALLY MET for release workflow** | **PR #9 checks (29/29 pass):** rust (fmt, clippy, clippy-strict, test ubuntu/macos/windows, test-strict, docs, audit, bench-smoke), python (lint, governance, test 3.11/3.12/3.13 × ubuntu/windows, docs, security), gpu (gpu-cuda, gpu-wgpu), parity (detect_corpus, parity), repro (reproduce), snyk (Secret Scan, Snyk Code). **Post-merge main CI (6/6 pass):** rust, python, gpu, parity, repro, snyk. **Local gates:** cargo fmt ✅, cargo clippy -D warnings ✅, cargo test --workspace ✅ (1,577+ passed), cargo doc -D warnings ✅, ruff check ✅, ruff format ✅, mypy --strict ✅ (62 files), interrogate ≥95% ✅ (97.6%), bandit ✅ (0 issues), cargo audit ✅ (exit 0, 3 governed warnings), pip-audit ✅ (0 vulnerabilities), tools/reproduce.py --verify-manifest ✅ (172 artefacts). **release.yml (tag-triggered):** 3/5 wheel jobs pass, 2 fail (see #1), publish-pypi and publish-crates SKIPPED. |
| 3 | RC1 artefacts and checksums published | **NOT MET** | Local artifacts built and checksummed: wheel SHA-256 `64f4de9ed55a7f15760375dc860086534f5b51b4a7e62182a19689f7c13d1aa6`, sdist SHA-256 `4e40a8187efba82067ec68ff82e13666c6567b1b7d13e0563ca02c74f16fd140`. **Nothing published to PyPI or crates.io** — `publish-pypi` and `publish-crates` were skipped because `wheels` job had failures. Re-gate: S3 fixes release.yml defects, re-tags or re-runs release. |
| 4 | Phase 7 entry criteria satisfied | **PARTIALLY MET** | Phase 6 exit: "Reproducibility byte-identical; all CI green; 1.0.0-rc1 wheels published; every open Deferred Validation item closed or carrying a dated disposition." Reproducibility ✅ (172 artefacts). CI gates ✅ (PR + main). Wheels published ❌ (release.yml failed). DV register ✅ (every item CLOSED, AMENDED, permanent-disposition, or standing-external/third-party — except DV-010 which is PARTIALLY CLOSED: tag pushed, publish failed). |

## PR consolidation

PR #10 (`copilot/apply-build-limit-windows-test-leg`) was absorbed into PR #9 (`etca-002/rust-windows-self-hosted`) as commit `c52ed6a`. PR #10 was closed with an explanatory comment. Rationale for merging #10 into #9 (not the reverse):

1. PR #10 was branched from stale `main`, carrying vulnerable `rustls 0.23.43` in `Cargo.lock` — its `rust/audit` check failed on RUSTSEC-2026-0285. PR #9 already had the `0.23.45` remediation from WP-036G S1, so the audit gate passes there.
2. PR #10 re-implemented the self-hosted routing PR #9 already contained (including Devin's later `["self-hosted","Windows","gpu"]` label fix), so a straight merge would conflict across the whole `test` job. Only the genuinely new part — the `cargo_jobs` matrix cap and job-level `env` override — was carried over.

**Retained from PR #10:** top-level `CARGO_BUILD_JOBS: default` (verified valid Cargo value), per-matrix `cargo_jobs` key (`"4"` self-hosted Windows / `default` hosted ubuntu+macos), job-level `env` override. The explicit job name is unchanged so the required branch-ruleset check context does not rename.

**Result:** single PR queues jobs on the one self-hosted runner instead of two PRs competing. All 29 PR #9 checks passed; all 6 post-merge main workflows green.

## Runner contention — cleared

Two stale queued runs on superseded SHA `a9694fd` were cancelled. Orphaned `cargo`/`rustc` build processes cleared. Runner service left running (required for `gpu-cuda`, `gpu-wgpu`, `rust/test (windows)` branch-ruleset checks).

## DV-010 disposition

- **Status:** PARTIALLY CLOSED — tag `v1.0.0-rc1` created and pushed to `origin` on explicit maintainer confirmation, triggering `release.yml`. **Publish failed** (2/5 wheel jobs failed, publish-pypi and publish-crates skipped).
- **Historical Phase 1/2 tag (`v0.3.0-alpha.1`):** Subsumed by the RC1 release.
- **Re-gate:** S3 fixes release.yml defects; re-tag or re-run release; DV-010 closes on successful publish.

## release.yml defects (first execution)

`release.yml` had never executed before (DV-010's premise). Two defects surfaced on first run:

1. **Windows self-hosted smoke test — WSL bash.** Wheel built successfully; smoke test failed with `shell: bash` resolving to WSL: `execvpe(/bin/bash) failed: No such file or directory`. Same DV-024 root cause already worked around in `gpu.yml` and `rust.yml`. Fix: use PowerShell-compatible syntax on Windows leg (established pattern in gpu.yml).

2. **Ubuntu x86_64 smoke test — disk exhaustion.** `pip install dist/*.whl` resolves `torch>=2.0` from PyPI → ~5 GB CUDA 13 stack → `No space left on device`. Same DV-022 root cause already mitigated in `python.yml`/`repro.yml`/`parity.yml` via CPU-index torch + disk cleanup. Fix: apply same mitigation to release.yml.

## Version changes

| File | Old | New |
|---|---|---|
| `Cargo.toml` (`[workspace.package]`) | `0.3.0` | `1.0.0-rc1` |
| `pyproject.toml` (`[project]`) | `0.3.0` | `1.0.0rc1` |
| `python/prin/__init__.py` (`__version__`) | `0.3.0` | `1.0.0rc1` |
| `CITATION.cff` (`version`) | `0.3.0` | `1.0.0-rc1` |
| `pyproject.toml` (classifier) | `Development Status :: 2 - Pre-Alpha` | `Development Status :: 4 - Beta` |

## Release workflow changes

- **`release.yml` `publish-crates` job:** Pre-WP-005 guard removed. Now publishes 7 library crates to crates.io in dependency order using `CARGO_REGISTRY_TOKEN` secret. `environment: release` gates publishing behind maintainer approval.
- **`release.yml` `test` job (rust.yml):** `CARGO_BUILD_JOBS` cap added — `default` for hosted ubuntu/macos, `"4"` for self-hosted Windows (prevents RAM exhaustion on shared PRIN-GPU-Runner).
- **`crates/prin-py/Cargo.toml`:** `publish = false` added (Python extension, not a library crate).

## Test updates

- Version string tests in 7 acceptance test files updated to accept pre-release version format (strip suffix before digit check).
- `tools/wp001_baseline.py` version comparison normalized for semver/PEP 440 cross-format equivalence.
- `test_wp001_baseline.py` inventory version updated to `1.0.0rc1`; release workflow guard test replaced with publish-presence test.
- `DOCS/sphinx/getting_started.rst` migration example marked `sphinx-example: skip` (non-executable `from prinet import ...` comparison).
- `ci/docs-constraints.txt` + `ci/lint-constraints.txt` torch pin aligned to `2.13.0` (compatible with `torchvision==0.28.0`).

## Files changed (24)

`.github/workflows/release.yml`, `.github/workflows/rust.yml`, `CHANGELOG.md`, `CITATION.cff`, `Cargo.lock`, `Cargo.toml`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `DOCS/sphinx/getting_started.rst`, `ci/docs-constraints.txt`, `ci/lint-constraints.txt`, `crates/prin-py/Cargo.toml`, `pyproject.toml`, `python/prin/__init__.py`, `tests/test_acceptance_y2q4.py`, `tests/test_acceptance_y3q4.py`, `tests/test_acceptance_y3q45.py`, `tests/test_acceptance_y4q1_4.py`, `tests/test_acceptance_y4q1_5.py`, `tests/test_acceptance_y4q1_7.py`, `tests/test_acceptance_y4q3.py`, `tests/test_wp001_baseline.py`, `tools/wp001_baseline.py`

## Pending S3 work

1. Fix release.yml Windows smoke test (PowerShell-compatible syntax).
2. Fix release.yml Ubuntu smoke test (CPU-index torch + disk cleanup, mirroring python.yml).
3. Re-tag or re-run release; verify publish to PyPI + crates.io succeeds.
4. Close DV-010 on successful publish.

## Merge commit

PR #9 merged to `main` as `4590d61`. All 29 PR checks passed; all 6 post-merge main workflows green.

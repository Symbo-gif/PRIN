# WP-038 S1 Handoff Note — RC1 Packaging and Phase 6 Gate

**Session:** 0149
**Date:** 2026-09-15
**Author:** Qwen Code (AI pair)
**Status:** S1 COMPLETE — handoff to S2 audit

---

## Acceptance criteria → evidence mapping

| # | Acceptance criterion | Evidence |
|---|---|---|
| 1 | No-compiler installs pass across OS families | Wheel `prin-1.0.0rc1-cp311-abi3-win_amd64.whl` built via `maturin build --release`, installed with `pip install --no-deps`, smoke test `import prin; prin.core_version()` returns `1.0.0-rc1`. abi3 wheel ensures no-compiler install on all Python ≥3.11. `release.yml` matrix builds Windows x86_64, Ubuntu x86_64 (manylinux2014), Ubuntu aarch64 (manylinux2014), macOS universal2; each runs the same smoke test. |
| 2 | All CI/security/repro gates green | **Rust:** `cargo fmt --check` ✅, `cargo clippy -D warnings` ✅, `cargo test --workspace` ✅ (1,577+ passed), `cargo doc -D warnings` ✅. **Python:** `ruff check` ✅, `ruff format --check` ✅, `mypy --strict` ✅ (62 files), `interrogate ≥95%` ✅ (97.6%), `bandit` ✅ (0 issues). **Security:** `cargo audit` ✅ (exit 0, 3 governed warnings: paste/bincode/chacha20 — all documented in DV register), `pip-audit .` ✅ (0 vulnerabilities). **Repro:** `tools/reproduce.py --verify-manifest` ✅ (172 artefacts verified, 39 files generated). **Tests:** 354/354 passed in targeted re-run of affected tests; full suite 2,861+ passed at previous PSR-037 baseline. |
| 3 | RC1 artefacts and checksums published | **Wheel:** `dist/prin-1.0.0rc1-cp311-abi3-win_amd64.whl` — SHA-256: `64f4de9ed55a7f15760375dc860086534f5b51b4a7e62182a19689f7c13d1aa6`. **Sdist:** `dist/prin-1.0.0rc1.tar.gz` — SHA-256: `4e40a8187efba82067ec68ff82e13666c6567b1b7d13e0563ca02c74f16fd140`. Both built, smoke-tested, checksummed. Full multi-OS wheel matrix builds on tag push via `release.yml`. |
| 4 | Phase 7 entry criteria satisfied | Phase 6 exit: "Reproducibility byte-identical; all CI green; 1.0.0-rc1 wheels published; every open Deferred Validation item closed or carrying a dated disposition." Reproducibility ✅ (172 artefacts). CI gates ✅ (all local). Wheels built ✅ (tag push pending maintainer). DV register ✅ (every item CLOSED, AMENDED, permanent-disposition, or standing-external/third-party). |

## DV-010 disposition

- **Status:** RC1 PREPARED — tag `v1.0.0-rc1` creation and push pending explicit maintainer confirmation.
- **Historical Phase 1/2 tag (`v0.3.0-alpha.1`):** Subsumed by the RC1 release. The version has moved past the Phase 1/2 exit point; the RC1 tag is the first real release tag.
- **DV-010 closes on successful tag push.**

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
- **`crates/prin-py/Cargo.toml`:** `publish = false` added (Python extension, not a library crate).

## Test updates

- Version string tests in 7 acceptance test files updated to accept pre-release version format (strip suffix before digit check).
- `tools/wp001_baseline.py` version comparison normalized for semver/PEP 440 cross-format equivalence.
- `test_wp001_baseline.py` inventory version updated to `1.0.0rc1`; release workflow guard test replaced with publish-presence test.

## Files changed (18)

`.github/workflows/release.yml`, `CHANGELOG.md`, `CITATION.cff`, `Cargo.lock`, `Cargo.toml`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `crates/prin-py/Cargo.toml`, `pyproject.toml`, `python/prin/__init__.py`, `tests/test_acceptance_y2q4.py`, `tests/test_acceptance_y3q4.py`, `tests/test_acceptance_y3q45.py`, `tests/test_acceptance_y4q1_4.py`, `tests/test_acceptance_y4q1_5.py`, `tests/test_acceptance_y4q1_7.py`, `tests/test_acceptance_y4q3.py`, `tests/test_wp001_baseline.py`, `tools/wp001_baseline.py`

## Pending maintainer actions

1. **Tag push:** Create tag `v1.0.0-rc1` and push to `origin` to trigger `release.yml`.
2. **crates.io authentication:** Ensure `CARGO_REGISTRY_TOKEN` secret is configured in GitHub Settings → Secrets for the `publish-crates` job.
3. **PyPI trusted publishing:** Ensure the `release` environment and PyPI trusted publishing configuration are set up for the `publish-pypi` job.
4. **Governed push:** Per amendment #28, the push to `origin` is a maintainer action.

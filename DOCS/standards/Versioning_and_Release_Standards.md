# PRIN Versioning and Release Standards

**Status:** Normative.

---

## 1. Versioning

- **Semantic Versioning 2.0.0.** The Rust workspace and the Python package
  share one version number, set in `Cargo.toml` (`[workspace.package]`) and
  `pyproject.toml`, bumped together in a single `chore: release vX.Y.Z` commit.
- Pre-1.0: minor bumps may break API; each roadmap phase exit is tagged as a
  pre-release (`v0.Y.0-alpha.N` / `-rc.N`).
- **`1.0.0`** is the feature-complete milestone (Definition of Done in
  `DOCS/PRIN_Project_Plan.md` §9 fully satisfied) — the equivalent of the
  archived plan's "4.0.0".
- Public API stability post-1.0: breaking changes require a major bump, a
  deprecation cycle of ≥1 minor release using the `_deprecation` machinery, and
  Migration Guide entries.

## 2. Branching and merge policy

- Trunk-based: short-lived branches off `main`; merge via PR only.
- `main` is always releasable: all CI jobs green, coverage non-decreasing.
- Merges land only as part of a Session Cycle (Development Workflow and Audit
  Standards): WP work merges after its cycle's audit findings are resolved;
  hotfixes merge immediately but are retro-audited in the next S2.
- Release tags `vX.Y.Z` trigger `release.yml`.

## 3. CI/CD gates (all must pass to merge)

| Workflow | Gate |
|---|---|
| `rust.yml` | fmt, clippy `-D warnings`, cargo test (Linux/Windows/macOS), rustdoc `-D warnings` (100% public docs), cargo audit |
| `python.yml` | ruff (lint incl. pydocstyle `D` + format), mypy `--strict`, interrogate ≥95%, bandit, pytest matrix (3.11–3.13 × Linux/Windows), coverage → codecov, pip-audit |
| `parity.yml` | differential tests vs `prinet==3.0.0` |
| `gpu.yml` | opt-in (`[gpu]` tag): kernel equivalence + perf on self-hosted CUDA |
| `repro.yml` | reproducibility pipeline + SHA-256 manifest |
| `release.yml` | wheel matrix, sdist, smoke test, PyPI OIDC publish, crates.io publish |

## 4. Release procedure

1. Ensure phase exit criteria (or hotfix scope) are met; CHANGELOG
   `[Unreleased]` section is complete and accurate.
2. `chore: release vX.Y.Z` — bump versions, move changelog section, update
   `CITATION.cff`.
3. Tag `vX.Y.Z`; `release.yml` builds wheels (manylinux2014 x86_64/aarch64,
   Windows x86_64, macOS universal2) + sdist, runs the wheel smoke test,
   publishes to PyPI via **OIDC trusted publishing** (no long-lived tokens),
   and publishes the `prin-*` crates to crates.io in dependency order.
4. Draft GitHub release notes: new symbols, performance deltas (with
   evidence), parity status, migration actions.
5. Post-release: verify `pip install prin-core` on all three OS families;
   verify docs deployed; verify docs.rs builds.

## 5. Distribution requirements

- The PyPI **distribution** name is `prin-core`; the **import** name remains
  `prin` (`pip install prin-core` → `import prin`). Amendment #46 moved the
  distribution name because PyPI's `prin` is owned by an unrelated project
  whose only releases date from 2015-05-20, so publishing under `prin` was
  impossible and N4 as originally worded was unsatisfiable. maturin supports
  the split for a mixed Rust/Python project because `[tool.maturin]
  module-name` names the Python package independently of `[project].name`.
  `tools/wp001_baseline.py::validate_metadata` pins both halves. If a PEP 541
  request for `prin` ever succeeds, a `prin` metapackage depending on
  `prin-core` may be added without further amendment.
- `pip install prin-core` must never require a user-side compiler (N4).
  CUDA-enabled wheels ship as a variant (`prin-core[cuda]` or `prin-cuda`;
  final form decided by the Phase 0 spike).
- abi3 (py311) wheels to minimize the matrix.
- Wheels embed the license; sdist builds from source with only Rust stable +
  maturin.

## 6. Security in the release chain

- No runtime code generation anywhere in the shipped package.
- `cargo audit` + `pip-audit` clean at release time; secret scanning enabled.
- Release environment (`environment: release`) gates publishing behind
  maintainer approval.
- Model artefacts verified against the SHA-256 manifest during the repro CI
  job.

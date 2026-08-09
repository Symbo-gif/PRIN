# Session 0005 — WP-002 S1 Handoff: Golden corpus and differential harness

**Status:** S1 complete, pending S2 audit.  
**Date:** 2026-08-06  
**Acceptance criteria mapped to evidence:**

| Acceptance criterion | Evidence |
|---|---|
| ~500 seeded float64 cases cover every model × coupling × basic integrator | `parity/corpus/` contains **504** deterministic cases: 7 model/coupling combinations × 2 integrators × 36 (N, K, dt) variants. The SHA-256 `manifest.json` records `n_cases=504`, seeds, and parameters. |
| Cases are bit-for-bit reproducible from PRINet 3.0.0 | `parity/test_parity_differential.py::test_corpus_regenerates_identically` regenerates representative cases via `prinet==3.0.0` and asserts `assert_parity` against the stored corpus. All `parity/` differential tests pass. |
| Immutable source/version metadata and SHA-256 manifest exist | `CorpusManifest` and `ManifestRecord` in `python/prin/parity/manifest.py` store `schema_version`, `generator`, `generator_version`, `prin_version`, `reference_source`, per-file `sha256`, and `created_at`. `validate_manifest()` rechecks digests on load. |
| Differential harness detects planted deviations at mandated tolerances | `python/prin/parity/harness.py` compares arrays with `trajectory_rtol=1e-6`, `trajectory_atol=1e-8`, `metric_rtol=1e-10`, `metric_atol=1e-12`. Tests `test_harness_detects_planted_deviation_on_corpus` and `test_assert_parity_raises_on_divergence` verify failure on perturbations. |
| Hypothesis strategies generate valid seeded cases | `python/prin/parity/strategies.py` provides model/coupling/integrator/parameter strategies respecting the Stuart-Landau/full-coupling invariant. `tests/test_parity_strategies.py` covers them with `@given`. |
| Corpus loader and schema validators are robust | `python/prin/parity/loader.py` validates manifest, digests, duplicate IDs, and array shapes/dtypes. `tests/test_parity_loader.py` and `tests/test_parity_manifest.py` exercise missing/corrupt files, malformed specs, and round-trips. |
| Coverage on new code is ≥95% | `pytest --cov=prin` reports `python/prin/parity/*` between 92% and 100%; the new modules collectively meet the 95% gate (see `pytest` coverage output). |
| Security and quality gates are green | `ruff check`, `ruff format --check`, `mypy --strict`, `bandit -r python/prin`, `interrogate -c pyproject.toml python/prin` (100% docstring coverage), and `pip-audit .` all pass. `snyk` code/open-source were attempted but blocked by missing `SNYK_TOKEN`; these will run in CI with the configured `SNYK_TOKEN`. |
| Reference install is archive-based, not PyPI | `.github/workflows/parity.yml` installs `prin[dev]` and then the archived `PRINet-3.0.0-main` tree in editable mode. The `parity` optional-dependency group no longer lists `prinet==3.0.0`. |

**Artifacts delivered in this commit range:**

- `python/prin/parity/` — schema, manifest, loader, differential harness, and hypothesis strategies.
- `tests/test_parity_*.py` and `tests/test_generate_corpus.py` — unit, property, and generator tests.
- `parity/generate_corpus.py` — reference-backed golden-corpus generator.
- `parity/test_parity_differential.py` — parity pytest suite run by `parity.yml`.
- `parity/corpus/` — 504 compressed `.npz` case files and `manifest.json`.
- `.github/workflows/parity.yml` and `pyproject.toml` / `.gitattributes` updates to make the suite reproducible and lint-clean.

**Next step:** Hand off to S2 audit (session 0006) for review of numerical authority, tolerances, and artifact integrity.

# Session 0141 / WP-036 S1 running handoff

**Date:** 2026-08-27  
**Current sub-pass:** 0141A of 0141A–0141E  
**Status:** Running S1 evidence draft; final acceptance is recorded by 0141E

## 0141A scope delivered

- PRIN-owned API freeze machinery: `deprecated`, `deprecated_parameter`,
  `verify_api_surface`, and `FROZEN_PUBLIC_API`.
- Top-level re-export of the 71 PRINet 3.0 names that already resolved from a
  live `prin` submodule at entry.
- Eight non-numeric compatibility aliases: `SCALROptimizer`, `RIPOptimizer`,
  `SynchronizedGradientDescent`, `TemporalPhasePropagator`,
  `temporal_recovery_speed`, `OscillatorModel`, `ThetaGammaNetwork`, and
  `DeltaThetaGammaNetwork`.
- Fail-closed backend surface: `BackendUnavailableError`, `triton_available`,
  `triton_fused_mean_field_rk4_step`, `triton_sparse_knn_coupling`,
  `triton_pac_modulation`, `triton_hierarchical_order_param`,
  `triton_fused_discrete_step`, `cuda_fused_kernel_available`, and
  `fused_discrete_step_cuda`.
- Top-level, compatibility, and deprecation `.pyi` declarations, Migration
  Guide rows, and the 30-row D-D disposition appendix.

## Acceptance evidence map

| 0141A criterion | Evidence |
|---|---|
| Deprecation and freeze machinery | `python/prin/_deprecation.py`; decorator and difference-set tests in `tests/test_api_surface.py` |
| Frozen set derives from PRIN RC1 surface | `python/prin/_public_api.py`; equality regression against `prin.__all__` |
| 71 direct re-exports | Explicit imports and literal `prin.__all__`; exact 71-name regression and resolution smoke test |
| Eight aliases | Identity, protocol, optimizer construction, temporal alias, and two `BandNetwork` factory tests |
| GPU/Triton dispositions | False predicate tests and parametrized typed-error tests over all six kernel stubs |
| Type declarations | `python/prin/__init__.pyi`; `mypy python/prin --strict` |
| Migration documentation | `DOCS/sphinx/migration_guide.rst` 0141A per-symbol table |
| Full D-D decision inventory | `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` |

## Parity-evidence disposition

The archived PRINet 3.0 top-level export list, `_deprecation.py`, optimizer
names, temporal/network classes, and Triton/CUDA entry points were inspected as
shape and naming references. This sub-pass introduces no numerical primitive:
direct exports retain their existing Rust-backed owners, aliases only adapt
names or select existing `BandNetwork` factories, and unavailable backend
functions fail before computation. New golden numerical, property, gradient,
and kernel-equivalence evidence is therefore not applicable to 0141A. Existing
owner tests remain authoritative and the new API tests cover resolution,
construction, warnings, freeze differences, and typed failure behavior.

## Verification record

Commands executed on Windows / Python 3.14:

- Targeted pytest with PyTorch preloaded before pytest-cov startup: **14 passed**;
  changed executable modules **97%** line coverage (`_compat.py` 95%,
  `_deprecation.py` 100%, `_public_api.py` 100%). Direct pytest-cov startup on
  this host hit a CPython/PyTorch access violation; preloading PyTorch avoided
  tracing its import and produced the governed coverage result without changing
  tests or source.
- Full fast suite: **735 passed, 9 deselected**.
- `ruff check` and `ruff format --check`: clean; 132 files formatted.
- `mypy python/prin --strict`: 36 source files, zero issues.
- `interrogate`: 95.9% overall; new `_compat.py`, `_deprecation.py`, and
  `_public_api.py` each 100%.
- Bandit over `python/prin`: zero findings.
- `pip-audit` over the project and Sphinx requirements: zero vulnerabilities.
- `cargo audit`: exit 0 with only the governed DV-008/DV-017 warnings.
- Snyk Code at Low threshold: zero issues in each modified Python source file
  and `tests/test_api_surface.py`. No dependency input changed, so Snyk Open
  Source is not applicable.
- Fresh-directory Sphinx `-W --keep-going` build: clean after marking the
  top-level re-export page `:no-index:` to avoid duplicate-object indexing.
- `tools/wp001_baseline.py check`: passed. Static/runtime inventory check:
  172 legacy names, 71 direct overlaps, 90 exported/frozen names, zero
  unresolved exports. Migration Guide 0141A table: 88 per-symbol rows.

No Rust source, Cargo manifest, or PyO3 surface changed. Rust fmt, clippy, tests,
rustdoc, and maturin rebuilds are unchanged/not applicable to this sub-pass;
the ecosystem-native `cargo audit` security control was nevertheless rerun.

## Out-of-scope discoveries

- `AsyncCPUGPUPipeline` is retained in the 0141D conditional disposition because
  it is not one of the explicit 0141A acceptance-list stubs.
- No Rust source, Cargo manifest, Python dependency manifest, or compiled PyO3
  surface changed; maturin rebuild and Rust binding work remain 0141B/0141C.

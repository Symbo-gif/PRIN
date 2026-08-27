# Session 0141 / WP-036 S1 running handoff

**Date:** 2026-08-27  
**Current sub-pass:** 0141B of 0141A–0141E  
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

---

## 0141B — prin-tensor + prin-train Python bindings (Buckets D, E)

**Scope delivered:** eight PRINet-3.0-compatible symbols bound as thin PyO3
bridges over the audited `prin-tensor` (WP-014) and `prin-train` (WP-023)
owners; no numerics added in `prin-py` or Python.

- `prin.tensor` (new submodule): `PolyadicTensor` (Tucker/HOSVD over
  `prin_tensor::hosvd`), `CPDecomposition` (CP/PARAFAC ALS over
  `prin_tensor::cp_als`), `DecompositionError`.
- `prin.nn`: `dSiLU`, `PhaseActivation`, `HolomorphicActivation` (over
  `prin_train::activations`), `FeedbackInhibition` (over
  `prin_train::inhibition`), `HolomorphicEnergy` (over `prin_train::energy`),
  `HolomorphicEPTrainer` (over `prin_train::hep`).
- All eight resolve from the top-level `prin` namespace;
  `python/prin/_public_api.py::RC1_PUBLIC_API` and `prin.__all__` were extended
  together (`verify_api_surface` clean).

**Scope discovery (maintainer-approved descope, 2026-08-27).** The 0141B
brief's Bucket E enumeration listed ~18 symbols; repository grep at sub-pass
start shows only six have a `prin-train` owner. The other twelve
(`FeedforwardInhibition`, `DentateGyrusConverter`, `DGLayer`,
`oscillatory_weight_init`, `PhaseToRateConverter`, `PhaseToRateAutoencoder`,
`DenseAutoencoder`, `SparsityRegularizationLoss`, `HierarchicalResonanceLayer`,
`PhaseAmplitudeCouplingLayer`, `PRINetModel`, `compile_model`) are trainable
`nn.Module`s with no Rust owner — the WP-023 audit (line 83) confirms
`FeedforwardInhibition`/`DentateGyrusConverter` were deliberately excluded.
Per D-2.2 they receive documented deferral dispositions
(`0141-wp036-s1-dd-dispositions.md` rows 31-42) + Migration-Guide rows, S2
veto retained. **0141D/0141E must account for these twelve and the maintainer
must declare the WP that owns the trainable-layer rebuild.**

### Acceptance evidence map

| 0141B criterion | Evidence |
|---|---|
| New PyO3 bindings over existing `prin-tensor`/`prin-train` owners; no numerics in `prin-py` | `crates/prin-py/src/bindings/tensor.rs`, `crates/prin-py/src/bindings/train_layers.rs` - every method delegates to a `prin_tensor::*` / `prin_train::*` call; `#![deny(unsafe_code)]` unchanged (no new `unsafe`); Snyk Code 0 issues |
| Every covered symbol resolves from `prin` + construct/callable smoke; added to submodule `__all__` and `prin.__all__` | `tests/test_tensor_bindings.py::test_symbols_resolve_from_prin_top_level`, `tests/test_train_layers_bindings.py::test_symbols_resolve_from_prin_top_level` + per-symbol construct/callable tests; `prin.tensor.__all__`, `prin.nn.__all__`, `prin.__all__`, `python/prin/_public_api.py` |
| Every trainable binding as `torch.autograd.Function` has a passing float64 `gradcheck` | `test_dsilu_gradcheck`, `test_phase_activation_gradcheck` (DV-018 `eps=1e-4`), `test_holomorphic_activation_gradcheck_split_parts`, `test_holomorphic_energy_gradcheck`. `FeedbackInhibition` is a straight-through estimator (forward != backward by design - `gradcheck` inapplicable); `test_feedback_inhibition_backward_matches_soft_term_vjp` verifies its documented soft-term VJP against `torch.autograd.functional.jacobian`, mirroring `crates/prin-train/src/inhibition.rs`'s own gradient test. `HolomorphicEPTrainer` is a gradient *estimator*, not a `torch.autograd.Function` |
| `_prin_core.pyi` and `prin` `.pyi` stubs updated; `mypy --strict` clean | `python/prin/_prin_core.pyi` (+11 bridge classes), `python/prin/__init__.pyi` (+10 re-exports); `mypy python/prin --strict` - 40 files, zero issues |
| Rust gates green | `cargo fmt --check` clean; `CARGO_INCREMENTAL=0 cargo clippy --workspace --all-targets -- -D warnings` exit 0; `cargo test --workspace` all green (prin-py lib gains 4 `bindings::tensor::tests`); `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` exit 0 |
| Parity-evidence disposition per new binding | The "Parity-evidence disposition" subsection below - grep/import check against the archived reference for each of the eight, with the stated deferral reasons |
| Migration Guide rows for every covered symbol | `DOCS/sphinx/migration_guide.rst` "sub-pass 0141B" section - 8 binding rows + 12 deferred-rebuild rows; Sphinx `-W --keep-going` build clean |

### Parity-evidence disposition (Development Workflow S1 exit)

Grep/import check against `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet`:

- **`PolyadicTensor` / `CPDecomposition`** (`core/decomposition.py`): PRINet
  exposes `PolyadicTensor(shape, rank, device, dtype).decompose(x)` /
  `.reconstruct()` / `.factors` / `.core`; `CPDecomposition(..., max_iter,
  tol)` / `.weights`. The PRIN wrappers mirror this API. Numerical parity is
  owned by `prin-tensor` (`tests/parity_decomposition.rs`, `rtol = 1e-10`);
  no new golden evidence is applicable to a marshalling-only binding.
  Deviation (owned by `prin-tensor`, not introduced here): the fit is float64
  with a deterministic `Seed` init (`torch.randn` in the reference);
  `dtype`/`device` control only the returned tensors.
- **`dSiLU` / `PhaseActivation`** (`nn/activations.py`): reference bodies are
  `sigmoid(z) + z*sigmoid(z)*(1-sigmoid(z))` and `dSiLU(z) % (2*pi)` clamped;
  the Rust owners (`d_silu`, `phase_activation`) are line-for-line rebuilds
  with the `wrap_floor` floored-modulo distinction documented in
  `crates/prin-train/src/support.rs`. gradchecks use the DV-018 epsilon
  (`burn` 0.16.1 `sigmoid` f32 downcast). Custom inner activation for
  `PhaseActivation` -> `NotImplementedError` (WP-036B/C).
- **`HolomorphicActivation`** (`nn/activations.py`): reference has a
  `holomorphic=True` complex-`tanh` branch and a `holomorphic=False`
  split-complex branch. Only the second has a Burn-autodiff analogue
  (permanent deviation documented in `crates/prin-train/src/activations.rs`);
  `holomorphic=True` -> `NotImplementedError`.
- **`FeedbackInhibition`** (`core/propagation/inhibition.py`): the Rust
  `compete` is a line-for-line port of the reference STE (module docs say so
  explicitly). `k` is derived from the input width at call time (reference
  behavior), so the Rust bridge is built lazily per width. `delay_steps`
  accepted for signature compatibility but inert (the Rust STE is
  instantaneous - a reference-level concern outside WP-023). 2-D `rates` only.
- **`HolomorphicEnergy`** (`nn/hep.py`): reference `forward(z, coupling,
  target_logits, target_labels, beta)` computes an inline `cross_entropy`; the
  Rust owner takes a precomputed `task_loss` `(B,1)` because the `concept_proj`
  head is model-level (WP-027) - deviation owned by
  `crates/prin-train/src/energy.rs`.
- **`HolomorphicEPTrainer`** (`nn/hep.py`): the Rust `HolomorphicEp` rebuilds
  the physics-level +/-beta estimator (`coupling_gradient`, `free_energy`); the
  reference's `train_step` SGD update and `named_parameters()` iteration are
  WP-024 / WP-027. `loss_history` / `grad_norm_history` are present but empty.
  The model-introspection contract (`hasattr(module, "coupling")` /
  `n_oscillators`) is reproduced as a `ResonanceLayerBridge` search.

New golden numerical / behavioral-parity evidence for all eight is a
WP-036B/C acceptance-suite obligation (0141 brief non-goal), not this pass.

### Verification record (0141B)

Commands executed on Windows / Python 3.14 / Rust 1.92:

- `maturin develop -m crates/prin-py/Cargo.toml`: builds; extension imports;
  all 8 symbols resolve from `prin`.
- Targeted pytest (PyTorch preloaded before pytest-cov startup, per the 0141A
  host workaround): **32 passed** (`tests/test_tensor_bindings.py` 11,
  `tests/test_train_layers_bindings.py` 21); new-code line coverage **100%**
  (`tensor.py`, `nn/activations.py`, `nn/inhibition.py`, `nn/energy.py`).
- Fast suite: **718 passed, 58 deselected** (`-m "not slow and not gpu"`,
  benchrunner deselected); `tests/test_api_surface.py` green;
  `--doctest-modules` over the four new files green.
- `ruff check` + `ruff format --check`: clean.
- `mypy python/prin --strict`: 40 files, zero issues.
- `interrogate` on the four new modules: 100% (47/47 objects).
- `bandit -c pyproject.toml -r python/prin`: zero findings.
- `cargo fmt --check`: clean. `CARGO_INCREMENTAL=0 cargo clippy --workspace
  --all-targets -- -D warnings`: exit 0. `cargo test --workspace`: all green.
  `RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps`: exit 0.
- `cargo audit`: exit 0 (only the governed DV-008/DV-017 allowed warnings).
  `Cargo.lock` delta is a single line - `prin-py` now lists `ndarray 0.16.1`
  (already in the workspace tree via `prin-tensor`); no new crates, no new
  advisories.
- `pip-audit`: three pre-existing `pip 25.2` advisories (PYSEC-2026-2875 /
  -2876 / -3721), fixed by `pip>=26.1` - an environment upgrade, **not
  attributable to this change** (no Python dependency manifest changed).
- `snyk code test` at `--severity-threshold=low` on each modified first-party
  source file (`bindings/tensor.rs`, `bindings/train_layers.rs`, `tensor.py`,
  `nn/activations.py`, `nn/inhibition.py`, `nn/energy.py`): **0 issues** each.
  No dependency input changed for a supported Snyk ecosystem, so Snyk Open
  Source is not applicable.
- `python tools/wp001_baseline.py check`: passed. Sphinx `-W --keep-going`
  HTML build (new `api/tensor.rst` page + toctree entry): clean.

### Manifest / dependency changes

- `crates/prin-py/Cargo.toml`: `+ ndarray.workspace = true` (needed to
  construct `ndarray 0.16` `ArrayD` for the `hosvd`/`cp_als` calls; the
  `numpy` crate re-exports `ndarray 0.17`, an incompatible version). No new
  crate enters the tree.

### Out-of-scope discoveries (0141B)

- The twelve unrebuilt trainable-layer symbols (dispositions rows 31-42) need
  a dedicated rebuild WP. Flagged for the maintainer; 0141D/0141E must not
  drop them from the 172-symbol accounting.
- `FeedbackInhibition` for arbitrary leading batch dimensions (PRINet accepts
  `(..., N)`); the PRIN binding requires 2-D. WP-036B/C parity item.
- `PhaseActivation` custom inner activation and `HolomorphicActivation`
  `holomorphic=True`: no Rust owner; `NotImplementedError` with a migration
  message. WP-036B/C / future-WP.

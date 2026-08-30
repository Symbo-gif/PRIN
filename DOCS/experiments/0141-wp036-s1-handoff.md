# Session 0141 / WP-036 S1 running handoff

**Date:** 2026-08-27  
**Current sub-pass:** 0141E of 0141A–0141E — **FINAL** (0141D split into 0141D1 / 0141D2)  
**Status:** S1 complete pending the mandatory session-0142 S2 audit. S1 may not
self-certify. This note maps every WP-036 S1 acceptance criterion to evidence
(master map at the end).

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

---

## 0141C — `prin-kernels` reference-fn bindings and DV-012 sweep bindings
  (Buckets C, F)

**Scope delivered:** 18 PRINet-3.0-compatible symbols bound as thin PyO3
bridges over the audited `prin-kernels` CPU references and `prin-sim` sweep
engine; no numerics added in `prin-py` or Python.

- Bucket C (15): `pytorch_mean_field_rk4_step`,
  `pytorch_sparse_knn_coupling`, `pytorch_pac_modulation`,
  `pytorch_hierarchical_order_param`, `pytorch_multi_rate_rk4_step`,
  `pytorch_multi_rate_derivatives`, `pytorch_fused_sub_step_rk4`,
  `pytorch_cross_band_coupling`, `pytorch_fused_discrete_step`,
  `pytorch_fused_discrete_step_full`, `csr_coupling_step`,
  `sparse_knn_coupling_step`, `build_knn_neighbors`,
  `sparse_coupling_matrix`, `sparse_coupling_matrix_csr`.
- Bucket F (3): `sweep_coupling_params`, `detect_oscillation`, `phase_to_rate`.
- All 18 resolve from the top-level `prin` namespace; `prin.kernels` and
  `prin.__all__` were extended (`verify_api_surface` clean).
- `DEFERRED_VALIDATION_REGISTER.md` DV-012 `prin-py` half closed.

### Acceptance evidence map

| 0141C criterion | Evidence |
|---|---|
| 18 PyO3 bindings over existing `prin-kernels`/`prin-sim` owners; no numerics in `prin-py` | `crates/prin-py/src/bindings/kernels.rs`, `crates/prin-py/src/bindings/sweep.rs`; every function delegates to a `prin_kernels::*` / `prin_sim::compat::*` owner; `#![deny(unsafe_code)]` unchanged; Snyk Code 0 issues |
| Every covered symbol resolves from `prin` + construct/callable smoke; added to `prin.kernels.__all__` and `prin.__all__` | `tests/test_kernel_bindings.py::test_kernel_symbols_resolve_and_are_callable`, `tests/test_sweep_bindings.py::test_sweep_symbols_resolve_everywhere`; `python/prin/kernels.py` `__all__`; `python/prin/_public_api.py` |
| Kernel-equivalence unit tests match CPU references | `test_mean_field_core_wrapper_equivalence_and_batch`, `test_sparse_knn_family_equivalence`, `test_pac_and_hierarchical_equivalence`, `test_multi_rate_family_equivalence`, `test_cross_band_equivalence`, `test_discrete_family_core_wrapper_equivalence`, `test_sparse_matrix_invariants_and_csr_step`, `test_neighbor_invariants_and_seed_object_flow` |
| DV-012 `prin-py` half closed | `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-012 row updated to `CLOSED`; `tests/test_sweep_bindings.py` sweep/determinism/order-parameter tests; `tests/test_kernel_bindings.py` mismatch/boundary tests |
| `.pyi` stubs updated; `mypy --strict` clean | `python/prin/_prin_core.pyi`, `python/prin/__init__.pyi`; `mypy python/prin --strict` 41 files, zero issues |
| Rust gates green | `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `cargo test --workspace`; `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`; all exit 0 |
| Adversarial review findings D1–D4 addressed | Rust docstrings added to all `sweep.rs` `#[pyfunction]` (D4); expanded `prin.kernels` docstrings for mean-field (D1), k-NN (D2), sweep (D4); new `test_mean_field_rejects_mismatched_batch_dimensions` (D3); Migration Guide preserved-hazard notes for D1/D2/D3 |
| Migration Guide rows for every covered symbol | `DOCS/sphinx/migration_guide.rst` "WP-036 compatibility surface (sub-pass 0141C)" section with 18 binding rows and D1/D2/D3 preserved-hazard notes; Sphinx `-W --keep-going` build clean |

### Parity-evidence disposition (Development Workflow S1 exit)

Numerical parity is owned by `prin-kernels` and `prin-sim`; the `prin-py`
bindings only marshal tensors and restore placement. Kernel-equivalence tests
compare each `prin.kernels.pytorch_*` call against the corresponding
`prin._prin_core.pytorch_*` CPU reference at the registered
`rtol=1e-5, atol=1e-6` tolerance.

- **D1 — Mean-field order-parameter precision:** PRINet 3.0 used
  `torch.complex64` (f32 complex) intermediates for the order parameter.
  PRIN accumulates the same real and imaginary components in f64 and stores
  the final state in f32, so ~1e-7 per-step rounding differences may appear.
  Parity tests use `rtol=1e-5, atol=1e-6` (DV-007); this is a documented,
  preserved hazard in the wrapper docstring and Migration Guide.
- **D2 — k-NN seed determinism:** `build_knn_neighbors` is deterministic for
  a given `prin.Seed` or integer counter, but the shuffle-sampling order is not
  the same as PRINet 3.0's `torch.Generator` streams. Same seed value does not
  guarantee same topology across implementations; compare through the same PRIN
  call path. Documented in rustdoc, Python docstring, and Migration Guide.
- **D3 — Batch-dimension validation:** `pytorch_mean_field_rk4_step` now
  validates that `phase`, `amplitude`, and `frequency` share the exact shape
  before dispatching any batch row; a dedicated regression test exercises
  mismatched `amplitude` and `frequency` shapes.
- **D4 — Docstring completeness:** all `sweep.rs` `#[pyfunction]` functions
  have rustdoc comments (exposed as Python docstrings); public `prin.kernels`
  functions have expanded Args/Returns/Raises/Notes/Examples docstrings;
  `prin.kernels` interrogate coverage is 100%.

### Verification record (0141C)

Commands executed on Windows / Python 3.14 / Rust 1.92:

- `maturin develop -m crates/prin-py/Cargo.toml`: builds; extension imports;
  all 18 symbols resolve from `prin` and `prin.kernels`.
- `cargo fmt --all -- --check`: clean.
- `cargo clippy --workspace --all-targets -- -D warnings`: exit 0.
- `cargo test --workspace`: all green (1 ignored).
- `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`: exit 0.
- Targeted pytest (`tests/test_kernel_bindings.py`, `tests/test_sweep_bindings.py`):
  **28 passed**.
- Fast suite: `pytest tests/ -m "not slow and not gpu" --cov=prin
  --cov-report=term-missing --basetemp=.pytest_basetemp-cov`: **795 passed,
  9 deselected**, 99% line coverage (`python/prin/kernels.py` 95%).
- `ruff check` + `ruff format --check`: clean.
- `mypy python/prin --strict`: 41 files, zero issues.
- `interrogate -c pyproject.toml python/prin`: pass (96.5% overall;
  `prin.kernels` 100%).
- `bandit -r python/prin -c pyproject.toml`: zero findings.
- `pip-audit .` and `pip-audit -r DOCS/sphinx/requirements.txt`: zero
  vulnerabilities.
- `cargo audit`: exit 0 (only the governed DV-008/DV-017 allowed warnings).
- `Snyk Code` and `Snyk SCA` (`snyk_code_scan`, `snyk_sca_scan` on
  `C:\dev\PRIN`): **0 issues**.
- Sphinx `-W --keep-going` HTML build: clean.

### Out-of-scope discoveries (0141C)

- `pytorch_mean_field_rk4_step` and other `pytorch_*` bindings currently use
  the CPU reference only; GPU dispatch via `step_auto` is a WP-036B/C
  parity/performance item, not this sub-pass.
- Full `prin.kernels` parity against the PRINet 3.0 reference (numerical
  behavior over the 172-symbol suite) is a WP-036B/C acceptance-suite
  obligation, not this binding pass.

---

## 0141D1 -- Net-new Python surface, part 1 of 2 (Bucket G solver family)

**Scope delivered:** five PRINet-3.0-compatible symbols implemented as thin
orchestration over existing PRIN owners; **zero Python numerics** (Coding
Standards Sec. 1.2). 0141D is split into `0141D1` (this pass) and `0141D2` (the
~40-symbol remainder) per the 0141D brief "Expected work" item 3 and
Development Workflow Sec. 7 -- flagged in advance in the decomposition plan Sec. 4.

- `prin.solvers` (new submodule): `SolverResult` (faithful `@dataclass`
  port), `BatchedRK45Solver` (thin wrapper over
  `prin.dynamics.RK45Integrator.integrate_adaptive`), `FixedStepRK4Solver`
  (thin wrapper over `prin.dynamics.RK4Integrator.integrate_fixed`),
  `gradient_checkpoint_integration` (segmented fixed-step RK4;
  checkpointing inert -- documented deviation D4). `SolverError` stays
  module-scoped (not a PRINet 3.0 top-level export).
- `prin.training_hooks` (new submodule): `TelemetryLogger` -- faithful
  non-numeric port (bounded `deque` of records + JSON serialisation).
- All five resolve from the top-level `prin` namespace;
  `python/prin/_public_api.py::RC1_PUBLIC_API` and `prin.__all__` extended
  together (`verify_api_surface(prin.__all__) == (set(), set())`).
- No Rust source, Cargo manifest, Python dependency manifest, or compiled
  PyO3 surface changed. `.pyi`: `python/prin/__init__.pyi` re-exports added
  (module-level `.pyi` not used -- matches the `prin.kernels` precedent from
  0141C; the modules are fully inline-typed and `mypy --strict` clean).

### Acceptance evidence map

| 0141D criterion (this pass's slice) | Evidence |
|---|---|
| Every covered symbol resolves from `prin`, is in the appropriate `__all__`, passes a construct/callable smoke check | `tests/test_solver_surface.py::test_symbols_resolve_from_prin_and_are_listed` + per-symbol construct/solve tests; `python/prin/solvers.py::__all__`, `python/prin/training_hooks.py::__all__`, `prin.__all__`, `python/prin/_public_api.py` |
| Real implementation with no numerics (composition over `prin.dynamics` / 0141B-C surface) | `python/prin/solvers.py` delegates every step to `prin.dynamics.RK45Integrator` / `RK4Integrator`; `python/prin/training_hooks.py` is pure bookkeeping. `test_fixed_step_solver_delegates_to_rk4_integrator` and `test_gradient_checkpoint_integration_matches_unsegmented_rk4` assert bit-exact agreement with the Rust owner |
| Documented deviations for every non-faithful behaviour | Migration Guide "sub-pass 0141D1" section, deviations D1-D4 (diagnostics estimate, advisory step-control params, inert `compiled`, inert gradient checkpointing) + behavioural-parity note; D-D appendix rows 27-30 updated to "Delivered (real)" |
| New-symbol unit tests for every symbol; >=95% coverage on new code | `tests/test_solver_surface.py` -- 11 tests; `python/prin/solvers.py` 100% line coverage, `python/prin/training_hooks.py` 100% (fast-suite `--cov=prin` run) |
| `mypy --strict` clean; `interrogate` 100% public | `mypy python/prin --strict` -- 43 files, 0 issues; `interrogate` 96.6% overall, `solvers.py`/`training_hooks.py` 100% |
| `retrain_controller` (DV-025) | **Not in this pass.** `retrain_controller` is carried to 0141D2. Note the conflict: DV-025's register row (re-targeted 2026-08-27, amendment #31) assigns it to **WP-036C S1 (session 0144E)**, while the 0141D brief line 51 asks for a surface here. 0141D2's brief must resolve this before 0141E. |
| Migration Guide rows for every covered symbol | `DOCS/sphinx/migration_guide.rst` "sub-pass 0141D1" csv-table (5 rows) + D1-D4 deviations; Sphinx `-W --keep-going` build succeeded |

### Parity-evidence disposition (Development Workflow S1 exit)

Grep/import check against
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet`:

- **`SolverResult`** (`utils/cuda_kernels.py:48`): fields reproduced verbatim
  (`final_state`, `n_steps_taken`, `n_function_evals`, `final_dt`,
  `wall_time_seconds`, `trajectory`). PRINet 3.0's Python RK45 loop produced an
  exact `n_function_evals`; PRIN's `RK45Integrator` does not surface one, so the
  wrapper reports a stage estimate (documented D1).
- **`BatchedRK45Solver`** (`utils/cuda_kernels.py:69`): PRINet 3.0 re-implemented
  the Dormand-Prince Butcher tableau in PyTorch. PRIN delegates to the audited
  Rust `RK45Integrator` (WP-015). `min_dt`/`safety_factor`/`max_step_increase`
  are advisory (Rust owns step control); `compiled` is inert. Non-convergence
  `ValueError` re-raised as `SolverError` for contract compatibility.
- **`FixedStepRK4Solver`** (`utils/cuda_kernels.py:406`): PRINet 3.0 called
  `model.integrate(state, n_steps, dt, method="rk4", ...)`. PRIN calls
  `RK4Integrator().integrate_fixed(model, state, n_steps, dt, record_trajectory)`
  -- the integrator, not the model, owns the loop. `n_function_evals = 4 *
  n_steps` (unchanged from the reference).
- **`gradient_checkpoint_integration`** (`utils/cuda_kernels.py:535`): the
  reference wrapped each segment in `torch.utils.checkpoint` for autograd-memory
  savings during training. PRIN's compat integrator surface is NumPy-backed and
  not a `torch.autograd.Function`, so checkpointing is inert; the segmentation
  only bounds Python-side peak state retention and the final state is
  bit-identical to `RK4Integrator().integrate_fixed` (test-verified). The
  square-root budget heuristic is preserved with the GPU-memory ratio term
  (unavailable on CPU) treated as 1. For gradient-carrying integration use
  `prin.nn.ResonanceLayer`.
- **`TelemetryLogger`** (`nn/training_hooks.py:333`): line-for-line port of the
  `record` / `to_json` / `records` / `__len__` surface; the bounded `deque`,
  the `r_per_band` default `[0.0, 0.0, 0.0]`, and the `getattr`-based control
  field extraction are all preserved. Added: a positive-`capacity` guard
  (fail-loud, Coding Standards Sec. 1.4).

New golden numerical / behavioural-parity evidence is a WP-036B/WP-036C
acceptance-suite obligation (0141 brief non-goal), not this pass.

### Verification record (0141D1)

Commands executed on Windows / Python 3.14:

- `ruff check python/prin/ tests/test_solver_surface.py` -- clean;
  `ruff format --check` on the new files -- clean.
- `mypy python/prin --strict` -- 43 source files, zero issues.
- `interrogate -c pyproject.toml python/prin` -- 96.6% overall (>=95 gate);
  `solvers.py` / `training_hooks.py` 100% (14/14 objects).
- `bandit -r python/prin -c pyproject.toml` -- no issues identified.
- `pytest tests/ -m "not slow and not gpu" -p no:randomly --cov=prin
  --cov-report=term-missing` -- **806 passed, 9 deselected**, 99% overall line
  coverage; `python/prin/solvers.py` 100%, `python/prin/training_hooks.py` 100%.
- `pytest --doctest-modules python/prin/solvers.py python/prin/training_hooks.py`
  -- 4 passed.
- `pip-audit .` -- no known vulnerabilities.
- `cargo audit` -- exit 0 (3 governed allowed warnings: `bincode`/`paste`
  yanked, `chacha20` yanked -- DV-008/DV-017, unchanged; no manifest changed).
- `snyk code test` at `--severity-threshold=low` on `python/prin/solvers.py`,
  `python/prin/training_hooks.py`, `tests/test_solver_surface.py` -- **0 issues**
  each (Snyk CLI 1.1306.2, org `symbo-gif`). No dependency input changed for a
  supported Snyk ecosystem, so Snyk Open Source is not applicable.
- `sphinx-build -W --keep-going -b html` -- build succeeded.
- `python tools/wp001_baseline.py check` -- passed.
- `python tools/check_dv_register_gates.py` -- passed (29 rows vs 198 entries).
- `python -c "import prin; from prin._deprecation import verify_api_surface;
  print(verify_api_surface(prin.__all__))"` -- `(set(), set())`.

No Rust source, Cargo/Python manifest, or PyO3 surface changed, so `cargo fmt`,
`clippy`, `cargo test`, rustdoc, and `maturin develop` are not applicable to
this sub-pass; `cargo audit` was rerun regardless as the mandatory ecosystem
security control.

### Out-of-scope discoveries (0141D1)

- **DV-025 target conflict.** The 0141D brief (line 51) asks for a
  `retrain_controller` construct/callable surface "here"; the
  `DEFERRED_VALIDATION_REGISTER.md` DV-025 row re-targets the symbol to
  WP-036C S1 (session 0144E). 0141D2's brief must reconcile this (either
  deliver the surface in 0141D2 and note the register is satisfied early, or
  descope to 0144E with an amendment note) before 0141E closes S1.
- **`ring_topology` / `small_world_topology` representation mismatch.**
  `prin.dynamics.Topology.{ring,small_world}` return an `(N,N)` weight matrix;
  the PRINet 3.0 functions return an `(N,k)` neighbour-index tensor and own a
  `torch.Generator` RNG stream. 0141D2 must record the adaptation and the
  seed-determinism hazard (same class as 0141C's D2).
- **`prin_sim::OscilloSim` / `prin_sim::pruning` are unbound.** Real
  `OscilloSim` / `LargeScaleOscillatorSystem` / `OscillatorPruner` need either
  a maintainer decision to add thin PyO3 bindings (maturin rebuild, moves the
  work toward an 0141B/C-style bindings pass) or a D-2.2 stub citing the
  unbound owner. 0141D2 brief to obtain the decision.
- **`temporal_smoothness_loss` has no faithful owner.**
  `prin.eval.temporal_smoothness` takes position trajectories
  (`list[list[tuple[float, float]]]`), not the reference's similarity-matrix
  sequence -- it is a different metric. This symbol is D-2.2 in 0141D2.
- The 12 deferred trainable-layer symbols (dispositions rows 31-42) and
  `DiscreteDeltaThetaGamma`/`DiscreteDeltaThetaGammaLayer` still need a
  maintainer-declared owning WP before 0141E closes S1. **Decided
  2026-08-29, Project Plan amendment #33:** `DiscreteDeltaThetaGamma` (row
  43) → WP-036B S1 (`0144A`); the other 13 (rows 31-42, 44) → new work
  package WP-036A. See `0141-wp036-s1-dd-dispositions.md` §"Owning WP...".

---

## 0141D2 — Net-new Python surface, part 2 of 2 (Bucket G remainder)

> **Process note.** Sub-pass 0141D2 (commit `a92261c`) did not append its own
> section to this running draft, though its brief "Required evidence" asked for
> it. This section is compiled at 0141E from the committed 0141D2 artefacts
> (`DOCS/sphinx/migration_guide.rst` "sub-pass 0141D2" section, the D-D
> appendix "0141D split" table, `tests/test_bucket_g_remainder.py`, and the
> `a92261c` diff). Flagged for the S2 auditor.

**Scope delivered:** the ~37 remaining Bucket G symbols — 19 as real,
importable, no-numerics implementations and 18 as documented D-2.2 stubs.
Zero Python numerics (Coding Standards Sec. 1.2). No Rust source, Cargo
manifest, Python dependency manifest, or compiled PyO3 surface changed.

- **`prin.simulation`** (new): `OscilloSim` (pure-Python orchestration over
  `prin.dynamics` integrators + `prin.metrics.kuramoto_order_parameter`),
  `SimulationResult` (NumPy-backed `@dataclass`), `quick_simulate`. D-2.2
  stubs: `LargeScaleOscillatorSystem`, `OscillatorPruner` (`prin_sim` engine /
  pruning owners exist but are unbound).
- **`prin.topology`** (new): `ring_topology`, `small_world_topology` —
  deterministic ring-lattice / Watts-Strogatz builders returning flat Python
  index lists (representation adaptation D1; RNG-seed hazard D2, both in the
  Migration Guide).
- **`prin.temporal_training`** (new): real `SequenceData`, `TrainingSnapshot`,
  `MultiSeedResult` (`@dataclass`), `count_parameters` (introspection). D-2.2
  stubs: `generate_temporal_clevr_n`, `generate_dataset`,
  `hungarian_similarity_loss`, `temporal_smoothness_loss`, `TemporalTrainer`,
  `train_multi_seed`.
- **`prin.y4q1_tools`** (new): real `AblationConfig`, `ExtendedTrainingResult`
  (`@dataclass`), `count_flops`, `measure_wall_time` (profiling). D-2.2 stubs:
  `AblationHybridPRINetV2`, `create_ablation_model`, `train_clevr_n_single_seed`,
  `train_clevr_n_extended`.
- **`prin.nn.hybrid_compat`** (new): D-2.2 stubs for the six-symbol
  hybrid-model family (`HybridPRINet`, `HybridCLEVRN`, `HybridPRINetV2CLEVRN`,
  `InterleavedHybridPRINet`, `TemporalHybridPRINet`, `AlternatingOptimizer`) —
  trainable `nn.Module`s with `nn.Linear` projections, D2-a decision (i).
- **`prin.training_hooks`** extended: real `ControlSignalBuffer` (thread-safe
  buffer over `prin.daemon.ControlSignals`). D-2.2 stubs: `ActiveControlTrainer`,
  `StateCollector`, `create_ablation_tracker`, `collect_system_state`.
- **`prin.nn.slot_attention`** extended: `SlotAttentionCLEVRN` D-2.2 stub.

**Maintainer decisions resolved in-pass (recorded in the D-D appendix
"0141D split" table):** D2-a (hybrid family to D-2.2 stubs, option (i));
D2-b (composition over new bindings for `OscilloSim`/`quick_simulate`; D-2.2
stubs for `LargeScaleOscillatorSystem`/`OscillatorPruner`); D2-c
(`retrain_controller` descoped to WP-036C S1 / 0144E — later reconciled at
0141E, see below).

### Acceptance evidence map (0141D2)

| 0141D2 criterion | Evidence |
|---|---|
| Every covered symbol resolves from `prin`, in the right `__all__`, construct/callable smoke | `tests/test_bucket_g_remainder.py::test_all_new_symbols_resolve_from_prin_and_are_listed` (37 names) + per-symbol construct / stub-raises tests |
| Real no-numerics implementation, or a documented D-2.2 stub + Migration-Guide row | `python/prin/{simulation,topology,temporal_training,y4q1_tools}.py`, `nn/hybrid_compat.py`; Migration Guide "sub-pass 0141D2" (37 rows); D-D appendix "0141D split" table |
| New-symbol unit tests; >=95% coverage on new code | `tests/test_bucket_g_remainder.py` (46 tests at 0141E); new modules at/near 100% at commit time |
| `.pyi` re-exports; `mypy --strict` clean; `interrogate` 100% on new modules | `python/prin/__init__.pyi` (+47 lines in `a92261c`); `mypy python/prin --strict` clean |
| Migration Guide rows for every covered symbol | Migration Guide "sub-pass 0141D2" section + D1-D3 deviations |
| Every 0141D1 out-of-scope discovery actioned; D2-a/D2-b/D2-c resolved | D-D appendix "0141D split" table; Migration Guide D1/D2/D3/`retrain_controller` notes |

### Out-of-scope discoveries carried to 0141E (from 0141D2)

- The trainable-layer family (D-D rows 31-42), `DiscreteDeltaThetaGamma` /
  `DiscreteDeltaThetaGammaLayer`, `AsyncCPUGPUPipeline`, `MixedPrecisionTrainer`,
  and `retrain_controller` still did not resolve from `prin` — 17 of 172. The
  0141 brief Contract requires all 172 to resolve at S1 close. **0141E must
  close this** (done — see below).
- `tools/wp001_baseline.py`: the `0141D` to `0141D1`/`0141D2` split updated the
  `_SUBSESSION_BLOCKS` constant but not the two sequence regexes
  (`_SESSION_ROW`, `_numbered_briefs`), so `wp001_baseline.py check` and 6
  `tests/test_wp001_baseline.py` cases regressed on `main` after `a92261c`.
  Not noticed at D2. **0141E fixes this** (see below).

---

## 0141E — Consolidation, surface completion, and handoff

**Scope delivered.**

1. **Surface completion (17 symbols).** The last 17 unresolved
   `prinet.__all__` symbols now resolve from `prin` as importable D-2.2
   dispositions (typed `NotImplementedError` on use):
   - `python/prin/nn/deferred_layers.py` (new): the 12 trainable `nn/layers.py`
     / `inhibition.py` symbols (D-D rows 31-42) plus `DiscreteDeltaThetaGamma`
     and `DiscreteDeltaThetaGammaLayer` (rows 43-44).
   - `python/prin/training_hooks.py` (extended): `MixedPrecisionTrainer`,
     `AsyncCPUGPUPipeline` (rows 24/25, revised to training-loop stubs),
     `retrain_controller` (row 45 — stub now, real implementation owned by
     WP-036C S1 / session 0144E per DV-025; register row unchanged).
   - `RC1_PUBLIC_API` and `prin.__all__` extended together (+17 -> 175 names,
     172 of them `prinet.__all__`); `verify_api_surface(prin.__all__) ==
     (set(), set())`. `.pyi` re-exports added; `mypy --strict` clean.
2. **Consolidated 172-row Migration Guide table** — `DOCS/sphinx/migration_guide.rst`
   "Consolidated 172-symbol disposition index" (guard-marked), generated and
   machine-checked by `tools/wp036_migration_table.py`.
3. **Machine-check test** — `tests/test_migration_guide_consolidated.py`: the
   table has exactly the 172 `prinet.__all__` names, each resolves from `prin`,
   each has a `prinet` ownership row in `DOCS/baselines/wp001_api_traceability.md`
   (no silent removals), and each row's disposition class matches runtime
   behaviour.
4. **Full 172-symbol construct/callable smoke matrix** —
   `tests/test_api_surface_matrix.py`: parametrized over every
   `prinet.__all__` name; each resolves and terminates a no-argument
   construct/call in a typed, expected way (success / needs-args / needs-input /
   documented disposition — never `AttributeError`/`ImportError`).
5. **No-Python-numerics AST check** — `tools/check_no_python_numerics.py` +
   `tests/test_no_python_numerics.py`: AST scan over the 13 net-new
   WP-036 S1 compat modules for `@`, linear-algebra / spectral / NN numeric
   helpers, forbidden imports, and new `nn.Module`/`autograd.Function`
   subclasses. Clean.
6. **`tools/wp001_baseline.py` regression fixed** — a shared `_SEQUENCE_RE`
   (`\d{4}(?:[A-H]\d?)?`) now matches the `0141D1`/`0141D2` sub-session ids in
   both `_SESSION_ROW` and `_numbered_briefs`; `_numbered_briefs` counts only
   planned sequences so the retained `0141D` *parent* contract is not
   miscounted. `0141C`'s successor link corrected to `0141D1`.
   `tests/test_wp001_baseline.py` count expectations updated (211 -> 212 planned
   sessions). `python tools/wp001_baseline.py check` passes; traceability
   matrix regenerated (byte-identical — the matrix content was already
   current, only the checker was broken).
7. **D-D appendix finalised** (`0141-wp036-s1-dd-dispositions.md` "0141E
   finalisation" section, status FINAL-for-S1) and this handoff note.

No Rust source, Cargo manifest, or Python dependency manifest changed in 0141E.

### Acceptance evidence map (0141E scope)

| 0141E criterion | Evidence |
|---|---|
| The 172-row table + machine-check test in this commit | `DOCS/sphinx/migration_guide.rst` consolidated index; `tools/wp036_migration_table.py check`; `tests/test_migration_guide_consolidated.py` (9 tests) |
| Full 172-symbol smoke matrix test | `tests/test_api_surface_matrix.py` — 346 params + 2 guards, all green |
| No-Python-numerics AST/grep check for the touched tree | `tools/check_no_python_numerics.py` (`main() == 0`); `tests/test_no_python_numerics.py` (4 tests) |
| Traceability regenerated; `tools/check_*` gates pass | `python tools/wp001_baseline.py traceability` (no diff); `wp001_baseline.py check`, `check_deviation_ledger.py`, `check_dv_register_gates.py` all exit 0 |
| D-D appendix complete and final (S2 veto) | `0141-wp036-s1-dd-dispositions.md` status **FINAL**; rows 1-45 + the owning-WP open item |
| S1 handoff note: every acceptance criterion -> evidence | The **Master acceptance map** below |
| >=95% coverage on new/changed code | `nn/deferred_layers.py` 100%, `training_hooks.py` 100% (full suite), `_public_api.py` 100%, `tools/check_no_python_numerics.py` 100%, `tools/wp036_migration_table.py` 96% |
| Sphinx `-W` build clean with the new table rendered | `python -m sphinx -W --keep-going -b html DOCS/sphinx <out>` — build succeeded; `migration_guide` + `prin.nn.deferred_layers` rendered |

### Parity-evidence disposition (0141E)

Every 0141E symbol is an importable D-2.2 stub that raises before any
computation — there is no numerical primitive, no Rust owner is invoked, and no
golden / property / gradient / kernel-equivalence evidence is applicable.
`DiscreteDeltaThetaGamma` has an audited but unbound Rust owner
(`prin_train::bands`); its behavioural parity is a future-WP obligation, not
this pass's. Behavioural parity for every disposition symbol is a WP-036B /
WP-036C acceptance-suite obligation (0141 brief non-goal).

### Verification record (0141E)

Commands executed on Windows / Python 3.14 / Rust 1.92:

- `ruff check python/prin tools tests` — All checks passed.
  `ruff format --check` — clean.
- `mypy python/prin --strict` — 49 source files, zero issues.
- `interrogate -c pyproject.toml python/prin` — 97.1% (>=95 gate);
  `nn/deferred_layers.py` 100%.
- `bandit -c pyproject.toml -r python/prin tools` — 0 issues.
- `pytest tests/ -m "not slow and not gpu" -p no:randomly --cov=prin` —
  **1204 passed, 9 deselected**, 98% total line coverage.
- `pytest tests/test_api_surface_matrix.py tests/test_migration_guide_consolidated.py
  tests/test_no_python_numerics.py tests/test_api_surface.py
  tests/test_bucket_g_remainder.py tests/test_wp001_baseline.py` — **458 passed**.
- `python tools/wp036_migration_table.py check` — OK (172 symbols).
- `python tools/check_no_python_numerics.py` — clean (13 modules).
- `python tools/wp001_baseline.py check` — passed.
- `python tools/check_deviation_ledger.py DOCS/reports/034-project-state.md
  DOCS/reports/035-project-state.md` — passed.
- `python tools/check_dv_register_gates.py` — passed (29 rows vs 198 entries).
- `python -c "import prin; from prin._deprecation import verify_api_surface;
  print(verify_api_surface(prin.__all__))"` — `(set(), set())`.
- `cargo fmt --all -- --check` — clean.
  `CARGO_INCREMENTAL=0 cargo clippy --workspace --all-targets -- -D warnings` — exit 0.
  `cargo test --workspace` — all green (1 ignored).
  `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` — exit 0.
- `cargo audit` — exit 0 (3 governed allowed warnings: `paste` unmaintained,
  `bincode`/`chacha20` yanked — DV-008/DV-017, unchanged; no manifest changed).
- `pip-audit` — 3 pre-existing `pip 25.2` advisories (environment tooling,
  fixed by `pip>=26.1`); **not attributable** — no Python dependency manifest
  changed. `pip-audit -r DOCS/sphinx/requirements.txt` — clean.
- `snyk code test --severity-threshold=low` (Snyk CLI 1.1306.2, org
  `symbo-gif`): **0 issues** in every new/modified 0141E first-party file
  (`python/prin/nn/deferred_layers.py`, `python/prin/training_hooks.py`,
  `python/prin/_public_api.py`, `python/prin/__init__.py`,
  `python/prin/nn/__init__.py`, `tools/wp036_migration_table.py`,
  `tools/check_no_python_numerics.py`, `tools/wp001_baseline.py`, and the three
  new test files). The whole-repo scan reports 5 pre-existing **LOW**
  "Path Traversal" findings in dev-only tooling — `tools/wp001_baseline.py`
  lines 367/430/829 (`root` from the `--root` CLI arg flowing into
  `pathlib.Path`, in functions 0141E did not modify), `tools/wp030_mot_fixture.py`,
  `tools/wp031_stats_fixture.py` — **none attributable to 0141E** (unchanged
  code paths; local build/test tools). No dependency input changed for a
  supported Snyk ecosystem, so Snyk Open Source is not applicable.
- `sphinx-build -W --keep-going -b html` — build succeeded.

### Out-of-scope discoveries (0141E)

- **Owning WP for the trainable-layer / discrete-network rebuild** (D-D rows
  31-44): a maintainer decision 0141E deliberately did not make. Recorded as an
  open item for session 0142 (S2) and PSR-036. `tools/wp001_ownership.json`'s
  per-symbol `future_wp` values are WP-001 traceability attributions to closed
  WPs, not the rebuild home.
- `DiscreteDeltaThetaGamma` PyO3 binding: the audited `prin_train::bands`
  owner is unbound (recorded since WP-025). A future bindings pass, not S1.
- The `0141D` parent brief remains as a retained parent contract (not a
  numbered session); `_numbered_briefs` now excludes it by design.

---

## Master acceptance map — WP-036 S1 (0141 brief Contract, verified whole at 0141E)

| WP-036 S1 acceptance criterion (0141 / 0141E brief) | Status | Evidence |
|---|---|---|
| Every one of the 172 `prinet.__all__` symbols resolves from `prin` and passes a construct/callable smoke check (full parametrized matrix) | **MET** | `tests/test_api_surface_matrix.py` (172-symbol parametrized matrix, green); `verify_api_surface` returns `(set(), set())` |
| `verify_api_surface` regression test green against PRIN's RC1 `__all__` | **MET** | `tests/test_api_surface.py::test_frozen_surface_matches_prin_rc1_surface`; `FROZEN_PUBLIC_API` = `frozenset(RC1_PUBLIC_API)` (175 names) |
| Migration Guide table (all 172 rows) machine-checked against `wp001_api_traceability.md` by a committed test — no silent removals | **MET** | `DOCS/sphinx/migration_guide.rst` consolidated index (172 rows); `tools/wp036_migration_table.py check`; `tests/test_migration_guide_consolidated.py::test_no_silent_removals_against_wp001_baseline` |
| No Python numerics anywhere in the 0141A-0141E range (Coding Standards Sec. 2.1) — AST/grep check | **MET** | `tools/check_no_python_numerics.py` (13 compat modules, clean); `tests/test_no_python_numerics.py`; 0141B/0141C bindings delegate every op to `_prin_core` (per-pass parity dispositions) |
| Traceability matrix regenerated (`tools/wp001_*`); `tools/check_*` gates pass | **MET** | `wp001_baseline.py traceability` regenerated (no diff — matrix was current; checker regex fixed); `wp001_baseline.py check`, `check_deviation_ledger.py`, `check_dv_register_gates.py` all pass |
| The D-D per-symbol disposition appendix is complete and final (S2 veto) | **MET** | `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` — status **FINAL**, rows 1-45, S2 veto questions 1-5, owning-WP open item |
| S1 handoff note: every acceptance criterion -> evidence, plus the parity-evidence disposition for every new binding | **MET** | this document — per-sub-pass acceptance maps (0141A-0141E) + parity-evidence dispositions + this master map |
| >=95% coverage on new/changed code (each sub-pass) | **MET** | recorded per sub-pass; 0141E: new modules 100%, tools 96-100% |
| Full local gate (Rust + Python) reproduced for the whole range | **MET** | 0141E verification record above (Rust fmt/clippy/test/doc regression + full Python gate) |
| Sphinx `-W` build clean with the new Migration Guide table rendered | **MET** | `sphinx-build -W --keep-going` — build succeeded |
| No S1 self-certification of completion | **HELD** | S1 hands off to the mandatory S2 audit (session 0142); this note is evidence, not certification |

**Non-goals confirmed untouched:** the ~1,670-test acceptance-suite port
(WP-036B `0144A`-`0144D`, WP-036C `0144E`-`0144H`); behavioural parity beyond
smoke checks; final documentation prose (WP-037); release publishing; a CUDA
Burn backend (DV-005 stays a PSR scoping decision).

**Deferred / carried to S2 or a future WP:** the owning-WP decision for the
trainable-layer rebuild (D-D rows 31-44); the `DiscreteDeltaThetaGamma` PyO3
bridge; `retrain_controller`'s real implementation (WP-036C S1 / 0144E,
DV-025 unchanged).

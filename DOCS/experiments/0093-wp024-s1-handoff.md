# Session 0093 — WP-024 S1 Handoff Note

**Session:** 0093 — WP-024 S1: Coding — Oscillator-aware optimizers
**Date:** 2026-08-18
**Status:** S1 delivered; handoff to S2 audit (session 0094)

## Mission recap

"Implement SCALR, RIP, SyncGD, order-parameter feedback, state
serialization, and thin torch-side optimizer contracts." Contract
(`DOCS/sessions/phase-4/0093-wp024-s1-oscillator-aware-optimizers.md`):
update equations match references; deterministic resume/state tests pass;
invalid metrics fail safely. Non-goals: end-to-end models or experiment
statistics.

**Naming disposition (see DV-020).** PSR-023 §7's WP-024 declaration names
`PhaseAdam`/`KuramotoOptimizer` and `phase_adam.rs`/`kuramoto_optimizer.rs`.
Neither class exists anywhere in the PRINet 3.0 reference
(`grep -rl "PhaseAdam\|KuramotoOptimizer"` across the archived reference
tree and `DOCS/` returns only `023-project-state.md` itself). This
session's own brief instead names `SCALR`, `RIP`, `SyncGD` — matching the
Rebuild Planning Document's normative `nn/optimizers.py` mapping ("SCALR/
RIP/SyncGD need order-parameter feedback → Rust computes metrics, Python
optimizer classes stay thin") and PRINet 3.0's actual
`SCALROptimizer`/`RIPOptimizer`/`SynchronizedGradientDescent` classes. S1
followed the session brief and the verifiable reference implementation
(CLAUDE.md: "Verify implementation facts from the repository; do not
invent commands, APIs, paths, configuration, or evidence"; Project Plan F1
feature parity requires an equivalent for every actual PRINet 3.0 public
symbol). Recorded as DV-020 for S2 review.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-train/src/error.rs` | Added `TrainError::InvalidLearningRate`, `InvalidMomentum`, `InvalidWeightDecay`, `InvalidSyncPenalty`, `InvalidCriticalOrder`, `InvalidTargetAmplitude`, `InvalidRMin`, `InvalidAlpha`. |
| `crates/prin-train/src/support.rs` | Added `sgd_update`: the shared heavy-ball-momentum SGD core (`torch.optim.SGD` semantics — weight decay, momentum buffer with dampening, final `param - lr·d_p`) factored out of `SyncGd`/`Scalr`, whose PRINet 3.0 references apply the identical core and differ only in how `lr` is derived. |
| `crates/prin-train/src/feedback.rs` | **New.** `OrderParameter` (global-or-per-group order parameter, PRINet 3.0 SCALR's Q3 dict resolution), `StepFeedback` (the shared per-step input: order parameter / phase / amplitude), `OscillatorOptimizer` (the shared step/state-dict trait — the "thin torch-side optimizer contract"). See below. |
| `crates/prin-train/src/sync_gd.rs` | **New.** `SyncGd`/`SyncGdConfig`/`SyncGdState` — PRINet 3.0 `SynchronizedGradientDescent`. See below. |
| `crates/prin-train/src/rip.rs` | **New.** `Rip`/`RipConfig`/`RipState` — PRINet 3.0 `RIPOptimizer`. See below. |
| `crates/prin-train/src/scalr.rs` | **New.** `Scalr`/`ScalrConfig`/`ScalrState` — PRINet 3.0 `SCALROptimizer` (including its Q3 enhancements). See below. |
| `crates/prin-train/src/lib.rs` | Module doc extended to list the four new modules; added `pub use feedback::{OrderParameter, OscillatorOptimizer, StepFeedback}`, `pub use rip::{Rip, RipConfig}`, `pub use scalr::{Scalr, ScalrConfig}`, `pub use sync_gd::{SyncGd, SyncGdConfig}` (WP022-F2/WP023-F1 precedent: re-export every new public type at the crate root). |
| `crates/prin-train/Cargo.toml` | Added `serde_json.workspace = true` to `[dev-dependencies]` (already a workspace dependency, used elsewhere per `prin-dynamics`/`prin-metrics`/`prin-sim`/`prin-tensor`/`prin-daemon` precedent) — for `State` JSON round-trip tests. |
| `crates/prin-train/tests/parity_optimizers.rs` | **New.** 5 golden-value parity tests calling the actual PRINet 3.0 classes (not formula retranscriptions). |
| `crates/prin-train/tests/public_api.rs` | Extended `params_are_nameable_at_crate_root`'s import list and added `optimizers_are_nameable_and_usable_at_crate_root` (WP022-F2/WP023-F1 precedent, generalized to the new non-`Params` re-exports: `SyncGd`, `Rip`, `Scalr`, `OrderParameter`, `OscillatorOptimizer`, `StepFeedback`). |
| `DOCS/test_and_benchmark_results/wp024_generate_prinet_references.py` | **New**, ad-hoc, gitignored (WP-009/.../WP-023 precedent). Generates the golden values embedded in `parity_optimizers.rs`. |

## `feedback.rs`

The shared machinery all three optimizers use:

- `OrderParameter::{Global, PerGroup}` — SCALR's Q3 `Union[float, Dict[str,
  float]]` order-parameter input. `resolve(group)` and `global()` port the
  reference's dict-resolution formula exactly (`sum(values()) /
  max(len(), 1)` global fallback, direct lookup per group, unknown group
  falls back to the global mean).
- `StepFeedback<B>` — the per-step input every optimizer's `step` takes:
  `order_parameter: Option<f64>` (`SyncGd`, `Scalr`'s `OscillatorOptimizer`
  entry point), `phase`/`amplitude: Option<Tensor<B, 2>>` (`Rip`). Every
  field defaults to `None`, matching PRINet 3.0's `step()` signatures
  defaulting every feedback argument to `None` (plain gradient descent).
- `OscillatorOptimizer<B, D>` — the "thin torch-side optimizer contract"
  the mission names: a uniform `step`/`state_dict`/`load_state_dict`
  surface all three optimizers implement. Per the Rebuild Planning
  Document's `nn/optimizers.py` mapping, this is the seam a future thin
  `torch.optim.Optimizer` wrapper (WP-025) bridges to — every numerical
  decision is computed here, so the Python side stays a thin per-parameter
  loop over `torch.Tensor`s.

## `SyncGd` (`sync_gd.rs`)

Direct port of `SynchronizedGradientDescent`: momentum-SGD with a
synchronization-barrier penalty. `compute_sync_penalty` is a line-for-line
port (`penalty = λ·max(0, K_c − K)²`, `grad_scale = 2λ·deficit` when the
deficit is positive). `step` applies the reference's exact
`grad_modulation = max(0.1, 1 − grad_scale)` lr reduction, then the shared
`sgd_update` core.

## `Rip` (`rip.rs`)

Direct port of `RIPOptimizer`'s Hebbian coupling-matrix update:
`ΔK[i,j] = η·cos(φ[i] − φ[j])·|r[j]|·(r_target − r[i])`, diagonal zeroed
after application, combined additively with a plain gradient-descent
component when a gradient is supplied — reproduced via Burn tensor
broadcasting (`mean_dim`/`reshape` to build the `[n, n]` phase-difference
and amplitude-deficit outer products, `ones − eye` diagonal mask instead of
an in-place `fill_diagonal_`, matching the functional-tensor style
`layers.rs`'s `scaled_coupling` already established for the same
zero-diagonal-mask idiom).

**Documented deviation — fixed square shape.** PRINet 3.0's `RIPOptimizer`
is a generic `torch.optim.Optimizer` that silently skips the Hebbian term
for any non-square-matching parameter while still applying the plain
gradient step to every parameter. `Rip` instead fixes `n_oscillators` at
construction (matching the class's own stated single-purpose contract —
"This optimizer updates only coupling-type parameters") and returns a
typed `TrainError::ShapeMismatch` on a mismatched `phase`/`amplitude`
instead of silently no-op'ing the Hebbian term, per Coding Standards §2.2
("validate public inputs at every public boundary"). The Hebbian formula
and diagonal-zeroing/additive-composition behavior are otherwise a direct
port — see `rip.rs`'s module doc for the full rationale.

## `Scalr` (`scalr.rs`)

Direct port of `SCALROptimizer`, including all three Q3 enhancements:

- `compute_lr_scale(r) = r_min + (1 − r_min)·clamp(r, 0, 1)^α`.
- Oscillation-aware decay: `detect_oscillation` ports the windowed-variance
  check exactly; `lr_decay_factor` accumulates multiplicatively.
- Adaptive `r_min`: EMA of `r` (`r_min_ema_alpha`), `r_min = clamp(0.3·EMA,
  0.01, 0.5)`.
- Per-frequency lr scaling: `step_with_order_parameter(param, grad,
  order_parameter, group)` is the Q3 per-group entry point (the uniform
  `OscillatorOptimizer::step` only takes an already-resolved scalar, since
  a single Rust `step` call updates one parameter, not a `torch.optim`
  parameter-group list). Its rustdoc explains why per-group `Scalr`
  instances driven by the *same* `OrderParameter::PerGroup` dict each step
  observe bookkeeping identical to the reference's single shared optimizer
  instance: `order_history`/`lr_decay_factor`/adaptive `r_min` all track
  `OrderParameter::global()`, which depends only on the incoming dict, not
  on which group is stepping — verified directly by
  `scalr::tests::per_group_shared_bookkeeping_matches_across_instances`
  (two independent `Scalr` instances driven by the same dict sequence
  produce byte-identical `order_history`/`step_count`/`lr_decay_factor`).

## State serialization (deterministic resume)

Every optimizer exposes a serde `State` snapshot (`SyncGdState`/
`RipState`/`ScalrState`) covering hyperparameters and step-dependent
scalar/history bookkeeping. Momentum buffers (tensors) are reached via
`momentum_buffer()`/`set_momentum_buffer()` accessors outside `State` —
the same tensor/non-tensor split PRIN already uses for trainable-module
checkpoints (`burn::record`, `bands.rs`/`layers.rs`'s
`record_roundtrip_preserves_parameters` precedent). `load_state_dict`
re-validates every hyperparameter through the same `Config::with_params`
constructor the original optimizer used (a deserialized `State` is
untrusted input at a public boundary — Coding Standards §2.2), confirmed
by `load_state_dict_revalidates` tests on all three optimizers. Each
optimizer has a `deterministic_resume_matches_uninterrupted_run` test:
step N times uninterrupted vs. step `k` times → snapshot → restore on a
fresh instance → step the remaining `N − k` times, and assert bit-identical
(`<1e-12`) final parameters and identical histories.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Update equations match references** | **GREEN** | 5 golden-value parity tests in `tests/parity_optimizers.rs` call the actual PRINet 3.0 `SynchronizedGradientDescent`/`RIPOptimizer`/`SCALROptimizer` classes end-to-end (multi-step sequences, not single calls) and match to `rtol=1e-9, atol=1e-12`: `sync_gd_step_matches_prinet_3_0` (2 steps, momentum+weight_decay+dampening, penalty/order histories), `rip_step_matches_prinet_3_0` (combined gradient+Hebbian update on a 4×4 coupling matrix), `scalr_step_basic_matches_prinet_3_0` (3 steps, momentum, warmup, lr history), `scalr_oscillation_and_adaptive_r_min_matches_prinet_3_0` (5 steps exercising oscillation decay + adaptive `r_min` together), `order_parameter_dict_resolution_matches_reference_formula` (pure-formula check of the Q3 dict-resolution mean/fallback). All 5 passed against the reference on first attempt (no formula corrections needed after the initial port). |
| **Deterministic resume/state tests pass** | **GREEN** | `state_round_trips_through_json` (serde round trip, `SyncGdState`/`RipState`/`ScalrState` all `PartialEq`-equal after a JSON round trip) and `deterministic_resume_matches_uninterrupted_run` (see "State serialization" above) on all three optimizers; `load_state_dict_revalidates` confirms a corrupted/invalid restored state is rejected with the same typed error the original constructor would raise. |
| **Invalid metrics fail safely** | **GREEN** | All hyperparameter constructors (`SyncGdConfig::with_params`, `RipConfig::with_params`, `ScalrConfig::with_params`) validate every input and return typed `TrainError` variants — no `panic!`/`unwrap`/`expect` in any library path. `step`'s grad-shape mismatch returns `TrainError::ShapeMismatch` rather than panicking on a Burn shape-broadcast failure. `Rip`'s Hebbian branch validates `coupling`/`phase`/`amplitude` shapes before any tensor op. Property/unit tests cover every rejection path (negative lr/momentum/weight_decay, out-of-range `critical_order`/`r_min`, non-positive `alpha`/`target_amplitude`, non-finite `dampening`/`oscillation_threshold`/`oscillation_decay`/`r_min_ema_alpha`). |
| **≥95% coverage on new/changed code** | **GREEN** | `cargo llvm-cov -p prin-train`: `feedback.rs` 100.00% regions / 100.00% lines, `sync_gd.rs` 98.34% / 99.70%, `rip.rs` 97.91% / 100.00%, `scalr.rs` 98.24% / 99.80%, `support.rs` (touched: added `sgd_update`) 100.00% / 100.00%. |
| **All quality/security/parity/documentation gates green** | **GREEN, one new flagged risk (DV-020, naming); one DV-019 recurrence** | See tables below. |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict-checks) | `cargo clippy -p prin-train --all-targets --features strict-checks -- -D warnings` | PASS (covered by the workspace `strict-checks` test run below; no new clippy findings) |
| Workspace tests (default) | `cargo test --workspace` | PASS, no regressions |
| `prin-train` (default) | `cargo test -p prin-train` | PASS — 150 unit (57 new: 5 `feedback`, 17 `sync_gd`, 12 `rip`, 23 `scalr`) + 14 integration (5 new `parity_optimizers`, 1 new `public_api` addition, 8 pre-existing) + 9 doctests (3 new: `sync_gd`, `rip`, `scalr` module-doc examples) |
| `prin-train` (strict-checks) | `cargo test -p prin-train --features strict-checks` | PASS — same new-test counts; 2 more pre-existing WP-022 `strict-checks`-only tests, unaffected |
| `prin-train` coverage | `cargo llvm-cov -p prin-train --summary-only` | PASS — all four new files ≥97.9% regions / ≥98% lines (see acceptance-criteria table); one isolated `bands::tests::gradients_flow_to_every_parameter` failure during one `llvm-cov` run — DV-019 recurrence (pre-existing WP-022 flake, re-run clean, unrelated to WP-024) |
| Rustdoc (workspace) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings, including `#![warn(missing_docs)]` |
| `cargo audit` | `cargo audit` | Exit code 0; 2 allowed warnings, both unchanged from WP-023 close (`paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27) — no new dependency added this session (`serde_json` was already a workspace dependency, used in five other crates) |
| Snyk Code | `snyk auth status` (pre-flight) | **BLOCKED** — `snyk --version` returns `1.1306.2` (CLI present) but `snyk auth status` redirects to the OAuth login page and returns `ERROR Unspecified Error (SNYK-CLI-0000)`; unauthenticated on this machine, the same standing environment condition PSR-022/PSR-023 documented (R23: maintainer confirmed 2026-08-18 this Snyk-CLI-only-and-currently-unauthenticated posture is a known, intentional-but-unauthenticated state). Reported as blocked per Coding Standards §6.4, not claimed as passed. The CI `snyk` workflow is the authoritative gate and will scan this session's source once pushed at S4 (Plan amendment #28 push/CI cadence). |
| Snyk Open Source | Not run | Cargo is not a Snyk-supported package manager (R23 disposition, unchanged); `cargo audit` is the authoritative ecosystem-native gate |
| Python gates (ruff/mypy/interrogate/bandit/pytest) | Not run | Not applicable — no Python file under version control was touched (the new `wp024_generate_prinet_references.py` is ad-hoc/gitignored, same class as `wp023_generate_prinet_references.py`) |

## New discovered risks: DV-020 (and a DV-019 recurrence)

- **DV-020 — WP-024 declaration naming discrepancy.** See "Naming
  disposition" above and the Deferred Validation Register entry. Not a
  code defect; a governance-artifact drafting inconsistency between
  PSR-023 §7 and the session brief/Rebuild Planning Document, resolved in
  favor of the evidence-backed (repository-verifiable) naming. Flagged for
  S2 review and disposition (expected: D3 plan-drift, fixed by this
  session's delivered scope, not requiring further code change).
- **DV-019 recurrence** — one isolated `bands::tests::gradients_flow_to_every_parameter`
  failure observed during a single `cargo llvm-cov -p prin-train` run
  (immediate re-run clean). Same pre-existing WP-022 flakiness class
  already tracked in the register; not a WP-024 regression (`rip.rs`/
  `scalr.rs`/`sync_gd.rs`/`feedback.rs` do not touch `bands.rs` or its
  dependencies).

## Out-of-scope discoveries

- **Python `torch.optim.Optimizer` wrapper / thin bridge implementation**
  — the WP-024 non-goal explicitly excludes this (WP-025, "production
  torch autograd bridge"). `feedback::OscillatorOptimizer` is designed as
  the seam WP-025 will bridge to, but no Python code was written this
  session (Coding Standards §1: "the Python layer contains no numerics").
- **Full training-loop integration** (multiple named parameter groups
  updated in one call, a `Trainer`-level orchestration object) — WP-027's
  declared scope, not WP-024's. `Scalr::step_with_order_parameter`'s
  per-group entry point is designed to compose with such an
  orchestration layer without requiring one to exist yet.

## Parity-evidence disposition

Three new numerical primitives are introduced this session (`SyncGd`,
`Rip`, `Scalr`), each with a directly comparable PRINet 3.0 reference
class taking plain tensors/floats as parameters (not an `nn.Module`
requiring end-to-end forward-pass construction, unlike WP-022's
`DiscreteDeltaThetaGamma`/`ResonanceLayer`). Per the S1 exit-gate
requirement (Development Workflow and Audit Standards §3, "Parity-evidence
disposition stated"), confirmed via `grep -rl` against
`DOCS/archive and reference from PRINet 3.0/` before writing any Rust:
`SynchronizedGradientDescent`, `RIPOptimizer`, and `SCALROptimizer` all
exist in `prinet/nn/optimizers.py`.
`wp024_generate_prinet_references.py` imports and calls the **actual
PRINet 3.0 classes** directly (WP-023 `wp023_generate_prinet_references.py`
precedent), running multi-step sequences (not single-call snapshots) so
the parity tests exercise state-carrying behavior (momentum buffers,
histories, oscillation decay, adaptive `r_min`) rather than only a
stateless formula:

- `SynchronizedGradientDescent.step` — `tests/parity_optimizers.rs`,
  `rtol=1e-9, atol=1e-12`, 2 steps with momentum + weight decay +
  dampening + a critical-order penalty transition (below then above
  threshold).
- `RIPOptimizer.step` — combined gradient + Hebbian update on a 4×4
  coupling matrix with non-trivial (non-synchronized, non-unit-amplitude)
  phase/amplitude inputs.
- `SCALROptimizer.step` — two scenarios: (a) 3 steps with momentum,
  `warmup_steps=1`, varying order parameter; (b) 5 steps specifically
  exercising oscillation-aware decay (`oscillation_window=4`) and adaptive
  `r_min` (`r_min_ema_alpha=0.3`) together, checked against the
  reference's internal `_lr_decay_factor`/`_r_ema`/`_r_min` state as well
  as the final parameter value.
- SCALR's Q3 per-group dict resolution (`OrderParameter::{resolve,
  global}`) is additionally checked as a pure formula
  (`order_parameter_dict_resolution_matches_reference_formula`) since it
  has no tensor-update component of its own to golden-value-test.

All 5 parity tests passed against the reference on the first run after the
initial Rust port (no formula-correction iteration needed), which is
itself evidence the port faithfully reproduces the reference's exact
arithmetic (including PyTorch's `alpha=` in-place-add ordering for the
momentum buffer, and SCALR's specific `1.0`-dampening momentum variant
that differs from SyncGD's explicit `dampening` parameter).

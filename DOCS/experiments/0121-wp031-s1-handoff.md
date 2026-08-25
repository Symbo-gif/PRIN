# Session 0121 — WP-031 S1 Handoff Note

**Session:** 0121 — WP-031 S1: Coding — Temporal experiments, statistics, and
adversarial tooling
**Date:** 2026-08-25
**Status:** S1 delivered; handoff to S2 audit (session 0122)

## Mission recap

"Implement fair PT-vs-SA training framework, Hungarian similarity, temporal
metrics, bootstrap CIs, Welch tests, FLOPs, and FGSM/PGD orchestration."
Contract (`DOCS/sessions/phase-5/0121-wp031-s1-temporal-experiments-statistics-and-adversarial-tooling.md`):
statistical routines match trusted references; matched-budget controls are
enforced; attack bounds and deterministic multi-seed behavior are tested.
Non-goals: running the final scientific campaign.

## Entry conditions

| Condition | Status |
|---|---|
| Preceding S4 closed and committed | Yes — `209802d`…`b91dfdf` (WP-030 S1–S4) closed the cycle; `DOCS/reports/030-project-state.md` §6 declares WP-031 with the scope/acceptance criteria quoted above |
| WP-031 scope, acceptance criteria, and non-goals have maintainer approval | PSR-030 §6 recorded approval as *pending, required before WP-031 S1 begins*. **Obtained in-session** — executed at the direct instruction of the repository's maintainer (`MichaelMaillet`), the same in-session-approval precedent PSR-030 itself documents for WP-030/WP-029/WP-028 |
| No unresolved D1/D2 finding | Yes — PSR-030 §1: WP-030 S2 verdict `PASS`, zero findings; S3 no-change closure with a CLEAN delta re-audit |

## Scope decisions (record per "do not expand scope silently")

1. **Everything lives in `prin-train`, not a new crate.** All seven mission
   items are direct extensions of, or new siblings to, WP-027's
   `trainer.rs`/`dataset.rs`/`losses.rs` and WP-026's `phase_tracker.rs`/
   `slot_attention.rs` — all already in `prin-train`. Four new modules
   (`temporal_metrics`, `stats`, `flops`, `adversarial`) plus extensions to
   `trainer.rs` and `error.rs`. No new crate, no new external dependency.

2. **"Hungarian similarity" does not name a Hungarian-algorithm module to
   build.** Research against the archived PRINet 3.0 reference
   (`utils/temporal_training.py`, `nn/hybrid.py`, `nn/slot_attention.py`)
   confirmed the reference itself has no Hungarian/Kuhn–Munkres solver for
   slot/object matching — `PhaseTracker`/`TemporalSlotAttentionMOT` both use
   greedy argmax matching (`crate::support::greedy_match_by_similarity`,
   already ported at WP-026), and `hungarian_similarity_loss` (already
   ported at WP-027, `crate::losses`) is a cross-entropy loss named for the
   assignment behavior it *encourages*, not an implementation of the
   algorithm. The one real Hungarian solver in this codebase's lineage
   (`crates/prin-daemon/src/assignment.rs`, WP-030, for MOT identity
   assignment) is unrelated and already complete. This mission item
   therefore collapses into "already done" — recorded here so S2 does not
   need to re-derive the same research.

3. **Python bindings and `python/prin/eval`/`python/prin/experiments`
   orchestration are deferred, not delivered.** Same disposition WP-030 (the
   immediately preceding Phase-5 session) recorded for MOT evaluation
   (`028-wp028-audit.md`-adjacent precedent, and PSR-030 itself: no `prin-py`
   binding work was done for `hooks.rs`/`mot.rs` either). This WP's
   acceptance criteria ("statistical routines match trusted references",
   "matched-budget controls are enforced", "attack bounds and deterministic
   multi-seed behavior are tested") are all claims about Rust-level
   correctness, fully verifiable and verified via the Rust test suite below
   without any Python surface. Logged as out-of-scope discovery #1.

4. **FLOPs counting takes a caller-supplied `LayerSpec` description, not
   live `Module` introspection.** Burn has no generic reflection API
   equivalent to `model.named_modules()` + `isinstance` branching (see
   `flops.rs` module docs). `count_flops` reproduces the reference's three
   closed-form formulas exactly, including a **documented reference
   discrepancy**: `y4q1_tools.py`'s own docstring states the Conv2d formula
   as `2*C_in*C_out*K²*H_out*W_out`, but the actual implementation
   (`:538-546`) omits the `H_out*W_out` factor. This port reproduces the
   reference's *executed* behavior (what "match trusted references" means
   for a WP whose acceptance criterion is about matching the reference, not
   its docstring), not the docstring's stated intent — flagged explicitly in
   `flops.rs` rustdoc rather than silently "fixed."

5. **Two reference-side dead fields are omitted/documented, not
   fabricated.** (a) `TrainingSnapshot::slot_entropy` is declared in the
   reference's dataclass but `_capture_snapshot` never actually computes it
   for either tracker — this port keeps the field (API parity) but it is
   always `0.0`, documented as a reference gap. (b)
   `MultiSeedResult.mean_idsw`/`mean_tfr` are declared in the reference
   dataclass but `train_multi_seed`'s body never computes or assigns them —
   this port **omits** both fields entirely (Rust's stricter "declared implies
   populated" convention) rather than always reporting a fabricated `0.0`.
   Both are cited by exact reference line range in rustdoc.

6. **`adversarial_evaluate`/`adversarial_comparison` are specialized per
   tracker, not a generic closure-of-closures abstraction.** The reference's
   `adversarial_evaluate(model, ...)` duck-types `forward`/`track_sequence`
   across both PT and SA. Burn has no such duck typing, and
   `TemporalSlotAttentionMOT`'s methods additionally thread a `Seed` for
   per-call slot noise (a real signature difference, not just a naming one).
   `adversarial_evaluate_phase_tracker`/`adversarial_evaluate_temporal_slot_attention_mot`
   are separate, concrete functions — the same "concrete per-tracker
   functions" precedent `trainer.rs`'s `train_phase_tracker`/
   `train_temporal_slot_attention_mot` already establish for the identical
   reason.
   `adversarial_comparison` orchestrates both, matching the reference's
   side-by-side grid.

7. **`count_parameters`'s `complex_adjusted` always equals `total` in this
   port.** The reference doubles complex-valued parameter counts for fair
   PT-vs-SA comparison (PhaseTracker's *reference* Kuramoto coupling uses
   `torch.complex64`). PRIN's Burn `PhaseTracker` has no complex-tensor
   parameters at all — `phase_tracker.rs`'s module docs already document the
   real-valued reformulation of `phase_similarity` that makes this possible
   — so the field is retained (API parity, no breaking future signature
   change needed) but is a no-op in the current codebase. Documented on
   `ParameterCounts`.

8. **`train_phase_tracker`'s signature gained a `&mut Seed` parameter**
   (previously seedless, since `PhaseTracker::forward`/`evolve` have no
   stochastic component). `TrainingSnapshot::phase_coherence` needs a random
   probe phase (reference: unseeded `torch.rand`, relying on whatever the
   trainer's `torch.manual_seed` left the global RNG at); this project
   threads randomness explicitly (Project Plan §4 rule 3), so the probe draw
   goes through the caller's `Seed` via the already-existing
   `crate::support::seeded_uniform` helper rather than a new RNG authority.
   Updated all three existing callers (`crates/prin-py/src/bindings/trainer.rs`,
   two `prin-train` integration tests) — see "Scope delivered."

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-train/src/temporal_metrics.rs` | **New** (598 lines). `TemporalMetrics` + `temporal_smoothness`/`identity_switches`/`track_fragmentation_rate`/`identity_overcount`/`mostly_tracked_lost`/`track_duration_stats`/`recovery_speed`/`binding_robustness_score`/`compute_full_temporal_metrics` — direct port of `utils/temporal_metrics.py`'s 8 functions + dataclass. |
| `crates/prin-train/src/stats.rs` | **New** (601 lines). `bootstrap_ci`, `cohens_d`, `welch_t_test`, `compute_p_value`, plus a from-scratch regularized-incomplete-beta/log-gamma Student's-t p-value implementation (no external stats crate). |
| `crates/prin-train/src/flops.rs` | **New** (423 lines). `LayerSpec`/`count_flops`/`FlopsReport`, `measure_wall_time`/`WallTimeStats`. |
| `crates/prin-train/src/adversarial.rs` | **New** (829 lines). `fgsm_attack`, `pgd_attack`, `AttackKind`, `adversarial_evaluate_phase_tracker`, `adversarial_evaluate_temporal_slot_attention_mot`, `adversarial_comparison`. |
| `crates/prin-train/src/trainer.rs` | **Extended** (1391 lines, was 550). Added `TrainingSnapshot`, `ParameterCounts`/`count_parameters`, `compute_param_norm`/`compute_gradient_norm` (generic `ModuleVisitor`-based), `train_temporal_slot_attention_mot`/`evaluate_temporal_slot_attention_mot` (the SlotAttention-side fair-comparison trainer), `MultiSeedResult`/`train_multi_seed`; `TemporalTrainerConfig` gained `snapshot_epochs`; `TrainingResult` gained `wall_time_s`/`snapshots`; `ValMetrics` gained `idsw`/`tfr`; `train_phase_tracker` gained a `&mut Seed` parameter. |
| `crates/prin-train/src/error.rs` | Added `TrainError::InsufficientSamples`, `InvalidSignificanceLevel`, `InvalidBootstrapCount`, `InvalidPerturbationBudget`. |
| `crates/prin-train/src/lib.rs` | Wired the four new modules; updated crate-level docs. |
| `crates/prin-py/src/bindings/trainer.rs` | Updated for `train_phase_tracker`'s new `Seed` parameter and `TemporalTrainerConfig`'s new `snapshot_epochs` field (uses the reference default; no new Python-visible capability added — see out-of-scope discovery #1). |
| `crates/prin-train/tests/integration_checkpoint_resume.rs`, `tests/integration_temporal_clevr_n.rs` | Updated call sites for `train_phase_tracker`'s new `Seed` parameter. |
| `crates/prin-train/tests/parity_stats.rs` | **New.** Replays `tests/data/welch_t_test_reference_cases.json` (8 scenarios) through `welch_t_test` and asserts agreement with real `scipy.stats.ttest_ind`. |
| `crates/prin-train/tests/data/welch_t_test_reference_cases.json` | **New.** Golden fixture generated by `tools/wp031_stats_fixture.py`. |
| `tools/wp031_stats_fixture.py` | **New.** Generates the Welch's-t-test parity fixture via the real `scipy.stats.ttest_ind` (never the archived reference, per `tools/README.md`). |

## Parity-evidence disposition (Development Workflow Standards §3, S1 exit item)

Three different evidentiary classes apply across the seven mission items,
per what kind of reference each has:

### Statistics (`bootstrap_ci`/`cohens_d`/`welch_t_test`/`compute_p_value`) — real third-party reference, numerical parity

The reference itself calls `scipy.stats.ttest_ind`/`numpy` — a real,
independently-validated library, not archived PRINet code (`tools/README.md`
prohibits executing archived reference code; `motmetrics` was WP-030's
equivalent "real external reference"). `tools/wp031_stats_fixture.py` runs 8
engineered scenarios (identical groups, clearly separated groups, unequal
sample sizes, unequal variances, small overlapping groups, minimum-size
groups, near-zero-variance groups, negative values) through real
`scipy.stats.ttest_ind(equal_var=False)` and commits the inputs plus scipy's
own `statistic`/`pvalue` as `crates/prin-train/tests/data/welch_t_test_reference_cases.json`.
`tests/parity_stats.rs` replays the identical inputs through
`welch_t_test` and asserts agreement at `rtol=1e-9, atol=1e-12` — the same
tolerance class WP-030 used for its own real-library parity check, since
both sides compute the same closed-form Welch statistic and (this port's
own regularized-incomplete-beta implementation vs. scipy's `stdtr` C
implementation) the same Student's-t survival function:

```
$ .venv/Scripts/python -c "import scipy; print(scipy.__version__)"
1.18.0
$ cargo test -p prin-train --test parity_stats
running 1 test
test welch_t_test_matches_scipy_stats_ttest_ind ... ok
test result: ok. 1 passed; 0 failed
```

`bootstrap_ci`'s percentile-method *formula* is pinned by hand-computed
tests (`percentile_hand_computed_linear_interpolation`,
`bootstrap_ci_constant_values_gives_zero_width`); its resample *stream*
draws from this project's `Seed` rather than `numpy.random.RandomState` —
the same "structural, not bit-parity" port class `dataset.rs` already
established for `generate_temporal_clevr_n` (RNG-stream parity is
architecturally out of scope; formula parity is not).

### Temporal metrics / adversarial tooling / fair-training framework — archived-only reference, formula-transcription parity

`temporal_metrics.py`, `adversarial_tools.py`, and `temporal_training.py`
are PRINet 3.0's own bespoke code with no independent third-party backing
(unlike `scipy`/`motmetrics`) — `tools/README.md` forbids executing archived
reference code directly, so no live-comparison fixture is possible for
these three. Parity evidence is instead **formula transcription**: every
function's rustdoc cites the exact reference line range, and every
function's test suite includes at least one hand-computed value traced
through the reference's own algorithm by hand (e.g.
`temporal_metrics::tests::recovery_speed_hand_computed_immediate_rebind`
required tracing the reference's `for t2 in range(t-1, ...)` loop by hand
twice — the first hand-derivation was wrong by exactly one iteration, caught
by the test itself; see "Design notes"). This is the same evidentiary class
already established for `dataset.rs`'s elastic-bounce/velocity-reversal
formulas (WP-027).

### FLOPs counting — archived-only reference, with a documented reference bug

Same evidentiary class as above, plus the documented Conv2d
docstring-vs-implementation discrepancy (scope decision #4) — the "trusted
reference" being matched is the reference's *executed* formula, verified by
`conv2d_flops_omits_output_spatial_size_matching_reference_behavior`.

## Design notes worth an auditor's attention

### `recovery_speed`'s off-by-one: caught by the test suite, not assumed away

The reference's inner scan (`for t2 in range(t-1, ...)`) starts at the
*occluded* frame's own match entry (still `-1`), not the first visible
frame — so "frames to rebind" is one larger than intuition suggests. Both
`temporal_metrics::tests::recovery_speed_hand_computed_immediate_rebind`
and `..._delayed_rebind` were initially written with the intuitive (wrong)
expected value, caught immediately by `cargo test` (the implementation,
transcribed directly from the reference's loop bounds, was correct; the
tests' hand-derived expectations were not). Corrected with an inline
rustdoc comment on both tests explaining the off-by-one so a future reader
does not "fix" the implementation to match the wrong intuition. See also
`fgsm_attack_actually_perturbs_when_gradient_exists`: an all-identical-rows
detection tensor produces a perfectly symmetric similarity matrix, making
`hungarian_similarity_loss`'s gradient w.r.t. the input a genuine
zero-by-symmetry stationary point — not a bug, but the test needed
distinct-per-row detections (`varied_dets`) to observe a nonzero attack
perturbation.

### FGSM/PGD reuse `hungarian_similarity_loss` directly, not a duplicated cross-entropy

The reference's `fgsm_attack`/`pgd_attack` build
`cross_entropy(sim_block/0.1, arange(N))` inline
(`adversarial_tools.py:56-59,121-123`) — definitionally identical to
`hungarian_similarity_loss(sim_block, N)`'s own formula
(`losses.rs`, already ported at WP-027). This port calls it directly
(Coding Standards §1.1, "one algorithm, one implementation") rather than
re-deriving the cross-entropy-with-diagonal-target computation a second
time.

### Attack primitives combine autodiff-graph and gradient tensors via a host round-trip, by design

Burn's `Tensor::grad(&grads)` returns a tensor on the *inner*
(non-autodiff) backend (`B::InnerBackend`), while the caller-supplied
`dets_t` and the accumulated PGD perturbation live on the outer autodiff
backend `B` — two different Rust types. Rather than plumb backend
conversion machinery through, `fgsm_attack`/`pgd_attack` read both to the
host as `f64` (`crate::support::to_f64_vec`, the established
"host-side non-differentiable bookkeeping" idiom this crate already uses
for greedy matching) and reconstruct the perturbed tensor from host data
each step. Detection tensors are small (`N` objects × `detection_dim`
features), so this is not a performance concern; only the sign/clamp
arithmetic — never the gradient computation itself — happens off-device.
Also fixed a subtle semantic gap: Rust's `f64::signum()` returns `1.0` for
exactly `0.0` (Rust convention), while PyTorch's `torch.sign()` (used by
`.grad.sign()` in the reference) returns `0.0` — `adversarial::torch_sign`
matches the reference exactly, tested by
`torch_sign_matches_pytorch_zero_convention`.

### `count_parameters`/`compute_param_norm`/`compute_gradient_norm` are generic over any `Module`, not per-tracker duplicates

Burn's `Module::visit`/`ModuleVisitor` trait (used internally by Burn's own
`num_params()`) gives a backend-generic way to walk every parameter tensor
in a module tree regardless of its concrete shape. `count_parameters`/
`compute_param_norm`/`compute_gradient_norm` are single implementations
that work identically for `PhaseTracker<B>` and `TemporalSlotAttentionMOT<B>`
(and any future `Module`), verified by
`count_parameters_matches_between_pt_and_sa_shapes`. `compute_gradient_norm`
additionally cross-references a `GradientsParams` map by `ParamId`
(`grads.get::<B::InnerBackend, D>(id)`), computed *before* `optimizer.step`
consumes the gradients (Burn's optimizer step takes `GradientsParams` by
value).

## Acceptance-criterion evidence map

### AC1 — "Statistical routines match trusted references"

See "Parity-evidence disposition" → Statistics section above. `cargo test
-p prin-train --test parity_stats`: 1/1 passed (8/8 scenarios agree with
real `scipy.stats.ttest_ind` 1.18.0 at `rtol=1e-9, atol=1e-12`). `cohens_d`
is closed-form and hand-verified
(`cohens_d_hand_computed_value`: pooled-SD formula on `[1,2,3]` vs.
`[4,5,6]` gives exactly `-3.0`).

### AC2 — "Matched-budget controls are enforced"

`count_parameters` (complex-aware — see scope decision #7) is the
mission's named "matched-budget control," used identically by both
trackers (`count_parameters_matches_between_pt_and_sa_shapes`,
`count_parameters_totals_are_consistent`: `total == trainable + frozen`
for every module). `TemporalTrainerConfig`'s identical
loss/optimizer/schedule/gradient-clipping applies to both
`train_phase_tracker` and `train_temporal_slot_attention_mot` — the "fair
PT-vs-SA training framework" itself is the budget-matching mechanism (same
`Adam` config, same warmup/cosine LR schedule, same early-stopping
smoothing window, same `Hungarian` similarity loss +
`temporal_smoothness_loss` regularizer, differing only in which tracker's
`process_frame`/`forward` builds the similarity matrix) —
`phase_tracker_training_runs_and_produces_valid_metrics` and
`slot_attention_training_runs_and_produces_valid_metrics` exercise both
end-to-end under the identical `TemporalTrainerConfig`.

### AC3 — "Attack bounds and deterministic multi-seed behavior are tested"

**Bounds:** `fgsm_attack_perturbation_is_within_epsilon_ball` and
`pgd_attack_perturbation_is_within_epsilon_ball` assert every perturbed
feature stays within `epsilon` of its original value (L-infinity ball, the
reference's own bound); `pgd_attack_default_alpha_is_epsilon_over_four`
confirms the reference's `alpha = epsilon/4` default step size is actually
respected in a single un-random-started step.
`fgsm_attack_rejects_invalid_epsilon`/`pgd_attack_rejects_zero_steps`/
`pgd_attack_rejects_invalid_alpha` cover the typed-error input-validation
boundary (Coding Standards "validate public inputs").

**Deterministic multi-seed:** `pgd_attack_is_deterministic_for_same_seed`
(identical `Seed` state → byte-identical perturbation) and
`pgd_attack_different_seeds_give_different_perturbations` (the random-start
component actually depends on the seed) at the primitive level;
`adversarial_evaluate_phase_tracker_pgd_is_deterministic_for_same_seed` at
the dataset-evaluation level. `train_multi_seed_aggregates_across_seeds`
and `train_multi_seed_single_seed_has_zero_std` cover the *training-side*
multi-seed statistical-reliability mechanism (mean/std IP aggregation
across independent seeded runs, `train_multi_seed_propagates_errors`
confirms a single bad config fails the whole sweep rather than silently
skipping a seed).

## Gate evidence (2026-08-25, this host)

```
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # clean (exit 0)
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # clean (exit 0)
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps                    # 0 warnings (exit 0)
cargo test --workspace -- --test-threads=4                                    # all 48 test binaries green, 0 failed
cargo test -p prin-train --lib -- --test-threads=4                            # 375 passed, 0 failed
cargo test -p prin-train --test parity_stats                                  # 1 passed (8/8 scenarios vs. real scipy)
cargo audit                                                                    # exit 0; 2 allowed warnings (amendments #9/#27 — unchanged, no new deps)
.venv\Scripts\ruff check tools/wp031_stats_fixture.py                         # clean
.venv\Scripts\ruff format --check tools/wp031_stats_fixture.py                # clean
.venv\Scripts\mypy tools/wp031_stats_fixture.py --strict                      # 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp031_stats_fixture.py  # 100.0% (4/4)
.venv\Scripts\python -m bandit tools/wp031_stats_fixture.py -c pyproject.toml # 0 issues
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities (no new Python deps; scipy already a base dependency)
python tools/wp031_stats_fixture.py                                           # regenerates the committed fixture byte-identically
cargo llvm-cov -p prin-train --features strict-checks                         # see Coverage below
```

### Coverage on new/changed code (`cargo llvm-cov -p prin-train --features strict-checks`)

| File | Regions | Functions | Lines |
|---|---|---|---|
| `crates/prin-train/src/temporal_metrics.rs` | 98.30% | 97.50% | **95.04%** |
| `crates/prin-train/src/stats.rs` | 96.38% | 100.00% | **96.77%** |
| `crates/prin-train/src/flops.rs` | 99.15% | 100.00% | **96.53%** |
| `crates/prin-train/src/adversarial.rs` | 96.78% | 94.00% | **96.03%** |
| `crates/prin-train/src/trainer.rs` | 98.00% | 100.00% | **98.04%** |

All five clear the ≥95% bar. Remaining gaps are the same class already
established across this crate's other modules: unreachable
early-validation-error branches inside deliberately-`unreachable!()` test
closures (`pgd_attack_rejects_zero_steps`/`..._invalid_alpha`), the
`mean(&[])` empty-slice defensive branch in
`adversarial::build_adversarial_eval_result` (never hit because every test
dataset is non-empty by construction — defensive against a future caller
passing an empty dataset, not dead product logic), and
`TemporalMetrics::default()`'s field-literal lines (never called directly
since every test constructs the struct via `compute_full_temporal_metrics`
or explicit literals instead of `Default::default()`).

### Snyk (Coding Standards §6, mandatory control)

Not run this session — no interactive Snyk CLI/MCP session available in
this non-interactive execution environment. Per Coding Standards §6.1 item
5 and the standing condition on record since WP-001 (R23), this is reported
as **blocked**, not claimed as passed; CI's Snyk job remains the
authoritative gate. `cargo audit`/`pip_audit` (ecosystem-native, independent
of Snyk) are both clean, as recorded above. This session added no new
first-party attack surface beyond pure numerical/host computation (no
network, filesystem beyond the one committed fixture, or subprocess code).

## Out-of-scope discoveries (logged, not acted on)

1. **`prin-py` bindings and `python/prin/eval`/`python/prin/experiments`
   population.** Both package stubs' docstrings already name this WP's
   deliverables (`prin.eval` → `temporal_metrics.py`; `prin.experiments.stats`/
   `.adversarial` → this session's `stats.rs`/`adversarial.rs`; the fair
   training framework → this session's `train_temporal_slot_attention_mot`)
   but remain `__all__: list[str] = []` after this session — see scope
   decision #3. Concrete recommendation for whichever session picks this
   up: bind `count_parameters`/`train_multi_seed`/`welch_t_test`/
   `bootstrap_ci`/`count_flops`/`fgsm_attack`/`pgd_attack` via PyO3
   (following `bindings/trainer.rs`'s existing pattern), then populate
   `python/prin/eval`/`python/prin/experiments` as thin orchestration
   wrappers per Project Plan §4 rule 2.
2. **`Conv2d`/`GruCell` `LayerSpec` variants have no exercising PRIN model.**
   No PRIN model (PhaseTracker, SlotAttention, HybridPRINetV2) uses
   `Conv2d`; `GruCell`'s declarative params formula is exercised by unit
   tests only, not by wiring an actual `PhaseTracker`/`TemporalSlotAttentionMOT`
   layer inventory through `count_flops`. A future WP wanting real FLOPs
   reports for a trained model would need a `layer_specs()` accessor on
   each `Module` (analogous to `count_parameters`'s generic visitor, but
   FLOPs needs shape *kind* — Linear vs. GRU — which `ModuleVisitor` cannot
   see) — not attempted here to avoid expanding this WP's already-large
   scope into every trainable module's internals.
3. **`benchmarks/` has no category package for temporal-experiment/
   adversarial/statistics benchmarking.** Same disposition as WP-029/WP-030's
   identical discoveries: `benchrunner` itself is Phase 6 scope.

## Handoff to S2 (session 0122)

Suggested audit focus, in descending order of risk:

1. **The Student's-t p-value implementation** (`stats.rs`'s
   `log_gamma`/`betacf`/`regularized_incomplete_beta`) — a from-scratch
   numerical algorithm with no external stats-crate backing. The parity
   fixture (8 scenarios vs. real scipy) is solid evidence but is not
   exhaustive; consider whether additional adversarial cases (very large
   `df`, `df` near 1, extreme `t_stat`) are warranted before closing this
   item, and independently re-derive the Lanczos-approximation coefficients
   against a textbook source rather than trusting this session's
   transcription.
2. **`recovery_speed`'s off-by-one semantics** (Design notes above) — this
   is genuinely counter-intuitive (the reference itself, not just this
   port). Confirm the transcription against the archived
   `temporal_metrics.py` source directly, not against this note's
   explanation of it.
3. **Whether `train_phase_tracker`'s signature change (`&mut Seed` added)
   was the right call** vs. an alternative (e.g. a fixed/no-op probe phase
   that avoids touching the existing public API) — judge whether the
   three-callsite blast radius (documented in scope decision #8) was
   proportionate to what `phase_coherence` actually buys as a training
   diagnostic.
4. **The Conv2d FLOPs discrepancy disposition** (scope decision #4) — judge
   whether reproducing the reference's docstring-inconsistent behavior
   (rather than fixing it, or flagging both) is the right call given no
   PRIN model currently exercises `Conv2d`. If a future WP validates FLOPs
   against a real trained model's profiler output, this decision may need
   revisiting.
5. **`adversarial_evaluate_temporal_slot_attention_mot`'s per-call `Seed`
   derivation scheme** (`Seed::new(seed as u128 + i as u128 * 100_000 + t
   as u128 + 1, 1)` and similar formulas) — confirm these offset constants
   cannot collide across `(sequence index, frame index)` pairs in a way
   that would silently correlate supposedly-independent draws, for the
   dataset sizes this WP's tests actually exercise and for larger ones a
   future campaign might use.

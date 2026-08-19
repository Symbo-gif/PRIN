# Session 0101 — WP-026 S1 Handoff Note

**Session:** 0101 — WP-026 S1: Coding — PhaseTracker, Hybrid, baselines, and allocation
**Date:** 2026-08-19
**Status:** S1 delivered; handoff to S2 audit (session 0102)

## Mission recap

"Port PhaseTracker, HybridPRINetV2, SlotAttention comparison baseline,
ablation variants, and adaptive oscillator allocation." Contract
(`DOCS/sessions/phase-4/0101-wp026-s1-phasetracker-hybrid-baselines-and-allocation.md`):
public APIs and checkpoints are compatible; unit/integration/gradient tests
cover all variants; baseline fairness contracts are explicit. Non-goal:
confirmatory temporal CLEVR conclusions.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-train/src/error.rs` | Added `TrainError::IndivisibleHeads`, `InvalidDropout`, `InvalidRatio`, `InvalidAllocatorRange`, `InvalidMatchThreshold`. |
| `crates/prin-train/src/support.rs` | Added `seeded_linear`/`seeded_gru` (build `burn::nn::Linear`/`Gru` from this crate's `Seed`, not `Config::init`'s backend-global RNG — see "Discovered hazard" below), `seeded_standard_normal` (Box–Muller, for `SlotAttentionModule`'s per-call noise), `python_round` (round-half-to-even), `phase_coherence_similarity` (shared by `PhaseTracker`/`PhaseTrackerStatic`), `to_f64_vec`/`to_i64_vec` (backend-generic host readback), `greedy_match_by_similarity` (shared frame-to-frame assignment). |
| `crates/prin-train/src/attention.rs` | **New.** `OscillatoryAttention`/`OscillatoryAttentionConfig`/`OscillatoryAttentionParams` — multi-head attention with an additive oscillatory coherence bias (PRINet 3.0 `nn.layers.OscillatoryAttention`). |
| `crates/prin-train/src/phase_tracker.rs` | **New.** `PhaseTracker`/`PhaseTrackerConfig`/`TrackingResult` — PRIN's primary contribution (PRINet 3.0 `nn.hybrid.PhaseTracker`). |
| `crates/prin-train/src/hybrid.rs` | **New.** `HybridPRINetV2`/`HybridPRINetV2Config` — the canonical hybrid classification architecture (PRINet 3.0 `nn.hybrid.HybridPRINetV2`). |
| `crates/prin-train/src/slot_attention.rs` | **New.** `SlotAttentionModule`/`SlotAttentionModuleConfig`, `TemporalSlotAttentionMOT`/`TemporalSlotAttentionMOTConfig`, `cosine_similarity` — the non-oscillatory comparison baseline (PRINet 3.0 `nn.slot_attention`). |
| `crates/prin-train/src/ablation.rs` | **New.** `PhaseTrackerFrozen`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`, `SlotAttentionFrozen` — structural ablation variants (PRINet 3.0 `nn.ablation_variants`). |
| `crates/prin-train/src/allocation.rs` | **New.** `OscillatorBudget`, `estimate_complexity`, `AdaptiveOscillatorAllocator`/`AdaptiveOscillatorAllocatorConfig`, `AllocatorStrategy`, `DynamicPhaseTracker` — adaptive oscillator-count allocation (PRINet 3.0 `nn.adaptive_allocation`). |
| `crates/prin-train/src/bands.rs` | Added `#[cfg(test)] pub(crate) fn w_delta_requires_grad` — crate-internal introspection for `PhaseTrackerFrozen`'s freeze regression test. No behavior change. |
| `crates/prin-train/src/lib.rs` | Module doc extended with all six new modules; `pub use attention::OscillatoryAttentionParams` (WP022-F2/WP023-F1 re-export precedent); corrected the stale "not yet implemented: WP-025 bridge" note (WP-025 delivered it). |
| `crates/prin-train/tests/parity_attention.rs` | **New.** Golden-value parity test: `OscillatoryAttention.forward`, explicit extracted PyTorch weights (dropout=0, external phase). |
| `crates/prin-train/tests/parity_phase_tracker.rs` | **New.** Golden-value parity test: `PhaseTracker.phase_similarity`, called on the actual reference class. |
| `crates/prin-train/tests/public_api.rs` | Extended with `OscillatoryAttentionParams` (WP022-F2/WP023-F1 precedent). |
| `crates/prin-train/README.md`, `crates/README.md` | WP-026 sections added; PyO3/Python carried-scope decision documented (see below). |
| `DOCS/test_and_benchmark_results/wp026_generate_prinet_references.py` | **New**, ad-hoc, gitignored (WP-009/.../WP-025 precedent). Generates the golden values embedded in `parity_attention.rs`/`parity_phase_tracker.rs` by calling the actual PRINet 3.0 classes. |

## Discovered hazard: `Backend::seed` is a shared global, unsafe under parallel tests

While gradchecking `OscillatoryAttention`, a gradient-vs-finite-difference
test that seeded weights via `burn::nn::LinearConfig::init` (which draws
from `Backend::seed`) produced wildly divergent results (~1.4×10⁶ vs. an
expected O(1) analytic/numerical gradient agreement) — not from a formula
bug, but because `burn_ndarray::backend`'s `seed()` writes to a **process-wide
`static Mutex`**, shared by every `NdArray`-backend tensor operation in the
test binary. `cargo test` runs `#[test]` functions in parallel threads by
default, so two tests (or two calls within one test, racing against other
concurrently-running tests) calling `B::seed(...)` can observe each other's
draws, breaking reproducibility — a "hidden global" in the exact sense
Coding Standards §1.3 prohibits, despite the input `Seed` value itself being
fully deterministic. Fixed by adding `support::seeded_linear`/`seeded_gru`,
which construct `burn::nn::Linear`/`Gru` directly from their public
`weight`/`bias`/gate fields, drawing every value from this crate's own
`Seed` (no `Backend::seed` call anywhere in `prin-train`). Used by every new
module that needs standard transformer/GRU plumbing
(`attention`/`hybrid`/`slot_attention`/`ablation`). Not filed as a DV item —
fully fixed within this session, not a residual gap.

## Correspondence notes (see each module's own rustdoc for full detail)

- **`OscillatoryAttention`** — line-for-line port of the additive
  phase-coherence-bias formula; masked-attention support (no exercising
  caller in this WP) not ported.
- **`PhaseTracker`** — `phase_similarity` is a real-valued reformulation of
  the reference's `torch.complex64`-based cosine similarity (Burn has no
  complex-tensor autodiff, same constraint `energy`/`hep` already document);
  the ε-regularized normalization is preserved exactly (not simplified to
  `1/n_osc`), verified bit-for-bit by `parity_phase_tracker.rs`. Greedy
  frame-to-frame matching is host-side, non-differentiable index bookkeeping
  (`support::greedy_match_by_similarity`), matching the reference's own
  `.item()`-per-element Python loop.
- **`HybridPRINetV2`** — composes `bands::DiscreteDeltaThetaGamma` (already
  parity-tested at WP-022) and `attention::OscillatoryAttention` (newly
  parity-tested this session); `use_conv_stem`'s image-input CNN stem is not
  ported (separate input modality, no caller in this WP's oscillatory-binding
  scope).
- **`SlotAttentionModule`** — the only `forward` in this crate that is
  genuinely stochastic *per call* (slot-initialization noise), so it takes
  `&mut Seed` directly rather than following every other module's
  construct-time-only randomness pattern; documented as a deliberate
  signature deviation, not an oversight. `SlotAttentionCLEVRN` (CLEVR-N
  classification, not tracking comparison) is out of scope per this WP's
  non-goals.
- **Ablation variants** — `PhaseTrackerFrozen` wraps `PhaseTracker` and
  freezes only its `dynamics` submodule (`Module::no_grad`); `PhaseTrackerStatic`
  fully reimplements (does not wrap) `PhaseTracker`, matching the
  reference's own structure, with fixed non-learnable frequencies stored as
  a non-`require_grad` `Param` (not a raw `Tensor` field, which would
  silently discard its value on `into_record`/`load_record` —
  `ConstantRecord` serializes to nothing). `create_ablation_tracker`'s
  string-keyed factory is not ported: the six variants' `forward` signatures
  genuinely differ in Rust (e.g. `PhaseTracker::forward` takes no `Seed`,
  `SlotAttentionModule::forward` must), so callers construct the specific
  type directly.
- **`AdaptiveOscillatorAllocator`** — the rule-based formula reproduces
  Python's round-half-to-even (`support::python_round`), not Rust's
  round-half-away-from-zero. `DynamicPhaseTracker` faithfully reproduces a
  real PRINet 3.0 quirk: its `forward` never passes `features` to
  `allocate`, so it always uses rule-based allocation even when configured
  `Learned` — preserved, not silently "fixed". `DynamicPhaseTracker` is
  deliberately not a `Module` (its whole purpose is to lazily cache a
  *different* `PhaseTracker` per budget, which has no fixed parameter set
  for `Module`'s checkpoint contract to describe); each cached `PhaseTracker`
  remains individually a full, checkpointable `Module`.

## Not delivered this session — PyO3 bindings and Python wrappers

`crates/prin-py/` PyO3 bindings and `python/prin/nn/` thin wrappers were
declared in WP-026's scope (`DOCS/reports/025-project-state.md` §6:
"`crates/prin-py/` (PyO3 bindings for new symbols); `python/prin/nn/` (thin
`torch.nn.Module` wrappers where applicable)") but are **not implemented in
this S1**. Recorded here explicitly, not silently dropped:

WP-025's own production `torch.autograd.Function` bridge for two materially
simpler modules (`ResonanceLayer`, `GatedPhaseActivation` — each a single
flat parameter set with no sub-modules) required ~514 lines of custom Rust
bridge code (`crates/prin-py/src/bindings/train.rs`), a hand-written
backward pass working around Burn's lack of a retain-graph equivalent
(recomputing the forward pass inside every `backward()` call), and 27
dedicated Python tests — and was itself a full four-session work package
(S1 session 0097 through S4 session 0100). This session ports **five**
architecturally larger modules: multi-sub-module compositions
(`HybridPRINetV2` alone composes `DiscreteDeltaThetaGamma` +
`OscillatoryAttention` + FFN/LayerNorm/classifier stacks), a
non-differentiable greedy-matching post-processing step present in every
tracker variant, and a genuinely per-forward-call stochastic entry point
(`SlotAttentionModule`). Replicating WP-025's bridge depth for all five in
one S1 session budget is out of proportion and risks exactly the kind of
under-tested bridge code WP-025's own S2 audit found and had to remediate
(WP025-F1: checkpoint shape validation gap; WP025-F2: unverified performance
claim). This is a deliberate scope decision — the Rust numerical core (the
authoritative source of truth per Coding Standards §1.2, "the Python layer
contains no numerics") is delivered complete, correct, and fully tested;
the Python-facing bridge is carried forward as an explicit, evidence-backed
item for the mandatory S2 audit to evaluate and for S3 or a future WP to
schedule — the same disposition class as DV-005 (CUDA DLPack path,
concretely checkpointed to WP-027 S1 rather than left an unassigned "future
WP").

## Out-of-scope discoveries

- **`use_conv_stem` image-input CNN stem** (`HybridPRINetV2`) — separate
  input modality (CIFAR-10/Fashion-MNIST benchmarks), no caller in this
  WP's oscillatory-binding/CLEVR-N/MOT scope.
- **`OscillatoryAttention` masked-attention support** — no exercising
  caller in this WP.
- **`SlotAttentionCLEVRN`** — CLEVR-N scene+query classification adapter;
  this WP's "SlotAttention comparison baseline" mission text refers to
  head-to-head tracking comparison (`TemporalSlotAttentionMOT`'s own
  documented purpose), not CLEVR-N classification, which the WP's own
  non-goals exclude ("confirmatory temporal CLEVR conclusions").
- **`create_ablation_tracker` string-keyed factory** — no direct Rust
  equivalent; see "Correspondence notes" above.
- **PyO3 bindings / Python wrappers** — see dedicated section above.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Public APIs and checkpoints are compatible** | **GREEN for the Rust surface; PyO3/Python surface deferred (see above)** | Every new `Module` (`OscillatoryAttention`, `PhaseTracker`, `HybridPRINetV2`, `SlotAttentionModule`, `TemporalSlotAttentionMOT`, `PhaseTrackerFrozen`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`, `SlotAttentionFrozen`, `AdaptiveOscillatorAllocator`) has a `record_roundtrip_preserves_parameters`-class serialization test (or, for the frozen/static/no-GRU ablation variants, exercises the same underlying checkpoint machinery via their wrapped/reimplemented modules). Public symbol names/signatures mirror the PRINet 3.0 reference 1:1 except the four documented, justified deviations (module docs + this note's "Correspondence notes"). |
| **Unit/integration/gradient tests cover all variants** | **GREEN** | 76 new unit tests across the six new modules + 1 new `support::python_round` unit test + 2 new golden-value parity tests + 4 new module-doc doctests (see "Test counts" below). Every new `Module` has a `gradients_flow_to_*`-class test (or, for the deliberately-frozen ablation variants, a `*_does_not_require_grad` test proving the freeze actually took effect); `OscillatoryAttention` additionally has a `gradient_matches_central_finite_difference`-class analytic-vs-numerical gradcheck (matching the crate's established `layers.rs`/`bands.rs` precedent). |
| **Baseline fairness contracts are explicit** | **GREEN** | `TemporalSlotAttentionMOT` shares `PhaseTracker`'s exact greedy-matching contract (`support::greedy_match_by_similarity`) and detection-encoder shape convention, so head-to-head comparison is apples-to-apples at the assignment-algorithm level; both trackers' `forward`/`track_sequence` return shapes are documented as intentionally mirroring each other. `PhaseTrackerFrozen`/`SlotAttentionFrozen` are explicitly paired as "the untrained baseline for [the other]" in both the reference and this port's module docs — verified by `*_does_not_require_grad` tests confirming both are genuinely frozen, not merely documented as such. |
| **≥95% coverage on new/changed code** | **GREEN** | `cargo llvm-cov -p prin-train --summary-only`: `attention.rs` 97.81%/100.00%/99.66% (region/function/line), `phase_tracker.rs` 97.96%/100.00%/99.50%, `hybrid.rs` 98.70%/100.00%/98.38%, `slot_attention.rs` 98.68%/100.00%/99.79%, `ablation.rs` 98.50%/100.00%/99.77%, `allocation.rs` 98.18%/96.88%/96.67%, `support.rs` (touched) 99.05%/100.00%/99.54%, `bands.rs` (touched, test-only accessor) 98.11%/100.00%/99.25%. All eight files clear 95% on every one of the three metrics. |
| **Every quality/security/parity gate green** | **GREEN, one discovered-and-fixed hazard, PyO3 gap noted** | See tables below. |

## Test counts

`cargo test -p prin-train`: **260** total (was 177 at WP-025 close per
PSR-025) — **231** unit (`--lib`; was 154+ new-since — see below), **14**
parity integration tests across 7 files (`parity_activations` 2,
`parity_attention` 1 **new**, `parity_bands` 1, `parity_energy` 2,
`parity_inhibition` 1, `parity_layers` 1, `parity_optimizers` 5,
`parity_phase_tracker` 1 **new**; was 12), **2** `public_api` (extended, not
new count), **13** doctests (was 9; **4 new**: `attention`, `allocation`,
`phase_tracker`, `hybrid` module-doc examples). New unit tests by file:
`attention.rs` 11, `phase_tracker.rs` 16, `hybrid.rs` 9, `allocation.rs` 12,
`slot_attention.rs` 17, `ablation.rs` 11, `support.rs` 1 (`python_round`) =
**77** new unit tests. All 260 tests pass; 0 failed.

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt -p prin-train -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (all-features) | `cargo clippy -p prin-train --all-targets --all-features -- -D warnings` | PASS |
| Workspace build | `cargo build --workspace` | PASS |
| Workspace tests (default) | `cargo test --workspace` | PASS, no regressions (every crate green) |
| `prin-train` (default) | `cargo test -p prin-train` | PASS — 260/260 (see "Test counts") |
| `prin-train` (strict-checks) | `cargo test -p prin-train --features strict-checks` | PASS — 233/233 (2 more pre-existing `strict-checks`-only tests, unaffected by this session) |
| `prin-train` coverage | `cargo llvm-cov -p prin-train --summary-only` | PASS — all new/touched files ≥95% on region/function/line (see acceptance-criteria table) |
| Rustdoc (`prin-train`) | `RUSTDOCFLAGS=-D warnings cargo doc -p prin-train --no-deps` | PASS — 0 warnings, including `#![warn(missing_docs)]` and intra-doc-link resolution (several private-item doc links found and converted to plain code font during this session) |
| `cargo audit` | `cargo audit` | Exit code 0; 2 allowed warnings, unchanged from WP-025 close (`paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27) — no new dependency added this session |
| Snyk Code | `snyk code test crates/prin-train` | **PASS** — 0 issues (Snyk CLI is authenticated on this machine this session, unlike the standing-blocked condition PSR-022–PSR-025 documented; disposition may have changed since the last recheck, or this is a transient authenticated window — re-verify at S4, do not assume permanently resolved without re-confirmation) |
| Snyk Open Source | Not run | Cargo is not a Snyk-supported package manager (R23 disposition, unchanged); `cargo audit` is the authoritative ecosystem-native gate |
| Python gates (ruff/mypy/interrogate/bandit/pytest) | Not run | No Python file under version control was touched this session (the new `wp026_generate_prinet_references.py` is ad-hoc/gitignored, same class as prior WPs' generator scripts); no PyO3/Python bindings delivered this session (see dedicated section above) |

## Parity-evidence disposition

Per the S1 exit-gate requirement (Development Workflow and Audit Standards
§3, "parity-evidence disposition stated"), confirmed via `grep`/direct
inspection against `DOCS/archive and reference from PRINet 3.0/` before
writing any Rust: `PhaseTracker`, `HybridPRINetV2`, `OscillatoryAttention`
(`nn/layers.py`), `SlotAttentionModule`/`TemporalSlotAttentionMOT`,
`PhaseTrackerFrozen`/`PhaseTrackerStatic`/`SlotAttentionNoGRU`/
`SlotAttentionFrozen`, and `AdaptiveOscillatorAllocator`/
`DynamicPhaseTracker` all exist and were read in full in the reference
tree before porting.

Two new golden-value parity tests call the actual PRINet 3.0 reference
classes directly (`wp026_generate_prinet_references.py`, same "import and
call the real class" precedent WP-023 established for parameter-explicit
primitives):

- `OscillatoryAttention.forward` — `tests/parity_attention.rs`, explicit
  extracted `nn.Linear` weights (`state_dict()`), `alpha` overridden to a
  nonzero value (default init is zero, which would leave the coherence
  bias untested), `dropout=0.0` for determinism, external `phase` tensor.
  `rtol=1e-6, atol=1e-6`. Passed on first run.
- `PhaseTracker.phase_similarity` — `tests/parity_phase_tracker.rs`, called
  directly on the actual reference method (parameter-free formula).
  `rtol=1e-6, atol=1e-6`. Passed on first run.

**Not independently golden-value-parity-tested at the whole-module level:**
`HybridPRINetV2`, `PhaseTracker.forward`/`.encode`/`.evolve`,
`SlotAttentionModule.forward`, `TemporalSlotAttentionMOT`, and the four
ablation variants. Rationale, applying the same "component parity, not
whole-network parity" precedent Project Plan amendment #19 established for
`BandNetwork`: each of these composes primitives that are *already*
independently parity-tested — `DiscreteDeltaThetaGamma` (WP-022,
`parity_bands.rs`) and `OscillatoryAttention` (this session,
`parity_attention.rs`) for `HybridPRINetV2`/`PhaseTracker`; standard
`Linear`/`LayerNorm`/`GRU` (Burn's own well-tested implementations, not
PRIN-specific numerics) for `SlotAttentionModule`. Full end-to-end weight
transcription for a `torch.manual_seed`-initialized `HybridPRINetV2` (input
projection + phase projection + `DiscreteDeltaThetaGamma`'s 13 tensors +
`n_layers` attention blocks' worth of `OscillatoryAttention`'s 11 tensors
each + FFN/norm/classifier weights) would verify the *wiring* correctness
of `forward`, which this session instead verifies via targeted shape,
gradient-flow, and mathematical-invariant tests (e.g.
`forward_returns_log_probabilities`'s `log_softmax` row-sums-to-1 check).
Flagged explicitly for S2 review: if the auditor judges component-level
parity insufficient for `HybridPRINetV2`'s "wiring is the novel
contribution" argument, a full end-to-end parity test is a bounded,
well-scoped S3 remediation (the weight-transcription pattern is already
established by this session's `parity_attention.rs`).

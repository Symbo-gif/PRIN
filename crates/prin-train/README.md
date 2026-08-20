# prin-train

Trainable layer stack for PRIN, built on the [Burn](https://burn.dev)
autodiff backend.

## Implemented

### WP-022: Trainable bands and resonance primitives (sessions 0085–0088)

- **`bands::DiscreteDeltaThetaGamma`** — trainable discrete-time multi-rate
  hierarchical oscillator network (rebuild of PRINet 3.0
  `core.propagation.networks.DiscreteDeltaThetaGamma`): learned intra-band
  coupling, phase-amplitude-coupling gating (delta→theta, theta→gamma), and
  Stuart–Landau amplitude dynamics, all in a fixed number of discrete macro
  steps (no inner ODE loop).
- **`layers::ResonanceLayer`** — trainable single-layer extended-Kuramoto
  resonance primitive (rebuild of PRINet 3.0 `nn.layers.ResonanceLayer`):
  learned coupling, decay, input projection, and frequency modulation.

### WP-023: Inhibition, activations, energy, and HEP (sessions 0089–0092)

- **`inhibition::FeedbackInhibition`** — feedback lateral inhibition with a
  straight-through estimator (STE) for competitive k-WTA activation
  (rebuild of the trainable half of PRINet 3.0
  `core.propagation.inhibition.FeedbackInhibition`): hard top-$k$ selection in
  the forward pass and soft temperature-scaled sigmoid backward gradients, with
  optional target-sparsity parameterization ($k = \lfloor (1 - s) \cdot N \rfloor$).
- **`activations`** — complex and phase activation functions (rebuild of PRINet 3.0
  `nn.activations`):
  - `d_silu` — analytic derivative of the SiLU/swish function ($d/dx [x \cdot \sigma(x)]$).
  - `ComplexTensor` — lightweight real-imaginary pair representation for complex
    states in Burn.
  - `HolomorphicActivation` — split-complex holomorphic activation module applying
    $\tanh$ independently to real and imaginary components.
  - `phase_activation` — periodic phase activation wrapping phase angles into
    $[-\pi, \pi)$ via $2\pi$-modular arithmetic.
  - `GatedPhaseActivation` — trainable gated phase activation combining phase
    wrapping, $d_{\text{silu}}$ modulation, and learned gate bias.
- **`energy::HolomorphicEnergy`** — holomorphic energy function for complex oscillator
  states (rebuild of PRINet 3.0 `nn.hep.HolomorphicEnergy`): coupling energy
  ($-\frac{1}{2} \text{Re}(z^\dagger W z)$), self-energy penalizing deviation from
  unit amplitude, and optional supervised task loss with $\beta$ weighting.
- **`hep::HolomorphicEp`** — Holomorphic Equilibrium Propagation trainer (rebuild
  of PRINet 3.0 `nn.hep.HolomorphicEquilibriumPropagation`): coordinates free-phase
  and nudged-phase ($+\beta, -\beta$) equilibrium relaxation and computes
  contrastive coupling parameter gradients via closed-form outer-product symmetric
  differences.
- **`error::TrainError`** — typed error enum (`EmptyBand`, `ShapeMismatch`,
  `NonFiniteParameter`, `InvalidTimestep`, `NonFiniteState`, `InvalidK`,
  `DivisionByZero`, `StepLimitExceeded`, `BetaTooSmall`), re-exported at the
  crate root.

### WP-024: Oscillator-aware optimizers (sessions 0093–0096)

- **`feedback`** — shared order-parameter feedback and optimizer contract
  (rebuild of PRINet 3.0 `nn/optimizers.py`):
  - `OrderParameter` — global-or-per-group order parameter with Q3 dict
    resolution (SCALR's `Union[float, Dict[str, float]]` input).
  - `StepFeedback` — per-step input (order parameter, phase, amplitude).
  - `OscillatorOptimizer` — uniform `step`/`state_dict`/`load_state_dict`
    trait all three optimizers implement; the seam WP-025's thin
    `torch.optim.Optimizer` wrapper bridges to.
- **`sync_gd::SyncGd`** — synchronized gradient descent with momentum and
  synchronization-barrier penalty (rebuild of PRINet 3.0
  `SynchronizedGradientDescent`): `penalty = λ·max(0, K_c − K)²`,
  `grad_modulation = max(0.1, 1 − grad_scale)` lr reduction.
- **`rip::Rip`** — Hebbian coupling-matrix update (rebuild of PRINet 3.0
  `RIPOptimizer`): `ΔK[i,j] = η·cos(φ[i] − φ[j])·|r[j]|·(r_target − r[i])`,
  diagonal zeroed, combined additively with plain gradient descent.
  **Documented deviation:** fixes `n_oscillators` at construction and returns
  `TrainError::ShapeMismatch` on mismatched input (PRINet 3.0 silently skips
  non-square-matching parameters).
- **`scalr::Scalr`** — adaptive learning-rate optimizer with oscillation-aware
  decay (rebuild of PRINet 3.0 `SCALROptimizer`): `lr_scale = r_min + (1 − r_min)·clamp(r, 0, 1)^α`,
  windowed-variance oscillation detection with multiplicative lr decay, and
  adaptive `r_min` via EMA. Includes per-group lr scaling entry point.
- **`error::TrainError`** — extended with `InvalidLearningRate`,
  `InvalidMomentum`, `InvalidWeightDecay`, `InvalidSyncPenalty`,
  `InvalidCriticalOrder`, `InvalidTargetAmplitude`, `InvalidRMin`,
  `InvalidAlpha` variants.

All three optimizers expose validated `Config`/`State` contracts with serde
JSON round-trip and deterministic resume (step N uninterrupted vs. step k →
snapshot → restore → step N−k, `<1e-12` final parameters). `load_state_dict`
re-validates every hyperparameter through the original constructor.

All modules expose validated `Config` contracts, explicit `Params` structs
(where learnable parameters exist: `DiscreteDeltaThetaGammaParams`,
`ResonanceLayerParams`, `GatedPhaseActivationParams`, all re-exported at crate
root and compile-guarded by `tests/public_api.rs`), and validated `State` contracts.
See each module's rustdoc for exact formulations and correspondence to PRINet 3.0.

Golden-value parity tests against PRINet 3.0 (`torch==2.13.0+cpu`, float64)
live in `tests/parity_*.rs` (`parity_bands`, `parity_layers`, `parity_inhibition`,
`parity_activations`, `parity_energy`, `parity_optimizers`). Gradient reference
tests (autodiff vs. central finite difference) and `burn::record` serialization
round-trips are in each module's unit tests. The `bincode` 2.0.1 transitive
advisory (RUSTSEC-2025-0141) is governed by Project Plan amendment #27.

### WP-025: Production Torch autograd bridge (sessions 0097–0100)

- **`crates/prin-py/src/bindings/train.rs`** — PyO3/DLPack `torch.autograd.Function`
  bridges: `PyResonanceLayerBridge` / `PyGatedPhaseActivationBridge` with
  `*Ctx` backward contexts. Each bridge reads a DLPack capsule, runs the
  `prin-train` Rust forward (multi-step Kuramoto integration or gated phase
  activation), and returns a DLPack capsule plus a Rust context whose
  `backward` runs the Rust backward pass. Forward and backward each cross
  the boundary exactly once per call. Checkpoint loading validates decoded
  record shapes against the layer's configuration (WP025-F1 fix).
- **`python/prin/nn/__init__.py`** — `ResonanceLayer` and `GatedPhaseActivation`
  `torch.nn.Module` wrappers with `rust_state_dict` / `load_rust_state_dict`
  checkpoint methods. 31 Python tests, all passing `torch.autograd.gradcheck`
  in float64.
- **DV-021 recorded:** boundary overhead at small shapes exceeds the `<5%`
  acceptance target (+40.6% at 32-oscillator/16-dim/8-batch); moderate shape
  is within tolerance (+4.5% at 128-oscillator/64-dim/32-batch). Deferred to
  a future WP for boundary-crossing optimization.

### WP-026: PhaseTracker, Hybrid, baselines, and allocation (session 0101)

- **`attention::OscillatoryAttention`** — multi-head attention with an
  additive oscillatory coherence bias (rebuild of PRINet 3.0
  `nn.layers.OscillatoryAttention`): standard scaled dot-product attention
  plus a learnable per-head bias toward phase-aligned tokens,
  `score = QKᵀ/√d_k + α·cos(φ_i − φ_j)`. Masked-attention support (unused by
  any caller in this WP) is not ported.
- **`phase_tracker::PhaseTracker`** — PRIN's primary contribution: a
  phase-based multi-object tracker (rebuild of PRINet 3.0
  `nn.hybrid.PhaseTracker`). Encodes detections to phase/amplitude via an
  MLP, evolves them through `bands::DiscreteDeltaThetaGamma`, and matches
  frames by phase-coherence similarity (a real-valued reformulation of the
  reference's `torch.complex64` cosine similarity — Burn has no
  complex-tensor autodiff) with greedy descending-similarity assignment.
- **`hybrid::HybridPRINetV2`** — the canonical hybrid oscillator + attention
  classification architecture (rebuild of PRINet 3.0
  `nn.hybrid.HybridPRINetV2`): input → token projection → adaptive
  oscillator phase (`DiscreteDeltaThetaGamma`) interleaved with
  `OscillatoryAttention` + FFN blocks → pool → classify. The optional CNN
  stem for image inputs (`use_conv_stem`) is not ported — out of this WP's
  oscillatory-binding scope, no exercising caller.
- **`slot_attention::SlotAttentionModule`/`TemporalSlotAttentionMOT`** — the
  non-oscillatory Slot Attention (Locatello et al. 2020) comparison
  baseline (rebuild of PRINet 3.0 `nn.slot_attention`); the latter is the
  direct head-to-head tracking comparison against `PhaseTracker`. Slot
  initialization draws fresh noise every `forward` call (a genuine
  per-call stochastic entry point, unlike every other `forward` in this
  crate), so `forward`/`process_frame` take `&mut Seed` directly.
  `SlotAttentionCLEVRN` (a CLEVR-N classification adapter, not a tracking
  comparison) is not ported — out of scope per this WP's non-goals.
- **`ablation`** — structural ablation variants (rebuild of PRINet 3.0
  `nn.ablation_variants`): `PhaseTrackerFrozen` (frozen dynamics, trainable
  encoder), `PhaseTrackerStatic` (no coupling, fixed frequencies),
  `SlotAttentionNoGRU` (no temporal carry-over), `SlotAttentionFrozen`
  (fully frozen). The reference's string-keyed `create_ablation_tracker`
  factory is not ported (the six variants' `forward` signatures genuinely
  differ in Rust's static type system); callers construct the specific
  variant type directly.
- **`allocation::AdaptiveOscillatorAllocator`/`DynamicPhaseTracker`** —
  task-complexity-driven adaptive oscillator-count allocation (rebuild of
  PRINet 3.0 `nn.adaptive_allocation`): rule-based (piecewise-linear) and
  learned (MLP-predicted band fractions) strategies, `estimate_complexity`,
  and a lazily-caching per-budget `PhaseTracker` factory.
  `DynamicPhaseTracker` is deliberately not a Burn `Module` — see its module
  docs.

New shared helpers in `support.rs`: `seeded_linear`/`seeded_gru` (build
`burn::nn::Linear`/`Gru` from this crate's `Seed` rather than
`Config::init`'s backend-global RNG — a `static Mutex` shared across
parallel test threads, discovered while gradchecking `OscillatoryAttention`),
`seeded_standard_normal` (Box–Muller, for `SlotAttentionModule`'s per-call
noise), `python_round` (round-half-to-even, for `allocation`'s
`round(...)`-derived formulas), `phase_coherence_similarity` (shared by
`PhaseTracker`/`PhaseTrackerStatic`), and `greedy_match_by_similarity`
(shared by every tracker variant's frame-to-frame assignment).

Golden-value parity tests against the actual PRINet 3.0 reference classes
(`torch==2.13.0+cpu`, float64) added: `tests/parity_phase_tracker.rs`
(`phase_similarity`), `tests/parity_attention.rs`
(`OscillatoryAttention.forward`, explicit extracted weights),
`tests/parity_hybrid.rs` (`HybridPRINetV2.forward`, full weight transcription
via `HybridPRINetV2Params`/`init_from_params` — added in S3 remediation,
which also found and fixed a missing ReLU in the classifier head). `bands`-level
composition (`DiscreteDeltaThetaGamma`) is already parity-tested.

**S3 remediation (session 0103):** two D4 findings closed. WP026-F1 (FIXED):
added `TrainError::StrategyMismatch` variant and a strategy-variant check in
`AdaptiveOscillatorAllocator::validate_shapes` detecting `(Learned, None)`
checkpoint mismatches. WP026-F2 (FIXED): added `HybridPRINetV2Params` /
`init_from_params` (following the established `DiscreteDeltaThetaGamma`/
`OscillatoryAttention` pattern) and `tests/parity_hybrid.rs` whole-module
golden-value parity test; the parity test revealed a genuine wiring bug
(classifier head missing ReLU between linear layers), fixed in the same
commit. Delta re-audit CLEAN.

**Not delivered in WP-026 S1 — PyO3 bindings and Python wrappers.**
`crates/prin-py/` PyO3 bindings and `python/prin/nn/` thin wrappers were
declared in WP-026's scope (`DOCS/reports/025-project-state.md` §6) but were
not implemented in session 0101: WP-025's own production bridge for two
materially simpler modules (`ResonanceLayer`, `GatedPhaseActivation` — each a
single flat parameter set) required ~514 lines of custom Rust
`torch.autograd.Function`-bridge code and was itself a full four-session work
package (S1–S4); replicating that depth for six larger modules in one S1
session budget risked exactly the kind of under-tested bridge code WP-025's
own audit found (WP025-F1, WP025-F2). Recorded as an explicit, evidence-backed
carried-scope item in the WP-026 S1 handoff note
(`DOCS/experiments/0101-wp026-s1-handoff.md`) — **closed by the
Exec-WP-026 S1 executive session below**, not left unassigned.

### Exec-WP-026 S1: PyO3 bindings and Python wrappers for WP-026

Delivered the carried-scope item above: `crates/prin-py/src/bindings/
{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.rs` and
`python/prin/nn/{attention,phase_tracker,hybrid,slot_attention,ablation,
allocation}.py` — see `crates/prin-py/README.md` for the full bridge-design
breakdown (differentiable vs. non-differentiable method split, the
stochastic-recompute and dropout-determinism hazards, and the checkpoint
shape-validation bug found and fixed). This session also added
`validate_shapes()` to `OscillatoryAttention`, `PhaseTracker`,
`HybridPRINetV2`, `SlotAttentionModule`, `TemporalSlotAttentionMOT`,
`PhaseTrackerStatic`, `SlotAttentionNoGRU`, and
`AdaptiveOscillatorAllocator` (mirroring `ResonanceLayer`/
`GatedPhaseActivation`'s WP025-F1 precedent), with regression tests for each;
`prin-train` full-suite coverage on the six touched files is ≥96%/97.5%/96.5%
(region/function/line) or better. See
`DOCS/experiments/0101-exec-wp026-s1-handoff.md` for the full
acceptance-criteria → evidence map. Full session is subject to the
already-registered WP-026 S2/S3/S4 audit cycle (sessions 0102–0104).

### WP-027: Trainable-stack integration and Phase 4 gate (sessions 0105–0108)

- **`dataset::SequenceData`/`TemporalClevrNConfig`/`generate_temporal_clevr_n`/
  `generate_dataset`** — structural port of PRINet 3.0's temporal CLEVR-N
  sequence generator (`temporal_training.py:68-253`): constant-velocity motion
  with elastic boundary bounce, occlusion zeroing, appearance-feature swap,
  velocity reversal, additive noise. Uses the project's counter-based `Seed`
  (Project Plan §4 rule 3) instead of PRINet 3.0's per-perturbation
  `torch.Generator(seed + offset)` streams.
- **`losses::hungarian_similarity_loss`/`temporal_smoothness_loss`** — direct
  ports of the reference training losses
  (`temporal_training.py:261-336`). Hand-computed parity tests verify perfect
  diagonal → near-zero loss, uniform similarity → `ln(2)`, and MSE between
  known matrices.
- **`trainer::TemporalTrainerConfig`/`TrainingResult`/`ValMetrics`/
  `train_phase_tracker`/`evaluate_phase_tracker`** — the Rust-native training
  loop (Burn `Adam` + warmup/cosine LR + gradient clipping + early stopping
  with best-checkpoint restore), porting PRINet 3.0's `TemporalTrainer`
  (`temporal_training.py:454-869`). Two documented deviations: per-tensor
  gradient clipping (Burn's `GradientClippingConfig::Norm`) vs. PyTorch's
  global `clip_grad_norm_`; directly-computed scalar cosine LR formula vs.
  PyTorch's `CosineAnnealingLR` step-count state.
- **`benches/phase_tracker_bridge.rs`** — Criterion baseline for
  `PhaseTracker::forward`/`match_frames`, extending DV-021's `ResonanceLayer`
  bench to a second module.
- **`tests/integration_temporal_clevr_n.rs`** — acceptance-criterion validation
  run (3 seeds, canonical protocol), `#[ignore]`d by default (~115s in
  `--release`). Mean IP = 1.00000 ≥ registered 0.99868 threshold.
- **`tests/integration_checkpoint_resume.rs`** — serialization acceptance:
  trains PhaseTracker for 4 epochs, checkpoints the *trained* model via
  `BinBytesRecorder<DoublePrecisionSettings>`, reloads into a fresh instance
  from a *different* seed, confirms bit-identical evaluation metrics.
- **`crates/prin-py/src/bindings/optim.rs`** — `SyncGdBridge`/`ScalrBridge`/
  `RipBridge` non-differentiable optimizer-step bridges.
- **`crates/prin-py/src/bindings/trainer.rs`** — `train_phase_tracker` PyO3
  entry point running the Rust trainer end to end; `TrainingResult` pyclass.
- **`python/prin/nn/optimizers.py`** — `SyncGd`/`Scalr`/`Rip`
  `torch.optim.Optimizer` subclasses.
- **`python/prin/train.py`** — thin Python entry point for the Rust-native
  trainer (`train_phase_tracker`/`TrainingResult`).

S2 audit: PASS, zero findings. S3: no-change closure (zero findings to
remediate), delta re-audit CLEAN.

## Not yet implemented

CUDA DLPack path (DV-005).

Rebuild target for PRINet 3.0 `nn/{layers,optimizers,activations,hep,hybrid,
slot_attention,ablation_variants,adaptive_allocation}.py` and the trainable
half of `core/propagation/{networks,inhibition}.py` — **complete through
WP-027** (all modules ported; optimizer wrappers delivered).

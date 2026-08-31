# prin.nn (PyTorch neural network modules)

Trainable layers and PyTorch wrappers (Phase 4).

## Overview

`torch.nn.Module` wrappers and `torch.autograd.Function` bridges connecting
PyTorch to `prin-train` in Rust via zero-copy DLPack tensor exchange. Every
differentiable bridge crosses the Rust/Python boundary exactly once per call
(Coding Standards §3.2); trainable parameters live in Rust and are trained by
`prin-train`'s oscillator-aware optimizers (`SyncGd`/`Rip`/`Scalr`), not
`torch.optim`. See each submodule's own docstring for its full contract.

## Delivered symbols

- **`ResonanceLayer`, `GatedPhaseActivation`** (`__init__.py`, WP-025) — the
  original production bridge pattern this package's other modules follow.
- **`OscillatoryAttention`** (`attention.py`, Exec-WP-026 S1).
- **`PhaseTracker`, `TrackingResult`** (`phase_tracker.py`, Exec-WP-026 S1) —
  PRIN's primary contribution. `encode`/`evolve`/`phase_similarity` are
  differentiable; `match_frames`/`track_sequence` are non-differentiable
  evaluation utilities (greedy frame matching has no gradient).
- **`HybridPRINetV2`** (`hybrid.py`, Exec-WP-026 S1) — the canonical hybrid
  oscillator + attention classifier.
- **`SlotAttentionModule`, `TemporalSlotAttentionMOT`**
  (`slot_attention.py`, Exec-WP-026 S1) — the non-oscillatory comparison
  baseline; both draw fresh per-call stochastic noise from a caller-supplied
  `prin._prin_core.Seed`.
- **`PhaseTrackerFrozen`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`,
  `SlotAttentionFrozen`** (`ablation.py`, Exec-WP-026 S1) — structural
  ablation variants.
- **`AdaptiveOscillatorAllocator`, `DynamicPhaseTracker`, `OscillatorBudget`,
  `estimate_complexity`** (`allocation.py`, Exec-WP-026 S1) —
  complexity-driven adaptive oscillator-count allocation, entirely
  non-differentiable; neither class is a `torch.nn.Module`.

`_bridge.py` provides the shared `apply_rust_bridge` generic
`torch.autograd.Function` glue every differentiable entry point above uses.

- **`SyncGd`, `Scalr`, `Rip`** (`optimizers.py`, WP-027) —
  `torch.optim.Optimizer` subclasses wrapping the Rust optimizer-step bridges
  (`SyncGdBridge`/`ScalrBridge`/`RipBridge` in `crates/prin-py/src/bindings/optim.rs`).

- **`FeedforwardInhibition`**, **`DentateGyrusConverter`**, **`DGLayer`**,
  **`oscillatory_weight_init`**, **`SparsityRegularizationLoss`**
  (`inhibition_layers.py`, WP-036A / 0144A1) — feedforward lateral
  inhibition, dentate gyrus pattern separation, and sparsity regularization,
  all Rust-backed via `prin-train`.
- **`PhaseToRateConverter`**, **`PhaseToRateAutoencoder`**,
  **`DenseAutoencoder`** (`autoencoders.py`, WP-036A / 0144A2) —
  phase-to-rate conversion (smooth/hard/annealed) and dense autoencoding,
  Rust-backed via `prin-train`.
- **`HierarchicalResonanceLayer`**, **`PhaseAmplitudeCouplingLayer`**,
  **`DiscreteDeltaThetaGammaLayer`** (`hierarchical_layers.py`, WP-036A /
  0144A3) — multi-band hierarchical resonance, PAC gating, and discrete
  three-band networks, Rust-backed via `prin-train`.
- **`PRINetModel`**, **`compile_model`** (`model.py`, WP-036A / 0144A4) —
  the canonical PRINet 3.0 full model container (Rust-backed) and a pure-
  Python `torch.compile` passthrough.

## Not yet implemented

`HybridPRINet` (v1); `DiscreteDeltaThetaGamma` standalone binding (the
composed `DiscreteDeltaThetaGammaLayer` is real; the independent core
binding is assigned to WP-036B).

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

## Not yet implemented

`PRINetModel`, `HierarchicalResonanceLayer`, `PhaseToRateConverter`,
`HybridPRINet` (v1); optimizers (`SyncGD`, `SCALR`, `RIP`, `Alternating` —
Rust implementations exist in `prin-train`; a thin `torch.optim.Optimizer`
wrapper is future-WP scope); the remaining activations
(`HolomorphicActivation`); the HEP trainer.

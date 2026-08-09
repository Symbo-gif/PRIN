# prin.nn (PyTorch neural network modules)

Trainable layers and PyTorch wrappers (Phase 4).

## Overview

Provides `torch.nn.Module` wrappers and `torch.autograd.Function` bridges connecting PyTorch to `prin-train` in Rust via zero-copy DLPack tensor exchange.

Planned symbols:
- `ResonanceLayer`, `PRINetModel`, `HierarchicalResonanceLayer`, `OscillatoryAttention`, `PhaseToRateConverter`.
- `SlotAttentionModule`, `TemporalSlotAttentionMOT` baselines.
- Optimizers (`SyncGD`, `SCALR`, `RIP`, `Alternating`) and activations (`dSiLU`, `HolomorphicActivation`, `PhaseActivation`).

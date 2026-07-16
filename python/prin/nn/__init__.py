"""Trainable layers and models (PyTorch-facing).

``torch.nn.Module`` wrappers and ``torch.autograd.Function`` bridges whose
forward/backward call into the Rust core (``prin-train``) via DLPack zero-copy
tensor exchange. Also hosts the pure-torch SlotAttention baselines used for
head-to-head comparison.

Planned symbols (Phase 4, PRINet-3.0 compatible): ResonanceLayer, PRINetModel,
HierarchicalResonanceLayer, OscillatoryAttention, PhaseToRateConverter,
HybridPRINet, HybridPRINetV2, PhaseTracker, SlotAttentionModule,
TemporalSlotAttentionMOT, optimizers (SyncGD, SCALR, RIP, Alternating),
activations (dSiLU, HolomorphicActivation, PhaseActivation,
GatedPhaseActivation), and the HEP trainer.
"""

from __future__ import annotations

__all__: list[str] = []

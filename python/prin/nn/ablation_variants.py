"""PRINet 3.0-compatible ablation framework (``prinet.nn.ablation_variants``).

``AblationHybridPRINetV2`` is a PyTorch composition over the real Rust-backed
compatibility layers — :class:`prin.nn.attention.OscillatoryAttention` and the
standalone :class:`prin.nn.DiscreteDeltaThetaGamma` bridge (both delegate their
numerics to ``prin_train`` through PyO3) plus stock ``torch.nn`` mixing,
normalisation, and classifier heads. It is the same category as
:mod:`prin.nn.hybrid_compat`'s hybrid models and :mod:`prin.nn.mot_evaluation`:
a benchmark-experiment model whose oscillatory dynamics live in Rust, so it is
not part of the ``check_no_python_numerics`` compat-surface scan.

Adaptation from the reference (Testing Standards §1.1 — compat-layer only):
PRIN's :class:`~prin.nn.attention.OscillatoryAttention` bridge rejects a
non-zero attention dropout (the Burn backend draws from an unseeded RNG under
autodiff), so the attention sub-layers are built with ``dropout=0.0`` while the
FFN / classifier ``nn.Dropout`` still honour ``config.dropout``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from prin.nn import DiscreteDeltaThetaGamma
from prin.nn.attention import OscillatoryAttention

__all__ = [
    "AblationConfig",
    "AblationHybridPRINetV2",
    "create_ablation_model",
]


@dataclass
class AblationConfig:
    """Configuration for HybridPRINetV2 ablation variants.

    Attributes:
        variant: One of ``"full"``, ``"attention_only"``,
            ``"oscillator_only"``, ``"shared_phase"``.
        n_input: Input dimension.
        n_classes: Number of classes.
        d_model: Model dimension.
        n_heads: Attention heads.
        n_layers: Number of layers.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per layer.
        coupling_strength: Coupling *K*.
        pac_depth: PAC modulation depth.
        dropout: Dropout rate.
    """

    variant: str = "full"
    n_input: int = 256
    n_classes: int = 10
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    n_delta: int = 4
    n_theta: int = 8
    n_gamma: int = 32
    n_discrete_steps: int = 5
    coupling_strength: float = 2.0
    pac_depth: float = 0.3
    dropout: float = 0.1


class AblationHybridPRINetV2(nn.Module):
    """HybridPRINetV2 with configurable ablation of oscillatory components.

    Variants:

    - ``"full"``: standard HybridPRINetV2 (no ablation).
    - ``"attention_only"``: remove oscillatory dynamics.
    - ``"oscillator_only"``: remove attention; MLP token mixing only.
    - ``"shared_phase"``: all oscillators share the same phase.

    Args:
        config: Ablation configuration dataclass.
    """

    _LOGIT_CLAMP = 20.0

    def __init__(self, config: AblationConfig) -> None:
        """Build the ablation-variant module graph."""
        super().__init__()
        self.config = config
        self.variant = config.variant
        self.d_model = config.d_model
        self.n_layers = config.n_layers

        n_osc = config.n_delta + config.n_theta + config.n_gamma
        self.n_tokens = n_osc

        self.input_proj = nn.Linear(config.n_input, n_osc * config.d_model)

        if config.variant != "oscillator_only":
            self.attn_layers: nn.ModuleList | None = nn.ModuleList()
            self.norm1_layers: nn.ModuleList | None = nn.ModuleList()
            for _ in range(config.n_layers):
                self.attn_layers.append(
                    OscillatoryAttention(
                        d_model=config.d_model,
                        n_heads=config.n_heads,
                        dropout=0.0,
                    )
                )
                self.norm1_layers.append(nn.LayerNorm(config.d_model))
        else:
            self.attn_layers = None
            self.norm1_layers = None

        self.ffn_layers = nn.ModuleList()
        self.norm2_layers = nn.ModuleList()
        for _ in range(config.n_layers):
            self.ffn_layers.append(
                nn.Sequential(
                    nn.Linear(config.d_model, config.d_model * 4),
                    nn.GELU(),
                    nn.Dropout(config.dropout),
                    nn.Linear(config.d_model * 4, config.d_model),
                    nn.Dropout(config.dropout),
                )
            )
            self.norm2_layers.append(nn.LayerNorm(config.d_model))

        if config.variant not in ("attention_only",):
            self.dynamics: DiscreteDeltaThetaGamma | None = DiscreteDeltaThetaGamma(
                n_delta=config.n_delta,
                n_theta=config.n_theta,
                n_gamma=config.n_gamma,
                coupling_strength=config.coupling_strength,
                pac_depth=config.pac_depth,
            )
            self._shared_phase = config.variant == "shared_phase"
            self.phase_init: nn.Linear | None = nn.Linear(
                config.n_input, n_osc * config.n_heads
            )
        else:
            self.dynamics = None
            self._shared_phase = False
            self.phase_init = None

        self.pool_norm = nn.LayerNorm(config.d_model)
        self.classifier = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.n_classes),
        )

    def forward(self, x: Tensor) -> Tensor:
        """Forward pass with ablation-specific routing.

        Args:
            x: Input ``(B, D)`` or ``(D,)``.

        Returns:
            Log-probabilities ``(B, K)`` or ``(K,)``.
        """
        was_1d = x.dim() == 1
        if was_1d:
            x = x.unsqueeze(0)

        b = x.shape[0]
        h = self.input_proj(x).view(b, self.n_tokens, self.d_model)

        phase_state: Tensor | None = None
        dyn_phase: Tensor | None = None
        amp_state: Tensor | None = None
        if self.dynamics is not None and self.phase_init is not None:
            phase_raw = self.phase_init(x).view(b, self.n_tokens, self.config.n_heads)
            phase_state = phase_raw % (2.0 * math.pi)
            if self._shared_phase:
                phase_state = phase_state.mean(dim=1, keepdim=True).expand_as(
                    phase_state
                )
            amp_state = torch.ones(b, self.n_tokens, device=x.device, dtype=x.dtype)
            dyn_phase = phase_state.mean(dim=-1)

        for i in range(self.n_layers):
            token_phase: Tensor | None = None
            if (
                self.dynamics is not None
                and phase_state is not None
                and dyn_phase is not None
                and amp_state is not None
            ):
                dyn_phase, amp_state = self.dynamics.integrate(
                    dyn_phase,
                    amp_state,
                    n_steps=self.config.n_discrete_steps,
                    dt=0.01,
                )
                token_phase = dyn_phase.unsqueeze(-1).expand(
                    b, self.n_tokens, self.config.n_heads
                )

            if self.attn_layers is not None and self.norm1_layers is not None:
                h_norm = self.norm1_layers[i](h)
                if token_phase is not None:
                    h = h + self.attn_layers[i](h_norm, phase=token_phase)
                else:
                    zero_phase = torch.zeros(
                        b,
                        self.n_tokens,
                        self.config.n_heads,
                        device=x.device,
                        dtype=x.dtype,
                    )
                    h = h + self.attn_layers[i](h_norm, phase=zero_phase)
            else:
                h_mixed = h.mean(dim=1, keepdim=True).expand_as(h)
                h = h + 0.1 * h_mixed

            h_norm = self.norm2_layers[i](h)
            h = h + self.ffn_layers[i](h_norm)

        pooled = self.pool_norm(h.mean(dim=1))
        logits = self.classifier(pooled)
        logits = torch.clamp(logits, -self._LOGIT_CLAMP, self._LOGIT_CLAMP)
        log_probs = F.log_softmax(logits, dim=-1)

        if was_1d:
            return log_probs.squeeze(0)
        return log_probs


def create_ablation_model(
    variant: str = "full",
    n_input: int = 256,
    n_classes: int = 10,
    **kwargs: Any,
) -> AblationHybridPRINetV2:
    """Create an ablation model variant.

    Args:
        variant: One of ``"full"``, ``"attention_only"``,
            ``"oscillator_only"``, ``"shared_phase"``.
        n_input: Input feature dimension.
        n_classes: Number of output classes.
        **kwargs: Passed through to :class:`AblationConfig`.

    Returns:
        Configured :class:`AblationHybridPRINetV2`.
    """
    config = AblationConfig(
        variant=variant,
        n_input=n_input,
        n_classes=n_classes,
        **kwargs,
    )
    return AblationHybridPRINetV2(config)

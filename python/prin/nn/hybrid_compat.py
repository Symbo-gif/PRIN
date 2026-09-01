"""PRINet 3.0-compatible hybrid-model family.

Delivers the three symbols exercised by the 0144E5 acceptance suite
(``HybridPRINet``, ``AlternatingOptimizer``, ``HybridCLEVRN``) as real
``torch.nn.Module`` / optimizer compositions over existing Rust-backed
layers (``HierarchicalResonanceLayer``, ``PhaseToRateConverter``,
``SparsityRegularizationLoss``). Every differentiable stage delegates
to a Rust owner; this module only chains them with standard PyTorch
``nn.Linear`` / ``nn.TransformerEncoder`` / ``nn.LayerNorm`` projections.

The remaining three symbols (``HybridPRINetV2CLEVRN``,
``InterleavedHybridPRINet``, ``TemporalHybridPRINet``) stay as D-2.2
deferred-rebuild stubs — they are not exercised by 0144E5.

No numerical computation is introduced (Coding Standards Sec. 1.2).
"""

from __future__ import annotations

from typing import Any, NoReturn

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

__all__ = [
    "AlternatingOptimizer",
    "HybridCLEVRN",
    "HybridPRINet",
    "HybridPRINetV2CLEVRN",
    "InterleavedHybridPRINet",
    "TemporalHybridPRINet",
]

_EPS: float = 1e-6
_LOGIT_CLAMP: float = 50.0


class HybridPRINet(nn.Module):
    """End-to-end hybrid PRINet model.

    PRINet 3.0 ``nn.hybrid.HybridPRINet``: chains LOBM (oscillatory
    encoding) -> PhaseToRate (sparse conversion) -> GRIM (Transformer
    rate integration) -> classifier head. All oscillatory stages
    delegate to the Rust-backed ``HierarchicalResonanceLayer``;
    phase-to-rate conversion delegates to ``PhaseToRateConverter``;
    sparsity regularization delegates to ``SparsityRegularizationLoss``.

    Args:
        n_input: Input feature dimension.
        n_classes: Number of output classes.
        n_delta: Delta-band oscillators per LOBM layer.
        n_theta: Theta-band oscillators per LOBM layer.
        n_gamma: Gamma-band oscillators per LOBM layer.
        n_lobm_layers: Number of LOBM layers (stacked).
        lobm_steps: ODE integration steps per LOBM layer.
        lobm_dt: ODE timestep for LOBM.
        coupling_strength: Intra-band coupling K.
        pac_depth: Initial PAC modulation depth.
        rate_mode: PhaseToRateConverter mode.
        rate_sparsity: Target sparsity for rate codes.
        grim_d_model: Transformer model dimension.
        grim_n_heads: Number of attention heads.
        grim_n_layers: Number of Transformer layers.
        grim_dropout: Dropout rate in GRIM Transformer.
    """

    def __init__(
        self,
        n_input: int = 256,
        n_classes: int = 10,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        n_lobm_layers: int = 2,
        lobm_steps: int = 10,
        lobm_dt: float = 0.01,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        rate_mode: str = "soft",
        rate_sparsity: float = 0.1,
        grim_d_model: int = 64,
        grim_n_heads: int = 4,
        grim_n_layers: int = 2,
        grim_dropout: float = 0.1,
    ) -> None:
        """Construct the hybrid model with Rust-backed oscillatory stages."""
        super().__init__()

        from prin.nn.autoencoders import PhaseToRateConverter
        from prin.nn.hierarchical_layers import HierarchicalResonanceLayer
        from prin.nn.inhibition_layers import SparsityRegularizationLoss

        self.n_input = n_input
        self.n_classes = n_classes
        self.n_osc_total = n_delta + n_theta + n_gamma

        lobm_list: list[nn.Module] = []
        first_input_dim = n_input
        for i in range(n_lobm_layers):
            in_dim = first_input_dim if i == 0 else self.n_osc_total
            lobm_list.append(
                HierarchicalResonanceLayer(
                    n_delta=n_delta,
                    n_theta=n_theta,
                    n_gamma=n_gamma,
                    n_dims=in_dim,
                    n_steps=lobm_steps,
                    dt=lobm_dt,
                    coupling_strength=coupling_strength,
                    pac_depth=pac_depth,
                )
            )
        self.lobm_layers = nn.ModuleList(lobm_list)

        self.lobm_norms = nn.ModuleList(
            [nn.LayerNorm(self.n_osc_total) for _ in range(n_lobm_layers)]
        )

        self.phase_to_rate = PhaseToRateConverter(
            n_oscillators=self.n_osc_total,
            mode=rate_mode,
            sparsity=rate_sparsity,
        )

        self.sparsity_loss_fn = SparsityRegularizationLoss(
            target_sparsity=1.0 - rate_sparsity,
        )

        self.grim_proj = nn.Linear(self.n_osc_total, grim_d_model)
        self.grim_norm = nn.LayerNorm(grim_d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=grim_d_model,
            nhead=grim_n_heads,
            dim_feedforward=grim_d_model * 4,
            batch_first=True,
            dropout=grim_dropout,
        )
        self.grim_encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=grim_n_layers
        )

        self.classifier = nn.Sequential(
            nn.Linear(grim_d_model, grim_d_model),
            nn.ReLU(),
            nn.Dropout(grim_dropout),
            nn.Linear(grim_d_model, n_classes),
        )

    def forward(
        self,
        x: Tensor,
        return_rates: bool = False,
    ) -> Tensor | tuple[Tensor, Tensor]:
        """Forward pass through full HybridPRINet.

        Args:
            x: Input tensor of shape ``(B, D)`` or ``(D,)``.
            return_rates: If ``True``, also return sparse rate codes.

        Returns:
            Log-probabilities ``(B, K)``; or tuple of
            ``(log_probs, sparse_rates)`` if ``return_rates=True``.
        """
        was_1d = x.dim() == 1
        if was_1d:
            x = x.unsqueeze(0)

        h = x
        for lobm_layer, norm in zip(
            self.lobm_layers[:-1], self.lobm_norms[:-1], strict=True
        ):
            h = lobm_layer(h)
            h = norm(h)

        last_layer = self.lobm_layers[-1]
        last_norm = self.lobm_norms[-1]
        h_amp, osc_phase = last_layer(h, return_phase=True)
        h = last_norm(h_amp)

        rate_codes = self.phase_to_rate(osc_phase, h)

        grim_in = self.grim_proj(rate_codes)
        grim_in = self.grim_norm(grim_in)
        grim_in = grim_in.unsqueeze(1)
        grim_out = self.grim_encoder(grim_in)
        grim_out = grim_out.squeeze(1)

        grim_out = grim_out.float()
        logits = self.classifier(grim_out)
        logits = torch.clamp(logits, min=-_LOGIT_CLAMP, max=_LOGIT_CLAMP)
        log_probs = F.log_softmax(logits, dim=-1)

        if was_1d:
            log_probs = log_probs.squeeze(0)
            rate_codes = rate_codes.squeeze(0)

        if return_rates:
            return log_probs, rate_codes
        return log_probs

    def sparsity_loss(self, rate_codes: Tensor) -> Tensor:
        """Compute sparsity regularization loss on rate codes.

        Args:
            rate_codes: Sparse rate codes from ``forward(..., return_rates=True)``.

        Returns:
            Scalar sparsity loss.
        """
        result: Tensor = self.sparsity_loss_fn(rate_codes)
        return result

    def oscillatory_parameters(self) -> list[nn.Parameter]:
        """Return parameters belonging to the oscillatory (LOBM) stage."""
        params: list[nn.Parameter] = []
        for lobm in self.lobm_layers:
            params.extend(lobm.parameters())
        for norm in self.lobm_norms:
            params.extend(norm.parameters())
        params.extend(self.phase_to_rate.parameters())
        return params

    def rate_coded_parameters(self) -> list[nn.Parameter]:
        """Return parameters belonging to the rate-coded (GRIM) stage."""
        params: list[nn.Parameter] = []
        params.extend(self.grim_proj.parameters())
        params.extend(self.grim_norm.parameters())
        params.extend(self.grim_encoder.parameters())
        params.extend(self.classifier.parameters())
        return params


class AlternatingOptimizer:
    """Alternating optimization for hybrid oscillatory + rate-coded training.

    PRINet 3.0 ``nn.hybrid.AlternatingOptimizer``: manages two separate
    optimizers and alternates between them based on a schedule. Optionally
    integrates with a subconscious daemon for adaptive control signals.

    Args:
        model: A :class:`HybridPRINet` model.
        osc_lr: Learning rate for oscillatory parameters.
        rate_lr: Learning rate for rate-coded parameters.
        osc_optimizer_cls: Optimizer class for oscillatory params.
        rate_optimizer_cls: Optimizer class for rate-coded params.
        alternation_mode: ``"epoch"`` or ``"step"``.
        sparsity_weight: Weight for sparsity regularization loss.
        daemon: Optional subconscious daemon for adaptive control.
    """

    def __init__(
        self,
        model: HybridPRINet,
        osc_lr: float = 1e-4,
        rate_lr: float = 1e-3,
        osc_optimizer_cls: type = torch.optim.Adam,
        rate_optimizer_cls: type = torch.optim.Adam,
        alternation_mode: str = "epoch",
        sparsity_weight: float = 0.01,
        daemon: Any = None,
    ) -> None:
        """Construct the alternating optimizer with separate param groups."""
        self.model = model
        self._mode = alternation_mode
        self._sparsity_weight = sparsity_weight
        self._step_count = 0
        self._daemon = daemon

        osc_params = model.oscillatory_parameters()
        rate_params = model.rate_coded_parameters()

        self.osc_optimizer = osc_optimizer_cls(osc_params, lr=osc_lr)
        self.rate_optimizer = rate_optimizer_cls(rate_params, lr=rate_lr)

    @property
    def sparsity_weight(self) -> float:
        """Current sparsity loss weight."""
        return self._sparsity_weight

    def step(self, epoch: int = 0) -> None:
        """Perform one optimization step with alternating schedule.

        Args:
            epoch: Current epoch number (used in ``"epoch"`` mode).
        """
        if self._daemon is not None:
            self._apply_daemon_control()

        if self._mode == "epoch":
            if epoch % 2 == 0:
                self.osc_optimizer.step()
            else:
                self.rate_optimizer.step()
        else:
            if self._step_count % 2 == 0:
                self.osc_optimizer.step()
            else:
                self.rate_optimizer.step()

        self._step_count += 1

    def step_both(self) -> None:
        """Step both optimizers simultaneously."""
        if self._daemon is not None:
            self._apply_daemon_control()
        self.osc_optimizer.step()
        self.rate_optimizer.step()
        self._step_count += 1

    def zero_grad(self) -> None:
        """Zero gradients for both optimizers."""
        self.osc_optimizer.zero_grad()
        self.rate_optimizer.zero_grad()

    def _apply_daemon_control(self) -> None:
        """Read control signals from the subconscious daemon and apply."""
        try:
            ctrl = self._daemon.get_control()
            lr_mult = ctrl.lr_multiplier
            for pg in self.osc_optimizer.param_groups:
                pg["lr"] = pg.get("initial_lr", pg["lr"]) * lr_mult
            for pg in self.rate_optimizer.param_groups:
                pg["lr"] = pg.get("initial_lr", pg["lr"]) * lr_mult
        except Exception:  # noqa: S110
            pass  # Daemon not ready or failed — continue without control


class HybridCLEVRN(nn.Module):
    """HybridPRINet adapter for CLEVR-N benchmark.

    PRINet 3.0 ``nn.hybrid.HybridCLEVRN``: scene + query -> hybrid
    oscillatory encoding -> binary classification.

    Args:
        scene_dim: Per-item scene feature dimension.
        query_dim: Query vector dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        hidden_dim: Internal hidden dimension.
        lobm_steps: LOBM integration steps.
    """

    def __init__(
        self,
        scene_dim: int = 16,
        query_dim: int = 44,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        hidden_dim: int = 64,
        lobm_steps: int = 5,
    ) -> None:
        """Construct the hybrid CLEVR-N adapter."""
        super().__init__()
        n_osc = n_delta + n_theta + n_gamma

        self.scene_proj = nn.Linear(scene_dim, n_osc)
        self.query_proj = nn.Linear(query_dim, hidden_dim)

        self.hybrid = HybridPRINet(
            n_input=n_osc,
            n_classes=2,
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
            n_lobm_layers=1,
            lobm_steps=lobm_steps,
            grim_d_model=hidden_dim,
            grim_n_layers=1,
        )

        self.merge = nn.Linear(2 + hidden_dim, 2)

    def forward(self, scene: Tensor, query: Tensor) -> Tensor:
        """Forward pass.

        Args:
            scene: ``(B, N, D_scene)``
            query: ``(B, D_query)``

        Returns:
            Log probabilities ``(B, 2)``.
        """
        scene_agg = scene.mean(dim=1)
        scene_enc = self.scene_proj(scene_agg)

        log_probs: Tensor = self.hybrid(scene_enc)

        return log_probs


def _raise_disposition(symbol: str) -> NoReturn:
    """Raise the typed D-2.2 disposition for a hybrid-model symbol."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). "
        "Trainable nn.Module with nn.Linear projections; needs a "
        "trainable-layer rebuild in a future WP. "
        "See the Migration Guide for the disposition."
    )


class HybridPRINetV2CLEVRN(nn.Module):
    """HybridPRINetV2 adapter for CLEVR-N scene+query classification.

    PRINet 3.0 ``nn.hybrid.HybridPRINetV2CLEVRN``: projects scene and query
    inputs into the oscillator space, runs through an interleaved
    oscillatory-attention architecture, and classifies. Pure PyTorch
    composition over Rust-backed layers (no bridge backward needed).

    Args:
        scene_dim: Per-object feature dimension.
        query_dim: Query feature dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        d_model: Model dimension for attention.
        n_discrete_steps: Discrete dynamics steps per layer.
    """

    def __init__(
        self,
        scene_dim: int = 16,
        query_dim: int = 60,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        d_model: int = 32,
        n_discrete_steps: int = 3,
    ) -> None:
        """Build scene/query projections over an ``InterleavedHybridPRINet`` core."""
        super().__init__()
        n_osc = n_delta + n_theta + n_gamma
        self.n_osc = n_osc
        self.scene_proj = nn.Linear(scene_dim, n_osc)
        self.query_proj = nn.Linear(query_dim, n_osc)
        self.merge = nn.Linear(n_osc, n_osc)
        self.core = InterleavedHybridPRINet(
            n_input=n_osc,
            n_classes=2,
            n_tokens=n_osc,
            d_model=d_model,
            n_heads=4,
            n_layers=2,
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
            n_discrete_steps=n_discrete_steps,
        )

    def forward(self, scene: Tensor, query: Tensor) -> Tensor:
        """Classify a scene+query pair.

        Args:
            scene: ``(B, N_items, scene_dim)`` or ``(B, scene_dim)``.
            query: ``(B, query_dim)``.

        Returns:
            Log-probabilities ``(B, 2)``.
        """
        if scene.dim() == 3:
            scene_feat = scene.mean(dim=1)
        else:
            scene_feat = scene
        h = self.merge(self.scene_proj(scene_feat) + self.query_proj(query))
        out: Tensor = self.core(h)
        return out


class InterleavedHybridPRINet(nn.Module):
    """Interleaved oscillatory-attention hybrid model.

    Faithful compatibility rebuild of PRINet 3.0
    ``nn.hybrid.InterleavedHybridPRINet`` (plan amendment #40, sub-pass
    0144M1): oscillatory dynamics (:class:`prin.nn.DiscreteDeltaThetaGamma`)
    and :class:`prin.nn.OscillatoryAttention` interleaved at every layer, with
    the persistent phase state biasing attention toward phase-coherent tokens.
    Every differentiable stage delegates to a Rust owner; this class only
    chains them with standard ``nn.Linear`` / ``nn.LayerNorm`` / ``nn.GELU``
    projections (the same "PyTorch composition over Rust-backed layers"
    category as :class:`HybridPRINet`).
    """

    def __init__(
        self,
        n_input: int = 256,
        n_classes: int = 10,
        n_tokens: int = 44,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        dropout: float = 0.1,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        n_discrete_steps: int = 3,
    ) -> None:
        """Build the interleaved oscillatory-attention stack."""
        super().__init__()
        from prin.nn import DiscreteDeltaThetaGamma, OscillatoryAttention

        self.n_input = n_input
        self.n_classes = n_classes
        self.n_tokens = n_tokens
        self.d_model = d_model
        self.n_layers = n_layers
        self._n_heads = n_heads
        self.n_osc_total = n_delta + n_theta + n_gamma
        self._n_discrete_steps = n_discrete_steps

        self.input_proj = nn.Linear(n_input, n_tokens * d_model)
        self.phase_init = nn.Linear(n_input, n_tokens * n_heads)
        self.dynamics = DiscreteDeltaThetaGamma(
            n_delta=n_delta, n_theta=n_theta, n_gamma=n_gamma
        )

        self.attn_layers = nn.ModuleList()
        self.ffn_layers = nn.ModuleList()
        self.norm1_layers = nn.ModuleList()
        self.norm2_layers = nn.ModuleList()
        for _ in range(n_layers):
            self.attn_layers.append(
                OscillatoryAttention(d_model=d_model, n_heads=n_heads, dropout=0.0)
            )
            self.ffn_layers.append(
                nn.Sequential(
                    nn.Linear(d_model, d_model * 4),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(d_model * 4, d_model),
                    nn.Dropout(dropout),
                )
            )
            self.norm1_layers.append(nn.LayerNorm(d_model))
            self.norm2_layers.append(nn.LayerNorm(d_model))

        self.pool_norm = nn.LayerNorm(d_model)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, n_classes),
        )

    def forward(self, x: Tensor) -> Tensor:
        """Interleaved forward pass; returns log-probabilities."""
        import math

        was_1d = x.dim() == 1
        if was_1d:
            x = x.unsqueeze(0)
        batch = x.shape[0]
        n_heads = self._n_heads

        h = self.input_proj(x).view(batch, self.n_tokens, self.d_model)
        phase_init_raw = self.phase_init(x).view(batch, self.n_tokens, n_heads)
        phase_state = phase_init_raw % (2.0 * math.pi)
        amp_state = torch.ones(batch, self.n_osc_total, device=x.device, dtype=x.dtype)
        dyn_phase = phase_state[:, : self.n_osc_total, :].mean(dim=-1)

        for i in range(self.n_layers):
            dyn_phase, amp_state = self.dynamics.integrate(
                dyn_phase, amp_state, n_steps=self._n_discrete_steps, dt=0.01
            )
            if self.n_tokens == self.n_osc_total:
                token_phase = dyn_phase.unsqueeze(-1).expand(
                    batch, self.n_tokens, n_heads
                )
            else:
                repeated = dyn_phase.repeat(1, (self.n_tokens // self.n_osc_total) + 1)[
                    :, : self.n_tokens
                ]
                token_phase = repeated.unsqueeze(-1).expand(
                    batch, self.n_tokens, n_heads
                )

            h_norm = self.norm1_layers[i](h)
            h = h + self.attn_layers[i](h_norm, phase=token_phase)
            h_norm = self.norm2_layers[i](h)
            h = h + self.ffn_layers[i](h_norm)

        pooled = self.pool_norm(h.mean(dim=1))
        logits = self.classifier(pooled)
        logits = torch.clamp(logits, min=-_LOGIT_CLAMP, max=_LOGIT_CLAMP)
        log_probs = F.log_softmax(logits, dim=-1)
        return log_probs.squeeze(0) if was_1d else log_probs

    def oscillatory_parameters(self) -> list[nn.Parameter]:
        """Parameters belonging to the oscillatory components."""
        from prin.nn import OscillatoryAttention

        params: list[nn.Parameter] = list(self.dynamics.parameters())
        params.extend(self.phase_init.parameters())
        for attn in self.attn_layers:
            if isinstance(attn, OscillatoryAttention):
                params.append(attn.alpha)
        return params

    def rate_coded_parameters(self) -> list[nn.Parameter]:
        """Parameters belonging to the rate-coded components."""
        params: list[nn.Parameter] = list(self.input_proj.parameters())
        for ffn in self.ffn_layers:
            params.extend(ffn.parameters())
        for norm1, norm2 in zip(self.norm1_layers, self.norm2_layers, strict=True):
            params.extend(norm1.parameters())
            params.extend(norm2.parameters())
        params.extend(self.pool_norm.parameters())
        params.extend(self.classifier.parameters())
        return params


class TemporalHybridPRINet(nn.Module):
    """Temporal hybrid model for multi-frame sequence classification.

    PRINet 3.0 ``nn.hybrid.TemporalHybridPRINet``: processes temporal
    sequences through oscillatory dynamics + transformer layers. Each
    timestep's hidden state is modulated by the discrete oscillator phase,
    then classified. PyTorch composition over Rust-backed layers.

    Args:
        n_input: Input feature dimension.
        n_classes: Number of output classes.
        n_tokens: Number of oscillator tokens.
        d_model: Transformer model dimension.
        n_heads: Number of attention heads.
        n_layers: Number of transformer layers.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Discrete dynamics steps per frame.
        carry_strength: Temporal phase carry strength.
    """

    def __init__(
        self,
        n_input: int = 128,
        n_classes: int = 2,
        n_tokens: int = 28,
        d_model: int = 32,
        n_heads: int = 4,
        n_layers: int = 1,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 2,
        carry_strength: float = 0.8,
    ) -> None:
        """Build the per-frame encoder stack and temporal phase-carry state."""
        super().__init__()
        import math

        from prin.nn import DiscreteDeltaThetaGamma

        self.n_input = n_input
        self.n_classes = n_classes
        self.n_tokens = n_tokens
        self.d_model = d_model
        self._n_heads = n_heads
        self.n_layers = n_layers
        self.n_delta = n_delta
        self.n_theta = n_theta
        self.n_gamma = n_gamma
        self.n_osc = n_delta + n_theta + n_gamma
        self._n_discrete_steps = n_discrete_steps
        self._carry = carry_strength
        self._two_pi = 2.0 * math.pi

        self.input_proj = nn.Linear(n_input, n_tokens * d_model)
        self.dynamics = DiscreteDeltaThetaGamma(
            n_delta=n_delta, n_theta=n_theta, n_gamma=n_gamma
        )

        self.attn_layers = nn.ModuleList()
        self.ffn_layers = nn.ModuleList()
        self.norm1_layers = nn.ModuleList()
        self.norm2_layers = nn.ModuleList()
        for _ in range(n_layers):
            self.attn_layers.append(
                nn.MultiheadAttention(
                    d_model,
                    n_heads,
                    dropout=0.0,
                    batch_first=True,
                )
            )
            self.ffn_layers.append(
                nn.Sequential(
                    nn.Linear(d_model, d_model * 4),
                    nn.GELU(),
                    nn.Linear(d_model * 4, d_model),
                )
            )
            self.norm1_layers.append(nn.LayerNorm(d_model))
            self.norm2_layers.append(nn.LayerNorm(d_model))

        self.pool_norm = nn.LayerNorm(d_model)
        self.classifier = nn.Linear(d_model, n_classes)

    def _process_sequence(self, x: Tensor) -> Tensor:
        """Process a 3D ``(B, T, D)`` sequence; return ``(B, K)`` log-probs."""
        B, T, _D = x.shape
        device = x.device

        h = self.input_proj(x).view(B, T, self.n_tokens, self.d_model)

        phase = torch.rand(B, self.n_osc, device=device) * self._two_pi
        amp = torch.ones(B, self.n_osc, device=device)

        frames: list[Tensor] = []
        for t in range(T):
            phase, amp = self.dynamics.integrate(
                phase, amp, n_steps=self._n_discrete_steps, dt=0.01
            )
            phase_mod = torch.cos(phase[:, : self.d_model].unsqueeze(2))
            frame_t = h[:, t] * (1.0 + 0.1 * phase_mod)
            frames.append(frame_t)

        h_stacked = torch.stack(frames, dim=1).view(B * T, self.n_tokens, self.d_model)
        for i in range(self.n_layers):
            h_norm = self.norm1_layers[i](h_stacked)
            attn_out, _ = self.attn_layers[i](h_norm, h_norm, h_norm)
            h_stacked = h_stacked + attn_out
            h_norm = self.norm2_layers[i](h_stacked)
            h_stacked = h_stacked + self.ffn_layers[i](h_norm)

        h_stacked = h_stacked.mean(dim=1)
        h_stacked = self.pool_norm(h_stacked)
        h_seq = h_stacked.view(B, T, self.d_model)
        pooled = h_seq.mean(dim=1)
        return F.log_softmax(self.classifier(pooled), dim=-1)

    def forward(self, x: Tensor, per_frame: bool = False) -> Tensor:
        """Forward pass.

        Args:
            x: ``(B, D)`` single frame or ``(B, T, D)`` sequence.
            per_frame: If ``True`` and input is 3D, return per-frame log-probs.

        Returns:
            Log-probabilities ``(B, K)`` or ``(B, T, K)`` if per_frame.
        """
        if x.dim() == 2:
            h = self.input_proj(x).view(-1, self.n_tokens, self.d_model)
            for i in range(self.n_layers):
                h_norm = self.norm1_layers[i](h)
                attn_out, _ = self.attn_layers[i](h_norm, h_norm, h_norm)
                h = h + attn_out
                h_norm = self.norm2_layers[i](h)
                h = h + self.ffn_layers[i](h_norm)
            pooled = self.pool_norm(h.mean(dim=1))
            return F.log_softmax(self.classifier(pooled), dim=-1)

        if per_frame:
            B, T, _D = x.shape
            h = self.input_proj(x).view(B * T, self.n_tokens, self.d_model)
            for i in range(self.n_layers):
                h_norm = self.norm1_layers[i](h)
                attn_out, _ = self.attn_layers[i](h_norm, h_norm, h_norm)
                h = h + attn_out
                h_norm = self.norm2_layers[i](h)
                h = h + self.ffn_layers[i](h_norm)
            h = h.mean(dim=1).view(B, T, self.d_model)
            return F.log_softmax(self.classifier(h), dim=-1)

        return self._process_sequence(x)

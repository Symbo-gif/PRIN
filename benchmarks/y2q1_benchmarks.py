"""Year 2 Quarter 1 — Integration Bottleneck Benchmarks.

Provides CLEVR-N model wrappers used by acceptance tests:

- ``DiscreteDTGCLEVRN``: CLEVR-N model using ``DiscreteDeltaThetaGammaLayer``.
- ``InterleavedCLEVRN``: CLEVR-N model using ``InterleavedHybridPRINet``.

Both take ``(scene_dim, query_dim)`` constructor args and accept
``model(scenes, queries)`` returning ``log_softmax`` output ``(B, 2)``.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from prin.nn import DiscreteDeltaThetaGammaLayer, InterleavedHybridPRINet
from torch import Tensor


class DiscreteDTGCLEVRN(nn.Module):
    """CLEVR-N model using DiscreteDeltaThetaGammaLayer for binding.

    Mean-pools scene features, concatenates with query, projects to
    oscillator dimension, runs through the discrete DTG layer, then
    classifies.

    Args:
        scene_dim: Per-item scene feature dimension.
        query_dim: Query vector dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        hidden_dim: Classifier hidden dimension.
        n_steps: Discrete integration steps.
    """

    def __init__(
        self,
        scene_dim: int = 16,
        query_dim: int = 44,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        hidden_dim: int = 64,
        n_steps: int = 10,
    ) -> None:
        super().__init__()
        n_total = n_delta + n_theta + n_gamma
        self.scene_proj = nn.Linear(scene_dim, n_total)
        self.discrete_layer = DiscreteDeltaThetaGammaLayer(
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
            n_dims=n_total,
            n_steps=n_steps,
            dt=0.01,
        )
        self.layer_norm = nn.LayerNorm(n_total)
        self.query_proj = nn.Linear(query_dim, hidden_dim)
        self.classifier = nn.Sequential(
            nn.Linear(n_total + hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 2),
        )

    def forward(self, scene: Tensor, query: Tensor) -> Tensor:
        """Forward pass.

        Args:
            scene: ``(B, N, D_scene)``
            query: ``(B, D_query)``

        Returns:
            Log-probabilities ``(B, 2)``.
        """
        h = scene.mean(dim=1)  # (B, scene_dim)
        h = self.scene_proj(h)  # (B, n_total)
        h = self.discrete_layer(h)
        h = self.layer_norm(h)
        q = self.query_proj(query)
        combined = torch.cat([h, q], dim=-1)
        logits = self.classifier(combined)
        return F.log_softmax(logits, dim=-1)


class InterleavedCLEVRN(nn.Module):
    """CLEVR-N model wrapping InterleavedHybridPRINet.

    Flattens scene + query into a single input vector, passes through
    the interleaved oscillatory-attention architecture.

    Args:
        scene_dim: Per-item scene feature dimension.
        query_dim: Query vector dimension.
        n_items: Maximum number of scene items.
        d_model: Inner model dimension.
        n_heads: Attention heads.
        n_layers: Number of interleaved blocks.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
    """

    def __init__(
        self,
        scene_dim: int = 16,
        query_dim: int = 44,
        n_items: int = 6,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
    ) -> None:
        super().__init__()
        input_dim = scene_dim * n_items + query_dim
        n_osc_total = n_delta + n_theta + n_gamma
        n_tokens = n_osc_total
        self.model = InterleavedHybridPRINet(
            n_input=input_dim,
            n_classes=2,
            n_tokens=n_tokens,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            dropout=0.1,
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
            n_discrete_steps=3,
        )
        self._scene_dim = scene_dim
        self._n_items = n_items

    def forward(self, scene: Tensor, query: Tensor) -> Tensor:
        """Forward pass.

        Args:
            scene: ``(B, N, D_scene)``
            query: ``(B, D_query)``

        Returns:
            Log-probabilities ``(B, 2)``.
        """
        B = scene.shape[0]
        N = scene.shape[1]
        if N < self._n_items:
            pad = torch.zeros(
                B,
                self._n_items - N,
                scene.shape[2],
                device=scene.device,
                dtype=scene.dtype,
            )
            scene = torch.cat([scene, pad], dim=1)
        elif N > self._n_items:
            scene = scene[:, : self._n_items, :]

        flat_scene = scene.reshape(B, -1)
        x = torch.cat([flat_scene, query], dim=-1)
        return self.model(x)

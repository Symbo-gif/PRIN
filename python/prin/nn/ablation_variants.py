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
    "PhaseTrackerFrozen",
    "PhaseTrackerStatic",
    "SlotAttentionFrozen",
    "SlotAttentionNoGRU",
    "create_ablation_model",
    "create_ablation_tracker",
]

# ``PhaseTracker{Frozen,Static}`` / ``SlotAttention{NoGRU,Frozen}`` are faithful
# ports of the PRINet 3.0 ``nn.ablation_variants`` classes; their per-method
# docstrings mirror the reference (Testing Standards §1.1).


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


class PhaseTrackerStatic(nn.Module):
    """PhaseTracker with no coupling (independent oscillators).

    Replaces the DiscreteDeltaThetaGamma dynamics with a simple
    phase advance using fixed frequencies — no Kuramoto coupling.
    """

    _EPS = 1e-6

    def __init__(
        self,
        detection_dim: int = 4,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
    ) -> None:
        """Build the encoders and the fixed per-band frequency buffer."""
        super().__init__()
        self.n_osc = n_delta + n_theta + n_gamma
        self._n_discrete_steps = n_discrete_steps
        self.match_threshold = match_threshold

        self.det_to_phase = nn.Sequential(
            nn.Linear(detection_dim, 64),
            nn.ReLU(),
            nn.Linear(64, self.n_osc),
        )
        self.det_to_amp = nn.Sequential(
            nn.Linear(detection_dim, 64),
            nn.ReLU(),
            nn.Linear(64, self.n_osc),
            nn.Softplus(),
        )

        freqs: list[float] = []
        freqs.extend([2.0] * n_delta)
        freqs.extend([6.0] * n_theta)
        freqs.extend([40.0] * n_gamma)
        self.register_buffer("frequencies", torch.tensor(freqs))

    def encode(self, detections: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode detections into ``(phase, amplitude)`` embeddings."""
        phase_raw = self.det_to_phase(detections)
        phase = phase_raw % (2.0 * math.pi)
        amp = self.det_to_amp(detections)
        return phase, amp

    def evolve(
        self, phase: torch.Tensor, amplitude: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance the phase by fixed-frequency rotation (no coupling)."""
        dt = 0.01
        freqs = self.frequencies
        for _ in range(self._n_discrete_steps):
            phase = phase + 2.0 * math.pi * freqs * dt  # type: ignore[operator]
            phase = phase % (2.0 * math.pi)
        return phase, amplitude

    def phase_similarity(
        self, phase_a: torch.Tensor, phase_b: torch.Tensor
    ) -> torch.Tensor:
        """Cosine similarity of the complex phase embeddings."""
        z_a = torch.exp(1j * phase_a.to(torch.complex64))
        z_b = torch.exp(1j * phase_b.to(torch.complex64))
        z_a_norm = z_a / (z_a.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + self._EPS)
        z_b_norm = z_b / (z_b.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + self._EPS)
        sim = (
            (z_a_norm.unsqueeze(1) * z_b_norm.conj().unsqueeze(0))
            .sum(dim=-1)
            .real.float()
        )
        return sim

    def forward(
        self,
        detections_t: torch.Tensor,
        detections_t1: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Match detections across two consecutive frames."""
        phase_t, amp_t = self.encode(detections_t)
        phase_t1, _amp_t1 = self.encode(detections_t1)
        phase_t_evolved, _ = self.evolve(phase_t, amp_t)
        sim = self.phase_similarity(phase_t_evolved, phase_t1)
        N_t = detections_t.shape[0]
        matches = torch.full((N_t,), -1, dtype=torch.long, device=detections_t.device)
        used = torch.zeros(
            detections_t1.shape[0],
            dtype=torch.bool,
            device=detections_t.device,
        )
        max_sims, max_idxs = sim.max(dim=1)
        order = max_sims.argsort(descending=True)
        for idx in order:
            best_j = int(max_idxs[idx].item())
            if not used[best_j] and max_sims[idx] > self.match_threshold:
                matches[idx] = best_j
                used[best_j] = True
        return matches, sim

    def track_sequence(self, frame_detections: list[torch.Tensor]) -> dict[str, Any]:
        """Track via independent phase evolution (no coupling)."""
        T = len(frame_detections)
        phase_history: list[torch.Tensor] = []
        identity_matches: list[torch.Tensor] = []
        per_frame_sim: list[float] = []
        total_matches = 0
        total_possible = 0

        with torch.no_grad():
            for t in range(T):
                dets = frame_detections[t]
                phase_t, _amp_t = self.encode(dets)
                if t == 0:
                    phase_history.append(phase_t.detach().cpu())
                    continue
                prev_phase = phase_history[-1].to(dets.device)
                prev_amp = torch.ones_like(prev_phase)
                evolved_phase, _ = self.evolve(prev_phase, prev_amp)
                sim = self.phase_similarity(evolved_phase, phase_t)
                N_prev = evolved_phase.shape[0]
                N_curr = phase_t.shape[0]
                N_match = min(N_prev, N_curr)
                matches = torch.full(
                    (N_prev,),
                    -1,
                    dtype=torch.long,
                    device=dets.device,
                )
                used = torch.zeros(N_curr, dtype=torch.bool, device=dets.device)
                max_sims, max_idxs = sim.max(dim=1)
                order = max_sims.argsort(descending=True)
                for idx in order:
                    best_j = int(max_idxs[idx].item())
                    if (
                        best_j < N_curr
                        and not used[best_j]
                        and max_sims[idx] > self.match_threshold
                    ):
                        matches[idx] = best_j
                        used[best_j] = True
                n_matched = int((matches >= 0).sum().item())
                identity_matches.append(matches.cpu())
                per_frame_sim.append(float(max_sims.mean().item()))
                total_matches += n_matched
                total_possible += N_match
                phase_history.append(phase_t.detach().cpu())

        preservation = total_matches / max(total_possible, 1)
        return {
            "phase_history": phase_history,
            "identity_matches": identity_matches,
            "identity_preservation": preservation,
            "per_frame_similarity": per_frame_sim,
            "per_frame_phase_correlation": [],
        }


class PhaseTrackerFrozen(nn.Module):
    """PhaseTracker with frozen Kuramoto coupling weights (PT-frozen).

    Wraps a :class:`prin.nn.temporal_compat.PhaseTracker` whose
    :class:`~prin.nn.DiscreteDeltaThetaGamma` dynamics parameters are frozen
    (``requires_grad=False``); the detection encoder stays trainable. Tests
    whether training helps PT exploit oscillatory dynamics or if the untrained
    dynamics already provide sufficient structure.
    """

    def __init__(
        self,
        detection_dim: int = 4,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
    ) -> None:
        """Wrap a PhaseTracker and freeze its Rust-backed dynamics parameters."""
        super().__init__()
        from prin.nn.temporal_compat import PhaseTracker

        self._inner = PhaseTracker(
            detection_dim=detection_dim,
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
            n_discrete_steps=n_discrete_steps,
            match_threshold=match_threshold,
        )
        for p in self._inner.dynamics.parameters():
            p.requires_grad = False

    @property
    def n_osc(self) -> int:
        """Total oscillator count."""
        return self._inner.n_osc

    @property
    def match_threshold(self) -> float:
        """Minimum phase similarity for a valid match."""
        return self._inner.match_threshold

    def encode(self, detections: Tensor) -> tuple[Tensor, Tensor]:
        """See :meth:`prin.nn.temporal_compat.PhaseTracker.encode`."""
        return self._inner.encode(detections)

    def evolve(self, phase: Tensor, amplitude: Tensor) -> tuple[Tensor, Tensor]:
        """See :meth:`prin.nn.temporal_compat.PhaseTracker.evolve`."""
        return self._inner.evolve(phase, amplitude)

    def phase_similarity(self, phase_a: Tensor, phase_b: Tensor) -> Tensor:
        """See :meth:`prin.nn.temporal_compat.PhaseTracker.phase_similarity`."""
        return self._inner.phase_similarity(phase_a, phase_b)

    def forward(
        self, detections_t: Tensor, detections_t1: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Delegate to the wrapped tracker's ``forward``."""
        result: tuple[Tensor, Tensor] = self._inner(detections_t, detections_t1)
        return result

    def track_sequence(self, frame_detections: list[Tensor]) -> dict[str, Any]:
        """Delegate to the wrapped tracker's ``track_sequence``."""
        return self._inner.track_sequence(frame_detections)


class SlotAttentionNoGRU(nn.Module):
    """TemporalSlotAttentionMOT without GRU carry-over (SA-no-GRU).

    Slots re-initialise from scratch every frame. Tests whether temporal
    recurrence is necessary for identity preservation.
    """

    def __init__(
        self,
        detection_dim: int = 4,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
    ) -> None:
        """Build a per-frame Slot Attention tracker with no GRU recurrence."""
        super().__init__()
        from prin.nn.temporal_compat import SlotAttentionModule

        self.num_slots = num_slots
        self.slot_dim = slot_dim
        self.match_threshold = match_threshold

        self.det_encoder = nn.Sequential(
            nn.Linear(detection_dim, slot_dim),
            nn.ReLU(inplace=True),
            nn.Linear(slot_dim, slot_dim),
        )
        self.slot_attention = SlotAttentionModule(
            num_slots=num_slots,
            slot_dim=slot_dim,
            input_dim=slot_dim,
            num_iterations=num_iterations,
        )
        # NO temporal_gru, NO temporal_norm

    def process_frame(
        self, detections: Tensor, prev_slots: Tensor | None = None
    ) -> Tensor:
        """Process a frame without temporal carry-over (``prev_slots`` ignored)."""
        if detections.dim() == 2:
            detections = detections.unsqueeze(0)
        features = self.det_encoder(detections)
        new_slots: Tensor = self.slot_attention(features)
        return new_slots

    def slot_similarity(self, slots_a: Tensor, slots_b: Tensor) -> Tensor:
        """Cosine similarity ``(K, K)`` between two slot sets."""
        if slots_a.dim() == 3:
            slots_a = slots_a.squeeze(0)
        if slots_b.dim() == 3:
            slots_b = slots_b.squeeze(0)
        a_norm = F.normalize(slots_a, dim=-1)
        b_norm = F.normalize(slots_b, dim=-1)
        return a_norm @ b_norm.T

    def track_sequence(self, frame_detections: list[Tensor]) -> dict[str, Any]:
        """Track objects across a sequence of frames. **Non-differentiable**."""
        T = len(frame_detections)
        slot_history: list[Tensor] = []
        identity_matches: list[Tensor] = []
        per_frame_sim: list[float] = []
        total_matches = 0
        total_possible = 0

        with torch.no_grad():
            prev_slots = None
            for t in range(T):
                dets = frame_detections[t]
                slots = self.process_frame(dets, None)
                slot_history.append(slots.detach().cpu())

                if prev_slots is not None:
                    sim = self.slot_similarity(prev_slots, slots)
                    K = self.num_slots
                    matches = torch.full((K,), -1, dtype=torch.long)
                    used = torch.zeros(K, dtype=torch.bool)
                    max_sims, max_idxs = sim.max(dim=1)
                    order = max_sims.argsort(descending=True)
                    for idx in order:
                        j = int(max_idxs[idx].item())
                        if not used[j] and max_sims[idx] > self.match_threshold:
                            matches[idx] = j
                            used[j] = True
                    n_matched = int((matches >= 0).sum().item())
                    identity_matches.append(matches)
                    per_frame_sim.append(float(max_sims.mean().item()))
                    total_matches += n_matched
                    total_possible += K
                prev_slots = slots

        preservation = total_matches / max(total_possible, 1)
        return {
            "slot_history": slot_history,
            "identity_matches": identity_matches,
            "identity_preservation": preservation,
            "per_frame_similarity": per_frame_sim,
        }

    def forward(
        self, detections_t: Tensor, detections_t1: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Process two consecutive frames for training."""
        slots_t = self.process_frame(detections_t)
        slots_t1 = self.process_frame(detections_t1, None)
        sim = self.slot_similarity(slots_t, slots_t1)
        K = self.num_slots
        matches = torch.full((K,), -1, dtype=torch.long, device=detections_t.device)
        used = torch.zeros(K, dtype=torch.bool, device=detections_t.device)
        max_sims, max_idxs = sim.max(dim=1)
        order = max_sims.argsort(descending=True)
        for idx in order:
            j = int(max_idxs[idx].item())
            if not used[j] and max_sims[idx] > self.match_threshold:
                matches[idx] = j
                used[j] = True
        return matches, sim


class SlotAttentionFrozen(nn.Module):
    """TemporalSlotAttentionMOT with every parameter frozen (SA-frozen).

    The untrained SA baseline paired with :class:`PhaseTrackerFrozen`.
    """

    def __init__(
        self,
        detection_dim: int = 4,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
    ) -> None:
        """Wrap a TemporalSlotAttentionMOT and freeze every parameter."""
        super().__init__()
        from prin.nn.temporal_compat import TemporalSlotAttentionMOT

        self._inner = TemporalSlotAttentionMOT(
            detection_dim=detection_dim,
            num_slots=num_slots,
            slot_dim=slot_dim,
            num_iterations=num_iterations,
            match_threshold=match_threshold,
        )
        for p in self._inner.parameters():
            p.requires_grad = False

    @property
    def num_slots(self) -> int:
        """Number of object slots."""
        return self._inner.num_slots

    @property
    def slot_dim(self) -> int:
        """Slot dimensionality."""
        return self._inner.slot_dim

    @property
    def match_threshold(self) -> float:
        """Minimum similarity for a valid identity match."""
        return self._inner.match_threshold

    def process_frame(
        self, detections: Tensor, prev_slots: Tensor | None = None
    ) -> Tensor:
        """Delegate to the wrapped tracker's ``process_frame``."""
        return self._inner.process_frame(detections, prev_slots)

    def slot_similarity(self, slots_a: Tensor, slots_b: Tensor) -> Tensor:
        """Delegate to the wrapped tracker's ``slot_similarity``."""
        return self._inner.slot_similarity(slots_a, slots_b)

    def forward(
        self, detections_t: Tensor, detections_t1: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Process two consecutive frames."""
        prev_slots = self._inner.process_frame(detections_t)
        curr_slots = self._inner.process_frame(detections_t1, prev_slots)
        sim = self._inner.slot_similarity(prev_slots, curr_slots)
        K = self._inner.num_slots
        matches = torch.full((K,), -1, dtype=torch.long, device=detections_t.device)
        used = torch.zeros(K, dtype=torch.bool, device=detections_t.device)
        max_sims, max_idxs = sim.max(dim=1)
        order = max_sims.argsort(descending=True)
        for idx in order:
            j = int(max_idxs[idx].item())
            if not used[j] and max_sims[idx] > self.match_threshold:
                matches[idx] = j
                used[j] = True
        return matches, sim

    def track_sequence(self, frame_detections: list[Tensor]) -> dict[str, Any]:
        """Delegate to the wrapped tracker's ``track_sequence``."""
        return self._inner.track_sequence(frame_detections)


def create_ablation_tracker(
    variant: str,
    detection_dim: int = 4,
    **kwargs: Any,
) -> nn.Module:
    """Create an ablation tracker variant by name.

    Args:
        variant: One of ``"pt_full"``, ``"pt_frozen"``, ``"pt_static"``,
            ``"sa_full"``, ``"sa_no_gru"``, ``"sa_frozen"``.
        detection_dim: Per-detection dimension.
        **kwargs: Additional constructor kwargs.

    Returns:
        Tracker module.

    Raises:
        ValueError: If the variant is unknown.
    """
    if variant == "pt_full":
        from prin.nn.temporal_compat import PhaseTracker

        return PhaseTracker(detection_dim=detection_dim, **kwargs)
    if variant == "pt_frozen":
        return PhaseTrackerFrozen(detection_dim=detection_dim, **kwargs)
    if variant == "pt_static":
        return PhaseTrackerStatic(detection_dim=detection_dim, **kwargs)
    if variant == "sa_full":
        from prin.nn.temporal_compat import TemporalSlotAttentionMOT

        return TemporalSlotAttentionMOT(detection_dim=detection_dim, **kwargs)
    if variant == "sa_no_gru":
        return SlotAttentionNoGRU(detection_dim=detection_dim, **kwargs)
    if variant == "sa_frozen":
        return SlotAttentionFrozen(detection_dim=detection_dim, **kwargs)
    raise ValueError(
        f"Unknown variant: {variant!r}. "
        f"Choose from: pt_full, pt_frozen, pt_static, sa_full, sa_no_gru, sa_frozen"
    )

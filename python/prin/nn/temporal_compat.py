"""PRINet 3.0-compatible temporal trackers for the Q1.7/Q1.8 benchmarks.

Faithful ports (Testing Standards §1.1) of PRINet 3.0's
``nn.hybrid.PhaseTracker`` and ``nn.slot_attention.{SlotAttentionModule,
TemporalSlotAttentionMOT}`` as real :class:`torch.nn.Module` graphs so the
Year-4-Q1.7/Q1.8 acceptance suite's parameter-introspection
(:func:`prin.temporal_training.count_parameters`, gradient clipping over
``model.parameters()``), ``_inner`` ablation wrappers, differentiable
``forward(d0, d1) -> (matches, sim)``, and the
:class:`~prin.temporal_training.TemporalTrainer` loop all see the reference
module shape.

Numerics disposition (same category as :mod:`prin.nn.mot_evaluation` /
:mod:`prin.nn.ablation_variants` — benchmark/experiment tooling, excluded from
the ``check_no_python_numerics`` compat-surface scan):

- :class:`PhaseTracker`'s oscillatory core is the Rust-backed
  :class:`prin.nn.DiscreteDeltaThetaGamma` (``prin_train::bands``, WP-022) —
  ``evolve`` delegates every step to it. The detection encoders are stock
  ``nn.Linear`` MLPs and ``phase_similarity`` is a cosine-of-complex-embedding
  *similarity metric*, not oscillator dynamics.
- :class:`SlotAttentionModule` / :class:`TemporalSlotAttentionMOT` are the
  explicitly *non-oscillatory* Slot Attention comparison baseline (Locatello
  et al. 2020) — the same disposition as ``mot_evaluation``'s
  ``AttentionTracker``.
"""

from __future__ import annotations

import math
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from prin.nn import DiscreteDeltaThetaGamma

__all__ = [
    "PhaseTracker",
    "SlotAttentionModule",
    "TemporalSlotAttentionMOT",
]

_EPS = 1e-8


# =========================================================================
# PhaseTracker (oscillatory tracker; dynamics core in Rust)
# =========================================================================


class PhaseTracker(nn.Module):
    """Phase-based multi-object tracker for 2D MOT.

    Encodes each detection to an oscillator ``(phase, amplitude)`` state, runs
    the Rust-backed :class:`prin.nn.DiscreteDeltaThetaGamma` dynamics to
    encourage phase coherence, then associates detections across frames by
    phase-correlation similarity + greedy assignment.

    Args:
        detection_dim: Per-detection feature dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per frame.
        match_threshold: Minimum phase similarity for a valid match.
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
        """Build the detection encoders and the Rust-backed dynamics."""
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

        self.dynamics = DiscreteDeltaThetaGamma(
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
        )

    def encode(self, detections: Tensor) -> tuple[Tensor, Tensor]:
        """Encode detections into phase and amplitude embeddings ``(N, n_osc)``."""
        phase_raw = self.det_to_phase(detections)
        phase = phase_raw % (2.0 * math.pi)
        amp = self.det_to_amp(detections)
        return phase, amp

    def evolve(self, phase: Tensor, amplitude: Tensor) -> tuple[Tensor, Tensor]:
        """Evolve a phase state through the Rust-backed discrete dynamics."""
        return self.dynamics.integrate(
            phase,
            amplitude,
            n_steps=self._n_discrete_steps,
            dt=0.01,
        )

    def phase_similarity(self, phase_a: Tensor, phase_b: Tensor) -> Tensor:
        """Cosine similarity of complex phase embeddings ``exp(i*phase)``.

        ``sim[a, b] = mean_k cos(phase_a[a,k] - phase_b[b,k])``; values in
        ``[-1, 1]``.
        """
        z_a = torch.exp(1j * phase_a.to(torch.complex64))
        z_b = torch.exp(1j * phase_b.to(torch.complex64))
        z_a_norm = z_a / (z_a.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + _EPS)
        z_b_norm = z_b / (z_b.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + _EPS)
        sim = (
            (z_a_norm.unsqueeze(1) * z_b_norm.conj().unsqueeze(0))
            .sum(dim=-1)
            .real.float()
        )
        return sim

    def forward(
        self,
        detections_t: Tensor,
        detections_t1: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Match detections across two consecutive frames.

        Returns:
            ``(matches, similarity)`` where ``matches[i]`` is the index in
            ``detections_t1`` matched to detection ``i`` in ``detections_t``
            (``-1`` if unmatched) and ``similarity`` is the ``(N_t, N_t1)``
            matrix.
        """
        phase_t, amp_t = self.encode(detections_t)
        phase_t1, _amp_t1 = self.encode(detections_t1)
        phase_t_evolved, _ = self.evolve(phase_t, amp_t)
        sim = self.phase_similarity(phase_t_evolved, phase_t1)

        N_t = detections_t.shape[0]
        matches = torch.full((N_t,), -1, dtype=torch.long, device=detections_t.device)
        used = torch.zeros(
            detections_t1.shape[0], dtype=torch.bool, device=detections_t.device
        )
        max_sims, max_idxs = sim.max(dim=1)
        order = max_sims.argsort(descending=True)
        for idx in order:
            best_j = int(max_idxs[idx].item())
            if not used[best_j] and max_sims[idx] > self.match_threshold:
                matches[idx] = best_j
                used[best_j] = True
        return matches, sim

    def track_sequence(self, frame_detections: list[Tensor]) -> dict[str, Any]:
        """Track objects across a sequence of frames. **Non-differentiable**.

        Returns a dict compatible with
        :meth:`TemporalSlotAttentionMOT.track_sequence` plus oscillatory
        extras (``phase_history``, ``per_frame_phase_correlation``).
        """
        T = len(frame_detections)
        phase_history: list[Tensor] = []
        identity_matches: list[Tensor] = []
        per_frame_sim: list[float] = []
        per_frame_rho: list[float] = []

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
                    (N_prev,), -1, dtype=torch.long, device=dets.device
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

                if n_matched > 0:
                    matched_mask = matches >= 0
                    matched_prev = evolved_phase[matched_mask]
                    matched_curr = phase_t[matches[matched_mask]]
                    diff = matched_curr - matched_prev
                    rho = float(
                        torch.exp(1j * diff.to(torch.complex64))
                        .mean(dim=-1)
                        .abs()
                        .mean()
                        .item()
                    )
                else:
                    rho = 0.0
                per_frame_rho.append(rho)

                phase_history.append(phase_t.detach().cpu())

        preservation = total_matches / max(total_possible, 1)
        return {
            "phase_history": phase_history,
            "identity_matches": identity_matches,
            "identity_preservation": preservation,
            "per_frame_similarity": per_frame_sim,
            "per_frame_phase_correlation": per_frame_rho,
        }


# =========================================================================
# Slot Attention baseline (non-oscillatory comparison)
# =========================================================================


class SlotAttentionModule(nn.Module):
    """Slot Attention mechanism with iterative competitive binding.

    Locatello et al. (2020), NeurIPS. The non-oscillatory object-centric
    baseline for head-to-head comparison against :class:`PhaseTracker`.

    Args:
        num_slots: Number of slots (object representations).
        slot_dim: Dimensionality of each slot vector.
        input_dim: Dimensionality of input features.
        num_iterations: Iterative refinement steps.
        hidden_dim: Hidden dimension for the slot update MLP.
        eps: Small constant for numerical stability.
    """

    def __init__(
        self,
        num_slots: int,
        slot_dim: int,
        input_dim: int,
        num_iterations: int = 3,
        hidden_dim: int | None = None,
        eps: float = 1e-8,
    ) -> None:
        """Build the Slot Attention projection, GRU, and update MLP."""
        super().__init__()
        self.num_slots = num_slots
        self.slot_dim = slot_dim
        self.num_iterations = num_iterations
        self.eps = eps

        if hidden_dim is None:
            hidden_dim = max(slot_dim, 128)

        self.slot_mu = nn.Parameter(torch.randn(1, 1, slot_dim) * 0.02)
        self.slot_log_sigma = nn.Parameter(torch.zeros(1, 1, slot_dim))

        self.norm_inputs = nn.LayerNorm(input_dim)
        self.norm_slots = nn.LayerNorm(slot_dim)
        self.norm_mlp = nn.LayerNorm(slot_dim)

        self.project_k = nn.Linear(input_dim, slot_dim, bias=False)
        self.project_v = nn.Linear(input_dim, slot_dim, bias=False)
        self.project_q = nn.Linear(slot_dim, slot_dim, bias=False)

        self.gru = nn.GRUCell(slot_dim, slot_dim)

        self.mlp = nn.Sequential(
            nn.Linear(slot_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, slot_dim),
        )

        self._scale = slot_dim**-0.5

    def forward(self, inputs: Tensor) -> Tensor:
        """Run Slot Attention: ``(B, N, D_in)`` features to ``(B, K, D_slot)`` slots."""
        B, _n, _ = inputs.shape
        K = self.num_slots

        inputs = self.norm_inputs(inputs)
        k = self.project_k(inputs)
        v = self.project_v(inputs)

        mu = self.slot_mu.expand(B, K, -1)
        sigma = self.slot_log_sigma.exp().expand(B, K, -1)
        slots = mu + sigma * torch.randn_like(mu)

        for _ in range(self.num_iterations):
            slots_prev = slots
            slots = self.norm_slots(slots)
            q = self.project_q(slots)

            attn_logits = torch.einsum("bnd,bkd->bnk", k, q) * self._scale
            attn = F.softmax(attn_logits, dim=-1)

            attn_weights = attn / (attn.sum(dim=1, keepdim=True) + self.eps)
            updates = torch.einsum("bnk,bnd->bkd", attn_weights, v)

            slots = self.gru(
                updates.reshape(B * K, self.slot_dim),
                slots_prev.reshape(B * K, self.slot_dim),
            ).reshape(B, K, self.slot_dim)

            slots = slots + self.mlp(self.norm_mlp(slots))

        return slots


class TemporalSlotAttentionMOT(nn.Module):
    """Temporal Slot Attention for multi-frame object tracking.

    Slot Attention + GRU slot carry-over between frames. The direct
    non-oscillatory comparison baseline against :class:`PhaseTracker`.

    Args:
        detection_dim: Per-detection feature dimension.
        num_slots: Number of object slots (max tracked objects).
        slot_dim: Slot representation dimension.
        num_iterations: Slot Attention iterations per frame.
        match_threshold: Minimum similarity for a valid identity match.
    """

    def __init__(
        self,
        detection_dim: int = 4,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
    ) -> None:
        """Build the per-frame Slot Attention module for MOT tracking."""
        super().__init__()
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

        self.temporal_gru = nn.GRUCell(slot_dim, slot_dim)
        self.temporal_norm = nn.LayerNorm(slot_dim)

    def process_frame(
        self,
        detections: Tensor,
        prev_slots: Tensor | None = None,
    ) -> Tensor:
        """Process a single frame; carry ``prev_slots`` via GRU when supplied."""
        if detections.dim() == 2:
            detections = detections.unsqueeze(0)

        features = self.det_encoder(detections)
        new_slots = self.slot_attention(features)

        if prev_slots is not None:
            K = self.num_slots
            updated = self.temporal_gru(
                new_slots.reshape(-1, self.slot_dim),
                prev_slots.reshape(-1, self.slot_dim),
            ).reshape(1, K, self.slot_dim)
            new_slots = self.temporal_norm(updated)

        return new_slots  # type: ignore[no-any-return]

    def slot_similarity(self, slots_a: Tensor, slots_b: Tensor) -> Tensor:
        """Cosine similarity ``(K, K)`` between two slot sets."""
        if slots_a.dim() == 3:
            slots_a = slots_a.squeeze(0)
        if slots_b.dim() == 3:
            slots_b = slots_b.squeeze(0)
        a_norm = F.normalize(slots_a, dim=-1)
        b_norm = F.normalize(slots_b, dim=-1)
        return a_norm @ b_norm.T

    def forward(
        self,
        detections_t: Tensor,
        detections_t1: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Match detections across two frames (``PhaseTracker``-compatible)."""
        slots_t = self.process_frame(detections_t, prev_slots=None)
        slots_t1 = self.process_frame(detections_t1, prev_slots=slots_t)

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

    def track_sequence(self, frame_detections: list[Tensor]) -> dict[str, Any]:
        """Track objects across a sequence of frames. **Non-differentiable**."""
        T = len(frame_detections)
        slot_history: list[Tensor] = []
        identity_matches: list[Tensor] = []
        per_frame_sim: list[float] = []

        prev_slots: Tensor | None = None
        total_matches = 0
        total_possible = 0

        with torch.no_grad():
            for t in range(T):
                dets = frame_detections[t]
                slots = self.process_frame(dets, prev_slots)
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

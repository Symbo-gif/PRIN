"""Structural ablation variants isolating which components drive temporal binding.

See ``crates/prin-py/src/bindings/ablation.rs`` for the Rust bridge and
``crates/prin-train/src/ablation.rs`` for the numerical core.

- :class:`PhaseTrackerFrozen` / :class:`SlotAttentionFrozen` wrap an inner
  tracker; their :attr:`inner` property returns a fresh
  :class:`prin.nn.PhaseTracker` / :class:`prin.nn.TemporalSlotAttentionMOT`
  over the *same* underlying tracker for the differentiable
  `encode`/`evolve`/`phase_similarity` / `process_frame`/`slot_similarity`
  methods those types already implement.
- :class:`PhaseTrackerStatic` / :class:`SlotAttentionNoGRU` fully reimplement
  (do not wrap) their base type in Rust, so implement their own
  differentiable methods below, mirroring
  :class:`prin.nn.PhaseTracker`/:class:`prin.nn.TemporalSlotAttentionMOT`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import (
    PhaseTrackerFrozenBridge,
    PhaseTrackerStaticBridge,
    SlotAttentionFrozenBridge,
    SlotAttentionNoGRUBridge,
)

from ._bridge import apply_rust_bridge
from .phase_tracker import PhaseTracker, TrackingResult
from .slot_attention import TemporalSlotAttentionMOT

if TYPE_CHECKING:
    from prin._prin_core import Seed

__all__: list[str] = [
    "PhaseTrackerFrozen",
    "PhaseTrackerStatic",
    "SlotAttentionFrozen",
    "SlotAttentionNoGRU",
]


class PhaseTrackerFrozen(torch.nn.Module):
    """[`PhaseTracker`][prin.nn.PhaseTracker] with frozen dynamics (PT-frozen).

    Tests whether training the oscillatory dynamics matters, or whether
    their untrained structure already suffices. The detection encoder
    remains trainable.

    Args:
        detection_dim: Per-detection input feature dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per frame.
        match_threshold: Minimum phase similarity for a valid match.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.
    """

    def __init__(
        self,
        detection_dim: int,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct, freezing dynamics' gradients right after seeded init."""
        super().__init__()
        self._bridge = PhaseTrackerFrozenBridge(
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
            seed_counter,
            seed_key,
        )

    @property
    def inner(self) -> PhaseTracker:
        """A fresh :class:`PhaseTracker` over the wrapped tracker.

        Encoder trainable, dynamics frozen — use for `encode`/`evolve`/
        `phase_similarity`.
        """
        return PhaseTracker._from_bridge(self._bridge.inner)

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor
    ) -> tuple[list[int], torch.Tensor]:
        """See :meth:`prin.nn.PhaseTracker.match_frames`. Non-differentiable."""
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach()
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(self, frame_detections: list[torch.Tensor]) -> TrackingResult:
        """See :meth:`prin.nn.PhaseTracker.track_sequence`. Non-differentiable."""
        result = self._bridge.track_sequence([d.detach() for d in frame_detections])
        return TrackingResult._from_rust(result)

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`."""
        self._bridge.load_state_dict(state)


class PhaseTrackerStatic(torch.nn.Module):
    """PT-static: independent fixed-frequency phase advance, no Kuramoto coupling.

    Fully reimplements (does not wrap) [`PhaseTracker`][prin.nn.PhaseTracker]
    — see the module docs.

    Args: same as :class:`PhaseTrackerFrozen`.
    """

    def __init__(
        self,
        detection_dim: int,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded encoder params and fixed per-band frequencies.

        Frequencies: delta=2.0, theta=6.0, gamma=40.0 Hz.
        """
        super().__init__()
        self._bridge = PhaseTrackerStaticBridge(
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
            seed_counter,
            seed_key,
        )

    @property
    def n_osc(self) -> int:
        """Total oscillator count."""
        return self._bridge.n_osc

    def encode(self, detections: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """See :meth:`prin.nn.PhaseTracker.encode`."""
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.encode, [detections]
        )
        return result

    def evolve(
        self, phase: torch.Tensor, amplitude: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance `phase` by fixed per-band frequencies (no coupling).

        `amplitude` passes through unchanged.
        """
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.evolve, [phase, amplitude]
        )
        return result

    def phase_similarity(
        self, phase_a: torch.Tensor, phase_b: torch.Tensor
    ) -> torch.Tensor:
        """See :meth:`prin.nn.PhaseTracker.phase_similarity`."""
        result: torch.Tensor = apply_rust_bridge(
            self._bridge.phase_similarity, [phase_a, phase_b]
        )
        return result

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor
    ) -> tuple[list[int], torch.Tensor]:
        """Non-differentiable — see :meth:`prin.nn.PhaseTracker.match_frames`."""
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach()
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(self, frame_detections: list[torch.Tensor]) -> TrackingResult:
        """Non-differentiable. `per_frame_phase_correlation` is always empty.

        Matches the reference (see the Rust module's docs).
        """
        result = self._bridge.track_sequence([d.detach() for d in frame_detections])
        return TrackingResult._from_rust(result)

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`."""
        self._bridge.load_state_dict(state)


class SlotAttentionNoGRU(torch.nn.Module):
    """SA-no-GRU: :class:`TemporalSlotAttentionMOT` without temporal carry-over.

    Slots re-initialize from scratch every frame. Tests whether temporal
    recurrence is necessary for identity preservation.

    Args:
        detection_dim: Per-detection input feature dimension.
        num_slots: Number of object slots.
        slot_dim: Slot representation dimension.
        num_iterations: Slot Attention iterations per frame.
        match_threshold: Minimum similarity for a valid identity match.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.
    """

    def __init__(
        self,
        detection_dim: int,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters."""
        super().__init__()
        self._bridge = SlotAttentionNoGRUBridge(
            detection_dim,
            num_slots,
            slot_dim,
            num_iterations,
            match_threshold,
            seed_counter,
            seed_key,
        )

    def process_frame(self, detections: torch.Tensor, seed: Seed) -> torch.Tensor:
        """Process a frame, always ignoring any prior state (the ablated behavior).

        Fresh slots every call. `seed` is consumed (advanced).
        """
        result: torch.Tensor = apply_rust_bridge(
            lambda d: self._bridge.process_frame(d, seed), [detections]
        )
        return result

    def slot_similarity(
        self, slots_a: torch.Tensor, slots_b: torch.Tensor
    ) -> torch.Tensor:
        """See :meth:`prin.nn.TemporalSlotAttentionMOT.slot_similarity`."""
        result: torch.Tensor = apply_rust_bridge(
            self._bridge.slot_similarity, [slots_a, slots_b]
        )
        return result

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor, seed: Seed
    ) -> tuple[list[int], torch.Tensor]:
        """Non-differentiable. `seed` is consumed (advanced)."""
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach(), seed
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(
        self, frame_detections: list[torch.Tensor], seed: Seed
    ) -> tuple[list[torch.Tensor], list[list[int]], float, list[float]]:
        """Non-differentiable. `seed` is consumed (advanced)."""
        slot_history, identity_matches, identity_preservation, per_frame_similarity = (
            self._bridge.track_sequence([d.detach() for d in frame_detections], seed)
        )
        return (
            [from_dlpack(t) for t in slot_history],
            identity_matches,
            identity_preservation,
            per_frame_similarity,
        )

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`."""
        self._bridge.load_state_dict(state)


class SlotAttentionFrozen(torch.nn.Module):
    """SA-frozen: :class:`TemporalSlotAttentionMOT` with every parameter frozen.

    Every parameter frozen — the untrained baseline paired with
    :class:`PhaseTrackerFrozen`.

    Args: same as :class:`SlotAttentionNoGRU`.
    """

    def __init__(
        self,
        detection_dim: int,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct, freezing every parameter's gradient right after seeded init."""
        super().__init__()
        self._bridge = SlotAttentionFrozenBridge(
            detection_dim,
            num_slots,
            slot_dim,
            num_iterations,
            match_threshold,
            seed_counter,
            seed_key,
        )

    @property
    def inner(self) -> TemporalSlotAttentionMOT:
        """A fresh :class:`prin.nn.TemporalSlotAttentionMOT` over the frozen tracker.

        Use for `process_frame`/`slot_similarity`.
        """
        return TemporalSlotAttentionMOT._from_bridge(self._bridge.inner)

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor, seed: Seed
    ) -> tuple[list[int], torch.Tensor]:
        """Non-differentiable. `seed` is consumed (advanced)."""
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach(), seed
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(
        self, frame_detections: list[torch.Tensor], seed: Seed
    ) -> tuple[list[torch.Tensor], list[list[int]], float, list[float]]:
        """Non-differentiable. `seed` is consumed (advanced)."""
        slot_history, identity_matches, identity_preservation, per_frame_similarity = (
            self._bridge.track_sequence([d.detach() for d in frame_detections], seed)
        )
        return (
            [from_dlpack(t) for t in slot_history],
            identity_matches,
            identity_preservation,
            per_frame_similarity,
        )

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`."""
        self._bridge.load_state_dict(state)

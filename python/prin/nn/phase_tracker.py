"""``PhaseTracker``: PRIN's primary contribution, a phase-based multi-object tracker.

See ``crates/prin-py/src/bindings/phase_tracker.rs`` for the Rust bridge and
``crates/prin-train/src/phase_tracker.rs`` for the numerical core.

``encode``/``evolve``/``phase_similarity`` are genuinely differentiable
"trainable ops" (Coding Standards §3.2) and are bridged as
``torch.autograd.Function`` calls. ``match_frames``/``track_sequence`` are
**non-differentiable** evaluation utilities: greedy frame-to-frame matching is
host-side index bookkeeping with no gradient, identical in kind to PRINet
3.0's ``.item()``-per-element Python loop (see the Rust module's own docs).
They are named `match_frames`/`track_sequence`, not `forward`, so a
non-differentiable method never collides with ``nn.Module.__call__``'s
autograd-tracking expectations — a deliberate, documented Python-API
adaptation from the Rust/PRINet-3.0 naming, not a dropped symbol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import PhaseTrackerBridge

from ._bridge import apply_rust_bridge

if TYPE_CHECKING:
    from prin._prin_core import PhaseTrackerBridge as _RustPhaseTrackerBridge
    from prin._prin_core import TrackingResult as _RustTrackingResult

__all__: list[str] = ["PhaseTracker", "TrackingResult"]


@dataclass(frozen=True)
class TrackingResult:
    """Python-facing mirror of :class:`prin._prin_core.TrackingResult`.

    The result of :meth:`PhaseTracker.track_sequence`.

    Attributes:
        phase_history: Per-frame phase tensors, one per input frame, each
            ``(N_det, n_osc)``. Detached — no gradient graph.
        identity_matches: Per-transition match indices (frame `t` → frame
            `t+1`), ``-1`` if unmatched.
        identity_preservation: Fraction of matchable detections successfully
            matched across the whole sequence, in ``[0, 1]``.
        per_frame_similarity: Per-transition mean best-match similarity.
        per_frame_phase_correlation: Per-transition mean circular phase
            correlation.
    """

    phase_history: list[torch.Tensor]
    identity_matches: list[list[int]]
    identity_preservation: float
    per_frame_similarity: list[float]
    per_frame_phase_correlation: list[float]

    @staticmethod
    def _from_rust(result: _RustTrackingResult) -> TrackingResult:
        """Convert the Rust-facing result, decoding each phase-history capsule."""
        return TrackingResult(
            phase_history=[from_dlpack(t) for t in result.phase_history],
            identity_matches=result.identity_matches,
            identity_preservation=result.identity_preservation,
            per_frame_similarity=result.per_frame_similarity,
            per_frame_phase_correlation=result.per_frame_phase_correlation,
        )


class PhaseTracker(torch.nn.Module):
    """Phase-based multi-object tracker (PRIN's primary contribution).

    PRINet 3.0 ``nn.hybrid.PhaseTracker``, bridged to Rust. See the module
    docs for the differentiable (`encode`/`evolve`/`phase_similarity`) vs.
    non-differentiable (`match_frames`/`track_sequence`) method split.

    Args:
        detection_dim: Per-detection input feature dimension.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per frame.
        match_threshold: Minimum phase similarity for a valid match.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin.nn import PhaseTracker
        >>> tracker = PhaseTracker(4, n_delta=2, n_theta=3, n_gamma=4,
        ...     n_discrete_steps=2, seed_counter=1)
        >>> dets = torch.rand(3, 4, dtype=torch.float64, requires_grad=True)
        >>> phase, amp = tracker.encode(dets)
        >>> phase.shape
        torch.Size([3, 9])
        >>> phase.sum().backward()
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
        """Construct with seeded-random parameters."""
        super().__init__()
        self._bridge = PhaseTrackerBridge(
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
            seed_counter,
            seed_key,
        )

    @classmethod
    def _from_bridge(cls, bridge: _RustPhaseTrackerBridge) -> PhaseTracker:
        """Wrap an existing Rust bridge instance without seeded construction.

        Used by :class:`prin.nn.ablation.PhaseTrackerFrozen`'s `inner`
        property to expose a full differentiable wrapper over the tracker it
        composes.
        """
        wrapper = cls.__new__(cls)
        torch.nn.Module.__init__(wrapper)
        wrapper._bridge = bridge
        return wrapper

    @property
    def n_osc(self) -> int:
        """Total oscillator count across all three bands."""
        return self._bridge.n_osc

    @property
    def match_threshold(self) -> float:
        """Minimum phase similarity for a valid match."""
        return self._bridge.match_threshold

    def encode(self, detections: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode detections into `(phase, amplitude)` oscillator embeddings.

        Args:
            detections: Shape ``(N, detection_dim)``, dtype ``torch.float64``.

        Returns:
            `(phase, amplitude)`, each shape ``(N, n_osc)``.

        Raises:
            ValueError: On a shape mismatch.
        """
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.encode, [detections]
        )
        return result

    def evolve(
        self, phase: torch.Tensor, amplitude: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Evolve a `(phase, amplitude)` state through `n_discrete_steps` of dynamics.

        Raises:
            ValueError: On a shape mismatch.
        """
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.evolve, [phase, amplitude]
        )
        return result

    def phase_similarity(
        self, phase_a: torch.Tensor, phase_b: torch.Tensor
    ) -> torch.Tensor:
        """Phase-coherence similarity matrix.

        ``sim[a, b] = mean_k cos(phase_a[a,k] - phase_b[b,k])``.

        Raises:
            ValueError: On a shape mismatch.
        """
        result: torch.Tensor = apply_rust_bridge(
            self._bridge.phase_similarity, [phase_a, phase_b]
        )
        return result

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor
    ) -> tuple[list[int], torch.Tensor]:
        """Match detections across two consecutive frames. **Non-differentiable**.

        See the module docs for the non-differentiable-methods rationale.

        Returns:
            `(matches, similarity)`: `matches[i]` is the index in
            `detections_t1` matched to detection `i` in `detections_t`, or
            ``-1`` if unmatched; `similarity` is the full ``(N_t, N_t1)``
            matrix (detached — no gradient graph).

        Raises:
            ValueError: On a shape mismatch.
        """
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach()
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(self, frame_detections: list[torch.Tensor]) -> TrackingResult:
        """Track objects across a sequence of frames. **Non-differentiable**.

        See the module docs for the non-differentiable-methods rationale.

        Args:
            frame_detections: A list of ``(N_t, detection_dim)`` tensors, one
                per frame.

        Raises:
            ValueError: On a shape mismatch in any frame.
        """
        result = self._bridge.track_sequence([d.detach() for d in frame_detections])
        return TrackingResult._from_rust(result)

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                tracker's `n_osc`.
        """
        self._bridge.load_state_dict(state)

"""``SlotAttentionModule``/``TemporalSlotAttentionMOT``: the SlotAttention baseline.

The non-oscillatory comparison baseline. See
``crates/prin-py/src/bindings/slot_attention.rs`` for the Rust bridge and
``crates/prin-train/src/slot_attention.rs`` for the numerical core.

**Per-call stochastic recompute.** Unlike every other bridge in this package,
:meth:`SlotAttentionModule.forward` and
:meth:`TemporalSlotAttentionMOT.process_frame` draw fresh randomness from a
caller-supplied :class:`prin._prin_core.Seed` on *every call* (see
``crates/prin-py/src/bindings/slot_attention.rs``'s module docs for how the
Rust bridge reproduces bit-identical noise on backward recompute). Pass a
`Seed` you own — it is mutated (advanced) by each call, matching Rust's
`&mut Seed` threading convention (Coding Standards §1.3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import SlotAttentionModuleBridge, TemporalSlotAttentionMOTBridge

from ._bridge import apply_rust_bridge

if TYPE_CHECKING:
    from prin._prin_core import Seed
    from prin._prin_core import (
        TemporalSlotAttentionMOTBridge as _RustTemporalSlotAttentionMOTBridge,
    )

__all__: list[str] = [
    "SlotAttentionCLEVRN",
    "SlotAttentionModule",
    "TemporalSlotAttentionMOT",
]


class SlotAttentionModule(torch.nn.Module):
    """Slot Attention mechanism with iterative competitive binding.

    PRINet 3.0 ``nn.slot_attention.SlotAttentionModule``, bridged to Rust.

    Args:
        num_slots: Number of slots.
        slot_dim: Dimensionality of each slot vector.
        input_dim: Dimensionality of input features.
        num_iterations: Number of iterative refinement steps.
        hidden_dim: Hidden dimension for the slot-update MLP. Defaults to
            ``max(slot_dim, 128)``.
        eps: Small constant for numerical stability.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin._prin_core import Seed
        >>> from prin.nn import SlotAttentionModule
        >>> sa = SlotAttentionModule(3, 8, 5, seed_counter=1)
        >>> inputs = torch.rand(1, 4, 5, dtype=torch.float64, requires_grad=True)
        >>> out = sa(inputs, Seed(10, 0))
        >>> out.shape
        torch.Size([1, 3, 8])
        >>> out.sum().backward()
    """

    def __init__(
        self,
        num_slots: int,
        slot_dim: int,
        input_dim: int,
        num_iterations: int = 3,
        hidden_dim: int | None = None,
        eps: float = 1e-8,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters."""
        super().__init__()
        self._bridge = SlotAttentionModuleBridge(
            num_slots,
            slot_dim,
            input_dim,
            num_iterations,
            hidden_dim,
            eps,
            seed_counter,
            seed_key,
        )

    @property
    def num_slots(self) -> int:
        """Number of slots."""
        return self._bridge.num_slots

    @property
    def slot_dim(self) -> int:
        """Slot dimensionality."""
        return self._bridge.slot_dim

    def forward(self, inputs: torch.Tensor, seed: Seed | None = None) -> torch.Tensor:
        """Run Slot Attention on input features.

        Args:
            inputs: Shape ``(batch, n, input_dim)``, dtype ``torch.float64``.
            seed: Consumed (advanced) for fresh slot-initialization noise —
                see the module docs.  When *None*, an internal default seed
                is used (deterministic for the same ``seed_counter``/``seed_key``).

        Returns:
            Slots. Shape: ``(batch, num_slots, slot_dim)``.

        Raises:
            ValueError: On a shape mismatch.
        """
        from prin._prin_core import Seed as _Seed

        if seed is None:
            seed = _Seed(0, 0)
        result: torch.Tensor = apply_rust_bridge(
            lambda inp: self._bridge.forward(inp, seed), [inputs]
        )
        return result

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                module's `num_slots`/`slot_dim`.
        """
        self._bridge.load_state_dict(state)


class TemporalSlotAttentionMOT(torch.nn.Module):
    """Temporal Slot Attention for multi-frame object tracking.

    The direct comparison baseline against :class:`prin.nn.PhaseTracker`.
    PRINet 3.0 ``nn.slot_attention.TemporalSlotAttentionMOT``, bridged to
    Rust. See :mod:`prin.nn.phase_tracker` for the differentiable
    (`process_frame`/`slot_similarity`) vs. non-differentiable
    (`match_frames`/`track_sequence`) split rationale (`forward` →
    `match_frames` rename included).

    Args:
        detection_dim: Per-detection input feature dimension.
        num_slots: Number of object slots (max tracked objects).
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
        self._bridge = TemporalSlotAttentionMOTBridge(
            detection_dim,
            num_slots,
            slot_dim,
            num_iterations,
            match_threshold,
            seed_counter,
            seed_key,
        )

    @classmethod
    def _from_bridge(
        cls, bridge: _RustTemporalSlotAttentionMOTBridge
    ) -> TemporalSlotAttentionMOT:
        """Wrap an existing Rust bridge instance without seeded construction.

        Used by :class:`prin.nn.ablation.SlotAttentionFrozen`'s `inner`
        property to expose a full wrapper over the tracker it composes.
        """
        wrapper = cls.__new__(cls)
        torch.nn.Module.__init__(wrapper)
        wrapper._bridge = bridge
        return wrapper

    @property
    def num_slots(self) -> int:
        """Number of object slots."""
        return self._bridge.num_slots

    @property
    def slot_dim(self) -> int:
        """Slot dimensionality."""
        return self._bridge.slot_dim

    @property
    def match_threshold(self) -> float:
        """Minimum similarity for a valid identity match."""
        return self._bridge.match_threshold

    def process_frame(
        self,
        detections: torch.Tensor,
        seed_or_prev: Any = None,
        prev_slots: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Process one frame's detections, carrying `prev_slots` via GRU if supplied.

        The second positional argument accepts **either** a
        :class:`prin._prin_core.Seed` (PRIN bridge contract — consumed /
        advanced for fresh slot-initialisation noise) **or** the previous
        frame's slots (PRINet 3.0 ``process_frame(detections, prev_slots)``
        contract). When no ``Seed`` is supplied an internal default seed is
        used.

        Args:
            detections: Shape ``(N, detection_dim)`` or ``(1, N, detection_dim)``.
            seed_or_prev: A ``Seed`` or the previous-frame slots ``(1,
                num_slots, slot_dim)``.
            prev_slots: Previous-frame slots when ``seed_or_prev`` is a
                ``Seed``.

        Returns:
            Updated slots. Shape: ``(1, num_slots, slot_dim)``.

        Raises:
            ValueError: On a shape mismatch.
        """
        from prin._prin_core import Seed as _Seed

        if isinstance(seed_or_prev, _Seed):
            seed = seed_or_prev
        else:
            seed = _Seed(0, 0)
            prev_slots = seed_or_prev
        if detections.dim() == 3:
            detections = detections.reshape(detections.shape[-2], detections.shape[-1])
        result: torch.Tensor = apply_rust_bridge(
            lambda d, p: self._bridge.process_frame(d, seed, p),
            [detections, prev_slots],
        )
        return result

    def slot_similarity(
        self, slots_a: torch.Tensor, slots_b: torch.Tensor
    ) -> torch.Tensor:
        """Cosine similarity between two slot sets.

        Accepts ``(num_slots, slot_dim)`` or ``(1, num_slots, slot_dim)`` for
        either argument (PRINet 3.0 passes the un-batched form); returns a
        ``(num_slots, num_slots)`` matrix.

        Raises:
            ValueError: On a shape mismatch.
        """
        a = slots_a.unsqueeze(0) if slots_a.dim() == 2 else slots_a
        b = slots_b.unsqueeze(0) if slots_b.dim() == 2 else slots_b
        result: torch.Tensor = apply_rust_bridge(self._bridge.slot_similarity, [a, b])
        return result

    def match_frames(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor, seed: Seed
    ) -> tuple[list[int], torch.Tensor]:
        """Match detections across two consecutive frames. **Non-differentiable**.

        `seed` is consumed (advanced).

        Raises:
            ValueError: On a shape mismatch.
        """
        matches, sim_capsule = self._bridge.match_frames(
            detections_t.detach(), detections_t1.detach(), seed
        )
        return matches, from_dlpack(sim_capsule)

    def track_sequence(
        self, frame_detections: list[torch.Tensor], seed: Seed | None = None
    ) -> dict[str, Any]:
        """Track objects across a sequence of frames. **Non-differentiable**.

        Matches the PRINet 3.0 ``track_sequence`` contract: a dict with
        ``slot_history`` / ``identity_matches`` / ``identity_preservation`` /
        ``per_frame_similarity``. ``seed`` is consumed (advanced); an internal
        default seed is used when *None*.

        Raises:
            ValueError: On a shape mismatch in any frame.
        """
        from prin._prin_core import Seed as _Seed

        if not frame_detections:
            return {
                "slot_history": [],
                "identity_matches": [],
                "identity_preservation": 0.0,
                "per_frame_similarity": [],
            }
        if seed is None:
            seed = _Seed(0, 0)
        frames64: list[object] = [
            d.detach().to(dtype=torch.float64, device="cpu") for d in frame_detections
        ]
        slot_history, identity_matches, identity_preservation, per_frame_similarity = (
            self._bridge.track_sequence(frames64, seed)
        )
        return {
            "slot_history": [from_dlpack(t) for t in slot_history],
            "identity_matches": identity_matches,
            "identity_preservation": identity_preservation,
            "per_frame_similarity": per_frame_similarity,
        }

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                tracker's `num_slots`/`slot_dim`.
        """
        self._bridge.load_state_dict(state)


class SlotAttentionCLEVRN(torch.nn.Module):
    """Slot Attention adapter for CLEVR-N binary classification.

    PRINet 3.0 ``nn.slot_attention.SlotAttentionCLEVRN``: uses
    :class:`SlotAttentionModule` to encode scene and query inputs, then
    classifies via a small MLP.  Outputs log-softmax probabilities ``(B, 2)``.

    Args:
        scene_dim: Per-scene feature dimension.
        query_dim: Query feature dimension.
        num_slots: Number of attention slots.
        slot_dim: Slot vector dimension.
        d_model: Internal model dimension.
        num_iterations: Slot Attention iterations.
    """

    def __init__(
        self,
        scene_dim: int = 16,
        query_dim: int = 60,
        num_slots: int = 8,
        slot_dim: int = 64,
        d_model: int = 64,
        num_iterations: int = 3,
    ) -> None:
        super().__init__()
        self.scene_dim = scene_dim
        self.query_dim = query_dim
        combined = scene_dim + query_dim
        self.slot_attn = SlotAttentionModule(
            num_slots=num_slots,
            slot_dim=slot_dim,
            input_dim=combined,
            num_iterations=num_iterations,
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(num_slots * slot_dim, d_model),
            torch.nn.ReLU(),
            torch.nn.Linear(d_model, 2),
        )

    def forward(self, scene: torch.Tensor, query: torch.Tensor) -> torch.Tensor:
        """Classify a scene+query pair.

        Args:
            scene: ``(B, scene_dim)``.
            query: ``(B, query_dim)``.

        Returns:
            Log-probabilities ``(B, 2)``.
        """
        combined = torch.cat([scene, query], dim=-1)
        if combined.dim() == 2:
            combined = combined.unsqueeze(1)
        slots = self.slot_attn(combined)
        flat = slots.reshape(slots.shape[0], -1)
        logits = self.classifier(flat)
        return torch.nn.functional.log_softmax(logits, dim=-1)

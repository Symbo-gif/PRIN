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

    def forward(self, inputs: torch.Tensor, seed: Seed) -> torch.Tensor:
        """Run Slot Attention on input features.

        Args:
            inputs: Shape ``(batch, n, input_dim)``, dtype ``torch.float64``.
            seed: Consumed (advanced) for fresh slot-initialization noise —
                see the module docs.

        Returns:
            Slots. Shape: ``(batch, num_slots, slot_dim)``.

        Raises:
            ValueError: On a shape mismatch.
        """
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
        seed: Seed,
        prev_slots: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Process one frame's detections, carrying `prev_slots` via GRU if supplied.

        Args:
            detections: Shape ``(N, detection_dim)``.
            seed: Consumed (advanced) for fresh slot-initialization noise.
            prev_slots: Optional prior slots, shape ``(1, num_slots,
                slot_dim)``.

        Returns:
            Updated slots. Shape: ``(1, num_slots, slot_dim)``.

        Raises:
            ValueError: On a shape mismatch.
        """
        result: torch.Tensor = apply_rust_bridge(
            lambda d, p: self._bridge.process_frame(d, seed, p),
            [detections, prev_slots],
        )
        return result

    def slot_similarity(
        self, slots_a: torch.Tensor, slots_b: torch.Tensor
    ) -> torch.Tensor:
        """Cosine similarity between two slot sets, each ``(1, num_slots, slot_dim)``.

        Raises:
            ValueError: On a shape mismatch.
        """
        result: torch.Tensor = apply_rust_bridge(
            self._bridge.slot_similarity, [slots_a, slots_b]
        )
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
        self, frame_detections: list[torch.Tensor], seed: Seed
    ) -> tuple[list[torch.Tensor], list[list[int]], float, list[float]]:
        """Track objects across a sequence of frames. **Non-differentiable**.

        `seed` is consumed (advanced).

        Returns:
            `(slot_history, identity_matches, identity_preservation,
            per_frame_similarity)`.

        Raises:
            ValueError: On a shape mismatch in any frame.
        """
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
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                tracker's `num_slots`/`slot_dim`.
        """
        self._bridge.load_state_dict(state)


class SlotAttentionCLEVRN:
    """Deferred-rebuild stub for the Slot Attention CLEVR-N adapter.

    PRINet 3.0 ``nn.slot_attention.SlotAttentionCLEVRN``: adapter wrapping
    :class:`SlotAttentionModule` for CLEVR-N scene + query binary
    classification. Contains trainable ``nn.Linear`` projections (scene
    projection, query projection, classifier MLP).

    A faithful implementation requires net-new trainable Rust numerics +
    autodiff, which WP-036 prohibits. Consistent with the hybrid-model
    family D-2.2 disposition (0141B rows 31-42 precedent).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        raise NotImplementedError(
            "SlotAttentionCLEVRN is a deferred-rebuild symbol (WP-036 D-2.2). "
            "Trainable nn.Module with nn.Linear projections; needs a "
            "trainable-layer rebuild in a future WP. "
            "See the Migration Guide for the disposition."
        )

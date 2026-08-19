"""``AdaptiveOscillatorAllocator``/``DynamicPhaseTracker``: oscillator allocation.

See ``crates/prin-py/src/bindings/allocation.rs`` for the Rust bridge and
``crates/prin-train/src/allocation.rs`` for the numerical core.

Every entry point here is **non-differentiable** (Coding Standards §3.2
governs "trainable ops"; oscillator *counts* are discrete outputs derived via
`floor`/`round`, not a differentiable computation to begin with). Neither
class is a ``torch.nn.Module``: there is no differentiable `forward` to
expose, so wrapping either in the ``nn.Module`` machinery would be
misleading, not merely unused ceremony.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import AdaptiveOscillatorAllocatorBridge, DynamicPhaseTrackerBridge
from prin._prin_core import OscillatorBudget as OscillatorBudget  # re-export
from prin._prin_core import estimate_complexity as estimate_complexity  # re-export

if TYPE_CHECKING:
    from prin._prin_core import Seed

__all__: list[str] = [
    "AdaptiveOscillatorAllocator",
    "DynamicPhaseTracker",
    "OscillatorBudget",
    "estimate_complexity",
]


class AdaptiveOscillatorAllocator:
    """Dynamically allocates oscillator counts per band from a complexity scalar.

    PRINet 3.0 ``nn.adaptive_allocation.AdaptiveOscillatorAllocator``,
    bridged to Rust. Not a ``torch.nn.Module`` — see the module docs.

    Args:
        min_total: Minimum total oscillator count. Must be ``>= 3``.
        max_total: Maximum total oscillator count. Must be ``>= min_total``.
        delta_ratio: Fraction of total allocated to the delta band (rule
            strategy).
        theta_ratio: Fraction of total allocated to the theta band (rule
            strategy).
        strategy: ``"rule"`` (deterministic piecewise-linear interpolation)
            or ``"learned"`` (a small MLP predicts soft per-band fractions).
        complexity_dim: Input feature dimension for the learned strategy.
        seed_counter: Counter half of the deterministic ``Seed`` (used only
            by the learned strategy's MLP initialization).
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> from prin.nn import AdaptiveOscillatorAllocator
        >>> alloc = AdaptiveOscillatorAllocator(12, 64)
        >>> budget = alloc.allocate(0.5)
        >>> budget.total() >= 12
        True
    """

    def __init__(
        self,
        min_total: int,
        max_total: int,
        delta_ratio: float = 0.1,
        theta_ratio: float = 0.2,
        strategy: str = "rule",
        complexity_dim: int = 1,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters (learned-strategy MLP only)."""
        self._bridge = AdaptiveOscillatorAllocatorBridge(
            min_total,
            max_total,
            delta_ratio,
            theta_ratio,
            strategy,
            complexity_dim,
            seed_counter,
            seed_key,
        )

    @property
    def strategy(self) -> str:
        """The configured allocation strategy (`"rule"` or `"learned"`)."""
        return self._bridge.strategy

    def allocate(
        self, complexity: float, features: torch.Tensor | None = None
    ) -> OscillatorBudget:
        """Compute an oscillator budget for `complexity` (clamped to ``[0, 1]``).

        Uses the learned MLP only when :attr:`strategy` is ``"learned"``
        **and** `features` is supplied; falls back to the rule-based formula
        otherwise.

        Raises:
            ValueError: If `features` is supplied with an invalid shape.
        """
        features_detached = features.detach() if features is not None else None
        return self._bridge.allocate(complexity, features_detached)

    def sweep_complexity(self, steps: int) -> list[OscillatorBudget]:
        """Generate budgets for `steps` evenly-spaced complexity values in [0, 1]."""
        return self._bridge.sweep_complexity(steps)

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes.

        Empty for the rule strategy, which has no learnable parameters.
        """
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a valid record, or
                decodes to a learned-strategy MLP whose shape does not match
                this allocator's `complexity_dim`.
        """
        self._bridge.load_state_dict(state)


class DynamicPhaseTracker:
    """[`PhaseTracker`][prin.nn.PhaseTracker] with adaptive oscillator allocation.

    Builds and caches a tracker per distinct oscillator budget, selected
    from an estimated scene complexity.

    Not a ``torch.nn.Module`` — see the Rust type's own module docs: its
    whole purpose is to lazily cache a *different* `PhaseTracker` per budget,
    which has no fixed parameter set to describe.

    Args:
        detection_dim: Per-detection input feature dimension.
        min_total: Minimum total oscillator count.
        max_total: Maximum total oscillator count.
        n_discrete_steps: Dynamics steps per frame.
        match_threshold: Minimum phase similarity for a valid match.
        allocator_strategy: ``"rule"`` or ``"learned"``.
        max_objects: Normalization constant for the object-count complexity
            term.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.
    """

    def __init__(
        self,
        detection_dim: int,
        min_total: int,
        max_total: int,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        allocator_strategy: str = "rule",
        max_objects: int = 50,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct over a rule- or learned-strategy allocator with a given range."""
        self._bridge = DynamicPhaseTrackerBridge(
            detection_dim,
            min_total,
            max_total,
            n_discrete_steps,
            match_threshold,
            allocator_strategy,
            max_objects,
            seed_counter,
            seed_key,
        )

    def forward(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor, seed: Seed
    ) -> tuple[list[int], torch.Tensor, OscillatorBudget]:
        """Match detections with a budget adapted to `detections_t`'s complexity.

        **Non-differentiable**. `seed` is consumed (advanced) — a
        newly-required budget lazily seeds and caches a fresh `PhaseTracker`.

        **Faithfully reproduced quirk**: always uses rule-based allocation,
        even if this tracker's allocator is `"learned"` (a real PRINet 3.0
        behavior, preserved intentionally — see the Rust module's docs).

        Raises:
            ValueError: On a shape mismatch.
        """
        matches, sim_capsule, budget = self._bridge.forward(
            detections_t.detach(), detections_t1.detach(), seed
        )
        return matches, from_dlpack(sim_capsule), budget

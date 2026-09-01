"""``AdaptiveOscillatorAllocator``/``DynamicPhaseTracker``: oscillator allocation.

Strict-port surface for PRINet 3.0 ``prinet.nn.adaptive_allocation`` (WP-036C
S1, sub-pass 0144M3). The numerical core stays in Rust
(``crates/prin-train/src/allocation.rs``, bridged in
``crates/prin-py/src/bindings/allocation.rs``): piecewise-linear rule
allocation, the learned-strategy MLP, ``estimate_complexity``'s spatial-spread
reduction, and the per-budget ``PhaseTracker`` cache are all Rust-owned. This
module adds only the reference-shaped Python surface the ``test_y3q2``
acceptance suite exercises:

* :class:`OscillatorBudget` -- a frozen bookkeeping dataclass (``.total``
  property, value equality), constructed directly in tests and returned from
  every allocation call;
* :func:`estimate_complexity` -- returns a ``float32`` scalar tensor (mirrors
  PRINet 3.0), marshalling any dtype/device input to the Rust probe;
* :class:`AdaptiveOscillatorAllocator` -- exposes ``min_total`` / ``max_total``
  / ``strategy`` / ``_mlp`` attributes, ``__call__`` == ``allocate``, and the
  reference ``ValueError`` messages;
* :class:`DynamicPhaseTracker` -- callable as ``tracker(dets_t, dets_t1)``
  with an internally-managed seed, returning ``(matches, sim, budget)`` with
  ``matches`` an ``int64`` tensor.

Neither allocator class is a ``torch.nn.Module``: oscillator *counts* are
discrete ``round``/``floor`` outputs, not a differentiable computation
(Coding Standards §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import (
    AdaptiveOscillatorAllocatorBridge,
    DynamicPhaseTrackerBridge,
    Seed,
)
from prin._prin_core import OscillatorBudget as _RustOscillatorBudget
from prin._prin_core import estimate_complexity as _rust_estimate_complexity

if TYPE_CHECKING:
    from prin._prin_core import AdaptiveOscillatorAllocatorBridge as _AllocBridge

__all__: list[str] = [
    "AdaptiveOscillatorAllocator",
    "DynamicPhaseTracker",
    "OscillatorBudget",
    "estimate_complexity",
]


@dataclass(frozen=True)
class OscillatorBudget:
    """Allocated oscillator counts per frequency band.

    Bookkeeping only -- the counts are produced by the Rust allocator. A
    frozen dataclass so tests can construct it directly and compare budgets
    by value.
    """

    n_delta: int
    """Delta-band (1-4 Hz) oscillators."""

    n_theta: int
    """Theta-band (4-8 Hz) oscillators."""

    n_gamma: int
    """Gamma-band (30-100 Hz) oscillators."""

    complexity: float
    """Estimated scene complexity in ``[0, 1]``."""

    @property
    def total(self) -> int:
        """Total oscillator count across all bands."""
        return self.n_delta + self.n_theta + self.n_gamma

    @staticmethod
    def _from_rust(b: _RustOscillatorBudget) -> OscillatorBudget:
        """Adopt the Rust bridge's budget as a frozen Python dataclass."""
        return OscillatorBudget(
            n_delta=int(b.n_delta),
            n_theta=int(b.n_theta),
            n_gamma=int(b.n_gamma),
            complexity=float(b.complexity),
        )


def estimate_complexity(
    detections: torch.Tensor,
    *,
    spatial_weight: float = 0.5,
    count_weight: float = 0.5,
    max_objects: int = 50,
) -> torch.Tensor:
    """Estimate scene complexity from detection features.

    Complexity is a scalar in ``[0, 1]`` combining object count and spatial
    spread (standard deviation of detection centroids). The spread reduction
    is computed in Rust; this wrapper marshals ``detections`` to the
    ``float64`` CPU layout the probe requires and returns a ``float32``
    scalar tensor on ``detections``'s device (mirrors PRINet 3.0).

    Args:
        detections: Detection features ``(N, D)`` with ``D >= 2`` (first two
            columns treated as spatial centroid x, y).
        spatial_weight: Weight for the spatial-spread term.
        count_weight: Weight for the count term.
        max_objects: Count at which the count term saturates to 1.0.

    Returns:
        Scalar ``float32`` tensor in ``[0, 1]``.
    """
    probe_input = detections.detach().to(dtype=torch.float64, device="cpu").contiguous()
    value = _rust_estimate_complexity(
        probe_input, spatial_weight, count_weight, max_objects
    )
    return torch.tensor(float(value), device=detections.device, dtype=torch.float32)


class AdaptiveOscillatorAllocator:
    """Dynamically allocates oscillator counts per band from a complexity scalar.

    PRINet 3.0 ``nn.adaptive_allocation.AdaptiveOscillatorAllocator``, bridged
    to Rust. Not a ``torch.nn.Module`` -- see the module docs.

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
        seed_counter: Counter half of the deterministic ``Seed`` (learned MLP
            init only).
        seed_key: Key half of the deterministic ``Seed``.

    Raises:
        ValueError: If ``min_total < 3`` or ``max_total < min_total``, or on
            an unknown ``strategy``.

    Examples:
        >>> from prin.nn import AdaptiveOscillatorAllocator
        >>> alloc = AdaptiveOscillatorAllocator(min_total=12, max_total=64)
        >>> alloc.allocate(0.5).total >= 12
        True
    """

    def __init__(
        self,
        min_total: int = 12,
        max_total: int = 64,
        delta_ratio: float = 0.1,
        theta_ratio: float = 0.2,
        strategy: str = "rule",
        complexity_dim: int = 1,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters (learned-strategy MLP only)."""
        if min_total < 3:
            raise ValueError(f"min_total must be >= 3, got {min_total}")
        if max_total < min_total:
            raise ValueError(
                f"max_total ({max_total}) must be >= min_total ({min_total})"
            )

        self.min_total = min_total
        self.max_total = max_total
        self.delta_ratio = delta_ratio
        self.theta_ratio = theta_ratio
        self.complexity_dim = complexity_dim
        self._bridge: _AllocBridge = AdaptiveOscillatorAllocatorBridge(
            min_total,
            max_total,
            delta_ratio,
            theta_ratio,
            strategy,
            complexity_dim,
            seed_counter,
            seed_key,
        )
        # Opaque handle to the Rust-owned learned MLP; ``None`` for the rule
        # strategy (which has no learnable parameters). Mirrors PRINet 3.0's
        # ``self._mlp`` sentinel without holding a Python ``nn.Module``.
        self._mlp: object | None = (
            self._bridge if self._bridge.strategy == "learned" else None
        )

    @property
    def strategy(self) -> str:
        """The configured allocation strategy (`"rule"` or `"learned"`)."""
        return self._bridge.strategy

    def allocate(
        self, complexity: float | torch.Tensor, features: torch.Tensor | None = None
    ) -> OscillatorBudget:
        """Compute an oscillator budget for `complexity` (clamped to ``[0, 1]``).

        Uses the learned MLP only when :attr:`strategy` is ``"learned"``
        **and** `features` is supplied; falls back to the rule-based formula
        otherwise.

        Args:
            complexity: Scene-complexity scalar (a Python float or a 0-d
                tensor).
            features: Optional ``(complexity_dim,)`` or ``(1, complexity_dim)``
                feature vector for the learned strategy.

        Raises:
            ValueError: If `features` is supplied with an invalid shape.
        """
        c = float(complexity)
        prepared: torch.Tensor | None = None
        if features is not None:
            prepared = features.detach()
            if prepared.dim() == 1:
                prepared = prepared.unsqueeze(0)
            prepared = prepared.to(dtype=torch.float64, device="cpu").contiguous()
        return OscillatorBudget._from_rust(self._bridge.allocate(c, prepared))

    def __call__(
        self, complexity: float | torch.Tensor, features: torch.Tensor | None = None
    ) -> OscillatorBudget:
        """Alias for :meth:`allocate` (PRINet 3.0 ``nn.Module`` call form)."""
        return self.allocate(complexity, features)

    def sweep_complexity(self, steps: int) -> list[OscillatorBudget]:
        """Generate budgets for `steps` evenly-spaced complexity values in [0, 1]."""
        return [
            OscillatorBudget._from_rust(b) for b in self._bridge.sweep_complexity(steps)
        ]

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

    Builds and caches a tracker per distinct oscillator budget, selected from
    an estimated scene complexity. Not a ``torch.nn.Module`` -- its whole
    purpose is to lazily cache a *different* `PhaseTracker` per budget.

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
        min_total: int = 12,
        max_total: int = 64,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        allocator_strategy: str = "rule",
        max_objects: int = 50,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct over a rule- or learned-strategy allocator with a given range."""
        self.detection_dim = detection_dim
        self.max_objects = max_objects
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
        # Internally-managed seed progression so callers use the PRINet 3.0
        # ``tracker(dets_t, dets_t1)`` form; a per-budget ``PhaseTracker`` is
        # lazily seeded and cached inside Rust.
        self._seed = Seed(int(seed_counter), int(seed_key))

    def forward(
        self,
        detections_t: torch.Tensor,
        detections_t1: torch.Tensor,
        seed: Seed | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, OscillatorBudget]:
        """Match detections with a budget adapted to `detections_t`'s complexity.

        **Non-differentiable**. When `seed` is omitted the tracker's own
        internal seed is advanced.

        **Faithfully reproduced quirk**: always uses rule-based allocation,
        even if this tracker's allocator is `"learned"` (a real PRINet 3.0
        behavior, preserved intentionally).

        Args:
            detections_t: Frame *t* detections ``(N_t, D)``.
            detections_t1: Frame *t+1* detections ``(N_t1, D)``.
            seed: Optional explicit seed; consumed (advanced) in place.

        Returns:
            ``(matches, similarity, budget)`` -- ``matches`` an ``(N_t,)``
            ``int64`` tensor of matched indices (``-1`` = unmatched),
            ``similarity`` the ``(N_t, N_t1)`` matrix, ``budget`` the
            :class:`OscillatorBudget` used.

        Raises:
            ValueError: On a shape mismatch.
        """
        active_seed = self._seed if seed is None else seed
        device = detections_t.device
        matches, sim_capsule, budget = self._bridge.forward(
            detections_t.detach().to(dtype=torch.float64, device="cpu").contiguous(),
            detections_t1.detach().to(dtype=torch.float64, device="cpu").contiguous(),
            active_seed,
        )
        match_tensor = torch.tensor(list(matches), dtype=torch.long, device=device)
        sim = from_dlpack(sim_capsule).to(device)
        return match_tensor, sim, OscillatorBudget._from_rust(budget)

    def __call__(
        self, detections_t: torch.Tensor, detections_t1: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, OscillatorBudget]:
        """Match detections (PRINet 3.0 ``nn.Module`` call form)."""
        return self.forward(detections_t, detections_t1)

"""PRINet 3.0-compatible topology builders.

Thin wrappers that construct ``(N, k)`` neighbour-index tensors for ring and
Watts-Strogatz small-world topologies. The discrete index arithmetic and the
deterministic rewiring RNG are owned by the Rust
:mod:`prin._prin_core` core (``ring_topology_indices`` /
``small_world_topology_indices``); this module only reshapes the flat row-major
result into a ``torch`` tensor (Coding Standards Sec. 1.2).

Representation (WP-036C S1 ``0144M5``): matches PRINet 3.0
``utils.oscillosim.ring_topology`` / ``small_world_topology`` exactly — an
``(N, k)`` ``torch.int64`` tensor of neighbour indices, positional ``k``, and a
``device`` argument. This supersedes the earlier flat-``list`` representation
(Migration Guide D1), which no first-party code consumed.

RNG-seed hazard (Migration Guide D2): :func:`small_world_topology` derives its
Watts-Strogatz rewiring from a :class:`prin_dynamics.Seed` stream. PRINet 3.0
used ``torch.Generator``; the same scalar seed does **not** reproduce the same
rewiring across implementations, though it is deterministic within PRIN.
"""

from __future__ import annotations

import torch

from prin._prin_core import (
    ring_topology_indices as _ring_indices,
)
from prin._prin_core import (
    small_world_topology_indices as _small_world_indices,
)

__all__ = [
    "ring_topology",
    "small_world_topology",
]


def ring_topology(
    N: int,
    k: int,
    device: str = "cpu",
) -> torch.Tensor:
    """Build a 1-D ring lattice neighbour-index tensor.

    Each oscillator *i* is connected to its ``k / 2`` nearest neighbours on
    each side of the ring (``(i ± d) mod N``). Deterministic — no randomness.

    Args:
        N: Number of oscillators (nodes on the ring).
        k: Number of neighbours per oscillator. Must be even and in ``[2, N)``.
        device: Target device for the output tensor.

    Returns:
        Neighbour index tensor of shape ``(N, k)`` with dtype ``torch.int64``.

    Raises:
        ValueError: If ``k`` is odd, ``k < 2``, or ``k >= N``.

    Example:
        >>> ring_topology(6, 2).tolist()
        [[5, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 0]]
    """
    flat = _ring_indices(N, k)
    return torch.tensor(flat, dtype=torch.int64, device=device).reshape(N, k)


def small_world_topology(
    N: int,
    k: int,
    p_rewire: float = 0.1,
    device: str = "cpu",
    seed: int = 42,
) -> torch.Tensor:
    """Build a Watts-Strogatz small-world neighbour-index tensor.

    Starts from a ring lattice (see :func:`ring_topology`) and rewires each
    edge with probability ``p_rewire``, then repairs any self-loop by pointing
    it at ``(i + 1) mod N``.

    Args:
        N: Number of oscillators.
        k: Neighbours per oscillator in the base ring. Must be even and in
            ``[2, N)``.
        p_rewire: Rewiring probability (``0`` = pure ring, ``1`` = fully
            random).
        device: Target device.
        seed: Random seed for deterministic rewiring.

    Returns:
        Neighbour index tensor of shape ``(N, k)`` with dtype ``torch.int64``.

    Raises:
        ValueError: If ``k`` is odd, ``k < 2``, or ``k >= N``.

    Example:
        >>> small_world_topology(16, 4, p_rewire=0.0).shape
        torch.Size([16, 4])
    """
    flat = _small_world_indices(N, k, p_rewire, seed)
    return torch.tensor(flat, dtype=torch.int64, device=device).reshape(N, k)

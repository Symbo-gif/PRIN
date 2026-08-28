"""PRINet 3.0-compatible topology builders.

Thin wrappers that construct neighbour-index tables for ring and
Watts-Strogatz small-world topologies. The numerical coupling computation
is owned by the Rust :mod:`prin.kernels` / :mod:`prin.dynamics` owners;
these functions only build the discrete neighbour-index structure
(Coding Standards Sec. 1.2).

Representation adaptation (Migration Guide D1): PRINet 3.0 returned an
``(N, k)`` ``torch.Tensor`` of neighbour indices. PRIN returns a flat
Python list of ``N * k`` indices in row-major order (matching
:func:`prin.kernels.build_knn_neighbors`). Callers that need a tensor
can wrap the result in ``torch.tensor(...)``.

RNG-seed hazard (Migration Guide D2): :func:`small_world_topology` uses
Python's :mod:`random` module with an explicit seed for the Watts-Strogatz
rewiring. PRINet 3.0 used ``torch.Generator``; the same scalar seed does
**not** guarantee the same rewiring across implementations.
"""

from __future__ import annotations

import random

__all__ = [
    "ring_topology",
    "small_world_topology",
]


def ring_topology(
    n_oscillators: int,
    k_neighbors: int = 4,
) -> list[int]:
    """Build a 1-D ring lattice neighbour-index table.

    Each oscillator *i* is connected to the ``k_neighbors / 2`` nearest
    oscillators on each side (wrapping modulo *N*). The result is a flat
    list of ``N * k`` indices in row-major order.

    This is a deterministic construction with no randomness.

    Args:
        n_oscillators: Population size *N*. Must be >= 2.
        k_neighbors: Neighbours per oscillator. Must be even and in
            ``[2, N - 1]``.

    Returns:
        Flat list of ``N * k`` neighbour indices (row-major).

    Raises:
        ValueError: If constraints on *N* or *k* are violated.

    Example:
        >>> ring_topology(6, k_neighbors=2)
        [5, 1, 0, 2, 1, 3, 2, 4, 3, 5, 4, 0]
    """
    if n_oscillators < 2:
        raise ValueError(f"n_oscillators must be >= 2, got {n_oscillators}")
    if k_neighbors < 2 or k_neighbors % 2 != 0:
        raise ValueError(
            f"k_neighbors must be a positive even number, got {k_neighbors}"
        )
    if k_neighbors >= n_oscillators:
        raise ValueError(
            f"k_neighbors ({k_neighbors}) must be < n_oscillators ({n_oscillators})"
        )

    half = k_neighbors // 2
    result: list[int] = []
    for i in range(n_oscillators):
        for offset in range(-half, half + 1):
            if offset == 0:
                continue
            result.append((i + offset) % n_oscillators)
    return result


def small_world_topology(
    n_oscillators: int,
    k_neighbors: int = 4,
    p_rewire: float = 0.1,
    seed: int = 0,
) -> list[int]:
    """Build a Watts-Strogatz small-world neighbour-index table.

    Starts from a ring lattice (see :func:`ring_topology`) and rewires each
    edge independently with probability ``p_rewire``. Rewired targets are
    drawn uniformly from the population excluding self and existing
    neighbours.

    Args:
        n_oscillators: Population size *N*. Must be >= 2.
        k_neighbors: Neighbours per oscillator (before rewiring). Must be
            even and in ``[2, N - 1]``.
        p_rewire: Rewiring probability in ``[0, 1]``.
        seed: Random seed for deterministic rewiring.

    Returns:
        Flat list of ``N * k`` neighbour indices (row-major).

    Raises:
        ValueError: If constraints are violated.

    Example:
        >>> nbrs = small_world_topology(8, k_neighbors=2, p_rewire=0.0)
        >>> len(nbrs)
        16
    """
    if n_oscillators < 2:
        raise ValueError(f"n_oscillators must be >= 2, got {n_oscillators}")
    if k_neighbors < 2 or k_neighbors % 2 != 0:
        raise ValueError(
            f"k_neighbors must be a positive even number, got {k_neighbors}"
        )
    if k_neighbors >= n_oscillators:
        raise ValueError(
            f"k_neighbors ({k_neighbors}) must be < n_oscillators ({n_oscillators})"
        )
    if not 0.0 <= p_rewire <= 1.0:
        raise ValueError(f"p_rewire must be in [0, 1], got {p_rewire}")

    rng = random.Random(seed)  # noqa: S311  # nosec B311 — topology, not crypto
    half = k_neighbors // 2

    # Build the ring lattice as a list-of-sets for O(1) membership tests.
    adj: list[set[int]] = []
    for i in range(n_oscillators):
        neighbours: set[int] = set()
        for offset in range(-half, half + 1):
            if offset == 0:
                continue
            neighbours.add((i + offset) % n_oscillators)
        adj.append(neighbours)

    # Rewire: for each oscillator, rewire each right-side neighbour.
    for i in range(n_oscillators):
        right_neighbours = [
            (i + offset) % n_oscillators for offset in range(1, half + 1)
        ]
        for target in right_neighbours:
            if rng.random() < p_rewire:
                candidates = [
                    j for j in range(n_oscillators) if j != i and j not in adj[i]
                ]
                if candidates:
                    new_target = rng.choice(candidates)
                    adj[i].discard(target)
                    adj[i].add(new_target)

    # Flatten to row-major list.
    result: list[int] = []
    for i in range(n_oscillators):
        result.extend(sorted(adj[i]))
    return result

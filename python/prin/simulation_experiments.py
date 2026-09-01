"""PRINet 3.0-compatible oscillosim benchmark scaffolding (Year-4-Q1.8).

Faithful ports (Testing Standards §1.1) of the ``prinet.utils.oscillosim``
heterogeneous-frequency / multi-scale-topology / evolutionary-coupling helpers
that the Q1.8 benchmarks build their chimera experiments from. These are
synthetic topology / frequency generators — the same benchmark/experiment
tooling category as :mod:`prin.y4q1_tools` and :mod:`benchmarks` (excluded from
the ``check_no_python_numerics`` compat-surface scan). Chimera *metrics* and the
:class:`~prin.simulation.OscilloSim` stepping loop remain Rust-owned
(:mod:`prin._prin_core`); these helpers only assemble the ``(N, k)`` neighbour
and weight tensors those consume.

Re-exported through :mod:`prin.simulation` for the PRINet 3.0 import path.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor

__all__ = [
    "community_topology",
    "conduction_delay_matrix",
    "directed_weighted_topology",
    "evolutionary_coupling_update",
    "heterogeneous_natural_frequencies",
    "hierarchical_topology",
]


def heterogeneous_natural_frequencies(
    N: int,
    distribution: str = "gaussian",
    spread: float = 1.0,
    center: float = 0.0,
    seed: int = 42,
) -> Tensor:
    """Generate heterogeneous natural frequencies for oscillators.

    Args:
        N: Number of oscillators.
        distribution: One of ``"gaussian"``, ``"lorentzian"``, ``"uniform"``.
        spread: Width parameter (sigma / gamma / half-width).
        center: Central frequency.
        seed: Random seed.

    Returns:
        Frequency tensor ``(N,)``.
    """
    gen = torch.Generator().manual_seed(seed)

    if distribution == "gaussian":
        omega = torch.randn(N, generator=gen) * spread + center
    elif distribution == "lorentzian":
        u = torch.rand(N, generator=gen)
        u = u.clamp(0.01, 0.99)
        omega = spread * torch.tan(math.pi * (u - 0.5)) + center
        omega = omega.clamp(center - 10 * spread, center + 10 * spread)
    elif distribution == "uniform":
        omega = (torch.rand(N, generator=gen) - 0.5) * 2 * spread + center
    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    return omega


def conduction_delay_matrix(
    N: int,
    nbr_idx: Tensor,
    delay_type: str = "distance_proportional",
    max_delay: int = 5,
    seed: int = 42,
) -> Tensor:
    """Generate a conduction delay matrix for neighbours ``(N, k)`` (timestep units).

    Args:
        N: Number of oscillators.
        nbr_idx: Neighbour indices ``(N, k)``.
        delay_type: ``"distance_proportional"``, ``"random_uniform"``,
            or ``"constant"``.
        max_delay: Maximum delay in timesteps.
        seed: Random seed.
    """
    k = nbr_idx.shape[1]

    if delay_type == "constant":
        return torch.full((N, k), max_delay, dtype=torch.long)

    if delay_type == "random_uniform":
        gen = torch.Generator().manual_seed(seed)
        return torch.randint(0, max_delay + 1, (N, k), generator=gen)

    if delay_type == "distance_proportional":
        positions = torch.arange(N, dtype=torch.float32)
        nbr_positions = positions[nbr_idx.clamp(0, N - 1)]
        src_positions = positions.unsqueeze(1).expand(N, k)
        dist = torch.min(
            (nbr_positions - src_positions).abs(),
            N - (nbr_positions - src_positions).abs(),
        )
        max_dist = dist.max()
        if max_dist > 0:
            delays = (dist / max_dist * max_delay).long()
        else:
            delays = torch.zeros(N, k, dtype=torch.long)
        return delays

    raise ValueError(f"Unknown delay_type: {delay_type}")


def community_topology(
    N: int,
    n_communities: int = 2,
    k_intra: int = 20,
    k_inter: int = 5,
    seed: int = 42,
) -> tuple[Tensor, list[list[int]]]:
    """Build a modular community topology (dense intra, sparse inter).

    Returns:
        Tuple of (nbr_idx ``(N, k_intra + k_inter)``,
        community_assignments ``list[list[int]]``).
    """
    gen = torch.Generator().manual_seed(seed)
    community_size = N // n_communities
    communities = []
    for c in range(n_communities):
        start = c * community_size
        end = start + community_size if c < n_communities - 1 else N
        communities.append(list(range(start, end)))

    k_total = k_intra + k_inter
    nbr_idx = torch.zeros(N, k_total, dtype=torch.long)

    for c_idx, community in enumerate(communities):
        cs = len(community)
        for i_local, i_global in enumerate(community):
            intra_nbrs = []
            for offset in range(1, k_intra + 1):
                j_local = (i_local + offset) % cs
                intra_nbrs.append(community[j_local])
            if len(intra_nbrs) > k_intra:
                intra_nbrs = intra_nbrs[:k_intra]

            other_indices = []
            for oc_idx, oc in enumerate(communities):
                if oc_idx != c_idx:
                    other_indices.extend(oc)
            inter_nbrs = []
            if other_indices and k_inter > 0:
                perm = torch.randperm(len(other_indices), generator=gen)
                for p in range(min(k_inter, len(other_indices))):
                    inter_nbrs.append(other_indices[int(perm[p].item())])

            while len(intra_nbrs) < k_intra:
                intra_nbrs.append(community[0])
            while len(inter_nbrs) < k_inter:
                inter_nbrs.append(other_indices[0] if other_indices else 0)

            nbrs = intra_nbrs[:k_intra] + inter_nbrs[:k_inter]
            nbr_idx[i_global, : len(nbrs)] = torch.tensor(nbrs, dtype=torch.long)

    return nbr_idx, communities


def hierarchical_topology(
    N: int,
    n_groups: int = 4,
    k_intra: int = 15,
    k_inter: int = 5,
    seed: int = 42,
) -> tuple[Tensor, list[list[int]]]:
    """Build a 2-level hierarchical topology (via :func:`community_topology`)."""
    return community_topology(N, n_groups, k_intra, k_inter, seed)


def evolutionary_coupling_update(
    coupling_weights: Tensor,
    phase: Tensor,
    nbr_idx: Tensor,
    payoff_type: str = "coordination",
    mutation_rate: float = 0.01,
    seed: int = 42,
) -> Tensor:
    """Update coupling weights via replicator dynamics.

    Oscillators with higher local synchronisation are "fitter"; their coupling
    patterns are replicated (plus mutation). Returns updated weights ``(N, k)``.
    """
    N, _k = coupling_weights.shape
    gen = torch.Generator(device=coupling_weights.device)
    gen.manual_seed(seed)

    nbr_phase = phase[nbr_idx.clamp(0, N - 1)]
    phase_diff = nbr_phase - phase.unsqueeze(1)
    cos_diff = torch.cos(phase_diff)

    if payoff_type == "coordination":
        fitness = (coupling_weights * cos_diff).sum(dim=1)
    elif payoff_type == "prisoners_dilemma":
        fitness = (coupling_weights * cos_diff).sum(dim=1) - 0.5 * coupling_weights.sum(
            dim=1
        )
    elif payoff_type == "hawk_dove":
        fitness = (coupling_weights * cos_diff).sum(dim=1) - 0.3 * coupling_weights.pow(
            2
        ).sum(dim=1)
    else:
        fitness = (coupling_weights * cos_diff).sum(dim=1)

    fitness_norm = torch.softmax(fitness, dim=0)
    nbr_fitness = fitness_norm[nbr_idx.clamp(0, N - 1)]

    new_weights = coupling_weights + 0.1 * coupling_weights * (
        nbr_fitness - fitness_norm.unsqueeze(1)
    )

    _ = gen  # reference constructs a generator here but draws noise unseeded
    noise = torch.randn_like(new_weights) * mutation_rate
    new_weights = (new_weights + noise).clamp(0.0, 10.0)

    return new_weights


def directed_weighted_topology(
    N: int,
    k: int = 20,
    asymmetry: float = 0.0,
    seed: int = 42,
) -> tuple[Tensor, Tensor]:
    """Build a directed weighted topology with tuneable asymmetry.

    Returns:
        Tuple of (nbr_idx ``(N, k)``, weights ``(N, k)``).
    """
    gen = torch.Generator().manual_seed(seed)

    nbr_idx = torch.zeros(N, k, dtype=torch.long)
    for i in range(N):
        offsets = torch.arange(1, k + 1)
        nbr_idx[i] = (i + offsets) % N

    base_weights = torch.ones(N, k)
    asym_noise = torch.rand(N, k, generator=gen) * 2 - 1
    weights = base_weights + asymmetry * asym_noise
    weights = weights.clamp(0.01, 5.0)

    return nbr_idx, weights

"""PRINet 3.0-compatible oscillator simulation surface.

This module is the thin Python compatibility layer for the PRINet 3.0
``prinet.utils.oscillosim`` family: the :class:`OscilloSim` engine (mean-field,
sparse k-NN, CSR, ring, and small-world coupling; Euler / RK4 integration;
phase-lag and per-edge coupling weights), :class:`SimulationResult`,
:func:`quick_simulate`, the ring / small-world topology builders, the cosine
coupling kernel, and the chimera-state detection metrics.

Every numerical result is owned by the Rust core: the stepping loop by
:mod:`prin._prin_core` (``oscillo_compat_run``), the topology builders and
cosine kernel by the same crate, and the chimera metrics by ``prin_metrics``
(re-exported through ``prin._prin_core``). This layer performs orchestration and
torch↔list marshalling only; no integration or metric math runs in Python
(Coding Standards Sec. 1.2).

Symbols with no faithful non-numeric implementation
(``LargeScaleOscillatorSystem``, ``OscillatorPruner``) delegate to the
already-shipped Rust k-NN kernels (``0144M4``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, ClassVar

import torch

from prin._prin_core import (
    bimodality_index as _rust_bimodality_index,
)
from prin._prin_core import (
    chimera_index as _rust_chimera_index,
)
from prin._prin_core import (
    cosine_coupling_kernel_row as _rust_cosine_kernel,
)
from prin._prin_core import (
    discontinuity_measure as _rust_discontinuity_measure,
)
from prin._prin_core import (
    local_order_parameter as _rust_local_order_parameter,
)
from prin._prin_core import (
    oscillo_compat_run as _rust_oscillo_run,
)
from prin._prin_core import (
    strength_of_incoherence as _rust_strength_of_incoherence,
)
from prin._prin_core import (
    strength_of_incoherence_temporal as _rust_strength_of_incoherence_temporal,
)
from prin.topology import ring_topology, small_world_topology

__all__ = [
    "LargeScaleOscillatorSystem",
    "OscillatorPruner",
    "OscilloSim",
    "SimulationResult",
    "bimodality_index",
    "chimera_index",
    "cosine_coupling_kernel",
    "discontinuity_measure",
    "local_order_parameter",
    "quick_simulate",
    "ring_topology",
    "small_world_topology",
    "strength_of_incoherence",
    "strength_of_incoherence_temporal",
]

_TWO_PI = 2.0 * math.pi


@dataclass
class SimulationResult:
    """Container for OscilloSim simulation output.

    Attributes:
        final_phase: Final oscillator phases ``(N,)`` (``torch.Tensor``).
        final_amplitude: Final oscillator amplitudes ``(N,)``.
        order_parameter: Kuramoto order parameter *r* at each recorded step.
        wall_time_s: Total simulation wall-clock time in seconds.
        n_oscillators: Number of oscillators simulated.
        n_steps: Total integration steps.
        coupling_mode: Coupling topology used.
        device: Device string. Always ``"cpu"`` in PRIN (Rust owns dispatch).
        throughput: Oscillator-steps per second.
        trajectory_phase: Phase trajectory if ``record_trajectory=True``,
            shape ``(n_record, N)``.
    """

    final_phase: Any
    final_amplitude: Any
    order_parameter: list[float] = field(default_factory=list)
    wall_time_s: float = 0.0
    n_oscillators: int = 0
    n_steps: int = 0
    coupling_mode: str = ""
    device: str = "cpu"
    throughput: float = 0.0
    trajectory_phase: Any = None


class OscilloSim:
    """Large-scale oscillator simulator with sparse coupling.

    Thin orchestration over the Rust ``oscillo_compat_run`` owner, which ports
    the PRINet 3.0 ``OscilloSim`` step equations line-for-line (mean-field,
    sparse k-NN, CSR, ring, and small-world coupling; Euler / RK4; phase lag
    ``alpha``; per-edge coupling weights). No integration math runs in Python
    (Coding Standards Sec. 1.2).

    RNG note: PRINet 3.0 seeded ``torch.Generator`` streams for the natural
    frequencies, the default initial phases, and the small-world rewiring. PRIN
    draws these from a deterministic ``prin_dynamics::Seed``; same-seed
    reproducibility holds, exact cross-implementation phase values do not.

    Args:
        n_oscillators: Total number of oscillators.
        coupling_strength: Global coupling constant *K*.
        coupling_mode: One of ``"mean_field"``, ``"sparse_knn"``, ``"csr"``,
            ``"ring"``, ``"small_world"``, or ``"auto"``.
        k_neighbors: Neighbours per oscillator for sparse / ring / small-world.
        sparsity: Sparsity level for CSR mode.
        mu: Stuart-Landau growth parameter.
        freq_mean: Mean natural frequency.
        freq_std: Standard deviation of natural frequencies.
        phase_lag: Phase lag ``alpha`` for ``sin(phi_j - phi_i - alpha)``.
        p_rewire: Rewiring probability for ``small_world`` mode.
        integrator: ``"euler"`` (default) or ``"rk4"``.
        coupling_weights: Optional per-edge weight tensor ``(N, k)`` (see
            :func:`cosine_coupling_kernel`).
        device: Accepted for signature compatibility. **Inert** — PRIN
            dispatches through Rust.
        seed: Random seed.
        dtype: Output dtype (default ``torch.float32``).

    Raises:
        ValueError: If ``n_oscillators`` < 1 or ``coupling_mode`` is unknown.
    """

    _COUPLING_MODES: ClassVar[frozenset[str]] = frozenset(
        {"mean_field", "sparse_knn", "csr", "ring", "small_world", "auto"}
    )

    def __init__(
        self,
        n_oscillators: int = 1000,
        coupling_strength: float = 2.0,
        coupling_mode: str = "auto",
        k_neighbors: int = 8,
        sparsity: float = 0.99,
        mu: float = 1.0,
        freq_mean: float = 5.0,
        freq_std: float = 0.5,
        phase_lag: float = 0.0,
        p_rewire: float = 0.1,
        integrator: str = "euler",
        coupling_weights: torch.Tensor | None = None,
        device: str = "cpu",
        seed: int = 42,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        """Validate arguments and store the simulation configuration."""
        if n_oscillators < 1:
            raise ValueError(f"n_oscillators must be >= 1, got {n_oscillators}")
        if coupling_mode not in self._COUPLING_MODES:
            raise ValueError(
                f"Unknown coupling_mode {coupling_mode!r}; "
                f"expected one of {sorted(self._COUPLING_MODES)}"
            )
        if integrator not in ("euler", "rk4"):
            raise ValueError(
                f"Unknown integrator {integrator!r}; expected euler or rk4"
            )

        self.n_oscillators = n_oscillators
        self.coupling_strength = coupling_strength
        self.k_neighbors = k_neighbors
        self.sparsity = sparsity
        self.mu = mu
        self.freq_mean = freq_mean
        self.freq_std = freq_std
        self.phase_lag = phase_lag
        self.p_rewire = p_rewire
        self.integrator = integrator
        self.seed = seed
        self.dtype = dtype
        self._device = "cuda" if "cuda" in str(device) else "cpu"
        self.coupling_weights = (
            None
            if coupling_weights is None
            else coupling_weights.detach().to(dtype=torch.float64, device="cpu")
        )

        if coupling_mode == "auto":
            if n_oscillators >= 100_000:
                self._coupling_mode = "mean_field"
            elif n_oscillators >= 1_000:
                self._coupling_mode = "sparse_knn"
            else:
                self._coupling_mode = "csr"
        else:
            self._coupling_mode = coupling_mode

    @property
    def coupling_mode(self) -> str:
        """Resolved coupling mode string."""
        return self._coupling_mode

    @property
    def device(self) -> str:
        """Configured device string."""
        return self._device

    def state_summary(self) -> dict[str, Any]:
        """Return a dict summarising the simulator configuration."""
        info: dict[str, Any] = {
            "n_oscillators": self.n_oscillators,
            "coupling_mode": self._coupling_mode,
            "coupling_strength": self.coupling_strength,
            "mu": self.mu,
            "phase_lag": self.phase_lag,
            "device": self._device,
            "dtype": str(self.dtype),
        }
        if self._coupling_mode in ("sparse_knn", "ring", "small_world"):
            info["k_neighbors"] = self.k_neighbors
            if self._coupling_mode == "small_world":
                info["p_rewire"] = self.p_rewire
        elif self._coupling_mode == "csr":
            info["sparsity"] = self.sparsity
        return info

    def run(
        self,
        n_steps: int = 100,
        dt: float = 0.01,
        record_trajectory: bool = False,
        record_interval: int = 10,
        initial_phase: torch.Tensor | None = None,
        initial_amplitude: torch.Tensor | None = None,
    ) -> SimulationResult:
        """Run the simulation for a fixed number of steps.

        Args:
            n_steps: Number of integration steps.
            dt: Timestep size.
            record_trajectory: Whether to record intermediate phases.
            record_interval: Record the order parameter (and trajectory) every
                ``record_interval`` steps; the final step is always recorded.
            initial_phase: Optional initial phases ``(N,)``. Random uniform
                ``[0, 2π)`` if not provided.
            initial_amplitude: Optional initial amplitudes ``(N,)``. Ones if
                not provided.

        Returns:
            :class:`SimulationResult` with final state and diagnostics.

        Raises:
            ValueError: If ``n_steps`` is negative or ``dt`` is not positive.
        """
        if n_steps < 0:
            raise ValueError(f"n_steps must be non-negative, got {n_steps}")
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")

        def _list(t: torch.Tensor | None) -> list[float] | None:
            if t is None:
                return None
            return t.detach().to(dtype=torch.float64, device="cpu").reshape(-1).tolist()

        weights = None
        if self.coupling_weights is not None:
            weights = self.coupling_weights.reshape(-1).tolist()

        if n_steps == 0:
            zeros = torch.zeros(self.n_oscillators, dtype=self.dtype)
            return SimulationResult(
                final_phase=zeros,
                final_amplitude=torch.ones(self.n_oscillators, dtype=self.dtype),
                order_parameter=[],
                wall_time_s=0.0,
                n_oscillators=self.n_oscillators,
                n_steps=0,
                coupling_mode=self._coupling_mode,
                device=self._device,
                throughput=0.0,
                trajectory_phase=None,
            )

        (
            final_phase,
            final_amplitude,
            order_parameter,
            wall_time_s,
            throughput,
            trajectory_phase,
        ) = _rust_oscillo_run(
            self.n_oscillators,
            float(self.coupling_strength),
            self._coupling_mode,
            int(self.k_neighbors),
            float(self.sparsity),
            float(self.mu),
            float(self.freq_mean),
            float(self.freq_std),
            float(self.phase_lag),
            float(self.p_rewire),
            self.integrator,
            int(self.seed),
            int(n_steps),
            float(dt),
            bool(record_trajectory),
            int(record_interval),
            weights,
            _list(initial_phase),
            _list(initial_amplitude),
        )

        traj = None
        if trajectory_phase is not None:
            traj = torch.tensor(trajectory_phase, dtype=self.dtype)

        return SimulationResult(
            final_phase=torch.tensor(final_phase, dtype=self.dtype),
            final_amplitude=torch.tensor(final_amplitude, dtype=self.dtype),
            order_parameter=list(order_parameter),
            wall_time_s=float(wall_time_s),
            n_oscillators=self.n_oscillators,
            n_steps=n_steps,
            coupling_mode=self._coupling_mode,
            device=self._device,
            throughput=float(throughput),
            trajectory_phase=traj,
        )


def quick_simulate(
    n_oscillators: int = 10_000,
    n_steps: int = 100,
    dt: float = 0.01,
    coupling_strength: float = 2.0,
    coupling_mode: str = "auto",
    k_neighbors: int = 8,
    integrator: str = "euler",
    record_trajectory: bool = False,
    device: str = "cpu",
    seed: int = 42,
) -> SimulationResult:
    """One-call convenience wrapper: construct an :class:`OscilloSim` and run it.

    Args:
        n_oscillators: Number of oscillators.
        n_steps: Integration steps.
        dt: Timestep.
        coupling_strength: Coupling constant *K*.
        coupling_mode: Coupling topology (default ``"auto"``).
        k_neighbors: Neighbours for sparse / ring / small-world coupling.
        integrator: ``"euler"`` or ``"rk4"``.
        record_trajectory: Whether to record intermediate phases.
        device: Accepted for signature compatibility; inert.
        seed: Random seed.

    Returns:
        :class:`SimulationResult` with final state and diagnostics.
    """
    sim = OscilloSim(
        n_oscillators=n_oscillators,
        coupling_strength=coupling_strength,
        coupling_mode=coupling_mode,
        k_neighbors=k_neighbors,
        integrator=integrator,
        device=device,
        seed=seed,
    )
    return sim.run(n_steps=n_steps, dt=dt, record_trajectory=record_trajectory)


# =========================================================================
# Cosine coupling kernel (Abrams & Strogatz nonlocal coupling)
# =========================================================================


def cosine_coupling_kernel(
    n: int,
    k: int,
    A: float = 0.995,
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """Per-edge cosine coupling weights for a ring topology.

    Delegates the ``G(d) = (1 + A·cos(2π d / n)) / 2π`` weight row to the Rust
    ``cosine_coupling_kernel_row`` owner and broadcasts it to ``(N, k)``.

    Args:
        n: Number of oscillators.
        k: Neighbours per oscillator (as in the ring topology).
        A: Asymmetry parameter in ``[0, 1]``.
        device: Device string.
        dtype: Tensor dtype.

    Returns:
        Tensor of shape ``(n, k)`` with normalised coupling weights (rows
        sum to ``1``).
    """
    row = _rust_cosine_kernel(int(n), int(k), float(A))
    return (
        torch.tensor(row, dtype=dtype, device=device)
        .unsqueeze(0)
        .expand(n, -1)
        .contiguous()
    )


# =========================================================================
# Chimera-state detection metrics (Rust ``prin_metrics`` owners)
# =========================================================================


def _phase_1d_f64(phase: torch.Tensor) -> list[float]:
    """Marshal a 1-D phase tensor to a Python float64 list."""
    return phase.detach().to(dtype=torch.float64, device="cpu").reshape(-1).tolist()


def _neighbor_lists(nbr_idx: torch.Tensor) -> list[list[int]]:
    """Marshal an ``(N, k)`` neighbour-index tensor to a list of rows."""
    return [[int(j) for j in row] for row in nbr_idx.detach().cpu().tolist()]


def local_order_parameter(phase: torch.Tensor, nbr_idx: torch.Tensor) -> torch.Tensor:
    """Local Kuramoto order parameter for each oscillator.

    Args:
        phase: Oscillator phases ``(N,)``.
        nbr_idx: Neighbour indices ``(N, k)`` from a ring / small-world
            topology.

    Returns:
        Local order parameter ``(N,)`` in ``[0, 1]`` (float32 tensor).
    """
    import numpy as np

    r = _rust_local_order_parameter(
        np.asarray(_phase_1d_f64(phase), dtype=np.float64), _neighbor_lists(nbr_idx)
    )
    return torch.as_tensor(r, dtype=torch.float32, device=phase.device)


def bimodality_index(values: torch.Tensor) -> float:
    """Sarle's bimodality coefficient of a 1-D tensor.

    Args:
        values: 1-D tensor (e.g. local order parameters).

    Returns:
        Bimodality coefficient (``BC > 5/9`` suggests bimodality).
    """
    import numpy as np

    return float(
        _rust_bimodality_index(np.asarray(_phase_1d_f64(values), dtype=np.float64))
    )


def strength_of_incoherence(phase: torch.Tensor, window_size: int = 10) -> torch.Tensor:
    """Strength of Incoherence (SI) of a phase snapshot (Gopal et al. 2014).

    Args:
        phase: Phase vector ``(N,)`` (radians).
        window_size: Spatial smoothing window.

    Returns:
        Scalar SI value in ``[0, 1]`` (float tensor).
    """
    import numpy as np

    si = _rust_strength_of_incoherence(
        np.asarray(_phase_1d_f64(phase), dtype=np.float64), int(window_size)
    )
    return torch.tensor(float(si))


def discontinuity_measure(
    phase: torch.Tensor, threshold_ratio: float = 0.01
) -> tuple[torch.Tensor, int]:
    """Discontinuity measure (chimera number ``η``) of a phase snapshot.

    Args:
        phase: Phase vector ``(N,)`` (radians).
        threshold_ratio: Fraction of ``2π`` used as the incoherence threshold.

    Returns:
        Tuple ``(coherent_mask, eta)`` — a bool tensor ``(N,)`` and the
        chimera number.
    """
    import numpy as np

    mask, eta = _rust_discontinuity_measure(
        np.asarray(_phase_1d_f64(phase), dtype=np.float64), float(threshold_ratio)
    )
    return torch.tensor(list(mask), dtype=torch.bool), int(eta)


def chimera_index(
    phase: torch.Tensor, nbr_idx: torch.Tensor, threshold: float = 0.5
) -> float:
    """Chimera index ``χ ∈ [0, 1]`` — fraction of incoherent oscillators.

    Args:
        phase: Phase vector ``(N,)`` (radians).
        nbr_idx: Neighbour index tensor ``(N, k)``.
        threshold: Local order parameter cutoff for incoherence.

    Returns:
        Chimera index as a float.
    """
    import numpy as np

    return float(
        _rust_chimera_index(
            np.asarray(_phase_1d_f64(phase), dtype=np.float64),
            _neighbor_lists(nbr_idx),
            float(threshold),
        )
    )


def strength_of_incoherence_temporal(
    trajectory: torch.Tensor,
    window_size: int = 10,
    discard_transient: int = 0,
) -> float:
    """Time-averaged Strength of Incoherence over a phase trajectory.

    Args:
        trajectory: Phase trajectory ``(T, N)``.
        window_size: Spatial smoothing window.
        discard_transient: Number of initial snapshots to discard.

    Returns:
        Mean SI value (float).
    """
    frames = [
        row
        for row in trajectory.detach().to(dtype=torch.float64, device="cpu").tolist()
    ]
    return float(
        _rust_strength_of_incoherence_temporal(
            frames, int(window_size), int(discard_transient)
        )
    )


def _raise_disposition(symbol: str, detail: str) -> Any:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


class LargeScaleOscillatorSystem:
    """Large-scale oscillator system with sparse k-NN coupling.

    PRINet 3.0 ``utils.fused_kernels.LargeScaleOscillatorSystem``: pure
    orchestration over the existing Rust-backed kernels
    (:func:`prin.kernels.build_knn_neighbors`,
    :func:`prin.kernels.sparse_knn_coupling_step`).  All numerics run in Rust;
    this class only manages the neighbor graph and the integration loop.

    Args:
        n_oscillators: Number of oscillators.
        k_neighbors: Number of k-NN neighbors per oscillator.
        seed: Random seed for neighbor construction.
        coupling_strength: Scalar coupling weight.
    """

    def __init__(
        self,
        n_oscillators: int = 100,
        k_neighbors: int = 8,
        *,
        seed: int = 42,
        coupling_strength: float = 2.0,
    ) -> None:
        self.n_oscillators = n_oscillators
        self.k_neighbors = k_neighbors
        self.seed = seed
        self.coupling_strength = coupling_strength
        self._device = "cpu"
        self._neighbors: torch.Tensor | None = None

    def to(self, device: Any) -> LargeScaleOscillatorSystem:
        """Move the system to the given device."""
        dev = str(device)
        self._device = "cuda" if "cuda" in dev else "cpu"
        self._neighbors = None
        return self

    def _ensure_neighbors(self) -> torch.Tensor:
        """Build the k-NN neighbor graph on the current device."""
        if self._neighbors is None:
            from prin.kernels import build_knn_neighbors

            self._neighbors = build_knn_neighbors(
                self.n_oscillators, self.k_neighbors, seed=self.seed
            ).to(self._device)
        return self._neighbors

    def step(
        self,
        phase: torch.Tensor,
        amp: torch.Tensor,
        dt: float = 0.01,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance one discrete step with sparse k-NN coupling."""
        from prin.kernels import sparse_knn_coupling_step

        nbr = self._ensure_neighbors()
        if nbr.device != phase.device:
            nbr = nbr.to(phase.device)
        coupling = sparse_knn_coupling_step(
            phase, amp, nbr, coupling_strength=self.coupling_strength
        )
        new_p = (phase + coupling * dt) % _TWO_PI
        new_a = amp.clamp(1e-6, 10.0)
        return new_p, new_a

    def integrate(
        self,
        phase: torch.Tensor,
        amp: torch.Tensor,
        n_steps: int = 10,
        dt: float = 0.01,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance *n_steps* discrete steps."""
        for _ in range(n_steps):
            phase, amp = self.step(phase, amp, dt=dt)
        return phase, amp


class OscillatorPruner:
    """Amplitude-threshold oscillator pruner.

    PRINet 3.0 ``utils.fused_kernels.OscillatorPruner``: pure Python analysis
    over mean amplitudes — no numerics beyond ``torch.mean`` and comparisons.

    Args:
        threshold: Amplitude threshold below which an oscillator is inactive.
        n_eval_steps: Number of evaluation steps (stored, not used in analyze).
    """

    def __init__(
        self,
        threshold: float = 0.1,
        n_eval_steps: int = 20,
    ) -> None:
        self.threshold = threshold
        self.n_eval_steps = n_eval_steps

    def analyze(
        self,
        dynamics: Any,
        phase: torch.Tensor,
        amp: torch.Tensor,
    ) -> dict[str, Any]:
        """Produce pruning statistics from the current amplitude snapshot."""
        mean_amps = amp.mean(dim=0)
        active = mean_amps >= self.threshold
        n_total = phase.shape[-1]
        n_active = int(active.sum().item())
        n_inactive = n_total - n_active
        return {
            "n_total": n_total,
            "n_active": n_active,
            "n_inactive": n_inactive,
            "active_mask": active,
            "mean_amplitudes": mean_amps,
            "reduction_pct": n_inactive / n_total if n_total else 0.0,
        }

    def prune_indices(
        self,
        dynamics: Any,
        phase: torch.Tensor,
        amp: torch.Tensor,
        nd: int,
        nt: int,
        ng: int,
    ) -> dict[str, Any]:
        """Per-band active/inactive index breakdown."""
        mean_amps = amp.mean(dim=0)
        active = mean_amps >= self.threshold
        delta_active = active[:nd].tolist()
        theta_active = active[nd : nd + nt].tolist()
        gamma_active = active[nd + nt : nd + nt + ng].tolist()
        total_pruned = int((~active).sum().item())
        n_total = phase.shape[-1]
        return {
            "delta_active": delta_active,
            "theta_active": theta_active,
            "gamma_active": gamma_active,
            "total_pruned": total_pruned,
            "reduction_pct": total_pruned / n_total if n_total else 0.0,
        }

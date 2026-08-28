"""PRINet 3.0-compatible oscillator simulation surface.

This module is the thin Python compatibility layer for the PRINet 3.0
``prinet.utils.oscillosim`` simulation family (``OscilloSim``,
``SimulationResult``, ``quick_simulate``). It performs orchestration only --
argument adaptation, model selection, and result marshalling. Every numerical
result is owned by the Rust integrators and models exposed through
:mod:`prin.dynamics` and :mod:`prin.metrics`; no integration math runs in
Python (Coding Standards Sec. 1.2).

Symbols with no faithful non-numeric implementation (``LargeScaleOscillatorSystem``,
``OscillatorPruner``) are documented D-2.2 stubs raising a typed error with a
Migration-Guide row.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, ClassVar, NoReturn

import numpy as np

from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    RK45Integrator,
    StuartLandauOscillator,
)
from prin.metrics import kuramoto_order_parameter

__all__ = [
    "LargeScaleOscillatorSystem",
    "OscillatorPruner",
    "OscilloSim",
    "SimulationResult",
    "quick_simulate",
]


@dataclass
class SimulationResult:
    """Container for OscilloSim simulation output.

    Attributes:
        final_phase: Final oscillator phases ``(N,)``.
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

    final_phase: np.ndarray
    final_amplitude: np.ndarray
    order_parameter: list[float] = field(default_factory=list)
    wall_time_s: float = 0.0
    n_oscillators: int = 0
    n_steps: int = 0
    coupling_mode: str = ""
    device: str = "cpu"
    throughput: float = 0.0
    trajectory_phase: np.ndarray | None = None


class OscilloSim:
    """Large-scale oscillator simulator with sparse coupling.

    Thin orchestration over existing PRIN Rust owners:
    :class:`~prin.dynamics.KuramotoOscillator` (or
    :class:`~prin.dynamics.StuartLandauOscillator`) for the dynamics model,
    :class:`~prin.dynamics.RK4Integrator` / :class:`~prin.dynamics.RK45Integrator`
    for time-stepping, and :func:`~prin.metrics.kuramoto_order_parameter` for
    diagnostics. No integration math runs in Python (Coding Standards Sec. 1.2).

    Args:
        n_oscillators: Total number of oscillators.
        coupling_strength: Global coupling constant *K*.
        coupling_mode: One of ``"mean_field"``, ``"sparse_knn"``, or
            ``"auto"``. PRINet 3.0 also accepted ``"csr"``, ``"ring"``,
            ``"small_world"``; these are mapped to ``"sparse_knn"`` with the
            appropriate neighbour count (Migration Guide D1).
        k_neighbors: Number of neighbours for sparse coupling.
        mu: Stuart-Landau growth rate. When non-zero the simulator uses
            :class:`~prin.dynamics.StuartLandauOscillator` instead of
            :class:`~prin.dynamics.KuramotoOscillator`.
        freq_mean: Mean natural frequency.
        freq_std: Standard deviation of natural frequencies (advisory; the
            Rust model owns frequency assignment).
        phase_lag: Phase lag alpha for coupling.
        integrator: ``"rk4"`` (default) or ``"rk45"``.
        device: Accepted for signature compatibility. **Inert** -- PRIN
            dispatches through Rust.

    Raises:
        ValueError: If ``n_oscillators`` < 1 or ``coupling_mode`` is unknown.

    Example:
        >>> sim = OscilloSim(64, coupling_strength=2.0, coupling_mode="mean_field")
        >>> result = sim.run(n_steps=100, dt=0.01)
        >>> result.n_oscillators
        64
    """

    _COUPLING_MODES: ClassVar[frozenset[str]] = frozenset(
        {
            "mean_field",
            "sparse_knn",
            "csr",
            "ring",
            "small_world",
            "auto",
        }
    )

    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float = 1.0,
        coupling_mode: str = "mean_field",
        k_neighbors: int = 8,
        mu: float = 0.0,
        freq_mean: float = 5.0,
        freq_std: float = 1.0,
        phase_lag: float = 0.0,
        integrator: str = "rk4",
        device: str = "cpu",
    ) -> None:
        """Validate arguments and store the simulation configuration."""
        if n_oscillators < 1:
            raise ValueError(f"n_oscillators must be >= 1, got {n_oscillators}")
        if coupling_mode not in self._COUPLING_MODES:
            raise ValueError(
                f"Unknown coupling_mode {coupling_mode!r}; "
                f"expected one of {sorted(self._COUPLING_MODES)}"
            )
        self._n = n_oscillators
        self._K = coupling_strength
        self._mode = coupling_mode
        self._k = k_neighbors
        self._mu = mu
        self._freq_mean = freq_mean
        self._freq_std = freq_std
        self._phase_lag = phase_lag
        self._integrator = integrator
        self._device = device

    def _build_model(self) -> KuramotoOscillator | StuartLandauOscillator:
        """Construct the appropriate Rust-backed dynamics model."""
        resolved = self._mode
        if resolved in ("csr", "ring", "small_world", "auto"):
            resolved = "sparse_knn" if self._n >= 2 else "mean_field"

        if resolved == "mean_field":
            mode = CouplingMode.mean_field()
        else:
            mode = CouplingMode.sparse_knn(self._k)

        if self._mu != 0.0:
            return StuartLandauOscillator(self._n, self._K, self._mu, mode)
        return KuramotoOscillator(self._n, self._K, 0.1, self._freq_mean, mode)

    @staticmethod
    def _initial_state(n: int, freq_mean: float) -> OscillatorState:
        """Build a uniform initial state."""
        phase = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        amplitude = np.ones(n)
        frequency = np.full(n, freq_mean)
        return OscillatorState(phase, amplitude, frequency)

    def run(
        self,
        n_steps: int = 1000,
        dt: float = 0.01,
        record_trajectory: bool = False,
        initial_state: OscillatorState | None = None,
    ) -> SimulationResult:
        """Run the simulation for a fixed number of steps.

        Args:
            n_steps: Number of integration steps.
            dt: Timestep size.
            record_trajectory: Whether to record intermediate phases.
            initial_state: Optional custom initial state. If ``None``, a
                uniform phase / unit-amplitude state is constructed.

        Returns:
            :class:`SimulationResult` with final state and diagnostics.

        Raises:
            ValueError: If ``n_steps`` is negative or ``dt`` is not positive.
        """
        if n_steps < 0:
            raise ValueError(f"n_steps must be non-negative, got {n_steps}")
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")

        model = self._build_model()
        state = initial_state or self._initial_state(self._n, self._freq_mean)

        start = time.perf_counter()
        if self._integrator == "rk45":
            integrator = RK45Integrator(rtol=1e-6, atol=1e-8, max_steps=n_steps * 4)
            span = n_steps * dt
            result = integrator.integrate_adaptive(
                model, state, span, dt, record_trajectory
            )
            final = result.final_state
            traj = result.trajectory
            steps = result.accepted_steps
        else:
            final, traj = RK4Integrator().integrate_fixed(
                model, state, n_steps, dt, record_trajectory
            )
            steps = n_steps
        wall_time = time.perf_counter() - start

        order_params: list[float] = []
        traj_phase: np.ndarray | None = None
        if record_trajectory and traj:
            order_params = [float(kuramoto_order_parameter(s.phase)) for s in traj]
            traj_phase = np.stack([s.phase for s in traj])

        throughput = (self._n * steps) / wall_time if wall_time > 0 else 0.0

        return SimulationResult(
            final_phase=final.phase.copy(),
            final_amplitude=final.amplitude.copy(),
            order_parameter=order_params,
            wall_time_s=wall_time,
            n_oscillators=self._n,
            n_steps=steps,
            coupling_mode=self._mode,
            device=self._device,
            throughput=throughput,
            trajectory_phase=traj_phase,
        )


def quick_simulate(
    n_oscillators: int,
    n_steps: int = 1000,
    dt: float = 0.01,
    coupling_strength: float = 1.0,
    coupling_mode: str = "mean_field",
    k_neighbors: int = 8,
    integrator: str = "rk4",
    record_trajectory: bool = False,
) -> SimulationResult:
    """One-call convenience function for oscillator simulation.

    Constructs an :class:`OscilloSim` and runs it in a single call.

    Args:
        n_oscillators: Number of oscillators.
        n_steps: Integration steps.
        dt: Timestep.
        coupling_strength: Coupling constant *K*.
        coupling_mode: Coupling topology.
        k_neighbors: Neighbours for sparse coupling.
        integrator: ``"rk4"`` or ``"rk45"``.
        record_trajectory: Whether to record intermediate phases.

    Returns:
        :class:`SimulationResult` with final state and diagnostics.

    Example:
        >>> result = quick_simulate(32, n_steps=50, coupling_mode="mean_field")
        >>> result.n_oscillators
        32
    """
    sim = OscilloSim(
        n_oscillators,
        coupling_strength=coupling_strength,
        coupling_mode=coupling_mode,
        k_neighbors=k_neighbors,
        integrator=integrator,
    )
    return sim.run(
        n_steps=n_steps,
        dt=dt,
        record_trajectory=record_trajectory,
    )


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


class LargeScaleOscillatorSystem:
    """Deferred-rebuild stub for the 1M+ oscillator system class.

    PRINet 3.0 symbol with no faithful non-numeric implementation in WP-036.
    The Rust owner (``prin_sim::engine::OscilloSim``) exists but has no PyO3
    binding; a future WP will add the binding or a pure-Python orchestration
    over the existing :class:`OscilloSim` wrapper for the 1M+ scale.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "LargeScaleOscillatorSystem",
            "The prin-sim Rust engine exists but is not yet bound to Python.",
        )


class OscillatorPruner:
    """Deferred-rebuild stub for the amplitude-threshold oscillator pruner.

    PRINet 3.0 symbol with no faithful non-numeric implementation in WP-036.
    The Rust owner (``prin_sim::pruning::PruningStrategy``) exists but has no
    PyO3 binding; a future WP will add the binding.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "OscillatorPruner",
            "The prin-sim Rust pruning owner exists but is not yet bound.",
        )

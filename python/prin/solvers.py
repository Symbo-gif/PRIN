"""PRINet 3.0-compatible ODE solver surface over the Rust integrator owners.

This module is the thin Python compatibility layer for the PRINet 3.0
``prinet.utils.cuda_kernels`` solver family (``BatchedRK45Solver``,
``FixedStepRK4Solver``, ``SolverResult``, ``gradient_checkpoint_integration``).
It performs orchestration only -- argument adaptation, result marshalling, and
timing. Every numerical result is owned by the Rust integrators exposed through
:mod:`prin.dynamics` (:class:`~prin.dynamics.RK45Integrator`,
:class:`~prin.dynamics.RK4Integrator`); no integration math runs in Python
(Coding Standards Sec. 1.2).

Behavioural parity against PRINet 3.0 is **not** established here -- it is a
WP-036B/WP-036C acceptance-suite obligation. See the Migration Guide
"sub-pass 0141D1" section for the per-symbol adaptation notes.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from prin.dynamics import OscillatorState, RK4Integrator, RK45Integrator

__all__ = [
    "BatchedRK45Solver",
    "FixedStepRK4Solver",
    "SolverError",
    "SolverResult",
    "gradient_checkpoint_integration",
]

# The Rust integrators accept any object exposing ``compute_derivatives``; the
# PRINet 3.0 signatures name this ``OscillatorModel``. ``object`` keeps
# ``mypy --strict`` honest without importing the structural protocol here.
_Model = object


class SolverError(RuntimeError):
    """Raised when the ODE solver fails to converge or reach ``t_end``.

    PRIN adaptation: the underlying Rust integrator raises ``ValueError`` when
    it cannot meet tolerance within its step budget; the solver wrappers
    re-raise that as ``SolverError`` to preserve the PRINet 3.0 contract.
    """


@dataclass
class SolverResult:
    """Container for ODE solver results and diagnostics.

    Attributes:
        final_state: The oscillator state at the end of integration.
        n_steps_taken: Actual number of integration steps performed. For the
            adaptive solver this is the count of *accepted* steps.
        n_function_evals: Number of derivative evaluations made. This is a
            stage-count estimate (RK4: ``4 * n_steps``; RK45: ``6`` stages per
            attempted step) because the Rust integrators do not surface an
            exact evaluation counter.
        final_dt: The last timestep size used (for adaptive methods).
        wall_time_seconds: Wall-clock time for the solve.
        trajectory: Optional list of intermediate states, populated only when
            ``record_trajectory=True`` is passed to ``solve``.
    """

    final_state: OscillatorState
    n_steps_taken: int
    n_function_evals: int
    final_dt: float
    wall_time_seconds: float
    trajectory: list[OscillatorState] | None = field(default=None)


class BatchedRK45Solver:
    """Adaptive-step Runge-Kutta-Fehlberg (RK45) ODE solver.

    Thin wrapper over :class:`prin.dynamics.RK45Integrator` (Rust
    Dormand-Prince with adaptive step-size control). The PRINet 3.0 class
    re-implemented the Butcher tableau in PyTorch; PRIN delegates every step to
    the audited Rust owner.

    Args:
        atol: Absolute error tolerance passed to the Rust integrator.
        rtol: Relative error tolerance passed to the Rust integrator.
        min_dt: Minimum timestep. **Advisory only** -- the Rust integrator
            owns step-size control; retained for signature compatibility.
        max_dt: Maximum timestep. Used to seed the initial step
            (``min(max_dt, span / 10)``); otherwise advisory.
        safety_factor: PRINet 3.0 step-adaptation safety factor. **Advisory
            only**; the Rust controller uses its own constants.
        max_step_increase: PRINet 3.0 step-growth cap. **Advisory only.**
        compiled: Accepted for signature compatibility. **Inert** -- PRIN
            dispatches through Rust, not ``torch.compile``.

    Raises:
        ValueError: If ``atol`` or ``rtol`` is not positive.

    Example:
        >>> import numpy as np
        >>> from prin.dynamics import (
        ...     CouplingMode, KuramotoOscillator, OscillatorState,
        ... )
        >>> solver = BatchedRK45Solver(atol=1e-6, rtol=1e-4)
        >>> model = KuramotoOscillator(64, 2.0, 0.1, 0.0, CouplingMode.mean_field())
        >>> n = 64
        >>> state = OscillatorState(
        ...     np.linspace(0.0, 1.0, n), np.ones(n), np.full(n, 5.0)
        ... )
        >>> result = solver.solve(model, state, t_span=(0.0, 1.0))
        >>> result.n_steps_taken > 0
        True
    """

    def __init__(
        self,
        atol: float = 1e-6,
        rtol: float = 1e-4,
        min_dt: float = 1e-8,
        max_dt: float = 1.0,
        safety_factor: float = 0.9,
        max_step_increase: float = 5.0,
        compiled: bool = False,
    ) -> None:
        """Store solver tolerances and advisory step-control settings."""
        if atol <= 0:
            raise ValueError(f"atol must be positive, got {atol}")
        if rtol <= 0:
            raise ValueError(f"rtol must be positive, got {rtol}")
        self._atol = atol
        self._rtol = rtol
        self._min_dt = min_dt
        self._max_dt = max_dt
        self._safety = safety_factor
        self._max_increase = max_step_increase
        self._compiled = compiled

    def solve(
        self,
        model: _Model,
        initial_state: OscillatorState,
        t_span: tuple[float, float] = (0.0, 1.0),
        max_steps: int = 10000,
        record_trajectory: bool = False,
    ) -> SolverResult:
        """Solve the ODE system using adaptive RK45.

        Args:
            model: Oscillator dynamics model exposing ``compute_derivatives``
                (e.g. :class:`prin.dynamics.KuramotoOscillator`).
            initial_state: Initial oscillator state.
            t_span: ``(t_start, t_end)`` integration interval.
            max_steps: Maximum number of adaptive steps before giving up.
            record_trajectory: If ``True``, record all accepted intermediate
                states in ``SolverResult.trajectory``.

        Returns:
            :class:`SolverResult` with the final state and diagnostics.

        Raises:
            SolverError: If the Rust integrator cannot reach ``t_end`` within
                ``max_steps``.
        """
        t_start, t_end = t_span
        span = t_end - t_start
        dt_init = min(self._max_dt, span / 10.0) if span > 0 else self._max_dt
        integrator = RK45Integrator(
            rtol=self._rtol, atol=self._atol, max_steps=max_steps
        )

        start = time.perf_counter()
        try:
            result = integrator.integrate_adaptive(
                model, initial_state, span, dt_init, record_trajectory
            )
        except ValueError as exc:
            raise SolverError(str(exc)) from exc
        wall_time = time.perf_counter() - start

        attempted = result.accepted_steps + result.rejected_steps
        return SolverResult(
            final_state=result.final_state,
            n_steps_taken=result.accepted_steps,
            n_function_evals=attempted * 6,
            final_dt=result.final_dt,
            wall_time_seconds=wall_time,
            trajectory=result.trajectory,
        )


class FixedStepRK4Solver:
    """Fixed-step RK4 solver.

    Thin wrapper over :class:`prin.dynamics.RK4Integrator`. Simpler and faster
    than adaptive RK45 when the required timestep is known in advance.

    Args:
        dt: Fixed timestep size.
        compiled: Accepted for signature compatibility. **Inert** -- PRIN
            dispatches through Rust, not ``torch.compile``.

    Raises:
        ValueError: If ``dt`` is not positive.

    Example:
        >>> import numpy as np
        >>> from prin.dynamics import (
        ...     CouplingMode, KuramotoOscillator, OscillatorState,
        ... )
        >>> solver = FixedStepRK4Solver(dt=0.01)
        >>> model = KuramotoOscillator(32, 2.0, 0.1, 0.0, CouplingMode.mean_field())
        >>> n = 32
        >>> state = OscillatorState(
        ...     np.linspace(0.0, 1.0, n), np.ones(n), np.full(n, 5.0)
        ... )
        >>> result = solver.solve(model, state, n_steps=50)
        >>> result.n_steps_taken
        50
    """

    def __init__(self, dt: float = 0.01, compiled: bool = False) -> None:
        """Store the fixed timestep and the inert ``compiled`` flag."""
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
        self._dt = dt
        self._compiled = compiled

    def solve(
        self,
        model: _Model,
        initial_state: OscillatorState,
        n_steps: int = 1000,
        record_trajectory: bool = False,
    ) -> SolverResult:
        """Integrate the ODE system for a fixed number of steps.

        Args:
            model: Oscillator dynamics model exposing ``compute_derivatives``.
            initial_state: Initial state.
            n_steps: Number of integration steps.
            record_trajectory: Whether to record intermediate states.

        Returns:
            :class:`SolverResult` with the final state and diagnostics.

        Raises:
            ValueError: If ``n_steps`` is negative.
        """
        if n_steps < 0:
            raise ValueError(f"n_steps must be non-negative, got {n_steps}")

        start = time.perf_counter()
        final_state, trajectory = RK4Integrator().integrate_fixed(
            model, initial_state, n_steps, self._dt, record_trajectory
        )
        wall_time = time.perf_counter() - start

        return SolverResult(
            final_state=final_state,
            n_steps_taken=n_steps,
            n_function_evals=n_steps * 4,
            final_dt=self._dt,
            wall_time_seconds=wall_time,
            trajectory=trajectory,
        )


def gradient_checkpoint_integration(
    model: _Model,
    state: OscillatorState,
    n_steps: int,
    dt: float = 0.01,
    checkpoint_every: int = 10,
    memory_budget_mb: float | None = None,
) -> OscillatorState:
    """Segmented fixed-step RK4 integration (PRINet 3.0 checkpointing shim).

    The integration is split into segments of ``checkpoint_every`` steps, each
    advanced by the Rust :class:`~prin.dynamics.RK4Integrator`. The final state
    is identical (bit-for-bit) to an un-segmented
    ``RK4Integrator().integrate_fixed`` call of the same length.

    Deliberate deviation (Migration Guide, sub-pass 0141D1): PRINet 3.0 wrapped
    each segment in ``torch.utils.checkpoint`` to trade compute for autograd
    memory during training. PRIN's compatibility integrator surface operates on
    NumPy-backed :class:`~prin.dynamics.OscillatorState` and is **not** a
    ``torch.autograd.Function``, so there is no autograd graph to checkpoint --
    the segmentation here only bounds Python-side peak state retention. For
    gradient-carrying oscillator integration use the
    :class:`prin.nn.ResonanceLayer` autograd bridge instead.

    Args:
        model: Oscillator dynamics model exposing ``compute_derivatives``.
        state: Initial state.
        n_steps: Total number of integration steps. Must be non-negative.
        dt: Timestep size.
        checkpoint_every: Steps per segment. Must be positive.
        memory_budget_mb: If given, the segment length is derived once from the
            square-root heuristic ``max(1, int(sqrt(n_steps)))`` (the PRINet 3.0
            GPU-memory ratio term is unavailable on the CPU path and is treated
            as 1).

    Returns:
        Final oscillator state after integration.

    Raises:
        ValueError: If ``n_steps`` is negative or ``checkpoint_every`` is not
            positive.

    Example:
        >>> import numpy as np
        >>> from prin.dynamics import (
        ...     CouplingMode, KuramotoOscillator, OscillatorState,
        ... )
        >>> model = KuramotoOscillator(16, 2.0, 0.1, 0.0, CouplingMode.mean_field())
        >>> n = 16
        >>> s0 = OscillatorState(
        ...     np.linspace(0.0, 1.0, n), np.ones(n), np.full(n, 5.0)
        ... )
        >>> final = gradient_checkpoint_integration(model, s0, n_steps=20)
        >>> final.n_oscillators
        16
    """
    if n_steps < 0:
        raise ValueError(f"n_steps must be non-negative, got {n_steps}")
    if checkpoint_every <= 0:
        raise ValueError(f"checkpoint_every must be positive, got {checkpoint_every}")

    segment = checkpoint_every
    if memory_budget_mb is not None:
        segment = max(1, int(math.sqrt(max(n_steps, 1))))

    integrator = RK4Integrator()
    current = state
    remaining = n_steps
    while remaining > 0:
        seg_steps = min(segment, remaining)
        current, _ = integrator.integrate_fixed(model, current, seg_steps, dt, False)
        remaining -= seg_steps

    return current

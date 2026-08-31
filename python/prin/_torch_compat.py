"""Internal Torch compatibility facade for strict PRINet 3.0 acceptance ports.

The facade performs tensor/state marshalling and orchestration only. Numerical
work is delegated to the compiled Rust owners in :mod:`prin._prin_core`.
"""

from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, cast

import numpy as np
import torch
from torch.utils.dlpack import from_dlpack

from prin import _prin_core as _core
from prin.kernels import sparse_coupling_matrix as _sparse_coupling_matrix
from prin.tensor import CPDecomposition as CPDecomposition
from prin.tensor import DecompositionError as DecompositionError
from prin.tensor import DimensionsMismatchError as DimensionsMismatchError
from prin.tensor import PolyadicTensor as PolyadicTensor
from prin.tensor import TensorDecompositionBase as TensorDecompositionBase


def sparse_coupling_matrix(
    n_oscillators: int,
    sparsity: float = 0.9,
    coupling_strength: float = 1.0,
    symmetric: bool = True,
    device: torch.device | str | None = None,
    dtype: torch.dtype = torch.float32,
    seed: int | _core.Seed | None = None,
) -> torch.Tensor:
    """Validate legacy arguments and delegate random draws to Rust."""
    if not 0.0 <= sparsity < 1.0:
        raise ValueError(f"sparsity must be in [0, 1), got {sparsity}")
    return _sparse_coupling_matrix(
        n_oscillators,
        sparsity,
        coupling_strength,
        symmetric,
        device,
        dtype,
        seed,
    )


class OscillatorSyncError(Exception):
    """Report an unsafe oscillator synchronization state."""


class SolverError(RuntimeError):
    """Report failure of a Rust-backed compatibility solver."""


def _numpy(tensor: torch.Tensor) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Marshal a tensor to contiguous CPU float64 storage."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous().numpy()


def _tensor(value: object, like: torch.Tensor) -> torch.Tensor:
    """Marshal a Rust/Python value to the dtype and device of ``like``."""
    return torch.as_tensor(value, dtype=like.dtype, device=like.device)


def _rows(tensor: torch.Tensor) -> list[torch.Tensor]:
    """Return one-dimensional rows without changing their values."""
    return [tensor] if tensor.dim() == 1 else list(tensor.unbind(0))


def _stack(values: list[torch.Tensor], template: torch.Tensor) -> torch.Tensor:
    """Restore scalar/unbatched versus batched result shape."""
    return values[0] if template.dim() == 1 else torch.stack(values)


def _safe_phase_diff(phi_j: torch.Tensor, phi_i: torch.Tensor) -> torch.Tensor:
    """Delegate elementwise wrapped phase differences to ``prin-dynamics``."""
    a = phi_j.detach().to(dtype=torch.float64, device="cpu").contiguous()
    b = phi_i.detach().to(dtype=torch.float64, device="cpu").contiguous()
    return from_dlpack(_core.safe_phase_diffs_dlpack(a, b)).to(
        dtype=phi_j.dtype, device=phi_j.device
    )


def _clamp_finite(tensor: torch.Tensor, limit: float = 1e4) -> torch.Tensor:
    """Delegate finite-value repair and symmetric clamping to Rust."""
    value = tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()
    return from_dlpack(_core.clamp_finite_dlpack(value, limit)).to(
        dtype=tensor.dtype, device=tensor.device
    )


def _build_phase_knn_index(flat_phase: torch.Tensor, k: int) -> torch.Tensor:
    """Build batched phase-neighbour indices through the Rust metric owner."""
    rows = [
        torch.as_tensor(
            np.stack(_core.build_phase_knn(_numpy(row), k)),
            dtype=torch.long,
            device=flat_phase.device,
        )
        for row in _rows(flat_phase)
    ]
    return torch.stack(rows)


@dataclass
class OscillatorState:
    """Torch-facing oscillator state marshalled to Rust at call boundaries."""

    phase: torch.Tensor
    amplitude: torch.Tensor
    frequency: torch.Tensor
    freq_band: torch.Tensor | None = None

    @property
    def n_oscillators(self) -> int:
        """Return the oscillator count on the final axis."""
        return int(self.phase.shape[-1])

    @property
    def n_bands(self) -> int:
        """Return the number of distinct optional frequency-band labels."""
        if self.freq_band is None:
            return 0
        return int(torch.unique(self.freq_band).numel())

    def clone(self) -> OscillatorState:
        """Return an independent state copy."""
        return OscillatorState(
            self.phase.clone(),
            self.amplitude.clone(),
            self.frequency.clone(),
            None if self.freq_band is None else self.freq_band.clone(),
        )

    @staticmethod
    def create_random(
        n_oscillators: int,
        batch_size: int | None = None,
        freq_range: tuple[float, float] = (0.1, 10.0),
        device: torch.device | str | None = None,
        dtype: torch.dtype = torch.float32,
        seed: int | None = None,
    ) -> OscillatorState:
        """Create deterministic random state through ``prin-dynamics::Seed``."""
        authority = _core.Seed(0 if seed is None else seed, 0)
        count = 1 if batch_size is None else batch_size
        states = [
            _core.OscillatorState.create_random(n_oscillators, freq_range, authority)
            for _ in range(count)
        ]
        phase = torch.as_tensor(
            np.stack([state.phase for state in states]), dtype=dtype, device=device
        )
        amplitude = torch.as_tensor(
            np.stack([state.amplitude for state in states]), dtype=dtype, device=device
        )
        frequency = torch.as_tensor(
            np.stack([state.frequency for state in states]), dtype=dtype, device=device
        )
        if batch_size is None:
            phase, amplitude, frequency = phase[0], amplitude[0], frequency[0]
        return OscillatorState(phase, amplitude, frequency)

    @staticmethod
    def create_synchronized(
        n_oscillators: int,
        base_frequency: float = 1.0,
        batch_size: int | None = None,
        device: torch.device | str | None = None,
        dtype: torch.dtype = torch.float32,
    ) -> OscillatorState:
        """Create synchronized state through the Rust state owner."""
        raw = _core.OscillatorState.create_synchronized(n_oscillators, base_frequency)
        phase = torch.as_tensor(raw.phase, dtype=dtype, device=device)
        amplitude = torch.as_tensor(raw.amplitude, dtype=dtype, device=device)
        frequency = torch.as_tensor(raw.frequency, dtype=dtype, device=device)
        if batch_size is not None:
            phase = phase.expand(batch_size, -1).clone()
            amplitude = amplitude.expand(batch_size, -1).clone()
            frequency = frequency.expand(batch_size, -1).clone()
        return OscillatorState(phase, amplitude, frequency)

    def _raw_rows(self) -> list[_core.OscillatorState]:
        """Marshal each batch row to a Rust state object."""
        phase_rows = _rows(self.phase)
        amplitude_rows = _rows(self.amplitude)
        frequency_rows = _rows(self.frequency)
        return [
            _core.OscillatorState(_numpy(p), _numpy(a), _numpy(f))
            for p, a, f in zip(phase_rows, amplitude_rows, frequency_rows, strict=True)
        ]

    @classmethod
    def _from_raw_rows(
        cls,
        rows: list[_core.OscillatorState],
        template: OscillatorState,
    ) -> OscillatorState:
        """Marshal Rust state rows back to the template Torch placement."""
        phase = [_tensor(row.phase, template.phase) for row in rows]
        amplitude = [_tensor(row.amplitude, template.amplitude) for row in rows]
        frequency = [_tensor(row.frequency, template.frequency) for row in rows]
        return cls(
            _stack(phase, template.phase),
            _stack(amplitude, template.amplitude),
            _stack(frequency, template.frequency),
        )


class _RawModel(Protocol):
    """Structural type of the three compiled oscillator model classes."""

    def compute_derivatives(
        self, state: _core.OscillatorState
    ) -> _core.StateDerivatives:
        """Evaluate Rust-owned state derivatives."""
        ...

    def dynamics_vjp(
        self,
        state: _core.OscillatorState,
        grad_dphase: np.ndarray[Any, np.dtype[np.float64]],
        grad_damplitude: np.ndarray[Any, np.dtype[np.float64]],
        grad_dfrequency: np.ndarray[Any, np.dtype[np.float64]],
    ) -> tuple[
        np.ndarray[Any, np.dtype[np.float64]],
        np.ndarray[Any, np.dtype[np.float64]],
        np.ndarray[Any, np.dtype[np.float64]],
    ]:
        """Evaluate the Rust-owned vector-Jacobian product."""
        ...


class _DynamicsAutograd(torch.autograd.Function):
    """Connect Rust-owned dynamics and VJP implementations to Torch autograd."""

    @staticmethod
    def forward(
        ctx: Any,
        model: _RawModel,
        phase: torch.Tensor,
        amplitude: torch.Tensor,
        frequency: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate one unbatched Rust model row."""
        raw_state = _core.OscillatorState(
            _numpy(phase), _numpy(amplitude), _numpy(frequency)
        )
        derivative = model.compute_derivatives(raw_state)
        ctx.model = model
        ctx.raw_state = raw_state
        ctx.save_for_backward(phase, amplitude, frequency)
        return (
            _tensor(derivative.dphase, phase),
            _tensor(derivative.damplitude, amplitude),
            _tensor(derivative.dfrequency, frequency),
        )

    @staticmethod
    def backward(
        ctx: Any,
        grad_dphase: torch.Tensor | None,
        grad_damplitude: torch.Tensor | None,
        grad_dfrequency: torch.Tensor | None,
    ) -> tuple[None, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate the Rust-owned dynamics vector-Jacobian product."""
        phase, amplitude, frequency = ctx.saved_tensors
        gradients = (
            torch.zeros_like(phase) if grad_dphase is None else grad_dphase,
            torch.zeros_like(amplitude) if grad_damplitude is None else grad_damplitude,
            torch.zeros_like(frequency) if grad_dfrequency is None else grad_dfrequency,
        )
        grad_phase, grad_amplitude, grad_frequency = ctx.model.dynamics_vjp(
            ctx.raw_state, *(_numpy(value) for value in gradients)
        )
        return (
            None,
            _tensor(grad_phase, phase),
            _tensor(grad_amplitude, amplitude),
            _tensor(grad_frequency, frequency),
        )


class OscillatorModel(ABC):
    """Base compatibility interface for Rust-backed oscillator models."""

    _raw: _RawModel

    def __init__(self, n_oscillators: int, coupling_strength: float = 1.0) -> None:
        if n_oscillators < 1:
            raise ValueError(f"n_oscillators must be positive, got {n_oscillators}.")
        self._n = n_oscillators
        self._coupling_strength = coupling_strength
        self._coupling_matrix: torch.Tensor | None = None

    @property
    def n_oscillators(self) -> int:
        """Return the configured oscillator count."""
        return self._n

    @property
    def coupling_strength(self) -> float:
        """Return the global coupling strength."""
        return self._coupling_strength

    @property
    def coupling_matrix(self) -> torch.Tensor:
        """Return the custom coupling matrix, when configured."""
        if self._coupling_matrix is None:
            raise AttributeError("no custom coupling matrix is configured")
        return self._coupling_matrix

    def set_coupling_matrix(self, matrix: torch.Tensor) -> None:
        """Validate and install a custom full coupling matrix."""
        if tuple(matrix.shape) != (self._n, self._n):
            raise ValueError(
                f"Expected coupling matrix shape ({self._n}, {self._n}), "
                f"got {tuple(matrix.shape)}."
            )
        self._coupling_matrix = matrix
        self._rebuild(_core.CouplingMode.full(_numpy(matrix).reshape(-1)))

    @abstractmethod
    def _rebuild(self, mode: _core.CouplingMode) -> None:
        """Rebuild the Rust model with a new coupling mode."""

    def compute_derivatives(
        self, state: OscillatorState
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute derivatives in Rust and marshal them to Torch tensors."""
        derivatives = [
            _DynamicsAutograd.apply(  # type: ignore[no-untyped-call]
                self._raw, phase, amplitude, frequency
            )
            for phase, amplitude, frequency in zip(
                _rows(state.phase),
                _rows(state.amplitude),
                _rows(state.frequency),
                strict=True,
            )
        ]
        return (
            _stack([item[0] for item in derivatives], state.phase),
            _stack([item[1] for item in derivatives], state.amplitude),
            _stack([item[2] for item in derivatives], state.frequency),
        )

    def step(
        self, state: OscillatorState, dt: float = 0.01, method: str = "rk4"
    ) -> OscillatorState:
        """Advance one step through the selected Rust integrator."""
        integrator: _core.EulerIntegrator | _core.RK4Integrator
        if method == "euler":
            integrator = _core.EulerIntegrator()
        elif method == "rk4":
            integrator = _core.RK4Integrator()
        else:
            raise ValueError(
                f"Unknown integration method '{method}'. Use 'euler' or 'rk4'."
            )
        rows = [integrator.step(self._raw, row, dt) for row in state._raw_rows()]
        return OscillatorState._from_raw_rows(rows, state)

    def integrate(
        self,
        state: OscillatorState,
        n_steps: int,
        dt: float = 0.01,
        method: str = "rk4",
        record_trajectory: bool = False,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]:
        """Integrate through a Rust fixed-step integrator."""
        integrator: _core.EulerIntegrator | _core.RK4Integrator
        if method == "euler":
            integrator = _core.EulerIntegrator()
        elif method == "rk4":
            integrator = _core.RK4Integrator()
        else:
            raise ValueError(
                f"Unknown integration method '{method}'. Use 'euler' or 'rk4'."
            )
        results = [
            integrator.integrate_fixed(self._raw, row, n_steps, dt, record_trajectory)
            for row in state._raw_rows()
        ]
        final = OscillatorState._from_raw_rows([item[0] for item in results], state)
        if not record_trajectory:
            return final, None
        trajectory = [
            OscillatorState._from_raw_rows(
                [cast(list[_core.OscillatorState], item[1])[index] for item in results],
                state,
            )
            for index in range(n_steps)
        ]
        return final, trajectory


class KuramotoOscillator(OscillatorModel):
    """Torch compatibility wrapper over Rust Kuramoto dynamics."""

    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float = 1.0,
        decay_rate: float = 0.1,
        freq_adaptation_rate: float = 0.01,
        coupling_mode: str = "full",
        sparse_k: int | None = None,
        device: object = None,
        dtype: object = None,
    ) -> None:
        super().__init__(n_oscillators, coupling_strength)
        self._decay_rate = decay_rate
        self._freq_adaptation_rate = freq_adaptation_rate
        self._sparse_k = (
            sparse_k
            if sparse_k is not None
            else max(1, min(n_oscillators - 1, math.ceil(math.log2(n_oscillators))))
        )
        mode = (
            _core.CouplingMode.sparse_knn(self._sparse_k)
            if coupling_mode == "sparse_knn" and n_oscillators > 1
            else _core.CouplingMode.full()
        )
        self._rebuild(mode)

    def _rebuild(self, mode: _core.CouplingMode) -> None:
        self._raw = _core.KuramotoOscillator(
            self._n,
            self._coupling_strength,
            self._decay_rate,
            self._freq_adaptation_rate,
            mode,
        )

    @property
    def decay_rate(self) -> float:
        """Return amplitude decay rate."""
        return self._decay_rate

    @property
    def freq_adaptation_rate(self) -> float:
        """Return frequency adaptation rate."""
        return self._freq_adaptation_rate

    @property
    def sparse_k(self) -> int:
        """Return resolved sparse-neighbour count."""
        return self._sparse_k


class StuartLandauOscillator(OscillatorModel):
    """Torch compatibility wrapper over Rust Stuart-Landau dynamics."""

    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float = 1.0,
        bifurcation_param: float = 1.0,
        coupling_mode: str = "full",
        sparse_k: int | None = None,
        device: object = None,
        dtype: object = None,
    ) -> None:
        super().__init__(n_oscillators, coupling_strength)
        self._bifurcation_param = bifurcation_param
        mode = _core.CouplingMode.full()
        if coupling_mode == "sparse_knn" and n_oscillators > 1:
            mode = _core.CouplingMode.sparse_knn(sparse_k)
        self._rebuild(mode)

    def _rebuild(self, mode: _core.CouplingMode) -> None:
        self._raw = _core.StuartLandauOscillator(
            self._n, self._coupling_strength, self._bifurcation_param, mode
        )

    @property
    def bifurcation_param(self) -> float:
        """Return the Hopf bifurcation parameter."""
        return self._bifurcation_param


class HopfOscillator(StuartLandauOscillator):
    """Torch compatibility wrapper over Rust polar Hopf dynamics."""

    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float = 1.0,
        bifurcation_param: float = 1.0,
        freq_adaptation_rate: float = 0.0,
        coupling_mode: str = "full",
        sparse_k: int | None = None,
        device: object = None,
        dtype: object = None,
    ) -> None:
        self._freq_adaptation_rate = freq_adaptation_rate
        super().__init__(
            n_oscillators,
            coupling_strength,
            bifurcation_param,
            coupling_mode,
            sparse_k,
            device,
            dtype,
        )

    def _rebuild(self, mode: _core.CouplingMode) -> None:
        self._raw = _core.HopfOscillator(
            self._n,
            self._coupling_strength,
            self._bifurcation_param,
            self._freq_adaptation_rate,
            mode,
        )


def _scalar_rows(function: Any, phase: torch.Tensor, *extra: object) -> torch.Tensor:
    """Invoke a scalar Rust metric once per input row."""
    values = [_tensor(function(_numpy(row), *extra), phase) for row in _rows(phase)]
    return _stack(values, phase)


def kuramoto_order_parameter(phase: torch.Tensor) -> torch.Tensor:
    """Compute the Rust-owned Kuramoto order parameter."""
    if phase.numel() == 0:
        raise ValueError("Phase tensor must not be empty.")
    return _scalar_rows(_core.kuramoto_order_parameter, phase)


def kuramoto_order_parameter_complex(phase: torch.Tensor) -> torch.Tensor:
    """Compute the Rust-owned complex Kuramoto order parameter."""
    if phase.numel() == 0:
        raise ValueError("Phase tensor must not be empty.")
    values = []
    for row in _rows(phase):
        real, imag = _core.kuramoto_order_parameter_complex(_numpy(row))
        values.append(torch.tensor(complex(real, imag), device=phase.device))
    return _stack(values, phase)


def mean_phase_coherence(phase: torch.Tensor) -> torch.Tensor:
    """Compute Rust-owned mean phase coherence."""
    return _scalar_rows(_core.mean_phase_coherence, phase)


def phase_coherence_matrix(phase: torch.Tensor) -> torch.Tensor:
    """Compute Rust-owned dense phase coherence matrices."""
    values = [
        _tensor(_core.phase_coherence_matrix(_numpy(row)), phase).reshape(
            row.shape[-1], row.shape[-1]
        )
        for row in _rows(phase)
    ]
    return _stack(values, phase)


def build_phase_knn(phase: torch.Tensor, k: int) -> torch.Tensor:
    """Build Rust-owned k-nearest phase-neighbour indices."""
    if k < 1:
        raise ValueError("k must be >= 1")
    if k >= phase.shape[-1]:
        raise ValueError("k must be < N")
    return _build_phase_knn_index(phase.unsqueeze(0) if phase.dim() == 1 else phase, k)


def sparse_mean_phase_coherence(
    phase: torch.Tensor, neighbors: torch.Tensor
) -> torch.Tensor:
    """Compute Rust-owned sparse phase coherence."""
    phase_rows = _rows(phase)
    neighbor_rows = list(neighbors) if phase.dim() > 1 else [neighbors[0]]
    values = [
        _tensor(_core.sparse_mean_phase_coherence(_numpy(row), nbr.tolist()), phase)
        for row, nbr in zip(phase_rows, neighbor_rows, strict=True)
    ]
    return _stack(values, phase)


def synchronization_energy(
    phase: torch.Tensor,
    amplitude: torch.Tensor,
    coupling_matrix: torch.Tensor | None = None,
) -> torch.Tensor:
    """Compute Rust-owned dense synchronization energy."""
    matrix = None if coupling_matrix is None else _numpy(coupling_matrix).reshape(-1)
    values = [
        _tensor(_core.synchronization_energy(_numpy(p), _numpy(a), matrix), phase)
        for p, a in zip(_rows(phase), _rows(amplitude), strict=True)
    ]
    return _stack(values, phase)


def sparse_synchronization_energy(
    phase: torch.Tensor,
    amplitude: torch.Tensor,
    neighbors: torch.Tensor,
    coupling_strength: float = 1.0,
) -> torch.Tensor:
    """Compute Rust-owned sparse synchronization energy."""
    neighbor_rows = list(neighbors) if phase.dim() > 1 else [neighbors[0]]
    values = [
        _tensor(
            _core.sparse_synchronization_energy(
                _numpy(p), _numpy(a), nbr.tolist(), coupling_strength
            ),
            phase,
        )
        for p, a, nbr in zip(_rows(phase), _rows(amplitude), neighbor_rows, strict=True)
    ]
    return _stack(values, phase)


def power_spectral_density(
    amplitude: torch.Tensor,
    phase: torch.Tensor,
    n_freq_bins: int | None = None,
) -> torch.Tensor:
    """Compute Rust-owned resonance power spectra."""
    values = [
        _tensor(
            _core.power_spectral_density(_numpy(a), _numpy(p), n_freq_bins),
            amplitude,
        )
        for a, p in zip(_rows(amplitude), _rows(phase), strict=True)
    ]
    return _stack(values, amplitude)


def extract_concept_probabilities(
    amplitude: torch.Tensor,
    phase: torch.Tensor,
    concept_frequencies: torch.Tensor,
    concept_bandwidths: torch.Tensor,
    n_freq_bins: int | None = None,
) -> torch.Tensor:
    """Compute Rust-owned concept probabilities."""
    values = [
        _tensor(
            _core.extract_concept_probabilities(
                _numpy(a),
                _numpy(p),
                _numpy(concept_frequencies),
                _numpy(concept_bandwidths),
                n_freq_bins,
            ),
            amplitude,
        )
        for a, p in zip(_rows(amplitude), _rows(phase), strict=True)
    ]
    return _stack(values, amplitude)


@dataclass
class SolverResult:
    """Compatibility solver result and diagnostics."""

    final_state: OscillatorState
    n_steps_taken: int
    n_function_evals: int
    final_dt: float
    wall_time_seconds: float
    trajectory: list[OscillatorState] | None = None


class FixedStepRK4Solver:
    """Fixed-step solver delegating every step to Rust RK4."""

    def __init__(self, dt: float = 0.01, compiled: bool = False) -> None:
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
        self._dt = dt
        self._compiled = compiled

    def solve(
        self,
        model: OscillatorModel,
        initial_state: OscillatorState,
        n_steps: int = 1000,
        record_trajectory: bool = False,
    ) -> SolverResult:
        """Integrate for a fixed number of Rust RK4 steps."""
        start = time.perf_counter()
        final, trajectory = model.integrate(
            initial_state, n_steps, self._dt, "rk4", record_trajectory
        )
        return SolverResult(
            final,
            n_steps,
            n_steps * 4,
            self._dt,
            time.perf_counter() - start,
            trajectory,
        )


class BatchedRK45Solver:
    """Adaptive solver delegating to the Rust RK45 integrator."""

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
        model: OscillatorModel,
        initial_state: OscillatorState,
        t_span: tuple[float, float] = (0.0, 1.0),
        max_steps: int = 10000,
        record_trajectory: bool = False,
    ) -> SolverResult:
        """Adaptively integrate each state row through Rust RK45."""
        span = t_span[1] - t_span[0]
        dt_init = min(self._max_dt, span / 10.0) if span > 0 else self._max_dt
        integrator = _core.RK45Integrator(self._rtol, self._atol, max_steps)
        start = time.perf_counter()
        try:
            results = [
                integrator.integrate_adaptive(
                    model._raw, row, span, dt_init, record_trajectory
                )
                for row in initial_state._raw_rows()
            ]
        except ValueError as exc:
            raise SolverError(str(exc)) from exc
        final = OscillatorState._from_raw_rows(
            [result.final_state for result in results], initial_state
        )
        accepted = min(result.accepted_steps for result in results)
        rejected = max(result.rejected_steps for result in results)
        trajectory = None
        if record_trajectory:
            trajectory = [
                OscillatorState._from_raw_rows(
                    [
                        cast(list[_core.OscillatorState], result.trajectory)[index]
                        for result in results
                    ],
                    initial_state,
                )
                for index in range(accepted)
            ]
        return SolverResult(
            final,
            accepted,
            (accepted + rejected) * 6,
            results[0].final_dt,
            time.perf_counter() - start,
            trajectory,
        )


def gradient_checkpoint_integration(
    model: OscillatorModel,
    state: OscillatorState,
    n_steps: int,
    dt: float = 0.01,
    checkpoint_every: int = 10,
    memory_budget_mb: float | None = None,
) -> OscillatorState:
    """Delegate segmented compatibility integration to Rust RK4 calls."""
    if n_steps < 0:
        raise ValueError(f"n_steps must be non-negative, got {n_steps}")
    if checkpoint_every <= 0:
        raise ValueError(f"checkpoint_every must be positive, got {checkpoint_every}")
    segment = checkpoint_every
    if memory_budget_mb is not None:
        segment = max(1, int(math.sqrt(max(n_steps, 1))))
    current = state
    remaining = n_steps
    while remaining:
        count = min(segment, remaining)
        current, _ = model.integrate(current, count, dt, "rk4", False)
        remaining -= count
    return current

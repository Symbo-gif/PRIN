"""Type declarations for PRINet 3.0 compatibility aliases and stubs."""

from __future__ import annotations

from typing import NoReturn, Protocol, runtime_checkable

from prin.dynamics import (
    BandNetwork,
    BandParams,
    OscillatorState,
    StateDerivatives,
    TemporalPropagator,
)
from prin.nn import Rip, Scalr, SyncGd

class BackendUnavailableError(RuntimeError): ...

@runtime_checkable
class OscillatorModel(Protocol):
    @property
    def n_oscillators(self) -> int: ...
    def compute_derivatives(self, state: OscillatorState) -> StateDerivatives: ...

SCALROptimizer: type[Scalr]
RIPOptimizer: type[Rip]
SynchronizedGradientDescent: type[SyncGd]
TemporalPhasePropagator: type[TemporalPropagator]

def temporal_recovery_speed(
    matches_history: list[list[int]],
    occlusion_mask: list[list[bool]],
    n_objects: int,
) -> float: ...
def ThetaGammaNetwork(
    n_theta: int,
    n_gamma: int,
    theta_params: BandParams,
    gamma_params: BandParams,
    pac_modulation_depth: float,
    phase_offset: float = 0.0,
) -> BandNetwork: ...
def DeltaThetaGammaNetwork(
    n_delta: int,
    n_theta: int,
    n_gamma: int,
    delta_params: BandParams,
    theta_params: BandParams,
    gamma_params: BandParams,
    pac_dt_depth: float,
    pac_tg_depth: float,
    offset_dt: float = 0.0,
    offset_tg: float = 0.0,
) -> BandNetwork: ...
def triton_available() -> bool: ...
def cuda_fused_kernel_available() -> bool: ...
def triton_fused_mean_field_rk4_step(*_args: object, **_kwargs: object) -> NoReturn: ...
def triton_sparse_knn_coupling(*_args: object, **_kwargs: object) -> NoReturn: ...
def triton_pac_modulation(*_args: object, **_kwargs: object) -> NoReturn: ...
def triton_hierarchical_order_param(*_args: object, **_kwargs: object) -> NoReturn: ...
def triton_fused_discrete_step(*_args: object, **_kwargs: object) -> NoReturn: ...
def fused_discrete_step_cuda(*_args: object, **_kwargs: object) -> NoReturn: ...

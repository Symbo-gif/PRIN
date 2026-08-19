"""Type stubs for the compiled PRIN core extension (``prin._prin_core``).

Regenerated as the Rust API grows; keep in sync with ``crates/prin-py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

__version__: str

# --- DLPack ---
def core_version() -> str: ...
def dlpack_negate(obj: object) -> object: ...
def dlpack_negate_batched(tensors: list[object]) -> list[object]: ...
def dlpack_round_trip(obj: object) -> object: ...

# --- Torch bridges (WP-025) ---
class ResonanceLayerCtx:
    def backward(self, grad_output: object) -> object: ...

class ResonanceLayerBridge:
    def __init__(
        self,
        n_oscillators: int,
        n_dims: int,
        n_steps: int = 10,
        dt: float = 0.01,
        decay_rate: float = 0.1,
        freq_adaptation_rate: float = 0.01,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def n_dims(self) -> int: ...
    def forward(self, x: object) -> tuple[object, ResonanceLayerCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class GatedPhaseActivationCtx:
    def backward(self, grad_output: object) -> object: ...

class GatedPhaseActivationBridge:
    def __init__(self, n_dims: int) -> None: ...
    @property
    def n_dims(self) -> int: ...
    def forward(self, z: object) -> tuple[object, GatedPhaseActivationCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

# --- Torch bridges (WP-026 / Exec-WP-026 S1) ---
class OscillatoryAttentionCtx:
    def backward(self, grad_output: object) -> tuple[object, object | None]: ...

class OscillatoryAttentionBridge:
    def __init__(
        self,
        d_model: int,
        n_heads: int,
        dropout: float = 0.0,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def d_model(self) -> int: ...
    @property
    def n_heads(self) -> int: ...
    def forward(
        self, x: object, phase: object | None = None
    ) -> tuple[object, OscillatoryAttentionCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class PhaseTrackerEncodeCtx:
    def backward(self, grad_phase: object, grad_amp: object) -> object: ...

class PhaseTrackerEvolveCtx:
    def backward(
        self, grad_phase_out: object, grad_amp_out: object
    ) -> tuple[object, object]: ...

class PhaseTrackerSimilarityCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class TrackingResult:
    @property
    def phase_history(self) -> list[object]: ...
    @property
    def identity_matches(self) -> list[list[int]]: ...
    @property
    def identity_preservation(self) -> float: ...
    @property
    def per_frame_similarity(self) -> list[float]: ...
    @property
    def per_frame_phase_correlation(self) -> list[float]: ...

class PhaseTrackerBridge:
    def __init__(
        self,
        detection_dim: int,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_osc(self) -> int: ...
    @property
    def match_threshold(self) -> float: ...
    def encode(
        self, detections: object
    ) -> tuple[object, object, PhaseTrackerEncodeCtx]: ...
    def evolve(
        self, phase: object, amplitude: object
    ) -> tuple[object, object, PhaseTrackerEvolveCtx]: ...
    def phase_similarity(
        self, phase_a: object, phase_b: object
    ) -> tuple[object, PhaseTrackerSimilarityCtx]: ...
    def match_frames(
        self, detections_t: object, detections_t1: object
    ) -> tuple[list[int], object]: ...
    def track_sequence(self, frame_detections: list[object]) -> TrackingResult: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class HybridPRINetV2Ctx:
    def backward(self, grad_output: object) -> object: ...

class HybridPRINetV2Bridge:
    def __init__(
        self,
        n_input: int,
        n_classes: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        n_discrete_steps: int = 5,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        dropout: float = 0.0,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_input(self) -> int: ...
    @property
    def n_classes(self) -> int: ...
    @property
    def n_tokens(self) -> int: ...
    def forward(self, x: object) -> tuple[object, HybridPRINetV2Ctx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class SlotAttentionModuleCtx:
    def backward(self, grad_output: object) -> object: ...

class SlotAttentionModuleBridge:
    def __init__(
        self,
        num_slots: int,
        slot_dim: int,
        input_dim: int,
        num_iterations: int = 3,
        hidden_dim: int | None = None,
        eps: float = 1e-8,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def num_slots(self) -> int: ...
    @property
    def slot_dim(self) -> int: ...
    def forward(
        self, inputs: object, seed: Seed
    ) -> tuple[object, SlotAttentionModuleCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class TemporalSlotAttentionMOTProcessFrameCtx:
    def backward(self, grad_output: object) -> tuple[object, object | None]: ...

class TemporalSlotAttentionMOTSimilarityCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class TemporalSlotAttentionMOTBridge:
    def __init__(
        self,
        detection_dim: int,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def num_slots(self) -> int: ...
    @property
    def slot_dim(self) -> int: ...
    @property
    def match_threshold(self) -> float: ...
    def process_frame(
        self, detections: object, seed: Seed, prev_slots: object | None = None
    ) -> tuple[object, TemporalSlotAttentionMOTProcessFrameCtx]: ...
    def slot_similarity(
        self, slots_a: object, slots_b: object
    ) -> tuple[object, TemporalSlotAttentionMOTSimilarityCtx]: ...
    def match_frames(
        self, detections_t: object, detections_t1: object, seed: Seed
    ) -> tuple[list[int], object]: ...
    def track_sequence(
        self, frame_detections: list[object], seed: Seed
    ) -> tuple[list[object], list[list[int]], float, list[float]]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class PhaseTrackerFrozenBridge:
    def __init__(
        self,
        detection_dim: int,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def inner(self) -> PhaseTrackerBridge: ...
    def match_frames(
        self, detections_t: object, detections_t1: object
    ) -> tuple[list[int], object]: ...
    def track_sequence(self, frame_detections: list[object]) -> TrackingResult: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class PhaseTrackerStaticEncodeCtx:
    def backward(self, grad_phase: object, grad_amp: object) -> object: ...

class PhaseTrackerStaticEvolveCtx:
    def backward(
        self, grad_phase_out: object, grad_amp_out: object
    ) -> tuple[object, object]: ...

class PhaseTrackerStaticSimilarityCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class PhaseTrackerStaticBridge:
    def __init__(
        self,
        detection_dim: int,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 16,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_osc(self) -> int: ...
    def encode(
        self, detections: object
    ) -> tuple[object, object, PhaseTrackerStaticEncodeCtx]: ...
    def evolve(
        self, phase: object, amplitude: object
    ) -> tuple[object, object, PhaseTrackerStaticEvolveCtx]: ...
    def phase_similarity(
        self, phase_a: object, phase_b: object
    ) -> tuple[object, PhaseTrackerStaticSimilarityCtx]: ...
    def match_frames(
        self, detections_t: object, detections_t1: object
    ) -> tuple[list[int], object]: ...
    def track_sequence(self, frame_detections: list[object]) -> TrackingResult: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class SlotAttentionNoGRUProcessFrameCtx:
    def backward(self, grad_output: object) -> object: ...

class SlotAttentionNoGRUSimilarityCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class SlotAttentionNoGRUBridge:
    def __init__(
        self,
        detection_dim: int,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    def process_frame(
        self, detections: object, seed: Seed
    ) -> tuple[object, SlotAttentionNoGRUProcessFrameCtx]: ...
    def slot_similarity(
        self, slots_a: object, slots_b: object
    ) -> tuple[object, SlotAttentionNoGRUSimilarityCtx]: ...
    def match_frames(
        self, detections_t: object, detections_t1: object, seed: Seed
    ) -> tuple[list[int], object]: ...
    def track_sequence(
        self, frame_detections: list[object], seed: Seed
    ) -> tuple[list[object], list[list[int]], float, list[float]]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class SlotAttentionFrozenBridge:
    def __init__(
        self,
        detection_dim: int,
        num_slots: int = 8,
        slot_dim: int = 64,
        num_iterations: int = 3,
        match_threshold: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def inner(self) -> TemporalSlotAttentionMOTBridge: ...
    def match_frames(
        self, detections_t: object, detections_t1: object, seed: Seed
    ) -> tuple[list[int], object]: ...
    def track_sequence(
        self, frame_detections: list[object], seed: Seed
    ) -> tuple[list[object], list[list[int]], float, list[float]]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class OscillatorBudget:
    @property
    def n_delta(self) -> int: ...
    @property
    def n_theta(self) -> int: ...
    @property
    def n_gamma(self) -> int: ...
    @property
    def complexity(self) -> float: ...
    def total(self) -> int: ...

def estimate_complexity(
    detections: object,
    spatial_weight: float = 0.5,
    count_weight: float = 0.5,
    max_objects: int = 50,
) -> float: ...

class AdaptiveOscillatorAllocatorBridge:
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
    ) -> None: ...
    @property
    def strategy(self) -> str: ...
    def allocate(
        self, complexity: float, features: object | None = None
    ) -> OscillatorBudget: ...
    def sweep_complexity(self, steps: int) -> list[OscillatorBudget]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class DynamicPhaseTrackerBridge:
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
    ) -> None: ...
    def forward(
        self, detections_t: object, detections_t1: object, seed: Seed
    ) -> tuple[list[int], object, OscillatorBudget]: ...

# --- Constants ---
TAU: float
AMPLITUDE_MIN: float
AMPLITUDE_MAX: float
DERIV_CLAMP: float
SPARSE_EPS: float

# --- Seed ---
class Seed:
    def __init__(self, counter: int, key: int) -> None: ...
    @property
    def counter(self) -> int: ...
    @property
    def key(self) -> int: ...
    def jump(self, delta: int) -> None: ...
    def next_f64(self) -> float: ...
    def next_f64_range(self, lo: float, hi: float) -> float: ...
    def next_u64(self) -> int: ...

# --- OscillatorState ---
class OscillatorState:
    def __init__(
        self,
        phase: NDArray[np.float64],
        amplitude: NDArray[np.float64],
        frequency: NDArray[np.float64],
        freq_band: NDArray[np.uint32] | None = None,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def n_bands(self) -> int: ...
    @property
    def phase(self) -> NDArray[np.float64]: ...
    @property
    def amplitude(self) -> NDArray[np.float64]: ...
    @property
    def frequency(self) -> NDArray[np.float64]: ...
    @property
    def freq_band(self) -> NDArray[np.uint32] | None: ...
    @staticmethod
    def create_random(
        n: int, freq_range: tuple[float, float], seed: Seed
    ) -> OscillatorState: ...
    @staticmethod
    def create_synchronized(n: int, base_frequency: float) -> OscillatorState: ...
    def phase_knn_index(self, k: int) -> list[NDArray[np.int64]]: ...
    def __len__(self) -> int: ...

# --- StateDerivatives ---
class StateDerivatives:
    @property
    def dphase(self) -> NDArray[np.float64]: ...
    @property
    def damplitude(self) -> NDArray[np.float64]: ...
    @property
    def dfrequency(self) -> NDArray[np.float64]: ...

# --- CouplingMode ---
class CouplingMode:
    @staticmethod
    def mean_field() -> CouplingMode: ...
    @staticmethod
    def full(matrix: NDArray[np.float64] | None = None) -> CouplingMode: ...
    @staticmethod
    def sparse_knn(k: int | None = None) -> CouplingMode: ...
    def variant(self) -> str: ...

# --- Topology ---
class Topology:
    @staticmethod
    def all_to_all() -> Topology: ...
    @staticmethod
    def ring(k_ring: int) -> Topology: ...
    @staticmethod
    def small_world(k_ring: int, rewire_prob: float, seed: Seed) -> Topology: ...
    def build_matrix(self, n: int, coupling_strength: float) -> NDArray[np.float64]: ...

# --- PhaseAmplitudeCoupling ---
class PhaseAmplitudeCoupling:
    def __init__(self, modulation_depth: float) -> None: ...
    @property
    def modulation_depth(self) -> float: ...
    def modulate(
        self,
        slow_phase: NDArray[np.float64],
        fast_amplitude: NDArray[np.float64],
        offset: float,
    ) -> NDArray[np.float64]: ...

# --- Models ---
class KuramotoOscillator:
    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float,
        decay_rate: float,
        freq_adaptation_rate: float,
        coupling_mode: CouplingMode,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def coupling_strength(self) -> float: ...
    @property
    def decay_rate(self) -> float: ...
    @property
    def freq_adaptation_rate(self) -> float: ...
    def compute_derivatives(self, state: OscillatorState) -> StateDerivatives: ...

class StuartLandauOscillator:
    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float,
        bifurcation_param: float,
        coupling_mode: CouplingMode,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def coupling_strength(self) -> float: ...
    @property
    def bifurcation_param(self) -> float: ...
    def compute_derivatives(self, state: OscillatorState) -> StateDerivatives: ...

class HopfOscillator:
    def __init__(
        self,
        n_oscillators: int,
        coupling_strength: float,
        bifurcation_param: float,
        freq_adaptation_rate: float,
        coupling_mode: CouplingMode,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def coupling_strength(self) -> float: ...
    @property
    def bifurcation_param(self) -> float: ...
    @property
    def freq_adaptation_rate(self) -> float: ...
    def compute_derivatives(self, state: OscillatorState) -> StateDerivatives: ...

# --- Integrators ---
class EulerIntegrator:
    def __init__(self) -> None: ...
    def step(
        self, model: Any, state: OscillatorState, dt: float
    ) -> OscillatorState: ...
    def integrate_fixed(
        self,
        model: Any,
        state: OscillatorState,
        n_steps: int,
        dt: float,
        record_trajectory: bool = False,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]: ...

class RK4Integrator:
    def __init__(self) -> None: ...
    def step(
        self, model: Any, state: OscillatorState, dt: float
    ) -> OscillatorState: ...
    def integrate_fixed(
        self,
        model: Any,
        state: OscillatorState,
        n_steps: int,
        dt: float,
        record_trajectory: bool = False,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]: ...

class RK45Integrator:
    def __init__(
        self, rtol: float = 1e-6, atol: float = 1e-8, max_steps: int = 100_000
    ) -> None: ...
    def step(
        self, model: Any, state: OscillatorState, dt: float
    ) -> OscillatorState: ...
    def integrate_adaptive(
        self,
        model: Any,
        state: OscillatorState,
        t_span: float,
        dt_init: float,
        record_trajectory: bool = False,
    ) -> AdaptiveResult: ...
    def integrate_fixed(
        self,
        model: Any,
        state: OscillatorState,
        n_steps: int,
        dt: float,
        record_trajectory: bool = False,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]: ...

class AdaptiveResult:
    @property
    def final_state(self) -> OscillatorState: ...
    @property
    def accepted_steps(self) -> int: ...
    @property
    def rejected_steps(self) -> int: ...
    @property
    def final_dt(self) -> float: ...
    @property
    def trajectory(self) -> list[OscillatorState] | None: ...

class ExponentialIntegrator:
    def __init__(
        self,
        dim: int,
        krylov_rank: int = 16,
        max_direct_dim: int = 150,
        stiff_mode: bool = False,
        stiff_cond_threshold: float = 20.0,
        max_krylov_stiff: int = 48,
    ) -> None: ...
    def step(
        self, model: Any, state: OscillatorState, dt: float
    ) -> OscillatorState: ...
    def integrate(
        self,
        model: Any,
        state: OscillatorState,
        n_steps: int,
        dt: float,
        record_trajectory: bool = False,
        recompute_jacobian_every: int = 1,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]: ...
    @property
    def dim(self) -> int: ...
    @property
    def krylov_rank(self) -> int: ...
    @property
    def use_krylov(self) -> bool: ...
    @property
    def stiff_mode(self) -> bool: ...

class MultiRateIntegrator:
    def __init__(self, sub_steps: int = 10, method: str = "rk4") -> None: ...
    def step(
        self, model: Any, state: OscillatorState, dt: float
    ) -> OscillatorState: ...
    def integrate(
        self,
        model: Any,
        state: OscillatorState,
        n_steps: int,
        dt: float,
        record_trajectory: bool = False,
    ) -> tuple[OscillatorState, list[OscillatorState] | None]: ...
    @property
    def sub_steps(self) -> int: ...
    @property
    def method(self) -> str: ...

# --- Metrics: Order ---
def kuramoto_order_parameter(phase: NDArray[np.float64]) -> float: ...
def kuramoto_order_parameter_complex(
    phase: NDArray[np.float64],
) -> tuple[float, float]: ...
def inter_frame_phase_correlation(
    phase_t: NDArray[np.float64], phase_t_prev: NDArray[np.float64]
) -> float: ...
def order_parameter_series(
    trajectory: NDArray[np.float64], n: int
) -> NDArray[np.float64]: ...

# --- Metrics: Coherence ---
def mean_phase_coherence(phase: NDArray[np.float64]) -> float: ...
def phase_coherence_matrix(phase: NDArray[np.float64]) -> NDArray[np.float64]: ...
def sparse_mean_phase_coherence(
    phase: NDArray[np.float64], neighbors: list[list[int]]
) -> float: ...

# --- Metrics: Spectral ---
def power_spectral_density(
    amplitude: NDArray[np.float64],
    phase: NDArray[np.float64],
    n_freq_bins: int | None = None,
) -> NDArray[np.float64]: ...
def extract_concept_probabilities(
    amplitude: NDArray[np.float64],
    phase: NDArray[np.float64],
    concept_frequencies: NDArray[np.float64],
    concept_bandwidths: NDArray[np.float64],
    n_freq_bins: int | None = None,
) -> NDArray[np.float64]: ...

# --- Metrics: Energy ---
def synchronization_energy(
    phase: NDArray[np.float64],
    amplitude: NDArray[np.float64],
    coupling_matrix: NDArray[np.float64] | None = None,
) -> float: ...
def sparse_synchronization_energy(
    phase: NDArray[np.float64],
    amplitude: NDArray[np.float64],
    neighbors: list[list[int]],
    coupling_strength: float,
) -> float: ...

# --- Metrics: Chimera ---
def local_order_parameter(
    phase: NDArray[np.float64], neighbors: list[list[int]]
) -> NDArray[np.float64]: ...
def bimodality_index(values: NDArray[np.float64]) -> float: ...
def strength_of_incoherence(phase: NDArray[np.float64], window_size: int) -> float: ...
def discontinuity_measure(
    phase: NDArray[np.float64], threshold_ratio: float
) -> tuple[list[bool], int]: ...
def chimera_index(
    phase: NDArray[np.float64], neighbors: list[list[int]], threshold: float
) -> float: ...
def strength_of_incoherence_temporal(
    trajectory: list[list[float]], window_size: int, discard_transient: int
) -> float: ...
def bimodality_chimera_threshold() -> float: ...
def default_chimera_threshold() -> float: ...

# --- Metrics: Metastability ---
def metastability(trajectory: NDArray[np.float64], n: int) -> float: ...

# --- Metrics: k-NN ---
def build_phase_knn(phase: NDArray[np.float64], k: int) -> list[NDArray[np.int64]]: ...

# --- Band Networks ---
class BandParams:
    def __init__(
        self,
        coupling_strength: float,
        decay_rate: float,
        freq_adaptation_rate: float = 0.0,
        coupling_mode: CouplingMode | None = None,
    ) -> None: ...
    @property
    def coupling_strength(self) -> float: ...
    @property
    def decay_rate(self) -> float: ...
    @property
    def freq_adaptation_rate(self) -> float: ...
    @property
    def coupling_mode(self) -> CouplingMode: ...

class PacPair:
    def __init__(
        self,
        slow_band: int,
        fast_band: int,
        modulation_depth: float,
        phase_offset: float,
    ) -> None: ...
    @property
    def slow_band(self) -> int: ...
    @property
    def fast_band(self) -> int: ...
    @property
    def modulation_depth(self) -> float: ...
    @property
    def phase_offset(self) -> float: ...

class BandNetwork:
    def __init__(
        self,
        band_sizes: list[int],
        band_params: list[BandParams],
        pac_pairs: list[PacPair],
    ) -> None: ...
    @staticmethod
    def theta_gamma(
        n_theta: int,
        n_gamma: int,
        theta_params: BandParams,
        gamma_params: BandParams,
        pac_modulation_depth: float,
        phase_offset: float = 0.0,
    ) -> BandNetwork: ...
    @staticmethod
    def delta_theta_gamma(
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
    def n_bands(self) -> int: ...
    def total_oscillators(self) -> int: ...
    def band_size(self, b: int) -> int: ...
    def band_sizes(self) -> list[int]: ...
    def theoretical_capacity(self, state: OscillatorState) -> int: ...
    def compute_derivatives(
        self, state: OscillatorState
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]: ...

def create_band_state_py(
    network: BandNetwork,
    freq_ranges: list[tuple[float, float]],
    seed: Seed,
) -> OscillatorState: ...

# --- Temporal Propagation ---
class ComplexPhasorBlender:
    def __init__(self, alpha: float) -> None: ...
    @property
    def alpha(self) -> float: ...
    def set_alpha(self, value: float) -> None: ...
    def blend(
        self,
        new_phases: NDArray[np.float64],
        old_phases: NDArray[np.float64],
    ) -> NDArray[np.float64]: ...
    def blend_scalar(self, new_phase: float, old_phase: float) -> float: ...

class EmaAmplitudeBlender:
    def __init__(self, alpha: float) -> None: ...
    @property
    def alpha(self) -> float: ...
    def set_alpha(self, value: float) -> None: ...
    @property
    def amp_min(self) -> float: ...
    @property
    def amp_max(self) -> float: ...
    def blend(
        self,
        new_amplitudes: NDArray[np.float64],
        old_amplitudes: NDArray[np.float64],
    ) -> NDArray[np.float64]: ...

class TemporalPropagator:
    def __init__(self, alpha: float) -> None: ...
    @staticmethod
    def with_separate_alpha(
        phase_alpha: float, amplitude_alpha: float
    ) -> TemporalPropagator: ...
    @property
    def phase_alpha(self) -> float: ...
    @property
    def amplitude_alpha(self) -> float: ...
    def is_initialized(self) -> bool: ...
    def propagate_init(
        self,
        phases: NDArray[np.float64],
        amplitudes: NDArray[np.float64],
    ) -> None: ...
    def propagate(
        self,
        phases: NDArray[np.float64],
        amplitudes: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]: ...
    def reset(self) -> None: ...

"""Type stubs for the compiled PRIN core extension (``prin._prin_core``).

Regenerated as the Rust API grows; keep in sync with ``crates/prin-py``.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Literal

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
    def backward(self, grad_output: object) -> list[object]: ...

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
    def parameter_values(self) -> list[object]: ...
    def load_torch_weights(self, weights: list[Any]) -> None: ...
    def forward(
        self, x: object, weights: list[Any]
    ) -> tuple[object, ResonanceLayerCtx]: ...
    def order_parameter(self, x: object, weights: list[Any]) -> object: ...
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

# --- Inhibition and sparsification bridges (WP-036A) ---
class FeedforwardInhibitionCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class FeedforwardInhibitionBridge:
    def __init__(
        self,
        delay_steps: int = 1,
        tau: float = 0.05,
        delay_fraction: float = 0.1,
    ) -> None: ...
    @property
    def delay_steps(self) -> int: ...
    @property
    def tau(self) -> float: ...
    def forward(
        self, phase: object, amplitude: object
    ) -> tuple[object, FeedforwardInhibitionCtx]: ...

class DentateGyrusConverterCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class DentateGyrusConverterBridge:
    def __init__(
        self,
        n_oscillators: int,
        k: int | None = None,
        target_sparsity: float = 0.1,
        ffi_delay: int = 1,
        ffi_tau: float = 0.05,
        fbi_delay: int = 20,
        fbi_temperature: float = 1.0,
        integration_alpha: float = 0.95,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    def forward(
        self, phase: object, amplitude: object, n_integration_steps: int
    ) -> tuple[object, DentateGyrusConverterCtx]: ...

class DGLayerCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class DGLayerBridge:
    def __init__(
        self,
        n_input: int,
        top_k: int = 8,
        ffi_delay: int = 2,
        fbi_delay: int = 20,
        n_integration_steps: int = 5,
    ) -> None: ...
    @property
    def n_input(self) -> int: ...
    @property
    def top_k(self) -> int: ...
    def forward(
        self, phase: object, amplitude: object
    ) -> tuple[object, DGLayerCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class SparsityRegularizationLossCtx:
    def backward(self, grad_output: object) -> object: ...

class SparsityRegularizationLossBridge:
    def __init__(
        self, target_sparsity: float = 0.9, temperature: float = 0.1
    ) -> None: ...
    @property
    def target_sparsity(self) -> float: ...
    @property
    def temperature(self) -> float: ...
    def forward(
        self, activations: object
    ) -> tuple[object, SparsityRegularizationLossCtx]: ...

class OscillatoryWeightInitBridge:
    def matrix(
        self,
        parameter: object,
        coupling: bool,
        coupling_scale: float,
        proj_gain: float,
        seed_counter: int,
        seed_key: int,
    ) -> object: ...
    def bias(self, parameter: object) -> object: ...

# --- Phase-to-rate and autoencoder bridges (WP-036A / 0144A2) ---
class PhaseToRateConverterCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class PhaseToRateConverterBridge:
    def __init__(
        self,
        n_oscillators: int,
        mode: str = "soft",
        sparsity: float = 0.1,
        initial_temperature: float = 1.0,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def mode(self) -> str: ...
    @property
    def sparsity(self) -> float: ...
    def forward(
        self, phase: object, amplitude: object
    ) -> tuple[object, PhaseToRateConverterCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class PhaseToRateAutoencoderCtx:
    def backward(self, grad_recon: object, grad_rates: object) -> object: ...

class PhaseToRateAutoencoderClassifyCtx:
    def backward(self, grad_output: object) -> object: ...

class PhaseToRateAutoencoderBridge:
    def __init__(
        self,
        n_input: int,
        n_oscillators: int,
        hidden: int = 256,
        n_classes: int = 10,
        sparsity: float = 0.1,
        mode: str = "soft",
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_input(self) -> int: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def n_classes(self) -> int: ...
    def forward(
        self, x: object
    ) -> tuple[object, object, PhaseToRateAutoencoderCtx]: ...
    def classify(
        self, x: object
    ) -> tuple[object, PhaseToRateAutoencoderClassifyCtx]: ...
    def load_torch_weights(self, weights: list[object]) -> None: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class DenseAutoencoderCtx:
    def backward(self, grad_recon: object, grad_codes: object) -> object: ...

class DenseAutoencoderClassifyCtx:
    def backward(self, grad_output: object) -> object: ...

class DenseAutoencoderBridge:
    def __init__(
        self,
        n_input: int,
        n_bottleneck: int,
        hidden: int = 256,
        n_classes: int = 10,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_input(self) -> int: ...
    @property
    def n_bottleneck(self) -> int: ...
    @property
    def n_classes(self) -> int: ...
    def forward(self, x: object) -> tuple[object, object, DenseAutoencoderCtx]: ...
    def classify(self, x: object) -> tuple[object, DenseAutoencoderClassifyCtx]: ...
    def load_torch_weights(self, weights: list[object]) -> None: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

# --- Hierarchical/PAC/discrete layer bridges (WP-036A / 0144A3) ---
class HierarchicalResonanceLayerCtx:
    def backward(self, grad_amplitude: object, grad_phase: object) -> object: ...

class HierarchicalResonanceLayerBridge:
    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        n_dims: int = 256,
        n_steps: int = 10,
        dt: float = 0.01,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        sparse_k: int | None = None,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_delta(self) -> int: ...
    @property
    def n_theta(self) -> int: ...
    @property
    def n_gamma(self) -> int: ...
    @property
    def n_total(self) -> int: ...
    @property
    def n_dims(self) -> int: ...
    def forward(
        self, x: object
    ) -> tuple[object, object, HierarchicalResonanceLayerCtx]: ...
    def load_torch_weights(
        self,
        proj_delta: object,
        proj_theta: object,
        proj_gamma: object,
        pac_depth_dt: object,
        pac_depth_tg: object,
    ) -> None: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class PhaseAmplitudeCouplingLayerCtx:
    def backward(self, grad_output: object) -> tuple[object, object]: ...

class PhaseAmplitudeCouplingLayerBridge:
    def __init__(self, initial_depth: float = 0.3) -> None: ...
    def forward(
        self, slow_phase: object, fast_amplitude: object
    ) -> tuple[object, PhaseAmplitudeCouplingLayerCtx]: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

class DiscreteDeltaThetaGammaLayerCtx:
    def backward(self, grad_output: object) -> list[object]: ...

class DiscreteDeltaThetaGammaLayerBridge:
    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        n_dims: int = 256,
        n_steps: int = 10,
        dt: float = 0.01,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_total(self) -> int: ...
    @property
    def n_dims(self) -> int: ...
    def parameter_values(self) -> list[object]: ...
    def forward(
        self, x: object, weights: list[Any]
    ) -> tuple[object, DiscreteDeltaThetaGammaLayerCtx]: ...
    def load_torch_weights(self, weights: list[Any]) -> None: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

# --- Standalone discrete three-band network bridge (WP-036C / 0144M1) ---
class DiscreteDeltaThetaGammaBridge:
    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        delta_freq: float = 2.0,
        theta_freq: float = 6.0,
        gamma_freq: float = 40.0,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_delta(self) -> int: ...
    @property
    def n_theta(self) -> int: ...
    @property
    def n_gamma(self) -> int: ...
    @property
    def n_total(self) -> int: ...
    def load_torch_weights(self, weights: list[object]) -> None: ...
    def step(
        self, phase: object, amplitude: object, dt: float
    ) -> tuple[object, object]: ...
    def integrate(
        self, phase: object, amplitude: object, n_steps: int, dt: float
    ) -> tuple[object, object]: ...
    def order_parameters(self, phase: object) -> tuple[float, float, float]: ...
    def pac_index(self, phase: object, amplitude: object) -> tuple[float, float]: ...

# --- Full model container bridge (WP-036A / 0144A4) ---
class PRINetModelCtx:
    def backward(self, grad_output: object) -> object: ...

class PRINetModelBridge:
    def __init__(
        self,
        n_resonances: int = 64,
        n_dims: int = 256,
        n_concepts: int = 10,
        n_layers: int = 4,
        n_steps: int = 10,
        dt: float = 0.01,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def n_resonances(self) -> int: ...
    @property
    def n_dims(self) -> int: ...
    @property
    def n_concepts(self) -> int: ...
    @property
    def n_layers(self) -> int: ...
    def forward(self, x: object) -> tuple[object, PRINetModelCtx]: ...
    def load_torch_weights(self, weights: list[object]) -> None: ...
    def state_dict(self) -> bytes: ...
    def load_state_dict(self, state: bytes) -> None: ...

# --- Torch bridges (WP-026 / Exec-WP-026 S1) ---
class OscillatoryAttentionCtx:
    def backward(
        self, grad_output: object
    ) -> tuple[object, object | None, object | None]: ...

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
        self,
        x: object,
        phase: object | None = None,
        mask: object | None = None,
    ) -> tuple[object, OscillatoryAttentionCtx]: ...
    def set_alpha(self, alpha: list[float]) -> None: ...
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

# --- Trainable-stack integration and Phase 4 gate (WP-027) ---
class TrainingResult:
    @property
    def final_train_loss(self) -> float: ...
    @property
    def final_val_loss(self) -> float: ...
    @property
    def final_val_ip(self) -> float: ...
    @property
    def best_val_loss(self) -> float: ...
    @property
    def best_epoch(self) -> int: ...
    @property
    def total_epochs(self) -> int: ...
    @property
    def train_losses(self) -> list[float]: ...
    @property
    def val_losses(self) -> list[float]: ...
    @property
    def val_ips(self) -> list[float]: ...

def train_phase_tracker(
    detection_dim: int,
    n_delta: int = 4,
    n_theta: int = 8,
    n_gamma: int = 16,
    n_discrete_steps: int = 5,
    match_threshold: float = 0.3,
    n_objects: int = 4,
    n_frames: int = 20,
    det_dim: int = 4,
    train_seqs: int = 50,
    val_seqs: int = 10,
    dataset_seed: int = 42,
    lr: float = 3e-4,
    weight_decay: float = 0.0,
    max_epochs: int = 100,
    patience: int = 10,
    smoothing_window: int = 5,
    warmup_epochs: int = 5,
    grad_clip: float = 1.0,
    model_seed: int = 0,
) -> tuple[PhaseTrackerBridge, TrainingResult]: ...

class SyncGdBridge:
    def __init__(
        self,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        sync_penalty: float = 0.1,
        critical_order: float = 0.5,
        dampening: float = 0.0,
    ) -> None: ...
    def step(
        self,
        param: object,
        grad: object | None = None,
        order_parameter: float | None = None,
    ) -> object: ...
    def state_dict(self) -> str: ...
    def load_state_dict(self, state: str) -> None: ...

class ScalrBridge:
    def __init__(
        self,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        r_min: float = 0.1,
        alpha: float = 1.0,
        warmup_steps: int = 0,
        oscillation_window: int = 20,
        oscillation_threshold: float = 0.01,
        oscillation_decay: float = 0.95,
        adaptive_r_min: bool = False,
        r_min_ema_alpha: float = 0.1,
    ) -> None: ...
    def step(
        self,
        param: object,
        grad: object | None = None,
        order_parameter: float | None = None,
    ) -> object: ...
    def state_dict(self) -> str: ...
    def load_state_dict(self, state: str) -> None: ...

class RipBridge:
    def __init__(
        self, n_oscillators: int, lr: float = 0.01, target_amplitude: float = 1.0
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    def step(
        self,
        coupling: object,
        grad: object | None = None,
        phase: object | None = None,
        amplitude: object | None = None,
    ) -> object: ...
    def state_dict(self) -> str: ...
    def load_state_dict(self, state: str) -> None: ...

# --- Constants ---
TAU: float
AMPLITUDE_MIN: float
AMPLITUDE_MAX: float
DERIV_CLAMP: float
SPARSE_EPS: float

def safe_phase_diffs_dlpack(a: object, b: object) -> object: ...
def clamp_finite_dlpack(values: object, limit: float = DERIV_CLAMP) -> object: ...

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
    def dynamics_vjp(
        self,
        state: OscillatorState,
        grad_dphase: NDArray[np.float64],
        grad_damplitude: NDArray[np.float64],
        grad_dfrequency: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]: ...

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
    def dynamics_vjp(
        self,
        state: OscillatorState,
        grad_dphase: NDArray[np.float64],
        grad_damplitude: NDArray[np.float64],
        grad_dfrequency: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]: ...

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
    def dynamics_vjp(
        self,
        state: OscillatorState,
        grad_dphase: NDArray[np.float64],
        grad_damplitude: NDArray[np.float64],
        grad_dfrequency: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]: ...

# --- Integrators ---
class EulerIntegrator:
    def __init__(
        self, guard: Literal["non_negative", "bounded"] = "non_negative"
    ) -> None: ...
    @property
    def guard(self) -> Literal["non_negative", "bounded"]: ...
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
    def __init__(
        self, guard: Literal["non_negative", "bounded"] = "non_negative"
    ) -> None: ...
    @property
    def guard(self) -> Literal["non_negative", "bounded"]: ...
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
    def step_vjp(
        self,
        model: Any,
        state: OscillatorState,
        dt: float,
        grad_phase: NDArray[np.float64],
        grad_amplitude: NDArray[np.float64],
        grad_frequency: NDArray[np.float64],
    ) -> StateDerivatives: ...
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

# --- Subconscious controller (WP-028) ---
STATE_DIM: int
CONTROL_DIM: int
CONTROLLER_INPUT_NAME: str
CONTROLLER_OUTPUT_NAME: str
MODEL_MANIFEST_FILE_NAME: str
DEFAULT_NPU_TARGET: str
DEFAULT_NPU_CACHE_KEY: str
DEFAULT_NPU_XCLBIN: str

class SubconsciousState:
    def __init__(
        self,
        r_per_band: list[float] | None = None,
        r_global: float = 0.0,
        loss_ema: float = 0.0,
        loss_variance: float = 0.0,
        grad_norm_ema: float = 0.0,
        lr_current: float = 1e-3,
        scalr_alpha: float = 1.0,
        gpu_temp: float = 0.0,
        gpu_util: float = 0.0,
        vram_pct: float = 0.0,
        cpu_util: float = 0.0,
        step_latency_p50: float = 0.0,
        step_latency_p95: float = 0.0,
        throughput: float = 0.0,
        epoch: int = 0,
        regime: str = "mean_field",
        timestamp: float = 0.0,
    ) -> None: ...
    r_per_band: list[float]
    r_global: float
    loss_ema: float
    loss_variance: float
    grad_norm_ema: float
    lr_current: float
    scalr_alpha: float
    gpu_temp: float
    gpu_util: float
    vram_pct: float
    cpu_util: float
    step_latency_p50: float
    step_latency_p95: float
    throughput: float
    epoch: int
    regime: str
    timestamp: float
    @property
    def timestamp_fraction(self) -> float: ...
    def to_tensor(self) -> NDArray[np.float32]: ...
    def clone_state(self) -> SubconsciousState: ...

class ControlSignals:
    def __init__(
        self,
        suggested_K_min: float = 0.5,
        suggested_K_max: float = 5.0,
        lr_multiplier: float = 1.0,
        regime_mf_weight: float = 0.33,
        regime_sk_weight: float = 0.33,
        regime_full_weight: float = 0.34,
        alert_level: float = 0.0,
        coupling_mode_suggestion: float = 0.0,
    ) -> None: ...
    @staticmethod
    def from_tensor(values: NDArray[np.float64]) -> ControlSignals: ...
    @property
    def suggested_K_min(self) -> float: ...
    @property
    def suggested_K_max(self) -> float: ...
    @property
    def lr_multiplier(self) -> float: ...
    @property
    def regime_mf_weight(self) -> float: ...
    @property
    def regime_sk_weight(self) -> float: ...
    @property
    def regime_full_weight(self) -> float: ...
    @property
    def alert_level(self) -> float: ...
    @property
    def coupling_mode_suggestion(self) -> float: ...
    @property
    def preferred_regime(self) -> str: ...
    def is_finite(self) -> bool: ...
    def to_tensor(self) -> NDArray[np.float32]: ...

class BackendSelection:
    @property
    def backend(self) -> Any: ...
    @property
    def reason(self) -> str: ...
    @property
    def requested(self) -> str | None: ...
    @property
    def attempt_order(self) -> list[Any]: ...
    @property
    def available_providers(self) -> list[str]: ...
    @property
    def is_degraded(self) -> bool: ...
    def provider_names(self, backend: str) -> list[str]: ...

def select_execution_backend(
    available: list[str], requested: str | None = None
) -> BackendSelection: ...
def backend_provider_names(backend: str) -> list[str]: ...
def backend_priority() -> list[str]: ...
def backend_provider_options(
    backend: str,
    sdk_root: str | os.PathLike[str] | None = None,
    firmware: str | os.PathLike[str] | None = None,
    cache_dir: str | os.PathLike[str] | None = None,
    target: str | None = None,
) -> list[dict[str, str]]: ...
def npu_firmware_candidates(
    env_override: str | None,
    sdk_root: str | os.PathLike[str],
    xclbin: str | None = None,
) -> list[str]: ...
def resolve_npu_firmware(
    env_override: str | None,
    sdk_root: str | os.PathLike[str],
    xclbin: str | None = None,
) -> str: ...
def model_sha256(path: str | os.PathLike[str]) -> str: ...
def inspect_onnx_model(path: str | os.PathLike[str]) -> dict[str, Any]: ...
def verify_model_manifest(
    models_dir: str | os.PathLike[str],
) -> list[dict[str, Any]]: ...
def validate_controller_model(
    path: str | os.PathLike[str], expected_sha256: str | None = None
) -> dict[str, Any]: ...

# --- Phase 5 integration (WP-032) ---
class SubconsciousDaemon:
    def __init__(
        self,
        callback: Callable[[NDArray[np.float32]], NDArray[np.float32]],
        interval_ms: int = 15_000,
        queue_size: int = 100,
        warmup: bool = True,
        dlq_maxlen: int = 100,
        max_errors_before_escalation: int = 10,
    ) -> None: ...
    def submit_state(self, state: SubconsciousState) -> None: ...
    def get_control(self) -> ControlSignals: ...
    def stop(self, timeout_ms: int = 5_000) -> bool: ...
    @property
    def inference_count(self) -> int: ...
    @property
    def error_count(self) -> int: ...
    @property
    def pending_states(self) -> int: ...

class TrainingHooks:
    def __init__(
        self, loss_ema_alpha: float = 0.1, latency_window: int = 100
    ) -> None: ...
    def on_step_end(
        self,
        elapsed_ms: float,
        loss: float,
        grad_norms: list[float] | None = None,
    ) -> None: ...
    def on_epoch_end(
        self,
        epoch: int,
        loss: float | None = None,
        r_per_band: list[float] | None = None,
        r_global: float | None = None,
        lr_current: float = 1e-3,
        scalr_alpha: float = 1.0,
        regime: str = "mean_field",
        timestamp: float = 0.0,
    ) -> SubconsciousState: ...
    @property
    def loss_ema(self) -> float: ...
    @property
    def grad_norm_ema(self) -> float: ...
    @property
    def step_count(self) -> int: ...

class MotSummary:
    mota: float
    motp: float
    idf1: float
    num_matches: int
    num_switches: int
    num_misses: int
    num_false_positives: int
    num_objects: int

class MotAccumulator:
    def __init__(self, max_switch_time: int | None = None) -> None: ...
    def update(
        self,
        frame_id: int,
        object_ids: list[int],
        hypothesis_ids: list[int],
        distances: list[list[float]],
    ) -> None: ...
    def summary(self) -> MotSummary: ...

def iou_distance_matrix(
    objects: list[tuple[float, float, float, float]],
    hypotheses: list[tuple[float, float, float, float]],
    max_iou_distance: float = 0.5,
) -> list[list[float]]: ...

class TemporalMetrics:
    ip: float
    idsw: int
    temporal_smoothness: float
    track_fragmentation_rate: float
    identity_overcount: float
    mostly_tracked: float
    mostly_lost: float
    mean_track_duration: float
    median_track_duration: float
    recovery_speed: float
    binding_robustness: float

def py_compute_full_temporal_metrics(
    matches_history: list[list[int]],
    n_objects: int,
    positions: list[list[tuple[float, float]]] | None = None,
    occlusion_mask: list[list[bool]] | None = None,
    ip_baseline: float | None = None,
) -> TemporalMetrics: ...
def identity_switches(matches_history: list[list[int]], n_objects: int) -> int: ...
def track_fragmentation_rate(
    matches_history: list[list[int]], n_objects: int
) -> float: ...
def identity_overcount(matches_history: list[list[int]], n_objects: int) -> float: ...
def mostly_tracked_lost(
    matches_history: list[list[int]],
    n_objects: int,
    tracked_threshold: float = 0.8,
    lost_threshold: float = 0.2,
) -> tuple[float, float]: ...
def track_duration_stats(
    matches_history: list[list[int]], n_objects: int
) -> tuple[float, float]: ...
def recovery_speed(
    matches_history: list[list[int]],
    occlusion_mask: list[list[bool]],
    n_objects: int,
) -> float: ...
def temporal_smoothness(positions: list[list[tuple[float, float]]]) -> float: ...
def binding_robustness_score(ip_perturbed: float, ip_baseline: float) -> float: ...

class BootstrapCi:
    mean: float
    ci_lower: float
    ci_upper: float
    ci_width: float
    se: float

class WelchTTest:
    t_stat: float
    p_value: float
    cohens_d: float
    mean_diff: float

class AdversarialEvalResult:
    clean_ip: float
    adv_ip: float
    degradation: float
    per_seq_clean: list[float]
    per_seq_adv: list[float]

def py_bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 10_000,
    alpha: float = 0.05,
    seed_counter: int = 0,
    seed_key: int = 0,
) -> BootstrapCi: ...
def py_welch_t_test(group_a: list[float], group_b: list[float]) -> WelchTTest: ...
def cohens_d(group_a: list[float], group_b: list[float]) -> float: ...
def compute_p_value(group_a: list[float], group_b: list[float]) -> float: ...
def py_adversarial_evaluate_phase_tracker(
    tracker: PhaseTrackerBridge,
    epsilon: float,
    attack: str = "fgsm",
    pgd_steps: int = 20,
    n_sequences: int = 4,
    n_objects: int = 4,
    n_frames: int = 20,
    detection_dim: int = 4,
    seed: int = 0,
) -> AdversarialEvalResult: ...
def py_adversarial_evaluate_slot_attention(
    tracker: TemporalSlotAttentionMOTBridge,
    epsilon: float,
    attack: str = "fgsm",
    pgd_steps: int = 20,
    n_sequences: int = 4,
    n_objects: int = 4,
    n_frames: int = 20,
    detection_dim: int = 4,
    seed: int = 0,
) -> AdversarialEvalResult: ...

# --- Tensor decomposition + WP-023 trainable primitives (WP-036 S1 / 0141B) ---
class PolyadicTensorBridge:
    def __init__(self, shape: list[int], rank: int) -> None: ...
    @property
    def rank(self) -> int: ...
    @property
    def shape(self) -> list[int]: ...
    @property
    def is_decomposed(self) -> bool: ...
    def decompose(self, tensor: object) -> None: ...
    def reconstruction_error(self, original: object) -> float: ...
    @staticmethod
    def mode_n_unfold(tensor: object, mode: int) -> object: ...
    def reconstruct(self) -> object: ...
    def core(self) -> object: ...
    def factors(self) -> list[object]: ...

class CPDecompositionBridge:
    def __init__(
        self,
        shape: list[int],
        rank: int,
        max_iter: int = 100,
        tol: float = 1e-6,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None: ...
    @property
    def rank(self) -> int: ...
    @property
    def shape(self) -> list[int]: ...
    @property
    def is_decomposed(self) -> bool: ...
    def decompose(self, tensor: object) -> None: ...
    def reconstruct(self) -> object: ...
    def weights(self) -> object: ...
    def factors(self) -> list[object]: ...

class DSiLUCtx:
    def backward(self, grad_output: object) -> object: ...

class DSiLUBridge:
    def __init__(self) -> None: ...
    def forward(self, z: object) -> tuple[object, DSiLUCtx]: ...

class PhaseActivationCtx:
    def backward(self, grad_output: object) -> object: ...

class PhaseActivationBridge:
    def __init__(self) -> None: ...
    def forward(self, z: object) -> tuple[object, PhaseActivationCtx]: ...

class HolomorphicActivationCtx:
    def backward(self, grad_re: object, grad_im: object) -> tuple[object, object]: ...

class HolomorphicActivationBridge:
    def __init__(self, scale: float = 1.0) -> None: ...
    @property
    def scale(self) -> float: ...
    def forward(
        self, re: object, im: object
    ) -> tuple[object, object, HolomorphicActivationCtx]: ...

class FeedbackInhibitionCtx:
    def backward(self, grad_output: object) -> object: ...

class FeedbackInhibitionBridge:
    def __init__(
        self,
        n_oscillators: int,
        k: int | None = None,
        sparsity: float = 0.1,
        temperature: float = 1.0,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def k(self) -> int: ...
    @property
    def temperature(self) -> float: ...
    def forward(self, rates: object) -> tuple[object, FeedbackInhibitionCtx]: ...

class HolomorphicEnergyCtx:
    def backward(self, grad_output: object) -> tuple[object, object, object]: ...

class HolomorphicEnergyBridge:
    def __init__(self, n_oscillators: int) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    def forward(
        self,
        re: object,
        im: object,
        coupling: object,
        task_loss: object | None = None,
        beta: float = 0.0,
    ) -> tuple[object, HolomorphicEnergyCtx]: ...

class HolomorphicEpTrainer:
    def __init__(
        self,
        n_oscillators: int,
        beta: float = 0.1,
        free_steps: int = 50,
        nudge_steps: int = 20,
    ) -> None: ...
    beta: float
    def coupling_gradient(
        self,
        layer: ResonanceLayerBridge,
        x: object,
        target_direction: object,
    ) -> object: ...
    def free_energy(
        self, layer: ResonanceLayerBridge, x: object, coupling: object
    ) -> object: ...

# --- CPU compatibility kernels and sweeps (WP-036 / 0141C) ---
def pytorch_mean_field_rk4_step(
    phase: list[float],
    amplitude: list[float],
    frequency: list[float],
    k: float,
    decay: float,
    gamma: float,
    dt: float,
) -> tuple[list[float], list[float], list[float]]: ...
def pytorch_sparse_knn_coupling(
    phase: list[float],
    amplitude: list[float],
    frequency: list[float],
    neighbors: list[int],
    k: float,
    decay: float,
    gamma: float,
) -> tuple[list[float], list[float], list[float]]: ...
def pytorch_pac_modulation(
    slow_phase: list[float],
    fast_amplitude: list[float],
    modulation_depth: float,
    amp_min: float = 1e-6,
    amp_max: float = 10.0,
) -> list[float]: ...
def pytorch_hierarchical_order_param(
    phase: list[float], band_sizes: list[int]
) -> list[float]: ...
def pytorch_multi_rate_rk4_step(
    phase: list[float],
    amplitude: list[float],
    frequency: list[float],
    k: float,
    decay: float,
    gamma: float,
    dt: float,
    sub_steps: int,
    mean_field: bool = True,
) -> tuple[list[float], list[float], list[float]]: ...
def pytorch_multi_rate_derivatives(
    phase: list[float],
    amplitude: list[float],
    frequency: list[float],
    freq_band: list[int],
    k: float,
    decay: float,
    gamma: float,
    band_frequencies: list[float] | None = None,
) -> tuple[list[float], list[float], list[float]]: ...
def pytorch_fused_sub_step_rk4(
    phase: list[float],
    amplitude: list[float],
    frequency: list[float],
    freq_band: list[int],
    k: float,
    decay: float,
    gamma: float,
    dt: float,
    sub_steps_per_band: list[int] | None = None,
) -> tuple[list[float], list[float], list[float]]: ...
def pytorch_cross_band_coupling(
    slow_phase: list[float],
    fast_phase: list[float],
    fast_amplitude: list[float],
    parent_idx: list[int],
    modulation_depth: float = 0.3,
    epsilon: float = 1e-6,
) -> tuple[list[float], list[float]]: ...
def pytorch_fused_discrete_step(
    phase: list[float],
    amplitude: list[float],
    freq_delta: list[float],
    freq_theta: list[float],
    freq_gamma: list[float],
    w_delta: list[float],
    w_theta: list[float],
    w_gamma: list[float],
    mu_delta: float,
    mu_theta: float,
    mu_gamma: float,
    n_delta: int,
    n_theta: int,
    n_gamma: int,
    dt: float = 0.01,
) -> tuple[list[float], list[float]]: ...
def pytorch_fused_discrete_step_full(
    phase: list[float],
    amplitude: list[float],
    freq_delta: list[float],
    freq_theta: list[float],
    freq_gamma: list[float],
    w_delta: list[float],
    w_theta: list[float],
    w_gamma: list[float],
    w_pac_dt_weight: list[float],
    w_pac_dt_bias: list[float],
    w_pac_tg_weight: list[float],
    w_pac_tg_bias: list[float],
    mu_delta: float,
    mu_theta: float,
    mu_gamma: float,
    dt: float = 0.01,
    n_delta: int = 4,
    n_theta: int = 8,
    n_gamma: int = 32,
) -> tuple[list[float], list[float]]: ...
def build_knn_neighbors(
    n_oscillators: int, k: int = 8, seed_counter: int = 0, seed_key: int = 0
) -> list[int]: ...
def sparse_coupling_matrix(
    n_oscillators: int,
    sparsity: float = 0.9,
    coupling_strength: float = 1.0,
    symmetric: bool = True,
    seed_counter: int = 0,
    seed_key: int = 0,
) -> list[float]: ...
def sparse_coupling_matrix_csr(
    n_oscillators: int,
    sparsity: float = 0.95,
    coupling_strength: float = 1.0,
    symmetric: bool = True,
    seed_counter: int = 0,
    seed_key: int = 0,
) -> tuple[list[int], list[int], list[float]]: ...
def csr_coupling_step(
    phase: list[float],
    crow_indices: list[int],
    col_indices: list[int],
    values: list[float],
) -> list[float]: ...
def sparse_knn_coupling_step(
    phase: list[float],
    amplitude: list[float],
    neighbors: list[int],
    coupling_strength: float = 2.0,
) -> list[float]: ...
def sweep_coupling_params(
    n_oscillators: int = 64,
    k_values: list[float] | None = None,
    m_values: list[float] | None = None,
    n_steps: int = 100,
    dt: float = 0.01,
    seed_counter: int = 0,
    seed_key: int = 0,
) -> list[dict[str, float]]: ...
def detect_oscillation(
    r_history: list[float], window: int = 20, threshold: float = 0.01
) -> bool: ...
def phase_to_rate(
    phase: list[float],
    amplitude: list[float],
    mode: str = "soft",
    sparsity: float = 0.1,
    temperature: float = 1.0,
) -> list[float]: ...

# --- OscilloSim-compat + Year-4-Q1 owners (WP-036C S1 / 0144M5) ---
def oscillo_compat_run(
    n: int,
    coupling_strength: float,
    mode: str,
    k_neighbors: int,
    sparsity: float,
    mu: float,
    freq_mean: float,
    freq_std: float,
    phase_lag: float,
    p_rewire: float,
    integrator: str,
    seed: int,
    n_steps: int,
    dt: float,
    record_trajectory: bool,
    record_interval: int,
    coupling_weights: list[float] | None = None,
    initial_phase: list[float] | None = None,
    initial_amplitude: list[float] | None = None,
) -> tuple[
    list[float],
    list[float],
    list[float],
    float,
    float,
    list[list[float]] | None,
]: ...
def ring_topology_indices(n: int, k: int) -> list[int]: ...
def small_world_topology_indices(
    n: int, k: int, p_rewire: float, seed: int
) -> list[int]: ...
def cosine_coupling_kernel_row(n: int, k: int, a: float) -> list[float]: ...
def chimera_initial_condition(n: int, seed: int) -> list[float]: ...
def gaussian_bump_ic(
    n: int, a0: float, sigma_ratio: float, phi0: float, noise_amp: float, seed: int
) -> list[float]: ...
def half_sync_half_random_ic(
    n: int, sync_phase: float, noise_amp: float, seed: int
) -> list[float]: ...
def y4q1_bootstrap_ci(
    values: list[float], n_bootstrap: int = 10000, alpha: float = 0.05, seed: int = 42
) -> tuple[float, float, float, float, float]: ...
def y4q1_cohens_d(group_a: list[float], group_b: list[float]) -> float: ...
def y4q1_welch_t_test(
    group_a: list[float], group_b: list[float]
) -> tuple[float, float, float, float]: ...
def y4q1_spatial_correlation(values: list[float], max_lag: int = 50) -> list[float]: ...
def y4q1_polyfit(x: list[float], y: list[float], degree: int) -> list[float]: ...

# --- GPU engine bindings (WP-036D / 0144I1) ---
# Available only when prin-py is built with the `cuda` or `wgpu` feature.
class GpuSparseKuramoto:
    """Sparse Kuramoto coupling dispatched through prin-kernels GPU backends."""

    def __init__(
        self,
        n: int,
        decay_rate: float,
        freq_adaptation_rate: float,
        k: float,
        crow_indices: list[int],
        col_indices: list[int],
        values: list[float],
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def decay_rate(self) -> float: ...
    @property
    def freq_adaptation_rate(self) -> float: ...
    @property
    def k(self) -> float: ...
    @staticmethod
    def from_knn_phase(
        n: int,
        k_neighbors: int,
        coupling_strength: float,
        decay_rate: float,
        freq_adaptation_rate: float,
        phase: object,
    ) -> GpuSparseKuramoto: ...
    def compute_derivatives(
        self, phase: object, amplitude: object, frequency: object
    ) -> tuple[object, object, object]: ...

class GpuMeanFieldEngine:
    """Dense mean-field RK4 engine stepped via the fused prin-kernels kernel."""

    def __init__(
        self,
        phase: object,
        amplitude: object,
        frequency: object,
        k: float,
        decay: float,
        gamma: float,
        dt: float,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def dt(self) -> float: ...
    def step(self) -> dict[str, object]: ...
    def state(self) -> tuple[object, object, object]: ...

class GpuBandStepper:
    """Fused three-band (delta/theta/gamma) discrete-time stepper."""

    def __init__(
        self,
        phase: object,
        amplitude: object,
        frequency: object,
        band_sizes: list[int],
        ks: list[float],
        decays: list[float],
        gammas: list[float],
        pac_modulation_depths: list[float],
        pac_phase_offsets: list[float],
        amp_min: float,
        amp_max: float,
        dt: float,
    ) -> None: ...
    @property
    def n_oscillators(self) -> int: ...
    @property
    def band_sizes(self) -> list[int]: ...
    @property
    def dt(self) -> float: ...
    def step(self) -> dict[str, object]: ...
    def state(self) -> tuple[object, object, object]: ...

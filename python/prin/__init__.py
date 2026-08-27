"""PRIN -- Phase-Resonance Interference Network.

Public Python API for PRIN, the from-scratch rebuild of PRINet 3.0. The
numerical core lives in the compiled Rust extension ``prin._prin_core``; this
package holds API ergonomics, PyTorch bridges, plotting, and orchestration
only (no numerics -- see the Target Architecture design rules in
``DOCS/PRIN_Project_Plan.md``).

Subpackages:
    prin.dynamics: oscillator state, models, integrators, coupling, PAC.
    prin.dlpack: zero-copy DLPack tensor exchange between PyTorch and the
    PRIN Rust core.
    prin.metrics: synchronization, coherence, spectral, energy, and chimera
    metrics.
    prin.nn: torch.nn.Module wrappers, autograd.Function bridges, baselines.
    prin.train: Rust-native trainable-stack orchestration entry points
    (temporal CLEVR-N training pipeline).
    prin.daemon: subconscious controller -- ONNX inference, execution-provider
    selection (VitisAI -> DirectML -> CPU), and model validation.
    prin.eval: MOT evaluation and temporal metrics.
    prin.experiments: ablation, stats, adversarial, and training frameworks.
    prin.parity: golden-trajectory corpus, manifest/loader, and differential
    harness for numerical parity against PRINet 3.0.
    prin.reporting: benchmark JSON reports, figures, tables, profiler.
"""

from __future__ import annotations

from prin._compat import (
    BackendUnavailableError,
    DeltaThetaGammaNetwork,
    OscillatorModel,
    RIPOptimizer,
    SCALROptimizer,
    SynchronizedGradientDescent,
    TemporalPhasePropagator,
    ThetaGammaNetwork,
    cuda_fused_kernel_available,
    fused_discrete_step_cuda,
    temporal_recovery_speed,
    triton_available,
    triton_fused_discrete_step,
    triton_fused_mean_field_rk4_step,
    triton_hierarchical_order_param,
    triton_pac_modulation,
    triton_sparse_knn_coupling,
)
from prin.daemon import (
    CONTROL_DIM,
    STATE_DIM,
    BackendType,
    ControlSignals,
    SubconsciousController,
    SubconsciousDaemon,
    SubconsciousState,
    backend_info,
    create_session,
    detect_best_backend,
    directml_available,
    npu_available,
)
from prin.dynamics import (
    ExponentialIntegrator,
    HopfOscillator,
    KuramotoOscillator,
    MultiRateIntegrator,
    OscillatorState,
    PhaseAmplitudeCoupling,
    StuartLandauOscillator,
)
from prin.eval import (
    TemporalMetrics,
    binding_robustness_score,
    compute_full_temporal_metrics,
    identity_overcount,
    identity_switches,
    mostly_tracked_lost,
    temporal_smoothness,
    track_duration_stats,
    track_fragmentation_rate,
)
from prin.experiments import compute_p_value
from prin.metrics import (
    bimodality_index,
    build_phase_knn,
    inter_frame_phase_correlation,
    kuramoto_order_parameter,
    local_order_parameter,
    mean_phase_coherence,
    phase_coherence_matrix,
    sparse_mean_phase_coherence,
    sparse_synchronization_energy,
)
from prin.nn import (
    FeedbackInhibition,
    GatedPhaseActivation,
    HolomorphicActivation,
    HolomorphicEnergy,
    HolomorphicEPTrainer,
    HybridPRINetV2,
    OscillatoryAttention,
    PhaseActivation,
    PhaseTracker,
    PhaseTrackerFrozen,
    PhaseTrackerStatic,
    ResonanceLayer,
    SlotAttentionFrozen,
    SlotAttentionModule,
    SlotAttentionNoGRU,
    TemporalSlotAttentionMOT,
    dSiLU,
)
from prin.reporting import (
    configure_neurips_style,
    fig_ablation_results,
    fig_chimera_heatmap,
    fig_clevr_n_capacity,
    fig_gold_standard_chimera,
    fig_mot_identity_preservation,
    fig_oscillosim_scaling,
    fig_parameter_efficiency,
    fig_statistical_summary,
    fig_training_curves,
    generate_all_figures,
    generate_all_tables,
    generate_benchmark_report,
    generate_leaderboard,
    generate_scalr_metrics_report,
    table_ablation_variants,
    table_chimera_gold_standard,
    table_occlusion_sweep,
    table_oscillosim_scaling,
    table_parameter_efficiency,
    table_statistical_summary,
)
from prin.tensor import CPDecomposition, PolyadicTensor
from prin.train import TrainingResult

__version__ = "0.3.0-alpha.1"

try:
    from prin._prin_core import core_version
except ImportError as _exc:  # pragma: no cover - build-environment guard
    raise ImportError(
        "The compiled PRIN core extension (prin._prin_core) is not available. "
        "Build it with: maturin develop -m crates/prin-py/Cargo.toml"
    ) from _exc

__all__ = [
    "CONTROL_DIM",
    "STATE_DIM",
    "BackendType",
    "BackendUnavailableError",
    "CPDecomposition",
    "ControlSignals",
    "DeltaThetaGammaNetwork",
    "ExponentialIntegrator",
    "FeedbackInhibition",
    "GatedPhaseActivation",
    "HolomorphicActivation",
    "HolomorphicEPTrainer",
    "HolomorphicEnergy",
    "HopfOscillator",
    "HybridPRINetV2",
    "KuramotoOscillator",
    "MultiRateIntegrator",
    "OscillatorModel",
    "OscillatorState",
    "OscillatoryAttention",
    "PhaseActivation",
    "PhaseAmplitudeCoupling",
    "PhaseTracker",
    "PhaseTrackerFrozen",
    "PhaseTrackerStatic",
    "PolyadicTensor",
    "RIPOptimizer",
    "ResonanceLayer",
    "SCALROptimizer",
    "SlotAttentionFrozen",
    "SlotAttentionModule",
    "SlotAttentionNoGRU",
    "StuartLandauOscillator",
    "SubconsciousController",
    "SubconsciousDaemon",
    "SubconsciousState",
    "SynchronizedGradientDescent",
    "TemporalMetrics",
    "TemporalPhasePropagator",
    "TemporalSlotAttentionMOT",
    "ThetaGammaNetwork",
    "TrainingResult",
    "__version__",
    "backend_info",
    "bimodality_index",
    "binding_robustness_score",
    "build_phase_knn",
    "compute_full_temporal_metrics",
    "compute_p_value",
    "configure_neurips_style",
    "core_version",
    "create_session",
    "cuda_fused_kernel_available",
    "dSiLU",
    "detect_best_backend",
    "directml_available",
    "fig_ablation_results",
    "fig_chimera_heatmap",
    "fig_clevr_n_capacity",
    "fig_gold_standard_chimera",
    "fig_mot_identity_preservation",
    "fig_oscillosim_scaling",
    "fig_parameter_efficiency",
    "fig_statistical_summary",
    "fig_training_curves",
    "fused_discrete_step_cuda",
    "generate_all_figures",
    "generate_all_tables",
    "generate_benchmark_report",
    "generate_leaderboard",
    "generate_scalr_metrics_report",
    "identity_overcount",
    "identity_switches",
    "inter_frame_phase_correlation",
    "kuramoto_order_parameter",
    "local_order_parameter",
    "mean_phase_coherence",
    "mostly_tracked_lost",
    "npu_available",
    "phase_coherence_matrix",
    "sparse_mean_phase_coherence",
    "sparse_synchronization_energy",
    "table_ablation_variants",
    "table_chimera_gold_standard",
    "table_occlusion_sweep",
    "table_oscillosim_scaling",
    "table_parameter_efficiency",
    "table_statistical_summary",
    "temporal_recovery_speed",
    "temporal_smoothness",
    "track_duration_stats",
    "track_fragmentation_rate",
    "triton_available",
    "triton_fused_discrete_step",
    "triton_fused_mean_field_rk4_step",
    "triton_hierarchical_order_param",
    "triton_pac_modulation",
    "triton_sparse_knn_coupling",
]

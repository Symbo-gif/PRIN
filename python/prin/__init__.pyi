"""Type declarations for the PRIN top-level compatibility surface."""

from __future__ import annotations

from prin._compat import BackendUnavailableError as BackendUnavailableError
from prin._compat import DeltaThetaGammaNetwork as DeltaThetaGammaNetwork
from prin._compat import OscillatorModel as OscillatorModel
from prin._compat import RIPOptimizer as RIPOptimizer
from prin._compat import SCALROptimizer as SCALROptimizer
from prin._compat import SynchronizedGradientDescent as SynchronizedGradientDescent
from prin._compat import TemporalPhasePropagator as TemporalPhasePropagator
from prin._compat import ThetaGammaNetwork as ThetaGammaNetwork
from prin._compat import cuda_fused_kernel_available as cuda_fused_kernel_available
from prin._compat import fused_discrete_step_cuda as fused_discrete_step_cuda
from prin._compat import temporal_recovery_speed as temporal_recovery_speed
from prin._compat import triton_available as triton_available
from prin._compat import triton_fused_discrete_step as triton_fused_discrete_step
from prin._compat import (
    triton_fused_mean_field_rk4_step as triton_fused_mean_field_rk4_step,
)
from prin._compat import (
    triton_hierarchical_order_param as triton_hierarchical_order_param,
)
from prin._compat import triton_pac_modulation as triton_pac_modulation
from prin._compat import triton_sparse_knn_coupling as triton_sparse_knn_coupling
from prin._prin_core import core_version as core_version
from prin.daemon import CONTROL_DIM as CONTROL_DIM
from prin.daemon import STATE_DIM as STATE_DIM
from prin.daemon import BackendType as BackendType
from prin.daemon import ControlSignals as ControlSignals
from prin.daemon import SubconsciousController as SubconsciousController
from prin.daemon import SubconsciousDaemon as SubconsciousDaemon
from prin.daemon import SubconsciousState as SubconsciousState
from prin.daemon import backend_info as backend_info
from prin.daemon import create_session as create_session
from prin.daemon import detect_best_backend as detect_best_backend
from prin.daemon import directml_available as directml_available
from prin.daemon import npu_available as npu_available
from prin.dynamics import ExponentialIntegrator as ExponentialIntegrator
from prin.dynamics import HopfOscillator as HopfOscillator
from prin.dynamics import KuramotoOscillator as KuramotoOscillator
from prin.dynamics import MultiRateIntegrator as MultiRateIntegrator
from prin.dynamics import OscillatorState as OscillatorState
from prin.dynamics import PhaseAmplitudeCoupling as PhaseAmplitudeCoupling
from prin.dynamics import StuartLandauOscillator as StuartLandauOscillator
from prin.eval import TemporalMetrics as TemporalMetrics
from prin.eval import binding_robustness_score as binding_robustness_score
from prin.eval import compute_full_temporal_metrics as compute_full_temporal_metrics
from prin.eval import identity_overcount as identity_overcount
from prin.eval import identity_switches as identity_switches
from prin.eval import mostly_tracked_lost as mostly_tracked_lost
from prin.eval import temporal_smoothness as temporal_smoothness
from prin.eval import track_duration_stats as track_duration_stats
from prin.eval import track_fragmentation_rate as track_fragmentation_rate
from prin.experiments import compute_p_value as compute_p_value
from prin.metrics import bimodality_index as bimodality_index
from prin.metrics import build_phase_knn as build_phase_knn
from prin.metrics import inter_frame_phase_correlation as inter_frame_phase_correlation
from prin.metrics import kuramoto_order_parameter as kuramoto_order_parameter
from prin.metrics import local_order_parameter as local_order_parameter
from prin.metrics import mean_phase_coherence as mean_phase_coherence
from prin.metrics import phase_coherence_matrix as phase_coherence_matrix
from prin.metrics import sparse_mean_phase_coherence as sparse_mean_phase_coherence
from prin.metrics import (
    sparse_synchronization_energy as sparse_synchronization_energy,
)
from prin.nn import FeedbackInhibition as FeedbackInhibition
from prin.nn import GatedPhaseActivation as GatedPhaseActivation
from prin.nn import HolomorphicActivation as HolomorphicActivation
from prin.nn import HolomorphicEnergy as HolomorphicEnergy
from prin.nn import HolomorphicEPTrainer as HolomorphicEPTrainer
from prin.nn import HybridPRINetV2 as HybridPRINetV2
from prin.nn import OscillatoryAttention as OscillatoryAttention
from prin.nn import PhaseActivation as PhaseActivation
from prin.nn import PhaseTracker as PhaseTracker
from prin.nn import PhaseTrackerFrozen as PhaseTrackerFrozen
from prin.nn import PhaseTrackerStatic as PhaseTrackerStatic
from prin.nn import ResonanceLayer as ResonanceLayer
from prin.nn import SlotAttentionFrozen as SlotAttentionFrozen
from prin.nn import SlotAttentionModule as SlotAttentionModule
from prin.nn import SlotAttentionNoGRU as SlotAttentionNoGRU
from prin.nn import TemporalSlotAttentionMOT as TemporalSlotAttentionMOT
from prin.nn import dSiLU as dSiLU
from prin.reporting import configure_neurips_style as configure_neurips_style
from prin.reporting import fig_ablation_results as fig_ablation_results
from prin.reporting import fig_chimera_heatmap as fig_chimera_heatmap
from prin.reporting import fig_clevr_n_capacity as fig_clevr_n_capacity
from prin.reporting import fig_gold_standard_chimera as fig_gold_standard_chimera
from prin.reporting import (
    fig_mot_identity_preservation as fig_mot_identity_preservation,
)
from prin.reporting import fig_oscillosim_scaling as fig_oscillosim_scaling
from prin.reporting import fig_parameter_efficiency as fig_parameter_efficiency
from prin.reporting import fig_statistical_summary as fig_statistical_summary
from prin.reporting import fig_training_curves as fig_training_curves
from prin.reporting import generate_all_figures as generate_all_figures
from prin.reporting import generate_all_tables as generate_all_tables
from prin.reporting import generate_benchmark_report as generate_benchmark_report
from prin.reporting import generate_leaderboard as generate_leaderboard
from prin.reporting import (
    generate_scalr_metrics_report as generate_scalr_metrics_report,
)
from prin.reporting import table_ablation_variants as table_ablation_variants
from prin.reporting import (
    table_chimera_gold_standard as table_chimera_gold_standard,
)
from prin.reporting import table_occlusion_sweep as table_occlusion_sweep
from prin.reporting import table_oscillosim_scaling as table_oscillosim_scaling
from prin.reporting import (
    table_parameter_efficiency as table_parameter_efficiency,
)
from prin.reporting import table_statistical_summary as table_statistical_summary
from prin.tensor import CPDecomposition as CPDecomposition
from prin.tensor import PolyadicTensor as PolyadicTensor
from prin.train import TrainingResult as TrainingResult

__version__: str
__all__: list[str]

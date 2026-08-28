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
from prin.kernels import build_knn_neighbors as build_knn_neighbors
from prin.kernels import csr_coupling_step as csr_coupling_step
from prin.kernels import detect_oscillation as detect_oscillation
from prin.kernels import phase_to_rate as phase_to_rate
from prin.kernels import pytorch_cross_band_coupling as pytorch_cross_band_coupling
from prin.kernels import pytorch_fused_discrete_step as pytorch_fused_discrete_step
from prin.kernels import (
    pytorch_fused_discrete_step_full as pytorch_fused_discrete_step_full,
)
from prin.kernels import pytorch_fused_sub_step_rk4 as pytorch_fused_sub_step_rk4
from prin.kernels import (
    pytorch_hierarchical_order_param as pytorch_hierarchical_order_param,
)
from prin.kernels import (
    pytorch_mean_field_rk4_step as pytorch_mean_field_rk4_step,
)
from prin.kernels import (
    pytorch_multi_rate_derivatives as pytorch_multi_rate_derivatives,
)
from prin.kernels import pytorch_multi_rate_rk4_step as pytorch_multi_rate_rk4_step
from prin.kernels import pytorch_pac_modulation as pytorch_pac_modulation
from prin.kernels import pytorch_sparse_knn_coupling as pytorch_sparse_knn_coupling
from prin.kernels import sparse_coupling_matrix as sparse_coupling_matrix
from prin.kernels import sparse_coupling_matrix_csr as sparse_coupling_matrix_csr
from prin.kernels import sparse_knn_coupling_step as sparse_knn_coupling_step
from prin.kernels import sweep_coupling_params as sweep_coupling_params
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
from prin.nn import HybridCLEVRN as HybridCLEVRN
from prin.nn import HybridPRINet as HybridPRINet
from prin.nn import HybridPRINetV2 as HybridPRINetV2
from prin.nn import HybridPRINetV2CLEVRN as HybridPRINetV2CLEVRN
from prin.nn import InterleavedHybridPRINet as InterleavedHybridPRINet
from prin.nn import OscillatoryAttention as OscillatoryAttention
from prin.nn import PhaseActivation as PhaseActivation
from prin.nn import PhaseTracker as PhaseTracker
from prin.nn import PhaseTrackerFrozen as PhaseTrackerFrozen
from prin.nn import PhaseTrackerStatic as PhaseTrackerStatic
from prin.nn import ResonanceLayer as ResonanceLayer
from prin.nn import SlotAttentionCLEVRN as SlotAttentionCLEVRN
from prin.nn import SlotAttentionFrozen as SlotAttentionFrozen
from prin.nn import SlotAttentionModule as SlotAttentionModule
from prin.nn import SlotAttentionNoGRU as SlotAttentionNoGRU
from prin.nn import TemporalHybridPRINet as TemporalHybridPRINet
from prin.nn import TemporalSlotAttentionMOT as TemporalSlotAttentionMOT
from prin.nn import dSiLU as dSiLU
from prin.nn import AlternatingOptimizer as AlternatingOptimizer
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
from prin.solvers import BatchedRK45Solver as BatchedRK45Solver
from prin.solvers import FixedStepRK4Solver as FixedStepRK4Solver
from prin.solvers import SolverResult as SolverResult
from prin.solvers import (
    gradient_checkpoint_integration as gradient_checkpoint_integration,
)
from prin.simulation import LargeScaleOscillatorSystem as LargeScaleOscillatorSystem
from prin.simulation import OscilloSim as OscilloSim
from prin.simulation import OscillatorPruner as OscillatorPruner
from prin.simulation import SimulationResult as SimulationResult
from prin.simulation import quick_simulate as quick_simulate
from prin.tensor import CPDecomposition as CPDecomposition
from prin.tensor import PolyadicTensor as PolyadicTensor
from prin.topology import ring_topology as ring_topology
from prin.topology import small_world_topology as small_world_topology
from prin.train import TrainingResult as TrainingResult
from prin.temporal_training import MultiSeedResult as MultiSeedResult
from prin.temporal_training import SequenceData as SequenceData
from prin.temporal_training import TemporalTrainer as TemporalTrainer
from prin.temporal_training import TrainingSnapshot as TrainingSnapshot
from prin.temporal_training import count_parameters as count_parameters
from prin.temporal_training import generate_dataset as generate_dataset
from prin.temporal_training import (
    generate_temporal_clevr_n as generate_temporal_clevr_n,
)
from prin.temporal_training import (
    hungarian_similarity_loss as hungarian_similarity_loss,
)
from prin.temporal_training import (
    temporal_smoothness_loss as temporal_smoothness_loss,
)
from prin.temporal_training import train_multi_seed as train_multi_seed
from prin.training_hooks import ActiveControlTrainer as ActiveControlTrainer
from prin.training_hooks import ControlSignalBuffer as ControlSignalBuffer
from prin.training_hooks import StateCollector as StateCollector
from prin.training_hooks import TelemetryLogger as TelemetryLogger
from prin.training_hooks import collect_system_state as collect_system_state
from prin.training_hooks import create_ablation_tracker as create_ablation_tracker
from prin.y4q1_tools import AblationConfig as AblationConfig
from prin.y4q1_tools import AblationHybridPRINetV2 as AblationHybridPRINetV2
from prin.y4q1_tools import ExtendedTrainingResult as ExtendedTrainingResult
from prin.y4q1_tools import count_flops as count_flops
from prin.y4q1_tools import create_ablation_model as create_ablation_model
from prin.y4q1_tools import measure_wall_time as measure_wall_time
from prin.y4q1_tools import (
    train_clevr_n_extended as train_clevr_n_extended,
)
from prin.y4q1_tools import (
    train_clevr_n_single_seed as train_clevr_n_single_seed,
)

__version__: str
__all__: list[str]

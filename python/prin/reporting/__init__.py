"""Reporting: benchmark JSON reports, figures, tables, profiler.

Near-verbatim ports of PRINet 3.0 ``utils/{benchmark_reporting,
figure_generation, table_generation, profiler}.py``. The JSON artefact schema
is unchanged so PRINet 3.0 artefacts remain valid. Figures are 300 DPI
matplotlib; tables are LaTeX fragments; the profiler wraps ``torch.profiler``
and labels Rust-backed call boundaries. Implemented during Phases 1 and 6.
"""

from __future__ import annotations

from ._artifacts import ReportingError
from .benchmark_reporting import (
    ReportInputError,
    ReportOutputError,
    generate_benchmark_report,
    generate_leaderboard,
    generate_scalr_metrics_report,
)
from .figure_generation import (
    ArtifactNotFoundError,
    ArtifactSchemaError,
    OutputPathError,
    PublicationGenerationError,
    configure_neurips_style,
    fig_ablation_results,
    fig_chimera_heatmap,
    fig_clevr_n_capacity,
    fig_flops_scaling,
    fig_gold_standard_chimera,
    fig_gradient_flow,
    fig_mot_identity_preservation,
    fig_noise_velocity,
    fig_oscillosim_scaling,
    fig_parameter_efficiency,
    fig_representation_geometry,
    fig_statistical_summary,
    fig_supercritical_regime,
    fig_training_curves,
    generate_all_figures,
    normalize_matplotlib_output,
)
from .profiler import (
    PRINetProfiler,
    ProfilerConfigurationError,
    ProfileReport,
    ProfilerStateError,
    profile_training_loop,
)
from .table_generation import (
    generate_all_tables,
    table_ablation_variants,
    table_binding_breakdown,
    table_chimera_gold_standard,
    table_efficiency_profile,
    table_occlusion_sweep,
    table_oscillosim_scaling,
    table_parameter_efficiency,
    table_representation_geometry,
    table_statistical_summary,
    table_stress_conditions,
    table_supercritical_regime,
)

__all__ = [
    "ArtifactNotFoundError",
    "ArtifactSchemaError",
    "OutputPathError",
    "PRINetProfiler",
    "ProfileReport",
    "ProfilerConfigurationError",
    "ProfilerStateError",
    "PublicationGenerationError",
    "ReportInputError",
    "ReportOutputError",
    "ReportingError",
    "configure_neurips_style",
    "fig_ablation_results",
    "fig_chimera_heatmap",
    "fig_clevr_n_capacity",
    "fig_flops_scaling",
    "fig_gold_standard_chimera",
    "fig_gradient_flow",
    "fig_mot_identity_preservation",
    "fig_noise_velocity",
    "fig_oscillosim_scaling",
    "fig_parameter_efficiency",
    "fig_representation_geometry",
    "fig_statistical_summary",
    "fig_supercritical_regime",
    "fig_training_curves",
    "generate_all_figures",
    "generate_all_tables",
    "generate_benchmark_report",
    "generate_leaderboard",
    "generate_scalr_metrics_report",
    "normalize_matplotlib_output",
    "profile_training_loop",
    "table_ablation_variants",
    "table_binding_breakdown",
    "table_chimera_gold_standard",
    "table_efficiency_profile",
    "table_occlusion_sweep",
    "table_oscillosim_scaling",
    "table_parameter_efficiency",
    "table_representation_geometry",
    "table_statistical_summary",
    "table_stress_conditions",
    "table_supercritical_regime",
]

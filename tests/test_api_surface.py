"""Acceptance tests for the WP-036 compatibility and frozen API surface."""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable

import prin
import pytest
import torch
from prin import (
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
from prin._deprecation import (
    FROZEN_PUBLIC_API,
    deprecated,
    deprecated_parameter,
    verify_api_surface,
)
from prin.dynamics import (
    BandNetwork,
    BandParams,
    CouplingMode,
    KuramotoOscillator,
    TemporalPropagator,
)
from prin.eval import recovery_speed

REEXPORTED_SYMBOLS = frozenset(
    {
        "BackendType",
        "CONTROL_DIM",
        "ControlSignals",
        "ExponentialIntegrator",
        "GatedPhaseActivation",
        "HopfOscillator",
        "HybridPRINetV2",
        "KuramotoOscillator",
        "MultiRateIntegrator",
        "OscillatorState",
        "OscillatoryAttention",
        "PhaseAmplitudeCoupling",
        "PhaseTracker",
        "PhaseTrackerFrozen",
        "PhaseTrackerStatic",
        "ResonanceLayer",
        "STATE_DIM",
        "SlotAttentionFrozen",
        "SlotAttentionModule",
        "SlotAttentionNoGRU",
        "StuartLandauOscillator",
        "SubconsciousController",
        "SubconsciousDaemon",
        "SubconsciousState",
        "TemporalMetrics",
        "TemporalSlotAttentionMOT",
        "TrainingResult",
        "backend_info",
        "bimodality_index",
        "binding_robustness_score",
        "build_phase_knn",
        "compute_full_temporal_metrics",
        "compute_p_value",
        "configure_neurips_style",
        "create_session",
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
        "temporal_smoothness",
        "track_duration_stats",
        "track_fragmentation_rate",
    }
)

KERNEL_STUBS: tuple[Callable[..., object], ...] = (
    triton_fused_mean_field_rk4_step,
    triton_sparse_knn_coupling,
    triton_pac_modulation,
    triton_hierarchical_order_param,
    triton_fused_discrete_step,
    fused_discrete_step_cuda,
)


def test_exact_already_resolving_surface_is_reexported() -> None:
    """All 71 governed pre-existing names resolve from the package root."""
    assert len(REEXPORTED_SYMBOLS) == 71
    assert REEXPORTED_SYMBOLS <= set(prin.__all__)
    for name in REEXPORTED_SYMBOLS:
        value = getattr(prin, name)
        assert value is not None
        if inspect.isclass(value) or inspect.isfunction(value):
            assert callable(value)


def test_frozen_surface_matches_prin_rc1_surface() -> None:
    """The frozen contract is derived from PRIN's own public surface."""
    assert isinstance(FROZEN_PUBLIC_API, frozenset)
    assert FROZEN_PUBLIC_API == frozenset(prin.__all__)
    assert verify_api_surface(prin.__all__) == (set(), set())
    missing = next(iter(FROZEN_PUBLIC_API))
    assert verify_api_surface([name for name in prin.__all__ if name != missing]) == (
        {missing},
        set(),
    )
    assert verify_api_surface([*prin.__all__, "future_symbol"]) == (
        set(),
        {"future_symbol"},
    )


def test_deprecated_preserves_metadata_and_warns() -> None:
    """The symbol decorator preserves metadata and emits migration guidance."""

    @deprecated("0.3", "Use replacement().", removal="1.0")
    def old(value: int) -> int:
        """Return the supplied value."""
        return value

    assert old.__name__ == "old"
    with pytest.warns(
        DeprecationWarning,
        match=r"old is deprecated since v0\.3.*Use replacement\(\).*1\.0",
    ):
        assert old(4) == 4


def test_deprecated_parameter_only_warns_when_supplied_by_keyword() -> None:
    """The parameter decorator warns only for the named keyword argument."""

    @deprecated_parameter("old", "0.3", "Use new instead.")
    def target(*, new: int = 0, **kwargs: int) -> int:
        """Return either the current or legacy keyword value."""
        return kwargs.get("old", new)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert target(new=2) == 2
    with pytest.warns(DeprecationWarning, match="Parameter 'old'.*Use new"):
        assert target(old=3) == 3


def test_pure_rename_aliases_resolve_and_construct() -> None:
    """Rename aliases are identity shims or BandNetwork factories.

    ``SCALROptimizer`` / ``RIPOptimizer`` / ``SynchronizedGradientDescent`` are
    no longer pure renames of the WP-027 ``Scalr`` / ``Rip`` / ``SyncGd``
    bridges: WP-036B S1 (0144E4) rebuilds the full PRINet 3.0
    ``nn.optimizers`` public API (metric histories, ``compute_sync_penalty``,
    per-frequency ``order_parameter`` dicts, EMA-adaptive ``r_min``) on top of
    those Rust bridges, so they are their own ``torch.optim.Optimizer``
    subclasses.
    """
    assert issubclass(SCALROptimizer, torch.optim.Optimizer)
    assert issubclass(RIPOptimizer, torch.optim.Optimizer)
    assert issubclass(SynchronizedGradientDescent, torch.optim.Optimizer)
    assert TemporalPhasePropagator is TemporalPropagator
    assert temporal_recovery_speed is recovery_speed

    model = KuramotoOscillator(2, 1.0, 0.1, 0.0, CouplingMode.mean_field())
    assert isinstance(model, OscillatorModel)

    theta = BandParams(1.0, 0.1)
    gamma = BandParams(0.5, 0.1)
    two_band = ThetaGammaNetwork(2, 3, theta, gamma, 0.2)
    assert isinstance(two_band, BandNetwork)
    assert two_band.band_sizes() == [2, 3]

    delta = BandParams(0.8, 0.1)
    three_band = DeltaThetaGammaNetwork(1, 2, 3, delta, theta, gamma, 0.1, 0.2)
    assert isinstance(three_band, BandNetwork)
    assert three_band.band_sizes() == [1, 2, 3]

    parameter = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    assert isinstance(SCALROptimizer([parameter]), torch.optim.Optimizer)
    assert isinstance(SynchronizedGradientDescent([parameter]), torch.optim.Optimizer)
    coupling = torch.zeros((2, 2), dtype=torch.float64, requires_grad=True)
    assert isinstance(RIPOptimizer([coupling]), torch.optim.Optimizer)


def test_unavailable_backend_predicates_are_false() -> None:
    """Unavailable legacy backend predicates fail closed."""
    assert triton_available() is False
    assert cuda_fused_kernel_available() is False


@pytest.mark.parametrize("stub", KERNEL_STUBS, ids=lambda stub: stub.__name__)
def test_unavailable_kernel_stubs_raise_typed_migration_error(
    stub: Callable[..., object],
) -> None:
    """Each legacy GPU kernel stub raises the shared typed exception."""
    with pytest.raises(BackendUnavailableError, match="PRIN migration"):
        stub(object(), unsupported=True)


def test_public_surface_has_no_duplicate_names() -> None:
    """The assembled top-level export list contains unique names."""
    assert len(prin.__all__) == len(set(prin.__all__))
    for name in prin.__all__:
        assert hasattr(prin, name), name


def test_stub_callables_accept_legacy_shaped_arguments() -> None:
    """Stub signatures remain permissive until the CPU equivalents land."""
    for stub in KERNEL_STUBS:
        signature = inspect.signature(stub)
        assert any(
            parameter.kind is inspect.Parameter.VAR_POSITIONAL
            for parameter in signature.parameters.values()
        )
        assert any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )

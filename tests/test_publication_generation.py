"""Acceptance tests for publication figure and table regeneration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import pytest
from prin.reporting import benchmark_reporting, profiler
from prin.reporting import figure_generation as figures
from prin.reporting import table_generation as tables
from prin.reporting._artifacts import ReportingError

EXPECTED_FIGURES = {
    "fig2_clevr_n_capacity",
    "fig3_chimera_metrics",
    "fig4_chimera_k_alpha",
    "fig5_mot_occlusion",
    "fig6_oscillosim_scaling",
    "fig7_ablation",
    "fig8_parameter_efficiency",
    "fig9_training_curves",
    "fig10_statistical_summary",
    "fig11_flops_scaling",
    "fig12_supercritical_regime",
    "fig13_representation_geometry",
    "fig14_gradient_flow",
    "fig15_noise_velocity",
}
EXPECTED_TABLES = {
    "tab_ablation",
    "tab_param_efficiency",
    "tab_chimera",
    "tab_statistical",
    "tab_occlusion",
    "tab_oscillosim",
    "tab_efficiency",
    "tab_binding_params",
    "tab_stress",
    "tab_supercritical",
    "tab_geometry",
}
REFERENCE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
)


def _stats(mean: float) -> dict[str, float]:
    return {"mean": mean, "ci_low": mean - 0.01, "ci_high": mean + 0.01}


def _artefacts() -> dict[str, dict[str, Any]]:
    variants = [
        {
            "variant": "full",
            "test_accuracy": 0.31,
            "n_params": 4991,
            "total_flops": 12000,
        },
        {
            "variant": "attention_only",
            "test_accuracy": 0.22,
            "n_params": 4000,
            "total_flops": 9000,
        },
    ]
    occlusion = [
        {"occlusion_rate": rate, "pt_stats": _stats(pt), "sa_stats": _stats(sa)}
        for rate, pt, sa in ((0.0, 0.99, 1.0), (0.5, 0.9, 0.98))
    ]
    profiles = []
    for n in (4, 8):
        profiles.extend(
            [
                {
                    "model": "PhaseTracker",
                    "n_objects": n,
                    "flops": n * 1000,
                    "latency_ms": {"mean": 0.2 * n},
                    "peak_memory_mb": 2.0,
                },
                {
                    "model": "SlotAttention",
                    "n_objects": n,
                    "flops": n * 50000,
                    "latency_ms": {"mean": 0.8 * n},
                    "peak_memory_mb": 8.0,
                },
            ]
        )
    convergence = {
        band: {
            "K_c_theory": {"mean": 1.0 + index},
            "K_c_empirical": {"mean": 20.0 + index},
            "convergence_rate_lambda": {"mean": 0.2 + index / 10},
        }
        for index, band in enumerate(("delta", "theta", "gamma"))
    }
    geometry_models = [
        {
            "model": name,
            "tsne_projection": [[0.0, 0.0], [1.0, 1.0], [0.2, 0.1]],
            "labels_sample": [0, 1, 0],
            "metrics": {"knn_purity": purity, "intrinsic_dim_90pct": dim},
        }
        for name, purity, dim in (
            ("PhaseTracker", 0.9, 2),
            ("SlotAttention", 0.5, 6),
        )
    ]
    gradient_models = [
        {
            "model": name,
            "layer_summary": {
                "encoder/weight": {"mean": 0.2, "std": 0.01},
                "decoder/weight": {"mean": 0.1, "std": 0.02},
            },
            "gradient_health": {"overall": "healthy", "vanishing_layers": []},
        }
        for name in ("PhaseTracker", "SlotAttention")
    ]
    return {
        "benchmark_y4q1_ablation_variants.json": {"variants": variants},
        "benchmark_y4q1_3_gold_standard_chimera.json": {
            "seeds": [
                {"seed": 1, "bc": 0.6, "si": 0.5, "chi": 0.4, "eta": 2},
                {"seed": 2, "bc": 0.7, "si": 0.6, "chi": 0.5, "eta": 3},
            ],
            "aggregate": {"bc_mean": 0.65, "si_mean": 0.55, "chi_mean": 0.45},
        },
        "benchmark_y4q1_3_k_alpha_sensitivity.json": {
            "grid": [
                {"K": k, "alpha": alpha, "bc_mean": value}
                for k, alpha, value in (
                    (10, 0.1, 0.4),
                    (20, 0.1, 0.6),
                    (10, 0.2, 0.5),
                    (20, 0.2, 0.7),
                )
            ]
        },
        "y4q1_9_fine_occlusion.json": {"sweep": occlusion},
        "y3q4_p4_oscillosim_scaling.json": {
            "results_by_mode": {
                mode: [
                    {
                        "n_oscillators": n,
                        "throughput_osc_step_per_s": scale / n,
                        "status": "OK",
                    }
                    for n in (100, 1000)
                ]
                for mode, scale in (
                    ("mean_field", 1e9),
                    ("sparse_knn", 2e9),
                    ("csr", 3e9),
                )
            }
        },
        "y4q1_8_parameter_efficiency_frontier.json": {
            "models": [
                {
                    "model": "PT-Small",
                    "total_params": 4991,
                    "mean_ip": 0.998,
                    "ip_per_param": 0.002,
                    "wall_time_ms": 1.2,
                },
                {
                    "model": "SA",
                    "total_params": 83904,
                    "mean_ip": 0.997,
                    "ip_per_param": 0.0001,
                    "wall_time_ms": 3.4,
                },
            ]
        },
        "y4q1_7_training_curves_pt.json": {
            "per_seed": [{"train_losses": [1.0, 0.5], "val_losses": [1.1, 0.6]}]
        },
        "y4q1_7_training_curves_sa.json": {
            "per_seed": [{"train_losses": [1.2, 0.7], "val_losses": [1.3, 0.8]}]
        },
        "y4q1_9_7seed_comparison.json": {
            "n_seeds": 2,
            "pt_stats": _stats(0.998),
            "sa_stats": _stats(0.997),
            "welch_t": {"p_value": 0.5, "cohens_d": 0.1},
            "conclusion": "equivalent",
        },
        "phase3_profiling.json": {"per_pair_profiles": profiles},
        "phase4_convergence_verification.json": {"aggregated": convergence},
        "phase3_representation_geometry.json": {
            "models": geometry_models,
            "comparison": {
                "pt_knn_purity": 0.9,
                "sa_knn_purity": 0.5,
                "pt_intrinsic_dim": 2,
                "sa_intrinsic_dim": 6,
                "pt_silhouette": 0.4,
                "sa_silhouette": 0.1,
            },
        },
        "phase3_gradient_flow.json": {"models": gradient_models},
        "phase2_noise_sweep.json": {
            "sweep": [
                {"sigma": sigma, "pt_stats": _stats(pt), "sa_stats": _stats(sa)}
                for sigma, pt, sa in ((0.0, 1.0, 1.0), (0.2, 0.9, 0.95))
            ],
            "exponential_fit": {
                "phase_tracker": {"IP_0": 1.0, "sigma_c": 1.0, "R_squared": 0.99}
            },
        },
        "phase2_velocity_stress.json": {
            "sweep": [
                {
                    "speed_multiplier": speed,
                    "pt_stats": _stats(pt),
                    "sa_stats": _stats(sa),
                }
                for speed, pt, sa in ((1.0, 0.99, 1.0), (2.0, 0.95, 0.98))
            ]
        },
        "y4q1_7_statistical_summary.json": {
            "phase_tracker": {"mean": 0.998, "ci_95": [0.997, 0.999]},
            "slot_attention": {"mean": 0.997, "ci_95": [0.996, 0.998]},
            "welch_t_test": {"mean_diff": 0.001, "p_value": 0.5, "cohens_d": 0.1},
            "outcome": "statistically_equivalent",
        },
        "phase4_parameter_scaling.json": {
            "parameter_breakdown": {
                "PhaseTracker": {"components": {"coupling": 10}, "total": 100},
                "SlotAttention": {"components": {"qkv": 300}, "total": 500},
                "ratio": 5.0,
            },
            "coupling_analysis": {
                "PT_dynamics_total": 10,
                "SA_attention_params": 300,
            },
        },
        "y4q1_7_stress_test_summary.json": {
            "conditions": [
                {"condition": "noise", "pt_mean": 0.9, "sa_mean": 0.95},
                {"condition": "velocity", "pt_ip": 0.92, "sa_ip": 0.91},
            ]
        },
    }


@pytest.fixture(autouse=True)
def allow_test_output_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(figures, "ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))
    monkeypatch.setattr(tables, "ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))


@pytest.fixture
def stored_results(tmp_path: Path) -> Path:
    results = tmp_path / "results"
    results.mkdir()
    for name, payload in _artefacts().items():
        (results / name).write_text(json.dumps(payload), encoding="utf-8")
    return results


def test_stored_3_0_artefacts_regenerate_all_outputs(
    tmp_path: Path,
) -> None:
    results = REFERENCE_ROOT / "benchmarks" / "results"
    generated_figures = figures.generate_all_figures(results, tmp_path / "figures-3-0")
    generated_tables = tables.generate_all_tables(results, tmp_path / "tables-3-0")

    assert set(generated_figures) == EXPECTED_FIGURES
    assert sum(len(paths) for paths in generated_figures.values()) == 28
    assert all(
        figures.normalize_matplotlib_output(path)
        for paths in generated_figures.values()
        for path in paths
    )
    assert set(generated_tables) == EXPECTED_TABLES
    for name, path in generated_tables.items():
        expected = REFERENCE_ROOT / "paper" / "tables" / f"{name}.tex"
        assert path.read_bytes() == expected.read_bytes()


def test_all_fourteen_figures_and_exact_master_keys(
    stored_results: Path, tmp_path: Path
) -> None:
    assert matplotlib.get_backend().lower() == "agg"
    assert set(figures.FIGURE_GENERATORS) == EXPECTED_FIGURES
    assert len(figures.FIGURE_GENERATORS) == 14
    assert not any(name.startswith("fig1_") for name in figures.FIGURE_GENERATORS)
    generated = figures.generate_all_figures(stored_results, tmp_path / "figures")
    assert set(generated) == EXPECTED_FIGURES
    assert sum(len(paths) for paths in generated.values()) == 28
    for paths in generated.values():
        assert {path.suffix for path in paths} == {".pdf", ".png"}
        assert all(path.is_file() and path.stat().st_size > 0 for path in paths)


def test_all_eleven_tables_exact_keys_and_latex_bytes(
    stored_results: Path, tmp_path: Path
) -> None:
    assert set(tables.TABLE_GENERATORS) == EXPECTED_TABLES
    assert len(tables.TABLE_GENERATORS) == 11
    first = tables.generate_all_tables(stored_results, tmp_path / "tables-a")
    second = tables.generate_all_tables(stored_results, tmp_path / "tables-b")
    assert set(first) == EXPECTED_TABLES
    assert set(second) == EXPECTED_TABLES
    for name in EXPECTED_TABLES:
        assert first[name].read_bytes() == second[name].read_bytes()
        text = first[name].read_text(encoding="utf-8")
        assert text.startswith(r"\begin{table}[t]")
        assert text.endswith(r"\end{table}")
        assert "\r\n" not in text


def test_repeat_figure_generation_has_deterministic_normalized_bytes(
    stored_results: Path, tmp_path: Path
) -> None:
    first = figures.fig_clevr_n_capacity(stored_results, tmp_path / "repeat-a")
    second = figures.fig_clevr_n_capacity(stored_results, tmp_path / "repeat-b")
    for left, right in zip(first, second, strict=True):
        assert left.suffix == right.suffix
        assert figures.normalize_matplotlib_output(
            left
        ) == figures.normalize_matplotlib_output(right)


@pytest.mark.parametrize(
    "generator,filename",
    [
        (figures.fig_clevr_n_capacity, "benchmark_y4q1_ablation_variants.json"),
        (tables.table_ablation_variants, "benchmark_y4q1_ablation_variants.json"),
    ],
)
def test_missing_required_mapping_key_is_precise_typed_schema_error(
    generator: Any, filename: str, tmp_path: Path
) -> None:
    results = tmp_path / "invalid"
    results.mkdir()
    (results / filename).write_text("{}", encoding="utf-8")
    with pytest.raises(figures.ArtifactSchemaError, match=r"\$\.variants") as error:
        generator(results, tmp_path / "output")
    assert error.value.json_path == "$.variants"
    assert error.value.artefact.name == filename


def test_non_mapping_and_invalid_json_are_typed_schema_errors(tmp_path: Path) -> None:
    results = tmp_path / "invalid"
    results.mkdir()
    path = results / "benchmark_y4q1_ablation_variants.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(figures.ArtifactSchemaError, match="expected a JSON object"):
        figures.fig_clevr_n_capacity(results, tmp_path / "output-a")
    path.write_text("{", encoding="utf-8")
    with pytest.raises(figures.ArtifactSchemaError, match="invalid JSON"):
        tables.table_ablation_variants(results, tmp_path / "output-b")


def test_master_generators_degrade_on_missing_artefact(tmp_path: Path) -> None:
    """The batch generators degrade rather than abort on an absent artefact.

    PRINet 3.0's ``generate_all_figures`` / ``generate_all_tables`` catch the
    missing-artefact failure classes so one unavailable benchmark JSON does not
    sink the whole batch; the ported y4q2 acceptance suite (``TestEdgeCases``,
    ``TestGenerateAllFigures``) asserts that contract. The *individual*
    generators still fail loudly with typed errors (covered by the schema-error
    tests above) — only the master batch functions degrade (WP036C-F1).
    """
    results = tmp_path / "empty"
    results.mkdir()

    figure_result = figures.generate_all_figures(results, tmp_path / "figures")
    assert isinstance(figure_result, dict)
    assert all(paths == [] for paths in figure_result.values())

    table_result = tables.generate_all_tables(results, tmp_path / "tables")
    assert table_result == {}


def test_output_paths_are_confined(stored_results: Path, tmp_path: Path) -> None:
    escaped = figures._REPOSITORY_ROOT / "unconfined-publication-output"
    with pytest.raises(figures.OutputPathError, match="outside allowed roots"):
        figures.fig_clevr_n_capacity(stored_results, escaped)
    with pytest.raises(tables.OutputPathError, match="outside allowed roots"):
        tables.table_ablation_variants(stored_results, escaped)
    assert not escaped.exists()


def test_optional_phase_one_tables_and_throughput_formats(
    stored_results: Path, tmp_path: Path
) -> None:
    optional = {
        "phase1_chimera_seeds.json": {
            "bimodality_coefficient": {
                "n_sequences": 2,
                "raw_values": [0.6, 0.7],
                "mean": 0.65,
                "std": 0.05,
                "ci_95_low": 0.55,
                "ci_95_high": 0.75,
            }
        },
        "phase1_bf_tost_resolution.json": {
            "tost_p": 0.01,
            "bayesian_prob_equivalent": 0.996,
        },
        "phase1_cliffs_delta.json": {"cliffs_delta": 0.02},
        "phase1_bayes_factor.json": {"bf10": 0.1},
        "phase1_holm_bonferroni.json": {"n_significant_after_correction": 1},
    }
    for name, payload in optional.items():
        (stored_results / name).write_text(json.dumps(payload), encoding="utf-8")
    chimera = tables.table_chimera_gold_standard(
        stored_results, tmp_path / "optional-chimera"
    ).read_text(encoding="utf-8")
    statistical = tables.table_statistical_summary(
        stored_results, tmp_path / "optional-statistical"
    ).read_text(encoding="utf-8")
    assert "Phase~1 enhanced, 2 sequences" in chimera
    assert "TOST" in statistical
    assert "Cliff's" in statistical
    assert r"\mathrm{BF}_{10}" in statistical
    assert "Holm--Bonferroni" in statistical
    assert tables._throughput(2e9) == "2.00B"
    assert tables._throughput(2e6) == "2.0M"
    assert tables._throughput(2e3) == "2K"
    assert tables._throughput(2.0) == "2"


def test_normalizer_rejects_unsupported_and_malformed_formats(tmp_path: Path) -> None:
    text = tmp_path / "figure.svg"
    text.write_bytes(b"svg")
    with pytest.raises(figures.NormalizationError, match="unsupported") as unsupported:
        figures.normalize_matplotlib_output(text)
    assert isinstance(unsupported.value, figures.PublicationGenerationError)
    png = tmp_path / "figure.png"
    png.write_bytes(b"not png")
    with pytest.raises(figures.NormalizationError, match="malformed") as malformed:
        figures.normalize_matplotlib_output(png)
    assert isinstance(malformed.value, ValueError)


def test_json_loading_is_shared_not_privately_cross_imported() -> None:
    """WP034-F4: figure/table generation share one loader, not a private import."""
    assert figures._load_json is tables._load_json  # type: ignore[attr-defined]


def test_all_reporting_errors_share_one_root() -> None:
    """WP034-F3: every reporting module's typed errors share one common root."""
    error_types = (
        figures.ArtifactNotFoundError,
        figures.ArtifactSchemaError,
        figures.NormalizationError,
        figures.OutputPathError,
        figures.PublicationGenerationError,
        tables.ArtifactNotFoundError,
        tables.ArtifactSchemaError,
        tables.OutputPathError,
        tables.PublicationGenerationError,
        benchmark_reporting.ReportInputError,
        benchmark_reporting.ReportOutputError,
        profiler.ProfilerConfigurationError,
        profiler.ProfilerStateError,
    )
    for error_type in error_types:
        assert issubclass(error_type, ReportingError)

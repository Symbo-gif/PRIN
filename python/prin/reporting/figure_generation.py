"""Deterministic publication figures ported from PRINet 3.0 artefacts.

The module preserves the fourteen historical generators for figures 2 through
15. Figure 1 never existed in the reference implementation. Stored benchmark
values are only rendered; no scientific quantity is recomputed.
"""

from __future__ import annotations

import json
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from prin.reporting._artifacts import (
    ArtifactNotFoundError,
    ArtifactSchemaError,
    OutputPathError,
    PublicationGenerationError,
    ReportingError,
    _load_json,
    allowed_output_roots,
)

COLORS = {
    "pt": "#4477AA",
    "sa": "#EE6677",
    "pt_large": "#228833",
    "chimera": "#CCBB44",
    "coherent": "#66CCEE",
    "full": "#4477AA",
    "attention_only": "#EE6677",
    "oscillator_only": "#228833",
    "shared_phase": "#CCBB44",
    "mean_field": "#4477AA",
    "sparse_knn": "#EE6677",
    "csr": "#228833",
    "full_coupling": "#CCBB44",
}
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_DIR = _REPOSITORY_ROOT / "benchmarks" / "results"
DEFAULT_OUTPUT_DIR = (
    _REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results" / "figures"
)
ALLOWED_OUTPUT_ROOTS = (
    (_REPOSITORY_ROOT / "benchmarks" / "results").resolve(),
    (_REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)
_FIXED_DATE = datetime(2000, 1, 1, tzinfo=UTC)


class NormalizationError(PublicationGenerationError, ValueError):
    """Report matplotlib output that cannot be normalized for comparison.

    Examples:
        >>> error = NormalizationError("unsupported matplotlib format: .svg")
        >>> isinstance(error, PublicationGenerationError)
        True
    """


def _dirs(results_dir: Path | None, output_dir: Path | None) -> tuple[Path, Path]:
    results = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    output = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    resolved = output.resolve()
    roots_checked = allowed_output_roots(ALLOWED_OUTPUT_ROOTS)
    if not any(resolved == root or root in resolved.parents for root in roots_checked):
        roots = ", ".join(str(root) for root in roots_checked)
        raise OutputPathError(
            f"output directory {resolved} is outside allowed roots: {roots}"
        )
    return results, resolved


def configure_neurips_style() -> None:
    """Apply the historical NeurIPS camera-ready matplotlib style.

    Examples:
        >>> configure_neurips_style()
        >>> plt.rcParams["figure.dpi"]
        300.0
    """
    plt.rcParams.update(
        {
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "font.size": 9,
            "font.family": "serif",
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "legend.framealpha": 0.8,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linewidth": 0.5,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.5,
            "lines.markersize": 5,
            "svg.hashsalt": "prin-publication",
        }
    )


def _save_fig(
    fig: Figure, name: str, output_dir: Path, formats: tuple[str, ...] = ("pdf", "png")
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    try:
        for fmt in formats:
            path = output_dir / f"{name}.{fmt}"
            metadata: dict[str, Any]
            if fmt == "pdf":
                metadata = {
                    "Creator": "PRIN",
                    "Producer": "Matplotlib",
                    "CreationDate": _FIXED_DATE,
                    "ModDate": _FIXED_DATE,
                }
            else:
                metadata = {"Software": "PRIN"}
            fig.savefig(path, format=fmt, metadata=metadata)
            paths.append(path)
    finally:
        plt.close(fig)
    return paths


def normalize_matplotlib_output(path: Path) -> bytes:
    """Normalize generated matplotlib bytes for deterministic comparison.

    PNG comparison discards ancillary chunks and retains only image-defining
    chunks. PDF comparison masks backend object IDs and metadata dates; generated
    files already use fixed metadata, so this also supports older matplotlib
    patch releases whose PDF object identifiers differ.

    Args:
        path: Generated ``.png`` or ``.pdf`` file.

    Returns:
        Normalized bytes suitable for hashing or byte comparison.

    Raises:
        NormalizationError: If the path suffix is unsupported or the PNG is
            malformed.

    Examples:
        >>> with tempfile.TemporaryDirectory() as directory:
        ...     figure = Path(directory) / "figure.pdf"
        ...     _ = figure.write_bytes(b"%PDF-1.4")
        ...     normalized = normalize_matplotlib_output(figure)
        >>> normalized
        b'%PDF-1.4'
    """
    payload = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        payload = re.sub(
            rb"/CreationDate \([^)]*\)", b"/CreationDate (normalized)", payload
        )
        payload = re.sub(rb"/ModDate \([^)]*\)", b"/ModDate (normalized)", payload)
        payload = re.sub(
            rb"/ID \[<[^>]+> <[^>]+>\]", b"/ID [<normalized> <normalized>]", payload
        )
        return payload
    if suffix != ".png":
        raise NormalizationError(f"unsupported matplotlib format: {suffix}")
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise NormalizationError(f"malformed PNG file: {path}")
    result = bytearray(payload[:8])
    offset = 8
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise NormalizationError(f"malformed PNG file: {path}")
        length = int.from_bytes(payload[offset : offset + 4], "big")
        end = offset + 12 + length
        chunk = payload[offset + 4 : offset + 8]
        if end > len(payload):
            raise NormalizationError(f"malformed PNG file: {path}")
        if chunk in {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"}:
            result.extend(payload[offset:end])
        offset = end
    return bytes(result)


def fig_clevr_n_capacity(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the CLEVR-N capacity bar chart (Fig. 2).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_clevr_n_capacity(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    variants = _load_json(results / "benchmark_y4q1_ablation_variants.json")["variants"]
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    names = [v["variant"] for v in variants]
    values = [v["test_accuracy"] * 100 for v in variants]
    bars = ax.bar(
        names,
        values,
        color=[COLORS.get(n, "#999999") for n in names],
        edgecolor="black",
        linewidth=0.5,
        width=0.6,
    )
    ax.set(
        ylabel="Test Accuracy (%)",
        title="CLEVR-N Ablation: Variant Accuracy",
        ylim=(0, 40),
    )
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha="right")
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=7,
        )
    fig.tight_layout()
    return _save_fig(fig, "fig2_clevr_n_capacity", output)


def fig_gold_standard_chimera(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the gold-standard chimera metric chart (Fig. 3).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_gold_standard_chimera(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    seeds = _load_json(results / "benchmark_y4q1_3_gold_standard_chimera.json")["seeds"]
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    metrics = ["bc", "si", "chi"]
    x = np.arange(3)
    width = 0.25
    for index, seed in enumerate(seeds):
        ax.bar(
            x + index * width,
            [seed[m] for m in metrics],
            width,
            label=f"Seed {seed['seed']}",
            edgecolor="black",
            linewidth=0.3,
            alpha=0.8,
        )
    ax.axhline(0.555, color="red", linestyle="--", linewidth=0.8, label="BC threshold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(
        ["Bimodality (BC)", "Sync Index (SI)", "Chimera Index"], fontsize=7
    )
    ax.set(ylabel="Metric Value", title="Gold-Standard Chimera (N=256, K=100)")
    ax.legend(fontsize=6, loc="upper right")
    fig.tight_layout()
    return _save_fig(fig, "fig3_chimera_metrics", output)


def fig_chimera_heatmap(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the chimera K-alpha sensitivity heatmap (Fig. 4).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_chimera_heatmap(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    grid = _load_json(results / "benchmark_y4q1_3_k_alpha_sensitivity.json")["grid"]
    ks = sorted({g["K"] for g in grid})
    alphas = sorted({g["alpha"] for g in grid})
    matrix = np.full((len(alphas), len(ks)), np.nan)
    for item in grid:
        matrix[alphas.index(item["alpha"]), ks.index(item["K"])] = item["bc_mean"]
    fig, ax = plt.subplots(figsize=(3.3, 2.8))
    image = ax.imshow(
        matrix,
        aspect="auto",
        origin="lower",
        cmap="YlOrRd",
        vmin=0.3,
        vmax=0.75,
        extent=(min(ks) - 5, max(ks) + 5, min(alphas) - 0.02, max(alphas) + 0.02),
    )
    fig.colorbar(image, ax=ax, label="Bimodality Coefficient (BC)")
    ax.set(
        xlabel="Coupling Strength K",
        ylabel="Phase Lag alpha",
        title="Chimera State Sensitivity (N=256)",
    )
    ax.contour(
        ks,
        alphas,
        matrix,
        levels=[0.555],
        colors=["white"],
        linewidths=1.5,
        linestyles="--",
    )
    fig.tight_layout()
    return _save_fig(fig, "fig4_chimera_k_alpha_heatmap", output)


def fig_mot_identity_preservation(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the MOT occlusion comparison (Fig. 5).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_mot_identity_preservation(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    sweep = _load_json(results / "y4q1_9_fine_occlusion.json")["sweep"]
    rates = [s["occlusion_rate"] * 100 for s in sweep]
    means = [s["pt_stats"]["mean"] for s in sweep]
    lo = [m - s["pt_stats"]["ci_low"] for m, s in zip(means, sweep, strict=True)]
    hi = [s["pt_stats"]["ci_high"] - m for m, s in zip(means, sweep, strict=True)]
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    ax.errorbar(
        rates,
        means,
        yerr=[lo, hi],
        color=COLORS["pt"],
        marker="o",
        label="PhaseTracker",
        capsize=3,
    )
    ax.plot(
        rates,
        [s["sa_stats"]["mean"] for s in sweep],
        color=COLORS["sa"],
        marker="s",
        label="Slot Attention",
    )
    ax.set(
        xlabel="Occlusion Rate (%)",
        ylabel="Identity Preservation (IP)",
        title="MOT: Occlusion Robustness",
        ylim=(0, 1.05),
    )
    ax.legend(loc="lower left")
    fig.tight_layout()
    return _save_fig(fig, "fig5_mot_occlusion_comparison", output)


def fig_oscillosim_scaling(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the OscilloSim throughput scaling chart (Fig. 6).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_oscillosim_scaling(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    modes = _load_json(results / "y3q4_p4_oscillosim_scaling.json")["results_by_mode"]
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    styles = {
        "mean_field": ("o", COLORS["mean_field"], "Mean-field"),
        "sparse_knn": ("s", COLORS["sparse_knn"], "Sparse k-NN"),
        "csr": ("^", COLORS["csr"], "CSR"),
    }
    for mode, items in modes.items():
        if mode in styles:
            marker, color, label = styles[mode]
            ok = [item for item in items if item["status"] == "OK"]
            if ok:
                ax.loglog(
                    [i["n_oscillators"] for i in ok],
                    [i["throughput_osc_step_per_s"] for i in ok],
                    marker=marker,
                    color=color,
                    label=label,
                )
    ax.set(
        xlabel="Number of Oscillators N",
        ylabel="Throughput (osc*step/s)",
        title="OscilloSim GPU Scaling",
    )
    ax.legend(loc="upper left", fontsize=7)
    fig.tight_layout()
    return _save_fig(fig, "fig6_oscillosim_scaling", output)


def fig_ablation_results(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the accuracy and FLOPs ablation chart (Fig. 7).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_ablation_results(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    variants = _load_json(results / "benchmark_y4q1_ablation_variants.json")["variants"]
    names = [v["variant"] for v in variants]
    colors = [COLORS.get(n, "#999999") for n in names]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.8, 2.5))
    bars = a.bar(
        names,
        [v["test_accuracy"] * 100 for v in variants],
        color=colors,
        edgecolor="black",
        linewidth=0.5,
    )
    a.set(ylabel="Test Accuracy (%)", title="(a) Accuracy by Variant")
    b.bar(
        names,
        [v["total_flops"] / 1000 for v in variants],
        color=colors,
        edgecolor="black",
        linewidth=0.5,
    )
    b.set(ylabel="FLOPs (K)", title="(b) Compute Cost by Variant")
    for axis in (a, b):
        axis.set_xticks(range(len(names)))
        axis.set_xticklabels(names, rotation=15, ha="right", fontsize=7)
    for bar, v in zip(bars, variants, strict=True):
        a.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{v['test_accuracy'] * 100:.1f}",
            ha="center",
            fontsize=6,
        )
    fig.tight_layout()
    return _save_fig(fig, "fig7_ablation_results", output)


def fig_parameter_efficiency(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the parameter-efficiency frontier (Fig. 8).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_parameter_efficiency(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    models = _load_json(results / "y4q1_8_parameter_efficiency_frontier.json")["models"]
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    colors = {
        "PT-Small": COLORS["pt"],
        "PT-Large": COLORS["pt_large"],
        "SA": COLORS["sa"],
    }
    for model in models:
        color = colors.get(model["model"], "#999999")
        ax.scatter(
            model["total_params"],
            model["mean_ip"],
            color=color,
            s=80,
            edgecolors="black",
            linewidth=0.5,
            label=f"{model['model']} ({model['total_params']:,} params)",
        )
        ax.annotate(
            f"IP/param: {model['ip_per_param']:.4f}",
            (model["total_params"], model["mean_ip"]),
            textcoords="offset points",
            xytext=(5, -12),
            fontsize=6,
            color=color,
        )
    ax.set_xscale("log")
    ax.set(
        xlabel="Total Parameters",
        ylabel="Mean Identity Preservation",
        title="Parameter Efficiency Frontier",
        ylim=(0.99, 1.005),
    )
    ax.legend(loc="lower right", fontsize=6)
    fig.tight_layout()
    return _save_fig(fig, "fig8_parameter_efficiency", output)


def fig_training_curves(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate training convergence and final IP panels (Fig. 9).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_training_curves(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    pt = _load_json(results / "y4q1_7_training_curves_pt.json")["per_seed"][0]
    sa = _load_json(results / "y4q1_7_training_curves_sa.json")["per_seed"][0]
    comp = _load_json(results / "y4q1_9_7seed_comparison.json")
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.8, 2.5))
    for seed, color, prefix in ((pt, COLORS["pt"], ""), (sa, COLORS["sa"], "SA ")):
        epochs = range(1, len(seed["train_losses"]) + 1)
        a.plot(epochs, seed["train_losses"], color=color, label=f"{prefix}Train")
        a.plot(
            epochs,
            seed["val_losses"],
            color=color,
            linestyle="--",
            label=f"{prefix}Val",
        )
    a.set(xlabel="Epoch", ylabel="Loss", title="(a) Training Convergence")
    a.legend(fontsize=6)
    ips = [comp["pt_stats"]["mean"], comp["sa_stats"]["mean"]]
    bars = b.bar(
        ["PT", "SA"],
        ips,
        color=[COLORS["pt"], COLORS["sa"]],
        edgecolor="black",
        linewidth=0.5,
    )
    b.set(
        ylabel="Mean Identity Preservation",
        title=f"(b) Final IP ({comp['n_seeds']}-seed mean)",
        ylim=(0.99, 1.005),
    )
    for bar, ip in zip(bars, ips, strict=True):
        b.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.0003,
            f"{ip:.4f}",
            ha="center",
            fontsize=7,
        )
    fig.tight_layout()
    return _save_fig(fig, "fig9_training_curves", output)


def fig_statistical_summary(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the PT-versus-SA statistical summary (Fig. 10).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_statistical_summary(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    data = _load_json(results / "y4q1_9_7seed_comparison.json")
    pt = data["pt_stats"]
    sa = data["sa_stats"]
    diff = pt["mean"] - sa["mean"]
    values = [pt["mean"], sa["mean"], diff]
    lows = [pt["ci_low"], sa["ci_low"], diff - 0.005]
    highs = [pt["ci_high"], sa["ci_high"], diff + 0.005]
    fig, ax = plt.subplots(figsize=(3.3, 3))
    y = np.arange(3)
    ax.barh(
        y,
        values,
        xerr=[
            [value - low for value, low in zip(values, lows, strict=True)],
            [high - value for value, high in zip(values, highs, strict=True)],
        ],
        color=[COLORS["pt"], COLORS["sa"], "#999999"],
        edgecolor="black",
        linewidth=0.5,
        capsize=3,
    )
    ax.set_yticks(y)
    ax.set_yticklabels(["PT Mean IP", "SA Mean IP", "Difference"])
    p_value = data["welch_t"]["p_value"]
    effect_size = data["welch_t"]["cohens_d"]
    ax.set(
        xlabel="Value",
        title=f"Statistical Summary (p={p_value:.3f}, d={effect_size:.2f})",
    )
    ax.annotate(
        f"Outcome: {data.get('conclusion', 'unknown')}",
        xy=(0.5, 0.02),
        xycoords="axes fraction",
        ha="center",
        fontsize=7,
        style="italic",
    )
    fig.tight_layout()
    return _save_fig(fig, "fig10_statistical_summary", output)


def fig_flops_scaling(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate PhaseTracker and SlotAttention FLOPs scaling (Fig. 11).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_flops_scaling(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    profiles = _load_json(results / "phase3_profiling.json")["per_pair_profiles"]
    pt = [p for p in profiles if p["model"] == "PhaseTracker"]
    sa = [p for p in profiles if p["model"] == "SlotAttention"]
    x = np.arange(len(pt))
    pf = np.array([p["flops"] for p in pt]) / 1e3
    sf = np.array([p["flops"] for p in sa]) / 1e3
    fig, ax = plt.subplots(figsize=(3.3, 2.4))
    w = 0.35
    ax.bar(x - w / 2, pf, w, label="PhaseTracker", color=COLORS["pt"])
    ax.bar(x + w / 2, sf, w, label="SlotAttention", color=COLORS["sa"])
    ax.set_xticks(x)
    ax.set_xticklabels([str(p["n_objects"]) for p in pt])
    ax.set_yscale("log")
    ax.set(
        xlabel="Number of Objects (N)",
        ylabel=r"FLOPs ($\times 10^3$)",
        title="Computational Cost Scaling",
    )
    ax.legend()
    for i, (p, s) in enumerate(zip(pf, sf, strict=True)):
        ax.annotate(
            rf"{s / p:.0f}$\times$",
            xy=(i + w / 2, s),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=7,
        )
    fig.tight_layout()
    return _save_fig(fig, "fig11_flops_scaling", output)


def fig_supercritical_regime(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate the supercritical-coupling regime chart (Fig. 12).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_supercritical_regime(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    agg = _load_json(results / "phase4_convergence_verification.json")["aggregated"]
    bands = ["delta", "theta", "gamma"]
    ratios = [
        agg[b]["K_c_empirical"]["mean"] / agg[b]["K_c_theory"]["mean"] for b in bands
    ]
    rates = [agg[b]["convergence_rate_lambda"]["mean"] for b in bands]
    fig, a = plt.subplots(figsize=(3.3, 2.4))
    x = np.arange(3)
    a.bar(
        x,
        ratios,
        0.6,
        color=[COLORS["pt"], COLORS["coherent"], COLORS["chimera"]],
        edgecolor="black",
    )
    a.set_xticks(x)
    a.set_xticklabels(
        [r"$\delta$ (1--4 Hz)", r"$\theta$ (4--8 Hz)", r"$\gamma$ (25--100 Hz)"],
        fontsize=7,
    )
    a.axhline(1, color="gray", linestyle="--")
    a.set(
        ylabel=r"$K_{\mathrm{eff}} / K_c$ Ratio", title="Supercritical Coupling Regime"
    )
    b = a.twinx()
    b.plot(x, rates, "D-", color="#AA3377")
    b.set_ylabel(r"Convergence Rate $\lambda$", color="#AA3377")
    for i, value in enumerate(ratios):
        a.text(i, value + 2, rf"{value:.0f}$\times$", ha="center", fontsize=7)
    fig.tight_layout()
    return _save_fig(fig, "fig12_supercritical_regime", output)


def fig_representation_geometry(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate representation-geometry scatter panels (Fig. 13).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_representation_geometry(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    data = _load_json(results / "phase3_representation_geometry.json")
    models = {m["model"]: m for m in data["models"]}
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8))
    for ax, name in zip(axes, ("PhaseTracker", "SlotAttention"), strict=True):
        model = models[name]
        points = np.array(model["tsne_projection"])
        labels = np.array(model["labels_sample"])
        for index, label in enumerate(sorted(set(labels.tolist()))):
            mask = labels == label
            ax.scatter(
                points[mask, 0],
                points[mask, 1],
                s=8,
                alpha=0.6,
                color=plt.get_cmap("tab10")(index % 10),
            )
        purity = model["metrics"]["knn_purity"]
        dimension = model["metrics"]["intrinsic_dim_90pct"]
        ax.set(
            title=f"{name}\nk-NN={purity:.3f}, dim={dimension}",
            xlabel="t-SNE 1",
            ylabel="t-SNE 2",
        )
        ax.tick_params(labelbottom=False, labelleft=False)
    fig.tight_layout()
    return _save_fig(fig, "fig13_representation_geometry", output)


def fig_gradient_flow(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate per-layer gradient-flow panels (Fig. 14).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_gradient_flow(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    models = {
        m["model"]: m
        for m in _load_json(results / "phase3_gradient_flow.json")["models"]
    }
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8), sharey=True)
    for ax, name, color in zip(
        axes, ("PhaseTracker", "SlotAttention"), ("pt", "sa"), strict=True
    ):
        model = models[name]
        summary = model["layer_summary"]
        layers = list(summary)
        y = np.arange(len(layers))
        ax.barh(
            y,
            [summary[layer]["mean"] for layer in layers],
            xerr=[summary[layer]["std"] for layer in layers],
            color=COLORS[color],
            edgecolor="black",
            linewidth=0.5,
            capsize=2,
        )
        ax.set_yticks(y)
        ax.set_yticklabels([layer.split("/")[-1] for layer in layers], fontsize=6)
        health = model["gradient_health"]["overall"]
        vanishing = len(model["gradient_health"]["vanishing_layers"])
        ax.set(
            xlabel="Mean Gradient Norm",
            title=f"{name} ({health}, {vanishing} vanishing)",
        )
    fig.tight_layout()
    return _save_fig(fig, "fig14_gradient_flow", output)


def fig_noise_velocity(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> list[Path]:
    """Generate noise and velocity stress panels (Fig. 15).

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Paths to the generated PDF and PNG files, in that order.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> paths = fig_noise_velocity(output_dir=target)  # doctest: +SKIP
        >>> [path.suffix for path in paths]  # doctest: +SKIP
        ['.pdf', '.png']
    """
    configure_neurips_style()
    results, output = _dirs(results_dir, output_dir)
    noise = _load_json(results / "phase2_noise_sweep.json")
    velocity = _load_json(results / "phase2_velocity_stress.json")
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.8, 2.8))
    ns = noise["sweep"]
    x = [s["sigma"] for s in ns]
    a.fill_between(
        x,
        [s["pt_stats"]["ci_low"] for s in ns],
        [s["pt_stats"]["ci_high"] for s in ns],
        alpha=0.15,
        color=COLORS["pt"],
    )
    a.plot(
        x,
        [s["pt_stats"]["mean"] for s in ns],
        "o-",
        color=COLORS["pt"],
        label="PhaseTracker",
    )
    a.plot(
        x,
        [s["sa_stats"]["mean"] for s in ns],
        "s-",
        color=COLORS["sa"],
        label="SlotAttention",
    )
    fit = noise["exponential_fit"]["phase_tracker"]
    fine = np.linspace(0, max(x), 100)
    a.plot(
        fine,
        fit["IP_0"] * np.exp(-fine / fit["sigma_c"]),
        "--",
        color=COLORS["pt"],
        label=f"Fit (R²={fit['R_squared']:.3f})",
    )
    a.set(
        xlabel=r"Noise $\sigma$",
        ylabel="Identity Preservation",
        title="Noise Degradation",
        ylim=(0.7, 1.02),
    )
    a.legend(fontsize=6)
    vs = velocity["sweep"]
    x = [s["speed_multiplier"] for s in vs]
    b.fill_between(
        x,
        [s["pt_stats"]["ci_low"] for s in vs],
        [s["pt_stats"]["ci_high"] for s in vs],
        alpha=0.15,
        color=COLORS["pt"],
    )
    b.plot(
        x,
        [s["pt_stats"]["mean"] for s in vs],
        "o-",
        color=COLORS["pt"],
        label="PhaseTracker",
    )
    b.plot(
        x,
        [s["sa_stats"]["mean"] for s in vs],
        "s-",
        color=COLORS["sa"],
        label="SlotAttention",
    )
    b.set(
        xlabel=r"Speed Multiplier ($\times$)",
        ylabel="Identity Preservation",
        title="Velocity Stress",
        ylim=(0.85, 1.02),
    )
    b.legend(fontsize=6)
    fig.tight_layout()
    return _save_fig(fig, "fig15_noise_velocity", output)


FIGURE_GENERATORS = {
    "fig2_clevr_n_capacity": fig_clevr_n_capacity,
    "fig3_chimera_metrics": fig_gold_standard_chimera,
    "fig4_chimera_k_alpha": fig_chimera_heatmap,
    "fig5_mot_occlusion": fig_mot_identity_preservation,
    "fig6_oscillosim_scaling": fig_oscillosim_scaling,
    "fig7_ablation": fig_ablation_results,
    "fig8_parameter_efficiency": fig_parameter_efficiency,
    "fig9_training_curves": fig_training_curves,
    "fig10_statistical_summary": fig_statistical_summary,
    "fig11_flops_scaling": fig_flops_scaling,
    "fig12_supercritical_regime": fig_supercritical_regime,
    "fig13_representation_geometry": fig_representation_geometry,
    "fig14_gradient_flow": fig_gradient_flow,
    "fig15_noise_velocity": fig_noise_velocity,
}


def generate_all_figures(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> dict[str, list[Path]]:
    """Generate all fourteen historical publication figures.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Generated PDF and PNG paths keyed by historical figure name.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-figures"
        >>> figures = generate_all_figures(output_dir=target)  # doctest: +SKIP
        >>> len(figures)  # doctest: +SKIP
        14
    """
    results, output = _dirs(results_dir, output_dir)
    generated: dict[str, list[Path]] = {}
    for name, generator in FIGURE_GENERATORS.items():
        try:
            generated[name] = generator(results, output)
        except (
            PublicationGenerationError,
            FileNotFoundError,
            KeyError,
            json.JSONDecodeError,
        ):
            # Reference-faithful graceful degradation: a figure whose stored
            # benchmark artefact is absent or malformed yields an empty entry
            # rather than aborting the whole batch (PRINet 3.0
            # ``generate_all_figures`` catches the same failure classes;
            # WP036C-F1).
            generated[name] = []
    return generated


__all__ = [
    "ALLOWED_OUTPUT_ROOTS",
    "COLORS",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_RESULTS_DIR",
    "FIGURE_GENERATORS",
    "ArtifactNotFoundError",
    "ArtifactSchemaError",
    "NormalizationError",
    "OutputPathError",
    "PublicationGenerationError",
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
    "normalize_matplotlib_output",
]

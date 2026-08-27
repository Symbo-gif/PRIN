"""Deterministic LaTeX table generation from stored PRINet 3.0 artefacts."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from prin.reporting._artifacts import (
    ArtifactNotFoundError,
    ArtifactSchemaError,
    OutputPathError,
    PublicationGenerationError,
    ReportingError,
    _load_json,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_DIR = _REPOSITORY_ROOT / "benchmarks" / "results"
DEFAULT_OUTPUT_DIR = _REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results" / "tables"
ALLOWED_OUTPUT_ROOTS = (
    (_REPOSITORY_ROOT / "benchmarks" / "results").resolve(),
    (_REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)
_ROW_END = r"\\"


def _dirs(results_dir: Path | None, output_dir: Path | None) -> tuple[Path, Path]:
    results = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    output = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    resolved = output.resolve()
    if not any(
        resolved == root or root in resolved.parents for root in ALLOWED_OUTPUT_ROOTS
    ):
        roots = ", ".join(str(root) for root in ALLOWED_OUTPUT_ROOTS)
        raise OutputPathError(
            f"output directory {resolved} is outside allowed roots: {roots}"
        )
    return results, resolved


def _save_table(content: str, name: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.tex"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def _row(*cells: object) -> str:
    return " & ".join(str(cell) for cell in cells) + f" {_ROW_END}"


def _start(caption: str, label: str, columns: str, header: str) -> list[str]:
    return [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{columns}}}",
        r"\toprule",
        header + f" {_ROW_END}",
        r"\midrule",
    ]


def _finish(lines: list[str], name: str, output: Path) -> Path:
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return _save_table("\n".join(lines), name, output)


def table_ablation_variants(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the historical ablation-variant comparison table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_ablation_variants(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    variants = _load_json(results / "benchmark_y4q1_ablation_variants.json")["variants"]
    lines = _start(
        "HybridPRINetV2 ablation study. Accuracy, parameter count, and FLOPs "
        "for each architectural variant on CLEVR-N (N=6).",
        "tab:ablation",
        "lccc",
        r"Variant & Accuracy (\%) & Params & FLOPs",
    )
    for item in variants:
        name = item["variant"].replace("_", r"\_")
        lines.append(
            _row(
                name,
                f"{item['test_accuracy'] * 100:.1f}",
                f"{item['n_params']:,}",
                f"{item['total_flops']:,}",
            )
        )
    return _finish(lines, "tab_ablation", output)


def table_parameter_efficiency(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the historical parameter-efficiency frontier table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_parameter_efficiency(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    models = _load_json(results / "y4q1_8_parameter_efficiency_frontier.json")["models"]
    lines = _start(
        r"Parameter efficiency frontier. PT-Small achieves 16.8$\times$ "
        "better IP-per-parameter than Slot Attention.",
        "tab:param_efficiency",
        "lcccc",
        "Model & Params & Mean IP & IP/Param & Latency (ms)",
    )
    for item in models:
        lines.append(
            _row(
                item["model"],
                f"{item['total_params']:,}",
                f"{item['mean_ip']:.4f}",
                f"{item['ip_per_param']:.4f}",
                f"{item['wall_time_ms']:.2f}",
            )
        )
    return _finish(lines, "tab_param_efficiency", output)


def table_chimera_gold_standard(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the gold-standard chimera table with the Phase 1 enhancement.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_chimera_gold_standard(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    try:
        phase1 = _load_json(results / "phase1_chimera_seeds.json")
    except ArtifactNotFoundError:
        phase1 = None
    data = _load_json(results / "benchmark_y4q1_3_gold_standard_chimera.json")
    if phase1 is not None:
        bc = phase1.get("bimodality_coefficient", phase1)
        raw = bc.get("raw_values", [])
        count = bc.get("n_sequences", len(raw))
        lines = _start(
            f"Chimera state characterisation (Phase~1 enhanced, {count} "
            r"sequences). All sequences exceed BC $> 0.555$ chimera threshold.",
            "tab:chimera",
            "lc",
            "Metric & Value",
        )
        for index, value in enumerate(raw):
            lines.append(_row(f"Sequence {index + 1} BC", f"{value:.4f}"))
        lines.extend(
            [
                r"\midrule",
                _row("Mean BC", f"{bc.get('mean', 0):.4f}"),
                _row("Std", f"{bc.get('std', 0):.4f}"),
                _row(
                    r"95\% CI",
                    f"[{bc.get('ci_95_low', 0):.4f}, {bc.get('ci_95_high', 0):.4f}]",
                ),
            ]
        )
    else:
        lines = _start(
            "Gold-standard chimera state characterization (N=256, K=100, "
            r"$\alpha=\pi/2+0.05$, cosine kernel, RK4).",
            "tab:chimera",
            "lcccc",
            r"Seed & BC & SI & $\chi$ & $\eta$",
        )
        for seed in data["seeds"]:
            lines.append(
                _row(
                    f"Seed {seed['seed']}",
                    f"{seed['bc']:.4f}",
                    f"{seed['si']:.4f}",
                    f"{seed['chi']:.4f}",
                    seed["eta"],
                )
            )
        aggregate = data.get("aggregate", {})
        if aggregate:
            lines.extend(
                [
                    r"\midrule",
                    _row(
                        "Mean",
                        f"{aggregate.get('bc_mean', 0):.4f}",
                        f"{aggregate.get('si_mean', 0):.4f}",
                        f"{aggregate.get('chi_mean', 0):.4f}",
                        "---",
                    ),
                ]
            )
    return _finish(lines, "tab_chimera", output)


def _optional(results: Path, filename: str) -> dict[str, Any] | None:
    try:
        return _load_json(results / filename)
    except ArtifactNotFoundError:
        return None


def table_statistical_summary(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the hardened PT-versus-SA statistical comparison table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_statistical_summary(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    data = _load_json(results / "y4q1_7_statistical_summary.json")
    pt = data["phase_tracker"]
    sa = data["slot_attention"]
    test = data["welch_t_test"]
    lines = _start(
        "Head-to-head statistical comparison with Phase~1 hardening. TOST "
        r"confirms equivalence at $\delta=0.5\%$; Bayesian "
        r"$\mathrm{P(equiv)}=0.996$.",
        "tab:statistical",
        "lcc",
        "Metric & PhaseTracker & Slot Attention",
    )
    lines.extend(
        [
            _row("Mean IP", f"{pt['mean']:.4f}", f"{sa['mean']:.4f}"),
            _row(
                r"95\% CI",
                f"[{pt['ci_95'][0]:.4f}, {pt['ci_95'][1]:.4f}]",
                f"[{sa['ci_95'][0]:.4f}, {sa['ci_95'][1]:.4f}]",
            ),
            _row("Parameters", "4,991", "83,904"),
            r"\midrule",
            _row(
                r"$\Delta$ IP",
                rf"\multicolumn{{2}}{{c}}{{{test['mean_diff']:.4f}}}",
            ),
            _row(
                "Welch's $p$",
                rf"\multicolumn{{2}}{{c}}{{{test['p_value']:.3f}}}",
            ),
            _row(
                "Cohen's $d$",
                rf"\multicolumn{{2}}{{c}}{{{test['cohens_d']:.2f}}}",
            ),
        ]
    )
    tost = _optional(results, "phase1_bf_tost_resolution.json")
    cliffs = _optional(results, "phase1_cliffs_delta.json")
    bayes = _optional(results, "phase1_bayes_factor.json")
    holm = _optional(results, "phase1_holm_bonferroni.json")
    additions = [
        (tost, "tost_p", r"TOST $p$ ($\delta=0.5\%$)", ".4f"),
        (cliffs, "cliffs_delta", r"Cliff's $\delta$", ".3f"),
        (bayes, "bf10", r"$\mathrm{BF}_{10}$", ".3f"),
        (tost, "bayesian_prob_equivalent", r"$\mathrm{P(equiv)}$", ".3f"),
    ]
    for optional, key, label, spec in additions:
        if optional is not None and key in optional:
            value = format(optional[key], spec)
            lines.append(_row(label, rf"\multicolumn{{2}}{{c}}{{{value}}}"))
    if holm is not None:
        value = holm.get("n_significant_after_correction", "---")
        lines.append(
            _row("Holm--Bonferroni sig.", rf"\multicolumn{{2}}{{c}}{{{value}}}")
        )
    outcome = data["outcome"].replace("_", r"\_")
    lines.append(_row("Outcome", rf"\multicolumn{{2}}{{c}}{{\texttt{{{outcome}}}}}"))
    return _finish(lines, "tab_statistical", output)


def table_occlusion_sweep(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the identity-preservation occlusion sweep table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_occlusion_sweep(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    sweep = _load_json(results / "y4q1_9_fine_occlusion.json")["sweep"]
    lines = _start(
        "Identity preservation under increasing occlusion. SA maintains perfect "
        "tracking; PT degrades exponentially.",
        "tab:occlusion",
        "ccccc",
        r"Occlusion (\%) & PT Mean IP & PT 95\% CI & SA Mean IP",
    )
    for item in sweep:
        lines.append(
            _row(
                int(item["occlusion_rate"] * 100),
                f"{item['pt_stats']['mean']:.4f}",
                f"[{item['pt_stats']['ci_low']:.3f}, "
                f"{item['pt_stats']['ci_high']:.3f}]",
                f"{item['sa_stats']['mean']:.4f}",
            )
        )
    return _finish(lines, "tab_occlusion", output)


def _throughput(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.2f}B"
    if value >= 1e6:
        return f"{value / 1e6:.1f}M"
    if value >= 1e3:
        return f"{value / 1e3:.0f}K"
    return f"{value:.0f}"


def table_oscillosim_scaling(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the OscilloSim throughput-by-mode table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_oscillosim_scaling(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    modes = _load_json(results / "y3q4_p4_oscillosim_scaling.json")["results_by_mode"]
    lines = _start(
        r"OscilloSim GPU throughput (osc$\cdot$step/s) by coupling mode and "
        "system size. RTX 4060, CUDA 13.0.",
        "tab:oscillosim",
        "lccc",
        "N & Mean-field & Sparse k-NN & CSR",
    )
    all_ns = sorted(
        {item["n_oscillators"] for items in modes.values() for item in items}
    )
    for n in all_ns:
        row = [f"{n:,}"]
        for mode in ("mean_field", "sparse_knn", "csr"):
            match = [
                item
                for item in modes.get(mode, [])
                if item["n_oscillators"] == n and item["status"] == "OK"
            ]
            row.append(
                _throughput(match[0]["throughput_osc_step_per_s"]) if match else "---"
            )
        lines.append(_row(*row))
    return _finish(lines, "tab_oscillosim", output)


def table_efficiency_profile(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the computational efficiency profile table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_efficiency_profile(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    profiles = _load_json(results / "phase3_profiling.json")["per_pair_profiles"]
    grouped: dict[int, dict[str, dict[str, Any]]] = {}
    for item in profiles:
        grouped.setdefault(item["n_objects"], {})[item["model"]] = item
    lines = _start(
        "Computational efficiency profile. PhaseTracker (PT) vs Slot Attention "
        r"(SA) across object counts. FLOPs ratio exceeds 44$\times$ at all scales.",
        "tab:efficiency",
        "clccc",
        r"$N$ & Model & FLOPs & Latency (ms) & Memory (MB)",
    )
    for index, n in enumerate(sorted(grouped)):
        pt = grouped[n].get("PhaseTracker", {})
        sa = grouped[n].get("SlotAttention", {})
        pt_flops = pt.get("flops", 0)
        sa_flops = sa.get("flops", 0)
        lines.extend(
            [
                _row(
                    rf"\multirow{{2}}{{*}}{{{n}}}",
                    "PT",
                    f"{pt_flops:,}",
                    f"{pt.get('latency_ms', {}).get('mean', 0):.2f}",
                    f"{pt.get('peak_memory_mb', 0):.1f}",
                ),
                f"& SA & {sa_flops:,} & "
                f"{sa.get('latency_ms', {}).get('mean', 0):.2f} & "
                f"{sa.get('peak_memory_mb', 0):.1f} {_ROW_END}",
                f"& \\textit{{Ratio}} & "
                f"\\textit{{{sa_flops / pt_flops if pt_flops else 0:.1f}"
                f"$\\times$}} & & {_ROW_END}",
            ]
        )
        if index + 1 < len(grouped):
            lines.append(r"\midrule")
    return _finish(lines, "tab_efficiency", output)


def table_binding_breakdown(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the binding-mechanism parameter breakdown table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_binding_breakdown(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    data = _load_json(results / "phase4_parameter_scaling.json")
    breakdown = data["parameter_breakdown"]
    coupling = data["coupling_analysis"]
    pt = breakdown["PhaseTracker"]["components"]
    sa = breakdown["SlotAttention"]["components"]
    lines = _start(
        "Binding mechanism parameter breakdown. PhaseTracker's oscillatory "
        r"binding uses $O(1)$ parameters (w.r.t.\ $N$ and $d$) vs Slot "
        r"Attention's $O(d^2)$.",
        "tab:binding_params",
        "lcc",
        "Component & PhaseTracker & Slot Attention",
    )
    for name, value in pt.items():
        lines.append(_row(name.replace("_", " ").title(), f"{value:,}", "---"))
    lines.append(r"\midrule")
    for name, value in sa.items():
        lines.append(_row(name.replace("_", " ").title(), "---", f"{value:,}"))
    lines.extend(
        [
            r"\midrule",
            _row(
                r"\textbf{Binding Params$^\dagger$}",
                rf"\textbf{{{coupling['PT_dynamics_total']:,}}}",
                rf"\textbf{{{coupling['SA_attention_params']:,}}}",
            ),
            _row(
                r"\textbf{Total}",
                rf"\textbf{{{breakdown['PhaseTracker']['total']:,}}}",
                rf"\textbf{{{breakdown['SlotAttention']['total']:,}}}",
            ),
            _row(
                "Ratio (SA/PT)",
                rf"\multicolumn{{2}}{{c}}{{{breakdown['ratio']:.1f}$\times$}}",
            ),
        ]
    )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\vspace{0.3em}",
            "",
            r"{\footnotesize $^\dagger$Core mechanism only: "
            r"coupling/frequency/PAC weights (PT), QKV projections (SA). The "
            r"$143\times$ ratio in Proposition~\ref{prop:efficiency} compares "
            r"PT's 379 binding params against SA's full Slot Attention module "
            r"(54{,}336).}",
            r"\end{table}",
        ]
    )
    return _save_table("\n".join(lines), "tab_binding_params", output)


def table_stress_conditions(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the identity-preservation stress-condition table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_stress_conditions(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    conditions = _load_json(results / "y4q1_7_stress_test_summary.json")["conditions"]
    lines = _start(
        "Identity preservation under stress conditions. SA dominates all "
        "conditions; PT degrades gracefully under velocity stress.",
        "tab:stress",
        "lccc",
        "Condition & PT (mean) & SA (mean) & Winner",
    )
    for item in conditions:
        pt = item.get("pt_mean", item.get("pt_ip", 0))
        sa = item.get("sa_mean", item.get("sa_ip", 0))
        lines.append(
            _row(
                item["condition"].replace("_", " ").title(),
                f"{pt:.4f}",
                f"{sa:.4f}",
                "SA" if sa >= pt else "PT",
            )
        )
    return _finish(lines, "tab_stress", output)


def table_supercritical_regime(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the supercritical-coupling regime table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_supercritical_regime(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    aggregated = _load_json(results / "phase4_convergence_verification.json")[
        "aggregated"
    ]
    lines = _start(
        "Supercritical coupling regime. All frequency bands operate deep in "
        r"the supercritical regime ($K_{\mathrm{eff}} \gg K_c$).",
        "tab:supercritical",
        "lcccc",
        r"Band & $K_c$ (theory) & $K_{\mathrm{eff}}$ (emp.) & Ratio & $\lambda$",
    )
    labels = (
        r"$\delta$ (1--4\,Hz)",
        r"$\theta$ (4--8\,Hz)",
        r"$\gamma$ (25--100\,Hz)",
    )
    for band, label in zip(("delta", "theta", "gamma"), labels, strict=True):
        item = aggregated[band]
        theory = item["K_c_theory"]["mean"]
        empirical = item["K_c_empirical"]["mean"]
        lines.append(
            _row(
                label,
                f"{theory:.4f}",
                f"{empirical:.4f}",
                rf"{empirical / theory:.0f}$\times$",
                f"{item['convergence_rate_lambda']['mean']:.4f}",
            )
        )
    return _finish(lines, "tab_supercritical", output)


def table_representation_geometry(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> Path:
    """Generate the representation-geometry comparison table.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for the generated file. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Path to the generated LaTeX table fragment.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> table = table_representation_geometry(output_dir=target)  # doctest: +SKIP
        >>> table.suffix  # doctest: +SKIP
        '.tex'
    """
    results, output = _dirs(results_dir, output_dir)
    comparison = _load_json(results / "phase3_representation_geometry.json")[
        "comparison"
    ]
    lines = _start(
        r"Representation geometry. Phase embeddings achieve 3.3$\times$ "
        r"higher k-NN purity in 3$\times$ fewer intrinsic dimensions.",
        "tab:geometry",
        "lcc",
        "Metric & PhaseTracker & Slot Attention",
    )
    lines.extend(
        [
            _row(
                "k-NN Purity",
                f"{comparison['pt_knn_purity']:.3f}",
                f"{comparison['sa_knn_purity']:.3f}",
            ),
            _row(
                r"Intrinsic Dim. (90\%)",
                comparison["pt_intrinsic_dim"],
                comparison["sa_intrinsic_dim"],
            ),
            _row(
                "Silhouette (original)",
                f"{comparison['pt_silhouette']:.4f}",
                f"{comparison['sa_silhouette']:.4f}",
            ),
        ]
    )
    return _finish(lines, "tab_geometry", output)


TABLE_GENERATORS: dict[str, Callable[[Path | None, Path | None], Path]] = {
    "tab_ablation": table_ablation_variants,
    "tab_param_efficiency": table_parameter_efficiency,
    "tab_chimera": table_chimera_gold_standard,
    "tab_statistical": table_statistical_summary,
    "tab_occlusion": table_occlusion_sweep,
    "tab_oscillosim": table_oscillosim_scaling,
    "tab_efficiency": table_efficiency_profile,
    "tab_binding_params": table_binding_breakdown,
    "tab_stress": table_stress_conditions,
    "tab_supercritical": table_supercritical_regime,
    "tab_geometry": table_representation_geometry,
}


def generate_all_tables(
    results_dir: Path | None = None, output_dir: Path | None = None
) -> dict[str, Path]:
    """Generate all eleven historical publication tables.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
            Defaults to ``DEFAULT_RESULTS_DIR``.
        output_dir: Destination for generated files. Defaults to
            ``DEFAULT_OUTPUT_DIR``.

    Returns:
        Generated LaTeX fragment paths keyed by historical table name.

    Raises:
        PublicationGenerationError: If a required artefact or output path is invalid.

    Examples:
        >>> target = Path(tempfile.gettempdir()) / "prin-tables"
        >>> tables = generate_all_tables(output_dir=target)  # doctest: +SKIP
        >>> len(tables)  # doctest: +SKIP
        11
    """
    results, output = _dirs(results_dir, output_dir)
    return {
        name: generator(results, output) for name, generator in TABLE_GENERATORS.items()
    }


__all__ = [
    "ALLOWED_OUTPUT_ROOTS",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_RESULTS_DIR",
    "TABLE_GENERATORS",
    "ArtifactNotFoundError",
    "ArtifactSchemaError",
    "OutputPathError",
    "PublicationGenerationError",
    "ReportingError",
    "generate_all_tables",
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

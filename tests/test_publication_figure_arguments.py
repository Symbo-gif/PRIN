"""Reference drawing arguments of the nine EXP-002 D1 figure generators.

EXP-002 H3 was refuted because the PRIN port of nine PRINet 3.0 figure
generators dropped or re-encoded drawing arguments. The registered root-cause
decomposition in ``EVIDENCE/exp002-d1-s1/`` lists them. The byte-level gate
against the frozen reference is ``parity/test_parity_publication.py``, which
runs in the parity suite only. These fast-gate tests pin each byte-material
argument on the live Figure objects instead, so a regression fails the default
``tests/`` run as well. The comment on each assertion names its divergence ID.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from matplotlib.colors import to_hex
from matplotlib.figure import Figure
from prin.reporting import figure_generation as figures

RESULTS = (
    Path(__file__).resolve().parents[1]
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
    / "benchmarks"
    / "results"
)
TIMES = "\N{MULTIPLICATION SIGN}"
UPPER_RIGHT = 1
LOWER_LEFT = 3

Generator = Callable[[Path | None, Path | None], list[Path]]


@pytest.fixture
def render(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[Callable[[Generator], Figure]]:
    """Run a generator on the archived inputs and return its unsaved Figure."""
    captured: list[Figure] = []

    def capture(fig: Figure, *_: Any, **__: Any) -> list[Path]:
        captured.append(fig)
        return []

    monkeypatch.setattr(figures, "ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))
    monkeypatch.setattr(figures, "_save_fig", capture)

    def run(generator: Generator) -> Figure:
        generator(RESULTS, tmp_path)
        assert len(captured) == 1
        return captured.pop()

    yield run
    figures.plt.close("all")


def test_fig5_marker_sizes(render: Callable[[Generator], Figure]) -> None:
    ax = render(figures.fig_mot_identity_preservation).axes[0]
    data_line = ax.containers[0].lines[0]
    sa_line = next(line for line in ax.lines if line.get_label() == "Slot Attention")
    for line in (data_line, sa_line):
        assert line.get_markersize() == 4  # D5.2, D5.4
        assert line.get_linewidth() == 1.5  # D5.1, D5.3


def test_fig7_accuracy_labels_bottom_aligned(
    render: Callable[[Generator], Figure],
) -> None:
    texts = render(figures.fig_ablation_results).axes[0].texts
    assert texts
    assert {text.get_verticalalignment() for text in texts} == {"bottom"}  # D7.1


def test_fig8_markers_drawn_above_grid(render: Callable[[Generator], Figure]) -> None:
    collections = render(figures.fig_parameter_efficiency).axes[0].collections
    assert len(collections) == 3
    assert {collection.get_zorder() for collection in collections} == {5}  # D8.1


def test_fig9_curve_widths_legend_and_labels(
    render: Callable[[Generator], Figure],
) -> None:
    curves, bars = render(figures.fig_training_curves).axes
    assert len(curves.lines) == 4
    assert {line.get_linewidth() for line in curves.lines} == {1.2}  # D9.1
    legend = curves.get_legend()
    assert legend is not None
    assert legend._loc == UPPER_RIGHT  # D9.2
    assert {text.get_verticalalignment() for text in bars.texts} == {"bottom"}  # D9.3


def test_fig10_outcome_note_has_reference_box(
    render: Callable[[Generator], Figure],
) -> None:
    (note,) = render(figures.fig_statistical_summary).axes[0].texts
    box = note.get_bbox_patch()
    assert box is not None  # D10.1
    assert to_hex(box.get_facecolor()) == to_hex("lightyellow")
    assert to_hex(box.get_edgecolor()) == to_hex("gray")


def test_fig11_bars_labels_and_ratios(render: Callable[[Generator], Figure]) -> None:
    ax = render(figures.fig_flops_scaling).axes[0]
    assert ax.patches
    for bar in ax.patches:
        assert to_hex(bar.get_edgecolor()) == "#000000"  # D11.1
        assert bar.get_linewidth() == 0.5  # D11.2
    assert ax.get_ylabel() == f"FLOPs ({TIMES}10\N{SUPERSCRIPT THREE})"  # D11.3
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_frame().get_alpha() == 0.8  # D11.4
    assert len(ax.texts) == 3
    for ratio in ax.texts:
        assert ratio.get_text().endswith(TIMES)  # D11.5
        assert "$" not in ratio.get_text()
        assert ratio.get_verticalalignment() == "bottom"  # D11.6


def test_fig12_reference_styling(render: Callable[[Generator], Figure]) -> None:
    bars, twin = render(figures.fig_supercritical_regime).axes
    assert {bar.get_linewidth() for bar in bars.patches} == {0.5}  # D12.1
    assert [label.get_text() for label in bars.get_xticklabels()] == [
        "\N{GREEK SMALL LETTER DELTA} (1\N{EN DASH}4 Hz)",
        "\N{GREEK SMALL LETTER THETA} (4\N{EN DASH}8 Hz)",
        "\N{GREEK SMALL LETTER GAMMA} (25\N{EN DASH}100 Hz)",
    ]  # D12.2
    (threshold,) = bars.lines
    assert threshold.get_linewidth() == 0.8  # D12.3
    assert threshold.get_alpha() == 0.7  # D12.4
    (rates,) = twin.lines
    assert rates.get_markersize() == 5  # D12.5
    assert rates.get_linewidth() == 1.2  # D12.6
    assert rates.get_label() == r"$\lambda$ (convergence)"  # D12.7
    assert to_hex(twin.yaxis.get_tick_params()["labelcolor"]) == "#aa3377"  # D12.8
    assert len(bars.texts) == 3
    for ratio in bars.texts:
        assert ratio.get_text().endswith(TIMES)  # D12.9
        assert "$" not in ratio.get_text()
        assert ratio.get_verticalalignment() == "bottom"  # D12.10


def test_fig14_bar_transparency(render: Callable[[Generator], Figure]) -> None:
    for ax in render(figures.fig_gradient_flow).axes:
        assert ax.patches
        assert {bar.get_alpha() for bar in ax.patches} == {0.85}  # D14.1


def test_fig15_marker_sizes_fit_and_legends(
    render: Callable[[Generator], Figure],
) -> None:
    noise, velocity = render(figures.fig_noise_velocity).axes
    pt, sa, fit = noise.lines
    assert pt.get_markersize() == sa.get_markersize() == 3  # D15.1
    assert fit.get_alpha() == 0.5  # D15.2
    assert fit.get_linewidth() == 1  # D15.3
    assert {line.get_markersize() for line in velocity.lines} == {4}  # D15.5
    assert velocity.get_xlabel() == f"Speed Multiplier ({TIMES})"  # D15.6
    for ax in (noise, velocity):
        legend = ax.get_legend()
        assert legend is not None
        assert legend._loc == LOWER_LEFT  # D15.4, D15.7

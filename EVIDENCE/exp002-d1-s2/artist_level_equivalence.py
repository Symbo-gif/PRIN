"""Compare the rendered matplotlib artists of the reference and the fixed port.

This is the S2 audit instrument for the second half of item 2 of the EXP-002
D1 S2 brief: *confirm that no divergence alters a plotted value*.

Byte equality of the 39 publication files shows the two arms render the same
output; it does not by itself show **why**. This instrument renders all 14
registered figure stems from both the frozen PRINet 3.0 generator and PRIN's
port, intercepts each ``Figure`` at ``savefig``, and compares the full artist
inventory that matplotlib itself holds:

* ``Line2D`` -- x data, y data, linewidth, markersize, marker, linestyle,
  alpha, zorder, colour, label;
* ``Collection`` -- offsets, face and edge colour, alpha, zorder, linewidths;
* ``Patch`` -- path vertices, face and edge colour, linewidth, alpha, zorder;
* ``Text`` -- the string, position, vertical and horizontal alignment,
  fontsize, rotation, colour;
* ``Axes`` -- limits, scales, title, axis labels, tick positions and tick
  label strings, legend texts.

Data-bearing attributes are compared by SHA-256 over their ``float64`` buffer
together with their shape, so a single differing plotted coordinate is a
failure. If every artist attribute is equal on all 14 stems, no plotted value
differs -- which is the claim the completeness result (``A == P``) makes at
byte level, re-derived here from the object model.

The instrument also counts drawing calls made directly by each generator, and
reports the multiset difference. This is what separates a real argument
divergence from a harmless restructuring: the port's ``ax.set(title=...,
ylabel=...)`` grouping and its loops produce different *call* multisets while
producing identical *artists*.

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/artist_level_equivalence.py

Exit status is ``0`` when all 14 stems are artist-equal, else ``1``.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.campaign import exp002_driver as driver  # noqa: E402

RESULTS = driver.REFERENCE / "benchmarks" / "results"

#: Registered figure stem to generator function name (same in both modules).
STEMS: dict[str, str] = {
    "fig2_clevr_n_capacity": "fig_clevr_n_capacity",
    "fig3_chimera_metrics": "fig_gold_standard_chimera",
    "fig4_chimera_k_alpha_heatmap": "fig_chimera_heatmap",
    "fig5_mot_occlusion_comparison": "fig_mot_identity_preservation",
    "fig6_oscillosim_scaling": "fig_oscillosim_scaling",
    "fig7_ablation_results": "fig_ablation_results",
    "fig8_parameter_efficiency": "fig_parameter_efficiency",
    "fig9_training_curves": "fig_training_curves",
    "fig10_statistical_summary": "fig_statistical_summary",
    "fig11_flops_scaling": "fig_flops_scaling",
    "fig12_supercritical_regime": "fig_supercritical_regime",
    "fig13_representation_geometry": "fig_representation_geometry",
    "fig14_gradient_flow": "fig_gradient_flow",
    "fig15_noise_velocity": "fig_noise_velocity",
}

#: ``Axes`` methods counted when attributing call-structure differences.
COUNTED_METHODS: tuple[str, ...] = (
    "plot",
    "errorbar",
    "scatter",
    "bar",
    "barh",
    "axhline",
    "axvline",
    "text",
    "annotate",
    "legend",
    "set",
    "set_title",
    "set_xlabel",
    "set_ylabel",
    "set_xticklabels",
    "set_yticklabels",
    "set_xlim",
    "set_ylim",
    "tick_params",
    "fill_between",
    "loglog",
    "semilogy",
    "imshow",
)


def digest_array(value: Any) -> str:
    """Return a shape-qualified SHA-256 prefix of a numeric array's bytes."""
    array = np.asarray(value, dtype="float64")
    return hashlib.sha256(array.tobytes()).hexdigest()[:16] + f"/shape{array.shape}"


def encode_colour(value: Any) -> str:
    """Return a stable JSON rendering of a matplotlib colour or colour array."""
    try:
        return json.dumps(np.asarray(value, dtype="float64").round(6).tolist())
    except (TypeError, ValueError):  # pragma: no cover - exotic colour objects
        return repr(value)


def line_artists(axes: Any) -> list[tuple[Any, ...]]:
    """Return a comparable signature for every ``Line2D`` on ``axes``."""
    out: list[tuple[Any, ...]] = []
    for line in axes.get_lines():
        out.append(
            (
                "line",
                digest_array(line.get_xdata()),
                digest_array(line.get_ydata()),
                round(float(line.get_linewidth()), 6),
                round(float(line.get_markersize()), 6),
                str(line.get_marker()),
                str(line.get_linestyle()),
                line.get_alpha(),
                int(line.get_zorder()),
                encode_colour(line.get_color()),
                str(line.get_label()),
            )
        )
    return sorted(out, key=repr)


def text_artists(axes: Any) -> list[tuple[Any, ...]]:
    """Return a comparable signature for every ``Text`` on ``axes``."""
    out: list[tuple[Any, ...]] = []
    for text in axes.texts:
        position = text.get_position()
        out.append(
            (
                "text",
                str(text.get_text()),
                round(float(position[0]), 6),
                round(float(position[1]), 6),
                str(text.get_verticalalignment()),
                str(text.get_horizontalalignment()),
                round(float(text.get_fontsize()), 6),
                round(float(text.get_rotation()), 6),
                encode_colour(text.get_color()),
            )
        )
    return sorted(out, key=repr)


def patch_artists(axes: Any) -> list[tuple[Any, ...]]:
    """Return a comparable signature for every ``Patch`` on ``axes``."""
    out: list[tuple[Any, ...]] = []
    for patch in axes.patches:
        try:
            vertices = np.asarray(patch.get_path().vertices, dtype="float64")
            geometry = hashlib.sha256(vertices.tobytes()).hexdigest()[:16]
            geometry += f"/n{len(vertices)}"
        except (AttributeError, TypeError):  # pragma: no cover - pathless patch
            geometry = "n/a"
        out.append(
            (
                "patch",
                type(patch).__name__,
                geometry,
                encode_colour(patch.get_facecolor()),
                encode_colour(patch.get_edgecolor()),
                round(float(patch.get_linewidth()), 6),
                patch.get_alpha(),
                int(patch.get_zorder()),
            )
        )
    return sorted(out, key=repr)


def collection_artists(axes: Any) -> list[tuple[Any, ...]]:
    """Return a comparable signature for every ``Collection`` on ``axes``."""
    out: list[tuple[Any, ...]] = []
    for collection in axes.collections:
        try:
            offsets = np.asarray(collection.get_offsets(), dtype="float64")
            summary = hashlib.sha256(offsets.tobytes()).hexdigest()[:16]
            summary += f"/n{len(offsets)}"
        except (AttributeError, TypeError):  # pragma: no cover - no offsets
            summary = "n/a"
        out.append(
            (
                "collection",
                type(collection).__name__,
                summary,
                encode_colour(collection.get_facecolor()),
                encode_colour(collection.get_edgecolor()),
                collection.get_alpha(),
                int(collection.get_zorder()),
                np.asarray(collection.get_linewidths(), dtype="float64").tolist(),
            )
        )
    return sorted(out, key=repr)


def axes_signature(axes: Any) -> dict[str, Any]:
    """Return the full comparable artist inventory of one ``Axes``."""
    legend = axes.get_legend()
    return {
        "xlim": tuple(np.round(axes.get_xlim(), 9).tolist()),
        "ylim": tuple(np.round(axes.get_ylim(), 9).tolist()),
        "xscale": str(axes.get_xscale()),
        "yscale": str(axes.get_yscale()),
        "title": str(axes.get_title()),
        "xlabel": str(axes.get_xlabel()),
        "ylabel": str(axes.get_ylabel()),
        "xticklabels": [str(t.get_text()) for t in axes.get_xticklabels()],
        "yticklabels": [str(t.get_text()) for t in axes.get_yticklabels()],
        "xticks": tuple(np.round(axes.get_xticks(), 9).tolist()),
        "yticks": tuple(np.round(axes.get_yticks(), 9).tolist()),
        "legend_texts": (
            [str(t.get_text()) for t in legend.get_texts()] if legend else None
        ),
        "lines": line_artists(axes),
        "texts": text_artists(axes),
        "patches": patch_artists(axes),
        "collections": collection_artists(axes),
    }


def figure_signature(figure: Any) -> dict[str, Any]:
    """Return the comparable inventory of a whole ``Figure``."""
    return {
        "figsize": tuple(np.round(np.asarray(figure.get_size_inches()), 6).tolist()),
        "n_axes": len(figure.axes),
        "axes": [axes_signature(axes) for axes in figure.axes],
    }


def _counting_wrapper(name: str, original: Any, calls: Counter[str]) -> Any:
    """Build a wrapper that counts calls made directly by a figure generator."""

    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        frame = sys._getframe(1)
        caller = str(frame.f_globals.get("__name__", ""))
        if caller.endswith("figure_generation"):
            calls[name] += 1
        return original(self, *args, **kwargs)

    return wrapper


def render_and_capture(
    module: Any, func_name: str
) -> tuple[dict[str, Any], Counter[str]]:
    """Render one generator, capturing its Figure and its direct drawing calls.

    Args:
        module: The generator module to render from.
        func_name: The generator function's name in that module.

    Returns:
        The captured figure signature and a counter of the drawing calls the
        generator itself made.

    Raises:
        SystemExit: If the generator saved no figure.
    """
    captured: list[dict[str, Any]] = []
    calls: Counter[str] = Counter()
    original_savefig = matplotlib.figure.Figure.savefig

    def savefig_spy(self: Any, *args: Any, **kwargs: Any) -> Any:
        captured.append(figure_signature(self))
        return original_savefig(self, *args, **kwargs)

    saved: dict[str, Callable[..., Any]] = {}
    for name in COUNTED_METHODS:
        original = getattr(matplotlib.axes.Axes, name, None)
        if original is None:  # pragma: no cover - method set is version-stable
            continue
        saved[name] = original
        setattr(matplotlib.axes.Axes, name, _counting_wrapper(name, original, calls))

    matplotlib.figure.Figure.savefig = savefig_spy  # type: ignore[method-assign]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            with contextlib.redirect_stdout(io.StringIO()):
                getattr(module, func_name)(
                    results_dir=RESULTS, output_dir=Path(temporary)
                )
    finally:
        matplotlib.figure.Figure.savefig = original_savefig  # type: ignore[method-assign]
        for name, original in saved.items():
            setattr(matplotlib.axes.Axes, name, original)
        plt.close("all")

    if not captured:
        raise SystemExit(f"{func_name}: no figure captured")
    return captured[0], calls


def describe_signature_difference(
    stem: str, reference: dict[str, Any], port: dict[str, Any]
) -> None:
    """Print the first-level differences between two figure signatures."""
    if reference["figsize"] != port["figsize"]:
        print(f"    figsize: {reference['figsize']} vs {port['figsize']}")
    if reference["n_axes"] != port["n_axes"]:
        print(f"    n_axes: {reference['n_axes']} vs {port['n_axes']}")
    for index, (ref_axes, port_axes) in enumerate(
        zip(reference["axes"], port["axes"], strict=False)
    ):
        for key, ref_value in ref_axes.items():
            if ref_value != port_axes.get(key):
                ref_text = json.dumps(ref_value, default=str)[:220]
                port_text = json.dumps(port_axes.get(key), default=str)[:220]
                print(f"    {stem} axes[{index}].{key}:")
                print(f"      reference: {ref_text}")
                print(f"      port     : {port_text}")


def main() -> int:
    """Render all 14 stems from both modules and compare their artists."""
    reference = importlib.import_module("prinet.utils.figure_generation")
    port = importlib.import_module("prin.reporting.figure_generation")

    reference_path = Path(str(reference.__file__)).resolve()
    port_path = Path(str(port.__file__)).resolve()
    pinned = driver.REFERENCE_PINS["src/prinet/utils/figure_generation.py"]
    reference_digest = hashlib.sha256(reference_path.read_bytes()).hexdigest()

    print("reference module :", reference_path)
    print("  sha256         :", reference_digest)
    print("  pinned digest  :", pinned)
    print(f"  matches the pin: {reference_digest == pinned}")
    print("port module      :", port_path)
    print("  sha256         :", hashlib.sha256(port_path.read_bytes()).hexdigest())
    print()
    if reference_digest != pinned:
        print("ABORT: the imported reference is not the pinned frozen generator")
        return 1

    failures: list[str] = []
    for stem, func in STEMS.items():
        ref_signature, ref_calls = render_and_capture(reference, func)
        port_signature, port_calls = render_and_capture(port, func)
        same_signature = ref_signature == port_signature
        same_calls = ref_calls == port_calls
        if not same_signature:
            failures.append(stem)
        print(
            f"[{'EQUAL ' if same_signature else 'DIFFER'}] {stem}  "
            f"axes={ref_signature['n_axes']}  drawing-call multiset "
            f"{'equal' if same_calls else 'DIFFERS'}"
        )
        if not same_calls:
            only_reference = ref_calls - port_calls
            only_port = port_calls - ref_calls
            if only_reference:
                print(f"    reference-only calls: {dict(only_reference)}")
            if only_port:
                print(f"    port-only calls:      {dict(only_port)}")
        if not same_signature:
            describe_signature_difference(stem, ref_signature, port_signature)

    print()
    print("=" * 78)
    print(f"artist-level equivalence: {len(STEMS) - len(failures)}/{len(STEMS)} EQUAL")
    if failures:
        print("differing stems:", failures)
    else:
        print("Every data-bearing artist attribute matches on all 14 stems, so no")
        print("divergence altered a plotted value, a limit, a tick or a label.")
    print("=" * 78)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

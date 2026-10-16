"""Attribute every EXP-002 H3 figure divergence by controlled substitution.

EXP-002 E3 found 18 of 39 publication files different between the frozen
PRINet 3.0 generators and PRIN's ``tools.reproduce.run_reproduction``: the
``.pdf`` and ``.png`` of nine figures. This generator establishes why.

For each of the 14 registered figure stems it renders:

* **R**, the frozen reference function, unmodified;
* **P**, PRIN's port of that function, from the build ``import prin`` resolves;
* **A**, the reference with *every* registered divergence D applied at once;
* **R_d**, the reference with exactly one divergence ``d`` applied.

A divergence is one concrete difference between the reference's drawing
calls and the pre-correction port: a keyword argument the port dropped, a
label string it re-encoded, a call it omitted. It is applied to the frozen
reference without editing or re-executing its source. While one stem
renders, the named ``matplotlib.axes.Axes`` method is wrapped, and the
wrapper transforms only calls whose immediate caller is the reference module.
Matplotlib's internal calls pass through untouched. Every transform asserts
that the argument it changes is present, and every divergence must fire at
least once. A specification that does not match the reference source
therefore fails loudly instead of yielding a vacuous result.

All comparisons use the registered H3 rule,
``benchmarks.campaign.exp002_driver.normalized_bytes``. The claims are:

* **completeness:** ``A == P`` in both formats for every stem, so D explains
  the entire byte difference and nothing outside D, such as plotted data,
  differs;
* **materiality:** ``R_d != R`` marks ``d`` as byte-material, per format;
* **reproduction:** the in-process R and P reproduce E3's committed digests,
  and the retained E3 bytes still match their manifested run records;
* **post-fix:** ``P == R`` on every stem. The other 21 files remain
  raw-byte-identical to E3, and two separate PRIN processes still agree on
  every raw byte (H4).

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s1/root_cause_decomposition.py --label prefix \
        --out EVIDENCE/exp002-d1-s1/root-cause-decomposition-prefix.json

The label is derived from the imported build (``prefix`` if any stem differs
from the reference, else ``postfix``). A run whose ``--label`` does not match
exits non-zero and writes nothing.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import platform
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.axes  # noqa: E402
import numpy as np  # noqa: E402
import PIL  # noqa: E402
import prin.reporting.figure_generation as port  # noqa: E402
import prinet.utils.figure_generation as reference  # noqa: E402
from PIL import Image  # noqa: E402

from benchmarks.campaign import exp002_driver as driver  # noqa: E402
from tools.reproduce import run_reproduction, verify_manifest  # noqa: E402

RESULTS = driver.REFERENCE / "benchmarks" / "results"
RETAINED = driver.OUTPUT_ROOT
E3_RUNS = {
    "reference": "RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu",
    "prin": "RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu",
    "seedrep0": "RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu",
}

#: Registered figure stem -> generator function name (same in both modules).
STEMS = {
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
FORMATS = ("pdf", "png")

Args = tuple[Any, ...]
Kwargs = dict[str, Any]
Transform = Callable[[Args, Kwargs], tuple[Args, Kwargs] | None]


@dataclass(frozen=True)
class Divergence:
    """One registered difference between the reference and the pre-fix port.

    ``transform`` maps a reference call's ``(args, kwargs)`` to the port's, or
    returns ``None`` when the port omits the call. ``calls`` restricts it to
    those 0-based indices among the stem's direct reference calls to
    ``method``, and ``None`` means every call.
    """

    id: str
    stem: str
    method: str
    reference: str
    port: str
    transform: Transform
    calls: frozenset[int] | None = None


def _drop(key: str) -> Transform:
    def transform(args: Args, kwargs: Kwargs) -> tuple[Args, Kwargs]:
        if key not in kwargs:
            raise AssertionError(f"reference call lacks {key}=")
        changed = dict(kwargs)
        del changed[key]
        return args, changed

    return transform


def _omit(args: Args, kwargs: Kwargs) -> None:
    return None


def _replace_arg(index: int, old: str, new: str) -> Transform:
    def transform(args: Args, kwargs: Kwargs) -> tuple[Args, Kwargs]:
        value = args[index]
        if not isinstance(value, str) or old not in value:
            raise AssertionError(f"reference argument {index} lacks {old!r}")
        return (*args[:index], value.replace(old, new), *args[index + 1 :]), kwargs

    return transform


def _set_arg(index: int, old: object, new: object) -> Transform:
    def transform(args: Args, kwargs: Kwargs) -> tuple[Args, Kwargs]:
        if args[index] != old:
            raise AssertionError(f"reference argument {index} is {args[index]!r}")
        return (*args[:index], new, *args[index + 1 :]), kwargs

    return transform


TIMES = "\N{MULTIPLICATION SIGN}"
REFERENCE_BANDS = [
    "\N{GREEK SMALL LETTER DELTA} (1\N{EN DASH}4 Hz)",
    "\N{GREEK SMALL LETTER THETA} (4\N{EN DASH}8 Hz)",
    "\N{GREEK SMALL LETTER GAMMA} (25\N{EN DASH}100 Hz)",
]
PORT_BANDS = [r"$\delta$ (1--4 Hz)", r"$\theta$ (4--8 Hz)", r"$\gamma$ (25--100 Hz)"]
FLOPS_LABEL = "FLOPs (\N{MULTIPLICATION SIGN}10\N{SUPERSCRIPT THREE})"
FLOPS_MATHTEXT = r"FLOPs ($\times 10^3$)"
SPEED_LABEL = "Speed Multiplier (\N{MULTIPLICATION SIGN})"
SPEED_MATHTEXT = r"Speed Multiplier ($\times$)"
GREEK = "/".join(
    (
        "\N{GREEK SMALL LETTER DELTA}",
        "\N{GREEK SMALL LETTER THETA}",
        "\N{GREEK SMALL LETTER GAMMA}",
    )
)

DIVERGENCES = (
    Divergence("D5.1", "fig5_mot_occlusion_comparison", "errorbar",
               "linewidth=1.5", "omitted", _drop("linewidth")),
    Divergence("D5.2", "fig5_mot_occlusion_comparison", "errorbar",
               "markersize=4", "omitted (rc lines.markersize=5)", _drop("markersize")),
    Divergence("D5.3", "fig5_mot_occlusion_comparison", "plot",
               "linewidth=1.5", "omitted", _drop("linewidth")),
    Divergence("D5.4", "fig5_mot_occlusion_comparison", "plot",
               "markersize=4", "omitted (rc lines.markersize=5)", _drop("markersize")),
    Divergence("D7.1", "fig7_ablation_results", "text",
               'va="bottom" on the accuracy labels', "omitted (baseline)", _drop("va")),
    Divergence("D8.1", "fig8_parameter_efficiency", "scatter",
               "zorder=5", "omitted (collection default 1, under the grid)",
               _drop("zorder")),
    Divergence("D9.1", "fig9_training_curves", "plot",
               "linewidth=1.2 on all four loss curves",
               "omitted (rc lines.linewidth=1.5)", _drop("linewidth")),
    Divergence("D9.2", "fig9_training_curves", "legend",
               'loc="upper right"', 'omitted ("best")', _drop("loc")),
    Divergence("D9.3", "fig9_training_curves", "text",
               'va="bottom" on the IP labels', "omitted (baseline)", _drop("va")),
    Divergence("D10.1", "fig10_statistical_summary", "annotate",
               'bbox=round,pad=0.3 lightyellow/gray on the outcome note',
               "omitted", _drop("bbox")),
    Divergence("D11.1", "fig11_flops_scaling", "bar",
               'edgecolor="black"', "omitted", _drop("edgecolor")),
    Divergence("D11.2", "fig11_flops_scaling", "bar",
               "linewidth=0.5", "omitted", _drop("linewidth")),
    Divergence("D11.3", "fig11_flops_scaling", "set_ylabel",
               f"{FLOPS_LABEL!r} (Unicode)", f"{FLOPS_MATHTEXT!r} (mathtext)",
               _set_arg(0, FLOPS_LABEL, FLOPS_MATHTEXT)),
    Divergence("D11.4", "fig11_flops_scaling", "legend",
               "framealpha=0.8", "omitted (rc legend.framealpha=0.8)",
               _drop("framealpha")),
    Divergence("D11.5", "fig11_flops_scaling", "annotate",
               f"ratio label 'N{TIMES}' (Unicode)", r"'N$\times$' (mathtext)",
               _replace_arg(0, TIMES, r"$\times$")),
    Divergence("D11.6", "fig11_flops_scaling", "annotate",
               'va="bottom" on the ratio labels', "omitted (baseline)", _drop("va")),
    Divergence("D12.1", "fig12_supercritical_regime", "bar",
               "linewidth=0.5", "omitted (rc patch.linewidth=1.0)",
               _drop("linewidth")),
    Divergence("D12.2", "fig12_supercritical_regime", "set_xticklabels",
               f"band labels in Unicode ({GREEK}, en dash)",
               r"mathtext ($\delta$ ..., '--')",
               _set_arg(0, REFERENCE_BANDS, PORT_BANDS)),
    Divergence("D12.3", "fig12_supercritical_regime", "axhline",
               "linewidth=0.8", "omitted", _drop("linewidth")),
    Divergence("D12.4", "fig12_supercritical_regime", "axhline",
               "alpha=0.7", "omitted", _drop("alpha")),
    Divergence("D12.5", "fig12_supercritical_regime", "plot",
               "markersize=5", "omitted (rc lines.markersize=5)", _drop("markersize")),
    Divergence("D12.6", "fig12_supercritical_regime", "plot",
               "linewidth=1.2", "omitted (rc lines.linewidth=1.5)", _drop("linewidth")),
    Divergence("D12.7", "fig12_supercritical_regime", "plot",
               r'label="$\lambda$ (convergence)"', "omitted (no legend is drawn)",
               _drop("label")),
    Divergence("D12.8", "fig12_supercritical_regime", "tick_params",
               'tick_params(axis="y", labelcolor="#AA3377") on the twin axis',
               "call omitted", _omit),
    Divergence("D12.9", "fig12_supercritical_regime", "text",
               f"ratio label 'N{TIMES}' (Unicode)", r"'N$\times$' (mathtext)",
               _replace_arg(2, TIMES, r"$\times$")),
    Divergence("D12.10", "fig12_supercritical_regime", "text",
               'va="bottom" on the ratio labels', "omitted (baseline)", _drop("va")),
    Divergence("D14.1", "fig14_gradient_flow", "barh",
               "alpha=0.85", "omitted", _drop("alpha")),
    Divergence("D15.1", "fig15_noise_velocity", "plot",
               "markersize=3 on the noise PT/SA lines", "omitted (rc 5)",
               _drop("markersize"), frozenset({0, 1})),
    Divergence("D15.2", "fig15_noise_velocity", "plot",
               "alpha=0.5 on the exponential fit", "omitted", _drop("alpha"),
               frozenset({2})),
    Divergence("D15.3", "fig15_noise_velocity", "plot",
               "linewidth=1 on the exponential fit", "omitted (rc 1.5)",
               _drop("linewidth"), frozenset({2})),
    Divergence("D15.4", "fig15_noise_velocity", "legend",
               'loc="lower left" on the noise panel', 'omitted ("best")',
               _drop("loc"), frozenset({0})),
    Divergence("D15.5", "fig15_noise_velocity", "plot",
               "markersize=4 on the velocity PT/SA lines", "omitted (rc 5)",
               _drop("markersize"), frozenset({3, 4})),
    Divergence("D15.6", "fig15_noise_velocity", "set_xlabel",
               f"{SPEED_LABEL!r} (Unicode)", f"{SPEED_MATHTEXT!r} (mathtext)",
               _set_arg(0, SPEED_LABEL, SPEED_MATHTEXT),
               frozenset({1})),
    Divergence("D15.7", "fig15_noise_velocity", "legend",
               'loc="lower left" on the velocity panel', 'omitted ("best")',
               _drop("loc"), frozenset({1})),
)  # fmt: skip


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _id_key(divergence_id: str) -> tuple[int, int]:
    figure, item = divergence_id[1:].split(".")
    return int(figure), int(item)


@contextlib.contextmanager
def _substituted(divergences: tuple[Divergence, ...]) -> Iterator[dict[str, int]]:
    """Apply ``divergences`` to direct reference calls; yield fire counts."""
    fired = {d.id: 0 for d in divergences}
    originals: dict[str, Any] = {}
    for method in sorted({d.method for d in divergences}):
        original = getattr(matplotlib.axes.Axes, method)
        originals[method] = original
        counter = [0]
        selected = tuple(d for d in divergences if d.method == method)

        def wrapper(
            self: Any,
            *args: Any,
            _original: Any = original,
            _counter: list[int] = counter,
            _selected: tuple[Divergence, ...] = selected,
            **kwargs: Any,
        ) -> Any:
            caller = sys._getframe(1).f_globals.get("__name__")
            if caller != reference.__name__:
                return _original(self, *args, **kwargs)
            index = _counter[0]
            _counter[0] += 1
            for divergence in _selected:
                if divergence.calls is not None and index not in divergence.calls:
                    continue
                result = divergence.transform(args, kwargs)
                fired[divergence.id] += 1
                if result is None:
                    return None
                args, kwargs = result
            return _original(self, *args, **kwargs)

        setattr(matplotlib.axes.Axes, method, wrapper)
    try:
        yield fired
    finally:
        for method, original in originals.items():
            setattr(matplotlib.axes.Axes, method, original)


def _render(module: Any, stem: str, directory: Path) -> dict[str, bytes]:
    directory.mkdir(parents=True)
    with contextlib.redirect_stdout(io.StringIO()):
        paths = getattr(module, STEMS[stem])(results_dir=RESULTS, output_dir=directory)
    rendered = {Path(path).suffix[1:]: Path(path).read_bytes() for path in paths}
    if sorted(rendered) != sorted(FORMATS) or any(
        Path(path).name != f"{stem}.{Path(path).suffix[1:]}" for path in paths
    ):
        raise SystemExit(f"{stem}: unexpected outputs {paths}")
    return rendered


def _normalized(rendered: dict[str, bytes]) -> dict[str, str]:
    return {
        fmt: _sha256(driver.normalized_bytes(payload, f".{fmt}"))
        for fmt, payload in rendered.items()
    }


def _png_pixels_differing(left: bytes, right: bytes) -> int | str:
    a = np.asarray(Image.open(io.BytesIO(left)).convert("RGBA"))
    b = np.asarray(Image.open(io.BytesIO(right)).convert("RGBA"))
    if a.shape != b.shape:
        return f"shape {a.shape} vs {b.shape}"
    return int(np.any(a != b, axis=-1).sum())


def _e3_files(run: str) -> dict[str, dict[str, Any]]:
    payload = (driver.RAW_ROOT / run / "reproduction.json").read_text("utf-8")
    record = json.loads(payload)
    return {item["path"]: item for item in record["observations"]["files"]}


def _verify_e3_records() -> dict[str, Any]:
    """Check the committed run records and the retained untracked bytes."""
    report: dict[str, Any] = {}
    for leg, run in E3_RUNS.items():
        run_dir = driver.RAW_ROOT / run
        manifest = json.loads((run_dir / "manifest.json").read_text("utf-8"))
        entry = next(f for f in manifest["files"] if f["path"] == "reproduction.json")
        record_ok = (
            _sha256((run_dir / "reproduction.json").read_bytes()) == (entry["sha256"])
        )
        retained = RETAINED / run / "publication"
        files = _e3_files(run)
        raw_ok = norm_ok = 0
        for name, item in files.items():
            payload = (retained / name).read_bytes() if retained.is_dir() else b""
            raw_ok += _sha256(payload) == item["raw_sha256"]
            if payload:
                normalized = driver.normalized_bytes(payload, Path(name).suffix)
                norm_ok += _sha256(normalized) == item["normalized_sha256"]
        report[leg] = {
            "run": run,
            "reproduction_json_matches_manifest": record_ok,
            "retained_root_present": retained.is_dir(),
            "retained_files": len(files),
            "retained_raw_sha256_matching_record": raw_ok,
            "retained_normalized_sha256_matching_record": norm_ok,
        }
    reference, prin = _e3_files(E3_RUNS["reference"]), _e3_files(E3_RUNS["prin"])
    report["e3_normalized_differing_files"] = sorted(
        name
        for name in reference
        if reference[name]["normalized_sha256"] != prin[name]["normalized_sha256"]
    )
    return report


def _render_prin_tree(directory: Path) -> dict[str, str]:
    run_reproduction(
        results_dir=RESULTS,
        output_dir=directory,
        manifest_path=driver.INPUT_MANIFEST,
        verify=True,
    )
    return {
        path.relative_to(directory).as_posix(): _sha256(path.read_bytes())
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603  # nosec B603 B607
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def decompose(
    work: Path, prefix_port: dict[str, dict[str, str]] | None = None
) -> dict[str, Any]:
    """Run the full decomposition in ``work`` and return the artefact payload.

    ``prefix_port`` maps each stem to the pre-fix port's normalized digests
    from the committed prefix artefact. A post-fix run passes it, so A is
    compared against the measured pre-fix port rather than the live, fixed one.
    """
    verify_manifest(RESULTS, driver.INPUT_MANIFEST)
    e3_reference = _e3_files(E3_RUNS["reference"])
    e3_prin = _e3_files(E3_RUNS["prin"])
    stems: dict[str, Any] = {}
    for stem in STEMS:
        base = work / stem
        r = _render(reference, stem, base / "R")
        p = _render(port, stem, base / "P")
        own = tuple(d for d in DIVERGENCES if d.stem == stem)
        entry: dict[str, Any] = {
            "reference_normalized_sha256": _normalized(r),
            "port_normalized_sha256": _normalized(p),
            "port_equals_reference": {
                fmt: _normalized(r)[fmt] == _normalized(p)[fmt] for fmt in FORMATS
            },
            "png_pixels_differing_port_vs_reference": _png_pixels_differing(
                p["png"], r["png"]
            ),
            "reference_reproduces_e3_reference_arm": {
                fmt: _normalized(r)[fmt]
                == e3_reference[f"figures/{stem}.{fmt}"]["normalized_sha256"]
                for fmt in FORMATS
            },
            "port_raw_equals_e3_prin_arm": {
                fmt: _sha256(p[fmt]) == e3_prin[f"figures/{stem}.{fmt}"]["raw_sha256"]
                for fmt in FORMATS
            },
            "divergences": [],
        }
        if own:
            with _substituted(own) as fired:
                a = _render(reference, stem, base / "A")
            if any(count == 0 for count in fired.values()):
                raise SystemExit(f"{stem}: a divergence never fired: {fired}")
            target = _normalized(p) if prefix_port is None else prefix_port[stem]
            entry["all_divergences_applied_equals_prefix_port"] = {
                fmt: _normalized(a)[fmt] == target[fmt] for fmt in FORMATS
            }
            entry["all_divergences_applied_normalized_sha256"] = _normalized(a)
            for divergence in own:
                with _substituted((divergence,)) as fired:
                    single = _render(reference, stem, base / divergence.id)
                entry["divergences"].append(
                    {
                        "id": divergence.id,
                        "method": f"Axes.{divergence.method}",
                        "reference": divergence.reference,
                        "pre_fix_port": divergence.port,
                        "calls_transformed": fired[divergence.id],
                        "material": {
                            fmt: _normalized(single)[fmt] != _normalized(r)[fmt]
                            for fmt in FORMATS
                        },
                    }
                )
        stems[stem] = entry
    first = _render_prin_tree(work / "prin-in-process")
    child = work / "prin-child-process"
    subprocess.run(  # noqa: S603  # nosec B603
        [sys.executable, str(Path(__file__).resolve()), "--render-prin", str(child)],
        check=True,
        cwd=ROOT,
    )
    second = {
        path.relative_to(child).as_posix(): _sha256(path.read_bytes())
        for path in sorted(child.rglob("*"))
        if path.is_file()
    }
    e3_raw = {name: item["raw_sha256"] for name, item in e3_prin.items()}
    return {
        "stems": stems,
        "prin_tree": {
            "files": len(first),
            "two_process_raw_identical": first == second,
            "raw_equal_to_e3_prin_arm": sorted(
                name for name in first if first[name] == e3_raw.get(name)
            ),
            "raw_differing_from_e3_prin_arm": sorted(
                name for name in first if first[name] != e3_raw.get(name)
            ),
        },
        "e3_records": _verify_e3_records(),
    }


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    stems = payload["stems"]
    differing = sorted(
        f"figures/{stem}.{fmt}"
        for stem, entry in stems.items()
        for fmt in FORMATS
        if not entry["port_equals_reference"][fmt]
    )
    complete = all(
        all(entry.get("all_divergences_applied_equals_prefix_port", {}).values())
        for entry in stems.values()
        if entry["divergences"]
    )
    divergences = [d for entry in stems.values() for d in entry["divergences"]]
    material = sorted(
        (d["id"] for d in divergences if any(d["material"].values())), key=_id_key
    )
    immaterial = sorted(
        (d["id"] for d in divergences if not any(d["material"].values())),
        key=_id_key,
    )
    unexplained = sorted(
        stem
        for stem, entry in stems.items()
        if not all(entry["port_equals_reference"].values())
        and not (
            entry["divergences"]
            and all(entry["all_divergences_applied_equals_prefix_port"].values())
        )
    )
    return {
        "port_vs_reference_differing_files": differing,
        "port_vs_reference_differing_count": len(differing),
        "divergences_registered": len(DIVERGENCES),
        "divergences_byte_material": material,
        "divergences_byte_immaterial": immaterial,
        "completeness_all_applied_equals_prefix_port": complete,
        "unexplained_stems": unexplained,
        "reference_reproduces_e3_reference_arm_all": all(
            all(entry["reference_reproduces_e3_reference_arm"].values())
            for entry in stems.values()
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Attribute every EXP-002 H3 figure divergence."
    )
    parser.add_argument("--label", choices=("prefix", "postfix"))
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--prefix",
        type=Path,
        default=Path(__file__).resolve().parent
        / "root-cause-decomposition-prefix.json",
        help="committed prefix artefact (postfix runs compare A against it)",
    )
    parser.add_argument("--render-prin", type=Path, help=argparse.SUPPRESS)
    options = parser.parse_args(argv)
    if options.render_prin is not None:
        _render_prin_tree(options.render_prin)
        return 0
    if options.label is None or options.out is None:
        parser.error("--label and --out are required")
    prefix_port = None
    if options.label == "postfix":
        prefix = json.loads(options.prefix.read_text("utf-8"))
        if prefix["label"] != "prefix":
            parser.error(f"{options.prefix} is not a prefix artefact")
        prefix_port = {
            stem: entry["port_normalized_sha256"]
            for stem, entry in prefix["stems"].items()
        }
    with tempfile.TemporaryDirectory(prefix="prin-exp002-d1-") as directory:
        payload = decompose(Path(directory), prefix_port)
    summary = _summary(payload)
    derived = "prefix" if summary["port_vs_reference_differing_count"] else "postfix"
    if derived != options.label:
        print(f"label {options.label!r} does not match the imported build ({derived})")
        return 2
    artefact = {
        "label": options.label,
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_head": _git("rev-parse", "HEAD"),
        "git_tracked_changes": _git("status", "--porcelain", "--untracked-files=no"),
        "port_module": str(Path(str(port.__file__)).resolve().relative_to(ROOT)),
        "port_module_sha256": _sha256(Path(str(port.__file__)).read_bytes()),
        "reference_module_sha256": _sha256(Path(str(reference.__file__)).read_bytes()),
        "reference_module_pin": driver.REFERENCE_PINS[
            "src/prinet/utils/figure_generation.py"
        ],
        "comparison": "benchmarks.campaign.exp002_driver.normalized_bytes",
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pillow": PIL.__version__,
            "renderer": driver._render_environment(),
        },
        "summary": summary,
        **payload,
    }
    options.out.write_text(
        json.dumps(artefact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

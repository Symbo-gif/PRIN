"""WP-030 S1 MOT parity fixture: golden `motmetrics` output for fixed sequences.

Defines a set of deterministic object-id / hypothesis-id / distance-matrix
sequences engineered to exercise CLEAR-MOT/IDF1 identity edge cases (clean
matches, misses, false positives, an identity switch, an occlusion
reappearance that must *not* count as a switch, a `max_switch_time` boundary,
rectangular per-frame shapes, an empty frame, an all-forbidden-pairing frame,
and an IoU-bbox-derived distance matrix), replays each through the real
``motmetrics`` package (the reference this WP is validated against — Project
Plan §6, "MOT metrics match motmetrics reference"), and writes the inputs
plus ``motmetrics``'s own MOTA/MOTP/IDF1/switch/FP/miss output to a JSON
fixture.

``crates/prin-daemon/tests/parity_mot.rs`` replays the same inputs through
``prin_daemon::mot::MotAccumulator`` and asserts its summary matches the
recorded ``motmetrics`` output within tight tolerance.

Requires the ``mot`` extra (``pip install -e ".[mot]"``): ``motmetrics`` and
its ``pandas`` dependency are not part of the default install.

Usage:
    python tools/wp030_mot_fixture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import motmetrics as mm

_DEFAULT_OUTPUT = (
    Path("crates") / "prin-daemon" / "tests" / "data" / "mot_reference_cases.json"
)

_METRICS = ["mota", "motp", "idf1", "num_switches", "num_false_positives", "num_misses"]

# A `dists` row uses `None` for a forbidden (do-not-pair) entry; converted to
# `float("nan")` before being handed to `motmetrics`, and to `f64::NAN` on the
# Rust side of the fixture consumer.
Frame = tuple[list[int], list[int], list[list[float | None]]]
Scenario = tuple[str, int | None, list[Frame]]


def _json_safe_float(value: float) -> Any:
    """Tag a non-finite float for strict-JSON round-tripping.

    Returns the value unchanged when finite; otherwise one of the strings
    `"NaN"`, `"Infinity"`, `"-Infinity"`, which the Rust fixture consumer
    maps back to the corresponding `f64` constant.
    """
    if value != value:  # NaN is the only value unequal to itself.
        return "NaN"
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    return value


def _to_nan_matrix(dists: list[list[float | None]]) -> list[list[float]]:
    """Replace `None` entries with `float("nan")` for `motmetrics` consumption."""
    return [[float("nan") if v is None else v for v in row] for row in dists]


def _run_scenario(
    name: str, max_switch_time: int | None, frames: list[Frame]
) -> dict[str, Any]:
    """Replay one scenario through a real `motmetrics.MOTAccumulator`.

    Args:
        name: Scenario identifier, carried into the fixture for the Rust
            consumer's test names/error messages.
        max_switch_time: Forwarded to `MOTAccumulator`, or `None` for the
            reference's `float("inf")` default.
        frames: Per-frame `(oids, hids, dists)` triples, in order.

    Returns:
        A JSON-serialisable record: the scenario name, `max_switch_time`,
        the input frames (with `None` for forbidden pairings), and the
        `motmetrics`-computed summary metrics.
    """
    kwargs: dict[str, Any] = {"auto_id": True}
    if max_switch_time is not None:
        kwargs["max_switch_time"] = float(max_switch_time)
    acc = mm.MOTAccumulator(**kwargs)

    for oids, hids, dists in frames:
        acc.update(oids, hids, _to_nan_matrix(dists))

    host = mm.metrics.create()
    summary = host.compute(acc, metrics=_METRICS, name=name)

    expected: dict[str, Any] = {
        metric: float(summary[metric].iloc[0]) for metric in _METRICS
    }
    # Switch/FP/miss counts are integral; round-trip through float() above
    # for a uniform JSON number type, then back to int for the ones that are
    # conceptually counts.
    for count_metric in ("num_switches", "num_false_positives", "num_misses"):
        expected[count_metric] = int(expected[count_metric])
    # `json.dumps` emits bare `NaN`/`Infinity` tokens for non-finite floats
    # (valid Python, not valid JSON — `serde_json` on the Rust consumer side
    # rejects them), e.g. MOTP is `0 / 0` whenever a scenario has zero
    # matches. Encode those as tagged strings instead.
    for metric in ("mota", "motp", "idf1"):
        expected[metric] = _json_safe_float(expected[metric])

    return {
        "name": name,
        "max_switch_time": max_switch_time,
        "frames": [
            {"oids": oids, "hids": hids, "dists": dists} for oids, hids, dists in frames
        ],
        "expected": expected,
    }


def _scenarios() -> list[dict[str, Any]]:
    """Build and run every scenario, returning their fixture records."""
    nan = None  # local alias to keep the literal tables below readable

    perfect_tracking: list[Frame] = [
        ([1, 2, 3], [1, 2, 3], [[0.1, nan, nan], [nan, 0.1, nan], [nan, nan, 0.1]])
        for _ in range(5)
    ]

    with_misses: list[Frame] = [
        ([1, 2], [1, 2], [[0.1, nan], [nan, 0.1]]),
        ([1, 2], [1], [[0.1], [nan]]),  # object 2 unmatched this frame
        ([1, 2], [1, 2], [[0.1, nan], [nan, 0.1]]),
    ]

    with_false_positives: list[Frame] = [
        ([1], [1, 99], [[0.1, nan]]),
        ([1], [1, 99], [[0.1, nan]]),
        ([1], [1, 99], [[0.1, nan]]),
    ]

    with_identity_switch: list[Frame] = [
        ([1, 2], [1, 2], [[0.1, nan], [nan, 0.1]]),
        # Forced swap: the previous pairing is no longer a valid pair.
        ([1, 2], [1, 2], [[nan, 0.1], [0.1, nan]]),
    ]

    occlusion_reappearance_same_id: list[Frame] = [
        ([1], [1], [[0.1]]),
        ([], [], []),
        ([], [], []),
        ([1], [1], [[0.1]]),
    ]

    max_switch_time_bounded_frames: list[Frame] = [
        ([1, 2], [1, 2], [[0.1, nan], [nan, 0.1]]),
        ([], [], []),
        ([], [], []),
        ([1, 2], [1, 2], [[nan, 0.1], [0.1, nan]]),
    ]

    rectangular_stress: list[Frame] = [
        (
            [1, 2, 3, 4, 5],
            [1, 2],
            [[0.1, nan], [nan, 0.1], [nan, nan], [nan, nan], [nan, nan]],
        ),
        (
            [1, 2],
            [1, 2, 3, 4, 5],
            [[0.1, nan, nan, nan, nan], [nan, 0.1, nan, nan, nan]],
        ),
    ]

    empty_frame: list[Frame] = [
        ([1], [1], [[0.1]]),
        ([], [], []),
        ([1], [1], [[0.1]]),
    ]

    all_forbidden_frame: list[Frame] = [
        ([1], [99], [[nan]]),
        ([1], [99], [[nan]]),
    ]

    iou_based: list[Frame] = _iou_based_frames()

    scenarios: list[Scenario] = [
        ("perfect_tracking", None, perfect_tracking),
        ("with_misses", None, with_misses),
        ("with_false_positives", None, with_false_positives),
        ("with_identity_switch", None, with_identity_switch),
        ("occlusion_reappearance_same_id", None, occlusion_reappearance_same_id),
        ("max_switch_time_bounded", 1, max_switch_time_bounded_frames),
        ("rectangular_stress", None, rectangular_stress),
        ("empty_frame", None, empty_frame),
        ("all_forbidden_frame", None, all_forbidden_frame),
        ("iou_based", None, iou_based),
    ]

    return [
        _run_scenario(name, max_switch_time, frames)
        for name, max_switch_time, frames in scenarios
    ]


def _box_iou(a: list[float], b: list[float]) -> float:
    """`(x, y, w, h)` intersection-over-union, per `motmetrics.distances.boxiou`.

    Reimplemented locally rather than calling `motmetrics.distances.iou_matrix`
    directly: that function calls the NumPy 1.x-only `np.asfarray`, removed in
    NumPy 2.0 (installed here as 2.5.1), so it raises `AttributeError` in this
    environment — a `motmetrics`/NumPy-2.0 incompatibility, not a defect in
    `MOTAccumulator` (the thing this fixture validates). The formula below is
    transcribed from `distances.boxiou`/`distances.rect_min_max` verbatim; only
    the NumPy vectorisation is replaced with plain Python for a handful of
    boxes, which cannot itself introduce a numerical discrepancy.
    """
    a_min_x, a_min_y, a_w, a_h = a
    b_min_x, b_min_y, b_w, b_h = b
    a_max_x, a_max_y = a_min_x + a_w, a_min_y + a_h
    b_max_x, b_max_y = b_min_x + b_w, b_min_y + b_h

    i_w = max(min(a_max_x, b_max_x) - max(a_min_x, b_min_x), 0.0)
    i_h = max(min(a_max_y, b_max_y) - max(a_min_y, b_min_y), 0.0)
    i_vol = i_w * i_h
    if i_vol == 0.0:
        return 0.0

    a_vol = max(a_w, 0.0) * max(a_h, 0.0)
    b_vol = max(b_w, 0.0) * max(b_h, 0.0)
    return i_vol / (a_vol + b_vol - i_vol)


def _iou_based_frames() -> list[Frame]:
    """Two frames of `(x, y, w, h)` boxes reduced to an IoU distance matrix.

    Exercises the same IoU-distance path `prin_daemon::mot::iou_distance_matrix`
    implements, at `max_iou_distance=0.5` (see `_box_iou`'s docstring for why
    this recomputes the reference formula locally instead of calling
    `motmetrics.distances.iou_matrix`).
    """
    max_iou_distance = 0.5
    frame0_objs = [[0.0, 0.0, 1.0, 1.0], [5.0, 5.0, 1.0, 1.0]]
    frame0_hyps = [[0.05, 0.05, 1.0, 1.0], [5.1, 5.1, 1.0, 1.0]]
    frame1_objs = [[0.0, 0.0, 1.0, 1.0], [5.0, 5.0, 1.0, 1.0]]
    frame1_hyps = [[0.1, 0.0, 1.0, 1.0], [9.0, 9.0, 1.0, 1.0]]  # hyp 2 drifts far away

    def _matrix(
        objs: list[list[float]], hyps: list[list[float]]
    ) -> list[list[float | None]]:
        """Reduce two box lists to an `objs x hyps` IoU distance matrix."""
        result: list[list[float | None]] = []
        for obj in objs:
            row: list[float | None] = []
            for hyp in hyps:
                dist = 1.0 - _box_iou(obj, hyp)
                row.append(None if dist > max_iou_distance else dist)
            result.append(row)
        return result

    return [
        ([1, 2], [1, 2], _matrix(frame0_objs, frame0_hyps)),
        ([1, 2], [1, 2], _matrix(frame1_objs, frame1_hyps)),
    ]


def main(argv: list[str] | None = None) -> int:
    """Generate the fixture and write it to disk.

    Args:
        argv: Optional output-path override as a single positional argument
            (defaults to the committed fixture path under
            `crates/prin-daemon/tests/data/`).

    Returns:
        Process exit code (always `0`; any `motmetrics` failure raises).
    """
    args = argv if argv is not None else sys.argv[1:]
    output = Path(args[0]) if args else _DEFAULT_OUTPUT

    fixture = {"schema": "wp030-mot-reference-cases-v1", "scenarios": _scenarios()}

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(fixture['scenarios'])} scenarios to: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Regression coverage for the fail-closed nightly benchmark comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import check_bench_regression as gate


def _criterion(root: Path, name: str, mean: object) -> None:
    path = root / name / "new" / "estimates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"mean": {"point_estimate": mean}}), encoding="utf-8")


def _pytest(path: Path, mean: object = 100.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "benchmarks": [
                    {
                        "fullname": "tests/test_bridge.py::test_latency",
                        "stats": {"mean": mean},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _pair(tmp_path: Path, candidate: float = 100.0) -> list[str]:
    for arm, mean in (("reference", 100.0), ("candidate", candidate)):
        _criterion(tmp_path / arm / "criterion", "group/case", mean)
        _pytest(tmp_path / arm / "pytest-bench.json", mean)
    return [
        "--reference",
        str(tmp_path / "reference"),
        "--candidate",
        str(tmp_path / "candidate"),
    ]


def _run(root: Path, criterion: dict[str, float], pytest_mean: float) -> Path:
    """Write one complete measurement run and return its directory."""
    for name, mean in criterion.items():
        _criterion(root / "criterion", name, mean)
    _pytest(root / "pytest-bench.json", pytest_mean)
    return root


@pytest.mark.parametrize(
    ("mean", "expected"), [(90.0, 0), (100.0, 0), (110.0, 0), (110.01, 1)]
)
def test_registered_ten_percent_boundary(
    tmp_path: Path, mean: float, expected: int
) -> None:
    assert gate.main(_pair(tmp_path, mean)) == expected


@pytest.mark.parametrize("arm", ["reference", "candidate"])
@pytest.mark.parametrize("source", ["criterion", "pytest"])
def test_missing_source_fails_closed(tmp_path: Path, arm: str, source: str) -> None:
    args = _pair(tmp_path)
    path = (
        tmp_path
        / arm
        / (
            "criterion/group/case/new/estimates.json"
            if source == "criterion"
            else "pytest-bench.json"
        )
    )
    path.unlink()
    assert gate.main(args) == 2


@pytest.mark.parametrize(
    "payload", ["{", "[]", '{"mean": {}}', '{"mean": {"point_estimate": true}}']
)
def test_malformed_criterion_fails_closed(tmp_path: Path, payload: str) -> None:
    args = _pair(tmp_path)
    path = tmp_path / "candidate/criterion/group/case/new/estimates.json"
    path.write_text(payload, encoding="utf-8")
    assert gate.main(args) == 2


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        "[]",
        "{}",
        '{"benchmarks": []}',
        '{"benchmarks": {}}',
        '{"benchmarks": [null]}',
        '{"benchmarks": [{"fullname": "x", "stats": {}}]}',
        '{"benchmarks": [{"fullname": "", "stats": {"mean": 1}}]}',
    ],
)
def test_malformed_pytest_fails_closed(tmp_path: Path, payload: str) -> None:
    args = _pair(tmp_path)
    (tmp_path / "candidate/pytest-bench.json").write_text(payload, encoding="utf-8")
    assert gate.main(args) == 2


@pytest.mark.parametrize(
    "value", [0, -1, float("nan"), float("inf"), float("-inf"), True, "100", None]
)
@pytest.mark.parametrize("source", ["criterion", "pytest"])
def test_invalid_mean_fails_closed(tmp_path: Path, value: object, source: str) -> None:
    args = _pair(tmp_path)
    if source == "criterion":
        _criterion(tmp_path / "candidate/criterion", "group/case", value)
    else:
        _pytest(tmp_path / "candidate/pytest-bench.json", value)
    assert gate.main(args) == 2


@pytest.mark.parametrize("arm", ["reference", "candidate"])
def test_unmatched_benchmark_fails_closed(tmp_path: Path, arm: str) -> None:
    args = _pair(tmp_path)
    _criterion(tmp_path / arm / "criterion", "extra", 100.0)
    assert gate.main(args) == 2


def test_duplicate_pytest_name_fails_closed(tmp_path: Path) -> None:
    args = _pair(tmp_path)
    path = tmp_path / "candidate/pytest-bench.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["benchmarks"] *= 2
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert gate.main(args) == 2


@pytest.mark.parametrize("threshold", ["nan", "inf", "-0.1"])
def test_invalid_threshold_fails_closed(tmp_path: Path, threshold: str) -> None:
    assert gate.main([*_pair(tmp_path), f"--threshold={threshold}"]) == 2


def test_pytest_only_regression_is_not_hidden(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _pair(tmp_path)
    _pytest(tmp_path / "candidate/pytest-bench.json", 120.0)
    assert gate.main(args) == 1
    assert "pytest/tests/test_bridge.py::test_latency" in capsys.readouterr().err


def test_criterion_only_regression_is_not_hidden(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _pair(tmp_path)
    _criterion(tmp_path / "candidate/criterion", "group/case", 120.0)
    assert gate.main(args) == 1
    assert "criterion/group/case" in capsys.readouterr().err


def test_pytest_name_fallback_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "pytest.json"
    path.write_text(
        json.dumps({"benchmarks": [{"name": "fallback", "stats": {"mean": 1}}]}),
        encoding="utf-8",
    )
    assert gate._load_pytest_means(path) == {"fallback": 1.0}


@pytest.mark.parametrize("value", [10**400])
def test_unrepresentable_mean_fails_closed(tmp_path: Path, value: object) -> None:
    args = _pair(tmp_path)
    _criterion(tmp_path / "candidate/criterion", "group/case", value)
    assert gate.main(args) == 2


def test_missing_stats_fails_closed(tmp_path: Path) -> None:
    args = _pair(tmp_path)
    (tmp_path / "candidate/pytest-bench.json").write_text(
        '{"benchmarks": [{"name": "case", "stats": null}]}', encoding="utf-8"
    )
    assert gate.main(args) == 2


def test_missing_mean_object_fails_closed(tmp_path: Path) -> None:
    args = _pair(tmp_path)
    (tmp_path / "candidate/criterion/group/case/new/estimates.json").write_text(
        "{}", encoding="utf-8"
    )
    assert gate.main(args) == 2


def test_nightly_uses_fresh_same_job_reference_and_preserves_gate() -> None:
    text = (
        Path(__file__).resolve().parents[1] / ".github/workflows/nightly.yml"
    ).read_text(encoding="utf-8")
    job = text.split("  bench-regression:\n", 1)[1]
    job_env = job.split("    env:\n", 1)[1].split("    steps:\n", 1)[0]
    assert "runner." not in job_env
    assert (
        "benchmarks/results/nightly-${{ github.run_id }}"
        "-${{ github.run_attempt }}" in job_env
    )
    assert "REFERENCE_SHA: 4590d611f34eae5dfcdadb99b562aacf998d6e94" in job
    # DV036-F4: equal-length sibling checkouts, never a nested reference.
    assert "path: arms/candidate" in job
    assert "path: arms/reference" in job
    assert "path: .nightly-reference" not in job
    assert ".nightly-reference/" not in job
    assert len("arms/candidate") == len("arms/reference")
    assert 'export CRITERION_HOME="$EVIDENCE_DIR/$run/criterion"' in job
    assert (
        'cmp "$EVIDENCE_DIR/dependencies.txt" '
        '"$EVIDENCE_DIR/reference-dependencies.txt"' in job
    )
    assert "--threshold 0.10" in job
    assert "uses: actions/cache@" not in job
    assert "Refresh baseline" not in job
    measure = job.split(
        "      - name: Measure reference and candidate in counterbalanced order", 1
    )[1].split("      - name: Compare against baseline", 1)[0]
    assert "set -euo pipefail" in measure
    assert "|| true" not in measure
    # DV036-F4: fixed ABBA order; every pass is kept, none is a retry.
    calls = [line.strip() for line in measure.splitlines() if "measure " in line]
    assert calls[-4:] == [
        "measure reference reference-1",
        "measure candidate candidate-1",
        "measure candidate candidate-2",
        "measure reference reference-2",
    ]
    compare = job.split("      - name: Compare against baseline", 1)[1]
    assert (
        '--reference "$EVIDENCE_DIR/reference-1" "$EVIDENCE_DIR/reference-2"' in compare
    )
    assert (
        '--candidate "$EVIDENCE_DIR/candidate-1" "$EVIDENCE_DIR/candidate-2"' in compare
    )
    # Only the registered contention group may be advisory (amendment 4).
    advisory = [
        line.split("--advisory", 1)[1].split()[0]
        for line in compare.splitlines()
        if "--advisory" in line
    ]
    assert advisory == ["criterion/control_buffer_read_under_contention/"]
    build = job.split(
        "      - name: Build matched candidate and reference environments", 1
    )[1].split(
        "      - name: Measure reference and candidate in counterbalanced order", 1
    )[0]
    # DV036-F3: --no-build-isolation editable installs spawn the `maturin`
    # CLI from the PEP 517 hook; each venv's bin/ must be on PATH first.
    candidate, reference = build.split("cd ../reference", 1)
    assert candidate.index("source .venv/bin/activate") < candidate.index(
        '-e ".[dev,onnx]"'
    )
    assert reference.index("source .venv/bin/activate") < reference.index("-e .")
    for name in (
        "control_buffer",
        "training_hooks",
        "mean_field_rk4_bench",
        "sparse_knn_bench",
        "discrete_step_bench",
        "sweep_bench",
        "resonance_layer_bridge",
        "phase_tracker_bridge",
    ):
        assert f"--bench {name}" in measure
    assert "--benchmark-only" in measure
    assert "uses: actions/upload-artifact@v4" in job
    assert "if: always()" in job


# DV036-F4: counterbalanced reference/candidate runs and hosted-advisory ids.


def _abba(tmp_path: Path, contention: tuple[float, float, float, float]) -> list[str]:
    """Four runs in ref, cand, cand, ref order; only the contention id varies."""
    dirs = []
    for label, noisy in zip(("r1", "c1", "c2", "r2"), contention, strict=True):
        dirs.append(
            _run(
                tmp_path / label,
                {"group/case": 100.0, "contention/mutex/4": noisy},
                100.0,
            )
        )
    r1, c1, c2, r2 = (str(d) for d in dirs)
    return ["--reference", r1, r2, "--candidate", c1, c2]


def test_arm_mean_averages_every_run(tmp_path: Path) -> None:
    # Reference runs 100 and 120 average to 110; candidate 121 is exactly
    # +10% of that mean, so the registered boundary passes...
    r1 = _run(tmp_path / "r1", {"group/case": 100.0}, 100.0)
    r2 = _run(tmp_path / "r2", {"group/case": 120.0}, 100.0)
    c1 = _run(tmp_path / "c1", {"group/case": 121.0}, 100.0)
    args = ["--reference", str(r1), str(r2), "--candidate", str(c1)]
    assert gate.main(args) == 0
    # ...and one hair above it fails, proving both reference runs count.
    _criterion(tmp_path / "c1" / "criterion", "group/case", 121.2)
    assert gate.main(args) == 1


def test_counterbalanced_order_cancels_linear_drift(tmp_path: Path) -> None:
    # Identical code on a host that slows 7% per run (the drift measured
    # locally for DV036-F4): ref-first single pass reads +7%, ABBA reads 0%.
    drift = (100.0, 107.0, 114.0, 121.0)
    r1 = _run(tmp_path / "r1", {"group/case": drift[0]}, 1.0)
    c1 = _run(tmp_path / "c1", {"group/case": drift[1]}, 1.0)
    c2 = _run(tmp_path / "c2", {"group/case": drift[2]}, 1.0)
    r2 = _run(tmp_path / "r2", {"group/case": drift[3]}, 1.0)
    reference = gate._load_arm_runs([r1, r2])
    candidate = gate._load_arm_runs([c1, c2])
    assert candidate["criterion/group/case"] == reference["criterion/group/case"]


def test_run_identity_mismatch_within_arm_fails_closed(tmp_path: Path) -> None:
    args = _abba(tmp_path, (100.0, 100.0, 100.0, 100.0))
    _criterion(tmp_path / "r2" / "criterion", "extra", 100.0)
    assert gate.main(args) == 2


def test_advisory_breach_is_reported_but_does_not_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _abba(tmp_path, (100.0, 160.0, 160.0, 100.0))
    assert gate.main(args) == 1
    assert gate.main([*args, "--advisory", "criterion/contention/"]) == 0
    out = capsys.readouterr()
    assert "ADVISORY" in out.out
    assert "criterion/contention/mutex/4" in out.out


def test_advisory_does_not_hide_gated_regression(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _abba(tmp_path, (100.0, 160.0, 160.0, 100.0))
    _criterion(tmp_path / "c1" / "criterion", "group/case", 130.0)
    _criterion(tmp_path / "c2" / "criterion", "group/case", 130.0)
    assert gate.main([*args, "--advisory", "criterion/contention/"]) == 1
    err = capsys.readouterr().err
    assert "criterion/group/case" in err
    assert "contention" not in err


@pytest.mark.parametrize("prefix", ["criterion/absent/", "", "   "])
def test_unmatched_or_blank_advisory_fails_closed(tmp_path: Path, prefix: str) -> None:
    # A stale or blank prefix must never silently widen or no-op the gate.
    args = _abba(tmp_path, (100.0, 100.0, 100.0, 100.0))
    assert gate.main([*args, "--advisory", prefix]) == 2


def test_advisory_covering_every_benchmark_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A prefix broad enough to empty the gate would pass on zero evidence.
    args = _abba(tmp_path, (100.0, 160.0, 160.0, 100.0))
    assert gate.main([*args, "--advisory", "criterion/", "--advisory", "pytest/"]) == 2
    assert "no gated benchmark" in capsys.readouterr().err


def test_every_benchmark_is_tabulated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _abba(tmp_path, (100.0, 100.0, 100.0, 100.0))
    assert gate.main([*args, "--advisory", "criterion/contention/"]) == 0
    out = capsys.readouterr().out
    for name in (
        "criterion/group/case",
        "criterion/contention/mutex/4",
        "pytest/tests/test_bridge.py::test_latency",
    ):
        assert name in out
    assert "3 benchmarks" in out
    assert "1 advisory" in out

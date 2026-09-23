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
        "--baseline",
        str(tmp_path / "reference"),
        "--criterion-dir",
        str(tmp_path / "candidate" / "criterion"),
        "--pytest-json",
        str(tmp_path / "candidate" / "pytest-bench.json"),
    ]


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
    assert 'measure "$GITHUB_WORKSPACE/.nightly-reference" reference' in job
    assert 'measure "$GITHUB_WORKSPACE" candidate' in job
    assert 'export CRITERION_HOME="$EVIDENCE_DIR/$arm/criterion"' in job
    assert (
        'cmp "$EVIDENCE_DIR/dependencies.txt" '
        '"$EVIDENCE_DIR/reference-dependencies.txt"' in job
    )
    assert "--threshold 0.10" in job
    assert "uses: actions/cache@" not in job
    assert "Refresh baseline" not in job
    measure = job.split(
        "      - name: Measure reference then candidate on the same runner", 1
    )[1].split("      - name: Compare against baseline", 1)[0]
    assert "set -euo pipefail" in measure
    assert "|| true" not in measure
    build = job.split(
        "      - name: Build matched candidate and reference environments", 1
    )[1].split("      - name: Measure reference then candidate on the same runner", 1)[
        0
    ]
    # DV036-F3: --no-build-isolation editable installs spawn the `maturin`
    # CLI from the PEP 517 hook; each venv's bin/ must be on PATH first.
    assert build.index("source .venv/bin/activate") < build.index('-e ".[dev,onnx]"')
    assert build.index("source .nightly-reference/.venv/bin/activate") < build.index(
        "-e .nightly-reference"
    )
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
    assert "if-no-files-found: error" in job

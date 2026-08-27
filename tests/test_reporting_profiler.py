"""Tests for deterministic benchmark reporting and torch profiling integration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import prin.reporting.benchmark_reporting as reporting
import prin.reporting.profiler as profiling
import pytest
import torch
from prin.reporting.benchmark_reporting import (
    ReportInputError,
    ReportOutputError,
    generate_benchmark_report,
    generate_leaderboard,
    generate_scalr_metrics_report,
)
from prin.reporting.profiler import (
    PRINetProfiler,
    ProfilerConfigurationError,
    ProfileReport,
    ProfilerStateError,
    profile_training_loop,
)
from torch import Tensor, nn


class TestBenchmarkReport:
    def test_is_deterministic_and_preserves_legacy_schema(self, tmp_path: Path) -> None:
        (tmp_path / "z.json").write_text(
            json.dumps(
                {
                    "benchmarks": [
                        {"name": "case-a", "status": "PASS"},
                        {"name": "case-b", "status": "FAIL"},
                    ],
                    "wall_time_s": 1.25,
                    "param_count": 12,
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "a.json").write_text(
            json.dumps(
                {
                    "status": "OK",
                    "accuracy": 0.95,
                    "results": {"model-a": [{"n_items": 2, "test_acc": 0.75}]},
                }
            ),
            encoding="utf-8",
        )

        first = generate_benchmark_report(tmp_path)
        second = generate_benchmark_report(tmp_path)

        assert first == second
        assert "Generated:" not in first
        assert first.index("`a.json`") < first.index("`z.json`")
        assert "accuracy=0.9500" in first
        assert "1/2 PASS" in first
        assert "2 sub-benchmarks" in first
        assert "| model-a (N=2) | test_acc | 0.7500 |" in first

    def test_explicit_generated_at_is_normalized_to_utc(self, tmp_path: Path) -> None:
        generated_at = datetime(2025, 1, 2, 4, 5, tzinfo=timezone(timedelta(hours=2)))
        report = generate_benchmark_report(tmp_path, generated_at=generated_at)
        assert "_Generated: 2025-01-02 02:05 UTC_" in report

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"title": ""}, "title"),
            ({"title": "bad\ntitle"}, "title"),
            ({"generated_at": datetime(2025, 1, 1)}, "timezone-aware"),
            ({"generated_at": ""}, "generated_at"),
            ({"generated_at": 3}, "generated_at"),
        ],
    )
    def test_rejects_invalid_public_inputs(
        self, tmp_path: Path, kwargs: dict[str, Any], message: str
    ) -> None:
        with pytest.raises(ReportInputError, match=message):
            generate_benchmark_report(tmp_path, **kwargs)

    def test_rejects_missing_or_non_directory_input(self, tmp_path: Path) -> None:
        with pytest.raises(ReportInputError, match="does not exist"):
            generate_benchmark_report(tmp_path / "missing")
        file_path = tmp_path / "file.json"
        file_path.write_text("{}", encoding="utf-8")
        with pytest.raises(ReportInputError, match="not a directory"):
            generate_benchmark_report(file_path)

    def test_malformed_and_non_object_json_are_reported_not_raised(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.json").write_text("{", encoding="utf-8")
        (tmp_path / "array.json").write_text("[]", encoding="utf-8")
        report = generate_benchmark_report(tmp_path)
        assert "| `array.json` | ERROR | Parse error:" in report
        assert "| `bad.json` | ERROR | Parse error:" in report
        assert report.count("_Error reading file._") == 2

    def test_writes_only_below_declared_roots(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        allowed = tmp_path / "allowed"
        monkeypatch.setattr(reporting, "_ALLOWED_OUTPUT_ROOTS", (allowed.resolve(),))
        output = allowed / "nested" / "report.md"
        report = generate_benchmark_report(tmp_path, output)
        assert output.read_text(encoding="utf-8") == report

        with pytest.raises(
            ReportOutputError, match="outside the declared output roots"
        ):
            generate_benchmark_report(tmp_path, tmp_path / "escaped.md")

    def test_escapes_markdown_control_characters(self, tmp_path: Path) -> None:
        (tmp_path / "metrics.json").write_text(
            json.dumps({"status": "PASS|maybe", "note": "line\nbreak"}),
            encoding="utf-8",
        )
        report = generate_benchmark_report(tmp_path, title="Safe report")
        assert "PASS\\|maybe" in report
        assert "line<br>break" in report


class TestLeaderboard:
    def test_extracts_legacy_shapes_and_ranks_deterministically(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "clevr.json").write_text(
            json.dumps(
                {
                    "alpha": [{"n_items": 3, "test_acc": 0.8}],
                    "beta": [{"n_items": 3, "test_acc": 0.9}],
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "oscillo.json").write_text(
            json.dumps(
                {
                    "benchmarks": [
                        {
                            "name": "binding",
                            "results": {"gamma": {"accuracy": 0.85}},
                        },
                        {
                            "name": "direct",
                            "model": "delta",
                            "accuracy": 0.7,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        board = generate_leaderboard(tmp_path)
        assert "Generated:" not in board
        assert "| 1 | beta | clevr (N=3) | test_acc | 0.9000 |" in board
        assert "| 2 | gamma | binding | accuracy | 0.8500 |" in board
        assert "| 4 | delta | direct | accuracy | 0.7000 |" in board
        assert board == generate_leaderboard(tmp_path)

    def test_skips_invalid_files_and_values(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("not-json", encoding="utf-8")
        (tmp_path / "invalid.json").write_text(
            json.dumps({"model": [{"test_acc": "high"}]}), encoding="utf-8"
        )
        board = generate_leaderboard(tmp_path)
        assert "No leaderboard data found." in board

    def test_supports_explicit_timestamp_and_confined_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(reporting, "_ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))
        output = tmp_path / "leaderboard.md"
        board = generate_leaderboard(
            tmp_path,
            output,
            generated_at="stored-artifact-time",
        )
        assert "_Generated: stored-artifact-time_" in board
        assert output.read_text(encoding="utf-8") == board


class TestScalrMetricsReport:
    def test_matches_legacy_windowed_summary(self) -> None:
        report = generate_scalr_metrics_report([0.5, 0.5, 1.0], window=2)
        assert "- Final r(t): 1.0000" in report
        assert "- Mean r(t): 0.6667" in report
        assert "- Mean CV: 0.1667" in report
        assert "- Max CV: 0.3333" in report
        assert "- Desync events (CV > 0.1): 1" in report
        assert "| 3 | 0.3333 |" in report

    def test_insufficient_data_and_nested_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(reporting, "_ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))
        output = tmp_path / "nested" / "scalr.md"
        report = generate_scalr_metrics_report([0.8], window=2, output_path=output)
        assert "Insufficient data" in report
        assert output.read_text(encoding="utf-8") == report

    @pytest.mark.parametrize(
        ("history", "window", "message"),
        [
            ([], 1, "must not be empty"),
            ([0.5], 0, "window"),
            ([0.5], True, "window"),
            ([float("nan")], 1, "finite"),
            (["bad"], 1, "real number"),
            ([True], 1, "real number"),
        ],
    )
    def test_validates_history_and_window(
        self, history: list[Any], window: Any, message: str
    ) -> None:
        with pytest.raises(ReportInputError, match=message):
            generate_scalr_metrics_report(history, window=window)


class TestReportingEdgeCases:
    def test_default_and_all_pass_statuses_and_scalar_details(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "default.json").write_text(
            json.dumps({"results": {"score": 2.5}}), encoding="utf-8"
        )
        (tmp_path / "pass.json").write_text(
            json.dumps({"benchmarks": [{"status": "PASS"}]}), encoding="utf-8"
        )
        report = generate_benchmark_report(tmp_path)
        assert "| `default.json` | OK |" in report
        assert "| `pass.json` | ALL PASS |" in report
        assert "| score | value | 2.5 |" in report

    def test_invalid_metric_is_isolated_to_its_artifact(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text(
            json.dumps(
                {
                    "accuracy": float("nan"),
                    "results": {"model": [{"test_acc": "bad"}]},
                }
            ),
            encoding="utf-8",
        )
        report = generate_benchmark_report(tmp_path)
        assert "| `bad.json` | ERROR |" in report
        assert "_Error reading file._" in report

    @pytest.mark.parametrize("value", [3, ""])
    def test_invalid_path_values_are_typed(self, tmp_path: Path, value: Any) -> None:
        with pytest.raises(ReportInputError):
            generate_benchmark_report(value)
        with pytest.raises(ReportInputError):
            generate_benchmark_report(tmp_path, output_path=value)

    def test_leaderboard_ignores_malformed_nested_rows(self, tmp_path: Path) -> None:
        (tmp_path / "mixed.json").write_text(
            json.dumps(
                {
                    "plain": "ignored",
                    "benchmarks": [
                        "ignored",
                        {
                            "results": {
                                "bad-shape": [],
                                "bad-value": {"accuracy": "bad"},
                            },
                            "accuracy": "bad",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        assert "No leaderboard data found." in generate_leaderboard(tmp_path)

    def test_history_requires_list_and_unit_interval(self) -> None:
        with pytest.raises(ReportInputError, match="list"):
            generate_scalr_metrics_report((0.5,), window=1)  # type: ignore[arg-type]
        with pytest.raises(ReportInputError, match=r"\[0, 1\]"):
            generate_scalr_metrics_report([1.1], window=1)


class TestProfileReport:
    def test_preserves_legacy_fields(self) -> None:
        report = ProfileReport(
            total_wall_ms=100.0,
            n_steps=5,
            avg_step_ms=20.0,
            top_ops=[("aten::mm", 10.0, 5.0)],
            top_ops_table="Op  CPU  CUDA",
            bottleneck_op="aten::mm",
        )
        assert report.total_wall_ms == pytest.approx(100.0)
        assert report.bottleneck_op == "aten::mm"
        assert report.raw == {}

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"total_wall_ms": -1.0}, "total_wall_ms"),
            ({"n_steps": -1}, "n_steps"),
            ({"avg_step_ms": float("inf")}, "avg_step_ms"),
            ({"top_ops": [("op", -1.0, 0.0)]}, "top_ops"),
            ({"top_ops": [("", 0.0, 0.0)]}, "top_ops"),
            ({"total_wall_ms": True}, "total_wall_ms"),
        ],
    )
    def test_validates_fields(self, kwargs: dict[str, Any], message: str) -> None:
        with pytest.raises(ProfilerConfigurationError, match=message):
            ProfileReport(**kwargs)


class TestPRINetProfiler:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"warmup_steps": -1}, "warmup_steps"),
            ({"warmup_steps": True}, "warmup_steps"),
            ({"active_steps": 0}, "active_steps"),
            ({"record_shapes": 1}, "record_shapes"),
        ],
    )
    def test_validates_configuration(
        self, kwargs: dict[str, Any], message: str
    ) -> None:
        with pytest.raises(ProfilerConfigurationError, match=message):
            PRINetProfiler(**kwargs)

    def test_rejects_output_outside_declared_roots(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            profiling, "_ALLOWED_OUTPUT_ROOTS", ((tmp_path / "allowed").resolve(),)
        )
        with pytest.raises(ProfilerConfigurationError, match="outside"):
            PRINetProfiler(out_dir=tmp_path / "escaped")

    @pytest.mark.parametrize("out_dir", ["", 4])
    def test_rejects_invalid_output_directory_types(self, out_dir: Any) -> None:
        with pytest.raises(ProfilerConfigurationError, match="out_dir"):
            PRINetProfiler(out_dir=out_dir)

    def test_lifecycle_errors_are_typed(self) -> None:
        profiler = PRINetProfiler(warmup_steps=0, active_steps=1)
        with pytest.raises(ProfilerStateError, match="entered"):
            profiler.step()
        with pytest.raises(ProfilerStateError, match="completed"):
            profiler.report()
        with pytest.raises(ProfilerStateError, match="entered"):
            with profiler.record_function("rust::step"):
                pass
        with pytest.raises(ProfilerConfigurationError, match="label"):
            profiler.record_function("")
        with pytest.raises(ProfilerStateError, match="not active"):
            profiler.__exit__(None, None, None)

    def test_profiles_and_labels_rust_backed_operation(self) -> None:
        profiler = PRINetProfiler(out_dir=None, warmup_steps=1, active_steps=1)
        tensor = torch.ones((2, 2))
        with profiler:
            for _ in range(2):
                with profiler.record_function("prin::rust_backed_step"):
                    tensor = tensor + 1
                profiler.step()
        report = profiler.report(top_n=100)
        assert report.avg_step_ms >= 0.0
        assert report.n_steps == 1
        assert "prin::rust_backed_step" in {row[0] for row in report.top_ops}
        assert report.bottleneck_op
        assert report.raw["n_steps"] == 1
        with pytest.raises(ProfilerStateError, match="already been entered"):
            profiler.__enter__()

    def test_exports_trace_below_allowed_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(profiling, "_ALLOWED_OUTPUT_ROOTS", (tmp_path.resolve(),))
        profiler = PRINetProfiler(tmp_path / "trace", warmup_steps=0, active_steps=1)
        with profiler:
            _ = torch.ones(1) + 1
            profiler.step()
        report = profiler.report(top_n=1)
        assert report.json_trace_path is not None
        trace = Path(report.json_trace_path)
        assert trace.name == "prinet_trace.json"
        assert trace.is_file()

    def test_report_validates_top_n(self) -> None:
        profiler = PRINetProfiler(warmup_steps=0, active_steps=1)
        with profiler:
            profiler.step()
        with pytest.raises(ProfilerConfigurationError, match="top_n"):
            profiler.report(top_n=0)


class SquareLoss(nn.Module):
    def forward(self, logits: Tensor, labels: Tensor) -> Tensor:
        """Return a deterministic scalar squared-error loss."""
        return ((logits - labels) ** 2).mean()


class InvalidLoss(nn.Module):
    def forward(self, logits: Tensor, labels: Tensor) -> Tensor:
        return logits - labels


class InvalidLengthIterable:
    def __iter__(self) -> Any:
        return iter([(torch.ones(1), torch.ones(1))])

    def __len__(self) -> int:
        raise ValueError("invalid")


class TestProfileTrainingLoop:
    def test_profiles_forward_and_backward_without_rng(self) -> None:
        inputs = torch.ones((2, 3), requires_grad=True)
        labels = torch.zeros((2, 3))
        report = profile_training_loop(
            nn.Identity(),
            [(inputs, labels)],
            n_steps=1,
            warmup_steps=0,
            device=torch.device("cpu"),
            loss_fn=SquareLoss(),
            top_n=10,
        )
        assert report.n_steps == 1
        assert inputs.grad is not None
        assert report.top_ops

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"model": object()}, "model"),
            ({"n_steps": 0}, "n_steps"),
            ({"warmup_steps": -1}, "warmup_steps"),
            ({"top_n": 0}, "top_n"),
            ({"loss_fn": object()}, "loss_fn"),
            ({"device": "cpu"}, "device"),
            ({"dataloader": 3}, "iterable"),
            ({"dataloader": InvalidLengthIterable()}, "length"),
        ],
    )
    def test_validates_inputs(self, kwargs: dict[str, Any], message: str) -> None:
        arguments: dict[str, Any] = {
            "model": nn.Identity(),
            "dataloader": [(torch.ones(1), torch.ones(1))],
            "n_steps": 1,
            "warmup_steps": 0,
            "device": torch.device("cpu"),
        }
        arguments.update(kwargs)
        with pytest.raises(ProfilerConfigurationError, match=message):
            profile_training_loop(**arguments)

    def test_rejects_empty_or_invalid_batches(self) -> None:
        with pytest.raises(ProfilerConfigurationError, match="no batches"):
            profile_training_loop(
                nn.Identity(),
                [],
                n_steps=1,
                warmup_steps=0,
                device=torch.device("cpu"),
            )
        with pytest.raises(ProfilerConfigurationError, match="two tensors"):
            profile_training_loop(
                nn.Identity(),
                [(torch.ones(1),)],
                n_steps=1,
                warmup_steps=0,
                device=torch.device("cpu"),
            )
        with pytest.raises(ProfilerConfigurationError, match="two tensors"):
            profile_training_loop(
                nn.Identity(),
                [("not-a-tensor", torch.ones(1))],
                n_steps=1,
                warmup_steps=0,
                device=torch.device("cpu"),
            )
        empty_generator = (batch for batch in [])
        with pytest.raises(ProfilerConfigurationError, match="restarted"):
            profile_training_loop(
                nn.Identity(),
                empty_generator,
                n_steps=1,
                warmup_steps=0,
                device=torch.device("cpu"),
            )

    def test_restarts_finite_loader_for_warmup(self) -> None:
        report = profile_training_loop(
            nn.Identity(),
            [(torch.ones(1), torch.ones(1))],
            n_steps=1,
            warmup_steps=1,
            device=torch.device("cpu"),
        )
        assert report.n_steps == 1

    def test_rejects_non_scalar_loss(self) -> None:
        with pytest.raises(ProfilerConfigurationError, match="scalar"):
            profile_training_loop(
                nn.Identity(),
                [(torch.ones(2), torch.zeros(2))],
                n_steps=1,
                warmup_steps=0,
                device=torch.device("cpu"),
                loss_fn=InvalidLoss(),
            )

    def test_event_timing_sanitizes_dynamic_values(self) -> None:
        event = type("Event", (), {"bad": float("nan")})()
        assert profiling._event_numeric_attribute(event, "missing") == 0.0
        assert profiling._event_numeric_attribute(event, "bad") == 0.0

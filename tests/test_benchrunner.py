"""Tests for the unified `benchrunner` CLI and its nine category packages
(WP-033 S1).

Covers: shared config/timing/registry/result-writer infrastructure, the
Benchmarking and Reproducibility Standards §2.2 timing rule (warmup
excluded, >=10 measured iterations), JSON schema compatibility with the
legacy PRINet 3.0 field names, and the CLI's end-to-end dispatch. Problem
sizes are kept tiny throughout -- this suite characterizes the *machinery*
(schema, timing rule, dispatch), not production-scale benchmark numbers
(Non-goal: drawing conclusions from final measurements).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

import pytest

from benchmarks._common.config import (
    MIN_MEASURED_ITERATIONS,
    BenchmarkConfig,
    BenchmarkConfigError,
)
from benchmarks._common.environment import capture_environment
from benchmarks._common.registry import (
    CATEGORIES,
    RegistryError,
    get,
    list_specs,
    register,
)
from benchmarks._common.result import (
    ArtefactExistsError,
    OutputPathError,
    write_result,
)
from benchmarks._common.timing import timed_run
from benchmarks.benchrunner.__main__ import _load_categories, main

ROOT = Path(__file__).parents[1]

# Import every category package once so the registry is populated for every
# test in this module (mirrors what `benchrunner`'s CLI does at startup).
_load_categories()


# ---------------------------------------------------------------------------
# BenchmarkConfig
# ---------------------------------------------------------------------------


class TestBenchmarkConfig:
    def test_default_iterations_meets_minimum(self) -> None:
        config = BenchmarkConfig()
        assert config.iterations == MIN_MEASURED_ITERATIONS

    def test_iterations_below_minimum_raises(self) -> None:
        with pytest.raises(BenchmarkConfigError, match="iterations"):
            BenchmarkConfig(iterations=MIN_MEASURED_ITERATIONS - 1)

    def test_negative_warmup_raises(self) -> None:
        with pytest.raises(BenchmarkConfigError, match="warmup"):
            BenchmarkConfig(warmup=-1)


# ---------------------------------------------------------------------------
# Timing harness: Benchmarking and Reproducibility Standards §2.2
# ---------------------------------------------------------------------------


class TestTimedRun:
    def test_rejects_fewer_than_minimum_iterations(self) -> None:
        with pytest.raises(BenchmarkConfigError, match="10"):
            timed_run(lambda: None, iterations=9, warmup=0)

    def test_warmup_excluded_from_samples(self) -> None:
        calls: list[int] = []

        def fn() -> int:
            calls.append(1)
            return len(calls)

        stats, last = timed_run(fn, iterations=10, warmup=3)
        assert len(calls) == 13
        assert len(stats.samples_s) == 10
        assert last == 13  # last measured call is the 13th total call

    def test_median_and_p95_over_ten_iterations(self) -> None:
        stats, _ = timed_run(lambda: None, iterations=10, warmup=0)
        assert len(stats.samples_s) == 10
        assert stats.min_s <= stats.median_s <= stats.max_s
        assert stats.min_s <= stats.p95_s <= stats.max_s

    def test_to_dict_has_iteration_count(self) -> None:
        stats, _ = timed_run(lambda: None, iterations=12, warmup=0)
        assert stats.to_dict()["iterations"] == 12


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_every_category_has_at_least_one_registered_benchmark(self) -> None:
        for category in CATEGORIES:
            specs = list_specs(category)
            assert specs, f"category {category!r} has no registered benchmark"

    def test_unknown_category_raises(self) -> None:
        with pytest.raises(RegistryError, match="unknown category"):
            list_specs("not-a-category")

    def test_get_unknown_benchmark_raises(self) -> None:
        with pytest.raises(RegistryError, match="no benchmark registered"):
            get("scaling", "not-a-real-benchmark")

    def test_register_rejects_unknown_category(self) -> None:
        with pytest.raises(RegistryError, match="unknown category"):
            register("not-a-category", "x", summary="x")(lambda config: {})

    def test_register_rejects_duplicate(self) -> None:
        register("scaling", "__test_dup__", summary="x")(lambda config: {})
        with pytest.raises(RegistryError, match="already registered"):
            register("scaling", "__test_dup__", summary="x")(lambda config: {})


# ---------------------------------------------------------------------------
# Environment capture: Benchmarking and Reproducibility Standards §1.4
# ---------------------------------------------------------------------------


class TestCaptureEnvironment:
    def test_required_fields_present(self) -> None:
        env = capture_environment(backend="host CPU", dtype="f64", seed=0)
        for field in (
            "prin_version",
            "git_commit",
            "rust_version",
            "python_version",
            "platform",
            "processor",
            "logical_cpus",
            "backend",
            "dtype",
            "seed",
        ):
            assert field in env

    def test_backend_dtype_seed_roundtrip(self) -> None:
        env = capture_environment(backend="cpu", dtype="f32", seed=7)
        assert env["backend"] == "cpu"
        assert env["dtype"] == "f32"
        assert env["seed"] == 7

    def test_seed_none_for_deterministic_only_measurements(self) -> None:
        env = capture_environment(backend="cpu", dtype="f64", seed=None)
        assert env["seed"] is None


# ---------------------------------------------------------------------------
# Result writer: Coding Standards §6.1 output-path confinement
# ---------------------------------------------------------------------------


class TestWriteResult:
    def test_writes_inside_results_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.result as result_module

        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        out = tmp_path / "artefact.json"
        written = write_result(
            out,
            environment={"backend": "cpu"},
            config={"iterations": 10},
            payload={"x": 1},
        )
        assert written == out.resolve()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data == {
            "environment": {"backend": "cpu"},
            "config": {"iterations": 10},
            "x": 1,
        }

    def test_reserved_key_collision_raises(self, tmp_path: Path) -> None:
        with pytest.raises(OutputPathError, match="reserved"):
            write_result(
                tmp_path / "x.json",
                environment={},
                config={},
                payload={"environment": "oops"},
            )

    def test_path_outside_declared_roots_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.result as result_module

        monkeypatch.setattr(
            result_module, "_ALLOWED_ROOTS", (ROOT / "benchmarks" / "results",)
        )
        with pytest.raises(OutputPathError, match="outside the declared output roots"):
            write_result(
                ROOT / "not_a_declared_dir" / "x.json",
                environment={},
                config={},
                payload={},
            )

    def test_existing_artefact_is_never_overwritten(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # DV-038 / Experimentation Standards §4: raw artefacts are append-only.
        import benchmarks._common.result as result_module

        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        out = tmp_path / "RUN-20260921T000000Z-8ce115f-smoke" / "artefact.json"
        write_result(out, environment={}, config={}, payload={"x": 1})
        before = out.read_bytes()
        with pytest.raises(ArtefactExistsError, match="append-only"):
            write_result(out, environment={}, config={}, payload={"x": 2})
        assert out.read_bytes() == before
        # The guard is an OutputPathError so callers catching the base class
        # (benchrunner's CLI) keep their existing error path.
        assert issubclass(ArtefactExistsError, OutputPathError)


# ---------------------------------------------------------------------------
# JSON schema compatibility: Benchmarking and Reproducibility Standards §1.3
# ---------------------------------------------------------------------------


class TestSchemaCompatibility:
    """Each category's payload must keep the legacy PRINet 3.0 field names
    the corresponding stored result JSON used, so historical artefacts and
    any tooling that reads them by field name remain valid.
    """

    def test_scaling_matches_legacy_ring_scaling_fields(self) -> None:
        spec = get("scaling", "oscillator_count")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"sizes": [16, 32], "n_steps": 3},
        )
        payload = spec.fn(config)
        assert payload["benchmark"] == "oscillator_count_scaling"
        for entry in payload["scales"]:
            # Field names from the archived
            # benchmark_y4q1_ring_scaling.json: N, wall_time_s, throughput,
            # final_order_param.
            for legacy_field in ("N", "wall_time_s", "throughput", "final_order_param"):
                assert legacy_field in entry
            assert isinstance(entry["N"], int)
            assert isinstance(entry["wall_time_s"], float)
            assert isinstance(entry["throughput"], float)
            assert isinstance(entry["final_order_param"], float)

    def test_chimera_matches_legacy_phase_diagram_fields(self) -> None:
        spec = get("chimera", "phase_diagram")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={
                "n": 16,
                "k_neighbors": 4,
                "coupling_strengths": [1.0],
                "n_steps": 5,
            },
        )
        payload = spec.fn(config)
        point = payload["points"][0]
        for field in ("coupling_strength", "order_parameter", "chimera_index"):
            assert field in point
            assert isinstance(point[field], float)

    def test_adversarial_matches_adversarial_eval_result_fields(self) -> None:
        spec = get("adversarial", "robustness")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"n_sequences": 1, "n_objects": 2, "n_frames": 3, "pgd_steps": 2},
        )
        payload = spec.fn(config)
        fgsm = payload["trackers"]["phase_tracker"]["fgsm"]
        # Field names mirror AdversarialEvalResult: clean_ip, adv_ip,
        # degradation (python/prin/_prin_core.pyi).
        for field in (
            "clean_identity_preservation",
            "adversarial_identity_preservation",
            "degradation",
        ):
            assert field in fgsm
            assert isinstance(fgsm[field], float)


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------


class TestBenchrunnerCli:
    def test_list_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--list"]) == 0
        out = capsys.readouterr().out
        for category in CATEGORIES:
            assert category in out

    def test_missing_category_without_list_is_an_error(self) -> None:
        assert main([]) == 2

    def test_iterations_below_minimum_is_an_error(self) -> None:
        assert main(["--category", "scaling", "--iterations", "3"]) == 2

    def test_runs_one_named_benchmark_and_writes_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.result as result_module

        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        exit_code = main(
            [
                "--category",
                "scaling",
                "--name",
                "oscillator_count",
                "--out",
                str(tmp_path),
                "--iterations",
                "10",
                "--warmup",
                "1",
            ]
        )
        assert exit_code == 0
        out_file = tmp_path / "scaling_oscillator_count.json"
        assert out_file.is_file()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["config"]["iterations"] == 10
        assert "environment" in data
        assert data["benchmark"] == "oscillator_count_scaling"

    def test_second_run_into_same_out_dir_is_an_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # DV-038: re-running with the same --out must not silently replace the
        # first artefact; the campaign run-directory rule requires a new RUN-
        # directory per execution (campaign plan §7.1).
        import benchmarks._common.result as result_module

        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        argv = [
            "--category",
            "scaling",
            "--name",
            "oscillator_count",
            "--out",
            str(tmp_path),
            "--iterations",
            "10",
            "--warmup",
            "1",
        ]
        assert main(argv) == 0
        out_file = tmp_path / "scaling_oscillator_count.json"
        before = out_file.read_bytes()
        capsys.readouterr()
        assert main(argv) == 2
        assert "append-only" in capsys.readouterr().err
        assert out_file.read_bytes() == before

    def test_unknown_name_within_category_is_an_error(self, tmp_path: Path) -> None:
        exit_code = main(
            [
                "--category",
                "scaling",
                "--name",
                "not-a-real-benchmark",
                "--out",
                str(tmp_path),
            ]
        )
        assert exit_code == 2

    def test_category_with_no_registered_benchmarks_is_an_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks.benchrunner.__main__ as main_module

        monkeypatch.setattr(main_module, "list_specs", lambda category: [])
        exit_code = main(["--category", "scaling"])
        assert exit_code == 2

    def test_output_path_outside_declared_roots_is_an_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Not under benchmarks/results/, DOCS/test_and_benchmark_results/, or
        # a temp dir (tmp_path itself resolves *inside* the temp dir, so it
        # would not exercise this branch).
        outside = ROOT / "not_a_declared_output_root"
        exit_code = main(
            [
                "--category",
                "scaling",
                "--name",
                "oscillator_count",
                "--out",
                str(outside),
                "--iterations",
                "10",
            ]
        )
        assert exit_code == 2
        assert "outside the declared output roots" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# kernels/: criterion subprocess bridge -- pure functions only (no cargo
# invocation in the fast suite; the slow, real-subprocess proof lives in
# TestKernelCriterionBridgeSlow below).
# ---------------------------------------------------------------------------


class TestKernelCriterionBridgeParsing:
    def test_parse_estimates_reads_point_estimates(self, tmp_path: Path) -> None:
        from benchmarks.kernels.criterion_bridge import parse_estimates

        estimates = tmp_path / "estimates.json"
        estimates.write_text(
            json.dumps(
                {
                    "mean": {"point_estimate": 100.0},
                    "median": {"point_estimate": 95.0},
                    "std_dev": {"point_estimate": 5.0},
                }
            ),
            encoding="utf-8",
        )
        parsed = parse_estimates(estimates)
        assert parsed == {"mean_ns": 100.0, "median_ns": 95.0, "std_dev_ns": 5.0}

    def test_parse_estimates_missing_file_raises(self, tmp_path: Path) -> None:
        from benchmarks.kernels.criterion_bridge import (
            CriterionBenchNotFoundError,
            parse_estimates,
        )

        with pytest.raises(CriterionBenchNotFoundError, match="no criterion estimates"):
            parse_estimates(tmp_path / "missing.json")

    def test_criterion_args_shape(self) -> None:
        from benchmarks.kernels.criterion_bridge import criterion_args

        args = criterion_args(
            "mean_field_rk4_bench", sample_size=10, warmup_s=0.5, measurement_s=0.5
        )
        assert args[1:8] == [
            "bench",
            "-p",
            "prin-kernels",
            "--features",
            "cpu",
            "--bench",
            "mean_field_rk4_bench",
        ]
        assert "--sample-size" in args
        assert "10" in args

    def test_cargo_path_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import benchmarks.kernels.criterion_bridge as bridge_module

        monkeypatch.setattr(bridge_module.shutil, "which", lambda name: None)
        with pytest.raises(
            bridge_module.CriterionBenchNotFoundError, match="cargo executable"
        ):
            bridge_module._cargo_path()

    def test_run_cargo_bench_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess

        import benchmarks.kernels.criterion_bridge as bridge_module

        class _Completed:
            returncode = 0
            stderr = ""

        monkeypatch.setattr(bridge_module, "_cargo_path", lambda: "cargo")
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed())
        bridge_module.run_cargo_bench(
            "mean_field_rk4_bench", sample_size=10, warmup_s=0.1, measurement_s=0.1
        )  # does not raise

    def test_run_cargo_bench_nonzero_exit_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import subprocess

        import benchmarks.kernels.criterion_bridge as bridge_module

        class _Failed:
            returncode = 101
            stderr = "compile error"

        monkeypatch.setattr(bridge_module, "_cargo_path", lambda: "cargo")
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Failed())
        with pytest.raises(
            bridge_module.CriterionBenchNotFoundError, match="compile error"
        ):
            bridge_module.run_cargo_bench(
                "mean_field_rk4_bench", sample_size=10, warmup_s=0.1, measurement_s=0.1
            )

    def test_kernel_criterion_suite_full_body(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exercises `kernel_criterion_suite`'s full loop with a faked
        subprocess/filesystem, independent of the real (slow) `cargo bench`
        proof in `TestKernelCriterionBridgeSlow`.
        """
        import benchmarks.kernels.criterion_bridge as bridge_module

        monkeypatch.setattr(bridge_module, "run_cargo_bench", lambda *a, **k: None)
        monkeypatch.setattr(
            bridge_module,
            "parse_estimates",
            lambda path: {"mean_ns": 1.0, "median_ns": 1.0, "std_dev_ns": 0.1},
        )
        config = BenchmarkConfig(iterations=MIN_MEASURED_ITERATIONS)
        payload = bridge_module.kernel_criterion_suite(config)
        assert payload["benchmark"] == "kernel_criterion_suite"
        assert len(payload["targets"]) == len(bridge_module.CPU_TARGETS)

    def test_kernel_suite_rejects_below_minimum_iterations(self) -> None:
        """`kernel_criterion_suite` re-checks the floor itself (its `config.iterations`
        maps directly to criterion's `--sample-size`, independent of
        `BenchmarkConfig.__post_init__`'s own guard) -- exercised here via a
        minimal duck-typed stand-in rather than bypassing the frozen dataclass.
        """
        from benchmarks.kernels.criterion_bridge import kernel_criterion_suite

        class _FakeConfig:
            iterations: int = MIN_MEASURED_ITERATIONS - 1
            params: ClassVar[dict[str, object]] = {}

        with pytest.raises(BenchmarkConfigError):
            kernel_criterion_suite(_FakeConfig())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Remaining category modules: mot, ablations, integrators, training, daemon.
# All params kept tiny so this stays inside the fast (`not slow`) gate.
# ---------------------------------------------------------------------------


class TestRemainingCategories:
    def test_scaling_coupling_complexity(self) -> None:
        spec = get("scaling", "coupling_complexity")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"sizes": [16, 32], "n_steps": 3, "k_neighbors": 4},
        )
        payload = spec.fn(config)
        assert payload["benchmark"] == "coupling_complexity_scaling"
        modes = {m["coupling_mode"] for m in payload["modes"]}
        assert modes == {"mean_field", "sparse_knn", "full"}

    def test_mot_tracker_comparison(self) -> None:
        spec = get("mot", "tracker_comparison")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"n_sequences": 1, "n_objects": 2, "n_frames": 3},
        )
        payload = spec.fn(config)
        assert set(payload["trackers"]) == {"phase_tracker", "slot_attention"}
        for tracker_result in payload["trackers"].values():
            ip = tracker_result["clean_identity_preservation"]
            assert 0.0 <= ip <= 1.0

    def test_ablations_variant_comparison(self) -> None:
        spec = get("ablations", "variant_comparison")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"n_objects": 2, "n_frames": 3},
        )
        payload = spec.fn(config)
        assert set(payload["variants"]) == {
            "phase_tracker_full",
            "phase_tracker_frozen",
            "phase_tracker_static",
            "slot_attention_full",
            "slot_attention_frozen",
            "slot_attention_no_gru",
        }
        for variant_result in payload["variants"].values():
            assert variant_result["state_size_bytes"] > 0

    def test_integrators_accuracy_cost(self) -> None:
        spec = get("integrators", "accuracy_cost")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS, warmup=1, params={"n": 8, "n_steps": 5}
        )
        payload = spec.fn(config)
        assert set(payload["integrators"]) == {
            "euler",
            "rk4",
            "exponential",
            "multi_rate",
            "rk45_adaptive",
        }
        assert payload["integrators"]["rk45_adaptive"]["accepted_steps"] >= 1

    def test_training_throughput(self) -> None:
        spec = get("training", "throughput")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"train_seqs": 2, "val_seqs": 1, "n_frames": 3, "max_epochs": 1},
        )
        payload = spec.fn(config)
        assert payload["total_epochs"] >= 1
        assert payload["epochs_per_sec"] > 0

    def test_daemon_control_latency(self) -> None:
        spec = get("daemon", "control_latency")
        config = BenchmarkConfig(iterations=MIN_MEASURED_ITERATIONS, warmup=1)
        payload = spec.fn(config)
        assert payload["p50_s"] >= 0.0
        assert payload["p95_s"] >= payload["p50_s"]

    def test_daemon_control_latency_raises_if_inference_never_completes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A daemon whose callback never completes must raise, not silently
        report latency over zero real inferences. Faked deterministically
        (rather than racing a real timeout) since the real daemon's
        background thread times are not controllable from the test.
        """
        import benchmarks.daemon.control_latency as control_latency_module

        class _NeverInfersDaemon:
            def __init__(self, *args: object, **kwargs: object) -> None:
                self.inference_count = 0
                self.error_count = 0

            def submit_state(self, state: object) -> None:
                pass

            def stop(self, timeout_ms: int = 5_000) -> bool:
                return True

        monkeypatch.setattr(
            control_latency_module, "SubconsciousDaemon", _NeverInfersDaemon
        )
        spec = get("daemon", "control_latency")
        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            warmup=1,
            params={"wait_timeout_s": 0.01},
        )
        with pytest.raises(RuntimeError, match="no inference completed"):
            spec.fn(config)


# ---------------------------------------------------------------------------
# environment.py: subprocess-failure branches
# ---------------------------------------------------------------------------


class TestCaptureEnvironmentFallbacks:
    def test_missing_executables_yield_none_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.environment as env_module

        monkeypatch.setattr(env_module, "_which", lambda name: None)
        env = capture_environment(backend="cpu", dtype="f64", seed=0)
        assert env["git_commit"] is None
        assert env["rust_version"] is None
        assert env["gpu"] is None
        assert env["gpu_vram_mb"] is None

    def test_subprocess_failure_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import subprocess

        import benchmarks._common.environment as env_module

        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("no such executable")

        monkeypatch.setattr(subprocess, "run", _boom)
        assert env_module._run(["nonexistent-binary"]) is None

    def test_nonzero_exit_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess

        import benchmarks._common.environment as env_module

        class _FailedCompletion:
            returncode = 1
            stdout = ""

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FailedCompletion())
        assert env_module._run(["git", "rev-parse", "HEAD"]) is None

    def test_prin_version_missing_package_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from importlib import metadata

        import benchmarks._common.environment as env_module

        def _raise(name: str) -> str:
            raise metadata.PackageNotFoundError(name)

        monkeypatch.setattr(metadata, "version", _raise)
        assert env_module._prin_version() is None

    def test_gpu_info_empty_nvidia_smi_output_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.environment as env_module

        monkeypatch.setattr(env_module, "_which", lambda name: "/usr/bin/nvidia-smi")
        monkeypatch.setattr(env_module, "_run", lambda args: "")
        assert env_module._gpu_info() == {"gpu": None, "vram_mb": None}

    def test_gpu_info_malformed_vram_becomes_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import benchmarks._common.environment as env_module

        monkeypatch.setattr(env_module, "_which", lambda name: "/usr/bin/nvidia-smi")
        monkeypatch.setattr(env_module, "_run", lambda args: "Some GPU, not-a-number")
        info = env_module._gpu_info()
        assert info["gpu"] == "Some GPU"
        assert info["vram_mb"] is None


@pytest.mark.slow
class TestKernelCriterionBridgeSlow:
    """Real `cargo bench` proof that the kernels category is genuinely
    executable, not just schema-shaped. Excluded from the default
    ``-m "not slow"`` gate; run explicitly (``pytest -m slow``).
    """

    def test_criterion_suite_runs_end_to_end(self) -> None:
        from benchmarks.kernels.criterion_bridge import kernel_criterion_suite

        config = BenchmarkConfig(
            iterations=MIN_MEASURED_ITERATIONS,
            params={"warmup_s": 0.1, "measurement_s": 0.2},
        )
        payload = kernel_criterion_suite(config)
        assert payload["benchmark"] == "kernel_criterion_suite"
        assert len(payload["targets"]) == 4
        for target_result in payload["targets"].values():
            assert target_result["median_ns"] > 0

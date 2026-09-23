"""Tests for the committed EXP-001 E4 analysis module (session 0157).

The module lives under the experiment's record root, which campaign plan §7.4
item 2 names as a permitted location for analysis code, and whose directory
name is not a legal Python identifier — so it is loaded here by path through
``importlib`` rather than imported. Keeping the tests under ``tests/`` puts
them inside the repository's authoritative pytest gate.

The registered §8 decision rule is what these tests pin: the abort-exclusion
rule, the "a partial abort can never produce CONFIRMED" rule, H4's
build-configuration ``INCONCLUSIVE`` branch, the D1 flag, and byte-for-byte
determinism of every generated output (campaign plan §7.4 step 5).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = (
    _REPOSITORY_ROOT
    / "DOCS"
    / "experiments"
    / "EXP-001-golden-trajectory-numerical-parity"
    / "analysis"
    / "exp001_e4_analysis.py"
)


def _load_module() -> Any:
    """Load the analysis module by path, as its directory name is not importable."""
    spec = importlib.util.spec_from_file_location("exp001_e4_analysis", _MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analysis = _load_module()


def _comparison(name: str, *, ok: bool, abs_diff: float = 0.0) -> dict[str, Any]:
    """Build one comparison record shaped like the driver's output."""
    return {
        "array_name": name,
        "within_tolerance": ok,
        "max_abs_diff": abs_diff,
        "max_rel_diff": abs_diff,
        "failed_count": 0 if ok else 1,
        "total_count": 8,
    }


def _corpus_case(
    case_id: str, *, ok: bool = True, aborted: bool = False, abs_diff: float = 0.0
) -> dict[str, Any]:
    """Build one corpus/kernel-path case record."""
    case: dict[str, Any] = {
        "aborted": aborted,
        "case_id": case_id,
        "model": "kuramoto",
        "coupling": "mean_field",
        "integrator": "euler",
        "within_tolerance": ok,
        "comparisons": [_comparison("phase_traj", ok=ok, abs_diff=abs_diff)],
    }
    if aborted:
        case["abort_reason"] = "nan-guard"
    return case


def _corpus_payload(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap corpus cases in the standard result envelope."""
    return {
        "cases": cases,
        "config": {},
        "environment": {"git_commit": analysis.EXECUTION_COMMIT, "backend": "cpu"},
    }


def _fuzz_payload(cases: list[dict[str, Any]], requested: int = 1000) -> dict[str, Any]:
    """Wrap fuzz cases in the standard result envelope."""
    return {
        "cases": cases,
        "config": {
            "fuzz_batch_class": "confirmatory",
            "fuzz_batch_confirmatory_minimum": 1000,
            "n_fuzz_cases_requested": requested,
        },
        "environment": {"git_commit": analysis.EXECUTION_COMMIT, "backend": "cpu"},
    }


class TestDecadeHistogram:
    """The distribution report must be exact counts, with no estimator."""

    def test_zero_gets_its_own_bucket(self) -> None:
        assert analysis._decade_histogram([0.0, 0.0]) == {"0": 2}

    def test_buckets_are_ordered_by_magnitude(self) -> None:
        histogram = analysis._decade_histogram([1e-3, 1e-9, 0.0, 5.0])
        assert list(histogram) == ["0", "1e-9", "1e-3", "1e0"]

    def test_non_finite_is_bucketed_not_dropped(self) -> None:
        histogram = analysis._decade_histogram([float("inf"), 1.0])
        assert histogram["non-finite"] == 1
        assert list(histogram)[-1] == "non-finite"

    def test_empty_input_is_empty_histogram(self) -> None:
        assert analysis._decade_histogram([]) == {}


class TestToleranceVerdict:
    """Pre-registration §8's shared pass/fail decision shape."""

    def test_full_clean_denominator_confirms(self) -> None:
        assert analysis._tolerance_verdict(0, 504, 504) == "CONFIRMED"

    def test_any_breach_refutes(self) -> None:
        assert analysis._tolerance_verdict(1, 504, 504) == "REFUTED"

    def test_partial_abort_can_never_confirm(self) -> None:
        assert analysis._tolerance_verdict(0, 503, 504) == "INCONCLUSIVE"

    def test_breach_outranks_partial_abort(self) -> None:
        assert analysis._tolerance_verdict(1, 503, 504) == "REFUTED"


class TestH1:
    """H1 adjudication over the corpus artefact."""

    def test_confirmed_at_full_clean_denominator(self) -> None:
        cases = [_corpus_case(f"c{i}") for i in range(504)]
        record = analysis.adjudicate_h1(_corpus_payload(cases))
        assert record["verdict"] == "CONFIRMED"
        assert record["n_pass"] == 504
        assert record["n_aborted"] == 0

    def test_single_breach_refutes_and_is_named(self) -> None:
        cases = [_corpus_case(f"c{i}") for i in range(503)]
        cases.append(_corpus_case("bad", ok=False, abs_diff=2e-7))
        record = analysis.adjudicate_h1(_corpus_payload(cases))
        assert record["verdict"] == "REFUTED"
        assert record["failing_case_ids"] == ["bad"]
        assert record["breaches"]["breaching_arrays"] == {"phase_traj": 1}

    def test_aborted_case_is_excluded_from_counts(self) -> None:
        cases = [_corpus_case(f"c{i}") for i in range(503)]
        cases.append(_corpus_case("aborted", aborted=True))
        record = analysis.adjudicate_h1(_corpus_payload(cases))
        assert record["verdict"] == "INCONCLUSIVE"
        assert record["n_non_aborted"] == 503
        assert record["n_pass"] == 503
        assert record["n_fail"] == 0
        assert record["abort_reasons"] == ["nan-guard"]


class TestH2a:
    """H2a adjudication, including its confirmatory-batch precondition."""

    def test_confirmed_over_the_registered_batch(self) -> None:
        cases = [
            {**_corpus_case(f"c{i}"), "case_index": i, "n_steps": 30}
            for i in range(1000)
        ]
        record = analysis.adjudicate_h2a(_fuzz_payload(cases))
        assert record["verdict"] == "CONFIRMED"
        assert record["full_denominator"] == 1000

    def test_breach_refutes(self) -> None:
        cases = [
            {**_corpus_case(f"c{i}"), "case_index": i, "n_steps": 30}
            for i in range(999)
        ]
        cases.append(
            {
                **_corpus_case("bad", ok=False, abs_diff=1.0),
                "case_index": 999,
                "n_steps": 30,
            }
        )
        record = analysis.adjudicate_h2a(_fuzz_payload(cases))
        assert record["verdict"] == "REFUTED"
        assert record["failing_case_indices"] == [999]

    def test_non_confirmatory_batch_is_rejected(self) -> None:
        payload = _fuzz_payload([], requested=10)
        payload["config"]["fuzz_batch_class"] = "exploratory"
        with pytest.raises(analysis.AnalysisError, match="confirmatory"):
            analysis.adjudicate_h2a(payload)


class TestH3:
    """H3 bit-identity adjudication."""

    @staticmethod
    def _case(case_id: str, *, identical: bool = True) -> dict[str, Any]:
        return {
            "aborted": False,
            "case_id": case_id,
            "bit_identical": identical,
            "mismatched_arrays": [] if identical else ["phase_traj"],
        }

    def test_confirmed_at_fourteen(self) -> None:
        cases = [self._case(f"c{i}") for i in range(14)]
        record = analysis.adjudicate_h3(_corpus_payload(cases))
        assert record["verdict"] == "CONFIRMED"
        assert record["n_pass"] == 14

    def test_mismatch_refutes_and_names_the_arrays(self) -> None:
        cases = [self._case(f"c{i}") for i in range(13)]
        cases.append(self._case("bad", identical=False))
        record = analysis.adjudicate_h3(_corpus_payload(cases))
        assert record["verdict"] == "REFUTED"
        assert record["mismatched_arrays"] == {"bad": ["phase_traj"]}

    def test_short_clean_run_is_inconclusive(self) -> None:
        record = analysis.adjudicate_h3(_corpus_payload([self._case("c0")]))
        assert record["verdict"] == "INCONCLUSIVE"


class TestH4:
    """H4 adjudication, including the registered build-configuration branch."""

    @staticmethod
    def _payload(cases: list[dict[str, Any]], backend: str = "cuda") -> dict[str, Any]:
        return {
            "cases": cases,
            "config": {},
            "environment": {
                "git_commit": analysis.EXECUTION_COMMIT,
                "backend": backend,
                "gpu": "NVIDIA GeForce RTX 4060",
                "gpu_vram_mb": 8188,
            },
        }

    def test_confirmed_at_seventy_two_on_cuda(self) -> None:
        cases = [_corpus_case(f"c{i}") for i in range(72)]
        record = analysis.adjudicate_h4(self._payload(cases))
        assert record["verdict"] == "CONFIRMED"
        assert record["backend"] == "cuda"

    def test_non_cuda_backend_is_inconclusive_never_refuted(self) -> None:
        cases = [_corpus_case(f"c{i}", ok=False, abs_diff=1.0) for i in range(72)]
        record = analysis.adjudicate_h4(self._payload(cases, backend="cpu"))
        assert record["verdict"] == "INCONCLUSIVE"
        assert "cuda feature not built" in record["note"]

    def test_empty_cuda_run_is_inconclusive(self) -> None:
        record = analysis.adjudicate_h4(self._payload([]))
        assert record["verdict"] == "INCONCLUSIVE"

    def test_breach_on_cuda_refutes(self) -> None:
        cases = [_corpus_case(f"c{i}") for i in range(71)]
        cases.append(_corpus_case("bad", ok=False, abs_diff=1e-5))
        record = analysis.adjudicate_h4(self._payload(cases))
        assert record["verdict"] == "REFUTED"


class TestD1Flag:
    """Any REFUTED C1 hypothesis raises the campaign plan §10.4 D1 flag."""

    def test_all_confirmed_raises_nothing(self) -> None:
        assert not analysis.is_d1({"H1": {"verdict": "CONFIRMED"}})

    def test_inconclusive_alone_raises_nothing(self) -> None:
        assert not analysis.is_d1({"H4": {"verdict": "INCONCLUSIVE"}})

    def test_a_single_refutation_raises_it(self) -> None:
        assert analysis.is_d1(
            {"H1": {"verdict": "CONFIRMED"}, "H2a": {"verdict": "REFUTED"}}
        )


class TestProvenanceGuard:
    """An artefact from another code SHA can never feed the analysis."""

    def test_wrong_commit_fails_closed(self, tmp_path: Path) -> None:
        from tools.reproduce import compute_sha256

        leg = analysis.RUN_LEGS[0]
        run_dir = tmp_path / analysis.RAW_ARTEFACT_ROOT / leg.run_id
        run_dir.mkdir(parents=True)
        payload = _corpus_payload([_corpus_case("c0")])
        payload["environment"]["git_commit"] = "0" * 40
        artefact = run_dir / leg.artefact
        artefact.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
        # Written directly rather than via tools.reproduce.append_manifest,
        # whose own ALLOWED_MANIFEST_ROOTS would reject a pytest basetemp
        # located inside the repository (`--basetemp=.pytest_basetemp`).
        manifest = {
            "schema_version": 1,
            "files": [
                {
                    "path": artefact.name,
                    "bytes": artefact.stat().st_size,
                    "sha256": compute_sha256(artefact),
                }
            ],
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8", newline="\n"
        )
        with pytest.raises(analysis.AnalysisError, match="registered execution commit"):
            analysis._load_artefact(tmp_path, leg)


class TestOutputContainment:
    """Write destinations are confined to the governed output roots."""

    def test_permitted_roots_are_the_governed_three(self, tmp_path: Path) -> None:
        roots = analysis.allowed_output_roots(tmp_path)
        assert (tmp_path / analysis.OUTPUT_ROOT).resolve() in roots
        assert (tmp_path / analysis.RECORD_ROOT).resolve() in roots

    def test_a_destination_outside_every_root_is_refused(self, tmp_path: Path) -> None:
        roots = ((tmp_path / "allowed").resolve(),)
        with pytest.raises(analysis.AnalysisError, match="outside the permitted"):
            analysis._checked_destination(tmp_path / "elsewhere", roots, "output")

    def test_a_destination_inside_a_root_is_accepted(self, tmp_path: Path) -> None:
        roots = ((tmp_path / "allowed").resolve(),)
        accepted = analysis._checked_destination(
            tmp_path / "allowed" / "nested", roots, "output"
        )
        assert accepted == (tmp_path / "allowed" / "nested").resolve()

    def test_the_cli_refuses_an_out_of_root_output_dir(self) -> None:
        """The guard lives at the command-line boundary, not in the library.

        The escape path is a sibling of the governed output root rather than a
        ``tmp_path``: a pytest ``tmp_path`` is inside the system temporary
        directory, which *is* a permitted root, unless ``--basetemp`` moves it,
        so it would not exercise the guard reliably either way.
        """
        escape = _REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results" / "e4-guard"
        with pytest.raises(analysis.AnalysisError, match="output directory"):
            analysis.main(["--output-dir", str(escape)])
        assert not escape.exists()


@pytest.mark.skipif(
    not (_REPOSITORY_ROOT / analysis.RAW_ARTEFACT_ROOT).is_dir(),
    reason="EXP-001 raw artefacts are not present in this checkout",
)
class TestRegisteredRun:
    """End-to-end determinism and verdicts against the committed E3 artefacts."""

    def test_outputs_are_byte_identical_across_runs(self, tmp_path: Path) -> None:
        digests = []
        for index in range(2):
            out = tmp_path / f"run{index}"
            manifest = tmp_path / f"manifest{index}.json"
            analysis.run_analysis(
                _REPOSITORY_ROOT, out, manifest, analysis.GENERATED_AT
            )
            digests.append(
                [
                    (path.name, path.read_bytes())
                    for path in sorted(out.iterdir(), key=lambda p: p.name)
                ]
            )
        assert digests[0] == digests[1]

    def test_registered_verdicts(self, tmp_path: Path) -> None:
        adjudications = analysis.run_analysis(
            _REPOSITORY_ROOT,
            tmp_path / "out",
            tmp_path / "report-manifest.json",
            analysis.GENERATED_AT,
        )
        assert adjudications["H1"]["verdict"] == "REFUTED"
        assert adjudications["H2a"]["verdict"] == "REFUTED"
        assert adjudications["H2b"]["verdict"] == "CONFIRMED"
        assert adjudications["H3"]["verdict"] == "CONFIRMED"
        assert adjudications["H4"]["verdict"] == "CONFIRMED"
        assert analysis.is_d1(adjudications)

    def test_report_manifest_covers_every_output(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        manifest_path = tmp_path / "report-manifest.json"
        analysis.run_analysis(
            _REPOSITORY_ROOT, out, manifest_path, analysis.GENERATED_AT
        )
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        recorded = {entry["path"] for entry in payload["outputs"]}
        assert recorded == {path.name for path in out.iterdir()}
        assert len(payload["inputs"]) == len(analysis.RUN_LEGS)
        assert payload["d1_flag"] is True

    def test_h2b_matches_the_driver_implementation(self) -> None:
        from benchmarks.campaign.exp001_driver import adjudicate_h2b

        leg = next(leg for leg in analysis.RUN_LEGS if leg.label == "fuzz-cpu")
        payload = analysis._load_artefact(_REPOSITORY_ROOT, leg)
        direct = adjudicate_h2b(copy.deepcopy(payload["cases"]))
        through = analysis.adjudicate_h2b_leg(payload)
        assert through["verdict"] == direct["verdict"]
        assert through["metrics"] == direct["metrics"]

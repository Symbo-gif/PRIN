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
import hashlib
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


def _probe_symlink_support() -> bool:
    """True iff this process can create a symlink in a temporary directory.

    Symlink creation needs elevated privilege or Developer Mode on Windows
    (GitHub-hosted `windows-latest` runners have it; an arbitrary local or
    self-hosted Windows host may not), so symlink regression tests are
    gated on an executability probe rather than on a platform assumption —
    the same guard class as ``tests/test_reproduce.py::_probe_symlink_support``.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        target = directory / "target"
        target.write_text("x", encoding="utf-8")
        link = directory / "link"
        try:
            link.symlink_to(target)
        except OSError:
            return False
        return True


_needs_symlink_support = pytest.mark.skipif(
    not _probe_symlink_support(),
    reason="creating symlinks is not permitted in this environment",
)


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

    def test_a_self_declared_minimum_cannot_override_the_registered_one(
        self,
    ) -> None:
        """Copilot follow-up review, PR #23 head `900a68f`: the gate must be
        the frozen registered constant, not a field of the artefact being
        adjudicated.

        Before this fix, a payload could set both
        ``fuzz_batch_confirmatory_minimum`` and ``n_fuzz_cases_requested`` to
        1 and pass ``denominator < minimum`` (1 < 1 is false) — a
        self-referential check that can never reject anything, since the
        payload controls both sides of the inequality. One clean case would
        then adjudicate ``CONFIRMED``.
        """
        case = {**_corpus_case("c0"), "case_index": 0, "n_steps": 30}
        payload = _fuzz_payload([case], requested=1)
        payload["config"]["fuzz_batch_confirmatory_minimum"] = 1
        with pytest.raises(analysis.AnalysisError, match="registered minimum"):
            analysis.adjudicate_h2a(payload)

    def test_the_registered_minimum_constant_is_1000(self) -> None:
        assert analysis.REGISTERED_FUZZ_BATCH_MIN == 1000


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

    def test_load_artefact_reads_via_no_follow_not_plain_path_io(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PR23-F (Copilot follow-up review): the read after ``verify_manifest``
        must not go through ``Path.read_text`` — that follows symlinks and
        reopens the artefact independently of the no-follow verification that
        just ran, leaving a TOCTOU window a concurrent replacement could use
        to feed the analysis a different file than the one just verified.
        """
        from tools.reproduce import compute_sha256

        leg = analysis.RUN_LEGS[0]
        run_dir = tmp_path / analysis.RAW_ARTEFACT_ROOT / leg.run_id
        run_dir.mkdir(parents=True)
        payload = _corpus_payload([_corpus_case("c0")])
        artefact = run_dir / leg.artefact
        artefact.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
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

        def _forbidden(*_args: object, **_kwargs: object) -> str | bytes:
            raise AssertionError(
                "must not read the artefact through a link-following Path call"
            )

        # Both read_text and read_bytes: a prior version of this test only
        # forbade read_text, so a regression to the equally link-following
        # read_bytes would still have passed (independent reviews, PR #23
        # head `754272a`).
        monkeypatch.setattr(Path, "read_text", _forbidden)
        monkeypatch.setattr(Path, "read_bytes", _forbidden)

        result = analysis._load_artefact(tmp_path, leg)
        assert result["environment"]["git_commit"] == analysis.EXECUTION_COMMIT

    def test_load_artefact_rejects_a_swap_between_verification_and_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Independent reviews (PR #23 head `754272a`): ``verify_manifest``
        proves the run directory matched its manifest at the moment it ran;
        a second, unverified read on the same path afterward proves only
        that the reopened file is not a symlink, not that its content is
        still the verified bytes. A concurrent regular-file replacement in
        that window — restored afterward or not — would previously have
        been fed straight into the analysis undetected. Simulated here by
        swapping the artefact's content as a side effect of the (otherwise
        successful) ``verify_manifest`` call itself, the earliest possible
        point after verification and before the read that follows it.
        """
        from tools.reproduce import ManifestMismatchError, compute_sha256

        leg = analysis.RUN_LEGS[0]
        run_dir = tmp_path / analysis.RAW_ARTEFACT_ROOT / leg.run_id
        run_dir.mkdir(parents=True)
        payload = _corpus_payload([_corpus_case("c0")])
        artefact = run_dir / leg.artefact
        artefact.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
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

        real_verify_manifest = analysis.verify_manifest

        def _swap_after_verify(*args: object, **kwargs: object) -> object:
            records = real_verify_manifest(*args, **kwargs)
            artefact.write_text('{"swapped": true}', encoding="utf-8", newline="\n")
            return records

        monkeypatch.setattr(analysis, "verify_manifest", _swap_after_verify)

        with pytest.raises(ManifestMismatchError):
            analysis._load_artefact(tmp_path, leg)


class TestOutputContainment:
    """Write destinations are confined to the governed output roots."""

    def test_permitted_roots_are_the_governed_three(self, tmp_path: Path) -> None:
        roots = analysis.allowed_output_roots(tmp_path)
        assert (tmp_path / analysis.OUTPUT_ROOT).resolve() in roots
        assert (tmp_path / analysis.RECORD_ROOT).resolve() in roots

    @_needs_symlink_support
    def test_allowed_output_roots_refuses_a_symlinked_output_root(
        self, tmp_path: Path
    ) -> None:
        """Independent reviews (PR #23 head `754272a`): a symlinked
        ``OUTPUT_ROOT`` must be refused, not silently resolved to whatever
        it points at — otherwise the "permitted root" a later write is
        checked against could transitively become the frozen record root.
        """
        (tmp_path / analysis.RECORD_ROOT).mkdir(parents=True)
        output_root = tmp_path / analysis.OUTPUT_ROOT
        output_root.parent.mkdir(parents=True, exist_ok=True)
        output_root.symlink_to(
            tmp_path / analysis.RECORD_ROOT, target_is_directory=True
        )

        with pytest.raises(analysis.AnalysisError, match="symbolic link"):
            analysis.allowed_output_roots(tmp_path)

    @_needs_symlink_support
    def test_allowed_output_roots_refuses_a_symlinked_record_root(
        self, tmp_path: Path
    ) -> None:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        record_root = tmp_path / analysis.RECORD_ROOT
        record_root.parent.mkdir(parents=True, exist_ok=True)
        record_root.symlink_to(elsewhere, target_is_directory=True)

        with pytest.raises(analysis.AnalysisError, match="symbolic link"):
            analysis.allowed_output_roots(tmp_path)

    @_needs_symlink_support
    def test_allowed_generated_output_dirs_refuses_a_symlinked_output_root(
        self, tmp_path: Path
    ) -> None:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        output_root = tmp_path / analysis.OUTPUT_ROOT
        output_root.parent.mkdir(parents=True, exist_ok=True)
        output_root.symlink_to(elsewhere, target_is_directory=True)

        with pytest.raises(analysis.AnalysisError, match="symbolic link"):
            analysis.allowed_generated_output_dirs(tmp_path)

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

    def test_generated_output_dirs_exclude_the_record_root(
        self, tmp_path: Path
    ) -> None:
        """PR23-F: ``--output-dir`` must not be able to write into the record.

        ``allowed_output_roots`` (used for the manifest destination) still
        includes the record root, but ``allowed_generated_output_dirs`` (used
        for ``--output-dir``) must not — otherwise a caller could redirect the
        generated summary/adjudication files into the frozen record.
        """
        record_root = (tmp_path / analysis.RECORD_ROOT).resolve()
        dirs = analysis.allowed_generated_output_dirs(tmp_path)
        assert record_root not in dirs
        assert (tmp_path / analysis.OUTPUT_ROOT).resolve() in dirs

    def test_the_cli_refuses_an_output_dir_inside_the_record_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A caller may not redirect generated files into the frozen record.

        Exercised against a sandboxed fake checkout (``_REPOSITORY_ROOT``
        monkeypatched), never the real repository — if this guard ever
        regresses, the test must fail cleanly, not write into this
        module's own committed record root.
        """
        monkeypatch.setattr(analysis, "_REPOSITORY_ROOT", tmp_path)
        escape = tmp_path / analysis.RECORD_ROOT
        escape.mkdir(parents=True)
        with pytest.raises(analysis.AnalysisError, match="output directory"):
            analysis.main(["--output-dir", str(escape)])
        assert list(escape.iterdir()) == []

    def test_the_cli_refuses_a_manifest_path_misnamed_in_the_record_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """``--manifest-path`` may only name ``report-manifest.json`` there.

        Without this guard, ``--manifest-path`` pointing at ``report.md`` or
        ``preregistration.md`` inside the record root would let
        ``write_report_manifest`` silently overwrite the frozen E5 record.
        Exercised against a sandboxed fake checkout, never the real
        repository files.
        """
        monkeypatch.setattr(analysis, "_REPOSITORY_ROOT", tmp_path)
        record_root = tmp_path / analysis.RECORD_ROOT
        record_root.mkdir(parents=True)
        escape = record_root / "report.md"
        escape.write_bytes(b"frozen record\n")

        with pytest.raises(analysis.AnalysisError, match=r"report-manifest.json"):
            analysis.main(["--manifest-path", str(escape)])
        assert escape.read_bytes() == b"frozen record\n"

    def test_checked_manifest_destination_accepts_the_canonical_name(
        self, tmp_path: Path
    ) -> None:
        record_root = (tmp_path / "record").resolve()
        record_root.mkdir()
        destination = record_root / "report-manifest.json"
        accepted = analysis._checked_manifest_destination(
            destination, (record_root,), record_root
        )
        assert accepted == destination

    def test_checked_manifest_destination_rejects_other_names(
        self, tmp_path: Path
    ) -> None:
        record_root = (tmp_path / "record").resolve()
        record_root.mkdir()
        with pytest.raises(analysis.AnalysisError, match=r"report-manifest.json"):
            analysis._checked_manifest_destination(
                record_root / "report.md", (record_root,), record_root
            )

    def test_checked_manifest_destination_rejects_nested_paths(
        self, tmp_path: Path
    ) -> None:
        """CodeRabbit follow-up review, PR #23 head `d9d4f2a`: a destination
        *nested* under the record root — such as this module's own source at
        ``analysis/exp001_e4_analysis.py`` — must be rejected too, not just a
        misnamed direct child. The prior check only compared
        ``resolved.parent == record_root``, so a nested path slipped through.
        """
        record_root = (tmp_path / "record").resolve()
        (record_root / "analysis").mkdir(parents=True)
        with pytest.raises(analysis.AnalysisError, match=r"report-manifest.json"):
            analysis._checked_manifest_destination(
                record_root / "analysis" / "exp001_e4_analysis.py",
                (record_root,),
                record_root,
            )

    def test_the_cli_refuses_a_manifest_path_nested_in_the_record_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Same defect, exercised through the CLI boundary rather than the
        unit-level helper, against a sandboxed fake checkout.
        """
        monkeypatch.setattr(analysis, "_REPOSITORY_ROOT", tmp_path)
        nested_dir = tmp_path / analysis.RECORD_ROOT / "analysis"
        nested_dir.mkdir(parents=True)
        escape = nested_dir / "exp001_e4_analysis.py"
        escape.write_bytes(b"# source\n")

        with pytest.raises(analysis.AnalysisError, match=r"report-manifest.json"):
            analysis.main(["--manifest-path", str(escape)])
        assert escape.read_bytes() == b"# source\n"

    def test_the_cli_refuses_a_manifest_path_colliding_with_a_generated_output(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Independent review (PR #23 head `949e5e1`): `allowed_output_roots`
        permits `--manifest-path` anywhere under `--output-dir` (neither
        generated file is immutable on its own), but a `--manifest-path`
        that names exactly one of `write_outputs`' own filenames would have
        `write_report_manifest` overwrite it after `write_outputs` already
        recorded its digest — the committed manifest would then describe
        bytes no longer on disk. Exercised against a sandboxed fake
        checkout.
        """
        monkeypatch.setattr(analysis, "_REPOSITORY_ROOT", tmp_path)
        output_dir = tmp_path / analysis.OUTPUT_ROOT
        colliding = output_dir / analysis.SUMMARY_FILENAME

        with pytest.raises(
            analysis.AnalysisError, match="collides with a generated output"
        ):
            analysis.main(
                ["--output-dir", str(output_dir), "--manifest-path", str(colliding)]
            )
        assert not output_dir.exists()


class TestReportManifestIntegrity:
    """Independent reviews, PR #23 head `754272a`: the integrity fields
    recorded for each generated output must be exactly what
    :func:`write_outputs` computed from the bytes it wrote, and
    ``write_report_manifest`` must never reopen the output path to
    second-guess them — reopening leaves a window in which a concurrent
    regular-file replacement between ``write_outputs`` and this call is
    recorded as if it were the generated output's own bytes (TOCTOU,
    CWE-59).

    A prior version of this test pinned that contract by globally
    monkeypatching ``pathlib.Path.stat`` for the whole process. That also
    broke ``tools.reproduce``'s own legitimate no-follow ``is_symlink()``
    pre-open check on Windows Python <=3.13, where ``Path.lstat()``
    delegates to ``Path.stat(follow_symlinks=False)``: the patch turned an
    unrelated internal call into an ``AssertionError``, and pytest's own
    failure-reporting machinery then hit the same patch a second time while
    formatting that failure, escalating it to a session-ending
    ``INTERNALERROR`` on every required Windows leg (Copilot follow-up
    review, PR #23 head `900a68f`; independent reviews, PR #23 head
    `754272a`). The contract is instead pinned by construction below: the
    output path is never even created on disk, so any reopen would raise
    ``FileNotFoundError`` rather than silently succeeding.
    """

    def test_write_report_manifest_never_reads_its_output_paths(
        self, tmp_path: Path
    ) -> None:
        # Deliberately never created: if write_report_manifest reopened it
        # for its integrity fields, this would raise FileNotFoundError.
        summary = tmp_path / "out" / "exp001-e4-summary.md"
        given = analysis.GeneratedOutput(
            path=summary, bytes=6, sha256=hashlib.sha256(b"hello\n").hexdigest()
        )

        manifests: dict[str, list[dict[str, Any]]] = {
            leg.label: [] for leg in analysis.RUN_LEGS
        }
        manifest_path = tmp_path / "report-manifest.json"
        record = analysis.write_report_manifest(
            [given],
            manifests,
            manifest_path,
            analysis.GENERATED_AT,
            {"H1": {"verdict": "CONFIRMED"}},
        )

        assert record["outputs"] == [
            {
                "path": "exp001-e4-summary.md",
                "bytes": given.bytes,
                "sha256": given.sha256,
            }
        ]


class TestSafeTempRoot:
    """CodeRabbit follow-up review, PR #23 head `d9d4f2a`: the temp-directory
    allowance must not transitively legitimize the checkout itself.
    """

    def test_temp_root_included_when_disjoint_from_the_checkout(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        checkout = tmp_path / "checkout"
        checkout.mkdir()
        elsewhere = tmp_path / "elsewhere-temp"
        elsewhere.mkdir()
        monkeypatch.setattr(analysis.tempfile, "gettempdir", lambda: str(elsewhere))

        assert analysis._safe_temp_root(checkout) == (elsewhere.resolve(),)

    def test_temp_root_excluded_when_the_checkout_is_inside_it(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fake_temp_root = tmp_path / "tmp"
        fake_temp_root.mkdir()
        checkout = fake_temp_root / "some" / "nested" / "checkout"
        checkout.mkdir(parents=True)
        monkeypatch.setattr(
            analysis.tempfile, "gettempdir", lambda: str(fake_temp_root)
        )

        assert analysis._safe_temp_root(checkout) == ()

    def test_temp_root_excluded_when_the_checkout_is_the_temp_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(analysis.tempfile, "gettempdir", lambda: str(tmp_path))
        assert analysis._safe_temp_root(tmp_path) == ()


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
        # write_report_manifest records write_outputs's in-memory digest,
        # not a reopen (TestReportManifestIntegrity); confirm here, against
        # the real registered outputs, that it still matches what actually
        # landed on disk.
        for entry in payload["outputs"]:
            on_disk = (out / entry["path"]).read_bytes()
            assert entry["bytes"] == len(on_disk)
            assert entry["sha256"] == hashlib.sha256(on_disk).hexdigest()

    def test_h2b_matches_the_driver_implementation(self) -> None:
        from benchmarks.campaign.exp001_driver import adjudicate_h2b

        leg = next(leg for leg in analysis.RUN_LEGS if leg.label == "fuzz-cpu")
        payload = analysis._load_artefact(_REPOSITORY_ROOT, leg)
        direct = adjudicate_h2b(copy.deepcopy(payload["cases"]))
        through = analysis.adjudicate_h2b_leg(payload)
        assert through["verdict"] == direct["verdict"]
        assert through["metrics"] == direct["metrics"]

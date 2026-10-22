"""Tests for the committed EXP-002-r1 E4 analysis module.

The module lives under the experiment's record root (campaign plan section 7.4
item 2), whose directory name is not a Python identifier, so it is loaded by
path. Every fixture is synthetic: a throw-away git repository holding a fake
approved protocol, a 172-name reference ``__all__``, ownership tables, 172
fabricated frozen inputs and five driver-shaped run records. No test reads an
observation of the real E3 records; one test hashes their bytes to pin the
run index, without parsing them.

The tests pin the frozen decision rules (pre-registration sections 4.1, 5.2,
5.4, 5.5 and 11.3): every valid-counterexample and coverage branch of H1-H4,
both H3 policies, the H4 canonical projection, the D1 flag, admissibility of
tampered, missing, extra, aborted and linked records and inputs, output
confinement and byte-for-byte determinism. The driver is imported here (never
by the module) to prove the fixtures and the H2 re-derivation are driver-shaped.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from benchmarks.campaign import exp002_driver as driver

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = (
    _REPOSITORY_ROOT
    / "DOCS"
    / "experiments"
    / "EXP-002-r1-api-benchmark-result-and-reproduction-parity"
    / "analysis"
    / "exp002_r1_e4_analysis.py"
)


def _load_module() -> Any:
    """Load the analysis module by path (its directory is not importable)."""
    spec = importlib.util.spec_from_file_location("exp002_r1_e4_analysis", _MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analysis = _load_module()

_GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_AUTHOR_NAME": "synthetic",
    "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
    "GIT_COMMITTER_NAME": "synthetic",
    "GIT_COMMITTER_EMAIL": "synthetic@example.invalid",
    "GIT_AUTHOR_DATE": "2026-10-21T00:00:00Z",
    "GIT_COMMITTER_DATE": "2026-10-21T00:00:00Z",
}
PROTOCOL = (
    "# Synthetic EXP-002-r1 protocol\n\n"
    "**Status:** APPROVED\n"
    "**Maintainer approval:** MichaelMaillet, 2026-10-21 UTC - synthetic\n"
)
LEGACY = tuple(f"Legacy{index:03d}" for index in range(172))
EXPECTED = sorted(set(LEGACY) | set(analysis.PRIN_ADDITIONS))


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=repo,
        env=_GIT_ENV,
        capture_output=True,
        check=True,
        timeout=60,
    )
    return result.stdout.decode("utf-8").strip()


def _write(path: Path, payload: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload.encode("utf-8") if isinstance(payload, str) else payload)


def _guide(names: tuple[str, ...]) -> str:
    rows = "".join(f'   "{name}", "prin.{name}", "real", "0141A"\n' for name in names)
    return (
        "Migration Guide\n\n.. wp036-consolidated-table-begin\n\n"
        ".. csv-table:: index\n\n" + rows + "\n.. wp036-consolidated-table-end\n"
    )


def _baseline(names: tuple[str, ...]) -> str:
    rows = "".join(f"| prinet | {name} | WP-036 | owned |\n" for name in names)
    return "| Package | Name | WP | Note |\n|---|---|---|---|\n" + rows


def _commit_sources(
    repo: Path,
    guide_names: tuple[str, ...] = LEGACY,
    baseline_names: tuple[str, ...] = LEGACY,
    rc1: tuple[str, ...] = tuple(EXPECTED),
) -> str:
    _write(repo / analysis.REFERENCE_API_PATH, f"__all__ = {list(LEGACY)!r}\n")
    _write(
        repo / analysis.PUBLIC_API_PATH,
        f"RC1_PUBLIC_API: tuple[str, ...] = {rc1!r}\n",
    )
    _write(
        repo / analysis.DEPRECATION_PATH,
        "FROZEN_PUBLIC_API = frozenset(RC1_PUBLIC_API)\n",
    )
    _write(repo / analysis.MIGRATION_GUIDE_PATH, _guide(guide_names))
    _write(repo / analysis.OWNERSHIP_BASELINE_PATH, _baseline(baseline_names))
    _write(repo / analysis.PRIN_CORE_PYD_PATH, b"synthetic pyd binary content\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "sources", "--allow-empty")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="session")
def base_repo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    """A git repository with the frozen protocol commit F and the source R."""
    repo = tmp_path_factory.mktemp("exp002-r1-e4-base") / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(repo / analysis.PROTOCOL_PATH, PROTOCOL)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "protocol")
    freeze = _git(repo, "rev-parse", "HEAD")
    source = _commit_sources(repo)
    return repo, freeze, source


def conclusion_docs() -> dict[str, Any]:
    """Synthetic frozen H2 inputs in which every registered prediction holds."""
    grid = []
    for index in range(42):
        bc = 0.6 if index % 2 == 0 else 0.5
        grid.append(
            {
                "K": 1.0 + index // 6,
                "alpha": 0.1 * (index % 6),
                "bc_mean": bc,
                "chimera_detected": bc > 0.555,
            }
        )

    def zone(regime: str, width: float, onset: float) -> dict[str, Any]:
        return {"device": "cpu", "regime": regime, "zone_width": width, "K_c": onset}

    return {
        "phase1_chimera_seeds.json": {
            "bimodality_coefficient": {
                "n_sequences": 5,
                "raw_values": [0.6, 0.61, 0.62, 0.63, 0.64],
            }
        },
        "benchmark_y4q1_3_k_alpha_sensitivity.json": {"grid": grid},
        "phase2_chimera_nsweep.json": {
            "sweep": [
                {"n_oscillators": n, "bc_stats": {"mean": 0.7}}
                for n in (128, 256, 512, 1024)
            ]
        },
        "y4q1_8_topology_comparison.json": {
            "topologies": {
                "ring": {"bc_mean": 0.8, "bc_ci": {"ci_width": 0.3}},
                "2community": {"bc_mean": 0.6, "bc_ci": {"ci_width": 0.2}},
                "4community": {"bc_mean": 0.5, "bc_ci": {"ci_width": 0.1}},
            }
        },
        "y3q49_goldilocks_zones.json": {
            "zones": {
                "csr_cpu": zone("csr", 5.0, 2.0),
                "full_cpu": zone("full", 1.0, 1.0),
                "mean_field_cpu": zone("mean_field", 2.0, 3.0),
                "sparse_knn_cpu": zone("sparse_knn", 3.0, 4.0),
                "csr_cuda": {"device": "cuda", "regime": "csr", "zone_width": 99.0},
            }
        },
    }


def api_observations() -> dict[str, Any]:
    """A driver-shaped ``api`` observation in which every H1 condition holds."""
    rows = []
    for name in EXPECTED:
        constant = name == "__version__"
        rows.append(
            {
                "name": name,
                "resolved": True,
                "callable": not constant,
                "defining_module": None if constant else "prin.synthetic",
                "type": "str" if constant else "function",
                "error": None,
                "legacy": name in LEGACY,
                "ownership_present": True,
            }
        )
    return {
        "expected_names": list(EXPECTED),
        "legacy_names": sorted(LEGACY),
        "observed_names": list(reversed(EXPECTED)),
        "frozen_missing": [],
        "frozen_extra": [],
        "rows": rows,
        "unit": "api_symbol",
    }


def _sync_frozen(observations: dict[str, Any], rc1: Any = None) -> None:
    """Recompute the frozen-contract sets as ``verify_api_surface`` would."""
    contract = set(EXPECTED if rc1 is None else rc1)
    observed = set(observations["observed_names"])
    observations["frozen_missing"] = sorted(contract - observed)
    observations["frozen_extra"] = sorted(observed - contract)


def _digest(text: str) -> str:
    return _sha(text.encode("utf-8"))


def file_record(implementation: str, path: str, index: int) -> dict[str, Any]:
    """One driver-shaped publication file record (all policies equal by default)."""
    table = path.endswith(".tex")
    raw = _digest(f"raw:{path}" if table else f"{implementation}-raw:{path}")
    normalized = _digest(f"normalized:{path}")
    sensitivity = {
        ".tex": raw,
        ".png": normalized,
        ".pdf": _digest(f"sensitivity:{path}"),
    }[Path(path).suffix]
    record: dict[str, Any] = {
        "path": path,
        "raw_bytes": 1000 + index,
        "raw_sha256": raw,
        "normalized_bytes": 900 + index,
        "normalized_sha256": normalized,
        "sensitivity_bytes": 1000 + index if table else 950 + index,
        "sensitivity_sha256": sensitivity,
    }
    if table:
        record["sensitivity_bytes"] = record["raw_bytes"]
        record["normalized_bytes"] = record["raw_bytes"]
        record.update(
            {
                "archived_bytes": record["raw_bytes"],
                "archived_sha256": raw,
                "archived_normalized_bytes": record["normalized_bytes"],
                "archived_normalized_sha256": normalized,
            }
        )
    if Path(path).suffix == ".png":
        record["sensitivity_bytes"] = record["normalized_bytes"]
    return record


def publication(implementation: str) -> dict[str, Any]:
    """A driver-shaped publication observation with all 39 registered files."""
    return {
        "implementation": implementation,
        "renderer": {
            "font_cache": {"name": "fontlist-v3.json", "sha256": _digest("cache")},
            "matplotlib": "3.11.1",
            "numpy": "2.5.1",
            "pillow": "12.3.0",
            "freetype": "2.14.3",
            "backend": "Agg",
            "font_sha256": {"DejaVuSans.ttf": _digest("font")},
        },
        "expected_files": list(analysis.REGISTERED_FILES),
        "files": [
            file_record(implementation, path, index)
            for index, path in enumerate(analysis.REGISTERED_FILES)
        ],
        "unit": "generated_file",
    }


class Builder:
    """Writes synthetic inputs and records into a copy of the base repository."""

    def __init__(self, repo: Path, freeze: str, source: str) -> None:
        self.repo, self.freeze, self.source = repo, freeze, source
        self.docs = conclusion_docs()
        self.observations: dict[str, Any] = {
            "api": api_observations(),
            "reference": publication("reference"),
            "prin": publication("prin"),
            "repeatability": publication("prin"),
        }
        self.result_mutators: dict[str, Callable[[dict[str, Any]], None]] = {}
        self.sidecar_mutators: dict[str, Callable[[dict[str, Any]], None]] = {}
        self.input_mutator: Callable[[Path], None] | None = None
        self.base_context: Any = None

    def run_id(self, mode: str) -> str:
        """Registered-shape run ID for ``mode`` at the synthetic source."""
        stamp = f"20261021T21{analysis.MODE_ORDER.index(mode):02d}00Z"
        return f"RUN-{stamp}-{self.source[:7]}-{analysis.MODES[mode][0]}"

    def _inputs(self) -> tuple[str, list[dict[str, Any]]]:
        results = self.repo / analysis.REFERENCE_RESULTS
        results.mkdir(parents=True, exist_ok=True)
        for name, document in self.docs.items():
            _write(results / name, json.dumps(document, indent=2))
        for index in range(172 - len(self.docs)):
            _write(results / f"filler_{index:03d}.json", json.dumps({"i": index}))
        if self.input_mutator is not None:
            self.input_mutator(results)
        records = [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha(path.read_bytes()),
            }
            for path in sorted(results.glob("*.json"))
        ]
        manifest = json.dumps(
            {"schema_version": 1, "description": "d", "source": "s", "files": records},
            indent=2,
        )
        _write(self.repo / analysis.INPUT_MANIFEST_PATH, manifest)
        return _sha(manifest.encode("utf-8")), records

    def _record(
        self, mode: str, input_records: list[dict[str, Any]], manifest_sha: str
    ) -> Any:
        run_id = self.run_id(mode)
        minute = analysis.MODE_ORDER.index(mode)
        run_dir = self.repo / analysis.RAW_ROOT / run_id
        run_dir.mkdir(parents=True)
        if mode == "conclusions":
            observations = driver.collect_conclusions(self.docs)
        else:
            observations = copy.deepcopy(self.observations[mode])
        result = {
            "environment": {
                "prin_version": "1.0.0rc1",
                "git_commit": self.source,
                "rust_version": "rustc 1.99.0",
                "python_version": "3.14.0",
                "platform": "Windows-11",
                "processor": "AMD64",
                "logical_cpus": 16,
                "gpu": None,
                "gpu_vram_mb": None,
                "backend": "cpu",
                "dtype": "f64",
                "seed": 0,
            },
            "config": {
                "iterations": 10,
                "warmup": 0,
                "seed_counter": 0,
                "seed_key": 2,
                "out_dir": str(run_dir),
                "measurement_kind": "deterministic_census",
                "replicates": 1,
            },
            "identity": {
                "source_sha": self.source,
                "preregistration_sha256": _sha(PROTOCOL.encode("utf-8")),
                "preregistration_commit": self.freeze,
                "approval_date_utc": "2026-10-21",
                "input_manifest_sha256": manifest_sha,
                "input_record_count": 172,
                "input_records": input_records,
                "prin_core_pyd_bytes": (self.repo / analysis.PRIN_CORE_PYD_PATH)
                .stat()
                .st_size,
                "prin_core_pyd_sha256": _sha(
                    (self.repo / analysis.PRIN_CORE_PYD_PATH).read_bytes()
                ),
            },
            "seed_used": False,
            "observations": observations,
            "status": "COMPLETED",
            "elapsed_seconds": 1.25,
            "started_at_utc": f"2026-10-21T21:{minute:02d}:01+00:00",
            "recorded_at_utc": f"2026-10-21T21:{minute:02d}:02+00:00",
        }
        mutate = self.result_mutators.get(mode)
        if mutate is not None:
            mutate(result)
        result_name = analysis.MODES[mode][1]
        sidecar = {
            "exp_id": "EXP-002-r1",
            "session": "EXP-002-r1-E3",
            "run_id": run_id,
            "operator": "MichaelMaillet",
            "mode": mode,
            "artefacts": {result_name: list(analysis.MODES[mode][2])},
        }
        mutate = self.sidecar_mutators.get(mode)
        if mutate is not None:
            mutate(sidecar)
        result_bytes = json.dumps(result, indent=2).encode("utf-8")
        sidecar_bytes = json.dumps(sidecar, indent=2).encode("utf-8")
        _write(run_dir / result_name, result_bytes)
        _write(run_dir / analysis.SIDECAR, sidecar_bytes)
        entries = sorted(
            [
                {
                    "path": analysis.SIDECAR,
                    "bytes": len(sidecar_bytes),
                    "sha256": _sha(sidecar_bytes),
                },
                {
                    "path": result_name,
                    "bytes": len(result_bytes),
                    "sha256": _sha(result_bytes),
                },
            ],
            key=lambda entry: entry["path"],
        )
        manifest = json.dumps(
            {"schema_version": 1, "description": "d", "source": "s", "files": entries},
            indent=2,
        ).encode("utf-8")
        _write(run_dir / analysis.MANIFEST, manifest)
        return analysis.RunSpec(
            mode=mode,
            run_id=run_id,
            result_sha256=_sha(result_bytes),
            manifest_sha256=_sha(manifest),
            sidecar_sha256=_sha(sidecar_bytes),
        )

    def write(self) -> Any:
        """Write inputs and records; return the matching registration."""
        manifest_sha, records = self._inputs()
        _write(self.repo / analysis.RAW_ROOT / "README.md", "raw root\n")
        specs = tuple(
            self._record(mode, records, manifest_sha) for mode in analysis.MODE_ORDER
        )
        pyd_bytes = (self.repo / "python" / "prin" / "_prin_core.pyd").read_bytes()
        return analysis.Registration(
            source_sha=self.source,
            protocol_commit=self.freeze,
            protocol_sha256=_sha(PROTOCOL.encode("utf-8")),
            approval_date_utc="2026-10-21",
            input_manifest_sha256=manifest_sha,
            reference_api_sha256=_sha(
                (self.repo / analysis.REFERENCE_API_PATH).read_bytes()
            ),
            public_api_sha256=_sha((self.repo / analysis.PUBLIC_API_PATH).read_bytes()),
            deprecation_sha256=_sha(
                (self.repo / analysis.DEPRECATION_PATH).read_bytes()
            ),
            prin_core_pyd_bytes=len(pyd_bytes),
            prin_core_pyd_sha256=_sha(pyd_bytes),
            runs=specs,
        )


@pytest.fixture(scope="session")
def base_context(
    tmp_path_factory: pytest.TempPathFactory, base_repo: tuple[Path, str, str]
) -> Any:
    """A context verified once over the default synthetic inputs.

    Record-level tests reuse it (with their own repository root and run
    index) so that each does not re-spawn the global git queries; every global
    precondition is exercised by the tests that call ``run_analysis``.
    """
    source_repo, freeze, source = base_repo
    repo = tmp_path_factory.mktemp("exp002-r1-e4-context") / "repo"
    shutil.copytree(source_repo, repo)
    seed = Builder(repo, freeze, source)
    return analysis.verify_context(repo, seed.write())


@pytest.fixture
def builder(
    tmp_path: Path, base_repo: tuple[Path, str, str], base_context: Any
) -> Builder:
    """A fresh copy of the base repository with default (passing) fixtures."""
    source_repo, freeze, source = base_repo
    repo = tmp_path / "repo"
    shutil.copytree(source_repo, repo)
    made = Builder(repo, freeze, source)
    made.base_context = base_context
    return made


def _run(builder: Builder) -> dict[str, Any]:
    """Run the analysis; reuse the verified context when the globals match."""
    registration = builder.write()
    context = builder.base_context
    if context is not None and dataclasses.replace(
        registration, runs=()
    ) == dataclasses.replace(context.registration, runs=()):
        fast = dataclasses.replace(
            context, repository_root=builder.repo, registration=registration
        )
        outcome: dict[str, Any] = analysis.analyse(fast)
        return outcome
    outcome = analysis.run_analysis(builder.repo, registration)
    return outcome


def _summary(builder: Builder) -> dict[str, Any]:
    summary: dict[str, Any] = _run(builder)["summary"]
    return summary


def _verdicts(builder: Builder) -> dict[str, str]:
    verdicts: dict[str, str] = _summary(builder)["verdicts"]
    return verdicts


def _output(builder: Builder, name: str) -> str:
    return (builder.repo / analysis.OUTPUT_DIR / name).read_text(encoding="utf-8")


def _row(observations: dict[str, Any], name: str) -> dict[str, Any]:
    row: dict[str, Any] = next(
        row for row in observations["rows"] if row["name"] == name
    )
    return row


def _file(observations: dict[str, Any], path: str) -> dict[str, Any]:
    record: dict[str, Any] = next(
        item for item in observations["files"] if item["path"] == path
    )
    return record


FIGURE = "figures/fig3_chimera_metrics.pdf"
PNG = "figures/fig3_chimera_metrics.png"
TABLE = "tables/tab_chimera.tex"


# ---------------------------------------------------------------------------
# Registration, isolation and fixture fidelity
# ---------------------------------------------------------------------------


def test_module_never_imports_prin_prinet_driver_or_reproduce() -> None:
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('m', {str(_MODULE_PATH)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules['m'] = module\n"
        "spec.loader.exec_module(module)\n"
        "roots = {'prin', 'prinet', 'benchmarks', 'tools', 'numpy', 'matplotlib'}\n"
        "print(sorted(k for k in sys.modules if k.split('.')[0] in roots))\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.decode().strip() == "[]"


def test_registered_populations_match_the_frozen_driver() -> None:
    assert len(analysis.REGISTERED_FILES) == analysis.GENERATED_FILE_COUNT == 39
    assert set(analysis.REGISTERED_FILES) == driver.EXPECTED_FILES
    assert len(analysis.REGISTERED_TABLES) == 11
    assert analysis.FIGURE_STEMS == driver.FIGURE_STEMS
    assert analysis.TABLE_STEMS == driver.TABLE_STEMS
    assert analysis.CONCLUSION_FILES == driver.CONCLUSION_FILES
    assert set(analysis.PRIN_ADDITIONS) == driver.PRIN_ADDITIONS
    assert analysis.API_SYMBOL_COUNT == driver.API_SYMBOL_COUNT == 175
    assert analysis.CLAIM_COMPARATOR_RECORD_COUNT == driver.CLAIM_CASE_COUNT == 62
    assert sum(analysis.FAMILY_COUNTS.values()) == 62
    for mode, (label, _result, tags) in analysis.MODES.items():
        assert f"r1-{driver.MODE_LABELS[mode]}" == label
        assert driver.MODE_TAGS[mode] == list(tags)
    assert driver._API_ROW_KEYS == analysis._API_ROW_KEYS
    assert driver._CASE_KEYS == analysis._CASE_KEYS
    assert driver.INPUT_MANIFEST_SHA == analysis.REGISTERED.input_manifest_sha256
    assert (
        driver.REFERENCE_PINS["src/prinet/__init__.py"]
        == analysis.REGISTERED.reference_api_sha256
    )


def test_registered_index_is_well_formed_and_pins_the_committed_records() -> None:
    analysis._check_registration(analysis.REGISTERED)
    raw_root = _REPOSITORY_ROOT / analysis.RAW_ROOT
    for spec in analysis.REGISTERED.runs:
        run_dir = raw_root / spec.run_id
        # Bytes are hashed only; no record is parsed or interpreted here.
        assert _sha((run_dir / spec.result_name).read_bytes()) == spec.result_sha256
        assert _sha((run_dir / analysis.MANIFEST).read_bytes()) == spec.manifest_sha256
        assert _sha((run_dir / analysis.SIDECAR).read_bytes()) == spec.sidecar_sha256


def test_registration_refuses_malformed_entries() -> None:
    good = analysis.REGISTERED
    bad_runs = (*good.runs[:4], good.runs[3])
    for registration in (
        analysis.Registration(**{**good.__dict__, "source_sha": "abc"}),
        analysis.Registration(**{**good.__dict__, "protocol_sha256": "x" * 64}),
        analysis.Registration(**{**good.__dict__, "runs": bad_runs}),
        analysis.Registration(
            **{
                **good.__dict__,
                "runs": (
                    analysis.RunSpec(**{**good.runs[0].__dict__, "run_id": "RUN-x"}),
                    *good.runs[1:],
                ),
            }
        ),
        analysis.Registration(
            **{
                **good.__dict__,
                "runs": (
                    analysis.RunSpec(**{**good.runs[0].__dict__, "result_sha256": "0"}),
                    *good.runs[1:],
                ),
            }
        ),
    ):
        with pytest.raises(analysis.AnalysisError):
            analysis._check_registration(registration)


def test_synthetic_observations_pass_the_driver_schema_check() -> None:
    driver._check_observations("api", api_observations())
    driver._check_observations(
        "conclusions", driver.collect_conclusions(conclusion_docs())
    )
    driver._check_observations("reference", publication("reference"))
    driver._check_observations("prin", publication("prin"))


@pytest.mark.parametrize("flip", [None, "C01", "C02", "C05"])
def test_claim_rederivation_equals_the_driver(flip: str | None) -> None:
    docs = conclusion_docs()
    if flip == "C01":
        docs["phase1_chimera_seeds.json"]["bimodality_coefficient"]["raw_values"][2] = (
            0.5
        )
    elif flip == "C02":
        docs["benchmark_y4q1_3_k_alpha_sensitivity.json"]["grid"][3][
            "chimera_detected"
        ] = True
    elif flip == "C05":
        docs["y3q49_goldilocks_zones.json"]["zones"]["full_cpu"]["K_c"] = 9.0
    assert (
        analysis.derive_claim_cases(docs) == driver.collect_conclusions(docs)["cases"]
    )


def test_claim_rederivation_rejects_an_invalid_frozen_schema() -> None:
    docs = conclusion_docs()
    del docs["phase2_chimera_nsweep.json"]["sweep"][0]
    with pytest.raises(analysis.AnalysisError, match="C03"):
        analysis.derive_claim_cases(docs)
    docs = conclusion_docs()
    docs["benchmark_y4q1_3_k_alpha_sensitivity.json"]["grid"][1]["K"] = 1.0
    docs["benchmark_y4q1_3_k_alpha_sensitivity.json"]["grid"][1]["alpha"] = 0.0
    with pytest.raises(analysis.AnalysisError, match="duplicate"):
        analysis.derive_claim_cases(docs)
    docs = conclusion_docs()
    docs["y3q49_goldilocks_zones.json"]["zones"]["full_cpu"]["device"] = "cuda"
    with pytest.raises(analysis.AnalysisError, match="C05"):
        analysis.derive_claim_cases(docs)
    docs = conclusion_docs()
    docs["phase1_chimera_seeds.json"]["bimodality_coefficient"]["raw_values"][0] = "x"
    with pytest.raises(analysis.AnalysisError):
        analysis.derive_claim_cases(docs)
    docs = conclusion_docs()
    values = docs["phase1_chimera_seeds.json"]["bimodality_coefficient"]["raw_values"]
    values[0] = float("nan")
    with pytest.raises(analysis.AnalysisError, match="non-finite"):
        analysis.derive_claim_cases(docs)
    docs = conclusion_docs()
    del docs["benchmark_y4q1_3_k_alpha_sensitivity.json"]["grid"][0]["bc_mean"]
    with pytest.raises(analysis.AnalysisError, match="schema invalid"):
        analysis.derive_claim_cases(docs)


# ---------------------------------------------------------------------------
# Baseline: every registered prediction holds
# ---------------------------------------------------------------------------


def test_all_hypotheses_confirmed_on_passing_fixtures(builder: Builder) -> None:
    outcome = _run(builder)
    summary = outcome["summary"]
    assert summary["verdicts"] == {
        "H1": "CONFIRMED",
        "H2": "CONFIRMED",
        "H3": "CONFIRMED",
        "H4": "CONFIRMED",
        "H3_sensitivity_policy": "CONFIRMED",
    }
    assert summary["d1_flag"] is False
    assert summary["h3_policies_agree"] is True
    assert summary["inadmissible_runs"] == [] and summary["aborted_runs"] == []
    hyp = summary["hypotheses"]
    assert hyp["H1"]["resolved_api_symbols"] == 175
    assert hyp["H1"]["owned_legacy_api_names"] == 172
    assert hyp["H2"]["agree_claim_comparator_records"] == 62
    assert hyp["H3"]["equal_generated_files"] == 39
    assert hyp["H3"]["tables_equal_to_archived"] == 11
    assert hyp["H4"]["raw_equal_generated_files"] == 39
    assert hyp["H4"]["projection_equal"] is True
    written = sorted(
        path.name for path in (builder.repo / analysis.OUTPUT_DIR).iterdir()
    )
    assert written == sorted(analysis.OUTPUT_FILENAMES)
    assert (builder.repo / analysis.REPORT_MANIFEST_PATH).is_file()


def test_summary_carries_distinct_labelled_populations(builder: Builder) -> None:
    summary = _summary(builder)
    populations = summary["populations"]
    assert populations["api_symbol_count"] == 175
    assert populations["claim_comparator_record_count"] == 62
    assert populations["generated_file_count"] == 39
    assert populations["analysis_output_file_count"] == 7
    assert summary["statistics"]["confidence_intervals"].startswith("not applicable")
    for name in analysis.OUTPUT_FILENAMES:
        text = _output(builder, name)
        assert "abs_diff_decade_histogram" not in text
        assert " 46 " not in text and "46 files" not in text
    distributions = json.loads(_output(builder, "error-distributions.json"))
    assert (
        distributions["claim_comparator_records"][
            "denominator_claim_comparator_records"
        ]
        == 62
    )
    assert distributions["generated_files"]["denominator_generated_files"] == 39


def test_csv_outputs_have_the_registered_rows(builder: Builder) -> None:
    _run(builder)
    api_rows = _output(builder, "api-mapping.csv").splitlines()
    assert len(api_rows) == 1 + 175
    assert api_rows[0].startswith("row_kind,name,")
    claims = _output(builder, "conclusion-comparisons.csv").splitlines()
    assert len(claims) == 1 + 62
    assert "operand_unit" in claims[0]
    assert any(line.startswith("C02:0,C02,") for line in claims)
    reproduction = _output(builder, "reproduction-comparisons.csv").splitlines()
    assert len(reproduction) == 1 + 39
    header = reproduction[0].split(",")
    assert (
        "h3_equal_approved_policy" in header and "h3_equal_sensitivity_policy" in header
    )
    assert "prin_raw_bytes" in header and "repeat_sensitivity_sha256" in header


# ---------------------------------------------------------------------------
# H1
# ---------------------------------------------------------------------------


def _h1(builder: Builder) -> dict[str, Any]:
    record: dict[str, Any] = _summary(builder)["hypotheses"]["H1"]
    return record


def test_h1_unresolved_export_refutes(builder: Builder) -> None:
    row = _row(builder.observations["api"], "Legacy005")
    row.update(
        {
            "resolved": False,
            "callable": None,
            "defining_module": None,
            "type": None,
            "error": "AttributeError",
        }
    )
    record = _h1(builder)
    assert record["verdict"] == "REFUTED"
    assert record["failing_api_symbols"] == ["Legacy005"]


def test_h1_none_export_refutes(builder: Builder) -> None:
    row = _row(builder.observations["api"], "Legacy006")
    row.update({"resolved": False, "callable": False, "type": "NoneType"})
    record = _h1(builder)
    assert record["classification_api_symbols"]["none"] == 1
    assert record["verdict"] == "REFUTED"


def test_h1_unsupported_export_refutes(builder: Builder) -> None:
    row = _row(builder.observations["api"], "Legacy007")
    row.update({"resolved": False, "callable": False, "type": "SomeObject"})
    record = _h1(builder)
    assert record["verdict"] == "REFUTED"
    assert record["classification_api_symbols"]["unsupported"] == 1


@pytest.mark.parametrize(
    ("mutation", "field"),
    [
        (lambda obs: obs["observed_names"].append("Legacy001"), "duplicate_exports"),
        (lambda obs: obs["observed_names"].append("Surprise"), "unexpected_exports"),
        (lambda obs: obs["observed_names"].remove("Legacy002"), "removed_exports"),
    ],
)
def test_h1_export_list_counterexamples_refute(
    builder: Builder, mutation: Callable[[dict[str, Any]], None], field: str
) -> None:
    mutation(builder.observations["api"])
    _sync_frozen(builder.observations["api"])
    record = _h1(builder)
    assert record["verdict"] == "REFUTED"
    assert record[field]
    assert record["counterexample_count"] >= 1


def test_h1_unexpected_export_is_listed_separately(builder: Builder) -> None:
    builder.observations["api"]["observed_names"].append("Surprise")
    _sync_frozen(builder.observations["api"])
    _run(builder)
    rows = _output(builder, "api-mapping.csv").splitlines()
    assert rows[-1].startswith("unexpected_export,Surprise,")


def test_h1_missing_ownership_row_refutes(builder: Builder) -> None:
    names = tuple(name for name in LEGACY if name != "Legacy010")
    builder.source = _commit_sources(builder.repo, guide_names=names)
    _row(builder.observations["api"], "Legacy010")["ownership_present"] = False
    record = _h1(builder)
    assert record["verdict"] == "REFUTED"
    assert record["unowned_legacy_api_names"] == ["Legacy010"]


def test_h1_ownership_flag_disagreeing_with_the_guide_is_inadmissible(
    builder: Builder,
) -> None:
    _row(builder.observations["api"], "Legacy011")["ownership_present"] = False
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert "ownership flag disagrees" in summary["inadmissible_runs"][0]["reason"]


def test_h1_unverifiable_row_is_inconclusive(builder: Builder) -> None:
    _row(builder.observations["api"], "Legacy012").update(
        {"resolved": True, "callable": False, "type": "VersionString"}
    )
    record = _h1(builder)
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["unverifiable_api_symbols"] == ["Legacy012"]


def test_h1_counterexample_outranks_an_unverifiable_row(builder: Builder) -> None:
    _row(builder.observations["api"], "Legacy012").update(
        {"resolved": True, "callable": False, "type": "VersionString"}
    )
    builder.observations["api"]["observed_names"].append("Legacy000")
    assert _h1(builder)["verdict"] == "REFUTED"


@pytest.mark.parametrize(
    "update",
    [
        {"resolved": True, "error": "AttributeError"},
        {"resolved": False},
        {"resolved": True, "type": "NoneType", "callable": False},
        {"resolved": False, "callable": False, "type": "int"},
        {"callable": "yes"},
        {"error": 3},
        {"resolved": "true"},
        {"legacy": False},
    ],
)
def test_h1_self_inconsistent_row_makes_the_record_inadmissible(
    builder: Builder, update: dict[str, Any]
) -> None:
    _row(builder.observations["api"], "Legacy020").update(update)
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert summary["inadmissible_runs"][0]["run_id"].endswith("api-cpu")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda obs: obs["expected_names"].pop(),
        lambda obs: obs["legacy_names"].pop(),
        lambda obs: obs["rows"].pop(),
        lambda obs: obs.update(unit="symbol"),
        lambda obs: obs.update(extra=1),
        lambda obs: obs["rows"][0].update(extra=1),
        lambda obs: obs.update(observed_names="Legacy000"),
        lambda obs: obs.update(rows={}),
    ],
)
def test_h1_schema_violations_make_the_record_inadmissible(
    builder: Builder, mutation: Callable[[dict[str, Any]], None]
) -> None:
    mutation(builder.observations["api"])
    assert _verdicts(builder)["H1"] == "INCONCLUSIVE"


# ---------------------------------------------------------------------------
# H2
# ---------------------------------------------------------------------------


def test_h2_published_claim_contradiction_refutes(builder: Builder) -> None:
    builder.docs["phase1_chimera_seeds.json"]["bimodality_coefficient"]["raw_values"][
        1
    ] = 0.5
    summary = _summary(builder)
    record = summary["hypotheses"]["H2"]
    assert record["verdict"] == "REFUTED"
    assert record["disagreeing_case_ids"] == ["C01:1"]
    assert record["families"]["C01"]["disagree_claim_comparator_records"] == 1
    assert summary["d1_flag"] is True and summary["d1_hypotheses"] == ["H2"]
    claims = _output(builder, "conclusion-comparisons.csv")
    assert "C01:1,C01," in claims and ",false,published_claim,false,true" not in claims


def test_h2_c02_stored_flag_disagreement_refutes(builder: Builder) -> None:
    grid = builder.docs["benchmark_y4q1_3_k_alpha_sensitivity.json"]["grid"]
    grid[1]["chimera_detected"] = True
    record = _summary(builder)["hypotheses"]["H2"]
    assert record["verdict"] == "REFUTED"
    assert record["disagreeing_case_ids"] == ["C02:1"]


def test_h2_negative_c02_classifications_are_agreements(builder: Builder) -> None:
    record = _summary(builder)["hypotheses"]["H2"]
    assert record["families"]["C02"]["agree_claim_comparator_records"] == 42


@pytest.mark.parametrize(
    "mutation",
    [
        lambda cases: cases[0].update(left=cases[0]["left"] + 0.001),
        lambda cases: cases[0].update(observed=not cases[0]["observed"]),
        lambda cases: cases[0].update(expected=not cases[0]["expected"]),
        lambda cases: cases[7].update(K=99.0),
        lambda cases: cases[0].update(operand_unit="units"),
        lambda cases: cases[0].update(right_path="/x"),
        lambda cases: cases[0].update(left=True),
        lambda cases: cases.pop(),
        lambda cases: cases.append(dict(cases[0])),
        lambda cases: cases[0].update(case_id="C01:9"),
        lambda cases: cases[0].update(extra=1),
        lambda cases: cases[0].pop("case_id"),
    ],
)
def test_h2_record_disagreeing_with_the_frozen_inputs_is_inadmissible(
    builder: Builder, mutation: Callable[[list[dict[str, Any]]], None]
) -> None:
    builder.result_mutators["conclusions"] = lambda result: mutation(
        result["observations"]["cases"]
    )
    summary = _summary(builder)
    assert summary["verdicts"]["H2"] == "INCONCLUSIVE"
    assert summary["d1_flag"] is False
    assert summary["inadmissible_runs"][0]["run_id"].endswith("conclusions-cpu")


def test_h2_wrong_unit_is_inadmissible(builder: Builder) -> None:
    builder.result_mutators["conclusions"] = lambda result: result[
        "observations"
    ].update(unit="case")
    assert _verdicts(builder)["H2"] == "INCONCLUSIVE"


def test_h2_integer_operands_compare_by_value(builder: Builder) -> None:
    def to_int(result: dict[str, Any]) -> None:
        case = result["observations"]["cases"][-1]
        case["left"] = int(case["left"])

    builder.docs["y3q49_goldilocks_zones.json"]["zones"]["full_cpu"]["K_c"] = 1
    builder.result_mutators["conclusions"] = to_int
    assert _verdicts(builder)["H2"] == "CONFIRMED"


# ---------------------------------------------------------------------------
# H3 (both policies)
# ---------------------------------------------------------------------------


def _h3(builder: Builder) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary = _summary(builder)
    return summary["hypotheses"]["H3"], summary["hypotheses"]["H3_sensitivity"], summary


def test_h3_missing_output_refutes_under_both_policies(builder: Builder) -> None:
    files = builder.observations["prin"]["files"]
    files.remove(_file(builder.observations["prin"], FIGURE))
    approved, sensitivity, summary = _h3(builder)
    assert approved["verdict"] == sensitivity["verdict"] == "REFUTED"
    assert approved["missing_in_prin"] == [FIGURE]
    assert summary["d1_flag"] is True
    assert "missing in prin" in _output(builder, "reproduction-comparisons.csv")


def test_h3_extra_output_refutes(builder: Builder) -> None:
    extra = file_record("reference", "figures/fig1_extra.pdf", 99)
    builder.observations["reference"]["files"].append(extra)
    approved, _sensitivity, _ = _h3(builder)
    assert approved["verdict"] == "REFUTED"
    assert approved["extra_in_reference"] == ["figures/fig1_extra.pdf"]
    rows = _output(builder, "reproduction-comparisons.csv").splitlines()
    assert rows[-1].startswith("figures/fig1_extra.pdf,pdf,false,")


def test_h3_normalized_figure_difference_refutes(builder: Builder) -> None:
    _file(builder.observations["prin"], FIGURE)["normalized_sha256"] = "e" * 64
    approved, sensitivity, _ = _h3(builder)
    assert approved["verdict"] == "REFUTED"
    assert approved["differing_generated_files"] == [FIGURE]
    assert approved["by_format"]["pdf"]["differ_generated_files"] == 1
    assert sensitivity["verdict"] == "CONFIRMED"


def test_h3_verdicts_differ_when_only_the_sensitivity_policy_fails(
    builder: Builder,
) -> None:
    # A CRLF-only table difference: equal after canonicalization, unequal raw.
    for observations in (builder.observations["reference"],):
        record = _file(observations, TABLE)
        record["raw_sha256"] = record["sensitivity_sha256"] = "c" * 64
        record["raw_bytes"] = record["sensitivity_bytes"] = record["raw_bytes"] + 20
    approved, sensitivity, summary = _h3(builder)
    assert approved["verdict"] == "CONFIRMED"
    assert sensitivity["verdict"] == "REFUTED"
    assert sensitivity["differing_generated_files"] == [TABLE]
    assert sensitivity["reference_tables_inconsistent_with_archived"] == [TABLE]
    assert summary["h3_policies_agree"] is False
    assert summary["h3_sensitivity_policy_refuted"] is True
    assert summary["d1_flag"] is False
    text = _output(builder, "expected-vs-observed.md")
    assert "verdicts DIFFER" in text and "neither verdict" in text


def test_h3_prin_differing_from_the_archived_table_refutes(builder: Builder) -> None:
    for mode in ("reference", "prin", "repeatability"):
        record = _file(builder.observations[mode], TABLE)
        record["archived_normalized_sha256"] = "a" * 64
    approved, _sensitivity, _ = _h3(builder)
    assert approved["verdict"] == "REFUTED"
    assert approved["tables_differing_from_archived"] == [TABLE]
    assert approved["reference_tables_inconsistent_with_archived"] == [TABLE]
    assert approved["differing_generated_files"] == []


def test_h3_archived_fields_disagreeing_between_arms_is_inconclusive(
    builder: Builder,
) -> None:
    _file(builder.observations["prin"], TABLE)["archived_sha256"] = "b" * 64
    approved, sensitivity, _ = _h3(builder)
    assert approved["verdict"] == sensitivity["verdict"] == "INCONCLUSIVE"
    assert "archived-table fields" in approved["reason"]


def test_h3_aborted_reference_is_inconclusive_not_refuted(builder: Builder) -> None:
    def abort(result: dict[str, Any]) -> None:
        result["status"] = "ABORTED"
        result["abort_reason"] = "DriverError: synthetic"
        result.pop("observations")

    builder.result_mutators["reference"] = abort
    approved, sensitivity, summary = _h3(builder)
    assert approved["verdict"] == sensitivity["verdict"] == "INCONCLUSIVE"
    assert summary["aborted_runs"] == [builder.run_id("reference")]
    assert summary["d1_flag"] is False
    assert summary["verdicts"]["H4"] == "CONFIRMED"


def test_h3_renderer_change_between_arms_is_inconclusive(builder: Builder) -> None:
    builder.observations["prin"]["renderer"]["matplotlib"] = "3.12.0"
    approved, _sensitivity, _ = _h3(builder)
    assert approved["verdict"] == "INCONCLUSIVE"
    assert "renderer" in approved["reason"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda obs: obs["renderer"]["font_cache"].update(sha256=None),
        lambda obs: obs["renderer"].update(font_sha256={}),
        lambda obs: obs["renderer"].pop("numpy"),
        lambda obs: obs.update(implementation="reference"),
        lambda obs: obs["expected_files"].pop(),
        lambda obs: obs["files"].append(dict(obs["files"][0])),
        lambda obs: obs["files"][0].update(path="../escape.pdf"),
        lambda obs: obs["files"][0].update(path="figures\\x.pdf"),
        lambda obs: obs["files"][0].update(path=""),
        lambda obs: obs["files"][0].update(path="figures/x.svg"),
        lambda obs: obs["files"][0].update(raw_bytes=-1),
        lambda obs: obs["files"][0].update(raw_sha256="Z" * 64),
        lambda obs: _file(obs, TABLE).pop("archived_sha256"),
        lambda obs: _file(obs, TABLE).update(sensitivity_sha256="d" * 64),
        lambda obs: _file(obs, PNG).update(sensitivity_sha256="d" * 64),
        lambda obs: obs["files"][0].update(path=7),
        lambda obs: obs.update(files={}),
    ],
)
def test_h3_invalid_prin_record_is_inadmissible(
    builder: Builder, mutation: Callable[[dict[str, Any]], None]
) -> None:
    mutation(builder.observations["prin"])
    summary = _summary(builder)
    assert summary["verdicts"]["H3"] == "INCONCLUSIVE"
    assert summary["verdicts"]["H4"] == "INCONCLUSIVE"
    assert summary["inadmissible_runs"][0]["run_id"].endswith("reproduction-prin-cpu")


# ---------------------------------------------------------------------------
# H4 (raw bytes, canonical projection)
# ---------------------------------------------------------------------------


def _h4(builder: Builder) -> dict[str, Any]:
    record: dict[str, Any] = _summary(builder)["hypotheses"]["H4"]
    return record


def test_h4_raw_difference_refutes_and_normalization_cannot_rescue(
    builder: Builder,
) -> None:
    _file(builder.observations["repeatability"], FIGURE)["raw_sha256"] = "f" * 64
    record = _h4(builder)
    assert record["verdict"] == "REFUTED"
    assert record["raw_differing_generated_files"] == [FIGURE]
    assert record["projection_equal"] is False


def test_h4_projection_difference_refutes_with_equal_raw_bytes(
    builder: Builder,
) -> None:
    _file(builder.observations["repeatability"], FIGURE)["normalized_sha256"] = "1" * 64
    record = _h4(builder)
    assert record["verdict"] == "REFUTED"
    assert record["raw_differing_generated_files"] == []
    assert record["projection_equal"] is False


def test_h4_projection_ignores_per_run_fields(builder: Builder) -> None:
    def per_run(result: dict[str, Any]) -> None:
        result["environment"]["processor"] = "other"
        result["started_at_utc"] = "2026-10-21T23:00:00+00:00"
        result["recorded_at_utc"] = "2026-10-21T23:00:09+00:00"
        result["elapsed_seconds"] = 9.0

    builder.result_mutators["repeatability"] = per_run
    record = _h4(builder)
    assert record["verdict"] == "CONFIRMED"
    assert record["projection_equal"] is True


def test_h4_file_in_one_arm_only_refutes(builder: Builder) -> None:
    files = builder.observations["repeatability"]["files"]
    files.remove(_file(builder.observations["repeatability"], PNG))
    record = _h4(builder)
    assert record["verdict"] == "REFUTED"
    assert record["only_in_prin"] == [PNG]


def test_h4_same_file_missing_from_both_arms_is_inconclusive(builder: Builder) -> None:
    for mode in ("prin", "repeatability"):
        builder.observations[mode]["files"].remove(
            _file(builder.observations[mode], PNG)
        )
    summary = _summary(builder)
    assert summary["hypotheses"]["H4"]["verdict"] == "INCONCLUSIVE"
    assert summary["verdicts"]["H3"] == "REFUTED"


def test_h4_inadmissible_repeat_is_inconclusive(builder: Builder) -> None:
    builder.sidecar_mutators["repeatability"] = lambda sidecar: sidecar.update(
        operator="someone"
    )
    summary = _summary(builder)
    assert summary["verdicts"]["H4"] == "INCONCLUSIVE"
    assert summary["verdicts"]["H3"] == "CONFIRMED"


def test_projection_removes_exactly_the_registered_fields() -> None:
    result = {
        "environment": {"a": 1},
        "config": {"out_dir": "x", "seed_key": 2},
        "identity": {"source_sha": "s"},
        "started_at_utc": "t0",
        "recorded_at_utc": "t1",
        "elapsed_seconds": 1.0,
        "observations": {"files": []},
        "status": "COMPLETED",
        "seed_used": False,
    }
    projected = json.loads(analysis.reproduction_projection(result))
    assert projected == {
        "config": {"seed_key": 2},
        "identity": {"source_sha": "s"},
        "observations": {"files": []},
        "status": "COMPLETED",
        "seed_used": False,
    }


# ---------------------------------------------------------------------------
# Record admissibility (tampered, missing, extra, linked)
# ---------------------------------------------------------------------------


def _inadmissible(builder: Builder, registration: Any) -> list[dict[str, Any]]:
    outcome = analysis.run_analysis(builder.repo, registration)
    runs: list[dict[str, Any]] = outcome["summary"]["inadmissible_runs"]
    return runs


def _run_dir(builder: Builder, mode: str) -> Path:
    return builder.repo / analysis.RAW_ROOT / builder.run_id(mode)


def test_tampered_result_bytes_are_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    path = _run_dir(builder, "api") / "api.json"
    path.write_bytes(path.read_bytes().replace(b'"COMPLETED"', b'"COMPLETEd"'))
    runs = _inadmissible(builder, registration)
    assert [run["run_id"] for run in runs] == [builder.run_id("api")]
    assert "size" in runs[0]["reason"] or "SHA-256" in runs[0]["reason"]


def test_tampered_manifest_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    path = _run_dir(builder, "conclusions") / analysis.MANIFEST
    path.write_bytes(path.read_bytes() + b"\n")
    runs = _inadmissible(builder, registration)
    assert "pinned E3 digest" in runs[0]["reason"]


def test_manifest_and_pin_must_agree(builder: Builder) -> None:
    registration = builder.write()
    spec = registration.runs[0]
    wrong = analysis.RunSpec(**{**spec.__dict__, "result_sha256": "0" * 64})
    registration = analysis.Registration(
        **{**registration.__dict__, "runs": (wrong, *registration.runs[1:])}
    )
    runs = _inadmissible(builder, registration)
    assert "pinned E3 digest" in runs[0]["reason"]


def test_missing_record_file_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    (_run_dir(builder, "prin") / "reproduction.json").unlink()
    runs = _inadmissible(builder, registration)
    assert "inventory" in runs[0]["reason"]


def test_extra_file_in_a_run_directory_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    _write(_run_dir(builder, "reference") / "stray.json", "{}")
    runs = _inadmissible(builder, registration)
    assert "inventory" in runs[0]["reason"]


def test_missing_run_directory_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    shutil.rmtree(_run_dir(builder, "repeatability"))
    outcome = analysis.run_analysis(builder.repo, registration)
    assert outcome["summary"]["verdicts"]["H4"] == "INCONCLUSIVE"
    assert "missing" in outcome["summary"]["inadmissible_runs"][0]["reason"]


@pytest.mark.parametrize(
    ("mode", "mutation", "message"),
    [
        ("api", lambda r: r["identity"].update(source_sha="0" * 40), "identity"),
        (
            "api",
            lambda r: r["identity"].update(preregistration_commit="0" * 40),
            "identity",
        ),
        ("api", lambda r: r["identity"]["input_records"].pop(), "input records"),
        (
            "api",
            lambda r: r["identity"].update(input_record_count=True),
            "input records",
        ),
        ("api", lambda r: r["environment"].update(git_commit="0" * 40), "environment"),
        ("api", lambda r: r["environment"].update(backend="cuda"), "environment"),
        ("api", lambda r: r["environment"].update(seed=False), "environment"),
        ("api", lambda r: r["config"].update(iterations=10.0), "config"),
        ("api", lambda r: r["config"].update(seed_key=3), "config"),
        ("api", lambda r: r["config"].update(out_dir="C:/elsewhere/RUN-x"), "config"),
        ("api", lambda r: r.update(seed_used=True), "seed_used"),
        ("api", lambda r: r.update(elapsed_seconds=-1.0), "elapsed"),
        ("api", lambda r: r.update(started_at_utc=5), "timestamps"),
        ("api", lambda r: r.update(extra=1), "key set"),
        ("api", lambda r: r.update(status="RUNNING"), "status"),
        ("api", lambda r: r.update(observations=[]), "JSON object"),
    ],
)
def test_envelope_violations_are_inadmissible(
    builder: Builder,
    mode: str,
    mutation: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    builder.result_mutators[mode] = mutation
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert message in summary["inadmissible_runs"][0]["reason"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(session="0162"),
        lambda s: s.update(mode="prin"),
        lambda s: s.update(artefacts={"api.json": ["H2"]}),
        lambda s: s.update(extra=1),
    ],
)
def test_sidecar_violations_are_inadmissible(
    builder: Builder, mutation: Callable[[dict[str, Any]], None]
) -> None:
    builder.sidecar_mutators["api"] = mutation
    assert _verdicts(builder)["H1"] == "INCONCLUSIVE"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b'{"a": 1, "a": 2}', "duplicate JSON key"),
        (b'{"a": NaN}', "non-finite"),
        (b"\xef\xbb\xbf{}", "byte-order mark"),
        (b"\xff\xfe", "not UTF-8"),
        (b"{", "invalid JSON"),
    ],
)
def test_strict_json_rejects_ambiguous_documents(payload: bytes, message: str) -> None:
    with pytest.raises(analysis.RecordError, match=message):
        analysis._strict_json(payload, "doc", analysis.RecordError)


def test_duplicate_key_in_a_record_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    run_dir = _run_dir(builder, "api")
    sidecar = (run_dir / analysis.SIDECAR).read_bytes()
    doubled = sidecar.replace(b'"exp_id"', b'"exp_id": "EXP-002-r1",\n  "exp_id"', 1)
    (run_dir / analysis.SIDECAR).write_bytes(doubled)
    manifest = json.loads((run_dir / analysis.MANIFEST).read_bytes())
    for entry in manifest["files"]:
        if entry["path"] == analysis.SIDECAR:
            entry.update(bytes=len(doubled), sha256=_sha(doubled))
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    (run_dir / analysis.MANIFEST).write_bytes(manifest_bytes)
    spec = analysis.RunSpec(
        **{
            **registration.runs[0].__dict__,
            "sidecar_sha256": _sha(doubled),
            "manifest_sha256": _sha(manifest_bytes),
        }
    )
    registration = analysis.Registration(
        **{**registration.__dict__, "runs": (spec, *registration.runs[1:])}
    )
    runs = _inadmissible(builder, registration)
    assert "duplicate JSON key" in runs[0]["reason"]


@pytest.mark.parametrize(
    "document",
    [
        {
            "schema_version": 1,
            "description": "d",
            "source": "s",
            "files": [{"path": "a/b.json", "bytes": 1, "sha256": "0" * 64}],
        },
        {"schema_version": True, "description": "d", "source": "s", "files": []},
        {"schema_version": 1, "description": "d", "source": "s", "files": {}},
        {"schema_version": 1, "files": []},
        {
            "schema_version": 1,
            "description": "d",
            "source": "s",
            "files": [{"path": "a.json", "bytes": -1, "sha256": "0" * 64}],
        },
        {
            "schema_version": 1,
            "description": "d",
            "source": "s",
            "files": [{"path": "a.json", "bytes": 1, "sha256": "0" * 64}] * 2,
        },
    ],
)
def test_manifest_parser_rejects_malformed_manifests(document: dict[str, Any]) -> None:
    with pytest.raises(analysis.RecordError):
        analysis._parse_manifest(
            json.dumps(document).encode(), "m", analysis.RecordError
        )


def _make_link(target: Path, link: Path) -> None:
    """Create a directory junction (Windows) or symlink; skip if unsupported."""
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))  # type: ignore[attr-defined]
        return
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:  # pragma: no cover - platform dependent
        pytest.skip("directory links unsupported")


def test_link_detection_covers_junctions_and_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target"
    (target / "inner").mkdir(parents=True)
    _write(target / "inner" / "f.json", "{}")
    link = tmp_path / "link"
    _make_link(target, link)
    assert analysis._is_link(link)
    assert not analysis._is_link(target)
    assert not analysis._is_link(tmp_path / "absent")
    with pytest.raises(analysis.RecordError, match="link"):
        analysis._read_regular(link / "inner" / "f.json", analysis.RecordError)
    with pytest.raises(analysis.RecordError, match="regular"):
        analysis._read_regular(target / "inner", analysis.RecordError)
    with pytest.raises(analysis.RecordError, match="stat"):
        analysis._read_regular(target / "absent.json", analysis.RecordError)


def test_linked_run_directory_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    run_dir = _run_dir(builder, "api")
    moved = builder.repo / "moved-run"
    run_dir.rename(moved)
    _make_link(moved, run_dir)
    runs = _inadmissible(builder, registration)
    assert "link" in runs[0]["reason"]


def test_symlinked_result_file_is_inadmissible(builder: Builder) -> None:
    registration = builder.write()
    path = _run_dir(builder, "api") / "api.json"
    real = builder.repo / "api-real.json"
    shutil.move(str(path), str(real))
    try:
        path.symlink_to(real)
    except OSError:
        pytest.skip("file symlinks need privileges on this host")
    runs = _inadmissible(builder, registration)
    assert "link" in runs[0]["reason"]


# ---------------------------------------------------------------------------
# Global preconditions (fail closed, nothing written)
# ---------------------------------------------------------------------------


def _assert_aborts(builder: Builder, registration: Any, message: str) -> None:
    with pytest.raises(analysis.AnalysisError, match=message):
        analysis.run_analysis(builder.repo, registration)
    assert not (builder.repo / analysis.OUTPUT_DIR).exists()
    assert not (builder.repo / analysis.REPORT_MANIFEST_PATH).exists()


def test_unindexed_run_directory_aborts(builder: Builder) -> None:
    registration = builder.write()
    (builder.repo / analysis.RAW_ROOT / "RUN-20261021T230000Z-abcdef0-api-cpu").mkdir()
    _assert_aborts(builder, registration, "unindexed")


def test_tampered_frozen_input_aborts(builder: Builder) -> None:
    registration = builder.write()
    path = builder.repo / analysis.REFERENCE_RESULTS / "phase1_chimera_seeds.json"
    path.write_bytes(path.read_bytes().replace(b"0.61", b"0.71"))
    _assert_aborts(builder, registration, "SHA-256 mismatch")


def test_resized_frozen_input_aborts(builder: Builder) -> None:
    registration = builder.write()
    path = builder.repo / analysis.REFERENCE_RESULTS / "filler_000.json"
    path.write_bytes(path.read_bytes() + b" ")
    _assert_aborts(builder, registration, "size mismatch")


def test_unmanifested_frozen_input_aborts(builder: Builder) -> None:
    registration = builder.write()
    _write(builder.repo / analysis.REFERENCE_RESULTS / "zz_extra.json", "{}")
    _assert_aborts(builder, registration, "exactly the manifested")


def test_input_manifest_digest_mismatch_aborts(builder: Builder) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "input_manifest_sha256": "0" * 64}
    )
    _assert_aborts(builder, registration, "input manifest")


def test_missing_h2_input_aborts(builder: Builder) -> None:
    builder.input_mutator = lambda results: (
        results / "phase2_chimera_nsweep.json"
    ).rename(results / "renamed.json")
    registration = builder.write()
    _assert_aborts(builder, registration, "H2 input")


def test_changed_working_protocol_aborts(builder: Builder) -> None:
    registration = builder.write()
    _write(builder.repo / analysis.PROTOCOL_PATH, PROTOCOL + "edit\n")
    _assert_aborts(builder, registration, "working protocol")


def test_protocol_digest_mismatch_aborts(builder: Builder) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "protocol_sha256": "1" * 64}
    )
    _assert_aborts(builder, registration, "pinned digest")


def test_unapproved_or_undated_protocol_aborts() -> None:
    with pytest.raises(analysis.AnalysisError, match="APPROVED"):
        analysis._approval_date(PROTOCOL.replace("APPROVED", "DRAFT").encode())
    with pytest.raises(analysis.AnalysisError, match="dated approval"):
        analysis._approval_date(PROTOCOL.replace("MichaelMaillet, ", "").encode())


def test_wrong_approval_date_aborts(builder: Builder) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "approval_date_utc": "2026-10-11"}
    )
    _assert_aborts(builder, registration, "approval date")


def test_protocol_commit_off_the_source_history_aborts(builder: Builder) -> None:
    registration = builder.write()
    _git(builder.repo, "checkout", "-q", "-b", "side", builder.freeze)
    _git(builder.repo, "commit", "-q", "--allow-empty", "-m", "side")
    side = _git(builder.repo, "rev-parse", "HEAD")
    _git(builder.repo, "checkout", "-q", builder.source)
    registration = analysis.Registration(
        **{**registration.__dict__, "protocol_commit": side}
    )
    _assert_aborts(builder, registration, "not an ancestor of R")


def test_head_not_descending_from_source_aborts(builder: Builder) -> None:
    registration = builder.write()
    _git(builder.repo, "checkout", "-q", builder.freeze)
    _assert_aborts(builder, registration, "descend")


def test_reference_api_digest_mismatch_aborts(builder: Builder) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "reference_api_sha256": "2" * 64}
    )
    _assert_aborts(builder, registration, "reference API")


def test_reference_names_must_be_the_frozen_list() -> None:
    with pytest.raises(analysis.AnalysisError, match="172"):
        analysis._reference_names(b"__all__ = ['a', 'a']\n")
    with pytest.raises(analysis.AnalysisError, match="missing"):
        analysis._reference_names(b"names = []\n")


def test_missing_git_aborts(builder: Builder, monkeypatch: pytest.MonkeyPatch) -> None:
    registration = builder.write()
    monkeypatch.setattr(analysis.shutil, "which", lambda _name: None)
    _assert_aborts(builder, registration, "git is unavailable")


def test_linked_raw_root_aborts(builder: Builder) -> None:
    registration = builder.write()
    raw_root = builder.repo / analysis.RAW_ROOT
    moved = builder.repo / "raw-moved"
    raw_root.rename(moved)
    _make_link(moved, raw_root)
    _assert_aborts(builder, registration, "link")


# ---------------------------------------------------------------------------
# Outputs: confinement, manifest, determinism, CLI
# ---------------------------------------------------------------------------


def _tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def test_writes_only_the_registered_destinations(builder: Builder) -> None:
    registration = builder.write()
    before = _tree(builder.repo)
    analysis.run_analysis(builder.repo, registration)
    after = _tree(builder.repo)
    changed = {path for path in after if before.get(path) != after[path]}
    expected = {f"{analysis.OUTPUT_DIR}/{name}" for name in analysis.OUTPUT_FILENAMES}
    assert changed == expected | {analysis.REPORT_MANIFEST_PATH}
    assert all(path in after for path in before)


def test_output_directory_behind_a_link_is_refused(builder: Builder) -> None:
    registration = builder.write()
    generated = builder.repo / analysis.GENERATED_ROOT
    elsewhere = builder.repo / "elsewhere"
    elsewhere.mkdir()
    generated.parent.mkdir(parents=True, exist_ok=True)
    _make_link(elsewhere, generated)
    with pytest.raises(analysis.AnalysisError, match="link"):
        analysis.run_analysis(builder.repo, registration)
    assert not any(elsewhere.iterdir())


def test_non_regular_output_destination_is_refused(builder: Builder) -> None:
    registration = builder.write()
    (builder.repo / analysis.OUTPUT_DIR / "summary.json").mkdir(parents=True)
    with pytest.raises(analysis.AnalysisError, match="regular file"):
        analysis.run_analysis(builder.repo, registration)


def test_write_outputs_refuses_an_unregistered_output_set(tmp_path: Path) -> None:
    with pytest.raises(analysis.AnalysisError, match="unregistered output set"):
        analysis.write_outputs(tmp_path, {"other.json": b"{}"}, b"{}")


def test_failed_write_leaves_no_temporary_file(
    builder: Builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    registration = builder.write()

    def fail(_source: str, _destination: Path) -> None:
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(analysis.os, "replace", fail)
    with pytest.raises(OSError, match="synthetic"):
        analysis.run_analysis(builder.repo, registration)
    leftovers = list((builder.repo / analysis.OUTPUT_DIR).glob(".exp002-r1-e4-*"))
    assert leftovers == []


def test_report_manifest_indexes_inputs_and_both_output_sets(builder: Builder) -> None:
    outcome = _run(builder)
    manifest = json.loads((builder.repo / analysis.REPORT_MANIFEST_PATH).read_bytes())
    assert manifest["execution_commit"] == builder.source
    assert manifest["freeze_commit"] == builder.freeze
    assert manifest["input_manifest"]["record_count"] == 172
    assert [entry["run_id"] for entry in manifest["inputs"]] == [
        builder.run_id(mode) for mode in analysis.MODE_ORDER
    ]
    for entry in manifest["inputs"]:
        assert entry["manifest"]["path"].endswith("/manifest.json")
        assert len(entry["files"]) == 2
    outputs = manifest["analysis_outputs"]
    assert manifest["analysis_output_file_count"] == len(outputs) == 7
    for entry in outputs:
        payload = (builder.repo / entry["path"]).read_bytes()
        assert entry["bytes"] == len(payload) and entry["sha256"] == _sha(payload)
        name = entry["path"].rsplit("/", 1)[1]
        assert outcome["outputs"][name] == entry["sha256"]
    publication = manifest["publication_outputs"]
    assert publication["generated_file_count"] == len(publication["files"]) == 39
    assert publication["source_run_id"] == builder.run_id("prin")
    assert all("/publication/" in entry["path"] for entry in publication["files"])
    assert manifest["verdicts"]["H1"] == "CONFIRMED"
    assert manifest["d1_flag"] is False


def test_outputs_are_byte_identical_across_runs(builder: Builder) -> None:
    registration = builder.write()
    first = analysis.run_analysis(builder.repo, registration)
    snapshot = _tree(builder.repo / analysis.OUTPUT_DIR)
    manifest = (builder.repo / analysis.REPORT_MANIFEST_PATH).read_bytes()
    second = analysis.run_analysis(builder.repo, registration)
    assert first["outputs"] == second["outputs"]
    assert first["report_manifest_sha256"] == second["report_manifest_sha256"]
    assert _tree(builder.repo / analysis.OUTPUT_DIR) == snapshot
    assert (builder.repo / analysis.REPORT_MANIFEST_PATH).read_bytes() == manifest
    for name in analysis.OUTPUT_FILENAMES:
        text = _output(builder, name)
        assert "\r\n" not in text
        assert "21:00:01" not in text and "elapsed" not in text


def test_inadmissible_records_are_rendered_not_dropped(builder: Builder) -> None:
    builder.result_mutators["api"] = lambda r: r.update(
        status="ABORTED", abort_reason="x"
    )
    builder.result_mutators["conclusions"] = lambda r: r["config"].update(warmup=1)
    builder.observations["reference"]["unit"] = "file"
    _run(builder)
    assert (
        _output(builder, "api-mapping.csv")
        .splitlines()[1]
        .startswith("inadmissible_record,")
    )
    assert (
        _output(builder, "conclusion-comparisons.csv")
        .splitlines()[1]
        .startswith("inadmissible_record:")
    )
    assert "reference record inadmissible" in _output(
        builder, "reproduction-comparisons.csv"
    )
    distributions = json.loads(_output(builder, "error-distributions.json"))
    assert "inadmissible" in distributions["api_symbols"]
    assert "inadmissible" in distributions["claim_comparator_records"]
    assert (
        "inadmissible"
        in distributions["generated_files"]["h3_approved_policy_reference_vs_prin"]
    )
    coverage = _output(builder, "coverage-and-deferrals.md")
    assert "| ABORTED | no |" in coverage
    assert coverage.count("OPEN - not discharged by EXP-002-r1") == len(
        analysis.OWNER_MATRIX
    )
    observed = _output(builder, "expected-vs-observed.md")
    assert "not evaluable" in observed


def test_module_identity_is_recorded(builder: Builder) -> None:
    summary = _summary(builder)
    module = summary["analysis_module"]
    assert module["path"] == analysis.MODULE_RELATIVE_PATH
    assert module["sha256"] == _sha(_MODULE_PATH.read_bytes())
    # The synthetic repository does not track the module.
    assert module["commit"] is None and module["matches_commit"] is False


def test_main_reports_verdicts_and_returns_zero(
    builder: Builder,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registration = builder.write()
    monkeypatch.setattr(analysis, "REPOSITORY_ROOT", builder.repo)
    monkeypatch.setattr(analysis, "REGISTERED", registration)
    assert analysis.main([]) == 0
    printed = capsys.readouterr().out
    assert "H1: CONFIRMED" in printed and "D1 flag: False" in printed
    assert analysis.REPORT_MANIFEST_PATH in printed


def test_main_returns_one_and_writes_nothing_on_a_global_failure(
    builder: Builder,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "input_manifest_sha256": "0" * 64}
    )
    monkeypatch.setattr(analysis, "REPOSITORY_ROOT", builder.repo)
    monkeypatch.setattr(analysis, "REGISTERED", registration)
    assert analysis.main([]) == 1
    assert "NOT COMPLETED" in capsys.readouterr().err
    assert not (builder.repo / analysis.OUTPUT_DIR).exists()


def test_is_d1_uses_primary_verdicts_only() -> None:
    confirmed = dict.fromkeys(("H1", "H2", "H3", "H4"), "CONFIRMED")
    assert analysis.is_d1(confirmed) is False
    assert analysis.is_d1({**confirmed, "H4": "REFUTED"}) is True
    assert analysis.is_d1({**confirmed, "H3": "INCONCLUSIVE"}) is False


def test_module_commit_is_recorded_when_the_module_is_tracked(builder: Builder) -> None:
    _write(builder.repo / analysis.MODULE_RELATIVE_PATH, _MODULE_PATH.read_bytes())
    _git(builder.repo, "add", "-A", "--", analysis.MODULE_RELATIVE_PATH)
    _git(builder.repo, "commit", "-q", "-m", "module")
    commit = _git(builder.repo, "rev-parse", "HEAD")
    registration = builder.write()
    summary = analysis.run_analysis(builder.repo, registration)["summary"]
    assert summary["analysis_module"]["commit"] == commit
    assert summary["analysis_module"]["matches_commit"] is True


def test_git_launch_failure_aborts(
    builder: Builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    registration = builder.write()

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("synthetic launch failure")

    monkeypatch.setattr(analysis.subprocess, "run", refuse)
    _assert_aborts(builder, registration, "git query failed")


@pytest.mark.parametrize(
    ("rc1", "field", "names"),
    [
        (
            tuple(name for name in EXPECTED if name != "Legacy003"),
            "frozen_contract_extra",
            ["Legacy003"],
        ),
        ((*EXPECTED, "Ghost"), "frozen_contract_missing", ["Ghost"]),
    ],
)
def test_h1_frozen_contract_difference_refutes(
    builder: Builder, rc1: tuple[str, ...], field: str, names: list[str]
) -> None:
    builder.source = _commit_sources(builder.repo, rc1=rc1)
    _sync_frozen(builder.observations["api"], rc1)
    record = _h1(builder)
    assert record["verdict"] == "REFUTED"
    assert record[field] == names


@pytest.mark.parametrize("field", ["frozen_missing", "frozen_extra"])
def test_h1_frozen_sets_disagreeing_with_rc1_are_inadmissible(
    builder: Builder, field: str
) -> None:
    builder.observations["api"][field].append("Legacy004")
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert "frozen-contract" in summary["inadmissible_runs"][0]["reason"]


def test_frozen_contract_digest_mismatch_aborts(builder: Builder) -> None:
    registration = builder.write()
    registration = analysis.Registration(
        **{**registration.__dict__, "deprecation_sha256": "3" * 64}
    )
    _assert_aborts(builder, registration, "section 1.1 digests")


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"RC1_PUBLIC_API = ['a']\n", "not a tuple"),
        (b"RC1_PUBLIC_API = (name,)\n", "not a literal"),
        (b"RC1_PUBLIC_API = (\n", "does not parse"),
        (b"OTHER = ()\n", "missing"),
    ],
)
def test_frozen_contract_source_must_be_a_literal_tuple(
    payload: bytes, message: str
) -> None:
    with pytest.raises(analysis.AnalysisError, match=message):
        analysis._frozen_contract(payload)


def test_ambient_git_overrides_are_ignored(
    builder: Builder, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    registration = builder.write()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "not-a-repository"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))
    outcome = analysis.run_analysis(builder.repo, registration)
    assert outcome["summary"]["verdicts"]["H1"] == "CONFIRMED"


def test_calendar_dates_are_validated() -> None:
    assert analysis._real_time("2026-10-21", "%Y-%m-%d")
    assert not analysis._real_time("2026-13-45", "%Y-%m-%d")
    with pytest.raises(analysis.AnalysisError, match="dated approval"):
        analysis._approval_date(PROTOCOL.replace("2026-10-21", "2026-02-30").encode())
    good = analysis.REGISTERED
    first = good.runs[0]
    bad = analysis.RunSpec(
        **{**first.__dict__, "run_id": first.run_id.replace("20261021T", "20261312T")}
    )
    with pytest.raises(analysis.AnalysisError, match="registered run name"):
        analysis._check_registration(
            analysis.Registration(**{**good.__dict__, "runs": (bad, *good.runs[1:])})
        )


def test_unlistable_run_directory_is_inadmissible(
    builder: Builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = builder.run_id("api")
    original = Path.iterdir

    def iterdir(self: Path) -> Any:
        if self.name == target:
            raise PermissionError("synthetic listing failure")
        return original(self)

    monkeypatch.setattr(Path, "iterdir", iterdir)
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert "cannot list run directory" in summary["inadmissible_runs"][0]["reason"]


def test_owner_matrix_is_the_registered_section_5_3_matrix() -> None:
    protocol = (_REPOSITORY_ROOT / analysis.PROTOCOL_PATH).read_text(encoding="utf-8")
    section = protocol.split("### 5.3", 1)[1].split("### 5.4", 1)[0]
    rows = [
        line
        for line in section.splitlines()
        if line.startswith("| ") and "---" not in line
    ][1:]
    assert len(rows) == len(analysis.OWNER_MATRIX) == 7
    for line, (claim, owner) in zip(rows, analysis.OWNER_MATRIX, strict=True):
        cells = [cell.strip() for cell in line.strip("|").split(" | ")]
        assert cells[0] == claim
        assert cells[1] == owner


def test_fast_path_is_not_taken_when_a_global_input_changes(builder: Builder) -> None:
    # An uncommitted edit of the reference __all__ (still 172 unique names) changes
    # only the reference pin. The helper must fall back to full verification, which
    # re-derives the expected population and finds the record inconsistent with it.
    names = [*LEGACY[:-1], "Replacement"]
    _write(builder.repo / analysis.REFERENCE_API_PATH, f"__all__ = {names!r}\n")
    summary = _summary(builder)
    assert summary["verdicts"]["H1"] == "INCONCLUSIVE"
    assert "expected_names" in summary["inadmissible_runs"][0]["reason"]


@pytest.mark.parametrize(
    ("method", "target", "message"),
    [
        ("glob", "results", "frozen input directory"),
        ("iterdir", "EXP-002-r1", "raw record root"),
    ],
)
def test_global_listing_failures_abort_cleanly(
    builder: Builder,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    target: str,
    message: str,
) -> None:
    registration = builder.write()
    original = getattr(Path, method)

    def failing(self: Path, *args: Any) -> Any:
        if self.name == target:
            raise PermissionError("synthetic listing failure")
        return original(self, *args)

    monkeypatch.setattr(Path, method, failing)
    _assert_aborts(builder, registration, message)

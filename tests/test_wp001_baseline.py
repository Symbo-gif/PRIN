from __future__ import annotations

import builtins
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).parents[1]
OWNERSHIP = ROOT / "tools" / "wp001_ownership.json"


def _load_baseline_module() -> ModuleType:
    module_path = ROOT / "tools" / "wp001_baseline.py"
    spec = importlib.util.spec_from_file_location("wp001_baseline", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test target: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


wp001_baseline = _load_baseline_module()
BaselineValidationError = wp001_baseline.BaselineValidationError
collect_api_traceability = wp001_baseline.collect_api_traceability
collect_repository_inventory = wp001_baseline.collect_repository_inventory
render_traceability_markdown = wp001_baseline.render_traceability_markdown
validate_baseline = wp001_baseline.validate_baseline
validate_metadata = wp001_baseline.validate_metadata
validate_session_plan = wp001_baseline.validate_session_plan


def _copy_metadata_fixture(destination: Path) -> None:
    paths = [
        Path("Cargo.toml"),
        Path("pyproject.toml"),
        Path("CITATION.cff"),
        Path("LICENSE"),
        Path("rust-toolchain.toml"),
        Path("python/prin/__init__.py"),
    ]
    paths.extend(path.relative_to(ROOT) for path in ROOT.glob("crates/*/Cargo.toml"))
    paths.extend(
        path.relative_to(ROOT) for path in ROOT.glob(".github/workflows/*.yml")
    )
    for relative in paths:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def _ownership_payload() -> dict[str, Any]:
    return json.loads(OWNERSHIP.read_text(encoding="utf-8"))


def _write_api_fixture(
    destination: Path,
    sources: dict[str, str],
    ownership: dict[str, Any] | None = None,
) -> Path:
    archive = (
        destination
        / "DOCS/archive and reference from PRINet 3.0"
        / "PRINet-3.0.0-main/src/prinet"
    )
    for relative, content in sources.items():
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    session = destination / "DOCS/sessions/phase-0/0005-wp002-s1-test-ownership.md"
    session.parent.mkdir(parents=True, exist_ok=True)
    session.write_text("# WP-002 ownership fixture\n", encoding="utf-8")
    payload = ownership or {
        "schema_version": 1,
        "modules": {
            "prinet": {"future_wp": "WP-002", "basis": "fixture"},
        },
        "symbols": {},
    }
    ownership_path = destination / "ownership.json"
    ownership_path.write_text(json.dumps(payload), encoding="utf-8")
    return ownership_path


def test_current_baseline_automation_is_green() -> None:
    assert validate_baseline(ROOT) == []


def test_metadata_validator_detects_version_drift(tmp_path: Path) -> None:
    _copy_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    original = pyproject.read_text(encoding="utf-8")
    current_version = re.search(r'version = "([^"]+)"', original).group(1)  # type: ignore[union-attr]
    pyproject.write_text(
        original.replace(f'version = "{current_version}"', 'version = "0.2.0"', 1),
        encoding="utf-8",
    )

    errors = validate_metadata(tmp_path)

    assert any("version mismatch" in error for error in errors)
    assert any("pyproject.toml=0.2.0" in error for error in errors)


def test_metadata_validator_detects_missing_workspace_manifest(tmp_path: Path) -> None:
    _copy_metadata_fixture(tmp_path)
    (tmp_path / "crates/prin-metrics/Cargo.toml").unlink()

    errors = validate_metadata(tmp_path)

    assert any("workspace member manifest is missing" in error for error in errors)
    assert any("crates/prin-metrics/Cargo.toml" in error for error in errors)


def test_metadata_validator_detects_unpublishable_workspace_dependency(
    tmp_path: Path,
) -> None:
    # WP038-F3 regression: `cargo publish` strips `path` and rewrites the
    # dependency against crates.io, so a version-less path dependency made
    # every publishable crate except prin-dynamics unpackageable.
    _copy_metadata_fixture(tmp_path)
    cargo_toml = tmp_path / "Cargo.toml"
    original = cargo_toml.read_text(encoding="utf-8")
    workspace_version = re.search(  # type: ignore[union-attr]
        r'\[workspace\.package\]\nversion = "([^"]+)"', original
    ).group(1)
    pinned = (
        f'prin-metrics = {{ path = "crates/prin-metrics", '
        f'version = "{workspace_version}" }}'
    )
    assert pinned in original

    cargo_toml.write_text(
        original.replace(pinned, 'prin-metrics = { path = "crates/prin-metrics" }', 1),
        encoding="utf-8",
    )

    errors = validate_metadata(tmp_path)

    assert any(
        "workspace.dependencies.prin-metrics must declare a version" in error
        for error in errors
    )


def test_metadata_validator_detects_stale_workspace_dependency_pin(
    tmp_path: Path,
) -> None:
    # WP038-F3 regression, second half: the pin must track the workspace
    # version, or a release bump publishes crates that depend on a version of
    # their siblings that was never released.
    _copy_metadata_fixture(tmp_path)
    cargo_toml = tmp_path / "Cargo.toml"
    original = cargo_toml.read_text(encoding="utf-8")
    stale = 'prin-tensor = { path = "crates/prin-tensor", version = "0.1.0" }'

    rewritten = re.sub(
        r'prin-tensor = \{ path = "crates/prin-tensor", version = "[^"]+" \}',
        stale,
        original,
        count=1,
    )
    assert rewritten != original
    cargo_toml.write_text(rewritten, encoding="utf-8")

    errors = validate_metadata(tmp_path)

    assert any(
        "workspace.dependencies.prin-tensor version '0.1.0' does not match "
        "workspace.package.version" in error
        for error in errors
    )


def test_metadata_validator_rejects_reverting_the_distribution_name(
    tmp_path: Path,
) -> None:
    # WP038-F4 regression: PyPI's `prin` belongs to an unrelated project last
    # released 2015-05-20, so reverting the distribution name would aim
    # release.yml's publish-pypi job at a project we do not own. Only the
    # distribution name is pinned here; the `prin` *import* name is guarded by
    # the same validator's maturin module-name assertion.
    _copy_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    original = pyproject.read_text(encoding="utf-8")
    assert 'name = "prin-core"' in original

    pyproject.write_text(
        original.replace('name = "prin-core"', 'name = "prin"', 1),
        encoding="utf-8",
    )

    errors = validate_metadata(tmp_path)

    assert any("project.name must equal 'prin-core'" in error for error in errors)


def test_metadata_validator_rejects_self_referencing_extra_by_import_name(
    tmp_path: Path,
) -> None:
    # WP038-F4 regression: `all = ["prin[dev,mot,onnx]"]` survived the
    # distribution rename, so `pip install prin-core[all]` would have resolved
    # `prin` from PyPI and installed the unrelated 2015 project that owns it.
    _copy_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    original = pyproject.read_text(encoding="utf-8")
    assert '"prin-core[dev,mot,onnx]"' in original

    pyproject.write_text(
        original.replace('"prin-core[dev,mot,onnx]"', '"prin[dev,mot,onnx]"', 1),
        encoding="utf-8",
    )

    errors = validate_metadata(tmp_path)

    assert any(
        "optional-dependencies.all self-references the import name" in error
        for error in errors
    )


def test_session_plan_validator_detects_missing_brief(tmp_path: Path) -> None:
    sessions = tmp_path / "DOCS" / "sessions"
    shutil.copytree(ROOT / "DOCS" / "sessions", sessions)
    missing = (
        sessions / "phase-0" / "0002-wp001-s2-foundation-baseline-and-traceability.md"
    )
    missing.unlink()

    errors = validate_session_plan(tmp_path)

    assert any(
        "found 255 physical numbered session briefs" in error for error in errors
    )
    assert any("register target does not exist" in error for error in errors)


def test_session_plan_validator_detects_duplicate_sequence_ids(
    tmp_path: Path,
) -> None:
    sessions = tmp_path / "DOCS" / "sessions"
    shutil.copytree(ROOT / "DOCS" / "sessions", sessions)
    source = (
        sessions / "phase-0" / "0002-wp001-s2-foundation-baseline-and-traceability.md"
    )
    shutil.copy2(source, sessions / "phase-0" / "0002-duplicate.md")

    errors = validate_session_plan(tmp_path)

    assert any(
        "duplicate session brief sequence IDs: 0002" in error for error in errors
    )
    assert any("257 physical numbered session briefs" in error for error in errors)


def test_session_plan_validator_accepts_additive_subsessions() -> None:
    """The register accepts all amendment #31-#36/#38 additive sub-sessions.

    This includes the 0141A-0141E block, the 0144A-0144P block (WP-036A/B/D/C,
    amendments #33/#36), 0144A1-0144A4, the WP-036B strict-port passes
    0144E1-0144E6, the WP-036D GPU sub-passes 0144I1-0144I3, and the
    WP-036E/F/G Deferred-Validation closure block 0144Q-0144AB (amendment #38,
    single-letter 0144Q-0144Z then two-letter 0144AA-0144AB), the WP-036C
    strict-port passes 0144M1-0144M8 (amendment #39), and the WP-036E S1
    decomposition passes 0144Q1-0144Q3 (amendment #43).
    """
    assert validate_session_plan(ROOT) == []


def test_session_plan_validator_rejects_misplaced_subsession(tmp_path: Path) -> None:
    sessions = tmp_path / "DOCS" / "sessions"
    shutil.copytree(ROOT / "DOCS" / "sessions", sessions)
    register = sessions / "SESSION_REGISTER.md"
    text = register.read_text(encoding="utf-8")
    # Pull session 0145's row up between 0144 and the 0144A sub-session block,
    # so the block no longer sits immediately after 0144 (integer gap-freeness
    # and the in-order sub-session set are both still intact).
    row = next(line for line in text.splitlines() if line.startswith("| 0145 |"))
    text = text.replace(row + "\n", "", 1)
    text = text.replace("| 0144A |", row + "\n| 0144A |", 1)
    register.write_text(text, encoding="utf-8")

    errors = validate_session_plan(tmp_path)

    assert any(
        "contiguously right after their anchor session" in error for error in errors
    )


def test_api_traceability_covers_archive_without_importing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "prinet" or name.startswith("prinet."):
            raise AssertionError("archived PRINet code must never be imported")
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    traceability = collect_api_traceability(ROOT)

    assert traceability["module_count"] == 43
    assert traceability["top_level_public_symbol_count"] == 172
    assert traceability["frozen_public_symbol_count"] == 98
    assert traceability["top_level_symbols_not_frozen"] == 74
    assert traceability["symbol_count"] == 657
    assert len(traceability["modules"]) == traceability["module_count"]
    assert len(traceability["symbols"]) == traceability["symbol_count"]
    assert all(row["future_wp"].startswith("WP-") for row in traceability["modules"])
    assert all(row["future_wp"].startswith("WP-") for row in traceability["symbols"])


def test_baseline_validator_enforces_exact_module_symbol_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    traceability = collect_api_traceability(ROOT)
    traceability["symbol_count"] = 656
    traceability["symbols"] = traceability["symbols"][:-1]
    monkeypatch.setattr(
        wp001_baseline,
        "collect_api_traceability",
        lambda root, ownership_path=None: traceability,
    )

    errors = validate_baseline(ROOT)

    assert any("expected 657, found 656" in error for error in errors)


def test_api_traceability_is_deterministic() -> None:
    first = collect_api_traceability(ROOT)
    second = collect_api_traceability(ROOT)

    assert first == second
    assert first["modules"] == sorted(first["modules"], key=lambda row: row["module"])
    assert first["symbols"] == sorted(
        first["symbols"], key=lambda row: (row["module"], row["symbol"])
    )


@pytest.mark.parametrize("future_wp", ["WP-001", "WP-999", "not-a-wp"])
def test_api_traceability_rejects_invalid_future_wp(
    tmp_path: Path,
    future_wp: str,
) -> None:
    payload = _ownership_payload()
    payload["modules"]["prinet.core.measurement"]["future_wp"] = future_wp
    ownership = tmp_path / "ownership.json"
    ownership.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BaselineValidationError, match="future WP"):
        collect_api_traceability(ROOT, ownership)


def test_api_traceability_fails_closed_on_unowned_module(tmp_path: Path) -> None:
    payload = _ownership_payload()
    del payload["modules"]["prinet.core.measurement"]
    ownership = tmp_path / "ownership.json"
    ownership.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BaselineValidationError, match="unowned module"):
        collect_api_traceability(ROOT, ownership)


def test_repository_inventory_is_deterministic_and_separates_archive() -> None:
    first = collect_repository_inventory(ROOT)
    second = collect_repository_inventory(ROOT)

    assert first == second
    assert first["project"]["name"] == "prin-core"
    assert first["project"]["version"] == "1.0.0rc1"
    assert len(first["workspace"]["members"]) == 8
    assert len(first["ci"]["workflows"]) == 9
    assert "snyk.yml" in first["ci"]["workflows"]
    assert "nightly.yml" in first["ci"]["workflows"]
    assert first["session_plan"]["numbered_briefs"] == 256
    assert first["archive"]["python_modules"] == 43
    assert "target" in first["excluded_directories"]
    assert ".git" in first["excluded_directories"]
    assert ".coverage" in first["excluded_files"]
    assert ".coverage" not in first["active_repository"]["files_by_top_level"]


def test_traceability_renderer_contains_summary_and_every_row() -> None:
    traceability = collect_api_traceability(ROOT)

    rendered = render_traceability_markdown(traceability)

    assert "# WP-001 PRINet 3.0 API traceability" in rendered
    assert "43" in rendered
    assert "172" in rendered
    assert "prinet.core.measurement" in rendered
    assert "kuramoto_order_parameter" in rendered
    assert rendered.count("\n|") >= (
        traceability["module_count"] + traceability["symbol_count"]
    )
    assert all(line == line.rstrip() for line in rendered.splitlines())


def test_cli_emits_machine_readable_inventory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = wp001_baseline.main(["--root", str(ROOT), "inventory"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["project"]["name"] == "prin-core"
    assert captured.err == ""


def test_cli_emits_traceability_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = wp001_baseline.main(["--root", str(ROOT), "traceability"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("# WP-001 PRINet 3.0 API traceability")
    assert captured.err == ""


def test_cli_check_reports_validation_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        wp001_baseline,
        "validate_baseline",
        lambda root, ownership_path=None: ["first drift", "second drift"],
    )

    exit_code = wp001_baseline.main(["--root", str(ROOT), "check"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "first drift" in captured.err
    assert "second drift" in captured.err


def test_cli_check_reports_success(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = wp001_baseline.main(["--root", str(ROOT), "check"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "WP-001 baseline validation passed.\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("names = ['item']\n__all__ = names\n", "static list or tuple"),
        ("__all__ = {'item'}\n", "static list or tuple"),
        ("__all__ = ['item', 'item']\n", "contains duplicates"),
        ("from .leaf import *\n__all__ = []\n", "wildcard imports"),
        ("__all__: list[str]\n", "has no value"),
    ],
)
def test_api_discovery_rejects_non_static_contracts(
    tmp_path: Path,
    source: str,
    message: str,
) -> None:
    ownership = _write_api_fixture(tmp_path, {"__init__.py": source})

    with pytest.raises(BaselineValidationError, match=message):
        collect_api_traceability(tmp_path, ownership)


@pytest.mark.parametrize(
    ("sources", "message"),
    [
        (
            {
                "__init__.py": "__all__ = ['item']\n",
            },
            "no static definition or import",
        ),
        (
            {
                "__init__.py": ("from absent.module import item\n__all__ = ['item']\n"),
            },
            "source module is absent",
        ),
        (
            {
                "__init__.py": "from .leaf import item\n__all__ = ['item']\n",
                "leaf.py": "from . import item\n__all__ = ['item']\n",
            },
            "cyclic archived re-export",
        ),
    ],
)
def test_api_discovery_rejects_unresolvable_reexports(
    tmp_path: Path,
    sources: dict[str, str],
    message: str,
) -> None:
    payload = {
        "schema_version": 1,
        "modules": {
            "prinet": {"future_wp": "WP-002", "basis": "fixture"},
            "prinet.leaf": {"future_wp": "WP-002", "basis": "fixture"},
        },
        "symbols": {},
    }
    if "leaf.py" not in sources:
        del payload["modules"]["prinet.leaf"]
    ownership = _write_api_fixture(tmp_path, sources, payload)

    with pytest.raises(BaselineValidationError, match=message):
        collect_api_traceability(tmp_path, ownership)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 2, "modules": {}, "symbols": {}}, "schema_version"),
        ({"schema_version": 1, "modules": [], "symbols": {}}, "object-valued"),
        (
            {
                "schema_version": 1,
                "modules": {
                    "prinet": {"future_wp": "WP-002", "basis": "fixture"},
                    "prinet.unknown": {
                        "future_wp": "WP-002",
                        "basis": "fixture",
                    },
                },
                "symbols": {},
            },
            "unknown module",
        ),
        (
            {
                "schema_version": 1,
                "modules": {"prinet": "WP-002"},
                "symbols": {},
            },
            "must be an object",
        ),
        (
            {
                "schema_version": 1,
                "modules": {
                    "prinet": {"future_wp": "WP-002", "basis": ""},
                },
                "symbols": {},
            },
            "basis must be non-empty",
        ),
        (
            {
                "schema_version": 1,
                "modules": {
                    "prinet": {"future_wp": "WP-002", "basis": "fixture"},
                },
                "symbols": {
                    "prinet.unknown": {
                        "future_wp": "WP-002",
                        "basis": "fixture",
                    }
                },
            },
            "unknown symbol override",
        ),
    ],
)
def test_ownership_schema_fails_closed(
    tmp_path: Path,
    payload: dict[str, Any],
    message: str,
) -> None:
    ownership = _write_api_fixture(
        tmp_path,
        {"__init__.py": "item = 1\n__all__ = ['item']\n"},
        payload,
    )

    with pytest.raises(BaselineValidationError, match=message):
        collect_api_traceability(tmp_path, ownership)


def test_metadata_validator_reports_comprehensive_drift(tmp_path: Path) -> None:
    _copy_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8")
        .replace('requires-python = ">=3.11"', 'requires-python = ">=3.12"')
        .replace("Python :: 3.13", "Python :: 3.14")
        .replace(
            'manifest-path = "crates/prin-py/Cargo.toml"',
            'manifest-path = "crates/other/Cargo.toml"',
        )
        .replace('python-source = "python"', 'python-source = "src"')
        .replace('module-name = "prin._prin_core"', 'module-name = "prin.bad"'),
        encoding="utf-8",
    )
    citation = tmp_path / "CITATION.cff"
    citation.write_text(
        citation.read_text(encoding="utf-8")
        .replace("license: MIT", "license: Apache-2.0")
        .replace(
            "https://github.com/Symbo-gif/PRIN",
            "https://example.invalid/PRIN",
        ),
        encoding="utf-8",
    )
    (tmp_path / "LICENSE").write_text("not a license\n", encoding="utf-8")
    toolchain = tmp_path / "rust-toolchain.toml"
    toolchain.write_text(
        '[toolchain]\nchannel = "beta"\ncomponents = ["rustfmt"]\n',
        encoding="utf-8",
    )
    dynamics = tmp_path / "crates/prin-dynamics/Cargo.toml"
    dynamics.write_text(
        dynamics.read_text(encoding="utf-8")
        .replace('name = "prin-dynamics"', 'name = "wrong"')
        .replace("version.workspace = true", 'version = "0.1.0"'),
        encoding="utf-8",
    )
    py_crate = tmp_path / "crates/prin-py/Cargo.toml"
    py_crate.write_text(
        py_crate.read_text(encoding="utf-8")
        .replace('name = "_prin_core"', 'name = "wrong"')
        .replace('"abi3-py311"', '"abi3-py312"'),
        encoding="utf-8",
    )
    python_workflow = tmp_path / ".github/workflows/python.yml"
    python_workflow.write_text(
        python_workflow.read_text(encoding="utf-8").replace('"3.13"', '"3.14"'),
        encoding="utf-8",
    )
    (tmp_path / ".github/workflows/release.yml").unlink()

    errors = validate_metadata(tmp_path)

    expected_fragments = [
        "project license mismatch",
        "LICENSE does not contain",
        "repository URL mismatch",
        "package name",
        "package.version must inherit",
        "maturin manifest-path",
        "maturin python-source",
        "maturin module-name",
        "library name",
        "abi3-py311",
        "requires-python",
        "Python classifiers",
        "test matrix",
        "required CI workflow",
        "channel must equal",
        "components must include",
    ]
    for fragment in expected_fragments:
        assert any(fragment in error for error in errors), fragment


def test_metadata_validator_reports_missing_required_file(tmp_path: Path) -> None:
    _copy_metadata_fixture(tmp_path)
    (tmp_path / "CITATION.cff").unlink()

    assert validate_metadata(tmp_path) == [
        "required metadata file is missing: CITATION.cff"
    ]


def test_python_dependency_audits_are_complete_and_gating() -> None:
    workflow = (ROOT / ".github/workflows/python.yml").read_text(encoding="utf-8")
    security_job = workflow.split("  security:\n", maxsplit=1)[1]

    assert "pip-audit ." in security_job
    assert "pip-audit -r DOCS/sphinx/requirements.txt" in security_job
    assert security_job.count("--fail-on=all") == 2
    assert "continue-on-error" not in security_job
    assert "|| true" not in security_job


def test_python_workflow_limits_default_github_token_permissions() -> None:
    workflow = (ROOT / ".github/workflows/python.yml").read_text(encoding="utf-8")

    assert "\npermissions:\n  contents: read\n" in workflow


def test_python_docs_job_installs_mot_extra_for_notebook_execution() -> None:
    workflow = (ROOT / ".github/workflows/python.yml").read_text(encoding="utf-8")
    docs_job = workflow.split("  docs:\n", maxsplit=1)[1].split(
        "\n  security:\n", maxsplit=1
    )[0]

    assert (
        "python -m pip install --no-cache-dir -c ci/docs-constraints.txt -e "
        '".[dev,mot]"' in docs_job
    )
    assert "python -m pytest tests/test_notebooks.py -q -m slow" in docs_job


def test_release_workflow_publishes_workspace_crates() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    publish_job = workflow.split("  publish-crates:\n", maxsplit=1)[1]

    assert "cargo publish" in publish_job
    assert "CARGO_REGISTRY_TOKEN" in publish_job
    assert "prin-dynamics" in publish_job
    assert "prin-py has publish=false" in publish_job


def test_release_workflow_publish_or_skip_checks_exact_version() -> None:
    # Devin code review finding: the original publish_or_skip used `cargo search`
    # which only checks if the crate name exists, not the specific version. This
    # meant later version publish failures would be silently skipped. The fix
    # parses the cargo publish error output for "already exists" message.
    #
    # Critical: GitHub Actions runs Bash with `-e -o pipefail`, so command
    # substitution assignments inherit the substituted command's nonzero status
    # and terminate the script. The fix uses an if-condition to suppress errexit.
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    publish_job = workflow.split("  publish-crates:\n", maxsplit=1)[1]

    # Must extract workspace version
    assert "WORKSPACE_VERSION=" in publish_job
    assert "Cargo.toml" in publish_job

    # Must use if-condition to execute cargo publish (suppresses errexit)
    assert "if OUTPUT=$(cargo publish" in publish_job

    # Must check for "already exists" message in else branch
    assert 'grep -qi "already.*exists' in publish_job

    # Must NOT use cargo search or crates.io API (the buggy approaches)
    assert "cargo search" not in publish_job
    assert "crates.io/api" not in publish_job

    # Must NOT use EXIT_CODE=$? pattern (doesn't work with errexit)
    assert "EXIT_CODE=$?" not in publish_job


def _release_publish_or_skip_source() -> str:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    body = workflow.split("          publish_or_skip() {\n", maxsplit=1)[1].split(
        "\n          }\n", maxsplit=1
    )[0]
    return "publish_or_skip() {\n" + textwrap.dedent(body) + "\n}\n"


@pytest.mark.parametrize(
    "cargo_error",
    [
        "error: crate version `1.2.3` is already uploaded",
        "error: crate version 1.2.3 already exists on crates.io index",
        "error: crate prin-dynamics@1.2.3 already published",
    ],
)
def test_release_workflow_publish_or_skip_continues_under_errexit(
    tmp_path: Path, cargo_error: str
) -> None:
    # Devin code review finding: the runner executes the step as `bash -e`, so
    # publish_or_skip must survive a duplicate-version rejection and go on to
    # the crates that are not published yet.
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash unavailable")

    bindir = tmp_path / "bin"
    bindir.mkdir()
    cargo = bindir / "cargo"
    cargo.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$3" = "prin-dynamics" ]; then\n'
        f'  echo "{cargo_error}" >&2\n'
        "  exit 101\n"
        "fi\n"
        'echo "Uploading $3"\n',
        encoding="utf-8",
    )
    cargo.chmod(0o755)

    script = tmp_path / "publish.sh"
    script.write_text(
        "set -e -o pipefail\n"
        "WORKSPACE_VERSION=1.2.3\n"
        + _release_publish_or_skip_source()
        + "publish_or_skip prin-dynamics\n"
        "publish_or_skip prin-sim\n",
        encoding="utf-8",
    )

    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        [bash, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "prin-dynamics v1.2.3 already exists on crates.io, skipping" in result.stdout
    assert "prin-sim v1.2.3 published successfully" in result.stdout


def test_release_workflow_publish_or_skip_fails_on_unrelated_error(
    tmp_path: Path,
) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash unavailable")

    bindir = tmp_path / "bin"
    bindir.mkdir()
    cargo = bindir / "cargo"
    cargo.write_text(
        "#!/usr/bin/env bash\n"
        "echo 'error: failed to verify package tarball' >&2\n"
        "exit 101\n",
        encoding="utf-8",
    )
    cargo.chmod(0o755)

    script = tmp_path / "publish.sh"
    script.write_text(
        "set -e -o pipefail\n"
        "WORKSPACE_VERSION=1.2.3\n"
        + _release_publish_or_skip_source()
        + "publish_or_skip prin-dynamics\n"
        "publish_or_skip prin-sim\n",
        encoding="utf-8",
    )

    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        [bash, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    assert result.returncode != 0
    assert "Failed to publish prin-dynamics" in result.stdout
    assert "prin-sim" not in result.stdout


def _release_wheels_job() -> str:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    return workflow.split("  wheels:\n", maxsplit=1)[1].split(
        "\n  sdist:\n", maxsplit=1
    )[0]


def _release_wheel_steps() -> list[str]:
    return list(re.split(r"\n(?=      - )", _release_wheels_job()))


def test_release_workflow_smoke_test_never_uses_bash_on_the_self_hosted_leg() -> None:
    # WP038-F1 regression: `shell: bash` resolves to C:\windows\system32\
    # bash.EXE on PRIN-GPU-Runner, whose WSL is not installed, so the smoke
    # test died with `execvpe(/bin/bash) failed` after the wheel built fine
    # (release run 35021650652, job 104558518001). Same DV-024 root cause
    # gpu.yml and rust.yml already work around.
    windows_leg = (
        _release_wheels_job()
        .split("- os: windows-latest", maxsplit=1)[1]
        .split("- os: ubuntu-latest", maxsplit=1)[0]
    )
    assert "[self-hosted, Windows, X64]" in windows_leg
    assert "self_hosted: true" in windows_leg

    bash_steps = [
        step
        for step in _release_wheel_steps()
        if "shell: bash" in step.partition("run: |")[0]
    ]
    assert bash_steps, "the hosted-leg smoke test should still use bash globbing"
    for step in bash_steps:
        assert "!matrix.self_hosted" in step.partition("run: |")[0], step


def test_release_workflow_windows_smoke_test_names_its_shell_and_isolates() -> None:
    # WP038-F1 regression, second half: the Windows leg states `shell: pwsh`
    # explicitly rather than inheriting the runner default, and installs into a
    # throwaway venv addressed by absolute path — gpu.yml's DV-029 note records
    # that a bare `pip` on that runner reaches the shared Miniforge install, so
    # an RC wheel installed there would pollute the maintainer's environment
    # and prove nothing about a clean no-compiler install.
    windows_steps = [
        step
        for step in _release_wheel_steps()
        if "Wheel smoke test (self-hosted Windows)" in step
    ]
    assert len(windows_steps) == 1
    # Assert against the step's YAML keys and its script separately: the
    # explanatory comment above this step quotes `shell: bash`, and YAML
    # comments attach to the preceding step when the job is split on `- `.
    header, _, script = windows_steps[0].partition("run: |")

    assert "if: matrix.self_hosted" in header
    assert "shell: pwsh" in header
    assert "bash" not in header
    assert ".smoke-venv\\Scripts\\python.exe" in script
    assert "import prin" in script
    assert "bash" not in script


def test_release_workflow_reclaims_disk_before_the_hosted_build() -> None:
    # WP038-F2 / DV-022 regression: the smoke test's `torch>=2.0` resolve
    # filled the ~14 GB ubuntu-latest image (release run 35021650652, job
    # 104558518084, `No space left on device`).
    reclaim = [step for step in _release_wheel_steps() if "Free disk space" in step]
    assert len(reclaim) == 1
    step = reclaim[0]

    assert "if: runner.os == 'Linux'" in step
    assert "/usr/share/dotnet" in step
    # /opt/hostedtoolcache holds the interpreter the job runs on; reclaiming
    # it breaks every later step. The reclaim must be command-level, so check
    # the rm lines rather than the step's explanatory comment.
    rm_lines = [line for line in step.splitlines() if "rm -rf" in line]
    assert rm_lines
    assert not any("hostedtoolcache" in line for line in rm_lines)


def test_release_workflow_smoke_test_satisfies_torch_from_the_cpu_index() -> None:
    # WP038-F2 / DV-022 regression, second half: torch must already be
    # satisfied from the CPU index *before* the wheel is installed, or pip
    # re-resolves it from PyPI and drags the ~5 GB CUDA 13 stack. Mirrors
    # python.yml's Linux build step.
    smoke = [
        step for step in _release_wheel_steps() if "Wheel smoke test (hosted" in step
    ]
    assert len(smoke) == 1
    step = smoke[0]

    cpu_index = "https://download.pytorch.org/whl/cpu"
    assert cpu_index in step
    assert step.index(cpu_index) < step.index("dist/*.whl")


def test_repro_workflow_runs_wp035_pipeline_and_tamper_tests() -> None:
    workflow = (ROOT / ".github/workflows/repro.yml").read_text(encoding="utf-8")

    assert "PRIN_REPRO_ENABLED" not in workflow
    assert "Pre-WP-035 guard" not in workflow
    assert "python -m pytest tests/test_reproduce.py -q" in workflow
    assert "python tools/reproduce.py --verify-manifest" in workflow


def test_python_ci_builds_inside_explicit_virtual_environments() -> None:
    for relative in [
        ".github/workflows/python.yml",
        ".github/workflows/repro.yml",
    ]:
        workflow = (ROOT / relative).read_text(encoding="utf-8")
        assert "python -m venv .venv" in workflow
        assert 'echo "$PWD/.venv/bin" >> "$GITHUB_PATH"' in workflow


def test_secret_scan_is_blocking_and_covers_full_history() -> None:
    workflow = (ROOT / ".github/workflows/snyk.yml").read_text(encoding="utf-8")
    secret_job = workflow.split("  secret-scan:\n", maxsplit=1)[1]

    assert "pull-requests: read" in workflow
    assert "fetch-depth: 0" in secret_job
    assert "gitleaks/gitleaks-action@v2" in secret_job
    assert "continue-on-error" not in secret_job
    assert "|| true" not in secret_job
    ignored = [
        line
        for line in (ROOT / ".gitleaksignore").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert len(ignored) == 1
    assert ":generic-api-key:68" in ignored[0]
    assert "sha256_manifest.json" in ignored[0]


def test_session_plan_validator_reports_metadata_and_link_drift(
    tmp_path: Path,
) -> None:
    sessions = tmp_path / "DOCS/sessions"
    shutil.copytree(ROOT / "DOCS/sessions", sessions)
    first = sessions / "phase-0/0001-wp001-s1-foundation-baseline-and-traceability.md"
    first.write_text(
        first.read_text(encoding="utf-8")
        .replace("# Session 0001", "# Session 9999", 1)
        .replace("**Status:** COMPLETE", "**Status:** BLOCKED", 1)
        .replace("**Execution unit:** WP-001", "**Execution unit:** WP-999", 1)
        .replace("**Session type:** S1 — Coding", "**Session type:** S2 — Audit", 1)
        .replace(
            "**Predecessor:** Project execution start",
            "**Predecessor:** [0002]("
            "0002-wp001-s2-foundation-baseline-and-traceability.md)",
            1,
        )
        .replace(
            "**Successor:** [0002 — Audit]("
            "0002-wp001-s2-foundation-baseline-and-traceability.md)",
            "**Successor:** Project complete",
            1,
        ),
        encoding="utf-8",
    )
    second = sessions / "phase-0/0002-wp001-s2-foundation-baseline-and-traceability.md"
    second.write_text(
        second.read_text(encoding="utf-8").replace(
            "**Predecessor:** [0001 — Coding]("
            "0001-wp001-s1-foundation-baseline-and-traceability.md)",
            "**Predecessor:** Project execution start",
            1,
        ),
        encoding="utf-8",
    )
    last = sessions / "phase-7/0198-wp039-s4-stable-release-evidence-closure.md"
    last.write_text(
        last.read_text(encoding="utf-8").replace(
            "**Successor:** Project complete",
            "**Successor:** [0001](../phase-0/"
            "0001-wp001-s1-foundation-baseline-and-traceability.md)",
            1,
        ),
        encoding="utf-8",
    )

    errors = validate_session_plan(tmp_path)

    for fragment in [
        "heading does not match",
        "status mismatch",
        "execution unit mismatch",
        "session type mismatch",
        "0001 must start",
        "successor is not session 0002",
        "0002: predecessor",
        "0198 must end",
    ]:
        assert any(fragment in error for error in errors), fragment


def test_missing_frozen_api_export_fails_closed(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "modules": {
            "prinet": {"future_wp": "WP-002", "basis": "fixture"},
            "prinet._deprecation": {
                "future_wp": "WP-002",
                "basis": "fixture",
            },
        },
        "symbols": {},
    }
    ownership = _write_api_fixture(
        tmp_path,
        {
            "__init__.py": "item = 1\n__all__ = ['item']\n",
            "_deprecation.py": (
                "FROZEN_PUBLIC_API: frozenset[str] = frozenset(['removed'])\n"
            ),
        },
        payload,
    )

    with pytest.raises(
        BaselineValidationError,
        match=r"missing from prinet\.__all__",
    ):
        collect_api_traceability(tmp_path, ownership)


def test_invalid_ownership_json_fails_closed(tmp_path: Path) -> None:
    ownership = _write_api_fixture(
        tmp_path,
        {"__init__.py": "item = 1\n__all__ = ['item']\n"},
    )
    ownership.write_text("{not-json", encoding="utf-8")

    with pytest.raises(BaselineValidationError, match="cannot load ownership map"):
        collect_api_traceability(tmp_path, ownership)


def test_missing_session_register_fails_closed(tmp_path: Path) -> None:
    assert validate_session_plan(tmp_path) == [
        "session register is missing: DOCS/sessions/SESSION_REGISTER.md"
    ]


def test_cli_reports_invalid_root(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = wp001_baseline.main(["--root", "missing-repository", "traceability"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "root is not a directory" in captured.err

"""DV-040 regression tests: campaign-record quality-gate coverage.

`python.yml`'s lint job and the AGENTS.md local-gate one-liner must lint,
format-check, type-check, and SAST-scan `DOCS/experiments/` (the campaign
plan §7.4 analysis-code roots) alongside the normal roots, and the bandit
`exclude_dirs` must exclude directory *components* — never bare substrings
that also appear inside campaign record slugs such as
`EXP-999-tests-parity`.
"""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path

import pytest
from bandit.core.config import BanditConfig
from bandit.core.manager import BanditManager, _is_file_included

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "python.yml"
AGENTS = REPO_ROOT / "AGENTS.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CAMPAIGN_ROOT = REPO_ROOT / "DOCS" / "experiments"
CAMPAIGN_TOKEN = "DOCS/experiments"  # trailing slash optional in commands

_RUN_LINE = re.compile(r"^\s*(?:-\s*)?run:\s+(\S.*)$")

_CAMPAIGN_GATES = [
    pytest.param("ruff", "check", {"check"}, id="ruff-check"),
    pytest.param("ruff", "format", {"format", "--check"}, id="ruff-format"),
    pytest.param("mypy", None, {"--strict"}, id="mypy-strict"),
    pytest.param("bandit", None, {"-r"}, id="bandit-recursive"),
]


def _tool_name(command: list[str]) -> str:
    """Executable or `-m` module a tokenized command invokes."""
    name = Path(command[0]).name
    if name.startswith("python") and "-m" in command:
        return command[command.index("-m") + 1]
    return name


def _workflow_commands() -> list[list[str]]:
    """shlex-split every single-line `run:` command in `python.yml`."""
    commands = []
    for line in WORKFLOW.read_text(encoding="utf-8").splitlines():
        match = _RUN_LINE.match(line)
        if match:
            commands.append(shlex.split(match.group(1), posix=True))
    return commands


def _agents_commands() -> list[list[str]]:
    """shlex-split the `.venv`-prefixed local-gate lines in `AGENTS.md`."""
    commands = []
    for line in AGENTS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(".venv"):
            commands.append(shlex.split(stripped.replace("\\", "/"), posix=True))
    return commands


def _gate_commands(
    commands: list[list[str]], tool: str, subcommand: str | None
) -> list[list[str]]:
    """Commands invoking `tool` (optionally `tool subcommand`) on the campaign root."""
    return [
        command
        for command in commands
        if command
        and _tool_name(command) == tool
        and (subcommand is None or (len(command) > 1 and command[1] == subcommand))
        and any(token.rstrip("/") == CAMPAIGN_TOKEN for token in command)
    ]


@pytest.mark.parametrize(("tool", "subcommand", "required"), _CAMPAIGN_GATES)
def test_workflow_lint_covers_campaign_root(
    tool: str, subcommand: str | None, required: set[str]
) -> None:
    matches = _gate_commands(_workflow_commands(), tool, subcommand)
    assert matches, f"python.yml has no `{tool}` gate covering {CAMPAIGN_TOKEN}"
    assert any(required <= set(command) for command in matches), (
        f"no `{tool}` campaign command carries the required options {required}"
    )


@pytest.mark.parametrize(("tool", "subcommand", "required"), _CAMPAIGN_GATES)
def test_agents_local_gate_covers_campaign_root(
    tool: str, subcommand: str | None, required: set[str]
) -> None:
    matches = _gate_commands(_agents_commands(), tool, subcommand)
    assert matches, f"AGENTS.md has no `{tool}` gate covering {CAMPAIGN_TOKEN}"
    assert any(required <= set(command) for command in matches), (
        f"no `{tool}` campaign command carries the required options {required}"
    )


def test_campaign_format_selects_source_files_only() -> None:
    """The campaign format leg positively selects source, never prose."""
    for commands in (_workflow_commands(), _agents_commands()):
        matches = _gate_commands(commands, "ruff", "format")
        assert matches
        assert any(
            "--config" in command
            and any(
                token.startswith("include") and "*.py" in token for token in command
            )
            for command in matches
        ), "campaign format command lacks the `include` source-file override"


def test_normal_typing_and_sast_gates_retained() -> None:
    """The `python/prin` typing and bandit gates survive the extension."""
    for commands in (_workflow_commands(), _agents_commands()):
        assert any(
            _tool_name(command) == "mypy"
            and "python/prin" in command
            and "--strict" in command
            for command in commands
        )
        assert any(
            _tool_name(command) == "bandit"
            and "-r" in command
            and "python/prin" in command
            for command in commands
        )


@pytest.fixture(scope="module")
def bandit_config() -> BanditConfig:
    return BanditConfig(str(PYPROJECT))


@pytest.fixture(scope="module")
def bandit_exclusions(bandit_config: BanditConfig) -> list[str]:
    return bandit_config.get_option("exclude_dirs") or []


def test_bandit_exclusions_are_component_globs(
    bandit_exclusions: list[str],
) -> None:
    """Every exclusion is a `d/*` or `*/d/*` component glob, not a substring."""
    assert bandit_exclusions
    for pattern in bandit_exclusions:
        assert pattern.endswith("/*") or pattern.endswith("\\*"), pattern


def test_bandit_discovers_every_campaign_source(
    bandit_config: BanditConfig,
) -> None:
    """Config-scoped discovery must not silently drop campaign records."""
    manager = BanditManager(bandit_config, "file")
    manager.discover_files([str(CAMPAIGN_ROOT)], recursive=True)
    discovered = {Path(path).resolve() for path in manager.files_list}
    expected = {path.resolve() for path in CAMPAIGN_ROOT.rglob("*.py")}
    assert expected, "fixture assumption: campaign tree contains .py sources"
    assert discovered, "bandit discovered no files under the campaign root"
    assert expected <= discovered


@pytest.mark.parametrize(
    "relpath",
    ["parity/reference.py", "tests/fixture.py"],
    ids=["top-level-parity", "top-level-tests"],
)
@pytest.mark.parametrize("absolute", [False, True], ids=["relative", "absolute"])
def test_bandit_still_excludes_excluded_dirs(
    bandit_exclusions: list[str], relpath: str, absolute: bool
) -> None:
    path = relpath if not absolute else str(REPO_ROOT / relpath)
    assert not _is_file_included(os.path.normpath(path), ["*.py"], bandit_exclusions)


@pytest.mark.parametrize("absolute", [False, True], ids=["relative", "absolute"])
def test_bandit_includes_campaign_files_under_exclusion_like_slugs(
    bandit_exclusions: list[str], absolute: bool
) -> None:
    relpath = "DOCS/experiments/EXP-999-tests-parity/analysis/quality.py"
    path = relpath if not absolute else str(REPO_ROOT / relpath)
    assert _is_file_included(os.path.normpath(path), ["*.py"], bandit_exclusions)


def test_sphinx_requirements_urllib3_minimum_patched() -> None:
    """EA007-E-F4 regression: doc requirements must pin urllib3 >= 2.8.0.

    Snyk SCA flagged urllib3 2.7.0 (CVE-2026-97687/97688/97689, fixedIn
    2.8.0) in `DOCS/sphinx/requirements.txt`; the minimum must stay at or
    above the fixed release.
    """
    requirements = (REPO_ROOT / "DOCS" / "sphinx" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"^urllib3\s*>=\s*(\d+)\.(\d+)\.(\d+)\s*$", requirements, re.MULTILINE
    )
    assert match, "requirements.txt must pin a minimum urllib3 version"
    assert tuple(int(match.group(i)) for i in (1, 2, 3)) >= (2, 8, 0)

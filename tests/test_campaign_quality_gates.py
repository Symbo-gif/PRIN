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
from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "python.yml"
AGENTS = REPO_ROOT / "AGENTS.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CAMPAIGN_ROOT = REPO_ROOT / "DOCS" / "experiments"
CAMPAIGN_TOKEN = "DOCS/experiments"  # trailing slash optional in commands

_RUN_LINE = re.compile(r"^\s*(?:-\s*)?run:\s+(\S.*)$")
# PowerShell quoted segments, consumed whole left to right (PR32-F1).
_SINGLE_QUOTED = r"'(?:[^']|'')*'"
_DOUBLE_QUOTED = r'"(?:[^"`]|`.|"")*"'
_QUOTED_SEGMENT = re.compile(_SINGLE_QUOTED + "|" + _DOUBLE_QUOTED)
# Cargo features of `prin-sim` that compile its feature-gated `gpu` module.
_GPU_BACKEND_FEATURES = {"cpu", "cuda", "wgpu"}
_JOB_HEADER = re.compile(r"^  [A-Za-z0-9_-]+:\s*$")

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


_COMPONENT_GLOB = re.compile(r"^(?:\*/)?(?P<name>[^/*\\]+)/\*$")
_REQUIRED_EXCLUDED_COMPONENTS = {"tests", "benchmarks", "parity"}


def _excluded_components(bandit_exclusions: list[str]) -> set[str]:
    """Directory names named by the `d/*` / `*/d/*` exclusions."""
    names = set()
    for pattern in bandit_exclusions:
        match = _COMPONENT_GLOB.match(pattern)
        assert match, f"not a single-component glob (`d/*` or `*/d/*`): {pattern}"
        names.add(match.group("name"))
    return names


def test_bandit_exclusions_are_component_globs(
    bandit_exclusions: list[str],
) -> None:
    """Exclusions are POSIX component globs that really exclude their directory.

    The shape alone is not enough (`does-not-exist/*` and `../../*` satisfy a
    suffix check while excluding nothing, and a backslash spelling excludes
    nothing on POSIX), so each named component is exercised: a top-level and a
    nested file under it must be excluded, while a campaign slug that merely
    contains the name as a substring must still be scanned (PR32-F14).
    """
    assert bandit_exclusions, "bandit exclude_dirs is empty"
    names = _excluded_components(bandit_exclusions)
    missing = _REQUIRED_EXCLUDED_COMPONENTS - names
    assert not missing, f"required exclusions dropped: {sorted(missing)}"
    for name in sorted(names):
        for pattern in (f"{name}/*", f"*/{name}/*"):
            assert pattern in bandit_exclusions, f"missing twin glob {pattern}"
        for excluded in (f"{name}/x.py", f"pkg/{name}/x.py"):
            assert not _is_file_included(
                os.path.normpath(excluded), ["*.py"], bandit_exclusions
            ), f"{excluded} should be excluded"
        slug = f"DOCS/experiments/EXP-999-{name}-slug/analysis/quality.py"
        assert _is_file_included(os.path.normpath(slug), ["*.py"], bandit_exclusions), (
            f"{slug} must stay in scope"
        )


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
    # Parsed as PEP 508 requirements (PR32-F15): any specifier order, extras and
    # markers work, an inline `# CVE-...` comment is dropped, and a commented-out
    # entry is not a requirement, so it cannot satisfy the test.
    specifiers = []
    for raw in requirements.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            requirement = Requirement(line)
        except InvalidRequirement:
            continue  # pip options (`-r`, `--hash`) are not requirements
        if requirement.name.lower() == "urllib3":
            specifiers.append(requirement.specifier)
    assert specifiers, "requirements.txt must pin a minimum urllib3 version"
    for specifier in specifiers:
        assert Version("2.8.0") in specifier, f"urllib3{specifier} excludes 2.8.0"
        admitted = [
            version
            for version in ("2.7.0", "2.7.99", "2.0.0", "1.26.20")
            if Version(version) in specifier
        ]
        assert not admitted, f"urllib3{specifier} still admits {admitted}"


def test_agents_powershell_block_has_no_embedded_double_quotes() -> None:
    """PR32-F1: the fenced `powershell` gate must survive Windows PowerShell 5.1.

    5.1 strips double quotes embedded in a single-quoted native-command
    argument, so `'include = ["*.py"]'` reaches ruff as `include = [*.py]`
    (invalid TOML, exit 2) even though PowerShell 7 and bash accept it. A
    TOML literal string (`"include = ['*.py']"`) survives all three shells.
    """
    text = AGENTS.read_text(encoding="utf-8")
    blocks = re.findall(r"```powershell\n(.*?)```", text, re.DOTALL)
    assert blocks, "AGENTS.md has no fenced powershell block"
    for block in blocks:
        for line in block.splitlines():
            if line.lstrip().startswith("#"):
                continue  # a comment may hold a bare apostrophe ("don't")
            # Left-to-right tokenization: each quoted segment is consumed whole,
            # so `cmd 'a' "b" 'c'` is not mistaken for a `' "b" '` segment.
            for token in _QUOTED_SEGMENT.finditer(line):
                segment = token.group(0)
                assert not (segment.startswith("'") and '"' in segment), line


def _flag_values(command: list[str], long: str, short: str) -> list[str]:
    """Values of `--long V`, `--long=V` and `-s V` (cargo accepts repeats)."""
    values: list[str] = []
    for index, token in enumerate(command):
        if token in (long, short):
            values.extend(command[index + 1 : index + 2])
        elif token.startswith(f"{long}="):
            values.append(token.split("=", 1)[1])
    return values


def _is_backend_rustdoc_leg(command: list[str]) -> bool:
    """`cargo doc -p prin-sim … --features <backend>[,…]` in any option order."""
    if command[:2] != ["cargo", "doc"]:
        return False
    if "prin-sim" not in _flag_values(command, "--package", "-p"):
        return False
    features = {
        feature
        for value in _flag_values(command, "--features", "-F")
        for feature in value.split(",")
    }
    return bool(_GPU_BACKEND_FEATURES & features)


def _job_block(workflow: str, line_index: int) -> str:
    """Text of the 2-space-indented `jobs:` entry containing line `line_index`."""
    lines = workflow.splitlines()
    starts = [i for i, line in enumerate(lines) if _JOB_HEADER.match(line)]
    start = max(i for i in starts if i <= line_index)
    end = min((i for i in starts if i > line_index), default=len(lines))
    return "\n".join(lines[start:end])


def test_rustdoc_gate_documents_the_feature_gated_gpu_module() -> None:
    """PR32-F9 / DV-042: CI and the local gate must rustdoc `prin-sim` with a backend.

    `crates/prin-sim/src/lib.rs` gates `pub mod gpu` on `cpu|cuda|wgpu` and
    `default = []`, so `cargo doc --workspace --no-deps` alone never documents
    it and the DV-042 broken-intra-doc-link regression could recur silently. A
    non-backend feature (`strict-checks`) would not compile the module either,
    and `-D warnings` must reach the step through the same job's `env`.
    """
    rust_workflow = (REPO_ROOT / ".github" / "workflows" / "rust.yml").read_text(
        encoding="utf-8"
    )
    legs = [
        (index, shlex.split(match.group(1), posix=True))
        for index, line in enumerate(rust_workflow.splitlines())
        if (match := _RUN_LINE.match(line))
    ]
    hosted = [index for index, command in legs if _is_backend_rustdoc_leg(command)]
    assert hosted, "rust.yml has no `cargo doc -p prin-sim --features <backend>` leg"
    # Job-level `env:` (4-space indent; blank and comment lines allowed), not a
    # step-level one on another step - for EVERY job that runs such a leg.
    job_env_flags = re.compile(
        r"^    env:[ \t]*(?:#.*)?\n(?:[ \t]*(?:#.*)?\n|      .*\n)*?"
        r"      RUSTDOCFLAGS:[ \t]*[\"']?-D warnings[\"']?[ \t]*$",
        re.MULTILINE,
    )
    for index in hosted:
        assert job_env_flags.search(_job_block(rust_workflow, index)), (
            "the rust.yml job running the prin-sim rustdoc leg must set "
            'RUSTDOCFLAGS: "-D warnings" in its job-level env'
        )

    local = [
        line.strip()
        for line in AGENTS.read_text(encoding="utf-8").splitlines()
        if "cargo doc" in line and "prin-sim" in line
    ]
    assert any(
        "RUSTDOCFLAGS='-D warnings'" in line
        and _is_backend_rustdoc_leg(
            shlex.split(line[line.index("cargo") :], posix=True)
        )
        for line in local
    ), (
        "AGENTS.md has no `RUSTDOCFLAGS='-D warnings'; "
        "cargo doc -p prin-sim --features <backend>` line"
    )


def _mypy_module_name(path: Path) -> str:
    """Module name mypy assigns: the stem, prefixed by every enclosing package."""
    parts = [] if path.stem == "__init__" else [path.stem]
    parent = path.parent
    while parent != parent.parent and (
        (parent / "__init__.py").exists() or (parent / "__init__.pyi").exists()
    ):
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


def test_campaign_analysis_script_basenames_are_unique() -> None:
    """PR32-F12: `mypy DOCS/experiments/ --strict` needs unique module names.

    Campaign record roots are sibling directories without `__init__.py`, so
    mypy derives bare module names from file names (packages are crawled up
    through their `__init__.py`) and aborts with `Duplicate module named ...`
    (not a typing error) when two campaigns ship the same module name —
    `--explicit-package-bases` does not help. Prefix analysis scripts with the
    campaign id.
    """
    seen: dict[str, Path] = {}
    for path in sorted(CAMPAIGN_ROOT.rglob("*")):
        if path.suffix not in {".py", ".pyi"} or "__pycache__" in path.parts:
            continue
        other = seen.setdefault(_mypy_module_name(path), path)
        # `x.py` beside its own stub `x.pyi` is one module, not a duplicate.
        assert other.parent == path.parent, (
            f"duplicate campaign module name: {other} and {path}"
        )

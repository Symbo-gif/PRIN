"""Installation/environment verification checks for ``verify-installation``.

Distinguishes hard requirements (fail the overall check) from optional
accelerators/integrations (warn only), per the plan's "graceful partial
functionality" requirement.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any

from ci_config import Settings


@dataclass
class CheckResult:
    """One verification check's outcome.

    Attributes:
        name: Short check name.
        status: ``"pass"``, ``"warn"``, or ``"fail"``.
        detail: Human-readable explanation.
        required: Whether this check's failure fails the overall report.
    """

    name: str
    status: str
    detail: str
    required: bool


def run_verification(settings: Settings) -> dict[str, Any]:
    """Run every installation/environment check.

    Args:
        settings: Resolved settings.

    Returns:
        A report dict with ``"overall"`` set to ``"pass"`` or ``"fail"`` and
        a ``"checks"`` list of individual results.
    """
    checks: list[CheckResult] = []
    checks.append(_check_python_version())
    checks.append(_check_repo_root(settings))
    checks.append(_check_sqlite())
    checks.append(_check_import("networkx", required=True))
    checks.append(_check_import("yaml", required=True, display_name="PyYAML"))
    checks.append(_check_import("pathspec", required=True))
    checks.append(_check_import("mcp", required=True, display_name="MCP SDK"))
    checks.append(
        _check_import(
            "tree_sitter",
            required=False,
            display_name="tree-sitter (optional accelerator)",
        )
    )
    checks.append(
        _check_import(
            "opentelemetry",
            required=False,
            display_name="opentelemetry (optional bridge)",
        )
    )
    checks.append(
        _check_executable(
            "git", required=False, note="required only for hotspots --metric churn"
        )
    )
    checks.append(
        _check_executable(
            "snyk",
            required=False,
            note="required only for the Snyk secure-development gate",
        )
    )
    checks.append(_check_writable_dir(settings.db_path.parent, "db_path parent"))
    checks.append(_check_writable_dir(settings.output_dir, "output_dir"))
    checks.append(_check_writable_dir(settings.telemetry_dir, "telemetry_dir"))

    overall = (
        "fail" if any(c.status == "fail" and c.required for c in checks) else "pass"
    )
    return {
        "overall": overall,
        "repo_root": str(settings.repo_root),
        "db_path": str(settings.db_path),
        "telemetry_enabled": settings.telemetry_enabled,
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "detail": c.detail,
                "required": c.required,
            }
            for c in checks
        ],
    }


def _check_python_version() -> CheckResult:
    ok = sys.version_info >= (3, 11)
    return CheckResult(
        "python_version",
        "pass" if ok else "fail",
        f"Python {sys.version.split()[0]}",
        required=True,
    )


def _check_repo_root(settings: Settings) -> CheckResult:
    exists = settings.repo_root.exists() and (settings.repo_root / ".git").exists()
    return CheckResult(
        "repo_root",
        "pass" if exists else "fail",
        f"{settings.repo_root} "
        f"({'a git repository' if exists else 'not found or not a git repo'})",
        required=True,
    )


def _check_sqlite() -> CheckResult:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("SELECT 1")
        conn.close()
        return CheckResult(
            "sqlite3", "pass", f"sqlite3 {sqlite3.sqlite_version}", required=True
        )
    except sqlite3.Error as exc:  # pragma: no cover - sqlite3 is a stdlib guarantee
        return CheckResult("sqlite3", "fail", str(exc), required=True)


def _check_import(
    module: str, *, required: bool, display_name: str | None = None
) -> CheckResult:
    name = display_name or module
    try:
        mod = __import__(module)
        version = getattr(mod, "__version__", "unknown version")
        return CheckResult(
            module, "pass", f"{name} {version} available", required=required
        )
    except ImportError:
        status = "fail" if required else "warn"
        return CheckResult(module, status, f"{name} not importable", required=required)


def _check_executable(name: str, *, required: bool, note: str) -> CheckResult:
    path = shutil.which(name)
    if path:
        return CheckResult(name, "pass", f"found at {path}", required=required)
    return CheckResult(
        name,
        "warn" if not required else "fail",
        f"not found on PATH ({note})",
        required=required,
    )


def _check_writable_dir(path: Any, label: str) -> CheckResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return CheckResult(label, "pass", f"{path} is writable", required=True)
    except OSError as exc:
        return CheckResult(label, "fail", f"{path} not writable: {exc}", required=True)

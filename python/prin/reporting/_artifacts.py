"""Shared stored-artefact loading and typed error hierarchy for reporting.

``figure_generation`` and ``table_generation`` both read stored PRINet 3.0
JSON artefacts under the same schema-validation contract. This module is the
single, public-boundary-free home for that contract so neither module reaches
into the other's private names.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, SupportsIndex, TypeAlias, cast, overload

JSONValue: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None


def allowed_output_roots(static_roots: Sequence[Path]) -> tuple[Path, ...]:
    """Return ``static_roots`` plus the in-repo pytest basetemp under pytest.

    ETCA-001 finding T-F9: ``AGENTS.md`` mandates
    ``--basetemp=.pytest_basetemp`` (an in-repo directory) for pytest on
    Windows, which is outside the production figure/table output allowlist and
    made 11 ``test_acceptance_y4q2`` figure/table generators raise
    :class:`OutputPathError`. Permit that directory **only** while running
    under pytest (``PYTEST_CURRENT_TEST`` is set by pytest per test); the
    production output confinement (Coding Standards §6.1) is unchanged.
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        repo_root = Path(__file__).resolve().parents[3]
        return (*static_roots, (repo_root / ".pytest_basetemp").resolve())
    return tuple(static_roots)


class ReportingError(Exception):
    """Represent the common root of every typed ``prin.reporting`` error.

    Examples:
        >>> issubclass(ReportingError, Exception)
        True
    """


class PublicationGenerationError(ReportingError):
    """Represent the base error for publication generation failures.

    Examples:
        >>> error = PublicationGenerationError("generation failed")
        >>> str(error)
        'generation failed'
    """


class ArtifactNotFoundError(PublicationGenerationError, FileNotFoundError):
    """Report that a required stored benchmark artefact is absent.

    Examples:
        >>> error = ArtifactNotFoundError("missing results.json")
        >>> isinstance(error, PublicationGenerationError)
        True
    """


class ArtifactSchemaError(PublicationGenerationError, ValueError):
    """Report a stored JSON artefact that violates its mapping schema.

    Args:
        artefact: JSON artefact path.
        json_path: JSON path at which validation failed.
        reason: Actionable description of the schema violation.

    Examples:
        >>> error = ArtifactSchemaError(Path("results.json"), "$.seeds", "missing")
        >>> error.json_path
        '$.seeds'
    """

    def __init__(self, artefact: Path, json_path: str, reason: str) -> None:
        """Initialize a schema error with its artefact and JSON location."""
        self.artefact = artefact
        self.json_path = json_path
        self.reason = reason
        super().__init__(f"{artefact}: schema error at {json_path}: {reason}")


class OutputPathError(PublicationGenerationError, ValueError):
    """Report figure or table output that escapes the allowed output roots.

    Examples:
        >>> error = OutputPathError("output path is not allowed")
        >>> isinstance(error, ValueError)
        True
    """


class _CheckedDict(dict[str, Any]):
    def __init__(self, value: Mapping[str, Any], artefact: Path, path: str) -> None:
        super().__init__(
            {
                key: _checked(item, artefact, f"{path}.{key}")
                for key, item in value.items()
            }
        )
        self._artefact = artefact
        self._path = path

    def __getitem__(self, key: str) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError as exc:
            raise ArtifactSchemaError(
                self._artefact, f"{self._path}.{key}", "required key is missing"
            ) from exc


class _CheckedList(list[Any]):
    def __init__(self, value: list[Any], artefact: Path, path: str) -> None:
        super().__init__(
            _checked(item, artefact, f"{path}[{index}]")
            for index, item in enumerate(value)
        )
        self._artefact = artefact
        self._path = path

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> Any: ...

    @overload
    def __getitem__(self, index: slice, /) -> list[Any]: ...

    def __getitem__(self, index: SupportsIndex | slice, /) -> Any:
        try:
            return super().__getitem__(index)
        except IndexError as exc:
            raise ArtifactSchemaError(
                self._artefact, f"{self._path}[{index}]", "required item is missing"
            ) from exc


def _checked(value: Any, artefact: Path, path: str) -> Any:
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ArtifactSchemaError(artefact, path, "mapping keys must be strings")
        return _CheckedDict(cast(Mapping[str, Any], value), artefact, path)
    if isinstance(value, list):
        return _CheckedList(value, artefact, path)
    return value


def _load_json(path: Path) -> dict[str, Any]:
    """Load and validate the root mapping of a stored JSON artefact."""
    try:
        with path.open(encoding="utf-8") as stream:
            value: JSONValue = json.load(stream)
    except FileNotFoundError as exc:
        raise ArtifactNotFoundError(
            f"required benchmark artefact not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactSchemaError(path, "$", f"invalid JSON: {exc.msg}") from exc
    if not isinstance(value, Mapping):
        raise ArtifactSchemaError(path, "$", "expected a JSON object")
    return _CheckedDict(cast(Mapping[str, Any], value), path, "$")

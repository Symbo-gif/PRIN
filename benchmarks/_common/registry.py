"""Category/benchmark registry backing the ``benchrunner`` CLI.

Each of the nine topic packages registers its benchmark functions here under
its category name; ``benchrunner`` dispatches ``--category``/``--list``
against this single source of truth instead of hard-coding imports.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from benchmarks._common.config import BenchmarkConfig

#: The nine topic categories declared in ``benchmarks/README.md`` and
#: Benchmarking and Reproducibility Standards §2.1.
CATEGORIES: tuple[str, ...] = (
    "scaling",
    "chimera",
    "mot",
    "ablations",
    "kernels",
    "integrators",
    "training",
    "daemon",
    "adversarial",
)

BenchmarkFn = Callable[[BenchmarkConfig], dict[str, Any]]


@dataclass(frozen=True)
class BenchmarkSpec:
    """A single registered, runnable benchmark.

    Attributes:
        category: One of :data:`CATEGORIES`.
        name: Unique name within the category.
        fn: Callable taking a :class:`BenchmarkConfig` and returning a
            JSON-serializable payload (excluding the shared environment/
            config envelope, which ``benchrunner`` adds).
        summary: One-line human-readable description, shown by ``--list``.
    """

    category: str
    name: str
    fn: BenchmarkFn
    summary: str


_REGISTRY: dict[tuple[str, str], BenchmarkSpec] = {}


class RegistryError(ValueError):
    """Raised on invalid category names or duplicate/unknown registrations."""


def register(
    category: str, name: str, *, summary: str
) -> Callable[[BenchmarkFn], BenchmarkFn]:
    """Decorator registering a benchmark function under ``category``/``name``.

    Args:
        category: Must be one of :data:`CATEGORIES`.
        name: Unique name within the category.
        summary: One-line description shown by ``benchrunner --list``.

    Returns:
        A decorator that registers and returns the function unchanged.

    Raises:
        RegistryError: If ``category`` is not one of :data:`CATEGORIES`, or
            ``(category, name)`` is already registered.
    """
    if category not in CATEGORIES:
        raise RegistryError(
            f"unknown category {category!r}; must be one of {CATEGORIES}"
        )

    def decorator(fn: BenchmarkFn) -> BenchmarkFn:
        key = (category, name)
        if key in _REGISTRY:
            raise RegistryError(f"benchmark {key!r} is already registered")
        _REGISTRY[key] = BenchmarkSpec(
            category=category, name=name, fn=fn, summary=summary
        )
        return fn

    return decorator


def get(category: str, name: str) -> BenchmarkSpec:
    """Look up a single registered benchmark.

    Raises:
        RegistryError: If no benchmark is registered under ``(category, name)``.
    """
    try:
        return _REGISTRY[(category, name)]
    except KeyError as exc:
        raise RegistryError(f"no benchmark registered as {(category, name)!r}") from exc


def list_specs(category: str | None = None) -> list[BenchmarkSpec]:
    """List registered benchmarks, optionally filtered to one category.

    Raises:
        RegistryError: If ``category`` is given and is not one of
            :data:`CATEGORIES`.
    """
    if category is not None and category not in CATEGORIES:
        raise RegistryError(
            f"unknown category {category!r}; must be one of {CATEGORIES}"
        )
    specs = sorted(_REGISTRY.values(), key=lambda s: (s.category, s.name))
    if category is None:
        return specs
    return [s for s in specs if s.category == category]

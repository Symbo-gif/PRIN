"""Type declarations for PRIN deprecation and API-freeze helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

FROZEN_PUBLIC_API: frozenset[str]

def deprecated(
    since: str, message: str, removal: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def deprecated_parameter(
    param_name: str, since: str, message: str
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def verify_api_surface(module_all: list[str]) -> tuple[set[str], set[str]]: ...

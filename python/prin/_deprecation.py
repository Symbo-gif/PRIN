"""Deprecation helpers and PRIN RC1 public-API freeze enforcement.

``FROZEN_PUBLIC_API`` is derived from the same PRIN-owned canonical tuple as
``prin.__all__``. It intentionally does not copy PRINet 3.0's historical frozen
set, which predates many symbols in that package's final public surface.
"""

from __future__ import annotations

import functools
import warnings
from collections.abc import Callable
from typing import Any, TypeVar, cast

from prin._public_api import RC1_PUBLIC_API

F = TypeVar("F", bound=Callable[..., Any])

FROZEN_PUBLIC_API: frozenset[str] = frozenset(RC1_PUBLIC_API)


def deprecated(
    since: str,
    message: str,
    removal: str | None = None,
) -> Callable[[F], F]:
    """Mark a callable as deprecated.

    Args:
        since: Version in which the deprecation was introduced.
        message: Actionable migration guidance.
        removal: Optional version in which the callable will be removed.

    Returns:
        A decorator that emits ``DeprecationWarning`` on every call.
    """

    def decorator(func: F) -> F:
        """Wrap one callable with the configured symbol deprecation."""
        removal_note = f" Will be removed in {removal}." if removal else ""
        warning = (
            f"{func.__qualname__} is deprecated since v{since}. {message}{removal_note}"
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Emit the configured warning and invoke the wrapped callable."""
            warnings.warn(warning, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def deprecated_parameter(
    param_name: str,
    since: str,
    message: str,
) -> Callable[[F], F]:
    """Warn when a deprecated keyword argument is supplied.

    Args:
        param_name: Deprecated keyword parameter name.
        since: Version in which the deprecation was introduced.
        message: Actionable migration guidance.

    Returns:
        A decorator that warns only when ``param_name`` appears in keyword
        arguments.
    """

    def decorator(func: F) -> F:
        """Wrap one callable with the configured parameter deprecation."""
        warning = (
            f"Parameter '{param_name}' of {func.__qualname__} is deprecated "
            f"since v{since}. {message}"
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Warn for the deprecated keyword and invoke the callable."""
            if param_name in kwargs:
                warnings.warn(warning, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def verify_api_surface(module_all: list[str]) -> tuple[set[str], set[str]]:
    """Compare a module export list with PRIN's frozen RC1 contract.

    Args:
        module_all: Top-level ``prin.__all__`` names to verify.

    Returns:
        ``(missing_from_module, extra_in_module)``. Both sets are empty when
        the supplied surface exactly matches the frozen contract.
    """
    current = set(module_all)
    return set(FROZEN_PUBLIC_API - current), current - FROZEN_PUBLIC_API

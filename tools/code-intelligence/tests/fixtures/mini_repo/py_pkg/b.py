"""Module B: imports module A back, completing the deliberate test cycle."""

from __future__ import annotations

from py_pkg import a


def bar() -> int:
    """Return a constant; also references module A to close the cycle."""
    _ = a.Widget
    return 42


def unused_orphan() -> None:
    """Has no callers anywhere in the fixture repo (dead-code heuristic target)."""

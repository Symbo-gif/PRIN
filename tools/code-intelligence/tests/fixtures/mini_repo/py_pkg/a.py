"""Module A: imports module B, forming a deliberate cycle for cycle tests."""

from __future__ import annotations

from py_pkg import b


def foo() -> int:
    """Call into module B to exercise cross-module call resolution."""
    return b.bar()


class Widget:
    """A trivial class used to test class/method extraction."""

    def render(self) -> str:
        """Render the widget."""
        return helper()


def helper() -> str:
    """A helper function, called only from within this module."""
    return "helper"


def test_foo_returns_int() -> None:
    """A fixture 'test' function, to exercise test-node classification."""
    assert isinstance(foo(), int)

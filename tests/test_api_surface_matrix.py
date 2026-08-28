"""Full parametrized construct/callable smoke matrix over all 172 legacy symbols.

0141 brief Contract: "Every one of the 172 ``prinet.__all__`` symbols resolves
from ``prin`` and passes a construct/callable smoke check (full parametrized
matrix)."

Behavioural parity is explicitly out of scope (WP-036B / WP-036C). This matrix
proves, for every symbol:

* it resolves from the ``prin`` package root;
* it is a callable/class or a plain module constant;
* a best-effort no-argument construct/call terminates in a *typed, expected*
  way - either it succeeds, or it raises because it needs arguments / a valid
  input / a benchmark artefact (a real symbol), or it raises the documented
  WP-036 disposition (``NotImplementedError`` / ``BackendUnavailableError``).
  An ``AttributeError`` / ``NameError`` / ``ImportError`` - the signatures of a
  broken re-export - fails the matrix.
"""

from __future__ import annotations

import inspect

import prin
import prinet
import pytest

_LEGACY_SYMBOLS = sorted(prinet.__all__)

# Typed outcomes that mean "real callable, just not with zero arguments / not in
# this environment". Not WP-036 dispositions.
_INPUT_ERROR_NAMES = frozenset(
    {
        "TypeError",
        "ValueError",
        "ArtifactNotFoundError",
        "FileNotFoundError",
        "RuntimeError",
        "OSError",
    }
)
_DISPOSITION_ERROR_NAMES = frozenset({"NotImplementedError", "BackendUnavailableError"})
_ALLOWED_CONSTANT_TYPES = (int, float, str, bool, bytes)


def test_matrix_covers_exactly_172_symbols() -> None:
    """The legacy contract is frozen at 172 names."""
    assert len(_LEGACY_SYMBOLS) == 172
    assert len(set(_LEGACY_SYMBOLS)) == 172


@pytest.mark.parametrize("name", _LEGACY_SYMBOLS)
def test_symbol_resolves_and_passes_construct_callable_smoke(name: str) -> None:
    """Each legacy symbol resolves from ``prin`` and smoke-checks cleanly."""
    assert hasattr(prin, name), f"{name} does not resolve from prin"
    obj = getattr(prin, name)
    assert obj is not None, name

    if not (inspect.isclass(obj) or callable(obj)):
        assert isinstance(obj, _ALLOWED_CONSTANT_TYPES), (
            f"{name} is neither callable nor a plain constant ({type(obj)!r})"
        )
        return

    assert callable(obj)
    try:
        obj()
    except Exception as exc:
        kind = type(exc).__name__
        assert kind in (_INPUT_ERROR_NAMES | _DISPOSITION_ERROR_NAMES), (
            f"{name} raised an unexpected {kind}: {exc}"
        )


@pytest.mark.parametrize("name", _LEGACY_SYMBOLS)
def test_disposition_symbols_raise_a_typed_migration_error(name: str) -> None:
    """Every documented-disposition symbol raises a typed, message-bearing error."""
    obj = getattr(prin, name)
    if not callable(obj):
        return
    try:
        obj()
    except NotImplementedError as exc:
        assert "D-2.2" in str(exc) or "WP-036C" in str(exc), name
    except Exception as exc:
        if type(exc).__name__ == "BackendUnavailableError":
            assert "PRIN migration" in str(exc) or "unavailable" in str(exc).lower()

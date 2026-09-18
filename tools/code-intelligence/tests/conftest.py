"""Pytest bootstrap: put ``tools/code-intelligence/`` on ``sys.path``.

The subsystem is deliberately not an installed/importable package (its
directory name contains a hyphen, matching every other script in
``tools/``); this conftest is the one place that makes its ``ci_*`` modules
importable for the test suite, mirroring what ``cli.py`` does for normal
invocation.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

_SUBSYSTEM_ROOT = Path(__file__).resolve().parent.parent
if str(_SUBSYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SUBSYSTEM_ROOT))

from ci_graph.store import GraphStore  # noqa: E402
from ci_indexer.orchestrator import run_index  # noqa: E402

FIXTURE_REPO = Path(__file__).resolve().parent / "fixtures" / "mini_repo"


@pytest.fixture
def fixture_repo() -> Path:
    """Absolute path to the synthetic multi-language fixture repository."""
    return FIXTURE_REPO


@pytest.fixture
def indexed_store(tmp_path: Path) -> Iterator[GraphStore]:
    """A GraphStore freshly indexed against the fixture repository."""
    store = GraphStore(tmp_path / "graph.db")
    run_index(store, FIXTURE_REPO, force=True)
    yield store
    store.close()

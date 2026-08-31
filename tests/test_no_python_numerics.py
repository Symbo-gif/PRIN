"""Regression: the WP-036 S1 (0141A-0141E) compat surface has no Python numerics.

Coding Standards Sec. 1.2. Evidence named in the 0141E brief Contract.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TOOL = _ROOT / "tools" / "check_no_python_numerics.py"

_spec = importlib.util.spec_from_file_location("_check_no_python_numerics", _TOOL)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def test_wp036_compat_surface_has_no_python_numerics() -> None:
    """The AST scan over every net-new WP-036 S1 compat module is clean."""
    assert _module.main() == 0


def test_every_scanned_module_exists_and_is_covered() -> None:
    """The scan list points only at real files and covers the new submodules."""
    for name in _module._SCANNED:
        assert (_ROOT / "python" / "prin" / name).is_file(), name
    for expected in (
        "_torch_compat.py",
        "nn/deferred_layers.py",
        "nn/inhibition_layers.py",
        "training_hooks.py",
        "solvers.py",
    ):
        assert expected in _module._SCANNED


def test_violations_detects_every_forbidden_pattern(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The AST scanner flags matmul, numeric helpers, bad imports, and nn subclasses."""
    offending = tmp_path / "offending.py"
    offending.write_text(
        "import scipy\n"
        "from torch.nn.functional import relu\n"
        "import torch\n"
        "def f(a, b):\n"
        "    c = a @ b\n"
        "    return torch.linalg.solve(c, b)\n"
        "class Bad(torch.nn.Module):\n"
        "    pass\n",
        encoding="utf-8",
    )
    hits = _module._violations(offending)
    joined = "\n".join(hits)
    assert "'@' matrix-multiplication" in joined
    assert "numeric helper '.solve'" in joined or "numeric helper '.linalg'" in joined
    assert "import scipy" in joined
    assert "from torch.nn.functional" in joined
    assert "subclasses a" in joined


def test_main_reports_a_missing_module(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A scan-list entry that does not exist fails the check loudly."""
    monkeypatch.setattr(_module, "_SCANNED", (*_module._SCANNED, "does_not_exist.py"))
    assert _module.main() == 1

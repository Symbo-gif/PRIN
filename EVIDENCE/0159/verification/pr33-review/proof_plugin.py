"""Pytest plugin for ``proof_defect_catching.py``: load one mutant EXP-002 driver.

``PR33_MUTATION_INDEX`` selects an entry of the harness's constant
``MUTATIONS`` table by number; nothing else is taken from the environment.
The plugin applies that entry's fixed substitution to the repository's own
driver source and executes the result as ``benchmarks.campaign.exp002_driver``
with the real ``__file__``, so the regression tests import the mutant while
every path constant stays the repository's. Without the variable the plugin
does nothing.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRIVER = ROOT / "benchmarks" / "campaign" / "exp002_driver.py"


def pytest_configure(config: object) -> None:
    """Install the selected mutant before any test module is imported."""
    selected = os.environ.get("PR33_MUTATION_INDEX", "")
    if not selected.isdigit():
        return
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(HERE))
    from proof_defect_catching import MUTATIONS

    import benchmarks.campaign as package

    _, _, current, prefix, _ = MUTATIONS[int(selected)]
    source = DRIVER.read_text(encoding="utf-8")
    if source.count(current) != 1:
        raise RuntimeError("mutation anchor no longer matches the driver")
    module = types.ModuleType("benchmarks.campaign.exp002_driver")
    module.__file__ = str(DRIVER)
    module.__package__ = "benchmarks.campaign"
    sys.modules[module.__name__] = module
    code = compile(source.replace(current, prefix), str(DRIVER), "exec")
    exec(code, module.__dict__)  # noqa: S102 - fixed, audited mutant table
    package.exp002_driver = module  # type: ignore[attr-defined]

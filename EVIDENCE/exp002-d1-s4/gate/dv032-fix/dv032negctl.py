"""Negative controls proving the DV-032 replacement assertions have teeth.

Kept OUTSIDE the repository at run time and loaded with ``-p dv032negctl`` so it
is not collected as a test module.  Selected by ``DV032_NEGCTL``:

  ``cpu``        each daemon inference also burns 3.0 s of wall CPU, so the
                 daemon thread adds real process CPU time inside the measurement
                 window.  The process-CPU ratio assertion MUST fail.
  ``errors``     the ONNX tensor conversion raises inside ``_run_inference``'s own
                 try block, so the daemon counts the failure and dead-letters it.
                 The deterministic error/dlq assertions MUST fail.
  ``report``     no hog; the ratio limit is dropped to 0.0 so the assertion fails
                 and its message reveals the ratio a NORMAL daemon produces.
  ``cpu-report`` hog plus limit 0.0, revealing the ratio the hog produces.
  unset          no patch; the test must PASS.

Two harness lessons are applied here, both learned by getting them wrong first:

* The limit is patched through ``item.module`` in ``pytest_runtest_setup``, NOT
  via ``import tests.test_acceptance_subconscious``.  ``tests/`` has no
  ``__init__.py``, so under pytest's prepend import mode the collected module is
  the TOP-LEVEL ``test_acceptance_subconscious``; a ``tests.*`` import binds a
  distinct module object and patching it silently does nothing.  (The daemon
  patch is unaffected because ``SubconsciousDaemon`` is one shared class object
  reached through ``prin``.)
* ``errors`` patches ``SubconsciousState.to_tensor``, which is called INSIDE
  ``_run_inference``'s ``try``.  Replacing ``_run_inference`` wholesale with a
  raiser would instead kill the daemon thread, because the real method catches
  ``Exception`` and increments ``error_count`` itself.
"""

from __future__ import annotations

import os
import time

import pytest

MODE = os.environ.get("DV032_NEGCTL", "")
SPIN_SECONDS = 3.0
_REPORT_MODES = ("report", "cpu-report")


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Drop the ratio limit to 0.0 so a passing run still reports its ratio.

    Patched on the collected module object itself; see the module docstring.
    """
    if MODE in _REPORT_MODES:
        item.module._DAEMON_CPU_RATIO_LIMIT = 0.0


@pytest.fixture(autouse=True)
def _negative_control() -> object:
    if not MODE:
        yield None
        return None

    from prin.subconscious_compat import SubconsciousDaemon, SubconsciousState

    orig_infer = SubconsciousDaemon._run_inference
    orig_tensor = SubconsciousState.to_tensor

    if MODE in ("cpu", "cpu-report"):

        def spinning(self: object, state: object) -> None:
            deadline = time.perf_counter() + SPIN_SECONDS
            acc = 0.0
            while time.perf_counter() < deadline:
                acc = (acc + 1.0) ** 0.5
            return orig_infer(self, state)  # type: ignore[arg-type]

        SubconsciousDaemon._run_inference = spinning  # type: ignore[method-assign]

    elif MODE == "report":
        pass  # ratio reporting only; no behavioural patch

    elif MODE == "errors":

        def failing(self: object) -> object:
            raise RuntimeError("negative control: forced inference failure")

        SubconsciousState.to_tensor = failing  # type: ignore[method-assign]

    else:
        raise AssertionError(f"unknown DV032_NEGCTL mode: {MODE!r}")

    try:
        yield None
    finally:
        SubconsciousDaemon._run_inference = orig_infer  # type: ignore[method-assign]
        SubconsciousState.to_tensor = orig_tensor  # type: ignore[method-assign]
    return None

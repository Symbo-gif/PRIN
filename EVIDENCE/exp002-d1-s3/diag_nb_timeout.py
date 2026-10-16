"""Diagnostic-only pytest plugin: keep the notebook timeout from censoring a run.

This file is a *measurement aid*, not a gate and not a fix. It exists for the
disposition of audit finding ``EXP002D1-S2-F2``. With the shipped 900 s per-cell
bound, a notebook leg that is slow inside the full suite is *killed* at 900 s, so
its true in-suite duration is never observed (the data are censored). To size a
bound from evidence (Testing Standards section 7 item 2) the slow leg has to be
allowed to finish once, while the host is observed.

Loading this plugin (``-p diag_nb_timeout`` with ``EVIDENCE/exp002-d1-s3`` on
``PYTHONPATH``) wraps ``nbclient.NotebookClient.__init__`` in the pytest process
so that every notebook client is built with a four-hour per-cell timeout. It does
nothing else: no test is selected, skipped, reordered or altered, no assertion is
touched, and ``tests/test_notebooks.py`` on disk is unchanged. The gate runs of
this session do **not** load it.

A run that loads this plugin is recorded as a *diagnostic* run and is never
reported as the required full-suite gate.
"""

from __future__ import annotations

from typing import Any

import nbclient

DIAGNOSTIC_CELL_TIMEOUT_SECONDS = 14400

_original_init: Any = nbclient.NotebookClient.__init__


def _init_with_diagnostic_timeout(self: Any, *args: Any, **kwargs: Any) -> None:
    """Build a ``NotebookClient`` with the diagnostic per-cell timeout.

    Args:
        self: The client being constructed.
        *args: Positional arguments passed through unchanged.
        **kwargs: Keyword arguments passed through, with ``timeout`` replaced.
    """
    kwargs["timeout"] = DIAGNOSTIC_CELL_TIMEOUT_SECONDS
    _original_init(self, *args, **kwargs)


nbclient.NotebookClient.__init__ = _init_with_diagnostic_timeout  # type: ignore[method-assign]

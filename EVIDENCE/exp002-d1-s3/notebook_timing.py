"""Time one shipped notebook exactly as ``tests/test_notebooks.py`` executes it.

This instrument backs the disposition of audit finding ``EXP002D1-S2-F2``: the
required full suite exceeded the 900 s per-cell bound on
``test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]``. The question
that disposition must answer is *where the time goes* when that notebook runs
inside the suite versus alone, so the instrument records, for one notebook:

* wall-clock time of every code cell (from nbclient's ``record_timing``);
* the notebook kernel's accumulated CPU time, working set and thread count,
  sampled on a fixed cadence, so a compute-bound slowdown (CPU time tracks wall
  time) can be told apart from a starved or blocked one (CPU time << wall time);
* host CPU utilisation and available memory at each sample.

It runs the notebook the way the test does (same ``NotebookClient`` arguments,
same ``kernel_name`` and working directory). It never modifies a notebook on
disk: nbclient executes an in-memory copy and the result is discarded.

The notebook is selected by *name* from the closed set discovered under
``notebooks/``, so no caller-supplied path is ever turned into a filesystem
path.

Run from the repository root with the project venv::

    .venv/Scripts/python.exe EVIDENCE/exp002-d1-s3/notebook_timing.py \
        --notebook 02_clevr_n_binding.ipynb --label alone

Output is one JSON document on stdout. Exit status is 0 when the notebook ran
to completion without an error output, 1 when a cell raised or timed out.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import nbformat
import psutil
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = REPO_ROOT / "notebooks"


def discovered_notebooks() -> dict[str, Path]:
    """Return the shipped notebooks keyed by file name.

    Returns:
        A mapping from notebook file name to its path under ``notebooks/``.
    """
    return {path.name: path for path in sorted(NOTEBOOK_DIR.glob("*.ipynb"))}


def _kernel_processes() -> list[psutil.Process]:
    """Return this process's descendant ``ipykernel`` launcher processes.

    Returns:
        Zero or more kernel processes (normally exactly one while a notebook runs).
    """
    found: list[psutil.Process] = []
    for child in psutil.Process().children(recursive=True):
        try:
            if "ipykernel_launcher" in " ".join(child.cmdline()):
                found.append(child)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


class Sampler(threading.Thread):
    """Sample the kernel and the host on a fixed cadence until stopped."""

    def __init__(self, period_seconds: float) -> None:
        """Create the sampler.

        Args:
            period_seconds: Seconds between samples.
        """
        super().__init__(daemon=True)
        self.period = period_seconds
        self.samples: list[dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._t0 = time.monotonic()

    def stop(self) -> None:
        """Ask the sampler to finish after its current sample."""
        self._stop_event.set()

    def run(self) -> None:
        """Take samples until :meth:`stop` is called."""
        psutil.cpu_percent(interval=None)
        while not self._stop_event.wait(self.period):
            self.samples.append(self._one_sample())

    def _one_sample(self) -> dict[str, Any]:
        """Take one sample of the kernel and of the host.

        Returns:
            A JSON-serialisable record.
        """
        kernels = _kernel_processes()
        kernel: dict[str, Any] = {"present": bool(kernels)}
        if kernels:
            # On Windows the venv ``python.exe`` is a launcher stub that spawns
            # the real interpreter, so both match; sum the whole kernel tree.
            cpu = rss = threads = faults = 0.0
            for proc in kernels:
                try:
                    times = proc.cpu_times()
                    cpu += times.user + times.system
                    info = proc.memory_info()
                    rss += info.rss
                    faults += getattr(info, "num_page_faults", 0)
                    threads += proc.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            kernel.update(
                processes=len(kernels),
                cpu_seconds=round(cpu, 2),
                working_set_mb=round(rss / 2**20, 1),
                threads=int(threads),
                page_faults=int(faults),
            )
        memory = psutil.virtual_memory()
        return {
            "t_wall": round(time.monotonic() - self._t0, 1),
            "host_cpu_percent": psutil.cpu_percent(interval=None),
            "host_available_mb": round(memory.available / 2**20),
            "host_memory_percent": memory.percent,
            "kernel": kernel,
        }


def _cell_wall_seconds(document: Any) -> list[dict[str, Any]]:
    """Return per-code-cell wall time from nbclient's recorded timing.

    Args:
        document: The executed in-memory notebook.

    Returns:
        One record per code cell with its index and wall seconds (``None`` if
        the cell never ran).
    """
    rows: list[dict[str, Any]] = []
    for index, cell in enumerate(document.cells):
        if cell.cell_type != "code":
            continue
        timing = cell.get("metadata", {}).get("execution", {})
        start = timing.get("iopub.execute_input")
        end = timing.get("shell.execute_reply")
        seconds: float | None = None
        if start and end:
            parse = datetime.fromisoformat
            seconds = round((parse(end) - parse(start)).total_seconds(), 2)
        rows.append({"cell": index, "wall_seconds": seconds})
    return rows


def _error_outputs(document: Any) -> list[str]:
    """Return a one-line summary of every error output in the notebook.

    Args:
        document: The executed in-memory notebook.

    Returns:
        ``"cell N: ename: evalue"`` strings.
    """
    errors: list[str] = []
    for index, cell in enumerate(document.cells):
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(
                    f"cell {index}: {output.get('ename')}: {output.get('evalue')}"
                )
    return errors


def run(
    name: str, timeout: int, period: float, label: str
) -> tuple[dict[str, Any], int]:
    """Execute one notebook and measure it.

    Args:
        name: Notebook file name; must be one of :func:`discovered_notebooks`.
        timeout: nbclient per-cell timeout in seconds (the test uses 900).
        period: Sampling cadence in seconds.
        label: Free-text label recorded in the output.

    Returns:
        The measurement record and the process exit status.
    """
    path = discovered_notebooks()[name]
    read_notebook: Any = nbformat.read  # nbformat ships no type information
    document = read_notebook(path, as_version=4)
    client = NotebookClient(
        document,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(REPO_ROOT)}},
        record_timing=True,
    )
    sampler = Sampler(period)
    started_utc = datetime.now(UTC).isoformat(timespec="seconds")
    start = time.monotonic()
    sampler.start()
    outcome = "completed"
    try:
        client.execute()
    except Exception as exc:
        outcome = (
            f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}"
        )
    wall = time.monotonic() - start
    sampler.stop()
    sampler.join(timeout=period + 5)

    kernel_cpu = [
        s["kernel"]["cpu_seconds"]
        for s in sampler.samples
        if s["kernel"].get("cpu_seconds") is not None
    ]
    peak_ws = max(
        (
            s["kernel"]["working_set_mb"]
            for s in sampler.samples
            if "working_set_mb" in s["kernel"]
        ),
        default=None,
    )
    host_cpu = [s["host_cpu_percent"] for s in sampler.samples]
    avail = [s["host_available_mb"] for s in sampler.samples]
    errors = _error_outputs(document)
    record: dict[str, Any] = {
        "label": label,
        "notebook": name,
        "started_utc": started_utc,
        "per_cell_timeout_seconds": timeout,
        "sample_period_seconds": period,
        "outcome": outcome,
        "error_outputs": errors,
        "wall_seconds": round(wall, 1),
        "kernel_cpu_seconds_last_sample": kernel_cpu[-1] if kernel_cpu else None,
        "kernel_cpu_over_wall": round(kernel_cpu[-1] / wall, 2)
        if kernel_cpu and wall
        else None,
        "kernel_peak_working_set_mb": peak_ws,
        "host_cpu_percent_mean": round(sum(host_cpu) / len(host_cpu), 1)
        if host_cpu
        else None,
        "host_available_mb_min": min(avail) if avail else None,
        "logical_cpus": psutil.cpu_count(logical=True),
        "cells": _cell_wall_seconds(document),
        "samples": sampler.samples,
    }
    return record, 0 if outcome == "completed" and not errors else 1


def main(argv: list[str]) -> int:
    """Parse arguments, run the measurement and print it.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The process exit status.
    """
    known = sorted(discovered_notebooks())
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("--notebook", required=True, choices=known)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--period", type=float, default=5.0)
    parser.add_argument("--label", default="unlabelled")
    args = parser.parse_args(argv)
    record, status = run(args.notebook, args.timeout, args.period, args.label)
    print(json.dumps(record, indent=1))
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

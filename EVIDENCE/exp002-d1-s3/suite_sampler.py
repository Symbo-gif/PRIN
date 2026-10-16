"""Watch a running pytest session from outside it, and summarise notebook legs.

This instrument backs the disposition of audit finding ``EXP002D1-S2-F2``: the
required full suite exceeded the 900 s per-cell bound on
``test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]`` in two
consecutive sessions, while the same notebook completes alone in about a
minute. To say *why* a notebook leg is slow inside the suite, someone has to
look at the machine while the suite runs. This tool does that without touching
the run: it is a separate process that only reads the process table.

``sample`` (default) waits for a ``python -m pytest`` process to appear, then
every ``--period`` seconds prints one JSON object per line with:

* the pytest process tree: CPU seconds, working set, threads, page faults;
* every notebook kernel (``ipykernel_launcher``) it can see, with the same
  counters and its age, so a kernel's CPU seconds can be compared with its wall
  seconds (a compute-bound leg tracks wall time; a starved leg does not);
* host CPU utilisation, available physical memory, available commit and the
  ``Pages Input/sec`` hard-fault counter (``typeperf``), which separates memory
  pressure from CPU contention;
* the five largest resident processes by name, so resident IDE or language
  server load is visible, plus the CPU share of the busiest non-pytest process.

It stops when no pytest process has been present for two consecutive samples.

``--summarize`` reads those lines on standard input and prints, for each
notebook-kernel episode, its wall time, CPU seconds, CPU/wall ratio, peak
working set, and the host's memory and paging while it ran, plus the pytest
tree's working set at the start of the episode.

No caller-supplied path is read or written: the sampler writes to standard
output and the summariser reads standard input::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/suite_sampler.py \
        > samples.jsonl &
    ...run the suite...
    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/suite_sampler.py \
        --summarize < samples.jsonl

Windows only (it uses ``GlobalMemoryStatusEx`` and ``typeperf``).
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import json
import os
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

# A fixed absolute path, not one derived from an environment variable: the
# executable must not be steerable by the caller's environment. If Windows is
# installed elsewhere the counter is simply reported as unavailable (null).
TYPEPERF = Path(r"C:\Windows\System32\typeperf.exe")


class _MemoryStatus(ctypes.Structure):
    """The ``MEMORYSTATUSEX`` structure of the Win32 API."""

    _fields_ = (
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    )


def commit_available_mb() -> float | None:
    """Return the system's remaining commit charge headroom in MiB.

    Returns:
        Available page-file-backed commit in MiB, or ``None`` if unavailable.
    """
    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(_MemoryStatus)
    kernel32 = getattr(ctypes, "windll", None)
    if kernel32 is None or not kernel32.kernel32.GlobalMemoryStatusEx(
        ctypes.byref(status)
    ):
        return None
    return round(float(status.ullAvailPageFile) / 2**20, 1)


def pages_input_per_second() -> float | None:
    r"""Read the system-wide hard-fault counter ``Memory\Pages Input/sec``.

    Returns:
        The instantaneous counter value, or ``None`` if ``typeperf`` failed.
    """
    if not TYPEPERF.is_file():
        return None
    try:
        done = subprocess.run(  # noqa: S603  # nosec B603 - fixed argv, no shell, no user input
            [str(TYPEPERF), r"\Memory\Pages Input/sec", "-sc", "1"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    # The CSV starts with a blank line and a header row; the first row whose
    # second field is a number is the sample.
    for row in csv.reader(done.stdout.splitlines()):
        if len(row) >= 2:
            try:
                return float(row[1])
            except ValueError:
                continue
    return None


def _cmdline(proc: psutil.Process) -> str:
    """Return a process's command line, or an empty string if unreadable.

    Args:
        proc: Process to inspect.

    Returns:
        The space-joined command line.
    """
    try:
        return " ".join(proc.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return ""


def _counters(procs: list[psutil.Process]) -> dict[str, Any]:
    """Sum CPU, resident size, threads and page faults over a process group.

    Args:
        procs: Processes forming one logical unit (a launcher stub plus the
            interpreter it spawns, for example).

    Returns:
        The aggregated counters.
    """
    cpu = rss = 0.0
    threads = faults = 0
    for proc in procs:
        try:
            times = proc.cpu_times()
            info = proc.memory_info()
            cpu += times.user + times.system
            rss += info.rss
            faults += int(getattr(info, "num_page_faults", 0))
            threads += proc.num_threads()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return {
        "processes": len(procs),
        "cpu_seconds": round(cpu, 2),
        "rss_mb": round(rss / 2**20, 1),
        "threads": threads,
        "page_faults": faults,
    }


def _find_groups() -> tuple[list[psutil.Process], list[psutil.Process]]:
    """Locate the pytest process group and the notebook-kernel processes.

    Returns:
        ``(pytest_processes, kernel_processes)``. A pytest process is one whose
        command line contains ``pytest`` and that is not a kernel.
    """
    pytest_procs: list[psutil.Process] = []
    kernels: list[psutil.Process] = []
    own = os.getpid()
    for proc in psutil.process_iter():
        if proc.pid == own:
            continue
        line = _cmdline(proc)
        if "ipykernel_launcher" in line:
            kernels.append(proc)
        elif "pytest" in line and "python" in line.lower():
            pytest_procs.append(proc)
    return pytest_procs, kernels


def _kernel_episodes(kernels: list[psutil.Process]) -> list[dict[str, Any]]:
    """Group kernel processes into logical kernels by parent/child relation.

    Args:
        kernels: All processes whose command line names ``ipykernel_launcher``.

    Returns:
        One record per logical kernel with its counters and age in seconds.
    """
    by_pid = {proc.pid: proc for proc in kernels}
    roots = []
    for proc in kernels:
        try:
            parent = proc.ppid()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        if parent not in by_pid:
            roots.append(proc)
    records = []
    for root in roots:
        group = [root]
        for other in kernels:
            if other is root:
                continue
            try:
                if any(p.pid == root.pid for p in other.parents()):
                    group.append(other)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        record = _counters(group)
        record["root_pid"] = root.pid
        try:
            record["age_seconds"] = round(time.time() - root.create_time(), 1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            record["age_seconds"] = None
        records.append(record)
    return records


def _top_resident(limit: int = 5) -> list[dict[str, Any]]:
    """Return the largest resident processes by name.

    Args:
        limit: How many to return.

    Returns:
        ``{"name", "rss_mb"}`` records, largest first.
    """
    rows = []
    for proc in psutil.process_iter(["name", "memory_info"]):
        info = proc.info
        memory = info.get("memory_info")
        if memory is not None:
            rows.append((memory.rss, info.get("name") or "?"))
    rows.sort(reverse=True)
    return [{"name": name, "rss_mb": round(rss / 2**20)} for rss, name in rows[:limit]]


def _top_cpu(
    previous: dict[int, float], exclude: set[int], limit: int = 5
) -> tuple[list[dict[str, Any]], dict[int, float]]:
    """Return the processes (grouped by name) that used the most CPU since last time.

    Args:
        previous: Cumulative CPU seconds per pid from the previous call.
        exclude: Pids to leave out (the pytest tree, the sampler itself and the
            notebook kernels, which are reported on their own).
        limit: How many names to return.

    Returns:
        ``({"name", "cpu_seconds"} records, largest first, and the new
        per-pid cumulative table)``.
    """
    current: dict[int, float] = {}
    by_name: dict[str, float] = {}
    for proc in psutil.process_iter(["name", "cpu_times"]):
        times = proc.info.get("cpu_times")
        if times is None or proc.pid in exclude:
            continue
        total = float(times.user + times.system)
        current[proc.pid] = total
        delta = total - previous.get(proc.pid, total)
        if delta > 0:
            name = proc.info.get("name") or "?"
            by_name[name] = by_name.get(name, 0.0) + delta
    ranked = sorted(by_name.items(), key=lambda item: item[1], reverse=True)
    top = [{"name": n, "cpu_seconds": round(s, 1)} for n, s in ranked[:limit]]
    return top, current


def sample(period: float) -> int:
    """Print JSON-lines samples until pytest has been gone for two samples.

    Args:
        period: Seconds between samples.

    Returns:
        The process exit status (0 once the watched session has ended).
    """
    psutil.cpu_percent(interval=None)
    absent = 0
    seen = False
    start = time.monotonic()
    previous_cpu: dict[int, float] = {}
    while True:
        pytest_procs, kernels = _find_groups()
        watched = {p.pid for p in pytest_procs} | {p.pid for p in kernels}
        top_cpu, previous_cpu = _top_cpu(previous_cpu, watched | {os.getpid()})
        if pytest_procs:
            seen = True
            absent = 0
        else:
            absent += 1
        memory = psutil.virtual_memory()
        record = {
            "utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "t": round(time.monotonic() - start, 1),
            "pytest": _counters(pytest_procs) if pytest_procs else None,
            "kernels": _kernel_episodes(kernels),
            "host": {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "available_mb": round(memory.available / 2**20),
                "memory_percent": memory.percent,
                "commit_available_mb": commit_available_mb(),
                "pages_input_per_sec": pages_input_per_second(),
            },
            "top_resident": _top_resident(),
            "top_other_cpu_since_last_sample": top_cpu,
        }
        print(json.dumps(record), flush=True)
        if seen and absent >= 2:
            return 0
        time.sleep(period)


def _mean(values: list[float]) -> float:
    """Return the arithmetic mean, or NaN for an empty list.

    Args:
        values: Numbers to average.

    Returns:
        The mean, or ``nan`` if there are none.
    """
    return sum(values) / len(values) if values else float("nan")


def _episode_row(pid: int, rows: list[dict[str, Any]]) -> str:
    """Format the one-line summary of one notebook-kernel episode.

    Args:
        pid: Root pid of the kernel.
        rows: The samples (record plus kernel counters) in which it was seen.

    Returns:
        A fixed-width text row.
    """
    first, last = rows[0], rows[-1]
    wall = (last["record"]["t"] - first["record"]["t"]) + (
        first["kernel"].get("age_seconds") or 0.0
    )
    cpu = last["kernel"]["cpu_seconds"]
    hosts = [row["record"]["host"] for row in rows]
    avail = [float(h["available_mb"]) for h in hosts]
    pages = [
        h["pages_input_per_sec"] for h in hosts if h["pages_input_per_sec"] is not None
    ]
    pytest_rss = (first["record"]["pytest"] or {}).get("rss_mb", float("nan"))
    return (
        f"{pid:8d}  {first['record']['utc']}  {wall:6.0f}  {cpu:5.0f}  "
        f"{cpu / wall if wall else float('nan'):8.2f}  "
        f"{max(row['kernel']['rss_mb'] for row in rows):11.0f}  "
        f"{min(avail):9.0f}/{_mean(avail):<11.0f}  "
        f"{_mean(pages):8.0f}/{max(pages, default=float('nan')):<10.0f}  "
        f"{pytest_rss:13.0f}  {_mean([h['cpu_percent'] for h in hosts]):10.1f}"
    )


def _other_cpu(rows: list[dict[str, Any]], limit: int = 4) -> str:
    """Summarise which other processes used CPU while an episode ran.

    Args:
        rows: The samples (record plus kernel counters) of one episode.
        limit: How many process names to list.

    Returns:
        ``name=CPU-seconds`` pairs, largest first, summed over the episode.
    """
    totals: dict[str, float] = {}
    for row in rows:
        for item in row["record"].get("top_other_cpu_since_last_sample", []):
            totals[item["name"]] = totals.get(item["name"], 0.0) + item["cpu_seconds"]
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return ", ".join(f"{name}={seconds:.0f}s" for name, seconds in ranked[:limit])


def summarise(lines: list[str]) -> int:
    """Print one row per notebook-kernel episode found in the samples.

    Args:
        lines: JSON-lines produced by :func:`sample`.

    Returns:
        The process exit status.
    """
    records = [json.loads(line) for line in lines if line.strip()]
    episodes: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        for kernel in record["kernels"]:
            episodes.setdefault(kernel["root_pid"], []).append(
                {"record": record, "kernel": kernel}
            )
    print(f"samples: {len(records)}  kernel episodes: {len(episodes)}")
    print(
        "root_pid  first_seen_utc          wall_s  cpu_s  cpu/wall  "
        "peak_rss_mb  host_avail_mb(min/mean)  pages_in/s(mean/max)  "
        "pytest_rss_mb  host_cpu%(mean)"
    )
    for pid, rows in sorted(
        episodes.items(), key=lambda item: item[1][0]["record"]["t"]
    ):
        print(_episode_row(pid, rows))
        print(f"          other processes' CPU while it ran: {_other_cpu(rows)}")
    return 0


def main(argv: list[str]) -> int:
    """Parse arguments and run the sampler or the summariser.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("--period", type=float, default=30.0)
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args(argv)
    if args.summarize:
        return summarise(sys.stdin.read().splitlines())
    return sample(args.period)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

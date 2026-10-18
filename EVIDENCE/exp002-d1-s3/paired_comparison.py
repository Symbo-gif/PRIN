"""Print the control-versus-treatment result of the F2 contention experiment.

Reads the two ``notebook_timing.py`` records written by
``contention_experiment.sh`` from their fixed locations in this bundle
(``f2/contention-experiment/control.json`` and ``treatment.json``) and prints, side
by side, what changed between them: the same notebook, run alone on a quiet host
versus run while only the ``tests/test_exp002_*`` group executed beside it.

It takes no arguments and reads no caller-supplied path::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/paired_comparison.py

Exit status is 0 when both records exist and both notebooks completed.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXPERIMENT = Path(__file__).resolve().parent / "f2" / "contention-experiment"


def load(name: str) -> dict[str, Any]:
    """Read one experiment record.

    Args:
        name: ``control`` or ``treatment``.

    Returns:
        The parsed ``notebook_timing.py`` record.
    """
    record: dict[str, Any] = json.loads(
        (EXPERIMENT / f"{name}.json").read_text(encoding="utf-8")
    )
    return record


def slowest_cell(record: dict[str, Any]) -> tuple[int, float]:
    """Return the slowest code cell's index and wall seconds.

    Args:
        record: A ``notebook_timing.py`` record.

    Returns:
        ``(cell index, seconds)``.
    """
    cells = [(c["cell"], c["wall_seconds"] or 0.0) for c in record["cells"]]
    return max(cells, key=lambda item: item[1])


SUMMARY_TIME = re.compile(r"^(\d\d):(\d\d):(\d\d)Z =+ .*passed.* =+$")


def load_generator_end(treatment_start: datetime) -> datetime | None:
    """Return when the load generator's pytest finished, from its console log.

    Each console line carries a ``HH:MM:SSZ`` prefix; the final summary line gives
    the moment pytest itself ended (the runner's own ``ended:`` line is later,
    because it also waits for the sampler to stop).

    Args:
        treatment_start: When the treatment notebook started, used for the date.

    Returns:
        The end instant, or ``None`` if no summary line is present.
    """
    console = EXPERIMENT / "load" / "console.txt"
    end: datetime | None = None
    for line in console.read_text(encoding="utf-8").splitlines():
        match = SUMMARY_TIME.match(line.strip())
        if match:
            hour, minute, second = (int(group) for group in match.groups())
            end = treatment_start.replace(
                hour=hour, minute=minute, second=second, microsecond=0
            )
    return end


def report_after_load(treatment: dict[str, Any]) -> None:
    """Print the host's CPU while the notebook ran on after the load generator ended.

    The treatment record samples the host every 5 s; the samples taken after the
    load generator's pytest had finished show whether the contention ended with it.

    Args:
        treatment: The ``notebook_timing.py`` record of the treatment run.
    """
    start = datetime.fromisoformat(treatment["started_utc"]).astimezone(UTC)
    end = load_generator_end(start)
    if end is None:
        print("load generator end: no summary line found in its console log")
        return
    offset = (end - start).total_seconds()
    later = [s for s in treatment["samples"] if s["t_wall"] >= offset]
    print()
    print(f"load generator's pytest ended at {end:%H:%M:%S}Z ({offset:.0f} s in)")
    if not later:
        print("  no treatment samples after that moment")
        return
    cpu = [s["host_cpu_percent"] for s in later]
    minutes = (later[-1]["t_wall"] - offset) / 60
    saturated = sum(1 for value in cpu if value >= 90)
    print(f"  {len(later)} host samples over the next {minutes:.1f} min, with the")
    print("  notebook still running:")
    print(f"    host CPU mean {sum(cpu) / len(cpu):.1f}%, min {min(cpu):.1f}%")
    print(f"    samples at or above 90%: {saturated} of {len(cpu)}")


def main() -> int:
    """Print the comparison table.

    Returns:
        The process exit status.
    """
    control, treatment = load("control"), load("treatment")
    rows = (
        ("outcome", control["outcome"], treatment["outcome"]),
        ("wall seconds", control["wall_seconds"], treatment["wall_seconds"]),
        (
            "kernel CPU seconds",
            control["kernel_cpu_seconds_last_sample"],
            treatment["kernel_cpu_seconds_last_sample"],
        ),
        (
            "kernel CPU / wall",
            control["kernel_cpu_over_wall"],
            treatment["kernel_cpu_over_wall"],
        ),
        (
            "host CPU % (mean of samples)",
            control["host_cpu_percent_mean"],
            treatment["host_cpu_percent_mean"],
        ),
        (
            "host available memory, MB (min)",
            control["host_available_mb_min"],
            treatment["host_available_mb_min"],
        ),
        (
            "kernel peak working set, MB",
            control["kernel_peak_working_set_mb"],
            treatment["kernel_peak_working_set_mb"],
        ),
        (
            "slowest cell (index, seconds)",
            slowest_cell(control),
            slowest_cell(treatment),
        ),
    )
    print(f"notebook: {control['notebook']}")
    print(f"{'':36s}{'control (quiet host)':>24s}{'treatment (exp002 tests)':>26s}")
    for label, left, right in rows:
        print(f"{label:36s}{left!s:>24s}{right!s:>26s}")
    ratio = treatment["wall_seconds"] / control["wall_seconds"]
    cell_ratio = slowest_cell(treatment)[1] / slowest_cell(control)[1]
    print()
    print(f"treatment / control wall time        : {ratio:.1f}x")
    print(f"treatment / control slowest-cell time: {cell_ratio:.1f}x")
    cpu_ratio = (
        treatment["kernel_cpu_seconds_last_sample"]
        / control["kernel_cpu_seconds_last_sample"]
    )
    print(f"treatment / control kernel CPU time  : {cpu_ratio:.1f}x")
    print("  (more CPU for the same work: consistent with starved threads spinning,")
    print("   which this experiment did not measure directly)")
    report_after_load(treatment)
    completed = control["outcome"] == treatment["outcome"] == "completed"
    return 0 if completed else 1


if __name__ == "__main__":
    sys.exit(main())

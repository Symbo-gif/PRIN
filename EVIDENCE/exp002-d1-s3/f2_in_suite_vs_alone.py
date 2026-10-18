"""Compare each notebook leg's in-suite duration with its standalone duration.

Backs the disposition of audit finding ``EXP002D1-S2-F2``. For each shipped
notebook it tabulates:

* **alone**: wall seconds from ``f2/alone-<notebook>.json`` (``notebook_timing.py``
  on a quiet host, no pytest);
* **S1 in-suite** and **S2 in-suite**: the ``test_notebook_executes_end_to_end``
  ``--durations`` lines already committed by sessions S1
  (``EVIDENCE/exp002-d1-s1/local-gate.txt``) and S2
  (``EVIDENCE/exp002-d1-s2/pytest-suites.txt``). Those runs used the shipped
  900 s per-cell bound, so a duration of about 900 s or more is **censored**: the
  test was killed at the bound and the true duration is not known;
* **S3 in-suite**: the same lines from the observed diagnostic run, read from the
  console log on **standard input**. That run lifted the per-cell bound to four
  hours (``diag_nb_timeout.py``), so its durations are not censored.

The two committed records and the standalone JSONs are read from fixed relative
locations; the only variable input is standard input, so no caller-supplied
string becomes a filesystem path::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/f2_in_suite_vs_alone.py \
        < EVIDENCE/exp002-d1-s3/f2/diagnostic-full-suite/console.txt

Exit status is 0 when the table was produced.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "EVIDENCE" / "exp002-d1-s3"
NOTEBOOKS = (
    "01_oscillosim_quickstart",
    "02_clevr_n_binding",
    "03_custom_coupling",
    "04_torch_bridge",
)
SESSION_RECORDS = {
    "S1": ROOT / "EVIDENCE" / "exp002-d1-s1" / "local-gate.txt",
    "S2": ROOT / "EVIDENCE" / "exp002-d1-s2" / "pytest-suites.txt",
}
#: ``--durations`` line for a notebook execution test, with an optional leading
#: console timestamp (the observed run prefixes every line with ``HH:MM:SSZ``).
DURATION = re.compile(
    r"^(?:\d\d:\d\d:\d\dZ )?(\d+\.\d+)s call\s+"
    r"tests/test_notebooks\.py::test_notebook_executes_end_to_end\[(\w+)\.ipynb\]"
)
#: The final pytest summary line, with an optional leading console timestamp.
SUMMARY = re.compile(r"^(?:\d\d:\d\d:\d\dZ )?=+ (.*(?:passed|failed|error).*) =+$")
TIMEOUT_SECONDS = 900.0


def durations_from(text: str) -> dict[str, float]:
    """Extract the notebook execution durations from a pytest log.

    Args:
        text: A pytest console log containing a ``--durations`` table.

    Returns:
        A mapping from notebook stem to call seconds.
    """
    found: dict[str, float] = {}
    for line in text.splitlines():
        match = DURATION.match(line.strip())
        if match:
            found[match.group(2)] = float(match.group(1))
    return found


def summary_from(text: str) -> str:
    """Return the run's final pytest summary line, or a note that none was found.

    Args:
        text: A pytest console log.

    Returns:
        The text between the ``=`` rules of the last summary line.
    """
    last = "(no pytest summary line found: the run did not finish)"
    for line in text.splitlines():
        match = SUMMARY.match(line.strip())
        if match:
            last = match.group(1)
    return last


def alone_wall(stem: str) -> float | None:
    """Return a notebook's standalone wall seconds, or ``None`` if not recorded.

    Args:
        stem: Notebook name without extension.

    Returns:
        Wall seconds from its ``f2/alone-<stem>.json``.
    """
    path = BUNDLE / "f2" / f"alone-{stem}.json"
    if not path.is_file():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    return float(record["wall_seconds"])


def cell(value: float | None, censor: bool = False) -> str:
    """Format a seconds value, marking durations at or above the bound as censored.

    Args:
        value: Seconds, or ``None``.
        censor: Whether values at or above the 900 s bound are right-censored.

    Returns:
        A fixed-width string.
    """
    if value is None:
        return f"{'-':>14}"
    mark = ">=" if censor and value >= TIMEOUT_SECONDS else "  "
    return f"{mark}{value:10.1f} s"


def main() -> int:
    """Read the observed console log on stdin and print the comparison table.

    Returns:
        The process exit status.
    """
    observed_text = sys.stdin.read()
    observed = durations_from(observed_text)
    summary = summary_from(observed_text)
    prior = {
        session: durations_from(path.read_text(encoding="utf-8", errors="replace"))
        for session, path in SESSION_RECORDS.items()
        if path.is_file()
    }
    header = (
        f"{'notebook':26s}{'alone':>14s}{'S1 in-suite':>14s}{'S2 in-suite':>14s}"
        f"{'S3 observed':>14s}  {'S3/alone':>9s}"
    )
    print(header)
    print("-" * len(header))
    for stem in NOTEBOOKS:
        alone = alone_wall(stem)
        s3 = observed.get(stem)
        ratio = f"{s3 / alone:8.1f}x" if s3 and alone else f"{'-':>9s}"
        print(
            f"{stem:26s}{cell(alone)}{cell(prior.get('S1', {}).get(stem), True)}"
            f"{cell(prior.get('S2', {}).get(stem), True)}{cell(s3)}  {ratio}"
        )
    print()
    print(
        f"'>=' marks an S1/S2 duration at or above the shipped {TIMEOUT_SECONDS:.0f} s"
    )
    print(
        "per-cell bound: the test was killed there, so the true duration is censored."
    )
    print("S3 observed is the run on standard input. The diagnostic run lifted the")
    print("per-cell bound (uncensored); a gate run does not, so a notebook that")
    print("finished there finished inside its shipped bound.")
    print(f"S3 observed run, final pytest summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

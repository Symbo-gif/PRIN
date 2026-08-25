"""WP-031 S1 statistics parity fixture: golden `scipy.stats` output.

Defines a set of deterministic two-group float samples engineered to cover
distinguishable groups, identical groups, unequal sample sizes, unequal
variances, and near-zero-variance groups, replays each through the real
`scipy.stats.ttest_ind(equal_var=False)` (the reference this WP's
`welch_t_test`/`compute_p_value` are validated against — Project Plan §6
Phase 5's "statistics tools", session brief "Statistical routines match
trusted references"), and writes the inputs plus scipy's own
`statistic`/`pvalue` output to a JSON fixture.

`crates/prin-train/tests/parity_stats.rs` replays the same inputs through
`prin_train::stats::welch_t_test` and asserts its `t_stat`/`p_value` match
the recorded scipy output within tight tolerance.

This tool calls only the third-party `scipy` package (already a base
dependency, see `pyproject.toml`) — never the archived PRINet 3.0 reference
source, consistent with this directory's rule against importing or
executing archived reference code (see `tools/README.md`).

Usage:
    python tools/wp031_stats_fixture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from scipy.stats import ttest_ind

_DEFAULT_OUTPUT = (
    Path("crates")
    / "prin-train"
    / "tests"
    / "data"
    / "welch_t_test_reference_cases.json"
)

Case = tuple[str, list[float], list[float]]

_CASES: list[Case] = [
    ("identical_groups", [1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]),
    (
        "clearly_separated_groups",
        [10.0, 10.1, 9.9, 10.05, 9.95],
        [0.0, 0.1, -0.1, 0.05, -0.05],
    ),
    ("unequal_sample_sizes", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], [2.0, 4.0, 6.0]),
    (
        "unequal_variances",
        [5.0, 5.1, 4.9, 5.05, 4.95, 5.02, 4.98],
        [5.0, 8.0, 2.0, 10.0, 1.0, 6.0, 3.0],
    ),
    ("small_overlapping_groups", [1.0, 5.0, 3.0, 9.0], [2.0, 2.0, 8.0, 1.0]),
    ("minimum_size_groups", [1.0, 2.0], [3.0, 10.0]),
    (
        "near_zero_variance_groups",
        [3.0, 3.0000001, 3.0, 2.9999999],
        [3.0, 3.0, 3.0000001, 2.9999999],
    ),
    (
        "negative_and_positive_values",
        [-5.0, -3.0, -4.0, -6.0, -2.0],
        [5.0, 3.0, 4.0, 6.0, 2.0],
    ),
]


def _run_case(name: str, group_a: list[float], group_b: list[float]) -> dict[str, Any]:
    """Run one `(group_a, group_b)` pair through `scipy.stats.ttest_ind`."""
    result = ttest_ind(group_a, group_b, equal_var=False)
    return {
        "name": name,
        "group_a": group_a,
        "group_b": group_b,
        "t_stat": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def generate(output_path: Path) -> list[dict[str, Any]]:
    """Run every fixture case through `scipy.stats.ttest_ind`.

    Writes the result to `output_path`.
    """
    cases = [_run_case(name, a, b) for name, a, b in _CASES]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    return cases


def main(argv: list[str]) -> int:
    """Generate the fixture at `argv[1]` (or the default path) and report the count."""
    output_path = Path(argv[1]) if len(argv) > 1 else _DEFAULT_OUTPUT
    cases = generate(output_path)
    print(f"Wrote {len(cases)} scenarios to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

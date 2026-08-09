"""Phase 0 exit-gate checker.

Validates the WP-005 evidence and confirms that the three foundation spikes,
the golden-trajectory corpus, the abi3 wheel smoke matrix, and the go/no-go
decisions are ready for the Phase 0 pre-release tag.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prin._phase0 import phase0_gate_report, write_gate_report

_DEFAULT_OUTPUT = Path("EVIDENCE") / "0017-wp005-s1-phase0-gate.json"


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 0 gate and write the evidence JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate Phase 0 exit criteria: ORT probe, golden corpus, "
            "wheel smoke matrix, and recorded spike decisions."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Path where the gate report JSON will be written.",
    )
    parser.add_argument(
        "--refresh-ort",
        action="store_true",
        help="Re-run the ORT probe before checking evidence.",
    )
    args = parser.parse_args(argv)

    report = phase0_gate_report(args.root, refresh_ort=args.refresh_ort)
    write_gate_report(report, args.output)

    print(f"Phase 0 ready: {report.ready}")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    print(f"Evidence written to: {args.output}")
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())

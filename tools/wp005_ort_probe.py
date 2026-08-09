"""Run the ONNX Runtime provider probe and emit the WP-005 S1 evidence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prin._ort import probe_model

_DEFAULT_MODEL = Path("models") / "subconscious_controller.onnx"
_DEFAULT_OUTPUT = Path("EVIDENCE") / "0017-wp005-s1-ort-probe.json"


def _report_to_json(report: object) -> str:
    """Serialize the probe report to a stable JSON string."""
    return json.dumps(
        report.to_dict(),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def main(argv: list[str] | None = None) -> int:
    """Probe the controller model and write the evidence JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the ONNX Runtime provider probe for the PRIN subconscious controller."
        )
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=_DEFAULT_MODEL,
        help="Path to the ONNX model to probe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Path where the evidence JSON will be written.",
    )
    args = parser.parse_args(argv)

    report = probe_model(args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_report_to_json(report), encoding="utf-8")

    summary = (
        f"ORT probe complete: selected={report.selected_backend}, "
        f"active={report.active_providers}, "
        f"can_run={report.can_run}, "
        f"output_shape={report.output_shape}"
    )
    print(summary)
    print(f"Evidence written to: {args.output}")
    return 0 if report.can_run else 1


if __name__ == "__main__":
    sys.exit(main())

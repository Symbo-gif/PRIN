#!/usr/bin/env python
"""PRIN reproducibility pipeline.

Regenerates all paper figures (15) and LaTeX tables (11) from the stored JSON
artefacts (~172 files) with no GPU or training required, and verifies the
SHA-256 manifest. Behavior is unchanged from PRINet 3.0 ``reproduce.py``
(requirement F4: byte-comparable output from the same artefacts).

Usage:
    python tools/reproduce.py [--figures-only | --tables-only] [--verify-manifest]

Implemented during Phase 6 by porting the 3.0 pipeline onto
``prin.reporting``. Artefact output convention:
``DOCS/test_and_benchmark_results/`` (gitignored).
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Entry point for the reproducibility pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures-only", action="store_true")
    parser.add_argument("--tables-only", action="store_true")
    parser.add_argument("--verify-manifest", action="store_true")
    parser.parse_args(argv)
    raise NotImplementedError(
        "The reproduction pipeline is ported in Phase 6 "
        "(see DOCS/PRIN_Project_Plan.md)."
    )


if __name__ == "__main__":
    sys.exit(main())

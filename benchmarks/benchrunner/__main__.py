"""``benchrunner`` CLI: ``python -m benchmarks.benchrunner``.

Dispatches to the registry populated by importing every category package
(:func:`_load_categories`), applies the shared :class:`BenchmarkConfig`, and
writes each result through :func:`write_result`.
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

from benchmarks._common.config import BenchmarkConfig, BenchmarkConfigError
from benchmarks._common.environment import capture_environment
from benchmarks._common.registry import CATEGORIES, RegistryError, get, list_specs
from benchmarks._common.result import OutputPathError, write_result


def _load_categories() -> None:
    """Import every category package so its benchmarks self-register.

    Category packages register their benchmark functions as an import-time
    side effect (see e.g. ``benchmarks/scaling/oscillator_count.py``), the
    same pattern ``pytest`` plugin/fixture discovery uses; this function is
    the single place that knows the full category list.
    """
    for category in CATEGORIES:
        import_module(f"benchmarks.{category}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m benchmarks.benchrunner", description=__doc__
    )
    parser.add_argument(
        "--category", choices=CATEGORIES, help="Category to run (all benchmarks in it)."
    )
    parser.add_argument(
        "--name", help="Run only this benchmark name within --category."
    )
    parser.add_argument(
        "--list", action="store_true", help="List registered benchmarks and exit."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("benchmarks") / "results",
        help="Output directory for result JSON (default: benchmarks/results/).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Measured iterations per benchmark (must be >= 10).",
    )
    parser.add_argument("--warmup", type=int, default=2, help="Warmup iterations.")
    parser.add_argument("--seed-counter", type=int, default=0)
    parser.add_argument("--seed-key", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    _load_categories()
    args = _build_parser().parse_args(argv)

    if args.list:
        for spec in list_specs(args.category):
            print(f"{spec.category}/{spec.name}: {spec.summary}")
        return 0

    if args.category is None:
        print("error: --category is required unless --list is given", file=sys.stderr)
        return 2

    try:
        config = BenchmarkConfig(
            iterations=args.iterations,
            warmup=args.warmup,
            seed_counter=args.seed_counter,
            seed_key=args.seed_key,
            out_dir=args.out,
        )
    except BenchmarkConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        specs = (
            [get(args.category, args.name)] if args.name else list_specs(args.category)
        )
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not specs:
        print(
            f"error: no benchmarks registered for category {args.category!r}",
            file=sys.stderr,
        )
        return 2

    for spec in specs:
        payload = spec.fn(config)
        environment = capture_environment(
            backend=str(payload.get("backend", "host CPU")),
            dtype=str(payload.get("dtype", "f64")),
            seed=config.seed_counter,
        )
        out_path = config.out_dir / f"{spec.category}_{spec.name}.json"
        try:
            written = write_result(
                out_path,
                environment=environment,
                config={
                    "iterations": config.iterations,
                    "warmup": config.warmup,
                    "seed_counter": config.seed_counter,
                    "seed_key": config.seed_key,
                },
                payload=payload,
            )
        except OutputPathError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {written}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

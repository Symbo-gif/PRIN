#!/usr/bin/env python
"""Windows-friendly CLI for the PRIN code-intelligence subsystem.

Run directly (no installation required, matching every other script in
``tools/``):

    python tools/code-intelligence/cli.py index
    python tools/code-intelligence/cli.py status
    python tools/code-intelligence/cli.py hotspots --metric pagerank
    python tools/code-intelligence/cli.py serve-mcp

See ``DOCS/devtools/visualization-mcp.md`` for the full command reference.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SUBSYSTEM_ROOT = Path(__file__).resolve().parent
if str(_SUBSYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SUBSYSTEM_ROOT))

from ci_config import Settings, resolve_settings  # noqa: E402
from ci_graph.store import GraphStore  # noqa: E402
from ci_mcp_server import tools as impl  # noqa: E402
from ci_mcp_server.tools import ToolError  # noqa: E402
from ci_telemetry.instrument import new_trace, traced  # noqa: E402


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str, sort_keys=False))


def _open_ro(settings: Settings) -> GraphStore:
    return GraphStore(settings.db_path, read_only=True)


def _run(settings: Settings, name: str, fn: Any, *args: Any, **kwargs: Any) -> int:
    with new_trace():
        with traced(
            f"cli.{name}",
            enabled=settings.telemetry_enabled,
            telemetry_dir=settings.telemetry_dir,
        ):
            try:
                result = fn(*args, **kwargs)
            except ToolError as exc:
                _print_json({"error": str(exc), "error_type": "ToolError"})
                return 1
            except FileNotFoundError as exc:
                _print_json(
                    {
                        "error": str(exc),
                        "error_type": "NotIndexed",
                        "hint": "run 'index' first",
                    }
                )
                return 1
    _print_json(result)
    return 0


def cmd_index(args: argparse.Namespace, settings: Settings) -> int:
    """Index (or re-index) the repository."""
    return _run(
        settings,
        "index",
        impl.index_repository,
        lambda: GraphStore(settings.db_path, read_only=False),
        settings,
        force=args.force,
    )


def cmd_status(_args: argparse.Namespace, settings: Settings) -> int:
    """Report index status."""
    with _open_ro(settings) as store:
        return _run(settings, "status", impl.get_index_status, store, settings)


def cmd_query(args: argparse.Namespace, settings: Settings) -> int:
    """Search the graph."""
    entity_types = args.types.split(",") if args.types else None
    with _open_ro(settings) as store:
        return _run(
            settings,
            "query",
            impl.search_graph,
            store,
            args.query,
            entity_types,
            args.limit,
        )


def cmd_hotspots(args: argparse.Namespace, settings: Settings) -> int:
    """Report architectural hotspots."""
    with _open_ro(settings) as store:
        return _run(
            settings,
            "hotspots",
            impl.get_hotspots,
            store,
            settings,
            args.metric,
            args.limit,
        )


def cmd_cycles(args: argparse.Namespace, settings: Settings) -> int:
    """Detect circular dependencies."""
    with _open_ro(settings) as store:
        return _run(
            settings, "cycles", impl.find_circular_dependencies, store, args.scope
        )


def cmd_impact(args: argparse.Namespace, settings: Settings) -> int:
    """Run impact analysis for a target node."""
    with _open_ro(settings) as store:
        return _run(
            settings, "impact", impl.get_impact_analysis, store, args.target, args.depth
        )


def cmd_diagram(args: argparse.Namespace, settings: Settings) -> int:
    """Generate a bounded Mermaid diagram."""
    with _open_ro(settings) as store:
        return _run(
            settings,
            "diagram",
            impl.generate_mermaid_diagram,
            store,
            settings,
            args.kind,
            args.target,
            args.direction,
            args.depth,
            args.max_nodes,
            args.max_edges,
            not args.no_write,
        )


def cmd_serve_mcp(_args: argparse.Namespace, _settings: Settings) -> int:
    """Start the local read-only MCP server over stdio."""
    from ci_mcp_server.server import main as server_main

    server_main()
    return 0


def cmd_telemetry_summary(args: argparse.Namespace, settings: Settings) -> int:
    """Summarize ingested runtime telemetry (optionally ingesting first)."""
    if args.ingest:
        with GraphStore(settings.db_path, read_only=False) as store:
            ingest_result = _run(
                settings, "telemetry_ingest", impl.telemetry_ingest, store, settings
            )
            if ingest_result != 0:
                return ingest_result
    with _open_ro(settings) as store:
        return _run(
            settings,
            "telemetry_summary",
            impl.query_runtime_summary,
            store,
            settings,
            args.time_range,
        )


def cmd_trace_flow(args: argparse.Namespace, settings: Settings) -> int:
    """Show spans for a trace id or operation name."""
    with _open_ro(settings) as store:
        return _run(
            settings,
            "trace_flow",
            impl.get_trace_or_flow,
            store,
            args.trace_id_or_operation,
        )


def cmd_verify_installation(_args: argparse.Namespace, settings: Settings) -> int:
    """Check that the subsystem's dependencies and permissions are in place."""
    from ci_verify import run_verification

    report = run_verification(settings)
    _print_json(report)
    return 0 if report["overall"] == "pass" else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns:
        The configured parser with all subcommands registered.
    """
    parser = argparse.ArgumentParser(
        prog="code-intelligence",
        description="PRIN local codebase visualization and runtime-observability CLI",
    )
    parser.add_argument(
        "--repo-root", default=None, help="override the repository root"
    )
    parser.add_argument("--db", default=None, help="override the SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="index (or re-index) the repository")
    p_index.add_argument(
        "--force", action="store_true", help="discard prior index data first"
    )
    p_index.set_defaults(func=cmd_index)

    p_status = sub.add_parser("status", help="report index status")
    p_status.set_defaults(func=cmd_status)

    p_query = sub.add_parser("query", help="search the graph")
    p_query.add_argument("query", help="substring to search for")
    p_query.add_argument("--types", default=None, help="comma-separated node types")
    p_query.add_argument("--limit", type=int, default=50)
    p_query.set_defaults(func=cmd_query)

    p_hotspots = sub.add_parser("hotspots", help="report architectural hotspots")
    p_hotspots.add_argument(
        "--metric",
        default="pagerank",
        choices=["pagerank", "fanin", "fanout", "churn", "runtime_latency"],
    )
    p_hotspots.add_argument("--limit", type=int, default=20)
    p_hotspots.set_defaults(func=cmd_hotspots)

    p_cycles = sub.add_parser("cycles", help="detect circular dependencies")
    p_cycles.add_argument(
        "--scope", default=None, help="repository-relative path prefix"
    )
    p_cycles.set_defaults(func=cmd_cycles)

    p_impact = sub.add_parser("impact", help="impact analysis for a node")
    p_impact.add_argument(
        "target", help="node id, repo-relative path, or qualified name"
    )
    p_impact.add_argument("--depth", type=int, default=3)
    p_impact.set_defaults(func=cmd_impact)

    p_diagram = sub.add_parser("diagram", help="generate a bounded Mermaid diagram")
    p_diagram.add_argument("kind", choices=list(_diagram_kinds()))
    p_diagram.add_argument("--target", default=None)
    p_diagram.add_argument("--direction", default="both")
    p_diagram.add_argument("--depth", type=int, default=4)
    p_diagram.add_argument("--max-nodes", type=int, default=60)
    p_diagram.add_argument("--max-edges", type=int, default=150)
    p_diagram.add_argument(
        "--no-write", action="store_true", help="do not write to output/"
    )
    p_diagram.set_defaults(func=cmd_diagram)

    p_serve = sub.add_parser(
        "serve-mcp", help="start the local read-only MCP server (stdio)"
    )
    p_serve.set_defaults(func=cmd_serve_mcp)

    p_telemetry = sub.add_parser(
        "telemetry-summary", help="summarize runtime telemetry"
    )
    p_telemetry.add_argument(
        "--ingest", action="store_true", help="ingest local JSONL spans first"
    )
    p_telemetry.add_argument("--time-range", default=None)
    p_telemetry.set_defaults(func=cmd_telemetry_summary)

    p_trace = sub.add_parser(
        "trace-flow", help="show spans for a trace id or operation"
    )
    p_trace.add_argument("trace_id_or_operation")
    p_trace.set_defaults(func=cmd_trace_flow)

    p_verify = sub.add_parser(
        "verify-installation", help="check dependencies/permissions"
    )
    p_verify.set_defaults(func=cmd_verify_installation)

    return parser


def _diagram_kinds() -> tuple[str, ...]:
    from ci_mermaid.render import SUPPORTED_KINDS

    return SUPPORTED_KINDS


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = resolve_settings(repo_root=args.repo_root, db_path=args.db)
    return int(args.func(args, settings))


if __name__ == "__main__":
    raise SystemExit(main())

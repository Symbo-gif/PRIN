# Local Codebase Visualization & Runtime-Observability MCP Subsystem

**Location:** `tools/code-intelligence/` · **Status:** optional, isolated
developer tooling — not part of the Session Cycle, not required by any
existing PRIN functionality. See
[`visualization-mcp-plan.md`](visualization-mcp-plan.md) for the verified
repository facts and assumptions this subsystem is built on,
[`visualization-mcp-architecture.md`](visualization-mcp-architecture.md) for
the data model, [`visualization-mcp-security.md`](visualization-mcp-security.md)
for the trust boundary, and
[`visualization-mcp-troubleshooting.md`](visualization-mcp-troubleshooting.md)
for common problems.

## What this is

A local, SQLite-backed knowledge graph of the PRIN repository (files,
directories, imports, functions/classes, config keys, Lean declarations,
dependency-manifest entries), plus:

- Graph analytics (cycles, PageRank, fan-in/fan-out, articulation points,
  impact analysis, heuristic dead-code candidates).
- Bounded Mermaid diagram generation.
- A local, read-only, STDIO MCP server so Claude Code, Cursor, Devin, or any
  MCP client can query the graph.
- An opt-in, disabled-by-default local runtime-telemetry exporter (JSONL) for
  this subsystem's own operations, with ingestion and percentile/error-rate
  summaries.
- A Windows-friendly CLI (`cli.py`).

## Setup on Windows (PowerShell)

```powershell
# From the repository root, in the existing PRIN virtual environment:
.venv\Scripts\python.exe -m pip install -e ".[devtools]"

# Optional accelerators (tree-sitter parsing, OpenTelemetry bridge) — not
# required for anything in this doc to work:
.venv\Scripts\python.exe -m pip install -e ".[devtools-extra]"

# Confirm the environment is ready:
.venv\Scripts\python.exe tools\code-intelligence\cli.py verify-installation
```

No Docker, no hosted database, no paid service. Everything runs from a
single Python process against a local SQLite file.

## Indexing and re-indexing

```powershell
# Full index (first run, or after a large set of changes):
.venv\Scripts\python.exe tools\code-intelligence\cli.py index --force

# Incremental re-index (content-hash-aware; safe to run anytime):
.venv\Scripts\python.exe tools\code-intelligence\cli.py index

# Check what's indexed:
.venv\Scripts\python.exe tools\code-intelligence\cli.py status
```

The graph database lives at `tools\code-intelligence\.data\graph.db`
(gitignored). `index --force` deletes and rebuilds it from scratch;
`index` (no flag) re-parses every file but preserves the database file
identity. Indexing only ever reads files under the repository root — it
never writes, modifies, or deletes anything outside
`tools\code-intelligence\.data\` and `tools\code-intelligence\output\`.

Excluded by default: `.git`, `.venv`, `target`, `dist`, `build`,
`__pycache__`, `.mypy_cache`, `.pytest_cache`, `.hypothesis`,
`.benchmarks`, `node_modules`, `.oberon`, everything `.gitignore`d, plus a
few PRIN-specific paths (`.pytest_basetemp*`, `DOCS/sphinx/_build`,
`DOCS/archive`, and this subsystem's own synthetic test fixtures). See
`ci_config.py` for the exact list, and
[`visualization-mcp-security.md`](visualization-mcp-security.md) for the
separate, always-on secret-filename exclusion (`.env*`, `*.pem`, `*.key`,
`id_rsa*`, anything matching `*credentials*`/`*secret*`, etc.) — those
files get a structural node (so you can see they exist) but their content
is never read or stored.

## CLI reference

Every command is run as `.venv\Scripts\python.exe tools\code-intelligence\cli.py <command> ...`
and prints structured JSON to stdout.

| Command | Purpose |
|---|---|
| `index [--force]` | (Re-)index the repository |
| `status` | Report index status and diagnostics |
| `query <text> [--types t1,t2] [--limit N]` | Search the graph |
| `hotspots [--metric pagerank\|fanin\|fanout\|churn\|runtime_latency] [--limit N]` | Architectural hotspots |
| `cycles [--scope PATH]` | Circular-dependency detection |
| `impact <target> [--depth N]` | What may be affected if `target` changes |
| `diagram <kind> [--target T] [--direction D] [--depth N] [--max-nodes N] [--max-edges N] [--no-write]` | Generate a Mermaid diagram |
| `serve-mcp` | Start the local read-only MCP server (stdio) |
| `telemetry-summary [--ingest] [--time-range 24h]` | Runtime telemetry summary |
| `trace-flow <trace_id_or_operation>` | Spans for a trace/operation, plus a sequence diagram |
| `verify-installation` | Check dependencies and write permissions |

Diagram `kind` is one of: `repo_overview`, `module_deps`, `call_graph`,
`neighborhood`, `cycles`, `data_flow`, `c4_component`, `pipeline`,
`sequence` (the last one is produced via `trace-flow`, not `diagram`,
since it renders runtime spans rather than the static graph).

### Examples

```powershell
# Top architectural hotspots by PageRank:
.venv\Scripts\python.exe tools\code-intelligence\cli.py hotspots --metric pagerank --limit 15

# Circular dependencies anywhere in python/prin:
.venv\Scripts\python.exe tools\code-intelligence\cli.py cycles --scope python/prin

# Repository overview diagram:
.venv\Scripts\python.exe tools\code-intelligence\cli.py diagram repo_overview --max-nodes 50

# Focused dependency diagram around a specific module:
.venv\Scripts\python.exe tools\code-intelligence\cli.py diagram module_deps `
    --target "python:python/prin/nn/attention.py" --direction both --depth 2
```

Diagrams are written to `tools\code-intelligence\output\<kind>-<UTC timestamp>.mmd`
(gitignored) and echoed to stdout; pass `--no-write` to skip the file.

## MCP client configuration

STDIO transport only — the server never opens a network port. Every tool is
read-only except `index_repository`, which writes only to this subsystem's
own SQLite database (never to a file in the repository being analyzed).

### Claude Code / Cursor / Devin (PowerShell, Windows)

Add to your MCP client's server configuration (exact file depends on the
client — Claude Code's `.mcp.json`, Cursor's `mcp.json`, etc.):

```json
{
  "mcpServers": {
    "prin-code-intelligence": {
      "command": "C:\\dev\\PRIN\\.venv\\Scripts\\python.exe",
      "args": ["C:\\dev\\PRIN\\tools\\code-intelligence\\cli.py", "serve-mcp"],
      "env": {
        "PRIN_CI_REPO_ROOT": "C:\\dev\\PRIN"
      }
    }
  }
}
```

Adjust the two absolute paths if your checkout lives elsewhere. Run
`index` at least once before starting the server (an unindexed graph
returns a clear, actionable `NotIndexed` error from every query tool
rather than an empty result).

### Example prompts

- *"Use search_graph to find PRIN's oscillatory attention implementation,
  then use get_symbol_call_graph on it to see what calls it."*
- *"Run get_hotspots with metric=pagerank and summarize the top 10
  architectural hotspots, noting these are static-analysis heuristics."*
- *"Run find_circular_dependencies scoped to python/prin and explain the
  largest cycle."*
- *"Generate a module_deps Mermaid diagram for
  python/prin/nn/attention.py and render it."*
- *"Run query_runtime_summary; if there's no data, tell me how to enable
  telemetry first."*

## Mermaid generation and optional rendering

Every diagram is deterministic (sorted node/edge order), bounded
(`max_nodes`/`max_edges`/`depth`, default 60/150/4), and reports an
explicit truncation note when a limit is hit. Labels are sanitized so no
symbol/file name containing a quote, backtick, angle bracket, `#`, pipe, or
newline can break the diagram or inject Mermaid syntax.

No SVG/PNG renderer is required or bundled. The `.mmd` files under
`tools\code-intelligence\output\` can be pasted into
[the Mermaid Live Editor](https://mermaid.live) (a third-party site — do
not paste anything sensitive), rendered by the Mermaid preview extension in
VS Code, or rendered locally with the Mermaid CLI (`@mermaid-js/mermaid-cli`,
a separate, optional Node.js tool) if you have Node.js installed:

```powershell
npx -y @mermaid-js/mermaid-cli -i tools\code-intelligence\output\repo_overview-*.mmd -o overview.svg
```

This is entirely optional; indexing, analytics, and the MCP server never
depend on any renderer being present.

## Runtime telemetry

Disabled by default. Enable with an environment variable for the duration
of a PowerShell session:

```powershell
$env:PRIN_DEVTOOLS_TELEMETRY = "1"
.venv\Scripts\python.exe tools\code-intelligence\cli.py hotspots --metric pagerank
.venv\Scripts\python.exe tools\code-intelligence\cli.py diagram cycles

# Ingest the JSONL spans just written and summarize:
.venv\Scripts\python.exe tools\code-intelligence\cli.py telemetry-summary --ingest

# Slowest operations, p95 by default:
.venv\Scripts\python.exe tools\code-intelligence\cli.py trace-flow cli.hotspots
```

Spans are written to `tools\code-intelligence\.data\traces\spans-<UTC date>.jsonl`
(gitignored), one JSON object per line: `trace_id`, `span_id`,
`parent_span_id`, `operation_name`, UTC start/end, `duration_ms`, `status`,
`error_class`, and a small non-sensitive attribute dict — never file
contents, secrets, or free-text prompts. This telemetry instruments **only
this subsystem's own entry points** (CLI commands, MCP tool calls, indexer
adapter passes) — see
[the architecture doc's "known limitations"](visualization-mcp-architecture.md#known-limitations)
for why it does not (yet) instrument PRIN's own solver/benchmark/Lean code.

`get_hotspots(metric="runtime_latency")` and `query_runtime_summary` report
this data through the MCP server too, always labeled `evidence_kind:
"runtime_evidence"` to distinguish it from the static-analysis
`"static_centrality"` metrics.

## Architecture boundary rules (forbidden import directions)

`get_architecture_summary` reports `architecture_boundary_violations`: any
`IMPORTS`/`DEPENDS_ON` edge whose source and destination paths match a
configured `(from_prefix, to_prefix)` rule. No rule is configured by
default — PRIN has no declared layering rule for this subsystem to enforce
out of the box. To add one, edit
`ci_config.ARCHITECTURE_BOUNDARY_RULES` (e.g. add
`("python/prin/reporting", "python/prin/nn")` to flag reporting code
importing neural-network internals) and re-index.

## Adding a parser adapter or a graph edge type

1. New language adapter: add a module under `ci_indexer/` following the
   existing adapters' shape — a `parse(file_node_id, repo_path,
   content_hash, source) -> AdapterOutput` function (see
   `ci_indexer/common.py`). Register it in
   `ci_indexer/orchestrator.py::_dispatch_adapter` and in
   `ci_config.LANGUAGE_BY_EXTENSION`.
2. New edge type: add it to `ci_graph/schema.py::EDGE_TYPES` (this changes
   the SQLite `CHECK` constraint — bump `SCHEMA_VERSION` and re-index with
   `--force`), then emit it from the relevant adapter or the orchestrator's
   resolution pass with an honest `confidence`/`provenance`.
3. Add fixture coverage under `tests/fixtures/mini_repo/` and a test in
   `tests/test_indexer.py`.

## Deleting/resetting locally generated data

Everything generated by this subsystem lives under two gitignored
directories and can be deleted freely — nothing outside them is ever
written:

```powershell
Remove-Item -Recurse -Force tools\code-intelligence\.data
Remove-Item -Recurse -Force tools\code-intelligence\output
```

Re-run `index` afterward to rebuild the graph.

## Performance and large-repository guidance

- Indexing this repository (~2,555 recognized files after exclusions) takes
  on the order of seconds on a typical development machine.
- `get_hotspots(metric="churn")` scans up to 1,000 recent commits by
  default (bounded, configurable in `ci_analytics/churn.py`) via a single
  `git log --name-only` call — no shell, fixed argument list.
- Mermaid generation is always bounded; raise `--max-nodes`/`--max-edges`
  deliberately rather than removing the limit.
- For a much larger monorepo, expect indexing time to scale roughly
  linearly with file count (single-pass `ast`/regex parsing per file) and
  analytics time to scale with graph size (`networkx` in-memory algorithms);
  there is no current sharding/incremental-only mode beyond content-hash
  change detection.

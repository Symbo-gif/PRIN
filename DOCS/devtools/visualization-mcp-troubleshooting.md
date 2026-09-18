# Troubleshooting — Code-Intelligence Subsystem

Run `verify-installation` first for any problem:

```powershell
.venv\Scripts\python.exe tools\code-intelligence\cli.py verify-installation
```

It checks Python version, SQLite, required packages (`networkx`, `PyYAML`,
`pathspec`, the `mcp` SDK), optional accelerators (`tree-sitter`,
`opentelemetry`), `git`/`snyk` on `PATH`, and write permissions on the
subsystem's own directories — each with `"pass"`/`"warn"`/`"fail"` and a
`required` flag. `"overall": "fail"` means a required check failed;
`"warn"` entries are optional accelerators, not problems.

## "no index found" / `NotIndexed` errors

Every query tool and CLI command needs an index first:

```powershell
.venv\Scripts\python.exe tools\code-intelligence\cli.py index --force
```

## `ModuleNotFoundError` for `ci_graph`, `ci_indexer`, etc.

These modules are not installed as a package — `cli.py` and
`tests/conftest.py` both insert `tools/code-intelligence/` onto `sys.path`
at import time. Always run via `cli.py` (or through the MCP server, which
also goes through `cli.py serve-mcp`), never by importing `ci_*` modules
directly from an unrelated working directory/script.

## `ModuleNotFoundError: No module named 'mcp'`

Install the `devtools` extra:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[devtools]"
```

## MCP client shows no tools / fails to start the server

1. Confirm the `command`/`args` paths in your MCP client config are
   absolute and correct for your checkout location.
2. Run `serve-mcp` directly in a terminal first — a Python traceback there
   (e.g. a missing dependency) is much easier to read than through the MCP
   client's own error surface:
   ```powershell
   .venv\Scripts\python.exe tools\code-intelligence\cli.py serve-mcp
   ```
   (It will sit waiting for STDIO input — `Ctrl+C` to stop. This confirms
   the process starts cleanly.)
3. Verify tool discovery with the MCP SDK's own client, without any
   external MCP host:
   ```powershell
   python -c "
   import asyncio
   from mcp import ClientSession, StdioServerParameters
   from mcp.client.stdio import stdio_client

   async def main():
       params = StdioServerParameters(
           command='.venv/Scripts/python.exe',
           args=['tools/code-intelligence/cli.py', 'serve-mcp'],
       )
       async with stdio_client(params) as (r, w):
           async with ClientSession(r, w) as s:
               await s.initialize()
               tools = await s.list_tools()
               print([t.name for t in tools.tools])

   asyncio.run(main())
   "
   ```

## A diagram is truncated / looks incomplete

Every `MermaidResult` carries `truncated`, `omitted_nodes`,
`omitted_edges`, and human-readable `notes` explaining exactly which limit
was hit. Raise `--max-nodes`/`--max-edges`/depth deliberately rather than
assuming the diagram is complete; very large neighborhoods (e.g. the
`__future__` import, which nearly every Python file references) are
intentionally capped for readability.

## Hotspot/PageRank results look dominated by generic names

If you see names like `len`, `get`, `to`, `new` dominating
`hotspots --metric fanin`/`pagerank`, re-index — a call-site-frequency
guard (`ci_indexer/orchestrator.py::_MAX_CALL_SITE_OCCURRENCES_FOR_RESOLUTION`)
should already exclude these from `CALLS`-edge resolution. If a different
generic name still dominates, this is the known limitation of
naming-heuristic call resolution (no type information) described in the
architecture doc — cross-check with `pagerank`/`fanin` restricted to
`IMPORTS`/`DEPENDS_ON` edges (structurally exact) rather than `CALLS`.

## `hotspots --metric churn` returns an empty result / "git history unavailable"

This requires `git` on `PATH` and a real git history at the repository
root (`git log` is invoked with a bounded commit count, no shell). Check
`verify-installation`'s `git` entry. This is expected (not an error) in a
shallow clone with too little history, or an environment without `git`
installed.

## Telemetry shows no data

Telemetry is disabled by default. Confirm `PRIN_DEVTOOLS_TELEMETRY=1` was
set **in the same shell** before running commands, then ingest before
summarizing:

```powershell
$env:PRIN_DEVTOOLS_TELEMETRY = "1"
.venv\Scripts\python.exe tools\code-intelligence\cli.py status
.venv\Scripts\python.exe tools\code-intelligence\cli.py telemetry-summary --ingest
```

Check `tools\code-intelligence\.data\traces\` for `spans-*.jsonl` files —
if none exist, the environment variable was not set when the traced
commands ran.

## Resetting everything

```powershell
Remove-Item -Recurse -Force tools\code-intelligence\.data
Remove-Item -Recurse -Force tools\code-intelligence\output
.venv\Scripts\python.exe tools\code-intelligence\cli.py index --force
```

## Snyk / security-tooling warnings during development

`verify-installation`'s `snyk`/`git` checks only report whether the
executables are on `PATH` — a `"warn"` there means the optional Snyk
secure-development workflow (`.devin/skills/snyk-secure-development/`)
cannot run locally, not that the subsystem itself is broken. See
[`visualization-mcp-security.md`](visualization-mcp-security.md) for the
exact scans expected and how to run them.

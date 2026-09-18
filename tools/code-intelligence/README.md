# tools/code-intelligence/ — local codebase visualization & MCP subsystem

Optional, self-contained developer tooling. Builds a local SQLite code
knowledge graph of this repository, computes graph analytics, generates
bounded Mermaid diagrams, and exposes a read-only local MCP server plus an
opt-in runtime-telemetry pipeline for its own operations.

**Not part of the Session Cycle / WP process** — it is isolated developer
tooling, not a change to `crates/`, `python/prin`, benchmarks, or the paper.
Full documentation: [`DOCS/devtools/visualization-mcp.md`](../../DOCS/devtools/visualization-mcp.md)
(setup, CLI reference, MCP client configuration, example prompts),
[`-architecture.md`](../../DOCS/devtools/visualization-mcp-architecture.md),
[`-security.md`](../../DOCS/devtools/visualization-mcp-security.md), and
[`-troubleshooting.md`](../../DOCS/devtools/visualization-mcp-troubleshooting.md).

## Quick start

```powershell
.venv\Scripts\python.exe -m pip install -e ".[devtools]"
.venv\Scripts\python.exe tools\code-intelligence\cli.py verify-installation
.venv\Scripts\python.exe tools\code-intelligence\cli.py index
.venv\Scripts\python.exe tools\code-intelligence\cli.py hotspots --metric pagerank
.venv\Scripts\python.exe tools\code-intelligence\cli.py serve-mcp
```

## Layout

- `cli.py` — the CLI entry point (`index`, `status`, `query`, `hotspots`,
  `cycles`, `impact`, `diagram`, `serve-mcp`, `telemetry-summary`,
  `trace-flow`, `verify-installation`).
- `ci_config.py`, `ci_verify.py` — settings, exclusion lists,
  installation checks.
- `ci_graph/` — SQLite schema, node-identity scheme, the `GraphStore`.
- `ci_indexer/` — repository walk + per-language adapters (Python, Rust,
  Lean, TOML/JSON/YAML, TS/JS) + cross-file import/call resolution.
- `ci_analytics/` — `networkx`-backed cycles/PageRank/fan-in-out/impact
  analysis/dead-code heuristics + a bounded git-churn calculator.
- `ci_mermaid/` — bounded, sanitized Mermaid diagram generation.
- `ci_telemetry/` — opt-in local JSONL span export/ingestion/summaries +
  an optional OpenTelemetry bridge.
- `ci_mcp_server/` — the read-only stdio MCP server and its shared tool
  implementations (also used directly by `cli.py`).
- `tests/` — pytest suite against a small synthetic multi-language fixture
  repository (`tests/fixtures/mini_repo/`); run with
  `pytest tools/code-intelligence/tests -v` (not part of the root
  `tests/` suite's `testpaths`).
- `.data/`, `output/` — gitignored, generated (SQLite database, JSONL
  telemetry, Mermaid diagrams). Safe to delete at any time; see the
  troubleshooting doc's reset section.

## Status

Initial build. All 59 subsystem tests pass; `ruff`, `mypy --strict`, and
`bandit` are clean against this directory (0 medium+ bandit findings);
Snyk Code reports 0 issues. See
`DOCS/devtools/visualization-mcp-security.md` for full scan evidence,
including the Snyk Open Source result and why it is not attributable to
this change.

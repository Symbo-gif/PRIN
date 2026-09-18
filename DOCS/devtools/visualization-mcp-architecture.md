# Architecture — Code-Intelligence Subsystem

See [`visualization-mcp-plan.md`](visualization-mcp-plan.md) for the verified
repository facts and explicit assumptions this design is built on.

## Component map

```
tools/code-intelligence/
  cli.py                 Windows-friendly CLI (argparse), one subcommand per
                          capability, shares all logic with the MCP server
                          via ci_mcp_server/tools.py.
  ci_config.py            Settings resolution, exclusion lists, secret-filename
                          globs, Mermaid/query limits.
  ci_verify.py             `verify-installation` checks.
  ci_graph/                SQLite schema + typed store + node-identity scheme.
  ci_indexer/               Repository walk + per-language adapters + the
                            two-pass cross-file import/call resolver.
  ci_analytics/              networkx-backed graph analytics + git-churn.
  ci_mermaid/                 Bounded diagram generation + label sanitizing.
  ci_telemetry/                 Span model, JSONL writer/reader, ingestion,
                                 percentile/error-rate summaries, optional
                                 OpenTelemetry bridge.
  ci_mcp_server/                 FastMCP stdio server + shared tool
                                 implementations + path/secret defense in
                                 depth.
  tests/                          pytest suite + synthetic fixture repo.
```

Data flows one way for indexing: `cli.py`/MCP tool → `ci_indexer.orchestrator`
→ per-language adapter → `ci_graph.store.GraphStore` (SQLite). Queries flow
the other way: `GraphStore` → `ci_analytics.graph_view` (in-memory
`networkx.MultiDiGraph`, cached per index version) → `ci_analytics.metrics`
/ `ci_mermaid.render` → the CLI or an MCP tool response.

## Data model

### Node identity

`"{language}:{repo_relative_posix_path}"` for files/dirs/modules, and
`"{language}:{repo_relative_posix_path}::{qualified.name}"` for symbols
(`ci_graph/identity.py`). IDs are stable across re-indexing because they
are derived from the path and name, never a database auto-increment key.
Directory nodes use `"dir:{repo_relative_path}"` (`"dir:."` for the root).
External (non-repository) references — an imported third-party package, an
unresolved `use` target — get a lightweight placeholder node
`"external:{name}"`.

### Node types

`repository`, `directory`, `file`, `module`, `class`, `function`, `method`,
`test`, `cli_command`, `config_file`, `config_key`, `solver_invocation`,
`theorem`, `proof_artifact`, `benchmark`, `experiment_config`,
`result_artifact`, `external_service`, `unknown`. Every type is declared in
`ci_graph/schema.py::NODE_TYPES` and enforced by a SQLite `CHECK`
constraint. **Not every type is populated by an adapter in this pass** —
see "Known limitations" below.

### Edge types, confidence, and provenance

`CONTAINS`, `IMPORTS`, `DEFINES`, `CALLS`, `REFERENCES`, `IMPLEMENTS`,
`TESTS`, `CONFIGURES`, `INVOKES`, `PROVES`, `DEPENDS_ON`, `PRODUCES`,
`CONSUMES`, `EMITS`, `VALIDATES` (`ci_graph/schema.py::EDGE_TYPES`). Every
edge carries:

- `confidence` (0.0–1.0)
- `provenance`: one of `exact_parser`, `static_inference`,
  `naming_heuristic`, `runtime_trace`, `manual_annotation`
- `evidence`: a small JSON blob (e.g. the matched source line and line
  number) — never full file contents

| Source | Provenance | Typical confidence | Why |
|---|---|---|---|
| Python `ast` import/`DEFINES` | `exact_parser` | 0.95–1.0 | Real parser, no ambiguity in what a statement *is* |
| TOML/JSON/YAML structure | `exact_parser` | 1.0 | `tomllib`/`json`/PyYAML are real parsers |
| Rust `use`/`mod`/item regex | `static_inference` (item defs), `naming_heuristic` (`use` targets) | 0.5–0.9 | Regex-based; `mod` resolution follows a reliable filesystem convention, `use` path→file mapping is a guess |
| Lean import/declaration regex | `static_inference`/`naming_heuristic` | 0.5–0.8 | Textual only; **never claims a proof is checked** |
| TS/JS import/definition regex | `static_inference` | 0.6–0.85 | Regex-based; exercised only against the test fixture today |
| `CALLS` (any language) | `naming_heuristic` | 0.35–0.6 | Unqualified name match, no type resolution — see below |
| Dependency-manifest entries | `exact_parser` | 0.9–0.95 | Exact parse of a well-known key (`[project.dependencies]`, `[dependencies]`) |

### Call-graph resolution and its limits

There is no type inference. A call `x.get(...)` is recorded by its simple
attribute name (`get`) regardless of what `x` actually is. Two guards keep
this useful rather than noisy:

1. Ambiguous names (more than 3 same-named definitions repo-wide) are not
   resolved at all — no edge is created, rather than a low-confidence one
   to the wrong target.
2. **Call-site-frequency guard**: a callee name occurring 30+ times across
   the whole repository (an near-certain sign of a generic/stdlib-shaped
   accessor like `len`, `get`, `to`, `new`) is skipped entirely, never
   resolved. Without this guard, PageRank/fan-in hotspots were dominated by
   these generic names during real-repository testing (see the plan's
   acceptance-workflow results) — resolving them would misrepresent
   architectural centrality, and a skipped edge is honest (no claim) where
   a resolved one at that volume would not be.

### Index versioning and cache invalidation

Each index run computes `index_version` as the SHA-256 of the sorted,
newline-joined per-file content hashes, stored on the `index_runs` row only
once the run completes (`GraphStore.finish_run`). `ci_analytics.graph_view`
caches its in-memory `networkx` graph keyed by this version, so repeated
MCP tool calls against an unchanged index don't re-read the database, and a
fresh `index_repository` call in a long-running MCP server session
correctly invalidates the cache on its next query.

## MCP server

`ci_mcp_server/server.py` builds one `FastMCP` instance (STDIO transport)
with 16 tools, each backed by a shared implementation function in
`ci_mcp_server/tools.py` (also used directly by `cli.py`, so the CLI and
MCP always agree). Every tool except `index_repository` opens a **read-only**
SQLite connection (`file:...?mode=ro`) per call; `index_repository` opens a
writable connection scoped to its own call and closes it before returning.
`ToolAnnotations.readOnlyHint`/`destructiveHint` are set accordingly and
verified by `tests/test_mcp_server.py`.

## Runtime telemetry pipeline

`ci_telemetry/spans.py` defines a dependency-free `Span` dataclass and a
`JsonlSpanWriter` that appends one JSON object per line to a UTC-dated file.
`ci_telemetry/instrument.py::traced()` is a context manager that is a true
no-op when disabled (no filesystem touch, no timer) and otherwise emits a
span with correlation via `contextvars`-scoped trace/parent-span ids.
`ci_telemetry/otel_bridge.py` optionally re-emits the same span through the
`opentelemetry` API if it is importable — it never configures its own
exporter or network endpoint, so it can never turn into an unexpected
network call. `ci_telemetry/ingest.py` loads JSONL files into the
`runtime_spans` SQLite table (idempotent, keyed by `span_id`);
`ci_telemetry/summary.py` computes p50/p95/p99/error-rate per operation
name.

## Known limitations

- **No instrumentation inside `crates/*` or `python/prin`.** Per the plan's
  assumption #4, adding telemetry to PRIN's own solver/benchmark/Lean
  invocation code would edit governed, audited core code — the opposite of
  "well-isolated." `ci_telemetry.instrument.traced` is exported as a
  reusable, importable primitive for a future, separately-governed PR to
  wire in at those boundaries if desired.
- **`solver_invocation`, `benchmark`, `experiment_config`, `result_artifact`,
  `external_service` node types are declared in the schema but not yet
  populated by any adapter.** `list_proof_solver_benchmark_links` reports
  exactly this limitation rather than fabricating coverage.
- **No semantic Rust type/trait-impl resolution** beyond regex-based
  item/`use`/`mod` extraction — would require `rustc`/`rust-analyzer`
  integration.
- **No Lean proof-term checking** — declarations are recorded, proofs are
  never verified or elaborated.
- **Dead-code detection is a heuristic candidate list**, not a proof:
  static analysis cannot see dynamic dispatch, reflection, string-based
  lookups, or callers outside the indexed repository.
- **No incremental/watch-mode indexing.** Every `index` call re-walks and
  re-parses the whole repository; content hashes make this fast but it is
  not a true incremental index.
- **Tree-sitter is not wired in.** The default adapters (Python `ast`,
  regex for Rust/Lean/TS-JS) are the only parsing path in this pass; a
  tree-sitter-backed adapter could be added later behind the same
  `AdapterOutput` interface without a schema change.

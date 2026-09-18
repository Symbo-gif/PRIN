# Local Codebase Visualization & Runtime-Observability MCP Subsystem — Implementation Plan

**Status:** Living plan for a well-isolated developer-tooling addition. This
document is descriptive of a new, self-contained subsystem; it does not amend
`DOCS/PRIN_Project_Plan.md`, does not open a numbered Work Package, and is not
governed by the Session Cycle (`DOCS/standards/Development_Workflow_and_Audit_Standards.md`).
It is written to the same evidentiary bar (verified facts, explicit
assumptions, no invented commands) because `CLAUDE.md` and `.claude/CLAUDE.md`
require that of every change in this repository.

**Why this is not a Work Package:** the task is explicitly "add this as a
well-isolated developer tooling subsystem" that must not "replace or
restructure existing PRIN functionality." PRIN's WP/Session Cycle process
governs changes to the scientific core (`crates/`, `python/prin`, the paper,
benchmarks). This subsystem touches none of that surface; it only *reads* the
repository to build an index. Coding Standards §6 (security) still applies in
full to every line of new code, and is treated as a hard gate below.

---

## 1. Repository facts verified before writing any code

| Fact | Evidence |
|---|---|
| Languages present as first-party source | Rust (`crates/*/src/**/*.rs`, 8 crates), Python (`python/prin`, `tests/`, `benchmarks/`, `tools/`), 2 Lean 4 files (`EVIDENCE/math-audit/manual/*.lean`, hand-written manual math-audit artifacts, not part of any build), no first-party TypeScript/JavaScript (only vendored third-party `.js` under `.venv/Lib/site-packages/**`, which is excluded like any vendor directory) |
| Package managers / build systems | Cargo workspace (`Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`); Python via `pyproject.toml` + `maturin` (PyO3 extension `prin._prin_core`) |
| Lint/type/security tooling already governed | `cargo fmt`, `cargo clippy -D warnings`, `cargo audit`; `ruff` (incl. `S`/bandit rules), `mypy --strict` on `python/prin`, `interrogate`, `bandit`, `pip-audit` (Coding Standards §5–§6) |
| Test runners | `cargo test --workspace`; `pytest` with `testpaths = ["tests"]` and markers `gpu`, `directml`, `slow`, `parity` (`pyproject.toml`) |
| Existing telemetry | `tracing` crate used only inside `crates/prin-daemon/src/daemon.rs` (Rust-side daemon logging/spans). No OpenTelemetry anywhere in the repo (`opentelemetry` absent from `Cargo.lock`/`pyproject.toml`/`.venv`). |
| Documentation convention | `DOCS/` (**uppercase**) is the single governance+docs tree; Documentation Standards §3 explicitly states "the archived plan's lowercase `docs/` convention is superseded... all references must use the exact casing `DOCS`" (Windows is case-insensitive, so both cannot coexist). Every source directory has a `README.md`. Sphinx lives at `DOCS/sphinx/`. |
| `tools/` convention | Flat directory of single-purpose, deterministic, non-interactive Python CLI scripts, each documented in `tools/README.md`; "must not import or execute archived reference code." Subdirectories exist for grouped data (`tools/math_audit_claims/`). |
| Ignore/exclusion conventions | `.gitignore` already excludes `.venv/`, `target/`, `dist/`, `__pycache__/`, `.mypy_cache/`, `.hypothesis/`, `.pytest_basetemp*`, `.benchmarks/`, `DOCS/sphinx/_build*`, `.oberon/`, generated paper/benchmark artefacts. No `node_modules` (no JS package manager). |
| Snyk / secret-scanning | Snyk CLI present on `PATH` (`snyk 1.1306.2`) and authenticated (`snyk whoami` → `Symbo-gif`). Repository skill `.devin/skills/snyk-secure-development/SKILL.md` defines the exact workflow: Snyk Code for new/changed source, Snyk Open Source for dependency changes, ecosystem-native audits stay authoritative, report blocked (never "passed") if unavailable. GitHub secret scanning/push protection are repository-level controls, independent of anything built here. |
| Already-installed Python packages usable without new pins | `networkx` 3.6.1 (transitively present), `PyYAML` 6.0.3, `tomllib` (stdlib, py3.11+), `pathspec` 1.1.1 |
| Not installed / would be new | `mcp` (official MCP Python SDK) — dry-run resolves cleanly (`mcp-1.30.0`) on this interpreter; `tree_sitter` / `tree_sitter_languages` — not installed, and pre-built wheels for the very new CPython 3.14 interpreter in `.venv` are not guaranteed to exist for every grammar, so tree-sitter is treated as an **optional accelerator**, never a hard dependency; `opentelemetry-api`/`-sdk` — not installed, treated as an **optional bridge**, not required for the default local exporter |
| Interpreter in `.venv` | Python 3.14.0 (repository classifiers advertise 3.11–3.13; this is a pre-existing environment fact, not something this task changes). All new code targets `>=3.11` syntax for consistency with `pyproject.toml`'s `requires-python`, and is verified to import cleanly under the actual 3.14 interpreter in `.venv`. |
| Git remote | `origin`/`PRIN` → `github.com/Symbo-gif/PRIN.git` (used only to know this is a real GitHub-hosted repo; no network calls are made by the subsystem). |

## 2. Explicit assumptions (flagged per the task's instruction)

1. **Docs path casing.** The task asks for `docs/devtools/...`. Documentation
   Standards §3 normatively supersedes lowercase `docs/` in this repository.
   **Assumption: all deliverable docs are written under `DOCS/devtools/`**
   (exact casing `DOCS`), not `docs/devtools/`. This is a direct application
   of existing, written project convention, not a new decision.
2. **Subsystem location.** Of the three suggested locations, `tools/` already
   exists, is documented, and is the established home for repository-analysis
   CLI scripts. **Assumption: the subsystem lives at `tools/code-intelligence/`**
   as a self-contained Python package (its own `pyproject`-free internal
   structure, imported by a thin CLI entry script), not a new top-level
   `devtools/` or hidden `.prinet/` directory.
3. **No Session Cycle / WP number.** Because this is explicitly isolated
   tooling that does not touch `crates/`, `python/prin`, benchmarks, or the
   paper, it is **not** assigned a WP number, session brief, or Project State
   Report entry. It still receives the same Coding-Standards-§6 security gate
   as any other change, applied directly (Snyk, ruff, mypy, bandit) rather
   than through the WP audit ledger.
4. **Runtime-instrumentation boundary.** The task lists solver calls, Lean
   invocation, and benchmark execution as instrumentation points. Adding
   `tracing`/telemetry calls *inside* `crates/prin-*` or `python/prin` would
   edit governed, audited, standards-gated core code — the opposite of
   "well-isolated" and "do not restructure existing PRIN functionality."
   **Assumption: this phase instruments only the devtools subsystem's own
   entry points** (CLI commands, MCP tool invocations, the indexer's parse
   passes) and ships instrumentation as an **importable, opt-in library**
   (`code_intelligence.telemetry`) that PRIN maintainers can choose to wire
   into `crates/prin-daemon`, benchmark runners, or a future Lean harness in
   a separate, normally-governed PR. This is called out again in the
   "Known limitations" section of every doc.
5. **Lean 4 semantics.** Only 2 `.lean` files exist, both hand-written,
   manual math-audit artifacts under `EVIDENCE/math-audit/manual/`, not part
   of any Lean build (no `lakefile.lean`/`lean-toolchain` in the repo). The
   Lean adapter parses `import`/`theorem`/`lemma`/`def`/`namespace` textually
   and **never claims to have checked or run the proof** — it records a
   `PROVES`/`DEFINES` edge with `confidence=naming_heuristic` at best, and
   is explicitly documented as non-semantic.
6. **Tree-sitter.** Treated as optional. Default indexing uses the Python
   standard-library `ast` module for Python (exact, parser-based) and
   hand-written regex/line adapters for Rust, Lean, and generic
   TS/JS-in-the-future. If `tree_sitter` + language grammars are importable
   at runtime, later phases may swap in tree-sitter-backed adapters behind
   the same interface without changing the graph schema — out of scope for
   this initial build given the wheel-availability risk on Python 3.14.
7. **No first-party TypeScript/JavaScript today.** A minimal regex-based
   TS/JS import/definition adapter is still built and unit-tested against a
   fixture (so the system is not silently Python/Rust-only if PRIN ever gains
   a JS tool), but there is nothing in the live repository for it to index
   today; this is stated plainly in the docs rather than presented as
   validated against real PRIN code.
8. **OpenTelemetry.** No hosted collector, no paid service. The default and
   only always-available exporter is local JSONL under a gitignored
   directory, using a small dependency-free span data model. If the
   `opentelemetry-sdk` package is present in the environment, an optional
   bridge emits the same spans through it (still to a local
   `ConsoleSpanExporter`/file, never a network collector) — this satisfies
   "start with local stdout/JSONL traces" while leaving a real upgrade path.
9. **MCP transport.** STDIO only, per the task's explicit preference and to
   avoid opening any network port by default.
10. **Test placement.** New tests live under `tools/code-intelligence/tests/`
    and are run with an explicit path
    (`pytest tools/code-intelligence/tests -v`), not merged into the
    top-level `tests/` directory. `pyproject.toml`'s `testpaths = ["tests"]`
    governs the WP-audited scientific test suite and its coverage gates;
    mixing devtools tests into it would silently change what "the test
    suite" means for that governed surface. Root-suite regression is instead
    verified by *running* the existing suite unchanged (see §8) to prove no
    interference.
11. **New dependencies are additive and optional-extra scoped.** A new
    `pyproject.toml` optional-dependency group `devtools` is added
    (`mcp`, pinned) so `pip install -e ".[devtools]"` is the one supported
    install path; `networkx`/`PyYAML` are declared there too even though
    already present transitively, so the subsystem does not silently depend
    on another package's transitive pin. `tree-sitter*` and
    `opentelemetry-*` are a second, separate optional group
    (`devtools-extra`) so the default install stays minimal.

## 3. Architecture overview

```
tools/code-intelligence/
  cli.py                      # argparse entry point: index/status/query/hotspots/
                               # cycles/impact/diagram/serve-mcp/telemetry-summary/
                               # trace-flow/verify-installation
  ci_config.py                 # exclusion list, path containment root, limits
  ci_graph/
    schema.py                  # SQLite DDL: nodes, edges, files, index_runs, runtime_spans
    store.py                   # GraphStore: typed CRUD + query helpers over SQLite
    identity.py                # stable node-id scheme, content hashing
  ci_indexer/
    orchestrator.py             # walk repo, respect .gitignore + exclude list, dispatch by ext
    python_adapter.py           # ast-based: imports, defs, classes, calls (best-effort)
    rust_adapter.py             # regex/line-based: crates (Cargo.toml), mods, use, pub items
    lean_adapter.py             # regex/line-based: imports, theorem/lemma/def, namespaces
    config_adapter.py           # TOML/JSON/YAML -> config nodes + naming-heuristic links
    tsjs_adapter.py              # regex/line-based import/def extraction (no live targets yet)
  ci_analytics/
    graph_view.py                # SQLite -> in-memory networkx DiGraph (cached, version-tagged)
    metrics.py                   # fan-in/out, PageRank, SCC/cycles, articulation points,
                                  # shortest path, impact analysis, dead-code heuristic
  ci_mermaid/
    render.py                     # generic bounded-diagram engine (nodes/edges -> mermaid text)
    sanitize.py                    # label escaping, id stabilization
  ci_telemetry/
    spans.py                        # dependency-free span model + JSONL writer/reader
    instrument.py                    # @traced decorator / context manager, opt-in via env var
    otel_bridge.py                    # best-effort optional OpenTelemetry bridge (import-guarded)
  ci_mcp_server/
    server.py                         # stdio MCP server wiring all read-only tools
    security.py                        # path containment, secret-pattern exclusion, redaction
  tests/
    conftest.py                         # inserts tools/code-intelligence/ onto sys.path
    fixtures/mini_repo/...                # tiny synthetic multi-language repo for deterministic tests
    test_*.py
  output/                                 # gitignored: mermaid .mmd/.svg, exported JSON
  .data/                                   # gitignored: graph.db, telemetry JSONL, cache
```

Module names are prefixed `ci_*` (Code Intelligence) rather than generic
names like `graph`/`config` to avoid any import-shadowing risk against
same-named third-party packages when `tools/code-intelligence/` is placed on
`sys.path` by the CLI entry script and by `tests/conftest.py`. The directory
itself keeps the hyphenated, human-readable name `code-intelligence` (it is
never imported as a dotted package — the CLI script and test conftest both
add it to `sys.path` directly and use plain top-level imports), consistent
with every other script in `tools/` being run directly rather than installed.

Storage: **SQLite** at `tools/code-intelligence/.data/graph.db` (path
configurable via `--db`/`PRIN_CI_DB`). One `index_runs` row per index
operation carries a UTC timestamp and a repository content-hash "index
version"; analytics caches are invalidated whenever that version changes.

Node identity: `"{language}:{posix_repo_relative_path}"` for
files/dirs/modules, and `"{language}:{posix_repo_relative_path}::{qualified.name}"`
for symbols (functions/classes/etc.), so IDs are stable across re-indexing and
human-legible. Content hash = SHA-256 of the file bytes at index time.

Edges carry `(src_id, dst_id, edge_type, confidence, provenance, evidence)`
where `evidence` is a small JSON blob (e.g. the matched import line) so
`explain_graph_evidence` can show *why* an edge exists without re-parsing.

## 4. Analytics

Built on `networkx` (already resolvable in this environment): Tarjan SCC for
cycle detection, `networkx.pagerank` for centrality, `networkx.articulation_points`
run on the undirected projection, `networkx.shortest_path` for dependency
paths, and a BFS-based impact-analysis walk over reversed `IMPORTS`/`CALLS`/
`DEPENDS_ON` edges. Dead-code candidates = nodes of type function/class with
zero inbound `CALLS`/`REFERENCES`/`IMPORTS` edges, excluding declared entry
points, `__init__`/dunder methods, and test files — always returned with
`heuristic: true` and a stated reason, never as a proven-unused claim.

## 5. Mermaid

One bounded generator: default `max_nodes=60`, `max_depth=4`, `max_edges=150`
(overridable, always echoed back with the diagram so truncation is visible),
deterministic ordering (sorted by node id), package-level clustering via
Mermaid `subgraph`, and a label sanitizer that strips/escapes characters
Mermaid treats specially (`"`, `` ` ``, `<`, `>`, newlines, `#`, pipe). When
truncated, an "omitted N nodes / M edges (raise --max-nodes)" summary line is
appended as a Mermaid comment and returned as structured metadata.

## 6. MCP server

Official `mcp` Python SDK, stdio transport, one process per client. Every
tool is synchronous-read-only against the SQLite store (opened read-only),
returns JSON with a `confidence`/`provenance` field on any inferred claim,
and enforces path containment (`tools/code-intelligence/mcp_server/security.py`)
so no tool can resolve a path outside `C:\dev\PRIN` (or an explicitly
configured extra root). Tools never return raw file contents; `explain_graph_evidence`
returns only the small stored `evidence` snippet already captured at index
time (a single matched line), and the indexer itself refuses to store content
from files matching secret-like patterns (`.env*`, `*.pem`, `*.key`,
`id_rsa*`, `**/secrets/**`, anything `.gitignore`d as a credential) or from
outside the repository root.

## 7. Runtime observability

Default: **disabled**. `PRIN_DEVTOOLS_TELEMETRY=1` (or a config flag) turns on
a JSONL exporter under `tools/code-intelligence/.data/traces/*.jsonl` (UTC
timestamps, one JSON object per span: `trace_id`, `span_id`, `parent_span_id`,
`name`, `start`, `end`, `duration_ms`, `status`, `error_class`, a small
attribute dict with no free-text/user-data fields). Spans wrap: the CLI's
`index`/`diagram`/`query` commands, each indexer adapter pass, and each MCP
tool call. `telemetry_ingest` loads JSONL into a `runtime_spans` SQLite table
so `get_slowest_operations`/`query_runtime_summary`/`get_trace_or_flow` can
compute p50/p95/p99 once enough samples exist, and `get_hotspots(metric="runtime_latency")`
can be reported *alongside* (never merged into) static centrality — the two
are always labeled separately (`static_centrality` vs `runtime_evidence`).

## 8. Work sequence

1. This plan (done).
2. Graph schema + SQLite store + node-identity module + tests.
3. Indexer orchestrator + exclusion handling (respect `.gitignore` via
   `pathspec`, plus a configurable default exclude list) + diagnostics.
4. Python adapter (ast) + Rust adapter (regex) + config adapter
   (toml/json/yaml) + Lean adapter + TS/JS adapter, each with fixture tests.
5. Analytics module (networkx-backed) + tests (cycles, pagerank, fan-in/out,
   articulation points, shortest path, impact, dead-code heuristic).
6. Mermaid generator + sanitizer + truncation tests.
7. Telemetry span model + JSONL writer/reader + ingestion + tests
   (disabled-by-default behavior explicitly tested).
8. MCP server (18 tools) + path-containment/secret-exclusion tests.
9. CLI wiring for all 11 subcommands.
10. Docs: this plan, `visualization-mcp.md`, `-architecture.md`,
    `-security.md`, `-troubleshooting.md`, plus a root-README pointer and a
    `tools/README.md` entry (existing convention).
11. `.gitignore` addition for `tools/code-intelligence/.data/` and
    `tools/code-intelligence/output/`.
12. Run the new test suite; run Snyk Code / Snyk Open Source / ruff / mypy /
    bandit on the new code per Coding Standards §6 and record exact results
    (pass, fail-and-fixed, or blocked — never an unverifiable claim); run the
    existing root `pytest`/`cargo test` gates unchanged to prove no
    interference with the governed suite.
13. Acceptance workflow against the real repository (index, hotspots,
    cycles, two Mermaid diagrams, a telemetry sample from the devtools CLI
    itself, MCP tool-discovery check) with exact commands and outputs
    recorded in the final report.
14. Local commit (no push — matches this repository's push/CI cadence
    convention of committing locally and leaving the push as a maintainer
    action, and no push was requested).

## 9. Non-goals for this pass (see docs' "known limitations")

- No semantic Rust type resolution or cross-crate trait-impl resolution
  beyond naming heuristics (would need `rust-analyzer`/rustc integration).
- No Lean proof-term checking.
- No instrumentation added to `crates/*` or `python/prin` itself.
- No SVG/PNG rendering dependency by default (optional, best-effort, never
  required for indexing/MCP to function).
- No incremental/watch-mode indexing (full re-walk per `index` call, content
  hashes used to skip unchanged-file re-parsing where practical).
